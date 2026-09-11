"""Tests for the metric catalog and the Mist collector."""

from __future__ import annotations

import re
from typing import Any

from src.metrics_gateway.catalog import MetricCatalog, MetricKind, MetricScope
from src.metrics_gateway.collector import MistMetricsCollector, MistStatsReader
from src.metrics_gateway.prometheus import NAME_PATTERN
from src.metrics_gateway.samples import MetricSnapshot
from tests.unit.metrics_gateway.conftest import ORG_ID, SITE_A, SITE_B, StubResponse, build_overrides


def _collect(overrides: dict[str, Any], site_ids: tuple[str, ...] = ()) -> MetricSnapshot:
    """Run one collector pass against the stand-in endpoints.

    Args:
        overrides: The endpoint callables.
        site_ids: The site filter to apply.

    Returns:
        The snapshot of the pass.
    """
    reader = MistStatsReader(session=None, overrides=overrides)
    return MistMetricsCollector(reader, ORG_ID, site_ids).collect()


def _value(snapshot: MetricSnapshot, name: str, row_key: str = "") -> float | None:
    """Read one value out of a snapshot.

    Args:
        snapshot: The snapshot to search.
        name: The metric name.
        row_key: The row identity, empty for a scalar.

    Returns:
        The value, or None when the snapshot holds no such reading.
    """
    for sample in snapshot.samples:
        if sample.definition.name == name and sample.row_key == row_key:
            return sample.value
    return None


class TestMetricCatalog:
    """The catalog must give every reading one name and one address."""

    def test_every_name_is_unique(self) -> None:
        """A duplicate name would make one reading unreachable."""
        catalog = MetricCatalog()
        names = catalog.names()
        assert len(names) == len(set(names))

    def test_every_name_matches_the_prometheus_grammar(self) -> None:
        """A name that breaks the grammar makes a scraper drop the whole response."""
        for name in MetricCatalog().names():
            assert NAME_PATTERN.match(name), f"The metric name {name} breaks the Prometheus grammar."

    def test_every_column_is_unique_within_a_scope(self) -> None:
        """Two readings at one OID would hide one of them from a walk."""
        catalog = MetricCatalog()
        for scope in MetricScope:
            columns = [definition.column for definition in catalog.for_scope(scope)]
            assert len(columns) == len(set(columns)), f"The scope {scope} reuses a column number."

    def test_help_text_reads_as_a_sentence(self) -> None:
        """A NOC engineer reads the help text beside the alarm, so it must be a sentence."""
        for name in MetricCatalog().names():
            definition = MetricCatalog().by_name(name)
            assert definition is not None
            assert definition.help_text.endswith("."), f"The help text of {name} is not a sentence."

    def test_an_unknown_name_returns_nothing(self) -> None:
        """A lookup of a name the catalog never defined must not raise."""
        assert MetricCatalog().by_name("mist_not_a_metric") is None


class TestCollectorOrgReadings:
    """The organization pass must copy the counts and derive the ratios."""

    def test_it_copies_the_org_counts(self, endpoint_overrides: dict[str, Any]) -> None:
        """A count that Mist reports must reach the snapshot unchanged."""
        snapshot = _collect(endpoint_overrides)
        assert _value(snapshot, "mist_org_sites") == 2
        assert _value(snapshot, "mist_org_devices_connected") == 2
        assert _value(snapshot, "mist_org_devices_disconnected") == 1

    def test_it_derives_the_service_level_ratio(self, endpoint_overrides: dict[str, Any]) -> None:
        """The gateway divides once, so every monitoring system reads the same ratio."""
        snapshot = _collect(endpoint_overrides)
        assert _value(snapshot, "mist_org_sle_ratio", "coverage") == 0.97
        assert _value(snapshot, "mist_org_sle_ratio", "capacity") == 1.0

    def test_a_zero_denominator_produces_no_ratio(self) -> None:
        """A division by zero must not raise, and it must not report a false 0."""
        payload = {"name": "Empty", "sle": [{"path": "coverage", "user_minutes": {"total": 0, "ok": 0}}]}
        snapshot = _collect(build_overrides(org=payload, sites=[], devices=[]))
        assert _value(snapshot, "mist_org_sle_ratio", "coverage") is None

    def test_an_org_reading_is_a_scalar(self, endpoint_overrides: dict[str, Any]) -> None:
        """An organization reading is an SNMP scalar, so it must carry no row identity."""
        snapshot = _collect(endpoint_overrides)
        assert snapshot.row_keys(MetricScope.ORG) == ()


