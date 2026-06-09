"""Workflow extraction for org-level PCAP wait-and-download behavior."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.capture.packet_capture_download import PacketCaptureDownloadManager


@dataclass
class OrgPcapWaitDownloadWorkflow:
    """Wait for and download organization-level PCAP captures with parity behavior."""

    manager: Any
    mistapi_module: Any
    requests_module: Any

    def execute(self, org_id: str, capture_id: str, duration: int) -> None:
        """Execute legacy-equivalent wait/download flow for organization captures."""
        logging.info(
            "Starting org PCAP wait/download workflow for org_id=%s capture_id=%s", org_id, capture_id
        )  # Log workflow entry with identifiers to support troubleshooting.
        logging.info(
            "Initializing packet-capture download manager"
        )  # Log before constructing helper manager used by polling flow.
        download_manager = (
            PacketCaptureDownloadManager()
        )  # Create helper manager that handles polling and file persistence.
        logging.debug(
            "Packet-capture download manager initialized successfully"
        )  # Log successful helper initialization for observability.
        logging.info(
            "Invoking poll_and_download_pcap for org capture_id=%s", capture_id
        )  # Log before entering polling/download state machine.

        def save_callback(
            pcap_url: str, capture_identifier: str, capture_prefix: str
        ) -> None:  # Callback returns None; return value of save_pcap_file is intentionally discarded.
            return download_manager.save_pcap_file(  # Delegate save operation to shared manager.
                pcap_url,  # Pass resolved download URL from polling results.
                capture_identifier,  # Pass capture identifier for deterministic output filename.
                capture_prefix,  # Pass org prefix to preserve org capture filename conventions.
                requests_module=self.requests_module,  # Inject requests dependency.
            )

        download_manager.poll_and_download_pcap(  # Execute org-level polling and download.
            list_captures_fn=lambda: self.mistapi_module.api.v1.orgs.pcaps.listOrgPacketCaptures(  # List callback.
                self.manager.mist_session,  # Reuse authenticated session from parent manager to maintain API context.
                org_id,  # Scope polling query to selected organization.
            ),
            capture_id=capture_id,
            duration=duration,
            prefix="org_",
            save_pcap_file_fn=save_callback,  # Reuse prepared save callback.
        )
        logging.debug(
            "Completed poll_and_download_pcap for org capture_id=%s", capture_id
        )  # Log workflow completion after polling/download returns.

    def run(self, org_id: str, capture_id: str, duration: int) -> None:
        """Backward-compatible alias for existing unit tests."""
        logging.info(
            "Running org PCAP wait/download compatibility alias"
        )  # Log alias entry so compatibility facade path is explicit.
        self.execute(org_id, capture_id, duration)  # Delegate to canonical execute method to keep behavior centralized.
        logging.debug(
            "Completed org PCAP wait/download compatibility alias"
        )  # Log alias completion to bracket compatibility execution.
