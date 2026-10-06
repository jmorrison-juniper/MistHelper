"""Guard the bounded network routing support package structure."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
NETWORK_ROOT = REPOSITORY_ROOT / "src" / "mist" / "networking" / "network"
SUPPORT_MODULES = {
    "_routing_utils_display.py",
    "_routing_utils_parsing.py",
    "_routing_utils_payload.py",
}
OLD_MODULES = {
    "_routing_utils_display.py",
    "_routing_utils_parsing.py",
    "_routing_utils_payload.py",
}


def visible_children(directory: Path) -> list[Path]:
    """Return structural children and exclude package metadata."""
    return [child for child in directory.iterdir() if child.name not in {"__init__.py", "__pycache__"}]


class NetworkRoutingStructureInspector:
    """Inspect the network and routing support package levels."""

    def __init__(self, network_root: Path) -> None:
        """Store the package root for inspection."""
        self.network_root = network_root

    def inspect(self) -> dict[str, int]:
        """Return measured child counts and reject over-limit package levels."""
        support_root = self.network_root / "support"
        directories = {
            self.network_root: len(visible_children(self.network_root)),
            support_root: len(visible_children(support_root)),
        }
        violations = {str(path): count for path, count in directories.items() if count > 5}
        message = f"Checked {len(directories)} package levels. Violations: {violations}"
        assert not violations, message
        return {path.relative_to(REPOSITORY_ROOT).as_posix(): count for path, count in directories.items()}

    def validate_layout(self) -> list[str]:
        """Return missing or misplaced routing support modules."""
        support_root = self.network_root / "support"
        missing = [
            str(support_root / module) for module in sorted(SUPPORT_MODULES) if not (support_root / module).is_file()
        ]
        misplaced = [
            str(self.network_root / module) for module in sorted(OLD_MODULES) if (self.network_root / module).exists()
        ]
        return missing + misplaced


def test_network_routing_support_has_five_and_three_children() -> None:
    """Require the network package and support package to meet the exact layout."""
    inspector = NetworkRoutingStructureInspector(NETWORK_ROOT)
    assert inspector.inspect() == {
        "src/mist/networking/network": 5,
        "src/mist/networking/network/support": 3,
    }
    assert inspector.validate_layout() == []


def test_sixth_network_child_fails_with_measured_count(tmp_path: Path) -> None:
    """Prove that a sixth network child fails the structure guard."""
    network_root = tmp_path / "network"
    network_root.mkdir()
    (network_root / "__init__.py").write_text('"""Test package."""\n', encoding="utf-8")
    for child_number in range(5):
        (network_root / f"child_{child_number}.py").write_text("", encoding="utf-8")
    support_root = network_root / "support"
    support_root.mkdir()
    (support_root / "__init__.py").write_text('"""Test package."""\n', encoding="utf-8")
    inspector = NetworkRoutingStructureInspector(network_root)
    with pytest.raises(AssertionError, match=r"Checked 2 .*network': 6"):
        inspector.inspect()


def test_missing_support_module_is_reported(tmp_path: Path) -> None:
    """Prove that an incomplete support package reports its missing module."""
    network_root = tmp_path / "network"
    support_root = network_root / "support"
    support_root.mkdir(parents=True)
    (network_root / "__init__.py").write_text('"""Test package."""\n', encoding="utf-8")
    (support_root / "__init__.py").write_text('"""Test package."""\n', encoding="utf-8")
    inspector = NetworkRoutingStructureInspector(network_root)
    missing = inspector.validate_layout()
    assert len(missing) == 3
    assert all(re.search(r"_routing_utils_(display|parsing|payload)\.py", path) for path in missing)
