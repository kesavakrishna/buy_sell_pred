"""Joint direction + vol sizing pipeline (Phase 5).

Combines two XGBoost models trained on the same fold:
  - Direction model → P(up)
  - Vol model       → P(high_vol)

Position size = P(up) × (1 − P(high_vol))
  → Large when bullish AND low-vol expected
  → Near zero when bearish OR high-vol expected

Three strategies are compared per fold:
  - Direction-only:  binary long/flat from P(up) > 0.5
  - Vol-sizing:      continuous 1 − P(high_vol)
  - Joint:           continuous P(up) × (1 − P(high_vol))
  - Baseline:        always invested (buy & hold)

Usage:
    python -m src.pipeline.run_joint --asset BTC/USDT --horizon 7
    python -m src.pipeline.run_joint --asset BTC/USDT          # all horizons
    python -m src.pipeline.run_joint --asset BTC/USDT --refresh
"""
import argparse
import logging
from pathlib import Path
from typing import List

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.evaluation.metrics import directional_accuracy, naive_long_sharpe, sized_sharpe, summarize_folds
from src.evaluation.walk_forward import WalkForwardCV
from src.features.targets import build_all_vol_targets
from src.models.xgboost_direction import XGBoostDirectionModel
from src.pipeline.run import _feature_cols, build_dataset, load_config

matplotlib.use("Agg")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_joint_horizon(
    df: pd.DataFrame,
    horizon: int,
    cfg: dict,
    output_dir: Path,
) -> None:
    """Run walk-forward CV comparing direction-only, vol-sizing, and joint strategies."""
    vol_col = f"future_vol_{horizon}d"
    ret_col = f"log_return_{horizon}d"
    dir_col = f"direction_{horizon}d"
    feat_cols = _feature_cols(df)

    df_clean = df.dropna(subset=feat_cols + [vol_col, ret_col, dir_col]).copy()
    logger.info("Joint horizon %dd — %d usable rows after NaN drop", horizon, len(df_clean))

    min_rows = cfg["evaluation"]["train_min_days"] + cfg["evaluation"]["test_days"]
    if len(df_clean) < min_rows:
        logger.warning("Only %d rows for joint %dd — need at least %d. Skipping.", len(df_clean), horizon, min_rows)
        return

    bars_per_day = cfg["data"].get("bars_per_day", 1)
    annualize = int(252 * bars_per_day)

    cv = WalkForwardCV(
        n_splits=cfg["evaluation"]["n_splits"],
        train_min_days=cfg["evaluation"]["train_min_days"],
        test_days=cfg["evaluation"]["test_days"],
        purge_days=horizon,
    )

    fold_results: List[dict] = []
    all_preds: List[pd.DataFrame] = []

    for fold_i, (train_idx, test_idx) in enumerate(cv.split(df_clean)):
        X_tr = df_clean.loc[train_idx, feat_cols]
        X_te = df_clean.loc[test_idx, feat_cols]
        y_tr_dir = df_clean.loc[train_idx, dir_col]
        y_te_dir = df_clean.loc[test_idx, dir_col]
        vol_tr = df_clean.loc[train_idx, vol_col]
        vol_te = df_clean.loc[test_idx, vol_col]
        ret_te = df_clean.loc[test_idx, ret_col]

        medians = X_tr.median()
        X_tr = X_tr.fillna(medians)
        X_te = X_te.fillna(medians)

        # Train direction model
        dir_model = XGBoostDirectionModel(**cfg["models"]["xgboost"]).fit(X_tr, y_tr_dir)
        y_prob_dir = dir_model.predict_proba(X_te)

        # Train vol model — binarize using training-fold median (no lookahead)
        vol_threshold = vol_tr.median()
        y_tr_vol = (vol_tr > vol_threshold).astype(float)
        y_te_vol = (vol_te > vol_threshold).astype(float)
        vol_model = XGBoostDirectionModel(**cfg["models"]["xgboost"]).fit(X_tr, y_tr_vol)
        y_prob_vol = vol_model.predict_proba(X_te)

        # Position sizes
        dir_size = (y_prob_dir >= 0.5).astype(float)                    # binary long/flat
        vol_size = 1.0 - y_prob_vol                                      # continuous vol inverse
        joint_size = y_prob_dir * (1.0 - y_prob_vol)                    # V1: product of both
        # V2: only go long when direction is net-bullish (P(up) > 0.5),
        # then scale by confidence and reduce for high vol.
        # max(2P−1, 0) maps [0.5,1] → [0,1] linearly; no position when P(up) < 0.5.
        joint_v2_size = np.maximum(2 * y_prob_dir - 1, 0) * (1.0 - y_prob_vol)

        ret = ret_te.values
        dir_sharpe = sized_sharpe(dir_size, ret, cfg["fees_bps"], annualize)
        vol_sharpe = sized_sharpe(vol_size, ret, cfg["fees_bps"], annualize)
        joint_sharpe = sized_sharpe(joint_size, ret, cfg["fees_bps"], annualize)
        joint_v2_sharpe = sized_sharpe(joint_v2_size, ret, cfg["fees_bps"], annualize)
        bh_sharpe = naive_long_sharpe(ret, cfg["fees_bps"], horizon, bars_per_day)

        metrics = {
            "dir_accuracy": directional_accuracy(y_te_dir.values, y_prob_dir),
            "vol_accuracy": directional_accuracy(y_te_vol.values, y_prob_vol),
            "dir_sharpe": dir_sharpe,
            "vol_sharpe": vol_sharpe,
            "joint_v1_sharpe": joint_sharpe,
            "joint_v2_sharpe": joint_v2_sharpe,
            "baseline_sharpe": bh_sharpe,
            "v2_lift": joint_v2_sharpe - bh_sharpe,
        }
        logger.info(
            "  Fold %d — dir_acc=%.3f  vol_acc=%.3f | vol=%.2f  jv1=%.2f  jv2=%.2f  bh=%.2f",
            fold_i + 1,
            metrics["dir_accuracy"],
            metrics["vol_accuracy"],
            vol_sharpe,
            joint_sharpe,
            joint_v2_sharpe,
            bh_sharpe,
        )

        fold_preds = pd.DataFrame(
            {
                "y_prob_dir": y_prob_dir,
                "y_prob_vol": y_prob_vol,
                "dir_size": dir_size,
                "vol_size": vol_size,
                "joint_size": joint_size,
                "joint_v2_size": joint_v2_size,
                "log_return": ret,
            },
            index=test_idx,
        )
        fold_results.append(metrics)
        all_preds.append(fold_preds)

    summary = summarize_folds(fold_results)
    print(f"\n{'='*60}\nJoint Horizon: {horizon}d — Walk-Forward Summary\n{'='*60}")
    print(summary.to_string())

    preds_df = pd.concat(all_preds).sort_index()
    preds_df.to_parquet(output_dir / f"joint_predictions_{horizon}d.parquet")
    _plot_joint_equity(preds_df, horizon, cfg["fees_bps"], output_dir)


