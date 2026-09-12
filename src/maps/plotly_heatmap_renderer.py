"""RF coverage heatmap rendering helpers for Plotly map viewer."""  # WHY: module docstring

from __future__ import annotations  # WHY: postpone annotation eval for | union syntax on 3.9+

import logging  # WHY: emit progress + diagnostic messages during heatmap build
from dataclasses import dataclass  # WHY: bundle >5 grid parameters into frozen slotted record
from typing import Any  # WHY: heatmap cell values may be int/float/None from mixed Mist payload

import plotly.graph_objects as go  # WHY: Heatmap trace constructor comes from Plotly graph objects

_DEFAULT_INDICES: tuple[int, int, int, int] = (0, 1, 4, 5)  # WHY: fallback x/y/max/avg column order
_FALLBACK_MIN_RSSI: int = -100  # WHY: sentinel min when grid contains only None values
_FALLBACK_MAX_RSSI: int = -40  # WHY: sentinel max when grid contains only None values
_COLORBAR_TICK_STEPS: int = 5  # WHY: split RSSI legend into five even ticks for readability
_HEATMAP_OPACITY: float = 0.5  # WHY: keep floor plan visible beneath translucent coverage overlay
_HEATMAP_NAME: str = "RF Coverage"  # WHY: legend label surfaced in Plotly control panel
_HOVER_TEMPLATE: str = "X: %{x}<br>Y: %{y}<br>RSSI: %{z} dBm<extra></extra>"  # WHY: hover text
_INDEX_FIELDS: tuple[str, ...] = ("x", "y", "max_rssi", "avg_rssi")  # WHY: expected result_def keys
_AXIS_LABELS: tuple[str, ...] = ("X", "Y")  # WHY: axis names emitted in alignment log output
_EMPTY_GRID_MSG: str = "No valid coverage grid data to visualize"  # WHY: dedup log string constant
_ALIGN_HEADER: str = "HEATMAP DEBUG - Map dimensions: %sx%s pixels, PPM: %s"  # WHY: log fmt string
_ALIGN_RANGE: str = (  # WHY: log format for pixel/meter range diagnostic
    "HEATMAP DEBUG - Coverage %s range: %.1f to %.1f pixels (from %.1fm to %.1fm)"
)
_ALIGN_SIZE: str = "HEATMAP DEBUG - Grid size: %s x %s = %s data points"  # WHY: cell count log fmt
_BUILD_SUMMARY: str = (  # WHY: final audit line format for post-hoc log review
    "Added RF Coverage heatmap: %s cells (%sm grid) with auto-scaled colors (%s to %s dBm)"
)
_COLORBAR_BASE: dict[str, Any] = {  # WHY: shared colorbar layout, cloned per trace with tick math
    "title": {"text": "RSSI (dBm)", "side": "right", "font": {"size": 12, "color": "white"}},
    "thickness": 20,
    "len": 0.5,
    "y": 0.95,
    "yanchor": "top",
    "x": 1.02,
    "tickfont": {"size": 10, "color": "white"},
    "tickmode": "linear",
    "outlinewidth": 1,
    "outlinecolor": "white",
}
_RF_COLORSCALE: tuple[tuple[float, str], ...] = (  # WHY: RF strength gradient blue->green->red
    (0.0, "rgb(0, 0, 255)"),
    (0.33, "rgb(0, 255, 0)"),
    (0.50, "rgb(255, 255, 0)"),
    (0.67, "rgb(255, 165, 0)"),
    (1.0, "rgb(255, 0, 0)"),
)
_STATIC_TRACE_KW: dict[str, Any] = {  # WHY: kwargs identical across every render, spread on build
    "opacity": _HEATMAP_OPACITY,
    "name": _HEATMAP_NAME,
    "hovertemplate": _HOVER_TEMPLATE,
    "visible": False,
    "showscale": True,
    "connectgaps": True,
    "zsmooth": "best",
}


