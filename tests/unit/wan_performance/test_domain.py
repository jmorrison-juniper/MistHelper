"""Test the isolated WAN performance identity and measurement contracts."""

import json  # Check that domain records contain portable scalar data.
import math  # Supply values that JSON cannot represent safely.
from datetime import UTC, datetime, timedelta, timezone  # Build controlled UTC intervals.
from typing import Literal, cast  # Pass malformed runtime inputs through typed contracts.

import pytest  # Check invalid domain inputs without external services.

from src.interfaces.wan_performance.domain.identity import (  # Import the feature-owned identity types.
    CircuitIdentity,
    GatewayIdentity,
    PeerPathIdentity,
    SiteIdentity,
)
from src.interfaces.wan_performance.domain.measurement import (  # Import the feature-owned metric records.
    HourlyMeasurement,
    MetricMeasurement,
)

ORG_ID = "00000000-0000-0000-0000-000000000001"  # Use a synthetic organization identifier.
SITE_ID = "11111111-1111-1111-1111-111111111111"  # Use the documented synthetic route identifier.
HOUR_START = datetime(2024, 1, 1, 12, tzinfo=UTC)  # Keep fixture history fixed and historical.
COLLECTED_AT = HOUR_START + timedelta(hours=1)  # Keep collection time outside the measured hour.


def build_circuit() -> CircuitIdentity:
    """Build one synthetic circuit identity for independent domain tests."""
    site = SiteIdentity(org_id=ORG_ID, site_id=SITE_ID)  # Preserve both parent identifiers.
    gateway = GatewayIdentity(site=site, gateway_id="aabbccddeeff")  # Keep the opaque gateway identifier.
    return CircuitIdentity(gateway=gateway, port_name="ge-0/0/1")  # Preserve the canonical port name.


def test_identity_keys_preserve_parent_and_source_identifiers() -> None:
    """Keep the organization, site, gateway, and port in each natural key."""
    circuit = build_circuit()  # Build the route identity without a live lookup.

    assert circuit.natural_key == (ORG_ID, SITE_ID, "aabbccddeeff", "ge-0/0/1")  # Keep every route value exact.
    assert circuit.to_dict() == {  # Make identity serialization stable for later persistence work.
        "org_id": ORG_ID,
        "site_id": SITE_ID,
        "gateway_id": "aabbccddeeff",
        "port_name": "ge-0/0/1",
    }  # Exclude display labels from the natural identity.


def test_peer_identity_keeps_tunnel_paths_separate() -> None:
    """Keep peer and tunnel identity in the peer-path natural key."""
    circuit = build_circuit()  # Reuse the same parent context for the peer.
    peer = PeerPathIdentity(  # Build a path with an explicit opaque tunnel identity.
        gateway=circuit.gateway,
        port_name=circuit.port_name,
        peer_port_id="ge-0/0/1",
        peer_mac="11:22:33:44:55:66",
        tunnel_identity="synthetic-tunnel-1",
    )
    second_peer = PeerPathIdentity(  # Build a second path without merging its tunnel identity.
        gateway=circuit.gateway,
        port_name=circuit.port_name,
        peer_port_id="ge-0/0/1",
        peer_mac="11:22:33:44:55:66",
        tunnel_identity="synthetic-tunnel-2",
    )
    remote_port_peer = PeerPathIdentity(  # Keep the remote port in the stored natural key.
        gateway=circuit.gateway,
        port_name=circuit.port_name,
        peer_port_id="ge-0/0/2",
        peer_mac="11:22:33:44:55:66",
        tunnel_identity="synthetic-tunnel-1",
    )

    assert peer.natural_key != second_peer.natural_key  # Keep separate tunnels distinct.
    assert peer.natural_key != remote_port_peer.natural_key  # Keep distinct remote ports separate.
    assert peer.to_dict()["peer_mac"] == "11:22:33:44:55:66"  # Preserve the peer identifier.


def test_hourly_measurement_serializes_utc_identity_and_metrics() -> None:
    """Serialize one finite synthetic measurement with a stable hourly key."""
    measurement = HourlyMeasurement(  # Build the complete controlled measurement record.
        identity=build_circuit(),
        hour_start_utc=HOUR_START,
        collected_at_utc=COLLECTED_AT,
        metrics={"utilization": MetricMeasurement(value=42.5, unit="percent")},
        provenance="synthetic",
    )

    payload = measurement.to_dict()  # Convert domain values to JSON-compatible primitives.
    encoded = json.dumps(payload, allow_nan=False, sort_keys=True)  # Reject non-finite serialized values.

    assert measurement.natural_key[-1] == HOUR_START.isoformat()  # Include the UTC hour in the natural key.
    assert payload["provenance"] == "synthetic"  # Keep fixture origin explicit.
    assert json.loads(encoded)["metrics"]["utilization"]["value"] == 42.5  # Preserve the metric value.


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])  # Cover each non-finite number form.
def test_metric_rejects_non_finite_values(value: float) -> None:
    """Reject values that cannot represent a valid measurement."""
    with pytest.raises(ValueError, match="finite"):  # Require an explicit invalid-value refusal.
        MetricMeasurement(value=value, unit="percent")  # Prevent invalid values from entering a record.


