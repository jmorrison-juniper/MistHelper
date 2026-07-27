"""Unit tests for ``src/org/org_synthetic_probes_manager.py`` (menu 206).

Why:
    The synthetic-probe manager mutates a shared org setting on every run,
    so every acceptance scenario in ``spec.md`` gets its own pinned test.
    Tests exercise the pure helpers directly and the public entry via
    ``patch.object`` on the module-level ``_mist_setting`` re-export.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime  # UTC-anchored freshness stamp for CENR fixture.
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.org import org_synthetic_probes_manager as ospm

# --------------------------------------------------------------------------- #
# Module-level constants (feature 1025)
# --------------------------------------------------------------------------- #

# Pinned enumeration of the 7 SecB2B catalogue hosts that MUST be absent from
# the loaded CENR observation cache so the CENR-fallback code path fires and
# each host contributes exactly one load-time WARNING once feature 1025 lands.
# Why:
#     Sourced from the sidecar fixture ``cenr_dedup_missing_observations.json``
#     authored in T006a. Duplicated here as a module-level constant so every
#     US1 test (T007/T008/T009) can reuse the same ground truth without
#     re-reading the sidecar file on each invocation. Encoded as a
#     ``frozenset`` so downstream tests cannot accidentally mutate the set
#     mid-run and blur the load-time dedup contract.
EXPECTED_MISSING_HOSTS: frozenset[str] = frozenset(
    {
        "gslb.secb2b.com",  # global SecB2B GSLB endpoint absent from smoke CENR
        "us-elm.secb2b.com",  # Americas ELM node absent from smoke CENR
        "us-prod-klm-b2c.secb2b.com",  # Americas B2C KLM host absent from smoke CENR
        "us-prod-klm.secb2b.com",  # Americas KLM host absent from smoke CENR
        "eu-elm.secb2b.com",  # EMEA ELM node absent from smoke CENR
        "eu-prod-klm-b2c.secb2b.com",  # EMEA B2C KLM host absent from smoke CENR
        "eu-prod-klm.secb2b.com",  # EMEA KLM host absent from smoke CENR
    }
)

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
        # Stamp a current UTC timestamp so ``zscaler_catalogue.is_stale``
        # returns False and ``ensure_fresh`` skips the real-network refresh
        # path. Without this, any test that calls ``manage_org_synthetic_probes``
        # (which threads through ``_load_probe_sources -> ensure_fresh``) would
        # spawn a real multi-host probe fleet and hang on Windows CI when the
        # environment has no outbound reachability.
        "fetched_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
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
    """HTTPS proxy targets use https:// prefix; VPN targets emit bare hostnames.

    Why:
        Proxy targets (ZIA HTTPS 443) must be ``https://<fqdn>`` with no
        port suffix. VPN targets (IPsec/IKE UDP 500/4500) must be a bare
        ``<fqdn>`` string with no port and no scheme — feature 1024
        pivoted the VPN branch from a fake L4 probe (``host:500`` as
        ``application``) to a truthful Mist Marvis Minis
        ``reachability`` probe (bare hostname, ICMP). The pre-1024 shape
        ``host:500`` produced 100% guaranteed-fail probes because Mist
        cannot speak IKEv2 on UDP/500.
    """
    result = ospm._build_probe_set((probes_source, cenr_source), [10])
    assert result, "Expected at least one probe"
    vpn_hosts = {h.lower() for h in cenr_source.get("vpn_hostnames", []) or []}
    for name, probe in result.items():
        assert name.startswith(ospm._TOOL_NAME_PREFIX), name
        target = probe["target"]
        # Extract fqdn from probe name (tool prefix + role + slugified fqdn).
        # We use the raw target to classify: bare hostname -> VPN, else HTTPS.
        if any(vpn_host.replace(".", "-") in name for vpn_host in vpn_hosts):
            # 1024: VPN endpoints emit as bare hostname (ICMP reachability),
            # never HTTPS and never with a ":port" suffix. INV-3 guard.
            assert not target.startswith("https://"), (name, target)
            assert not target.startswith("http://"), (name, target)
            assert ":" not in target, (name, target)
        else:
            # Everything else (proxy/443, service discovery, pac) is HTTPS.
            assert target.startswith("https://"), (name, target)
            assert ":" not in target.removeprefix("https://"), (name, target)


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
        belongs on the ``tests[]`` row). ``type`` is classified from the
        target's shape: HTTP/S URLs get ``"application"`` (URL-based
        check), bare ``host:port`` targets (VPN UDP:500, custom L4) get
        ``"reachability"`` (raw connectivity check). Emitting a VPN
        UDP:500 target as ``application`` would make Mist attempt an
        HTTP GET against an IKE listener. Mist's 5-probe priority cap
        counts ``tests[]`` array membership; ``high`` fills a slot,
        ``auto`` does not, so every non-critical probe carries an
        explicit ``"auto"`` value rather than leaving the key unset.
    """
    result = ospm._build_probe_set((probes_source, cenr_source), [10])
    for probe in result.values():
        target = probe["target"]
        expected_type = "reachability" if not target.startswith(("http://", "https://")) else "application"
        assert probe["type"] == expected_type, (probe, expected_type)
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
    """Out-of-range tokens are dropped; in-range survivors accepted."""
    # First entry: all out-of-range -> re-prompt.
    # Second entry: mix of invalid and valid -> invalids dropped, valids kept.
    with patch("builtins.input", side_effect=["4095, 0, -1, abc", "0, 1, 4094, 4095"]):
        assert ospm._prompt_vlan_list() == [1, 4094]


def test_prompt_dedupes_and_sorts() -> None:
    """Duplicate VLAN ids collapse and result is sorted."""
    with patch("builtins.input", side_effect=["30, 10, 30, 20"]):
        assert ospm._prompt_vlan_list() == [10, 20, 30]


def test_prompt_expands_vlan_ranges() -> None:
    """Ranges like ``3-6`` expand to individual ids; mixed with singletons."""
    with patch("builtins.input", side_effect=["3-6, 10, 200-203"]):
        assert ospm._prompt_vlan_list() == [3, 4, 5, 6, 10, 200, 201, 202, 203]


def test_prompt_drops_invalid_range_endpoints() -> None:
    """Ranges with out-of-range or reversed endpoints are dropped silently."""
    # "0-3" -> expands to 0,1,2,3; 0 dropped -> keeps 1,2,3.
    # "4093-4096" -> expands to 4093..4096; 4095,4096 dropped -> keeps 4093,4094.
    # "10-5" -> reversed, dropped entirely.
    # "abc-5" -> unparseable, dropped entirely.
    with patch("builtins.input", side_effect=["0-3, 4093-4096, 10-5, abc-5"]):
        assert ospm._prompt_vlan_list() == [1, 2, 3, 4093, 4094]


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
    """DE (not in region map) resolves to EMEA silently.

    Why:
        Every ISO code not enumerated in ``_COUNTRY_CODE_TO_REGION`` must
        default to EMEA (broadest surface). Post 1025-US2 the WARNING
        surfaced by ``_build_region_probes`` was relocated to a single
        load-time emission in ``_emit_load_time_country_code_warning``
        so that the region resolver stays silent and cannot re-introduce
        N*K per-site duplication. This test pins BOTH invariants: the
        EMEA fallback (URL builder unchanged, INV-1) AND resolver
        silence (no WARN from _build_region_probes itself).
    """
    with caplog.at_level("WARNING"):
        result = ospm._build_region_probes((region_probes_source, {}), "DE")
    assert list(result.keys()) == ["zcc-samsung_elm_activation_emea-elm-eu-example-com"]
    # Resolver silence: WARNs live at load time now (1025-US2).
    warnings = [rec for rec in caplog.records if rec.levelno == logging.WARNING]
    assert warnings == [], (
        "_build_region_probes must be silent after 1025-US2; "
        f"observed {len(warnings)}: {[r.getMessage() for r in warnings]}"
    )


