"""Tests for the alert digest operation workflows."""

from __future__ import annotations  # Enable modern annotations without runtime imports.

from dataclasses import dataclass, field  # Build small fake client and writer objects.
from typing import Any  # Accept raw rows in fake clients.
from unittest.mock import MagicMock  # Provide fake input helpers.

from src.reports.alert_digest.client import AlertDigestListResult  # Return client search results.
from src.reports.alert_digest.operation import AlertDigestOperation  # Test the operation class.

from .conftest import alarm, definition  # Reuse synthetic row factories.


@dataclass
class FakeClient:
    """Fake alert digest client that never uses the network."""

    definitions: list[dict[str, Any]] = field(default_factory=lambda: [definition()])  # Default category map.
    alarms: list[dict[str, Any]] = field(default_factory=list)  # Alarm rows returned by search.
    ack_status: int | None = 200  # Bulk acknowledgement status.
    ack_problem: str = ""  # Bulk acknowledgement problem text.
    searched_hours: list[int] = field(default_factory=list)  # Record lookback values used by searches.
    ack_requests: list[list[str]] = field(default_factory=list)  # Record destructive request alarm IDs.

    def list_alarm_definitions(self) -> list[dict[str, Any]]:
        """Return fake alarm definitions."""
        return self.definitions  # Return a direct fake constants response.

    def search_alarms(self, hours: int) -> AlertDigestListResult:
        """Return fake alarm search rows."""
        self.searched_hours.append(hours)  # Record the shared lookback value.
        return AlertDigestListResult(self.alarms, 200)  # Return a successful fake search.

    def acknowledge_alarms(self, alarm_ids: list[str]) -> tuple[int | None, str]:
        """Record a fake bulk acknowledgement request."""
        self.ack_requests.append(list(alarm_ids))  # Record the destructive request.
        return self.ack_status, self.ack_problem  # Return the configured result.


@dataclass
class FakeWriter:
    """Fake writer that records output rows without writing files."""

    digest_groups: list[Any] = field(default_factory=list)  # Store digest groups passed by the operation.
    ack_results: list[Any] = field(default_factory=list)  # Store acknowledgement rows passed by the operation.

    def write_digest(self, groups: list[Any]) -> bool:
        """Record digest groups."""
        self.digest_groups = list(groups)  # Preserve groups for assertions.
        return True  # Simulate a successful write.

    def write_acknowledgement_log(self, results: list[Any]) -> bool:
        """Record acknowledgement results."""
        self.ack_results = list(results)  # Preserve results for assertions.
        return True  # Simulate a successful write.


def operation(client: FakeClient, writer: FakeWriter, answer: str = "") -> AlertDigestOperation:
    """Return an operation with fake dependencies."""
    input_utils = MagicMock()  # Fake the safe input helper.
    input_utils.safe_input.return_value = answer  # Return scripted operator input.
    return AlertDigestOperation(client=client, writer=writer, input_utils=input_utils)  # Build operation under test.


def test_run_digest_writes_grouped_outputs_without_prompt(monkeypatch: Any) -> None:
    """Menu 280 writes digest outputs and does not prompt."""
    monkeypatch.delenv("ALERT_DIGEST_HOURS", raising=False)  # Use the default lookback.
    client = FakeClient(alarms=[alarm(1), alarm(2, count=2)])  # Provide grouped alarm data.
    writer = FakeWriter()  # Capture output rows.
    assert operation(client, writer).execute_digest() is True  # Run the digest path.
    assert len(writer.digest_groups) == 1  # Confirm grouping by type and site.
    assert client.searched_hours == [24]  # Confirm default lookback.


def test_run_digest_keeps_unknown_category(monkeypatch: Any) -> None:
    """Unknown alarm types are grouped under unknown."""
    monkeypatch.delenv("ALERT_DIGEST_HOURS", raising=False)  # Use the default lookback.
    client = FakeClient(alarms=[alarm(1, type="new_alarm")])  # Provide an alarm absent from definitions.
    writer = FakeWriter()  # Capture output rows.
    operation(client, writer).execute_digest()  # Run the digest path.
    assert writer.digest_groups[0].category == "unknown"  # Confirm unknown category.


