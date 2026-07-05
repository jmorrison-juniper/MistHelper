"""Site export utilities extracted from MistHelper.py."""

from __future__ import annotations  # WHY: enable forward-reference typing.

import inspect  # WHY: introspect API signatures to gate limit kwarg.
import logging  # WHY: structured export progress + error logging.
import os  # WHY: derive display path for operator feedback.
from dataclasses import dataclass  # WHY: bundle 14 DI params into a frozen slots record.
from typing import Any  # WHY: dependencies are unknown-type runtime injections.

from src.export.site_insights_exporter import (  # WHY: reuse insights exporter via inheritance.
    SiteInsightsExporter,
    configure_site_insights_exporter_dependencies,
)

_LIMIT_DEFAULT: int = 1000  # WHY: default page size for mistapi list endpoints.
_LOOKBACK_DEFAULT_HOURS: int = 24  # WHY: default dynamic lookback window (hours).
_LOOKBACK_MIN_HOURS: int = 1  # WHY: minimum floor for dynamic lookback.
_DATA_SUBDIR: str = "data"  # WHY: default output folder for exports.
_INSIGHT_METRIC_SCOPE: str = "site"  # WHY: constant scope used for SLE metric queries.

apisession: Any = None  # WHY: injected mistapi session handle.
PromptUtils: Any = None  # WHY: injected operator-prompt helpers.
ConfigUtils: Any = None  # WHY: injected config/org resolution helpers.
DataProcessingUtils: Any = None  # WHY: injected row-flattening helpers.
DataExporter: Any = None  # WHY: injected CSV/format writer.
TimeUtils: Any = None  # WHY: injected time-window computation helpers.
EnhancedSSHRunner: Any = None  # WHY: injected SSH runner for filename sanitization.
InsightMetricsUtils: Any = None  # WHY: injected insight metric helpers.
PacketCaptureManager: Any = None  # WHY: injected MAC validation/normalization.
APICoreFetchUtils: Any = None  # WHY: injected org-wide fetch helpers.
is_debug_mode: Any = None  # WHY: injected debug-mode predicate.
PrettyTable: Any = None  # WHY: injected table renderer for debug output.
tqdm: Any = None  # WHY: injected progress bar module.
mistapi: Any = None  # WHY: injected mistapi client module.


@dataclass(frozen=True, slots=True)
class _ExportDeps:  # WHY: bundle 14 DI kwargs into a single frozen record for handoff.
    """Bundle 14 runtime dependencies into a single immutable config record."""

    apisession_dependency: Any  # WHY: mistapi session handle.
    prompt_utils: Any  # WHY: operator-prompt helpers.
    config_utils: Any  # WHY: config/org resolution helpers.
    data_processing_utils: Any  # WHY: row-flattening helpers.
    data_exporter: Any  # WHY: CSV/format writer.
    time_utils: Any  # WHY: time-window computation helpers.
    enhanced_ssh_runner: Any  # WHY: SSH runner for filename sanitization.
    insight_metrics_utils: Any  # WHY: insight metric helpers.
    packet_capture_manager: Any  # WHY: MAC validation/normalization.
    api_core_fetch_utils: Any  # WHY: org-wide fetch helpers.
    is_debug_mode_fn: Any  # WHY: debug-mode predicate.
    pretty_table_class: Any  # WHY: table renderer for debug output.
    tqdm_module: Any  # WHY: progress bar module.
    mistapi_dependency: Any  # WHY: mistapi client module.


