#!/usr/bin/env python3
"""MapsManager - Interactive Map Viewer for Mist Networks.

This module contains the MapsManager class for managing site floor plans
and maps in Juniper Mist Cloud. It provides:
- Interactive web-based map viewer (Dash/Plotly)
- Map inventory and export operations
- Device placement and auto-placement operations
- Zone and wayfinding path visualization
- Connected client visualization
- RF coverage heatmaps

Can be run standalone or imported by MistHelper.py for Menu 112 integration.

Usage:
    Standalone:     python maps_manager.py [--menu] [--org ORG_ID]
    As module:      Menu option 112 in MistHelper.py (40. Interactive Map Viewer)

Author: Joseph Morrison (jmorrison@juniper.net)
Version: 26.01.09.18.00
"""

# ============================================================================
# IMPORTS
# ============================================================================

import importlib.util  # Runtime probe for optional visualization deps (plotly/dash/matplotlib)
import logging  # Module-level logger for MapsManager operations
import os  # Path utilities and environment variable access
import sys  # exit() calls in standalone entry point
from math import cos, pi, radians, sin  # Geometry helpers for map coordinate math
from typing import Any  # Type hints on payload dicts

from src.dataclasses.map_clone_deps import MapCloneSummary, ZoneCloneResult  # Issue #433 Phase C T3: clone helpers.
from src.dataclasses.map_marker_deps import DeviceMarkerStyle, MarkerPosition  # Issue #433 Phase C T3: marker helpers.
from src.dataclasses.map_scaling_deps import (  # Issue #433 Phase C T3: scaling wizard inputs.
    MapDimensions,
    MapScalingFactors,
    OriginalMapMetrics,
    ScaleChoiceContext,
)
from src.dataclasses.map_viewer_deps import (  # Issue #433 Phase C T3: viewer launcher inputs.
    HeatmapRenderCtx,
    MapViewerData,
    MapViewerOptional,
    MapViewerScope,
)
from src.dataclasses.map_wizard_deps import (  # Issue #433 Phase C T3: replacement wizard inputs.
    MapWizardApplyContext,
    MapWizardApplyTarget,
    MapWizardPreviewContext,
    MapWizardSummaryContext,
)
from src.maps._container_detection import (
    is_running_in_container,
)  # Detects Docker/container runtimes to gate GUI viewer launches.
from src.maps._flask_viewer import launch_flask_viewer  # Flask fallback viewer for headless environments.
from src.maps._plotly_viewer import launch_plotly_viewer  # Dash/Plotly interactive viewer for desktop use.
from src.maps._maps_utils import (  # Shared helpers: dict flattening, filename sanitization, CSV/JSON exports.
    flatten_dict_recursively,
    sanitize_filename,
    write_data_with_format_selection,
)
from src.maps.launcher import MapViewerCallbacks, MapViewerState  # Wave-A: extracted Dash callback wiring + state.
from src.maps.plotly_heatmap_renderer import PlotlyCoverageHeatmapRenderer  # RF coverage heatmap trace generator.
from src.maps.plotly_map_callback_manager import (
    PlotlyMapCallbackManager,
)  # Registers Dash callbacks for the interactive viewer.
from src.maps.plotly_map_figure_builder import PlotlyMapFigureBuilder  # Builds go.Figure objects with map overlays.
from src.maps.plotly_map_serializer import PlotlyMapDataSerializer  # Serializes map data for browser/Dash rendering.
from src.maps.plotly_map_templates import DashTemplateManager  # Provides HTML layout templates for the viewer.
from src.utils.input_utils import InputUtils  # Issue #433 Phase C: EOF-safe input wrapper for interactive prompts.

# Optional visualization imports — use find_spec for availability checks
PLOTLY_AVAILABLE = importlib.util.find_spec("plotly") is not None  # Cached truthy flag: plotly package available.
DASH_AVAILABLE = importlib.util.find_spec("dash") is not None  # Cached truthy flag: dash package available.
PIL_AVAILABLE = importlib.util.find_spec("PIL") is not None  # Cached truthy flag: Pillow imaging installed.

if PLOTLY_AVAILABLE:  # Only import heavy plotly module when available at runtime.
    import plotly.graph_objects as go  # Bound at module level so downstream figure builders can reference it.
else:
    go = None  # Fallback sentinel so attribute checks do not NameError.

# Dash symbols (Input, Output, State, and so on) are imported locally
# in methods that need them, since they require dash to be installed.
Dash = None  # Placeholder. Real Dash class imported lazily inside launcher methods.
html = None  # Placeholder for dash.html. Imported lazily where needed.
dcc = None  # Placeholder for dash.dcc. Imported lazily where needed.

try:
    import requests  # Used to download map images from Mist-signed URLs.
except ImportError:  # WHY: handle expected error
    requests = None  # Fallback sentinel so image-download paths can degrade gracefully.

try:
    from tqdm import tqdm  # Progress bar for bulk download/export loops.
except ImportError:  # WHY: handle expected error

    def tqdm(iterable, **_kwargs):  # WHY: declare public method tqdm
        """No-op fallback for tqdm progress bar."""
        return iterable  # WHY: return computed result


# Mist API import
try:
    import mistapi  # type: ignore[import-untyped]  # Optional dependency. Required for real API calls.
except ImportError:  # WHY: handle expected error
    mistapi = None  # type: ignore[assignment]  # Sentinel so tests can run without the SDK.

# Configure module logger
logger = logging.getLogger(__name__)  # Module-scoped logger for MapsManager operations.

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

# Page limit configuration
try:
    _raw_page_limit_env = os.environ.get("MIST_PAGE_LIMIT", "1000").strip()  # Read override from env, default "1000".
    _parsed_limit = int(_raw_page_limit_env)  # Parse to int. May raise ValueError caught below.
except Exception:  # WHY: handle expected error
    _parsed_limit = 1000  # Fall back to safe default on any parse failure.

DEFAULT_API_PAGE_LIMIT = max(1, min(_parsed_limit, 1000))  # Clamp to [1, 1000] per Mist API constraints.


