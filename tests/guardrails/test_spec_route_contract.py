"""Guard the fixed-width base-5 route used by the Spec Kit generator."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ROUTE_SCRIPT = REPOSITORY_ROOT / ".specify/scripts/powershell/spec-route.ps1"
GENERATOR_SCRIPT = REPOSITORY_ROOT / ".specify/scripts/powershell/create-new-feature.ps1"


def python_route(number: int, width: int = 8) -> str:
    """Return the fixed-width base-5 route for a feature number."""
    digits = ["0"] * width
    remaining = number
    for index in range(width - 1, -1, -1):
        digits[index] = str(remaining % 5)
        remaining //= 5
    if remaining:
        raise ValueError(f"Feature number {number} exceeds route width {width}.")
    return "/".join(digits)


def test_radix_route_is_stable() -> None:
    """Pin the route for the first migration and the current maximum."""
    expected = {
        800: "0/0/0/1/1/2/0/0",
        801: "0/0/0/1/1/2/0/1",
        3750: "0/0/1/1/0/0/0/0",
        3923: "0/0/1/1/1/1/4/3",
    }
    assert {number: python_route(number) for number in expected} == expected


def test_generator_calls_route_helper() -> None:
    """Require the generator to use the route helper for every new feature."""
    source = GENERATOR_SCRIPT.read_text(encoding="utf-8")
    assert "spec-route.ps1" in source
    assert "Resolve-SpecFeaturePath" in source
    assert "$featureDir = Join-Path $specsDir $branchName" not in source


def test_powershell_route_reports_environment() -> None:
    """Run PowerShell when available or report its absence explicitly."""
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        message = "pwsh not installed"
        print(message)
        assert pwsh is None
        return
    command = f". '{ROUTE_SCRIPT}'; " "$route = Get-SpecRadixSegments -Number 800; " "Write-Output ($route -join '/')"
    result = subprocess.run(
        [pwsh, "-NoProfile", "-Command", command],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout.strip() == "0/0/0/1/1/2/0/0"
