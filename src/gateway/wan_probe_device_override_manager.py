"""WAN probe device override manager extracted from MistHelper menu 167 flow."""

from __future__ import annotations  # WHY: postpone hint evaluation for forward refs.

import csv  # WHY: parse cached template/site CSV exports.
import logging  # WHY: structured logging for entry/exit and errors.
import os  # WHY: read MIST_WAN_PROBE_* environment overrides.
import traceback  # WHY: capture full exception traces on device update failures.
from dataclasses import dataclass  # WHY: build the frozen dependency bundle.
from typing import Any  # WHY: opaque types for injected utility modules.

from tqdm import tqdm  # WHY: progress bar for per-site and per-device loops.

apisession: Any = None  # WHY: Mist API session slot populated at wiring time.
ConfigUtils: Any = None  # WHY: config helpers (org id + stop-signal check).
CacheUtils: Any = None  # WHY: CSV cache generator for exported data.
OrgSiteExporter: Any = None  # WHY: org-scoped site export utility.
GatewayExportUtils: Any = None  # WHY: gateway template export utility.
FilePathUtils: Any = None  # WHY: resolves CSV cache file locations.
InputUtils: Any = None  # WHY: safe_input wrapper for operator prompts.
DataExporter: Any = None  # WHY: writes report data with format selection.
mistapi: Any = None  # WHY: Mist REST client library reference.
MIST_SITE_EXCLUDE_PREFIX = ""  # WHY: prefix filter that removes lab/test sites.

_DEFAULT_PROBE_IPS_ENV = os.getenv("MIST_WAN_PROBE_IPS", "192.151.29.254,18.154.184.32")  # WHY: env-configurable IPs.
DEFAULT_PROBE_IPS = [ip.strip() for ip in _DEFAULT_PROBE_IPS_ENV.split(",") if ip.strip()]  # WHY: normalise IP list.
DEFAULT_PROBE_PROFILE = os.getenv("MIST_WAN_PROBE_PROFILE", "lte")  # WHY: env-configurable probe profile.
HEADER_RULE = "=" * 70  # WHY: reusable banner separator.
PREVIEW_DEVICE_LIMIT = 5  # WHY: cap sample devices printed in preview banner.
APPLY_CONFIRM_TOKEN = "APPLY"  # WHY: required uppercase confirmation phrase.
CANCEL_TOKEN = "cancel"  # WHY: template selection cancel keyword.
HTTP_OK = 200  # WHY: expected Mist update success status code.
AUDIT_OUTPUT_FILE = "GatewayDevice_WAN_Probe_Override_Audit.csv"  # WHY: stable audit filename.


@dataclass(frozen=True)
class WANProbeDeviceOverrideDependencies:  # WHY: frozen bundle avoids 10-arg configure signature.
    """Immutable dependency bundle wired into the WAN probe override module."""

    apisession: Any  # WHY: authenticated Mist API session handle.
    config_utils: Any  # WHY: ConfigUtils facade for org id/stop signals.
    cache_utils: Any  # WHY: CacheUtils facade for CSV generation.
    org_site_exporter: Any  # WHY: OrgSiteExporter facade for site data.
    gateway_export_utils: Any  # WHY: GatewayExportUtils facade for template data.
    file_path_utils: Any  # WHY: FilePathUtils facade for path resolution.
    input_utils: Any  # WHY: InputUtils facade for safe_input prompts.
    data_exporter: Any  # WHY: DataExporter facade for report writing.
    mistapi: Any  # WHY: mistapi library used for device endpoints.
    site_exclude_prefix: str = ""  # WHY: prefix filter for excluded sites.


def configure_wan_probe_device_override_dependencies(  # WHY: wire module-level slots from orchestrator.
    dependencies: WANProbeDeviceOverrideDependencies,
) -> None:
    """Configure runtime dependencies from MistHelper orchestration layer."""
    logging.info(
        "Wiring WAN probe device override deps (prefix=%r)", dependencies.site_exclude_prefix
    )  # WHY: log wire.
    globals().update(  # WHY: bulk-assign module slots without listing 10 explicit globals.
        {
            "apisession": dependencies.apisession,  # WHY: expose API session at module scope.
            "ConfigUtils": dependencies.config_utils,  # WHY: expose config helpers.
            "CacheUtils": dependencies.cache_utils,  # WHY: expose cache utilities.
            "OrgSiteExporter": dependencies.org_site_exporter,  # WHY: expose site exporter.
            "GatewayExportUtils": dependencies.gateway_export_utils,  # WHY: expose gateway exporter.
            "FilePathUtils": dependencies.file_path_utils,  # WHY: expose path resolver.
            "InputUtils": dependencies.input_utils,  # WHY: expose safe input helper.
            "DataExporter": dependencies.data_exporter,  # WHY: expose report writer.
            "mistapi": dependencies.mistapi,  # WHY: expose REST client library.
            "MIST_SITE_EXCLUDE_PREFIX": dependencies.site_exclude_prefix,  # WHY: expose exclude prefix.
        }
    )


