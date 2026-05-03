"""Regime-conditional direction model (Phase 5B).

Trains separate XGBoost direction models for bull and bear regimes, then routes
each test bar to the model that matches its current regime.

Motivation: The fold-collapse problem (Folds 3/4 across all phases) happens
because a model trained on mixed bull+bear data generalises poorly when tested
on a regime-transition period. Separate models learn regime-specific patterns
and are never asked to extrapolate across regimes.

Regime split: trend_strength > 0 → bull model; trend_strength ≤ 0 → bear model.
trend_strength = (EMA_fast − EMA_slow) / EMA_slow — known at prediction time,
computed from historical prices only, no lookahead.

Fallback: if either regime has fewer than MIN_REGIME_ROWS training rows the fold
uses a single combined model (same as run.py), and logs a warning.

Usage:
    python -m src.pipeline.run_regime --asset BTC/USDT --horizon 7
    python -m src.pipeline.run_regime --asset BTC/USDT        # 7d and 30d
    python -m src.pipeline.run_regime --asset BTC/USDT --refresh
"""
import argparse
import logging
from pathlib import Path
from typing import List, Optional

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.evaluation.metrics import (
    brier_score,
    directional_accuracy,
    evaluate_fold,
    naive_long_sharpe,
    sized_sharpe,
    summarize_folds,
)
from src.evaluation.shap_analysis import run_shap
from src.evaluation.walk_forward import WalkForwardCV
from src.models.xgboost_direction import XGBoostDirectionModel
from src.pipeline.run import _feature_cols, build_dataset, load_config

matplotlib.use("Agg")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MIN_REGIME_ROWS = 80   # minimum training rows per regime before falling back to combined


def _train_regime_models(
    X_tr: pd.DataFrame,
    y_tr: pd.Series,
    trend_tr: pd.Series,
    xgb_cfg: dict,
) -> tuple:
    """Train bull and bear XGBoost models on regime-split training data.

    Returns:
        (bull_model, bear_model, used_fallback)
        If either regime has fewer than MIN_REGIME_ROWS rows, returns
        (combined_model, combined_model, True) as fallback.
    """
    bull_mask = trend_tr > 0
    bear_mask = ~bull_mask

    n_bull = bull_mask.sum()
    n_bear = bear_mask.sum()
    logger.debug("  Regime split — bull: %d rows, bear: %d rows", n_bull, n_bear)

    if n_bull < MIN_REGIME_ROWS or n_bear < MIN_REGIME_ROWS:
        logger.warning(
            "  Regime fallback: bull=%d bear=%d (min=%d) — using combined model",
            n_bull, n_bear, MIN_REGIME_ROWS,
        )
        combined = XGBoostDirectionModel(**xgb_cfg).fit(X_tr, y_tr)
        return combined, combined, True

    bull_model = XGBoostDirectionModel(**xgb_cfg).fit(X_tr[bull_mask], y_tr[bull_mask])
    bear_model = XGBoostDirectionModel(**xgb_cfg).fit(X_tr[bear_mask], y_tr[bear_mask])
    return bull_model, bear_model, False


def _predict_regime_routed(
    bull_model,
    bear_model,
    X_te: pd.DataFrame,
    trend_te: pd.Series,
) -> np.ndarray:
    """Route each test bar to the matching regime model and return P(up)."""
    probs = np.empty(len(X_te))
    bull_mask = (trend_te > 0).values
    bear_mask = ~bull_mask

    if bull_mask.any():
        probs[bull_mask] = bull_model.predict_proba(X_te[bull_mask])
    if bear_mask.any():
        probs[bear_mask] = bear_model.predict_proba(X_te[bear_mask])
    return probs


