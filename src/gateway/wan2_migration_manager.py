"""WAN2 migration manager extracted from MistHelper menu 149 flow."""

from __future__ import annotations  # WHY: postpone hint evaluation for forward refs.

import csv  # WHY: parse SiteList / gateway config CSV caches.
import json  # WHY: decode port_config_* JSON payloads from CSV rows.
import logging  # WHY: structured logging for entry/exit and errors.
import traceback  # WHY: capture full exception traces on site update failures.
from dataclasses import dataclass  # WHY: build the frozen dependency bundle.
from typing import Any  # WHY: opaque types for injected utility modules.

from tqdm import tqdm  # WHY: progress bar over per-site update loop.

apisession: Any = None  # WHY: Mist API session slot populated at wiring time.
ConfigUtils: Any = None  # WHY: config helpers (org id + stop-signal check).
CacheUtils: Any = None  # WHY: CSV cache generator for exported data.
OrgSiteExporter: Any = None  # WHY: org-scoped site export utility.
GatewayExportUtils: Any = None  # WHY: device/template export utilities.
FilePathUtils: Any = None  # WHY: resolves CSV cache file locations.
InputUtils: Any = None  # WHY: safe_input wrapper for operator prompts.
DataExporter: Any = None  # WHY: writes report data with format selection.
mistapi: Any = None  # WHY: Mist REST client library reference.
MIST_SITE_EXCLUDE_PREFIX = ""  # WHY: prefix filter that removes lab/test sites.

DEFAULT_WAN2_INTERFACE_VALUE = "ge-0/0/1"  # WHY: canonical value applied to sites.
WAN2_VARIABLE_NAME = "wan2_interface"  # WHY: site-variable key updated by Menu #149.
BASE_PORT_IDENTIFIER = "ge-0/0/1"  # WHY: fallback port identifier when subif missing.
NULLISH_TOKENS = frozenset({"", "null", "none"})  # WHY: values treated as "no override".
VPN_MARKER = "_vpn_paths_"  # WHY: substring that flags a VPN-only override we ignore.
PORT_CONFIG_PREFIXES = (  # WHY: field prefixes considered part of the WAN2 port.
    "port_config_ge-0/0/1_",  # WHY: literal base-port scalar fields.
    "port_config_ge-0/0/1.",  # WHY: literal base-port subinterface fields.
    "port_config_{{wan2_interface}}_",  # WHY: variablised base-port scalar fields.
    "port_config_{{wan2_interface}}.",  # WHY: variablised base-port subinterface fields.
)
SUBIF_PREFIXES = (  # WHY: subset of PORT_CONFIG_PREFIXES that mark subinterfaces.
    "port_config_ge-0/0/1.",  # WHY: literal subinterface fields.
    "port_config_{{wan2_interface}}.",  # WHY: variablised subinterface fields.
)
IP_TYPE_SEVERITY: dict[tuple[str, str], str] = {  # WHY: lookup table for severity classifier.
    ("dhcp", "static"): "CRITICAL",  # WHY: static IP override against DHCP template.
    ("static", "dhcp"): "WARNING",  # WHY: DHCP override against static template.
    ("dhcp", "dhcp"): "INFO",  # WHY: matching DHCP with non-critical override.
    ("static", "static"): "INFO",  # WHY: matching static with non-critical override.
}
CONFIRM_YES_TOKENS = frozenset({"yes", "y"})  # WHY: accepted affirmative confirm inputs.
HTTP_OK = 200  # WHY: expected success status from Mist site-setting API.


@dataclass(frozen=True)
class WAN2MigrationDependencies:  # WHY: frozen bundle avoids 10-arg configure signature.
    """Immutable dependency bundle wired into the WAN2 migration module."""

    apisession: Any  # WHY: authenticated Mist API session handle.
    config_utils: Any  # WHY: ConfigUtils facade for org id/stop signals.
    cache_utils: Any  # WHY: CacheUtils facade for CSV generation.
    org_site_exporter: Any  # WHY: OrgSiteExporter facade for site data.
    gateway_export_utils: Any  # WHY: GatewayExportUtils facade for gateway data.
    file_path_utils: Any  # WHY: FilePathUtils facade for path resolution.
    input_utils: Any  # WHY: InputUtils facade for safe_input prompts.
    data_exporter: Any  # WHY: DataExporter facade for report writing.
    mistapi: Any  # WHY: mistapi library used for site setting endpoints.
    site_exclude_prefix: str = ""  # WHY: prefix filter for excluded sites.


def configure_wan2_migration_dependencies(dependencies: WAN2MigrationDependencies) -> None:  # WHY: wire slots.
    """Configure runtime dependencies from MistHelper orchestration layer."""
    logging.info("Wiring WAN2 migration dependencies (prefix=%r)", dependencies.site_exclude_prefix)  # WHY: log entry.
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
    logging.debug("WAN2 migration dependencies wired successfully")  # WHY: exit-log for observability.


def _is_meaningful_override_value(raw: str) -> bool:  # WHY: filter null/blank overrides.
    """Return True when a raw CSV value should be treated as a real override."""
    return raw.strip().lower() not in NULLISH_TOKENS  # WHY: reject blanks / null tokens.


def _looks_like_wan2_field(column_name: str) -> bool:  # WHY: WAN2-column predicate.
    """Return True when a column belongs to the WAN2 port_config family."""
    return column_name.startswith(PORT_CONFIG_PREFIXES)  # WHY: any WAN2 prefix qualifies.


def _looks_like_subif_type_field(column_name: str) -> bool:  # WHY: subif-type predicate.
    """Return True when a column is a subinterface `_ip_config_type` marker."""
    return column_name.startswith(SUBIF_PREFIXES) and column_name.endswith("_ip_config_type")  # WHY: two-part match.