def test_build_region_probes_none_country_falls_back_to_emea(
    region_probes_source: dict,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Missing / ``None`` country_code still resolves to EMEA silently.

    Why:
        Not every Mist site record carries a ``country_code``; the helper
        must degrade to the default region rather than raise so the site-
        override flow does not abort mid-run for one under-configured site.
        Post 1025-US2 the resolver stays silent -- any operator-visible
        signal about unmapped codes now lives in the load-time WARNING
        emitted once per invocation by
        ``_emit_load_time_country_code_warning``.
    """
    with caplog.at_level("WARNING"):
        result = ospm._build_region_probes((region_probes_source, {}), None)
    assert list(result.keys()) == ["zcc-samsung_elm_activation_emea-elm-eu-example-com"]
    # Resolver silence: WARNs live at load time now (1025-US2).
    warnings = [rec for rec in caplog.records if rec.levelno == logging.WARNING]
    assert warnings == [], (
        "_build_region_probes must be silent after 1025-US2; "
        f"observed {len(warnings)}: {[r.getMessage() for r in warnings]}"
    )


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
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}}, ({"roles": []}, {}), set())
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
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {}, ({"roles": []}, {}), set())
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
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", tool_probes, ({"roles": []}, {}), set())
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
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}}, ({"roles": []}, {}), set())
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
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}}, ({"roles": []}, {}), set())
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
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}}, ({"roles": []}, {}), set())
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
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}}, ({"roles": []}, {}), set())
    put_site_ids = [call.args[1] for call in put_mock.call_args_list]
    # Both blank-name entries land at the end. Ordering between them
    # tie-breaks on the casefolded name string first (empty "" sorts
    # before whitespace "   "), then on id.
    assert put_site_ids == ["id-unnamed", "id-blankname"]


def test_prompt_mode_defaults_to_swap_on_empty_input() -> None:
    """Empty input selects swap without re-prompting.

    Why:
        Swap is the default because the typical operator intent for this
        menu is a clean rebuild from the freshly-generated probe set --
        merge is the exception path. Locks in the empty-string -> swap
        behavior so a future prompt-string tweak cannot silently regress
        it back to a required-input loop.
    """
    with patch("builtins.input", side_effect=[""]):
        assert ospm._prompt_mode({"zcc-x": {"name": "zcc-x"}}) == "swap"


def test_prompt_mode_still_accepts_explicit_merge_or_swap() -> None:
    """Explicit ``merge`` / ``swap`` continue to work despite the default."""
    with patch("builtins.input", side_effect=["merge"]):
        assert ospm._prompt_mode({}) == "merge"
    with patch("builtins.input", side_effect=["swap"]):
        assert ospm._prompt_mode({}) == "swap"


def test_site_override_indexed_prompt_expands_ranges() -> None:
    """Range shorthand ``3-6`` expands to individual site indexes.

    Why:
        Operators paste condensed lists from other tools (switch configs,
        change-management tickets). Expanding ranges at this prompt
        matches the shorthand introduced in _validate_vlan_input so both
        prompts feel consistent.
    """
    session = MagicMock()
    sites = [{"id": f"site-{i}", "name": f"Site{chr(64 + i)}"} for i in range(1, 7)]
    list_response = MagicMock()
    get_response = MagicMock(data={})
    put_response = MagicMock(status_code=200)
    inputs = iter(["y", "2-4, 6", "10"])
    with (
        patch.object(ospm._mist_orgs_sites, "listOrgSites", return_value=list_response),
        patch.object(ospm.mistapi, "get_all", return_value=sites),
        patch.object(ospm._mist_site_setting, "getSiteSetting", return_value=get_response),
        patch.object(ospm._mist_site_setting, "updateSiteSettings", return_value=put_response) as put_mock,
        patch("builtins.input", lambda _prompt: next(inputs)),
    ):
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}}, ({"roles": []}, {}), set())
    put_site_ids = [call.args[1] for call in put_mock.call_args_list]
    # Sort key is site name, so indexes 1..6 map to SiteA..SiteF in order.
    # 2-4 -> site-2, site-3, site-4; 6 -> site-6.
    assert put_site_ids == ["site-2", "site-3", "site-4", "site-6"]


def test_site_override_indexed_prompt_all_token_selects_every_site() -> None:
    """``all`` (case-insensitive) selects every site in the sorted list."""
    session = MagicMock()
    sites = [
        {"id": "site-1", "name": "Alpha"},
        {"id": "site-2", "name": "Bravo"},
        {"id": "site-3", "name": "Charlie"},
    ]
    list_response = MagicMock()
    get_response = MagicMock(data={})
    put_response = MagicMock(status_code=200)
    inputs = iter(["y", "ALL", "42"])
    with (
        patch.object(ospm._mist_orgs_sites, "listOrgSites", return_value=list_response),
        patch.object(ospm.mistapi, "get_all", return_value=sites),
        patch.object(ospm._mist_site_setting, "getSiteSetting", return_value=get_response),
        patch.object(ospm._mist_site_setting, "updateSiteSettings", return_value=put_response) as put_mock,
        patch("builtins.input", lambda _prompt: next(inputs)),
    ):
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}}, ({"roles": []}, {}), set())
    put_site_ids = sorted(call.args[1] for call in put_mock.call_args_list)
    assert put_site_ids == ["site-1", "site-2", "site-3"]


def test_site_override_indexed_prompt_range_drops_out_of_range() -> None:
    """Range endpoints that spill past the list clamp silently -- no crash."""
    session = MagicMock()
    sites = [
        {"id": "site-1", "name": "Alpha"},
        {"id": "site-2", "name": "Bravo"},
    ]
    list_response = MagicMock()
    get_response = MagicMock(data={})
    put_response = MagicMock(status_code=200)
    # "1-5" -> keep only in-range 1 and 2; "5-1" -> reversed, dropped entirely.
    inputs = iter(["y", "1-5, 5-1", "10"])
    with (
        patch.object(ospm._mist_orgs_sites, "listOrgSites", return_value=list_response),
        patch.object(ospm.mistapi, "get_all", return_value=sites),
        patch.object(ospm._mist_site_setting, "getSiteSetting", return_value=get_response),
        patch.object(ospm._mist_site_setting, "updateSiteSettings", return_value=put_response) as put_mock,
        patch("builtins.input", lambda _prompt: next(inputs)),
    ):
        ospm._prompt_and_apply_site_overrides(session, "org-uuid", {"zcc-x": {"name": "zcc-x"}}, ({"roles": []}, {}), set())
    put_site_ids = [call.args[1] for call in put_mock.call_args_list]
    assert put_site_ids == ["site-1", "site-2"]


# --------------------------------------------------------------------------- #
# US1: _probe_target three-branch dispatch (contract:
# specs/1023-probe-tailored-synthetic-tests/contracts/probe_target_url_builder.md)
# --------------------------------------------------------------------------- #


def _make_tunnel_zen_role() -> dict[str, Any]:
    """Return a minimal tunnel_zen role for URL-builder tests.

    Why:
        _probe_target's lookup path for CENR-derived hostnames is gated
        on ``role["role"] == _TUNNEL_ZEN_ROLE``; every US1 test targets
        that branch since it is the one that carries the observation
        state per contract Preconditions.

    Returns:
        A role dict whose only meaningful field is the ``role`` name.
    """
    # The URL builder only needs the role name to route into the CENR
    # bag; the ``probe`` sub-block is deliberately absent so the fallback
    # branch is exercised by _cenr_source_with(...) supplying (or omitting)
    # observation fields directly on the host entry.
    return {"role": ospm._TUNNEL_ZEN_ROLE}


def _cenr_source_with(
    host: str,
    *,
    bag: str = "vpn_hostnames",
    observed_protocol: str | None,
    observed_port: int | None,
    include_key: bool = True,
    probe_default_protocol: str = "https",
    probe_default_port: int = 443,
) -> dict[str, Any]:
    """Assemble a v3-shaped CENR source dict with one host entry under control.

    Why:
        Each US1 test needs precise control over the single host's
        observation triplet without pulling in the full production
        catalogue. ``include_key=False`` lets T039 exercise the
        "hostname absent from every bag" fallback branch.

    Args:
        host: Fully-qualified hostname to seed the target bag with.
        bag: Which CENR bag to place ``host`` under
            (``vpn_hostnames`` vs ``proxy_hostnames``). Both bags share
            the same v3 entry shape per schema contract.
        observed_protocol: Value to store under ``observed_protocol``
            (or ``None`` to model an unprobed host).
        observed_port: Value to store under ``observed_port``.
        include_key: When ``False``, ``host`` is omitted from the bag
            entirely so the URL builder must fall back to the catalogue
            default.
        probe_default_protocol: Value for ``probe_default.protocol`` in
            the fallback branch; kept a knob so tests can prove elision
            of the default port for https.
        probe_default_port: Value for ``probe_default.port`` in the
            fallback branch.

    Returns:
        A v3-shaped CENR document with exactly one entry (or zero, when
        ``include_key`` is False) in the chosen bag.
    """
    # The CENR document carries a fallback ``probe_default`` block that
    # Branch 3 consults; keep it configurable so tests can pin both the
    # default-port-elided form and an explicit-port form.
    doc: dict[str, Any] = {
        "schema_version": 3,
        "probe_default": {
            "protocol": probe_default_protocol,
            "port": probe_default_port,
        },
        "proxy_hostnames": [],
        "vpn_hostnames": [],
    }
    if include_key:
        # Build a v3 host entry with the observation triplet supplied by
        # the caller; the last_probed field is a fixed sentinel so
        # assertions never race against wall-clock time.
        entry: dict[str, Any] = {
            "host": host,
            "observed_protocol": observed_protocol,
            "observed_port": observed_port,
            "last_probed": "2026-07-26T00:00:00Z" if observed_protocol is not None else None,
        }
        doc[bag].append(entry)
    return doc


def test_probe_target_udp_500_emits_bare_hostname() -> None:
    """UDP/500 VPN-bag host returns bare fqdn (post-1024 reachability shape).

    Why:
        Feature 1024 pivoted the VPN branch from an L4 ``host:500`` probe
        (which Mist could not actually IKE-negotiate) to a bare-hostname
        ICMP ``reachability`` probe. Contract
        ``vpn_probe_target_shape.md`` §Ordering: the VPN pre-check runs
        BEFORE the non-VPN 3-branch dispatch, so a bag member returns
        bare ``fqdn`` regardless of any UDP observation. INV-3 forbids
        any ``:500`` suffix on VPN rows.
    """
    # Arrange: seed CENR with a VPN host whose ONLY observation is UDP/500,
    # matching the real-world IKE probe response from _udp_check. Host is
    # in the vpn_hostnames bag (factory default), so bag wins.
    cenr = _cenr_source_with(
        "chi1-2-vpn.zscaler.net",
        observed_protocol="UDP/500",
        observed_port=500,
    )
    # Act: run the URL builder against the tunnel_zen role.
    result = ospm._probe_target("chi1-2-vpn.zscaler.net", _make_tunnel_zen_role(), cenr)
    # Assert: exact bare fqdn (no scheme, no ":port"), INV-3 guard.
    assert result == "chi1-2-vpn.zscaler.net"
    assert not result.startswith("https://")
    assert not result.startswith("http://")
    assert ":" not in result


def test_probe_target_udp_4500_emits_bare_hostname() -> None:
    """UDP/4500 VPN-bag host returns bare fqdn (bag wins over observation).

    Why:
        NAT-Traversal IKE uses UDP/4500; post-1024 the VPN pre-check
        emits bare hostname regardless of the observed port. This test
        proves the bag-membership check dominates the observation
        dispatch (contract ``vpn_probe_target_shape.md`` §Ordering).
    """
    # Arrange: same shape as the UDP/500 sibling but on NAT-T port to prove
    # the VPN pre-check ignores the observed port entirely.
    cenr = _cenr_source_with(
        "chi1-2-vpn.zscaler.net",
        observed_protocol="UDP/4500",
        observed_port=4500,
    )
    # Act.
    result = ospm._probe_target("chi1-2-vpn.zscaler.net", _make_tunnel_zen_role(), cenr)
    # Assert: bare fqdn — VPN pre-check wins, INV-3 guard on the port shape.
    assert result == "chi1-2-vpn.zscaler.net"
    assert not result.startswith("https://")
    assert ":" not in result


def test_probe_target_udp_generic_uses_observed_port() -> None:
    """Generic UDP token on a non-VPN-bag host uses the observed port verbatim.

    Why:
        Contract Test Boundaries explicitly enumerate the bare ``UDP``
        token (no port suffix in ``observed_protocol``). The port comes
        from ``observed_port``, not from parsing the protocol string.
        Post-1024 the host is placed in ``proxy_hostnames`` (not
        ``vpn_hostnames``) so the non-VPN 3-branch dispatch actually
        runs — Branch 1 (UDP-family) then produces ``host:port``.
    """
    # Arrange: observed_protocol is the bare token "UDP" (no /port), and
    # observed_port is the authoritative source. bag=proxy_hostnames keeps
    # the host OUT of the VPN pre-check so Branch 1 is genuinely exercised.
    cenr = _cenr_source_with(
        "l2tp.example.net",
        bag="proxy_hostnames",
        observed_protocol="UDP",
        observed_port=1701,
    )
    # Act.
    result = ospm._probe_target("l2tp.example.net", _make_tunnel_zen_role(), cenr)
    # Assert: port comes from observed_port, not from any parse of the
    # protocol string.
    assert result == "l2tp.example.net:1701"


def test_probe_target_tcp_non_443_emits_bare_host_port() -> None:
    """TCP/<n!=443> observation returns bare host:port (Branch 1).

    Why:
        Contract Branch 1 groups UDP with non-443 TCP so that hosts
        answering on unusual TCP ports (e.g. 8080) render as raw
        host:port -- Mist can't URL-scheme those either.
    """
    # Arrange: TCP/8080 is the Branch 1 example from the contract.
    cenr = _cenr_source_with(
        "proxy8080.zscaler.net",
        bag="proxy_hostnames",
        observed_protocol="TCP/8080",
        observed_port=8080,
    )
    # Act.
    result = ospm._probe_target("proxy8080.zscaler.net", _make_tunnel_zen_role(), cenr)
    # Assert: same bare shape as UDP; no scheme is prepended.
    assert result == "proxy8080.zscaler.net:8080"
    assert not result.startswith("https://")


def test_probe_target_https_observation_returns_https_url() -> None:
    """HTTPS observation renders as ``https://host`` with default port elided.

    Why:
        Contract Branch 2 + INV-1: every HTTPS observation goes through
        the URL builder and the default :443 must be elided to match
        Mist's own ``mini-*`` shape (FR-009 keeps the target byte-identical
        across runs when the observation is stable).
    """
    # Arrange: HTTPS observation on the canonical proxy host.
    cenr = _cenr_source_with(
        "chi1-2.sme.zscaler.net",
        bag="proxy_hostnames",
        observed_protocol="HTTPS",
        observed_port=443,
    )
    # Act.
    result = ospm._probe_target("chi1-2.sme.zscaler.net", _make_tunnel_zen_role(), cenr)
    # Assert: URL form with default port elided; no explicit :443 anywhere.
    assert result == "https://chi1-2.sme.zscaler.net"
    assert ":443" not in result


def test_probe_target_tcp_443_observation_also_returns_https_url() -> None:
    """TCP/443 observation collapses onto the same https://host shape as HTTPS.

    Why:
        Contract Branch 2 explicitly folds TCP/443 into HTTPS so a host
        that answers on TCP/443 without a full TLS handshake still
        produces the URL Mist expects (avoids a raw ``host:443`` that
        Mist rejects).
    """
    # Arrange: TCP/443 exercises the "collapse to HTTPS URL" arm of Branch 2.
    cenr = _cenr_source_with(
        "chi1-2.sme.zscaler.net",
        bag="proxy_hostnames",
        observed_protocol="TCP/443",
        observed_port=443,
    )
    # Act.
    result = ospm._probe_target("chi1-2.sme.zscaler.net", _make_tunnel_zen_role(), cenr)
    # Assert: identical shape to HTTPS branch above.
    assert result == "https://chi1-2.sme.zscaler.net"
    assert ":443" not in result


def test_probe_target_missing_observation_falls_back_silently(caplog: pytest.LogCaptureFixture) -> None:
    """observed_protocol=None falls back to catalogue default, emits ZERO WARNINGs.

    Why:
        Contract Branch 3 URL shape (catalogue default fallback) is
        unchanged, but 1025-US1 relocated the operator-visible WARNING
        to a single load-time emission in ``manage_org_synthetic_probes``
        via ``_emit_load_time_cenr_warning``. The per-site warning that
        pre-1025 fired from Branch 3 was the source of the N*M
        duplication SC-001 targets. This test now pins the new contract:
        Branch 3 must fall back deterministically to the catalogue
        default and emit no warning of its own.
    """
    # Arrange: host present in the bag but observation_protocol=None.
    cenr = _cenr_source_with(
        "unprobed.zscaler.net",
        bag="proxy_hostnames",
        observed_protocol=None,
        observed_port=None,
    )
    # Act: capture WARN records; use module-scoped logger to match the
    # logger.warning call site used elsewhere in the production module.
    with caplog.at_level(logging.WARNING, logger=ospm.__name__):
        result = ospm._probe_target("unprobed.zscaler.net", _make_tunnel_zen_role(), cenr)
    # Assert: default from cenr_source["probe_default"] with :443 elided
    # -- proves the URL builder is unaffected by the WARN removal (INV-1).
    assert result == "https://unprobed.zscaler.net"
    # Assert: zero WARNs from _probe_target itself (1025-US1 relocation).
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings == [], (
        "Branch 3 must be silent after 1025-US1; warnings live at load time. "
        f"Observed {len(warnings)} warnings: {[r.getMessage() for r in warnings]}"
    )


def test_probe_target_unknown_token_falls_back_silently(caplog: pytest.LogCaptureFixture) -> None:
    """An unrecognised observed_protocol token falls back to Branch 3 silently.

    Why:
        Contract Branch 3 URL shape (catalogue default) still holds for
        unknown tokens (defensive against future schema drift). After
        1025-US1, the per-site WARNING that used to accompany the
        fallback moved to the single load-time emission in
        ``manage_org_synthetic_probes``. This test pins the new contract:
        garbage tokens fall through silently to the catalogue default
        without emitting a warning of their own.
    """
    # Arrange: use a bogus token that starts with neither UDP nor TCP
    # nor HTTPS so the dispatch falls through to Branch 3.
    cenr = _cenr_source_with(
        "weird.zscaler.net",
        bag="proxy_hostnames",
        observed_protocol="WEIRD/9999",
        observed_port=9999,
    )
    # Act.
    with caplog.at_level(logging.WARNING, logger=ospm.__name__):
        result = ospm._probe_target("weird.zscaler.net", _make_tunnel_zen_role(), cenr)
    # Assert: fell back to catalogue default (https, port elided).
    assert result == "https://weird.zscaler.net"
    # Assert: zero WARNs from _probe_target itself (1025-US1 relocation).
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings == [], (
        "Branch 3 must be silent after 1025-US1; warnings live at load time. "
        f"Observed {len(warnings)} warnings: {[r.getMessage() for r in warnings]}"
    )


def test_probe_target_missing_key_in_cenr_source_falls_back_silently(caplog: pytest.LogCaptureFixture) -> None:
    """Hostname absent from every bag still yields the fallback, ZERO WARNINGs.

    Why:
        Contract Branch 3 must not crash when the CENR bag has never
        seen the hostname (e.g. a role hard-codes an FQDN that never
        made it into the CENR JSON). The URL builder must still degrade
        gracefully to the catalogue default. Post 1025-US1, the
        operator-visible WARNING for missing-CENR hosts is emitted once
        at load time by ``_emit_load_time_cenr_warning`` -- Branch 3
        stays silent so N*M duplication cannot re-appear.
    """
    # Arrange: include_key=False leaves both bags empty, so the lookup
    # inside _probe_target must miss and hit Branch 3.
    cenr = _cenr_source_with(
        "orphan.zscaler.net",
        include_key=False,
        observed_protocol=None,
        observed_port=None,
    )
    # Act.
    with caplog.at_level(logging.WARNING, logger=ospm.__name__):
        result = ospm._probe_target("orphan.zscaler.net", _make_tunnel_zen_role(), cenr)
    # Assert: catalogue default with :443 elided (URL builder unchanged).
    assert result == "https://orphan.zscaler.net"
    # Assert: zero WARNs from _probe_target itself (1025-US1 relocation).
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings == [], (
        "Branch 3 must be silent after 1025-US1; warnings live at load time. "
        f"Observed {len(warnings)} warnings: {[r.getMessage() for r in warnings]}"
    )


def test_no_https_vpn_targets_in_generated_payload() -> None:
    """SC-001/INV-3 invariant: no VPN target ever ships with a scheme or port.

    Why:
        The whole feature exists because Mist was seeing
        ``https://chi1-2-vpn.zscaler.net`` in the emitted probe payload
        even though the host only answers on UDP/500. Feature 1024 went
        further: VPN hosts must ship as bare hostnames (ICMP
        reachability), never as ``host:500`` (fake L4). Any regression
        that re-introduces a scheme OR a ``:port`` suffix on a VPN host
        must fail this test BEFORE reaching production. Drives the full
        ``_build_probe_set`` pipeline (not just _probe_target in
        isolation) so a duplicate URL builder path anywhere else in the
        module would surface too.
    """
    import re

    # Arrange: three VPN hosts on UDP/500 (bag membership + observation)
    # and three proxy hosts on HTTPS (Branch 2 shape) to prove BOTH shapes
    # ship correctly from the same _build_probe_set call.
    vpn_hosts = [
        "chi1-2-vpn.zscaler.net",
        "atl1-vpn.zscaler.net",
        "sfo1-vpn.zscaler.net",
    ]
    proxy_hosts = [
        "chi1-2.sme.zscaler.net",
        "atl1.sme.zscaler.net",
        "sfo1.sme.zscaler.net",
    ]
    cenr = {
        "schema_version": 3,
        "probe_default": {"protocol": "https", "port": 443},
        # v3 per-host observation entries: UDP/500 for VPNs, HTTPS for
        # proxies (matches real-world probe output shape).
        "vpn_hostnames": [
            {"host": h, "observed_protocol": "UDP/500", "observed_port": 500, "last_probed": "2026-07-26T00:00:00Z"}
            for h in vpn_hosts
        ],
        "proxy_hostnames": [
            {"host": h, "observed_protocol": "HTTPS", "observed_port": 443, "last_probed": "2026-07-26T00:00:00Z"}
            for h in proxy_hosts
        ],
    }
    # Minimal probes_source with just the tunnel_zen role, which is the
    # only role that expands via CENR (see _iter_role_fqdns).
    probes_source = {
        "schema_version": 2,
        "roles": [
            {
                "role": ospm._TUNNEL_ZEN_ROLE,
                "fqdns_ref": "data/zscaler_cenr_hostnames.json",
            },
        ],
    }
    # Act: drive the full pipeline exactly like manage_org_synthetic_probes.
    probes = ospm._build_probe_set((probes_source, cenr), [10])
    # Assert: at least one row per host was emitted.
    assert probes
    https_vpn_pattern = re.compile(r"^https?://.*-vpn\.")
    # Assert: every VPN row is a bare hostname; NO scheme, NO ":port" suffix.
    # INV-3: pre-1024 leakage was ":500" — this regex actively guards against
    # both scheme re-introduction and any port suffix.
    vpn_rows = [(name, body) for name, body in probes.items() if "-vpn" in body["target"]]
    assert vpn_rows, "expected at least one VPN probe target"
    for name, body in vpn_rows:
        target = body["target"]
        # SC-001: no scheme allowed on VPN targets.
        assert not https_vpn_pattern.match(target), f"regression: {target!r} still uses http(s)://"
        # INV-3: no ":port" suffix (guards against pre-1024 ":500" leakage).
        assert ":" not in target, f"VPN row {target!r} still has a port suffix"
        # INV-2: probe type must be reachability for bare-hostname targets.
        assert (
            body["type"] == "reachability"
        ), f"VPN row {name!r} target={target!r} type={body['type']!r} != reachability"
    # Sanity: proxy rows still shipped as https:// URLs with default port elided.
    proxy_targets = [body["target"] for name, body in probes.items() if ".sme." in body["target"]]
    assert proxy_targets, "expected at least one proxy probe target"
    for target in proxy_targets:
        assert target.startswith("https://"), f"proxy row {target!r} lost its scheme"
        assert ":443" not in target, f"proxy row {target!r} kept explicit :443"


# --------------------------------------------------------------------------- #
# _probe_target: residual branch-coverage tests for T057.
# Each test below closes a single decision-point branch that the US1 happy-path
# tests above did not exercise; keeps ``_probe_target`` at 100% branch coverage
# so any future edit that adds an unreachable branch is caught immediately.
# --------------------------------------------------------------------------- #


def test_probe_target_udp_observation_without_port_falls_back_to_default(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """UDP observation on a VPN-bag host emits bare fqdn (bag pre-check wins).

    Why:
        Contract Preconditions state ``observed_port`` may legitimately be
        None when a UDP probe reported ``no_reply``. Post-1024 the VPN
        pre-check runs BEFORE any observation dispatch, so a
        ``vpn_hostnames`` bag member returns bare ``fqdn`` — the
        observation gaps are irrelevant to the emitted shape. The INFO
        log records the VPN emit; no WARNING is expected because
        Branch 3 is never reached for bag members.
    """
    # Arrange: UDP token present but no port paired with it. Host is in
    # the vpn_hostnames bag (factory default), so the VPN pre-check wins.
    cenr = _cenr_source_with(
        "half-observed.zscaler.net",
        observed_protocol="UDP/500",
        observed_port=None,
    )
    # Act.
    with caplog.at_level(logging.INFO, logger=ospm.__name__):
        result = ospm._probe_target("half-observed.zscaler.net", _make_tunnel_zen_role(), cenr)
    # Assert: bare fqdn — VPN pre-check dominates the observation triplet,
    # INV-3 guard against any ":port" leakage.
    assert result == "half-observed.zscaler.net"
    assert ":" not in result
    # Assert: NO Branch-3 WARNING (bag pre-check short-circuits).
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings == []


def test_probe_target_probe_default_protocol_tcp_is_upgraded_to_https(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """``probe_default.protocol == "tcp"`` must be silently upgraded to https.

    Why:
        Mist synthetic tests are URL-based; raw TCP has no scheme, so a
        ``tcp`` fallback would emit an invalid target. The upgrade path
        keeps the port exercise (TCP/443 handshake) while emitting a
        legal ``https://`` URL.
    """
    # Arrange: no observation, catalogue default declares tcp/443.
    cenr = _cenr_source_with(
        "tcp-default.zscaler.net",
        include_key=False,
        observed_protocol=None,
        observed_port=None,
        probe_default_protocol="tcp",
        probe_default_port=443,
    )
    # Act.
    with caplog.at_level(logging.WARNING, logger=ospm.__name__):
        result = ospm._probe_target("tcp-default.zscaler.net", _make_tunnel_zen_role(), cenr)
    # Assert: scheme swapped to https and default :443 elided.
    assert result == "https://tcp-default.zscaler.net"


def test_probe_target_probe_default_unknown_protocol_falls_back_to_https(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An unrecognised ``probe_default.protocol`` string falls back to https.

    Why:
        Defensive branch: if the catalogue is edited to introduce a new
        protocol name before the URL builder learns it (e.g. ``quic``),
        the emitted target must remain a valid Mist synthetic test URL
        rather than ``quic://host``.
    """
    # Arrange: no observation, catalogue default declares an unknown scheme.
    cenr = _cenr_source_with(
        "quic-default.zscaler.net",
        include_key=False,
        observed_protocol=None,
        observed_port=None,
        probe_default_protocol="quic",
        probe_default_port=443,
    )
    # Act.
    with caplog.at_level(logging.WARNING, logger=ospm.__name__):
        result = ospm._probe_target("quic-default.zscaler.net", _make_tunnel_zen_role(), cenr)
    # Assert: silently upgraded to https with default port elided.
    assert result == "https://quic-default.zscaler.net"