def _apply_module_globals(
    deps: _ExportDeps,
) -> None:  # WHY: assign 14 injected deps to module globals for class methods.
    """Assign injected dependencies to module-level globals used by class methods."""
    global apisession, PromptUtils, ConfigUtils, DataProcessingUtils  # WHY: publish session + config + processing.
    global DataExporter, TimeUtils, EnhancedSSHRunner, InsightMetricsUtils  # WHY: publish writer/time/ssh/metrics.
    global PacketCaptureManager, APICoreFetchUtils, is_debug_mode  # WHY: publish MAC + fetch + debug predicate.
    global PrettyTable, tqdm, mistapi  # WHY: publish table + progress + mistapi module.
    apisession = deps.apisession_dependency  # WHY: bind session for exporters.
    PromptUtils = deps.prompt_utils  # WHY: bind prompt helpers.
    ConfigUtils = deps.config_utils  # WHY: bind config helpers.
    DataProcessingUtils = deps.data_processing_utils  # WHY: bind flatten helpers.
    DataExporter = deps.data_exporter  # WHY: bind writer.
    TimeUtils = deps.time_utils  # WHY: bind time helpers.
    EnhancedSSHRunner = deps.enhanced_ssh_runner  # WHY: bind SSH runner.
    InsightMetricsUtils = deps.insight_metrics_utils  # WHY: bind insight metrics.
    PacketCaptureManager = deps.packet_capture_manager  # WHY: bind packet capture manager.
    APICoreFetchUtils = deps.api_core_fetch_utils  # WHY: bind fetch helpers.
    is_debug_mode = deps.is_debug_mode_fn  # WHY: bind debug predicate.
    PrettyTable = deps.pretty_table_class  # WHY: bind table renderer.
    tqdm = deps.tqdm_module  # WHY: bind progress bar.
    mistapi = deps.mistapi_dependency  # WHY: bind mistapi module.


def _forward_insights_dependencies(deps: _ExportDeps) -> None:  # WHY: relay dep subset to sibling insights module.
    """Forward the insights subset of dependencies to the insights exporter module."""
    configure_site_insights_exporter_dependencies(  # WHY: keep insights exporter globals wired.
        apisession_dependency=deps.apisession_dependency,
        prompt_utils=deps.prompt_utils,
        data_processing_utils=deps.data_processing_utils,
        data_exporter=deps.data_exporter,
        enhanced_ssh_runner=deps.enhanced_ssh_runner,
        insight_metrics_utils=deps.insight_metrics_utils,
        packet_capture_manager=deps.packet_capture_manager,
        mistapi_dependency=deps.mistapi_dependency,
    )


def configure_site_export_utils_dependencies(
    **deps: Any,
) -> None:  # WHY: single kwargs param satisfies STRUCT-PARAMS budget.
    """Configure runtime dependencies from MistHelper orchestration layer."""
    record = _ExportDeps(**deps)  # WHY: validate + freeze the 14 kwargs into a record.
    _apply_module_globals(record)  # WHY: publish deps as module globals.
    _forward_insights_dependencies(record)  # WHY: keep insights exporter deps in sync.


def _sanitize_for_filename(text: str) -> str:  # WHY: shared filename-token normalization for exports.
    """Normalize spaces and dashes to underscores for filename tokens."""
    return text.replace(" ", "_").replace("-", "_")  # WHY: single-token filename fragment.


def _build_export_filename(data_type: str, site_name: str) -> str:  # WHY: legacy CamelCase filename builder.
    """Build legacy-format ``Site<Type>_<SiteName>.csv`` filename."""
    safe_data_type = data_type.replace(" ", "").replace("-", "").title()  # WHY: preserve legacy CamelCase.
    safe_site_name = _sanitize_for_filename(site_name)  # WHY: safe site fragment.
    return f"Site{safe_data_type}_{safe_site_name}.csv"  # WHY: preserved legacy format.


def _api_supports_limit(api_call: Any) -> bool:  # WHY: introspect signature so limit kwarg is only sent when accepted.
    """Return True when the target API accepts a ``limit`` keyword argument."""
    try:
        sig = inspect.signature(api_call)  # WHY: probe signature for limit gating.
        return "limit" in sig.parameters  # WHY: only pass limit when supported.
    except (TypeError, ValueError):  # WHY: builtins may reject signature inspection.
        return True  # WHY: default to sending limit if signature unavailable.


