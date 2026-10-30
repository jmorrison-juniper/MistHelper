"""Unit tests for RF diagnostics operation prompts and outcomes."""

from __future__ import annotations  # WHY: keep annotations import-safe.

from collections.abc import Iterator  # WHY: fake input uses a typed sequence iterator.
from dataclasses import dataclass  # WHY: fake responses mimic SDK responses.
from datetime import UTC, datetime  # WHY: fixed clock keeps file names deterministic.
from typing import Any  # WHY: fake calls carry dynamic payloads.

from src.mist.intelligence.troubleshooting.rf_diagnostics import (
    operation as operation_module,  # Patch the moved operation seams.
)
from src.mist.intelligence.troubleshooting.rf_diagnostics.file_naming import (
    RfDiagnosticFileNamer,
)  # WHY: inject tmp download path.
from src.mist.intelligence.troubleshooting.rf_diagnostics.models import (
    STATUS_CANCELLED,
    STATUS_SUCCESS,
)  # WHY: assert final states.
from src.mist.intelligence.troubleshooting.rf_diagnostics.operation import RfDiagnosticsOperation  # WHY: test target.
from src.mist.intelligence.troubleshooting.rf_diagnostics.recording import (
    RfDiagnosticRecordingRunner,
)  # WHY: use real runner.
from src.mist.intelligence.troubleshooting.rf_diagnostics.spectrum import (
    SpectrumAnalysisRunner,
)  # WHY: use real runner.


@dataclass
class FakeResponse:
    """Small response object with a data payload."""

    data: Any  # WHY: client helpers unwrap this attribute.


class FakeAudit:
    """Capture audit rows without writing a file."""

    def __init__(self) -> None:
        """Create audit row storage."""
        self.rows: list[Any] = []  # WHY: tests assert one audit row per attempt.

    def append(self, run: Any) -> bool:
        """Store one audit row and report success."""
        self.rows.append(run)  # WHY: preserve the row for assertions.
        return True  # WHY: operation should follow the normal persistence path.


class FakeRfDiagnosticsClient:
    """Fake client for operation-level RF diagnostics tests."""

    def __init__(self, poll_payloads: list[dict[str, Any]] | None = None) -> None:
        """Store fake payloads and create call history."""
        self.poll_payloads = poll_payloads or [{"status": "complete", "band": "5"}]  # WHY: default final scan.
        self.calls: list[tuple[str, tuple[Any, ...]]] = []  # WHY: tests assert remote action order.

    def start_spectrum(self, site_id: str, device_id: str, band: str, duration: int) -> FakeResponse:
        """Capture spectrum start requests."""
        self.calls.append(("start_spectrum", (site_id, device_id, band, duration)))  # WHY: assert request values.
        return FakeResponse({"status": "running"})  # WHY: force the runner to poll state.

    def get_running_spectrum(self, site_id: str) -> FakeResponse:
        """Return the next spectrum state."""
        self.calls.append(("get_running_spectrum", (site_id,)))  # WHY: assert bounded polling.
        payload = self.poll_payloads.pop(0) if self.poll_payloads else {"status": "running"}  # WHY: default run.
        return FakeResponse(payload)  # WHY: mimic SDK response shape.

    def start_recording(self, site_id: str, name: str, client_mac: str, duration: int) -> FakeResponse:
        """Capture recording start requests."""
        self.calls.append(("start_recording", (site_id, name, client_mac, duration)))  # WHY: assert body inputs.
        return FakeResponse({"id": "rf1"})  # WHY: runner needs an RF diagnostic id.

    def stop_recording(self, site_id: str, rfdiag_id: str) -> FakeResponse:
        """Capture recording stop requests."""
        self.calls.append(("stop_recording", (site_id, rfdiag_id)))  # WHY: prove finally stop runs.
        return FakeResponse({})  # WHY: stop response has no required data.

    def download_recording(self, site_id: str, rfdiag_id: str) -> FakeResponse:
        """Capture recording download requests."""
        self.calls.append(("download_recording", (site_id, rfdiag_id)))  # WHY: prove success downloads evidence.
        return FakeResponse(b"pcap")  # WHY: real runner writes these bytes to disk.


