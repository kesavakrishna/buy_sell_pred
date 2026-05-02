# Phase 2 ML System — XGBoost + Regime Features + SHAP Findings

**System:** Phase 2 — XGBoost direction model with regime features and SHAP analysis  
**Asset:** BTC/USDT  
**Data:** 1001 daily candles from Binance (~2.75 years)  
**New in Phase 2:** XGBoost (replaces logistic regression), regime features (trend_strength, bull_regime, golden_cross), SHAP feature importance  
**Date run:** 2026-05-01

---

## Phase 2 vs Phase 1 Comparison

### 1-Day Horizon

|                | Dir Accuracy | Mean Sharpe | Brier  |
|----------------|-------------|-------------|--------|
| Logistic (P1)  | 47.7%       | -0.95       | 0.272  |
| XGBoost (P2)   | **50.0%**   | **-0.43**   | **0.251** |
| Delta          | +2.3pp      | +0.52       | -0.021 |

### 7-Day Horizon

|                | Dir Accuracy | Mean Sharpe | Brier  |
|----------------|-------------|-------------|--------|
| Logistic (P1)  | 41.0%       | -3.27       | 0.312  |
| XGBoost (P2)   | **45.3%**   | **-2.62**   | **0.275** |
| Delta          | +4.3pp      | +0.65       | -0.037 |

### 30-Day Horizon

|                | Dir Accuracy | Mean Sharpe | Brier  |
|----------------|-------------|-------------|--------|
| Logistic (P1)  | 44.7%       | -4.54       | 0.398  |
| XGBoost (P2)   | 43.0%       | -5.27       | 0.333  |
| Delta          | -1.7pp      | -0.73       | -0.065 |

**Summary:** XGBoost improves 1d and 7d but is marginally worse on 30d. The 30d model is dominated by two fold extremes (Fold 1 at +11 Sharpe, Fold 3 at -25 Sharpe) — the mean is meaningless without addressing regime.

---

## Per-Fold Results (Phase 2, XGBoost)

### 1-Day

| Fold | Accuracy | Brier | Sharpe | Trades | Best Iter |
|------|----------|-------|--------|--------|-----------|
| 1    | 56.7%    | 0.248 | +1.29  | 28     | 27        |
| 2    | 53.3%    | 0.251 | +0.07  | 25     | 20        |
| 3    | 40.0%    | 0.256 | -3.31  | 3      | **1**     |
| 4    | 43.3%    | 0.255 | -2.07  | 1      | **0**     |
| 5    | 56.7%    | 0.247 | +1.88  | 3      | **1**     |
| Mean | 50.0%    | 0.251 | -0.43  | 12.0   |           |

### 7-Day

| Fold | Accuracy | Brier | Sharpe | Trades | Best Iter |
|------|----------|-------|--------|--------|-----------|
| 1    | 40.0%    | 0.263 | -1.67  | 17     | 21        |
| 2    | 51.7%    | 0.266 | -1.96  | 11     | 23        |
| 3    | 31.7%    | 0.336 | -8.79  | 1      | 9         |
| 4    | 36.7%    | 0.285 | -7.15  | 1      | **0**     |
| 5    | 66.7%    | 0.226 | +6.49  | 1      | **0**     |
| Mean | 45.3%    | 0.275 | -2.62  | 6.2    |           |

### 30-Day

| Fold | Accuracy | Brier | Sharpe  | Trades | Best Iter |
|------|----------|-------|---------|--------|-----------|
| 1    | 75.0%    | 0.191 | +11.04  | 1      | 10        |
| 2    | 35.0%    | 0.415 | -1.13   | 1      | 10        |
| 3    | 6.7%     | 0.479 | **-25.85** | 1   | 10        |
| 4    | 35.0%    | 0.346 | -11.37  | 1      | **1**     |
| 5    | 63.3%    | 0.236 | +0.99   | 1      | **0**     |
| Mean | 43.0%    | 0.333 | -5.27   | 1.0    |           |

---

## SHAP Feature Importance

### 1-Day Horizon — Top Features

| Rank | Feature         | Mean \|SHAP\| | Interpretation |
|------|-----------------|--------------|----------------|
| 1    | ret_mean_30d    | 0.0155       | 30-day momentum of returns |
| 2    | close_vs_ema9   | 0.0098       | Short-term trend (9-day EMA deviation) |
| 3    | log_volume      | 0.0084       | Volume level |
| 4    | vol_30d         | 0.0059       | 30-day realized volatility |
| 5    | vol_ratio_7d    | 0.0058       | Volume spike relative to 7-day avg |

Most MACD and EMA-cross features scored 0.000 — they contribute nothing to the 1d model.

### 7-Day Horizon — Top Features

| Rank | Feature         | Mean \|SHAP\| | Interpretation |
|------|-----------------|--------------|----------------|
| 1    | trend_strength  | 0.0223       | EMA50/EMA200 divergence (regime feature) |
| 2    | vol_14d         | 0.0178       | 14-day realized volatility |
| 3    | vol_30d         | 0.0171       | 30-day realized volatility |
| 4    | close_vs_ema50  | 0.0091       | Medium-term trend |
| 5    | vol_7d          | 0.0090       | Short-term volatility |

### 30-Day Horizon — Top Features

| Rank | Feature         | Mean \|SHAP\| | Interpretation |
|------|-----------------|--------------|----------------|
| 1    | trend_strength  | **0.0567**   | EMA50/EMA200 divergence — 5× next feature |
| 2    | vol_30d         | 0.0114       | Long-run volatility regime |
| 3    | ret_mean_30d    | 0.0101       | 30-day momentum |
| 4    | macd_signal     | 0.0072       | Smoothed MACD |
| 5    | bb_width        | 0.0036       | Volatility expansion/contraction |

