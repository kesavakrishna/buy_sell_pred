"""Feature engineering from Binance Futures derivatives data."""
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def build_derivatives_features(
    df: pd.DataFrame,
    deriv_df: pd.DataFrame,
    z_window: int = 30,
) -> pd.DataFrame:
    """Merge and engineer features from funding rate, open interest, and long/short ratio.

    Each raw signal is transformed into Z-scored and change-based features so the
    model sees *extremes* and *momentum*, not raw levels that change across market regimes.

    Args:
        df: Main OHLCV + indicator DataFrame indexed by tz-naive UTC date
        deriv_df: DataFrame from DerivativesFetcher with columns
                  [funding_rate, open_interest, ls_ratio]
        z_window: Rolling window (days) for Z-score normalization

    Returns:
        Copy of df with derivatives features appended.
        Rows with no derivatives coverage are forward-filled then filled with 0
        (neutral / no signal) so no rows are dropped.
    """
    out = df.join(deriv_df, how="left")

    # Forward-fill sparse data (weekends / API gaps) then default to neutral
    for col in ["funding_rate", "open_interest", "ls_ratio"]:
        if col in out.columns:
            out[col] = out[col].ffill()

    out = _add_funding_features(out, z_window)
    out = _add_oi_features(out)
    out = _add_ls_features(out, z_window)

    # Drop raw signal columns — they have limited history (OI/LS = 30 days) and
    # would create NaN-dense rows that collapse the training set via dropna.
    # Derived features above already encode what is useful.
    out = out.drop(columns=["open_interest", "ls_ratio"], errors="ignore")

    n_new = len(out.columns) - len(df.columns)
    logger.debug("Derivatives features added: %d new columns", n_new)
    return out


# ------------------------------------------------------------------
# Per-signal feature builders
# ------------------------------------------------------------------

def _add_funding_features(df: pd.DataFrame, z_window: int) -> pd.DataFrame:
    """Funding rate features.

    Funding rate is the 8-hour fee paid by longs to shorts (or vice versa).
    Persistently positive = market is paying to be long = crowded longs.
    Extreme Z-score is a contrarian signal (unwind risk is high).
    """
    if "funding_rate" not in df.columns:
        return df
    out = df.copy()
    fr = out["funding_rate"].fillna(0)
    out["funding_7d_mean"] = fr.rolling(7).mean()
    out["funding_30d_mean"] = fr.rolling(30).mean()
    roll_std = fr.rolling(z_window).std().replace(0, np.nan)
    out["funding_z"] = (fr - fr.rolling(z_window).mean()) / roll_std
    # Binary: is market in persistently bullish funding territory?
    out["funding_positive"] = (out["funding_7d_mean"] > 0).astype(float)
    return out


def _add_oi_features(df: pd.DataFrame) -> pd.DataFrame:
    """Open interest features.

    Rising OI + rising price = trend has fresh capital behind it (bullish confirmation).
    Falling OI + rising price = rally is driven by short covering, not new longs (weak).

    Binance OI history is capped at ~30 days. Rows without coverage default to 0
    (no signal) so the NaN gap does not collapse the training set via dropna.
    """
    if "open_interest" not in df.columns:
        return df
    out = df.copy()
    oi = out["open_interest"].ffill()
    log_ret = np.log(out["close"] / out["close"].shift(1)).fillna(0)
    out["oi_change_1d"] = oi.pct_change(1).clip(-1, 1).fillna(0)
    out["oi_change_7d"] = oi.pct_change(7).clip(-1, 1).fillna(0)
    out["oi_price_diverge"] = (out["oi_change_1d"] - log_ret).fillna(0)
    return out


def _add_ls_features(df: pd.DataFrame, z_window: int) -> pd.DataFrame:
    """Long/short ratio features.

    Ratio > 1 means more accounts are net long.
    Extreme Z-score means positioning is historically one-sided → contrarian signal.

    Binance LS history is capped at ~30 days. Rows without coverage default to 0.
    """
    if "ls_ratio" not in df.columns:
        return df
    out = df.copy()
    ls = out["ls_ratio"].ffill()
    roll_mean = ls.rolling(z_window).mean()
    roll_std = ls.rolling(z_window).std().replace(0, np.nan)
    out["ls_ratio_z"] = ((ls - roll_mean) / roll_std).fillna(0)
    out["ls_crowded_long"] = (out["ls_ratio_z"] > 1.5).astype(float)
    out["ls_crowded_short"] = (out["ls_ratio_z"] < -1.5).astype(float)
    return out
