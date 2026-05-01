"""Logistic regression baseline for binary direction prediction."""
import logging
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class DirectionModel:
    """Binary direction classifier: logistic regression with standard scaling.

    Scales features on the training set and applies the same transformation
    at inference time, preventing data leakage from test rows.

    Example:
        model = DirectionModel(C=1.0)
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)  # P(up) for each row
    """

    def __init__(self, C: float = 1.0, max_iter: int = 1000):
        """
        Args:
            C: Inverse regularization strength (smaller = stronger L2 regularization)
            max_iter: Maximum solver iterations
        """
        self.C = C
        self.max_iter = max_iter
        self._scaler = StandardScaler()
        self._model = LogisticRegression(C=C, max_iter=max_iter, random_state=42)
        self.feature_names: Optional[list] = None

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> "DirectionModel":
        """Fit scaler and classifier. Rows with NaN labels are silently dropped.

        Args:
            X_train: Feature DataFrame (NaN values are forward-filled before fitting)
            y_train: Binary direction labels (0/1); NaN rows are excluded

        Returns:
            self
        """
        self.feature_names = list(X_train.columns)
        X_arr = self._scaler.fit_transform(X_train.values.astype(float))
        mask = ~np.isnan(y_train.values.astype(float))
        self._model.fit(X_arr[mask], y_train.values[mask])
        logger.debug("DirectionModel fitted on %d samples, %d features", mask.sum(), X_arr.shape[1])
        return self

    def predict_proba(self, X_test: pd.DataFrame) -> np.ndarray:
        """Predict probability of price going up.

        Args:
            X_test: Feature DataFrame with the same columns as X_train

        Returns:
            1-D array of P(up) values, one per row
        """
        X_arr = self._scaler.transform(X_test.values.astype(float))
        return self._model.predict_proba(X_arr)[:, 1]

    def feature_importance(self) -> pd.Series:
        """Absolute logistic coefficients as a rough feature importance proxy.

        Returns:
            Series of |coef| sorted descending, indexed by feature name

        Raises:
            RuntimeError: If called before fit()
        """
        if self.feature_names is None:
            raise RuntimeError("Model must be fitted before calling feature_importance().")
        return (
            pd.Series(np.abs(self._model.coef_[0]), index=self.feature_names)
            .sort_values(ascending=False)
        )