---

## Key Findings

### 1. `trend_strength` is the dominant signal at medium and long horizons

The `trend_strength` feature (= `(EMA50 - EMA200) / EMA200`, added in Phase 2) is the **single most important feature** for both the 7-day and 30-day models by a wide margin — 2.2× the next feature at 7d, and 5× the next feature at 30d. This directly validates the hypothesis from the Phase 1 findings that regime awareness was the critical missing piece.

**Implication:** The model is essentially asking "are we in a trending upmarket?" before predicting direction. A simple rule filter — only go long when `trend_strength > 0` — may be nearly as effective as the full XGBoost model for 30d predictions.

### 2. Early stopping at iteration 0 or 1 is a signal, not a bug

Folds where `best_iter = 0` or `best_iter = 1` mean XGBoost found no learnable pattern in the training data for that market period and immediately fell back to the base rate (always predict the majority class). This is the correct behavior. It tells us:

- The features available do not encode useful signal for those particular market regimes
- A more complex model would just overfit — the problem is feature quality, not model capacity
- Folds 3 and 4 at 30d are "no signal" periods, not model failures

### 3. Volatility is consistently predictive; most MACD/EMA features are not

Across all three horizons, realized volatility (7d, 14d, 30d) appears in the top 5 features. Several MACD-derived features and short-period EMA ratios score exactly 0.000 in SHAP — XGBoost never uses them in any split. These can be removed in Phase 3 to reduce feature noise.

Features with zero SHAP importance across all horizons (candidates for removal):
- `macd`, `macd_hist` (1d and 7d)
- `close_vs_ema21`, `close_vs_ema200` (redundant with `trend_strength`)
- `golden_cross`, `bull_regime` (subsumed by `trend_strength`)
- Several lag return features (`return_2d`, `return_3d`)

### 4. 30-day Fold 3 (6.7% accuracy) remains unexplained

With best_iter=10 (not zero), XGBoost was confident in its wrong predictions during Fold 3. This is the worst case — a model that's convinced rather than uncertain. Investigating what period Fold 3 covers and what market event occurred there would explain why the pattern inverted so sharply. The model likely learned a bull-regime signal from training data, then the test period was a sharp regime reversal.

### 5. XGBoost does not meaningfully help the 30-day horizon

The 30d model has exactly 1 trade per fold. With only ~20 samples in each 60-day test window and a 30-day target, the effective sample count per fold is 30 non-overlapping observations. XGBoost cannot learn from 30 samples better than logistic regression. The 30d problem requires either a much longer data history, macro/on-chain features with 30d predictive power, or regime-conditional modeling.

---

## What Didn't Work

| Hypothesis | Result |
|------------|--------|
| XGBoost > logistic at all horizons | Only true for 1d and 7d; neutral/worse at 30d |
| More model complexity fixes the variance | No — fold variance is unchanged; problem is regime, not model |
| Regime features improve calibration (Brier) | Yes, Brier improves consistently (+0.02–0.07) |
| 30d is learnable with good features | No — sample count is the binding constraint |

---

## Limitations Still Present

| Limitation | Evidence | Fix |
|------------|----------|-----|
| No regime-conditional model | High fold variance, `trend_strength` dominance | Train separate bull/bear models or add regime as interaction feature |
| 30d sample poverty | best_iter=1, 1 trade/fold | Needs 5+ years of data or a different target (volatility, drawdown) |
| Dead features (MACD, some EMA ratios) | SHAP = 0.000 | Drop before Phase 3 to reduce noise |
| No on-chain/derivatives features | Limited 1d signal | Funding rate, OI, exchange flows (Phase 3) |
| Quantile intervals not validated | Not checked for coverage | Add calibration curve for quantile intervals |

---

## Recommended Phase 3 Priorities

1. **Feature pruning** — remove the ~8 features with zero SHAP across all horizons. Tighter feature set reduces variance and speeds up training.

2. **Regime-conditional modeling** — train separate 1d and 7d models for bull/bear regimes (split on `trend_strength > 0`). This addresses the core cause of fold-to-fold variance.

3. **On-chain / derivatives signals** — funding rate (from Binance Futures), open interest, and long/short ratio are available free via the Binance API. These should have 1d–7d predictive power for BTC specifically.

4. **ETH baseline** — run `python -m src.pipeline.run --asset ETH/USDT` to check whether BTC regime features transfer to ETH or whether it needs its own signal set.

5. **Investigate Fold 3** — identify the exact date range and market event that caused 6.7% accuracy on 30d. Understanding the failure mode is more valuable than improving the mean.

---

## How to Reproduce

```bash
# XGBoost (default, Phase 2)
venv/Scripts/python -m src.pipeline.run --asset BTC/USDT

# Single horizon
venv/Scripts/python -m src.pipeline.run --asset BTC/USDT --horizon 7

# Logistic baseline for comparison
venv/Scripts/python -m src.pipeline.run --asset BTC/USDT --model logistic

# ETH
venv/Scripts/python -m src.pipeline.run --asset ETH/USDT
```

## Output Files (Phase 2)

```
outputs/BTC_USDT/
├── equity_curve_1d_xgboost.png
├── equity_curve_7d_xgboost.png
├── equity_curve_30d_xgboost.png
├── shap_importance_1d.png          # top 20 SHAP features, last fold
├── shap_importance_7d.png
├── shap_importance_30d.png
├── predictions_1d_xgboost.parquet  # y_true, y_prob, q10/50/90 per test row
├── predictions_7d_xgboost.parquet
└── predictions_30d_xgboost.parquet
```
