"""Callback helper logic for Plotly map viewer interactions."""

from __future__ import annotations

from typing import Any

TRACE_VISIBILITY_RULES: list[tuple[str, str]] = [
    ("walls", "wall"),
    ("wayfinding", "wayfinding"),
    ("zones", "zone"),
    ("validation", "validation"),
    ("rf_heatmap", "rf coverage"),
    ("origin", "map origin"),
    ("vbeacons", "virtual beacon"),
    ("vbeacons", "vbeacon"),
    ("ble_beacons", "ble beacon"),
    ("wifi_clients", "wifi client"),
    ("wired_clients", "wired client"),
    ("show_client_ap", "client-ap link"),
    ("mesh_links", "mesh link"),
    ("vbeacon_coverage", "vbeacon coverage"),
    ("aps", "access point"),
    ("switches", "switch"),
    ("gateways", "gateway"),
]

ANNOTATION_VISIBILITY_RULES: list[tuple[str, str]] = [
    ("zones", "zone label"),
    ("aps", "access points label"),
    ("switches", "switches label"),
    ("gateways", "gateways label"),
    ("wifi_clients", "wifi clients label"),
    ("wired_clients", "wired clients label"),
    ("vbeacons", "virtual beacons label"),
    ("ble_beacons", "ble beacons label"),
]


class PlotlyMapCallbackManager:
    """Encapsulate callback business logic for map viewer callbacks."""

    def apply_layer_toggles(
        self,
        current_fig: dict[str, Any],
        infra_layers: list[str] | None,
        beacon_layers: list[str] | None,
        client_layers: list[str] | None,
        device_layers: list[str] | None,
        filter_layers: list[str] | None,
    ) -> dict[str, Any]:
        """Apply user layer selections to traces and annotations."""
        all_layers = (
            (infra_layers or [])
            + (beacon_layers or [])
            + (client_layers or [])
            + (device_layers or [])
            + (filter_layers or [])
        )

        for trace in current_fig.get("data", []):
            trace_name = trace.get("name", "").lower()
            self._set_trace_visibility(trace, trace_name, all_layers)

        for annotation in current_fig.get("layout", {}).get("annotations", []):
            annotation_name = annotation.get("name", "").lower()
            self._set_annotation_visibility(annotation, annotation_name, all_layers)

        return current_fig

    def build_click_details(self, click_data: dict[str, Any] | None, html: Any) -> list[Any]:
        """Build click-data sidebar content from Plotly click payload."""
        if click_data is None:
            return [
                html.H3("Device Info"),
                html.P("Click a device for details", style={"color": "#888", "fontStyle": "italic"}),
            ]

        point = click_data["points"][0]
        hover_text = point.get("hovertext", "")

        details = []
        if hover_text:
            lines = hover_text.split("<br>")
            for line in lines:
                if line.strip():
                    details.append(
                        html.P(
                            line.replace("<b>", "").replace("</b>", ""),
                            className="device-detail" if "Type:" in line else None,
                        )
                    )

        return [html.H3("Device Details"), html.Div(details if details else [html.P("No device data available")])]

    def _set_trace_visibility(self, trace: dict[str, Any], trace_name: str, all_layers: list[str]) -> None:
        """Set visibility for a trace based on layer selections."""
        for layer_name, token in TRACE_VISIBILITY_RULES:
            if token in trace_name:
                trace["visible"] = layer_name in all_layers
                return
        if trace_name.startswith("beacon "):
            trace["visible"] = "ble_beacons" in all_layers
            return
        if "client" in trace_name:
            trace["visible"] = self._client_layers_enabled(all_layers)
            return
        if "ap" in trace_name:
            trace["visible"] = "aps" in all_layers

    def _set_annotation_visibility(
        self,
        annotation: dict[str, Any],
        annotation_name: str,
        all_layers: list[str],
    ) -> None:
        """Set visibility for an annotation based on layer selections."""
        for layer_name, token in ANNOTATION_VISIBILITY_RULES:
            if token in annotation_name:
                annotation["visible"] = layer_name in all_layers
                return
        if "clients label" in annotation_name:
            annotation["visible"] = self._client_layers_enabled(all_layers)

    def _client_layers_enabled(self, all_layers: list[str]) -> bool:
        """Return True when any client layer is enabled."""
        return "wifi_clients" in all_layers or "wired_clients" in all_layers
