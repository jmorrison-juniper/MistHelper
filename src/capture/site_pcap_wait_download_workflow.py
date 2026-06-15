"""Workflow extraction for site-level PCAP wait-and-download behavior."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.capture.packet_capture_download import PacketCaptureDownloadManager


@dataclass
class SitePcapWaitDownloadWorkflow:
    """Wait for and download site-level PCAP captures using legacy behavior."""

    manager: Any
    mistapi_module: Any
    requests_module: Any

    def execute(self, site_id: str, capture_id: str, duration: int) -> None:
        """Execute legacy-equivalent wait/download flow for site captures."""
        logging.info(
            "Starting site PCAP wait/download workflow for site_id=%s capture_id=%s", site_id, capture_id
        )  # Log workflow entry with key identifiers for traceability.
        logging.info(
            "Initializing packet-capture download manager"
        )  # Log before constructing helper object used by polling flow.
        download_manager = (
            PacketCaptureDownloadManager()
        )  # Create helper manager that owns polling and file-download mechanics.
        logging.debug(
            "Packet-capture download manager initialized successfully"
        )  # Log successful helper initialization.
        logging.info(
            "Invoking poll_and_download_pcap for site capture_id=%s", capture_id
        )  # Log before triggering polling/download state machine.

        def save_callback(
            pcap_url: str, capture_identifier: str, capture_prefix: str
        ) -> None:  # Callback returns None; return value of save_pcap_file is intentionally discarded.
            return download_manager.save_pcap_file(  # Delegate save operation to shared manager.
                pcap_url,  # Pass URL discovered by polling flow for actual file retrieval.
                capture_identifier,  # Pass capture identifier for deterministic filename generation.
                capture_prefix,  # Pass prefix so filename conventions remain compatibility-safe.
                requests_module=self.requests_module,  # Inject requests dependency.
            )

        download_manager.poll_and_download_pcap(  # Execute polling and download sequence.
            list_captures_fn=lambda: self.mistapi_module.api.v1.sites.pcaps.listSitePacketCaptures(  # List callback.
                self.manager.mist_session,  # Reuse active authenticated session.
                site_id,  # Scope capture-list lookup to the selected site.
            ),
            capture_id=capture_id,
            duration=duration,
            prefix="",
            save_pcap_file_fn=save_callback,  # Reuse prepared save callback.
        )
        logging.debug(
            "Completed poll_and_download_pcap for site capture_id=%s", capture_id
        )  # Log workflow completion after polling/download returns.

    def run(self, site_id: str, capture_id: str, duration: int) -> None:
        """Temporary compatibility adapter for legacy callsites.

        Expiry: 2026-08-31 (remove after canonical execute()-path test migration closes).
        """
        logging.info(
            "Running site PCAP wait/download compatibility alias"
        )  # Log alias invocation so compatibility path is visible in logs.
        self.execute(
            site_id, capture_id, duration
        )  # Delegate to canonical execute method to preserve single implementation path.
        logging.debug(
            "Completed site PCAP wait/download compatibility alias"
        )  # Log alias completion to bracket the compatibility call path.