class TestCollectorSiteReadings:
    """The site pass must produce one stable row for each site."""

    def test_rows_sort_by_site_identifier(self, endpoint_overrides: dict[str, Any]) -> None:
        """A stable row order gives the same SNMP row number to the same site on every refresh."""
        snapshot = _collect(endpoint_overrides)
        assert snapshot.row_keys(MetricScope.SITE) == (SITE_A, SITE_B)

    def test_it_copies_the_site_counts(self, endpoint_overrides: dict[str, Any]) -> None:
        """A site count must reach the snapshot unchanged."""
        snapshot = _collect(endpoint_overrides)
        assert _value(snapshot, "mist_site_clients", SITE_A) == 42
        assert _value(snapshot, "mist_site_aps_connected", SITE_B) == 0

    def test_a_missing_count_stays_absent(self, endpoint_overrides: dict[str, Any]) -> None:
        """A missing count must not become 0, because 0 devices reads as an outage."""
        snapshot = _collect(endpoint_overrides)
        assert _value(snapshot, "mist_site_switches", SITE_B) is None

    def test_the_site_filter_drops_every_other_site(self, endpoint_overrides: dict[str, Any]) -> None:
        """An operator who names one site must not receive a second one."""
        snapshot = _collect(endpoint_overrides, site_ids=(SITE_A,))
        assert snapshot.row_keys(MetricScope.SITE) == (SITE_A,)

    def test_the_site_filter_also_drops_the_devices(self, endpoint_overrides: dict[str, Any]) -> None:
        """A device of an excluded site must not reach the snapshot either."""
        snapshot = _collect(endpoint_overrides, site_ids=(SITE_A,))
        assert "aabbcc000003" not in snapshot.row_keys(MetricScope.DEVICE)


class TestCollectorDeviceReadings:
    """The device pass must cover the access point, the switch, and the gateway."""

    def test_rows_sort_by_mac_address(self, endpoint_overrides: dict[str, Any]) -> None:
        """A stable row order keeps the SNMP row number of a device fixed."""
        snapshot = _collect(endpoint_overrides)
        assert snapshot.row_keys(MetricScope.DEVICE) == ("2c6bf5000002", "5c5b350e0001", "aabbcc000003")

    def test_a_connected_device_reads_up(self, endpoint_overrides: dict[str, Any]) -> None:
        """The `up` reading is the one a NOC alerts on."""
        snapshot = _collect(endpoint_overrides)
        assert _value(snapshot, "mist_device_up", "5c5b350e0001") == 1.0
        assert _value(snapshot, "mist_device_up", "aabbcc000003") == 0.0

    def test_an_access_point_reports_processor_use_as_a_ratio(self, endpoint_overrides: dict[str, Any]) -> None:
        """Mist reports a percent, and a Prometheus ratio runs from 0 to 1."""
        snapshot = _collect(endpoint_overrides)
        assert _value(snapshot, "mist_device_cpu_utilization_ratio", "5c5b350e0001") == 0.37

    def test_a_switch_reports_processor_use_from_its_own_field(self, endpoint_overrides: dict[str, Any]) -> None:
        """A switch reports `cpu_stat.util`, and an access point reports `cpu_util`."""
        snapshot = _collect(endpoint_overrides)
        assert _value(snapshot, "mist_device_cpu_utilization_ratio", "2c6bf5000002") == 0.12

    def test_memory_arrives_in_bytes(self, endpoint_overrides: dict[str, Any]) -> None:
        """Mist reports kilobytes, and Prometheus expects the base unit."""
        snapshot = _collect(endpoint_overrides)
        assert _value(snapshot, "mist_device_memory_used_bytes", "5c5b350e0001") == 2048 * 1024

    def test_a_switch_reports_its_processor_temperature(self, endpoint_overrides: dict[str, Any]) -> None:
        """A NOC alerts on a hot switch, and the reading is nested in `environment`."""
        snapshot = _collect(endpoint_overrides)
        assert _value(snapshot, "mist_device_cpu_temperature_celsius", "2c6bf5000002") == 45

    def test_the_running_firmware_version_reaches_the_labels(self, endpoint_overrides: dict[str, Any]) -> None:
        """Issue #2006 requires the running version, which a statistics endpoint reports."""
        snapshot = _collect(endpoint_overrides)
        info = [s for s in snapshot.samples if s.definition.name == "mist_device_info" and s.row_key == "2c6bf5000002"]
        assert dict(info[0].labels)["version"] == "23.4R2-S3"

    def test_an_info_reading_carries_a_constant_one(self, endpoint_overrides: dict[str, Any]) -> None:
        """Prometheus holds an informational value at 1 and carries the text in the labels."""
        snapshot = _collect(endpoint_overrides)
        for sample in snapshot.samples:
            if sample.definition.kind is MetricKind.INFO:
                assert sample.value == 1.0


