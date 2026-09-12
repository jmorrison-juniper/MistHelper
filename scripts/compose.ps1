<#
.SYNOPSIS
    Start or stop the MistHelper container stack with a working compose provider.

.DESCRIPTION
    The command "podman compose" delegates to an external provider. On this
    machine that provider is docker-compose.exe, which resolves the bind mount
    "./data" to an absolute Windows path and sends it over the podman API:

        C:\Users\...\data:/app/data:rw

    That text holds three colons, because the drive letter carries one. The
    volume parser of the API allows two, so it refuses the whole service with
    the message "incorrect volume format". The two database services start,
    the application service does not, and the message names no service. See
    issue #2184.

    The native provider podman-compose drives the podman command line instead
    of the API, and that parser understands a drive letter. This script finds
    the native provider and runs it, so one command works on every platform.

    The script passes every argument through, so it accepts the whole compose
    command set.

.EXAMPLE
    .\scripts\compose.ps1 up -d

.EXAMPLE
    .\scripts\compose.ps1 down

.EXAMPLE
    .\scripts\compose.ps1 logs -f misthelper
#>

# Warning: this script declares no param block on purpose, and it reads the
# automatic variable $args instead. A declared parameter makes PowerShell treat
# a compose flag as a parameter name. The flag -d never reached the provider,
# so "up -d" ran as "up". The provider then stayed attached, it streamed the
# container logs, and the command never returned. An operator who stops that
# command can leave a part of the stack behind.

$ErrorActionPreference = "Stop"  # Stop on the first error, so the user sees one clear failure.

$ComposeArguments = $args  # The automatic variable keeps every flag word for word.

# The repository root holds compose.yml. The script runs from any directory,
# so it resolves the root from its own location.
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $RepositoryRoot "compose.yml"

if (-not (Test-Path $ComposeFile)) {
    throw "No compose.yml exists at $ComposeFile. Run this script from the MistHelper repository."
}

# Find the interpreter that holds the native provider. The virtual environment
# of the worktree comes first, because bootstrap_worktree.ps1 creates it and
# every other tool of this repository already uses it.
$VenvPython = Join-Path $RepositoryRoot ".venv\Scripts\python.exe"
$Interpreter = if (Test-Path $VenvPython) { $VenvPython } else { "python" }

# Test the provider before the run. A missing provider must name the install
# command, because the failure of the external provider names a volume format
# and never names the true cause.
& $Interpreter -m podman_compose version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "The native compose provider is absent." -ForegroundColor Yellow
    Write-Host "Install it with this command, then run this script again:" -ForegroundColor Yellow
    Write-Host "    $Interpreter -m pip install podman-compose" -ForegroundColor Cyan
    throw "podman-compose is required on Windows. See issue #2184."
}

if (-not $ComposeArguments) {
    $ComposeArguments = @("up", "-d")  # The command that an operator runs most.
}

Write-Host "Running the stack with the native compose provider." -ForegroundColor Green
& $Interpreter -m podman_compose -f $ComposeFile @ComposeArguments
exit $LASTEXITCODE  # Report the status of the provider, so a script that calls this one sees a failure.
