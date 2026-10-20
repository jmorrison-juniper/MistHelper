"""Tests for the alert digest operation workflows."""

from __future__ import annotations  # Enable modern annotations without runtime imports.

from dataclasses import dataclass, field  # Build small fake client and writer objects.
from pathlib import Path  # Validate files through pytest temporary directories.
from time import perf_counter  # Measure the local full digest path for the performance criterion.
from typing import Any  # Accept raw rows in fake clients.
from unittest.mock import MagicMock  # Provide fake input helpers.

import pytest  # Assert validation failures without network calls.

from src.mist.intelligence.reports.alert_digest.client import AlertDigestListResult  # Return client search results.
from src.mist.intelligence.reports.alert_digest.model import (
    AlertDigestModel,
)  # Build realistic digest groups for writer tests.
from src.mist.intelligence.reports.alert_digest.operation import (  # Test the operation class and prompt resolver.
    AlertDigestOperation,
    AlertDigestPromptResolver,
)
from src.mist.intelligence.reports.alert_digest.writer import (
    AlertDigestWriter,
)  # Test output writing through the operation seam.

from .conftest import alarm, definition  # Reuse synthetic row factories.


@dataclass
class FakeClient:
    """Fake alert digest client that never uses the network."""

    definitions: list[dict[str, Any]] = field(default_factory=lambda: [definition()])  # Default category map.
    sites: list[dict[str, Any]] = field(default_factory=lambda: [{"id": "site-1", "name": "Lab Site"}])  # Sites.
    alarms: list[dict[str, Any]] = field(default_factory=list)  # Alarm rows returned by search.
    ack_status: int | None = 200  # Bulk acknowledgement status.
    ack_problem: str = ""  # Bulk acknowledgement problem text.
    searched_hours: list[int] = field(default_factory=list)  # Record lookback values used by searches.
    ack_requests: list[list[str]] = field(default_factory=list)  # Record destructive request alarm IDs.

    def list_alarm_definitions(self) -> list[dict[str, Any]]:
        """Return fake alarm definitions."""
        return self.definitions  # Return a direct fake constants response.

    def list_org_sites(self) -> list[dict[str, Any]]:
        """Return fake organization sites."""
        return self.sites  # Return a direct fake site list response.

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
    digest_calls: int = 0  # Count write_digest invocations, including empty lists.

    def write_digest(self, groups: list[Any]) -> bool:
        """Record digest groups."""
        self.digest_calls += 1  # Prove whether the operation called the writer.
        self.digest_groups = list(groups)  # Preserve groups for assertions.
        return True  # Simulate a successful write.

    def write_acknowledgement_log(self, results: list[Any]) -> bool:
        """Record acknowledgement results."""
        self.ack_results = list(results)  # Preserve results for assertions.
        return True  # Simulate a successful write.


@dataclass
class FakeExporter:
    """Fake DataExporter that records requested CSV writes."""

    writes: list[dict[str, Any]] = field(default_factory=list)  # Keep each write for assertions.

    def write_with_format_selection(
        self,
        data: list[dict[str, Any]],
        filename_or_table: str,
        api_function_name: str,
        fieldnames: list[str] | None = None,
    ) -> bool:
        """Record one CSV write request."""
        self.writes.append(  # Preserve the export request without touching shared data files.
            {
                "data": data,
                "filename": filename_or_table,
                "api_function_name": api_function_name,
                "fieldnames": fieldnames,
            }
        )
        return True  # Simulate a successful DataExporter write.


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
    assert operation(client, writer).execute_digest().state == "completed"  # Run the digest path.
    assert len(writer.digest_groups) == 1  # Confirm grouping by type and site.
    assert client.searched_hours == [24]  # Confirm default lookback.


def test_run_digest_keeps_unknown_category(monkeypatch: Any) -> None:
    """Unknown alarm types are grouped under unknown."""
    monkeypatch.delenv("ALERT_DIGEST_HOURS", raising=False)  # Use the default lookback.
    client = FakeClient(alarms=[alarm(1, type="new_alarm")])  # Provide an alarm absent from definitions.
    writer = FakeWriter()  # Capture output rows.
    operation(client, writer).execute_digest()  # Run the digest path.
    assert writer.digest_groups[0].category == "unknown"  # Confirm unknown category.


def test_run_digest_uses_site_name_and_not_reported_ack_state(monkeypatch: Any) -> None:
    """Menu 280 converts live alarm site ids and absent acked fields into clear output."""
    monkeypatch.delenv("ALERT_DIGEST_HOURS", raising=False)  # Use the default lookback.
    site_id = "cf36153a-97bb-4974-8f8f-e9cc25d64d83"  # Match the live site id shape from issue #3696.
    live_alarm = alarm(1, site_id=site_id, site=site_id, site_name=None, acked=None)  # Match the live search shape.
    client = FakeClient(sites=[{"id": site_id, "name": "Morrison House Site"}], alarms=[live_alarm])  # Site map.
    writer = FakeWriter()  # Capture digest groups without file I/O.
    assert operation(client, writer).execute_digest().state == "completed"  # Run the digest path.
    assert writer.digest_groups[0].site == "Morrison House Site"  # Verify the CSV and Markdown site value.
    assert writer.digest_groups[0].acknowledged_state == "not_reported"  # Verify absent acked state wording.


