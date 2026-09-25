"""Walk the cascade phases of one multi-site upgrade.

Why:
    Issue #3245. The single-site driver sends every device family in one step.
    Then it runs one settle gate for each phase, in the order gateways,
    switches, access points, and wireless clients. This module gives a
    multi-site operation the same watch.

    The watch reads the cloud, and it writes the operation record only. It
    sends no firmware write. A watch that starts again after a restart
    therefore cannot upgrade a device a second time.

    The capture portal runs one Gunicorn worker process. The single-site driver
    keeps its run threads in that process, and the registry below keeps one
    watch thread for each operation in the same way.
"""

from __future__ import annotations

import functools
import logging
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar, Final

from src.upgrade_portal.runtime.lock import MAX_LOCK_LIFE_SECONDS
from src.upgrade_portal.runtime.runs import PHASE_ORDER, PhaseState
from src.upgrade_portal.upgrade import driver, events, gate, phase_gate
from src.upgrade_portal.upgrade.driver import CLIENT_PHASE, PhaseOutcome
from src.upgrade_portal.upgrade.org_cascade.close import OrgCascadeClose
from src.upgrade_portal.upgrade.org_cascade.readers import BudgetSleep, OrgStatisticsReader
from src.upgrade_portal.upgrade.org_cascade.record import (
    FAILED_NOTE,
    FINAL_WATCH_STATES,
    PHASE_ENDED_STATES,
    RUNNING_NOTE,
    SUBMISSION_OPEN_STATES,
    WAITING_FOR_START_NOTE,
    WATCH_KEY,
    OrgPhaseEntries,
    OrgPhaseStore,
    OrgPhaseTargets,
    OrgPhaseWatch,
    PhaseTargetSet,
    WatchState,
)
from src.upgrade_portal.upgrade.org_postcheck import PostCheckTaker

logger = logging.getLogger(__name__)  # One logger for the phase watch thread.

# WHY: FR-010. The walk reads the cancellation between two slices of the start
# wait, so a cancelled schedule stops the watch within one poll interval.
START_SLICE_SECONDS: Final[int] = gate.POLL_INTERVAL_SECONDS  # The same interval as the single-site poll.

# WHY: The option parser refuses a start time past the site lock life. This
# bound on the start wait therefore never cuts a real schedule short.
START_WAIT_SLICES: Final[int] = MAX_LOCK_LIFE_SECONDS // START_SLICE_SECONDS + 1  # One more slice for the rest.


@dataclass(frozen=True, slots=True)
class OrgCascadeDeps:
    """Everything that one phase watch needs from outside itself.

    Attributes:
        store: The run store with ``read_run`` and ``compare_and_set_run``.
        session: The cloud session of the operator. The watch reads with it and never writes.
        clock: The clock in epoch seconds. A test passes a fake clock.
        sleep: The wait. A test passes a callable that moves the fake clock.
        deadline_seconds: The time limit of one phase.
        post_check: The seam that takes the post-check capture of one site, or None (issue #3244).
    """

    store: Any  # The durable record of the operation lives in this store.
    session: Any  # The watch reads the cloud with this session and never writes.
    clock: Callable[[], float] = time.time  # A test passes a fake clock.
    sleep: Callable[[float], None] = time.sleep  # A test moves the fake clock instead of a real wait.
    deadline_seconds: int = phase_gate.PHASE_DEADLINE_SECONDS  # The single-site time limit of one phase.
    post_check: PostCheckTaker | None = None  # Last member, so every existing keyword call still builds.


