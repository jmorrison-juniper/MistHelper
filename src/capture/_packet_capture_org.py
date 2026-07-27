"""Org / MxEdge capture cluster extracted from packet_capture.py.

Owns the ~420-LOC MxEdge selection, port picking, payload assembly,
summary printing and org-level capture execution for
``PacketCaptureManager``. Follows the same wrapper-class +
``__getattr__`` template as :mod:`src.maps._maps_clone` so the parent
manager stays a thin coordinator: it holds an instance of
:class:`PacketCaptureOrg` as ``self._org`` and exposes slim two-statement
delegator wrappers for the public method names still called by
``OrgCaptureWorkflow``, ``site_capture_loop`` and existing unit tests.
"""

from __future__ import annotations  # WHY: postponed evaluation consistent with parent module

import logging  # WHY: capture-lifecycle audit trail
from typing import Any, cast  # WHY: opaque manager plus typed cast for lazy proxy returns


def _pc() -> Any:  # WHY: lazy accessor exposing packet_capture module for name lookup
    """Return the ``packet_capture`` module for test-patchable name lookup.

    Helpers route ``mistapi`` and ``_get_*``/``_lazy_*`` accessor calls through
    this module so unit tests can patch ``src.capture.packet_capture.<name>``
    once and intercept all helper call sites without per-file patches.
    """
    from src.capture import packet_capture as _pc_mod  # pylint: disable=import-outside-toplevel

    return _pc_mod  # WHY: attribute lookup at call time picks up test patches


def _lazy_input_utils() -> Any:  # WHY: routes InputUtils lookup through packet_capture for test patch parity
    """Return InputUtils via packet_capture so tests can patch ``_get_input_utils``."""
    return _pc()._get_input_utils()  # WHY: single indirection = single test patch point


def _lazy_data_exporter() -> Any:  # WHY: routes DataExporter lookup through packet_capture for test patch parity
    """Return DataExporter via packet_capture so tests can patch ``_get_data_exporter``."""
    return _pc()._get_data_exporter()  # WHY: single indirection = single test patch point


_API_LIMIT_NOTICE = (  # WHY: legacy notice hoisted to constant to keep call-site under line-length budget
    "  ! API Limitation: Only 1 MxEdge can be captured at a time for organization-level captures"
)


