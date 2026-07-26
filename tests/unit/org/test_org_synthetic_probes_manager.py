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
from typing import Any
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
# Build from empty
# --------------------------------------------------------------------------- #


def test_build_from_empty_produces_https_prefixed_no_port_targets(probes_source: dict, cenr_source: dict) -> None:
    """Every probe target uses https:// prefix and no port suffix.

    Why:
        Targets must be ``https://<fqdn>`` with no port number, even when
        the source file lists ports.
    """
    result = ospm._build_probe_set((probes_source, cenr_source), [10])
    assert result, "Expected at least one probe"
    for name, probe in result.items():
        assert probe["target"].startswith("https://"), name
        assert ":" not in probe["target"].removeprefix("https://"), name
        assert name.startswith(ospm._TOOL_NAME_PREFIX), name


def test_build_from_empty_skips_wildcards(probes_source: dict, cenr_source: dict) -> None:
    """Entries starting with ``*.`` are filtered out."""
    result = ospm._build_probe_set((probes_source, cenr_source), [10])
    for probe in result.values():
        assert "*." not in probe["target"], probe


def test_build_from_empty_includes_tunnel_zen_cenr_hostnames(probes_source: dict, cenr_source: dict) -> None:
    """The tunnel_zen role expands via CENR hostnames.

    Why:
        The tunnel_zen role pulls its FQDN list from the CENR file so both
        proxy and vpn hostnames are covered by synthetic probes.
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
        priority cap counts ``tests[]`` array membership; ``high`` fills a
        slot, ``auto`` does not, so every non-critical probe carries an
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
# Merge
# --------------------------------------------------------------------------- #


def test_merge_strips_legacy_name_and_vlan_ids() -> None:
    """Merge strips legacy ``name``/``vlan_ids`` off existing probe bodies.

    Why:
        The live Mist config (2026-07-24) shows the correct shape is
        ``{type, target, aggressiveness}`` only, so the merge pass acts as
        a migration: any on-org probe still carrying the legacy fields is
        normalised on the next re-sync.
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
            "aggressiveness": "high",
        }
    }
    merged = ospm._merge_probes(existing_tool, new_probes, [20, 30])
    body = merged["zcc-pac-pac-zscaler-net"]
    assert "name" not in body
    assert "vlan_ids" not in body
    assert body["type"] == "application"
    assert body["target"] == "https://pac.zscaler.net"
    # aggressiveness re-syncs to freshly-built authoritative value.
    assert body["aggressiveness"] == "high"


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
# Swap
# --------------------------------------------------------------------------- #


def test_swap_preserves_foreign_probes() -> None:
    """Foreign probes survive swap unchanged."""
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
        Swap must not preserve legacy body fields (``name``/``vlan_ids``)
        on tool-authored probes -- the new set is authoritative and must
        land verbatim.
    """
    new_probes = {
        "zcc-pac-pac-zscaler-net": {
            "type": "application",
            "target": "https://pac.zscaler.net",
            "aggressiveness": "high",
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
    """Sibling fields under synthetic_test survive round-trip."""
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


def test_merge_emits_one_row_per_critical_probe() -> None:
    """Each critical zcc name gets its own ``tests[]`` row.

    Why:
        Mist emits one ``tests[]`` row per probe (each row's ``probes``
        array contains exactly one name), and the row carries its own
        ``vlan_ids`` / ``lan_networks`` copy. Foreign rows are preserved
        untouched and one nameless row is appended per critical ``zcc-*``
        probe, inheriting the first foreign row's ``vlan_ids`` and
        ``lan_networks`` so operator scoping flows to the injected rows.
    """
    existing = [
        {
            "probes": ["mini-cloudflare-1"],
            "vlan_ids": [3, 10],
            "lan_networks": ["Guest-WiFi", "servers"],
        }
    ]
    combined = {
        "zcc-crit-a": {"name": "zcc-crit-a", "aggressiveness": "high"},
        "zcc-plain": {"name": "zcc-plain", "aggressiveness": "auto"},
        "zcc-crit-b": {"name": "zcc-crit-b", "aggressiveness": "high"},
    }
    merged = ospm._merge_zcc_criticals_into_tests(existing, combined, [10])
    assert merged == [
        {
            "probes": ["mini-cloudflare-1"],
            "vlan_ids": [3, 10],
            "lan_networks": ["Guest-WiFi", "servers"],
        },
        {
            "probes": ["zcc-crit-a"],
            "vlan_ids": [3, 10],
            "lan_networks": ["Guest-WiFi", "servers"],
        },
        {
            "probes": ["zcc-crit-b"],
            "vlan_ids": [3, 10],
            "lan_networks": ["Guest-WiFi", "servers"],
        },
    ]


def test_merge_strips_stale_zcc_names_on_rerun() -> None:
    """Stale ``zcc-*`` names in a foreign row are stripped; a new row is added.

    Why:
        Re-runs must be idempotent. If a prior version of this module
        merged criticals into a foreign row's ``probes[]``, migration
        must strip those stale ``zcc-*`` names so the foreign row
        returns to its single-probe shape. The currently-critical
        probe is then appended as its own per-probe row.
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
            "aggressiveness": "high",
        },
    }
    merged = ospm._merge_zcc_criticals_into_tests(existing, combined, [1])
    assert merged == [
        {"probes": ["mini-a"], "vlan_ids": [1]},
        {"probes": ["zcc-still-critical"], "vlan_ids": [1]},
    ]


