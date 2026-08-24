"""Site configuration manager extracted from MistHelper menu 171-174 flows."""

from __future__ import annotations  # WHY: enable PEP 604 union syntax across Python 3.9+.

import csv  # WHY: parse CSV rows into per-site payload dicts.
import logging  # WHY: emit structured audit trail for destructive ops.
import os  # WHY: verify CSV presence before opening.
from dataclasses import dataclass, field  # WHY: group callable dependencies into typed containers.
from typing import Any  # WHY: dependencies are duck-typed injection surfaces.

from src.utils.rate_limiting import AdaptivePacer  # WHY: quota-aware pacing replaces the fixed sleep calls.

# --- Module-level dependency container (populated by configure_...) ---------


@dataclass
class SiteConfigDependencies:  # WHY: typed container consumed by every helper via _deps().
    """Holds injected collaborators so callers pass one object rather than seven."""

    apisession: Any = None  # WHY: authenticated mistapi session for all requests.
    config_utils: Any = None  # WHY: provides org id caching + stop-signal check.
    file_path_utils: Any = None  # WHY: resolves CSV paths portably across OS.
    input_utils: Any = None  # WHY: gated safe_input for destructive confirmations.
    data_exporter: Any = None  # WHY: exports run reports in operator-chosen format.
    mistapi: Any = None  # WHY: root SDK module used for both calls and pagination.
    default_api_page_limit: int = 1000  # WHY: paginate wide list endpoints in one call when possible.
    api_usage_cache: dict[str, Any] | None = None  # WHY: shared quota view for the adaptive rate limiter.


def _pacer(enabled: bool = True) -> AdaptivePacer:  # WHY: one builder keeps every bulk loop on the same quota view.
    """Return a pacer bound to the live session and the shared API usage cache."""
    deps = _deps()  # WHY: read the wired collaborators one time per loop.
    return AdaptivePacer(deps.apisession, deps.api_usage_cache, enabled)  # WHY: PID pacing replaces a fixed sleep.


_DEPS: SiteConfigDependencies = SiteConfigDependencies()  # WHY: single shared holder mutated at wire-up.


def _deps() -> SiteConfigDependencies:  # WHY: single accessor used by every helper.
    """Return the active dependency container so helpers can pull collaborators."""
    return _DEPS  # WHY: indirection keeps tests able to swap the whole graph atomically.


@dataclass
class RfTemplateReport:  # WHY: pack 6 report inputs into one arg to satisfy limit.
    """Bundles RF-template outcome lists for a single result-report call."""

    created: list[dict[str, Any]] = field(default_factory=list)  # WHY: templates newly created this run.
    updated: list[dict[str, Any]] = field(default_factory=list)  # WHY: templates already present (or updated).
    update_mode: str = "skip"  # WHY: "update" vs "skip" changes displayed label.
    success: list[dict[str, Any]] = field(default_factory=list)  # WHY: sites successfully re-templated.
    failed: list[dict[str, Any]] = field(default_factory=list)  # WHY: sites that failed template assignment.
    skipped: list[dict[str, Any]] = field(default_factory=list)  # WHY: sites without a country code.


def configure_site_config_manager_dependencies(deps: SiteConfigDependencies) -> None:  # WHY: single wire-up entry.
    """Wire runtime collaborators from the MistHelper orchestration layer."""
    global _DEPS  # WHY: rebind the module-level holder used by every helper.
    _DEPS = deps  # WHY: single assignment ensures atomic swap of collaborators.


