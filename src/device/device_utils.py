"""DeviceUtils -- centralized device helper utilities.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 6).
Provides device lookups, port parsing, and MAC address helpers shared across
menus, capture modules, and export utilities.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import importlib  # WHY: lazy MistHelper import to avoid circular load.
import logging  # WHY: emit structured trace for API + fallback warnings.
import re  # WHY: parse port-range prefixes like ``ge-0/0/0-2``.
from typing import Any  # WHY: duck-typed device dicts + Mist API responses.

import mistapi  # WHY: dotted-path API resolution for site device list.


class DeviceUtils:  # Device helper utilities.
    """Centralized device-related utilities for lookups, port parsing, and MAC operations."""

    @staticmethod
    def get_all_ap_macs_from_site(site_id: str) -> list[str]:  # Get all AP MACs for a site.
        """Fetch all AP MAC addresses from a site.

        Args:
            site_id: The site ID to fetch APs from.

        Returns:
            List of AP MAC addresses, or empty list if error/none found.
        """
        logging.debug("Fetching all AP MACs for site: %s", site_id)  # Log before AP fetch.

        try:
            apisession = importlib.import_module("MistHelper").apisession  # WHY: lazy fetch of live session
            rawdata = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id, type="ap").data
            if not rawdata:  # Handle empty AP set.
                logging.warning("No APs found for site_id: %s", site_id)  # Log no APs found.
                return []  # Return empty list.

            ap_macs = [ap.get("mac") for ap in rawdata if ap.get("mac")]  # Collect AP MAC addresses.
            logging.info("Found %s AP MACs at site", len(ap_macs))  # Log AP MAC count.
            return ap_macs  # Return AP MACs.

        except Exception as error:  # Catch fetch errors.
            logging.exception("Exception in DeviceUtils.get_all_ap_macs_from_site: %s", error)  # Log the exception.
            return []  # Return empty on error.

    @staticmethod
    def expand_port_range_string(port_range_string: str) -> list[str]:  # Expand a port-range string.
        """Expand a port range string from device config into individual port names.

        Examples:
            "ge-0/0/0" -> ["ge-0/0/0"]
            "ge-0/0/0-2" -> ["ge-0/0/0", "ge-0/0/1", "ge-0/0/2"]
            "ge-0/0/0-2, ge-0/1/2-3" -> ["ge-0/0/0", "ge-0/0/1", "ge-0/0/2", "ge-0/1/2", "ge-0/1/3"]
            "mge-0/2/0, xe-0/1/0-3" -> ["mge-0/2/0", "xe-0/1/0", "xe-0/1/1", "xe-0/1/2", "xe-0/1/3"]

        Args:
            port_range_string: Port name or range specification from port_config.

        Returns:
            List of individual port names.
        """
        expanded_ports = []  # Accumulator for expanded ports.

        # Split by comma to handle multiple ranges
        port_parts = [part.strip() for part in port_range_string.split(",")]  # Split on comma into parts.

        for port_part in port_parts:  # Process each part.
            expanded_ports.extend(DeviceUtils._expand_one_port_part(port_part))  # Expand range or keep literal port

        return expanded_ports  # Return expanded port list.

    @staticmethod
    def _expand_one_port_part(port_part: str) -> list[str]:  # Expand a single port token into concrete port names
        """Expand one port token: a 'prefix/N-M' range -> [prefix/N..prefix/M]; anything else -> [port_part]."""
        if "-" not in port_part:  # Not a range expression
            return [port_part]  # Single literal port name
        match = re.match(r"^(.+/)(\d+)-(\d+)$", port_part)  # Match prefix plus numeric start-end range
        if not match:  # Could not parse as a range
            return [port_part]  # Keep the literal token
        prefix = match.group(1)  # for example, "ge-0/0/"
        start_num = int(match.group(2))  # Range start (for example, 0)
        end_num = int(match.group(3))  # Range end (for example, 2)
        return [f"{prefix}{port_num}" for port_num in range(start_num, end_num + 1)]  # Concrete ports across the range

    @staticmethod
    def _warn_degraded_identifier(value: str, prior_fields: str, key: str) -> None:
        """Log a warning when ``key`` is used as identifier because ``prior_fields`` were blank."""
        if not prior_fields:  # First-choice field was non-empty; nothing degraded
            return
        logging.warning(  # Warn that earlier identifier fields are missing
            "Device %s missing %s field, using %s as identifier",  # Format string
            value,
            prior_fields,
            key,  # Substitute the actual value and missing fields
        )

    @staticmethod
    def get_device_identifier(device: dict[str, Any], warn_on_missing: bool = False) -> str:
        """Return best available identifier for a device: name -> serial -> id -> 'UNKNOWN'."""
        for key, prior_fields in (("name", ""), ("serial", "name"), ("id", "name and serial")):
            value = device.get(key, "").strip()  # Read candidate identifier from device record
            if value:  # Found a non-empty identifier
                if warn_on_missing:  # Operator wants visibility into fallback chain
                    DeviceUtils._warn_degraded_identifier(value, prior_fields, key)  # Emit only when truly degraded
                return value  # type: ignore[no-any-return]
        if warn_on_missing:  # All identifier fields blank -- last-resort fallback
            logging.warning("Device found with no name, serial, or id - using 'UNKNOWN'")  # Final warning
        return "UNKNOWN"  # Last-resort placeholder id
