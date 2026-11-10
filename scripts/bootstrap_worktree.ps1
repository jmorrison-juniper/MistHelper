<#
.SYNOPSIS
    Prepare the virtual environment of a MistHelper worktree on Windows.

.DESCRIPTION
    The command "git worktree add" copies the tracked files only. The directory
    .venv is not tracked, so a new worktree holds no virtual environment.
    Without that environment, pytest runs against the global interpreter, and
    every test module fails to import. Run this script one time in each new
    worktree. See issue #1866.

    The script uses UV to select Python 3.15.2 and then starts
    scripts/bootstrap_worktree.py.

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

$uv = Get-Command uv -ErrorAction SilentlyContinue  # Find UV, which selects the supported interpreter.
if (-not $uv) {  # A missing installer blocks every following step.
    Write-Error "UV is not on the PATH. Install UV, then run this script again."
    exit 1  # Report the failure to the shell.
}

$arguments = @("run", "--no-project", "--python", "3.15.2", "python", $bootstrap)  # Select Python 3.15.2 before setup.
if ($Recreate) {  # Pass the option through, because the Python script owns the behavior.
    $arguments += "--recreate"  # Add the recreate option to the argument list.
}

& $uv.Source @arguments  # Run the bootstrap with the selected interpreter.
exit $LASTEXITCODE  # Give the exit code of the bootstrap to the shell.
