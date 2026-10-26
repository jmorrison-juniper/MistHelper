"""Unit tests for spectrum analysis flow."""

from __future__ import annotations  # WHY: keep annotations import-safe.

from dataclasses import dataclass  # WHY: fake client responses mimic SDK responses.
from datetime import UTC, datetime  # WHY: make audit timestamps deterministic.
from typing import Any  # WHY: fake responses carry dynamic payloads.

from src.mist.intelligence.troubleshooting.rf_diagnostics.models import (
    STATUS_SUCCESS,
    STATUS_TIMEOUT,
)  # WHY: assert outcomes.
from src.mist.intelligence.troubleshooting.rf_diagnostics.spectrum import SpectrumAnalysisRunner  # WHY: test target.


@dataclass
class FakeResponse:
    """Small response object with a data payload."""

    data: Any  # WHY: runner unwraps response.data through the client helper.


class FakeSpectrumClient:
    """Fake spectrum client with configurable poll payloads."""

    def __init__(self, poll_payloads: list[dict[str, Any]]) -> None:
        """Store poll data and create call counters."""
        self.poll_payloads = poll_payloads  # WHY: tests control running and final states.
        self.start_calls: list[tuple[str, str, str, int]] = []  # WHY: assert start was called.
        self.poll_calls: list[str] = []  # WHY: assert bounded polling.

    def start_spectrum(self, site_id: str, device_id: str, band: str, duration: int) -> FakeResponse:
        """Capture spectrum start requests."""
        self.start_calls.append((site_id, device_id, band, duration))  # WHY: preserve call arguments.
        return FakeResponse({"session": "s1", "status": "running"})  # WHY: start response is not final.

    def get_running_spectrum(self, site_id: str) -> FakeResponse:
        """Return the next poll payload."""
        self.poll_calls.append(site_id)  # WHY: record poll attempts.
        payload = self.poll_payloads.pop(0) if self.poll_payloads else {"status": "running"}  # WHY: default running.
        return FakeResponse(payload)  # WHY: mimic SDK response shape.


def test_spectrum_runner_polls_until_final_result() -> None:
    """Spectrum runner starts, polls, and returns a success audit row."""
    client = FakeSpectrumClient([{"status": "running"}, {"status": "complete", "band": "5"}])  # WHY: final poll.
    runner = SpectrumAnalysisRunner(
        client, sleep_fn=lambda seconds: None, clock=lambda: datetime(2026, 9, 29, tzinfo=UTC)
    )
    session, run = runner.run("site1", "ap1", "5", 300, poll_limit=3)  # WHY: exercise happy path.
    assert client.start_calls == [("site1", "ap1", "5", 300)]  # WHY: start uses operator values.
    assert len(client.poll_calls) == 2  # WHY: runner stops after the final payload.
    assert session.status == STATUS_SUCCESS  # WHY: final result is successful.
    assert run.status == STATUS_SUCCESS  # WHY: audit row marks success.
    assert "band=5" in run.result_reference  # WHY: audit row gives a useful result summary.


def test_spectrum_runner_times_out_after_poll_limit() -> None:
    """Spectrum runner reports timeout after the bounded poll limit."""
    client = FakeSpectrumClient([{"status": "running"}, {"status": "running"}])  # WHY: no final payload.
    runner = SpectrumAnalysisRunner(
        client, sleep_fn=lambda seconds: None, clock=lambda: datetime(2026, 9, 29, tzinfo=UTC)
    )
    session, run = runner.run("site1", "ap1", "5", 300, poll_limit=2)  # WHY: exercise timeout path.
    assert session.status == STATUS_TIMEOUT  # WHY: session result states timeout.
    assert run.status == STATUS_TIMEOUT  # WHY: audit row states timeout.
    assert len(client.poll_calls) == 2  # WHY: runner honors the poll limit.


def test_spectrum_runner_marks_failed_final_payload() -> None:
    """Spectrum runner audits a failed final payload as failed."""
    client = FakeSpectrumClient([{"status": "failed", "band": "5"}])  # WHY: Mist can return a final failed state.
    runner = SpectrumAnalysisRunner(
        client, sleep_fn=lambda seconds: None, clock=lambda: datetime(2026, 9, 29, tzinfo=UTC)
    )
    session, run = runner.run("site1", "ap1", "5", 300, poll_limit=1)  # WHY: exercise final failure state.
    assert session.status == "failed"  # WHY: session must not claim success.
    assert run.status == "failed"  # WHY: audit row must not claim success.
