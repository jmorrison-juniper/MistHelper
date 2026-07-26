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
        assert merged["proxy_hostnames"] == ["a.example.com", "b.example.com", "c.example.com"]

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
        assert entry["proxy_hostnames"] == ["lon1.zs.example", "lon2.zs.example"]
        assert entry["vpn_hostnames"] == ["vpn1"]
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
        assert merged["schema_version"] == 2

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
        assert merged["proxy_hostnames"] == ["a"]

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
        assert merged["proxy_hostnames"] == ["also-good", "good"]
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
        assert fresh["proxy_hostnames"] == ["p.zs"]
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
        assert seen["probes"] == {"roles": []}

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
        assert seen["probes"] == {}

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