class MapsManager:  # WHY: declare MapsManager class
    """Comprehensive Maps Management System for Mist Sites.

    Provides interactive management of site floor plans and maps including:
    - Map inventory and export operations
    - Image download and upload capabilities
    - Map creation and configuration
    - Device placement and auto-placement operations
    - Analytics and reporting
    """

    def __init__(self, api_session, organization_id):  # WHY: declare private helper __init__
        """Initialize MapsManager with API session and org context."""
        self.apisession = api_session  # WHY: init/update apisession attribute
        self.org_id = organization_id  # WHY: init/update org_id attribute
        self.current_site_id = None  # WHY: init/update current_site_id attribute
        self.current_site_name = None  # WHY: init/update current_site_name attribute
        logging.info("MapsManager initialized for organization: %s", self.org_id)  # WHY: action-log before operation

    def _fetch_sites(self):  # WHY: declare private helper _fetch_sites
        """Fetch all sites using instance API session (not global)."""
        try:
            resp = mistapi.api.v1.orgs.sites.listOrgSites(  # type: ignore[union-attr]
                self.apisession, self.org_id, limit=DEFAULT_API_PAGE_LIMIT
            )
            return mistapi.get_all(response=resp, mist_session=self.apisession)  # type: ignore[union-attr]
        except Exception as e:  # WHY: handle expected error
            logging.error("MapsManager._fetch_sites error: %s", e)  # WHY: surface fatal issue
            return []  # WHY: return computed result

    @staticmethod
    def _render_sites_menu(sites_sorted: list) -> None:  # WHY: declare private helper _render_sites_menu
        """Print numbered site menu."""
        print("\nAvailable Sites:")  # WHY: surface user-facing message
        print("-" * 60)  # WHY: surface user-facing message
        for idx, site in enumerate(sites_sorted):  # WHY: iterate collection
            print(f"  [{idx}] {site.get('name', 'Unnamed')}")  # WHY: surface user-facing message
        print("-" * 60)  # WHY: surface user-facing message

    @staticmethod
    def _match_site_by_index(
        sites_sorted: list, selection: str
    ) -> "dict | None":  # WHY: declare private helper _match_site_by_index
        """Resolve a numeric selection to a site, or None if invalid."""
        try:
            site_idx = int(selection)  # WHY: compute site_idx
        except ValueError:  # WHY: handle expected error
            return None  # WHY: return computed result
        if 0 <= site_idx < len(sites_sorted):  # WHY: branch on condition
            return sites_sorted[site_idx]  # WHY: return computed result
        print("\n! Invalid index")  # WHY: surface user-facing message
        return None  # WHY: return computed result

    @staticmethod
    def _match_site_by_name(
        sites_sorted: list, selection: str
    ) -> "dict | None":  # WHY: declare private helper _match_site_by_name
        """Substring-match against site names. None if no unique hit."""
        matches = [s for s in sites_sorted if selection.lower() in s.get("name", "").lower()]  # WHY: compute matches
        if len(matches) == 1:  # WHY: branch on condition
            return matches[0]  # WHY: return computed result
        if len(matches) > 1:  # WHY: branch on condition
            print(
                f"\n! Multiple matches found ({len(matches)}). Please be more specific."
            )  # WHY: surface user-facing message
            return None  # WHY: return computed result
        print("\n! No matching site found")  # WHY: surface user-facing message
        return None  # WHY: return computed result

    def _resolve_site_selection(
        self, sites_sorted: list, selection: str
    ) -> "dict | None":  # WHY: declare private helper _resolve_site_selection
        """Try index resolution first, fall back to name substring match."""
        by_index = self._match_site_by_index(sites_sorted, selection)  # WHY: compute by_index
        if by_index is not None:  # WHY: branch on condition
            return by_index  # WHY: return computed result
        try:
            int(selection)  # WHY: advance computation
        except ValueError:  # WHY: handle expected error
            return self._match_site_by_name(sites_sorted, selection)  # WHY: return computed result
        return None  # WHY: return computed result

    def _commit_selected_site(self, selected_site: dict) -> None:  # WHY: declare private helper _commit_selected_site
        """Persist the chosen site on the instance and surface confirmation."""
        self.current_site_id = selected_site.get("id")  # WHY: init/update current_site_id attribute
        self.current_site_name = selected_site.get("name", "Unknown")  # WHY: init/update current_site_name attribute
        print(f"\n   Site selected: {self.current_site_name}")  # WHY: surface user-facing message
        logging.info(
            "MapsManager site selection: %s (%s)", self.current_site_name, self.current_site_id
        )  # WHY: action-log before operation

    def select_site(self):  # WHY: declare public method select_site
        """Prompt user to select a site and cache the selection."""
        sites = self._fetch_sites()  # WHY: compute sites
        if not sites:  # WHY: guard against missing precondition
            print("\n! No sites found in organization")  # WHY: surface user-facing message
            return False  # WHY: return computed result
        sites_sorted = sorted(sites, key=lambda x: x.get("name", "").lower())  # WHY: compute sites_sorted
        self._render_sites_menu(sites_sorted)  # WHY: advance computation
        try:
            selection = InputUtils.safe_input(
                "Enter site index or name: ", context="select_site"
            ).strip()  # WHY: compute selection
            selected_site = self._resolve_site_selection(sites_sorted, selection)  # WHY: compute selected_site
            if selected_site is None:  # WHY: branch on condition
                return False  # WHY: return computed result
            self._commit_selected_site(selected_site)  # WHY: advance computation
            return True  # WHY: return computed result
        except EOFError:  # WHY: handle expected error
            logging.info("EOF detected during site selection")  # WHY: action-log before operation
            return False  # WHY: return computed result

    def get_current_site(self):  # WHY: declare public method get_current_site
        """Get current site selection, prompting if not set."""
        if not self.current_site_id:  # WHY: guard against missing precondition
            print("\n! No site currently selected. Please select a site first.")  # WHY: surface user-facing message
            if not self.select_site():  # WHY: guard against missing precondition
                return None, None  # WHY: return computed result
        return self.current_site_id, self.current_site_name  # WHY: return computed result

    @staticmethod
    def _print_map_selection_list(
        maps: list, site_name: str
    ) -> None:  # WHY: declare private helper _print_map_selection_list
        """Print the numbered list of maps available for a site."""
        print(f"\nMaps for site: {site_name}")  # Header
        print(f"{'-' * 80}")  # Separator rule
        for idx, map_item in enumerate(maps, 1):  # Enumerate with 1-based index for humans
            map_name = map_item.get("name", "Unnamed")  # Map display name
            map_type = map_item.get("type", "N/A")  # Map type (image, geojson, and so on)
            has_image = "with image" if "url" in map_item else "no image"  # Image availability tag
            print(f"  {idx}. {map_name} ({map_type}) - {has_image}")  # Numbered row
        print(f"{'-' * 80}")  # Closing rule

    @staticmethod
    def _parse_map_selection(
        selection: str, maps: list
    ) -> "str | None":  # WHY: declare private helper _parse_map_selection
        """Parse the user's numeric selection and return the chosen map_id or None."""
        map_idx = int(selection) - 1  # Convert to 0-based index (raises ValueError on bad input)
        if map_idx < 0:  # Zero or negative means cancel
            return None  # User cancelled the selection
        if map_idx >= len(maps):  # Out-of-range selection
            print("\n! Invalid selection")  # Inform the user
            return None  # No map chosen
        return maps[map_idx].get("id")  # Return the selected map's id

    def _prompt_map_choice(
        self, maps: list, site_name: str
    ) -> "str | None":  # WHY: declare private helper _prompt_map_choice
        """Display map list and prompt user to pick one. Returns map_id or None."""
        self._print_map_selection_list(maps, site_name)  # Show the selectable options
        try:
            selection = InputUtils.safe_input(
                "\nSelect map number (or 0 to cancel): ", context="_prompt_map_choice"
            ).strip()  # Read raw selection
            return self._parse_map_selection(selection, maps)  # Convert to a map id
        except ValueError:  # WHY: handle expected error
            print("\n! Invalid input - please enter a number")  # Guard against non-numeric input
            return None  # WHY: return computed result

    def _fetch_site_maps_or_none(
        self, site_id: str, site_name: str
    ) -> "list | None":  # WHY: declare private helper _fetch_site_maps_or_none
        """Fetch maps for a site, printing errors and returning None on failure/empty."""
        resp = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site_id)  # API call
        if resp.status_code != 200:  # HTTP failure guard
            print(f"\n! Failed to fetch maps: HTTP {resp.status_code}")  # Surface status
            return None  # Signal failure
        if not resp.data:  # Empty catalog guard
            print(f"\n! No maps found for site: {site_name}")  # Inform the operator
            return None  # Nothing to select
        return resp.data  # Return the list of maps

    def _select_map_with_list(
        self, site_id: str, site_name: str
    ) -> "tuple[str | None, list]":  # WHY: declare private helper _select_map_with_list
        """Fetch site maps and prompt for selection. Returns (map_id, maps_list)."""
        try:
            maps = self._fetch_site_maps_or_none(site_id, site_name)  # Try to load the catalog
            if not maps:  # Fetch failed or empty
                return None, []  # Nothing to select
            if len(maps) == 1:  # Auto-select when only one map exists
                print(f"\nAuto-selecting only available map: {maps[0].get('name', 'Unnamed')}")  # Notify
                return maps[0].get("id"), maps  # Return sole map
            return self._prompt_map_choice(maps, site_name), maps  # Interactive selection path
        except EOFError:  # WHY: handle expected error
            logging.info("EOF detected during map selection")  # Non-interactive shutdown
            return None, []  # No selection possible
        except Exception as e:  # WHY: handle expected error
            logging.exception("Error selecting map: %s", e)  # Log for diagnosis
            print(f"\n! Error selecting map: {e}")  # Surface to operator
            return None, []  # WHY: return computed result

    def _select_map_from_site(
        self, site_id, site_name, return_all_maps=False
    ):  # WHY: declare private helper _select_map_from_site
        """Select a map from a site.

        Returns map_id or None, optionally returns (map_id, maps_list).
        """
        map_id, maps = self._select_map_with_list(site_id, site_name)  # WHY: compute map_id
        return (map_id, maps) if return_all_maps else map_id  # WHY: return computed result

    def _backup_map_geometry(
        self, api_session, site_id, map_id, map_name, backup_reason="manual"
    ):  # WHY: declare private helper _backup_map_geometry
        """Delegating wrapper: backup lives in src.maps._maps_backup."""
        # Wrapper kept so viewer_callbacks.maps_manager_ref._backup_map_geometry
        # still resolves and tests can continue to stub the method on MapsManager.
        from src.maps._maps_backup import (  # WHY: import module symbols on demand
            BackupRequest,
            backup_map_geometry,
        )

        request = BackupRequest(  # WHY: aggregate five call args into one value object
            api_session=api_session,
            site_id=site_id,
            map_id=map_id,
            map_name=map_name,
            backup_reason=backup_reason,
        )
        return backup_map_geometry(request)  # WHY: return computed result

    def run_systematic_test(self) -> bool:  # WHY: declare public method run_systematic_test
        """Delegating wrapper: testing lives in src.maps._maps_testing."""
        # Wrapper kept so launch_viewer_standalone can still call
        # maps_manager.run_systematic_test() by name.
        from src.maps._maps_testing import run_systematic_test  # WHY: import required module

        return run_systematic_test(self)  # WHY: return computed result

    def _build_menu_dispatch(self) -> dict:  # WHY: declare private helper _build_menu_dispatch
        """Build menu choice to handler mapping."""
        table: dict = {"S": self.select_site}  # Site selection is the shared entry action.
        table.update(self._menu_dispatch_maps_section())  # Map inventory + edit + placement handlers.
        table.update(self._menu_dispatch_bulk_section())  # Org-wide bulk export/backup handlers.
        table.update(self._menu_dispatch_analytics_section())  # Analytics + viewer handlers.
        return table  # Combined dispatch table used by run_interactive_menu.

    def _menu_dispatch_maps_section(self) -> dict:  # WHY: declare private helper _menu_dispatch_maps_section
        """Return the map inventory/edit/placement portion of the dispatch table."""
        return {
            "1": self.list_site_maps,  # List maps for the current site.
            "2": self.export_site_maps,  # Export site maps to CSV/SQLite.
            "3": self.view_map_details,  # Detailed map view.
            "4": self.create_site_map,  # Create a new site map.
            "5": self.update_map_properties,  # Rename/resize an existing map.
            "6": self.delete_site_map,  # Delete a map.
            "7": self.upload_map_image,  # Upload/replace the map image.
            "8": self.view_devices_on_map,  # Show devices placed on a map.
            "9": self.auto_place_aps,  # Auto-place APs (placeholder).
            "10": self.auto_orient_aps,  # Auto-orient APs (placeholder).
            "11": self.set_device_location,  # Manually set an AP location.
            "12": self.clone_map,  # Duplicate a map.
            "13": self.intelligent_map_replacement_wizard,  # Guided replacement flow.
        }

    def _menu_dispatch_bulk_section(self) -> dict:  # WHY: declare private helper _menu_dispatch_bulk_section
        """Return the org-wide bulk export/backup handlers."""
        return {
            "20": self.list_all_org_maps,  # Org-wide map listing.
            "21": self.export_all_site_maps,  # Export every site's maps.
            "22": self.export_maps_with_images,  # Export maps plus images.
            "23": self.bulk_download_org_images,  # Bulk image download.
            "24": self.backup_all_maps,  # Full org backup.
            "25": self.maps_without_images_report,  # Report maps missing images.
        }

    def _menu_dispatch_analytics_section(self) -> dict:  # WHY: declare private helper _menu_dispatch_analytics_section
        """Return the analytics + interactive viewer handlers."""
        return {
            "30": self.map_coverage_analytics,  # Coverage analytics.
            "31": self.device_density_analytics,  # Device density analytics.
            "32": self.map_usage_statistics,  # Usage/statistics report.
            "40": self.interactive_map_viewer,  # Launch the interactive viewer.
        }

    @staticmethod
    def _print_menu_inventory_section() -> None:  # WHY: declare private helper _print_menu_inventory_section
        """Inventory + creation + placement sections of the menu."""
        print("\nSite Selection:")  # WHY: surface user-facing message
        print("  S. Select different site")  # WHY: surface user-facing message
        print("\nMap Inventory & Export:")  # WHY: surface user-facing message
        print("  1. List maps for current site")  # WHY: surface user-facing message
        print("  2. Export maps for current site to CSV/SQLite")  # WHY: surface user-facing message
        print("  3. View detailed map information")  # WHY: surface user-facing message
        print("\nMap Creation & Modification:")  # WHY: surface user-facing message
        print("  4. Create new site map")  # WHY: surface user-facing message
        print("  5. Update map properties")  # WHY: surface user-facing message
        print("  6. Delete site map")  # WHY: surface user-facing message
        print("  7. Upload/replace map image")  # WHY: surface user-facing message
        print("  12. Clone/duplicate map")  # WHY: surface user-facing message
        print("  13. Intelligent map replacement wizard")  # WHY: surface user-facing message
        print("\nDevice Placement:")  # WHY: surface user-facing message
        print("  8. View devices on map")  # WHY: surface user-facing message
        print("  9. Auto-place APs on map")  # WHY: surface user-facing message
        print("  10. Auto-orient APs on map")  # WHY: surface user-facing message
        print("  11. Set AP/device location manually")  # WHY: surface user-facing message

    @staticmethod
    def _print_menu_bulk_and_analytics_section() -> (
        None
    ):  # WHY: declare private helper _print_menu_bulk_and_analytics_section
        """Bulk + analytics + visualization sections of the menu."""
        print("\nBulk Operations (All Sites):")  # WHY: surface user-facing message
        print("  20. List all site maps across organization")  # WHY: surface user-facing message
        print("  21. Export all site maps to CSV/SQLite")  # WHY: surface user-facing message
        print("  22. Export maps with image metadata")  # WHY: surface user-facing message
        print("  23. Download all org map images")  # WHY: surface user-facing message
        print("  24. Backup all maps (metadata + images)")  # WHY: surface user-facing message
        print("  25. Maps without images report")  # WHY: surface user-facing message
        print("\nAnalytics & Reporting:")  # WHY: surface user-facing message
        print("  30. Map coverage analytics")  # WHY: surface user-facing message
        print("  31. Device density by map")  # WHY: surface user-facing message
        print("  32. Map usage statistics")  # WHY: surface user-facing message
        print("\nVisualization & Editing:")  # WHY: surface user-facing message
        print("  40. Interactive map viewer (view/edit devices, walls, zones)")  # WHY: surface user-facing message
        print("\n  0. Return to main menu")  # WHY: surface user-facing message
        print("=" * 80)  # WHY: surface user-facing message

    def _print_menu(self) -> None:  # WHY: declare private helper _print_menu
        """Display the Maps Manager menu."""
        print("\n" + "=" * 80)  # WHY: surface user-facing message
        print("MAPS MANAGER - Site Floorplan & Map Operations")  # WHY: surface user-facing message
        if self.current_site_name:  # WHY: branch on condition
            print(f"Current Site: {self.current_site_name}")  # WHY: surface user-facing message
        print("=" * 80)  # WHY: surface user-facing message
        self._print_menu_inventory_section()  # WHY: advance computation
        self._print_menu_bulk_and_analytics_section()  # WHY: advance computation

    def _read_menu_choice(self) -> "str | None":  # WHY: declare private helper _read_menu_choice
        """Prompt for a menu selection. Return None on EOF."""
        try:
            return (  # WHY: return computed result
                InputUtils.safe_input("\nEnter your selection number now: ", context="run_interactive_menu")
                .strip()
                .upper()
            )
        except EOFError:  # WHY: handle expected error
            logging.info("EOF detected in MapsManager menu - session disconnected")  # WHY: action-log before operation
            return None  # WHY: return computed result

    @staticmethod
    def _print_maps_manager_banner() -> None:  # WHY: declare private helper _print_maps_manager_banner
        """Print the Maps Manager header banner before initial site selection."""
        print("\n" + "=" * 80)  # Top rule
        print("MAPS MANAGER - Initial Site Selection")  # Screen title
        print("=" * 80)  # Bottom rule
        print("\nPlease select a site to work with:")  # Instruction line

    def _dispatch_menu_choice(
        self, choice: "str | None", dispatch: dict
    ) -> bool:  # WHY: declare private helper _dispatch_menu_choice
        """Handle one menu choice. Return True to keep looping, False to exit."""
        if choice is None or choice == "0":  # Sentinel or explicit quit
            if choice == "0":  # Only log the deliberate exit
                logging.info("Exiting Maps Manager")  # Note the exit reason
            return False  # Signal the caller to break the loop
        handler = dispatch.get(choice)  # Look up the handler for this choice
        if handler:  # Recognised choice
            handler()  # Invoke the associated action
        else:
            print(f"\n! Invalid selection: '{choice}'. Please enter a valid option.")  # Feedback
            logging.warning("Invalid Maps Manager menu selection: %s", choice)  # Audit trail
        return True  # Continue the menu loop

    def run_interactive_menu(self):  # WHY: declare public method run_interactive_menu
        """Main interactive menu loop for Maps Manager."""
        self._print_maps_manager_banner()  # Show entry banner
        if not self.select_site():  # Site is required before any action
            print("\n! Site selection required. Returning to main menu.")  # Explain the exit
            return  # Bail out of the menu entirely
        dispatch = self._build_menu_dispatch()  # Build the choice -> callable table once
        while True:  # Menu loop until the user quits
            self._print_menu()  # Render the current menu screen
            if not self._dispatch_menu_choice(self._read_menu_choice(), dispatch):  # Handle one action
                return  # Exit sentinel returned

    def _fetch_maps_for_site(self, site_id: str):  # WHY: declare private helper _fetch_maps_for_site
        """Fetch maps for a site. Return list or None on non-200 / error."""
        try:
            resp = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site_id)  # WHY: compute resp
        except Exception as e:  # WHY: handle expected error
            logging.exception("Error listing site maps: %s", e)  # WHY: capture exception with traceback
            print(f"\n! Error listing maps: {e}")  # WHY: surface user-facing message
            return None  # WHY: return computed result
        if resp.status_code != 200:  # WHY: branch on condition
            print(f"\n! Failed to fetch maps: HTTP {resp.status_code}")  # WHY: surface user-facing message
            return None  # WHY: return computed result
        return resp.data  # WHY: return computed result

    @staticmethod
    def _format_site_maps_row(map_item: dict) -> str:  # WHY: declare private helper _format_site_maps_row
        """Format a single map into the site-list table row."""
        map_name = map_item.get("name", "Unnamed")[:34]  # WHY: compute map_name
        map_type = map_item.get("type", "N/A")[:14]  # WHY: compute map_type
        width = map_item.get("width", 0)  # WHY: compute width
        height = map_item.get("height", 0)  # WHY: compute height
        dimensions = f"{width}x{height}" if width and height else "N/A"  # WHY: compute dimensions
        has_image = "Yes" if "url" in map_item else "No"  # WHY: compute has_image
        return f"{map_name:<35} {map_type:<15} {dimensions:<20} {has_image:<8}"  # WHY: return computed result

    @staticmethod
    def _render_site_maps_table(maps: list) -> None:  # WHY: the table prints no site name, so the parameter went
        """Print the header + all rows for the site-map summary table."""
        print(f"\n{'-' * 80}")  # WHY: surface user-facing message
        print(f"Total Maps Found: {len(maps)}")  # WHY: surface user-facing message
        print(f"{'-' * 80}")  # WHY: surface user-facing message
        print(f"{'Map Name':<35} {'Type':<15} {'Dimensions':<20} {'Image':<8}")  # WHY: surface user-facing message
        print(f"{'-' * 80}")  # WHY: surface user-facing message
        for map_item in maps:  # WHY: iterate collection
            print(MapsManager._format_site_maps_row(map_item))  # WHY: surface user-facing message
        print(f"{'-' * 80}")  # WHY: surface user-facing message

    def list_site_maps(self):  # WHY: declare public method list_site_maps
        """Display list of maps for currently selected site."""
        print("\n" + "-" * 80)  # WHY: surface user-facing message
        print("LIST SITE MAPS - Current Site")  # WHY: surface user-facing message
        print("-" * 80)  # WHY: surface user-facing message
        site_id, site_name = self.get_current_site()  # WHY: compute site_id
        if not site_id:  # WHY: guard against missing precondition
            return  # WHY: return early
        print(f"\nFetching maps for site: {site_name}")  # WHY: surface user-facing message
        maps = self._fetch_maps_for_site(site_id)  # WHY: compute maps
        if maps is None:  # WHY: branch on condition
            return  # WHY: return early
        if not maps:  # WHY: guard against missing precondition
            print(f"\n! No maps found for site: {site_name}")  # WHY: surface user-facing message
            return  # WHY: return early
        self._render_site_maps_table(maps)  # WHY: advance computation. The caller above already printed the site name
        logging.info("Listed %s maps for site %s", len(maps), site_name)  # WHY: action-log before operation

    @staticmethod
    def _build_org_map_row(site: dict, map_item: dict) -> dict:  # WHY: declare private helper _build_org_map_row
        """Flatten a (site, map) pair into the org-wide summary row shape."""
        return {  # WHY: return computed result
            "site_id": site["id"],
            "site_name": site.get("name", "Unknown"),
            "map_id": map_item.get("id", "N/A"),
            "map_name": map_item.get("name", "Unnamed"),
            "type": map_item.get("type", "N/A"),
            "width": map_item.get("width", 0),
            "height": map_item.get("height", 0),
            "has_image": "url" in map_item,
        }

    def _collect_all_org_map_rows(self, sites: list) -> list:  # WHY: declare private helper _collect_all_org_map_rows
        """Iterate sites. Return the flattened summary rows for every map."""
        all_maps: list = []  # WHY: assign computed value
        for site in tqdm(sites, desc="Scanning sites", unit="site"):  # WHY: iterate collection
            try:
                resp = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site["id"])  # WHY: compute resp
                if resp.status_code != 200:  # WHY: branch on condition
                    continue  # WHY: skip to next iteration
                for map_item in resp.data:  # WHY: iterate collection
                    all_maps.append(self._build_org_map_row(site, map_item))  # WHY: advance computation
            except Exception as e:  # WHY: handle expected error
                # Skip sites whose listSiteMaps failed. Keep scanning the rest.
                logging.debug("Error fetching maps for site %s: %s", site["id"], e)  # WHY: action-log after operation
                continue  # WHY: skip to next iteration
        return all_maps  # WHY: return computed result

    @staticmethod
    def _render_org_maps_table(rows: list) -> None:  # WHY: declare private helper _render_org_maps_table
        """Print the (site, map, type, image?) table for the org-wide listing."""
        print(f"\n{'-' * 80}")  # WHY: surface user-facing message
        print(f"Total Maps Found: {len(rows)}")  # WHY: surface user-facing message
        print(f"{'-' * 80}")  # WHY: surface user-facing message
        print(f"{'Site Name':<30} {'Map Name':<25} {'Type':<15} {'Image':<8}")  # WHY: surface user-facing message
        print(f"{'-' * 80}")  # WHY: surface user-facing message
        for map_item in rows:  # WHY: iterate collection
            site_name = map_item["site_name"][:29]  # WHY: compute site_name
            map_name = map_item["map_name"][:24]  # WHY: compute map_name
            map_type = map_item["type"][:14]  # WHY: compute map_type
            has_image = "Yes" if map_item["has_image"] else "No"  # WHY: compute has_image
            print(f"{site_name:<30} {map_name:<25} {map_type:<15} {has_image:<8}")  # WHY: surface user-facing message
        print(f"{'-' * 80}")  # WHY: surface user-facing message

    def list_all_org_maps(self):  # WHY: declare public method list_all_org_maps
        """Display summary list of all maps across organization sites."""
        print("\n" + "-" * 80)  # WHY: surface user-facing message
        print("LIST ALL ORGANIZATION MAPS - All Sites")  # WHY: surface user-facing message
        print("-" * 80)  # WHY: surface user-facing message
        try:
            sites = self._fetch_sites()  # WHY: compute sites
            if not sites:  # WHY: guard against missing precondition
                print("\n! No sites found in organization")  # WHY: surface user-facing message
                return  # WHY: return early
            print(f"\nFetching maps from {len(sites)} sites...")  # WHY: surface user-facing message
            all_maps = self._collect_all_org_map_rows(sites)  # WHY: compute all_maps
            if not all_maps:  # WHY: guard against missing precondition
                print("\n! No maps found across all sites")  # WHY: surface user-facing message
                return  # WHY: return early
            self._render_org_maps_table(all_maps)  # WHY: advance computation
            logging.info("Listed %s maps from %s sites", len(all_maps), len(sites))  # WHY: action-log before operation
        except Exception as e:  # WHY: handle expected error
            logging.exception("Error listing site maps: %s", e)  # WHY: capture exception with traceback
            print(f"\n! Error listing maps: {e}")  # WHY: surface user-facing message

    def export_site_maps(self):  # WHY: declare public method export_site_maps
        """Export maps for currently selected site to CSV/SQLite."""
        self._print_export_site_maps_header()  # Section banner for the export flow.
        site_id, site_name = self.get_current_site()  # Resolve currently-selected site context.
        if not site_id:  # Guard clause: no site chosen, nothing to export.
            return  # WHY: return early
        try:
            self._run_export_site_maps(site_id, site_name)  # Delegate the fetch+write body to a helper.
        except Exception as e:  # WHY: handle expected error
            logging.exception("Error exporting site maps: %s", e)  # Full stack for post-mortem debugging.
            print(f"\n! Error during export: {e}")  # User-facing summary.

    @staticmethod
    def _print_export_site_maps_header() -> None:  # WHY: declare private helper _print_export_site_maps_header
        """Print the banner for the export_site_maps flow."""
        print("\n" + "-" * 80)  # Visual break before the section.
        print("EXPORT SITE MAPS - Current Site")  # Section title.
        print("-" * 80)  # Trailing divider.

    def _run_export_site_maps(
        self, site_id: str, site_name: str
    ) -> None:  # WHY: declare private helper _run_export_site_maps
        """Fetch, flatten, and persist maps for a single site."""
        print(f"\nExporting maps for site: {site_name}")  # Progress line for the user.
        maps = self._fetch_maps_for_site(site_id)  # Retrieve map list via API.
        if not maps:  # Guard clause: empty or None result.
            if maps is not None:  # Distinguish "API OK, empty list" from "API error".
                print(f"\n! No maps found for site: {site_name}")  # Inform the user of the empty result.
            return  # WHY: return early
        site_stub = {"id": site_id, "name": site_name}  # Minimal site payload used by the flattener.
        maps_data = [self._flatten_map_for_export(site_stub, m) for m in maps]  # Flatten each map for export.
        filename = f"SiteMaps_{sanitize_filename(site_name or 'unknown_site')}"  # Sanitize name for filesystem.
        write_data_with_format_selection(maps_data, filename, api_function_name="listSiteMaps")  # Prompt+write.
        self._print_export_completion(len(maps_data))  # Confirm success and count.
        logging.info("Exported %s maps from site %s", len(maps_data), site_name)  # Audit trail entry.

    @staticmethod
    def _print_export_completion(count: int) -> None:  # WHY: declare private helper _print_export_completion
        """Print the export completion banner."""
        print(f"\n{'-' * 80}")  # Divider before summary.
        print(f"Export completed: {count} maps exported")  # Count of maps exported.
        print(f"{'-' * 80}")  # Divider after summary.

    def _flatten_map_for_export(
        self, site: dict, map_item: dict
    ) -> dict:  # WHY: declare private helper _flatten_map_for_export
        """Flatten nested map + inject site/org identifiers for tabular export."""
        flattened = flatten_dict_recursively(map_item)  # WHY: compute flattened
        flattened["site_id"] = site["id"]  # WHY: assign computed value
        flattened["site_name"] = site.get("name", "Unknown")  # WHY: assign computed value
        flattened["org_id"] = self.org_id  # WHY: assign computed value
        return flattened  # WHY: return computed result

    def _fetch_site_maps_safe(
        self, site_id: str, err_context: str
    ) -> list:  # WHY: declare private helper _fetch_site_maps_safe
        """Fetch maps for a site. Swallow + log per-site failures so the outer loop continues."""
        try:
            resp = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site_id)  # WHY: compute resp
            if resp.status_code == 200:  # WHY: branch on condition
                return resp.data or []  # WHY: return computed result
        except Exception as e:  # WHY: handle expected error
            logging.debug("Error %s site %s: %s", err_context, site_id, e)  # WHY: action-log after operation
        return []  # WHY: return computed result

    def _collect_flat_map_rows(
        self, sites: list, desc: str
    ) -> list:  # WHY: declare private helper _collect_flat_map_rows
        """Fetch + flatten every map across sites. Progress-bar labelled `desc`."""
        rows: list = []  # WHY: assign computed value
        for site in tqdm(sites, desc=desc, unit="site"):  # WHY: iterate collection
            for map_item in self._fetch_site_maps_safe(site["id"], "exporting maps for"):  # WHY: iterate collection
                rows.append(self._flatten_map_for_export(site, map_item))  # WHY: advance computation
        return rows  # WHY: return computed result

    def _collect_maps_with_images(self, sites: list) -> list:  # WHY: declare private helper _collect_maps_with_images
        """Fetch + flatten only maps that carry a `url` or `thumbnail_url`."""
        rows: list = []  # WHY: assign computed value
        for site in tqdm(sites, desc="Scanning for images", unit="site"):  # WHY: iterate collection
            for map_item in self._fetch_site_maps_safe(site["id"], "scanning"):  # WHY: iterate collection
                if "url" in map_item or "thumbnail_url" in map_item:  # WHY: branch on condition
                    rows.append(self._flatten_map_for_export(site, map_item))  # WHY: advance computation
        return rows  # WHY: return computed result

    def _print_maps_export_summary(
        self, exported_count: int, sites_count: int
    ) -> None:  # WHY: declare private helper _print_maps_export_summary
        """Print and log the finalization banner for a bulk map export."""
        print(f"\n{'-' * 80}")  # WHY: surface user-facing message
        print(f"Export completed: {exported_count} maps exported")  # WHY: surface user-facing message
        print(f"{'-' * 80}")  # WHY: surface user-facing message
        logging.info("Exported %s maps from %s sites", exported_count, sites_count)  # WHY: action-log before operation

    def export_all_site_maps(self):  # WHY: declare public method export_all_site_maps
        """Export all site maps across organization to CSV/SQLite with full metadata."""
        print("\n" + "-" * 80)  # WHY: surface user-facing message
        print("EXPORT ALL ORGANIZATION MAPS - All Sites")  # WHY: surface user-facing message
        print("-" * 80)  # WHY: surface user-facing message
        try:
            sites = self._fetch_sites()  # WHY: compute sites
            if not sites:  # WHY: guard against missing precondition
                print("\n! No sites found in organization")  # WHY: surface user-facing message
                return  # WHY: return early
            print(f"\nExporting maps from {len(sites)} sites...")  # WHY: surface user-facing message
            all_maps_data = self._collect_flat_map_rows(sites, "Exporting maps")  # WHY: compute all_maps_data
            if not all_maps_data:  # WHY: guard against missing precondition
                print("\n! No maps found to export")  # WHY: surface user-facing message
                return  # WHY: return early
            write_data_with_format_selection(
                all_maps_data, "SiteMaps_Export", api_function_name="listSiteMaps"
            )  # WHY: assign computed value
            self._print_maps_export_summary(len(all_maps_data), len(sites))  # WHY: advance computation
        except Exception as e:  # WHY: handle expected error
            logging.exception("Error exporting site maps: %s", e)  # WHY: capture exception with traceback
            print(f"\n! Error during export: {e}")  # WHY: surface user-facing message

    def export_maps_with_images(self):  # WHY: declare public method export_maps_with_images
        """Export maps metadata focusing on image information."""
        print("\n" + "-" * 80)  # WHY: surface user-facing message
        print("EXPORT MAPS WITH IMAGE METADATA")  # WHY: surface user-facing message
        print("-" * 80)  # WHY: surface user-facing message
        try:
            sites = self._fetch_sites()  # WHY: compute sites
            if not sites:  # WHY: guard against missing precondition
                print("\n! No sites found in organization")  # WHY: surface user-facing message
                return  # WHY: return early
            print(f"\nScanning {len(sites)} sites for maps with images...")  # WHY: surface user-facing message
            maps_with_images = self._collect_maps_with_images(sites)  # WHY: compute maps_with_images
            if not maps_with_images:  # WHY: guard against missing precondition
                print("\n! No maps with images found")  # WHY: surface user-facing message
                return  # WHY: return early
            write_data_with_format_selection(
                maps_with_images, "SiteMaps_WithImages", api_function_name="listSiteMaps"
            )  # WHY: assign computed value
            print(f"\n{'-' * 80}")  # WHY: surface user-facing message
            print(f"Export completed: {len(maps_with_images)} maps with images")  # WHY: surface user-facing message
            print(f"{'-' * 80}")  # WHY: surface user-facing message
            logging.info("Exported %s maps with images", len(maps_with_images))  # WHY: action-log before operation
        except Exception as e:  # WHY: handle expected error
            logging.exception("Error exporting maps with images: %s", e)  # WHY: capture exception with traceback
            print(f"\n! Error during export: {e}")  # WHY: surface user-facing message

    def _determine_image_extension(
        self, image_url: str
    ) -> str:  # WHY: declare private helper _determine_image_extension
        """Determine file extension from image URL. Returns '.png' if unknown."""
        if "." not in image_url:  # WHY: branch on condition
            return ".png"  # WHY: return computed result
        url_ext = image_url.rsplit(".", 1)[-1].split("?")[0].lower()  # WHY: compute url_ext
        if url_ext in ["png", "jpg", "jpeg", "gif", "svg"]:  # WHY: branch on condition
            return f".{url_ext}"  # WHY: return computed result
        return ".png"  # WHY: return computed result

    def _resolve_map_download_target(
        self, map_item: dict, download_dir: str
    ) -> "tuple[str, str] | None":  # WHY: declare private helper _resolve_map_download_target
        """Return (image_url, filepath) for the map image, or None when URL missing."""
        import os  # WHY: import required module

        image_url = map_item.get("url")  # WHY: compute image_url
        if not image_url:  # WHY: guard against missing precondition
            return None  # WHY: return computed result
        map_name = map_item.get("name", "unnamed")  # WHY: compute map_name
        map_id = map_item.get("id", "unknown")  # WHY: compute map_id
        file_ext = self._determine_image_extension(image_url)  # WHY: compute file_ext
        filename = f"{sanitize_filename(map_name)}_{map_id[:8]}{file_ext}"  # WHY: compute filename
        filepath = os.path.join(download_dir, filename)  # WHY: compute filepath
        return image_url, filepath  # WHY: return computed result

    def _download_single_map_image(
        self, map_item: dict, download_dir: str
    ) -> bool:  # WHY: declare private helper _download_single_map_image
        """Download one map image to download_dir. Returns True on success."""
        import requests  # WHY: import required module

        target = self._resolve_map_download_target(map_item, download_dir)  # WHY: compute target
        if target is None:  # WHY: guard against missing precondition
            return False  # WHY: return computed result
        image_url, filepath = target  # WHY: compute image_url
        map_name = map_item.get("name", "unnamed")  # WHY: compute map_name
        try:
            response = requests.get(image_url, timeout=30)  # WHY: compute response
            if response.status_code == 200:  # WHY: branch on condition
                with open(filepath, "wb") as f:  # WHY: manage scoped resource
                    f.write(response.content)  # WHY: advance computation
                return True  # WHY: return computed result
            logging.warning(
                "Failed to download %s: HTTP %s", map_name, response.status_code
            )  # WHY: surface non-fatal issue
        except Exception as e:  # WHY: handle expected error
            logging.error("Error downloading map image %s: %s", map_item.get("id"), e)  # WHY: surface fatal issue
        return False  # WHY: return computed result

    def _lookup_site_name(self, site_id: str) -> str:  # WHY: declare private helper _lookup_site_name
        """Return the site's display name from the site catalog, or 'Unknown'."""
        sites = self._fetch_sites()  # Fetch site catalog for name lookup
        return next((s.get("name", "Unknown") for s in sites if s["id"] == site_id), "Unknown")  # Match by id

    def _fetch_maps_with_images(
        self, site_id: str, site_name: str
    ) -> "list | None":  # WHY: declare private helper _fetch_maps_with_images
        """Fetch site maps and return those with downloadable images (or None)."""
        logging.info("Calling listSiteMaps for site_id=%s", site_id)  # Log API call start
        maps_response = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site_id)  # Fetch maps
        logging.debug("listSiteMaps returned status=%s", maps_response.status_code)  # Log API result
        if maps_response.status_code != 200:  # API call failed
            print(f"\n! Failed to fetch maps: {maps_response.status_code}")  # User-visible failure
            return None  # Signal failure to orchestrator
        maps_with_images = [m for m in maps_response.data if "url" in m]  # Only maps that carry an image URL
        if not maps_with_images:  # No images available for this site
            print(f"\n! No maps with images found for site: {site_name}")  # User-visible no-data message
            return None  # Signal nothing to download
        return maps_with_images  # Return the filtered list

    def _resolve_site_maps_for_download(
        self, site_id: str
    ) -> tuple[str, list] | None:  # WHY: declare private helper _resolve_site_maps_for_download
        """Resolve site name and fetch list of maps with downloadable images. Returns None on failure."""
        logging.info("Resolving site name for download target site_id=%s", site_id)  # Log resolution start
        site_name = self._lookup_site_name(site_id)  # Resolve human-readable site name
        logging.debug("Resolved site_name=%s", site_name)  # Log resolved name
        print(f"\nFetching maps for site: {site_name}")  # User-visible status
        maps_with_images = self._fetch_maps_with_images(site_id, site_name)  # Filtered map list
        if not maps_with_images:  # Fetch failed or nothing downloadable
            return None  # Propagate the failure sentinel
        return site_name, maps_with_images  # Return resolved name and maps for download loop

    def _download_maps_batch(
        self, maps_with_images: list, download_dir: str
    ) -> int:  # WHY: declare private helper _download_maps_batch
        """Download a batch of map images to the target directory, returning the success count."""
        # Log batch start with count and target dir
        logging.info(
            "Starting batch download of %d map images to %s", len(maps_with_images), download_dir
        )  # WHY: action-log before operation
        downloaded = sum(  # Count successful downloads
            1  # Each successful download contributes 1
            for map_item in tqdm(maps_with_images, desc="Downloading", unit="image")  # Iterate with progress bar
            if self._download_single_map_image(map_item, download_dir)  # Delegate to existing single-image helper
        )
        logging.debug("Batch download finished with %d successes", downloaded)  # Log batch outcome
        return downloaded  # Return count for summary

    @staticmethod
    def _print_download_images_header() -> None:  # WHY: declare private helper _print_download_images_header
        """Print the banner for the download-site-map-images flow."""
        print("\n" + "-" * 80)  # User-visible banner top border.
        print("DOWNLOAD SITE MAP IMAGES")  # User-visible operation title.
        print("-" * 80)  # User-visible banner bottom border.

    @staticmethod
    def _print_download_images_summary(
        downloaded: int, total: int, download_dir: str
    ) -> None:  # WHY: declare private helper _print_download_images_summary
        """Print the final tally after a batch image download."""
        print(f"\n{'-' * 80}")  # User-visible summary top border.
        print(f"Downloaded {downloaded} of {total} images")  # User-visible success count.
        print(f"Location: {download_dir}")  # User-visible target path.
        print(f"{'-' * 80}")  # User-visible summary bottom border.

    def _run_download_site_map_images(
        self, site_id: str
    ) -> None:  # WHY: declare private helper _run_download_site_map_images
        """Resolve the current site's maps and download all with images."""
        resolved = self._resolve_site_maps_for_download(site_id)  # Resolve name + maps with images.
        if resolved is None:  # Helper signalled failure or no images.
            return  # Stop -- user already informed.
        site_name, maps_with_images = resolved  # Unpack resolved tuple.
        print(f"\nFound {len(maps_with_images)} maps with images")  # User-visible count.
        import os  # Standard path utilities -- imported lazily to match prior behavior.

        download_dir = os.path.join("data", "map_images", sanitize_filename(site_name))  # Per-site output dir.
        os.makedirs(download_dir, exist_ok=True)  # Ensure directory exists.
        print(f"Downloading to: {download_dir}")  # User-visible target path.
        downloaded = self._download_maps_batch(maps_with_images, download_dir)  # Run batch download loop.
        self._print_download_images_summary(downloaded, len(maps_with_images), download_dir)  # Final tally.
        logging.info("Downloaded %s map images to %s", downloaded, download_dir)  # Log final outcome.

    def download_site_map_images(self):  # WHY: declare public method download_site_map_images
        """Download map images to local disk."""
        self._print_download_images_header()  # Section banner.
        try:  # Wrap orchestrator to log any unexpected error to user.
            site_id, _ = self.get_current_site()  # Resolve currently selected site.
            if not site_id:  # No site selected by user.
                print("\n! No site selected")  # User-visible no-site message.
                return  # Nothing to download.
            self._run_download_site_map_images(site_id)  # Delegate the flow to helper.
        except Exception as e:  # Catch-all for unexpected runtime errors.
            logging.exception("Error downloading map images: %s", e)  # Log full traceback.
            print(f"\n! Error downloading images: {e}")  # User-visible error message.

    def _print_map_optional_fields(
        self, map_details: dict
    ) -> None:  # WHY: declare private helper _print_map_optional_fields
        """Print optional detail fields for a map (URL, coordinates, wayfinding)."""
        if "url" in map_details:  # WHY: branch on condition
            print(f"Image URL: {map_details['url'][:80]}...")  # WHY: surface user-facing message
        if "latlng" in map_details:  # WHY: branch on condition
            latlng = map_details["latlng"]  # WHY: compute latlng
            print(f"Coordinates: {latlng.get('lat')}, {latlng.get('lng')}")  # WHY: surface user-facing message
        if "wayfinding" in map_details:  # WHY: branch on condition
            print("Wayfinding Enabled: Yes")  # WHY: surface user-facing message

    @staticmethod
    def _print_view_map_details_header() -> None:  # WHY: declare private helper _print_view_map_details_header
        """Print the banner for the view-map-details flow."""
        print("\n" + "-" * 80)  # Top rule of the section banner.
        print("VIEW MAP DETAILS")  # Human-readable title.
        print("-" * 80)  # Bottom rule of the section banner.

    def _fetch_map_detail(
        self, site_id: str, map_id: str
    ) -> dict | None:  # WHY: declare private helper _fetch_map_detail
        """Fetch a single map detail record. Return None and print on failure."""
        detail_response = mistapi.api.v1.sites.maps.getSiteMap(
            self.apisession, site_id=site_id, map_id=map_id
        )  # API call for map details.
        if detail_response.status_code != 200:  # Any non-200 is a failure to fetch.
            print(f"\n! Failed to fetch map details: {detail_response.status_code}")  # Surface HTTP error.
            return None  # Signal failure to caller.
        return detail_response.data  # Parsed map payload.

    def _print_map_detail_body(self, map_details: dict) -> None:  # WHY: declare private helper _print_map_detail_body
        """Print the formatted map-detail body block."""
        print(f"\n{'-' * 80}")  # Leading rule.
        print(f"MAP DETAILS: {map_details.get('name', 'Unnamed')}")  # Section title with map name.
        print(f"{'-' * 80}")  # Rule beneath title.
        print(f"Map ID: {map_details.get('id', 'N/A')}")  # Map identifier.
        print(f"Type: {map_details.get('type', 'N/A')}")  # Map type (image/google/baidu).
        print(f"Width: {map_details.get('width', 0)} pixels")  # Width in pixels.
        print(f"Height: {map_details.get('height', 0)} pixels")  # Height in pixels.
        print(f"PPM (Pixels per meter): {map_details.get('ppm', 'N/A')}")  # Scale in pixels per meter.
        print(f"Orientation: {map_details.get('orientation', 0)} degrees")  # Rotation orientation.
        print(f"Has Image: {'Yes' if 'url' in map_details else 'No'}")  # Whether a background image is set.
        self._print_map_optional_fields(map_details)  # Optional URL/coords/wayfinding fields.
        print(f"{'-' * 80}")  # Trailing rule.

    def _run_view_map_details(
        self, site_id: str, site_name: str
    ) -> None:  # WHY: declare private helper _run_view_map_details
        """Execute the interactive view-map-details flow for a site."""
        map_id, _ = self._select_map_with_list(site_id, site_name)  # Prompt user to pick a map.
        if not map_id:  # User cancelled selection.
            return  # Nothing to display.
        map_details = self._fetch_map_detail(site_id, map_id)  # Load the map record.
        if map_details is None:  # API call failed and already printed reason.
            return  # Nothing to display.
        self._print_map_detail_body(map_details)  # Emit the formatted body.
        logging.info("Viewed details for map %s", map_id)  # Audit log of the view.

    def view_map_details(self):  # WHY: declare public method view_map_details
        """View detailed information for a specific map."""
        self._print_view_map_details_header()  # Section banner.
        site_id, site_name = self.get_current_site()  # Resolve currently selected site.
        if not site_id:  # No site selected -> nothing to do.
            return  # WHY: return early
        try:
            self._run_view_map_details(site_id, site_name)  # Delegate the flow to the helper.
        except Exception as e:  # Catch-all so the menu keeps running.
            logging.exception("Error viewing map details: %s", e)  # Log full trace for triage.
            print(f"\n! Error viewing map details: {e}")  # Surface error to the operator.

    def _prompt_map_name(self) -> str | None:  # WHY: declare private helper _prompt_map_name
        """Prompt user for a map name. Return None if empty or EOF."""
        try:
            map_name = InputUtils.safe_input(
                "Enter map name: ", context="_prompt_map_name"
            ).strip()  # WHY: compute map_name
        except EOFError:  # WHY: handle expected error
            logging.info("EOF detected during map name input")  # WHY: action-log before operation
            return None  # WHY: return computed result
        if not map_name:  # WHY: guard against missing precondition
            print("\n! Map name is required")  # WHY: surface user-facing message
            return None  # WHY: return computed result
        return map_name  # WHY: return computed result

    def _prompt_map_type(self) -> str:  # WHY: declare private helper _prompt_map_type
        """Display map type options and return the selected type string."""
        print("\nMap type options:")  # WHY: surface user-facing message
        print("  1. image (standard floor plan)")  # WHY: surface user-facing message
        print("  2. google (Google Maps integration)")  # WHY: surface user-facing message
        print("  3. baidu (Baidu Maps integration)")  # WHY: surface user-facing message
        type_choice = (
            InputUtils.safe_input("Select type (1-3, default=1): ", context="_prompt_map_type").strip() or "1"
        )  # WHY: compute type_choice
        type_map = {"1": "image", "2": "google", "3": "baidu"}  # WHY: compute type_map
        return type_map.get(type_choice, "image")  # WHY: return computed result

    def _prompt_image_dimensions(
        self,
    ) -> tuple[int, int, float]:  # WHY: declare private helper _prompt_image_dimensions
        """Prompt for image map dimensions. Return (width, height, ppm) with defaults."""
        width_input = InputUtils.safe_input(  # WHY: compute width_input
            "Enter width in pixels (default=1024): ", context="_prompt_image_dimensions"
        ).strip()
        height_input = InputUtils.safe_input(  # WHY: compute height_input
            "Enter height in pixels (default=768): ", context="_prompt_image_dimensions"
        ).strip()
        ppm_input = InputUtils.safe_input(  # WHY: compute ppm_input
            "Enter pixels per meter (default=10): ", context="_prompt_image_dimensions"
        ).strip()
        width = int(width_input) if width_input else 1024  # WHY: compute width
        height = int(height_input) if height_input else 768  # WHY: compute height
        ppm = float(ppm_input) if ppm_input else 10.0  # WHY: compute ppm
        return width, height, ppm  # WHY: return computed result

    def _print_map_creation_success(
        self, created_map: dict, site_id: str
    ) -> None:  # WHY: declare private helper _print_map_creation_success
        """Print the success banner and log the created map identifier."""
        print(f"\n{'-' * 80}")  # WHY: surface user-facing message
        print("Map created successfully!")  # WHY: surface user-facing message
        print(f"Map ID: {created_map.get('id')}")  # WHY: surface user-facing message
        print(f"Name: {created_map.get('name')}")  # WHY: surface user-facing message
        print(f"Type: {created_map.get('type')}")  # WHY: surface user-facing message
        print(f"{'-' * 80}")  # WHY: surface user-facing message
        logging.info("Created map %s for site %s", created_map.get("id"), site_id)  # WHY: action-log before operation

    def _build_and_create_map(
        self, site_id: str, map_name: str, map_type: str
    ) -> None:  # WHY: declare private helper _build_and_create_map
        """Build map payload, call API, and print the result."""
        try:
            map_payload: dict[str, Any] = {"name": map_name, "type": map_type}  # WHY: assign computed value
            if map_type == "image":  # WHY: branch on condition
                width, height, ppm = self._prompt_image_dimensions()  # WHY: compute width
                map_payload.update({"width": width, "height": height, "ppm": ppm})  # WHY: advance computation
            print(f"\nCreating map '{map_name}'...")  # WHY: surface user-facing message
            response = mistapi.api.v1.sites.maps.createSiteMap(
                self.apisession, site_id=site_id, body=map_payload
            )  # WHY: compute response
            if response.status_code in [200, 201]:  # WHY: branch on condition
                self._print_map_creation_success(response.data, site_id)  # WHY: advance computation
            else:
                print(f"\n! Failed to create map: HTTP {response.status_code}")  # WHY: surface user-facing message
                logging.error(
                    "Map creation failed: %s - %s", response.status_code, response.data
                )  # WHY: surface fatal issue
        except ValueError as ve:  # WHY: handle expected error
            print(f"\n! Invalid input: {ve}")  # WHY: surface user-facing message

    def create_site_map(self):  # WHY: declare public method create_site_map
        """Create a new site map with basic configuration."""
        print("\n" + "-" * 80)  # WHY: surface user-facing message
        print("CREATE NEW SITE MAP")  # WHY: surface user-facing message
        print("-" * 80)  # WHY: surface user-facing message
        print(
            "\n! Note: This creates a map placeholder. Upload image separately (Menu 7)"
        )  # WHY: surface user-facing message

        site_id, site_name = self.get_current_site()  # WHY: compute site_id
        if not site_id:  # WHY: guard against missing precondition
            return  # WHY: return early

        try:
            print(f"\nCreating map for site: {site_name}")  # WHY: surface user-facing message
            print(f"{'-' * 80}")  # WHY: surface user-facing message
            map_name = self._prompt_map_name()  # WHY: compute map_name
            if not map_name:  # WHY: guard against missing precondition
                return  # WHY: return early
            map_type = self._prompt_map_type()  # WHY: compute map_type
            self._build_and_create_map(site_id, map_name, map_type)  # WHY: advance computation
        except Exception as e:  # WHY: handle expected error
            logging.exception("Error creating site map: %s", e)  # WHY: capture exception with traceback
            print(f"\n! Error creating map: {e}")  # WHY: surface user-facing message

    def clone_map(self):  # WHY: declare public method clone_map
        """Delegating wrapper: clone lives in src.maps._maps_clone."""
        # Wrapper kept so run_interactive_menu's dispatch table -
        # which references self.clone_map - continues to resolve
        # without touching the menu builder.
        from src.maps._maps_clone import clone_map  # WHY: import required module

        return clone_map(self)  # WHY: return computed result

    def intelligent_map_replacement_wizard(self):  # WHY: declare public method intelligent_map_replacement_wizard
        """Menu entry point: delegate to the extracted wizard module."""
        # Wrapper kept so run_interactive_menu's dispatch table -
        # which references self.intelligent_map_replacement_wizard -
        # continues to resolve without touching the menu builder.
        from src.maps._maps_wizard import run_wizard  # WHY: import required module

        return run_wizard(self)  # WHY: return computed result

    @staticmethod
    def _build_map_without_image_record(
        site: dict, map_item: dict, org_id: str
    ) -> dict:  # WHY: declare private helper _build_map_without_image_record
        """Flatten a (site, map) pair lacking a url field into a report row."""
        return {  # WHY: return computed result
            "site_id": site["id"],
            "site_name": site.get("name", "Unknown"),
            "map_id": map_item.get("id"),
            "map_name": map_item.get("name", "Unnamed"),
            "type": map_item.get("type", "N/A"),
            "width": map_item.get("width", 0),
            "height": map_item.get("height", 0),
            "org_id": org_id,
        }

    def _scan_site_missing_image_maps(
        self, site: dict
    ) -> tuple[list, int]:  # WHY: declare private helper _scan_site_missing_image_maps
        """Return (rows without url, total scanned) for a single site."""
        try:
            resp = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site["id"])  # API
        except Exception as e:  # WHY: handle expected error
            logging.debug("Error scanning site %s: %s", site["id"], e)  # Skip failed sites but log
            return [], 0  # Contribute nothing on failure
        if resp.status_code != 200:  # Non-success HTTP
            return [], 0  # Skip this site but keep scanning
        maps = resp.data  # Full map list for the site
        rows = [
            self._build_map_without_image_record(site, m, self.org_id) for m in maps if "url" not in m
        ]  # WHY: compute rows
        return rows, len(maps)  # Rows for maps missing images + total map count

    def _collect_maps_missing_images(
        self, sites: list
    ) -> tuple[list, int]:  # WHY: declare private helper _collect_maps_missing_images
        """Scan every site's maps. Return (rows without url, total scanned)."""
        rows: list = []  # Accumulated rows across all sites
        total = 0  # Running total of maps scanned
        for site in tqdm(sites, desc="Scanning sites", unit="site"):  # Progress-visible iteration
            site_rows, site_total = self._scan_site_missing_image_maps(site)  # Per-site delegation
            rows.extend(site_rows)  # Accumulate rows
            total += site_total  # Accumulate scanned count
        return rows, total  # WHY: return computed result

    @staticmethod
    def _render_maps_without_images_table(
        rows: list,
    ) -> None:  # WHY: declare private helper _render_maps_without_images_table
        """Print the (site, map, type) table for the report."""
        print(f"\n{'-' * 80}")  # WHY: surface user-facing message
        print(f"MAPS WITHOUT IMAGES: {len(rows)} found")  # WHY: surface user-facing message
        print(f"{'-' * 80}")  # WHY: surface user-facing message
        print(f"{'Site Name':<30} {'Map Name':<30} {'Type':<15}")  # WHY: surface user-facing message
        print(f"{'-' * 80}")  # WHY: surface user-facing message
        for map_item in rows:  # WHY: iterate collection
            site_name = map_item["site_name"][:29]  # WHY: compute site_name
            map_name = map_item["map_name"][:29]  # WHY: compute map_name
            map_type = map_item["type"][:14]  # WHY: compute map_type
            print(f"{site_name:<30} {map_name:<30} {map_type:<15}")  # WHY: surface user-facing message
        print(f"{'-' * 80}")  # WHY: surface user-facing message

    def _print_all_maps_have_images(
        self, total: int
    ) -> None:  # WHY: declare private helper _print_all_maps_have_images
        """Emit the banner shown when every scanned map already has an image."""
        print("\n" + "-" * 80)  # WHY: surface user-facing message
        print(f"All {total} maps have images uploaded!")  # WHY: surface user-facing message
        print("-" * 80)  # WHY: surface user-facing message

    def maps_without_images_report(self):  # WHY: declare public method maps_without_images_report
        """Generate report of maps that do not have uploaded images."""
        print("\n" + "-" * 80)  # WHY: surface user-facing message
        print("MAPS WITHOUT IMAGES REPORT")  # WHY: surface user-facing message
        print("-" * 80)  # WHY: surface user-facing message
        try:
            sites = self._fetch_sites()  # WHY: compute sites
            if not sites:  # WHY: guard against missing precondition
                print("\n! No sites found in organization")  # WHY: surface user-facing message
                return  # WHY: return early
            print(f"\nScanning {len(sites)} sites for maps without images...")  # WHY: surface user-facing message
            rows, total = self._collect_maps_missing_images(sites)  # WHY: compute rows
            print(f"\nTotal maps scanned: {total}")  # WHY: surface user-facing message
            if not rows:  # WHY: guard against missing precondition
                self._print_all_maps_have_images(total)  # WHY: advance computation
                return  # WHY: return early
            self._render_maps_without_images_table(rows)  # WHY: advance computation
            write_data_with_format_selection(
                rows, "MapsWithoutImages_Report", api_function_name="listSiteMaps"
            )  # WHY: assign computed value
            logging.info("Generated report: %s maps without images", len(rows))  # WHY: action-log before operation
        except Exception as e:  # WHY: handle expected error
            logging.exception("Error generating maps report: %s", e)  # WHY: capture exception with traceback
            print(f"\n! Error generating report: {e}")  # WHY: surface user-facing message

    # Placeholder methods for future implementation
    def _collect_property_input(
        self, prompt, current_value, value_type=str
    ):  # WHY: declare private helper _collect_property_input
        """Collect a single property update from user with type validation."""
        raw = InputUtils.safe_input(
            f"{prompt} [{current_value}]: ", context="_collect_property_input"
        ).strip()  # WHY: compute raw
        if not raw:  # WHY: guard against missing precondition
            return None  # WHY: return computed result
        if value_type is str:  # WHY: branch on condition
            return raw  # WHY: return computed result
        try:
            return value_type(raw)  # WHY: return computed result
        except ValueError:  # WHY: handle expected error
            print("! Invalid value, skipping")  # WHY: surface user-facing message
            return None  # WHY: return computed result

    def _collect_map_updates(self, current_map):  # WHY: declare private helper _collect_map_updates
        """Collect all map property updates from user input."""
        print("\nEnter new values (press Enter to keep current value):")  # WHY: surface user-facing message
        fields = [  # WHY: compute fields
            ("name", "Map name", current_map.get("name", ""), str),
            ("width", "Width in pixels", current_map.get("width", ""), int),
            ("height", "Height in pixels", current_map.get("height", ""), int),
            ("ppm", "Pixels per meter", current_map.get("ppm", ""), float),
            ("orientation", "Orientation in degrees", current_map.get("orientation", 0), int),
        ]
        payload = {}  # WHY: compute payload
        for key, label, current, vtype in fields:  # WHY: iterate collection
            value = self._collect_property_input(label, current, vtype)  # WHY: compute value
            if value is not None:  # WHY: branch on condition
                payload[key] = value  # WHY: compute payload
        return payload  # WHY: return computed result

    @staticmethod
    def _print_map_update_preview(
        update_payload: dict,
    ) -> None:  # WHY: declare private helper _print_map_update_preview
        """Print the preview block listing pending map property changes."""
        print(f"\n{'-' * 80}")  # Preview banner top.
        print("Changes to apply:")  # Section label.
        for key, value in update_payload.items():  # Show each changed key.
            print(f"  {key}: {value}")  # Indented key/value pair.
        print(f"{'-' * 80}")  # Preview banner bottom.

    def _apply_map_update(
        self, site_id: str, map_id: str, update_payload: dict
    ) -> None:  # WHY: declare private helper _apply_map_update
        """Invoke the update API and print the outcome."""
        print("\nApplying changes...")  # User-visible progress note.
        update_response = mistapi.api.v1.sites.maps.updateSiteMap(
            self.apisession, site_id=site_id, map_id=map_id, body=update_payload
        )  # PUT the update payload.
        if update_response.status_code in [200, 201]:  # HTTP success codes.
            print(f"\n{'-' * 80}")  # Success banner top.
            print("Map updated successfully!")  # User-visible confirmation.
            print(f"{'-' * 80}")  # Success banner bottom.
            logging.info("Updated map %s for site %s", map_id, site_id)  # Audit log.
            return  # Success path complete.
        print(f"\n! Failed to update map: HTTP {update_response.status_code}")  # Report failure.
        logging.error("Map update failed: %s", update_response.status_code)  # Log HTTP error.

    def _confirm_and_apply_map_update(
        self, site_id: str, map_id: str, update_payload: dict
    ) -> None:  # WHY: declare private helper _confirm_and_apply_map_update
        """Prompt user to confirm and then apply the map property update via API."""
        self._print_map_update_preview(update_payload)  # Show pending change preview.
        confirm = (
            InputUtils.safe_input("\nApply these changes? (yes/no): ", context="_confirm_and_apply_map_update")
            .strip()
            .lower()
        )  # Explicit yes/no confirmation.
        if confirm not in ["yes", "y"]:  # User declined.
            print("\n! Update cancelled")  # Note cancellation.
            return  # Do not call the API.
        self._apply_map_update(site_id, map_id, update_payload)  # Perform the update.

    @staticmethod
    def _render_current_map_properties(
        current_map: dict,
    ) -> None:  # WHY: declare private helper _render_current_map_properties
        """Print the current-map properties block used by the update flow."""
        print("\nCurrent Map Properties:")  # WHY: surface user-facing message
        print(f"{'-' * 80}")  # WHY: surface user-facing message
        for label, key in [("Name", "name"), ("Type", "type")]:  # WHY: iterate collection
            print(f"{label}: {current_map.get(key, 'N/A')}")  # WHY: surface user-facing message
        print(f"Width: {current_map.get('width', 'N/A')} pixels")  # WHY: surface user-facing message
        print(f"Height: {current_map.get('height', 'N/A')} pixels")  # WHY: surface user-facing message
        print(f"PPM (Pixels per meter): {current_map.get('ppm', 'N/A')}")  # WHY: surface user-facing message
        print(f"Orientation: {current_map.get('orientation', 0)} degrees")  # WHY: surface user-facing message
        print(f"{'-' * 80}")  # WHY: surface user-facing message

    def _load_map_for_update(
        self, site_id: str, site_name: str
    ) -> "tuple[str, dict] | None":  # WHY: declare private helper _load_map_for_update
        """Pick a map and fetch its current state. None if user cancels or fetch fails."""
        map_id = self._select_map_from_site(site_id, site_name)  # WHY: compute map_id
        if not map_id:  # WHY: guard against missing precondition
            return None  # WHY: return computed result
        resp = mistapi.api.v1.sites.maps.getSiteMap(
            self.apisession, site_id=site_id, map_id=map_id
        )  # WHY: compute resp
        if resp.status_code != 200:  # WHY: branch on condition
            print(f"\n! Failed to fetch map details: HTTP {resp.status_code}")  # WHY: surface user-facing message
            return None  # WHY: return computed result
        return map_id, resp.data  # WHY: return computed result

    @staticmethod
    def _print_update_map_properties_header() -> (
        None
    ):  # WHY: declare private helper _print_update_map_properties_header
        """Print the banner shown by the update-map-properties action."""
        print("\n" + "-" * 80)  # Top rule
        print("UPDATE MAP PROPERTIES")  # Title
        print("-" * 80)  # Bottom rule

    def _run_update_map_properties(
        self, site_id: str, site_name: str
    ) -> None:  # WHY: declare private helper _run_update_map_properties
        """Execute the update flow after site selection and header."""
        loaded = self._load_map_for_update(site_id, site_name)  # Pick a map and fetch its current state
        if loaded is None:  # User cancelled or fetch failed
            return  # Nothing further to do
        map_id, current_map = loaded  # Unpack the selected map
        self._render_current_map_properties(current_map)  # Show existing values
        update_payload = self._collect_map_updates(current_map)  # Prompt for changes
        if not update_payload:  # No fields were modified
            print("\n! No changes specified")  # Inform the operator
            return  # Skip the no-op update
        self._confirm_and_apply_map_update(site_id, map_id, update_payload)  # Confirm + PUT

    def update_map_properties(self):  # WHY: declare public method update_map_properties
        """Update existing map properties (name, dimensions, orientation, and so on)."""
        self._print_update_map_properties_header()  # Banner
        site_id, site_name = self.get_current_site()  # Require a selected site
        if not site_id:  # Site prompt cancelled
            return  # WHY: return early
        try:
            self._run_update_map_properties(site_id, site_name)  # Execute the update flow
        except EOFError:  # WHY: handle expected error
            logging.info("EOF detected during map update")  # Non-interactive shutdown
            return  # WHY: return early
        except Exception as e:  # WHY: handle expected error
            logging.exception("Error updating map properties: %s", e)  # Log for diagnosis
            print(f"\n! Error updating map: {e}")  # Surface to operator

    def _fetch_map_for_delete(
        self, site_id: str, map_id: str
    ) -> dict | None:  # WHY: declare private helper _fetch_map_for_delete
        """Fetch current map or print HTTP error and return None on failure."""
        resp = mistapi.api.v1.sites.maps.getSiteMap(
            self.apisession, site_id=site_id, map_id=map_id
        )  # WHY: compute resp
        if resp.status_code != 200:  # WHY: branch on condition
            print(f"\n! Failed to fetch map details: HTTP {resp.status_code}")  # WHY: surface user-facing message
            return None  # WHY: return computed result
        return resp.data  # WHY: return computed result

    @staticmethod
    def _render_map_delete_preview(
        current_map: dict, map_id: str
    ) -> None:  # WHY: declare private helper _render_map_delete_preview
        """Print the (name, type, id) preview shown before delete confirmation."""
        print(f"\n{'-' * 80}")  # WHY: surface user-facing message
        print("Map to be deleted:")  # WHY: surface user-facing message
        print(f"  Name: {current_map.get('name', 'N/A')}")  # WHY: surface user-facing message
        print(f"  Type: {current_map.get('type', 'N/A')}")  # WHY: surface user-facing message
        print(f"  ID: {map_id}")  # WHY: surface user-facing message
        print(f"{'-' * 80}")  # WHY: surface user-facing message

    @staticmethod
    def _confirm_map_delete(map_id: str) -> bool:  # WHY: declare private helper _confirm_map_delete
        """Require user to type DELETE in uppercase. True iff they confirmed."""
        print("\nType 'DELETE' in uppercase to confirm deletion:")  # WHY: surface user-facing message
        confirmation = InputUtils.safe_input(
            "Confirmation: ", context="delete_site_map"
        ).strip()  # WHY: compute confirmation
        if confirmation != "DELETE":  # WHY: branch on condition
            print("\n! Deletion cancelled")  # WHY: surface user-facing message
            logging.info("Map deletion cancelled by user for map %s", map_id)  # WHY: action-log before operation
            return False  # WHY: return computed result
        return True  # WHY: return computed result

    def _perform_map_delete(self, site_id: str, map_id: str) -> None:  # WHY: declare private helper _perform_map_delete
        """Call deleteSiteMap and report success/failure to the user."""
        print("\nDeleting map...")  # WHY: surface user-facing message
        resp = mistapi.api.v1.sites.maps.deleteSiteMap(
            self.apisession, site_id=site_id, map_id=map_id
        )  # WHY: compute resp
        if resp.status_code in [200, 204]:  # WHY: branch on condition
            print(f"\n{'-' * 80}")  # WHY: surface user-facing message
            print("Map deleted successfully!")  # WHY: surface user-facing message
            print(f"{'-' * 80}")  # WHY: surface user-facing message
            logging.info("Deleted map %s from site %s", map_id, site_id)  # WHY: action-log before operation
        else:
            print(f"\n! Failed to delete map: HTTP {resp.status_code}")  # WHY: surface user-facing message
            logging.error("Map deletion failed: %s - %s", resp.status_code, resp.data)  # WHY: surface fatal issue

    @staticmethod
    def _print_delete_site_map_header() -> None:  # WHY: declare private helper _print_delete_site_map_header
        """Print the banner and warning for the delete-site-map flow."""
        print("\n" + "-" * 80)  # Section banner top rule.
        print("DELETE SITE MAP")  # Section title.
        print("-" * 80)  # Section banner bottom rule.
        print("\n! WARNING: This action cannot be undone!")  # Destructive-action warning.

    def _run_delete_site_map(
        self, site_id: str, site_name: str
    ) -> None:  # WHY: declare private helper _run_delete_site_map
        """Execute the interactive delete flow for the currently selected site."""
        map_id = self._select_map_from_site(site_id, site_name)  # Prompt for map to delete.
        if not map_id:  # User cancelled selection.
            return  # Nothing to delete.
        current_map = self._fetch_map_for_delete(site_id, map_id)  # Load current record.
        if current_map is None:  # Fetch failed and already printed reason.
            return  # Abort.
        self._render_map_delete_preview(current_map, map_id)  # Show what will be deleted.
        if not self._confirm_map_delete(map_id):  # Explicit confirmation prompt.
            return  # User declined.
        self._perform_map_delete(site_id, map_id)  # Perform DELETE call.

    def delete_site_map(self):  # WHY: declare public method delete_site_map
        """Delete a site map with confirmation."""
        self._print_delete_site_map_header()  # Section banner + warning.
        site_id, site_name = self.get_current_site()  # Resolve currently selected site.
        if not site_id:  # No site selected -> nothing to do.
            return  # WHY: return early
        try:
            self._run_delete_site_map(site_id, site_name)  # Delegate the flow.
        except EOFError:  # User hit Ctrl-D at a prompt.
            logging.info("EOF detected during map deletion")  # Log soft abort.
            return  # Return to caller.
        except Exception as e:  # Catch-all so the menu keeps running.
            logging.exception("Error deleting site map: %s", e)  # Log full traceback.
            print(f"\n! Error deleting map: {e}")  # Surface error to operator.

    @staticmethod
    def _read_image_path_input() -> str:  # WHY: declare private helper _read_image_path_input
        """Prompt the user for an image file path and normalize the raw value."""
        print("\nEnter the path to the image file:")  # User-visible prompt header.
        print("Supported formats: PNG, JPG, JPEG, GIF, SVG")  # Show supported extensions.
        return (
            InputUtils.safe_input("File path: ", context="_prompt_and_validate_image_path")
            .strip()
            .strip('"')
            .strip("'")
        )  # Strip whitespace + surrounding quotes from pasted paths.

    @staticmethod
    def _validate_image_file_path(
        file_path: str,
    ) -> str | None:  # WHY: declare private helper _validate_image_file_path
        """Validate a filesystem path points at a supported image. Return path or None."""
        if not file_path:  # Empty input -> nothing to validate.
            print("\n! No file path provided")  # Report empty input.
            return None  # WHY: return computed result
        if not os.path.exists(file_path):  # File must actually exist.
            print(f"\n! File not found: {file_path}")  # Report missing path.
            return None  # WHY: return computed result
        if not os.path.isfile(file_path):  # Directories and specials are not accepted.
            print(f"\n! Path is not a file: {file_path}")  # Report wrong kind.
            return None  # WHY: return computed result
        valid_extensions = [".png", ".jpg", ".jpeg", ".gif", ".svg"]  # Allowed image extensions.
        file_ext = os.path.splitext(file_path)[1].lower()  # Extract extension case-insensitively.
        if file_ext not in valid_extensions:  # Reject unsupported types.
            print(f"\n! Invalid file type: {file_ext}")  # Report bad extension.
            print(f"Supported types: {', '.join(valid_extensions)}")  # Restate accepted list.
            return None  # WHY: return computed result
        return file_path  # Path is valid.

    def _prompt_and_validate_image_path(
        self,
    ) -> str | None:  # WHY: declare private helper _prompt_and_validate_image_path
        """Prompt user for image file path and validate it. Return path or None if invalid."""
        return self._validate_image_file_path(self._read_image_path_input())  # Compose read + validate.

    @staticmethod
    def _prompt_yes_no(prompt: str, context: str) -> bool:  # WHY: declare private helper _prompt_yes_no
        """Return True when the user answers yes/y (case-insensitive) at the prompt."""
        return InputUtils.safe_input(prompt, context=context).strip().lower() in [
            "yes",
            "y",
        ]  # WHY: return computed result

    def _check_upload_size(
        self, file_path: str
    ) -> tuple[float, bool]:  # WHY: declare private helper _check_upload_size
        """Compute file size MB and confirm large uploads. Return (size_mb, proceed)."""
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)  # Bytes to megabytes.
        if file_size_mb <= 10:  # Small file -> no extra confirm needed.
            return file_size_mb, True  # WHY: return computed result
        print(f"\n! Warning: File size is {file_size_mb:.2f}MB")  # Alert about large upload.
        proceed = self._prompt_yes_no("Continue with upload? (yes/no): ", "_confirm_image_upload")  # Confirm.
        if not proceed:  # Operator declined.
            print("\n! Upload cancelled")  # Note cancellation.
        return file_size_mb, proceed  # WHY: return computed result

    def _perform_image_upload(
        self, site_id: str, map_id: str, file_path: str
    ) -> None:  # WHY: declare private helper _perform_image_upload
        """Call the addSiteMapImageFile endpoint and print the outcome."""
        print("\nUploading image...")  # Progress note before HTTP call.
        with open(file_path, "rb"):  # Ensure file is readable. API takes path itself.
            upload_response = mistapi.api.v1.sites.maps.addSiteMapImageFile(
                self.apisession, site_id=site_id, map_id=map_id, file=file_path
            )  # Multipart upload of the image asset.
        if upload_response.status_code in [200, 201]:  # HTTP success codes.
            print(f"\n{'-' * 80}")  # Success banner top.
            print("Image uploaded successfully!")  # User-visible confirmation.
            print(f"{'-' * 80}")  # Success banner bottom.
            logging.info("Uploaded image to map %s for site %s", map_id, site_id)  # Audit log.
            return  # Success path complete.
        print(f"\n! Failed to upload image: HTTP {upload_response.status_code}")  # Failure banner.
        logging.error("Image upload failed: %s - %s", upload_response.status_code, upload_response.data)  # Log.

    def _confirm_image_upload(
        self, site_id: str, map_id: str, file_path: str
    ) -> None:  # WHY: declare private helper _confirm_image_upload
        """Warn on large files, confirm upload, and perform the multipart upload."""
        file_size_mb, proceed = self._check_upload_size(file_path)  # Size warning + confirm.
        if not proceed:  # Operator aborted at the size warning.
            return  # WHY: return early
        print(f"\nFile: {os.path.basename(file_path)}")  # Show the basename.
        print(f"Size: {file_size_mb:.2f}MB")  # Show the size.
        if not self._prompt_yes_no(
            "\nUpload this image to the selected map? (yes/no): ", "_confirm_image_upload"
        ):  # Final go/no-go confirmation.
            print("\n! Upload cancelled")  # Note cancellation.
            return  # WHY: return early
        self._perform_image_upload(site_id, map_id, file_path)  # Execute the HTTP upload.

    @staticmethod
    def _print_upload_image_header() -> None:  # WHY: declare private helper _print_upload_image_header
        """Print the banner shown by the upload/replace map image action."""
        print("\n" + "-" * 80)  # Top rule
        print("UPLOAD/REPLACE MAP IMAGE")  # Title
        print("-" * 80)  # Bottom rule

    def _run_upload_map_image(
        self, site_id: str, site_name: str
    ) -> None:  # WHY: declare private helper _run_upload_map_image
        """Execute the upload flow after site selection and header."""
        map_id = self._select_map_from_site(site_id, site_name)  # Prompt for target map
        if not map_id:  # User cancelled the map selection
            return  # WHY: return early
        file_path = self._prompt_and_validate_image_path()  # Prompt for a valid image path
        if not file_path:  # Cancelled or invalid path
            return  # WHY: return early
        self._confirm_image_upload(site_id, map_id, file_path)  # Confirm + POST the multipart upload

    def upload_map_image(self):  # WHY: declare public method upload_map_image
        """Upload or replace map image file (multipart upload)."""
        logging.info("upload_map_image operation initiated")  # Audit trail
        self._print_upload_image_header()  # Banner
        site_id, site_name = self.get_current_site()  # Require a selected site
        if not site_id:  # Site prompt cancelled
            logging.warning("upload_map_image aborted: No site selected")  # Note the abort
            return  # WHY: return early
        logging.debug("upload_map_image - Site: %s (ID: %s)", site_name, site_id)  # Trace context
        try:
            self._run_upload_map_image(site_id, site_name)  # Execute the upload flow
        except EOFError:  # WHY: handle expected error
            logging.info("EOF detected during image upload")  # Non-interactive shutdown
            return  # WHY: return early
        except Exception as e:  # WHY: handle expected error
            logging.exception("Error uploading map image: %s", e)  # Log for diagnosis
            print(f"\n! Error uploading image: {e}")  # Surface to operator

    def _get_devices_on_map(
        self, site_id: str, map_id: str
    ) -> list | None:  # WHY: declare private helper _get_devices_on_map
        """Fetch all site devices and return those placed on the specified map. None on failure."""
        print("\nFetching devices for site...")  # WHY: surface user-facing message
        devices_response = mistapi.api.v1.sites.devices.listSiteDevices(
            self.apisession, site_id=site_id, type="all"
        )  # WHY: compute devices_response
        if devices_response.status_code != 200:  # WHY: branch on condition
            print(
                f"\n! Failed to fetch devices: HTTP {devices_response.status_code}"
            )  # WHY: surface user-facing message
            return None  # WHY: return computed result
        devices_on_map = [d for d in devices_response.data if d.get("map_id") == map_id]  # WHY: compute devices_on_map
        if not devices_on_map:  # WHY: guard against missing precondition
            print("\n! No devices placed on this map")  # WHY: surface user-facing message
            return None  # WHY: return computed result
        return devices_on_map  # WHY: return computed result

    def _export_map_devices_csv(
        self, devices: list, site_id: str, site_name: str
    ) -> None:  # WHY: declare private helper _export_map_devices_csv
        """Flatten and export the given device list to CSV/data output."""
        devices_data = []  # WHY: compute devices_data
        for device in devices:  # WHY: iterate collection
            flattened = flatten_dict_recursively(device)  # WHY: compute flattened
            flattened["site_id"] = site_id  # WHY: assign computed value
            flattened["site_name"] = site_name  # WHY: assign computed value
            devices_data.append(flattened)  # WHY: advance computation
        filename = f"MapDevices_{sanitize_filename(site_name or 'unknown_site')}"  # WHY: compute filename
        write_data_with_format_selection(
            devices_data, filename, api_function_name="listSiteDevices"
        )  # WHY: assign computed value
        print(f"\n   Exported {len(devices_data)} devices")  # WHY: surface user-facing message

    def view_devices_on_map(self):  # WHY: declare public method view_devices_on_map
        """Display all devices placed on a specific map."""
        self._print_view_devices_header()  # Uniform banner for the interactive section.
        site_id, site_name = self.get_current_site()  # Resolve currently-selected site context.
        if not site_id:  # Guard clause: no site chosen, nothing to display.
            return  # WHY: return early
        try:
            self._run_view_devices_flow(site_id, site_name)  # Delegate the interactive body to a helper.
        except EOFError:  # WHY: handle expected error
            logging.info("EOF detected during view devices")  # Silent EOF exit for scripted sessions.
        except Exception as e:  # WHY: handle expected error
            logging.exception("Error viewing devices on map: %s", e)  # Full stack for post-mortem debugging.
            print(f"\n! Error viewing devices: {e}")  # User-facing summary of the failure.

    @staticmethod
    def _print_view_devices_header() -> None:  # WHY: declare private helper _print_view_devices_header
        """Print the section banner for view_devices_on_map."""
        print("\n" + "-" * 80)  # Visual break before the section.
        print("VIEW DEVICES ON MAP")  # Section title.
        print("-" * 80)  # Trailing divider.

    def _run_view_devices_flow(
        self, site_id: str, site_name: str
    ) -> None:  # WHY: declare private helper _run_view_devices_flow
        """Interactive body of view_devices_on_map after site is resolved."""
        map_id = self._select_map_from_site(site_id, site_name)  # Prompt user to pick a map from the site.
        if not map_id:  # Guard clause: cancelled or no maps available.
            return  # WHY: return early
        devices_on_map = self._get_devices_on_map(site_id, map_id)  # Fetch placed devices for the map.
        if not devices_on_map:  # Guard clause: no devices, nothing to show.
            return  # WHY: return early
        self._print_devices_table(devices_on_map)  # Render the tabular device listing.
        self._maybe_export_map_devices(devices_on_map, site_id, site_name)  # Optional CSV export step.
        logging.info("Viewed %s devices on map %s", len(devices_on_map), map_id)  # Audit trail entry.

    @staticmethod
    def _print_devices_table(devices_on_map: list) -> None:  # WHY: declare private helper _print_devices_table
        """Render the devices-on-map table body."""
        print(f"\n{'-' * 80}")  # Divider before the table.
        print(f"Devices on Map: {len(devices_on_map)} found")  # Row-count summary line.
        print(f"{'-' * 80}")  # Divider between summary and header row.
        print(f"{'Device Name':<30} {'Type':<10} {'Model':<20} {'X,Y Coordinates':<20}")  # Column header.
        print(f"{'-' * 80}")  # Divider under header.
        for device in devices_on_map:  # Emit one padded row per device.
            device_name = device.get("name", "Unnamed")[:29]  # Truncate name to fit column width.
            device_type = device.get("type", "N/A")[:9]  # Truncate type to fit column width.
            device_model = device.get("model", "N/A")[:19]  # Truncate model to fit column width.
            coordinates = f"{device.get('x', 'N/A')},{device.get('y', 'N/A')}"  # Compact X,Y coord string.
            print(f"{device_name:<30} {device_type:<10} {device_model:<20} {coordinates:<20}")  # Padded row.
        print(f"{'-' * 80}")  # Divider closing the table.

    def _maybe_export_map_devices(
        self, devices_on_map: list, site_id: str, site_name: str
    ) -> None:  # WHY: declare private helper _maybe_export_map_devices
        """Prompt for and optionally perform CSV export of the device listing."""
        answer = (
            InputUtils.safe_input(
                "\nExport to CSV? (yes/no): ",
                context="view_devices_on_map",
            )
            .strip()
            .lower()
        )  # Normalize the user's reply for comparison.
        if answer in ("yes", "y"):  # Only export on affirmative reply.
            self._export_map_devices_csv(devices_on_map, site_id, site_name)  # Delegate CSV writing.

    def auto_place_aps(self):  # WHY: declare public method auto_place_aps
        """Automatically place APs on map using Mist auto-placement."""
        print("\n! Feature coming soon: Auto-place APs")  # WHY: surface user-facing message
        logging.info("auto_place_aps called (placeholder)")  # WHY: action-log before operation

    def auto_orient_aps(self):  # WHY: declare public method auto_orient_aps
        """Automatically orient APs on map."""
        print("\n! Feature coming soon: Auto-orient APs")  # WHY: surface user-facing message
        logging.info("auto_orient_aps called (placeholder)")  # WHY: action-log before operation

    def set_device_location(self):  # WHY: declare public method set_device_location
        """Manually set AP/device coordinates on map."""
        print("\n! Feature coming soon: Set device location")  # WHY: surface user-facing message
        logging.info("set_device_location called (placeholder)")  # WHY: action-log before operation

    def _fetch_site_maps_with_images(
        self, site_id: str
    ) -> "list | None":  # WHY: declare private helper _fetch_site_maps_with_images
        """Return the site's maps that have an image URL, or None on HTTP failure."""
        resp = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site_id)  # API list
        if resp.status_code != 200:  # HTTP failure
            return None  # Signal failure
        return [m for m in resp.data if "url" in m]  # Filter to maps that carry an image

    def _download_all_site_map_images(
        self, site: dict, base_dir: str
    ) -> tuple[int, int]:  # WHY: declare private helper _download_all_site_map_images
        """Download all map images for a single site. Return (downloaded, total_with_images)."""
        site_id = site["id"]  # Site identifier
        site_name = site.get("name", "Unknown")  # Human-friendly folder name
        try:
            maps_with_images = self._fetch_site_maps_with_images(site_id)  # Fetch downloadable maps
            if not maps_with_images:  # None on HTTP failure or empty list
                return 0, 0  # No downloads recorded
            site_dir = os.path.join(base_dir, sanitize_filename(site_name))  # Per-site output folder
            os.makedirs(site_dir, exist_ok=True)  # Ensure destination exists
            downloaded = sum(
                1 for m in maps_with_images if self._download_single_map_image(m, site_dir)
            )  # WHY: compute downloaded
            return downloaded, len(maps_with_images)  # Counts for the summary
        except Exception as error:  # WHY: handle expected error
            logging.debug("Error processing site %s: %s", site_id, error)  # Log and continue outer loop
            return 0, 0  # Site contributed no downloads

    @staticmethod
    def _print_bulk_download_header() -> None:  # WHY: declare private helper _print_bulk_download_header
        """Print the banner for the bulk-download-org-images flow."""
        print("\n" + "-" * 80)  # Section banner top rule.
        print("BULK DOWNLOAD ORG MAP IMAGES")  # Section title.
        print("-" * 80)  # Section banner bottom rule.

    @staticmethod
    def _print_bulk_download_summary(
        total_downloaded: int, total_maps: int, base_dir: str
    ) -> None:  # WHY: declare private helper _print_bulk_download_summary
        """Print the tally at the end of a bulk-download run."""
        print(f"\n{'-' * 80}")  # Summary banner top.
        print("Download completed!")  # Completion note.
        print(f"Total maps found: {total_maps}")  # Total maps scanned across sites.
        print(f"Successfully downloaded: {total_downloaded}")  # Downloaded count.
        print(f"Location: {base_dir}")  # Target directory used.
        print(f"{'-' * 80}")  # Summary banner bottom.

    def _run_bulk_download_org_images(self) -> None:  # WHY: declare private helper _run_bulk_download_org_images
        """Scan all sites and download every map image found."""
        sites = self._fetch_sites()  # Load org sites.
        if not sites:  # Nothing to scan.
            print("\n! No sites found in organization")  # User-visible empty message.
            return  # WHY: return early
        print(f"\nScanning {len(sites)} sites for maps with images...")  # Progress note.
        base_dir = os.path.join("data", "map_images_org_backup")  # Root output dir.
        os.makedirs(base_dir, exist_ok=True)  # Ensure directory exists.
        total_maps = 0  # Running count of maps scanned.
        total_downloaded = 0  # Running count of successful downloads.
        for site in tqdm(sites, desc="Processing sites", unit="site"):  # Progress bar over sites.
            downloaded, found = self._download_all_site_map_images(site, base_dir)  # Per-site work.
            total_downloaded += downloaded  # Accumulate downloaded count.
            total_maps += found  # Accumulate found count.
        self._print_bulk_download_summary(total_downloaded, total_maps, base_dir)  # Print tally.
        logging.info(
            "Bulk downloaded %s of %s map images to %s", total_downloaded, total_maps, base_dir
        )  # Audit log of the batch.

    def bulk_download_org_images(self):  # WHY: declare public method bulk_download_org_images
        """Download all map images across entire organization."""
        self._print_bulk_download_header()  # Section banner.
        try:
            self._run_bulk_download_org_images()  # Delegate the flow.
        except Exception as e:  # Catch-all so menu keeps running.
            logging.exception("Error bulk downloading map images: %s", e)  # Log full traceback.
            print(f"\n! Error during bulk download: {e}")  # Surface error to operator.

    def backup_all_maps(self):  # WHY: declare public method backup_all_maps
        """Complete backup of all maps (metadata + images)."""
        print("\n! Feature coming soon: Backup all maps")  # WHY: surface user-facing message
        logging.info("backup_all_maps called (placeholder)")  # WHY: action-log before operation

    def map_coverage_analytics(self):  # WHY: declare public method map_coverage_analytics
        """Analyze RF coverage patterns by map."""
        print("\n! Feature coming soon: Map coverage analytics")  # WHY: surface user-facing message
        logging.info("map_coverage_analytics called (placeholder)")  # WHY: action-log before operation

    def device_density_analytics(self):  # WHY: declare public method device_density_analytics
        """Analyze device density and distribution by map."""
        print("\n! Feature coming soon: Device density analytics")  # WHY: surface user-facing message
        logging.info("device_density_analytics called (placeholder)")  # WHY: action-log before operation

    def map_usage_statistics(self):  # WHY: declare public method map_usage_statistics
        """Generate usage statistics for maps."""
        print("\n! Feature coming soon: Map usage statistics")  # WHY: surface user-facing message
        logging.info("map_usage_statistics called (placeholder)")  # WHY: action-log before operation

    def _install_required_visualization_packages(
        self, import_mgr, required: dict
    ) -> None:  # WHY: declare private helper _install_required_visualization_packages
        """Probe/install each required visualization package via the import manager."""
        for package_name, package_spec in required.items():  # WHY: iterate collection
            logging.debug(
                "Checking required package: %s (%s)", package_name, package_spec
            )  # WHY: action-log after operation
            import_mgr.import_module_safely(  # WHY: advance computation
                package_name, package_spec=package_spec, required=False, skip_deps=False, skip_upgrade=True
            )
            logging.debug("Package %s check completed", package_name)  # WHY: action-log after operation

    def _install_optional_visualization_packages(
        self, import_mgr, optional: dict
    ) -> None:  # WHY: declare private helper _install_optional_visualization_packages
        """Probe/install optional visualization packages, swallowing individual failures."""
        for package_name, package_spec in optional.items():  # WHY: iterate collection
            try:
                logging.debug(
                    "Checking optional package: %s (%s)", package_name, package_spec
                )  # WHY: action-log after operation
                import_mgr.import_module_safely(  # WHY: advance computation
                    package_name, package_spec=package_spec, required=False, skip_deps=False, skip_upgrade=True
                )
                logging.debug("Optional package %s installed/verified", package_name)  # WHY: action-log after operation
            except Exception as pkg_error:  # WHY: handle expected error
                logging.debug(
                    "Optional package %s unavailable: %s", package_name, pkg_error
                )  # WHY: action-log after operation

    def _install_visualization_packages(self) -> None:  # WHY: declare private helper _install_visualization_packages
        """Attempt to install plotly, dash, kaleido, and matplotlib via the global import_manager."""
        _import_manager = globals().get("import_manager")  # WHY: compute _import_manager
        if _import_manager is None:  # WHY: branch on condition
            logging.debug(
                "import_manager not available (standalone mode) - skipping package installation checks"
            )  # WHY: action-log after operation
            return  # WHY: return early
        required = {"plotly": "plotly>=5.14.0", "dash": "dash>=2.9.0"}  # WHY: compute required
        optional = {"kaleido": "kaleido>=0.2.1", "matplotlib": "matplotlib>=3.5.0"}  # WHY: compute optional
        self._install_required_visualization_packages(_import_manager, required)  # WHY: advance computation
        self._install_optional_visualization_packages(_import_manager, optional)  # WHY: advance computation

    @staticmethod
    def _prompt_matplotlib_fallback() -> bool:  # WHY: declare private helper _prompt_matplotlib_fallback
        """Prompt user to fall back to matplotlib mode. Return True if user consented."""
        confirm = (
            InputUtils.safe_input(
                "\nWould you like to continue without interactive features? (yes/no): ",
                context="_check_visualization_packages",
            )
            .strip()
            .lower()
        )  # Case-insensitive yes/y confirmation.
        return confirm in ["yes", "y"]  # Only proceed if user affirmed.

    @staticmethod
    def _resolve_matplotlib_fallback() -> "bool | None":  # WHY: declare private helper _resolve_matplotlib_fallback
        """Return False when matplotlib is available, None otherwise (with a message)."""
        if importlib.util.find_spec("matplotlib"):  # matplotlib import spec present.
            print("\n! Using matplotlib fallback (view-only mode)")  # Note view-only mode.
            logging.info("Successfully imported matplotlib for fallback mode")  # Audit log.
            return False  # False -> caller uses matplotlib path.
        logging.error("matplotlib fallback also not available")  # Both libraries missing.
        print("\n! No visualization libraries available")  # User-visible missing-libs message.
        print("! Install plotly: pip install plotly dash")  # Suggest plotly install.
        print("! Or matplotlib: pip install matplotlib")  # Suggest matplotlib install.
        return None  # Signal abort to caller.

    def _check_visualization_packages(
        self,
    ) -> "bool | None":  # WHY: declare private helper _check_visualization_packages
        """Check available visualization packages and prompt user if plotly is unavailable.

        Returns True if plotly/Dash is available, False for matplotlib fallback, or None to abort.
        """
        print("\nChecking visualization dependencies...")  # Progress note.
        logging.info("Starting visualization dependency check")  # Audit log.
        self._install_visualization_packages()  # Attempt on-demand install.
        if importlib.util.find_spec("plotly"):  # plotly import spec present.
            logging.info("Successfully imported plotly modules")  # Audit log.
            logging.debug("Using Plotly/Dash mode for interactive viewer")  # Detail log.
            return True  # True -> caller uses full interactive mode.
        logging.error("plotly not available")  # Report missing plotly.
        print("\n! Missing required package: plotly")  # User-visible message.
        print("! Install with: pip install plotly dash")  # Install hint.
        if not self._prompt_matplotlib_fallback():  # Confirm fallback path.
            logging.info("User declined matplotlib fallback")  # Audit log of decline.
            return None  # None -> caller aborts.
        return self._resolve_matplotlib_fallback()  # Try matplotlib backend.

    @staticmethod
    def _log_and_print_map_summary(
        map_data: dict, map_id: str
    ) -> None:  # WHY: declare private helper _log_and_print_map_summary
        """Log detailed map dimensions/features and print the summary line."""
        map_name = map_data.get("name", "Unnamed")  # WHY: compute map_name
        logging.info("Map loaded: %s (ID: %s)", map_name, map_id)  # WHY: action-log before operation
        logging.debug(  # WHY: action-log after operation
            "Map dimensions: %sx%spx, PPM: %s, Orientation: %s",
            map_data.get("width", 1000),
            map_data.get("height", 1000),
            map_data.get("ppm", 0),
            map_data.get("orientation", 0),
        )
        logging.debug(  # WHY: action-log after operation
            "Map has image: %s, Has walls: %s, Has wayfinding: %s",
            "url" in map_data,
            "wall_path" in map_data,
            "wayfinding_path" in map_data,
        )
        print(f"\nMap: {map_name}")  # WHY: surface user-facing message
        print(
            f"Dimensions: {map_data.get('width', 1000)}x{map_data.get('height', 1000)} pixels"
        )  # WHY: surface user-facing message

    @staticmethod
    def _warn_if_map_unscaled(map_data: dict) -> None:  # WHY: declare private helper _warn_if_map_unscaled
        """Emit a scaling warning if PPM is 0 or missing."""
        map_ppm = map_data.get("ppm", 0)  # WHY: compute map_ppm
        if map_ppm:  # WHY: branch on condition
            return  # WHY: return early
        map_name = map_data.get("name", "Unnamed")  # WHY: compute map_name
        logging.warning(
            "MAP NOT SCALED: Map '%s' has PPM=0 - image has not been scaled in Mist Portal", map_name
        )  # WHY: surface non-fatal issue
        print("\n" + "!" * 60)  # WHY: surface user-facing message
        print("! WARNING: This map image has NOT been scaled!")  # WHY: surface user-facing message
        print(
            "! RF coverage heatmap and location features will not work correctly."
        )  # WHY: surface user-facing message
        print("! Please scale this map in Mist Portal: Location > Set Scale")  # WHY: surface user-facing message
        print("!" * 60 + "\n")  # WHY: surface user-facing message

    def _log_map_fetch_failure(self, map_response) -> None:  # WHY: declare private helper _log_map_fetch_failure
        """Log details of a failed getSiteMap response and surface a user message."""
        logging.error(  # WHY: surface fatal issue
            "Failed to fetch map details - HTTP %s, Response: %s",
            map_response.status_code,
            map_response.data if hasattr(map_response, "data") else "No data",
        )
        print(f"\n! Failed to fetch map: HTTP {map_response.status_code}")  # WHY: surface user-facing message

    def _fetch_map_details(
        self, site_id: str, map_id: str
    ) -> "dict | None":  # WHY: declare private helper _fetch_map_details
        """Fetch map metadata from the API. Warn if PPM is unset.

        Returns the map data dict on success, or None on API failure.
        """
        print("\nLoading map data...")  # WHY: surface user-facing message
        logging.info(
            "Fetching map details - site_id: %s, map_id: %s", site_id, map_id
        )  # WHY: action-log before operation
        map_response = mistapi.api.v1.sites.maps.getSiteMap(
            self.apisession, site_id=site_id, map_id=map_id
        )  # WHY: compute map_response
        logging.debug("getSiteMap API response: HTTP %s", map_response.status_code)  # WHY: action-log after operation
        if map_response.status_code != 200:  # WHY: branch on condition
            self._log_map_fetch_failure(map_response)  # WHY: advance computation
            return None  # WHY: return computed result
        map_data = map_response.data  # WHY: compute map_data
        self._log_and_print_map_summary(map_data, map_id)  # WHY: advance computation
        self._warn_if_map_unscaled(map_data)  # WHY: advance computation
        return map_data  # WHY: return computed result

    def _log_device_type_breakdown(
        self, devices_on_map: list
    ) -> None:  # WHY: declare private helper _log_device_type_breakdown
        """Tally device types on the current map and emit a debug breakdown."""
        device_type_counts: dict[str, int] = {}  # WHY: assign computed value
        for device in devices_on_map:  # WHY: iterate collection
            dtype = device.get("type", "unknown")  # WHY: compute dtype
            device_type_counts[dtype] = device_type_counts.get(dtype, 0) + 1  # WHY: compute device_type_counts
        logging.debug("Device breakdown on map: %s", device_type_counts)  # WHY: action-log after operation

    def _fetch_devices_on_map(
        self, site_id: str, map_id: str
    ) -> list:  # WHY: declare private helper _fetch_devices_on_map
        """Fetch device stats for the site and filter to the given map_id."""
        logging.info("Fetching device stats for site %s (type=all)", site_id)  # WHY: action-log before operation
        devices_response = mistapi.api.v1.sites.stats.listSiteDevicesStats(
            self.apisession, site_id=site_id, limit=1000
        )  # WHY: compute devices_response
        logging.debug(
            "listSiteDevicesStats API response: HTTP %s", devices_response.status_code
        )  # WHY: action-log after operation
        if devices_response.status_code != 200:  # WHY: branch on condition
            logging.error("Failed to fetch devices - HTTP %s", devices_response.status_code)  # WHY: surface fatal issue
            print(
                f"\n! Failed to fetch devices: HTTP {devices_response.status_code}"
            )  # WHY: surface user-facing message
            return []  # WHY: return computed result
        all_devices = devices_response.data  # WHY: compute all_devices
        logging.debug("Total devices at site: %s", len(all_devices))  # WHY: action-log after operation
        devices_on_map = [d for d in all_devices if d.get("map_id") == map_id]  # WHY: compute devices_on_map
        logging.info("Devices on selected map: %s", len(devices_on_map))  # WHY: action-log before operation
        self._log_device_type_breakdown(devices_on_map)  # WHY: advance computation
        return devices_on_map  # WHY: return computed result

    def _fetch_zones_on_map(self, site_id: str, map_id: str) -> list:  # WHY: declare private helper _fetch_zones_on_map
        """Fetch site zones and filter to the given map_id."""
        logging.info("Fetching zones for site %s", site_id)  # WHY: action-log before operation
        try:
            zones_response = mistapi.api.v1.sites.zones.listSiteZones(
                self.apisession, site_id=site_id
            )  # WHY: compute zones_response
            if zones_response.status_code == 200:  # WHY: branch on condition
                all_zones = zones_response.data  # WHY: compute all_zones
                zones_on_map = [z for z in all_zones if z.get("map_id") == map_id]  # WHY: compute zones_on_map
                logging.info(
                    "Total zones at site: %s, Zones on this map: %s", len(all_zones), len(zones_on_map)
                )  # WHY: action-log before operation
                logging.debug("Zones on map: %s", zones_on_map)  # WHY: action-log after operation
                return zones_on_map  # WHY: return computed result
            logging.warning(
                "Failed to fetch zones - HTTP %s", zones_response.status_code
            )  # WHY: surface non-fatal issue
            return []  # WHY: return computed result
        except Exception as zone_error:  # WHY: handle expected error
            logging.exception("Error fetching zones: %s", zone_error)  # WHY: capture exception with traceback
            return []  # WHY: return computed result

    def _filter_clients_for_map(
        self, all_clients: list, map_id: str
    ) -> list:  # WHY: declare private helper _filter_clients_for_map
        """Return clients whose map_id matches and who have valid x/y coordinates."""
        return [  # WHY: return computed result
            c for c in all_clients if c.get("map_id") == map_id and c.get("x") is not None and c.get("y") is not None
        ]

    def _fetch_all_wireless_clients(
        self, site_id: str
    ) -> "list | None":  # WHY: declare private helper _fetch_all_wireless_clients
        """Fetch every wireless client stat for a site with pagination, or None on failure."""
        logging.info("Fetching connected wireless client stats for site %s", site_id)  # Trace API call
        resp = mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(
            self.apisession, site_id=site_id, limit=1000
        )  # Fetch first page
        if resp.status_code != 200:  # HTTP failure guard
            logging.warning("Failed to fetch client stats - HTTP %s", resp.status_code)  # Note the failure
            return None  # Signal failure
        return mistapi.get_all(response=resp, mist_session=self.apisession)  # Paginate to end

    @staticmethod
    def _log_client_map_diagnostics(
        all_clients: list, clients_on_map: list, map_id: str
    ) -> None:  # WHY: declare private helper _log_client_map_diagnostics
        """Emit diagnostic logs after filtering clients to a specific map."""
        client_map_ids = {c.get("map_id") for c in all_clients if c.get("map_id")}  # Distinct map ids seen
        logging.info("Client map_ids found: %s", client_map_ids)  # Trace the id set
        logging.info("Looking for map_id: %s", map_id)  # Trace the filter target
        logging.info("Clients on this map (after filtering): %s", len(clients_on_map))  # Filtered count
        if clients_on_map:  # Show a sample for the matched case
            logging.info("Sample client data: %s", clients_on_map[0])  # Trace sample match
        elif all_clients:  # Show a sample for the empty-match case
            logging.warning("No clients matched map_id %s. Sample: %s", map_id, all_clients[0])  # Diagnose

    def _fetch_clients_on_map(
        self, site_id: str, map_id: str
    ) -> list:  # WHY: declare private helper _fetch_clients_on_map
        """Fetch wireless client stats with pagination and filter to map_id with valid x/y coordinates."""
        try:
            all_clients = self._fetch_all_wireless_clients(site_id)  # Paginated client fetch
            if all_clients is None:  # Fetch failed
                return []  # No clients to plot
            logging.info("Total wireless clients retrieved: %s", len(all_clients))  # Trace totals
            clients_on_map = self._filter_clients_for_map(all_clients, map_id)  # Filter by map placement
            self._log_client_map_diagnostics(all_clients, clients_on_map, map_id)  # Diagnostics
            return clients_on_map  # Filtered set for the caller
        except Exception as client_error:  # WHY: handle expected error
            logging.exception("Error fetching client stats: %s", client_error)  # Log for diagnosis
            return []  # Fail closed with empty list

    def _handle_coverage_exception(
        self, coverage_data: dict
    ) -> None:  # WHY: declare private helper _handle_coverage_exception
        """Log and report an error-structure response from the RF coverage API."""
        exception_str = str(coverage_data.get("exception", ""))  # WHY: compute exception_str
        if "psycopg2" in exception_str or "database" in exception_str.lower():  # WHY: branch on condition
            logging.warning(
                "RF Coverage temporarily unavailable: Mist backend database connectivity issue"
            )  # WHY: surface non-fatal issue
            logging.debug("Coverage API backend error: %s", exception_str)  # WHY: action-log after operation
        else:
            logging.error(
                "Coverage API returned error response (first 500 chars): %s", exception_str[:500]
            )  # WHY: surface fatal issue
            logging.debug("Coverage API full error response: %s", exception_str)  # WHY: action-log after operation
            logging.debug(
                "Error details - Query: %s, URI: %s", coverage_data.get("query"), coverage_data.get("uri")
            )  # WHY: action-log after operation
        print(
            "  Note: RF Coverage heatmap unavailable (Mist backend issue) - continuing without it"
        )  # WHY: surface user-facing message

    def _request_map_coverage(self, site_id: str, map_id: str):  # WHY: declare private helper _request_map_coverage
        """Call the location coverage endpoint and return the raw response object."""
        coverage_url = f"/api/v1/sites/{site_id}/location/coverage"  # Site-scoped coverage endpoint.
        coverage_params = {
            "resolution": "fine",  # Fine grid resolution.
            "duration": "1d",  # Last 24h window.
            "map_id": map_id,  # Restrict to a single map.
            "type": "client",  # Client-based coverage samples.
            "from_apollo": "true",  # Undocumented: forces Apollo backend instead of PostgreSQL.
        }  # Query parameters for the coverage call.
        return self.apisession.mist_get(coverage_url, query=coverage_params)  # HTTP GET.

    def _parse_map_coverage_response(
        self, coverage_response
    ) -> "dict | None":  # WHY: declare private helper _parse_map_coverage_response
        """Extract coverage payload or handle known exception envelopes."""
        if coverage_response.status_code != 200:  # Non-200 -> failure.
            logging.warning(
                "Failed to fetch RF coverage data - HTTP %s", coverage_response.status_code
            )  # WHY: surface non-fatal issue
            return None  # WHY: return computed result
        coverage_data = coverage_response.data  # Parsed body.
        if isinstance(coverage_data, dict) and "exception" in coverage_data:  # Server error envelope.
            self._handle_coverage_exception(coverage_data)  # Log/print the exception details.
            return None  # WHY: return computed result
        result_count = len(coverage_data.get("results", [])) if coverage_data else 0  # Grid-point count.
        logging.info("RF coverage data retrieved: %s grid points", result_count)  # Audit log.
        return coverage_data  # Return the parsed payload.

    def _fetch_map_coverage(
        self, site_id: str, map_id: str
    ) -> "dict | None":  # WHY: declare private helper _fetch_map_coverage
        """Fetch RF coverage heatmap data for the given map from the Mist location API."""
        try:
            logging.info("Fetching RF coverage data for map %s", map_id)  # Audit log of the fetch.
            return self._parse_map_coverage_response(
                self._request_map_coverage(site_id, map_id)
            )  # WHY: return computed result
        except Exception as coverage_error:  # Network/parse errors return None.
            logging.exception("Error fetching RF coverage data: %s", coverage_error)  # Log full trace.
            return None  # WHY: return computed result

    def _fetch_map_entities(
        self, site_id: str, map_id: str
    ) -> "tuple[list, list, list]":  # WHY: declare private helper _fetch_map_entities
        """Fetch devices, zones, and clients on the map and echo their counts."""
        print("Loading devices...")  # WHY: surface user-facing message
        devices_on_map = self._fetch_devices_on_map(site_id, map_id)  # WHY: compute devices_on_map
        print(f"Devices on map: {len(devices_on_map)}")  # WHY: surface user-facing message
        zones_on_map = self._fetch_zones_on_map(site_id, map_id)  # WHY: compute zones_on_map
        print(f"Zones on map: {len(zones_on_map)}")  # WHY: surface user-facing message
        clients_on_map = self._fetch_clients_on_map(site_id, map_id)  # WHY: compute clients_on_map
        print(f"Connected clients on map: {len(clients_on_map)}")  # WHY: surface user-facing message
        return devices_on_map, zones_on_map, clients_on_map  # WHY: return computed result

    def _load_map_viewer_bundle(
        self, site_id: str, map_id: str
    ) -> tuple[dict, list, list, list, object, list] | None:  # WHY: declare private helper _load_map_viewer_bundle
        """Fetch all viewer inputs. Return (map_data, devices, zones, clients, coverage, all_sites) or None on missing map."""
        map_data = self._fetch_map_details(site_id, map_id)  # WHY: compute map_data
        if map_data is None:  # WHY: branch on condition
            return None  # WHY: return computed result
        devices_on_map, zones_on_map, clients_on_map = self._fetch_map_entities(
            site_id, map_id
        )  # WHY: compute devices_on_map
        coverage_data = self._fetch_map_coverage(site_id, map_id)  # WHY: compute coverage_data
        print("Loading organization sites...")  # WHY: surface user-facing message
        all_sites = self._fetch_sites()  # WHY: compute all_sites
        logging.info("Fetched %s sites for site selector dropdown", len(all_sites))  # WHY: action-log before operation
        return (
            map_data,
            devices_on_map,
            zones_on_map,
            clients_on_map,
            coverage_data,
            all_sites,
        )  # WHY: return computed result

    def _dispatch_map_viewer(  # WHY: declare private helper _dispatch_map_viewer
        self,
        use_plotly: bool,
        scope: "MapViewerScope",
        data: "MapViewerData",
        optional: "MapViewerOptional",
    ) -> None:
        """Launch either the Plotly/Dash viewer or the matplotlib fallback."""
        map_name = data.map_data.get("name", "Unnamed")  # WHY: compute map_name
        if use_plotly:  # WHY: branch on condition
            logging.info("Launching Plotly/Dash viewer for map %s", map_name)  # WHY: action-log before operation
            launch_plotly_viewer(self, scope, data, optional)  # WHY: advance computation
        else:
            logging.info(
                "Launching matplotlib fallback viewer for map %s", map_name
            )  # WHY: action-log before operation
            self._launch_matplotlib_viewer(data.map_data, data.devices)  # WHY: advance computation

    def _run_map_viewer_flow(
        self, site_id: str, site_name: str
    ) -> None:  # WHY: declare private helper _run_map_viewer_flow
        """Body of interactive_map_viewer, split out to keep the entry method thin."""
        use_plotly = self._check_visualization_packages()  # WHY: compute use_plotly
        if use_plotly is None:  # WHY: branch on condition
            return  # WHY: return early
        logging.debug("Prompting user to select map from site %s", site_name)  # nosec B608 — not SQL, just logging
        map_id, all_maps = self._select_map_from_site(site_id, site_name, return_all_maps=True)  # WHY: compute map_id
        if not map_id:  # WHY: guard against missing precondition
            logging.info("Map viewer aborted: No map selected")  # WHY: action-log before operation
            return  # WHY: return early
        logging.debug(
            "Selected map_id: %s, Total maps available: %s", map_id, len(all_maps)
        )  # WHY: action-log after operation
        bundle = self._load_map_viewer_bundle(site_id, map_id)  # WHY: compute bundle
        if bundle is None:  # WHY: branch on condition
            return  # WHY: return early
        map_data, devices, zones, clients, coverage_data, all_sites = bundle  # WHY: compute map_data
        scope = MapViewerScope(site_id=site_id, site_name=site_name, map_id=map_id)  # WHY: compute scope
        data = MapViewerData(map_data=map_data, devices=devices, zones=zones, clients=clients)  # WHY: compute data
        optional = MapViewerOptional(
            coverage_data=coverage_data, all_maps=all_maps, all_sites=all_sites
        )  # WHY: compute optional
        self._dispatch_map_viewer(use_plotly, scope, data, optional)  # WHY: advance computation

    @staticmethod
    def _print_interactive_viewer_header() -> None:  # WHY: declare private helper _print_interactive_viewer_header
        """Print the banner for the interactive-map-viewer flow."""
        print("\n" + "-" * 80)  # Section banner top rule.
        print("INTERACTIVE MAP VIEWER")  # Section title.
        print("-" * 80)  # Section banner bottom rule.

    def interactive_map_viewer(self) -> None:  # WHY: declare public method interactive_map_viewer
        """Interactive map viewer with Plotly/Dash for viewing and editing.

        Supports:
        - Floor plan image display
        - Toggleable overlays: walls, zones, wayfinding paths
        - Device visualization: APs, switches, gateways with orientation indicators
        - Click-to-edit device locations
        - Save changes back to Mist Cloud
        """
        logging.info("Interactive map viewer initiated")  # Audit log at entry.
        self._print_interactive_viewer_header()  # Section banner.
        site_id, site_name = self.get_current_site()  # Resolve current site.
        if not site_id:  # No site selected -> nothing to view.
            logging.warning("Interactive map viewer aborted: No site selected")  # Log soft abort.
            return  # WHY: return early
        logging.debug("Interactive map viewer - Site: %s (ID: %s)", site_name, site_id)  # Detail log.
        try:
            self._run_map_viewer_flow(site_id, site_name)  # Delegate to flow method.
        except EOFError:  # User hit Ctrl-D.
            logging.info("EOF detected during interactive map viewer")  # Log soft abort.
            return  # WHY: return early
        except Exception as e:  # Catch-all so menu keeps running.
            logging.exception("Error in interactive map viewer: %s", e)  # Log full trace.
            print(f"\n! Error launching map viewer: {e}")  # Surface error to operator.

    @staticmethod
    def _axis_ppm(pixels, meters) -> float | None:  # WHY: declare private helper _axis_ppm
        """Return pixels/meters when both values are truthy and meters > 0, else None."""
        if pixels and meters and meters > 0:  # Both values required and meters must be positive.
            return pixels / meters  # Ratio yields pixels-per-meter for this axis.
        return None  # Signal caller to skip this axis.

    def _client_ppm_samples(self, client: dict) -> list[float]:  # WHY: declare private helper _client_ppm_samples
        """Return the x/y PPM samples derivable from a single client record."""
        samples: list[float] = []  # Accumulate the up-to-two axis samples.
        for pixels_key, meters_key in (("x", "x_m"), ("y", "y_m")):  # One entry per axis.
            ratio = self._axis_ppm(client.get(pixels_key), client.get(meters_key))  # Compute or skip.
            if ratio is not None:  # Only keep valid samples.
                samples.append(ratio)  # Record for averaging.
        return samples  # Hand back the per-client samples.

    def _collect_ppm_samples(self, clients: list) -> list[float]:  # WHY: declare private helper _collect_ppm_samples
        """Walk the first 10 clients and collect PPM ratio samples from x/y pixel-vs-meter pairs."""
        logging.debug("Collecting PPM samples from up to 10 clients")  # Log sample collection start.
        ppm_samples: list[float] = []  # Accumulate computed PPM values.
        for client in clients[:10]:  # Check first 10 clients only -- sufficient for validation.
            ppm_samples.extend(self._client_ppm_samples(client))  # Merge per-client samples.
        logging.debug("Collected %d PPM samples", len(ppm_samples))  # Log result count.
        return ppm_samples  # Hand back samples for averaging.

    @staticmethod
    def _log_ppm_mismatch(
        ppm: float, calculated_ppm: float, ppm_ratio: float
    ) -> None:  # WHY: declare private helper _log_ppm_mismatch
        """Emit two warning logs describing a detected PPM calibration mismatch."""
        logging.warning(
            "PPM MISMATCH DETECTED! Map PPM=%s, Calculated from clients=%s (ratio: %sx)",
            ppm,
            f"{calculated_ppm:.1f}",
            f"{ppm_ratio:.2f}",
        )  # Warn operator about calibration issue.
        logging.warning(
            "Map may not be scaled correctly. Using calculated PPM for coverage heatmap."
        )  # Explain correction to operator.

    def _validate_ppm(self, clients: list, ppm: float) -> float:  # WHY: declare private helper _validate_ppm
        """Validate pixels-per-meter ratio using client coordinate data and return corrected value."""
        if not clients:  # No clients to validate against -- return map PPM unchanged.
            return ppm  # Return the map's stored PPM value as-is.
        ppm_samples = self._collect_ppm_samples(clients)  # Gather PPM samples from client coordinates.
        if not ppm_samples:  # No valid samples found -- cannot validate.
            return ppm  # Return original PPM unchanged.
        calculated_ppm = sum(ppm_samples) / len(ppm_samples)  # Average all samples for accuracy.
        ppm_ratio = (calculated_ppm / ppm) if ppm > 0 else 0  # Compare map PPM to calculated PPM.
        if abs(ppm_ratio - 1.0) > 0.1:  # More than 10% difference indicates mismatch.
            self._log_ppm_mismatch(ppm, calculated_ppm, ppm_ratio)  # Emit calibration warnings.
            return calculated_ppm  # Use client-derived PPM for better accuracy.
        logging.debug("PPM validation passed: map=%s, calculated=%s", ppm, f"{calculated_ppm:.1f}")  # OK.
        return ppm  # Return original PPM when within acceptable range.

    @staticmethod
    def _survey_path_scatter(
        path_name: str, path_x: list, path_y: list, point_count: int
    ):  # WHY: declare private helper _survey_path_scatter
        """Build the go.Scatter trace for a survey path."""
        return go.Scatter(
            x=path_x,
            y=path_y,
            mode="lines+markers",
            name=f"Validation: {path_name}",
            line=dict(color="#ff00ff", width=3, dash="dot"),  # Magenta dashed line for visibility.
            marker=dict(size=10, color="#ff00ff", symbol="diamond", line=dict(color="white", width=2)),
            visible=True,
            showlegend=True,
            hovertext=f"Validation Path: {path_name}<br>{point_count} points",
            hoverinfo="text",
        )  # Draw the path as a connected line with diamond markers.

    @staticmethod
    def _survey_path_annotation(
        path_name: str, path_x: list, path_y: list
    ) -> dict:  # WHY: declare private helper _survey_path_annotation
        """Build the annotation dict labeling the start of a survey path."""
        return dict(
            x=path_x[0],
            y=path_y[0] - 20,
            text=f"<b>{path_name}</b>",
            showarrow=False,
            font=dict(size=11, color="white", family="Arial Black"),
            bgcolor="rgba(255,0,255,0.9)",
            bordercolor="white",
            borderwidth=2,
            borderpad=3,
            xanchor="center",
            yanchor="bottom",
        )  # Label the start point of the path for identification.

    @staticmethod
    def _add_survey_path_trace(
        fig, path_name: str, path_x: list, path_y: list, point_count: int
    ) -> None:  # WHY: declare private helper _add_survey_path_trace
        """Draw one survey path as a magenta dashed line with a start-point label."""
        fig.add_trace(
            MapsManager._survey_path_scatter(path_name, path_x, path_y, point_count)
        )  # Add the connected-line trace for the path.
        fig.add_annotation(
            **MapsManager._survey_path_annotation(path_name, path_x, path_y)
        )  # Add the identifying label at the start of the path.

    def _add_single_survey_path(
        self, fig, path: dict, path_idx: int
    ) -> None:  # WHY: declare private helper _add_single_survey_path
        """Add one validation path to the figure, skipping if it lacks enough points."""
        path_name = path.get("name", f"Path {path_idx + 1}")  # Use name or generate fallback label.
        path_coords = path.get("coordinate", [])  # List of {x, y} coordinate dicts.
        if not path_coords or len(path_coords) < 2:  # Need at least 2 points to draw a line.
            logging.warning(
                "Validation path '%s' has insufficient coordinates: %d", path_name, len(path_coords)
            )  # WHY: surface non-fatal issue
            return  # Skip this path -- cannot draw a line with fewer than 2 points.
        path_x = [coord.get("x", 0) for coord in path_coords]  # Extract x coordinates.
        path_y = [coord.get("y", 0) for coord in path_coords]  # Extract y coordinates.
        self._add_survey_path_trace(fig, path_name, path_x, path_y, len(path_coords))  # Draw + label.
        logging.debug("Added validation path '%s' with %d points", path_name, len(path_coords))  # Trace.

    def _add_site_survey_paths(self, fig, map_data: dict) -> None:  # WHY: declare private helper _add_site_survey_paths
        """Add site survey (validation) paths to the Plotly figure as dashed magenta lines."""
        if not map_data.get("sitesurvey_path"):  # No validation paths on this map -- skip.
            logging.info("No validation paths found on this map")  # Informational for operator.
            return  # Nothing to draw.
        sitesurvey_paths = map_data["sitesurvey_path"]  # List of survey path objects from Mist API.
        logging.info("Processing %d validation paths", len(sitesurvey_paths))  # Log path count.
        for path_idx, path in enumerate(sitesurvey_paths):  # Iterate all paths.
            self._add_single_survey_path(fig, path, path_idx)  # Delegate per-path handling.

    @staticmethod
    def _build_client_hover(client: dict, x, y) -> str:  # WHY: declare private helper _build_client_hover
        """Assemble the rich HTML hover tooltip for a single client marker."""
        hover = "<b>Client</b><br>"  # Tooltip header
        hover += f"MAC: {client.get('mac', 'N/A')}<br>"  # MAC line
        hover += f"Hostname: {client.get('hostname', 'N/A')}<br>"  # Hostname line
        hover += f"SSID: {client.get('ssid', 'N/A')}<br>"  # SSID line
        hover += f"AP: {client.get('ap_name', 'N/A')}<br>"  # Associated AP
        hover += f"Band: {client.get('band', 'N/A')}<br>"  # Radio band
        hover += f"Signal: {client.get('rssi', 'N/A')} dBm<br>"  # Signal strength
        hover += f"Position: ({x}, {y})"  # Pixel coordinates on map
        return hover  # WHY: return computed result

    @staticmethod
    def _extract_client_point(
        client: dict, map_id: str
    ) -> tuple | None:  # WHY: declare private helper _extract_client_point
        """Return (x, y, hover, label) for one placed client, or None to skip."""
        x = client.get("x")  # Client x pixel coordinate
        y = client.get("y")  # Client y pixel coordinate
        client_mac = client.get("mac", "unknown")  # MAC for logging + fallback label
        logging.debug(
            "Client %s: x=%s, y=%s, map_id=%s (looking for map_id=%s)",
            client_mac,
            x,
            y,
            client.get("map_id", "none"),
            map_id,
        )  # Trace each client's raw coords
        if x is None or y is None:  # Skip clients without coordinates
            return None  # Not placed on map -- cannot render
        hostname = client.get("hostname", "")  # Prefer hostname label
        label = hostname if hostname else client_mac[-8:]  # Fall back to short MAC
        return x, y, MapsManager._build_client_hover(client, x, y), label  # WHY: return computed result

    @staticmethod
    def _collect_client_points(
        clients: list, map_id: str
    ) -> tuple[list, list, list, list]:  # WHY: declare private helper _collect_client_points
        """Return (x, y, hover, label) lists for clients with valid coordinates."""
        xs: list = []  # x pixel coordinates
        ys: list = []  # y pixel coordinates
        hovers: list = []  # HTML hover tooltip strings
        names: list = []  # Display labels for annotations
        for client in clients:  # Iterate all clients on the map
            point = MapsManager._extract_client_point(client, map_id)  # Normalize the entry
            if point is None:  # Skip unplaced clients
                continue  # Move to next client
            xs.append(point[0])  # Store valid x
            ys.append(point[1])  # Store valid y
            hovers.append(point[2])  # Store rich hover
            names.append(point[3])  # Store label
        return xs, ys, hovers, names  # WHY: return computed result

    @staticmethod
    def _add_client_marker_trace(
        fig, xs: list, ys: list, hovers: list
    ) -> None:  # WHY: declare private helper _add_client_marker_trace
        """Add the single Plotly Scatter trace holding all client markers."""
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers",
                name="Clients",
                marker=dict(
                    symbol="circle",
                    size=12,
                    color="#00ff00",  # Bright green for clients
                    line=dict(color="white", width=2),
                    opacity=0.9,
                ),
                hovertext=hovers,
                hoverinfo="text",
                visible=True,
                showlegend=True,
            )
        )  # Single trace keeps legend + rendering efficient

    @staticmethod
    def _add_client_label_annotations(
        fig, xs: list, ys: list, names: list
    ) -> None:  # WHY: declare private helper _add_client_label_annotations
        """Add one label annotation per client, positioned below the marker."""
        for x, y, name in zip(xs, ys, names, strict=True):  # Per-client label loop
            fig.add_annotation(
                x=x,
                y=y - 10,
                text=f"<b>{name}</b>",
                showarrow=False,
                font=dict(size=9, color="white", family="Arial"),
                bgcolor="rgba(0,128,0,0.9)",
                bordercolor="white",
                borderwidth=1,
                borderpad=2,
                xanchor="center",
                yanchor="bottom",
                name="Clients Label",
            )  # Below-marker placement keeps map imagery visible

    def _add_clients_to_figure(
        self, fig, clients: list, map_id: str
    ) -> None:  # WHY: declare private helper _add_clients_to_figure
        """Add connected wireless client markers and labels to the Plotly figure."""
        if not clients:  # No clients on this map -- skip rendering
            logging.info("No connected clients found on this map")  # WHY: action-log before operation
            return  # WHY: return early
        logging.info("Processing %d connected clients on this map", len(clients))  # WHY: action-log before operation
        logging.debug("Client sample data: %s", clients[0])  # First-record sample
        xs, ys, hovers, names = self._collect_client_points(clients, map_id)  # Filter to placed clients
        if not xs:  # No clients had valid coordinates
            logging.warning(
                "Found %d clients but none have x,y coordinates", len(clients)
            )  # WHY: surface non-fatal issue
            return  # WHY: return early
        self._add_client_marker_trace(fig, xs, ys, hovers)  # Marker layer
        self._add_client_label_annotations(fig, xs, ys, names)  # Text label layer
        logging.info(  # WHY: action-log before operation
            "Added %d clients to map visualization (out of %d total clients)",
            len(xs),
            len(clients),
        )

    @staticmethod
    def _resolve_site_name(
        all_sites: list[dict], site_id: str
    ) -> str:  # WHY: declare private helper _resolve_site_name
        """Look up a site's display name from the cached site list, or 'Unknown'."""
        for site in all_sites:  # WHY: iterate collection
            if site.get("id") == site_id:  # WHY: branch on condition
                return site.get("name", "Unknown")  # WHY: return computed result
        return "Unknown"  # WHY: return computed result

    @staticmethod
    def _extract_graph_segments(graph_data: dict) -> list[dict]:  # WHY: declare private helper _extract_graph_segments
        """Convert a Mist graph payload (nodes + edges) into x1/y1/x2/y2 line segments."""
        if not graph_data:  # WHY: guard against missing precondition
            return []  # WHY: return computed result
        nodes = graph_data.get("nodes", [])  # WHY: compute nodes
        if not nodes:  # WHY: guard against missing precondition
            return []  # WHY: return computed result
        node_lookup = MapsManager._build_node_position_lookup(nodes)  # WHY: compute node_lookup
        return MapsManager._edges_to_segments(nodes, node_lookup)  # WHY: return computed result

    @staticmethod
    def _build_node_position_lookup(
        nodes: list[dict],
    ) -> dict[str, dict[str, float]]:  # WHY: declare private helper _build_node_position_lookup
        """Map node name -> {x, y} for any node that has a position."""
        lookup: dict[str, dict[str, float]] = {}  # WHY: assign computed value
        for node in nodes:  # WHY: iterate collection
            position = node.get("position", {})  # WHY: compute position
            if position:  # WHY: branch on condition
                lookup[node.get("name", "")] = {  # WHY: assign computed value
                    "x": position.get("x", 0),
                    "y": position.get("y", 0),
                }
        return lookup  # WHY: return computed result

    @staticmethod
    def _node_edge_segments(
        node: dict, node_lookup: dict[str, dict[str, float]]
    ) -> list[dict]:  # WHY: declare private helper _node_edge_segments
        """Return every segment connecting one node's edges to their target positions."""
        position = node.get("position", {})  # Origin coordinates for this node.
        edges = node.get("edges", {})  # Mapping of edge name -> target metadata.
        if not (position and edges):  # Node must have both a position and outgoing edges.
            return []  # Nothing to emit for isolated / positionless nodes.
        start_x = position.get("x", 0)  # Origin x pixel coordinate.
        start_y = position.get("y", 0)  # Origin y pixel coordinate.
        segments: list[dict] = []  # Accumulate the segments from this node.
        for edge_name in edges.keys():  # Iterate every outgoing edge by target name.
            end = node_lookup.get(edge_name)  # Look up destination position by name.
            if end is None:  # Skip edges whose destination we cannot locate.
                continue  # Ignore orphan edge entries.
            segments.append({"x1": start_x, "y1": start_y, "x2": end["x"], "y2": end["y"]})  # Line seg.
        return segments  # Hand back the per-node segments.

    @staticmethod
    def _edges_to_segments(
        nodes: list[dict], node_lookup: dict[str, dict[str, float]]
    ) -> list[dict]:  # WHY: declare private helper _edges_to_segments
        """Walk every (node, edge) pair and emit a connecting segment when both ends are known."""
        segments: list[dict] = []  # Accumulate segments across all nodes.
        for node in nodes:  # Iterate the graph nodes in order.
            segments.extend(MapsManager._node_edge_segments(node, node_lookup))  # Merge per-node output.
        return segments  # Hand back the complete segment list.

    def _extract_walls(self, map_data: dict) -> list[dict]:  # WHY: declare private helper _extract_walls
        """Pull wall segments from the map's wall_path graph, log the count, return segments."""
        wall_data = map_data.get("wall_path", {})  # WHY: compute wall_data
        if wall_data:  # WHY: branch on condition
            logging.debug("[Flask API] Raw wall_path data: %s", wall_data)  # WHY: action-log after operation
        walls = self._extract_graph_segments(wall_data)  # WHY: compute walls
        if walls:  # WHY: branch on condition
            logging.info(  # WHY: action-log before operation
                "[Flask API] Extracted %s wall segments from %s nodes",
                len(walls),
                len(wall_data.get("nodes", [])),
            )
        return walls  # WHY: return computed result

    def _extract_wayfinding(self, map_data: dict) -> list[dict]:  # WHY: declare private helper _extract_wayfinding
        """Pull wayfinding segments from the map's wayfinding_path graph."""
        wayfinding_data = map_data.get("wayfinding_path", {})  # WHY: compute wayfinding_data
        if wayfinding_data:  # WHY: branch on condition
            logging.debug(
                "[Flask API] Raw wayfinding_path data: %s", wayfinding_data
            )  # WHY: action-log after operation
        wayfinding = self._extract_graph_segments(wayfinding_data)  # WHY: compute wayfinding
        if wayfinding:  # WHY: branch on condition
            logging.info(  # WHY: action-log before operation
                "[Flask API] Extracted %s wayfinding segments from %s nodes",
                len(wayfinding),
                len(wayfinding_data.get("nodes", [])),
            )
        return wayfinding  # WHY: return computed result

    def _collect_map_payload(
        self, api_session, all_sites, site_id, map_id
    ):  # WHY: declare private helper _collect_map_payload
        """Delegating wrapper: payload assembly lives in src.maps._maps_coverage."""
        # Wrapper kept so launch_viewer_standalone can still pass
        # self._collect_map_payload as a bound callable to launch_flask_viewer.
        from src.maps._maps_coverage import _MapsCoverage  # WHY: import extracted coverage helper class.

        coverage = _MapsCoverage(self)  # WHY: bind extracted helper to this MapsManager for __getattr__ delegation.
        return coverage._collect_map_payload(api_session, all_sites, site_id, map_id)  # WHY: forward args to helper.

    def _build_map_data_response(
        self, site_id, map_id, map_data, layers
    ):  # WHY: declare private helper _build_map_data_response
        """Delegating wrapper: response assembly lives in src.maps._maps_coverage."""
        # Wrapper kept so launch_viewer_standalone can still pass
        # self._build_map_data_response as a bound callable to launch_flask_viewer.
        from src.maps._maps_coverage import _MapsCoverage  # WHY: import extracted coverage helper class.

        coverage = _MapsCoverage(self)  # WHY: bind extracted helper to this MapsManager for __getattr__ delegation.
        return coverage._build_map_data_response(site_id, map_id, map_data, layers)  # WHY: forward args to helper.

    def launch_viewer_standalone(self):  # WHY: declare public method launch_viewer_standalone
        """Delegating wrapper: matplotlib viewer + launcher live in src.maps._maps_matplotlib."""
        # Wrapper kept so main() in this same file can still call
        # maps_manager.launch_viewer_standalone() as an instance method.
        from src.maps._maps_matplotlib import launch_viewer_standalone  # WHY: import required module

        return launch_viewer_standalone(self)  # WHY: return computed result