def test_merge_drops_legacy_aggregate_tool_row() -> None:
    """Legacy aggregate rows (name=zcc-*) are removed, replaced by per-probe rows.

    Why:
        Earlier iterations wrote a single row named
        ``zcc-critical-probes`` with every critical name bundled under
        it. Migration must drop such rows and re-emit one nameless
        row per critical probe to match Mist's own per-probe-row
        convention.
    """
    existing = [
        {"probes": ["mini-a"], "vlan_ids": [10]},
        {
            "name": "zcc-critical-probes",
            "probes": ["zcc-x", "zcc-y"],
            "vlan_ids": [10],
        },
    ]
    combined = {"zcc-x": {"name": "zcc-x", "aggressiveness": "high"}}
    merged = ospm._merge_zcc_criticals_into_tests(existing, combined, [10])
    assert merged == [
        {"probes": ["mini-a"], "vlan_ids": [10]},
        {"probes": ["zcc-x"], "vlan_ids": [10]},
    ]


def test_merge_drops_pure_zcc_rows_from_prior_per_probe_injection() -> None:
    """Prior per-probe zcc rows are dropped so re-injection is authoritative.

    Why:
        A row whose ``probes`` list contains only ``zcc-*`` names is a
        prior-run injection. When the curated critical set changes,
        those stale rows must go so the new critical set is emitted
        cleanly without leftover names.
    """
    existing = [
        {"probes": ["mini-a"], "vlan_ids": [10], "lan_networks": ["default"]},
        {"probes": ["zcc-old"], "vlan_ids": [10], "lan_networks": ["default"]},
    ]
    combined = {"zcc-new": {"name": "zcc-new", "aggressiveness": "high"}}
    merged = ospm._merge_zcc_criticals_into_tests(existing, combined, [10])
    assert merged == [
        {"probes": ["mini-a"], "vlan_ids": [10], "lan_networks": ["default"]},
        {"probes": ["zcc-new"], "vlan_ids": [10], "lan_networks": ["default"]},
    ]


def test_merge_fabricates_bare_row_when_no_foreign_row() -> None:
    """With no foreign template, injected rows use the supplied vlan_ids arg."""
    combined = {"zcc-x": {"name": "zcc-x", "aggressiveness": "high"}}
    merged = ospm._merge_zcc_criticals_into_tests([], combined, [42])
    assert merged == [{"probes": ["zcc-x"], "vlan_ids": [42]}]


def test_merge_no_criticals_leaves_foreign_row_alone() -> None:
    """Non-critical-only probe maps leave existing rows unchanged."""
    existing = [{"probes": ["mini-a"], "vlan_ids": [10]}]
    combined = {"zcc-plain": {"name": "zcc-plain", "aggressiveness": "auto"}}
    merged = ospm._merge_zcc_criticals_into_tests(existing, combined, [10])
    assert merged == [{"probes": ["mini-a"], "vlan_ids": [10]}]


