"""PromptUtils: centralized interactive selection helpers.

Extracted from MistHelper.py per issue #1015 T-07 (Cat E fresh extraction).
Canonical home for site/device/client selection prompts. Uses lazy access
to MistHelper globals (``apisession``, ``DataExporter``, ``LAST_SELECTED_SITE_ID``)
via ``importlib.import_module("MistHelper")`` to avoid circular imports.
"""

from __future__ import annotations

import csv
import importlib
import logging
import time
from typing import Literal

import mistapi
from prettytable import PrettyTable

from src.api.api_core_fetch_utils import APICoreFetchUtils
from src.cache.cache_utils import CacheUtils
from src.data.data_processing_utils import DataProcessingUtils
from src.export.org_site_exporter import OrgSiteExporter
from src.input.prompt_client_utils import PromptClientUtils
from src.utils.file_path_utils import FilePathUtils
from src.utils.input_utils import InputUtils


class PromptUtils:  # General prompt helpers.
    """Centralized prompt utilities for user input and selection operations.

    Groups all interactive selection functions (sites, devices, ports, clients).
    All methods are static to avoid unnecessary object instantiation.
    """

    @staticmethod
    def select_device_id_from_inventory(
        site_id: str, device_type: str = "all", csv_filename: str = "SiteInventory.csv"
    ) -> str | None:
        """Prompt operator to select a device from ``site_id`` inventory and return its device id.

        Always fetches type=all from the API (Mist default is APs-only) and filters locally.
        """
        inventory = PromptUtils._fetch_and_filter_devices(site_id, device_type)  # API + local filter.
        if not inventory:  # Nothing matched the requested filter.
            return None  # Abort selection.
        table, index_to_device, name_to_device = PromptUtils._export_and_index_inventory(inventory, csv_filename)
        print(table)  # Render the device table.
        logging.info("Displayed device selection table to user.")  # Log table display.
        user_input = InputUtils.safe_input(  # Read operator device choice.
            "Enter the index or name of the device to view device: ",
            context="device_inventory_selection",
        ).strip()
        logging.debug("User input for device selection: %s", user_input)  # Log raw device input.
        return PromptUtils._resolve_device_selection(user_input, index_to_device, name_to_device)  # Resolve.

    @staticmethod
    def _filter_inventory_by_type(inventory: list, device_type: str) -> list:
        """Filter inventory rows by comma-separated device types (case-insensitive); 'all' returns input as-is."""
        if device_type == "all":  # No filter needed
            return inventory
        requested_types = [dtype.strip() for dtype in device_type.split(",")]  # Split requested filter
        return [device for device in inventory if device.get("type", "").lower() in requested_types]

    @staticmethod
    def _fetch_and_filter_devices(site_id: str, device_type: str) -> list | None:
        """Fetch the full site inventory (``type=all``) and filter locally to ``device_type``."""
        mh = importlib.import_module("MistHelper")
        rawdata = mistapi.api.v1.sites.devices.listSiteDevices(mh.apisession, site_id, type="all").data  # Fetch
        if not rawdata:  # Empty inventory path
            print("No devices found for the selected site.")
            logging.warning("No devices found for site_id: %s", site_id)
            return None
        filtered = PromptUtils._filter_inventory_by_type(rawdata, device_type)  # Apply type filter
        if not filtered:  # Filter produced empty set
            print(f"No devices of type '{device_type}' found at the selected site.")
            logging.warning("No devices of type '%s' found for site_id: %s", device_type, site_id)
            return None
        return filtered

    @staticmethod
    def _export_and_index_inventory(rawdata: list, csv_filename: str) -> tuple:
        """Sort + flatten + CSV-export ``rawdata`` and return ``(table, index_map, name_map)``."""
        mh = importlib.import_module("MistHelper")
        inventory = sorted(rawdata, key=lambda x: x.get("model", ""))  # Sort by model.
        inventory = DataProcessingUtils.flatten_nested_fields(inventory)  # Flatten nested fields.
        inventory = DataProcessingUtils.escape_multiline(inventory)  # type: ignore[no-untyped-call]
        mh.DataExporter.write_with_format_selection(inventory, csv_filename)  # type: ignore[no-untyped-call]
        logging.info("Device inventory for site_id written to %s", csv_filename)  # Log CSV write location.
        table = PrettyTable()  # Build selection table.
        table.field_names = ["Index", "name", "mac", "model", "serial"]  # Columns.
        index_to_device: dict = {}  # Index lookup.
        name_to_device: dict = {}  # Name lookup.
        for idx, item in enumerate(inventory):  # Build rows.
            table.add_row(
                [idx, item.get("name", ""), item.get("mac", ""), item.get("model", ""), item.get("serial", "")]
            )
            index_to_device[idx] = item  # Map index to device.
            name_to_device[item.get("name", "")] = item  # Map name to device.
        return table, index_to_device, name_to_device  # Return all three for caller.

    @staticmethod
    def _resolve_device_selection(user_input: str, index_to_device: dict, name_to_device: dict) -> str | None:
        """Resolve ``user_input`` to a device id by index or name; return None on miss."""
        normalized = user_input[1:] if user_input.startswith(".") else user_input  # Strip leading dot.
        if normalized.isdigit():  # Numeric index path.
            idx = int(normalized)  # Parse index.
            if idx in index_to_device:  # Valid index.
                device_id = index_to_device[idx].get("id")  # Read id.
                logging.info("User selected device by index: %s (device_id: %s)", idx, device_id)  # Log.
                return device_id  # type: ignore[no-any-return]
            logging.error(" Invalid index.")  # Log invalid index.
            return None  # Abort.
        if normalized in name_to_device:  # Name match path.
            device_id = name_to_device[normalized].get("id")  # Read id by name.
            logging.info("User selected device by name: %s (device_id: %s)", normalized, device_id)  # Log.
            return device_id  # type: ignore[no-any-return]
        logging.error(" Device not found by name or index.")  # Log not-found.
        return None  # Abort.

    @staticmethod
    def select_site_id_from_csv(csv_file: str = "SiteList.csv") -> str | None:  # Prompt site id from CSV.
        """Prompt user to select a site by index or name from csv_file; returns the site ID or None."""
        mh = importlib.import_module("MistHelper")
        CacheUtils.check_and_generate_csv(csv_file, OrgSiteExporter.sites)  # Ensure site CSV exists/fresh.
        index_to_site, name_to_site = PromptUtils._load_site_csv_maps(csv_file)  # Read CSV into index/name maps.
        print("\nAvailable Sites:")  # Print available sites heading.
        for idx, row in index_to_site.items():  # Enumerate site rows.
            print(f"[{idx}] {row.get('name', 'Unnamed')}")  # Print each site option.
        user_input = InputUtils.safe_input("\nEnter site index or name: ", context="site_selection").strip()
        logging.debug("User input for site selection: %s", user_input)  # Log raw site input.
        if user_input.isdigit():  # Branch: numeric index choice.
            site_id = PromptUtils._pick_site_by_index(int(user_input), index_to_site)  # Resolve by index.
            if site_id is not None:  # Cache successful selection.
                mh.LAST_SELECTED_SITE_ID = site_id  # Remember last selected site (module attr assignment).
            return site_id  # Return resolved id (or None on invalid index).
        if user_input in name_to_site:  # Branch: name match.
            site_id = PromptUtils._pick_site_by_name(user_input, name_to_site)  # Resolve by name.
            mh.LAST_SELECTED_SITE_ID = site_id  # Remember last selected site (module attr assignment).
            return site_id  # Return resolved id.
        print(" Site not found by name or index.")  # Report not-found site.
        logging.warning("Site not found by name or index: %s", user_input)  # Log not-found site.
        return None  # Abort on not found.

    @staticmethod
    def _load_site_csv_maps(csv_file: str) -> tuple[dict[int, dict], dict[str, dict]]:  # type: ignore[type-arg]
        """Read site CSV at FilePathUtils.get_csv_path(csv_file) and return (index_to_site, name_to_site) maps."""
        csv_file_path = FilePathUtils.get_csv_path(csv_file)  # Resolve CSV file path.
        with open(csv_file_path, encoding="utf-8") as file:  # Open the site CSV.
            reader = list(csv.DictReader(file))  # Read all CSV rows.
        index_to_site = {i: row for i, row in enumerate(reader)}  # Map index to site row.
        name_to_site = {row["name"]: row for row in reader if "name" in row}  # Map name to site row.
        return index_to_site, name_to_site

    @staticmethod
    def _pick_site_by_index(idx: int, index_to_site: dict[int, dict]) -> str | None:  # type: ignore[type-arg]
        """Resolve a numeric site index to a site_id; print/log selection or invalid-index message."""
        if idx not in index_to_site:  # Validate index exists.
            print(" Invalid index.")  # Reject out-of-range index.
            logging.warning("Invalid site index entered: %s", idx)  # Log invalid index.
            return None  # Abort on invalid index.
        site_id = index_to_site[idx].get("id")  # Read selected site id.
        print(f"! Selected site: {index_to_site[idx].get('name')} (ID: {site_id})")  # Confirm site selection.
        logging.info("User selected site by index: %s (site_id: %s)", idx, site_id)  # Log index selection.
        return site_id  # Return selected site id.

    @staticmethod
    def _pick_site_by_name(name: str, name_to_site: dict[str, dict]) -> str | None:  # type: ignore[type-arg]
        """Resolve a site name to a site_id; print/log the selection."""
        site_id = name_to_site[name].get("id")  # Read site id by name.
        print(f"! Selected site: {name} (ID: {site_id})")  # Confirm site selection.
        logging.info("User selected site by name: %s (site_id: %s)", name, site_id)  # Log name selection.
        return site_id  # Return selected site id.

    @staticmethod
    def select_site() -> str | None:  # Convenience site selector.
        """Prompt the user to select a site and return the site_id.

        Uses the existing CSV-based site selection functionality.

        Returns:
            str: The selected site ID or None if no selection made
        """
        return PromptUtils.select_site_id_from_csv()  # Delegate to CSV selector.

    @staticmethod
    def select_site_with_logging() -> str | None:  # Site selector with logging.
        """Prompt the user to select a site from the CSV list and log the selection.

        Returns:
            str: The selected site ID or None if no selection made
        """
        logging.info("Prompting user to select a site from SiteList.csv...")  # Log selection prompt start.
        site_id = PromptUtils.select_site_id_from_csv()  # Prompt site from CSV.
        if site_id:  # Handle successful selection.
            logging.info("! Selected site ID: %s", site_id)  # Log selected site id.
        else:
            logging.error(" No site selected. User may have entered an invalid value or cancelled the prompt.")
        return site_id  # Return selected site id.

    # PromptUtils.select_device removed per issue #431 (ARCH-DELEGATE).
    # Callers now use PromptUtils.select_device_id_from_inventory(site_id, device_type)
    # directly -- it is the canonical implementation and accepts the same arguments.

    @staticmethod
    def _determine_search_scope(site_id: str | None) -> str | None | Literal[False]:  # Determine client search scope.
        """Resolve search scope: provided site_id, prompted site_id, None (org-wide), or False (user cancelled)."""
        if site_id:  # Use provided site directly.
            return site_id  # Return supplied site id.
        scope_choice = (  # Prompt for scope choice.
            InputUtils.safe_input(
                "Search scope - (s)ite-specific or (o)rganization-wide? [s/o]: ",
                context="client_search_scope",
            )
            .strip()
            .lower()
        )
        if scope_choice == "s":  # Branch: single-site scope.
            selected_site = PromptUtils.select_site()  # Prompt to pick a site.
            if not selected_site:  # Handle no-site selection.
                print(" No site selected.")  # Tell operator none selected.
                return False  # Signal scope failure.
            return selected_site  # Return chosen site scope.
        return None  # Org-wide search

    @staticmethod
    def _fetch_all_clients(org_id: str, site_id: str | None) -> list[dict]:  # type: ignore[type-arg]
        """Fetch wireless and wired clients from site or org.

        Returns:
            List of client dictionaries with client_type added.
        """
        all_clients = []  # Combined client accumulator.

        if site_id:  # Branch: site-scoped search.
            print("! Searching for clients in selected site...")  # Inform operator of site search.
            wireless = PromptUtils._fetch_site_wireless_clients(site_id)  # Fetch site wireless clients.
            wired = PromptUtils._fetch_site_wired_clients(site_id)  # Fetch site wired clients.
        else:
            print("! Searching for clients across organization...")  # Inform operator of org search.
            wireless = PromptUtils._fetch_org_wireless_clients(org_id)  # Fetch org wireless clients.
            wired = PromptUtils._fetch_org_wired_clients(org_id)  # Fetch org wired clients.

        all_clients.extend(wireless)  # Add wireless clients to list.
        all_clients.extend(wired)  # Add wired clients to list.

        return sorted(all_clients, key=lambda x: (x.get("hostname", ""), x.get("mac", "")))

    @staticmethod
    def _fetch_site_wireless_clients(site_id: str) -> list[dict]:  # type: ignore[type-arg]
        """Fetches wireless clients for a specific site."""
        mh = importlib.import_module("MistHelper")
        try:
            response = mistapi.api.v1.sites.clients.searchSiteWirelessClients(mh.apisession, site_id, limit=1000)
            clients = mistapi.get_all(response=response, mist_session=mh.apisession) or []  # Page through all results.
            for client in clients:  # Tag each client.
                client["client_type"] = "wireless"  # Mark as wireless type.
                client["source_site_id"] = site_id  # Record source site id.
            logging.info("Found %s wireless clients in site", len(clients))  # Log wireless client count.
            return clients  # Return wireless clients.
        except Exception as exception:  # Catch fetch errors.
            logging.warning("Could not fetch wireless clients for site: %s", exception)  # Log fetch failure.
            return []  # Return empty on error.

    @staticmethod
    def _fetch_site_wired_clients(site_id: str) -> list[dict]:  # type: ignore[type-arg]
        """Fetches wired clients for a specific site."""
        mh = importlib.import_module("MistHelper")
        try:
            response = mistapi.api.v1.sites.wired_clients.searchSiteWiredClients(mh.apisession, site_id, limit=1000)
            clients = mistapi.get_all(response=response, mist_session=mh.apisession) or []  # Page through all results.
            for client in clients:  # Tag each client.
                client["client_type"] = "wired"  # Mark as wired type.
                client["source_site_id"] = site_id  # Record source site id.
            logging.info("Found %s wired clients in site", len(clients))  # Log wired client count.
            return clients  # Return wired clients.
        except Exception as exception:  # Catch fetch errors.
            logging.warning("Could not fetch wired clients for site: %s", exception)  # Log fetch failure.
            return []  # Return empty on error.

    @staticmethod
    def _fetch_org_wireless_clients(org_id: str) -> list[dict]:  # type: ignore[type-arg]
        """Fetches wireless clients for the entire organization."""
        mh = importlib.import_module("MistHelper")
        try:
            response = mistapi.api.v1.orgs.clients.searchOrgWirelessClients(mh.apisession, org_id, limit=1000)
            clients = mistapi.get_all(response=response, mist_session=mh.apisession) or []  # Page through all results.
            for client in clients:  # Tag each client.
                client["client_type"] = "wireless"  # Mark as wireless type.
            logging.info("Found %s wireless clients in organization", len(clients))  # Log wireless client count.
            return clients  # Return wireless clients.
        except Exception as exception:  # Catch fetch errors.
            logging.warning("Could not fetch wireless clients for org: %s", exception)  # Log fetch failure.
            return []  # Return empty on error.

    @staticmethod
    def _fetch_org_wired_clients(org_id: str) -> list[dict]:  # type: ignore[type-arg]
        """Fetches wired clients for the entire organization."""
        mh = importlib.import_module("MistHelper")
        try:
            response = mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients(mh.apisession, org_id, limit=1000)
            clients = mistapi.get_all(response=response, mist_session=mh.apisession) or []  # Page through all results.
            for client in clients:  # Tag each client.
                client["client_type"] = "wired"  # Mark as wired type.
            logging.info("Found %s wired clients in organization", len(clients))  # Log wired client count.
            return clients  # Return wired clients.
        except Exception as exception:  # Catch fetch errors.
            logging.warning("Could not fetch wired clients for org: %s", exception)  # Log fetch failure.
            return []  # Return empty on error.

    @staticmethod
    def _load_sites_cache(org_id: str) -> dict[str, str]:  # Load site id-to-name cache.
        """Loads site ID to name mapping for display purposes."""
        try:
            print(" Loading site information...")  # Inform operator of load.
            sites = APICoreFetchUtils.all_sites_with_limit(org_id)  # Fetch all sites for org.
            cache = {site["id"]: site["name"] for site in sites}  # Build id-to-name map.
            logging.info("Cached %s sites for client display", len(cache))  # Log cached site count.
            return cache  # Return the cache.
        except Exception as exception:  # Catch fetch errors.
            logging.warning("Could not fetch sites for display: %s", exception)  # Log fetch failure.
            return {}  # Return empty cache on error.

    @staticmethod
    def _print_client_type_summary(all_clients: list[dict]) -> None:
        """Print the wireless/wired count line and status legend for the client selection table."""
        wireless_count = sum(1 for c in all_clients if c.get("client_type") == "wireless")  # Count wireless
        wired_count = sum(1 for c in all_clients if c.get("client_type") == "wired")  # Count wired
        print(f"\n  Summary: {wireless_count} wireless, {wired_count} wired clients")
        print("\n  [+] = Online  [~] = Recently seen  [-] = Offline")
        print("---" * 20)

    @staticmethod
    def _display_client_table(all_clients: list[dict], sites_cache: dict[str, str]) -> dict[int, dict]:  # type: ignore[type-arg]
        """Render the client selection table and a summary line; return an index-to-client map for selection."""
        table = PromptUtils._build_client_table_skeleton()  # Build empty table with columns + alignment
        for idx, client in enumerate(all_clients):  # Enumerate clients for rows
            row = PromptUtils._format_client_row(idx, client, sites_cache)  # Format a client row
            table.add_row(row)
        print(f"\n  Found {len(all_clients)} clients:")
        print(table)
        PromptUtils._print_client_type_summary(all_clients)  # Type counts + legend
        return dict(enumerate(all_clients))  # Index-to-client map for caller

    @staticmethod
    def _build_client_table_skeleton() -> PrettyTable:  # Build empty client display table.
        """Build an empty PrettyTable with the client-selection columns, alignment, and per-column max widths."""
        table = PrettyTable()  # Build client display table.
        table.field_names = ["#", "Hostname", "MAC Address", "Type", "IP Address", "SSID/VLAN", "Site", "Status"]
        # Typed so PrettyTable AlignType is preserved through the tuple literal.
        column_alignments: tuple[tuple[str, Literal["l", "c", "r"]], ...] = (
            ("#", "r"),
            ("Hostname", "l"),
            ("MAC Address", "l"),
            ("Type", "c"),
            ("IP Address", "l"),
            ("SSID/VLAN", "l"),
            ("Site", "l"),
            ("Status", "c"),
        )
        for column, alignment in column_alignments:
            table.align[column] = alignment  # Apply column alignment.
        for column, width in (("Hostname", 20), ("IP Address", 16), ("SSID/VLAN", 15), ("Site", 15)):
            table.max_width[column] = width  # Cap column width.
        return table

    @staticmethod
    def _format_client_row(idx: int, client: dict, sites_cache: dict[str, str]) -> list:  # type: ignore[type-arg]
        """Formats a single client row for the selection table."""
        site_name = PromptUtils._get_client_site_name(client, sites_cache)  # Resolve site name for row.
        status = PromptUtils._get_client_status(client)  # Resolve status marker.
        hostname = PromptUtils._truncate_string(client.get("hostname", client.get("name", "Unknown")) or "Unknown", 20)
        ip_address = PromptUtils._format_client_ip(client)  # Format client IP.
        ssid_vlan = PromptUtils._format_client_ssid_vlan(client)  # Format SSID/VLAN field.

        return [  # Return formatted row cells.
            idx,
            hostname,
            client.get("mac", "Unknown"),
            client.get("client_type", "unknown")[:8],
            ip_address,
            ssid_vlan,
            PromptUtils._truncate_string(site_name, 15),
            status,
        ]

    @staticmethod
    def _get_client_site_name(client: dict, sites_cache: dict[str, str]) -> str:  # type: ignore[type-arg]
        """Gets site name from cache or returns site ID."""
        site_id = client.get("site_id", "")  # Read client site id.
        if site_id in sites_cache:  # Branch: site found in cache.
            return sites_cache[site_id]  # Return cached site name.
        return site_id if site_id else ""  # Fallback to raw site id.

    @staticmethod
    def _get_client_status(client: dict) -> str:  # type: ignore[type-arg]
        """Determines client connection status indicator."""
        if client.get("connected", True):  # Branch: client connected.
            status = "[+]"  # Mark online status.
        else:
            status = "[-]"  # Mark offline status.

        if "last_seen" in client:  # Branch: last_seen present.
            last_seen = client.get("last_seen", 0)  # Read last_seen timestamp.
            current_time = int(time.time())  # Capture current time.
            if current_time - last_seen > 300:  # More than 5 minutes ago
                status = "[~]"  # Mark recently-seen status.

        return status  # Return status marker.

    @staticmethod
    def _format_client_ip(client: dict) -> str:  # type: ignore[type-arg]
        """Formats client IP address, handling arrays."""
        ip_address = client.get("ip", "")  # Read client IP field.
        if isinstance(ip_address, list):  # Branch: IP is a list.
            return ip_address[0] if ip_address else "N/A"  # Return first IP or N/A.
        return ip_address if ip_address and ip_address != "[]" else "N/A"  # Return IP or N/A.

    @staticmethod
    def _format_client_ssid_vlan(client: dict) -> str:  # type: ignore[type-arg]
        """Formats client SSID/VLAN, handling arrays."""
        ssid_vlan = client.get("ssid", client.get("vlan", ""))  # Read SSID or VLAN field.
        if isinstance(ssid_vlan, list):  # Branch: value is a list.
            ssid_vlan = str(ssid_vlan[0]) if ssid_vlan else "N/A"  # Use first element or N/A.
        elif not ssid_vlan or ssid_vlan == "[]":  # Branch: empty value.
            ssid_vlan = "N/A"  # Default to N/A.
        return PromptUtils._truncate_string(str(ssid_vlan), 15)  # Truncate for column width.

    @staticmethod
    def _truncate_string(value: str, max_length: int) -> str:  # Truncate helper.
        """Truncates string with ellipsis if too long."""
        if len(value) > max_length:  # Branch: over max length.
            return value[: max_length - 3] + "..."  # Truncate with ellipsis.
        return value  # Return unchanged value.

    @staticmethod
    def _handle_client_selection(
        all_clients: list[dict],  # type: ignore[type-arg]
        sites_cache: dict[str, str],
        default_site_id: str | None,
    ) -> tuple[str | None, str | None, str | None]:
        """Read operator client choice. Returns (mac, type, site_id) or (None, None, None)."""
        max_index = len(all_clients) - 1  # Compute max valid index for prompt
        user_input = InputUtils.safe_input(  # Read operator choice from stdin
            f"\n  Enter client index (0-{max_index}) or 'q' to quit: ",
            context="client_selection_index",
        ).strip()
        idx = PromptClientUtils._parse_client_choice(user_input, max_index)  # Parse to validated index
        if idx is None:  # Quit / invalid / out-of-range -- abort
            return None, None, None  # Signal no selection to caller
        return PromptUtils._extract_selected_client(all_clients[idx], sites_cache, default_site_id)

    @staticmethod
    def _extract_selected_client(
        client: dict,  # type: ignore[type-arg]
        sites_cache: dict[str, str],
        default_site_id: str | None,
    ) -> tuple[str, str, str]:
        """Extracts and displays selected client information."""
        client_mac = client.get("mac", "")  # Read client MAC.
        client_type = client.get("client_type", "unknown")  # Read client type.
        client_site_id = client.get("site_id", default_site_id) or ""  # Resolve client site id.
        hostname = client.get("hostname", client.get("name", "Unknown"))  # Read hostname/name.

        print("\n Selected client:")  # Print selection heading.
        print(f"   Name: {hostname}")  # Show client name.
        print(f"   MAC: {client_mac}")  # Show client MAC.
        print(f"   Type: {client_type}")  # Show client type.
        if client_site_id and client_site_id in sites_cache:  # Branch: known site.
            print(f"   Site: {sites_cache[client_site_id]}")  # Show resolved site name.

        logging.info("User selected client: MAC=%s, type=%s, site=%s", client_mac, client_type, client_site_id)
        return client_mac, client_type, client_site_id  # Return client id triple.
