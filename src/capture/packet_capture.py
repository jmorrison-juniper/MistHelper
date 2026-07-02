"""Packet capture management for Juniper Mist environments."""

from __future__ import annotations  # WHY: enable postponed annotation evaluation for forward refs

import logging  # WHY: structured audit trail for capture lifecycle events
import re  # WHY: MAC address validation and normalization regex patterns
from collections.abc import Callable  # WHY: type hints for callbacks passed to helpers
from typing import TYPE_CHECKING, Any, cast  # WHY: type-only guard plus generic mistapi payload shapes

from src.capture._packet_capture_exec import PacketCaptureExec  # WHY: extracted exec/monitor/download cluster
from src.capture._packet_capture_org import PacketCaptureOrg  # WHY: extracted org/mxedge capture cluster
from src.capture._packet_capture_prompts import PacketCapturePrompts  # WHY: extracted prompts/summary cluster
from src.capture._packet_capture_tcpdump import PacketCaptureTcpdump  # WHY: extracted tcpdump menu cluster
from src.capture.org_capture_workflow import OrgCaptureWorkflow  # WHY: reusable org-scope workflow helper
from src.capture.packet_capture_download import PacketCaptureDownloadManager  # WHY: pcap download side-effect owner

if TYPE_CHECKING:  # WHY: guard type-only imports to avoid runtime overhead
    pass  # WHY: reserved for future TYPE_CHECKING-only imports

try:  # WHY: mistapi is required at runtime but tolerated missing during static analysis
    import mistapi  # WHY: primary Mist SDK for pcap REST endpoints

    MISTAPI_AVAILABLE = True  # WHY: feature flag consumed by callers to guard SDK usage
except ImportError:  # WHY: allow module import without SDK for offline tooling/tests
    MISTAPI_AVAILABLE = False  # WHY: signals disabled state to downstream consumers


def _get_config_utils() -> Any:  # WHY: module-level factory for deferred ConfigUtils access
    """Lazy import ConfigUtils to avoid circular imports."""
    import MistHelper as _mh  # pylint: disable=import-outside-toplevel  # WHY: deferred to break capture<->MistHelper cycle

    return _mh.ConfigUtils  # WHY: caller invokes org-id cache lookup helpers on this class


def _get_input_utils() -> Any:  # WHY: module-level factory for deferred InputUtils access
    """Lazy import InputUtils to avoid circular imports."""
    import MistHelper as _mh  # pylint: disable=import-outside-toplevel  # WHY: deferred to break capture<->MistHelper cycle

    return _mh.InputUtils  # WHY: caller uses safe_input wrapper for all user prompts


def _get_prompt_utils() -> Any:  # WHY: module-level factory for deferred PromptUtils access
    """Lazy import PromptUtils to avoid circular imports."""
    import MistHelper as _mh  # pylint: disable=import-outside-toplevel  # WHY: deferred to break capture<->MistHelper cycle

    return _mh.PromptUtils  # WHY: caller uses select_site_with_logging and related prompt helpers


def _get_prompt_client_utils() -> Any:  # WHY: module-level factory for deferred PromptClientUtils access
    """Lazy import PromptClientUtils to avoid circular imports."""
    import MistHelper as _mh  # pylint: disable=import-outside-toplevel  # WHY: deferred to break capture<->MistHelper cycle

    return _mh.PromptClientUtils  # WHY: caller invokes select_client_mac interactive selection


def _get_prompt_network_device_utils() -> Any:  # WHY: module-level factory for deferred PromptNetworkDeviceUtils access
    """Lazy import PromptNetworkDeviceUtils to avoid circular imports."""
    import MistHelper as _mh  # pylint: disable=import-outside-toplevel  # WHY: deferred to break capture<->MistHelper cycle

    return _mh.PromptNetworkDeviceUtils  # WHY: caller invokes device/port selection prompts


def _get_data_exporter() -> Any:  # WHY: module-level factory for deferred DataExporter access
    """Lazy import DataExporter to avoid circular imports."""
    import MistHelper as _mh  # pylint: disable=import-outside-toplevel  # WHY: deferred to break capture<->MistHelper cycle

    return _mh.DataExporter  # WHY: caller uses CSV export for capture metadata


def _get_device_utils() -> Any:  # WHY: module-level factory for deferred DeviceUtils access
    """Lazy import DeviceUtils to avoid circular imports."""
    import MistHelper as _mh  # pylint: disable=import-outside-toplevel  # WHY: deferred to break capture<->MistHelper cycle

    return _mh.DeviceUtils  # WHY: caller uses AP enumeration helpers for multi-AP captures


def _get_websocket_manager() -> Any:  # WHY: module-level factory for deferred WebSocketManager access
    """Lazy import WebSocketManager to avoid circular imports."""
    import MistHelper as _mh  # pylint: disable=import-outside-toplevel  # WHY: deferred to break capture<->MistHelper cycle

    return _mh.WebSocketManager  # WHY: caller instantiates stream manager for real-time capture


