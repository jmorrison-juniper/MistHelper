param(
    [string]$GateName = "G1"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
Set-Location $projectRoot

$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Error "Gate requires an isolated virtual environment at $pythonExe"
    exit 1
}

$commands = @(
    @{ Name = "py_compile"; Args = @("-m", "py_compile", "MistHelper.py") },
    @{ Name = "ruff"; Args = @("-m", "ruff", "check", "MistHelper.py", "src", "tests") },
    @{ Name = "black_check"; Args = @("-m", "black", "--check", "MistHelper.py", "src", "tests") },
    @{ Name = "mypy"; Args = @("-m", "mypy", "src", "--config-file", "pyproject.toml") },
    @{ Name = "pytest_cov"; Args = @("-m", "pytest", "-m", "not integration", "--cov=src", "--cov=tests", "--cov-report=term-missing") },
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
