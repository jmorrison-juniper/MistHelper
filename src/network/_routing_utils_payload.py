"""HTTP/API payload construction cluster for :mod:`src.network.routing_utils`.

Owns the helpers that translate collected user inputs into request
bodies for Mist device commands and the dedicated SSR/SRX routing API,
plus the two callers that POST those payloads
(``_post_device_command`` for generic device commands and
``_call_ssr_api`` for the SSR/SRX routing endpoint). Splitting these
helpers off the parent :class:`~src.network.routing_utils.RoutingUtils`
cuts several length + complexity + STRUCT-PARAMS violations from the
parent module.

The parent binds an instance as ``self._payload`` and its
``__getattr__`` proxies unknown attribute lookups here so shared state
(dependencies, apisession, parsing/display clusters) stays transparent.
This module mirrors the Phase 1/2 parsing + display split.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import logging  # WHY: SSR API error path emits structured warnings for production visibility
import os  # WHY: MIST_HOST / MIST_APITOKEN fall back to environment when session lacks them
from dataclasses import dataclass  # WHY: RoutingPayloadQuery bundles 6 user inputs into one param
from http import HTTPStatus  # WHY: response.status_code compared against HTTPStatus.OK
from typing import TYPE_CHECKING, Any  # WHY: TYPE_CHECKING avoids runtime cycle with parent

import mistapi  # WHY: SSR/SRX routing table API lives under mistapi.api.v1.sites.devices
import requests  # WHY: generic device command endpoint is invoked via requests.post

logger = logging.getLogger(__name__)  # WHY: module-scoped logger for print-to-logger migration

if TYPE_CHECKING:  # WHY: only needed for static type checkers; skipped at runtime
    from src.network.routing_utils import RoutingUtils, SsrRouteQuery  # WHY: types for annotation only


# WHY: routing table API accepts this closed set of protocol filters (lowercase)
_VALID_ROUTING_PROTOCOLS: frozenset[str] = frozenset(
    {"bgp", "ospf", "static", "direct", "evpn", "any"}  # WHY: 'any' is default, others are filters
)

# WHY: SSR/SRX routing API uses the same protocol set as generic routing table
_VALID_SSR_PROTOCOLS: frozenset[str] = frozenset(
    {"any", "bgp", "ospf", "static", "direct", "evpn"}  # WHY: matches SSR API contract
)

# WHY: BGP neighbor route direction filter accepts only these two directional keywords
_VALID_ROUTE_DIRECTIONS: frozenset[str] = frozenset({"received", "advertised"})  # WHY: API-defined

# WHY: HA cluster node selection accepts only these two identifiers
_VALID_NODES: frozenset[str] = frozenset({"node0", "node1"})  # WHY: API-defined enum

# WHY: SSR refresh interval must fall inside [0, 10] seconds per API contract
_MIN_INTERVAL: int = 0  # WHY: 0 disables real-time refresh (one-shot query)
_MAX_INTERVAL: int = 10  # WHY: SSR API refuses intervals above 10 seconds

# WHY: SSR refresh duration must fall inside [0, 300] seconds per API contract
_MIN_DURATION: int = 0  # WHY: 0 duration is documented but rare
_MAX_DURATION: int = 300  # WHY: SSR API caps refresh duration at 5 minutes

# WHY: default refresh duration when user supplies interval but leaves duration blank
_DEFAULT_DURATION: int = 30  # WHY: matches legacy inline default preserved from parent module

# WHY: outbound POST to Mist has a hard timeout to prevent hung sessions
_HTTP_TIMEOUT: int = 30  # WHY: 30s matches legacy behavior


@dataclass(frozen=True)
class RoutingPayloadQuery:
    """User inputs collected for the routing table API request.

    Bundles the 6 fields that :meth:`_RoutingUtilsPayload._build_routing_payload`
    previously accepted as separate arguments, resolving the parent
    module's STRUCT-PARAMS violation and matching the pattern used by
    :class:`SsrRouteQuery` on the parent module.
    """

    prefix_input: str  # WHY: CIDR string filter; empty means match every prefix
    protocol_input: str  # WHY: protocol keyword (bgp/ospf/static/direct/evpn/any); coerced to 'any'
    vrf_input: str  # WHY: VRF/routing-instance name; empty means default VRF
    neighbor_input: str  # WHY: BGP neighbor IP filter; empty disables neighbor scoping
    route_direction: str  # WHY: received/advertised when neighbor is set; empty means both
    node_input: str  # WHY: HA node identifier (node0/node1); empty means unspecified


class _RoutingUtilsPayload:  # WHY: cluster wrapper matching the parsing/display split
    """Wrapper class holding the extracted payload/HTTP helpers."""

    def __init__(self, parent: RoutingUtils) -> None:  # WHY: bind parent so __getattr__ can proxy state
        """Store the parent :class:`RoutingUtils` for delegate lookups."""
        self._ru = parent  # WHY: enable __getattr__ delegation back to RoutingUtils

    def __getattr__(self, name: str) -> Any:  # WHY: transparent proxy so callers see combined API
        """Delegate unknown attributes to the wrapped parent object."""
        parent = self.__dict__.get("_ru")  # WHY: guard against half-initialized instances
        if parent is None:  # WHY: only trips during broken init; avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly to callers
        return getattr(parent, name)  # WHY: transparent proxy to the parent RoutingUtils

    # ------------------------------------------------------------------
    # Routing table payload builder (was STRUCT-PARAMS violation on parent)
    # ------------------------------------------------------------------

    def _build_routing_payload(self, query: RoutingPayloadQuery) -> dict[str, Any]:
        """Build routing table API payload from user inputs."""
        payload: dict[str, Any] = {}  # WHY: accumulator populated by each optional-field applier
        self._apply_prefix(payload, query.prefix_input)  # WHY: attaches prefix only when non-empty
        self._apply_protocol(payload, query.protocol_input)  # WHY: coerces invalid input to 'any'
        self._apply_vrf(payload, query.vrf_input)  # WHY: attaches vrf only when non-empty
        self._apply_neighbor(payload, query.neighbor_input, query.route_direction)  # WHY: pair set
        self._apply_node(payload, query.node_input)  # WHY: attaches node only when valid identifier
        return payload  # WHY: caller passes payload straight to the device command endpoint

    @staticmethod
    def _apply_prefix(payload: dict[str, Any], prefix_input: str) -> None:
        """Attach a route prefix to ``payload`` when the user supplied one."""
        if prefix_input:  # WHY: empty string means "match all prefixes"; omit key entirely
            payload["prefix"] = prefix_input  # WHY: preserve original casing/format for the API

    @staticmethod
    def _apply_protocol(payload: dict[str, Any], protocol_input: str) -> None:
        """Attach a protocol filter to ``payload`` (coerces invalid input to 'any')."""
        normalized = protocol_input.lower() if protocol_input else ""  # WHY: normalize once
        if normalized in _VALID_ROUTING_PROTOCOLS:  # WHY: guard clause routes valid keywords through
            payload["protocol"] = normalized  # WHY: store normalized (lowercase) form
            return  # WHY: early-return prevents the default fallback below
        payload["protocol"] = "any"  # WHY: legacy behavior — unknown filter degrades to 'any'

    @staticmethod
    def _apply_vrf(payload: dict[str, Any], vrf_input: str) -> None:
        """Attach a VRF name to ``payload`` when the user supplied one."""
        if vrf_input:  # WHY: empty means default VRF; API omission = default
            payload["vrf"] = vrf_input  # WHY: preserve original casing for name-matching

    def _apply_neighbor(
        self,
        payload: dict[str, Any],
        neighbor_input: str,
        route_direction: str,
    ) -> None:
        """Attach neighbor IP (and optional route direction) to ``payload``."""
        if not neighbor_input:  # WHY: neighbor filter is optional; short-circuit when unset
            return  # WHY: skip both neighbor and direction fields when neighbor is empty
        payload["neighbor"] = neighbor_input  # WHY: preserve exact IP the user entered
        direction = route_direction.lower() if route_direction else ""  # WHY: normalize once
        if direction in _VALID_ROUTE_DIRECTIONS:  # WHY: only accept received/advertised keywords
            payload["route"] = direction  # WHY: attach direction only when it validates

    @staticmethod
    def _apply_node(payload: dict[str, Any], node_input: str) -> None:
        """Attach HA node identifier to ``payload`` when it validates."""
        node = node_input.lower() if node_input else ""  # WHY: normalize once for the compare below
        if node in _VALID_NODES:  # WHY: only node0/node1 are accepted by the API
            payload["node"] = node  # WHY: store normalized (lowercase) form

    # ------------------------------------------------------------------
    # SSR/SRX payload builder (was STRUCT-BLOCKS + STRUCT-COMPLEXITY on parent)
    # ------------------------------------------------------------------

    def _build_ssr_payload(self, query: SsrRouteQuery) -> dict[str, Any]:
        """Build SSR/SRX routing API request body from user inputs."""
        request_body: dict[str, Any] = {}  # WHY: accumulator populated by each optional-field applier
        self._apply_ssr_scalars(request_body, query)  # WHY: prefix/vrf/protocol block
        self._apply_ssr_neighbor(request_body, query)  # WHY: neighbor+direction pair block
        self._apply_ssr_node(request_body, query.node_input)  # WHY: node0/node1 identifier block
        self._apply_ssr_refresh_params(  # WHY: refresh interval + duration block
            request_body,
            query.interval_input,
            query.duration_input,
        )
        return request_body  # WHY: caller ships this directly to the SSR API

    @staticmethod
    def _apply_ssr_scalars(request_body: dict[str, Any], query: SsrRouteQuery) -> None:
        """Attach protocol, prefix, and VRF to ``request_body`` when supplied."""
        if query.protocol_input and query.protocol_input in _VALID_SSR_PROTOCOLS:  # WHY: guard set
            request_body["protocol"] = query.protocol_input  # WHY: store already-normalized keyword
        if query.prefix_input:  # WHY: prefix is always optional for the SSR API
            request_body["prefix"] = query.prefix_input  # WHY: preserve exact CIDR the user entered
        if query.vrf_input:  # WHY: empty vrf means "default VRF" (API omission convention)
            request_body["vrf"] = query.vrf_input  # WHY: preserve casing for name-matching

    @staticmethod
    def _apply_ssr_neighbor(request_body: dict[str, Any], query: SsrRouteQuery) -> None:
        """Attach BGP neighbor (and optional direction) to ``request_body``."""
        if not query.neighbor_input:  # WHY: neighbor filter is optional; short-circuit when unset
            return  # WHY: skip both neighbor + direction fields when neighbor is empty
        request_body["neighbor"] = query.neighbor_input  # WHY: preserve exact IP the user entered
        if query.route_direction in _VALID_ROUTE_DIRECTIONS:  # WHY: only received/advertised valid
            request_body["route"] = query.route_direction  # WHY: attach direction only when valid

    @staticmethod
    def _apply_ssr_node(request_body: dict[str, Any], node_input: str) -> None:
        """Attach HA node object to ``request_body`` when identifier validates."""
        if node_input in _VALID_NODES:  # WHY: only node0/node1 accepted; SSR wraps in nested object
            request_body["node"] = {"node": node_input}  # WHY: SSR API expects nested {"node": ...}

    def _apply_ssr_refresh_params(
        self,
        request_body: dict[str, Any],
        interval_input: str,
        duration_input: str,
    ) -> None:
        """Apply refresh interval and duration to SSR request body."""
        interval_val = self._parse_refresh_interval(interval_input)  # WHY: parse-once helper
        if interval_val is None:  # WHY: invalid/blank interval disables the entire refresh block
            return  # WHY: skip both interval and duration when interval is missing
        request_body["interval"] = interval_val  # WHY: always attach interval when it validates
        if interval_val == 0:  # WHY: interval=0 means one-shot; duration is meaningless then
            return  # WHY: early-return omits duration for one-shot queries
        request_body["duration"] = self._parse_refresh_duration(duration_input)  # WHY: parsed once

    @staticmethod
    def _parse_refresh_interval(interval_input: str) -> int | None:
        """Return the parsed interval seconds (in range) or ``None`` on any failure."""
        if not (interval_input and interval_input.isdigit()):  # WHY: guard clause on non-digit input
            return None  # WHY: caller treats None as "no refresh block"
        interval_val = int(interval_input)  # WHY: safe int cast after isdigit guard
        if not (_MIN_INTERVAL <= interval_val <= _MAX_INTERVAL):  # WHY: enforce API range [0, 10]
            return None  # WHY: out-of-range values disable refresh (matches legacy behavior)
        return interval_val  # WHY: valid interval passed through to the request body

    @staticmethod
    def _parse_refresh_duration(duration_input: str) -> int:
        """Return the parsed duration seconds (in range) or the legacy default."""
        if duration_input and duration_input.isdigit():  # WHY: guard clause on non-digit input
            duration_val = int(duration_input)  # WHY: safe int cast after isdigit guard
            if _MIN_DURATION <= duration_val <= _MAX_DURATION:  # WHY: enforce API range [0, 300]
                return duration_val  # WHY: user-supplied duration wins when it validates
        return _DEFAULT_DURATION  # WHY: legacy fallback default matches parent behavior

    # ------------------------------------------------------------------
    # Generic device command POST helper (was STRUCT-LENGTH + COMPLEXITY on parent)
    # ------------------------------------------------------------------

    def _post_device_command(
        self,
        site_id: str,
        device_id: str,
        endpoint: str,
        payload: dict[str, Any],
        debug_mode: bool,
    ) -> tuple[str | None, str | None]:
        """POST a command to a device REST endpoint. Returns (session_id, error_msg)."""
        host, token = self._resolve_credentials()  # WHY: pull host/token from session or env once
        if not host or not token:  # WHY: guard against missing credentials before attempting POST
            return None, "Mist host or API token not found in session or environment"  # WHY: signal
        url = f"https://{host}/api/v1/sites/{site_id}/devices/{device_id}/{endpoint}"  # WHY: standard path
        if debug_mode:  # WHY: expose URL for troubleshooting when debug is on
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.debug("[DEBUG] POST URL = %s", url)  # WHY: match legacy debug output verbatim
        response = requests.post(  # WHY: synchronous POST with hard timeout
            url,
            headers=self._build_auth_headers(token),  # WHY: token-based auth per Mist API
            json=payload,  # WHY: requests handles JSON serialization
            timeout=_HTTP_TIMEOUT,  # WHY: prevent hung sessions
        )
        self._log_response_debug(response, debug_mode)  # WHY: keep debug output identical to legacy
        return self._parse_command_response(response)  # WHY: uniform (session, error) tuple projection

    def _resolve_credentials(self) -> tuple[str | None, str | None]:
        """Return (host, token) from the apisession or the environment."""
        host = getattr(self._ru.apisession, "host", None) or os.getenv("MIST_HOST")  # WHY: fall-thru
        token = getattr(self._ru.apisession, "apitoken", None) or os.getenv("MIST_APITOKEN")  # WHY:
        return host, token  # WHY: caller validates both halves before continuing

    @staticmethod
    def _build_auth_headers(token: str) -> dict[str, str]:
        """Return the standard Mist auth + content-type headers."""
        return {  # WHY: dict literal keeps the two headers together in one expression
            "Authorization": f"Token {token}",  # WHY: Mist requires "Token <api-token>" scheme
            "Content-Type": "application/json",  # WHY: request body is always JSON
        }

    @staticmethod
    def _log_response_debug(response: requests.Response, debug_mode: bool) -> None:
        """Emit response status + body when debug mode is on."""
        if not debug_mode:  # WHY: guard clause avoids formatting the body when debug is off
            return  # WHY: keeps the hot path free of debug string formatting
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.debug("[DEBUG] HTTP Response Status = %s", response.status_code)  # WHY: legacy debug format
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.debug("[DEBUG] HTTP Response Body = %s", response.text)  # WHY: legacy debug format

    @staticmethod
    def _parse_command_response(
        response: requests.Response,
    ) -> tuple[str | None, str | None]:
        """Project a device command HTTP response into ``(session_id, error_msg)``."""
        if response.status_code != HTTPStatus.OK:  # WHY: any non-200 surfaces as an error message
            return None, f"HTTP {response.status_code}: {response.text}"  # WHY: preserve body detail
        session_id: str | None = response.json().get("session")  # WHY: session key holds the id
        if not session_id:  # WHY: missing session id is a soft failure (API accepted but no id)
            return None, "No session ID returned"  # WHY: caller surfaces this message to the user
        return session_id, None  # WHY: happy path — id present, no error

    # ------------------------------------------------------------------
    # SSR/SRX dedicated API helpers (was STRUCT-LENGTH + COMPLEXITY on parent)
    # ------------------------------------------------------------------

    def _call_ssr_api(
        self,
        site_id: str,
        device_id: str,
        request_body: dict[str, Any],
        debug_mode: bool,
    ) -> str | None:
        """Call the SSR/SRX routing table API and return session ID."""
        try:  # WHY: mistapi raises broad exceptions on transport/protocol failures
            return self._invoke_ssr_route_api(site_id, device_id, request_body, debug_mode)  # WHY:
        except Exception as api_error:  # WHY: match legacy catch-all to preserve UX
            return self._handle_ssr_api_error(api_error, debug_mode)  # WHY: uniform failure logging

    def _invoke_ssr_route_api(
        self,
        site_id: str,
        device_id: str,
        request_body: dict[str, Any],
        debug_mode: bool,
    ) -> str | None:
        """Perform the SSR/SRX API call and hand the response to session-id extraction."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("-> Calling dedicated SSR/SRX routing table API...")  # WHY: legacy UX text preserved
        if debug_mode:  # WHY: mirror legacy verbose logging for debug traces
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.debug("[DEBUG] Calling mistapi.api.v1.sites.devices.showSiteSsrAndSrxRoutes")  # WHY: URL
        response = mistapi.api.v1.sites.devices.showSiteSsrAndSrxRoutes(  # WHY: dedicated endpoint
            self._ru.apisession,  # WHY: reuse the parent-injected authenticated session
            site_id,  # WHY: path parameter identifying the site
            device_id,  # WHY: path parameter identifying the target device
            request_body,  # WHY: filter/refresh parameters assembled by _build_ssr_payload
        )
        self._log_ssr_response_debug(response, debug_mode)  # WHY: keep debug output identical
        return self._extract_ssr_session_id(response, debug_mode)  # WHY: uniform id extraction

    @staticmethod
    def _log_ssr_response_debug(response: Any, debug_mode: bool) -> None:
        """Emit SSR API response metadata when debug mode is on."""
        if not debug_mode:  # WHY: guard clause avoids attribute lookups when debug is off
            return  # WHY: keeps hot path free of formatting overhead
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.debug("[DEBUG] API response type: %s", type(response))  # WHY: legacy debug output preserved
        if hasattr(response, "data"):  # WHY: some responses do not carry a data attribute at all
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.debug("[DEBUG] Response data: %s", response.data)  # WHY: expose payload for triage

    @staticmethod
    def _handle_ssr_api_error(api_error: Exception, debug_mode: bool) -> None:
        """Emit uniform failure output for an SSR API exception and return ``None``."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.warning("! Error calling SSR/SRX routing table API: %s", api_error)  # WHY: user-facing message
        logger.error("SSR/SRX routing table API error: %s", api_error)  # WHY: capture for logs
        if debug_mode:  # WHY: only dump the traceback when debug mode is explicitly on
            import traceback  # WHY: local import matches legacy lazy behavior (rare failure path)

            traceback.print_exc()  # WHY: full stack aids on-site triage
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("\n-> Try the generic routing table command (Menu 7) as fallback")  # WHY: guidance
        return None  # WHY: signal failure to caller so it can skip the results wait

    def _extract_ssr_session_id(self, response: Any, debug_mode: bool) -> str | None:
        """Extract session ID from SSR API response."""
        if not (hasattr(response, "data") and response.data):  # WHY: guard against empty responses
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! Unexpected API response format")  # WHY: legacy message preserved for UX parity
            return None  # WHY: caller treats None as "no session started"
        session_id: str | None = response.data.get("session")  # WHY: 'session' key holds the id
        if not session_id:  # WHY: guard against present-but-empty session field
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! No session ID returned from SSR/SRX routing API")  # WHY: legacy message
            return None  # WHY: caller cancels the wait when no id is present
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("-> Command initiated (session: %s...)", session_id[:8])  # WHY: legacy UX preserved
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("-> Waiting for SSR/SRX routing table results...")  # WHY: user context between calls
        if debug_mode:  # WHY: full-id debug output when debug is on
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.debug("[DEBUG] Full session ID: %s", session_id)  # WHY: match legacy debug format
        return session_id  # WHY: caller uses this id to correlate WebSocket results
