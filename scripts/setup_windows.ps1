# Pickup Pal Windows setup helper (run in PowerShell)
# Does everything that can be automated. You still need one browser login for gcloud.

$ErrorActionPreference = "Stop"

Write-Host "=== Pickup Pal Windows Setup ===" -ForegroundColor Cyan

# Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found. Install from https://www.python.org/downloads/ (check Add to PATH)" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python: $(python --version)"

# gcloud
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "gcloud not found. Install from https://cloud.google.com/sdk" -ForegroundColor Red
    exit 1
}
Write-Host "✓ gcloud found"

# Project
$project = gcloud config get-value project 2>$null
if ($project -ne "wf-gcp-us-ae-global-tnd-prod") {
    Write-Host "Setting gcloud project..." -ForegroundColor Yellow
    gcloud config set project wf-gcp-us-ae-global-tnd-prod
}
Write-Host "✓ Project: wf-gcp-us-ae-global-tnd-prod"

# ADC login (opens browser — cannot be skipped)
Write-Host "`nOpening browser for Google login..." -ForegroundColor Yellow
gcloud auth application-default login

# Python deps
Write-Host "`nInstalling Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Validate
python scripts/validate_setup.py --skip-slack

Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host "Open this folder in Cursor, then ask Agent:"
Write-Host '  "How many pickups does Fusion Furniture have this week?"'
