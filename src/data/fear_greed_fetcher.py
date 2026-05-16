"""Fetches Fear & Greed Index historical data from alternative.me."""
import logging
from datetime import datetime

import pandas as pd
import requests

logger = logging.getLogger(__name__)

_API_URL = "https://api.alternative.me/fng/"


class FearGreedFetcher:
    """Fetches historical Crypto Fear & Greed Index from the free alternative.me API.

    The index ranges 0–100: extreme fear (0–25), fear (26–45),
    neutral (46–55), greed (56–75), extreme greed (76–100).

    Example:
        fetcher = FearGreedFetcher()
        df = fetcher.fetch(limit=365)
    """

    def fetch(self, limit: int = 365) -> pd.DataFrame:
        """Fetch historical Fear & Greed Index values.

        Args:
            limit: Number of days of history to retrieve (free tier max: 365)

        Returns:
            DataFrame with columns [fear_greed, fg_label] indexed by tz-naive UTC date,
            sorted ascending

        Raises:
            requests.HTTPError: If the API request fails
            ValueError: If the API returns an unexpected payload
        """
        logger.info("Fetching %d days of Fear & Greed Index", limit)
        response = requests.get(_API_URL, params={"limit": limit}, timeout=15)
        response.raise_for_status()

        payload = response.json()
        if "data" not in payload:
            raise ValueError(f"Unexpected API response — missing 'data' key: {payload}")

        rows = [
            {
                "date": pd.Timestamp(datetime.utcfromtimestamp(int(r["timestamp"]))).normalize(),
                "fear_greed": int(r["value"]),
                "fg_label": r["value_classification"],
            }
            for r in payload["data"]
        ]

        df = pd.DataFrame(rows).set_index("date").sort_index()
        logger.info("Fetched %d Fear & Greed rows", len(df))
        return df
