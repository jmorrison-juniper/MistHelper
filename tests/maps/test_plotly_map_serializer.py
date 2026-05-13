"""Unit tests for PlotlyMapDataSerializer."""

from src.maps.plotly_map_serializer import PlotlyMapDataSerializer


def test_build_map_config() -> None:
    """Map config payload contains expected keys and values."""
    payload = PlotlyMapDataSerializer.build_map_config(
        site_id="s1",
        site_name="Site A",
        map_id="m1",
        map_name="Floor 1",
        ppm=12.5,
        map_width=1000,
        map_height=600,
    )

    assert payload == {
        "site_id": "s1",
        "site_name": "Site A",
        "map_id": "m1",
        "map_name": "Floor 1",
        "ppm": 12.5,
        "map_width": 1000,
        "map_height": 600,
    }


def test_build_named_items_defaults() -> None:
    """Named item serialization applies default names when missing."""
    items = [{"id": "a", "name": "Alpha"}, {"id": "b"}]
    payload = PlotlyMapDataSerializer.build_named_items(items, default_name="Unnamed")
    assert payload == [{"id": "a", "name": "Alpha"}, {"id": "b", "name": "Unnamed"}]


def test_build_dropdown_options_defaults() -> None:
    """Dropdown option serialization applies labels and values correctly."""
    items = [{"id": "a", "name": "Alpha"}, {"id": "b"}]
    payload = PlotlyMapDataSerializer.build_dropdown_options(items, default_name="Unnamed")
    assert payload == [{"label": "Alpha", "value": "a"}, {"label": "Unnamed", "value": "b"}]


def test_store_builders() -> None:
    """Simple store builders return expected defaults."""
    assert PlotlyMapDataSerializer.build_selected_zone_store() == {"zone_id": None, "zone_name": None}
    assert PlotlyMapDataSerializer.build_refresh_times_store() == {
        "client_last_refresh": 0,
        "coverage_last_refresh": 0,
    }
    assert PlotlyMapDataSerializer.build_cache_bust_store() == {"trigger": 0}


def test_increment_cache_bust() -> None:
    """Cache bust counter increments safely with or without input."""
    assert PlotlyMapDataSerializer.increment_cache_bust(None) == {"trigger": 1}
    assert PlotlyMapDataSerializer.increment_cache_bust({"trigger": 7}) == {"trigger": 8}
