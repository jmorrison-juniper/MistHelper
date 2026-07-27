"""CSV ingestion for the address-audit feature (1003-site-address-audit).

Parses the customer-provided, header-less CSV into ``AddressRow`` objects. The
six positional columns are: serial, model, address, city, state, zip.

Real customer exports vary: a file saved as ``.csv`` from Excel is comma-
delimited, while a ``.tsv`` (or a tab-pasted file) is tab-delimited. The
delimiter is therefore **auto-detected** per file rather than assumed. Addresses
themselves may contain the delimiter (for example a comma in "Mall, Suite 330"), so the
row is parsed by its fixed structure -- the first two fields are serial/model,
the last three are city/state/zip, and everything in between is rejoined as the
address. Rows whose serial is empty or non-numeric after stripping are skipped
and counted (never emitted), since the serial is the golden key for matching.
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

import csv  # Standard-library delimited-file parsing.
import logging  # Action logging before/after every operation (project NON-NEGOTIABLE).
import os  # File-existence checks and path handling.
import re  # Whitespace-collapsing in address sanitization.

from src.site.address_audit.models import AddressRow  # Parsed-row dataclass.

_MIN_COLUMNS = 6  # serial, model, address, city, state, zip (address may span >1 physical field).
_CANDIDATE_DELIMITERS = ("\t", ",", ";", "|")  # Delimiters to probe, in priority order.


class CSVAddressIngester:
    """Read and sanitize the customer address CSV (delimiter auto-detected)."""

    def load(self, path: str) -> tuple[list[AddressRow], int]:
        """Parse ``path`` into ``AddressRow`` objects plus a parse-failure count."""
        logging.info("Starting CSV ingestion from %s", path)  # Action-log the source file.
        if not os.path.isfile(path):  # Guard: a missing file is a controlled error, not a crash.
            logging.error("CSV file not found: %s", path)  # Log the missing-file condition.
            raise FileNotFoundError(f"CSV file not found: {path}")  # Controlled, caller-catchable error.
        with open(path, encoding="utf-8-sig", newline="") as handle:  # utf-8-sig strips an Excel BOM.
            sample = self._read_sample_line(handle)  # First non-blank line, for delimiter detection.
            handle.seek(0)  # Rewind so the csv.reader sees the whole file (quoted newlines intact).
            delimiter = self._detect_delimiter(sample)  # Pick tab/comma/and so on from the data itself.
            logging.debug("Detected delimiter %r for %s", delimiter, path)  # Trace the chosen delimiter.
            reader = csv.reader(handle, delimiter=delimiter)  # Reader honors quoted multi-line fields.
            rows, failures = self._parse_reader(reader)  # Parse every record.
        logging.debug("Ingested %d rows, %d parse failures", len(rows), failures)  # Action-log totals.
        return rows, failures  # Hand both back to the orchestrator.

    @staticmethod
    def _read_sample_line(handle: object) -> str:
        """Return the first non-blank physical line from an open handle, or ''."""
        for line in handle:  # type: ignore[attr-defined]  # Iterate the file lazily.
            if line.strip():  # First line with visible content.
                return line  # Use it for delimiter detection.
        return ""  # Empty file -> no sample line.

    def _parse_reader(self, reader: object) -> tuple[list[AddressRow], int]:
        """Consume a csv.reader into parsed rows + a parse-failure count."""
        rows: list[AddressRow] = []  # Accumulator for valid parsed rows.
        failures = 0  # Counter for skipped (invalid-serial) rows.
        for raw_fields in reader:  # type: ignore[attr-defined]  # Walk every record.
            if not any(field.strip() for field in raw_fields):  # Entirely blank line.
                continue  # Silent skip -- blank lines are not parse failures.
            parsed = self._parse_row(raw_fields)  # Convert fields to an AddressRow or None.
            if parsed is None:  # None signals an invalid/empty-serial row.
                failures += 1  # Count the skip for the run summary.
                continue  # Skip without emitting.
            rows.append(parsed)  # Keep the valid row.
        return rows, failures  # Return both to the caller.

    def _detect_delimiter(self, sample: str) -> str:
        """Choose the delimiter that best splits the first data line into >=6 fields."""
        if not sample.strip():  # Empty file -> any delimiter works (no rows to parse).
            return ","  # Harmless default.
        return self._choose_delimiter(sample)  # Delegate the probing loop to keep CC bounded.

    def _choose_delimiter(self, sample: str) -> str:
        """Probe each candidate delimiter and return the one giving the most fields."""
        # WHY: split from _detect_delimiter so the empty-sample guard does not inflate CC past 5.
        best_delimiter = ","  # Fallback when nothing yields enough columns.
        best_count = -1  # Highest field count seen so far.
        for candidate in _CANDIDATE_DELIMITERS:  # Probe each candidate delimiter.
            count = len(sample.split(candidate))  # Field count this delimiter would produce.
            if count >= _MIN_COLUMNS and candidate == "\t":  # A tab that yields >=6 wins outright.
                return candidate  # Tab is the documented format; prefer it when it fits.
            if count > best_count:  # Otherwise track the delimiter giving the most fields.
                best_count = count  # Remember the new best field count.
                best_delimiter = candidate  # Remember the delimiter that produced it.
        return best_delimiter  # Most-splitting delimiter (comma for Excel exports).

    def _parse_row(self, raw_fields: list[str]) -> AddressRow | None:
        """Build an ``AddressRow`` from raw fields, or ``None`` if the serial is invalid."""
        cleaned = [field.strip() for field in raw_fields]  # Trim every field up front.
        if len(cleaned) < _MIN_COLUMNS:  # Too few columns to be a valid 6-field record.
            if any(cleaned):  # Only log non-blank short rows (blank lines are silent skips).
                logging.debug("Skipping short row (%d fields): %r", len(cleaned), raw_fields)  # Trace.
            return None  # Signal a parse failure.
        serial = cleaned[0]  # Serial is the golden key (already trimmed).
        if not serial.isdigit():  # Non-numeric serial cannot match a device (also rejects headers).
            logging.debug("Skipping row with non-numeric serial: %r", cleaned[0])  # Trace the skip.
            return None  # Signal a parse failure to the caller.
        return self._build_row(cleaned)  # Assemble the AddressRow by fixed structure.

    def _build_row(self, cleaned: list[str]) -> AddressRow:
        """Assemble an ``AddressRow`` using first-2 / last-3 anchors, address in the middle."""
        address_parts = cleaned[2:-3]  # Everything between model and city is the address (>=1 field).
        joined_address = ", ".join(part for part in address_parts if part)  # Rejoin any comma-split address.
        return AddressRow(  # Build the sanitized row.
            serial=cleaned[0],  # Validated numeric serial.
            model=cleaned[1],  # Device model (display only).
            address=self.sanitize_address(joined_address),  # Clean the (possibly rejoined) address.
            city=cleaned[-3],  # Third-from-last field is the city.
            state=cleaned[-2],  # Second-from-last is the state code.
            zip_code=cleaned[-1],  # Last field is the ZIP.
        )

    @staticmethod
    def sanitize_address(raw: str) -> str:
        """Strip, flatten embedded newlines, and collapse repeated whitespace."""
        flattened = raw.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")  # Newlines -> space.
        collapsed = re.sub(r"\s+", " ", flattened)  # Collapse runs of whitespace to a single space.
        return collapsed.strip()  # Trim leading/trailing whitespace.
