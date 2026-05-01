"""Purged expanding-window walk-forward cross-validation."""
import logging
from typing import Iterator, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class WalkForwardCV:
    """Expanding-window walk-forward CV with a purge gap between train and test.

    The purge gap (set equal to the forecast horizon) prevents label leakage:
    if a 7-day return target at train row t overlaps with the test window,
    that row is excluded from the training set.

    Produces `n_splits` folds where:
      - Training expands from the start of the series to just before the test window
      - Test window is a fixed-size block that slides forward each fold
      - A gap of `purge_days` rows sits between train end and test start

    Example:
        cv = WalkForwardCV(n_splits=5, train_min_days=200, test_days=60, purge_days=7)
        for train_idx, test_idx in cv.split(df):
            X_train, X_test = df.loc[train_idx, features], df.loc[test_idx, features]
    """

    def __init__(
        self,
        n_splits: int = 5,
        train_min_days: int = 200,
        test_days: int = 60,
        purge_days: int = 1,
    ):
        """
        Args:
            n_splits: Number of CV folds
            train_min_days: Minimum training window size (rows)
            test_days: Size of each test window (rows)
            purge_days: Gap between train end and test start. Should equal the
                        forecast horizon to prevent target-feature leakage.
        """
        self.n_splits = n_splits
        self.train_min_days = train_min_days
        self.test_days = test_days
        self.purge_days = purge_days

    def split(self, df: pd.DataFrame) -> Iterator[Tuple[pd.Index, pd.Index]]:
        """Generate (train_index, test_index) pairs in chronological order.

        Args:
            df: DataFrame sorted ascending by date

        Yields:
            Tuples of (train_index, test_index) — both are pd.Index objects
            pointing into df's index

        Raises:
            ValueError: If df is too short for the requested CV configuration
        """
        n = len(df)
        required = self.train_min_days + self.purge_days + self.test_days * self.n_splits
        if n < required:
            raise ValueError(
                f"Dataset has {n} rows but CV needs at least {required} "
                f"({self.n_splits} folds × {self.test_days} test days + "
                f"{self.train_min_days} min train + {self.purge_days} purge). "
                "Reduce n_splits, test_days, or train_min_days in settings.yaml."
            )

        for i in range(self.n_splits):
            test_end = n - (self.n_splits - 1 - i) * self.test_days
            test_start = test_end - self.test_days
            train_end = test_start - self.purge_days
            logger.debug(
                "Fold %d/%d — train [0:%d], purge [%d:%d], test [%d:%d]",
                i + 1, self.n_splits,
                train_end, train_end, test_start, test_start, test_end,
            )
            yield df.index[:train_end], df.index[test_start:test_end]
