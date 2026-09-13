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
        assert any("zscloud.net" in w for w in warnings)
        assert any("zscalerbeta.net" in w for w in warnings)
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


def _load_v2_fixture(name: str) -> dict[str, Any]:
    """Load a legacy Zscaler cache fixture.

    Why:
        Promotion tests must start with v2 data so the adapter does real work.
    """
    fixtures = Path(__file__).parent / "fixtures"  # Read fixtures that live beside this test module.
    return json.loads((fixtures / name).read_text(encoding="utf-8"))  # Load the fixture as an editable dict.


def _promote_v2_fixture(name: str, kind: str, caplog: pytest.LogCaptureFixture) -> dict[str, Any]:
    """Promote one legacy fixture and capture its log.

    Why:
        Each test needs the same precondition and the same INFO capture level.
    """
    legacy_doc = _load_v2_fixture(name)  # Load fresh data so tests do not share mutations.
    assert legacy_doc.get("schema_version") != 3  # Prove the fixture is still legacy-shaped.
    with caplog.at_level("INFO", logger="src.utils.zscaler_catalogue"):  # Capture the promotion notice.
        promoted_doc = zc_mod.promote_cache_document(legacy_doc, kind=kind)  # Convert v2 cache data to v3 shape.
    assert promoted_doc["schema_version"] == 3  # Prove the adapter stamped the v3 schema.
    return promoted_doc  # Return the promoted document for focused assertions.


def _assert_fresh_promotion_entry(entry: Any, bag_key: str) -> None:
    """Assert that one promoted host entry has the v3 empty-observation shape.

    Why:
        A freshly promoted entry must add the host key without invented probe
        observations.
    """
    assert isinstance(entry, dict), f"non-dict entry in {bag_key}: {entry!r}"  # Require the v3 object shape.
    _assert_host_key(entry)  # Require a usable host value.
    _assert_absent_or_none(entry, "observed_protocol")  # Keep observations absent.
    _assert_absent_or_none(entry, "observed_port")  # Keep the observed port empty.
    _assert_absent_or_none(entry, "last_probed")  # Keep the probe time empty.


def _assert_host_key(entry: dict[str, Any]) -> None:
    """Assert that a promoted entry has a usable host key.

    Why:
        The probe target builder needs a non-empty host string.
    """
    assert "host" in entry  # Require the key that the v3 schema defines.
    assert isinstance(entry["host"], str)  # Require the host value type.
    assert entry["host"]  # Reject an empty host string.


def _assert_absent_or_none(entry: dict[str, Any], key: str) -> None:
    """Assert that an optional observation field has no value.

    Why:
        Promotion must not invent observations before a probe runs.
    """
    if key not in entry:  # Missing optional fields are valid for fresh promotion.
        return  # Leave the caller with a passing empty field check.
    assert entry[key] is None  # Present optional fields must hold a null value.


def _assert_top_level_cenr_entries(cenr_v3: dict[str, Any]) -> None:
    """Assert that all top-level CENR bags hold v3 host objects.

    Why:
        Menu 206 reads these bags when it builds synthetic probe targets.
    """
    for bag_key in ("proxy_hostnames", "vpn_hostnames"):  # Check both top-level CENR host lists.
        bag = cenr_v3.get(bag_key) or []  # Use the same absent-list fallback as callers.
        assert bag, f"fixture CENR bag {bag_key} was empty; test is meaningless"  # Keep the fixture meaningful.
        for entry in bag:  # Validate each promoted top-level host entry.
            _assert_fresh_promotion_entry(entry, bag_key)  # Reuse the shared v3 shape contract.


def _assert_city_cenr_entries(cenr_v3: dict[str, Any]) -> None:
    """Assert that all per-city CENR bags hold v3 host objects.

    Why:
        City-scoped host bags must promote with the same shape as top-level
        bags.
    """
    by_city = cenr_v3.get("by_city") or {}  # Read the city map with the existing absent-map fallback.
    assert by_city, "fixture must exercise the by_city bags too"  # Keep city coverage active.
    for entry in _city_cenr_entries(by_city):  # Walk each city host entry.
        assert isinstance(entry, dict)  # Preserve the original city entry shape assertion.
        assert "host" in entry  # Preserve the original city host key assertion.


def _city_cenr_entries(by_city: dict[str, Any]) -> list[Any]:
    """Return all host entries from city CENR bags.

    Why:
        City assertions should focus on entry shape, not nested bag traversal.
    """
    entries: list[Any] = []  # Collect city entries in fixture order.
    for city_slot in by_city.values():  # Walk each city entry in fixture order.
        entries.extend(_entries_from_city_slot(city_slot))  # Add entries from valid city slots.
    return entries  # Return the flattened city entry list.


