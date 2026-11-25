"""Menu 309: collect the hardware inventory of every connected EX switch into one CSV report.

Why:
    A network operations center needs one file that lists the hardware of every
    connected EX switch, and it must not open a shell on a switch by accident.
    This menu finds the scope of the credential (one organization, or every
    organization of an MSP), previews the connected switches, asks for a typed
    phrase, runs the fixed read-only command on each switch through the verified
    collector of the Multi Site tab, and writes one CSV report. A switch that
    returned no valid reply, and an organization that could not be read, appear
    in the report as outcome rows, so the report never hides a missing switch.
"""

from __future__ import annotations

import logging  # Record each step and each result for the operator trace.
import os  # The org_id setting can come from the environment.
from collections.abc import Mapping, Sequence  # Targets are read-only identity mappings.
from dataclasses import dataclass  # One plan for each organization.
from datetime import UTC, datetime  # The run start is in UTC.
from pathlib import Path  # The run folders live under data/websocket-streams.
from typing import Any  # The SDK session has no public type.

from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolver  # Session and config.
from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # Refusals of the service.
from src.mist.realtime.websocket_streams.live.sessions.settings import StreamSettings  # Limits and flags.
from src.operations.exporting.ex_hardware_inventory.console import HardwareConsole  # The console lines.
from src.operations.exporting.ex_hardware_inventory.report.builder import ReportBuilder, TargetResult  # Report rows.
from src.operations.exporting.ex_hardware_inventory.report.csv_file import ReportCheckError, ReportTooLarge  # Errors.
from src.operations.exporting.ex_hardware_inventory.report.export import ReportExporter, ReportFile  # The file.
from src.operations.exporting.ex_hardware_inventory.run.batch import (
    BatchPreview,
    BatchRunResult,
    BatchStack,
    OrganizationBatchRun,
)  # The batch driver.
from src.operations.exporting.ex_hardware_inventory.scope.resolver import (
    OrganizationRef,
    ScopeDecision,
    ScopeError,
    ScopeResolver,
)  # The scope detection.

logger = logging.getLogger(__name__)  # Name the logger after this module so log lines carry their source.

RECOVERABLE = (StreamRequestError, OSError, RuntimeError, ValueError)  # The failures of one organization.


@dataclass
class OrganizationPlan:
    """One organization of the run, from its preview to its result.

    Attributes:
        ref: The organization.
        runner: The batch driver of the organization.
        stack: The batch services of the organization.
        preview: What the preview found, or None when the organization could not be read.
        failure: The reason code when the organization could not be read, otherwise empty.
    """

    ref: OrganizationRef  # Who this plan is for.
    runner: OrganizationBatchRun  # Previews and runs the organization.
    stack: BatchStack  # Closed at the end of the run.
    preview: BatchPreview | None = None  # Set by ``discover``.
    failure: str = ""  # Set by ``discover`` on a failure.

    @classmethod
    def build(cls, ref: OrganizationRef, apisession: Any, settings: StreamSettings) -> OrganizationPlan:
        """Build the services and the driver of one organization."""
        stack = BatchStack(apisession, ref.org_id, Path("data") / "websocket-streams", settings)  # Own services.
        return cls(ref, OrganizationBatchRun(stack, ref.org_name), stack)  # A plan with no preview yet.

    @property
    def targets(self) -> tuple[Mapping[str, object], ...]:
        """Return the confirmed switches, or none when the organization could not be read."""
        return self.preview.targets if self.preview is not None else ()  # An unread organization has no switch.

    @staticmethod
    def reason_for(error: Exception) -> str:
        """Return the reason code of a failure: its own code for a known refusal, otherwise a general code."""
        code = getattr(error, "code", "")  # Only a service refusal has a code.
        return code if code in {"target_limit", "rate_limited"} else "discovery_failed"  # A sentence for each.

    def discover(self) -> None:
        """Preview the organization, and keep a failure as a reason code instead of stopping the run."""
        try:  # A failure in one organization must not stop the others.
            self.preview = self.runner.preview()  # Discovery, filter, and snapshot.
        except RECOVERABLE as error:  # The service refuses, Mist refuses, or the transport fails.
            self.failure = self.reason_for(error)  # One plain sentence for the console and the report.
            logger.error("Discovery failed for one organization (%s)", type(error).__name__)  # Never the text.

    def unrun(self, reason: str, state: str = "skipped") -> BatchRunResult:
        """Return the result of an organization that did not run, one result for each confirmed switch."""
        return BatchRunResult.skipped(
            self.targets, self.ref.org_name, reason, state
        )  # One skipped or cancelled result for each confirmed switch.