def _plot_joint_equity(
    preds_df: pd.DataFrame, horizon: int, fees_bps: float, output_dir: Path
) -> None:
    """Save equity curve comparing all three strategies."""
    log_ret = preds_df["log_return"].values

    def _equity(size):
        prev = np.concatenate([[0.0], size[:-1]])
        pnl = size * log_ret - np.abs(size - prev) * (fees_bps / 10_000)
        return np.exp(np.cumsum(pnl))

    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(preds_df.index, _equity(preds_df["joint_v2_size"].values),
            label="Joint V2: max(2P−1,0)×(1−P(vol))", linewidth=2, color="steelblue")
    ax.plot(preds_df.index, _equity(preds_df["joint_size"].values),
            label="Joint V1: P(up)×(1−P(vol))", linewidth=1.5, linestyle="--", color="royalblue", alpha=0.6)
    ax.plot(preds_df.index, _equity(preds_df["vol_size"].values),
            label="Vol-sizing only", linewidth=1.5, linestyle=":", color="green")
    ax.plot(preds_df.index, _equity(preds_df["dir_size"].values),
            label="Direction-only", linewidth=1.2, linestyle="-.", color="darkorange", alpha=0.6)
    ax.plot(preds_df.index, np.exp(np.cumsum(log_ret)),
            label="Buy & Hold", linewidth=1.2, linestyle="-.", color="gray")
    ax.axhline(1.0, color="black", linewidth=0.6, linestyle=":")
    ax.set_title(f"{horizon}d Horizon — Joint V2 vs Vol vs Direction (net {fees_bps}bps/trade)")
    ax.set_ylabel("Growth of $1")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = output_dir / f"joint_equity_{horizon}d.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    logger.info("Saved joint equity curve -> %s", path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 5 joint direction + vol sizing")
    parser.add_argument("--asset", default="BTC/USDT")
    parser.add_argument("--horizon", type=int, default=None, help="e.g. 7. Omit for all configured horizons.")
    parser.add_argument("--refresh", action="store_true", help="Re-fetch OHLCV and derivatives data")
    parser.add_argument("--config", default="config/settings.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    # Skip H=1 by default — both models are near-random at 1-bar horizon
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

    bars_per_day = cfg["data"].get("bars_per_day", 1)
    vol_horizons = [h for h in horizons if h > 1]
    df = build_all_vol_targets(df, vol_horizons, bars_per_day=bars_per_day)
    logger.info("Dataset: %d rows x %d columns", *df.shape)

    for h in horizons:
        logger.info("\n--- Joint Horizon %dd ---", h)
        run_joint_horizon(df, h, cfg, output_dir)

    logger.info("Done. Results in %s/", output_dir)


if __name__ == "__main__":
    main()
