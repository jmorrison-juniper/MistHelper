"""Site inventory health analyzer extracted from MistHelper.py."""  # WHY: module docstring anchor

from __future__ import annotations  # WHY: enable PEP 563 postponed evaluation for type hints

import logging  # WHY: structured logging for analyzer progress/failures
from dataclasses import dataclass  # WHY: frozen slotted deps container
from datetime import datetime  # WHY: timestamp for CSV export filenames
from typing import Any  # WHY: generic hints for opaque mistapi payloads

_TYPE_TO_BUCKET: dict[str, str] = {  # WHY: raw mistapi device.type -> per-site bucket key
    "ap": "aps",
    "switch": "switches",
    "gateway": "gateways",
}
_EMPTY_BUCKETS: dict[str, list[dict[str, Any]]] = {  # WHY: template for lazy per-site bucket init
    "aps": [],
    "switches": [],
    "gateways": [],
}
_PREVIEW_LIMIT: int = 5  # WHY: max sample sites/APs shown in console output and report rows
_DETAIL_TRUNC: int = 80  # WHY: char cap for offline-devices label in preview lines


@dataclass(frozen=True, slots=True)  # WHY: immutable dep bundle, slots saves memory
class SiteInventoryHealthAnalyzerDeps:  # WHY: DI container reduces per-call param count
    """Dependency container for SiteInventoryHealthAnalyzer execution."""

    apisession: Any  # WHY: live mistapi session token for API calls
    mistapi: Any  # WHY: mistapi module handle (dependency-injected for tests)
    get_org_id_fn: Any  # WHY: callable returning currently-selected org id
    all_sites_fn: Any  # WHY: callable that lists all sites in an org
    save_data_fn: Any  # WHY: callable that writes report rows to a CSV file


@dataclass(frozen=True, slots=True)  # WHY: immutable export spec bundles filename+labels
class _ExportSpec:  # WHY: shrinks _export_report signature to <= 5 params
    """Parameters describing a single CSV export target."""

    filename: str  # WHY: output CSV filename with timestamp
    api_function_name: str  # WHY: passed through to save_data_fn for provenance
    label: str  # WHY: human-friendly report title used in the confirmation line
    empty_message: str  # WHY: printed instead of writing when the report has no rows


