"""Site client insights export orchestration extracted from MistHelper high-CC offender."""

from __future__ import annotations  # WHY: PEP 563 postponed annotations for forward Any typing

import importlib  # WHY: Late-bound MistHelper import avoids circular src->MistHelper
import logging  # WHY: Structured trace for workflow start/abort events
from dataclasses import dataclass  # WHY: Frozen slotted state bundles keep execute() CC low
from types import SimpleNamespace  # WHY: SimpleNamespace preserves the deps shape tests already rely on
from typing import Any  # WHY: MistHelper collaborators are dynamic attrs typed loosely

# Module-level constants: banners, log messages, prompts, tag keys, filename template.
# Extracting them keeps every method free of repeated string literals so CC stays low.
_MIST_MODULE = "MistHelper"  # WHY: Single source for the late-import target
_BANNER = "Export Site Client Insights:"  # WHY: User-facing workflow banner
_MSG_START = "Starting export of site client insights..."  # WHY: Log message: workflow start
_MSG_REFRESH = "! Refreshing available insight metrics from Mist API..."  # WHY: User-facing metric refresh notice
_MSG_NO_SITE = "No site selected. Exiting."  # WHY: Log message: abort when no site chosen
_MSG_SKIP_EMPTY = "! No client input provided. Skipping client insights export."  # WHY: User skip message
_MSG_NO_MAC = "! Could not determine client MAC address."  # WHY: User-facing empty-MAC message
_MSG_INVALID_MAC_TMPL = "! Invalid client MAC address format: {mac}"  # WHY: User-facing invalid-MAC template
_MSG_INVALID_MAC_LOG = "Invalid client MAC address format provided for client insights: %s"  # WHY: Log template
_MSG_NO_METRICS = "! No metrics found for client scope. Check ConstInsightMetrics.csv file."  # WHY: User misconfig msg
_MSG_NO_METRICS_LOG = "No client-scope metrics found in const insight metrics"  # WHY: Log misconfig message
_MSG_RETRIEVING_TMPL = "! Retrieving {count} different client insight metrics for selected client..."  # WHY: Progress
_MSG_PROMPT_HEADER = "\nEnter client MAC address or index number (or press Enter to skip):"  # WHY: Prompt header
_PROMPT_CLIENT = "Client MAC/Index: "  # WHY: Client selection prompt text
_CTX_CLIENT = "site_client_insights_selection"  # WHY: safe_input context tag
_MSG_ERROR_TMPL = "! Error exporting client insights: {error}"  # WHY: User-facing top-level error template
_MSG_ERROR_LOG = "Failed to export client insights at %s: %s"  # WHY: Log template for top-level failure
_MSG_FOUND_TMPL = "\n! Found {count} clients at site {site}"  # WHY: Client-count summary template
_MSG_PREVIEW_HEADER = "Recent clients (showing first 5):"  # WHY: Preview header text
_MSG_PREVIEW_ROW_TMPL = "  [{index}] MAC: {mac}, Hostname: {hostname}, Last seen: {last_seen}"  # WHY: Preview row
_MSG_NO_CLIENTS_TMPL = "! No clients found at site {site}"  # WHY: Empty-list message template
_MSG_CLIENT_FETCH_FAIL = "Could not retrieve client list: %s"  # WHY: Log template for client-list failure
_MSG_INVALID_INDEX_TMPL = "! Invalid index: {value}"  # WHY: User invalid-index template
_MSG_INDEX_RANGE_TMPL = "! Invalid index {index}. Must be between 0 and {max_index}"  # WHY: Range-error template
_MSG_SELECTED_TMPL = "! Selected client by index: {mac}"  # WHY: Selection echo template
_MSG_METRIC_OK = "Retrieved client insight data for metric: %s"  # WHY: Log template for successful metric
_MSG_METRIC_EMPTY = "No data available for client metric: %s"  # WHY: Log template for empty metric result
_MSG_METRIC_FAIL = "Failed to get client insight data for metric %s: %s"  # WHY: Log template for metric failure
_MSG_EXPORT_OK_TMPL = "! {count} client insight metrics exported to {filename}"  # WHY: Export success user template
_MSG_EXPORT_OK_LOG = "Exported %s client insight metrics at %s to %s"  # WHY: Log template for successful export
_MSG_EXPORT_EMPTY_TMPL = "! 0 client insights exported to {filename} (no data available)"  # WHY: Empty export template
_MSG_EXPORT_EMPTY_LOG = "No client insight data available at %s"  # WHY: Log template for empty export
_FILENAME_TMPL = "SiteClientInsights_{site}_{mac}.csv"  # WHY: Output filename template
_CLIENT_SCOPE = "client"  # WHY: InsightMetricsUtils scope name for client metrics
_KEY_MAC = "mac"  # WHY: Client dict key for MAC address
_KEY_HOSTNAME = "hostname"  # WHY: Client dict key for hostname
_KEY_LAST_SEEN = "last_seen"  # WHY: Client dict key for last-seen timestamp
_KEY_ID = "id"  # WHY: Site dict key for the site id
_KEY_NAME = "name"  # WHY: Site dict key for the site name
_KEY_METRIC_TYPE = "metric_type"  # WHY: Insight record tag: metric name
_KEY_SITE_ID = "site_id"  # WHY: Insight record tag: site id
_KEY_SITE_NAME = "site_name"  # WHY: Insight record tag: site name
_KEY_CLIENT_MAC = "client_mac"  # WHY: Insight record tag: client MAC
_UNKNOWN = "Unknown"  # WHY: Placeholder for missing client attributes
_PREVIEW_LIMIT = 5  # WHY: Number of clients to show in the preview


