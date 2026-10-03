"""Pure helpers for the client fingerprint census report."""

from __future__ import annotations  # WHY: allow forward-compatible annotations in this report package.

import logging  # WHY: trace validation and normalization decisions for the operator.
from dataclasses import dataclass, fields  # WHY: keep export column order in one declared type.
from typing import Final  # WHY: define stable constants and response row shapes.

logger = logging.getLogger(__name__)  # WHY: name this module in the shared log stream.

DISTINCT_FIELDS: Final[tuple[str, ...]] = ("family", "model", "os", "os_type")  # WHY: OpenAPI enum source.
UNKNOWN_VALUE: Final[str] = "Unknown"  # WHY: keep a readable bucket for missing API properties.
DISPLAY_LIMIT: Final[int] = 20  # WHY: protect narrow consoles from very long reports.
EXPORT_FILENAME: Final[str] = "ClientFingerprintCensus.csv"  # WHY: one stable operator report name.
EXPORT_ENDPOINT_NAME: Final[str] = "countOrgClientFingerprints"  # WHY: match the OpenAPI operation ID.
EMPTY_CENSUS_MESSAGE: Final[str] = "The client fingerprint census is empty for this site."  # WHY: clear empty state.


RawFingerprintCount = dict[str, object]  # WHY: live rows use the selected distinct field as the value key.


@dataclass(frozen=True, slots=True)
class FingerprintCensusRow:
    """One normalized client fingerprint census export row."""

    site_id: str  # WHY: identify the selected site in each exported row.
    site_name: str  # WHY: make the CSV useful without another site lookup.
    distinct: str  # WHY: record which fingerprint field grouped the count.
    value: str  # WHY: hold the grouped fingerprint value for the selected field.
    count: int  # WHY: hold the number of clients in this fingerprint group.

    @classmethod
    def column_names(cls) -> list[str]:
        """Return the export column names in stable order."""
        return [field.name for field in fields(cls)]  # WHY: the dataclass declares the CSV schema.

    def as_row(self) -> dict[str, str | int]:
        """Return this census row as a flat export dictionary."""
        return {field.name: getattr(self, field.name) for field in fields(self)}  # WHY: exporter takes dict rows.


class FingerprintCensusModel:
    """Normalize, validate, and sort client fingerprint census data."""

    @staticmethod
    def validate_distinct(distinct: str) -> str:
        """Return a valid distinct field, or raise a clear error."""
        logger.info("Validating client fingerprint distinct field")  # WHY: trace operator input validation.
        normalized = distinct.strip()  # WHY: ignore accidental whitespace from the prompt.
        if normalized not in DISTINCT_FIELDS:  # WHY: reject values outside the OpenAPI enum.
            logger.error("Invalid client fingerprint distinct field %s", normalized)  # WHY: state bad input.
            raise ValueError(f"Unsupported distinct field: {normalized}")  # WHY: tests and callers need failure.
        logger.debug("Validated client fingerprint distinct field %s", normalized)  # WHY: record accepted input.
        return normalized  # WHY: downstream code uses the normalized field.

    @staticmethod
    def normalize_rows(
        raw_rows: list[RawFingerprintCount],
        site_id: str,
        site_name: str,
        distinct: str,
    ) -> list[FingerprintCensusRow]:
        """Return sorted export rows for the raw count response."""
        logger.info("Normalizing client fingerprint census rows")  # WHY: trace the data transform step.
        valid_distinct = FingerprintCensusModel.validate_distinct(distinct)  # WHY: guard rows before export.
        rows = [  # WHY: convert each JSON row into the stable dataclass schema.
            FingerprintCensusModel._normalize_row(raw_row, site_id, site_name, valid_distinct) for raw_row in raw_rows
        ]
        sorted_rows = sorted(rows, key=lambda row: (-row.count, row.value.lower()))  # WHY: table shows top counts.
        logger.debug("Normalized client fingerprint census rows=%d", len(sorted_rows))  # WHY: result summary.
        return sorted_rows  # WHY: caller exports and displays the sorted rows.

    @staticmethod
    def top_rows(rows: list[FingerprintCensusRow]) -> list[FingerprintCensusRow]:
        """Return the rows that the console table should show."""
        logger.info("Selecting client fingerprint census display rows")  # WHY: trace console truncation.
        selected = rows[:DISPLAY_LIMIT]  # WHY: the console contract shows only the top rows.
        logger.debug("Selected client fingerprint census display rows=%d", len(selected))  # WHY: count output.
        return selected  # WHY: operation prints this subset only.

    @staticmethod
    def _normalize_row(
        raw_row: RawFingerprintCount,
        site_id: str,
        site_name: str,
        distinct: str,
    ) -> FingerprintCensusRow:
        """Return one normalized census row."""
        raw_value = raw_row.get("property", raw_row.get(distinct))  # WHY: live org rows key by distinct field.
        value = FingerprintCensusModel._read_value(raw_value)  # WHY: API field can be absent.
        count = FingerprintCensusModel._read_count(raw_row.get("count"))  # WHY: API value must become an integer.
        return FingerprintCensusRow(site_id, site_name, distinct, value, count)  # WHY: dataclass fixes schema.

    @staticmethod
    def _read_value(raw_value: object) -> str:
        """Return a readable grouped value."""
        if raw_value is None:  # WHY: missing property needs a stable export bucket.
            return UNKNOWN_VALUE  # WHY: CSV readers need text, not a blank unknown.
        value = str(raw_value).strip()  # WHY: normalize whitespace in API strings.
        return value or UNKNOWN_VALUE  # WHY: empty strings belong in the unknown bucket.

    @staticmethod
    def _read_count(raw_count: object) -> int:
        """Return a safe integer count."""
        if isinstance(raw_count, bool):  # WHY: bool is an int subclass, but it is not a count.
            return 0  # WHY: invalid counts must not inflate the census.
        if isinstance(raw_count, int):  # WHY: the usual API shape already gives an integer.
            return max(raw_count, 0)  # WHY: negative counts are not meaningful for a census.
        if isinstance(raw_count, str) and raw_count.isdigit():  # WHY: tolerate a stringified integer.
            return int(raw_count)  # WHY: preserve valid numeric content from the API.
        return 0  # WHY: untrusted shapes become a safe zero.