class OrgPhaseGates:
    """Build the settle gate of each phase of one walk.

    Why:
        The single-site wiring builds one event reader for the whole run. The
        walk does the same, so the failure events of an early phase stay in the
        event window of a later phase. Each phase gets its own statistics
        reader, because FR-015 narrows each read to one device family.
    """

    def __init__(self, deps: OrgCascadeDeps, org_id: str, stop_requested: Callable[[str], bool]) -> None:
        """Keep the collaborators of every gate of one walk.

        Args:
            deps: The store, the session, the clock, the sleep, and the deadline.
            org_id: The organization of the operation.
            stop_requested: The reader of the cancellation request.
        """
        self._deps = deps  # The session, the clock, the sleep, and the deadline.
        self._org_id = org_id  # Both readers narrow to this organization.
        self._stop_requested = stop_requested  # The gate reads the cancellation after each round.
        catalogue = events.EventCatalogue()  # The holder of the reconnect event keys. It reads at the first poll.
        self._events = phase_gate.CloudReconnectReader(deps.session, org_id, catalogue, deps.clock)  # One window.

    def build(self, chosen: PhaseTargetSet) -> phase_gate.PhaseSettleGate:
        """Return the settle gate of one phase.

        Args:
            chosen: The followed devices of the phase. The set holds at least one device.

        Returns:
            The gate that waits for the devices of this phase.
        """
        family = str(chosen.targets[0].get("device_type") or "")  # One phase holds one device family.
        reader = OrgStatisticsReader(self._deps.session, self._org_id, family, chosen.site_ids)  # FR-015.
        gate_deps = phase_gate.PhaseGateDeps(
            event_reader=self._events,  # The reconnect signal of every phase.
            statistics_reader=reader,  # The uptime and the version of this phase only.
            settle_gate=gate.SettleGate(clock=self._deps.clock),  # One clock for the deadline and each device.
            sleep=BudgetSleep(reader, self._deps.sleep),  # FR-016: a long read stretches the wait.
            stop_requested=self._stop_requested,  # FR-011: a cancellation ends the wait early.
        )
        return phase_gate.PhaseSettleGate(gate_deps, self._deps.deadline_seconds)  # The single-site gate.


