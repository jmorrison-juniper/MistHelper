"""MSP and organization selection workflow for the interactive session."""

from __future__ import annotations  # Defer annotation evaluation for forward refs

import logging  # Standard library structured logging
from collections.abc import Callable  # Typing for the injected callbacks
from typing import Any  # Generic typing for the shared state bag


class MspOrgSelector:
    """Drive the MSP + organization selection flow after a successful login."""

    def __init__(
        self,
        state: dict[str, Any],
        safe_input: Callable[..., str],
        select_org_fallback: Callable[[], None],
    ) -> None:
        """Store mutable state and injected callbacks used by the selector."""
        self.state = state  # Shared mutable state bag persisted across the workflow
        self.safe_input = safe_input  # Injected EOF-safe input wrapper
        self.select_org_fallback = select_org_fallback  # Direct-org-select fallback callback

    def select(self) -> None:
        """Run the MSP + org selection workflow, mutating state in place."""
        msp_privileges = self.state.get("msp_privileges", [])  # Cached MSP grants from login
        logging.info("MspOrgSelector.select() starting with %d MSP(s)", len(msp_privileges))  # Trace
        self._print_banner()  # Render the legacy banner preserved verbatim
        if not msp_privileges:  # Operator has no MSP grants: skip straight to direct org pick
            logging.debug("No MSP grants present - delegating to direct org selector")  # Trace path
            self.select_org_fallback()  # Invoke the injected org selector callback
            return  # Nothing else to do at this layer
        chosen_msp = self._choose_msp(msp_privileges)  # Pick (or auto-pick) one MSP
        if chosen_msp is None:  # User aborted or chose to skip MSP selection
            logging.debug("MSP selection skipped - delegating to direct org selector")  # Trace path
            self.select_org_fallback()  # Fall back to direct org pick
            return  # Nothing else to do at this layer
        self._select_org_under_msp(chosen_msp)  # Fetch + pick org under the chosen MSP

    @staticmethod
    def _print_banner() -> None:
        """Print the legacy 'SELECT MSP AND ORGANIZATION' banner verbatim."""
        logging.warning("")  # Blank spacer matches legacy output exactly
        logging.warning("=" * 60)  # Top divider routed via logger
        logging.warning("  SELECT MSP AND ORGANIZATION")  # Banner heading routed via logger
        logging.warning("=" * 60)  # Bottom divider routed via logger
        logging.warning("")  # Blank spacer matches legacy output exactly

    def _choose_msp(self, msps: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Return the chosen MSP dict, auto-selecting when only one is available."""
        if len(msps) == 1:  # Auto-pick path preserves the legacy convenience behaviour
            only = msps[0]  # Single MSP available
            logging.warning(
                "  Using MSP: %s (only one available)", only["msp_name"]
            )  # Legacy message routed via logger
            logging.debug("Auto-selected the only available MSP: %s", only.get("msp_id"))  # Trace
            return only  # Caller will proceed straight to org selection
        return self._prompt_msp(msps)  # Multi-MSP case requires an interactive prompt

    def _prompt_msp(self, msps: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Render the MSP menu and read the operator selection."""
        self._render_msp_menu(msps)  # Print the numbered list of MSPs
        logging.info("Prompting operator to choose MSP from %d options", len(msps))  # Trace
        try:
            choice = self.safe_input(  # EOF-safe stdin read
                "  Select MSP (number, or Enter to skip): ", context="msp_select"
            ).strip()
        except (ValueError, SystemExit):  # Preserve legacy combined exception handling
            logging.warning("  X Invalid input - skipping MSP selection")  # Legacy console message routed via logger
            return None  # Caller will fall back to direct org selection
        if choice == "":  # Blank input means "skip MSP selection" in the legacy flow
            logging.warning("  Skipping MSP selection - using direct org access")  # Legacy message routed via logger
            return None  # Caller will fall back to direct org selection
        try:
            index = int(choice) - 1  # Convert 1-based selection to 0-based list index
        except ValueError:  # Non-numeric input falls into the legacy invalid path
            logging.warning("  X Invalid selection - skipping MSP selection")  # Legacy message routed via logger
            return None  # Caller will fall back to direct org selection
        if not (0 <= index < len(msps)):  # Out-of-range index falls into the legacy invalid path
            logging.warning("  X Invalid selection - skipping MSP selection")  # Legacy message routed via logger
            return None  # Caller will fall back to direct org selection
        logging.debug("MSP selected at index %d", index)  # Trace the picked index
        return msps[index]  # Hand the chosen MSP dict back to the caller

    @staticmethod
    def _render_msp_menu(msps: list[dict[str, Any]]) -> None:
        """Print the numbered MSP menu using the legacy formatting."""
        logging.warning("  Available MSPs:")  # Legacy header routed via logger
        for index, msp in enumerate(msps, start=1):  # 1-based numbering matches legacy UI
            msp_name = msp.get("msp_name", "Unknown")  # Preserve legacy fallback label
            msp_role = msp.get("role", "unknown")  # Preserve legacy fallback role
            logging.warning("    %d. %s (role: %s)", index, msp_name, msp_role)  # Legacy format routed via logger
        logging.warning("")  # Blank spacer matches legacy output exactly

    def _select_org_under_msp(self, msp: dict[str, Any]) -> None:
        """Fetch orgs under the chosen MSP and persist the operator's pick to state."""
        self.state["selected_msp"] = msp  # Cache the chosen MSP regardless of org outcome
        msp_id = msp["msp_id"]  # Required field per the MSP detection contract
        msp_name = msp.get("msp_name", "Unknown")  # Preserve legacy fallback label
        logging.warning("  + Selected MSP: %s", msp_name)  # Legacy console message routed via logger
        logging.warning("  Fetching organizations under %s...", msp_name)  # Legacy console message routed via logger
        apisession = self.state.get("apisession")  # Pull the live session from shared state
        if apisession is None:  # Defensive guard preserved from the legacy code path
            logging.warning("  X API session not initialized")  # Legacy console message routed via logger
            logging.error("API session not initialized when selecting MSP org")  # Legacy error log
            return  # Cannot continue without a session
        try:
            orgs = self._fetch_msp_orgs(apisession, msp_id)  # Sorted list of org dicts (or None)
        except Exception as org_error:  # Preserve legacy catch-all surface
            logging.warning("  X Error fetching MSP organizations: %s", org_error)  # Legacy message routed via logger
            logging.error("Failed to fetch MSP organizations: %s", org_error)  # Legacy error log
            return  # Bail out without mutating org_id
        if not orgs:  # Empty list or None means "no orgs to choose from"
            return  # Legacy behaviour: silently bail out after the earlier print
        chosen_org = self._paginated_pick(orgs)  # Interactive paginated org picker
        if chosen_org is None:  # User skipped/aborted the org picker
            return  # Legacy behaviour: leave org_id unchanged
        self._record_org_selection(msp_name, chosen_org)  # Persist + log the chosen org

    def _fetch_msp_orgs(self, apisession: Any, msp_id: str) -> list[dict[str, Any]] | None:
        """Call listMspOrgs and return a sorted list of org dicts (or None on bad response)."""
        mistapi_module = self._resolve_mistapi()  # Ensure SDK reference is available
        logging.info("Calling listMspOrgs for msp_id=%s", msp_id)  # Trace before SDK call
        response = mistapi_module.api.v1.msps.orgs.listMspOrgs(apisession, msp_id)  # SDK call
        if not response or not hasattr(response, "data"):  # Legacy guard for empty/invalid response
            logging.warning("  X Failed to retrieve MSP organizations")  # Legacy console message routed via logger
            logging.debug("listMspOrgs returned an empty or invalid response")  # Trace bad response
            return None  # Caller will treat as "no orgs"
        orgs_data = response.data  # SDK response payload (list or dict)
        if not isinstance(orgs_data, list):  # Normalize single-object responses to a list
            orgs_data = [orgs_data] if orgs_data else []  # Empty falsy values become empty list
        if not orgs_data:  # Empty list short-circuits to the legacy "no orgs" message
            logging.warning("  No organizations found under this MSP")  # Legacy console message routed via logger
            logging.debug("listMspOrgs returned an empty org list")  # Trace empty list
            return []  # Caller will short-circuit on empty list
        orgs_data = sorted(orgs_data, key=lambda org: org.get("name", "").lower())  # Stable sort
        logging.warning("  Found %d organization(s):", len(orgs_data))  # Legacy console message routed via logger
        logging.warning("")  # Blank spacer matches legacy output exactly
        logging.debug("listMspOrgs returned %d orgs (sorted by name)", len(orgs_data))  # Trace
        return orgs_data  # Hand the sorted list back to the picker

    def _resolve_mistapi(self) -> Any:
        """Return the mistapi SDK module, importing it if state does not have it."""
        mistapi_module = self.state.get("mistapi")  # Prefer the SDK reference already in state
        if mistapi_module is not None:  # Fast path when MistHelper.py has imported it
            return mistapi_module  # Use the existing reference
        logging.info("Resolving mistapi SDK via fallback import (MSP org fetch)")  # Trace import
        import mistapi as mistapi_fallback  # Deferred import keeps module load cheap

        self.state["mistapi"] = mistapi_fallback  # Cache the SDK reference in shared state
        return mistapi_fallback  # Hand the SDK reference back to the caller

    def _paginated_pick(self, orgs: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Render the full-index org picker loop and return the chosen org (or None)."""
        current_page = 0  # Single-page index: the entire org list always renders at once
        total_pages = 1  # Force single-page rendering so the full org list shows as one index
        while True:  # Loop until the user picks an org, skips, or aborts
            self._render_page(orgs, current_page, total_pages)  # Print the current page contents
            try:
                choice = self.safe_input("  Selection: ", context="org_select").strip().lower()  # EOF-safe
            except SystemExit:  # safe_input raises SystemExit on EOF
                logging.debug("Org picker aborted via EOF")  # Trace abort path
                return None  # Treat EOF as a skip
            action, current_page, picked = self._interpret_choice(  # Decode the operator choice
                choice, current_page, total_pages, orgs
            )
            if action == "quit":  # Operator chose to skip the org picker
                return None  # Legacy behaviour: leave org_id unchanged
            if action == "select":  # Operator picked a valid org number
                return picked  # Hand the picked org back to the caller

    def _render_page(
        self,
        orgs: list[dict[str, Any]],
        current_page: int,
        total_pages: int,
    ) -> None:
        """Print the full org list as a single numbered index plus the skip hint."""
        start_index = 0  # Always start at the first org so the entire list renders as one index
        end_index = len(orgs)  # Render every org in a single full index (no pagination)
        for org_index in range(start_index, end_index):  # Iterate every org index in the full list
            org = orgs[org_index]  # Current org dict
            org_name = org.get("name", "Unknown")  # Preserve legacy fallback label
            org_id_preview = org.get("id", "N/A")[:8]  # Preserve legacy 8-char id preview
            logging.warning(
                "    %3d. %s (%s...)", org_index + 1, org_name, org_id_preview
            )  # Legacy format routed via logger
        logging.warning("")  # Blank spacer matches legacy output exactly
        if total_pages > 1:  # Multi-page mode prints the page counter + nav hint
            logging.warning("  Page %d/%d", current_page + 1, total_pages)  # Legacy page indicator routed via logger
            logging.warning(
                "  Enter number to select, 'n' for next page, 'p' for previous, 'q' to skip"
            )  # Legacy hint routed via logger
        else:
            logging.warning("  Enter number to select, or 'q' to skip")  # Legacy single-page hint routed via logger

    @staticmethod
    def _interpret_choice(
        choice: str,
        current_page: int,
        total_pages: int,
        orgs: list[dict[str, Any]],
    ) -> tuple[str, int, dict[str, Any] | None]:
        """Decode the operator's choice into (action, next_page, picked_org)."""
        if choice in {"", "q"}:  # Blank or 'q' both mean "skip" in the legacy flow
            logging.warning("  Skipping org selection")  # Legacy console message routed via logger
            return ("quit", current_page, None)  # Loop caller will exit with None
        if choice == "n" and current_page < total_pages - 1:  # Next-page navigation
            return ("nav", current_page + 1, None)  # Loop caller will re-render the next page
        if choice == "p" and current_page > 0:  # Previous-page navigation
            return ("nav", current_page - 1, None)  # Loop caller will re-render the previous page
        try:
            index = int(choice) - 1  # Convert 1-based selection to 0-based list index
        except ValueError:  # Non-numeric input falls into the legacy invalid-input path
            logging.warning("  X Invalid input - try again")  # Legacy console message routed via logger
            return ("nav", current_page, None)  # Stay on the same page and loop again
        if 0 <= index < len(orgs):  # Index is in range: this is a valid selection
            return ("select", current_page, orgs[index])  # Hand the picked org back via loop caller
        logging.warning("  X Invalid number - try again")  # Out-of-range index routed via logger
        return ("nav", current_page, None)  # Stay on the same page and loop again

    def _record_org_selection(self, msp_name: str, org: dict[str, Any]) -> None:
        """Persist the chosen org to state and emit the legacy confirmation output."""
        selected_org_id = org.get("id")  # Pull the org UUID from the chosen entry
        selected_org_name = org.get("name", "Unknown")  # Preserve legacy fallback label
        self.state["org_id"] = selected_org_id  # Update shared state with the new org id
        logging.warning("")  # Blank spacer matches legacy output exactly
        logging.warning("  + Selected organization: %s", selected_org_name)  # Legacy console message routed via logger
        logging.warning("  + Organization ID: %s", selected_org_id)  # Legacy console message routed via logger
        logging.info(  # Legacy info log preserved verbatim
            "User selected org: %s (%s) under MSP: %s",
            selected_org_name,
            selected_org_id,
            msp_name,
        )
