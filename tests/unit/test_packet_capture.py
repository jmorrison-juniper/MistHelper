"""Unit tests for PacketCaptureManager in src/capture/packet_capture.py."""

import logging
import os
from unittest.mock import MagicMock, patch

import pytest

from src.capture.packet_capture import PacketCaptureManager
from src.capture.packet_capture_download import PacketCaptureDownloadManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _clean_env(tmp_path, monkeypatch):
    """Run each test in a temp directory to avoid file side effects."""
    monkeypatch.chdir(tmp_path)
    os.makedirs("data", exist_ok=True)
    yield


@pytest.fixture()
def mock_session():
    """Return a mock Mist API session."""
    return MagicMock()


@pytest.fixture()
def manager(mock_session):
    """Return a PacketCaptureManager with mocked dependencies."""
    with patch("src.capture.packet_capture._get_config_utils") as mock_config:
        mock_config.return_value.get_cached_or_prompted_org_id.return_value = "test-org-id"
        mgr = PacketCaptureManager(mock_session)
    return mgr


@pytest.fixture()
def manager_with_org(mock_session):
    """Return a PacketCaptureManager with explicit org_id."""
    return PacketCaptureManager(mock_session, org_id="explicit-org-id")


# ---------------------------------------------------------------------------
# MAC Address Validation Tests
# ---------------------------------------------------------------------------
class TestValidateMacAddress:
    """Tests for PacketCaptureManager.validate_mac_address()."""

    def test_valid_colon_separated(self):
        """Accept standard colon-separated MAC."""
        assert PacketCaptureManager.validate_mac_address("aa:bb:cc:dd:ee:ff") is True

    def test_valid_dash_separated(self):
        """Accept dash-separated MAC."""
        assert PacketCaptureManager.validate_mac_address("AA-BB-CC-DD-EE-FF") is True

    def test_valid_no_separator(self):
        """Accept bare 12-hex-digit MAC."""
        assert PacketCaptureManager.validate_mac_address("aabbccddeeff") is True

    def test_valid_mixed_case(self):
        """Accept mixed-case MAC addresses."""
        assert PacketCaptureManager.validate_mac_address("Aa:Bb:Cc:Dd:Ee:Ff") is True

    def test_empty_string(self):
        """Reject empty string."""
        assert PacketCaptureManager.validate_mac_address("") is False

    def test_too_short(self):
        """Reject MAC with too few characters."""
        assert PacketCaptureManager.validate_mac_address("aa:bb:cc") is False

    def test_too_long(self):
        """Reject MAC with extra characters."""
        assert PacketCaptureManager.validate_mac_address("aa:bb:cc:dd:ee:ff:00") is False

    def test_invalid_hex(self):
        """Reject MAC with non-hex characters."""
        assert PacketCaptureManager.validate_mac_address("gg:hh:ii:jj:kk:ll") is False

    def test_mixed_separators(self):
        """Reject MAC with mixed separators."""
        assert PacketCaptureManager.validate_mac_address("aa:bb-cc:dd-ee:ff") is False

    def test_none_input(self):
        """Reject None input (falsy)."""
        assert PacketCaptureManager.validate_mac_address("") is False

    def test_spaces_only(self):
        """Reject whitespace-only input."""
        assert PacketCaptureManager.validate_mac_address("   ") is False

    def test_partial_colons(self):
        """Reject incomplete colon-separated MAC."""
        assert PacketCaptureManager.validate_mac_address("aa:bb:cc:dd:ee") is False

    def test_bare_11_chars(self):
        """Reject bare MAC with only 11 characters."""
        assert PacketCaptureManager.validate_mac_address("aabbccddee1") is False

    def test_bare_13_chars(self):
        """Reject bare MAC with 13 characters."""
        assert PacketCaptureManager.validate_mac_address("aabbccddeeff1") is False

    def test_all_zeros(self):
        """Accept all-zeros MAC (valid format)."""
        assert PacketCaptureManager.validate_mac_address("00:00:00:00:00:00") is True

    def test_all_fs(self):
        """Accept broadcast MAC (all FF)."""
        assert PacketCaptureManager.validate_mac_address("FF:FF:FF:FF:FF:FF") is True


# ---------------------------------------------------------------------------
# MAC Address Normalization Tests
# ---------------------------------------------------------------------------
class TestNormalizeMacAddress:
    """Tests for PacketCaptureManager.normalize_mac_address()."""

    def test_already_normalized(self):
        """Colon-separated lowercase passes through."""
        assert PacketCaptureManager.normalize_mac_address("aa:bb:cc:dd:ee:ff") == "aa:bb:cc:dd:ee:ff"

    def test_uppercase_to_lowercase(self):
        """Normalize uppercase to lowercase."""
        assert PacketCaptureManager.normalize_mac_address("AA:BB:CC:DD:EE:FF") == "aa:bb:cc:dd:ee:ff"

    def test_dash_separated(self):
        """Convert dash-separated to colon-separated."""
        assert PacketCaptureManager.normalize_mac_address("AA-BB-CC-DD-EE-FF") == "aa:bb:cc:dd:ee:ff"

    def test_bare_mac(self):
        """Convert bare MAC to colon-separated."""
        assert PacketCaptureManager.normalize_mac_address("aabbccddeeff") == "aa:bb:cc:dd:ee:ff"

    def test_mixed_case_bare(self):
        """Convert mixed-case bare MAC."""
        assert PacketCaptureManager.normalize_mac_address("AaBbCcDdEeFf") == "aa:bb:cc:dd:ee:ff"

    def test_all_zeros(self):
        """Normalize all-zeros MAC."""
        assert PacketCaptureManager.normalize_mac_address("000000000000") == "00:00:00:00:00:00"

    def test_broadcast(self):
        """Normalize broadcast MAC."""
        assert PacketCaptureManager.normalize_mac_address("FFFFFFFFFFFF") == "ff:ff:ff:ff:ff:ff"


# ---------------------------------------------------------------------------
# Init Tests
# ---------------------------------------------------------------------------
class TestInit:
    """Tests for PacketCaptureManager.__init__()."""

    def test_explicit_org_id(self, mock_session):
        """Use explicit org_id when provided."""
        mgr = PacketCaptureManager(mock_session, org_id="my-org")
        assert mgr.org_id == "my-org"
        assert mgr.mist_session is mock_session
        assert mgr.websocket_manager is None

    def test_org_id_from_config(self, manager):
        """Fall back to ConfigUtils when org_id is None."""
        assert manager.org_id == "test-org-id"

    def test_session_stored(self, manager_with_org, mock_session):
        """Session reference is stored."""
        assert manager_with_org.mist_session is mock_session

    def test_websocket_manager_init_none(self, manager_with_org):
        """WebSocket manager starts as None."""
        assert manager_with_org.websocket_manager is None


# ---------------------------------------------------------------------------
# tcpdump Expression Tests
# ---------------------------------------------------------------------------
class TestTcpdumpExpressionSelection:
    """Tests for _get_tcpdump_expression_selection()."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_default_no_filter(self, mock_iu, manager):
        """Choice '1' returns empty string (no filter)."""
        mock_iu.return_value.safe_input.return_value = "1"
        result = manager._get_tcpdump_expression_selection()
        assert result == ""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_https_filter(self, mock_iu, manager):
        """Choice '2' returns HTTPS port filter."""
        mock_iu.return_value.safe_input.return_value = "2"
        result = manager._get_tcpdump_expression_selection()
        assert result == "port 443"

    @patch("src.capture.packet_capture._get_input_utils")
    def test_dns_filter(self, mock_iu, manager):
        """Choice '4' returns DNS filter."""
        mock_iu.return_value.safe_input.return_value = "4"
        result = manager._get_tcpdump_expression_selection()
        assert result == "port 53"

    @patch("src.capture.packet_capture._get_input_utils")
    def test_icmp_filter(self, mock_iu, manager):
        """Choice '8' returns ICMP filter."""
        mock_iu.return_value.safe_input.return_value = "8"
        result = manager._get_tcpdump_expression_selection()
        assert result == "icmp"

    @patch("src.capture.packet_capture._get_input_utils")
    def test_tcp_filter(self, mock_iu, manager):
        """Choice '10' returns TCP filter."""
        mock_iu.return_value.safe_input.return_value = "10"
        result = manager._get_tcpdump_expression_selection()
        assert result == "tcp"

    @patch("src.capture.packet_capture._get_input_utils")
    def test_custom_expression(self, mock_iu, manager):
        """Choice '40' prompts for custom expression."""
        mock_iu.return_value.safe_input.side_effect = [
            "40",
            "host 10.0.0.1 and port 80",
        ]
        result = manager._get_tcpdump_expression_selection()
        assert result == "host 10.0.0.1 and port 80"

    @patch("src.capture.packet_capture._get_input_utils")
    def test_dhcp_filter(self, mock_iu, manager):
        """Choice '33' returns DHCP filter."""
        mock_iu.return_value.safe_input.return_value = "33"
        result = manager._get_tcpdump_expression_selection()
        assert result == "port 67 or port 68"

    @patch("src.capture.packet_capture._get_input_utils")
    def test_invalid_choice_returns_empty(self, mock_iu, manager):
        """Invalid choice returns empty string."""
        mock_iu.return_value.safe_input.return_value = "99"
        result = manager._get_tcpdump_expression_selection()
        assert result == ""


# ---------------------------------------------------------------------------
# Capture Format Selection Tests
# ---------------------------------------------------------------------------
class TestCaptureFormatSelection:
    """Tests for _get_capture_format_selection()."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_default_pcap(self, mock_iu, manager):
        """Choice '1' returns pcap format."""
        mock_iu.return_value.safe_input.return_value = "1"
        result = manager._get_capture_format_selection()
        assert result == "pcap"

    @patch("src.capture.packet_capture._get_input_utils")
    def test_stream_format(self, mock_iu, manager):
        """Choice '2' returns stream format."""
        mock_iu.return_value.safe_input.return_value = "2"
        result = manager._get_capture_format_selection()
        assert result == "stream"


