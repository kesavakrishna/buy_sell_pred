"""ARCH/GARCH-motivated features for sub-daily bar frequencies.

At daily resolution these features exist but the clustering signal is weak.
At 4h resolution, vol_1b (absolute previous bar return) and hl_range become
the strongest predictors of future realized vol — this is the ARCH effect.
"""
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def build_garch_features(df: pd.DataFrame, bars_per_day: int = 6) -> pd.DataFrame:
    """Add short-lag volatility features that capture ARCH clustering effects.

    Args:
        df: DataFrame with 'close', 'high', 'low' columns
        bars_per_day: Bars per calendar day (6 for 4h, 1 for daily)

    Returns:
        Copy of df with GARCH feature columns appended:
            - abs_ret_1b: absolute log-return of the previous bar (purest ARCH feature)
            - vol_3b: trailing 3-bar realized vol (12h window at 4h)
            - hl_range: intra-bar high/low log range (range-based vol proxy)
            - avg_hl_range: rolling mean of hl_range over one day of bars
            - vol_accel: ratio of 1-day vol to 4-day vol (is short-term vol rising?)
    """
    out = df.copy()
    log_ret = np.log(out["close"] / out["close"].shift(1))

    # Absolute previous-bar return — direct ARCH(1) input
    out["abs_ret_1b"] = log_ret.shift(1).abs()

    # Very short trailing vol (3 bars = 12h at 4h, 3 days at 1d)
    out["vol_3b"] = log_ret.rolling(3).std()

    # Intra-bar high-low range: log(H/L) — range-based vol within this bar
    out["hl_range"] = np.log(out["high"] / out["low"].replace(0, np.nan))

    # Rolling average of HL range over one day of bars
    out["avg_hl_range"] = out["hl_range"].rolling(bars_per_day).mean()

    # Vol acceleration: 1d trailing vol / 4d trailing vol
    # At daily (bars_per_day=1) use abs(return) as 1-day vol proxy to avoid
    # rolling(1).std() which is always NaN with ddof=1.
    if bars_per_day > 1:
        v_1d = log_ret.rolling(bars_per_day).std()
    else:
        v_1d = log_ret.abs()
    v_4d = log_ret.rolling(max(bars_per_day * 4, 4)).std().replace(0, np.nan)
    out["vol_accel"] = (v_1d / v_4d).fillna(1.0)

    n_new = len(out.columns) - len(df.columns)
    logger.debug("GARCH features added: %d new columns", n_new)
    return out