class SiteInventoryHealthAnalyzer:  # WHY: namespace for the analyzer entry point + helpers
    """Analyzes site inventory health to identify gaps and offline devices."""

    @staticmethod
    def analyze(deps: SiteInventoryHealthAnalyzerDeps) -> None:  # WHY: main entry point orchestrator
        """Main entry point for site inventory health analysis."""
        SiteInventoryHealthAnalyzer._print_header()  # WHY: banner + start log
        org_id = deps.get_org_id_fn()  # WHY: resolve current org id from harness state
        if not org_id:  # WHY: bail early when no org is selected
            print("! No organization selected. Exiting.")  # WHY: user-facing exit reason
            return  # WHY: nothing to analyze without an org
        site_inventory, site_lookup = SiteInventoryHealthAnalyzer._collect_inventory(org_id, deps)  # WHY: fetch+group
        if site_inventory is None:  # WHY: fetch failed → abort with user-facing hint
            print("! Failed to fetch required data. Please verify API access.")  # WHY: guide operator
            return  # WHY: cannot proceed without inventory
        missing_report = SiteInventoryHealthAnalyzer._find_sites_missing_infrastructure(  # WHY: gap analysis
            site_inventory, site_lookup
        )
        offline_report = SiteInventoryHealthAnalyzer._find_sites_with_offline_infrastructure(  # WHY: offline analysis
            site_inventory, site_lookup
        )
        SiteInventoryHealthAnalyzer._display_results(missing_report, offline_report)  # WHY: console rendering
        SiteInventoryHealthAnalyzer._export_results(missing_report, offline_report, deps)  # WHY: CSV export
        logging.info("Site inventory health analysis complete.")  # WHY: completion audit trail

    @staticmethod
    def _print_header() -> None:  # WHY: extracted header block keeps analyze under length cap
        """Emit banner and start log."""
        print("Site Inventory Health Analyzer:")  # WHY: user-facing title
        print("=" * 60)  # WHY: visual separator
        logging.info("Starting site inventory health analysis...")  # WHY: audit trail entry

    @staticmethod
    def _collect_inventory(  # WHY: extracts fetch+group so analyze stays short and flat
        org_id: str, deps: SiteInventoryHealthAnalyzerDeps
    ) -> tuple[dict[str, dict[str, Any]] | None, dict[str, str]]:
        """Fetch sites+devices, then group devices by site. Returns (None, {}) on fetch failure."""
        sites_data = SiteInventoryHealthAnalyzer._fetch_sites(org_id, deps)  # WHY: pull all sites in org
        devices_data = SiteInventoryHealthAnalyzer._fetch_devices(org_id, deps)  # WHY: pull inventory
        if not sites_data or not devices_data:  # WHY: analyzer requires both datasets to be meaningful
            return None, {}  # WHY: sentinel signals fetch failure to caller
        site_lookup = {  # WHY: id → friendly-name map for report display
            site.get("id"): site.get("name", "Unnamed Site") for site in sites_data
        }
        site_inventory = SiteInventoryHealthAnalyzer._group_devices_by_site(devices_data)  # WHY: bucket devices
        return site_inventory, site_lookup  # WHY: hand both structures back to analyze()

    @staticmethod
    def _fetch_sites(org_id: str, deps: SiteInventoryHealthAnalyzerDeps) -> list[dict[str, Any]]:  # WHY: sites list
        """Fetch all sites in the organization."""
        print("! Fetching sites...")  # WHY: user progress message
        logging.info("Fetching all organization sites...")  # WHY: pre-action log
        try:
            sites = deps.all_sites_fn(org_id)  # WHY: injected fetcher for testability
            print(f"  Found {len(sites)} sites")  # WHY: user-facing count confirmation
            return sites  # WHY: hand off list to caller for grouping
        except Exception as error:  # noqa: BLE001 - Mist SDK raises bare Exception subclasses
            logging.error("Failed to fetch sites: %s", error)  # WHY: capture root cause for support
            return []  # WHY: empty list triggers downstream fetch-failure path

    @staticmethod
    def _fetch_devices(org_id: str, deps: SiteInventoryHealthAnalyzerDeps) -> list[dict[str, Any]]:  # WHY: devices
        """Fetch all devices (inventory) in the organization."""
        print("! Fetching device inventory...")  # WHY: user progress message
        logging.info("Fetching all organization devices from inventory...")  # WHY: pre-action log
        try:
            response = deps.mistapi.api.v1.orgs.inventory.getOrgInventory(  # WHY: first page of inventory
                deps.apisession, org_id, limit=1000
            )
            devices = deps.mistapi.get_all(response=response, mist_session=deps.apisession) or []  # WHY: paginate
            logging.debug("Fetched %d devices from organization inventory", len(devices))  # WHY: post-action log
            SiteInventoryHealthAnalyzer._print_device_summary(devices)  # WHY: type/connected breakdown
            return devices  # WHY: hand off list to caller for grouping
        except Exception as error:  # noqa: BLE001 - Mist SDK raises bare Exception subclasses
            logging.error("Failed to fetch devices: %s", error)  # WHY: capture root cause for support
            return []  # WHY: empty list triggers downstream fetch-failure path

    @staticmethod
    def _print_device_summary(devices: list[dict[str, Any]]) -> None:  # WHY: one-line breakdown helper
        """Print a one-line summary of device counts by type plus connected total."""
        counts = {"ap": 0, "switch": 0, "gateway": 0, "connected": 0}  # WHY: accumulator for tally below
        for device in devices:  # WHY: single pass over device list
            device_type = device.get("type")  # WHY: categorise by mistapi type field
            if device_type in counts:  # WHY: bump per-type counter when known
                counts[device_type] += 1  # WHY: increment matched-type slot
            if device.get("connected") is True:  # WHY: connected counter independent of type
                counts["connected"] += 1
        print(  # WHY: user-facing summary line
            f"  Found {len(devices)} devices: {counts['ap']} APs, {counts['switch']} switches, "
            f"{counts['gateway']} gateways ({counts['connected']} connected)"
        )

    @staticmethod
    def _group_devices_by_site(devices: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:  # WHY: bucket by site
        """Group devices by site_id and categorize by type."""
        site_inventory: dict[str, dict[str, Any]] = {}  # WHY: site_id -> {aps:[], switches:[], gateways:[]}
        for device in devices:  # WHY: walk every device record once
            site_id = device.get("site_id", "")  # WHY: devices without site_id are unassigned — skip
            if not site_id:
                continue
            bucket_key = _TYPE_TO_BUCKET.get(device.get("type", ""))  # WHY: type → bucket name via table
            if bucket_key is None:  # WHY: unknown/unsupported device type — skip
                continue
            buckets = site_inventory.setdefault(  # WHY: lazily create the per-site bucket dict
                site_id, {"aps": [], "switches": [], "gateways": []}
            )
            buckets[bucket_key].append(SiteInventoryHealthAnalyzer._build_device_info(device))  # WHY: append
        return site_inventory

    @staticmethod
    def _build_device_info(device: dict[str, Any]) -> dict[str, Any]:  # WHY: project raw device into report row
        """Project a raw device record into our internal info dict (name/model/status)."""
        device_id = device.get("id", "")  # WHY: mist device UUID
        device_mac = device.get("mac", "")  # WHY: MAC address (fallback name source)
        return {
            "id": device_id,
            "mac": device_mac,
            "name": device.get("name", device_mac or device_id or "Unknown"),  # WHY: best-available name
            "model": device.get("model", "Unknown"),
            "serial": device.get("serial", "Unknown"),
            "status": SiteInventoryHealthAnalyzer._derive_status(device.get("connected")),  # WHY: 3-state label
        }

    @staticmethod
    def _derive_status(connected: Any) -> str:  # WHY: pure 3-state mapper
        """Translate the raw ``connected`` flag into a 3-state status string."""
        if connected is True:  # WHY: explicit boolean True → connected
            return "connected"
        if connected is False:  # WHY: explicit boolean False → disconnected
            return "disconnected"
        return "unknown"  # WHY: None / missing → unknown

    @staticmethod
    def _find_sites_missing_infrastructure(  # WHY: sites with APs but missing switch/gateway
        site_inventory: dict[str, dict[str, Any]], site_lookup: dict[str, str]
    ) -> list[dict[str, Any]]:
        """Find sites that have APs but are missing switches or gateways."""
        rows: list[dict[str, Any]] = []  # WHY: accumulator for qualifying site rows
        for site_id, inventory in site_inventory.items():  # WHY: evaluate each site independently
            row = SiteInventoryHealthAnalyzer._build_missing_row(site_id, inventory, site_lookup)  # WHY: per-site
            if row is not None:  # WHY: append only qualifying sites
                rows.append(row)
        return sorted(rows, key=lambda r: r["site_name"])  # WHY: stable display order

    @staticmethod
    def _build_missing_row(  # WHY: per-site row builder keeps outer loop simple + low CC
        site_id: str, inventory: dict[str, Any], site_lookup: dict[str, str]
    ) -> dict[str, Any] | None:
        """Return report row when the site has APs and is missing switch/gateway, else None."""
        ap_count = len(inventory["aps"])  # WHY: AP presence is the trigger for this report
        if ap_count == 0:  # WHY: no APs → not interesting
            return None
        switch_count = len(inventory["switches"])  # WHY: bucket size drives missing flag
        gateway_count = len(inventory["gateways"])  # WHY: bucket size drives missing flag
        missing_types = SiteInventoryHealthAnalyzer._collect_missing_types(switch_count, gateway_count)  # WHY: labels
        if not missing_types:  # WHY: everything present → skip site
            return None
        return {
            "site_id": site_id,
            "site_name": site_lookup.get(site_id, "Unknown Site"),  # WHY: friendly name fallback
            "ap_count": ap_count,
            "switch_count": switch_count,
            "gateway_count": gateway_count,
            "missing_types": ", ".join(missing_types),  # WHY: CSV-friendly joined label
            "ap_names": SiteInventoryHealthAnalyzer._format_ap_names(inventory["aps"], ap_count),  # WHY: sample
        }

    @staticmethod
    def _collect_missing_types(switch_count: int, gateway_count: int) -> list[str]:  # WHY: flat label collector
        """Return list of missing infrastructure type labels for a site."""
        missing: list[str] = []  # WHY: preserve insertion order for stable output
        if switch_count == 0:  # WHY: zero switches means switch tier is missing
            missing.append("switch")
        if gateway_count == 0:  # WHY: zero gateways means gateway tier is missing
            missing.append("gateway")
        return missing

    @staticmethod
    def _format_ap_names(aps: list[dict[str, Any]], ap_count: int) -> str:  # WHY: bounded sample formatter
        """Return preview of AP names capped at ``_PREVIEW_LIMIT`` with ellipsis when truncated."""
        joined = ", ".join(ap["name"] for ap in aps[:_PREVIEW_LIMIT])  # WHY: first-N preview
        suffix = "..." if ap_count > _PREVIEW_LIMIT else ""  # WHY: signal truncation to reader
        return joined + suffix

    @staticmethod
    def _find_sites_with_offline_infrastructure(  # WHY: sites with APs where switch/GW is offline
        site_inventory: dict[str, dict[str, Any]], site_lookup: dict[str, str]
    ) -> list[dict[str, Any]]:
        """Find sites with APs where switch or gateway is offline."""
        offline_sites: list[dict[str, Any]] = []  # WHY: accumulator for matching site reports
        for site_id, inventory in site_inventory.items():  # WHY: one pass over every site
            entry = SiteInventoryHealthAnalyzer._build_offline_entry(site_id, site_lookup, inventory)
            if entry is not None:  # WHY: append only when this site qualifies
                offline_sites.append(entry)
        return sorted(offline_sites, key=lambda row: row["site_name"])  # WHY: stable display order

    @staticmethod
    def _build_offline_entry(  # WHY: per-site offline row builder
        site_id: str, site_lookup: dict[str, str], inventory: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Build a per-site offline-infrastructure report row, or None when not applicable."""
        ap_count = len(inventory["aps"])  # WHY: APs are the trigger for this report
        if ap_count == 0:  # WHY: no APs → site not interesting for this report
            return None
        offline_switches = SiteInventoryHealthAnalyzer._filter_disconnected(inventory["switches"])  # WHY: bad SW
        offline_gateways = SiteInventoryHealthAnalyzer._filter_disconnected(inventory["gateways"])  # WHY: bad GW
        if not (offline_switches or offline_gateways):  # WHY: nothing offline → skip
            return None
        return SiteInventoryHealthAnalyzer._compose_offline_row(  # WHY: build final report dict
            site_id, site_lookup, inventory, offline_switches, offline_gateways
        )

    @staticmethod
    def _compose_offline_row(  # WHY: pure builder isolates dict shape from control flow
        site_id: str,
        site_lookup: dict[str, str],
        inventory: dict[str, Any],
        offline_switches: list[dict[str, Any]],
        offline_gateways: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Compose the offline-infrastructure report row for a single site."""
        offline_details = SiteInventoryHealthAnalyzer._format_offline_details(  # WHY: pretty labels
            offline_switches, offline_gateways
        )
        return {
            "site_id": site_id,
            "site_name": site_lookup.get(site_id, "Unknown Site"),  # WHY: friendly name fallback
            "ap_count": len(inventory["aps"]),  # WHY: recomputed here to keep signature <= 5 params
            "total_switches": len(inventory["switches"]),
            "offline_switches": len(offline_switches),
            "total_gateways": len(inventory["gateways"]),
            "offline_gateways": len(offline_gateways),
            "offline_devices": "; ".join(offline_details),  # WHY: semi-colon list for CSV
            "offline_switch_names": ", ".join(s["name"] for s in offline_switches),
            "offline_gateway_names": ", ".join(g["name"] for g in offline_gateways),
        }

    @staticmethod
    def _filter_disconnected(devices: list[dict[str, Any]]) -> list[dict[str, Any]]:  # WHY: predicate filter
        """Return the subset of devices whose status is ``disconnected``."""
        return [device for device in devices if device["status"] == "disconnected"]

    @staticmethod
    def _format_offline_details(  # WHY: label formatter shared by row builder
        offline_switches: list[dict[str, Any]], offline_gateways: list[dict[str, Any]]
    ) -> list[str]:
        """Format ``Switch: name (model)`` / ``Gateway: name (model)`` labels for the report."""
        switch_labels = [f"Switch: {s['name']} ({s['model']})" for s in offline_switches]  # WHY: SW rows
        gateway_labels = [f"Gateway: {g['name']} ({g['model']})" for g in offline_gateways]  # WHY: GW rows
        return switch_labels + gateway_labels

    @staticmethod
    def _display_results(  # WHY: console rendering top-level
        missing_report: list[dict[str, Any]], offline_report: list[dict[str, Any]]
    ) -> None:
        """Display analysis results to console."""
        print("\n" + "=" * 60)  # WHY: banner separator
        print("ANALYSIS RESULTS")  # WHY: section title
        print("=" * 60)  # WHY: banner separator
        SiteInventoryHealthAnalyzer._display_missing_section(missing_report)  # WHY: missing block
        SiteInventoryHealthAnalyzer._display_offline_section(offline_report)  # WHY: offline block
        print("\n" + "=" * 60)  # WHY: trailing separator

    @staticmethod
    def _display_missing_section(missing_report: list[dict[str, Any]]) -> None:  # WHY: missing console block
        """Console block for sites missing switch/gateway infrastructure."""
        print("\n[SITES MISSING INFRASTRUCTURE]")  # WHY: section header
        print(f"  Sites with APs but missing switch/gateway: {len(missing_report)}")  # WHY: total line
        if not missing_report:  # WHY: nothing more to render when report is empty
            return
        SiteInventoryHealthAnalyzer._print_missing_totals(missing_report)  # WHY: per-type totals
        SiteInventoryHealthAnalyzer._print_missing_samples(missing_report)  # WHY: sample preview rows

    @staticmethod
    def _print_missing_totals(missing_report: list[dict[str, Any]]) -> None:  # WHY: per-type totals helper
        """Print aggregate counts of missing switches and gateways."""
        missing_switches = sum(1 for r in missing_report if "switch" in r["missing_types"])  # WHY: switch tally
        missing_gateways = sum(1 for r in missing_report if "gateway" in r["missing_types"])  # WHY: gateway tally
        print(f"    - Missing switches: {missing_switches}")
        print(f"    - Missing gateways: {missing_gateways}")

    @staticmethod
    def _print_missing_samples(missing_report: list[dict[str, Any]]) -> None:  # WHY: bounded preview helper
        """Print sample preview lines from the missing-infrastructure report."""
        print("\n  Sample sites (first 5):")  # WHY: preview header
        for site in missing_report[:_PREVIEW_LIMIT]:  # WHY: bounded preview
            print(f"    - {site['site_name']}: {site['ap_count']} APs, missing {site['missing_types']}")

    @staticmethod
    def _display_offline_section(offline_report: list[dict[str, Any]]) -> None:  # WHY: offline console block
        """Console block for sites with offline switch/gateway infrastructure."""
        print("\n[SITES WITH OFFLINE INFRASTRUCTURE]")  # WHY: section header
        print(f"  Sites with APs and offline switch/gateway: {len(offline_report)}")  # WHY: total line
        if not offline_report:  # WHY: nothing more to render when report is empty
            return
        SiteInventoryHealthAnalyzer._print_offline_totals(offline_report)  # WHY: per-type totals
        SiteInventoryHealthAnalyzer._print_offline_samples(offline_report)  # WHY: sample preview rows

    @staticmethod
    def _print_offline_totals(offline_report: list[dict[str, Any]]) -> None:  # WHY: per-type totals helper
        """Print aggregate counts of offline switches and gateways."""
        total_switches = sum(r["offline_switches"] for r in offline_report)  # WHY: switch tally
        total_gateways = sum(r["offline_gateways"] for r in offline_report)  # WHY: gateway tally
        print(f"    - Total offline switches: {total_switches}")
        print(f"    - Total offline gateways: {total_gateways}")

    @staticmethod
    def _print_offline_samples(offline_report: list[dict[str, Any]]) -> None:  # WHY: bounded preview helper
        """Print sample preview lines from the offline-infrastructure report."""
        print("\n  Sample sites (first 5):")  # WHY: preview header
        for site in offline_report[:_PREVIEW_LIMIT]:  # WHY: bounded preview
            label = site["offline_devices"]  # WHY: raw joined label
            suffix = "..." if len(label) > _DETAIL_TRUNC else ""  # WHY: truncate long strings
            print(f"    - {site['site_name']}: {site['ap_count']} APs, offline: {label[:_DETAIL_TRUNC]}{suffix}")

    @staticmethod
    def _export_results(  # WHY: CSV export orchestrator
        missing_report: list[dict[str, Any]],
        offline_report: list[dict[str, Any]],
        deps: SiteInventoryHealthAnalyzerDeps,
    ) -> None:
        """Export analysis results to CSV files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # WHY: filename-safe local timestamp
        missing_spec = _ExportSpec(  # WHY: bundle missing-report export parameters
            filename=f"SitesMissingInfrastructure_{timestamp}.csv",
            api_function_name="sitesMissingInfrastructure",
            label="Missing infrastructure",
            empty_message="! No sites found with missing infrastructure (all sites with APs have switches and gateways)",
        )
        offline_spec = _ExportSpec(  # WHY: bundle offline-report export parameters
            filename=f"SitesWithOfflineInfrastructure_{timestamp}.csv",
            api_function_name="sitesWithOfflineInfrastructure",
            label="Offline infrastructure",
            empty_message="! No sites found with offline infrastructure (all switches and gateways are online)",
        )
        SiteInventoryHealthAnalyzer._export_report(missing_report, deps, missing_spec)  # WHY: missing CSV
        SiteInventoryHealthAnalyzer._export_report(offline_report, deps, offline_spec)  # WHY: offline CSV

    @staticmethod
    def _export_report(  # WHY: single-report exporter reused for both CSVs
        rows: list[dict[str, Any]],
        deps: SiteInventoryHealthAnalyzerDeps,
        spec: _ExportSpec,
    ) -> None:
        """Export a single report to CSV or print the empty-message fallback."""
        if not rows:  # WHY: nothing to write → user hint instead
            print(spec.empty_message)
            return
        deps.save_data_fn(rows, spec.filename, api_function_name=spec.api_function_name)  # WHY: delegated write
        print(f"! {spec.label} report exported to {spec.filename}")  # WHY: user-facing confirmation
        logging.info("Exported %d sites to %s", len(rows), spec.filename)  # WHY: audit trail