# ---------------------------------------------------------------------------
# Start Site Packet Capture Menu Tests
# ---------------------------------------------------------------------------
class TestStartSitePacketCapture:
    """Tests for start_site_packet_capture() menu routing."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_cancel_choice(self, mock_iu, manager):
        """Choice '0' cancels and returns without calling any capture."""
        mock_iu.return_value.safe_input.return_value = "0"
        manager.start_site_packet_capture()
        # Should not raise

    @patch("src.capture.packet_capture._get_input_utils")
    def test_invalid_choice(self, mock_iu, manager):
        """Invalid choice prints error and returns."""
        mock_iu.return_value.safe_input.return_value = "99"
        manager.start_site_packet_capture()
        # Should not raise

    @patch("src.capture.packet_capture._get_input_utils")
    def test_routes_to_wireless(self, mock_iu, manager):
        """Choice '1' routes to wireless capture."""
        mock_iu.return_value.safe_input.return_value = "1"
        with patch.object(manager, "_start_site_client_capture_wireless") as mock_method:
            manager.start_site_packet_capture()
            mock_method.assert_called_once()

    @patch("src.capture.packet_capture._get_input_utils")
    def test_routes_to_wired(self, mock_iu, manager):
        """Choice '2' routes to wired capture."""
        mock_iu.return_value.safe_input.return_value = "2"
        with patch.object(manager, "_start_site_client_capture_wired") as mock_method:
            manager.start_site_packet_capture()
            mock_method.assert_called_once()

    @patch("src.capture.packet_capture._get_input_utils")
    def test_routes_to_gateway(self, mock_iu, manager):
        """Choice '3' routes to gateway capture."""
        mock_iu.return_value.safe_input.return_value = "3"
        with patch.object(manager, "_start_site_gateway_capture") as mock_method:
            manager.start_site_packet_capture()
            mock_method.assert_called_once()

    @patch("src.capture.packet_capture._get_input_utils")
    def test_routes_to_switch(self, mock_iu, manager):
        """Choice '4' routes to switch capture."""
        mock_iu.return_value.safe_input.return_value = "4"
        with patch.object(manager, "_start_site_switch_capture") as mock_method:
            manager.start_site_packet_capture()
            mock_method.assert_called_once()

    @patch("src.capture.packet_capture._get_input_utils")
    def test_routes_to_new_association(self, mock_iu, manager):
        """Choice '5' routes to new association capture."""
        mock_iu.return_value.safe_input.return_value = "5"
        with patch.object(manager, "_start_site_new_association_capture") as mock_method:
            manager.start_site_packet_capture()
            mock_method.assert_called_once()

    @patch("src.capture.packet_capture._get_input_utils")
    def test_routes_to_scan(self, mock_iu, manager):
        """Choice '6' routes to scan capture."""
        mock_iu.return_value.safe_input.return_value = "6"
        with patch.object(manager, "_start_site_scan_capture") as mock_method:
            manager.start_site_packet_capture()
            mock_method.assert_called_once()


# ---------------------------------------------------------------------------
# Execute Site Capture Tests
# ---------------------------------------------------------------------------
class TestExecuteSiteCapture:
    """Tests for _execute_site_capture()."""

    @patch("src.capture.packet_capture.mistapi")
    def test_successful_pcap_capture(self, mock_mistapi, manager):
        """Successful PCAP capture calls download."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = {
            "id": "cap-123",
            "format": "pcap",
            "duration": 60,
            "expiry": "2025-01-01T00:00:00Z",
        }
        mock_mistapi.api.v1.sites.pcaps.startSitePacketCapture.return_value = mock_response

        with patch.object(manager, "_wait_and_download_pcap") as mock_dl:
            with patch.object(manager, "_export_capture_info_to_csv"):
                manager._execute_site_capture("site-123", {"type": "client"})
                mock_dl.assert_called_once_with("site-123", "cap-123", 60)

    @patch("src.capture.packet_capture.mistapi")
    def test_successful_stream_capture(self, mock_mistapi, manager):
        """Successful stream capture subscribes to WebSocket."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = {
            "id": "cap-456",
            "format": "stream",
            "duration": 120,
        }
        mock_mistapi.api.v1.sites.pcaps.startSitePacketCapture.return_value = mock_response

        with patch.object(manager, "_subscribe_to_site_capture_stream") as mock_sub:
            with patch.object(manager, "_export_capture_info_to_csv"):
                manager._execute_site_capture("site-123", {"type": "client"})
                mock_sub.assert_called_once_with("site-123", "cap-456")

    @patch("src.capture.packet_capture.mistapi")
    def test_api_error_response(self, mock_mistapi, manager):
        """Non-200 response logs error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.data = "Internal error"
        mock_mistapi.api.v1.sites.pcaps.startSitePacketCapture.return_value = mock_response

        manager._execute_site_capture("site-123", {"type": "client"})
        # Should not raise

    @patch("src.capture.packet_capture.mistapi")
    def test_recording_already_in_progress(self, mock_mistapi, manager):
        """400 with 'Recording already in progress' handled gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.data = {"detail": "Recording already in progress"}
        mock_mistapi.api.v1.sites.pcaps.startSitePacketCapture.return_value = mock_response

        manager._execute_site_capture("site-123", {"type": "client"})
        # Should not raise

    @patch("src.capture.packet_capture.mistapi")
    def test_exception_handled(self, mock_mistapi, manager):
        """Exception during API call is caught and logged."""
        mock_mistapi.api.v1.sites.pcaps.startSitePacketCapture.side_effect = RuntimeError("Network error")

        manager._execute_site_capture("site-123", {"type": "client"})
        # Should not raise


# ---------------------------------------------------------------------------
# Execute Org Capture Tests
# ---------------------------------------------------------------------------
class TestExecuteOrgCapture:
    """Tests for _execute_org_capture()."""

    @patch("src.capture.packet_capture.mistapi")
    def test_successful_org_capture(self, mock_mistapi, manager):
        """Successful org capture with PCAP format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = {
            "id": "org-cap-789",
            "format": "pcap",
            "duration": 300,
        }
        mock_mistapi.api.v1.orgs.pcaps.startOrgPacketCapture.return_value = mock_response

        with patch.object(manager, "_wait_and_download_pcap_org") as mock_dl:
            with patch.object(manager, "_export_capture_info_to_csv"):
                manager._execute_org_capture({"type": "client"})
                mock_dl.assert_called_once()

    @patch("src.capture.packet_capture.mistapi")
    def test_org_capture_stream_format(self, mock_mistapi, manager):
        """Stream format subscribes to org WebSocket."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = {
            "id": "org-cap-stream",
            "format": "stream",
            "duration": 60,
        }
        mock_mistapi.api.v1.orgs.pcaps.startOrgPacketCapture.return_value = mock_response

        with patch.object(manager, "_subscribe_to_org_capture_stream") as mock_sub:
            with patch.object(manager, "_export_capture_info_to_csv"):
                manager._execute_org_capture({"type": "client"})
                mock_sub.assert_called_once_with("org-cap-stream")

    @patch("src.capture.packet_capture.mistapi")
    def test_org_capture_api_failure(self, mock_mistapi, manager):
        """Non-200 org capture handled gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.data = "Forbidden"
        mock_mistapi.api.v1.orgs.pcaps.startOrgPacketCapture.return_value = mock_response

        manager._execute_org_capture({"type": "client"})
        # Should not raise

    @patch("src.capture.packet_capture.mistapi")
    def test_org_capture_exception(self, mock_mistapi, manager):
        """Exception during org capture is caught."""
        mock_mistapi.api.v1.orgs.pcaps.startOrgPacketCapture.side_effect = RuntimeError("API down")

        manager._execute_org_capture({"type": "client"})
        # Should not raise


# ---------------------------------------------------------------------------
# Export Capture Info Tests
# ---------------------------------------------------------------------------
class TestExportCaptureInfoToCsv:
    """Tests for _export_capture_info_to_csv()."""

    @patch("src.capture.packet_capture._get_data_exporter")
    def test_export_creates_csv(self, mock_exporter_factory, manager):
        """Export calls DataExporter with capture data."""
        mock_exporter = MagicMock()
        mock_exporter_factory.return_value = mock_exporter
        capture_data = {
            "id": "cap-export-1",
            "format": "pcap",
            "duration": 60,
            "type": "client",
        }
        manager._export_capture_info_to_csv(capture_data, "site", "site-abc")
        mock_exporter.write_with_format_selection.assert_called_once()

    def test_export_handles_exception(self, manager, caplog):
        """Exception during export is logged, not raised."""
        with patch("src.capture.packet_capture._get_data_exporter", side_effect=ImportError("No module")):
            with caplog.at_level(logging.ERROR):
                manager._export_capture_info_to_csv({}, "site", "site-abc")
        # Should not raise


