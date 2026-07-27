"""PromptClientUtils -- interactive client-selection prompts.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 35).
Backs client-selection UX across the CLI (capture, SSH shell, and site
device prompts). Direct imports cover stdlib + installed packages
(mistapi, prettytable). Live-global reads (``apisession``, ``InputUtils``,
``PromptUtils``, ``ConfigUtils``) are resolved via lazy
``mh = importlib.import_module("MistHelper")`` inside each helper. Callers
continue to reach the class through the ``MistHelper.PromptClientUtils``
re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace for client-selection lifecycle events.
from typing import Any  # WHY: mistapi response payloads are duck-typed here.

import mistapi  # WHY: direct calls to sites.clients + sites.wired_clients search endpoints.
from prettytable import PrettyTable  # WHY: render the interactive client selection table.


class PromptClientUtils:
    """Client Selection Prompts.

    Handles client MAC selection, client selection, and combined site-device selection.
    Extracted from PromptUtils.
    """

    @staticmethod
    def select_client_mac(site_id: str) -> str | None:
        """Prompt the operator to select a connected client at ``site_id`` and return its MAC."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils.
        logging.debug("Fetching connected clients for site: %s", site_id)  # Trace start.
        try:
            all_clients = PromptClientUtils._fetch_all_clients_for_site(site_id)  # Wireless + wired tagged.
            if not all_clients:  # No clients to choose from.
                # WHY (#886 Phase 2): consolidate print+warning into single WARNING so operator sees notice
                # on the default root-logger config (INFO is suppressed by default).
                logging.warning("No connected clients found at the selected site (site_id=%s).", site_id)
                return None  # Abort.
            all_clients.sort(key=lambda x: (x.get("hostname", ""), x.get("username", "")))  # Sort.
            table, index_to_client = PromptClientUtils._build_client_selection_table(all_clients)  # Build UI.
            PromptClientUtils._render_client_selection_prompt(table, len(all_clients))  # Print prompt.
            user_input = mh.InputUtils.safe_input("\nEnter your choice: ", context="client_selection").strip()
            logging.debug("User input for client selection: %s", user_input)  # Log raw choice.
            return PromptClientUtils._handle_client_selection_input(user_input, index_to_client)  # Resolve.
        except Exception as error:  # Catch fetch + render failures.
            # WHY (#886 Phase 2): consolidate print+exception into single logging.exception
            # (operator-visible ERROR + stack trace).
            logging.exception("Error fetching clients: %s", error)
            return None  # Abort on error.

    @staticmethod
    def _log_combined_client_counts(wireless: list | None, wired: list | None) -> None:
        """Log counts when at least one of the two client lists has data. Silent on fully empty input."""
        wireless_list = wireless or []  # Coerce None -> empty for safe len()
        wired_list = wired or []  # Coerce None -> empty for safe len()
        if not (wireless_list or wired_list):  # Nothing to log when both empty
            return
        logging.info(
            "Found %s connected clients at site (%s wireless, %s wired)",
            len(wireless_list) + len(wired_list),  # Combined total
            len(wireless_list),  # Per-type breakdown
            len(wired_list),
        )

    @staticmethod
    def _fetch_all_clients_for_site(site_id: str) -> list:
        """Fetch wireless and wired clients for ``site_id`` and tag each with a ``connection_type``."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession.
        wireless = PromptClientUtils._normalize_clients_response(
            mistapi.api.v1.sites.clients.searchSiteWirelessClients(mh.apisession, site_id)
        )  # Wifi search + payload normalize
        wired = PromptClientUtils._normalize_clients_response(
            mistapi.api.v1.sites.wired_clients.searchSiteWiredClients(mh.apisession, site_id)
        )  # Wired search + payload normalize
        PromptClientUtils._tag_connection_type(wireless, "Wireless")  # Tag wireless rows in place
        PromptClientUtils._tag_connection_type(wired, "Wired")  # Tag wired rows in place
        all_clients = (wireless or []) + (wired or [])  # Combined list (handle None payloads safely)
        PromptClientUtils._log_combined_client_counts(wireless, wired)  # Operator-visible count log
        return all_clients  # Return combined list

    @staticmethod
    def _normalize_clients_response(response: Any) -> list:
        """Pull ``results`` from a Mist search response payload regardless of shape."""
        data = response.data  # Raw payload from mistapi.
        return data.get("results", []) if hasattr(data, "get") else data  # Dict or list.

    @staticmethod
    def _tag_connection_type(clients: list | None, label: str) -> None:
        """Tag each ``client`` dict with ``connection_type=label``. Tolerate empty/None."""
        if not clients:  # Nothing to tag.
            return  # No-op when empty.
        for client in clients:  # Iterate clients.
            client["connection_type"] = label  # Mark connection type in place.

    @staticmethod
    def _build_client_selection_table(all_clients: list) -> tuple:
        """Build the PrettyTable and ``index_to_client`` map for the client selection UI."""
        table = PrettyTable()  # Build selection table.
        table.field_names = ["Index", "Hostname/User", "MAC", "IP", "Type", "SSID/VLAN"]  # Columns.
        table.max_width["Hostname/User"] = 25  # Cap hostname width.
        index_to_client: dict = {}  # Index lookup.
        for idx, client in enumerate(all_clients):  # Iterate to build rows.
            hostname = client.get("hostname", client.get("username", "Unknown"))[:25]  # Hostname or user.
            mac = client.get("mac", "Unknown")  # MAC fallback.
            ip = client.get("ip", "Unknown")  # IP fallback.
            conn_type = client.get("connection_type", "Unknown")  # Connection type for branching.
            network = client.get("ssid", "N/A") if conn_type == "Wireless" else f"VLAN {client.get('vlan_id', 'N/A')}"
            table.add_row([idx, hostname, mac, ip, conn_type, network])  # Append row.
            index_to_client[idx] = client  # Map index to client.
        return table, index_to_client  # Return both for caller.

    @staticmethod
    def _render_client_selection_prompt(table: PrettyTable, count: int) -> None:
        """Print the standard header + table + options block for client selection.

        Why:
            Post-#886 Phase 2 the render pipeline goes through ``logging.warning``
            so operators still see the prompt UI on the default root-logger config
            (INFO is suppressed) while satisfying the ruff T20 print/pprint ban.
        """
        logging.warning("\n%s", "=" * 80)  # Header rule.
        logging.warning(" SELECT CONNECTED CLIENT")  # Title.
        logging.warning("%s", "=" * 80)  # Header rule.
        logging.warning("  Found %d connected clients", count)  # Count.
        logging.warning("%s", "=" * 80)  # Separator.
        logging.warning("%s", table)  # Render table.
        logging.warning("\nOptions:")  # Options heading.
        logging.warning("  - Enter index number to select a client")  # Index option.
        logging.warning("  - Enter 'm' to manually type MAC address")  # Manual option.
        logging.warning("  - Enter 'c' to cancel")  # Cancel option.

    @staticmethod
    def _handle_client_selection_input(user_input: str, index_to_client: dict) -> str | None:
        """Resolve ``user_input`` to a MAC: manual entry, cancel, or numeric index lookup."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils.
        if user_input.lower() == "m":  # Manual MAC path.
            manual_mac = mh.InputUtils.safe_input("Enter client MAC address: ", context="manual_mac")  # Prompt.
            logging.info("User chose manual MAC entry: %s", manual_mac)  # Log manual choice.
            return manual_mac  # type: ignore[no-any-return]  # Return typed MAC.
        if user_input.lower() == "c":  # Cancel path.
            logging.info("User cancelled client selection")  # Log cancel.
            return None  # Abort selection.
        if not user_input.isdigit():  # Bad input path.
            # WHY (#886 Phase 2): consolidate print+error into single WARNING so operator sees
            # the validation hint on the default root-logger config.
            logging.warning("Please enter a valid index number, 'm' for manual, or 'c' to cancel (got %r).", user_input)
            return None  # Abort selection.
        idx = int(user_input)  # Parse index.
        if idx not in index_to_client:  # Out of range path.
            # WHY (#886 Phase 2): consolidate print+error into single WARNING for operator visibility.
            logging.warning("Invalid index: %s", idx)
            return None  # Abort selection.
        return PromptClientUtils._finalize_client_choice(idx, index_to_client[idx])  # Success path.

    @staticmethod
    def _finalize_client_choice(idx: int, client: dict) -> str | None:
        """Print + log the operator's chosen client and return its MAC."""
        client_mac = client.get("mac")  # Read MAC.
        client_hostname = client.get("hostname", client.get("username", "Unknown"))  # Hostname for log.
        conn_type = client.get("connection_type", "Unknown")  # Connection type for log.
        # WHY (#886 Phase 2): consolidate print+info into single WARNING so the "Selected: ..."
        # confirmation surfaces on the default root-logger config (INFO is suppressed).
        logging.warning(
            "Selected: %s (%s) - MAC: %s (idx=%s)",
            client_hostname,
            conn_type,
            client_mac,
            idx,
        )
        return client_mac  # type: ignore[no-any-return]  # Return chosen MAC.

    @staticmethod
    def _parse_client_choice(user_input: str, max_index: int) -> int | None:
        """Parse client-selection input to a validated 0..max_index, or None for quit/invalid."""
        if user_input.lower() in ("q", "quit", "exit"):  # Explicit quit commands
            # WHY (#886 Phase 2): retire print() in favor of logging.warning (surfaces on default root-logger).
            logging.warning("Exiting client selection...")
            return None  # Signal quit to caller
        try:
            idx = int(user_input)  # Parse numeric index
        except ValueError:  # Non-numeric, non-quit input
            # WHY (#886 Phase 2): retire print() in favor of logging.warning (surfaces on default root-logger).
            logging.warning("Please enter a valid number or 'q' to quit.")
            return None  # Signal invalid input
        if not 0 <= idx <= max_index:  # Out-of-range numeric input
            # WHY (#886 Phase 2): retire print() in favor of logging.warning (surfaces on default root-logger).
            logging.warning("Invalid index. Please enter a number between 0 and %d.", max_index)
            return None  # Signal out-of-range
        return idx  # Validated index in range

    @staticmethod
    def select_client(site_id: str | None = None) -> tuple[str | None, str | None, str | None]:
        """Prompt user to select a wireless/wired client. Returns (mac, type, site_id) or (None,None,None)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of PromptUtils + ConfigUtils.
        # WHY (#886 Phase 2): retire print() decorations in favor of logging.warning
        # (visible on default root-logger config while satisfying the ruff T20 ban).
        logging.warning("\n  Client Selection")
        logging.warning("%s", "=" * 30)
        site_id = mh.PromptUtils._determine_search_scope(site_id)  # type: ignore[assignment]
        if site_id is False:  # type: ignore[comparison-overlap]  # User explicitly cancelled
            return None, None, None  # Abort when no scope resolved.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org id from cache/prompt.
        try:
            return PromptClientUtils._run_client_selection_flow(org_id, site_id)  # Run fetch/display/select flow.
        except Exception as exception:  # Catch selection errors.
            # WHY (#886 Phase 2): consolidate print+error into single logging.error (surfaces on default root-logger).
            logging.error("Error searching for clients: %s", exception)
            return None, None, None  # Abort on error.

    @staticmethod
    def _run_client_selection_flow(  # Fetch -> display -> prompt for client.
        org_id: str, site_id: str | None
    ) -> tuple[str | None, str | None, str | None]:
        """Fetch all clients for org/site, render table, and prompt the user to pick one (returns selection tuple)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of PromptUtils facade.
        all_clients = mh.PromptUtils._fetch_all_clients(org_id, site_id)  # Fetch all clients for org/site.
        if not all_clients:  # Handle empty client set.
            # WHY (#886 Phase 2): retire print() in favor of logging.warning (surfaces on default root-logger).
            logging.warning("No clients found.")
            return None, None, None  # Abort with empty result.
        sites_cache = mh.PromptUtils._load_sites_cache(org_id)  # Load sites cache for names.
        mh.PromptUtils._display_client_table(all_clients, sites_cache)  # Display the client table.
        return mh.PromptUtils._handle_client_selection(all_clients, sites_cache, site_id)  # type: ignore[no-any-return]

    @staticmethod
    def select_site_and_device_ids(site_id=None, device_id=None):  # Prompt for site and device ids.
        """Return site_id and device_id, either from arguments or via interactive prompts.

        Args:
            site_id: Optional pre-selected site ID
            device_id: Optional pre-selected device ID

        Returns:
            tuple: (site_id, device_id) or (None, None) if selection failed
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of PromptUtils facade.
        if not site_id:  # Resolve site when not supplied.
            site_id = mh.PromptUtils.select_site_id_from_csv()  # Prompt site from CSV.
            if not site_id:  # Handle no-site selection.
                # WHY (#886 Phase 2): retire print() in favor of logging.warning (surfaces on default root-logger).
                logging.warning("No site selected.")
                return None, None  # Abort with no ids.

        if not device_id:  # Resolve device when not supplied.
            device_id = mh.PromptUtils.select_device_id_from_inventory(site_id, device_type="all")
            if not device_id:  # Handle no-device selection.
                # WHY (#886 Phase 2): retire print() in favor of logging.warning (surfaces on default root-logger).
                logging.warning("No device selected.")
                return None, None  # Abort with no ids.

        return site_id, device_id  # Return resolved id pair.
