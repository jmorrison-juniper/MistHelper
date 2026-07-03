"""Per-row override detection and per-port report-entry construction."""

from __future__ import annotations  # Defer annotation evaluation for forward refs

import logging  # Standard library structured logging (use %s formatting per project standard)
from typing import Any  # Generic typing for CSV dict rows and API JSON payloads


class OverrideClassifier:  # Namespace for stateless override classification helpers.
    """Classify configured ports as overridden vs template-aligned and shape report rows."""

    @staticmethod
    def classify(row: dict[str, Any], target_ports: list[str]) -> list[str]:  # Public entry point.
        """Return the subset of target_ports that show non-default overrides in row."""
        logging.info("Classifying overrides across %d target ports for one device row", len(target_ports))  # before
        overridden: list[str] = []  # Accumulator for ports whose flattened CSV fields show overrides
        for port_name in target_ports:  # Walk every WAN port the operator marked as managed in .env
            if OverrideClassifier._port_has_override(row, port_name):  # Delegate per-port decision to helper
                overridden.append(port_name)  # Capture port so the second pass fetches live device data
        logging.debug("Classified %d overridden ports for row", len(overridden))  # after action summary
        return overridden  # Caller skips live API calls for any device that returns an empty list here

    @staticmethod
    def _field_matches_port(field_name: str, port_name: str) -> bool:  # Extracted to keep _port_has_override CC <= 5.
        """Return True if field_name is a port_config_<port> column (either separator variant)."""
        # WHY: extracting the 'or' predicate cuts one branch out of _port_has_override.
        prefix_underscore = f"port_config_{port_name}_"  # Flattened CSV variant using underscore separator.
        prefix_dot = f"port_config_{port_name}."  # Flattened CSV variant using dot separator.
        return field_name.startswith(prefix_underscore) or field_name.startswith(prefix_dot)  # Either variant qualifies.

    @staticmethod
    def _value_is_override(value: Any) -> bool:  # Extracted so _port_has_override stays CC <= 5.
        """Return True if value normalizes to a meaningful (non-blank/null/none) override."""
        # WHY: keeps the cleaning + comparison out of the branching hotspot in _port_has_override.
        cleaned = (value or "").strip().lower()  # Normalize so blank/null/none all map to "unset".
        return cleaned not in ("", "null", "none")  # Anything else counts as a real override value.

    @staticmethod
    def _port_has_override(row: dict[str, Any], port_name: str) -> bool:  # CC 5 after helper extraction.
        """Return True if any port_config_<port> CSV field carries a non-empty override value."""
        for field_name, value in row.items():  # Single linear pass over the flattened CSV columns.
            if not OverrideClassifier._field_matches_port(field_name, port_name):  # Column belongs to another port.
                continue  # Skip columns that do not belong to the port currently under consideration.
            if "_vpn_paths_" in field_name:  # VPN path fields are shared across templates.
                continue  # Ignore VPN path fields: present on every device, never count as overrides.
            if OverrideClassifier._value_is_override(value):  # Any meaningful value flags this port.
                return True  # Any meaningful value here means this port deviates from the template.
        return False  # No managed field on this port carries an override value.

    @staticmethod
    def build_port_entry(
        device_info: dict[str, Any],
        port_name: str,
        port_config: dict[str, Any],
        interface_stat: dict[str, Any],
    ) -> dict[str, Any]:  # Public shaper called once per overridden port.
        """Build one CSV row describing a single overridden port using live device data."""
        logging.debug("Building port entry %s for device %s", port_name, device_info.get("device_name"))  # trace
        ip_config = port_config.get("ip_config", {})  # IP-related fields nest under ip_config on live device
        config_type_display = OverrideClassifier._format_config_type(ip_config.get("type", ""))  # display label
        port_status = "up" if interface_stat and interface_stat.get("up", False) else "down"  # operational state
        admin_status = "disabled" if port_config.get("disabled", False) else "enabled"  # configured state
        return OverrideClassifier._assemble_entry(  # Hand off to assembler to keep this method's CC small
            device_info=device_info,
            port_name=port_name,
            port_config=port_config,
            ip_config=ip_config,
            display=(config_type_display, port_status, admin_status),
        )

    @staticmethod
    def _format_config_type(config_type: str) -> str:  # Small display-label normalizer.
        """Normalize raw API config type strings to the CSV display label operators expect."""
        if config_type == "dhcp":  # Canonical DHCP variant.
            return "DHCP"  # Operators see "DHCP" rather than the lowercase API value
        if config_type == "static":  # Canonical STATIC variant.
            return "STATIC"  # Operators see "STATIC" rather than the lowercase API value
        return config_type.upper() if config_type else "UNKNOWN"  # Unknown/empty maps to UNKNOWN per legacy

    @staticmethod
    def _port_detail_columns(
        port_config: dict[str, Any],
        ip_config: dict[str, Any],
        display: tuple[str, str, str],
    ) -> dict[str, Any]:  # Extracted to keep _assemble_entry under STRUCT-LENGTH.
        """Return the port-detail columns, preserving legacy column order."""
        # WHY: pulling the port-detail chunk out drops _assemble_entry from 27 to <25 lines.
        config_type_display, port_status, admin_status = display  # Unpack the precomputed display labels.
        return {  # Column order matches legacy consumer expectations exactly.
            "port_description": port_config.get("description", ""),  # Free-text from device config
            "port_status": port_status,  # Operational link state at observation time
            "port_admin_status": admin_status,  # Configured admin state (enabled/disabled)
            "port_gateway_ip": ip_config.get("gateway", ""),  # IP gateway assigned to the port
            "port_ip_address": ip_config.get("ip", ""),  # IP address assigned to the port
            "port_netmask": ip_config.get("netmask", ""),  # Subnet mask assigned to the port
            "port_config_type": config_type_display,  # DHCP/STATIC/UNKNOWN display label
            "port_usage": port_config.get("usage", ""),  # Mist role (wan/lan/etc)
            "overridden_from_template": "Yes",  # Constant flag so downstream filters can match easily
        }

    @staticmethod
    def _assemble_entry(
        device_info: dict[str, Any],
        port_name: str,
        port_config: dict[str, Any],
        ip_config: dict[str, Any],
        display: tuple[str, str, str],
    ) -> dict[str, Any]:  # Final CSV row composer.
        """Compose the final CSV row dict in the exact column order legacy consumers expect."""
        return {  # Column ordering is preserved verbatim from the original GatewayOverrideAnalyzer
            "gateway_device_name": device_info["device_name"],  # Reporting key for operator triage
            "site_name": device_info["site_name"],  # Human-readable site label resolved earlier
            "template_name": device_info["template_name"],  # Template the device was assigned to
            "port_name": port_name,  # Specific port that diverges from the template
            **OverrideClassifier._port_detail_columns(port_config, ip_config, display),  # Port-detail block.
            "device_id": device_info.get("device_id", ""),  # Mist device UUID for cross-reference
            "site_id": device_info["site_id"],  # Mist site UUID for cross-reference
            "template_id": device_info["template_id"],  # Mist template UUID for cross-reference
        }
