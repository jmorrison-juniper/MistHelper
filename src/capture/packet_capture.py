"""Packet capture management for Juniper Mist environments."""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import requests

from src.capture.org_capture_workflow import OrgCaptureWorkflow
from src.capture.packet_capture_download import PacketCaptureDownloadManager
from src.capture.site_capture_loop import SiteCaptureLoopRunner

if TYPE_CHECKING:
    pass

try:
    import mistapi

    MISTAPI_AVAILABLE = True
except ImportError:
    MISTAPI_AVAILABLE = False


def _get_config_utils() -> Any:
    """Lazy import ConfigUtils to avoid circular imports."""
    from MistHelper import ConfigUtils  # pylint: disable=import-outside-toplevel

    return ConfigUtils


def _get_input_utils() -> Any:
    """Lazy import InputUtils to avoid circular imports."""
    from MistHelper import InputUtils  # pylint: disable=import-outside-toplevel

    return InputUtils


def _get_prompt_utils() -> Any:
    """Lazy import PromptUtils to avoid circular imports."""
    from MistHelper import PromptUtils  # pylint: disable=import-outside-toplevel

    return PromptUtils


def _get_prompt_client_utils() -> Any:
    """Lazy import PromptClientUtils to avoid circular imports."""
    from MistHelper import PromptClientUtils  # pylint: disable=import-outside-toplevel

    return PromptClientUtils


def _get_prompt_network_device_utils() -> Any:
    """Lazy import PromptNetworkDeviceUtils to avoid circular imports."""
    from MistHelper import PromptNetworkDeviceUtils  # pylint: disable=import-outside-toplevel

    return PromptNetworkDeviceUtils


def _get_data_exporter() -> Any:
    """Lazy import DataExporter to avoid circular imports."""
    from MistHelper import DataExporter  # pylint: disable=import-outside-toplevel

    return DataExporter


def _get_device_utils() -> Any:
    """Lazy import DeviceUtils to avoid circular imports."""
    from MistHelper import DeviceUtils  # pylint: disable=import-outside-toplevel

    return DeviceUtils


def _get_websocket_manager() -> Any:
    """Lazy import WebSocketManager to avoid circular imports."""
    from MistHelper import WebSocketManager  # pylint: disable=import-outside-toplevel

    return WebSocketManager


