"""Figure-building helpers for Plotly map layers.

Extracted from the historical ``PlotlyMapFigureBuilder`` C-grade module. Every
public method now delegates the trace/annotation construction to small helpers
so that walls, wayfinding, and zone overlays share a single edge-drawing +
legend-trace path. Layer styling is expressed with a frozen ``_LayerStyle``
value object so the trace factories accept one bundle instead of five keyword
arguments.
"""

from __future__ import annotations  # WHY: postponed annotation evaluation for PEP 604 unions.

import logging  # WHY: debug/warning traces for map overlay construction.
from dataclasses import dataclass  # WHY: frozen slots ``_LayerStyle`` declaration.
from typing import Any  # WHY: opaque map/zone payload dicts flow through helpers.

import plotly.graph_objects as go  # WHY: figure/scatter primitives used to render overlays.

# ---------------------------------------------------------------------------
# Module-level styling constants (magic values extracted for maintainability)
# ---------------------------------------------------------------------------
_WALL_COLOR = "#ff3333"  # WHY: canonical wall stroke color shared by segment + legend.
_WALL_WIDTH = 4  # WHY: canonical wall stroke width in pixels.
_WAYFIND_COLOR = "#4488ff"  # WHY: canonical wayfinding stroke color.
_WAYFIND_WIDTH = 3  # WHY: canonical wayfinding stroke width in pixels.
_WAYFIND_MARKER_SIZE = 8  # WHY: wayfinding node marker radius in pixels.
_WAYFIND_DASH = "dash"  # WHY: wayfinding line dash pattern name.
_ZONE_BORDER_WIDTH = 2  # WHY: zone polygon border stroke width.
_ZONE_BORDER_DASH = "dot"  # WHY: zone polygon border dash pattern name.
_ZONE_LABEL_OFFSET = 10  # WHY: pixel inset for zone label from polygon min corner.
_ZONE_MIN_VERTICES = 3  # WHY: polygon requires at least 3 vertices to render.
_ZONE_LABEL_FONT_SIZE = 14  # WHY: zone label font size in points.
_ZONE_LABEL_BORDER_WIDTH = 2  # WHY: zone annotation border stroke width.
_ZONE_LABEL_BORDER_PAD = 4  # WHY: zone annotation border padding in pixels.
_ZONE_LABEL_FONT_FAMILY = "Arial Black"  # WHY: zone annotation font family.
_ZONE_LABEL_FONT_COLOR = "white"  # WHY: zone annotation text color.
_ZONE_LABEL_BORDER_COLOR = "white"  # WHY: zone annotation border color.
_FILL_ALPHA_TOKEN = "0.2"  # WHY: token replaced to derive darker border variant.
_BORDER_ALPHA_TOKEN = "0.8"  # WHY: token replaced again to derive label background variant.
_LABEL_BG_ALPHA_TOKEN = "0.9"  # WHY: label background alpha derived from border token.

_ZONE_FILL_COLORS: tuple[str, ...] = (  # WHY: table-driven palette cycled per zone index.
    "rgba(255,165,0,0.2)",
    "rgba(0,255,255,0.2)",
    "rgba(255,0,255,0.2)",
    "rgba(255,255,0,0.2)",
    "rgba(0,255,0,0.2)",
    "rgba(128,0,255,0.2)",
)


# ---------------------------------------------------------------------------
# Layer style value object
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class _LayerStyle:  # WHY: immutable bundle keeps trace helpers under STRUCT-PARAMS.
    """Line + marker styling for a single map overlay layer."""

    name: str  # WHY: legend/hover label and trace name.
    color: str  # WHY: line + marker stroke color.
    width: int  # WHY: line stroke width in pixels.
    dash: str | None = None  # WHY: optional dash pattern name (None -> solid).
    marker_size: int | None = None  # WHY: optional endpoint marker radius (None -> line-only).


_WALL_STYLE = _LayerStyle(  # WHY: reusable wall layer style avoids literal duplication.
    name="Walls",
    color=_WALL_COLOR,
    width=_WALL_WIDTH,
)

_WAYFIND_STYLE = _LayerStyle(  # WHY: reusable wayfinding layer style bundles dashed line + markers.
    name="Wayfinding",
    color=_WAYFIND_COLOR,
    width=_WAYFIND_WIDTH,
    dash=_WAYFIND_DASH,
    marker_size=_WAYFIND_MARKER_SIZE,
)