def run_regime_horizon(
    df: pd.DataFrame,
    horizon: int,
    cfg: dict,
    output_dir: Path,
) -> None:
    """Walk-forward CV with regime-conditional direction models."""
    dir_col = f"direction_{horizon}d"
    ret_col = f"log_return_{horizon}d"
    feat_cols = _feature_cols(df)

    df_clean = df.dropna(subset=feat_cols + [dir_col, ret_col]).copy()
    logger.info("Regime horizon %dd — %d usable rows after NaN drop", horizon, len(df_clean))

    min_rows = cfg["evaluation"]["train_min_days"] + cfg["evaluation"]["test_days"]
    if len(df_clean) < min_rows:
        logger.warning("Only %d rows for regime %dd — need %d. Skipping.", len(df_clean), horizon, min_rows)
        return

    bars_per_day = cfg["data"].get("bars_per_day", 1)
    annualize = int(252 * bars_per_day)
    xgb_cfg = cfg["models"]["xgboost"]

    cv = WalkForwardCV(
        n_splits=cfg["evaluation"]["n_splits"],
        train_min_days=cfg["evaluation"]["train_min_days"],
        test_days=cfg["evaluation"]["test_days"],
        purge_days=horizon,
    )

    fold_results: List[dict] = []
    all_preds: List[pd.DataFrame] = []
    last_bull_model: Optional[object] = None
    last_X_te: Optional[pd.DataFrame] = None
    n_fallbacks = 0

    for fold_i, (train_idx, test_idx) in enumerate(cv.split(df_clean)):
        X_tr = df_clean.loc[train_idx, feat_cols]
        X_te = df_clean.loc[test_idx, feat_cols]
        y_tr_dir = df_clean.loc[train_idx, dir_col]
        y_te_dir = df_clean.loc[test_idx, dir_col]
        ret_te = df_clean.loc[test_idx, ret_col]
        trend_tr = df_clean.loc[train_idx, "trend_strength"]
        trend_te = df_clean.loc[test_idx, "trend_strength"]

        medians = X_tr.median()
        X_tr = X_tr.fillna(medians)
        X_te = X_te.fillna(medians)

        bull_model, bear_model, fallback = _train_regime_models(X_tr, y_tr_dir, trend_tr, xgb_cfg)
        if fallback:
            n_fallbacks += 1

        # Regime-routed predictions
        y_prob_regime = _predict_regime_routed(bull_model, bear_model, X_te, trend_te)

        # Combined model (same as run.py) — for direct comparison
        combined_model = XGBoostDirectionModel(**xgb_cfg).fit(X_tr, y_tr_dir)
        y_prob_combined = combined_model.predict_proba(X_te)

        ret = ret_te.values
        regime_size = (y_prob_regime >= 0.5).astype(float)
        combined_size = (y_prob_combined >= 0.5).astype(float)

        regime_sharpe = sized_sharpe(regime_size, ret, cfg["fees_bps"], annualize)
        combined_sharpe = sized_sharpe(combined_size, ret, cfg["fees_bps"], annualize)
        bh_sharpe = naive_long_sharpe(ret, cfg["fees_bps"], horizon, bars_per_day)

        n_bull_test = int((trend_te > 0).sum())
        n_bear_test = int((trend_te <= 0).sum())

        metrics = {
            "regime_accuracy": directional_accuracy(y_te_dir.values, y_prob_regime),
            "combined_accuracy": directional_accuracy(y_te_dir.values, y_prob_combined),
            "regime_brier": brier_score(y_te_dir.values, y_prob_regime),
            "combined_brier": brier_score(y_te_dir.values, y_prob_combined),
            "regime_sharpe": regime_sharpe,
            "combined_sharpe": combined_sharpe,
            "baseline_sharpe": bh_sharpe,
            "regime_lift": regime_sharpe - combined_sharpe,
            "fallback": float(fallback),
        }
        logger.info(
            "  Fold %d — regime_acc=%.3f  combined_acc=%.3f | "
            "regime_sharpe=%.2f  combined_sharpe=%.2f  bh=%.2f  "
            "[bull_test=%d  bear_test=%d  fallback=%s]",
            fold_i + 1,
            metrics["regime_accuracy"],
            metrics["combined_accuracy"],
            regime_sharpe,
            combined_sharpe,
            bh_sharpe,
            n_bull_test,
            n_bear_test,
            fallback,
        )

        fold_preds = pd.DataFrame(
            {
                "y_prob_regime": y_prob_regime,
                "y_prob_combined": y_prob_combined,
                "regime_size": regime_size,
                "combined_size": combined_size,
                "log_return": ret,
                "is_bull": (trend_te > 0).astype(float).values,
            },
            index=test_idx,
        )
        fold_results.append(metrics)
        all_preds.append(fold_preds)
        last_bull_model = bull_model
        last_X_te = X_te

    if n_fallbacks > 0:
        logger.warning("%d/%d folds used fallback combined model", n_fallbacks, len(fold_results))

    summary = summarize_folds(fold_results)
    print(f"\n{'='*60}\nRegime Horizon: {horizon}d — Walk-Forward Summary\n{'='*60}")
    print(summary.to_string())

    preds_df = pd.concat(all_preds).sort_index()
    preds_df.to_parquet(output_dir / f"regime_predictions_{horizon}d.parquet")
    _plot_regime_equity(preds_df, horizon, cfg["fees_bps"], output_dir)

    if last_bull_model is not None and not isinstance(last_bull_model, type(None)) and last_X_te is not None:
        importance = run_shap(last_bull_model, last_X_te, output_dir, f"regime_bull_{horizon}d")
        if not importance.empty:
            print(f"\nTop 10 features — bull model ({horizon}d):")
            print(importance.head(10).to_string())