class PacketCaptureOrg:  # WHY: wraps org/MxEdge capture helpers extracted from PacketCaptureManager
    """Wrapper class holding the extracted org/MxEdge capture helpers."""

    def __init__(self, manager: Any) -> None:  # WHY: bind parent manager so __getattr__ can proxy state
        """Store the parent manager for delegate lookups."""
        self._mm = manager  # WHY: enable __getattr__ delegation back to PacketCaptureManager

    def __getattr__(self, name: str) -> Any:  # WHY: transparent proxy so callers see combined API
        """Delegate unknown attributes to the wrapped manager."""
        mm = self.__dict__.get("_mm")  # WHY: guard against half-initialized instances
        if mm is None:  # WHY: only trips during broken init. Avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly to callers
        return getattr(mm, name)  # WHY: transparent proxy to the parent manager

    # ------------------------------------------------------------------
    # MxEdge discovery
    # ------------------------------------------------------------------

    def fetch_org_mxedges(self) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:  # WHY: two-step fetch entry
        """Fetch MxEdges and their stats for org-level captures.

        Returns:
            Tuple of ``(mxedge_list, stats_map)`` or ``None`` on failure.
        """
        print("\n  Fetching available MxEdges...")  # WHY: user progress cue before long API call
        mxedges = self._fetch_mxedge_list()  # WHY: primary list-call isolated for clarity
        if mxedges is None:  # WHY: explicit None means fetch failure, propagate cancel
            return None  # WHY: preserve legacy None-on-error contract
        stats_map = self._fetch_mxedge_stats_map()  # WHY: secondary stats call, best-effort
        return mxedges, stats_map  # WHY: return the two-tuple expected by the workflow

    def _fetch_mxedge_list(self) -> list[dict[str, Any]] | None:  # WHY: primary listOrgMxEdges + error path
        """Fetch the MxEdge inventory or return None on empty/error."""
        try:  # WHY: swallow SDK errors and surface as None sentinel
            response = _pc().mistapi.api.v1.orgs.mxedges.listOrgMxEdges(  # WHY: primary MxEdge listing endpoint
                self.mist_session, self.org_id, limit=1000
            )
            mxedges = _pc().mistapi.get_all(
                response=response, mist_session=self.mist_session
            )  # WHY: paginate through everything
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"\n! Error fetching MxEdges: {error}")  # WHY: surface failure detail to user
            logging.error("Menu #10: Failed to fetch MxEdges: %s", error)  # WHY: keep legacy log line
            return None  # WHY: signal fetch failure to caller
        if not mxedges:  # WHY: empty inventory is treated as a soft failure by callers
            print("\n! No MxEdges found for this organization")  # WHY: preserve legacy user message
            logging.warning("Menu #10: No MxEdges found")  # WHY: keep legacy audit trail
            return None  # WHY: signal empty inventory as None
        return cast(list[dict[str, Any]], mxedges)  # WHY: mistapi returns list[dict] via untyped SDK

    def _fetch_mxedge_stats_map(self) -> dict[str, Any]:  # WHY: best-effort stats fetch keyed by mxedge id
        """Return an ``{id: stats}`` map, best-effort (empty on error)."""
        print("  Fetching MxEdge status information...")  # WHY: cue user before secondary call
        stats_map: dict[str, Any] = {}  # WHY: default-empty so failure still yields a usable value
        try:  # WHY: stats are advisory. Failures must not block capture
            stats_response = _pc().mistapi.api.v1.orgs.stats.listOrgMxEdgesStats(  # WHY: org-scope stats endpoint
                self.mist_session, self.org_id, limit=1000
            )
            stats_data = _pc().mistapi.get_all(response=stats_response, mist_session=self.mist_session)  # WHY: paginate
            for stat in stats_data or []:  # WHY: guard against None response payload
                mxedge_id = stat.get("id")  # WHY: id keys the map, skip records lacking it
                if mxedge_id:  # WHY: id is required for the map key. Skip records lacking it
                    stats_map[mxedge_id] = stat  # WHY: populate map keyed by mxedge id
        except Exception as error:  # pylint: disable=broad-exception-caught
            logging.warning("Menu #10: Failed to fetch MxEdge stats: %s", error)  # WHY: legacy log line
        return stats_map  # WHY: caller merges this into row display

    # ------------------------------------------------------------------
    # MxEdge selection
    # ------------------------------------------------------------------

    def display_and_select_mxedge(  # WHY: interactive picker returning the chosen mxedge or None on cancel
        self,
        mxedges: list[dict[str, Any]],
        stats_map: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Display MxEdge list and prompt user to select one."""
        print(f"\n  Available MxEdges ({len(mxedges)} found):")  # WHY: header for the list
        print("=" * 120)  # WHY: visual separator matching legacy width
        index_to_mxedge = self._render_mxedge_rows(mxedges, stats_map)  # WHY: build index map
        print()  # WHY: blank line before the API-limitation notice
        print(_API_LIMIT_NOTICE)  # WHY: legacy notice - org captures restricted to 1 MxEdge per session
        idx = self._prompt_mxedge_index(len(mxedges))  # WHY: prompt for numeric index
        if idx is None or idx not in index_to_mxedge:  # WHY: cancel or invalid index
            return None  # WHY: caller treats None as user-cancel
        selected = index_to_mxedge[idx]  # WHY: resolve chosen index to the mxedge dict
        print("\n  Selected MxEdge:")  # WHY: confirm selection to user
        print(f"    -> {selected.get('name', 'Unnamed')} (ID: {selected.get('id')})")  # WHY: show name+id
        return selected  # WHY: hand chosen mxedge back to workflow

    def _render_mxedge_rows(  # WHY: prints one row per mxedge and returns index->mxedge map
        self,
        mxedges: list[dict[str, Any]],
        stats_map: dict[str, Any],
    ) -> dict[int, dict[str, Any]]:
        """Print one row per MxEdge and return the index-to-mxedge map."""
        index_to_mxedge: dict[int, dict[str, Any]] = {}  # WHY: preserve display order for selection
        for index, mxedge in enumerate(mxedges):  # WHY: index drives the user-facing selector
            self.print_mxedge_row(index, mxedge, stats_map)  # WHY: extracted single-row printer
            index_to_mxedge[index] = mxedge  # WHY: bookkeeping for the later idx lookup
        return index_to_mxedge  # WHY: hand map to the outer prompt loop

    def _prompt_mxedge_index(self, count: int) -> int | None:  # WHY: safe numeric-index prompt with bounds check
        """Prompt for a numeric MxEdge index. Return None on cancel/invalid input."""
        try:  # WHY: safe_input can raise on EOF/Ctrl-C
            selection_input = (  # WHY: prompt and strip whitespace inline for parse below
                _lazy_input_utils()
                .safe_input(f"Select MxEdge index [0-{count - 1}]: ", context="mxedge_selection")
                .strip()
            )
        except (EOFError, KeyboardInterrupt):  # WHY: legacy cancel path prints and returns None
            print("\n! Operation cancelled")  # WHY: legacy user message on cancel
            logging.info("Menu #10: User cancelled MxEdge selection")  # WHY: legacy audit log
            return None  # WHY: signal cancel to caller
        try:  # WHY: int() may raise on non-numeric input
            idx = int(selection_input)  # WHY: parse index. ValueError caught below
        except ValueError:  # WHY: non-numeric input path warns and returns None
            print("\n! Invalid input format. Please enter a single numeric index.")  # WHY: legacy user error
            logging.warning("Menu #10: Invalid selection input: %s", selection_input)  # WHY: legacy log line
            return None  # WHY: signal invalid input to caller
        if not 0 <= idx < count:  # WHY: bounds check with legacy warning line
            print(f"\n! Invalid index {idx}. Please select from 0-{count - 1}")  # nosec B608 # WHY: user error
            logging.warning("Menu #10: Invalid MxEdge index: %s", idx)  # WHY: legacy audit log
            return None  # WHY: signal out-of-range index to caller
        return idx  # WHY: valid index returned to caller

    # ------------------------------------------------------------------
    # MxEdge row rendering
    # ------------------------------------------------------------------

    def print_mxedge_row(self, index: int, mxedge: dict[str, Any], stats_map: dict[str, Any]) -> None:  # WHY: row
        """Print a single MxEdge row with status details."""
        mxedge_name = mxedge.get("name", "Unnamed MxEdge")  # WHY: fall back to placeholder name
        mxedge_id = mxedge.get("id", "No ID")  # WHY: legacy placeholder for missing id
        model = mxedge.get("model", "Unknown")  # WHY: unknown-model fallback matches legacy
        stat = stats_map.get(mxedge_id, {})  # WHY: default empty dict keeps .get chains simple
        status_marker, uptime_str = self._format_mxedge_status(stat)  # WHY: split status/uptime rendering
        mxagent_state, tunterm_state = self._extract_service_states(stat)  # WHY: split service parsing
        print(  # WHY: primary row printed as one formatted line matching legacy width
            f"  [{index}] {mxedge_name:30} | Model: {model:10}"
            f" | Status: {status_marker:8} | Uptime: {uptime_str:10}"
        )
        print(f"       mxagent: {mxagent_state:15} | tunterm: {tunterm_state:15}")  # WHY: legacy secondary row

    @staticmethod
    def _format_mxedge_status(stat: dict[str, Any]) -> tuple[str, str]:  # WHY: legacy status/uptime formatter
        """Return (status_marker, uptime_str) for a stats record."""
        status = stat.get("status", "unknown")  # WHY: default "unknown" preserves legacy display
        uptime = stat.get("uptime", 0)  # WHY: 0 uptime maps to N/A per legacy
        if uptime > 0:  # WHY: only format non-zero uptimes into "Xd Yh"
            uptime_str = f"{uptime // 86400}d {(uptime % 86400) // 3600}h"  # WHY: legacy day/hour format
        else:
            uptime_str = "N/A"  # WHY: legacy placeholder for missing uptime
        if status == "connected":  # WHY: legacy label mapping for status
            status_marker = "ONLINE"  # WHY: legacy display for connected state
        elif status == "disconnected":  # WHY: legacy branch for disconnected state
            status_marker = "OFFLINE"  # WHY: legacy display for disconnected state
        else:
            status_marker = status.upper()  # WHY: fallback matches legacy behavior
        return status_marker, uptime_str  # WHY: caller renders both in one print

    @staticmethod
    def _extract_service_states(stat: dict[str, Any]) -> tuple[str, str]:  # WHY: legacy service-state extractor
        """Return (mxagent_state, tunterm_state) strings from a stats record."""
        service_stat = stat.get("service_stat", {})  # WHY: nested dict may be absent
        mxagent_state = service_stat.get("mxagent", {}).get("running_state", "Unknown")  # WHY: legacy default
        tunterm_state = service_stat.get("tunterm", {}).get("running_state", "Unknown")  # WHY: legacy default
        return mxagent_state, tunterm_state  # WHY: caller renders both in one print

    # ------------------------------------------------------------------
    # Port listing / selection
    # ------------------------------------------------------------------

    def display_mxedge_ports(self, mxedge_name: str, port_stat: dict[str, Any]) -> list[str]:  # WHY: port list UI
        """Display MxEdge interface stats and return port name list."""
        port_list: list[str] = []  # WHY: preserve iteration order for later index lookup
        print(f"\n  {mxedge_name} - Available Interfaces:")  # WHY: legacy header
        print(f"  {'-' * 70}")  # WHY: legacy visual separator
        for port_index, (port_name, port_info) in enumerate(sorted(port_stat.items())):  # WHY: sort for stable index
            status = "UP" if port_info.get("up", False) else "DOWN"  # WHY: legacy up/down flag mapping
            speed = port_info.get("speed", 0)  # WHY: 0 speed maps to N/A per legacy
            speed_str = f"{speed}Mbps" if speed else "N/A"  # WHY: format only when non-zero
            mac = port_info.get("mac", "N/A")  # WHY: legacy placeholder for missing MAC
            print(f"    [{port_index}] {port_name:10} Status: {status:5} Speed: {speed_str:10} MAC: {mac}")  # WHY: row
            port_list.append(port_name)  # WHY: order-preserving list for later index resolution
        return port_list  # WHY: caller passes this to the index prompt

    def select_port_by_index(  # WHY: legacy interactive single-port selector
        self,
        port_list: list[str],
        mxedge_name: str,
        mxedge_id: str,
    ) -> list[str] | None:
        """Prompt user to select a port by index."""
        print("\n  Port Selection:")  # WHY: legacy header
        print("  ! API Limitation: Only 1 port can be captured at a time")  # WHY: legacy notice
        port_input = self._prompt_port_input(port_list, mxedge_name, mxedge_id)  # WHY: extracted safe-prompt
        if port_input is None:  # WHY: cancel path from prompt
            return None  # WHY: propagate cancel to caller
        if not port_input:  # WHY: legacy path when user submits empty response
            print("\n! Port selection is required. Please select a port index.")  # WHY: legacy user error line
            logging.warning("Menu #10: No port selected")  # WHY: legacy audit log
            return None  # WHY: signal empty selection to caller
        return self._resolve_port_index(port_list, port_input)  # WHY: parse and validate index

    @staticmethod
    def _prompt_port_input(port_list: list[str], mxedge_name: str, mxedge_id: str) -> str | None:  # WHY: safe prompt
        """Safely prompt for a port index string. None on cancel."""
        try:  # WHY: safe_input can raise on EOF/Ctrl-C
            return cast(  # WHY: safe_input->str traverses untyped lazy proxy
                str,
                _lazy_input_utils()
                .safe_input(
                    f"\n  {mxedge_name} - Select a single port index [0-{len(port_list) - 1}]: ",
                    context=f"port_selection_{mxedge_id}",
                )
                .strip(),
            )
        except (EOFError, KeyboardInterrupt):  # WHY: legacy cancel path
            print("\n! Operation cancelled")  # WHY: legacy user message on cancel
            logging.info("Menu #10: User cancelled port selection")  # WHY: legacy audit log
            return None  # WHY: signal cancel to caller

    @staticmethod
    def _resolve_port_index(port_list: list[str], port_input: str) -> list[str] | None:  # WHY: legacy index parser
        """Parse a numeric index and return the selected single-port list."""
        try:  # WHY: int() may raise on non-numeric input
            idx = int(port_input)  # WHY: parse port index. ValueError caught below
        except ValueError:  # WHY: non-numeric input path warns and returns None
            print("\n! Invalid input format. Please enter a single numeric index.")  # WHY: legacy user error
            logging.warning("Menu #10: Invalid port input: %s", port_input)  # WHY: legacy audit log
            return None  # WHY: signal parse failure to caller
        if not 0 <= idx < len(port_list):  # WHY: legacy bounds check with warning
            print(f"\n! Invalid index {idx} (valid range: 0-{len(port_list) - 1})")  # WHY: legacy user error line
            logging.warning("Menu #10: Invalid port index: %s", idx)  # WHY: legacy audit log
            return None  # WHY: signal out-of-range index to caller
        selected_port = port_list[idx]  # WHY: resolve chosen index to the port name
        print(f"    -> Selected port: {selected_port}")  # WHY: confirm to user
        return [selected_port]  # WHY: API expects list-of-one for single-port capture

    def fetch_and_select_mxedge_port(self, mxedge: dict[str, Any]) -> list[str] | None:  # WHY: legacy port picker
        """Fetch MxEdge interfaces and prompt port selection."""
        mxedge_id: str = mxedge.get("id", "")  # WHY: default empty preserves legacy None-safety
        mxedge_name: str = mxedge.get("name", "Unnamed MxEdge")  # WHY: display fallback
        stats_data = self._fetch_single_mxedge_stats(mxedge_id, mxedge_name)  # WHY: extracted API call
        if stats_data is None:  # WHY: fetch failure already reported to user
            return None  # WHY: propagate fetch failure to caller
        port_stat = stats_data.get("port_stat", {})  # WHY: nested field may be absent
        if not port_stat:  # WHY: legacy path when device exposes no port stats
            print(f"\n  {mxedge_name} - No interface stats available")  # WHY: legacy user message
            return None  # WHY: no ports means nothing to capture
        port_list = self.display_mxedge_ports(mxedge_name, port_stat)  # WHY: prints + returns port names
        if not port_list:  # WHY: empty port list is a soft failure
            print(f"\n  {mxedge_name}: No ports available")  # WHY: legacy user message
            return None  # WHY: empty port list means nothing to capture
        return self.select_port_by_index(port_list, mxedge_name, mxedge_id)  # WHY: interactive picker

    def _fetch_single_mxedge_stats(self, mxedge_id: str, mxedge_name: str) -> dict[str, Any] | None:
        """Fetch stats for a single MxEdge. Return dict or None on failure."""
        try:  # WHY: SDK may raise on transport errors
            stats_response = _pc().mistapi.api.v1.orgs.stats.getOrgMxEdgeStats(  # WHY: per-mxedge stats endpoint
                self.mist_session, self.org_id, mxedge_id
            )
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"\n  {mxedge_name} - Error fetching stats: {error}")  # WHY: legacy user message
            logging.error("Menu #10: Failed to fetch stats for %s: %s", mxedge_name, error)
            return None
        if stats_response.status_code != 200:  # WHY: non-200 is a soft failure
            print(f"\n  {mxedge_name} - Failed to fetch stats (HTTP {stats_response.status_code})")
            return None
        return stats_response.data if hasattr(stats_response, "data") else {}  # WHY: match legacy fallback

    # ------------------------------------------------------------------
    # Capture parameter prompts
    # ------------------------------------------------------------------

    def prompt_org_format_selection(self) -> tuple[str, str | None, int | None] | None:
        """Prompt for org capture format (stream or TZSP)."""
        print("\nCapture format:")  # WHY: legacy header
        print("  1. Stream to Mist Cloud (default)")  # WHY: menu option 1
        print("  2. TZSP stream to remote host (Wireshark)")  # WHY: menu option 2
        format_choice = _lazy_input_utils().safe_input(
            "Enter choice (default 1): ", default_value="1", context="format"
        )
        if format_choice != "2":  # WHY: any non-"2" choice keeps stream default
            return ("stream", None, None)  # WHY: canonical stream tuple
        return self._prompt_tzsp_target()  # WHY: split TZSP flow for length/complexity budget

    @staticmethod
    def _prompt_tzsp_target() -> tuple[str, str | None, int | None] | None:
        """Prompt for TZSP host + port. Return the tzsp tuple or None on invalid."""
        tzsp_host = _lazy_input_utils().safe_input("Enter TZSP host (IP address or hostname): ", context="tzsp_host")
        if not tzsp_host:  # WHY: TZSP requires a target host
            print("\n! TZSP host required")
            return None
        tzsp_port_str = _lazy_input_utils().safe_input(
            "Enter TZSP port (default 37008): ", default_value="37008", context="tzsp_port"
        )
        try:  # WHY: int() may raise for non-numeric port
            tzsp_port = int(tzsp_port_str)
        except ValueError:
            print(f"\n! Invalid port: {tzsp_port_str}")
            return None
        if not 1 <= tzsp_port <= 65535:  # WHY: valid TCP/UDP port range
            print("\n! Port must be between 1 and 65535")
            return None
        return ("tzsp", tzsp_host, tzsp_port)  # WHY: canonical TZSP tuple

    def gather_org_capture_params(
        self,
    ) -> tuple[int, int, int, str, str | None, int | None] | None:
        """Gather org capture parameters interactively."""
        duration = self._prompt_capture_duration(default=30, min_val=30)  # WHY: delegate to prompts cluster
        if duration is None:  # WHY: user cancelled the duration prompt
            return None
        num_packets = self._prompt_num_packets()  # WHY: delegate to prompts cluster
        if num_packets is None:  # WHY: user cancelled the packet-count prompt
            return None
        max_pkt_len = self._prompt_max_packet_length()  # WHY: delegate to prompts cluster
        if max_pkt_len is None:  # WHY: user cancelled the packet-length prompt
            return None
        format_result = self._prompt_org_format_selection()  # WHY: extracted format prompt
        if format_result is None:  # WHY: user cancelled or supplied invalid format
            return None
        capture_format, tzsp_host, tzsp_port = format_result  # WHY: unpack for return tuple
        return (duration, num_packets, max_pkt_len, capture_format, tzsp_host, tzsp_port)

    # ------------------------------------------------------------------
    # Confirmation + payload assembly
    # ------------------------------------------------------------------

    def confirm_and_execute_org_capture(self, payload: dict[str, Any]) -> None:
        """Prompt for confirmation and execute org capture payload."""
        _lazy_input_utils().safe_input(  # WHY: block until user acknowledges the summary
            "\nPress Enter to start capture (Ctrl+C to cancel): ",
            context="confirmation",
            allow_empty=True,
        )
        mm = self._mm  # WHY: route back through manager so tests can patch _execute_org_capture
        mm._execute_org_capture(payload)  # WHY: mock-friendly indirection preserved for legacy tests

    @staticmethod
    def log_loop_stop(iteration: int) -> None:
        """Log loop-stop summary after keyboard interrupt in loop mode."""
        logging.info("Capture loop stopped by user after %s iterations", iteration)  # WHY: legacy log line

    def build_org_payload(
        self,
        mxedge: dict[str, Any],
        ports: list[str],
        tcpdump_expr: str,
        capture_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the API payload for org-level MxEdge capture."""
        mxedge_id: str = mxedge.get("id", "")  # WHY: default empty preserves legacy behavior
        capture_format = capture_config["format"]  # WHY: required key. Missing = programmer error
        payload: dict[str, Any] = self._base_org_payload(
            mxedge_id, capture_format, capture_config
        )  # WHY: split for length
        if tcpdump_expr:  # WHY: only include filter when user supplied one
            payload["tcpdump_expression"] = tcpdump_expr
        if ports:  # WHY: interfaces block requires at least one port
            payload["mxedges"][mxedge_id]["interfaces"] = {port: {} for port in ports}
        if capture_format == "tzsp":  # WHY: TZSP-only fields promoted to top level
            payload["tzsp_host"] = capture_config.get("tzsp_host")
            payload["tzsp_port"] = capture_config.get("tzsp_port")
        return payload  # WHY: fully assembled body for startOrgPacketCapture

    @staticmethod
    def _base_org_payload(mxedge_id: str, capture_format: str, capture_config: dict[str, Any]) -> dict[str, Any]:
        """Return the base payload dict shared by all org captures."""
        return {  # WHY: fixed field ordering matches legacy JSON output
            "type": "mxedge",
            "duration": capture_config["duration"],
            "num_packets": capture_config["num_packets"],
            "max_pkt_len": capture_config["max_pkt_len"],
            "format": capture_format,
            "mxedges": {mxedge_id: {}},
        }

    # ------------------------------------------------------------------
    # Summary + execution
    # ------------------------------------------------------------------

    def display_org_capture_summary(
        self,
        payload: dict[str, Any],
        mxedge: dict[str, Any],
        ports: list[str],
        tcpdump_expr: str,
    ) -> None:
        """Display org capture configuration summary."""
        self._print_org_summary_header(mxedge, ports, tcpdump_expr)  # WHY: split for length budget
        duration = payload.get("duration", 0)  # WHY: default 0 preserves legacy output
        num_packets = payload.get("num_packets", 0)  # WHY: default 0 preserves legacy output
        print(f"  Duration: {duration} seconds")
        print(f"  Packets: {num_packets} ({'unlimited' if num_packets == 0 else 'max'})")
        print(f"  Max Packet Length: {payload.get('max_pkt_len', 0)} bytes")
        capture_format = payload.get("format", "stream")  # WHY: default stream matches legacy
        print(f"  Format: {capture_format}")
        if capture_format == "tzsp":  # WHY: only TZSP mode shows host/port line
            print(f"  TZSP Host: {payload.get('tzsp_host')}:{payload.get('tzsp_port')}")
        print("=" * 80)  # WHY: legacy trailing separator

    @staticmethod
    def _print_org_summary_header(mxedge: dict[str, Any], ports: list[str], tcpdump_expr: str) -> None:
        """Print the top-of-summary block (banner, mxedge, filter)."""
        print("\n" + "=" * 80)  # WHY: legacy leading separator
        print(" CAPTURE CONFIGURATION SUMMARY")  # WHY: banner text matches legacy
        print("=" * 80)
        print("  Capture Type: MxEdge (Organization Level)")
        print(f"  MxEdge: {mxedge.get('name', 'Unnamed')} (ID: {mxedge.get('id')})")
        print(f"  Port: {ports[0] if ports else 'None'}")  # WHY: only one port supported per capture
        if tcpdump_expr:  # WHY: choose filter line based on presence of expression
            print(f"  Packet Filter: {tcpdump_expr}")
        else:
            print("  Packet Filter: None (all traffic)")

    def execute_org_capture(self, payload: dict[str, Any]) -> None:
        """Execute org-level packet capture via API."""
        try:  # WHY: broad guard preserves legacy user-friendly error handling
            print("\n> Starting organization packet capture...")  # WHY: legacy progress line
            logging.info("Initiating org capture with payload: %s", payload)  # WHY: audit log
            response = _pc().mistapi.api.v1.orgs.pcaps.startOrgPacketCapture(  # WHY: primary start endpoint
                self.mist_session, self.org_id, payload
            )
            if response.status_code == 200:  # WHY: success branch continues into result handling
                self._handle_org_capture_started(response.data)
            else:
                self._log_org_capture_failure(response)  # WHY: uniform failure logging
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"\n! Error starting capture: {error}")  # WHY: legacy user message
            logging.exception("Exception in _execute_org_capture: %s", error)  # WHY: full traceback in log

    def _handle_org_capture_started(self, result: dict[str, Any]) -> None:
        """Print status, dispatch on format, and export capture info."""
        capture_id = result.get("id", "unknown")  # WHY: fallback preserves legacy display
        print("\n* Capture started successfully!")  # WHY: legacy success banner
        print(f"  Capture ID: {capture_id}")  # WHY: expose id for later manual tracking
        print(f"  Format: {result.get('format', 'unknown')}")  # WHY: echo negotiated format
        print(f"  Duration: {result.get('duration', 0)} seconds")  # WHY: echo negotiated duration
        print(f"  Expires: {result.get('expiry', 'unknown')}")  # WHY: echo capture TTL
        logging.info("Org capture started: capture_id=%s", capture_id)  # WHY: legacy log line
        capture_format = result.get("format", "pcap")  # WHY: default pcap matches API behavior
        self._dispatch_org_capture_format(capture_format, capture_id, result)  # WHY: pcap vs stream branch
        self._export_capture_info_to_csv(result, "org", self.org_id)  # WHY: legacy CSV export step

    def _dispatch_org_capture_format(
        self,
        capture_format: str,
        capture_id: str,
        result: dict[str, Any],
    ) -> None:
        """Route to pcap-download or stream-subscribe based on format."""
        if capture_format == "pcap":  # WHY: pcap flow polls + downloads a file
            duration = result.get("duration", 60)  # WHY: fall back to legacy default
            self._wait_and_download_pcap_org(self.org_id, capture_id, duration)  # WHY: exec cluster owns download
        elif capture_format == "stream":  # WHY: stream flow attaches a websocket subscriber
            self._subscribe_to_org_capture_stream(capture_id)  # WHY: exec cluster owns channel string

    @staticmethod
    def _log_org_capture_failure(response: Any) -> None:
        """Log and print a failed startOrgPacketCapture response."""
        print(f"\n! Failed to start capture: {response.status_code}")  # WHY: legacy user message
        error_details = response.data if hasattr(response, "data") else "No error details available"  # WHY: fallback
        print(f"  Error details: {error_details}")  # WHY: surface API error body
        logging.error("Capture failed: %s - %s", response.status_code, error_details)  # WHY: legacy log

    def export_capture_info_to_csv(
        self,
        capture_data: dict[str, Any],
        scope: str,
        scope_id: str,
    ) -> None:
        """Export capture session information to CSV (org-scope helper)."""
        try:  # WHY: swallow exporter errors so capture path continues
            filename = f"PacketCapture_{scope}_{capture_data.get('id', 'unknown')}.csv"
            export_data = {"scope": scope, "scope_id": scope_id, **capture_data}  # WHY: enrich with scope
            api_name = "startSitePacketCapture" if scope == "site" else "startOrgPacketCapture"  # WHY: legacy tag
            _lazy_data_exporter().write_with_format_selection([export_data], filename, api_function_name=api_name)
            print(f"\n* Capture info exported to: {filename}")  # WHY: legacy confirmation
            logging.info("Capture info exported to %s", filename)  # WHY: audit log line
        except Exception as error:  # pylint: disable=broad-exception-caught
            logging.exception("Failed to export capture info: %s", error)  # WHY: legacy traceback log
