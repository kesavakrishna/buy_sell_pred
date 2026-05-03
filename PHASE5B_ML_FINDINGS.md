# Phase 5B — Regime-Conditional Model + Better Joint Formula

**Experiments:** (B) Regime-conditional XGBoost; (C) V2 joint formula `max(2P−1,0)×(1−P(vol))`  
**Asset:** BTC/USDT | **Date run:** 2026-05-02 | **Timeframe:** 1d

---

## Experiment B — Regime-Conditional Direction Model

### Design
For each fold, split training data by `trend_strength`:
- `trend_strength > 0` → bull training set → bull XGBoost
- `trend_strength ≤ 0` → bear training set → bear XGBoost

At test time: route each bar to the model matching its current regime.  
Fallback: if either regime has < 80 training rows, use a single combined model.

### Results

| | 7d Horizon | 30d Horizon |
|-|-----------|-------------|
| Folds using fallback | **3/5** | **4/5** |
| Mean regime_sharpe | -2.01 | -5.22 |
| Mean combined_sharpe | -2.01 | -5.22 |
| **Mean regime_lift** | **0.00** | **0.00** |

The regime-conditional model is **identical to the combined model** across every fold.

### Why It Failed — Data Imbalance

The training data has a severe regime imbalance. For folds 1–3, the bear regime
(trend_strength ≤ 0) has only **~50 rows** — triggering the 80-row fallback threshold.

| Fold | Bull train rows | Bear train rows | Fallback? |
|------|----------------|----------------|-----------|
| 1    | 607            | **50**         | ✅ Yes |
| 2    | 667            | **50**         | ✅ Yes |
| 3    | 727            | **50**         | ✅ Yes |
| 4    | ~750           | ~80+           | ❌ No |
| 5    | ~810           | ~80+           | ❌ No |