def test_writer_creates_csv_request_and_ascii_markdown(tmp_path: Path) -> None:
    """Digest writing creates the required CSV target and ASCII Markdown."""
    definitions = AlertDigestModel.definitions_by_key([definition()])  # Build category lookup.
    records = AlertDigestModel.records_from_rows([alarm(1)], definitions)  # Build one realistic alarm row.
    groups = AlertDigestModel.group_records(records)  # Group data as menu 280 does.
    exporter = FakeExporter()  # Capture the CSV write request.
    writer = AlertDigestWriter(exporter=exporter, data_dir=tmp_path)  # Direct Markdown into a safe temp path.
    assert writer.write_digest(groups) is True  # Write both digest outputs.
    assert exporter.writes[0]["filename"] == "AlertDigest.csv"  # Confirm required CSV file name.
    markdown = (tmp_path / "AlertDigest.md").read_text(encoding="utf-8")  # Read the handover summary.
    assert "## infrastructure" in markdown  # Confirm the category section exists.
    assert all(ord(character) < 128 for character in markdown)  # Confirm ASCII-only operator output.


def test_run_digest_handles_normal_volume_under_local_budget(monkeypatch: Any) -> None:
    """Menu 280 processes a normal local alarm volume quickly."""
    monkeypatch.delenv("ALERT_DIGEST_HOURS", raising=False)  # Use the default lookback.
    rows = [alarm(number, site_name=f"Site {number % 5}") for number in range(1, 501)]  # Build normal volume.
    client = FakeClient(alarms=rows)  # Provide the bounded normal volume.
    writer = FakeWriter()  # Capture output rows without file I/O.
    started = perf_counter()  # Start a local end-to-end timing guard.
    assert operation(client, writer).execute_digest().state == "completed"  # Run the digest workflow.
    elapsed = perf_counter() - started  # Stop the local timing guard.
    assert len(writer.digest_groups) == 5  # Confirm the full digest path grouped the volume.
    assert elapsed < 1.0  # Confirm local work preserves the 60 second operation budget.


@dataclass
class RaisingWriter(FakeWriter):
    """Fake writer that raises or rejects the digest write."""

    result: bool = True  # Configure the returned write result.
    error: Exception | None = None  # Configure an exception to raise.

    def write_digest(self, groups: list[Any]) -> bool:
        """Raise the configured error or return the configured result."""
        self.digest_calls += 1  # Count the attempt.
        if self.error is not None:  # Simulate an exporter exception.
            raise self.error  # Propagate it to the caller.
        return self.result  # Simulate a rejected write.


def test_zero_alarm_rows_return_no_output_without_write(monkeypatch: Any) -> None:
    """Menu 280 reports no_output and skips the writer when no alarm exists."""
    monkeypatch.delenv("ALERT_DIGEST_HOURS", raising=False)  # Use the default lookback.
    writer = FakeWriter()  # Capture any write attempt.
    outcome = operation(FakeClient(alarms=[]), writer).execute_digest()  # Run with zero rows.
    assert outcome.state == "no_output"  # The empty result is explicit.
    assert writer.digest_calls == 0  # The writer was never called, even with an empty list.


def test_alarm_search_failure_returns_failed(monkeypatch: Any) -> None:
    """A failed alarm search returns a failed outcome and writes nothing."""
    monkeypatch.delenv("ALERT_DIGEST_HOURS", raising=False)  # Use the default lookback.
    client = FakeClient(alarms=[alarm(1)])  # Provide a row that must not be written.
    client.search_alarms = lambda hours: AlertDigestListResult([], 500, False, "HTTP 500")  # type: ignore[method-assign]
    writer = FakeWriter()  # Capture any write attempt.
    assert operation(client, writer).execute_digest().state == "failed"  # HTTP 5xx fails closed.
    assert writer.digest_groups == []  # Nothing was written.


def test_client_error_search_failure_returns_failed(monkeypatch: Any) -> None:
    """An HTTP 4xx alarm search returns a failed outcome."""
    monkeypatch.delenv("ALERT_DIGEST_HOURS", raising=False)  # Use the default lookback.
    client = FakeClient(alarms=[alarm(1)])  # Provide a row that must not be written.
    client.search_alarms = lambda hours: AlertDigestListResult([], 403, False, "HTTP 403")  # type: ignore[method-assign]
    assert operation(client, FakeWriter()).execute_digest().state == "failed"  # HTTP 4xx fails closed.


