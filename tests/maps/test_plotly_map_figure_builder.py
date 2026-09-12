"""Unit tests for PlotlyMapFigureBuilder."""

import logging

import plotly.graph_objects as go

from src.maps.plotly_map_figure_builder import PlotlyMapFigureBuilder


def _wall_map_data() -> dict:
    """Create map payload containing wall path nodes/edges."""
    return {
        "wall_path": {
            "nodes": [
                {"name": "A", "position": {"x": 0, "y": 0}, "edges": {"B": "wall"}},
                {"name": "B", "position": {"x": 10, "y": 10}, "edges": {}},
            ]
        }
    }


def _wayfinding_map_data() -> dict:
    """Create map payload containing wayfinding nodes/edges."""
    return {
        "wayfinding_path": {
            "nodes": [
                {"name": "P0", "position": {"x": 1, "y": 1}, "edges": {"P1": "path"}},
                {"name": "P1", "position": {"x": 5, "y": 7}, "edges": {}},
            ]
        }
    }


def test_add_walls_adds_segment_and_legend() -> None:
    """Walls builder adds one segment trace and one legend trace."""
    fig = go.Figure()
    builder = PlotlyMapFigureBuilder(logger=logging.getLogger("test"))

    builder.add_walls(fig, _wall_map_data())

    assert len(fig.data) == 2
    assert fig.data[0].name == "Walls"
    assert fig.data[1].name == "Walls"
    assert fig.data[1].showlegend is True


def test_add_wayfinding_adds_segment_and_legend() -> None:
    """Wayfinding builder adds one segment trace and one legend trace."""
    fig = go.Figure()
    builder = PlotlyMapFigureBuilder(logger=logging.getLogger("test"))

    builder.add_wayfinding(fig, _wayfinding_map_data())

    assert len(fig.data) == 2
    assert fig.data[0].name == "Wayfinding"
    assert fig.data[1].name == "Wayfinding"
    assert fig.data[1].showlegend is True


def test_add_zones_adds_polygon_and_annotation() -> None:
    """Zones builder adds a zone trace and corresponding label annotation."""
    fig = go.Figure()
    builder = PlotlyMapFigureBuilder(logger=logging.getLogger("test"))
    zones = [{"name": "Zone A", "vertices": [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}]}]

    builder.add_zones(fig, zones)

    assert len(fig.data) == 1
    assert fig.data[0].name == "Zone: Zone A"
    assert fig.layout.annotations is not None
    assert len(fig.layout.annotations) == 1


def test_add_zones_handles_empty_input() -> None:
    """Zones builder leaves figure unchanged for empty zone input."""
    fig = go.Figure()
    builder = PlotlyMapFigureBuilder(logger=logging.getLogger("test"))

    builder.add_zones(fig, [])

    assert len(fig.data) == 0


def test_add_walls_no_path_no_changes() -> None:
    """Walls builder leaves figure unchanged when wall_path is missing."""
    fig = go.Figure()
    builder = PlotlyMapFigureBuilder(logger=logging.getLogger("test"))

    builder.add_walls(fig, {})

    assert len(fig.data) == 0