# ============================================================================
# STANDALONE ENTRY POINT
# ============================================================================


def _check_dependencies() -> None:  # WHY: declare private helper _check_dependencies
    """Verify required dependencies are available. Exit with error if not."""
    if not DASH_AVAILABLE or not PLOTLY_AVAILABLE:  # WHY: guard against missing precondition
        print("ERROR: This module requires dash and plotly packages.")  # WHY: surface user-facing message
        print("Install with: pip install dash plotly")  # WHY: surface user-facing message
        sys.exit(1)  # WHY: advance computation
    if not mistapi:  # WHY: guard against missing precondition
        print("ERROR: This module requires the mistapi package.")  # WHY: surface user-facing message
        print("Install with: pip install mistapi")  # WHY: surface user-facing message
        sys.exit(1)  # WHY: advance computation


def _configure_logging(debug: bool) -> None:  # WHY: declare private helper _configure_logging
    """Configure logging level and handlers."""
    log_level = logging.DEBUG if debug else logging.INFO  # WHY: compute log_level
    logging.basicConfig(  # WHY: advance computation
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join("data", "maps_manager.log"), encoding="utf-8"),
        ],
    )


def _setup_api_session(env_file: str):  # WHY: declare private helper _setup_api_session
    """Initialize and return a Mist API session. Exit on failure."""
    try:
        if os.path.exists(env_file):  # WHY: branch on condition
            apisession = mistapi.APISession(env_file=env_file)  # WHY: compute apisession
        else:
            print("No .env file found. Please provide Mist API credentials.")  # WHY: surface user-facing message
            host = (  # WHY: compute host
                InputUtils.safe_input("Mist API Host [api.mist.com]: ", context="_setup_api_session").strip()
                or "api.mist.com"
            )
            token = InputUtils.safe_input("API Token: ", context="_setup_api_session").strip()  # WHY: compute token
            apisession = mistapi.APISession(host=host, token=token)  # WHY: compute apisession
        apisession.login()  # WHY: advance computation
        return apisession  # WHY: return computed result
    except Exception as e:  # WHY: handle expected error
        print(f"ERROR: Failed to initialize API session: {e}")  # WHY: surface user-facing message
        sys.exit(1)  # WHY: advance computation


