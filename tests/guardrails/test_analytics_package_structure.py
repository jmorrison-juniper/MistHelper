"""Guard the issue #3992 analytics package structure and canonical site paths."""

from __future__ import annotations  # Use current annotation behavior in the guard.

import logging  # Report each external read and measured scan result.
import re  # Detect removed dotted imports and repository file paths.
import subprocess  # Read the authoritative tracked file set from Git.
from pathlib import Path  # Inspect package levels with platform-safe paths.

import pytest  # Prove each required guard failure mode.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Resolve the current repository checkout.
ANALYTICS_ROOT = REPOSITORY_ROOT / "src" / "mist" / "intelligence" / "analytics"  # Bound the scan.
EXCLUDED_NAMES = {"__init__.py", "__pycache__", ".mypy_cache", ".pytest_cache"}  # Ignore metadata.
TEXT_SUFFIXES = {  # Limit the active scan to maintained text file formats.
    ".cfg",
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
PRESERVATION_PATHS = {  # Permit exact old paths only in active move-preservation contracts.
    Path("tests/guardrails/test_performance_hook_catalog.py"),
}
OLD_MODULE_NAMES = (  # Name the three modules that moved into the site package.
    "site_analytics_configurator",
    "site_inventory_health_analyzer",
    "zone_analyzer",
)
OLD_SITE_PATH = re.compile(  # Match removed dotted imports, parent imports, and slash paths.
    r"src" + r"\.mist\.intelligence\.analytics\.(?:" + "|".join(OLD_MODULE_NAMES) + r")"
    r"|from\s+src\.mist\.intelligence\.analytics\s+import\s+(?:" + "|".join(OLD_MODULE_NAMES) + r")"
    r"|src/mist/intelligence/analytics/(?:" + "|".join(OLD_MODULE_NAMES) + r")\.py"
)
LOGGER = logging.getLogger(__name__)  # Share one logger for guard actions and failures.


class AnalyticsStructureInspector:
    """Inspect approved analytics package levels and active canonical paths."""

    def __init__(
        self,
        analytics_root: Path,
        repository_root: Path,
        required_packages: tuple[str, ...] = ("", "site"),
    ) -> None:
        """Store the bounded package root, repository root, and required packages."""
        self.analytics_root = analytics_root  # Keep hierarchy checks inside the approved package.
        self.repository_root = repository_root  # Build stable repository-relative result paths.
        self.required_packages = required_packages  # Validate each required directory before counting.

    @staticmethod
    def _visible_children(directory: Path) -> list[Path]:
        """Return direct structural children after metadata exclusions."""
        return sorted(  # Keep inspection order stable across operating systems.
            child for child in directory.iterdir() if child.name not in EXCLUDED_NAMES
        )

    def _package_directories(self) -> list[Path]:
        """Return each required readable package directory."""
        directories = [self.analytics_root / relative_path for relative_path in self.required_packages]
        missing = [directory for directory in directories if not directory.is_dir()]  # Validate all inputs first.
        if missing:  # A partial result cannot prove the package hierarchy.
            missing_paths = [str(path) for path in missing]  # Preserve each absent required path.
            raise AssertionError(f"Cannot inspect required analytics directories: {missing_paths}")
        return directories  # Return only the explicitly approved package levels.

    def inspect(self) -> dict[str, int]:
        """Return measured counts and reject a sixth structural child."""
        directories = self._package_directories()  # Fail before any partial count result.
        counts = {  # Preserve each checked directory and measured direct-child count.
            directory.relative_to(self.repository_root).as_posix(): len(self._visible_children(directory))
            for directory in directories
        }
        violations = {path: count for path, count in counts.items() if count > 5}  # Find excess children.
        message = f"Checked {len(counts)} analytics package directories. Violations: {violations}"
        assert not violations, message  # Report the checked count, path, and measured violation.
        print(f"Checked {len(counts)} analytics package directories: {counts}")  # Report passing scope.
        return counts  # Let the repository test require the exact approved hierarchy.


class ActiveAnalyticsPathScanner:
    """Inspect tracked active files for removed analytics paths."""

    def __init__(self, repository_root: Path) -> None:
        """Store the repository root for Git and file reads."""
        self.repository_root = repository_root  # Keep all scan paths inside the active checkout.

    def _tracked_paths(self) -> list[Path]:
        """Return the tracked repository paths or fail with the Git cause."""
        LOGGER.info("Reading tracked files for the analytics path guard")  # Announce the external Git read.
        try:
            result = subprocess.run(  # Ask Git for the required tracked file inventory.
                ["git", "ls-files", "-z"],
                cwd=self.repository_root,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as error:  # Convert a missing input into a clear guard failure.
            LOGGER.error("Cannot read tracked files for the analytics path guard: code %s", error.returncode)
            raise AssertionError(
                f"Cannot inspect tracked active files: git ls-files failed with code {error.returncode}"
            ) from error
        tracked_paths = [  # Decode each null-delimited repository-relative path.
            Path(value.decode("utf-8")) for value in result.stdout.split(b"\0") if value
        ]
        LOGGER.debug("Read %s tracked files for the analytics path guard", len(tracked_paths))
        return tracked_paths  # Supply the complete tracked inventory for active-path filtering.

    @staticmethod
    def _active_paths(tracked_paths: list[Path]) -> list[Path]:
        """Return maintained text paths outside immutable process records."""
        return [  # Keep all maintained text except historical specifications and released history.
            path
            for path in tracked_paths
            if path.suffix.lower() in TEXT_SUFFIXES
            and path.parts
            and path.parts[0] != "specs"
            and path.as_posix() != "CHANGELOG.md"
            and path not in PRESERVATION_PATHS
        ]

    def active_path_violations(self) -> list[str]:
        """Return tracked active files that still name a removed analytics path."""
        active_paths = self._active_paths(self._tracked_paths())  # Select maintained text from the Git inventory.
        LOGGER.info("Scanning %s active files for removed analytics paths", len(active_paths))
        violations = []  # Collect each violating path once for stable failure output.
        for path in active_paths:  # Read each maintained text file with one explicit path.
            absolute_path = self.repository_root / path  # Resolve the tracked path inside the checkout.
            if absolute_path.is_file() and OLD_SITE_PATH.search(absolute_path.read_text(encoding="utf-8")):
                violations.append(path.as_posix())  # Preserve the repository-relative violating path.
        LOGGER.debug("Found %s removed analytics path references", len(violations))
        return sorted(violations)  # Keep failure output stable across Git and operating systems.


class TestAnalyticsPackageStructure:
    """Prove the bounded hierarchy and each required failure result."""

    def test_repository_structure_and_paths(self) -> None:
        """Require exact package counts and canonical active site paths."""
        inspector = AnalyticsStructureInspector(ANALYTICS_ROOT, REPOSITORY_ROOT)  # Inspect the live package.
        counts = inspector.inspect()  # Require both approved package levels.
        assert counts == {  # Fix the exact issue #3992 hierarchy and measured checked count.
            "src/mist/intelligence/analytics": 4,
            "src/mist/intelligence/analytics/site": 3,
        }
        scanner = ActiveAnalyticsPathScanner(REPOSITORY_ROOT)  # Scan the complete maintained tracked surface.
        assert scanner.active_path_violations() == []  # Reject each removed active analytics path.

    def test_sixth_child_fails_with_measured_count(self, tmp_path: Path) -> None:
        """Prove that one checked package with six children fails."""
        analytics_root = tmp_path / "analytics"  # Build one isolated package for the failure proof.
        analytics_root.mkdir()  # Create the required package root.
        (analytics_root / "__init__.py").write_text('"""Test package."""\n', encoding="utf-8")
        for child_number in range(6):  # Create exactly one child above the approved maximum.
            (analytics_root / f"child_{child_number}.py").write_text("", encoding="utf-8")
        inspector = AnalyticsStructureInspector(analytics_root, tmp_path, ("",))  # Check one directory.
        with pytest.raises(AssertionError, match=r"Checked 1 .*'analytics': 6"):  # Require the six-child failure.
            inspector.inspect()  # Trigger the controlled structural failure.

    def test_missing_root_fails_with_path_and_cause(self, tmp_path: Path) -> None:
        """Prove that an absent root fails with its path and inspection cause."""
        missing_root = tmp_path / "missing-analytics"  # Name a package root that does not exist.
        inspector = AnalyticsStructureInspector(missing_root, tmp_path)  # Configure the absent root.
        with pytest.raises(
            AssertionError,
            match=rf"Cannot inspect.*{re.escape(str(missing_root))}",
        ):  # Require the missing path.
            inspector.inspect()  # Trigger the required input failure.

    def test_active_old_path_is_reported(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Prove that one tracked active old path reports its filename."""
        source_path = Path("src") / "sample.py"  # Use one controlled active source file.
        absolute_path = tmp_path / source_path  # Resolve the tracked file in the temporary repository.
        absolute_path.parent.mkdir()  # Create the active source directory.
        old_module = "zone_" + "analyzer"  # Avoid naming the removed full path in this guard.
        absolute_path.write_text(  # Add one removed import path for the direct failure proof.
            f"from src.mist.intelligence.analytics.{old_module} import ZoneConfigurationAnalyzer\n",
            encoding="utf-8",
        )  # Persist the controlled source file.
        completed = subprocess.CompletedProcess(
            [], 0, stdout=f"{source_path.as_posix()}\0".encode()
        )  # Mock one tracked active file.
        monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: completed)
        scanner = ActiveAnalyticsPathScanner(tmp_path)  # Use the controlled repository inventory.
        assert scanner.active_path_violations() == ["src/sample.py"]  # Require the violating filename.

    def test_git_input_failure_reports_cause(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Prove that a failed tracked-file read stops with its cause."""

        def fail_git(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
            """Raise the Git failure that the inspector must report."""
            raise subprocess.CalledProcessError(2, ["git", "ls-files", "-z"])  # Simulate an unreadable inventory.

        monkeypatch.setattr(subprocess, "run", fail_git)  # Replace Git with one controlled failure.
        scanner = ActiveAnalyticsPathScanner(tmp_path)  # Use the controlled repository root.
        with pytest.raises(AssertionError, match=r"git ls-files failed with code 2"):  # Require the Git failure cause.
            scanner.active_path_violations()  # Trigger the required tracked-input failure.