def _fetch_site_data(
    api_call: Any, site_id: str, api_kwargs: dict[str, Any]
) -> Any:  # WHY: paged fetch helper for site endpoints.
    """Call site API respecting limit support and return paginated rawdata."""
    if _api_supports_limit(api_call):  # WHY: branch on limit-kwarg support to avoid TypeError.
        logging.info(
            "Calling %s with limit=%s for site %s", api_call.__name__, _LIMIT_DEFAULT, site_id
        )  # WHY: audit pre-call.
        response = api_call(apisession, site_id, limit=_LIMIT_DEFAULT, **api_kwargs)  # WHY: paged call.
    else:
        logging.debug("API function %s does not support 'limit' parameter", api_call.__name__)  # WHY: audit unpaged.
        response = api_call(apisession, site_id, **api_kwargs)  # WHY: call without limit.
    return mistapi.get_all(response=response, mist_session=apisession)  # WHY: full pagination.


def _resolve_site_display_path(filename: str) -> str:  # WHY: helper to compute confirmation path.
    """Return storage-relative display path for operator confirmation."""
    return filename if os.path.dirname(filename) else os.path.join(_DATA_SUBDIR, filename)  # WHY: legacy display path.


def _prepare_rows(
    rawdata: list[dict[str, Any]], sort_key: str
) -> list[dict[str, Any]]:  # WHY: shared row prep pipeline.
    """Sort (when key provided) then flatten and escape rows for export."""
    if sort_key:  # WHY: skip sorting when caller omits key.
        rawdata = sorted(rawdata, key=lambda x: x.get(sort_key, ""))  # WHY: stable operator-facing sort.
    data = DataProcessingUtils.flatten_nested_fields(rawdata)  # WHY: flatten nested JSON for CSV.
    return DataProcessingUtils.escape_multiline(data)  # WHY: escape newlines for CSV safety.


def _emit_debug_table(data: list[dict[str, Any]]) -> None:  # WHY: renders PrettyTable in debug mode only.
    """Render PrettyTable of exported rows for debug-mode operators."""
    fields = DataProcessingUtils.get_unique_keys(data)  # WHY: union of keys as columns.
    table = PrettyTable()  # WHY: instantiate debug table renderer.
    table.field_names = fields  # WHY: set stable column order.
    table.valign = "t"  # WHY: preserve legacy top alignment.
    for item in tqdm(data, desc="Processing", unit="record"):  # WHY: progress bar per row.
        row = [item.get(field, "") for field in table.field_names]  # WHY: row in stable order.
        table.add_row(row)  # WHY: append to table.
    print(table)  # WHY: legacy debug console output.
    logging.debug("Site data displayed in table format (debug mode).")  # WHY: audit debug render.


def _read_site_response_rows(response: Any) -> list[dict[str, Any]]:  # WHY: normalizes heterogeneous API shapes.
    """Coerce a site API response into a list-of-dicts payload for flattening."""
    raw = getattr(response, "data", response) or {}  # WHY: tolerate dataclass or dict responses.
    if isinstance(raw, dict):  # WHY: dict payloads represent a single-row report.
        return [raw]  # WHY: single-dict wraps into single-row list.
    return raw if isinstance(raw, list) else []  # WHY: fall back to empty when shape unknown.


def _write_site_report(  # WHY: single-endpoint export helper reused by many exports.
    api_call: Any,
    site_id: str,
    filename: str,
    api_function_name: str,
) -> int:
    """Export a single-endpoint site report and return the number of rows written."""
    response = api_call(apisession, site_id)  # WHY: fetch site endpoint payload.
    rows = _read_site_response_rows(response)  # WHY: normalize shape.
    rows = DataProcessingUtils.flatten_nested_fields(rows)  # WHY: flatten for CSV.
    DataExporter.write_with_format_selection(
        rows, filename, api_function_name=api_function_name
    )  # WHY: dispatch CSV/JSON writer.
    return len(rows)  # WHY: count for legacy log line.


