"""Persist the WAN override compliance report and print the operator summary."""

from __future__ import annotations  # Defer annotation evaluation for forward refs

import csv  # Standard library CSV writer used for the empty-result fast path
import logging  # Standard library structured logging
from typing import Any  # Generic typing for the per-port entry dicts

from . import _deps  # Sibling runtime dependency container set by configure_gateway_override_dependencies

OUTPUT_FILENAME = "GatewayOverriddenPorts.csv"  # Single source of truth for the report file name

_EMPTY_FIELDNAMES: list[str] = [  # Header layout preserved verbatim from the original analyzer
    "gateway_device_name",
    "site_name",
    "template_name",
    "port_name",
    "recommended_variable",
    "port_description",
    "port_status",
    "port_admin_status",
    "port_gateway_ip",
    "port_ip_address",
    "port_netmask",
    "port_config_type",
    "port_usage",
    "overridden_from_template",
    "device_id",
    "site_id",
    "template_id",
]


class OverrideReportWriter:
    """Write the override report CSV and print the matching operator-facing summary lines."""

    @staticmethod
    def write_empty() -> None:
        """Write a header-only CSV and print the compliant-fleet message when no overrides exist."""
        logging.info(  # Legacy log preserved verbatim for downstream log parsers
            " No template overrides found - all gateways are compliant with their assigned templates!"
        )
        output_path = _deps.FilePathUtils.get_csv_path(OUTPUT_FILENAME)  # Resolves data/ output dir
        with open(output_path, mode="w", newline="", encoding="utf-8") as csvfile:  # Truncate-and-write CSV
            writer = csv.DictWriter(csvfile, fieldnames=_EMPTY_FIELDNAMES)  # DictWriter for header-only output
            writer.writeheader()  # Header row only; no data rows are written when fleet is fully compliant
        logging.debug("Header-only CSV written to %s", output_path)  # Confirm write completed for operator log
        print(f"! Gateway override report written to {OUTPUT_FILENAME}")  # Legacy console message preserved
        print(  # Legacy console message preserved verbatim
            " No template overrides found - all gateways are compliant with their assigned templates!"
        )

    @staticmethod
    def write_full(
        entries: list[dict[str, Any]],
        total_gateways: int,
        devices_with_overrides_count: int,
        target_ports: list[str],
    ) -> None:
        """Write entries via DataExporter and print the legacy operator-facing summary block."""
        logging.info("Writing %d override entries to %s", len(entries), OUTPUT_FILENAME)  # before action
        _deps.DataExporter.write_with_format_selection(
            entries, OUTPUT_FILENAME
        )  # Multi-backend writer (CSV/SQLite/etc)
        logging.debug("Override entries persisted via DataExporter")  # after action confirmation
        OverrideReportWriter._log_summary(entries, total_gateways, devices_with_overrides_count)  # Legacy logs
        OverrideReportWriter._print_summary(  # Legacy operator-facing console block
            entries=entries,
            total_gateways=total_gateways,
            devices_with_overrides_count=devices_with_overrides_count,
            target_ports=target_ports,
        )

    @staticmethod
    def _log_summary(
        entries: list[dict[str, Any]],
        total_gateways: int,
        devices_with_overrides_count: int,
    ) -> None:
        """Emit the two legacy info log lines that operators grep on for compliance posture."""
        if entries:  # Distinct-device count is only meaningful when at least one port was overridden
            gateways_with_overrides = len({entry["device_id"] for entry in entries})  # Unique device_id count
        else:
            gateways_with_overrides = 0  # No entries means zero gateways had overrides (sanity for log line)
        logging.info(  # Legacy info log preserved verbatim for downstream log parsers
            "! Gateway override report written to %s with %d overridden ports from %d gateway devices.",
            OUTPUT_FILENAME,
            len(entries),
            gateways_with_overrides,
        )
        logging.info(  # Legacy info log preserved verbatim for downstream log parsers
            "! API Optimization: Made device config/stats calls for only %d devices instead of all %d devices",
            devices_with_overrides_count,
            total_gateways,
        )

    @staticmethod
    def _print_summary(
        entries: list[dict[str, Any]],
        total_gateways: int,
        devices_with_overrides_count: int,
        target_ports: list[str],
    ) -> None:
        """Print the legacy operator-facing console summary block verbatim."""
        if entries:  # Same distinct-device math used for the console block as for the log block
            gateways_with_overrides = len({entry["device_id"] for entry in entries})  # Unique device_id count
        else:
            gateways_with_overrides = 0  # No entries means zero gateways had overrides (sanity for print line)
        total_overridden_ports = len(entries)  # Count of CSV rows for the console summary line
        saved_calls = total_gateways - devices_with_overrides_count  # API calls saved by the override pre-filter
        print(f"! Gateway override report written to {OUTPUT_FILENAME}")  # Legacy console line preserved
        print(  # Legacy console line preserved verbatim across two physical lines
            f"! Found {total_overridden_ports} overridden ports across"
            f" {gateways_with_overrides} of {total_gateways} gateway devices"
        )
        print(  # Legacy console line preserved verbatim across two physical lines
            f"! API Optimization: Only fetched live data for {devices_with_overrides_count}"
            f" devices with overrides (saved {saved_calls} unnecessary API calls)"
        )
        print(f"! Target ports analyzed: {', '.join(target_ports)}")  # Legacy console line preserved
        print("! These are outliers that may need correction to match template configuration")  # Legacy line
        if total_overridden_ports == 0:  # Repeat compliant-fleet message when full path produces zero rows
            print(  # Legacy console line preserved verbatim
                " No template overrides found - all gateways are compliant with their assigned templates!"
            )
