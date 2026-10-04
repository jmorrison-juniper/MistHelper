"""Menu operation 292 for destructive CSV imports into Mist."""

from __future__ import annotations  # WHY: keep annotation evaluation lazy during CLI startup.

import csv  # WHY: append the sanitized audit row with stable columns.
import logging  # WHY: record each operator action and result.
import sys  # WHY: detect the shared --dry-run flag until menu wiring passes options.
from collections.abc import Callable  # WHY: type dependency seams for tests.
from dataclasses import dataclass  # WHY: group dependencies and options under two parameters.
from pathlib import Path  # WHY: handle data directory paths portably.
from typing import Any  # WHY: the Mist SDK session and response are dynamic.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,
)  # WHY: read shared CLI services.
from src.mist.resources.inventory.csv_imports.client import (
    CsvImportClient,
    CsvImportResponseSummary,
)  # WHY: send and summarize.
from src.mist.resources.inventory.csv_imports.model import (  # WHY: keep validation and masking pure and tested.
    CsvImportBatch,
    CsvImportCatalog,
    CsvImportConfirmation,
    CsvImportDefinition,
    CsvImportReader,
    CsvImportResult,
    CsvImportSanitizer,
    CsvImportValidator,
)

logger = logging.getLogger(__name__)  # WHY: module logger helps passphrase leak tests.
LOG_FILE_NAME = "CsvImportLog.csv"  # WHY: the assignment requires this exact data/ output file.


@dataclass(slots=True)
class CsvImportOptions:
    """Hold optional non-interactive settings for tests and future CLI wiring."""

    import_key: str | None = None  # WHY: tests can select a type without prompt text parsing.
    dry_run: bool | None = None  # WHY: None lets the operation read --dry-run from argv.
    scope_id: str | None = None  # WHY: tests can avoid org or site prompts.
    confirmation: str | None = None  # WHY: tests can prove the destructive gate.


@dataclass(slots=True)
class CsvImportDependencies:
    """Hold runtime seams used by the menu operation."""

    session: Any  # WHY: the active Mist session carries auth and regional host state.
    get_csv_path: Callable[[str], str]  # WHY: anchor input and output files under data/.
    safe_input: Callable[[str, str], str]  # WHY: prompts must be EOF-safe in SSH and containers.
    get_org_id: Callable[[], str]  # WHY: organization imports need the selected org id.
    client_factory: Callable[[Any], CsvImportClient]  # WHY: tests inject a no-network client.


