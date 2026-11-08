"""Workflow extraction for site WiFi client export orchestration."""

from __future__ import annotations  # WHY: postponed annotations keep forward refs cheap under strict typing.

import csv  # WHY: CSV reader for SiteList lookup and writer for the no-data placeholder artifact.
import logging  # WHY: structured operational logging preserves action-trace continuity with legacy flow.
from dataclasses import dataclass  # WHY: dataclass bundles both the injected deps and the immutable stamp payload.
from typing import Any  # WHY: vendor JSON payload shapes remain dynamic dicts of arbitrary value types.

from requests.exceptions import RequestException  # WHY: identify transport failures that can leave a partial read.

from src.mist.access.api.response_integrity import (
    ResponseIntegrityChecker,  # WHY: detect JSON parse failures swallowed by the mistapi SDK.
)

logger = logging.getLogger(__name__)  # Use a module logger for non-exception export messages.

_SITE_LIST_CSV = "SiteList.csv"  # WHY: canonical SiteList filename referenced by cache + prompt + lookup helpers.
_OUTPUT_CSV = "SiteWiFiClients.CSV"  # WHY: canonical output filename shared by placeholder and finalize paths.
_API_PAGE_LIMIT = 1000  # WHY: paginated API page size — matches legacy behavior for parity with prior exporter.
_HTTP_ERROR_MIN = 400  # WHY: HTTP 4xx and 5xx responses cannot prove an empty WiFi result.
_MISSING_ATTRIBUTE = object()  # WHY: distinguish absent raw_data from a native empty response body.
_UNKNOWN_SITE = "Unknown Site"  # WHY: fallback display name preserving legacy stamp semantics on lookup failure.
_SOURCE_CLIENT = "client"  # WHY: provenance marker distinguishing client-origin rows in downstream tooling.
_SOURCE_SESSION_ONLY = "session_only"  # WHY: provenance marker distinguishing orphan-session-origin rows.
_PLACEHOLDER_HEADER = ["site_id", "site_name", "message"]  # WHY: fixed schema header expected by downstream readers.
_PLACEHOLDER_MESSAGE = "No WiFi clients or sessions found"  # WHY: sentinel row body used when neither dataset exists.
_NO_DATA_TEXT = " No WiFi clients or sessions found at this site."  # WHY: legacy operator-facing empty-result text.
_NO_POST_MERGE_TEXT = " No data to export after processing."  # WHY: legacy defensive empty-post-merge message.
_NO_SITE_TEXT = " No site selected."  # WHY: legacy cancel-path operator-facing message preserved verbatim.
_META_KEYS = frozenset({"site_id", "site_name", "data_source", "session_count"})  # WHY: keys never namespace-prefixed.


@dataclass(frozen=True, slots=True)
class _SiteStamp:  # WHY: immutable value bundle carrying site identifiers stamped onto every emitted row.
    """Immutable bundle carrying the site identifiers stamped onto every emitted row."""

    site_id: str  # WHY: canonical UUID stamped for cross-report joins.
    site_name: str  # WHY: human-readable label stamped for operator context.


@dataclass(slots=True)
class _PageReadResult:  # WHY: retain collected rows and mark a read that stopped before its final page.
    """Hold records from successful pages and identify an interrupted later-page read."""

    records: list[dict[str, Any]]  # WHY: preserve each validated page for export or failure reporting.
    is_partial: bool = False  # WHY: distinguish a timed-out read from a complete empty result.