class TestCollectorFailures:
    """A Mist fault must become a failed snapshot and never an exception."""

    def test_a_raised_fault_produces_a_failed_snapshot(self) -> None:
        """The refresh thread must survive every fault a Mist call can raise."""

        def _boom(_session: Any, _org_id: str) -> StubResponse:
            raise ConnectionError("the cloud is unreachable")

        overrides = build_overrides()
        overrides["getOrgStats"] = _boom
        snapshot = _collect(overrides)
        assert snapshot.ok is False
        assert "unreachable" in snapshot.error

    def test_a_non_200_status_produces_an_empty_reading(self) -> None:
        """A failed call carries no reading, and the pass must not invent one."""
        overrides = build_overrides()
        overrides["getOrgStats"] = lambda _s, _o: StubResponse(None, status_code=401)
        snapshot = _collect(overrides)
        assert snapshot.ok is True
        assert _value(snapshot, "mist_org_sites") is None

    def test_a_record_that_is_not_a_mapping_is_dropped(self) -> None:
        """A malformed record must not stop the pass."""
        snapshot = _collect(build_overrides(sites=["not-a-record"]))  # type: ignore[list-item]
        assert snapshot.ok is True
        assert snapshot.row_keys(MetricScope.SITE) == ()

    def test_an_empty_snapshot_reports_itself_as_empty(self) -> None:
        """The cache needs to tell an empty start from a failed refresh."""
        assert MetricSnapshot().is_empty() is True

    def test_the_device_type_argument_asks_for_every_type(self, endpoint_overrides: dict[str, Any]) -> None:
        """Without `type=all` Mist returns the access points alone."""
        seen: dict[str, Any] = {}

        def _capture(_session: Any, _org_id: str, **kwargs: Any) -> StubResponse:
            seen.update(kwargs)
            return StubResponse([])

        endpoint_overrides["listOrgDevicesStats"] = _capture
        _collect(endpoint_overrides)
        assert seen["type"] == "all"


def test_a_label_value_never_holds_a_raw_quotation_mark(endpoint_overrides: dict[str, Any]) -> None:
    """A site name can hold a quotation mark, which the renderer must escape later."""
    snapshot = _collect(endpoint_overrides)
    names = [dict(s.labels).get("site_name", "") for s in snapshot.samples if s.definition.scope is MetricScope.SITE]
    assert 'Branch "A"' in names
    assert re.search(r'Branch "A"', "".join(names))
