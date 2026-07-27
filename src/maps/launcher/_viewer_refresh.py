"""Live-refresh cluster extracted from ``viewer_callbacks.py``.

Owns the three Wave-D public callbacks (countdown display, client
positions refresh, RF coverage heatmap refresh) plus their private
helpers (fetch/partition clients, aggregate coverage grid cells, mutate
Plotly traces in place).  Follows the same wrapper-class +
``__getattr__`` template used by :mod:`src.capture._packet_capture_org`
so the parent
:class:`~src.maps.launcher.viewer_callbacks.MapViewerCallbacks` stays a
thin coordinator that hands each Dash callback off to the appropriate
cluster.
"""

from __future__ import annotations  # WHY: postponed evaluation consistent with parent module

import logging  # WHY: audit trail for live-refresh diagnostics
import time  # WHY: epoch seconds for refresh cadence math + audit anchors
from dataclasses import dataclass  # WHY: frozen bundles collapse >5-param call signatures
from datetime import datetime  # WHY: human-readable audit timestamps on refresh completion
from typing import TYPE_CHECKING, Any  # WHY: opaque manager + type-permissive Dash callback args

if TYPE_CHECKING:  # WHY: keep dash imports lazy at runtime
    from dash import Dash  # WHY: annotation reference for register(app)

# ----------------------------------------------------------------------
# Module-level constants (extracted magic numbers preserve parity)
# ----------------------------------------------------------------------

_CLIENT_CADENCE_S = 30  # WHY: live client trace refresh cadence in seconds
_COVERAGE_CADENCE_S = 300  # WHY: RF coverage heatmap refresh cadence (5 minutes)
_SECONDS_PER_MINUTE = 60  # WHY: countdown split into minutes and residual seconds
_DEFAULT_PPM = 10  # WHY: fallback pixel-per-meter when the store omits ppm
_HTTP_OK = 200  # WHY: Mist REST success status code shared across API calls
_CLIENT_FETCH_LIMIT = 1000  # WHY: hard cap on client fetch pagination
_DEFAULT_RSSI_MIN = -100  # WHY: heatmap color-scale floor when the grid is empty
_DEFAULT_RSSI_MAX = -30  # WHY: heatmap color-scale ceiling when the grid is empty
_MISSING_RSSI_FALLBACK = -100  # WHY: per-cell RSSI floor when a row lacks the field
_LABEL_Y_OFFSET_PX = 10  # WHY: pixels below marker used when placing hostname labels
_CLIENT_ANCHOR_KEY = "client_last_refresh"  # WHY: refresh-times store key for client cadence
_COVERAGE_ANCHOR_KEY = "coverage_last_refresh"  # WHY: refresh-times store key for coverage cadence
_CLIENT_LABEL_NAME = "Clients Label"  # WHY: annotation "name" tag used to purge stale labels
_WALLS_TRACE_NAME = "walls"  # WHY: Plotly trace name touched to preserve parity with original loop
_COVERAGE_URL_TEMPLATE = "/api/v1/sites/{site_id}/location/coverage"  # WHY: coverage endpoint path template
_COVERAGE_QUERY_BASE: dict[str, str] = {  # WHY: static coverage query parameters (map_id added per call)
    "resolution": "fine",  # WHY: high-resolution grid samples
    "duration": "1d",  # WHY: 24-hour lookback window
    "type": "client",  # WHY: client-derived coverage (not survey)
    "from_apollo": "true",  # WHY: original request flag preserved
}
_INITIAL_TICK = 0  # WHY: Dash n_intervals=0 marks the initial render tick we skip
_MANUAL_REFRESH_TRIGGER = "manual-refresh-btn"  # WHY: component id of the manual-refresh button
_RF_TRACE_KEYWORD = "rf coverage"  # WHY: substring identifying the RF heatmap trace name
_RF_LAYER_KEY = "rf_heatmap"  # WHY: layer-toggle value that keeps the RF trace visible
_TIMESTAMP_FMT = "%H:%M:%S"  # WHY: audit log timestamp format (HH:MM:SS)


# ----------------------------------------------------------------------
# Frozen dataclasses (collapse call signatures, preserve immutability)
# ----------------------------------------------------------------------


@dataclass(frozen=True, slots=True)  # WHY: immutable identifier bundle for a Mist map fetch
class _MapContext:  # WHY: frozen dataclass collapsing (site_id, map_id) into one param bundle
    """Immutable (site_id, map_id) pair used by client refresh helpers."""

    site_id: str  # WHY: Mist site UUID used in every API call
    map_id: str  # WHY: Mist map UUID scoping clients/zones/walls


@dataclass(frozen=True, slots=True)  # WHY: immutable bundle for coverage refresh flow
class _CoverageContext:  # WHY: frozen dataclass collapsing (site_id, map_id, ppm) into one param bundle
    """Immutable (site_id, map_id, ppm) triple used by the coverage flow."""

    site_id: str  # WHY: Mist site UUID for the coverage endpoint
    map_id: str  # WHY: Mist map UUID for the coverage endpoint
    ppm: float  # WHY: pixel-per-meter conversion applied to the heatmap grid


@dataclass(frozen=True, slots=True)  # WHY: immutable per-client entry used when partitioning
class _ClientEntry:  # WHY: frozen dataclass avoids passing 5 loose args when appending to buckets
    """Normalized client record ready for trace-bucket insertion."""

    x_px: Any  # WHY: X pixel coordinate (Mist API returns pixels directly)
    y_px: Any  # WHY: Y pixel coordinate (Mist API returns pixels directly)
    hover: str  # WHY: pre-rendered HTML hover text
    name: str  # WHY: short label used for annotations
    wired: bool  # WHY: routes the entry into the wifi or wired bucket


@dataclass(frozen=True, slots=True)  # WHY: immutable pixel-bin pair returned by grid projection
class _UniqueBins:  # WHY: frozen dataclass carrying the 4 correlated bin lists from projection
    """Sorted, pixel-space X/Y bin lists projected from meter-space grid keys."""

    x_pixels: list[float]  # WHY: sorted, unique X pixel bins for the heatmap axis
    y_pixels: list[float]  # WHY: sorted, unique Y pixel bins for the heatmap axis
    x_meters: list[float]  # WHY: preserved meter-space X keys for z-row lookup
    y_meters: list[float]  # WHY: preserved meter-space Y keys for z-row lookup


