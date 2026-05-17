param(
    [string]$GateName = "G1"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
Set-Location $projectRoot

$pythonExe = "c:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper/.venv/Scripts/python.exe"

$commands = @(
    @{ Name = "py_compile"; Args = @("-m", "py_compile", "MistHelper.py") },
    @{ Name = "ruff"; Args = @("-m", "ruff", "check", "MistHelper.py", "src", "tests") },
    @{ Name = "black_check"; Args = @("-m", "black", "--check", "MistHelper.py", "src", "tests") },
    @{ Name = "mypy"; Args = @("-m", "mypy", "src", "--config-file", "pyproject.toml") },
    @{ Name = "pytest_cov"; Args = @("-m", "pytest", "--cov=src", "--cov=tests", "--cov-report=term-missing") },
    @{ Name = "misthelper_test"; Args = @("MistHelper.py", "--test") }
)

Write-Host "Running Wave 1 gate: $GateName" -ForegroundColor Cyan

foreach ($entry in $commands) {
    $displayCmd = "$pythonExe $($entry.Args -join ' ')"
    Write-Host "-> $($entry.Name): $displayCmd" -ForegroundColor Yellow
    & $pythonExe @($entry.Args)
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Gate $GateName failed at step '$($entry.Name)'"
        exit $LASTEXITCODE
    }
}

Write-Host "Gate $GateName passed." -ForegroundColor Green
exit 0