class PacketCaptureManager:
    """Comprehensive packet capture management for Juniper Mist environments.

    This class handles both organization-level and site-level packet captures with support
    for multiple capture types:
    - Client captures (wireless/wired)
    - Gateway captures (wired/wireless)
    - Scan captures (wireless radiotap)
    - MxEdge captures (org-level only)

    All captures stream output via WebSocket for real-time monitoring.

    SECURITY:
        - Validates all user inputs (MAC addresses, channels, durations)
        - Enforces API constraints (max duration, packet counts)
        - Requires explicit confirmation for capture initiation
        - Logs all operations with full audit trail

    ARCHITECTURE:
        - Leverages existing WebSocketManager for streaming
        - Follows NASA/JPL defensive programming patterns
        - Class-based design eliminates wrapper functions
    """

    def __init__(self, mist_session: Any, org_id: str | None = None) -> None:
        """Initialize packet capture manager.

        Args:
            mist_session: Active Mist API session
            org_id (str, optional): Organization ID for operations
        """
        self.mist_session = mist_session
        self.org_id = org_id or _get_config_utils().get_cached_or_prompted_org_id()
        self.websocket_manager: Any = None
        self._download_manager = PacketCaptureDownloadManager()
        logging.debug("PacketCaptureManager initialized for org_id: %s", self.org_id)

    @staticmethod
    def validate_mac_address(mac_address: str) -> bool:
        """Validate MAC address format.

        Args:
            mac_address (str): MAC address to validate

        Returns:
            bool: True if valid, False otherwise

        SECURITY: Prevents injection of malformed MAC addresses into API calls
        """
        if not mac_address:
            return False

        # Support common MAC formats: aa:bb:cc:dd:ee:ff, aa-bb-cc-dd-ee-ff, aabbccddeeff
        # Each alternative enforces consistent separator (no mixing : and -)
        mac_pattern = re.compile(
            r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$" r"|^([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}$" r"|^[0-9A-Fa-f]{12}$"
        )
        return bool(mac_pattern.match(mac_address))

    @staticmethod
    def normalize_mac_address(mac_address: str) -> str:
        """Normalize MAC address to colon-separated format.

        Args:
            mac_address (str): MAC address in any common format

        Returns:
            str: Normalized MAC address (aa:bb:cc:dd:ee:ff)
        """
        # Remove all separators
        mac_clean = re.sub(r"[:-]", "", mac_address.lower())
        # Insert colons every 2 characters
        return ":".join(mac_clean[i : i + 2] for i in range(0, 12, 2))

    def _prompt_client_mac(self, site_id: str) -> str | None:
        """Prompt user to select or enter a client MAC address.

        Args:
            site_id: Site UUID for client lookup

        Returns:
            Normalized MAC address string, or None if cancelled/invalid.
        """
        print("\nClient selection:")
        print("  1. Select from connected clients")
        print("  2. Manually enter MAC address")
        choice = _get_input_utils().safe_input("Enter choice (default 1): ", default_value="1", context="client_select")

        if choice == "1":
            client_mac = _get_prompt_client_utils().select_client_mac(site_id)
            if not client_mac:
                print("\n! No client selected")
                return None
        else:
            client_mac = _get_input_utils().safe_input("\nEnter client MAC address: ", context="client_mac")

        if not self.validate_mac_address(client_mac):
            print(f"\n! Invalid MAC address format: {client_mac}")
            return None
        return self.normalize_mac_address(client_mac)

    def _prompt_ap_mac_filter(self, site_id: str) -> str | None:
        """Prompt user to optionally filter by a specific AP MAC address.

        Args:
            site_id: Site UUID for AP lookup

        Returns:
            Normalized AP MAC address, or None if skipped.
        """
        print("\nOptional: Filter by specific AP")
        print("  1. Select AP from list")
        print("  2. Enter MAC manually")
        print("  3. Skip (capture from any AP)")
        choice = _get_input_utils().safe_input("Enter choice (default 3): ", default_value="3", context="ap_filter")

        if choice == "1":
            ap_mac = _get_prompt_network_device_utils().select_ap_mac(site_id)
            if ap_mac:
                return self.normalize_mac_address(ap_mac)
            return None
        if choice == "2":
            ap_mac = _get_input_utils().safe_input("Enter AP MAC address: ", context="ap_mac")
            if not self.validate_mac_address(ap_mac):
                print(f"\n! Invalid AP MAC address format: {ap_mac}")
                return None  # Caller treats None as "skip", not "abort"
            return self.normalize_mac_address(ap_mac)
        return None

    def _prompt_multicast(self) -> bool:
        """Prompt user whether to include multicast traffic.

        Returns:
            True if multicast should be included, False otherwise.
        """
        result: str = _get_input_utils().safe_input(
            "Include multicast traffic? (y/n, default n): ", default_value="n", context="includes_mcast"
        )
        return result.lower() == "y"

    def _prompt_scan_band(self) -> str:
        """Prompt for scan radio band selection.

        Returns:
            Band string ('24', '5', or '6').
        """
        print("\nSelect band:")
        print("  1. 2.4 GHz")
        print("  2. 5 GHz (default)")
        print("  3. 6 GHz")
        choice = _get_input_utils().safe_input("Enter choice [1-3] (default 2): ", default_value="2", context="band")
        band_map = {"1": "24", "2": "5", "3": "6", "24": "24", "5": "5", "6": "6"}
        return band_map.get(choice, "5")

    def _prompt_scan_channel(self, band: str) -> int | None:
        """Prompt for scan radio channel based on band.

        Args:
            band: Band string ('24', '5', or '6').

        Returns:
            Channel number, or None on invalid input.
        """
        if band == "24":
            channel_str = _get_input_utils().safe_input(
                "Enter channel (1-11, default 1): ", default_value="1", context="channel"
            )
        elif band == "5":
            channel_str = _get_input_utils().safe_input(
                "Enter channel (36-144, default 36): ", default_value="36", context="channel"
            )
        else:
            channel_str = _get_input_utils().safe_input(
                "Enter channel (1-233, default 1): ", default_value="1", context="channel"
            )
        try:
            return int(channel_str)
        except ValueError:
            print(f"\n! Invalid channel: {channel_str}")
            return None

    def _prompt_scan_bandwidth(self, band: str) -> str | None:
        """Prompt for scan radio bandwidth based on band.

        Args:
            band: Band string ('24', '5', or '6').

        Returns:
            Bandwidth string ('20', '40', '80', or '160'), or None if invalid.
        """
        print("\nSelect bandwidth:")
        print("  1. 20 MHz")
        print("  2. 40 MHz")
        if band in ["5", "6"]:
            print("  3. 80 MHz")
        if band == "6":
            print("  4. 160 MHz")
        choice = _get_input_utils().safe_input("Enter choice (default 1): ", default_value="1", context="bandwidth")
        bw_map = {"1": "20", "2": "40", "3": "80", "4": "160"}
        bandwidth = bw_map.get(choice, "20")
        if band == "24" and bandwidth not in ("20", "40"):
            print(f"\n! Invalid bandwidth {bandwidth} for 2.4 GHz band")
            logging.error("Invalid bandwidth %s for 2.4 GHz band", bandwidth)
            return None
        return bandwidth

    def _check_existing_ap_capture(self, site_id: str, ap_mac: str) -> bool:
        """Check for existing captures on an AP and warn the user.

        Args:
            site_id: Site UUID.
            ap_mac: AP MAC address to check.

        Returns:
            True if safe to proceed, False if user cancelled.
        """
        print(f"\n> Checking for existing captures on AP {ap_mac}...")
        try:
            response = mistapi.api.v1.sites.pcaps.listSitePacketCaptures(self.mist_session, site_id)
            if response.status_code != 200:
                return True
            existing_captures = response.data or []
            normalized = ap_mac.replace(":", "").replace("-", "").lower()
            ap_has_capture = any(
                cap.get("ap_mac", "").replace(":", "").replace("-", "").lower() == normalized
                for cap in existing_captures
            )
            if not ap_has_capture:
                return True
            print("\n! WARNING: This AP already has a capture in progress")
            print("  Mist only allows one capture per AP at a time")
            proceed = (
                _get_input_utils()
                .safe_input(
                    "\nContinue anyway? (y/n, default n): ",
                    default_value="n",
                    context="capture_conflict_confirmation",
                )
                .lower()
            )
            if proceed != "y":
                print("\n* Capture cancelled by user")
                logging.info("User cancelled due to existing capture on AP")
                return False
        except Exception as error:  # pylint: disable=broad-exception-caught
            logging.warning("Failed to check for existing captures: %s", error)
        return True

    def _log_existing_site_captures(self, site_id: str) -> None:
        """Log any existing captures at a site for informational purposes.

        Args:
            site_id: Site UUID to check.
        """
        try:
            response = mistapi.api.v1.sites.pcaps.listSitePacketCaptures(self.mist_session, site_id)
            if response.status_code != 200:
                return
            existing = response.data or []
            if existing:
                logging.info("Found %s existing capture(s) at site %s", len(existing), site_id)
                print(f"  Note: {len(existing)} existing capture(s) found at this site")
        except Exception as error:  # pylint: disable=broad-exception-caught
            logging.warning("Failed to check existing site captures: %s", error)

    def _handle_multi_ap_capture_result(
        self,
        response: Any,
        site_id: str,
        duration: int,
        capture_format: str,
    ) -> None:
        """Handle API response for multi-AP capture.

        Args:
            response: API response object.
            site_id: Site UUID.
            duration: Capture duration in seconds.
            capture_format: Capture format ('pcap' or 'stream').
        """
        if response.status_code == 200:
            result = response.data
            capture_id = result.get("id", "unknown")
            ap_count = result.get("ap_count", 0)
            print("\n* Multi-AP capture started successfully!")
            print(f"  Capture ID: {capture_id}")
            print(f"  AP Count: {ap_count}")
            print(f"  Format: {capture_format}")
            print(f"  Duration: {duration} seconds")
            print(f"  Expires: {result.get('expiry', 'unknown')}")
            logging.info("Multi-AP capture started: id=%s, aps=%s", capture_id, ap_count)
            self._export_capture_info_to_csv(result, "site", site_id)
            if capture_format == "pcap":
                print("\n> Waiting for PCAP file to be ready...")
                self._wait_and_download_pcap(site_id, capture_id, duration)
            elif capture_format == "stream":
                print("\n> Stream format - subscribe to WebSocket")
                self._subscribe_to_site_capture_stream(site_id, capture_id)
            return

        error_details = response.data if hasattr(response, "data") else "Unknown"
        if response.status_code == 400 and isinstance(error_details, dict):
            detail = error_details.get("detail", "")
            if "Recording already in progress" in detail:
                print("\n! Capture(s) already in progress on one or more APs")
                print("  Wait for existing captures to complete")
                logging.error("Multi-AP capture conflict: %s", detail)
                return
        print(f"\n! Failed to start capture: {response.status_code}")
        print(f"  Error details: {error_details}")
        logging.error("Multi-AP capture failed: %s", response.status_code)

    def _display_client_capture_summary(
        self,
        capture_type: str,
        payload: dict[str, Any],
        enable_loop: bool,
        ap_mac: str | None = None,
    ) -> None:
        """Display capture summary and prompt for confirmation.

        Args:
            capture_type: Human-readable capture type name.
            payload: Capture configuration payload.
            enable_loop: Whether loop mode is enabled.
            ap_mac: Optional AP MAC filter (wireless only).
        """
        tcpdump_expr = payload.get("tcpdump_expression")
        num_packets = payload.get("num_packets", 0)
        includes_mcast = payload.get("includes_mcast", False)
        max_pkt_len = payload.get("max_pkt_len")

        print("\n" + "=" * 80)
        print(" CAPTURE CONFIGURATION SUMMARY")
        print("=" * 80)
        print(f"  Capture Type: {capture_type}")
        print(f"  Client MAC: {payload.get('client_mac', 'N/A')}")
        if ap_mac:
            print(f"  AP MAC Filter: {ap_mac}")
        if tcpdump_expr:
            print(f"  Packet Filter: {tcpdump_expr}")
        else:
            print("  Packet Filter: None (all traffic)")
        print(f"  Duration: {payload.get('duration', 0)} seconds")
        packets_label = "unlimited" if num_packets == 0 else "max"
        print(f"  Packets: {num_packets} ({packets_label})")
        if max_pkt_len is not None:
            print(f"  Max Packet Length: {max_pkt_len} bytes")
        mcast_label = "Yes" if includes_mcast else "No"
        print(f"  Include Multicast: {mcast_label}")
        if payload.get("format"):
            print(f"  Format: {payload['format']}")
        loop_label = "ENABLED (continuous until Ctrl+C)" if enable_loop else "Disabled (single capture)"
        print(f"  Loop Mode: {loop_label}")
        print("=" * 80)

        _get_input_utils().safe_input(
            "\nPress Enter to start capture (Ctrl+C to cancel): ",
            context="confirmation",
            allow_empty=True,
        )

    def _display_scan_capture_summary(
        self,
        payload: dict[str, Any],
        enable_loop: bool,
    ) -> None:
        """Display scan radio capture summary and prompt for confirmation.

        Args:
            payload: Capture configuration payload.
            enable_loop: Whether loop mode is enabled.
        """
        print("\n" + "=" * 80)
        print(" CAPTURE CONFIGURATION SUMMARY")
        print("=" * 80)
        print("  Capture Type: Scan Radio")
        print(f"  AP MAC: {payload.get('ap_mac', 'N/A')}")
        print(f"  Band: {payload.get('band', 'N/A')} GHz")
        print(f"  Channel: {payload.get('channel', 'N/A')}")
        print(f"  Bandwidth: {payload.get('bandwidth', 'N/A')} MHz")
        print(f"  Duration: {payload.get('duration', 0)} seconds")
        print(f"  Packets: {payload.get('num_packets', 0)}")
        loop_label = "ENABLED (continuous until Ctrl+C)" if enable_loop else "Disabled (single capture)"
        print(f"  Loop Mode: {loop_label}")
        print("=" * 80)

        _get_input_utils().safe_input(
            "\nPress Enter to start capture (Ctrl+C to cancel): ",
            context="confirmation",
            allow_empty=True,
        )

    @staticmethod
    def _extract_port_names(payload: dict[str, Any], capture_type: str) -> list[str]:
        """Extract port names from a device capture payload.

        Args:
            payload: Capture payload dict.
            capture_type: 'Gateway' or 'Switch'.

        Returns:
            List of port name strings.
        """
        config_key = f"{capture_type.lower()}s"
        device_config = payload.get(config_key, {})
        for mac_config in device_config.values():
            ports = mac_config.get("ports", {})
            return list(ports.keys())
        return []

    def _display_device_capture_summary(
        self,
        capture_type: str,
        device_mac: str,
        payload: dict[str, Any],
        enable_loop: bool = False,
    ) -> None:
        """Display device (gateway/switch) capture summary and confirm.

        Args:
            capture_type: Human-readable type (e.g. 'Gateway', 'Switch').
            device_mac: Device MAC address.
            payload: Capture configuration payload.
            enable_loop: Whether loop mode is enabled.
        """
        tcpdump_expr = payload.get("tcpdump_expression", "")
        # Extract port names from device-type-specific config
        port_names = self._extract_port_names(payload, capture_type)
        print("\n" + "=" * 80)
        print(" CAPTURE CONFIGURATION SUMMARY")
        print("=" * 80)
        print(f"  Capture Type: {capture_type}")
        print(f"  {capture_type} MAC: {device_mac}")
        ports_label = ", ".join(port_names) if port_names else "All ports"
        print(f"  Ports: {ports_label}")
        print(f"  Duration: {payload.get('duration', 0)} seconds")
        print(f"  Packets: {payload.get('num_packets', 0)}")
        print(f"  Max Packet Length: {payload.get('max_pkt_len', 0)} bytes")
        if tcpdump_expr:
            print(f"  Filter: {tcpdump_expr}")
        loop_label = "ENABLED (continuous until Ctrl+C)" if enable_loop else "Disabled (single capture)"
        print(f"  Loop Mode: {loop_label}")
        print("=" * 80)

        _get_input_utils().safe_input(
            "\nPress Enter to start capture (Ctrl+C to cancel): ",
            context="confirmation",
            allow_empty=True,
        )

    def _run_site_capture(
        self,
        site_id: str,
        payload: dict[str, Any],
        enable_loop: bool,
        check_ap_mac: str | None = None,
    ) -> None:
        """Execute site capture with optional AP conflict check.

        Args:
            site_id: Site UUID.
            payload: Capture configuration payload.
            enable_loop: Whether to run in loop mode.
            check_ap_mac: If set, check for existing captures on this AP first.
        """
        if check_ap_mac and not self._check_existing_ap_capture(site_id, check_ap_mac):
            return
        if enable_loop:
            self._execute_site_capture_loop(site_id, payload)
        else:
            self._execute_site_capture(site_id, payload)

    def _validate_port_selection(self, port_selection_result: Any) -> tuple[list[str], list[Any]] | None:
        """Validate and expand port selection from device.

        Args:
            port_selection_result: Result from select_ports_from_device().

        Returns:
            Tuple of (port_list, available_ports), or None if invalid.
        """
        if port_selection_result is None:
            logging.warning("Port selection failed or cancelled")
            return None
        port_list, available_ports = port_selection_result
        if port_list is None:
            logging.warning("Port selection failed or cancelled")
            return None
        if not port_list and available_ports:
            port_list = [name for name, _ in available_ports]
            logging.debug("All ports selected: %s", port_list)
        else:
            logging.debug("Specific ports selected: %s", port_list)
        return port_list, available_ports

    def _build_ports_config(self, port_list: list[str], tcpdump_expr: str | None) -> dict[str, Any]:
        """Build ports configuration dict for device capture payload.

        Args:
            port_list: List of port names.
            tcpdump_expr: Optional tcpdump filter expression.

        Returns:
            Ports configuration dictionary.
        """
        ports_config: dict[str, Any] = {}
        for port in port_list:
            ports_config[port] = {}
            if tcpdump_expr:
                ports_config[port]["tcpdump_expression"] = tcpdump_expr
        return ports_config

    def _prompt_capture_duration(self, default: int = 60, min_val: int = 60, max_val: int = 86400) -> int | None:
        """Prompt for capture duration and validate range.

        Args:
            default: Default duration in seconds.
            min_val: Minimum allowed duration.
            max_val: Maximum allowed duration.

        Returns:
            Validated duration in seconds, or None on invalid input.
        """
        duration_str = _get_input_utils().safe_input(
            f"Enter capture duration in seconds (default {default}, max {max_val}): ",
            default_value=str(default),
            context="duration",
        )
        try:
            duration = int(duration_str)
        except ValueError:
            print(f"\n! Invalid duration: {duration_str}")
            return None
        if duration < min_val or duration > max_val:
            print(f"\n! Duration must be between {min_val} and {max_val} seconds")
            if min_val >= 60:
                print("  (Mist API requires minimum 60 seconds for all packet captures)")
            return None
        return duration

    def _prompt_num_packets(self, default: int = 1024) -> int | None:
        """Prompt for number of packets and validate range.

        Args:
            default: Default number of packets.

        Returns:
            Validated packet count, or None on invalid input.
        """
        num_packets_str = _get_input_utils().safe_input(
            f"Enter number of packets (default {default}, max 10000, 0 for unlimited): ",
            default_value=str(default),
            context="num_packets",
        )
        try:
            num_packets = int(num_packets_str)
        except ValueError:
            print(f"\n! Invalid number of packets: {num_packets_str}")
            return None
        if num_packets < 0 or num_packets > 10000:
            print("\n! Number of packets must be between 0 and 10000")
            return None
        return num_packets

    def _prompt_max_packet_length(self, default: int = 128) -> int | None:
        """Prompt for max packet length and validate range.

        Args:
            default: Default max packet length in bytes.

        Returns:
            Validated max packet length, or None on invalid input.
        """
        max_pkt_len_str = _get_input_utils().safe_input(
            f"Enter max packet length in bytes (default {default}, max 2048): ",
            default_value=str(default),
            context="max_pkt_len",
        )
        try:
            max_pkt_len = int(max_pkt_len_str)
        except ValueError:
            print(f"\n! Invalid max packet length: {max_pkt_len_str}")
            return None
        if max_pkt_len < 64 or max_pkt_len > 2048:
            print("\n! Max packet length must be between 64 and 2048 bytes")
            return None
        return max_pkt_len

    def _prompt_loop_mode(self) -> bool:
        """Prompt user for continuous loop mode.

        Returns:
            True if loop mode enabled, False otherwise.
        """
        print("\nLoop Mode:")
        print("  Automatically start a new capture when the current one completes")
        print("  Downloads happen in background while next capture runs")
        loop_mode: str = _get_input_utils().safe_input(
            "Enable continuous loop mode? (y/n, default n): ", default_value="n", context="loop_mode"
        )
        return loop_mode.lower() == "y"

    @staticmethod
    def _print_tcpdump_menu() -> None:
        """Print the tcpdump filter selection menu."""
        sections = [
            (
                "BASIC FILTERS",
                [
                    "1.  All traffic (no filter)",
                    "2.  HTTPS only (port 443)",
                    "3.  HTTP/HTTPS (port 80 or 443)",
                    "4.  DNS (port 53)",
                    "5.  SSH (port 22)",
                    "6.  FTP (port 21)",
                    "7.  SMTP Email (port 25)",
                    "8.  ICMP/ping",
                    "9.  ARP",
                ],
            ),
            (
                "PROTOCOL FILTERS",
                [
                    "10. TCP only",
                    "11. UDP only",
                    "12. Not ICMP (exclude ping)",
                ],
            ),
            (
                "DIRECTION FILTERS",
                [
                    "13. Outbound to port 443",
                    "14. Inbound from port 80",
                ],
            ),
            (
                "COMBINED FILTERS",
                [
                    "15. HTTP or HTTPS or DNS (port 80 or 443 or 53)",
                    "16. All except SSH (not port 22)",
                    "17. TCP SYN packets (connection attempts)",
                    "18. TCP SYN-ACK packets (connection replies)",
                    "19. TCP RST packets (connection resets)",
                    "20. TCP FIN packets (connection close)",
                ],
            ),
            (
                "ADVANCED FILTERS",
                [
                    "21. Non-standard ports (>1024)",
                    "22. All except ARP and DNS",
                    "23. TCP traffic on non-standard ports",
                    "24. Broadcast traffic",
                    "25. Multicast traffic",
                    "26. IPv6 only",
                    "27. VLAN tagged traffic",
                ],
            ),
            (
                "APPLICATION PROTOCOLS",
                [
                    "28. SMB/CIFS file sharing (port 445)",
                    "29. RDP Remote Desktop (port 3389)",
                    "30. NTP time sync (port 123)",
                    "31. SNMP monitoring (port 161)",
                    "32. Syslog (port 514)",
                    "33. DHCP (port 67 or 68)",
                    "34. LDAP directory (port 389)",
                    "35. MySQL database (port 3306)",
                ],
            ),
            (
                "SECURITY & TROUBLESHOOTING",
                [
                    "36. Port scans (SYN without ACK)",
                    "37. Fragmented packets",
                    "38. Large packets (>1500 bytes)",
                    "39. Retransmissions (duplicate SEQ)",
                    "40. Custom expression",
                ],
            ),
        ]
        separator = "=" * 80
        print(f"\n{separator}")
        print(" PACKET FILTER SELECTION (tcpdump expression)")
        print(separator)
        for header, items in sections:
            print(f"\n--- {header} ---")
            for item in items:
                print(f"  {item}")
        print(separator)

    @staticmethod
    def _get_tcpdump_expressions() -> dict[str, str]:
        """Return mapping of menu choice to tcpdump expression."""
        return {
            # Basic filters
            "1": "",  # No filter
            "2": "port 443",
            "3": "port 80 or port 443",
            "4": "port 53",
            "5": "port 22",
            "6": "port 21",
            "7": "port 25",
            "8": "icmp",
            "9": "arp",
            # Protocol filters
            "10": "tcp",
            "11": "udp",
            "12": "not icmp",
            # Direction filters
            "13": "dst port 443",
            "14": "src port 80",
            # Combined filters
            "15": "port 80 or port 443 or port 53",
            "16": "not port 22",
            "17": "tcp[tcpflags] & tcp-syn != 0",
            "18": "tcp[tcpflags] = 0x12",
            "19": "tcp[tcpflags] & tcp-rst != 0",
            "20": "tcp[tcpflags] & tcp-fin != 0",
            # Advanced filters
            "21": "tcp[0:2] > 1024 or udp[0:2] > 1024",
            "22": "not arp and not port 53",
            "23": "tcp and port > 1024",
            "24": "ether broadcast",
            "25": "ether multicast",
            "26": "ip6",
            "27": "vlan",
            # Application protocols
            "28": "port 445",
            "29": "port 3389",
            "30": "port 123",
            "31": "port 161",
            "32": "port 514",
            "33": "port 67 or port 68",
            "34": "port 389",
            "35": "port 3306",
            # Security & troubleshooting
            "36": "tcp[tcpflags] & (tcp-syn) != 0 and tcp[tcpflags] & (tcp-ack) = 0",
            "37": "ip[6:2] & 0x1fff != 0",
            "38": "greater 1500",
            "39": ("tcp[tcpflags] & " "(tcp-syn|tcp-fin|tcp-rst|tcp-push|tcp-ack|tcp-urg) = 0"),
        }

    def _get_tcpdump_expression_selection(self) -> str:
        """Prompt user for tcpdump expression with comprehensive examples.

        Based on Daniel Miessler's tcpdump tutorial (danielmiessler.com/blog/tcpdump)

        Returns:
            str: tcpdump expression or empty string to skip
        """
        self._print_tcpdump_menu()

        choice = _get_input_utils().safe_input(
            "\nEnter choice (default 1 - all traffic): ",
            default_value="1",
            context="tcpdump_filter",
        )

        expressions = self._get_tcpdump_expressions()

        if choice in expressions:
            expr = expressions[choice]
            if expr:
                print(f"\n! Filter applied: {expr}")
            else:
                print("\n! Filter: None (capturing all traffic)")
            return expr

        if choice == "40":
            print("\nEnter custom tcpdump expression:")
            print("  Examples: 'host 192.168.1.1', 'net 10.0.0.0/8', 'port 8080'")
            custom_expr = _get_input_utils().safe_input("Expression: ", context="tcpdump_custom", allow_empty=True)
            if custom_expr:
                print(f"\n! Filter applied: {custom_expr}")
                return str(custom_expr)
            print("\n! No filter applied")
            return ""

        print("\n! Invalid choice, using no filter")
        return ""

    def _get_capture_format_selection(self) -> str:
        """Prompt user for capture format selection.

        NOTE: API documentation shows switches/gateways only support "stream" format,
        but testing confirms "pcap" format works and generates downloadable files.
        We offer both options and let the API reject if unsupported.

        Returns:
            str: Selected format - 'pcap' or 'stream'
        """
        print("\nCapture format:")
        print("  1. PCAP file - downloadable (default, recommended)")
        print("  2. Stream to Mist Cloud (WebSocket real-time)")
        format_choice = _get_input_utils().safe_input("Enter choice (default 1): ", default_value="1", context="format")
        return "pcap" if format_choice == "1" else "stream"

    def start_site_packet_capture(self) -> None:
        """Interactive menu for starting site-level packet captures.

        Presents user with capture type options and guides through configuration.
        """
        logging.info("Menu #9: Starting site packet capture manager")
        logging.debug("ENTRY: PacketCaptureManager.start_site_packet_capture()")

        print("\n" + "=" * 80)
        print(" SITE PACKET CAPTURE MANAGER")
        print("=" * 80)
        print("\nSelect capture type:")
        print("  1. Client Capture (Wireless) - Captures ongoing traffic from connected clients")
        print("  2. Client Capture (Wired) - Captures wired client traffic")
        print("  3. Gateway Capture - Captures WAN/LAN gateway port traffic")
        print("  4. Switch Capture - Captures switch port traffic")
        print("  5. New Association Capture - Captures NEW connection attempts (auth/assoc handshakes)")
        print("  6. Scan Radio Capture - Captures raw 802.11 frames on specific channel")
        print("  0. Cancel")
        print("=" * 80)

        choice = _get_input_utils().safe_input("\nEnter your choice: ", context="site_capture_menu")

        if choice == "1":
            self._start_site_client_capture_wireless()
        elif choice == "2":
            self._start_site_client_capture_wired()
        elif choice == "3":
            self._start_site_gateway_capture()
        elif choice == "4":
            self._start_site_switch_capture()
        elif choice == "5":
            self._start_site_new_association_capture()
        elif choice == "6":
            self._start_site_scan_capture()
        elif choice == "0":
            print("\n! Cancelled by user")
            return
        else:
            print("\n! Invalid choice")
            return

    def _start_site_client_capture_wireless(self) -> None:  # noqa: C901, PLR0912, PLR0915
        """Start wireless client packet capture at site level."""
        logging.info("Starting site wireless client capture")

        # Get site selection
        site_id = _get_prompt_utils().select_site_with_logging()
        if not site_id:
            return

        # Get capture parameters
        print("\n" + "-" * 80)
        print(" WIRELESS CLIENT CAPTURE CONFIGURATION")
        print("-" * 80)
        print("\nThis capture type monitors ongoing traffic from ALREADY CONNECTED wireless clients.")
        print("Note: To capture new connection attempts (auth/assoc handshakes), use New Association Capture instead.")

        # Client MAC selection
        client_mac = self._prompt_client_mac(site_id)
        if not client_mac:
            return

        # Optional AP MAC filter
        ap_mac = self._prompt_ap_mac_filter(site_id)

        # Duration (Mist API enforces minimum 60 seconds for all captures)
        duration = self._prompt_capture_duration()
        if duration is None:
            return

        # Number of packets
        num_packets = self._prompt_num_packets()
        if num_packets is None:
            return

        # Max packet length
        max_pkt_len = self._prompt_max_packet_length(default=1300)
        if max_pkt_len is None:
            return

        # Multicast option
        includes_mcast = self._prompt_multicast()

        # Tcpdump filter selection
        tcpdump_expr = self._get_tcpdump_expression_selection()

        # Format selection
        capture_format = self._get_capture_format_selection()

        enable_loop = self._prompt_loop_mode()

        # Build request payload
        payload = {
            "type": "client",
            "client_mac": client_mac,
            "duration": duration,
            "num_packets": num_packets,
            "max_pkt_len": max_pkt_len,
            "includes_mcast": includes_mcast,
            "format": capture_format,
        }

        if ap_mac:
            payload["ap_mac"] = ap_mac

        # Add tcpdump filter if specified
        if tcpdump_expr:
            payload["tcpdump_expression"] = tcpdump_expr

        # Display configuration and confirm
        self._display_client_capture_summary("Wireless Client", payload, enable_loop, ap_mac=ap_mac)

        # Start capture via API
        self._run_site_capture(site_id, payload, enable_loop)

    def _start_site_client_capture_wired(self) -> None:  # noqa: C901, PLR0912, PLR0915
        """Start wired client packet capture at site level."""
        logging.info("Starting site wired client capture")

        # Get site selection
        site_id = _get_prompt_utils().select_site_with_logging()
        if not site_id:
            return

        print("\n" + "-" * 80)
        print(" WIRED CLIENT CAPTURE CONFIGURATION")
        print("-" * 80)

        # Client MAC selection
        client_mac = self._prompt_client_mac(site_id)
        if not client_mac:
            return

        # Duration (Mist API enforces minimum 60 seconds for all captures)
        duration = self._prompt_capture_duration()
        if duration is None:
            return

        num_packets = self._prompt_num_packets()
        if num_packets is None:
            return

        # Multicast option
        includes_mcast = self._prompt_multicast()

        # Tcpdump filter selection
        tcpdump_expr = self._get_tcpdump_expression_selection()

        # Format selection
        capture_format = self._get_capture_format_selection()

        enable_loop = self._prompt_loop_mode()

        # Build payload
        payload = {
            "type": "client",
            "client_mac": client_mac,
            "duration": duration,
            "num_packets": num_packets,
            "includes_mcast": includes_mcast,
            "format": capture_format,
        }

        # Add tcpdump filter if specified
        if tcpdump_expr:
            payload["tcpdump_expression"] = tcpdump_expr

        # Display and confirm
        self._display_client_capture_summary("Wired Client", payload, enable_loop)

        self._run_site_capture(site_id, payload, enable_loop)

    def _start_site_gateway_capture(self) -> None:  # noqa: C901, PLR0912, PLR0915
        """Start gateway packet capture at site level."""
        logging.info("Starting site gateway capture")

        site_id = _get_prompt_utils().select_site_with_logging()
        if not site_id:
            return

        print("\n" + "-" * 80)
        print(" GATEWAY CAPTURE CONFIGURATION")
        print("-" * 80)

        # Gateway selection - interactive list
        logging.debug("Prompting for gateway selection from site inventory")
        gateway_mac = _get_prompt_network_device_utils().select_gateway_mac(site_id)
        if not gateway_mac:
            logging.warning("No gateway selected or gateway selection failed - aborting capture")
            return

        # Normalize MAC address (already validated by selection function)
        gateway_mac = self.normalize_mac_address(gateway_mac)
        logging.debug("Selected and normalized gateway MAC: %s", gateway_mac)

        # Port selection - now using interactive port selector with status information
        logging.debug("Prompting for port selection from gateway")
        port_selection_result = _get_prompt_network_device_utils().select_ports_from_device(
            site_id, gateway_mac, device_type="gateway", return_available=True
        )

        validated = self._validate_port_selection(port_selection_result)
        if validated is None:
            return
        port_list, _available_ports = validated

        # Duration (Mist API enforces minimum 60 seconds for all captures)
        duration = self._prompt_capture_duration()
        if duration is None:
            return

        num_packets = self._prompt_num_packets()
        if num_packets is None:
            return

        # Packet filter selection (applies to all selected ports)
        tcpdump_expr = self._get_tcpdump_expression_selection()

        # Format selection
        capture_format = self._get_capture_format_selection()

        enable_loop = self._prompt_loop_mode()

        # Build payload - CORRECT structure per API spec
        payload = {
            "type": "gateway",
            "duration": duration,
            "num_packets": num_packets,
            "max_pkt_len": 1500,  # API example uses 1500 for gateways
            "format": capture_format,
        }

        # Build gateways structure with actual port names
        ports_config = self._build_ports_config(port_list, tcpdump_expr)
        gateways_config: dict[str, Any] = {}
        gateways_config[gateway_mac] = {"ports": ports_config}
        payload["gateways"] = gateways_config

        # Display and confirm
        self._display_device_capture_summary(
            "Gateway",
            gateway_mac,
            payload,
            enable_loop=enable_loop,
        )

        if enable_loop:
            self._execute_site_capture_loop(site_id, payload)
        else:
            self._execute_site_capture(site_id, payload)

    def _start_site_switch_capture(self) -> None:  # noqa: C901, PLR0912, PLR0915
        """Start switch packet capture at site level."""
        logging.info("Starting site switch capture")

        site_id = _get_prompt_utils().select_site_with_logging()
        if not site_id:
            return

        print("\n" + "-" * 80)
        print(" SWITCH CAPTURE CONFIGURATION")
        print("-" * 80)

        # Switch selection - interactive list
        logging.debug("Prompting for switch selection from site inventory")
        switch_mac = _get_prompt_network_device_utils().select_switch_mac(site_id)
        if not switch_mac:
            logging.warning("No switch selected or switch selection failed - aborting capture")
            return

        # Normalize MAC address (already validated by selection function)
        switch_mac = self.normalize_mac_address(switch_mac)
        logging.debug("Selected and normalized switch MAC: %s", switch_mac)

        # Port selection - now using interactive port selector with status information
        logging.debug("Prompting for port selection from switch")
        port_selection_result = _get_prompt_network_device_utils().select_ports_from_device(
            site_id, switch_mac, device_type="switch", return_available=True
        )

        validated = self._validate_port_selection(port_selection_result)
        if validated is None:
            return
        port_list, _available_ports = validated

        # Duration (Mist API enforces minimum 60 seconds for all captures)
        duration = self._prompt_capture_duration()
        if duration is None:
            return

        num_packets = self._prompt_num_packets()
        if num_packets is None:
            return

        # Packet filter selection (applies to all selected ports)
        tcpdump_expr = self._get_tcpdump_expression_selection()

        # Format selection
        capture_format = self._get_capture_format_selection()

        enable_loop = self._prompt_loop_mode()

        # Build payload
        payload = {
            "type": "switch",
            "duration": duration,
            "num_packets": num_packets,
            "max_pkt_len": 1500,  # API example uses 1500 for switches
            "format": capture_format,
        }

        # Build switches structure with actual port names
        ports_config = self._build_ports_config(port_list, tcpdump_expr)
        switches_config: dict[str, Any] = {}
        switches_config[switch_mac] = {"ports": ports_config}
        payload["switches"] = switches_config

        # Display and confirm
        self._display_device_capture_summary(
            "Switch",
            switch_mac,
            payload,
            enable_loop=enable_loop,
        )

        if enable_loop:
            self._execute_site_capture_loop(site_id, payload)
        else:
            self._execute_site_capture(site_id, payload)

    def _start_site_new_association_capture(self) -> None:
        """Start new association packet capture at site level."""
        logging.info("Starting site new association capture")

        site_id = _get_prompt_utils().select_site_with_logging()
        if not site_id:
            return

        print("\n" + "-" * 80)
        print(" NEW ASSOCIATION CAPTURE CONFIGURATION")
        print("-" * 80)
        print("\nThis capture type monitors NEW client connection attempts (802.11 auth/assoc handshakes).")
        print("Note: To capture ongoing traffic from already-connected clients, use Client Capture (Wireless) instead.")

        # Optional SSID filter
        ssid = _get_input_utils().safe_input(
            "\nEnter SSID to monitor (optional, press Enter for all): ", context="ssid", allow_empty=True
        )

        # Duration (Mist API enforces minimum 60 seconds for new_assoc captures)
        duration = self._prompt_capture_duration()
        if duration is None:
            return

        # Format selection
        capture_format = self._get_capture_format_selection()

        enable_loop = self._prompt_loop_mode()

        # Build payload
        payload = {"type": "new_assoc", "duration": duration, "format": capture_format}

        if ssid:
            payload["ssid"] = ssid

        # Display and confirm
        print("\n" + "=" * 80)
        print(" CAPTURE CONFIGURATION SUMMARY")
        print("=" * 80)
        print("  Capture Type: New Association")
        if ssid:
            print(f"  SSID Filter: {ssid}")
        else:
            print("  SSID Filter: All SSIDs")
        print(f"  Duration: {duration} seconds")
        print(f"  Loop Mode: {'ENABLED (continuous until Ctrl+C)' if enable_loop else 'Disabled (single capture)'}")
        print("=" * 80)

        # Prompt user to proceed (Enter to continue, Ctrl+C to cancel)
        _get_input_utils().safe_input(
            "\nPress Enter to start capture (Ctrl+C to cancel): ", context="confirmation", allow_empty=True
        )

        if enable_loop:
            self._execute_site_capture_loop(site_id, payload)
        else:
            self._execute_site_capture(site_id, payload)

    def _gather_scan_radio_params(self, band: str) -> dict[str, Any] | None:
        """Gather scan radio capture parameters interactively.

        Args:
            band: Radio band string (e.g. '24', '5', '6').

        Returns:
            Dict with channel, bandwidth, duration, num_packets, format
            or None if the user cancelled any prompt.
        """
        channel = self._prompt_scan_channel(band)
        if channel is None:
            return None

        bandwidth = self._prompt_scan_bandwidth(band)
        if bandwidth is None:
            return None

        duration = self._prompt_capture_duration()
        if duration is None:
            return None

        num_packets = self._prompt_num_packets()
        if num_packets is None:
            return None

        capture_format = self._get_capture_format_selection()
        return {
            "channel": channel,
            "bandwidth": bandwidth,
            "duration": duration,
            "num_packets": num_packets,
            "format": capture_format,
        }

    def _start_site_scan_capture(self) -> None:  # noqa: C901, PLR0912
        """Start scan radio packet capture at site level."""
        logging.info("Starting site scan capture")

        site_id = _get_prompt_utils().select_site_with_logging()
        logging.debug("Site selection returned: %s", site_id)
        if not site_id:
            logging.warning("No site_id returned from selection - aborting capture")
            return

        logging.debug("Proceeding with scan capture configuration for site: %s", site_id)
        print("\n" + "-" * 80)
        print(" SCAN RADIO CAPTURE CONFIGURATION")
        print("-" * 80)

        # AP Selection - interactive list
        logging.debug("Prompting for AP selection from site inventory")
        ap_mac = _get_prompt_network_device_utils().select_ap_mac(site_id)
        if not ap_mac:
            logging.warning("No AP selected or AP selection failed - aborting capture")
            return

        # Check if user selected all APs
        if ap_mac == "ALL_APS":
            logging.info("User selected all APs - launching multi-AP captures")
            self._start_site_scan_capture_all_aps(site_id)
            return

        # Normalize MAC address (already validated by selection function)
        ap_mac = self.normalize_mac_address(ap_mac)
        logging.debug("Selected and normalized AP MAC: %s", ap_mac)

        # Band selection
        logging.debug("Prompting for band selection")
        band = self._prompt_scan_band()
        logging.debug("Band selected: %s", band)

        # Gather remaining scan parameters (channel, bandwidth, duration, etc.)
        scan_params = self._gather_scan_radio_params(band)
        if scan_params is None:
            return

        # Format selection loop mode
        enable_loop = self._prompt_loop_mode()

        # Build payload
        logging.debug("Building capture payload")
        payload = {
            "type": "scan",
            "ap_mac": ap_mac,
            "band": band,
            "max_pkt_len": 1300,
            **scan_params,
        }
        logging.debug("Payload constructed: %s", payload)

        # Display and confirm
        self._display_scan_capture_summary(payload, enable_loop)

        logging.info("User confirmed - executing site capture")
        self._run_site_capture(site_id, payload, enable_loop, check_ap_mac=ap_mac)

    def _start_site_scan_capture_all_aps(self, site_id: str) -> None:  # noqa: C901, PLR0912, PLR0915
        """Start scan radio packet captures for ALL APs at a site simultaneously.

        Args:
            site_id (str): Site UUID
        """
        logging.info("Starting multi-AP scan capture for site: %s", site_id)

        # Get all AP MACs from site
        ap_macs = _get_device_utils().get_all_ap_macs_from_site(site_id)
        if not ap_macs:
            print("\n! No APs found at site")
            return

        print(f"\n* Found {len(ap_macs)} APs at site")

        # Check for existing captures at this site
        self._log_existing_site_captures(site_id)

        print(f"  Preparing to launch {len(ap_macs)} simultaneous captures...")

        # Get common capture parameters for all APs
        print("\n" + "-" * 80)
        print(" SCAN RADIO CAPTURE CONFIGURATION (All APs)")
        print("-" * 80)

        # Band selection
        band = self._prompt_scan_band()

        # Channel
        channel = self._prompt_scan_channel(band)
        if channel is None:
            return

        # Bandwidth
        bandwidth = self._prompt_scan_bandwidth(band)

        # Duration
        duration = self._prompt_capture_duration()
        if duration is None:
            return

        # Number of packets
        num_packets = self._prompt_num_packets()
        if num_packets is None:
            return

        # Format selection
        capture_format = self._get_capture_format_selection()

        # Display configuration summary
        print("\n" + "=" * 80)
        print(" MULTI-AP CAPTURE CONFIGURATION SUMMARY")
        print("=" * 80)
        print("  Capture Type: Scan Radio (All APs)")
        print(f"  Number of APs: {len(ap_macs)}")
        print(f"  Band: {band} GHz")
        print(f"  Channel: {channel}")
        print(f"  Bandwidth: {bandwidth} MHz")
        print(f"  Duration: {duration} seconds")
        print(f"  Packets: {num_packets}")
        print(f"  Format: {capture_format}")
        print("=" * 80)

        _get_input_utils().safe_input(
            f"\nPress Enter to start capture for {len(ap_macs)} APs (Ctrl+C to cancel): ",
            context="confirmation",
            allow_empty=True,
        )

        # Build single payload with aps dictionary for all APs
        print(f"\n> Launching multi-AP capture for {len(ap_macs)} APs with single API call...")

        # Build the aps dictionary - each AP uses the same parent configuration
        aps_dict = {}
        for ap_mac in ap_macs:
            normalized_mac = self.normalize_mac_address(ap_mac)
            # Per-AP config inherits from parent, so we can leave empty or specify overrides
            aps_dict[normalized_mac] = {"band": band, "channel": str(channel), "width": str(bandwidth)}

        # Build single payload with parent config + aps dictionary
        payload = {
            "type": "scan",
            "band": band,
            "channel": channel,
            "bandwidth": bandwidth,
            "duration": duration,
            "num_packets": num_packets,
            "format": capture_format,
            "max_pkt_len": 1300,
            "aps": aps_dict,
        }

        logging.debug("Multi-AP payload constructed for %s APs", len(ap_macs))

        try:
            response = mistapi.api.v1.sites.pcaps.startSitePacketCapture(self.mist_session, site_id, payload)
            self._handle_multi_ap_capture_result(response, site_id, duration, capture_format)
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"\n! Error starting multi-AP capture: {error}")
            logging.error("Exception launching multi-AP capture: %s", error, exc_info=True)

        logging.info("Multi-AP scan capture function completed")

    def _execute_site_capture(self, site_id: str, payload: dict[str, Any]) -> None:
        """Execute site-level packet capture via API.

        Args:
            site_id (str): Site UUID
            payload (dict): Capture configuration payload
        """
        try:
            print(f"\n> Starting packet capture for site {site_id}...")
            logging.info("Initiating site capture with payload: %s", payload)

            # Call Mist API to start capture
            response = mistapi.api.v1.sites.pcaps.startSitePacketCapture(self.mist_session, site_id, payload)

            if response.status_code == 200:
                result = response.data
                capture_id = result.get("id", "unknown")
                capture_format = result.get("format", "unknown")
                print("\n* Capture started successfully!")
                print(f"  Capture ID: {capture_id}")
                print(f"  Format: {capture_format}")
                print(f"  Duration: {result.get('duration', 0)} seconds")
                print(f"  Expires: {result.get('expiry', 'unknown')}")

                logging.info("Site capture started: capture_id=%s, format=%s", capture_id, capture_format)

                # Handle based on format
                if capture_format == "pcap":
                    # PCAP file format - wait for file and download
                    print("\n> Waiting for PCAP file to be ready...")
                    print("  This may take a few moments after capture completes.")
                    self._wait_and_download_pcap(site_id, capture_id, result.get("duration", 600))
                elif capture_format == "stream":
                    # Stream format - subscribe to WebSocket
                    self._subscribe_to_site_capture_stream(site_id, capture_id)

                # Export capture details to CSV
                self._export_capture_info_to_csv(result, "site", site_id)

            else:
                error_details = response.data if hasattr(response, "data") else "No error details available"

                # Check for specific "Recording already in progress" error
                if response.status_code == 400 and isinstance(error_details, dict):
                    if "Recording already in progress" in error_details.get("detail", ""):
                        print("\n! Capture already in progress on this AP")
                        print("  Only one capture per AP is allowed at a time")
                        print("  Wait for the existing capture to complete or check the Mist portal to stop it")
                        logging.error("Capture conflict: Recording already in progress on AP")
                        return

                print(f"\n! Failed to start capture: {response.status_code}")
                print(f"  Error details: {error_details}")
                logging.error("Capture failed: %s - %s", response.status_code, error_details)

        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"\n! Error starting capture: {error}")
            logging.error("Exception in _execute_site_capture: %s", error, exc_info=True)

    def _fetch_completed_pcaps(self, site_id: str, iteration: int) -> list[dict[str, Any]]:
        """Fetch completed PCAPs from the API for the last 24 hours.

        Args:
            site_id: Site UUID
            iteration: Current loop iteration number

        Returns:
            List of completed PCAP records with download URLs.
        """

        def list_fn() -> Any:
            return mistapi.api.v1.sites.pcaps.listSitePacketCaptures(
                self.mist_session,
                site_id,
                duration="1d",
                limit=100,
            )

        return self._download_manager.fetch_completed_pcaps(list_fn, iteration)

    def _download_pending_pcaps(self, completed_pcaps: list[dict[str, Any]], download_folder: str) -> int:
        """Download PCAPs that are not already saved locally.

        Args:
            completed_pcaps: List of completed PCAP records from the API
            download_folder: Local folder path for saving PCAP files

        Returns:
            Number of newly downloaded files.
        """
        return self._download_manager.download_pending_pcaps(
            completed_pcaps,
            download_folder,
            self._download_single_pcap,
        )

    def _download_single_pcap(self, url: str, local_path: str, filename: str, capture_id: str) -> int:
        """Download a single PCAP file from a URL.

        Args:
            url: Download URL for the PCAP
            local_path: Full local file path to save to
            filename: Display filename for logging
            capture_id: Capture ID for logging

        Returns:
            1 if downloaded successfully, 0 otherwise.
        """
        return self._download_manager.download_single_pcap(
            url,
            local_path,
            filename,
            capture_id,
            requests_module=requests,
        )

    def _attempt_loop_capture(self, site_id: str, payload: dict[str, Any], iteration: int) -> float | None:
        """Attempt to start a new capture and return the capture start time.

        Args:
            site_id: Site UUID
            payload: Capture configuration payload
            iteration: Current loop iteration number

        Returns:
            Time of capture start if successful, None otherwise.
        """
        print("\n  Starting new packet capture...")
        logging.info("Loop iteration %s: Starting new capture with payload: %s", iteration, payload)

        try:
            response = mistapi.api.v1.sites.pcaps.startSitePacketCapture(self.mist_session, site_id, payload)
        except Exception as capture_error:  # pylint: disable=broad-exception-caught
            print(f"  Error starting capture: {capture_error}")
            logging.error("Exception starting capture: %s", capture_error, exc_info=True)
            return None

        if response.status_code != 200:
            error_details = response.data if hasattr(response, "data") else "No error details"
            print(f"  Failed to start capture: HTTP {response.status_code}")
            print(f"    Error: {error_details}")
            logging.error("Loop iteration %s capture failed: %s - %s", iteration, response.status_code, error_details)
            if response.status_code == 400 and isinstance(error_details, dict):
                if "Recording already in progress" in error_details.get("detail", ""):
                    print("    Capture conflict detected - will retry next loop")
            return None

        result = response.data
        capture_id = result.get("id", "unknown")
        duration = result.get("duration", 600)
        print("  Capture started successfully!")
        print(f"    Capture ID: {capture_id}")
        print(f"    Duration: {duration} seconds")
        logging.info("Loop iteration %s: Capture started - ID=%s", iteration, capture_id)
        self._export_capture_info_to_csv(result, "site", site_id)
        return time.time()

    def _execute_site_capture_loop(self, site_id: str, payload: dict[str, Any]) -> None:
        """Execute site-level packet captures in continuous loop mode.

        Strategy: fetch completed PCAPs, download new ones, start a new capture, repeat.

        Args:
            site_id: Site UUID
            payload: Capture configuration payload (reused each iteration)
        """
        runner = SiteCaptureLoopRunner(manager=self)
        try:
            runner.run(site_id, payload)
        except Exception as loop_error:  # pylint: disable=broad-exception-caught
            print(f"\n! Unexpected error in capture loop: {loop_error}")
            logging.error("Exception in capture loop: %s", loop_error, exc_info=True)

    def _print_loop_banner(self, payload: dict[str, Any]) -> None:
        """Print the continuous capture mode startup banner.

        Args:
            payload: Capture configuration payload
        """
        print(f"\n{'=' * 80}\n CONTINUOUS CAPTURE MODE ACTIVE\n{'=' * 80}")
        print("  Press Ctrl+C to stop and exit gracefully")
        print(f"  Capture duration: {payload.get('duration', 60)} seconds")
        print(f"  Strategy: Download existing PCAPs, then start new captures\n{'=' * 80}\n")

    def _check_capture_readiness(self, last_capture_time: float | None, min_interval: int) -> float:
        """Determine if enough time has elapsed to start a new capture.

        Args:
            last_capture_time: Timestamp of last capture start, or None
            min_interval: Minimum seconds between captures

        Returns:
            Remaining wait time in seconds (0 means ready to capture).
        """
        print("\n[Step 3/3] Checking if ready to start new capture...")
        if last_capture_time is None:
            print("  First capture of this session - starting now")
            return 0

        elapsed = time.time() - last_capture_time
        if elapsed >= min_interval:
            print(f"  {elapsed:.0f}s elapsed since last capture (>= {min_interval}s) - ready")
            return 0

        wait_time = min_interval - elapsed
        print(f"  Only {elapsed:.0f}s elapsed - waiting {wait_time:.0f}s more...")
        return wait_time

    @staticmethod
    def _calc_loop_sleep(wait_time: float, loop_duration: float) -> float:
        """Calculate sleep time before next loop iteration.

        Args:
            wait_time: Remaining capture interval wait (0 if capture just started)
            loop_duration: How long the current iteration took

        Returns:
            Seconds to sleep before next iteration.
        """
        if wait_time > 0:
            return wait_time
        if loop_duration < 30:
            return 30 - loop_duration
        return 10

    def _check_capture_status(
        self,
        captures: list[dict[str, Any]],
        capture_id: str,
        expected_duration: int,
        progress: tuple[float, int],
    ) -> bool | None:
        """Check if a specific capture has completed.

        Args:
            captures: List of capture records from API.
            capture_id: Target capture ID.
            expected_duration: Expected capture duration in seconds.
            progress: Tuple of (elapsed_seconds, poll_attempt_number).

        Returns:
            True if complete, False if not found, None if still running.
        """
        elapsed, poll_attempt = progress
        for capture in captures:
            if not isinstance(capture, dict):
                continue
            if capture.get("id") != capture_id:
                continue

            enabled = capture.get("enabled", True)
            timestamp = capture.get("timestamp", 0)
            time_running = time.time() - timestamp if timestamp else elapsed

            if not enabled:
                logging.debug("Capture %s completed (enabled=False)", capture_id)
                return True
            if time_running >= expected_duration:
                logging.debug("Capture %s completed (duration reached)", capture_id)
                return True

            remaining = int(expected_duration - time_running)
            if poll_attempt % 5 == 0:
                print(f"  ...capture in progress (~{remaining}s remaining)", end="\r")
            logging.debug("Capture %s still running (%ss remaining)", capture_id, remaining)
            return None

        # Capture not found
        if elapsed < 10:
            logging.debug("Capture %s not found yet (elapsed=%ss)", capture_id, elapsed)
        else:
            logging.warning("Capture %s not found in list (elapsed=%ss)", capture_id, elapsed)
        return False

    def _wait_for_capture_completion(
        self,
        site_id: str,
        capture_id: str,
        expected_duration: int,
    ) -> bool:  # noqa: C901, PLR0912
        """Poll for capture completion status (separate from PCAP download availability).

        Returns as soon as capture completes, does not wait for PCAP file URL.

        Args:
            site_id (str): Site UUID
            capture_id (str): Capture session ID
            expected_duration (int): Expected capture duration in seconds

        Returns:
            bool: True if capture confirmed complete, False if timeout/error
        """
        poll_interval = 3
        max_wait = expected_duration + 30
        max_polls = max_wait // poll_interval
        start_time = time.time()

        for poll_attempt in range(1, max_polls + 1):
            try:
                elapsed = time.time() - start_time
                response = mistapi.api.v1.sites.pcaps.listSitePacketCaptures(self.mist_session, site_id)

                if response.status_code == 200:
                    captures = self._parse_captures_response(response.data, poll_attempt)
                    status = self._check_capture_status(
                        captures,
                        capture_id,
                        expected_duration,
                        (elapsed, poll_attempt),
                    )
                    if status is True:
                        return True

                time.sleep(poll_interval)

            except Exception as poll_error:  # pylint: disable=broad-exception-caught
                logging.error("Completion poll error: %s", poll_error, exc_info=True)
                time.sleep(poll_interval)

        logging.warning("Capture %s completion check timed out after %ss", capture_id, max_wait)
        return False

    def _fetch_org_mxedges(self) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
        """Fetch MxEdges and their stats for org-level captures.

        Returns:
            Tuple of (mxedge_list, stats_map) or None on failure.
        """
        print("\n  Fetching available MxEdges...")
        try:
            response = mistapi.api.v1.orgs.mxedges.listOrgMxEdges(self.mist_session, self.org_id, limit=1000)
            mxedges = mistapi.get_all(response=response, mist_session=self.mist_session)
            if not mxedges:
                print("\n! No MxEdges found for this organization")
                logging.warning("Menu #10: No MxEdges found")
                return None
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"\n! Error fetching MxEdges: {error}")
            logging.error("Menu #10: Failed to fetch MxEdges: %s", error)
            return None

        print("  Fetching MxEdge status information...")
        stats_map: dict[str, Any] = {}
        try:
            stats_response = mistapi.api.v1.orgs.stats.listOrgMxEdgesStats(self.mist_session, self.org_id, limit=1000)
            stats_data = mistapi.get_all(response=stats_response, mist_session=self.mist_session)
            if stats_data:
                for stat in stats_data:
                    mxedge_id = stat.get("id")
                    if mxedge_id:
                        stats_map[mxedge_id] = stat
        except Exception as error:  # pylint: disable=broad-exception-caught
            logging.warning("Menu #10: Failed to fetch MxEdge stats: %s", error)

        return mxedges, stats_map

    def _display_and_select_mxedge(
        self,
        mxedges: list[dict[str, Any]],
        stats_map: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Display MxEdge list and prompt user to select one.

        Args:
            mxedges: List of MxEdge objects from API.
            stats_map: Map of mxedge_id to stats data.

        Returns:
            Selected MxEdge dict, or None if cancelled.
        """
        print(f"\n  Available MxEdges ({len(mxedges)} found):")
        print("=" * 120)

        index_to_mxedge: dict[int, dict[str, Any]] = {}
        for index, mxedge in enumerate(mxedges):
            self._print_mxedge_row(index, mxedge, stats_map)
            index_to_mxedge[index] = mxedge

        print()
        print("  ! API Limitation: Only 1 MxEdge can be captured at a time for organization-level captures")
        try:
            selection_input = (
                _get_input_utils()
                .safe_input(f"Select MxEdge index [0-{len(mxedges) - 1}]: ", context="mxedge_selection")
                .strip()
            )
        except (EOFError, KeyboardInterrupt):
            print("\n! Operation cancelled")
            logging.info("Menu #10: User cancelled MxEdge selection")
            return None

        try:
            idx = int(selection_input)
            if idx not in index_to_mxedge:
                print(f"\n! Invalid index {idx}. Please select from 0-{len(mxedges) - 1}")  # nosec B608
                logging.warning("Menu #10: Invalid MxEdge index: %s", idx)
                return None
        except ValueError:
            print("\n! Invalid input format. Please enter a single numeric index.")
            logging.warning("Menu #10: Invalid selection input: %s", selection_input)
            return None

        selected = index_to_mxedge[idx]
        print("\n  Selected MxEdge:")
        print(f"    -> {selected.get('name', 'Unnamed')} (ID: {selected.get('id')})")
        return selected

    def _print_mxedge_row(self, index: int, mxedge: dict[str, Any], stats_map: dict[str, Any]) -> None:
        """Print a single MxEdge row with status details.

        Args:
            index: Display index for selection.
            mxedge: MxEdge config dict from API.
            stats_map: Map of mxedge_id to stats data.
        """
        mxedge_name = mxedge.get("name", "Unnamed MxEdge")
        mxedge_id = mxedge.get("id", "No ID")
        model = mxedge.get("model", "Unknown")

        stat = stats_map.get(mxedge_id, {})
        status = stat.get("status", "unknown")
        uptime = stat.get("uptime", 0)
        service_stat = stat.get("service_stat", {})

        if uptime > 0:
            uptime_str = f"{uptime // 86400}d {(uptime % 86400) // 3600}h"
        else:
            uptime_str = "N/A"

        mxagent_state = service_stat.get("mxagent", {}).get("running_state", "Unknown")
        tunterm_state = service_stat.get("tunterm", {}).get("running_state", "Unknown")

        if status == "connected":
            status_marker = "ONLINE"
        elif status == "disconnected":
            status_marker = "OFFLINE"
        else:
            status_marker = status.upper()

        print(
            f"  [{index}] {mxedge_name:30} | Model: {model:10}"
            f" | Status: {status_marker:8} | Uptime: {uptime_str:10}"
        )
        print(f"       mxagent: {mxagent_state:15} | tunterm: {tunterm_state:15}")

    def _display_mxedge_ports(self, mxedge_name: str, port_stat: dict[str, Any]) -> list[str]:
        """Display MxEdge interface stats and return port name list.

        Args:
            mxedge_name: MxEdge display name.
            port_stat: Port statistics dictionary from API.

        Returns:
            Ordered list of port names.
        """
        port_list: list[str] = []
        print(f"\n  {mxedge_name} - Available Interfaces:")
        print(f"  {'-' * 70}")
        for port_index, (port_name, port_info) in enumerate(sorted(port_stat.items())):
            status = "UP" if port_info.get("up", False) else "DOWN"
            speed = port_info.get("speed", 0)
            speed_str = f"{speed}Mbps" if speed else "N/A"
            mac = port_info.get("mac", "N/A")
            print(f"    [{port_index}] {port_name:10} Status: {status:5} Speed: {speed_str:10} MAC: {mac}")
            port_list.append(port_name)
        return port_list

    def _select_port_by_index(
        self,
        port_list: list[str],
        mxedge_name: str,
        mxedge_id: str,
    ) -> list[str] | None:
        """Prompt user to select a port by index.

        Args:
            port_list: Available port names.
            mxedge_name: MxEdge display name.
            mxedge_id: MxEdge UUID for logging.

        Returns:
            Single-element list with selected port name, or None.
        """
        print("\n  Port Selection:")
        print("  ! API Limitation: Only 1 port can be captured at a time")

        try:
            port_input = (
                _get_input_utils()
                .safe_input(
                    f"\n  {mxedge_name} - Select a single port index [0-{len(port_list) - 1}]: ",
                    context=f"port_selection_{mxedge_id}",
                )
                .strip()
            )
        except (EOFError, KeyboardInterrupt):
            print("\n! Operation cancelled")
            logging.info("Menu #10: User cancelled port selection")
            return None

        if not port_input:
            print("\n! Port selection is required. Please select a port index.")
            logging.warning("Menu #10: No port selected")
            return None

        try:
            idx = int(port_input)
            if 0 <= idx < len(port_list):
                selected_port = port_list[idx]
                print(f"    -> Selected port: {selected_port}")
                return [selected_port]
            print(f"\n! Invalid index {idx} (valid range: 0-{len(port_list) - 1})")
            logging.warning("Menu #10: Invalid port index: %s", idx)
            return None
        except ValueError:
            print("\n! Invalid input format. Please enter a single numeric index.")
            logging.warning("Menu #10: Invalid port input: %s", port_input)
            return None

    def _fetch_and_select_mxedge_port(self, mxedge: dict[str, Any]) -> list[str] | None:
        """Fetch MxEdge interfaces and prompt port selection.

        Args:
            mxedge: Selected MxEdge dict from API.

        Returns:
            List with single selected port name, or None on failure/cancel.
        """
        mxedge_id: str = mxedge.get("id", "")
        mxedge_name: str = mxedge.get("name", "Unnamed MxEdge")
        try:
            stats_response = mistapi.api.v1.orgs.stats.getOrgMxEdgeStats(self.mist_session, self.org_id, mxedge_id)
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"\n  {mxedge_name} - Error fetching stats: {error}")
            logging.error("Menu #10: Failed to fetch stats for %s: %s", mxedge_name, error)
            return None

        if stats_response.status_code != 200:
            print(f"\n  {mxedge_name} - Failed to fetch stats (HTTP {stats_response.status_code})")
            return None

        stats_data = stats_response.data if hasattr(stats_response, "data") else {}
        port_stat = stats_data.get("port_stat", {})
        if not port_stat:
            print(f"\n  {mxedge_name} - No interface stats available")
            return None

        port_list = self._display_mxedge_ports(mxedge_name, port_stat)
        if not port_list:
            print(f"\n  {mxedge_name}: No ports available")
            return None

        return self._select_port_by_index(port_list, mxedge_name, mxedge_id)

    def _prompt_org_format_selection(self) -> tuple[str, str | None, int | None] | None:
        """Prompt for org capture format (stream or TZSP).

        Returns:
            Tuple of (format, tzsp_host, tzsp_port) or None on invalid input.
        """
        print("\nCapture format:")
        print("  1. Stream to Mist Cloud (default)")
        print("  2. TZSP stream to remote host (Wireshark)")
        format_choice = _get_input_utils().safe_input("Enter choice (default 1): ", default_value="1", context="format")

        if format_choice != "2":
            return ("stream", None, None)

        tzsp_host = _get_input_utils().safe_input("Enter TZSP host (IP address or hostname): ", context="tzsp_host")
        if not tzsp_host:
            print("\n! TZSP host required")
            return None

        tzsp_port_str = _get_input_utils().safe_input(
            "Enter TZSP port (default 37008): ", default_value="37008", context="tzsp_port"
        )
        try:
            tzsp_port = int(tzsp_port_str)
            if tzsp_port < 1 or tzsp_port > 65535:
                print("\n! Port must be between 1 and 65535")
                return None
        except ValueError:
            print(f"\n! Invalid port: {tzsp_port_str}")
            return None

        return ("tzsp", tzsp_host, tzsp_port)

    def _gather_org_capture_params(
        self,
    ) -> tuple[int, int, int, str, str | None, int | None] | None:
        """Gather org capture parameters interactively.

        Returns:
            Tuple of (duration, num_packets, max_pkt_len,
            capture_format, tzsp_host, tzsp_port) or None if cancelled.
        """
        duration = self._prompt_capture_duration(default=30, min_val=30)
        if duration is None:
            return None
        num_packets = self._prompt_num_packets()
        if num_packets is None:
            return None
        max_pkt_len = self._prompt_max_packet_length()
        if max_pkt_len is None:
            return None
        format_result = self._prompt_org_format_selection()
        if format_result is None:
            return None
        capture_format, tzsp_host, tzsp_port = format_result
        return (duration, num_packets, max_pkt_len, capture_format, tzsp_host, tzsp_port)

    def start_org_packet_capture(self) -> None:
        """Interactive menu for starting org-level packet captures (MxEdge only).

        NOTE: Organization-level captures are for Mist Edges only.
        Site-level Mist Edges should use site captures (option 9).
        """
        logging.info("Menu #10: Starting organization packet capture manager")
        logging.debug("ENTRY: PacketCaptureManager.start_org_packet_capture()")

        print("\n" + "=" * 80)
        print(" ORGANIZATION PACKET CAPTURE MANAGER")
        print("=" * 80)
        print("\n! NOTE: Org-level captures are for organization-level Mist Edges ONLY")
        print("  For site-level Mist Edges, use Site Packet Capture (option 9)")
        print("\n" + "=" * 80)
        workflow = OrgCaptureWorkflow(manager=self)
        workflow.run()

    def _confirm_and_execute_org_capture(self, payload: dict[str, Any]) -> None:
        """Prompt for confirmation and execute org capture payload."""
        _get_input_utils().safe_input(
            "\nPress Enter to start capture (Ctrl+C to cancel): ",
            context="confirmation",
            allow_empty=True,
        )
        self._execute_org_capture(payload)

    @staticmethod
    def _log_loop_stop(iteration: int) -> None:
        """Log loop-stop summary after keyboard interrupt in loop mode."""
        logging.info("Capture loop stopped by user after %s iterations", iteration)

    def _build_org_payload(
        self,
        mxedge: dict[str, Any],
        ports: list[str],
        tcpdump_expr: str,
        capture_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the API payload for org-level MxEdge capture.

        Args:
            mxedge: Selected MxEdge dict.
            ports: List of selected port names.
            tcpdump_expr: Tcpdump filter expression.
            capture_config: Dict with keys: duration, num_packets,
                max_pkt_len, format, tzsp_host, tzsp_port.

        Returns:
            API payload dict.
        """
        mxedge_id: str = mxedge.get("id", "")
        capture_format = capture_config["format"]
        payload: dict[str, Any] = {
            "type": "mxedge",
            "duration": capture_config["duration"],
            "num_packets": capture_config["num_packets"],
            "max_pkt_len": capture_config["max_pkt_len"],
            "format": capture_format,
            "mxedges": {mxedge_id: {}},
        }
        if tcpdump_expr:
            payload["tcpdump_expression"] = tcpdump_expr
        if ports:
            payload["mxedges"][mxedge_id]["interfaces"] = {port: {} for port in ports}
        if capture_format == "tzsp":
            payload["tzsp_host"] = capture_config.get("tzsp_host")
            payload["tzsp_port"] = capture_config.get("tzsp_port")
        return payload

    def _display_org_capture_summary(
        self,
        payload: dict[str, Any],
        mxedge: dict[str, Any],
        ports: list[str],
        tcpdump_expr: str,
    ) -> None:
        """Display org capt[str, Any], mxedge: dict[str, Any]ion summary.

        Args:
            payload: Built API payload dict.
            mxedge: Selected MxEdge dict.
            ports: List of selected port names.
            tcpdump_expr: Tcpdump filter expression.
        """
        print("\n" + "=" * 80)
        print(" CAPTURE CONFIGURATION SUMMARY")
        print("=" * 80)
        print("  Capture Type: MxEdge (Organization Level)")
        print(f"  MxEdge: {mxedge.get('name', 'Unnamed')} (ID: {mxedge.get('id')})")
        print(f"  Port: {ports[0] if ports else 'None'}")
        if tcpdump_expr:
            print(f"  Packet Filter: {tcpdump_expr}")
        else:
            print("  Packet Filter: None (all traffic)")
        duration = payload.get("duration", 0)
        num_packets = payload.get("num_packets", 0)
        print(f"  Duration: {duration} seconds")
        print(f"  Packets: {num_packets} ({'unlimited' if num_packets == 0 else 'max'})")
        print(f"  Max Packet Length: {payload.get('max_pkt_len', 0)} bytes")
        capture_format = payload.get("format", "stream")
        print(f"  Format: {capture_format}")
        if capture_format == "tzsp":
            print(f"  TZSP Host: {payload.get('tzsp_host')}:{payload.get('tzsp_port')}")
        print("=" * 80)

    def _execute_org_capture(self, payload: dict[str, Any]) -> None:
        """Execute org-level packet capture via API.

        Args:
            payload (dict): Capture configuration payload
        """
        try:
            print("\n> Starting organization packet capture...")
            logging.info("Initiating org capture with payload: %s", payload)

            # Call Mist API to start capture
            response = mistapi.api.v1.orgs.pcaps.startOrgPacketCapture(self.mist_session, self.org_id, payload)

            if response.status_code == 200:
                result = response.data
                capture_id = result.get("id", "unknown")
                print("\n* Capture started successfully!")
                print(f"  Capture ID: {capture_id}")
                print(f"  Format: {result.get('format', 'unknown')}")
                print(f"  Duration: {result.get('duration', 0)} seconds")
                print(f"  Expires: {result.get('expiry', 'unknown')}")

                logging.info("Org capture started: capture_id=%s", capture_id)

                # Handle based on format type
                capture_format = result.get("format", "pcap")

                if capture_format == "pcap":
                    # Wait for PCAP file and download it
                    # Note: For org captures, we need the org ID instead of site_id
                    self._wait_and_download_pcap_org(self.org_id, capture_id, result.get("duration", 60))
                elif capture_format == "stream":
                    # Subscribe to WebSocket for streaming results
                    self._subscribe_to_org_capture_stream(capture_id)

                # Export capture details to CSV
                self._export_capture_info_to_csv(result, "org", self.org_id)

            else:
                print(f"\n! Failed to start capture: {response.status_code}")
                error_details = response.data if hasattr(response, "data") else "No error details available"
                print(f"  Error details: {error_details}")
                logging.error("Capture failed: %s - %s", response.status_code, error_details)

        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"\n! Error starting capture: {error}")
            logging.error("Exception in _execute_org_capture: %s", error, exc_info=True)

    def _monitor_capture_stream(self, channel: str, capture_id: str) -> None:
        """Monitor WebSocket stream for capture packets.

        Shared implementation for site and org capture streams.

        Args:
            channel: WebSocket channel path.
            capture_id: Capture session ID.
        """
        try:
            print("\n> Subscribing to capture stream...")
            print("  Press Ctrl+C to stop monitoring")

            if not self.websocket_manager:
                self.websocket_manager = _get_websocket_manager()(self.mist_session)
            if not self.websocket_manager.connected:
                self.websocket_manager.connect()

            self.websocket_manager.subscribe_to_channel(channel)
            confirmed = self.websocket_manager.wait_for_subscription_confirmation(channel, timeout_seconds=10)

            if not confirmed:
                print("\n! Failed to subscribe to capture stream")
                return

            print("\n* Subscribed to capture stream")
            print(f"  Capture ID: {capture_id}")
            print("  Monitoring for packets...")
            print("-" * 80)

            self._read_stream_packets(channel, capture_id)

        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"\n! Error subscribing to stream: {error}")
            logging.error("Exception in _monitor_capture_stream: %s", error, exc_info=True)

    def _read_stream_packets(self, channel: str, capture_id: str) -> None:
        """Read and count packets from WebSocket stream.

        Args:
            channel: WebSocket channel to monitor.
            capture_id: Target capture session ID.
        """
        packet_count = 0
        start_time = time.time()

        if self.websocket_manager is None:
            logging.error("WebSocket manager not available for stream reading")
            return

        try:
            while True:
                with self.websocket_manager.results_lock:
                    messages = list(self.websocket_manager.command_results.values())

                for msg in messages:
                    if msg.get("channel") != channel:
                        continue
                    data = msg.get("data", {})
                    if data.get("capture_id") != capture_id:
                        continue
                    packet_count += 1
                    if packet_count % 10 == 0:
                        elapsed = time.time() - start_time
                        print(f"  Received {packet_count} packets ({elapsed:.1f}s elapsed)")
                    if data.get("pcap_dict") is None:
                        print(f"\n* Capture completed: {packet_count} packets received")
                        return

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n\n! Monitoring stopped by user")
            print(f"  Total packets received: {packet_count}")

    def _subscribe_to_site_capture_stream(self, site_id: str, capture_id: str) -> None:
        """Subscribe to WebSocket stream for site capture results.

        Args:
            site_id (str): Site UUID
            capture_id (str): Capture session ID
        """
        channel = f"/sites/{site_id}/pcaps"
        self._monitor_capture_stream(channel, capture_id)

    def _subscribe_to_org_capture_stream(self, capture_id: str) -> None:
        """Subscribe to WebSocket stream for org capture results.

        Args:
            capture_id (str): Capture session ID
        """
        channel = f"/orgs/{self.org_id}/pcaps"
        self._monitor_capture_stream(channel, capture_id)

    def _wait_and_download_pcap(self, site_id: str, capture_id: str, duration: int) -> None:
        """Wait for site-level PCAP capture to complete and download the file.

        Args:
            site_id: Site UUID
            capture_id: Capture session ID returned from API
            duration: Expected capture duration in seconds
        """

        def list_fn() -> Any:
            return mistapi.api.v1.sites.pcaps.listSitePacketCaptures(self.mist_session, site_id)

        self._poll_and_download_pcap(list_fn, capture_id, duration, prefix="")

    def _wait_and_download_pcap_org(self, org_id: str, capture_id: str, duration: int) -> None:
        """Wait for org-level PCAP capture to complete and download the file.

        Args:
            org_id: Organization UUID
            capture_id: Capture session ID returned from API
            duration: Expected capture duration in seconds
        """

        def list_fn() -> Any:
            return mistapi.api.v1.orgs.pcaps.listOrgPacketCaptures(self.mist_session, org_id)

        self._poll_and_download_pcap(list_fn, capture_id, duration, prefix="org_")

    def _poll_and_download_pcap(
        self,
        list_captures_fn: Callable[[], Any],
        capture_id: str,
        duration: int,
        prefix: str = "",
    ) -> None:
        """Poll for PCAP readiness and download the file.

        Args:
            list_captures_fn: Callable that returns the API response for listing captures
            capture_id: Capture session ID
            duration: Expected capture duration in seconds
            prefix: Filename prefix (e.g. 'org_' for org-level captures)
        """
        print(f"\n* Capture initiated (ID: {capture_id})")
        print(f"  Duration: {duration} seconds (plus processing time)")
        print("  Polling for PCAP file availability...")
        print("  Press Ctrl+C to cancel wait and check portal manually")
        logging.info("Polling for PCAP availability for capture %s", capture_id)

        pcap_url: str | None = None
        try:
            pcap_url = self._poll_for_pcap_url(list_captures_fn, capture_id, duration)
            if not pcap_url:
                logging.debug("Polling finished for %s without a downloadable URL", capture_id)
                return

            logging.info("PCAP URL resolved for %s; starting file save", capture_id)
            self._save_pcap_file(pcap_url, capture_id, prefix)
            logging.debug("PCAP save callback completed for %s", capture_id)
        except KeyboardInterrupt:
            print("\n\n! Download cancelled by user")
            print(f"  Capture ID: {capture_id}")
            if pcap_url:
                print(f"  Download manually from: {pcap_url}")
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"\n! Error downloading PCAP file: {error}")
            logging.error("Exception in poll_and_download_pcap for %s: %s", capture_id, error, exc_info=True)
            if pcap_url:
                print(f"  Try downloading manually from: {pcap_url}")

    def _poll_for_pcap_url(
        self,
        list_captures_fn: Callable[[], Any],
        capture_id: str,
        duration: int,
    ) -> str | None:
        """Poll the API until the PCAP download URL is available.

        Args:
            list_captures_fn: Callable returning API response for listing captures
            capture_id: Capture session ID to look for
            duration: Expected capture duration (used to calculate timeout)

        Returns:
            PCAP download URL if found, None if timed out.
        """
        return self._download_manager.poll_for_pcap_url(
            list_captures_fn,
            capture_id,
            duration,
            sleep_fn=time.sleep,
        )

    @staticmethod
    def _parse_captures_response(raw_data: Any, poll_attempt: int) -> list[dict[str, Any]]:
        """Parse API response into a list of capture records.

        Args:
            raw_data: Raw API response data (dict or list)
            poll_attempt: Current poll attempt number for logging

        Returns:
            List of capture records.
        """
        return PacketCaptureDownloadManager.parse_captures_response(raw_data, poll_attempt)

    @staticmethod
    def _find_capture_url(captures: list[dict[str, Any]], capture_id: str, poll_attempt: int) -> str | None:
        """Find the PCAP URL for a specific capture ID in the captures list.

        Args:
            captures: List of capture records
            capture_id: Target capture ID
            poll_attempt: Current poll attempt for logging

        Returns:
            PCAP download URL if found and ready, None otherwise.
        """
        return PacketCaptureDownloadManager.find_capture_url(captures, capture_id, poll_attempt)

    @staticmethod
    def _save_pcap_file(pcap_url: str, capture_id: str, prefix: str = "") -> None:
        """Download and save a PCAP file from a URL.

        Args:
            pcap_url: URL to download from
            capture_id: Capture ID for filename
            prefix: Filename prefix (e.g. 'org_')
        """
        PacketCaptureDownloadManager.save_pcap_file(
            pcap_url,
            capture_id,
            prefix,
            requests_module=requests,
        )

    def _export_capture_info_to_csv(self, capture_data: dict[str, Any], scope: str, scope_id: str) -> None:
        """Export capture session information to CSV.

        Args:
            capture_data (dict): Capture response from API
            scope (str): 'site' or 'org'
            scope_id (str): Site or org UUID
        """
        try:
            filename = f"PacketCapture_{scope}_{capture_data.get('id', 'unknown')}.csv"

            # Add scope context
            export_data = {"scope": scope, "scope_id": scope_id, **capture_data}

            _get_data_exporter().write_with_format_selection(
                [export_data],
                filename,
                api_function_name="startSitePacketCapture" if scope == "site" else "startOrgPacketCapture",
            )

            print(f"\n* Capture info exported to: {filename}")
            logging.info("Capture info exported to %s", filename)

        except Exception as error:  # pylint: disable=broad-exception-caught
            logging.error("Failed to export capture info: %s", error, exc_info=True)
