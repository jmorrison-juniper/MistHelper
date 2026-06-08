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

from dataclasses import dataclass  # Lightweight container with auto __init__/__repr__
from typing import TYPE_CHECKING  # Guard heavy imports from runtime evaluation

if TYPE_CHECKING:  # pragma: no cover - imports for static analysis only
    from src.maps.plotly_map_callback_manager import (  # noqa: F401 - typing reference
        PlotlyMapCallbackManager,
    )


@dataclass
class MapViewerState:
    """Shared state for Plotly viewer Dash callbacks (wave A scope).

    Attributes
    ----------
    callback_manager:
        Pre-constructed :class:`PlotlyMapCallbackManager` used by the
        layer-toggle and click-details callbacks to apply visibility
        rules and build hover/click HTML panels.
    """

    callback_manager: PlotlyMapCallbackManager  # Owns layer-toggle and click-detail helpers
