"""Menu handler for the Mist Edge lifecycle operation.

Why:
    Menu 293 groups destructive Mist Edge lifecycle actions behind typed
    confirmations and dry-run support.
"""

from __future__ import annotations  # WHY: allow concise type syntax on Python 3.13.

import csv  # WHY: the feature writes one operator evidence file.
import logging  # WHY: every destructive action needs an action trace.
import time  # WHY: upgrade polling uses a bounded sleep interval.
from pathlib import Path  # WHY: paths must work on Windows, macOS, and Linux.
from typing import Any, Protocol  # WHY: tests use fake clients with the same methods.

from src.config.source_dependency_resolver import SourceDependencyResolver  # WHY: access shared session and org helper.
from src.org.mxedge_lifecycle.client import MxEdgeLifecycleClient  # WHY: real Mist SDK client.
from src.org.mxedge_lifecycle.models import (  # WHY: pure request and row models.
    CSV_FIELDNAMES,
    STATUS_CANCELLED,
    STATUS_DRY_RUN,
    STATUS_ERROR,
    STATUS_SENT,
    STATUS_TIMEOUT,
    LifecycleRequest,
    MxEdgeLifecycleModels,
    UpgradePollResult,
    UpgradeStatusReader,
)
from src.utils.input_utils import InputUtils  # WHY: prompts must be EOF-safe.

logger = logging.getLogger(__name__)  # WHY: module logger lets operators filter lifecycle runs.

EXPORT_FILENAME = "MxEdgeLifecycleLog.csv"  # WHY: assignment requires this exact evidence file.
UPGRADE_POLL_INTERVAL_SECONDS = 5  # WHY: avoid tight loops against Mist API.
UPGRADE_POLL_TIMEOUT_SECONDS = 1800  # WHY: service plus OS upgrade can take about 30 minutes.
MENU_PROMPT = "Select Mist Edge lifecycle step (1-5, q to quit): "  # WHY: one submenu owns all steps.