class OrgCascade:
    """Walk the four phases of one multi-site operation in the cascade order."""

    def __init__(self, deps: OrgCascadeDeps, operation_id: str) -> None:
        """Keep the collaborators and the key of one operation.

        Args:
            deps: The store, the session, the clock, the sleep, and the deadline.
            operation_id: The key of the operation record.
        """
        self._deps = deps  # Every outside collaborator of the walk.
        self._operation_id = operation_id  # The key of the operation record.
        self._records = OrgPhaseStore(deps.store, operation_id, self._now_text)  # FR-014: bounded writes.
        self._close = OrgCascadeClose(self._records, deps.post_check, operation_id)  # Issue #3244: captures first.

    def run(self) -> str:
        """Walk every phase that has not ended, and return the final watch state.

        Returns:
            The watch state after the walk: finished, stopped, or a state that an earlier walk wrote.
        """
        logger.info("org cascade: start the phase watch of %s", self._operation_id)  # Before the first read.
        record = self._records.read()  # The durable record decides where the walk starts.
        state = OrgPhaseWatch.state_of(record or {})  # FR-012: a final watch never runs again.
        if record is None or state in FINAL_WATCH_STATES:  # No record, or an earlier walk ended the watch.
            logger.info(  # After the read. The watch has no work to do.
                "org cascade: the watch of %s has no work in state %s", self._operation_id, state
            )
            return state  # The caller logs the state and ends the thread.
        gates = OrgPhaseGates(self._deps, str(record.get("org_id", "")), self._stop_signal)  # One event window.
        if not self._wait_for_start():  # FR-010: a scheduled upgrade starts later.
            return self._close.stop()  # The operator cancelled the schedule.
        self._write_watch(WatchState.RUNNING, RUNNING_NOTE, None)  # The page shows the active watch.
        for name in PHASE_ORDER:  # FR-005: the fixed cascade order.
            if not self._run_phase(name, gates):  # A cancellation stops the walk at once.
                return self._close.stop()  # The page shows the stopped watch.
        return self._close.finish()  # Every phase ended.

    def fail(self) -> None:
        """Write the failed watch state after an internal error, and never raise."""
        logger.info("org cascade: write the failed watch state of %s", self._operation_id)  # Before the write.
        try:  # A fault in the store must not keep the thread alive.
            self._records.update(  # The page then shows the failed watch.
                functools.partial(OrgCascadeClose.end, state=WatchState.FAILED, note=FAILED_NOTE)
            )
        except Exception as error:  # Keep broad: the thread must end even when the store fails.
            logger.error(  # After the failed write. The record keeps the last state.
                "org cascade: the failed state of %s did not write (%s)", self._operation_id, error
            )
            return  # The next poll finds the running state and starts a new walk.
        logger.debug("org cascade: wrote the failed watch state of %s", self._operation_id)  # After the write.

    def _wait_for_start(self) -> bool:
        """Wait until the scheduled start time, and read the cancellation between two slices.

        Returns:
            True when the start time arrived, and False when the operator cancelled.
        """
        announced = False  # The waiting state is written one time.
        for _ in range(START_WAIT_SLICES):  # A bounded loop. The option parser caps the schedule.
            record = self._records.read() or {}  # A cancellation arrives through the record.
            if OrgCascade._stop_requested(record):  # FR-011: the operator cancelled the schedule.
                return False  # The caller writes the stopped state.
            remaining = self._seconds_to_start(record)  # Zero or less means the upgrade started.
            if remaining <= 0:  # The start time arrived, or the upgrade starts at once.
                return True  # The first phase starts now.
            announced = announced or self._announce_start(record)  # Show the start time one time.
            self._deps.sleep(min(float(START_SLICE_SECONDS), remaining))  # No cloud read before the start.
        return True  # The bound passed, so the first phase starts. The gate then waits as usual.

    def _seconds_to_start(self, record: Mapping[str, Any]) -> float:
        """Return the seconds until the scheduled start, or zero for an immediate start."""
        moment = OrgPhaseTargets.start_moment(record)  # The start time of the accepted child jobs.
        return float(moment) - self._deps.clock() if moment is not None else 0.0  # None means an immediate start.

    def _announce_start(self, record: Mapping[str, Any]) -> bool:
        """Write the waiting state with the start time, and return True."""
        moment = OrgPhaseTargets.start_moment(record) or 0  # The caller checked that a start time exists.
        start = datetime.fromtimestamp(moment, tz=UTC).strftime("%Y-%m-%d %H:%M UTC")  # A readable time.
        self._write_watch(  # The page shows the scheduled start time.
            WatchState.WAITING_FOR_START, WAITING_FOR_START_NOTE.format(start=start), None
        )
        logger.info(  # After the write.
            "org cascade: the watch of %s waits for the start at %s", self._operation_id, start
        )
        return True  # The caller stores the flag, so the write happens one time.

    def _run_phase(self, name: str, gates: OrgPhaseGates) -> bool:
        """Run one phase, and return False when the operator cancelled.

        Args:
            name: The phase name.
            gates: The gate builder of this walk.

        Returns:
            True when the walk continues with the next phase.
        """
        record = self._records.read() or {}  # Read the record again before each phase.
        if OrgPhaseEntries.entry(record, name)["state"] in PHASE_ENDED_STATES:  # FR-013: the resume rule.
            logger.info("org cascade: keep the ended %s phase of %s", name, self._operation_id)  # No new wait.
            return True  # A resumed walk continues with the next phase.
        if OrgCascade._stop_requested(record):  # FR-011: the operator cancelled.
            return False  # The caller writes the stopped state.
        outcome = self._decide(record, name, gates)  # The verdict of this phase, or None after a cancellation.
        if outcome is None:  # The operator cancelled while the gate waited.
            return False  # The caller writes the stopped state.
        self._records.update(functools.partial(OrgPhaseEntries.put, entry=self._entry_of(outcome)))  # One write.
        logger.info(  # After the write of the phase entry.
            "org cascade: the %s phase of %s ended as %s", name, self._operation_id, outcome.state
        )
        return True  # The walk continues.

    def _entry_of(self, outcome: PhaseOutcome) -> dict[str, Any]:
        """Return the stored entry of one phase outcome."""
        return OrgPhaseEntries.from_outcome(outcome, self._now_text())  # The single-site entry shape.

    def _decide(self, record: Mapping[str, Any], name: str, gates: OrgPhaseGates) -> PhaseOutcome | None:
        """Return the verdict of one phase, and wait for its devices when it holds any.

        Args:
            record: The durable record before the phase.
            name: The phase name.
            gates: The gate builder of this walk.

        Returns:
            The outcome, or None when the operator cancelled during the wait.
        """
        if name == CLIENT_PHASE:  # The client phase holds no device.
            return OrgCascade._client_outcome(record)  # The single-site client gate rule.
        chosen = OrgPhaseTargets.collect(record, name)  # The followed devices and the excluded count.
        if not chosen.targets and not chosen.excluded:  # FR-008: the operation holds no device of this family.
            return PhaseOutcome(name, PhaseState.SKIPPED.value)  # The single-site skip.
        if not chosen.targets:  # FR-006: the cloud accepted no device of this phase.
            return OrgPhaseEntries.with_exclusions(  # The phase fails, and the note names the excluded count.
                PhaseOutcome(name, PhaseState.FAILED.value), chosen.excluded
            )
        return self._settle(name, chosen, gates)  # Wait for the devices of this phase.

    @staticmethod
    def _client_outcome(record: Mapping[str, Any]) -> PhaseOutcome:
        """Return the client phase verdict with the single-site rule.

        Why:
            The single-site driver settles the client phase at once when one
            access point came back, and it fails the phase with no note when
            none came back. ``OrgPhaseEntries.first_failure`` then names the
            shut gate, as the single-site run reason does.
        """
        if driver.client_gate_open(OrgPhaseEntries.of(record)):  # One access point returned, or none existed.
            return PhaseOutcome(CLIENT_PHASE, PhaseState.SETTLED.value)  # The single-site empty outcome.
        logger.warning("org cascade: no access point returned, so the client phase failed")  # The shut gate.
        return PhaseOutcome(CLIENT_PHASE, PhaseState.FAILED.value)  # The single-site shape has no note.

    def _settle(self, name: str, chosen: PhaseTargetSet, gates: OrgPhaseGates) -> PhaseOutcome | None:
        """Write the waiting entry, wait for the devices, and add the excluded devices.

        Args:
            name: The phase name.
            chosen: The followed devices of the phase.
            gates: The gate builder of this walk.

        Returns:
            The outcome, or None when the operator cancelled during the wait.
        """
        waiting = OrgPhaseEntries.waiting(name, len(chosen.targets))  # The page shows the active phase.
        self._records.update(functools.partial(OrgPhaseEntries.put, entry=waiting))  # One write before the wait.
        logger.info("org cascade: wait for %d device(s) of the %s phase", len(chosen.targets), name)  # Before.
        outcome = gates.build(chosen).settle(self._operation_id, name, chosen.targets)  # Blocks up to 30 minutes.
        logger.debug("org cascade: the gate of the %s phase returned %s", name, outcome.state)  # After the wait.
        if OrgCascade._stop_requested(self._records.read() or {}):  # The gate returns early after a cancellation.
            return None  # The caller writes the stopped state.
        return OrgPhaseEntries.with_exclusions(outcome, chosen.excluded)  # FR-006: name the refused devices.

    def _stop_signal(self, run_id: str) -> bool:
        """Return True when the operator requested the cancellation. The gate calls this reader."""
        del run_id  # The walk knows its own operation key.
        return OrgCascade._stop_requested(self._records.read() or {})  # Read the durable request.

    @staticmethod
    def _stop_requested(record: Mapping[str, Any]) -> bool:
        """Return True when the record holds a cancellation request."""
        cancellation = record.get("cancellation")  # The cancel route sets requested to True.
        return isinstance(cancellation, Mapping) and cancellation.get("requested") is True  # A strict check.

    def _write_watch(self, state: WatchState, note: str, reason: str | None) -> None:
        """Write one watch state through the bounded compare-and-set."""
        self._records.update(  # One write. A conflict reads the record again.
            functools.partial(OrgPhaseWatch.set_state, state=state, note=note, reason=reason)
        )

    def _now_text(self) -> str:
        """Return the present time of the walk clock as UTC ISO text."""
        return datetime.fromtimestamp(self._deps.clock(), tz=UTC).isoformat()  # The single-site text shape.


