"""Unit tests for :mod:`src.utils.zscaler_catalogue`.

Why:
    The catalogue module owns menu 206's auto-refresh gate for the Zscaler
    CENR feed. A regression here would either silently serve stale hostnames
    (missing new ZEN pops on any of the 7 clouds) or crash the menu when a
    cloud endpoint is unreachable. Both failure modes are exactly what the
    plan's fail-open contract is meant to prevent, so exercise every branch
    that decision-tree flows through: is_stale variants, merge dedup,
    refresh happy/partial/total-failure paths, and ensure_fresh gating.

    All network I/O is monkey-patched: no real HTTPS reaches
    ``config.zscaler.com`` from the test suite.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from src.utils import zscaler_catalogue as zc_mod
from src.utils.zscaler_catalogue import (
    _CLOUDS,
    _FRESHNESS_TTL,
    ensure_fresh,
    fetch_cloud,
    is_stale,
    merge_clouds,
    refresh_cenr,
)


def _fresh_ts() -> str:
    """Return an ISO-8601 UTC timestamp that is definitely within the TTL.

    Why:
        Tests repeatedly need a ``fetched_utc`` value that :func:`is_stale`
        will report as fresh; hoist the construction so individual tests
        stay focused on the behaviour under test rather than clock math.

    Returns:
        A ``YYYY-MM-DDTHH:MM:SSZ`` string 1 minute in the past.
    """
    now = datetime.now(UTC) - timedelta(minutes=1)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def _stale_ts() -> str:
    """Return an ISO-8601 UTC timestamp older than the TTL.

    Why:
        Companion to :func:`_fresh_ts` for exercising the stale branch.
        Offsets a full extra hour beyond the TTL so a slow test host can't
        race the boundary.

    Returns:
        A ``YYYY-MM-DDTHH:MM:SSZ`` string ``_FRESHNESS_TTL + 1h`` in the past.
    """
    now = datetime.now(UTC) - (_FRESHNESS_TTL + timedelta(hours=1))
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


class TestIsStale:
    """Cover every branch of the freshness gate."""

    def test_fresh_timestamp_returns_false(self):
        """A timestamp within TTL is fresh."""
        assert is_stale({"fetched_utc": _fresh_ts()}) is False

    def test_stale_timestamp_returns_true(self):
        """A timestamp older than TTL is stale."""
        assert is_stale({"fetched_utc": _stale_ts()}) is True

    def test_missing_timestamp_returns_true(self):
        """Missing ``fetched_utc`` biases toward refresh."""
        assert is_stale({}) is True

    def test_malformed_timestamp_returns_true(self):
        """Unparseable ``fetched_utc`` biases toward refresh."""
        assert is_stale({"fetched_utc": "not-a-timestamp"}) is True

    def test_non_string_timestamp_returns_true(self):
        """Non-string ``fetched_utc`` (e.g. int) is treated as missing."""
        assert is_stale({"fetched_utc": 1234567890}) is True

    def test_empty_string_timestamp_returns_true(self):
        """Empty ``fetched_utc`` is treated as missing."""
        assert is_stale({"fetched_utc": ""}) is True

    def test_plus_zero_suffix_is_parsed(self):
        """``+00:00`` suffix is a valid ISO-8601 offset and parses cleanly."""
        now = datetime.now(UTC) - timedelta(minutes=1)
        raw = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        assert is_stale({"fetched_utc": raw}) is False

    def test_naive_timestamp_is_treated_as_utc(self):
        """A tz-naive timestamp is coerced to UTC rather than crashing."""
        now = datetime.utcnow() - timedelta(minutes=1)
        raw = now.strftime("%Y-%m-%dT%H:%M:%S")
        assert is_stale({"fetched_utc": raw}) is False


def _cloud_doc(cloud: str, cities: dict[str, list[dict[str, Any]]], continent: str = "EMEA") -> dict[str, Any]:
    """Build a real-shape single-cloud CENR document for tests.

    Why:
        The real ``config.zscaler.com/api/<cloud>/cenr/json`` payload nests
        records as ``{cloud: {"continent : X": {"city : Y": [record, ...]}}}``.
        Fixtures must match this exact shape to exercise
        :func:`merge_clouds`'s actual traversal rather than the old
        (incorrect) flat-key assumption it replaced.

    Args:
        cloud: Cloud slug this document represents (e.g. ``"zscaler.net"``).
        cities: Mapping of bare city name -> list of raw CENR records (each
            optionally carrying ``hostname``/``vpn`` keys).
        continent: Bare continent name to nest the cities under.

    Returns:
        A dict matching the real per-cloud CENR JSON shape.
    """
    return {cloud: {f"continent : {continent}": {f"city : {city}": records for city, records in cities.items()}}}


class TestMergeClouds:
    """Verify the nested-shape merge produces deduped, sorted, provenance-rich output."""

    def test_dedup_across_overlapping_hostnames(self):
        """Identical hostnames from multiple clouds collapse to one entry."""
        per_cloud = {
            "zscaler.net": _cloud_doc(
                "zscaler.net", {"City A": [{"hostname": "a.example.com"}, {"hostname": "b.example.com"}]}
            ),
            "zscalerone.net": _cloud_doc(
                "zscalerone.net", {"City A": [{"hostname": "b.example.com"}, {"hostname": "c.example.com"}]}
            ),
        }
        merged = merge_clouds(per_cloud)
        # merge_clouds now emits v3 host-entry dicts so the on-disk shape
        # matches the ``schema_version=3`` stamp. See root-cause bug where a
        # v3 stamp over flat-string bags made the loader short-circuit skip
        # observation merging, and ``_probe_target`` fell through to HTTPS
        # for every VPN host.
        assert [entry["host"] for entry in merged["proxy_hostnames"]] == [
            "a.example.com",
            "b.example.com",
            "c.example.com",
        ]

    def test_dedup_across_overlapping_cities(self):
        """A city seen in multiple clouds unions its hostnames and tracks provenance."""
        per_cloud = {
            "zscaler.net": _cloud_doc("zscaler.net", {"London I": [{"hostname": "lon1.zs.example"}]}),
            "zscalerone.net": _cloud_doc(
                "zscalerone.net", {"London I": [{"hostname": "lon2.zs.example", "vpn": "vpn1"}]}
            ),
        }
        merged = merge_clouds(per_cloud)
        entry = merged["by_city"]["London I"]
        assert [h["host"] for h in entry["proxy_hostnames"]] == ["lon1.zs.example", "lon2.zs.example"]
        assert [h["host"] for h in entry["vpn_hostnames"]] == ["vpn1"]
        assert entry["seen_in_clouds"] == ["zscaler.net", "zscalerone.net"]

    def test_output_shape_has_required_keys(self):
        """Merged doc exposes the exact keys downstream consumers depend on."""
        merged = merge_clouds({"zscaler.net": {}})
        for key in (
            "schema_version",
            "fetched_utc",
            "source_urls",
            "description",
            "probe_default",
            "proxy_hostnames",
            "vpn_hostnames",
            "by_city",
        ):
            assert key in merged
        assert merged["schema_version"] == 3

    def test_source_urls_reflect_per_cloud_input(self):
        """``source_urls`` contains one URL per cloud actually merged."""
        merged = merge_clouds({"zscaler.net": {}, "zscloud.net": {}})
        assert merged["source_urls"] == [
            "https://config.zscaler.com/api/zscaler.net/cenr/json",
            "https://config.zscaler.com/api/zscloud.net/cenr/json",
        ]

    def test_ignores_non_dict_cloud_entries(self):
        """A cloud entry that is not a dict is silently skipped."""
        per_cloud = {
            "zscaler.net": _cloud_doc("zscaler.net", {"City A": [{"hostname": "a"}]}),
            "zscloud.net": None,
        }
        merged = merge_clouds(per_cloud)  # type: ignore[arg-type]
        assert [entry["host"] for entry in merged["proxy_hostnames"]] == ["a"]

    def test_skips_non_string_hostnames(self):
        """Non-string / empty hostname entries are dropped rather than crashing."""
        per_cloud = {
            "zscaler.net": _cloud_doc(
                "zscaler.net",
                {
                    "City A": [
                        {"hostname": "good"},
                        {"hostname": ""},
                        {"hostname": 42},
                        {"hostname": None},
                        {"hostname": "also-good"},
                    ]
                },
            ),
        }
        merged = merge_clouds(per_cloud)
        assert [entry["host"] for entry in merged["proxy_hostnames"]] == ["also-good", "good"]
        assert merged["vpn_hostnames"] == []

    def test_ignores_non_dict_city_entries(self):
        """A city entry whose value is not a list of records is silently skipped."""
        per_cloud = {
            "zscaler.net": {
                "zscaler.net": {
                    "continent : EMEA": {
                        "city : London": "not-a-list",
                        "city : Paris": [{"hostname": "p.zs"}],
                    }
                }
            }
        }
        merged = merge_clouds(per_cloud)
        assert list(merged["by_city"].keys()) == ["Paris"]


class TestFetchCloud:
    """Verify HTTP fetch is defensive against every plausible failure."""

    def test_success_returns_parsed_json(self, monkeypatch):
        """A 200 response with valid JSON round-trips through the parser."""

        class _Resp:
            status = 200

            def read(self):
                return b'{"proxy_hostnames": ["x.example"]}'

            def __enter__(self):
                return self

            def __exit__(self, *_a):
                return False

        monkeypatch.setattr(zc_mod.urllib.request, "urlopen", lambda *_a, **_kw: _Resp())
        assert fetch_cloud("zscaler.net") == {"proxy_hostnames": ["x.example"]}

    def test_non_200_returns_none(self, monkeypatch):
        """A non-200 status is a soft failure and returns ``None``."""

        class _Resp:
            status = 503

            def read(self):
                return b""

            def __enter__(self):
                return self

            def __exit__(self, *_a):
                return False

        monkeypatch.setattr(zc_mod.urllib.request, "urlopen", lambda *_a, **_kw: _Resp())
        assert fetch_cloud("zscaler.net") is None

    def test_network_error_returns_none(self, monkeypatch):
        """URLError from the transport surfaces as ``None``, not an exception."""

        def _boom(*_a, **_kw):
            raise zc_mod.urllib.error.URLError("dns down")

        monkeypatch.setattr(zc_mod.urllib.request, "urlopen", _boom)
        assert fetch_cloud("zscaler.net") is None

    def test_timeout_returns_none(self, monkeypatch):
        """A socket timeout surfaces as ``None`` rather than propagating."""

        def _boom(*_a, **_kw):
            raise TimeoutError("slow")

        monkeypatch.setattr(zc_mod.urllib.request, "urlopen", _boom)
        assert fetch_cloud("zscaler.net") is None

    def test_bad_json_returns_none(self, monkeypatch):
        """Malformed JSON in the response body degrades to ``None``."""

        class _Resp:
            status = 200

            def read(self):
                return b"not json"

            def __enter__(self):
                return self

            def __exit__(self, *_a):
                return False

        monkeypatch.setattr(zc_mod.urllib.request, "urlopen", lambda *_a, **_kw: _Resp())
        assert fetch_cloud("zscaler.net") is None

    def test_non_object_json_returns_none(self, monkeypatch):
        """Top-level JSON that isn't a dict is rejected (defends the merge contract)."""

        class _Resp:
            status = 200

            def read(self):
                return b"[1, 2, 3]"

            def __enter__(self):
                return self

            def __exit__(self, *_a):
                return False

        monkeypatch.setattr(zc_mod.urllib.request, "urlopen", lambda *_a, **_kw: _Resp())
        assert fetch_cloud("zscaler.net") is None


