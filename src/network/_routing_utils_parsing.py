"""Pure route-line parsing helpers extracted from ``routing_utils``.

Owns the token/line-level parsers that convert raw device output
(Juniper multi-line, tabular, SSR JSON) into normalized route entry
dicts. The parent :class:`~src.network.routing_utils.RoutingUtils`
binds an instance as ``self._parsing`` and delegates the public
parsing surface to it; ``__getattr__`` on this wrapper proxies unknown
attribute lookups back to the parent so shared state (dependencies,
apisession, helpers) stays transparent.

Keeping this cluster in its own module lets the parent file shrink
below compliance limits without creating a wrapper/alias shim.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import json  # WHY: SSR routing output arrives as a JSON payload from the API
import logging  # WHY: emit warning when SSR JSON is malformed (production visibility)
import re  # WHY: multiple parsers use regex to pluck fields out of legacy text formats
from typing import TYPE_CHECKING, Any  # WHY: TYPE_CHECKING avoids runtime import cycle with parent

if TYPE_CHECKING:  # WHY: only needed for static type checkers. Skipped at runtime
    from src.network.routing_utils import RoutingUtils  # WHY: parent type for cross-reference only


# WHY: protocol keywords carried inline in tabular/protocol route lines
_PROTOCOL_TOKENS: frozenset[str] = frozenset(
    {"BGP", "OSPF", "STATIC", "DIRECT", "LOCAL"}  # WHY: uppercase set for O(1) membership lookup
)

# WHY: interface-name prefixes recognized across Juniper/SSR/Linux flavors
_INTERFACE_PREFIXES: tuple[str, ...] = ("eth", "ge-", "xe-", "et-", "lo", "irb")

# WHY: precompiled IPv4 regex reused across route-part classification
_IPV4_RE: re.Pattern[str] = re.compile(r"\d+\.\d+\.\d+\.\d+")

# WHY: matches ``inet.0:`` / ``inet6.0:`` table headers in Juniper output
_JUNIPER_TABLE_RE: re.Pattern[str] = re.compile(r"^(\S+\.0):\s")

# WHY: destination line with optional ``>*`` flag prefix + IPv4/IPv6 prefix
_JUNIPER_DEST_RE: re.Pattern[str] = re.compile(r"^([>*\s]*)([\d\.]+/\d+|[\da-f:]+/\d+)\s")

# WHY: ``[proto/distance]`` bracketed protocol+admin-distance pair on Juniper dest line
_JUNIPER_PROTO_RE: re.Pattern[str] = re.compile(r"\[(\w+)/(\d+)\]")

# WHY: ``via <next-hop>`` fragment on Juniper continuation lines
_VIA_RE: re.Pattern[str] = re.compile(r"via\s+(\S+)")


def _empty_route_entry() -> dict[str, Any]:  # WHY: canonical shape reused by tabular/juniper builders
    """Return a fresh route-entry dict with every field zero-initialized."""
    return {  # WHY: dict literal is cheaper and clearer than dict(...) constructor
        "destination": "",  # WHY: prefix/CIDR string. Empty until a parser fills it
        "next_hop": "",  # WHY: gateway address. Empty for connected/local routes
        "interface": "",  # WHY: egress interface name. Empty when not known
        "protocol": "",  # WHY: BGP/OSPF/STATIC/... routing protocol tag
        "admin_distance": "",  # WHY: administrative distance kept as string for uniform display
        "metric": "",  # WHY: route metric kept as string for uniform display
        "active": False,  # WHY: mirrors Juniper ``>`` flag (installed in fwd table)
        "selected": False,  # WHY: mirrors Juniper ``*`` flag (best of alternatives)
    }


class _RoutingUtilsParsing:  # WHY: cluster wrapper matching the ``_packet_capture_tcpdump`` pattern
    """Wrapper class holding the extracted route-parsing helpers."""

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
    # Protocol-line token classification
    # ------------------------------------------------------------------

    def _classify_route_part(self, entry: dict[str, Any], part: str) -> None:
        """Classify a single token from a protocol route line into ``entry``.

        Uses a dispatch chain of early-return handlers so cyclomatic
        complexity and nesting stay well under the compliance limits.
        """
        # WHY: each handler returns True when it consumes ``part``. Short-circuit stops the chain
        if self._set_protocol_token(entry, part):  # WHY: BGP/OSPF/STATIC/... keyword match
            return  # WHY: keep nesting flat by exiting as soon as one handler succeeds
        if self._set_cidr_destination(entry, part):  # WHY: CIDR (``a.b.c.d/N``) → destination
            return  # WHY: prevent later IPv4 handler from re-matching the prefix half
        if self._set_ipv4_endpoint(entry, part):  # WHY: bare IPv4 → destination or next_hop
            return  # WHY: only fall through to interface check when part is not an IP
        self._set_interface_token(entry, part)  # WHY: last-resort handler for known iface prefixes

    @staticmethod
    def _set_protocol_token(entry: dict[str, Any], part: str) -> bool:
        """Set ``entry['protocol']`` if ``part`` is a known protocol keyword."""
        upper = part.upper()  # WHY: normalize to match uppercase _PROTOCOL_TOKENS
        if upper not in _PROTOCOL_TOKENS:  # WHY: guard clause. Leaves entry untouched on miss
            return False  # WHY: signal caller to try the next handler
        entry["protocol"] = upper  # WHY: store normalized uppercase form for uniform display
        return True  # WHY: caller stops the classification chain

    @staticmethod
    def _set_cidr_destination(entry: dict[str, Any], part: str) -> bool:
        """Assign a CIDR-form token to ``entry['destination']``."""
        if "/" not in part or "." not in part:  # WHY: require both slash + dot to look like CIDR
            return False  # WHY: not CIDR — let the IPv4/interface handlers try
        entry["destination"] = part  # WHY: CIDR always represents the prefix, never the next-hop
        return True  # WHY: consumed the token

    @staticmethod
    def _set_ipv4_endpoint(entry: dict[str, Any], part: str) -> bool:
        """Fill ``destination`` (then ``next_hop``) when ``part`` is a bare IPv4."""
        if not _IPV4_RE.match(part):  # WHY: guard clause keeps the assignment logic single-depth
            return False  # WHY: not IPv4 — defer to the interface handler
        if not entry["destination"]:  # WHY: first bare IPv4 in a line is the destination
            entry["destination"] = part  # WHY: fill destination slot first
        elif not entry["next_hop"]:  # WHY: second bare IPv4 is the next-hop gateway
            entry["next_hop"] = part  # WHY: fill next_hop only when destination is already set
        return True  # WHY: consumed regardless of which field was filled

    @staticmethod
    def _set_interface_token(entry: dict[str, Any], part: str) -> bool:
        """Assign ``part`` to ``entry['interface']`` when it looks like an iface name."""
        if not part.startswith(_INTERFACE_PREFIXES):  # WHY: reject unknown tokens instead of guessing
            return False  # WHY: leave entry untouched so classifier is idempotent
        entry["interface"] = part  # WHY: preserve original casing for downstream display
        return True  # WHY: token consumed

    # ------------------------------------------------------------------
    # Tabular route-line parsing
    # ------------------------------------------------------------------

    def _parse_tabular_route_line(self, line: str) -> dict[str, Any] | None:
        """Parse a space-separated tabular route line into a route entry."""
        parts = line.split()  # WHY: whitespace-split into tokens for positional access
        if len(parts) < 2:  # need at least destination + next-hop  # WHY: guard clause
            return None  # WHY: single-token lines are section headers, not routes
        entry = _empty_route_entry()  # WHY: shared factory keeps field order/shape uniform
        entry["destination"] = parts[0]  # WHY: default when no flag prefix consumed parts[0]
        parts = self._apply_tabular_flags(entry, parts, line)  # WHY: reslice when >/* flags present
        self._fill_tabular_fields(entry, parts)  # WHY: positional fill for remaining tokens
        return entry  # WHY: caller distinguishes None (skip) from valid entry

    @staticmethod
    def _apply_tabular_flags(
        entry: dict[str, Any],
        parts: list[str],
        line: str,
    ) -> list[str]:
        """Extract active/selected flags from a tabular line and reslice ``parts``."""
        if not (line.startswith(">") or line.startswith("*")):  # WHY: guard: no flag prefix present
            return parts  # WHY: leave parts untouched when there is no ``>``/``*`` prefix
        head = line[:3]  # WHY: only the first 3 chars can hold both flag markers plus a space
        entry["active"] = ">" in head  # WHY: preserve legacy detection window
        entry["selected"] = "*" in head  # WHY: preserve legacy detection window
        entry["destination"] = parts[1] if len(parts) > 1 else parts[0]  # WHY: flag pushes dest to [1]
        return parts[1:]  # WHY: shift so subsequent positional fills line up with dest-at-index-0

    @staticmethod
    def _fill_tabular_fields(entry: dict[str, Any], parts: list[str]) -> None:
        """Fill next-hop / interface / protocol / admin_distance from positional tokens."""
        # WHY: table below maps 1-based positional index to entry key for uniform assignment
        positional: tuple[tuple[int, str], ...] = (
            (1, "next_hop"),  # WHY: parts[1] is the gateway address in the tabular format
            (2, "interface"),  # WHY: parts[2] is the egress interface
            (3, "protocol"),  # WHY: parts[3] is the routing protocol keyword
            (4, "admin_distance"),  # WHY: parts[4] is the administrative distance
        )
        for idx, key in positional:  # WHY: single loop replaces four ``if len(parts) > N`` blocks
            if len(parts) > idx:  # WHY: guard against short rows without inflating complexity
                entry[key] = parts[idx]  # WHY: assign matching field only when data is present

    # ------------------------------------------------------------------
    # Juniper multi-line route parsing
    # ------------------------------------------------------------------

    def _process_juniper_line(
        self,
        line_stripped: str,
        routes: list[dict[str, Any]],
        current_route: dict[str, Any],
        current_table: str,
    ) -> tuple[dict[str, Any], str]:
        """Dispatch a single stripped Juniper line to the correct sub-parser."""
        table_match = _JUNIPER_TABLE_RE.match(line_stripped)  # WHY: table header wins over dest match
        if table_match:  # WHY: early-return keeps the destination/continuation logic flat
            return self._finalize_table_transition(routes, current_route, table_match)  # WHY: reused
        dest_match = _JUNIPER_DEST_RE.match(line_stripped)  # WHY: attempt to start a new route entry
        if dest_match:  # WHY: destination line flushes the in-flight route (if any)
            return self._finalize_dest_transition(  # WHY: helper isolates flush+build side effects
                routes, current_route, dest_match, line_stripped, current_table
            )
        if current_route:  # WHY: continuation lines only make sense inside an active route
            self._update_juniper_via(current_route, line_stripped)  # WHY: mutate in place
        return current_route, current_table  # WHY: preserve state when line matches nothing

    @staticmethod
    def _finalize_table_transition(
        routes: list[dict[str, Any]],
        current_route: dict[str, Any],
        table_match: re.Match[str],
    ) -> tuple[dict[str, Any], str]:
        """Flush pending route and switch to the new Juniper routing table."""
        if current_route:  # WHY: preserve the in-flight route before wiping state
            routes.append(current_route)  # WHY: entering a new table means the previous route is done
        return {}, table_match.group(1)  # WHY: reset current_route and adopt the new table name

    def _finalize_dest_transition(
        self,
        routes: list[dict[str, Any]],
        current_route: dict[str, Any],
        dest_match: re.Match[str],
        line_stripped: str,
        current_table: str,
    ) -> tuple[dict[str, Any], str]:
        """Flush pending route and start a new route from a destination line."""
        if current_route:  # WHY: flush previous entry before starting a fresh one
            routes.append(current_route)  # WHY: keep append order matching input line order
        new_route = self._build_juniper_route(dest_match, line_stripped, current_table)  # WHY: build
        return new_route, current_table  # WHY: table stays. Only the current route advances

    @staticmethod
    def _build_juniper_route(
        dest_match: re.Match[str],
        line_stripped: str,
        current_table: str,
    ) -> dict[str, Any]:
        """Build a new route entry from a Juniper destination line."""
        flags = dest_match.group(1).strip()  # WHY: capture group 1 holds any leading ``>``/``*``
        route = _empty_route_entry()  # WHY: shared factory keeps the field set in sync
        route["destination"] = dest_match.group(2)  # WHY: capture group 2 is the prefix (v4 or v6)
        route["active"] = ">" in flags  # WHY: ``>`` marks the installed/active route
        route["selected"] = "*" in flags  # WHY: ``*`` marks the selected best route
        route["table"] = current_table  # WHY: preserve routing-table context (inet.0/inet6.0/...)
        proto_match = _JUNIPER_PROTO_RE.search(line_stripped)  # WHY: optional ``[proto/distance]`` pair
        if proto_match:  # WHY: absent on some legacy formats — leave defaults untouched
            route["protocol"] = proto_match.group(1)  # WHY: capture group 1 is the protocol keyword
            route["admin_distance"] = proto_match.group(2)  # WHY: capture group 2 is the distance
        return route  # WHY: caller stores this as the new ``current_route``

    def _update_juniper_via(
        self,
        current_route: dict[str, Any],
        line_stripped: str,
    ) -> None:
        """Update ``current_route`` with next-hop / interface info from a continuation line."""
        via_match = _VIA_RE.search(line_stripped)  # WHY: most continuation lines carry ``via <hop>``
        if via_match:  # WHY: hand off to helper that dispatches by via-token shape
            self._apply_via_match(current_route, via_match.group(1))  # WHY: keeps complexity flat
            return  # WHY: early-return prevents fallback handlers from double-writing fields
        if line_stripped == "Local":  # WHY: Juniper emits the literal token for locally-hosted routes
            current_route["next_hop"] = "Local"  # WHY: preserve display exactly as the router shows it
            return  # WHY: guard keeps interface-only branch from firing on the same line
        # WHY: bare ``ge-0/0/0.0``-style continuation line → treat as interface hint
        if "." in line_stripped and len(line_stripped.split()) == 1:
            current_route["interface"] = line_stripped  # WHY: single dotted token → interface name

    @staticmethod
    def _apply_via_match(current_route: dict[str, Any], via_token: str) -> None:
        """Classify a ``via`` fragment into next-hop or interface on ``current_route``."""
        via_parts = via_token.rstrip(",")  # WHY: strip trailing comma emitted by some releases
        if _IPV4_RE.match(via_parts):  # WHY: ``via 10.0.0.1`` → gateway IPv4 next-hop
            current_route["next_hop"] = via_parts  # WHY: store normalized (comma-stripped) form
            return  # WHY: early-return keeps subsequent checks from firing on same token
        if "." in via_parts and "/" not in via_parts:  # WHY: interface names have dot but no slash
            current_route["interface"] = via_parts.strip()  # WHY: for example ``ge-0/0/0.0``
            return  # WHY: guard prevents fallthrough from also setting next_hop
        current_route["next_hop"] = via_parts.strip()  # WHY: fallback (hostname/non-numeric next-hop)

    # ------------------------------------------------------------------
    # SSR/SRX JSON routing table parsing
    # ------------------------------------------------------------------

    def _parse_ssr_routing(self, json_data: str) -> list[dict[str, Any]]:
        """Parse SSR/SRX routing table JSON returned by the dedicated API."""
        payload = self._decode_ssr_payload(json_data)  # WHY: isolate JSON errors from row projection
        if payload is None:  # WHY: guard covers decode failure and non-SUCCESS status
            return []  # WHY: empty result is the documented sentinel for callers
        rows = payload.get("rows", [])  # WHY: ``rows`` holds the projected route table
        if not payload.get("columns") or not rows:  # WHY: schema requires both to be non-empty
            return []  # WHY: nothing to project when either half of the schema is missing
        protocol = self._infer_ssr_protocol(payload.get("message", ""))  # WHY: single lookup per call
        return [self._ssr_row_to_entry(row, protocol) for row in rows]  # WHY: uniform per-row build

    @staticmethod
    def _decode_ssr_payload(json_data: str) -> dict[str, Any] | None:
        """Decode SSR JSON and validate status. Return ``None`` on any failure."""
        try:  # WHY: SSR JSON can be truncated or malformed in real traffic
            data = json.loads(json_data)  # WHY: only place json.loads runs for SSR parsing
        except (json.JSONDecodeError, KeyError, TypeError) as error:  # WHY: match legacy exception set
            logging.warning("Failed to parse SSR routing JSON: %s", error)  # WHY: production visibility
            return None  # WHY: caller returns [] so the display layer can surface an empty table
        if not isinstance(data, dict):  # WHY: guard against list/str payloads slipping through
            return None  # WHY: only object-shaped SSR responses carry ``status``/``rows``
        if data.get("status") != "SUCCESS":  # WHY: any non-success indicates the API refused the query
            return None  # WHY: signal empty-result semantics uniformly
        return data  # WHY: caller extracts columns/rows from here

    @staticmethod
    def _infer_ssr_protocol(message: str) -> str:
        """Infer a protocol label from the SSR response ``message`` field."""
        # WHY: the SSR API embeds hints like "bgp routes" / "static routes" in the message string
        return "BGP" if "bgp" in message.lower() else "Unknown"  # WHY: extend when other hints appear

    @staticmethod
    def _ssr_row_to_entry(row: dict[str, Any], protocol: str) -> dict[str, Any]:
        """Project a single SSR row into a normalized route entry dict."""
        return {  # WHY: dict literal keeps column projection concise and readable
            "destination": row.get("prefix", ""),  # WHY: SSR names the destination column ``prefix``
            "next_hop": row.get("nextHops", ""),  # WHY: SSR aggregates next-hops as a string
            "interface": "",  # WHY: SSR JSON does not carry interface names in this endpoint
            "protocol": protocol,  # WHY: caller-supplied so all rows share the same label
            "admin_distance": "",  # WHY: SSR does not expose admin distance in this response
            "metric": str(row.get("metric", "")),  # WHY: coerce int→str for uniform display formatting
            "status": row.get("status", ""),  # WHY: for example active/inactive per row
            "vrf": row.get("vrfName", "default"),  # WHY: SSR uses ``vrfName`` (camelCase)
            "name": row.get("name", ""),  # WHY: optional route name assigned in SSR config
            "weight": str(row.get("weight", "")),  # WHY: coerce int→str for uniform display formatting
            "as_path": row.get("path", ""),  # WHY: BGP AS path string when protocol is BGP
            "local_preference": str(row.get("localPreference", "")),  # WHY: BGP local preference
            "selection_reason": row.get("selectionReason", ""),  # WHY: BGP selection reason
        }

    # ------------------------------------------------------------------
    # Top-level routing-table dispatch + text/JSON sub-parsers
    # ------------------------------------------------------------------

    def _parse_routing_table(self, raw_output: str) -> list[dict[str, Any]]:
        """Parse routing table output supporting multiple formats."""
        if not raw_output:  # WHY: empty input has no routes to project
            return []  # WHY: caller renders "no data" from an empty list
        json_result = self._try_parse_routing_json(raw_output)  # WHY: JSON is the preferred format
        if json_result is not None:  # WHY: guard clause — JSON parsed cleanly
            return json_result  # WHY: skip text-format fallbacks entirely
        lines = raw_output.strip().split("\n")  # WHY: split once for both juniper/text branches
        if self._looks_like_juniper(lines):  # WHY: split-out predicate keeps CC ≤5
            return self._parse_juniper_routing(raw_output)  # WHY: multi-line juniper parser
        return self._parse_routing_text_lines(lines)  # WHY: last-resort text-line parser

    @staticmethod
    def _looks_like_juniper(lines: list[str]) -> bool:
        """Return True when the first 20 lines contain an inet.0/inet6.0 marker."""
        # WHY: probing only the first 20 lines matches legacy behavior (bounded scan)
        return any("inet.0" in line or "inet6.0" in line for line in lines[:20])

    def _try_parse_routing_json(self, raw_output: str) -> list[dict[str, Any]] | None:
        """Try parsing routing output as JSON. Returns None if not JSON."""
        try:  # WHY: real router output is frequently non-JSON — catch and fall through
            data = json.loads(raw_output)  # WHY: single json.loads for the whole payload
        except (json.JSONDecodeError, TypeError):  # WHY: match legacy exception set exactly
            return None  # WHY: None signals caller to try text-format parsers next
        if isinstance(data, list):  # WHY: top-level list → list of route dicts
            return self._normalize_json_route_list(data)  # WHY: helper keeps CC ≤5
        if isinstance(data, dict):  # WHY: top-level dict → routes nested under some key
            return self._extract_routes_from_json_dict(data)  # WHY: recover nested payloads
        return None  # WHY: unexpected shape — let caller try text parsers

    def _normalize_json_route_list(self, data: list[Any]) -> list[dict[str, Any]]:
        """Normalize a top-level JSON list of route dicts."""
        # WHY: skip non-dict entries so malformed items do not crash the projection
        return [self._normalize_json_route_entry(item) for item in data if isinstance(item, dict)]

    def _extract_routes_from_json_dict(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract route entries from a JSON dict with list values."""
        routes: list[dict[str, Any]] = []  # WHY: accumulator for projected route entries
        for _key, value in data.items():  # WHY: iterate top-level fields looking for list payloads
            if isinstance(value, list):  # WHY: only list values carry the route rows
                for item in value:  # WHY: each element is expected to be a route dict
                    if isinstance(item, dict):  # WHY: guard against malformed non-dict rows
                        routes.append(self._normalize_json_route_entry(item))  # WHY: project it
        return routes  # WHY: caller renders empty list as "no routes"

    def _parse_routing_text_lines(self, lines: list[str]) -> list[dict[str, Any]]:
        """Parse text-format routing lines into route entries."""
        route_entries: list[dict[str, Any]] = []  # WHY: accumulator for parsed route entries
        for line in lines:  # WHY: iterate every input line
            stripped = line.strip()  # WHY: normalize whitespace once
            if self._should_skip_route_line(stripped):  # WHY: split-out predicate keeps CC ≤5
                continue  # WHY: skip blank/comment/divider lines
            entry = self._ru._classify_and_parse_route_line(stripped)  # WHY: proxy to routing cluster
            if entry:  # WHY: classifier returns None for lines it cannot parse
                route_entries.append(entry)  # WHY: collect only successfully parsed entries
        return route_entries  # WHY: caller renders empty list when nothing classified

    @staticmethod
    def _should_skip_route_line(line: str) -> bool:
        """Return True for empty/comment/divider lines in a text-format routing dump."""
        # WHY: consolidates the three legacy skip conditions into a single predicate
        return not line or line.startswith("#") or line.startswith("---")

    def _parse_standard_route_line(self, line: str) -> dict[str, Any] | None:
        """Parse a route line with via/dev/proto keywords."""
        entry = _empty_route_entry()  # WHY: shared factory keeps route-entry shape uniform
        entry, line = self._extract_route_flags(entry, line)  # WHY: consume leading >/* markers
        parts = line.split()  # WHY: whitespace-split for the destination token
        if parts:  # WHY: guard against fully-consumed lines
            entry["destination"] = parts[0]  # WHY: first token is always the destination
        via_match = re.search(r"via\s+(\S+)", line)  # WHY: "via <next-hop>" fragment
        if via_match:  # WHY: guard: line may omit via keyword
            entry["next_hop"] = via_match.group(1)  # WHY: capture group 1 is the next-hop
        dev_match = re.search(r"dev\s+(\S+)", line)  # WHY: "dev <interface>" fragment
        if dev_match:  # WHY: guard: line may omit dev keyword
            entry["interface"] = dev_match.group(1)  # WHY: capture group 1 is the interface
        proto_match = re.search(r"proto\s+(\S+)", line)  # WHY: "proto <name>" fragment
        if proto_match:  # WHY: guard: line may omit proto keyword
            entry["protocol"] = proto_match.group(1)  # WHY: capture group 1 is the protocol
        return entry  # WHY: caller filters None separately

    def _parse_protocol_route_line(self, line: str) -> dict[str, Any] | None:
        """Parse a route line with BGP/OSPF/static protocol indicators."""
        entry = _empty_route_entry()  # WHY: shared factory keeps route-entry shape uniform
        entry, line = self._extract_route_flags(entry, line)  # WHY: consume leading >/* markers
        parts = line.split()  # WHY: whitespace-split into tokens for classification
        if not parts:  # WHY: guard: empty line after flag consumption
            return None  # WHY: signal "no data" so caller skips this line
        for part in parts:  # WHY: classify each token independently
            self._classify_route_part(entry, part)  # WHY: shared token classifier
        return entry if entry["destination"] else None  # WHY: destination required for valid row

    @staticmethod
    def _extract_route_flags(entry: dict[str, Any], line: str) -> tuple[dict[str, Any], str]:
        """Extract active/selected flags from line prefix."""
        if line.startswith(">") or line.startswith("*"):  # WHY: only these two chars mark flags
            entry["active"] = ">" in line[:3]  # WHY: 3-char window preserves legacy semantics
            entry["selected"] = "*" in line[:3]  # WHY: 3-char window preserves legacy semantics
            line = line.lstrip(">* ")  # WHY: strip flag markers before returning cleaned line
        return entry, line  # WHY: caller uses updated entry + reduced line

    def _normalize_json_route_entry(self, item: dict[str, Any]) -> dict[str, Any]:
        """Normalize a JSON dict into standard route entry format."""
        return {  # WHY: dict literal keeps field projection concise and readable
            "destination": item.get("prefix", item.get("destination", item.get("route", ""))),  # WHY: 3 aliases
            "next_hop": item.get("nextHop", item.get("next_hop", item.get("gateway", ""))),  # WHY: 3 aliases
            "interface": item.get("interface", item.get("dev", item.get("iface", ""))),  # WHY: 3 aliases
            "protocol": item.get("protocol", item.get("proto", item.get("type", ""))),  # WHY: 3 aliases
            "admin_distance": str(item.get("adminDistance", item.get("admin_distance", ""))),  # WHY: str
            "metric": str(item.get("metric", "")),  # WHY: coerce int→str for uniform display
            "active": item.get("active", False),  # WHY: pass-through boolean flag
            "selected": item.get("selected", False),  # WHY: pass-through boolean flag
        }

    def _parse_juniper_routing(self, raw_output: str) -> list[dict[str, Any]]:
        """Parse Juniper inet.0/inet6.0 multi-line routing format."""
        routes: list[dict[str, Any]] = []  # WHY: accumulator for finalized route entries
        current_route: dict[str, Any] = {}  # WHY: in-flight route being built line-by-line
        current_table = ""  # WHY: current routing-table context (inet.0/inet6.0/...)
        for line in raw_output.strip().split("\n"):  # WHY: iterate every input line
            line_stripped = line.strip()  # WHY: normalize whitespace once per line
            current_route, current_table = self._process_juniper_line(  # WHY: helper owns state txn
                line_stripped,
                routes,
                current_route,
                current_table,
            )
        if current_route:  # WHY: flush final in-flight route after loop terminates
            routes.append(current_route)  # WHY: last route otherwise leaks
        return routes  # WHY: caller renders empty list when no routes classified