@dataclass(frozen=True, slots=True)
class _GridIndices:  # WHY: typed record replaces four scalar params into a single value object
    """Column offsets identifying RSSI fields inside a Mist coverage result row."""

    x: int  # WHY: index of the meter-space x coordinate within each result row
    y: int  # WHY: index of the meter-space y coordinate within each result row
    max_rssi: int  # WHY: index of peak RSSI signal (used as cell colour value)
    avg_rssi: int  # WHY: index of average RSSI signal (reserved for future averaging modes)

    def max_offset(self) -> int:  # WHY: expose max used offset for row-length bounds check
        """Return the highest column offset used, for bounds checks on short rows."""
        return max(self.x, self.y, self.max_rssi, self.avg_rssi)  # WHY: any shorter row is invalid


@dataclass(frozen=True, slots=True)
class _GridBuildRequest:  # WHY: bundle bounds/index inputs so builder stays under param cap
    """Immutable bundle of inputs required to build the pixel-space RSSI grid."""

    results: list[list[Any]]  # WHY: raw coverage rows from Mist API result array
    indices: _GridIndices  # WHY: precomputed column layout, avoids re-resolving inside loop
    ppm: float  # WHY: pixels-per-meter scale factor applied to convert coordinates


@dataclass(frozen=True, slots=True)
class _AlignmentContext:  # WHY: alignment logger fields grouped into a single record parameter
    """Snapshot of coordinate math needed to log heatmap-to-map alignment diagnostics."""

    map_width: int  # WHY: floor plan width in pixels for alignment log context
    map_height: int  # WHY: floor plan height in pixels for alignment log context
    ppm: float  # WHY: reverse-project pixels back into meters for debug output
    unique_x: list[float]  # WHY: sorted pixel x-axis ticks in the heatmap grid
    unique_y: list[float]  # WHY: sorted pixel y-axis ticks in the heatmap grid
    grid_data: dict[tuple[float, float], Any]  # WHY: cell count reported in the diagnostic summary


