#!/usr/bin/env pwsh
# MistHelper Podman Automation Script
# Run this script to build and execute MistHelper in a Podman container

param(
    [string]$OutputFormat = "sqlite",
    [string]$Menu = "11",
    [switch]$Help
)

if ($Help) {
    Write-Host "MistHelper Podman Runner" -ForegroundColor Green
    Write-Host "Usage: .\run-podman.ps1 [-OutputFormat csv|sqlite] [-Menu <option>] [-Help]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Parameters:"
    Write-Host "  -OutputFormat   Output format (csv or sqlite, default: sqlite)"
    Write-Host "  -Menu          Menu option to execute (default: 11 - Export all sites)"
    Write-Host "  -Help          Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\run-podman.ps1                    # Run with SQLite output, menu 11"
    Write-Host "  .\run-podman.ps1 -OutputFormat csv  # Run with CSV output, menu 11"
    Write-Host "  .\run-podman.ps1 -Menu 12           # Run menu 12 (device inventory)"
    exit 0
}

# Validate output format
if ($OutputFormat -notin @("csv", "sqlite")) {
    Write-Host "Error: Invalid output format. Use 'csv' or 'sqlite'" -ForegroundColor Red
    exit 1
}

Write-Host "=== MistHelper Podman Automation ===" -ForegroundColor Green
Write-Host "Output Format: $OutputFormat" -ForegroundColor Cyan
Write-Host "Menu Option: $Menu" -ForegroundColor Cyan
Write-Host "Container uses UV package manager for optimized performance" -ForegroundColor Magenta

# Detect Podman executable
$PodmanExe = $null
$PodmanPaths = @(
    "podman",  # Try PATH first
    "C:\Program Files\RedHat\Podman\podman.exe",
    "C:\Program Files (x86)\RedHat\Podman\podman.exe",
    "$env:USERPROFILE\AppData\Local\Podman\podman.exe"
)

foreach ($path in $PodmanPaths) {
    try {
        $null = & $path --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $PodmanExe = $path
            break
        }
    } catch {
        continue
    }
}

if ($null -eq $PodmanExe) {
    Write-Host "Error: Podman not found in PATH or common installation locations" -ForegroundColor Red
    Write-Host "Please ensure Podman Desktop is installed and either:" -ForegroundColor Yellow
    Write-Host "  1. Add Podman to your PATH, or" -ForegroundColor Yellow
    Write-Host "  2. Install it to the default location: C:\Program Files\RedHat\Podman\" -ForegroundColor Yellow
    Write-Host "  3. Run: python setup-podman.py for cross-platform detection" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found Podman at: $PodmanExe" -ForegroundColor Green

# Build the Podman image
Write-Host "Building Podman image..." -ForegroundColor Yellow
& $PodmanExe build -t misthelper .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to build Podman image" -ForegroundColor Red
    exit 1
}

# Create data directory if it doesn't exist
$dataDir = ".\data"
if (!(Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir -Force
    Write-Host "Created data directory: $dataDir" -ForegroundColor Green
}

# Run the container
Write-Host "Running MistHelper container..." -ForegroundColor Yellow
Write-Host "Data will be saved to: $dataDir" -ForegroundColor Cyan

& $PodmanExe run --rm -it `
    -v "$(Get-Location)\data:/app/data:Z" `
    -v "$(Get-Location)\.env:/app/.env:Z" `
    misthelper `
    python MistHelper.py --output-format $OutputFormat --menu $Menu

if ($LASTEXITCODE -eq 0) {
    Write-Host "MistHelper completed successfully!" -ForegroundColor Green
    Write-Host "Check the $dataDir directory for output files" -ForegroundColor Cyan
} else {
    Write-Host "MistHelper encountered an error" -ForegroundColor Red
    exit 1
}
