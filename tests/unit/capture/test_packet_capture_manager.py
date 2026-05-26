"""Focused unit tests for PacketCaptureManager Phase 9 delegation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.capture.packet_capture import PacketCaptureManager


@pytest.fixture()
def manager() -> PacketCaptureManager:
    """Create a PacketCaptureManager with deterministic org-id dependency."""
    with patch("src.capture.packet_capture._get_config_utils") as config_utils:
        config_utils.return_value.get_cached_or_prompted_org_id.return_value = "org-1"
        return PacketCaptureManager(MagicMock(), org_id=None)


def test_fetch_completed_pcaps_delegates_to_download_manager(manager: PacketCaptureManager) -> None:
    """Manager should delegate completed-PCAP fetch work to helper."""
    expected = [{"id": "cap-1", "pcap_url": "https://example/cap-1.pcap", "format": "pcap"}]
    manager._download_manager = MagicMock()
    manager._download_manager.fetch_completed_pcaps.return_value = expected
    result = manager._fetch_completed_pcaps("site-1", 4)
    assert result == expected
    manager._download_manager.fetch_completed_pcaps.assert_called_once()


def test_download_pending_pcaps_delegates_to_download_manager(manager: PacketCaptureManager) -> None:
    """Manager should delegate pending download orchestration to helper."""
    manager._download_manager = MagicMock()
    manager._download_manager.download_pending_pcaps.return_value = 3
    result = manager._download_pending_pcaps([{"id": "cap-1"}], "data")
    assert result == 3
    manager._download_manager.download_pending_pcaps.assert_called_once()


def test_poll_and_download_delegates_to_download_manager(manager: PacketCaptureManager) -> None:
    """Manager should delegate poll/download loop orchestration to helper."""
    manager._download_manager = MagicMock()
    manager._poll_and_download_pcap(lambda: MagicMock(), "cap-9", 60, "org_")
    manager._download_manager.poll_and_download_pcap.assert_called_once()


def test_poll_for_url_delegates_to_download_manager(manager: PacketCaptureManager) -> None:
    """Manager should delegate URL polling to helper and return helper value."""
    manager._download_manager = MagicMock()
    manager._download_manager.poll_for_pcap_url.return_value = "https://example/cap-9.pcap"
    result = manager._poll_for_pcap_url(lambda: MagicMock(), "cap-9", 60)
    assert result == "https://example/cap-9.pcap"


def test_parse_and_find_delegate_to_download_manager() -> None:
    """Static parse/find wrappers should delegate to helper statics."""
    captures = [{"id": "cap-10", "pcap_url": "https://example/cap-10.pcap"}]
    parsed = PacketCaptureManager._parse_captures_response({"results": captures}, 1)
    url = PacketCaptureManager._find_capture_url(parsed, "cap-10", 1)
    assert parsed == captures
    assert url == "https://example/cap-10.pcap"