def _line_kwargs(style: _LayerStyle) -> dict[str, Any]:  # WHY: build go.Scatter line dict for a style.
    """Return the ``line=`` kwargs dict for a layer style."""
    kwargs: dict[str, Any] = {"color": style.color, "width": style.width}  # WHY: base color + width.
    if style.dash:  # WHY: only include ``dash`` key when the style requests one.
        kwargs["dash"] = style.dash  # WHY: preserve original dashed-line rendering.
    return kwargs


def _scatter_extras(style: _LayerStyle) -> dict[str, Any]:  # WHY: emit mode + optional marker together.
    """Return ``mode`` + optional ``marker`` kwargs consistent with the style."""
    if style.marker_size is None:  # WHY: line-only styles must not attach a marker kwarg.
        return {"mode": "lines"}
    return {  # WHY: styles with markers render endpoint dots alongside the line.
        "mode": "lines+markers",
        "marker": dict(size=style.marker_size, color=style.color),
    }


class PlotlyMapFigureBuilder:  # WHY: attaches walls/wayfinding/zones traces onto a go.Figure.
    """Add map layer traces/annotations to a Plotly figure."""

    def __init__(self, logger: logging.Logger | None = None):  # WHY: injectable logger simplifies testing.
        """Initialize figure builder with optional logger."""
        self.logger = logger or logging.getLogger(__name__)  # WHY: fallback to module logger.

    def add_walls(self, fig: go.Figure, map_data: dict[str, Any]) -> None:  # WHY: draws wall segments + legend.
        """Add wall segment traces and legend trace to figure."""
        nodes = self._extract_nodes(map_data, "wall_path", "Wall")  # WHY: guarded lookup for wall nodes.
        if not nodes:  # WHY: no nodes means the payload lacks a wall path.
            return
        node_lookup = self._build_node_lookup(nodes, "Wall")  # WHY: name -> position index for edge targets.
        self._add_edge_segments(fig, nodes, node_lookup, _WALL_STYLE)  # WHY: emit one trace per wall edge.
        fig.add_trace(self._legend_trace(_WALL_STYLE))  # WHY: hidden trace surfaces the legend entry.

    def add_wayfinding(self, fig: go.Figure, map_data: dict[str, Any]) -> None:  # WHY: draws path segments + legend.
        """Add wayfinding segment traces and legend trace to figure."""
        nodes = self._extract_nodes(map_data, "wayfinding_path", "Wayfinding")  # WHY: guarded wayfinding lookup.
        if not nodes:  # WHY: no nodes means the payload lacks a wayfinding path.
            return
        node_lookup = self._build_node_lookup(nodes, "Wayfinding")  # WHY: reuse edge-target index.
        self._add_edge_segments(fig, nodes, node_lookup, _WAYFIND_STYLE)  # WHY: emit one trace per wayfinding edge.
        fig.add_trace(self._legend_trace(_WAYFIND_STYLE))  # WHY: hidden trace surfaces the legend entry.

    def add_zones(self, fig: go.Figure, zones: list[dict[str, Any]]) -> None:  # WHY: draw zone polygons + labels.
        """Add zone polygons and labels to figure."""
        if not zones:  # WHY: guard-clause short-circuit for empty zone input.
            self.logger.info("No zones found on this map")
            return
        self.logger.info("Processing %s zones on this map", len(zones))  # WHY: audit total zone count.
        for index, zone in enumerate(zones):  # WHY: table-driven per-zone rendering keeps CC low.
            self._add_single_zone(fig, index, zone)

    def _extract_nodes(  # WHY: shared guard/logging shrinks add_walls / add_wayfinding to one liners.
        self,
        map_data: dict[str, Any],
        path_key: str,
        node_type: str,
    ) -> list[dict[str, Any]]:
        """Return non-empty node list under ``path_key`` or an empty list."""
        path = map_data.get(path_key)  # WHY: locate wall/wayfinding sub-payload.
        if not path:  # WHY: absent path is a no-op (legacy behavior preserved).
            return []
        self.logger.debug("%s path data structure: %s", node_type, path)  # WHY: aid map-data debugging.
        nodes = path.get("nodes", [])  # WHY: node list is optional in payload.
        if not nodes:  # WHY: empty node list is a no-op (legacy behavior preserved).
            return []
        self.logger.info("Processing %s %s path nodes", len(nodes), node_type.lower())  # WHY: audit count.
        return list(nodes)  # WHY: force list narrowing so mypy accepts declared return type.

    def _build_node_lookup(  # WHY: name-indexed positions used to resolve edge endpoints.
        self,
        nodes: list[dict[str, Any]],
        node_type: str,
    ) -> dict[str, dict[str, Any]]:
        """Build lookup table of named nodes to positions."""
        lookup: dict[str, dict[str, Any]] = {}  # WHY: accumulator returned to caller.
        for node in nodes:  # WHY: single pass keeps CC at 3.
            self._register_node(lookup, node, node_type)  # WHY: per-node work extracted to keep loop small.
        return lookup

    def _register_node(  # WHY: extracts the named/position check so _build_node_lookup stays flat.
        self,
        lookup: dict[str, dict[str, Any]],
        node: dict[str, Any],
        node_type: str,
    ) -> None:
        """Insert node into lookup if it has both a name and a position."""
        node_name = node.get("name", "")  # WHY: unnamed nodes cannot be edge targets.
        position = node.get("position", {})  # WHY: skip nodes without spatial data.
        if not (node_name and position):  # WHY: guard-clause exits when either piece is missing.
            return
        lookup[node_name] = position  # WHY: register for edge endpoint resolution.
        self.logger.debug(  # WHY: verbose per-node trace for map debugging sessions.
            "%s node '%s': x=%s, y=%s, edges=%s",
            node_type,
            node_name,
            position.get("x"),
            position.get("y"),
            node.get("edges", {}),
        )

    def _add_edge_segments(  # WHY: draw one scatter trace per node->edge->target relationship.
        self,
        fig: go.Figure,
        nodes: list[dict[str, Any]],
        node_lookup: dict[str, dict[str, Any]],
        style: _LayerStyle,
    ) -> None:
        """Add line segments based on node edge relationships."""
        for node in nodes:  # WHY: single top-level loop keeps CC at 3.
            self._add_node_edges(fig, node, node_lookup, style)  # WHY: per-node fan-out extracted below.

    def _add_node_edges(  # WHY: draw all outbound edges for one node; keeps _add_edge_segments flat.
        self,
        fig: go.Figure,
        node: dict[str, Any],
        node_lookup: dict[str, dict[str, Any]],
        style: _LayerStyle,
    ) -> None:
        """Add scatter traces for every resolvable outbound edge of ``node``."""
        node_pos = node.get("position", {})  # WHY: source coordinate for each segment.
        edges = node.get("edges", {})  # WHY: mapping of edge-name -> edge kind.
        if not node_pos or not edges:  # WHY: guard-clause skips isolated or unplaced nodes.
            return
        for edge_name in edges.keys():  # WHY: iterate edge targets by name.
            target_pos = node_lookup.get(edge_name)  # WHY: resolve target via prebuilt lookup.
            if target_pos is None:  # WHY: skip unresolved neighbors (legacy behavior).
                continue
            fig.add_trace(self._segment_trace(node_pos, target_pos, style))  # WHY: emit segment.

    # ------------------------------------------------------------------
    # Zone rendering helpers
    # ------------------------------------------------------------------
    def _add_single_zone(  # WHY: renders one polygon + label for a zone dict.
        self,
        fig: go.Figure,
        index: int,
        zone: dict[str, Any],
    ) -> None:
        """Render one polygon+label for a zone dict; skip if too few vertices."""
        zone_name = zone.get("name", f"Zone {index + 1}")  # WHY: fallback name preserves legacy labels.
        vertices = zone.get("vertices", [])  # WHY: polygon geometry source.
        self.logger.debug("Zone '%s': %s vertices - %s", zone_name, len(vertices), vertices)  # WHY: trace.
        if len(vertices) < _ZONE_MIN_VERTICES:  # WHY: guard-clause enforces triangle-or-larger polygons.
            self.logger.warning("Zone '%s' has insufficient vertices: %s", zone_name, len(vertices))
            return
        xs, ys = self._closed_polygon_xy(vertices)  # WHY: extract + close polygon coordinates.
        fill_color = _ZONE_FILL_COLORS[index % len(_ZONE_FILL_COLORS)]  # WHY: cycle palette.
        border_color = fill_color.replace(_FILL_ALPHA_TOKEN, _BORDER_ALPHA_TOKEN)  # WHY: darker hue.
        fig.add_trace(self._zone_polygon_trace(zone_name, xs, ys, fill_color, border_color))
        fig.add_annotation(**self._zone_label_kwargs(zone_name, min(xs), min(ys), border_color))

    @staticmethod
    def _closed_polygon_xy(  # WHY: extract xy lists and close polygon by repeating first vertex.
        vertices: list[dict[str, Any]],
    ) -> tuple[list[float], list[float]]:
        """Return (xs, ys) with the first vertex appended to close the polygon."""
        xs = [vertex.get("x", 0) for vertex in vertices]  # WHY: list comprehension avoids explicit loop.
        ys = [vertex.get("y", 0) for vertex in vertices]  # WHY: paired list comprehension for y coords.
        xs.append(xs[0])  # WHY: repeat first vertex so Plotly closes the polygon.
        ys.append(ys[0])  # WHY: paired closure for y coords.
        return xs, ys

    # ------------------------------------------------------------------
    # Trace + annotation factories (static, no instance state)
    # ------------------------------------------------------------------
    @staticmethod
    def _segment_trace(  # WHY: uniform scatter trace for one edge segment.
        src: dict[str, Any],
        dst: dict[str, Any],
        style: _LayerStyle,
    ) -> go.Scatter:
        """Return scatter trace connecting two node positions."""
        return go.Scatter(  # WHY: single Plotly primitive shared by walls + wayfinding.
            x=[src.get("x", 0), dst.get("x", 0)],
            y=[src.get("y", 0), dst.get("y", 0)],
            name=style.name,
            line=dict(**_line_kwargs(style)),
            visible=True,
            showlegend=False,
            hoverinfo="skip",
            **_scatter_extras(style),
        )

    @staticmethod
    def _legend_trace(style: _LayerStyle) -> go.Scatter:  # WHY: single hidden trace exposes legend entry.
        """Return legend-only scatter trace for ``style``."""
        return go.Scatter(  # WHY: x/y=None placeholders keep entry invisible while listing legend.
            x=[None],
            y=[None],
            name=style.name,
            line=dict(**_line_kwargs(style)),
            visible=True,
            showlegend=True,
            **_scatter_extras(style),
        )

    @staticmethod
    def _zone_polygon_trace(  # WHY: filled polygon scatter with hovertext.
        name: str,
        xs: list[float],
        ys: list[float],
        fill: str,
        border: str,
    ) -> go.Scatter:
        """Return zone polygon trace with border+fill styling."""
        return go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            name=f"Zone: {name}",
            line=dict(color=border, width=_ZONE_BORDER_WIDTH, dash=_ZONE_BORDER_DASH),
            fill="toself",
            fillcolor=fill,
            opacity=1.0,
            visible=True,
            showlegend=True,
            hovertext=f"Zone: {name}",
            hoverinfo="text",
        )

    @staticmethod
    def _zone_label_kwargs(  # WHY: annotation kwargs for zone label overlay.
        name: str,
        min_x: float,
        min_y: float,
        border: str,
    ) -> dict[str, Any]:
        """Return add_annotation kwargs positioning the zone label."""
        return dict(  # WHY: dict returned so callers can splat into fig.add_annotation.
            x=min_x + _ZONE_LABEL_OFFSET,
            y=min_y + _ZONE_LABEL_OFFSET,
            text=f"<b>{name}</b>",
            showarrow=False,
            font=dict(
                size=_ZONE_LABEL_FONT_SIZE,
                color=_ZONE_LABEL_FONT_COLOR,
                family=_ZONE_LABEL_FONT_FAMILY,
            ),
            bgcolor=border.replace(_BORDER_ALPHA_TOKEN, _LABEL_BG_ALPHA_TOKEN),
            bordercolor=_ZONE_LABEL_BORDER_COLOR,
            borderwidth=_ZONE_LABEL_BORDER_WIDTH,
            borderpad=_ZONE_LABEL_BORDER_PAD,
            xanchor="left",
            yanchor="top",
            name="Zone Label",
        )
