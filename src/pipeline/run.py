"""CLI entry point: build dataset, run walk-forward CV, report metrics.

Usage:
    python -m src.pipeline.run --asset BTC/USDT --horizon 1
    python -m src.pipeline.run --asset BTC/USDT                  # all horizons
    python -m src.pipeline.run --asset ETH/USDT --refresh        # re-fetch data
    python -m src.pipeline.run --asset BTC/USDT --model logistic # baseline comparison
"""
import argparse
import logging
from pathlib import Path
from typing import List

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from src.data.fear_greed_fetcher import FearGreedFetcher
from src.data.ohlcv_fetcher import OHLCVFetcher
from src.evaluation.metrics import evaluate_fold, summarize_folds
from src.evaluation.shap_analysis import run_shap
from src.evaluation.walk_forward import WalkForwardCV
from src.features.lags import build_lag_features
from src.features.regime import add_regime_features
from src.features.targets import build_all_targets
from src.features.technical import build_technical_features
from src.models.baseline_logistic import DirectionModel
from src.models.baseline_quantile import QuantileModel
from src.models.xgboost_direction import XGBoostDirectionModel

matplotlib.use("Agg")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_OHLCV_COLS = {"open", "high", "low", "close", "volume"}


def load_config(path: str = "config/settings.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def build_dataset(cfg: dict, asset: str, refresh: bool = False) -> pd.DataFrame:
    """Fetch OHLCV + Fear & Greed, then build all features and targets."""
    fetcher = OHLCVFetcher(
        exchange_id=cfg["data"]["exchange"],
        timeframe=cfg["data"]["timeframe"],
    )
    data_dir = cfg["data"]["data_dir"]

    if refresh:
        df = fetcher.fetch_and_save(asset, data_dir, cfg["data"]["days_back"])
    else:
        try:
            df = fetcher.load_cached(asset, data_dir)
        except FileNotFoundError:
            logger.info("No cache found — fetching from Binance")
            df = fetcher.fetch_and_save(asset, data_dir, cfg["data"]["days_back"])

    fg_df = FearGreedFetcher().fetch(limit=365)
    df = df.join(fg_df, how="left")
    df["fear_greed"] = df["fear_greed"].ffill().fillna(50)  # 50 = neutral when no history
    df = df.drop(columns=["fg_label"], errors="ignore")

    fc = cfg["features"]
    df = build_technical_features(
        df,
        rsi_period=fc["rsi_period"],
        macd_fast=fc["macd_fast"],
        macd_slow=fc["macd_slow"],
        macd_signal=fc["macd_signal"],
        bb_period=fc["bb_period"],
        bb_std=fc["bb_std"],
        ema_periods=fc["ema_periods"],
        vol_windows=fc["rolling_windows"],
    )
    df = build_lag_features(df, fc["lag_days"], fc["rolling_windows"])
    df = add_regime_features(df)
    df = build_all_targets(df, horizons=cfg["horizons"])
    return df


def _feature_cols(df: pd.DataFrame) -> List[str]:
    target_prefixes = ("direction_", "log_return_")
    return [
        c for c in df.columns
        if c not in _OHLCV_COLS and not any(c.startswith(p) for p in target_prefixes)
    ]


def _make_direction_model(model_type: str, cfg: dict):
    if model_type == "xgboost":
        return XGBoostDirectionModel(**cfg["models"]["xgboost"])
    return DirectionModel(**cfg["models"]["logistic"])


def _plot_equity_curve(
    preds_df: pd.DataFrame, horizon: int, fees_bps: float, output_dir: Path, model_type: str
) -> None:
    position = (preds_df["y_prob"] >= 0.5).astype(float).values
    prev_pos = np.concatenate([[0.0], position[:-1]])
    fee_cost = np.abs(position - prev_pos) * (fees_bps / 10_000)
    pnl = position * preds_df["y_true_ret"].values - fee_cost
    bh_pnl = preds_df["y_true_ret"].values

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(preds_df.index, np.exp(np.cumsum(pnl)),
            label=f"Strategy/{model_type} ({horizon}d)", linewidth=1.5)
    ax.plot(preds_df.index, np.exp(np.cumsum(bh_pnl)),
            label="Buy & Hold", linewidth=1.5, linestyle="--")
    ax.axhline(1.0, color="gray", linewidth=0.8, linestyle=":")
    ax.set_title(f"{horizon}d Horizon — Equity Curve ({model_type}, net {fees_bps}bps/trade)")
    ax.set_ylabel("Growth of $1")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = output_dir / f"equity_curve_{horizon}d_{model_type}.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    logger.info("Saved equity curve -> %s", path)


def run_horizon(
    df: pd.DataFrame,
    horizon: int,
    cfg: dict,
    output_dir: Path,
    model_type: str = "xgboost",
) -> None:
    """Run walk-forward CV for a single forecast horizon."""
    dir_col = f"direction_{horizon}d"
    ret_col = f"log_return_{horizon}d"
    feat_cols = _feature_cols(df)

    df_clean = df.dropna(subset=feat_cols + [dir_col]).copy()
    logger.info("Horizon %dd — %d usable rows after NaN drop", horizon, len(df_clean))

    cv = WalkForwardCV(
        n_splits=cfg["evaluation"]["n_splits"],
        train_min_days=cfg["evaluation"]["train_min_days"],
        test_days=cfg["evaluation"]["test_days"],
        purge_days=horizon,
    )

    fold_results, all_preds = [], []
    last_dir_model, last_X_test = None, None

    for fold_i, (train_idx, test_idx) in enumerate(cv.split(df_clean)):
        X_tr = df_clean.loc[train_idx, feat_cols]
        y_tr_dir = df_clean.loc[train_idx, dir_col]
        y_tr_ret = df_clean.loc[train_idx, ret_col]
        X_te = df_clean.loc[test_idx, feat_cols]
        y_te_dir = df_clean.loc[test_idx, dir_col]
        y_te_ret = df_clean.loc[test_idx, ret_col]

        medians = X_tr.median()
        X_tr, X_te = X_tr.fillna(medians), X_te.fillna(medians)

        dir_model = _make_direction_model(model_type, cfg).fit(X_tr, y_tr_dir)
        quant_model = QuantileModel(cfg["models"]["quantile"]["quantiles"]).fit(X_tr, y_tr_ret)

        y_prob = dir_model.predict_proba(X_te)
        q_df = quant_model.predict_as_df(X_te)

        metrics = evaluate_fold(y_te_dir.values, y_prob, y_te_ret.values, cfg["fees_bps"])
        metrics["fold"] = fold_i + 1
        fold_results.append(metrics)
        logger.info(
            "  Fold %d — acc=%.3f  brier=%.3f  sharpe=%.2f  trades=%d  best_iter=%s",
            fold_i + 1, metrics["dir_accuracy"], metrics["brier"],
            metrics["sharpe"], int(metrics["n_trades"]),
            getattr(dir_model, "best_iteration_", "n/a"),
        )

        fold_preds = pd.DataFrame({
            "y_true_dir": y_te_dir.values,
            "y_true_ret": y_te_ret.values,
            "y_prob": y_prob,
        }, index=test_idx).join(q_df)
        all_preds.append(fold_preds)
        last_dir_model, last_X_test = dir_model, X_te

    summary = summarize_folds(fold_results)
    print(f"\n{'='*60}\nHorizon: {horizon}d [{model_type}] — Walk-Forward Summary\n{'='*60}")
    print(summary.to_string())

    preds_df = pd.concat(all_preds).sort_index()
    preds_df.to_parquet(output_dir / f"predictions_{horizon}d_{model_type}.parquet")
    _plot_equity_curve(preds_df, horizon, cfg["fees_bps"], output_dir, model_type)

    if model_type == "xgboost" and last_dir_model is not None:
        importance = run_shap(last_dir_model, last_X_test, output_dir, f"{horizon}d")
        if not importance.empty:
            print(f"\nTop 10 features ({horizon}d):")
            print(importance.head(10).to_string())


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 2 crypto prediction pipeline")
    parser.add_argument("--asset", default="BTC/USDT")
    parser.add_argument("--horizon", type=int, default=None,
                        help="1, 7, or 30. Omit for all.")
    parser.add_argument("--model", default="xgboost", choices=["xgboost", "logistic"],
                        help="Direction model to use (default: xgboost)")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--config", default="config/settings.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    horizons = [args.horizon] if args.horizon else cfg["horizons"]

    output_dir = Path("outputs") / args.asset.replace("/", "_")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Building dataset for %s...", args.asset)
    df = build_dataset(cfg, args.asset, refresh=args.refresh)
    logger.info("Dataset: %d rows x %d columns", *df.shape)

    for h in horizons:
        logger.info("\n--- Horizon %dd [%s] ---", h, args.model)
        run_horizon(df, h, cfg, output_dir, model_type=args.model)

    logger.info("Done. Results in %s/", output_dir)


if __name__ == "__main__":
    main()
