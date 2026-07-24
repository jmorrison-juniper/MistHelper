"""Unit tests for ``src/org/org_synthetic_probes_manager.py`` (menu 206).

Why:
    The synthetic-probe manager mutates a shared org setting on every run,
    so every acceptance scenario in ``spec.md`` gets its own pinned test.
    Tests exercise the pure helpers directly and the public entry via
    ``patch.object`` on the module-level ``_mist_setting`` re-export.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.org import org_synthetic_probes_manager as ospm

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture()
def probes_source() -> dict:
    """Return a curated probe-source dict with roles + wildcards.

    Why:
        Mirrors the shape of the real
        ``data/zscaler_client_connector_probes.json`` so the tests exercise
        the same code paths as production (including tunnel_zen expansion).

    Returns:
        Parsed probe-source dict fixture.
    """
    return {
        "schema_version": 1,
        "source": "fixture",
        "wildcards": ["*.prod.zpath.net", "*.private.zscaler.com"],
        "roles": [
            {
                "role": "pac",
                "ports": [80, 443],
                "fqdns": ["pac.zscaler.net"],
            },
            {
                "role": "service_discovery",
                "ports": [443],
                "fqdns": ["mobile.zscaler.net", "login.zscaler.net"],
            },
            {
                "role": "tunnel_zen",
                "ports": [80, 443, 8080],
                "fqdns_ref": "data/zscaler_cenr_hostnames.json",
            },
            {
                "role": "wildcards_only",
                "ports": [443],
                "fqdns": ["*.zscaler.net"],  # Should be skipped.
            },
        ],
    }


@pytest.fixture()
def cenr_source() -> dict:
    """Return a curated CENR hostnames dict.

    Why:
        The tunnel_zen role expands via the CENR file; a small fixture keeps
        assertions readable while still exercising both proxy+vpn arms.

    Returns:
        Parsed CENR dict fixture.
    """
    return {
        "schema_version": 1,
        "proxy_hostnames": [
            "atl1.sme.zscaler.net",
            "mad3.sme.zscaler.net",
        ],
        "vpn_hostnames": [
            "atl1-vpn.zscaler.net",
        ],
    }


@pytest.fixture()
def data_dir(tmp_path: Path, probes_source: dict, cenr_source: dict) -> Path:
    """Write the two curated JSON fixtures into a temp dir.

    Why:
        ``_load_probe_sources`` reads from disk; a tmp fixture lets us stress
        both success and failure paths without polluting the real repo.

    Args:
        tmp_path: pytest-supplied temp directory.
        probes_source: probe fixture dict.
        cenr_source: CENR fixture dict.

    Returns:
        The temp directory path containing both files.
    """
    (tmp_path / ospm._PROBE_SOURCE_FILE).write_text(json.dumps(probes_source), encoding="utf-8")
    (tmp_path / ospm._CENR_SOURCE_FILE).write_text(json.dumps(cenr_source), encoding="utf-8")
    return tmp_path


# --------------------------------------------------------------------------- #
# Story 1 — build from empty
# --------------------------------------------------------------------------- #


def test_build_from_empty_produces_https_prefixed_no_port_targets(probes_source: dict, cenr_source: dict) -> None:
    """Every probe target uses https:// prefix and no port suffix.

    Why:
        FR-007 requires ``https://<fqdn>`` targets with no port number,
        even when the source file lists ports. This is SC-001.
    """
    result = ospm._build_probe_set((probes_source, cenr_source), [10])
    assert result, "Expected at least one probe"
    for name, probe in result.items():
        assert probe["target"].startswith("https://"), name
        assert ":" not in probe["target"].removeprefix("https://"), name
        assert name.startswith(ospm._TOOL_NAME_PREFIX), name


def test_build_from_empty_skips_wildcards(probes_source: dict, cenr_source: dict) -> None:
    """Entries starting with ``*.`` are filtered out (FR-008)."""
    result = ospm._build_probe_set((probes_source, cenr_source), [10])
    for probe in result.values():
        assert "*." not in probe["target"], probe


def test_build_from_empty_includes_tunnel_zen_cenr_hostnames(probes_source: dict, cenr_source: dict) -> None:
    """The tunnel_zen role expands via CENR (FR-006).

    Why:
        FR-006 mandates that the tunnel_zen role pulls its FQDN list from
        the CENR file. Both proxy and vpn hostnames must be present.
    """
    result = ospm._build_probe_set((probes_source, cenr_source), [10])
    tunnel_names = {n for n in result if "tunnel_zen" in n}
    assert any("atl1-sme" in n for n in tunnel_names)
    assert any("mad3-sme" in n for n in tunnel_names)
    assert any("atl1-vpn" in n for n in tunnel_names)


def test_build_applies_defaults(probes_source: dict, cenr_source: dict) -> None:
    """Type defaults to reachability and aggressiveness to high (FR-009)."""
    result = ospm._build_probe_set((probes_source, cenr_source), [10])
    for probe in result.values():
        assert probe["type"] == "reachability"
        assert probe["aggressiveness"] == "high"
        assert probe["vlan_ids"] == [10]


# --------------------------------------------------------------------------- #
# Story 2 — merge
# --------------------------------------------------------------------------- #


def test_merge_dedupes_vlan_union() -> None:
    """Merge produces sorted, deduplicated VLAN union per probe (SC-002)."""
    existing_tool = {
        "zcc-pac-pac-zscaler-net": {
            "name": "zcc-pac-pac-zscaler-net",
            "target": "https://pac.zscaler.net",
            "vlan_ids": [10, 20],
            "type": "reachability",
            "aggressiveness": "high",
        }
    }
    merged = ospm._merge_probes(existing_tool, {}, [20, 30])
    assert merged["zcc-pac-pac-zscaler-net"]["vlan_ids"] == [10, 20, 30]


def test_merge_reports_no_changes_when_subset() -> None:
    """Merge is a no-op when new VLANs are already present on every probe.

    Why:
        Story 2 acceptance #3 says the tool should short-circuit and skip
        the PUT when nothing would actually change.
    """
    existing_tool = {
        "zcc-pac-pac-zscaler-net": {
            "name": "zcc-pac-pac-zscaler-net",
            "target": "https://pac.zscaler.net",
            "vlan_ids": [10, 20, 30],
            "type": "reachability",
            "aggressiveness": "high",
        }
    }
    merged = ospm._merge_probes(existing_tool, {}, [10, 20])
    assert merged == existing_tool


# --------------------------------------------------------------------------- #
# Story 3 — swap
# --------------------------------------------------------------------------- #


def test_swap_preserves_foreign_probes() -> None:
    """Foreign probes survive swap unchanged (SC-003 / FR-012)."""
    existing = {
        "zcc-pac-pac-zscaler-net": {"vlan_ids": [10]},
        "custom-user-probe": {"vlan_ids": [99], "target": "https://acme.example"},
    }
    tool_authored, foreign = ospm._partition_tool_authored(existing)
    assert "custom-user-probe" in foreign
    assert "zcc-pac-pac-zscaler-net" in tool_authored


def test_swap_replaces_vlan_ids_completely() -> None:
    """Swap replaces existing tool-authored VLAN lists with new list.

    Why:
        Story 3 acceptance #2: swap must not preserve legacy VLAN ids on
        tool-authored probes.
    """
    new_probes = {
        "zcc-pac-pac-zscaler-net": {
            "name": "zcc-pac-pac-zscaler-net",
            "target": "https://pac.zscaler.net",
            "vlan_ids": [42],
            "type": "reachability",
            "aggressiveness": "high",
        }
    }
    result = ospm._swap_probes(new_probes)
    assert result["zcc-pac-pac-zscaler-net"]["vlan_ids"] == [42]


# --------------------------------------------------------------------------- #
# Prompt validation
# --------------------------------------------------------------------------- #


def test_prompt_rejects_empty_vlan_list() -> None:
    """Empty input re-prompts until a valid list is entered."""
    with patch("builtins.input", side_effect=["", "  ", "10, 20"]):
        assert ospm._prompt_vlan_list() == [10, 20]


def test_prompt_rejects_out_of_range_vlan() -> None:
    """VLAN ids outside [0, 4094] re-prompt."""
    with patch("builtins.input", side_effect=["4095", "-1", "abc", "0, 4094"]):
        assert ospm._prompt_vlan_list() == [0, 4094]


def test_prompt_dedupes_and_sorts() -> None:
    """Duplicate VLAN ids collapse and result is sorted."""
    with patch("builtins.input", side_effect=["30, 10, 30, 20"]):
        assert ospm._prompt_vlan_list() == [10, 20, 30]


# --------------------------------------------------------------------------- #
# Apply / PUT
# --------------------------------------------------------------------------- #


def test_apply_preserves_synthetic_test_sibling_fields() -> None:
    """FR-015: sibling fields under synthetic_test survive round-trip."""
    setting = {
        "synthetic_test": {
            "custom_probes": {"old": {"name": "old"}},
            "other_sibling_field": {"keep": "me"},
        },
        "top_level_sibling": "keep me too",
    }
    new_probes = {"zcc-new": {"name": "zcc-new"}}
    session = MagicMock()
    fake_response = MagicMock(status_code=200)
    with patch.object(ospm._mist_setting, "updateOrgSettings", return_value=fake_response) as put_mock:
        ospm._apply(session, "org-uuid", setting, new_probes)
    put_mock.assert_called_once()
    body = put_mock.call_args.args[2]
    assert body["synthetic_test"]["custom_probes"] == new_probes
    assert body["synthetic_test"]["other_sibling_field"] == {"keep": "me"}
    assert body["top_level_sibling"] == "keep me too"


def test_apply_reports_http_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Non-2xx status codes surface via stdout for the operator."""
    session = MagicMock()
    fake_response = MagicMock(status_code=500)
    with patch.object(ospm._mist_setting, "updateOrgSettings", return_value=fake_response):
        ospm._apply(session, "org-uuid", {}, {"zcc-x": {"name": "zcc-x"}})
    out = capsys.readouterr().out
    assert "HTTP 500" in out


