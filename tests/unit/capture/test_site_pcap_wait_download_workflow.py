"""Unit tests for src.capture.site_pcap_wait_download_workflow."""

from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from src.capture.site_pcap_wait_download_workflow import SitePcapWaitDownloadWorkflow


def test_execute_calls_site_list_callback_and_download_manager() -> None:
    """Workflow should delegate to PacketCaptureDownloadManager with site callback."""
    manager = MagicMock()
    manager.mist_session = MagicMock()
    mistapi_module = MagicMock()
    requests_module = MagicMock()
    workflow = SitePcapWaitDownloadWorkflow(manager, mistapi_module, requests_module)

    response = MagicMock()
    response.status_code = 200
    response.data = []
    mistapi_module.api.v1.sites.pcaps.listSitePacketCaptures.return_value = response

    with patch("src.capture.site_pcap_wait_download_workflow.PacketCaptureDownloadManager") as mock_manager_cls:
        mock_manager = MagicMock()
        mock_manager_cls.return_value = mock_manager
        workflow.execute("site-1", "capture-1", 60)

    mock_manager.poll_and_download_pcap.assert_called_once()
