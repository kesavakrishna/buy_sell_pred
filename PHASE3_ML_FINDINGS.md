# Phase 3 ML System — Derivatives Signals Findings

**New in Phase 3:** Funding rate (full history), open interest, long/short ratio from Binance Futures  
**Asset:** BTC/USDT | **Date run:** 2026-05-02

---

## API Reality Check

Before results: a significant constraint was discovered during implementation.

| Signal | History Available | startTime Supported | Notes |
|--------|------------------|--------------------|-|
| Funding rate | 1000+ days | ✅ Yes | Full history, 8h cadence resampled daily |
| Open interest | ~30 days | ❌ No (400 error) | Binance caps daily OI history |
| Long/short ratio | ~30 days | ❌ No (400 error) | Same constraint as OI |

The OI and LS endpoints simply do not expose historical data beyond 30 days at daily granularity. Free Binance API is the binding constraint here — not the code. Full history would require a paid provider (CryptoQuant, Coinalyze, Glassnode).

**Workaround applied:** OI and LS are fetched for the available 30-day window and joined. Derived features default to 0 (neutral) for rows with no coverage, preserving the full 970-row training set.

---

## Results: Phase 1 → Phase 2 → Phase 3

### 1-Day Horizon (Mean across 5 folds)

| Phase | Dir Accuracy | Sharpe | Brier |
|-------|-------------|--------|-------|
| P1 — Logistic | 47.7% | -0.95 | 0.272 |
| P2 — XGBoost | 50.0% | -0.43 | 0.251 |
| P3 — XGBoost + Derivatives | **50.0%** | **-0.40** | **0.253** |

Derivatives added negligible improvement at 1d. Funding rate SHAP = 0.0025 — present but tiny.

### 7-Day Horizon

| Phase | Dir Accuracy | Sharpe | Brier |
|-------|-------------|--------|-------|
| P1 — Logistic | 41.0% | -3.27 | 0.312 |
| P2 — XGBoost | 45.3% | -2.62 | 0.275 |
| P3 — XGBoost + Derivatives | 45.7% | -2.76 | 0.277 |

Marginal, within run-to-run noise. No meaningful improvement.

### 30-Day Horizon

| Phase | Dir Accuracy | Sharpe | Brier |
|-------|-------------|--------|-------|
| P1 — Logistic | 44.7% | -4.54 | 0.398 |
| P2 — XGBoost | 43.0% | -5.27 | 0.333 |
| P3 — XGBoost + Derivatives | 40.7% | -5.37 | 0.315 |

Worse accuracy but better Brier — the model is less overconfident in the wrong direction. `funding_30d_mean` appeared as the 3rd most important feature (SHAP = 0.011), suggesting monthly funding persistence carries real signal for 30d prediction.

---

## SHAP — What Derivatives Features Contributed

### Funding Rate Showed Up (Marginally)

**1d horizon:** `funding_z` ranked 6th (SHAP = 0.0025). Small but non-zero — the Z-score of today's funding rate relative to the past 30 days has a tiny predictive edge at 1-day horizon.

**30d horizon:** `funding_30d_mean` ranked 3rd (SHAP = 0.011). If funding has been persistently positive for 30 days, it's meaningful for 30-day direction. This is a contrarian signal — persistent longs eventually get squeezed.

### OI and LS Features: Zero Everywhere

Every OI and LS feature scored exactly 0.000 SHAP across all horizons. With only 30 days of coverage and the model needing to see patterns across hundreds of training rows, these features carry no learnable signal. They can be removed without any loss.

### `trend_strength` Grows Stronger Each Phase

| Phase | 30d SHAP for trend_strength |
|-------|-----------------------------|
| P2    | 0.057 |
| P3    | 0.082 |

As the feature set grows, the model routes more and more weight to `trend_strength`. It's increasingly clear this is the single load-bearing feature for medium-to-long horizons.

---

## What Three Phases Have Established

After running logistic regression, XGBoost, regime features, and derivatives signals, the picture is consistent:

**What works (has non-zero SHAP):**
| Feature | Horizon | Role |
|---------|---------|------|
| `trend_strength` | 7d, 30d | Dominant — regime classification |
| `vol_14d`, `vol_30d` | 7d | Volatility regime |
| `ret_mean_30d` | 1d, 30d | Momentum of returns |
| `close_vs_ema9` | 1d | Short-term mean reversion |
| `log_volume` | 1d | Volume level |
| `funding_30d_mean` | 30d | Funding persistence (contrarian) |

**What doesn't work (zero SHAP every phase):**
- MACD line and histogram (7d, 30d)
- Most EMA ratios (ema21, ema200)
- Fear & Greed index at most horizons
- OI and LS features (data too sparse)
- All voting/binary regime flags (`bull_regime`, `golden_cross`) — subsumed by `trend_strength`

**The core problem hasn't changed:** fold-to-fold Sharpe ranges from -25 to +11 across all three phases. The mean Sharpe is negative at every horizon for every model. Better features haven't solved the regime variance.

---

## Honest Assessment After Three Phases

The current approach — technical features + sentiment + positioning, trained on daily OHLCV — is near its ceiling. Three phases of improvement yielded:
- 1d: -0.95 → -0.40 Sharpe (meaningful but still negative)
- 7d: -3.27 → -2.76 Sharpe (marginal)
- 30d: still dominated by two catastrophic folds

This isn't a failure of the code — it's an accurate reflection of how hard short-term crypto prediction is with public data. Hedge funds spending millions on ML barely eke out 1–2% alpha at daily horizons.

**What's actually happening:** the model is good at identifying regime (trend_strength) but within a regime, day-to-day direction is largely noise. The wide fold variance confirms this — the model performs well in regime-stable periods (folds 1, 5) and catastrophically in regime-transition periods (folds 3, 4).

---

## Recommended Path Forward

The honest next step is to **change what the model is trying to do**, not keep adding features to the same formulation.

**Option A: Predict volatility regime, not direction**
Train a classifier for "high vol / low vol" over the next H days. Volatility is far more persistent than direction, has better signal-to-noise, and is directly useful for sizing positions. Predict direction only as a secondary output.

**Option B: Regime-conditional direction model**
Split training by regime (`trend_strength > 0` = bull, `< 0` = bear). Train a separate direction model per regime. This directly addresses why fold 3 is catastrophic — the bear model learns from bear data, not from a mixed signal.

**Option C: Hold and build data**
Stop model development. Run the pipeline daily for 3–6 months to accumulate fresh out-of-sample predictions. Then evaluate whether the model has any real forward-looking skill before investing further in features.

**My recommendation:** Option B first (regime-conditional, two weeks of work), then Option C in parallel to accumulate live predictions. Option A is valid but changes the product definition.

---

## Cleanup Before Next Phase

Remove these zero-SHAP features from the pipeline to reduce noise (edit `config/settings.yaml` and `src/features/`):
- OI and LS features (entire `build_derivatives_features` OI/LS sections)
- `bull_regime`, `golden_cross` (keep only `trend_strength`)
- Consider dropping `macd`, `macd_hist` at 7d and 30d horizons
