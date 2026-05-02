"""SHAP feature importance analysis for tree-based models."""
import logging
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")
logger = logging.getLogger(__name__)


def run_shap(model, X_test: pd.DataFrame, output_dir: Path, tag: str) -> pd.Series:
    """Compute SHAP values from the last fold's model and save an importance chart.

    Uses TreeExplainer, which is exact and fast for gradient boosted trees.

    Args:
        model: Fitted XGBoostDirectionModel (must expose .get_booster())
        X_test: Feature DataFrame from the last CV fold's test set
        output_dir: Directory to write the PNG chart
        tag: Label for the file name and chart title, e.g. '1d'

    Returns:
        Series of mean |SHAP| per feature, sorted descending
    """
    try:
        import shap
    except ImportError:
        logger.warning("shap not installed — skipping SHAP analysis. Run: pip install shap")
        return pd.Series(dtype=float)

    booster = model.get_booster()
    explainer = shap.TreeExplainer(booster)

    X_arr = X_test.values.astype(float)
    shap_values = explainer.shap_values(X_arr)

    importance = pd.Series(
        np.abs(shap_values).mean(axis=0),
        index=X_test.columns,
    ).sort_values(ascending=False)

    _plot_shap_bar(importance.head(20), output_dir, tag)
    logger.info("SHAP analysis complete — top feature: %s (%.4f)", importance.index[0], importance.iloc[0])
    return importance


def _plot_shap_bar(importance: pd.Series, output_dir: Path, tag: str) -> None:
    """Save a horizontal bar chart of the top SHAP features."""
    fig, ax = plt.subplots(figsize=(8, 6))
    importance[::-1].plot.barh(ax=ax, color="steelblue", edgecolor="none")
    ax.set_title(f"SHAP Feature Importance — {tag} horizon (last fold)")
    ax.set_xlabel("Mean |SHAP value|")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    path = output_dir / f"shap_importance_{tag}.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    logger.info("Saved SHAP chart -> %s", path)