def test_invalid_lookback_returns_failed(monkeypatch: Any) -> None:
    """An invalid lookback returns a failed outcome before any search."""
    monkeypatch.setenv("ALERT_DIGEST_HOURS", "bad")  # Set an invalid override.
    client = FakeClient(alarms=[alarm(1)])  # Provide a row that must not be read.
    assert operation(client, FakeWriter()).execute_digest().state == "failed"  # Invalid input fails.
    assert client.searched_hours == []  # No search ran.


def test_rejected_write_returns_failed_without_success_message(monkeypatch: Any, capsys: Any) -> None:
    """A writer that returns False yields a failed outcome and no success message."""
    monkeypatch.delenv("ALERT_DIGEST_HOURS", raising=False)  # Use the default lookback.
    writer = RaisingWriter(result=False)  # Reject the write.
    outcome = operation(FakeClient(alarms=[alarm(1)]), writer).execute_digest()  # Run the digest.
    assert outcome.state == "failed"  # Not completed.
    assert outcome.message == "The alert digest could not write its output."  # Failure text is explicit.
    assert writer.digest_calls == 1  # The writer was attempted once.
    assert "wrote" not in capsys.readouterr().out  # No success line for a rejected write.


def test_write_exception_still_propagates(monkeypatch: Any) -> None:
    """The handler does not convert an export exception into an outcome."""
    monkeypatch.delenv("ALERT_DIGEST_HOURS", raising=False)  # Use the default lookback.
    writer = RaisingWriter(error=RuntimeError("export write failed"))  # Raise during write.
    with pytest.raises(RuntimeError, match="export write failed"):  # Preserve existing exception handling.
        operation(FakeClient(alarms=[alarm(1)]), writer).execute_digest()  # Run the digest path.


def test_state_ignores_failure_wording_in_messages(monkeypatch: Any, caplog: Any) -> None:
    """Failure words in logs or alarm text do not change a completed state."""
    monkeypatch.delenv("ALERT_DIGEST_HOURS", raising=False)  # Use the default lookback.
    rows = [alarm(1, type="failed to connect")]  # Put marker words in the alarm data.
    with caplog.at_level("INFO"):  # Capture log text.
        outcome = operation(FakeClient(alarms=rows), FakeWriter()).execute_digest()  # Run the digest.
    assert outcome.state == "completed"  # Wording does not decide the state.


def test_menu_handlers_return_outcomes(monkeypatch: Any) -> None:
    """The class handlers return the outcome from the digest path."""
    monkeypatch.delenv("ALERT_DIGEST_HOURS", raising=False)  # Use the default lookback.
    expected = operation(FakeClient(alarms=[]), FakeWriter()).execute_digest()  # Build a no_output outcome.
    monkeypatch.setattr(AlertDigestOperation, "execute_digest", lambda self: expected)  # Stub the workflow.
    assert AlertDigestOperation.run_digest() is expected  # Menu 280 returns it unchanged.
    assert AlertDigestOperation.run() is expected  # The default action forwards it.


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


def test_default_lookback_is_24_hours() -> None:
    """The shared lookback default is one day."""
    assert AlertDigestPromptResolver.resolve_lookback_hours({}) == 24  # Confirm the default contract.


def test_env_override_sets_lookback_hours() -> None:
    """A valid environment value overrides the default."""
    assert AlertDigestPromptResolver.resolve_lookback_hours({"ALERT_DIGEST_HOURS": "8"}) == 8  # Confirm override.


@pytest.mark.parametrize("value", ["", "0", "-1", "abc"])
def test_invalid_lookback_values_fail_closed(value: str) -> None:
    """Blank uses default, and invalid explicit values fail closed."""
    env = {"ALERT_DIGEST_HOURS": value}  # Build the injected environment.
    if value == "":  # Blank is equivalent to unset.
        assert AlertDigestPromptResolver.resolve_lookback_hours(env) == 24  # Confirm blank default.
    else:
        with pytest.raises(ValueError):  # Invalid explicit values must stop the operation.
            AlertDigestPromptResolver.resolve_lookback_hours(env)  # Exercise the validation path.


@pytest.mark.parametrize(
    ("text", "count", "expected"),
    [("ACK 3", 3, True), ("ACK 2", 3, False), ("ack 3", 3, False), ("ACK", 3, False), ("ACK three", 3, False)],
)
def test_confirmation_requires_ack_and_exact_count(text: str, count: int, expected: bool) -> None:
    """Only ACK followed by the exact count authorizes menu 281."""
    assert AlertDigestPromptResolver.confirmation_matches(text, count) is expected  # Confirm exact parsing.


@pytest.mark.parametrize(("arguments", "expected"), [(["--dry-run"], True), (["--menu", "281"], False)])
def test_dry_run_requested_reads_shared_flag(arguments: list[str], expected: bool) -> None:
    """Only --dry-run enables the acknowledgement preview mode."""
    assert AlertDigestPromptResolver.dry_run_requested(arguments) is expected  # Confirm dry-run flag parsing.
