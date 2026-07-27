"""OrgTicketManager -- Mist support ticket lifecycle operations (Menus 188-193).

Extracted from MistHelper.py during initiative 1013 (Cat B, position 46)
under the SC-001 facade pattern. Provides 6 public operations covering the
full ticket lifecycle: list, create, add-comment (with optional
attachment), update, view, and export-details.

Direct imports cover stdlib (importlib, logging, os.path). Every
live-global read (``InputUtils``, ``ConfigUtils``, ``mistapi``,
``apisession``, ``APIDataFetcher``, ``DataExporter``,
``DataProcessingUtils``) is resolved via lazy
``mh = importlib.import_module("MistHelper")`` inside the methods that
need them. Callers continue to reach the class through the
``MistHelper.OrgTicketManager`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for future annotations.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace + info/warn/error logging.
import os  # WHY: os.path.isfile() to detect attachments before multipart upload.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).


class OrgTicketManager:  # Support ticket operations.
    """Full lifecycle management for Juniper Mist support tickets.

    Provides 6 public operations (list, create, add comment, update, view, export) that
    cover reading, creating, and modifying support tickets via the Mist API.
    Attachment support is integrated into add_comment via multipart upload.
    """

    TICKET_TYPES = ["question", "problem", "incident", "feature_request"]  # Valid Mist ticket type values

    # ------------------------------------------------------------------
    # Public entry points (6 operations -- cohesive ticket lifecycle)
    # ------------------------------------------------------------------

    @staticmethod
    def list_tickets() -> None:  # List org support tickets.
        """Menu 188: Export all organization support tickets to CSV/SQLite."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of APIDataFetcher + mistapi.
        logging.info("Menu 188: Starting organization ticket list export")  # Log operation entry
        logging.debug("ENTRY: OrgTicketManager.list_tickets()")  # Debug trace
        try:
            mh.APIDataFetcher(  # Delegate to standard fetch-export pipeline
                title="Organization Support Tickets:",  # User-facing header
                api_call=mh.mistapi.api.v1.orgs.tickets.listOrgTickets,  # SDK function for ticket listing
                filename="OrgTickets.csv",  # Output filename in data/ directory
                sort_key="created_at",  # Sort tickets by creation timestamp
                duration="365d",  # Look back 1 year (SDK defaults to 1d which misses older tickets)
            ).execute()  # Run the full fetch-flatten-export workflow
            logging.info("Completed org ticket list export")  # Log success
            logging.debug("EXIT: OrgTicketManager.list_tickets - success")  # Debug trace
        except Exception as error:  # Catch API or export failures
            logging.error("Failed to export org tickets: %s", error)  # Log error with context
            logging.debug("EXIT: OrgTicketManager.list_tickets - error")  # Debug trace
            raise  # Re-raise so caller sees the failure

    @staticmethod
    def create_ticket() -> None:  # Create a support ticket.
        """Menu 189: Create a new support ticket in the organization."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils + InputUtils.
        logging.info("Menu 189: Starting support ticket creation")  # Log operation entry
        logging.debug("ENTRY: OrgTicketManager.create_ticket()")  # Debug trace
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org from cache or user prompt
        subject = OrgTicketManager._prompt_subject()  # Prompt user for ticket subject line
        if not subject:  # User left subject blank -- abort
            logging.warning("  Ticket creation cancelled -- subject is required.")  # Inform user
            logging.info("Ticket creation cancelled: blank subject")  # Log cancellation
            return  # Early exit
        ticket_type = OrgTicketManager._prompt_ticket_type()  # Prompt user to select ticket type
        comment = mh.InputUtils.safe_input(  # Prompt for initial ticket description (optional)
            "  Enter initial comment/description: ",
            default_value="",
            allow_empty=True,
            context="create_ticket_comment",
        )
        body = {"subject": subject, "type": ticket_type}  # Build required API request fields
        if comment:  # Include comment only if user provided one
            body["comment"] = comment  # Add optional comment to request body
        OrgTicketManager._submit_create_ticket(org_id, body, subject, ticket_type)  # API + report

    @staticmethod
    def add_comment() -> None:  # Add a comment to a ticket.
        """Menu 190: Add a comment (with optional attachment) to an existing ticket."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils.
        logging.info("Menu 190: Starting add comment to ticket")  # Log operation entry
        logging.debug("ENTRY: OrgTicketManager.add_comment()")  # Debug trace
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org from cache or user prompt
        ticket_id = OrgTicketManager._select_ticket(org_id)  # Show ticket list for user selection
        if not ticket_id:  # User cancelled selection -- abort
            logging.warning("  Operation cancelled -- no ticket selected.")  # Inform user
            logging.info("Add comment cancelled: no ticket selected")  # Log the cancellation
            return  # Early exit without adding comment
        comment_text, file_path = OrgTicketManager._prompt_comment_and_file()  # Gather inputs together
        if not comment_text and not file_path:  # Neither comment nor file provided -- abort
            logging.warning("  Operation cancelled -- provide a comment or file.")  # Inform user
            logging.info("Add comment cancelled: no comment or file provided")  # Log cancellation
            return  # Early exit
        OrgTicketManager._submit_comment(  # Submit comment to API
            org_id,
            ticket_id,
            comment_text,
            file_path,  # Pass all user-provided values
        )

    @staticmethod
    def update_ticket() -> None:  # Update a support ticket.
        """Menu 191: Update fields on an existing support ticket."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils.
        logging.info("Menu 191: Starting ticket update")  # Log operation entry
        logging.debug("ENTRY: OrgTicketManager.update_ticket()")  # Debug trace
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org from cache or user prompt
        ticket_id = OrgTicketManager._select_ticket(org_id)  # Show ticket list for user selection
        if not ticket_id:  # User cancelled selection -- abort
            logging.warning("  Operation cancelled -- no ticket selected.")  # Inform user
            logging.info("Ticket update cancelled: no ticket selected")  # Log the cancellation
            return  # Early exit
        body = OrgTicketManager._build_update_body()  # Collect changed fields from user
        if not body:  # No fields were changed -- abort
            logging.warning("  No changes specified -- update cancelled.")  # Inform user
            logging.info("Ticket update cancelled: no fields changed")  # Log cancellation
            return  # Early exit
        OrgTicketManager._update_via_api(org_id, ticket_id, body)  # Send update + report results

    # ------------------------------------------------------------------
    # Private helpers (max 5 per group)
    # ------------------------------------------------------------------

    @staticmethod
    def _prompt_subject() -> str:  # Prompt for ticket subject.
        """Prompt user for ticket subject line."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils.
        return mh.InputUtils.safe_input(  # Use EOF-safe input wrapper
            "  Enter ticket subject: ",  # Prompt text for ticket title
            default_value="",  # No default -- user must provide subject
            allow_empty=True,  # Allow blank to signal cancellation
            context="create_ticket_subject",  # Context label for EOF logging
        )

    @staticmethod
    def _prompt_ticket_type() -> str:  # Prompt for ticket type.
        """Prompt user to select a ticket type from valid options."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils.
        logging.warning("\n  Ticket types:")  # Section header for type selection
        for index, ticket_type in enumerate(OrgTicketManager.TICKET_TYPES, 1):  # Number each type for selection
            logging.warning("    %d. %s", index, ticket_type)  # Display numbered option
        choice = mh.InputUtils.safe_input(  # Prompt user to pick a type number
            "  Select type [1]: ",  # Default to first option (question)
            default_value="1",  # Default selection is 'question'
            allow_empty=True,  # Allow enter for default
            context="create_ticket_type",  # Context label for EOF logging
        )
        try:
            index = int(choice) - 1  # Convert 1-based user input to 0-based index
            if 0 <= index < len(OrgTicketManager.TICKET_TYPES):  # Validate index is within bounds
                return OrgTicketManager.TICKET_TYPES[index]  # Return selected ticket type string
        except ValueError:  # User entered non-numeric input
            pass  # Fall through to default
        return OrgTicketManager.TICKET_TYPES[0]  # Default to 'question' for invalid input

    @staticmethod
    def _prompt_ticket_id() -> str:  # Prompt for ticket id.
        """Prompt user for ticket UUID."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils.
        return mh.InputUtils.safe_input(  # Use EOF-safe input wrapper
            "  Enter ticket ID: ",  # Prompt text for ticket UUID
            default_value="",  # No default -- user must provide ID
            allow_empty=True,  # Allow blank to signal cancellation
            context="ticket_id_prompt",  # Context label for EOF logging
        )

    @staticmethod
    def _print_ticket_created_summary(ticket_data: dict, subject: str, ticket_type: str) -> None:
        """Print + log the newly created ticket summary."""
        ticket_id = ticket_data.get("id", "unknown")  # Get new ticket UUID from response
        logging.debug("Ticket created: id=%s, status=%s", ticket_id, ticket_data.get("status"))  # Log result
        logging.warning(
            "\n  Ticket created successfully!" "\n  ID:      %s" "\n  Subject: %s" "\n  Type:    %s" "\n  Status:  %s",
            ticket_id,
            subject,
            ticket_type,
            ticket_data.get("status", "open"),
        )
        logging.info("Menu 189: Ticket creation complete, id=%s", ticket_id)  # Log success

    @staticmethod
    def _submit_create_ticket(org_id: str, body: dict, subject: str, ticket_type: str) -> None:
        """Send createOrgTicket API + print summary (or print + raise on error)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of mistapi + apisession.
        logging.info("Creating ticket '%s' (type=%s) in org %s", subject, ticket_type, org_id)
        try:
            response = mh.mistapi.api.v1.orgs.tickets.createOrgTicket(mh.apisession, org_id, body)
            OrgTicketManager._print_ticket_created_summary(getattr(response, "data", {}), subject, ticket_type)
        except Exception as error:  # Catch API errors during ticket creation
            logging.error("Failed to create ticket: %s", error)  # Log error with context
            logging.error("\n  Error creating ticket: %s", error)  # Show error to user
            raise  # Re-raise for upstream error handling

    @staticmethod
    def _build_update_body() -> dict[str, str]:  # Build ticket update body.
        """Collect optional update fields (subject, status, type) from user prompts."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils.
        body: dict[str, str] = {}  # Accumulate changed fields in a dict
        fields = (  # (api_key, prompt_text, eof_context) tuples for each updatable field
            ("subject", "  New subject (leave blank to skip): ", "update_ticket_subject"),
            ("status", "  New status [open/closed] (leave blank to skip): ", "update_ticket_status"),
            (
                "type",
                "  New type [question/problem/incident/feature_request] (leave blank to skip): ",
                "update_ticket_type",
            ),
        )
        for api_key, prompt, ctx in fields:  # Prompt for each updatable field in turn
            value = mh.InputUtils.safe_input(  # EOF-safe prompt for this field
                prompt,
                default_value="",
                allow_empty=True,
                context=ctx,
            )
            if value:  # Only include field if user provided a value
                body[api_key] = value  # Add user-supplied value to update body
        return body  # Return dict of fields to update (may be empty)

    @staticmethod
    def _update_via_api(org_id: str, ticket_id: str, body: dict[str, str]) -> None:
        """Send updateOrgTicket API call and print + log results."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of mistapi + apisession.
        logging.info("Updating ticket %s with fields: %s", ticket_id, list(body.keys()))  # Log before API call
        try:
            response = mh.mistapi.api.v1.orgs.tickets.updateOrgTicket(  # Call Mist API to update ticket
                mh.apisession,
                org_id,
                ticket_id,
                body,  # Pass session, org, ticket ID, body
            )
            logging.debug("Ticket updated: %s", getattr(response, "data", {}))  # Log full response
            logging.warning("\n  Ticket %s updated successfully!", ticket_id)  # Confirm to user
            for field, value in body.items():  # Show each changed field to user
                logging.warning("  %s: %s", field, value)  # Display field name and new value
            logging.info("Menu 191: Ticket update complete for %s", ticket_id)  # Log success
        except Exception as error:  # Catch API errors during ticket update
            logging.error("Failed to update ticket %s: %s", ticket_id, error)  # Log error with context
            logging.error("\n  Error updating ticket: %s", error)  # Show error to user
            raise  # Re-raise for upstream error handling

    @staticmethod
    def _prompt_comment_and_file() -> tuple[str, str]:
        """Prompt for comment text and optional attachment path."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils.
        comment_text = mh.InputUtils.safe_input(  # Prompt user for comment body text
            "  Enter comment text: ",
            default_value="",
            allow_empty=True,
            context="add_ticket_comment",
        )
        file_path = mh.InputUtils.safe_input(  # Prompt for optional file attachment path
            "  Attach a file? Enter path (leave blank to skip): ",
            default_value="",
            allow_empty=True,
            context="add_ticket_attachment",
        )
        return comment_text, file_path  # Tuple of (text, file_path)

    @staticmethod
    def _submit_comment(org_id: str, ticket_id: str, comment_text: str, file_path: str) -> None:
        """Submit comment with optional file attachment to ticket."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of mistapi + apisession.
        has_file = bool(file_path and os.path.isfile(file_path))  # Check if valid file was specified

        if has_file:  # Use multipart upload API when file is attached
            logging.info("Adding comment with attachment to ticket %s", ticket_id)  # Log before API call
            mh.mistapi.api.v1.orgs.tickets.addOrgTicketCommentFile(  # Multipart comment+file API
                mh.apisession,
                org_id,
                ticket_id,  # Session, org, and ticket identifiers
                comment=comment_text or None,  # Comment text (None if empty)
                file=file_path,  # Path to file for upload
            )
            logging.debug("Comment with file submitted to ticket %s", ticket_id)  # Log after API call
            logging.warning("\n  Comment with attachment added to ticket %s", ticket_id)  # Confirm to user
        elif file_path:  # User specified a path but file does not exist
            logging.warning(  # Warn about missing file path
                "File not found: %s -- adding comment without attachment", file_path
            )
            logging.warning("  Warning: File not found at '%s' -- adding comment only.", file_path)  # Alert user
            OrgTicketManager._submit_text_comment(org_id, ticket_id, comment_text)  # Fall back to text-only
        else:  # No file specified -- text-only comment
            OrgTicketManager._submit_text_comment(org_id, ticket_id, comment_text)  # Submit text comment

    @staticmethod
    def _submit_text_comment(org_id: str, ticket_id: str, comment_text: str) -> None:  # Submit a text-only comment.
        """Submit a text-only comment to a ticket."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of mistapi + apisession.
        logging.info("Adding text comment to ticket %s", ticket_id)  # Log before API call
        body = {"comment": comment_text}  # Build comment request body
        mh.mistapi.api.v1.orgs.tickets.addOrgTicketComment(  # Call Mist API to add comment
            mh.apisession,
            org_id,
            ticket_id,
            body,  # Session, org, ticket ID, and comment body
        )
        logging.debug("Text comment submitted to ticket %s", ticket_id)  # Log after API call
        logging.warning("\n  Comment added to ticket %s", ticket_id)  # Confirm to user

    # ------------------------------------------------------------------
    # Public entry points -- ticket viewing and export (Menu 192-193)
    # ------------------------------------------------------------------

    @staticmethod
    def view_ticket() -> None:  # View a single ticket.
        """Menu 192: View a single ticket with full comments and history."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils.
        logging.info("Menu 192: Starting ticket detail viewer")  # Log operation entry
        logging.debug("ENTRY: OrgTicketManager.view_ticket()")  # Debug trace
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org from cache or user prompt

        ticket_id = OrgTicketManager._select_ticket(org_id)  # Show ticket list for user selection
        if not ticket_id:  # User cancelled selection -- abort
            logging.warning("  Operation cancelled -- no ticket selected.")  # Inform user
            logging.info("View ticket cancelled: no ticket selected")  # Log the cancellation
            return  # Early exit

        ticket_data = OrgTicketManager._fetch_ticket_detail(org_id, ticket_id)  # Fetch full ticket+comments
        if not ticket_data:  # API returned empty or failed
            logging.error("  Could not retrieve ticket details.")  # Inform user of failure
            return  # Early exit

        OrgTicketManager._display_ticket_detail(ticket_data)  # Format and print to screen
        logging.info("Menu 192: Ticket detail view complete for %s", ticket_id)  # Log success

    @staticmethod
    def export_ticket_details() -> None:  # Export ticket details to file.
        """Menu 193: Export all tickets with full details and comments to CSV/SQLite."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils + DataExporter.
        logging.info("Menu 193: Starting full ticket detail export")  # Log operation entry
        logging.debug("ENTRY: OrgTicketManager.export_ticket_details()")  # Debug trace
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org from cache or user prompt
        tickets = OrgTicketManager._fetch_all_ticket_summaries(org_id)  # API list summaries
        if not tickets:  # No tickets found in the org
            logging.warning("\n  No tickets found in this organization.")  # Inform user
            return  # Nothing to export
        all_details = OrgTicketManager._collect_ticket_details(org_id, tickets)  # Per-ticket detail fetch
        if all_details:  # Export if we have any ticket details
            logging.info("Exporting %d ticket details", len(all_details))  # Log before export
            mh.DataExporter.write_with_format_selection(  # Write to CSV/SQLite via standard pipeline
                all_details,
                "OrgTicketDetails.csv",
                api_function_name="getOrgTicket",
            )
            logging.info("Menu 193: Full ticket detail export complete")  # Log success
        else:  # No details were retrieved
            logging.warning("\n  No ticket details could be retrieved.")  # Inform user

    # ------------------------------------------------------------------
    # Private helpers -- ticket selection and detail display
    # ------------------------------------------------------------------

    @staticmethod
    def _select_ticket(org_id: str) -> str:  # Prompt to select a ticket.
        """List tickets and let user pick by index, or enter ID manually."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils.
        tickets = OrgTicketManager._fetch_tickets_for_selection(org_id)  # Fetch + handle empty
        if not tickets:  # No tickets or fetch error
            return ""  # Signal cancellation to caller
        OrgTicketManager._render_ticket_list_table(tickets)  # Display numbered ticket table
        logging.warning("\n  Enter a number (1-%d) to select, or 'm' to enter ID manually.", len(tickets))
        choice = mh.InputUtils.safe_input(  # Prompt user for selection input
            "  Selection: ",
            default_value="",
            allow_empty=True,
            context="select_ticket",
        )
        if not choice:  # Blank input -- cancel
            return ""  # Signal cancellation
        if choice.lower() == "m":  # Manual ID entry path
            return OrgTicketManager._prompt_ticket_id()  # Prompt for manual ticket UUID
        return OrgTicketManager._resolve_ticket_choice(choice, tickets)  # Parse + validate index

    @staticmethod
    def _fetch_tickets_for_selection(org_id: str) -> list:
        """Fetch ticket summaries for selection; print + return [] on error/empty."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of mistapi + apisession.
        logging.info("Fetching ticket list for selection (org %s)", org_id)  # Log before API call
        try:
            response = mh.mistapi.api.v1.orgs.tickets.listOrgTickets(  # Fetch ticket summaries
                mh.apisession,
                org_id,
                duration="365d",  # 1-year history window
            )
            tickets = getattr(response, "data", []) or []  # Extract ticket list
            logging.debug("Retrieved %d tickets for selection", len(tickets))  # Log count
        except Exception as error:  # Catch API failures
            logging.error("Failed to fetch tickets for selection: %s", error)  # Log error
            logging.error("  Error fetching tickets: %s", error)  # Show error to user
            return []  # Signal failure with empty list
        if not tickets:  # API returned no tickets
            logging.warning("\n  No tickets found in this organization.")  # Inform user
        return tickets  # Return list (possibly empty)

    @staticmethod
    def _render_ticket_list_table(tickets: list) -> None:
        """Print a numbered table of ticket #/status/type/subject for selection."""
        header_line = f"  {'#':<4} {'Status':<10} {'Type':<18} {'Subject'}"  # Column header row
        separator = f"  {'-' * 4} {'-' * 10} {'-' * 18} {'-' * 40}"  # Separator row
        logging.warning(
            "\n  Organization Support Tickets:\n%s\n%s",
            header_line,
            separator,
        )  # Section header + column headers + separator in one record
        for index, ticket in enumerate(tickets, 1):  # Display numbered rows
            status = ticket.get("status", "unknown")  # Ticket status field
            ttype = ticket.get("type", "unknown")  # Ticket type field
            subject = ticket.get("subject", "(no subject)")  # Ticket subject field
            logging.warning("  %-4d %-10s %-18s %s", index, status, ttype, subject)  # Print formatted row

    @staticmethod
    def _resolve_ticket_choice(choice: str, tickets: list) -> str:
        """Parse numeric choice into ticket ID; print error + return '' on bad input."""
        try:
            idx = int(choice) - 1  # Convert 1-based to 0-based index
        except ValueError:  # Non-numeric input that was not 'm'
            logging.error("  Invalid selection: %s", choice)  # Inform user of bad input
            return ""  # Signal cancellation
        if not 0 <= idx < len(tickets):  # Index out of range
            logging.error("  Invalid selection: %s", choice)  # Inform user of bad input
            return ""  # Signal cancellation
        selected_id = tickets[idx].get("id", "")  # Extract ticket ID
        selected_subj = tickets[idx].get("subject", "(no subject)")  # Extract subject for confirmation
        logging.warning("  Selected: %s", selected_subj)  # Confirm selection to user
        logging.info("User selected ticket %s (%s)", selected_id, selected_subj)  # Log selection
        return selected_id  # Return chosen ticket ID

    @staticmethod
    def _fetch_ticket_detail(org_id: str, ticket_id: str) -> dict:  # Fetch one ticket detail.
        """Fetch full ticket data including comments via getOrgTicket."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of mistapi + apisession.
        logging.info("Fetching detail for ticket %s", ticket_id)  # Log before API call
        try:
            response = mh.mistapi.api.v1.orgs.tickets.getOrgTicket(  # Call SDK for full ticket detail
                mh.apisession,
                org_id,
                ticket_id,
                duration="365d",  # Look back 1 year for comment history
            )
            ticket_data = getattr(response, "data", {}) or {}  # Extract response data dict
            logging.debug("Received ticket detail: %d fields", len(ticket_data))  # Log field count
            return ticket_data  # Return the full ticket dict with comments
        except Exception as error:  # Catch API failures
            logging.error("Failed to fetch ticket %s: %s", ticket_id, error)  # Log error
            logging.error("  Error fetching ticket %s: %s", ticket_id, error)  # Show error to user
            return {}  # Return empty dict to signal failure

    @staticmethod
    def _fetch_all_ticket_summaries(org_id: str) -> list:
        """Fetch ticket-summary list via listOrgTickets, raise on failure."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of mistapi + apisession.
        logging.info("Fetching ticket list for org %s", org_id)  # Log before API call
        try:
            response = mh.mistapi.api.v1.orgs.tickets.listOrgTickets(  # Fetch all ticket summaries
                mh.apisession,
                org_id,
                duration="365d",  # 1-year window for ticket history
            )
            tickets = getattr(response, "data", []) or []  # Extract list from APIResponse
            logging.debug("Found %d tickets to export with details", len(tickets))  # Log count
            return tickets  # Return summary list to caller
        except Exception as error:  # Catch API failures on ticket list
            logging.error("Failed to fetch ticket list: %s", error)  # Log the failure
            logging.error("\n  Error fetching tickets: %s", error)  # Show error to user
            raise  # Re-raise for upstream handling

    @staticmethod
    def _collect_ticket_details(org_id: str, tickets: list) -> list:
        """For each summary in tickets, fetch + flatten its full detail. Returns list of flat dicts."""
        all_details = []  # Accumulate flattened ticket+comment records
        logging.warning("\n  Fetching details for %d tickets...", len(tickets))  # Progress indicator
        for index, ticket in enumerate(tickets, 1):  # Iterate each ticket summary
            tid = ticket.get("id", "")  # Extract ticket ID from summary
            if not tid:  # Skip tickets without valid IDs
                continue  # Move to next ticket
            logging.info("Fetching detail %d/%d: ticket %s", index, len(tickets), tid)  # Progress log
            detail = OrgTicketManager._fetch_ticket_detail(org_id, tid)  # Get full ticket data
            if detail:  # Only include tickets that returned data
                all_details.append(DataProcessingUtils.flatten_dict(detail))  # Flatten and add
            logging.debug("Fetched detail %d/%d", index, len(tickets))  # Progress debug log
        return all_details  # All flattened records (may be empty)

    @staticmethod
    def _display_ticket_detail(ticket_data: dict) -> None:  # Display ticket detail.
        """Format and display a ticket with its full comment history."""
        meta_fields = (  # (label, key, default) for the metadata block
            ("Ticket", "subject", "(no subject)"),
            ("ID    ", "id", "unknown"),
            ("Status", "status", "unknown"),
            ("Type  ", "type", "unknown"),
            ("Created", "created_at", "unknown"),
            ("Updated", "updated_at", "unknown"),
        )
        top_bar = "  " + "=" * 60  # Top separator bar
        rows = "\n".join(  # Metadata rows built off meta_fields
            f"  {label}: {ticket_data.get(key, default)}" for label, key, default in meta_fields
        )
        section_sep = "  " + "-" * 60  # Section separator between metadata and comments
        logging.warning("\n%s\n%s\n%s", top_bar, rows, section_sep)  # Render header block atomically
        OrgTicketManager._render_comments_block(ticket_data.get("comments", []))  # Render comments

    @staticmethod
    def _render_comments_block(comments: list) -> None:
        """Render the comments section: header + one block per comment + attachments."""
        if not comments:  # No comments on this ticket
            logging.warning("  No comments on this ticket.")  # Inform user
            return  # Nothing else to render
        logging.warning("  Comments (%d):", len(comments))  # Comment section header with count
        for idx, comment in enumerate(comments, 1):  # Iterate each comment
            author = comment.get("author", "unknown")  # Get comment author name
            created = comment.get("created_at", "unknown")  # Get comment timestamp
            text = comment.get("comment", "(no text)")  # Get comment body text
            logging.warning("\n  [%d] %s -- %s\n      %s", idx, author, created, text)  # Header + body atomically
            for att in comment.get("attachments", []) or []:  # Iterate attachments (may be empty)
                logging.warning(
                    "      Attachment: %s",
                    att.get("name", att.get("content_url", "file")),
                )

        logging.warning("  %s", "=" * 60)  # Bottom separator bar