def _prompt_site_or_abort(abort_message: str) -> str | None:  # WHY: shared prompt-with-abort helper.
    """Prompt for a site ID and log an abort message when the operator declines."""
    site_id = PromptUtils.select_site()  # WHY: operator picks target site.
    if site_id:  # WHY: happy-path return when a valid site is chosen.
        return site_id  # WHY: valid selection.
    logging.error(abort_message)  # WHY: preserve legacy abort log.
    return None  # WHY: signal caller to bail out.


def _run_dynamic_event_export(
    api_call: Any, data_type: str, description: str
) -> None:  # WHY: dynamic-window event exporter.
    """Run a dynamic-lookback event export using the shared ``_export_data`` helper."""
    hours = TimeUtils.get_dynamic_lookback_hours(_LOOKBACK_DEFAULT_HOURS, _LOOKBACK_MIN_HOURS)  # WHY: compute window.
    TimeUtils.log_dynamic_lookback(description, hours)  # WHY: operator-visible window log.
    SiteExportUtils._export_data(  # WHY: reuse generic exporter path.
        api_call=api_call,
        data_type=data_type,
        sort_key="timestamp",
        duration=f"{hours}h",
    )


def _flatten_channel_planning_dict(
    raw: dict[str, Any], site_id: str
) -> list[dict[str, Any]]:  # WHY: dict shape flattener.
    """Flatten RRM channel-planning dict into per-AP-per-band row list."""
    rows: list[dict[str, Any]] = []  # WHY: accumulate flattened rows.
    for ap_mac, bands in raw.items():  # WHY: iterate one AP at a time.
        if not isinstance(bands, dict):  # WHY: scalar-per-AP path (no band map).
            rows.append({"ap": ap_mac, "site_id": site_id, "value": bands})  # WHY: single-value AP entry.
            continue  # WHY: skip per-band loop when payload was scalar.
        for band, assignment in bands.items():  # WHY: iterate band-assignment pairs.
            row = {"ap": ap_mac, "band": band, "site_id": site_id}  # WHY: base row keys.
            payload = assignment if isinstance(assignment, dict) else {"value": assignment}  # WHY: coerce to dict.
            row.update(payload)  # WHY: merge assignment fields.
            rows.append(row)  # WHY: emit flattened row.
    return rows  # WHY: return the flattened row list.


def _channel_planning_rows_from_raw(
    raw: Any, site_id: str
) -> list[dict[str, Any]]:  # WHY: shape dispatcher for planning payload.
    """Return flattened channel-planning rows from a raw API payload shape."""
    if isinstance(raw, dict):  # WHY: dispatch to dict flattener.
        return _flatten_channel_planning_dict(raw, site_id)  # WHY: dict shape needs bespoke flatten.
    return raw if isinstance(raw, list) else [raw]  # WHY: list stays as-is; scalar wraps.


def _fetch_org_site_name(site_id: str) -> str:  # WHY: cross-endpoint site-name resolver.
    """Resolve a site's human-readable name from the org site listing."""
    response = mistapi.api.v1.orgs.sites.listOrgSites(
        apisession, ConfigUtils.get_cached_or_prompted_org_id()
    )  # WHY: fetch org sites for name resolution.
    sites = mistapi.get_all(response=response, mist_session=apisession)  # WHY: paginate full list.
    return next((site["name"] for site in sites if site["id"] == site_id), site_id)  # WHY: fallback to id.


def _fetch_site_sle_metrics_payload(site_id: str) -> dict[str, Any]:  # WHY: SLE-metrics API fetch helper.
    """Fetch SLE metric availability payload for a site (enabled + supported lists)."""
    response = mistapi.api.v1.sites.sle.listSiteSlesMetrics(
        apisession,
        site_id,
        scope=_INSIGHT_METRIC_SCOPE,
        scope_id=site_id,
    )  # WHY: SLE metric availability endpoint.
    payload = getattr(response, "data", response) or {}  # WHY: tolerate dataclass or dict.
    return payload if isinstance(payload, dict) else {}  # WHY: guard non-dict shapes.


