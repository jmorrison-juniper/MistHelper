"""Matplotlib viewer + standalone launcher cluster (extracted from MapsManager).

Split out of ``src/maps/maps_manager.py`` so the ~165 LOC matplotlib
fallback viewer + standalone-launch flow lives in its own module. The
extracted methods stay as methods of a small wrapper class
:class:`_MapsMatplotlib`; ``__getattr__`` delegates lookups that miss
on the wrapper to the wrapped MapsManager, so calls to
``self._collect_map_payload``, ``self._build_map_data_response``,
``self.apisession``, and other shared state resolve without rewrites.

MapsManager keeps a slim ``launch_viewer_standalone`` delegating method
because ``main()`` in the same file invokes it as
``maps_manager.launch_viewer_standalone()``.
"""

from __future__ import annotations

import logging
from typing import Any

import mistapi  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class _MapsMatplotlib:
    """Wrapper class holding the extracted matplotlib/launch methods."""

    def __init__(self, maps_manager: Any) -> None:
        self._mm = maps_manager

    def __getattr__(self, name: str) -> Any:
        mm = self.__dict__.get("_mm")
        if mm is None:  # pragma: no cover - only during broken init
            raise AttributeError(name)
        return getattr(mm, name)

    def _launch_matplotlib_viewer(self, map_data, devices):
        """Fallback matplotlib viewer (view-only)."""
        logging.info("_launch_matplotlib_viewer called - basic fallback mode")
        from math import cos, radians, sin

        import matplotlib.pyplot as plt

        print("\n! Using matplotlib viewer (view-only, no interactivity)")
        logging.debug("Creating matplotlib figure for basic visualization")

        fig, ax = plt.subplots(figsize=(12, 10))

        map_width = map_data.get("width", 1000)
        map_height = map_data.get("height", 1000)

        ax.set_xlim(0, map_width)
        ax.set_ylim(0, map_height)
        ax.set_aspect("equal")
        ax.set_title(f"Map: {map_data.get('name', 'Unnamed')}")
        ax.set_xlabel("X (pixels)")
        ax.set_ylabel("Y (pixels)")

        # Plot devices
        for device in devices:
            if "x" not in device or "y" not in device:
                continue

            x, y = device["x"], device["y"]
            device_type = device.get("type", "unknown")
            name = device.get("name", device.get("mac", "Unknown"))
            orientation = device.get("orientation", 0)

            # Color by type
            color = {"ap": "green", "switch": "orange", "gateway": "purple"}.get(device_type, "gray")

            # Plot device
            ax.plot(
                x,
                y,
                marker="o",
                markersize=10,
                color=color,
                label=device_type if device_type not in ax.get_legend_handles_labels()[1] else "",
            )
            ax.text(x, y + 20, name, fontsize=8, ha="center")

            # Add orientation arrow
            if orientation != 0:
                arrow_length = 30
                dx = arrow_length * cos(radians(orientation))
                dy = arrow_length * sin(radians(orientation))
                ax.arrow(x, y, dx, dy, head_width=10, head_length=10, fc=color, ec=color, alpha=0.7)

        ax.legend()
        ax.grid(True, alpha=0.3)

        print("\n! Displaying map... Close window to return to menu")
        logging.info("Displaying matplotlib figure (blocking until window closed)")
        plt.show()
        logging.info("Matplotlib map viewer closed by user")

    def _resolve_initial_site(self, sites_sorted: list, requested_site_id: str | None) -> tuple[str, str]:
        """Resolve the initial site for standalone viewer from requested or default."""
        maps_by_id = {s.get("id"): s for s in sites_sorted}
        if requested_site_id and requested_site_id in maps_by_id:
            site = maps_by_id[requested_site_id]
            return site.get("id"), site.get("name", "Unknown")
        default_site = next((s for s in sites_sorted if s.get("name", "") == "CAS0123G"), None)
        site = default_site or sites_sorted[0]
        return site.get("id"), site.get("name", "Unknown")

    def _resolve_initial_map(self, all_maps: list, requested_map_id: str | None) -> tuple[str, dict]:
        """Resolve the initial map from requested or first available."""
        maps_by_id = {m.get("id"): m for m in all_maps}
        if requested_map_id and requested_map_id in maps_by_id:
            return requested_map_id, maps_by_id[requested_map_id]
        return all_maps[0].get("id"), all_maps[0]

    def _fetch_entities_on_map(self, api_fn, site_id: str, map_id: str, **kwargs) -> list:
        """Call api_fn for site_id, return entities filtered to map_id."""
        try:
            resp = api_fn(self.apisession, site_id=site_id, **kwargs)
            if resp.status_code == 200:
                return [entity for entity in (resp.data or []) if entity.get("map_id") == map_id]
        except Exception:
            pass
        return []

    def _fetch_site_maps(self, site_id: str) -> list:
        """Fetch maps for a site; return empty list on failure."""
        try:
            resp = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site_id)
            if resp.status_code == 200 and resp.data:
                return resp.data
        except Exception as error:
            logging.error("Error fetching maps for site %s: %s", site_id, error)
        return []

    def launch_viewer_standalone(self, requested_site_id: str = None, requested_map_id: str = None):
        """Launch the interactive map viewer directly without CLI site selection.

        This method is designed for standalone usage (e.g., maps_manager.py --viewer)
        where the user wants to skip the CLI menu and select sites/maps directly
        in the web browser interface via searchable dropdowns.

        Uses the full-featured viewer with all layers, controls, and sidebar.
        Site/map selection is handled in-browser via URL parameters.

        Args:
            requested_site_id: Optional site ID to load initially (from URL parameter)
            requested_map_id: Optional map ID to load initially (from URL parameter)
        """
        logging.info("launch_viewer_standalone: Starting web-first viewer mode")
        print("\n" + "=" * 70)
        print("  MAPS MANAGER - Standalone Web Viewer")
        print("  Select a site and map from the browser interface")
        print("=" * 70)
        print("\n  Loading sites...")

        all_sites = self._fetch_sites()
        if not all_sites:
            print("\n  [!] No sites found in organization")
            return

        sites_sorted = sorted(all_sites, key=lambda x: x.get("name", "").lower())
        print(f"  Found {len(sites_sorted)} sites")

        target_site_id, target_site_name = self._resolve_initial_site(sites_sorted, requested_site_id)
        print(f"  Loading maps for site: {target_site_name}...")

        all_maps = self._fetch_site_maps(target_site_id)

        devices: list = []
        zones: list = []
        clients: list = []
        map_id: str | None = None

        if not all_maps:
            print(f"\n  [!] No maps found for site {target_site_name}")
            print("  Launching viewer anyway - select a different site in browser")
        else:
            map_id, target_map = self._resolve_initial_map(all_maps, requested_map_id)
            print(f"  Loading map: {target_map.get('name', 'Unnamed')}...")
            devices = self._fetch_entities_on_map(
                mistapi.api.v1.sites.stats.listSiteDevicesStats,
                target_site_id,
                map_id,
                type="all",
                limit=1000,
            )
            zones = self._fetch_entities_on_map(mistapi.api.v1.sites.zones.listSiteZones, target_site_id, map_id)
            clients = self._fetch_entities_on_map(
                mistapi.api.v1.sites.stats.listSiteWirelessClientsStats, target_site_id, map_id
            )
            print(f"  Found {len(devices)} devices, {len(zones)} zones, {len(clients)} clients")

        launch_flask_viewer(
            self.apisession,
            target_site_id,
            map_id,
            sites_sorted,
            all_maps,
            self._collect_map_payload,
            self._build_map_data_response,
        )


def launch_viewer_standalone(maps_manager: Any):
    """Entry point mirroring MapsManager.launch_viewer_standalone.

    Kept as a module-level factory so callers can invoke the standalone
    viewer without instantiating :class:`_MapsMatplotlib` directly.
    """
    return _MapsMatplotlib(maps_manager).launch_viewer_standalone()
