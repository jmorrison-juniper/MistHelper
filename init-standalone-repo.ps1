# Quick Migration Script for PowerShell
# Run this from the MistHelper directory to initialize standalone repository

Write-Host "MistHelper Standalone Repository Initialization" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$currentPath = Get-Location
$expectedPath = "*\MistHelper"

if ($currentPath -notlike $expectedPath) {
    Write-Host "ERROR: Please run this script from the MistHelper directory" -ForegroundColor Red
    exit 1
}

# Check if .git already exists
if (Test-Path .git) {
    Write-Host "WARNING: .git directory already exists" -ForegroundColor Yellow
    $confirm = Read-Host "Do you want to reinitialize? This will delete existing Git history (yes/no)"
    if ($confirm -ne "yes") {
        Write-Host "Migration cancelled" -ForegroundColor Yellow
        exit 0
    }
    Remove-Item -Recurse -Force .git
}

Write-Host "Step 1: Initializing Git repository..." -ForegroundColor Green
git init

Write-Host "Step 2: Adding all files..." -ForegroundColor Green
git add .

Write-Host "Step 3: Creating initial commit..." -ForegroundColor Green
git commit -m "Initial commit: MistHelper v2.1.0 - Standalone repository migration"

Write-Host ""
Write-Host "Local repository initialized successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Create repository on GitHub: jmorrison-juniper/MistHelper"
Write-Host "2. Run these commands:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   git remote add origin https://github.com/jmorrison-juniper/MistHelper.git" -ForegroundColor White
Write-Host "   git branch -M main" -ForegroundColor White
Write-Host "   git push -u origin main" -ForegroundColor White
Write-Host ""
Write-Host "Or use GitHub CLI:" -ForegroundColor Yellow
Write-Host "   gh repo create jmorrison-juniper/MistHelper --public --source=. --push" -ForegroundColor White
Write-Host ""
