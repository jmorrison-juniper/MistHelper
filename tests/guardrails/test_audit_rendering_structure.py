"""Guard the bounded audit rendering package structure."""  # State the structural contract under test.

from __future__ import annotations  # Use current annotation behavior in the guard.

import re  # Detect each removed canonical renderer path in tracked text.
import subprocess  # Read the tracked repository file set from Git.
from pathlib import Path  # Inspect package levels with platform-safe paths.

import pytest  # Prove each required guard failure mode.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Resolve the active worktree from this guard file.
AUDIT_ROOT = REPOSITORY_ROOT / "src" / "mist" / "access" / "audit"  # Limit the hierarchy scope to the audit package.
MAX_CHILDREN = 5  # Enforce the repository five-child hierarchy limit.
EXPECTED_LAYOUT = {  # Record the approved structural child count of each audit package level.
    "src/mist/access/audit": 5,
    "src/mist/access/audit/rendering": 2,
    "src/mist/access/audit/rendering/helpers": 5,
}
OLD_RENDERER_PATH = re.compile(  # Match each removed dotted module path and each removed file path.
    r"src\.mist\.access\.audit\.(?:renderer|_renderer_(?:delta|format|html|mermaid|time))\b"
    r"|src/mist/access/audit/(?:renderer|_renderer_(?:delta|format|html|mermaid|time))\.py"
)
SNAPSHOT_MAP_OWNER = "tests/guardrails/test_performance_hook_catalog.py"  # Own the approved snapshot path map.


class AuditRenderingStructureInspector:
    """Inspect the approved audit package levels and the active canonical renderer paths."""

    def __init__(self, audit_root: Path, repository_root: Path) -> None:
        """Store the bounded package root and the repository root."""
        self.audit_root = audit_root  # Keep the hierarchy scan inside the approved package.
        self.repository_root = repository_root  # Resolve readable messages and tracked paths.

    @staticmethod
    def _visible_children(directory: Path) -> list[Path]:
        """Return direct structural children and exclude generated package metadata."""
        excluded_names = {"__init__.py", "__pycache__", ".mypy_cache", ".pytest_cache"}  # Ignore metadata only.
        return [child for child in directory.iterdir() if child.name not in excluded_names]  # Measure structure.

    def _package_directories(self) -> list[Path]:
        """Return each readable package directory in the bounded audit tree."""
        if not self.audit_root.is_dir():  # Reject a missing or unreadable required package root.
            raise AssertionError(f"Cannot inspect audit root: {self.audit_root}")  # Report the cause.
        package_directories = {self.audit_root}  # Include the required package root in every result.
        package_directories.update(path.parent for path in self.audit_root.rglob("__init__.py"))  # Find packages.
        return sorted(package_directories)  # Keep failure output stable across platforms.

    def inspect(self) -> dict[str, int]:
        """Return measured counts and fail when a package holds more than five children."""
        package_directories = self._package_directories()  # Fail before a partial hierarchy result.
        counts = {  # Preserve every checked count for the repository contract test.
            directory.relative_to(self.repository_root).as_posix(): len(self._visible_children(directory))
            for directory in package_directories
        }
        violations = {path: count for path, count in counts.items() if count > MAX_CHILDREN}  # Collect violations.
        message = f"Checked {len(counts)} audit package directories. Violations: {violations}"  # Report the scope.
        assert not violations, message  # Reject a sixth structural child with the measured evidence.
        return counts  # Let the normal test verify the exact repaired hierarchy.

    def active_path_violations(self) -> list[str]:
        """Return tracked active files that still name a removed renderer path."""
        result = subprocess.run(  # Ask Git for the authoritative tracked file set.
            ["git", "ls-files", "-z"],
            cwd=self.repository_root,
            check=True,
            capture_output=True,
        )
        tracked_paths = [Path(value.decode("utf-8")) for value in result.stdout.split(b"\0") if value]  # Decode paths.
        active_roots = {"src", "tests", "scripts", "junk", "documentation"}  # Exclude historical specifications.
        text_suffixes = {".md", ".py", ".toml", ".txt", ".yaml", ".yml"}  # Read maintained text formats only.
        active_paths = [  # Keep maintained code, tests, scripts, utilities, and documentation.
            path
            for path in tracked_paths
            if path.suffix.lower() in text_suffixes
            and path.parts
            and path.parts[0] in active_roots
            and path.as_posix() != SNAPSHOT_MAP_OWNER
        ]
        return [  # Report every active tracked file that still holds a removed path.
            path.as_posix()
            for path in active_paths
            if OLD_RENDERER_PATH.search((self.repository_root / path).read_text(encoding="utf-8"))
        ]


