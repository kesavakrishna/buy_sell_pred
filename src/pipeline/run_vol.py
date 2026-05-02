"""Volatility regime prediction pipeline (Phase 3B).

Instead of predicting price direction, predict whether the next H days will be
high- or low-volatility. Position size = 1 - P(high_vol): reduce exposure when
vol is predicted high, hold full when vol is predicted low.

Usage:
    python -m src.pipeline.run_vol --asset BTC/USDT --horizon 7
    python -m src.pipeline.run_vol --asset BTC/USDT              # 7d and 30d
    python -m src.pipeline.run_vol --asset BTC/USDT --refresh
"""
import argparse
import logging
from pathlib import Path
from typing import List

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.evaluation.metrics import evaluate_vol_fold, summarize_folds
from src.evaluation.shap_analysis import run_shap
from src.evaluation.walk_forward import WalkForwardCV
from src.features.targets import build_all_vol_targets
from src.models.xgboost_direction import XGBoostDirectionModel
from src.pipeline.run import _feature_cols, build_dataset, load_config

matplotlib.use("Agg")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# At daily frequency, H=1 is degenerate (std of 1 point = NaN with ddof=1).
# The pipeline skips any horizon where dropna leaves < min_rows.
_DEFAULT_VOL_HORIZONS = [7, 30]


def run_vol_horizon(
    df: pd.DataFrame,
    horizon: int,
    cfg: dict,
    output_dir: Path,
) -> None:
    """Run walk-forward CV for vol regime prediction at a single horizon."""
    vol_col = f"future_vol_{horizon}d"
    ret_col = f"log_return_{horizon}d"
    feat_cols = _feature_cols(df)  # excludes OHLCV, direction_, log_return_, future_vol_

    df_clean = df.dropna(subset=feat_cols + [vol_col, ret_col]).copy()
    logger.info("Vol horizon %dd — %d usable rows after NaN drop", horizon, len(df_clean))

    min_rows = cfg["evaluation"]["train_min_days"] + cfg["evaluation"]["test_days"]
    if len(df_clean) < min_rows:
        logger.warning("Only %d rows for vol %dd — need at least %d. Skipping.", len(df_clean), horizon, min_rows)
        return

    cv = WalkForwardCV(
        n_splits=cfg["evaluation"]["n_splits"],
        train_min_days=cfg["evaluation"]["train_min_days"],
        test_days=cfg["evaluation"]["test_days"],
        purge_days=horizon,
    )

    fold_results: List[dict] = []
    all_preds: List[pd.DataFrame] = []
    last_model, last_X_test = None, None

    for fold_i, (train_idx, test_idx) in enumerate(cv.split(df_clean)):
        X_tr = df_clean.loc[train_idx, feat_cols]
        vol_tr = df_clean.loc[train_idx, vol_col]
        X_te = df_clean.loc[test_idx, feat_cols]
        vol_te = df_clean.loc[test_idx, vol_col]
        ret_te = df_clean.loc[test_idx, ret_col]

        medians = X_tr.median()
        X_tr = X_tr.fillna(medians)
        X_te = X_te.fillna(medians)

        # Binarize with training-fold median — no lookahead into test set
        vol_threshold = vol_tr.median()
        y_tr_vol = (vol_tr > vol_threshold).astype(float)
        y_te_vol = (vol_te > vol_threshold).astype(float)

        model = XGBoostDirectionModel(**cfg["models"]["xgboost"]).fit(X_tr, y_tr_vol)
        vol_prob = model.predict_proba(X_te)

        bars_per_day = cfg["data"].get("bars_per_day", 1)
        metrics = evaluate_vol_fold(
            y_te_vol.values, vol_prob, ret_te.values, cfg["fees_bps"], horizon, bars_per_day
        )
        logger.info(
            "  Fold %d — vol_acc=%.3f  brier=%.3f  sizing_sharpe=%.2f"
            "  baseline_sharpe=%.2f  lift=%.2f  best_iter=%s",
            fold_i + 1,
            metrics["vol_accuracy"],
            metrics["vol_brier"],
            metrics["sizing_sharpe"],
            metrics["baseline_sharpe"],
            metrics["sharpe_lift"],
            getattr(model, "best_iteration_", "n/a"),
        )

        fold_preds = pd.DataFrame(
            {
                "y_true_vol": y_te_vol.values,
                "vol_prob": vol_prob,
                "log_return": ret_te.values,
                "size": 1.0 - vol_prob,
            },
            index=test_idx,
        )
        fold_results.append(metrics)
        all_preds.append(fold_preds)
        last_model, last_X_test = model, X_te

    summary = summarize_folds(fold_results)
    print(f"\n{'='*60}\nVol Horizon: {horizon}d — Walk-Forward Summary\n{'='*60}")
    print(summary.to_string())

    preds_df = pd.concat(all_preds).sort_index()
    preds_df.to_parquet(output_dir / f"vol_predictions_{horizon}d.parquet")
    _plot_vol_equity(preds_df, horizon, cfg["fees_bps"], output_dir)

    if last_model is not None:
        importance = run_shap(last_model, last_X_test, output_dir, f"vol_{horizon}d")
        if not importance.empty:
            print(f"\nTop 10 features for vol prediction ({horizon}d):")
            print(importance.head(10).to_string())


def _plot_vol_equity(
    preds_df: pd.DataFrame, horizon: int, fees_bps: float, output_dir: Path
) -> None:
    """Save equity curve: vol-sized strategy vs buy-and-hold."""
    size = preds_df["size"].values
    log_ret = preds_df["log_return"].values
    prev_size = np.concatenate([[0.0], size[:-1]])
    fee_cost = np.abs(size - prev_size) * (fees_bps / 10_000)
    pnl = size * log_ret - fee_cost

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(preds_df.index, np.exp(np.cumsum(pnl)), label=f"Vol-Sized ({horizon}d)", linewidth=1.5)
    ax.plot(preds_df.index, np.exp(np.cumsum(log_ret)), label="Buy & Hold", linewidth=1.5, linestyle="--")
    ax.axhline(1.0, color="gray", linewidth=0.8, linestyle=":")
    ax.set_title(f"{horizon}d Horizon — Vol-Sized vs Buy & Hold (net {fees_bps}bps/trade)")
    ax.set_ylabel("Growth of $1")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = output_dir / f"vol_equity_{horizon}d.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    logger.info("Saved vol equity curve -> %s", path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 3B volatility regime prediction")
    parser.add_argument("--asset", default="BTC/USDT")
    parser.add_argument("--horizon", type=int, default=None, help="7 or 30. Omit for both.")
    parser.add_argument("--refresh", action="store_true", help="Re-fetch OHLCV and derivatives data")
    parser.add_argument("--config", default="config/settings.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    horizons = [args.horizon] if args.horizon else cfg.get("vol_horizons", cfg.get("horizons", _DEFAULT_VOL_HORIZONS))

    timeframe = cfg["data"].get("timeframe", "1d")
    output_dir = Path("outputs") / f"{args.asset.replace('/', '_')}_{timeframe}"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Building dataset for %s...", args.asset)
    df = build_dataset(cfg, args.asset, refresh=args.refresh)
    bars_per_day = cfg["data"].get("bars_per_day", 1)
    df = build_all_vol_targets(df, horizons, bars_per_day=bars_per_day)
    logger.info("Dataset: %d rows x %d columns", *df.shape)

    for h in horizons:
        logger.info("\n--- Vol Horizon %dd ---", h)
        run_vol_horizon(df, h, cfg, output_dir)

    logger.info("Done. Results in %s/", output_dir)


if __name__ == "__main__":
    main()