class WANProbeDeviceOverrideManager:  # WHY: encapsulates Menu #167 destructive workflow.
    """Manages WAN probe configuration for device-level port overrides.

    Menu #167: Configure WAN probe override settings on gateway devices that
    have device-level port overrides. This complements Menu #166 (template-level)
    by targeting ONLY ports that have been overridden from their template.

    Workflow:
        1. User selects a gateway template
        2. Find all sites using that template
        3. Find all gateway devices in those sites
        4. Identify devices with port-level WAN overrides
        5. Apply ICMP probe configuration to ONLY overridden WAN ports

    Default Configuration:
        - probe IPs: ["192.151.29.254", "18.154.184.32"] (override via MIST_WAN_PROBE_IPS)
        - probe_profile: "lte" (override via MIST_WAN_PROBE_PROFILE)
    """

    DEFAULT_PROBE_IPS = DEFAULT_PROBE_IPS  # WHY: expose module default at class scope for callers.
    DEFAULT_PROBE_PROFILE = DEFAULT_PROBE_PROFILE  # WHY: expose module default at class scope for callers.

    def __init__(self) -> None:  # WHY: seed per-run state on the manager instance.
        """Initialize the WAN Probe Device Override Manager."""
        self.org_id: str | None = None  # WHY: resolved org UUID (set during init phase).
        self.templates: list[dict[str, Any]] = []  # WHY: gateway template rows loaded from CSV cache.
        self.sites: list[dict[str, Any]] = []  # WHY: site rows loaded from CSV cache.
        self.probe_ips = list(DEFAULT_PROBE_IPS)  # WHY: mutable per-instance copy of default probe IPs.
        self.probe_profile = DEFAULT_PROBE_PROFILE  # WHY: mutable per-instance probe profile.
        self.selected_template: dict[str, Any] | None = None  # WHY: user-selected template snapshot.
        self.template_sites: list[dict[str, Any]] = []  # WHY: sites bound to the selected template.

    @classmethod
    def configure(cls, dry_run: bool = False) -> None:  # WHY: single classmethod entry point for Menu #167.
        """Menu #167: Configure WAN Probe Override on Device Port Overrides (DESTRUCTIVE).

        Updates wan_probe_override settings for WAN ports that have device-level
        overrides from their gateway template.

        Args:
            dry_run: If True, show what would change without making modifications
        """
        manager = cls()  # WHY: fresh per-run manager instance.
        manager._execute(dry_run)  # WHY: delegate to the pipeline runner.

    def _execute(self, dry_run: bool) -> None:  # WHY: high-level pipeline orchestrator.
        """Main execution flow for device-level WAN probe configuration."""
        self._display_header(dry_run)  # WHY: banner + operator warning first.
        if not self._prepare_run():  # WHY: init + load + template + sites phase. Bail on failure.
            return
        devices = self._find_devices_with_overrides()  # WHY: identify targets for probe config.
        if not devices:  # WHY: nothing to do if no overrides exist.
            return
        self._finalise_run(devices, dry_run)  # WHY: preview + confirm + apply + report phase.

    def _prepare_run(self) -> bool:  # WHY: preparation gate returns True on success.
        """Run initialization, data load, template selection, and site discovery gates."""
        if not self._initialize():  # WHY: resolve org id first — everything else depends on it.
            return False
        if not self._load_data():  # WHY: prime template/site CSV caches.
            return False
        if not self._select_template():  # WHY: operator picks the template to target.
            return False
        return self._find_template_sites()  # WHY: expand template into concrete sites.

    def _finalise_run(self, devices: list[dict[str, Any]], dry_run: bool) -> None:
        """Preview, optionally confirm, apply changes and emit the audit report."""
        self._show_preview(devices, dry_run)  # WHY: show operator what will change.
        if not dry_run and not self._confirm_operation(len(devices)):  # WHY: gate live runs behind APPLY prompt.
            return
        results = self._apply_changes(devices, dry_run)  # WHY: push changes (or simulate in dry-run).
        self._generate_report(results, dry_run)  # WHY: emit audit CSV and summary banner.

    def _display_header(self, dry_run: bool) -> None:  # WHY: emit banner with mode-dependent warnings.
        """Display operation header with configuration details."""
        print("\n  DESTRUCTIVE: Configure WAN Probe on Device Port Overrides")  # WHY: menu banner headline.
        print(HEADER_RULE)  # WHY: visual separator.
        if dry_run:  # WHY: dry-run branch uses safer wording.
            print("  >> DRY-RUN MODE: No changes will be made to devices")  # WHY: reassure operator.
            print("  >> This will show what WOULD be changed without modifying anything")  # WHY: describe intent.
        else:  # WHY: live-run branch emits an explicit destructive warning.
            print("  !? WARNING: This operation modifies gateway device configurations")  # WHY: destructive warning.
            print("  !? Only device-level overridden WAN ports will be modified")  # WHY: scope disclaimer.
        print(HEADER_RULE)  # WHY: close warning block.
        print("\n  Probe Configuration:")  # WHY: label for configuration echo.
        print(f"    Probe IPs: {self.probe_ips}")  # WHY: echo configured probe IPs.
        print(f"    Probe Profile: {self.probe_profile}")  # WHY: echo configured probe profile.
        print(HEADER_RULE)  # WHY: close configuration echo block.
        logging.warning(
            "Menu #167 DESTRUCTIVE: Configure WAN Probe on Device Port Overrides started"
        )  # WHY: audit log.

    def _initialize(self) -> bool:  # WHY: initialization gate — resolves org id.
        """Initialize org_id. Returns True on success."""
        self.org_id = ConfigUtils.get_cached_or_prompted_org_id()  # WHY: cached-or-prompted resolution.
        if not self.org_id:  # WHY: empty org id means we cannot proceed.
            print(" Failed to get organization ID.")  # WHY: user-facing diagnostic.
            logging.error("Menu #167: Could not obtain org_id")  # WHY: audit log.
            return False
        return True

    def _load_data(self) -> bool:  # WHY: prime template/site caches and materialise CSV rows.
        """Load gateway templates and site data. Returns True on success."""
        print("\n  Loading gateway template and site data...")  # WHY: user progress message.
        CacheUtils.check_and_generate_csv(
            "OrgGatewayTemplates.csv", GatewayExportUtils.templates
        )  # WHY: refresh cache.
        CacheUtils.check_and_generate_csv("SiteList.csv", OrgSiteExporter.sites)  # WHY: refresh site cache.
        self.templates = self._read_csv_rows("OrgGatewayTemplates.csv")  # WHY: load template rows.
        if not self.templates:  # WHY: no templates → cannot proceed.
            print(" No gateway templates found.")  # WHY: user-facing diagnostic.
            logging.warning("Menu #167: No gateway templates available")  # WHY: audit log.
            return False
        self.sites = self._read_csv_rows("SiteList.csv")  # WHY: load site rows.
        logging.info(
            "Loaded %s gateway templates and %s sites", len(self.templates), len(self.sites)
        )  # WHY: audit log.
        return True

    @staticmethod
    def _read_csv_rows(name: str) -> list[dict[str, Any]]:  # WHY: shared CSV reader helper.
        """Read a cached CSV file by logical name and return its rows."""
        path = FilePathUtils.get_csv_path(name)  # WHY: resolve to concrete filesystem path.
        with open(path, encoding="utf-8") as file_handle:  # WHY: UTF-8 by convention for CSV cache.
            return list(csv.DictReader(file_handle))  # WHY: materialise rows for repeated iteration.

    def _select_template(self) -> bool:  # WHY: display template list and record operator selection.
        """Display templates and get user selection. Returns True if selected."""
        template_list = self._build_template_display_list()  # WHY: templates enriched with site counts.
        self._print_template_menu(template_list)  # WHY: emit numbered menu to operator.
        selection = self._prompt_template_selection()  # WHY: capture and normalise operator input.
        if selection == CANCEL_TOKEN:  # WHY: explicit cancel keyword short-circuits selection.
            print(" Operation cancelled.")  # WHY: user-facing diagnostic.
            logging.info("Menu #167 cancelled by user at template selection")  # WHY: audit log.
            return False
        return self._resolve_template_selection(selection, template_list)  # WHY: parse + validate numeric input.

    def _build_template_display_list(self) -> list[dict[str, Any]]:  # WHY: precompute enriched template rows.
        """Sort templates and enrich them with per-template site counts."""
        templates_sorted = sorted(self.templates, key=lambda t: t.get("name", "").lower())  # WHY: stable name order.
        counts = self._compute_template_site_counts()  # WHY: precomputed template_id -> count map.
        return [
            {
                "id": template.get("id", ""),  # WHY: template UUID for later lookup.
                "name": template.get("name", "Unnamed Template"),  # WHY: display fallback.
                "site_count": counts.get(template.get("id", ""), 0),  # WHY: site count for operator context.
            }
            for template in templates_sorted  # WHY: preserve sorted order in menu output.
        ]

    def _compute_template_site_counts(self) -> dict[str, int]:  # WHY: aggregate sites per template id.
        """Return a template_id -> site count map, honouring the exclusion prefix."""
        counts: dict[str, int] = {}  # WHY: accumulator for template site counts.
        for site in self.sites:  # WHY: single pass over cached site rows.
            if self._is_site_excluded(site):  # WHY: skip sites matched by exclude prefix.
                continue
            template_id = site.get("gatewaytemplate_id", "").strip()  # WHY: template linkage field.
            if template_id:  # WHY: ignore unbound sites.
                counts[template_id] = counts.get(template_id, 0) + 1  # WHY: increment running count.
        return counts

    @staticmethod
    def _is_site_excluded(site: dict[str, Any]) -> bool:  # WHY: single source of truth for exclusion.
        """Return True if the site should be excluded by the configured prefix filter."""
        prefix = MIST_SITE_EXCLUDE_PREFIX  # WHY: read the current module-level exclusion prefix.
        return bool(prefix) and site.get("name", "").startswith(prefix)  # WHY: match prefix when set.

    @staticmethod
    def _print_template_menu(template_list: list[dict[str, Any]]) -> None:  # WHY: numbered menu emitter.
        """Emit the numbered template selection menu."""
        print(f"\n  Available Gateway Templates ({len(template_list)}):")  # WHY: menu header with count.
        for idx, entry in enumerate(template_list, start=1):  # WHY: 1-based index for operator input.
            print(f"   [{idx}] {entry['name']} ({entry['site_count']} sites)")  # WHY: numbered entry.
        print("\n  Template Selection:")  # WHY: help label.
        print("   Enter a template number to select")  # WHY: help text for numeric input.
        print("   Or 'cancel' to abort")  # WHY: help text for cancel keyword.

    @staticmethod
    def _prompt_template_selection() -> str:  # WHY: isolated input capture for testability.
        """Read and normalise the operator's template selection."""
        raw = InputUtils.safe_input(  # WHY: shared safe_input wrapper (handles EOF/interrupts).
            "\n  Selection: ",
            context="wan_probe_device_template_selection",
        )
        return raw.strip().lower()  # WHY: normalise so 'CANCEL', ' 1 ' and so on work.

    def _resolve_template_selection(  # WHY: parse numeric input and commit to selected_template.
        self,
        selection: str,
        template_list: list[dict[str, Any]],
    ) -> bool:
        """Parse a numeric selection string and record the chosen template."""
        try:
            idx = int(selection) - 1  # WHY: operator indexes from 1. Internal index is 0-based.
        except ValueError:
            print(f" Invalid selection: {selection}")  # WHY: user-facing diagnostic.
            logging.error("Menu #167: Invalid template selection: %s", selection)  # WHY: audit log.
            return False
        if not 0 <= idx < len(template_list):  # WHY: bounds check before indexing.
            print(" Invalid selection.")  # WHY: user-facing diagnostic.
            return False
        self.selected_template = template_list[idx]  # WHY: commit operator choice to instance state.
        template_name = self.selected_template["name"]  # WHY: cached for logging output below.
        print(f"\n  Selected template: {template_name}")  # WHY: echo choice back to operator.
        logging.info("Menu #167: Selected template %s", template_name)  # WHY: audit log.
        return True

    def _find_template_sites(self) -> bool:  # WHY: expand selected template into concrete site list.
        """Find all sites using the selected template. Returns True if found."""
        assert self.selected_template is not None, "Template must be selected before finding sites"  # nosec B101
        template_id = self.selected_template["id"]  # WHY: identifier used to match sites.
        template_name = self.selected_template["name"]  # WHY: friendly name for diagnostics.
        self.template_sites = [
            {"site_id": site.get("id", ""), "site_name": site.get("name", "Unknown Site")}  # WHY: minimal projection.
            for site in self.sites  # WHY: single pass over cached rows.
            if self._site_matches_template(site, template_id)  # WHY: predicate encapsulates filtering rules.
        ]
        if not self.template_sites:  # WHY: no sites → cannot proceed further.
            print(f"\n  No sites found using template '{template_name}'.")  # WHY: user-facing diagnostic.
            logging.warning("Menu #167: No sites using template %s", template_name)  # WHY: audit log.
            return False
        print(f"\n  Found {len(self.template_sites)} sites using template '{template_name}'")  # WHY: progress echo.
        logging.info("Found %s sites using template %s", len(self.template_sites), template_name)  # WHY: audit log.
        return True

    @staticmethod
    def _site_matches_template(site: dict[str, Any], template_id: str) -> bool:  # WHY: filter predicate.
        """Return True if the site is bound to the given template and not excluded."""
        if WANProbeDeviceOverrideManager._is_site_excluded(site):  # WHY: honour exclusion prefix first.
            return False
        return site.get("gatewaytemplate_id", "").strip() == template_id  # WHY: exact template match.

    def _find_devices_with_overrides(self) -> list[dict[str, Any]]:
        """Find gateway devices with WAN port overrides. Returns list of devices."""
        print(f"\n  Scanning {len(self.template_sites)} sites for gateway devices...")  # WHY: user progress message.
        all_gateways = self._scan_template_sites_for_gateways()  # WHY: collect raw gateway entries across sites.
        if not all_gateways:  # WHY: nothing to inspect — emit diagnostics and return.
            print(f"\n  No gateway devices found in the {len(self.template_sites)} sites using this template.")
            print("  Gateways must be assigned to sites before checking for port overrides.")  # WHY: hint operator.
            logging.info("Menu #167: No gateway devices found in template sites")  # WHY: audit log.
            return []
        print(f"\n  Found {len(all_gateways)} gateway devices. Checking for WAN port overrides...")  # WHY: progress.
        devices = self._collect_devices_with_overrides(all_gateways)  # WHY: filter to overridden-only set.
        if not devices:  # WHY: no device-level overrides — short-circuit.
            print(f"\n  No WAN port overrides found on the {len(all_gateways)} gateway devices.")  # WHY: diagnostic.
            print("  All devices are using template-level WAN configuration.")  # WHY: hint operator.
            logging.info("Menu #167: No devices with WAN port overrides found")  # WHY: audit log.
            return []
        total_ports = sum(len(d["overridden_wan_ports"]) for d in devices)  # WHY: aggregate port count.
        print(f"\n  Found {len(devices)} devices with {total_ports} overridden WAN ports")  # WHY: progress echo.
        logging.info("Found %s devices with %s overridden WAN ports", len(devices), total_ports)  # WHY: audit log.
        return devices

    def _scan_template_sites_for_gateways(self) -> list[dict[str, Any]]:
        """Fetch gateway devices from every template site. Returns wrapped entries."""
        all_gateways: list[dict[str, Any]] = []  # WHY: accumulator for {device, site_id, site_name} entries.
        for site_info in tqdm(self.template_sites, desc="Scanning sites", unit="site"):  # type: ignore[no-untyped-call]
            if ConfigUtils.check_stop_signal():  # WHY: honour cooperative cancellation.
                break
            all_gateways.extend(self._scan_single_site(site_info))  # WHY: delegate per-site fetch + wrap.
        return all_gateways

    @staticmethod
    def _scan_single_site(site_info: dict[str, Any]) -> list[dict[str, Any]]:  # WHY: isolate per-site try/except.
        """Fetch gateway devices for a single site and wrap them with site metadata."""
        site_id = site_info["site_id"]  # WHY: site UUID for API call + reporting.
        site_name = site_info["site_name"]  # WHY: site name preserved for downstream report rows.
        try:
            logging.info("Listing gateway devices for site %s", site_name)  # WHY: pre-call log.
            resp = mistapi.api.v1.sites.devices.listSiteDevices(  # WHY: enumerate gateways at this site.
                apisession, site_id, type="gateway", limit=1000
            )
            devices = resp.data if hasattr(resp, "data") else []  # WHY: response may lack .data defensively.
        except Exception as error:  # pylint: disable=broad-exception-caught
            logging.warning("Error scanning site %s: %s", site_name, error)  # WHY: per-site failure is non-fatal.
            return []
        logging.debug("Site %s returned %s gateway entries", site_name, len(devices))  # WHY: post-call log.
        return [
            {"device": device, "site_id": site_id, "site_name": site_name}  # WHY: wrap with site metadata.
            for device in devices  # WHY: iterate each gateway record.
            if isinstance(device, dict)  # WHY: skip malformed entries silently.
        ]

    def _collect_devices_with_overrides(self, all_gateways: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter scanned gateways to only those with overridden WAN ports."""
        devices_with_overrides: list[dict[str, Any]] = []  # WHY: accumulator for filtered devices.
        for gateway_info in all_gateways:  # WHY: walk every scanned gateway record.
            entry = self._extract_device_override_entry(gateway_info)  # WHY: build per-device entry when applicable.
            if entry is not None:  # WHY: only retain devices that actually have WAN overrides.
                devices_with_overrides.append(entry)  # WHY: append matched device.
        return devices_with_overrides

    @classmethod
    def _extract_device_override_entry(  # WHY: pure helper (predicate + projection) per gateway record.
        cls,
        gateway_info: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Return a normalised override entry for a gateway, or None if it has no WAN overrides."""
        device = gateway_info["device"]  # WHY: raw device dict from Mist.
        port_config = device.get("port_config", {})  # WHY: local port overrides keyed by port name.
        if not isinstance(port_config, dict) or not port_config:  # WHY: nothing to inspect.
            return None
        overridden_wan_ports = cls._extract_overridden_wan_ports(port_config)  # WHY: per-device override extract.
        if not overridden_wan_ports:  # WHY: skip devices with no WAN overrides.
            return None
        return {
            "device_id": device.get("id", ""),  # WHY: preserve device UUID for later update call.
            "device_name": device.get("name", "Unknown Device"),  # WHY: friendly name for reporting.
            "site_id": gateway_info["site_id"],  # WHY: carry forward site UUID.
            "site_name": gateway_info["site_name"],  # WHY: carry forward site display name.
            "overridden_wan_ports": overridden_wan_ports,  # WHY: override details for downstream update.
        }

    @staticmethod
    def _extract_overridden_wan_ports(port_config: dict[str, Any]) -> list[dict[str, Any]]:
        """Return a list of overridden WAN port descriptors from a device's port_config."""
        overridden_wan_ports: list[dict[str, Any]] = []  # WHY: collected WAN port override entries.
        for port_name, port_settings in port_config.items():  # WHY: inspect each port.
            if not isinstance(port_settings, dict) or port_settings.get("usage") != "wan":  # WHY: WAN-only.
                continue
            current_probe = port_settings.get("wan_probe_override", {})  # WHY: existing override blob (if any).
            if not isinstance(current_probe, dict):  # WHY: defensive — probe may be malformed.
                current_probe = {}
            overridden_wan_ports.append(
                {
                    "port_name": port_name,  # WHY: port identifier (for example ge-0/0/0).
                    "current_ips": current_probe.get("ips", []),  # WHY: existing probe IPs.
                    "current_profile": current_probe.get("probe_profile", ""),  # WHY: existing probe profile.
                    "port_settings": port_settings,  # WHY: full port settings retained for context.
                }
            )
        return overridden_wan_ports

    def _show_preview(self, devices_with_overrides: list[dict[str, Any]], dry_run: bool) -> None:  # nosec B101
        """Display preview of changes to be made."""
        del dry_run  # WHY: parameter retained for signature parity with pipeline dispatcher.
        assert self.selected_template is not None, "Template must be selected"  # nosec B101
        total_ports = sum(len(d["overridden_wan_ports"]) for d in devices_with_overrides)  # WHY: aggregate ports.
        self._print_preview_header(devices_with_overrides, total_ports)  # WHY: banner + counts.
        preview_count = min(PREVIEW_DEVICE_LIMIT, len(devices_with_overrides))  # WHY: cap sample size.
        print(f"\n  Sample devices (showing {preview_count} of {len(devices_with_overrides)}):")  # WHY: sample label.
        for device in devices_with_overrides[:preview_count]:  # WHY: print sample slice.
            self._print_preview_device(device)  # WHY: delegate per-device rendering.
        remaining = len(devices_with_overrides) - preview_count  # WHY: count devices not printed.
        if remaining > 0:  # WHY: only show ellipsis when there are more devices.
            print(f"\n   ... and {remaining} more devices")  # WHY: hint operator that list is truncated.

    def _print_preview_header(self, devices: list[dict[str, Any]], total_ports: int) -> None:  # WHY: banner emitter.
        """Emit the preview header block."""
        assert self.selected_template is not None  # nosec B101
        print("\n  Preview of Changes:")  # WHY: banner label.
        print(f"  Template: {self.selected_template['name']}")  # WHY: echo target template.
        print(f"  Devices: {len(devices)}")  # WHY: echo device count.
        print(f"  Overridden WAN Ports: {total_ports}")  # WHY: echo port count.

    def _print_preview_device(self, device: dict[str, Any]) -> None:  # WHY: per-device preview renderer.
        """Print current-vs-new probe config for one device."""
        print(f"\n   Device: {device['device_name']} ({device['site_name']})")  # WHY: device header line.
        for wan_port in device["overridden_wan_ports"]:  # WHY: iterate overridden WAN ports.
            port = wan_port["port_name"]  # WHY: port identifier.
            current_ips = wan_port["current_ips"] or ["(none)"]  # WHY: pretty-print empty ip list.
            current_profile = wan_port["current_profile"] or "(none)"  # WHY: pretty-print empty profile.
            print(f"     {port}:")  # WHY: port sub-header.
            print(f"       Current: ips={current_ips}, profile={current_profile}")  # WHY: show current state.
            print(f"       New:     ips={self.probe_ips}, profile={self.probe_profile}")  # WHY: show pending state.

    def _confirm_operation(self, device_count: int) -> bool:  # WHY: destructive-change gate.
        """Prompt for confirmation. Returns True if confirmed."""
        print(f"\n  {HEADER_RULE}")  # WHY: banner rule.
        print(f"  !? CRITICAL: This will modify {device_count} gateway devices")  # WHY: destructive warning.
        print(f"  !? Type '{APPLY_CONFIRM_TOKEN}' (all caps) to proceed or anything else to cancel")  # WHY: prompt.
        print(f"  {HEADER_RULE}")  # WHY: banner rule.
        confirmation = InputUtils.safe_input(  # WHY: shared safe_input wrapper.
            "\n  Confirmation: ",
            context="wan_probe_device_apply_confirmation",
        ).strip()
        if confirmation != APPLY_CONFIRM_TOKEN:  # WHY: require exact uppercase APPLY.
            print(" Operation cancelled.")  # WHY: user-facing diagnostic.
            logging.info("Menu #167 cancelled by user at final confirmation")  # WHY: audit log.
            return False
        return True

    def _apply_changes(self, devices_with_overrides: list[dict[str, Any]], dry_run: bool) -> list[dict[str, Any]]:
        """Apply probe configuration changes to devices. Returns results."""
        print("\n  Applying WAN probe configuration to device overrides...")  # WHY: user progress message.
        results: list[dict[str, Any]] = []  # WHY: accumulator for per-device outcomes.
        for device in tqdm(  # type: ignore[no-untyped-call]  # WHY: progress bar over device list.
            devices_with_overrides,
            desc="Updating devices",
            unit="device",
        ):
            if ConfigUtils.check_stop_signal():  # WHY: honour cooperative cancellation.
                break
            results.append(self._update_single_device(device, dry_run))  # WHY: record per-device outcome.
        return results

    def _update_single_device(self, device: dict[str, Any], dry_run: bool) -> dict[str, Any]:  # nosec B101
        """Update a single device's overridden WAN port probe configuration."""
        assert self.selected_template is not None, "Template must be selected"  # nosec B101
        result = self._initial_device_result(device)  # WHY: pre-populated result skeleton.
        try:
            self._run_device_update(device, dry_run, result)  # WHY: delegate patch pipeline.
        except Exception as error:  # pylint: disable=broad-exception-caught
            result["status"] = "ERROR"  # WHY: record any unexpected failure.
            result["error"] = str(error)  # WHY: preserve error message for audit CSV.
            logging.error("Error updating device %s: %s", result["device_name"], error)  # WHY: audit log.
            logging.error(traceback.format_exc())  # WHY: full traceback for postmortem.
        return result

    def _run_device_update(  # WHY: extracted try-body keeps _update_single_device under length limit.
        self,
        device: dict[str, Any],
        dry_run: bool,
        result: dict[str, Any],
    ) -> None:
        """Execute the fetch/patch/commit pipeline for a single device."""
        logging.info("Updating WAN probe overrides for device %s", result["device_name"])  # WHY: pre-action log.
        device_config = self._fetch_device_config(device, result)  # WHY: fetch + validate device config.
        if device_config is None:  # WHY: validation failed — result already set, exit early.
            return
        ports_modified = self._apply_probe_to_ports(  # WHY: mutate port_config in place.
            device_config["port_config"],
            device["overridden_wan_ports"],
            result["device_name"],
        )
        if not ports_modified:  # WHY: nothing matched — record SKIPPED.
            result["status"] = "SKIPPED"  # WHY: record outcome for report.
            result["error"] = "No matching ports found in current config"  # WHY: human-readable reason.
            return
        result["ports_updated"] = ports_modified  # WHY: record names of mutated ports.
        self._commit_device_update(device, device_config, dry_run, result)  # WHY: push or dry-run.
        logging.debug("Device %s update result: %s", result["device_name"], result["status"])  # WHY: post-log.

    def _initial_device_result(self, device: dict[str, Any]) -> dict[str, Any]:  # nosec B101
        """Return a fresh result skeleton for one device update attempt."""
        assert self.selected_template is not None  # nosec B101
        return {
            "device_name": device["device_name"],  # WHY: for logging + report rendering.
            "device_id": device["device_id"],  # WHY: preserve UUID in report.
            "site_name": device["site_name"],  # WHY: preserve site name for report.
            "site_id": device["site_id"],  # WHY: preserve site UUID in report.
            "template_name": self.selected_template["name"],  # WHY: template association for audit.
            "ports_updated": [],  # WHY: filled in if any ports are actually modified.
            "status": "",  # WHY: SUCCESS / FAILED / SKIPPED / DRY-RUN / ERROR.
            "error": "",  # WHY: human-readable failure detail.
        }

    @staticmethod
    def _fetch_device_config(device: dict[str, Any], result: dict[str, Any]) -> dict[str, Any] | None:
        """Fetch device config from Mist and verify it has a usable port_config."""
        logging.debug("Fetching device config for %s", device["device_name"])  # WHY: pre-call log.
        resp = mistapi.api.v1.sites.devices.getSiteDevice(  # WHY: full device config from Mist.
            apisession, device["site_id"], device["device_id"]
        )
        device_config = resp.data if hasattr(resp, "data") else {}  # WHY: defensive — response may lack .data.
        if not isinstance(device_config, dict):  # WHY: Mist returned non-dict body — unusable.
            result["status"] = "SKIPPED"  # WHY: record skipped outcome.
            result["error"] = "Invalid device config structure"  # WHY: human-readable reason.
            return None
        port_config = device_config.get("port_config", {})  # WHY: ensure port_config dict exists.
        if not isinstance(port_config, dict):  # WHY: no port_config to patch — skip.
            result["status"] = "SKIPPED"  # WHY: record skipped outcome.
            result["error"] = "No port_config found"  # WHY: human-readable reason.
            return None
        device_config["port_config"] = port_config  # WHY: normalise back onto config for downstream mutation.
        return device_config

    def _apply_probe_to_ports(
        self,
        port_config: dict[str, Any],
        overridden_wan_ports: list[dict[str, Any]],
        device_name: str,
    ) -> list[str]:
        """Patch wan_probe_override on each matching port. Return modified port names."""
        ports_modified: list[str] = []  # WHY: names of ports that were actually patched.
        for wan_port in overridden_wan_ports:  # WHY: iterate planned overrides.
            port_name = wan_port["port_name"]  # WHY: cached port identifier.
            if port_name not in port_config:  # WHY: port no longer present on device — skip silently.
                continue
            if not isinstance(port_config[port_name], dict):  # WHY: defensive — replace non-dict scalar.
                port_config[port_name] = {}
            port_config[port_name]["wan_probe_override"] = {  # WHY: write new probe payload.
                "ips": self.probe_ips.copy(),  # WHY: copy so callers cannot mutate shared list.
                "probe_profile": self.probe_profile,  # WHY: current profile value.
            }
            ports_modified.append(port_name)  # WHY: record success for this port.
            logging.debug("Device %s: Updated %s probe config", device_name, port_name)  # WHY: audit log.
        return ports_modified

    @staticmethod
    def _commit_device_update(
        device: dict[str, Any],
        device_config: dict[str, Any],
        dry_run: bool,
        result: dict[str, Any],
    ) -> None:
        """Push the patched config back to Mist or mark as DRY-RUN."""
        device_name = device["device_name"]  # WHY: cached for logging.
        if dry_run:  # WHY: skip the actual API write in dry-run mode.
            result["status"] = "DRY-RUN"  # WHY: mark simulated outcome.
            logging.info("DRY-RUN: Would update device %s ports: %s", device_name, result["ports_updated"])
            return
        logging.info("Updating device %s via Mist API", device_name)  # WHY: pre-call log.
        update_resp = mistapi.api.v1.sites.devices.updateSiteDevice(  # WHY: write back patched config.
            apisession, device["site_id"], device["device_id"], body=device_config
        )
        logging.debug("Device %s update API status=%s", device_name, update_resp.status_code)  # WHY: post-call log.
        if update_resp.status_code == HTTP_OK:  # WHY: success path.
            result["status"] = "SUCCESS"  # WHY: record success outcome.
            logging.info("Successfully updated device %s", device_name)  # WHY: audit log.
            return
        result["status"] = "FAILED"  # WHY: non-200 → mark failed.
        result["error"] = f"API returned status {update_resp.status_code}"  # WHY: capture status code.
        logging.error("Failed to update device %s: %s", device_name, update_resp.status_code)  # WHY: audit log.

    def _generate_report(self, results: list[dict[str, Any]], dry_run: bool) -> None:  # nosec B101
        """Generate and display final report."""
        assert self.selected_template is not None, "Template must be selected"  # nosec B101
        template_name = self.selected_template["name"]  # WHY: display name for summary banner.
        self._write_audit_csv(results)  # WHY: emit CSV before summary banner.
        total_ports = self._total_ports_from_results(results)  # WHY: aggregate for summary.
        self._emit_summary(results, template_name, total_ports, dry_run)  # WHY: mode-specific summary.
        print(f"\n  Report saved to: {AUDIT_OUTPUT_FILE}")  # WHY: echo audit file path.
        print(HEADER_RULE)  # WHY: close banner.
        success_count = self._count_success(results)  # WHY: successful updates only.
        logging.warning("Menu #167 DESTRUCTIVE operation complete: %s devices updated", success_count)  # WHY: audit.

    def _write_audit_csv(self, results: list[dict[str, Any]]) -> None:  # WHY: isolate CSV export side effect.
        """Serialise per-device results to the audit CSV via the injected exporter."""
        report_data = self._build_report_rows(results)  # WHY: CSV-shaped rows per device.
        logging.info("Saving WAN probe override audit CSV: %s", AUDIT_OUTPUT_FILE)  # WHY: pre-write log.
        DataExporter.write_with_format_selection(report_data, AUDIT_OUTPUT_FILE)  # type: ignore[no-untyped-call]
        logging.debug("Audit CSV saved (rows=%s)", len(report_data))  # WHY: post-write log.

    def _emit_summary(  # WHY: dispatch dry-run vs apply summary printer.
        self,
        results: list[dict[str, Any]],
        template_name: str,
        total_ports: int,
        dry_run: bool,
    ) -> None:
        """Emit the mode-appropriate completion summary banner."""
        summary_printer = self._print_dry_run_summary if dry_run else self._print_apply_summary  # WHY: dispatch.
        summary_printer(results, template_name, total_ports)  # WHY: emit mode-specific summary.

    @staticmethod
    def _total_ports_from_results(results: list[dict[str, Any]]) -> int:  # WHY: isolate genexp branch.
        """Return the total number of ports across all per-device results."""
        return sum(len(r["ports_updated"]) for r in results)  # WHY: aggregate ports modified.

    @staticmethod
    def _count_success(results: list[dict[str, Any]]) -> int:  # WHY: isolate filtered genexp branch.
        """Return the count of SUCCESS-status entries in the results list."""
        return sum(1 for r in results if r["status"] == "SUCCESS")  # WHY: successful updates only.

    def _build_report_rows(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert internal per-device results into CSV-shaped report rows."""
        rows: list[dict[str, Any]] = []  # WHY: accumulator for the flattened rows.
        for result in results:  # WHY: iterate per-device outcome.
            rows.append(
                {
                    "device_name": result["device_name"],  # WHY: device display name.
                    "device_id": result["device_id"],  # WHY: device UUID.
                    "site_name": result["site_name"],  # WHY: site display name.
                    "site_id": result["site_id"],  # WHY: site UUID.
                    "template_name": result["template_name"],  # WHY: template association.
                    "ports_updated": ", ".join(result["ports_updated"]) if result["ports_updated"] else "",
                    "port_count": len(result["ports_updated"]),  # WHY: number of ports patched.
                    "status": result["status"],  # WHY: outcome status token.
                    "error": result["error"],  # WHY: error detail (empty on success).
                    "new_probe_ips": ", ".join(self.probe_ips),  # WHY: configuration applied.
                    "new_probe_profile": self.probe_profile,  # WHY: probe profile applied.
                }
            )
        return rows

    @staticmethod
    def _print_dry_run_summary(results: list[dict[str, Any]], template_name: str, total_ports: int) -> None:
        """Print the dry-run completion banner."""
        dry_run_count = sum(1 for r in results if r["status"] == "DRY-RUN")  # WHY: count planned updates.
        print("\n  WAN Probe Device Override DRY-RUN Complete!")  # WHY: completion banner.
        print(HEADER_RULE)  # WHY: banner separator.
        print("  >> DRY-RUN MODE: No actual changes were made")  # WHY: reassure operator.
        print(f"  Template: {template_name}")  # WHY: echo target template.
        print(f"  Devices Analyzed: {len(results)}")  # WHY: total devices considered.
        print(f"  Would Update: {dry_run_count} devices")  # WHY: devices with pending changes.
        print(f"  WAN Ports: {total_ports}")  # WHY: aggregate ports considered.
        print("\n  >> To apply changes, run without --dry-run flag")  # WHY: hint operator.

    def _print_apply_summary(self, results: list[dict[str, Any]], template_name: str, total_ports: int) -> None:
        """Print the live-run completion banner with success/failure breakdown."""
        success_count = sum(1 for r in results if r["status"] == "SUCCESS")  # WHY: successful updates.
        failure_count = len(results) - success_count  # WHY: everything else counts as failed/skipped.
        print("\n  WAN Probe Device Override Complete!")  # WHY: completion banner.
        print(HEADER_RULE)  # WHY: banner separator.
        print(f"  Template: {template_name}")  # WHY: echo target template.
        print(f"  Devices Updated: {success_count}")  # WHY: successful count.
        print(f"  Devices Failed: {failure_count}")  # WHY: failed/skipped count.
        print(f"  WAN Ports Configured: {total_ports}")  # WHY: aggregate ports configured.
        if success_count > 0:  # WHY: echo configuration for operator visibility.
            print("\n  Configuration Applied:")  # WHY: config label.
            print(f"    Probe IPs: {self.probe_ips}")  # WHY: applied probe IPs.
            print(f"    Probe Profile: {self.probe_profile}")  # WHY: applied probe profile.
        if failure_count > 0:  # WHY: direct operator to audit CSV for details.
            print(f"\n  !? {failure_count} devices failed - check audit report")  # WHY: failure hint.