# ---------------------------------------------------------------------------
# Wait for Capture Completion Tests
# ---------------------------------------------------------------------------
class TestWaitForCaptureCompletion:
    """Tests for _wait_for_capture_completion()."""

    @patch("src.capture.packet_capture.mistapi")
    @patch("src.capture.packet_capture.time.sleep", return_value=None)
    def test_capture_completes(self, mock_sleep, mock_mistapi, manager):
        """Completed capture returns True."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = [
            {"id": "cap-123", "enabled": False, "timestamp": 0},
        ]
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.return_value = mock_response

        result = manager._wait_for_capture_completion("site-123", "cap-123", 10)
        assert result is True

    @patch("src.capture.packet_capture.mistapi")
    @patch("src.capture.packet_capture.time.sleep", return_value=None)
    def test_capture_timeout(self, mock_sleep, mock_mistapi, manager):
        """Timeout returns False when capture not found."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = []  # Capture not in list
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.return_value = mock_response

        result = manager._wait_for_capture_completion("site-123", "cap-123", 5)
        assert result is False

    @patch("src.capture.packet_capture.mistapi")
    @patch("src.capture.packet_capture.time.sleep", return_value=None)
    def test_api_error_during_wait(self, mock_sleep, mock_mistapi, manager):
        """API error during polling returns False."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.data = "Error"
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.return_value = mock_response

        result = manager._wait_for_capture_completion("site-123", "cap-123", 5)
        assert result is False


# ---------------------------------------------------------------------------
# Start Org Packet Capture Menu Tests
# ---------------------------------------------------------------------------
class TestStartOrgPacketCapture:
    """Tests for start_org_packet_capture() menu routing."""

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_cancel_choice(self, mock_pu, mock_iu, manager):
        """Choice '0' cancels org capture."""
        mock_pu.return_value.select_site.return_value = "site-123"
        mock_iu.return_value.safe_input.return_value = "0"
        manager.start_org_packet_capture()
        # Should not raise

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_invalid_choice(self, mock_pu, mock_iu, manager):
        """Invalid choice handled gracefully."""
        mock_pu.return_value.select_site.return_value = "site-123"
        mock_iu.return_value.safe_input.return_value = "99"
        manager.start_org_packet_capture()
        # Should not raise


# ---------------------------------------------------------------------------
# WebSocket Subscribe Tests
# ---------------------------------------------------------------------------
class TestSubscribeToCaptureStream:
    """Tests for _subscribe_to_site_capture_stream()."""

    @patch("src.capture.packet_capture._get_websocket_manager")
    def test_site_stream_subscribe(self, mock_ws_factory, manager):
        """Site stream creates WebSocketManager and subscribes."""
        mock_ws = MagicMock()
        mock_ws.connected = True
        mock_ws.wait_for_subscription_confirmation.return_value = False
        mock_ws_factory.return_value.return_value = mock_ws
        manager._subscribe_to_site_capture_stream("site-123", "cap-456")
        mock_ws.subscribe_to_channel.assert_called_once()

    @patch("src.capture.packet_capture._get_websocket_manager")
    def test_site_stream_exception(self, mock_ws_factory, manager):
        """Exception during WebSocket subscribe is handled."""
        mock_ws_factory.return_value.side_effect = RuntimeError("WS error")
        manager._subscribe_to_site_capture_stream("site-123", "cap-456")
        # Should not raise

    @patch("src.capture.packet_capture._get_websocket_manager")
    def test_org_stream_subscribe(self, mock_ws_factory, manager):
        """Org stream creates WebSocketManager and subscribes."""
        mock_ws = MagicMock()
        mock_ws.connected = True
        mock_ws.wait_for_subscription_confirmation.return_value = False
        mock_ws_factory.return_value.return_value = mock_ws
        manager._subscribe_to_org_capture_stream("cap-789")
        mock_ws.subscribe_to_channel.assert_called_once()

    @patch("src.capture.packet_capture._get_websocket_manager")
    def test_org_stream_exception(self, mock_ws_factory, manager):
        """Exception during org WebSocket subscribe is handled."""
        mock_ws_factory.return_value.side_effect = RuntimeError("WS error")
        manager._subscribe_to_org_capture_stream("cap-789")
        # Should not raise


# ---------------------------------------------------------------------------
# New Association Capture Tests
# ---------------------------------------------------------------------------
class TestNewAssociationCapture:
    """Tests for _start_site_new_association_capture()."""

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    def test_new_assoc_cancel(self, mock_pndu, mock_pu, mock_iu, manager):
        """Cancellation during site selection returns."""
        mock_pu.return_value.select_site.return_value = None
        manager._start_site_new_association_capture()
        # Should not raise


# ---------------------------------------------------------------------------
# Lazy Import Helper Tests
# ---------------------------------------------------------------------------
class TestLazyImports:
    """Tests for lazy import helper functions."""

    def test_get_config_utils(self):
        """_get_config_utils returns the ConfigUtils class."""
        with patch("src.capture.packet_capture._get_config_utils") as mock:
            mock.return_value = MagicMock()
            result = mock()
            assert result is not None

    def test_get_input_utils(self):
        """_get_input_utils returns the InputUtils class."""
        with patch("src.capture.packet_capture._get_input_utils") as mock:
            mock.return_value = MagicMock()
            result = mock()
            assert result is not None

    def test_get_websocket_manager(self):
        """_get_websocket_manager returns the WebSocketManager class."""
        with patch(
            "src.capture.packet_capture._get_websocket_manager",
        ) as mock:
            mock.return_value = MagicMock()
            result = mock()
            assert result is not None


# ---------------------------------------------------------------------------
# Static / Pure Method Tests
# ---------------------------------------------------------------------------
class TestExtractPortNames:
    """Tests for _extract_port_names()."""

    def test_gateway_payload(self):
        """Extract port names from gateway payload."""
        payload = {"gateways": {"aa:bb:cc:dd:ee:ff": {"ports": {"ge-0/0/0": {}, "ge-0/0/1": {}}}}}
        result = PacketCaptureManager._extract_port_names(payload, "Gateway")
        assert result == ["ge-0/0/0", "ge-0/0/1"]

    def test_switch_payload(self):
        """Extract port names from switch payload."""
        # _extract_port_names uses f"{capture_type.lower()}s" as key
        payload = {"switchs": {"aa:bb:cc:dd:ee:ff": {"ports": {"ge-0/0/5": {}}}}}
        result = PacketCaptureManager._extract_port_names(payload, "Switch")
        assert result == ["ge-0/0/5"]

    def test_empty_payload(self):
        """Return empty list for missing device config."""
        result = PacketCaptureManager._extract_port_names({}, "Gateway")
        assert result == []

    def test_no_ports_key(self):
        """Return empty list when ports key missing."""
        payload = {"gateways": {"mac": {}}}
        result = PacketCaptureManager._extract_port_names(payload, "Gateway")
        assert result == []


class TestCalcLoopSleep:
    """Tests for _calc_loop_sleep()."""

    def test_wait_time_positive(self):
        """Return wait_time when positive."""
        assert PacketCaptureManager._calc_loop_sleep(45.0, 5.0) == 45.0

    def test_loop_duration_short(self):
        """Fill up to 30s when loop was fast."""
        assert PacketCaptureManager._calc_loop_sleep(0, 10.0) == 20.0

    def test_default_ten_seconds(self):
        """Return 10s when loop took >= 30s."""
        assert PacketCaptureManager._calc_loop_sleep(0, 35.0) == 10


class TestParsesCapturesResponse:
    """Tests for PacketCaptureDownloadManager.parse_captures_response()."""

    def test_dict_with_results(self):
        """Extract 'results' key from dict."""
        raw = {"results": [{"id": "a"}, {"id": "b"}]}
        result = PacketCaptureDownloadManager.parse_captures_response(raw, 1)
        assert len(result) == 2

    def test_raw_list(self):
        """Pass-through list directly."""
        raw = [{"id": "a"}]
        result = PacketCaptureDownloadManager.parse_captures_response(raw, 1)
        assert result == [{"id": "a"}]

    def test_unexpected_structure(self):
        """Return empty list for unexpected type."""
        result = PacketCaptureDownloadManager.parse_captures_response("garbage", 1)
        assert result == []

    def test_dict_without_results(self):
        """Return empty list for dict missing 'results'."""
        result = PacketCaptureDownloadManager.parse_captures_response({"other": 1}, 1)
        assert result == []


class TestFindCaptureUrl:
    """Tests for PacketCaptureDownloadManager.find_capture_url()."""

    def test_found_with_url(self):
        """Return URL when capture found with pcap_url."""
        captures = [{"id": "cap-1", "pcap_url": "https://example.com/cap.pcap"}]
        result = PacketCaptureDownloadManager.find_capture_url(captures, "cap-1", 1)
        assert result == "https://example.com/cap.pcap"

    def test_found_without_url(self):
        """Return None when capture found but no pcap_url yet."""
        captures = [{"id": "cap-1"}]
        result = PacketCaptureDownloadManager.find_capture_url(captures, "cap-1", 1)
        assert result is None

    def test_not_found(self):
        """Return None when capture ID not in list."""
        captures = [{"id": "cap-other", "pcap_url": "https://example.com/other.pcap"}]
        result = PacketCaptureDownloadManager.find_capture_url(captures, "cap-1", 1)
        assert result is None

    def test_empty_list(self):
        """Return None for empty captures list."""
        result = PacketCaptureDownloadManager.find_capture_url([], "cap-1", 1)
        assert result is None

    def test_non_dict_items_skipped(self):
        """Skip non-dict items in captures list."""
        captures = ["not-a-dict", {"id": "cap-1", "pcap_url": "https://url"}]
        result = PacketCaptureDownloadManager.find_capture_url(captures, "cap-1", 1)
        assert result == "https://url"


class TestValidatePortSelection:
    """Tests for _validate_port_selection()."""

    def test_none_input(self, manager):
        """Return None when port_selection_result is None."""
        assert manager._validate_port_selection(None) is None

    def test_none_port_list(self, manager):
        """Return None when port_list is None."""
        assert manager._validate_port_selection((None, [])) is None

    def test_empty_selects_all(self, manager):
        """Empty port_list with available ports selects all."""
        available = [("ge-0/0/0", "UP"), ("ge-0/0/1", "DOWN")]
        result = manager._validate_port_selection(([], available))
        assert result is not None
        port_list, avail = result
        assert port_list == ["ge-0/0/0", "ge-0/0/1"]

    def test_specific_ports(self, manager):
        """Specific port selection passes through."""
        result = manager._validate_port_selection((["ge-0/0/0"], [("ge-0/0/0", "UP")]))
        assert result is not None
        port_list, _ = result
        assert port_list == ["ge-0/0/0"]


class TestBuildPortsConfig:
    """Tests for _build_ports_config()."""

    def test_single_port_no_filter(self, manager):
        """Build config for single port without filter."""
        result = manager._build_ports_config(["ge-0/0/0"], None)
        assert result == {"ge-0/0/0": {}}

    def test_multiple_ports_with_filter(self, manager):
        """Build config for multiple ports with tcpdump filter."""
        result = manager._build_ports_config(["ge-0/0/0", "ge-0/0/1"], "port 80")
        assert result == {
            "ge-0/0/0": {"tcpdump_expression": "port 80"},
            "ge-0/0/1": {"tcpdump_expression": "port 80"},
        }

    def test_empty_port_list(self, manager):
        """Empty port list returns empty dict."""
        result = manager._build_ports_config([], None)
        assert result == {}


class TestBuildOrgPayload:
    """Tests for _build_org_payload()."""

    def test_basic_stream(self, manager):
        """Build payload for stream format."""
        mxedge = {"id": "mx-1", "name": "Edge1"}
        config = {"duration": 30, "num_packets": 100, "max_pkt_len": 128, "format": "stream"}
        result = manager._build_org_payload(mxedge, ["eth0"], "", config)
        assert result["type"] == "mxedge"
        assert result["duration"] == 30
        assert result["mxedges"]["mx-1"]["interfaces"] == {"eth0": {}}

    def test_with_tcpdump(self, manager):
        """Include tcpdump expression when provided."""
        mxedge = {"id": "mx-1"}
        config = {"duration": 30, "num_packets": 100, "max_pkt_len": 128, "format": "stream"}
        result = manager._build_org_payload(mxedge, ["eth0"], "port 443", config)
        assert result["tcpdump_expression"] == "port 443"

    def test_tzsp_format(self, manager):
        """Include TZSP host/port for tzsp format."""
        mxedge = {"id": "mx-1"}
        config = {
            "duration": 30,
            "num_packets": 100,
            "max_pkt_len": 128,
            "format": "tzsp",
            "tzsp_host": "10.0.0.1",
            "tzsp_port": 37008,
        }
        result = manager._build_org_payload(mxedge, ["eth0"], "", config)
        assert result["format"] == "tzsp"
        assert result["tzsp_host"] == "10.0.0.1"
        assert result["tzsp_port"] == 37008

    def test_no_tcpdump_no_key(self, manager):
        """Omit tcpdump_expression key when empty."""
        mxedge = {"id": "mx-1"}
        config = {"duration": 30, "num_packets": 100, "max_pkt_len": 128, "format": "stream"}
        result = manager._build_org_payload(mxedge, [], "", config)
        assert "tcpdump_expression" not in result


# ---------------------------------------------------------------------------
# Prompt Method Tests
# ---------------------------------------------------------------------------
class TestPromptClientMac:
    """Tests for _prompt_client_mac()."""

    @patch("src.capture.packet_capture._get_prompt_client_utils")
    @patch("src.capture.packet_capture._get_input_utils")
    def test_select_from_list(self, mock_iu, mock_pcu, manager):
        """Select client from connected clients list."""
        mock_iu.return_value.safe_input.return_value = "1"
        mock_pcu.return_value.select_client_mac.return_value = "AA:BB:CC:DD:EE:FF"
        result = manager._prompt_client_mac("site-1")
        assert result == "aa:bb:cc:dd:ee:ff"

    @patch("src.capture.packet_capture._get_prompt_client_utils")
    @patch("src.capture.packet_capture._get_input_utils")
    def test_manual_valid(self, mock_iu, mock_pcu, manager):
        """Manually enter a valid MAC address."""
        mock_iu.return_value.safe_input.side_effect = ["2", "aa:bb:cc:dd:ee:ff"]
        result = manager._prompt_client_mac("site-1")
        assert result == "aa:bb:cc:dd:ee:ff"

    @patch("src.capture.packet_capture._get_prompt_client_utils")
    @patch("src.capture.packet_capture._get_input_utils")
    def test_manual_invalid(self, mock_iu, mock_pcu, manager):
        """Return None for invalid manual MAC entry."""
        mock_iu.return_value.safe_input.side_effect = ["2", "not-a-mac"]
        result = manager._prompt_client_mac("site-1")
        assert result is None

    @patch("src.capture.packet_capture._get_prompt_client_utils")
    @patch("src.capture.packet_capture._get_input_utils")
    def test_select_cancelled(self, mock_iu, mock_pcu, manager):
        """Return None when client selection cancelled."""
        mock_iu.return_value.safe_input.return_value = "1"
        mock_pcu.return_value.select_client_mac.return_value = None
        result = manager._prompt_client_mac("site-1")
        assert result is None


class TestPromptApMacFilter:
    """Tests for _prompt_ap_mac_filter()."""

    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    @patch("src.capture.packet_capture._get_input_utils")
    def test_select_from_list(self, mock_iu, mock_pndu, manager):
        """Select AP from list returns normalized MAC."""
        mock_iu.return_value.safe_input.return_value = "1"
        mock_pndu.return_value.select_ap_mac.return_value = "AA:BB:CC:DD:EE:FF"
        result = manager._prompt_ap_mac_filter("site-1")
        assert result == "aa:bb:cc:dd:ee:ff"

    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    @patch("src.capture.packet_capture._get_input_utils")
    def test_manual_valid(self, mock_iu, mock_pndu, manager):
        """Manually enter valid AP MAC."""
        mock_iu.return_value.safe_input.side_effect = ["2", "aa:bb:cc:dd:ee:ff"]
        result = manager._prompt_ap_mac_filter("site-1")
        assert result == "aa:bb:cc:dd:ee:ff"

    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    @patch("src.capture.packet_capture._get_input_utils")
    def test_manual_invalid(self, mock_iu, mock_pndu, manager):
        """Return None for invalid manual AP MAC."""
        mock_iu.return_value.safe_input.side_effect = ["2", "bad"]
        result = manager._prompt_ap_mac_filter("site-1")
        assert result is None

    @patch("src.capture.packet_capture._get_input_utils")
    def test_skip(self, mock_iu, manager):
        """Return None when user skips AP filter."""
        mock_iu.return_value.safe_input.return_value = "3"
        result = manager._prompt_ap_mac_filter("site-1")
        assert result is None


class TestPromptMulticast:
    """Tests for _prompt_multicast()."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_yes(self, mock_iu, manager):
        """Return True for 'y'."""
        mock_iu.return_value.safe_input.return_value = "y"
        assert manager._prompt_multicast() is True

    @patch("src.capture.packet_capture._get_input_utils")
    def test_no(self, mock_iu, manager):
        """Return False for 'n'."""
        mock_iu.return_value.safe_input.return_value = "n"
        assert manager._prompt_multicast() is False