def test_apply_appends_per_probe_rows_for_criticals() -> None:
    """Org PUT body appends one ``tests[]`` row per critical zcc probe.

    Why:
        Regression guard for the per-probe-row fix: the live Mist
        config shows one nameless row per probe. The tool must append
        a new row for each critical zcc name rather than bundling them
        into an existing foreign row's ``probes`` list.
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
    assert tests == [
        {"probes": ["mini-cloudflare-1"], "vlan_ids": [10]},
        {"probes": ["zcc-crit"], "vlan_ids": [10]},
    ]


def test_apply_to_site_appends_per_probe_rows_for_criticals() -> None:
    """Site PUT body appends one ``tests[]`` row per critical zcc probe."""
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
        ospm._apply_to_site(
            session,
            {"id": "site-uuid"},
            tool_probes,
            [42],
            ({"roles": []}, {}),
        )
    body = put_mock.call_args.args[2]
    tests = body["synthetic_test"]["tests"]
    assert tests == [
        {"probes": ["mini-google-1"], "vlan_ids": [42]},
        {"probes": ["zcc-crit"], "vlan_ids": [42]},
    ]


# --------------------------------------------------------------------------- #
# Region probes (site-scope only)
# --------------------------------------------------------------------------- #


@pytest.fixture()
def region_probes_source() -> dict:
    """Return a probes-source dict containing all three Samsung ELM roles.

    Why:
        ``_build_region_probes`` reads the shared probe source file and picks
        the one role matching the site's resolved region. The tests need a
        fixture with all three regions declared so we can exercise the
        Americas / EMEA / China dispatch paths from a single input.

    Returns:
        Parsed probe-source dict with three ``samsung_elm_activation_*``
        roles plus a couple of unrelated roles as noise.
    """
    return {
        "schema_version": 2,
        "source": "fixture",
        "wildcards": [],
        "roles": [
            {
                "role": "pac",  # Noise: ensures the region matcher is exact.
                "ports": [443],
                "fqdns": ["pac.zscaler.net"],
            },
            {
                "role": "samsung_elm_activation_americas",
                "fqdns": ["elm.us.example.com", "*.wild.example.com"],
            },
            {
                "role": "samsung_elm_activation_emea",
                "fqdns": ["elm.eu.example.com"],
            },
            {
                "role": "samsung_elm_activation_china",
                "fqdns": ["elm.cn.example.com.cn"],
            },
        ],
    }


def test_build_region_probes_us_selects_americas_role(region_probes_source: dict) -> None:
    """US country code yields the ``americas`` ELM probes only.

    Why:
        US is in ``_COUNTRY_CODE_TO_REGION`` -> ``americas``; the helper
        must return exactly the concrete-FQDN probes from that role and
        must NOT emit anything for EMEA or China (avoiding site-scope
        noise for probes that would never resolve locally).
    """
    result = ospm._build_region_probes((region_probes_source, {}), "US")
    assert list(result.keys()) == ["zcc-samsung_elm_activation_americas-elm-us-example-com"]
    body = result["zcc-samsung_elm_activation_americas-elm-us-example-com"]
    # Wildcards are structurally unprobable so must be dropped.
    assert body == {
        "type": "application",
        "target": "https://elm.us.example.com",
        "aggressiveness": "auto",
    }


def test_build_region_probes_unmapped_country_falls_back_to_emea(
    region_probes_source: dict,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """DE (unmapped) resolves to EMEA and logs a warning.

    Why:
        Every ISO code not enumerated in ``_COUNTRY_CODE_TO_REGION`` must
        default to EMEA (broadest surface) and the warning is the only
        signal operators get that a code is missing from the mapping.
    """
    with caplog.at_level("WARNING"):
        result = ospm._build_region_probes((region_probes_source, {}), "DE")
    assert list(result.keys()) == ["zcc-samsung_elm_activation_emea-elm-eu-example-com"]
    assert any("not mapped" in rec.message and "emea" in rec.message for rec in caplog.records)


def test_build_region_probes_none_country_falls_back_to_emea(
    region_probes_source: dict,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Missing / ``None`` country_code still resolves to EMEA (with warning).

    Why:
        Not every Mist site record carries a ``country_code``; the helper
        must degrade to the default region rather than raise so the site-
        override flow does not abort mid-run for one under-configured site.
    """
    with caplog.at_level("WARNING"):
        result = ospm._build_region_probes((region_probes_source, {}), None)
    assert list(result.keys()) == ["zcc-samsung_elm_activation_emea-elm-eu-example-com"]
    assert any("not mapped" in rec.message for rec in caplog.records)


