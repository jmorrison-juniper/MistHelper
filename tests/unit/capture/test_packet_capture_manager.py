"""Focused unit tests for PacketCaptureManager Phase 9 delegation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.capture.packet_capture import PacketCaptureManager
from src.capture.packet_capture_download import PacketCaptureDownloadManager


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


def test_download_pending_pcaps_uses_download_manager(manager: PacketCaptureManager) -> None:
    """The site capture loop downloads pending PCAPs directly via the download manager."""
    manager._download_manager = MagicMock()  # Replace the download manager collaborator
    manager._download_manager.download_pending_pcaps.return_value = 3  # Three files written
    result = manager._download_manager.download_pending_pcaps([{"id": "cap-1"}], "data")  # Direct call
    assert result == 3  # Returns the helper's download count
    manager._download_manager.download_pending_pcaps.assert_called_once()  # Invoked exactly once


def test_poll_and_download_uses_download_manager_poll_and_save(manager: PacketCaptureManager) -> None:
    """poll_and_download polls via the download manager and saves via its static saver."""
    manager._download_manager = MagicMock()  # Replace the download manager collaborator
    manager._download_manager.poll_for_pcap_url.return_value = "https://example/cap-9.pcap"  # URL ready
    with patch("src.capture.packet_capture.PacketCaptureDownloadManager.save_pcap_file") as mock_save:
        manager._poll_and_download_pcap(lambda: MagicMock(), "cap-9", 60, "org_")  # Drive the flow
    manager._download_manager.poll_for_pcap_url.assert_called_once()  # Polled once via the manager
    mock_save.assert_called_once_with("https://example/cap-9.pcap", "cap-9", "org_")  # Saved with org prefix


def test_parse_and_find_use_download_manager_statics() -> None:
    """Parse/find capture URL logic is owned by the download manager statics."""
    captures = [{"id": "cap-10", "pcap_url": "https://example/cap-10.pcap"}]
    parsed = PacketCaptureDownloadManager.parse_captures_response({"results": captures}, 1)
    url = PacketCaptureDownloadManager.find_capture_url(parsed, "cap-10", 1)
    assert parsed == captures
    assert url == "https://example/cap-10.pcap"