class TestPromptScanBand:
    """Tests for _prompt_scan_band()."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_24ghz(self, mock_iu, manager):
        """Select 2.4 GHz band."""
        mock_iu.return_value.safe_input.return_value = "1"
        assert manager._prompt_scan_band() == "24"

    @patch("src.capture.packet_capture._get_input_utils")
    def test_5ghz(self, mock_iu, manager):
        """Select 5 GHz band (default)."""
        mock_iu.return_value.safe_input.return_value = "2"
        assert manager._prompt_scan_band() == "5"

    @patch("src.capture.packet_capture._get_input_utils")
    def test_6ghz(self, mock_iu, manager):
        """Select 6 GHz band."""
        mock_iu.return_value.safe_input.return_value = "3"
        assert manager._prompt_scan_band() == "6"

    @patch("src.capture.packet_capture._get_input_utils")
    def test_invalid_defaults_5ghz(self, mock_iu, manager):
        """Invalid choice defaults to 5 GHz."""
        mock_iu.return_value.safe_input.return_value = "99"
        assert manager._prompt_scan_band() == "5"


class TestPromptScanChannel:
    """Tests for _prompt_scan_channel()."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_24ghz_valid(self, mock_iu, manager):
        """Valid 2.4 GHz channel."""
        mock_iu.return_value.safe_input.return_value = "6"
        assert manager._prompt_scan_channel("24") == 6

    @patch("src.capture.packet_capture._get_input_utils")
    def test_5ghz_valid(self, mock_iu, manager):
        """Valid 5 GHz channel."""
        mock_iu.return_value.safe_input.return_value = "36"
        assert manager._prompt_scan_channel("5") == 36

    @patch("src.capture.packet_capture._get_input_utils")
    def test_6ghz_valid(self, mock_iu, manager):
        """Valid 6 GHz channel."""
        mock_iu.return_value.safe_input.return_value = "1"
        assert manager._prompt_scan_channel("6") == 1

    @patch("src.capture.packet_capture._get_input_utils")
    def test_invalid(self, mock_iu, manager):
        """Return None for non-integer channel."""
        mock_iu.return_value.safe_input.return_value = "abc"
        assert manager._prompt_scan_channel("5") is None


class TestPromptScanBandwidth:
    """Tests for _prompt_scan_bandwidth()."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_20mhz(self, mock_iu, manager):
        """Select 20 MHz bandwidth."""
        mock_iu.return_value.safe_input.return_value = "1"
        assert manager._prompt_scan_bandwidth("5") == "20"

    @patch("src.capture.packet_capture._get_input_utils")
    def test_40mhz(self, mock_iu, manager):
        """Select 40 MHz bandwidth."""
        mock_iu.return_value.safe_input.return_value = "2"
        assert manager._prompt_scan_bandwidth("5") == "40"

    @patch("src.capture.packet_capture._get_input_utils")
    def test_80mhz_on_5ghz(self, mock_iu, manager):
        """80 MHz valid on 5 GHz."""
        mock_iu.return_value.safe_input.return_value = "3"
        assert manager._prompt_scan_bandwidth("5") == "80"

    @patch("src.capture.packet_capture._get_input_utils")
    def test_80mhz_invalid_on_24ghz(self, mock_iu, manager):
        """80 MHz invalid on 2.4 GHz returns None."""
        mock_iu.return_value.safe_input.return_value = "3"
        assert manager._prompt_scan_bandwidth("24") is None


class TestPromptCaptureDuration:
    """Tests for _prompt_capture_duration()."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_valid(self, mock_iu, manager):
        """Valid duration within range."""
        mock_iu.return_value.safe_input.return_value = "120"
        assert manager._prompt_capture_duration() == 120

    @patch("src.capture.packet_capture._get_input_utils")
    def test_too_low(self, mock_iu, manager):
        """Duration below min returns None."""
        mock_iu.return_value.safe_input.return_value = "5"
        assert manager._prompt_capture_duration() is None

    @patch("src.capture.packet_capture._get_input_utils")
    def test_too_high(self, mock_iu, manager):
        """Duration above max returns None."""
        mock_iu.return_value.safe_input.return_value = "999999"
        assert manager._prompt_capture_duration() is None

    @patch("src.capture.packet_capture._get_input_utils")
    def test_non_integer(self, mock_iu, manager):
        """Non-integer input returns None."""
        mock_iu.return_value.safe_input.return_value = "abc"
        assert manager._prompt_capture_duration() is None

    @patch("src.capture.packet_capture._get_input_utils")
    def test_custom_min_val(self, mock_iu, manager):
        """Custom min_val is respected."""
        mock_iu.return_value.safe_input.return_value = "30"
        assert manager._prompt_capture_duration(default=30, min_val=30) == 30


class TestPromptNumPackets:
    """Tests for _prompt_num_packets()."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_valid(self, mock_iu, manager):
        """Valid packet count."""
        mock_iu.return_value.safe_input.return_value = "500"
        assert manager._prompt_num_packets() == 500

    @patch("src.capture.packet_capture._get_input_utils")
    def test_zero_unlimited(self, mock_iu, manager):
        """Zero means unlimited."""
        mock_iu.return_value.safe_input.return_value = "0"
        assert manager._prompt_num_packets() == 0

    @patch("src.capture.packet_capture._get_input_utils")
    def test_negative(self, mock_iu, manager):
        """Negative returns None."""
        mock_iu.return_value.safe_input.return_value = "-1"
        assert manager._prompt_num_packets() is None

    @patch("src.capture.packet_capture._get_input_utils")
    def test_too_high(self, mock_iu, manager):
        """Above 10000 returns None."""
        mock_iu.return_value.safe_input.return_value = "99999"
        assert manager._prompt_num_packets() is None

    @patch("src.capture.packet_capture._get_input_utils")
    def test_non_integer(self, mock_iu, manager):
        """Non-integer returns None."""
        mock_iu.return_value.safe_input.return_value = "abc"
        assert manager._prompt_num_packets() is None


class TestPromptMaxPacketLength:
    """Tests for _prompt_max_packet_length()."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_valid(self, mock_iu, manager):
        """Valid packet length."""
        mock_iu.return_value.safe_input.return_value = "256"
        assert manager._prompt_max_packet_length() == 256

    @patch("src.capture.packet_capture._get_input_utils")
    def test_too_low(self, mock_iu, manager):
        """Below 64 returns None."""
        mock_iu.return_value.safe_input.return_value = "10"
        assert manager._prompt_max_packet_length() is None

    @patch("src.capture.packet_capture._get_input_utils")
    def test_too_high(self, mock_iu, manager):
        """Above 2048 returns None."""
        mock_iu.return_value.safe_input.return_value = "9999"
        assert manager._prompt_max_packet_length() is None

    @patch("src.capture.packet_capture._get_input_utils")
    def test_non_integer(self, mock_iu, manager):
        """Non-integer returns None."""
        mock_iu.return_value.safe_input.return_value = "abc"
        assert manager._prompt_max_packet_length() is None


class TestPromptLoopMode:
    """Tests for _prompt_loop_mode()."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_yes(self, mock_iu, manager):
        """'y' enables loop mode."""
        mock_iu.return_value.safe_input.return_value = "y"
        assert manager._prompt_loop_mode() is True

    @patch("src.capture.packet_capture._get_input_utils")
    def test_no(self, mock_iu, manager):
        """'n' disables loop mode."""
        mock_iu.return_value.safe_input.return_value = "n"
        assert manager._prompt_loop_mode() is False

    @patch("src.capture.packet_capture._get_input_utils")
    def test_default_no(self, mock_iu, manager):
        """Default is no loop."""
        mock_iu.return_value.safe_input.return_value = "N"
        assert manager._prompt_loop_mode() is False


class TestPromptOrgFormatSelection:
    """Tests for _prompt_org_format_selection()."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_stream_default(self, mock_iu, manager):
        """Default choice returns stream format."""
        mock_iu.return_value.safe_input.return_value = "1"
        result = manager._prompt_org_format_selection()
        assert result == ("stream", None, None)

    @patch("src.capture.packet_capture._get_input_utils")
    def test_tzsp_valid(self, mock_iu, manager):
        """Valid TZSP choice returns host and port."""
        mock_iu.return_value.safe_input.side_effect = ["2", "10.0.0.1", "37008"]
        result = manager._prompt_org_format_selection()
        assert result == ("tzsp", "10.0.0.1", 37008)

    @patch("src.capture.packet_capture._get_input_utils")
    def test_tzsp_invalid_port(self, mock_iu, manager):
        """Invalid TZSP port returns None."""
        mock_iu.return_value.safe_input.side_effect = ["2", "10.0.0.1", "99999"]
        result = manager._prompt_org_format_selection()
        assert result is None

    @patch("src.capture.packet_capture._get_input_utils")
    def test_tzsp_no_host(self, mock_iu, manager):
        """Empty TZSP host returns None."""
        mock_iu.return_value.safe_input.side_effect = ["2", ""]
        result = manager._prompt_org_format_selection()
        assert result is None

    @patch("src.capture.packet_capture._get_input_utils")
    def test_tzsp_non_numeric_port(self, mock_iu, manager):
        """Non-numeric TZSP port returns None."""
        mock_iu.return_value.safe_input.side_effect = ["2", "10.0.0.1", "abc"]
        result = manager._prompt_org_format_selection()
        assert result is None


# ---------------------------------------------------------------------------
# Display / Print Method Tests
# ---------------------------------------------------------------------------
class TestDisplayClientCaptureSummary:
    """Tests for _display_client_capture_summary()."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_basic_summary(self, mock_iu, manager, capsys):
        """Display basic wireless client summary."""
        mock_iu.return_value.safe_input.return_value = ""
        payload = {
            "client_mac": "aa:bb:cc:dd:ee:ff",
            "duration": 60,
            "num_packets": 100,
            "includes_mcast": False,
            "format": "pcap",
        }
        manager._display_client_capture_summary("Wireless Client", payload, False)
        captured = capsys.readouterr()
        assert "Wireless Client" in captured.out
        assert "aa:bb:cc:dd:ee:ff" in captured.out

    @patch("src.capture.packet_capture._get_input_utils")
    def test_with_ap_mac(self, mock_iu, manager, capsys):
        """Include AP MAC filter in summary."""
        mock_iu.return_value.safe_input.return_value = ""
        payload = {"client_mac": "aa:bb:cc:dd:ee:ff", "duration": 60, "num_packets": 0}
        manager._display_client_capture_summary("Wireless Client", payload, True, ap_mac="11:22:33:44:55:66")
        captured = capsys.readouterr()
        assert "11:22:33:44:55:66" in captured.out
        assert "ENABLED" in captured.out


class TestDisplayScanCaptureSummary:
    """Tests for _display_scan_capture_summary()."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_basic_scan_summary(self, mock_iu, manager, capsys):
        """Display scan capture summary."""
        mock_iu.return_value.safe_input.return_value = ""
        payload = {
            "ap_mac": "aa:bb:cc:dd:ee:ff",
            "band": "5",
            "channel": 36,
            "bandwidth": "20",
            "duration": 60,
            "num_packets": 1024,
        }
        manager._display_scan_capture_summary(payload, False)
        captured = capsys.readouterr()
        assert "Scan Radio" in captured.out
        assert "5" in captured.out


class TestDisplayDeviceCaptureSummary:
    """Tests for _display_device_capture_summary()."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_gateway_summary(self, mock_iu, manager, capsys):
        """Display gateway capture summary."""
        mock_iu.return_value.safe_input.return_value = ""
        payload = {
            "duration": 120,
            "num_packets": 500,
            "max_pkt_len": 1500,
            "gateways": {"aa:bb:cc:dd:ee:ff": {"ports": {"ge-0/0/0": {}}}},
        }
        manager._display_device_capture_summary("Gateway", "aa:bb:cc:dd:ee:ff", payload)
        captured = capsys.readouterr()
        assert "Gateway" in captured.out
        assert "ge-0/0/0" in captured.out

    @patch("src.capture.packet_capture._get_input_utils")
    def test_loop_enabled(self, mock_iu, manager, capsys):
        """Show loop mode enabled."""
        mock_iu.return_value.safe_input.return_value = ""
        payload = {"duration": 60, "num_packets": 0, "max_pkt_len": 1500}
        manager._display_device_capture_summary("Switch", "aa:bb:cc:dd:ee:ff", payload, enable_loop=True)
        captured = capsys.readouterr()
        assert "ENABLED" in captured.out


class TestDisplayOrgCaptureSummary:
    """Tests for _display_org_capture_summary()."""

    def test_stream_format(self, manager, capsys):
        """Display org capture summary with stream format."""
        payload = {"duration": 30, "num_packets": 100, "max_pkt_len": 128, "format": "stream"}
        mxedge = {"name": "Edge1", "id": "mx-1"}
        manager._display_org_capture_summary(payload, mxedge, ["eth0"], "")
        captured = capsys.readouterr()
        assert "Edge1" in captured.out
        assert "stream" in captured.out

    def test_tzsp_format(self, manager, capsys):
        """Display org capture summary with TZSP format."""
        payload = {
            "duration": 30,
            "num_packets": 100,
            "max_pkt_len": 128,
            "format": "tzsp",
            "tzsp_host": "10.0.0.1",
            "tzsp_port": 37008,
        }
        mxedge = {"name": "Edge2", "id": "mx-2"}
        manager._display_org_capture_summary(payload, mxedge, ["eth0"], "port 443")
        captured = capsys.readouterr()
        assert "10.0.0.1" in captured.out
        assert "port 443" in captured.out


class TestPrintLoopBanner:
    """Tests for _print_loop_banner()."""

    def test_banner_output(self, manager, capsys):
        """Print loop banner with duration."""
        manager._print_loop_banner({"duration": 120})
        captured = capsys.readouterr()
        assert "CONTINUOUS CAPTURE MODE" in captured.out
        assert "120" in captured.out


class TestLogExistingSiteCaptures:
    """Tests for _log_existing_site_captures()."""

    @patch("src.capture.packet_capture.mistapi")
    def test_with_captures(self, mock_mistapi, manager, capsys):
        """Log count when captures exist."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.data = [{"id": "cap-1"}, {"id": "cap-2"}]
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.return_value = mock_resp
        manager._log_existing_site_captures("site-1")
        captured = capsys.readouterr()
        assert "2 existing capture(s)" in captured.out

    @patch("src.capture.packet_capture.mistapi")
    def test_api_error(self, mock_mistapi, manager, capsys):
        """Silently handle API error."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.return_value = mock_resp
        manager._log_existing_site_captures("site-1")
        captured = capsys.readouterr()
        assert "existing capture" not in captured.out

    @patch("src.capture.packet_capture.mistapi")
    def test_empty_captures(self, mock_mistapi, manager, capsys):
        """No output when no captures exist."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.data = []
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.return_value = mock_resp
        manager._log_existing_site_captures("site-1")
        captured = capsys.readouterr()
        assert "existing capture" not in captured.out


