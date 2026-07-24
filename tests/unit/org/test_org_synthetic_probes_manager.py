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
    """Body shape mirrors Mist's mini-* probes: type/target/aggressiveness only.

    Why:
        Live Mist config (2026-07-24) shows the correct ``custom_probes``
        body shape is ``{type, target, aggressiveness}`` -- no ``name``
        (the dict key IS the name) and no ``vlan_ids`` (VLAN scoping
        belongs on the ``tests[]`` row). ``type`` defaults to
        ``"application"`` to match the mini-* convention. Mist's 5-probe
        priority cap counts ``critical`` + ``high`` only; ``auto`` does
        not consume a slot, so every non-critical probe carries an
        explicit ``"auto"`` value rather than leaving the key unset.
    """
    result = ospm._build_probe_set((probes_source, cenr_source), [10])
    for probe in result.values():
        assert probe["type"] == "application"
        assert "name" not in probe
        assert "vlan_ids" not in probe
        # Every probe carries the key with one of the two accepted values.
        assert probe["aggressiveness"] in {
            ospm._CRITICAL_AGGRESSIVENESS,
            ospm._AUTO_AGGRESSIVENESS,
        }


# --------------------------------------------------------------------------- #
# Story 2 — merge
# --------------------------------------------------------------------------- #


def test_merge_strips_legacy_name_and_vlan_ids() -> None:
    """Merge strips legacy ``name``/``vlan_ids`` off existing probe bodies.

    Why:
        Prior versions of the tool wrote ``name`` and ``vlan_ids`` INTO
        the probe body. The live Mist config (2026-07-24) shows the
        correct shape is ``{type, target, aggressiveness}`` only, so the
        merge pass acts as a migration: any on-org probe still carrying
        the legacy fields is normalised on the next re-sync.
    """
    existing_tool = {
        "zcc-pac-pac-zscaler-net": {
            "name": "zcc-pac-pac-zscaler-net",
            "target": "https://pac.zscaler.net",
            "vlan_ids": [10, 20],
            "type": "reachability",
            "aggressiveness": "auto",
        }
    }
    new_probes = {
        "zcc-pac-pac-zscaler-net": {
            "type": "application",
            "target": "https://pac.zscaler.net",
            "aggressiveness": "critical",
        }
    }
    merged = ospm._merge_probes(existing_tool, new_probes, [20, 30])
    body = merged["zcc-pac-pac-zscaler-net"]
    assert "name" not in body
    assert "vlan_ids" not in body
    assert body["type"] == "application"
    assert body["target"] == "https://pac.zscaler.net"
    # aggressiveness re-syncs to freshly-built authoritative value.
    assert body["aggressiveness"] == "critical"


def test_merge_preserves_bodies_when_already_clean() -> None:
    """Merge is a body-shape no-op when existing probes are already mini-shaped.

    Why:
        Once the migration has run once, subsequent merges should not
        rewrite bodies unnecessarily -- the only field that may change
        is ``aggressiveness`` (re-synced from ``new_probes``).
    """
    existing_tool = {
        "zcc-pac-pac-zscaler-net": {
            "type": "application",
            "target": "https://pac.zscaler.net",
            "aggressiveness": "auto",
        }
    }
    new_probes = {
        "zcc-pac-pac-zscaler-net": {
            "type": "application",
            "target": "https://pac.zscaler.net",
            "aggressiveness": "auto",
        }
    }
    merged = ospm._merge_probes(existing_tool, new_probes, [10, 20])
    assert merged == existing_tool


# --------------------------------------------------------------------------- #
# Story 3 — swap
# --------------------------------------------------------------------------- #


def test_swap_preserves_foreign_probes() -> None:
    """Foreign probes survive swap unchanged (SC-003 / FR-012)."""
    existing = {
        "zcc-pac-pac-zscaler-net": {"target": "https://pac.zscaler.net"},
        "custom-user-probe": {"target": "https://acme.example"},
    }
    tool_authored, foreign = ospm._partition_tool_authored(existing)
    assert "custom-user-probe" in foreign
    assert "zcc-pac-pac-zscaler-net" in tool_authored


