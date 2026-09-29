"""Pure models for CSV import validation and sanitized reporting."""

from __future__ import annotations  # WHY: allow compact type annotations without runtime imports.

import csv  # WHY: parse operator CSV files with the standard dialect support.
import logging  # WHY: record validation actions without exposing row secrets.
from dataclasses import dataclass, fields  # WHY: declare row and definition contracts once.
from pathlib import Path  # WHY: type resolved CSV paths without hard-coded separators.
from typing import Any, ClassVar  # WHY: type class constants and JSON-like result values.

logger = logging.getLogger(__name__)  # WHY: name the logger for tests and operator diagnostics.

MASK = "***"  # WHY: one mask value prevents secret leakage in previews and summaries.
PREVIEW_LIMIT = 10  # WHY: the operator needs the first ten rows only.
CONFIRM_VERB = "IMPORT"  # WHY: one exact destructive confirmation verb across the feature.


@dataclass(frozen=True, slots=True)
class CsvImportDefinition:
    """Describe one supported import endpoint and its CSV contract."""

    key: str  # WHY: identify the import type in prompts, tests, and logs.
    label: str  # WHY: show a clear name to the operator.
    file_name: str  # WHY: anchor the input file under data/ by name.
    scope: str  # WHY: choose organization or site identifier resolution.
    operation_id: str  # WHY: bind the type to the audited Mist API operation.
    required_columns: tuple[str, ...]  # WHY: reject bad files before any Mist request.
    optional_columns: tuple[str, ...]  # WHY: document accepted example columns for preview order.
    secret_columns: tuple[str, ...] = ()  # WHY: mask PSK secrets wherever rows appear.

    @property
    def allowed_columns(self) -> tuple[str, ...]:
        """Return known columns in a stable order."""
        return (*self.required_columns, *self.optional_columns)  # WHY: required columns lead preview tables.


@dataclass(frozen=True, slots=True)
class CsvImportBatch:
    """Hold one parsed CSV file and its import definition."""

    definition: CsvImportDefinition  # WHY: keep row data tied to the selected endpoint.
    file_path: Path  # WHY: write diagnostics with the exact resolved file path.
    fieldnames: tuple[str, ...]  # WHY: preserve the header for validation and tests.
    rows: tuple[dict[str, str], ...]  # WHY: hold immutable parsed rows for preview and count.

    @property
    def row_count(self) -> int:
        """Return the number of data rows in the CSV file."""
        return len(self.rows)  # WHY: confirmation must match this exact count.


@dataclass(frozen=True, slots=True)
class CsvImportResult:
    """Represent one sanitized row for CsvImportLog.csv."""

    import_type: str  # WHY: identify which Mist import endpoint ran.
    row_count: int  # WHY: audit only the scope, not any row secret.
    dry_run: bool  # WHY: distinguish rehearsal from a live import.
    status: str  # WHY: summarize dry_run, sent, error, or cancelled.
    message: str  # WHY: give a sanitized operator-readable result.

    @classmethod
    def column_names(cls) -> list[str]:
        """Return the CSV output columns in dataclass order."""
        return [field.name for field in fields(cls)]  # WHY: one source controls log column order.

    def as_row(self) -> dict[str, Any]:
        """Return the result as a CSV row."""
        return {field.name: getattr(self, field.name) for field in fields(self)}  # WHY: csv.DictWriter needs a dict.


class CsvImportCatalog:
    """Provide the supported CSV import definitions."""

    _PSK_REQUIRED: ClassVar[tuple[str, ...]] = ("name", "ssid", "passphrase")  # WHY: OpenAPI requires these.
    _PSK_OPTIONAL: ClassVar[tuple[str, ...]] = (  # WHY: API examples list these optional fields.
        "usage",
        "vlan_id",
        "mac",
        "max_usage",
        "role",
        "expire_time",
        "notify_expiry",
        "expiry_notification_time",
        "notify_on_create_or_edit",
        "email",
    )
    _USER_MAC_OPTIONAL: ClassVar[tuple[str, ...]] = ("labels", "vlan", "notes", "name", "radius_group")
    _ASSET_REQUIRED: ClassVar[tuple[str, ...]] = ("name", "mac")  # WHY: API examples require these columns.
    DEFINITIONS: ClassVar[tuple[CsvImportDefinition, ...]] = (  # WHY: one ordered source feeds prompts and tests.
        CsvImportDefinition(
            "org_psks",
            "Organization PSKs",
            "import_org_psks.csv",
            "org",
            "importOrgPsks",
            _PSK_REQUIRED,
            _PSK_OPTIONAL,
            ("passphrase", "old_passphrase"),
        ),
        CsvImportDefinition(
            "org_user_macs",
            "Organization user MACs",
            "import_org_user_macs.csv",
            "org",
            "importOrgUserMacs",
            ("mac",),
            _USER_MAC_OPTIONAL,
        ),
        CsvImportDefinition(
            "org_assets", "Organization assets", "import_org_assets.csv", "org", "importOrgAssets", _ASSET_REQUIRED, ()
        ),
        CsvImportDefinition(
            "site_psks",
            "Site PSKs",
            "import_site_psks.csv",
            "site",
            "importSitePsks",
            _PSK_REQUIRED,
            _PSK_OPTIONAL,
            ("passphrase", "old_passphrase"),
        ),
        CsvImportDefinition(
            "site_assets", "Site assets", "import_site_assets.csv", "site", "importSiteAssets", _ASSET_REQUIRED, ()
        ),
    )

    @classmethod
    def by_key(cls, key: str) -> CsvImportDefinition:
        """Return the definition for an import key."""
        logger.info("Resolving CSV import definition key=%s", key)  # WHY: record the operator selection lookup.
        definitions = {definition.key: definition for definition in cls.DEFINITIONS}  # WHY: keep lookup exact.
        definition = definitions[key]  # WHY: invalid keys are programmer errors and should fail in tests.
        logger.debug("Resolved CSV import definition operation=%s", definition.operation_id)  # WHY: log result.
        return definition  # WHY: callers need the endpoint metadata.


