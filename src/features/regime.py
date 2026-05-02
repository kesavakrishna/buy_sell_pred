"""Market regime features derived from trend structure."""
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def add_regime_features(
    df: pd.DataFrame,
    trend_ema: int = 200,
    fast_ema: int = 50,
    slow_ema: int = 200,
) -> pd.DataFrame:
    """Add binary regime flags based on EMA structure.

    These give the model clean split points on market regime without
    requiring it to discover the threshold implicitly from continuous EMA ratios.

    Args:
        df: DataFrame with 'close' column
        trend_ema: EMA period for bull/bear regime flag
        fast_ema: Fast EMA for golden/death cross signal
        slow_ema: Slow EMA for golden/death cross signal

    Returns:
        Copy of df with added columns:
            - 'bull_regime': 1 if close > EMA(trend_ema), else 0
            - 'golden_cross': 1 if EMA(fast) > EMA(slow), else 0
            - 'trend_strength': (EMA_fast - EMA_slow) / EMA_slow, continuous version
    """
    out = df.copy()
    ema_trend = out["close"].ewm(span=trend_ema, adjust=False).mean()
    ema_fast = out["close"].ewm(span=fast_ema, adjust=False).mean()
    ema_slow = out["close"].ewm(span=slow_ema, adjust=False).mean()

    out["bull_regime"] = (out["close"] > ema_trend).astype(float)
    out["golden_cross"] = (ema_fast > ema_slow).astype(float)
    out["trend_strength"] = (ema_fast - ema_slow) / ema_slow.replace(0, np.nan)

    logger.debug("Regime features added: bull_regime, golden_cross, trend_strength")
    return out