class CsvImportOperation:
    """Import PSKs, user MACs, or assets from CSV after typed confirmation."""

    @staticmethod
    def _default_dependencies() -> CsvImportDependencies:
        """Return dependencies from the shared MistHelper context."""
        return CsvImportDependencies(  # WHY: gather shared services once at operation startup.
            session=SourceDependencyResolver.apisession,
            get_csv_path=SourceDependencyResolver.FilePathUtils.get_csv_path,
            safe_input=SourceDependencyResolver.InputUtils.safe_input,
            get_org_id=lambda: str(SourceDependencyResolver.ConfigUtils.get_cached_or_prompted_org_id()),
            client_factory=CsvImportClient,
        )

    @staticmethod
    def _is_dry_run(options: CsvImportOptions) -> bool:
        """Return whether this run must avoid the Mist request."""
        if options.dry_run is not None:  # WHY: tests and future CLI wiring can set the value directly.
            return options.dry_run  # WHY: explicit input outranks process arguments.
        return "--dry-run" in sys.argv  # WHY: support the assignment flag before menu wiring exists.

    @staticmethod
    def _select_definition(options: CsvImportOptions, deps: CsvImportDependencies) -> CsvImportDefinition:
        """Return the selected import definition."""
        if options.import_key:  # WHY: tests and automation can select without an interactive prompt.
            return CsvImportCatalog.by_key(options.import_key)  # WHY: central metadata validates the key.
        logger.info("Prompting for CSV import type")  # WHY: action log before operator input.
        for index, definition in enumerate(CsvImportCatalog.DEFINITIONS, start=1):  # WHY: present stable choices.
            print(f"{index}. {definition.label} ({definition.file_name})")  # WHY: operator sees type and file name.
        answer = deps.safe_input("Select import type number: ", "csv import type")  # WHY: EOF-safe selection.
        index = int(answer.strip()) - 1  # WHY: convert the menu number to a zero-based tuple index.
        definition = CsvImportCatalog.DEFINITIONS[index]  # WHY: invalid indexes should fail loudly in tests.
        logger.debug("Selected CSV import type=%s", definition.key)  # WHY: log the selection without row data.
        return definition  # WHY: caller needs the endpoint metadata.

    @staticmethod
    def _resolve_scope_id(
        definition: CsvImportDefinition, options: CsvImportOptions, deps: CsvImportDependencies
    ) -> str:
        """Return the organization or site identifier for the selected import."""
        if options.scope_id:  # WHY: tests and future automation can provide the identifier directly.
            return options.scope_id  # WHY: avoid prompts when the value is already known.
        if definition.scope == "org":  # WHY: organization imports use the cached org selection.
            return deps.get_org_id()  # WHY: shared helper follows existing MistHelper org selection behavior.
        return deps.safe_input("Enter the target site_id: ", "csv import site id").strip()  # WHY: site scope needs id.

    @staticmethod
    def _print_preview(batch: CsvImportBatch) -> None:
        """Print a sanitized preview for the operator."""
        logger.info("Printing CSV import preview rows=%d", batch.row_count)  # WHY: log only safe counts.
        print(f"Import type: {batch.definition.label}")  # WHY: remind the operator which endpoint is selected.
        print(f"Rows found: {batch.row_count}")  # WHY: row count must match the confirmation phrase.
        for row in CsvImportSanitizer.preview_rows(batch):  # WHY: print only masked rows.
            print(row)  # WHY: sanitized dictionaries keep the preview compact and readable.
        logger.debug("CSV import preview printed rows=%d", min(batch.row_count, 10))  # WHY: safe result summary.

    @staticmethod
    def _get_confirmation(batch: CsvImportBatch, options: CsvImportOptions, deps: CsvImportDependencies) -> str:
        """Return the destructive confirmation answer."""
        if options.confirmation is not None:  # WHY: tests can supply the exact operator answer.
            return options.confirmation  # WHY: avoid an input prompt during tests.
        prompt = f"Type 'IMPORT {batch.row_count}' to proceed: "  # WHY: row count proves preview review.
        return deps.safe_input(prompt, "csv import confirmation")  # WHY: EOF-safe destructive prompt.

    @staticmethod
    def _write_log(deps: CsvImportDependencies, result: CsvImportResult) -> None:
        """Append one sanitized audit row under data/."""
        log_path = Path(deps.get_csv_path(LOG_FILE_NAME))  # WHY: output stays anchored under data/.
        write_header = not log_path.exists()  # WHY: first append creates the header row.
        logger.info("Writing CSV import audit result rows=%d", result.row_count)  # WHY: action log with safe count.
        with log_path.open("a", newline="", encoding="utf-8") as log_file:  # WHY: append preserves prior runs.
            writer = csv.DictWriter(log_file, fieldnames=CsvImportResult.column_names())  # WHY: stable columns.
            if write_header:  # WHY: a new log file needs column names.
                writer.writeheader()  # WHY: operators can read the CSV without external schema.
            writer.writerow(result.as_row())  # WHY: write the sanitized summary row.
        logger.debug("CSV import audit result written path=%s", log_path)  # WHY: log the destination only.

    @classmethod
    def _handle_invalid_batch(cls, deps: CsvImportDependencies, batch: CsvImportBatch) -> bool:
        """Return True when validation found a blocking error."""
        missing = CsvImportValidator.missing_columns(batch)  # WHY: required columns protect the Mist endpoint.
        if not missing:  # WHY: no missing column means the batch can continue.
            return False  # WHY: caller should proceed with preview and confirmation.
        message = f"Missing required column: {', '.join(missing)}"  # WHY: name every absent column for repair.
        logger.error("CSV import stopped: %s", message)  # WHY: audit the schema stop without row data.
        print(message)  # WHY: operator needs the exact header to add.
        cls._write_log(deps, CsvImportResult(batch.definition.key, batch.row_count, False, "cancelled", message))
        return True  # WHY: caller should stop before any request.

    @classmethod
    def _execute_import(
        cls,
        deps: CsvImportDependencies,
        batch: CsvImportBatch,
        scope_id: str,
        dry_run: bool,
    ) -> CsvImportResult:
        """Return the dry run or live import result."""
        if dry_run:  # WHY: dry run must never create or update Mist records.
            return CsvImportResult(batch.definition.key, batch.row_count, True, "dry_run", "request_not_sent")
        logger.info("Creating CSV import client for type=%s", batch.definition.key)  # WHY: action log before request.
        client = deps.client_factory(deps.session)  # WHY: build the client after confirmation only.
        response = client.send(batch.definition, scope_id, batch.file_path)  # WHY: one destructive request per run.
        message = CsvImportResponseSummary.summarize(response)  # WHY: keep result free of row values and secrets.
        return CsvImportResult(batch.definition.key, batch.row_count, False, "sent", message)  # WHY: audit result.

    @classmethod
    def run(
        cls,
        options: CsvImportOptions | None = None,
        deps: CsvImportDependencies | None = None,
        dry_run: bool | None = None,
    ) -> None:
        """Run menu 292 without positional arguments."""
        logger.warning("Menu #292 destructive CSV import started")  # WHY: destructive audit start.
        run_options = options or CsvImportOptions(dry_run=dry_run)  # WHY: default accepts the shared dry-run flag.
        run_deps = deps or cls._default_dependencies()  # WHY: use shared runtime unless tests inject seams.
        dry_run = cls._is_dry_run(run_options)  # WHY: determine whether a request can be sent.
        definition = cls._select_definition(run_options, run_deps)  # WHY: choose the exact import endpoint.
        file_path = Path(run_deps.get_csv_path(definition.file_name))  # WHY: follow existing data/ CSV rule.
        if not file_path.exists():  # WHY: fail before opening a missing operator file.
            logger.error("CSV import file not found path=%s", file_path)  # WHY: audit missing input path.
            print(f"CSV import file not found: {file_path}")  # WHY: operator sees where to place the CSV.
            return  # WHY: no file means no batch and no request.
        batch = CsvImportReader.read(definition, file_path)  # WHY: parse once for validation, preview, and count.
        if cls._handle_invalid_batch(run_deps, batch):  # WHY: validation failures must stop before confirmation.
            return  # WHY: never send a request after a schema failure.
        cls._print_preview(batch)  # WHY: operator reviews scope before the destructive phrase.
        answer = cls._get_confirmation(batch, run_options, run_deps)  # WHY: require typed row count confirmation.
        if not CsvImportConfirmation.is_confirmed(answer, batch.row_count):  # WHY: exact phrase gates the request.
            logger.info("CSV import cancelled by confirmation mismatch rows=%d", batch.row_count)  # WHY: audit stop.
            cls._write_log(
                run_deps,
                CsvImportResult(definition.key, batch.row_count, dry_run, "cancelled", "confirmation_mismatch"),
            )
            return  # WHY: no confirmed phrase means no Mist request.
        scope_id = cls._resolve_scope_id(definition, run_options, run_deps)  # WHY: resolve scope after confirmation.
        result = cls._execute_import(run_deps, batch, scope_id, dry_run)  # WHY: run dry or live path.
        cls._write_log(run_deps, result)  # WHY: every completed import writes a sanitized audit row.
        logger.warning("Menu #292 destructive CSV import finished status=%s rows=%d", result.status, result.row_count)
