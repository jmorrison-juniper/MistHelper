"""Workflow extraction for site WiFi client export orchestration."""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from typing import Any


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
        print("Export Site WiFi Clients:")  # Preserve legacy header text so operator experience remains unchanged.
        logging.info(
            "Starting export of site WiFi clients..."
        )  # Log workflow start so the execution boundary is explicit.
        logging.info(
            "Ensuring SiteList.csv cache is available before site resolution"
        )  # Log before cache precondition action.
        self.cache_utils.check_and_generate_csv(
            "SiteList.csv", self.org_site_exporter.sites
        )  # Ensure site list cache exists for site selection and name resolution.
        logging.debug("SiteList.csv cache check/generation completed")  # Log completion of cache precondition action.
        if not site_id:
            logging.info(
                "No site_id provided; prompting operator to select a site from CSV"
            )  # Log before interactive site selection action.
            site_id = self.prompt_utils.select_site_id_from_csv(
                "SiteList.csv"
            )  # Prompt operator to choose a site using cached SiteList CSV.
            logging.debug(
                "Site selection prompt completed with site_id=%s", site_id
            )  # Log selection result for traceability.
            if not site_id:
                logging.error(" No site selected.")  # Log early-exit reason when operator cancels selection.
                print(" No site selected.")  # Preserve legacy operator message for cancellation path.
                return  # Exit early because downstream API calls require a valid site identifier.
        site_name = "Unknown Site"  # Initialize fallback site name so exports remain stable if lookup fails.
        try:
            logging.info(
                "Resolving site name from SiteList.csv for site_id=%s", site_id
            )  # Log before local file lookup for site-name enrichment.
            site_list_path = self.file_path_utils.get_csv_path(
                "SiteList.csv"
            )  # Resolve canonical path for SiteList CSV location.
            with open(
                site_list_path, encoding="utf-8"
            ) as file_handle:  # Open SiteList CSV for deterministic site-name lookup.
                reader = csv.DictReader(file_handle)  # Create dictionary reader so rows can be keyed by column names.
                for row in reader:  # Iterate SiteList rows until matching site_id is found.
                    if row.get("id") == site_id:  # Match on site UUID so displayed/exported site name is accurate.
                        site_name = row.get(
                            "name", "Unknown Site"
                        )  # Capture resolved site name while preserving fallback semantics.
                        break  # Stop scanning once the matching site is found to avoid unnecessary IO work.
            logging.debug(
                "Resolved site name for site_id=%s to '%s'", site_id, site_name
            )  # Log site-name resolution result.
        except Exception as exception:
            logging.warning(
                "! Failed to load site name from SiteList.csv: %s", exception
            )  # Log non-fatal lookup failure while preserving workflow continuity.
        logging.info(
            "Fetching WiFi clients for site: %s (ID: %s)", site_name, site_id
        )  # Log before network retrieval actions.
        print(f"! Fetching WiFi clients for site: {site_name}")  # Preserve legacy operator-facing fetch message.
        try:
            logging.info("Fetching wireless clients data...")  # Log before primary clients API call.
            client_response = self.mistapi_module.api.v1.sites.clients.searchSiteWirelessClients(  # API call.
                self.apisession,
                site_id,
                limit=1000,
            )
            clients = self.mistapi_module.get_all(
                response=client_response, mist_session=self.apisession
            )  # Resolve paginated clients response into a full client list.
            logging.debug(
                "Fetched %d wireless client records", len(clients) if clients else 0
            )  # Log clients retrieval result summary.
            logging.info("Fetching wireless client sessions data...")  # Log before sessions API call.
            session_response = self.mistapi_module.api.v1.sites.clients.searchSiteWirelessClientSessions(  # API call.
                self.apisession,
                site_id,
                limit=1000,
            )
            sessions = self.mistapi_module.get_all(
                response=session_response, mist_session=self.apisession
            )  # Resolve paginated session response into a full sessions list.
            logging.debug(
                "Fetched %d wireless session records", len(sessions) if sessions else 0
            )  # Log sessions retrieval result summary.
            if not clients and not sessions:
                logging.warning(
                    " No WiFi clients or sessions found at this site."
                )  # Log empty-result condition for operational visibility.
                print(
                    " No WiFi clients or sessions found at this site."
                )  # Preserve legacy operator message for no-data scenarios.
                logging.info(
                    "Writing no-data placeholder CSV for SiteWiFiClients.CSV"
                )  # Log before writing explicit no-data output artifact.
                wifi_clients_path = self.file_path_utils.get_csv_path(
                    "SiteWiFiClients.CSV"
                )  # Resolve canonical path for no-data output file.
                with open(
                    wifi_clients_path, "w", newline="", encoding="utf-8"
                ) as file_handle:  # Open output CSV in write mode to create a deterministic no-data artifact.
                    writer = csv.writer(file_handle)  # Initialize CSV writer for explicit output rows.
                    writer.writerow(
                        ["site_id", "site_name", "message"]
                    )  # Write schema header row expected by downstream readers.
                    writer.writerow(
                        [site_id, site_name, "No WiFi clients or sessions found"]
                    )  # Write sentinel no-data row preserving legacy behavior.
                logging.debug(
                    "No-data placeholder CSV written to %s", wifi_clients_path
                )  # Log completion of no-data file write.
                return  # Exit after creating no-data artifact because there is nothing to process further.
            sessions_by_mac: dict[str, list[dict[str, Any]]] = (
                {}
            )  # Initialize MAC-indexed session map for client/session merge.
            if sessions:
                logging.info("Indexing sessions by MAC for efficient merge")  # Log before session-index build action.
                for session in sessions:  # Iterate each session to build a MAC-based lookup table.
                    mac = session.get("mac")  # Extract session MAC used as merge key.
                    if mac:
                        if mac not in sessions_by_mac:
                            sessions_by_mac[mac] = []  # Initialize bucket for this MAC before appending sessions.
                        sessions_by_mac[mac].append(
                            session
                        )  # Append session so latest-session lookup can be performed later.
                logging.debug(
                    "Indexed sessions for %d unique MAC addresses", len(sessions_by_mac)
                )  # Log indexing summary for observability.
            enriched_clients: list[dict[str, Any]] = (
                []
            )  # Initialize merged output record list consumed by flatten/export pipeline.
            processed_macs: set[str] = set()  # Track client MACs already merged to avoid duplicate session-only rows.
            if clients:
                logging.info(
                    "Merging client records with latest session details"
                )  # Log before client/session merge pass.
                for client in clients:  # Iterate each client record to enrich with session metadata where available.
                    client_mac = client.get("mac")  # Capture client MAC used for lookup in session index.
                    client["site_id"] = site_id  # Stamp site ID for downstream reporting and export consistency.
                    client["site_name"] = site_name  # Stamp site name for human-readable reporting context.
                    client["data_source"] = "client"  # Mark source as client-origin row to preserve existing semantics.
                    if client_mac and client_mac in sessions_by_mac:
                        session_list = sessions_by_mac[client_mac]  # Fetch all sessions tied to current client MAC.
                        latest_session = max(
                            session_list, key=lambda session_row: session_row.get("start_time", 0)
                        )  # Choose newest session to preserve prior merge policy.
                        for (
                            key,
                            value,
                        ) in (
                            latest_session.items()
                        ):  # Copy missing latest-session fields onto client row using session_ prefix.
                            if key not in client:
                                client[f"session_{key}"] = (
                                    value  # Preserve existing behavior of namespacing borrowed session fields.
                                )
                        client["session_count"] = len(session_list)  # Record number of sessions found for client MAC.
                        processed_macs.add(client_mac)  # Mark MAC as processed so session-only pass can skip it.
                    else:
                        client["session_count"] = 0  # Preserve explicit zero session count when no session data exists.
                    enriched_clients.append(client)  # Add enriched client row to output list.
                logging.debug(
                    "Client merge produced %d enriched client rows", len(enriched_clients)
                )  # Log result count after client merge pass.
            if sessions:
                logging.info(
                    "Adding session-only rows for MACs not present in client list"
                )  # Log before secondary merge pass for orphan sessions.
                for (
                    session
                ) in (
                    sessions
                ):  # Iterate sessions again to include MACs that have session records but no active client row.
                    session_mac = session.get("mac")  # Extract MAC to determine whether a session-only row is needed.
                    if session_mac and session_mac not in processed_macs:
                        session["site_id"] = (
                            site_id  # Stamp site ID on session-only row for consistency with client rows.
                        )
                        session["site_name"] = site_name  # Stamp site name on session-only row for human readability.
                        session["data_source"] = (
                            "session_only"  # Mark source so downstream users can distinguish row provenance.
                        )
                        session["session_count"] = (
                            1  # Preserve legacy session-only semantics of one represented session per row.
                        )
                        session_data: dict[str, Any] = {}  # Initialize transformed session-only row structure.
                        for (
                            key,
                            value,
                        ) in (
                            session.items()
                        ):  # Normalize session fields into output schema with prefixed keys where required.
                            if key not in ["site_id", "site_name", "data_source", "session_count"]:
                                session_data[f"session_{key}"] = (
                                    value  # Prefix session-origin fields to avoid collisions with client-key namespace.
                                )
                            else:
                                session_data[key] = value  # Preserve meta fields without prefix.
                        enriched_clients.append(
                            session_data
                        )  # Add synthesized session-only row to enriched output list.
                logging.debug(
                    "Total enriched rows after session-only merge: %d", len(enriched_clients)
                )  # Log merged-row count after second pass.
            if not enriched_clients:
                logging.warning(
                    " No data to export after processing."
                )  # Log safety check failure when merge produced zero rows.
                print(
                    " No data to export after processing."
                )  # Preserve legacy operator message for empty-postprocess condition.
                return  # Exit early because exporter has no rows to persist.
            logging.info(
                "Flattening nested WiFi client/session fields for export"
            )  # Log before flatten transformation action.
            flattened = self.data_processing_utils.flatten_nested_fields(
                enriched_clients
            )  # Flatten nested dictionaries for tabular output compatibility.
            logging.debug(
                "Flatten transformation produced %d rows", len(flattened)
            )  # Log flatten result size for observability.
            logging.info("Escaping multiline fields for CSV-safe output")  # Log before multiline-sanitization action.
            sanitized = self.data_processing_utils.escape_multiline(
                flattened
            )  # Escape multiline values to preserve CSV integrity.
            logging.debug("Multiline escaping completed for %d rows", len(sanitized))  # Log sanitization result size.
            logging.info(
                "Writing SiteWiFiClients.CSV to configured output backend"
            )  # Log before final output write action.
            self.data_exporter.save_data_to_output(
                sanitized, "SiteWiFiClients.CSV"
            )  # Persist final processed records via existing data exporter.
            logging.debug("SiteWiFiClients.CSV write completed successfully")  # Log completion of output write action.
            client_count = len(clients) if clients else 0  # Compute client count for final summary messaging.
            session_count = len(sessions) if sessions else 0  # Compute session count for final summary messaging.
            total_records = len(enriched_clients)  # Compute total merged record count for summary reporting.
            logging.info(
                "! WiFi data exported to SiteWiFiClients.CSV (%d clients, %d sessions, %d total records)",
                client_count,
                session_count,
                total_records,
            )
            print(
                "! WiFi data exported to SiteWiFiClients.CSV"
            )  # Preserve legacy success message for operator confirmation.
            print(
                f"   {client_count} current clients, {session_count} sessions, "
                f"{total_records} total records from {site_name}"
            )  # Preserve legacy detailed summary line with counts and site context.
        except Exception as exception:
            logging.error(
                "! Failed to fetch WiFi data for site %s: %s", site_id, exception, exc_info=True
            )  # Log failure with traceback for root-cause analysis.
            print(f"! Failed to fetch WiFi data: {exception}")  # Preserve legacy operator-facing error output.