def test_swap_returns_new_probes_unchanged() -> None:
    """Swap replaces tool-authored bodies wholesale with the freshly-built set.

    Why:
        Story 3 acceptance #2: swap must not preserve legacy body fields
        (``name``/``vlan_ids``) on tool-authored probes -- the new set
        is authoritative and must land verbatim.
    """
    new_probes = {
        "zcc-pac-pac-zscaler-net": {
            "type": "application",
            "target": "https://pac.zscaler.net",
            "aggressiveness": "critical",
        }
    }
    result = ospm._swap_probes(new_probes)
    assert result == new_probes
    body = result["zcc-pac-pac-zscaler-net"]
    assert "name" not in body
    assert "vlan_ids" not in body


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
        ospm._apply(session, "org-uuid", setting, new_probes, [10])
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
        ospm._apply(session, "org-uuid", {}, {"zcc-x": {"name": "zcc-x"}}, [10])
    out = capsys.readouterr().out
    assert "HTTP 500" in out


def test_merge_injects_critical_names_into_first_foreign_row() -> None:
    """Critical zcc names merge into the existing foreign row's ``probes[]``.

    Why:
        Verified against a live Mist org config 2026-07-24: Mist emits a
        single ``tests[]`` row that co-schedules every probe under one
        ``probes`` array. The tool must extend that same row rather than
        appending a separate categorized row -- the operator's earlier
        directive was that all probe names belong under one unified
        ``probes`` section, not split by tool prefix. The target row's
        ``vlan_ids``, ``lan_networks``, and other keys survive untouched.
    """
    existing = [
        {
            "probes": ["mini-cloudflare-1", "mini-google-1"],
            "vlan_ids": [10],
            "lan_networks": ["default"],
        }
    ]
    combined = {
        "zcc-crit-a": {"name": "zcc-crit-a", "aggressiveness": "critical"},
        "zcc-plain": {"name": "zcc-plain", "aggressiveness": "auto"},
        "zcc-crit-b": {"name": "zcc-crit-b", "aggressiveness": "critical"},
    }
    merged = ospm._merge_zcc_criticals_into_tests(existing, combined, [10])
    assert len(merged) == 1
    row = merged[0]
    assert row["probes"] == [
        "mini-cloudflare-1",
        "mini-google-1",
        "zcc-crit-a",
        "zcc-crit-b",
    ]
    assert row["vlan_ids"] == [10]
    assert row["lan_networks"] == ["default"]


def test_merge_strips_stale_zcc_names_on_rerun() -> None:
    """Stale ``zcc-*`` names in an existing row are stripped before injection.

    Why:
        Re-runs must be idempotent: if a prior run injected a critical
        probe that is no longer part of the curated set, or the operator
        removed one, the stale name must not linger in ``probes[]``. Only
        the current critical set is re-injected.
    """
    existing = [
        {
            "probes": ["mini-a", "zcc-old-removed", "zcc-still-critical"],
            "vlan_ids": [1],
        }
    ]
    combined = {
        "zcc-still-critical": {
            "name": "zcc-still-critical",
            "aggressiveness": "critical",
        },
    }
    merged = ospm._merge_zcc_criticals_into_tests(existing, combined, [1])
    assert merged[0]["probes"] == ["mini-a", "zcc-still-critical"]


def test_merge_drops_legacy_aggregate_tool_row() -> None:
    """Legacy tool-authored aggregate rows (name=zcc-*) are removed.

    Why:
        Earlier iterations of this module wrote a separate row named
        ``zcc-critical-probes``. The user rejected that shape. Migration
        must delete any such row on the next run so the config
        converges to the merged-into-existing-row model.
    """
    existing = [
        {"probes": ["mini-a"], "vlan_ids": [10]},
        {
            "name": "zcc-critical-probes",
            "probes": ["zcc-x", "zcc-y"],
            "vlan_ids": [10],
        },
    ]
    combined = {"zcc-x": {"name": "zcc-x", "aggressiveness": "critical"}}
    merged = ospm._merge_zcc_criticals_into_tests(existing, combined, [10])
    assert len(merged) == 1
    assert merged[0]["probes"] == ["mini-a", "zcc-x"]
    assert "name" not in merged[0] or merged[0].get("name") != "zcc-critical-probes"


def test_merge_fabricates_bare_row_when_no_foreign_row() -> None:
    """When no foreign row exists, a bare row with the criticals is added."""
    combined = {"zcc-x": {"name": "zcc-x", "aggressiveness": "critical"}}
    merged = ospm._merge_zcc_criticals_into_tests([], combined, [42])
    assert merged == [{"probes": ["zcc-x"], "vlan_ids": [42]}]