# --------------------------------------------------------------------------- #
# Confirmation & abort
# --------------------------------------------------------------------------- #


def test_confirm_no_aborts_without_put(
    data_dir: Path,
) -> None:
    """When the operator answers 'n', no PUT is issued (Story 3 accept #3)."""
    session = MagicMock()
    get_response = MagicMock(data={"synthetic_test": {"custom_probes": {}}})
    inputs = iter(["10", "n"])  # VLAN prompt, then confirmation.
    with (
        patch.object(ospm, "_DEFAULT_DATA_DIR", data_dir),
        patch.object(ospm._mist_setting, "getOrgSettings", return_value=get_response),
        patch.object(ospm._mist_setting, "updateOrgSettings") as put_mock,
        patch("builtins.input", lambda _prompt: next(inputs)),
    ):
        ospm.manage_org_synthetic_probes(session, "org-uuid")
    put_mock.assert_not_called()


def test_confirm_yes_triggers_put(data_dir: Path) -> None:
    """'y' at the confirmation prompt fires exactly one PUT."""
    session = MagicMock()
    get_response = MagicMock(data={"synthetic_test": {"custom_probes": {}}})
    inputs = iter(["10", "y"])
    put_response = MagicMock(status_code=200)
    with (
        patch.object(ospm, "_DEFAULT_DATA_DIR", data_dir),
        patch.object(ospm._mist_setting, "getOrgSettings", return_value=get_response),
        patch.object(ospm._mist_setting, "updateOrgSettings", return_value=put_response) as put_mock,
        patch("builtins.input", lambda _prompt: next(inputs)),
    ):
        ospm.manage_org_synthetic_probes(session, "org-uuid")
    put_mock.assert_called_once()