class TestAuditRenderingStructure:
    """Prove the bounded structure and each required failure result."""

    def test_repository_structure_and_paths(self) -> None:
        """Require the exact package counts and canonical active renderer paths."""
        inspector = AuditRenderingStructureInspector(AUDIT_ROOT, REPOSITORY_ROOT)  # Inspect the live package.
        counts = inspector.inspect()  # Require the repaired package hierarchy.
        assert counts == EXPECTED_LAYOUT, f"Checked {len(counts)} audit directories: {counts}"  # Report the scope.
        assert inspector.active_path_violations() == []  # Reject each removed active renderer path.

    def test_sixth_child_fails_with_measured_count(self, tmp_path: Path) -> None:
        """Prove that one checked package with six children fails."""
        audit_root = tmp_path / "audit"  # Build one isolated package level for the failure proof.
        audit_root.mkdir()  # Create the required package root.
        (audit_root / "__init__.py").write_text('"""Test package."""\n', encoding="utf-8")  # Mark the package.
        for child_number in range(6):  # Create exactly one child above the approved maximum.
            (audit_root / f"child_{child_number}.py").write_text("", encoding="utf-8")  # Add a structural child.
        inspector = AuditRenderingStructureInspector(audit_root, tmp_path)  # Inspect only the temporary package.
        with pytest.raises(AssertionError, match=r"Checked 1 .*'audit': 6"):  # Require count and path evidence.
            inspector.inspect()  # Trigger the controlled hierarchy failure.

    def test_missing_root_fails_with_path(self, tmp_path: Path) -> None:
        """Prove that an absent required root fails with its path."""
        missing_root = tmp_path / "missing-audit"  # Name a package root that does not exist.
        inspector = AuditRenderingStructureInspector(missing_root, tmp_path)  # Configure the unreadable root.
        with pytest.raises(AssertionError, match=re.escape(str(missing_root))):  # Require the missing path.
            inspector.inspect()  # Trigger the required input failure.

    def test_active_old_path_is_reported(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Prove that one tracked active old path fails the canonical path check."""
        source_path = Path("src") / "sample.py"  # Use an active source root in the controlled repository.
        absolute_path = tmp_path / source_path  # Resolve the controlled tracked file.
        absolute_path.parent.mkdir()  # Create the active source directory.
        absolute_path.write_text(  # Add one removed import path for the failure proof.
            "from src.mist.access.audit." + "renderer import AuditReportRenderer\n",
            encoding="utf-8",
        )
        completed = subprocess.CompletedProcess(
            [], 0, stdout=f"{source_path.as_posix()}\0".encode()
        )  # Mock Git output.
        monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: completed)  # Keep the proof local.
        inspector = AuditRenderingStructureInspector(tmp_path, tmp_path)  # Inspect the controlled path set.
        assert inspector.active_path_violations() == ["src/sample.py"]  # Require the violating path in the result.

    def test_snapshot_map_owner_still_holds_each_old_path(self) -> None:
        """Prove that the one exempt guard still maps every removed renderer path."""
        owner_path = REPOSITORY_ROOT / SNAPSHOT_MAP_OWNER  # Resolve the single exempt guard module.
        assert owner_path.is_file(), f"The exempt snapshot map owner is absent: {owner_path}"  # Require the file.
        owner_text = owner_path.read_text(encoding="utf-8")  # Read the guard that owns the approved map.
        found = OLD_RENDERER_PATH.findall(owner_text)  # Count the removed paths that the map still names.
        assert len(found) == 6, f"Checked {SNAPSHOT_MAP_OWNER} and found {len(found)} removed renderer paths"
