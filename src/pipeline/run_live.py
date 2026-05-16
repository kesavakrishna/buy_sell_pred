"""Live vol-prediction logger and evaluator.

Run once per day to log today's vol-regime prediction. After 7+ days from the
first prediction, --eval compares logged predictions against actual realized vol.

How it works
------------
1. Fetches latest OHLCV + derivatives (always refreshes — needs today's close).
2. Trains the vol XGBoost model on all rows where the 7d future vol is known
   (i.e., every bar except the last 7).
3. Predicts P(high_vol) for today's bar (whose future vol is not yet known).
4. Pickles the trained model to data/model_snapshots/{date}_{asset}.pkl.
5. Appends one row to data/live_predictions.parquet, including a snapshot of
   the top ~12 features the model saw and the path to the saved model.

--eval joins the log against actuals, then reports:
- Hit rate and Brier score
- Strategy Sharpe (vol-sizing) vs buy-and-hold
- Calibration table (mean predicted P vs actual high-vol rate per decile bin)
- Last 10 resolved predictions with feature snapshot

Usage
-----
    python -m src.pipeline.run_live                      # predict and log
    python -m src.pipeline.run_live --asset ETH/USDT
    python -m src.pipeline.run_live --eval               # evaluate past predictions
    python -m src.pipeline.run_live --eval --min-days 14 # require 14 days before eval
"""
import argparse
import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluation.metrics import brier_score, directional_accuracy, sized_sharpe
from src.features.targets import build_all_vol_targets
from src.models.xgboost_direction import XGBoostDirectionModel
from src.pipeline.run import _feature_cols, build_dataset, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_HORIZON = 7          # days — 7d vol is the best-performing horizon from CV
_LOG_PATH = Path("data/live_predictions.parquet")
_MODEL_SNAPSHOT_DIR = Path("data/model_snapshots")

# Snapshotted alongside each prediction. Top SHAP features across Phase 3B/4/5
# plus regime + funding context. Locking these in at prediction time protects
# against later feature-engineering changes invalidating audits.
_SNAPSHOT_FEATURES = [
    "trend_strength", "close_vs_ema200",
    f"vol_{_HORIZON}d", "vol_14d", "vol_30d", "vol_3b",
    "funding_7d_mean", "funding_30d_mean",
    "hl_range", "rsi", "fear_greed", "return_7d",
]


def _safe_get(row: pd.DataFrame, col: str) -> float:
    return float(row[col].iloc[0]) if col in row.columns else float("nan")


# ---------------------------------------------------------------------------
# Predict
# ---------------------------------------------------------------------------