class TestRefreshCenr:
    """Cover happy, partial-failure, and total-failure branches."""

    def test_happy_path_writes_merged_file(self, monkeypatch, tmp_path):
        """All 7 clouds return data → merged file is written atomically."""
        monkeypatch.setattr(
            zc_mod,
            "fetch_cloud",
            lambda cloud, **_kw: _cloud_doc(cloud, {"City A": [{"hostname": "p.zs", "vpn": "v.zs"}]}),
        )
        monkeypatch.setattr(
            zc_mod,
            "attach_city_metadata",
            lambda doc: (doc, []),
        )
        cenr_path = tmp_path / "zscaler_cenr_hostnames.json"
        fresh, warnings = refresh_cenr(cenr_path)
        assert warnings == []
        assert cenr_path.is_file()
        on_disk = json.loads(cenr_path.read_text(encoding="utf-8"))
        assert on_disk == fresh
        assert [entry["host"] for entry in fresh["proxy_hostnames"]] == ["p.zs"]
        assert len(fresh["source_urls"]) == len(_CLOUDS)

    def test_partial_failure_still_writes_merged_subset(self, monkeypatch, tmp_path):
        """2 of 7 clouds fail → merge proceeds with the 5 that succeeded."""
        failing = {"zscloud.net", "zscalerbeta.net"}

        def _fetch(cloud, **_kw):
            if cloud in failing:
                return None
            return _cloud_doc(cloud, {"City A": [{"hostname": f"{cloud}.host"}]})

        monkeypatch.setattr(zc_mod, "fetch_cloud", _fetch)
        monkeypatch.setattr(zc_mod, "attach_city_metadata", lambda doc: (doc, []))
        cenr_path = tmp_path / "zscaler_cenr_hostnames.json"
        fresh, warnings = refresh_cenr(cenr_path)
        assert cenr_path.is_file()
        assert len(fresh["source_urls"]) == len(_CLOUDS) - len(failing)
        assert any("zscloud.net" in w for w in warnings)  # lgtm[py/incomplete-url-substring-sanitization]
        assert any("zscalerbeta.net" in w for w in warnings)  # lgtm[py/incomplete-url-substring-sanitization]
        # Every non-failing cloud contributed exactly one hostname.
        assert len(fresh["proxy_hostnames"]) == len(_CLOUDS) - len(failing)

    def test_total_failure_keeps_stale_cache(self, monkeypatch, tmp_path):
        """All 7 clouds fail → the on-disk stale copy is returned unchanged."""
        cenr_path = tmp_path / "zscaler_cenr_hostnames.json"
        stale = {"fetched_utc": _stale_ts(), "proxy_hostnames": ["kept.zs"]}
        cenr_path.write_text(json.dumps(stale), encoding="utf-8")
        monkeypatch.setattr(zc_mod, "fetch_cloud", lambda cloud, **_kw: None)
        fresh, warnings = refresh_cenr(cenr_path)
        assert fresh == stale
        assert any("all Zscaler cloud fetches failed" in w for w in warnings)
        # Stale file must not have been overwritten.
        assert json.loads(cenr_path.read_text(encoding="utf-8")) == stale

    def test_total_failure_with_missing_file_returns_empty(self, monkeypatch, tmp_path):
        """Total failure + no on-disk cache → empty dict + warning, no crash."""
        cenr_path = tmp_path / "missing.json"
        monkeypatch.setattr(zc_mod, "fetch_cloud", lambda cloud, **_kw: None)
        fresh, warnings = refresh_cenr(cenr_path)
        assert fresh == {}
        assert warnings  # at least the "all fetches failed" warning

    def test_city_metadata_warnings_propagate(self, monkeypatch, tmp_path):
        """Warnings from ``attach_city_metadata`` bubble into the return list."""
        monkeypatch.setattr(
            zc_mod,
            "fetch_cloud",
            lambda cloud, **_kw: _cloud_doc(cloud, {"City A": [{"hostname": "p.zs"}]}),
        )
        monkeypatch.setattr(
            zc_mod,
            "attach_city_metadata",
            lambda doc: (doc, ["unmapped city: Atlantis"]),
        )
        cenr_path = tmp_path / "zscaler_cenr_hostnames.json"
        _, warnings = refresh_cenr(cenr_path)
        assert "unmapped city: Atlantis" in warnings


