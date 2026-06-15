"""Adapter for routing device commands through ``mistapi.device_utils``.

This module provides :class:`DeviceUtilsAdapter`, a thin dispatch layer
that prefers the high-level ``mistapi.device_utils`` helpers (which
manage the underlying WebSocket session for us) and transparently falls
back to a caller-supplied raw API implementation when device_utils is
unavailable, when the command/device combo is not covered, or when an
error occurs while invoking the helper.

See ``specs/device-utils-adoption/`` for the full design.
"""


from __future__ import annotations  # Defer type evaluation for forward refs across versions

import logging  # Project-standard logging facility
from collections.abc import Callable  # Type hint for fallback / dispatch callables
from typing import Any  # Generic typing for mistapi.APISession and util responses

# -----------------------------------------------------------------------------
# device_utils availability detection
# -----------------------------------------------------------------------------
# Attempting the import at module load lets the rest of MistHelper boot
# even on older mistapi releases (<0.61) that pre-date device_utils.
# The module-level boolean is the single source of truth referenced by
# both the adapter and the unit tests.
try:  # Probe for the optional device_utils namespace
    from mistapi import device_utils as _device_utils

    DEVICE_UTILS_AVAILABLE: bool = True  # Helper present, full dispatch enabled
except ImportError:  # Older mistapi or installation without device_utils
    _device_utils = None  # Sentinel so dispatch knows to fall back
    DEVICE_UTILS_AVAILABLE = False  # Disables every dispatch entry; fallback path always used

# Public re-export of the logger so tests can monkeypatch or capture
LOGGER = logging.getLogger(__name__)  # Module-scoped logger; honors MistHelper config

# Type alias: fallback callable signature matches DeviceUtilsAdapter.execute
FallbackFn = Callable[..., list[dict[str, Any]]]  # (command, device_type, site_id, device_id, **params) -> rows