def _build_insight_rows(  # WHY: per-metric availability row builder.
    site_id: str, site_name: str, enabled: list[str], supported: list[str]
) -> list[dict[str, Any]]:
    """Build one insight-availability row per known metric name."""
    metric_names = sorted(set(enabled + supported))  # WHY: union of both lists for row set.
    return [  # WHY: list comprehension emits one row per metric.
        {
            "site_id": site_id,
            "site_name": site_name,
            "metric_name": metric_name,
            "enabled": metric_name in enabled,
            "supported": metric_name in supported,
        }
        for metric_name in metric_names
    ]


def _write_insight_rows(
    rows: list[dict[str, Any]], filename: str, site_name: str
) -> None:  # WHY: insight-rows CSV writer.
    """Write insight rows to CSV, emitting operator messages for empty-payload cases."""
    if rows:  # WHY: happy-path when metric availability payload had data.
        DataExporter.write_with_format_selection(rows, filename)  # WHY: persist rows.
        print(f"! {len(rows)} records exported to data\\{filename}")  # WHY: legacy operator message.
        logging.info(
            "Exported %s site SLE metric insight records to %s", len(rows), filename
        )  # WHY: success audit log.
        return  # WHY: skip empty-file emission when rows exist.
    print(f"! 0 records exported to data\\{filename} (no metrics available)")  # WHY: legacy empty message.
    logging.warning("No site SLE metric insight data available for site %s", site_name)  # WHY: warn on empty payload.
    DataExporter.write_with_format_selection([], filename)  # WHY: still emit empty file for pipeline continuity.


def _resolve_insights_site_name(site_id: str) -> str:  # WHY: insights-flow name resolver with fallback.
    """Resolve site display name for insights export with fallback on API failure."""
    try:
        return _fetch_org_site_name(site_id)  # WHY: happy-path resolution.
    except Exception as exception:  # noqa: BLE001  # WHY: preserve legacy broad-except behavior.
        logging.error("Error getting site name: %s", exception)  # WHY: preserve legacy log line.
        return site_id  # WHY: fall back to raw id.


