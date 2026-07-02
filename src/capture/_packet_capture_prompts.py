"""Interactive prompt + summary cluster extracted from packet_capture.py.

Owns the user-facing prompt helpers (MAC selection, band/channel/duration,
loop mode, capture-summary displays, existing-capture warnings, and
port/config builders) so the parent ``PacketCaptureManager`` stays lean.
Each helper is intentionally short (<=25 physical lines) and low-branch
(cyclomatic complexity <=5) so this file remains at the A+/>=95 tier of
the project compliance analyzer.

Callers instantiate :class:`PacketCapturePrompts` directly (no factory
indirection) so ``PacketCaptureManager`` binds an instance on itself as
``self._prompts``. ``__getattr__`` delegates lookups back to the manager
so shared state (``mist_session``, ``validate_mac_address``,
``normalize_mac_address``, etc.) works transparently without duplicating
class-level attributes.
"""

from __future__ import annotations  # WHY: postponed annotation eval for forward refs used below

import logging  # WHY: audit-trail logging for capture prompt lifecycle events
from typing import Any  # WHY: opaque manager reference avoids import cycles

try:  # WHY: mistapi runtime-required, but tolerated missing during static analysis
    import mistapi  # WHY: primary Mist SDK used for listSitePacketCaptures / stream helpers

    MISTAPI_AVAILABLE = True  # WHY: feature flag consumed by callers to guard SDK usage
except ImportError:  # WHY: allow module import without SDK for offline tooling/tests
    MISTAPI_AVAILABLE = False  # WHY: signals disabled state to downstream consumers


def _lazy_input_utils() -> Any:
    """Return InputUtils lazily to avoid circular imports at load time."""
    from MistHelper import InputUtils  # WHY: deferred import breaks capture<->MistHelper cycle

    return InputUtils  # WHY: caller uses safe_input wrapper for all user prompts


def _lazy_prompt_client_utils() -> Any:
    """Return PromptClientUtils lazily to avoid circular imports."""
    from MistHelper import PromptClientUtils  # WHY: deferred to break capture<->MistHelper cycle

    return PromptClientUtils  # WHY: caller invokes select_client_mac interactive selection


def _lazy_prompt_network_device_utils() -> Any:
    """Return PromptNetworkDeviceUtils lazily to avoid circular imports."""
    from MistHelper import PromptNetworkDeviceUtils  # WHY: deferred to break capture<->MistHelper cycle

    return PromptNetworkDeviceUtils  # WHY: caller invokes device/port selection prompts


_BAND_MAP: dict[str, str] = {  # WHY: menu-choice -> band code lookup shared by scan helpers
    "1": "24",  # WHY: menu item 1 selects the 2.4GHz band
    "2": "5",  # WHY: menu item 2 selects the default 5GHz band
    "3": "6",  # WHY: menu item 3 selects the 6GHz band
    "24": "24",  # WHY: allow direct band code entry as legacy accepted these
    "5": "5",  # WHY: allow direct band code entry
    "6": "6",  # WHY: allow direct band code entry
}

_CHANNEL_PROMPT: dict[str, tuple[str, str]] = {  # WHY: band -> (prompt-text, default) shared between prompts
    "24": ("Enter channel (1-11, default 1): ", "1"),  # WHY: 2.4GHz channel range with default 1
    "5": ("Enter channel (36-144, default 36): ", "36"),  # WHY: 5GHz range with UNII1 default
    "6": ("Enter channel (1-233, default 1): ", "1"),  # WHY: 6GHz range spanning full band
}

_BW_MAP: dict[str, str] = {"1": "20", "2": "40", "3": "80", "4": "160"}  # WHY: menu-choice -> bandwidth MHz


