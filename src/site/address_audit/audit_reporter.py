"""CSV report writer for the address-audit feature (1003-site-address-audit).

Persists the full audit results to a timestamped CSV under ``data/`` so the
operator can review (or hand back to the customer) the old-vs-suggested address
comparison. Unlike the terminal table, the saved CSV keeps full, untruncated
values.
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

import csv  # Standard-library CSV writing.
import logging  # Action logging before/after every operation (project NON-NEGOTIABLE).
import os  # Path construction and directory creation.
from datetime import UTC, datetime  # Timestamped output filenames.

from src.site.address_audit.models import AuditResult  # Per-row audit record.

_HEADER = [  # CSV header row -- matches the seven terminal columns.
    "Site Name",  # Mist site name.
    "Current Mist Address",  # Address on the Mist record.
    "CSV Address",  # Customer-supplied address.
    "SNMP Location",  # SNMP-derived location (full value).
    "Suggested Address",  # Resolver suggestion (full value).
    "Source",  # Originating tier.
    "Issue Type",  # Classification state.
]


class AddressAuditReporter:
    """Write the audit results to a timestamped CSV file in ``data/``."""

    def save(self, results: list[AuditResult], output_dir: str = "data") -> str:
        """Write ``results`` to ``data/address_audit_<UTC timestamp>.csv``; return the path."""
        logging.info("Saving address-audit report (%d rows)", len(results))  # Action-log start.
        os.makedirs(output_dir, exist_ok=True)  # Ensure the output directory exists.
        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")  # UTC timestamp for the filename.
        path = os.path.join(output_dir, f"address_audit_{stamp}.csv")  # Full output path.
        with open(path, "w", encoding="utf-8", newline="") as handle:  # Open for CSV writing.
            writer = csv.writer(handle)  # Standard CSV writer.
            writer.writerow(_HEADER)  # Write the header row first.
            for result in results:  # One CSV row per audited row.
                writer.writerow(self._build_row(result))  # Write full (untruncated) values.
        logging.debug("Address-audit report written to %s", path)  # Action-log completion.
        return path  # Return the written path to the caller.

    def _build_row(self, result: AuditResult) -> list[str]:
        """Assemble one full-value CSV row from an ``AuditResult``."""
        site = result.matched_site  # Match outcome for this row.
        return [  # Seven cells matching _HEADER order, untruncated.
            site.site_name or "",  # Site name.
            self._format_address(site.mist_address),  # Full current Mist address.
            self._format_csv_address(result.address_row),  # Full CSV address.
            site.snmp_location or "",  # Full SNMP location.
            result.suggested_address or "",  # Full suggested address.
            result.source,  # Source label.
            result.issue_type,  # Classification state.
        ]

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
