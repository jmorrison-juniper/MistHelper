"""Mist API client for RF diagnostics operations."""

from __future__ import annotations  # WHY: keep type hints import-safe.

import logging  # WHY: log before and after each Mist API call.
from typing import Any  # WHY: Mist SDK responses are dynamic objects.

import mistapi  # WHY: use the installed Mist SDK when it exposes the operation.

logger = logging.getLogger(__name__)  # WHY: make API client logs easy to filter.


class RfDiagnosticsClient:
    """Wrap Mist API calls needed by RF diagnostics."""

    def __init__(self, mist_session: Any, sdk: Any = mistapi) -> None:
        """Store the Mist session and SDK module."""
        self._mist_session = mist_session  # WHY: every SDK call needs the active APISession.
        self._sdk = sdk  # WHY: tests inject a fake SDK without network access.

    @staticmethod
    def spectrum_body(device_id: str, band: str, duration: int, result_format: str = "json") -> dict[str, Any]:
        """Return the OpenAPI-shaped spectrum request body."""
        return {  # WHY: OpenAPI requires band and allows device_id, duration, and format.
            "band": band,  # WHY: Mist requires a band value such as 24, 5, or 6.
            "device_id": device_id,  # WHY: the AP performs the analysis.
            "duration": duration,  # WHY: bounded collection protects the operator session.
            "format": result_format,  # WHY: json lets the CLI print a bounded result.
        }

    @staticmethod
    def recording_body(name: str, client_mac: str, duration: int) -> dict[str, Any]:
        """Return the OpenAPI-shaped RF diagnostic recording body."""
        bounded_duration = (
            180 if duration <= 0 else min(duration, 180)
        )  # WHY: OpenAPI limits recordings to 180 seconds.
        return {  # WHY: OpenAPI requires name and type, and client type uses mac.
            "name": name,  # WHY: Mist stores a visible recording name.
            "type": "client",  # WHY: issue 3570 records a client RF diagnostic.
            "mac": client_mac,  # WHY: the client MAC selects the RF target.
            "duration": bounded_duration,  # WHY: zero means operator-stop mode with the cloud maximum.
        }

    @staticmethod
    def response_data(response: Any) -> Any:
        """Return payload data from a Mist SDK response or fake response."""
        return getattr(response, "data", response)  # WHY: tests pass plain data, while SDK returns APIResponse.

    def start_spectrum(self, site_id: str, device_id: str, band: str, duration: int) -> Any:
        """Start one site spectrum analysis."""
        body = self.spectrum_body(device_id, band, duration)  # WHY: isolate OpenAPI shape for tests.
        logger.info("Starting spectrum analysis for site %s and device %s", site_id, device_id)  # WHY: action log.
        response = self._sdk.api.v1.sites.analyze_spectrum.initiateSiteAnalyzeSpectrum(  # WHY: SDK exposes start.
            self._mist_session, site_id, body
        )
        logger.debug(
            "Spectrum start returned data_type=%s", type(self.response_data(response)).__name__
        )  # WHY: summary.
        return response  # WHY: runner extracts the response data.

    def get_running_spectrum(self, site_id: str) -> Any:
        """Read the current running spectrum analysis through the API-session fallback."""
        path = f"/api/v1/sites/{site_id}/analyze_spectrum"  # WHY: SDK lacks getSiteRunningSprectrumAnalysis.
        logger.info("Reading running spectrum analysis for site %s", site_id)  # WHY: action log before fallback.
        getter = self._mist_session.mist_get  # WHY: APISession owns generic GET calls.
        response = getter(path)  # WHY: call the documented path when SDK has no generated function.
        logger.debug(
            "Running spectrum returned data_type=%s", type(self.response_data(response)).__name__
        )  # WHY: summary.
        return response  # WHY: runner extracts the response data.

    def start_recording(self, site_id: str, name: str, client_mac: str, duration: int) -> Any:
        """Start one client RF diagnostic recording."""
        body = self.recording_body(name, client_mac, duration)  # WHY: isolate OpenAPI shape for tests.
        logger.info(
            "Starting RF diagnostic recording for site %s", site_id
        )  # WHY: do not log the client as secret-like.
        response = self._sdk.api.v1.sites.rfdiags.startSiteRecording(
            self._mist_session, site_id, body
        )  # WHY: SDK call.
        logger.debug(
            "RF diagnostic start returned data_type=%s", type(self.response_data(response)).__name__
        )  # WHY: summary.
        return response  # WHY: runner extracts the RF diagnostic id.

    def get_recording(self, site_id: str, rfdiag_id: str) -> Any:
        """Read one RF diagnostic recording."""
        logger.info("Reading RF diagnostic recording %s at site %s", rfdiag_id, site_id)  # WHY: action log.
        response = self._sdk.api.v1.sites.rfdiags.getSiteRfdiagRecording(  # WHY: SDK exposes the read operation.
            self._mist_session, site_id, rfdiag_id
        )
        logger.debug(
            "RF diagnostic get returned data_type=%s", type(self.response_data(response)).__name__
        )  # WHY: summary.
        return response  # WHY: caller handles payload details.

    def stop_recording(self, site_id: str, rfdiag_id: str) -> Any:
        """Stop one RF diagnostic recording."""
        logger.info("Stopping RF diagnostic recording %s at site %s", rfdiag_id, site_id)  # WHY: stop must be visible.
        response = self._sdk.api.v1.sites.rfdiags.stopSiteRfdiagRecording(  # WHY: SDK exposes the stop operation.
            self._mist_session, site_id, rfdiag_id
        )
        logger.debug(
            "RF diagnostic stop returned data_type=%s", type(self.response_data(response)).__name__
        )  # WHY: summary.
        return response  # WHY: runner can include stop result in failure handling.

    def download_recording(self, site_id: str, rfdiag_id: str) -> Any:
        """Download one RF diagnostic recording."""
        logger.info("Downloading RF diagnostic recording %s at site %s", rfdiag_id, site_id)  # WHY: action log.
        response = self._sdk.api.v1.sites.rfdiags.downloadSiteRfdiagRecording(  # WHY: SDK exposes download.
            self._mist_session, site_id, rfdiag_id
        )
        logger.debug(
            "RF diagnostic download returned data_type=%s", type(self.response_data(response)).__name__
        )  # WHY: summary.
        return response  # WHY: recording runner writes bytes to disk.

    def list_recordings(self, site_id: str, limit: int = 100) -> Any:
        """List recent RF diagnostic recordings."""
        logger.info("Listing RF diagnostic recordings for site %s", site_id)  # WHY: action log.
        response = (
            self._sdk.api.v1.sites.rfdiags.getSiteSiteRfdiagRecording(  # WHY: OpenAPI exposes this generated name.
                self._mist_session, site_id, limit=limit
            )
        )
        logger.debug(
            "RF diagnostic list returned data_type=%s", type(self.response_data(response)).__name__
        )  # WHY: summary.
        return response  # WHY: callers can reconcile recorded IDs if needed.
