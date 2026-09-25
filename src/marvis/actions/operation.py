"""Menu operation 270 -- export the Marvis Actions of one organization, or resolve them in bulk.

Why:
    Marvis Actions stay open in the Mist portal until someone closes them. A
    NOC engineer who fixed a problem by hand, or who knows that an action is
    false, must close each action with a resolution code. This module lets the
    engineer export the actions as a report, and close the open actions of the
    chosen topics in one run.

Output:
    Modes 1, 2, and 4 write ``OrgMarvisActions.csv`` under the data directory
    and write the same rows to the configured database backend. Mode 1 writes
    every action, mode 2 writes the open actions, and mode 4 writes the closed
    actions. Before the write, these modes search the Marvis alarms one time
    and add the alarm of each action to its row (issue #3339). Mode 3 writes
    ``OrgMarvisActionsResolveResults.csv``, with one row for each request, and
    it searches no alarm. With ``--output-format sqlite``, each write goes to a
    SQLite table that has the file name without ``.csv``, and the run writes no
    CSV file.

Safety:
    Mode 3 changes Mist records. It sends nothing until the operator types
    ``RESOLVE <count>``. It changes open actions only, one request at a time,
    and it reads the list again to verify each change.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions in the annotations of this module.

import logging  # WHY: log an action before each step and a summary after it.
import os  # WHY: read the optional cap on the number of actions that one run changes.
import time  # WHY: stamp the resolve time and wait before the verify read.
from collections import Counter  # WHY: count the outcomes and the statuses for the summary lines.
from collections.abc import Sequence  # WHY: type the record lists without a concrete class.
from dataclasses import dataclass, fields  # WHY: the results row declares its column order one time.
from datetime import UTC, datetime  # WHY: stamp the export time as readable UTC text.
from typing import Any  # WHY: the database documents hold values of any JSON type.

from src.config import runtime_settings  # WHY: the shared page size that every list reader uses.
from src.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: reach the shared session, config helper, and exporter without the root module.
)
from src.dataclasses.export_backend_options import ExportBackendOptions  # WHY: send the raw documents to the DB.
from src.marvis.actions.alarms import MarvisAlarmJoin  # WHY: add the Marvis alarm of each action to its row.
from src.marvis.actions.client import MarvisActionsClient, MarvisListResult  # WHY: every API call of the feature.
from src.marvis.actions.model import (  # WHY: the status catalog, the records, and the field reader.
    OPEN_STATUSES,
    STATUS_NAMES,
    MarvisActionRecord,
    MarvisActionRecordBuilder,
    MarvisCatalog,
    MarvisFieldReader,
)
from src.marvis.actions.selection import (  # WHY: the modes, the filter prompts, and the resolve prompts.
    ANSWER_ECHO_LIMIT,
    DISPLAY_LEVEL,
    MODE_ACTION_NOUNS,
    MODE_IS_OPEN_VALUES,
    MODE_RESOLVE,
    MODES,
    MarvisFilterPrompts,
    MarvisResolvePrompts,
    MarvisResolveRequest,
    MarvisTopicSelector,
)
from src.utils.rate_limiting import AdaptivePacer  # WHY: the quota-aware wait between two resolve requests.

logger = logging.getLogger(__name__)  # WHY: name the logger for this module so a reader filters by source.

EXPORT_FILENAME = "OrgMarvisActions.csv"  # WHY: the data directory holds one export file for this operation.
EXPORT_ENDPOINT_NAME = "listOrgMarvisActions"  # WHY: the primary key strategy registers under this name.
RESULTS_FILENAME = "OrgMarvisActionsResolveResults.csv"  # WHY: one results file for each resolve run.
RESULTS_ENDPOINT_NAME = "resolveOrgMarvisActions"  # WHY: the primary key strategy registers under this name.
MAX_ACTIONS_ENV = "MARVIS_RESOLVE_MAX_ACTIONS"  # WHY: the operator can lower or raise the cap in .env.
DEFAULT_MAX_ACTIONS = 500  # WHY: a guard against a filter that is wider than the operator intended.
VERIFY_DELAY_SECONDS = 2.0  # WHY: give Mist time to store the change before the verify read.
PROGRESS_EVERY = 25  # WHY: a long resolve run shows one progress line for each group of 25 requests.

OUTCOME_SENT = "sent"  # WHY: an interim outcome. The verify step replaces it.
OUTCOME_RESOLVED = "resolved"  # WHY: Mist accepted the request, and the verify read shows a closed status.
OUTCOME_UNVERIFIED = "sent_unverified"  # WHY: Mist accepted the request, but the verify read did not confirm it.
OUTCOME_ERROR = "error"  # WHY: Mist refused the request, or no HTTP answer arrived.
OUTCOME_NOT_SENT = "not_sent"  # WHY: the stop signal arrived before this request.
OUTCOME_SKIPPED = "skipped"  # WHY: the action holds no row_key, so no request can address it.
OUTCOMES = (OUTCOME_RESOLVED, OUTCOME_UNVERIFIED, OUTCOME_ERROR, OUTCOME_NOT_SENT, OUTCOME_SKIPPED)  # WHY: summary.
STOP_SIGNAL_MESSAGE = "The stop signal arrived before this request."  # WHY: the reason of a not_sent row.
NO_ROW_KEY_MESSAGE = "The action holds no row_key, so no request can address it."  # WHY: the reason of a skip.


@dataclass(slots=True)
class MarvisResolveResult:
    """One row of the resolve results file.

    Why:
        The operator needs one row for each action that the run touched, with
        the HTTP status and the verified status, so a partial failure is easy
        to find and to repeat.
    """

    result_id: str  # WHY: the row key, made of the action uuid and the run time.
    uuid: str  # WHY: the stable key of the action.
    row_key: str  # WHY: the key that the request named.
    org_id: str  # WHY: the organization of the action.
    site_id: str  # WHY: the site of the action.
    site_name: str  # WHY: the site name, for a human reader.
    category: str  # WHY: the super category key.
    category_name: str  # WHY: the super category name.
    symptom: str  # WHY: the subcategory key.
    symptom_name: str  # WHY: the subcategory name.
    topic: str  # WHY: the pair key, such as switch/sw_offline.
    entity_names: str  # WHY: the names of the impacted devices.
    previous_status: str  # WHY: the status before the run.
    resolution_code: str  # WHY: the code that the run sent.
    resolution_name: str  # WHY: the text of the code.
    comment: str  # WHY: the comment that the run sent.
    outcome: str  # WHY: resolved, sent_unverified, error, not_sent, or skipped.
    http_status: int | None  # WHY: the HTTP status, or no value when no request went out.
    message: str  # WHY: the reason of the outcome.
    verified_status: str  # WHY: the status that the verify read shows.
    resolve_time: int  # WHY: the epoch millisecond time of the run.
    resolve_time_iso: str  # WHY: the readable time of the run.

    @classmethod
    def column_names(cls) -> list[str]:
        """Return the CSV column names in field order.

        Returns:
            The column names.
        """
        return [field.name for field in fields(cls)]  # WHY: the dataclass is the one source of the column order.

    def as_row(self) -> dict[str, Any]:
        """Return the result as one CSV row.

        Returns:
            The column name and value pairs, in field order.
        """
        return {field.name: getattr(self, field.name) for field in fields(self)}  # WHY: keep the column order.

    @classmethod
    def start(cls, record: MarvisActionRecord, request: MarvisResolveRequest) -> MarvisResolveResult:
        """Return the first form of the result row for one action.

        Args:
            record: The action that the run changes.
            request: The resolution code, the comment, and the time of the run.

        Returns:
            The result row without an outcome.
        """
        return cls(
            result_id=f"{record.uuid}_{request.resolve_time}",  # WHY: one row for each action and each run.
            **{name: getattr(record, name) for name in _RECORD_COPY_FIELDS},  # WHY: copy the action columns.
            previous_status=record.status,  # WHY: the status before this run.
            resolution_code=request.code.key,  # WHY: the code that the run sent.
            resolution_name=request.code.name,  # WHY: the text of the code.
            comment=request.comment,  # WHY: the comment that the run sent.
            outcome="",  # WHY: the send step sets the outcome.
            http_status=None,  # WHY: the send step sets the status.
            message="",  # WHY: the send step and the verify step set the message.
            verified_status="",  # WHY: the verify step sets the status that Mist reports.
            resolve_time=request.resolve_time,  # WHY: the epoch time of the run.
            resolve_time_iso=MarvisFieldReader.iso(request.resolve_time),  # WHY: the readable time of the run.
        )


_RECORD_COPY_FIELDS = (  # WHY: the result columns that copy the action columns without a change.
    "uuid",
    "row_key",
    "org_id",
    "site_id",
    "site_name",
    "category",
    "category_name",
    "symptom",
    "symptom_name",
    "topic",
    "entity_names",
)


class MarvisBulkResolver:
    """Send the resolve requests one at a time, then verify them.

    Why:
        The API changes one action for each request. One request at a time
        keeps the load low, lets the stop signal end the run between two
        requests, and gives one clear result row for each action.
    """

    def __init__(self, client: MarvisActionsClient, request: MarvisResolveRequest, pacer: AdaptivePacer) -> None:
        """Keep the client, the request values, and the pacer.

        Args:
            client: The API client of the organization.
            request: The resolution code, the comment, and the time of the run.
            pacer: The quota-aware wait between two requests.
        """
        self._client = client  # WHY: the client sends every request.
        self._request = request  # WHY: every request carries the same code, comment, and time.
        self._pacer = pacer  # WHY: protect the shared API quota of every MistHelper user.

    def resolve(self, targets: Sequence[MarvisActionRecord]) -> list[MarvisResolveResult]:
        """Send one resolve request for each target.

        Args:
            targets: The open actions to resolve, in the order of the preview.

        Returns:
            One result row for each target.
        """
        logger.log(  # WHY: the operator sees the start of the loop on the SSH menu console.
            DISPLAY_LEVEL, "Sending %d resolve requests, one at a time", len(targets)
        )
        results: list[MarvisResolveResult] = []  # WHY: one row for each target.
        stopped = False  # WHY: after the stop signal, no later request goes out.
        for number, record in enumerate(targets, start=1):  # WHY: the number matches the preview line.
            result = MarvisResolveResult.start(record, self._request)  # WHY: the row before the send.
            stopped = stopped or SourceDependencyResolver.ConfigUtils.check_stop_signal()  # WHY: honor a stop.
            if stopped:  # WHY: the operator asked the run to end.
                self._mark(result, OUTCOME_NOT_SENT, STOP_SIGNAL_MESSAGE)  # WHY: no later request goes out.
            else:  # WHY: no stop signal, so send the request.
                self._send(result, number, len(targets))  # WHY: one PUT for this action.
            results.append(result)  # WHY: every target gets a row, also a target that was not sent.
            self._log_progress(number, len(targets))  # WHY: a long run must not look stopped.
        logger.debug("Finished %d resolve requests", len(results))  # WHY: result summary.
        return results  # WHY: the caller verifies and writes the rows.

    @staticmethod
    def _log_progress(number: int, total: int) -> None:
        """Log one progress line after each group of requests, and after the last request."""
        if number % PROGRESS_EVERY and number != total:  # WHY: one line for each group keeps the console short.
            return  # WHY: no progress line for this request.
        logger.log(DISPLAY_LEVEL, "Resolve progress: %d of %d actions", number, total)  # WHY: the progress line.

    def verify(self, results: Sequence[MarvisResolveResult], listing: MarvisListResult) -> None:
        """Compare each accepted request with the status of a new list read.

        Args:
            results: The result rows of the run.
            listing: The list read after the requests.
        """
        logger.info("Verifying the accepted requests against a new list read")  # WHY: action log before the step.
        statuses = {  # WHY: the current status of each action, keyed like the result rows.
            MarvisActionRecordBuilder.action_key(row): MarvisFieldReader.text(row.get("status")) for row in listing.rows
        }
        for result in results:  # WHY: check each row that Mist accepted.
            if result.outcome == OUTCOME_SENT:  # WHY: a refused or skipped row has nothing to verify.
                self._verify_one(result, statuses, listing.problem)  # WHY: set the final outcome.
        logger.debug("Verified %d rows", len(results))  # WHY: result summary.

    def _send(self, result: MarvisResolveResult, number: int, total: int) -> None:
        """Send the request for one row and record the answer."""
        if not result.row_key:  # WHY: the API finds an action by its row_key only.
            self._mark(result, OUTCOME_SKIPPED, NO_ROW_KEY_MESSAGE)  # WHY: no request can address the action.
            return  # WHY: nothing to send.
        logger.info(  # WHY: action log before each request.
            "Sending the resolve request %d of %d for Marvis Action %s (%s)", number, total, result.uuid, result.topic
        )
        status, error = self._client.resolve_action(self._request.body(result.row_key))  # WHY: one PUT.
        result.http_status = status  # WHY: the results file shows the HTTP status of every request.
        if error:  # WHY: Mist refused the request, or no HTTP answer arrived.
            self._mark(result, OUTCOME_ERROR, error)  # WHY: keep the reason for the operator.
            logger.warning("The resolve request %d of %d returned: %s", number, total, error)  # WHY: show it now.
        else:  # WHY: Mist accepted the request.
            self._mark(result, OUTCOME_SENT, "Mist accepted the request.")  # WHY: the verify step decides.
        self._pacer.pace()  # WHY: quota-aware wait between two requests.

    @staticmethod
    def _verify_one(result: MarvisResolveResult, statuses: dict[str, str], problem: str) -> None:
        """Set the final outcome of one accepted row."""
        status = "" if problem else statuses.get(result.uuid, "")  # WHY: a failed read shows no status.
        result.verified_status = status  # WHY: the results file shows the status that Mist reports.
        outcome, message = MarvisBulkResolver._verdict(status, problem)  # WHY: one rule table for the outcome.
        MarvisBulkResolver._mark(result, outcome, message)  # WHY: record the final outcome.

    @staticmethod
    def _verdict(status: str, problem: str) -> tuple[str, str]:
        """Return the final outcome and its reason for the status that the verify read shows."""
        if problem:  # WHY: without a good list read, no row can be verified.
            return OUTCOME_UNVERIFIED, f"Mist accepted the request. {problem}"  # WHY: the status is unknown.
        if not status:  # WHY: the action left the list, or its row holds no status.
            return OUTCOME_UNVERIFIED, "The new list read shows no status for the action."  # WHY: unknown.
        if status in OPEN_STATUSES:  # WHY: Mist accepted the request, but the action is still open.
            return OUTCOME_UNVERIFIED, "Mist still reports an open status."  # WHY: the operator must check.
        return OUTCOME_RESOLVED, "Mist reports a closed status."  # WHY: a closed status confirms the change.

    @staticmethod
    def _mark(result: MarvisResolveResult, outcome: str, message: str) -> None:
        """Set the outcome and the message of one row."""
        result.outcome = outcome  # WHY: the summary counts this value.
        result.message = message  # WHY: the operator reads the reason in the results file.


@dataclass(slots=True)
class MarvisLoadedActions:
    """The actions of one organization, ready for the filter step.

    Attributes:
        org_id: The organization of the run.
        client: The API client of the organization.
        catalog: The names of the topics and their recommended actions.
        records: One flat record for each action, without duplicates.
        documents: The database document of each action, keyed by the action uuid.
    """

    org_id: str  # WHY: the organization of the run.
    client: MarvisActionsClient  # WHY: the client for the resolve and the verify read.
    catalog: MarvisCatalog  # WHY: the topic names for the filter tables.
    records: list[MarvisActionRecord]  # WHY: one flat record for each action.
    documents: dict[str, dict[str, Any]]  # WHY: the database document of each action.


class MarvisOutputTarget:
    """Name the place that receives the rows, for the active output format.

    Why:
        The CSV format writes a file under the data directory. The SQLite
        format writes a table in the SQLite database and writes no CSV file.
        A line that names the CSV file after a SQLite write sends the operator
        to a file that the run did not write.
    """

    @staticmethod
    def describe(filename: str) -> str:
        """Return the text that names the output of one write.

        Args:
            filename: The CSV file name of the write, such as ``OrgMarvisActions.csv``.

        Returns:
            The file name for the CSV format. For the SQLite format, the table name and the database path.
        """
        output_format = SourceDependencyResolver.OUTPUT_FORMAT  # WHY: the format that the exporter selects.
        if output_format != "sqlite":  # WHY: the CSV format keeps the file name that the web dashboard reads.
            return filename  # WHY: the web dashboard finds the file through this exact name.
        table = filename.removesuffix(".csv")  # WHY: the exporter names the table after the file, without .csv.
        database_path = SourceDependencyResolver.DATABASE_PATH  # WHY: the SQLite file that holds the table.
        target = f"the SQLite table {table} in {database_path}"  # WHY: the table and the file, in one phrase.
        logger.debug("The output target of %s is %s", filename, target)  # WHY: result summary.
        return target  # WHY: every export line and completion line uses this text.


class MarvisResolveWorkflow:
    """Run mode 3: preview, confirm, resolve, verify, and write the results.

    Why:
        The resolve steps must run in a fixed order, and each refusal must stop
        the run before the first request. One class holds that order.
    """

    def __init__(self, loaded: MarvisLoadedActions) -> None:
        """Keep the loaded actions of the run.

        Args:
            loaded: The actions of the organization and the API client.
        """
        self._loaded = loaded  # WHY: the client and the records serve every step.

    def resolve_open_actions(self, selected: Sequence[MarvisActionRecord]) -> None:
        """Resolve the selected open actions.

        The method name is unique in ``src``, so ``tools/prompt_audit.py`` can
        follow the call and count the three resolve prompts.

        Args:
            selected: The open actions that the filter kept.
        """
        targets = self._capped_targets(selected)  # WHY: the oldest actions first, up to the cap.
        self._log_preview(targets)  # WHY: the operator must see each action before the confirmation.
        request = self._ask_request(len(targets))  # WHY: the code, the comment, and the typed confirmation.
        if request is None:  # WHY: a refusal ends the run before any request.
            return  # WHY: the refusal is already in the log.
        resolver = MarvisBulkResolver(self._loaded.client, request, self._pacer())  # WHY: one resolver per run.
        results = resolver.resolve(targets)  # WHY: send the requests.
        self._verify(resolver, results)  # WHY: confirm each accepted request.
        self._write_results(results)  # WHY: one row for each target, then the summary.

    @staticmethod
    def max_actions() -> int:
        """Return the cap on the number of actions that one run changes.

        Returns:
            The value of ``MARVIS_RESOLVE_MAX_ACTIONS``, or 500 when the value is missing or not valid.
        """
        raw = os.environ.get(MAX_ACTIONS_ENV, "").strip()  # WHY: the operator can set the cap in .env.
        if not raw:  # WHY: no value means the default cap.
            return DEFAULT_MAX_ACTIONS  # WHY: the documented default.
        value = MarvisFieldReader.integer(raw)  # WHY: accept a whole number only.
        if value is None or value < 1:  # WHY: a cap below 1 would block every run.
            logger.warning(  # WHY: tell the operator that the value has no effect.
                "Ignoring %s: the value %r is not a positive whole number. The cap stays %d.",
                MAX_ACTIONS_ENV,
                raw,
                DEFAULT_MAX_ACTIONS,
            )
            return DEFAULT_MAX_ACTIONS  # WHY: fall back to the documented default.
        return value  # WHY: the operator value.

    def _capped_targets(self, selected: Sequence[MarvisActionRecord]) -> list[MarvisActionRecord]:
        """Return the oldest selected actions, up to the cap."""
        ordered = sorted(selected, key=lambda record: (record.start_time_iso, record.uuid))  # WHY: oldest first.
        cap = self.max_actions()  # WHY: the limit for this run.
        if len(ordered) > cap:  # WHY: the filter matched more actions than one run may change.
            logger.warning(  # WHY: the operator must know that some actions stay open.
                "The filter matches %d open actions. This run resolves the oldest %d, because %s is %d.",
                len(ordered),
                cap,
                MAX_ACTIONS_ENV,
                cap,
            )
        return ordered[:cap]  # WHY: the rest stay open for a later run.

    @staticmethod
    def _log_preview(targets: Sequence[MarvisActionRecord]) -> None:
        """Log one preview line for each action that the run changes."""
        logger.log(  # WHY: the heading of the preview.
            DISPLAY_LEVEL, "Preview of the %d open Marvis Actions that this run resolves:", len(targets)
        )
        for number, record in enumerate(targets, start=1):  # WHY: the numbers match the request log lines.
            logger.log(  # WHY: one line for each action.
                DISPLAY_LEVEL,
                "  %4d. %s | %s / %s | %s | %s | started %s",
                number,
                record.site_name or record.site_id,
                record.category_name,
                record.symptom_name,
                record.entity_names or record.entity_id,
                record.status_name,
                record.start_time_iso,
            )

    @staticmethod
    def _ask_request(count: int) -> MarvisResolveRequest | None:
        """Ask the code, the comment, and the confirmation, in that order."""
        code = MarvisResolvePrompts.ask_code()  # WHY: prompt 4 of the portal contract.
        if code is None:  # WHY: the refusal is already in the log.
            return None  # WHY: stop before the next prompt.
        comment = MarvisResolvePrompts.ask_comment(code)  # WHY: prompt 5 of the portal contract.
        if comment is None:  # WHY: the refusal is already in the log.
            return None  # WHY: stop before the confirmation.
        if not MarvisResolvePrompts.ask_confirmation(count):  # WHY: prompt 6 of the portal contract.
            return None  # WHY: never change Mist without the typed confirmation.
        return MarvisResolveRequest(code, comment, int(time.time() * 1000))  # WHY: one time for the whole run.

    @staticmethod
    def _pacer() -> AdaptivePacer:
        """Return the quota-aware pacer that the other bulk loops use."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        return AdaptivePacer(  # WHY: the same pacer as the other bulk PUT loops.
            getattr(mh, "apisession", None),  # WHY: the PID pipeline reads the quota through this session.
            getattr(mh, "_api_usage_cache", None),  # WHY: share one quota view with every other menu.
            True,  # WHY: every request of this loop is real, so the pacer must wait.
        )

    def _verify(self, resolver: MarvisBulkResolver, results: Sequence[MarvisResolveResult]) -> None:
        """Read the list again and verify the accepted requests."""
        if not any(result.outcome == OUTCOME_SENT for result in results):  # WHY: nothing to verify.
            return  # WHY: save one list read.
        logger.info("Waiting %.0f seconds before the verify read", VERIFY_DELAY_SECONDS)  # WHY: explain the wait.
        time.sleep(VERIFY_DELAY_SECONDS)  # WHY: give Mist time to store the changes.
        resolver.verify(results, self._loaded.client.list_actions())  # WHY: compare with the new statuses.

    @staticmethod
    def _write_results(results: Sequence[MarvisResolveResult]) -> None:
        """Write the results file, then log the summary and the completion line."""
        rows = [result.as_row() for result in results]  # WHY: one CSV row for each target.
        target = MarvisOutputTarget.describe(RESULTS_FILENAME)  # WHY: the file or the table of the active format.
        logger.info("Writing %d resolve result rows to %s", len(rows), target)  # WHY: action log.
        written = SourceDependencyResolver.DataExporter.write_with_format_selection(
            rows,
            RESULTS_FILENAME,
            api_function_name=RESULTS_ENDPOINT_NAME,  # WHY: the primary key strategy for the results table.
            fieldnames=MarvisResolveResult.column_names(),  # WHY: a fixed column order.
        )
        logger.debug("The results export returned written=%s", written)  # WHY: result summary.
        MarvisResolveWorkflow._log_summary(results, target)  # WHY: the counts come before the completion line.
        if not written:  # WHY: never report success after a failed write.
            logger.error(  # WHY: the handled failure that the web dashboard reports as failed.
                "MistHelper could not write %s. Read the export error above.", target
            )
            return  # WHY: the error is the last word of the run.
        logger.log(  # WHY: the completion line names the file that the web dashboard offers.
            DISPLAY_LEVEL, "Completed the Marvis Actions resolve and wrote results to %s", target
        )

    @staticmethod
    def _log_summary(results: Sequence[MarvisResolveResult], target: str) -> None:
        """Log the outcome counts, and one line for each kind of problem.

        Args:
            results: One result for each action that the run touched.
            target: The file or the SQLite table that holds the results.
        """
        counts = Counter(result.outcome for result in results)  # WHY: one count for each outcome.
        summary = " ".join(f"{outcome}={counts[outcome]}" for outcome in OUTCOMES)  # WHY: one fixed order.
        logger.log(DISPLAY_LEVEL, "Marvis Actions resolve summary: %s", summary)  # WHY: the operator reads it here.
        if counts[OUTCOME_ERROR]:  # WHY: a refused request is a failure of the run.
            logger.error(  # WHY: the handled failure that the web dashboard reports as failed.
                "MistHelper could not resolve %d of %d Marvis Actions. Read %s for the HTTP status of each one.",
                counts[OUTCOME_ERROR],
                len(results),
                target,  # WHY: the operator reads the HTTP status in this file or table.
            )
        if counts[OUTCOME_UNVERIFIED]:  # WHY: an accepted request without a closed status needs a check.
            logger.warning(  # WHY: the operator must check these actions in the Mist portal.
                "Mist accepted %d requests, but the verify read shows no closed status for them yet.",
                counts[OUTCOME_UNVERIFIED],
            )
        if counts[OUTCOME_NOT_SENT]:  # WHY: the stop signal ended the run early.
            logger.warning(  # WHY: the operator must run the menu again for the rest.
                "The stop signal ended the run. %d actions stay open.", counts[OUTCOME_NOT_SENT]
            )


