# Live Forward Validation — Reference Doc

This is the live OOS test of the **vol-sizing strategy** identified as the
best-performing approach across Phase 3B / 4 / 5 / 5B walk-forward CV.

The goal: run for 60–90 days, then check whether the strategy that looked best
in-sample (`size = 1 − P(high_vol)`, 7d horizon, BTC daily) actually holds up
out-of-sample on truly unseen data.

---

## ⚡ Status at a glance (last updated 2026-05-30)

| Thing | State |
|---|---|
| **Daily predictor** | ✅ Running **locally** — task `BTC vol-regime daily logger` via `wscript.exe daily_predict.vbs`, daily **09:00 IST**, console hidden |
| **Cloud routine** (`trig_017YH8WA7fpk5nchnzNYNDFs`) | ⛔ **Disabled** — broken by Anthropic egress SSL proxy; left disabled, not deleted |
| **Predictions logged** | 7 (bars 2026-05-22 through 2026-05-29) — one gap on 2026-05-28 from a missed run (expected, harmless) |
| **First `--eval` worth running** | **~2026-06-05** (need 7 resolved days; today only 2 are resolved) |
| **Where data lands** | `data/live_predictions.parquet` + `data/model_snapshots/`, committed & pushed each run |
| **Run log** | `logs/daily_predict.log` (UTF-8, local, gitignored) |

**Fast controls:**
```powershell
# Is it on? when does it run next? did the last run succeed?
Get-ScheduledTaskInfo -TaskName "BTC vol-regime daily logger"

# Pause / resume the automatic daily run
Disable-ScheduledTask -TaskName "BTC vol-regime daily logger"
Enable-ScheduledTask  -TaskName "BTC vol-regime daily logger"

# Remove it entirely
Unregister-ScheduledTask -TaskName "BTC vol-regime daily logger" -Confirm:$false

# Run a prediction right now (also commits + pushes)
powershell -ExecutionPolicy Bypass -File scripts/daily_predict.ps1

# See what happened
Get-Content logs/daily_predict.log -Tail 40

# Evaluate accumulated predictions (after ~7 days)
venv/Scripts/python -m src.pipeline.run_live --eval
```

> The disabled cloud routine is controlled at https://claude.ai/code/routines — it
> runs in Anthropic's cloud, NOT on your laptop, and is currently off.

---

## What's deployed

The daily prediction runs **locally via Windows Task Scheduler**, not in the
cloud. See "Why local, not cloud" below for the reason.

### Windows Task Scheduler task
- **Task name:** `BTC vol-regime daily logger` (open Task Scheduler GUI to inspect)
- **What it runs:** `scripts/daily_predict.ps1` → runs `run_live`, commits the log + model snapshot, best-effort `git push`.
- **Schedule:** daily at **09:00 IST**. The time is flexible — the prediction is computed from the last *fully-closed* UTC daily bar, so any run during a given UTC day produces the same result.
- **Missed runs:** `StartWhenAvailable=True` — if the laptop was off at 09:00, the task runs as soon as it next powers on. A multi-day outage may skip a bar or two (harmless: fewer data points, never corrupt data).
- **Runs as:** current user, only when logged on. No stored password.
- **Cost:** none (local CPU). No tokens, no cloud.
- **Logs:** every run appends to `logs/daily_predict.log` (gitignored, local only).

### Why local, not cloud
The original plan was an Anthropic-hosted routine (`trig_017YH8WA7fpk5nchnzNYNDFs`,
now **disabled**). It failed because Anthropic's cloud egress proxy does TLS
interception with a self-signed CA that Python's `certifi` bundle doesn't trust —
so *every* outbound HTTPS call (Binance, alternative.me) fails with
`CERTIFICATE_VERIFY_FAILED`. The only cloud workarounds were (a) trust the proxy
CA, which may not be installed in the container, or (b) disable cert verification,
which would mean trusting proxy-altered price data. For a *validation experiment*,
ingesting untrusted prices could silently corrupt the OOS result — unacceptable.
Local execution reaches Binance directly over trusted TLS, so we run there.

The cloud routine is left disabled (not deleted) as a reference; re-enable at
https://claude.ai/code/routines/trig_017YH8WA7fpk5nchnzNYNDFs only if the SSL
situation changes.

