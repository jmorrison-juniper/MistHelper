"""
PromptNetworkDeviceUtils -- Interactive network device selection prompts.

Extracted from MistHelper.py to src/device/prompt_utils.py as part of
Wave 2 systematic decomposition (issue #332).

Provides interactive user prompts for selecting APs, gateways, and switches
from a Mist site, and for choosing ports from a selected device.

NOC Engineer Note: Every method logs clearly before and after each operation
so operators can trace exactly what happened during any run.
"""

from __future__ import annotations  # Enable PEP 604 union syntax on Python 3.10+

import logging  # Standard logging for all progress and error messages
import re  # Regular expressions for natural port sorting
from typing import Any  # Type annotation for heterogeneous dicts

import mistapi.api.v1.sites.devices  # Mist Sites Devices API for listing APs/gateways/switches
import mistapi.api.v1.sites.stats  # Mist Sites Stats API for per-port status info
from prettytable import PrettyTable  # Tabular display for device and port selection lists


class PromptNetworkDeviceUtils:
    """
    Interactive prompts for selecting network devices and ports from a Mist site.

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

    def __init__(self, apisession: Any, safe_input_fn: Any, expand_port_range_fn: Any) -> None:
        """
        Initialise with injected runtime dependencies.

        Args:
            apisession: Active mistapi session object used for all API calls.
            safe_input_fn: Callable matching InputUtils.safe_input signature
                           for all interactive user prompts.
            expand_port_range_fn: Callable matching DeviceUtils.expand_port_range_string
                                  that expands a port range key like 'ge-0/0/0-5'
                                  into a list of individual port name strings.
        """
        self._session = apisession  # Mist API session injected at construction time
        self._safe_input = safe_input_fn  # Input helper injected to avoid global dependency
        self._expand_port_range = expand_port_range_fn  # Port range expander injected at construction

    # ------------------------------------------------------------------
    # Public device-selection helpers
    # ------------------------------------------------------------------

    def select_ap_mac(self, site_id: str) -> str | None:
        """
        Prompt the user to choose an AP from a site and return its MAC address.

        Fetches all APs at the site, renders a numbered selection table,
        and returns the chosen MAC or the special sentinel "ALL_APS".

        Args:
            site_id: Mist site ID to scope the AP inventory query.

        Returns:
            MAC address string of the chosen AP, "ALL_APS" if the user chose
            all APs, or None if the selection was cancelled or failed.
        """
        logging.info("Fetching AP list for site %s to present selection prompt", site_id)  # Log before API call
        try:
            rawdata = mistapi.api.v1.sites.devices.listSiteDevices(  # Fetch all APs from this site
                self._session, site_id, type="ap"
            ).data
            if not rawdata:  # No APs found -- nothing to offer the user
                print("\n! No APs found at the selected site.")
                logging.warning("No APs found for site_id: %s", site_id)  # Log empty result for traceability
                return None

            logging.debug("Received %d APs for site %s from Mist API", len(rawdata), site_id)  # Log count after API

            aps = sorted(rawdata, key=lambda x: x.get("name", ""))  # Sort alphabetically for user readability

            table = PrettyTable()  # Build a clean numbered table for the terminal
            table.field_names = ["Index", "Name", "MAC", "Model", "Status"]  # Column headers
            index_to_ap: dict[int, Any] = {}  # Map display index back to the raw AP dict

            for idx, ap in enumerate(aps):  # Populate one row per AP
                table.add_row(
                    [
                        idx,  # Zero-based index that the user enters
                        ap.get("name", "Unknown"),  # Human-readable AP name from inventory
                        ap.get("mac", "Unknown"),  # AP MAC address (may include colons)
                        ap.get("model", "Unknown"),  # Hardware model identifier
                        ap.get("status", "Unknown"),  # Connected / disconnected status
                    ]
                )
                index_to_ap[idx] = ap  # Store full dict so we can retrieve MAC by index later

            print("\n" + "=" * 80)
            print(" SELECT ACCESS POINT")
            print("=" * 80)
            print(table)
            print("\nSpecial options:")
            print("  'all' - Select all APs (launches simultaneous captures)")  # Inform user of 'all' option

            logging.info("Displaying AP selection table (%d APs) -- awaiting user input", len(aps))  # Log before prompt
            user_input = self._safe_input(  # Use injected safe_input so EOF is handled identically to main app
                "\nEnter the index number of the AP or 'all': ", context="ap_selection"
            ).strip()
            logging.debug("User input for AP selection: %s", user_input)  # Log raw input for diagnostics

            if user_input.lower() == "all":  # User wants to capture on every AP simultaneously
                print(f"\n! Selected: All APs ({len(aps)} APs)")
                logging.info("User selected all APs: %d APs", len(aps))  # Log aggregate selection
                return "ALL_APS"  # Caller checks for this sentinel to launch multi-AP mode

            if user_input.isdigit():  # Validate that input is a non-negative integer index
                idx = int(user_input)  # Convert to integer for dict lookup
                if idx in index_to_ap:  # Confirm the index is within the displayed range
                    ap_mac = index_to_ap[idx].get("mac")  # Retrieve MAC from the stored AP dict
                    ap_name = index_to_ap[idx].get("name", "Unknown")  # Retrieve name for confirmation message
                    print(f"\n! Selected AP: {ap_name} (MAC: {ap_mac})")
                    logging.info(  # Log successful selection with both name and MAC for audit trail
                        "User selected AP index %d: name=%s mac=%s", idx, ap_name, ap_mac
                    )
                    return ap_mac  # type: ignore[no-any-return]  # Return the MAC to the caller
                else:
                    print("\n! Invalid index")
                    logging.error("Invalid AP index entered by user: %d", idx)  # Log bad index for diagnostics
                    return None
            else:
                print("\n! Please enter a valid index number")
                logging.error("Non-numeric AP selection input: %s", user_input)  # Log unexpected input
                return None

        except Exception as error:  # Catch all exceptions so a single failure does not crash the capture flow
            print(f"\n! Error fetching APs: {error}")
            logging.error(  # Log full traceback so operators can diagnose API failures
                "Exception in PromptNetworkDeviceUtils.select_ap_mac: %s", error, exc_info=True
            )
            return None

    def select_gateway_mac(self, site_id: str) -> str | None:
        """
        Prompt the user to choose a gateway from a site and return its MAC address.

        Args:
            site_id: Mist site ID to scope the gateway inventory query.

        Returns:
            MAC address string of the chosen gateway, or None if cancelled or failed.
        """
        logging.info("Fetching gateway list for site %s to present selection prompt", site_id)  # Log before API call
        try:
            rawdata = mistapi.api.v1.sites.devices.listSiteDevices(  # Fetch gateways only for this site
                self._session, site_id, type="gateway"
            ).data
            if not rawdata:  # No gateways found at this site
                print("\n! No gateways found at the selected site.")
                logging.warning("No gateways found for site_id: %s", site_id)  # Log empty result
                return None

            logging.debug("Received %d gateways for site %s", len(rawdata), site_id)  # Log count after API call

            gateways = sorted(rawdata, key=lambda x: x.get("name", ""))  # Alphabetical sort for readability

            table = PrettyTable()  # Build selection table for terminal display
            table.field_names = ["Index", "Name", "MAC", "Model", "Status"]  # Column headers
            index_to_gateway: dict[int, Any] = {}  # Map display index to gateway dict for MAC retrieval

            for idx, gateway in enumerate(gateways):  # One row per gateway
                table.add_row(
                    [
                        idx,  # Zero-based index for user selection
                        gateway.get("name", "Unknown"),  # Human-readable gateway name
                        gateway.get("mac", "Unknown"),  # Gateway MAC address
                        gateway.get("model", "Unknown"),  # Hardware model identifier
                        gateway.get("status", "Unknown"),  # Connected / disconnected
                    ]
                )
                index_to_gateway[idx] = gateway  # Store full dict so we can look up MAC by index

            print("\n" + "=" * 80)
            print(" SELECT GATEWAY")
            print("=" * 80)
            print(table)

            logging.info("Displaying gateway selection table (%d gateways) -- awaiting user input", len(gateways))
            user_input = self._safe_input(  # Use injected safe_input for consistent EOF handling
                "\nEnter the index number of the gateway: ", context="gateway_selection"
            ).strip()
            logging.debug("User input for gateway selection: %s", user_input)  # Log raw input for diagnostics

            if user_input.isdigit():  # Only accept numeric index values
                idx = int(user_input)  # Convert to integer for lookup
                if idx in index_to_gateway:  # Verify the index is within the displayed table
                    gateway_mac = index_to_gateway[idx].get("mac")  # Retrieve MAC from stored dict
                    gateway_name = index_to_gateway[idx].get("name", "Unknown")  # Retrieve name for confirmation
                    print(f"\n! Selected gateway: {gateway_name} (MAC: {gateway_mac})")
                    logging.info(  # Log successful selection for audit trail
                        "User selected gateway index %d: name=%s mac=%s", idx, gateway_name, gateway_mac
                    )
                    return gateway_mac  # type: ignore[no-any-return]
                else:
                    print("\n! Invalid index")
                    logging.error("Invalid gateway index entered by user: %d", idx)  # Log bad index
                    return None
            else:
                print("\n! Please enter a valid index number")
                logging.error("Non-numeric gateway selection input: %s", user_input)  # Log unexpected input
                return None

        except Exception as error:  # Broad catch keeps capture flow alive on API failures
            print(f"\n! Error fetching gateways: {error}")
            logging.error("Exception in PromptNetworkDeviceUtils.select_gateway_mac: %s", error, exc_info=True)
            return None

    def select_switch_mac(self, site_id: str) -> str | None:
        """
        Prompt the user to choose a switch from a site and return its MAC address.

        Args:
            site_id: Mist site ID to scope the switch inventory query.

        Returns:
            MAC address string of the chosen switch, or None if cancelled or failed.
        """
        logging.info("Fetching switch list for site %s to present selection prompt", site_id)  # Log before API call
        try:
            rawdata = mistapi.api.v1.sites.devices.listSiteDevices(  # Fetch switches only for this site
                self._session, site_id, type="switch"
            ).data
            if not rawdata:  # No switches found at this site
                print("\n! No switches found at the selected site.")
                logging.warning("No switches found for site_id: %s", site_id)  # Log empty result
                return None

            logging.debug("Received %d switches for site %s", len(rawdata), site_id)  # Log count after API call

            switches = sorted(rawdata, key=lambda x: x.get("name", ""))  # Alphabetical sort for readability

            table = PrettyTable()  # Build selection table for terminal display
            table.field_names = ["Index", "Name", "MAC", "Model", "Status"]  # Column headers
            index_to_switch: dict[int, Any] = {}  # Map display index to switch dict for MAC retrieval

            for idx, switch in enumerate(switches):  # One row per switch
                table.add_row(
                    [
                        idx,  # Zero-based index for user selection
                        switch.get("name", "Unknown"),  # Human-readable switch name
                        switch.get("mac", "Unknown"),  # Switch MAC address
                        switch.get("model", "Unknown"),  # Hardware model identifier
                        switch.get("status", "Unknown"),  # Connected / disconnected
                    ]
                )
                index_to_switch[idx] = switch  # Store full dict for MAC lookup by index

            print("\n" + "=" * 80)
            print(" SELECT SWITCH")
            print("=" * 80)
            print(table)

            logging.info("Displaying switch selection table (%d switches) -- awaiting user input", len(switches))
            user_input = self._safe_input(  # Use injected safe_input for consistent EOF handling
                "\nEnter the index number of the switch: ", context="switch_selection"
            ).strip()
            logging.debug("User input for switch selection: %s", user_input)  # Log raw input for diagnostics

            if user_input.isdigit():  # Only accept numeric index values
                idx = int(user_input)  # Convert to integer for lookup
                if idx in index_to_switch:  # Verify the index is within the displayed table
                    switch_mac = index_to_switch[idx].get("mac")  # Retrieve MAC from stored dict
                    switch_name = index_to_switch[idx].get("name", "Unknown")  # Retrieve name for confirmation
                    print(f"\n! Selected switch: {switch_name} (MAC: {switch_mac})")
                    logging.info(  # Log successful selection for audit trail
                        "User selected switch index %d: name=%s mac=%s", idx, switch_name, switch_mac
                    )
                    return switch_mac  # type: ignore[no-any-return]
                else:
                    print("\n! Invalid index")
                    logging.error("Invalid switch index entered by user: %d", idx)  # Log bad index
                    return None
            else:
                print("\n! Please enter a valid index number")
                logging.error("Non-numeric switch selection input: %s", user_input)  # Log unexpected input
                return None

        except Exception as error:  # Broad catch keeps capture flow alive on API failures
            print(f"\n! Error fetching switches: {error}")
            logging.error("Exception in PromptNetworkDeviceUtils.select_switch_mac: %s", error, exc_info=True)
            return None

    def select_ports_from_device(  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        self,
        site_id: str,
        device_mac: str,
        device_type: str = "switch",
        return_available: bool = False,
    ):
        """
        Prompt the user to select one or more ports from a switch or gateway.

        Fetches live port status from the Mist Stats API and falls back to device
        config when stats are unavailable (e.g., device offline).  Displays a
        numbered table of UP ports and accepts index-based, comma-separated, or
        range-style selections.  Enforces the Mist API limit of 6 ports per capture.

        Args:
            site_id: Mist site ID where the device is located.
            device_mac: MAC address of the target device (with or without colons).
            device_type: Either "switch" or "gateway" -- controls which API is used.
            return_available: When True, returns (selected_ports, all_available_ports)
                              so callers can expand an empty selection to all ports.

        Returns:
            When return_available is False: list of port name strings, or None on failure.
            When return_available is True: (selected_ports, available_ports) tuple,
            or None on failure.  selected_ports is [] when user chose all ports.
        """
        logging.info(  # Log device type, MAC, and site before any API calls
            "Fetching port information for %s %s at site %s", device_type, device_mac, site_id
        )

        try:
            normalized_input_mac = (  # Normalise input MAC: strip colons/hyphens, lowercase for comparison
                str(device_mac).replace(":", "").replace("-", "").lower()
            )
            logging.debug("Normalised input MAC for comparison: %s", normalized_input_mac)

            devices_response = mistapi.api.v1.sites.devices.listSiteDevices(  # Fetch all devices of specified type
                self._session, site_id, type=device_type
            )
            devices = devices_response.data  # List of device dicts from the API

            device = self._find_device_by_mac(devices, normalized_input_mac, device_mac)  # Match by normalised MAC
            if not device:  # Device not found in the site inventory
                print(f"\n! Could not find {device_type} with MAC {device_mac}")
                logging.error(  # Log full available MAC list to help diagnose stale inventory
                    "Device not found with MAC: %s (normalised: %s). Available: %s",
                    device_mac,
                    normalized_input_mac,
                    [d.get("mac") for d in devices],
                )
                return None

            device_id = device.get("id")  # Mist UUID needed for stats and config API calls
            device_name = device.get("name", "Unknown")  # Human-readable name for display messages

            port_stat = self._fetch_port_stats(  # Retrieve per-port status dict (may be from stats or config fallback)
                site_id, device_id, device_mac, device_type
            )

            port_config = self._fetch_port_config(  # Retrieve device config for port profiles and descriptions
                site_id, device_id
            )

            port_to_config = self._build_port_to_config_map(  # Expand range keys like 'ge-0/0/0-5' to individual ports
                port_config
            )

            if not port_stat:  # Stats completely unavailable -- try building from config instead
                port_stat = self._build_port_stat_from_config(  # Returns fake port_stat dict using config values
                    port_config, device_id, device_type, device_name
                )
                if port_stat is None:  # Config fallback also failed -- nothing to show
                    return None

            available_ports = self._filter_and_sort_ports(port_stat)  # Exclude mgmt ports, keep UP ports, sort

            if not available_ports:  # No usable ports remain after filtering
                print(f"\n! No network ports available for {device_type}: {device_name}")
                logging.warning("No user-facing ports found for device %s", device_id)
                return None

            return self._prompt_port_selection(  # Present table and collect user choice
                available_ports, port_to_config, device_mac, device_name, device_type, return_available
            )

        except Exception as error:  # Catch all so one bad device doesn't abort the whole capture flow
            print(f"\n! Error fetching port information: {error}")
            logging.error("Exception in PromptNetworkDeviceUtils.select_ports_from_device: %s", error, exc_info=True)
            return None

    # ------------------------------------------------------------------
    # Private helpers -- called only by select_ports_from_device
    # ------------------------------------------------------------------

    def _find_device_by_mac(  # type: ignore[no-untyped-def]
        self, devices: list[Any], normalized_target: str, original_mac: str
    ) -> Any | None:
        """Return the first device dict whose MAC matches normalized_target, or None."""
        for dev in devices:  # Iterate over every device returned by the API
            dev_mac = dev.get("mac", "")  # Raw MAC from API (may include colons)
            normalized_dev_mac = str(dev_mac).replace(":", "").replace("-", "").lower()  # Normalise for comparison
            logging.debug(  # Log each comparison so failed matches are traceable
                "Comparing device %s: %s (normalised: %s)",
                dev.get("name", "Unknown"),
                dev_mac,
                normalized_dev_mac,
            )
            if normalized_dev_mac == normalized_target:  # Exact match after normalisation
                logging.debug("MAC match found for device: %s", dev.get("name", "Unknown"))
                return dev  # Return the matching device dict immediately
        logging.error(  # Log the full MAC we were looking for to help operators diagnose mismatches
            "No device found matching normalised MAC: %s (original: %s)", normalized_target, original_mac
        )
        return None  # No match found in inventory

    def _fetch_port_stats(  # type: ignore[no-untyped-def]
        self, site_id: str, device_id: str, device_mac: str, device_type: str
    ) -> dict[str, Any]:
        """
        Retrieve per-port status data for a switch, gateway, or AP.

        Uses searchSiteSwOrGwPorts for switches/gateways (richer per-port data)
        and getSiteDeviceStats for APs (uses port_stat embedded in device stats).

        Returns a dict keyed by port_id/port_name containing status attributes.
        """
        port_stat: dict[str, Any] = {}  # Accumulate port stats keyed by port name

        if device_type in ["switch", "gateway"]:  # Switches and gateways have a dedicated port search endpoint
            logging.info(  # Log before the API call so failures are easy to pin-point
                "Fetching switch/gateway port stats via searchSiteSwOrGwPorts for device %s", device_id
            )
            try:
                ports_search_response = mistapi.api.v1.sites.stats.searchSiteSwOrGwPorts(  # Dedicated port stats API
                    self._session, site_id, mac=device_mac, limit=1000
                )
                ports_results = ports_search_response.data.get("results", [])  # List of per-port stat dicts
                logging.info(  # Log result count after API call for diagnostics
                    "Retrieved %d port stat entries from searchSiteSwOrGwPorts", len(ports_results)
                )
                for port_obj in ports_results:  # Build dict keyed by port_id for O(1) lookup
                    port_id = port_obj.get("port_id")
                    if port_id:  # Only store entries that have a port identifier
                        port_stat[port_id] = port_obj
                if port_stat:
                    logging.info(  # Log successful conversion to dict with sample data for quick sanity check
                        "Converted %d switch/gateway ports to stat dict", len(port_stat)
                    )
                else:
                    logging.warning(  # Warn if API returned results but none had a port_id
                        "searchSiteSwOrGwPorts returned no usable port data for device %s", device_mac
                    )
            except Exception as port_search_error:  # Log and swallow -- caller will fall back to config
                logging.error("Error fetching switch/gateway port stats: %s", port_search_error)
        else:  # AP devices use the general device stats endpoint with embedded port_stat dict
            logging.info("Fetching AP port stats via getSiteDeviceStats for device %s", device_id)
            stats_response = mistapi.api.v1.sites.stats.getSiteDeviceStats(  # AP stats endpoint
                self._session, site_id, device_id
            )
            stats_data = stats_response.data  # Full device stats dict
            if "port_stat" in stats_data:  # APs embed port stats directly in device stats
                port_stat = stats_data.get("port_stat", {})
                logging.info("Found port_stat (AP-style) with %d ports", len(port_stat))
            else:
                logging.warning("No port_stat found in AP stats for device %s", device_id)

        return port_stat  # May be empty if device is offline -- caller handles this case

    def _fetch_port_config(self, site_id: str, device_id: str) -> dict[str, Any]:  # type: ignore[no-untyped-def]
        """
        Retrieve device configuration and return the port_config section.

        Falls back to an empty dict if the device config API call fails.
        """
        logging.debug("Fetching device config for port profiles and descriptions from device %s", device_id)
        try:
            device_config_response = mistapi.api.v1.sites.devices.getSiteDevice(  # Get full device config
                self._session, site_id, device_id
            )
            port_config: dict[str, Any] = device_config_response.data.get("port_config", {})
            logging.debug("Retrieved port_config with %d entries for device %s", len(port_config), device_id)
            return port_config  # Dict keyed by port range strings like 'ge-0/0/0-5'
        except Exception as cfg_error:  # Non-fatal: port profiles/descriptions will just be missing
            logging.warning("Could not fetch device config for port details: %s", cfg_error)
            return {}  # Return empty dict so callers don't need to guard for None

    def _build_port_to_config_map(self, port_config: dict[str, Any]) -> dict[str, Any]:
        """
        Expand range-based port config keys to individual port name mappings.

        Converts {'ge-0/0/0-5': {...}} to {'ge-0/0/0': {...}, 'ge-0/0/1': {...}, ...}
        so per-port config lookups are O(1).
        """
        port_to_config: dict[str, Any] = {}  # Output dict: individual port name -> config dict
        if not port_config:  # Nothing to expand -- return empty dict immediately
            logging.warning("No port_config available -- port profiles and descriptions will be missing")
            return port_to_config

        logging.info(  # Log before expansion so operator can see the input size
            "Expanding %d port_config entries to individual port mappings", len(port_config)
        )
        for port_range_key, cfg in port_config.items():  # Iterate over range-keyed config entries
            expanded_ports = self._expand_port_range(port_range_key)  # Use injected expander callable
            logging.debug(  # Log each expansion for detailed diagnostics
                "Port config key '%s' expands to %d ports", port_range_key, len(expanded_ports)
            )
            for individual_port in expanded_ports:  # Map each individual port to the shared config dict
                port_to_config[individual_port] = cfg
        logging.info("Built port_to_config map with %d individual port entries", len(port_to_config))
        return port_to_config

    def _build_port_stat_from_config(  # type: ignore[no-untyped-def]
        self,
        port_config: dict[str, Any],
        device_id: str,
        device_type: str,
        device_name: str,
    ) -> dict[str, Any] | None:
        """
        Build a synthetic port_stat dict from device config when live stats are unavailable.

        Used as a fallback when the device is offline or has not yet reported stats.
        Returns None if neither stats nor config are available.
        """
        logging.warning(  # Warn before fallback so operator knows stats are not live
            "No port_stat from API for device %s -- attempting config-based fallback", device_id
        )
        if not port_config:  # Config also unavailable -- nothing to show
            print(f"\n! No port information available for {device_type}: {device_name}")
            print("  This device may be offline or not yet reporting statistics.")
            logging.warning("No port_stat or port_config found for device %s", device_id)
            return None

        port_stat: dict[str, Any] = {}  # Build synthetic stats from config values
        try:
            logging.info(  # Log before iteration so operator knows a fallback build is starting
                "Building synthetic port_stat from %d port_config entries for device %s",
                len(port_config),
                device_id,
            )
            for port_range_key, port_cfg in port_config.items():  # Iterate over configured port ranges
                expanded_ports = self._expand_port_range(port_range_key)  # Expand range to individual ports
                logging.debug(  # Log expansion count for diagnostics
                    "Expanded port range '%s' to %d ports", port_range_key, len(expanded_ports)
                )
                for individual_port in expanded_ports:  # Create a synthetic stat entry per port
                    usage = port_cfg.get("usage", "")  # Usage profile name (empty or 'disabled' means port off)
                    port_up = usage not in ["disabled", "", None]  # Derive UP state from usage profile
                    speed_value = port_cfg.get("speed", "N/A")  # Configured speed (may differ from actual)
                    duplex_value = port_cfg.get("duplex", "N/A")  # Configured duplex setting
                    full_duplex = duplex_value in ("full", "auto")  # Normalise to bool for display
                    port_stat[individual_port] = {  # Synthetic entry -- mark as fallback for display notice
                        "up": port_up,
                        "speed": speed_value,
                        "full_duplex": full_duplex,
                        "duplex": duplex_value,
                        "_fallback": True,  # Flag so the table header shows a caveat to the user
                    }
            logging.info(  # Log result size after building synthetic stats
                "Built synthetic port_stat with %d individual port entries for device %s",
                len(port_stat),
                device_id,
            )
        except Exception as config_error:  # Log and return None if config parsing fails
            print(f"\n! No port information available for {device_type}: {device_name}")
            print("  This device may be offline or not yet reporting statistics.")
            logging.error("Could not build port_stat from device config: %s", config_error)
            return None

        return port_stat  # Caller will proceed with synthetic stats and display the fallback notice

    def _filter_and_sort_ports(  # type: ignore[no-untyped-def]
        self, port_stat: dict[str, Any]
    ) -> list[tuple[str, Any]]:
        """
        Filter management/service ports and DOWN ports, then sort remaining UP ports naturally.

        Returns a list of (port_name, port_info) tuples ordered by natural sort key.
        """
        exclude_prefixes = [  # Prefixes for management, loopback, and internal Junos virtual ports
            "fxp",
            "em",
            "me",
            "vme",
            "irb",
            "lo",
            "vlan",
            "bme",
            "cbp",
            "jsrv",
            "pip",
        ]
        available_ports = []  # Accumulate (name, info) tuples for UP user-facing ports

        for port_name, port_info in port_stat.items():  # Iterate over all ports in the stat dict
            if any(port_name.startswith(prefix) for prefix in exclude_prefixes):  # Skip management ports
                logging.debug("Excluding management/service port: %s", port_name)
                continue
            if not port_info.get("up", False):  # Skip DOWN ports -- users can't capture on them
                logging.debug("Excluding DOWN port: %s", port_name)
                continue
            available_ports.append((port_name, port_info))  # Keep this UP user-facing port

        def _natural_sort_key(port_tuple: tuple[str, Any]) -> list[Any]:  # type: ignore[return]
            """Split port name on digit runs for natural (human) sort order."""
            parts = re.split(r"(\d+)", port_tuple[0])  # Split 'ge-0/0/1' into ['ge-', '0', '/', '0', '/', '1', '']
            return [int(part) if part.isdigit() else part for part in parts]  # Convert digit runs to ints for sorting

        available_ports = sorted(available_ports, key=_natural_sort_key)  # Natural sort: ge-0/0/0 before ge-0/0/10
        logging.debug("Filtered to %d UP user-facing ports after exclusions", len(available_ports))
        return available_ports  # Sorted list of (name, info) tuples ready for display

    def _prompt_port_selection(  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912
        self,
        available_ports: list[tuple[str, Any]],
        port_to_config: dict[str, Any],
        device_mac: str,
        device_name: str,
        device_type: str,
        return_available: bool,
    ):
        """
        Render the port selection table and collect the user's choice.

        Enforces the Mist API 6-port-per-capture limit.  Returns the selected
        port name list (or tuple with available ports if return_available is True),
        or None on failure/cancellation.
        """
        table = self._build_port_table(available_ports, port_to_config)  # Render the formatted port table

        using_fallback = any(  # Check if any port came from config fallback so we can show a caveat
            port_info.get("_fallback", False) for _, port_info in available_ports
        )

        print("\n" + "=" * 80)
        print(f" SELECT PORTS FROM {device_type.upper()}: {device_name}")  # nosec B608
        print("=" * 80)
        print(f"  Device MAC: {device_mac}")
        print(f"  Available Ports: {len(available_ports)}")
        if using_fallback:  # Inform user that speed/duplex came from config, not live stats
            print("  NOTE: Speed/Duplex showing configured values (device stats unavailable)")
        print("=" * 80)
        print(table)
        print("\n" + "!" * 80)
        print("  API LIMITATION: Maximum 6 ports per capture")
        print("!" * 80)
        print("\nPort Selection Options:")
        print("  - Enter a single index (e.g., '0') for one port")
        print("  - Enter multiple indices separated by commas (e.g., '0,2,5')")
        print("  - Enter a range (e.g., '0-3' for ports 0, 1, 2, 3)")
        if len(available_ports) <= 6:  # Only offer 'all' when it fits within the API limit
            print("  - Press Enter with no input to capture on ALL ports (default)")
        else:
            print("  - Press Enter with no input to capture on ALL ports (NOT AVAILABLE - exceeds 6 port limit)")
        print("  - Enter 'c' to cancel")

        logging.info(  # Log before the prompt so the operator knows we are waiting on user input
            "Displaying port selection table for %s %s (%d UP ports) -- awaiting user input",
            device_type,
            device_mac,
            len(available_ports),
        )
        user_input = self._safe_input(  # Injected safe_input handles EOF and empty-value edge cases
            "\nEnter your choice (up to 6 ports): ", context="port_selection", allow_empty=True
        ).strip()
        logging.debug("User input for port selection: %s", user_input)  # Log raw input for diagnostics

        if user_input.lower() == "c":  # User explicitly cancelled port selection
            print("\n! Port selection cancelled")
            logging.info("Port selection cancelled by user")
            return None

        index_to_port: dict[int, str] = {  # Build index -> port_name map from the sorted available list
            idx: port_name for idx, (port_name, _) in enumerate(available_ports)
        }

        if not user_input or user_input.lower() == "all":  # Empty input means all available ports
            return self._handle_all_ports_selection(available_ports, return_available)

        return self._parse_port_indices(user_input, index_to_port, return_available, available_ports)

    def _build_port_table(  # type: ignore[no-untyped-def]
        self, available_ports: list[tuple[str, Any]], port_to_config: dict[str, Any]
    ) -> PrettyTable:
        """Build and return a PrettyTable of available ports with status, speed, and config info."""
        table = PrettyTable()  # Create table with column headers matching operator expectations
        table.field_names = ["Index", "Port Name", "Status", "Speed", "Duplex", "Profile", "Description"]
        table.max_width = 120  # Limit overall width to fit standard 120-char terminals
        table.align["Description"] = "l"  # Left-align description so long text wraps predictably
        table.align["Profile"] = "l"  # Left-align profile name for readability

        for idx, (port_name, port_info) in enumerate(available_ports):  # One row per available port
            status = "UP" if port_info.get("up", False) else "DOWN"  # Human-readable link state

            speed = port_info.get("speed", "N/A")  # Raw speed value from API or config
            speed_str = self._format_speed(speed)  # Convert raw value to human-readable string

            duplex_value = port_info.get("duplex", "")  # Raw duplex value from API or config
            duplex_str = self._format_duplex(duplex_value, port_info.get("full_duplex", False))

            port_cfg = port_to_config.get(port_name, {})  # Look up per-port config for profile/description
            port_profile = port_cfg.get("port_profile", "N/A")  # VLAN or access profile name
            port_description = port_cfg.get("description", "")  # Operator-entered description
            if len(port_description) > 30:  # Truncate long descriptions to keep table readable
                port_description = port_description[:27] + "..."
            if not port_description:  # Use dash when no description is configured
                port_description = "-"

            table.add_row([idx, port_name, status, speed_str, duplex_str, port_profile, port_description])

        return table  # Fully populated PrettyTable ready to print

    @staticmethod
    def _format_speed(speed: Any) -> str:
        """Convert a raw speed value (string or int) to a human-readable Mbps string."""
        if isinstance(speed, str):  # API may return string like 'auto', '1G', '10G'
            speed_upper = speed.upper()
            if speed_upper == "AUTO":  # Auto-negotiated speed -- just show 'Auto'
                return "Auto"
            if speed_upper.endswith("G"):  # e.g. '1G' -> '1000 Mbps'
                try:
                    return f"{int(speed_upper[:-1]) * 1000} Mbps"
                except ValueError:
                    return speed  # Fallback: return raw value if parse fails
        if isinstance(speed, (int, float)) and speed > 0:  # Numeric value already in Mbps
            return f"{speed} Mbps"
        return "N/A"  # Unknown or zero speed

    @staticmethod
    def _format_duplex(duplex_value: str, full_duplex_flag: bool) -> str:
        """Return a human-readable duplex string from API value or bool fallback."""
        if duplex_value:  # Prefer the explicit string value from the API
            mapping = {"full": "Full", "half": "Half", "auto": "Auto"}
            return mapping.get(duplex_value.lower(), str(duplex_value).capitalize())  # Use mapping or capitalise
        return "Full" if full_duplex_flag else "Half"  # Fall back to bool flag when string is absent

    def _handle_all_ports_selection(  # type: ignore[no-untyped-def]
        self,
        available_ports: list[tuple[str, Any]],
        return_available: bool,
    ):
        """Handle the 'select all ports' case and enforce the 6-port API limit."""
        if len(available_ports) > 6:  # Mist API enforces a hard 6-port cap per capture
            print(f"\n! ERROR: Cannot select all {len(available_ports)} ports " "- API maximum is 6 ports per capture")
            print("  Please select up to 6 specific ports from the list above")
            logging.error(  # Log the violation so operators can audit it
                "User attempted to select all %d ports -- exceeds API limit of 6", len(available_ports)
            )
            return None

        print(f"\n! Selected ALL {len(available_ports)} ports for capture")
        logging.info("User selected all %d ports (within 6-port limit)", len(available_ports))
        if return_available:  # Caller wants the full available list alongside the empty selection sentinel
            return [], available_ports
        return []  # Empty list signals 'all ports' to the caller

    def _parse_port_indices(  # type: ignore[no-untyped-def]  # noqa: C901
        self,
        user_input: str,
        index_to_port: dict[int, str],
        return_available: bool,
        available_ports: list[tuple[str, Any]],
    ):
        """
        Parse comma-separated and range-style port index input and return selected port names.

        Supports formats: '0', '0,2,5', '0-3', or combinations thereof.
        Warns on out-of-range indices without aborting the whole selection.
        Returns None on parse errors or if the selection exceeds the 6-port limit.
        """
        selected_indices: set[int] = set()  # Use a set to deduplicate repeated indices

        try:
            parts = user_input.split(",")  # Split on commas first to handle multiple segments
            for part in parts:
                part = part.strip()  # Remove surrounding whitespace from each segment

                if "-" in part:  # Range notation: '2-5' -> indices 2, 3, 4, 5
                    range_parts = part.split("-")
                    if len(range_parts) == 2:  # Valid range has exactly two endpoints
                        start_idx = int(range_parts[0].strip())  # Inclusive start
                        end_idx = int(range_parts[1].strip())  # Inclusive end
                        for i in range(start_idx, end_idx + 1):  # Expand range to individual indices
                            if i in index_to_port:  # Only accept indices within the displayed table
                                selected_indices.add(i)
                            else:
                                print(f"\n! Warning: Index {i} is out of range, skipping")
                                logging.warning("Invalid port index in range: %d", i)
                else:  # Single index
                    idx = int(part)  # Must be a numeric string
                    if idx in index_to_port:  # Validate against displayed table size
                        selected_indices.add(idx)
                    else:
                        print(f"\n! Warning: Index {idx} is out of range, skipping")
                        logging.warning("Invalid port index: %d", idx)

            if not selected_indices:  # No valid indices after parsing -- nothing to capture
                print("\n! No valid ports selected")
                logging.error("No valid port indices provided by user")
                return None

            selected_ports = [index_to_port[idx] for idx in sorted(selected_indices)]  # Ordered list of port names

            if len(selected_ports) > 6:  # Enforce Mist API hard limit of 6 ports per capture
                print(f"\n! ERROR: Selected {len(selected_ports)} ports, but API maximum is 6 ports per capture")
                print("  Please refine your selection to 6 or fewer ports")
                logging.error(  # Log the violation for audit trail
                    "User selected %d ports -- exceeds API limit of 6", len(selected_ports)
                )
                return None

            print(f"\n! Selected {len(selected_ports)} port(s): {', '.join(selected_ports)}")
            logging.info("User selected ports: %s", selected_ports)  # Log final selection after validation

            if return_available:  # Caller wants both the selection and the full available list
                return selected_ports, available_ports
            return selected_ports  # Return just the selected port name list

        except ValueError as value_error:  # User entered non-numeric text -- cannot parse as index
            print(f"\n! Invalid input format: {value_error}")
            logging.error("Port selection parse error: %s", value_error)
            return None