class TestEnsureFresh:
    """Verify the choke-point gates refresh + validation correctly."""

    def test_fresh_cache_is_passthrough(self, monkeypatch, tmp_path):
        """In-TTL cache short-circuits before any refresh work."""
        called: dict[str, bool] = {"refresh": False, "validate": False}

        def _refresh(_p: Path) -> tuple[dict[str, Any], list[str]]:
            called["refresh"] = True
            return {}, []

        monkeypatch.setattr(zc_mod, "refresh_cenr", _refresh)
        monkeypatch.setattr(zc_mod, "run_full_validation", lambda *_a, **_kw: called.update(validate=True) or [])
        cenr = {"fetched_utc": _fresh_ts(), "proxy_hostnames": ["kept.zs"]}
        result = ensure_fresh(tmp_path / "cenr.json", cenr)
        assert result is cenr
        assert called == {"refresh": False, "validate": False}

    def test_stale_cache_triggers_refresh_and_validation(self, monkeypatch, tmp_path):
        """Stale cache runs refresh + full-fleet validation before returning."""
        refreshed = {"fetched_utc": _fresh_ts(), "proxy_hostnames": ["new.zs"]}
        monkeypatch.setattr(zc_mod, "refresh_cenr", lambda _p: (refreshed, []))
        seen: dict[str, Any] = {}

        def _validate(probes, cenr, **_kw):
            seen["cenr"] = cenr
            seen["probes"] = probes
            return []

        monkeypatch.setattr(zc_mod, "run_full_validation", _validate)
        # Give the probes file some contents so the "is_file" branch is taken.
        (tmp_path / "zscaler_client_connector_probes.json").write_text(json.dumps({"roles": []}), encoding="utf-8")
        stale = {"fetched_utc": _stale_ts()}
        result = ensure_fresh(tmp_path / "zscaler_cenr_hostnames.json", stale)
        assert result is refreshed
        assert seen["cenr"] is refreshed
        # promote_cache_document stamps schema_version=3 into the probes
        # dict when the on-disk file was v2 (or missing schema_version), so
        # the dict seen by run_full_validation carries the version marker.
        assert seen["probes"] == {"roles": [], "schema_version": 3}

    def test_missing_probes_file_uses_empty_dict(self, monkeypatch, tmp_path):
        """When probes JSON is absent, validation runs against an empty catalogue."""
        refreshed = {"fetched_utc": _fresh_ts(), "proxy_hostnames": []}
        monkeypatch.setattr(zc_mod, "refresh_cenr", lambda _p: (refreshed, []))
        seen: dict[str, Any] = {}

        def _validate(probes, _cenr, **_kw):
            seen["probes"] = probes
            return []

        monkeypatch.setattr(zc_mod, "run_full_validation", _validate)
        result = ensure_fresh(tmp_path / "zscaler_cenr_hostnames.json", {"fetched_utc": _stale_ts()})
        assert result is refreshed
        # promote_cache_document stamps schema_version=3 into the empty
        # probes fallback dict, so the caller sees the version marker even
        # when no probes file exists on disk.
        assert seen["probes"] == {"schema_version": 3}

    def test_validation_exception_is_non_fatal(self, monkeypatch, tmp_path):
        """A crash in ``run_full_validation`` does not block the refreshed dict."""
        refreshed = {"fetched_utc": _fresh_ts(), "proxy_hostnames": ["new.zs"]}
        monkeypatch.setattr(zc_mod, "refresh_cenr", lambda _p: (refreshed, []))

        def _boom(*_a, **_kw):
            raise RuntimeError("network gone")

        monkeypatch.setattr(zc_mod, "run_full_validation", _boom)
        result = ensure_fresh(tmp_path / "zscaler_cenr_hostnames.json", {"fetched_utc": _stale_ts()})
        assert result is refreshed

    def test_empty_refresh_result_falls_back_to_in_memory_copy(self, monkeypatch, tmp_path):
        """Total-failure refresh (empty dict) falls back to the caller's dict."""
        monkeypatch.setattr(zc_mod, "refresh_cenr", lambda _p: ({}, ["all fetches failed"]))
        # run_full_validation should not be reached in this branch.
        monkeypatch.setattr(
            zc_mod,
            "run_full_validation",
            lambda *_a, **_kw: pytest.fail("validation should not run on empty refresh"),
        )
        in_memory = {"fetched_utc": _stale_ts(), "proxy_hostnames": ["kept.zs"]}
        result = ensure_fresh(tmp_path / "zscaler_cenr_hostnames.json", in_memory)
        assert result is in_memory

    def test_zero_responding_endpoints_still_returns_refreshed(self, monkeypatch, tmp_path):
        """Validation reporting zero responders logs a warning but keeps the refresh."""
        refreshed = {"fetched_utc": _fresh_ts(), "proxy_hostnames": ["new.zs"]}
        monkeypatch.setattr(zc_mod, "refresh_cenr", lambda _p: (refreshed, []))

        class _Result:
            responding_protocols: list[str] = []

        monkeypatch.setattr(zc_mod, "run_full_validation", lambda *_a, **_kw: [_Result(), _Result()])
        result = ensure_fresh(tmp_path / "zscaler_cenr_hostnames.json", {"fetched_utc": _stale_ts()})
        assert result is refreshed


