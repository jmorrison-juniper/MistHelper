"""WLANRadiusTimerManager extracted from MistHelper.

Interactive WLAN RADIUS authentication timer management (Menu 148). Owns
the top-level orchestration originally defined as class
WLANRadiusTimerManager in MistHelper.py.

Runtime dependencies (apisession module-global, and the utility
classes InputUtils / PromptUtils / ConfigUtils) are still
owned by MistHelper.py. They are resolved lazily via the module-level
_MH proxy so the extracted module keeps its import graph flat, live
re-bindings of apisession (for example after interactive login) are always
honoured, and monkeypatched attributes in tests continue to work.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import importlib  # Late-import MistHelper module to avoid circular src<->MistHelper dependency
import logging  # Structured action logging required by coding standards
from typing import Any, cast  # Loose typing for late-bound MistHelper attributes; cast for Any-narrowing returns

import mistapi  # Direct dependency: Mist API SDK used throughout the class body


class _MistHelperProxy:  # Attribute forwarder to MistHelper module attributes
    """Forward attribute access to the currently-loaded MistHelper module."""

    def __getattr__(self, name: str) -> Any:  # Called only when the attribute is not found normally
        """Resolve name against the live MistHelper module (call-time lookup)."""
        misthelper_module = importlib.import_module("MistHelper")  # Lazy import at call time
        return getattr(misthelper_module, name)  # Fetch the current bound value from MistHelper


_MH = _MistHelperProxy()  # Sole module-level proxy handle used inside the class body


class WLANRadiusTimerManager:  # Menu 148 entrypoint for WLAN RADIUS timer edits
    """Interactive WLAN RADIUS authentication timer management.

    Workflow:
    1. Select site
    2. List WLANs using RADIUS/RadSec authentication
    3. Show inheritance information (site-level vs template-level)
    4. Allow modification of auth_servers_timeout, auth_servers_retries,
       auth_server_selection, and fast_dot1x_timers
    5. Push changes to appropriate endpoint (site WLAN or template)

    SECURITY: Modifies WLAN authentication configuration - requires explicit 'APPLY' confirmation.

    Usage:
        WLANRadiusTimerManager().manage()
    """

    def __init__(self, debug: bool = False):  # Constructor -- initialize workflow state
        """Initialize manager with debug mode setting."""
        self.debug = debug  # Debug flag toggles verbose logging during manage()
        self.original_log_level: int | None = None  # Saved root logger level so debug mode can be reverted
        self.site_id: str | None = ""  # Target site UUID (populated by _select_site)
        self.org_id: str | None = ""  # Owning org UUID (populated by _get_org_id)
        self.site_name: str = ""  # Human-friendly site name for prompts and logs
        self.site_info: dict[str, Any] = {}  # Cached site record from mistapi.getSiteInfo
        self.site_template_id: str | None = None  # UUID of the site template applied to the site (if any)
        self.template_name: str | None = None  # Human-friendly template name for prompts and logs
        self.site_wlans: list[dict[str, Any]] = []  # WLANs owned by the site directly
        self.site_template_wlans: list[dict[str, Any]] = []  # WLANs inherited from the site template
        self.org_wlans: list[dict[str, Any]] = []  # WLANs owned by the org (referenced via templates)
        self.wlan_templates: list[dict[str, Any]] = []  # Org-level WLAN template records
        self.assigned_template_ids: set = set()  # type: ignore[type-arg]  # Templates applied to this site (dedup)
        self.all_radius_wlans: list[dict[str, Any]] = []  # RADIUS-authenticated WLANs merged from all sources
        self.selected_wlan: dict[str, Any] | None = None  # The WLAN the user chose to edit
        self.new_timeout: int = 5  # New auth_servers_timeout value (seconds)
        self.new_retries: int = 2  # New auth_servers_retries value
        self.new_selection: str = "ordered"  # New auth_server_selection strategy
        self.new_fast: bool = False  # New fast_dot1x_timers flag

    def _get_selected_wlan(self) -> dict[str, Any]:  # nosec B101 -- helper wraps runtime assertion
        """Get selected WLAN with assertion that it exists."""
        assert self.selected_wlan is not None, "No WLAN selected"  # nosec B101
        return self.selected_wlan  # Return the confirmed-non-None WLAN dict

    def _discover_radius_wlans(self) -> bool:  # Aggregates site/org/template lookups + filtering
        """Prepare org/site context, fetch all WLANs, filter to RADIUS-only. Return False to abort the workflow."""
        if not self._select_site():  # Prompt for a site; abort if none chosen
            return False  # No site selected -- nothing to manage
        if not self._get_org_id():  # Resolve the org ID; abort if it cannot be determined
            return False  # Without an org ID we cannot fetch templates
        if not self._fetch_site_info():  # Load site details; abort on failure
            return False  # Site info is required for template resolution
        self._fetch_all_wlans()  # Gather WLANs from site, template, and org sources
        self._filter_radius_wlans()  # Reduce to only RADIUS/RadSec WLANs
        if not self.all_radius_wlans:  # No RADIUS WLANs were found
            self._print_no_wlans_message()  # Tell the user there is nothing to modify
            return False  # Exit -- no candidates to change
        return True  # Discovery complete; ready for interactive edit

    def manage(self) -> None:  # Public menu entrypoint invoked by MistHelper menu action 148
        """Main entry point - orchestrates the WLAN timer management workflow."""
        logging.info("Starting WLAN RADIUS authentication timer management")  # Announce the workflow start
        self._enable_debug_if_requested()  # Start verbose logging if the user asked for it
        if not self._discover_radius_wlans():  # Site + org + WLAN discovery; bail on abort.
            return  # Discovery aborted -- nothing further to do
        self._display_wlans()  # Show the user the candidate WLANs and their timers
        if not self._prompt_wlan_selection():  # Ask which WLAN to modify; abort if cancelled
            return  # User declined to pick a WLAN
        self._display_current_config()  # Show the selected WLAN's current timer config
        if not self._prompt_new_values():  # Collect new timer values; abort if cancelled
            return  # User declined to enter new values
        self._display_behavior_impact()  # Explain how the new values change behavior
        self._display_proposed_changes()  # Show a before/after diff of the settings
        if not self._confirm_changes():  # Require explicit confirmation before writing
            return  # User did not confirm -- make no changes
        self._apply_changes()  # Push the new timer settings to the Mist API
        self._print_completion_message()  # Report that the workflow finished

    def _enable_debug_if_requested(self) -> None:  # Enable debug logging if debug mode is requested
        """Enable debug logging if debug mode is requested."""
        if not self.debug:  # Debug mode was not requested
            return  # Leave the existing log level untouched
        self.original_log_level = logging.getLogger().level  # Remember the current level so it can be restored later
        logging.getLogger().setLevel(logging.DEBUG)  # Raise verbosity to DEBUG for troubleshooting
        logging.debug(
            "Debug mode enabled - verbose output active for WLAN template troubleshooting"
        )  # Confirm debug is on

    def _select_site(self) -> bool:  # Prompt user to select a site
        """Prompt user to select a site."""
        # Show the interactive site picker and capture the choice
        self.site_id = _MH.PromptUtils.select_site_with_logging()
        if not self.site_id:  # The user did not select a site
            logging.warning("No site selected for WLAN management")  # Log the empty selection
            print("\n[!] No site selected. Exiting.")  # Inform the user and bail out
            return False  # Signal the caller to abort
        return True  # A site was selected -- continue

    def _get_org_id(self) -> bool:  # Get organization ID from cache or prompt
        """Get organization ID from cache or prompt."""
        self.org_id = _MH.ConfigUtils.get_cached_or_prompted_org_id()  # Reuse a cached org ID or prompt for one
        if not self.org_id:  # The org ID could not be determined
            logging.error("Could not determine organization ID")  # Log the failure
            print("\n[!] Unable to determine organization ID. Exiting.")  # Inform the user and bail out
            return False  # Signal the caller to abort
        return True  # An org ID is available -- continue

    def _fetch_site_info(self) -> bool:  # Fetch site information from API
        """Fetch site information from API."""
        logging.info("Fetching site information for site ID: %s", self.site_id)  # Log before the API call
        try:
            # Request the site's details
            response = mistapi.api.v1.sites.sites.getSiteInfo(_MH.apisession, self.site_id)
            if response.status_code != 200:  # The API returned a non-success status
                logging.error("Failed to fetch site info: HTTP %s", response.status_code)  # Log the HTTP error
                print("\n[!] Failed to fetch site information. Exiting.")  # Inform the user
                return False  # Abort -- we cannot proceed without site info
            self.site_info = response.data  # Cache the decoded site record
            self.site_name = self.site_info.get("name", "Unknown Site")  # Extract a display name (fallback if missing)
            self.site_template_id = self.site_info.get("sitetemplate_id")  # Note any assigned site template
            self._log_site_info()  # Log the resolved site details
            return True  # Site info loaded successfully
        except Exception as error:  # Network or parsing failure
            logging.error("Error fetching site info: %s", error)  # Log the exception detail
            print(f"\n[!] Error fetching site information: {error}")  # Inform the user
            return False  # Abort on error

    def _log_site_info(self) -> None:  # Log site information details
        """Log site information details."""
        logging.info("Site: %s", self.site_name)  # Record the resolved site name
        if self.site_template_id:  # A site template is assigned
            logging.info("Site Template ID: %s", self.site_template_id)  # Log the template ID for traceability
        else:  # No template is assigned to this site
            logging.info("No site template assigned")  # Note the absence of a template

    def _fetch_all_wlans(self) -> None:  # Fetch WLANs from all sources (site, template, org)
        """Fetch WLANs from all sources (site, template, org)."""
        self._fetch_site_wlans()  # Pull WLANs defined directly on the site
        self._fetch_site_template_wlans()  # Pull WLANs inherited from the site template
        self._fetch_org_wlans()  # Pull org WLANs applied via assigned templates

    def _fetch_site_wlans(self) -> None:  # Fetch WLANs configured at site level
        """Fetch WLANs configured at site level."""
        logging.info("Fetching WLANs configured at site level...")  # Log before the API call
        try:
            # Request site-level WLANs
            response = mistapi.api.v1.sites.wlans.listSiteWlans(_MH.apisession, self.site_id)
            if response.status_code == 200:  # The request succeeded
                self.site_wlans = response.data  # Cache the returned WLAN list
                logging.info("Found %s site-level WLANs", len(self.site_wlans))  # Report how many were found
            else:  # Non-success status
                logging.warning("Failed to fetch site WLANs: HTTP %s", response.status_code)  # Warn but continue
        except Exception as error:  # Network or parsing failure
            logging.error("Error fetching site WLANs: %s", error)  # Log the exception detail

    @staticmethod
    def _extract_template_wlans(template_data: dict) -> list:  # type: ignore[type-arg]
        """Flatten the ``wlans`` map of a template to a list (returns [] when absent/empty)."""
        if "wlans" in template_data and template_data["wlans"]:  # The template embeds WLAN definitions
            return list(template_data["wlans"].values())  # Flatten the WLAN map to a list
        return []  # No embedded WLANs

    def _apply_site_template_response(self, response) -> None:  # type: ignore[no-untyped-def]
        """Persist site-template name + WLANs from a getOrgSiteTemplate response."""
        if response.status_code != 200:  # Non-success status
            logging.warning("Failed to fetch site template: HTTP %s", response.status_code)  # Warn but continue
            return
        template_data = response.data  # Decode the template record
        self.template_name = template_data.get("name", "Unknown Template")  # Capture a display name
        wlans = WLANRadiusTimerManager._extract_template_wlans(template_data)  # Delegate wlan extraction
        if wlans:  # Only persist when the template actually had WLANs
            self.site_template_wlans = wlans  # Record on instance
            logging.info("Found %s site template-level WLANs", len(self.site_template_wlans))  # Report the count

    def _fetch_site_template_wlans(self) -> None:  # Fetch WLANs from site template if assigned
        """Fetch WLANs from site template if assigned."""
        if not self.site_template_id:  # No site template is assigned
            return  # Nothing to fetch from a template
        logging.info("Fetching WLANs from site template...")  # Log before the API call
        try:
            response = mistapi.api.v1.orgs.sitetemplates.getOrgSiteTemplate(  # Request the assigned site template
                _MH.apisession, self.org_id, self.site_template_id  # Scope the lookup to this org and template
            )
            self._apply_site_template_response(response)  # Delegate response handling
        except Exception as error:  # Network or parsing failure
            logging.error("Error fetching site template: %s", error)  # Log the exception detail

    def _fetch_org_wlans(self) -> None:  # Fetch org-level WLANs using templates assigned to this site
        """Fetch org-level WLANs using templates assigned to this site."""
        logging.info("Fetching org-level WLANs to check for template-based configurations...")  # Log before the work
        try:
            self._fetch_wlan_templates()  # Load every WLAN template in the org
            self._determine_assigned_templates()  # Work out which templates apply to this site
            self._fetch_and_filter_org_wlans()  # Pull org WLANs and keep only those on assigned templates
        except Exception as error:  # Any failure across the multi-step fetch
            logging.error("Error fetching org WLANs or templates: %s", error)  # Log the exception detail

    def _fetch_wlan_templates(self) -> None:  # Fetch all WLAN templates from the organization
        """Fetch all WLAN templates from the organization."""
        # Log before the API call
        logging.debug("Fetching WLAN templates to determine which are assigned to this site")
        # Request all org templates
        response = mistapi.api.v1.orgs.templates.listOrgTemplates(_MH.apisession, self.org_id)
        if response.status_code == 200:  # The request succeeded
            self.wlan_templates = response.data  # Cache the template list
            logging.info("Found %s org-level WLAN templates", len(self.wlan_templates))  # Report the count
        else:  # Non-success status
            logging.warning("Failed to fetch WLAN templates: HTTP %s", response.status_code)  # Warn but continue

    def _determine_assigned_templates(self) -> None:  # Determine which templates are assigned to the selected site
        """Determine which templates are assigned to the selected site."""
        for wlan_template in self.wlan_templates:  # Examine every org template
            if self._is_template_assigned_to_site(wlan_template):  # The template applies to this site
                self.assigned_template_ids.add(wlan_template.get("id"))  # Remember its ID for WLAN filtering
        logging.info(
            "Found %s WLAN templates assigned to this site", len(self.assigned_template_ids)
        )  # Report the count

    @staticmethod
    def _template_matches_org_or_site(
        applies: dict[str, Any], site_id: str
    ) -> bool:  # True when the template's `applies` block targets org-wide OR explicitly lists this site
        """True when the template's `applies` block targets org-wide OR explicitly lists this site."""
        if applies.get("org_id"):  # Org-wide templates cover every site
            return True
        return site_id in applies.get("site_ids", [])  # Direct site list match

    @staticmethod
    def _template_matches_grouping(
        applies: dict[str, Any], site_groups: list[Any], site_tags: list[Any]
    ) -> bool:  # True when the template's `applies` shares any sitegroup_id or wxtag_id with this site
        """True when the template's `applies` shares any sitegroup_id or wxtag_id with this site."""
        if any(sg in applies.get("sitegroup_ids", []) for sg in site_groups):  # Group-based assignment
            return True
        return any(tag in applies.get("wxtag_ids", []) for tag in site_tags)  # Tag-based assignment

    def _is_template_assigned_to_site(
        self, wlan_template: dict[str, Any]
    ) -> bool:  # Check if a WLAN template is assigned to the current site
        """Check if a WLAN template is assigned to the current site."""
        applies = wlan_template.get("applies", {})  # The template's assignment scope rules
        if not isinstance(applies, dict):  # Malformed/absent scope object -- not applicable
            return False
        # Org-wide or explicit site scope wins immediately without checking group/tag rules.
        if self.site_id and type(self)._template_matches_org_or_site(applies, self.site_id):
            return True
        site_groups = self.site_info.get("sitegroup_ids", [])  # Site groups this site belongs to
        site_tags = self.site_info.get("wxtag_ids", [])  # Wx tags applied to this site
        return type(self)._template_matches_grouping(applies, site_groups, site_tags)  # Group/tag match

    def _collect_assigned_org_wlan(
        self, wlan: dict[str, Any]
    ) -> bool:  # Tag and keep an org WLAN if it uses a template assigned to this site (True on keep)
        """Tag and keep an org WLAN if it uses a template assigned to this site (True on keep)."""
        wlan_template_id = wlan.get("template_id")  # The template this WLAN belongs to
        if not wlan_template_id or wlan_template_id not in self.assigned_template_ids:
            return False  # Skip -- no template or not in assigned set
        self._add_org_wlan_metadata(wlan, wlan_template_id)  # Tag it with inheritance metadata
        self.org_wlans.append(wlan)  # Keep it as a relevant org WLAN
        return True

    def _fetch_and_filter_org_wlans(self) -> None:  # Fetch org WLANs and filter to those using assigned templates
        """Fetch org WLANs and filter to those using assigned templates."""
        response = mistapi.api.v1.orgs.wlans.listOrgWlans(_MH.apisession, self.org_id)  # Request every WLAN in the org
        if response.status_code != 200:  # The request failed
            logging.warning("Failed to fetch org WLANs: HTTP %s", response.status_code)  # Warn but continue
            return  # Nothing to filter without data
        all_org_wlans = response.data  # Decode the full org WLAN list
        logging.info("Found %s total org WLANs", len(all_org_wlans))  # Report the total count
        for wlan in all_org_wlans:  # Examine each org WLAN
            self._collect_assigned_org_wlan(wlan)  # Delegate per-WLAN match + keep
        if self.org_wlans:  # At least one relevant org WLAN was kept
            logging.info(
                "Found %s org WLANs using templates assigned to this site", len(self.org_wlans)
            )  # Report the count

    def _add_org_wlan_metadata(
        self, wlan: dict[str, Any], template_id: str
    ) -> None:  # Add inheritance metadata to an org WLAN
        """Add inheritance metadata to an org WLAN."""
        wlan["_inheritance_level"] = "org_wlan_with_template"  # Mark where this WLAN sits in the inheritance chain
        wlan["_wlan_template_id"] = template_id  # Record the source template ID
        template_info = next(
            (t for t in self.wlan_templates if t.get("id") == template_id), None
        )  # Find the template record
        wlan["_wlan_template_name"] = (  # Store a human-readable template name for display
            template_info.get("name", "Unknown Template")
            if template_info
            else "Unknown Template"  # Fallback if not found
        )

    def _uses_radius_auth(self, wlan: dict[str, Any]) -> bool:  # Check if WLAN uses RADIUS or RadSec authentication
        """Check if WLAN uses RADIUS or RadSec authentication."""
        has_auth_servers = bool(wlan.get("auth_servers"))  # True if any RADIUS auth servers are configured
        radsec_config = wlan.get("radsec", {})  # The RadSec sub-configuration (may be absent)
        has_radsec = (
            radsec_config.get("enabled", False) if isinstance(radsec_config, dict) else False
        )  # RadSec turned on?
        auth_config = wlan.get("auth", {})  # The auth sub-configuration (may be absent)
        uses_eap = (
            auth_config.get("type", "") in ["eap", "eap192"] if isinstance(auth_config, dict) else False
        )  # 802.1X/EAP?
        return has_auth_servers or has_radsec or uses_eap  # Any RADIUS-style auth signal counts

    def _filter_radius_wlans(self) -> None:  # Filter all WLANs to only those using RADIUS or RadSec
        """Filter all WLANs to only those using RADIUS or RadSec."""
        filtered_site = self._filter_site_wlans()  # RADIUS WLANs defined on the site
        filtered_template = self._filter_site_template_wlans()  # RADIUS WLANs from the site template
        filtered_org = self._filter_org_wlans()  # RADIUS WLANs from assigned org templates
        self.all_radius_wlans = filtered_site + filtered_template + filtered_org  # Combine all sources into one list

    def _filter_site_wlans(self) -> list[dict[str, Any]]:  # Filter site WLANs and add inheritance metadata
        """Filter site WLANs and add inheritance metadata."""
        filtered = []  # Collect site WLANs that use RADIUS auth
        for wlan in self.site_wlans:  # Examine each site-level WLAN
            if self._uses_radius_auth(wlan):  # Keep only RADIUS/RadSec/EAP WLANs
                wlan["_inheritance_level"] = "site"  # Mark its inheritance level for display
                wlan["_inheritance_source"] = f"Site: {self.site_name}"  # Describe where it comes from
                filtered.append(wlan)  # Add it to the result list
        return filtered  # Return the RADIUS site WLANs

    def _filter_site_template_wlans(
        self,
    ) -> list[dict[str, Any]]:  # Filter site template WLANs and add inheritance metadata
        """Filter site template WLANs and add inheritance metadata."""
        filtered = []  # Collect template WLANs that use RADIUS auth
        for wlan in self.site_template_wlans:  # Examine each site-template WLAN
            if self._uses_radius_auth(wlan):  # Keep only RADIUS/RadSec/EAP WLANs
                wlan["_inheritance_level"] = "site_template"  # Mark its inheritance level
                wlan["_inheritance_source"] = f"Site Template: {self.template_name}"  # Describe its source template
                wlan["_template_id"] = self.site_template_id  # Record the template ID for later writes
                filtered.append(wlan)  # Add it to the result list
        return filtered  # Return the RADIUS template WLANs

    def _filter_org_wlans(self) -> list[dict[str, Any]]:  # Filter org WLANs and add inheritance metadata
        """Filter org WLANs and add inheritance metadata."""
        filtered = []  # Collect org WLANs that use RADIUS auth
        for wlan in self.org_wlans:  # Examine each relevant org WLAN
            if self._uses_radius_auth(wlan):  # Keep only RADIUS/RadSec/EAP WLANs
                template_name_wlan = wlan.get("_wlan_template_name", "Unknown Template")  # The source template's name
                wlan["_inheritance_source"] = f"Org WLAN using template: {template_name_wlan}"  # Describe its source
                filtered.append(wlan)  # Add it to the result list
        return filtered  # Return the RADIUS org WLANs

    def _print_no_wlans_message(self) -> None:  # Print message when no RADIUS/RadSec WLANs are found
        """Print message when no RADIUS/RadSec WLANs are found."""
        print("\n[!] No WLANs using RADIUS or RadSec authentication found at this site.")
        print("[!] Only WLANs with RADIUS auth servers or RadSec configuration are shown.")
        logging.info("No RADIUS/RadSec WLANs found")

    def _display_wlans(self) -> None:  # Display all RADIUS/RadSec WLANs with current configuration
        """Display all RADIUS/RadSec WLANs with current configuration."""
        print(f"\n{'=' * 100}")  # Top border of the WLAN list banner
        print(f"RADIUS/RadSec Authenticated WLANs at Site: {self.site_name}")  # Banner title with the site name
        print(f"{'=' * 100}\n")  # Bottom border of the WLAN list banner
        for index, wlan in enumerate(self.all_radius_wlans, start=1):  # Number each WLAN from 1 for the user
            self._display_single_wlan(index, wlan)  # Render this WLAN's details
        print(f"{'=' * 100}\n")  # Closing border after the full list

    def _extract_wlan_summary_fields(
        self, wlan: dict[str, Any]
    ) -> dict[
        str, Any
    ]:  # Extract the fields needed to render one WLAN summary row from a WLAN dict (with safe defaults)
        """Extract the fields needed to render one WLAN summary row from a WLAN dict (with safe defaults)."""
        radsec_config = wlan.get("radsec", {})  # The RadSec sub-configuration (may be absent)
        return {
            "ssid": wlan.get("ssid", "Unknown SSID"),  # The WLAN's broadcast name
            "wlan_id": wlan.get("id", "Unknown ID"),  # The WLAN's unique identifier
            "enabled": wlan.get("enabled", False),  # Whether the WLAN is currently active
            "inheritance": wlan.get("_inheritance_level", "unknown"),  # Defined-at level
            "source": wlan.get("_inheritance_source", "Unknown"),  # Source description
            "timeout": wlan.get("auth_servers_timeout", 5),  # Per-attempt RADIUS timeout
            "retries": wlan.get("auth_servers_retries", 2),  # RADIUS retry count
            "selection": wlan.get("auth_server_selection", "ordered"),  # Server-selection mode
            "fast_timers": wlan.get("fast_dot1x_timers", False),  # Fast 802.1X timers flag
            "server_count": len(wlan.get("auth_servers") or []),  # RADIUS server count
            "radsec_enabled": radsec_config.get("enabled", False) if isinstance(radsec_config, dict) else False,
        }

    def _display_single_wlan(self, index: int, wlan: dict[str, Any]) -> None:  # Display a single WLAN's information
        """Display a single WLAN's information."""
        f = self._extract_wlan_summary_fields(wlan)  # Pull all summary fields with safe defaults.
        print(f"[{index}] SSID: {f['ssid']}")  # Show the menu index and SSID
        print(f"    ID: {f['wlan_id']}")  # Show the WLAN ID
        print(f"    Status: {'Enabled' if f['enabled'] else 'Disabled'}")  # Show enabled/disabled state
        print(f"    Inheritance: {f['inheritance'].upper()} - {f['source']}")  # Show where the WLAN comes from
        print("    \n    Authentication Configuration:")  # Sub-header for auth details
        print(f"      - RADIUS Servers: {f['server_count']}")  # Number of RADIUS servers
        print(f"      - RadSec: {'Enabled' if f['radsec_enabled'] else 'Disabled'}")  # RadSec on/off
        print("    \n    Current Timer Settings:")  # Sub-header for timer values
        print(f"      - auth_servers_timeout: {f['timeout']} seconds")  # Current timeout value
        print(f"      - auth_servers_retries: {f['retries']}")  # Current retry value
        print(f"      - auth_server_selection: {f['selection']}")  # Current selection mode
        print(f"      - fast_dot1x_timers: {f['fast_timers']}\n")  # Current fast-timer flag + spacer

    def _read_wlan_selection_input(
        self,
    ) -> str:  # Read the WLAN-picker input from the user, strip/lower it for normalized comparison
        """Read the WLAN-picker input from the user, strip/lower it for normalized comparison."""
        # str(...) coerces the Any return from the late-bound _MH.InputUtils.safe_input into a concrete str
        return str(
            _MH.InputUtils.safe_input(
                f"Select WLAN to modify (1-{len(self.all_radius_wlans)}) or 'q' to quit: ", context="wlan_selection"
            )
            .strip()  # Trim surrounding whitespace
            .lower()  # Normalize to lowercase so 'Q' also works
        )

    def _prompt_wlan_selection(self) -> bool:  # Prompt user to select a WLAN to modify
        """Prompt user to select a WLAN to modify."""
        try:
            selection_input = self._read_wlan_selection_input()  # Capture the normalized choice.
            if selection_input == "q":  # User chose to quit the picker
                print("\n[*] Exiting WLAN management.")  # Acknowledge the exit
                return False  # Signal the caller to abort
            selected_index = int(selection_input) - 1  # Convert the 1-based choice to a 0-based list index
            if selected_index < 0 or selected_index >= len(self.all_radius_wlans):  # Index out of range
                print(f"\n[!] Invalid selection. Must be between 1 and {len(self.all_radius_wlans)}.")
                return False  # Signal the caller to abort
            self.selected_wlan = self.all_radius_wlans[selected_index]  # Record the chosen WLAN
            return True  # A valid WLAN was selected
        except ValueError:  # The input was not a number
            print(f"\n[!] Invalid input. Please enter a number between 1 and {len(self.all_radius_wlans)}.")
            return False  # Signal the caller to abort

    def _display_current_config(self) -> None:  # Display current configuration of selected WLAN
        """Display current configuration of selected WLAN."""
        wlan = self._get_selected_wlan()  # Fetch the WLAN the user picked
        print(f"\n{'=' * 100}")  # Top border of the config banner
        print(f"Modifying WLAN: {wlan.get('ssid')}")  # Show which SSID is being edited
        print(f"Inheritance: {wlan.get('_inheritance_level', 'unknown').upper()}")  # Show where the WLAN is defined
        print(f"{'=' * 100}\n")  # Bottom border of the config banner
        print("Current Configuration:")  # Header for the current values
        print(f"  auth_servers_timeout: {wlan.get('auth_servers_timeout', 5)} seconds")  # Current per-attempt timeout
        print(f"  auth_servers_retries: {wlan.get('auth_servers_retries', 2)}")  # Current retry count
        print(
            f"  auth_server_selection: {wlan.get('auth_server_selection', 'ordered')}"
        )  # Current server-selection mode
        print(f"  fast_dot1x_timers: {wlan.get('fast_dot1x_timers', False)}")  # Whether fast 802.1X timers are on
        print("")  # Blank spacer line

    def _prompt_new_values(self) -> bool:  # Prompt user for new timer values
        """Prompt user for new timer values."""
        print("Enter new values (press Enter to keep current):\n")  # Tell the user blank entries keep current values
        try:
            self._prompt_timeout()  # Ask for the new auth_servers_timeout
            self._prompt_retries()  # Ask for the new auth_servers_retries
            self._prompt_selection()  # Ask for the new auth_server_selection
            self._prompt_fast_timers()  # Ask whether to enable fast 802.1X timers
            return True  # All prompts completed successfully
        except ValueError as error:  # A prompt received an unparseable value
            print(f"\n[!] Invalid input: {error}. Exiting.")  # Inform the user and abort
            return False  # Signal the caller to abort

    def _prompt_timeout(self) -> None:  # Prompt for auth_servers_timeout value
        """Prompt for auth_servers_timeout value."""
        wlan = self._get_selected_wlan()  # Fetch the WLAN being edited
        current = wlan.get("auth_servers_timeout", 5)  # Current timeout, defaulting to 5 seconds
        timeout_input = _MH.InputUtils.safe_input(  # Prompt with the current value as the default
            f"auth_servers_timeout (1-30) [{current}]: ", default_value=str(current), context="timeout_input"
        ).strip()  # Trim whitespace from the response
        self.new_timeout = int(timeout_input) if timeout_input else current  # Parse the entry or keep current
        if self.new_timeout < 1 or self.new_timeout > 30:  # Validate the allowed range
            print("\n[!] Timeout must be between 1 and 30 seconds. Using current value.")  # Reject out-of-range input
            self.new_timeout = current  # Fall back to the existing value

    def _prompt_retries(self) -> None:  # Prompt for auth_servers_retries value
        """Prompt for auth_servers_retries value."""
        wlan = self._get_selected_wlan()  # Fetch the WLAN being edited
        current = wlan.get("auth_servers_retries", 2)  # Current retry count, defaulting to 2
        retries_input = _MH.InputUtils.safe_input(  # Prompt with the current value as the default
            f"auth_servers_retries (0-10) [{current}]: ", default_value=str(current), context="retries_input"
        ).strip()  # Trim whitespace from the response
        self.new_retries = int(retries_input) if retries_input else current  # Parse the entry or keep current
        if self.new_retries < 0 or self.new_retries > 10:  # Validate the allowed range
            print("\n[!] Retries must be between 0 and 10. Using current value.")  # Reject out-of-range input
            self.new_retries = current  # Fall back to the existing value

    def _prompt_selection(self) -> None:  # Prompt for auth_server_selection value
        """Prompt for auth_server_selection value."""
        wlan = self._get_selected_wlan()  # Fetch the WLAN being edited
        current = wlan.get("auth_server_selection", "ordered")  # Current selection mode, defaulting to ordered
        selection_input = (  # Prompt with the current value as the default
            _MH.InputUtils.safe_input(
                f"auth_server_selection (ordered/unordered) [{current}]: ",
                default_value=current,
                context="selection_input",
            )
            .strip()  # Trim whitespace from the response
            .lower()  # Normalize to lowercase for comparison
        )
        self.new_selection = (
            selection_input if selection_input in ["ordered", "unordered"] else current
        )  # Accept only valid modes

    def _prompt_fast_timers(self) -> None:  # Prompt for fast_dot1x_timers value
        """Prompt for fast_dot1x_timers value."""
        wlan = self._get_selected_wlan()  # Fetch the WLAN being edited
        current = wlan.get("fast_dot1x_timers", False)  # Current fast-timer flag, defaulting to False
        fast_input = (  # Prompt with the current value as the default
            _MH.InputUtils.safe_input(
                f"fast_dot1x_timers (true/false) [{str(current).lower()}]: ",
                default_value=str(current).lower(),
                context="fast_timers_input",
            )
            .strip()  # Trim whitespace from the response
            .lower()  # Normalize to lowercase for comparison
        )
        self.new_fast = (
            fast_input == "true" if fast_input in ["true", "false"] else current
        )  # Parse the boolean or keep current

    def _display_behavior_impact(self) -> None:  # Display calculated authentication behavior impact
        """Display calculated authentication behavior impact."""
        wlan = self._get_selected_wlan()  # Fetch the WLAN being edited
        print(f"\n{'=' * 100}")  # Top border of the behavior banner
        print("Calculated Authentication Behavior:")  # Banner title
        print(f"{'=' * 100}\n")  # Bottom border of the behavior banner
        auth_servers = wlan.get("auth_servers", [])  # The configured RADIUS servers (may be empty)
        server_count = len(auth_servers) if auth_servers else 1  # Count servers, assuming 1 if none listed
        single_server_max = self.new_timeout * self.new_retries  # Worst-case seconds per server
        all_servers_max = single_server_max * server_count  # Worst-case seconds across every server
        self._print_radius_config(server_count)  # Show the server count and selection mode
        self._print_timeout_behavior(single_server_max)  # Show per-server timeout math
        self._print_failover_behavior(server_count, all_servers_max)  # Show failover/load-balancing behavior
        self._print_fast_timer_info()  # Show the 802.1X fast-timer impact
        self._print_client_experience(server_count, single_server_max, all_servers_max)  # Show expected client timings

    def _print_radius_config(self, server_count: int) -> None:  # Print RADIUS server configuration details
        """Print RADIUS server configuration details."""
        print("RADIUS Server Configuration:")  # Section header
        print(f"  - Configured servers: {server_count}")  # How many RADIUS servers are defined
        print(f"  - Server selection mode: {self.new_selection}")  # Ordered vs unordered selection
        print("")  # Blank spacer line

    def _print_timeout_behavior(self, single_server_max: int) -> None:  # Print timeout behavior details
        """Print timeout behavior details."""
        print("Timeout Behavior:")  # Section header
        print(f"  - Timeout per attempt: {self.new_timeout} seconds")  # Seconds before one attempt gives up
        # How many times each server is retried
        print(f"  - Retry attempts per server: {self.new_retries}")
        print(  # Worst-case time for a single server, with the math shown
            f"  - Maximum time per server: {single_server_max} seconds ({self.new_timeout}s x {self.new_retries} retries)"  # noqa: E501
        )
        print("")  # Blank spacer line

    def _print_failover_behavior(
        self, server_count: int, all_servers_max: int
    ) -> None:  # Print failover or single-server behavior details
        """Print failover or single-server behavior details."""
        if server_count > 1:  # Multiple servers -- failover/load-balancing applies
            if self.new_selection == "ordered":  # Ordered mode tries servers in sequence
                print("Failover Behavior (ordered mode):")  # Section header for ordered failover
                print("  - Primary server: Server #1 (always tries first)")  # Server #1 is always primary
                print(
                    f"  - Failover sequence: Server #1 -> Server #2 -> ... -> Server #{server_count}"
                )  # Show the order
                print("  - Returns to Server #1 for next authentication")  # Next auth restarts at the primary
                print(f"  - Maximum time if all servers fail: {all_servers_max} seconds")  # Worst-case total time
            else:  # Unordered mode load-balances across servers
                print("Load Balancing Behavior (unordered mode):")  # Section header for load balancing
                print("  - Server selection: Round-robin or random")  # How servers are chosen
                print("  - No server preference")  # No primary in unordered mode
                print(f"  - Maximum time if all servers fail: {all_servers_max} seconds")  # Worst-case total time
        else:  # Only one server is configured
            single_max = self.new_timeout * self.new_retries  # Worst-case time for the lone server
            print("Single Server Behavior:")  # Section header for the single-server case
            print(f"  - Maximum authentication failure time: {single_max} seconds")  # Worst-case failure time
        print("")  # Blank spacer line

    def _print_fast_timers_enabled(
        self, quiet_period: float, transmit_period: float, supplicant_timeout: int, max_requests: int
    ) -> None:
        """Print the ENABLED variant of the fast-802.1X-timer info block."""
        print("Fast 802.1X Timers (ENABLED):")  # Section header for the enabled case
        print(f"  - quiet-period: {quiet_period:.1f} seconds (auth_servers_timeout / 2)")
        print(f"  - transmit-period: {transmit_period:.1f} seconds (auth_servers_timeout / 2)")
        print(f"  - retries: {self.new_retries} (from auth_servers_retries)")
        print(f"  - supplicant-timeout: {supplicant_timeout} seconds (fixed default)")
        print(f"  - max-requests: {max_requests} (fixed default)\n")
        print("  Impact: Faster authentication and retry cycles")
        print("  Best for: Modern clients, stable networks, quick roaming")

    def _print_fast_timers_disabled(
        self, quiet_period: float, transmit_period: float, supplicant_timeout: int, max_requests: int
    ) -> None:
        """Print the DISABLED variant of the fast-802.1X-timer info block (shows current defaults + hypothetical)."""
        print("Standard 802.1X Timers (DISABLED):")  # Section header for the disabled case
        print("  - Current mode: Uses standard 802.1X defaults")
        print("  - quiet-period: ~60 seconds (standard default)")
        print("  - transmit-period: ~30 seconds (standard default)\n")
        print("  If fast_dot1x_timers were enabled, would calculate:")
        print(f"    - quiet-period: {quiet_period:.1f} seconds (auth_servers_timeout / 2)")
        print(f"    - transmit-period: {transmit_period:.1f} seconds (auth_servers_timeout / 2)")
        print(f"    - retries: {self.new_retries} (from auth_servers_retries)")
        print(f"    - supplicant-timeout: {supplicant_timeout} seconds (fixed default)")
        print(f"    - max-requests: {max_requests} (fixed default)\n")
        print("  Impact: Slower but more conservative authentication")
        print("  Best for: Legacy clients, unstable networks, maximum compatibility")

    def _print_fast_timer_info(self) -> None:  # Print fast 802
        """Print fast 802.1X timer information."""
        quiet_period = self.new_timeout / 2  # Derived quiet-period when fast timers are enabled
        transmit_period = self.new_timeout / 2  # Derived transmit-period when fast timers are enabled
        supplicant_timeout = 10  # Fixed default supplicant timeout in seconds
        max_requests = 3  # Fixed default maximum EAP requests
        if self.new_fast:  # Fast 802.1X timers are being enabled
            self._print_fast_timers_enabled(quiet_period, transmit_period, supplicant_timeout, max_requests)
        else:  # Fast timers remain disabled (standard 802.1X defaults)
            self._print_fast_timers_disabled(quiet_period, transmit_period, supplicant_timeout, max_requests)
        print("")  # Blank spacer line

    def _print_client_experience(
        self, server_count: int, single_max: int, all_max: int
    ) -> None:  # Print expected client experience information
        """Print expected client experience information."""
        print("Expected Client Experience:")  # Section header
        print("  - Success case: 1-3 seconds (single request/response)")  # Typical happy-path timing
        print(f"  - First server timeout: ~{single_max} seconds")  # Delay if the first server is unresponsive
        if server_count > 1:  # Only relevant when multiple servers exist
            print(f"  - All servers fail: ~{all_max} seconds")  # Worst-case delay across all servers
        print("")  # Blank spacer line

    def _display_proposed_changes(self) -> None:  # Display proposed configuration changes with warnings
        """Display proposed configuration changes with warnings."""
        wlan = self._get_selected_wlan()  # Fetch the WLAN being edited
        print(f"{'=' * 100}")  # Top border of the changes banner
        print("Proposed Configuration Changes:")  # Banner title
        print(f"{'=' * 100}")  # Bottom border of the changes banner
        print(
            f"  auth_servers_timeout: {wlan.get('auth_servers_timeout', 5)} -> {self.new_timeout}"
        )  # Old -> new timeout
        print(
            f"  auth_servers_retries: {wlan.get('auth_servers_retries', 2)} -> {self.new_retries}"
        )  # Old -> new retries
        print(
            f"  auth_server_selection: {wlan.get('auth_server_selection', 'ordered')} -> {self.new_selection}"
        )  # Old -> new mode
        print(
            f"  fast_dot1x_timers: {wlan.get('fast_dot1x_timers', False)} -> {self.new_fast}"
        )  # Old -> new fast-timer flag
        print("")  # Blank spacer line
        self._print_inheritance_warning()  # Warn if the change affects shared templates

    def _print_inheritance_warning(self) -> None:  # Print warning about template inheritance if applicable
        """Print warning about template inheritance if applicable."""
        wlan = self._get_selected_wlan()  # Fetch the WLAN being edited
        inheritance = wlan.get("_inheritance_level")  # Where this WLAN is defined in the hierarchy
        if inheritance == "site_template":  # The WLAN comes from a shared site template
            print(
                f"[!] WARNING: This WLAN is inherited from site template: {wlan.get('_inheritance_source')}"
            )  # Name the template
            print("[!] Changes will affect ALL sites using this template!")  # Emphasize the blast radius
        elif inheritance == "org_wlan_with_template":  # The WLAN comes from an org-level WLAN template
            print(
                f"[!] WARNING: This WLAN is from an org-level WLAN template: {wlan.get('_inheritance_source')}"
            )  # Name the source
            assignment = wlan.get(
                "_org_template_assignment", "assigned sites"
            )  # Which sites the template is applied to
            template_name_wlan = wlan.get("_wlan_template_name", "Unknown")  # The template's display name
            print(  # Warn that every site using this template is affected
                f"[!] Changes will affect ALL sites where WLAN template '{template_name_wlan}' is applied: {assignment}"
            )
        print("")  # Blank spacer line

    def _confirm_changes(self) -> bool:  # Prompt user for confirmation to apply changes
        """Prompt user for confirmation to apply changes."""
        confirmation = _MH.InputUtils.safe_input(
            "Type 'APPLY' to apply these changes: ", context="confirmation"
        ).strip()  # Require an explicit typed keyword
        if confirmation != "APPLY":  # The user did not type the exact confirmation word
            print("\n[*] Changes cancelled. No modifications made.")  # Inform the user nothing changed
            logging.info("User cancelled WLAN authentication timer changes")  # Log the cancellation
            return False  # Signal the caller to abort
        return True  # Confirmation received -- proceed with the update

    def _build_update_payload(self) -> dict[str, Any]:  # Build the update payload for the API call
        """Build the update payload for the API call."""
        return {  # Assemble only the four timer fields the API should change
            "auth_servers_timeout": self.new_timeout,  # New per-attempt timeout
            "auth_servers_retries": self.new_retries,  # New retry count
            "auth_server_selection": self.new_selection,  # New server-selection mode
            "fast_dot1x_timers": self.new_fast,  # New fast-timer flag
        }

    def _apply_changes(self) -> None:  # Apply changes to appropriate endpoint based on inheritance
        """Apply changes to appropriate endpoint based on inheritance."""
        wlan = self._get_selected_wlan()  # Fetch the WLAN being edited
        inheritance = wlan.get("_inheritance_level")  # Decide which API endpoint owns this WLAN
        try:
            if inheritance == "site":  # WLAN lives directly on the site
                self._update_site_wlan()  # Update via the site WLAN endpoint
            elif inheritance == "site_template":  # WLAN lives in a site template
                self._update_site_template_wlan()  # Update via the site-template endpoint
            elif inheritance == "org_wlan_with_template":  # WLAN is an org WLAN tied to a template
                self._update_org_wlan()  # Update via the org WLAN endpoint
            else:  # The inheritance level is unrecognized
                print(f"[!] Unknown inheritance level: {inheritance}")  # Report the unexpected value
                logging.error("Unknown inheritance level for WLAN")  # Log the error for diagnosis
        except Exception as error:  # Any API failure during the write
            print(f"\n[!] Error applying changes: {error}")  # Inform the user of the failure
            logging.exception("Error applying WLAN authentication timer changes: %s", error)  # Log with traceback

    def _update_site_wlan(self) -> None:  # Update a site-level WLAN
        """Update a site-level WLAN."""
        wlan = self._get_selected_wlan()  # Fetch the WLAN being edited
        print("\n[*] Updating site-level WLAN...")  # Inform the user the write is starting
        payload = self._build_update_payload()  # Build the timer-only update body
        logging.info("Updating site WLAN %s with payload: %s", wlan.get("id"), payload)  # Log before the API call
        response = mistapi.api.v1.sites.wlans.updateSiteWlan(
            _MH.apisession, self.site_id, wlan.get("id"), payload
        )  # Push the update
        if response.status_code == 200:  # The update succeeded
            print(f"[+] Successfully updated WLAN: {wlan.get('ssid')}")  # Confirm success to the user
            logging.info("Successfully updated site WLAN %s", wlan.get("id"))  # Log the success
        else:  # The update failed
            print(f"[!] Failed to update WLAN: HTTP {response.status_code}")  # Report the HTTP error
            logging.error(
                "Failed to update site WLAN: HTTP %s, Response: %s", response.status_code, response.data
            )  # Log the detail

    def _fetch_site_template_for_update(
        self, template_id: str
    ) -> dict[str, Any] | None:  # Fetch a site template document and validate its shape
        """Fetch a site template document and validate its shape. Returns None on failure."""
        template_response = mistapi.api.v1.orgs.sitetemplates.getOrgSiteTemplate(
            _MH.apisession, self.org_id, template_id
        )  # Fetch current template
        if template_response.status_code != 200:  # Could not load the template to modify
            print(f"[!] Failed to fetch site template: HTTP {template_response.status_code}")
            logging.error("Failed to fetch site template for update: HTTP %s", template_response.status_code)
            return None  # Abort -- cannot safely update without the current state
        template_data = template_response.data  # The full template document to mutate
        if "wlans" not in template_data or not isinstance(template_data["wlans"], dict):
            print("[!] Site template does not contain wlans data structure")
            logging.error("Site template missing wlans dictionary")
            return None  # Abort -- nothing to update
        return cast("dict[str, Any]", template_data)  # Caller may now mutate the WLAN map in place

    def _apply_wlan_update_to_template(
        self, template_data: dict[str, Any], wlan_id: str
    ) -> bool:  # Find target WLAN in template_data['wlans'] and apply update payload in place
        """Find target WLAN in template_data['wlans'] and apply update payload in place. Return True if found."""
        for _wlan_key, wlan_data in template_data["wlans"].items():  # Scan every WLAN in the template
            if wlan_data.get("id") == wlan_id:  # Found the WLAN we intend to change
                wlan_data.update(self._build_update_payload())  # Apply the new timer values in place
                return True  # Stop scanning once updated
        return False  # The WLAN was not present in the template

    def _write_site_template_update(
        self, template_id: str, template_data: dict[str, Any], wlan: dict[str, Any]
    ) -> None:
        """Push the mutated template back to Mist and report success or failure."""
        wlan_id = wlan.get("id")  # Reused for logging
        update_response = mistapi.api.v1.orgs.sitetemplates.updateOrgSiteTemplate(
            _MH.apisession, self.org_id, template_id, template_data  # Send the full mutated document
        )
        if update_response.status_code == 200:  # The template write succeeded
            print(f"[+] Successfully updated site template WLAN: {wlan.get('ssid')}")
            print("[+] All sites using this template will inherit these changes")
            logging.info("Successfully updated site template WLAN %s in template %s", wlan_id, template_id)
        else:  # The template write failed
            print(f"[!] Failed to update site template: HTTP {update_response.status_code}")
            logging.error(
                "Failed to update site template: HTTP %s, Response: %s",
                update_response.status_code,
                update_response.data,
            )

    def _update_site_template_wlan(self) -> None:  # Update a site template-level WLAN
        """Update a site template-level WLAN."""
        wlan = self._get_selected_wlan()  # Fetch the WLAN being edited
        print("\n[*] Updating site template-level WLAN...")
        template_id = wlan.get("_template_id")  # The template that owns this WLAN
        wlan_id = wlan.get("id")  # The WLAN's unique ID within the template
        if not template_id or not wlan_id:  # Both are required for a template-level update
            logging.error("Missing template_id or wlan_id for site template WLAN update")
            return
        logging.info("Updating site template WLAN %s in template %s", wlan_id, template_id)
        template_data = self._fetch_site_template_for_update(template_id)  # Load + validate
        if template_data is None:  # Fetch or shape-check failed (already reported by helper)
            return
        if not self._apply_wlan_update_to_template(template_data, wlan_id):  # WLAN missing in template
            print("[!] WLAN not found in site template")
            logging.error("WLAN %s not found in site template %s", wlan_id, template_id)
            return
        self._write_site_template_update(template_id, template_data, wlan)  # Write back + report

    def _update_org_wlan(self) -> None:  # Update an org-level WLAN
        """Update an org-level WLAN."""
        wlan = self._get_selected_wlan()  # Fetch the WLAN being edited
        print("\n[*] Updating org-level WLAN...")  # Inform the user the write is starting
        wlan_id = wlan.get("id")  # The org WLAN's unique ID
        if not wlan_id:  # Defensive: the WLAN record lacks an ID
            print("[!] Missing WLAN ID - cannot update")  # Report the missing identifier
            logging.error("Missing WLAN id for org WLAN update")  # Log the failure
            # Abort -- cannot target the update
            return
        payload = self._build_update_payload()  # Build the timer-only update body
        logging.info("Updating org WLAN %s with payload: %s", wlan_id, payload)  # Log before the API call
        # Push the update
        response = mistapi.api.v1.orgs.wlans.updateOrgWlan(_MH.apisession, self.org_id, wlan_id, payload)
        self._report_org_wlan_update_result(response, wlan, wlan_id)  # Print + log success/failure

    def _report_org_wlan_update_result(
        self, response: Any, wlan: dict[str, Any], wlan_id: str
    ) -> None:  # Print user-visible message and structured log for an org WLAN update HTTP response
        """Print user-visible message and structured log for an org WLAN update HTTP response."""
        if response.status_code == 200:  # The update succeeded
            print(f"[+] Successfully updated org WLAN: {wlan.get('ssid')}")  # Confirm success to the user
            template_name = wlan.get("_wlan_template_name", "Unknown")  # The base template name for context
            print(
                f"[+] WLAN uses template '{template_name}' for its base configuration"
            )  # Clarify the template relationship
            logging.info("Successfully updated org WLAN %s", wlan_id)  # Log the success
        else:  # The update failed
            print(f"[!] Failed to update org WLAN: HTTP {response.status_code}")  # Report the HTTP error
            logging.error(
                "Failed to update org WLAN: HTTP %s, Response: %s", response.status_code, response.data
            )  # Log the detail

    def _print_completion_message(self) -> None:  # Print completion message
        """Print completion message."""
        print(
            "\n[+] WLAN authentication timer management completed successfully"
        )  # Tell the user the workflow finished
        logging.info("WLAN authentication timer management completed")  # Log the completion
