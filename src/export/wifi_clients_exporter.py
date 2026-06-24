"""Workflow extraction for site WiFi client export orchestration."""

from __future__ import annotations

import csv  # CSV reader for SiteList lookup and writer for no-data placeholder file.
import logging  # Structured operational logging for action tracing.
from dataclasses import dataclass  # Dataclass for injected-dependency container.
from typing import Any  # Vendor JSON shapes are dynamic dicts of arbitrary value types.


@dataclass
class WifiClientsExporter:
    """Export merged wireless client and session data with legacy-compatible output behavior."""

    cache_utils: Any
    org_site_exporter: Any
    prompt_utils: Any
    file_path_utils: Any
    data_processing_utils: Any
    data_exporter: Any
    mistapi_module: Any
    apisession: Any

    def execute(self, site_id: str | None = None) -> None:
        """Run the extracted WiFi client export flow preserving output and side effects."""
        print("Export Site WiFi Clients:")  # Preserve legacy header text so operator experience stays identical.
        logging.info("Starting export of site WiFi clients...")  # Log workflow start boundary.

        site_id = self._ensure_site_selected(site_id)  # Resolve / prompt for the site to operate on.
        if site_id is None:
            return  # Operator cancelled site selection — abort cleanly.

        site_name = self._resolve_site_name(site_id)  # Look up display name for headers and stamping.

        logging.info("Fetching WiFi clients for site: %s (ID: %s)", site_name, site_id)  # Log before API actions.
        print(f"! Fetching WiFi clients for site: {site_name}")  # Preserve legacy operator-facing fetch message.

        try:
            fetched = self._fetch_clients_and_sessions(site_id)  # Pull paginated clients + sessions.
            if fetched is None:
                return  # Helper already wrote the no-data placeholder artifact.
            clients, sessions = fetched  # Unpack non-empty datasets for merge.

            enriched = self._merge_clients_and_sessions(clients, sessions, site_id, site_name)  # Build output rows.
            if not enriched:
                logging.warning(" No data to export after processing.")  # Defensive empty-post-merge guard.
                print(" No data to export after processing.")  # Preserve legacy operator message.
                return  # Nothing to persist.

            self._finalize_export(enriched, clients, sessions, site_name)  # Flatten + escape + write final CSV.
        except Exception as exception:
            logging.error(  # Log failure with traceback for root-cause analysis.
                "! Failed to fetch WiFi data for site %s: %s", site_id, exception, exc_info=True
            )
            print(f"! Failed to fetch WiFi data: {exception}")  # Preserve legacy operator-facing error output.

    def _ensure_site_selected(self, site_id: str | None) -> str | None:
        """Ensure SiteList cache exists and resolve site_id (prompt operator when missing)."""
        logging.info("Ensuring SiteList.csv cache is available before site resolution")  # Log precondition action.
        self.cache_utils.check_and_generate_csv(
            "SiteList.csv", self.org_site_exporter.sites
        )  # Ensure SiteList cache exists so prompts + name lookup both succeed.
        logging.debug("SiteList.csv cache check/generation completed")  # After-action confirmation.

        if site_id:
            return site_id  # Caller supplied a site id — no prompt needed.

        logging.info("No site_id provided; prompting operator to select a site from CSV")  # Log interactive prompt.
        chosen = self.prompt_utils.select_site_id_from_csv("SiteList.csv")  # Interactive picker via shared helper.
        logging.debug("Site selection prompt completed with site_id=%s", chosen)  # Result for traceability.
        if not chosen:
            logging.error(" No site selected.")  # Cancel-path log preserved verbatim.
            print(" No site selected.")  # Preserve legacy operator-facing cancel message.
            return None  # Signal abort to orchestrator.
        return chosen  # Resolved site identifier to operate on.

    def _resolve_site_name(self, site_id: str) -> str:
        """Look up the display name for site_id from SiteList.csv (fallback preserved)."""
        site_name = "Unknown Site"  # Default fallback so downstream stamps remain stable on lookup failure.
        try:
            logging.info("Resolving site name from SiteList.csv for site_id=%s", site_id)  # Log before file lookup.
            site_list_path = self.file_path_utils.get_csv_path("SiteList.csv")  # Resolve canonical CSV path.
            with open(site_list_path, encoding="utf-8") as file_handle:  # Open SiteList CSV for name lookup.
                reader = csv.DictReader(file_handle)  # Header-keyed reader for stable column access.
                for row in reader:
                    if row.get("id") == site_id:  # Match on UUID so resolved name is unambiguous.
                        site_name = row.get("name", "Unknown Site")  # Capture name preserving fallback semantics.
                        break  # Stop scanning once the matching site is found.
            logging.debug("Resolved site name for site_id=%s to '%s'", site_id, site_name)  # Log result.
        except Exception as exception:
            logging.warning("! Failed to load site name from SiteList.csv: %s", exception)  # Non-fatal lookup fail.
        return site_name  # Fallback or resolved name for headers and CSV stamping.

    def _fetch_clients_and_sessions(self, site_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | None:
        """Fetch clients + sessions; on empty result write placeholder CSV and return None."""
        logging.info("Fetching wireless clients data...")  # Log before primary clients API call.
        client_response = self.mistapi_module.api.v1.sites.clients.searchSiteWirelessClients(
            self.apisession, site_id, limit=1000
        )  # First-page clients API call (paginated below by get_all).
        clients = self.mistapi_module.get_all(
            response=client_response, mist_session=self.apisession
        )  # Resolve full paginated clients list.
        logging.debug("Fetched %d wireless client records", len(clients) if clients else 0)  # After-action result.

        logging.info("Fetching wireless client sessions data...")  # Log before sessions API call.
        session_response = self.mistapi_module.api.v1.sites.clients.searchSiteWirelessClientSessions(
            self.apisession, site_id, limit=1000
        )  # First-page sessions API call (paginated below by get_all).
        sessions = self.mistapi_module.get_all(
            response=session_response, mist_session=self.apisession
        )  # Resolve full paginated sessions list.
        logging.debug("Fetched %d wireless session records", len(sessions) if sessions else 0)  # After-action.

        if not clients and not sessions:
            site_name = self._resolve_site_name(site_id)  # Re-resolve name for placeholder row context.
            self._write_no_data_placeholder(site_id, site_name)  # Persist sentinel artifact for downstream tooling.
            return None  # Signal early-exit to orchestrator.
        return clients or [], sessions or []  # Normalize None to empty list so merge helpers can iterate safely.

    def _write_no_data_placeholder(self, site_id: str, site_name: str) -> None:
        """Write the legacy no-data sentinel CSV when neither clients nor sessions are found."""
        logging.warning(" No WiFi clients or sessions found at this site.")  # Log empty-result condition.
        print(" No WiFi clients or sessions found at this site.")  # Preserve legacy operator message.
        logging.info("Writing no-data placeholder CSV for SiteWiFiClients.CSV")  # Log before placeholder write.
        wifi_clients_path = self.file_path_utils.get_csv_path("SiteWiFiClients.CSV")  # Canonical output path.
        with open(wifi_clients_path, "w", newline="", encoding="utf-8") as file_handle:
            writer = csv.writer(file_handle)  # Plain CSV writer for fixed schema.
            writer.writerow(["site_id", "site_name", "message"])  # Schema header expected by downstream readers.
            writer.writerow([site_id, site_name, "No WiFi clients or sessions found"])  # Sentinel row.
        logging.debug("No-data placeholder CSV written to %s", wifi_clients_path)  # After-action confirmation.

    def _merge_clients_and_sessions(
        self,
        clients: list[dict[str, Any]],
        sessions: list[dict[str, Any]],
        site_id: str,
        site_name: str,
    ) -> list[dict[str, Any]]:
        """Merge client records with latest sessions and append session-only rows for orphan MACs."""
        sessions_by_mac = self._index_sessions_by_mac(sessions)  # Build MAC -> sessions lookup table.

        enriched: list[dict[str, Any]] = []  # Final merged record list returned to caller.
        processed_macs: set[str] = set()  # Track MACs already emitted so session-only pass skips them.

        if clients:
            logging.info("Merging client records with latest session details")  # Log before merge pass.
            for client in clients:
                self._stamp_client(client, site_id, site_name)  # Add site metadata + data_source marker.
                self._attach_latest_session(client, sessions_by_mac, processed_macs)  # Borrow session_* fields.
                enriched.append(client)  # Add enriched client row to output list.
            logging.debug("Client merge produced %d enriched client rows", len(enriched))  # After-action.

        if sessions:
            logging.info("Adding session-only rows for MACs not present in client list")  # Log before second pass.
            for session in sessions:
                session_mac = session.get("mac")  # Extract MAC to detect orphan session rows.
                if not session_mac or session_mac in processed_macs:
                    continue  # Skip when no MAC or already represented by a client row.
                enriched.append(
                    self._build_session_only_row(session, site_id, site_name)
                )  # Synthesize session-only output row.
            logging.debug("Total enriched rows after session-only merge: %d", len(enriched))  # After-action.

        return enriched  # Combined merged output list for finalization.

    @staticmethod
    def _index_sessions_by_mac(
        sessions: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Build a MAC-indexed map of session lists for efficient merge."""
        sessions_by_mac: dict[str, list[dict[str, Any]]] = {}  # Output map: MAC -> list of session dicts.
        if not sessions:
            return sessions_by_mac  # Nothing to index.
        logging.info("Indexing sessions by MAC for efficient merge")  # Log before indexing action.
        for session in sessions:
            mac = session.get("mac")  # Extract session MAC as merge key.
            if mac:
                sessions_by_mac.setdefault(mac, []).append(session)  # Append session to MAC's bucket.
        logging.debug(
            "Indexed sessions for %d unique MAC addresses", len(sessions_by_mac)
        )  # After-action indexing summary.
        return sessions_by_mac  # Ready-to-use lookup map for merge pass.

    @staticmethod
    def _stamp_client(client: dict[str, Any], site_id: str, site_name: str) -> None:
        """Stamp site metadata fields on a client row in place."""
        client["site_id"] = site_id  # Stamp site UUID for downstream reporting consistency.
        client["site_name"] = site_name  # Stamp human-readable site name for context.
        client["data_source"] = "client"  # Mark provenance so consumers can distinguish row source.

    @staticmethod
    def _attach_latest_session(
        client: dict[str, Any],
        sessions_by_mac: dict[str, list[dict[str, Any]]],
        processed_macs: set[str],
    ) -> None:
        """Borrow the newest session's missing fields onto the client row (legacy session_ prefix preserved)."""
        client_mac = client.get("mac")  # Capture client MAC used for session lookup.
        if not (client_mac and client_mac in sessions_by_mac):
            client["session_count"] = 0  # Preserve explicit zero count when no session data exists.
            return  # No matching session bucket — nothing to borrow.
        session_list = sessions_by_mac[client_mac]  # All sessions tied to this MAC.
        latest_session = max(
            session_list, key=lambda session_row: session_row.get("start_time", 0)
        )  # Pick the newest session to preserve prior merge policy.
        for key, value in latest_session.items():
            if key not in client:
                client[f"session_{key}"] = value  # Namespace borrowed fields to avoid client-key collisions.
        client["session_count"] = len(session_list)  # Record total sessions found for this client MAC.
        processed_macs.add(client_mac)  # Mark MAC as processed so the session-only pass skips it.

    @staticmethod
    def _build_session_only_row(session: dict[str, Any], site_id: str, site_name: str) -> dict[str, Any]:
        """Build a session-only output row with the legacy session_ field prefixing."""
        session["site_id"] = site_id  # Stamp site UUID for consistency with client rows.
        session["site_name"] = site_name  # Stamp site name for human readability.
        session["data_source"] = "session_only"  # Mark provenance for downstream consumers.
        session["session_count"] = 1  # Legacy semantics: one represented session per row.
        meta_fields = {"site_id", "site_name", "data_source", "session_count"}  # Keys NOT to namespace-prefix.
        session_data: dict[str, Any] = {}  # Output row structure built from input session.
        for key, value in session.items():
            if key in meta_fields:
                session_data[key] = value  # Preserve metadata fields without prefix.
            else:
                session_data[f"session_{key}"] = value  # Prefix session-origin fields to avoid collisions.
        return session_data  # Synthesized row for the session-only pass.

    def _finalize_export(
        self,
        enriched: list[dict[str, Any]],
        clients: list[dict[str, Any]],
        sessions: list[dict[str, Any]],
        site_name: str,
    ) -> None:
        """Flatten, escape, write to backend, and print legacy success summary."""
        logging.info("Flattening nested WiFi client/session fields for export")  # Log before flatten action.
        flattened = self.data_processing_utils.flatten_nested_fields(
            enriched
        )  # Flatten nested dicts for tabular output compatibility.
        logging.debug("Flatten transformation produced %d rows", len(flattened))  # Result size.

        logging.info("Escaping multiline fields for CSV-safe output")  # Log before sanitize action.
        sanitized = self.data_processing_utils.escape_multiline(
            flattened
        )  # Escape multiline values to preserve CSV integrity.
        logging.debug("Multiline escaping completed for %d rows", len(sanitized))  # Result size.

        logging.info("Writing SiteWiFiClients.CSV to configured output backend")  # Log before final write action.
        self.data_exporter.write_with_format_selection(
            sanitized, "SiteWiFiClients.CSV"
        )  # Persist final processed records via existing data exporter.
        logging.debug("SiteWiFiClients.CSV write completed successfully")  # After-action confirmation.

        client_count = len(clients) if clients else 0  # Compute counts for the legacy summary line.
        session_count = len(sessions) if sessions else 0  # Compute counts for the legacy summary line.
        total_records = len(enriched)  # Total merged-row count for summary reporting.
        logging.info(
            "! WiFi data exported to SiteWiFiClients.CSV (%d clients, %d sessions, %d total records)",
            client_count,
            session_count,
            total_records,
        )
        print("! WiFi data exported to SiteWiFiClients.CSV")  # Preserve legacy success confirmation.
        print(
            f"   {client_count} current clients, {session_count} sessions, "
            f"{total_records} total records from {site_name}"
        )  # Preserve legacy detailed summary line with counts and site context.
