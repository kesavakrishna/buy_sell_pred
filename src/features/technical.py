"""Technical indicator computation for OHLCV DataFrames."""
import logging
from typing import List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Add Relative Strength Index.

    Args:
        df: DataFrame with 'close' column
        period: Lookback period (default 14)

    Returns:
        Copy of df with 'rsi' column added
    """
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = df.copy()
    out["rsi"] = 100 - (100 / (1 + rs))
    return out


def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """Add MACD line, signal line, and histogram.

    Args:
        df: DataFrame with 'close' column
        fast: Fast EMA span
        slow: Slow EMA span
        signal: Signal EMA span

    Returns:
        Copy of df with 'macd', 'macd_signal', 'macd_hist' columns added
    """
    out = df.copy()
    ema_fast = out["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = out["close"].ewm(span=slow, adjust=False).mean()
    out["macd"] = ema_fast - ema_slow
    out["macd_signal"] = out["macd"].ewm(span=signal, adjust=False).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]
    return out


def add_bollinger_bands(df: pd.DataFrame, period: int = 20, std_mult: float = 2.0) -> pd.DataFrame:
    """Add Bollinger Band %B (position within bands) and normalized width.

    Args:
        df: DataFrame with 'close' column
        period: Rolling window period
        std_mult: Number of standard deviations for band width

    Returns:
        Copy of df with 'bb_pct_b' and 'bb_width' columns added
    """
    out = df.copy()
    mid = out["close"].rolling(period).mean()
    std = out["close"].rolling(period).std()
    upper = mid + std_mult * std
    lower = mid - std_mult * std
    band_range = (upper - lower).replace(0, np.nan)
    out["bb_pct_b"] = (out["close"] - lower) / band_range
    out["bb_width"] = band_range / mid.replace(0, np.nan)
    return out


def add_ema_ratios(df: pd.DataFrame, periods: List[int] = [9, 21, 50, 200]) -> pd.DataFrame:
    """Add close-price deviation from each EMA (as a fraction).

    Args:
        df: DataFrame with 'close' column
        periods: EMA spans to compute

    Returns:
        Copy of df with 'close_vs_ema{p}' columns (value > 0 means price above EMA)
    """
    out = df.copy()
    for p in periods:
        ema = out["close"].ewm(span=p, adjust=False).mean()
        out[f"close_vs_ema{p}"] = out["close"] / ema.replace(0, np.nan) - 1
    return out


def add_rolling_vol(df: pd.DataFrame, windows: List[int] = [7, 14, 30]) -> pd.DataFrame:
    """Add annualized realized volatility over rolling windows.

    Args:
        df: DataFrame with 'close' column
        windows: Rolling window sizes in days

    Returns:
        Copy of df with 'vol_{w}d' columns (annualized)
    """
    out = df.copy()
    log_ret = np.log(out["close"] / out["close"].shift(1))
    for w in windows:
        out[f"vol_{w}d"] = log_ret.rolling(w).std() * np.sqrt(252)
    return out


def build_technical_features(
    df: pd.DataFrame,
    rsi_period: int = 14,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    bb_period: int = 20,
    bb_std: float = 2.0,
    ema_periods: List[int] = [9, 21, 50, 200],
    vol_windows: List[int] = [7, 14, 30],
) -> pd.DataFrame:
    """Apply all technical indicators sequentially.

    Args:
        df: DataFrame with OHLCV columns

    Returns:
        DataFrame with all indicator columns appended
    """
    df = add_rsi(df, rsi_period)
    df = add_macd(df, macd_fast, macd_slow, macd_signal)
    df = add_bollinger_bands(df, bb_period, bb_std)
    df = add_ema_ratios(df, ema_periods)
    df = add_rolling_vol(df, vol_windows)
    logger.debug("Technical features built: %d columns total", df.shape[1])
    return df
