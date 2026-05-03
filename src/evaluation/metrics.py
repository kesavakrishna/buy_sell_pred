"""Trading-oriented evaluation metrics for directional prediction."""
import logging
from typing import Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def directional_accuracy(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Fraction of test days where the predicted direction matches actual.

    Args:
        y_true: Binary labels (0 = down, 1 = up)
        y_prob: Predicted probability of 'up' (class 1)

    Returns:
        Accuracy in [0, 1]
    """
    y_pred = (y_prob >= 0.5).astype(int)
    return float((y_pred == y_true.astype(int)).mean())


def brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Mean squared error of probability forecasts (lower = better calibration).

    Args:
        y_true: Binary labels (0/1)
        y_prob: Predicted probability of 'up'

    Returns:
        Brier score in [0, 1]
    """
    return float(np.mean((y_prob - y_true) ** 2))


def sized_sharpe(
    size: np.ndarray,
    log_returns: np.ndarray,
    fees_bps: float = 10,
    annualize: int = 252,
) -> float:
    """Annualized Sharpe for any continuous position-size array.

    Fee is proportional to the absolute change in position size each step.

    Args:
        size: Position size at each step, in [0, 1]
        log_returns: Actual log returns for each step
        fees_bps: One-way fee in basis points
        annualize: Periods per year

    Returns:
        Annualized Sharpe ratio
    """
    size = np.asarray(size, dtype=float)
    prev_size = np.concatenate([[0.0], size[:-1]])
    fee_cost = np.abs(size - prev_size) * (fees_bps / 10_000)
    pnl = size * log_returns - fee_cost
    std = pnl.std()
    if std == 0:
        return 0.0
    return float(pnl.mean() / std * np.sqrt(annualize))


def strategy_sharpe(
    y_prob: np.ndarray,
    log_returns: np.ndarray,
    fees_bps: float = 10,
    annualize: int = 252,
) -> float:
    """Annualized Sharpe ratio of a long/flat strategy derived from model probabilities.

    Position rule: long (1) when P(up) >= 0.5, flat (0) otherwise.
    Fee is applied when position changes.

    Args:
        y_prob: Predicted probability of 'up'
        log_returns: Actual H-bar log returns for each prediction
        fees_bps: One-way fee in basis points (default 10 bps = 0.1%)
        annualize: Periods per year (252 for daily, 252*6=1512 for 4h, etc.)

    Returns:
        Annualized Sharpe ratio (0.0 if strategy has no variance)
    """
    position = (y_prob >= 0.5).astype(float)
    prev_position = np.concatenate([[0.0], position[:-1]])
    fee_cost = np.abs(position - prev_position) * (fees_bps / 10_000)
    pnl = position * log_returns - fee_cost
    std = pnl.std()
    if std == 0:
        return 0.0
    return float(pnl.mean() / std * np.sqrt(annualize))


def evaluate_fold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    log_returns: np.ndarray,
    fees_bps: float = 10,
    annualize: int = 252,
) -> Dict[str, float]:
    """Compute all metrics for a single CV fold.

    Args:
        y_true: Binary direction labels (0/1)
        y_prob: Predicted probability of 'up'
        log_returns: Actual log returns for each test row
        fees_bps: One-way transaction cost in basis points
        annualize: Periods per year for Sharpe annualization

    Returns:
        Dict with keys: dir_accuracy, brier, sharpe, n_trades
    """
    position = (y_prob >= 0.5).astype(float)
    prev_position = np.concatenate([[0.0], position[:-1]])
    n_trades = int(np.abs(position - prev_position).sum())
    return {
        "dir_accuracy": directional_accuracy(y_true, y_prob),
        "brier": brier_score(y_true, y_prob),
        "sharpe": strategy_sharpe(y_prob, log_returns, fees_bps, annualize),
        "n_trades": float(n_trades),
    }


