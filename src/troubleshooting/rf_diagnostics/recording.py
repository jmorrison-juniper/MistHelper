"""RF diagnostic recording runner."""

from __future__ import annotations  # WHY: keep annotations import-safe.

import logging  # WHY: log start, wait, stop, download, and file actions.
import time  # WHY: provide the default wait function.
from collections.abc import Callable  # WHY: tests inject fake wait and clock functions.
from datetime import UTC, datetime  # WHY: timestamp downloads and audit rows.
from typing import Any  # WHY: Mist SDK response payloads are dynamic.

from src.troubleshooting.rf_diagnostics.client import RfDiagnosticsClient  # WHY: runner calls the API seam.
from src.troubleshooting.rf_diagnostics.file_naming import RfDiagnosticFileNamer  # WHY: centralize safe file names.
from src.troubleshooting.rf_diagnostics.models import (  # WHY: audit outcome constants.
    STATUS_FAILED,
    STATUS_SUCCESS,
    RfDiagnosticFile,
    RfDiagnosticRecording,
    RfDiagnosticRun,
)  # WHY: data.

logger = logging.getLogger(__name__)  # WHY: make recording runner logs easy to filter.


class RfDiagnosticRecordingRunner:
    """Start, stop, and download one client RF diagnostic recording."""

    def __init__(
        self,
        client: RfDiagnosticsClient,
        namer: RfDiagnosticFileNamer | None = None,
        wait_fn: Callable[[float], None] = time.sleep,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Store injected collaborators for deterministic tests."""
        self._client = client  # WHY: one client owns Mist calls.
        self._namer = namer or RfDiagnosticFileNamer()  # WHY: default path is data/rfdiags.
        self._wait = wait_fn  # WHY: tests avoid real wait time.
        self._clock = clock or (lambda: datetime.now(UTC))  # WHY: one timestamp source aids tests.

    def run(
        self,
        site_id: str,
        client_mac: str,
        duration: int,
        name: str,
    ) -> tuple[RfDiagnosticRecording, RfDiagnosticFile | None, RfDiagnosticRun]:
        """Run a recording and always stop it after start."""
        started_at = self._clock().isoformat(timespec="seconds")  # WHY: audit time matches file-name time source.
        rfdiag_id = ""  # WHY: finally needs a sentinel before start returns.
        try:  # WHY: turn failures into one audit row.
            response = self._client.start_recording(site_id, name, client_mac, duration)  # WHY: start recording first.
            rfdiag_id = self._extract_id(response)  # WHY: stop and download need this identifier.
            try:  # WHY: Ctrl+C must stop the recording in the finally block below.
                self._wait_for_operator(duration)  # WHY: recording continues for the requested window.
            finally:  # WHY: stop must run even when wait raises KeyboardInterrupt.
                self._client.stop_recording(
                    site_id, rfdiag_id
                )  # WHY: prevent a running recording from being left behind.
            diagnostic_file = self._download(site_id, client_mac, rfdiag_id)  # WHY: persist evidence for the operator.
            recording = RfDiagnosticRecording(site_id, client_mac, rfdiag_id, STATUS_SUCCESS, {"id": rfdiag_id})
            run = RfDiagnosticRun(MODE, site_id, client_mac, started_at, STATUS_SUCCESS, str(diagnostic_file.path))
            return recording, diagnostic_file, run  # WHY: caller prints and audits exactly once.
        except KeyboardInterrupt as error:  # WHY: Ctrl+C is not an Exception, but it still needs an audit row.
            logger.warning("RF diagnostic recording was interrupted after stop for site %s", site_id)  # WHY: notice.
            message = str(error) or "operator interrupted the recording wait"  # WHY: audit cannot use an empty detail.
            recording = RfDiagnosticRecording(site_id, client_mac, rfdiag_id, STATUS_FAILED, {"message": message})
            run = RfDiagnosticRun(MODE, site_id, client_mac, started_at, STATUS_FAILED, message)
            return recording, None, run  # WHY: caller still writes one audit row.
        except Exception as error:  # pylint: disable=broad-exception-caught
            logger.exception("RF diagnostic recording failed: %s", error)  # WHY: preserve the full stack for triage.
            recording = RfDiagnosticRecording(site_id, client_mac, rfdiag_id, STATUS_FAILED, {"message": str(error)})
            run = RfDiagnosticRun(MODE, site_id, client_mac, started_at, STATUS_FAILED, str(error))
            return recording, None, run  # WHY: caller still writes one audit row.

    def _wait_for_operator(self, duration: int) -> None:
        """Wait for a duration, or until the operator interrupts an open wait."""
        logger.info("Waiting for RF diagnostic recording duration=%s", duration)  # WHY: action log before wait.
        if duration > 0:  # WHY: positive duration gives an automatic stop.
            self._wait(float(duration))  # WHY: injected wait makes tests fast.
            logger.debug("Finished timed RF diagnostic wait duration=%s", duration)  # WHY: result summary.
            return  # WHY: stop happens in the caller finally block.
        while True:  # WHY: zero duration means the operator stops with Ctrl+C.
            self._wait(1.0)  # WHY: short sleep keeps the loop responsive to Ctrl+C.

    def _download(self, site_id: str, client_mac: str, rfdiag_id: str) -> RfDiagnosticFile:
        """Download and save one RF diagnostic recording."""
        moment = self._clock()  # WHY: the file name must hold the run time.
        target_path = self._namer.build_recording_path(site_id, client_mac, moment)  # WHY: central safe path builder.
        logger.info("Writing RF diagnostic download to %s", target_path)  # WHY: action log before disk write.
        raw_bytes = self._bytes(self._client.download_recording(site_id, rfdiag_id))  # WHY: unwrap download payload.
        if not raw_bytes:  # WHY: an empty capture is not useful evidence.
            raise ValueError("The RF diagnostic download returned no bytes.")  # WHY: audit as a failed run.
        target_path.parent.mkdir(parents=True, exist_ok=True)  # WHY: data/rfdiags may not exist yet.
        target_path.write_bytes(raw_bytes)  # WHY: persist the downloaded capture for later analysis.
        logger.debug("Wrote RF diagnostic download bytes=%s", len(raw_bytes))  # WHY: result summary after write.
        return RfDiagnosticFile(target_path, len(raw_bytes))  # WHY: caller prints path and size.

    @staticmethod
    def _extract_id(response: Any) -> str:
        """Return the RF diagnostic identifier from a response."""
        data = RfDiagnosticsClient.response_data(response)  # WHY: unwrap SDK and fake responses consistently.
        if isinstance(data, dict) and data.get("id"):  # WHY: common object response shape.
            return str(data["id"])  # WHY: stop and download need a string identifier.
        if isinstance(data, list) and data and isinstance(data[0], dict) and data[0].get("id"):  # WHY: list shape.
            return str(data[0]["id"])  # WHY: use the first created recording.
        raise ValueError("The RF diagnostic start response did not include an id.")  # WHY: stop cannot proceed safely.

    @staticmethod
    def _bytes(response: Any) -> bytes:
        """Return downloaded bytes from a response."""
        data = RfDiagnosticsClient.response_data(response)  # WHY: unwrap SDK and fake responses consistently.
        if isinstance(data, bytes):  # WHY: expected download shape.
            return data  # WHY: write bytes unchanged.
        if isinstance(data, bytearray):  # WHY: tolerate mutable byte arrays from tests.
            return bytes(data)  # WHY: write immutable bytes.
        content = getattr(response, "content", None)  # WHY: some clients expose bytes as content.
        return content if isinstance(content, bytes) else b""  # WHY: empty bytes makes caller fail safely.


MODE = "recording"  # WHY: keep the audit mode value local and stable.
