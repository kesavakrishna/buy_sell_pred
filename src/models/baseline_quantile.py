"""Quantile regression baseline for log-return confidence intervals."""
import logging
from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.linear_model import QuantileRegressor
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class QuantileModel:
    """Multi-quantile linear regression for predicting log-return ranges.

    Fits one QuantileRegressor per quantile level. The q10/q90 predictions
    form a calibrated confidence interval around the q50 (median) estimate.

    Example:
        model = QuantileModel(quantiles=[0.1, 0.5, 0.9])
        model.fit(X_train, y_train_log_return)
        df_intervals = model.predict_as_df(X_test)
        # columns: q10, q50, q90 — log-return predictions
    """

    def __init__(self, quantiles: List[float] = [0.1, 0.5, 0.9]):
        """
        Args:
            quantiles: Quantile levels to fit (e.g. [0.1, 0.5, 0.9])
        """
        self.quantiles = quantiles
        self._scaler = StandardScaler()
        self._models: Dict[float, QuantileRegressor] = {
            q: QuantileRegressor(quantile=q, alpha=0.0, solver="highs")
            for q in quantiles
        }

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> "QuantileModel":
        """Fit scaler and all quantile regressors. Rows with NaN targets are dropped.

        Args:
            X_train: Feature DataFrame
            y_train: Log-return target (continuous; NaN rows are excluded)

        Returns:
            self
        """
        mask = ~np.isnan(y_train.values.astype(float))
        X_arr = self._scaler.fit_transform(X_train.values.astype(float))
        y_arr = y_train.values[mask]
        for q, model in self._models.items():
            model.fit(X_arr[mask], y_arr)
        logger.debug("QuantileModel fitted on %d samples for quantiles %s", mask.sum(), self.quantiles)
        return self

    def predict(self, X_test: pd.DataFrame) -> Dict[float, np.ndarray]:
        """Predict log-return quantiles.

        Args:
            X_test: Feature DataFrame (same columns as X_train)

        Returns:
            Dict mapping quantile level → 1-D prediction array
        """
        X_arr = self._scaler.transform(X_test.values.astype(float))
        return {q: model.predict(X_arr) for q, model in self._models.items()}

    def predict_as_df(self, X_test: pd.DataFrame) -> pd.DataFrame:
        """Predict quantiles and return as a DataFrame.

        Args:
            X_test: Feature DataFrame

        Returns:
            DataFrame with columns 'q10', 'q50', 'q90' (or matching quantile levels),
            indexed by X_test.index
        """
        preds = self.predict(X_test)
        return pd.DataFrame(
            {f"q{int(q * 100)}": v for q, v in preds.items()},
            index=X_test.index,
        )