def _entries_from_city_slot(city_slot: Any) -> list[Any]:
    """Return host entries from one city slot.

    Why:
        The loader tolerates malformed city slots, so this helper keeps that
        tolerance local.
    """
    if not isinstance(city_slot, dict):  # Ignore malformed slots the loader must tolerate.
        return []  # Match the old tolerant assertion behavior.
    entries: list[Any] = []  # Collect entries from both city bag names.
    for bag_key in ("proxy_hostnames", "vpn_hostnames"):  # Check both city host bag names.
        entries.extend(city_slot.get(bag_key, []) or [])  # Add present host entries only.
    return entries  # Return the entries for this city slot.


def _assert_zcc_role_entries(zcc_v3: dict[str, Any]) -> None:
    """Assert that all ZCC role FQDNs hold v3 host objects.

    Why:
        The ZCC schema stores role objects in a list, and each object owns an
        FQDN bag.
    """
    roles_iter = _zcc_roles(zcc_v3)  # Read and validate the role list.
    entries = _zcc_role_fqdn_entries(roles_iter)  # Flatten FQDN entries across role objects.
    assert entries, "ZCC promotion produced zero v3 fqdn dicts"  # Keep the fixture meaningful.
    for entry in entries:  # Walk each promoted FQDN object.
        assert isinstance(entry, dict)  # Preserve the original ZCC entry shape assertion.
        assert "host" in entry  # Preserve the original ZCC host key assertion.


def _zcc_roles(zcc_v3: dict[str, Any]) -> list[Any]:
    """Return the ZCC role list from a promoted cache document.

    Why:
        The fixture must include roles before FQDN entry assertions are useful.
    """
    roles_iter = zcc_v3.get("roles") or []  # Read role objects with the existing absent-list fallback.
    assert isinstance(roles_iter, list) and roles_iter, "ZCC fixture must have roles"  # Keep role coverage active.
    return roles_iter  # Return the validated role list.


def _zcc_role_fqdn_entries(roles_iter: list[Any]) -> list[Any]:
    """Return all FQDN entries from ZCC role objects.

    Why:
        The ZCC schema nests FQDN entries under role objects.
    """
    entries: list[Any] = []  # Collect FQDN entries in role order.
    for role_body in roles_iter:  # Walk each role object in fixture order.
        entries.extend(_entries_from_zcc_role(role_body))  # Add entries from valid role objects.
    return entries  # Return the flattened FQDN list.


def _entries_from_zcc_role(role_body: Any) -> list[Any]:
    """Return FQDN entries from one ZCC role object.

    Why:
        The loader tolerates malformed role slots, so this helper keeps that
        tolerance local.
    """
    if not isinstance(role_body, dict):  # Ignore malformed slots the loader must tolerate.
        return []  # Match the old tolerant assertion behavior.
    return list(role_body.get("fqdns", []) or [])  # Return entries under the role FQDN bag.


def _assert_promotion_info_lines(caplog: pytest.LogCaptureFixture, expected_count: int) -> None:
    """Assert that promotion emitted the expected INFO lines.

    Why:
        The loader must warn once for each legacy document and stay quiet for
        already promoted documents.
    """
    info_lines = _catalogue_info_records(caplog)  # Filter catalogue INFO lines.
    count_message = f"expected {expected_count} INFO lines, got {len(info_lines)}"  # Explain a count failure.
    assert len(info_lines) == expected_count, count_message  # Check the count.
    for record in info_lines:  # Inspect each emitted promotion line.
        _assert_promotion_record(record)  # Verify the promotion message shape.


def _catalogue_info_records(caplog: pytest.LogCaptureFixture) -> list[Any]:
    """Return INFO records from the Zscaler catalogue logger.

    Why:
        Promotion tests must ignore unrelated loggers.
    """
    return [
        r for r in caplog.records if r.levelname == "INFO" and r.name == "src.utils.zscaler_catalogue"
    ]  # Preserve the old log filter.


def _assert_promotion_record(record: Any) -> None:
    """Assert the required legacy promotion log text.

    Why:
        Operators need the version marker and the missing-observation note.
    """
    message = record.getMessage()  # Read the rendered log message once.
    assert "loaded v" in message  # Require the legacy version marker.
    assert "observations absent" in message  # Require the missing-observation message.


