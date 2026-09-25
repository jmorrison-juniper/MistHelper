"""Guard every Mist SDK call in the web portal against SDK drift.

Issue #3233: `_fetch_wired_clients()` called
`mistapi.api.v1.sites.clients.searchSiteWiredClients`. In mistapi 0.64.0 that
function lives in `mistapi.api.v1.sites.wired_clients`. The call raised
AttributeError, so every client pick list lost its wired half.

A unit test that mocks the SDK cannot catch this defect, because a mock
accepts any attribute. This guard reads the portal source with `ast`, finds
each call whose function is a `mistapi.api...` attribute chain, and requires
that the chain resolves in the installed SDK.
"""

import ast
import importlib
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PORTAL_ROOT = REPOSITORY_ROOT / "web_portal"


def _dotted(node: ast.AST) -> str:
    """Return the dotted name of an attribute chain, or an empty string."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return ""


def _sdk_calls() -> list[tuple[str, int, str]]:
    """Return the file, line, and dotted name of each `mistapi.api` call in the portal."""
    calls: list[tuple[str, int, str]] = []
    for module in sorted(PORTAL_ROOT.rglob("*.py")):
        tree = ast.parse(module.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = _dotted(node.func)
                if name.startswith("mistapi.api."):
                    calls.append((module.relative_to(REPOSITORY_ROOT).as_posix(), node.lineno, name))
    return calls


def _resolves(dotted: str) -> bool:
    """Report whether a dotted SDK function name exists in the installed mistapi."""
    module_path, _, function = dotted.rpartition(".")
    try:
        module = importlib.import_module(module_path)
    except ImportError:
        return False
    return callable(getattr(module, function, None))


SDK_CALLS = _sdk_calls()

# A call that already fails on main, with the issue that tracks its repair. The
# guard skips each entry below, and the companion test fails when an entry is
# repaired, so no exemption outlives its defect. This list must only shrink.
# The last entry, for #3236, left when the Maps image route stopped its call to
# the missing getOrgMapImage function.
KNOWN_DRIFT: dict[tuple[str, str], str] = {}


def test_the_guard_found_the_portal_sdk_calls():
    """The guard below means something only while it finds real calls."""
    # Measured on 2026-09-23: the portal routes make several direct SDK calls,
    # including the wireless and wired client searches.
    names = {name for _, _, name in SDK_CALLS}
    assert len(SDK_CALLS) >= 3, f"the parse found only {SDK_CALLS}, so it proves too little"
    assert "mistapi.api.v1.sites.wired_clients.searchSiteWiredClients" in names


@pytest.mark.parametrize("location,line,dotted", SDK_CALLS, ids=[f"{f}:{n}" for f, n, _ in SDK_CALLS])
def test_each_portal_sdk_call_exists_in_the_installed_sdk(location, line, dotted):
    """A call to a missing SDK function fails at run time, so it must fail here first."""
    if (location, dotted) in KNOWN_DRIFT:
        pytest.skip(f"{dotted} is a known drift that {KNOWN_DRIFT[(location, dotted)]} tracks")
    assert _resolves(dotted), f"{location}:{line} calls {dotted}, which the installed mistapi does not hold"


def test_each_known_drift_is_still_broken():
    """An exemption must end the moment its call is repaired."""
    present = {(location, dotted) for location, _, dotted in SDK_CALLS}
    stale = {key: issue for key, issue in KNOWN_DRIFT.items() if key not in present or _resolves(key[1])}
    assert stale == {}, f"these drifts are repaired or gone, so delete them from KNOWN_DRIFT: {stale}"