def _resolve_runtime_dependencies() -> SimpleNamespace:
    """Resolve MistHelper runtime dependencies without static cross-module imports."""
    misthelper_module = importlib.import_module(_MIST_MODULE)  # WHY: Late import avoids circular src->MistHelper
    return SimpleNamespace(
        mistapi=misthelper_module.mistapi,
        apisession=misthelper_module.apisession,
        InsightMetricsUtils=misthelper_module.InsightMetricsUtils,
        ConstDefinitionsExporter=misthelper_module.ConstDefinitionsExporter,  # WHY: Canonical metrics refresh exporter
        PromptUtils=misthelper_module.PromptUtils,
        InputUtils=misthelper_module.InputUtils,
        EnhancedSSHRunner=misthelper_module.EnhancedSSHRunner,
        DataProcessingUtils=misthelper_module.DataProcessingUtils,
        DataExporter=misthelper_module.DataExporter,
        SiteClientExporter=misthelper_module.SiteClientExporter,
    )


@dataclass(frozen=True, slots=True)
class _SiteContext:
    """Frozen bundle of resolved site identifiers so helper signatures stay narrow."""

    site_id: str  # WHY: Raw site id used for API calls
    site_name: str  # WHY: Human-readable display name (falls back to id)
    sanitized_site_name: str  # WHY: Filesystem-safe form for the output filename


@dataclass(frozen=True, slots=True)
class _ExportContext:
    """Frozen bundle of state carried into the collect+export phase."""

    site_id: str  # WHY: Raw site id used for insight metric queries
    site_name: str  # WHY: Human-readable display name (for user output and traces)
    client_mac: str  # WHY: Normalized client MAC used for insight metric queries
    filename: str  # WHY: Target export filename (used on success and on failure fallback)


def _emit_preview_rows(clients: list[dict[str, Any]], site_name: str) -> None:
    """Print the client-count summary and the first _PREVIEW_LIMIT rows (kept CC low)."""
    print(_MSG_FOUND_TMPL.format(count=len(clients), site=site_name))  # WHY: Summary count line
    print(_MSG_PREVIEW_HEADER)  # WHY: Preview header
    for index, client in enumerate(clients[:_PREVIEW_LIMIT]):  # WHY: Show only the first few rows
        print(
            _MSG_PREVIEW_ROW_TMPL.format(
                index=index,
                mac=client.get(_KEY_MAC, _UNKNOWN),
                hostname=client.get(_KEY_HOSTNAME, _UNKNOWN),
                last_seen=client.get(_KEY_LAST_SEEN, _UNKNOWN),
            )
        )  # WHY: One preview row per iteration


def _tag_insight_record(
    record: dict[str, Any],
    metric: str,
    context: _ExportContext,
) -> dict[str, Any]:
    """Attach metric/site/client tags to an insight record so exports stay self-describing."""
    record[_KEY_METRIC_TYPE] = metric  # WHY: Tag the metric type
    record[_KEY_SITE_ID] = context.site_id  # WHY: Tag the site id
    record[_KEY_SITE_NAME] = context.site_name  # WHY: Tag the site name
    record[_KEY_CLIENT_MAC] = context.client_mac  # WHY: Tag the client MAC
    return record  # WHY: Same object, now enriched with tag keys


