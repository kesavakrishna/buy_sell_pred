# Phase 4 ML System — 4h Data + GARCH Features Findings

**New in Phase 4:** 4h bars (6003 rows), GARCH features (`hl_range`, `avg_hl_range`, `abs_ret_1b`, `vol_accel`), regime EMAs scaled to calendar-equivalent periods  
**Asset:** BTC/USDT | **Date run:** 2026-05-02

---

## What Changed

| Component | Phase 3B (daily) | Phase 4 (4h) |
|-----------|-----------------|--------------|
| Timeframe | 1d | 4h |
| Rows | 1001 | 6003 |
| Horizon 1 (1d equiv) | 1 bar | 6 bars |
| Horizon 2 (7d equiv) | 7 bars | 42 bars |
| Horizon 3 (30d equiv) | 30 bars | 180 bars |
| Vol windows | [7d, 14d, 30d] days | [6, 24, 42] bars (1d, 4d, 7d) |
| Regime EMAs | EMA50, EMA200 | EMA300, EMA1200 (same calendar days) |
| New features | — | `hl_range`, `avg_hl_range`, `abs_ret_1b`, `vol_3b`, `vol_accel` |

---

## Direction Prediction Results (4h)

| Horizon | Dir Accuracy | Mean Sharpe | Trades/Fold |
|---------|-------------|-------------|-------------|
| 6 bars (≈1d) | 50.5% | -1.39 | 1 |
| 42 bars (≈7d) | 46.1% | -3.82 | 7.6 |
| 180 bars (≈30d) | 45.1% | -9.40 | 2.6 |

The direction pipeline at 4h is **worse** than daily. The model is extremely risk-averse (1 trade per fold in many cases), and the fold Sharpe variance is 3–4× larger than at daily. The 4h direction model is not an improvement over the daily direction model.

**Why:** At 4h, each test fold has 360 bars but the model must predict 6/42/180-bar return windows with massive label overlap. The XGBoost model defaults to low confidence (P ≈ 0.5) when overlapping labels create conflicting training signal, resulting in very few trades.

---

## Vol Prediction Results (4h) — Main Finding

### 6-Bar Vol Horizon (≈1d Calendar)

| Fold | Vol Accuracy | Vol Brier | Sizing Sharpe | Baseline | Lift |
|------|-------------|-----------|---------------|----------|------|
| 1    | 62.2%       | 0.232     | +0.28         | +0.49    | -0.21 |
| 2    | 59.4%       | 0.243     | -0.06         | -0.31    | +0.25 |
| 3    | 59.2%       | 0.229     | -2.69         | -2.26    | -0.44 |
| 4    | **77.5%**   | **0.186** | -2.79         | -2.36    | -0.43 |
| 5    | 55.0%       | 0.250     | +1.71         | +1.61    | +0.10 |
| **Mean** | **62.7%** | **0.228** | **-0.71** | **-0.57** | **-0.14** |

### 42-Bar Vol Horizon (≈7d Calendar)

| Fold | Vol Accuracy | Vol Brier | Sizing Sharpe | Baseline | Lift |
|------|-------------|-----------|---------------|----------|------|
| 1    | 79.4%       | 0.168     | +0.68         | +0.31    | +0.37 |
| 2    | 65.0%       | 0.224     | +0.04         | +0.12    | -0.08 |
| 3    | 66.1%       | 0.218     | -3.40         | -3.05    | -0.35 |
| 4    | 73.3%       | 0.163     | -2.30         | -2.81    | +0.51 |
| 5    | 59.7%       | 0.251     | +2.07         | +2.52    | -0.46 |
| **Mean** | **68.7%** | **0.205** | **-0.58** | **-0.58** | **0.00** |

---

## SHAP — The ARCH Effect Is Real

### 6-Bar Vol (≈1d) — GARCH Features Dominate

| Rank | Feature | SHAP | What It Captures |
|------|---------|------|-----------------|
| 1 | `trend_strength` | 0.160 | Regime (carry-over from all phases) |
| 2 | `vol_42d` | 0.127 | 7d trailing realized vol (ARCH lag) |
| 3 | `vol_ratio_24d` | 0.114 | Volume vs 4d average (liquidity stress) |
| **4** | **`avg_hl_range`** | **0.090** | **Rolling 1d intra-bar range (direct ARCH)** |
| **5** | **`hl_range`** | **0.075** | **This bar's high-low range (direct ARCH)** |
| 6 | `close_vs_ema24` | 0.063 | Price vs 4d EMA |
| 7 | `close_vs_ema300` | 0.059 | Price vs 50d EMA |
| 8 | `ret_std_42d` | 0.050 | 7d return std |

`hl_range = log(high/low)` is the intra-4h-bar range — a direct measure of within-bar volatility. `avg_hl_range` = rolling 6-bar (1d) mean of that range. **These rank 4th and 5th for predicting next-day vol, confirming the ARCH hypothesis:** what happened in this bar (and the past day of bars) predicts how volatile the next day will be.

### 42-Bar Vol (≈7d) — Regime Takes Over

| Rank | Feature | SHAP |
|------|---------|------|
| 1 | `trend_strength` | 0.888 |
| 2 | `close_vs_ema300` | 0.305 |
| 3 | `bb_width` | 0.173 |
| 4 | `funding_30d_mean` | 0.158 |
| 5 | `golden_cross` | 0.142 |

At 7d horizon, `trend_strength` completely dominates (SHAP 0.888 vs 0.160 at 1d). **The model has learned: when trend is strong (high trend_strength), 7-day vol is low; when trend is breaking, vol is high.** This is regime-vol correlation, not ARCH — it's a structural market relationship, not volatility clustering per se.

---

## Key Findings

