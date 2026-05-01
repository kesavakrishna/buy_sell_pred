"""Lag returns, rolling statistics, and volume features."""
import logging
from typing import List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def add_lag_returns(df: pd.DataFrame, lags: List[int] = [1, 2, 3, 7, 14]) -> pd.DataFrame:
    """Add lagged log-return features.

    'return_1d' is yesterday's 1-day log return (already observed at time t).

    Args:
        df: DataFrame with 'close' column
        lags: How many days back to shift the 1-day log return

    Returns:
        Copy of df with 'return_{lag}d' columns added
    """
    out = df.copy()
    log_ret = np.log(out["close"] / out["close"].shift(1))
    for lag in lags:
        out[f"return_{lag}d"] = log_ret.shift(lag - 1)
    return out


def add_volume_features(df: pd.DataFrame, windows: List[int] = [7, 14, 30]) -> pd.DataFrame:
    """Add log volume and rolling volume ratio features.

    Args:
        df: DataFrame with 'volume' column
        windows: Rolling window sizes in days

    Returns:
        Copy of df with 'log_volume' and 'vol_ratio_{w}d' columns added
    """
    out = df.copy()
    out["log_volume"] = np.log1p(out["volume"])
    for w in windows:
        avg = out["volume"].rolling(w).mean().replace(0, np.nan)
        out[f"vol_ratio_{w}d"] = out["volume"] / avg
    return out


def add_rolling_return_stats(df: pd.DataFrame, windows: List[int] = [7, 14, 30]) -> pd.DataFrame:
    """Add rolling mean and standard deviation of log returns.

    Args:
        df: DataFrame with 'close' column
        windows: Rolling window sizes in days

    Returns:
        Copy of df with 'ret_mean_{w}d' and 'ret_std_{w}d' columns added
    """
    out = df.copy()
    log_ret = np.log(out["close"] / out["close"].shift(1))
    for w in windows:
        out[f"ret_mean_{w}d"] = log_ret.rolling(w).mean()
        out[f"ret_std_{w}d"] = log_ret.rolling(w).std()
    return out


def build_lag_features(
    df: pd.DataFrame,
    lag_days: List[int] = [1, 2, 3, 7, 14],
    rolling_windows: List[int] = [7, 14, 30],
) -> pd.DataFrame:
    """Apply all lag-based features.

    Args:
        df: DataFrame with OHLCV columns
        lag_days: Lag periods for return features
        rolling_windows: Window sizes for rolling stats and volume ratios

    Returns:
        DataFrame with all lag features appended
    """
    df = add_lag_returns(df, lag_days)
    df = add_volume_features(df, rolling_windows)
    df = add_rolling_return_stats(df, rolling_windows)
    logger.debug("Lag features built: %d columns total", df.shape[1])
    return df