class SiteExportUtils(SiteInsightsExporter):  # WHY: inherit insights exporters and add site-specific exports.
    """Centralized site-level data export utilities."""

    @staticmethod
    def _resolve_site_name(site_id: str) -> str:  # WHY: class-side name resolver with legacy log format.
        """Resolve human-readable site name from org sites list; fall back to site_id."""
        try:
            logging.info("Fetching org sites to resolve site name for %s", site_id)  # WHY: pre-API log.
            site_name = _fetch_org_site_name(site_id)  # WHY: shared org-name lookup.
            logging.debug("Resolved site_name=%s for site_id=%s", site_name, site_id)  # WHY: post-log.
            return site_name  # WHY: hand back to caller.
        except Exception as e:  # noqa: BLE001  # WHY: preserve legacy broad-except behavior.
            logging.error("Error getting site name: %s", e)  # WHY: preserve legacy error string.
            return site_id  # WHY: fall back to raw site_id.

    @staticmethod
    def _call_site_api(
        api_call: Any, site_id: str, api_kwargs: dict[str, Any]
    ) -> Any:  # WHY: bridge to fetch helper with logs.
        """Invoke site API call, respecting limit-parameter support; return paginated rawdata."""
        logging.debug(
            "Making site-specific API call: %s with site_id: %s", api_call.__name__, site_id
        )  # WHY: pre-call log.
        rawdata = _fetch_site_data(api_call, site_id, api_kwargs)  # WHY: shared fetch + paginate.
        logging.debug("Retrieved rawdata with %s records", len(rawdata) if rawdata else 0)  # WHY: count log.
        return rawdata  # WHY: return paginated rawdata.

    @staticmethod
    def _display_or_log_results(
        data: list[dict[str, Any]], data_type: str, filename: str
    ) -> None:  # WHY: post-export operator feedback.
        """Render debug-mode PrettyTable or log completion summary."""
        if is_debug_mode():  # WHY: debug operators see full table dump.
            _emit_debug_table(data)  # WHY: extract debug rendering into helper.
            return  # WHY: skip completion log after debug render.
        logging.info(
            "Site %s export completed - %s records saved to %s.", data_type, len(data), filename
        )  # WHY: legacy completion line.

    @staticmethod
    def _export_data(api_call: Any, data_type: str, sort_key: str = "name", **api_kwargs: Any) -> None:
        """Generic function to export site-specific data to CSV."""
        logging.info("Starting export of site %s...", data_type)
        site_id = _prompt_site_or_abort("No site selected. Exiting.")  # WHY: shared prompt + abort.
        if site_id is None:
            return  # WHY: abort when operator declines.
        site_name = SiteExportUtils._resolve_site_name(site_id)  # WHY: resolve for filename + log.
        logging.info("Exporting %s for site: %s", data_type, site_name)
        filename = _build_export_filename(data_type, site_name)  # WHY: legacy CamelCase filename.
        try:
            rawdata = SiteExportUtils._call_site_api(api_call, site_id, api_kwargs)  # WHY: fetch site data.
            if rawdata is None:
                logging.warning("! No data returned from API for %s at site %s. Skipping.", data_type, site_name)
                return  # WHY: abort on empty response.
            logging.info("Fetched %s raw records for %s from site %s.", len(rawdata), data_type, site_name)
            data = _prepare_rows(rawdata, sort_key)  # WHY: sort, flatten, escape.
            logging.info("Saving exported site data to %s", filename)  # WHY: pre-save log.
            DataExporter.write_with_format_selection(data, filename)  # WHY: legacy writer entry.
            print(f"! {len(data)} records exported to {_resolve_site_display_path(filename)}")
            logging.info("Site %s data written to %s (%s rows).", data_type, filename, len(data))
            SiteExportUtils._display_or_log_results(data, data_type, filename)  # WHY: display or log.
        except Exception as e:
            logging.error("! Error during site %s export for %s: %s", data_type, site_name, e)
            raise  # WHY: re-raise to preserve legacy bubbling.

    @staticmethod
    def insights() -> None:
        """Export SLE metric availability for a selected site."""
        logging.info("Starting export of site SLE metric insights...")
        site_id = _prompt_site_or_abort("No site selected. Exiting.")  # WHY: shared prompt.
        if site_id is None:
            return  # WHY: abort when operator declines.
        site_name = _resolve_insights_site_name(site_id)  # WHY: resolve with fallback.
        filename = f"SiteSleMetricsInsights_{_sanitize_for_filename(site_name)}.csv"  # WHY: legacy filename.
        try:
            payload = _fetch_site_sle_metrics_payload(site_id)  # WHY: fetch enabled+supported lists.
            rows = _build_insight_rows(  # WHY: assemble one row per metric.
                site_id,
                site_name,
                payload.get("enabled", []),
                payload.get("supported", []),
            )
            _write_insight_rows(rows, filename, site_name)  # WHY: persist and log.
        except Exception as exception:  # noqa: BLE001
            print(f"! Error exporting site SLE metric insights: {exception}")  # WHY: legacy operator msg.
            logging.error("Failed to export site SLE metric insights for site %s: %s", site_name, exception)
            DataExporter.write_with_format_selection([], filename)  # WHY: empty file preserves pipeline.

    @staticmethod
    def _system_events() -> None:
        """Export system events for a site to SiteSystemEvents.csv."""
        _run_dynamic_event_export(  # WHY: shared dynamic-lookback wrapper.
            mistapi.api.v1.sites.events.searchSiteSystemEvents,
            "system events",
            "site system events export",
        )

    @staticmethod
    def _fast_roam_events() -> None:
        """Export fast roam events for a site to SiteFastRoamEvents.csv."""
        _run_dynamic_event_export(  # WHY: shared dynamic-lookback wrapper.
            mistapi.api.v1.sites.events.searchSiteFastRoamEvents,
            "fast roam events",
            "site fast roam events export",
        )

    @staticmethod
    def ospf_stats() -> None:
        """Export OSPF adjacency statistics for a selected site to SiteOspfStats.csv."""
        SiteExportUtils._export_data(  # WHY: generic exporter path.
            api_call=mistapi.api.v1.sites.stats.searchSiteOspfStats,
            data_type="ospf stats",
            sort_key="mac",
        )

    @staticmethod
    def mxedge_upgrade_status() -> None:
        """Export MxEdge upgrade status for a selected site to SiteMxEdgeUpgrades.csv."""
        SiteExportUtils._export_data(  # WHY: generic exporter path.
            api_call=mistapi.api.v1.sites.mxedges.listSiteMxEdgeUpgrades,
            data_type="mxedge upgrade status",
            sort_key="id",
        )

    @staticmethod
    def auto_map_assignment_status() -> None:
        """Export auto-map assignment status for a selected site to SiteAutoMapAssignmentStatus.csv."""
        SiteExportUtils._export_data(  # WHY: generic exporter path.
            api_call=mistapi.api.v1.sites.auto_map_assignment.getSiteAutoMapAssignmentStatus,
            data_type="auto map assignment status",
            sort_key="id",
        )

    @staticmethod
    def site_stats() -> None:
        """Export aggregate health and capacity statistics for a selected site to SiteSiteStats.csv."""
        logging.info("Starting export of site statistics...")
        site_id = _prompt_site_or_abort("No site selected. Aborting site stats export.")  # WHY: shared prompt.
        if site_id is None:
            return  # WHY: abort when operator declines.
        try:
            count = _write_site_report(  # WHY: shared single-endpoint report flow.
                mistapi.api.v1.sites.stats.getSiteStats,
                site_id,
                "SiteSiteStats.csv",
                "getSiteStats",
            )
            logging.info("Exported %d site stats records to %s", count, "SiteSiteStats.csv")
        except Exception as exception:  # noqa: BLE001
            logging.exception("Failed to export site stats: %s", exception)  # WHY: preserve legacy log.

    @staticmethod
    def gateway_metrics() -> None:
        """Export gateway performance metrics summary for a selected site to SiteGatewayMetrics.csv."""
        logging.info("Starting export of site gateway metrics...")
        site_id = _prompt_site_or_abort("No site selected. Aborting gateway metrics export.")  # WHY: shared prompt.
        if site_id is None:
            return  # WHY: abort when operator declines.
        try:
            count = _write_site_report(  # WHY: shared single-endpoint report flow.
                mistapi.api.v1.sites.stats.getSiteGatewayMetrics,
                site_id,
                "SiteGatewayMetrics.csv",
                "getSiteGatewayMetrics",
            )
            logging.info("Exported %d gateway metric records to %s", count, "SiteGatewayMetrics.csv")
        except Exception as exception:  # noqa: BLE001
            logging.exception("Failed to export gateway metrics: %s", exception)  # WHY: preserve legacy log.

    @staticmethod
    def switches_metrics() -> None:
        """Export switch performance metrics summary for a selected site to SiteSwitchesMetrics.csv."""
        logging.info("Starting export of site switches metrics...")
        site_id = _prompt_site_or_abort("No site selected. Aborting switches metrics export.")  # WHY: shared prompt.
        if site_id is None:
            return  # WHY: abort when operator declines.
        try:
            count = _write_site_report(  # WHY: shared single-endpoint report flow.
                mistapi.api.v1.sites.stats.getSiteSwitchesMetrics,
                site_id,
                "SiteSwitchesMetrics.csv",
                "getSiteSwitchesMetrics",
            )
            logging.info("Exported %d switches metric records to %s", count, "SiteSwitchesMetrics.csv")
        except Exception as exception:  # noqa: BLE001
            logging.exception("Failed to export switches metrics: %s", exception)  # WHY: preserve legacy log.

    @staticmethod
    def beacons_stats() -> None:
        """Export BLE beacon statistics for a selected site to SiteBeaconsStats.csv."""
        logging.info("Starting export of site BLE beacon statistics...")
        SiteExportUtils._export_data(  # WHY: generic exporter path.
            api_call=mistapi.api.v1.sites.stats.listSiteBeaconsStats,
            data_type="beacons stats",
            sort_key="id",
        )

    @staticmethod
    def wxrules_usage() -> None:
        """Export WxLAN rule usage statistics for a selected site to SiteWxrulesUsage.csv."""
        logging.info("Starting export of site WxLAN rules usage statistics...")
        site_id = _prompt_site_or_abort("No site selected. Aborting WxRules usage export.")  # WHY: shared prompt.
        if site_id is None:
            return  # WHY: abort when operator declines.
        try:
            count = _write_site_report(  # WHY: shared single-endpoint report flow.
                mistapi.api.v1.sites.stats.getSiteWxRulesUsage,
                site_id,
                "SiteWxrulesUsage.csv",
                "getSiteWxRulesUsage",
            )
            logging.info("Exported %d WxRules usage records to %s", count, "SiteWxrulesUsage.csv")
        except Exception as exception:  # noqa: BLE001
            logging.exception("Failed to export WxRules usage: %s", exception)  # WHY: preserve legacy log.

    @staticmethod
    def assets_stats() -> None:
        """Export asset statistics for a selected site to SiteAssetsStats.csv."""
        logging.info("Starting export of site asset statistics...")
        SiteExportUtils._export_data(  # WHY: generic exporter path.
            api_call=mistapi.api.v1.sites.stats.listSiteAssetsStats,
            data_type="assets stats",
            sort_key="mac",
        )

    @staticmethod
    def current_channel_planning() -> None:
        """Export current RRM channel and power plan per AP radio for a selected site."""
        logging.info("Starting export of site current channel planning (RRM)...")
        site_id = _prompt_site_or_abort("No site selected. Aborting channel planning export.")  # WHY: shared prompt.
        if site_id is None:
            return  # WHY: abort when operator declines.
        try:
            response = mistapi.api.v1.sites.rrm.getSiteCurrentChannelPlanning(apisession, site_id)  # WHY: RRM plan.
            raw = getattr(response, "data", response) or {}  # WHY: tolerate dataclass or dict.
            rows = _channel_planning_rows_from_raw(raw, site_id)  # WHY: normalize payload shape to rows.
            rows = DataProcessingUtils.flatten_nested_fields(rows)  # WHY: flatten for CSV.
            filename = "SiteCurrentChannelPlanning.csv"  # WHY: legacy output filename.
            DataExporter.write_with_format_selection(rows, filename, api_function_name="getSiteCurrentChannelPlanning")
            logging.info("Exported %d channel planning records to %s", len(rows), filename)
        except Exception as exception:  # noqa: BLE001
            logging.exception("Failed to export channel planning: %s", exception)  # WHY: preserve legacy log.

    @staticmethod
    def zone_config_analysis() -> None:
        """Zone, engagement, and occupancy config analysis (Menu #6). Delegates to src.analytics.zone_analyzer."""
        from src.analytics.zone_analyzer import ZoneConfigurationAnalyzer as _ZCA  # noqa: PLC0415

        _ZCA.analyze(  # WHY: reuse zone analyzer for menu #6.
            apisession=apisession,
            get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
            check_stop_fn=ConfigUtils.check_stop_signal,
            all_sites_fn=APICoreFetchUtils.all_sites_with_limit,
            save_data_fn=DataExporter.write_with_format_selection,
        )
