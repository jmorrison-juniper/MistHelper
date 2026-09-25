"""Stand-ins for the two phase watch seams of the multi-site routes (issue #3245).

Why:
    The route layer reads the settle anchors before the first firmware write.
    It starts one watch thread after the cloud accepts a child job. A contract
    test and a browser test must reach no cloud and must start no thread. The
    stand-ins in this module answer both seams.

Scope:
    ``CascadeSeamStandIn`` records each call and changes no record.
    ``ScriptedCascadeStarter`` moves the watch of one operation one step for
    each call, so a browser journey sees each phase end. It writes through the
    production record helpers, so the page reads the production record shape.
    Issue #3244: it ends the watch through the production close, so a browser
    journey also sees the post-check capture of each site.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Mapping, MutableMapping
from datetime import UTC, datetime
from typing import Any

from src.upgrade_portal.app.routes.org_upgrade import ANCHOR_READER_CONFIG_KEY, CASCADE_STARTER_CONFIG_KEY
from src.upgrade_portal.runtime.runs import PhaseState
from src.upgrade_portal.upgrade.driver import CLIENT_PHASE, PhaseOutcome
from src.upgrade_portal.upgrade.org_cascade.close import OrgCascadeClose
from src.upgrade_portal.upgrade.org_cascade.readers import AnchorRead
from src.upgrade_portal.upgrade.org_cascade.record import (
    FINAL_WATCH_STATES,
    RUNNING_NOTE,
    OrgPhaseEntries,
    OrgPhaseStore,
    OrgPhaseTargets,
    OrgPhaseWatch,
    WatchState,
)
from src.upgrade_portal.upgrade.org_cascade.walk import OrgCascadeRegistry

logger = logging.getLogger(__name__)  # The seam logs under this module.
OPEN_PHASE_STATES = frozenset({PhaseState.WAITING.value, PhaseState.PENDING.value})  # A phase that still has work.


class CascadeSeamStandIn:
    """Answer the anchor seam and the starter seam, and record each call.

    Attributes:
        anchor_reads: The operation key of each anchor read, in order.
        starts: The operation key of each start call, in order.
    """

    def __init__(self, anchors: Mapping[str, Mapping[str, Any]] | None = None, note: str = "") -> None:
        """Keep the fixed anchor answer.

        Args:
            anchors: The anchors of each device, keyed by the normalized address.
            note: The anchor gap note of the answer.
        """
        self.anchor_reads: list[str] = []  # The contract tests read the order of the calls.
        self.starts: list[str] = []  # The contract tests read the order of the calls.
        self._anchors = {mac: dict(value) for mac, value in (anchors or {}).items()}  # A detached answer.
        self._note = note  # The gap note that the submission stores.

    def install(self, config: MutableMapping[str, Any]) -> CascadeSeamStandIn:
        """Put both seams into the configuration of one application.

        Args:
            config: The configuration of the Flask application.

        Returns:
            This stand-in, so a fixture keeps one handle.
        """
        config[ANCHOR_READER_CONFIG_KEY] = self.read_anchors  # The submission reads no cloud.
        config[CASCADE_STARTER_CONFIG_KEY] = self.start  # No request starts a thread.
        return self  # The fixture reads the recorded calls later.

    def read_anchors(self, cloud_session: Any, record: Mapping[str, Any]) -> AnchorRead:
        """Record one anchor read, and return the fixed answer.

        Args:
            cloud_session: The cloud session. The stand-in opens no socket.
            record: The operation record before the submission.

        Returns:
            A detached copy of the fixed anchors and the gap note.
        """
        del cloud_session  # The stand-in opens no socket.
        self.anchor_reads.append(str(record.get("operation_id", "")))  # One entry for each read.
        return AnchorRead(
            {mac: dict(value) for mac, value in self._anchors.items()}, self._note
        )  # The caller receives copies.

    def start(self, record: Mapping[str, Any], deps: Any) -> bool:
        """Record one start call, and start no thread.

        Args:
            record: The operation record.
            deps: The collaborators of the walk. The stand-in reads none of them.

        Returns:
            False, because the stand-in starts no thread.
        """
        del deps  # The stand-in starts no walk.
        self.starts.append(str(record.get("operation_id", "")))  # One entry for each call.
        return False  # The route logs this result.


class ScriptedCascadeStarter:
    """Move the phase watch of each operation one step for each call.

    Why:
        A browser journey cannot wait for a real settle gate. The page load and
        each status poll call the starter one time. Each call ends the phase
        that waits, and it moves the next phase to the waiting state. When no
        phase has work left, the call ends the watch through the production
        close, so the post-check stage runs and the poll stops. A cancellation
        request stops the watch through the same close, as the real walk does.

    Attributes:
        calls: The operation key of each call, in order.
    """

    def __init__(self) -> None:
        """Start with no call."""
        self.calls: list[str] = []  # The journey reads the count of calls.
        self._guard = threading.Lock()  # Two request threads can call at the same time.

    def __call__(self, record: Mapping[str, Any], deps: Any) -> bool:
        """Move the watch of one operation one step.

        Args:
            record: The operation record of the request.
            deps: The collaborators of the walk. The starter reads the store and the post-check seam.

        Returns:
            False, because the starter starts no thread.
        """
        operation_id = str(record.get("operation_id") or "")  # The key of the record.
        with self._guard:  # One step at a time for each process.
            self.calls.append(operation_id)  # Record the call before the decision.
            if not OrgCascadeRegistry.may_run(record):  # The production rule decides.
                return False  # A final watch or an open submission takes no step.
            records = OrgPhaseStore(deps.store, operation_id, ScriptedCascadeStarter._now_text)  # The bounded writer.
            stored = records.update(ScriptedCascadeStarter._advance)  # The store writes one step.
            ScriptedCascadeStarter._close(stored, records, deps, operation_id)  # Issue #3244: the production close.
        logger.debug("scripted cascade: moved the watch of %s one step", operation_id)  # After the write.
        return False  # No thread started.

    @staticmethod
    def _advance(candidate: MutableMapping[str, Any]) -> None:
        """Take one step on a candidate record in place."""
        if OrgPhaseWatch.state_of(candidate) in FINAL_WATCH_STATES:  # A stale request found an ended watch.
            return  # Change nothing.
        if ScriptedCascadeStarter._cancelled(candidate):  # The operator cancelled.
            return  # The close stops the watch after this step.
        for row in OrgPhaseEntries.of(candidate):  # End the phase that waits now.
            if row["state"] == PhaseState.WAITING.value:  # One phase waits at a time.
                OrgPhaseEntries.put(
                    candidate, ScriptedCascadeStarter._ended(candidate, str(row["name"]))
                )  # The waiting phase ends.
        ScriptedCascadeStarter._next(candidate)  # Start the next phase, when one is pending.

    @staticmethod
    def _close(stored: Mapping[str, Any] | None, records: OrgPhaseStore, deps: Any, operation_id: str) -> None:
        """End the watch through the production close when the script has no step left.

        Args:
            stored: The record after the step, or None when the write failed.
            records: The bounded writer of the operation record.
            deps: The collaborators of the walk. The close reads the post-check seam.
            operation_id: The key of the operation record.
        """
        if stored is None or OrgPhaseWatch.state_of(stored) in FINAL_WATCH_STATES:  # No open watch to end.
            return  # The next call reads the record again.
        close = OrgCascadeClose(records, getattr(deps, "post_check", None), operation_id)  # The production close.
        if ScriptedCascadeStarter._cancelled(stored):  # FR-002: a stop takes the captures too.
            close.stop()  # The captures, then the stopped state.
            return  # The watch ended.
        if not {str(row["state"]) for row in OrgPhaseEntries.of(stored)} & OPEN_PHASE_STATES:  # Every phase ended.
            close.finish()  # FR-001: the captures, then the finished state.

    @staticmethod
    def _cancelled(record: Mapping[str, Any]) -> bool:
        """Return True when the cancel route asked the watch to stop."""
        cancellation = record.get("cancellation")  # The cancel route sets requested to True.
        return isinstance(cancellation, Mapping) and cancellation.get("requested") is True  # The request.

    @staticmethod
    def _next(candidate: MutableMapping[str, Any]) -> None:
        """Move the first pending phase to the waiting state, when one exists."""
        pending = [
            row for row in OrgPhaseEntries.of(candidate) if row["state"] == PhaseState.PENDING.value
        ]  # Pending phases can start.
        if not pending:  # Every phase ended.
            return  # The close ends the watch.
        name = str(pending[0]["name"])  # The next phase in the fixed order.
        total = len(OrgPhaseTargets.collect(candidate, name).targets)  # The devices of the phase.
        OrgPhaseEntries.put(candidate, OrgPhaseEntries.waiting(name, total))  # The page shows the wait.
        OrgPhaseWatch.set_state(candidate, WatchState.RUNNING, RUNNING_NOTE, None)  # The real running note.

    @staticmethod
    def _ended(candidate: Mapping[str, Any], name: str) -> dict[str, Any]:
        """Return the entry of one phase that ended with every device back."""
        chosen = OrgPhaseTargets.collect(candidate, name)  # The followed and the excluded devices.
        count = len(chosen.targets)  # Every followed device returns in the script.
        state = (
            PhaseState.SETTLED.value if count or name == CLIENT_PHASE else PhaseState.SKIPPED.value
        )  # Empty phases skip.
        outcome = OrgPhaseEntries.with_exclusions(
            PhaseOutcome(name, state, count, count), chosen.excluded
        )  # The result keeps exclusions.
        return OrgPhaseEntries.from_outcome(outcome, ScriptedCascadeStarter._now_text())  # The real entry shape.

    @staticmethod
    def _now_text() -> str:
        """Return the present time as UTC ISO text."""
        return datetime.now(tz=UTC).isoformat()  # The shape of the production clock text.