def predict_today(cfg: dict, asset: str) -> dict:
    """Train vol model on all known history and predict for today's bar.

    Returns a dict with one row's worth of log data.
    """
    bars_per_day = cfg["data"].get("bars_per_day", 1)

    logger.info("Fetching latest data for %s...", asset)
    df = build_dataset(cfg, asset, refresh=True)
    df = build_all_vol_targets(df, horizons=[_HORIZON], bars_per_day=bars_per_day)

    vol_col = f"future_vol_{_HORIZON}d"
    feat_cols = _feature_cols(df)

    # Training rows: all bars where the 7d future vol is known (not NaN)
    train_df = df.dropna(subset=feat_cols + [vol_col]).copy()
    if len(train_df) < 100:
        raise RuntimeError(f"Only {len(train_df)} training rows — too few to train.")

    X_tr = train_df[feat_cols].fillna(train_df[feat_cols].median())
    vol_tr = train_df[vol_col]

    # Binarize with training median — same approach as CV loop
    vol_threshold = float(vol_tr.median())
    y_tr_vol = (vol_tr > vol_threshold).astype(float)

    logger.info("Training vol model on %d rows (vol_threshold=%.4f)...", len(X_tr), vol_threshold)
    model = XGBoostDirectionModel(**cfg["models"]["xgboost"]).fit(X_tr, y_tr_vol)

    # Today = the last bar in the dataset (future vol not yet known)
    today_row = df.iloc[[-1]]
    today_date = today_row.index[0]
    X_today = today_row[feat_cols].fillna(train_df[feat_cols].median())

    p_high_vol = float(model.predict_proba(X_today)[0])
    implied_size = 1.0 - p_high_vol

    feature_snapshot = {f"feat_{col}": _safe_get(today_row, col) for col in _SNAPSHOT_FEATURES}

    asset_slug = asset.replace("/", "_")
    snapshot_date = pd.Timestamp(today_date).date()
    snapshot_path = _MODEL_SNAPSHOT_DIR / f"{snapshot_date}_{asset_slug}.pkl"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    with open(snapshot_path, "wb") as f:
        pickle.dump({
            "model": model,
            "feat_cols": feat_cols,
            "vol_threshold": vol_threshold,
            "train_rows": len(X_tr),
            "train_median": train_df[feat_cols].median().to_dict(),
            "snapshot_date": str(snapshot_date),
            "asset": asset,
        }, f)
    logger.info("Saved model snapshot -> %s", snapshot_path)

    record = {
        "date": pd.Timestamp(today_date).normalize(),
        "asset": asset,
        "horizon": _HORIZON,
        "p_high_vol": p_high_vol,
        "implied_size": implied_size,
        "vol_threshold": vol_threshold,
        "train_rows": len(X_tr),
        "model_snapshot": str(snapshot_path).replace("\\", "/"),
        **feature_snapshot,
    }

    logger.info(
        "Prediction for %s: P(high_vol)=%.3f  implied_size=%.3f  "
        "trend_strength=%.4f  trailing_vol=%.4f",
        snapshot_date, p_high_vol, implied_size,
        feature_snapshot["feat_trend_strength"], feature_snapshot[f"feat_vol_{_HORIZON}d"],
    )
    return record


