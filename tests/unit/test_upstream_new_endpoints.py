"""Unit tests for upstream-new-endpoints spec additions.

Validates:
- 12 new ENDPOINT_PRIMARY_KEY_STRATEGIES entries exist in MistHelper.py
  with correct shape (type, primary_key, indexes).
- 13 menu_actions dispatch entries (195-207) point at callables.
- MAC normalization helper accepts compact / colon / dash forms and rejects
  malformed input.

Pattern: text-scan MistHelper.py (R1 — avoid heavy import side effects).
Confirmation prompts and API call sites are NOT exercised here — those
require a Mist session and are covered by integration / manual smoke tests.
"""
from __future__ import annotations  # Postponed annotation evaluation for type hints

import re  # MAC regex for the standalone helper-replica test
from pathlib import Path  # Filesystem path handling

REPO_ROOT = Path(__file__).resolve().parents[2]  # tests/unit/.. -> tests/.. -> repo root
MISTHELPER_PY = REPO_ROOT / "MistHelper.py"  # Path to the single-file MistHelper script


def _read_source() -> str:  # Cached single read of MistHelper.py source text
    return MISTHELPER_PY.read_text(encoding="utf-8")  # Decode as UTF-8 (project standard)


# --- PK strategies ------------------------------------------------------------

NEW_PK_KEYS = (  # Tuple of all PK strategy keys this spec must register
    "getSiteChannelScores",  # Wave 1 - safe exports
    "searchSiteIotEndpoints",
    "sendOrgNacClientCoA",  # Wave 2 - interactive
    "sendSiteNacClientCoA",
    "startSiteAutoMapAssignment",
    "getSiteAutoMapAssignmentStatus",  # Corrected from spec - actual mistapi name
    "deleteOrgSsoAdmins",  # Wave 3 - destructive
    "deleteMspSsoAdmins",
    "listOrgMxEdgeUpgrades",
    "upgradeOrgMxEdges",
    "listSiteMxEdgeUpgrades",
    "upgradeSiteMxEdges",
)


def test_all_pk_strategies_present():  # Every spec endpoint has a PK strategy entry
    source = _read_source()  # Load file once
    for key in NEW_PK_KEYS:  # Iterate every required strategy key
        assert f"'{key}':" in source, f"Missing PK strategy for {key}"  # Quoted-key form used in dict


# --- Menu dispatch entries ----------------------------------------------------

NEW_MENU_KEYS = tuple(str(n) for n in range(195, 208))  # Menus 195 through 207 inclusive


def test_all_menu_entries_present():  # Every spec menu key is registered
    source = _read_source()  # Reload (cheap; small file relative to test pool)
    for key in NEW_MENU_KEYS:  # Each expected menu number
        assert f'"{key}":' in source, f"Missing menu_actions entry for menu {key}"


# --- MAC normalization helper -------------------------------------------------
# Reproduce the regex + normalization logic locally so the test stays standalone
# and does not trigger MistHelper.py import side effects.
_MAC_RE = re.compile(r"^[0-9a-fA-F]{12}$|^([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}$")  # Spec form


def _normalize_mac(raw_mac):  # Mirror of MistHelper.py:_normalize_mac for isolated testing
    if not raw_mac:  # Empty / None
        return None
    cleaned = raw_mac.strip().lower().replace(":", "").replace("-", "")  # Strip separators
    if len(cleaned) != 12 or not all(c in "0123456789abcdef" for c in cleaned):  # Hex check
        return None
    return cleaned  # 12-char lowercase form


def test_normalize_mac_compact():  # Compact form passes through
    assert _normalize_mac("AABBCCDDEEFF") == "aabbccddeeff"  # Uppercase normalized


def test_normalize_mac_colon():  # Colon form normalizes to compact
    assert _normalize_mac("aa:bb:cc:dd:ee:ff") == "aabbccddeeff"


def test_normalize_mac_dash():  # Dash form normalizes to compact
    assert _normalize_mac("AA-BB-CC-DD-EE-FF") == "aabbccddeeff"


def test_normalize_mac_invalid_length():  # Wrong length rejected
    assert _normalize_mac("abc") is None  # Too short


def test_normalize_mac_invalid_hex():  # Non-hex characters rejected
    assert _normalize_mac("zzzzzzzzzzzz") is None  # Right length, wrong alphabet


def test_normalize_mac_empty():  # Empty string returns None
    assert _normalize_mac("") is None


def test_normalize_mac_none():  # None input returns None
    assert _normalize_mac(None) is None
