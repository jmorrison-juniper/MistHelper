"""Serialization helpers for Plotly/Dash map viewer state stores."""

from __future__ import annotations  # WHY: PEP 563 postponed annotations for forward refs.

from dataclasses import dataclass  # WHY: frozen slotted dataclass groups wide map-config params.

_KEY_SITE_ID: str = "site_id"  # WHY: map-config payload key for scope site id.
_KEY_SITE_NAME: str = "site_name"  # WHY: map-config payload key for scope site display name.
_KEY_MAP_ID: str = "map_id"  # WHY: map-config payload key for current floor/map id.
_KEY_MAP_NAME: str = "map_name"  # WHY: map-config payload key for current floor/map display name.
_KEY_PPM: str = "ppm"  # WHY: map-config payload key for pixels-per-meter scaling factor.
_KEY_MAP_WIDTH: str = "map_width"  # WHY: map-config payload key for rendered map width in pixels.
_KEY_MAP_HEIGHT: str = "map_height"  # WHY: map-config payload key for rendered map height in pixels.

_KEY_ID: str = "id"  # WHY: canonical primary-key attribute name in Mist API records.
_KEY_NAME: str = "name"  # WHY: canonical display-name attribute name in Mist API records.
_KEY_LABEL: str = "label"  # WHY: dcc.Dropdown option label field.
_KEY_VALUE: str = "value"  # WHY: dcc.Dropdown option value field.

_KEY_ZONE_ID: str = "zone_id"  # WHY: selected-zone-store payload key for zone id.
_KEY_ZONE_NAME: str = "zone_name"  # WHY: selected-zone-store payload key for zone display name.

_KEY_CLIENT_LAST_REFRESH: str = "client_last_refresh"  # WHY: refresh-times key for wireless client tick.
_KEY_COVERAGE_LAST_REFRESH: str = "coverage_last_refresh"  # WHY: refresh-times key for coverage-heatmap tick.

_KEY_TRIGGER: str = "trigger"  # WHY: cache-bust-store payload key incremented on clone/delete reload.

_DEFAULT_TRIGGER: int = 0  # WHY: initial cache-bust value before any reload event.
_DEFAULT_REFRESH_TIME: int = 0  # WHY: initial refresh-tick value before any interval fires.


@dataclass(frozen=True, slots=True)
class MapConfigParams:
    """Immutable bundle of the seven identity fields for ``map-config-store``."""

    site_id: str  # WHY: scope site id passed through to store payload.
    site_name: str  # WHY: scope site display name for UI badges.
    map_id: str  # WHY: current map/floor id used by JS overlays.
    map_name: str  # WHY: current map/floor display name for header.
    ppm: float  # WHY: pixels-per-meter scale used by coordinate math.
    map_width: int  # WHY: rendered map width in pixels for viewport calc.
    map_height: int  # WHY: rendered map height in pixels for viewport calc.


class PlotlyMapDataSerializer:
    """Build normalized payloads for Dash dcc.Store and dropdown options."""

    @staticmethod
    def build_map_config(params: MapConfigParams) -> dict:  # WHY: 1-arg dataclass fix (STRUCT-PARAMS).
        """Create canonical map-config-store payload from an immutable params bundle."""
        return {
            _KEY_SITE_ID: params.site_id,  # WHY: propagate scope site id to store.
            _KEY_SITE_NAME: params.site_name,  # WHY: propagate scope site display name.
            _KEY_MAP_ID: params.map_id,  # WHY: propagate current map id.
            _KEY_MAP_NAME: params.map_name,  # WHY: propagate current map display name.
            _KEY_PPM: params.ppm,  # WHY: propagate pixels-per-meter scale.
            _KEY_MAP_WIDTH: params.map_width,  # WHY: propagate rendered map width.
            _KEY_MAP_HEIGHT: params.map_height,  # WHY: propagate rendered map height.
        }

    @staticmethod
    def build_named_items(items: list | None, default_name: str) -> list[dict]:
        """Build [{id,name}] list from API records with safe defaults."""
        records = items or []  # WHY: coerce None to empty list for safe iteration.
        return [  # WHY: return normalized list of id+name dicts for downstream stores.
            # WHY: default_name is fallback when API record omits the "name" key.
            {_KEY_ID: item.get(_KEY_ID), _KEY_NAME: item.get(_KEY_NAME, default_name)}
            for item in records
        ]

    @staticmethod
    def build_dropdown_options(items: list | None, default_name: str) -> list[dict]:
        """Build [{label,value}] dropdown options from API records."""
        records = items or []  # WHY: coerce None to empty list for safe iteration.
        return [  # WHY: return dcc.Dropdown-compatible options list.
            # WHY: map API "name" -> Dash "label" and "id" -> "value".
            {_KEY_LABEL: item.get(_KEY_NAME, default_name), _KEY_VALUE: item.get(_KEY_ID)}
            for item in records
        ]

    @staticmethod
    def build_selected_zone_store(zone_id: str | None = None, zone_name: str | None = None) -> dict:
        """Create selected-zone-store payload."""
        return {_KEY_ZONE_ID: zone_id, _KEY_ZONE_NAME: zone_name}  # WHY: nullable zone selection payload.

    @staticmethod
    def build_refresh_times_store(
        client_last_refresh: int = _DEFAULT_REFRESH_TIME,
        coverage_last_refresh: int = _DEFAULT_REFRESH_TIME,
    ) -> dict:
        """Create refresh-times-store payload."""
        return {  # WHY: dcc.Store payload tracking last-refresh ticks per interval.
            _KEY_CLIENT_LAST_REFRESH: client_last_refresh,  # WHY: wireless client interval tick.
            _KEY_COVERAGE_LAST_REFRESH: coverage_last_refresh,  # WHY: coverage heatmap interval tick.
        }

    @staticmethod
    def build_cache_bust_store(trigger: int = _DEFAULT_TRIGGER) -> dict:
        """Create cache-bust-store payload."""
        return {_KEY_TRIGGER: trigger}  # WHY: single-field trigger payload.

    @staticmethod
    def increment_cache_bust(data: dict | None) -> dict:
        """Increment cache-bust trigger payload safely."""
        current = data.get(_KEY_TRIGGER, _DEFAULT_TRIGGER) if data else _DEFAULT_TRIGGER  # WHY: None-safe read.
        return {_KEY_TRIGGER: current + 1}  # WHY: bump trigger to invalidate cached view.
