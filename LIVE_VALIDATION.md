# Live Forward Validation — Reference Doc

This is the live OOS test of the **vol-sizing strategy** identified as the
best-performing approach across Phase 3B / 4 / 5 / 5B walk-forward CV.

The goal: run for 60–90 days, then check whether the strategy that looked best
in-sample (`size = 1 − P(high_vol)`, 7d horizon, BTC daily) actually holds up
out-of-sample on truly unseen data.

---

## What's deployed

### Daily routine
- **What:** Anthropic-hosted scheduled agent that runs `python -m src.pipeline.run_live --asset BTC/USDT` once per day, then commits the result back to this repo.
- **Schedule:** `30 0 * * *` UTC → **00:30 UTC daily (06:00 IST)**, ~30 min after Binance's daily candle closes.
- **Routine ID:** `trig_017YH8WA7fpk5nchnzNYNDFs`
- **Dashboard:** https://claude.ai/code/routines/trig_017YH8WA7fpk5nchnzNYNDFs (view logs, run-now, disable, edit)
- **Cost:** Each fire is a real Sonnet 4.6 session — consumes plan tokens. Check usage at `claude.ai`. Expect modest per-fire cost (small handful of tool calls).
- **Lifetime:** Runs forever until disabled or deleted at the dashboard.

### Local execution (manual / smoke test)
```bash
python -m src.pipeline.run_live --asset BTC/USDT           # predict + log
python -m src.pipeline.run_live --eval                      # evaluate (needs 7+ days resolved)
python -m src.pipeline.run_live --eval --min-days 14        # require 14 resolved before reporting
python -m src.pipeline.run_live --asset BTC/USDT --config config/settings.yaml
```

---

## What gets logged each day

Two artifacts per prediction, both committed to git so they persist:

### 1. `data/live_predictions.parquet` — append-only row per (date, asset)

Columns:

| Column | Meaning |
|---|---|
| `p_high_vol` | XGBoost probability that next 7d realized vol > training median |
| `implied_size` | `1 − p_high_vol`, the position size the strategy would take ∈ [0, 1] |
| `vol_threshold` | Training median of future vol — the binarization cutoff used today |
| `train_rows` | How many rows of history the model was trained on |
| `model_snapshot` | Path to the pickled model in `data/model_snapshots/` |
| `feat_trend_strength` | (EMA50 − EMA200) / EMA200 — regime indicator |
| `feat_close_vs_ema200` | Close relative to EMA200 (long-term regime) |
| `feat_vol_7d`, `feat_vol_14d`, `feat_vol_30d` | Trailing realized vol at multiple horizons |
| `feat_vol_3b` | 3-bar trailing vol (ARCH proxy) |
| `feat_funding_7d_mean`, `feat_funding_30d_mean` | Funding rate context — top vol predictor per SHAP |
| `feat_hl_range` | log(high/low) — intra-bar range, ARCH signal |
| `feat_rsi` | 14-day RSI |
| `feat_fear_greed` | Alternative.me fear & greed index |
| `feat_return_7d` | Trailing 7d log return |

**Why log features:** they're nominally backfillable from OHLCV, but only as long as feature-engineering code doesn't change. Snapshotting them locks in what the model actually saw, so a future code change won't invalidate audits.

### 2. `data/model_snapshots/{date}_{asset}.pkl` — pickled training state

Contains:
- `model` — the fitted `XGBoostDirectionModel` wrapper
- `feat_cols` — exact feature column order used for training
- `vol_threshold` — binarization cutoff
- `train_rows`, `train_median` — training-set summary stats
- `snapshot_date`, `asset`

**Why snapshot the model:** truly non-backfillable. The model on day N was trained on whatever data was available on day N with whatever code version was deployed. Tomorrow's model differs (one more day of data, possibly different code). The snapshot lets you reload exactly what predicted today's `p_high_vol` weeks later, e.g. to debug a weird prediction or to apply a new calibration retroactively.

To load:
```python
import pickle
with open("data/model_snapshots/2026-05-17_BTC_USDT.pkl", "rb") as f:
    snap = pickle.load(f)
snap["model"].predict_proba(new_X)
```

---

## Evaluation: `--eval`

After 7+ days have passed, `--eval` joins logged predictions against fresh price data to compute the actual realized vol for each prediction date, then reports:

```
============================================================
Live Prediction Evaluation — BTC/USDT (7d horizon)
============================================================
Resolved predictions : N
Date range           : YYYY-MM-DD → YYYY-MM-DD
Vol accuracy         : XX.X%
Brier score          : 0.XXXX
Strategy Sharpe      : X.XX
Buy & Hold Sharpe    : X.XX

Calibration (5 bins, gap = actual − predicted):
                          n   mean_pred   actual_rate   gap
(0.10, 0.30]              4       0.21          0.25  0.04
(0.30, 0.45]              4       0.38          0.50  0.12
...
```

### How to read this

