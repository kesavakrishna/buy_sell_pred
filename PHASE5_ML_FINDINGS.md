# Phase 5 ML System — Joint Direction + Vol Sizing Findings

**New in Phase 5:** `size = P(up) × (1 − P(high_vol))` — both models trained per fold  
**Asset:** BTC/USDT | **Date run:** 2026-05-02 | **Timeframe:** 1d

---

## Strategy Definitions

Three strategies compared against buy-and-hold in each fold:

| Strategy | Formula | Type |
|----------|---------|------|
| Direction-only | `size = 1 if P(up) ≥ 0.5 else 0` | Binary |
| Vol-sizing | `size = 1 − P(high_vol)` | Continuous |
| **Joint** | **`size = P(up) × (1 − P(high_vol))`** | **Continuous** |
| Baseline | `size = 1` always | Continuous |

---

## Results — 7d Horizon

| Fold | Dir Acc | Vol Acc | Dir Sharpe | Vol Sharpe | **Joint Sharpe** | B&H Sharpe |
|------|---------|---------|-----------|-----------|-----------------|------------|
| 1    | 43.3%   | **76.7%** | -1.39   | +1.06      | **+0.16**       | +0.26      |
| 2    | 53.3%   | 38.3%   | -0.02     | -0.75      | **-0.93**       | -0.01      |
| 3    | 35.0%   | 56.7%   | -7.87     | -7.76      | **-7.73**       | -2.98      |
| 4    | 36.7%   | 56.7%   | -6.95     | -6.91      | **-6.97**       | -2.63      |
| 5    | 68.3%   | 48.3%   | +6.19     | +6.21      | **+6.16**       | +2.34      |
| **Mean** | **47.3%** | **55.3%** | **-2.01** | **-1.63** | **-1.86** | **-0.60** |

## Results — 30d Horizon

| Fold | Dir Acc | Vol Acc | Dir Sharpe | Vol Sharpe | **Joint Sharpe** | B&H Sharpe |
|------|---------|---------|-----------|-----------|-----------------|------------|
| 1    | 65.0%   | **81.7%** | +8.57   | **+9.11**  | +8.38           | +1.57      |
| 2    | 25.0%   | **0.0%**  | -9.19   | -2.37      | -4.45           | -0.42      |
| 3    | **8.3%**  | 36.7% | -23.19    | -23.59     | -22.99          | -4.23      |
| 4    | 33.3%   | 48.3%   | -13.25    | -13.27     | -13.30          | -2.42      |
| 5    | 73.3%   | **80.0%** | +10.97  | **+11.11** | +11.11          | +2.00      |
| **Mean** | **41.0%** | **49.3%** | **-5.22** | **-3.80** | **-4.25** | **-0.70** |

---

## Key Findings

### 1. Vol-Sizing Is the Best Single Strategy

Across both horizons, vol-sizing beats direction-only:
- 7d: vol_sharpe = −1.63 vs dir_sharpe = −2.01 (+0.38 advantage)
- 30d: vol_sharpe = −3.80 vs dir_sharpe = −5.22 (+1.42 advantage)

This is consistent with Phase 3B and Phase 4: **volatility is more predictable than direction**, and the vol model's superior accuracy translates directly into better Sharpe.

### 2. Joint Is Not Better Than Vol-Alone

The joint formula (`P(up) × (1 − P(high_vol))`) lands between the two strategies, closer to direction-only:
- 7d: joint_sharpe = −1.86 (worse than vol −1.63, better than dir −2.01)
- 30d: joint_sharpe = −4.25 (worse than vol −3.80, better than dir −5.22)

**Why:** When the direction model is wrong (which is frequent — Fold 3 at 30d: 8.3% accuracy), multiplying `P(up)` into the joint size amplifies the wrong signal. The vol model correctly identified low-vol folds but the direction model steered into losses. The joint formula dilutes the vol model's advantage.

**The math:** In Fold 3 (30d), `P(up)` is systematically too high (model predicts "up," market goes down). This inflates `joint_size = P(up) × vol_size` relative to `vol_size = 1 − P(high_vol)`. The contamination from the direction model makes joint worse than vol alone.

### 3. Fold 2 (30d): Wrong Vol Model Still Beats Direction

Fold 2 at 30d is extreme: vol_accuracy = 0% (perfectly wrong), yet vol_sharpe = −2.37 vs dir_sharpe = −9.19.

How? When P(high_vol) is systematically too low (< 0.5 everywhere), `vol_size ≈ 1 − small = ~1`, meaning the vol strategy stays mostly invested with stable, consistent exposure. The direction model (25% accuracy) was churning — flipping position many times, each flip capturing a wrong-direction return AND paying fees. Consistent wrong exposure beats active wrong trading.