def test_v2_cenr_cache_promotes_top_level_bags(caplog: pytest.LogCaptureFixture) -> None:
    """A v2 CENR cache promotes top-level host bags to v3.

    Why:
        The loader adapter must convert legacy CENR host strings before menu
        206 builds synthetic probe targets.
    """
    cenr_v3 = _promote_v2_fixture("zscaler_cenr_hostnames_v2.json", "cenr", caplog)  # Promote the CENR fixture.
    _assert_top_level_cenr_entries(cenr_v3)  # Verify the top-level host bags.
    _assert_promotion_info_lines(caplog, 1)  # Verify the promotion notice.


def test_v2_cenr_cache_promotes_city_bags(caplog: pytest.LogCaptureFixture) -> None:
    """A v2 CENR cache promotes per-city host bags to v3.

    Why:
        City host bags feed regional targets and must not keep legacy strings.
    """
    cenr_v3 = _promote_v2_fixture("zscaler_cenr_hostnames_v2.json", "cenr", caplog)  # Promote the CENR fixture.
    _assert_city_cenr_entries(cenr_v3)  # Verify city host bags.
    _assert_promotion_info_lines(caplog, 1)  # Verify the promotion notice.


def test_v2_zcc_cache_promotes_role_fqdns(caplog: pytest.LogCaptureFixture) -> None:
    """A v2 ZCC cache promotes role FQDN bags to v3.

    Why:
        ZCC role FQDNs must become host objects before the probe target builder
        reads them.
    """
    zcc_v3 = _promote_v2_fixture("zscaler_client_connector_probes_v2.json", "zcc", caplog)  # Promote the ZCC fixture.
    _assert_zcc_role_entries(zcc_v3)  # Verify role FQDN host objects.
    _assert_promotion_info_lines(caplog, 1)  # Verify the promotion notice.


def test_v3_cache_promotion_is_silent(caplog: pytest.LogCaptureFixture) -> None:
    """A promoted v3 cache does not emit a second promotion message.

    Why:
        The loader must log once for legacy cache use and stay silent on a
        later v3 load.
    """
    cenr_v3 = _promote_v2_fixture("zscaler_cenr_hostnames_v2.json", "cenr", caplog)  # Create one promoted CENR doc.
    zcc_v3 = _promote_v2_fixture(
        "zscaler_client_connector_probes_v2.json", "zcc", caplog
    )  # Create one promoted ZCC doc.
    _assert_promotion_info_lines(caplog, 2)  # Verify both first-promotion notices.
    caplog.clear()  # Remove first-promotion log records before the silent check.
    with caplog.at_level("INFO", logger="src.utils.zscaler_catalogue"):  # Capture any unexpected idempotency notices.
        zc_mod.promote_cache_document(cenr_v3, kind="cenr")  # Re-promote the CENR v3 document.
        zc_mod.promote_cache_document(zcc_v3, kind="zcc")  # Re-promote the ZCC v3 document.
    assert [r for r in caplog.records if r.levelname == "INFO"] == []  # Require silence for v3 re-promotion.


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


def _write_observation_refresh_fixture(cenr_path: Path) -> dict[str, Any]:
    """Write a CENR fixture for the observation persistence path.

    Why:
        The test needs one HTTPS host, one UDP host, and one silent host to
        cover the priority table.
    """
    _write_min_cenr_file(  # Seed a stale v2 file so ensure_fresh rewrites it.
        cenr_path,  # Use the test-specific cache path.
        ["chi1-2.sme.zscaler.net", "chi1-2-vpn.zscaler.net", "silent.zs"],  # Cover each observation result type.
    )
    return {
        "schema_version": 3,  # Simulate merge_clouds output.
        "fetched_utc": _fresh_ts(),  # Prevent a second refresh after the write.
        "proxy_hostnames": [{"host": "chi1-2.sme.zscaler.net"}, {"host": "silent.zs"}],  # Keep proxy hosts grouped.
        "vpn_hostnames": [{"host": "chi1-2-vpn.zscaler.net"}],  # Keep the UDP host in the VPN bag.
        "by_city": {},  # Keep this fixture focused on top-level persistence.
    }


def _mixed_observation_results() -> list[Any]:
    """Build probe results that cover HTTPS, UDP, and silent endpoints.

    Why:
        The observation merger chooses a value from the first responsive
        protocol, so the test needs each important class.
    """
    return [
        _make_probe_result(  # Build the HTTPS responder.
            "chi1-2.sme.zscaler.net",  # Match the proxy host in the fixture.
            tcp={443: "open"},  # Mark HTTPS TCP as available.
            https_status=200,  # Show that the HTTPS request received a response.
            responding_protocols=["HTTPS"],  # Let the merger choose HTTPS.
        ),
        _make_probe_result(  # Build the UDP responder.
            "chi1-2-vpn.zscaler.net",  # Match the VPN host in the fixture.
            udp={500: "open"},  # Mark IKE UDP as available.
            responding_protocols=["UDP/500"],  # Let the merger choose UDP/500.
        ),
        _make_probe_result("silent.zs"),  # Keep one host without observations.
    ]


