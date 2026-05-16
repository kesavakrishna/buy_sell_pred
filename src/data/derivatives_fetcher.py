"""Fetches Binance Futures derivatives data: funding rate, open interest, long/short ratio.

All endpoints are public — no API key required.

Binance API constraints discovered empirically:
  - Funding rate: startTime supported, full multi-year history available.
  - Open interest (daily): startTime rejected (400). Max 30 days without startTime.
  - Long/short ratio (daily): same constraint as OI — 30 days max.

OI and LS are fetched for the available window (30 days) and joined via left-join.
Rows with no coverage are filled with neutral defaults in build_derivatives_features().
"""
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger(__name__)

_BASE = "https://fapi.binance.com"


class DerivativesFetcher:
    """Fetches Binance Futures positioning data and caches to Parquet.

    Signals:
      - Funding rate (full history): 8h cost of holding longs.
        Persistently positive = market is paying to be long = crowded.
        Extreme positive funding is historically a contrarian bearish signal.
      - Open interest (last 30 days): USD value of open futures contracts.
        Rising OI + rising price = trend has conviction.
      - Long/short ratio (last 30 days): fraction of accounts net long.
        Extreme readings are contrarian — crowded trades tend to unwind.

    Example:
        fetcher = DerivativesFetcher()
        df = fetcher.fetch_and_save("BTC/USDT", "data/")
    """

    def __init__(self, timeout: int = 15):
        self._session = requests.Session()
        self._session.headers["Accept"] = "application/json"
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_funding_rate(self, symbol: str, days_back: int = 1000) -> pd.DataFrame:
        """Fetch historical 8-hour funding rates, resampled to daily mean.

        Full multi-year history available via Binance /fapi/v1/fundingRate.

        Args:
            symbol: Trading pair, e.g. 'BTC/USDT'
            days_back: Calendar days of history to fetch

        Returns:
            DataFrame with 'funding_rate' column indexed by tz-naive UTC date
        """
        sym = self._futures_symbol(symbol)
        since_ms = self._since_ms(days_back)
        records: list = []
        start = since_ms
        while True:
            batch = self._get("/fapi/v1/fundingRate", {"symbol": sym, "startTime": start, "limit": 1000})
            if not batch:
                break
            records.extend(batch)
            start = int(batch[-1]["fundingTime"]) + 1
            if len(batch) < 1000:
                break

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["fundingTime"].astype("int64"), unit="ms").dt.normalize()
        df["funding_rate"] = df["fundingRate"].astype(float)
        daily = df.groupby("date")["funding_rate"].mean().to_frame().sort_index()
        logger.info("Funding rate: %d days for %s", len(daily), symbol)
        return daily

    def fetch_open_interest(self, symbol: str) -> pd.DataFrame:
        """Fetch recent open interest history (Binance caps at ~30 daily bars).

        Args:
            symbol: Trading pair, e.g. 'BTC/USDT'

        Returns:
            DataFrame with 'open_interest' column indexed by tz-naive UTC date
        """
        sym = self._futures_symbol(symbol)
        data = self._get("/futures/data/openInterestHist", {"symbol": sym, "period": "1d", "limit": 500})
        if not data:
            return pd.DataFrame(columns=["open_interest"])
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["timestamp"].astype("int64"), unit="ms").dt.normalize()
        df["open_interest"] = df["sumOpenInterestValue"].astype(float)
        daily = df.set_index("date")[["open_interest"]].sort_index()
        daily = daily[~daily.index.duplicated(keep="last")]
        logger.info("Open interest: %d days for %s (Binance caps at ~30)", len(daily), symbol)
        return daily

    def fetch_long_short_ratio(self, symbol: str) -> pd.DataFrame:
        """Fetch recent long/short ratio history (Binance caps at ~30 daily bars).

        Args:
            symbol: Trading pair, e.g. 'BTC/USDT'

        Returns:
            DataFrame with 'ls_ratio' column indexed by tz-naive UTC date
        """
        sym = self._futures_symbol(symbol)
        data = self._get(
            "/futures/data/globalLongShortAccountRatio",
            {"symbol": sym, "period": "1d", "limit": 500},
        )
        if not data:
            return pd.DataFrame(columns=["ls_ratio"])
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["timestamp"].astype("int64"), unit="ms").dt.normalize()
        df["ls_ratio"] = df["longShortRatio"].astype(float)
        daily = df.set_index("date")[["ls_ratio"]].sort_index()
        daily = daily[~daily.index.duplicated(keep="last")]
        logger.info("Long/short ratio: %d days for %s (Binance caps at ~30)", len(daily), symbol)
        return daily

    def fetch_and_save(self, symbol: str, data_dir: str, days_back: int = 1000) -> pd.DataFrame:
        """Fetch all available derivatives signals and cache to Parquet.

        Each signal is fetched independently — partial failures are logged and
        skipped so that a working signal is never lost due to a failing one.

        Args:
            symbol: Trading pair, e.g. 'BTC/USDT'
            data_dir: Directory to write Parquet
            days_back: Calendar days of history for funding rate

        Returns:
            Combined DataFrame (funding_rate always present; OI and LS where available)
        """
        frames: list = []

        try:
            frames.append(self.fetch_funding_rate(symbol, days_back))
        except Exception as exc:
            logger.warning("Funding rate fetch failed for %s: %s", symbol, exc)

        try:
            frames.append(self.fetch_open_interest(symbol))
        except Exception as exc:
            logger.warning("Open interest fetch failed for %s: %s", symbol, exc)

        try:
            frames.append(self.fetch_long_short_ratio(symbol))
        except Exception as exc:
            logger.warning("Long/short ratio fetch failed for %s: %s", symbol, exc)

        if not frames:
            raise RuntimeError(f"All derivatives fetches failed for {symbol}")

        df = pd.concat(frames, axis=1).sort_index()
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        path = self._parquet_path(symbol, data_dir)
        df.to_parquet(path)
        logger.info("Saved derivatives (%d rows, columns: %s) -> %s", len(df), list(df.columns), path)
        return df

    def load_cached(self, symbol: str, data_dir: str) -> pd.DataFrame:
        """Load cached derivatives Parquet.

        Raises:
            FileNotFoundError: If no cache exists
        """
        path = self._parquet_path(symbol, data_dir)
        if not path.exists():
            raise FileNotFoundError(f"No derivatives cache at {path}. Run fetch_and_save first.")
        return pd.read_parquet(path)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _futures_symbol(pair: str) -> str:
        return pair.replace("/", "")

    @staticmethod
    def _since_ms(days_back: int) -> int:
        dt = datetime.now(timezone.utc) - timedelta(days=days_back)
        return int(dt.timestamp() * 1000)

    def _get(self, path: str, params: dict) -> list:
        resp = self._session.get(_BASE + path, params=params, timeout=self._timeout)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _parquet_path(symbol: str, data_dir: str) -> Path:
        return Path(data_dir) / f"{symbol.replace('/', '_')}_derivatives.parquet"