### 1. ARCH Effect Confirmed at 4h — Short-Lag HL Range Is a Real Signal

`hl_range` and `avg_hl_range` were designed specifically to capture ARCH effects at 4h frequency, and they work: ranked 4th-5th for 1d vol prediction. This validates the hypothesis that switching to sub-daily data unlocks vol clustering signal.

At daily frequency, the equivalent (`vol_14d`, `vol_30d`) ranked 9th-10th. The jump to top-5 at 4h is the ARCH effect becoming visible at the right timescale.

### 2. Vol Accuracy Is Genuinely High — 62.7% at 1d, 68.7% at 7d

Compare to direction accuracy (50.5% and 46.1% at the same horizons). **Vol is substantially more predictable than direction at 4h.** This was the hypothesis going into Phase 4 and it's confirmed more strongly than expected.

At 42d horizon, the model achieves 68.7% accuracy with `trend_strength` SHAP = 0.888. This means: if trend_strength is strongly positive, the model correctly predicts that the next 7 days will be low-vol ~70% of the time.

### 3. High Vol Accuracy Doesn't Translate to Sharpe Lift — The Crypto Problem

The vol-sizing strategy (size = 1 − P(high_vol)) shows **negative Sharpe lift at 6d (−0.14) and zero lift at 42d (0.00)** despite 62–69% vol accuracy. This is the critical crypto-specific finding:

**In crypto, high-volatility periods often coincide with strong directional moves.** When the model correctly predicts "high vol next day," it reduces position size. But if Bitcoin rips +20% on that high-vol day, the reduced position misses the gain.

In traditional assets (equities, bonds), high vol periods are usually drawdowns. In crypto, vol is symmetric — high vol means big moves, which can be up OR down. A vol-reduction strategy assumes "high vol = bad," but in crypto it's "high vol = uncertain."

The sizing rule needs refinement for crypto: instead of `size = 1 − P(high_vol)`, use `size = direction_confidence × (1 − P(high_vol))` — only reduce when vol is high AND the direction model is uncertain. This is the regime-conditional model from Phase 3's Option B.

### 4. Direction Prediction Is Worse at 4h Than Daily

4h direction prediction (50.5% at 6d, −1.39 Sharpe) is actually worse than the daily equivalent (50.0%, −0.40 Sharpe). Two reasons:

1. **Label overlap**: At 4h with horizon=6, every prediction covers a 24h window, but predictions are made every 4h. 5 out of 6 consecutive predictions overlap — training becomes contradictory. XGBoost's response: make low-confidence predictions, leading to n_trades=1.

2. **Noise increase**: At 4h, 6-bar returns include noise from liquidity events (low-volume 4h bars) that daily candles smooth out. Direction is harder to predict from noisy sub-day returns.

---

## Phase 1→4 Vol Prediction Comparison

| Phase | Timeframe | Horizon | Vol Accuracy | Top SHAP Feature | Sharpe Lift |
|-------|-----------|---------|-------------|-----------------|-------------|
| P3B | Daily | 7d (7 bars) | 52.0% | `funding_7d_mean` (0.041) | +0.05 |
| P4 | 4h | 6 bars (≈1d) | **62.7%** | `trend_strength` (0.160) | -0.14 |
| P4 | 4h | 42 bars (≈7d) | **68.7%** | `trend_strength` (0.888) | 0.00 |

Vol accuracy improved dramatically at 4h (+10–17pp). But Sharpe lift did not follow — and for the 6d horizon it went negative.

---

## Honest Assessment

Phase 4 answered the questions it was designed to answer:

**✅ ARCH effects are real at 4h** — `hl_range` and `avg_hl_range` show up as genuine predictors  
**✅ Vol is more predictable at 4h than daily** — 62–69% accuracy vs 52% at daily  
**❌ Vol sizing does not improve risk-adjusted returns in crypto** — the positive vol-accuracy doesn't translate to Sharpe lift  
**❌ Direction prediction is not improved by 4h data** — it's actually worse due to label overlap  

The core issue: **the vol-sizing strategy assumes high-vol = drawdown, but in crypto high-vol = both directions.** The strategy is correct for equity portfolios but needs rethinking for crypto.

---

## What We Now Know After Four Phases

| Question | Answer |
|----------|--------|
| Can we predict direction? | Barely (50–52% accuracy), not tradeable |
| Can we predict vol? | Yes, 62–69% at 4h, 52% at daily |
| Does better vol prediction = better returns? | Not with naive vol sizing in crypto |
| What drives vol prediction? | Regime (trend_strength) at 7d+; ARCH (hl_range) at 1d |
| What drives direction prediction? | Regime only; within-regime noise is irreducible with this data |

---

## Recommended Next Steps

**Option 1: Combine direction + vol into joint sizing**
`size = P(up) × (1 − P(high_vol))`
Go long when direction is bullish AND vol is low. Go flat when direction is uncertain OR vol is high. This is the natural synthesis of all four phases of work.

**Option 2: Live forward test (deferred from Phase 3B)**
Set up a daily cron job to run both the daily direction pipeline (`run.py`) and the 4h vol pipeline (`run_vol.py`) every day. Log predictions to a Parquet file. After 60–90 days, evaluate whether the predictions had any out-of-sample skill. This is the only honest validation.

**Option 3: Regime-conditional direction model (Phase 3's Option B, still unbuilt)**
Train separate XGBoost direction models for bull and bear regimes. The fold-collapse problem (Fold 3, 4 in every phase) is caused by the model learning bull patterns and being tested on bear patterns. Regime conditioning fixes this directly.

**My recommendation:** Option 1 is a one-day implementation (combine existing models, no new data needed). Option 2 should run in parallel always. Option 3 is the theoretically correct fix for the fold-collapse problem.
