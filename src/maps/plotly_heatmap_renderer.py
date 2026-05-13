"""RF coverage heatmap rendering helpers for Plotly map viewer."""

from __future__ import annotations

import logging
from typing import Any

import plotly.graph_objects as go


class PlotlyCoverageHeatmapRenderer:
    """Render Mist RF coverage API payloads into Plotly heatmap traces."""

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize renderer with optional logger."""
        self.logger = logger or logging.getLogger(__name__)

    def build_heatmap_trace(
        self,
        coverage_data: dict[str, Any] | None,
        ppm: float,
        map_width: int,
        map_height: int,
    ) -> go.Heatmap | None:
        """Create RF coverage heatmap trace from Mist coverage payload."""
        if not coverage_data:
            self.logger.info("No RF coverage data available")
            return None

        results = coverage_data.get("results", [])
        if not results:
            self.logger.warning("Coverage data received but no results")
            return None

        self.logger.info("Processing RF coverage data - %s grid points", len(results))
        result_def = coverage_data.get("result_def", [])
        gridsize_meters = coverage_data.get("gridsize", 1)
        self.logger.debug("Coverage result_def: %s", result_def)
        self.logger.debug("Coverage gridsize: %s meters, PPM: %s", gridsize_meters, ppm)

        x_idx, y_idx, max_rssi_idx, avg_rssi_idx = self._resolve_indices(result_def)
        grid_data = self._build_grid_data(results, x_idx, y_idx, max_rssi_idx, avg_rssi_idx, ppm)

        if not grid_data:
            self.logger.warning("No valid coverage grid data to visualize")
            return None

        all_rssi_values = [value for value in grid_data.values() if value is not None]
        min_rssi = min(all_rssi_values) if all_rssi_values else -100
        max_rssi = max(all_rssi_values) if all_rssi_values else -40

        unique_x = sorted({x for x, _ in grid_data.keys()})
        unique_y = sorted({y for _, y in grid_data.keys()})

        self._log_alignment(map_width, map_height, ppm, unique_x, unique_y, grid_data)
        z_matrix = self._build_z_matrix(unique_x, unique_y, grid_data)

        trace = go.Heatmap(
            x=unique_x,
            y=unique_y,
            z=z_matrix,
            colorscale=self._colorscale(),
            zmin=min_rssi,
            zmax=max_rssi,
            opacity=0.5,
            name="RF Coverage",
            hovertemplate="X: %{x}<br>Y: %{y}<br>RSSI: %{z} dBm<extra></extra>",
            visible=False,
            showscale=True,
            colorbar=dict(
                title=dict(text="RSSI (dBm)", side="right", font=dict(size=12, color="white")),
                thickness=20,
                len=0.5,
                y=0.95,
                yanchor="top",
                x=1.02,
                tickfont=dict(size=10, color="white"),
                tickmode="linear",
                tick0=min_rssi,
                dtick=(max_rssi - min_rssi) / 5,
                outlinewidth=1,
                outlinecolor="white",
            ),
            connectgaps=True,
            zsmooth="best",
        )

        self.logger.info(
            "Added RF Coverage heatmap: %s cells (%sm grid) with auto-scaled colors (%s to %s dBm)",
            len(grid_data),
            gridsize_meters,
            min_rssi,
            max_rssi,
        )
        return trace

    def _resolve_indices(self, result_def: list[str]) -> tuple[int, int, int, int]:
        """Resolve coverage field indices with safe fallback."""
        try:
            return (
                result_def.index("x"),
                result_def.index("y"),
                result_def.index("max_rssi"),
                result_def.index("avg_rssi"),
            )
        except ValueError as error:
            self.logger.error("Coverage data missing expected fields: %s", error)
            return 0, 1, 4, 5

    def _build_grid_data(
        self,
        results: list[list[Any]],
        x_idx: int,
        y_idx: int,
        max_rssi_idx: int,
        avg_rssi_idx: int,
        ppm: float,
    ) -> dict[tuple[float, float], Any]:
        """Convert API meter-coordinate points to pixel-coordinate grid map."""
        grid_data: dict[tuple[float, float], Any] = {}
        for result in results:
            if len(result) <= max(x_idx, y_idx, max_rssi_idx, avg_rssi_idx):
                continue
            pixel_x = result[x_idx] * ppm
            pixel_y = result[y_idx] * ppm
            grid_data[(pixel_x, pixel_y)] = result[max_rssi_idx]
        return grid_data

    def _build_z_matrix(
        self,
        unique_x: list[float],
        unique_y: list[float],
        grid_data: dict[tuple[float, float], Any],
    ) -> list[list[Any]]:
        """Build z matrix with None for missing points to avoid fake interpolation values."""
        matrix: list[list[Any]] = []
        for y_value in unique_y:
            row: list[Any] = []
            for x_value in unique_x:
                row.append(grid_data.get((x_value, y_value), None))
            matrix.append(row)
        return matrix

    def _log_alignment(
        self,
        map_width: int,
        map_height: int,
        ppm: float,
        unique_x: list[float],
        unique_y: list[float],
        grid_data: dict[tuple[float, float], Any],
    ) -> None:
        """Log coordinate alignment diagnostics for debugging coverage placement."""
        self.logger.info("HEATMAP DEBUG - Map dimensions: %sx%s pixels, PPM: %s", map_width, map_height, ppm)
        self.logger.info(
            "HEATMAP DEBUG - Coverage X range: %.1f to %.1f pixels (from %.1fm to %.1fm)",
            min(unique_x),
            max(unique_x),
            min(unique_x) / ppm,
            max(unique_x) / ppm,
        )
        self.logger.info(
            "HEATMAP DEBUG - Coverage Y range: %.1f to %.1f pixels (from %.1fm to %.1fm)",
            min(unique_y),
            max(unique_y),
            min(unique_y) / ppm,
            max(unique_y) / ppm,
        )
        self.logger.info(
            "HEATMAP DEBUG - Grid size: %s x %s = %s data points",
            len(unique_x),
            len(unique_y),
            len(grid_data),
        )

    def _colorscale(self) -> list[list[Any]]:
        """Return RF color scale (red strongest to blue weakest)."""
        return [
            [0.0, "rgb(0, 0, 255)"],
            [0.33, "rgb(0, 255, 0)"],
            [0.50, "rgb(255, 255, 0)"],
            [0.67, "rgb(255, 165, 0)"],
            [1.0, "rgb(255, 0, 0)"],
        ]