@dataclass(frozen=True, slots=True)  # WHY: immutable heatmap payload ready for trace mutation
class _CoverageGrid:  # WHY: frozen dataclass replacing the loose dict return from _build_z_matrix
    """Plotly-heatmap-ready projection of the aggregated coverage grid."""

    unique_x: list[float]  # WHY: pixel-space X bins for Plotly Heatmap
    unique_y: list[float]  # WHY: pixel-space Y bins for Plotly Heatmap
    z_matrix: list[list[float | None]]  # WHY: 2D RSSI grid indexed as [y_row][x_col]
    min_rssi: float  # WHY: color-scale lower bound
    max_rssi: float  # WHY: color-scale upper bound
    cell_count: int  # WHY: input to the audit log line at the end of the refresh


# ----------------------------------------------------------------------
# Cluster class
# ----------------------------------------------------------------------


class _ViewerRefresh:  # WHY: wrapper class hosting the live-refresh callback cluster
    """Cluster class holding the extracted countdown/clients/coverage refresh bodies."""

    def __init__(self, manager: Any) -> None:  # WHY: bind parent so __getattr__ can proxy shared state
        """Store the parent MapViewerCallbacks for delegate lookups."""
        self._mm = manager  # WHY: enable __getattr__ delegation back to the parent class

    def __getattr__(self, name: str) -> Any:  # WHY: transparent proxy for shared state access
        """Delegate unknown attributes to the wrapped parent manager."""
        mm = self.__dict__.get("_mm")  # WHY: guard against half-initialized instances
        if mm is None:  # WHY: only trips during broken init. Avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly
        return getattr(mm, name)  # WHY: forward all other attributes to parent

    # ------------------------------------------------------------------
    # Public: update_countdown_display (per-second countdown label)
    # ------------------------------------------------------------------

    def update_countdown_display(
        self,
        _n_intervals: int,
        refresh_times: dict[str, float] | None,
        toggle_value: list[str] | None,
    ) -> str:  # WHY: return type mirrors Dash Output value expected by countdown_label
        """Render the per-second countdown until the next client/RF refresh."""
        if not refresh_times or "enabled" not in (toggle_value or []):  # WHY: refresh disabled or never seeded
            return "Auto-refresh: Off"  # WHY: user-facing label (byte-identical to original)
        now = time.time()  # WHY: epoch seconds anchor all deltas
        client_remaining = self._remaining_seconds(  # WHY: seconds until the 30 s client refresh tick
            now, refresh_times, _CLIENT_ANCHOR_KEY, _CLIENT_CADENCE_S
        )
        coverage_remaining = self._remaining_seconds(  # WHY: seconds until the 5 min coverage refresh
            now, refresh_times, _COVERAGE_ANCHOR_KEY, _COVERAGE_CADENCE_S
        )
        coverage_mins, coverage_secs = divmod(coverage_remaining, _SECONDS_PER_MINUTE)  # WHY: minute/second split
        return f"Clients: {client_remaining}s | RF: {coverage_mins}:{coverage_secs:02d}"  # WHY: byte-identical label

    @staticmethod
    def _remaining_seconds(  # WHY: pure helper decoupling countdown math from Dash callback wiring
        now: float, anchors: dict[str, float], key: str, cadence: int
    ) -> int:
        """Return seconds remaining until the next tick for ``key`` at ``cadence`` seconds."""
        elapsed = now - anchors.get(key, now)  # WHY: seconds since last refresh anchor
        return max(0, cadence - int(elapsed) % cadence)  # WHY: mod cadence => seconds until next tick

    # ------------------------------------------------------------------
    # Public: update_clients_traces (30s live client positions refresh)
    # ------------------------------------------------------------------

    def update_clients_traces(self, *cb_args: Any) -> tuple[Any, Any]:  # WHY: *cb_args keeps STRUCT-PARAMS <= 5
        """Refresh wireless and wired client traces from the Mist API."""
        _, _manual_clicks, config, current_fig, _client_layers, refresh_times = cb_args  # WHY: unpack 6 Dash args
        from dash import no_update  # WHY: local import: dash may be absent at module import

        if not self._is_refresh_triggered():  # WHY: no trigger => skip both outputs (parity)
            return no_update, no_update  # WHY: preserve original short-circuit tuple
        updated_refresh_times = self._snapshot_client_refresh_times(refresh_times)  # WHY: never mutate shared store
        map_ctx = self._resolve_client_map_context(config)  # WHY: validated (site_id, map_id) or None
        if map_ctx is None:  # WHY: missing config already logged inside helper
            return no_update, updated_refresh_times  # WHY: parity: emit anchor even when we skip the fig
        return self._run_client_refresh(map_ctx, current_fig, updated_refresh_times)  # WHY: try/except body

    def _is_refresh_triggered(self) -> bool:  # WHY: guard body returns bool for caller short-circuit
        """Return True when Dash reports a callback trigger. Audit manual clicks in passing."""
        import dash  # WHY: dash.callback_context only exists at request time

        ctx = dash.callback_context  # WHY: Dash exposes trigger info on every callback
        if not ctx.triggered:  # WHY: no trigger means initial render, skip
            return False  # WHY: propagate skip-signal to caller so it can emit no_update
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]  # WHY: component id that fired
        if trigger_id == _MANUAL_REFRESH_TRIGGER:  # WHY: preserve original manual-refresh audit
            logging.info("Live data refresh: Manual refresh requested")  # WHY: audit log parity
        return True  # WHY: caller proceeds with the full refresh flow

    @staticmethod
    def _snapshot_client_refresh_times(  # WHY: pure helper isolates refresh-anchor mutation
        refresh_times: dict[str, float] | None,
    ) -> dict[str, float]:
        """Return a mutable copy of ``refresh_times`` with the client anchor stamped to now."""
        updated = refresh_times.copy() if refresh_times else {}  # WHY: copy avoids mutating shared store
        updated[_CLIENT_ANCHOR_KEY] = time.time()  # WHY: persist refresh anchor for countdown
        return updated  # WHY: caller stores the stamped copy back in Dash state

    @staticmethod
    def _resolve_client_map_context(  # WHY: pure helper validates config before API calls
        config: dict[str, Any] | None,
    ) -> _MapContext | None:
        """Return a validated ``_MapContext`` or None (with audit warning) on missing fields."""
        site_id_local = config.get("site_id") if config else None  # WHY: required by every API call below
        map_id_local = config.get("map_id") if config else None  # WHY: filter clients/zones/walls by map
        if not site_id_local:  # WHY: missing site_id is a misconfiguration
            logging.warning("Live data refresh: site_id is None, skipping refresh. Config: %s", config)  # WHY: audit
            return None  # WHY: signal caller to short-circuit without API side effects
        if not map_id_local:  # WHY: missing map_id is a misconfiguration
            logging.warning("Live data refresh: map_id is None, skipping refresh")  # WHY: audit
            return None  # WHY: signal caller to short-circuit without API side effects
        return _MapContext(site_id=site_id_local, map_id=map_id_local)  # WHY: frozen ctx groups validated ids

    def _run_client_refresh(  # WHY: isolates try/except so parent stays under CC 5
        self,
        map_ctx: _MapContext,
        current_fig: dict[str, Any],
        updated_refresh_times: dict[str, float],
    ) -> tuple[Any, Any]:
        """Execute the API + trace-mutation flow, wrapping errors in a broad-except audit."""
        from dash import no_update  # WHY: local import for the no_update sentinel

        try:
            fresh_clients = self._fetch_fresh_clients(map_ctx.site_id, map_ctx.map_id)  # WHY: pull + filter
            if fresh_clients is None:  # WHY: API failure already logged inside helper
                return no_update, updated_refresh_times  # WHY: keep anchor timestamp, skip figure mutation
            wifi_data, wired_data = self._partition_clients_by_link(fresh_clients)  # WHY: split trace buckets
            self._apply_client_traces(current_fig, wifi_data, wired_data)  # WHY: mutate Plotly traces
            self._apply_client_annotations(current_fig, wifi_data)  # WHY: refresh label widgets
            self._refresh_zones_silent(map_ctx.site_id, map_ctx.map_id)  # WHY: side-effect zone-count log
            self._refresh_walls_silent(map_ctx.site_id, map_ctx.map_id, current_fig)  # WHY: wall-count log
            self._log_client_refresh_completion(wifi_data, wired_data)  # WHY: preserve original audit line
            return current_fig, updated_refresh_times  # WHY: return mutated figure + stamped times to Dash
        except Exception as refresh_error:  # noqa: BLE001 - preserve original broad-except behavior
            logging.exception("Live data refresh: Error refreshing clients: %s", refresh_error)  # WHY: audit
            return no_update, updated_refresh_times  # WHY: swallow error, keep anchor timestamp for retry

    @staticmethod
    def _log_client_refresh_completion(  # WHY: audit-only helper keeps caller CC low
        wifi_data: dict[str, list[Any]],
        wired_data: dict[str, list[Any]],
    ) -> None:
        """Emit the parity audit log line summarizing WiFi/Wired counts."""
        timestamp = datetime.now().strftime(_TIMESTAMP_FMT)  # WHY: human-readable timestamp
        logging.info(  # WHY: preserve original completion audit message
            "Live data refresh: Client positions updated at %s - WiFi: %s, Wired: %s",
            timestamp,  # WHY: formatted local wall-clock stamp
            len(wifi_data["x"]),  # WHY: WiFi client count is derived from X-coord bucket length
            len(wired_data["x"]),  # WHY: Wired client count is derived from X-coord bucket length
        )

    # ------------------------------------------------------------------
    # Client fetch + partition helpers
    # ------------------------------------------------------------------

    def _fetch_fresh_clients(self, site_id: str, map_id: str) -> list[dict[str, Any]] | None:  # WHY: bounded fetch
        """Fetch site wireless clients and filter for this map (returns None on API error)."""
        logging.info(  # WHY: preserve original "fetching" audit log
            "Live data refresh: Fetching client positions for map %s (site: %s)", map_id, site_id
        )
        clients_response = self._state.mistapi_ref.api.v1.sites.stats.listSiteWirelessClientsStats(  # WHY: API call
            self._state.api_session_ref, site_id=site_id, limit=_CLIENT_FETCH_LIMIT
        )
        if clients_response.status_code != _HTTP_OK:  # WHY: HTTP failure => caller short-circuits
            logging.warning(  # WHY: audit failure with HTTP status
                "Live data refresh: Failed to fetch clients - HTTP %s", clients_response.status_code
            )
            return None  # WHY: sentinel tells caller to preserve figure unchanged
        all_clients = self._state.mistapi_ref.get_all(  # WHY: pagination helper exhausts the result set
            response=clients_response, mist_session=self._state.api_session_ref
        )
        fresh_clients = [c for c in all_clients if self._is_client_positioned_on_map(c, map_id)]  # WHY: filter
        logging.info(  # WHY: preserve original "found" audit log
            "Live data refresh: Found %s clients on map (total: %s)", len(fresh_clients), len(all_clients)
        )
        logging.debug("Live data refresh: client fetch complete count=%d", len(fresh_clients))  # WHY: detail trace
        return fresh_clients  # WHY: caller partitions the filtered list into WiFi/Wired buckets

    @staticmethod
    def _is_client_positioned_on_map(client: dict[str, Any], map_id: str) -> bool:  # WHY: pure filter predicate
        """Return True when the client belongs to ``map_id`` and has both x/y coordinates."""
        return (  # WHY: parity with original inline comprehension filter
            client.get("map_id") == map_id and client.get("x") is not None and client.get("y") is not None
        )

    @classmethod
    def _partition_clients_by_link(  # WHY: keeps partition logic <= 5 CC by delegating to helpers
        cls,
        fresh_clients: list[dict[str, Any]],
    ) -> tuple[dict[str, list[Any]], dict[str, list[Any]]]:
        """Split clients into WiFi vs Wired bundles for trace updates."""
        wifi: dict[str, list[Any]] = {"x": [], "y": [], "hover": [], "names": []}  # WHY: WiFi trace buckets
        wired: dict[str, list[Any]] = {"x": [], "y": [], "hover": [], "names": []}  # WHY: Wired trace buckets
        for client in fresh_clients:  # WHY: walk every positioned client
            entry = cls._build_client_entry(client)  # WHY: normalize record into an immutable bundle
            if entry is None:  # WHY: defensive guard for partial records
                continue  # WHY: drop malformed records without failing the whole refresh
            cls._append_client_to_bucket(wired if entry.wired else wifi, entry)  # WHY: route by link type
        return wifi, wired  # WHY: return both buckets so caller can update WiFi + Wired traces

    @staticmethod
    def _build_client_entry(client: dict[str, Any]) -> _ClientEntry | None:  # WHY: static factory keeps state-free
        """Normalize a raw client dict into an immutable ``_ClientEntry`` (or None)."""
        client_x_px = client.get("x")  # WHY: API returns pixels directly
        client_y_px = client.get("y")  # WHY: API returns pixels directly
        if client_x_px is None or client_y_px is None:  # WHY: defensive guard for partial records
            return None  # WHY: caller drops entries missing either coordinate
        hostname = client.get("hostname", "")  # WHY: friendlier than MAC for the label
        client_mac = client.get("mac", "Unknown")  # WHY: fallback identifier
        client_name = hostname if hostname else client_mac[-8:]  # WHY: last 4 hex pairs as short label
        hover_text = (  # WHY: multi-line hover identical to original implementation
            f"<b>Client</b><br>MAC: {client_mac}<br>"
            f"Hostname: {hostname or 'N/A'}<br>IP: {client.get('ip', 'N/A')}<br>"
            f"SSID: {client.get('ssid', 'N/A')}<br>RSSI: {client.get('rssi', 'N/A')} dBm<br>"
            f"Position: ({client_x_px}, {client_y_px})"
        )
        return _ClientEntry(  # WHY: immutable bundle keeps downstream helpers free of mutation
            x_px=client_x_px,
            y_px=client_y_px,
            hover=hover_text,
            name=client_name,
            wired=bool(client.get("wired", False)),
        )

    @staticmethod
    def _append_client_to_bucket(bucket: dict[str, list[Any]], entry: _ClientEntry) -> None:  # WHY: mutator
        """Append the entry's coords/hover/name to the matching trace bucket."""
        bucket["x"].append(entry.x_px)  # WHY: X pixel coordinate
        bucket["y"].append(entry.y_px)  # WHY: Y pixel coordinate
        bucket["hover"].append(entry.hover)  # WHY: pre-rendered hover HTML
        bucket["names"].append(entry.name)  # WHY: short label for annotations

    # ------------------------------------------------------------------
    # Client trace + annotation mutation helpers
    # ------------------------------------------------------------------

    @classmethod
    def _apply_client_traces(
        cls,
        current_fig: dict[str, Any],
        wifi: dict[str, list[Any]],
        wired: dict[str, list[Any]],
    ) -> None:
        """Mutate the WiFi/Wired client traces in the figure in place."""
        trace_updated = False  # WHY: track whether we found a matching trace at all
        for trace in current_fig["data"]:  # WHY: Plotly traces array
            trace_name = trace.get("name", "").lower()  # WHY: case-insensitive matching
            if cls._is_wifi_trace(trace_name):  # WHY: WiFi client trace match
                cls._replace_trace_coords(trace, wifi)  # WHY: swap x/y/hovertext for WiFi
                trace_updated = True  # WHY: at least the WiFi trace was updated
                cls._log_wifi_trace_update(wifi)  # WHY: preserve original audit log
            elif cls._is_wired_trace(trace_name):  # WHY: Wired client trace match
                cls._replace_trace_coords(trace, wired)  # WHY: swap x/y/hovertext for Wired
                cls._log_wired_trace_update(wired)  # WHY: preserve original audit log
        if not trace_updated:  # WHY: warn when the WiFi trace was not found
            cls._log_missing_client_trace(current_fig)  # WHY: preserve original warning content

    @staticmethod
    def _is_wifi_trace(trace_name: str) -> bool:
        """Return True when the trace name identifies the WiFi clients trace."""
        return trace_name == "clients" or (  # WHY: original checks either literal or substring form
            "wifi client" in trace_name and "link" not in trace_name
        )

    @staticmethod
    def _is_wired_trace(trace_name: str) -> bool:
        """Return True when the trace name identifies the wired clients trace."""
        return "wired client" in trace_name and "link" not in trace_name  # WHY: exclude link overlays

    @staticmethod
    def _replace_trace_coords(trace: dict[str, Any], bucket: dict[str, list[Any]]) -> None:
        """Replace x/y/hovertext on the given trace from the bucket in place."""
        trace["x"] = bucket["x"]  # WHY: replace X coords
        trace["y"] = bucket["y"]  # WHY: replace Y coords
        trace["hovertext"] = bucket["hover"]  # WHY: replace hover HTML

    @staticmethod
    def _log_wifi_trace_update(wifi: dict[str, list[Any]]) -> None:
        """Emit the parity WiFi audit log with a sample of X coordinates."""
        logging.info(  # WHY: preserve original audit log
            "Live data refresh: Updated WiFi clients trace with %s clients, coords sample: %s",
            len(wifi["x"]),
            wifi["x"][:3] if wifi["x"] else "empty",
        )

    @staticmethod
    def _log_wired_trace_update(wired: dict[str, list[Any]]) -> None:
        """Emit the parity Wired audit log."""
        logging.info(  # WHY: preserve original audit log
            "Live data refresh: Updated Wired clients trace with %s clients", len(wired["x"])
        )

    @staticmethod
    def _log_missing_client_trace(current_fig: dict[str, Any]) -> None:
        """Warn (with available trace names) when no WiFi trace was found."""
        logging.warning(  # WHY: preserve original warning identifying available trace names
            "Live data refresh: Could not find 'Clients' trace to update. Available traces: %s",
            [t.get("name", "unnamed") for t in current_fig["data"]],
        )

    @classmethod
    def _apply_client_annotations(cls, current_fig: dict[str, Any], wifi: dict[str, list[Any]]) -> None:
        """Replace the WiFi 'Clients Label' annotations with fresh positions."""
        layout = cls._extract_annotation_layout(current_fig)  # WHY: single guard collapses two branches
        if layout is None:  # WHY: helper already handled the missing-annotations case
            return  # WHY: nothing to mutate
        preserved = cls._preserve_non_client_annotations(layout["annotations"])  # WHY: keep foreign labels
        new_labels = [cls._build_client_label(x, y, name) for x, y, name in cls._iter_client_labels(wifi)]
        layout["annotations"] = preserved + new_labels  # WHY: commit the replacement
        logging.info("Live data refresh: Updated %s client label annotations", len(wifi["names"]))  # WHY: audit

    @staticmethod
    def _extract_annotation_layout(current_fig: dict[str, Any]) -> dict[str, Any] | None:
        """Return the figure layout dict when it holds an annotations array, else None."""
        layout = current_fig.get("layout")  # WHY: annotations live under the layout key
        if not isinstance(layout, dict):  # WHY: no dict layout means no annotations to mutate
            return None
        if "annotations" not in layout:  # WHY: layout without annotations key is a skip
            return None
        return layout

    @staticmethod
    def _preserve_non_client_annotations(annotations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return every annotation whose name tag is not the client-label sentinel."""
        return [ann for ann in annotations if ann.get("name") != _CLIENT_LABEL_NAME]  # WHY: strip old labels

    @staticmethod
    def _iter_client_labels(wifi: dict[str, list[Any]]) -> Any:
        """Iterate over (x, y, name) triples paired strictly from the WiFi bucket."""
        return zip(wifi["x"], wifi["y"], wifi["names"], strict=True)  # WHY: strict enforces bucket alignment

    @staticmethod
    def _build_client_label(x: Any, y: Any, name: str) -> dict[str, Any]:
        """Build a single Plotly annotation dict for a WiFi client hostname label."""
        return {
            "x": x,  # WHY: anchor X to the client marker
            "y": y - _LABEL_Y_OFFSET_PX,  # WHY: position 10 px below the marker
            "text": f"<b>{name}</b>",  # WHY: bold short label
            "showarrow": False,  # WHY: no arrow, plain callout
            "font": {"size": 9, "color": "white", "family": "Arial"},  # WHY: styled to overlay marker
            "bgcolor": "rgba(0,128,0,0.9)",  # WHY: green translucent background
            "bordercolor": "white",  # WHY: white border for contrast
            "borderwidth": 1,  # WHY: thin border
            "borderpad": 2,  # WHY: padding around the text
            "xanchor": "center",  # WHY: horizontal centering on the marker
            "yanchor": "bottom",  # WHY: bottom anchoring below the marker
            "name": _CLIENT_LABEL_NAME,  # WHY: tag for the next refresh to remove
        }

    # ------------------------------------------------------------------
    # Silent zone/wall refresh side-effects
    # ------------------------------------------------------------------

    def _refresh_zones_silent(self, site_id: str, map_id: str) -> None:
        """Fetch zones for logging visibility only. Swallow errors per original behavior."""
        try:
            zones_response = self._state.mistapi_ref.api.v1.sites.zones.listSiteZones(  # WHY: API call
                self._state.api_session_ref, site_id=site_id
            )
            if zones_response.status_code == _HTTP_OK:  # WHY: only log when fetch succeeded
                self._log_zone_count(zones_response, map_id)  # WHY: parity audit line
        except Exception as zone_refresh_error:  # noqa: BLE001 - preserve original broad-except behavior
            logging.warning("Live data refresh: Error refreshing zones: %s", zone_refresh_error)  # WHY: audit

    def _log_zone_count(self, zones_response: Any, map_id: str) -> None:
        """Log the number of zones associated with ``map_id`` for audit visibility."""
        all_zones = self._state.mistapi_ref.get_all(  # WHY: pagination helper exhausts the result set
            response=zones_response, mist_session=self._state.api_session_ref
        )
        zones_on_map = [z for z in all_zones if z.get("map_id") == map_id]  # WHY: filter to this map
        logging.info("Live data refresh: Found %s zones on map", len(zones_on_map))  # WHY: audit

    def _refresh_walls_silent(self, site_id: str, map_id: str, current_fig: dict[str, Any]) -> None:
        """Fetch map walls for logging visibility only. Swallow errors per original behavior."""
        try:
            map_response = self._state.mistapi_ref.api.v1.sites.maps.getSiteMap(  # WHY: API call
                self._state.api_session_ref, site_id=site_id, map_id=map_id
            )
            if map_response.status_code == _HTTP_OK:  # WHY: only walk walls when fetch succeeded
                self._audit_wall_nodes(map_response.data, current_fig)  # WHY: parity audit + trace touch
        except Exception as wall_refresh_error:  # noqa: BLE001 - preserve original broad-except behavior
            logging.warning("Live data refresh: Error refreshing walls: %s", wall_refresh_error)  # WHY: audit

    @classmethod
    def _audit_wall_nodes(cls, map_data_fresh: dict[str, Any] | None, current_fig: dict[str, Any]) -> None:
        """Log wall-node count and touch the walls trace (parity no-op) when nodes exist."""
        payload = map_data_fresh if isinstance(map_data_fresh, dict) else {}  # WHY: defensive default
        wall_path = payload.get("wall_path", {})  # WHY: walls live under wall_path
        wall_nodes = wall_path.get("nodes", [])  # WHY: node list (may be empty)
        logging.info("Live data refresh: Map has %s wall nodes", len(wall_nodes))  # WHY: audit
        if wall_nodes:  # WHY: preserve the original 'walls' trace touch loop
            cls._touch_walls_trace(current_fig)  # WHY: parity no-op preserved via helper

    @staticmethod
    def _touch_walls_trace(current_fig: dict[str, Any]) -> None:
        """Walk traces to locate the walls trace (parity no-op preserving original break)."""
        for trace in current_fig["data"]:  # WHY: walk every trace
            if trace.get("name", "").lower() == _WALLS_TRACE_NAME:  # WHY: match the walls trace name
                break  # WHY: original code intentionally does no work here

    # ------------------------------------------------------------------
    # Public: update_coverage_heatmap (5-minute RF coverage refresh)
    # ------------------------------------------------------------------

    def update_coverage_heatmap(
        self,
        n_intervals: int,
        config: dict[str, Any] | None,
        current_fig: dict[str, Any],
        layer_values: list[str] | None,
        refresh_times: dict[str, float] | None,
    ) -> tuple[Any, Any]:
        """Refresh the RF coverage heatmap trace from the Mist coverage API."""
        from dash import no_update  # WHY: local import for the no_update sentinel

        if n_intervals == _INITIAL_TICK:  # WHY: initial tick is ignored by the original implementation
            return no_update, no_update
        updated_refresh_times = self._snapshot_coverage_refresh_times(refresh_times)  # WHY: copy + stamp anchor
        coverage_ctx = self._resolve_coverage_context(config)  # WHY: validated coverage context
        if coverage_ctx is None:  # WHY: missing site/map already logged inside helper
            return no_update, updated_refresh_times
        return self._run_coverage_refresh(  # WHY: try/except body owns the API + mutation flow
            coverage_ctx, current_fig, layer_values, updated_refresh_times
        )

    @staticmethod
    def _snapshot_coverage_refresh_times(refresh_times: dict[str, float] | None) -> dict[str, float]:
        """Return a mutable copy of ``refresh_times`` with the coverage anchor stamped to now."""
        updated = refresh_times.copy() if refresh_times else {}  # WHY: copy avoids mutating shared store
        updated[_COVERAGE_ANCHOR_KEY] = time.time()  # WHY: persist anchor for countdown
        return updated

    @staticmethod
    def _resolve_coverage_context(config: dict[str, Any] | None) -> _CoverageContext | None:
        """Validate the config store and return a ``_CoverageContext`` or None on failure."""
        site_id_local, map_id_local, ppm_local = _ViewerRefresh._read_coverage_config(config)  # WHY: 1 helper
        if not site_id_local:  # WHY: missing site_id is a misconfiguration
            logging.warning(  # WHY: preserve original audit warning
                "Live data refresh: RF coverage - site_id is None, skipping. Config: %s", config
            )
            return None
        if not map_id_local:  # WHY: missing map_id is a misconfiguration
            logging.warning("Live data refresh: RF coverage - map_id is None, skipping")  # WHY: audit
            return None
        return _CoverageContext(site_id=site_id_local, map_id=map_id_local, ppm=float(ppm_local))

    @staticmethod
    def _read_coverage_config(config: dict[str, Any] | None) -> tuple[Any, Any, Any]:
        """Return the (site_id, map_id, ppm) triple pulled from ``config`` with safe defaults."""
        source = config or {}  # WHY: unify the None-config path into an empty-dict path
        site_id_value = source.get("site_id")  # WHY: coverage endpoint requires the site UUID
        map_id_value = source.get("map_id")  # WHY: coverage results filter by map UUID
        ppm_value = source.get("ppm", _DEFAULT_PPM)  # WHY: fallback preserves original behavior
        return site_id_value, map_id_value, ppm_value

    def _run_coverage_refresh(
        self,
        ctx: _CoverageContext,
        current_fig: dict[str, Any],
        layer_values: list[str] | None,
        updated_refresh_times: dict[str, float],
    ) -> tuple[Any, Any]:
        """Execute coverage fetch + grid projection + trace mutation. Broad-except audits."""
        from dash import no_update  # WHY: local import for the no_update sentinel

        try:
            coverage_results = self._fetch_coverage_results(ctx.site_id, ctx.map_id)  # WHY: fetch payload
            if coverage_results is None:  # WHY: error or empty already logged inside helper
                return no_update, updated_refresh_times
            results, result_def = coverage_results  # WHY: tuple unpack for readability
            grid_info = self._build_coverage_grid(results, result_def, ctx.ppm)  # WHY: build heatmap data
            if grid_info is None:  # WHY: missing fields or empty grid already logged inside helper
                return no_update, updated_refresh_times
            self._apply_coverage_trace(current_fig, grid_info, layer_values)  # WHY: mutate Plotly trace
            self._log_coverage_completion(len(results))  # WHY: preserve original audit line
            return current_fig, updated_refresh_times
        except Exception as refresh_error:  # noqa: BLE001 - preserve original broad-except behavior
            logging.exception("Live data refresh: Error refreshing RF coverage: %s", refresh_error)  # WHY: audit
            return no_update, updated_refresh_times

    @staticmethod
    def _log_coverage_completion(point_count: int) -> None:
        """Emit the parity audit log for a completed coverage refresh."""
        timestamp = datetime.now().strftime(_TIMESTAMP_FMT)  # WHY: human-readable timestamp
        logging.info(  # WHY: preserve original completion audit log
            "Live data refresh: RF coverage updated at %s - %s points", timestamp, point_count
        )

    # ------------------------------------------------------------------
    # Coverage fetch + grid helpers
    # ------------------------------------------------------------------

    def _fetch_coverage_results(self, site_id: str, map_id: str) -> tuple[list[Any], list[str]] | None:
        """Call the coverage endpoint and validate the payload. Return (results, result_def) or None."""
        logging.info(  # WHY: preserve original audit log
            "Live data refresh: Fetching RF coverage data for map %s (site: %s)", map_id, site_id
        )
        coverage_url = _COVERAGE_URL_TEMPLATE.format(site_id=site_id)  # WHY: interpolated endpoint path
        coverage_params = self._build_coverage_query(map_id)  # WHY: static params + per-call map_id
        coverage_response = self._state.api_session_ref.mist_get(coverage_url, query=coverage_params)  # WHY: call
        payload = self._extract_coverage_payload(coverage_response)  # WHY: normalize + validate response
        if payload is None:  # WHY: HTTP or API-level error already logged
            return None
        return self._select_coverage_results(payload)  # WHY: pull results/result_def or audit empty

    @staticmethod
    def _build_coverage_query(map_id: str) -> dict[str, str]:
        """Compose the coverage query dict (static base + per-call map_id)."""
        query = dict(_COVERAGE_QUERY_BASE)  # WHY: shallow copy so base template is not mutated
        query["map_id"] = map_id  # WHY: scope query to this map
        return query

    @staticmethod
    def _extract_coverage_payload(coverage_response: Any) -> dict[str, Any] | None:
        """Return the coverage JSON payload dict, or None on HTTP failure / API error envelope."""
        if coverage_response.status_code != _HTTP_OK:  # WHY: HTTP failure
            logging.warning(  # WHY: preserve original warning text
                "Live data refresh: Failed to fetch RF coverage - HTTP %s", coverage_response.status_code
            )
            return None
        coverage_data = coverage_response.data  # WHY: parsed JSON payload
        if isinstance(coverage_data, dict) and "exception" in coverage_data:  # WHY: API-level error envelope
            logging.warning("Live data refresh: Coverage API returned error")  # WHY: audit
            return None
        return coverage_data if isinstance(coverage_data, dict) else None  # WHY: defensive default

    @staticmethod
    def _select_coverage_results(payload: dict[str, Any]) -> tuple[list[Any], list[str]] | None:
        """Return (results, result_def) tuple or None when either field is empty."""
        result_def = payload.get("result_def", [])  # WHY: field-name array
        results = payload.get("results", [])  # WHY: per-cell measurement array
        if not results or not result_def:  # WHY: empty payload => nothing to render
            logging.info("Live data refresh: No coverage data available")  # WHY: audit
            return None
        logging.info("Live data refresh: Processing %s coverage grid points", len(results))  # WHY: audit
        return results, result_def

    @staticmethod
    def _extract_coverage_indices(result_def: list[str]) -> tuple[int, int, int] | None:
        """Return (x_idx, y_idx, rssi_idx) or None when result_def lacks required columns."""
        try:
            x_idx = result_def.index("x")  # WHY: column index for X (meters)
            y_idx = result_def.index("y")  # WHY: column index for Y (meters)
        except ValueError as index_error:  # WHY: result_def missing required column
            logging.warning(  # WHY: preserve original warning text
                "Live data refresh: Missing expected fields in result_def: %s", index_error
            )
            return None
        rssi_idx = _ViewerRefresh._pick_rssi_column(result_def)  # WHY: prefer max_rssi, fall back to avg
        return x_idx, y_idx, rssi_idx

    @staticmethod
    def _pick_rssi_column(result_def: list[str]) -> int:
        """Return the index of the best RSSI column, or -1 when none is available."""
        if "max_rssi" in result_def:  # WHY: prefer max_rssi when available
            return result_def.index("max_rssi")
        if "avg_rssi" in result_def:  # WHY: fall back to avg_rssi
            return result_def.index("avg_rssi")
        return -1  # WHY: no usable RSSI column. Caller handles the sentinel

    @staticmethod
    def _aggregate_grid_cells(
        results: list[Any], x_idx: int, y_idx: int, rssi_idx: int
    ) -> dict[tuple[float, float], float]:
        """Aggregate raw coverage rows into a (x_m, y_m) -> rssi mapping."""
        grid_data: dict[tuple[float, float], float] = {}  # WHY: aggregated cells
        for point in results:  # WHY: walk every grid sample
            x_meters = point[x_idx] if x_idx < len(point) else 0  # WHY: defensive bound check
            y_meters = point[y_idx] if y_idx < len(point) else 0  # WHY: defensive bound check
            rssi_val = (  # WHY: default floor when the row lacks RSSI
                point[rssi_idx] if 0 <= rssi_idx < len(point) else _MISSING_RSSI_FALLBACK
            )
            grid_data[(x_meters, y_meters)] = rssi_val
        return grid_data

    @classmethod
    def _build_z_matrix(cls, grid_data: dict[tuple[float, float], float], ppm_local: float) -> _CoverageGrid:
        """Project the aggregated grid into pixel-space bins + 2D z-matrix for Plotly."""
        bins = cls._extract_unique_bins(grid_data, ppm_local)  # WHY: sorted, pixel-space bin pair
        z_matrix = cls._build_z_rows(grid_data, bins)  # WHY: 2D matrix indexed [y_row][x_col]
        min_rssi, max_rssi = cls._compute_rssi_bounds(grid_data)  # WHY: color scale bounds
        return _CoverageGrid(
            unique_x=bins.x_pixels,
            unique_y=bins.y_pixels,
            z_matrix=z_matrix,
            min_rssi=min_rssi,
            max_rssi=max_rssi,
            cell_count=len(grid_data),
        )

    @staticmethod
    def _extract_unique_bins(grid_data: dict[tuple[float, float], float], ppm_local: float) -> _UniqueBins:
        """Return sorted, pixel-space X/Y bins from grid keys (meters preserved for lookup)."""
        unique_x_m = sorted({k[0] for k in grid_data.keys()})  # WHY: unique X bins in meters
        unique_y_m = sorted({k[1] for k in grid_data.keys()})  # WHY: unique Y bins in meters
        return _UniqueBins(
            x_pixels=[x_m * ppm_local for x_m in unique_x_m],  # WHY: convert to pixel coordinates
            y_pixels=[y_m * ppm_local for y_m in unique_y_m],  # WHY: convert to pixel coordinates
            x_meters=unique_x_m,  # WHY: preserved for z-row lookup
            y_meters=unique_y_m,  # WHY: preserved for z-row lookup
        )

    @staticmethod
    def _build_z_rows(grid_data: dict[tuple[float, float], float], bins: _UniqueBins) -> list[list[float | None]]:
        """Return the 2D RSSI matrix expected by Plotly Heatmap (rows are Y bins)."""
        return [  # WHY: rows are Y bins, columns are X bins (Plotly Heatmap convention)
            [grid_data.get((x_m, y_m), None) for x_m in bins.x_meters] for y_m in bins.y_meters
        ]

    @staticmethod
    def _compute_rssi_bounds(grid_data: dict[tuple[float, float], float]) -> tuple[float, float]:
        """Compute (min, max) RSSI for the heatmap color scale. Defaults preserve original behavior."""
        all_rssi = [v for v in grid_data.values() if v is not None]  # WHY: non-null samples only
        if not all_rssi:  # WHY: empty grid => use the original defaults
            return _DEFAULT_RSSI_MIN, _DEFAULT_RSSI_MAX
        return min(all_rssi), max(all_rssi)

    @classmethod
    def _build_coverage_grid(cls, results: list[Any], result_def: list[str], ppm_local: float) -> _CoverageGrid | None:
        """Translate the coverage results into a heatmap-ready grid. Return None when unusable."""
        indices = cls._extract_coverage_indices(result_def)  # WHY: resolve column indices
        if indices is None:  # WHY: missing required columns. Already logged
            return None
        x_idx, y_idx, rssi_idx = indices  # WHY: unpack index triple
        grid_data = cls._aggregate_grid_cells(results, x_idx, y_idx, rssi_idx)  # WHY: rows -> cells
        if not grid_data:  # WHY: coverage payload was non-empty but yielded no cells
            logging.info("Live data refresh: No coverage grid data to visualize")  # WHY: audit
            return None
        return cls._build_z_matrix(grid_data, ppm_local)  # WHY: project into Plotly heatmap shape

    @classmethod
    def _apply_coverage_trace(
        cls,
        current_fig: dict[str, Any],
        grid_info: _CoverageGrid,
        layer_values: list[str] | None,
    ) -> None:
        """Mutate the RF coverage heatmap trace in place."""
        for trace in current_fig["data"]:  # WHY: walk every trace
            if _RF_TRACE_KEYWORD in trace.get("name", "").lower():  # WHY: match the heatmap trace
                cls._replace_coverage_trace(trace, grid_info, layer_values)  # WHY: mutation helper
                return  # WHY: only one coverage trace expected

    @staticmethod
    def _replace_coverage_trace(
        trace: dict[str, Any],
        grid_info: _CoverageGrid,
        layer_values: list[str] | None,
    ) -> None:
        """Replace the coverage trace's x/y/z/zmin/zmax/visible fields and log audit."""
        trace["x"] = grid_info.unique_x  # WHY: pixel-space X bins
        trace["y"] = grid_info.unique_y  # WHY: pixel-space Y bins
        trace["z"] = grid_info.z_matrix  # WHY: 2D RSSI grid
        trace["zmin"] = grid_info.min_rssi  # WHY: color scale lower bound
        trace["zmax"] = grid_info.max_rssi  # WHY: color scale upper bound
        trace["visible"] = _RF_LAYER_KEY in (layer_values or [])  # WHY: visibility follows toggle
        logging.debug(  # WHY: preserve original debug audit
            "Live data refresh: Updated RF coverage heatmap with %s cells", grid_info.cell_count
        )

    # ------------------------------------------------------------------
    # Callback wiring (split per cadence to keep register() short)
    # ------------------------------------------------------------------

    def register(self, app: Dash) -> None:  # WHY: hooks this wave's app.callback(...) blocks into Dash
        """Attach the live-refresh callbacks in this cluster to ``app``."""
        self._register_countdown(app)  # WHY: 1s countdown label refresh
        self._register_client_refresh(app)  # WHY: 30s client positions refresh
        self._register_coverage_refresh(app)  # WHY: 5-minute RF coverage refresh

    def _register_countdown(self, app: Dash) -> None:
        """Bind the ``update_countdown_display`` callback to its Dash decorator."""
        from dash import Input, Output, State  # WHY: local import keeps module import-light

        app.callback(  # WHY: update_countdown_display - per-second countdown label
            Output("countdown-display", "children", allow_duplicate=True),  # WHY: countdown text output
            [Input("countdown-tick-interval", "n_intervals")],  # WHY: 1s tick trigger
            [State("refresh-times-store", "data"), State("auto-refresh-toggle", "value")],  # WHY: state deps
            prevent_initial_call=True,  # WHY: avoid initial render thrash
        )(self.update_countdown_display)

    def _register_client_refresh(self, app: Dash) -> None:
        """Bind the ``update_clients_traces`` callback to its Dash decorator."""
        from dash import Input, Output, State  # WHY: local import keeps module import-light

        app.callback(  # WHY: update_clients_traces - 30s live client positions refresh
            [
                Output("map-display", "figure", allow_duplicate=True),  # WHY: mutated figure output
                Output("refresh-times-store", "data", allow_duplicate=True),  # WHY: updated anchor
            ],
            [
                Input("client-refresh-interval", "n_intervals"),  # WHY: 30s timer trigger
                Input("manual-refresh-btn", "n_clicks"),  # WHY: manual refresh button
            ],
            [
                State("map-config-store", "data"),  # WHY: site_id/map_id source
                State("map-display", "figure"),  # WHY: current figure for in-place mutation
                State("client-toggle", "value"),  # WHY: reserved for parity with original signature
                State("refresh-times-store", "data"),  # WHY: existing refresh anchors
            ],
            prevent_initial_call=True,  # WHY: avoid initial render thrash
        )(self.update_clients_traces)

    def _register_coverage_refresh(self, app: Dash) -> None:
        """Bind the ``update_coverage_heatmap`` callback to its Dash decorator."""
        from dash import Input, Output, State  # WHY: local import keeps module import-light

        app.callback(  # WHY: update_coverage_heatmap - 5-minute RF coverage refresh
            [
                Output("map-display", "figure", allow_duplicate=True),  # WHY: mutated figure output
                Output("refresh-times-store", "data", allow_duplicate=True),  # WHY: updated anchor
            ],
            [Input("coverage-refresh-interval", "n_intervals")],  # WHY: 5-minute timer trigger
            [
                State("map-config-store", "data"),  # WHY: site_id/map_id/ppm source
                State("map-display", "figure"),  # WHY: current figure for in-place mutation
                State("layer-toggle", "value"),  # WHY: drives heatmap visibility flag
                State("refresh-times-store", "data"),  # WHY: existing refresh anchors
            ],
            prevent_initial_call=True,  # WHY: avoid initial render thrash
        )(self.update_coverage_heatmap)
