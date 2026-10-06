"""Guard the bounded persistence package structure and canonical writer paths."""

from __future__ import annotations  # Use current annotation behavior in the guard.

import re  # Detect both Python imports and repository file paths.
import subprocess  # Read the tracked repository file set from Git.
from pathlib import Path  # Inspect package levels with platform-safe paths.

import pytest  # Prove each required guard failure mode.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Resolve the current repository checkout.
PERSISTENCE_ROOT = REPOSITORY_ROOT / "src" / "foundation" / "persistence"  # Limit the hierarchy scope.
OLD_WRITER_PATH = re.compile(  # Match each removed dotted, imported, or slash path.
    r"src\.foundation\.persistence\.db\.(?:arango_writer|redis_writer)"
    r"|from\s+src\.foundation\.persistence\.db\s+import\s+(?:arango_writer|redis_writer)"
    r"|src/foundation/persistence/db/(?:arango_writer|redis_writer)\.py"
)


class PersistenceStructureInspector:
    """Inspect the approved persistence package levels and active canonical paths."""

    def __init__(self, persistence_root: Path, repository_root: Path) -> None:
        """Store the bounded package root and repository root."""
        self.persistence_root = persistence_root  # Keep the hierarchy scan inside the approved package.
        self.repository_root = repository_root  # Resolve readable messages and tracked paths.

    @staticmethod
    def _visible_children(directory: Path) -> list[Path]:
        """Return direct structural children and exclude generated package metadata."""
        excluded_names = {"__init__.py", "__pycache__", ".mypy_cache", ".pytest_cache"}  # Ignore metadata only.
        return [child for child in directory.iterdir() if child.name not in excluded_names]  # Measure structure.

    def _package_directories(self) -> list[Path]:
        """Return each readable package directory in the bounded persistence tree."""
        if not self.persistence_root.is_dir():  # Reject a missing or unreadable required package root.
            raise AssertionError(f"Cannot inspect persistence root: {self.persistence_root}")  # Report the cause.
        package_directories = {self.persistence_root}  # Include the required package root in every result.
        package_directories.update(path.parent for path in self.persistence_root.rglob("__init__.py"))  # Find packages.
        return sorted(package_directories)  # Keep failure output stable across platforms.

    def inspect(self) -> dict[str, int]:
        """Return measured counts and fail when a package has more than five children."""
        package_directories = self._package_directories()  # Fail before a partial hierarchy result.
        counts = {  # Preserve every checked count for the repository contract test.
            directory.relative_to(self.repository_root).as_posix(): len(self._visible_children(directory))
            for directory in package_directories
        }
        violations = {path: count for path, count in counts.items() if count > 5}  # Collect each measured violation.
        message = f"Checked {len(counts)} persistence package directories. Violations: {violations}"  # Report scope.
        assert not violations, message  # Reject a sixth structural child with the measured evidence.
        return counts  # Let the normal test verify the exact repaired hierarchy.

    def active_path_violations(self) -> list[str]:
        """Return tracked active files that still name a removed writer path."""
        result = subprocess.run(  # Ask Git for the authoritative tracked file set.
            ["git", "ls-files", "-z"],
            cwd=self.repository_root,
            check=True,
            capture_output=True,
        )
        tracked_paths = [Path(value.decode("utf-8")) for value in result.stdout.split(b"\0") if value]  # Decode paths.
        active_roots = {"src", "tests", "scripts", "documentation"}  # Exclude immutable historical specifications.
        text_suffixes = {".md", ".py", ".toml", ".txt", ".yaml", ".yml"}  # Read maintained text formats only.
        active_paths = [  # Keep maintained code, tests, scripts, documentation, and the root README.
            path
            for path in tracked_paths
            if path.suffix.lower() in text_suffixes
            and (path.name == "README.md" or (path.parts and path.parts[0] in active_roots))
        ]
        return [  # Report every active tracked file that still contains a removed path.
            path.as_posix()
            for path in active_paths
            if OLD_WRITER_PATH.search((self.repository_root / path).read_text(encoding="utf-8"))
        ]


class TestPersistencePackageStructure:
    """Prove the bounded structure and each required failure result."""

    def test_repository_structure_and_paths(self) -> None:
        """Require exact package counts and canonical active writer paths."""
        inspector = PersistenceStructureInspector(PERSISTENCE_ROOT, REPOSITORY_ROOT)  # Inspect the live package.
        counts = inspector.inspect()  # Require the repaired package hierarchy.
        assert counts == {  # Fix the approved scope and report each checked directory through assertion output.
            "src/foundation/persistence": 2,
            "src/foundation/persistence/cache": 1,
            "src/foundation/persistence/db": 5,
            "src/foundation/persistence/db/writers": 2,
        }
        assert inspector.active_path_violations() == []  # Reject each removed active writer path.

    def test_sixth_child_fails_with_measured_count(self, tmp_path: Path) -> None:
        """Prove that one checked package with six children fails."""
        persistence_root = tmp_path / "persistence"  # Build one isolated package level for the failure proof.
        persistence_root.mkdir()  # Create the required package root.
        (persistence_root / "__init__.py").write_text('"""Test package."""\n', encoding="utf-8")  # Mark the package.
        for child_number in range(6):  # Create exactly one child above the approved maximum.
            (persistence_root / f"child_{child_number}.py").write_text("", encoding="utf-8")  # Add a structural child.
        inspector = PersistenceStructureInspector(persistence_root, tmp_path)  # Inspect only the temporary package.
        with pytest.raises(AssertionError, match=r"Checked 1 .*'persistence': 6"):  # Require count and path evidence.
            inspector.inspect()  # Trigger the controlled hierarchy failure.

    def test_missing_root_fails_with_path(self, tmp_path: Path) -> None:
        """Prove that an absent required root fails with its path."""
        missing_root = tmp_path / "missing-persistence"  # Name a package root that does not exist.
        inspector = PersistenceStructureInspector(missing_root, tmp_path)  # Configure the unreadable root.
        with pytest.raises(AssertionError, match=re.escape(str(missing_root))):  # Require the missing path in output.
            inspector.inspect()  # Trigger the required input failure.

    def test_active_old_path_is_reported(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Prove that one tracked active old path fails the canonical path check."""
        source_path = Path("src") / "sample.py"  # Use an active source root in the controlled repository.
        absolute_path = tmp_path / source_path  # Resolve the controlled tracked file.
        absolute_path.parent.mkdir()  # Create the active source directory.
        absolute_path.write_text(  # Add one removed import path for the failure proof.
            "from src.foundation.persistence.db." + "arango_writer import ArangoDBWriter\n",
            encoding="utf-8",
        )
        completed = subprocess.CompletedProcess(
            [], 0, stdout=f"{source_path.as_posix()}\0".encode()
        )  # Mock Git output.
        monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: completed)  # Keep the proof repository-local.
        inspector = PersistenceStructureInspector(tmp_path, tmp_path)  # Inspect the controlled active path set.
        assert inspector.active_path_violations() == ["src/sample.py"]  # Require the violating path in the result.