def test_build_region_probes_cn_selects_china_role(region_probes_source: dict) -> None:
    """CN country code yields the ``china`` ELM probes only.

    Why:
        China + SARs + Taiwan hit ``.com.cn`` endpoints; routing them to
        the EMEA fallback would send traffic to unreachable ``.com`` hosts,
        so this dispatch is a correctness (not just noise) guard.
    """
    result = ospm._build_region_probes((region_probes_source, {}), "CN")
    assert list(result.keys()) == ["zcc-samsung_elm_activation_china-elm-cn-example-com-cn"]


def test_build_region_probes_country_code_is_case_insensitive(region_probes_source: dict) -> None:
    """Lowercase / mixed-case country codes normalise before lookup.

    Why:
        Mist site records occasionally carry lowercase country codes; the
        helper upper-cases before hitting the map so ``"us"`` resolves the
        same way as ``"US"``.
    """
    result = ospm._build_region_probes((region_probes_source, {}), "us")
    assert list(result.keys()) == ["zcc-samsung_elm_activation_americas-elm-us-example-com"]


def test_build_region_probes_missing_role_returns_empty() -> None:
    """Returning empty when the resolved role isn't in the source is safe.

    Why:
        Defensive: if the shipped catalogue is ever pruned to omit one of
        the three region roles, the site-override flow must silently
        contribute zero region probes rather than raise.
    """
    stripped = {"roles": [{"role": "pac", "fqdns": ["pac.zscaler.net"]}]}
    result = ospm._build_region_probes((stripped, {}), "US")
    assert result == {}


# --------------------------------------------------------------------------- #
# Scheduler: extra_regular_names (region-probe scheduling)
# --------------------------------------------------------------------------- #


def test_merge_extra_regular_names_appends_rows_after_criticals() -> None:
    """Regular names emit tests[] rows after critical rows, alphabetically.

    Why:
        Region probes are ``auto`` aggressiveness so the default critical-
        only filter would leave them defined but never scheduled. The
        opt-in ``extra_regular_names`` closes that gap; ordering must be
        stable (critical block first, regular block second, both sorted)
        so callers/assertions never see reshuffling.
    """
    combined = {
        "zcc-crit": {"name": "zcc-crit", "aggressiveness": "critical"},
        "zcc-samsung_elm_activation_americas-a": {"aggressiveness": "auto"},
        "zcc-samsung_elm_activation_americas-b": {"aggressiveness": "auto"},
    }
    merged = ospm._merge_zcc_criticals_into_tests(
        [],
        combined,
        [10],
        extra_regular_names=[
            "zcc-samsung_elm_activation_americas-b",
            "zcc-samsung_elm_activation_americas-a",
        ],
    )
    assert merged == [
        {"probes": ["zcc-crit"], "vlan_ids": [10]},
        {"probes": ["zcc-samsung_elm_activation_americas-a"], "vlan_ids": [10]},
        {"probes": ["zcc-samsung_elm_activation_americas-b"], "vlan_ids": [10]},
    ]


def test_merge_extra_regular_names_deduplicates_against_criticals() -> None:
    """A name appearing in both lists emits exactly one (critical) row.

    Why:
        Guardrail: if region-role naming ever collides with a critical
        role name, the probe still runs but only once -- writing two rows
        for the same probe would be a shape divergence Mist operators
        would flag as wrong.
    """
    combined = {"zcc-shared": {"aggressiveness": "critical"}}
    merged = ospm._merge_zcc_criticals_into_tests(
        [],
        combined,
        [10],
        extra_regular_names=["zcc-shared"],
    )
    assert merged == [{"probes": ["zcc-shared"], "vlan_ids": [10]}]


def test_merge_extra_regular_names_inherits_template_vlan_and_lan() -> None:
    """Regular rows inherit vlan_ids / lan_networks from the first foreign row.

    Why:
        Region rows should follow the same scoping the operator already
        applied to their existing schedule rather than the fallback
        ``vlan_ids`` arg, so injected probes stay inside the site's
        intended reachability scope.
    """
    existing = [
        {
            "probes": ["mini-a"],
            "vlan_ids": [99],
            "lan_networks": ["net-uuid"],
        }
    ]
    combined = {"zcc-region": {"aggressiveness": "auto"}}
    merged = ospm._merge_zcc_criticals_into_tests(
        existing,
        combined,
        [10],  # Fallback -- must be ignored because template exists.
        extra_regular_names=["zcc-region"],
    )
    assert merged == [
        {"probes": ["mini-a"], "vlan_ids": [99], "lan_networks": ["net-uuid"]},
        {"probes": ["zcc-region"], "vlan_ids": [99], "lan_networks": ["net-uuid"]},
    ]