def test_wrong_confirmation_cancels_without_request(monkeypatch: Any, caplog: Any) -> None:
    """Menu 281 sends no request when confirmation does not match."""
    monkeypatch.delenv("ALERT_DIGEST_HOURS", raising=False)  # Use the default lookback.
    client = FakeClient(alarms=[alarm(1), alarm(2), alarm(3)])  # Provide three candidates.
    writer = FakeWriter()  # Capture acknowledgement results.
    with caplog.at_level("INFO"):  # Capture the required cancellation log line.
        assert operation(client, writer, "ACK 2").execute_acknowledge() is False  # Wrong count cancels.
    assert client.ack_requests == []  # Confirm no destructive request.
    assert [result.outcome for result in writer.ack_results] == ["cancelled", "cancelled", "cancelled"]
    assert "confirmation did not match" in caplog.text  # Confirm cancellation log line.


def test_dry_run_lists_candidates_without_request(monkeypatch: Any) -> None:
    """Menu 281 dry-run writes rows and sends no request."""
    monkeypatch.delenv("ALERT_DIGEST_HOURS", raising=False)  # Use the default lookback.
    client = FakeClient(alarms=[alarm(1), alarm(2)])  # Provide two candidates.
    writer = FakeWriter()  # Capture acknowledgement results.
    assert operation(client, writer).execute_acknowledge(dry_run=True) is True  # Run dry mode.
    assert client.ack_requests == []  # Confirm no destructive request.
    assert [result.outcome for result in writer.ack_results] == ["dry_run", "dry_run"]  # Confirm log rows.


def test_valid_confirmation_sends_one_bulk_request(monkeypatch: Any) -> None:
    """Menu 281 sends one request only after exact confirmation."""
    monkeypatch.delenv("ALERT_DIGEST_HOURS", raising=False)  # Use the default lookback.
    client = FakeClient(alarms=[alarm(1), alarm(2)])  # Provide two candidates.
    writer = FakeWriter()  # Capture acknowledgement results.
    assert operation(client, writer, "ACK 2").execute_acknowledge() is True  # Exact confirmation sends request.
    assert client.ack_requests == [["alarm-1", "alarm-2"]]  # Confirm one bulk request.
    assert [result.outcome for result in writer.ack_results] == ["acknowledged", "acknowledged"]  # Confirm rows.


def test_no_candidates_send_no_request(monkeypatch: Any) -> None:
    """No unacknowledged alarms means no request."""
    monkeypatch.delenv("ALERT_DIGEST_HOURS", raising=False)  # Use the default lookback.
    client = FakeClient(alarms=[alarm(1, acked=True)])  # Provide acknowledged row only.
    writer = FakeWriter()  # Capture acknowledgement results.
    assert operation(client, writer, "ACK 0").execute_acknowledge() is True  # Nothing to acknowledge is safe success.
    assert client.ack_requests == []  # Confirm no destructive request.
    assert writer.ack_results == []  # Confirm no fake CSV rows for zero candidates.


def test_shared_lookback_override_applies_to_both_paths(monkeypatch: Any) -> None:
    """Digest and acknowledge use the same ALERT_DIGEST_HOURS value."""
    monkeypatch.setenv("ALERT_DIGEST_HOURS", "8")  # Set a shared override.
    client = FakeClient(alarms=[alarm(1)])  # Provide one candidate.
    writer = FakeWriter()  # Capture outputs.
    operation(client, writer).execute_digest()  # Run digest path.
    operation(client, writer, "ACK 1").execute_acknowledge()  # Run acknowledgement path.
    assert client.searched_hours == [8, 8]  # Confirm both paths used the override.


def test_invalid_lookback_sends_no_destructive_request(monkeypatch: Any) -> None:
    """Invalid lookback values fail before any acknowledgement request."""
    monkeypatch.setenv("ALERT_DIGEST_HOURS", "bad")  # Set an invalid override.
    client = FakeClient(alarms=[alarm(1)])  # Provide a candidate that must not be touched.
    writer = FakeWriter()  # Capture outputs.
    assert operation(client, writer, "ACK 1").execute_acknowledge() is False  # Invalid lookback fails.
    assert client.ack_requests == []  # Confirm no destructive request.