def vol_sizing_sharpe(
    vol_prob: np.ndarray,
    log_returns: np.ndarray,
    fees_bps: float = 10,
    horizon: int = 7,
    bars_per_day: int = 1,
) -> float:
    """Annualized Sharpe of a continuous vol-sizing strategy.

    Position size = 1 - P(high_vol), ranging from 0 (expect high vol) to 1
    (expect low vol, hold full position). Fee is applied on size changes.

    Args:
        vol_prob: Predicted probability of high-vol regime
        log_returns: Actual H-bar log returns for each prediction
        fees_bps: One-way fee in basis points
        horizon: Forecast horizon in bars
        bars_per_day: Bars per calendar day for annualization

    Returns:
        Annualized Sharpe ratio
    """
    size = 1.0 - vol_prob
    prev_size = np.concatenate([[0.0], size[:-1]])
    fee_cost = np.abs(size - prev_size) * (fees_bps / 10_000)
    pnl = size * log_returns - fee_cost
    std = pnl.std()
    if std == 0:
        return 0.0
    periods_per_year = 252 * bars_per_day / horizon
    return float(pnl.mean() / std * np.sqrt(periods_per_year))


def naive_long_sharpe(
    log_returns: np.ndarray,
    fees_bps: float = 10,
    horizon: int = 7,
    bars_per_day: int = 1,
) -> float:
    """Always-invested baseline Sharpe (single entry fee at start).

    Args:
        log_returns: Actual H-bar log returns
        fees_bps: One-way fee in basis points
        horizon: Forecast horizon in bars
        bars_per_day: Bars per calendar day for annualization

    Returns:
        Annualized Sharpe ratio
    """
    pnl = log_returns.copy().astype(float)
    pnl[0] = pnl[0] - fees_bps / 10_000
    std = pnl.std()
    if std == 0:
        return 0.0
    periods_per_year = 252 * bars_per_day / horizon
    return float(pnl.mean() / std * np.sqrt(periods_per_year))


def evaluate_vol_fold(
    y_true_vol: np.ndarray,
    vol_prob: np.ndarray,
    log_returns: np.ndarray,
    fees_bps: float = 10,
    horizon: int = 7,
    bars_per_day: int = 1,
) -> Dict[str, float]:
    """Compute all metrics for a single vol CV fold.

    Args:
        y_true_vol: Binary high-vol labels (1 = high vol, 0 = low vol)
        vol_prob: Predicted probability of high-vol regime
        log_returns: Actual H-bar log returns for PnL calculation
        fees_bps: One-way transaction cost in basis points
        horizon: Forecast horizon in bars
        bars_per_day: Bars per calendar day for annualization

    Returns:
        Dict with keys: vol_accuracy, vol_brier, sizing_sharpe, baseline_sharpe, sharpe_lift
    """
    y_pred_vol = (vol_prob >= 0.5).astype(int)
    vol_accuracy = float((y_pred_vol == y_true_vol.astype(int)).mean())
    vol_brier = float(np.mean((vol_prob - y_true_vol) ** 2))
    sizing = vol_sizing_sharpe(vol_prob, log_returns, fees_bps, horizon, bars_per_day)
    baseline = naive_long_sharpe(log_returns, fees_bps, horizon, bars_per_day)
    return {
        "vol_accuracy": vol_accuracy,
        "vol_brier": vol_brier,
        "sizing_sharpe": sizing,
        "baseline_sharpe": baseline,
        "sharpe_lift": sizing - baseline,
    }


def summarize_folds(fold_results: List[Dict[str, float]]) -> pd.DataFrame:
    """Aggregate per-fold metrics into a summary table with mean and std rows.

    Args:
        fold_results: List of dicts returned by evaluate_fold

    Returns:
        DataFrame indexed by 'Fold 1', 'Fold 2', ..., 'Mean', 'Std'
    """
    df = pd.DataFrame(fold_results, index=[f"Fold {i + 1}" for i in range(len(fold_results))])
    df.loc["Mean"] = df.mean()
    df.loc["Std"] = df.std()
    return df.round(4)