This shows that **vol-sizing has an implicit anti-churn benefit** even when the vol model is inaccurate.

### 4. All Strategies Fail in Folds 3 and 4

No strategy improves on buy-and-hold in folds 3 and 4. The regime-transition collapse is unchanged:

| Period | What happened |
|--------|--------------|
| Fold 3 | Bear market onset — model trained on bull regime, all predictions wrong |
| Fold 4 | Continued bear, model slowly adapting — still poor |

This is the structural problem that five phases of work have not solved. **Technical features from OHLCV data cannot predict regime transitions**, and regime transitions are what drive the catastrophic fold losses.

### 5. When Both Models Are Accurate, Joint ≈ Vol ≈ Direction

In folds where both models are accurate (Fold 1 and 5):
- All three strategies produce similar Sharpe
- The joint formula provides no synergy — it's just a product of two things that are each already correct

**The joint formula's failure case:** It was designed to filter for "bullish + low-vol" scenarios. But in practice, the two models make mistakes on different folds. When one is right and one is wrong, their product is worse than using the better model alone.

---

## What a Better Joint Formula Would Look Like

The current `P(up) × (1 − P(high_vol))` multiplies two probabilities, meaning:
- Uncertain direction (P(up) ≈ 0.5) → position cut in half even in confirmed low-vol environments
- Wrong direction (P(up) < 0.5) → position inverted by direction model

A more robust joint formula for crypto would use an **OR gate rather than AND**:

```python
# Exit if EITHER condition is bad
size = max(2 * P(up) - 1, 0) * (1 - P(high_vol))
# max(2*P(up)-1, 0) = 0 when P(up) < 0.5, linear when P(up) > 0.5
```

This way:
- P(up) < 0.5: position = 0 (don't go long when bearish signal)
- P(up) > 0.5: position scaled by how confident the bull signal is, then adjusted for vol
- P(high_vol) high: reduces remaining position

This wasn't implemented in Phase 5 but would be the next iteration.

---

## Five-Phase Summary

| Phase | Key Change | Best Sharpe (7d) | Key Finding |
|-------|-----------|-----------------|-------------|
| P1 Logistic | Baseline | -3.27 | Technical features work; MACD doesn't |
| P2 XGBoost | Tree model | -2.62 | trend_strength is the load-bearing feature |
| P3 Derivatives | Funding rate | -2.76 | Funding is contrarian signal at 30d |
| P3B Vol (daily) | Vol target | -0.56 (baseline) | Vol > direction predictability |
| P4 Vol (4h) | GARCH features | n/a | ARCH effect confirmed; hl_range matters |
| **P5 Joint** | `P(up)×(1−P(vol))` | **-1.86** | Vol-only beats joint; fold 3/4 remain fatal |

Best achievable mean 7d Sharpe across five phases: **vol-sizing at −1.63** — still negative, but the best result produced.

---

## Honest Assessment and What's Left

After five phases, the findings are internally consistent and converging:

**What we've learned:**
1. Vol is more predictable than direction (confirmed at daily and 4h)
2. ARCH effects are real at 4h (hl_range and avg_hl_range are genuine signals)
3. Vol-sizing is the best single strategy (−1.63 at 7d vs −2.01 for direction)
4. No combination of features or formulas fixes the regime-transition collapse
5. The joint formula adds no value over vol-alone with current model accuracy

**The remaining problem:** Mean Sharpe is negative at every horizon for every strategy. The two catastrophic folds (regime transitions) dominate. This is not fixed by better models — it's fixed by either:
(a) Detecting regime transitions before they happen (requires different data, e.g. on-chain, macro)
(b) Accepting regime uncertainty and running live for 60–90 days to measure real OOS performance

**The one unbuilt option that could still matter:** Regime-conditional models (Phase 3's Option B) — train separate XGBoosts for bull and bear regimes. This directly addresses why fold 3 collapses: the bull-regime model shouldn't be tested on bear-regime data. Not guaranteed to work, but it's the last untested structural fix.

---

## Recommended Next Steps

1. **Live forward test** — the most honest option. Set up a daily script that runs the pipeline and logs today's prediction. Check back in 90 days.

2. **Regime-conditional model** — one last structural experiment. Split training data by `trend_strength > 0` (bull) and `< 0` (bear). Train separate XGBoost for each regime. Test on holdout regime. This is specifically designed to fix the fold-collapse problem.

3. **Better joint formula** — `max(2*P(up)−1, 0) × (1 − P(high_vol))` — only goes long when direction model is net bullish, then sizes down for vol. Eliminates the direction contamination when P(up) < 0.5.

The lowest-effort highest-confidence move is the live forward test. Everything else is further in-sample iteration.