class FastTimeoutSpectrumRunner(SpectrumAnalysisRunner):
    """Spectrum runner that uses one no-sleep poll for operation tests."""

    def run(self, site_id: str, device_id: str, band: str, duration: int) -> Any:
        """Run with a one-poll limit so timeout tests are fast."""
        return super().run(site_id, device_id, band, duration, poll_limit=1, poll_interval=0)  # WHY: avoid sleeps.


def test_operation_spectrum_decline_writes_cancel_audit(monkeypatch) -> None:
    """Spectrum mode writes a cancelled row when the operator declines."""
    client = FakeRfDiagnosticsClient()  # WHY: prove no remote action starts.
    audit = FakeAudit()  # WHY: capture the cancellation row.
    operation = _operation_with_answers(["1", "ap1", "", "bad", "N"], client, audit)  # WHY: fake prompts.
    monkeypatch.setattr(RfDiagnosticsOperation, "_select_site", staticmethod(lambda: "site1"))  # WHY: no prompt UI.
    operation._run()  # WHY: exercise mode dispatch and decline path.
    assert client.calls == []  # WHY: decline must happen before remote action.
    assert [(row.mode, row.status, row.target) for row in audit.rows] == [
        ("spectrum", STATUS_CANCELLED, "ap1")
    ]  # WHY: exactly one cancelled spectrum row is written.


def test_operation_recording_decline_writes_cancel_audit(monkeypatch) -> None:
    """Recording mode writes a cancelled row when the operator declines."""
    client = FakeRfDiagnosticsClient()  # WHY: prove no remote action starts.
    audit = FakeAudit()  # WHY: capture the cancellation row.
    operation = _operation_with_answers(["2", "AA:BB:CC:DD:EE:FF", "30", "N"], client, audit)  # WHY: prompts.
    monkeypatch.setattr(RfDiagnosticsOperation, "_select_site", staticmethod(lambda: "site1"))  # WHY: no prompt UI.
    operation._run()  # WHY: exercise mode dispatch and decline path.
    assert client.calls == []  # WHY: decline must happen before remote action.
    assert [(row.mode, row.status, row.target) for row in audit.rows] == [
        ("recording", STATUS_CANCELLED, "aabbccddeeff")
    ]  # WHY: MAC normalization is visible in the audit row.


def test_operation_spectrum_timeout_writes_timeout_audit(monkeypatch) -> None:
    """Spectrum mode records a timeout when the poll limit expires."""
    client = FakeRfDiagnosticsClient([{"status": "running"}])  # WHY: force timeout with the fast runner.
    audit = FakeAudit()  # WHY: capture the timeout row.
    operation = _operation_with_answers(["1", "ap1", "5", "300", "y"], client, audit)  # WHY: confirm start.
    monkeypatch.setattr(RfDiagnosticsOperation, "_select_site", staticmethod(lambda: "site1"))  # WHY: no prompt UI.
    monkeypatch.setattr(operation_module, "SpectrumAnalysisRunner", FastTimeoutSpectrumRunner)  # WHY: avoid sleep.
    operation._run()  # WHY: exercise the confirmed spectrum path.
    assert [call[0] for call in client.calls] == [
        "start_spectrum",
        "get_running_spectrum",
    ]  # WHY: timeout performs one poll after start.
    assert [(row.mode, row.status, row.target) for row in audit.rows] == [
        ("spectrum", "timeout", "ap1")
    ]  # WHY: timeout is written as one audit row.