class MxEdgeLifecycleClientProtocol(Protocol):
    """Methods the operation needs from a Mist Edge lifecycle client."""

    def claim(self, body: dict[str, Any]) -> dict[str, Any]:
        """Claim a Mist Edge."""

    def assign(self, body: dict[str, Any]) -> dict[str, Any]:
        """Assign Mist Edges to a site."""

    def unassign(self, body: dict[str, Any]) -> dict[str, Any]:
        """Unassign Mist Edges from a site."""

    def bounce(self, mxedge_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Bounce data ports."""

    def upgrade(self, body: dict[str, Any]) -> dict[str, Any]:
        """Start an upgrade."""

    def list_upgrades(self) -> list[dict[str, Any]]:
        """List upgrades."""

    def get_upgrade(self, upgrade_id: str) -> dict[str, Any]:
        """Read one upgrade."""


class MxEdgeLifecycleOperation:
    """Run the destructive Mist Edge lifecycle sub-menu.

    Why:
        The integration pull request can point menu 293 at `run()` with no
        arguments, matching other class-based menu handlers.
    """

    @staticmethod
    def run(dry_run: bool = False) -> None:
        """Resolve shared context and run the interactive sub-menu."""
        logger.warning("Menu #293 DESTRUCTIVE: Starting Mist Edge lifecycle operation")  # WHY: risk banner.
        org_id = str(SourceDependencyResolver.ConfigUtils.get_cached_or_prompted_org_id())  # WHY: org scoped API.
        session = SourceDependencyResolver.apisession  # WHY: shared authenticated session.
        if session is None:  # WHY: no request can run without a session.
            logger.error("No active API session exists for Mist Edge lifecycle operation")  # WHY: clear stop reason.
            return  # WHY: stop before prompts can imply a change.
        client = MxEdgeLifecycleClient(session, org_id)  # WHY: real SDK client for menu runs.
        MxEdgeLifecycleOperation(
            client, org_id, default_dry_run=dry_run
        ).run_menu()  # WHY: pass the shared dry-run flag.

    def __init__(
        self,
        client: MxEdgeLifecycleClientProtocol,
        org_id: str,
        csv_path: Path | None = None,
        default_dry_run: bool = False,
    ) -> None:
        """Store client, organization, CSV path, and dry-run default."""
        self.client = client  # WHY: fake clients make tests network-free.
        self.org_id = org_id  # WHY: each CSV row names the organization.
        self.csv_path = csv_path or Path("data") / EXPORT_FILENAME  # WHY: assignment requires data directory output.
        self.default_dry_run = default_dry_run  # WHY: CLI --dry-run must preview without another prompt.

    def run_menu(self) -> None:
        """Ask for one sub-menu choice and execute it."""
        self._print_menu()  # WHY: show the five destructive steps.
        choice = self._ask(MENU_PROMPT, "mxedge_lifecycle_menu").strip().lower()  # WHY: EOF-safe menu input.
        handlers = self._handlers()  # WHY: one mapping keeps dispatch simple.
        if choice in {"q", "quit", ""}:  # WHY: allow a no-change exit.
            logger.info("Mist Edge lifecycle operation exited before selecting a step")  # WHY: audit no-op exit.
            return  # WHY: no request selected.
        handler = handlers.get(choice)  # WHY: map number to lifecycle step.
        if handler is None:  # WHY: invalid choice must not guess a destructive action.
            logger.error("Invalid Mist Edge lifecycle menu choice: %s", choice[:20])  # WHY: clear refusal.
            return  # WHY: no request selected.
        try:
            handler()  # WHY: execute one selected step.
        except ValueError as error:
            self._print_input_error(error)  # WHY: replace validation tracebacks with one safe sentence.

    @staticmethod
    def _print_input_error(error: ValueError) -> None:
        """Print a concise validation error and stop before any request."""
        logger.error("Mist Edge lifecycle input was invalid: %s", error)  # WHY: log validation failure without trace.
        print(f"No Mist request was sent because {error}.")  # WHY: one sentence replaces an operator traceback.

    def _handlers(self) -> dict[str, Any]:
        """Return sub-menu handlers by numeric choice."""
        return {  # WHY: keep menu dispatch explicit and testable.
            "1": self._claim_prompt,  # WHY: claim inventory step.
            "2": self._assign_prompt,  # WHY: assign site step.
            "3": self._unassign_prompt,  # WHY: unassign site step.
            "4": self._bounce_prompt,  # WHY: bounce data ports step.
            "5": self._upgrade_prompt,  # WHY: upgrade and poll step.
        }

    @staticmethod
    def _print_menu() -> None:
        """Print the Mist Edge lifecycle sub-menu."""
        print("Mist Edge lifecycle steps")  # WHY: title for the sub-menu.
        print("1. Claim a Mist Edge")  # WHY: step 1.
        print("2. Assign Mist Edges to a site")  # WHY: step 2.
        print("3. Unassign Mist Edges from a site")  # WHY: step 3.
        print("4. Bounce Mist Edge data ports")  # WHY: step 4.
        print("5. Upgrade Mist Edges and poll status")  # WHY: step 5.

    def _claim_prompt(self) -> None:
        """Prompt for claim inputs and run the claim step."""
        claim_code = self._ask("Enter Mist Edge claim code: ", "mxedge_claim_code").strip()  # WHY: API body needs code.
        dry_run = self._ask_dry_run()  # WHY: every destructive step supports preview.
        request = MxEdgeLifecycleModels.claim(claim_code, dry_run=dry_run)  # WHY: build OpenAPI request body.
        self._execute(request, lambda: self.client.claim(request.body))  # WHY: send after confirmation only.

    def _assign_prompt(self) -> None:
        """Prompt for assign inputs and run the assign step."""
        mxedge_ids = self._ask_ids("Enter Mist Edge IDs, comma separated: ", "mxedge_assign_ids")  # WHY: targets.
        site_id = self._ask("Enter target site ID: ", "mxedge_assign_site").strip()  # WHY: assignment target.
        dry_run = self._ask_dry_run()  # WHY: every destructive step supports preview.
        request = MxEdgeLifecycleModels.assign(mxedge_ids, site_id, dry_run=dry_run)  # WHY: build request body.
        self._execute(request, lambda: self.client.assign(request.body))  # WHY: send after confirmation only.

    def _unassign_prompt(self) -> None:
        """Prompt for unassign inputs and run the unassign step."""
        mxedge_ids = self._ask_ids("Enter Mist Edge IDs, comma separated: ", "mxedge_unassign_ids")  # WHY: targets.
        dry_run = self._ask_dry_run()  # WHY: every destructive step supports preview.
        request = MxEdgeLifecycleModels.unassign(mxedge_ids, dry_run=dry_run)  # WHY: build request body.
        self._execute(request, lambda: self.client.unassign(request.body))  # WHY: send after confirmation only.

    def _bounce_prompt(self) -> None:
        """Prompt for bounce inputs and run the port bounce step."""
        mxedge_id = self._ask("Enter Mist Edge ID: ", "mxedge_bounce_id").strip()  # WHY: endpoint path needs ID.
        ports = self._ask_ids("Enter data ports, comma separated: ", "mxedge_bounce_ports")  # WHY: body needs ports.
        dry_run = self._ask_dry_run()  # WHY: every destructive step supports preview.
        request = MxEdgeLifecycleModels.bounce(mxedge_id, ports, dry_run=dry_run)  # WHY: build request body.
        self._execute(request, lambda: self.client.bounce(mxedge_id, request.body))  # WHY: send after confirmation.

    def _upgrade_prompt(self) -> None:
        """Prompt for upgrade inputs, start upgrade, and poll status."""
        mxedge_ids = self._ask_ids("Enter Mist Edge IDs, comma separated: ", "mxedge_upgrade_ids")  # WHY: targets.
        version = self._ask(  # WHY: read the target tunnel service version.
            "Enter tunnel service version or latest: ", "mxedge_upgrade_version"
        ).strip()
        dry_run = self._ask_dry_run()  # WHY: every destructive step supports preview.
        request = MxEdgeLifecycleModels.upgrade(mxedge_ids, version or "latest", dry_run=dry_run)  # WHY: body.
        self._execute_upgrade(request, mxedge_ids)  # WHY: upgrade needs polling after submit.

    def _execute(self, request: LifecycleRequest, sender: Any) -> None:
        """Confirm, optionally send, and write one lifecycle log row."""
        if not self._confirmed(request):  # WHY: wrong word blocks destructive API call.
            logger.info("Mist Edge lifecycle step %s cancelled by confirmation", request.step)  # WHY: audit cancel.
            self._write_row(request.as_row(self.org_id, STATUS_CANCELLED, "confirmation mismatch"))  # WHY: evidence.
            return  # WHY: do not send.
        if request.dry_run:  # WHY: dry-run must send no request.
            print(f"Dry run request: {request.step} {self._safe_body(request)}")  # WHY: operator previews request.
            self._write_row(request.as_row(self.org_id, STATUS_DRY_RUN, "dry-run only"))  # WHY: evidence.
            return  # WHY: do not send.
        try:  # WHY: API failures need one CSV row.
            data = sender()  # WHY: call the selected client method only after confirmation.
        except Exception as error:  # WHY: keep CLI alive with a clear row.
            logger.error("Mist Edge lifecycle step %s failed: %s", request.step, error)  # WHY: action failure.
            self._write_row(request.as_row(self.org_id, STATUS_ERROR, str(error)[:200]))  # WHY: evidence.
            return  # WHY: failed request is complete.
        self._write_row(request.as_row(self.org_id, STATUS_SENT, self._detail(data)))  # WHY: record accepted request.

    def _execute_upgrade(self, request: LifecycleRequest, mxedge_ids: list[str]) -> None:
        """Confirm, start upgrade, and poll when not a dry-run."""
        if not self._confirmed(request):  # WHY: wrong word blocks destructive API call.
            logger.info("Mist Edge lifecycle step %s cancelled by confirmation", request.step)  # WHY: audit cancel.
            self._write_row(request.as_row(self.org_id, STATUS_CANCELLED, "confirmation mismatch"))  # WHY: evidence.
            return  # WHY: do not send.
        if request.dry_run:  # WHY: dry-run must send no request.
            print(f"Dry run request: {request.step} {self._safe_body(request)}")  # WHY: operator previews request.
            self._write_row(request.as_row(self.org_id, STATUS_DRY_RUN, "dry-run only"))  # WHY: evidence.
            return  # WHY: do not send.
        try:  # WHY: upgrade and polling can each fail.
            data = self.client.upgrade(request.body)  # WHY: start the upgrade after confirmation.
            upgrade_id = self._upgrade_id(data, mxedge_ids)  # WHY: choose the status object to poll.
            poll = self.poll_upgrade(upgrade_id)  # WHY: wait for terminal status or timeout.
        except Exception as error:  # WHY: keep CLI alive with a clear row.
            logger.error("Mist Edge upgrade step failed: %s", error)  # WHY: action failure.
            self._write_row(request.as_row(self.org_id, STATUS_ERROR, str(error)[:200]))  # WHY: evidence.
            return  # WHY: failed request is complete.
        self._write_row(self._upgrade_row(request, poll))  # WHY: record final poll state.

    def poll_upgrade(self, upgrade_id: str, timeout_seconds: int = UPGRADE_POLL_TIMEOUT_SECONDS) -> UpgradePollResult:
        """Poll one upgrade status until terminal state or timeout."""
        deadline = time.monotonic() + timeout_seconds  # WHY: monotonic time is safe across clock changes.
        poll_count = 0  # WHY: result evidence includes read count.
        while time.monotonic() <= deadline:  # WHY: bounded loop prevents endless API calls.
            poll_count += 1  # WHY: count this status read.
            document = self.client.get_upgrade(upgrade_id)  # WHY: read current upgrade status.
            status = UpgradeStatusReader.status_from(document)  # WHY: normalize status field names.
            if UpgradeStatusReader.is_terminal(status):  # WHY: terminal status stops polling.
                return UpgradePollResult(upgrade_id, status, True, False, poll_count)  # WHY: success or terminal fail.
            time.sleep(UPGRADE_POLL_INTERVAL_SECONDS)  # WHY: avoid a tight API loop.
        return UpgradePollResult(  # WHY: timeout reached before a terminal status.
            upgrade_id, status if poll_count else "unknown", False, True, poll_count
        )

    def _upgrade_id(self, data: dict[str, Any], mxedge_ids: list[str]) -> str:
        """Return the upgrade identifier from response data or list fallback."""
        direct = self._first_text(data, ("id", "upgrade_id"))  # WHY: common response fields.
        if direct:  # WHY: direct ID is most reliable.
            return direct  # WHY: poll this ID.
        rows = self.client.list_upgrades()  # WHY: fallback when submit response has no ID.
        return self._matching_upgrade_id(rows, mxedge_ids)  # WHY: choose newest matching upgrade.

    @staticmethod
    def _matching_upgrade_id(rows: list[dict[str, Any]], mxedge_ids: list[str]) -> str:
        """Return the first upgrade ID that mentions a target Mist Edge."""
        target_ids = set(mxedge_ids)  # WHY: set lookup is clear and fast.
        for row in rows:  # WHY: API usually returns newest first.
            row_ids = set(row.get("mxedge_ids", []))  # WHY: row can name target devices.
            upgrade_id = MxEdgeLifecycleOperation._first_text(row, ("id", "upgrade_id"))  # WHY: possible keys.
            if upgrade_id and (not row_ids or row_ids & target_ids):  # WHY: accept matching or generic row.
                return upgrade_id  # WHY: poll this status object.
        raise ValueError("No Mist Edge upgrade ID was found for polling")  # WHY: cannot poll without an ID.

    @staticmethod
    def _first_text(data: dict[str, Any], keys: tuple[str, ...]) -> str:
        """Return the first non-empty text value for candidate keys."""
        for key in keys:  # WHY: response field can vary by SDK version.
            value = data.get(key)  # WHY: inspect one candidate.
            if isinstance(value, str) and value:  # WHY: only text IDs are valid.
                return value  # WHY: caller can use this ID.
        return ""  # WHY: caller handles missing text.

    def _upgrade_row(self, request: LifecycleRequest, poll: UpgradePollResult) -> dict[str, object]:
        """Build the CSV row for an upgrade poll result."""
        status = STATUS_TIMEOUT if poll.timed_out else STATUS_SENT  # WHY: timeout has its own outcome.
        detail = f"upgrade_id={poll.upgrade_id} status={poll.status} polls={poll.poll_count}"  # WHY: concise result.
        return request.as_row(self.org_id, status, detail)  # WHY: reuse row schema.

    def _confirmed(self, request: LifecycleRequest) -> bool:
        """Return True only when the operator types the exact confirmation word."""
        logger.info("Mist Edge lifecycle step %s targets %s", request.step, request.target_summary)  # WHY: safe target.
        answer = self._ask(f"Type {request.confirmation_word} to proceed: ", request.step).strip()  # WHY: guard.
        matched = answer == request.confirmation_word  # WHY: exact uppercase word required.
        logger.debug("Mist Edge lifecycle confirmation matched=%s for step=%s", matched, request.step)  # WHY: result.
        return matched  # WHY: caller gates the API call.

    @staticmethod
    def _ask(prompt: str, context: str) -> str:
        """Read one EOF-safe answer from the operator."""
        return InputUtils.safe_input(prompt, context=context)  # WHY: shared helper handles SSH/container EOF.

    def _ask_ids(self, prompt: str, context: str) -> list[str]:
        """Read a comma-separated identifier list."""
        answer = self._ask(prompt, context)  # WHY: shared prompt helper.
        values = [part.strip() for part in answer.split(",") if part.strip()]  # WHY: remove accidental blanks.
        if not values:  # WHY: stop before later prompts when targets are absent.
            field_name = "ports" if "ports" in context else "mxedge_ids"  # WHY: name the field that failed.
            raise ValueError(f"{field_name} must contain at least one value")  # WHY: match model validation wording.
        return values  # WHY: request builders still validate the cleaned identifiers.

    def _ask_dry_run(self) -> bool:
        """Return True when the operator chooses dry-run."""
        if self.default_dry_run:  # WHY: the shared CLI --dry-run flag must force preview mode.
            return True  # WHY: no destructive request can run when the global preview flag is set.
        answer = self._ask("Dry run only? (y/N): ", "mxedge_lifecycle_dry_run").strip().lower()  # WHY: preview flag.
        return answer in {"y", "yes"}  # WHY: default is live only after confirmation.

    def _write_row(self, row: dict[str, object]) -> None:
        """Append one row to `MxEdgeLifecycleLog.csv`."""
        logger.info("Writing Mist Edge lifecycle row to %s", self.csv_path)  # WHY: action log before file write.
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)  # WHY: data directory may not exist in tests.
        write_header = not self.csv_path.exists()  # WHY: first write needs CSV headers.
        with self.csv_path.open("a", newline="", encoding="utf-8") as handle:  # WHY: append one evidence row.
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDNAMES)  # WHY: stable column order.
            if write_header:  # WHY: create a readable CSV on first write.
                writer.writeheader()  # WHY: header row documents the schema.
            writer.writerow(row)  # WHY: persist the lifecycle evidence.
        logger.debug("Mist Edge lifecycle row write finished for step=%s", row.get("step"))  # WHY: result summary.

    @staticmethod
    def _safe_body(request: LifecycleRequest) -> dict[str, Any]:
        """Return a request body that is safe to print."""
        if request.step != "claim":  # WHY: only the claim body contains a secret.
            return dict(request.body)  # WHY: copy prevents accidental mutation.
        safe = dict(request.body)  # WHY: redact a copy for display.
        safe["code"] = "REDACTED"  # WHY: claim codes must never appear in output.
        return safe  # WHY: dry-run can show body shape safely.

    @staticmethod
    def _detail(data: dict[str, Any]) -> str:
        """Return a short redacted detail string for a response."""
        status = data.get("status") or data.get("state") or "accepted"  # WHY: prefer API status when present.
        return str(status)[:200]  # WHY: keep CSV detail bounded.
