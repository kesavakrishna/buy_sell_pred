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
        log_returns: Actual H-day log returns for each prediction
        fees_bps: One-way fee in basis points (default 10 bps = 0.1%)
        annualize: Annualization factor (252 for daily)

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
) -> Dict[str, float]:
    """Compute all metrics for a single CV fold.

    Args:
        y_true: Binary direction labels (0/1)
        y_prob: Predicted probability of 'up'
        log_returns: Actual log returns for each test row
        fees_bps: One-way transaction cost in basis points

    Returns:
        Dict with keys: dir_accuracy, brier, sharpe, n_trades
    """
    position = (y_prob >= 0.5).astype(float)
    prev_position = np.concatenate([[0.0], position[:-1]])
    n_trades = int(np.abs(position - prev_position).sum())
    return {
        "dir_accuracy": directional_accuracy(y_true, y_prob),
        "brier": brier_score(y_true, y_prob),
        "sharpe": strategy_sharpe(y_prob, log_returns, fees_bps),
        "n_trades": float(n_trades),
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
