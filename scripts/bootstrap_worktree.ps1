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
    scripts/bootstrap_worktree.py. UV is found on PATH first, and then in the
    per-user folders of pip and of the standalone installer. See issue #4876.

.PARAMETER Recreate
    Delete the existing .venv directory before the script creates a new one.

.PARAMETER PublicLockIndex
    Sync from the public index for this run only, when the configured index does
    not match uv.lock. Your pip configuration is not changed. See issue #4876.

.EXAMPLE
    .\scripts\bootstrap_worktree.ps1

.EXAMPLE
    .\scripts\bootstrap_worktree.ps1 -Recreate

.EXAMPLE
    .\scripts\bootstrap_worktree.ps1 -PublicLockIndex
#>

[CmdletBinding()]
param(
    [switch]$Recreate,
    [switch]$PublicLockIndex
)

$ErrorActionPreference = "Stop"  # Stop on the first error, so the user sees one clear failure.

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path  # Find the scripts directory of this worktree.
$bootstrap = Join-Path $scriptDir "bootstrap_worktree.py"  # Build the path of the Python bootstrap.

$uv = Get-Command uv -ErrorAction SilentlyContinue  # Find UV, which selects the supported interpreter.
if (-not $uv) {  # Per-user installs live outside PATH, so search their folders next.
    # Use APPDATA when the shell shows it, and fall back to the profile default when it does not.
    $appData = if ($env:APPDATA) { $env:APPDATA } else { Join-Path $env:USERPROFILE "AppData\Roaming" }
    $userFolders = @(Join-Path $env:USERPROFILE ".local\bin")  # The standalone installer folder comes first.
    $userFolders += @(Get-ChildItem -Path (Join-Path $appData "Python\Python*\Scripts") -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending | ForEach-Object { $_.FullName })  # Newest Python first.
    foreach ($folder in $userFolders) {  # Take the first folder that holds the executable.
        $candidate = Join-Path $folder "uv.exe"  # Build the Windows executable path.
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            $uv = [pscustomobject]@{ Source = $candidate }  # Keep the shape of Get-Command, so the run line is the same.
            break  # Stop at the first match, which keeps the search order.
        }
    }
}
if (-not $uv) {  # A missing installer blocks every following step.
    Write-Error "UV was not found on PATH or in the per-user folders. Install UV, add its folder to PATH, then run this script again."
    exit 1  # Report the failure to the shell.
}

$arguments = @("run", "--no-project", "--python", "3.15.2", "python", $bootstrap)  # Select Python 3.15.2 before setup.
if ($Recreate) {  # Pass the option through, because the Python script owns the behavior.
    $arguments += "--recreate"  # Add the recreate option to the argument list.
}
if ($PublicLockIndex) {  # Pass the option through, because the Python script owns the lock policy.
    $arguments += "--public-lock-index"  # Add the public lock option to the argument list.
}

& $uv.Source @arguments  # Run the bootstrap through the selected UV command.
exit $LASTEXITCODE  # Give the exit code of the bootstrap to the shell.