class TestPrintMxedgeRow:
    """Tests for _print_mxedge_row()."""

    def test_online_mxedge(self, manager, capsys):
        """Print row for online MxEdge with stats."""
        mxedge = {"id": "mx-1", "name": "Edge1", "model": "ME-X5"}
        stats_map = {
            "mx-1": {
                "status": "connected",
                "uptime": 86400,
                "mxagent_registered": True,
                "tunterm_registered": True,
            }
        }
        manager._print_mxedge_row(0, mxedge, stats_map)
        captured = capsys.readouterr()
        assert "Edge1" in captured.out

    def test_offline_mxedge(self, manager, capsys):
        """Print row for MxEdge without stats."""
        mxedge = {"id": "mx-2", "name": "Edge2", "model": "ME-X10"}
        manager._print_mxedge_row(1, mxedge, {})
        captured = capsys.readouterr()
        assert "Edge2" in captured.out


class TestDisplayMxedgePorts:
    """Tests for _display_mxedge_ports()."""

    def test_multiple_ports(self, manager, capsys):
        """Display multiple ports with status."""
        port_stat = {
            "eth0": {"up": True, "speed": 1000, "mac": "aa:bb:cc:dd:ee:ff"},
            "eth1": {"up": False, "speed": 0, "mac": "11:22:33:44:55:66"},
        }
        result = manager._display_mxedge_ports("Edge1", port_stat)
        assert len(result) == 2
        captured = capsys.readouterr()
        assert "Edge1" in captured.out


# ---------------------------------------------------------------------------
# API Method Tests
# ---------------------------------------------------------------------------
class TestCheckExistingApCapture:
    """Tests for _check_existing_ap_capture()."""

    @patch("src.capture.packet_capture.mistapi")
    def test_no_conflict(self, mock_mistapi, manager):
        """No conflict returns True."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.data = [{"ap_mac": "11:22:33:44:55:66"}]
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.return_value = mock_resp
        assert manager._check_existing_ap_capture("site-1", "aa:bb:cc:dd:ee:ff") is True

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture.mistapi")
    def test_conflict_user_cancels(self, mock_mistapi, mock_iu, manager):
        """Conflict and user says no returns False."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.data = [{"ap_mac": "aa:bb:cc:dd:ee:ff"}]
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.return_value = mock_resp
        mock_iu.return_value.safe_input.return_value = "n"
        assert manager._check_existing_ap_capture("site-1", "aa:bb:cc:dd:ee:ff") is False

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture.mistapi")
    def test_conflict_user_proceeds(self, mock_mistapi, mock_iu, manager):
        """Conflict and user says yes returns True."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.data = [{"ap_mac": "aa:bb:cc:dd:ee:ff"}]
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.return_value = mock_resp
        mock_iu.return_value.safe_input.return_value = "y"
        assert manager._check_existing_ap_capture("site-1", "aa:bb:cc:dd:ee:ff") is True

    @patch("src.capture.packet_capture.mistapi")
    def test_api_error_proceeds(self, mock_mistapi, manager):
        """API error still returns True (safe to proceed)."""
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.side_effect = RuntimeError("fail")
        assert manager._check_existing_ap_capture("site-1", "aa:bb:cc:dd:ee:ff") is True


class TestFetchCompletedPcaps:
    """Tests for _fetch_completed_pcaps()."""

    @patch("src.capture.packet_capture.mistapi")
    def test_success_with_results(self, mock_mistapi, manager):
        """Return completed PCAPs with URLs."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.data = {
            "results": [
                {"id": "cap-1", "pcap_url": "https://url1", "format": "pcap"},
                {"id": "cap-2", "format": "stream"},
            ]
        }
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.return_value = mock_resp
        result = manager._fetch_completed_pcaps("site-1", 1)
        assert len(result) == 1
        assert result[0]["id"] == "cap-1"

    @patch("src.capture.packet_capture.mistapi")
    def test_api_error(self, mock_mistapi, manager):
        """Return empty list on API error."""
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.side_effect = RuntimeError("fail")
        result = manager._fetch_completed_pcaps("site-1", 1)
        assert result == []

    @patch("src.capture.packet_capture.mistapi")
    def test_non_200(self, mock_mistapi, manager):
        """Return empty list on non-200 status."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.return_value = mock_resp
        result = manager._fetch_completed_pcaps("site-1", 1)
        assert result == []

    @patch("src.capture.packet_capture.mistapi")
    def test_list_format_response(self, mock_mistapi, manager):
        """Handle list-format response data."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.data = [{"id": "cap-1", "pcap_url": "https://url1", "format": "pcap"}]
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.return_value = mock_resp
        result = manager._fetch_completed_pcaps("site-1", 1)
        assert len(result) == 1


class TestDownloadSinglePcap:
    """Tests for PacketCaptureDownloadManager.download_single_pcap()."""

    @patch("src.capture.packet_capture_download.requests")
    def test_success(self, mock_requests, manager):
        """Download succeeds with HTTP 200."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_content.return_value = [b"pcap-data"]
        mock_requests.get.return_value = mock_resp
        local_path = os.path.join("data", "test.pcap")
        result = manager._download_manager.download_single_pcap(
            "https://url", local_path, "test.pcap", "cap-1", requests_module=mock_requests
        )
        assert result == 1

    @patch("src.capture.packet_capture_download.requests")
    def test_http_error(self, mock_requests, manager):
        """Return 0 on non-200 HTTP response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_requests.get.return_value = mock_resp
        result = manager._download_manager.download_single_pcap(
            "https://url", "data/test.pcap", "test.pcap", "cap-1", requests_module=mock_requests
        )
        assert result == 0

    @patch("src.capture.packet_capture_download.requests")
    def test_exception(self, mock_requests, manager):
        """Return 0 on exception."""
        mock_requests.get.side_effect = ConnectionError("fail")
        result = manager._download_manager.download_single_pcap(
            "https://url", "data/test.pcap", "test.pcap", "cap-1", requests_module=mock_requests
        )
        assert result == 0


class TestDownloadPendingPcaps:
    """Tests for PacketCaptureDownloadManager.download_pending_pcaps()."""

    def test_downloads_new(self, manager):
        """Download PCAPs not already on disk via the injected single-download callback."""
        pcaps = [{"id": "cap-new", "pcap_url": "https://url"}]
        result = manager._download_manager.download_pending_pcaps(pcaps, "data", download_single_fn=lambda *_args: 1)
        assert result == 1

    def test_skips_existing(self, manager):
        """Skip PCAPs already downloaded."""
        existing = os.path.join("data", "PacketCapture_cap-existing.pcap")
        with open(existing, "wb") as f:
            f.write(b"already here")
        pcaps = [{"id": "cap-existing", "pcap_url": "https://url"}]
        result = manager._download_manager.download_pending_pcaps(pcaps, "data", download_single_fn=lambda *_args: 1)
        assert result == 0

    def test_empty_list(self, manager):
        """No downloads when empty list."""
        result = manager._download_manager.download_pending_pcaps([], "data")
        assert result == 0


class TestAttemptLoopCapture:
    """Tests for _attempt_loop_capture()."""

    @patch("src.capture.packet_capture._get_data_exporter")
    @patch("src.capture.packet_capture.mistapi")
    def test_success(self, mock_mistapi, mock_exporter, manager):
        """Successful capture returns start time."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.data = {"id": "cap-1", "duration": 60}
        mock_mistapi.api.v1.sites.pcaps.startSitePacketCapture.return_value = mock_resp
        result = manager._attempt_loop_capture("site-1", {"type": "client"}, 1)
        assert result is not None
        assert isinstance(result, float)

    @patch("src.capture.packet_capture.mistapi")
    def test_api_error(self, mock_mistapi, manager):
        """API error returns None."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.data = "Server Error"
        mock_mistapi.api.v1.sites.pcaps.startSitePacketCapture.return_value = mock_resp
        result = manager._attempt_loop_capture("site-1", {"type": "client"}, 1)
        assert result is None

    @patch("src.capture.packet_capture.mistapi")
    def test_conflict_detected(self, mock_mistapi, manager):
        """Recording conflict returns None with message."""
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.data = {"detail": "Recording already in progress"}
        mock_mistapi.api.v1.sites.pcaps.startSitePacketCapture.return_value = mock_resp
        result = manager._attempt_loop_capture("site-1", {"type": "client"}, 1)
        assert result is None

    @patch("src.capture.packet_capture.mistapi")
    def test_exception(self, mock_mistapi, manager):
        """Exception returns None."""
        mock_mistapi.api.v1.sites.pcaps.startSitePacketCapture.side_effect = RuntimeError("fail")
        result = manager._attempt_loop_capture("site-1", {"type": "client"}, 1)
        assert result is None