def test_merge_extra_regular_names_empty_still_returns_surviving() -> None:
    """Empty ``extra_regular_names`` behaves like the omitted-arg default.

    Why:
        Back-compat guard: existing callers that never pass the new arg
        must see identical behaviour to before, so an empty list must be
        indistinguishable from ``None``.
    """
    existing = [{"probes": ["mini-a"], "vlan_ids": [10]}]
    combined = {"zcc-plain": {"aggressiveness": "auto"}}
    merged = ospm._merge_zcc_criticals_into_tests(
        existing,
        combined,
        [10],
        extra_regular_names=[],
    )
    assert merged == [{"probes": ["mini-a"], "vlan_ids": [10]}]


# --------------------------------------------------------------------------- #
# Site-apply: end-to-end region-probe scheduling
# --------------------------------------------------------------------------- #


def test_apply_to_site_schedules_region_probes_by_country_code(
    region_probes_source: dict,
) -> None:
    """Site with ``country_code=US`` gets region probes in custom_probes AND tests[].

    Why:
        End-to-end guard for the fix: a probe defined in ``custom_probes``
        but absent from ``tests[]`` is silently never scheduled. The site-
        apply path must both inject the region probe body AND emit the
        matching per-probe row, otherwise the region roles are dead code.
    """
    session = MagicMock()
    tool_probes = {
        "zcc-crit": {"name": "zcc-crit", "aggressiveness": "critical"},
    }
    get_response = MagicMock(data={"synthetic_test": {"tests": []}})
    put_response = MagicMock(status_code=200)
    with (
        patch.object(ospm._mist_site_setting, "getSiteSetting", return_value=get_response),
        patch.object(
            ospm._mist_site_setting,
            "updateSiteSettings",
            return_value=put_response,
        ) as put_mock,
    ):
        ospm._apply_to_site(
            session,
            {"id": "site-uuid", "country_code": "US"},
            tool_probes,
            [42],
            (region_probes_source, {}),
        )
    body = put_mock.call_args.args[2]
    custom = body["synthetic_test"]["custom_probes"]
    tests = body["synthetic_test"]["tests"]
    # Region probe is present in custom_probes with auto aggressiveness.
    assert "zcc-samsung_elm_activation_americas-elm-us-example-com" in custom
    assert custom["zcc-samsung_elm_activation_americas-elm-us-example-com"]["aggressiveness"] == "auto"
    # AND it received its own tests[] row -- otherwise Mist would define
    # but never schedule the probe.
    assert tests == [
        {"probes": ["zcc-crit"], "vlan_ids": [42]},
        {"probes": ["zcc-samsung_elm_activation_americas-elm-us-example-com"], "vlan_ids": [42]},
    ]


def test_apply_to_site_de_uses_emea_region_probes(
    region_probes_source: dict,
) -> None:
    """Site with ``country_code=DE`` gets EMEA region probes via fallback.

    Why:
        DE isn't in the country map, so the EMEA fallback fires; the site
        must still receive the correct region's ELM probes rather than the
        Americas or China set (which target completely different hosts).
    """
    session = MagicMock()
    get_response = MagicMock(data={"synthetic_test": {"tests": []}})
    put_response = MagicMock(status_code=200)
    with (
        patch.object(ospm._mist_site_setting, "getSiteSetting", return_value=get_response),
        patch.object(
            ospm._mist_site_setting,
            "updateSiteSettings",
            return_value=put_response,
        ) as put_mock,
    ):
        ospm._apply_to_site(
            session,
            {"id": "site-uuid", "country_code": "DE"},
            {},
            [7],
            (region_probes_source, {}),
        )
    body = put_mock.call_args.args[2]
    custom = body["synthetic_test"]["custom_probes"]
    tests = body["synthetic_test"]["tests"]
    assert "zcc-samsung_elm_activation_emea-elm-eu-example-com" in custom
    assert "zcc-samsung_elm_activation_americas-elm-us-example-com" not in custom
    assert "zcc-samsung_elm_activation_china-elm-cn-example-com-cn" not in custom
    assert tests == [
        {"probes": ["zcc-samsung_elm_activation_emea-elm-eu-example-com"], "vlan_ids": [7]},
    ]