def test_metric_requires_a_reason_when_value_is_missing() -> None:
    """Require a reason instead of treating missing data as zero."""
    with pytest.raises(ValueError, match="missing_reason"):  # Keep unsupported data distinct from a zero.
        MetricMeasurement(value=None, unit="percent")  # Reject an unexplained missing value.


@pytest.mark.parametrize("sample_count", [True, 1.5])  # Reject booleans and fractional sample counts.
def test_metric_rejects_non_integer_sample_counts(sample_count: int | float | bool) -> None:
    """Require a non-negative integer sample count."""
    with pytest.raises(ValueError, match="sample_count"):  # Refuse values outside the declared type.
        MetricMeasurement(  # Reject ambiguous sample totals.
            value=1.0,
            unit="percent",
            sample_count=cast(int, sample_count),
        )


def test_metric_rejects_boolean_coverage() -> None:
    """Reject boolean coverage even though booleans are integer subclasses."""
    with pytest.raises(ValueError, match="coverage_fraction"):  # Require an explicit fractional coverage value.
        MetricMeasurement(value=1.0, unit="percent", coverage_fraction=True)  # Reject true as a numeric fraction.


def test_measurement_rejects_non_string_metric_names() -> None:
    """Reject malformed metric names before string operations."""
    metrics = cast(dict[str, MetricMeasurement], {1: MetricMeasurement(value=1.0, unit="percent")})

    with pytest.raises(ValueError, match="named measurements"):  # Return a domain error instead of AttributeError.
        HourlyMeasurement(  # Validate keys before serializing the mapping.
            identity=build_circuit(),
            hour_start_utc=HOUR_START,
            collected_at_utc=COLLECTED_AT,
            metrics=metrics,
            provenance="synthetic",
        )


@pytest.mark.parametrize(
    "hour_start",
    [
        datetime(2024, 1, 1, 12, 1, tzinfo=UTC),
        datetime(2024, 1, 1, 12),
        datetime(2024, 1, 1, 12, tzinfo=timezone(timedelta(hours=1))),
    ],
)  # Reject partial, naive, and non-UTC hour identities.
def test_hourly_measurement_rejects_invalid_utc_hours(hour_start: datetime) -> None:
    """Require an hour-aligned timestamp with an explicit UTC offset."""
    with pytest.raises(ValueError):  # Refuse unverified or ambiguous time identities.
        HourlyMeasurement(  # Validate the interval before any storage or aggregation use.
            identity=build_circuit(),
            hour_start_utc=hour_start,
            collected_at_utc=COLLECTED_AT,
            metrics={"utilization": MetricMeasurement(value=42.5, unit="percent")},
            provenance="synthetic",
        )


def test_hourly_measurement_rejects_non_utc_collection_time() -> None:
    """Require collection timestamps to use UTC rather than a matching local offset."""
    local_time = COLLECTED_AT.astimezone(timezone(timedelta(hours=1)))  # Keep the same instant with a non-UTC zone.

    with pytest.raises(ValueError, match="collected_at_utc"):  # Refuse non-UTC source timestamps.
        HourlyMeasurement(  # Validate collection time before the record enters storage.
            identity=build_circuit(),
            hour_start_utc=HOUR_START,
            collected_at_utc=local_time,
            metrics={"utilization": MetricMeasurement(value=42.5, unit="percent")},
            provenance="synthetic",
        )


@pytest.mark.parametrize("site_id", ["../site", "", "has space"])  # Reject unsafe or empty source values.
def test_site_identity_rejects_invalid_identifiers(site_id: str) -> None:
    """Reject site identifiers that cannot safely identify a Mist entity."""
    with pytest.raises(ValueError, match="site_id"):  # Refuse unsafe identity before route use.
        SiteIdentity(org_id=ORG_ID, site_id=site_id)  # Validate external identifiers at the domain boundary.


def test_hourly_measurement_rejects_unknown_provenance() -> None:
    """Reject an unrecognized data origin instead of labeling it as live."""
    with pytest.raises(ValueError, match="provenance"):  # Keep data-state labels explicit.
        HourlyMeasurement(  # Validate provenance before consumers show data.
            identity=build_circuit(),
            hour_start_utc=HOUR_START,
            collected_at_utc=COLLECTED_AT,
            metrics={"utilization": MetricMeasurement(value=42.5, unit="percent")},
            provenance=cast(Literal["live", "synthetic"], "imported"),
        )