class PlotlyCoverageHeatmapRenderer:  # WHY: public renderer entry point for map viewer callers
    """Render Mist RF coverage API payloads into Plotly heatmap traces."""

    def __init__(self, logger: logging.Logger | None = None) -> None:  # WHY: optional logger inject
        """Initialize renderer with optional logger."""
        self.logger = logger or logging.getLogger(__name__)  # WHY: fall back to module logger

    def build_heatmap_trace(  # WHY: single public API used by _viewer_launch and maps_manager
        self,
        coverage_data: dict[str, Any] | None,
        ppm: float,
        map_width: int,
        map_height: int,
    ) -> go.Heatmap | None:
        """Create RF coverage heatmap trace from Mist coverage payload."""
        results = self._extract_results(coverage_data)  # WHY: guard-clause payload validation
        if not results or coverage_data is None:  # WHY: unusable payload short-circuits to caller
            return None  # WHY: nothing renderable, log already emitted inside _extract_results
        grid_data = self._prepare_grid(results, coverage_data, ppm)  # WHY: pixel-space RSSI mapping
        if not grid_data:  # WHY: no valid grid cells built from the rows
            self.logger.warning(_EMPTY_GRID_MSG)  # WHY: surface data gap to log stream
            return None  # WHY: skip trace creation when nothing to render
        return self._assemble_trace(grid_data, coverage_data, ppm, map_width, map_height)

    def _extract_results(  # WHY: normalize payload -> results list or None with logged reason
        self, coverage_data: dict[str, Any] | None
    ) -> list[list[Any]] | None:
        """Return results array or None with a logged reason when payload is unusable."""
        if not coverage_data:  # WHY: benign empty payload path
            self.logger.info("No RF coverage data available")  # WHY: informational, not an error
            return None  # WHY: signal caller to short-circuit
        results: list[list[Any]] = coverage_data.get("results", [])  # WHY: Mist rows live here
        if not results:  # WHY: envelope present but empty
            self.logger.warning("Coverage data received but no results")  # WHY: payload shape issue
            return None  # WHY: nothing to plot despite envelope being present
        self.logger.info("Processing RF coverage data - %s grid points", len(results))  # WHY: audit
        return results  # WHY: valid rows for downstream conversion

    def _prepare_grid(  # WHY: keep index resolution + grid build together for callers
        self,
        results: list[list[Any]],
        coverage_data: dict[str, Any],
        ppm: float,
    ) -> dict[tuple[float, float], Any]:
        """Resolve column indices then build the pixel-space RSSI grid map."""
        result_def: list[str] = coverage_data.get("result_def", [])  # WHY: schema headers list
        gridsize_meters = coverage_data.get("gridsize", 1)  # WHY: log context, not build math
        self.logger.debug("Coverage result_def: %s", result_def)  # WHY: help debug schema drift
        self.logger.debug("Coverage gridsize: %s meters, PPM: %s", gridsize_meters, ppm)  # WHY: log
        indices = self._resolve_indices(result_def)  # WHY: map field names to row offsets
        request = _GridBuildRequest(results=results, indices=indices, ppm=ppm)  # WHY: bundle inputs
        return self._build_grid_data(request)  # WHY: hand off to <=5-param helper

    def _assemble_trace(  # WHY: orchestrate axes/logging/trace under the STRUCT-LENGTH cap
        self,
        grid_data: dict[tuple[float, float], Any],
        coverage_data: dict[str, Any],
        ppm: float,
        map_width: int,
        map_height: int,
    ) -> go.Heatmap:
        """Compose axes, bounds, alignment logs, z matrix, and final Heatmap trace."""
        unique_x = sorted({x for x, _ in grid_data.keys()})  # WHY: axis ticks derive from grid keys
        unique_y = sorted({y for _, y in grid_data.keys()})  # WHY: sorted for monotonic axis
        min_rssi, max_rssi = self._rssi_bounds(grid_data)  # WHY: colorbar range from live samples
        context = _AlignmentContext(map_width, map_height, ppm, unique_x, unique_y, grid_data)
        self._log_alignment(context)  # WHY: emit alignment diagnostics before trace assembly
        z_matrix = self._build_z_matrix(unique_x, unique_y, grid_data)  # WHY: dense 2D grid
        trace = self._make_trace(unique_x, unique_y, z_matrix, min_rssi, max_rssi)  # WHY: assembled
        gridsize_meters = coverage_data.get("gridsize", 1)  # WHY: reused only for the summary log
        self.logger.info(  # WHY: single audit line summarising final trace shape
            _BUILD_SUMMARY, len(grid_data), gridsize_meters, min_rssi, max_rssi
        )
        return trace  # WHY: caller adds this trace to a Plotly figure

    @staticmethod
    def _rssi_bounds(  # WHY: derive display range or fall back to sentinel constants
        grid_data: dict[tuple[float, float], Any],
    ) -> tuple[float, float]:
        """Return (min, max) RSSI values across the grid, using sentinels when empty."""
        values = [value for value in grid_data.values() if value is not None]  # WHY: skip gaps
        if not values:  # WHY: no live samples available in the grid
            return _FALLBACK_MIN_RSSI, _FALLBACK_MAX_RSSI  # WHY: safe defaults
        return min(values), max(values)  # WHY: actual observed range drives the colorbar

    def _resolve_indices(self, result_def: list[str]) -> _GridIndices:  # WHY: schema mapper
        """Resolve coverage field indices with safe fallback."""
        try:
            offsets = tuple(result_def.index(name) for name in _INDEX_FIELDS)  # WHY: schema lookup
        except ValueError as error:  # WHY: schema drift, expected fields missing
            self.logger.error("Coverage data missing expected fields: %s", error)  # WHY: warn once
            offsets = _DEFAULT_INDICES  # WHY: fall back to documented column order
        return _GridIndices(*offsets)  # WHY: return typed record for downstream helpers

    @staticmethod
    def _build_grid_data(  # WHY: convert meter rows to pixel-keyed grid dict
        request: _GridBuildRequest,
    ) -> dict[tuple[float, float], Any]:
        """Convert API meter-coordinate points to pixel-coordinate grid map."""
        grid_data: dict[tuple[float, float], Any] = {}  # WHY: (px_x, px_y) -> max_rssi mapping
        indices = request.indices  # WHY: local alias for tight loop readability
        min_row_length = indices.max_offset() + 1  # WHY: rows shorter than this cannot be indexed
        for result in request.results:  # WHY: iterate coverage rows once
            if len(result) < min_row_length:  # WHY: skip malformed rows defensively
                continue  # WHY: cannot safely index this row
            pixel_x = result[indices.x] * request.ppm  # WHY: meters -> pixels for map alignment
            pixel_y = result[indices.y] * request.ppm  # WHY: meters -> pixels for map alignment
            grid_data[(pixel_x, pixel_y)] = result[indices.max_rssi]  # WHY: peak signal per cell
        return grid_data  # WHY: dense dict keyed by pixel coordinates

    @staticmethod
    def _build_z_matrix(  # WHY: gap-preserving dense matrix builder for Plotly Heatmap
        unique_x: list[float],
        unique_y: list[float],
        grid_data: dict[tuple[float, float], Any],
    ) -> list[list[Any]]:
        """Build z matrix with None for missing points to avoid fake interpolation values."""
        matrix: list[list[Any]] = []  # WHY: row-major 2D grid for Plotly Heatmap
        for y_value in unique_y:  # WHY: iterate rows in sorted y order
            row = [grid_data.get((x_value, y_value)) for x_value in unique_x]  # WHY: fill row
            matrix.append(row)  # WHY: preserve axis ordering for Plotly indexing
        return matrix  # WHY: dense matrix aligned with unique_x/unique_y axes

    def _log_alignment(self, context: _AlignmentContext) -> None:  # WHY: emit multi-line diag log
        """Log coordinate alignment diagnostics for debugging coverage placement."""
        self.logger.info(_ALIGN_HEADER, context.map_width, context.map_height, context.ppm)
        axes_ticks = (context.unique_x, context.unique_y)  # WHY: pair labels with tick lists
        for label, ticks in zip(_AXIS_LABELS, axes_ticks, strict=True):  # WHY: iterate X and Y
            lo_px, hi_px = min(ticks), max(ticks)  # WHY: precompute range for compact log call
            self.logger.info(_ALIGN_RANGE, label, lo_px, hi_px, lo_px / context.ppm, hi_px / context.ppm)
        self.logger.info(  # WHY: quick sanity count of the produced grid
            _ALIGN_SIZE, len(context.unique_x), len(context.unique_y), len(context.grid_data)
        )

    def _make_trace(  # WHY: build the fully configured Heatmap trace for Plotly
        self,
        unique_x: list[float],
        unique_y: list[float],
        z_matrix: list[list[Any]],
        min_rssi: float,
        max_rssi: float,
    ) -> go.Heatmap:
        """Build the fully configured Plotly Heatmap trace."""
        colorbar = self._colorbar(min_rssi, max_rssi)  # WHY: precompute colorbar with tick math
        return go.Heatmap(  # WHY: static kwargs spread from module dict to keep body compact
            x=unique_x,
            y=unique_y,
            z=z_matrix,
            colorscale=self._colorscale(),
            zmin=min_rssi,
            zmax=max_rssi,
            colorbar=colorbar,
            **_STATIC_TRACE_KW,
        )

    @staticmethod
    def _colorbar(min_rssi: float, max_rssi: float) -> dict[str, Any]:  # WHY: clone base + ticks
        """Return colorbar config dict matching the map viewer visual style."""
        tick_step = (max_rssi - min_rssi) / _COLORBAR_TICK_STEPS  # WHY: even spacing across range
        config: dict[str, Any] = dict(_COLORBAR_BASE)  # WHY: shallow copy so module dict stays pure
        config["tick0"] = min_rssi  # WHY: colorbar labels start at observed minimum
        config["dtick"] = tick_step  # WHY: labels spaced evenly across the observed range
        return config  # WHY: return dict consumed by go.Heatmap(colorbar=...)

    @staticmethod
    def _colorscale() -> list[list[Any]]:  # WHY: convert module tuple to Plotly's list-of-lists
        """Return RF color scale (red strongest to blue weakest)."""
        return [[stop, color] for stop, color in _RF_COLORSCALE]  # WHY: Plotly wants list[list]
