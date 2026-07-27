"""WAN client events export orchestration for a selected Mist site.

Why:
    Mist exposes ``searchSiteWanClientEvents`` (GET
    ``/api/v1/sites/{site_id}/wan_clients/events/search``) — the underlying REST
    path is nested, but the ``mistapi==0.63.3`` SDK exposes the Python callable
    flat under ``mistapi.api.v1.sites.wan_clients`` (issue #1639). MistHelper had
    no menu item wired to it. Spec 899 (issue #1407) requires a read-only menu that
    invokes the endpoint via the ``mistapi`` SDK, prompts the operator with
    ``safe_input`` for the site identifier when unspecified, paginates the
    response with ``mistapi.get_all``, and persists the flattened rows through
    ``DataExporter.write_with_format_selection`` so all three storage backends
    (CSV, SQLite, ArangoDB+Redis) work uniformly. The orchestrator mirrors the
    ``WifiClientsExporter`` structural pattern so future site-scoped search
    endpoints have a consistent template to follow.
"""

from __future__ import annotations  # WHY: postponed annotations keep forward refs cheap under strict typing.

import csv  # WHY: CSV reader for SiteList lookup + writer for the no-data placeholder artifact.
import logging  # WHY: structured operational logging preserves action-trace continuity per Constitution VII.
from dataclasses import dataclass  # WHY: dataclass bundles injected deps + the immutable site stamp payload.
from typing import Any  # WHY: vendor JSON payload shapes remain dynamic dicts of arbitrary value types.

_SITE_LIST_CSV = "SiteList.csv"  # WHY: canonical SiteList filename referenced by cache + prompt + lookup helpers.
_OUTPUT_CSV = "SiteWanClientEvents.CSV"  # WHY: canonical output filename for placeholder and finalize paths.
_API_PAGE_LIMIT = 1000  # WHY: paginated API page size — matches sibling exporters for behavioral parity.
_UNKNOWN_SITE = "Unknown Site"  # WHY: fallback display name preserving stamping semantics on lookup failure.
_API_FUNCTION_NAME = "searchSiteWanClientEvents"  # WHY: operationId used by DataExporter for PK-strategy lookup.
_PLACEHOLDER_HEADER = ["site_id", "site_name", "message"]  # WHY: fixed placeholder schema for downstream readers.
_PLACEHOLDER_MESSAGE = "No WAN client events found"  # WHY: sentinel body used when the endpoint returns empty.
_NO_DATA_TEXT = " No WAN client events found at this site."  # WHY: operator-facing empty-result message text.
_NO_SITE_TEXT = " No site selected."  # WHY: cancel-path operator-facing message matches sibling exporters.


@dataclass(frozen=True, slots=True)
class _SiteStamp:
    """Immutable bundle of site identifiers stamped onto every emitted row.

    Why:
        Every row persisted to CSV/SQLite must carry a stable ``site_id`` and a
        human-readable ``site_name`` so downstream joins (SiteList + events)
        work without additional lookups. Freezing the pair prevents accidental
        mutation during the merge/finalize passes.
    """

    site_id: str  # WHY: canonical UUID stamped for cross-report joins.
    site_name: str  # WHY: human-readable label stamped for operator context.


