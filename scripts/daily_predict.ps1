<#
.SYNOPSIS
    Daily vol-regime prediction logger - wrapper for Windows Task Scheduler.

.DESCRIPTION
    Runs src.pipeline.run_live to log today's BTC vol prediction, then commits
    and pushes the updated log + model snapshot. Designed to be run unattended
    by Task Scheduler. All output is appended to logs/daily_predict.log.

    The prediction is computed from the last fully-closed daily bar, so it does
    not matter what time of day this fires: any run during a given UTC day
    produces the same result. If the machine was off at the scheduled time,
    Task Scheduler's "run as soon as possible after a missed start" replays it.

    Git push is best-effort: if it fails (e.g. offline), the local parquet is
    still the source of truth and the next successful run will push everything.

    NOTES on PowerShell 5.1:
    - Keep this file ASCII-only. PS 5.1 reads .ps1 as ANSI without a BOM, so
      non-ASCII punctuation breaks the parser.
    - Native stderr is redirected to the log with file operators (1>>/2>>),
      NOT piped via 2>&1. Piping a native command's stderr wraps each line in
      an ErrorRecord, which aborts under ErrorActionPreference=Stop even on a
      clean exit. We check $LASTEXITCODE for real success/failure instead.
#>

$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot "venv\Scripts\python.exe"
$LogDir = Join-Path $RepoRoot "logs"
$LogFile = Join-Path $LogDir "daily_predict.log"

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

function Log($msg) {
    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $line = "$ts  $msg"
    Write-Host $line
    Add-Content -Path $LogFile -Encoding utf8 -Value $line
}

Set-Location $RepoRoot
Log "=== daily_predict start ==="

# 1. Run the predictor. Merge stderr into stdout (single stream) and append to
#    the log. $LASTEXITCODE still reflects python's real exit code.
& $Python -m src.pipeline.run_live --asset BTC/USDT 2>&1 | Add-Content -Path $LogFile -Encoding utf8
$exit = $LASTEXITCODE

if ($exit -ne 0) {
    Log "PREDICTOR FAILED (exit $exit) - no commit attempted. See output above."
    Log "=== daily_predict end (failure) ==="
    exit 1
}

# 2. Commit only if the prediction log actually changed.
$changed = git status --porcelain data/live_predictions.parquet data/model_snapshots/
if ([string]::IsNullOrWhiteSpace($changed)) {
    Log "No change to prediction log - nothing to commit (likely already logged today)."
    Log "=== daily_predict end (no-op) ==="
    exit 0
}

$today = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
git add data/live_predictions.parquet data/model_snapshots/ 2>&1 | Add-Content -Path $LogFile -Encoding utf8
git commit -m "Log daily vol prediction $today" 2>&1 | Add-Content -Path $LogFile -Encoding utf8
Log "Committed prediction for $today."

# 3. Best-effort push. A failure here is non-fatal: local parquet persists.
git push origin main 2>&1 | Add-Content -Path $LogFile -Encoding utf8
if ($LASTEXITCODE -eq 0) {
    Log "Pushed to origin/main."
} else {
    Log "PUSH FAILED (non-fatal, exit $LASTEXITCODE) - committed locally; next run will push."
}

Log "=== daily_predict end (logged) ==="
exit 0
