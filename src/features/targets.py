"""Target variable construction for multi-horizon directional and vol prediction."""
import logging
from typing import List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def add_direction_target(
    df: pd.DataFrame,
    horizon: int,
    threshold: float = 0.0,
) -> pd.DataFrame:
    """Add binary direction label and raw log-return for a given horizon.

    Rows within `horizon` days of the end of the DataFrame will have NaN targets
    because the future price is unknown. These rows must be excluded from training.

    Args:
        df: DataFrame with 'close' column, sorted ascending by date
        horizon: Forecast horizon in days
        threshold: Log-return threshold for classifying as 'up' (default 0 = any gain)

    Returns:
        Copy of df with columns:
            - 'log_return_{horizon}d': raw H-day log return (NaN for last H rows)
            - 'direction_{horizon}d': 1.0 if return > threshold else 0.0 (NaN for last H rows)
    """
    out = df.copy()
    log_ret = np.log(out["close"].shift(-horizon) / out["close"])
    out[f"log_return_{horizon}d"] = log_ret
    direction = (log_ret > threshold).astype(float)
    direction[log_ret.isna()] = np.nan
    out[f"direction_{horizon}d"] = direction
    return out


def build_all_targets(
    df: pd.DataFrame,
    horizons: List[int] = [1, 7, 30],
    threshold: float = 0.0,
) -> pd.DataFrame:
    """Add direction and log-return targets for every horizon.

    Args:
        df: DataFrame with 'close' column
        horizons: List of forecast horizons in days
        threshold: Log-return threshold for 'up' classification

    Returns:
        DataFrame with target columns for each horizon appended
    """
    for h in horizons:
        df = add_direction_target(df, h, threshold)
    logger.debug("Targets built for horizons %s", horizons)
    return df


def add_vol_target(df: pd.DataFrame, horizon: int, bars_per_day: int = 1) -> pd.DataFrame:
    """Add annualized future realized volatility target for a given horizon.

    Vol = std of bar log-returns over the next H bars × sqrt(252 × bars_per_day).
    At daily (bars_per_day=1), H=1 is degenerate (std of one bar = NaN with ddof=1)
    and the vol pipeline will skip it automatically via dropna.

    The continuous vol column is named `future_vol_{H}d`. Binarization into
    high/low regime is done inside the CV loop using the training-fold median
    so there is no lookahead into the test set.

    Args:
        df: DataFrame with 'close' column, sorted ascending
        horizon: Forecast horizon in bars
        bars_per_day: Bars per calendar day for correct annualization

    Returns:
        Copy of df with 'future_vol_{horizon}d' column appended
    """
    out = df.copy()
    log_ret = np.log(out["close"] / out["close"].shift(1))
    ann = np.sqrt(252 * bars_per_day)
    future_vol = log_ret.rolling(horizon).std().shift(-horizon) * ann
    out[f"future_vol_{horizon}d"] = future_vol
    return out


def build_all_vol_targets(
    df: pd.DataFrame,
    horizons: List[int] = [7, 30],
    bars_per_day: int = 1,
) -> pd.DataFrame:
    """Add future realized vol targets for every horizon.

    Args:
        df: DataFrame with 'close' column
        horizons: List of forecast horizons in bars
        bars_per_day: Bars per calendar day for annualization

    Returns:
        DataFrame with 'future_vol_{H}d' columns appended for each horizon
    """
    for h in horizons:
        df = add_vol_target(df, h, bars_per_day)
    logger.debug("Vol targets built for horizons %s", horizons)
    return df