def test_v2_cache_promotes_to_v3_shape_in_memory(caplog: pytest.LogCaptureFixture) -> None:
    """A v2 (flat-string) cache is loaded and every host bag becomes a v3 dict.

    Why:
        Feature 1023 (contract ``cenr_cache_schema_v3.md``) requires the
        loader adapter :func:`promote_cache_document` to convert existing
        v2 on-disk caches into the v3 per-host object shape without any
        refresh cycle. Regressing this would either crash menu 206 on load
        of a legacy cache (breaking FR-006) or silently pass v2 strings
        through to ``_probe_target``, which would then dispatch on the
        wrong branch. Both cache kinds (CENR + ZCC) must be exercised so a
        typo in ``kind=`` cannot silently drop half the fleet.
    """
    fixtures = Path(__file__).parent / "fixtures"  # v2 fixtures live alongside the test module
    cenr_v2 = json.loads((fixtures / "zscaler_cenr_hostnames_v2.json").read_text(encoding="utf-8"))
    zcc_v2 = json.loads((fixtures / "zscaler_client_connector_probes_v2.json").read_text(encoding="utf-8"))
    # Pre-conditions: fixtures MUST be v2-shaped so the adapter has real work.
    assert cenr_v2.get("schema_version") != 3  # ensure fixture is actually legacy
    assert zcc_v2.get("schema_version") != 3  # ensure fixture is actually legacy

    with caplog.at_level("INFO", logger="src.utils.zscaler_catalogue"):
        cenr_v3 = zc_mod.promote_cache_document(cenr_v2, kind="cenr")  # v2 -> v3
        zcc_v3 = zc_mod.promote_cache_document(zcc_v2, kind="zcc")  # v2 -> v3

    # Post: version stamped so re-load short-circuits without logging.
    assert cenr_v3["schema_version"] == 3
    assert zcc_v3["schema_version"] == 3

    # Every top-level CENR host is now a dict of the v3 shape.
    for bag_key in ("proxy_hostnames", "vpn_hostnames"):
        bag = cenr_v3.get(bag_key) or []
        assert bag, f"fixture CENR bag {bag_key} was empty; test is meaningless"
        for entry in bag:
            assert isinstance(entry, dict), f"non-dict entry in {bag_key}: {entry!r}"
            assert "host" in entry and isinstance(entry["host"], str) and entry["host"]
            # Observation fields absent per contract for a freshly-promoted entry.
            assert "observed_protocol" not in entry or entry["observed_protocol"] is None
            assert "observed_port" not in entry or entry["observed_port"] is None
            assert "last_probed" not in entry or entry["last_probed"] is None

    # Every per-city CENR host must also be promoted.
    by_city = cenr_v3.get("by_city") or {}
    assert by_city, "fixture must exercise the by_city bags too"
    for city_slot in by_city.values():
        if not isinstance(city_slot, dict):
            continue
        for bag_key in ("proxy_hostnames", "vpn_hostnames"):
            for entry in city_slot.get(bag_key, []) or []:
                assert isinstance(entry, dict) and "host" in entry

    # Every roles[*].fqdns entry in the ZCC cache must be a v3 dict too. The
    # ZCC schema stores ``roles`` as a list of role objects (each with its own
    # ``fqdns`` bag), not as a dict keyed by role name — iterate the list.
    roles_iter = zcc_v3.get("roles") or []
    assert isinstance(roles_iter, list) and roles_iter, "ZCC fixture must have roles"
    zcc_fqdn_dicts = 0
    for role_body in roles_iter:
        if not isinstance(role_body, dict):
            continue
        for entry in role_body.get("fqdns", []) or []:
            assert isinstance(entry, dict) and "host" in entry
            zcc_fqdn_dicts += 1
    assert zcc_fqdn_dicts > 0, "ZCC promotion produced zero v3 fqdn dicts"

    # Exactly one INFO line per promotion event (two total: one per kind).
    info_lines = [r for r in caplog.records if r.levelname == "INFO" and r.name == "src.utils.zscaler_catalogue"]
    assert len(info_lines) == 2, f"expected 2 INFO lines (one per kind); got {len(info_lines)}"
    for record in info_lines:
        assert "loaded v" in record.getMessage()
        assert "observations absent" in record.getMessage()

    # Idempotency: re-promoting a v3 doc must NOT emit any additional INFO line.
    caplog.clear()
    with caplog.at_level("INFO", logger="src.utils.zscaler_catalogue"):
        zc_mod.promote_cache_document(cenr_v3, kind="cenr")
        zc_mod.promote_cache_document(zcc_v3, kind="zcc")
    idem_info = [r for r in caplog.records if r.levelname == "INFO"]
    assert idem_info == [], f"re-promotion must be silent; got {[r.getMessage() for r in idem_info]}"