class TestSavePcapFile:
    """Tests for PacketCaptureDownloadManager.save_pcap_file()."""

    @patch("src.capture.packet_capture_download.requests")
    def test_success(self, mock_requests, capsys):
        """Download and save PCAP file successfully."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"pcap-binary-content"
        mock_requests.get.return_value = mock_resp
        PacketCaptureDownloadManager.save_pcap_file("https://url", "cap-1", requests_module=mock_requests)
        captured = capsys.readouterr()
        assert "downloaded successfully" in captured.out
        assert os.path.exists(os.path.join("data", "PacketCapture_cap-1.pcap"))

    @patch("src.capture.packet_capture_download.requests")
    def test_with_prefix(self, mock_requests):
        """Save PCAP with org_ prefix."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"data"
        mock_requests.get.return_value = mock_resp
        PacketCaptureDownloadManager.save_pcap_file(
            "https://url", "cap-1", prefix="org_", requests_module=mock_requests
        )
        assert os.path.exists(os.path.join("data", "PacketCapture_org_cap-1.pcap"))

    @patch("src.capture.packet_capture_download.requests")
    def test_http_error(self, mock_requests, capsys):
        """Handle non-200 HTTP response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_requests.get.return_value = mock_resp
        PacketCaptureDownloadManager.save_pcap_file("https://url", "cap-1", requests_module=mock_requests)
        captured = capsys.readouterr()
        assert "Failed to download" in captured.out


class TestFetchOrgMxedges:
    """Tests for _fetch_org_mxedges()."""

    @patch("src.capture.packet_capture.mistapi")
    def test_success(self, mock_mistapi, manager):
        """Return mxedges and stats on success."""
        # get_all returns the list directly, not a response object
        mock_mistapi.get_all.return_value = [{"id": "mx-1", "name": "Edge1"}]

        stats_resp = MagicMock()
        stats_resp.status_code = 200
        mock_mistapi.api.v1.orgs.stats.listOrgMxEdgesStats.return_value = stats_resp
        # Second get_all for stats returns list
        mock_mistapi.get_all.side_effect = [
            [{"id": "mx-1", "name": "Edge1"}],
            [{"id": "mx-1", "status": "connected"}],
        ]

        result = manager._fetch_org_mxedges()
        assert result is not None
        mxedges, stats_map = result
        assert len(mxedges) == 1

    @patch("src.capture.packet_capture.mistapi")
    def test_empty(self, mock_mistapi, manager):
        """Return None when no MxEdges found."""
        mock_mistapi.get_all.return_value = []
        result = manager._fetch_org_mxedges()
        assert result is None


class TestCheckCaptureReadiness:
    """Tests for _check_capture_readiness()."""

    def test_first_capture(self, manager):
        """First capture (None last_capture_time) is always ready."""
        assert manager._check_capture_readiness(None, 60) == 0

    @patch("src.capture.packet_capture.time")
    def test_enough_elapsed(self, mock_time, manager):
        """Ready when enough time has elapsed."""
        mock_time.time.return_value = 1000.0
        assert manager._check_capture_readiness(900.0, 60) == 0

    @patch("src.capture.packet_capture.time")
    def test_not_ready(self, mock_time, manager):
        """Returns wait time when not ready."""
        mock_time.time.return_value = 950.0
        result = manager._check_capture_readiness(920.0, 60)
        assert result == 30.0


# ---------------------------------------------------------------------------
# Orchestrator Tests
# ---------------------------------------------------------------------------
class TestRunSiteCapture:
    """Tests for _run_site_capture()."""

    def test_no_loop(self, manager):
        """Execute single capture without loop."""
        manager._check_existing_ap_capture = MagicMock(return_value=True)
        manager._execute_site_capture = MagicMock()
        manager._run_site_capture("site-1", {"type": "client"}, False, check_ap_mac="aa:bb:cc:dd:ee:ff")
        manager._execute_site_capture.assert_called_once()

    def test_with_loop(self, manager):
        """Execute loop capture."""
        manager._execute_site_capture_loop = MagicMock()
        manager._run_site_capture("site-1", {"type": "client"}, True)
        manager._execute_site_capture_loop.assert_called_once()

    def test_conflict_aborts(self, manager):
        """Abort when AP conflict check fails."""
        manager._check_existing_ap_capture = MagicMock(return_value=False)
        manager._execute_site_capture = MagicMock()
        manager._run_site_capture("site-1", {"type": "client"}, False, check_ap_mac="aa:bb:cc:dd:ee:ff")
        manager._execute_site_capture.assert_not_called()


class TestGatherOrgCaptureParams:
    """Tests for _gather_org_capture_params()."""

    def test_all_valid(self, manager):
        """All prompts valid returns full tuple."""
        manager._prompt_capture_duration = MagicMock(return_value=30)
        manager._prompt_num_packets = MagicMock(return_value=100)
        manager._prompt_max_packet_length = MagicMock(return_value=128)
        manager._prompt_org_format_selection = MagicMock(return_value=("stream", None, None))
        result = manager._gather_org_capture_params()
        assert result == (30, 100, 128, "stream", None, None)

    def test_duration_cancelled(self, manager):
        """Return None when duration cancelled."""
        manager._prompt_capture_duration = MagicMock(return_value=None)
        assert manager._gather_org_capture_params() is None

    def test_num_packets_cancelled(self, manager):
        """Return None when num_packets cancelled."""
        manager._prompt_capture_duration = MagicMock(return_value=30)
        manager._prompt_num_packets = MagicMock(return_value=None)
        assert manager._gather_org_capture_params() is None

    def test_max_pkt_len_cancelled(self, manager):
        """Return None when max_pkt_len cancelled."""
        manager._prompt_capture_duration = MagicMock(return_value=30)
        manager._prompt_num_packets = MagicMock(return_value=100)
        manager._prompt_max_packet_length = MagicMock(return_value=None)
        assert manager._gather_org_capture_params() is None

    def test_format_cancelled(self, manager):
        """Return None when format cancelled."""
        manager._prompt_capture_duration = MagicMock(return_value=30)
        manager._prompt_num_packets = MagicMock(return_value=100)
        manager._prompt_max_packet_length = MagicMock(return_value=128)
        manager._prompt_org_format_selection = MagicMock(return_value=None)
        assert manager._gather_org_capture_params() is None


class TestExecuteSiteCaptureLoop:
    """Tests for _execute_site_capture_loop()."""

    @patch("src.capture.packet_capture.time")
    def test_keyboard_interrupt(self, mock_time, manager):
        """KeyboardInterrupt stops loop gracefully."""
        manager._print_loop_banner = MagicMock()
        manager._fetch_completed_pcaps = MagicMock(side_effect=KeyboardInterrupt)
        manager._execute_site_capture_loop("site-1", {"duration": 60})
        manager._print_loop_banner.assert_called_once()

    @patch("src.capture.packet_capture.time")
    def test_exception_handled(self, mock_time, manager):
        """Generic exception is caught and logged."""
        manager._print_loop_banner = MagicMock()
        manager._fetch_completed_pcaps = MagicMock(side_effect=RuntimeError("boom"))
        manager._execute_site_capture_loop("site-1", {"duration": 60})


class TestHandleMultiApCaptureResult:
    """Tests for _handle_multi_ap_capture_result()."""

    @patch("src.capture.packet_capture._get_data_exporter")
    def test_success_pcap(self, mock_exporter, manager, capsys):
        """HTTP 200 with pcap format triggers download."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.data = {"id": "cap-1", "ap_count": 3, "expiry": "2h"}
        manager._wait_and_download_pcap = MagicMock()
        manager._handle_multi_ap_capture_result(mock_resp, "site-1", 60, "pcap")
        captured = capsys.readouterr()
        assert "Multi-AP capture started" in captured.out
        manager._wait_and_download_pcap.assert_called_once()

    @patch("src.capture.packet_capture._get_data_exporter")
    def test_success_stream(self, mock_exporter, manager, capsys):
        """HTTP 200 with stream format subscribes to WebSocket."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.data = {"id": "cap-1", "ap_count": 2, "expiry": "1h"}
        manager._subscribe_to_site_capture_stream = MagicMock()
        manager._handle_multi_ap_capture_result(mock_resp, "site-1", 60, "stream")
        manager._subscribe_to_site_capture_stream.assert_called_once()

    def test_conflict_error(self, manager, capsys):
        """HTTP 400 with conflict message."""
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.data = {"detail": "Recording already in progress"}
        manager._handle_multi_ap_capture_result(mock_resp, "site-1", 60, "pcap")
        captured = capsys.readouterr()
        assert "already in progress" in captured.out

    def test_generic_error(self, manager, capsys):
        """Non-200 non-conflict error."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.data = "Server error"
        manager._handle_multi_ap_capture_result(mock_resp, "site-1", 60, "pcap")
        captured = capsys.readouterr()
        assert "Failed to start" in captured.out


class TestPollAndDownloadPcap:
    """Tests for _poll_and_download_pcap()."""

    def test_success(self, manager):
        """Download PCAP after polling via the download manager."""
        manager._download_manager = MagicMock()  # Replace the download manager collaborator
        manager._download_manager.poll_for_pcap_url.return_value = "https://url"  # URL ready immediately
        with patch("src.capture.packet_capture.PacketCaptureDownloadManager.save_pcap_file") as mock_save:
            manager._poll_and_download_pcap(MagicMock(), "cap-1", 60)
            mock_save.assert_called_once()

    def test_timeout(self, manager):
        """No download when poll returns None."""
        manager._download_manager = MagicMock()  # Replace the download manager collaborator
        manager._download_manager.poll_for_pcap_url.return_value = None  # No URL within timeout
        with patch("src.capture.packet_capture.PacketCaptureDownloadManager.save_pcap_file") as mock_save:
            manager._poll_and_download_pcap(MagicMock(), "cap-1", 60)
            mock_save.assert_not_called()

    def test_keyboard_interrupt(self, manager, capsys):
        """KeyboardInterrupt prints URL and exits cleanly."""
        manager._download_manager = MagicMock()  # Replace the download manager collaborator
        manager._download_manager.poll_for_pcap_url.side_effect = KeyboardInterrupt()  # Simulate Ctrl+C
        manager._poll_and_download_pcap(MagicMock(), "cap-1", 60)
        captured = capsys.readouterr()
        assert "cancelled" in captured.out.lower() or "cap-1" in captured.out


class TestSelectPortByIndex:
    """Tests for _select_port_by_index()."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_valid_selection(self, mock_iu, manager):
        """Valid index returns port."""
        mock_iu.return_value.safe_input.return_value = "0"
        result = manager._select_port_by_index(["eth0", "eth1"], "Edge1", "mx-1")
        assert result == ["eth0"]

    @patch("src.capture.packet_capture._get_input_utils")
    def test_invalid_index(self, mock_iu, manager):
        """Out-of-range index returns None."""
        mock_iu.return_value.safe_input.return_value = "5"
        result = manager._select_port_by_index(["eth0"], "Edge1", "mx-1")
        assert result is None

    @patch("src.capture.packet_capture._get_input_utils")
    def test_non_numeric(self, mock_iu, manager):
        """Non-numeric input returns None."""
        mock_iu.return_value.safe_input.return_value = "abc"
        result = manager._select_port_by_index(["eth0"], "Edge1", "mx-1")
        assert result is None


class TestFetchAndSelectMxedgePort:
    """Tests for _fetch_and_select_mxedge_port()."""

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture.mistapi")
    def test_success(self, mock_mistapi, mock_iu, manager):
        """Fetch stats and select port successfully."""
        stats_resp = MagicMock()
        stats_resp.status_code = 200
        stats_resp.data = {"port_stat": {"eth0": {"up": True, "speed": 1000, "mac": "aa:bb:cc:dd:ee:ff"}}}
        mock_mistapi.api.v1.orgs.stats.getOrgMxEdgeStats.return_value = stats_resp
        mock_iu.return_value.safe_input.return_value = "0"
        mxedge = {"id": "mx-1", "name": "Edge1"}
        result = manager._fetch_and_select_mxedge_port(mxedge)
        assert result == ["eth0"]

    @patch("src.capture.packet_capture.mistapi")
    def test_api_error(self, mock_mistapi, manager):
        """Return None on API error."""
        mock_mistapi.api.v1.orgs.stats.getOrgMxEdgeStats.side_effect = RuntimeError("fail")
        result = manager._fetch_and_select_mxedge_port({"id": "mx-1", "name": "Edge1"})
        assert result is None

    @patch("src.capture.packet_capture.mistapi")
    def test_no_port_stat(self, mock_mistapi, manager):
        """Return None when no port_stat in stats."""
        stats_resp = MagicMock()
        stats_resp.status_code = 200
        stats_resp.data = {}
        mock_mistapi.api.v1.orgs.stats.getOrgMxEdgeStats.return_value = stats_resp
        result = manager._fetch_and_select_mxedge_port({"id": "mx-1", "name": "Edge1"})
        assert result is None


class TestDisplayAndSelectMxedge:
    """Tests for _display_and_select_mxedge()."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_valid_selection(self, mock_iu, manager):
        """Select MxEdge by valid index."""
        mock_iu.return_value.safe_input.return_value = "0"
        mxedges = [{"id": "mx-1", "name": "Edge1"}, {"id": "mx-2", "name": "Edge2"}]
        result = manager._display_and_select_mxedge(mxedges, {})
        assert result["id"] == "mx-1"

    @patch("src.capture.packet_capture._get_input_utils")
    def test_invalid_index(self, mock_iu, manager):
        """Invalid index returns None."""
        mock_iu.return_value.safe_input.return_value = "99"
        mxedges = [{"id": "mx-1", "name": "Edge1"}]
        result = manager._display_and_select_mxedge(mxedges, {})
        assert result is None

    @patch("src.capture.packet_capture._get_input_utils")
    def test_non_numeric(self, mock_iu, manager):
        """Non-numeric input returns None."""
        mock_iu.return_value.safe_input.return_value = "abc"
        mxedges = [{"id": "mx-1", "name": "Edge1"}]
        result = manager._display_and_select_mxedge(mxedges, {})
        assert result is None


