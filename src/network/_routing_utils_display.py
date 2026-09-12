"""Table/report rendering cluster for :mod:`src.network.routing_utils`.

Owns every pure display helper previously inlined on the parent class:
top-level renderers (``_display_forwarding_summary``,
``_display_routing_summary``, ``_display_ssr_routing`` and their
details/fallback siblings), stat accumulators
(``_collect_forwarding_stats``, ``_collect_routing_stats``,
``_collect_ssr_stats``, ``_accumulate_route_stats``), and pure
formatters (``_format_route_status``, ``_extract_prefix_group``,
``_update_set_if_present``).

The parent :class:`~src.network.routing_utils.RoutingUtils` binds an
instance as ``self._display`` and its ``__getattr__`` proxies unknown
attribute lookups back to the parent so shared state (dependencies,
apisession, parsing helpers) stays transparent. Thin delegators on the
parent expose the five entry points that tests call directly.

Keeping this cluster in its own module lets the parent file shrink
below compliance limits without a wrapper/alias shim, matching the
Phase 1 parsing-cluster split.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

from dataclasses import dataclass  # WHY: RoutingStatsAcc bundles 5 stat containers into one param
from typing import TYPE_CHECKING, Any  # WHY: TYPE_CHECKING avoids runtime cycle with parent

from prettytable import PrettyTable  # WHY: every table renderer builds a PrettyTable instance

if TYPE_CHECKING:  # WHY: only needed for static type checkers. Skipped at runtime
    from src.network.routing_utils import RoutingUtils  # WHY: parent type for cross-reference only


# WHY: sentinel token upstream uses to mean "no data" in tabular columns
_MISSING: str = "-"  # WHY: single-char placeholder aligns with legacy fallback renderer output

# WHY: single source of truth for SSR column ordering shared by main + fallback renderers
_SSR_COLUMNS: tuple[str, ...] = (
    "Destination",  # WHY: canonical column-1 label for SSR routing dumps
    "Next Hop",  # WHY: gateway IP for the route
    "Protocol",  # WHY: BGP/OSPF/... source protocol
    "Route Name",  # WHY: SSR-configured route name (may be empty)
    "Status",  # WHY: for example active/inactive per SSR row
    "Selection Reason",  # WHY: BGP selection reason string
    "Weight",  # WHY: route weight when supplied
    "Metric",  # WHY: metric column stringified upstream
    "Local Pref",  # WHY: BGP local preference
    "AS Path",  # WHY: BGP AS path attribute
    "VRF",  # WHY: routing-instance label (defaults to "default")
)

# WHY: forwarding-table column order for `_display_prefix_table_impl`
_FWD_COLUMNS: tuple[str, ...] = (
    "Destination",  # WHY: prefix column
    "Next Hop",  # WHY: gateway column
    "Interface",  # WHY: egress interface
    "Service",  # WHY: SSR service name if present
    "Table",  # WHY: routing-table identifier (mostly SSR)
    "Type",  # WHY: forwarding entry type
)

# WHY: routing-details column order shared with the fallback text renderer
_RIB_COLUMNS: tuple[str, ...] = (
    "Status",  # WHY: >/*/blank flag indicator
    "Destination",  # WHY: prefix
    "Next Hop",  # WHY: gateway
    "Interface",  # WHY: egress
    "Protocol",  # WHY: RIB protocol source
    "Admin Dist",  # WHY: administrative distance
)


@dataclass(frozen=True)
class RoutingStatsAcc:  # WHY: bundles the 5 routing stat buckets into one param
    """Mutable buckets used while accumulating routing-table statistics.

    ``frozen=True`` prevents the *reference* to each container from
    being swapped mid-loop. The containers themselves stay mutable so
    per-entry helpers add without re-wiring the accumulator. Bundling
    the five stat buckets into one dataclass drops
    ``_accumulate_route_stats`` from six parameters to two, resolving
    the STRUCT-PARAMS violation on the parent module.
    """

    protocols: dict[str, int]  # WHY: protocol keyword → occurrence count
    destinations: set[str]  # WHY: unique destination prefixes
    next_hops: set[str]  # WHY: unique next-hop gateways
    interfaces: set[str]  # WHY: unique egress interfaces
    tables: set[str]  # WHY: unique routing table names

    @classmethod
    def empty(cls) -> RoutingStatsAcc:  # WHY: factory for zero-state accumulator
        """Return a fresh accumulator with empty containers per field."""
        return cls(  # WHY: factory keeps call sites concise (one constructor for zero-state)
            protocols={},  # WHY: dict for count-by-name aggregation
            destinations=set(),  # WHY: set enforces uniqueness on prefixes
            next_hops=set(),  # WHY: set enforces uniqueness on gateway IPs
            interfaces=set(),  # WHY: set enforces uniqueness on iface names
            tables=set(),  # WHY: set enforces uniqueness on table names
        )


class _RoutingUtilsDisplay:  # WHY: cluster wrapper matches the Phase 1 parsing-cluster pattern
    """Wrapper class holding the extracted table/report display helpers."""

    def __init__(self, parent: RoutingUtils) -> None:  # WHY: bind parent so __getattr__ can proxy state
        """Store the parent :class:`RoutingUtils` for delegate lookups."""
        self._ru = parent  # WHY: enable __getattr__ delegation back to RoutingUtils

    def __getattr__(self, name: str) -> Any:  # WHY: transparent proxy so callers see combined API
        """Delegate unknown attributes to the wrapped parent object."""
        parent = self.__dict__.get("_ru")  # WHY: guard against half-initialized instances
        if parent is None:  # WHY: only trips during broken init. Avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly to callers
        return getattr(parent, name)  # WHY: transparent proxy to the parent RoutingUtils

    # ------------------------------------------------------------------
    # Forwarding-table renderers
    # ------------------------------------------------------------------

    def _display_forwarding_summary(self, entries: list[dict[str, Any]]) -> None:  # WHY: cluster entry
        """Display formatted summary of forwarding table entries."""
        if not entries:  # WHY: guard so empty results do not spam the table renderer
            print("-> No forwarding table entries found")  # WHY: user-facing empty-state notice
            return  # WHY: nothing else to render when entries list is empty
        print(f"-> Total forwarding entries: {len(entries)}")  # WHY: headline count first
        stats = self._collect_forwarding_stats(entries)  # WHY: single pass builds all buckets
        self._print_forwarding_stats(stats)  # WHY: helper keeps this method under LOC cap
        self._display_prefix_groups(entries)  # WHY: /16 rollup is separate from headline stats
        print("\n-> Forwarding table entries:")  # WHY: section header before detail table
        self._display_prefix_table_impl(entries)  # WHY: detailed row-per-entry dump

    @staticmethod
    def _print_forwarding_stats(stats: dict[str, Any]) -> None:  # WHY: split from summary for LOC cap
        """Print top services / tables / unique-endpoint counts from ``stats``."""
        if stats["services"]:  # WHY: skip block when no service metadata was captured
            top_services = sorted(  # WHY: top-5 services by count, descending order
                stats["services"].items(), key=lambda x: x[1], reverse=True
            )[:5]
            service_str = ", ".join(  # WHY: inline "svc(count)" format keeps output compact
                [f"{svc}({cnt})" for svc, cnt in top_services]
            )
            print(f"-> Top services: {service_str}")  # WHY: user-facing summary of hot services
        if len(stats["tables"]) > 1:  # WHY: single-table dumps make this line noise
            joined = ", ".join(sorted(stats["tables"]))  # WHY: sorted for deterministic output
            print(f"-> Forwarding tables: {joined}")  # WHY: emit multi-table roster
        print(f"-> Unique next hops: {len(stats['next_hops'])}")  # WHY: always report cardinality
        print(f"-> Unique interfaces: {len(stats['interfaces'])}")  # WHY: always report cardinality

    @staticmethod
    def _update_set_if_present(  # WHY: sentinel-aware add
        target_set: set[str], value: Any, sentinel: str = _MISSING
    ) -> None:
        """Add ``value`` to ``target_set`` if it is truthy and not the sentinel."""
        if value and value != sentinel:  # WHY: two-guard filter keeps "-" placeholders out
            target_set.add(value)  # WHY: sets deduplicate. Caller does not need to check membership

    def _collect_forwarding_stats(self, entries: list[dict[str, Any]]) -> dict[str, Any]:  # WHY: aggregator
        """Collect summary statistics from forwarding table entries."""
        services: dict[str, int] = {}  # WHY: service-name -> count map
        tables: set[str] = set()  # WHY: distinct routing tables
        next_hops: set[str] = set()  # WHY: distinct next-hops excluding sentinel
        interfaces: set[str] = set()  # WHY: distinct interfaces excluding sentinel
        for entry in entries:  # WHY: single pass keeps overall cost O(n)
            self._tally_fwd_service(entry, services)  # WHY: nested branch pulled into helper
            if entry.get("table"):  # WHY: only record real table strings
                tables.add(entry["table"])  # WHY: dedup via set semantics
            self._update_set_if_present(next_hops, entry.get("next_hop"))  # WHY: sentinel filter reused
            self._update_set_if_present(interfaces, entry.get("interface"))  # WHY: sentinel filter reused
        return {  # WHY: dict return shape matches legacy caller expectations
            "services": services,
            "tables": tables,
            "next_hops": next_hops,
            "interfaces": interfaces,
        }

    @staticmethod
    def _tally_fwd_service(entry: dict[str, Any], services: dict[str, int]) -> None:  # WHY: helper
        """Increment the per-service counter when ``entry`` carries a service name."""
        service = entry.get("service", "")  # WHY: default empty preserves falsiness guard
        if service:  # WHY: skip entries without a service label (most FIB rows)
            services[service] = services.get(service, 0) + 1  # WHY: default 0 keeps aggregation clean

    @staticmethod
    def _extract_prefix_group(dest: str) -> str | None:  # WHY: /16 grouping utility
        """Return the /16 group for an IPv4 destination prefix, or ``None``."""
        if not (dest and "/" in dest):  # WHY: reject empty/non-CIDR early
            return None  # WHY: unable to group without a CIDR mask
        prefix = dest.split("/")[0]  # WHY: drop the mask portion before splitting octets
        octets = prefix.split(".")  # WHY: split IPv4 dotted decimal for octet inspection
        if len(octets) < 2:  # WHY: /16 group needs the first two octets only
            return None  # WHY: malformed address cannot be grouped
        return f"{octets[0]}.{octets[1]}.0.0/16"  # WHY: canonical /16 label for grouping

    def _display_prefix_groups(self, entries: list[dict[str, Any]]) -> None:  # WHY: rollup renderer
        """Analyze and display top /16 prefix groups from entries."""
        prefix_groups: dict[str, int] = {}  # WHY: /16 group -> count map
        for entry in entries:  # WHY: one pass over entries
            group = self._extract_prefix_group(entry.get("destination", ""))  # WHY: delegate parsing
            if group:  # WHY: skip entries with unparseable destinations
                prefix_groups[group] = prefix_groups.get(group, 0) + 1  # WHY: increment count
        if prefix_groups:  # WHY: skip section entirely when nothing groups
            self._print_top_prefix_groups(prefix_groups)  # WHY: keeps this method under LOC cap

    @staticmethod
    def _print_top_prefix_groups(prefix_groups: dict[str, int]) -> None:  # WHY: top-5 renderer
        """Print the top-5 prefix groups sorted by count desc."""
        top_groups = sorted(prefix_groups.items(), key=lambda x: x[1], reverse=True)[:5]  # WHY: rank
        print("\n-> Top prefix groups:")  # WHY: section header for the rollup
        for group, count in top_groups:  # WHY: iterate in already-sorted order
            print(f"  - {group}: {count} entries")  # WHY: bullet-line per top group

    def _display_prefix_table_impl(self, entries: list[dict[str, Any]]) -> None:  # WHY: fwd renderer
        """Display forwarding table entries using PrettyTable."""
        if not entries:  # WHY: nothing to render when the list is empty
            return  # WHY: empty-state short-circuit avoids empty table output
        try:  # WHY: PrettyTable can fail with unusual terminals — fall back gracefully
            table = self._build_prefix_pretty_table(entries)  # WHY: builder isolated for testing
            print(table)  # WHY: render assembled PrettyTable to stdout
        except Exception:  # WHY: broad catch — any renderer failure routes to text fallback
            self._render_prefix_fallback(entries)  # WHY: text-mode display never fails

    _FWD_ROW_FIELDS: tuple[str, ...] = (  # WHY: forwarding-table row field order shared by renderers
        "destination",
        "next_hop",
        "interface",
        "service",
        "table",
        "type",
    )

    @staticmethod
    def _build_prefix_pretty_table(entries: list[dict[str, Any]]) -> PrettyTable:  # WHY: PrettyTable builder
        """Build a PrettyTable for forwarding-table entries."""
        table = PrettyTable()  # WHY: fresh table per invocation prevents state carryover
        table.field_names = list(_FWD_COLUMNS)  # WHY: shared column order between renderers
        table.align = "l"  # WHY: left-align mirrors legacy formatting
        for entry in entries:  # WHY: one row per parsed forwarding entry
            row = [entry.get(k, _MISSING) for k in _RoutingUtilsDisplay._FWD_ROW_FIELDS]  # WHY: shared field order
            table.add_row(row)  # WHY: single call keeps row projection out of the loop body
        return table  # WHY: caller handles printing so exceptions bubble up here

    @staticmethod
    def _render_prefix_fallback(entries: list[dict[str, Any]]) -> None:  # WHY: text-mode fallback path
        """Text fallback used when PrettyTable rendering fails."""
        for entry in entries:  # WHY: one compact line per entry when the table renderer breaks
            dest = entry.get("destination", _MISSING)  # WHY: safe lookup falls back to _MISSING sentinel
            nhop = entry.get("next_hop", _MISSING)  # WHY: safe lookup falls back to _MISSING sentinel
            iface = entry.get("interface", _MISSING)  # WHY: safe lookup falls back to _MISSING sentinel
            svc = entry.get("service", _MISSING)  # WHY: safe lookup falls back to _MISSING sentinel
            print(f"  {dest} -> {nhop} via {iface} [{svc}]")  # WHY: preserves legacy fallback shape

    # ------------------------------------------------------------------
    # Routing-table renderers
    # ------------------------------------------------------------------

    def _display_routing_summary(  # WHY: routing-table summary orchestrator (empty-state + stats + detail)
        self,
        route_entries: list[dict[str, Any]],
        query_params: dict[str, Any] | None = None,
    ) -> None:
        """Display formatted summary of routing table entries."""
        if not route_entries:  # WHY: dispatch to empty-state helper so this method stays short
            self._display_empty_routing(query_params)  # WHY: delegate empty-state formatting
            return  # WHY: no further stats to compute when the entry list is empty
        print(f"-> Total routing table entries: {len(route_entries)}")  # WHY: headline count first
        stats = self._collect_routing_stats(route_entries)  # WHY: single pass builds all buckets
        self._print_routing_stats(stats)  # WHY: fan-out kept in helper to keep this under LOC cap
        print("\n-> Detailed routing table:")  # WHY: section header before detail table
        self._display_routing_details(route_entries)  # WHY: detailed row-per-entry dump

    @staticmethod
    def _print_routing_stats(stats: dict[str, Any]) -> None:  # WHY: emit the four stats blocks
        """Print protocol / table / cardinality / active-route lines from ``stats``."""
        if stats["protocols"]:  # WHY: skip when nothing tracked a protocol
            proto_str = ", ".join([f"{p}({c})" for p, c in stats["protocols"].items()])  # WHY: join protocol tallies
            print(f"-> Protocols: {proto_str}")  # WHY: single formatted protocol summary line
        if len(stats["tables"]) > 1:  # WHY: single-table dumps make this line noise
            print(f"-> Routing tables: {', '.join(sorted(stats['tables']))}")  # WHY: sorted for determinism
        print(f"-> Unique destinations: {len(stats['destinations'])}")  # WHY: always report cardinality
        print(f"-> Unique next hops: {len(stats['next_hops'])}")  # WHY: always report cardinality
        print(f"-> Unique interfaces: {len(stats['interfaces'])}")  # WHY: always report cardinality
        if stats["active_routes"] > 0:  # WHY: only show active count when at least one exists
            print(f"-> Active routes (marked with >): {stats['active_routes']}")  # WHY: count formatted inline

    @staticmethod
    def _display_empty_routing(query_params: dict[str, Any] | None) -> None:  # WHY: empty-state renderer
        """Display message when no routing entries found."""
        print("-> No routing table entries found")  # WHY: uniform empty-state signal
        if query_params:  # WHY: only echo params when caller supplied them
            print("  -> Try adjusting query parameters:")  # WHY: guide the user toward a re-query
            for key, value in query_params.items():  # WHY: iterate in caller-supplied order
                print(f"    - {key}: {value}")  # WHY: one bullet per user-supplied filter

    def _collect_routing_stats(self, route_entries: list[dict[str, Any]]) -> dict[str, Any]:  # WHY: aggregator
        """Collect summary statistics from routing table entries."""
        acc = RoutingStatsAcc.empty()  # WHY: single dataclass replaces 5 local buckets
        active_routes = 0  # WHY: separate int counter — dataclass fields are containers only
        for entry in route_entries:  # WHY: single pass keeps overall cost O(n)
            self._accumulate_route_stats(entry, acc)  # WHY: mutates acc in place. Two params only
            if entry.get("active"):  # WHY: count active routes outside the acc for clarity
                active_routes += 1  # WHY: increment only on truthy 'active' field
        return {  # WHY: dict projection preserves the legacy return shape
            "protocols": acc.protocols,
            "destinations": acc.destinations,
            "next_hops": acc.next_hops,
            "interfaces": acc.interfaces,
            "tables": acc.tables,
            "active_routes": active_routes,
        }

    def _accumulate_route_stats(self, entry: dict[str, Any], acc: RoutingStatsAcc) -> None:  # WHY: per-entry
        """Accumulate statistics from a single route entry into ``acc``."""
        self._acc_protocol(entry, acc.protocols)  # WHY: protocol has custom uppercase rule
        self._acc_str_field(entry, "destination", acc.destinations)  # WHY: shared sentinel filter
        self._acc_str_field(entry, "next_hop", acc.next_hops)  # WHY: shared sentinel filter
        self._acc_str_field(entry, "interface", acc.interfaces)  # WHY: shared sentinel filter
        if entry.get("table"):  # WHY: table has no sentinel — just truthy check
            acc.tables.add(entry["table"])  # WHY: set add dedups when multiple entries share a table

    @staticmethod
    def _acc_protocol(entry: dict[str, Any], protocols: dict[str, int]) -> None:  # WHY: protocol tallier
        """Increment protocol counter when ``entry`` carries a known protocol."""
        proto = entry.get("protocol", "Unknown").upper()  # WHY: normalize case for aggregation
        if proto and proto != "UNKNOWN":  # WHY: skip default-unknown rows to keep counts meaningful
            protocols[proto] = protocols.get(proto, 0) + 1  # WHY: default 0 keeps aggregation clean

    @staticmethod
    def _acc_str_field(entry: dict[str, Any], key: str, bucket: set[str]) -> None:  # WHY: generic bucket
        """Add ``entry[key]`` to ``bucket`` when it is truthy and not a sentinel."""
        value = entry.get(key)  # WHY: single lookup for both guards
        if value and value not in (_MISSING, ""):  # WHY: legacy filter set — keep behavior identical
            bucket.add(value)  # WHY: sets deduplicate so we do not need to pre-check membership

    def _display_routing_details(self, route_entries: list[dict[str, Any]]) -> None:
        """Display detailed routing table in a formatted table."""
        if not route_entries:  # WHY: skip renderer entirely on empty input
            return
        try:  # WHY: PrettyTable can fail with unusual terminals — text fallback below
            table = self._build_routing_details_table(route_entries)  # WHY: builder isolated
            print(table)
            self._print_rib_status_legend()  # WHY: legend printed after every successful table
        except Exception:  # WHY: broad catch — any renderer failure routes to text fallback
            self._display_routing_details_fallback(route_entries)  # WHY: text-mode never fails

    def _build_routing_details_table(self, route_entries: list[dict[str, Any]]) -> PrettyTable:
        """Build a PrettyTable for routing-details display."""
        table = PrettyTable()  # WHY: fresh table per invocation prevents state carryover
        table.field_names = list(_RIB_COLUMNS)  # WHY: shared column order with fallback
        table.align = "l"  # WHY: left-align mirrors legacy formatting
        for entry in route_entries:  # WHY: one row per route entry
            table.add_row(self._rib_row_values(entry))  # WHY: helper keeps row projection out of loop
        return table  # WHY: caller handles printing so exceptions bubble up here

    # WHY: RIB row field order used by both PrettyTable and text-fallback row projections
    _RIB_ROW_FIELDS: tuple[str, ...] = (
        "destination",  # WHY: prefix column
        "next_hop",  # WHY: gateway column
        "interface",  # WHY: egress interface column
        "protocol",  # WHY: RIB protocol source column
        "admin_distance",  # WHY: administrative-distance column
    )

    def _rib_row_values(self, entry: dict[str, Any]) -> list[str]:
        """Project a routing-details row into the shared column order."""
        status = self._format_route_status(entry)  # WHY: composed status prefix >/*/blank
        # WHY: comprehension collapses 5 branchy ``or "-"`` guards into one loop for CC <= 5
        fields = [entry.get(key) or _MISSING for key in self._RIB_ROW_FIELDS]
        return [status, *fields]  # WHY: prepend status to keep _RIB_COLUMNS ordering

    @staticmethod
    def _print_rib_status_legend() -> None:
        """Print the RIB status-flag legend beneath a details table."""
        print("\nStatus Legend:")  # WHY: aligns with legacy user-facing output
        print("  > = Active route (installed in forwarding table)")  # WHY: explain > flag
        print("  * = Selected route (best route among alternatives)")  # WHY: explain * flag

    @staticmethod
    def _format_route_status(entry: dict[str, Any]) -> str:
        """Format the status indicator for a route entry."""
        status = ""  # WHY: accumulate flags in caller-visible order
        if entry.get("active"):  # WHY: > marker takes visual precedence
            status += ">"
        if entry.get("selected"):  # WHY: * marker follows the active flag
            status += "*"
        return status if status else " "  # WHY: blank space preserves column alignment

    def _display_routing_details_fallback(self, route_entries: list[dict[str, Any]]) -> None:
        """Text fallback for routing-details when PrettyTable is unavailable."""
        header = "   Status | Destination              | Next Hop        | Interface       | Protocol | Dist"
        print(header)  # WHY: mimic the PrettyTable header row
        print("   " + "-" * 95)  # WHY: divider width chosen to match legacy output
        for entry in route_entries:  # WHY: one line per entry
            self._print_rib_fallback_row(entry)  # WHY: helper keeps per-row projection isolated
        print("\nStatus Legend:")  # WHY: legend still emitted in fallback mode
        print("  > = Active route, * = Selected route")  # WHY: shortened legend for text mode

    def _print_rib_fallback_row(self, entry: dict[str, Any]) -> None:
        """Print one RIB row in text-fallback mode."""
        status = self._format_route_status(entry)  # WHY: reuse the shared flag formatter
        dest = entry.get("destination", _MISSING)
        next_hop = entry.get("next_hop", _MISSING)
        interface = entry.get("interface", _MISSING)
        protocol = entry.get("protocol", _MISSING)
        admin_dist = entry.get("admin_distance", _MISSING)
        print(f"   {status:<6} | {dest:<25} | {next_hop:<15} | {interface:<15} | {protocol:<8} | {admin_dist}")

    # ------------------------------------------------------------------
    # SSR/SRX routing renderers
    # ------------------------------------------------------------------

    def _display_ssr_routing(
        self,
        route_entries: list[dict[str, Any]],
        query_params: dict[str, Any] | None = None,
    ) -> None:
        """Display SSR/SRX routing table with BGP-specific columns."""
        if not route_entries:  # WHY: reuse the generic empty-state helper
            self._display_empty_routing(query_params)
            return
        stats = self._collect_ssr_stats(route_entries)  # WHY: single pass builds all summaries
        print(f"-> Total routing table entries: {len(route_entries)}")  # WHY: headline count first
        print(f"-> Protocols: {stats['protocol_summary']}")  # WHY: SSR-specific protocol rollup
        print(f"-> VRFs: {stats['vrf_summary']}")  # WHY: SSR-specific VRF rollup
        print(f"-> Unique next hops: {len(stats['next_hops'])}")  # WHY: cardinality line
        self._display_ssr_table(route_entries)  # WHY: detailed row-per-entry SSR dump

    def _collect_ssr_stats(self, route_entries: list[dict[str, Any]]) -> dict[str, Any]:
        """Collect summary statistics from SSR routing entries."""
        protocols: dict[str, int] = {}  # WHY: protocol-name -> count map
        vrfs: dict[str, int] = {}  # WHY: vrf-name -> count map
        next_hops: set[str] = set()  # WHY: unique next-hop gateways (minus 0.0.0.0 sentinel)
        for entry in route_entries:  # WHY: single pass keeps cost O(n)
            self._tally_ssr_entry(entry, protocols, vrfs, next_hops)  # WHY: nested logic in helper
        return {  # WHY: legacy return shape kept intact for downstream callers
            "protocol_summary": ", ".join([f"{p}({c})" for p, c in protocols.items()]),
            "vrf_summary": ", ".join([f"{v}({c})" for v, c in vrfs.items()]),
            "next_hops": next_hops,
        }

    @staticmethod
    def _tally_ssr_entry(
        entry: dict[str, Any],
        protocols: dict[str, int],
        vrfs: dict[str, int],
        next_hops: set[str],
    ) -> None:
        """Update SSR protocol/VRF counters and next-hop set from ``entry``."""
        protocol = entry.get("protocol", "Unknown")  # WHY: SSR labels default to "Unknown"
        protocols[protocol] = protocols.get(protocol, 0) + 1  # WHY: default 0 keeps aggregation clean
        vrf = entry.get("vrf", "default")  # WHY: SSR default VRF label is literal "default"
        vrfs[vrf] = vrfs.get(vrf, 0) + 1  # WHY: default 0 keeps aggregation clean
        next_hop = entry.get("next_hop", "")  # WHY: extract before sentinel comparison
        if next_hop and next_hop != "0.0.0.0":  # nosec B104  # WHY: skip default-route sentinel
            next_hops.add(next_hop)  # WHY: sets deduplicate for uniqueness count

    def _display_ssr_table(self, route_entries: list[dict[str, Any]]) -> None:
        """Display SSR routing entries using PrettyTable with fallback."""
        try:  # WHY: PrettyTable can fail with unusual terminals — text fallback below
            table = self._build_ssr_pretty_table(route_entries)  # WHY: builder isolated
            print("\n-> Detailed routing table:")  # WHY: section header before table print
            print(table)
        except Exception:  # WHY: broad catch — any renderer failure routes to text fallback
            self._display_ssr_table_fallback(route_entries)  # WHY: text-mode never fails

    def _build_ssr_pretty_table(self, route_entries: list[dict[str, Any]]) -> PrettyTable:
        """Build a PrettyTable for SSR routing entries."""
        table = PrettyTable()  # WHY: fresh table per invocation prevents state carryover
        table.field_names = list(_SSR_COLUMNS)  # WHY: shared column order with fallback
        table.align = "l"  # WHY: left-align mirrors legacy formatting
        for entry in route_entries:  # WHY: one row per SSR entry
            table.add_row(self._ssr_row_values(entry))  # WHY: helper keeps row projection out of loop
        return table  # WHY: caller handles printing so exceptions bubble up here

    @staticmethod
    def _ssr_row_values(entry: dict[str, Any]) -> list[str]:
        """Project an SSR entry into the shared column order."""
        return [  # WHY: keep column order aligned with _SSR_COLUMNS
            entry.get("destination", _MISSING),
            entry.get("next_hop", _MISSING),
            entry.get("protocol", _MISSING),
            entry.get("name", _MISSING),
            entry.get("status", _MISSING),
            entry.get("selection_reason", _MISSING),
            entry.get("weight", _MISSING),
            entry.get("metric", _MISSING),
            entry.get("local_preference", _MISSING),
            entry.get("as_path", _MISSING),
            entry.get("vrf", "default"),  # WHY: SSR VRF default label is "default", not "-"
        ]

    def _display_ssr_table_fallback(self, route_entries: list[dict[str, Any]]) -> None:
        """Text fallback display for SSR routing entries."""
        print("\n-> Detailed routing table:")  # WHY: matches non-fallback section header
        header = (
            "   Destination | Next Hop | Protocol | Route Name | Status"
            " | Selection Reason | Weight | Metric | Local Pref | AS Path | VRF"
        )
        print(header)  # WHY: mimic the PrettyTable header row
        print("   " + "-" * 140)  # WHY: divider width chosen to match legacy output
        for entry in route_entries:  # WHY: one line per SSR entry
            self._print_ssr_fallback_row(entry)  # WHY: helper keeps per-row projection isolated

    @staticmethod
    def _print_ssr_fallback_row(entry: dict[str, Any]) -> None:
        """Print one SSR row in text-fallback mode."""
        dest = entry.get("destination", _MISSING)
        nhop = entry.get("next_hop", _MISSING)
        proto = entry.get("protocol", _MISSING)
        name = entry.get("name", _MISSING)
        status = entry.get("status", _MISSING)
        reason = entry.get("selection_reason", _MISSING)
        weight = entry.get("weight", _MISSING)
        metric = entry.get("metric", _MISSING)
        lpref = entry.get("local_preference", _MISSING)
        aspath = entry.get("as_path", _MISSING)
        vrf = entry.get("vrf", "default")  # WHY: SSR VRF default label is "default", not "-"
        print(
            f"   {dest} | {nhop} | {proto} | {name} | {status}"
            f" | {reason} | {weight} | {metric} | {lpref} | {aspath} | {vrf}"
        )