# ----------------------------------------------------------------------
# US3 (T021-T026): Persisted observations round-trip through the cache files.
#
# Why (5-W):
#     Feature 1023 US3 (specs/1023-.../spec.md) adds an observation-merge step
#     to ``ensure_fresh`` so every host entry in both CENR and ZCC caches
#     carries ``observed_protocol`` / ``observed_port`` / ``last_probed`` after
#     each refresh. Regressions would either wipe the observations (breaking
#     US1's URL builder) or silently mis-classify a host (e.g. writing HTTPS
#     for a VPN host), so exercise every branch of the write-path priority
#     table declared in ``contracts/cenr_cache_schema_v3.md`` §Write Path.
# ----------------------------------------------------------------------


def _make_probe_result(
    fqdn: str,
    *,
    tcp: dict[int, str] | None = None,
    udp: dict[int, str] | None = None,
    https_status: int | None = None,
    responding_protocols: list[str] | None = None,
) -> Any:
    """Build a minimal ``ProbeResult`` stub for write-path tests.

    Why:
        The write-path merger only reads ``fqdn`` / ``tcp`` / ``udp`` /
        ``https_status`` / ``responding_protocols`` from the result. Building
        one via the real dataclass constructor keeps the isinstance / attribute
        contract identical to what ``run_full_validation`` actually returns
        (so a refactor that changes the shape breaks the tests, not silently
        skips them).

    Args:
        fqdn: Hostname the fake probe targeted.
        tcp: Optional per-port TCP outcome map.
        udp: Optional per-port UDP outcome map.
        https_status: Optional HTTPS status code observed on 443.
        responding_protocols: Optional compact protocol list (mirrors
            ``ProbeResult.responding_protocols``).

    Returns:
        A ``ProbeResult`` instance ready to hand to the merge helper.
    """
    from src.utils.zscaler_probe import ProbeResult  # local import; only tests need it

    return ProbeResult(
        fqdn=fqdn,
        role="test-role",
        role_description="synthetic",
        declared_ports=[443],
        critical=False,
        tcp=dict(tcp or {}),
        udp=dict(udp or {}),
        https_status=https_status,
        responding_protocols=list(responding_protocols or []),
    )