# --------------------------------------------------------------------------- #
# Confirmation & abort
# --------------------------------------------------------------------------- #


def test_confirm_no_aborts_without_put(
    data_dir: Path,
) -> None:
    """When the operator answers 'n', no PUT is issued."""
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
# CENR auto-refresh wiring
# --------------------------------------------------------------------------- #


def test_load_probe_sources_threads_ensure_fresh_result(
    monkeypatch: pytest.MonkeyPatch,
    data_dir: Path,
) -> None:
    """``_load_probe_sources`` must route the CENR dict through ``ensure_fresh``.

    Why:
        The auto-refresh contract lives at a single choke point: every menu
        206 code path reads the CENR catalogue via ``_load_probe_sources``, so
        that function -- and only that function -- calls
        ``src.utils.zscaler_catalogue.ensure_fresh`` with the on-disk cenr
        path and dict. If a maintainer removes the call, downstream callers
        would silently serve stale (or single-cloud) hostnames until the
        cache was manually rotated. Assert the call signature *and* that the
        return value replaces the caller's dict, so both halves of the wiring
        remain covered.
    """
    captured: dict[str, Any] = {}
    sentinel = {"proxy_hostnames": ["refreshed.zscaler.net"], "vpn_hostnames": []}

    def fake_ensure_fresh(cenr_path: Path, cenr: dict[str, Any]) -> dict[str, Any]:
        """Record the call args and swap in a sentinel dict."""
        captured["cenr_path"] = cenr_path
        captured["cenr_in"] = cenr
        return sentinel

    monkeypatch.setattr(ospm, "ensure_fresh", fake_ensure_fresh)

    _probes, cenr_out = ospm._load_probe_sources(data_dir)

    assert captured["cenr_path"] == data_dir / ospm._CENR_SOURCE_FILE
    # The dict passed in is the parsed on-disk cenr file (from the fixture).
    assert isinstance(captured["cenr_in"], dict)
    assert "proxy_hostnames" in captured["cenr_in"]
    # The returned cenr is the sentinel produced by ensure_fresh, proving the
    # refreshed value is what flows through to downstream callers.
    assert cenr_out is sentinel


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
    """Foreign probes with any priority-tier aggressiveness get demoted to ``auto``.

    Why:
        A previous org config or another tool may have burned the 5-slot
        priority budget. Menu 206 relaxes strict foreign-preservation so it
        can force-write ``aggressiveness=auto`` on foreign priority-tier
        probes -- both ``"critical"`` and ``"high"`` count against the cap
        -- so the tool's own five critical probes stay under the priority
        cap regardless of which spelling the prior writer chose.
    """
    foreign = {
        "custom-a": {"name": "custom-a", "aggressiveness": "critical", "vlan_ids": [1]},
        "custom-b": {"name": "custom-b", "aggressiveness": "high", "vlan_ids": [1]},
        "custom-c": {"name": "custom-c", "aggressiveness": "auto", "vlan_ids": [1]},
    }
    demoted = ospm._demote_stale_critical(foreign)
    # Both priority-tier spellings get demoted; ``auto`` is left alone.
    assert demoted["custom-a"]["aggressiveness"] == ospm._AUTO_AGGRESSIVENESS
    assert demoted["custom-b"]["aggressiveness"] == ospm._AUTO_AGGRESSIVENESS
    assert demoted["custom-c"]["aggressiveness"] == "auto"
    # Original dict must not be mutated in-place.
    assert foreign["custom-a"]["aggressiveness"] == "critical"
    assert foreign["custom-b"]["aggressiveness"] == "high"


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
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}}, ({"roles": []}, {}))
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
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {}, ({"roles": []}, {}))
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
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", tool_probes, ({"roles": []}, {}))
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
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}}, ({"roles": []}, {}))
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
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}}, ({"roles": []}, {}))
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
        ospm._apply_to_site(
            session,
            {"id": "site-uuid"},
            tool_probes,
            [10],
            ({"roles": []}, {}),
        )
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
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}}, ({"roles": []}, {}))
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
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}}, ({"roles": []}, {}))
    put_site_ids = [call.args[1] for call in put_mock.call_args_list]
    # Both blank-name entries land at the end. Ordering between them
    # tie-breaks on the casefolded name string first (empty "" sorts
    # before whitespace "   "), then on id.
    assert put_site_ids == ["id-unnamed", "id-blankname"]
