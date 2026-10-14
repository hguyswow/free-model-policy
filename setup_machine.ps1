# Apply free-model-policy on this machine (laptop / home desktop / office desktop).
# Usage (PowerShell, from the repo folder):  powershell -ExecutionPolicy Bypass -File .\setup_machine.ps1 [-NoTraining]
# Idempotent: safe to re-run after every `git pull`.
param([switch]$NoTraining)
$ErrorActionPreference = 'Stop'
$h = Join-Path $env:LOCALAPPDATA 'hermes'
if (-not (Get-Command hermes -ErrorAction SilentlyContinue)) { throw 'hermes CLI not found on PATH' }

# 1. Hermes agent venv python (rotates on `hermes update`, so discover newest)
$py = Get-ChildItem "$h\installs\*\environments\*\venv\Scripts\python.exe" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $py) { throw "Hermes venv python not found under $h\installs" }
Write-Host "[1/5] python: $py"

# 2. Install / refresh the skill
$skillDir = Join-Path $h 'skills\free-model-policy'
New-Item -ItemType Directory -Force $skillDir | Out-Null
Copy-Item (Join-Path $PSScriptRoot 'SKILL.md') (Join-Path $skillDir 'SKILL.md') -Force
Write-Host "[2/5] skill installed: $skillDir"

# 3. muse-spark-*-contributor is a data-training tier; allow it in unattended runs unless -NoTraining
if ($NoTraining) { hermes config set security.allow_data_training_tiers_noninteractive false | Out-Null }
else { hermes config set security.allow_data_training_tiers_noninteractive true | Out-Null }
Write-Host "[3/5] data-training tiers allowed: $(-not $NoTraining)"

# 4. Default model + fallback chain (built-in ranking is used when the cron has not produced one yet)
& $py (Join-Path $PSScriptRoot 'apply_model_policy.py')
if ($LASTEXITCODE -ne 0) { throw 'apply_model_policy.py failed' }

# 5. Make the daily ranking cron re-apply the policy with THIS machine's repo path
& $py (Join-Path $PSScriptRoot 'wire_cron.py') (Join-Path $PSScriptRoot 'apply_model_policy.py')
hermes fallback list
hermes gateway restart
Write-Host 'done.'