def _subif_name_from_type_column(column_name: str) -> str:  # WHY: strip prefix/suffix noise.
    """Strip prefix/suffix noise to recover a subinterface identifier."""
    return column_name.replace("port_config_", "").replace("_ip_config_type", "")  # WHY: keep only subif segment.


def _parse_json_ip_payload(raw: str) -> tuple[str, str, str, str]:  # WHY: shared JSON parser.
    """Parse a raw port_config IP JSON payload into (ip_type, ip, netmask, gateway)."""
    if not raw:  # WHY: fast-path for empty payloads (common case).
        return ("", "", "", "")  # WHY: caller substitutes defaults.
    try:  # WHY: JSON may be malformed in operator-provided CSV rows.
        payload = json.loads(raw)  # WHY: convert JSON string into dict.
    except json.JSONDecodeError as error:  # WHY: swallow parse error and surface tag.
        logging.warning("Failed to parse IP JSON payload: %s", error)  # WHY: expose warning to logs.
        return ("parse_error", "", "", "")  # WHY: propagate sentinel for downstream flow.
    ip_type = payload.get("type", "").lower()  # WHY: normalise to lowercase for comparisons.
    if ip_type == "static":  # WHY: only static payloads carry ip/netmask/gateway.
        return (
            ip_type,
            payload.get("ip", ""),
            payload.get("netmask", ""),
            payload.get("gateway", ""),
        )  # WHY: pass-through.
    return (ip_type or "not_configured", "", "", "")  # WHY: normalise missing/unknown types.


@dataclass(frozen=True)
class OverrideAnalysisContext:  # WHY: immutable context bundle for override analysis helpers.
    """Immutable context passed between override-analysis helpers."""

    site_id: str  # WHY: site identifier for template lookup.
    device_name: str  # WHY: device name kept for reporting.
    device_ip: dict[str, str]  # WHY: parsed device IP info (base or subif).
    template_ip_type: str  # WHY: template's expected IP type for the port.


