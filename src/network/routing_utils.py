"""Routing utilities for Mist network devices.

Extracted from MistHelper.py (Issue #207). Provides three WebSocket-based
routing table operations: forwarding table (gateways), routing table
(switches), and SSR/SRX dedicated routing queries.

Dependencies are injected via constructor for testability.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation

from __future__ import annotations

import json
import logging
import os
import re
import time
from collections.abc import Callable
from typing import Any

import mistapi
import requests
from prettytable import PrettyTable

# ---------------------------------------------------------------------------
# Type aliases for dependency injection
# ---------------------------------------------------------------------------
SelectSiteFn = Callable[[], str | None]
SelectDeviceFn = Callable[[str, str], str | None]
SafeInputFn = Callable[..., str]
WebSocketManagerFactory = Callable[[Any], Any]
IsDebugModeFn = Callable[[], bool]


class RoutingUtils:
    """Routing table operations via WebSocket and dedicated APIs.

    Three public entry points:
    - execute_show_forwarding_table: FIB on gateways/SSR via WebSocket
    - execute_show_routing_table: RIB on switches via WebSocket
    - execute_show_ssr_routes: SSR/SRX dedicated routing API

    All external dependencies are injected via constructor.
    """

    def __init__(
        self,
        apisession: Any,
        select_site_fn: SelectSiteFn,
        select_device_fn: SelectDeviceFn,
        safe_input_fn: SafeInputFn,
        websocket_manager_factory: WebSocketManagerFactory,
        is_debug_mode_fn: IsDebugModeFn,
    ) -> None:
        """Initialize RoutingUtils with injected dependencies."""
        self.apisession = apisession
        self.select_site_fn = select_site_fn
        self.select_device_fn = select_device_fn
        self.safe_input_fn = safe_input_fn
        self.websocket_manager_factory = websocket_manager_factory
        self.is_debug_mode_fn = is_debug_mode_fn

    # =====================================================================
    # PARSING METHODS (pure data transformation)
    # =====================================================================

    def _parse_forwarding_table(self, raw_output: str) -> list[dict[str, Any]]:
        """Parse raw forwarding table output into structured entries."""
        if not raw_output:
            return []

        json_result = self._try_parse_forwarding_json(raw_output)
        if json_result is not None:
            return json_result

        return self._parse_forwarding_text(raw_output)

    def _try_parse_forwarding_json(self, raw_output: str) -> list[dict[str, Any]] | None:
        """Try parsing forwarding output as JSON. Returns None if not JSON."""
        try:
            data = json.loads(raw_output)
        except (json.JSONDecodeError, TypeError):
            return None

        if isinstance(data, list):
            return [self._normalize_forwarding_entry(item) for item in data]
        if isinstance(data, dict):
            return self._extract_forwarding_from_dict(data)
        return None

    def _normalize_forwarding_entry(self, item: dict[str, Any]) -> dict[str, Any]:
        """Normalize a single forwarding entry from JSON."""
        return {
            "destination": item.get("prefix", item.get("destination", "")),
            "next_hop": item.get("nextHop", item.get("next_hop", "")),
            "interface": item.get("interface", item.get("dev", "")),
            "service": item.get("service", item.get("serviceName", "")),
            "table": item.get("table", ""),
            "type": item.get("type", ""),
        }

    def _extract_forwarding_from_dict(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract forwarding entries from a JSON dict with list values."""
        entries: list[dict[str, Any]] = []
        for _key, value in data.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        entries.append(self._normalize_forwarding_entry(item))
        return entries

    def _parse_forwarding_text(self, raw_output: str) -> list[dict[str, Any]]:
        """Parse text-format forwarding table lines."""
        entries: list[dict[str, Any]] = []
        for line in raw_output.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("---"):
                continue
            parts = line.split()
            if len(parts) >= 2:  # noqa: PLR2004
                entries.append(
                    {
                        "destination": parts[0],
                        "next_hop": parts[1] if len(parts) > 1 else "",
                        "interface": parts[2] if len(parts) > 2 else "",  # noqa: PLR2004
                        "service": parts[3] if len(parts) > 3 else "",  # noqa: PLR2004
                        "table": "",
                        "type": "",
                    }
                )
        return entries

    def _display_forwarding_summary(self, entries: list[dict[str, Any]]) -> None:
        """Display formatted summary of forwarding table entries."""
        if not entries:
            print("-> No forwarding table entries found")
            return

        print(f"-> Total forwarding entries: {len(entries)}")
        stats = self._collect_forwarding_stats(entries)

        if stats["services"]:
            top_services = sorted(stats["services"].items(), key=lambda x: x[1], reverse=True)[:5]
            service_str = ", ".join([f"{svc}({cnt})" for svc, cnt in top_services])
            print(f"-> Top services: {service_str}")

        if len(stats["tables"]) > 1:
            print(f"-> Forwarding tables: {', '.join(sorted(stats['tables']))}")

        print(f"-> Unique next hops: {len(stats['next_hops'])}")
        print(f"-> Unique interfaces: {len(stats['interfaces'])}")

        self._display_prefix_groups(entries)

        print("\n-> Forwarding table entries:")
        self._display_prefix_table_impl(entries)

    def _collect_forwarding_stats(
        self,
        entries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Collect summary statistics from forwarding table entries."""
        services: dict[str, int] = {}
        tables: set[str] = set()
        next_hops: set[str] = set()
        interfaces: set[str] = set()

        for entry in entries:
            service = entry.get("service", "")
            if service:
                services[service] = services.get(service, 0) + 1
            if entry.get("table"):
                tables.add(entry["table"])
            if entry.get("next_hop") and entry["next_hop"] != "-":
                next_hops.add(entry["next_hop"])
            if entry.get("interface") and entry["interface"] != "-":
                interfaces.add(entry["interface"])

        return {
            "services": services,
            "tables": tables,
            "next_hops": next_hops,
            "interfaces": interfaces,
        }

    def _display_prefix_groups(self, entries: list[dict[str, Any]]) -> None:
        """Analyze and display top prefix groups from entries."""
        prefix_groups: dict[str, int] = {}
        for entry in entries:
            dest = entry.get("destination", "")
            if dest and "/" in dest:
                prefix = dest.split("/")[0]
                octets = prefix.split(".")
                if len(octets) >= 2:  # noqa: PLR2004
                    group = f"{octets[0]}.{octets[1]}.0.0/16"
                    prefix_groups[group] = prefix_groups.get(group, 0) + 1

        if prefix_groups:
            top_groups = sorted(prefix_groups.items(), key=lambda x: x[1], reverse=True)[:5]
            print("\n-> Top prefix groups:")
            for group, count in top_groups:
                print(f"  - {group}: {count} entries")

    def _display_prefix_table_impl(self, entries: list[dict[str, Any]]) -> None:
        """Display forwarding table entries using PrettyTable."""
        if not entries:
            return

        try:
            table = PrettyTable()
            table.field_names = [
                "Destination",
                "Next Hop",
                "Interface",
                "Service",
                "Table",
                "Type",
            ]
            table.align = "l"

            for entry in entries:
                table.add_row(
                    [
                        entry.get("destination", "-"),
                        entry.get("next_hop", "-"),
                        entry.get("interface", "-"),
                        entry.get("service", "-"),
                        entry.get("table", "-"),
                        entry.get("type", "-"),
                    ]
                )

            print(table)

        except Exception:
            for entry in entries:
                dest = entry.get("destination", "-")
                nhop = entry.get("next_hop", "-")
                iface = entry.get("interface", "-")
                svc = entry.get("service", "-")
                print(f"  {dest} -> {nhop} via {iface} [{svc}]")

    def _parse_routing_table(self, raw_output: str) -> list[dict[str, Any]]:
        """Parse routing table output supporting multiple formats."""
        if not raw_output:
            return []

        json_result = self._try_parse_routing_json(raw_output)
        if json_result is not None:
            return json_result

        lines = raw_output.strip().split("\n")
        if any("inet.0" in line or "inet6.0" in line for line in lines[:20]):
            return self._parse_juniper_routing(raw_output)

        return self._parse_routing_text_lines(lines)

    def _try_parse_routing_json(self, raw_output: str) -> list[dict[str, Any]] | None:
        """Try parsing routing output as JSON. Returns None if not JSON."""
        try:
            data = json.loads(raw_output)
        except (json.JSONDecodeError, TypeError):
            return None

        if isinstance(data, list):
            return [self._normalize_json_route_entry(item) for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            return self._extract_routes_from_json_dict(data)
        return None

    def _extract_routes_from_json_dict(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract route entries from a JSON dict with list values."""
        routes: list[dict[str, Any]] = []
        for _key, value in data.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        routes.append(self._normalize_json_route_entry(item))
        return routes

    def _parse_routing_text_lines(self, lines: list[str]) -> list[dict[str, Any]]:
        """Parse text-format routing lines into route entries."""
        route_entries: list[dict[str, Any]] = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("---"):
                continue
            entry = self._classify_and_parse_route_line(line)
            if entry:
                route_entries.append(entry)
        return route_entries

    def _classify_and_parse_route_line(self, line: str) -> dict[str, Any] | None:
        """Classify a route line and dispatch to the correct parser."""
        if "via" in line or "dev" in line or "proto" in line:
            return self._parse_standard_route_line(line)
        if "BGP" in line or "OSPF" in line or "static" in line:
            return self._parse_protocol_route_line(line)
        parts = line.split()
        if len(parts) >= 2:  # noqa: PLR2004
            return self._parse_tabular_route_line(line)
        return None

    def _parse_standard_route_line(self, line: str) -> dict[str, Any] | None:
        """Parse a route line with via/dev/proto keywords."""
        entry = self._make_empty_route_entry()
        entry, line = self._extract_route_flags(entry, line)

        parts = line.split()
        if parts:
            entry["destination"] = parts[0]

        via_match = re.search(r"via\s+(\S+)", line)
        if via_match:
            entry["next_hop"] = via_match.group(1)

        dev_match = re.search(r"dev\s+(\S+)", line)
        if dev_match:
            entry["interface"] = dev_match.group(1)

        proto_match = re.search(r"proto\s+(\S+)", line)
        if proto_match:
            entry["protocol"] = proto_match.group(1)

        return entry

    def _parse_protocol_route_line(self, line: str) -> dict[str, Any] | None:
        """Parse a route line with BGP/OSPF/static protocol indicators."""
        entry = self._make_empty_route_entry()
        entry, line = self._extract_route_flags(entry, line)

        parts = line.split()
        if not parts:
            return None

        for part in parts:
            self._classify_route_part(entry, part)

        return entry if entry["destination"] else None

    def _make_empty_route_entry(self) -> dict[str, Any]:
        """Create a blank route entry dict with default values."""
        return {
            "destination": "",
            "next_hop": "",
            "interface": "",
            "protocol": "",
            "admin_distance": "",
            "metric": "",
            "active": False,
            "selected": False,
        }

    def _extract_route_flags(
        self,
        entry: dict[str, Any],
        line: str,
    ) -> tuple[dict[str, Any], str]:
        """Extract active/selected flags from line prefix."""
        if line.startswith(">") or line.startswith("*"):
            entry["active"] = ">" in line[:3]
            entry["selected"] = "*" in line[:3]
            line = line.lstrip(">* ")
        return entry, line

    def _classify_route_part(self, entry: dict[str, Any], part: str) -> None:
        """Classify a single token from a protocol route line."""
        upper = part.upper()
        if upper in ("BGP", "OSPF", "STATIC", "DIRECT", "LOCAL"):
            entry["protocol"] = upper
        elif "/" in part and "." in part:
            entry["destination"] = part
        elif re.match(r"\d+\.\d+\.\d+\.\d+", part):
            if not entry["destination"]:
                entry["destination"] = part
            elif not entry["next_hop"]:
                entry["next_hop"] = part
        elif part.startswith(("eth", "ge-", "xe-", "et-", "lo", "irb")):
            entry["interface"] = part

    def _parse_tabular_route_line(self, line: str) -> dict[str, Any] | None:
        """Parse a space-separated tabular route line."""
        parts = line.split()
        if len(parts) < 2:  # noqa: PLR2004
            return None

        entry: dict[str, Any] = {
            "destination": parts[0],
            "next_hop": "",
            "interface": "",
            "protocol": "",
            "admin_distance": "",
            "metric": "",
            "active": False,
            "selected": False,
        }

        if line.startswith(">") or line.startswith("*"):
            entry["active"] = ">" in line[:3]
            entry["selected"] = "*" in line[:3]
            entry["destination"] = parts[1] if len(parts) > 1 else parts[0]
            parts = parts[1:]

        if len(parts) > 1:
            entry["next_hop"] = parts[1]
        if len(parts) > 2:  # noqa: PLR2004
            entry["interface"] = parts[2]
        if len(parts) > 3:  # noqa: PLR2004
            entry["protocol"] = parts[3]
        if len(parts) > 4:  # noqa: PLR2004
            entry["admin_distance"] = parts[4]

        return entry

    def _normalize_json_route_entry(self, item: dict[str, Any]) -> dict[str, Any]:
        """Normalize a JSON dict into standard route entry format."""
        return {
            "destination": item.get("prefix", item.get("destination", item.get("route", ""))),
            "next_hop": item.get("nextHop", item.get("next_hop", item.get("gateway", ""))),
            "interface": item.get("interface", item.get("dev", item.get("iface", ""))),
            "protocol": item.get("protocol", item.get("proto", item.get("type", ""))),
            "admin_distance": str(item.get("adminDistance", item.get("admin_distance", ""))),
            "metric": str(item.get("metric", "")),
            "active": item.get("active", False),
            "selected": item.get("selected", False),
        }

    def _parse_juniper_routing(self, raw_output: str) -> list[dict[str, Any]]:
        """Parse Juniper inet.0/inet6.0 multi-line routing format."""
        routes: list[dict[str, Any]] = []
        current_route: dict[str, Any] = {}
        current_table = ""

        for line in raw_output.strip().split("\n"):
            line_stripped = line.strip()
            current_route, current_table = self._process_juniper_line(
                line_stripped,
                routes,
                current_route,
                current_table,
            )

        if current_route:
            routes.append(current_route)

        return routes

    def _process_juniper_line(
        self,
        line_stripped: str,
        routes: list[dict[str, Any]],
        current_route: dict[str, Any],
        current_table: str,
    ) -> tuple[dict[str, Any], str]:
        """Process a single line of Juniper routing output."""
        table_match = re.match(r"^(\S+\.0):\s", line_stripped)
        if table_match:
            if current_route:
                routes.append(current_route)
            return {}, table_match.group(1)

        dest_match = re.match(
            r"^([>*\s]*)([\d\.]+/\d+|[\da-f:]+/\d+)\s",
            line_stripped,
        )
        if dest_match:
            if current_route:
                routes.append(current_route)
            return self._build_juniper_route(dest_match, line_stripped, current_table), current_table

        if current_route:
            self._update_juniper_via(current_route, line_stripped)

        return current_route, current_table

    def _build_juniper_route(
        self,
        dest_match: re.Match[str],
        line_stripped: str,
        current_table: str,
    ) -> dict[str, Any]:
        """Build a new route entry from a Juniper destination line."""
        flags = dest_match.group(1).strip()
        route: dict[str, Any] = {
            "destination": dest_match.group(2),
            "next_hop": "",
            "interface": "",
            "protocol": "",
            "admin_distance": "",
            "metric": "",
            "active": ">" in flags,
            "selected": "*" in flags,
            "table": current_table,
        }

        proto_match = re.search(r"\[(\w+)/(\d+)\]", line_stripped)
        if proto_match:
            route["protocol"] = proto_match.group(1)
            route["admin_distance"] = proto_match.group(2)

        return route

    def _update_juniper_via(
        self,
        current_route: dict[str, Any],
        line_stripped: str,
    ) -> None:
        """Update current route with via/interface info from continuation line."""
        via_match = re.search(r"via\s+(\S+)", line_stripped)
        if via_match:
            via_parts = via_match.group(1).rstrip(",")
            if re.match(r"\d+\.\d+\.\d+\.\d+", via_parts):
                current_route["next_hop"] = via_parts
            elif "." in via_parts and "/" not in via_parts:
                current_route["interface"] = via_parts.strip()
            else:
                current_route["next_hop"] = via_parts.strip()
        elif line_stripped in ["Local"]:
            current_route["next_hop"] = "Local"
        elif "." in line_stripped and len(line_stripped.split()) == 1:
            current_route["interface"] = line_stripped

    def _parse_ssr_routing(self, json_data: str) -> list[dict[str, Any]]:
        """Parse SSR/SRX routing table JSON from the dedicated API."""
        try:
            data = json.loads(json_data)

            if data.get("status") != "SUCCESS":
                return []

            columns = data.get("columns", [])
            rows = data.get("rows", [])

            if not columns or not rows:
                return []

            route_entries: list[dict[str, Any]] = []
            for row in rows:
                route_entry = {
                    "destination": row.get("prefix", ""),
                    "next_hop": row.get("nextHops", ""),
                    "interface": "",
                    "protocol": ("BGP" if "bgp" in data.get("message", "").lower() else "Unknown"),
                    "admin_distance": "",
                    "metric": str(row.get("metric", "")),
                    "status": row.get("status", ""),
                    "vrf": row.get("vrfName", "default"),
                    "name": row.get("name", ""),
                    "weight": str(row.get("weight", "")),
                    "as_path": row.get("path", ""),
                    "local_preference": str(row.get("localPreference", "")),
                    "selection_reason": row.get("selectionReason", ""),
                }
                route_entries.append(route_entry)

            return route_entries

        except (json.JSONDecodeError, KeyError, TypeError) as error:
            logging.warning(f"Failed to parse SSR routing JSON: {error}")
            return []

    # =====================================================================
    # DISPLAY METHODS
    # =====================================================================

    def _display_routing_summary(
        self,
        route_entries: list[dict[str, Any]],
        query_params: dict[str, Any] | None = None,
    ) -> None:
        """Display formatted summary of routing table entries."""
        if not route_entries:
            self._display_empty_routing(query_params)
            return

        print(f"-> Total routing table entries: {len(route_entries)}")
        stats = self._collect_routing_stats(route_entries)

        if stats["protocols"]:
            proto_str = ", ".join([f"{p}({c})" for p, c in stats["protocols"].items()])
            print(f"-> Protocols: {proto_str}")

        if len(stats["tables"]) > 1:
            print(f"-> Routing tables: {', '.join(sorted(stats['tables']))}")

        print(f"-> Unique destinations: {len(stats['destinations'])}")
        print(f"-> Unique next hops: {len(stats['next_hops'])}")
        print(f"-> Unique interfaces: {len(stats['interfaces'])}")

        if stats["active_routes"] > 0:
            print(f"-> Active routes (marked with >): {stats['active_routes']}")

        print("\n-> Detailed routing table:")
        self._display_routing_details(route_entries)

    def _display_empty_routing(self, query_params: dict[str, Any] | None) -> None:
        """Display message when no routing entries found."""
        print("-> No routing table entries found")
        if query_params:
            print("  -> Try adjusting query parameters:")
            for key, value in query_params.items():
                print(f"    - {key}: {value}")

    def _collect_routing_stats(
        self,
        route_entries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Collect summary statistics from routing table entries."""
        protocols: dict[str, int] = {}
        destinations: set[str] = set()
        next_hops: set[str] = set()
        interfaces: set[str] = set()
        tables: set[str] = set()
        active_routes = 0

        for entry in route_entries:
            self._accumulate_route_stats(
                entry,
                protocols,
                destinations,
                next_hops,
                interfaces,
                tables,
            )
            if entry.get("active"):
                active_routes += 1

        return {
            "protocols": protocols,
            "destinations": destinations,
            "next_hops": next_hops,
            "interfaces": interfaces,
            "tables": tables,
            "active_routes": active_routes,
        }

    def _accumulate_route_stats(
        self,
        entry: dict[str, Any],
        protocols: dict[str, int],
        destinations: set[str],
        next_hops: set[str],
        interfaces: set[str],
        tables: set[str],
    ) -> None:
        """Accumulate statistics from a single route entry."""
        protocol = entry.get("protocol", "Unknown").upper()
        if protocol and protocol != "UNKNOWN":
            protocols[protocol] = protocols.get(protocol, 0) + 1
        if entry.get("destination") and entry.get("destination") != "-":
            destinations.add(entry["destination"])
        if entry.get("next_hop") and entry.get("next_hop") not in ["-", ""]:
            next_hops.add(entry["next_hop"])
        if entry.get("interface") and entry.get("interface") not in ["-", ""]:
            interfaces.add(entry["interface"])
        if entry.get("table"):
            tables.add(entry["table"])

    def _display_routing_details(self, route_entries: list[dict[str, Any]]) -> None:
        """Display detailed routing table in a formatted table."""
        if not route_entries:
            return

        try:
            table = PrettyTable()
            table.field_names = [
                "Status",
                "Destination",
                "Next Hop",
                "Interface",
                "Protocol",
                "Admin Dist",
            ]
            table.align = "l"

            for entry in route_entries:
                status = self._format_route_status(entry)
                table.add_row(
                    [
                        status,
                        entry.get("destination", "-") or "-",
                        entry.get("next_hop", "-") or "-",
                        entry.get("interface", "-") or "-",
                        entry.get("protocol", "-") or "-",
                        entry.get("admin_distance", "-") or "-",
                    ]
                )

            print(table)
            print("\nStatus Legend:")
            print("  > = Active route (installed in forwarding table)")
            print("  * = Selected route (best route among alternatives)")

        except Exception:
            self._display_routing_details_fallback(route_entries)

    def _format_route_status(self, entry: dict[str, Any]) -> str:
        """Format the status indicator for a route entry."""
        status = ""
        if entry.get("active"):
            status += ">"
        if entry.get("selected"):
            status += "*"
        return status if status else " "

    def _display_routing_details_fallback(
        self,
        route_entries: list[dict[str, Any]],
    ) -> None:
        """Fallback text display when PrettyTable is unavailable."""
        header = "   Status | Destination              " "| Next Hop        | Interface       " "| Protocol | Dist"
        print(header)
        print("   " + "-" * 95)
        for entry in route_entries:
            status = self._format_route_status(entry)
            dest = entry.get("destination", "-")
            next_hop = entry.get("next_hop", "-")
            interface = entry.get("interface", "-")
            protocol = entry.get("protocol", "-")
            admin_dist = entry.get("admin_distance", "-")
            print(
                f"   {status:<6} | {dest:<25} | {next_hop:<15}" f" | {interface:<15} | {protocol:<8}" f" | {admin_dist}"
            )

        print("\nStatus Legend:")
        print("  > = Active route, * = Selected route")

    def _display_ssr_routing(
        self,
        route_entries: list[dict[str, Any]],
        query_params: dict[str, Any] | None = None,
    ) -> None:
        """Display SSR/SRX routing table with BGP-specific columns."""
        if not route_entries:
            self._display_empty_routing(query_params)
            return

        stats = self._collect_ssr_stats(route_entries)
        print(f"-> Total routing table entries: {len(route_entries)}")
        print(f"-> Protocols: {stats['protocol_summary']}")
        print(f"-> VRFs: {stats['vrf_summary']}")
        print(f"-> Unique next hops: {len(stats['next_hops'])}")

        self._display_ssr_table(route_entries)

    def _collect_ssr_stats(
        self,
        route_entries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Collect summary statistics from SSR routing entries."""
        protocols: dict[str, int] = {}
        vrfs: dict[str, int] = {}
        next_hops: set[str] = set()

        for entry in route_entries:
            protocol = entry.get("protocol", "Unknown")
            protocols[protocol] = protocols.get(protocol, 0) + 1
            vrf = entry.get("vrf", "default")
            vrfs[vrf] = vrfs.get(vrf, 0) + 1
            next_hop = entry.get("next_hop", "")
            if next_hop and next_hop != "0.0.0.0":  # nosec B104
                next_hops.add(next_hop)

        return {
            "protocol_summary": ", ".join([f"{p}({c})" for p, c in protocols.items()]),
            "vrf_summary": ", ".join([f"{v}({c})" for v, c in vrfs.items()]),
            "next_hops": next_hops,
        }

    def _display_ssr_table(self, route_entries: list[dict[str, Any]]) -> None:
        """Display SSR routing entries using PrettyTable with fallback."""
        try:
            table = PrettyTable()
            table.field_names = [
                "Destination",
                "Next Hop",
                "Protocol",
                "Route Name",
                "Status",
                "Selection Reason",
                "Weight",
                "Metric",
                "Local Pref",
                "AS Path",
                "VRF",
            ]
            table.align = "l"

            for entry in route_entries:
                table.add_row(
                    [
                        entry.get("destination", "-"),
                        entry.get("next_hop", "-"),
                        entry.get("protocol", "-"),
                        entry.get("name", "-"),
                        entry.get("status", "-"),
                        entry.get("selection_reason", "-"),
                        entry.get("weight", "-"),
                        entry.get("metric", "-"),
                        entry.get("local_preference", "-"),
                        entry.get("as_path", "-"),
                        entry.get("vrf", "default"),
                    ]
                )

            print("\n-> Detailed routing table:")
            print(table)

        except Exception:
            self._display_ssr_table_fallback(route_entries)

    def _display_ssr_table_fallback(
        self,
        route_entries: list[dict[str, Any]],
    ) -> None:
        """Fallback text display for SSR routing entries."""
        print("\n-> Detailed routing table:")
        header = (
            "   Destination | Next Hop | Protocol"
            " | Route Name | Status"
            " | Selection Reason | Weight"
            " | Metric | Local Pref"
            " | AS Path | VRF"
        )
        print(header)
        print("   " + "-" * 140)
        for entry in route_entries:
            dest = entry.get("destination", "-")
            nhop = entry.get("next_hop", "-")
            proto = entry.get("protocol", "-")
            name = entry.get("name", "-")
            status = entry.get("status", "-")
            reason = entry.get("selection_reason", "-")
            weight = entry.get("weight", "-")
            metric = entry.get("metric", "-")
            lpref = entry.get("local_preference", "-")
            aspath = entry.get("as_path", "-")
            vrf = entry.get("vrf", "default")
            print(
                f"   {dest} | {nhop} | {proto}"
                f" | {name} | {status}"
                f" | {reason} | {weight}"
                f" | {metric} | {lpref}"
                f" | {aspath} | {vrf}"
            )

    # =====================================================================
    # ORCHESTRATOR: FORWARDING TABLE
    # =====================================================================

    def execute_show_forwarding_table(self) -> None:
        """Execute show forwarding table on a gateway/SSR via WebSocket."""
        debug_mode = self.is_debug_mode_fn()
        self._setup_debug_mode(debug_mode)
        logging.info("Starting WebSocket show forwarding table operation...")
        logging.debug("ENTER: execute_show_forwarding_table")

        websocket_manager = None
        try:
            site_id, device_id, device_info = self._select_forwarding_table_device(debug_mode)
            if not site_id or not device_id:
                return

            websocket_manager = self._connect_websocket(site_id, device_id, debug_mode)
            if not websocket_manager:
                return

            payload = self._get_forwarding_table_params()

            session_id = self._execute_forwarding_table_command(site_id, device_id, payload, debug_mode)
            if not session_id:
                websocket_manager.disconnect()
                return

            self._process_forwarding_table_results(
                websocket_manager,
                session_id,
                device_id,
                device_info,
                debug_mode,
            )

        except Exception as error:
            self._handle_routing_error("forwarding table", error, debug_mode)

        finally:
            self._cleanup_websocket(websocket_manager, debug_mode)
            logging.debug("EXIT: execute_show_forwarding_table")

    def _setup_debug_mode(self, debug_mode: bool) -> None:
        """Configure logging for debug mode if enabled."""
        if debug_mode:
            logging.getLogger().setLevel(logging.DEBUG)
            print("[DEBUG] DEBUG MODE ENABLED")

    def _select_forwarding_table_device(self, debug_mode: bool) -> tuple[str | None, str | None, dict[str, Any] | None]:
        """Select site and gateway device for forwarding table."""
        site_id = self.select_site_fn()
        if not site_id:
            print("! No site selected. Operation cancelled.")
            return None, None, None

        if debug_mode:
            print(f"[DEBUG] Selected site_id = {site_id}")

        print("-> Forwarding table is available on routers" " and gateways (Layer 3 devices)")
        print("-> This shows the Forwarding Information Base (FIB)" " used for packet routing decisions")
        print("-> SSR gateways provide the most comprehensive" " forwarding table information")

        device_id = self.select_device_fn(site_id, "gateway")
        if not device_id:
            print(
                "! No gateway device selected." " Forwarding table command is optimized" " for Layer 3 routing devices."
            )
            return None, None, None

        if debug_mode:
            print(f"[DEBUG] Selected device_id = {device_id}")

        device_info = self._get_device_info(site_id, device_id, "all", debug_mode)
        self._display_forwarding_device_guidance(device_info)

        return site_id, device_id, device_info

    def _get_device_info(
        self,
        site_id: str,
        device_id: str,
        device_type: str,
        debug_mode: bool,
    ) -> dict[str, Any] | None:
        """Retrieve device information for compatibility checking."""
        try:
            rawdata = mistapi.api.v1.sites.devices.listSiteDevices(self.apisession, site_id, type=device_type).data
            device_info = next(
                (device for device in rawdata if device.get("id") == device_id),
                None,
            )
            if device_info and debug_mode:
                print(
                    f"[DEBUG] Device type: {device_info.get('type')},"
                    f" model: {device_info.get('model')},"
                    f" name: {device_info.get('name')}"
                )
            return device_info
        except Exception as error:
            logging.warning(f"Could not verify device compatibility: {error}")
            if debug_mode:
                print(f"[DEBUG] Device check failed: {error}")
            print("   -> Proceeding with standard command")
            return None

    def _display_forwarding_device_guidance(self, device_info: dict[str, Any] | None) -> None:
        """Display device-specific guidance for forwarding table."""
        if not device_info:
            return

        device_type = device_info.get("type", "unknown")
        device_model = device_info.get("model", "unknown")

        if device_type == "gateway":
            if "SSR" in device_model.upper() or "128T" in device_model:
                print(f"-> SSR gateway detected ({device_model}):" " Excellent forwarding table support")
            else:
                print(f"-> Gateway device detected ({device_model}):" " Good forwarding table support")
        elif device_type == "switch":
            print(f"!? Switch device ({device_model}):" " Limited forwarding table - primarily Layer 2")
            print("  -> Consider using MAC table command" " for Layer 2 switching information")
        elif device_type == "ap":
            print(f"!? Access Point ({device_model}):" " No forwarding table - wireless bridging only")

    def _connect_websocket(self, site_id: str, device_id: str, debug_mode: bool) -> Any | None:
        """Establish WebSocket connection and subscribe to channel."""
        print(f"\n-> Executing show forwarding table on device" f" {device_id}...")
        print("-> Establishing WebSocket connection...")

        websocket_manager = self.websocket_manager_factory(self.apisession)
        if debug_mode:
            print("[DEBUG] WebSocketManager initialized")

        if not websocket_manager.connect():
            print("! Failed to establish WebSocket connection")
            return None

        if debug_mode:
            print("[DEBUG] WebSocket connection established")

        command_channel = f"/sites/{site_id}/devices/{device_id}/cmd"
        if not websocket_manager.subscribe_to_channel(command_channel):
            print("! Failed to subscribe to device command channel")
            websocket_manager.disconnect()
            return None

        if debug_mode:
            print(f"[DEBUG] Subscribed to channel: {command_channel}")

        print("-> WebSocket connected and subscribed")
        time.sleep(1)
        return websocket_manager

    def _get_forwarding_table_params(self) -> dict[str, Any]:
        """Get user input for forwarding table query parameters."""
        print("\n=== Forwarding Table Lookup Parameters ===")
        print("The Mist API requires filtering parameters" " for forwarding table lookups.")
        print("You can provide:")
        print("  1. IP prefix" " (e.g., 192.168.1.0/24, 10.0.0.0/8)")
        print("  2. Service name (for SSR gateways)")
        print("  3. Both prefix and service name")
        print("  4. Leave empty to use default" " (0.0.0.0/0 - all routes)")

        prefix_input = self.safe_input_fn("\nEnter IP prefix" " (press Enter for default 0.0.0.0/0): ").strip()
        service_name_input = self.safe_input_fn("Enter service name (press Enter to skip): ").strip()
        vrf_input = self.safe_input_fn("Enter VRF name (press Enter to skip): ").strip()
        node_input = self.safe_input_fn("Enter node" " (node0/node1 for HA, press Enter to skip): ").strip()

        payload: dict[str, Any] = {
            "prefix": prefix_input if prefix_input else "0.0.0.0/0",
        }
        if not prefix_input:
            print("-> Using default prefix: 0.0.0.0/0 (all routes)")

        if service_name_input:
            payload["service_name"] = service_name_input
        if vrf_input:
            payload["vrf"] = vrf_input
        if node_input and node_input.lower() in ["node0", "node1"]:
            payload["node"] = node_input.lower()

        return payload

    def _post_device_command(
        self,
        site_id: str,
        device_id: str,
        endpoint: str,
        payload: dict[str, Any],
        debug_mode: bool,
    ) -> tuple[str | None, str | None]:
        """POST a command to a device REST endpoint. Returns (session_id, error_msg)."""
        mist_host = getattr(self.apisession, "host", None) or os.getenv("MIST_HOST")
        mist_apitoken = getattr(self.apisession, "apitoken", None) or os.getenv("MIST_APITOKEN")

        if not mist_host or not mist_apitoken:
            return None, "Mist host or API token not found in session or environment"

        url = f"https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/{endpoint}"
        headers = {
            "Authorization": f"Token {mist_apitoken}",
            "Content-Type": "application/json",
        }

        if debug_mode:
            print(f"[DEBUG] POST URL = {url}")

        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if debug_mode:
            print(f"[DEBUG] HTTP Response Status = {response.status_code}")
            print(f"[DEBUG] HTTP Response Body = {response.text}")

        if response.status_code != 200:  # noqa: PLR2004
            return None, f"HTTP {response.status_code}: {response.text}"

        response_data = response.json()
        session_id: str | None = response_data.get("session")
        if not session_id:
            return None, "No session ID returned"

        return session_id, None

    def _execute_forwarding_table_command(
        self,
        site_id: str,
        device_id: str,
        payload: dict[str, Any],
        debug_mode: bool,
    ) -> str | None:
        """Execute the forwarding table command via REST API."""
        print("-> Issuing show forwarding table command...")
        logging.debug(f"Forwarding table payload: {payload}")

        if debug_mode:
            print(f"[DEBUG] Forwarding table payload = {payload}")

        session_id, error_msg = self._post_device_command(
            site_id,
            device_id,
            "show_forwarding_table",
            payload,
            debug_mode,
        )

        if error_msg:
            print(f"! Failed to issue show forwarding table command: {error_msg}")
            return None

        print(f"-> Show forwarding table command issued (session: {session_id[:8]}...)")  # type: ignore[index]
        print("-> Waiting for forwarding table results...")

        if debug_mode:
            print(f"[DEBUG] Full session ID = {session_id}")

        return session_id

    def _process_forwarding_table_results(
        self,
        websocket_manager: Any,
        session_id: str,
        device_id: str,
        device_info: dict[str, Any] | None,
        debug_mode: bool,
    ) -> None:
        """Wait for and process forwarding table results."""
        if debug_mode:
            print("[DEBUG] Starting to wait for WebSocket results...")

        result = websocket_manager.wait_for_command_result(session_id, timeout_seconds=60)

        if debug_mode:
            print(f"[DEBUG] wait_for_command_result returned:" f" {result is not None}")
            if result:
                print(f"[DEBUG] Result keys: {list(result.keys())}")

        if result:
            self._display_forwarding_table_output(result, device_id, device_info, debug_mode)
        else:
            self._display_forwarding_table_timeout(device_info)

    def _display_debug_result_fields(
        self,
        result: dict[str, Any],
        debug_mode: bool,
    ) -> None:
        """Display debug fields from WebSocket result if debug mode is on."""
        if not debug_mode:
            return
        available = [k for k in result if k not in ["raw", "Output", "session"]]
        if available:
            print(f"\n[DEBUG] OTHER AVAILABLE FIELDS: {available}")
            for field in available:
                if result.get(field):
                    print(f"[DEBUG] {field}: {result.get(field)}")

    def _display_no_data_message(self, result: dict[str, Any], label: str) -> None:
        """Display message when no raw or Output data is present."""
        raw_output = result.get("raw", "")
        output_fields = result.get("Output", "")
        if not raw_output and not output_fields:
            print(f"! No {label} data received")
            print(f"Available result keys: {list(result.keys())}")

    def _log_command_completion(
        self,
        operation: str,
        device_id: str,
        device_info: dict[str, Any] | None,
    ) -> None:
        """Log successful command completion with device context."""
        device_context = f"device {device_id}"
        if device_info:
            device_context = f"{device_info.get('type', 'unknown')}" f" {device_info.get('name', device_id[:8])}"
        logging.info(f"WebSocket {operation} completed successfully for {device_context}")

    def _display_forwarding_table_output(
        self,
        result: dict[str, Any],
        device_id: str,
        device_info: dict[str, Any] | None,
        debug_mode: bool,
    ) -> None:
        """Display formatted forwarding table results."""
        print("\n" + "=" * 80)
        print("FORWARDING TABLE RESULTS:")
        print("=" * 80)

        raw_output = result.get("raw", "")
        if raw_output:
            entries = self._parse_forwarding_table(raw_output)
            self._display_forwarding_summary(entries)

        output_fields = result.get("Output", "")
        if output_fields and output_fields != raw_output:
            print("\n" + "=" * 40)
            print("ADDITIONAL OUTPUT:")
            print("=" * 40)
            additional = self._parse_forwarding_table(output_fields)
            self._display_forwarding_summary(additional)

        self._display_debug_result_fields(result, debug_mode)
        self._display_no_data_message(result, "forwarding table")

        print("=" * 80)
        self._log_command_completion("show forwarding table", device_id, device_info)

    def _display_forwarding_table_timeout(self, device_info: dict[str, Any] | None) -> None:
        """Display timeout message with troubleshooting guidance."""
        print("! Timeout waiting for forwarding table results")
        print("! This may indicate:")
        print("  - The device doesn't support" " forwarding table commands")
        print("  - The device is busy or not responding")
        print("  - Network connectivity issues")

        if device_info:
            device_type = device_info.get("type", "unknown")
            device_model = device_info.get("model", "unknown")

            if device_type == "gateway":
                print(f"\nGateway troubleshooting ({device_model}):")
                print("-> Ensure the device is online and reachable")
                print("-> Try the command again or use" " SSH-based routing commands")
            elif device_type == "switch":
                print(f"\nSwitch troubleshooting ({device_model}):")
                print("-> Use 'Show MAC Table' command" " for Layer 2 forwarding information")
            elif device_type == "ap":
                print(f"\nAccess Point troubleshooting" f" ({device_model}):")
                print("-> APs don't maintain forwarding tables")

        logging.warning("WebSocket show forwarding table" " operation timed out")

    def _handle_routing_error(
        self,
        operation_name: str,
        error: Exception,
        debug_mode: bool,
    ) -> None:
        """Handle exceptions during routing operations."""
        error_message = f"WebSocket {operation_name} operation failed: {error}"
        print(f"! {error_message}")
        logging.error(error_message)

        if debug_mode:
            print("[DEBUG] Exception details:")
            import traceback

            traceback.print_exc()

    def _cleanup_websocket(self, websocket_manager: Any | None, debug_mode: bool) -> None:
        """Cleanup WebSocket connection."""
        try:
            if websocket_manager is not None:
                websocket_manager.disconnect()
                print("-> WebSocket connection closed")
                if debug_mode:
                    print("[DEBUG] WebSocket cleanup completed")
        except Exception as cleanup_error:
            logging.warning(f"WebSocket cleanup error: {cleanup_error}")

    # =====================================================================
    # ORCHESTRATOR: ROUTING TABLE (Switches)
    # =====================================================================

    def execute_show_routing_table(self) -> None:
        """Execute show route command on switches via WebSocket."""
        debug_mode = self.is_debug_mode_fn()
        self._setup_debug_mode(debug_mode)
        logging.info("Starting WebSocket show routing table operation...")
        logging.debug("ENTER: execute_show_routing_table")

        websocket_manager = None
        try:
            site_id, device_id, device_info = self._select_routing_table_device(debug_mode)
            if not site_id or not device_id:
                return

            websocket_manager = self._connect_websocket(site_id, device_id, debug_mode)
            if not websocket_manager:
                return

            payload = self._get_routing_table_params()

            session_id = self._execute_routing_table_command(site_id, device_id, payload, debug_mode)
            if not session_id:
                websocket_manager.disconnect()
                return

            self._process_routing_table_results(
                websocket_manager,
                session_id,
                device_id,
                device_info,
                payload,
                debug_mode,
            )

        except KeyboardInterrupt:
            print("\n! Operation interrupted by user")
            logging.info("WebSocket show routing table" " operation interrupted by user")

        except Exception as error:
            self._handle_routing_error("routing table", error, debug_mode)

        finally:
            self._cleanup_websocket(websocket_manager, debug_mode)
            logging.debug("EXIT: execute_show_routing_table")

    def _select_routing_table_device(self, debug_mode: bool) -> tuple[str | None, str | None, dict[str, Any] | None]:
        """Select site and switch device for routing table."""
        site_id = self.select_site_fn()
        if not site_id:
            print("! No site selected. Operation cancelled.")
            return None, None, None

        if debug_mode:
            print(f"[DEBUG] Selected site_id = {site_id}")

        print("-> Switch routing table information" " (Layer 3 routing protocols)")
        print("-> This shows the Routing Information Base (RIB)" " maintained by routing protocols")
        print("-> Includes routes from BGP, OSPF, static routes," " direct routes, etc.")
        print("-> For SSR/SRX devices, use Menu Option 8" " (dedicated SSR/SRX routing API)")

        device_id = self.select_device_fn(site_id, "switch")
        if not device_id:
            print("! No device selected. Operation cancelled.")
            return None, None, None

        if debug_mode:
            print(f"[DEBUG] Selected device_id = {device_id}")

        device_info = self._get_device_info(site_id, device_id, "switch", debug_mode)
        should_continue = self._display_routing_device_guidance(device_info)
        if not should_continue:
            return None, None, None

        return site_id, device_id, device_info

    def _display_routing_device_guidance(self, device_info: dict[str, Any] | None) -> bool:
        """Display device-specific guidance. Returns False to cancel."""
        if not device_info:
            return True

        device_type = device_info.get("type", "unknown")
        device_model = device_info.get("model", "unknown")

        if device_type == "switch":
            if "EX" in device_model.upper():
                print(f"!? Juniper EX switch detected" f" ({device_model}):" " Excellent Layer 3 routing support")
            elif "QFX" in device_model.upper():
                print(f"!? Juniper QFX switch detected" f" ({device_model}):" " Good Layer 3 routing support")
            else:
                print(f"-> Switch device detected ({device_model}):" " Layer 3 routing table support")
            return True

        print(f"!? Non-switch device detected" f" ({device_type}/{device_model})")
        print("  -> For SSR/SRX devices, use Menu Option 8")
        print("  -> For gateway forwarding tables," " use Menu Option 6")
        user_choice = self.safe_input_fn("Continue with switch routing command anyway? (y/N): ").strip().lower()
        return user_choice in ["y", "yes"]

    def _get_routing_table_params(self) -> dict[str, Any]:
        """Get user input for routing table query parameters."""
        print("\n=== Routing Table Query Parameters ===")
        print("Configure the routing table query" " (all parameters are optional):")
        print("  X  Prefix: Specific route prefix to look up" " (e.g., 192.168.1.0/24)")
        print("  X  Protocol: Filter by routing protocol" " (bgp, ospf, static, direct, evpn, any)")
        print("  X  VRF: Virtual Routing" " and Forwarding instance name")
        print("  X  Neighbor: BGP neighbor IP" " (shows received/advertised routes)")
        print("  X  Node: For HA devices (node0/node1)")

        prefix_input = self.safe_input_fn("\nEnter route prefix" " (press Enter to show all routes): ").strip()

        print("\nProtocol options:" " any (default), bgp, ospf, static, direct, evpn")
        protocol_input = self.safe_input_fn("Enter protocol filter" " (press Enter for 'any'): ").strip()

        vrf_input = self.safe_input_fn("Enter VRF name (press Enter to skip): ").strip()
        neighbor_input = self.safe_input_fn("Enter BGP neighbor IP (press Enter to skip): ").strip()

        route_direction = ""
        if neighbor_input:
            print("\nRoute direction options:" " received, advertised, (empty for both)")
            route_direction = self.safe_input_fn("Enter route direction" " (press Enter for both): ").strip()

        node_input = self.safe_input_fn("Enter node" " (node0/node1 for HA, press Enter to skip): ").strip()

        payload = self._build_routing_payload(
            prefix_input,
            protocol_input,
            vrf_input,
            neighbor_input,
            route_direction,
            node_input,
        )
        return payload

    def _build_routing_payload(
        self,
        prefix_input: str,
        protocol_input: str,
        vrf_input: str,
        neighbor_input: str,
        route_direction: str,
        node_input: str,
    ) -> dict[str, Any]:
        """Build routing table API payload from user inputs."""
        payload: dict[str, Any] = {}
        if prefix_input:
            payload["prefix"] = prefix_input

        valid_protocols = ["bgp", "ospf", "static", "direct", "evpn", "any"]
        if protocol_input and protocol_input.lower() in valid_protocols:
            payload["protocol"] = protocol_input.lower()
        else:
            payload["protocol"] = "any"

        if vrf_input:
            payload["vrf"] = vrf_input
        if neighbor_input:
            payload["neighbor"] = neighbor_input
            valid_directions = ["received", "advertised"]
            if route_direction and route_direction.lower() in valid_directions:
                payload["route"] = route_direction.lower()
        if node_input and node_input.lower() in ["node0", "node1"]:
            payload["node"] = node_input.lower()

        return payload

    def _execute_routing_table_command(
        self,
        site_id: str,
        device_id: str,
        payload: dict[str, Any],
        debug_mode: bool,
    ) -> str | None:
        """Execute the routing table command via REST API."""
        print("-> Issuing show route command...")
        logging.debug(f"Route payload: {payload}")

        if debug_mode:
            print(f"[DEBUG] Route payload = {payload}")

        session_id, error_msg = self._post_device_command(
            site_id,
            device_id,
            "show_route",
            payload,
            debug_mode,
        )

        if error_msg:
            print(f"! Failed to issue show route command: {error_msg}")
            return None

        print(f"-> Show route command issued (session: {session_id[:8]}...)")  # type: ignore[index]
        print("-> Waiting for routing table results...")

        if debug_mode:
            print(f"[DEBUG] Full session ID = {session_id}")

        return session_id

    def _process_routing_table_results(  # noqa: PLR0913
        self,
        websocket_manager: Any,
        session_id: str,
        device_id: str,
        device_info: dict[str, Any] | None,
        payload: dict[str, Any],
        debug_mode: bool,
    ) -> None:
        """Wait for and process routing table results."""
        if debug_mode:
            print("[DEBUG] Starting to wait for WebSocket results...")

        result = websocket_manager.wait_for_command_result(session_id, timeout_seconds=60)

        if debug_mode:
            print(f"[DEBUG] wait_for_command_result returned:" f" {result is not None}")
            if result:
                print(f"[DEBUG] Result keys: {list(result.keys())}")

        if result:
            self._display_routing_table_output(result, device_id, device_info, payload, debug_mode)
        else:
            print("! Timeout waiting for routing table results")
            print("! This may indicate:")
            print("  - The device doesn't support" " routing table commands")
            print("  - The device has no" " routing protocols configured")
            print("  - The device is busy or not responding")

    def _display_routing_table_output(  # noqa: PLR0913
        self,
        result: dict[str, Any],
        device_id: str,
        device_info: dict[str, Any] | None,
        payload: dict[str, Any],
        debug_mode: bool,
    ) -> None:
        """Display formatted routing table results."""
        print("\n" + "=" * 80)
        print("ROUTING TABLE RESULTS:")
        print("=" * 80)

        raw_output = result.get("raw", "")
        if raw_output:
            entries = self._parse_routing_table(raw_output)
            self._display_routing_summary(entries, payload)

        output_fields = result.get("Output", "")
        if output_fields and output_fields != raw_output:
            print("\n" + "=" * 40)
            print("ADDITIONAL OUTPUT:")
            print("=" * 40)
            additional = self._parse_routing_table(output_fields)
            self._display_routing_summary(additional, payload)

        self._display_debug_result_fields(result, debug_mode)
        self._display_no_data_message(result, "routing table")

        print("=" * 80)
        self._log_command_completion("show routing table", device_id, device_info)

    # =====================================================================
    # ORCHESTRATOR: SSR/SRX ROUTES
    # =====================================================================

    def execute_show_ssr_routes(self) -> None:
        """Execute SSR/SRX routing table via dedicated API."""
        debug_mode = self.is_debug_mode_fn()
        self._setup_debug_mode(debug_mode)
        logging.info("Starting SSR/SRX dedicated" " routing table operation...")
        logging.debug("ENTER: execute_show_ssr_routes")

        websocket_manager = None
        try:
            site_id, device_id, device_info = self._select_ssr_device(debug_mode)
            if not site_id or not device_id:
                return

            request_body = self._get_ssr_route_params()

            websocket_manager = self._connect_websocket(site_id, device_id, debug_mode)
            if not websocket_manager:
                return

            session_id = self._execute_ssr_route_command(site_id, device_id, request_body, debug_mode)
            if not session_id:
                websocket_manager.disconnect()
                return

            self._process_ssr_route_results(
                websocket_manager,
                session_id,
                device_id,
                device_info,
                request_body,
                debug_mode,
            )

        except KeyboardInterrupt:
            print("\n! Operation interrupted by user")
            logging.info("SSR/SRX routing table" " operation interrupted by user")

        except Exception as error:
            self._handle_routing_error("SSR/SRX routing table", error, debug_mode)

        finally:
            self._cleanup_websocket(websocket_manager, debug_mode)
            logging.debug("EXIT: execute_show_ssr_routes")

    def _select_ssr_device(self, debug_mode: bool) -> tuple[str | None, str | None, dict[str, Any] | None]:
        """Select site and SSR/SRX device for routing command."""
        site_id = self.select_site_fn()
        if not site_id:
            print("! No site selected. Operation cancelled.")
            return None, None, None

        if debug_mode:
            print(f"[DEBUG] Selected site_id = {site_id}")

        print("-> SSR/SRX routing table query" " using dedicated API function")
        print("-> This function is optimized" " for SSR (128T) and SRX devices")
        print("-> Provides structured routing table queries" " with advanced filtering")

        device_id = self.select_device_fn(site_id, "gateway")
        if not device_id:
            print("! No device selected. Operation cancelled.")
            return None, None, None

        if debug_mode:
            print(f"[DEBUG] Selected device_id = {device_id}")

        device_info = self._get_device_info(site_id, device_id, "gateway", debug_mode)
        should_continue = self._verify_ssr_compatibility(device_info)
        if not should_continue:
            return None, None, None

        return site_id, device_id, device_info

    def _verify_ssr_compatibility(self, device_info: dict[str, Any] | None) -> bool:
        """Verify device is SSR/SRX compatible. False to cancel."""
        if not device_info:
            return True

        device_type = device_info.get("type", "unknown")
        device_model = device_info.get("model", "unknown")

        if device_type == "gateway":
            if "SSR" in device_model.upper() or "128T" in device_model:
                print(f"!? SSR gateway detected ({device_model}):" " Fully compatible")
                return True
            if "SRX" in device_model.upper():
                print(f"!? SRX router detected ({device_model}):" " Fully compatible")
                return True
            print(f"!? Gateway device ({device_model}):" " May have limited compatibility")
            user_choice = self.safe_input_fn("Continue anyway? (y/N): ").strip().lower()
            return user_choice in ["y", "yes"]

        print(f"!? Non-gateway device detected" f" ({device_type}/{device_model})")
        user_choice = self.safe_input_fn("Continue anyway? (y/N): ").strip().lower()
        return user_choice in ["y", "yes"]

    def _get_ssr_route_params(self) -> dict[str, Any]:
        """Get user input for SSR/SRX routing table parameters."""
        print("\n=== SSR/SRX Routing Table Query Parameters ===")
        print("Configure the routing table query" " (all parameters are optional):")
        print("  X  Protocol: bgp, any, ospf," " static, direct, evpn")
        print("  X  Prefix: Specific route prefix to look up")
        print("  X  VRF: Virtual Routing" " and Forwarding instance")
        print("  X  Neighbor: BGP neighbor IP for route analysis")
        print("  X  Node: For HA clusters (node0/node1)")

        print("\nProtocol options:" " bgp, any, ospf, static, direct, evpn, (none)")
        protocol_input = self.safe_input_fn("Enter protocol" " (press Enter for API default): ").strip().lower()

        prefix_input = self.safe_input_fn(
            "\nEnter route prefix" " (e.g., 192.168.1.0/24," " press Enter to skip): "
        ).strip()

        vrf_input = self.safe_input_fn("Enter VRF name" " (press Enter for default VRF): ").strip()
        neighbor_input = self.safe_input_fn("Enter BGP neighbor IP" " (press Enter to skip): ").strip()

        route_direction = ""
        if neighbor_input:
            print("\nRoute direction:" " received, advertised, (empty for both)")
            route_direction = self.safe_input_fn("Enter route direction" " (press Enter for both): ").strip().lower()

        node_input = self.safe_input_fn("Enter HA cluster node" " (node0/node1, press Enter to skip): ").strip().lower()

        print("\nReal-time refresh options:")
        interval_input = self.safe_input_fn("Refresh interval in seconds" " (0-10, press Enter for one-time): ").strip()
        duration_input = ""
        if interval_input and interval_input.isdigit() and 0 < int(interval_input) <= 10:  # noqa: PLR2004
            duration_input = self.safe_input_fn("Refresh duration in seconds" " (0-300, press Enter for 30): ").strip()

        return self._build_ssr_payload(
            protocol_input,
            prefix_input,
            vrf_input,
            neighbor_input,
            route_direction,
            node_input,
            interval_input,
            duration_input,
        )

    def _build_ssr_payload(  # noqa: PLR0913
        self,
        protocol_input: str,
        prefix_input: str,
        vrf_input: str,
        neighbor_input: str,
        route_direction: str,
        node_input: str,
        interval_input: str,
        duration_input: str,
    ) -> dict[str, Any]:
        """Build SSR/SRX routing API request body from user inputs."""
        request_body: dict[str, Any] = {}
        valid_protocols = ["any", "bgp", "ospf", "static", "direct", "evpn"]
        if protocol_input and protocol_input in valid_protocols:
            request_body["protocol"] = protocol_input
        if prefix_input:
            request_body["prefix"] = prefix_input
        if vrf_input:
            request_body["vrf"] = vrf_input
        if neighbor_input:
            request_body["neighbor"] = neighbor_input
            if route_direction and route_direction in ["received", "advertised"]:
                request_body["route"] = route_direction
        if node_input and node_input in ["node0", "node1"]:
            request_body["node"] = {"node": node_input}
        self._apply_ssr_refresh_params(request_body, interval_input, duration_input)
        return request_body

    def _apply_ssr_refresh_params(
        self,
        request_body: dict[str, Any],
        interval_input: str,
        duration_input: str,
    ) -> None:
        """Apply refresh interval and duration to SSR request body."""
        if not (interval_input and interval_input.isdigit()):
            return
        interval_val = int(interval_input)
        if not (0 <= interval_val <= 10):  # noqa: PLR2004
            return
        request_body["interval"] = interval_val
        if interval_val == 0:
            return
        if duration_input and duration_input.isdigit():
            duration_val = int(duration_input)
            if 0 <= duration_val <= 300:  # noqa: PLR2004
                request_body["duration"] = duration_val
                return
        request_body["duration"] = 30

    def _execute_ssr_route_command(
        self,
        site_id: str,
        device_id: str,
        request_body: dict[str, Any],
        debug_mode: bool,
    ) -> str | None:
        """Execute the SSR/SRX routing table API call."""
        print(f"\n-> Executing SSR/SRX routing table query" f" on device {device_id}...")
        logging.debug(f"Request body: {request_body}")

        if debug_mode:
            print(f"[DEBUG] Request body = {request_body}")

        return self._call_ssr_api(site_id, device_id, request_body, debug_mode)

    def _call_ssr_api(
        self,
        site_id: str,
        device_id: str,
        request_body: dict[str, Any],
        debug_mode: bool,
    ) -> str | None:
        """Call the SSR/SRX routing table API and return session ID."""
        try:
            print("-> Calling dedicated" " SSR/SRX routing table API...")
            if debug_mode:
                print("[DEBUG] Calling mistapi.api.v1.sites.devices" ".showSiteSsrAndSrxRoutes")

            response = mistapi.api.v1.sites.devices.showSiteSsrAndSrxRoutes(
                self.apisession,
                site_id,
                device_id,
                request_body,
            )

            if debug_mode:
                print(f"[DEBUG] API response type: {type(response)}")
                if hasattr(response, "data"):
                    print(f"[DEBUG] Response data: {response.data}")

            return self._extract_ssr_session_id(response, debug_mode)

        except Exception as api_error:
            print(f"! Error calling SSR/SRX" f" routing table API: {api_error}")
            logging.error(f"SSR/SRX routing table" f" API error: {api_error}")
            if debug_mode:
                import traceback

                traceback.print_exc()
            print("\n-> Try the generic routing table command" " (Menu 7) as fallback")
            return None

    def _extract_ssr_session_id(
        self,
        response: Any,
        debug_mode: bool,
    ) -> str | None:
        """Extract session ID from SSR API response."""
        if not (hasattr(response, "data") and response.data):
            print("! Unexpected API response format")
            return None
        session_id: str | None = response.data.get("session")
        if not session_id:
            print("! No session ID returned" " from SSR/SRX routing API")
            return None
        print(f"-> Command initiated" f" (session: {session_id[:8]}...)")
        print("-> Waiting for SSR/SRX" " routing table results...")
        if debug_mode:
            print(f"[DEBUG] Full session ID:" f" {session_id}")
        return session_id

    def _process_ssr_route_results(  # noqa: PLR0913
        self,
        websocket_manager: Any,
        session_id: str,
        device_id: str,
        device_info: dict[str, Any] | None,
        request_body: dict[str, Any],
        debug_mode: bool,
    ) -> None:
        """Wait for and process SSR/SRX routing table results."""
        if debug_mode:
            print("[DEBUG] Starting to wait for WebSocket results...")

        result = websocket_manager.wait_for_command_result(session_id, timeout_seconds=60)

        if debug_mode:
            print(f"[DEBUG] wait_for_command_result returned:" f" {result is not None}")
            if result:
                print(f"[DEBUG] Result keys: {list(result.keys())}")

        if result:
            self._display_ssr_route_output(
                result,
                device_id,
                device_info,
                request_body,
                debug_mode,
            )
        else:
            print("! Timeout waiting for" " SSR/SRX routing table results")
            print("! Try the generic routing table command" " (Menu 7) as fallback")

    def _display_ssr_route_output(  # noqa: PLR0913
        self,
        result: dict[str, Any],
        device_id: str,
        device_info: dict[str, Any] | None,
        request_body: dict[str, Any],
        debug_mode: bool,
    ) -> None:
        """Display formatted SSR/SRX routing table results."""
        print("\n" + "=" * 80)
        print("SSR/SRX ROUTING TABLE RESULTS:")
        print("=" * 80)

        raw_output = result.get("raw", "")
        if raw_output:
            self._display_ssr_parsed_section(raw_output, request_body)

        output_fields = result.get("Output", "")
        if output_fields and output_fields != raw_output:
            print("\n" + "=" * 40)
            print("ADDITIONAL OUTPUT:")
            print("=" * 40)
            self._display_ssr_parsed_section(output_fields, request_body)

        self._display_debug_result_fields(result, debug_mode)
        self._display_no_data_message(result, "routing table")

        print("=" * 80)
        self._log_command_completion("SSR/SRX routing table", device_id, device_info)

    def _display_ssr_parsed_section(
        self,
        output: str,
        request_body: dict[str, Any],
    ) -> None:
        """Parse and display an SSR output section with fallback."""
        entries = self._parse_ssr_routing(output)
        if entries:
            self._display_ssr_routing(entries, request_body)
        else:
            entries = self._parse_routing_table(output)
            self._display_routing_summary(entries, request_body)