def _prompt_org_selection(orgs: list) -> str:  # WHY: declare private helper _prompt_org_selection
    """Display org choices and return the selected org_id. Exit on invalid input."""
    print("\nAvailable Organizations:")  # WHY: surface user-facing message
    for idx, oid in enumerate(orgs, 1):  # WHY: iterate collection
        print(f"  {idx}. {oid}")  # WHY: surface user-facing message
    try:
        choice = InputUtils.safe_input(
            "Select organization number: ", context="_prompt_org_selection"
        ).strip()  # WHY: compute choice
        return orgs[int(choice) - 1]  # WHY: return computed result
    except (ValueError, IndexError):  # WHY: handle expected error
        print("Invalid selection")  # WHY: surface user-facing message
        sys.exit(1)  # WHY: advance computation


def _filter_org_privileges(privileges: list) -> list:  # WHY: declare private helper _filter_org_privileges
    """Extract org-scoped org_ids from session privileges."""
    return [
        p["org_id"] for p in privileges if p.get("scope") == "org" and p.get("org_id")
    ]  # WHY: return computed result


def _pick_org_from_privileges(
    orgs: list[str], test_mode: bool
) -> str | None:  # WHY: declare private helper _pick_org_from_privileges
    """Return the org_id to use given the filtered privilege list and test-mode flag."""
    if len(orgs) == 1:  # Single-org account -- no ambiguity.
        return orgs[0]  # Auto-select the sole org.
    if orgs and test_mode:  # Multi-org but running non-interactively.
        print(f"Test mode: Using first available org: {orgs[0]}")  # Announce the automatic pick.
        return orgs[0]  # Deterministic first-org choice for test runs.
    return _prompt_org_selection(orgs) if orgs else None  # Prompt only when there is something to pick.


