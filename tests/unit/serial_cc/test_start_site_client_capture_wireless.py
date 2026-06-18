"""Unit tests for offender wireless client capture service extraction."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.refactors.serial_cc.start_site_client_capture_wireless import SiteWirelessClientCaptureService


def _build_manager():
    manager = SimpleNamespace()
    manager.mist_session = MagicMock()
    manager.validate_mac_address = MagicMock(return_value=True)
    manager.normalize_mac_address = MagicMock(side_effect=lambda value: value.lower())
    manager._get_tcpdump_expression_selection = MagicMock(return_value="")
    manager._get_capture_format_selection = MagicMock(return_value="pcap")
    manager._execute_site_capture_loop = MagicMock()
    manager._execute_site_capture = MagicMock()
    return manager


@patch("src.refactors.serial_cc.start_site_client_capture_wireless._resolve_prompt_helpers")
def test_site_selection_cancelled_returns_early(mock_resolve_prompt_helpers):
    manager = _build_manager()
    input_utils = MagicMock()
    prompt_utils = MagicMock()
    prompt_client_utils = MagicMock()
    prompt_network_device_utils = MagicMock()
    prompt_utils.select_site_with_logging.return_value = None
    mock_resolve_prompt_helpers.return_value = (
        input_utils,
        prompt_utils,
        prompt_client_utils,
        prompt_network_device_utils,
    )

    SiteWirelessClientCaptureService.execute(manager)

    prompt_client_utils.select_client_mac.assert_not_called()
    manager._execute_site_capture.assert_not_called()


@patch("src.refactors.serial_cc.start_site_client_capture_wireless._resolve_prompt_helpers")
def test_invalid_client_mac_returns_before_capture(mock_resolve_prompt_helpers):
    manager = _build_manager()
    manager.validate_mac_address.return_value = False
    input_utils = MagicMock()
    prompt_utils = MagicMock()
    prompt_client_utils = MagicMock()
    prompt_network_device_utils = MagicMock()
    prompt_utils.select_site_with_logging.return_value = "site-1"
    input_utils.safe_input.side_effect = ["1"]
    prompt_client_utils.select_client_mac.return_value = "bad-mac"
    mock_resolve_prompt_helpers.return_value = (
        input_utils,
        prompt_utils,
        prompt_client_utils,
        prompt_network_device_utils,
    )

    SiteWirelessClientCaptureService.execute(manager)

    manager._execute_site_capture.assert_not_called()
    manager._execute_site_capture_loop.assert_not_called()


@patch("src.refactors.serial_cc.start_site_client_capture_wireless._resolve_prompt_helpers")
def test_full_flow_single_capture(mock_resolve_prompt_helpers):
    manager = _build_manager()
    input_utils = MagicMock()
    prompt_utils = MagicMock()
    prompt_client_utils = MagicMock()
    prompt_network_device_utils = MagicMock()
    prompt_utils.select_site_with_logging.return_value = "site-1"
    prompt_client_utils.select_client_mac.return_value = "aa:bb:cc:dd:ee:ff"
    input_utils.safe_input.side_effect = [
        "1",  # client mode
        "3",  # AP filter skip
        "120",  # duration
        "1024",  # packets
        "1300",  # pkt len
        "n",  # mcast
        "n",  # loop mode
        "",  # confirmation
    ]
    mock_resolve_prompt_helpers.return_value = (
        input_utils,
        prompt_utils,
        prompt_client_utils,
        prompt_network_device_utils,
    )

    SiteWirelessClientCaptureService.execute(manager)

    manager._execute_site_capture.assert_called_once()
    manager._execute_site_capture_loop.assert_not_called()