class DeviceUtilsAdapter:
    """Dispatch device commands to ``mistapi.device_utils`` with raw-API fallback.

    The adapter is intentionally side-effect free at import time so it
    can be unit-tested without a live Mist session.  All decisions about
    which path to take happen inside :meth:`execute`.
    """

    def __init__(
        self,
        mist_session: Any,
        fallback_fn: FallbackFn | None = None,
    ) -> None:
        """Wire up the adapter.

        Args:
            mist_session: Authenticated ``mistapi.APISession`` instance,
                forwarded to every device_utils helper.
            fallback_fn: Callable invoked when device_utils cannot
                service a request.  Must accept the same positional
                arguments as :meth:`execute` and return the same
                ``list[dict]`` shape.  When ``None``, fallback raises
                ``NotImplementedError`` so misconfiguration is loud.
        """
        LOGGER.info("Initializing DeviceUtilsAdapter (device_utils available=%s)", DEVICE_UTILS_AVAILABLE)
        self._mist_session = mist_session  # Stored for forwarding to helper calls
        self._utils_available = DEVICE_UTILS_AVAILABLE  # Per-instance copy keeps tests independent
        self._fallback_fn = fallback_fn  # Optional caller-supplied raw API path
        self._command_map = self._build_command_map()  # Dispatch table built once at construction
        LOGGER.debug("DeviceUtilsAdapter ready with %d dispatch entries", len(self._command_map))

    # ------------------------------------------------------------------
    # Dispatch table
    # ------------------------------------------------------------------
    def _build_command_map(self) -> dict[tuple[str, str], Callable[..., Any]]:
        """Build ``(device_type, command) -> device_utils callable`` table.

        Returns an empty dict when device_utils is not importable so the
        adapter degrades to always-fallback mode without raising.  Each
        namespace lookup is defensive (``getattr`` with a None default)
        so test stubs or pruned SDK builds do not crash construction.
        """
        LOGGER.debug("Building device_utils command dispatch map")
        if not self._utils_available or _device_utils is None:  # Guard the attribute lookups below
            LOGGER.info("device_utils unavailable; dispatch map will be empty (fallback only)")
            return {}  # Empty map causes execute() to always call fallback
        ex = getattr(_device_utils, "ex", None)  # EX switch helpers namespace (may be missing in stubs)
        ssr = getattr(_device_utils, "ssr", None)  # SSR gateway helpers namespace
        srx = getattr(_device_utils, "srx", None)  # SRX gateway helpers namespace
        ap = getattr(_device_utils, "ap", None)  # AP helpers namespace
        command_map: dict[tuple[str, str], Callable[..., Any]] = {}  # Final dispatch table
        self._register_ex_commands(command_map, ex)  # Phase 1: EX show + diagnostics + mgmt
        self._register_gateway_commands(command_map, ssr, srx)  # Phase 1-2: SSR + SRX show/diag
        self._register_ap_commands(command_map, ap)  # Phase 2: AP diagnostics
        LOGGER.debug("Command map built: %d entries", len(command_map))
        return command_map

    @staticmethod
    def _register_ex_commands(
        command_map: dict[tuple[str, str], Callable[..., Any]],
        ex: Any,
    ) -> None:
        """Register EX switch dispatch entries (show, diag, management)."""
        if ex is None or not hasattr(ex, "__dict__"):  # Namespace missing or not a real module
            return  # Skip registration; fallback path will handle requests
        # Map (device_type, command) -> helper name on ``mistapi.device_utils.ex``
        ex_helpers: dict[tuple[str, str], str] = {
            ("switch", "show_arp"): "retrieveArpTable",  # show arp -> ARP table
            ("switch", "show_mac_table"): "retrieveMacTable",  # show ethernet-switching table
            ("switch", "show_dhcp_leases"): "retrieveDhcpLeases",  # show dhcp server binding
            ("switch", "show_bgp_summary"): "retrieveBgpSummary",  # show bgp summary
            ("switch", "ping"): "ping",  # ping host from EX
            ("switch", "traceroute"): "traceroute",  # traceroute from EX
            ("switch", "bounce_port"): "bouncePort",  # disable/enable a port (destructive)
            ("switch", "cable_test"): "cableTest",  # run TDR cable diagnostic (destructive)
            ("switch", "clear_mac_table"): "clearMacTable",  # clear ethernet-switching table (destructive)
            ("switch", "clear_learned_mac"): "clearLearnedMac",  # clear single learned MAC (destructive)
            ("switch", "clear_bpdu_error"): "clearBpduError",  # clear bpdu-error on STP port (destructive)
            ("switch", "clear_dot1x"): "clearDot1xSessions",  # clear dot1x sessions (destructive)
            ("switch", "release_dhcp"): "releaseDhcpLeases",  # release DHCP server leases (destructive)
        }
        for key, attr_name in ex_helpers.items():  # Walk the table once
            helper = getattr(ex, attr_name, None)  # Defensive lookup; missing attr -> None
            if callable(helper):  # Stubs may return non-callable sentinels; skip them
                command_map[key] = helper  # Register the real callable

    @staticmethod
    def _register_gateway_commands(
        command_map: dict[tuple[str, str], Callable[..., Any]],
        ssr: Any,
        srx: Any,
    ) -> None:
        """Register SSR + SRX gateway dispatch entries."""
        ssr_helpers: dict[tuple[str, str], str] = {
            ("gateway_ssr", "show_arp"): "retrieveArpTable",  # SSR ARP table
            ("gateway_ssr", "ping"): "ping",  # SSR ping helper
            ("gateway_ssr", "traceroute"): "traceroute",  # SSR traceroute
        }
        srx_helpers: dict[tuple[str, str], str] = {
            ("gateway_srx", "show_arp"): "retrieveArpTable",  # SRX ARP table
            ("gateway_srx", "ping"): "ping",  # SRX ping
            ("gateway_srx", "traceroute"): "traceroute",  # SRX traceroute
        }
        if ssr is not None and hasattr(ssr, "__dict__"):  # Only walk a real module
            for key, attr_name in ssr_helpers.items():  # Iterate registrations
                helper = getattr(ssr, attr_name, None)  # Defensive lookup
                if callable(helper):  # Filter out test stubs and missing attrs
                    command_map[key] = helper  # Register helper
        if srx is not None and hasattr(srx, "__dict__"):  # Same pattern for SRX
            for key, attr_name in srx_helpers.items():  # Iterate SRX table
                helper = getattr(srx, attr_name, None)  # Defensive lookup
                if callable(helper):  # Filter
                    command_map[key] = helper  # Register

    @staticmethod
    def _register_ap_commands(
        command_map: dict[tuple[str, str], Callable[..., Any]],
        ap: Any,
    ) -> None:
        """Register AP dispatch entries (ping, traceroute, ARP)."""
        if ap is None or not hasattr(ap, "__dict__"):  # Skip when namespace absent or stubbed
            return  # Fallback path will service AP commands
        ap_helpers: dict[tuple[str, str], str] = {
            ("ap", "show_arp"): "retrieveArpTable",  # AP ARP table
            ("ap", "ping"): "ping",  # AP ping helper
            ("ap", "traceroute"): "traceroute",  # AP traceroute helper
        }
        for key, attr_name in ap_helpers.items():  # Walk AP table
            helper = getattr(ap, attr_name, None)  # Defensive lookup
            if callable(helper):  # Filter stubs
                command_map[key] = helper  # Register helper

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def is_available(self, command: str, device_type: str) -> bool:
        """Return True when device_utils can service ``(device_type, command)``."""
        LOGGER.debug("Checking device_utils availability for %s/%s", device_type, command)
        if not self._utils_available:  # Short-circuit when module not importable
            return False  # Forces caller path to fallback
        present = (device_type, command) in self._command_map  # Dispatch table lookup
        LOGGER.debug("Availability for %s/%s = %s", device_type, command, present)
        return present

    def execute(
        self,
        command: str,
        device_type: str,
        site_id: str,
        device_id: str,
        **params: Any,
    ) -> list[dict[str, Any]]:
        """Run ``command`` on ``device_id``; return flattened rows.

        See ``specs/device-utils-adoption/contracts/adapter-api.md`` for
        the full behavioral contract.  In short: same output shape as
        the legacy raw-API path, transparent fallback on any failure.
        """
        LOGGER.info("Executing device command %s on %s device %s (site=%s)", command, device_type, device_id, site_id)
        if not self.is_available(command, device_type):  # Either module missing or command unmapped
            LOGGER.info("device_utils does not cover %s/%s -- using fallback", device_type, command)
            return self._fallback_raw_api(command, device_type, site_id, device_id, **params)
        helper = self._command_map[(device_type, command)]  # Resolve callable from dispatch table
        try:  # Any helper error must degrade to fallback rather than crash menu flow
            util_response = helper(self._mist_session, site_id, device_id, **params)  # Invoke helper
        except Exception as exc:  # Defensive: SDK exceptions vary
            LOGGER.warning("device_utils helper failed for %s/%s: %s -- falling back", device_type, command, exc)
            return self._fallback_raw_api(command, device_type, site_id, device_id, **params)
        rows = self._normalize_response(util_response)  # Convert UtilResponse -> list[dict]
        LOGGER.debug("device_utils helper returned %d rows for %s/%s", len(rows), device_type, command)
        return rows

    # ------------------------------------------------------------------
    # Response normalization
    # ------------------------------------------------------------------
    def _normalize_response(self, util_response: Any) -> list[dict[str, Any]]:
        """Flatten a :class:`UtilResponse` into the project-standard row shape.

        The device_utils helpers return a ``UtilResponse`` whose payload
        lives in ``ws_data`` (streamed messages) and/or
        ``trigger_api_response.data`` (immediate API result).  We block
        until completion, then normalize to a list of flat dicts that
        match the existing CSV/SQLite columns.
        """
        LOGGER.debug("Normalizing UtilResponse into row list")
        if util_response is None:  # Defensive: helper may legitimately return None
            return []  # Empty result set
        if hasattr(util_response, "wait"):  # Block until stream complete (no-op when already done)
            util_response.wait()  # Honors any timeout set on the UtilResponse
        raw_items = self._collect_payload(util_response)  # Gather messages from .ws_data / .data
        rows = [self._flatten_payload(item) for item in raw_items]  # Flatten each record for tabular export
        LOGGER.debug("Normalized %d rows from UtilResponse", len(rows))
        return rows

    @staticmethod
    def _collect_payload(util_response: Any) -> list[Any]:
        """Pull message payloads out of a UtilResponse (WS data or API data)."""
        payloads: list[Any] = []  # Accumulator for both data sources
        ws_data = getattr(util_response, "ws_data", None)  # Streamed messages, if any
        if ws_data:  # Truthy check covers None and empty list
            payloads.extend(ws_data)  # Each ws_data item is a parsed dict / string
        api_resp = getattr(util_response, "trigger_api_response", None)  # Immediate API result
        api_data = getattr(api_resp, "data", None) if api_resp is not None else None  # data attribute, when present
        if api_data is None:  # Nothing to add from the API side
            return payloads  # Return whatever ws_data gave us
        if isinstance(api_data, list):  # Mist often returns a list of records
            payloads.extend(api_data)  # Flatten one level so each record becomes a row
        else:  # Single dict or scalar payload
            payloads.append(api_data)  # Treat as one row
        return payloads

    @staticmethod
    def _flatten_payload(item: Any) -> dict[str, Any]:
        """Flatten one payload entry into a single-level dict.

        Mirrors the behavior of MistHelper's ``flatten_dict_recursively``
        without taking a hard dependency on the monolith.  Non-dict
        payloads are wrapped as ``{"value": item}`` so the row contract
        is preserved.
        """
        if not isinstance(item, dict):  # Strings / numbers come from raw WS frames
            return {"value": item}  # Single-column row keeps the writer happy
        flat: dict[str, Any] = {}  # Output accumulator
        _flatten_into(item, parent_key="", sep="_", sink=flat)  # Recurse via module helper
        return flat

    def _fallback_raw_api(
        self,
        command: str,
        device_type: str,
        site_id: str,
        device_id: str,
        **params: Any,
    ) -> list[dict[str, Any]]:
        """Delegate to the caller-provided raw API + WebSocket implementation."""
        LOGGER.info("Falling back to raw API path for %s/%s on device %s", device_type, command, device_id)
        if self._fallback_fn is None:  # No fallback wired -- treat as configuration bug
            raise NotImplementedError(
                f"device_utils cannot service {device_type}/{command} and no fallback_fn was provided"
            )
        rows = self._fallback_fn(command, device_type, site_id, device_id, **params)  # Invoke legacy path
        LOGGER.debug("Fallback returned %d rows for %s/%s", len(rows) if rows else 0, device_type, command)
        return rows or []  # Normalize None -> [] for caller convenience


