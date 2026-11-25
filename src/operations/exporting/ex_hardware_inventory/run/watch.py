"""Wait for one running batch and read its results from the run folder.

Why:
    The portal batch service runs the shells on worker threads and keeps its
    results in memory and in a private run folder. The CLI has no browser to poll
    it, so these two helpers poll the service until the batch ends, stop it when
    the operator presses Ctrl+C, and read each target outcome and each saved XML
    reply. The CLI reads the folder only through the paths that the service
    itself recorded, and it checks that each path stays inside the run folder.
"""

from __future__ import annotations

import logging  # Record each wait and each read for the operator trace.
import time  # The poll loop sleeps between reads and keeps a deadline.
from collections.abc import Mapping  # The batch rows are read-only mappings.
from typing import TYPE_CHECKING, Any, cast  # The stack type is only needed for annotations.

from src.operations.exporting.ex_hardware_inventory.report.builder import TargetResult  # One result for each target.

if TYPE_CHECKING:  # Avoid a runtime import cycle with the batch module.
    from src.operations.exporting.ex_hardware_inventory.run.batch import BatchStack  # The services of one organization.

logger = logging.getLogger(__name__)  # Name the logger after this module so log lines carry their source.


class BatchWatcher:
    """Poll one batch until it ends, and stop it when the operator presses Ctrl+C."""

    POLL_SECONDS = 0.5  # The service keeps its state in memory, so a short poll costs nothing.
    SECONDS_PER_TURN = 120  # One target needs at most this long: shell open, prompt wait, and one command.
    STOP_SECONDS = 60  # After a stop, the open shells close within this time.

    def __init__(self, stack: BatchStack, session_id: str) -> None:
        """Store the services and the batch session.

        Args:
            stack: The batch services of the organization.
            session_id: The public identifier of the batch session.
        """
        self._stack = stack  # The service and the manager.
        self._session_id = session_id  # The batch to poll and to stop.

    def wait(self, target_count: int) -> bool:
        """Wait until the batch and its output are final.

        Args:
            target_count: The number of targets in the batch. It sets the longest wait.

        Returns:
            True when the batch was stopped, by the operator or by the longest wait.
        """
        logger.info("Waiting for the batch of %d targets", target_count)  # Log before the wait.
        turns = -(-target_count // self._stack.concurrency) + 1  # Rounds of shells, plus one for the final write.
        deadline = time.monotonic() + self.SECONDS_PER_TURN * turns  # A hung batch cannot hold the CLI forever.
        stopped = False  # No stop was requested yet.
        while time.monotonic() < deadline:  # Poll until the batch is final or the time is gone.
            try:  # Ctrl+C stops the batch, and the loop then waits for the shells to close.
                if self._final():  # The artifact status shows that every target ended.
                    logger.debug("The batch is final. stopped=%s", stopped)  # Log the result.
                    return stopped  # The caller reads the results.
                time.sleep(self.POLL_SECONDS)  # Give the worker threads time.
            except KeyboardInterrupt:  # The operator wants to stop.
                if stopped:  # A second Ctrl+C: stop waiting at once.
                    return True  # Read whatever exists.
                self._stack.manager.stop(self._session_id)  # Stop queued targets and close open shells.
                stopped = True  # Remember that the run is partial.
                deadline = min(deadline, time.monotonic() + self.STOP_SECONDS)  # Open shells close quickly.
        logger.warning("The batch did not finish in time. It is stopped.")  # The longest wait is over.
        self._stack.manager.stop(self._session_id)  # Do not leave shells open.
        return True  # The run is partial.

    def _final(self) -> bool:
        """Return True when every target ended and the run folder is closed."""
        batch = self._stack.service.summary(self._session_id).get("batch")  # The in-memory batch summary.
        if not isinstance(batch, dict):  # The service always builds this mapping for a batch session.
            return False  # Keep polling until the longest wait ends.
        done = {"completed", "failed", "stopped", "partial"}  # The target states of a finished batch.
        return batch.get("artifact_status") in {"ready", "failed"} and batch.get("status") in done  # Final.


class RunFolder:
    """Read the outcome and the saved reply of each target of one finished batch."""

    PAGE = 500  # The service clamps one page of targets to this many rows.
    FINAL = frozenset({"completed", "failed", "skipped", "stopped"})  # The states that cannot change again.
    MAX_BYTES = 1_048_576  # The writer never saves a reply above this size.

    def __init__(self, stack: BatchStack, org_name: str) -> None:
        """Store the services and the organization name.

        Args:
            stack: The batch services of the organization.
            org_name: The organization name for the report rows.
        """
        self._stack = stack  # The service and the run folder root.
        self._org_name = org_name  # The batch identity holds the organization identifier only.

    def collect(self, session_id: str, cancelled: bool) -> tuple[str, tuple[TargetResult, ...]]:
        """Read every target outcome and every saved reply.

        Args:
            session_id: The public identifier of the batch session.
            cancelled: True when the batch was stopped before it ended by itself.

        Returns:
            The run folder name and one result for each target, in the batch order.
        """
        logger.info("Reading the outcomes of the batch")  # Log before the reads.
        batch = self._stack.service.summary(session_id).get("batch")  # The summary holds the run folder name.
        run_id = str(batch.get("run_id") or "") if isinstance(batch, dict) else ""  # An empty name reads no file.
        results = tuple(self._result(run_id, row, cancelled) for row in self._rows(session_id))  # One each.
        logger.debug("Read %d target outcomes", len(results))  # Log the count.
        return run_id, results  # Hand them to the report builder.

    def _rows(self, session_id: str) -> list[dict[str, Any]]:
        """Read every page of target rows in batch order."""
        rows: list[dict[str, Any]] = []  # The rows of every page.
        after = 0  # The cursor of the first page.
        while True:  # Follow the cursor until the last page.
            page = self._stack.service.targets(session_id, after, self.PAGE)  # One bounded page.
            found = cast(list[dict[str, Any]], page["targets"])  # The service builds a list of mappings.
            rows.extend(found)  # Keep the rows in batch order.
            if page["complete"] or not found:  # The last page, or a page that gives no progress.
                return rows  # Every row.
            after = cast(int, page["next_after"])  # The cursor of the next page.

    def _result(self, run_id: str, row: Mapping[str, Any], cancelled: bool) -> TargetResult:
        """Build one target result, and give a target that never ended a final state."""
        state, reason = str(row["state"]), str(row.get("reason_code") or "")  # What the batch recorded.
        if state not in self.FINAL:  # A queued or running target after a stop or a timeout.
            state, reason = ("stopped", "cancelled") if cancelled else ("failed", "target_failed")  # Final.
        xml_text = self._xml(run_id, row) if state == "completed" else None  # Only a collected target has a reply.
        return TargetResult(row["target"], self._org_name, state, reason, xml_text)  # One result.

    def _xml(self, run_id: str, row: Mapping[str, Any]) -> str | None:
        """Read the saved XML reply of one target, or None when it is missing or not safe to read."""
        names = [str(name) for name in row.get("files") or [] if str(name).endswith(".xml")]  # One XML file.
        if not run_id or not names:  # Nothing was saved.
            return None  # The report shows that the reply is missing.
        base = (self._stack.root / run_id).resolve()  # The run folder, with links resolved.
        path = (base / names[0]).resolve()  # An absolute name, a parent step, or a link resolves outside the folder.
        try:  # A missing or unreadable file gives no reply.
            if base not in path.parents or path.stat().st_size > self.MAX_BYTES:  # Inside the folder and small.
                return None  # Refuse a path outside the folder and an oversized file.
            return path.read_bytes().decode("utf-8")  # Exact bytes, so the CRLF of the switch stays.
        except (OSError, UnicodeDecodeError):  # The file is gone, is not a file, or is not UTF-8.
            return None  # The report shows that the reply is missing.
