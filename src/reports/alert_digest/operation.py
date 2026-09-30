"""Menu operation for alert digest and alarm acknowledgement."""

from __future__ import annotations  # Enable modern annotations without runtime imports.

import logging  # Record each operator action before and after it.
from typing import Any  # Accept resolver, client, and writer test doubles.

from src.config.source_dependency_resolver import SourceDependencyResolver  # Resolve MistHelper shared dependencies.
from src.reports.alert_digest.client import AlertDigestClient  # Use the feature-owned Mist API wrapper.
from src.reports.alert_digest.model import AlertDigestModel  # Use pure grouping and result helpers.
from src.reports.alert_digest.prompts import AlertDigestPromptResolver  # Use shared lookback and confirmation logic.
from src.reports.alert_digest.writer import AlertDigestWriter  # Write CSV and Markdown outputs.
from src.utils.console import echo  # Show operator messages without warning-level logs.

logger = logging.getLogger(__name__)  # Keep log records tied to this module.


class AlertDigestOperation:
    """Run menu 280 and menu 281 alert workflows."""

    def __init__(
        self,
        client: Any | None = None,
        writer: AlertDigestWriter | None = None,
        input_utils: Any | None = None,
        resolver: Any | None = None,
    ) -> None:
        """Keep optional test seams for client, writer, input, and resolver."""
        self._client = client  # Store a fake client when a unit test supplies one.
        self._writer = writer or AlertDigestWriter()  # Store the writer that creates output files.
        self._resolver = resolver or SourceDependencyResolver  # Store the shared dependency resolver.
        self._input_utils = input_utils or self._resolver.InputUtils  # Store EOF-safe input helpers.

    @classmethod
    def run(cls) -> bool:
        """Run the safe digest path as the default action."""
        logger.info("Running the default alert digest action")  # Log before dispatch.
        result = cls.run_digest()  # Dispatch to the safe menu 280 behavior.
        logger.debug("The default alert digest action returned %s", result)  # Log result.
        return result  # Return the digest outcome.

    @classmethod
    def run_digest(cls) -> bool:
        """Create the alert digest outputs for menu 280."""
        logger.info("Menu #280: Starting the alert digest handler")  # Log the menu entry point.
        result = cls().execute_digest()  # Build live dependencies and run the safe workflow.
        logger.debug("Menu #280 alert digest handler returned %s", result)  # Log the handler result.
        return result  # Return the operation result for dashboards.

    @classmethod
    def run_acknowledge(cls) -> bool:
        """Acknowledge alarms for menu 281 after destructive safety checks."""
        logger.info("Menu #281: Starting the alert acknowledgement handler")  # Log the destructive entry point.
        dry_run = AlertDigestPromptResolver.dry_run_requested()  # Read the shared dry-run flag from arguments.
        result = cls().execute_acknowledge(dry_run=dry_run)  # Build live dependencies and run the workflow.
        logger.debug("Menu #281 alert acknowledgement handler returned %s", result)  # Log the handler result.
        return result  # Return the operation result for dashboards.

    def execute_digest(self) -> bool:
        """Create the alert digest outputs for the shared lookback window."""
        logger.info("Starting the alert digest operation")  # Log before the workflow starts.
        context = self._load_context()  # Resolve lookback, client, and rows.
        if context is None:  # Invalid lookback or API failure stops the digest safely.
            return False  # Return a failed operation.
        groups = AlertDigestModel.group_records(context["records"])  # Group alarms by category, type, and site.
        output_ok = self._writer.write_digest(groups)  # Write CSV and Markdown outputs.
        echo("  Alert digest wrote %d grouped row(s).", len(groups))  # Tell the operator what was produced.
        logger.debug("The alert digest operation completed with output_ok=%s", output_ok)  # Log result.
        return output_ok  # Return the write result.

    def execute_acknowledge(self, dry_run: bool = False) -> bool:
        """Acknowledge unacknowledged alarms after exact operator confirmation."""
        logger.info("Starting the alert acknowledgement operation dry_run=%s", dry_run)  # Log before workflow.
        context = self._load_context()  # Resolve lookback, client, and rows.
        if context is None:  # Invalid lookback or API failure sends no destructive request.
            return False  # Return a failed operation.
        candidates = AlertDigestModel.acknowledgement_candidates(context["records"])  # Select unacknowledged alarms.
        self._display_candidates(candidates)  # Show the operator exactly what can be acknowledged.
        if not candidates:  # No candidate means no destructive request is needed.
            return self._write_results(candidates, "skipped", None, "No unacknowledged alarms were found.")  # Log.
        if dry_run:  # Dry run must not send a request.
            return self._write_results(candidates, "dry_run", None, "Dry run. No acknowledgement request was sent.")
        if not self._confirmed(len(candidates)):  # Exact confirmation is required before a request.
            return self._write_results(candidates, "cancelled", None, "Confirmation did not match. No request sent.")
        status, problem = context["client"].acknowledge_alarms([candidate.alarm_id for candidate in candidates])
        outcome = "acknowledged" if not problem else "error"  # Treat an empty problem as a successful bulk request.
        message = "Acknowledgement request accepted." if not problem else problem  # Preserve an error reason.
        return self._write_results(candidates, outcome, status, message)  # Write one row per candidate.

    def _load_context(self) -> dict[str, Any] | None:
        """Resolve client data needed by both menu paths."""
        try:
            hours = AlertDigestPromptResolver.resolve_lookback_hours()  # Read the shared lookback value.
        except ValueError as error:
            logger.error("Invalid alert digest lookback: %s", error)  # Log the rejected operator setting.
            echo("  %s", error)  # Show the validation message to the operator.
            return None  # Fail closed before any destructive request.
        client = self._resolve_client()  # Build or reuse the API client.
        definitions = AlertDigestModel.definitions_by_key(client.list_alarm_definitions())  # Read categories.
        alarm_result = client.search_alarms(hours)  # Read alarm rows from the same lookback window.
        if alarm_result.problem:  # A failed alarm search must not produce a false success.
            logger.error("Alert alarm search failed: %s", alarm_result.problem)  # Log failure reason.
            echo("  Alert alarm search failed: %s", alarm_result.problem)  # Show failure to the operator.
            return None  # Fail closed.
        records = AlertDigestModel.records_from_rows(alarm_result.rows, definitions)  # Normalize rows.
        return {"client": client, "records": records, "hours": hours}  # Return shared operation context.

    def _resolve_client(self) -> Any:
        """Return the injected or live alert digest client."""
        if self._client is not None:  # Unit tests inject a fake client.
            logger.debug("Using the injected alert digest client")  # Log the test seam.
            return self._client  # Return the fake client.
        logger.info("Resolving the organization for alert digest")  # Log before dependency lookup.
        org_id = self._resolver.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the active organization.
        client = AlertDigestClient(self._resolver.apisession, org_id)  # Build the live Mist API client.
        logger.debug("Resolved alert digest client for org_present=%s", bool(org_id))  # Log safe result.
        return client  # Return the live client.

    def _confirmed(self, count: int) -> bool:
        """Prompt for exact acknowledgement confirmation."""
        logger.info("Prompting for alert acknowledgement confirmation")  # Log before destructive prompt.
        answer = self._input_utils.safe_input(
            f"Type ACK {count} to acknowledge {count} alarm(s): ", context="alert_ack"
        )
        matched = AlertDigestPromptResolver.confirmation_matches(answer, count)  # Validate exact confirmation.
        if not matched:  # Wrong input cancels the destructive action.
            logger.info("Alert acknowledgement cancelled because confirmation did not match")  # Required log line.
        logger.debug("Alert acknowledgement confirmation matched=%s", matched)  # Log result.
        return matched  # Return the safety decision.

    @staticmethod
    def _display_candidates(candidates: list[Any]) -> None:
        """Show acknowledgement candidates to the operator."""
        logger.info("Displaying %d acknowledgement candidates", len(candidates))  # Log before output.
        echo("  Found %d unacknowledged alarm(s).", len(candidates))  # Show count required for confirmation.
        for candidate in candidates:  # Show each ID so dry-run output is complete.
            echo("  %s %s %s %s", candidate.alarm_id, candidate.severity, candidate.site, candidate.alarm_type)
        logger.debug("Displayed %d acknowledgement candidates", len(candidates))  # Log result.

    def _write_results(self, candidates: list[Any], outcome: str, status: int | None, message: str) -> bool:
        """Write acknowledgement result rows and report the operation outcome."""
        results = AlertDigestModel.result_rows(candidates, outcome, status, message)  # Build log rows.
        write_ok = self._writer.write_acknowledgement_log(results) if results else True  # Skip empty writes safely.
        echo("  %s", message)  # Show the operator the final outcome.
        logger.debug("Alert acknowledgement result outcome=%s write_ok=%s", outcome, write_ok)  # Log result.
        return bool(write_ok and outcome not in {"error", "cancelled"})  # Cancellation is safe but not successful.
