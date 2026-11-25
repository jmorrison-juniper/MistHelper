"""Print the steps of menu 309 and read the typed confirmation.

Why:
    The operator is a junior engineer in a network operations center, so every
    line uses plain words, and the text is ASCII only. The lines live in one
    place so the console contract has one owner, and so a test can check the
    exact text. The confirmation phrase goes through the repository input helper,
    which handles end of input and Ctrl+C by returning an empty answer, and an
    empty or wrong answer cancels the run.
"""

from __future__ import annotations

import logging  # Record each prompt and its result for the operator trace.
from collections.abc import Mapping  # The counts arrive as read-only mappings.
from typing import TYPE_CHECKING

from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolver  # Input helper.
from src.mist.realtime.websocket_streams.web.services.operations.hardware_xml import HardwareXmlPreset  # Command.
from src.operations.exporting.ex_hardware_inventory.scope.resolver import ScopeDecision  # The scope decision.

if TYPE_CHECKING:  # Avoid a runtime import for a type that only annotates.
    from src.operations.exporting.ex_hardware_inventory.report.export import ReportFile  # The written file.

logger = logging.getLogger(__name__)  # Name the logger after this module so log lines carry their source.


class HardwareConsole:
    """The console lines of menu 309, one method for each part of the contract."""

    FAILURES = {
        "target_limit": "has more than 1000 targets. The limit is 1000 for one batch.",
        "rate_limited": "was not read, because Mist limited the requests.",
        "discovery_failed": "was not read, because Mist could not list its switches. See the log for the cause.",
    }  # One plain sentence for each reason that an organization could not be read.

    def credential(self, decision: ScopeDecision) -> None:
        """Print step 1: the credential, the scope, and the notes."""
        scope = "MSP" if decision.mode == "msp" else "organization"  # The two scopes.
        kind = "interactive login" if decision.credential_type == "login" else "API token"  # Plain names.
        account = "user account" if decision.account_kind == "user" else "organization token"  # Plain names.
        print("Step 1 of 4: Check the credential")  # WHY: the operator follows the four steps on the console.
        print(f"  Credential: {kind} ({account})")  # WHY: the operator must see what kind of credential runs.
        print(f"  Scope: {scope}")  # WHY: the operator must see which scope the tool chose.
        print(f"  Organizations in scope: {len(decision.organizations)}")  # WHY: the size of the run.
        for note in decision.notes:  # One plain sentence for each unusual event, for example a denied MSP list.
            print(f"  Note: {note}")  # WHY: a failed MSP list must be said once.

    def found(self, org_name: str, target_count: int, excluded: Mapping[str, int], failure: str = "") -> None:
        """Print the result of step 2 for one organization.

        Args:
            org_name: The organization name.
            target_count: The number of connected EX switches that the preview found.
            excluded: The count of each left-out reason.
            failure: The reason code when the organization could not be read, otherwise empty.
        """
        if failure:  # The organization could not be read, so there is no count to show.
            print(f"  {org_name} {self.FAILURES[failure]}")  # WHY: a failed organization must not look empty.
            return  # No left-out line for an organization that was not read.
        print(f"  {org_name}: {target_count} connected EX switches")  # WHY: the operator confirms these counts.
        if any(excluded.values()):  # The line appears for an organization with a count above 0.
            print(
                f"  Left out: offline {excluded.get('offline', 0)}, "
                f"unknown status {excluded.get('unknown_status', 0)}, "
                f"other device types {excluded.get('incompatible_family', 0)}, "
                f"repeated chassis {excluded.get('duplicate_device', 0)}"
            )  # WHY: the operator sees why a device is not in the run.

    def confirm(self, total: int, concurrency: int) -> bool:
        """Print step 3 and read the typed phrase.

        Args:
            total: The number of targets of all organizations.
            concurrency: The most shells open at the same time.

        Returns:
            True only when the operator typed the exact phrase.
        """
        phrase = f"RUN {total} TARGETS"  # The phrase that starts the run.
        print(f"  Total targets: {total}")  # WHY: the phrase names this number.
        print("Step 3 of 4: Confirm")  # WHY: the operator follows the four steps on the console.
        print("  This run opens a read-only shell on each switch and runs one command:")
        print(f"    {HardwareXmlPreset.COMMANDS['xml']}")  # WHY: the operator sees the one fixed command.
        print(f"  Shells open at the same time: {concurrency}")  # WHY: the setting in use.
        logger.info("Asking the operator for the typed confirmation phrase")  # Log before the prompt.
        answer = SourceDependencyResolver.InputUtils.safe_input(
            f"  Type {phrase} to start, or press Enter to cancel: ", context="ex_hardware_confirmation"
        )  # End of input and Ctrl+C return an empty answer.
        confirmed = str(answer).strip() == phrase  # An exact compare. The case counts.
        logger.debug("The typed confirmation matched=%s", confirmed)  # Log the result, never the answer.
        if not confirmed:  # Any other text, an empty answer, end of input, or an interrupt cancels the run.
            print("Cancelled. No shell was opened and no file was written.")  # WHY: tell the safe outcome.
        return confirmed

    def collected(self, org_name: str, counts: Mapping[str, int]) -> None:
        """Print the step 4 line of one organization."""
        print(
            f"  {org_name}: collected {counts['collected']}, failed {counts['failed']}, "
            f"skipped {counts['skipped']}, cancelled {counts['cancelled']}"
        )  # WHY: the operator sees the result of each organization as it ends.

    def finished(self, report: ReportFile | None, partial: bool) -> None:
        """Print the report line and the run status."""
        if report is not None:  # A run with no row writes no file, so it has no report line.
            print(f"Report: {report.path} ({report.row_count} rows)")  # WHY: the operator needs the file path.
        print(f"Run status: {'partial' if partial else 'complete'}")  # WHY: a partial run must be visible.
