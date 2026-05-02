# Phase 3B ML System — Volatility Regime Prediction Findings

**New in Phase 3B:** Vol regime classifier; position sizing = 1 − P(high_vol)  
**Asset:** BTC/USDT | **Date run:** 2026-05-02

---

## What Changed

Instead of predicting *direction* (up/down), the model now predicts *vol regime* (high/low
realized volatility over the next H days). The sizing rule is continuous:

```
size = 1 − P(high_vol)
```

When the model is confident vol will be high, reduce position to 0. When it's confident vol
will be low, hold full position. P(high_vol) ∈ [0, 1] so size is always non-negative.

The high/low label is binarized inside each CV fold using the **training-fold median** — no
lookahead. XGBoost classifier; same feature set and walk-forward setup as Phase 3.

---

## Results

### 7-Day Vol Horizon

| Fold | Vol Accuracy | Vol Brier | Sizing Sharpe | Baseline Sharpe | Sharpe Lift |
|------|-------------|-----------|---------------|-----------------|-------------|
| 1    | 68.3%       | 0.209     | +0.57         | +0.26           | **+0.31**   |
| 2    | 23.3%       | 0.289     | -0.29         | -0.01           | -0.28       |
| 3    | 70.0%       | 0.225     | -2.84         | -2.98           | +0.14       |
| 4    | 51.7%       | 0.238     | -2.53         | -2.63           | +0.09       |
| 5    | 46.7%       | 0.251     | +2.32         | +2.34           | -0.02       |
| **Mean** | **52.0%** | **0.242** | **-0.56** | **-0.60** | **+0.05** |
| Std  | 17.0%       | 0.027     | 1.94          | 1.97            | 0.20        |

### 30-Day Vol Horizon

| Fold | Vol Accuracy | Vol Brier | Sizing Sharpe | Baseline Sharpe | Sharpe Lift |
|------|-------------|-----------|---------------|-----------------|-------------|
| 1    | 65.0%       | 0.228     | +1.66         | +1.57           | +0.09       |
| 2    | **0.0%**    | 0.509     | -0.48         | -0.42           | -0.07       |
| 3    | 36.7%       | 0.304     | -4.25         | -4.23           | -0.02       |
| 4    | 48.3%       | 0.268     | -2.41         | -2.42           | +0.01       |
| 5    | 53.3%       | 0.239     | +2.01         | +2.00           | +0.00       |
| **Mean** | **40.7%** | **0.310** | **-0.70** | **-0.70** | **+0.00** |
| Std  | 22.3%       | 0.103     | 2.39          | 2.37            | 0.05        |

---

## SHAP — What Predicts Volatility

### 7d Vol Horizon (last fold)

| Rank | Feature | SHAP |
|------|---------|------|
| 1 | `funding_7d_mean` | 0.041 |
| 2 | `close_vs_ema50` | 0.039 |
| 3 | `trend_strength` | 0.037 |
| 4 | `funding_z` | 0.025 |
| 5 | `close_vs_ema200` | 0.019 |
| 6 | `macd_signal` | 0.017 |
| 7 | `funding_30d_mean` | 0.013 |
| 8 | `close_vs_ema21` | 0.011 |
| 9 | `ret_std_14d` | 0.007 |
| 10 | `vol_14d` | 0.007 |

### 30d Vol Horizon (last fold)

| Rank | Feature | SHAP |
|------|---------|------|
| 1 | `funding_30d_mean` | 0.052 |
| 2 | `macd_signal` | 0.049 |
| 3 | `vol_30d` | 0.017 |
| 4 | `ret_mean_14d` | 0.009 |
| 5 | `trend_strength` | 0.006 |

---

## Key Findings

### 1. Vol Is Slightly More Predictable Than Direction — But Only Slightly

At 7d, vol sizing produces a mean Sharpe **lift of +0.05** over buy-and-hold. The direction
pipeline produced near-zero lift at 7d (Sharpe improved from −3.27 to −2.76 across models,
but the individual fold lift from better prediction was essentially zero). So vol regime is a
fraction more predictable than direction — but +0.05 Sharpe lift is well inside noise (Std = 0.20).

At 30d, the lift is +0.004 — indistinguishable from zero.

### 2. Funding Rate Is the Top Vol Predictor

For direction prediction (Phase 3), `funding_30d_mean` ranked 3rd with SHAP = 0.011 as a
contrarian signal. For *vol* prediction, `funding_7d_mean` and `funding_30d_mean` now rank
**1st at both horizons**. The interpretation is intuitive:

- Persistently positive funding = longs are crowded and paying to hold → elevated unwind risk → higher vol
- The funding rate is telling the model about positioning risk, which maps more directly to vol than to direction

This is the most actionable finding of Phase 3B: **funding rate is a vol signal, not a direction signal**.

### 3. ARCH Effects Don't Show Up Strongly

In theory, the strongest predictor of future realized vol should be *recent* realized vol (the
ARCH/GARCH effect: volatility clusters). But `vol_14d` and `vol_30d` (lagged trailing vol)
rank 9th–10th at 7d and 3rd at 30d — not dominant.

