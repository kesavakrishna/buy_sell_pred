# Phase 7 — Long-History Experiment (2017–2026)

**Question:** Does extending BTC history to include the 2018-2019 and 2022 bear
cycles fix the regime-conditional model's bear-data scarcity (the open Phase 5B
blocker), and does it change the strategy's viability?

**Date run:** 2026-05-23 | **Asset:** BTC/USDT | **Timeframe:** 1d
**Config:** `config/settings_longhist.yaml` (isolated: `data_dir: data/longhist/`)
**Data:** 3201 rows, 2017-08-18 → 2026-05-23 (vs ~1000 rows in prior phases)
**CV:** 10 folds × 180-day test windows, expanding train from 2018, purge = horizon

> Isolation note: this experiment used a separate data cache and never touched
> the live validation's `data/BTC_USDT_1d.parquet` (still 1001 rows). The live
> forward test (see `LIVE_VALIDATION.md`) was unaffected.

---

## Finding 1 — Bear-data scarcity is SOLVED

Every one of the 20 fold-runs (10 folds × {7d, 30d}) reported `fallback=0.0`.
With 8 years of data, every fold has ≥80 bull **and** ≥80 bear training rows,
so the regime-conditional model trains properly instead of collapsing to the
combined fallback.

Recall Phase 5B (1000-day window): bear regime had only ~50 rows, triggering the
80-row fallback in 3-4 of 5 folds. **That blocker was purely a data-window
artifact, now resolved.**

## Finding 2 — Regime-conditional STILL doesn't beat combined

| | 7d | 30d |
|-|----|-----|
| Mean regime_lift (regime − combined Sharpe) | **−0.03** | **−0.78** |
| Std of lift | 0.86 | 1.42 |

Even with adequate bear data, splitting into separate bull/bear models gives no
edge — essentially zero at 7d, negative at 30d. The fold-by-fold lift is noisy
(sometimes +1, sometimes −1.8) with no consistent direction.

**Conclusion: the regime-conditional approach is closed.** It wasn't a data
problem — separating models by trend regime simply doesn't improve on a single
model that has the regime features available to it anyway.

## Finding 3 — With long history, the model beats buy-and-hold on average

| Horizon | Combined Sharpe | Regime Sharpe | Buy & Hold | Dir. accuracy |
|---|---|---|---|---|
| 7d  | **+1.07** | +1.05 | +0.28 | 53.5% |
| 30d | **+2.51** | +1.74 | +0.27 | 56.8% |

This **reverses the Phase 5B headline** ("nothing beats buy-and-hold; all Sharpes
negative"). Two reasons the earlier conclusion was too pessimistic:

1. **Short window was mostly bull** — the 1000-day window (Aug 2023 → May 2026)
   barely contained a bear regime, so the model never learned bear dynamics and
   the few transition folds dominated a 5-fold mean.
2. **Too few folds** — 5 folds meant 1-2 catastrophic regime-transition folds
   swamped the average. With 10 folds over 8 years, good and bad folds average
   out to a positive mean.

Direction accuracy rose from ~47% (short history) to **53-57%** — more data gives
a more stable, genuinely above-50% signal.

### Important caveat — not "alpha", just "less bad + more stable"

- Sharpe **variance is huge** (std 2.6 at 7d, 7.4 at 30d).
- The **2022-bear folds (2-3) are still catastrophic**: −9 to −11 Sharpe at 30d.
  Position sizing can reduce but not escape a long-only strategy in a sustained
  downtrend.
- The positive mean is **averaging over more bull folds**, not evidence the model
  handles bears. The unsolved problem (long-only can't profit from downtrends) is
  unchanged — it's just diluted across more folds.

## Finding 4 — Funding dominates across full history

Top features (30d bull model): `funding_30d_mean` (0.43), `macd_signal` (0.40),
`funding_7d_mean` (0.24), `trend_strength` (0.17), `vol_30d` (0.16). Funding rate
is confirmed as the dominant signal over the entire 2017-2026 history, consistent
with every prior phase.

---

## Implications

1. **Close the regime-conditional line.** Confirmed across both data regimes
   (scarce and abundant bear data) that it doesn't help.
2. **Train on full history, not 1000 days.** The single most actionable result:
   more history → more stable, above-50% direction accuracy and positive mean
   Sharpe. The live predictor currently caps at `days_back: 1000`; it should use
   full history.
3. **Long-only remains the ceiling.** Even with 8 years and positive mean Sharpe,
   the 2022-bear folds are disasters. The next real lever is allowing short
   positions (`size ∈ [−1, 1]`) — now more justified, because the model has
   real bear-regime training data and ~53% accuracy to gate on.

## What this does NOT change

- The live forward test stays as-is unless we explicitly decide to widen its
  training window (a separate, logged decision).
- This is in-sample CV on 8 years — better than before, but still in-sample. The
  live test remains the honest OOS check.
