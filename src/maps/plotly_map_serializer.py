"""Serialization helpers for Plotly/Dash map viewer state stores."""

from __future__ import annotations


class PlotlyMapDataSerializer:
    """Build normalized payloads for Dash dcc.Store and dropdown options."""

    @staticmethod
    def build_map_config(
        site_id: str,
        site_name: str,
        map_id: str,
        map_name: str,
        ppm: float,
        map_width: int,
        map_height: int,
    ) -> dict:
        """Create canonical map-config-store payload."""
        return {
            "site_id": site_id,
            "site_name": site_name,
            "map_id": map_id,
            "map_name": map_name,
            "ppm": ppm,
            "map_width": map_width,
            "map_height": map_height,
        }

    @staticmethod
    def build_named_items(items: list | None, default_name: str) -> list[dict]:
        """Build [{id,name}] list from API records with safe defaults."""
        records = items or []
        return [{"id": item.get("id"), "name": item.get("name", default_name)} for item in records]

    @staticmethod
    def build_dropdown_options(items: list | None, default_name: str) -> list[dict]:
        """Build [{label,value}] dropdown options from API records."""
        records = items or []
        return [{"label": item.get("name", default_name), "value": item.get("id")} for item in records]

    @staticmethod
    def build_selected_zone_store(zone_id: str | None = None, zone_name: str | None = None) -> dict:
        """Create selected-zone-store payload."""
        return {"zone_id": zone_id, "zone_name": zone_name}

    @staticmethod
    def build_refresh_times_store(client_last_refresh: int = 0, coverage_last_refresh: int = 0) -> dict:
        """Create refresh-times-store payload."""
        return {"client_last_refresh": client_last_refresh, "coverage_last_refresh": coverage_last_refresh}

    @staticmethod
    def build_cache_bust_store(trigger: int = 0) -> dict:
        """Create cache-bust-store payload."""
        return {"trigger": trigger}

    @staticmethod
    def increment_cache_bust(data: dict | None) -> dict:
        """Increment cache-bust trigger payload safely."""
        current = data.get("trigger", 0) if data else 0
        return {"trigger": current + 1}
