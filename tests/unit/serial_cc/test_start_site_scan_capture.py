"""Unit tests for scan capture service extraction."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.refactors.serial_cc.start_site_scan_capture import SiteScanCaptureService


def _build_manager():
    manager = SimpleNamespace()
    manager.mist_session = MagicMock()
    manager.normalize_mac_address = MagicMock(side_effect=lambda value: value.lower())
    manager._get_capture_format_selection = MagicMock(return_value="pcap")
    manager._execute_site_capture_loop = MagicMock()
    manager._execute_site_capture = MagicMock()
    manager._start_site_scan_capture_all_aps = MagicMock()
    return manager


@patch("src.refactors.serial_cc.start_site_scan_capture._resolve_prompt_helpers")
def test_no_site_selected_returns_early(mock_resolve_prompt_helpers):
    manager = _build_manager()
    input_utils = MagicMock()
    prompt_utils = MagicMock()
    prompt_network_device_utils = MagicMock()
    device_utils = MagicMock()
    mistapi_module = MagicMock()
    prompt_utils.select_site_with_logging.return_value = None
    mock_resolve_prompt_helpers.return_value = (
        input_utils,
        prompt_utils,
        prompt_network_device_utils,
        device_utils,
        mistapi_module,
    )

    SiteScanCaptureService.execute(manager)

    manager._execute_site_capture.assert_not_called()


@patch("src.refactors.serial_cc.start_site_scan_capture._resolve_prompt_helpers")
def test_all_aps_path_delegates_to_all_ap_handler(mock_resolve_prompt_helpers):
    manager = _build_manager()
    input_utils = MagicMock()
    prompt_utils = MagicMock()
    prompt_network_device_utils = MagicMock()
    device_utils = MagicMock()
    mistapi_module = MagicMock()
    prompt_utils.select_site_with_logging.return_value = "site-1"
    prompt_utils_instance = MagicMock()
    prompt_utils_instance.select_ap_mac.return_value = "ALL_APS"
    prompt_network_device_utils.return_value = prompt_utils_instance
    mock_resolve_prompt_helpers.return_value = (
        input_utils,
        prompt_utils,
        prompt_network_device_utils,
        device_utils,
        mistapi_module,
    )

    SiteScanCaptureService.execute(manager)

    manager._start_site_scan_capture_all_aps.assert_called_once_with("site-1")


@patch("src.refactors.serial_cc.start_site_scan_capture._resolve_prompt_helpers")
def test_full_flow_single_capture(mock_resolve_prompt_helpers):
    manager = _build_manager()
    input_utils = MagicMock()
    prompt_utils = MagicMock()
    prompt_network_device_utils = MagicMock()
    device_utils = MagicMock()
    mistapi_module = MagicMock()
    prompt_utils.select_site_with_logging.return_value = "site-1"
    prompt_utils_instance = MagicMock()
    prompt_utils_instance.select_ap_mac.return_value = "aa:bb:cc:dd:ee:ff"
    prompt_network_device_utils.return_value = prompt_utils_instance
    input_utils.safe_input.side_effect = [
        "2",  # band
        "36",  # channel
        "1",  # bandwidth
        "120",  # duration
        "1024",  # packets
        "n",  # loop mode
        "",  # confirm
    ]
    mistapi_module.api.v1.sites.pcaps.listSitePacketCaptures.return_value = SimpleNamespace(status_code=500, data=[])
    mock_resolve_prompt_helpers.return_value = (
        input_utils,
        prompt_utils,
        prompt_network_device_utils,
        device_utils,
        mistapi_module,
    )

    SiteScanCaptureService.execute(manager)

    manager._execute_site_capture.assert_called_once()
    manager._execute_site_capture_loop.assert_not_called()