@dataclass
class WanClientEventsExporter:
    """Orchestrate paginated WAN-client-events export for a selected site.

    Why:
        Encapsulates the workflow behind spec 899 so the CLI menu wrapper stays
        a thin one-liner. Dependencies are injected (not imported) to keep the
        orchestrator testable and to avoid the historic MistHelper import
        cycle. All attributes are collaborator handles matched to the shape
        established by ``WifiClientsExporter``.
    """

    cache_utils: Any  # WHY: injected dep providing SiteList cache generation used before prompting.
    org_site_exporter: Any  # WHY: injected dep supplying the org-scoped site collection for cache seeding.
    prompt_utils: Any  # WHY: injected dep providing the interactive site-selection prompt from CSV.
    file_path_utils: Any  # WHY: injected dep resolving canonical CSV paths under the current backend layout.
    data_processing_utils: Any  # WHY: injected dep flattening + escaping nested vendor payloads before write.
    data_exporter: Any  # WHY: injected dep persisting the final dataset via the configured backend format.
    mistapi_module: Any  # WHY: injected dep exposing the vendor SDK entry points for WAN client events.
    apisession: Any  # WHY: injected dep providing the authenticated mistapi session for API calls.

    def execute(self, site_id: str | None = None) -> None:
        """Run the WAN-client-events export flow for the selected site.

        Why:
            Public entry point wired into the menu dispatcher. Delegates
            site-resolution + fetch + finalize to focused helpers so this method
            stays under the 5-Item Rule limits (<=25 lines, <=5 params).

        Args:
            site_id: Optional site UUID. When omitted, the operator is prompted
                via SiteList CSV picker.
        """
        self._announce_start()  # WHY: emit legacy-style header + start log before any external calls.
        resolved_site_id = self._ensure_site_selected(site_id)  # WHY: resolve or prompt for a site identifier.
        if resolved_site_id is None:  # WHY: operator cancelled — no site to operate on downstream.
            return  # WHY: abort cleanly with no artifacts when site selection cancelled.
        site_name = self._resolve_site_name(resolved_site_id)  # WHY: look up display name for stamping.
        self._announce_fetch(resolved_site_id, site_name)  # WHY: log + print pre-fetch operator text.
        try:
            self._run_export_pipeline(_SiteStamp(resolved_site_id, site_name))  # WHY: delegate guarded flow.
        except Exception as exception:  # WHY: single top-level guard preserves resilient exporter behavior.
            self._log_export_failure(resolved_site_id, exception)  # WHY: preserve traceback + operator message.

    @staticmethod
    def _announce_start() -> None:
        """Emit the header line and start-of-workflow log entry.

        Why:
            Consistent operator-facing UX across all site-scoped exporters — a
            header line before the SiteList prompt and a structured info log
            marking the workflow boundary for tracing.
        """
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logging.info("Export Site WAN Client Events:")
        logging.info("Starting export of site WAN client events...")  # WHY: log workflow start boundary.

    @staticmethod
    def _announce_fetch(site_id: str, site_name: str) -> None:
        """Emit the pre-fetch log line and operator-facing message.

        Why:
            Two-channel notification (structured log + print) lets both NOC
            engineers and log-analysis tooling see progress at the same point
            in the workflow.

        Args:
            site_id: Resolved site UUID being queried.
            site_name: Resolved display name for the site.
        """
        logging.info(
            "Fetching WAN client events for site: %s (ID: %s)", site_name, site_id
        )  # WHY: log before API calls for tracing.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logging.info("! Fetching WAN client events for site: %s", site_name)

    @staticmethod
    def _log_export_failure(site_id: str, exception: BaseException) -> None:
        """Log the exception traceback and print the operator-facing failure line.

        Why:
            Isolates the exception-path emitter so ``execute`` stays
            branch-shallow and testable. Preserves both structured log
            (with traceback) and operator print for parity with siblings.

        Args:
            site_id: Site UUID whose fetch failed.
            exception: The exception raised during the guarded pipeline.
        """
        logging.exception(
            "! Failed to fetch WAN client events for site %s: %s", site_id, exception
        )  # WHY: full traceback log.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logging.error("! Failed to fetch WAN client events: %s", exception)

    def _run_export_pipeline(self, stamp: _SiteStamp) -> None:
        """Execute the fetch + finalize stages under exception-guard protection.

        Why:
            Separating the try-guarded body from ``execute`` keeps the entry
            point's cyclomatic complexity low while still routing every
            downstream failure through the shared failure emitter.

        Args:
            stamp: Immutable site identifiers stamped onto every emitted row.
        """
        events = self._fetch_events(stamp.site_id)  # WHY: paginated fetch of WAN client events for the site.
        if not events:  # WHY: empty-result branch — helper persists sentinel artifact and returns.
            self._write_no_data_placeholder(stamp)  # WHY: sentinel artifact preserves parity with sibling exporters.
            return  # WHY: nothing further to persist when the endpoint returned zero rows.
        stamped = self._stamp_events(events, stamp)  # WHY: attach site_id + site_name to each event row.
        self._finalize_export(stamped)  # WHY: flatten, escape, and persist through the configured backend.

    def _ensure_site_selected(self, site_id: str | None) -> str | None:
        """Ensure SiteList cache exists and resolve site_id (prompt when missing).

        Why:
            The SiteList CSV cache is a precondition for both the interactive
            picker and the display-name lookup. Seeding the cache before
            prompting avoids a redundant round-trip when the operator selects.

        Args:
            site_id: Caller-supplied site UUID; None triggers interactive prompt.

        Returns:
            Resolved site UUID string, or None when the operator cancelled.
        """
        logging.info("Ensuring SiteList.csv cache is available before site resolution")  # WHY: log precondition.
        self.cache_utils.check_and_generate_csv(_SITE_LIST_CSV, self.org_site_exporter.sites)  # WHY: seed cache.
        logging.debug("SiteList.csv cache check/generation completed")  # WHY: after-action confirmation for trace.
        if site_id:
            return site_id  # WHY: caller supplied a site id — no interactive prompt required.
        logging.info("No site_id provided; prompting operator to select a site from CSV")  # WHY: log prompt intent.
        chosen = self.prompt_utils.select_site_id_from_csv(_SITE_LIST_CSV)  # WHY: interactive picker via helper.
        logging.debug("Site selection prompt completed with site_id=%s", chosen)  # WHY: result for traceability.
        if not chosen:
            logging.error(_NO_SITE_TEXT)  # WHY: cancel-path log preserved for operator debugging.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logging.info(_NO_SITE_TEXT)
            return None  # WHY: signal abort to orchestrator so no artifacts are written.
        return chosen  # WHY: resolved site identifier to operate on for the remainder of the workflow.

    def _resolve_site_name(self, site_id: str) -> str:
        """Look up the display name for site_id from SiteList.csv.

        Why:
            Fallback is critical — the exporter must produce output even when
            the SiteList cache is corrupt or missing, so a stable ``Unknown
            Site`` sentinel keeps stamping consistent.

        Args:
            site_id: Site UUID to look up.

        Returns:
            The site's display name, or ``Unknown Site`` on lookup failure.
        """
        try:
            logging.info("Resolving site name from SiteList.csv for site_id=%s", site_id)  # WHY: log lookup start.
            site_list_path = self.file_path_utils.get_csv_path(_SITE_LIST_CSV)  # WHY: canonical CSV path lookup.
            site_name = self._scan_site_list_for_name(site_list_path, site_id)  # WHY: delegate row-scan to helper.
            logging.debug("Resolved site name for site_id=%s to '%s'", site_id, site_name)  # WHY: log resolved.
            return site_name  # WHY: return the resolved (or fallback) name for headers and CSV stamping.
        except Exception as exception:
            logging.warning("! Failed to load site name from SiteList.csv: %s", exception)  # WHY: non-fatal warn log.
            return _UNKNOWN_SITE  # WHY: fallback so downstream stamping stays stable when lookup fails.

    @staticmethod
    def _scan_site_list_for_name(site_list_path: str, site_id: str) -> str:
        """Scan the SiteList CSV once for the row whose id matches site_id.

        Why:
            Streaming a single pass keeps memory bounded on large orgs and
            avoids constructing a full in-memory index for a one-shot lookup.

        Args:
            site_list_path: Filesystem path to the SiteList CSV.
            site_id: Site UUID being resolved.

        Returns:
            Matching site name or the fallback constant.
        """
        with open(site_list_path, encoding="utf-8") as file_handle:  # WHY: open SiteList CSV for name lookup.
            reader = csv.DictReader(file_handle)  # WHY: header-keyed reader for stable column access.
            for row in reader:
                if row.get("id") == site_id:
                    return row.get("name", _UNKNOWN_SITE)  # WHY: matched name with fallback default preserved.
        return _UNKNOWN_SITE  # WHY: no matching row — return fallback so callers rely on a single default source.

    def _fetch_events(self, site_id: str) -> list[dict[str, Any]]:
        """Fetch the full paginated WAN-client-events dataset for the site.

        Why:
            Wraps the two-step SDK dance (first-page request → ``get_all``
            pagination) so callers get a single normalized list. Also handles
            the SDK's habit of returning ``None`` for empty responses.

        Args:
            site_id: Site UUID scoping the search endpoint.

        Returns:
            List of event-row dicts (possibly empty); never ``None``.
        """
        logging.info("Fetching WAN client events data...")  # WHY: log before first-page API call for tracing.
        # WHY: #1639 — mistapi 0.63.3 exposes the callable flat under wan_clients, not under .events.search.
        endpoint = self.mistapi_module.api.v1.sites.wan_clients.searchSiteWanClientEvents
        response = endpoint(self.apisession, site_id, limit=_API_PAGE_LIMIT)  # WHY: first-page API call.
        results = self.mistapi_module.get_all(response=response, mist_session=self.apisession)  # WHY: paginate.
        count = len(results) if results else 0  # WHY: capture size once for both log line and return value.
        logging.debug("Fetched %d WAN client event records", count)  # WHY: after-action size for trace.
        return results or []  # WHY: normalize None to empty list so caller logic stays branch-free.

    def _write_no_data_placeholder(self, stamp: _SiteStamp) -> None:
        """Write the no-data sentinel CSV when the endpoint returns nothing.

        Why:
            Downstream tooling expects an artifact after every export run;
            emitting a fixed-schema sentinel row is the least-surprising way
            to satisfy that contract while still signalling "no upstream data".

        Args:
            stamp: Site identifiers used to populate the sentinel row.
        """
        logging.warning(_NO_DATA_TEXT)  # WHY: preserve empty-result log severity + text from sibling exporters.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logging.info(_NO_DATA_TEXT)
        logging.info("Writing no-data placeholder CSV for %s", _OUTPUT_CSV)  # WHY: log before placeholder write.
        output_path = self.file_path_utils.get_csv_path(_OUTPUT_CSV)  # WHY: resolve canonical output path.
        with open(output_path, "w", newline="", encoding="utf-8") as file_handle:
            writer = csv.writer(file_handle)  # WHY: plain CSV writer for the fixed placeholder schema.
            writer.writerow(_PLACEHOLDER_HEADER)  # WHY: emit header row expected by downstream readers.
            writer.writerow([stamp.site_id, stamp.site_name, _PLACEHOLDER_MESSAGE])  # WHY: emit sentinel body row.
        logging.debug("No-data placeholder CSV written to %s", output_path)  # WHY: after-action confirmation.

    @staticmethod
    def _stamp_events(
        events: list[dict[str, Any]],
        stamp: _SiteStamp,
    ) -> list[dict[str, Any]]:
        """Stamp site identifiers on every event row in place.

        Why:
            The SDK returns raw event rows without site context; downstream
            joins and per-site aggregations rely on both the UUID (stable) and
            the display name (human readability).

        Args:
            events: Raw event rows returned by the SDK.
            stamp: Site identifiers to stamp onto each row.

        Returns:
            The same list, mutated in place, returned for pipeline chaining.
        """
        logging.info("Stamping site identifiers on %d event rows", len(events))  # WHY: log before stamping loop.
        for event in events:
            event["site_id"] = stamp.site_id  # WHY: stamp site UUID for downstream reporting consistency.
            event["site_name"] = stamp.site_name  # WHY: stamp human-readable site name for operator context.
        logging.debug("Completed stamping site identifiers on event rows")  # WHY: after-action confirmation.
        return events  # WHY: return mutated list for chained finalize call.

    def _finalize_export(self, events: list[dict[str, Any]]) -> None:
        """Flatten, escape, write to backend, and print operator success summary.

        Why:
            Isolating the finalize stage keeps the pipeline branch-shallow and
            centralizes the backend-write call so future PK-strategy or
            format-selection changes only need to touch one place.

        Args:
            events: Site-stamped event rows ready for flattening + persistence.
        """
        sanitized = self._flatten_and_sanitize(events)  # WHY: normalize nested + multiline fields for CSV write.
        self._write_final_output(sanitized)  # WHY: persist the final processed records via configured backend.
        self._print_success_summary(sanitized)  # WHY: operator success text with record count for confirmation.

    def _flatten_and_sanitize(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Flatten nested fields and escape multiline values for tabular output.

        Why:
            The event payloads contain nested objects and multiline strings
            (for example, diagnostic details) that break naive CSV writers. Reusing
            the shared helpers guarantees identical sanitization semantics
            across all site-scoped exporters.

        Args:
            events: Site-stamped raw event rows.

        Returns:
            CSV-safe flattened rows ready for the backend writer.
        """
        logging.info("Flattening nested WAN client event fields for export")  # WHY: log before flatten action.
        flattened = self.data_processing_utils.flatten_nested_fields(events)  # WHY: flatten nested dicts.
        logging.debug("Flatten transformation produced %d rows", len(flattened))  # WHY: after-action row count.
        logging.info("Escaping multiline fields for CSV-safe output")  # WHY: log before sanitize action.
        sanitized = self.data_processing_utils.escape_multiline(flattened)  # WHY: escape multiline values.
        logging.debug("Multiline escaping completed for %d rows", len(sanitized))  # WHY: after-action size.
        return sanitized  # WHY: return CSV-safe rows for the final write stage.

    def _write_final_output(self, sanitized: list[dict[str, Any]]) -> None:
        """Persist the sanitized rows through the configured data exporter backend.

        Why:
            Passing ``api_function_name`` lets the exporter consult
            ``ENDPOINT_PRIMARY_KEY_STRATEGIES`` and pick the correct upsert
            strategy (composite ``mac`` + ``timestamp``), which is what
            prevents duplicate rows across repeated runs against SQLite.

        Args:
            sanitized: CSV-safe rows for the backend writer.
        """
        logging.info("Writing %s to configured output backend", _OUTPUT_CSV)  # WHY: log before final write.
        self.data_exporter.write_with_format_selection(
            sanitized, _OUTPUT_CSV, api_function_name=_API_FUNCTION_NAME
        )  # WHY: persist with PK-strategy hint so SQLite upserts by mac+timestamp.
        logging.debug("%s write completed successfully", _OUTPUT_CSV)  # WHY: after-action write confirmation.

    @staticmethod
    def _print_success_summary(sanitized: list[dict[str, Any]]) -> None:
        """Emit the operator-facing success summary block.

        Why:
            Terminal parity with the WifiClientsExporter — every site-scoped
            exporter should print a matching "! X exported to Y" success line
            so operators reading logs can pattern-match across menu options.

        Args:
            sanitized: Final CSV-safe rows persisted to the backend.
        """
        total_records = len(sanitized)  # WHY: total row count for summary reporting.
        logging.info(
            "! WAN client events exported to %s (%d records)", _OUTPUT_CSV, total_records
        )  # WHY: structured log mirrors the operator print block for tracing parity.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logging.info("! WAN client events exported to %s", _OUTPUT_CSV)
        logging.info("   %d WAN client event records", total_records)