class SiteConfigManager:  # WHY: umbrella namespace for the four menu entrypoints.
    """Bulk site config workflows: test site creation, RF templates, device profiles.

    All destructive operations require explicit user confirmation.
    """

    # -------------------------------------------------------------------------
    # Test Site Creation (Menu 171)
    # -------------------------------------------------------------------------
    @staticmethod
    def create_test_sites_from_csv() -> None:  # WHY: menu 171 destructive workflow entrypoint.
        """Create test sites from NorthAmericanTestSites.csv (DESTRUCTIVE)."""
        logging.warning("Menu #171 DESTRUCTIVE: Create test sites from CSV operation started")  # WHY: audit start.
        SiteConfigManager._display_test_sites_header()  # WHY: show scope to operator before prompt.
        if not SiteConfigManager._confirm_test_site_creation():  # WHY: bail if user did not type exact keyword.
            return  # WHY: user declined confirmation prompt.
        org_id = _deps().config_utils.get_cached_or_prompted_org_id()  # WHY: resolve target org before any work.
        if not org_id:  # WHY: without an org id nothing can be created safely.
            logging.error("No organization ID provided - cannot create sites")  # WHY: audit missing org id.
            print(" ERROR: No organization ID provided")  # WHY: operator-visible error line.
            return  # WHY: cannot proceed without org id.
        sites_data = SiteConfigManager._load_test_sites_csv()  # WHY: load rows once for both create + report.
        if not sites_data:  # WHY: skip execution when CSV missing/empty (helper printed reason).
            return  # WHY: no data means nothing to create.
        created, failed = SiteConfigManager._execute_site_creation(org_id, sites_data)  # WHY: run create loop.
        SiteConfigManager._report_site_creation_results(sites_data, created, failed)  # WHY: summarize + export.
        logging.warning(  # WHY: audit final tallies for later compliance review.
            "Menu #171 complete: %s sites created, %s failed", len(created), len(failed)
        )

    @staticmethod
    def _display_test_sites_header() -> None:  # WHY: static banner helper.
        """Display test site creation warning header."""
        print("\n========================================")  # WHY: visually delimit destructive banner.
        print(" DESTRUCTIVE OPERATION WARNING")  # WHY: primary warning line.
        print("========================================")  # WHY: banner divider.
        print(" This will CREATE 137 new test sites in your organization")  # WHY: state scope numerically.
        print(" Sites span 13 North American countries:")  # WHY: preview country list.
        print(" US, Canada, Mexico, Guatemala, Costa Rica, Panama,")  # WHY: country row 1.
        print(" Honduras, Belize, Bahamas, Cuba, Jamaica,")  # WHY: country row 2.
        print(" Dominican Republic, and Haiti")  # WHY: country row 3.
        print("========================================\n")  # WHY: close banner with trailing blank line.

    @staticmethod
    def _confirm_test_site_creation() -> bool:  # WHY: exact-keyword gate helper.
        """Return True only if operator typed the exact keyword CREATE."""
        confirmation = _deps().input_utils.safe_input(  # WHY: use gated input for auditable prompt.
            "Type 'CREATE' (uppercase) to proceed with site creation: ",
            context="site creation confirmation",
        )
        if confirmation != "CREATE":  # WHY: exact keyword match prevents accidental typos triggering ops.
            print(" Site creation cancelled - confirmation phrase not matched")  # WHY: inform operator.
            logging.info("Site creation cancelled by user")  # WHY: audit non-execution.
            return False  # WHY: signal decline to caller.
        return True  # WHY: signal proceed.

    @staticmethod
    def _load_test_sites_csv() -> list[dict[str, Any]] | None:  # WHY: CSV loader with narrow error typing.
        """Load test sites from CSV file returning None on error."""
        csv_file_path = _deps().file_path_utils.get_csv_path("NorthAmericanTestSites.csv")  # WHY: portable path.
        if not os.path.exists(csv_file_path):  # WHY: fail fast when data file is missing.
            logging.error("CSV file not found: %s", csv_file_path)  # WHY: audit missing file.
            print(f" ERROR: CSV file not found: {csv_file_path}")  # WHY: operator-visible error.
            return None  # WHY: signal missing-file failure to caller.
        try:
            with open(csv_file_path, encoding="utf-8") as csv_file:  # WHY: explicit utf-8 avoids locale issues.
                sites_data = list(csv.DictReader(csv_file))  # WHY: materialize rows for count + iteration.
            logging.info("Loaded %s sites from CSV file", len(sites_data))  # WHY: audit successful load.
            print(f"\n Loaded {len(sites_data)} sites from CSV file")  # WHY: operator feedback on scope.
            return sites_data  # WHY: hand parsed rows back to caller.
        except OSError as read_error:  # WHY: narrow to filesystem errors. Do not swallow programmer errors.
            logging.error("Failed to read CSV file: %s", read_error)  # WHY: audit read failure with detail.
            print(f" ERROR: Failed to read CSV file: {read_error}")  # WHY: surface reason to operator.
            return None  # WHY: signal read-failure to caller.

    @staticmethod
    def _copy_optional_fields(site_data: dict[str, Any], payload: dict[str, Any]) -> None:  # WHY: mutate helper.
        """Copy present, non-empty optional fields from CSV row into payload."""
        for key in ("address", "country_code", "timezone", "notes"):  # WHY: single source of truth for keys.
            value = site_data.get(key)  # WHY: fetch once. None + "" both mean absent.
            if value:  # WHY: only copy truthy values so we do not send blanks to API.
                payload[key] = value.strip()  # WHY: strip whitespace per API hygiene.

    @staticmethod
    def _extract_latlng(site_data: dict[str, Any]) -> dict[str, float] | None:  # WHY: coord parse helper.
        """Return {'lat', 'lng'} dict when both coordinates parse, else None."""
        lat_str = site_data.get("lat", "").strip()  # WHY: normalize whitespace before parsing.
        lng_str = site_data.get("lng", "").strip()  # WHY: normalize whitespace before parsing.
        if not (lat_str and lng_str):  # WHY: require both to form a valid coordinate pair.
            return None  # WHY: skip when either coord is absent.
        try:
            return {"lat": float(lat_str), "lng": float(lng_str)}  # WHY: numeric coercion matches API contract.
        except ValueError:  # WHY: silently skip malformed coords rather than fail whole site.
            return None  # WHY: unparseable coords are treated as absent.

    @staticmethod
    def _build_site_payload(site_data: dict[str, Any]) -> dict[str, Any] | None:  # WHY: payload builder.
        """Build API payload from a single site CSV row. None when name is missing."""
        site_name = site_data.get("name", "").strip()  # WHY: name is the only mandatory field.
        if not site_name:  # WHY: reject nameless rows so caller can record row-level failure.
            return None  # WHY: signal invalid row so caller can log failure.
        payload: dict[str, Any] = {"name": site_name}  # WHY: seed with the mandatory attribute.
        SiteConfigManager._copy_optional_fields(site_data, payload)  # WHY: attach non-empty optional attributes.
        latlng = SiteConfigManager._extract_latlng(site_data)  # WHY: coords are conditional on parse success.
        if latlng is not None:  # WHY: only attach when both coords parsed cleanly.
            payload["latlng"] = latlng  # WHY: attach parsed coordinate pair.
        return payload  # WHY: return fully-populated payload to caller.

    @staticmethod
    def _create_single_site(  # WHY: single-row create helper isolates try/except for readability.
        org_id: str,
        site_payload: dict[str, Any],
        index: int,
        total: int,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """Attempt to create one site and return (created_record, failed_record)."""
        site_name = site_payload["name"]  # WHY: cached for both records + operator line.
        try:
            deps = _deps()  # WHY: single lookup keeps this call block simple.
            response = deps.mistapi.api.v1.orgs.sites.createOrgSite(  # WHY: SDK path for create.
                deps.apisession, org_id, body=site_payload
            )
            if hasattr(response, "data") and response.data:  # WHY: guard against empty responses seen in prod.
                created_site_id = response.data.get("id", "unknown")  # WHY: fall back to sentinel when id missing.
                print(f" [{index}/{total}] Created: {site_name}")  # WHY: operator progress feedback.
                return ({"name": site_name, "id": created_site_id, "row": index}, None)  # WHY: success tuple.
            return (None, {"row": index, "name": site_name, "error": "No data"})  # WHY: record empty-response.
        except (RuntimeError, ValueError, OSError, KeyError) as create_error:  # WHY: broad but narrower than bare.
            logging.error("Failed to create site %s: %s", site_name, create_error)  # WHY: audit each failure.
            return (None, {"row": index, "name": site_name, "error": str(create_error)})  # WHY: failure tuple.

    @staticmethod
    def _execute_site_creation(  # WHY: orchestrator over per-row create helper.
        org_id: str, sites_data: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Execute site creation API calls. Returns (created, failed) lists."""
        created_sites: list[dict[str, Any]] = []  # WHY: collect successful records for later export.
        failed_sites: list[dict[str, Any]] = []  # WHY: collect failed records for later export.
        total = len(sites_data)  # WHY: cache for progress lines.
        pacer = _pacer()  # WHY: one pacer per loop carries the PID state across every create call.
        print(f"\n Creating sites in organization {org_id}...")  # WHY: operator visibility for long loop.
        for index, site_data in enumerate(sites_data, start=1):  # WHY: 1-based indices align with CSV rows.
            site_payload = SiteConfigManager._build_site_payload(site_data)  # WHY: shape payload for API.
            if not site_payload:  # WHY: nameless rows short-circuit to failure record.
                failed_sites.append({"row": index, "name": "MISSING", "error": "No site name"})  # WHY: log row.
                continue  # WHY: skip API call for invalid row.
            created, failed = SiteConfigManager._create_single_site(  # WHY: delegate to per-row helper.
                org_id, site_payload, index, total
            )
            if created:  # WHY: append to matching bucket without conditional wrapping.
                created_sites.append(created)  # WHY: capture success record.
            if failed:  # WHY: at most one of the two is non-None per call.
                failed_sites.append(failed)  # WHY: capture failure record.
            pacer.pace()  # WHY: quota-aware wait replaces the fixed sleep between site creates.
        return created_sites, failed_sites  # WHY: hand paired result buckets to caller.

    @staticmethod
    def _report_site_creation_results(  # WHY: post-run reporter kept as its own single-purpose helper.
        sites_data: list[dict[str, Any]],
        created: list[dict[str, Any]],
        failed: list[dict[str, Any]],
    ) -> None:
        """Report and export site creation results."""
        print("\n========================================")  # WHY: begin summary banner.
        print(" SITE CREATION SUMMARY")  # WHY: summary title.
        print("========================================")  # WHY: banner divider.
        print(f" Total sites in CSV: {len(sites_data)}")  # WHY: baseline count for operator.
        print(f" Successfully created: {len(created)}")  # WHY: success tally.
        print(f" Failed: {len(failed)}")  # WHY: failure tally.
        print("========================================\n")  # WHY: close banner.
        deps = _deps()  # WHY: reuse locally to avoid repeated getter calls.
        if created:  # WHY: only export non-empty datasets to keep artefacts clean.
            deps.data_exporter.write_with_format_selection(created, "CreatedTestSites.csv")  # WHY: export success.
            print(" Created sites exported to CreatedTestSites.csv")  # WHY: confirm export location.
        if failed:  # WHY: same rationale for failure export.
            deps.data_exporter.write_with_format_selection(failed, "FailedTestSites.csv")  # WHY: export failure.
            print(" Failed sites exported to FailedTestSites.csv")  # WHY: confirm export location.

    # -------------------------------------------------------------------------
    # RF Template Creation (Menu 172)
    # -------------------------------------------------------------------------
    @staticmethod
    def create_country_rf_templates_and_assign() -> None:  # WHY: Menu 172 top-level entry point.
        """Create country-specific RF templates and assign sites to them (DESTRUCTIVE)."""
        logging.warning("Menu #172 DESTRUCTIVE: Create country RF templates operation started")  # WHY: audit.
        SiteConfigManager._display_rf_template_header()  # WHY: banner before any work.
        if not _deps().apisession:  # WHY: guard against unwired dependency graph.
            logging.error("API session not initialized")  # WHY: audit unwired state.
            print(" ERROR: Mist API session not initialized")  # WHY: operator error line.
            return  # WHY: cannot proceed without a session.
        org_id = _deps().config_utils.get_cached_or_prompted_org_id()  # WHY: resolve target org id.
        if not org_id:  # WHY: bail without valid target.
            return  # WHY: no org means no target for template operations.
        SiteConfigManager._run_rf_template_workflow(org_id)  # WHY: single-responsibility inner runner.

    @staticmethod
    def _run_rf_template_workflow(org_id: str) -> None:  # WHY: workflow driver for Menu 172.
        """Drive the analyze/plan/confirm/execute/report sequence for RF templates."""
        analysis = SiteConfigManager._analyze_sites_for_rf_templates(org_id)  # WHY: gather data before planning.
        if not analysis:  # WHY: helper printed reason on failure.
            return  # WHY: cannot plan without analysis results.
        sites_by_country, sites_without_country, existing_templates = analysis  # WHY: unpack analysis triple.
        plan = SiteConfigManager._plan_rf_template_operations(sites_by_country, existing_templates)  # WHY: plan.
        if not plan:  # WHY: user cancelled inside planner.
            return  # WHY: honor user cancel before any writes.
        templates_to_create, templates_to_update, update_mode = plan  # WHY: unpack plan triple.
        if not SiteConfigManager._confirm_rf_template_operation(  # WHY: final destructive gate.
            templates_to_create, templates_to_update, sites_by_country, update_mode
        ):
            return  # WHY: bail without any writes when user does not confirm.
        SiteConfigManager._run_rf_template_execution(  # WHY: hand off to execution helper.
            org_id,
            (templates_to_create, templates_to_update, update_mode),
            sites_by_country,
            sites_without_country,
        )

    @staticmethod
    def _run_rf_template_execution(  # WHY: perform writes + reporting after user confirms.
        org_id: str,
        plan_triple: tuple[list[dict[str, Any]], list[dict[str, Any]], str],
        sites_by_country: dict[str, list[dict[str, Any]]],
        sites_without_country: list[dict[str, Any]],
    ) -> None:
        """Execute template ops, assign sites, emit report + audit log."""
        templates_to_create, templates_to_update, update_mode = plan_triple  # WHY: unpack plan triple.
        template_mapping = SiteConfigManager._execute_rf_template_operations(  # WHY: create/update templates.
            org_id, templates_to_create, templates_to_update, update_mode
        )
        success, failed = SiteConfigManager._assign_sites_to_rf_templates(  # WHY: attach sites to templates.
            sites_by_country, template_mapping
        )
        report = RfTemplateReport(  # WHY: single object keeps _report_ under param limit.
            created=templates_to_create,
            updated=templates_to_update,
            update_mode=update_mode,
            success=success,
            failed=failed,
            skipped=sites_without_country,
        )
        SiteConfigManager._report_rf_template_results(report)  # WHY: emit summary + exports.
        SiteConfigManager._audit_rf_template_completion(templates_to_create, success, failed)  # WHY: audit.

    @staticmethod
    def _audit_rf_template_completion(  # WHY: helper isolates final audit log block.
        created: list[dict[str, Any]],
        success: list[dict[str, Any]],
        failed: list[dict[str, Any]],
    ) -> None:
        """Log final tallies for the Menu 108 RF template workflow."""
        logging.warning(  # WHY: audit final tallies with elevated level so operators see summary.
            "Menu #172 complete: %s templates created, %s sites assigned, %s failed",
            len(created),
            len(success),
            len(failed),
        )

    @staticmethod
    def _display_rf_template_header() -> None:  # WHY: banner helper isolates presentation from logic.
        """Display RF template operation header."""
        print("\n" + "=" * 70)  # WHY: open header banner.
        print(" Menu 108: Create Country-Specific RF Templates and Assign")  # WHY: title line.
        print("=" * 70)  # WHY: close header banner.

    @staticmethod
    def _fetch_org_sites_for_rf(org_id: str) -> list[dict[str, Any]] | None:  # WHY: fetch helper with narrow errs.
        """Fetch all sites for an org, returning None on failure or empty result."""
        logging.info("Fetching org sites for RF-template analysis (org_id=%s)", org_id)  # WHY: audit start.
        try:
            deps = _deps()  # WHY: local reference keeps call chain readable.
            sites_response = deps.mistapi.api.v1.orgs.sites.listOrgSites(  # WHY: page-aware list of org sites.
                deps.apisession, org_id, limit=deps.default_api_page_limit
            )
            sites = deps.mistapi.get_all(response=sites_response, mist_session=deps.apisession)  # WHY: paginate.
        except (RuntimeError, ValueError, OSError, KeyError) as error:  # WHY: narrow exception set.
            logging.error("Failed to fetch sites: %s", error)  # WHY: audit failure.
            print(f" ERROR: Failed to fetch sites - {error}")  # WHY: operator visibility.
            return None  # WHY: propagate failure to caller.
        if not sites:  # WHY: no sites means nothing to template.
            print(" No sites found in organization.")  # WHY: legacy message preserved.
            return None  # WHY: nothing to do without any sites.
        logging.debug("Fetched %d sites for RF-template analysis", len(sites))  # WHY: audit success size.
        print(f" Found {len(sites)} sites in organization")  # WHY: operator feedback.
        return sites  # WHY: hand fetched inventory back to caller.

    @staticmethod
    def _group_sites_by_country(  # WHY: bucket helper isolates single-pass grouping logic.
        sites: list[dict[str, Any]],
    ) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
        """Bucket sites by uppercase country code. Collect empty-country sites separately."""
        logging.info("Grouping %d sites by country code", len(sites))  # WHY: audit grouping start.
        sites_by_country: dict[str, list[dict[str, Any]]] = {}  # WHY: country -> site descriptors.
        sites_without_country: list[dict[str, Any]] = []  # WHY: sites missing country info.
        for site in sites:  # WHY: single pass bucketing keeps CC=1.
            country_code = site.get("country_code", "").strip().upper()  # WHY: normalize to uppercase code.
            site_info = {"id": site.get("id"), "name": site.get("name", "Unknown")}  # WHY: minimal descriptor.
            if country_code:  # WHY: only bucket sites with a country.
                sites_by_country.setdefault(country_code, []).append(site_info)  # WHY: add to country bucket.
            else:  # WHY: track for operator warning.
                sites_without_country.append(site_info)  # WHY: capture no-country sites separately.
        logging.debug(  # WHY: audit outcome.
            "Grouped %d countries; %d sites without country",
            len(sites_by_country),
            len(sites_without_country),
        )
        return sites_by_country, sites_without_country  # WHY: return paired buckets for downstream use.

    @staticmethod
    def _print_country_distribution(  # WHY: presentation-only helper isolates print statements.
        sites_by_country: dict[str, list[dict[str, Any]]],
        sites_without_country: list[dict[str, Any]],
    ) -> None:
        """Print the per-country site distribution and any missing-country warning."""
        print(f"\n  Found {len(sites_by_country)} unique countries:")  # WHY: header for distribution table.
        for country in sorted(sites_by_country.keys()):  # WHY: deterministic order for operator.
            print(f"   - {country}: {len(sites_by_country[country])} sites")  # WHY: per-country tally.
        if sites_without_country:  # WHY: only warn when there is a problem to report.
            print(f"\n  WARNING: {len(sites_without_country)} sites have no country code")  # WHY: warn user.

    @staticmethod
    def _fetch_existing_rf_templates(org_id: str) -> dict[str, str] | None:  # WHY: fetch existing templates.
        """Fetch existing RF templates as a {name: id} map. Return None on API error."""
        print("\n  Step 2: Checking for existing RF templates...")  # WHY: legacy step header preserved.
        logging.info("Fetching existing RF templates for org_id=%s", org_id)  # WHY: audit start.
        try:
            deps = _deps()  # WHY: local ref for readability.
            templates_response = deps.mistapi.api.v1.orgs.rftemplates.listOrgRfTemplates(  # WHY: SDK list call.
                deps.apisession, org_id, limit=deps.default_api_page_limit
            )
            existing = (
                deps.mistapi.get_all(  # WHY: materialize paginated list into flat list.
                    response=templates_response, mist_session=deps.apisession
                )
                or []
            )
        except (RuntimeError, ValueError, OSError, KeyError) as error:  # WHY: narrow exception set.
            logging.error("Failed to fetch RF templates: %s", error)  # WHY: audit failure.
            return None  # WHY: signal fetch-failure to caller.
        existing_templates = {t.get("name"): t.get("id") for t in existing}  # WHY: name->id lookup table.
        logging.debug("Loaded %d existing RF templates", len(existing_templates))  # WHY: audit outcome size.
        return existing_templates  # WHY: hand table back to caller for plan step.

    @staticmethod
    def _analyze_sites_for_rf_templates(  # WHY: orchestration helper wraps analyze phase.
        org_id: str,
    ) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], dict[str, str]] | None:
        """Analyze organization sites and existing RF templates."""
        print("\n  Step 1: Scanning organization sites for unique country codes...")  # WHY: legacy header.
        sites = SiteConfigManager._fetch_org_sites_for_rf(org_id)  # WHY: pull site inventory.
        if not sites:  # WHY: helper printed reason.
            return None  # WHY: cannot analyze without inventory.
        sites_by_country, sites_without_country = SiteConfigManager._group_sites_by_country(sites)  # WHY: bucket.
        if not sites_by_country:  # WHY: cannot template with zero country-tagged sites.
            print(" WARNING: No sites have country codes assigned.")  # WHY: legacy warning preserved.
            return None  # WHY: nothing to plan without country tags.
        SiteConfigManager._print_country_distribution(sites_by_country, sites_without_country)  # WHY: table.
        existing_templates = SiteConfigManager._fetch_existing_rf_templates(org_id)  # WHY: for de-dup planning.
        if existing_templates is None:  # WHY: API error signals abort.
            return None  # WHY: propagate fetch failure upstream.
        return sites_by_country, sites_without_country, existing_templates  # WHY: analysis triple.

    @staticmethod
    def _split_templates_by_existence(  # WHY: partition helper isolates create-vs-update classification.
        sites_by_country: dict[str, list[dict[str, Any]]],
        existing_templates: dict[str, str],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Partition country templates into create-vs-update lists."""
        to_create: list[dict[str, Any]] = []  # WHY: templates that will be created fresh.
        to_update: list[dict[str, Any]] = []  # WHY: templates that already exist.
        for country in sorted(sites_by_country.keys()):  # WHY: stable order for deterministic UX.
            template_name = f"RF-{country}"  # WHY: naming convention "RF-<ISO country>".
            if template_name in existing_templates:  # WHY: existing name means update-or-skip decision.
                to_update.append(  # WHY: record existing template with its id.
                    {"country": country, "name": template_name, "id": existing_templates[template_name]}
                )
            else:  # WHY: new template needs creation.
                to_create.append({"country": country, "name": template_name})  # WHY: record for create.
        return to_create, to_update  # WHY: paired create/update buckets.

    @staticmethod
    def _prompt_update_mode(to_update: list[dict[str, Any]]) -> str:  # WHY: interactive mode selector.
        """Ask operator whether to SKIP or UPDATE existing RF templates."""
        print(f"\n  Found {len(to_update)} existing RF templates:")  # WHY: show count before mode prompt.
        for template in to_update[:5]:  # WHY: preview first 5 to bound console output.
            print(f"   - {template['name']}")  # WHY: preview one template name per line.
        print("\n  How should existing templates be handled?")  # WHY: mode selection header.
        print("   1. SKIP - Keep existing templates as-is (recommended)")  # WHY: option 1.
        print("   2. UPDATE - Update existing templates (DESTRUCTIVE)")  # WHY: option 2.
        while True:  # WHY: reprompt until we get a valid choice.
            choice = (
                _deps()
                .input_utils.safe_input(  # WHY: gated input keeps prompt auditable.
                    "\n  Enter choice (1 or 2): ", "rf_update_mode"
                )
                .strip()
            )
            if choice == "1":  # WHY: SKIP is safe default.
                return "skip"  # WHY: caller uses mode string.
            if choice == "2":  # WHY: UPDATE is destructive.
                return "update"  # WHY: caller uses mode string.
            print("  Invalid choice.")  # WHY: operator feedback for invalid input.

    @staticmethod
    def _plan_rf_template_operations(
        sites_by_country: dict[str, list[dict[str, Any]]],
        existing_templates: dict[str, str],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str] | None:
        """Plan which RF templates to create, update, or skip."""
        to_create, to_update = SiteConfigManager._split_templates_by_existence(  # WHY: partition first.
            sites_by_country, existing_templates
        )
        update_mode = "skip"  # WHY: safe default when there are no existing templates to prompt about.
        if to_update:  # WHY: only prompt when there is something to update/skip.
            update_mode = SiteConfigManager._prompt_update_mode(to_update)
        return to_create, to_update, update_mode

    @staticmethod
    def _confirm_rf_template_operation(
        to_create: list[dict[str, Any]],
        to_update: list[dict[str, Any]],
        sites_by_country: dict[str, list[dict[str, Any]]],
        update_mode: str,
    ) -> bool:
        """Confirm RF template operation with user."""
        print("\n  " + "!" * 66)  # WHY: destructive banner open.
        print("  WARNING: DESTRUCTIVE OPERATION")  # WHY: warning line.
        print("  " + "!" * 66)  # WHY: banner divider.
        if to_create:  # WHY: only list actions we will actually take.
            print(f"  - CREATE {len(to_create)} new RF templates")
        if update_mode == "update" and to_update:  # WHY: skip mode omits update line.
            print(f"  - UPDATE {len(to_update)} existing RF templates")
        total_sites = sum(len(sites) for sites in sites_by_country.values())  # WHY: total scope of assignment.
        print(f"  - ASSIGN {total_sites} sites to country templates")  # WHY: state assignment scope.
        print("  " + "!" * 66)  # WHY: banner close.
        confirmation = _deps().input_utils.safe_input("\n  Type 'CREATE' to proceed: ", "rf_template_confirm")
        return confirmation == "CREATE"  # WHY: exact keyword required to gate destructive path.

    @staticmethod
    def _build_rf_template_payload(country: str, template_name: str) -> dict[str, Any]:
        """Build RF template API payload with auto settings."""
        return {  # WHY: literal payload keeps API contract co-located.
            "name": template_name,
            "country_code": country,
            "band_24": {"disabled": False, "bandwidth": 20, "preamble": "short"},
            "band_5": {"disabled": False, "bandwidth": 40, "preamble": "short"},
            "band_6": {"disabled": False, "bandwidth": 80, "preamble": "short"},
            "band_24_usage": "auto",
        }

    @staticmethod
    def _update_one_rf_template(
        org_id: str, template_info: dict[str, Any], mapping: dict[str, dict[str, str]], pacer: AdaptivePacer
    ) -> None:
        """Update a single existing RF template and record mapping on success."""
        country = template_info["country"]  # WHY: local key for mapping insertion.
        payload = SiteConfigManager._build_rf_template_payload(country, template_info["name"])  # WHY: fresh body.
        try:
            deps = _deps()  # WHY: local reference simplifies call.
            response = deps.mistapi.api.v1.orgs.rftemplates.updateOrgRfTemplate(  # WHY: SDK update call.
                deps.apisession, org_id, template_info["id"], body=payload
            )
            if response.status_code == 200:  # WHY: only accept HTTP 200 as successful update.
                mapping[country] = {"id": template_info["id"], "name": template_info["name"]}
                print(f"  Updated: {template_info['name']}")  # WHY: operator progress line.
            pacer.pace()  # WHY: quota-aware wait replaces the fixed sleep between template updates.
        except (RuntimeError, ValueError, OSError, KeyError) as error:  # WHY: narrow set.
            logging.error("Failed to update template %s: %s", template_info["name"], error)  # WHY: audit.

    @staticmethod
    def _create_one_rf_template(
        org_id: str, template_info: dict[str, Any], mapping: dict[str, dict[str, str]], pacer: AdaptivePacer
    ) -> None:
        """Create a single new RF template and record mapping on success."""
        country = template_info["country"]  # WHY: local key for mapping insertion.
        payload = SiteConfigManager._build_rf_template_payload(country, template_info["name"])  # WHY: body.
        try:
            deps = _deps()  # WHY: local ref.
            response = deps.mistapi.api.v1.orgs.rftemplates.createOrgRfTemplate(  # WHY: SDK create call.
                deps.apisession, org_id, payload
            )
            if response.status_code == 200:  # WHY: only 200 is success per Mist contract.
                created_id = response.data.get("id")  # WHY: extract new template id.
                mapping[country] = {"id": created_id, "name": template_info["name"]}
                print(f" Created: {template_info['name']}")  # WHY: operator feedback.
            pacer.pace()  # WHY: quota-aware wait replaces the fixed sleep between template creates.
        except (RuntimeError, ValueError, OSError, KeyError) as error:  # WHY: narrow set.
            logging.error("Failed to create template %s: %s", template_info["name"], error)  # WHY: audit.

    @staticmethod
    def _apply_existing_templates_mapping(to_update: list[dict[str, Any]], mapping: dict[str, dict[str, str]]) -> None:
        """Populate mapping from existing templates without touching the API (skip mode)."""
        for template_info in to_update:  # WHY: reuse existing ids in mapping when skipping updates.
            mapping[template_info["country"]] = {
                "id": template_info["id"],
                "name": template_info["name"],
            }

    @staticmethod
    def _execute_rf_template_operations(
        org_id: str,
        to_create: list[dict[str, Any]],
        to_update: list[dict[str, Any]],
        update_mode: str,
    ) -> dict[str, dict[str, str]]:
        """Execute RF template create/update operations. Returns country->template mapping."""
        template_mapping: dict[str, dict[str, str]] = {}  # WHY: country -> {id,name} lookup for assignment.
        pacer = _pacer()  # WHY: one pacer spans both write phases so the PID state survives the whole run.
        if update_mode == "update":  # WHY: only touch existing templates on explicit update.
            for template_info in to_update:  # WHY: iterate updates individually so one failure is isolated.
                SiteConfigManager._update_one_rf_template(org_id, template_info, template_mapping, pacer)
        else:  # WHY: skip mode reuses existing ids without API mutation.
            SiteConfigManager._apply_existing_templates_mapping(to_update, template_mapping)
        for template_info in to_create:  # WHY: create fresh templates last so failures do not block updates.
            SiteConfigManager._create_one_rf_template(org_id, template_info, template_mapping, pacer)
        return template_mapping

    @staticmethod
    def _assign_one_site_to_template(
        site_info: dict[str, Any],
        template: dict[str, str],
        buckets: tuple[list[dict[str, Any]], list[dict[str, Any]]],
        pacer: AdaptivePacer,
    ) -> None:
        """Assign one site to its RF template and record success/failure."""
        success, failed = buckets  # WHY: unpack shared result accumulators.
        try:
            deps = _deps()  # WHY: local ref keeps call chain compact.
            response = deps.mistapi.api.v1.sites.sites.updateSiteInfo(  # WHY: SDK site update call.
                deps.apisession, site_info["id"], body={"rftemplate_id": template["id"]}
            )
            if response.status_code == 200:  # WHY: only 200 is success.
                success.append(
                    {
                        "site_name": site_info["name"],
                        "country": template["country"],
                        "template_name": template["name"],
                    }
                )
            else:  # WHY: non-200 is recorded as HTTP-level failure with status.
                failed.append({"site_name": site_info["name"], "error": f"HTTP {response.status_code}"})
            pacer.pace()  # WHY: quota-aware wait replaces the fixed sleep between site assignments.
        except (RuntimeError, ValueError, OSError, KeyError) as error:  # WHY: narrow set.
            failed.append({"site_name": site_info["name"], "error": str(error)})

    @staticmethod
    def _assign_sites_to_rf_templates(
        sites_by_country: dict[str, list[dict[str, Any]]],
        template_mapping: dict[str, dict[str, str]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Assign sites to their country RF templates. Honors stop-signal for cancellation."""
        success: list[dict[str, Any]] = []  # WHY: success bucket for report + export.
        failed: list[dict[str, Any]] = []  # WHY: failure bucket for report + export.
        deps = _deps()  # WHY: local ref shared by whole assignment loop.
        pacer = _pacer()  # WHY: one pacer spans every country so the PID state tracks the whole assignment run.
        for country, sites in sites_by_country.items():  # WHY: iterate one country at a time.
            if country not in template_mapping:  # WHY: no mapping means we skip that whole country.
                continue
            template = {  # WHY: bundle template identity for helper call.
                "id": template_mapping[country]["id"],
                "name": template_mapping[country]["name"],
                "country": country,
            }
            for site_info in sites:  # WHY: iterate sites within country.
                if deps.config_utils.check_stop_signal():  # WHY: honor cancel semantics between requests.
                    return success, failed
                SiteConfigManager._assign_one_site_to_template(site_info, template, (success, failed), pacer)
        return success, failed

    @staticmethod
    def _report_rf_template_results(report: RfTemplateReport) -> None:
        """Report RF template operation results and export CSV files."""
        print("\n" + "=" * 70)  # WHY: open completion banner.
        print(" OPERATION COMPLETE")  # WHY: banner title.
        print("=" * 70)  # WHY: banner divider.
        print(f"  RF Templates Created: {len(report.created)}")  # WHY: creation tally.
        label = "Updated" if report.update_mode == "update" else "Existing"  # WHY: label changes with mode.
        print(f"  RF Templates {label}: {len(report.updated)}")  # WHY: emit mode-aware label.
        print(f"  Sites Successfully Assigned: {len(report.success)}")  # WHY: success tally.
        print(f"  Sites Failed: {len(report.failed)}")  # WHY: failure tally.
        print(f"  Sites Skipped (no country): {len(report.skipped)}")  # WHY: skipped tally.
        deps = _deps()  # WHY: local ref for exporter calls.
        if report.success:  # WHY: only export non-empty datasets.
            deps.data_exporter.write_with_format_selection(report.success, "SuccessfulRFTemplateAssignments.csv")
        if report.failed:  # WHY: same rationale for failure export.
            deps.data_exporter.write_with_format_selection(report.failed, "FailedRFTemplateAssignments.csv")

    # -------------------------------------------------------------------------
    # Device Profile Creation (Menu 173)
    # -------------------------------------------------------------------------
    @staticmethod
    def create_ap_model_device_profiles() -> None:
        """Create Device Profile for each unique AP model (DESTRUCTIVE)."""
        logging.warning("Menu #173 DESTRUCTIVE: Create AP model device profiles operation started")  # WHY: audit.
        SiteConfigManager._display_device_profile_header()  # WHY: banner.
        org_id = _deps().config_utils.get_cached_or_prompted_org_id()  # WHY: resolve target org.
        ap_models, _models_without_info = SiteConfigManager._analyze_ap_models(org_id)  # WHY: gather models.
        if not ap_models:  # WHY: nothing to do without AP models.
            return
        existing_profiles = SiteConfigManager._get_existing_device_profiles(org_id)  # WHY: for de-dup planning.
        if existing_profiles is None:  # WHY: API error aborts here.
            return
        to_create, to_skip = SiteConfigManager._plan_profile_creation(ap_models, existing_profiles)  # WHY: plan.
        if not to_create:  # WHY: no-op when every model already has a profile.
            print("\n  All AP model Device Profiles already exist.")
            return
        if not SiteConfigManager._confirm_profile_creation(to_create, to_skip):  # WHY: final destructive gate.
            return
        created, failed = SiteConfigManager._execute_profile_creation(org_id, to_create)  # WHY: run creates.
        SiteConfigManager._report_profile_creation_results(created, failed, to_skip)  # WHY: summarize.
        logging.warning(  # WHY: audit final tallies.
            "Menu #173 complete: %s profiles created, %s failed", len(created), len(failed)
        )

    @staticmethod
    def _display_device_profile_header() -> None:
        """Display device profile creation header."""
        print("\n" + "=" * 70)  # WHY: open header banner.
        print(" CREATE AP MODEL DEVICE PROFILES")  # WHY: title.
        print("=" * 70)  # WHY: close header banner.

    @staticmethod
    def _fetch_org_ap_inventory(org_id: str) -> list[dict[str, Any]] | None:
        """Fetch org AP inventory list. Return None on error or empty."""
        try:
            deps = _deps()  # WHY: local ref simplifies call.
            inventory_response = deps.mistapi.api.v1.orgs.inventory.getOrgInventory(  # WHY: SDK inventory call.
                deps.apisession, org_id, type="ap", limit=deps.default_api_page_limit
            )
            all_devices = (
                deps.mistapi.get_all(  # WHY: materialize paginated list.
                    response=inventory_response, mist_session=deps.apisession
                )
                or []
            )
        except (RuntimeError, ValueError, OSError, KeyError) as error:  # WHY: narrow set.
            logging.error("Failed to fetch inventory: %s", error)  # WHY: audit failure.
            print(f" ERROR: Failed to fetch inventory - {error}")  # WHY: operator visibility.
            return None
        if not all_devices:  # WHY: empty inventory means nothing to profile.
            print(" No AP devices found in organization.")
            return None
        return all_devices

    @staticmethod
    def _tally_ap_models(
        all_devices: list[dict[str, Any]],
    ) -> tuple[set[str], list[str]]:
        """Return (unique models, devices without model info) from inventory."""
        ap_models: set[str] = set()  # WHY: dedupe models via set.
        models_without_info: list[str] = []  # WHY: record devices missing model for report.
        for device in all_devices:  # WHY: single pass tally.
            model = device.get("model")
            if model:  # WHY: keep only valid model strings.
                ap_models.add(model)
            else:  # WHY: fall back to name/mac for operator identification.
                models_without_info.append(device.get("name", device.get("mac", "unknown")))
        return ap_models, models_without_info

    @staticmethod
    def _analyze_ap_models(org_id: str) -> tuple[set[str], list[str]]:
        """Analyze organization inventory for unique AP models."""
        print("\n  Step 1: Scanning organization for AP device models...")  # WHY: legacy header preserved.
        all_devices = SiteConfigManager._fetch_org_ap_inventory(org_id)  # WHY: pull inventory once.
        if all_devices is None:  # WHY: helper printed reason.
            return set(), []
        ap_models, models_without_info = SiteConfigManager._tally_ap_models(all_devices)  # WHY: tally.
        print(f"\n  Found {len(ap_models)} unique AP models:")  # WHY: operator summary header.
        for model in sorted(ap_models):  # WHY: sorted list is deterministic and easier to scan.
            print(f"   - {model}")
        return ap_models, models_without_info

    @staticmethod
    def _get_existing_device_profiles(org_id: str) -> dict[str, str] | None:
        """Get existing device profiles as {name: id} map, None on error."""
        print("\n  Step 2: Checking for existing Device Profiles...")  # WHY: legacy step header preserved.
        try:
            deps = _deps()  # WHY: local ref.
            profiles_response = deps.mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(  # WHY: SDK list.
                deps.apisession, org_id, type="ap", limit=deps.default_api_page_limit
            )
            existing = (
                deps.mistapi.get_all(  # WHY: materialize paginated list.
                    response=profiles_response, mist_session=deps.apisession
                )
                or []
            )
            return {profile.get("name"): profile.get("id") for profile in existing}  # WHY: name->id lookup.
        except (RuntimeError, ValueError, OSError, KeyError) as error:  # WHY: narrow set.
            logging.error("Failed to fetch device profiles: %s", error)  # WHY: audit failure.
            print(f" ERROR: Failed to fetch device profiles - {error}")  # WHY: operator visibility.
            return None

    @staticmethod
    def _plan_profile_creation(
        ap_models: set[str], existing_profiles: dict[str, str]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Plan which device profiles to create vs skip."""
        to_create: list[dict[str, Any]] = []  # WHY: profiles that need creation.
        to_skip: list[dict[str, Any]] = []  # WHY: profiles that already exist.
        for model in sorted(ap_models):  # WHY: deterministic order for operator UX.
            profile_name = f"AP-{model}"  # WHY: naming convention "AP-<model>".
            if profile_name in existing_profiles:  # WHY: existing profile means skip creation.
                to_skip.append({"model": model, "name": profile_name, "id": existing_profiles[profile_name]})
            else:  # WHY: absent profile means create.
                to_create.append({"model": model, "name": profile_name})
        if to_skip:  # WHY: only report non-empty counts to operator.
            print(f"\n  Found {len(to_skip)} existing Device Profiles (will skip)")
        if to_create:  # WHY: report create count for scope preview.
            print(f"\n  Will create {len(to_create)} new Device Profiles")
        return to_create, to_skip

    @staticmethod
    def _confirm_profile_creation(to_create: list[dict[str, Any]], to_skip: list[dict[str, Any]]) -> bool:
        """Confirm device profile creation with user."""
        _ = to_skip  # WHY: preserve legacy signature. Count is already reported by planner.
        print("\n  " + "!" * 66)  # WHY: destructive banner open.
        print("  WARNING: DESTRUCTIVE OPERATION")  # WHY: warning line.
        print("  " + "!" * 66)  # WHY: banner divider.
        print(f"  This will CREATE {len(to_create)} new Device Profiles")  # WHY: scope preview.
        print("  " + "!" * 66)  # WHY: banner close.
        confirmation = _deps().input_utils.safe_input("\n  Type 'CREATE' to proceed: ", "profile_creation")
        return confirmation == "CREATE"  # WHY: exact keyword gate.

    @staticmethod
    def _create_one_device_profile(
        org_id: str,
        profile_info: dict[str, Any],
        created: list[dict[str, Any]],
        failed: list[dict[str, Any]],
        pacer: AdaptivePacer,
    ) -> None:
        """Create one device profile and append to created/failed bucket."""
        payload = {"name": profile_info["name"], "type": "ap"}  # WHY: minimal API contract for AP profile.
        try:
            deps = _deps()  # WHY: local ref.
            response = deps.mistapi.api.v1.orgs.deviceprofiles.createOrgDeviceProfile(  # WHY: SDK create call.
                deps.apisession, org_id, body=payload
            )
            SiteConfigManager._record_profile_create_response(response, profile_info, created, failed)
            pacer.pace()  # WHY: quota-aware wait replaces the fixed sleep between profile creates.
        except (RuntimeError, ValueError, OSError, KeyError) as error:  # WHY: narrow set.
            failed.append({"model": profile_info["model"], "name": profile_info["name"], "error": str(error)})

    @staticmethod
    def _record_profile_create_response(
        response: Any,
        profile_info: dict[str, Any],
        created: list[dict[str, Any]],
        failed: list[dict[str, Any]],
    ) -> None:
        """Record HTTP response outcome onto created/failed buckets."""
        if response.status_code == 200:  # WHY: only 200 is success.
            created_id = response.data.get("id")  # WHY: extract id from response.
            created.append({"model": profile_info["model"], "name": profile_info["name"], "id": created_id})
            print(f"  Created: {profile_info['name']}")  # WHY: operator progress line.
            return
        failed.append(  # WHY: HTTP-level failure captured with status.
            {
                "model": profile_info["model"],
                "name": profile_info["name"],
                "error": f"HTTP {response.status_code}",
            }
        )

    @staticmethod
    def _execute_profile_creation(
        org_id: str, to_create: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Execute device profile creation. Returns (created, failed) lists."""
        created: list[dict[str, Any]] = []  # WHY: success bucket.
        failed: list[dict[str, Any]] = []  # WHY: failure bucket.
        print(f"\n  Step 3: Creating {len(to_create)} new Device Profiles...")  # WHY: legacy step header.
        pacer = _pacer()  # WHY: one pacer per run carries the PID state across every profile create.
        for profile_info in to_create:  # WHY: iterate sequentially to keep rate under limits.
            SiteConfigManager._create_one_device_profile(org_id, profile_info, created, failed, pacer)
        return created, failed

    @staticmethod
    def _report_profile_creation_results(
        created: list[dict[str, Any]],
        failed: list[dict[str, Any]],
        skipped: list[dict[str, Any]],
    ) -> None:
        """Report device profile creation results and export CSV files."""
        print("\n" + "=" * 70)  # WHY: open completion banner.
        print(" OPERATION COMPLETE")  # WHY: banner title.
        print("=" * 70)  # WHY: banner divider.
        print(f"  Device Profiles Created: {len(created)}")  # WHY: created tally.
        print(f"  Device Profiles Failed: {len(failed)}")  # WHY: failed tally.
        print(f"  Device Profiles Skipped: {len(skipped)}")  # WHY: skipped tally.
        deps = _deps()  # WHY: local ref for exporter.
        if created:  # WHY: export only non-empty.
            deps.data_exporter.write_with_format_selection(created, "CreatedAPModelDeviceProfiles.csv")
        if failed:  # WHY: export only non-empty.
            deps.data_exporter.write_with_format_selection(failed, "FailedAPModelDeviceProfiles.csv")

    # -------------------------------------------------------------------------
    # Device Profile Assignment (Menu 174)
    # -------------------------------------------------------------------------
    @staticmethod
    def assign_aps_to_matching_device_profiles() -> None:
        """Assign AP devices to matching Device Profiles (DESTRUCTIVE)."""
        logging.warning("Menu #174 DESTRUCTIVE: Assign APs to device profiles operation started")  # WHY: audit.
        SiteConfigManager._display_profile_assignment_header()  # WHY: banner.
        org_id = _deps().config_utils.get_cached_or_prompted_org_id()  # WHY: resolve target org.
        SiteConfigManager._run_profile_assignment_workflow(org_id)  # WHY: single-responsibility inner runner.

    @staticmethod
    def _run_profile_assignment_workflow(org_id: str) -> None:
        """Drive fetch/analyze/confirm/execute/report sequence for AP profile assignment."""
        all_aps = SiteConfigManager._fetch_ap_inventory(org_id)  # WHY: pull APs first.
        if not all_aps:  # WHY: helper printed reason.
            return
        profile_map = SiteConfigManager._fetch_profile_map(org_id)  # WHY: fetch profile lookup.
        if not profile_map:  # WHY: cannot match without profiles.
            return
        matched, unmatched, no_model = SiteConfigManager._analyze_ap_profile_matching(  # WHY: categorize.
            all_aps, profile_map
        )
        if not matched:  # WHY: nothing to assign.
            print("\n  No APs have matching Device Profiles to assign.")
            return
        if not SiteConfigManager._confirm_profile_assignment(matched, unmatched):  # WHY: destructive gate.
            return
        success, failed = SiteConfigManager._execute_profile_assignment(org_id, matched)  # WHY: run assigns.
        SiteConfigManager._report_profile_assignment_results(success, failed, unmatched, no_model)  # WHY: report.
        logging.warning(  # WHY: audit final tallies.
            "Menu #174 complete: %s APs assigned, %s failed", len(success), len(failed)
        )

    @staticmethod
    def _display_profile_assignment_header() -> None:
        """Display profile assignment header."""
        print("\n" + "=" * 70)  # WHY: open banner.
        print(" ASSIGN APS TO MATCHING DEVICE PROFILES")  # WHY: title.
        print("=" * 70)  # WHY: banner close.

    @staticmethod
    def _fetch_ap_inventory(org_id: str) -> list[dict[str, Any]] | None:
        """Fetch AP inventory from organization."""
        print("\n  Step 1: Fetching AP inventory from organization...")  # WHY: legacy header.
        try:
            deps = _deps()  # WHY: local ref.
            inventory_response = deps.mistapi.api.v1.orgs.inventory.getOrgInventory(  # WHY: SDK inventory call.
                deps.apisession, org_id, type="ap", limit=deps.default_api_page_limit
            )
            all_aps = (
                deps.mistapi.get_all(  # WHY: materialize paginated list.
                    response=inventory_response, mist_session=deps.apisession
                )
                or []
            )
            if not all_aps:  # WHY: empty inventory means nothing to assign.
                print(" No APs found in organization inventory.")
                return None
            print(f"  Found {len(all_aps)} APs in organization")  # WHY: operator feedback.
            return all_aps
        except (RuntimeError, ValueError, OSError, KeyError) as error:  # WHY: narrow set.
            logging.error("Failed to fetch AP inventory: %s", error)  # WHY: audit failure.
            print(f" ERROR: Failed to fetch AP inventory - {error}")  # WHY: operator visibility.
            return None

    @staticmethod
    def _build_profile_map(existing: list[dict[str, Any]]) -> dict[str, str]:
        """Return {name: id} map from existing device profiles, filtering incomplete rows."""
        return {  # WHY: comprehension avoids intermediate loop variables.
            profile.get("name"): profile.get("id") for profile in existing if profile.get("name") and profile.get("id")
        }

    @staticmethod
    def _fetch_profile_map(org_id: str) -> dict[str, str] | None:
        """Fetch device profiles and return name->id mapping. None on error/empty."""
        print("\n  Step 2: Fetching existing Device Profiles...")  # WHY: legacy header preserved.
        try:
            deps = _deps()  # WHY: local ref.
            profiles_response = deps.mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(  # WHY: SDK list.
                deps.apisession, org_id, type="ap", limit=deps.default_api_page_limit
            )
            existing = (
                deps.mistapi.get_all(  # WHY: materialize paginated list.
                    response=profiles_response, mist_session=deps.apisession
                )
                or []
            )
        except (RuntimeError, ValueError, OSError, KeyError) as error:  # WHY: narrow set.
            logging.error("Failed to fetch Device Profiles: %s", error)  # WHY: audit failure.
            print(f" ERROR: Failed to fetch Device Profiles - {error}")  # WHY: operator visibility.
            return None
        profile_map = SiteConfigManager._build_profile_map(existing)  # WHY: build lookup outside try block.
        if not profile_map:  # WHY: no profiles means nothing to assign against.
            print(" No Device Profiles found in organization.")
            return None
        print(f"  Found {len(profile_map)} Device Profiles")  # WHY: operator feedback.
        return profile_map

    @staticmethod
    def _classify_one_ap(
        access_point: dict[str, Any],
        profile_map: dict[str, str],
    ) -> tuple[str, dict[str, Any]]:
        """Return ('matched'|'unmatched'|'no_model', record) for a single AP."""
        ap_mac = access_point.get("mac", "unknown")  # WHY: identifier fallback.
        ap_name = access_point.get("name", ap_mac)  # WHY: prefer name, fall back to MAC.
        ap_model = access_point.get("model")  # WHY: model drives profile lookup.
        if not ap_model:  # WHY: missing model cannot be matched to profile.
            return "no_model", {"mac": ap_mac, "name": ap_name}
        expected_profile = f"AP-{ap_model}"  # WHY: naming convention "AP-<model>".
        if expected_profile in profile_map:  # WHY: matched entry gets full record for assignment.
            return "matched", {
                "mac": ap_mac,
                "name": ap_name,
                "model": ap_model,
                "profile_name": expected_profile,
                "profile_id": profile_map[expected_profile],
            }
        return "unmatched", {  # WHY: unmatched keeps model + expected name for report.
            "mac": ap_mac,
            "name": ap_name,
            "model": ap_model,
            "expected_profile": expected_profile,
        }

    @staticmethod
    def _analyze_ap_profile_matching(
        all_aps: list[dict[str, Any]],
        profile_map: dict[str, str],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Categorize APs into (matched, unmatched, no_model) buckets."""
        matched: list[dict[str, Any]] = []  # WHY: APs with matching device profile.
        unmatched: list[dict[str, Any]] = []  # WHY: APs whose model has no matching profile.
        no_model: list[dict[str, Any]] = []  # WHY: APs missing model info entirely.
        buckets = {"matched": matched, "unmatched": unmatched, "no_model": no_model}  # WHY: dispatch table.
        for access_point in all_aps:  # WHY: single pass classification.
            bucket_name, record = SiteConfigManager._classify_one_ap(access_point, profile_map)
            buckets[bucket_name].append(record)  # WHY: dispatch to bucket by classifier result.
        print("\n  Analysis:")  # WHY: operator summary header.
        print(f"   APs with matching profiles: {len(matched)}")  # WHY: matched tally.
        print(f"   APs without matching profiles: {len(unmatched)}")  # WHY: unmatched tally.
        print(f"   APs without model info: {len(no_model)}")  # WHY: no-model tally.
        return matched, unmatched, no_model

    @staticmethod
    def _confirm_profile_assignment(with_profile: list[dict[str, Any]], without_profile: list[dict[str, Any]]) -> bool:
        """Confirm profile assignment with user."""
        print("\n  " + "!" * 66)  # WHY: destructive banner open.
        print("  WARNING: DESTRUCTIVE OPERATION")  # WHY: warning line.
        print("  " + "!" * 66)  # WHY: banner divider.
        print(f"  This will ASSIGN {len(with_profile)} APs to their matching Device Profiles")  # WHY: scope.
        print(f"  APs without matching profiles will be SKIPPED: {len(without_profile)}")  # WHY: skip scope.
        print("  " + "!" * 66)  # WHY: banner close.
        confirmation = _deps().input_utils.safe_input("\n  Type 'ASSIGN' to proceed: ", "profile_assignment")
        return confirmation == "ASSIGN"  # WHY: keyword differs from other menus by design.

    @staticmethod
    def _assign_one_ap_to_profile(
        org_id: str,
        ap_info: dict[str, Any],
        success: list[dict[str, Any]],
        failed: list[dict[str, Any]],
        pacer: AdaptivePacer,
    ) -> None:
        """Assign one AP to its device profile, updating success/failed buckets."""
        try:
            deps = _deps()  # WHY: local ref.
            response = deps.mistapi.api.v1.orgs.deviceprofiles.assignOrgDeviceProfile(  # WHY: SDK assign call.
                deps.apisession, org_id, ap_info["profile_id"], body={"macs": [ap_info["mac"]]}
            )
            SiteConfigManager._record_ap_assign_response(response, ap_info, success, failed)
            pacer.pace()  # WHY: quota-aware wait replaces the fixed sleep between AP assignments.
        except (RuntimeError, ValueError, OSError, KeyError) as error:  # WHY: narrow set.
            failed.append({"mac": ap_info["mac"], "name": ap_info["name"], "error": str(error)})

    @staticmethod
    def _record_ap_assign_response(
        response: Any,
        ap_info: dict[str, Any],
        success: list[dict[str, Any]],
        failed: list[dict[str, Any]],
    ) -> None:
        """Record HTTP response onto success/failed buckets for AP assignment."""
        if response.status_code == 200:  # WHY: only 200 is success.
            success.append(
                {
                    "mac": ap_info["mac"],
                    "name": ap_info["name"],
                    "model": ap_info["model"],
                    "profile_name": ap_info["profile_name"],
                }
            )
            return
        failed.append(  # WHY: HTTP-level failure captured with status.
            {"mac": ap_info["mac"], "name": ap_info["name"], "error": f"HTTP {response.status_code}"}
        )

    @staticmethod
    def _execute_profile_assignment(
        org_id: str, with_profile: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Execute profile assignment API calls."""
        success: list[dict[str, Any]] = []  # WHY: success bucket.
        failed: list[dict[str, Any]] = []  # WHY: failure bucket.
        print(f"\n  Step 3: Assigning {len(with_profile)} APs to Device Profiles...")  # WHY: legacy header.
        pacer = _pacer()  # WHY: one pacer per run carries the PID state across every assignment call.
        for ap_info in with_profile:  # WHY: iterate sequentially to stay under rate limits.
            SiteConfigManager._assign_one_ap_to_profile(org_id, ap_info, success, failed, pacer)
        return success, failed

    @staticmethod
    def _report_profile_assignment_results(
        success: list[dict[str, Any]],
        failed: list[dict[str, Any]],
        without_profile: list[dict[str, Any]],
        without_model: list[dict[str, Any]],
    ) -> None:
        """Report profile assignment results and export CSV files."""
        print("\n" + "=" * 70)  # WHY: open completion banner.
        print(" OPERATION COMPLETE")  # WHY: banner title.
        print("=" * 70)  # WHY: banner divider.
        print(f"  APs Successfully Assigned: {len(success)}")  # WHY: success tally.
        print(f"  APs Failed: {len(failed)}")  # WHY: failure tally.
        print(f"  APs Skipped (no matching profile): {len(without_profile)}")  # WHY: no-profile tally.
        print(f"  APs Skipped (no model info): {len(without_model)}")  # WHY: no-model tally.
        deps = _deps()  # WHY: local ref for exporter.
        if success:  # WHY: export only non-empty datasets.
            deps.data_exporter.write_with_format_selection(success, "SuccessfulAPProfileAssignments.csv")
        if failed:  # WHY: same rationale for failures.
            deps.data_exporter.write_with_format_selection(failed, "FailedAPProfileAssignments.csv")
        if without_profile:  # WHY: skipped-no-profile bucket exported for follow-up.
            deps.data_exporter.write_with_format_selection(without_profile, "SkippedAPsNoMatchingProfile.csv")
