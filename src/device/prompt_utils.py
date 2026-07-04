"""PromptNetworkDeviceUtils -- Interactive network device selection prompts.

Extracted from MistHelper.py to src/device/prompt_utils.py as part of
Wave 2 systematic decomposition (issue #332).

Provides interactive user prompts for selecting APs, gateways, and switches
from a Mist site, and for choosing ports from a selected device.

NOC Engineer Note: Every method logs clearly before and after each operation
so operators can trace exactly what happened during any run.
"""

from __future__ import annotations  # WHY: enable PEP 604 union syntax on Python 3.10+

import logging  # WHY: standard logging for all progress and error messages
import re  # WHY: regular expressions drive natural port-name sorting
from dataclasses import dataclass  # WHY: bundle port-prompt parameters to keep call arity low
from typing import Any, cast  # WHY: Any for heterogeneous dicts, cast to narrow API return types

import mistapi.api.v1.sites.devices  # WHY: Mist Sites Devices API for listing APs/gateways/switches
import mistapi.api.v1.sites.stats  # WHY: Mist Sites Stats API for per-port status info
from prettytable import PrettyTable  # WHY: tabular display for device and port selection lists

_MAX_PORTS_PER_CAPTURE = 6  # WHY: Mist API hard cap on concurrent packet-capture ports

# WHY: Junos management/loopback/service interfaces are never valid capture targets.
_MANAGEMENT_PORT_PREFIXES: tuple[str, ...] = (
    "fxp",  # WHY: Junos front-panel management interface
    "em",  # WHY: embedded management ethernet
    "me",  # WHY: management ethernet on legacy platforms
    "vme",  # WHY: virtual management ethernet
    "irb",  # WHY: integrated routing/bridging virtual interface
    "lo",  # WHY: loopback interface
    "vlan",  # WHY: VLAN routing interface
    "bme",  # WHY: broadband management ethernet
    "cbp",  # WHY: customer backbone port -- internal Junos construct
    "jsrv",  # WHY: internal Junos services interface
    "pip",  # WHY: internal Junos platform interconnect
)

_DEVICE_TABLE_FIELDS: list[str] = ["Index", "Name", "MAC", "Model", "Status"]  # WHY: shared header set

# WHY: port table columns kept short so line stays within 120-char limit with inline comment.
_PORT_TABLE_FIELDS = ["Index", "Port Name", "Status", "Speed", "Duplex", "Profile", "Description"]  # WHY: header

PortSelectionResult = list[str] | tuple[list[str], list[tuple[str, Any]]] | None  # WHY: return type union


def _natural_sort_key(port_tuple: tuple[str, Any]) -> list[Any]:  # WHY: natural sort by digit runs
    """Split a port name on digit runs for natural (human) sort order.

    Enables 'ge-0/0/9' to sort before 'ge-0/0/10' rather than lexicographically
    after it, which is the ordering operators expect when scanning ports.
    """
    parts = re.split(r"(\d+)", port_tuple[0])  # WHY: partition into text/digit segments
    return [int(part) if part.isdigit() else part for part in parts]  # WHY: numeric segments compare as ints


def _normalize_mac(mac: str) -> str:  # WHY: strip separators + lowercase so any MAC format compares equal
    """Strip separators and lowercase a MAC address so any format compares equal."""
    return str(mac).replace(":", "").replace("-", "").lower()  # WHY: colons/hyphens must not affect equality


def _is_management_port(port_name: str) -> bool:  # WHY: filter out non-capturable service interfaces
    """Return True when the port name starts with a management/service prefix."""
    return any(port_name.startswith(prefix) for prefix in _MANAGEMENT_PORT_PREFIXES)  # WHY: prefix match


@dataclass(frozen=True)
class _PortPromptRequest:  # WHY: bundle prompt inputs to keep _prompt_port_selection signature narrow
    """Bundled arguments for _prompt_port_selection.

    Grouping these six related fields into a single value keeps the interactive
    prompt method's parameter list within project style limits without losing
    any of the context it needs to render the selection UI.
    """

    available_ports: list[tuple[str, Any]]  # WHY: filtered UP ports to render as choices
    port_to_config: dict[str, Any]  # WHY: per-port config for profile/description columns
    device_mac: str  # WHY: shown in the prompt header for operator confirmation
    device_name: str  # WHY: shown in the prompt header for operator confirmation
    device_type: str  # WHY: distinguishes 'SWITCH' vs 'GATEWAY' in the header
    return_available: bool  # WHY: caller controls the shape of the returned value


