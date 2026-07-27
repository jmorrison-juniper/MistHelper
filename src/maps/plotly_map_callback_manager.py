"""Callback helper logic for Plotly map viewer interactions."""

from __future__ import annotations  # WHY: postponed evaluation for annotations

from collections.abc import Callable  # WHY: Callable moved to collections.abc per PEP 585
from dataclasses import dataclass  # WHY: frozen bundle collapses wide callback signatures
from typing import Any  # WHY: Dash payloads are dynamic dicts

# WHY: (layer_name, substring) rule table drives trace visibility without if/elif chains.
TRACE_VISIBILITY_RULES: tuple[tuple[str, str], ...] = (
    ("walls", "wall"),  # WHY: floor-plan walls trace
    ("wayfinding", "wayfinding"),  # WHY: wayfinding path trace
    ("zones", "zone"),  # WHY: zone polygon trace
    ("validation", "validation"),  # WHY: coverage validation trace
    ("rf_heatmap", "rf coverage"),  # WHY: RF heatmap trace
    ("origin", "map origin"),  # WHY: origin marker trace
    ("vbeacons", "virtual beacon"),  # WHY: vbeacon trace variant 1
    ("vbeacons", "vbeacon"),  # WHY: vbeacon trace variant 2
    ("ble_beacons", "ble beacon"),  # WHY: BLE beacon trace
    ("wifi_clients", "wifi client"),  # WHY: connected WiFi clients
    ("wired_clients", "wired client"),  # WHY: connected wired clients
    ("show_client_ap", "client-ap link"),  # WHY: client<->AP association line
    ("mesh_links", "mesh link"),  # WHY: mesh backhaul link trace
    ("vbeacon_coverage", "vbeacon coverage"),  # WHY: vbeacon coverage overlay
    ("aps", "access point"),  # WHY: access-point marker trace
    ("switches", "switch"),  # WHY: switch marker trace
    ("gateways", "gateway"),  # WHY: gateway marker trace
)

# WHY: (layer_name, substring) rule table drives annotation visibility.
ANNOTATION_VISIBILITY_RULES: tuple[tuple[str, str], ...] = (
    ("zones", "zone label"),  # WHY: zone text annotation
    ("aps", "access points label"),  # WHY: AP text annotation
    ("switches", "switches label"),  # WHY: switch text annotation
    ("gateways", "gateways label"),  # WHY: gateway text annotation
    ("wifi_clients", "wifi clients label"),  # WHY: WiFi client text annotation
    ("wired_clients", "wired clients label"),  # WHY: wired client text annotation
    ("vbeacons", "virtual beacons label"),  # WHY: vbeacon text annotation
    ("ble_beacons", "ble beacons label"),  # WHY: BLE beacon text annotation
)

CLIENT_LAYER_NAMES: frozenset[str] = frozenset({"wifi_clients", "wired_clients"})  # WHY: combined client layer set
_BEACON_PREFIX: str = "beacon "  # WHY: unnamed BLE beacon trace prefix
_CLIENT_TOKEN: str = "client"  # WHY: catch-all client trace token
_AP_TOKEN: str = "ap"  # WHY: catch-all AP trace token
_CLIENTS_LABEL_TOKEN: str = "clients label"  # WHY: catch-all client label token
_HOVER_LINE_SEP: str = "<br>"  # WHY: Plotly hover-text line separator
_BOLD_OPEN: str = "<b>"  # WHY: bold open tag stripped from lines
_BOLD_CLOSE: str = "</b>"  # WHY: bold close tag stripped from lines
_TYPE_MARKER: str = "Type:"  # WHY: marks the row containing device type
_TYPE_CLASSNAME: str = "device-detail"  # WHY: CSS class applied to the type row
_DEFAULT_INFO_STYLE: dict[str, str] = {"color": "#888", "fontStyle": "italic"}  # WHY: default sidebar prompt style
_NO_DATA_MESSAGE: str = "No device data available"  # WHY: fallback body message
_DEFAULT_PROMPT: str = "Click a device for details"  # WHY: empty-state prompt copy
_DEVICE_INFO_HEADER: str = "Device Info"  # WHY: header when no click has occurred
_DEVICE_DETAILS_HEADER: str = "Device Details"  # WHY: header when device is selected


def _coerce_layer_list(value: list[str] | None) -> tuple[str, ...]:  # WHY: shared None-safe coercion
    """Return a tuple copy of ``value``, treating None/empty uniformly as an empty tuple."""
    return tuple(value or ())  # WHY: single branch keeps callers simple