def _load_cenr_hosts_by_name(cenr_path: Path) -> dict[str, dict[str, Any]]:
    """Load a CENR cache and return host entries by name.

    Why:
        Observation tests assert host fields, not list order.
    """
    on_disk = json.loads(cenr_path.read_text(encoding="utf-8"))  # Read the persisted cache after ensure_fresh.
    assert on_disk["schema_version"] == 3  # Prove the write path stored a v3 document.
    by_host = {entry["host"]: entry for entry in on_disk["proxy_hostnames"]}  # Index proxy entries by host.
    by_host.update({entry["host"]: entry for entry in on_disk["vpn_hostnames"]})  # Add VPN entries to the same index.
    return by_host  # Return a combined view for concise assertions.


def _assert_observation(entry: dict[str, Any], protocol: str | None, port: int | None) -> None:
    """Assert the persisted observation fields for one host.

    Why:
        The test uses the same contract for responsive and silent hosts.
    """
    assert entry.get("observed_protocol") == protocol  # Verify the selected protocol or the silent marker.
    assert entry.get("observed_port") == port  # Verify the selected port or the silent marker.
    if protocol is None:  # Silent hosts must not invent a probe time.
        assert entry.get("last_probed") is None  # Keep the no-observation timestamp empty.
    else:  # Responsive hosts must record when the probe occurred.
        assert isinstance(entry.get("last_probed"), str)  # Verify that the write path stored a timestamp string.


def _assert_null_observation_bags(promoted: dict[str, Any]) -> None:
    """Assert that promoted CENR bags do not invent observations.

    Why:
        A load-only promotion must not create probe data.
    """
    for bag_key in ("proxy_hostnames", "vpn_hostnames"):  # Check the two top-level CENR bags.
        for entry in promoted.get(bag_key) or []:  # Walk each promoted host entry.
            assert isinstance(entry, dict)  # Require the v3 object shape.
            assert entry.get("observed_protocol") in (None, ""), entry  # Permit only empty protocol values.
            assert entry.get("observed_port") in (None, 0) or entry.get("observed_port") is None  # Permit empty ports.
            assert entry.get("last_probed") in (None, "") or entry.get("last_probed") is None  # Permit empty times.


def _write_zcc_v2_fixture(probes_path: Path) -> None:
    """Write a ZCC v2 fixture to the requested path.

    Why:
        The observation write path must also update the ZCC cache file.
    """
    probes_v2 = {
        "schema_version": 2,  # Force ZCC promotion during ensure_fresh.
        "roles": [  # Keep one role because the merger walks roles[*].fqdns.
            {
                "role": "zcc_health",  # Preserve the role name used in assertions.
                "description": "core zcc reachability",  # Preserve role metadata.
                "critical": True,  # Preserve role metadata.
                "fqdns": ["gateway.zscaler.net", "mobile.zscaler.net"],  # Cover responsive and silent ZCC hosts.
            }
        ],
    }
    probes_path.write_text(json.dumps(probes_v2), encoding="utf-8")  # Persist the v2 ZCC cache beside the CENR cache.


def _zcc_observation_results() -> list[Any]:
    """Build ZCC probe results for one responsive and one silent host.

    Why:
        The ZCC observation path must write both populated and empty fields.
    """
    return [
        _make_probe_result(  # Build the responsive ZCC host.
            "gateway.zscaler.net",  # Match the first fixture FQDN.
            tcp={443: "open"},  # Mark HTTPS TCP as available.
            https_status=200,  # Show that HTTPS returned a response.
            responding_protocols=["HTTPS"],  # Let the merger choose HTTPS.
        ),
        _make_probe_result("mobile.zscaler.net"),  # Keep one ZCC host silent.
    ]