class WAN2MigrationManager:  # WHY: consolidated Menu 103/104 flow into a single manager.
    """Manages WAN2 interface variable migration for gateway templates and sites.

    Consolidates Menu Options 103 and 104:
    - set_site_variable(): Set wan2_interface site variable across sites (Menu 103)
    - update_templates(): Migrate gateway templates to use {{wan2_interface}} variable (Menu 104)

    Both operations support bidirectional migration (apply/revert) and preserve device-level
    static IP overrides by properly handling port_config keys.
    """

    def __init__(self) -> None:  # WHY: capture org id and prep hydration slots.
        """Initialize the WAN2 migration manager."""
        self.org_id = ConfigUtils.get_cached_or_prompted_org_id()  # WHY: capture active org for downstream calls.
        self.sites: list[dict[str, Any]] = []  # WHY: hydrated from SiteList.csv cache.
        self.gateway_configs: list[dict[str, Any]] = []  # WHY: hydrated from gateway export CSV.
        self.template_data: list[dict[str, Any]] = []  # WHY: hydrated from template export CSV.
        self.site_to_template_id: dict[str, str] = {}  # WHY: quick site->template lookup.
        self.template_port_configs: dict[str, dict[str, str]] = {}  # WHY: template port IP config cache.
        self.site_overrides_map: dict[str, list[dict[str, Any]]] = {}  # WHY: per-site override records.

    def set_site_variable(self) -> None:  # WHY: Menu #149 entrypoint.
        """Menu #149 entrypoint: assign wan2_interface variable across selected sites."""
        self._display_site_variable_header()  # WHY: banner + operation description.
        if not self._load_required_data():  # WHY: fail early when caches unavailable.
            return  # WHY: caller aborts without further processing.
        sites_to_configure = self._resolve_sites_to_configure()  # WHY: consolidated selection pipeline.
        if not sites_to_configure:  # WHY: user cancelled or nothing survived filtering.
            return  # WHY: bail when selection is empty.
        if not self._confirm_site_variable_operation(len(sites_to_configure)):  # WHY: last-chance operator gate.
            return
        self._build_override_detection_map()  # WHY: pre-compute per-site override severity map.
        results = self._process_sites_for_variable(sites_to_configure)  # WHY: apply variable per site.
        self._generate_site_variable_report(results)  # WHY: emit CSV/report and print summary.

    def _resolve_sites_to_configure(self) -> list[dict[str, Any]]:
        """Select target sites and remove excluded ones in a single pipeline."""
        selected = self._get_site_selection()  # WHY: run interactive selection.
        if not selected:  # WHY: skip filtering when nothing selected.
            return []
        return self._filter_excluded_sites(selected)  # WHY: apply security prefix filter.

    def _display_site_variable_header(self) -> None:
        """Display operation header for Menu #149."""
        print("\n  Set WAN2 Interface Site Variable")  # WHY: menu banner line 1.
        print("=" * 70)  # WHY: banner divider.
        print("  This operation will set the 'wan2_interface' site variable to 'ge-0/0/1'")  # WHY: describe action.
        print("  across selected sites, preparing them for template-based WAN migration.")  # WHY: describe scope.
        print("=" * 70)  # WHY: banner closing divider.
        logging.info("Menu #149: Set WAN2 Interface Site Variable operation started")  # WHY: audit-log entry.

    def _load_required_data(self) -> bool:
        """Load site and gateway configuration data. Returns True on success."""
        print("\n  Preparing site and gateway configuration data...")  # WHY: operator progress cue.
        CacheUtils.check_and_generate_csv("SiteList.csv", OrgSiteExporter.sites)  # WHY: ensure site cache present.
        CacheUtils.check_and_generate_csv(
            "AllSiteGatewayConfigs.csv", GatewayExportUtils.device_configs
        )  # WHY: device cache.
        CacheUtils.check_and_generate_csv(
            "OrgGatewayTemplates.csv", GatewayExportUtils.templates
        )  # WHY: template cache.
        site_list_path = FilePathUtils.get_csv_path("SiteList.csv")  # WHY: resolve cache location.
        with open(site_list_path, encoding="utf-8") as file_handle:  # WHY: read cached site list.
            self.sites = list(csv.DictReader(file_handle))  # WHY: hydrate self.sites for downstream selectors.
        if not self.sites:  # WHY: empty cache aborts the flow.
            print(" No sites found in organization.")  # WHY: operator feedback.
            logging.warning("No sites available for WAN2 variable assignment")  # WHY: log warning.
            return False
        return True  # WHY: signal success to caller.

    def _get_site_selection(self) -> list[dict[str, Any]]:
        """Prompt user for site selection. Returns selected sites or empty list."""
        logging.info("Entering _get_site_selection: %s sites available", len(self.sites))  # WHY: entry log.
        self._print_selection_menu()  # WHY: display selection options.
        choice = self._prompt_selection_method()  # WHY: capture operator choice.
        result = self._dispatch_selection_choice(choice)  # WHY: convert choice into a site list.
        logging.info("Exiting _get_site_selection: %s sites returned", len(result))  # WHY: exit log.
        return result

    def _print_selection_menu(self) -> None:
        """Print the operator-facing site selection menu."""
        print(f"\n  Found {len(self.sites)} sites in organization")  # WHY: quick summary.
        print("  Site Selection:")  # WHY: menu header.
        print("   1. Select individual sites")  # WHY: option one.
        print("   2. All sites in organization")  # WHY: option two.
        print("   3. Cancel")  # WHY: option three.

    def _prompt_selection_method(self) -> str:
        """Prompt for the site-selection method and return the raw choice string."""
        return InputUtils.safe_input(  # WHY: reuse safe_input for policy-compliant prompts.
            "\n  Choose selection method (1-3): ",
            context="wan2_site_selection_method",
        ).strip()

    def _dispatch_selection_choice(self, choice: str) -> list[dict[str, Any]]:
        """Convert a selection choice string into the corresponding site list."""
        if choice == "1":  # WHY: individual selection path.
            return self._select_individual_sites()
        if choice == "2":  # WHY: whole-org selection path.
            return self.sites.copy()  # WHY: defensive copy to avoid mutation.
        print(" Operation cancelled.")  # WHY: any other input cancels.
        logging.info("Menu #149 cancelled by user")  # WHY: audit-log cancellation.
        return []  # WHY: empty list signals cancellation.

    def _select_individual_sites(self) -> list[dict[str, Any]]:
        """Display site list and get individual selections."""
        self._print_site_index_menu()  # WHY: enumerate available sites.
        raw_indices = InputUtils.safe_input(
            "  Site numbers: ", context="wan2_site_index_selection"
        ).strip()  # WHY: get input.
        return self._parse_site_indices(raw_indices)  # WHY: convert to concrete site dicts.

    def _print_site_index_menu(self) -> None:
        """Print the numbered site menu for individual selection."""
        print("\n  Available Sites:")  # WHY: menu header.
        for index, site in enumerate(self.sites, start=1):  # WHY: enumerate for operator input.
            site_name = site.get("name", "Unnamed Site")  # WHY: fallback name when missing.
            site_id = site.get("id", "")  # WHY: display id alongside name.
            print(f"   [{index}] {site_name} ({site_id})")  # WHY: formatted menu row.
        print("\n  Enter site numbers to configure (comma-separated, e.g., 1,3,5):")  # WHY: guidance.

    def _parse_site_indices(self, raw_indices: str) -> list[dict[str, Any]]:
        """Parse comma-separated 1-based indices into a list of site records."""
        try:  # WHY: guard against malformed operator input.
            selected = [int(idx.strip()) - 1 for idx in raw_indices.split(",")]  # WHY: convert to 0-based.
            return [self.sites[idx] for idx in selected if 0 <= idx < len(self.sites)]  # WHY: bounds-check.
        except (ValueError, IndexError) as error:  # WHY: surface conversion / index errors.
            print(f" Invalid site selection: {error}")  # WHY: operator feedback.
            logging.error("Invalid site selection in Menu #149: %s", error)  # WHY: audit-log.
            return []  # WHY: empty list signals abort.

    def _filter_excluded_sites(self, sites_to_configure: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter out excluded sites from configuration list based on MIST_SITE_EXCLUDE_PREFIX."""
        if not MIST_SITE_EXCLUDE_PREFIX:  # WHY: no prefix configured -> nothing to filter.
            return sites_to_configure
        filtered = self._apply_exclude_prefix(sites_to_configure, MIST_SITE_EXCLUDE_PREFIX)  # WHY: prefix filter.
        self._log_exclusion_result(len(sites_to_configure), len(filtered))  # WHY: audit-log outcome.
        return filtered

    @staticmethod
    def _apply_exclude_prefix(sites: list[dict[str, Any]], prefix: str) -> list[dict[str, Any]]:
        """Return sites whose name does not start with the exclusion prefix."""
        return [site for site in sites if not site.get("name", "").startswith(prefix)]  # WHY: keep non-matching sites.

    @staticmethod
    def _log_exclusion_result(original_count: int, filtered_count: int) -> None:
        """Emit operator and log messages describing how many sites were excluded."""
        removed = original_count - filtered_count  # WHY: derive number of dropped sites.
        if removed > 0:  # WHY: only announce when something was excluded.
            print(
                f"\n  !? SECURITY: Excluded {removed} '{MIST_SITE_EXCLUDE_PREFIX}*' sites from configuration"
            )  # WHY: msg.
            logging.info(
                "Menu #149: Excluded %s sites matching prefix '%s'", removed, MIST_SITE_EXCLUDE_PREFIX
            )  # WHY: log.
        if filtered_count == 0:  # WHY: everything dropped -> abort message.
            print(
                f" No sites remaining after filtering '{MIST_SITE_EXCLUDE_PREFIX}*' sites."
            )  # WHY: operator feedback.
            logging.warning(
                "Menu #149: all selected sites matched exclude prefix '%s'", MIST_SITE_EXCLUDE_PREFIX
            )  # WHY: log.

    def _confirm_site_variable_operation(self, site_count: int) -> bool:
        """Confirm the site variable operation with user."""
        logging.info("Entering _confirm_site_variable_operation: %s sites pending", site_count)  # WHY: entry log.
        print(f"\n  Will configure {site_count} sites with wan2_interface variable.")  # WHY: operator summary.
        confirm = self._prompt_operator_confirmation()  # WHY: capture safe_input value.
        confirmed = confirm in CONFIRM_YES_TOKENS  # WHY: normalise into boolean gate.
        self._log_confirmation_result(confirmed, site_count)  # WHY: single-place logging + operator feedback.
        return confirmed

    @staticmethod
    def _prompt_operator_confirmation() -> str:
        """Prompt for yes/no confirmation and return normalized text."""
        return (  # WHY: safe_input with normalised casing/trim.
            InputUtils.safe_input(
                "\n  Proceed with setting site variables? (yes/no): ",
                context="wan2_site_variable_confirm",
            )
            .strip()
            .lower()
        )

    @staticmethod
    def _log_confirmation_result(confirmed: bool, site_count: int) -> None:
        """Emit both operator print and audit log lines for confirmation outcome."""
        if confirmed:  # WHY: log confirmation branch.
            logging.info("Exiting _confirm_site_variable_operation: confirmed for %s sites", site_count)  # WHY: audit.
            return
        print(" Operation cancelled.")  # WHY: cancel branch operator feedback.
        logging.info("Menu #149 cancelled by user at confirmation prompt")  # WHY: audit-log.
        logging.info("Exiting _confirm_site_variable_operation: result=cancelled")  # WHY: audit-log.

    def _build_override_detection_map(self) -> None:
        """Build map of sites with WAN2 port overrides for analysis."""
        self._load_gateway_configs()  # WHY: hydrate device-config rows.
        self._load_template_configs()  # WHY: hydrate template-config rows.
        self._build_site_to_template_mapping()  # WHY: derive site->template index.
        self._extract_template_port_configs()  # WHY: pre-compute per-template port IP.
        self._detect_device_overrides()  # WHY: populate per-site overrides map.

    def _load_gateway_configs(self) -> None:
        """Load gateway device configurations from CSV."""
        path = FilePathUtils.get_csv_path("AllSiteGatewayConfigs.csv")  # WHY: resolve cache location.
        with open(path, encoding="utf-8") as file_handle:  # WHY: read gateway cache.
            self.gateway_configs = list(csv.DictReader(file_handle))  # WHY: hydrate device configs.

    def _load_template_configs(self) -> None:
        """Load gateway template configurations from CSV."""
        path = FilePathUtils.get_csv_path("OrgGatewayTemplates.csv")  # WHY: resolve cache location.
        with open(path, encoding="utf-8") as file_handle:  # WHY: read template cache.
            self.template_data = list(csv.DictReader(file_handle))  # WHY: hydrate template configs.

    def _build_site_to_template_mapping(self) -> None:
        """Build mapping from site_id to gateway template_id."""
        for site in self.sites:  # WHY: iterate all sites to build lookup.
            site_id = site.get("id", "").strip()  # WHY: normalise site id.
            template_id = site.get("gatewaytemplate_id", "").strip()  # WHY: normalise template id.
            if site_id and template_id:  # WHY: only map when both fields present.
                self.site_to_template_id[site_id] = template_id  # WHY: record mapping.
        logging.info("Mapped %s sites to gateway templates", len(self.site_to_template_id))  # WHY: audit.

    def _extract_template_port_configs(self) -> None:
        """Extract IP configuration type from templates for ge-0/0/1 port."""
        for template_row in self.template_data:  # WHY: iterate all template rows.
            template_id = template_row.get("id", "").strip()  # WHY: normalise template id.
            if not template_id:  # WHY: skip malformed rows without ids.
                continue
            self.template_port_configs[template_id] = self._parse_template_ip_config(template_row)  # WHY: cache config.
        logging.info("Loaded port IP configs for %s templates", len(self.template_port_configs))  # WHY: audit.

    @staticmethod
    def _parse_template_ip_config(template_row: dict[str, Any]) -> dict[str, str]:
        """Parse IP configuration from template row."""
        raw = template_row.get("port_config_ge-0/0/1_ip_config", "").strip()  # WHY: fetch raw JSON payload.
        ip_type, ip_addr, netmask, gateway = _parse_json_ip_payload(raw)  # WHY: reuse shared parser.
        return {  # WHY: uniform dict shape expected by downstream code.
            "ip_type": ip_type or "not_configured",  # WHY: replace empty with sentinel.
            "ip": ip_addr,
            "netmask": netmask,
            "gateway": gateway,
        }

    def _detect_device_overrides(self) -> None:
        """Detect devices with WAN2 port overrides and classify severity."""
        for config_row in self.gateway_configs:  # WHY: iterate all device config rows.
            site_id = config_row.get("site_id", "").strip()  # WHY: normalise site id for grouping.
            device_name = config_row.get("name", "").strip()  # WHY: capture device name for report.
            override_info = self._analyze_device_override(config_row, site_id)  # WHY: classify override.
            if override_info is None:  # WHY: no meaningful override -> skip.
                continue
            self.site_overrides_map.setdefault(site_id, []).append(  # WHY: append per-site override record.
                {"device_name": device_name, **override_info}
            )

    def _analyze_device_override(self, config_row: dict[str, Any], site_id: str) -> dict[str, Any] | None:
        """Analyze a device config for WAN2 port overrides. Returns override info or None."""
        wan2_fields = self._get_wan2_override_fields(config_row)  # WHY: identify candidate columns.
        if not self._check_has_meaningful_override(config_row, wan2_fields):  # WHY: skip nullish/vpn-only rows.
            return None
        device_ip_info = self._extract_device_ip_config(config_row)  # WHY: capture device IP snapshot.
        template_ip_type = self._get_template_ip_type_for_site(  # WHY: template's IP expectation.
            site_id, device_ip_info.get("port_identifier", "")
        )
        context = OverrideAnalysisContext(  # WHY: bundle inputs for the record builder.
            site_id=site_id,
            device_name="",  # WHY: filled by caller before storage.
            device_ip=device_ip_info,
            template_ip_type=template_ip_type,
        )
        return self._build_override_record(context)  # WHY: single-place record shape assembly.

    @staticmethod
    def _build_override_record(context: OverrideAnalysisContext) -> dict[str, Any]:
        """Assemble a single override record from an analysis context."""
        device_ip_type = context.device_ip.get("ip_type", "")  # WHY: normalise before lookup.
        severity = WAN2MigrationManager._classify_override_severity(
            context.template_ip_type, device_ip_type
        )  # WHY: lookup.
        return {  # WHY: shape used by report data.
            "port_identifier": context.device_ip.get("port_identifier", BASE_PORT_IDENTIFIER),  # WHY: default port.
            "template_ip_type": context.template_ip_type.upper(),  # WHY: report expects uppercase.
            "device_ip_type": device_ip_type.upper() or "NOT_CONFIGURED",  # WHY: uppercase with sentinel.
            "device_static_ip": context.device_ip.get("ip", ""),  # WHY: static IP for report.
            "device_netmask": context.device_ip.get("netmask", ""),  # WHY: netmask for report.
            "device_gateway": context.device_ip.get("gateway", ""),  # WHY: gateway for report.
            "override_severity": severity,  # WHY: pre-computed severity token.
            "ip_type_conflict": severity in ("CRITICAL", "WARNING"),  # WHY: flag conflict rows.
        }

    @staticmethod
    def _get_wan2_override_fields(config_row: dict[str, Any]) -> list[str]:
        """Get list of WAN2-related port_config fields from config row."""
        return [col for col in config_row if _looks_like_wan2_field(col)]  # WHY: single-prefix predicate.

    @staticmethod
    def _check_has_meaningful_override(config_row: dict[str, Any], fields: list[str]) -> bool:
        """Check if config row has meaningful WAN2 overrides (excluding VPN paths)."""
        return any(  # WHY: any non-null / non-vpn field counts as an override.
            _is_meaningful_override_value(config_row.get(field, "")) for field in fields if VPN_MARKER not in field
        )

    def _extract_device_ip_config(self, config_row: dict[str, Any]) -> dict[str, str]:
        """Extract IP configuration from device config row."""
        subinterface_configs = self._find_subinterface_ip_configs(config_row)  # WHY: prefer subinterface data.
        if subinterface_configs:  # WHY: first subinterface wins when present.
            return subinterface_configs[0]
        return self._extract_base_port_ip_config(config_row)  # WHY: fall back to base port.

    def _find_subinterface_ip_configs(self, config_row: dict[str, Any]) -> list[dict[str, str]]:
        """Find and parse subinterface IP configurations."""
        return [  # WHY: single comprehension keeps complexity low.
            self._build_subif_config(config_row, col)
            for col in config_row
            if _looks_like_subif_type_field(col) and config_row.get(col, "").strip()
        ]

    @staticmethod
    def _build_subif_config(config_row: dict[str, Any], type_column: str) -> dict[str, str]:
        """Build a subinterface IP-config dictionary from a raw row."""
        subif_name = _subif_name_from_type_column(type_column)  # WHY: recover subif identifier.
        ip_base = f"port_config_{subif_name}_ip_config"  # WHY: prefix for related columns.
        return {  # WHY: uniform shape mirrored by base-port helper.
            "port_identifier": subif_name,
            "ip_type": config_row.get(type_column, "").strip().lower(),  # WHY: normalise casing.
            "ip": config_row.get(f"{ip_base}_ip", "").strip(),
            "netmask": config_row.get(f"{ip_base}_netmask", "").strip(),
            "gateway": config_row.get(f"{ip_base}_gateway", "").strip(),
        }

    @staticmethod
    def _extract_base_port_ip_config(config_row: dict[str, Any]) -> dict[str, str]:
        """Extract base port (ge-0/0/1) IP configuration from device config."""
        raw = config_row.get("port_config_ge-0/0/1_ip_config", "").strip()  # WHY: raw JSON payload.
        ip_type, ip_addr, netmask, gateway = _parse_json_ip_payload(raw)  # WHY: reuse shared parser.
        return {  # WHY: match subif dict shape.
            "port_identifier": BASE_PORT_IDENTIFIER,
            "ip_type": ip_type,
            "ip": ip_addr,
            "netmask": netmask,
            "gateway": gateway,
        }

    def _get_template_ip_type_for_site(self, site_id: str, port_identifier: str) -> str:
        """Get the template IP type for a site, checking subinterface if needed."""
        template_id = self.site_to_template_id.get(site_id, "")  # WHY: resolve template id.
        template_config = self.template_port_configs.get(template_id, {})  # WHY: cached parsed config.
        default_ip_type = template_config.get("ip_type", "unknown")  # WHY: base-port ip_type.
        if "." not in port_identifier:  # WHY: not a subinterface -> return base value.
            return default_ip_type
        return self._lookup_subif_template_ip_type(template_id, port_identifier, default_ip_type)  # WHY: subif lookup.

    def _lookup_subif_template_ip_type(self, template_id: str, port_identifier: str, default_ip_type: str) -> str:
        """Look up a subinterface IP type on the raw template row, falling back to the base value."""
        column = f"port_config_{port_identifier}_ip_config_type"  # WHY: subif type column name.
        for template_row in self.template_data:  # WHY: linear scan matches original behaviour.
            if template_row.get("id", "").strip() != template_id:  # WHY: skip non-matching rows.
                continue
            subif_type = template_row.get(column, "").strip().lower()  # WHY: normalise casing.
            return subif_type or default_ip_type  # WHY: fall back when missing.
        return default_ip_type  # WHY: template row not found -> use base default.

    @staticmethod
    def _classify_override_severity(template_ip_type: str, device_ip_type: str) -> str:
        """Classify override severity based on IP type mismatch."""
        return IP_TYPE_SEVERITY.get((template_ip_type, device_ip_type), "UNKNOWN")  # WHY: table lookup keeps CC low.

    def _process_sites_for_variable(self, sites_to_configure: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process each site to set the wan2_interface variable."""
        results: list[dict[str, Any]] = []  # WHY: accumulate per-site outcomes.
        print("\n  Processing sites...")  # WHY: operator progress cue.
        for site in tqdm(sites_to_configure, desc="Configuring sites", unit="site"):  # WHY: progress bar.
            if ConfigUtils.check_stop_signal():  # WHY: respect cooperative cancel signal.
                break
            results.append(self._set_variable_for_site(site))  # WHY: process each site individually.
        return results

    def _set_variable_for_site(self, site: dict[str, Any]) -> dict[str, Any]:
        """Set wan2_interface variable for a single site."""
        site_id = site.get("id", "")  # WHY: capture id for API + result.
        site_name = site.get("name", "Unnamed Site")  # WHY: friendly name for logs/report.
        result = self._initialize_site_result(site_id, site_name)  # WHY: build result skeleton.
        self._add_override_info_to_result(result, site_id)  # WHY: attach override metadata if any.
        try:  # WHY: outer guard around the API mutation.
            self._update_site_settings(site_id, site_name, result)
        except Exception as error:  # pylint: disable=broad-exception-caught  # WHY: capture any API error.
            result["status"] = "ERROR"  # WHY: mark result as errored.
            result["error"] = str(error)  # WHY: preserve human-readable message.
            logging.error("Error setting variable for site %s: %s", site_name, error)  # WHY: log summary.
            logging.error(traceback.format_exc())  # WHY: log formatted stack for debugging.
        return result

    @staticmethod
    def _initialize_site_result(site_id: str, site_name: str) -> dict[str, Any]:
        """Initialize result dictionary for a site."""
        return {  # WHY: canonical shape reused everywhere downstream.
            "site_id": site_id,
            "site_name": site_name,
            "variable_set": False,
            "has_overrides": False,
            "override_devices": [],
            "critical_override_count": 0,
            "warning_override_count": 0,
            "info_override_count": 0,
            "total_override_count": 0,
            "status": "",
            "error": "",
        }

    def _add_override_info_to_result(self, result: dict[str, Any], site_id: str) -> None:
        """Add override detection info to result dictionary."""
        override_details = self.site_overrides_map.get(site_id)  # WHY: fetch once, may be None.
        if not override_details:  # WHY: skip when no overrides recorded.
            return
        result["has_overrides"] = True  # WHY: mark presence flag.
        result["override_devices"] = [d["device_name"] for d in override_details]  # WHY: capture device names.
        counts = self._count_severity_buckets(override_details)  # WHY: single-pass severity tally.
        result["critical_override_count"] = counts["CRITICAL"]  # WHY: expose critical count.
        result["warning_override_count"] = counts["WARNING"]  # WHY: expose warning count.
        result["info_override_count"] = counts["INFO"]  # WHY: expose info count.
        result["total_override_count"] = len(override_details)  # WHY: expose total override count.
        result["override_details"] = self._format_override_details(override_details)  # WHY: attach formatted text.

    @staticmethod
    def _count_severity_buckets(override_details: list[dict[str, Any]]) -> dict[str, int]:
        """Count overrides grouped by severity bucket (CRITICAL/WARNING/INFO)."""
        buckets: dict[str, int] = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}  # WHY: initialise slots.
        for detail in override_details:  # WHY: linear pass tally per severity.
            severity = detail.get("override_severity", "")  # WHY: normalise missing values.
            if severity in buckets:  # WHY: ignore UNKNOWN and typos.
                buckets[severity] += 1
        return buckets

    def _format_override_details(self, override_details: list[dict[str, Any]]) -> str:
        """Format override details for CSV export."""
        return "; ".join(self._format_single_override(detail) for detail in override_details)  # WHY: concat summaries.

    @staticmethod
    def _format_single_override(detail: dict[str, Any]) -> str:
        """Return the compact string representation of a single override record."""
        device = detail["device_name"]  # WHY: header segment.
        port = detail.get("port_identifier", BASE_PORT_IDENTIFIER)  # WHY: port segment with fallback.
        severity = detail["override_severity"]  # WHY: severity segment.
        template_ip = detail["template_ip_type"]  # WHY: expected template IP type.
        device_ip = detail["device_ip_type"]  # WHY: observed device IP type.
        static_ip = detail["device_static_ip"]  # WHY: optional static IP value.
        netmask = detail["device_netmask"]  # WHY: optional netmask value.
        if static_ip and netmask:  # WHY: full-detail format when both known.
            return f"{device}@{port}({severity}:{template_ip}->{device_ip}:{static_ip}{netmask})"
        if static_ip:  # WHY: IP only when netmask missing.
            return f"{device}@{port}({severity}:{template_ip}->{device_ip}:{static_ip})"
        return f"{device}@{port}({severity}:{template_ip}->{device_ip})"  # WHY: fallback with types only.

    def _update_site_settings(self, site_id: str, site_name: str, result: dict[str, Any]) -> None:
        """Update site settings with wan2_interface variable."""
        current_settings = self._fetch_current_site_settings(site_id, site_name)  # WHY: pull existing settings.
        self._inject_wan2_variable(current_settings)  # WHY: mutate settings dict in place.
        self._apply_site_settings(site_id, site_name, current_settings, result)  # WHY: push to API + update result.

    @staticmethod
    def _fetch_current_site_settings(site_id: str, site_name: str) -> dict[str, Any]:
        """Fetch and normalise the current site settings dictionary."""
        logging.debug("Fetching current settings for site %s (%s)", site_name, site_id)  # WHY: debug log.
        settings_resp = mistapi.api.v1.sites.setting.getSiteSetting(apisession, site_id)  # WHY: pull from API.
        current_settings = settings_resp.data if hasattr(settings_resp, "data") else {}  # WHY: guard against SDK shape.
        return current_settings if isinstance(current_settings, dict) else {}  # WHY: normalise to dict.

    @staticmethod
    def _inject_wan2_variable(current_settings: dict[str, Any]) -> None:
        """Inject the wan2_interface variable into the settings dict (mutates in place)."""
        site_vars = current_settings.get("vars", {})  # WHY: fetch existing vars sub-dict.
        if not isinstance(site_vars, dict):  # WHY: normalise malformed vars payloads.
            site_vars = {}
        site_vars[WAN2_VARIABLE_NAME] = DEFAULT_WAN2_INTERFACE_VALUE  # WHY: assign canonical value.
        current_settings["vars"] = site_vars  # WHY: write back in case dict was replaced.

    @staticmethod
    def _apply_site_settings(
        site_id: str,
        site_name: str,
        current_settings: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        """Push updated site settings to the API and record outcome in result."""
        logging.debug("Updating site settings for %s with wan2_interface variable", site_name)  # WHY: pre-call log.
        update_resp = mistapi.api.v1.sites.setting.updateSiteSettings(
            apisession, site_id, body=current_settings
        )  # WHY: PUT.
        if update_resp.status_code == HTTP_OK:  # WHY: success branch.
            result["variable_set"] = True  # WHY: mark applied flag.
            result["status"] = "SUCCESS"  # WHY: expose success token.
            logging.info("Successfully set wan2_interface variable for site %s", site_name)  # WHY: audit log.
            return
        result["status"] = "FAILED"  # WHY: expose failure token.
        result["error"] = f"API returned status {update_resp.status_code}"  # WHY: capture status text.
        logging.error("Failed to set variable for site %s: status %s", site_name, update_resp.status_code)  # WHY: log.

    def _generate_site_variable_report(self, results: list[dict[str, Any]]) -> None:
        """Generate and save the site variable report."""
        report_data = self._build_report_data(results)  # WHY: shape rows for DataExporter.
        output_file = "WAN2_SiteVariable_Report.csv"  # WHY: fixed report filename per Menu #149 spec.
        DataExporter.write_with_format_selection(report_data, output_file)  # WHY: persist to disk.
        self._print_site_variable_summary(results, output_file)  # WHY: emit summary block to operator.

    def _build_report_data(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Build report data from results."""
        return [self._build_report_row(result) for result in results]  # WHY: one row per result.

    @staticmethod
    def _classify_manual_review(result: dict[str, Any]) -> str:
        """Return the manual-review classification token for a result row."""
        if result.get("critical_override_count", 0) > 0:  # WHY: critical always wins.
            return "CRITICAL"
        if result.get("warning_override_count", 0) > 0:  # WHY: warning ranks above info.
            return "WARNING"
        if result.get("info_override_count", 0) > 0:  # WHY: info is lowest positive class.
            return "INFO"
        return "No"  # WHY: no overrides -> no manual review needed.

    @classmethod
    def _build_report_row(cls, result: dict[str, Any]) -> dict[str, Any]:
        """Build a single report-data row from a per-site result record."""
        return {  # WHY: preserve legacy column order for downstream consumers.
            "site_name": result["site_name"],
            "site_id": result["site_id"],
            "wan2_variable_set": "Yes" if result["variable_set"] else "No",  # WHY: friendly boolean text.
            "status": result["status"],
            "has_wan2_overrides": "Yes" if result["has_overrides"] else "No",  # WHY: friendly boolean text.
            "total_override_count": result.get("total_override_count", 0),
            "critical_override_count": result.get("critical_override_count", 0),
            "warning_override_count": result.get("warning_override_count", 0),
            "info_override_count": result.get("info_override_count", 0),
            "override_devices": (
                ", ".join(result["override_devices"]) if result["override_devices"] else ""
            ),  # WHY: join.
            "override_details": result.get("override_details", ""),
            "requires_manual_review": cls._classify_manual_review(result),  # WHY: precomputed classification.
            "error": result["error"],
        }

    @staticmethod
    def _is_info_only_override(result: dict[str, Any]) -> bool:
        """Return True when a result has overrides but no critical or warning ones."""
        if not result.get("has_overrides"):  # WHY: no overrides -> not info-only.
            return False
        if result.get("critical_override_count", 0) > 0:  # WHY: any critical excludes info-only.
            return False
        return result.get("warning_override_count", 0) == 0  # WHY: last check -> warning-free means info-only.

    @staticmethod
    def _count_override_severities(results: list[dict[str, Any]]) -> dict[str, int]:  # WHY: tally severities.
        """Count override sites by severity bucket (override/critical/warning/info)."""
        counters = {"override": 0, "critical": 0, "warning": 0, "info": 0}  # WHY: initial slots.
        for record in results:  # WHY: linear pass keeps CC minimal.
            WAN2MigrationManager._accumulate_severity(record, counters)  # WHY: delegate branching to helper.
        return counters  # WHY: return finalised tallies.

    @staticmethod
    def _accumulate_severity(record: dict[str, Any], counters: dict[str, int]) -> None:  # WHY: single-record tally.
        """Increment severity counters for a single result record (mutates counters)."""
        if record.get("has_overrides"):  # WHY: presence flag captured once per record.
            counters["override"] += 1  # WHY: bump aggregate override tally.
        counters["critical"] += 1 if record.get("critical_override_count", 0) > 0 else 0  # WHY: CRITICAL count.
        counters["warning"] += 1 if record.get("warning_override_count", 0) > 0 else 0  # WHY: WARNING count.
        counters["info"] += 1 if WAN2MigrationManager._is_info_only_override(record) else 0  # WHY: INFO-only count.

    def _compute_severity_counts(self, results: list[dict[str, Any]]) -> dict[str, int]:
        """Compute per-severity site counts from per-site result records."""
        logging.debug("Computing severity counts from %d result records", len(results))  # WHY: pre-scan debug log.
        success_count = sum(1 for r in results if r["variable_set"])  # WHY: sites where variable was set.
        severity = self._count_override_severities(results)  # WHY: single-pass override tallies.
        return {"success": success_count, **severity}  # WHY: merge success into severity dict.

    @staticmethod
    def _print_summary_block(results: list[dict[str, Any]], counts: dict[str, int], output_file: str) -> None:
        """Print the human-readable summary block for the site-variable operation."""
        print("\n  Configuration Complete!")  # WHY: legacy completion banner.
        print("=" * 70)  # WHY: legacy divider.
        print(f"  Sites Processed: {len(results)}")  # WHY: legacy total-sites line.
        print(f"  Variables Set: {counts['success']}")  # WHY: legacy variables-set line.
        print(f"  Sites with WAN2 Overrides: {counts['override']}")  # WHY: legacy override-total line.
        print(f"    -> CRITICAL (DHCP->Static IP conflicts): {counts['critical']}")  # WHY: legacy CRITICAL line.
        print(f"    -> WARNING (Static->DHCP conflicts): {counts['warning']}")  # WHY: legacy WARNING line.
        print(f"    -> INFO (Same IP type, other overrides): {counts['info']}")  # WHY: legacy INFO line.
        print(f"\n  Report saved to: {output_file}")  # WHY: legacy report-location line.
        print("=" * 70)  # WHY: legacy trailing divider.

    def _print_site_variable_summary(self, results: list[dict[str, Any]], output_file: str) -> None:
        """Print summary of site variable operation."""
        counts = self._compute_severity_counts(results)  # WHY: single-pass counters for the block.
        self._print_summary_block(results, counts, output_file)  # WHY: render the summary block.
        self._print_severity_warnings(
            counts["critical"], counts["warning"], counts["info"]
        )  # WHY: contextual warnings.
        logging.info("Menu #149 complete: %s/%s sites configured", counts["success"], len(results))  # WHY: audit-log.
        logging.info(  # WHY: audit-log severity breakdown.
            "Override breakdown - CRITICAL: %s, WARNING: %s, INFO: %s",
            counts["critical"],
            counts["warning"],
            counts["info"],
        )

    @staticmethod
    def _print_severity_warnings(critical_sites: int, warning_sites: int, info_sites: int) -> None:
        """Print severity-specific warnings."""
        if critical_sites > 0:  # WHY: emit critical guidance block when applicable.
            print(f"\n  !? CRITICAL ATTENTION: {critical_sites} sites have DHCP->Static IP conflicts")  # WHY: banner.
            print("  Template specifies DHCP but devices use locally unique static IPs")  # WHY: describe conflict.
            print("  These MUST be manually reviewed before template migration (Menu #163)")  # WHY: guidance line 1.
            print("  Static IPs will be lost if template DHCP is applied without device overrides")  # WHY: guidance 2.
            print("  Check 'override_details' column for device names and static IP addresses")  # WHY: guidance 3.
        if warning_sites > 0:  # WHY: emit warning guidance block when applicable.
            print(f"\n  ! WARNING: {warning_sites} sites have Static->DHCP conflicts")  # WHY: banner.
            print("  Template specifies Static IP but devices configured for DHCP")  # WHY: describe conflict.
            print("  Review recommended before template migration")  # WHY: guidance.
        if info_sites > 0:  # WHY: emit info guidance block when applicable.
            print(f"\n  INFO: {info_sites} sites have same-IP-type overrides (likely safe)")  # WHY: banner.
            print("  Template and device use same IP configuration type (both DHCP or both Static)")  # WHY: describe.
            print("  Overrides may be for description, usage, or other non-critical fields")  # WHY: guidance.