# ---------------------------------------------------------------------------
# Internal helper -- flattens nested dicts/lists without importing MistHelper
# ---------------------------------------------------------------------------
def _flatten_into(
    source: dict[str, Any],
    parent_key: str,
    sep: str,
    sink: dict[str, Any],
) -> None:
    """Recursive flatten that writes into ``sink`` in place.

    Behavior matches ``MistHelper.flatten_dict_recursively``: nested
    dicts get joined keys; lists of dicts are indexed; lists of scalars
    become comma-joined strings.  Kept local so the adapter has zero
    runtime dependency on MistHelper.py.
    """
    for key, value in source.items():  # Iterate keys in insertion order
        key_str = str(key)  # CSV/JSON safety -- coerce non-str keys
        new_key = f"{parent_key}{sep}{key_str}" if parent_key else key_str  # Build dotted key path
        if isinstance(value, dict):  # Recurse into nested mapping
            _flatten_into(value, new_key, sep, sink)  # In-place update of sink
            continue  # Done with this entry
        if isinstance(value, list):  # Lists need per-element treatment
            if all(isinstance(elem, dict) for elem in value):  # List-of-dicts: index each entry
                for idx, elem in enumerate(value):  # Stable ordering for reproducible columns
                    _flatten_into(elem, f"{new_key}{sep}{idx}", sep, sink)  # Recurse with indexed key
                continue  # All children handled
            sink[new_key] = ",".join(map(str, value))  # Scalar list -> comma-joined string
            continue  # Move to next key
        sink[new_key] = value  # Base case: scalar value goes straight in