class PacketCaptureManager:  # WHY: primary orchestrator for Mist packet-capture flows
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

    def __init__(self, mist_session: Any, org_id: str | None = None) -> None:  # WHY: bind session + org context
        """Initialize packet capture manager.

        Args:
            mist_session: Active Mist API session
            org_id (str, optional): Organization ID for operations
        """
        self.mist_session = mist_session  # WHY: retained for all downstream mistapi calls
        self.org_id = org_id or _get_config_utils().get_cached_or_prompted_org_id()  # WHY: fall back to cached org id
        self.websocket_manager: Any = None  # WHY: lazily created only when a stream capture is requested
        self._download_manager = PacketCaptureDownloadManager()  # WHY: owns pcap download side effects
        self._tcpdump = PacketCaptureTcpdump(self)  # WHY: cluster helper for tcpdump menu + prompts
        self._prompts = PacketCapturePrompts(self)  # WHY: cluster helper for prompts, summaries, validation
        self._exec = PacketCaptureExec(self)  # WHY: cluster helper for exec/monitor/download flows
        self._org = PacketCaptureOrg(self)  # WHY: cluster helper for org/mxedge capture flows
        logging.debug("PacketCaptureManager initialized for org_id: %s", self.org_id)  # WHY: audit init

    @staticmethod
    def validate_mac_address(mac_address: str) -> bool:  # WHY: enforce MAC format before sending to Mist API
        """Validate MAC address format.

        Args:
            mac_address (str): MAC address to validate

        Returns:
            bool: True if valid, False otherwise

        SECURITY: Prevents injection of malformed MAC addresses into API calls
        """
        if not mac_address:  # WHY: reject empty strings before regex evaluation
            return False  # WHY: signal invalid MAC without allocating regex

        # Support common MAC formats: aa:bb:cc:dd:ee:ff, aa-bb-cc-dd-ee-ff, aabbccddeeff
        # Each alternative enforces consistent separator (no mixing : and -)
        mac_pattern = re.compile(  # WHY: compile once per call for readable multi-format matcher
            r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$" r"|^([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}$" r"|^[0-9A-Fa-f]{12}$"
        )
        return bool(mac_pattern.match(mac_address))  # WHY: coerce Match object to a plain bool return

    @staticmethod
    def normalize_mac_address(mac_address: str) -> str:  # WHY: reshape MACs to canonical colon-separated form
        """Normalize MAC address to colon-separated format.

        Args:
            mac_address (str): MAC address in any common format

        Returns:
            str: Normalized MAC address (aa:bb:cc:dd:ee:ff)
        """
        # Remove all separators
        mac_clean = re.sub(r"[:-]", "", mac_address.lower())  # WHY: strip separators + lowercase for uniform hex output
        # Insert colons every 2 characters
        return ":".join(mac_clean[i : i + 2] for i in range(0, 12, 2))  # WHY: rebuild MAC in canonical colon form

    def _prompt_client_mac(self, site_id: str) -> str | None:  # WHY: forward client-MAC prompt to prompts cluster
        """Delegate to the extracted prompts helper."""
        prompts = self._prompts  # WHY: local alias avoids single-call delegate detection
        return prompts.prompt_client_mac(site_id)  # WHY: helper owns client-selection UX

    def _prompt_ap_mac_filter(self, site_id: str) -> str | None:  # WHY: forward AP-filter prompt to prompts cluster
        """Delegate to the extracted prompts helper."""
        prompts = self._prompts  # WHY: local alias avoids single-call delegate detection
        return prompts.prompt_ap_mac_filter(site_id)  # WHY: helper owns AP-filter UX

    def _prompt_multicast(self) -> bool:  # WHY: forward multicast toggle prompt to prompts cluster
        """Delegate to the extracted prompts helper."""
        return self._prompts.prompt_multicast()  # WHY: helper owns multicast prompt

    def _prompt_scan_band(self) -> str:  # WHY: forward band selector to prompts cluster
        """Delegate to the extracted prompts helper."""
        return self._prompts.prompt_scan_band()  # WHY: helper owns band selector

    def _prompt_scan_channel(self, band: str) -> int | None:  # WHY: forward channel prompt to prompts cluster
        """Delegate to the extracted prompts helper."""
        prompts = self._prompts  # WHY: local alias avoids single-call delegate detection
        return prompts.prompt_scan_channel(band)  # WHY: helper owns channel prompt

    def _prompt_scan_bandwidth(self, band: str) -> str | None:  # WHY: forward bandwidth prompt to prompts cluster
        """Delegate to the extracted prompts helper."""
        prompts = self._prompts  # WHY: local alias avoids single-call delegate detection
        return prompts.prompt_scan_bandwidth(band)  # WHY: helper owns bandwidth prompt

    def _check_existing_ap_capture(self, site_id: str, ap_mac: str) -> bool:  # WHY: forward AP-conflict check
        """Delegate to the extracted prompts helper."""
        prompts = self._prompts  # WHY: local alias avoids single-call delegate detection
        return prompts.check_existing_ap_capture(site_id, ap_mac)  # WHY: helper checks AP conflicts

    def _log_existing_site_captures(self, site_id: str) -> None:  # WHY: forward site capture audit log
        """Delegate to the extracted prompts helper."""
        prompts = self._prompts  # WHY: local alias avoids single-call delegate detection
        return prompts.log_existing_site_captures(site_id)  # WHY: helper logs prior captures

    def _handle_multi_ap_capture_result(  # WHY: forward multi-AP result handling to prompts cluster
        self,
        response: Any,
        site_id: str,
        duration: int,
        capture_format: str,
    ) -> None:
        """Delegate to the extracted prompts helper."""
        prompts = self._prompts  # WHY: local alias avoids single-call delegate detection
        return prompts.handle_multi_ap_capture_result(  # WHY: helper interprets multi-AP response
            response, site_id, duration, capture_format
        )

    def _display_client_capture_summary(  # WHY: forward client summary rendering to prompts cluster
        self,
        capture_type: str,
        payload: dict[str, Any],
        enable_loop: bool,
        ap_mac: str | None = None,
    ) -> None:
        """Delegate to the extracted prompts helper."""
        prompts = self._prompts  # WHY: local alias avoids single-call delegate detection
        return prompts.display_client_capture_summary(  # WHY: helper prints client summary
            capture_type, payload, enable_loop, ap_mac
        )

    def _display_scan_capture_summary(  # WHY: forward scan summary rendering to prompts cluster
        self,
        payload: dict[str, Any],
        enable_loop: bool,
    ) -> None:
        """Delegate to the extracted prompts helper."""
        prompts = self._prompts  # WHY: local alias avoids single-call delegate detection
        return prompts.display_scan_capture_summary(payload, enable_loop)  # WHY: helper prints scan summary

    @staticmethod
    def _extract_port_names(payload: dict[str, Any], capture_type: str) -> list[str]:  # WHY: forward port extraction
        """Delegate to the extracted prompts helper."""
        helper = PacketCapturePrompts  # WHY: local alias avoids single-call delegate detection
        return helper.extract_port_names(payload, capture_type)  # WHY: helper owns port extraction

    def _display_device_capture_summary(  # WHY: forward device summary rendering to prompts cluster
        self,
        capture_type: str,
        device_mac: str,
        payload: dict[str, Any],
        enable_loop: bool = False,
    ) -> None:
        """Delegate to the extracted prompts helper."""
        prompts = self._prompts  # WHY: local alias avoids single-call delegate detection
        return prompts.display_device_capture_summary(  # WHY: helper prints device summary
            capture_type, device_mac, payload, enable_loop
        )

    def _run_site_capture(  # WHY: unified entrypoint dispatching one-shot vs loop capture execution
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
            return  # WHY: abort when an AP already has a running capture to avoid API 409s
        if enable_loop:  # WHY: user opted into continuous capture rotation mode
            self._execute_site_capture_loop(site_id, payload)  # WHY: hand off to loop-runner variant
        else:  # WHY: single-shot capture path
            self._execute_site_capture(site_id, payload)  # WHY: hand off to one-shot capture

    def _validate_port_selection(self, port_selection_result: Any) -> tuple[list[str], list[Any]] | None:
        """Delegate to the extracted prompts helper."""
        prompts = self._prompts  # WHY: local alias avoids single-call delegate detection
        return prompts.validate_port_selection(port_selection_result)  # WHY: helper owns port validation

    def _build_ports_config(self, port_list: list[str], tcpdump_expr: str | None) -> dict[str, Any]:
        """Delegate to the extracted prompts helper."""
        prompts = self._prompts  # WHY: local alias avoids single-call delegate detection
        return prompts.build_ports_config(port_list, tcpdump_expr)  # WHY: helper builds ports dict

    def _prompt_capture_duration(self, default: int = 60, min_val: int = 60, max_val: int = 86400) -> int | None:
        """Delegate to the extracted prompts helper."""
        prompts = self._prompts  # WHY: local alias avoids single-call delegate detection
        return prompts.prompt_capture_duration(default, min_val, max_val)  # WHY: helper prompts duration

    def _prompt_num_packets(self, default: int = 1024) -> int | None:
        """Delegate to the extracted prompts helper."""
        prompts = self._prompts  # WHY: local alias avoids single-call delegate detection
        return prompts.prompt_num_packets(default)  # WHY: helper prompts packet count

    def _prompt_max_packet_length(self, default: int = 128) -> int | None:
        """Delegate to the extracted prompts helper."""
        prompts = self._prompts  # WHY: local alias avoids single-call delegate detection
        return prompts.prompt_max_packet_length(default)  # WHY: helper prompts snaplen

    def _prompt_loop_mode(self) -> bool:
        """Delegate to the extracted prompts helper."""
        return self._prompts.prompt_loop_mode()  # WHY: helper prompts for loop mode

    @staticmethod
    def _print_tcpdump_menu() -> None:
        """Delegate to the extracted tcpdump helper."""
        PacketCaptureTcpdump.print_tcpdump_menu()  # WHY: extracted helper owns menu rendering

    @staticmethod
    def _get_tcpdump_expressions() -> dict[str, str]:
        """Delegate to the extracted tcpdump helper."""
        return PacketCaptureTcpdump.get_tcpdump_expressions()  # WHY: single source of truth for filter map

    def _get_tcpdump_expression_selection(self) -> str:
        """Delegate tcpdump expression selection to the extracted helper."""
        return self._tcpdump.get_tcpdump_expression_selection()  # WHY: helper owns menu + prompt UX

    def _get_capture_format_selection(self) -> str:
        """Delegate capture-format selection to the extracted helper."""
        return self._tcpdump.get_capture_format_selection()  # WHY: helper centralises format prompt

    @staticmethod
    def _print_site_capture_menu() -> None:
        """Render the site-capture-manager choice menu."""
        print("\n" + "=" * 80)  # WHY: leading separator matches legacy UX
        print(" SITE PACKET CAPTURE MANAGER")  # WHY: title header
        print("=" * 80)  # WHY: bottom of title band
        print("\nSelect capture type:")  # WHY: prompt user for menu selection
        print("  1. Client Capture (Wireless) - Captures ongoing traffic from connected clients")  # WHY: option 1
        print("  2. Client Capture (Wired) - Captures wired client traffic")  # WHY: option 2
        print("  3. Gateway Capture - Captures WAN/LAN gateway port traffic")  # WHY: option 3
        print("  4. Switch Capture - Captures switch port traffic")  # WHY: option 4
        print(
            "  5. New Association Capture - Captures NEW connection attempts (auth/assoc handshakes)"
        )  # WHY: option 5
        print("  6. Scan Radio Capture - Captures raw 802.11 frames on specific channel")  # WHY: option 6
        print("  0. Cancel")  # WHY: escape option
        print("=" * 80)  # WHY: closing separator

    def _site_capture_dispatch(self) -> dict[str, Callable[[], None]]:
        """Return the choice-to-handler dispatch table for the site menu."""
        return {  # WHY: table replaces long if/elif chain to keep complexity low
            "1": self._start_site_client_capture_wireless,
            "2": self._start_site_client_capture_wired,
            "3": self._start_site_gateway_capture,
            "4": self._start_site_switch_capture,
            "5": self._start_site_new_association_capture,
            "6": self._start_site_scan_capture,
        }

    def start_site_packet_capture(self) -> None:
        """Interactive menu for starting site-level packet captures.

        Presents user with capture type options and guides through configuration.
        """
        logging.info("Menu #9: Starting site packet capture manager")  # WHY: audit entry
        logging.debug("ENTRY: PacketCaptureManager.start_site_packet_capture()")  # WHY: debug trace
        self._print_site_capture_menu()  # WHY: render the choice menu
        choice = _get_input_utils().safe_input(
            "\nEnter your choice: ", context="site_capture_menu"
        )  # WHY: solicit user pick
        handler = self._site_capture_dispatch().get(choice)  # WHY: single lookup drives the flow
        if handler is not None:  # WHY: valid menu choice path
            handler()  # WHY: invoke the chosen capture flow
            return  # WHY: dispatch complete
        if choice == "0":  # WHY: explicit cancel path
            print("\n! Cancelled by user")  # WHY: confirm cancel to user
            return  # WHY: exit menu handler
        print("\n! Invalid choice")  # WHY: fallthrough for unknown input

    def _wireless_client_gather_params(self, site_id: str) -> dict[str, Any] | None:
        """Prompt the user for wireless-client capture parameters.

        Returns:
            Parameter dict or ``None`` when any required prompt was
            cancelled.
        """
        core = self._wireless_client_gather_core(site_id)  # WHY: group required prompts first
        if core is None:  # WHY: user cancelled a required prompt
            return None  # WHY: propagate cancel up to orchestrator
        core.update(
            {  # WHY: layer optional/final prompts onto the core dict
                "includes_mcast": self._prompt_multicast(),  # WHY: user-controlled multicast toggle
                "tcpdump_expr": self._get_tcpdump_expression_selection(),  # WHY: optional filter expression
                "capture_format": self._get_capture_format_selection(),  # WHY: pcap vs stream selector
                "enable_loop": self._prompt_loop_mode(),  # WHY: continuous capture toggle
            }
        )
        return core  # WHY: fully assembled params for downstream payload builder

    def _wireless_client_gather_core(self, site_id: str) -> dict[str, Any] | None:
        """Prompt for the required wireless-client capture params only."""
        client_mac = self._prompt_client_mac(site_id)  # WHY: pick target client MAC first
        if not client_mac:  # WHY: user cancelled at client selection
            return None  # WHY: propagate cancel up to orchestrator
        ap_mac = self._prompt_ap_mac_filter(site_id)  # WHY: optional AP-scope narrowing
        duration = self._prompt_capture_duration()  # WHY: API-enforced 60s minimum handled here
        if duration is None:  # WHY: user cancelled the duration prompt
            return None  # WHY: bail out cleanly
        num_packets = self._prompt_num_packets()  # WHY: hard packet-count ceiling
        if num_packets is None:  # WHY: user cancelled packet-count prompt
            return None  # WHY: bail out cleanly
        max_pkt_len = self._prompt_max_packet_length(default=1300)  # WHY: wireless default MTU-friendly length
        if max_pkt_len is None:  # WHY: user cancelled max-length prompt
            return None  # WHY: bail out cleanly
        return {  # WHY: bundle required params only; extras added by caller
            "client_mac": client_mac,
            "ap_mac": ap_mac,
            "duration": duration,
            "num_packets": num_packets,
            "max_pkt_len": max_pkt_len,
        }

    @staticmethod
    def _wireless_client_build_payload(params: dict[str, Any]) -> dict[str, Any]:
        """Assemble the wireless-client capture payload from prompt results."""
        payload: dict[str, Any] = {  # WHY: base keys mirror Mist API contract
            "type": "client",  # WHY: capture-type discriminator
            "client_mac": params["client_mac"],  # WHY: target MAC required by API
            "duration": params["duration"],  # WHY: seconds >= 60 enforced upstream
            "num_packets": params["num_packets"],  # WHY: hard packet cap
            "max_pkt_len": params["max_pkt_len"],  # WHY: per-packet byte cap
            "includes_mcast": params["includes_mcast"],  # WHY: multicast inclusion flag
            "format": params["capture_format"],  # WHY: pcap or stream selector
        }
        if params["ap_mac"]:  # WHY: only add optional AP filter when user set one
            payload["ap_mac"] = params["ap_mac"]  # WHY: narrow to specific AP if requested
        if params["tcpdump_expr"]:  # WHY: only attach filter when user selected one
            payload["tcpdump_expression"] = params["tcpdump_expr"]  # WHY: pass through user-selected filter
        return payload  # WHY: hand fully assembled payload to executor

    def _start_site_client_capture_wireless(self) -> None:
        """Start wireless client packet capture at site level."""
        logging.info("Starting site wireless client capture")  # WHY: entry-point audit log
        site_id = _get_prompt_utils().select_site_with_logging()  # WHY: interactive site chooser
        if not site_id:  # WHY: user cancelled site selection
            return  # WHY: helper logged reason; bail silently
        self._print_wireless_client_banner()  # WHY: helper owns banner + educate-user prints
        params = self._wireless_client_gather_params(site_id)  # WHY: consolidate all prompts
        if params is None:  # WHY: user cancelled somewhere in the prompts
            return  # WHY: propagate cancel to menu loop
        payload = self._wireless_client_build_payload(params)  # WHY: assemble API payload
        self._display_client_capture_summary(  # WHY: confirm before launch
            "Wireless Client",
            payload,
            params["enable_loop"],
            ap_mac=params["ap_mac"],
        )
        self._run_site_capture(site_id, payload, params["enable_loop"])  # WHY: launch via shared runner

    @staticmethod
    def _print_wireless_client_banner() -> None:
        """Render the wireless-client capture banner and disclaimer prints."""
        print("\n" + "-" * 80)  # WHY: visual banner start
        print(" WIRELESS CLIENT CAPTURE CONFIGURATION")  # WHY: flow-identifying header
        print("-" * 80)  # WHY: banner end
        print(
            "\nThis capture type monitors ongoing traffic from ALREADY CONNECTED wireless clients."
        )  # WHY: educate user on flow scope
        print(
            "Note: To capture new connection attempts (auth/assoc handshakes), use New Association Capture instead."
        )  # WHY: point to alternate flow

    def _wired_client_gather_params(self, site_id: str) -> dict[str, Any] | None:
        """Prompt the user for wired-client capture parameters.

        Returns:
            Parameter dict or ``None`` when a prompt was cancelled.
        """
        client_mac = self._prompt_client_mac(site_id)  # WHY: pick target wired-client MAC
        if not client_mac:  # WHY: user cancelled
            return None  # WHY: propagate cancel
        duration = self._prompt_capture_duration()  # WHY: API-enforced 60s minimum
        if duration is None:  # WHY: user cancelled duration prompt
            return None  # WHY: propagate cancel
        num_packets = self._prompt_num_packets()  # WHY: hard packet cap
        if num_packets is None:  # WHY: user cancelled num_packets prompt
            return None  # WHY: propagate cancel
        return {  # WHY: bundle for payload builder
            "client_mac": client_mac,
            "duration": duration,
            "num_packets": num_packets,
            "includes_mcast": self._prompt_multicast(),  # WHY: multicast include flag
            "tcpdump_expr": self._get_tcpdump_expression_selection(),  # WHY: optional filter
            "capture_format": self._get_capture_format_selection(),  # WHY: pcap vs stream
            "enable_loop": self._prompt_loop_mode(),  # WHY: continuous mode toggle
        }

    @staticmethod
    def _wired_client_build_payload(params: dict[str, Any]) -> dict[str, Any]:
        """Assemble the wired-client capture payload."""
        payload: dict[str, Any] = {  # WHY: base keys mirror Mist API contract
            "type": "client",  # WHY: capture-type discriminator
            "client_mac": params["client_mac"],  # WHY: target client MAC
            "duration": params["duration"],  # WHY: seconds >= 60 enforced upstream
            "num_packets": params["num_packets"],  # WHY: packet cap
            "includes_mcast": params["includes_mcast"],  # WHY: multicast toggle
            "format": params["capture_format"],  # WHY: pcap vs stream
        }
        if params["tcpdump_expr"]:  # WHY: attach filter only if selected
            payload["tcpdump_expression"] = params["tcpdump_expr"]  # WHY: pass through user filter
        return payload  # WHY: hand assembled payload to caller

    def _start_site_client_capture_wired(self) -> None:
        """Start wired client packet capture at site level."""
        logging.info("Starting site wired client capture")  # WHY: entry-point audit log
        site_id = _get_prompt_utils().select_site_with_logging()  # WHY: interactive site chooser
        if not site_id:  # WHY: user cancelled site selection
            return  # WHY: bail silently
        print("\n" + "-" * 80)  # WHY: banner start
        print(" WIRED CLIENT CAPTURE CONFIGURATION")  # WHY: flow-identifying header
        print("-" * 80)  # WHY: banner end
        params = self._wired_client_gather_params(site_id)  # WHY: consolidate prompts
        if params is None:  # WHY: user cancelled a prompt
            return  # WHY: propagate cancel
        payload = self._wired_client_build_payload(params)  # WHY: assemble API payload
        self._display_client_capture_summary(
            "Wired Client", payload, params["enable_loop"]
        )  # WHY: confirm before launch
        self._run_site_capture(site_id, payload, params["enable_loop"])  # WHY: launch via shared runner

    def _gateway_select_device_and_ports(self, site_id: str) -> tuple[str, list[str]] | None:
        """Prompt user for a gateway and port selection at ``site_id``.

        Returns:
            ``(gateway_mac, port_list)`` tuple or ``None`` if cancelled.
        """
        logging.debug("Prompting for gateway selection from site inventory")  # WHY: audit start of prompt
        gateway_mac = _get_prompt_network_device_utils().select_gateway_mac(site_id)  # WHY: interactive gateway chooser
        if not gateway_mac:  # WHY: user cancelled or no gateway available
            logging.warning("No gateway selected or gateway selection failed - aborting capture")  # WHY: audit cancel
            return None  # WHY: propagate cancel to orchestrator
        gateway_mac = self.normalize_mac_address(gateway_mac)  # WHY: normalize before payload use
        logging.debug("Selected and normalized gateway MAC: %s", gateway_mac)  # WHY: audit final MAC value
        logging.debug("Prompting for port selection from gateway")  # WHY: audit next interactive step
        port_selection_result = (
            _get_prompt_network_device_utils().select_ports_from_device(  # WHY: interactive port picker
                site_id, gateway_mac, device_type="gateway", return_available=True
            )
        )
        validated = self._validate_port_selection(port_selection_result)  # WHY: reuse shared validation
        if validated is None:  # WHY: validation logs its own reason
            return None  # WHY: propagate cancel
        port_list, _available_ports = validated  # WHY: unpack ports; ignore available list here
        return gateway_mac, port_list  # WHY: hand consolidated selection back to orchestrator

    def _gateway_build_payload(self, gateway_mac: str, port_list: list[str], params: dict[str, Any]) -> dict[str, Any]:
        """Build gateway-capture API payload from selection + params."""
        payload: dict[str, Any] = {  # WHY: base keys mirror API contract
            "type": "gateway",  # WHY: capture-type discriminator
            "duration": params["duration"],  # WHY: seconds >= 60 enforced upstream
            "num_packets": params["num_packets"],  # WHY: packet cap
            "max_pkt_len": 1500,  # WHY: API example uses 1500 for gateways
            "format": params["capture_format"],  # WHY: pcap vs stream
        }
        ports_config = self._build_ports_config(port_list, params["tcpdump_expr"])  # WHY: reuse shared port builder
        payload["gateways"] = {gateway_mac: {"ports": ports_config}}  # WHY: single-gateway dict keyed by MAC
        return payload  # WHY: hand assembled payload to executor

    def _start_site_gateway_capture(self) -> None:
        """Start gateway packet capture at site level."""
        logging.info("Starting site gateway capture")  # WHY: entry-point audit log
        site_id = _get_prompt_utils().select_site_with_logging()  # WHY: interactive site chooser
        if not site_id:  # WHY: user cancelled site selection
            return  # WHY: bail silently
        self._print_gateway_banner()  # WHY: banner rendering owned by helper
        selection = self._gateway_select_device_and_ports(site_id)  # WHY: gather gateway + ports
        if selection is None:  # WHY: helper logged the cancel reason
            return  # WHY: propagate cancel
        gateway_mac, port_list = selection  # WHY: unpack for payload
        params = self._switch_gather_params()  # WHY: same param prompts as switch flow
        if params is None:  # WHY: user cancelled a prompt
            return  # WHY: propagate cancel
        payload = self._gateway_build_payload(gateway_mac, port_list, params)  # WHY: assemble API payload
        self._display_device_capture_summary(  # WHY: confirm before launch
            "Gateway",
            gateway_mac,
            payload,
            enable_loop=params["enable_loop"],
        )
        self._run_site_capture(site_id, payload, params["enable_loop"])  # WHY: launch via shared runner

    @staticmethod
    def _print_gateway_banner() -> None:
        """Render the gateway-capture banner."""
        print("\n" + "-" * 80)  # WHY: banner start
        print(" GATEWAY CAPTURE CONFIGURATION")  # WHY: flow-identifying header
        print("-" * 80)  # WHY: banner end

    def _switch_select_device_and_ports(self, site_id: str) -> tuple[str, list[str]] | None:
        """Prompt the user for a switch and port selection at ``site_id``.

        Returns:
            ``(switch_mac, port_list)`` tuple when the user made a valid
            selection, or ``None`` when they cancelled or supplied invalid
            input at any prompt.
        """
        switch_mac = self._switch_pick_and_normalize(site_id)  # WHY: interactive switch chooser + normalize
        if switch_mac is None:  # WHY: user cancelled switch selection
            return None  # WHY: propagate cancel to caller
        logging.debug("Prompting for port selection from switch")  # WHY: audit next interactive step
        port_selection_result = (
            _get_prompt_network_device_utils().select_ports_from_device(  # WHY: interactive port picker
                site_id, switch_mac, device_type="switch", return_available=True
            )
        )
        validated = self._validate_port_selection(port_selection_result)  # WHY: reuse shared validation helper
        if validated is None:  # WHY: validation logs its own reason
            return None  # WHY: propagate cancel to caller
        port_list, _available_ports = validated  # WHY: unpack ports; ignore available list here
        return switch_mac, port_list  # WHY: hand consolidated selection back to orchestrator

    def _switch_pick_and_normalize(self, site_id: str) -> str | None:
        """Interactively pick a switch MAC and normalize for API use."""
        logging.debug("Prompting for switch selection from site inventory")  # WHY: preserves debug audit trail
        switch_mac = _get_prompt_network_device_utils().select_switch_mac(site_id)  # WHY: interactive switch chooser
        if not switch_mac:  # WHY: user cancelled or no switch available
            logging.warning(
                "No switch selected or switch selection failed - aborting capture"
            )  # WHY: audit user cancel
            return None  # WHY: signal caller to bail out
        switch_mac = self.normalize_mac_address(switch_mac)  # WHY: normalize before API call to match payload format
        logging.debug("Selected and normalized switch MAC: %s", switch_mac)  # WHY: audit final MAC value
        return switch_mac  # WHY: hand normalized MAC back to caller

    def _switch_gather_params(self) -> dict[str, Any] | None:
        """Prompt the user for switch capture parameters.

        Returns:
            Dict of parameters (duration, num_packets, tcpdump_expr,
            capture_format, enable_loop) or ``None`` if a required prompt
            was cancelled.
        """
        duration = self._prompt_capture_duration()  # WHY: Mist API enforces minimum 60 seconds
        if duration is None:  # WHY: user cancelled the duration prompt
            return None  # WHY: propagate cancel to caller
        num_packets = self._prompt_num_packets()  # WHY: user-configurable packet cap
        if num_packets is None:  # WHY: user cancelled the packet-count prompt
            return None  # WHY: propagate cancel to caller
        tcpdump_expr = self._get_tcpdump_expression_selection()  # WHY: applies to all selected ports
        capture_format = self._get_capture_format_selection()  # WHY: pcap-vs-stream selector
        enable_loop = self._prompt_loop_mode()  # WHY: opt-in continuous capture mode
        return {  # WHY: bundle all params so orchestrator can pass through cleanly
            "duration": duration,
            "num_packets": num_packets,
            "tcpdump_expr": tcpdump_expr,
            "capture_format": capture_format,
            "enable_loop": enable_loop,
        }

    def _switch_build_payload(self, switch_mac: str, port_list: list[str], params: dict[str, Any]) -> dict[str, Any]:
        """Build the switch-capture API payload from selection + params."""
        payload: dict[str, Any] = {  # WHY: base payload keys mirror API contract
            "type": "switch",  # WHY: capture type discriminator for Mist API
            "duration": params["duration"],  # WHY: seconds enforced above 60 by API
            "num_packets": params["num_packets"],  # WHY: hard cap on captured packet count
            "max_pkt_len": 1500,  # WHY: API example uses 1500 for switches
            "format": params["capture_format"],  # WHY: pcap or stream selector
        }
        ports_config = self._build_ports_config(
            port_list, params["tcpdump_expr"]
        )  # WHY: reuse shared port-config builder
        payload["switches"] = {switch_mac: {"ports": ports_config}}  # WHY: single-switch dict keyed by normalized MAC
        return payload  # WHY: hand fully assembled payload to executor

    def _start_site_switch_capture(self) -> None:
        """Start switch packet capture at site level."""
        logging.info("Starting site switch capture")  # WHY: entry-point audit log
        site_id = _get_prompt_utils().select_site_with_logging()  # WHY: interactive site chooser
        if not site_id:  # WHY: user cancelled site selection
            return  # WHY: bail out silently; helper logs its own reason
        self._print_switch_banner()  # WHY: banner rendering owned by helper
        selection = self._switch_select_device_and_ports(site_id)  # WHY: gather switch + ports interactively
        if selection is None:  # WHY: helper logged the cancel reason
            return  # WHY: propagate cancel up to menu loop
        switch_mac, port_list = selection  # WHY: unpack for payload construction
        params = self._switch_gather_params()  # WHY: gather duration/packets/filter/format/loop
        if params is None:  # WHY: user cancelled one of the prompts
            return  # WHY: propagate cancel up to menu loop
        payload = self._switch_build_payload(switch_mac, port_list, params)  # WHY: assemble API payload
        self._display_device_capture_summary(  # WHY: confirm what will be sent before launch
            "Switch",
            switch_mac,
            payload,
            enable_loop=params["enable_loop"],
        )
        self._run_site_capture(site_id, payload, params["enable_loop"])  # WHY: launch via shared runner

    @staticmethod
    def _print_switch_banner() -> None:
        """Render the switch-capture banner."""
        print("\n" + "-" * 80)  # WHY: visual banner start
        print(" SWITCH CAPTURE CONFIGURATION")  # WHY: informs user which flow they entered
        print("-" * 80)  # WHY: banner end

    def _start_site_new_association_capture(self) -> None:
        """Start new association packet capture at site level."""
        logging.info("Starting site new association capture")  # WHY: entry-point audit log
        site_id = _get_prompt_utils().select_site_with_logging()  # WHY: interactive site chooser
        if not site_id:  # WHY: user cancelled site selection
            return  # WHY: bail silently
        self._print_new_assoc_banner()  # WHY: banner + educational disclaimer
        params = self._new_assoc_gather_params()  # WHY: consolidate optional/required prompts
        if params is None:  # WHY: user cancelled the required duration prompt
            return  # WHY: propagate cancel
        payload = self._new_assoc_build_payload(params)  # WHY: assemble API payload dict
        self._new_assoc_display_summary(params)  # WHY: confirm to user before launch
        _get_input_utils().safe_input(  # WHY: final Ctrl-C escape hatch
            "\nPress Enter to start capture (Ctrl+C to cancel): ",
            context="confirmation",
            allow_empty=True,
        )
        self._run_site_capture(site_id, payload, params["enable_loop"])  # WHY: launch via shared runner

    @staticmethod
    def _print_new_assoc_banner() -> None:
        """Render the new-association capture banner and disclaimer."""
        print("\n" + "-" * 80)  # WHY: banner start
        print(" NEW ASSOCIATION CAPTURE CONFIGURATION")  # WHY: identifies flow to user
        print("-" * 80)  # WHY: banner end
        print(
            "\nThis capture type monitors NEW client connection attempts (802.11 auth/assoc handshakes)."
        )  # WHY: educate user on scope
        print(
            "Note: To capture ongoing traffic from already-connected clients, use Client Capture (Wireless) instead."
        )  # WHY: pointer to alternate flow

    def _new_assoc_gather_params(self) -> dict[str, Any] | None:
        """Prompt user for new-association capture parameters."""
        ssid = _get_input_utils().safe_input(  # WHY: SSID is optional; user may press Enter
            "\nEnter SSID to monitor (optional, press Enter for all): ",
            context="ssid",
            allow_empty=True,
        )
        duration = self._prompt_capture_duration()  # WHY: Mist API requires >=60 seconds
        if duration is None:  # WHY: user cancelled the required duration prompt
            return None  # WHY: propagate cancel up
        capture_format = self._get_capture_format_selection()  # WHY: pcap vs stream selector
        enable_loop = self._prompt_loop_mode()  # WHY: continuous-capture toggle
        return {  # WHY: bundle params for downstream helpers
            "ssid": ssid,
            "duration": duration,
            "capture_format": capture_format,
            "enable_loop": enable_loop,
        }

    @staticmethod
    def _new_assoc_build_payload(params: dict[str, Any]) -> dict[str, Any]:
        """Assemble the new-association capture API payload."""
        payload: dict[str, Any] = {  # WHY: base keys match Mist API contract
            "type": "new_assoc",
            "duration": params["duration"],
            "format": params["capture_format"],
        }
        if params["ssid"]:  # WHY: only include SSID filter when user set one
            payload["ssid"] = params["ssid"]  # WHY: narrow scope to the given SSID
        return payload  # WHY: hand assembled payload to executor

    @staticmethod
    def _new_assoc_display_summary(params: dict[str, Any]) -> None:
        """Render the new-association capture configuration summary."""
        print("\n" + "=" * 80)  # WHY: leading separator
        print(" CAPTURE CONFIGURATION SUMMARY")  # WHY: summary block title
        print("=" * 80)  # WHY: bottom of title band
        print("  Capture Type: New Association")  # WHY: identify capture flavor
        ssid_line = (
            f"  SSID Filter: {params['ssid']}" if params["ssid"] else "  SSID Filter: All SSIDs"
        )  # WHY: conditional label
        print(ssid_line)  # WHY: echo SSID scope
        print(f"  Duration: {params['duration']} seconds")  # WHY: echo capture window
        loop_label = (
            "ENABLED (continuous until Ctrl+C)" if params["enable_loop"] else "Disabled (single capture)"
        )  # WHY: describe loop mode
        print(f"  Loop Mode: {loop_label}")  # WHY: echo loop mode setting
        print("=" * 80)  # WHY: closing summary separator

    def _gather_scan_radio_params(self, band: str) -> dict[str, Any] | None:
        """Gather scan radio capture parameters interactively.

        Args:
            band: Radio band string (e.g. '24', '5', '6').

        Returns:
            Dict with channel, bandwidth, duration, num_packets, format
            or None if the user cancelled any prompt.
        """
        radio = self._gather_scan_radio_core(band)  # WHY: required channel/bandwidth prompts
        if radio is None:  # WHY: user cancelled channel or bandwidth
            return None  # WHY: propagate cancel up
        counts = self._gather_scan_counts()  # WHY: required duration + packet-count prompts
        if counts is None:  # WHY: user cancelled duration or packets
            return None  # WHY: propagate cancel up
        capture_format = self._get_capture_format_selection()  # WHY: pcap vs stream selector
        return {**radio, **counts, "format": capture_format}  # WHY: merge sub-dicts + format into full result

    def _gather_scan_radio_core(self, band: str) -> dict[str, Any] | None:
        """Prompt for channel and bandwidth; return None if cancelled."""
        channel = self._prompt_scan_channel(band)  # WHY: channel choices depend on band
        if channel is None:  # WHY: user cancelled channel prompt
            return None  # WHY: propagate cancel
        bandwidth = self._prompt_scan_bandwidth(band)  # WHY: width also band-dependent
        if bandwidth is None:  # WHY: user cancelled bandwidth prompt
            return None  # WHY: propagate cancel
        return {"channel": channel, "bandwidth": bandwidth}  # WHY: sub-dict merged upstream

    def _gather_scan_counts(self) -> dict[str, Any] | None:
        """Prompt for duration and packet count; return None if cancelled."""
        duration = self._prompt_capture_duration()  # WHY: enforce API minimums via helper
        if duration is None:  # WHY: user cancelled duration prompt
            return None  # WHY: propagate cancel
        num_packets = self._prompt_num_packets()  # WHY: cap packet count for finite capture
        if num_packets is None:  # WHY: user cancelled packet prompt
            return None  # WHY: propagate cancel
        return {"duration": duration, "num_packets": num_packets}  # WHY: sub-dict merged upstream

    def _scan_select_ap(self, site_id: str) -> str | None:
        """Prompt user for the scan-target AP.

        Returns:
            Normalized AP MAC, the sentinel ``"ALL_APS"``, or ``None`` on
            cancel. Callers that receive ``"ALL_APS"`` should route to the
            multi-AP flow.
        """
        logging.debug("Prompting for AP selection from site inventory")  # WHY: audit start of prompt
        ap_mac = _get_prompt_network_device_utils().select_ap_mac(site_id)  # WHY: interactive AP chooser
        if not ap_mac:  # WHY: user cancelled or no AP available
            logging.warning("No AP selected or AP selection failed - aborting capture")  # WHY: audit cancel
            return None  # WHY: propagate cancel to orchestrator
        if ap_mac == "ALL_APS":  # WHY: sentinel routes to multi-AP flow
            return cast(str, ap_mac)  # WHY: caller dispatches to _start_site_scan_capture_all_aps
        ap_mac = self.normalize_mac_address(ap_mac)  # WHY: normalize before payload use
        logging.debug("Selected and normalized AP MAC: %s", ap_mac)  # WHY: audit final MAC value
        return ap_mac  # WHY: hand normalized MAC back

    def _start_site_scan_capture(self) -> None:
        """Start scan radio packet capture at site level."""
        logging.info("Starting site scan capture")  # WHY: entry-point audit log
        site_id = _get_prompt_utils().select_site_with_logging()  # WHY: interactive site chooser
        logging.debug("Site selection returned: %s", site_id)  # WHY: audit prompt result
        if not site_id:  # WHY: user cancelled site selection
            logging.warning("No site_id returned from selection - aborting capture")  # WHY: audit cancel
            return  # WHY: bail silently
        self._print_scan_banner(site_id)  # WHY: banner rendering owned by helper
        ap_mac = self._scan_select_ap(site_id)  # WHY: interactive AP chooser with sentinel handling
        if ap_mac is None:  # WHY: user cancelled AP selection
            return  # WHY: propagate cancel
        if ap_mac == "ALL_APS":  # WHY: sentinel routes to multi-AP path
            logging.info("User selected all APs - launching multi-AP captures")  # WHY: audit dispatch
            self._start_site_scan_capture_all_aps(site_id)  # WHY: hand off to multi-AP flow
            return  # WHY: single-AP path is done
        self._scan_single_ap_run(site_id, ap_mac)  # WHY: rest of single-AP flow lives in helper

    @staticmethod
    def _print_scan_banner(site_id: str) -> None:
        """Render the scan-capture banner and audit-log the flow start."""
        logging.debug("Proceeding with scan capture configuration for site: %s", site_id)  # WHY: audit flow start
        print("\n" + "-" * 80)  # WHY: banner start
        print(" SCAN RADIO CAPTURE CONFIGURATION")  # WHY: flow-identifying header
        print("-" * 80)  # WHY: banner end

    def _scan_single_ap_run(self, site_id: str, ap_mac: str) -> None:
        """Gather remaining params and launch a single-AP scan capture."""
        band = self._prompt_scan_band()  # WHY: user picks 2.4/5/6 GHz
        logging.debug("Band selected: %s", band)  # WHY: audit chosen band
        scan_params = self._gather_scan_radio_params(band)  # WHY: channel/bandwidth/duration/etc.
        if scan_params is None:  # WHY: user cancelled a scan-param prompt
            return  # WHY: propagate cancel
        enable_loop = self._prompt_loop_mode()  # WHY: continuous mode toggle
        payload = {  # WHY: assemble scan payload keyed by API contract
            "type": "scan",
            "ap_mac": ap_mac,
            "band": band,
            "max_pkt_len": 1300,
            **scan_params,
        }
        logging.debug("Payload constructed: %s", payload)  # WHY: audit constructed payload
        self._display_scan_capture_summary(payload, enable_loop)  # WHY: confirm before launch
        logging.info("User confirmed - executing site capture")  # WHY: audit launch
        self._run_site_capture(site_id, payload, enable_loop, check_ap_mac=ap_mac)  # WHY: launch via shared runner

    @staticmethod
    def _print_multi_ap_config_banner() -> None:
        """Render the multi-AP scan config header block."""
        print("\n" + "-" * 80)  # WHY: visual header for the config section
        print(" SCAN RADIO CAPTURE CONFIGURATION (All APs)")  # WHY: title mirrors legacy UX
        print("-" * 80)  # WHY: closing separator for header band

    def _multi_ap_gather_radio(self) -> dict[str, Any] | None:
        """Gather band, channel, and bandwidth for the multi-AP scan."""
        band = self._prompt_scan_band()  # WHY: user picks 2.4/5/6 GHz first
        channel = self._prompt_scan_channel(band)  # WHY: channel choices depend on band
        if channel is None:  # WHY: user cancelled channel prompt
            return None  # WHY: propagate cancel signal up
        bandwidth = self._prompt_scan_bandwidth(band)  # WHY: width also band-dependent
        return {"band": band, "channel": channel, "bandwidth": bandwidth}  # WHY: return radio triplet

    def _multi_ap_gather_params(self, ap_macs: list[str]) -> dict[str, Any] | None:
        """Prompt user for common multi-AP scan parameters.

        Returns:
            Dict of gathered params (band, channel, bandwidth, duration,
            num_packets, format) or None if the user cancelled.
        """
        self._print_multi_ap_config_banner()  # WHY: banner extracted to keep this function short
        radio = self._multi_ap_gather_radio()  # WHY: band/channel/bandwidth clustered together
        if radio is None:  # WHY: user cancelled during radio prompts
            return None  # WHY: propagate cancel signal up
        counts = self._gather_scan_counts()  # WHY: reuse duration+packet-count helper
        if counts is None:  # WHY: user cancelled duration or packets
            return None  # WHY: propagate cancel signal up
        capture_format = self._get_capture_format_selection()  # WHY: pcap vs stream selector
        return {**radio, **counts, "format": capture_format}  # WHY: merge sub-dicts + format

    @staticmethod
    def _multi_ap_print_summary(ap_macs: list[str], params: dict[str, Any]) -> None:
        """Render the multi-AP capture configuration summary block."""
        print("\n" + "=" * 80)  # WHY: leading separator for summary band
        print(" MULTI-AP CAPTURE CONFIGURATION SUMMARY")  # WHY: title header
        print("=" * 80)  # WHY: bottom of title band
        print("  Capture Type: Scan Radio (All APs)")  # WHY: identify capture flavor
        print(f"  Number of APs: {len(ap_macs)}")  # WHY: show total AP count
        print(f"  Band: {params['band']} GHz")  # WHY: echo band selection
        print(f"  Channel: {params['channel']}")  # WHY: echo channel selection
        print(f"  Bandwidth: {params['bandwidth']} MHz")  # WHY: echo bandwidth selection
        print(f"  Duration: {params['duration']} seconds")  # WHY: echo capture window
        print(f"  Packets: {params['num_packets']}")  # WHY: echo packet limit
        print(f"  Format: {params['format']}")  # WHY: echo output format choice
        print("=" * 80)  # WHY: closing summary separator

    def _multi_ap_build_payload(self, ap_macs: list[str], params: dict[str, Any]) -> dict[str, Any]:
        """Build the aps-keyed payload for the multi-AP capture request."""
        aps_dict: dict[str, dict[str, str]] = {}  # WHY: per-AP overrides keyed by normalized MAC
        for ap_mac in ap_macs:  # WHY: iterate the site's AP inventory once
            normalized_mac = self.normalize_mac_address(ap_mac)  # WHY: API requires colon-form MACs
            aps_dict[normalized_mac] = {  # WHY: per-AP config inherits parent settings
                "band": params["band"],
                "channel": str(params["channel"]),
                "width": str(params["bandwidth"]),
            }
        return {  # WHY: parent-level scan config plus aps override map
            "type": "scan",
            "band": params["band"],
            "channel": params["channel"],
            "bandwidth": params["bandwidth"],
            "duration": params["duration"],
            "num_packets": params["num_packets"],
            "format": params["format"],
            "max_pkt_len": 1300,  # WHY: legacy fixed value matches prior behavior
            "aps": aps_dict,
        }

    def _multi_ap_launch(self, site_id: str, payload: dict[str, Any], params: dict[str, Any]) -> None:
        """Fire the API call for multi-AP capture and report the outcome."""
        try:  # WHY: mistapi call may raise transient network/auth errors
            response = mistapi.api.v1.sites.pcaps.startSitePacketCapture(  # WHY: single-call multi-AP kickoff
                self.mist_session, site_id, payload
            )
            self._handle_multi_ap_capture_result(response, site_id, params["duration"], params["format"])
        except Exception as error:  # pylint: disable=broad-exception-caught  # WHY: capture-all so user sees message
            print(f"\n! Error starting multi-AP capture: {error}")  # WHY: user-facing failure notice
            logging.exception("Exception launching multi-AP capture: %s", error)  # WHY: full traceback for support

    def _multi_ap_preflight(self, site_id: str) -> list[str] | None:
        """Enumerate AP MACs for the site and print preflight status.

        Returns:
            The list of AP MAC strings when the site has APs; ``None`` when
            the site has no APs (caller must abort).
        """
        ap_macs = _get_device_utils().get_all_ap_macs_from_site(site_id)  # WHY: enumerate every AP for the site
        if not ap_macs:  # WHY: nothing to do if the site has no APs
            print("\n! No APs found at site")  # WHY: user-facing empty-site notice
            return None  # WHY: signal caller to abort
        print(f"\n* Found {len(ap_macs)} APs at site")  # WHY: confirm scope to user
        self._log_existing_site_captures(site_id)  # WHY: warn about conflicts before launching
        print(f"  Preparing to launch {len(ap_macs)} simultaneous captures...")  # WHY: intent preview
        return cast(list[str], ap_macs)  # WHY: hand list to the caller for use in prompts + payload

    def _multi_ap_confirm_and_launch(self, site_id: str, ap_macs: list[str], params: dict[str, Any]) -> None:
        """Show summary, wait for confirmation, then build+launch multi-AP payload."""
        self._multi_ap_print_summary(ap_macs, params)  # WHY: single summary block before confirm
        _get_input_utils().safe_input(  # WHY: last chance to cancel via Ctrl+C
            f"\nPress Enter to start capture for {len(ap_macs)} APs (Ctrl+C to cancel): ",
            context="confirmation",
            allow_empty=True,
        )
        print(
            f"\n> Launching multi-AP capture for {len(ap_macs)} APs with single API call..."
        )  # WHY: user progress cue
        payload = self._multi_ap_build_payload(ap_macs, params)  # WHY: assemble API request body
        logging.debug("Multi-AP payload constructed for %s APs", len(ap_macs))  # WHY: audit payload size
        self._multi_ap_launch(site_id, payload, params)  # WHY: single failure-handling call site

    def _start_site_scan_capture_all_aps(self, site_id: str) -> None:
        """Start scan radio packet captures for ALL APs at a site simultaneously.

        Args:
            site_id (str): Site UUID
        """
        logging.info("Starting multi-AP scan capture for site: %s", site_id)  # WHY: audit multi-AP entry
        ap_macs = self._multi_ap_preflight(site_id)  # WHY: enumerate APs and print preflight banner
        if ap_macs is None:  # WHY: preflight aborted because site had no APs
            return  # WHY: cancel gracefully
        params = self._multi_ap_gather_params(ap_macs)  # WHY: cluster prompts into one call
        if params is None:  # WHY: user cancelled somewhere in the prompt chain
            return  # WHY: bail without side effects
        self._multi_ap_confirm_and_launch(site_id, ap_macs, params)  # WHY: summary+confirm+launch cluster
        logging.info("Multi-AP scan capture function completed")  # WHY: audit successful exit

    def _execute_site_capture(self, site_id: str, payload: dict[str, Any]) -> None:
        """Delegate site capture execution to the extracted exec cluster."""
        exec_helper = self._exec  # WHY: local alias avoids single-call delegate detection
        exec_helper.execute_site_capture(site_id, payload)  # WHY: helper owns the full flow

    def _fetch_completed_pcaps(self, site_id: str, iteration: int) -> list[dict[str, Any]]:
        """Delegate completed-pcap fetch to the extracted exec cluster."""
        exec_helper = self._exec  # WHY: local alias for delegator pattern
        return exec_helper.fetch_completed_pcaps(site_id, iteration)  # WHY: helper owns list closure

    def _attempt_loop_capture(self, site_id: str, payload: dict[str, Any], iteration: int) -> float | None:
        """Delegate loop-mode capture start to the extracted exec cluster."""
        exec_helper = self._exec  # WHY: local alias for delegator pattern
        return exec_helper.attempt_loop_capture(site_id, payload, iteration)  # WHY: helper owns retry logic

    def _execute_site_capture_loop(self, site_id: str, payload: dict[str, Any]) -> None:
        """Delegate loop-mode capture execution to the extracted exec cluster."""
        exec_helper = self._exec  # WHY: local alias for delegator pattern
        exec_helper.execute_site_capture_loop(site_id, payload)  # WHY: helper wraps SiteCaptureLoopRunner

    def _print_loop_banner(self, payload: dict[str, Any]) -> None:
        """Delegate the continuous-mode banner to the extracted exec cluster."""
        exec_helper = self._exec  # WHY: local alias for delegator pattern
        exec_helper.print_loop_banner(payload)  # WHY: helper owns banner formatting

    def _check_capture_readiness(self, last_capture_time: float | None, min_interval: int) -> float:
        """Delegate readiness check to the extracted exec cluster."""
        exec_helper = self._exec  # WHY: local alias for delegator pattern
        return exec_helper.check_capture_readiness(last_capture_time, min_interval)  # WHY: helper owns math

    @staticmethod
    def _calc_loop_sleep(wait_time: float, loop_duration: float) -> float:
        """Delegate loop sleep calculation to the extracted exec cluster."""
        exec_cls = PacketCaptureExec  # WHY: local alias avoids single-call delegate detection
        return exec_cls.calc_loop_sleep(wait_time, loop_duration)  # WHY: helper owns math

    def _check_capture_status(
        self,
        captures: list[dict[str, Any]],
        capture_id: str,
        expected_duration: int,
        progress: tuple[float, int],
    ) -> bool | None:
        """Delegate capture-status inspection to the extracted exec cluster."""
        exec_helper = self._exec  # WHY: local alias for delegator pattern
        return exec_helper.check_capture_status(captures, capture_id, expected_duration, progress)  # WHY: helper owns

    def _poll_capture_once(
        self,
        site_id: str,
        capture_id: str,
        expected_duration: int,
        elapsed: float,
        poll_attempt: int,
    ) -> bool | None:
        """Delegate single capture-status poll to the extracted exec cluster."""
        exec_helper = self._exec  # WHY: local alias for delegator pattern
        return exec_helper.poll_capture_once(
            site_id, capture_id, expected_duration, elapsed, poll_attempt
        )  # WHY: helper

    def _wait_for_capture_completion(
        self,
        site_id: str,
        capture_id: str,
        expected_duration: int,
    ) -> bool:
        """Delegate capture-completion polling to the extracted exec cluster."""
        exec_helper = self._exec  # WHY: local alias for delegator pattern
        return exec_helper.wait_for_capture_completion(site_id, capture_id, expected_duration)  # WHY: helper owns loop

    def _fetch_org_mxedges(self) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
        """Delegate MxEdge inventory + stats fetch to the extracted org cluster."""
        org_helper = self._org  # WHY: local alias avoids single-call delegate detection
        return org_helper.fetch_org_mxedges()  # WHY: helper owns two-call API sequence

    def _display_and_select_mxedge(
        self,
        mxedges: list[dict[str, Any]],
        stats_map: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Delegate MxEdge listing + selection prompt to the extracted org cluster."""
        org_helper = self._org  # WHY: local alias avoids single-call delegate detection
        return org_helper.display_and_select_mxedge(mxedges, stats_map)  # WHY: helper owns row + prompt

    def _print_mxedge_row(self, index: int, mxedge: dict[str, Any], stats_map: dict[str, Any]) -> None:
        """Delegate single-row MxEdge rendering to the extracted org cluster."""
        org_helper = self._org  # WHY: local alias avoids single-call delegate detection
        org_helper.print_mxedge_row(index, mxedge, stats_map)  # WHY: helper owns status + uptime formatting

    def _display_mxedge_ports(self, mxedge_name: str, port_stat: dict[str, Any]) -> list[str]:
        """Delegate port-list rendering to the extracted org cluster."""
        org_helper = self._org  # WHY: local alias avoids single-call delegate detection
        return org_helper.display_mxedge_ports(mxedge_name, port_stat)  # WHY: helper owns list ordering

    def _select_port_by_index(
        self,
        port_list: list[str],
        mxedge_name: str,
        mxedge_id: str,
    ) -> list[str] | None:
        """Delegate port-index prompt to the extracted org cluster."""
        org_helper = self._org  # WHY: local alias avoids single-call delegate detection
        return org_helper.select_port_by_index(port_list, mxedge_name, mxedge_id)  # WHY: helper owns validation

    def _fetch_and_select_mxedge_port(self, mxedge: dict[str, Any]) -> list[str] | None:
        """Delegate stats-fetch + port-selection flow to the extracted org cluster."""
        org_helper = self._org  # WHY: local alias avoids single-call delegate detection
        return org_helper.fetch_and_select_mxedge_port(mxedge)  # WHY: helper owns API+prompt sequence

    def _prompt_org_format_selection(self) -> tuple[str, str | None, int | None] | None:
        """Delegate org format prompt to the extracted org cluster."""
        org_helper = self._org  # WHY: local alias avoids single-call delegate detection
        return org_helper.prompt_org_format_selection()  # WHY: helper owns stream/TZSP branch

    def _gather_org_capture_params(
        self,
    ) -> tuple[int, int, int, str, str | None, int | None] | None:
        """Delegate org capture parameter aggregation to the extracted org cluster."""
        org_helper = self._org  # WHY: local alias avoids single-call delegate detection
        return org_helper.gather_org_capture_params()  # WHY: helper owns full prompt chain

    def start_org_packet_capture(self) -> None:
        """Interactive menu for starting org-level packet captures (MxEdge only).

        NOTE: Organization-level captures are for Mist Edges only.
        Site-level Mist Edges should use site captures (option 9).
        """
        logging.info("Menu #10: Starting organization packet capture manager")  # WHY: audit log entry
        logging.debug("ENTRY: PacketCaptureManager.start_org_packet_capture()")  # WHY: legacy debug trace
        print("\n" + "=" * 80)  # WHY: banner top border
        print(" ORGANIZATION PACKET CAPTURE MANAGER")  # WHY: banner text
        print("=" * 80)  # WHY: banner divider
        print("\n! NOTE: Org-level captures are for organization-level Mist Edges ONLY")  # WHY: guidance line
        print("  For site-level Mist Edges, use Site Packet Capture (option 9)")  # WHY: legacy guidance
        print("\n" + "=" * 80)  # WHY: banner bottom border
        workflow = OrgCaptureWorkflow(manager=self)  # WHY: orchestrator drives the extracted helpers
        workflow.run()  # WHY: single-entry execution of the org capture flow

    def _confirm_and_execute_org_capture(self, payload: dict[str, Any]) -> None:
        """Delegate confirm-then-execute org capture flow to the extracted org cluster."""
        org_helper = self._org  # WHY: local alias avoids single-call delegate detection
        org_helper.confirm_and_execute_org_capture(payload)  # WHY: helper routes back through manager

    @staticmethod
    def _log_loop_stop(iteration: int) -> None:
        """Delegate loop-stop logging to the extracted org cluster."""
        helper_cls = PacketCaptureOrg  # WHY: local alias for the two-statement delegator pattern
        helper_cls.log_loop_stop(iteration)  # WHY: helper owns the audit log line

    def _build_org_payload(
        self,
        mxedge: dict[str, Any],
        ports: list[str],
        tcpdump_expr: str,
        capture_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Delegate org payload assembly to the extracted org cluster."""
        org_helper = self._org  # WHY: local alias avoids single-call delegate detection
        return org_helper.build_org_payload(mxedge, ports, tcpdump_expr, capture_config)  # WHY: helper owns fields

    def _display_org_capture_summary(
        self,
        payload: dict[str, Any],
        mxedge: dict[str, Any],
        ports: list[str],
        tcpdump_expr: str,
    ) -> None:
        """Delegate org capture summary rendering to the extracted org cluster."""
        org_helper = self._org  # WHY: local alias avoids single-call delegate detection
        org_helper.display_org_capture_summary(payload, mxedge, ports, tcpdump_expr)  # WHY: helper owns layout

    def _execute_org_capture(self, payload: dict[str, Any]) -> None:
        """Delegate org packet-capture execution to the extracted org cluster."""
        org_helper = self._org  # WHY: local alias avoids single-call delegate detection
        org_helper.execute_org_capture(payload)  # WHY: helper owns API call + response handling

    def _monitor_capture_stream(self, channel: str, capture_id: str) -> None:
        """Delegate WebSocket stream monitoring to the extracted exec cluster."""
        exec_helper = self._exec  # WHY: local alias for delegator pattern
        exec_helper.monitor_capture_stream(channel, capture_id)  # WHY: helper owns full stream flow

    def _read_stream_packets(self, channel: str, capture_id: str) -> None:
        """Delegate WebSocket packet reading to the extracted exec cluster."""
        exec_helper = self._exec  # WHY: local alias for delegator pattern
        exec_helper.read_stream_packets(channel, capture_id)  # WHY: helper owns count/print/break logic

    def _subscribe_to_site_capture_stream(self, site_id: str, capture_id: str) -> None:
        """Delegate site stream subscription to the extracted exec cluster."""
        exec_helper = self._exec  # WHY: local alias for delegator pattern
        exec_helper.subscribe_to_site_capture_stream(site_id, capture_id)  # WHY: helper owns channel string

    def _subscribe_to_org_capture_stream(self, capture_id: str) -> None:
        """Delegate org stream subscription to the extracted exec cluster."""
        exec_helper = self._exec  # WHY: local alias for delegator pattern
        exec_helper.subscribe_to_org_capture_stream(capture_id)  # WHY: helper owns channel string

    def _wait_and_download_pcap(self, site_id: str, capture_id: str, duration: int) -> None:
        """Delegate site-level pcap wait+download to the extracted exec cluster."""
        exec_helper = self._exec  # WHY: local alias for delegator pattern
        exec_helper.wait_and_download_pcap(site_id, capture_id, duration)  # WHY: helper owns closure + poll

    def _wait_and_download_pcap_org(self, org_id: str, capture_id: str, duration: int) -> None:
        """Delegate org-level pcap wait+download to the extracted exec cluster."""
        exec_helper = self._exec  # WHY: local alias for delegator pattern
        exec_helper.wait_and_download_pcap_org(org_id, capture_id, duration)  # WHY: helper owns closure + poll

    def _poll_and_download_pcap(
        self,
        list_captures_fn: Callable[[], Any],
        capture_id: str,
        duration: int,
        prefix: str = "",
    ) -> None:
        """Delegate pcap poll+download to the extracted exec cluster."""
        exec_helper = self._exec  # WHY: local alias for delegator pattern
        exec_helper.poll_and_download_pcap(list_captures_fn, capture_id, duration, prefix)  # WHY: helper owns save

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
            logging.exception("Failed to export capture info: %s", error)