def _write_min_cenr_file(cenr_path: Path, hosts: list[str]) -> None:
    """Write a stale v2 CENR JSON with the given proxy_hostnames to disk.

    Why:
        The ensure_fresh write path needs a real on-disk file to atomic-rename
        into. A stale ``fetched_utc`` guarantees the freshness gate flips to
        "refresh" so the merge/write branch is exercised in every test.

    Args:
        cenr_path: Destination path.
        hosts: Bare host strings (v2 shape) to seed into ``proxy_hostnames``.
    """
    doc = {
        "schema_version": 2,  # forces the v2 -> v3 promotion branch on load
        "fetched_utc": _stale_ts(),  # forces the refresh branch of ensure_fresh
        "proxy_hostnames": list(hosts),  # legacy flat-string bag; adapter promotes
        "vpn_hostnames": [],  # empty is fine; adapter still normalises
        "by_city": {},  # empty city bag keeps the fixture minimal
    }
    cenr_path.write_text(json.dumps(doc), encoding="utf-8")


def _install_refresh_returning(monkeypatch, refreshed: dict[str, Any]) -> None:
    """Stub ``zc_mod.refresh_cenr`` so it returns a pre-built merged dict.

    Why:
        Real ``refresh_cenr`` fans out HTTPS fetches; every US3 test needs a
        deterministic dict to feed the write step, so the network side is
        stubbed and only the observation-merge/atomic-write path is exercised.

    Args:
        monkeypatch: pytest fixture.
        refreshed: The dict the stub returns as ``(refreshed, [])``.
    """

    def _stub(_path: Path) -> tuple[dict[str, Any], list[str]]:
        return refreshed, []

    monkeypatch.setattr(zc_mod, "refresh_cenr", _stub)


