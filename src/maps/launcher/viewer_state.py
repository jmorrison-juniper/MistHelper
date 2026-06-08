"""Mutable state container shared by Plotly viewer callbacks.

The Dash callbacks that historically lived inside
:py:meth:`src.maps.maps_manager.MapsManager._launch_plotly_viewer`
captured many local variables via closure (``callback_manager``,
``devices``, ``zones``, ``clients``, ``ppm``, ``site_id``, ``map_id``,
``api_session_ref``, ...). To extract those callbacks into a class,
we collect the captured values onto this state object so each callback
method can read them via ``self._state.<field>``.

Wave A scope (current): only :attr:`callback_manager` is needed by the
five trivial callbacks moved in this wave. Subsequent waves should add
fields here as they extract callbacks needing additional context:

* **Wave B** -- zone/layer visibility callbacks: add ``zones`` and
  ``map_id`` so the zone-toggle callback can look up zone IDs.
* **Wave C** -- drawing tools and origin-set callbacks: add
  ``site_id``, ``map_id``, ``api_session_ref``, ``ppm``, plus a
  reference to ``MapsManager`` (or its ``_backup_map_geometry`` helper).
* **Wave D** -- live refresh callbacks: add ``devices``, ``clients``,
  and any refresh-helper bound methods needed.
* **Wave E** -- clone/delete/utilities callbacks: add ``all_sites``,
  ``all_maps``, and the ``MapsManager`` instance for cross-map ops.

Conventions for adding state fields:

1. Use the same name as the closure variable they replace, so reviewers
   can trace ``self._state.foo`` back to the original ``foo`` local.
2. Prefer immutable types (str, int, tuple) for read-only context and
   mutable list/dict only when a callback needs to update shared data.
3. Type-annotate every field; use ``TYPE_CHECKING`` imports for heavy
   modules (``mistapi``, ``Dash``) to keep import cost low.
"""

from __future__ import annotations

from dataclasses import dataclass, field  # Container types; field used for mutable defaults
from typing import TYPE_CHECKING, Any  # Type guards + Any for mistapi/manager references

if TYPE_CHECKING:  # pragma: no cover - imports for static analysis only
    from src.maps.plotly_map_callback_manager import (  # noqa: F401 - typing reference
        PlotlyMapCallbackManager,
    )


@dataclass
class MapViewerState:
    """Shared state for Plotly viewer Dash callbacks (waves A + B + C).

    Attributes
    ----------
    callback_manager:
        Pre-constructed :class:`PlotlyMapCallbackManager` used by the
        layer-toggle and click-details callbacks to apply visibility
        rules and build hover/click HTML panels.
    zones:
        Site zone records (from ``listSiteZones``) used by zone toggle
        and zone-action callbacks to resolve zone names to IDs.
    map_id:
        Current map UUID; used for logging context in panel-toggle and
        utility callbacks and as a fallback when the config store is
        missing.
    site_id:
        Current site UUID; used by delete and zone-action callbacks as
        the ``site_id`` parameter to Mist API delete calls and as a
        fallback when the config store is missing.
    api_session_ref:
        Live ``mistapi.APISession`` instance used by callbacks that
        invoke Mist API mutations (delete map, delete zone, etc.).
    ppm:
        Pixels-per-meter scale value; used by ``update_shape_labels``
        as the fallback when the figure metadata lacks an override.
    mistapi_ref:
        Reference to the ``mistapi`` module itself so callbacks can
        invoke ``mistapi.api.v1.*.delete*`` helpers without re-importing
        at call sites (mirrors the closure capture pattern).
    maps_manager_ref:
        Reference to the parent :class:`MapsManager` instance so
        callbacks can call instance helpers like ``_backup_map_geometry``
        without holding a direct method bound reference.
    """

    callback_manager: PlotlyMapCallbackManager  # Owns layer-toggle and click-detail helpers
    zones: list[dict[str, Any]] = field(default_factory=list)  # Site zone records (wave B/C)
    map_id: str | None = None  # Current map UUID for logging/fallback (wave B/C)
    site_id: str | None = None  # Current site UUID for API mutations (wave C)
    api_session_ref: Any = None  # mistapi.APISession used by delete/zone callbacks (wave C)
    ppm: float = 10.0  # Pixels-per-meter scale used by update_shape_labels (wave C)
    mistapi_ref: Any = None  # mistapi module reference used by API-touching callbacks (wave C)
    maps_manager_ref: Any = None  # MapsManager instance for _backup_map_geometry (wave C)