@dataclass(frozen=True, slots=True)
class LayerToggleInputs:  # WHY: frozen bundle keeps callback signature narrow
    """Frozen bundle of layer selection lists sourced from Dash toggle inputs."""

    infra: tuple[str, ...] = ()  # WHY: walls, wayfinding, zones, and so on
    beacon: tuple[str, ...] = ()  # WHY: vbeacons + BLE beacons category
    client: tuple[str, ...] = ()  # WHY: wifi/wired client toggles
    device: tuple[str, ...] = ()  # WHY: APs, switches, gateways
    filter: tuple[str, ...] = ()  # WHY: status-filter category

    @classmethod
    def from_optional_lists(  # WHY: Dash inputs arrive as five optional lists
        cls,
        infra: list[str] | None,
        beacon: list[str] | None,
        client: list[str] | None,
        device: list[str] | None,
        filter_: list[str] | None,
    ) -> LayerToggleInputs:
        """Coerce Dash-supplied optional lists into a frozen tuple bundle."""
        return cls(
            infra=_coerce_layer_list(infra),  # WHY: delegate None-safe copy
            beacon=_coerce_layer_list(beacon),  # WHY: delegate None-safe copy
            client=_coerce_layer_list(client),  # WHY: delegate None-safe copy
            device=_coerce_layer_list(device),  # WHY: delegate None-safe copy
            filter=_coerce_layer_list(filter_),  # WHY: delegate None-safe copy
        )

    def all_layers(self) -> frozenset[str]:  # WHY: precomputed union used by two passes
        """Return the union of every selected layer across every category."""
        merged = self.infra + self.beacon + self.client + self.device + self.filter  # WHY: concat tuples
        return frozenset(merged)  # WHY: O(1) membership tests downstream


def _client_layers_enabled(all_layers: frozenset[str]) -> bool:  # WHY: shared wifi/wired check
    """Return True when any client layer (wifi or wired) is enabled."""
    return not CLIENT_LAYER_NAMES.isdisjoint(all_layers)  # WHY: set intersection check


def _resolve_by_rules(  # WHY: table-driven visibility lookup shared by traces + annotations
    entity_name: str,
    rules: tuple[tuple[str, str], ...],
    all_layers: frozenset[str],
) -> bool | None:
    """Consult a visibility rule table; return None when no rule matches."""
    for layer_name, token in rules:  # WHY: linear scan preserves original ordering semantics
        if token in entity_name:  # WHY: substring match against lowercased entity name
            return layer_name in all_layers  # WHY: first-match wins
    return None  # WHY: caller must fall back to secondary rules


def _resolve_trace_visibility(trace_name: str, all_layers: frozenset[str]) -> bool | None:  # WHY: trace-only resolver
    """Return trace visibility from the rule table or via fallback prefix/token logic."""
    table_hit = _resolve_by_rules(trace_name, TRACE_VISIBILITY_RULES, all_layers)  # WHY: primary table
    if table_hit is not None:  # WHY: rule table decisions win outright
        return table_hit  # WHY: skip fallback ladder when a rule already matched
    if trace_name.startswith(_BEACON_PREFIX):  # WHY: unnamed BLE beacon prefix fallback
        return "ble_beacons" in all_layers  # WHY: gate BLE beacons visibility
    if _CLIENT_TOKEN in trace_name:  # WHY: catch-all client trace fallback
        return _client_layers_enabled(all_layers)  # WHY: any-client catch-all
    if _AP_TOKEN in trace_name:  # WHY: catch-all AP trace fallback
        return "aps" in all_layers  # WHY: any-AP catch-all
    return None  # WHY: no rule matched — leave trace visibility untouched


def _resolve_annotation_visibility(  # WHY: annotation-only resolver
    annotation_name: str, all_layers: frozenset[str]
) -> bool | None:
    """Return annotation visibility from the rule table or via fallback token logic."""
    table_hit = _resolve_by_rules(annotation_name, ANNOTATION_VISIBILITY_RULES, all_layers)  # WHY: primary
    if table_hit is not None:  # WHY: rule table decisions win outright
        return table_hit  # WHY: skip fallback when a rule already matched
    if _CLIENTS_LABEL_TOKEN in annotation_name:  # WHY: generic clients-label fallback
        return _client_layers_enabled(all_layers)  # WHY: any-client-label catch-all
    return None  # WHY: no rule matched — leave annotation untouched


