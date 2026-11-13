"""Offline tests for the multi-AP workflow and packet-length prompts."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, call, patch

import pytest

from src.foundation.support.refactors.serial_cc.start_site_client_capture_wireless import (
    SiteWirelessClientCaptureService,
)
from src.foundation.support.utils.input_utils import InputUtils
from src.operations.execution.capture._packet_capture_prompts import PacketCapturePrompts
from src.operations.execution.capture.multi_ap_scan_workflow import MultiApScanCaptureWorkflow


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
    assert workflow.mistapi_module.api.v1.sites.pcaps.startSitePacketCapture.call_count == 0  # No APs means no capture.
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


@pytest.mark.parametrize("prompt_path", ["shared", "wireless"])
@pytest.mark.parametrize(
    "case",
    [pytest.param((str(length), length, ""), id=str(length)) for length in range(64, 1537)]
    + [
        pytest.param(
            (str(length), None, "\n! Max packet length must be between 64 and 1536 bytes"),
            id=f"rejected-{length}",
        )
        for length in [*range(1537, 2050), 63, 0, -1, 9999]
    ]
    + [
        pytest.param((" \t64 ", 64, ""), id="padded-minimum"),
        pytest.param((" 1536\t ", 1536, ""), id="padded-maximum"),
        pytest.param(("text", None, "\n! Invalid max packet length: text"), id="text"),
        pytest.param(("64.0", None, "\n! Invalid max packet length: 64.0"), id="fraction"),
        pytest.param(("1e3", None, "\n! Invalid max packet length: 1e3"), id="scientific-notation"),
        pytest.param((KeyboardInterrupt, None, "\n! Invalid max packet length: "), id="interruption"),
    ],
)
def test_packet_length_prompt_limits(
    prompt_path: str,
    case: tuple[str | type[KeyboardInterrupt], int | None, str],
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Exercise all numeric limits and actual messages through real safe_input."""
    raw_input, expected_length, message = case
    inputs = [raw_input] if prompt_path == "shared" else ["120", "7", raw_input]
    with patch("builtins.input", side_effect=inputs) as terminal_input:
        if prompt_path == "shared":
            result = PacketCapturePrompts.prompt_max_packet_length()
        else:
            result = SiteWirelessClientCaptureService._collect_bounded_ints(InputUtils)
    expected_settings = None if expected_length is None else (120, 7, expected_length)
    assert result == (expected_length if prompt_path == "shared" else expected_settings)
    default = 128 if prompt_path == "shared" else 1300
    assert terminal_input.call_args == call(f"Enter max packet length in bytes (default {default}, max 1536): ")
    assert capsys.readouterr().out == (message + "\n" if prompt_path == "shared" and message else "")
    if prompt_path == "wireless" and message:
        assert (SiteWirelessClientCaptureService.__module__, logging.WARNING, message) in caplog.record_tuples
    if raw_input is KeyboardInterrupt:
        assert "[INTERRUPT] User interrupted max_pkt_len. Canceling..." in caplog.messages


@pytest.mark.parametrize("prompt_path", ["shared", "wireless"])
@pytest.mark.parametrize(
    "case",
    [
        pytest.param(("", 128, True), id="blank-default"),
        pytest.param((" ", 128, True), id="spaces-default"),
        pytest.param(("\t", 128, True), id="tabs-default"),
        pytest.param(("", 1300, True), id="blank-caller-default"),
        pytest.param((" ", 1300, True), id="spaces-caller-default"),
        pytest.param(("\t", 1300, True), id="tabs-caller-default"),
        pytest.param((EOFError, 128, False), id="eof-default"),
        pytest.param((EOFError, 1300, False), id="eof-caller-default"),
        pytest.param((EOFError, 128, True), id="eof-whole-sequence"),
    ],
)
def test_packet_length_prompt_defaults(
    prompt_path: str, case: tuple[str | type[EOFError], int, bool], caplog: pytest.LogCaptureFixture
) -> None:
    """Preserve blank and EOF defaults through the real input helper."""
    raw_input, shared_default, whole_sequence = case
    wireless_inputs = [raw_input] * 3 if whole_sequence else ["120", "7", raw_input]
    inputs = [raw_input] if prompt_path == "shared" else wireless_inputs
    with patch("builtins.input", side_effect=inputs) as terminal_input:
        if prompt_path == "shared":
            result = PacketCapturePrompts.prompt_max_packet_length(default=shared_default)
        else:
            result = SiteWirelessClientCaptureService._collect_bounded_ints(InputUtils)
    expected_settings = (60, 1024, 1300) if whole_sequence else (120, 7, 1300)
    assert result == (shared_default if prompt_path == "shared" else expected_settings)
    default = shared_default if prompt_path == "shared" else 1300
    assert terminal_input.call_args == call(f"Enter max packet length in bytes (default {default}, max 1536): ")
    if raw_input is EOFError:
        assert f"[EOF] Input stream closed during max_pkt_len. Using default value: '{default}'" in caplog.messages
        assert len(caplog.records) == (3 if prompt_path == "wireless" and whole_sequence else 1)
    else:
        assert caplog.messages == []