class PromptNetworkDeviceUtils:  # WHY: interactive Mist device and port selection prompts
    """Interactive prompts for selecting network devices and ports from a Mist site.

    Extracted from MistHelper.py PromptNetworkDeviceUtils to allow constructor
    injection of runtime dependencies (API session and helper callables) so
    the class can be tested and reused without relying on module-level globals.

    Usage:
        _prompt_utils = PromptNetworkDeviceUtils(
            apisession=session,
            safe_input_fn=InputUtils.safe_input,
            expand_port_range_fn=DeviceUtils.expand_port_range_string,
        )
        ap_mac = _prompt_utils.select_ap_mac(site_id)
    """

    def __init__(self, apisession: Any, safe_input_fn: Any, expand_port_range_fn: Any) -> None:  # WHY: DI ctor
        """Initialise with injected runtime dependencies.

        Args:
            apisession: Active mistapi session object used for all API calls.
            safe_input_fn: Callable matching InputUtils.safe_input signature
                           for all interactive user prompts.
            expand_port_range_fn: Callable matching DeviceUtils.expand_port_range_string
                                  that expands a port range key like 'ge-0/0/0-5'
                                  into a list of individual port name strings.
        """
        self._session = apisession  # WHY: Mist API session injected at construction time
        self._safe_input = safe_input_fn  # WHY: input helper injected to avoid global dependency
        self._expand_port_range = expand_port_range_fn  # WHY: port range expander injected at construction

    # ------------------------------------------------------------------
    # Public device-selection helpers
    # ------------------------------------------------------------------

    def select_ap_mac(self, site_id: str) -> str | None:  # WHY: interactive AP MAC selection entry point
        """Prompt the user to choose an AP from a site and return its MAC address.

        Returns the chosen MAC, the special sentinel "ALL_APS" when the user
        opts to capture on every AP, or None on cancel/failure.
        """
        devices = self._fetch_and_sort_devices(site_id, "ap", "APs")  # WHY: fetch and sort or bail
        if devices is None:  # WHY: empty inventory or API failure -- nothing to prompt for
            return None  # WHY: propagate no-result up so caller can abort the flow
        index_map = self._render_device_selection(devices, "SELECT ACCESS POINT")  # WHY: draw table
        print("\nSpecial options:")  # WHY: signal below is AP-specific
        print("  'all' - Select all APs (launches simultaneous captures)")  # WHY: only APs support 'all'
        user_input = self._safe_input(  # WHY: injected input helper handles EOF consistently
            "\nEnter the index number of the AP or 'all': ", context="ap_selection"
        ).strip()
        logging.debug("User input for AP selection: %s", user_input)  # WHY: log raw input for diagnostics
        if user_input.lower() == "all":  # WHY: sentinel path -- capture on every AP simultaneously
            print(f"\n! Selected: All APs ({len(devices)} APs)")  # WHY: confirm to operator
            logging.info("User selected all APs: %d APs", len(devices))  # WHY: audit aggregate selection
            return "ALL_APS"  # WHY: caller checks for this string to enter multi-AP mode
        return self._resolve_mac_choice(user_input, index_map, "AP")  # WHY: single-index resolution

    def select_gateway_mac(self, site_id: str) -> str | None:  # WHY: interactive gateway MAC selection
        """Prompt the user to choose a gateway from a site and return its MAC address.

        Returns the chosen MAC, or None on cancel/failure.
        """
        devices = self._fetch_and_sort_devices(site_id, "gateway", "gateways")  # WHY: fetch or bail
        if devices is None:  # WHY: empty inventory or API failure -- nothing to prompt for
            return None  # WHY: propagate no-result up so caller can abort the flow
        index_map = self._render_device_selection(devices, "SELECT GATEWAY")  # WHY: draw selection table
        user_input = self._safe_input(  # WHY: injected input helper handles EOF consistently
            "\nEnter the index number of the gateway: ", context="gateway_selection"
        ).strip()
        logging.debug("User input for gateway selection: %s", user_input)  # WHY: raw input for diagnostics
        return self._resolve_mac_choice(user_input, index_map, "gateway")  # WHY: single-index resolution

    def select_switch_mac(self, site_id: str) -> str | None:  # WHY: interactive switch MAC selection
        """Prompt the user to choose a switch from a site and return its MAC address.

        Returns the chosen MAC, or None on cancel/failure.
        """
        devices = self._fetch_and_sort_devices(site_id, "switch", "switches")  # WHY: fetch or bail
        if devices is None:  # WHY: empty inventory or API failure -- nothing to prompt for
            return None  # WHY: propagate no-result up so caller can abort the flow
        index_map = self._render_device_selection(devices, "SELECT SWITCH")  # WHY: draw selection table
        user_input = self._safe_input(  # WHY: injected input helper handles EOF consistently
            "\nEnter the index number of the switch: ", context="switch_selection"
        ).strip()
        logging.debug("User input for switch selection: %s", user_input)  # WHY: raw input for diagnostics
        return self._resolve_mac_choice(user_input, index_map, "switch")  # WHY: single-index resolution

    # ------------------------------------------------------------------
    # Shared helpers for the three public device-selection methods
    # ------------------------------------------------------------------

    def _fetch_and_sort_devices(  # WHY: shared fetch+sort helper
        self, site_id: str, device_type: str, plural_label: str
    ) -> list[Any] | None:
        """Fetch devices of a given type, sort by name, or return None on empty/error.

        Emits the user-facing 'No <plural> found' / 'Error fetching <plural>' messages
        so callers can simply check for a None result and bail out.
        """
        logging.info("Fetching %s list for site %s to present selection prompt", plural_label, site_id)  # WHY: audit
        try:
            response = mistapi.api.v1.sites.devices.listSiteDevices(  # WHY: single API call for the type
                self._session, site_id, type=device_type
            )
        except Exception as error:  # WHY: broad catch keeps flow alive on any API failure
            print(f"\n! Error fetching {plural_label}: {error}")  # WHY: surface failure to operator
            logging.exception("Exception fetching %s for site %s: %s", plural_label, site_id, error)  # WHY: audit
            return None  # WHY: signal fetch failure to caller
        rawdata = response.data  # WHY: unwrap to the list payload the API returned
        if not rawdata:  # WHY: guard against zero-length inventory before prompting
            print(f"\n! No {plural_label} found at the selected site.")  # WHY: nothing to offer the user
            logging.warning("No %s found for site_id: %s", plural_label, site_id)  # WHY: audit empty result
            return None  # WHY: signal empty inventory to caller
        logging.debug("Received %d %s for site %s from Mist API", len(rawdata), plural_label, site_id)  # WHY: audit
        return sorted(rawdata, key=lambda x: x.get("name", ""))  # WHY: alphabetical order aids readability

    def _render_device_selection(self, devices: list[Any], header: str) -> dict[int, Any]:  # WHY: shared table renderer
        """Print a numbered PrettyTable of devices and return an index->device map.

        The returned map lets callers translate a user-entered index back to
        the full device dict so they can pull out MAC/name for confirmation.
        """
        table = PrettyTable()  # WHY: fresh table per prompt so state is not shared across calls
        table.field_names = _DEVICE_TABLE_FIELDS  # WHY: use shared header set for visual consistency
        index_map = self._populate_device_rows(table, devices)  # WHY: rows plus index map for callers
        self._print_selection_banner(header)  # WHY: banner + separators around header text
        print(table)  # WHY: render the selection table to the terminal
        logging.info("Displaying %s table (%d) -- awaiting input", header, len(devices))  # WHY: audit prompt
        return index_map  # WHY: caller uses this to resolve the entered index

    @staticmethod
    def _populate_device_rows(table: PrettyTable, devices: list[Any]) -> dict[int, Any]:  # WHY: rows + index map
        """Add one row per device to the table and return the index->device map."""
        index_map: dict[int, Any] = {}  # WHY: maps display index back to the raw device dict
        for idx, dev in enumerate(devices):  # WHY: assign one row per device
            table.add_row(
                [
                    idx,  # WHY: zero-based index that the user enters
                    dev.get("name", "Unknown"),  # WHY: human-readable device name
                    dev.get("mac", "Unknown"),  # WHY: device MAC address for operator context
                    dev.get("model", "Unknown"),  # WHY: hardware model identifier
                    dev.get("status", "Unknown"),  # WHY: connection state
                ]
            )
            index_map[idx] = dev  # WHY: retain the full dict so we can retrieve MAC by index later
        return index_map  # WHY: caller uses this to resolve the entered index

    @staticmethod
    def _print_selection_banner(header: str) -> None:  # WHY: shared header banner
        """Print the visual separator banner around a device-selection header."""
        print("\n" + "=" * 80)  # WHY: visual separator before the header
        print(f" {header}")  # WHY: identify which type of device is being selected
        print("=" * 80)  # WHY: visual separator after the header

    def _resolve_mac_choice(  # WHY: shared input validator
        self, user_input: str, index_map: dict[int, Any], kind_label: str
    ) -> str | None:
        """Validate a numeric device-selection choice and return the picked MAC, or None."""
        if not user_input.isdigit():  # WHY: only accept numeric index values
            print("\n! Please enter a valid index number")  # WHY: guide operator toward correct input
            logging.error("Non-numeric %s selection input: %s", kind_label, user_input)  # WHY: audit bad input
            return None  # WHY: reject non-numeric input
        idx = int(user_input)  # WHY: convert to integer for map lookup
        if idx not in index_map:  # WHY: reject out-of-range indices before dereferencing
            print("\n! Invalid index")  # WHY: guide operator toward correct input
            logging.error("Invalid %s index entered by user: %d", kind_label, idx)  # WHY: audit bad index
            return None  # WHY: reject out-of-range index
        device = index_map[idx]  # WHY: retrieve the chosen device dict
        mac: str | None = device.get("mac")  # WHY: typed local narrows Any so mypy accepts the return
        name = device.get("name", "Unknown")  # WHY: retrieve name for the confirmation message
        print(f"\n! Selected {kind_label}: {name} (MAC: {mac})")  # WHY: confirm selection to operator
        logging.info("User selected %s index %d: name=%s mac=%s", kind_label, idx, name, mac)  # WHY: audit
        return mac  # WHY: caller uses this to target the selected device

    # ------------------------------------------------------------------
    # Public port-selection entry point
    # ------------------------------------------------------------------

    def select_ports_from_device(  # WHY: public entry point for port selection
        self,
        site_id: str,
        device_mac: str,
        device_type: str = "switch",
        return_available: bool = False,
    ) -> PortSelectionResult:
        """Prompt the user to select up to six ports from a switch or gateway.

        Fetches live port status (falling back to device config when unavailable) and
        displays a numbered selection table.  Returns the selected port names, or
        ``None`` on failure/cancellation.  When ``return_available`` is True the
        caller receives ``(selected_ports, available_ports)`` so an empty selection
        can be expanded to every UP port.
        """
        logging.info("Fetching port information for %s %s at site %s", device_type, device_mac, site_id)
        try:
            return self._perform_port_selection(site_id, device_mac, device_type, return_available)
        except Exception as error:  # WHY: broad catch keeps flow alive on any API failure
            print(f"\n! Error fetching port information: {error}")  # WHY: surface failure to operator
            logging.exception("Exception in select_ports_from_device: %s", error)  # WHY: full traceback
            return None  # WHY: signal failure so caller can prompt again or abort

    def _perform_port_selection(
        self, site_id: str, device_mac: str, device_type: str, return_available: bool
    ) -> PortSelectionResult:
        """Run the fetch-gather-prompt pipeline for select_ports_from_device."""
        available, port_to_config, device_name = self._gather_available_ports(  # WHY: fetch + filter
            site_id, device_mac, device_type
        )
        if not available:  # WHY: nothing selectable -- helper already printed the reason
            return None
        request = _PortPromptRequest(  # WHY: bundle prompt inputs to keep signature narrow
            available_ports=available,
            port_to_config=port_to_config,
            device_mac=device_mac,
            device_name=device_name,
            device_type=device_type,
            return_available=return_available,
        )
        return self._prompt_port_selection(request)  # WHY: hand off to interactive selector

    # ------------------------------------------------------------------
    # Private helpers for select_ports_from_device
    # ------------------------------------------------------------------

    def _gather_available_ports(
        self, site_id: str, device_mac: str, device_type: str
    ) -> tuple[list[tuple[str, Any]], dict[str, Any], str]:
        """Fetch device stats/config and return filtered available ports.

        Returns (available_ports, port_to_config, device_name).  All user-facing
        error messages are emitted here so the caller only needs to check the
        returned list before deciding whether to prompt.
        """
        device = self._resolve_target_device(site_id, device_mac, device_type)  # WHY: locate device
        if device is None:  # WHY: device not in inventory -- helper already logged/printed
            return [], {}, ""
        device_id = cast("str", device.get("id"))  # WHY: Mist UUID needed by subsequent API calls
        device_name = cast("str", device.get("name", "Unknown"))  # WHY: human-readable label for messages
        port_stat, port_to_config = self._collect_port_stat_and_config(  # WHY: stats + fallback + config
            site_id, device_id, device_mac, device_type, device_name
        )
        if port_stat is None:  # WHY: neither live stats nor synthetic fallback succeeded
            return [], port_to_config, device_name
        available = self._filter_and_sort_ports(port_stat)  # WHY: strip mgmt/DOWN and natural sort
        if not available:  # WHY: everything filtered out -- warn once
            print(f"\n! No network ports available for {device_type}: {device_name}")  # WHY: user-facing
            logging.warning("No user-facing ports found for device %s", device_id)  # WHY: audit trail
        return available, port_to_config, device_name  # WHY: caller decides whether to prompt

    def _collect_port_stat_and_config(
        self, site_id: str, device_id: str, device_mac: str, device_type: str, device_name: str
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """Fetch port_stat with config fallback and build the port-to-config map."""
        port_stat = self._fetch_port_stats(site_id, device_id, device_mac, device_type)  # WHY: live status
        port_config = self._fetch_port_config(site_id, device_id)  # WHY: profile/description source
        port_to_config = self._build_port_to_config_map(port_config)  # WHY: O(1) per-port lookup
        if port_stat:  # WHY: live stats present -- no fallback needed
            return port_stat, port_to_config
        fallback = self._build_port_stat_from_config(  # WHY: synthesize from config when stats absent
            port_config, device_id, device_type, device_name
        )
        if fallback is None:  # WHY: fallback also failed -- helper already told the operator why
            return None, port_to_config
        return fallback, port_to_config  # WHY: proceed with synthetic stats flagged as _fallback=True

    def _resolve_target_device(self, site_id: str, device_mac: str, device_type: str) -> Any | None:
        """Look up the target device in site inventory by normalised MAC."""
        normalized = _normalize_mac(device_mac)  # WHY: separator-agnostic comparison key
        logging.debug("Normalised input MAC for comparison: %s", normalized)  # WHY: diagnostics for misses
        devices_response = mistapi.api.v1.sites.devices.listSiteDevices(  # WHY: fetch all of target type
            self._session, site_id, type=device_type
        )
        devices = devices_response.data  # WHY: unwrap to the device list
        device = self._find_device_by_mac(devices, normalized, device_mac)  # WHY: linear scan by MAC
        if device is None:  # WHY: not found -- print helpful diagnostic before returning None
            print(f"\n! Could not find {device_type} with MAC {device_mac}")  # WHY: guide operator
            logging.error(  # WHY: list observed MACs to help diagnose stale inventory
                "Device not found with MAC: %s (normalised: %s). Available: %s",
                device_mac,
                normalized,
                [d.get("mac") for d in devices],
            )
        return device  # WHY: dict on success, None on miss

    def _find_device_by_mac(self, devices: list[Any], normalized_target: str, original_mac: str) -> Any | None:
        """Return the first device dict whose MAC matches normalized_target, or None."""
        for dev in devices:  # WHY: linear scan over the inventory list
            dev_mac = dev.get("mac", "")  # WHY: raw MAC from API (may include colons)
            normalized_dev_mac = _normalize_mac(str(dev_mac))  # WHY: identical normalisation as the target
            logging.debug(  # WHY: each comparison is logged so failed matches are traceable
                "Comparing device %s: %s (normalised: %s)",
                dev.get("name", "Unknown"),
                dev_mac,
                normalized_dev_mac,
            )
            if normalized_dev_mac == normalized_target:  # WHY: exact post-normalisation match
                logging.debug("MAC match found for device: %s", dev.get("name", "Unknown"))  # WHY: audit hit
                return dev  # WHY: first match wins -- MACs are unique in inventory
        logging.error(  # WHY: log the target MAC so operators can diagnose mismatches
            "No device found matching normalised MAC: %s (original: %s)", normalized_target, original_mac
        )
        return None  # WHY: no match found in inventory

    def _fetch_port_stats(self, site_id: str, device_id: str, device_mac: str, device_type: str) -> dict[str, Any]:
        """Dispatch to the switch/gateway or AP port-stat handler by device type."""
        if device_type in ("switch", "gateway"):  # WHY: switches and gateways share a richer stats endpoint
            return self._fetch_switch_gateway_port_stats(site_id, device_id, device_mac)
        return self._fetch_ap_port_stats(site_id, device_id)  # WHY: APs use general device stats endpoint

    def _fetch_switch_gateway_port_stats(self, site_id: str, device_id: str, device_mac: str) -> dict[str, Any]:
        """Fetch switch/gateway port stats via searchSiteSwOrGwPorts."""
        logging.info("Fetching switch/gateway port stats via searchSiteSwOrGwPorts for device %s", device_id)
        try:
            response = mistapi.api.v1.sites.stats.searchSiteSwOrGwPorts(  # WHY: dedicated port stats API
                self._session, site_id, mac=device_mac, limit=1000
            )
        except Exception as port_search_error:  # WHY: log and swallow -- caller falls back to config
            logging.error("Error fetching switch/gateway port stats: %s", port_search_error)  # WHY: audit
            return {}  # WHY: empty dict signals 'no live stats' to the caller
        results = response.data.get("results", [])  # WHY: unwrap to the list of per-port dicts
        logging.info("Retrieved %d port stat entries from searchSiteSwOrGwPorts", len(results))  # WHY: audit
        port_stat = self._index_port_results(results)  # WHY: build port_id -> stat map
        self._log_port_stat_summary(port_stat, device_mac)  # WHY: emit info/warn based on outcome
        return port_stat  # WHY: may be empty when device is offline -- caller handles fallback

    @staticmethod
    def _index_port_results(results: list[Any]) -> dict[str, Any]:
        """Index a searchSiteSwOrGwPorts result list by port_id for O(1) lookup."""
        port_stat: dict[str, Any] = {}  # WHY: accumulate keyed by port_id
        for port_obj in results:  # WHY: one iteration per per-port stat dict
            port_id = port_obj.get("port_id")  # WHY: only store entries with a stable identifier
            if port_id:  # WHY: skip malformed entries that lack a port_id
                port_stat[port_id] = port_obj  # WHY: index by port_id for downstream lookup
        return port_stat  # WHY: caller decides whether to warn on empty

    @staticmethod
    def _log_port_stat_summary(port_stat: dict[str, Any], device_mac: str) -> None:
        """Emit info or warn log describing how many port stats were indexed."""
        if port_stat:  # WHY: healthy path -- log count for audit trail
            logging.info("Converted %d switch/gateway ports to stat dict", len(port_stat))
        else:  # WHY: warn when API returned data but nothing usable
            logging.warning("searchSiteSwOrGwPorts returned no usable port data for device %s", device_mac)

    def _fetch_ap_port_stats(self, site_id: str, device_id: str) -> dict[str, Any]:
        """Fetch AP port stats from the port_stat field embedded in device stats."""
        logging.info("Fetching AP port stats via getSiteDeviceStats for device %s", device_id)  # WHY: audit
        stats_response = mistapi.api.v1.sites.stats.getSiteDeviceStats(  # WHY: AP stats endpoint
            self._session, site_id, device_id
        )
        stats_data = stats_response.data  # WHY: unwrap to the device stats dict
        port_stat = cast("dict[str, Any]", stats_data.get("port_stat", {}))  # WHY: narrow Any for mypy strict
        if port_stat:  # WHY: log presence so operators can confirm live data
            logging.info("Found port_stat (AP-style) with %d ports", len(port_stat))
        else:  # WHY: warn when the AP hasn't reported any port stats yet
            logging.warning("No port_stat found in AP stats for device %s", device_id)
        return port_stat  # WHY: empty dict when device is silent -- caller handles fallback

    def _fetch_port_config(self, site_id: str, device_id: str) -> dict[str, Any]:
        """Retrieve device configuration and return the port_config section.

        Falls back to an empty dict if the device config API call fails.
        """
        logging.debug("Fetching device config for port profiles/descriptions from device %s", device_id)  # WHY: audit
        try:
            device_config_response = mistapi.api.v1.sites.devices.getSiteDevice(  # WHY: full device config
                self._session, site_id, device_id
            )
        except Exception as cfg_error:  # WHY: non-fatal -- profiles/descriptions will just be missing
            logging.warning("Could not fetch device config for port details: %s", cfg_error)  # WHY: audit
            return {}  # WHY: empty dict spares callers a None guard
        port_config: dict[str, Any] = device_config_response.data.get("port_config", {})  # WHY: extract section
        logging.debug("Retrieved port_config with %d entries for device %s", len(port_config), device_id)  # WHY: audit
        return port_config  # WHY: dict keyed by range strings like 'ge-0/0/0-5'

    def _build_port_to_config_map(self, port_config: dict[str, Any]) -> dict[str, Any]:
        """Expand range-based port config keys to individual port name mappings.

        Converts {'ge-0/0/0-5': {...}} to {'ge-0/0/0': {...}, ...} so per-port
        config lookups are O(1) in the table-rendering path.
        """
        port_to_config: dict[str, Any] = {}  # WHY: output map keyed by individual port name
        if not port_config:  # WHY: no config to expand -- warn once and return
            logging.warning("No port_config available -- port profiles and descriptions will be missing")
            return port_to_config
        logging.info("Expanding %d port_config entries to individual port mappings", len(port_config))  # WHY: audit
        for port_range_key, cfg in port_config.items():  # WHY: iterate range-keyed config entries
            expanded_ports = self._expand_port_range(port_range_key)  # WHY: use injected expander callable
            logging.debug("Port config key '%s' expands to %d ports", port_range_key, len(expanded_ports))  # WHY: audit
            for individual_port in expanded_ports:  # WHY: map each individual port to the shared config
                port_to_config[individual_port] = cfg  # WHY: same dict object -- reads are shared
        logging.info("Built port_to_config map with %d individual port entries", len(port_to_config))  # WHY: audit
        return port_to_config  # WHY: caller uses this for O(1) profile/description lookup

    def _build_port_stat_from_config(
        self,
        port_config: dict[str, Any] | None,
        device_id: str,
        device_type: str,
        device_name: str,
    ) -> dict[str, Any] | None:
        """Build a synthetic port_stat dict from device config when live stats are unavailable."""
        logging.warning(  # WHY: warn before fallback so operator knows stats are not live
            "No port_stat from API for device %s -- attempting config-based fallback", device_id
        )
        if not port_config:  # WHY: neither stats nor config -- nothing to show
            self._report_no_port_info(device_type, device_name)  # WHY: user-facing rejection message
            logging.warning("No port_stat or port_config found for device %s", device_id)  # WHY: audit
            return None
        try:
            return self._synthesize_port_stat_from_config(port_config, device_id)  # WHY: main synthesis path
        except Exception as config_error:  # WHY: malformed config or expander failure
            self._report_no_port_info(device_type, device_name)  # WHY: reuse the shared rejection message
            logging.error("Could not build port_stat from device config: %s", config_error)  # WHY: audit
            return None

    @staticmethod
    def _report_no_port_info(device_type: str, device_name: str) -> None:
        """Emit the user-facing 'no port information' message pair."""
        print(f"\n! No port information available for {device_type}: {device_name}")  # WHY: user-facing
        print("  This device may be offline or not yet reporting statistics.")  # WHY: guide operator

    def _synthesize_port_stat_from_config(self, port_config: dict[str, Any], device_id: str) -> dict[str, Any]:
        """Iterate configured port ranges and build a synthetic port_stat dict."""
        logging.info(  # WHY: audit start of synthesis
            "Building synthetic port_stat from %d port_config entries for device %s",
            len(port_config),
            device_id,
        )
        port_stat: dict[str, Any] = {}  # WHY: accumulate one entry per individual port
        for port_range_key, port_cfg in port_config.items():  # WHY: iterate over configured ranges
            expanded_ports = self._expand_port_range(port_range_key)  # WHY: turn range into individual ports
            logging.debug("Expanded port range '%s' to %d ports", port_range_key, len(expanded_ports))  # WHY: audit
            for individual_port in expanded_ports:  # WHY: create one synthetic entry per port
                port_stat[individual_port] = self._synthesize_port_entry(port_cfg)  # WHY: fixed shape per port
        logging.info(  # WHY: audit result size after building synthetic stats
            "Built synthetic port_stat with %d individual port entries for device %s",
            len(port_stat),
            device_id,
        )
        return port_stat  # WHY: caller flags _fallback=True in each entry

    @staticmethod
    def _synthesize_port_entry(port_cfg: dict[str, Any]) -> dict[str, Any]:
        """Return a single synthetic port_stat entry derived from a port config dict."""
        usage = port_cfg.get("usage", "")  # WHY: empty/'disabled' usage means port is off
        duplex_value = port_cfg.get("duplex", "N/A")  # WHY: configured duplex may differ from live
        return {
            "up": usage not in ("disabled", "", None),  # WHY: derive UP state from usage profile
            "speed": port_cfg.get("speed", "N/A"),  # WHY: configured speed placeholder
            "full_duplex": duplex_value in ("full", "auto"),  # WHY: normalise to bool for display
            "duplex": duplex_value,  # WHY: preserve raw value for the formatter
            "_fallback": True,  # WHY: table renderer shows a NOTE when any port has this flag
        }

    def _filter_and_sort_ports(self, port_stat: dict[str, Any]) -> list[tuple[str, Any]]:
        """Filter management/service and DOWN ports, then natural-sort the rest.

        Returns a list of (port_name, port_info) tuples ordered so ge-0/0/9
        precedes ge-0/0/10 rather than sorting lexicographically.
        """
        available: list[tuple[str, Any]] = []  # WHY: accumulate surviving (name, info) tuples
        for port_name, port_info in port_stat.items():  # WHY: iterate over every port in the stat dict
            if _is_management_port(port_name):  # WHY: skip loopback/management/service interfaces
                logging.debug("Excluding management/service port: %s", port_name)  # WHY: audit exclusion
                continue
            if not port_info.get("up", False):  # WHY: DOWN ports cannot be captured -- skip
                logging.debug("Excluding DOWN port: %s", port_name)  # WHY: audit exclusion
                continue
            available.append((port_name, port_info))  # WHY: keep this UP user-facing port
        result = sorted(available, key=_natural_sort_key)  # WHY: natural sort places ge-0/0/9 before ge-0/0/10
        logging.debug("Filtered to %d UP user-facing ports after exclusions", len(result))  # WHY: audit
        return result  # WHY: sorted list of (name, info) tuples ready for display

    # ------------------------------------------------------------------
    # Interactive port-selection prompt and its display helpers
    # ------------------------------------------------------------------

    def _prompt_port_selection(self, request: _PortPromptRequest) -> PortSelectionResult:
        """Render the port selection table and collect the user's choice.

        Enforces the Mist API 6-port-per-capture limit.  Returns the selected
        port name list (or a tuple with available ports when ``return_available``
        is True), or ``None`` on failure or cancellation.
        """
        self._display_full_port_prompt(request)  # WHY: banner + table + help block
        user_input = self._safe_input(  # WHY: injected input helper handles EOF/empty consistently
            "\nEnter your choice (up to 6 ports): ", context="port_selection", allow_empty=True
        ).strip()
        logging.debug("User input for port selection: %s", user_input)  # WHY: raw input for diagnostics
        return self._dispatch_port_input(user_input, request)  # WHY: cancel/all/parse dispatch

    def _display_full_port_prompt(self, request: _PortPromptRequest) -> None:
        """Render port table header, table, and help block to the terminal."""
        table = self._build_port_table(request.available_ports, request.port_to_config)  # WHY: build UI
        using_fallback = any(  # WHY: any config-derived port triggers a NOTE banner
            port_info.get("_fallback", False) for _, port_info in request.available_ports
        )
        self._display_port_prompt_header(request, table, using_fallback)  # WHY: banner + table
        self._display_port_selection_options(len(request.available_ports))  # WHY: help block
        logging.info(
            "Displaying port selection table for %s %s (%d UP ports) -- awaiting user input",
            request.device_type,
            request.device_mac,
            len(request.available_ports),
        )

    def _dispatch_port_input(self, user_input: str, request: _PortPromptRequest) -> PortSelectionResult:
        """Route port input to cancel, all, or index-parse handling."""
        if user_input.lower() == "c":  # WHY: explicit cancel path
            print("\n! Port selection cancelled")  # WHY: confirm cancellation to operator
            logging.info("Port selection cancelled by user")  # WHY: audit cancel
            return None
        if not user_input or user_input.lower() == "all":  # WHY: empty/'all' selects every available port
            return self._handle_all_ports_selection(request.available_ports, request.return_available)
        index_to_port = {idx: name for idx, (name, _) in enumerate(request.available_ports)}  # WHY: idx map
        return self._parse_port_indices(  # WHY: index/comma/range parsing path
            user_input, index_to_port, request.return_available, request.available_ports
        )

    def _display_port_prompt_header(
        self, request: _PortPromptRequest, table: PrettyTable, using_fallback: bool
    ) -> None:
        """Print the SELECT PORTS banner, device info, optional fallback notice, and the table."""
        print("\n" + "=" * 80)  # WHY: visual separator before header
        print(
            f" SELECT PORTS FROM {request.device_type.upper()}: {request.device_name}"
        )  # nosec B608 - display header, not SQL
        print("=" * 80)  # WHY: visual separator after title
        print(f"  Device MAC: {request.device_mac}")  # WHY: show MAC so operator can confirm target
        print(f"  Available Ports: {len(request.available_ports)}")  # WHY: show count up-front
        if using_fallback:  # WHY: warn when values came from config rather than live stats
            print("  NOTE: Speed/Duplex showing configured values (device stats unavailable)")
        print("=" * 80)  # WHY: visual separator before the table
        print(table)  # WHY: render the actual port table

    def _display_port_selection_options(self, port_count: int) -> None:
        """Print the help block describing the port selection input syntax and API limit."""
        print("\n" + "!" * 80)  # WHY: emphasise the API limitation with '!'
        print("  API LIMITATION: Maximum 6 ports per capture")  # WHY: state the hard cap
        print("!" * 80)  # WHY: close the emphasised block
        print("\nPort Selection Options:")  # WHY: introduce the help lines
        print("  - Enter a single index (e.g., '0') for one port")  # WHY: single-index syntax
        print("  - Enter multiple indices separated by commas (e.g., '0,2,5')")  # WHY: comma-list syntax
        print("  - Enter a range (e.g., '0-3' for ports 0, 1, 2, 3)")  # WHY: range syntax
        if port_count <= _MAX_PORTS_PER_CAPTURE:  # WHY: only offer 'all' when it fits within the cap
            print("  - Press Enter with no input to capture on ALL ports (default)")
        else:  # WHY: 'all' unavailable when port count exceeds the API cap
            print("  - Press Enter with no input to capture on ALL ports (NOT AVAILABLE - exceeds 6 port limit)")
        print("  - Enter 'c' to cancel")  # WHY: explicit cancel option

    def _build_port_table(self, available_ports: list[tuple[str, Any]], port_to_config: dict[str, Any]) -> PrettyTable:
        """Build a PrettyTable of available ports with status, speed, and config info."""
        table = PrettyTable()  # WHY: fresh table per call so state is not shared
        table.field_names = _PORT_TABLE_FIELDS  # WHY: use shared column set for visual consistency
        table.max_width = 120  # WHY: cap width so long descriptions don't overflow a 120-col terminal
        table.align["Description"] = "l"  # WHY: left-align description so text wraps predictably
        table.align["Profile"] = "l"  # WHY: left-align profile name for readability
        for idx, (port_name, port_info) in enumerate(available_ports):  # WHY: one row per available port
            table.add_row(self._build_port_row(idx, port_name, port_info, port_to_config))  # WHY: compose row
        return table  # WHY: fully populated table ready to print

    def _build_port_row(
        self, idx: int, port_name: str, port_info: dict[str, Any], port_to_config: dict[str, Any]
    ) -> list[Any]:
        """Return a single formatted table row for a port."""
        status = "UP" if port_info.get("up", False) else "DOWN"  # WHY: human-readable link state
        speed_str = self._format_speed(port_info.get("speed", "N/A"))  # WHY: convert raw speed to display form
        duplex_str = self._format_duplex(  # WHY: convert raw duplex to display form
            port_info.get("duplex", ""), port_info.get("full_duplex", False)
        )
        port_cfg = port_to_config.get(port_name, {})  # WHY: look up per-port config for profile/description
        port_profile = port_cfg.get("port_profile", "N/A")  # WHY: VLAN or access profile name
        port_description = port_cfg.get("description", "")  # WHY: operator-entered description
        if len(port_description) > 30:  # WHY: truncate long descriptions to keep table readable
            port_description = port_description[:27] + "..."
        if not port_description:  # WHY: dash placeholder is friendlier than empty cell
            port_description = "-"
        return [idx, port_name, status, speed_str, duplex_str, port_profile, port_description]  # WHY: row shape

    @staticmethod
    def _format_speed(speed: Any) -> str:
        """Convert a raw speed value (string or number) to a human-readable Mbps string."""
        if isinstance(speed, str):  # WHY: API may return string like 'auto', '1G', '10G'
            string_result = PromptNetworkDeviceUtils._format_speed_string(speed)  # WHY: string-specific parser
            if string_result is not None:  # WHY: valid string form produced a display value
                return string_result
        if isinstance(speed, (int, float)) and speed > 0:  # WHY: numeric speed already in Mbps
            return f"{speed} Mbps"
        return "N/A"  # WHY: unknown, zero, or non-parseable non-G string

    @staticmethod
    def _format_speed_string(speed: str) -> str | None:
        """Convert an alphanumeric speed string to display form, or None if not recognised."""
        speed_upper = speed.upper()  # WHY: comparisons and endswith checks use uppercase
        if speed_upper == "AUTO":  # WHY: 'auto' -- show 'Auto' with proper case
            return "Auto"
        if speed_upper.endswith("G"):  # WHY: '1G'/'10G' style -- multiply by 1000
            try:
                return f"{int(speed_upper[:-1]) * 1000} Mbps"  # WHY: strip G and convert to Mbps
            except ValueError:
                return speed  # WHY: non-integer prefix (e.g. '1.5G') falls back to raw value
        return None  # WHY: unrecognised string form -- caller falls through to numeric/N-A logic

    @staticmethod
    def _format_duplex(duplex_value: str, full_duplex_flag: bool) -> str:
        """Return a human-readable duplex string from API value or bool fallback."""
        if duplex_value:  # WHY: prefer the explicit string value from the API when present
            mapping = {"full": "Full", "half": "Half", "auto": "Auto"}  # WHY: normalise known values
            return mapping.get(duplex_value.lower(), str(duplex_value).capitalize())  # WHY: unknowns capitalise
        return "Full" if full_duplex_flag else "Half"  # WHY: fall back to bool flag when string is absent

    def _handle_all_ports_selection(
        self, available_ports: list[tuple[str, Any]], return_available: bool
    ) -> PortSelectionResult:
        """Handle the 'select all ports' case and enforce the 6-port API limit."""
        if len(available_ports) > _MAX_PORTS_PER_CAPTURE:  # WHY: Mist API rejects >6 ports per capture
            print(  # WHY: user-facing rejection message
                f"\n! ERROR: Cannot select all {len(available_ports)} ports - API maximum is 6 ports per capture"
            )
            print("  Please select up to 6 specific ports from the list above")  # WHY: guide operator
            logging.error(  # WHY: audit the violation for later review
                "User attempted to select all %d ports -- exceeds API limit of 6", len(available_ports)
            )
            return None
        print(f"\n! Selected ALL {len(available_ports)} ports for capture")  # WHY: confirm selection
        logging.info("User selected all %d ports (within 6-port limit)", len(available_ports))  # WHY: audit
        if return_available:  # WHY: caller wants full list alongside the empty-selection sentinel
            return [], available_ports
        return []  # WHY: empty list signals 'all ports' to the caller

    def _expand_index_range(self, part: str, index_to_port: dict[int, str]) -> set[int]:
        """Expand a range token like '2-5' into validated individual port indices."""
        result: set[int] = set()  # WHY: accumulate validated indices for this range token
        range_parts = part.split("-")  # WHY: split on hyphen separator
        if len(range_parts) != 2:  # WHY: reject malformed ranges like '2-3-4' or '-'
            return result
        start_idx = int(range_parts[0].strip())  # WHY: inclusive start index of the range
        end_idx = int(range_parts[1].strip())  # WHY: inclusive end index of the range
        for port_index in range(start_idx, end_idx + 1):  # WHY: expand to every index in the closed interval
            if port_index in index_to_port:  # WHY: only accept indices within the displayed table
                result.add(port_index)
            else:  # WHY: warn the operator so out-of-range indices are surfaced
                print(f"\n! Warning: Index {port_index} is out of range, skipping")
                logging.warning("Invalid port index in range: %d", port_index)  # WHY: audit
        return result  # WHY: set of valid indices from this range token

    def _collect_selected_indices(self, user_input: str, index_to_port: dict[int, str]) -> set[int] | None:
        """Parse comma-separated tokens into a validated index set, or None on parse error."""
        selected: set[int] = set()  # WHY: deduplicate across all tokens
        try:
            for part in [p.strip() for p in user_input.split(",")]:  # WHY: split on commas, strip whitespace
                selected |= self._parse_selection_token(part, index_to_port)  # WHY: delegate per token
        except ValueError as parse_error:  # WHY: non-numeric text triggers ValueError from int()
            print(f"\n! Invalid input format: {parse_error}")  # WHY: guide operator toward correct input
            logging.error("Port selection parse error: %s", parse_error)  # WHY: audit parse failure
            return None
        return selected  # WHY: complete set of valid indices from the input

    def _parse_selection_token(self, part: str, index_to_port: dict[int, str]) -> set[int]:
        """Return validated indices from a single token -- either a range or a single index."""
        if "-" in part:  # WHY: hyphen marks a range token -- delegate to range expander
            return self._expand_index_range(part, index_to_port)
        idx = int(part)  # WHY: single-index token must be numeric (ValueError bubbles up)
        if idx in index_to_port:  # WHY: only accept indices within the displayed table
            return {idx}
        print(f"\n! Warning: Index {idx} is out of range, skipping")  # WHY: warn the operator
        logging.warning("Invalid port index: %d", idx)  # WHY: audit bad index
        return set()  # WHY: empty set contributes nothing to the running union

    def _parse_port_indices(
        self,
        user_input: str,
        index_to_port: dict[int, str],
        return_available: bool,
        available_ports: list[tuple[str, Any]],
    ) -> PortSelectionResult:
        """Parse user port index input and return the validated selected port name list."""
        logging.debug("Parsing port selection input: %s", user_input)  # WHY: raw input for diagnostics
        selected_indices = self._collect_selected_indices(user_input, index_to_port)  # WHY: to index set
        if selected_indices is None:  # WHY: parse failure -- helper already printed the reason
            return None
        selected_ports = self._materialize_and_validate_ports(selected_indices, index_to_port)  # WHY: names
        if selected_ports is None:  # WHY: empty selection or 6-port cap exceeded -- helper messaged
            return None
        print(f"\n! Selected {len(selected_ports)} port(s): {', '.join(selected_ports)}")  # WHY: confirm
        logging.info("User selected ports: %s", selected_ports)  # WHY: audit final selection
        if return_available:  # WHY: caller wants both the selection and the full available list
            return selected_ports, available_ports
        return selected_ports  # WHY: return just the selected port name list

    def _materialize_and_validate_ports(
        self, selected_indices: set[int], index_to_port: dict[int, str]
    ) -> list[str] | None:
        """Convert an index set to a sorted port-name list, or None on empty/over-cap."""
        if not selected_indices:  # WHY: no valid indices remained after parsing
            print("\n! No valid ports selected")  # WHY: user-facing rejection
            logging.error("No valid port indices provided by user")  # WHY: audit empty result
            return None
        selected_ports = [index_to_port[idx] for idx in sorted(selected_indices)]  # WHY: ordered by index
        if len(selected_ports) > _MAX_PORTS_PER_CAPTURE:  # WHY: enforce Mist API hard limit
            print(  # WHY: user-facing rejection message
                f"\n! ERROR: Selected {len(selected_ports)} ports, but API maximum is 6 ports per capture"
            )
            print("  Please refine your selection to 6 or fewer ports")  # WHY: guide operator
            logging.error(  # WHY: audit the violation
                "User selected %d ports -- exceeds API limit of 6", len(selected_ports)
            )
            return None
        return selected_ports  # WHY: caller emits the confirmation message