def test_merge_no_criticals_leaves_foreign_row_alone() -> None:
    """Non-critical-only probe maps leave existing rows unchanged."""
    existing = [{"probes": ["mini-a"], "vlan_ids": [10]}]
    combined = {"zcc-plain": {"name": "zcc-plain", "aggressiveness": "auto"}}
    merged = ospm._merge_zcc_criticals_into_tests(existing, combined, [10])
    assert merged == [{"probes": ["mini-a"], "vlan_ids": [10]}]


def test_apply_merges_critical_names_into_existing_row() -> None:
    """Org PUT body extends the existing ``tests[]`` row's probes list.

    Why:
        Regression guard for the merge-into-existing-row fix: the
        operator's live config shows one nameless system row; the tool
        must inject its critical zcc names into that row rather than
        appending a separate categorized row.
    """
    session = MagicMock()
    combined = {
        "zcc-crit": {"name": "zcc-crit", "aggressiveness": "critical"},
        "zcc-plain": {"name": "zcc-plain", "aggressiveness": "auto"},
    }
    existing_setting = {
        "synthetic_test": {
            "tests": [{"probes": ["mini-cloudflare-1"], "vlan_ids": [10]}],
        }
    }
    fake_response = MagicMock(status_code=200)
    with patch.object(ospm._mist_setting, "updateOrgSettings", return_value=fake_response) as put_mock:
        ospm._apply(session, "org-uuid", existing_setting, combined, [10, 20])
    body = put_mock.call_args.args[2]
    tests = body["synthetic_test"]["tests"]
    assert tests == [{"probes": ["mini-cloudflare-1", "zcc-crit"], "vlan_ids": [10]}]


def test_apply_to_site_merges_critical_names_into_existing_row() -> None:
    """Site PUT body extends the existing ``tests[]`` row's probes list."""
    session = MagicMock()
    tool_probes = {
        "zcc-crit": {"name": "zcc-crit", "aggressiveness": "critical"},
        "zcc-plain": {"name": "zcc-plain", "aggressiveness": "auto"},
    }
    get_response = MagicMock(
        data={
            "synthetic_test": {
                "tests": [{"probes": ["mini-google-1"], "vlan_ids": [42]}],
            }
        }
    )
    put_response = MagicMock(status_code=200)
    with (
        patch.object(ospm._mist_site_setting, "getSiteSetting", return_value=get_response),
        patch.object(
            ospm._mist_site_setting,
            "updateSiteSettings",
            return_value=put_response,
        ) as put_mock,
    ):
        ospm._apply_to_site(session, "site-uuid", tool_probes, [42])
    body = put_mock.call_args.args[2]
    tests = body["synthetic_test"]["tests"]
    assert tests == [{"probes": ["mini-google-1", "zcc-crit"], "vlan_ids": [42]}]


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
    """'y' at the confirmation prompt fires exactly one PUT.

    Why:
        The post-PUT site-override prompt asks a third question; we answer
        'n' so the org-level PUT stays the only mutation this test asserts.
    """
    session = MagicMock()
    get_response = MagicMock(data={"synthetic_test": {"custom_probes": {}}})
    inputs = iter(["10", "y", "n"])  # VLAN, confirm PUT, decline site overrides.
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


# --------------------------------------------------------------------------- #
# Critical aggressiveness selection (Mist 5-per-org cap)
# --------------------------------------------------------------------------- #


