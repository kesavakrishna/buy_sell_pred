"""Fetches OHLCV data from Binance via ccxt and caches to Parquet."""
import logging
from datetime import datetime, timedelta
from pathlib import Path

import ccxt
import pandas as pd

logger = logging.getLogger(__name__)

_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


class OHLCVFetcher:
    """Fetches OHLCV candles from Binance public API via ccxt.

    No API key required — uses Binance's public endpoints.
    Data is cached as Parquet for fast subsequent reads.

    Example:
        fetcher = OHLCVFetcher()
        df = fetcher.fetch_and_save("BTC/USDT", "data/", days_back=1000)
    """

    def __init__(self, exchange_id: str = "binance", timeframe: str = "1d"):
        """
        Args:
            exchange_id: ccxt exchange name (default 'binance')
            timeframe: Candle interval, e.g. '1d', '4h'
        """
        self.exchange = getattr(ccxt, exchange_id)({"enableRateLimit": True})
        self.timeframe = timeframe

    def fetch(self, symbol: str, days_back: int = 1000) -> pd.DataFrame:
        """Fetch OHLCV history for a symbol from the exchange.

        Args:
            symbol: Trading pair, e.g. 'BTC/USDT'
            days_back: Number of calendar days to fetch

        Returns:
            DataFrame with columns [open, high, low, close, volume] indexed by tz-naive UTC date
        """
        since_dt = datetime.utcnow() - timedelta(days=days_back)
        since_ms = self.exchange.parse8601(since_dt.strftime("%Y-%m-%dT00:00:00Z"))
        logger.info("Fetching %dd of %s %s from %s", days_back, symbol, self.timeframe, self.exchange.id)

        candles: list = []
        while True:
            batch = self.exchange.fetch_ohlcv(symbol, self.timeframe, since=since_ms, limit=1000)
            if not batch:
                break
            candles.extend(batch)
            since_ms = batch[-1][0] + 1
            if len(batch) < 1000:
                break

        df = pd.DataFrame(candles, columns=_COLUMNS)
        # For daily bars normalize to midnight; for sub-daily keep full timestamp so
        # each bar in a day has a unique index entry.
        ts = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_convert(None)
        df["date"] = ts.dt.normalize() if self.timeframe == "1d" else ts
        df = df.set_index("date").drop(columns=["timestamp"])
        df = df[~df.index.duplicated(keep="last")].sort_index()
        df = df.astype(float)
        logger.info("Fetched %d candles for %s", len(df), symbol)
        return df

    def fetch_and_save(self, symbol: str, data_dir: str, days_back: int = 1000) -> pd.DataFrame:
        """Fetch and cache OHLCV data to Parquet.

        Args:
            symbol: Trading pair, e.g. 'BTC/USDT'
            data_dir: Directory to write the Parquet file
            days_back: Number of calendar days to fetch

        Returns:
            DataFrame with OHLCV data
        """
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        df = self.fetch(symbol, days_back)
        path = self._parquet_path(symbol, data_dir)
        df.to_parquet(path)
        logger.info("Saved %d rows to %s", len(df), path)
        return df

    def load_cached(self, symbol: str, data_dir: str) -> pd.DataFrame:
        """Load previously cached Parquet file.

        Args:
            symbol: Trading pair, e.g. 'BTC/USDT'
            data_dir: Directory containing cached Parquet files

        Returns:
            DataFrame with OHLCV data

        Raises:
            FileNotFoundError: If no cache exists for this symbol/timeframe
        """
        path = self._parquet_path(symbol, data_dir)
        if not path.exists():
            raise FileNotFoundError(f"No cache at {path}. Run fetch_and_save first.")
        df = pd.read_parquet(path)
        logger.info("Loaded %d cached rows for %s", len(df), symbol)
        return df

    def _parquet_path(self, symbol: str, data_dir: str) -> Path:
        safe_symbol = symbol.replace("/", "_")
        return Path(data_dir) / f"{safe_symbol}_{self.timeframe}.parquet"