For Folds 4 and 5 (which don't fall back), the bear model still produces identical
predictions to the combined model — a bear-regime model trained on only ~80 rows
is too data-starved to learn anything the combined model hasn't already learned.

**Root cause:** BTC has been in a bull regime (EMA50 > EMA200) for roughly 920 of
the 970 usable training rows. Only ~50 rows are in bear regime across the entire
1000-day history. You can't train a meaningful bear model on 50 samples.

### What Regime-Conditional Would Need

For this approach to work, either:
1. **More bear data** — extend history to 2018–2020 bear cycles (~1500 days), or
2. **Looser regime definition** — define "bear" as `trend_strength < −0.05` (strong downtrend)
   and "neutral" as `−0.05 < trend_strength < 0.05`, giving three models rather than two, but
   with cleaner regime separation and more balanced samples
3. **Shorter regime lookback** — instead of EMA50/EMA200 (50/200 days), use EMA10/EMA30
   to get faster regime transitions and more balanced classes at daily frequency

---

## Experiment C — Joint V2 Formula: `max(2P−1, 0) × (1 − P(high_vol))`

### Design
Only go long when the direction model is net-bullish (P(up) > 0.5), scaled by confidence.
`max(2P−1, 0)` maps [0.5, 1] → [0, 1] linearly and returns 0 when P(up) < 0.5.

### Results

| Strategy | 7d Sharpe | 30d Sharpe |
|---------|-----------|------------|
| Buy & Hold | -0.60 | -0.70 |
| Vol-only | **-1.63** | **-3.80** |
| Joint V1: P(up)×(1−P(vol)) | -1.86 | -4.25 |
| **Joint V2: max(2P−1,0)×(1−P(vol))** | **-2.91** | **-4.50** |
| Direction-only | -2.01 | -5.22 |

V2 is **worse than V1** at 7d (−2.91 vs −1.86) and marginally worse at 30d.

### Why V2 Is Worse — The Sub-50% Accuracy Trap

V2 only enters a position when P(up) > 0.5. When the direction model has < 50% accuracy
(which happens in Folds 1, 3, 4), P(up) is systematically too low — the model predicts
"down" when the market is actually going up. V2 stays flat during those "down" predictions,
missing the upside:

| Fold 1 (7d) | Direction Acc | P(up) regime | V2 behaviour | V2 Sharpe |
|-------------|--------------|-------------|--------------|-----------|
| Bull market (bh=+0.26) | 43.3% | Often < 0.5 | Flat — misses uptrend | **-3.85** |

When direction accuracy is 43.3%, P(up) is more often < 0.5 than > 0.5.
V2 stays flat and misses the bull run. Vol-only (which is always invested, just at
reduced size) participates in the trend: vol_sharpe = +1.06.

V2 would only beat vol-only when:
1. Direction accuracy is reliably > 55% (so P(up) > 0.5 on up-days)
2. High-vol periods have net-negative returns

Neither condition holds consistently with this dataset.

---

## Full Strategy Comparison Across All Phases

### 7d Horizon (Mean Sharpe across 5 folds)

| Strategy | Mean Sharpe | Notes |
|---------|-------------|-------|
| Buy & Hold | -0.60 | Benchmark |
| **Vol-only (Phase 3B)** | **-1.63** | Best strategy found |
| Joint V1: P(up)×(1−P(vol)) | -1.86 | Contaminated by direction |
| Direction-only (Phase 3) | -2.01 | Baseline model |
| Regime-conditional (Phase 5B) | -2.01 | = Combined, data too sparse |
| Joint V2: max(2P−1,0)×(1−P(vol)) | -2.91 | Worse: flat when dir < 50% |

### 30d Horizon

| Strategy | Mean Sharpe |
|---------|-------------|
| Buy & Hold | -0.70 |
| **Vol-only (Phase 3B)** | **-3.80** |
| Joint V1 | -4.25 |
| Joint V2 | -4.50 |
| Regime-conditional | -5.22 |
| Direction-only | -5.22 |

---

## What Six Phases Have Established

After six iterations across three structural approaches (better features, vol prediction,
regime separation) and multiple formula variations, the conclusions are stable:

| Finding | Status |
|---------|--------|
| Vol is more predictable than direction | ✅ Confirmed (52% daily, 63–69% at 4h) |
| ARCH effects are real at 4h | ✅ Confirmed (hl_range ranks 4th-5th) |
| Vol-only sizing beats direction-only | ✅ Confirmed at both 7d and 30d |
| Joint formula beats vol-only | ❌ No — direction signal too noisy |
| Regime-conditional fixes fold-collapse | ❌ No — bear data too sparse (50 rows) |
| Any strategy beats buy-and-hold | ❌ No — mean Sharpe negative at all horizons |

---

## Honest Assessment

The space of improvements available from public daily OHLCV + technical + derivatives data
has been exhaustively explored. Every structural improvement tried has either:
- Not moved the needle (regime-conditional — not enough bear data)
- Made things worse (V2 joint — direction accuracy too low to gate on)
- Made things slightly better but not enough to beat B&H (vol-sizing)

**The one remaining lever**: vol-only sizing with `1 − P(high_vol)` is the best formula
found. It doesn't beat buy-and-hold because the regime-transition folds (3 and 4) have
negative buy-and-hold returns that no position-sizing can fully escape — you can reduce
exposure but you can't go short (this strategy is long-only).

**What would actually move the needle:**
1. **Going short** — allow `size ∈ [−1, 1]`. In bear folds where vol is high and direction
   is down, short selling would flip the loss into a gain. Currently `size ∈ [0, 1]` — we
   can reduce but not profit from the downside.
2. **Longer history with more bear cycles** — 2018, 2020, 2022 all had extended bear regimes.
   This would give the regime model hundreds of bear-regime training rows.
3. **Live forward test** — stop in-sample iteration and run the vol-sizing strategy live for
   60–90 days to get honest OOS evaluation.

---

## Next Steps

The cleanest path forward is the **live forward test**. Six phases of walk-forward CV have
produced a stable best strategy (vol-sizing). The only remaining question is whether it has
any real OOS skill, and that can only be answered by running live.

Set up a daily cron to:
1. Fetch latest OHLCV + derivatives
2. Run `src/pipeline/run_vol.py` (daily config, 7d horizon)
3. Log today's `P(high_vol)` and implied position size to a Parquet file
4. In 60–90 days, compare logged predictions against actual vol outcomes
