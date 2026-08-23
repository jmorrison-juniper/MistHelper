<#
.SYNOPSIS
    Prepare the virtual environment of a MistHelper worktree on Windows.

.DESCRIPTION
    The command "git worktree add" copies the tracked files only. The directory
    .venv is not tracked, so a new worktree holds no virtual environment.
    Without that environment, pytest runs against the global interpreter, and
    every test module fails to import. Run this script one time in each new
    worktree. See issue #1866.

    The script starts scripts/bootstrap_worktree.py, which does the work on
    Windows and on Linux.

.PARAMETER Recreate
    Delete the existing .venv directory before the script creates a new one.

.EXAMPLE
    .\scripts\bootstrap_worktree.ps1

.EXAMPLE
    .\scripts\bootstrap_worktree.ps1 -Recreate
#>

[CmdletBinding()]
param(
    [switch]$Recreate
)

$ErrorActionPreference = "Stop"  # Stop on the first error, so the user sees one clear failure.

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path  # Find the scripts directory of this worktree.
$bootstrap = Join-Path $scriptDir "bootstrap_worktree.py"  # Build the path of the Python bootstrap.

$python = Get-Command python -ErrorAction SilentlyContinue  # Look for the interpreter on the PATH.
if (-not $python) {  # A missing interpreter blocks every following step.
    Write-Error "Python is not on the PATH. Install Python 3.13 or newer, then run this script again."
    exit 1  # Report the failure to the shell.
}

$arguments = @($bootstrap)  # Start the argument list with the Python bootstrap.
if ($Recreate) {  # Pass the option through, because the Python script owns the behavior.
    $arguments += "--recreate"  # Add the recreate option to the argument list.
}

& $python.Source @arguments  # Run the Python bootstrap with the collected arguments.
exit $LASTEXITCODE  # Give the exit code of the bootstrap to the shell.