Two reasons:
1. XGBoost distributes credit across correlated features. `trend_strength`, EMA ratios, and
   funding all encode regime information that also predicts vol, so credit is split.
2. ARCH effects are strongest at hourly/4h frequencies. At daily resolution, the clustering
   signal decays — 14-day lagged vol is a weak predictor of 7-day future vol.

### 4. Fold 2 at 30d: Zero Accuracy

Fold 2 achieved 0.0% vol accuracy (Brier = 0.509 — worse than predicting 0.5 everywhere).
The model trained on a high-vol period, then tested on a low-vol period where its predictions
were inverted. This is the same regime-transition collapse seen in direction prediction.

### 5. The Same Fundamental Problem

Fold-to-fold Sharpe ranges from −4.25 to +2.01 at 30d and −2.84 to +2.32 at 7d. The mean is
negative. Regime-transition folds (3 and 4) dominate the negative mean. This problem is structural
— it's not addressed by changing what we predict (direction vs vol).

---

## Comparison: Direction vs Vol Prediction

| Metric | P3 Direction 7d | P3B Vol 7d |
|--------|----------------|------------|
| Accuracy (dir/vol) | 45.7% | 52.0% |
| Brier | 0.277 | 0.242 |
| Mean Sharpe | -2.76 | -0.56 |
| Sharpe Lift vs Baseline | ~0 | +0.05 |

| Metric | P3 Direction 30d | P3B Vol 30d |
|--------|-----------------|-------------|
| Accuracy (dir/vol) | 40.7% | 40.7% |
| Brier | 0.315 | 0.310 |
| Mean Sharpe | -5.37 | -0.70 |
| Sharpe Lift vs Baseline | ~0 | +0.00 |

Notes:
- The absolute Sharpe numbers are different because the baseline differs (vol sizing is always invested,
  direction model is flat half the time)
- Vol accuracy is slightly higher than direction accuracy at 7d (52% vs 45.7%)
- Vol Brier is slightly better (0.242 vs 0.277)

Vol prediction is marginally better at the model-quality level, but the real-world Sharpe lift is tiny.

---

## Honest Assessment

Phase 3B confirmed the hypothesis that vol is slightly easier to predict than direction, but the
improvement is not large enough to matter in practice.

**What the model learned:**
- Funding rate extreme + crowded positioning → expect higher vol in next 7 days (sensible)
- Trend strength and EMA distance → when price is extended vs moving averages, vol tends to spike (reversion risk)
- These are real patterns but weak signals at daily granularity

**What's blocking further improvement:**
1. **Wrong frequency**: ARCH effects are strongest at 1h–4h. Daily vol prediction from daily features
   misses the clustering that happens at finer granularities.
2. **Missing implied vol**: Options IV (analogous to VIX for BTC, e.g. Deribit DVOL) is the market's
   forward-looking vol estimate. It would be the single strongest predictor of realized vol but requires
   a paid data source.
3. **Label quality**: The training-median binarization means the "high vol" and "low vol" classes are
   exactly 50/50 in each fold — optimal for balanced classification but loses information about *how*
   high the vol is.

---

## What Three Phases + 3B Have Established

After four iterations, the picture is clear and consistent:

| What we tried | What we learned |
|---------------|-----------------|
| Logistic regression | Baseline: vol features matter, MACD doesn't |
| XGBoost + regime | `trend_strength` is the load-bearing feature; within-regime noise is the problem |
| Derivatives signals | Funding rate has signal (contrarian at 30d); OI and LS are useless with 30d history |
| Vol regime prediction | Vol is slightly more predictable than direction; funding rate is a vol signal |

The core obstacle has not changed across any of these phases: **regime transitions produce catastrophic
folds that dominate the mean Sharpe**. Technical features from daily OHLCV do not predict when a
regime will change, only what the current regime is.

---

## Recommended Next Steps

At this point, the daily OHLCV + technical feature approach has been thoroughly explored. The marginal
return from adding more features in this framework is near zero.

**To genuinely improve, pick ONE of these structural changes:**

**Option 1: Sub-daily data for GARCH**
Switch from daily to 4h bars. Recompute all features at 4h. The ARCH effect — high vol follows high
vol — is strong at 4h and would make `vol_prev_4h` a dominant predictor. This is the most accessible
structural improvement with free Binance data.

**Option 2: Options implied vol (Deribit DVOL)**
DVOL is Deribit's BTC implied vol index (analogous to VIX). It is a market consensus forward-looking
vol estimate and would likely be the single strongest predictor. Deribit has a free public API for the
index itself but historical data requires a paid plan (Amberdata, Kaiko).

**Option 3: Live forward test**
Stop adding features. Run both pipelines (direction + vol sizing) daily for 60–90 days. The only
honest evaluation of a trading model is live forward prediction — all in-sample evidence is suspect.
This is the path that reveals whether the weak positive signals seen here are real or curve-fitted.

**My recommendation:** Option 3 first (set up daily cron, cheapest and most honest), then Option 1
(4h data for GARCH, accessible and structural). Option 2 is the theoretically best lever but has cost.