def _detect_org_from_session(
    apisession, test_mode: bool
) -> str | None:  # WHY: declare private helper _detect_org_from_session
    """Detect org_id from the API session privileges. Return None if not found."""
    try:
        self_info = mistapi.api.v1.self.self.getSelf(apisession)  # Fetch the authenticated user info.
        if not (hasattr(self_info, "data") and self_info.data):  # Guard against empty API responses.
            return None  # Cannot detect anything without a data payload.
        orgs = _filter_org_privileges(self_info.data.get("privileges", []))  # Keep only org privileges.
        return _pick_org_from_privileges(orgs, test_mode)  # Delegate the selection policy.
    except Exception as e:  # Any API/network failure just means "no auto-detected org".
        logging.warning("Could not auto-detect org_id: %s", e)  # Log the reason for diagnostics.
        return None  # Signal caller to fall back to prompting or defaults.


def _resolve_org_id(apisession, args) -> str | None:  # WHY: declare private helper _resolve_org_id
    """Resolve org_id from CLI args, environment variables, or API session."""
    org_id = args.org or os.getenv("org_id") or os.getenv("ORG_ID") or os.getenv("MIST_ORG_ID")  # WHY: compute org_id
    if org_id:  # WHY: branch on condition
        return org_id  # WHY: return computed result
    return _detect_org_from_session(apisession, args.test)  # WHY: return computed result