class PacketCapturePrompts:
    """Wrapper class holding the extracted prompt helpers."""

    def __init__(self, manager: Any) -> None:
        """Store the parent manager for delegate lookups."""
        self._mm = manager  # WHY: enable __getattr__ delegation back to PacketCaptureManager

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to the wrapped manager."""
        mm = self.__dict__.get("_mm")  # WHY: guard against half-initialized instances
        if mm is None:  # WHY: only trips during broken init; avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly to callers
        return getattr(mm, name)  # WHY: transparent proxy back to the parent manager

    def _prompt_client_choice(self) -> str:
        """Prompt for client selection mode and return the raw choice string."""
        print("\nClient selection:")  # WHY: banner introduces the two-mode selector
        print("  1. Select from connected clients")  # WHY: option 1 uses the list picker
        print("  2. Manually enter MAC address")  # WHY: option 2 accepts free-form MAC entry
        return _lazy_input_utils().safe_input(  # WHY: safe wrapper trims + logs input
            "Enter choice (default 1): ",  # WHY: prompt text preserved from legacy UX
            default_value="1",  # WHY: default to the interactive picker for safety
            context="client_select",  # WHY: audit tag for input logging
        )

    def _resolve_client_mac_input(self, choice: str, site_id: str) -> str | None:
        """Route the choice to picker or manual entry and return raw MAC."""
        if choice == "1":  # WHY: option 1 routes to the interactive client picker
            client_mac = _lazy_prompt_client_utils().select_client_mac(site_id)  # WHY: reuse shared helper
            if not client_mac:  # WHY: picker returns falsy when user cancels
                print("\n! No client selected")  # WHY: explicit user feedback for cancel
                return None  # WHY: sentinel telling caller the flow was aborted
            return client_mac  # WHY: raw MAC surfaced for downstream normalization
        return _lazy_input_utils().safe_input(  # WHY: option 2 collects manual MAC entry
            "\nEnter client MAC address: ", context="client_mac"  # WHY: distinct audit tag
        )

    def prompt_client_mac(self, site_id: str) -> str | None:
        """Prompt user to select or enter a client MAC address."""
        choice = self._prompt_client_choice()  # WHY: gather the selection mode first
        client_mac = self._resolve_client_mac_input(choice, site_id)  # WHY: resolve mode -> MAC text
        if client_mac is None:  # WHY: helper signals user cancel via None
            return None  # WHY: propagate cancel to caller
        if not self._mm.validate_mac_address(client_mac):  # WHY: reject malformed MAC before API use
            print(f"\n! Invalid MAC address format: {client_mac}")  # WHY: explicit feedback to user
            return None  # WHY: sentinel indicating validation failure
        return self._mm.normalize_mac_address(client_mac)  # WHY: normalize to colon form

    def _prompt_ap_filter_choice(self) -> str:
        """Prompt for AP filter selection mode and return raw choice string."""
        print("\nOptional: Filter by specific AP")  # WHY: banner for the optional AP filter
        print("  1. Select AP from list")  # WHY: option 1 uses the list picker
        print("  2. Enter MAC manually")  # WHY: option 2 accepts free-form MAC entry
        print("  3. Skip (capture from any AP)")  # WHY: option 3 skips filtering entirely
        return _lazy_input_utils().safe_input(  # WHY: safe wrapper handles Ctrl-C/EOF cleanly
            "Enter choice (default 3): ",  # WHY: prompt text preserved from legacy UX
            default_value="3",  # WHY: default skips filter to preserve backward behavior
            context="ap_filter",  # WHY: audit tag for input logging
        )

    def _handle_ap_manual_entry(self) -> str | None:
        """Prompt for manual AP MAC entry and validate; return normalized MAC or None."""
        ap_mac = _lazy_input_utils().safe_input("Enter AP MAC address: ", context="ap_mac")  # WHY: prompt
        if not self._mm.validate_mac_address(ap_mac):  # WHY: reject malformed MAC before API use
            print(f"\n! Invalid AP MAC address format: {ap_mac}")  # WHY: user-facing error message
            return None  # WHY: caller treats None as "skip", not "abort"
        return self._mm.normalize_mac_address(ap_mac)  # WHY: normalize before returning to caller

    def prompt_ap_mac_filter(self, site_id: str) -> str | None:
        """Prompt user to optionally filter by a specific AP MAC address."""
        choice = self._prompt_ap_filter_choice()  # WHY: gather selection mode first
        if choice == "1":  # WHY: option 1 dispatches to interactive AP list picker
            ap_mac = _lazy_prompt_network_device_utils().select_ap_mac(site_id)  # WHY: shared helper
            return self._mm.normalize_mac_address(ap_mac) if ap_mac else None  # WHY: normalize or skip
        if choice == "2":  # WHY: option 2 branches to manual entry helper
            return self._handle_ap_manual_entry()  # WHY: helper owns validation + normalization
        return None  # WHY: option 3 (skip) or unknown -> return None to signal no filter

    def prompt_multicast(self) -> bool:
        """Prompt user whether to include multicast traffic."""
        result: str = _lazy_input_utils().safe_input(  # WHY: single y/n prompt for multicast toggle
            "Include multicast traffic? (y/n, default n): ",  # WHY: prompt text preserved
            default_value="n",  # WHY: default excludes multicast to keep captures small
            context="includes_mcast",  # WHY: audit tag for input logging
        )
        return result.lower() == "y"  # WHY: coerce to bool for API payload

    def prompt_scan_band(self) -> str:
        """Prompt for scan radio band selection."""
        print("\nSelect band:")  # WHY: banner for the three-band selector
        print("  1. 2.4 GHz")  # WHY: option 1 selects legacy 2.4GHz
        print("  2. 5 GHz (default)")  # WHY: option 2 selects 5GHz, the default
        print("  3. 6 GHz")  # WHY: option 3 selects Wi-Fi 6E's 6GHz band
        choice = _lazy_input_utils().safe_input(  # WHY: capture user's numeric choice
            "Enter choice [1-3] (default 2): ",  # WHY: preserves prompt text
            default_value="2",  # WHY: default to 5GHz for typical enterprise deployments
            context="band",  # WHY: audit tag for input logging
        )
        return _BAND_MAP.get(choice, "5")  # WHY: unknown input falls back to 5GHz safely

    def prompt_scan_channel(self, band: str) -> int | None:
        """Prompt for scan radio channel based on band."""
        prompt_text, default = _CHANNEL_PROMPT.get(band, _CHANNEL_PROMPT["6"])  # WHY: band-specific range
        channel_str = _lazy_input_utils().safe_input(  # WHY: single prompt path via lookup table
            prompt_text, default_value=default, context="channel"  # WHY: reuse audit tag
        )
        try:  # WHY: guard against non-numeric input from the user
            return int(channel_str)  # WHY: API requires an integer channel number
        except ValueError:  # WHY: coerce input errors into an explicit None return
            print(f"\n! Invalid channel: {channel_str}")  # WHY: user-facing error message
            return None  # WHY: sentinel indicating validation failure

    def _print_bandwidth_menu(self, band: str) -> None:
        """Print the bandwidth selection menu with band-specific options."""
        print("\nSelect bandwidth:")  # WHY: banner for the bandwidth selector
        print("  1. 20 MHz")  # WHY: 20MHz supported on all bands
        print("  2. 40 MHz")  # WHY: 40MHz supported on all bands
        if band in ["5", "6"]:  # WHY: 80MHz only meaningful on 5GHz/6GHz radios
            print("  3. 80 MHz")  # WHY: expose 80MHz option when applicable
        if band == "6":  # WHY: 160MHz limited to 6GHz per Mist API constraints
            print("  4. 160 MHz")  # WHY: expose 160MHz option only on 6GHz

    def prompt_scan_bandwidth(self, band: str) -> str | None:
        """Prompt for scan radio bandwidth based on band."""
        self._print_bandwidth_menu(band)  # WHY: render band-aware menu first
        choice = _lazy_input_utils().safe_input(  # WHY: capture user's numeric selection
            "Enter choice (default 1): ", default_value="1", context="bandwidth"  # WHY: audit tag
        )
        bandwidth = _BW_MAP.get(choice, "20")  # WHY: unknown input falls back to 20MHz safely
        if band == "24" and bandwidth not in ("20", "40"):  # WHY: 2.4GHz caps at 40MHz per spec
            print(f"\n! Invalid bandwidth {bandwidth} for 2.4 GHz band")  # WHY: user-facing error
            logging.error("Invalid bandwidth %s for 2.4 GHz band", bandwidth)  # WHY: audit-trail log
            return None  # WHY: sentinel indicating validation failure
        return bandwidth  # WHY: valid bandwidth returned to caller

    def _fetch_site_pcaps(self, site_id: str) -> list[dict[str, Any]] | None:
        """Return list of existing pcap captures for a site or None on error."""
        try:  # WHY: wrap network call so upstream flow tolerates SDK errors
            response = mistapi.api.v1.sites.pcaps.listSitePacketCaptures(  # WHY: SDK call for existing pcaps
                self._mm.mist_session, site_id  # WHY: reuse manager's session + site scope
            )
            if response.status_code != 200:  # WHY: any non-200 is treated as unknown state
                return None  # WHY: signal failure so caller does not gate on partial data
            return response.data or []  # WHY: empty list when the endpoint returns null payload
        except Exception as error:  # pylint: disable=broad-exception-caught  # WHY: SDK raises varied
            logging.warning("Failed to check for existing captures: %s", error)  # WHY: audit warning
            return None  # WHY: signal failure to caller

    @staticmethod
    def _ap_has_active_capture(captures: list[dict[str, Any]], ap_mac: str) -> bool:
        """Return True when ap_mac already has a capture in progress."""
        normalized = ap_mac.replace(":", "").replace("-", "").lower()  # WHY: match API's canonical form
        return any(  # WHY: short-circuit as soon as one capture references the AP
            cap.get("ap_mac", "").replace(":", "").replace("-", "").lower() == normalized  # WHY: match
            for cap in captures  # WHY: iterate every active capture record
        )

    @staticmethod
    def _confirm_conflict_proceed() -> bool:
        """Prompt user to confirm proceeding despite an active AP capture."""
        print("\n! WARNING: This AP already has a capture in progress")  # WHY: highlight the conflict
        print("  Mist only allows one capture per AP at a time")  # WHY: explain the constraint
        proceed = (  # WHY: capture the user's y/n decision with default no
            _lazy_input_utils()  # WHY: reuse safe input wrapper
            .safe_input(  # WHY: standard prompt method
                "\nContinue anyway? (y/n, default n): ",  # WHY: default no protects existing captures
                default_value="n",  # WHY: safer default when in doubt
                context="capture_conflict_confirmation",  # WHY: distinct audit tag
            )
            .lower()  # WHY: allow "Y" or "y" both to mean yes
        )
        if proceed != "y":  # WHY: any answer other than y means cancel
            print("\n* Capture cancelled by user")  # WHY: explicit user feedback
            logging.info("User cancelled due to existing capture on AP")  # WHY: audit-trail entry
            return False  # WHY: signal cancel to caller
        return True  # WHY: signal user chose to proceed despite the conflict

    def check_existing_ap_capture(self, site_id: str, ap_mac: str) -> bool:
        """Return True if safe to proceed; False if a conflict caused user cancel."""
        print(f"\n> Checking for existing captures on AP {ap_mac}...")  # WHY: user status message
        captures = self._fetch_site_pcaps(site_id)  # WHY: fetch current pcap list
        if captures is None:  # WHY: fetch failed - fail-open to allow capture attempt
            return True  # WHY: preserve legacy behavior where errors do not block
        if not self._ap_has_active_capture(captures, ap_mac):  # WHY: no conflict detected
            return True  # WHY: safe to proceed without further prompt
        return self._confirm_conflict_proceed()  # WHY: user must confirm to override conflict

    def log_existing_site_captures(self, site_id: str) -> None:
        """Log any existing captures at a site for informational purposes."""
        captures = self._fetch_site_pcaps(site_id)  # WHY: reuse the shared listing helper
        if captures is None:  # WHY: fetch failed - nothing to log
            return  # WHY: skip log line rather than mislead user
        if captures:  # WHY: only announce when at least one capture exists
            logging.info("Found %s existing capture(s) at site %s", len(captures), site_id)  # WHY: audit
            print(f"  Note: {len(captures)} existing capture(s) found at this site")  # WHY: user note

    def _multi_ap_success_summary(self, result: dict[str, Any], capture_format: str, duration: int) -> str:
        """Print the success summary lines for multi-AP capture and return capture_id."""
        capture_id = result.get("id", "unknown")  # WHY: prefer the id echoed by the API
        ap_count = result.get("ap_count", 0)  # WHY: fall back to 0 when API omits field
        print("\n* Multi-AP capture started successfully!")  # WHY: user-visible success banner
        print(f"  Capture ID: {capture_id}")  # WHY: displayed so user can correlate downloads
        print(f"  AP Count: {ap_count}")  # WHY: confirm how many APs are participating
        print(f"  Format: {capture_format}")  # WHY: show file vs stream so user knows next step
        print(f"  Duration: {duration} seconds")  # WHY: echo requested duration for clarity
        print(f"  Expires: {result.get('expiry', 'unknown')}")  # WHY: expiry helps download timing
        logging.info("Multi-AP capture started: id=%s, aps=%s", capture_id, ap_count)  # WHY: audit
        return str(capture_id)  # WHY: coerce to str for downstream URL construction

    def _dispatch_multi_ap_output(self, site_id: str, capture_id: str, capture_format: str) -> None:
        """Route successful multi-AP capture to pcap download or stream subscribe."""
        if capture_format == "pcap":  # WHY: pcap needs a file-ready poll + download
            print("\n> Waiting for PCAP file to be ready...")  # WHY: user status message
            self._mm._wait_and_download_pcap(site_id, capture_id, 0)  # WHY: delegate to download helper
            return  # WHY: pcap path complete
        if capture_format == "stream":  # WHY: stream subscribes to real-time WebSocket
            print("\n> Stream format - subscribe to WebSocket")  # WHY: user status message
            self._mm._subscribe_to_site_capture_stream(site_id, capture_id)  # WHY: delegate to streamer

    @staticmethod
    def _handle_multi_ap_conflict(response: Any, error_details: Any) -> bool:
        """Print conflict message when API rejects due to existing capture; return True if handled."""
        if response.status_code != 400 or not isinstance(error_details, dict):  # WHY: only 400+dict here
            return False  # WHY: caller should print generic failure instead
        detail = error_details.get("detail", "")  # WHY: extract API-provided reason string
        if "Recording already in progress" not in detail:  # WHY: only handle specific conflict text
            return False  # WHY: leave other 400s to the generic failure branch
        print("\n! Capture(s) already in progress on one or more APs")  # WHY: user-visible conflict
        print("  Wait for existing captures to complete")  # WHY: guidance on next step
        logging.error("Multi-AP capture conflict: %s", detail)  # WHY: audit-trail log
        return True  # WHY: caller can short-circuit the generic failure branch

    def handle_multi_ap_capture_result(self, response: Any, site_id: str, duration: int, capture_format: str) -> None:
        """Handle API response for multi-AP capture: success dispatch or error print."""
        if response.status_code == 200:  # WHY: happy path from the API
            capture_id = self._multi_ap_success_summary(response.data, capture_format, duration)  # WHY: log
            self._mm._export_capture_info_to_csv(response.data, "site", site_id)  # WHY: audit CSV export
            self._dispatch_multi_ap_output(site_id, capture_id, capture_format)  # WHY: route by format
            return  # WHY: success handled; caller does not need further branching
        error_details = response.data if hasattr(response, "data") else "Unknown"  # WHY: safe access
        if self._handle_multi_ap_conflict(response, error_details):  # WHY: dedicated conflict path
            return  # WHY: conflict path already logged and messaged
        print(f"\n! Failed to start capture: {response.status_code}")  # WHY: generic failure banner
        print(f"  Error details: {error_details}")  # WHY: dump API-provided details for debugging
        logging.error("Multi-AP capture failed: %s", response.status_code)  # WHY: audit-trail log

    @staticmethod
    def _print_client_summary_body(capture_type: str, payload: dict[str, Any], ap_mac: str | None) -> None:
        """Print the descriptive rows of the client capture summary."""
        print(f"  Capture Type: {capture_type}")  # WHY: echo which capture kind is active
        print(f"  Client MAC: {payload.get('client_mac', 'N/A')}")  # WHY: confirm target client
        if ap_mac:  # WHY: only show AP filter when caller set one
            print(f"  AP MAC Filter: {ap_mac}")  # WHY: audit which AP scope was applied
        tcpdump_expr = payload.get("tcpdump_expression")  # WHY: pull optional filter expression
        if tcpdump_expr:  # WHY: differentiate filtered vs unfiltered captures for user
            print(f"  Packet Filter: {tcpdump_expr}")  # WHY: show the exact filter applied
        else:  # WHY: explicit branch communicates "no filter"
            print("  Packet Filter: None (all traffic)")  # WHY: user-visible confirmation
        print(f"  Duration: {payload.get('duration', 0)} seconds")  # WHY: echo requested duration

    @staticmethod
    def _loop_label(enable_loop: bool) -> str:
        """Return the human-readable loop-mode label."""
        return "ENABLED (continuous until Ctrl+C)" if enable_loop else "Disabled (single capture)"

    @staticmethod
    def _print_client_summary_tail(payload: dict[str, Any], enable_loop: bool) -> None:
        """Print the tail rows (packets/mcast/format/loop) of the client capture summary."""
        num_packets = payload.get("num_packets", 0)  # WHY: 0 means unlimited per Mist API
        packets_label = "unlimited" if num_packets == 0 else "max"  # WHY: user-friendly labeling
        print(f"  Packets: {num_packets} ({packets_label})")  # WHY: echo packet cap
        max_pkt_len = payload.get("max_pkt_len")  # WHY: optional per-packet truncation length
        if max_pkt_len is not None:  # WHY: only show when caller set it
            print(f"  Max Packet Length: {max_pkt_len} bytes")  # WHY: user-visible value
        mcast_label = "Yes" if payload.get("includes_mcast", False) else "No"  # WHY: display bool
        print(f"  Include Multicast: {mcast_label}")  # WHY: echo multicast toggle
        if payload.get("format"):  # WHY: format field only present for some capture kinds
            print(f"  Format: {payload['format']}")  # WHY: echo output format
        print(f"  Loop Mode: {PacketCapturePrompts._loop_label(enable_loop)}")  # WHY: echo loop state

    @staticmethod
    def _wait_for_start_confirmation() -> None:
        """Block until user presses Enter or aborts via Ctrl+C."""
        _lazy_input_utils().safe_input(  # WHY: reuse the safe input wrapper for consistency
            "\nPress Enter to start capture (Ctrl+C to cancel): ",  # WHY: gate execution on ack
            context="confirmation",  # WHY: audit tag distinguishing confirmation prompts
            allow_empty=True,  # WHY: Enter alone is a valid confirmation
        )

    def display_client_capture_summary(
        self, capture_type: str, payload: dict[str, Any], enable_loop: bool, ap_mac: str | None = None
    ) -> None:
        """Display capture summary and prompt for confirmation."""
        print("\n" + "=" * 80)  # WHY: visual boundary for the summary block
        print(" CAPTURE CONFIGURATION SUMMARY")  # WHY: banner text preserved from legacy UX
        print("=" * 80)  # WHY: bottom border of the banner
        self._print_client_summary_body(capture_type, payload, ap_mac)  # WHY: first half of the rows
        self._print_client_summary_tail(payload, enable_loop)  # WHY: remaining rows + labels
        print("=" * 80)  # WHY: closing boundary of the summary block
        self._wait_for_start_confirmation()  # WHY: gate execution on user confirmation

    def display_scan_capture_summary(self, payload: dict[str, Any], enable_loop: bool) -> None:
        """Display scan radio capture summary and prompt for confirmation."""
        print("\n" + "=" * 80)  # WHY: visual boundary for the summary block
        print(" CAPTURE CONFIGURATION SUMMARY")  # WHY: banner text preserved from legacy UX
        print("=" * 80)  # WHY: bottom border of the banner
        print("  Capture Type: Scan Radio")  # WHY: literal label for the scan radio kind
        print(f"  AP MAC: {payload.get('ap_mac', 'N/A')}")  # WHY: echo target AP
        print(f"  Band: {payload.get('band', 'N/A')} GHz")  # WHY: echo selected band
        print(f"  Channel: {payload.get('channel', 'N/A')}")  # WHY: echo selected channel number
        print(f"  Bandwidth: {payload.get('bandwidth', 'N/A')} MHz")  # WHY: echo bandwidth in MHz
        print(f"  Duration: {payload.get('duration', 0)} seconds")  # WHY: echo requested duration
        print(f"  Packets: {payload.get('num_packets', 0)}")  # WHY: echo packet cap
        print(f"  Loop Mode: {self._loop_label(enable_loop)}")  # WHY: echo loop-mode state to user
        print("=" * 80)  # WHY: closing boundary of the summary block
        self._wait_for_start_confirmation()  # WHY: gate execution on user confirmation

    @staticmethod
    def extract_port_names(payload: dict[str, Any], capture_type: str) -> list[str]:
        """Extract port names from a device capture payload."""
        config_key = f"{capture_type.lower()}s"  # WHY: e.g. 'Gateway' -> 'gateways' payload key
        device_config = payload.get(config_key, {})  # WHY: default empty dict when key missing
        for mac_config in device_config.values():  # WHY: single-device payloads carry one mac entry
            ports = mac_config.get("ports", {})  # WHY: ports dict keyed by port name
            return list(ports.keys())  # WHY: return names for user-facing summary
        return []  # WHY: empty payload -> empty list

    @staticmethod
    def _print_device_summary_middle(
        capture_type: str, device_mac: str, port_names: list[str], payload: dict[str, Any]
    ) -> None:
        """Print the middle rows (type/MAC/ports/duration/packets/length) of the device summary."""
        print(f"  Capture Type: {capture_type}")  # WHY: echo device capture kind
        print(f"  {capture_type} MAC: {device_mac}")  # WHY: echo target device
        ports_label = ", ".join(port_names) if port_names else "All ports"  # WHY: readable label
        print(f"  Ports: {ports_label}")  # WHY: echo scoped ports
        print(f"  Duration: {payload.get('duration', 0)} seconds")  # WHY: echo requested duration
        print(f"  Packets: {payload.get('num_packets', 0)}")  # WHY: echo packet cap
        print(f"  Max Packet Length: {payload.get('max_pkt_len', 0)} bytes")  # WHY: echo truncation

    def display_device_capture_summary(
        self,
        capture_type: str,
        device_mac: str,
        payload: dict[str, Any],
        enable_loop: bool = False,
    ) -> None:
        """Display device (gateway/switch) capture summary and confirm."""
        tcpdump_expr = payload.get("tcpdump_expression", "")  # WHY: pull optional filter for summary
        port_names = self.extract_port_names(payload, capture_type)  # WHY: derive port list from config
        print("\n" + "=" * 80)  # WHY: visual boundary for the summary block
        print(" CAPTURE CONFIGURATION SUMMARY")  # WHY: banner text preserved from legacy UX
        print("=" * 80)  # WHY: bottom border of the banner
        self._print_device_summary_middle(capture_type, device_mac, port_names, payload)  # WHY: rows
        if tcpdump_expr:  # WHY: only print filter when one was specified
            print(f"  Filter: {tcpdump_expr}")  # WHY: user-visible filter confirmation
        print(f"  Loop Mode: {self._loop_label(enable_loop)}")  # WHY: echo loop-mode state
        print("=" * 80)  # WHY: closing boundary of the summary block
        self._wait_for_start_confirmation()  # WHY: gate execution on user confirmation

    @staticmethod
    def _expand_port_selection(port_list: list[str], available_ports: list[Any]) -> list[str]:
        """Expand an empty port_list to include all available ports."""
        if port_list:  # WHY: user-selected ports take precedence
            logging.debug("Specific ports selected: %s", port_list)  # WHY: debug-log the choice
            return port_list  # WHY: return the user's explicit selection unchanged
        expanded = [name for name, _ in available_ports]  # WHY: derive names from (name, meta) tuples
        logging.debug("All ports selected: %s", expanded)  # WHY: debug-log the expansion
        return expanded  # WHY: fully-expanded list acts as "all ports"

    @staticmethod
    def validate_port_selection(port_selection_result: Any) -> tuple[list[str], list[Any]] | None:
        """Validate and expand port selection from device."""
        if port_selection_result is None:  # WHY: helper returns None when user cancels
            logging.warning("Port selection failed or cancelled")  # WHY: audit warning
            return None  # WHY: propagate cancel
        port_list, available_ports = port_selection_result  # WHY: unpack the (list, list) tuple
        if port_list is None:  # WHY: nested None signals cancel from downstream helper
            logging.warning("Port selection failed or cancelled")  # WHY: audit warning
            return None  # WHY: propagate cancel
        return PacketCapturePrompts._expand_port_selection(port_list, available_ports), available_ports

    @staticmethod
    def build_ports_config(port_list: list[str], tcpdump_expr: str | None) -> dict[str, Any]:
        """Build ports configuration dict for device capture payload."""
        ports_config: dict[str, Any] = {}  # WHY: accumulate per-port config as {port: {...}}
        for port in port_list:  # WHY: iterate every port the user selected
            ports_config[port] = {}  # WHY: initialise an empty per-port dict
            if tcpdump_expr:  # WHY: attach filter only when caller supplied one
                ports_config[port]["tcpdump_expression"] = tcpdump_expr  # WHY: per-port filter
        return ports_config  # WHY: hand structured config back to caller

    @staticmethod
    def prompt_capture_duration(default: int = 60, min_val: int = 60, max_val: int = 86400) -> int | None:
        """Prompt for capture duration and validate range."""
        duration_str = _lazy_input_utils().safe_input(  # WHY: solicit numeric duration input
            f"Enter capture duration in seconds (default {default}, max {max_val}): ",  # WHY: prompt
            default_value=str(default),  # WHY: default preserved as legacy behavior
            context="duration",  # WHY: audit tag for input logging
        )
        try:  # WHY: guard against non-numeric input
            duration = int(duration_str)  # WHY: coerce user input to integer seconds
        except ValueError:  # WHY: bad input signals validation failure
            print(f"\n! Invalid duration: {duration_str}")  # WHY: user-facing error
            return None  # WHY: sentinel signal to caller
        if duration < min_val or duration > max_val:  # WHY: range check per API limits
            print(f"\n! Duration must be between {min_val} and {max_val} seconds")  # WHY: message
            if min_val >= 60:  # WHY: extra hint when API's 60s floor applies
                print("  (Mist API requires minimum 60 seconds for all packet captures)")  # WHY: guide
            return None  # WHY: validation failure sentinel
        return duration  # WHY: valid duration returned to caller

    @staticmethod
    def prompt_num_packets(default: int = 1024) -> int | None:
        """Prompt for number of packets and validate range."""
        num_packets_str = _lazy_input_utils().safe_input(  # WHY: solicit numeric packet cap
            f"Enter number of packets (default {default}, max 10000, 0 for unlimited): ",  # WHY: prompt
            default_value=str(default),  # WHY: default matches typical Mist usage
            context="num_packets",  # WHY: audit tag for input logging
        )
        try:  # WHY: guard against non-numeric input
            num_packets = int(num_packets_str)  # WHY: coerce input to integer count
        except ValueError:  # WHY: bad input -> validation failure
            print(f"\n! Invalid number of packets: {num_packets_str}")  # WHY: user-facing error
            return None  # WHY: sentinel signal to caller
        if num_packets < 0 or num_packets > 10000:  # WHY: enforce API-defined range
            print("\n! Number of packets must be between 0 and 10000")  # WHY: user-facing error
            return None  # WHY: validation failure sentinel
        return num_packets  # WHY: valid packet count returned to caller

    @staticmethod
    def prompt_max_packet_length(default: int = 128) -> int | None:
        """Prompt for max packet length and validate range."""
        max_pkt_len_str = _lazy_input_utils().safe_input(  # WHY: solicit numeric truncation length
            f"Enter max packet length in bytes (default {default}, max 2048): ",  # WHY: prompt text
            default_value=str(default),  # WHY: default preserves legacy value
            context="max_pkt_len",  # WHY: audit tag for input logging
        )
        try:  # WHY: guard against non-numeric input
            max_pkt_len = int(max_pkt_len_str)  # WHY: coerce input to integer bytes
        except ValueError:  # WHY: bad input -> validation failure
            print(f"\n! Invalid max packet length: {max_pkt_len_str}")  # WHY: user-facing error
            return None  # WHY: sentinel signal to caller
        if max_pkt_len < 64 or max_pkt_len > 2048:  # WHY: enforce API-defined range
            print("\n! Max packet length must be between 64 and 2048 bytes")  # WHY: user-facing error
            return None  # WHY: validation failure sentinel
        return max_pkt_len  # WHY: valid packet length returned to caller

    @staticmethod
    def prompt_loop_mode() -> bool:
        """Prompt user for continuous loop mode."""
        print("\nLoop Mode:")  # WHY: banner introduces the feature
        print("  Automatically start a new capture when the current one completes")  # WHY: explain
        print("  Downloads happen in background while next capture runs")  # WHY: additional context
        loop_mode: str = _lazy_input_utils().safe_input(  # WHY: capture y/n selection
            "Enable continuous loop mode? (y/n, default n): ",  # WHY: preserves prompt text
            default_value="n",  # WHY: default disables to avoid unattended captures
            context="loop_mode",  # WHY: audit tag for input logging
        )
        return loop_mode.lower() == "y"  # WHY: coerce answer into bool