class RunCollector:
    """Run each organization, add its results to the report, and write the file."""

    def __init__(self, scope: str, run_time: datetime, console: HardwareConsole) -> None:
        """Start an empty report.

        Args:
            scope: ``organization`` or ``msp``.
            run_time: The run start in UTC.
            console: The console that prints the step 4 lines.
        """
        self._run_time = run_time  # Names the file, and stamps every row.
        self.builder = ReportBuilder(scope, run_time.strftime("%Y-%m-%dT%H:%M:%SZ"))  # ISO 8601 in UTC.
        self._console = console  # One line for each organization.

    def run_all(self, plans: Sequence[OrganizationPlan]) -> bool:
        """Run every organization that has a target, in order.

        Args:
            plans: The organizations of the run.

        Returns:
            True when the operator cancelled the run.
        """
        cancelled = False  # No cancel yet.
        for plan in plans:  # One organization at a time, so the rate limit holds.
            if plan.failure:  # The organization could not be read: one outcome row, no run.
                identity = {"org_id": plan.ref.org_id}  # No site and no switch exist for this row.
                self.builder.add(
                    TargetResult(identity, plan.ref.org_name, "failed", plan.failure, None)
                )  # One outcome row for the unread organization.
            elif plan.targets:  # An organization with no switch has nothing to run.
                cancelled = self._run_one(plan, cancelled)  # Marks the switches cancelled once cancelled.
        return cancelled  # The caller must know whether the operator cancelled.

    def _run_one(self, plan: OrganizationPlan, cancelled: bool) -> bool:
        """Run one organization, or mark its switches cancelled when the run is already cancelled."""
        before = self.builder.counts()  # The tally before this organization.
        result = plan.unrun("cancelled", "stopped")  # The result when the operator already cancelled.
        if not cancelled:  # Run only while the operator has not cancelled.
            try:  # Ctrl+C outside the wait also cancels, and a failure here must not stop the others.
                result = self._attempt(plan)  # Re-preview when needed, start, wait, and read.
            except KeyboardInterrupt:  # Nothing started, so every switch is cancelled.
                result = plan.unrun("cancelled", "stopped")  # Nothing started, so every switch is cancelled.
        for item in result.results:  # One result for each confirmed switch.
            self.builder.add(item)  # Rows and tally.
        after = self.builder.counts()  # The tally after this organization.
        self._console.collected(
            plan.ref.org_name, {name: count - before[name] for name, count in after.items()}
        )  # Show the result of this organization.
        if result.reason == "new_targets":  # The organization was not run.
            print(
                f"  {plan.ref.org_name}: new switches appeared after the confirmation. Run the menu again."
            )  # WHY: the operator must run the menu again to see them.
        return cancelled or result.cancelled  # A cancelled run skips the remaining organizations.

    @staticmethod
    def _attempt(plan: OrganizationPlan) -> BatchRunResult:
        """Run one organization and turn a failure into skipped results that name the cause."""
        if plan.preview is None:  # Only a plan with a preview reaches this method.
            return plan.unrun("discovery_failed")  # A plan with no preview cannot run.
        try:  # The service refuses, Mist refuses, or the transport fails.
            return plan.runner.run(plan.preview)  # Re-preview when needed, start, wait, and read.
        except RECOVERABLE as error:  # One organization fails alone.
            logger.error("The run failed for one organization (%s)", type(error).__name__)  # Never the text.
            return plan.unrun(plan.reason_for(error))  # Each confirmed switch is skipped with the cause.

    def write(self) -> ReportFile | None:
        """Write the report and say so when the size limit or the file check stops it.

        Returns:
            The written file, or None when no file exists.
        """
        try:  # The exporter refuses a report over the limit and removes a file that fails its check.
            return ReportExporter().write(
                self.builder.rows(), self.builder.fieldnames(), self._run_time
            )  # Writes the file, reads it back, and removes a damaged file.
        except ReportTooLarge:  # FR-041: say so, and write nothing.
            print(
                "The report would pass the size limit of 64 MiB. No file was written."
            )  # WHY: say why no file exists.
        except ReportCheckError:  # The exporter removed the damaged file.
            print(
                "The report file failed its check and was removed. See the log for the cause."
            )  # WHY: say why no file exists.
        return None  # No file exists.


