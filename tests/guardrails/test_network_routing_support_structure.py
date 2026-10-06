"""Guard the bounded network routing support package structure."""

from __future__ import annotations  # Use current annotation behavior in the guard.

import re  # Detect removed dotted and filesystem module paths.
import subprocess  # Read the tracked repository file set from Git.
from pathlib import Path  # Inspect package levels with platform-safe paths.

import pytest  # Prove each required guard failure mode.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Resolve the current repository checkout.
NETWORK_ROOT = REPOSITORY_ROOT / "src" / "mist" / "networking" / "network"  # Bound the structure check.
EXPECTED_NETWORK_CHILDREN = {  # Define the approved direct routing package structure.
    "_routing_utils_forwarding.py",
    "_routing_utils_routing.py",
    "_routing_utils_ssr.py",
    "routing_utils.py",
    "support",
}
EXPECTED_SUPPORT_CHILDREN = {  # Define the three modules owned by the support package.
    "_routing_utils_display.py",
    "_routing_utils_parsing.py",
    "_routing_utils_payload.py",
}
REMOVED_MODULE_NAMES = (  # Keep the removed names in one reusable contract.
    "_routing_utils_display",
    "_routing_utils_parsing",
    "_routing_utils_payload",
)


class RoutingSupportStructureInspector:
    """Inspect the routing package shape and active canonical paths."""

    def __init__(self, network_root: Path, repository_root: Path) -> None:
        """Store the bounded package root and repository root."""
        self.network_root = network_root  # Keep the hierarchy scan inside the approved package.
        self.repository_root = repository_root  # Resolve tracked paths and readable messages.

    @staticmethod
    def _visible_children(directory: Path) -> set[str]:
        """Return direct structural child names and exclude package metadata."""
        excluded_names = {"__init__.py", "__pycache__", ".mypy_cache", ".pytest_cache"}  # Ignore metadata only.
        return {child.name for child in directory.iterdir() if child.name not in excluded_names}  # Measure shape.

    def inspect(self) -> tuple[set[str], set[str]]:
        """Return both package shapes and fail when a required root is absent."""
        if not self.network_root.is_dir():  # Reject a missing required network package.
            raise AssertionError(f"Cannot inspect network root: {self.network_root}")  # Report the missing path.
        support_root = self.network_root / "support"  # Resolve the required nested package.
        if not support_root.is_dir():  # Reject an incomplete move before child inspection.
            raise AssertionError(f"Cannot inspect routing support root: {support_root}")  # Report the missing path.
        return self._visible_children(self.network_root), self._visible_children(support_root)  # Supply both shapes.

    def active_old_path_violations(self) -> list[str]:
        """Return active tracked files that still name a removed support module path."""
        result = subprocess.run(  # Ask Git for the authoritative tracked file set.
            ["git", "ls-files", "-z"],
            cwd=self.repository_root,
            check=True,
            capture_output=True,
        )
        tracked_paths = [Path(value.decode("utf-8")) for value in result.stdout.split(b"\0") if value]  # Decode paths.
        active_roots = {"src", "tests", "scripts", "documentation"}  # Exclude historical specifications.
        suffixes = {".md", ".py", ".toml", ".txt", ".yaml", ".yml"}  # Read maintained text formats only.
        active_paths = [  # Select maintained code, tests, scripts, documentation, and the root README.
            path
            for path in tracked_paths
            if path.suffix.lower() in suffixes
            and (path.name == "README.md" or (path.parts and path.parts[0] in active_roots))
        ]
        separators = r"[./\\]"  # Match import and filesystem path separators.
        module_group = "|".join(REMOVED_MODULE_NAMES)  # Build the removed module alternatives.
        old_path = re.compile(  # Match an old path without embedding one removable path in this guard.
            rf"src{separators}mist{separators}networking{separators}network{separators}(?:{module_group})"
        )
        return [  # Report each active file that still uses a removed path.
            path.as_posix()
            for path in active_paths
            if old_path.search((self.repository_root / path).read_text(encoding="utf-8"))
        ]


class TestNetworkRoutingSupportStructure:
    """Prove the exact routing structure and each required failure result."""

    def test_repository_structure_and_paths(self) -> None:
        """Require five network children, three support children, and canonical active paths."""
        inspector = RoutingSupportStructureInspector(NETWORK_ROOT, REPOSITORY_ROOT)  # Inspect the live packages.
        network_children, support_children = inspector.inspect()  # Read both measured package shapes.
        assert (
            network_children == EXPECTED_NETWORK_CHILDREN
        ), (  # Require the exact five-child network package.
            f"Checked {len(network_children)} network children: {sorted(network_children)}"
        )
        assert (
            support_children == EXPECTED_SUPPORT_CHILDREN
        ), (  # Require the exact three-child support package.
            f"Checked {len(support_children)} support children: {sorted(support_children)}"
        )
        assert inspector.active_old_path_violations() == []  # Reject each removed active module path.

    def test_sixth_network_child_fails_with_measured_count(self, tmp_path: Path) -> None:
        """Prove that a sixth network child fails the exact structure contract."""
        network_root = tmp_path / "network"  # Build an isolated network package.
        support_root = network_root / "support"  # Build its required support package.
        support_root.mkdir(parents=True)  # Create both controlled package levels.
        for child_name in (EXPECTED_NETWORK_CHILDREN - {"support"}) | {  # Add one child above the approved count.
            "extra.py"
        }:
            child_path = network_root / child_name  # Resolve the controlled structural child.
            child_path.write_text("", encoding="utf-8")  # Add one controlled module child.
        inspector = RoutingSupportStructureInspector(network_root, tmp_path)  # Inspect the invalid shape.
        network_children, _ = inspector.inspect()  # Read the measured invalid child set.
        with pytest.raises(AssertionError, match=r"Checked 6 network children"):  # Require measured evidence.
            assert (
                network_children == EXPECTED_NETWORK_CHILDREN
            ), (  # Apply the production shape assertion.
                f"Checked {len(network_children)} network children: {sorted(network_children)}"
            )

    def test_missing_support_root_fails_with_path(self, tmp_path: Path) -> None:
        """Prove that an absent support package fails with its path."""
        network_root = tmp_path / "network"  # Build the required parent package only.
        network_root.mkdir()  # Leave the required support package absent.
        inspector = RoutingSupportStructureInspector(network_root, tmp_path)  # Inspect the incomplete move.
        with pytest.raises(AssertionError, match=re.escape(str(network_root / "support"))):  # Require its path.
            inspector.inspect()  # Trigger the required input failure.
