# Phase 1 ML System — Baseline Findings

**System:** Production-grade crypto direction prediction pipeline  
**Assets tested:** BTC/USDT  
**Data source:** Binance public API (1001 daily candles, ~2.75 years)  
**Date run:** 2026-04-26  
**Model:** Logistic Regression (direction) + Quantile Regression (return intervals)  
**Evaluation:** Expanding walk-forward CV, 5 folds, 60-day test windows, purge = horizon

---

## Baseline Results

### 1-Day Horizon

| Fold | Dir Accuracy | Brier Score | Sharpe (net 10bps) | Trades |
|------|-------------|-------------|---------------------|--------|
| 1    | 53.3%       | 0.257       | -0.79               | 26     |
| 2    | 45.0%       | 0.267       | -0.52               | 11     |
| 3    | 48.3%       | 0.297       | -2.56               | 9      |
| 4    | 45.0%       | 0.289       | -2.04               | 13     |
| 5    | 46.7%       | 0.248       | +1.14               | 10     |
| **Mean** | **47.7%** | **0.272** | **-0.95**         | 13.8   |
| Std  | 3.1%        | 0.019       | 1.29                | 6.2    |

**Naive benchmark (always long):** ~52% accuracy on a bull-biased asset.  
**Baseline verdict:** Near-random. The model is slightly *below* the naive benchmark on accuracy. Negative mean Sharpe means the strategy loses money after fees.

---

### 7-Day Horizon

| Fold | Dir Accuracy | Brier Score | Sharpe (net 10bps) | Trades |
|------|-------------|-------------|---------------------|--------|
| 1    | 46.7%       | 0.292       | -0.50               | 7      |
| 2    | 63.3%       | 0.222       | +0.41               | 5      |
| 3    | 31.7%       | 0.401       | -8.79               | 1      |
| 4    | 26.7%       | 0.340       | -8.82               | 9      |
| 5    | 36.7%       | 0.303       | +1.38               | 12     |
| **Mean** | **41.0%** | **0.312** | **-3.27**         | 6.8    |
| Std  | 12.9%       | 0.059       | 4.57                | 3.7    |

**Baseline verdict:** Worse than 1-day. High fold-to-fold variance (std accuracy = 13%) signals the model is picking up regime-specific noise, not a stable signal. Folds 3 and 4 (worst Sharpe, 1 and 9 trades) suggest the model confidently bet wrong during those market regimes.

---

### 30-Day Horizon

| Fold | Dir Accuracy | Brier Score | Sharpe (net 10bps) | Trades |
|------|-------------|-------------|---------------------|--------|
| 1    | 70.0%       | 0.286       | +9.99               | 5      |
| 2    | 35.0%       | 0.367       | -1.13               | 1      |
| 3    | 11.7%       | 0.684       | -23.27              | 5      |
| 4    | 35.0%       | 0.434       | -11.37              | 1      |
| 5    | 71.7%       | 0.219       | +3.09               | 5      |
| **Mean** | **44.7%** | **0.398** | **-4.54**         | 3.4    |
| Std  | 23.0%       | 0.160       | 11.65               | 2.0    |

**Baseline verdict:** Highest variance of all three horizons (std accuracy = 23%). Fold 3 with 11.7% accuracy is spectacularly wrong — the model learned the *wrong* direction during that period. Folds 1 and 5 look deceptively good (Sharpe +10, +3), but these are likely regime-fitting artifacts, not generalizable skill.

---

## What the Numbers Mean

### Directional accuracy near 50% is expected
A coin flip gets 50%. Crypto returns are notoriously noisy — especially at the 1-day horizon where microstructure, news shocks, and leverage cascades dominate over any technical signal. Getting 47.7% is not embarrassing; it is an honest measurement.

### Negative Sharpe is the right starting point
The baseline losing money after fees is the *correct* null result. It tells you the signal-to-noise ratio with a linear model on these features is not good enough to overcome transaction costs. Any strategy that shows positive Sharpe from a first-pass baseline on crypto should be treated with suspicion (overfitting to the test period).

### Walk-forward variance is the most important signal
The spread between the best and worst fold (e.g., 7d horizon: Sharpe +1.38 to -8.82) reveals that the model is not learning a regime-stable relationship. It is fitting patterns that hold in some market conditions and fail badly in others. **A single train/test split would have hidden this completely.**

### 30-day Fold 3 is a warning
Fold 3 got 11.7% direction accuracy — worse than random by a large margin. This happens when the model learns a relationship (e.g., "technical momentum precedes continuation") that *inverts* in the test period (a trend reversal regime). This is not a bug; it is why naive ML on crypto without regime awareness will fail.

### The Brier score tells you about calibration
A perfectly calibrated model predicts 70% when it's actually right 70% of the time. Our Brier scores (0.25–0.68) are below the 0.25 threshold you'd expect from a well-calibrated model, meaning the model is overconfident in its wrong predictions. Calibration will improve with XGBoost + Platt scaling.