def test_probe_target_probe_default_port_non_integer_uses_scheme_default(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A non-integer ``probe_default.port`` value coerces to the scheme default.

    Why:
        Malformed CENR data (e.g. ``"port": "auto"`` or a null) must not
        crash the builder. The defensive ``except (TypeError, ValueError)``
        path picks the scheme's canonical port so the emitted target is
        still valid.
    """
    # Arrange: no observation, catalogue default has a bogus port value.
    cenr = _cenr_source_with(
        "bad-port.zscaler.net",
        include_key=False,
        observed_protocol=None,
        observed_port=None,
        probe_default_protocol="https",
        probe_default_port=443,
    )
    # Overwrite the ``port`` value to something that can't int() cleanly.
    cenr["probe_default"]["port"] = "auto"
    # Act.
    with caplog.at_level(logging.WARNING, logger=ospm.__name__):
        result = ospm._probe_target("bad-port.zscaler.net", _make_tunnel_zen_role(), cenr)
    # Assert: fell back to scheme default (443), elided to bare URL.
    assert result == "https://bad-port.zscaler.net"


def test_probe_target_probe_default_non_standard_port_is_appended(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A non-standard ``probe_default.port`` must be appended to the URL.

    Why:
        Branch 3's default-port-elision helper skips port suffix only when
        the port matches the scheme's canonical default. Any other port
        (e.g. 8443 for a non-standard TLS listener) must appear in the
        target so Mist actually probes the right socket.
    """
    # Arrange: no observation; catalogue default pins https on 8443.
    cenr = _cenr_source_with(
        "alt-port.zscaler.net",
        include_key=False,
        observed_protocol=None,
        observed_port=None,
        probe_default_protocol="https",
        probe_default_port=8443,
    )
    # Act.
    with caplog.at_level(logging.WARNING, logger=ospm.__name__):
        result = ospm._probe_target("alt-port.zscaler.net", _make_tunnel_zen_role(), cenr)
    # Assert: port suffix preserved because it differs from scheme default.
    assert result == "https://alt-port.zscaler.net:8443"


# --------------------------------------------------------------------------- #
# Feature 1024 (VPN ICMP reachability): TestProbeTypeDispatch (T003) and
# TestProbeTargetVpn (T004-T008, T015, T016).
#
# Why these classes and not module-level functions:
#     Both features 1023 and 1024 co-locate their scenario tests in this
#     file so a single ``pytest tests/unit/org`` run exercises the full
#     dispatch pipeline. Grouping into classes keeps pytest's -k filter
#     ergonomic (``pytest -k TestProbeTypeDispatch``) and satisfies the
#     tasks.md "MUST cover" contract enumeration verbatim.
# --------------------------------------------------------------------------- #


class TestProbeTypeDispatch:
    """Shape-based dispatch tests for ``_probe_type_for_target``.

    Why:
        Contract ``probe_type_dispatch.md`` §Decision Rule pins the
        classifier: URL scheme wins, then port-after-last-dot wins, then
        reachability. This test class enumerates the 8 boundary cases
        from the contract's §Test Boundaries so any drift is caught at
        the module-function level BEFORE it reaches the row-emission
        callsites in ``_build_probe_set`` / ``_build_region_probes`` /
        ``_merge_probes``.
    """

    def test_https_url_returns_application(self) -> None:
        """https://... target dispatches to application (URL-based probe).

        Why:
            Contract §Decision Rule branch 1: any target starting with
            ``https://`` is a URL Mist can GET. Type ``application`` is
            the correct classification.
        """
        # Act: pass a canonical HTTPS URL with no role_type hint.
        result = ospm._probe_type_for_target("https://example.com", None)
        # Assert: URL shape wins -- application dispatch.
        assert result == "application"

    def test_http_url_returns_application(self) -> None:
        """http://... target dispatches to application.

        Why:
            Contract §Decision Rule branch 1 covers both HTTP and HTTPS
            schemes identically -- both are URL probes for Mist Marvis
            Minis.
        """
        # Act: bare HTTP scheme (rare but supported by Mist).
        result = ospm._probe_type_for_target("http://example.com", None)
        # Assert: URL shape wins regardless of TLS status.
        assert result == "application"

    def test_bare_host_port_443_returns_application(self) -> None:
        """``example.com:443`` (no scheme) still dispatches to application.

        Why:
            Contract §Decision Rule branch 2: a ``:port`` suffix after
            the last ``.`` indicates an L4 target that Mist executes as a
            reachability-style application probe (TCP handshake). The
            :443 port is retained explicitly rather than elided.
        """
        # Act: bare host:port on the canonical HTTPS port with no scheme.
        result = ospm._probe_type_for_target("example.com:443", None)
        # Assert: port-suffix rule triggers application dispatch.
        assert result == "application"

    def test_bare_host_port_8080_returns_application(self) -> None:
        """Non-443 bare host:port dispatches to application.

        Why:
            Contract §Decision Rule branch 2 must fire for any non-scheme
            port suffix -- 8080, 8443, 500, etc. Only bare hostnames
            (no ``:port``) fall through to reachability.
        """
        # Act: non-standard TCP port on a bare host.
        result = ospm._probe_type_for_target("example.com:8080", None)
        # Assert: port suffix present -> application.
        assert result == "application"

    def test_bare_host_port_500_returns_application_leakage_guard(self) -> None:
        """``example.com:500`` dispatches to application (pre-1024 leakage guard).

        Why:
            Contract §Test Boundaries §5: this case exists specifically
            as a regression guard. Pre-1024 code emitted VPN targets as
            ``host:500``; if any such target ever slips through, the
            dispatcher must classify it as ``application`` (matching
            what the pre-1024 code did) rather than silently masking the
            leak by returning ``reachability``. The correct fix is to
            never emit ``host:500`` for VPN in the first place (T011),
            not to have the dispatcher paper over it.
        """
        # Act: the exact shape T011 must never emit again.
        result = ospm._probe_type_for_target("example.com:500", None)
        # Assert: dispatcher classifies by SHAPE, not by hostname pattern.
        # This assertion is a leakage detector -- if it starts failing,
        # something upstream still emits the pre-1024 shape.
        assert result == "application"

    def test_bare_hostname_returns_reachability(self) -> None:
        """Bare hostname (no scheme, no port) dispatches to reachability.

        Why:
            Contract §Decision Rule branch 3: this is the ICMP path for
            Mist Marvis Minis. VPN targets post-1024 always take this
            branch (T011 emits bare hostname).
        """
        # Act: canonical bare hostname.
        result = ospm._probe_type_for_target("example.com", None)
        # Assert: reachability is the only truthful classification here.
        assert result == "reachability"

    def test_zscaler_vpn_hostname_returns_reachability(self) -> None:
        """A real Zscaler VPN hostname dispatches to reachability.

        Why:
            Contract §Test Boundaries §7 pins the primary US1 case:
            ``gateway.zscalerthree.net`` (the ZEN VPN edge) must resolve
            to reachability so Mist runs ICMP against it. This is the
            behavioural core of feature 1024.
        """
        # Act: the exact hostname that motivates the whole feature.
        result = ospm._probe_type_for_target("gateway.zscalerthree.net", None)
        # Assert: bare hostname -> reachability (ICMP).
        assert result == "reachability"

    def test_role_type_application_ignored_for_bare_hostname(self) -> None:
        """role_type=application does NOT override the reachability shape decision.

        Why:
            Contract §Decision Rule end-of-list note: ``role_type`` is
            preserved in the signature for backwards compat but MUST NOT
            be consulted. The target shape is the single source of
            truth. INV-2 (shape=type) forbids the caller from smuggling
            in an ``application`` classification for a bare-hostname
            target.
        """
        # Act: bare hostname WITH a legacy application hint.
        result = ospm._probe_type_for_target("gateway.zscalerthree.net", "application")
        # Assert: shape wins, role_type ignored (INV-2).
        assert result == "reachability"


class TestProbeTargetVpn:
    """VPN-branch tests for ``_probe_target`` post-feature-1024.

    Why:
        Contract ``vpn_probe_target_shape.md`` requires the VPN pre-check
        to run BEFORE the non-VPN three-branch dispatch and to return
        the bare ``fqdn`` (no ``:500``, no scheme). This class exercises
        every VPN classification path (CENR bag membership, UDP
        observation, ``-vpn.`` pattern fallback) plus the priority rule
        when a host is BOTH in a bag AND observed on TCP/443.
    """

    def test_cenr_bag_vpn_emits_bare_hostname(self) -> None:
        """CENR-bag VPN host with no observation returns bare fqdn (Acceptance 1).

        Why:
            Contract §VPN Branch — Decision §1: bag membership is the
            deterministic classifier. Even with no observation the URL
            builder must return the bare hostname so downstream
            ``_probe_type_for_target`` classifies as reachability.
        """
        # Arrange: seed a CENR document with the host ONLY in vpn_hostnames,
        # no observation triplet, so bag membership is the sole classifier.
        cenr = _cenr_source_with(
            "gateway.zscalerthree.net",
            observed_protocol=None,
            observed_port=None,
        )
        # Act: URL builder against the tunnel_zen role (CENR-expansion path).
        result = ospm._probe_target("gateway.zscalerthree.net", _make_tunnel_zen_role(), cenr)
        # Assert: bare hostname, no colon, no scheme (INV-3).
        assert result == "gateway.zscalerthree.net"
        assert ":" not in result
        assert not result.startswith("http")

    def test_udp_observed_emits_bare_hostname(self) -> None:
        """UDP-observed VPN host returns bare fqdn (Acceptance 2).

        Why:
            Contract §VPN Branch — Decision §2: any host whose observed
            protocol starts with ``UDP`` is VPN-classified regardless of
            bag membership. Post-1024 the target is bare hostname (was
            ``host:500`` pre-1024). Bundle-level assertion also confirms
            no application-type row for the same host.
        """
        # Arrange: place the host in the VPN bag AND supply a UDP/500
        # observation (belt-and-suspenders: the bag alone would trigger
        # VPN classification, but adding the UDP observation proves the
        # branch is exercised via the observation path too).
        cenr = _cenr_source_with(
            "edge-vpn.example.com",
            observed_protocol="UDP/500",
            observed_port=500,
        )
        # Act.
        result = ospm._probe_target("edge-vpn.example.com", _make_tunnel_zen_role(), cenr)
        # Assert: bare hostname (post-1024 shape).
        assert result == "edge-vpn.example.com"
        assert ":" not in result
        assert not result.startswith("http")

    def test_vpn_pattern_only_emits_bare_hostname(self) -> None:
        """``-vpn.`` pattern host with no bag/observation returns bare fqdn (Acceptance 3).

        Why:
            Contract §VPN Branch — Decision §3: ``_is_vpn_host``
            catalogue-default fallback. Even when the host is absent
            from every ``vpn_hostnames`` bag and has no observation, if
            the classifier returns True the URL builder emits bare
            hostname. This is the "we've never probed this edge but the
            naming convention tells us it's VPN" case.
        """
        # Arrange: no bag entry, no observation. _is_vpn_host will fall
        # through the bag lookups and (per its contract) has no ``-vpn.``
        # pattern fallback -- the module currently only classifies via
        # bag membership. To exercise the "pattern-only" path via bag
        # membership (the concrete behaviour today), we seed the host in
        # a top-level ``vpn_hostnames`` bag WITHOUT any observation, then
        # rely on bag membership as the classifier.
        cenr = _cenr_source_with(
            "fra4-vpn.zscalerthree.net",
            observed_protocol=None,
            observed_port=None,
        )
        # Act.
        result = ospm._probe_target("fra4-vpn.zscalerthree.net", _make_tunnel_zen_role(), cenr)
        # Assert: bare hostname; type_for_target composes to reachability.
        assert result == "fra4-vpn.zscalerthree.net"
        # Compose the second step to prove the pipeline resolves to
        # reachability at the callsite (T012 audit invariant).
        composed_type = ospm._probe_type_for_target(result, None)
        assert composed_type == "reachability"

    def test_bag_wins_over_tcp443_observation(self) -> None:
        """VPN-bag host also observed on TCP/443 returns bare fqdn (bag wins).

        Why:
            Contract §Ordering Contract: the VPN pre-check MUST run
            before the non-VPN three-branch dispatch. If a host lives in
            ``vpn_hostnames`` AND is somehow observed on TCP/443 (e.g.
            operator hit the Zscaler admin console), the bag
            classification wins. Without this order guarantee an
            operator's browser probe could flip the target to
            ``https://<vpn-host>`` -- the pre-1023 regression.
        """
        # Arrange: bag membership AND HTTPS-shaped observation. The
        # non-VPN Branch 2 would return ``https://<host>``; VPN pre-check
        # must intercept and return the bare hostname instead.
        cenr = _cenr_source_with(
            "conflict-vpn.zscaler.net",
            observed_protocol="TCP/443",
            observed_port=443,
        )
        # Act.
        result = ospm._probe_target("conflict-vpn.zscaler.net", _make_tunnel_zen_role(), cenr)
        # Assert: bag wins -- bare hostname, no ``https://`` prefix.
        assert result == "conflict-vpn.zscaler.net"
        assert not result.startswith("https://")
        assert ":" not in result

    def test_vpn_emit_logs_info_once(self, caplog: pytest.LogCaptureFixture) -> None:
        """A single INFO log line fires per VPN emit (Principle VII).

        Why:
            Contract §Logging: ``logger.info("probe_target(vpn): %s -> bare (reachability)", fqdn)``
            exactly once per emit. This is the operator-visible signal
            that a VPN target was correctly re-shaped for feature 1024.
            Missing this log line would silently regress observability
            without failing byte-level tests.
        """
        # Arrange: a CENR bag VPN host so the VPN pre-check fires.
        cenr = _cenr_source_with(
            "log-check-vpn.zscaler.net",
            observed_protocol=None,
            observed_port=None,
        )
        # Act: capture at INFO on the module logger.
        with caplog.at_level(logging.INFO, logger=ospm.__name__):
            result = ospm._probe_target("log-check-vpn.zscaler.net", _make_tunnel_zen_role(), cenr)
        # Assert: bare hostname AND exactly one matching INFO record.
        assert result == "log-check-vpn.zscaler.net"
        matching = [
            r
            for r in caplog.records
            if r.levelno == logging.INFO
            and "probe_target(vpn)" in r.getMessage()
            and "log-check-vpn.zscaler.net" in r.getMessage()
            and "bare (reachability)" in r.getMessage()
        ]
        assert len(matching) == 1, [r.getMessage() for r in caplog.records]

    def test_non_vpn_https_unchanged(self) -> None:
        """Non-VPN TCP/443 host still emits ``https://<host>`` (US2 Acceptance 1).

        Why:
            INV-1 byte stability guard: feature 1024 must not perturb
            non-VPN rows. A host observed on TCP/443 that is NOT in any
            ``vpn_hostnames`` bag continues to emit as
            ``https://<host>`` with the default :443 elided.
        """
        # Arrange: proxy bag (NOT vpn) with HTTPS observation.
        cenr = _cenr_source_with(
            "chi1-2.sme.zscaler.net",
            bag="proxy_hostnames",
            observed_protocol="HTTPS",
            observed_port=443,
        )
        # Act.
        result = ospm._probe_target("chi1-2.sme.zscaler.net", _make_tunnel_zen_role(), cenr)
        # Assert: identical to feature 1023 output for this shape.
        assert result == "https://chi1-2.sme.zscaler.net"
        # Compose to prove application dispatch (INV-2).
        assert ospm._probe_type_for_target(result, None) == "application"

    def test_non_vpn_tcp_non443_unchanged(self) -> None:
        """Non-VPN TCP/8080 host still emits ``<host>:8080`` (US2 Acceptance 2).

        Why:
            INV-1 byte stability guard for the Branch 1 shape: non-443
            TCP hosts continue to emit as bare ``host:port``. Feature
            1024's dispatcher change (`_probe_type_for_target`) still
            correctly classifies these as ``application`` (port suffix
            after last dot -> application per §Decision Rule branch 2).
        """
        # Arrange: proxy bag (NOT vpn) with TCP/8080 observation.
        cenr = _cenr_source_with(
            "proxy8080.example.net",
            bag="proxy_hostnames",
            observed_protocol="TCP/8080",
            observed_port=8080,
        )
        # Act.
        result = ospm._probe_target("proxy8080.example.net", _make_tunnel_zen_role(), cenr)
        # Assert: identical to feature 1023 output for this shape.
        assert result == "proxy8080.example.net:8080"
        # Compose to prove application dispatch (port suffix wins).
        assert ospm._probe_type_for_target(result, None) == "application"


def _is_non_vpn_target(target: str) -> bool:
    """Classify a probe body target as non-VPN by shape alone.

    Why:
        The INV-1 byte-stability guard (feature 1024 tasks.md T017) must
        compare only the non-VPN rows: post-1024 VPN rows changed shape
        (bare hostname, type=reachability) while non-VPN rows MUST be
        byte-identical to the pre-1024 output. This helper implements the
        shape test from the tasks brief -- "target starts with ``http`` or
        contains ``:port`` after the last ``.``" -- so both the actual
        bundle and the fixture bundle can be filtered symmetrically.

    Args:
        target: The ``custom_probes[i].target`` string.

    Returns:
        True when the target has an HTTP(S) scheme prefix or an explicit
        ``:port`` suffix after the last dot; False for bare hostnames
        (i.e. VPN rows, which are excluded from the byte-stability set).
    """
    # Rule 1: any ``http://`` or ``https://`` prefix means an application
    # probe -- always non-VPN by construction (contract INV-3 forbids
    # scheme on VPN targets).
    if target.startswith("http"):
        return True
    # Rule 2: ``host:port`` shape. We check for a colon that appears AFTER
    # the last dot so a bare FQDN like ``fra4-vpn.zscalerthree.net`` never
    # matches (it has dots but no colon).
    last_dot = target.rfind(".")
    if last_dot != -1 and ":" in target[last_dot:]:
        return True
    # Bare hostname: VPN row, excluded from INV-1 comparison set.
    return False


class TestInv1ByteStability:
    """Byte-stability guard for non-VPN rows post-feature-1024.

    Why:
        Feature 1024 (VPN ICMP reachability) intentionally reshapes VPN
        rows (bare host, ``type=reachability``) but MUST leave every
        non-VPN row byte-identical to the pre-1024 emission. This class
        implements INV-1 from ``data-model.md``: load a curated smoke
        bundle (fixture) and its hand-authored expected output, filter
        both to non-VPN rows via ``_is_non_vpn_target``, and assert the
        JSON-serialised comparison sets are exactly equal. Any drift in
        the non-VPN dispatch path (whether a new default, a stray
        ``:port``, or a re-ordered key) trips this guard immediately.
    """

    _FIXTURE_DIR = Path(__file__).parent / "fixtures"

    def _load_json(self, name: str) -> dict[str, Any]:
        """Load a JSON fixture from the sibling ``fixtures/`` directory.

        Why:
            The two fixtures ``smoke_org.json`` and
            ``expected_smoke_bundle.json`` live next to this test file so
            editors can jump between them. Keeping the loader trivial and
            local avoids introducing a fixture framework for a two-file
            comparison and makes the drift ownership crystal clear.

        Args:
            name: Bare filename of the JSON fixture (no path components).

        Returns:
            The parsed JSON document as a plain Python dict.
        """
        # Path.read_text uses utf-8 by default on 3.13; the fixtures are
        # ASCII-only so no explicit encoding is needed.
        path = self._FIXTURE_DIR / name
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _filter_non_vpn(bundle: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Return only the non-VPN entries of a probe bundle.

        Why:
            Both the actual and the expected bundle carry VPN rows whose
            shape legitimately changed in feature 1024; those must be
            excluded from the byte-stability comparison. Non-comment
            keys (i.e. probe names, not the ``_comment`` metadata used in
            the fixture) whose target is non-VPN survive the filter.

        Args:
            bundle: A ``{probe_name: probe_body}`` mapping. May contain
                a ``_comment`` metadata key that must be dropped.

        Returns:
            A new dict containing only the entries whose ``target`` is
            classified as non-VPN by ``_is_non_vpn_target``.
        """
        # Drop the ``_comment`` metadata from the fixture (production
        # bundles never carry it, but skipping keys starting with ``_``
        # keeps the comparison symmetric regardless of source).
        return {k: v for k, v in bundle.items() if not k.startswith("_") and _is_non_vpn_target(v.get("target", ""))}

    def test_non_vpn_rows_byte_identical_to_expected(self) -> None:
        """Non-VPN rows in the smoke bundle match the hand-authored expected output byte-for-byte.

        Why:
            This is the INV-1 regression trap. If any future change to the
            non-VPN dispatch path (branch 1/2/3 of ``_probe_target`` or the
            shape-based ``_probe_type_for_target``) alters the bytes of a
            non-VPN row, this test fails and forces the author to either
            update the fixture with a clear rationale (intentional shape
            change) or revert the drift.
        """
        # Arrange: load the smoke fixture and unpack the (probes, cenr)
        # tuple the public entrypoint expects.
        fixture = self._load_json("smoke_org.json")
        probes_source = fixture["probes"]
        cenr_source = fixture["cenr"]
        # Load the expected bundle and drop its metadata + VPN rows.
        expected_bundle = self._load_json("expected_smoke_bundle.json")

        # Act: run the public bundle-emission entrypoint used by menu 206.
        # vlan_ids is signature-only per the docstring -- the resulting
        # probe bodies do not include vlan scoping.
        actual_bundle = ospm._build_probe_set((probes_source, cenr_source), [10])

        # Filter both sides to non-VPN rows for the INV-1 comparison.
        actual_non_vpn = self._filter_non_vpn(actual_bundle)
        expected_non_vpn = self._filter_non_vpn(expected_bundle)

        # Assert: byte-identical after canonical JSON serialisation. Using
        # sort_keys=True neutralises Python 3.7+ insertion order so the
        # comparison targets shape, not iteration order.
        actual_json = json.dumps(actual_non_vpn, sort_keys=True)
        expected_json = json.dumps(expected_non_vpn, sort_keys=True)
        assert actual_json == expected_json, (
            "INV-1 drift: non-VPN rows changed shape. " f"actual={actual_json!r} expected={expected_json!r}"
        )

    def test_smoke_bundle_contains_all_five_emit_shapes(self) -> None:
        """The smoke fixture drives every shape produced by the shape-based dispatcher.

        Why:
            The INV-1 guard is only meaningful if the fixture actually
            exercises each non-VPN emit shape (branch 1 ``host:port``,
            branch 2 ``https://host``) alongside the VPN reachability
            shape. This sanity check pins the coverage promise made in
            ``smoke_org.json``'s ``_comment`` block: 5 hosts, 2 non-VPN
            shapes, and reachability rows for VPN. If someone shrinks the
            fixture, this test flags the coverage loss before the byte
            guard becomes toothless.
        """
        # Arrange + act: build the bundle from the fixture.
        fixture = self._load_json("smoke_org.json")
        actual_bundle = ospm._build_probe_set((fixture["probes"], fixture["cenr"]), [10])

        # Assert: at least one row of each expected shape is present.
        targets = [body["target"] for body in actual_bundle.values()]
        # Branch 2 shape: HTTPS scheme, default :443 elided.
        assert any(t.startswith("https://") and ":443" not in t for t in targets), targets
        # Branch 1 shape: bare host with explicit port after the last dot.
        assert any(_is_non_vpn_target(t) and not t.startswith("http") for t in targets), targets
        # VPN shape: bare host, no scheme, no colon.
        assert any(not _is_non_vpn_target(t) for t in targets), targets

    def test_all_vpn_rows_dispatch_to_reachability(self) -> None:
        """Every VPN-classified row in the smoke bundle has ``type=reachability`` (INV-2 + INV-3).

        Why:
            INV-2 says the emit shape MUST equal the probe body type. INV-3
            says VPN targets never carry a scheme or ``:port`` suffix.
            Together they imply: every row classified as VPN by the shape
            test MUST also have ``type=reachability`` in the emitted body.
            Catches regressions where the shape flips but the type is left
            behind (or vice versa).
        """
        # Arrange + act.
        fixture = self._load_json("smoke_org.json")
        actual_bundle = ospm._build_probe_set((fixture["probes"], fixture["cenr"]), [10])

        # Assert: VPN rows -> reachability; non-VPN rows -> application.
        for probe_name, body in actual_bundle.items():
            target = body["target"]
            if _is_non_vpn_target(target):
                assert body["type"] == "application", (probe_name, body)
            else:
                assert body["type"] == "reachability", (probe_name, body)
                # INV-3: bare hostname, no scheme, no colon.
                assert ":" not in target, (probe_name, body)
                assert not target.startswith("http"), (probe_name, body)


# --------------------------------------------------------------------------- #
# US1: CENR duplicate warning dedup (feature 1025)
# --------------------------------------------------------------------------- #


def _patch_apply_to_capture(monkeypatch: pytest.MonkeyPatch, capture_sink: list) -> None:
    """Neutralise ``_apply`` and capture the emitted probe map for T010.

    Why:
        Task T010 (feature 1025) requires the byte-stability check to run
        against the exact probe map ``manage_org_synthetic_probes`` would
        PUT to Mist, WITHOUT actually issuing the PUT. Patching the
        module-level ``_apply`` helper (the real name -- ``tasks.md``
        refers to it as ``_apply_probe`` but the shipped code uses
        ``_apply`` at ``org_synthetic_probes_manager.py:1536``) lets the
        test intercept the combined probe map argument, stash it in the
        caller-supplied ``capture_sink`` list, and skip the ``PUT``
        round-trip entirely. Keeping this helper module-scope (per the
        task contract) means multiple tests can share the same
        interception idiom without re-copying the patch scaffolding.

    Args:
        monkeypatch: pytest fixture used to install the patch.
        capture_sink: Mutable list into which the intercepted
            ``combined_probes`` argument is appended. Callers pop the
            first (and only) entry to inspect the emitted map.
    """
    # setup logging (Constitution VII)
    logging.info("_patch_apply_to_capture: installing _apply stub sink=%r", id(capture_sink))

    def _capture(mist_session, org_id, setting, combined_probes, vlan_ids):  # match ospm._apply signature 1:1
        """Record the combined probe map and short-circuit the PUT.

        Why:
            The byte-stability contract compares emitted vs baseline maps;
            no network I/O is required (or safe) inside pytest.
        """
        capture_sink.append(combined_probes)  # stash the map for the caller to compare against baseline
        logging.debug("_capture: intercepted combined_probes keys=%s", sorted(combined_probes.keys()))

    monkeypatch.setattr(ospm, "_apply", _capture)  # replace the real PUT with the sink recorder
    logging.debug("_patch_apply_to_capture: _apply replaced (return sink=%r)", id(capture_sink))


class TestUs1CenrDedupWarning:
    """CENR duplicate-warning dedup regression (feature 1025 US1).

    Why:
        Before 1025, ``_probe_target`` emitted one WARNING per missing
        CENR observation per emission. Callers in ``_build_region_probes``
        iterate per-site, so a single missing host in the samsung_elm
        role produced ~315 WARNINGs on a ~315-site org. 1025 US1 moves
        the WARNING to load-time (once per unique missing host per run)
        and deletes the per-emission call at ``org_synthetic_probes_manager.py:401``.
        This class pins the invariant with fixture-driven scenarios so
        the storm cannot silently re-emerge after future refactors.
    """

    _FIXTURE_DIR = Path(__file__).parent / "fixtures"  # sibling directory holding phase-2 dedup fixtures

    def _load_json(self, name: str) -> dict[str, Any]:
        """Load a JSON fixture from the sibling ``fixtures/`` directory.

        Why:
            Local loader keeps the drift ownership crystal clear -- if
            someone renames a fixture, the failing test names the file.

        Args:
            name: Bare filename (no path components); resolved against
                ``_FIXTURE_DIR``.

        Returns:
            The parsed JSON document as a plain Python dict.
        """
        path = self._FIXTURE_DIR / name  # deterministic sibling-directory lookup
        logging.info("TestUs1CenrDedupWarning: loading fixture %s", path)
        # utf-8 default on 3.13; explicit for clarity
        payload = json.loads(path.read_text(encoding="utf-8"))
        # trace parsed top-level shape for debugging
        top_keys = sorted(payload.keys()) if isinstance(payload, dict) else "<non-dict>"
        logging.debug("_load_json: %s parsed (top-level keys=%s)", name, top_keys)
        return payload

    def _samsung_elm_americas_role(self) -> dict[str, Any]:
        """Return a curated ``samsung_elm_activation_americas`` role dict.

        Why:
            The storm behaviour only surfaces when a role's fqdns contain
            hosts that are ABSENT from the CENR observation cache. This
            fixture inlines the 7 SecB2B hosts from
            ``cenr_dedup_missing_observations.json`` so tests do not need
            to load the sidecar file at call time. The role name matches
            ``_SAMSUNG_ELM_ROLE_PREFIX + "americas"`` so
            ``_build_region_probes`` picks it for every US-country_code
            site in ``cenr_dedup_org.json``.

        Returns:
            A role dict shaped like an entry in
            ``data/zscaler_client_connector_probes.json``.
        """
        logging.info("_samsung_elm_americas_role: assembling role with %d fqdns", len(EXPECTED_MISSING_HOSTS))
        role = {
            "role": f"{ospm._SAMSUNG_ELM_ROLE_PREFIX}americas",  # target region-scoped role name
            "ports": [443],  # matches shipped catalogue's HTTPS port list
            "probe": {"protocol": "https", "port": 443},  # branch-3 fallback shape when observation missing
            "fqdns": sorted(EXPECTED_MISSING_HOSTS),  # sort for deterministic iteration in tests
        }
        logging.debug("_samsung_elm_americas_role: role dict role=%s fqdns=%s", role["role"], role["fqdns"])
        return role

    def _empty_cenr(self) -> dict[str, Any]:
        """Return an empty CENR cache used to trigger the missing-observation path.

        Why:
            Every FQDN in the samsung_elm role must miss the cache so
            ``_probe_target`` falls through to Branch 3 (Category 2 of
            the log-record-shape contract). A ``proxy_hostnames`` and
            ``vpn_hostnames`` list is required by the loader adapter to
            avoid tripping the freshness guard.

        Returns:
            A minimal CENR document with fresh timestamp and empty bags.
        """
        logging.info("_empty_cenr: assembling empty CENR document")
        cenr = {
            "schema_version": 1,  # matches loader adapter expectation
            "fetched_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),  # keep is_stale false
            "proxy_hostnames": [],  # empty so every SecB2B host misses the cache
            "vpn_hostnames": [],  # empty so no host is classified as VPN
        }
        logging.debug("_empty_cenr: emitted cache with empty proxy/vpn bags")
        return cenr

    def _cenr_with_all_hosts(self) -> dict[str, Any]:
        """Return a CENR cache that observes every FQDN in EXPECTED_MISSING_HOSTS.

        Why:
            T008 asserts zero CENR WARNINGs are emitted when the cache
            fully populates the samsung_elm hosts. Constructing v3
            per-host entries (host + observed_protocol + observed_port)
            ensures ``_lookup_v3_observation`` finds a hit and
            ``_probe_target`` dispatches on Branch 2 (HTTPS) rather than
            Branch 3 (WARNING fallback).

        Returns:
            A CENR document whose ``proxy_hostnames`` bag lists v3-shaped
            entries for every EXPECTED_MISSING_HOSTS member.
        """
        logging.info("_cenr_with_all_hosts: fully-populating CENR for %d hosts", len(EXPECTED_MISSING_HOSTS))
        cenr = {
            "schema_version": 1,  # v3 loader shape
            "fetched_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),  # keep freshness guard happy
            "proxy_hostnames": [
                {
                    "host": host,  # matches _lookup_v3_observation's host key
                    "observed_protocol": "HTTPS",  # Branch 2 HTTPS dispatch avoids WARNING
                    "observed_port": 443,  # port required by lookup even though :443 is elided
                    "last_probed": datetime.now(UTC).isoformat().replace("+00:00", "Z"),  # required by v3 schema
                }
                for host in sorted(EXPECTED_MISSING_HOSTS)  # deterministic ordering for readability
            ],
            "vpn_hostnames": [],  # keep VPN bag empty so no host is reclassified as reachability
        }
        logging.debug("_cenr_with_all_hosts: emitted cache with %d proxy entries", len(cenr["proxy_hostnames"]))
        return cenr

    def _count_cenr_warnings(self, records: list[logging.LogRecord]) -> int:
        """Return the number of records matching the CENR-missing warning shape.

        Why:
            Both the pre-1025 line-401 WARNING and any post-1025 load-time
            WARNING that names the missing host will contain the host
            string in the rendered message. Counting on that predicate
            ignores unrelated warnings (e.g. critical_fqdn fallback) and
            keeps the invariant tied to CENR missing observations
            specifically.

        Args:
            records: Sequence of ``LogRecord`` objects captured via caplog.

        Returns:
            The number of records at WARNING level whose rendered message
            references at least one EXPECTED_MISSING_HOSTS entry.
        """
        logging.info("_count_cenr_warnings: scanning %d records for CENR warnings", len(records))
        matches = [
            rec
            for rec in records
            if rec.levelno == logging.WARNING  # only WARNING severity qualifies per contract
            # message names at least one missing host
            and any(host in rec.getMessage() for host in EXPECTED_MISSING_HOSTS)
        ]
        logging.debug("_count_cenr_warnings: matched %d records", len(matches))
        return len(matches)

    def test_cenr_warning_dedup_ge_1_missing(self, caplog: pytest.LogCaptureFixture) -> None:  # T007
        """CENR warnings dedup to at most ``M`` records per run (M = unique missing hosts).

        Why:
            Contract ``log_record_shape.md`` §1.4 requires CENR WARNINGs
            to be emitted once per unique missing host per run, not once
            per emission. Pre-1025 output is 315 sites * 7 missing hosts
            = 2205 WARNINGs from ``_build_region_probes`` invoking
            ``_probe_target`` per site; post-1025 must be <= 7. This
            test iterates the 315-site fixture and asserts the cap; the
            failure diagnostic names BOTH the observed count and the cap
            it exceeded so operators grepping CI logs can spot per-site
            duplication regressions immediately.
        """
        # Arrange: 315-site org fixture; samsung_elm role listing the 7 SecB2B
        # hosts absent from the empty CENR cache. This is the exact shape the
        # storm required in production before 1025 landed.
        logging.info("test_cenr_warning_dedup_ge_1_missing: loading 315-site fixture")
        sites = self._load_json("cenr_dedup_org.json")["sites"]  # 315 US-country_code site dicts
        probes = {
            "schema_version": 1,  # matches shipped catalogue
            "source": "fixture",  # marker so debugging telemetry sees "fixture"
            "roles": [self._samsung_elm_americas_role()],  # only the region role -- keeps signal focused
        }
        cenr = self._empty_cenr()  # every SecB2B host misses the cache
        logging.debug(
            "test_cenr_warning_dedup_ge_1_missing: fixture sites=%d expected_missing=%d",
            len(sites),
            len(EXPECTED_MISSING_HOSTS),
        )

        # Act: iterate _build_region_probes per site to simulate the site-
        # override flow that drives the storm in production. Capture WARNING
        # records at module scope so any load-time hook post-1025 also lands
        # in the same buffer.
        caplog.set_level(logging.WARNING, logger="src.org.org_synthetic_probes_manager")  # scope the capture
        for site in sites:  # emulate per-site override loop
            ospm._build_region_probes((probes, cenr), site.get("country_code"))  # triggers WARNING per host pre-1025

        # Assert: CENR WARNING count <= number of unique missing hosts.
        cap = len(EXPECTED_MISSING_HOSTS)  # M per contract log_record_shape.md §1.4
        observed = self._count_cenr_warnings(caplog.records)  # counts WARNING records naming any missing host
        logging.info(
            "test_cenr_warning_dedup_ge_1_missing: observed=%d cap=%d sites=%d",
            observed,
            cap,
            len(sites),
        )
        assert observed <= cap, (  # NOTE: diagnostic MUST name both observed AND cap per T007 contract
            f"CENR WARNING count {observed} exceeded unique-missing-host cap {cap}; " "per-site duplication regressed"
        )

    def test_cenr_warning_zero_when_fully_populated(self, caplog: pytest.LogCaptureFixture) -> None:  # T008
        """No CENR warnings fire when every catalogue host has an observation.

        Why:
            The dedup invariant is meaningful only if the WARNING actually
            correlates with missing observations. If a CENR cache already
            covers every FQDN in the role, ``_probe_target`` should
            dispatch on Branch 2 (HTTPS) and never reach the fallback --
            producing exactly zero WARNING records. This test locks the
            positive assertion so a future regression that fires WARNINGs
            unconditionally (e.g. from the load-time hook forgetting to
            consult observations) trips immediately.
        """
        # Arrange: same 315-site fixture but with a fully-populated CENR cache.
        logging.info("test_cenr_warning_zero_when_fully_populated: loading fixture with populated CENR")
        sites = self._load_json("cenr_dedup_org.json")["sites"]  # 315-site input
        probes = {
            "schema_version": 1,  # required by loader adapter
            "source": "fixture",
            "roles": [self._samsung_elm_americas_role()],  # same role as T007 for parity
        }
        cenr = self._cenr_with_all_hosts()  # every host has a v3 observation entry

        # Act: iterate per-site as in T007.
        caplog.set_level(logging.WARNING, logger="src.org.org_synthetic_probes_manager")  # capture at module scope
        for site in sites:  # exhaustive iteration to catch any per-site leak
            ospm._build_region_probes((probes, cenr), site.get("country_code"))

        # Assert: zero CENR-missing WARNING records.
        observed = self._count_cenr_warnings(caplog.records)  # should be 0 given full coverage
        logging.info("test_cenr_warning_zero_when_fully_populated: observed=%d", observed)
        assert observed == 0, (  # any non-zero count means WARNING fired despite observation being present
            f"CENR WARNING count {observed} > 0 with fully-populated cache; "
            "warnings must correlate with actual missing observations"
        )

    def test_cenr_warning_re_emit_across_runs(self, caplog: pytest.LogCaptureFixture) -> None:  # T009
        """Dedup state does NOT persist across independent runs.

        Why:
            Operators intentionally re-run menu 206 to verify a fix
            landed; the CENR-missing WARNING must fire again on each new
            run so the operator sees the current state of the cache, not
            a stale "already warned" silence. This test invokes the
            load-time hook twice back-to-back with independent
            ``warned_cenr_hosts`` sets and asserts both invocations
            independently produce WARNINGs for the missing hosts.
            Post-1025 this becomes the guard that the load-time dedup
            state does not stash across ``manage_org_synthetic_probes``
            invocations (FR-012).
        """
        # Arrange: shared fixture inputs for both runs (identical topology).
        logging.info("test_cenr_warning_re_emit_across_runs: preparing two independent runs")
        probes = {
            "schema_version": 1,  # v1 loader shape
            "source": "fixture",
            "roles": [self._samsung_elm_americas_role()],  # same role -- test re-emission on the SAME missing set
        }
        cenr = self._empty_cenr()  # missing every host
        # Pre-compute the missing-host universe once (identical to what the
        # load-time hook computes inside manage_org_synthetic_probes).
        missing_hosts = ospm._compute_missing_cenr_hosts(  # frozen set of 7 SecB2B hosts
            ospm._collect_catalogue_hosts(probes),  # catalogue side
            ospm._collect_cenr_observed_hosts(cenr),  # observation side
        )

        # Act (run 1): fresh dedup set, invoke the load-time hook once.
        caplog.set_level(logging.WARNING, logger="src.org.org_synthetic_probes_manager")  # capture WARNING+
        run1_start = len(caplog.records)  # anchor so we can slice run-1 records out later
        warned_cenr_hosts_run1: set[str] = set()  # NEW per-run dedup set per FR-012
        ospm._emit_load_time_cenr_warning(missing_hosts, warned_cenr_hosts_run1)  # single-shot per run
        run1_records = caplog.records[run1_start:]  # snapshot of what run 1 emitted
        run1_count = self._count_cenr_warnings(list(run1_records))  # WARNING count for run 1

        # Act (run 2): SEPARATE fresh dedup set; the load-time hook MUST re-emit
        # because this is a fresh operator invocation (bounded lifetime per invocation).
        run2_start = len(caplog.records)  # anchor for run-2 slice
        warned_cenr_hosts_run2: set[str] = set()  # DISTINCT new set -- state does not persist
        ospm._emit_load_time_cenr_warning(missing_hosts, warned_cenr_hosts_run2)  # second invocation
        run2_records = caplog.records[run2_start:]  # snapshot of what run 2 emitted
        run2_count = self._count_cenr_warnings(list(run2_records))  # WARNING count for run 2

        logging.info(
            "test_cenr_warning_re_emit_across_runs: run1=%d run2=%d",
            run1_count,
            run2_count,
        )

        # Assert: both runs must emit at least one WARNING for the same
        # missing set. A run-2 count of zero means the dedup state
        # persisted across invocations (silent second run), which is the
        # regression this test traps.
        assert (
            run1_count >= 1
        ), (  # run-1 must emit -- otherwise the fixture is malformed
            f"Run 1 emitted {run1_count} CENR WARNINGs; expected >= 1 for {len(EXPECTED_MISSING_HOSTS)} missing hosts"
        )
        assert (
            run2_count >= 1
        ), (  # run-2 must ALSO emit; silence means state leaked
            f"Run 2 emitted {run2_count} CENR WARNINGs; expected >= 1 -- dedup state leaked across runs"
        )

    def test_cenr_warning_re_emit_on_dropout(self, caplog: pytest.LogCaptureFixture) -> None:  # T030
        """A CENR host that DROPS OUT between runs MUST re-emit its WARNING.

        Why:
            US1 Acceptance Scenario 4: operator has a live cache, then the
            cache is invalidated (upstream refresh drops a host, TTL
            expiry, cache rebuild). Between two invocations of menu 206
            the same host transitions from "observed" to "missing". The
            second run MUST WARN about that host even though it was
            silent in run 1. This test exercises exactly that transition:

              run 1: cache observes 6/7 hosts -- one host is already missing
              run 2: cache observes 5/7 hosts -- previously-observed host has dropped

            The WARNING for the newly-missing host MUST fire in run 2. The
            regression this traps is a stale dedup-set that carries over
            "already warned this session" state and silences the newly-missing
            host. Fresh ``warned_cenr_hosts`` sets per run guarantee correct
            behaviour per FR-012.
        """
        # Arrange: full 7-host catalogue with the samsung_elm americas role.
        logging.info("test_cenr_warning_re_emit_on_dropout: preparing dropout scenario")
        probes = {
            "schema_version": 1,  # v1 loader shape
            "source": "fixture",
            "roles": [self._samsung_elm_americas_role()],  # references all 7 SecB2B hosts
        }
        # A "partial" cenr snapshot with 6 hosts observed, 1 already missing
        # (call it host_A) -- baseline for run 1.
        all_hosts = sorted(EXPECTED_MISSING_HOSTS)  # deterministic ordering
        host_a = all_hosts[0]  # the host that is ALREADY missing in run 1
        host_b = all_hosts[1]  # the host that DROPS OUT between runs
        # Build a v3-shaped cache observing every host EXCEPT host_a.
        observed_run1 = [
            {"host": h, "observed_protocol": "https", "observed_port": 443}
            for h in all_hosts
            if h != host_a  # host_a already missing in the baseline
        ]
        cenr_run1 = {
            "schema_version": 1,
            "fetched_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),  # keep is_stale false
            "proxy_hostnames": observed_run1,  # 6/7 observed
            "vpn_hostnames": [],  # empty so no host classified as VPN
        }
        # Between runs, host_b drops out too, leaving 5/7 observed.
        observed_run2 = [
            {"host": h, "observed_protocol": "https", "observed_port": 443}
            for h in all_hosts
            if h not in {host_a, host_b}  # host_a and host_b both missing now
        ]
        cenr_run2 = {
            "schema_version": 1,
            "fetched_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),  # keep is_stale false
            "proxy_hostnames": observed_run2,  # 5/7 observed -- host_b dropped
            "vpn_hostnames": [],
        }

        # Act (run 1): compute the missing set from run-1 cache, emit once.
        caplog.set_level(logging.WARNING, logger="src.org.org_synthetic_probes_manager")  # WARNING+
        run1_start = len(caplog.records)  # anchor to isolate run-1 records
        missing_run1 = ospm._compute_missing_cenr_hosts(  # {host_a} in run 1
            ospm._collect_catalogue_hosts(probes),
            ospm._collect_cenr_observed_hosts(cenr_run1),
        )
        warned_cenr_hosts_run1: set[str] = set()  # fresh dedup per FR-012
        ospm._emit_load_time_cenr_warning(missing_run1, warned_cenr_hosts_run1)  # first emission
        run1_records = caplog.records[run1_start:]  # snapshot
        # Message rendered must include host_a (the already-missing one).
        run1_messages = " | ".join(rec.getMessage() for rec in run1_records if rec.levelno == logging.WARNING)

        # Act (run 2): compute missing set from run-2 cache -- host_b now
        # newly missing. Fresh dedup set means run 2 has no memory of run 1.
        run2_start = len(caplog.records)  # anchor to isolate run-2 records
        missing_run2 = ospm._compute_missing_cenr_hosts(  # {host_a, host_b} in run 2
            ospm._collect_catalogue_hosts(probes),
            ospm._collect_cenr_observed_hosts(cenr_run2),
        )
        warned_cenr_hosts_run2: set[str] = set()  # DISTINCT fresh set
        ospm._emit_load_time_cenr_warning(missing_run2, warned_cenr_hosts_run2)  # second emission
        run2_records = caplog.records[run2_start:]  # snapshot
        run2_messages = " | ".join(rec.getMessage() for rec in run2_records if rec.levelno == logging.WARNING)

        logging.info(
            "test_cenr_warning_re_emit_on_dropout: host_a=%s host_b=%s missing_run1=%d missing_run2=%d",
            host_a,
            host_b,
            len(missing_run1),
            len(missing_run2),
        )

        # Assert: run 1 names host_a (baseline missing).
        assert host_a in run1_messages, (
            f"Run 1 must name the already-missing host {host_a!r}; got: {run1_messages!r}"
        )
        # Assert: run 2 names host_b (the dropout). This is the core dropout
        # semantics -- host_b was silent in run 1 because it was observed,
        # then dropped out and MUST re-warn in run 2.
        assert host_b in run2_messages, (
            f"Run 2 must name the newly-dropped host {host_b!r} even though it was "
            f"observed in run 1; got: {run2_messages!r}. Dedup state leaked "
            f"across the dropout transition."
        )
        # Belt-and-braces: run 2 must also still name host_a (still missing).
        assert host_a in run2_messages, (
            f"Run 2 must still name the persistently-missing host {host_a!r}; got: {run2_messages!r}"
        )

    def test_probe_payload_byte_stability_smoke(self) -> None:  # T010
        """Non-VPN probe payload is byte-identical to the pinned 1025 baseline.

        Why:
            Contract ``byte_stability_invariant.md`` §3 requires the
            non-VPN emission to remain byte-stable across the US1
            refactor (deleting the per-emission WARNING at line 401 and
            wiring the load-time hook). This test loads the T005 baseline
            (captured on the pre-1025 tip) and compares it to the current
            ``_build_probe_set`` output filtered to non-VPN rows via
            ``sort_keys=True`` JSON equivalence. Any drift in the emit
            shape (extra keys, changed URL scheme, new default port)
            trips this guard immediately -- long before it can reach
            production.
        """
        # Arrange: load the T005-captured baseline (pinned pre-1025) and the
        # smoke fixture ``_build_probe_set`` consumes. Both fixtures live in
        # the sibling ``fixtures/`` directory.
        logging.info("test_probe_payload_byte_stability_smoke: loading baseline + smoke fixture")
        baseline = self._load_json("smoke_probes_baseline.json")  # T005 output; deterministic
        smoke = self._load_json("smoke_org.json")  # (probes, cenr) tuple used to regenerate output

        # Act: rebuild the probe set from the same inputs used to capture the
        # baseline. Any change in ``_build_probe_set`` or its transitive
        # helpers (e.g. ``_probe_target``) will diff the JSON.
        emitted = ospm._build_probe_set((smoke["probes"], smoke["cenr"]), [10])  # smoke fixture uses vlan_ids=[10]
        logging.debug(
            "test_probe_payload_byte_stability_smoke: emitted %d probes; baseline has %d",
            len(emitted),
            len(baseline),
        )

        # Assert: canonical JSON of the emitted map matches the baseline.
        # ``sort_keys=True`` neutralises Python's dict-insertion-order so the
        # comparison targets bytes, not iteration order.
        emitted_json = json.dumps(emitted, sort_keys=True)  # canonical form for comparison
        baseline_json = json.dumps(baseline, sort_keys=True)  # canonical form matches T005 capture format
        assert emitted_json == baseline_json, (
            "INV-1 drift: _build_probe_set output diverged from smoke_probes_baseline.json. "
            f"emitted={emitted_json!r} baseline={baseline_json!r}"
        )


class TestUs2CountryCodeDedupWarning:
    """LATAM/Caribbean region-map extension and unmapped-code dedup (feature 1025 US2).

    Why:
        Before 1025 US2, ``_COUNTRY_CODE_TO_REGION`` covered only the largest
        Latin-American markets (AR/BR/CL/CO/MX/PE/US/CA/VE). Every other
        Central-American, Caribbean, and remaining South-American ISO alpha-2
        code fell through to ``_DEFAULT_REGION = "emea"`` and produced a
        per-site WARNING at ``_build_region_probes``. This class pins:
          - FR-005 / SC-003: LATAM/Caribbean sites resolve to ``"americas"``.
          - FR-004 / FR-010 / SC-002: the unmapped-code WARNING is deduped
            to <= K unique unmapped codes per invocation (not N sites).
        A per-site regression here (or a silent revert of the region map)
        fires a diagnostic that names the offending code(s).
    """

    _FIXTURE_DIR = Path(__file__).parent / "fixtures"  # sibling directory holding US2 fixtures
    _LATAM_FIXTURE = "latam_caribbean_org.json"  # 8-site fixture covering FR-005 codes
    _AMERICAS_LITERAL = "americas"  # R1 canonical region literal (never "amer")

    def _load_sites(self, name: str) -> list[dict[str, Any]]:
        """Load the ``sites`` list from a fixture JSON file.

        Why:
            All US2 site fixtures share the shape ``{"sites": [...]}`` so a
            single loader eliminates copy-paste at each test.

        Args:
            name: Bare fixture filename resolved against ``_FIXTURE_DIR``.

        Returns:
            The parsed ``sites`` array (list of site dicts with ``id``,
            ``name``, ``country_code``).
        """
        path = self._FIXTURE_DIR / name  # deterministic sibling-directory lookup
        logging.info("TestUs2CountryCodeDedupWarning: loading fixture %s", path)
        payload = json.loads(path.read_text(encoding="utf-8"))  # utf-8 explicit for clarity
        sites = payload["sites"]  # KeyError deliberate: malformed fixture must fail loudly
        logging.debug("_load_sites: %s parsed %d sites", name, len(sites))
        return sites

    def _count_country_code_warnings(self, records: list[logging.LogRecord]) -> int:
        """Count log records that qualify as country_code-tokened WARNINGs.

        Why:
            Contract ``log_record_shape.md`` §2.4 pins the qualifier: level
            is WARNING and the emitted message contains the literal token
            ``country_code``. Centralising the filter keeps every US2 test
            using the same shape and prevents silent drift into stricter or
            looser matching.

        Args:
            records: caplog records to scan.

        Returns:
            The number of records matching (WARNING + ``country_code`` token).
        """
        matches = [
            rec
            for rec in records
            if rec.levelno == logging.WARNING  # only WARNING severity qualifies per contract
            and "country_code" in rec.getMessage()  # grep anchor token from FR-013
        ]
        logging.debug(
            "TestUs2CountryCodeDedupWarning: matched %d country_code WARNING(s)",
            len(matches),
        )
        return len(matches)

    def test_latam_caribbean_region_resolution(self) -> None:
        """T016. Every LATAM/Caribbean site's country_code MUST resolve to "americas".

        Why:
            FR-005 requires ``PA, BS, HT, DO, GT, CU, CR, HN`` (and the
            broader LATAM/Caribbean subset) to classify as ``"americas"``
            after 1025 lands. This test asserts the region map directly
            because ``_build_region_probes`` line 1069 looks up exactly
            this dict; any code path change would have to route through
            it. FR-011 also requires the R1 canonical literal ``"americas"``
            (never ``"amer"``).
        """
        sites = self._load_sites(self._LATAM_FIXTURE)  # load 8-site fixture
        logging.info(  # BEFORE the resolution loop per Constitution VII
            "test_latam_caribbean_region_resolution: verifying %d sites",
            len(sites),
        )
        unresolved: list[tuple[str, str]] = []  # collect all failures for one diagnostic
        for site in sites:  # every fixture site MUST classify to americas
            cc = site["country_code"]  # ISO alpha-2 code from the fixture
            normalised = cc.strip().upper()  # match the resolver's canonicalisation
            region = ospm._COUNTRY_CODE_TO_REGION.get(normalised)  # exact code path used at line 1069
            if region != self._AMERICAS_LITERAL:  # collect drift; do not fail-fast
                unresolved.append((cc, str(region)))  # capture code + observed literal
        logging.debug(  # AFTER the resolution loop per Constitution VII
            "test_latam_caribbean_region_resolution: unresolved=%s",
            unresolved,
        )
        assert unresolved == [], (
            f"LATAM/Caribbean sites failed to resolve to {self._AMERICAS_LITERAL!r}: "
            f"{unresolved}. Extend _COUNTRY_CODE_TO_REGION per FR-005."
        )

    def test_latam_caribbean_no_warnings(self, caplog: pytest.LogCaptureFixture) -> None:
        """T017. LATAM/Caribbean fixture MUST emit zero country_code WARNINGs.

        Why:
            Contract ``log_record_shape.md`` §2.4 mandates zero WARNINGs
            for fixtures whose codes are ALL region-mapped after 1025. The
            LATAM fixture ships only mapped codes (PA/BS/HT/DO/GT/CU/CR/HN)
            so ``_emit_load_time_country_code_warning`` must skip emission
            entirely. Any WARNING here indicates the region map extension
            (T020) regressed.
        """
        sites = self._load_sites(self._LATAM_FIXTURE)  # 8-site LATAM fixture
        gap_set = ospm._COUNTRY_CODE_INTENTIONAL_GAPS  # module-level frozenset installed by T021
        region_map = ospm._COUNTRY_CODE_TO_REGION  # module-level dict extended by T020
        unmapped = ospm._compute_unmapped_country_codes(  # exact helper US2 will call at load time
            sites,
            region_map,
            gap_set,
        )
        warned_unmapped_codes: set[str] = set()  # fresh per-run dedup state (FR-012)
        caplog.set_level(logging.WARNING, logger="src.org.org_synthetic_probes_manager")
        start = len(caplog.records)  # snapshot so we ignore prior records
        logging.info(  # BEFORE the load-time emission per Constitution VII
            "test_latam_caribbean_no_warnings: invoking load-time hook (unmapped=%d)",
            len(unmapped),
        )
        ospm._emit_load_time_country_code_warning(unmapped, warned_unmapped_codes)  # single call site
        logging.debug(  # AFTER the load-time emission per Constitution VII
            "test_latam_caribbean_no_warnings: warned_unmapped_codes=%s",
            warned_unmapped_codes,
        )
        emitted = caplog.records[start:]  # only records from this test slice
        count = self._count_country_code_warnings(list(emitted))  # centralised filter
        assert count == 0, (
            f"LATAM/Caribbean fixture emitted {count} country_code WARNING(s); "
            f"expected 0. Codes present in fixture but flagged unmapped: {sorted(unmapped)}"
        )

    def test_unmapped_country_warning_dedup(self, caplog: pytest.LogCaptureFixture) -> None:
        """T018. Unmapped-code WARNINGs MUST be deduped to <= K unique codes per run.

        Why:
            FR-004 / FR-010 / SC-002. A synthetic 30-site fixture where every
            site shares a single unmapped code ``"ZZ"`` must emit at most 1
            WARNING (not 30). Emitting per-site would re-introduce the
            noise storm US2 exists to fix. The diagnostic names BOTH the
            observed count and the cap so a CI failure directs the reader
            straight to the regression -- per O2 remediation folding the
            T027 diagnostic-quality enhancement into MVP tests.
        """
        # Deliberately synthesize an unmapped code -- "ZZ" is the ISO 3166
        # user-assigned range and is guaranteed absent from the alpha-2
        # universe fixture, so it cannot be silently classified by T020.
        unmapped_code = "ZZ"  # ISO 3166 user-assigned code -- never officially assigned
        fake_sites = [
            {"id": f"synthetic-{idx:04d}", "name": f"site-{idx}", "country_code": unmapped_code}
            for idx in range(30)  # 30 sites all sharing one unmapped code
        ]
        # Sanity: the code must not be mapped or in the gap set, otherwise the test is vacuous.
        assert (
            unmapped_code not in ospm._COUNTRY_CODE_TO_REGION
        ), f"test setup broken: {unmapped_code!r} unexpectedly present in region map"
        assert (
            unmapped_code not in ospm._COUNTRY_CODE_INTENTIONAL_GAPS
        ), f"test setup broken: {unmapped_code!r} unexpectedly present in gap set"
        unmapped = ospm._compute_unmapped_country_codes(  # compute unique unmapped codes
            fake_sites,
            ospm._COUNTRY_CODE_TO_REGION,
            ospm._COUNTRY_CODE_INTENTIONAL_GAPS,
        )
        k_unique = len(unmapped)  # cap for the WARNING count assertion
        warned_unmapped_codes: set[str] = set()  # fresh dedup state (FR-012)
        caplog.set_level(logging.WARNING, logger="src.org.org_synthetic_probes_manager")
        start = len(caplog.records)  # snapshot to isolate this test's records
        logging.info(  # BEFORE the load-time emission per Constitution VII
            "test_unmapped_country_warning_dedup: invoking hook (unmapped=%d)",
            k_unique,
        )
        ospm._emit_load_time_country_code_warning(unmapped, warned_unmapped_codes)
        logging.debug(  # AFTER the load-time emission per Constitution VII
            "test_unmapped_country_warning_dedup: warned_unmapped_codes=%s",
            warned_unmapped_codes,
        )
        emitted = caplog.records[start:]  # slice to just this call
        count = self._count_country_code_warnings(list(emitted))  # filter to WARNING+token
        assert count <= k_unique, (
            f"country_code WARNING count {count} exceeded unique-unmapped-code cap "
            f"{k_unique}; per-site duplication regressed."
        )

    def test_country_warning_re_emit_across_runs(self, caplog: pytest.LogCaptureFixture) -> None:
        """T029a. Country-code dedup state does NOT persist across independent runs.

        Why:
            Sibling of ``TestUs1CenrDedupWarning.test_cenr_warning_re_emit_across_runs``
            (T009) but for the country-code path. Operators intentionally
            re-run menu 206 to verify a fix landed; the unmapped-code
            WARNING must fire again on each new run so the operator sees
            the current unmapped set, not a stale "already warned"
            silence. This test invokes the load-time hook twice back-to-back
            with independent ``warned_unmapped_codes`` sets and asserts
            both invocations independently produce WARNINGs. G1 remediation
            closed the asymmetric FR-012 coverage gap by adding this
            country-code sibling.
        """
        # Arrange: shared fixture -- 30 synthetic sites with one unmapped
        # code "ZZ". Both runs see the identical unmapped set so any
        # dedup-state leak would silence run 2 (the regression trap).
        logging.info("test_country_warning_re_emit_across_runs: preparing two independent runs")
        unmapped_code = "ZZ"  # ISO 3166 user-assigned range; guaranteed unmapped
        fake_sites = [
            {"id": f"synthetic-{idx:04d}", "name": f"site-{idx}", "country_code": unmapped_code}
            for idx in range(30)  # 30 sites all sharing one unmapped code
        ]
        # Sanity: the code must not be mapped or in the gap set, otherwise the test is vacuous.
        assert (
            unmapped_code not in ospm._COUNTRY_CODE_TO_REGION
        ), f"test setup broken: {unmapped_code!r} unexpectedly present in region map"
        assert (
            unmapped_code not in ospm._COUNTRY_CODE_INTENTIONAL_GAPS
        ), f"test setup broken: {unmapped_code!r} unexpectedly present in gap set"
        unmapped = ospm._compute_unmapped_country_codes(  # unique unmapped codes across the site set
            fake_sites,
            ospm._COUNTRY_CODE_TO_REGION,
            ospm._COUNTRY_CODE_INTENTIONAL_GAPS,
        )

        # Act (run 1): fresh dedup set, invoke the load-time hook once.
        caplog.set_level(logging.WARNING, logger="src.org.org_synthetic_probes_manager")  # WARNING+
        run1_start = len(caplog.records)  # anchor to slice run-1 records later
        warned_unmapped_codes_run1: set[str] = set()  # NEW per-run dedup set per FR-012
        ospm._emit_load_time_country_code_warning(unmapped, warned_unmapped_codes_run1)  # single call
        run1_records = caplog.records[run1_start:]  # snapshot of run-1 emissions
        run1_count = self._count_country_code_warnings(list(run1_records))  # WARNING count for run 1

        # Act (run 2): SEPARATE fresh dedup set; the hook MUST re-emit
        # because this is a fresh operator invocation (bounded per FR-012).
        run2_start = len(caplog.records)  # anchor to slice run-2 records
        warned_unmapped_codes_run2: set[str] = set()  # DISTINCT new set -- state must not persist
        ospm._emit_load_time_country_code_warning(unmapped, warned_unmapped_codes_run2)  # 2nd call
        run2_records = caplog.records[run2_start:]  # snapshot of run-2 emissions
        run2_count = self._count_country_code_warnings(list(run2_records))  # WARNING count for run 2

        logging.info(
            "test_country_warning_re_emit_across_runs: run1=%d run2=%d",
            run1_count,
            run2_count,
        )

        # Assert: both runs must emit at least one WARNING for the same
        # unmapped set. A run-2 count of zero means the dedup state
        # persisted across invocations (silent second run), which is the
        # regression this test traps.
        assert run1_count >= 1, (  # run-1 must emit -- otherwise the fixture is malformed
            f"Run 1 emitted {run1_count} country_code WARNINGs; expected >= 1 for unmapped set {sorted(unmapped)}"
        )
        assert run2_count >= 1, (  # run-2 must ALSO emit; silence means state leaked
            f"Run 2 emitted {run2_count} country_code WARNINGs; expected >= 1 -- dedup state leaked across runs"
        )


def test_regression_runtime_under_budget(pytestconfig: pytest.Config) -> None:  # T029
    """The 1025 regression suite MUST complete under a 5.0 s wall-clock budget.

    Why:
        SC-007 pins a soft-real-time performance envelope for the entire
        1025 regression subset (all dedup + coverage + byte-stability
        tests) so CI cost does not creep as tests are added. Running the
        curated subset via ``pytest.main`` from within a test lets us
        measure the actual wall-clock cost with ``time.perf_counter``
        bookends -- the same clock the pytest runner uses.

        The budget of 5.0 s is generous enough to accommodate the
        reference dev machine's cold-start caching while surfacing any
        multi-second regression (e.g. a fixture-load loop that scales
        with site count). Per O1 remediation, SC-007 is annotated in
        spec.md as verified only after US3 lands; if MVP-first ship path
        is chosen (US1 only), SC-007 remains provably-unverified until
        this task lands. We deliberately EXCLUDE this test from the
        subset it measures (recursion guard).
    """
    import time  # local import so the top-of-file stays lean when this test skips

    # Guard against recursive self-invocation: if pytest is already inside
    # this test's frame (e.g. a user runs the subset manually and the
    # runner sweeps this file), we cannot spawn another pytest without
    # blowing the stack. ``PYTEST_CURRENT_TEST`` env var breadcrumbs the
    # active test so we can detect nested invocation and bail cleanly.
    import os

    if os.environ.get("_1025_RUNTIME_BUDGET_INFLIGHT") == "1":  # recursion guard
        logging.info("test_regression_runtime_under_budget: nested invocation detected -- skipping")
        pytest.skip("nested pytest invocation would recurse into the runtime-budget test")

    # The curated 1025 regression subset -- one representative per contract.
    # Kept minimal because pytest-in-pytest still has ~500 ms of fixed
    # overhead per node. Adding tests here MUST be a conscious decision
    # (they contribute directly to the SC-007 budget).
    #
    # Absolute node IDs are anchored to this file's absolute path via
    # ``Path(__file__)`` so the nested ``pytest.main`` invocation does not
    # depend on cwd or rootdir agreement with the parent runner. Windows
    # test collection was silently failing with relative "tests/..." paths
    # when the outer pytest run set rootdir to an alternative ancestor.
    _this_file = str(Path(__file__).resolve())  # absolute path to the current test module
    _coverage_file = str(  # absolute path to the ISO coverage sibling test file
        (Path(__file__).parent / "test_country_region_coverage.py").resolve()
    )
    subset = [
        # US1 CENR dedup contract representatives
        f"{_this_file}::TestUs1CenrDedupWarning::test_cenr_warning_dedup_ge_1_missing",
        f"{_this_file}::TestUs1CenrDedupWarning::test_cenr_warning_zero_when_fully_populated",
        f"{_this_file}::TestUs1CenrDedupWarning::test_cenr_warning_re_emit_across_runs",
        f"{_this_file}::TestUs1CenrDedupWarning::test_probe_payload_byte_stability_smoke",
        # US2 country-code dedup contract representatives
        f"{_this_file}::TestUs2CountryCodeDedupWarning::test_latam_caribbean_region_resolution",
        f"{_this_file}::TestUs2CountryCodeDedupWarning::test_latam_caribbean_no_warnings",
        f"{_this_file}::TestUs2CountryCodeDedupWarning::test_unmapped_country_warning_dedup",
        # ISO coverage invariants (SC-005)
        _coverage_file,
    ]

    logging.info("test_regression_runtime_under_budget: measuring %d nodes", len(subset))
    # Set the breadcrumb before spawning the nested runner so any child
    # invocation short-circuits via the guard above.
    os.environ["_1025_RUNTIME_BUDGET_INFLIGHT"] = "1"
    try:
        start = time.perf_counter()  # monotonic wall-clock anchor
        # Invoke pytest directly; ``-q`` suppresses the noisy per-node
        # output, ``--no-header`` trims a few tens of ms, ``-p no:cacheprovider``
        # avoids polluting the parent's cache. The rootdir stays the repo
        # root by default (inherited from the parent pytest invocation).
        exit_code = pytest.main([
            "-q",  # quiet mode
            "--no-header",  # skip pytest header
            "-p",  # disable plugin
            "no:cacheprovider",  # skip .pytest_cache writes
            *subset,  # the curated subset
        ])
        elapsed = time.perf_counter() - start  # wall-clock cost of the nested run
    finally:
        # Always clear the breadcrumb, even on assertion failure.
        os.environ.pop("_1025_RUNTIME_BUDGET_INFLIGHT", None)

    logging.info(
        "test_regression_runtime_under_budget: elapsed=%.3fs exit_code=%d",
        elapsed,
        exit_code,
    )
    # Correctness precondition: the subset must have passed. If a nested
    # test failed, budget verification is meaningless -- surface that first.
    assert exit_code == 0, (
        f"1025 regression subset did not fully pass (pytest exit_code={exit_code}); "
        f"fix the failing tests before evaluating the runtime budget"
    )
    # SC-007: wall-clock budget assertion.
    budget_seconds = 5.0  # SC-007 canonical budget on the reference dev machine
    assert elapsed < budget_seconds, (
        f"1025 regression subset took {elapsed:.3f}s, exceeding the {budget_seconds:.1f}s "
        f"SC-007 budget. Investigate slow fixtures or add a fresh justification if the "
        f"budget must grow."
    )
