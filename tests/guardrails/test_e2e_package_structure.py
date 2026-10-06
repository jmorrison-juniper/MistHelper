"""Guard the E2E package layout and its collection boundary."""

from collections import Counter
from pathlib import Path

E2E_ROOT = Path(__file__).parents[1] / "e2e"
WEB_PORTAL_ROOT = E2E_ROOT / "web_portal"
EXPECTED_PACKAGES = {"upgrade_portal", "web_portal", "websockets_tab"}


def _shared_portal_test_names() -> list[str]:
    """Return each shared portal test from its package or its legacy root."""
    locations = (E2E_ROOT, WEB_PORTAL_ROOT)
    return sorted(path.name for location in locations for path in location.glob("test_*.py"))


def test_e2e_root_contains_only_coherent_packages() -> None:
    """Keep E2E tests below the five-item directory limit."""
    entries = {entry.name for entry in E2E_ROOT.iterdir() if entry.name != "__pycache__"}
    assert entries == {"__init__.py", "conftest.py", *EXPECTED_PACKAGES}
    assert len(entries) <= 5


def test_web_portal_package_contains_all_shared_portal_tests() -> None:
    """Keep shared portal tests in one package for focused collection."""
    expected_names = _shared_portal_test_names()
    actual_names = sorted(path.name for path in WEB_PORTAL_ROOT.glob("test_*.py"))
    assert expected_names, "The shared portal test inventory is empty, so the guard measured nothing."
    missing = sorted((Counter(expected_names) - Counter(actual_names)).elements())
    extra = sorted((Counter(actual_names) - Counter(expected_names)).elements())
    assert (
        not missing and not extra
    ), f"The web_portal package differs from the shared portal test inventory: missing={missing} extra={extra}"
