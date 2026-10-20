"""Prove that the tracked uv.lock file matches the declarations (issue #3400).

The guard reads ``uv.lock`` and checks that it holds every package of the two
requirements files at a version that the requirement accepts. When UV exists, it
also runs ``uv lock --check``. The guard prints the count that it examined and fails
when the lock is missing or empty.
"""

import logging
import shutil
import subprocess  # nosec B404 - runs the fixed uv command with no shell
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

logger = logging.getLogger(__name__)  # WHY: keep the guard records on the module logger.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Resolve paths from the test, not the working directory.
MINIMUM_LOCKED_PACKAGES = 150  # The measured lock holds 197 packages.


class DependencyLock:
    """Read uv.lock and compare it with the requirements files."""

    @staticmethod
    def read_versions(path: Path) -> dict[str, Version]:
        """Return the locked version of each package, and fail when the file is absent or empty."""
        if not path.is_file():  # A missing lock means the guard has nothing to check.
            raise AssertionError(f"Lock file not found: {path}")
        packages = tomllib.loads(path.read_text(encoding="utf-8")).get("package", [])  # Every locked package entry.
        versions: dict[str, Version] = {
            canonicalize_name(item["name"]): Version(item["version"]) for item in packages if "version" in item
        }
        if len(versions) < MINIMUM_LOCKED_PACKAGES:  # An almost empty lock hides drift.
            raise AssertionError(f"Lock holds {len(versions)} packages, below {MINIMUM_LOCKED_PACKAGES}")
        return versions

    @staticmethod
    def find_defects(requirements: list[Requirement], versions: dict[str, Version]) -> list[str]:
        """Return one message for each requirement that the lock does not satisfy."""
        defects: list[str] = []  # Collect every defect, so one run reports all of them.
        for requirement in requirements:
            if requirement.url:  # A Git direct reference is not a lockable version here.
                continue
            locked = versions.get(canonicalize_name(requirement.name))  # None when the package is absent.
            if locked is None:
                defects.append(f"{requirement.name}: not locked")
            elif not requirement.specifier.contains(locked, prereleases=True):
                defects.append(f"{requirement.name}: locked {locked} does not satisfy {requirement.specifier}")
        return defects

    @classmethod
    def read_requirements(cls) -> list[Requirement]:
        """Parse both requirements files and keep the lines that apply to this platform marker set."""
        found: list[Requirement] = []  # Requirements from both files.
        for name in ("requirements.txt", "requirements-dev.txt"):
            for line in (REPOSITORY_ROOT / name).read_text(encoding="utf-8").splitlines():
                text = line.split(" #")[0].strip()  # Drop trailing comments
                if text and not text.startswith("#"):
                    found.append(Requirement(text))
        return found


def test_lock_satisfies_every_requirement() -> None:
    """Fail when a requirement is missing from the lock or locked at a version that it rejects."""
    versions = DependencyLock.read_versions(REPOSITORY_ROOT / "uv.lock")  # Raises when absent.
    requirements = DependencyLock.read_requirements()
    defects = DependencyLock.find_defects(requirements, versions)
    print(f"dependency lock: {len(versions)} locked packages, {len(requirements)} requirements, {len(defects)} defects")
    assert len(requirements) >= 50, "the guard read too few requirements"
    assert defects == []


def test_lock_is_current_with_pyproject() -> None:
    """Run ``uv lock --check`` with the stored cutoff date, and skip with the cause when UV is absent."""
    uv_path = shutil.which("uv")  # The check needs the uv program.
    if uv_path is None:
        pytest.skip("uv is not installed, so uv lock --check did not run")
    options = tomllib.loads((REPOSITORY_ROOT / "uv.lock").read_text(encoding="utf-8")).get("options", {})
    command = [uv_path, "lock", "--check"]  # The lock stores its cutoff date, so pass it back.
    if "exclude-newer" in options:
        command += ["--exclude-newer", options["exclude-newer"]]
    result = subprocess.run(  # nosec B603 - fixed arguments, no shell, no user input
        command, cwd=REPOSITORY_ROOT, capture_output=True, text=True, check=False, timeout=120
    )
    logger.debug("uv lock --check exit code %s", result.returncode)
    assert result.returncode == 0, result.stderr


def test_missing_lock_fails(tmp_path: Path) -> None:
    """Prove the guard fails when the lock file is absent."""
    with pytest.raises(AssertionError, match="not found"):
        DependencyLock.read_versions(tmp_path / "uv.lock")


def test_defects_are_reported() -> None:
    """Prove the comparison reports an absent package and a rejected version."""
    versions = {"requests": Version("2.0.0")}  # Locked below the floor.
    requirements = [Requirement("requests>=2.34.2,<3"), Requirement("tqdm>=4.70.1,<5")]
    defects = DependencyLock.find_defects(requirements, versions)
    assert defects == [
        "requests: locked 2.0.0 does not satisfy <3,>=2.34.2",
        "tqdm: not locked",
    ]