---

## Feature Set (40 columns total)

| Category | Features | Count |
|----------|----------|-------|
| OHLCV (raw, excluded from model) | open, high, low, close, volume | 5 |
| RSI | rsi | 1 |
| MACD | macd, macd_signal, macd_hist | 3 |
| Bollinger Bands | bb_pct_b, bb_width | 2 |
| EMA Ratios | close_vs_ema9/21/50/200 | 4 |
| Realized Volatility | vol_7d, vol_14d, vol_30d | 3 |
| Lag Returns | return_1d/2d/3d/7d/14d | 5 |
| Log Volume + Ratios | log_volume, vol_ratio_7/14/30d | 4 |
| Rolling Return Stats | ret_mean/std at 7/14/30d | 6 |
| Fear & Greed | fear_greed | 1 |
| Targets (not used as features) | direction_1/7/30d, log_return_1/7/30d | 6 |

**Note on fear_greed:** Historical F&G data only covers ~365 days. Rows before that period use a fill value of 50 (neutral). This affects the first ~635 rows but does not affect recent test folds, which all fall within the 365-day window.

---

## Key Methodological Findings

### 1. Walk-forward CV is load-bearing infrastructure
Without it, we would have reported the results of whichever fold happened to coincide with the tested period — potentially the +9.99 Sharpe fold. With it, we see the full distribution of outcomes. **This is the single most important piece of engineering in Phase 1.**

### 2. Purge gap correctly prevents lookahead leakage
For a 7-day horizon model, the target at row t is the return from t to t+7. Without a 7-row purge gap, the training set could include rows t-1, t-2... whose targets overlap with the test row's feature window. The purge eliminates this. Any reported accuracy improvement in Phase 2 without a purge should be treated as leakage.

### 3. Logistic regression is the right first model
It is fast, transparent, and interpretable. The negative result it produces is unambiguous: these features, linearly combined, do not produce a tradeable edge. This is the correct foundation to build on. It also establishes what "no skill" looks like so Phase 2 improvements can be measured against it.

### 4. Fees matter more at higher trade frequency
The 1d horizon model trades ~14x per fold (60 days), paying 10bps each way. The 30d model trades ~3x per fold. Even with a negative Sharpe, the 30d model bleeds less to fees — high-frequency trading with a marginal model is doubly punished.

---

## Limitations of the Phase 1 Baseline

| Limitation | Impact | Phase 2 fix |
|------------|--------|-------------|
| Linear model can't capture non-linear interactions | High — crypto features interact multiplicatively (e.g., high vol + low RSI is not just additive) | XGBoost captures interactions automatically |
| No regime awareness | High — model applies same logic in bull/bear/sideways markets | Regime features (HMM-derived or trend filter) |
| F&G coverage only 365 days | Medium — older folds get neutral fill value | Use on-chain/derivatives data as additional sentiment |
| Single asset (BTC) | Low for now — by design, Phase 1 scope | ETH via `--asset ETH/USDT` is already supported |
| No position sizing | Medium — strategy is all-in or flat | Confidence-weighted sizing (Phase 2 extension) |
| Calibration not enforced | Medium — overconfident predictions in some folds | Platt scaling or isotonic regression on top of model |

---

## Recommended Phase 2 Priorities

1. **XGBoost direction model** — swap `DirectionModel` in `src/models/` for XGBoost. Same `.fit()` / `.predict_proba()` interface. Expected lift: +5–10pp directional accuracy, positive Sharpe in majority of folds.

2. **SHAP feature importance** — XGBoost gives us SHAP values. Run SHAP analysis on the best-performing fold to understand which features carry signal vs noise. Likely candidates: `vol_7d`, `bb_pct_b`, `rsi`, `ret_mean_7d`.

3. **Regime filter** — add a simple trend filter: `close > EMA(200)` = bull regime, else bear. Train separate models or add regime as a binary feature. This is why fold-to-fold variance is so high.

4. **Calibration** — apply `CalibratedClassifierCV` (Platt scaling) on top of XGBoost predictions before computing Brier score and Sharpe. This will improve the confidence intervals from the QuantileModel too.

5. **ETH baseline** — run `python -m src.pipeline.run --asset ETH/USDT` to get the ETH baseline numbers for comparison.

---

## Output Files

```
outputs/BTC_USDT/
├── predictions_1d.parquet    # y_true_dir, y_true_ret, y_prob, q10, q50, q90 per test row
├── predictions_7d.parquet
├── predictions_30d.parquet
├── equity_curve_1d.png       # strategy vs buy & hold
├── equity_curve_7d.png
└── equity_curve_30d.png
```

The predictions Parquets contain the full out-of-sample predictions from all folds, concatenated in chronological order. These can be used for further analysis (calibration curves, feature importance post-hoc, strategy simulation with different position sizing rules) without re-running the pipeline.