def log_prediction(record: dict, log_path: Path = _LOG_PATH) -> None:
    """Append one prediction row to the log Parquet file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    new_row = pd.DataFrame([record]).set_index("date")

    if log_path.exists():
        existing = pd.read_parquet(log_path)
        # Avoid duplicate entries for the same date + asset
        key = (new_row.index[0], record["asset"])
        mask = ~((existing.index == key[0]) & (existing["asset"] == key[1]))
        combined = pd.concat([existing[mask], new_row]).sort_index()
    else:
        combined = new_row

    combined.to_parquet(log_path)
    logger.info("Logged prediction to %s (%d total rows)", log_path, len(combined))


# ---------------------------------------------------------------------------
# Evaluate
# ---------------------------------------------------------------------------

def evaluate(cfg: dict, asset: str, min_resolved_days: int = 7) -> None:
    """Compare logged predictions against actual realized vol outcomes.

    Only evaluates predictions where the outcome window has already closed
    (i.e., prediction date + horizon days ≤ today).
    """
    if not _LOG_PATH.exists():
        logger.error("No prediction log found at %s. Run without --eval first.", _LOG_PATH)
        return

    log = pd.read_parquet(_LOG_PATH)
    log = log[log["asset"] == asset].copy()
    if log.empty:
        logger.error("No predictions logged for %s.", asset)
        return

    logger.info("Fetching latest prices to compute actual vol outcomes...")
    df = build_dataset(cfg, asset, refresh=True)
    bars_per_day = cfg["data"].get("bars_per_day", 1)
    df = build_all_vol_targets(df, horizons=[_HORIZON], bars_per_day=bars_per_day)

    vol_col = f"future_vol_{_HORIZON}d"
    # Join actual future vol onto the prediction log
    actual_vol = df[[vol_col]].rename(columns={vol_col: "actual_future_vol"})
    log = log.join(actual_vol, how="left")

    # Only evaluate rows where the outcome window has closed and vol is known
    today = pd.Timestamp.utcnow().normalize().tz_localize(None)
    cutoff = today - pd.Timedelta(days=_HORIZON)
    resolved = log[log.index <= cutoff].dropna(subset=["actual_future_vol"]).copy()

    if len(resolved) < min_resolved_days:
        logger.info(
            "Only %d resolved predictions (need %d). Come back in %d days.",
            len(resolved), min_resolved_days, min_resolved_days - len(resolved),
        )
        return

    # Binarize actual vol using the logged threshold (same threshold used at prediction time)
    resolved["actual_high_vol"] = (resolved["actual_future_vol"] > resolved["vol_threshold"]).astype(float)
    resolved["predicted_high_vol"] = (resolved["p_high_vol"] >= 0.5).astype(float)

    vol_acc = directional_accuracy(resolved["actual_high_vol"].values, resolved["p_high_vol"].values)
    vol_brier = brier_score(resolved["actual_high_vol"].values, resolved["p_high_vol"].values)

    # Fetch actual log returns for Sharpe computation
    ret_col = f"log_return_{_HORIZON}d"
    if ret_col in df.columns:
        actual_ret = df[[ret_col]].rename(columns={ret_col: "log_return"})
        resolved = resolved.join(actual_ret, how="left").dropna(subset=["log_return"])

        bars_per_day = cfg["data"].get("bars_per_day", 1)
        annualize = int(252 * bars_per_day)
        size = resolved["implied_size"].values
        ret = resolved["log_return"].values
        strategy_sharpe = sized_sharpe(size, ret, cfg["fees_bps"], annualize)
        bh_sharpe = sized_sharpe(np.ones(len(ret)), ret, 0, annualize)
    else:
        strategy_sharpe = float("nan")
        bh_sharpe = float("nan")

    print(f"\n{'='*60}")
    print(f"Live Prediction Evaluation — {asset} ({_HORIZON}d horizon)")
    print(f"{'='*60}")
    print(f"Resolved predictions : {len(resolved)}")
    print(f"Date range           : {resolved.index.min().date()} → {resolved.index.max().date()}")
    print(f"Vol accuracy         : {vol_acc:.1%}")
    print(f"Brier score          : {vol_brier:.4f}")
    print(f"Strategy Sharpe      : {strategy_sharpe:.2f}")
    print(f"Buy & Hold Sharpe    : {bh_sharpe:.2f}")

    # Calibration: if predictions are well-calibrated, mean(P) in each bin
    # should match the actual high-vol rate. Large gaps indicate Platt scaling
    # would help.
    n_bins = min(5, max(2, len(resolved) // 4))
    try:
        bins = pd.qcut(resolved["p_high_vol"], q=n_bins, duplicates="drop")
        cal = resolved.groupby(bins, observed=True).agg(
            n=("p_high_vol", "size"),
            mean_pred=("p_high_vol", "mean"),
            actual_rate=("actual_high_vol", "mean"),
        )
        cal["gap"] = cal["actual_rate"] - cal["mean_pred"]
        print(f"\nCalibration ({n_bins} bins, gap = actual − predicted):")
        print(cal.round(3).to_string())
    except ValueError:
        print("\nCalibration: not enough variance in p_high_vol to bin.")

    # Show the most recent feature snapshots so drift is visible at a glance
    feat_cols_logged = [c for c in resolved.columns if c.startswith("feat_")]
    print(f"\nResolved prediction log (last 10):")
    show_cols = ["p_high_vol", "implied_size", "actual_high_vol"] + feat_cols_logged[:4]
    show_cols = [c for c in show_cols if c in resolved.columns]
    print(resolved[show_cols].tail(10).round(4).to_string())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Daily vol prediction logger")
    parser.add_argument("--asset", default="BTC/USDT")
    parser.add_argument("--eval", action="store_true", help="Evaluate past predictions")
    parser.add_argument("--min-days", type=int, default=7,
                        help="Minimum resolved predictions before --eval reports (default 7)")
    parser.add_argument("--config", default="config/settings.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)

    if args.eval:
        evaluate(cfg, args.asset, min_resolved_days=args.min_days)
    else:
        record = predict_today(cfg, args.asset)
        log_prediction(record)
        print(
            f"\nLogged: P(high_vol)={record['p_high_vol']:.3f}  "
            f"size={record['implied_size']:.3f}  "
            f"(vol_threshold={record['vol_threshold']:.4f})"
        )
        print(f"Run --eval in {_HORIZON}+ days to compare against actual outcomes.")


if __name__ == "__main__":
    main()