def _load_zcc_hosts_by_name(probes_path: Path) -> dict[str, dict[str, Any]]:
    """Load a ZCC cache and return FQDN entries by host name.

    Why:
        The ZCC cache nests FQDN entries under role objects.
    """
    rewritten = json.loads(probes_path.read_text(encoding="utf-8"))  # Read the rewritten ZCC cache file.
    assert rewritten.get("schema_version") == 3  # Prove the write path stored a v3 document.
    roles_iter = rewritten.get("roles") or []  # Read the role list with the existing absent-list fallback.
    assert roles_iter, "ZCC probes file must retain its roles bag"  # Keep role coverage active.
    flattened: dict[str, dict[str, Any]] = {}  # Build a lookup by host name.
    for role_body in roles_iter:  # Walk each role object in fixture order.
        for entry in role_body.get("fqdns") or []:  # Walk FQDN entries under this role.
            assert isinstance(entry, dict) and "host" in entry  # Require the v3 object shape.
            flattened[entry["host"]] = entry  # Store the entry for direct assertions.
    return flattened  # Return all ZCC FQDN entries by host.


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
        cenr_path = tmp_path / "zscaler_cenr_hostnames.json"  # Target file for the atomic write.
        refreshed = _write_observation_refresh_fixture(cenr_path)  # Seed the stale input and build refreshed data.
        _install_refresh_returning(monkeypatch, refreshed)  # Stub the network refresh step.
        monkeypatch.setattr(
            zc_mod, "run_full_validation", lambda *_a, **_kw: _mixed_observation_results()
        )  # Stub probe output.

        stale_in_memory = json.loads(cenr_path.read_text(encoding="utf-8"))  # Load freshness gate input.
        zc_mod.ensure_fresh(cenr_path, stale_in_memory)  # Run the refresh, merge, and write path.

        by_host = _load_cenr_hosts_by_name(cenr_path)  # Re-read the file to prove persistence.
        _assert_observation(by_host["chi1-2.sme.zscaler.net"], "HTTPS", 443)  # Verify the HTTPS observation.
        _assert_observation(by_host["chi1-2-vpn.zscaler.net"], "UDP/500", 500)  # Verify the UDP observation.
        _assert_observation(by_host["silent.zs"], None, None)  # Verify the silent host fields.

    def test_schema_v2_compat_load_produces_null_observations(self, caplog):
        """T022 [US3]: v2 fixture loads clean and every host has null observations.

        Why:
            Contract §Backward-Compatibility Adapter requires that a freshly-
            promoted v2 document yields entries whose observation fields are
            all absent/None -- observations never appear out of thin air.
        """
        promoted = _promote_v2_fixture(
            "zscaler_cenr_hostnames_v2.json", "cenr", caplog
        )  # Promote the legacy CENR fixture.
        _assert_null_observation_bags(promoted)  # Verify that promotion does not invent probe observations.
        _assert_promotion_info_lines(caplog, 1)  # Verify the promotion notice.

    def test_zcc_probes_file_gets_same_v3_shape_under_roles_fqdns(self, monkeypatch, tmp_path):
        """T023 [US3]: the ZCC probes file receives the same v3 observation triplet.

        Why:
            The ZCC file uses ``roles[*].fqdns`` as its host bag. Contract
            §v3 Top-Level Shape (ZCC) requires the exact same per-host object
            shape, so the write-path merger must decorate those entries too.
        """
        cenr_path = tmp_path / "zscaler_cenr_hostnames.json"  # Build the CENR cache path that ensure_fresh requires.
        _write_min_cenr_file(cenr_path, ["placeholder.zs"])  # Seed a minimal stale CENR file.
        probes_path = tmp_path / "zscaler_client_connector_probes.json"  # Build the sibling ZCC cache path.
        _write_zcc_v2_fixture(probes_path)  # Seed the legacy ZCC cache file.
        refreshed = _write_observation_refresh_fixture(cenr_path)  # Build refreshed CENR data for the write path.
        _install_refresh_returning(monkeypatch, refreshed)  # Stub the CENR refresh.
        monkeypatch.setattr(
            zc_mod, "run_full_validation", lambda *_a, **_kw: _zcc_observation_results()
        )  # Stub ZCC probes.

        stale_in_memory = json.loads(cenr_path.read_text(encoding="utf-8"))  # Load freshness gate input.
        zc_mod.ensure_fresh(cenr_path, stale_in_memory)  # Run the refresh path that updates both cache files.

        flattened = _load_zcc_hosts_by_name(probes_path)  # Re-read the ZCC cache to prove persistence.
        _assert_observation(flattened["gateway.zscaler.net"], "HTTPS", 443)  # Verify the responsive ZCC host.
        _assert_observation(flattened["mobile.zscaler.net"], None, None)  # Verify the silent ZCC host.

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
        protocol_message = "stale HTTPS observation was not replaced by fresh UDP/500 probe"  # Explain protocol drift.
        assert vpn_entry["observed_protocol"] == "UDP/500", protocol_message  # Verify the fresh protocol value.
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
        except Exception as exc:  # test asserts non-raise
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