class TestUS3PersistedObservations:
    """Cover the observation-merge write path introduced by US3."""

    def test_schema_v3_write_populates_observation_fields(self, monkeypatch, tmp_path):
        """T021 [US3]: refresh writes the v3 observation triplet per host.

        Why:
            Contract §Write Path requires every host across the four CENR bags
            to acquire ``observed_protocol`` / ``observed_port`` /
            ``last_probed`` matching whatever ``run_full_validation`` reported.
            A single mixed batch (HTTPS + UDP/500 + silent) exercises the
            three main branches of the priority table.
        """
        cenr_path = tmp_path / "zscaler_cenr_hostnames.json"  # target file for the atomic write
        # Pre-seed a stale v2 file so ensure_fresh takes the refresh + write path.
        _write_min_cenr_file(cenr_path, ["chi1-2.sme.zscaler.net", "chi1-2-vpn.zscaler.net", "silent.zs"])

        # The refreshed dict is what the write-path merger will decorate.
        refreshed = {
            "schema_version": 3,  # merge_clouds already emits v3
            "fetched_utc": _fresh_ts(),  # fresh so a re-read short-circuits
            "proxy_hostnames": [
                {"host": "chi1-2.sme.zscaler.net"},  # HTTPS observation expected
                {"host": "silent.zs"},  # no observation expected
            ],
            "vpn_hostnames": [
                {"host": "chi1-2-vpn.zscaler.net"},  # UDP/500 observation expected
            ],
            "by_city": {},
        }
        _install_refresh_returning(monkeypatch, refreshed)

        # Fake validation results: one HTTPS, one UDP/500, one silent.
        results = [
            _make_probe_result(
                "chi1-2.sme.zscaler.net",
                tcp={443: "open"},
                https_status=200,
                responding_protocols=["HTTPS"],
            ),
            _make_probe_result(
                "chi1-2-vpn.zscaler.net",
                udp={500: "open"},
                responding_protocols=["UDP/500"],
            ),
            _make_probe_result("silent.zs"),  # nothing responded
        ]
        monkeypatch.setattr(zc_mod, "run_full_validation", lambda *_a, **_kw: results)

        stale_in_memory = json.loads(cenr_path.read_text(encoding="utf-8"))  # freshness gate input
        zc_mod.ensure_fresh(cenr_path, stale_in_memory)

        # Re-read the file to prove the observations were persisted (not merely in memory).
        on_disk = json.loads(cenr_path.read_text(encoding="utf-8"))
        assert on_disk["schema_version"] == 3

        by_host = {entry["host"]: entry for entry in on_disk["proxy_hostnames"]}
        by_host.update({entry["host"]: entry for entry in on_disk["vpn_hostnames"]})

        assert by_host["chi1-2.sme.zscaler.net"]["observed_protocol"] == "HTTPS"
        assert by_host["chi1-2.sme.zscaler.net"]["observed_port"] == 443
        assert isinstance(by_host["chi1-2.sme.zscaler.net"].get("last_probed"), str)

        assert by_host["chi1-2-vpn.zscaler.net"]["observed_protocol"] == "UDP/500"
        assert by_host["chi1-2-vpn.zscaler.net"]["observed_port"] == 500
        assert isinstance(by_host["chi1-2-vpn.zscaler.net"].get("last_probed"), str)

        # Silent host: observation fields present but null (contract §Per-Host Entry).
        silent = by_host["silent.zs"]
        assert silent.get("observed_protocol") is None
        assert silent.get("observed_port") is None
        assert silent.get("last_probed") is None

    def test_schema_v2_compat_load_produces_null_observations(self, caplog):
        """T022 [US3]: v2 fixture loads clean and every host has null observations.

        Why:
            Contract §Backward-Compatibility Adapter requires that a freshly-
            promoted v2 document yields entries whose observation fields are
            all absent/None -- observations never appear out of thin air.
        """
        fixtures = Path(__file__).parent / "fixtures"
        cenr_v2 = json.loads((fixtures / "zscaler_cenr_hostnames_v2.json").read_text(encoding="utf-8"))
        assert cenr_v2.get("schema_version") != 3, "fixture must be v2 for this test to matter"

        with caplog.at_level("INFO", logger="src.utils.zscaler_catalogue"):
            promoted = zc_mod.promote_cache_document(cenr_v2, kind="cenr")

        for bag_key in ("proxy_hostnames", "vpn_hostnames"):
            for entry in promoted.get(bag_key) or []:
                assert isinstance(entry, dict)
                assert entry.get("observed_protocol") in (None, ""), entry
                assert entry.get("observed_port") in (None, 0) or entry.get("observed_port") is None
                assert entry.get("last_probed") in (None, "") or entry.get("last_probed") is None

        # Contract §Logging: exactly one INFO line per load with the fixed format.
        info_lines = [r for r in caplog.records if r.levelname == "INFO" and r.name == "src.utils.zscaler_catalogue"]
        assert len(info_lines) == 1, f"expected exactly 1 INFO line; got {len(info_lines)}"
        assert "loaded v" in info_lines[0].getMessage()
        assert "observations absent" in info_lines[0].getMessage()

    def test_zcc_probes_file_gets_same_v3_shape_under_roles_fqdns(self, monkeypatch, tmp_path):
        """T023 [US3]: the ZCC probes file receives the same v3 observation triplet.

        Why:
            The ZCC file uses ``roles[*].fqdns`` as its host bag. Contract
            §v3 Top-Level Shape (ZCC) requires the exact same per-host object
            shape, so the write-path merger must decorate those entries too.
        """
        cenr_path = tmp_path / "zscaler_cenr_hostnames.json"
        _write_min_cenr_file(cenr_path, ["placeholder.zs"])
        probes_path = tmp_path / "zscaler_client_connector_probes.json"
        probes_v2 = {
            "schema_version": 2,
            "roles": [
                {
                    "role": "zcc_health",
                    "description": "core zcc reachability",
                    "critical": True,
                    "fqdns": ["gateway.zscaler.net", "mobile.zscaler.net"],
                }
            ],
        }
        probes_path.write_text(json.dumps(probes_v2), encoding="utf-8")

        refreshed = {
            "schema_version": 3,
            "fetched_utc": _fresh_ts(),
            "proxy_hostnames": [{"host": "placeholder.zs"}],
            "vpn_hostnames": [],
            "by_city": {},
        }
        _install_refresh_returning(monkeypatch, refreshed)

        results = [
            _make_probe_result(
                "gateway.zscaler.net",
                tcp={443: "open"},
                https_status=200,
                responding_protocols=["HTTPS"],
            ),
            _make_probe_result("mobile.zscaler.net"),
        ]
        monkeypatch.setattr(zc_mod, "run_full_validation", lambda *_a, **_kw: results)

        stale_in_memory = json.loads(cenr_path.read_text(encoding="utf-8"))
        zc_mod.ensure_fresh(cenr_path, stale_in_memory)

        # The probes file MUST have been rewritten to v3 with observation fields.
        rewritten = json.loads(probes_path.read_text(encoding="utf-8"))
        assert rewritten.get("schema_version") == 3
        roles_iter = rewritten.get("roles") or []
        assert roles_iter, "ZCC probes file must retain its roles bag"
        flattened: dict[str, dict[str, Any]] = {}
        for role_body in roles_iter:
            for entry in role_body.get("fqdns") or []:
                assert isinstance(entry, dict) and "host" in entry
                flattened[entry["host"]] = entry
        assert flattened["gateway.zscaler.net"]["observed_protocol"] == "HTTPS"
        assert flattened["gateway.zscaler.net"]["observed_port"] == 443
        # Silent ZCC host still records null observation fields.
        assert flattened["mobile.zscaler.net"].get("observed_protocol") is None
        assert flattened["mobile.zscaler.net"].get("observed_port") is None

    def test_stale_observation_replaced_on_refresh(self, monkeypatch, tmp_path):
        """T024 [US3]: an old cached observation is overwritten by the fresh probe.

        Why:
            Acceptance Scenario 3 of US3 says a refresh MUST replace whatever
            observation the previous cycle wrote, so a Zscaler pop that flipped
            from HTTPS to UDP/500 propagates within the next refresh cycle.
        """
        cenr_path = tmp_path / "zscaler_cenr_hostnames.json"
        # Pre-seed a v3 doc with a STALE-BUT-PRESENT observation for the VPN host.
        preseeded = {
            "schema_version": 3,
            "fetched_utc": _stale_ts(),  # forces refresh path
            "proxy_hostnames": [],
            "vpn_hostnames": [
                {
                    "host": "chi1-2-vpn.zscaler.net",
                    "observed_protocol": "HTTPS",  # WRONG on purpose -- must be overwritten
                    "observed_port": 443,
                    "last_probed": "1999-01-01T00:00:00Z",
                }
            ],
            "by_city": {},
        }
        cenr_path.write_text(json.dumps(preseeded), encoding="utf-8")

        refreshed = {
            "schema_version": 3,
            "fetched_utc": _fresh_ts(),
            "proxy_hostnames": [],
            "vpn_hostnames": [{"host": "chi1-2-vpn.zscaler.net"}],
            "by_city": {},
        }
        _install_refresh_returning(monkeypatch, refreshed)

        results = [
            _make_probe_result(
                "chi1-2-vpn.zscaler.net",
                udp={500: "open"},
                responding_protocols=["UDP/500"],
            )
        ]
        monkeypatch.setattr(zc_mod, "run_full_validation", lambda *_a, **_kw: results)

        stale_in_memory = json.loads(cenr_path.read_text(encoding="utf-8"))
        zc_mod.ensure_fresh(cenr_path, stale_in_memory)

        on_disk = json.loads(cenr_path.read_text(encoding="utf-8"))
        vpn_entry = on_disk["vpn_hostnames"][0]
        assert (
            vpn_entry["observed_protocol"] == "UDP/500"
        ), "stale HTTPS observation was not replaced by fresh UDP/500 probe"
        assert vpn_entry["observed_port"] == 500
        assert vpn_entry["last_probed"] != "1999-01-01T00:00:00Z"

    def test_malformed_cache_file_falls_through_to_refresh_without_crash(self, monkeypatch, tmp_path):
        """T025 [US3]: a truncated JSON on disk MUST NOT crash the refresh flow.

        Why:
            Spec Edge Cases: Malformed cache file. Menu 206 must never die on
            a corrupted cache -- the freshness gate treats the in-memory dict
            (empty here) as stale and re-fetches. We prove no exception
            escapes and the fresh dict is persisted successfully.
        """
        cenr_path = tmp_path / "zscaler_cenr_hostnames.json"
        cenr_path.write_text('{"schema_version": 2, "proxy_hostnames": ["a.zs"', encoding="utf-8")  # truncated

        refreshed = {
            "schema_version": 3,
            "fetched_utc": _fresh_ts(),
            "proxy_hostnames": [{"host": "a.zs"}],
            "vpn_hostnames": [],
            "by_city": {},
        }
        _install_refresh_returning(monkeypatch, refreshed)
        monkeypatch.setattr(zc_mod, "run_full_validation", lambda *_a, **_kw: [])

        # We pass an empty dict as the in-memory copy to simulate the caller having
        # noticed the file was garbage and starting from scratch. ensure_fresh MUST
        # NOT raise; it should refresh and persist the merged doc.
        try:
            result = zc_mod.ensure_fresh(cenr_path, {})
        except Exception as exc:  # noqa: BLE001 -- test asserts non-raise
            pytest.fail(f"ensure_fresh raised on malformed cache path: {exc}")
        assert isinstance(result, dict)
        assert result.get("schema_version") == 3

    def test_write_path_priority_https_beats_udp_when_both_open(self, monkeypatch, tmp_path):
        """T026 [US3]: hybrid host with HTTPS AND UDP/500 open resolves to HTTPS.

        Why:
            Contract §Write Path priority table (R-003). A host that answers
            HTTPS on 443 while ALSO answering IKE on 500 must persist as HTTPS
            because that's what the URL builder wants to hit -- IKE is only
            relevant when nothing on TCP responds.
        """
        cenr_path = tmp_path / "zscaler_cenr_hostnames.json"
        _write_min_cenr_file(cenr_path, ["hybrid.zs"])

        refreshed = {
            "schema_version": 3,
            "fetched_utc": _fresh_ts(),
            "proxy_hostnames": [{"host": "hybrid.zs"}],
            "vpn_hostnames": [],
            "by_city": {},
        }
        _install_refresh_returning(monkeypatch, refreshed)

        results = [
            _make_probe_result(
                "hybrid.zs",
                tcp={443: "open"},
                udp={500: "open"},
                https_status=200,
                responding_protocols=["HTTPS", "UDP/500"],  # both live
            )
        ]
        monkeypatch.setattr(zc_mod, "run_full_validation", lambda *_a, **_kw: results)

        stale_in_memory = json.loads(cenr_path.read_text(encoding="utf-8"))
        zc_mod.ensure_fresh(cenr_path, stale_in_memory)

        on_disk = json.loads(cenr_path.read_text(encoding="utf-8"))
        entry = on_disk["proxy_hostnames"][0]
        assert entry["observed_protocol"] == "HTTPS", "HTTPS must beat UDP when both open (R-003)"
        assert entry["observed_port"] == 443
