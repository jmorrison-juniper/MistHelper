"""Unit tests for src.capture.multi_ap_scan_workflow."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.capture.multi_ap_scan_workflow import MultiApScanCaptureWorkflow


def _build_workflow() -> tuple[MultiApScanCaptureWorkflow, MagicMock, MagicMock, MagicMock]:
    """Create a workflow instance with mocked collaborators."""
    manager = MagicMock()
    manager.mist_session = MagicMock()
    manager._get_capture_format_selection.return_value = "pcap"
    manager.normalize_mac_address.side_effect = lambda value: value.lower()
    mistapi_module = MagicMock()
    input_utils = MagicMock()
    device_utils = MagicMock()
    workflow = MultiApScanCaptureWorkflow(manager, mistapi_module, input_utils, device_utils)
    return workflow, manager, mistapi_module, input_utils


def test_run_returns_when_no_aps() -> None:
    """Workflow should short-circuit when no APs are returned."""
    workflow, _manager, _mistapi, _input = _build_workflow()
    workflow.device_utils.get_all_ap_macs_from_site.return_value = []
    workflow.run("site-1")
    workflow.mistapi_module.api.v1.sites.pcaps.startSitePacketCapture.assert_not_called()


def test_run_starts_capture_and_waits_for_pcap() -> None:
    """Workflow should submit multi-AP capture and invoke wait/download for pcap format."""
    workflow, manager, mistapi_module, input_utils = _build_workflow()
    workflow.device_utils.get_all_ap_macs_from_site.return_value = ["AA:BB:CC:DD:EE:FF"]
    input_utils.safe_input.side_effect = ["2", "36", "1", "60", "1024", ""]
    list_response = MagicMock()
    list_response.status_code = 200
    list_response.data = []
    start_response = MagicMock()
    start_response.status_code = 200
    start_response.data = {"id": "cap-1", "ap_count": 1}
    mistapi_module.api.v1.sites.pcaps.listSitePacketCaptures.return_value = list_response
    mistapi_module.api.v1.sites.pcaps.startSitePacketCapture.return_value = start_response

    workflow.run("site-1")

    mistapi_module.api.v1.sites.pcaps.startSitePacketCapture.assert_called_once()
    manager._wait_and_download_pcap.assert_called_once_with("site-1", "cap-1", 60)