### Local execution (manual / one-off)
```bash
# Direct (what the scheduler wraps):
python -m src.pipeline.run_live --asset BTC/USDT           # predict + log
python -m src.pipeline.run_live --eval                      # evaluate (needs 7+ days resolved)
python -m src.pipeline.run_live --eval --min-days 14        # require 14 resolved before reporting

# Or run the full scheduler wrapper by hand (also commits + pushes):
powershell -ExecutionPolicy Bypass -File scripts/daily_predict.ps1
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

Each scheduled fire runs `scripts/daily_predict.ps1` on the local machine:

1. Runs `python -m src.pipeline.run_live --asset BTC/USDT` (via the repo venv):
   - Fetches latest OHLCV from Binance, funding/OI/LS-ratio derivatives, fear & greed.
   - Trains a vol XGBoost on all rows where the 7d future vol is known (~last bar minus 7).
   - Predicts P(high_vol) for the **last fully-closed** UTC daily bar.
   - Saves the fitted model to `data/model_snapshots/`.
   - Appends a row to `data/live_predictions.parquet`.
2. If the parquet changed, `git add` parquet + snapshots, commit, best-effort push.
   Otherwise logs "no change ... nothing to commit" and exits.
3. All output appends to `logs/daily_predict.log`.

**Failure handling in the wrapper:**
- Predictor exits non-zero → wrapper logs the failure and makes no commit.
- `git push` fails (offline etc.) → non-fatal; the commit stays local and the next successful run pushes everything.

**What can still go wrong (worth checking weekly — `tail logs/daily_predict.log`):**
- Laptop off for several days → those bars are skipped (fewer data points, not corruption).
- Binance rate-limit / outage → that day's run fails; check the log, re-run by hand.
- Schema drift if you change `_SNAPSHOT_FEATURES` or `XGBoostDirectionModel` → old parquet rows get NaN for new cols (fine); old pickles may not load under new code (only matters if you reload them).

---

## Controlling the task

All via the Windows **Task Scheduler** GUI (search "Task Scheduler", find `BTC vol-regime daily logger`) or PowerShell:

| Action | How (PowerShell) |
|---|---|
| Run once now | `Start-ScheduledTask -TaskName "BTC vol-regime daily logger"` |
| See last result / next run | `Get-ScheduledTaskInfo -TaskName "BTC vol-regime daily logger"` |
| Disable temporarily | `Disable-ScheduledTask -TaskName "BTC vol-regime daily logger"` |
| Re-enable | `Enable-ScheduledTask -TaskName "BTC vol-regime daily logger"` |
| Change the time | `Set-ScheduledTask` with a new `New-ScheduledTaskTrigger -Daily -At "HH:mm"` |
| Delete | `Unregister-ScheduledTask -TaskName "BTC vol-regime daily logger"` |
| Inspect recent output | `Get-Content logs/daily_predict.log -Tail 40` |

Run a prediction manually anytime: `powershell -ExecutionPolicy Bypass -File scripts/daily_predict.ps1`

The disabled cloud routine (`trig_017YH8WA7fpk5nchnzNYNDFs`) is controlled separately at https://claude.ai/code/routines.

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

- [src/pipeline/run_live.py](src/pipeline/run_live.py) — the daily predictor + `--eval`
- [scripts/daily_predict.ps1](scripts/daily_predict.ps1) — Task Scheduler wrapper (run + commit + push)
- [data/live_predictions.parquet](data/live_predictions.parquet) — append-only log (first row: 2026-05-22)
- [data/model_snapshots/](data/model_snapshots/) — pickled models per day
- [config/settings.yaml](config/settings.yaml) — model + data config
- `logs/daily_predict.log` — local run log (gitignored)

## Related findings (in-sample CV results)

- [PHASE5B_ML_FINDINGS.md](PHASE5B_ML_FINDINGS.md) — full strategy comparison, why we picked vol-sizing
- Memory: `project_phase3b_findings.md` — short-form summary of all 6 phases

---

## Change log

Newest first. Each entry = what changed, why, and the commit(s).

### 2026-05-30 — Scheduler polish + first sneak-peek eval
- **Verified 7 days of unattended runs.** Predictions 2026-05-22 through 2026-05-29 logged and pushed; one bar (05-28) skipped because the laptop wasn't reachable that UTC day (the designed harmless-gap mode).
- **Hidden scheduler window via VBS launcher** — Task Scheduler now invokes `wscript.exe scripts/daily_predict.vbs` instead of `powershell.exe` directly. `powershell.exe -WindowStyle Hidden` still flashed a console on first paint; the `.vbs` Shell.Run with intWindowStyle=0 truly suppresses it. _(commit `24766d2`)_
- **Log encoding fixed** — `Add-Content -Encoding utf8` on every sink; PS 5.1's default was UTF-16 LE, which made the file read as spaced-out gibberish via Unix tools. Old log was rotated; new entries are UTF-8 + BOM.
- **Removed pandas deprecation warning** — `pd.Timestamp.utcnow()` -> `Timestamp.now(tz="UTC")` in `run_live.py`; the warning was leaking into the daily log.
- **ASCII-safe eval output** — replaced em-dash and arrow in `evaluate()` prints; cp1252 console crashed on them during the sneak-peek `--eval`.
- **Sneak-peek `--eval --min-days 2` ran cleanly** with N=2 resolved (bars 5/22, 5/23). Numbers are noise at that sample size; confirmed the report renders end-to-end. Real eval target: ~2026-06-05.

### 2026-05-23 — Live validation deployed locally
- **Decided to run locally, not in the cloud.** Set up the Anthropic-hosted routine first, but its test fire failed: the cloud egress proxy does TLS interception with a self-signed CA, so ccxt/requests reject every HTTPS call (`CERTIFICATE_VERIFY_FAILED`). The only workarounds were trusting the proxy CA (may not exist) or disabling cert verification (would risk ingesting proxy-altered prices and corrupting the validation). Chose local execution over trusted TLS instead. Cloud routine left **disabled**.
- **`run_live` now predicts from the last fully-closed UTC daily bar** (was: the in-progress bar via `iloc[-1]`). Makes the prediction independent of run time, so a local schedule can fire at any hour and a missed run can replay late without changing the result. _(commit `ec9f0f7`)_
- **Added `scripts/daily_predict.ps1`** — Task Scheduler wrapper: run predictor → commit log + snapshot → best-effort push. Fixed three PS 5.1 gotchas (ANSI/em-dash parse, `2>&1`-under-`Stop` abort, same-file `1>>`/`2>>` lock). _(commits `ec9f0f7`, `97c2c11`)_
- **Registered Windows Task Scheduler task** `BTC vol-regime daily logger`, daily 09:00 IST, `StartWhenAvailable=True`, run-when-logged-on.
- **First prediction logged & pushed:** 2026-05-22, via a manual wrapper run. _(commit `e92f3c4`)_

### 2026-05-23 — Audit instrumentation (before data accumulates)
- **Model snapshots:** each run pickles the fitted XGBoost + feat_cols + train_median to `data/model_snapshots/{date}_{asset}.pkl`. Non-backfillable — lets you reload exactly what predicted a given day.
- **Expanded feature snapshot:** log ~12 `feat_*` columns (was 3) so model inputs can be reconstructed even if feature code changes later.
- **Calibration table in `--eval`:** bins `p_high_vol` by decile vs actual high-vol rate; surfaces miscalibration that Brier alone hides. _(commit `153da78`)_

### 2026-05-16 — Bootstrapped the live logger
- **Committed `src/data/*` fetchers** that the pipeline imports but had never been pushed (cloud clone would have crashed on import). _(commit `6e0e9d2`)_
- **Made `.gitignore` granular** so `data/live_predictions.parquet` persists while OHLCV/derivative caches stay ignored. _(commit `6e0e9d2`)_
- **Wrote `src/pipeline/run_live.py`** — daily predictor + `--eval` evaluator. _(earlier commit `dc0c2ed`)_

## Planned / deferred (not done yet)

In rough priority order — revisit after ~1–2 weeks of clean single-asset runs:

1. **Confirm unattended firing** — verify the 2026-05-24 09:00 IST scheduler run actually fires and pushes (the only untested link; manual runs are proven).
2. **Extend training history to 2018/2020/2022** — biggest open lever; the bear-data scarcity (~50 bear rows in the current 1000-day window) is what broke the regime-conditional model. More bear cycles could make a bear-trained model honest enough to eventually justify short positions.
3. **Multi-asset (ETH) + multi-horizon (14d/30d) logging** — 6× the evaluation density; held off because it multiplies each run's training cost.
4. **Going short (`size ∈ [−1, 1]`)** — only after (2); shorting on the current sub-50% bear-fold direction signal would amplify losses.
5. **Weekly auto-report / Platt recalibration** — backfillable from the logs, so no rush.