class OrgCascadeRegistry:
    """Keep one watch thread for each operation in this process."""

    _threads: ClassVar[dict[str, threading.Thread]] = {}  # The live thread of each operation.
    _guard: ClassVar[threading.Lock] = threading.Lock()  # The request threads call at the same time.

    @staticmethod
    def may_run(record: Mapping[str, Any]) -> bool:
        """Return True when a watch thread may start for one record.

        Args:
            record: The durable operation record.

        Returns:
            True when the record holds a watch that has work to do.
        """
        if not isinstance(record.get(WATCH_KEY), Mapping):  # A record of an earlier release holds no anchors.
            return False  # A watch with no anchors would report a false failure.
        if OrgPhaseWatch.state_of(record) in FINAL_WATCH_STATES:  # FR-012: a final watch never runs again.
            return False  # The page keeps the final verdict.
        if str(record.get("state", "")) in SUBMISSION_OPEN_STATES:  # The submission still writes the child jobs.
            return False  # The exclusion count is not final yet.
        return OrgPhaseTargets.accepted_count(record) > 0  # FR-005: the watch needs an accepted child job.

    @classmethod
    def ensure_running(cls, record: Mapping[str, Any], deps: OrgCascadeDeps) -> bool:
        """Start the watch thread of one operation when none runs.

        Args:
            record: The durable operation record.
            deps: The collaborators of the walk.

        Returns:
            True when this call started a thread.
        """
        operation_id = str(record.get("operation_id") or "")  # The key of the thread.
        if not operation_id or not cls.may_run(record):  # FR-005 and FR-012 decide.
            return False  # No thread starts.
        with cls._guard:  # Two polls can arrive at the same time.
            if cls._alive(operation_id):  # FR-012: one thread for each operation.
                return False  # The live thread keeps the watch.
            thread = threading.Thread(
                target=cls._run, args=(deps, operation_id), name=f"org-cascade-{operation_id[-8:]}", daemon=True
            )  # A daemon thread never blocks the shutdown of the server.
            cls._threads[operation_id] = thread  # Record the thread before it starts.
            thread.start()  # The walk runs outside the request.
        logger.info("org cascade: started the watch thread of %s", operation_id)  # After the start.
        return True  # The caller logs the result.

    @classmethod
    def _alive(cls, operation_id: str) -> bool:
        """Return True when a live thread watches one operation. The caller holds the guard."""
        thread = cls._threads.get(operation_id)  # The last thread of this operation.
        return thread is not None and thread.is_alive()  # A finished thread does not count.

    @classmethod
    def _run(cls, deps: OrgCascadeDeps, operation_id: str) -> None:
        """Run one walk, and write the failed state after an internal error."""
        walk = OrgCascade(deps, operation_id)  # One walk for the life of this thread.
        try:  # The guard makes sure that the thread always ends.
            state = walk.run()  # Blocks until every phase ended or the operator cancelled.
            logger.info("org cascade: the watch thread of %s ended in state %s", operation_id, state)  # After.
        except Exception:  # Keep broad: a fault must end with a state that the page shows.
            logger.exception(  # After the fault. The portal log keeps the traceback.
                "org cascade: the watch of %s stopped after an internal error", operation_id
            )
            walk.fail()  # FR-004: the page shows the failed watch.
        finally:
            cls._forget(operation_id)  # A later poll may start a new thread.

    @classmethod
    def _forget(cls, operation_id: str) -> None:
        """Remove the entry of the current thread."""
        with cls._guard:  # The request threads read the same map.
            if cls._threads.get(operation_id) is threading.current_thread():  # Remove this thread only.
                del cls._threads[operation_id]  # The entry of a newer thread stays.