def _plot_regime_equity(
    preds_df: pd.DataFrame, horizon: int, fees_bps: float, output_dir: Path
) -> None:
    """Equity curves: regime-conditional vs combined vs buy-and-hold."""
    log_ret = preds_df["log_return"].values

    def _equity(size):
        prev = np.concatenate([[0.0], size[:-1]])
        pnl = size * log_ret - np.abs(size - prev) * (fees_bps / 10_000)
        return np.exp(np.cumsum(pnl))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8), sharex=True)

    # Equity curves
    ax1.plot(preds_df.index, _equity(preds_df["regime_size"].values),
             label="Regime-conditional", linewidth=2, color="steelblue")
    ax1.plot(preds_df.index, _equity(preds_df["combined_size"].values),
             label="Combined (baseline)", linewidth=1.5, linestyle="--", color="darkorange")
    ax1.plot(preds_df.index, np.exp(np.cumsum(log_ret)),
             label="Buy & Hold", linewidth=1.2, linestyle="-.", color="gray")
    ax1.axhline(1.0, color="black", linewidth=0.6, linestyle=":")
    ax1.set_title(f"{horizon}d Horizon — Regime-Conditional vs Combined (net {fees_bps}bps/trade)")
    ax1.set_ylabel("Growth of $1")
    ax1.legend(fontsize=9)
    ax1.grid(alpha=0.3)

    # Regime indicator
    ax2.fill_between(preds_df.index, preds_df["is_bull"].values,
                     alpha=0.3, color="green", label="Bull regime (trend_strength > 0)")
    ax2.fill_between(preds_df.index, 1 - preds_df["is_bull"].values,
                     alpha=0.3, color="red", label="Bear regime")
    ax2.set_ylabel("Regime")
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(["Bear", "Bull"])
    ax2.legend(fontsize=9)
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    path = output_dir / f"regime_equity_{horizon}d.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    logger.info("Saved regime equity curve -> %s", path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 5B regime-conditional direction model")
    parser.add_argument("--asset", default="BTC/USDT")
    parser.add_argument("--horizon", type=int, default=None, help="e.g. 7. Omit for [7, 30].")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--config", default="config/settings.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    all_horizons = cfg["horizons"]
    if args.horizon:
        horizons = [args.horizon]
    else:
        horizons = [h for h in all_horizons if h > 1]

    timeframe = cfg["data"].get("timeframe", "1d")
    output_dir = Path("outputs") / f"{args.asset.replace('/', '_')}_{timeframe}"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Building dataset for %s (%s)...", args.asset, timeframe)
    df = build_dataset(cfg, args.asset, refresh=args.refresh)
    logger.info("Dataset: %d rows x %d columns", *df.shape)

    for h in horizons:
        logger.info("\n--- Regime Horizon %dd ---", h)
        run_regime_horizon(df, h, cfg, output_dir)

    logger.info("Done. Results in %s/", output_dir)


if __name__ == "__main__":
    main()
