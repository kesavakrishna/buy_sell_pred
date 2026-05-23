<#
.SYNOPSIS
    Daily vol-regime prediction logger — wrapper for Windows Task Scheduler.

.DESCRIPTION
    Runs src.pipeline.run_live to log today's BTC vol prediction, then commits
    and pushes the updated log + model snapshot. Designed to be run unattended
    by Task Scheduler. All output is appended to logs/daily_predict.log.

    The prediction is computed from the last fully-closed daily bar, so it does
    not matter what time of day this fires — any run during a given UTC day
    produces the same result. If the machine was off at the scheduled time,
    Task Scheduler's "run as soon as possible after a missed start" replays it.

    Git push is best-effort: if it fails (e.g. offline), the local parquet is
    still the source of truth and the next successful run will push everything.
#>

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot "venv\Scripts\python.exe"
$LogDir = Join-Path $RepoRoot "logs"
$LogFile = Join-Path $LogDir "daily_predict.log"

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

function Log($msg) {
    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    "$ts  $msg" | Tee-Object -FilePath $LogFile -Append
}

Set-Location $RepoRoot
Log "=== daily_predict start ==="

# 1. Run the predictor. Capture combined output.
$predictOut = & $Python -m src.pipeline.run_live --asset BTC/USDT 2>&1 | Out-String
$predictOut.TrimEnd().Split("`n") | ForEach-Object { Log $_ }

if ($LASTEXITCODE -ne 0) {
    Log "PREDICTOR FAILED (exit $LASTEXITCODE) — no commit attempted."
    Log "=== daily_predict end (failure) ==="
    exit 1
}

# 2. Commit only if the prediction log actually changed.
$changed = git status --porcelain data/live_predictions.parquet data/model_snapshots/
if ([string]::IsNullOrWhiteSpace($changed)) {
    Log "No change to prediction log — nothing to commit (likely already logged today)."
    Log "=== daily_predict end (no-op) ==="
    exit 0
}

$today = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
git add data/live_predictions.parquet data/model_snapshots/
git commit -m "Log daily vol prediction $today" | ForEach-Object { Log $_ }

# 3. Best-effort push. A failure here is non-fatal — local parquet persists.
try {
    git push origin main 2>&1 | ForEach-Object { Log $_ }
    if ($LASTEXITCODE -ne 0) { throw "git push exited $LASTEXITCODE" }
    Log "Pushed to origin/main."
} catch {
    Log "PUSH FAILED (non-fatal): $_  — committed locally; next run will push."
}

Log "=== daily_predict end (logged) ==="
exit 0