def test_operation_recording_downloads_into_tmp_path(monkeypatch, tmp_path) -> None:
    """Recording mode writes the downloaded file through the operation path."""
    client = FakeRfDiagnosticsClient()  # WHY: fake remote calls for real recording runner.
    audit = FakeAudit()  # WHY: capture the success row.
    operation = _operation_with_answers(["2", "AA:BB:CC:DD:EE:FF", "30", "y"], client, audit)  # WHY: confirm.
    namer = RfDiagnosticFileNamer(tmp_path / "data" / "rfdiags")  # WHY: isolate the downloaded file.
    monkeypatch.setattr(RfDiagnosticsOperation, "_select_site", staticmethod(lambda: "site1"))  # WHY: no prompt UI.
    monkeypatch.setattr(operation_module, "RfDiagnosticRecordingRunner", _recording_runner_factory(namer))  # WHY.
    operation._run()  # WHY: exercise confirmed recording flow through the operation.
    assert [call[0] for call in client.calls] == [
        "start_recording",
        "stop_recording",
        "download_recording",
    ]  # WHY: success starts, stops, and downloads in order.
    assert audit.rows[0].status == STATUS_SUCCESS  # WHY: success writes one audit row.
    assert (tmp_path / "data" / "rfdiags").is_dir()  # WHY: download path stays under tmp data.
    assert list((tmp_path / "data" / "rfdiags").glob("*.pcap"))[0].read_bytes() == b"pcap"  # WHY: bytes persist.


def test_operation_recording_ctrl_c_still_stops(monkeypatch, tmp_path) -> None:
    """Recording mode stops the recording when Ctrl+C interrupts the wait."""
    client = FakeRfDiagnosticsClient()  # WHY: fake remote calls for real recording runner.
    audit = FakeAudit()  # WHY: capture the failure row.
    operation = _operation_with_answers(["2", "aabbccddeeff", "30", "y"], client, audit)  # WHY: confirm.
    namer = RfDiagnosticFileNamer(tmp_path / "data" / "rfdiags")  # WHY: isolate any accidental download.
    monkeypatch.setattr(RfDiagnosticsOperation, "_select_site", staticmethod(lambda: "site1"))  # WHY: no prompt UI.
    monkeypatch.setattr(operation_module, "RfDiagnosticRecordingRunner", _interrupting_runner_factory(namer))  # WHY.
    operation._run()  # WHY: exercise Ctrl+C path through the operation.
    assert [call[0] for call in client.calls] == [
        "start_recording",
        "stop_recording",
    ]  # WHY: finally block stops without download after interrupt.
    assert audit.rows[0].status == "failed"  # WHY: interrupted wait is not reported as success.


def _operation_with_answers(answers: list[str], client: Any, audit: FakeAudit) -> RfDiagnosticsOperation:
    """Build an operation instance with fake prompts and collaborators."""
    answer_iterator = iter(answers)  # WHY: each prompt consumes one controlled answer.
    operation = RfDiagnosticsOperation.__new__(RfDiagnosticsOperation)  # WHY: bypass resolver-backed constructor.
    operation._client = client  # WHY: use a fake client with no network.
    operation._audit = audit  # WHY: use in-memory audit rows.
    operation._input = _fake_input(answer_iterator)  # WHY: drive prompts without user input.
    return operation  # WHY: caller runs the selected flow.


def _fake_input(answer_iterator: Iterator[str]) -> Any:
    """Return a safe-input compatible fake prompt function."""
    return lambda *args, **kwargs: next(answer_iterator)  # WHY: tests control exact prompt answers.


def _recording_runner_factory(namer: RfDiagnosticFileNamer) -> Any:
    """Return a recording runner factory that writes under a temp path."""
    return lambda client: RfDiagnosticRecordingRunner(  # WHY: operation expects a one-argument constructor.
        client, namer=namer, wait_fn=lambda seconds: None, clock=_fixed_clock
    )


def _interrupting_runner_factory(namer: RfDiagnosticFileNamer) -> Any:
    """Return a recording runner factory that simulates Ctrl+C."""
    return lambda client: RfDiagnosticRecordingRunner(  # WHY: operation expects a one-argument constructor.
        client, namer=namer, wait_fn=_raise_keyboard_interrupt, clock=_fixed_clock
    )


def _fixed_clock() -> datetime:
    """Return a deterministic UTC time."""
    return datetime(2026, 9, 29, 16, 10, 13, tzinfo=UTC)  # WHY: file names and audit rows stay stable.


def _raise_keyboard_interrupt(seconds: float) -> None:
    """Raise Ctrl+C from a fake wait function."""
    raise KeyboardInterrupt  # WHY: prove the runner stops in a finally block.