# --------------------------------------------------------------------------- #
# Failure paths
# --------------------------------------------------------------------------- #


def test_missing_source_file_raises_with_clear_message(tmp_path: Path) -> None:
    """Missing curated file surfaces a FileNotFoundError with the path."""
    with pytest.raises(FileNotFoundError) as exc:
        ospm._load_probe_sources(tmp_path)
    assert ospm._PROBE_SOURCE_FILE in str(exc.value)


def test_malformed_source_file_raises_value_error(tmp_path: Path) -> None:
    """Malformed JSON in either file raises a ValueError referencing it."""
    (tmp_path / ospm._PROBE_SOURCE_FILE).write_text("{not-json", encoding="utf-8")
    (tmp_path / ospm._CENR_SOURCE_FILE).write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError) as exc:
        ospm._load_probe_sources(tmp_path)
    assert ospm._PROBE_SOURCE_FILE in str(exc.value)


# --------------------------------------------------------------------------- #
# Detection / partition helpers
# --------------------------------------------------------------------------- #


def test_detect_existing_returns_empty_when_missing() -> None:
    """Missing synthetic_test or custom_probes returns an empty dict."""
    assert ospm._detect_existing({}) == {}
    assert ospm._detect_existing({"synthetic_test": None}) == {}
    assert ospm._detect_existing({"synthetic_test": {}}) == {}


def test_partition_splits_by_prefix() -> None:
    """Only names starting with the zcc- prefix are tool-authored."""
    tool, foreign = ospm._partition_tool_authored(
        {
            "zcc-foo": {"vlan_ids": [1]},
            "user-bar": {"vlan_ids": [2]},
        }
    )
    assert tool == {"zcc-foo": {"vlan_ids": [1]}}
    assert foreign == {"user-bar": {"vlan_ids": [2]}}


def test_fqdn_slug_lowercases_and_replaces_dots() -> None:
    """Slugs are lowercased with dots replaced by hyphens."""
    assert ospm._fqdn_slug("PAC.Zscaler.Net") == "pac-zscaler-net"