class MarvisActionsOperation:
    """Run menu 270 for the SSH menu, the command line, and the web dashboard.

    Why:
        One class method is the single entry point of the feature. The menu
        row and the web dashboard call it with no arguments, and it asks every
        value through the shared EOF-safe prompt.
    """

    @classmethod
    def run(cls) -> None:
        """Ask the mode and the filters, then export or resolve the Marvis Actions."""
        logger.info("Menu #270: Starting the Marvis Actions export and bulk resolve")  # WHY: action log.
        mode = MarvisFilterPrompts.ask_mode()  # WHY: prompt 1 of the portal contract.
        if mode not in MODES:  # WHY: an unknown mode must not guess an action.
            logger.error(  # WHY: the handled refusal that the web dashboard reports as failed.
                "MistHelper could not match the mode answer '%s'. Enter 1, 2, 3, or 4. No file was written.",
                mode[:ANSWER_ECHO_LIMIT],  # WHY: repeat the start of a bad answer only.
            )
            return  # WHY: stop before any API call.
        loaded = cls._load(mode)  # WHY: read the list, the schema, and the site names.
        if loaded is None:  # WHY: the reason is already in the log.
            return  # WHY: nothing to filter.
        selected = cls._filter(loaded, mode)  # WHY: prompts 2 and 3 of the portal contract.
        if not selected:  # WHY: the reason is already in the log.
            return  # WHY: nothing to export or resolve.
        if mode == MODE_RESOLVE:  # WHY: mode 3 changes Mist records.
            MarvisResolveWorkflow(loaded).resolve_open_actions(selected)  # WHY: preview, confirm, resolve, and verify.
            return  # WHY: mode 3 writes the results file only.
        cls._export(loaded, selected)  # WHY: modes 1, 2, and 4 write the report.

    @classmethod
    def _load(cls, mode: str) -> MarvisLoadedActions | None:
        """Read the actions of the organization, or log why the run stops."""
        org_id = str(SourceDependencyResolver.ConfigUtils.get_cached_or_prompted_org_id())  # WHY: the shared helper.
        page_limit = int(runtime_settings.DEFAULT_API_PAGE_LIMIT)  # WHY: the shared page size.
        client = MarvisActionsClient(SourceDependencyResolver.apisession, org_id, page_limit)  # WHY: one client.
        listing = client.list_actions()  # WHY: read every page of the list.
        if listing.problem:  # WHY: a failed read must not produce a partial report or a partial resolve.
            logger.error(  # WHY: the handled failure that the web dashboard reports as failed.
                "MistHelper could not read the Marvis Actions list. %s %s", listing.problem, cls._tail(mode)
            )
            return None  # WHY: stop the run.
        if not listing.rows:  # WHY: an organization without actions has nothing to report.
            logger.log(  # WHY: a clear answer on every console.
                DISPLAY_LEVEL, "No Marvis Actions exist in this organization. %s", cls._tail(mode)
            )
            return None  # WHY: stop the run.
        loaded = cls._build(org_id, client, listing.rows)  # WHY: one flat record for each action.
        kept_values = MODE_IS_OPEN_VALUES[mode]  # WHY: the is_open values that the mode keeps.
        if not any(record.is_open in kept_values for record in loaded.records):  # WHY: the mode keeps no action.
            logger.log(  # WHY: a clear answer on every console. Mode 1 keeps every action, so it never stops here.
                DISPLAY_LEVEL, "No %s exist in this organization. %s", MODE_ACTION_NOUNS[mode], cls._tail(mode)
            )
            return None  # WHY: modes 2, 3, and 4 can have nothing to do.
        return loaded  # WHY: the filter step reads these records.

    @staticmethod
    def _build(org_id: str, client: MarvisActionsClient, rows: list[dict[str, Any]]) -> MarvisLoadedActions:
        """Return the flat records and the documents of the raw rows, without duplicates."""
        catalog = MarvisCatalog(client.read_schema())  # WHY: the names and the recommended actions.
        exported_at = datetime.now(UTC).isoformat(timespec="seconds")  # WHY: one time for every row of the run.
        builder = MarvisActionRecordBuilder(catalog, client.read_site_names(), exported_at)  # WHY: shared lookups.
        logger.info("Building the records of %d Marvis Action rows", len(rows))  # WHY: action log.
        records: list[MarvisActionRecord] = []  # WHY: one record for each unique action.
        documents: dict[str, dict[str, Any]] = {}  # WHY: one document for each unique action.
        for raw in rows:  # WHY: build each row.
            record = builder.build(raw)  # WHY: the flat CSV record.
            if record.uuid not in documents:  # WHY: a page overlap can repeat an action.
                records.append(record)  # WHY: keep the first copy.
                documents[record.uuid] = builder.document(raw, record)  # WHY: the database document.
        logger.debug("Built %d records from %d rows", len(records), len(rows))  # WHY: result summary.
        return MarvisLoadedActions(org_id, client, catalog, records, documents)  # WHY: the filter step input.

    @classmethod
    def _filter(cls, loaded: MarvisLoadedActions, mode: str) -> list[MarvisActionRecord]:
        """Ask the two filter prompts and return the matching records, or log why none remain."""
        selector = MarvisTopicSelector(loaded.records, loaded.catalog, mode)  # WHY: the mode sets the kept actions.
        answer = MarvisFilterPrompts.ask_categories(selector.category_counts())  # WHY: prompt 2.
        categories, bad_token = selector.match_categories(answer)  # WHY: read the category answer.
        if bad_token or not categories:  # WHY: a typo or an empty category stops the run.
            cls._refuse(mode, "category", bad_token)  # WHY: explain the stop.
            return []  # WHY: nothing to export or resolve.
        answer = MarvisFilterPrompts.ask_subcategories(selector.topic_counts(categories))  # WHY: prompt 3.
        topics, bad_token = selector.match_topics(answer, categories)  # WHY: read the subcategory answer.
        selected = selector.select(topics) if not bad_token else []  # WHY: a typo selects nothing.
        if not selected:  # WHY: a typo or an empty result stops the run.
            cls._refuse(mode, "subcategory", bad_token)  # WHY: explain the stop.
        return selected  # WHY: the export or the resolve reads these records.

    @classmethod
    def _refuse(cls, mode: str, prompt_name: str, bad_token: str) -> None:
        """Log why the filter step kept no action."""
        if bad_token:  # WHY: a token that names nothing known.
            logger.error(  # WHY: the handled refusal that the web dashboard reports as failed.
                "MistHelper could not match the %s answer '%s'. Enter all, a table number, a category key, "
                "a subcategory key, or a category/subcategory pair. %s",
                prompt_name,
                bad_token[:ANSWER_ECHO_LIMIT],  # WHY: repeat the start of a bad answer only.
                cls._tail(mode),
            )
            return  # WHY: one message for each stop.
        logger.log(  # WHY: a clear empty answer that names the actions of the mode.
            DISPLAY_LEVEL, "No %s match the filter. %s", MODE_ACTION_NOUNS[mode], cls._tail(mode)
        )

    @staticmethod
    def _tail(mode: str) -> str:
        """Return the sentence that states what the stop left unchanged."""
        return "No action was changed." if mode == MODE_RESOLVE else "No file was written."  # WHY: mode scope.

    @classmethod
    def _export(cls, loaded: MarvisLoadedActions, selected: Sequence[MarvisActionRecord]) -> None:
        """Write the selected records to the CSV file and the database backend."""
        cls._log_status_mix(selected)  # WHY: the status summary before the alarm search and the write.
        records, documents = MarvisAlarmJoin(loaded.client).apply(selected, loaded.documents)  # WHY: issue #3339.
        rows = [record.as_row() for record in records]  # WHY: one CSV row for each action, with its alarm columns.
        target = MarvisOutputTarget.describe(EXPORT_FILENAME)  # WHY: the file or the table of the active format.
        logger.info("Writing %d Marvis Actions to %s", len(rows), target)  # WHY: action log.
        written = SourceDependencyResolver.DataExporter.write_with_format_selection(
            rows,
            EXPORT_FILENAME,
            api_function_name=EXPORT_ENDPOINT_NAME,  # WHY: the primary key strategy for the database.
            fieldnames=MarvisActionRecord.column_names(),  # WHY: a fixed column order.
            backend_options=ExportBackendOptions(raw_data=documents),  # WHY: the database keeps the raw values.
        )
        logger.debug("The export returned written=%s", written)  # WHY: result summary.
        if not written:  # WHY: never report success after a failed write.
            logger.error(  # WHY: the handled failure that the web dashboard reports as failed.
                "MistHelper could not write %s. Read the export error above.", target
            )
            return  # WHY: the error is the last word of the run.
        logger.log(  # WHY: the completion line names the file that the web dashboard offers.
            DISPLAY_LEVEL, "Completed the Marvis Actions export and wrote results to %s", target
        )

    @staticmethod
    def _log_status_mix(selected: Sequence[MarvisActionRecord]) -> None:
        """Log the status mix of the report, and one caution line for the status keys without a known name."""
        statuses = Counter(record.status_name for record in selected)  # WHY: the status mix of the report.
        mix = sorted(statuses.items())  # WHY: a stable order for the log line.
        status_text = ", ".join(f"{name or repr(name)}={count}" for name, count in mix)  # WHY: '' names an empty key.
        logger.log(  # WHY: the operator sees the mix before the write.
            DISPLAY_LEVEL, "Selected Marvis Actions by status: %s", status_text
        )
        unknown = Counter(  # WHY: issue #3342. The report counts an action with an unknown key as closed.
            record.status for record in selected if record.status not in STATUS_NAMES
        )
        if not unknown:  # WHY: each key has a known name, so the open flag of each action is certain.
            return  # WHY: no caution line.
        pairs = sorted(unknown.items())  # WHY: a stable order for the log line.
        unknown_text = ", ".join(f"{key!r}={count}" for key, count in pairs)  # WHY: repr shows an empty key as ''.
        logger.log(  # WHY: Mist can add an open status without a notice, so the operator must check these actions.
            DISPLAY_LEVEL,
            "Caution: MistHelper does not know these status keys, so the report counts their actions as closed: "
            "%s. Compare these actions with the Mist UI.",
            unknown_text,
        )