def _apply_trace_visibility(fig: dict[str, Any], all_layers: frozenset[str]) -> None:
    """Update visibility for every trace in ``fig`` based on layer selection."""
    for trace in fig.get("data", []):  # WHY: iterate figure traces in place
        visibility = _resolve_trace_visibility(trace.get("name", "").lower(), all_layers)
        if visibility is not None:
            trace["visible"] = visibility  # WHY: overwrite only when we have a decision


def _apply_annotation_visibility(fig: dict[str, Any], all_layers: frozenset[str]) -> None:
    """Update visibility for every annotation in ``fig`` based on layer selection."""
    annotations = fig.get("layout", {}).get("annotations", [])  # WHY: safe deep-get
    for annotation in annotations:  # WHY: iterate annotations in place
        visibility = _resolve_annotation_visibility(annotation.get("name", "").lower(), all_layers)
        if visibility is not None:
            annotation["visible"] = visibility  # WHY: overwrite only when we have a decision


def _clean_hover_line(line: str) -> str:
    """Strip bold tags from a hover-text line."""
    return line.replace(_BOLD_OPEN, "").replace(_BOLD_CLOSE, "")  # WHY: drop Plotly markup


def _build_hover_paragraphs(hover_text: str, html: Any) -> list[Any]:
    """Convert Plotly hover-text into a list of Dash html paragraphs."""
    paragraphs: list[Any] = []  # WHY: accumulate <p> nodes for the sidebar
    for line in hover_text.split(_HOVER_LINE_SEP):  # WHY: <br>-separated rows
        stripped = line.strip()
        if not stripped:
            continue  # WHY: skip blank rows to avoid empty <p> tags
        classname = _TYPE_CLASSNAME if _TYPE_MARKER in stripped else None  # WHY: highlight type row
        paragraphs.append(html.P(_clean_hover_line(stripped), className=classname))
    return paragraphs


def _default_click_sidebar(html: Any) -> list[Any]:
    """Return the default click-info sidebar shown before any device is clicked."""
    return [
        html.H3(_DEVICE_INFO_HEADER),  # WHY: header for empty-state
        html.P(_DEFAULT_PROMPT, style=_DEFAULT_INFO_STYLE),  # WHY: styled hint copy
    ]


def make_dash_layer_callback(
    manager: PlotlyMapCallbackManager,
) -> Callable[..., dict[str, Any]]:
    """Return a Dash-facing callback that packs positional inputs into the bundle."""

    def _pack_and_apply(*dash_args: Any) -> dict[str, Any]:  # WHY: Dash entry point
        """Dash entry point: five layer lists followed by the current figure state."""
        *layer_lists, current_fig = dash_args  # WHY: last positional arg is the figure state
        bundle = LayerToggleInputs.from_optional_lists(*layer_lists)  # WHY: pack into frozen bundle
        return manager.apply_layer_toggles(bundle, current_fig)  # WHY: dispatch to typed API

    return _pack_and_apply


class PlotlyMapCallbackManager:
    """Encapsulate callback business logic for map viewer callbacks."""

    def apply_layer_toggles(
        self,
        layer_inputs: LayerToggleInputs,
        current_fig: dict[str, Any],
    ) -> dict[str, Any]:
        """Apply user layer selections to traces and annotations.

        Callers pack the Dash Input values into a :class:`LayerToggleInputs`
        bundle (see :func:`make_dash_layer_callback`) so this method stays
        under the parameter limit while still mutating the figure in place.
        """
        all_layers = layer_inputs.all_layers()  # WHY: precompute union for both passes
        _apply_trace_visibility(current_fig, all_layers)  # WHY: mutate figure traces in place
        _apply_annotation_visibility(current_fig, all_layers)  # WHY: mutate annotations in place
        return current_fig  # WHY: Dash expects the updated figure back

    def build_click_details(self, click_data: dict[str, Any] | None, html: Any) -> list[Any]:
        """Build click-data sidebar content from Plotly click payload."""
        if click_data is None:
            return _default_click_sidebar(html)  # WHY: no click yet — show empty-state prompt
        hover_text = click_data["points"][0].get("hovertext", "")  # WHY: first point drives the panel
        details = _build_hover_paragraphs(hover_text, html) if hover_text else []  # WHY: parse rows
        body = details if details else [html.P(_NO_DATA_MESSAGE)]  # WHY: fallback when parse yields nothing
        return [html.H3(_DEVICE_DETAILS_HEADER), html.Div(body)]  # WHY: sidebar layout header + body