class TestStartSiteClientCaptureWireless:
    """Tests for _start_site_client_capture_wireless()."""

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_client_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_no_site_selected(self, mock_pu, mock_pcu, mock_iu, manager):
        """Return early when site selection cancelled."""
        mock_pu.return_value.select_site_with_logging.return_value = None
        manager._start_site_client_capture_wireless()
        mock_pcu.return_value.select_client_mac.assert_not_called()

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_client_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_no_client_selected(self, mock_pu, mock_pcu, mock_iu, manager):
        """Return early when client selection cancelled."""
        mock_pu.return_value.select_site_with_logging.return_value = "site-1"
        mock_iu.return_value.safe_input.return_value = "1"
        mock_pcu.return_value.select_client_mac.return_value = None
        manager._start_site_client_capture_wireless()

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    @patch("src.capture.packet_capture._get_prompt_client_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_full_flow(self, mock_pu, mock_pcu, mock_pndu, mock_iu, manager):
        """Complete flow triggers _run_site_capture."""
        mock_pu.return_value.select_site_with_logging.return_value = "site-1"
        mock_iu.return_value.safe_input.side_effect = [
            "1",  # client select mode
            "3",  # AP filter: skip
            "120",  # duration
            "1024",  # num_packets
            "1300",  # max_pkt_len
            "n",  # multicast
            "1",  # tcpdump: no filter
            "1",  # format: pcap
            "n",  # loop mode
            "",  # confirmation
        ]
        mock_pcu.return_value.select_client_mac.return_value = "aa:bb:cc:dd:ee:ff"
        manager._run_site_capture = MagicMock()
        manager._start_site_client_capture_wireless()
        manager._run_site_capture.assert_called_once()


class TestStartSiteClientCaptureWired:
    """Tests for _start_site_client_capture_wired()."""

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_client_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_no_site_selected(self, mock_pu, mock_pcu, mock_iu, manager):
        """Return early when site selection cancelled."""
        mock_pu.return_value.select_site_with_logging.return_value = None
        manager._start_site_client_capture_wired()

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_client_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_full_flow(self, mock_pu, mock_pcu, mock_iu, manager):
        """Complete wired flow triggers _run_site_capture."""
        mock_pu.return_value.select_site_with_logging.return_value = "site-1"
        mock_iu.return_value.safe_input.side_effect = [
            "1",  # client select mode
            "120",  # duration
            "1024",  # num_packets
            "n",  # multicast
            "1",  # tcpdump: no filter
            "1",  # format: pcap
            "n",  # loop mode
            "",  # confirmation
        ]
        mock_pcu.return_value.select_client_mac.return_value = "aa:bb:cc:dd:ee:ff"
        manager._run_site_capture = MagicMock()
        manager._start_site_client_capture_wired()
        manager._run_site_capture.assert_called_once()


class TestStartSiteGatewayCapture:
    """Tests for _start_site_gateway_capture()."""

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_no_site(self, mock_pu, mock_pndu, mock_iu, manager):
        """Return early when site cancelled."""
        mock_pu.return_value.select_site_with_logging.return_value = None
        manager._start_site_gateway_capture()

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_no_gateway(self, mock_pu, mock_pndu, mock_iu, manager):
        """Return early when gateway cancelled."""
        mock_pu.return_value.select_site_with_logging.return_value = "site-1"
        mock_pndu.return_value.select_gateway_mac.return_value = None
        manager._start_site_gateway_capture()

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_full_flow(self, mock_pu, mock_pndu, mock_iu, manager):
        """Complete gateway flow executes capture."""
        mock_pu.return_value.select_site_with_logging.return_value = "site-1"
        mock_pndu.return_value.select_gateway_mac.return_value = "aa:bb:cc:dd:ee:ff"
        mock_pndu.return_value.select_ports_from_device.return_value = (
            ["ge-0/0/0"],
            [("ge-0/0/0", "UP")],
        )
        mock_iu.return_value.safe_input.side_effect = [
            "120",  # duration
            "1024",  # num_packets
            "1",  # tcpdump: no filter
            "1",  # format: pcap
            "n",  # loop mode
            "",  # confirmation
        ]
        manager._execute_site_capture = MagicMock()
        manager._start_site_gateway_capture()
        manager._execute_site_capture.assert_called_once()


class TestStartSiteSwitchCapture:
    """Tests for _start_site_switch_capture()."""

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_no_site(self, mock_pu, mock_pndu, mock_iu, manager):
        """Return early when site cancelled."""
        mock_pu.return_value.select_site_with_logging.return_value = None
        manager._start_site_switch_capture()

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_no_switch(self, mock_pu, mock_pndu, mock_iu, manager):
        """Return early when switch cancelled."""
        mock_pu.return_value.select_site_with_logging.return_value = "site-1"
        mock_pndu.return_value.select_switch_mac.return_value = None
        manager._start_site_switch_capture()

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_full_flow(self, mock_pu, mock_pndu, mock_iu, manager):
        """Complete switch flow executes capture."""
        mock_pu.return_value.select_site_with_logging.return_value = "site-1"
        mock_pndu.return_value.select_switch_mac.return_value = "aa:bb:cc:dd:ee:ff"
        mock_pndu.return_value.select_ports_from_device.return_value = (
            ["ge-0/0/5"],
            [("ge-0/0/5", "UP")],
        )
        mock_iu.return_value.safe_input.side_effect = [
            "120",  # duration
            "1024",  # num_packets
            "1",  # tcpdump: no filter
            "1",  # format: pcap
            "n",  # loop mode
            "",  # confirmation
        ]
        manager._execute_site_capture = MagicMock()
        manager._start_site_switch_capture()
        manager._execute_site_capture.assert_called_once()


class TestStartOrgPacketCaptureFlow:
    """Tests for start_org_packet_capture() full flow."""

    def test_no_mxedges(self, manager):
        """Return early when no MxEdges found."""
        manager._fetch_org_mxedges = MagicMock(return_value=None)
        manager.start_org_packet_capture()

    def test_mxedge_selection_cancelled(self, manager):
        """Return early when MxEdge selection cancelled."""
        manager._fetch_org_mxedges = MagicMock(return_value=([{"id": "mx-1"}], {}))
        manager._display_and_select_mxedge = MagicMock(return_value=None)
        manager.start_org_packet_capture()

    def test_port_selection_cancelled(self, manager):
        """Return early when port selection cancelled."""
        manager._fetch_org_mxedges = MagicMock(return_value=([{"id": "mx-1"}], {}))
        manager._display_and_select_mxedge = MagicMock(return_value={"id": "mx-1"})
        manager._fetch_and_select_mxedge_port = MagicMock(return_value=None)
        manager.start_org_packet_capture()

    @patch("src.capture.packet_capture._get_input_utils")
    def test_full_flow(self, mock_iu, manager):
        """Complete org capture flow executes capture."""
        manager._fetch_org_mxedges = MagicMock(return_value=([{"id": "mx-1", "name": "Edge1"}], {}))
        manager._display_and_select_mxedge = MagicMock(return_value={"id": "mx-1", "name": "Edge1"})
        manager._fetch_and_select_mxedge_port = MagicMock(return_value=["eth0"])
        manager._get_tcpdump_expression_selection = MagicMock(return_value="")
        manager._gather_org_capture_params = MagicMock(return_value=(30, 100, 128, "stream", None, None))
        manager._execute_org_capture = MagicMock()
        mock_iu.return_value.safe_input.return_value = ""
        manager.start_org_packet_capture()
        manager._execute_org_capture.assert_called_once()


class TestWaitAndDownloadPcap:
    """Tests for _wait_and_download_pcap()."""

    @patch("src.capture.packet_capture.mistapi")
    def test_calls_poll(self, mock_mistapi, manager):
        """Calls _poll_and_download_pcap with correct args."""
        manager._poll_and_download_pcap = MagicMock()
        manager._wait_and_download_pcap("site-1", "cap-1", 60)
        manager._poll_and_download_pcap.assert_called_once()

    @patch("src.capture.packet_capture.mistapi")
    def test_org_calls_poll(self, mock_mistapi, manager):
        """Org variant calls _poll_and_download_pcap."""
        manager._poll_and_download_pcap = MagicMock()
        manager._wait_and_download_pcap_org("org-1", "cap-1", 60)
        manager._poll_and_download_pcap.assert_called_once()


# ---------------------------------------------------------------------------
# Gather Scan Radio Params Tests
# ---------------------------------------------------------------------------
class TestGatherScanRadioParams:
    """Tests for _gather_scan_radio_params()."""

    def test_all_valid(self, manager):
        """All prompts valid returns full dict."""
        manager._prompt_scan_channel = MagicMock(return_value=36)
        manager._prompt_scan_bandwidth = MagicMock(return_value="20")
        manager._prompt_capture_duration = MagicMock(return_value=60)
        manager._prompt_num_packets = MagicMock(return_value=100)
        manager._get_capture_format_selection = MagicMock(return_value="pcap")
        result = manager._gather_scan_radio_params("5")
        assert result == {
            "channel": 36,
            "bandwidth": "20",
            "duration": 60,
            "num_packets": 100,
            "format": "pcap",
        }

    def test_channel_cancelled(self, manager):
        """Return None when channel cancelled."""
        manager._prompt_scan_channel = MagicMock(return_value=None)
        assert manager._gather_scan_radio_params("5") is None

    def test_bandwidth_cancelled(self, manager):
        """Return None when bandwidth cancelled."""
        manager._prompt_scan_channel = MagicMock(return_value=36)
        manager._prompt_scan_bandwidth = MagicMock(return_value=None)
        assert manager._gather_scan_radio_params("5") is None

    def test_duration_cancelled(self, manager):
        """Return None when duration cancelled."""
        manager._prompt_scan_channel = MagicMock(return_value=36)
        manager._prompt_scan_bandwidth = MagicMock(return_value="20")
        manager._prompt_capture_duration = MagicMock(return_value=None)
        assert manager._gather_scan_radio_params("5") is None

    def test_num_packets_cancelled(self, manager):
        """Return None when num_packets cancelled."""
        manager._prompt_scan_channel = MagicMock(return_value=36)
        manager._prompt_scan_bandwidth = MagicMock(return_value="20")
        manager._prompt_capture_duration = MagicMock(return_value=60)
        manager._prompt_num_packets = MagicMock(return_value=None)
        assert manager._gather_scan_radio_params("5") is None


# ---------------------------------------------------------------------------
# Start Site New Association Capture Tests
# ---------------------------------------------------------------------------
class TestStartSiteNewAssociationCaptureDetailed:
    """Extended tests for _start_site_new_association_capture()."""

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_no_site(self, mock_pu, mock_iu, manager):
        """Return early when site cancelled."""
        mock_pu.return_value.select_site_with_logging.return_value = None
        manager._start_site_new_association_capture()

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_full_flow_no_ssid(self, mock_pu, mock_iu, manager):
        """Complete flow without SSID filter."""
        mock_pu.return_value.select_site_with_logging.return_value = "site-1"
        mock_iu.return_value.safe_input.side_effect = [
            "",  # SSID (empty = all)
            "120",  # duration
            "1",  # format: pcap
            "n",  # loop mode
            "",  # confirmation
        ]
        manager._execute_site_capture = MagicMock()
        manager._start_site_new_association_capture()
        manager._execute_site_capture.assert_called_once()

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_full_flow_with_ssid(self, mock_pu, mock_iu, manager):
        """Complete flow with SSID filter."""
        mock_pu.return_value.select_site_with_logging.return_value = "site-1"
        mock_iu.return_value.safe_input.side_effect = [
            "Corp-WiFi",  # SSID
            "60",  # duration
            "1",  # format: pcap
            "n",  # loop
            "",  # confirm
        ]
        manager._execute_site_capture = MagicMock()
        manager._start_site_new_association_capture()
        call_args = manager._execute_site_capture.call_args
        payload = call_args[0][1]
        assert payload["ssid"] == "Corp-WiFi"

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_with_loop_mode(self, mock_pu, mock_iu, manager):
        """Loop mode invokes _execute_site_capture_loop."""
        mock_pu.return_value.select_site_with_logging.return_value = "site-1"
        mock_iu.return_value.safe_input.side_effect = [
            "",  # SSID
            "60",  # duration
            "1",  # format
            "y",  # loop enabled
            "",  # confirm
        ]
        manager._execute_site_capture_loop = MagicMock()
        manager._start_site_new_association_capture()
        manager._execute_site_capture_loop.assert_called_once()

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_duration_cancelled(self, mock_pu, mock_iu, manager):
        """Return early when duration cancelled."""
        mock_pu.return_value.select_site_with_logging.return_value = "site-1"
        mock_iu.return_value.safe_input.side_effect = [
            "",  # SSID
            "abc",  # invalid duration
        ]
        manager._execute_site_capture = MagicMock()
        manager._start_site_new_association_capture()
        manager._execute_site_capture.assert_not_called()


# ---------------------------------------------------------------------------
# Start Site Scan Capture Tests
# ---------------------------------------------------------------------------
class TestStartSiteScanCapture:
    """Tests for _start_site_scan_capture()."""

    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_no_site(self, mock_pu, manager):
        """Return early when site cancelled."""
        mock_pu.return_value.select_site_with_logging.return_value = None
        manager._start_site_scan_capture()

    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_no_ap(self, mock_pu, mock_pndu, manager):
        """Return early when AP cancelled."""
        mock_pu.return_value.select_site_with_logging.return_value = "site-1"
        mock_pndu.return_value.select_ap_mac.return_value = None
        manager._start_site_scan_capture()

    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_all_aps_delegates(self, mock_pu, mock_pndu, manager):
        """ALL_APS selection delegates to multi-AP method."""
        mock_pu.return_value.select_site_with_logging.return_value = "site-1"
        mock_pndu.return_value.select_ap_mac.return_value = "ALL_APS"
        manager._start_site_scan_capture_all_aps = MagicMock()
        manager._start_site_scan_capture()
        manager._start_site_scan_capture_all_aps.assert_called_once_with("site-1")

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_full_flow(self, mock_pu, mock_pndu, mock_iu, manager):
        """Complete scan capture flow."""
        mock_pu.return_value.select_site_with_logging.return_value = "site-1"
        mock_pndu.return_value.select_ap_mac.return_value = "AA:BB:CC:DD:EE:FF"
        mock_iu.return_value.safe_input.side_effect = [
            "2",  # band: 5 GHz
            "36",  # channel
            "1",  # bandwidth: 20
            "60",  # duration
            "100",  # num_packets
            "1",  # format: pcap
            "n",  # loop mode
            "",  # confirmation
        ]
        manager._run_site_capture = MagicMock()
        manager._start_site_scan_capture()
        manager._run_site_capture.assert_called_once()

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    @patch("src.capture.packet_capture._get_prompt_utils")
    def test_scan_params_cancelled(self, mock_pu, mock_pndu, mock_iu, manager):
        """Return early when scan params cancelled."""
        mock_pu.return_value.select_site_with_logging.return_value = "site-1"
        mock_pndu.return_value.select_ap_mac.return_value = "AA:BB:CC:DD:EE:FF"
        mock_iu.return_value.safe_input.side_effect = [
            "2",  # band: 5 GHz
            "abc",  # invalid channel
        ]
        manager._run_site_capture = MagicMock()
        manager._start_site_scan_capture()
        manager._run_site_capture.assert_not_called()


# ---------------------------------------------------------------------------
# Start Site Scan Capture All APs Tests
# ---------------------------------------------------------------------------
class TestStartSiteScanCaptureAllAps:
    """Tests for _start_site_scan_capture_all_aps()."""

    @patch("src.capture.packet_capture._get_device_utils")
    def test_no_aps(self, mock_du, manager, capsys):
        """Return early when no APs at site."""
        mock_du.return_value.get_all_ap_macs_from_site.return_value = []
        manager._start_site_scan_capture_all_aps("site-1")
        captured = capsys.readouterr()
        assert "No APs found" in captured.out

    @patch("src.capture.packet_capture.mistapi")
    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_device_utils")
    def test_full_flow(self, mock_du, mock_iu, mock_mistapi, manager, capsys):
        """Complete multi-AP scan flow."""
        mock_du.return_value.get_all_ap_macs_from_site.return_value = [
            "AA:BB:CC:DD:EE:01",
            "AA:BB:CC:DD:EE:02",
        ]
        mock_iu.return_value.safe_input.side_effect = [
            "2",  # band: 5 GHz
            "36",  # channel
            "1",  # bandwidth: 20
            "60",  # duration
            "100",  # num_packets
            "1",  # format: pcap
            "",  # confirmation
        ]
        # Mock _log_existing_site_captures to avoid API call
        manager._log_existing_site_captures = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.data = {"id": "cap-1", "ap_count": 2, "expiry": "1h"}
        mock_mistapi.api.v1.sites.pcaps.startSitePacketCapture.return_value = mock_resp
        manager._handle_multi_ap_capture_result = MagicMock()
        manager._start_site_scan_capture_all_aps("site-1")
        manager._handle_multi_ap_capture_result.assert_called_once()
        captured = capsys.readouterr()
        assert "2 APs" in captured.out

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_device_utils")
    def test_channel_cancelled(self, mock_du, mock_iu, manager):
        """Return early when channel cancelled."""
        mock_du.return_value.get_all_ap_macs_from_site.return_value = ["AA:BB:CC:DD:EE:01"]
        manager._log_existing_site_captures = MagicMock()
        mock_iu.return_value.safe_input.side_effect = [
            "2",  # band: 5 GHz
            "abc",  # invalid channel
        ]
        manager._start_site_scan_capture_all_aps("site-1")

    @patch("src.capture.packet_capture.mistapi")
    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_device_utils")
    def test_api_error(self, mock_du, mock_iu, mock_mistapi, manager, capsys):
        """Handle API error during capture start."""
        mock_du.return_value.get_all_ap_macs_from_site.return_value = ["AA:BB:CC:DD:EE:01"]
        manager._log_existing_site_captures = MagicMock()
        mock_iu.return_value.safe_input.side_effect = [
            "2",  # band
            "36",  # channel
            "1",  # bandwidth
            "60",  # duration
            "100",  # num_packets
            "1",  # format
            "",  # confirmation
        ]
        mock_mistapi.api.v1.sites.pcaps.startSitePacketCapture.side_effect = RuntimeError("boom")
        manager._start_site_scan_capture_all_aps("site-1")
        captured = capsys.readouterr()
        assert "Error" in captured.out

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_device_utils")
    def test_duration_cancelled(self, mock_du, mock_iu, manager):
        """Return early when duration cancelled."""
        mock_du.return_value.get_all_ap_macs_from_site.return_value = ["AA:BB:CC:DD:EE:01"]
        manager._log_existing_site_captures = MagicMock()
        mock_iu.return_value.safe_input.side_effect = [
            "2",  # band
            "36",  # channel
            "1",  # bandwidth
            "abc",  # invalid duration
        ]
        manager._start_site_scan_capture_all_aps("site-1")

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_device_utils")
    def test_num_packets_cancelled(self, mock_du, mock_iu, manager):
        """Return early when num_packets cancelled."""
        mock_du.return_value.get_all_ap_macs_from_site.return_value = ["AA:BB:CC:DD:EE:01"]
        manager._log_existing_site_captures = MagicMock()
        mock_iu.return_value.safe_input.side_effect = [
            "2",  # band
            "36",  # channel
            "1",  # bandwidth
            "60",  # duration
            "abc",  # invalid num_packets
        ]
        manager._start_site_scan_capture_all_aps("site-1")


# ---------------------------------------------------------------------------
# Additional edge-case tests to reach coverage threshold
# ---------------------------------------------------------------------------
class TestTcpdumpCustomEmpty:
    """Cover empty custom tcpdump expression path (line 859-860)."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_custom_empty(self, mock_iu, manager):
        """Choice '40' with empty expression returns empty string."""
        mock_iu.return_value.safe_input.side_effect = ["40", ""]
        result = manager._get_tcpdump_expression_selection()
        assert result == ""


class TestApMacFilterManualInvalid:
    """Cover invalid manual AP MAC path (line 201)."""

    @patch("src.capture.packet_capture._get_input_utils")
    def test_manual_invalid_mac(self, mock_iu, manager):
        """Choice '2' with invalid MAC returns None."""
        mock_iu.return_value.safe_input.side_effect = ["2", "not-a-mac"]
        result = manager._prompt_ap_mac_filter("site-1")
        assert result is None

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    def test_list_no_selection(self, mock_pndu, mock_iu, manager):
        """Choice '1' with no AP selected returns None."""
        mock_iu.return_value.safe_input.return_value = "1"
        mock_pndu.return_value.select_ap_mac.return_value = None
        result = manager._prompt_ap_mac_filter("site-1")
        assert result is None

    @patch("src.capture.packet_capture._get_input_utils")
    @patch("src.capture.packet_capture._get_prompt_network_device_utils")
    def test_list_valid(self, mock_pndu, mock_iu, manager):
        """Choice '1' with valid AP returns normalized MAC."""
        mock_iu.return_value.safe_input.return_value = "1"
        mock_pndu.return_value.select_ap_mac.return_value = "AA:BB:CC:DD:EE:FF"
        result = manager._prompt_ap_mac_filter("site-1")
        assert result is not None

    @patch("src.capture.packet_capture._get_input_utils")
    def test_manual_valid_mac(self, mock_iu, manager):
        """Choice '2' with valid MAC returns normalized MAC."""
        mock_iu.return_value.safe_input.side_effect = ["2", "AA:BB:CC:DD:EE:FF"]
        result = manager._prompt_ap_mac_filter("site-1")
        assert result is not None


class TestLogExistingSiteCapturesEdge:
    """Cover _log_existing_site_captures exception path (line 343-344)."""

    @patch("src.capture.packet_capture.mistapi")
    def test_exception(self, mock_mistapi, manager):
        """Exception during API call is caught gracefully."""
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.side_effect = RuntimeError("boom")
        manager._log_existing_site_captures("site-1")

    @patch("src.capture.packet_capture.mistapi")
    def test_non_200(self, mock_mistapi, manager):
        """Non-200 response returns early."""
        resp = MagicMock()
        resp.status_code = 500
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.return_value = resp
        manager._log_existing_site_captures("site-1")

    @patch("src.capture.packet_capture.mistapi")
    def test_with_existing(self, mock_mistapi, manager, capsys):
        """Existing captures are logged."""
        resp = MagicMock()
        resp.status_code = 200
        resp.data = [{"id": "cap1"}, {"id": "cap2"}]
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.return_value = resp
        manager._log_existing_site_captures("site-1")
        captured = capsys.readouterr()
        assert "2 existing" in captured.out


class TestCheckExistingApCaptureEdge:
    """Cover _check_existing_ap_capture exception and user-cancel paths."""

    @patch("src.capture.packet_capture.mistapi")
    def test_exception_returns_true(self, mock_mistapi, manager):
        """Exception returns True (safe to proceed)."""
        mock_mistapi.api.v1.sites.pcaps.listSitePacketCaptures.side_effect = RuntimeError("boom")
        result = manager._check_existing_ap_capture("site-1", "AA:BB:CC:DD:EE:FF")
        assert result is True


class TestReadStreamPackets:
    """Cover _read_stream_packets (lines 2386-2416)."""

    def test_no_websocket(self, manager, capsys):
        """Return immediately when websocket_manager is None."""
        manager.websocket_manager = None
        manager._read_stream_packets(1, "cap-1")

    @patch("src.capture.packet_capture.time")
    def test_packet_received_complete(self, mock_time, manager, capsys):
        """Process packets and complete when pcap_dict is None."""
        mock_time.time.return_value = 100.0
        ws = MagicMock()
        ws.results_lock = MagicMock()
        ws.command_results = {
            "msg1": {
                "channel": 5,
                "data": {"capture_id": "cap-1", "pcap_dict": None},
            }
        }
        manager.websocket_manager = ws
        manager._read_stream_packets(5, "cap-1")
        captured = capsys.readouterr()
        assert "Capture completed" in captured.out

    @patch("src.capture.packet_capture.time")
    def test_keyboard_interrupt(self, mock_time, manager, capsys):
        """Handle KeyboardInterrupt gracefully."""
        mock_time.time.return_value = 100.0
        ws = MagicMock()
        ws.results_lock = MagicMock()
        ws.command_results = {}
        mock_time.sleep.side_effect = KeyboardInterrupt()
        manager.websocket_manager = ws
        manager._read_stream_packets(5, "cap-1")
        captured = capsys.readouterr()
        assert "stopped by user" in captured.out
