"""Plotly/Dash viewer launcher subpackage.

Holds collaborators extracted from
:py:meth:`src.maps.maps_manager.MapsManager._launch_plotly_viewer` to
drive its cyclomatic complexity down toward the project ceiling of
CC <= 10. Wave A established :class:`MapViewerState` and
:class:`MapViewerCallbacks` with five trivial UI-toggle callbacks
(``apply_layer_toggles``, ``display_click_data``, ``toggle_origin_mode``,
``toggle_zone_name_input``, ``toggle_auto_refresh``). Subsequent waves
will move additional callbacks into the same callback class and grow
:class:`MapViewerState` to hold the closure variables they need.
"""

from src.maps.launcher.viewer_callbacks import MapViewerCallbacks  # Re-export for callers
from src.maps.launcher.viewer_state import MapViewerState  # Re-export for callers

__all__ = ["MapViewerCallbacks", "MapViewerState"]  # Public API of the subpackage