def test_build_marks_only_critical_flagged_roles_as_critical() -> None:
    """A role with ``critical: true`` yields exactly one critical probe.

    Why:
        Mist caps priority probes (``critical`` + ``high``) at 5 per org.
        The builder must promote exactly one FQDN per critical role -- either
        the ``critical_fqdn`` hint or, absent that, the first non-wildcard
        FQDN -- and mark every other probe with ``aggressiveness=auto``
        (Mist's explicit default, which doesn't consume a priority slot;
        verified against a live org config 2026-07-24).
    """
    probes = {
        "roles": [
            {
                "role": "pac",
                "critical": True,
                "critical_fqdn": "pac.zscaler.net",
                "fqdns": ["pac.zscaler.net", "other.zscaler.net"],
            },
            {
                "role": "support",
                "fqdns": ["mobilesupport.zscaler.com"],
            },
        ],
    }
    result = ospm._build_probe_set((probes, {"proxy_hostnames": [], "vpn_hostnames": []}), [10])
    critical = {n: p for n, p in result.items() if p.get("aggressiveness") == ospm._CRITICAL_AGGRESSIVENESS}
    assert len(critical) == 1
    (only_name,) = critical
    assert only_name == "zcc-pac-pac-zscaler-net"
    non_critical = [p for p in result.values() if p.get("aggressiveness") == ospm._AUTO_AGGRESSIVENESS]
    assert non_critical, "Expected at least one non-critical probe"
    for probe in non_critical:
        assert probe["aggressiveness"] == ospm._AUTO_AGGRESSIVENESS


def test_demote_stale_critical_downgrades_foreign_probes() -> None:
    """Foreign probes with ``aggressiveness=critical`` get demoted to ``auto``.

    Why:
        A previous org config or another tool may have burned the 5-slot
        priority budget. Menu 206 relaxes strict foreign-preservation so it
        can force-write ``aggressiveness=auto`` on foreign criticals,
        matching Mist's own explicit-default convention so the tool's own
        five critical probes stay under the priority cap.
    """
    foreign = {
        "custom-a": {"name": "custom-a", "aggressiveness": "critical", "vlan_ids": [1]},
        "custom-b": {"name": "custom-b", "aggressiveness": "high", "vlan_ids": [1]},
    }
    demoted = ospm._demote_stale_critical(foreign)
    assert demoted["custom-a"]["aggressiveness"] == ospm._AUTO_AGGRESSIVENESS
    assert demoted["custom-b"]["aggressiveness"] == "high"
    # Original dict must not be mutated in-place.
    assert foreign["custom-a"]["aggressiveness"] == "critical"


def test_merge_syncs_aggressiveness_change_from_new_probes() -> None:
    """Merge downgrades a probe to ``auto`` when the new build omits critical.

    Why:
        Without this sync, a probe that lost critical status in the new
        build (i.e., is no longer one of the 5 curated critical roles) would
        stay ``critical`` after merge and silently keep consuming a priority
        slot. When the authoritative rebuild does not mark the probe as
        critical, the merged probe must fall back to ``aggressiveness=auto``
        so the tool converges to Mist's explicit-default convention.
    """
    existing_tool = {
        "zcc-pac-pac-zscaler-net": {
            "type": "application",
            "target": "https://pac.zscaler.net",
            "aggressiveness": "critical",
        }
    }
    new_probes = {
        "zcc-pac-pac-zscaler-net": {
            "type": "application",
            "target": "https://pac.zscaler.net",
            # No aggressiveness key -- role is no longer critical.
        }
    }
    merged = ospm._merge_probes(existing_tool, new_probes, [10])
    assert merged["zcc-pac-pac-zscaler-net"]["aggressiveness"] == ospm._AUTO_AGGRESSIVENESS


# --------------------------------------------------------------------------- #
# Site-override flow
# --------------------------------------------------------------------------- #


def test_site_override_prompt_declined_makes_no_calls() -> None:
    """Answering 'n' to the site-override prompt performs no API calls."""
    session = MagicMock()
    with (
        patch("builtins.input", side_effect=["n"]),
        patch.object(ospm._mist_orgs_sites, "listOrgSites") as list_mock,
        patch.object(ospm._mist_site_setting, "getSiteSetting") as get_mock,
        patch.object(ospm._mist_site_setting, "updateSiteSettings") as put_mock,
    ):
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}})
    list_mock.assert_not_called()
    get_mock.assert_not_called()
    put_mock.assert_not_called()


def test_site_override_prompt_empty_resulting_tool_returns_immediately() -> None:
    """No prompt is shown when there are no tool probes to push."""
    session = MagicMock()
    with (
        patch("builtins.input") as input_mock,
        patch.object(ospm._mist_orgs_sites, "listOrgSites") as list_mock,
        patch.object(ospm._mist_site_setting, "updateSiteSettings") as put_mock,
    ):
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {})
    input_mock.assert_not_called()
    list_mock.assert_not_called()
    put_mock.assert_not_called()


