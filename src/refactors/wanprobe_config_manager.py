"""WANProbeConfigManager extracted from MistHelper.

WAN interface ICMP probe configuration for gateway templates (Menu 166).
Owns the top-level orchestration originally defined as class
WANProbeConfigManager in MistHelper.py.

Runtime dependencies (apisession module-global, and the utility
classes ConfigUtils / InputUtils / CacheUtils / GatewayExportUtils /
OrgSiteExporter / FilePathUtils / DataExporter) are still owned by
MistHelper.py. They are resolved lazily via the module-level _MH proxy
so the extracted module keeps its import graph flat, live re-bindings
of apisession (e.g. after interactive login) are always honoured, and
monkeypatched attributes in tests continue to work.

The ``MIST_SITE_EXCLUDE_PREFIX`` constant is imported directly from
``src.refactors.mist_site_exclude_prefix`` (initiative 1015 T-15) --
it is a static string captured at env-init time, so no live rebind
is needed.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import concurrent.futures  # Provides as_completed for the ThreadPoolExecutor result loop
import csv  # Reads the generated OrgGatewayTemplates.csv and SiteList.csv files
import importlib  # Late-import MistHelper module to avoid circular src<->MistHelper dependency
import logging  # Structured action logging required by coding standards
import os  # Environment variable lookup for MIST_WAN_PROBE_IPS / MIST_WAN_PROBE_PROFILE
import traceback  # Format traceback strings for exception logging
from concurrent.futures import ThreadPoolExecutor  # Parallel per-template fetch worker pool
from typing import Any  # Loose typing for late-bound MistHelper attributes and JSON payloads

import mistapi  # Direct dependency: Mist API SDK used to fetch/update gateway templates
from tqdm import tqdm  # Progress bar used during parallel analyze and update loops


class _MistHelperProxy:  # Attribute forwarder to MistHelper module attributes
    """Forward attribute access to the currently-loaded MistHelper module."""

    def __getattr__(self, name: str) -> Any:  # Called only when the attribute is not found normally
        """Resolve name against the live MistHelper module (call-time lookup)."""
        misthelper_module = importlib.import_module("MistHelper")  # Lazy import at call time
        return getattr(misthelper_module, name)  # Fetch the current bound value from MistHelper


_MH = _MistHelperProxy()  # Sole module-level proxy handle used inside the class body


class WANProbeConfigManager:  # WAN probe config manager (Menu 166 destructive entrypoint)
    """Manages WAN interface ICMP probe configuration for gateway templates.

    Menu #166: Configure WAN probe override settings (probe IPs and profile)
    for all WAN interfaces across selected gateway templates.

    Default Configuration:
        - probe IPs: ["192.151.29.254", "18.154.184.32"]
        - probe_profile: "lte"

    This operation updates the wan_probe_override section for all interfaces
    where usage == "wan" in the template's port_config.
    """

    # Default probe configuration - loaded from environment variables
    # MIST_WAN_PROBE_IPS: Comma-separated list of probe IPs (e.g., "192.151.29.254,18.154.184.32")
    # MIST_WAN_PROBE_PROFILE: Probe profile name (e.g., "lte")
    DEFAULT_PROBE_IPS = [  # Default probe IPs.
        ip.strip() for ip in os.getenv("MIST_WAN_PROBE_IPS", "192.151.29.254,18.154.184.32").split(",") if ip.strip()
    ]
    DEFAULT_PROBE_PROFILE = os.getenv("MIST_WAN_PROBE_PROFILE", "lte")  # Default probe profile.

    def __init__(self) -> None:  # Init the manager state.
        """Initialize the WAN Probe Configuration Manager."""
        self.org_id: str | None = None  # Resolved org id.
        self.templates: list[dict[str, Any]] = []  # Loaded templates.
        self.sites: list[dict[str, Any]] = []  # Loaded sites.
        self.template_site_counts: dict[str, int] = {}  # Sites per template.
        self.probe_ips: list[str] = self.DEFAULT_PROBE_IPS.copy()  # Working probe IPs.
        self.probe_profile: str = self.DEFAULT_PROBE_PROFILE  # Working probe profile.

    @classmethod
    def configure(cls, dry_run: bool = False) -> None:  # Configure entry point.
        """Menu #166: Configure WAN Probe Override on Gateway Templates (DESTRUCTIVE).

        Updates wan_probe_override settings for all WAN interfaces in selected
        gateway templates. Replaces existing probe IPs with configured values.

        Args:
            dry_run: If True, show what would change without making modifications
        """
        manager = cls()  # Build the manager.
        manager._execute(dry_run)  # Run the flow.

    def _announce_no_wan_interfaces(self) -> None:
        """Print and log the 'no WAN interfaces found' message for the menu #166 dry-run path."""
        print("\n  No WAN interfaces found in selected templates.")  # Tell the user.
        print("  No changes needed.")  # Tell the user.
        logging.info("Menu #166: No WAN interfaces found in selected templates")  # Log it.

    def _prepare_templates_with_changes(self) -> list[dict[str, Any]] | None:
        """Run all init/load/select/analyze guard steps; return analyzed list or None to signal abort."""
        if not self._initialize():  # Org id resolution
            return None
        if not self._load_data():  # Sites + templates load
            return None
        templates_to_modify = self._select_templates()  # Operator picks targets
        if not templates_to_modify:  # User cancelled / empty
            return None
        templates_with_changes = self._analyze_templates(templates_to_modify)  # Diff per template
        if not templates_with_changes:  # Nothing to change
            self._announce_no_wan_interfaces()  # Operator notice + log
            return None
        return templates_with_changes

    def _execute(self, dry_run: bool) -> None:  # Run the probe config flow.
        """Main execution flow for WAN probe configuration."""
        self._display_header(dry_run)  # Show the banner
        templates_with_changes = self._prepare_templates_with_changes()  # Init -> load -> select -> analyze
        if templates_with_changes is None:  # Any prep step aborted
            return
        self._show_preview(templates_with_changes, dry_run)  # Operator preview
        if not dry_run and not self._confirm_operation(len(templates_with_changes)):  # Confirm before destructive
            return
        results = self._apply_changes(templates_with_changes, dry_run)  # Execute writes
        self._generate_report(results, dry_run)  # Final summary

    def _display_header(self, dry_run: bool) -> None:  # Show the header.
        """Display operation header with configuration details."""
        print("\n  DESTRUCTIVE: Configure WAN Interface ICMP Probe Settings")  # Header.
        print("=" * 70)  # Divider.
        if dry_run:  # Dry-run.
            print("  >> DRY-RUN MODE: No changes will be made to templates")  # Tell the user.
            print("  >> This will show what WOULD be changed without modifying anything")  # Tell the user.
        else:
            print("  !? WARNING: This operation modifies gateway templates")  # Warn destructive.
            print("  !? All sites using affected templates will inherit the change")  # Warn inheritance.
        print("=" * 70)  # Divider.
        print("\n  Probe Configuration:")  # Probe config header.
        print(f"    Probe IPs: {self.probe_ips}")  # Show probe IPs.
        print(f"    Probe Profile: {self.probe_profile}")  # Show probe profile.
        print("=" * 70)  # Divider.
        logging.warning("Menu #166 DESTRUCTIVE: Configure WAN Probe Override operation started")  # Log the start.

    def _initialize(self) -> bool:  # Initialize state.
        """Initialize org_id and return True on success."""
        self.org_id = _MH.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        if not self.org_id:  # No org.
            print(" Failed to get organization ID.")  # Tell the user.
            logging.error("Menu #166: Could not obtain org_id")  # Log the error.
            return False  # Abort.
        return True  # Initialized.

    def _build_template_site_counts(self) -> None:
        """Tally how many sites reference each gateway template (skipping MIST_SITE_EXCLUDE_PREFIX names)."""
        from src.refactors.mist_site_exclude_prefix import (  # noqa: PLC0415 - local import.
            MIST_SITE_EXCLUDE_PREFIX,
        )

        exclude_prefix = MIST_SITE_EXCLUDE_PREFIX  # Read exclude prefix once for the loop (canonical import).
        for site in self.sites:  # Walk sites.
            if exclude_prefix and site.get("name", "").startswith(exclude_prefix):
                continue  # Skip it.
            template_id = site.get("gatewaytemplate_id", "").strip()  # Read template id.
            if template_id:  # Have a template.
                self.template_site_counts[template_id] = self.template_site_counts.get(template_id, 0) + 1

    def _load_data(self) -> bool:  # Load the data.
        """Load gateway templates and site data and return True on success."""
        print("\n  Loading gateway template data...")  # Tell the user.
        _MH.CacheUtils.check_and_generate_csv("OrgGatewayTemplates.csv", _MH.GatewayExportUtils.templates)
        _MH.CacheUtils.check_and_generate_csv("SiteList.csv", _MH.OrgSiteExporter.sites)  # Refresh sites CSV.
        templates_path = _MH.FilePathUtils.get_csv_path("OrgGatewayTemplates.csv")  # Templates path.
        with open(templates_path, encoding="utf-8") as file_handle:  # Open the CSV.
            self.templates = list(csv.DictReader(file_handle))  # Read the templates.
        if not self.templates:  # No templates.
            print(" No gateway templates found.")  # Tell the user.
            logging.warning("Menu #166: No gateway templates available")  # Warn none.
            return False  # Abort.
        sites_path = _MH.FilePathUtils.get_csv_path("SiteList.csv")  # Sites path.
        with open(sites_path, encoding="utf-8") as file_handle:  # Open the CSV.
            self.sites = list(csv.DictReader(file_handle))  # Read the sites.
        self._build_template_site_counts()  # Tally per-template site counts.
        logging.info("Loaded %s gateway templates and %s sites", len(self.templates), len(self.sites))
        return True  # Loaded.

    def _render_template_list(self, templates_sorted: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Print the menu of available gateway templates and return the matching display rows."""
        print(f"\n  Available Gateway Templates ({len(templates_sorted)}):")  # Tell the user.
        template_list: list[dict[str, Any]] = []  # Display rows.
        for idx, template in enumerate(templates_sorted, start=1):  # Enumerate templates.
            template_id = template.get("id", "")  # Template id.
            template_name = template.get("name", "Unnamed Template")  # Template name.
            site_count = self.template_site_counts.get(template_id, 0)  # Site count.
            template_list.append({"id": template_id, "name": template_name, "site_count": site_count})
            print(f"   [{idx}] {template_name} ({site_count} sites)")  # Print the option.
        return template_list  # Return rows for selection.

    @staticmethod
    def _resolve_template_indices(selection: str, template_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Parse a comma-separated 1-based index string into the matching template rows (raises on bad input)."""
        indices = [int(idx.strip()) - 1 for idx in selection.split(",")]  # 1-based input -> 0-based indices
        return [template_list[idx] for idx in indices if 0 <= idx < len(template_list)]  # Drop out-of-range

    def _parse_template_selection(self, selection: str, template_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Parse a user template-selection string into the matching template rows (empty list on failure)."""
        if selection == "cancel":  # User cancelled
            print(" Operation cancelled.")
            logging.info("Menu #166 cancelled by user at template selection")
            return []
        if selection == "all":  # Select all templates as-is
            return template_list
        try:
            selected = type(self)._resolve_template_indices(selection, template_list)  # Parse + filter indices
        except (ValueError, IndexError) as error:  # Bad numeric input
            print(f" Invalid selection: {error}")
            logging.error("Menu #166: Invalid template selection: %s", error)
            return []
        if not selected:  # All indices were out-of-range
            print(" No valid templates selected.")
            return []
        return selected

    def _select_templates(self) -> list[dict[str, Any]]:  # Select templates.
        """Display templates and get user selection; returns selected templates."""
        templates_sorted = sorted(self.templates, key=lambda t: t.get("name", "").lower())  # Sort by name.
        template_list = self._render_template_list(templates_sorted)  # Show menu + collect rows.
        print("\n  Template Selection:")  # Selection header.
        print("   Enter template numbers (comma-separated, e.g., 1,3,5)")  # Tell the user.
        print("   Or 'all' to modify all templates")  # Tell the user.
        print("   Or 'cancel' to abort")  # Tell the user.
        selection = (
            _MH.InputUtils.safe_input("\n  Selection: ", context="wan_probe_template_selection").strip().lower()
        )  # Read + normalise
        return self._parse_template_selection(selection, template_list)  # Parse + resolve.

    def _analyze_templates(self, templates_to_modify: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Fetch and analyze templates for WAN interfaces and return templates with changes."""
        print(f"\n  Analyzing {len(templates_to_modify)} templates for WAN interfaces...")  # Tell the user
        logging.info("Analyzing %s templates for WAN interfaces", len(templates_to_modify))  # Trace count
        result = self._run_template_analysis_pool(templates_to_modify)  # Run parallel analysis
        logging.debug("Template analysis produced %s templates with changes", len(result))  # Trace result count
        return result  # Return templates with WAN interfaces

    def _run_template_analysis_pool(self, templates_to_modify: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Run per-template analysis in a thread pool and collect the non-empty results."""
        max_workers = min(10, len(templates_to_modify))  # Size the worker pool
        logging.info(
            "Fetching %s templates in parallel (max %s workers)", len(templates_to_modify), max_workers
        )  # Trace pool sizing
        templates_with_changes: list[dict[str, Any]] = []  # Collect changed templates
        with ThreadPoolExecutor(max_workers=max_workers) as executor:  # Run the pool
            future_map = {executor.submit(self._analyze_template, t): t for t in templates_to_modify}
            for future in tqdm(
                concurrent.futures.as_completed(future_map),
                total=len(templates_to_modify),
                desc="Analyzing templates",
                unit="template",
            ):
                analyzed = future.result()  # Read the result
                if analyzed:  # Skip None results (template had no WAN interfaces or failed)
                    templates_with_changes.append(analyzed)  # Collect it
        return templates_with_changes  # Return collected templates

    def _analyze_template(self, template_info: dict[str, Any]) -> dict[str, Any] | None:
        """Analyze a single template: fetch config and extract WAN interfaces."""
        logging.debug("Analyzing template %s", template_info.get("name"))  # Trace per-template start
        config = self._fetch_template_config(template_info)  # Fetch the template config
        if config is None:  # Fetch failed or returned invalid structure
            return None  # Skip this template
        wan_interfaces = self._extract_wan_interfaces(config.get("port_config"))  # Walk port_config for WAN ports
        if not wan_interfaces:  # Template has no WAN-usage ports
            logging.debug("Template %s has no WAN interfaces", template_info.get("name"))  # Trace empty result
            return None  # Skip this template
        logging.debug(
            "Template %s has %s WAN interfaces", template_info.get("name"), len(wan_interfaces)
        )  # Trace per-template result
        return {  # Return the change record
            "id": template_info["id"],
            "name": template_info["name"],
            "site_count": template_info["site_count"],
            "config": config,
            "wan_interfaces": wan_interfaces,
        }

    def _fetch_template_config(self, template_info: dict[str, Any]) -> dict[str, Any] | None:
        """Fetch a single gateway template's config dict, or None on error or invalid structure."""
        template_id = template_info["id"]  # Template id
        template_name = template_info["name"]  # Template name
        try:
            logging.debug("Fetching template configuration for %s", template_name)  # Trace the fetch
            response = mistapi.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate(  # Fetch the template
                _MH.apisession, self.org_id, template_id
            )
            config = response.data if hasattr(response, "data") else {}  # Unwrap the config
            if not isinstance(config, dict):  # Invalid structure
                logging.warning("Template %s returned invalid structure", template_name)  # Warn it
                return None  # Skip it
            return config  # Return the valid config dict
        except Exception as error:  # Analysis failed
            logging.error("Error analyzing template %s: %s", template_name, error)  # Log the error
            logging.error(traceback.format_exc())  # Log the traceback
            print(f"\n  !? Error analyzing template '{template_name}': {error}")  # Tell the user
            return None  # Skip it

    def _extract_wan_interfaces(self, port_config: Any) -> list[dict[str, Any]]:
        """Extract WAN-usage interfaces from a template's port_config, returning empty list when invalid."""
        if not isinstance(port_config, dict):  # Invalid or missing port_config
            logging.debug("Skipping template: port_config is not a dict")  # Trace skip
            return []  # No WAN ports
        wan_interfaces: list[dict[str, Any]] = []  # Collect WAN ports
        for port_name, port_settings in port_config.items():  # Walk every port entry
            if isinstance(port_settings, dict) and port_settings.get("usage") == "wan":  # WAN-usage port
                wan_interfaces.append(self._build_wan_interface(port_name, port_settings))  # Collect it
        return wan_interfaces  # Return collected WAN ports

    def _build_wan_interface(self, port_name: str, port_settings: dict[str, Any]) -> dict[str, Any]:
        """Build the WAN interface change-record dict for one WAN-usage port."""
        current_probe = port_settings.get("wan_probe_override", {})  # Read probe override
        current_ips = current_probe.get("ips", []) if isinstance(current_probe, dict) else []  # Probe IPs
        current_profile = (
            current_probe.get("probe_profile", "") if isinstance(current_probe, dict) else ""
        )  # Probe profile
        return {
            "port_name": port_name,
            "current_ips": current_ips,
            "current_profile": current_profile,
        }  # Return the interface record

    def _print_wan_interface_change(self, wan_if: dict[str, Any]) -> None:
        """Print a single WAN interface's before/after probe override block."""
        port = wan_if["port_name"]  # Port the override targets
        current_ips = wan_if["current_ips"] or ["(none)"]  # Substitute literal for empty list display
        current_profile = wan_if["current_profile"] or "(none)"  # Substitute literal for missing profile
        print(f"     {port}:")  # Header line for this port
        print(f"       Current: ips={current_ips}, profile={current_profile}")  # Pre-change state
        print(f"       New:     ips={self.probe_ips}, profile={self.probe_profile}")  # Post-change state

    def _show_preview(self, templates_with_changes: list[dict[str, Any]], dry_run: bool) -> None:
        """Display preview of changes to be made."""
        del dry_run  # Kept in signature for API-compat with sibling _apply_changes; not used in preview.
        total_interfaces = sum(len(t["wan_interfaces"]) for t in templates_with_changes)  # Sum across all
        total_sites = sum(t["site_count"] for t in templates_with_changes)  # Sum site reach
        print("\n  Preview of Changes:")  # Section header
        print(f"  {len(templates_with_changes)} templates with {total_interfaces} WAN interfaces")  # Scale line
        print(f"  Affecting {total_sites} sites")  # Blast-radius line
        for template in templates_with_changes:  # Iterate each impacted template
            print(f"\n   Template: {template['name']} ({template['site_count']} sites)")  # Template subheader
            for wan_if in template["wan_interfaces"]:  # Iterate each affected WAN port
                self._print_wan_interface_change(wan_if)  # Delegate per-port formatting

    def _confirm_operation(self, template_count: int) -> bool:  # Confirm the operation.
        """Prompt for confirmation and return True if confirmed."""
        print(f"\n  {'=' * 70}")  # Divider.
        print(f"  !? CRITICAL: This will modify {template_count} gateway templates")  # Warn destructive.
        print("  !? Type 'APPLY' (all caps) to proceed or anything else to cancel")  # Ask to type APPLY.
        print(f"  {'=' * 70}")  # Divider.

        confirmation = _MH.InputUtils.safe_input(  # Read the confirmation.
            "\n  Confirmation: ",
            context="wan_probe_apply_confirmation",
        ).strip()
        if confirmation != "APPLY":  # Not confirmed.
            print(" Operation cancelled.")  # Tell the user.
            logging.info("Menu #166 cancelled by user at final confirmation")  # Log the cancel.
            return False  # Abort.
        return True  # Confirmed.

    def _apply_changes(self, templates_with_changes: list[dict[str, Any]], dry_run: bool) -> list[dict[str, Any]]:
        """Apply probe configuration changes to templates and return per-template results."""
        print("\n  Applying WAN probe configuration...")  # Tell the user.
        results: list[dict[str, Any]] = []  # Collect results.

        for template in tqdm(templates_with_changes, desc="Updating templates", unit="template"):
            result = self._update_single_template(template, dry_run)  # Update one template.
            results.append(result)  # Collect the result.

        return results  # Return all results.

    def _update_single_template(self, template: dict[str, Any], dry_run: bool) -> dict[str, Any]:
        """Update a single template's WAN probe configuration."""
        template_name = template["name"]  # Template name (used across logging and the result).
        result = self._blank_template_result(template)  # Pre-populated result skeleton for this template
        try:
            config = template["config"]  # Template config to mutate and persist.
            port_config = config.get("port_config", {})  # Read port config.
            interfaces_modified = self._apply_wan_probe_overrides(template, port_config)  # Set probe overrides
            if interfaces_modified:  # Any modifications.
                config["port_config"] = port_config  # Store port config.
                result["interfaces_updated"] = interfaces_modified  # Record updates.
                status, error = self._persist_template_update(template, config, dry_run, interfaces_modified)  # Commit
                result["status"] = status  # Record the outcome status.
                result["error"] = error  # Record any error detail.
            else:
                result["status"] = "SKIPPED"  # Mark skipped.
                result["error"] = "No WAN interfaces found in port_config"  # Record the reason.
        except Exception as error:  # Update failed.
            result["status"] = "ERROR"  # Mark error.
            result["error"] = str(error)  # Record the error.
            logging.error("Error updating template %s: %s", template_name, error)  # Log the error.
            logging.error(traceback.format_exc())  # Log the traceback.
        return result  # Return the result.

    @staticmethod
    def _blank_template_result(template: dict[str, Any]) -> dict[str, Any]:  # Pre-fill the per-template result
        """Build the per-template result skeleton (identity fields set; status/error/updates start empty)."""
        return {
            "template_name": template["name"],  # Template name for the report.
            "template_id": template["id"],  # Template id for the report.
            "site_count": template["site_count"],  # How many sites use this template.
            "interfaces_updated": [],  # Filled with modified port names when an update happens.
            "status": "",  # Outcome status (DRY-RUN/SUCCESS/FAILED/SKIPPED/ERROR).
            "error": "",  # Error detail when the outcome is not success.
        }

    def _apply_wan_probe_overrides(self, template: dict[str, Any], port_config: dict[str, Any]) -> list[str]:
        """Set wan_probe_override on each WAN interface present in port_config; return the modified port names."""
        interfaces_modified: list[str] = []  # Track modified ports.
        template_name = template["name"]  # Template name for trace logging.
        for wan_if in template["wan_interfaces"]:  # Walk WAN ports.
            port_name = wan_if["port_name"]  # Port name.
            if port_name in port_config:  # Port present.
                port_config[port_name]["wan_probe_override"] = {  # Set the probe override.
                    "ips": self.probe_ips.copy(),
                    "probe_profile": self.probe_profile,
                }
                interfaces_modified.append(port_name)  # Mark it modified.
                logging.debug("Template %s: Updated %s probe config", template_name, port_name)  # Trace the update.
        return interfaces_modified  # Ports that received a probe override

    def _persist_template_update(
        self,
        template: dict[str, Any],
        config: dict[str, Any],
        dry_run: bool,
        interfaces_modified: list[str],
    ) -> tuple[str, str]:
        """Commit the template config (dry-run logs only, else calls the API); return (status, error)."""
        template_name = template["name"]  # Template name for logging.
        if dry_run:  # Dry-run.
            logging.info("DRY-RUN: Would update template %s interfaces: %s", template_name, interfaces_modified)
            return "DRY-RUN", ""  # No API call performed.
        logging.debug("Updating template %s via API", template_name)  # Trace the update.
        update_resp = mistapi.api.v1.orgs.gatewaytemplates.updateOrgGatewayTemplate(  # Update the template.
            _MH.apisession, self.org_id, template["id"], body=config
        )
        if update_resp.status_code == 200:  # Success.
            logging.info("Successfully updated template %s", template_name)  # Log success.
            return "SUCCESS", ""  # Updated successfully.
        logging.error("Failed to update template %s: status %s", template_name, update_resp.status_code)  # Log fail
        return "FAILED", f"API returned status {update_resp.status_code}"  # Report the API failure

    def _generate_report(self, results: list[dict[str, Any]], dry_run: bool) -> None:  # Generate the audit report
        """Generate and display final report."""
        logging.info("Generating audit report for %s results (dry_run=%s)", len(results), dry_run)  # Trace start
        report_data = [self._build_report_row(result) for result in results]  # Build per-result report rows
        output_file = "GatewayTemplate_WAN_Probe_Config_Audit.csv"  # Output filename
        _MH.DataExporter.write_with_format_selection(report_data, output_file)  # Write CSV/XLSX audit report
        total_interfaces, total_sites = self._compute_report_totals(results)  # Compute aggregate counts
        if dry_run:  # Dry-run summary
            self._emit_dry_run_summary(results, total_interfaces, total_sites)  # Print dry-run section
        else:  # Live-run summary
            self._emit_live_run_summary(results, total_interfaces, total_sites)  # Print live-run section
        print(f"\n  Report saved to: {output_file}")  # Tell the user
        print("=" * 70)  # Divider
        self._log_destructive_completion(results)  # Log the warning summary

    def _build_report_row(self, result: dict[str, Any]) -> dict[str, Any]:
        """Build one audit-report row from a per-template result dict."""
        interfaces_updated = result["interfaces_updated"]  # Read updated interface names
        return {
            "template_name": result["template_name"],
            "template_id": result["template_id"],
            "site_count": result["site_count"],
            "interfaces_updated": ", ".join(interfaces_updated) if interfaces_updated else "",  # Joined names
            "interface_count": len(interfaces_updated),
            "status": result["status"],
            "error": result["error"],
            "new_probe_ips": ", ".join(self.probe_ips),
            "new_probe_profile": self.probe_profile,
        }

    def _compute_report_totals(self, results: list[dict[str, Any]]) -> tuple[int, int]:
        """Compute total interfaces and total affected sites from per-template results."""
        total_interfaces = sum(len(r["interfaces_updated"]) for r in results)  # Total interfaces across all results
        total_sites = sum(
            r["site_count"] for r in results if r["status"] in ("SUCCESS", "DRY-RUN")
        )  # Sites affected by successful or dry-run results
        logging.debug("Report totals: interfaces=%s sites=%s", total_interfaces, total_sites)  # Trace totals
        return total_interfaces, total_sites  # Return aggregates

    def _emit_dry_run_summary(self, results: list[dict[str, Any]], total_interfaces: int, total_sites: int) -> None:
        """Print the dry-run summary block (no changes were applied)."""
        dry_run_count = sum(1 for r in results if r["status"] == "DRY-RUN")  # Count dry-run rows
        print("\n  WAN Probe Configuration DRY-RUN Complete!")  # Tell the user
        print("=" * 70)  # Divider
        print("  >> DRY-RUN MODE: No actual changes were made")  # Tell the user
        print(f"  Templates Analyzed: {len(results)}")  # Show analyzed count
        print(f"  Would Update: {dry_run_count} templates")  # Show would-update count
        print(f"  WAN Interfaces: {total_interfaces}")  # Show interfaces
        print(f"  Sites Affected: {total_sites}")  # Show sites
        print("\n  >> To apply changes, run without --dry-run flag")  # Tell the user

    def _emit_live_run_summary(self, results: list[dict[str, Any]], total_interfaces: int, total_sites: int) -> None:
        """Print the live-run summary block (changes were actually applied)."""
        success_count = sum(1 for r in results if r["status"] == "SUCCESS")  # Count successes
        failure_count = len(results) - success_count  # Count failures
        print("\n  WAN Probe Configuration Complete!")  # Tell the user
        print("=" * 70)  # Divider
        print(f"  Templates Updated: {success_count}")  # Show updated count
        print(f"  Templates Failed: {failure_count}")  # Show failed count
        print(f"  WAN Interfaces Configured: {total_interfaces}")  # Show interfaces
        print(f"  Sites Affected: {total_sites}")  # Show sites
        if success_count > 0:  # Any success
            print("\n  Configuration Applied:")  # Tell the user
            print(f"    Probe IPs: {self.probe_ips}")  # Show probe IPs
            print(f"    Probe Profile: {self.probe_profile}")  # Show probe profile
        if failure_count > 0:  # Any failure
            print(f"\n  !? {failure_count} templates failed - check audit report")  # Warn the failures

    def _log_destructive_completion(self, results: list[dict[str, Any]]) -> None:
        """Log a warning-level summary of the destructive operation completion."""
        success_count = sum(1 for r in results if r["status"] == "SUCCESS")  # Count successes
        logging.warning(  # Log the summary
            "Menu #166 DESTRUCTIVE operation complete: %s templates updated", success_count
        )