- **Vol accuracy** — % of days the binary call (P > 0.5 → high vol predicted) matched the actual outcome. Baseline is 50%. Phase 3B daily CV got 52%; if we hit ≥55% OOS that's mild signal, ≥60% is meaningful.
- **Brier score** — calibration-aware loss. Lower is better. 0.25 = random; in-sample CV got 0.242.
- **Strategy Sharpe vs B&H** — annualized Sharpe of the vol-sized strategy vs buy-and-hold over the same window. In-sample 7d vol-only ran −1.63 mean Sharpe (worse than B&H of −0.60). If live shows a positive gap to B&H, the strategy has OOS edge.
- **Calibration table** — bins predictions into deciles, compares mean predicted P to actual high-vol rate.
  - `gap` close to 0 → well-calibrated.
  - Systematic positive gap → model under-predicts vol (too conservative on calling high-vol).
  - Systematic negative gap → model over-predicts vol (false alarms).
  - Big gaps → apply Platt scaling: `p_calibrated = sigmoid(a * logit(p) + b)` fit on the resolved predictions.

---

## Daily routine: under the hood

Each routine fire does this on Anthropic's cloud:

1. Clones `github.com/kesavakrishna/buy_sell_pred` fresh.
2. `pip install -r requirements.txt`.
3. Runs `python -m src.pipeline.run_live --asset BTC/USDT`:
   - Fetches latest OHLCV from Binance, funding/OI/LS-ratio derivatives, fear & greed.
   - Trains a vol XGBoost on all rows where the 7d future vol is known (~last bar minus 7).
   - Predicts P(high_vol) for today's last bar (whose future is unknown).
   - Saves the fitted model to `data/model_snapshots/`.
   - Appends a row to `data/live_predictions.parquet`.
4. If the parquet changed, `git add` parquet + snapshots, commit, push. Otherwise reports "no new prediction to log" and exits cleanly.

**Failure modes the routine handles:**
- Binance API unreachable → reports error, exits (no retry storm).
- Push rejected non-fast-forward → `pull --rebase`, retry push once.

**What can still go wrong (worth checking weekly):**
- Anthropic cloud IPs blocked by Binance → all runs fail. Look at routine logs.
- Schema drift if you change `_SNAPSHOT_FEATURES` or `XGBoostDirectionModel` between runs → old rows have NaN for new cols (fine), new code can't load old pickles (problem only if you try to load).

---

## Controlling the routine

| Action | How |
|---|---|
| View logs / past runs | https://claude.ai/code/routines/trig_017YH8WA7fpk5nchnzNYNDFs |
| Run once manually | Hit "Run now" on the dashboard, or `python -m src.pipeline.run_live` locally |
| Change schedule | Update via dashboard or `RemoteTrigger {action: "update"}` |
| Disable temporarily | Set `enabled: false` on the routine |
| Delete entirely | Only via https://claude.ai/code/routines (no API support) |
| Change prompt / what it does | Update via dashboard or `RemoteTrigger {action: "update"}` |

---

## What's NOT being done (and why)

- **Multi-asset / multi-horizon logging** — worth doing eventually, but each new asset/horizon multiplies the routine's runtime + token cost. Hold for 1–2 weeks until we confirm single-asset works.
- **Going short (`size ∈ [−1, 1]`)** — biggest theoretical lever per PHASE5B, but direction accuracy is sub-50% in bear folds — shorting on a wrong signal amplifies losses. Revisit after extending training history to include 2018/2020/2022 bear cycles.
- **New features / model variants** — locked at the start of the live test. Changing the model mid-test invalidates the OOS comparison.
- **Slack / email failure alerts** — operational nicety, not analytical. Add if you find yourself missing failed runs.

---

## Decision points to revisit

| When | What to check | What it means |
|---|---|---|
| Day 7 | First `--eval` runs successfully | Routine end-to-end works |
| Day 14 | Vol accuracy, Brier vs in-sample baseline | Early signal: is the model behaving as in CV? |
| Day 30 | Calibration table | If miscalibrated, apply Platt scaling and re-eval |
| Day 60 | Strategy Sharpe vs B&H | The honest answer to whether vol-sizing has OOS edge |
| Day 90 | Same metrics + drift in feature distributions | Decide whether to extend test, ship, or kill |

---

## Files in play

- [src/pipeline/run_live.py](src/pipeline/run_live.py) — the daily script
- [data/live_predictions.parquet](data/live_predictions.parquet) — append-only log (created on first routine fire)
- [data/model_snapshots/](data/model_snapshots/) — pickled models per day
- [config/settings.yaml](config/settings.yaml) — model + data config

## Related findings (in-sample CV results)

- [PHASE5B_ML_FINDINGS.md](PHASE5B_ML_FINDINGS.md) — full strategy comparison, why we picked vol-sizing
- Memory: `project_phase3b_findings.md` — short-form summary of all 6 phases