def test_site_override_indexed_prompt_applies_to_selected_sites() -> None:
    """Indexed selection resolves 1-based indexes to the correct site ids.

    Why:
        The new indexed prompt replaced raw UUID entry. This test locks in
        the mapping: index 1 -> sites[0], index 3 -> sites[2], and skips
        the middle site. It also confirms invalid/out-of-range tokens are
        silently ignored rather than aborting, and that the freshly
        prompted VLAN list flows onto the generated ``tests[]`` rows
        (not into probe bodies, which no longer carry ``vlan_ids``).
    """
    session = MagicMock()
    sites = [
        {"id": "site-1", "name": "Alpha"},
        {"id": "site-2", "name": "Bravo"},
        {"id": "site-3", "name": "Charlie"},
    ]
    list_response = MagicMock()
    get_response = MagicMock(data={})
    put_response = MagicMock(status_code=200)
    # Critical probe so _merge_zcc_criticals_into_tests emits a tests[] row.
    tool_probes = {
        "zcc-x": {
            "type": "application",
            "target": "https://x.example",
            "aggressiveness": "critical",
        }
    }
    # Third prompt is the VLAN list for site overrides; substitute [42].
    inputs = iter(["y", "1, 3, 99, notanumber", "42"])
    with (
        patch.object(ospm._mist_orgs_sites, "listOrgSites", return_value=list_response) as list_mock,
        patch.object(ospm.mistapi, "get_all", return_value=sites) as get_all_mock,
        patch.object(ospm._mist_site_setting, "getSiteSetting", return_value=get_response) as get_mock,
        patch.object(ospm._mist_site_setting, "updateSiteSettings", return_value=put_response) as put_mock,
        patch("builtins.input", lambda _prompt: next(inputs)),
    ):
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", tool_probes)
    list_mock.assert_called_once()
    get_all_mock.assert_called_once()
    # Exactly the two in-range indexes trigger a per-site PUT round-trip.
    assert get_mock.call_count == 2
    assert put_mock.call_count == 2
    put_site_ids = [call.args[1] for call in put_mock.call_args_list]
    assert put_site_ids == ["site-1", "site-3"]
    # Every PUT carries the prompted VLAN list on tests[] rows, and probe
    # bodies stay VLAN-free (mini-* shape).
    for call in put_mock.call_args_list:
        body = call.args[2]
        probes = body["synthetic_test"]["custom_probes"]
        assert "vlan_ids" not in probes["zcc-x"]
        tests = body["synthetic_test"]["tests"]
        assert any("zcc-x" in row.get("probes", []) and row.get("vlan_ids") == [42] for row in tests)


def test_site_override_indexed_prompt_empty_input_skips() -> None:
    """Blank index input skips the site flow without any per-site PUT."""
    session = MagicMock()
    sites = [{"id": "site-1", "name": "Alpha"}]
    list_response = MagicMock()
    inputs = iter(["y", ""])
    with (
        patch.object(ospm._mist_orgs_sites, "listOrgSites", return_value=list_response),
        patch.object(ospm.mistapi, "get_all", return_value=sites),
        patch.object(ospm._mist_site_setting, "getSiteSetting") as get_mock,
        patch.object(ospm._mist_site_setting, "updateSiteSettings") as put_mock,
        patch("builtins.input", lambda _prompt: next(inputs)),
    ):
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}})
    get_mock.assert_not_called()
    put_mock.assert_not_called()


def test_site_override_no_sites_short_circuits(capsys: pytest.CaptureFixture[str]) -> None:
    """An org with zero sites surfaces a message and skips per-site PUTs."""
    session = MagicMock()
    list_response = MagicMock()
    inputs = iter(["y"])
    with (
        patch.object(ospm._mist_orgs_sites, "listOrgSites", return_value=list_response),
        patch.object(ospm.mistapi, "get_all", return_value=[]),
        patch.object(ospm._mist_site_setting, "updateSiteSettings") as put_mock,
        patch("builtins.input", lambda _prompt: next(inputs)),
    ):
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}})
    out = capsys.readouterr().out
    assert "No sites found" in out
    put_mock.assert_not_called()


