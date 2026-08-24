"""Security tests for capture payload logging in ``PacketCaptureManager``.

These tests protect the fix for issue #1734. CodeQL reported that the scan
flow logged the whole capture payload as clear text. A capture payload can
carry a device MAC, a client MAC, an SSID, a tcpdump filter, or a future
credential field. The scan flow now logs the payload field names only.

Each test fails if a later change restores the raw payload log line.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.capture.packet_capture import PacketCaptureManager

AP_MAC = "001122334455"  # WHY: device identifier that the payload log must never hold
SCAN_PARAMS: dict[str, Any] = {  # WHY: stand in for the radio prompts so the test needs no user input
    "channel": 36,  # WHY: sample 5 GHz channel
    "bandwidth": "40",  # WHY: sample channel width
    "duration": 60,  # WHY: Mist enforces a 60 second minimum
    "num_packets": 1024,  # WHY: default packet cap
    "format": "pcap",  # WHY: default capture format
}


@pytest.fixture()
def manager() -> PacketCaptureManager:
    """Create a PacketCaptureManager with a deterministic org id."""
    with patch("src.capture.packet_capture._get_config_utils") as config_utils:  # WHY: block the org id prompt
        config_utils.return_value.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: fixed org id
        return PacketCaptureManager(MagicMock(), org_id=None)  # WHY: a mock session makes no network call


def _run_scan_flow(capture_manager: PacketCaptureManager) -> None:
    """Run the single-AP scan flow with every collaborator replaced by a mock."""
    with patch.multiple(  # WHY: class-level patch keeps mypy happy and needs no method assignment
        PacketCaptureManager,
        _prompt_scan_band=MagicMock(return_value="5"),  # WHY: skip the interactive band prompt
        _gather_scan_radio_params=MagicMock(return_value=dict(SCAN_PARAMS)),  # WHY: skip the radio prompts
        _prompt_loop_mode=MagicMock(return_value=False),  # WHY: a single capture keeps the flow short
        _display_scan_capture_summary=MagicMock(),  # WHY: block the console summary
        _run_site_capture=MagicMock(),  # WHY: block the live capture call
    ):
        capture_manager._scan_single_ap_run("site-1", AP_MAC)  # WHY: run the real payload log statement


def _payload_log_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Return every captured log message that reports the constructed payload."""
    return [
        record.getMessage() for record in caplog.records if "Payload constructed" in record.getMessage()
    ]  # WHY: isolate the log line that issue #1734 flagged


def test_payload_log_omits_the_ap_mac(manager: PacketCaptureManager, caplog: pytest.LogCaptureFixture) -> None:
    """The scan flow must not write the AP MAC into the payload log line."""
    with caplog.at_level(logging.DEBUG):  # WHY: the payload log line runs at DEBUG level
        _run_scan_flow(manager)  # WHY: exercise the production code path
    lines = _payload_log_lines(caplog)  # WHY: read back the payload log records
    assert lines, "The scan flow must still log the payload shape"  # WHY: catch a silent removal of the audit line
    assert all(AP_MAC not in line for line in lines)  # WHY: fails if a change restores the raw payload log


def test_scan_flow_logs_no_mac_at_all(manager: PacketCaptureManager, caplog: pytest.LogCaptureFixture) -> None:
    """No log record from the single-AP scan flow may hold the AP MAC."""
    with caplog.at_level(logging.DEBUG):  # WHY: capture every record the flow emits
        _run_scan_flow(manager)  # WHY: exercise the production code path
    assert AP_MAC not in caplog.text  # WHY: broad guard against a new leak anywhere in this flow


def test_payload_log_keeps_the_field_names(manager: PacketCaptureManager, caplog: pytest.LogCaptureFixture) -> None:
    """The payload log line must keep the field names for the audit trail."""
    with caplog.at_level(logging.DEBUG):  # WHY: the payload log line runs at DEBUG level
        _run_scan_flow(manager)  # WHY: exercise the production code path
    lines = _payload_log_lines(caplog)  # WHY: read back the payload log records
    assert "ap_mac" in lines[0]  # WHY: the field name is a code literal and is safe to log
    assert "channel" in lines[0]  # WHY: prove the summary covers the merged scan parameters


def test_log_safe_payload_fields_drops_every_value() -> None:
    """The helper returns sorted field names and no field value."""
    payload = {"type": "scan", "ap_mac": AP_MAC, "ssid": "corp-wifi", "psk": "s3cret", "channel": 36}
    summary = PacketCaptureManager._log_safe_payload_fields(payload)  # WHY: call the scrub helper directly
    assert summary == "ap_mac, channel, psk, ssid, type"  # WHY: sorted names give a stable log line
    assert AP_MAC not in summary  # WHY: a device identifier must not survive the scrub
    assert "corp-wifi" not in summary  # WHY: an SSID must not survive the scrub
    assert "s3cret" not in summary  # WHY: a credential must not survive the scrub


def test_log_safe_payload_fields_handles_an_empty_payload() -> None:
    """The helper returns an empty string when the payload holds no field."""
    assert PacketCaptureManager._log_safe_payload_fields({}) == ""  # WHY: guard the boundary case