def _build_arg_parser():  # WHY: declare private helper _build_arg_parser
    """Build the argparse parser for standalone execution."""
    import argparse  # WHY: import required module

    parser = argparse.ArgumentParser(  # WHY: compute parser
        description="MapsManager - Interactive Map Viewer for Mist Networks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python maps_manager.py                    # Launch interactive viewer (default)
    python maps_manager.py --menu             # Show menu for non-viewer operations
    python maps_manager.py --org <ORG_ID>     # Use specific org ID
        """,
    )
    parser.add_argument(
        "--menu", action="store_true", help="Show operations menu instead of launching viewer directly"
    )  # WHY: assign computed value
    parser.add_argument(
        "--org", type=str, default=None, help="Organization ID to use (optional)"
    )  # WHY: assign computed value
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")  # WHY: assign computed value
    parser.add_argument(
        "--test", action="store_true", help="Run systematic test of safe, non-destructive operations"
    )  # WHY: assign computed value
    return parser  # WHY: return computed result


def _require_org_id(apisession, args) -> str:  # WHY: declare private helper _require_org_id
    """Resolve org_id or prompt/exit if missing."""
    org_id = _resolve_org_id(apisession, args)  # WHY: compute org_id
    if not org_id:  # WHY: guard against missing precondition
        if args.test:  # WHY: branch on condition
            print(
                "ERROR: Organization ID required for test mode. Set org_id in .env or use --org flag"
            )  # WHY: surface user-facing message
            sys.exit(1)  # WHY: advance computation
        org_id = InputUtils.safe_input("Organization ID: ", context="main").strip()  # WHY: compute org_id
    if not org_id:  # WHY: guard against missing precondition
        print("ERROR: Organization ID is required")  # WHY: surface user-facing message
        sys.exit(1)  # WHY: advance computation
    return org_id  # WHY: return computed result


def _dispatch_maps_manager(maps_manager, args) -> None:  # WHY: declare private helper _dispatch_maps_manager
    """Dispatch to test / menu / viewer based on CLI flags."""
    if args.test:  # WHY: branch on condition
        success = maps_manager.run_systematic_test()  # WHY: compute success
        sys.exit(0 if success else 1)  # WHY: advance computation
    if args.menu:  # WHY: branch on condition
        maps_manager.run_interactive_menu()  # WHY: advance computation
        return  # WHY: return early
    maps_manager.launch_viewer_standalone()  # WHY: advance computation


def main():  # WHY: declare public method main
    """Main entry point for standalone execution."""
    args = _build_arg_parser().parse_args()  # WHY: compute args
    _check_dependencies()  # WHY: advance computation
    _configure_logging(args.debug)  # WHY: advance computation
    apisession = _setup_api_session(".env")  # WHY: compute apisession
    org_id = _require_org_id(apisession, args)  # WHY: compute org_id
    maps_manager = MapsManager(apisession, org_id)  # WHY: compute maps_manager
    _dispatch_maps_manager(maps_manager, args)  # WHY: advance computation


if __name__ == "__main__":  # WHY: branch on condition
    main()  # WHY: advance computation
