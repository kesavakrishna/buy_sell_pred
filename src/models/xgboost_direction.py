"""XGBoost direction classifier with internal early stopping."""
import logging
from typing import Optional

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

logger = logging.getLogger(__name__)


class XGBoostDirectionModel:
    """Binary direction classifier using XGBoost gradient boosting.

    Identical external interface to DirectionModel (logistic baseline) —
    same .fit() / .predict_proba() signatures so run.py can swap models
    without changes.

    Uses the last 20% of the training window as an internal validation set
    for early stopping, preventing over-boosting on the training data while
    preserving the temporal ordering.

    Example:
        model = XGBoostDirectionModel(n_estimators=300, max_depth=4)
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)   # P(up) per row
        shap_vals = shap.TreeExplainer(model.get_booster()).shap_values(X_test)
    """

    def __init__(
        self,
        n_estimators: int = 300,
        max_depth: int = 4,
        learning_rate: float = 0.05,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        min_child_weight: int = 5,
        early_stopping_rounds: int = 30,
        val_fraction: float = 0.2,
    ):
        """
        Args:
            n_estimators: Maximum number of boosting rounds
            max_depth: Max tree depth (shallow = less overfitting; 3–5 typical for tabular finance)
            learning_rate: Step size shrinkage
            subsample: Row subsampling ratio per tree
            colsample_bytree: Feature subsampling ratio per tree
            min_child_weight: Minimum sum of instance weight in a leaf (regularizer)
            early_stopping_rounds: Stop if no improvement on val loss for this many rounds
            val_fraction: Fraction of training data held out as internal validation set
        """
        self.val_fraction = val_fraction
        self._model = XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            min_child_weight=min_child_weight,
            objective="binary:logistic",
            eval_metric="logloss",
            early_stopping_rounds=early_stopping_rounds,
            tree_method="hist",
            random_state=42,
            n_jobs=-1,
        )
        self.feature_names: Optional[list] = None
        self.best_iteration_: Optional[int] = None

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> "XGBoostDirectionModel":
        """Fit XGBoost on training data with early stopping on an internal val split.

        The last `val_fraction` rows (chronologically) of X_train are held out
        as a validation set. The temporal split prevents leakage from val to train.

        Args:
            X_train: Feature DataFrame
            y_train: Binary direction labels (0/1); NaN rows are dropped

        Returns:
            self
        """
        self.feature_names = list(X_train.columns)

        mask = ~np.isnan(y_train.values.astype(float))
        X_arr = X_train.values[mask].astype(float)
        y_arr = y_train.values[mask].astype(float)

        split = max(1, int(len(X_arr) * (1 - self.val_fraction)))
        X_tr, X_val = X_arr[:split], X_arr[split:]
        y_tr, y_val = y_arr[:split], y_arr[split:]

        self._model.fit(
            X_tr, y_tr,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )
        self.best_iteration_ = self._model.best_iteration
        logger.debug(
            "XGBoost fitted: %d train, %d val, best_iteration=%d",
            len(y_tr), len(y_val), self.best_iteration_ or 0,
        )
        return self

    def predict_proba(self, X_test: pd.DataFrame) -> np.ndarray:
        """Predict probability of price going up.

        Args:
            X_test: Feature DataFrame with the same columns as X_train

        Returns:
            1-D array of P(up) values, one per row
        """
        return self._model.predict_proba(X_test.values.astype(float))[:, 1]

    def get_booster(self):
        """Return the underlying XGBoost Booster for SHAP TreeExplainer.

        Returns:
            xgboost.Booster instance
        """
        return self._model.get_booster()

    def feature_importance(self, importance_type: str = "gain") -> pd.Series:
        """XGBoost native feature importance (gain, weight, or cover).

        Args:
            importance_type: 'gain' (default), 'weight', or 'cover'

        Returns:
            Series sorted descending by importance

        Raises:
            RuntimeError: If called before fit()
        """
        if self.feature_names is None:
            raise RuntimeError("Model must be fitted before calling feature_importance().")
        scores = self._model.get_booster().get_score(importance_type=importance_type)
        return (
            pd.Series(scores)
            .reindex(self.feature_names)
            .fillna(0)
            .sort_values(ascending=False)
        )
