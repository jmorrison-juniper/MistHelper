"""Comparison-table rendering for the address-audit feature (1003-site-address-audit).

Renders the audited rows as a 7-column terminal table (current Mist address on
the left, the suggested correction on the right) and, afterwards, prompts the
operator to either save the full results to CSV or quit. The terminal view
truncates the two widest columns for readability; the saved CSV keeps full
values (handled by ``AddressAuditReporter``).
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

import logging  # Action logging before/after every operation (project NON-NEGOTIABLE).

from prettytable import PrettyTable  # Terminal table formatting (project dependency).

from src.site.address_audit.models import AuditResult  # Per-row audit record.
from src.utils.input_utils import InputUtils  # EOF-safe operator prompts.

_COLUMN_NAMES = [  # The seven table columns, in display order.
    "Site Name",  # Mist site name (or - when unmatched).
    "Current Mist Address",  # Address currently on the Mist site record.
    "CSV Address",  # Address supplied by the customer CSV.
    "SNMP Location",  # SNMP-derived location reference (truncated in terminal).
    "Suggested Address",  # Resolver's best correction (truncated in terminal).
    "Source",  # Which tier produced the suggestion.
    "Issue Type",  # One of the nine classification states.
]
_TRUNCATE_WIDTH = 40  # Max terminal width for the two widest columns.


class ComparisonTableRenderer:
    """Build the comparison table and run the post-table save/quit prompt."""

    def render(self, results: list[AuditResult]) -> str:
        """Build, print, and return the comparison table for ``results``."""
        logging.info("Rendering comparison table for %d row(s)", len(results))  # Action-log start.
        table = PrettyTable()  # Fresh table instance.
        table.field_names = _COLUMN_NAMES  # Apply the seven column headers.
        table.align = "l"  # Left-align all cells for readability.
        for result in results:  # Add one terminal row per audited CSV row.
            table.add_row(self._build_row(result))  # Append the (truncated) row cells.
        rendered = table.get_string()  # Materialize the table as a string.
        print(rendered)  # Show the table to the operator.
        logging.debug("Comparison table rendered (%d rows)", len(results))  # Action-log completion.
        return rendered  # Return for tests/callers.

    def _build_row(self, result: AuditResult) -> list[str]:
        """Assemble one terminal row, truncating the two widest columns."""
        site = result.matched_site  # Match outcome for this row.
        mist_text = self._format_address(site.mist_address)  # Current Mist address as text.
        csv_text = self._format_csv_address(result.address_row)  # CSV address as text.
        snmp_text = self._truncate(site.snmp_location or "(none)")  # SNMP location (truncated).
        suggested = self._truncate(result.suggested_address or "-")  # Suggestion (truncated).
        return [  # Seven cells matching _COLUMN_NAMES order.
            site.site_name or "-",  # Site name or placeholder.
            mist_text or "-",  # Mist address or placeholder.
            csv_text or "-",  # CSV address or placeholder.
            snmp_text,  # Truncated SNMP location.
            suggested,  # Truncated suggestion.
            result.source,  # Source label.
            result.issue_type,  # Classification state.
        ]

    def prompt_post_table(self, results: list[AuditResult]) -> str:
        """Print a one-line summary, then loop until the operator picks save/quit."""
        logging.info("Prompting operator for post-table action")  # Action-log start.
        print(self._summary_line(results))  # Show the per-state summary line.
        print("\n[1] Save comparison as CSV to data/ for review")  # Save option.
        print("[q] Quit without saving")  # Quit option.
        while True:  # Re-prompt until a valid choice is entered.
            choice = InputUtils.safe_input("Choice: ", context="address_audit_post_table").strip().lower()
            if choice == "1":  # Operator chose to save.
                logging.debug("Operator selected save")  # Trace the choice.
                return "save"  # Engine will invoke the reporter.
            if choice == "q":  # Operator chose to quit.
                logging.debug("Operator selected quit")  # Trace the choice.
                return "quit"  # Engine exits without saving.
            print("Invalid choice. Enter 1 to save or q to quit.")  # One-line error, then re-prompt.

    def _summary_line(self, results: list[AuditResult]) -> str:
        """Build the 'N sites processed: ...' per-state summary string."""
        counts: dict[str, int] = {}  # Accumulate counts per classification state.
        for result in results:  # Tally every row.
            counts[result.issue_type] = counts.get(result.issue_type, 0) + 1  # Increment that state.
        breakdown = ", ".join(f"{count} {state}" for state, count in sorted(counts.items()))  # Readable list.
        return f"\nAudit complete. {len(results)} sites processed: {breakdown}"  # Summary line.

    @staticmethod
    def _truncate(text: str) -> str:
        """Truncate a cell to the terminal width with an ellipsis when needed."""
        if len(text) <= _TRUNCATE_WIDTH:  # Already short enough.
            return text  # Return unchanged.
        return text[: _TRUNCATE_WIDTH - 3] + "..."  # Trim and mark truncation.

    @staticmethod
    def _format_address(address: dict) -> str:
        """Join a Mist address dict into a single line."""
        parts = [  # Ordered address components.
            address.get("address", ""),  # Street.
            address.get("city", ""),  # City.
            address.get("state", ""),  # State code.
            str(address.get("zip", "")),  # ZIP.
        ]
        return " ".join(part for part in parts if part).strip()  # Skip blanks; trim.

    @staticmethod
    def _format_csv_address(row) -> str:
        """Join a CSV ``AddressRow`` into a single line."""
        parts = [row.address, row.city, row.state, row.zip_code]  # CSV address components.
        return " ".join(part for part in parts if part).strip()  # Skip blanks; trim.