def test_apply_to_site_puts_combined_probes_and_preserves_siblings() -> None:
    """Site PUT carries tool probes plus demoted foreign, siblings intact."""
    session = MagicMock()
    site_setting = {
        "synthetic_test": {
            "custom_probes": {
                "old-foreign": {"name": "old-foreign", "aggressiveness": "critical"},
            },
            "other_sibling_field": {"keep": "me"},
        },
        "top_level_sibling": "keep",
    }
    tool_probes = {"zcc-new": {"name": "zcc-new", "aggressiveness": "critical"}}
    get_response = MagicMock(data=site_setting)
    put_response = MagicMock(status_code=200)
    with (
        patch.object(ospm._mist_site_setting, "getSiteSetting", return_value=get_response),
        patch.object(ospm._mist_site_setting, "updateSiteSettings", return_value=put_response) as put_mock,
    ):
        ospm._apply_to_site(session, "site-uuid", tool_probes, [10])
    body = put_mock.call_args.args[2]
    probes = body["synthetic_test"]["custom_probes"]
    assert probes["zcc-new"] == {"name": "zcc-new", "aggressiveness": "critical"}
    assert probes["old-foreign"]["aggressiveness"] == ospm._AUTO_AGGRESSIVENESS
    assert body["synthetic_test"]["other_sibling_field"] == {"keep": "me"}
    assert body["top_level_sibling"] == "keep"


# --------------------------------------------------------------------------- #
# Sort ordering
# --------------------------------------------------------------------------- #


def test_site_override_indexed_prompt_sorts_by_name() -> None:
    """Picker is sorted by human-readable site name (case-insensitive).

    Why:
        Operators pick by the name they see on the Mist dashboard, not
        the API return order. This test hands in an out-of-order site
        list and asserts index 1 maps to the alphabetically-first name,
        proving the sort is applied before the index map is built.
    """
    session = MagicMock()
    # Intentionally scrambled + mixed case to exercise casefold ordering.
    sites = [
        {"id": "id-charlie", "name": "charlie"},
        {"id": "id-alpha", "name": "Alpha"},
        {"id": "id-bravo", "name": "BRAVO"},
    ]
    list_response = MagicMock()
    get_response = MagicMock(data={})
    put_response = MagicMock(status_code=200)
    inputs = iter(["y", "1", "5"])  # index 1 -> Alpha; VLAN [5].
    with (
        patch.object(ospm._mist_orgs_sites, "listOrgSites", return_value=list_response),
        patch.object(ospm.mistapi, "get_all", return_value=sites),
        patch.object(ospm._mist_site_setting, "getSiteSetting", return_value=get_response),
        patch.object(ospm._mist_site_setting, "updateSiteSettings", return_value=put_response) as put_mock,
        patch("builtins.input", lambda _prompt: next(inputs)),
    ):
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}})
    assert put_mock.call_count == 1
    assert put_mock.call_args.args[1] == "id-alpha"


def test_site_override_unnamed_sites_sink_to_end() -> None:
    """Sites with no ``name`` sort after every named site regardless of id.

    Why:
        Unnamed sites are rare in production but happen (fresh onboards,
        API-provisioned sites without labels). Sinking them keeps the
        alphabetical section clean; picking index 1 must still land on a
        named site even when the API-return order puts the unnamed one
        first.
    """
    session = MagicMock()
    sites = [
        {"id": "id-unnamed", "name": None},
        {"id": "id-blankname", "name": "   "},
        {"id": "id-zulu", "name": "Zulu"},
        {"id": "id-alpha", "name": "Alpha"},
    ]
    list_response = MagicMock()
    get_response = MagicMock(data={})
    put_response = MagicMock(status_code=200)
    # Pick the last two indexes to prove the unnamed sites are 3 and 4.
    inputs = iter(["y", "3, 4", "7"])
    with (
        patch.object(ospm._mist_orgs_sites, "listOrgSites", return_value=list_response),
        patch.object(ospm.mistapi, "get_all", return_value=sites),
        patch.object(ospm._mist_site_setting, "getSiteSetting", return_value=get_response),
        patch.object(ospm._mist_site_setting, "updateSiteSettings", return_value=put_response) as put_mock,
        patch("builtins.input", lambda _prompt: next(inputs)),
    ):
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}})
    put_site_ids = [call.args[1] for call in put_mock.call_args_list]
    # Both blank-name entries land at the end. Ordering between them
    # tie-breaks on the casefolded name string first (empty "" sorts
    # before whitespace "   "), then on id.
    assert put_site_ids == ["id-unnamed", "id-blankname"]
