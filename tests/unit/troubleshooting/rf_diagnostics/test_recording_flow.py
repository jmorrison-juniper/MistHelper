"""Unit tests for RF diagnostic recording flow."""

from __future__ import annotations  # WHY: keep annotations import-safe.

from dataclasses import dataclass  # WHY: fake client responses mimic SDK responses.
from datetime import UTC, datetime  # WHY: make file names and audit times deterministic.
from typing import Any  # WHY: fake responses carry dynamic payloads.

from src.troubleshooting.rf_diagnostics.file_naming import RfDiagnosticFileNamer  # WHY: inject temp download path.
from src.troubleshooting.rf_diagnostics.models import STATUS_FAILED, STATUS_SUCCESS  # WHY: assert outcomes.
from src.troubleshooting.rf_diagnostics.recording import RfDiagnosticRecordingRunner  # WHY: test target.


@dataclass
class FakeResponse:
    """Small response object with a data payload."""

    data: Any  # WHY: runner unwraps response.data through the client helper.


class FakeRecordingClient:
    """Fake RF diagnostics client for recording tests."""

    def __init__(self, download_data: bytes = b"pcap") -> None:
        """Store fake download data and create call history."""
        self.download_data = download_data  # WHY: tests control empty and non-empty downloads.
        self.calls: list[tuple[str, tuple[Any, ...]]] = []  # WHY: assert start, stop, and download order.

    def start_recording(self, site_id: str, name: str, client_mac: str, duration: int) -> FakeResponse:
        """Capture recording start requests."""
        self.calls.append(("start", (site_id, name, client_mac, duration)))  # WHY: preserve call arguments.
        return FakeResponse({"id": "rf1"})  # WHY: return the id needed for stop and download.

    def stop_recording(self, site_id: str, rfdiag_id: str) -> FakeResponse:
        """Capture recording stop requests."""
        self.calls.append(("stop", (site_id, rfdiag_id)))  # WHY: prove stop runs in finally.
        return FakeResponse({})  # WHY: stop has no useful payload.

    def download_recording(self, site_id: str, rfdiag_id: str) -> FakeResponse:
        """Capture recording download requests."""
        self.calls.append(("download", (site_id, rfdiag_id)))  # WHY: prove download runs after stop.
        return FakeResponse(self.download_data)  # WHY: return bytes for the file write.


def test_recording_runner_stops_then_downloads_file(tmp_path) -> None:
    """Recording runner stops a recording and writes the downloaded file."""
    client = FakeRecordingClient()  # WHY: fake remote calls.
    namer = RfDiagnosticFileNamer(tmp_path / "data" / "rfdiags")  # WHY: isolate download output.
    runner = RfDiagnosticRecordingRunner(client, namer=namer, wait_fn=lambda seconds: None, clock=_fixed_clock)
    recording, diagnostic_file, run = runner.run("site1", "aabbccddeeff", 30, "name1")  # WHY: happy path.
    assert [call[0] for call in client.calls] == ["start", "stop", "download"]  # WHY: stop before download.
    assert recording.status == STATUS_SUCCESS  # WHY: recording result marks success.
    assert diagnostic_file is not None  # WHY: success returns a file object.
    assert diagnostic_file.path.read_bytes() == b"pcap"  # WHY: downloaded bytes reach disk.
    assert "site1" in diagnostic_file.path.name  # WHY: file name includes the site.
    assert "aabbccddeeff" in diagnostic_file.path.name  # WHY: file name includes the client MAC.
    assert run.status == STATUS_SUCCESS  # WHY: audit row marks success.


def test_recording_runner_stops_when_wait_is_interrupted(tmp_path) -> None:
    """Recording stop runs when the wait raises Ctrl+C."""
    client = FakeRecordingClient()  # WHY: fake remote calls.
    namer = RfDiagnosticFileNamer(tmp_path / "data" / "rfdiags")  # WHY: isolate download output.
    runner = RfDiagnosticRecordingRunner(client, namer=namer, wait_fn=_raise_keyboard_interrupt, clock=_fixed_clock)
    recording, diagnostic_file, run = runner.run("site1", "aabbccddeeff", 30, "name1")  # WHY: interrupt path.
    assert [call[0] for call in client.calls] == ["start", "stop"]  # WHY: finally stopped the recording.
    assert diagnostic_file is None  # WHY: interrupted run does not download.
    assert recording.status == STATUS_FAILED  # WHY: interrupted run is not reported as success.
    assert run.status == STATUS_FAILED  # WHY: audit row records the failure.


def test_recording_runner_fails_on_empty_download(tmp_path) -> None:
    """An empty RF diagnostic download becomes a failed run."""
    client = FakeRecordingClient(download_data=b"")  # WHY: simulate empty cloud download.
    namer = RfDiagnosticFileNamer(tmp_path / "data" / "rfdiags")  # WHY: isolate download output.
    runner = RfDiagnosticRecordingRunner(client, namer=namer, wait_fn=lambda seconds: None, clock=_fixed_clock)
    recording, diagnostic_file, run = runner.run("site1", "aabbccddeeff", 30, "name1")  # WHY: empty download path.
    assert [call[0] for call in client.calls] == ["start", "stop", "download"]  # WHY: download was attempted.
    assert diagnostic_file is None  # WHY: no file is returned on empty data.
    assert recording.status == STATUS_FAILED  # WHY: recording result marks failure.
    assert run.status == STATUS_FAILED  # WHY: audit row marks failure.


def _fixed_clock() -> datetime:
    """Return a deterministic UTC time."""
    return datetime(2026, 9, 29, 16, 10, 13, tzinfo=UTC)  # WHY: file names and audit rows stay stable.


def _raise_keyboard_interrupt(seconds: float) -> None:
    """Raise Ctrl+C from a fake wait function."""
    raise KeyboardInterrupt  # WHY: prove the runner stops in a finally block.
