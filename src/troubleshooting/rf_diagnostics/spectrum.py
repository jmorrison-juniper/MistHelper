"""Spectrum analysis runner for RF diagnostics."""

from __future__ import annotations  # WHY: keep annotations import-safe.

import logging  # WHY: log poll actions and outcomes.
import time  # WHY: sleep between bounded poll attempts.
from collections.abc import Callable  # WHY: tests inject a fake sleep function.
from datetime import UTC, datetime  # WHY: stamp audit-ready result objects.
from typing import Any  # WHY: Mist payloads are dynamic JSON.

from src.troubleshooting.rf_diagnostics.client import RfDiagnosticsClient  # WHY: runner calls the API client seam.
from src.troubleshooting.rf_diagnostics.models import (  # WHY: outcomes.  # WHY: return data.
    STATUS_FAILED,
    STATUS_SUCCESS,
    STATUS_TIMEOUT,
    RfDiagnosticRun,
    SpectrumAnalysisSession,
)

logger = logging.getLogger(__name__)  # WHY: make spectrum runner logs easy to filter.

_RUNNING_VALUES = {"running", "started", "in_progress", "active"}  # WHY: Mist states can vary by payload.
_FAILURE_VALUES = {"failed", "failure", "error"}  # WHY: failed states must not be audited as success.


class SpectrumAnalysisRunner:
    """Start and poll one AP spectrum analysis."""

    def __init__(
        self,
        client: RfDiagnosticsClient,
        sleep_fn: Callable[[float], None] = time.sleep,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Store injected collaborators for deterministic tests."""
        self._client = client  # WHY: one client owns all Mist calls.
        self._sleep = sleep_fn  # WHY: tests skip real waiting.
        self._clock = clock or (lambda: datetime.now(UTC))  # WHY: one timestamp source aids tests.

    @staticmethod
    def _status(payload: dict[str, Any]) -> str:
        """Return the best available status text from a spectrum payload."""
        value = payload.get("status") or payload.get("state") or payload.get("format")  # WHY: schemas vary here.
        return str(value or "complete").lower()  # WHY: missing state means the payload itself is the result.

    @staticmethod
    def _summary(payload: dict[str, Any]) -> str:
        """Return a compact spectrum result summary."""
        fields = ["band", "device_id", "duration", "format", "started_time", "status"]  # WHY: useful safe keys.
        parts = [f"{field}={payload[field]}" for field in fields if field in payload]  # WHY: omit absent values.
        return ", ".join(parts) if parts else "spectrum result received"  # WHY: never return an empty message.

    def run(
        self,
        site_id: str,
        device_id: str,
        band: str,
        duration: int,
        poll_limit: int = 5,
        poll_interval: float = 1.0,
    ) -> tuple[SpectrumAnalysisSession, RfDiagnosticRun]:
        """Start spectrum analysis and return the final session and audit row."""
        started_at = self._clock().isoformat(timespec="seconds")  # WHY: audit row and operator output share one time.
        try:  # WHY: convert API failures into a failed run row.
            start_response = self._client.start_spectrum(site_id, device_id, band, duration)  # WHY: begin analysis.
            start_payload = self._payload(start_response)  # WHY: normalize SDK response shape.
            final_payload = self._poll(site_id, start_payload, poll_limit, poll_interval)  # WHY: wait for result.
            final_status = self._final_status(final_payload)  # WHY: Mist can return a failed final state.
            session = SpectrumAnalysisSession(site_id, device_id, final_status, final_payload)  # WHY: caller prints.
            run = RfDiagnosticRun(MODE, site_id, device_id, started_at, final_status, self._summary(final_payload))
            return session, run  # WHY: caller writes audit exactly once.
        except TimeoutError as error:  # WHY: poll timeout is a controlled outcome.
            return self._failed(site_id, device_id, started_at, STATUS_TIMEOUT, str(error))  # WHY: audit timeout.
        except Exception as error:  # pylint: disable=broad-exception-caught
            logger.exception("Spectrum analysis failed: %s", error)  # WHY: preserve stack trace for troubleshooting.
            return self._failed(site_id, device_id, started_at, STATUS_FAILED, str(error))  # WHY: audit failure.

    @staticmethod
    def _final_status(payload: dict[str, Any]) -> str:
        """Return success or failure for a final spectrum payload."""
        if SpectrumAnalysisRunner._status(payload) in _FAILURE_VALUES:  # WHY: failed states must not audit success.
            return STATUS_FAILED  # WHY: record the Mist final state as a failure.
        return STATUS_SUCCESS  # WHY: any non-failed final payload is a successful collection.

    def _poll(
        self, site_id: str, first_payload: dict[str, Any], poll_limit: int, poll_interval: float
    ) -> dict[str, Any]:
        """Poll running spectrum state until final data or timeout."""
        payload = first_payload  # WHY: start response can already hold enough detail.
        for attempt in range(max(poll_limit, 1)):  # WHY: bounded poll prevents an endless CLI wait.
            logger.info("Polling spectrum analysis attempt %s for site %s", attempt + 1, site_id)  # WHY: action log.
            payload = self._payload(self._client.get_running_spectrum(site_id))  # WHY: read current state.
            logger.debug("Spectrum poll attempt %s status=%s", attempt + 1, self._status(payload))  # WHY: summary.
            if self._status(payload) not in _RUNNING_VALUES:  # WHY: non-running payload is final enough to print.
                return payload  # WHY: caller can summarize final data.
            self._sleep(poll_interval)  # WHY: avoid a tight loop against the Mist API.
        raise TimeoutError("Spectrum analysis did not finish before the poll limit.")  # WHY: controlled timeout.

    @staticmethod
    def _payload(response: Any) -> dict[str, Any]:
        """Return one dictionary payload from a Mist response."""
        data = RfDiagnosticsClient.response_data(response)  # WHY: unwrap SDK and fake responses consistently.
        if isinstance(data, dict):  # WHY: expected shape for spectrum state.
            return data  # WHY: caller reads known fields.
        if isinstance(data, list) and data and isinstance(data[0], dict):  # WHY: tolerate list-shaped SDK data.
            return data[0]  # WHY: first row is the current state.
        return {"status": "complete", "value": str(data)}  # WHY: preserve unusual but safe data as text.

    @staticmethod
    def _failed(
        site_id: str,
        device_id: str,
        started_at: str,
        status: str,
        message: str,
    ) -> tuple[SpectrumAnalysisSession, RfDiagnosticRun]:
        """Return failed spectrum data and one audit row."""
        payload = {"status": status, "message": message}  # WHY: caller needs a safe failure summary.
        session = SpectrumAnalysisSession(site_id, device_id, status, payload)  # WHY: operation prints this result.
        run = RfDiagnosticRun(MODE, site_id, device_id, started_at, status, message)  # WHY: audit still gets one row.
        return session, run  # WHY: caller writes audit exactly once.


MODE = "spectrum"  # WHY: keep the audit mode value local and stable.
