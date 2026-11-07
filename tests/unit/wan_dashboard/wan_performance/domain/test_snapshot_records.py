"""Verify current snapshot normalization without history codec behavior."""

import pytest

from src.interfaces.wan_performance.collection.snapshot_records import SnapshotRecords, SnapshotStates


class TestSnapshotRecords:
    """Verify source values and current state only."""

    @staticmethod
    def snapshot() -> dict[str, object]:
        """Return independent rows with documented source identity fields."""
        return {  # Keep the fixture local to this test class.
            "org_id": "org-one",  # Select one tenant.
            "collected_at_utc": "2024-01-01T12:34:00+00:00",  # Preserve one source instant.
            "provenance": "live",  # Use only live source data.
            "ports": [
                {
                    "org_id": "org-one",
                    "site_id": "site-one",
                    "mac": "aabbccddeeff",
                    "port_id": "ge-0/0/0",
                    "rx_bps": 0,
                    "speed": 1000,
                    "up": False,
                }
            ],  # Include one current port.
            "peers": [
                {
                    "org_id": "org-one",
                    "site_id": "site-one",
                    "mac": "aabbccddeeff",
                    "port_id": "ge-0/0/0",
                    "peer_mac": "112233445566",
                    "peer_port_id": "ge-0/0/1",
                    "peer_site_id": "site-two",
                    "type": "ipsec",
                    "loss": 0,
                    "up": True,
                    "is_active": False,
                    "uptime": 0,
                    "last_seen": 1704112440,
                }
            ],  # Include one peer path.
        }

    def test_snapshot_uses_observation_hour_without_coverage_claim(self) -> None:
        """Assign an hour key but preserve the exact collection time."""
        records = SnapshotRecords.build(self.snapshot())  # Normalize both source rows.
        assert len(records) == 2  # Keep port and peer observations.
        assert records[0].hour_start_utc.isoformat() == "2024-01-01T12:00:00+00:00"  # Assign the observation hour.
        assert records[0].collected_at_utc.minute == 34  # Preserve the source instant.
        assert records[0].metrics["rx_bps"].value == 0  # Preserve measured zero.
        assert records[0].metrics["rx_utilization_percent"].value == 0  # Derive from the reported speed only.
        assert records[0].metrics["rx_bps"].coverage_fraction is None  # Do not claim full-hour coverage.

    def test_peer_paths_keep_remote_port_and_mac(self) -> None:
        """Keep distinct remote path values in the natural key."""
        first = SnapshotRecords.build(self.snapshot())[1]  # Normalize the first peer path.
        other_data = self.snapshot()  # Copy the independent input fixture.
        other_data["peers"][0]["peer_port_id"] = "ge-0/0/2"  # Change the remote port.
        second = SnapshotRecords.build(other_data)[1]  # Normalize the second peer path.
        assert first.natural_key != second.natural_key  # Prevent path collisions.

    def test_cross_organization_rows_are_rejected(self) -> None:
        """Reject tenant data before it enters the current-state model."""
        data = self.snapshot()  # Create an isolated snapshot.
        data["ports"][0]["org_id"] = "other-org"  # Change the row tenant.
        with pytest.raises(ValueError, match="organization"):  # Require a tenant-scope failure.
            SnapshotRecords.build(data)  # Refuse the mixed-tenant snapshot.

    def test_cumulative_counters_do_not_become_rates(self) -> None:
        """Keep byte counters out of directional rates and utilization."""
        data = self.snapshot()  # Create an isolated snapshot.
        data["ports"][0].pop("rx_bps")  # Remove the actual rate.
        data["ports"][0]["rx_bytes"] = 1000000  # Add a cumulative counter.
        record = SnapshotRecords.build(data)[0]  # Normalize the current port.
        assert record.metrics["rx_bps"].value is None  # Do not treat bytes as a rate.
        assert record.metrics["rx_utilization_percent"].value is None  # Do not infer utilization.

    def test_current_state_is_separate_and_explicit(self) -> None:
        """Preserve explicit booleans and reported uptime outside metrics."""
        data = self.snapshot()  # Create an isolated snapshot.
        records = SnapshotRecords.build(data)  # Normalize observations.
        states = SnapshotStates.build(data, records)  # Build a separate current-state map.
        assert records[0].is_up_observation is False  # Keep explicit down state.
        assert records[1].is_up_observation is True  # Keep explicit up state.
        assert states[records[1].natural_key]["Redundant path"] == "Standby"  # Preserve explicit inactive state.
        assert states[records[1].natural_key]["Gateway-reported uptime (s)"] == "0"  # Preserve reported zero.
        assert "availability" not in records[1].metrics  # Do not infer availability.