class SiteClientInsightsService:
    """Owns site client insights workflow formerly embedded in SiteClientExporter."""

    @staticmethod
    def _resolve_site_name(deps: SimpleNamespace, site_id: str) -> str:
        """Resolve the human-readable site name, falling back to the site id on failure."""
        try:  # WHY: Site name lookup is best-effort; any failure falls back to the id
            response = deps.mistapi.api.v1.sites.listSites(deps.apisession, site_id)  # WHY: Fetch site metadata
            sites = deps.mistapi.get_all(response=response, mist_session=deps.apisession)  # WHY: Page all sites
            return next((site[_KEY_NAME] for site in sites if site[_KEY_ID] == site_id), site_id)  # WHY: Match id->name
        except Exception:  # WHY: Any API/shape error - fall back to the raw id
            return site_id  # WHY: Use the id as the display name

    @staticmethod
    def _list_and_display_clients(deps: SimpleNamespace, site_id: str, site_name: str) -> list[dict[str, Any]]:
        """Fetch wireless clients for the site and print a short preview; return the client list."""
        try:  # WHY: Client listing is best-effort; failures are warned and yield an empty list
            response = deps.mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(
                deps.apisession, site_id
            )  # WHY: Query wireless clients for the site
            clients = deps.mistapi.get_all(response=response, mist_session=deps.apisession) or []  # WHY: Page clients
        except Exception as exception:  # WHY: Retrieval failed - warn and return an empty list
            logging.warning(_MSG_CLIENT_FETCH_FAIL, exception)  # WHY: Trace the failure
            return []  # WHY: Empty list on retrieval failure
        if clients:  # WHY: Found at least one client - show a short preview
            _emit_preview_rows(clients, site_name)  # WHY: Delegate preview emission
        else:  # WHY: No clients returned for the site
            print(_MSG_NO_CLIENTS_TMPL.format(site=site_name))  # WHY: Inform the user
        return clients  # WHY: Hand back whatever clients were found (possibly empty)

    @staticmethod
    def _resolve_client_mac(client_input: str, clients: list[dict[str, Any]]) -> str | None:
        """Resolve a client MAC from raw input; return None to abort (message already printed)."""
        if not client_input.isdigit():  # WHY: Non-numeric input is treated as a literal MAC string
            return client_input  # WHY: Use the input directly as the MAC
        try:  # WHY: Numeric input is an index into the displayed client list
            index = int(client_input)  # WHY: Parse the index
        except (ValueError, IndexError):  # WHY: Parsing failed despite isdigit (defensive)
            print(_MSG_INVALID_INDEX_TMPL.format(value=client_input))  # WHY: Inform the user
            return None  # WHY: Abort - message already printed
        if not (0 <= index < len(clients)):  # WHY: Index must reference an existing client
            print(_MSG_INDEX_RANGE_TMPL.format(index=index, max_index=len(clients) - 1))  # WHY: Inform the user
            return None  # WHY: Abort - message already printed
        client_mac = str(clients[index].get(_KEY_MAC, ""))  # WHY: Resolve MAC (may be empty)
        print(_MSG_SELECTED_TMPL.format(mac=client_mac))  # WHY: Echo the selection
        return client_mac  # WHY: Return the resolved MAC (possibly empty string)

    @staticmethod
    def _fetch_single_metric(deps: SimpleNamespace, context: _ExportContext, metric: str) -> dict[str, Any] | None:
        """Fetch one client-scope insight metric; return the tagged record or None on empty/failure."""
        try:  # WHY: Per-metric failures are non-fatal and skip to the next metric
            response = deps.mistapi.api.v1.sites.insights.getSiteInsightMetricsForClient(
                deps.apisession, context.site_id, context.client_mac, metrics=metric
            )  # WHY: Query one client insight metric
        except Exception as metric_error:  # WHY: Per-metric API failure - log and continue
            logging.debug(_MSG_METRIC_FAIL, metric, metric_error)  # WHY: Trace the failure
            return None  # WHY: Skip to the next metric
        client_insight_data = getattr(response, "data", response) or {}  # WHY: Normalize to the payload (or empty)
        if not client_insight_data:  # WHY: Metric returned no data
            logging.debug(_MSG_METRIC_EMPTY, metric)  # WHY: Trace empty result
            return None  # WHY: No record to accumulate
        logging.debug(_MSG_METRIC_OK, metric)  # WHY: Trace success
        return _tag_insight_record(client_insight_data, metric, context)  # WHY: Return the tagged record

    @classmethod
    def _collect_client_metrics(
        cls, deps: SimpleNamespace, context: _ExportContext, client_metrics: list[str]
    ) -> tuple[list[dict[str, Any]], int]:
        """Fetch every client-scope insight metric; return (collected records, retrieved count)."""
        all_client_data: list[dict[str, Any]] = []  # WHY: Accumulator for tagged records
        for metric in client_metrics:  # WHY: Iterate every client-scope metric
            record = cls._fetch_single_metric(deps, context, metric)  # WHY: Fetch one metric (None on empty/failure)
            if record is not None:  # WHY: Only accumulate metrics that returned data
                all_client_data.append(record)  # WHY: Accept the tagged record
        return all_client_data, len(all_client_data)  # WHY: Collected records plus success count

    @staticmethod
    def _export_client_data(
        deps: SimpleNamespace,
        all_client_data: list[dict[str, Any]],
        metrics_retrieved: int,
        filename: str,
        site_name: str,
    ) -> None:
        """Flatten and export collected client insight data, or write an empty file when none."""
        if not all_client_data:  # WHY: No data collected for any metric - write empty for consistency
            print(_MSG_EXPORT_EMPTY_TMPL.format(filename=filename))  # WHY: User summary
            logging.warning(_MSG_EXPORT_EMPTY_LOG, site_name)  # WHY: Warn on empty run
            deps.DataExporter.write_with_format_selection([], filename)  # WHY: Write empty export file
            return  # WHY: Empty-case complete
        processed = deps.DataProcessingUtils.flatten_nested_fields(all_client_data)  # WHY: Flatten nested structures
        processed = deps.DataProcessingUtils.escape_multiline(processed)  # WHY: Escape multiline fields for CSV
        deps.DataExporter.write_with_format_selection(processed, filename)  # WHY: Write the export file
        print(_MSG_EXPORT_OK_TMPL.format(count=metrics_retrieved, filename=filename))  # WHY: User summary
        logging.info(_MSG_EXPORT_OK_LOG, metrics_retrieved, site_name, filename)  # WHY: Trace successful export

    @classmethod
    def _prepare_site_context(cls, deps: SimpleNamespace, site_id: str) -> _SiteContext:
        """Resolve site name + sanitized form and bundle them for downstream helpers."""
        site_name = cls._resolve_site_name(deps, site_id)  # WHY: Resolve display name (falls back to id)
        sanitized = deps.EnhancedSSHRunner.sanitize_filename(site_name or site_id)  # WHY: Filesystem-safe name
        return _SiteContext(site_id=site_id, site_name=site_name, sanitized_site_name=sanitized)  # WHY: Bundle state

    @staticmethod
    def _read_client_input(deps: SimpleNamespace) -> str:
        """Prompt for the client MAC/index and return the trimmed input string."""
        print(_MSG_PROMPT_HEADER)  # WHY: Prompt header
        raw = deps.InputUtils.safe_input(_PROMPT_CLIENT, context=_CTX_CLIENT)  # WHY: Read raw client selection
        return str(raw).strip()  # WHY: str-cast narrows Any for downstream str consumers

    @classmethod
    def _resolve_normalized_mac(
        cls, deps: SimpleNamespace, client_input: str, clients: list[dict[str, Any]]
    ) -> str | None:
        """Resolve MAC from input, validate/normalize; return the normalized MAC or None to abort."""
        client_mac = cls._resolve_client_mac(client_input, clients)  # WHY: Resolve MAC from input (None = abort)
        if client_mac is None:  # WHY: Invalid index/value - helper already printed the reason
            return None  # WHY: Abort silently
        if not client_mac:  # WHY: Resolved to an empty MAC (selected client had no MAC)
            print(_MSG_NO_MAC)  # WHY: Inform the user
            return None  # WHY: Abort
        normalized = deps.SiteClientExporter._normalize_client_mac_or_none(client_mac)  # WHY: Validate/normalize
        if not normalized:  # WHY: MAC failed format validation
            print(_MSG_INVALID_MAC_TMPL.format(mac=client_mac))  # WHY: Inform the user
            logging.error(_MSG_INVALID_MAC_LOG, client_mac)  # WHY: Trace the failure
            return None  # WHY: Abort
        return str(normalized)  # WHY: Normalized MAC (str-cast narrows Any for downstream str formatting)

    @staticmethod
    def _load_client_metrics_or_empty(deps: SimpleNamespace, filename: str) -> list[str] | None:
        """Return the configured client-scope metric list, or None (empty file written) if none."""
        client_metrics = deps.InsightMetricsUtils.get_by_scope(_CLIENT_SCOPE)  # WHY: Client-scope metric list
        if client_metrics:  # WHY: At least one metric configured
            return list(client_metrics)  # WHY: Freeze return type (list[str])
        print(_MSG_NO_METRICS)  # WHY: Inform the user of misconfiguration
        logging.error(_MSG_NO_METRICS_LOG)  # WHY: Trace the misconfiguration
        deps.DataExporter.write_with_format_selection([], filename)  # WHY: Write an empty export for consistency
        return None  # WHY: Signal abort (empty file already written)

    @classmethod
    def _run_collect_and_export(cls, deps: SimpleNamespace, context: _ExportContext, client_metrics: list[str]) -> None:
        """Guarded collect+export path; writes an empty file if the top-level fetch fails."""
        try:  # WHY: Guard the fetch+export so failures still write an empty file
            all_client_data, metrics_retrieved = cls._collect_client_metrics(
                deps, context, client_metrics
            )  # WHY: Fetch every client-scope metric
            cls._export_client_data(
                deps, all_client_data, metrics_retrieved, context.filename, context.site_name
            )  # WHY: Export results
        except Exception as exception:  # WHY: Unexpected top-level failure
            print(_MSG_ERROR_TMPL.format(error=exception))  # WHY: User-facing error
            logging.error(_MSG_ERROR_LOG, context.site_name, exception)  # WHY: Trace the failure
            deps.DataExporter.write_with_format_selection([], context.filename)  # WHY: Write empty export on failure

    @staticmethod
    def _print_intro_and_refresh(deps: SimpleNamespace) -> None:
        """Emit the banner + refresh notice and run the canonical metric refresh."""
        print(_BANNER)  # WHY: User-facing banner
        logging.info(_MSG_START)  # WHY: Trace workflow start
        print(_MSG_REFRESH)  # WHY: Inform about the metric refresh
        deps.ConstDefinitionsExporter(deps.apisession).export_all()  # WHY: Regenerate ConstInsightMetrics.csv

    @classmethod
    def _resolve_export_context(cls, deps: SimpleNamespace, site_id: str) -> _ExportContext | None:
        """Resolve site context + client + normalized MAC into an _ExportContext; None aborts."""
        site_context = cls._prepare_site_context(deps, site_id)  # WHY: Resolve display + sanitized name
        clients = cls._list_and_display_clients(
            deps, site_context.site_id, site_context.site_name
        )  # WHY: Fetch + preview
        client_input = cls._read_client_input(deps)  # WHY: Prompt for the client selection
        if not client_input:  # WHY: User pressed Enter to skip
            print(_MSG_SKIP_EMPTY)  # WHY: Inform the user
            return None  # WHY: Abort the workflow
        normalized_mac = cls._resolve_normalized_mac(deps, client_input, clients)  # WHY: Resolve normalized MAC
        if normalized_mac is None:  # WHY: Any of the MAC guards fired (message already printed)
            return None  # WHY: Abort the workflow
        filename = _FILENAME_TMPL.format(
            site=site_context.sanitized_site_name, mac=normalized_mac.replace(":", "")
        )  # WHY: MAC without separators in filename
        return _ExportContext(
            site_id=site_context.site_id,
            site_name=site_context.site_name,
            client_mac=normalized_mac,
            filename=filename,
        )  # WHY: Bundle collect+export state

    @classmethod
    def execute(cls) -> None:
        """Run site client insights export workflow."""
        deps = _resolve_runtime_dependencies()  # WHY: Resolve MistHelper collaborators at call time
        cls._print_intro_and_refresh(deps)  # WHY: Banner + metric refresh
        site_id = deps.PromptUtils.select_site()  # WHY: Prompt for the target site
        if not site_id:  # WHY: No site chosen - nothing to export
            logging.error(_MSG_NO_SITE)  # WHY: Trace the early exit
            return  # WHY: Abort the workflow
        context = cls._resolve_export_context(deps, site_id)  # WHY: Resolve site + client + filename
        if context is None:  # WHY: Any prompt/guard aborted (message already printed)
            return  # WHY: Abort the workflow
        client_metrics = cls._load_client_metrics_or_empty(deps, context.filename)  # WHY: Load metric list
        if client_metrics is None:  # WHY: No metrics configured (empty file already written)
            return  # WHY: Abort the workflow
        print(_MSG_RETRIEVING_TMPL.format(count=len(client_metrics)))  # WHY: Progress info line
        cls._run_collect_and_export(deps, context, client_metrics)  # WHY: Guarded fetch + export