@dataclass
class WifiClientsExporter:  # WHY: orchestrator dataclass — attributes act as injected collaborator handles.
    """Export merged wireless client and session data with legacy-compatible output behavior."""

    cache_utils: Any  # WHY: injected dep providing SiteList cache generation used before prompting.
    org_site_exporter: Any  # WHY: injected dep supplying the org-scoped site collection for cache seeding.
    prompt_utils: Any  # WHY: injected dep providing the interactive site-selection prompt from CSV.
    file_path_utils: Any  # WHY: injected dep resolving canonical CSV paths under the current backend layout.
    data_processing_utils: Any  # WHY: injected dep flattening + escaping nested vendor payloads before write.
    data_exporter: Any  # WHY: injected dep persisting the final dataset via the configured backend format.
    mistapi_module: Any  # WHY: injected dep exposing the vendor SDK entry points for wireless client APIs.
    apisession: Any  # WHY: injected dep providing the authenticated mistapi session for API calls.

    def execute(self, site_id: str | None = None) -> None:  # WHY: public entry point invoked by the CLI layer.
        """Run the extracted WiFi client export flow preserving output and side effects."""
        self._announce_start()  # WHY: emit legacy header + start log before any external calls.
        resolved_site_id = self._ensure_site_selected(site_id)  # WHY: resolve or prompt for a site identifier.
        if resolved_site_id is None:  # WHY: operator cancelled — no site to operate on downstream.
            return  # WHY: operator cancelled site selection — abort cleanly with no artifacts.
        site_name = self._resolve_site_name(resolved_site_id)  # WHY: look up display name for headers + stamping.
        self._announce_fetch(resolved_site_id, site_name)  # WHY: log + print legacy fetch-start operator text.
        try:
            self._run_export_pipeline(_SiteStamp(resolved_site_id, site_name))  # WHY: delegate the try-guarded flow.
        except Exception as exception:  # WHY: single top-level guard preserves legacy resilient behavior.
            self._log_export_failure(resolved_site_id, exception)  # WHY: preserve traceback + operator message.

    @staticmethod
    def _announce_start() -> None:  # WHY: header + start-log emitter kept pure-static for testability.
        """Emit the legacy header line and start-of-workflow log entry."""
        # WHY: preserve legacy header text so operator experience is identical. Route via logger for capture.
        logger.info("Export Site WiFi Clients:")
        logger.info("Starting export of site WiFi clients...")  # WHY: log workflow start boundary for tracing.

    @staticmethod
    def _announce_fetch(site_id: str, site_name: str) -> None:  # WHY: pre-fetch messaging isolated for reuse.
        """Emit the pre-fetch log line and legacy operator-facing message."""
        logger.info("Fetching WiFi clients for site: %s (ID: %s)", site_name, site_id)  # WHY: log before API calls.
        # WHY: preserve legacy fetch-start operator text. Route via logger for capture/redirection.
        logger.info("! Fetching WiFi clients for site: %s", site_name)

    @staticmethod
    def _log_export_failure(site_id: str, exception: BaseException) -> None:  # WHY: exception-path emitter.
        """Log the exception traceback and print the legacy operator-facing failure line."""
        logger.exception("! Failed to fetch WiFi data for site %s: %s", site_id, exception)  # WHY: traceback log.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("! Failed to fetch WiFi data: %s", exception)  # WHY: preserve legacy operator-facing error output.

    def _run_export_pipeline(self, stamp: _SiteStamp) -> None:  # WHY: try-guarded fetch/merge/finalize sequencer.
        """Execute the fetch, merge, and finalize stages that require exception-guard protection."""
        fetched = self._fetch_clients_and_sessions(stamp)  # WHY: pull paginated clients + sessions from the SDK.
        if fetched is None:  # WHY: the fetch helper handled a valid-empty or partial-empty result.
            return  # WHY: no record remains for the merge or export stages.
        clients_read, sessions_read = fetched  # WHY: retain completion state beside each dataset.
        clients = clients_read.records  # WHY: merge only records from validated successful pages.
        sessions = sessions_read.records  # WHY: merge only records from validated successful pages.
        enriched = self._merge_clients_and_sessions(clients, sessions, stamp)  # WHY: build the merged output rows.
        if not enriched:  # WHY: defensive empty-post-merge branch — nothing to persist to disk.
            if clients_read.is_partial or sessions_read.is_partial:  # WHY: do not report an incomplete read as empty.
                self._log_partial_empty_export()  # WHY: tell the operator that no successful page supplied rows.
            else:
                self._log_empty_merge()  # WHY: preserve the complete-read empty-merge notice.
            return  # WHY: nothing to persist when the merge produced zero rows.
        self._finalize_export(
            enriched,
            clients_read,
            sessions_read,
            stamp.site_name,
        )  # WHY: flatten, write, and report completion state for both datasets.

    @staticmethod
    def _log_empty_merge() -> None:  # WHY: empty-post-merge emitter isolated to keep pipeline branch-shallow.
        """Log + print the defensive empty-post-merge operator messages."""
        logger.warning(_NO_POST_MERGE_TEXT)  # WHY: preserve defensive empty-post-merge log severity + text.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info(_NO_POST_MERGE_TEXT)  # WHY: preserve legacy operator-facing empty-result message text.

    @staticmethod
    def _log_partial_empty_export() -> None:
        """Report a partial read with no exportable records without creating a valid-empty placeholder."""
        logger.warning(  # WHY: distinguish a short read from a complete empty result.
            "WiFi export is partial. No records from successful pages are available, so no output file was created."
        )

    def _ensure_site_selected(self, site_id: str | None) -> str | None:  # WHY: cache-seed + prompt orchestrator.
        """Ensure SiteList cache exists and resolve site_id (prompt operator when missing)."""
        logger.info("Ensuring SiteList.csv cache is available before site resolution")  # WHY: log precondition.
        self.cache_utils.check_and_generate_csv(_SITE_LIST_CSV, self.org_site_exporter.sites)  # WHY: seed cache.
        logger.debug("SiteList.csv cache check/generation completed")  # WHY: after-action confirmation for trace.
        if site_id:
            return site_id  # WHY: caller supplied a site id — no interactive prompt required.
        logger.info("No site_id provided; prompting operator to select a site from CSV")  # WHY: log prompt intent.
        chosen = self.prompt_utils.select_site_id_from_csv(_SITE_LIST_CSV)  # WHY: interactive picker via helper.
        logger.debug("Site selection prompt completed with site_id=%s", chosen)  # WHY: result for traceability.
        if not chosen:
            logger.error(_NO_SITE_TEXT)  # WHY: cancel-path log preserved verbatim from the legacy exporter.
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.info(_NO_SITE_TEXT)  # WHY: preserve legacy operator-facing cancel-path message.
            return None  # WHY: signal abort to orchestrator so no artifacts are written.
        return chosen  # WHY: resolved site identifier to operate on for the remainder of the workflow.

    def _resolve_site_name(self, site_id: str) -> str:
        """Look up the display name for site_id from SiteList.csv (fallback preserved)."""
        try:
            logger.info("Resolving site name from SiteList.csv for site_id=%s", site_id)  # WHY: log lookup start.
            site_list_path = self.file_path_utils.get_csv_path(_SITE_LIST_CSV)  # WHY: canonical CSV path lookup.
            site_name = self._scan_site_list_for_name(site_list_path, site_id)  # WHY: delegate row-scan to helper.
            logger.debug("Resolved site name for site_id=%s to '%s'", site_id, site_name)  # WHY: log resolved.
            return site_name  # WHY: return the resolved (or fallback) name for headers and CSV stamping.
        except Exception as exception:
            logging.warning("! Failed to load site name from SiteList.csv: %s", exception)  # WHY: non-fatal log.
            return _UNKNOWN_SITE  # WHY: fallback so downstream stamping stays stable when lookup fails.

    @staticmethod
    def _scan_site_list_for_name(site_list_path: str, site_id: str) -> str:
        """Scan the SiteList CSV once for the row whose id matches site_id and return its name."""
        with open(site_list_path, encoding="utf-8") as file_handle:  # WHY: open SiteList CSV for name lookup.
            reader = csv.DictReader(file_handle)  # WHY: header-keyed reader for stable column access.
            for row in reader:
                if row.get("id") == site_id:
                    return row.get("name", _UNKNOWN_SITE)  # WHY: capture matched name preserving fallback default.
        return _UNKNOWN_SITE  # WHY: no matching row — return fallback so callers rely on a single default source.

    def _fetch_clients_and_sessions(self, stamp: _SiteStamp) -> tuple[_PageReadResult, _PageReadResult] | None:
        """Fetch clients and sessions, preserving valid-empty and partial-empty behavior."""
        clients = self._fetch_paginated(
            self.mistapi_module.api.v1.sites.clients.searchSiteWirelessClients, stamp.site_id, "wireless clients"
        )  # WHY: pull the full paginated wireless clients dataset for the site.
        sessions = self._fetch_paginated(
            self.mistapi_module.api.v1.sites.clients.searchSiteWirelessClientSessions,
            stamp.site_id,
            "wireless client sessions",
        )  # WHY: pull the full paginated wireless session dataset for the site.
        if not clients.records and not sessions.records:  # WHY: distinguish complete emptiness from a short read.
            if clients.is_partial or sessions.is_partial:  # WHY: incomplete reads cannot create valid-empty output.
                self._log_partial_empty_export()  # WHY: report the partial result without writing a placeholder.
                return None  # WHY: no successful records exist for a safe export.
            self._write_no_data_placeholder(stamp)  # WHY: preserve the sentinel for a complete empty read.
            return None  # WHY: stop after the valid-empty placeholder satisfies the output contract.
        return clients, sessions  # WHY: retain page state until the export summary is written.

    def _fetch_paginated(self, endpoint: Any, site_id: str, label: str) -> _PageReadResult:
        """Read every page through mistapi while retaining valid rows after a later transport failure."""
        logger.info("Fetching %s data...", label)  # WHY: log before the first-page API call for tracing.
        current_response = endpoint(self.apisession, site_id, limit=_API_PAGE_LIMIT)  # WHY: request the first page.
        logger.debug(  # WHY: record the response status before validation decides whether data is trustworthy.
            "Received HTTP %s response for %s at site %s",
            self._response_status_code(current_response),
            label,
            site_id,
        )
        self._reject_failed_response(current_response, site_id, label)  # WHY: keep first-page validation unchanged.
        results = self._response_records(current_response)  # WHY: copy rows before a later request can fail.
        while getattr(current_response, "next", None):  # WHY: request only pages that the SDK response identifies.
            logger.info("Fetching the next page of %s for site %s", label, site_id)  # WHY: trace each page request.
            try:
                next_response = self.mistapi_module.get_next(  # WHY: keep SDK authentication and URL handling.
                    mist_session=self.apisession,
                    response=current_response,
                )
            except (RequestException, TimeoutError) as exception:  # WHY: retain rows only for transport failures.
                logger.warning(  # WHY: report an incomplete read without exposing the exception or response body.
                    "WiFi %s pagination stopped after %s. Retaining %d records from successful pages.",
                    label,
                    type(exception).__name__,
                    len(results),
                )
                return _PageReadResult(records=results, is_partial=True)  # WHY: export only proven successful rows.
            if next_response is None:  # WHY: a missing page cannot prove that the result is complete.
                logger.warning(  # WHY: distinguish an incomplete read from a complete result.
                    "WiFi %s pagination stopped without a response. Retaining %d records from successful pages.",
                    label,
                    len(results),
                )
                return _PageReadResult(records=results, is_partial=True)  # WHY: never mark a missing page complete.
            logger.debug(  # WHY: record each completed SDK page request before response validation.
                "Received HTTP %s response for %s at site %s",  # WHY: report safe response metadata only.
                self._response_status_code(next_response),  # WHY: exclude response bodies and credentials.
                label,  # WHY: identify the WiFi dataset without exposing response content.
                site_id,  # WHY: associate the page result with its site.
            )
            self._reject_failed_response(next_response, site_id, label)  # WHY: never append a failed HTTP page.
            results.extend(self._response_records(next_response))  # WHY: append only a validated page.
            current_response = next_response  # WHY: use the received page's next link for the next iteration.
        logger.debug("Fetched %d %s records", len(results), label)  # WHY: record the complete page count.
        return _PageReadResult(records=results)  # WHY: mark the fully traversed result as complete.

    @staticmethod
    def _response_records(response: Any) -> list[dict[str, Any]]:
        """Copy records from a list response or a search response with a results field."""
        payload = getattr(response, "data", None)  # WHY: APIResponse stores parsed page data in this field.
        if isinstance(payload, list):  # WHY: some Mist endpoints return the record list directly.
            return list(payload)  # WHY: isolate accumulated records from later response mutation.
        if isinstance(payload, dict) and "results" in payload:  # WHY: search endpoints wrap records in results.
            page_records = payload["results"]  # WHY: validate the wrapped records before accumulation.
            if isinstance(page_records, list):  # WHY: only a list is a valid record page.
                return list(page_records)  # WHY: isolate accumulated records from later response mutation.
            raise ValueError("WiFi page results are not a list")  # WHY: reject malformed response shapes.
        return []  # WHY: preserve the SDK's empty result for a valid object without a results field.

    @classmethod
    def _reject_failed_response(cls, response: Any, site_id: str, label: str) -> None:
        """Reject HTTP failures and native responses whose body cannot prove an empty result."""
        status_code = cls._response_status_code(response)  # WHY: inspect the native HTTP outcome before pagination.
        if (  # WHY: failed HTTP answers cannot prove emptiness.
            status_code is not None and status_code >= _HTTP_ERROR_MIN
        ):
            logger.error(  # WHY: expose the actual cloud failure instead of a valid-empty notice.
                "The cloud returned HTTP %s for %s at site %s",
                status_code,
                label,
                site_id,
            )
            raise RuntimeError(  # WHY: route failure to execute() with the cloud status.
                f"WiFi {label} request failed with HTTP {status_code}"
            )
        if cls._response_body_failed(response):  # WHY: malformed or empty bodies cannot prove an empty result.
            if ResponseIntegrityChecker.body_failed_to_parse(response):  # WHY: use the shared parse-failure report.
                ResponseIntegrityChecker.report_parse_failure(response, label, site_id)  # WHY: name the broken reply.
            else:
                logger.error(  # WHY: report a native 200 response with no body as a failed WiFi answer.
                    "The cloud reply for %s at site %s has an empty body. Treat this run as a failure.",
                    label,
                    site_id,
                )
            raise ValueError(f"WiFi {label} response body is unusable")  # WHY: prevent placeholder output.

    @staticmethod
    def _response_status_code(response: Any) -> int | None:
        """Return an integer HTTP status when the response exposes one."""
        status_code = getattr(response, "status_code", None)  # WHY: native APIResponse carries the HTTP result here.
        return status_code if isinstance(status_code, int) else None  # WHY: ignore incomplete test doubles safely.

    @classmethod
    def _response_body_failed(cls, response: Any) -> bool:
        """Return whether the response body cannot prove a valid WiFi result."""
        if ResponseIntegrityChecker.body_failed_to_parse(response):  # WHY: detect malformed JSON retained by mistapi.
            return True  # WHY: malformed JSON must not become a valid-empty export.
        raw_data = getattr(response, "raw_data", _MISSING_ATTRIBUTE)  # WHY: inspect only native SDK body state.
        payload = getattr(response, "data", _MISSING_ATTRIBUTE)  # WHY: pair body state with the parsed payload state.
        return (  # WHY: reject native empty bodies while preserving response doubles without raw_data.
            isinstance(raw_data, str) and not raw_data.strip() and payload in ({}, [])
        )

    def _write_no_data_placeholder(self, stamp: _SiteStamp) -> None:
        """Write the legacy no-data sentinel CSV when neither clients nor sessions are found."""
        logger.warning(_NO_DATA_TEXT)  # WHY: preserve empty-result log severity + text from the legacy exporter.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info(_NO_DATA_TEXT)  # WHY: preserve legacy operator-facing empty-result message text.
        logger.info("Writing no-data placeholder CSV for %s", _OUTPUT_CSV)  # WHY: log before placeholder write.
        wifi_clients_path = self.file_path_utils.get_csv_path(_OUTPUT_CSV)  # WHY: resolve canonical output path.
        with open(wifi_clients_path, "w", newline="", encoding="utf-8") as file_handle:
            writer = csv.writer(file_handle)  # WHY: plain CSV writer for the fixed placeholder schema.
            writer.writerow(_PLACEHOLDER_HEADER)  # WHY: emit header row expected by downstream readers.
            writer.writerow([stamp.site_id, stamp.site_name, _PLACEHOLDER_MESSAGE])  # WHY: emit sentinel body row.
        logger.debug("No-data placeholder CSV written to %s", wifi_clients_path)  # WHY: after-action confirmation.

    def _merge_clients_and_sessions(
        self,
        clients: list[dict[str, Any]],
        sessions: list[dict[str, Any]],
        stamp: _SiteStamp,
    ) -> list[dict[str, Any]]:
        """Merge client records with latest sessions and append session-only rows for orphan MACs."""
        sessions_by_mac = self._index_sessions_by_mac(sessions)  # WHY: build MAC -> sessions lookup for merge.
        processed_macs: set[str] = set()  # WHY: track MACs already emitted so orphan pass skips duplicates.
        enriched = self._merge_client_pass(clients, sessions_by_mac, processed_macs, stamp)  # WHY: client rows.
        self._merge_session_only_pass(sessions, processed_macs, enriched, stamp)  # WHY: append orphan session rows.
        return enriched  # WHY: combined merged output list handed to the finalize stage.

    @classmethod
    def _merge_client_pass(
        cls,
        clients: list[dict[str, Any]],
        sessions_by_mac: dict[str, list[dict[str, Any]]],
        processed_macs: set[str],
        stamp: _SiteStamp,
    ) -> list[dict[str, Any]]:
        """Stamp each client and attach its latest session, returning the enriched rows."""
        enriched: list[dict[str, Any]] = []  # WHY: accumulator for enriched client rows returned to caller.
        if not clients:
            return enriched  # WHY: skip logging + iteration when no clients were returned by the API.
        logger.info("Merging client records with latest session details")  # WHY: log before the merge pass.
        for client in clients:
            cls._stamp_client(client, stamp)  # WHY: add site metadata + client provenance marker.
            cls._attach_latest_session(client, sessions_by_mac, processed_macs)  # WHY: borrow session_* fields.
            enriched.append(client)  # WHY: append enriched client row to the merged output list.
        logger.debug("Client merge produced %d enriched client rows", len(enriched))  # WHY: after-action size.
        return enriched  # WHY: hand enriched list back to the coordinator for orphan-pass extension.

    @classmethod
    def _merge_session_only_pass(
        cls,
        sessions: list[dict[str, Any]],
        processed_macs: set[str],
        enriched: list[dict[str, Any]],
        stamp: _SiteStamp,
    ) -> None:
        """Append synthetic rows for session MACs not already represented by a client row."""
        if not sessions:
            return  # WHY: skip logging + iteration when the sessions dataset is empty.
        logger.info("Adding session-only rows for MACs not present in client list")  # WHY: log before pass.
        for session in sessions:
            session_mac = session.get("mac")  # WHY: extract MAC to detect orphan session rows.
            if not session_mac or session_mac in processed_macs:
                continue  # WHY: skip when no MAC or already represented by a client row.
            enriched.append(cls._build_session_only_row(session, stamp))  # WHY: synthesize orphan-session row.
        logger.debug("Total enriched rows after session-only merge: %d", len(enriched))  # WHY: after-action size.

    @staticmethod
    def _index_sessions_by_mac(
        sessions: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Build a MAC-indexed map of session lists for efficient merge."""
        sessions_by_mac: dict[str, list[dict[str, Any]]] = {}  # WHY: output map keyed by MAC address.
        if not sessions:
            return sessions_by_mac  # WHY: nothing to index — return the empty map immediately.
        logger.info("Indexing sessions by MAC for efficient merge")  # WHY: log before indexing action for trace.
        for session in sessions:
            mac = session.get("mac")  # WHY: extract session MAC used as the merge key.
            if mac:
                sessions_by_mac.setdefault(mac, []).append(session)  # WHY: append session into MAC bucket.
        logger.debug("Indexed sessions for %d unique MAC addresses", len(sessions_by_mac))  # WHY: after-action.
        return sessions_by_mac  # WHY: ready-to-use lookup map handed to the merge pass.

    @staticmethod
    def _stamp_client(client: dict[str, Any], stamp: _SiteStamp) -> None:
        """Stamp site metadata fields on a client row in place."""
        client["site_id"] = stamp.site_id  # WHY: stamp site UUID for downstream reporting consistency.
        client["site_name"] = stamp.site_name  # WHY: stamp human-readable site name for operator context.
        client["data_source"] = _SOURCE_CLIENT  # WHY: mark provenance so consumers distinguish row origin.

    @staticmethod
    def _attach_latest_session(
        client: dict[str, Any],
        sessions_by_mac: dict[str, list[dict[str, Any]]],
        processed_macs: set[str],
    ) -> None:
        """Borrow the newest session's missing fields onto the client row (legacy session_ prefix preserved)."""
        client_mac = client.get("mac")  # WHY: capture client MAC used for session lookup.
        if not (client_mac and client_mac in sessions_by_mac):
            client["session_count"] = 0  # WHY: preserve explicit zero count when no session data exists.
            return  # WHY: no matching session bucket — nothing to borrow onto the client row.
        session_list = sessions_by_mac[client_mac]  # WHY: all sessions tied to this MAC.
        latest_session = max(session_list, key=lambda row: row.get("start_time", 0))  # WHY: newest session wins.
        for key, value in latest_session.items():
            if key not in client:
                client[f"session_{key}"] = value  # WHY: namespace borrowed fields to avoid key collisions.
        client["session_count"] = len(session_list)  # WHY: record total sessions found for this client MAC.
        processed_macs.add(client_mac)  # WHY: mark MAC as processed so the orphan pass skips this MAC.

    @staticmethod
    def _build_session_only_row(session: dict[str, Any], stamp: _SiteStamp) -> dict[str, Any]:
        """Build a session-only output row with the legacy session_ field prefixing."""
        session["site_id"] = stamp.site_id  # WHY: stamp site UUID for consistency with client rows.
        session["site_name"] = stamp.site_name  # WHY: stamp site name for human readability.
        session["data_source"] = _SOURCE_SESSION_ONLY  # WHY: mark provenance for downstream consumers.
        session["session_count"] = 1  # WHY: legacy semantics — one represented session per orphan row.
        return {
            key if key in _META_KEYS else f"session_{key}": value  # WHY: preserve meta keys. Prefix payload keys.
            for key, value in session.items()
        }

    def _finalize_export(
        self,
        enriched: list[dict[str, Any]],
        clients: _PageReadResult,
        sessions: _PageReadResult,
        site_name: str,
    ) -> None:
        """Flatten, escape, write to backend, and print legacy success summary."""
        sanitized = self._flatten_and_sanitize(enriched)  # WHY: normalize nested + multiline fields for CSV write.
        self._write_final_csv(sanitized)  # WHY: persist the final processed records via the configured backend.
        self._print_success_summary(clients, sessions, enriched, site_name)  # WHY: legacy operator success text.

    def _flatten_and_sanitize(self, enriched: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Flatten nested fields and escape multiline values for CSV-safe tabular output."""
        logger.info("Flattening nested WiFi client/session fields for export")  # WHY: log before flatten action.
        flattened = self.data_processing_utils.flatten_nested_fields(enriched)  # WHY: flatten nested dicts.
        logger.debug("Flatten transformation produced %d rows", len(flattened))  # WHY: after-action row count.
        logger.info("Escaping multiline fields for CSV-safe output")  # WHY: log before sanitize action.
        sanitized = self.data_processing_utils.escape_multiline(flattened)  # WHY: escape multiline values.
        logger.debug("Multiline escaping completed for %d rows", len(sanitized))  # WHY: after-action size.
        return sanitized  # WHY: return CSV-safe rows for the final write stage.

    def _write_final_csv(self, sanitized: list[dict[str, Any]]) -> None:
        """Persist the sanitized rows through the configured data exporter backend."""
        logger.info("Writing %s to configured output backend", _OUTPUT_CSV)  # WHY: log before final write.
        self.data_exporter.write_with_format_selection(
            sanitized, _OUTPUT_CSV, api_function_name="listSiteWirelessClientsStats"
        )  # WHY: persist final records.
        logger.debug("%s write completed successfully", _OUTPUT_CSV)  # WHY: after-action write confirmation.

    @staticmethod
    def _print_success_summary(
        clients: _PageReadResult,
        sessions: _PageReadResult,
        enriched: list[dict[str, Any]],
        site_name: str,
    ) -> None:
        """Emit the legacy operator-facing success summary block preserving prior formatting."""
        client_count = len(clients.records)  # WHY: compute client count for the legacy summary line.
        session_count = len(sessions.records)  # WHY: compute session count for the legacy summary.
        total_records = len(enriched)  # WHY: total merged-row count for summary reporting.
        if clients.is_partial or sessions.is_partial:  # WHY: do not label a short read as a complete export.
            logger.warning(  # WHY: identify retained data and its partial status for the operator.
                "! WiFi data partially exported to %s (%d clients, %d sessions, %d total records)",
                _OUTPUT_CSV,
                client_count,
                session_count,
                total_records,
            )
            logger.info("! WiFi data partially exported to %s", _OUTPUT_CSV)  # WHY: state the output status.
            return  # WHY: omit the legacy complete-success notice for a partial result.
        logger.info(
            "! WiFi data exported to %s (%d clients, %d sessions, %d total records)",
            _OUTPUT_CSV,
            client_count,
            session_count,
            total_records,
        )  # WHY: structured log mirrors the operator print block for tracing parity.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("! WiFi data exported to %s", _OUTPUT_CSV)  # WHY: preserve legacy success confirmation line.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info(
            "   %d current clients, %d sessions, %d total records from %s",
            client_count,
            session_count,
            total_records,
            site_name,
        )  # WHY: preserve legacy detailed summary with counts and site context.