class ExHardwareInventoryReport:
    """Menu 309: one CSV report of the hardware inventory of every connected EX switch."""

    @staticmethod
    def run() -> int:
        """Run the whole workflow.

        Returns:
            The number of report rows, or 0 when the run wrote no file.
        """
        logger.info("Starting the EX hardware inventory report")  # Log before the first request.
        console = HardwareConsole()  # The console lines.
        plans: list[OrganizationPlan] = []  # The plans fill as the organizations are found.
        try:  # Close every service stack, whatever ends the run.
            try:  # Ctrl+C before the shells open cancels the run safely.
                decision = ExHardwareInventoryReport._scope(console)  # Step 1.
                if decision is None:  # The profile could not be read, or the organization is not clear.
                    return 0  # No file was written.
                ExHardwareInventoryReport._find(decision, console, plans)  # Step 2.
                if not ExHardwareInventoryReport._confirmed(plans, console):  # Step 3.
                    return 0  # No file was written.
            except KeyboardInterrupt:  # The operator pressed Ctrl+C before any shell opened.
                print("Cancelled. No shell was opened and no file was written.")  # WHY: tell the safe outcome.
                return 0  # No file was written.
            return ExHardwareInventoryReport._collect(decision, plans, console)  # Step 4 and the report.
        finally:  # Close every service stack, whatever ends the run.
            for plan in plans:  # Stop the helper threads of each stack.
                plan.stack.shutdown()  # Stop the helper threads of the stack.

    @staticmethod
    def _scope(console: HardwareConsole) -> ScopeDecision | None:
        """Step 1: read the profile and decide the scope. Print the reason and return None when it cannot."""
        apisession = SourceDependencyResolver.apisession  # The session that the menu already opened.
        if apisession is None:  # No credential, so no request can run.
            print("No Mist session exists. Sign in first. No shell was opened.")  # WHY: the operator must act.
            return None  # The run cannot go on.
        cached = SourceDependencyResolver.ConfigUtils.get_cached_org_id()  # A cached choice never prompts.
        configured = cached or os.environ.get("org_id") or os.environ.get("ORG_ID")  # The documented settings.
        try:  # The scope can be unclear, and the operator then needs one plain sentence.
            decision = ScopeResolver(
                apisession, configured
            ).resolve()  # The profile and the MSP lists decide the scope.
        except ScopeError as error:  # The sentence of the error names the fix.
            print(str(error))  # WHY: the sentence names the fix.
            return None  # The run cannot go on.
        console.credential(decision)  # The credential, the scope, the organizations, and the notes.
        return decision  # Step 2 uses the decision.

    @staticmethod
    def _find(decision: ScopeDecision, console: HardwareConsole, plans: list[OrganizationPlan]) -> None:
        """Step 2: preview each organization, one at a time, and keep each plan in the caller list."""
        print("Step 2 of 4: Find the connected EX switches")  # WHY: the operator follows the four steps.
        apisession, settings = (
            SourceDependencyResolver.apisession,
            StreamSettings.from_environment(),
        )  # One session and one set of limits for each organization.
        for ref in decision.organizations:  # One organization at a time, so the rate limit holds.
            plan = OrganizationPlan.build(ref, apisession, settings)  # Own services for the organization.
            plans.append(plan)  # The caller closes it even when Ctrl+C stops this loop.
            plan.discover()  # A failure becomes a reason code, not a stop.
            excluded = plan.preview.excluded if plan.preview is not None else {}  # The left-out counts.
            console.found(
                ref.org_name, len(plan.targets), excluded, plan.failure
            )  # Show the count and the left-out switches of this organization.

    @staticmethod
    def _confirmed(plans: Sequence[OrganizationPlan], console: HardwareConsole) -> bool:
        """Step 3: ask for the typed phrase. Return False when there is nothing to run or the operator cancels."""
        total = sum(len(plan.targets) for plan in plans)  # The phrase names the total of all organizations.
        if total == 0:  # FR-042: no target means no run and no file.
            print("No connected EX switch was found. No file was written.")  # WHY: say so.
            return False  # Nothing to confirm.
        return console.confirm(total, plans[0].stack.concurrency)  # The same setting for every stack.

    @staticmethod
    def _collect(decision: ScopeDecision, plans: Sequence[OrganizationPlan], console: HardwareConsole) -> int:
        """Step 4: run each organization, write the report, and print the summary."""
        print("Step 4 of 4: Collect")  # WHY: the operator follows the four steps.
        collector = RunCollector(decision.mode, datetime.now(UTC).replace(microsecond=0), console)  # UTC.
        cancelled = collector.run_all(plans)  # The tally and the rows fill as each organization ends.
        report = collector.write()  # One CSV file, or none.
        counts = collector.builder.counts()  # The tally of all organizations.
        partial = cancelled or counts["failed"] + counts["skipped"] + counts["cancelled"] > 0  # Anything missing.
        console.finished(report, partial)  # The report line and the run status.
        logger.debug(
            "Finished the EX hardware inventory report with %d rows", report.row_count if report else 0
        )  # Log the result.
        return report.row_count if report is not None else 0  # The rows written, or none.
