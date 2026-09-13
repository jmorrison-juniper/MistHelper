"""Unit tests for PlotlyCoverageHeatmapRenderer."""

import logging

import plotly.graph_objects as go

from src.maps.plotly_heatmap_renderer import PlotlyCoverageHeatmapRenderer


def _sample_coverage() -> dict:
    """Create minimal valid coverage payload."""
    return {
        "result_def": ["x", "y", "channel", "snr", "max_rssi", "avg_rssi"],
        "results": [
            [0.0, 0.0, 36, 25, -45, -50],
            [1.0, 0.0, 36, 20, -60, -65],
            [0.0, 1.0, 36, 18, -70, -72],
            [1.0, 1.0, 36, 16, -80, -82],
        ],
        "gridsize": 1,
    }


def test_build_heatmap_trace_none_data() -> None:
    """Renderer returns None when no coverage payload is provided."""
    renderer = PlotlyCoverageHeatmapRenderer(logger=logging.getLogger("test"))
    assert renderer.build_heatmap_trace(None, ppm=10, map_width=1000, map_height=500) is None


def test_build_heatmap_trace_empty_results() -> None:
    """Renderer returns None for empty coverage results."""
    renderer = PlotlyCoverageHeatmapRenderer(logger=logging.getLogger("test"))
    payload = {"result_def": ["x", "y"], "results": []}
    assert renderer.build_heatmap_trace(payload, ppm=10, map_width=1000, map_height=500) is None


def test_build_heatmap_trace_valid_payload() -> None:
    """Renderer returns a Plotly heatmap trace for valid payloads."""
    renderer = PlotlyCoverageHeatmapRenderer(logger=logging.getLogger("test"))
    trace = renderer.build_heatmap_trace(_sample_coverage(), ppm=10, map_width=1000, map_height=500)

    assert trace is not None
    assert isinstance(trace, go.Heatmap)
    assert trace.name == "RF Coverage"
    assert trace.visible is False


def test_build_heatmap_trace_value_ranges() -> None:
    """Rendered heatmap keeps expected RSSI range bounds from payload."""
    renderer = PlotlyCoverageHeatmapRenderer(logger=logging.getLogger("test"))
    trace = renderer.build_heatmap_trace(_sample_coverage(), ppm=10, map_width=1000, map_height=500)

    assert trace is not None
    assert trace.zmin == -80
    assert trace.zmax == -45


def test_build_heatmap_trace_fallback_indices() -> None:
    """Renderer tolerates missing expected fields by using fallback index mapping."""
    renderer = PlotlyCoverageHeatmapRenderer(logger=logging.getLogger("test"))
    payload = {
        "result_def": ["foo", "bar"],
        "results": [[0.0, 0.0, 36, 20, -55, -60]],
        "gridsize": 1,
    }

    trace = renderer.build_heatmap_trace(payload, ppm=10, map_width=1000, map_height=500)
    assert trace is not None
