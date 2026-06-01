"""Figure-building helpers for Plotly map layers."""

from __future__ import annotations

import logging
from typing import Any

import plotly.graph_objects as go


class PlotlyMapFigureBuilder:
    """Add map layer traces/annotations to a Plotly figure."""

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize figure builder with optional logger."""
        self.logger = logger or logging.getLogger(__name__)

    def add_walls(self, fig: go.Figure, map_data: dict[str, Any]) -> None:
        """Add wall segment traces and legend trace to figure."""
        wall_path = map_data.get("wall_path")
        if not wall_path:
            return

        self.logger.debug("Wall path data structure: %s", wall_path)
        nodes = wall_path.get("nodes", [])
        if not nodes:
            return

        self.logger.info("Processing %s wall path nodes", len(nodes))
        node_lookup = self._build_node_lookup(nodes, "Wall")
        self._add_edge_segments(
            fig, nodes, node_lookup, layer_name="Walls", line_style={"color": "#ff3333", "width": 4}
        )
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                name="Walls",
                line=dict(color="#ff3333", width=4),
                visible=True,
                showlegend=True,
            )
        )

    def add_wayfinding(self, fig: go.Figure, map_data: dict[str, Any]) -> None:
        """Add wayfinding segment traces and legend trace to figure."""
        wayfinding_path = map_data.get("wayfinding_path")
        if not wayfinding_path:
            return

        self.logger.debug("Wayfinding path data structure: %s", wayfinding_path)
        nodes = wayfinding_path.get("nodes", [])
        if not nodes:
            return

        self.logger.info("Processing %s wayfinding path nodes", len(nodes))
        node_lookup = self._build_node_lookup(nodes, "Wayfinding")
        for node in nodes:
            node_pos = node.get("position", {})
            edges = node.get("edges", {})
            if not node_pos or not edges:
                continue
            for edge_name in edges.keys():
                if edge_name in node_lookup:
                    target_pos = node_lookup[edge_name]
                    fig.add_trace(
                        go.Scatter(
                            x=[node_pos.get("x", 0), target_pos.get("x", 0)],
                            y=[node_pos.get("y", 0), target_pos.get("y", 0)],
                            mode="lines+markers",
                            name="Wayfinding",
                            line=dict(color="#4488ff", width=3, dash="dash"),
                            marker=dict(size=8, color="#4488ff"),
                            visible=True,
                            showlegend=False,
                            hoverinfo="skip",
                        )
                    )

        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines+markers",
                name="Wayfinding",
                line=dict(color="#4488ff", width=3, dash="dash"),
                marker=dict(size=8, color="#4488ff"),
                visible=True,
                showlegend=True,
            )
        )

    def add_zones(self, fig: go.Figure, zones: list[dict[str, Any]]) -> None:
        """Add zone polygons and labels to figure."""
        if not zones:
            self.logger.info("No zones found on this map")
            return

        self.logger.info("Processing %s zones on this map", len(zones))
        zone_colors = [
            "rgba(255,165,0,0.2)",
            "rgba(0,255,255,0.2)",
            "rgba(255,0,255,0.2)",
            "rgba(255,255,0,0.2)",
            "rgba(0,255,0,0.2)",
            "rgba(128,0,255,0.2)",
        ]

        for index, zone in enumerate(zones):
            zone_name = zone.get("name", f"Zone {index + 1}")
            vertices = zone.get("vertices", [])
            self.logger.debug("Zone '%s': %s vertices - %s", zone_name, len(vertices), vertices)

            if not vertices or len(vertices) < 3:
                self.logger.warning("Zone '%s' has insufficient vertices: %s", zone_name, len(vertices))
                continue

            zone_x = [vertex.get("x", 0) for vertex in vertices]
            zone_y = [vertex.get("y", 0) for vertex in vertices]
            zone_x.append(zone_x[0])
            zone_y.append(zone_y[0])

            color = zone_colors[index % len(zone_colors)]
            border_color = color.replace("0.2", "0.8")
            fig.add_trace(
                go.Scatter(
                    x=zone_x,
                    y=zone_y,
                    mode="lines",
                    name=f"Zone: {zone_name}",
                    line=dict(color=border_color, width=2, dash="dot"),
                    fill="toself",
                    fillcolor=color,
                    opacity=1.0,
                    visible=True,
                    showlegend=True,
                    hovertext=f"Zone: {zone_name}",
                    hoverinfo="text",
                )
            )

            min_x = min(zone_x)
            min_y = min(zone_y)
            fig.add_annotation(
                x=min_x + 10,
                y=min_y + 10,
                text=f"<b>{zone_name}</b>",
                showarrow=False,
                font=dict(size=14, color="white", family="Arial Black"),
                bgcolor=border_color.replace("0.8", "0.9"),
                bordercolor="white",
                borderwidth=2,
                borderpad=4,
                xanchor="left",
                yanchor="top",
                name="Zone Label",
            )

    def _build_node_lookup(self, nodes: list[dict[str, Any]], node_type: str) -> dict[str, dict[str, Any]]:
        """Build lookup table of named nodes to positions."""
        lookup: dict[str, dict[str, Any]] = {}
        for node in nodes:
            node_name = node.get("name", "")
            position = node.get("position", {})
            if node_name and position:
                lookup[node_name] = position
                self.logger.debug(
                    "%s node '%s': x=%s, y=%s, edges=%s",
                    node_type,
                    node_name,
                    position.get("x"),
                    position.get("y"),
                    node.get("edges", {}),
                )
        return lookup

    def _add_edge_segments(
        self,
        fig: go.Figure,
        nodes: list[dict[str, Any]],
        node_lookup: dict[str, dict[str, Any]],
        layer_name: str,
        line_style: dict[str, Any],
    ) -> None:
        """Add line segments based on node edge relationships."""
        for node in nodes:
            node_pos = node.get("position", {})
            edges = node.get("edges", {})
            if not node_pos or not edges:
                continue
            for edge_name in edges.keys():
                if edge_name in node_lookup:
                    target_pos = node_lookup[edge_name]
                    fig.add_trace(
                        go.Scatter(
                            x=[node_pos.get("x", 0), target_pos.get("x", 0)],
                            y=[node_pos.get("y", 0), target_pos.get("y", 0)],
                            mode="lines",
                            name=layer_name,
                            line=dict(**line_style),
                            visible=True,
                            showlegend=False,
                            hoverinfo="skip",
                        )
                    )
