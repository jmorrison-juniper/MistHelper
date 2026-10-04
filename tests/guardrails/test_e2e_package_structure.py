"""Guard the E2E package layout and its collection boundary."""

from pathlib import Path

E2E_ROOT = Path(__file__).parents[1] / "e2e"
EXPECTED_PACKAGES = {"upgrade_portal", "web_portal", "websockets_tab"}


def test_e2e_root_contains_only_coherent_packages() -> None:
    """Keep E2E tests below the five-item directory limit."""
    entries = {entry.name for entry in E2E_ROOT.iterdir() if entry.name != "__pycache__"}
    assert entries == {"__init__.py", "conftest.py", *EXPECTED_PACKAGES}
    assert len(entries) <= 5


def test_web_portal_package_contains_all_shared_portal_tests() -> None:
    """Keep shared portal tests in one package for focused collection."""
    test_files = sorted((E2E_ROOT / "web_portal").glob("test_*.py"))
    assert len(test_files) == 15
    assert all(test_file.parent.name == "web_portal" for test_file in test_files)
