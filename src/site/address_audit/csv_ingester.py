"""CSV ingestion for the address-audit feature (1003-site-address-audit).

Parses the customer-provided, tab-delimited, header-less CSV into ``AddressRow``
objects. The columns (positional) are: serial, model, address, city, state, zip.
Addresses frequently contain embedded newlines/whitespace from the source
export, so each is sanitized. Rows whose serial is empty or non-numeric after
stripping are skipped and counted (never emitted), since the serial is the
golden key for site matching.
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

import csv  # Standard-library tab-delimited parsing.
import logging  # Action logging before/after every operation (project NON-NEGOTIABLE).
import os  # File-existence checks and path handling.
import re  # Whitespace-collapsing in address sanitization.

from src.site.address_audit.models import AddressRow  # Parsed-row dataclass.

_EXPECTED_COLUMNS = 6  # serial, model, address, city, state, zip.


class CSVAddressIngester:
    """Read and sanitize the customer tab-delimited address CSV."""

    def load(self, path: str) -> tuple[list[AddressRow], int]:
        """Parse ``path`` into ``AddressRow`` objects plus a parse-failure count."""
        logging.info("Starting CSV ingestion from %s", path)  # Action-log the source file.
        if not os.path.isfile(path):  # Guard: a missing file is a controlled error, not a crash.
            logging.error("CSV file not found: %s", path)  # Log the missing-file condition.
            raise FileNotFoundError(f"CSV file not found: {path}")  # Controlled, caller-catchable error.
        rows: list[AddressRow] = []  # Accumulator for valid parsed rows.
        failures = 0  # Counter for skipped (invalid-serial) rows.
        with open(path, encoding="utf-8", newline="") as handle:  # UTF-8 per the data contract.
            reader = csv.reader(handle, delimiter="\t")  # Tab-delimited, no header row.
            for raw_fields in reader:  # Walk every physical CSV record.
                parsed = self._parse_row(raw_fields)  # Convert fields to an AddressRow or None.
                if parsed is None:  # None signals an invalid/empty-serial row.
                    failures += 1  # Count the skip for the run summary.
                    continue  # Skip without emitting.
                rows.append(parsed)  # Keep the valid row.
        logging.debug("Ingested %d rows, %d parse failures", len(rows), failures)  # Action-log totals.
        return rows, failures  # Hand both back to the orchestrator.

    def _parse_row(self, raw_fields: list[str]) -> AddressRow | None:
        """Build an ``AddressRow`` from raw fields, or ``None`` if the serial is invalid."""
        if not raw_fields:  # Entirely blank line.
            return None  # Treat as a parse failure.
        fields = self._pad_fields(raw_fields)  # Normalize to the expected column count.
        serial = fields[0].strip()  # Serial is the golden key; trim surrounding whitespace.
        if not serial or not serial.isdigit():  # Empty or non-numeric serial cannot match a device.
            logging.debug("Skipping row with invalid serial: %r", fields[0])  # Trace the skip.
            return None  # Signal a parse failure to the caller.
        return AddressRow(  # Assemble the sanitized row.
            serial=serial,  # Validated numeric serial.
            model=fields[1].strip(),  # Device model (display only).
            address=self.sanitize_address(fields[2]),  # Clean the messy address field.
            city=fields[3].strip(),  # City name.
            state=fields[4].strip(),  # 2-letter state code.
            zip_code=fields[5].strip(),  # 5-digit ZIP.
        )

    @staticmethod
    def _pad_fields(raw_fields: list[str]) -> list[str]:
        """Pad/truncate a raw record to exactly the expected column count."""
        padded = list(raw_fields)  # Copy so we never mutate the reader's list.
        while len(padded) < _EXPECTED_COLUMNS:  # Short rows get empty trailing fields.
            padded.append("")  # Append blanks until the column count matches.
        return padded[:_EXPECTED_COLUMNS]  # Drop any extra trailing columns.

    @staticmethod
    def sanitize_address(raw: str) -> str:
        """Strip, flatten embedded newlines, and collapse repeated whitespace."""
        flattened = raw.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")  # Newlines -> space.
        collapsed = re.sub(r"\s+", " ", flattened)  # Collapse runs of whitespace to a single space.
        return collapsed.strip()  # Trim leading/trailing whitespace.