class CsvImportReader:
    """Read CSV files into immutable import batches."""

    @staticmethod
    def read(definition: CsvImportDefinition, file_path: Path) -> CsvImportBatch:
        """Read one CSV file for one import definition."""
        logger.info("Reading CSV import file type=%s", definition.key)  # WHY: do not log row values.
        with file_path.open(newline="", encoding="utf-8-sig") as csv_file:  # WHY: support Excel UTF-8 BOM files.
            reader = csv.DictReader(csv_file)  # WHY: column names decide schema validation.
            fieldnames = tuple(reader.fieldnames or ())  # WHY: normalize missing header to an empty tuple.
            rows = tuple(dict(row) for row in reader)  # WHY: materialize rows for preview and exact count.
        logger.debug("Read CSV import rows=%d columns=%d", len(rows), len(fieldnames))  # WHY: safe summary.
        return CsvImportBatch(definition, file_path, fieldnames, rows)  # WHY: return all parsed data together.


class CsvImportValidator:
    """Validate parsed import batches before any request runs."""

    @staticmethod
    def missing_columns(batch: CsvImportBatch) -> tuple[str, ...]:
        """Return required columns absent from the batch."""
        logger.info("Validating CSV import columns type=%s", batch.definition.key)  # WHY: action log before check.
        present = {column.strip() for column in batch.fieldnames}  # WHY: ignore accidental header whitespace.
        missing = tuple(
            column for column in batch.definition.required_columns if column not in present
        )  # WHY: exact list.
        logger.debug("CSV import validation missing_columns=%d", len(missing))  # WHY: safe validation summary.
        return missing  # WHY: the operation prints column names and stops on any value.


class CsvImportSanitizer:
    """Mask secret columns before rows reach output or logs."""

    @staticmethod
    def sanitize_row(definition: CsvImportDefinition, row: dict[str, str]) -> dict[str, str]:
        """Return one row with secret values masked."""
        secrets = set(definition.secret_columns)  # WHY: membership checks should be explicit and local.
        return {key: (MASK if key in secrets and value else value) for key, value in row.items()}  # WHY: mask secrets.

    @classmethod
    def preview_rows(cls, batch: CsvImportBatch) -> tuple[dict[str, str], ...]:
        """Return the first rows that are safe to print."""
        logger.info("Building CSV import preview type=%s", batch.definition.key)  # WHY: action log before preview.
        preview = tuple(cls.sanitize_row(batch.definition, row) for row in batch.rows[:PREVIEW_LIMIT])  # WHY: cap rows.
        logger.debug("Built CSV import preview rows=%d", len(preview))  # WHY: safe result summary.
        return preview  # WHY: callers print sanitized rows only.


class CsvImportConfirmation:
    """Parse destructive confirmation text."""

    @staticmethod
    def is_confirmed(answer: str, row_count: int) -> bool:
        """Return True only for `IMPORT <row_count>`."""
        logger.info("Validating CSV import confirmation for rows=%d", row_count)  # WHY: log the gate check.
        expected = f"{CONFIRM_VERB} {row_count}"  # WHY: row count binds the prompt to the reviewed preview.
        confirmed = answer.strip() == expected  # WHY: exact match prevents accidental destructive imports.
        logger.debug("CSV import confirmation accepted=%s", confirmed)  # WHY: safe boolean result.
        return confirmed  # WHY: caller decides whether to send the request.
