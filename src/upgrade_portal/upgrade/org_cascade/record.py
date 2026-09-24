"""The durable phase record of one multi-site upgrade.

Why:
    Issue #3245. A single-site run record holds four cascade phases, and one
    settle gate decides each phase. The multi-site record now holds the same
    four entries, in the same shape. This module collects the devices of one
    phase from the child jobs, builds each entry, and writes each change
    through the compare-and-set of the run store.

    The watch never adds a key to ``child["targets"]``. The retry path rebuilds
    ``DeviceTarget(**target)`` from each stored entry, so a new key there
    breaks a later retry. The anchors therefore live in a separate map.
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Callable, Mapping, MutableMapping
from copy import deepcopy
from enum import StrEnum
from typing import Any, Final

from src.upgrade_portal.capture.devices import normalize_device_mac
from src.upgrade_portal.runtime.runs import PHASE_ORDER, PhaseState, RunRecordBuilder
from src.upgrade_portal.upgrade import driver
from src.upgrade_portal.upgrade.driver import AP_PHASE, CLIENT_GATE_SHUT_REASON, CLIENT_PHASE, PhaseOutcome

logger = logging.getLogger(__name__)  # One logger for the record fields of the phase watch.

PHASES_KEY: Final[str] = "phases"  # The four phase entries, in the single-site shape.
WATCH_KEY: Final[str] = "phase_watch"  # The state and the note of the watch thread.
ANCHORS_KEY: Final[str] = "settle_anchors"  # The uptime and the last report time of each device before the write.
CAS_ATTEMPTS: Final[int] = 5  # FR-014: a conflict causes a new read and a new try, up to five tries.

# WHY: FR-006. A child job in one of these states never reached the cloud, or
# the cloud refused it. No device of that child job can upgrade, so the watch
# must not wait 30 minutes for it.
EXCLUDED_CHILD_STATES: Final[frozenset[str]] = frozenset(  # No device of these child jobs can upgrade.
    {"planned", "not_submitted", "rejected"}
)

# WHY: A child job in one of these operation states can still change. The
# exclusion count of each phase is final only after the submission ends.
SUBMISSION_OPEN_STATES: Final[frozenset[str]] = frozenset(  # The submission still writes the child jobs.
    {"planned", "submission_claimed"}
)

# WHY: A resumed watch keeps each phase that holds one of these states, and it
# continues with the first phase that holds none of them.
PHASE_ENDED_STATES: Final[frozenset[str]] = frozenset(  # A resumed watch does not wait for these phases again.
    {PhaseState.SETTLED.value, PhaseState.SKIPPED.value, PhaseState.FAILED.value}
)

# WHY: The single-site driver writes a settle time for these two states only.
PHASE_COMPLETE_STATES: Final[frozenset[str]] = frozenset(  # Only these two states get a settle time.
    {PhaseState.SETTLED.value, PhaseState.SKIPPED.value}
)

# WHY: The single-site page uses these labels. One map keeps both pages equal.
PHASE_LABELS: Final[Mapping[str, str]] = {  # The page label of each phase name.
    "gateways": "Gateways",
    "switches": "Switches",
    "aps": "Access points",
    "clients": "Wireless clients",
}


class WatchState(StrEnum):
    """Every state that the watch of one operation can hold (FR-004)."""

    NOT_STARTED = "not_started"  # The submission stored the watch, and no thread ran yet.
    WAITING_FOR_START = "waiting_for_start"  # The thread waits for the scheduled start time.
    RUNNING = "running"  # The thread follows the phases in the cascade order.
    FINISHED = "finished"  # Every phase ended.
    STOPPED = "stopped"  # The operator cancelled the operation.
    FAILED = "failed"  # An internal error stopped the thread.


# WHY: FR-012. No call starts a thread for a watch in one of these states.
FINAL_WATCH_STATES: Final[frozenset[str]] = frozenset(  # The page keeps these verdicts.
    {WatchState.FINISHED.value, WatchState.STOPPED.value, WatchState.FAILED.value}
)

# WHY: The page shows one sentence for each watch state. The notes live here,
# so the walk and the view use the same words.
NOT_STARTED_NOTE: Final[str] = (  # The note before the first thread runs.
    "The portal starts the phase watch after the cloud accepts a child job."
)
NO_CHILD_NOTE: Final[str] = (  # The note when the cloud accepted no child job.
    "The cloud accepted no child job, so the portal watches no phase."
)
WAITING_FOR_START_NOTE: Final[str] = (  # The note while the thread waits for the start time.
    "The upgrade starts at {start}. The portal watches the first phase after that time."
)
RUNNING_NOTE: Final[str] = "The portal watches each phase in the cascade order."  # The note of a running thread.
FINISHED_NOTE: Final[str] = "Every phase ended."  # The note when no phase failed.
STOPPED_NOTE: Final[str] = (  # The note after a cancellation.
    "The operator requested the cancellation, so the portal stopped the phase watch."
)
FAILED_NOTE: Final[str] = (  # The note after an internal error.
    "The phase watch stopped after an internal error. Read the portal log."
)


@dataclasses.dataclass(frozen=True, slots=True)
class PhaseTargetSet:
    """Hold the devices of one phase that the watch follows.

    Attributes:
        targets: One gate entry for each device of an accepted child job.
        excluded: The count of devices of this phase that the cloud did not accept.
        site_ids: The sites of the followed devices, in sorted order.
    """

    targets: tuple[Mapping[str, Any], ...]  # The gate entries of the followed devices.
    excluded: int  # The devices whose child job never reached the cloud or met a refusal.
    site_ids: tuple[str, ...]  # The read scope of the phase.


class OrgPhaseTargets:
    """Collect the devices of one phase from the child jobs of one operation."""

    @staticmethod
    def collect(record: Mapping[str, Any], phase: str) -> PhaseTargetSet:
        """Return the followed devices and the excluded count of one phase.

        Args:
            record: The durable operation record.
            phase: The phase name, one of the members of PHASE_ORDER.

        Returns:
            The followed devices, the excluded count, and the sites.
        """
        anchors = OrgPhaseTargets._anchors(record)  # The map of the anchors that the submission read.
        watched: list[Mapping[str, Any]] = []  # The devices that the gate follows.
        excluded = 0  # The devices that the cloud did not accept.
        for child in OrgPhaseTargets.children(record):  # Keep the plan order of the child jobs.
            rows = OrgPhaseTargets._child_rows(child, anchors)  # The gate entries of this child job.
            matched = driver.phase_targets({"targets": rows}, phase)  # The single-site family filter.
            if OrgPhaseTargets.excluded(child):  # FR-006: the cloud did not accept this child job.
                excluded += len(matched)  # Count the devices, so the phase note can name them.
                continue  # The gate does not wait for a device that cannot upgrade.
            watched.extend(matched)  # Follow each device of an accepted child job.
        sites = sorted({str(row.get("site_id") or "") for row in watched} - {""})  # FR-015: the read scope.
        return PhaseTargetSet(tuple(watched), excluded, tuple(sites))  # One immutable answer.

    @staticmethod
    def excluded(child: Mapping[str, Any]) -> bool:
        """Return True when the cloud did not accept one child job (FR-006).

        Args:
            child: One durable child job.

        Returns:
            True when no device of the child job can upgrade.
        """
        return str(child.get("status", "")).strip().lower() in EXCLUDED_CHILD_STATES  # The stored child state.

    @staticmethod
    def accepted_count(record: Mapping[str, Any]) -> int:
        """Return the count of child jobs that can hold a device upgrade.

        Args:
            record: The durable operation record.

        Returns:
            The count of child jobs whose state is not excluded.
        """
        children = OrgPhaseTargets.children(record)  # The valid child jobs, in the plan order.
        return sum(1 for child in children if not OrgPhaseTargets.excluded(child))  # FR-005: the start rule.

    @staticmethod
    def start_moment(record: Mapping[str, Any]) -> int | None:
        """Return the latest start time of the accepted child jobs.

        Why:
            FR-010. A scheduled upgrade does not start at the submission. Every
            child job holds the same start time, and the latest value is the
            safe choice if a damaged record holds two values.

        Args:
            record: The durable operation record.

        Returns:
            The start time in epoch seconds, or None when no child job holds one.
        """
        moments: list[int] = []  # One start time for each accepted child job that holds one.
        for child in OrgPhaseTargets.children(record):  # Read each child body.
            body = child.get("body") if isinstance(child.get("body"), Mapping) else {}  # A damaged child has none.
            value = body.get("start_time")  # The cloud field that schedules the upgrade.
            if type(value) is int and value > 0 and not OrgPhaseTargets.excluded(child):  # A real schedule.
                moments.append(value)  # Keep the value of an accepted child job only.
        return max(moments) if moments else None  # None means an immediate start.

    @staticmethod
    def children(record: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        """Return the valid child rows of one record, in the plan order.

        Args:
            record: The durable operation record.

        Returns:
            Each child job that is a mapping.
        """
        children = record.get("children")  # The durable child jobs of the operation.
        return (  # Drop each damaged entry. A damaged list reads as no child job.
            [child for child in children if isinstance(child, Mapping)] if isinstance(children, list) else []
        )

    @staticmethod
    def _anchors(record: Mapping[str, Any]) -> Mapping[str, Any]:
        """Return the stored anchor map, or an empty map for a damaged record."""
        anchors = record.get(ANCHORS_KEY)  # FR-001: the submission stored the map.
        return anchors if isinstance(anchors, Mapping) else {}  # FR-002: no map means null anchors.

    @staticmethod
    def _child_rows(child: Mapping[str, Any], anchors: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Return one gate entry for each target of one child job.

        Why:
            FR-009. The gate reads ``reboot_at`` from each entry, and the
            aggregate record stores that time on the child job.

        Args:
            child: One durable child job.
            anchors: The anchor map of the operation.

        Returns:
            One detached entry for each valid target.
        """
        reboot_at = child.get("reboot_at")  # Epoch seconds of a delayed reboot, or absent.
        rows: list[dict[str, Any]] = []  # The detached gate entries.
        for target in child.get("targets") or ():  # Keep the stored target order.
            if not isinstance(target, Mapping):  # A damaged entry cannot name a device.
                continue  # The other devices still reach the gate.
            row = dict(target)  # Detach the entry, so the stored child does not change.
            anchor = anchors.get(normalize_device_mac(row.get("mac")) or "")  # The anchors of this device.
            known = anchor if isinstance(anchor, Mapping) else {}  # FR-002: a missing anchor reads as null.
            row["uptime_before"] = known.get("uptime_before")  # The gate compares the uptime after the reboot.
            row["last_seen_before"] = known.get("last_seen_before")  # The absolute anchor of the gate.
            if type(reboot_at) is int and reboot_at > 0:  # A delayed reboot moves the phase deadline.
                row["reboot_at"] = reboot_at  # The gate waits for the scheduled reboot.
            rows.append(row)  # Keep this device.
        return rows  # The entries of this child job.


class OrgPhaseEntries:
    """Build and change the four phase entries of one operation."""

    @staticmethod
    def of(record: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Return the four entries in the fixed order, with a pending entry for each gap.

        Args:
            record: The durable operation record.

        Returns:
            Four detached entries in the order gateways, switches, aps, clients.
        """
        stored = record.get(PHASES_KEY)  # The entries that the watch wrote.
        rows = stored if isinstance(stored, list) else []  # A record without entries reads as pending.
        by_name = {str(row.get("name", "")): row for row in rows if isinstance(row, Mapping)}  # Look up by name.
        pending = {str(row["name"]): row for row in RunRecordBuilder.initial_phases()}  # The single-site shape.
        return [dict(by_name.get(name) or pending[name]) for name in PHASE_ORDER]  # Keep the fixed order.

    @staticmethod
    def entry(record: Mapping[str, Any], name: str) -> dict[str, Any]:
        """Return the entry of one phase.

        Args:
            record: The durable operation record.
            name: The phase name.

        Returns:
            The detached entry of the phase.
        """
        return next(row for row in OrgPhaseEntries.of(record) if row["name"] == name)  # Each name exists once.

    @staticmethod
    def waiting(name: str, total: int) -> dict[str, Any]:
        """Return the entry of a phase that the gate now watches.

        Why:
            The multi-site record holds no run state such as
            ``settling_switches``. The state ``waiting`` therefore names the
            phase that the watch follows now.

        Args:
            name: The phase name.
            total: The count of devices that the gate follows.

        Returns:
            One entry in the single-site shape.
        """
        return {
            "name": name,  # The phase name of the contract.
            "state": PhaseState.WAITING.value,  # The gate now follows this phase.
            "settled": 0,  # No device returned yet.
            "total": total,  # The count of devices that the gate follows.
            "settled_at": None,  # The phase did not end.
            "note": "",  # No fault yet.
            "failures": [],  # No failure event yet.
        }

    @staticmethod
    def from_outcome(outcome: PhaseOutcome, now_text: str) -> dict[str, Any]:
        """Return the entry of one phase that ended.

        Args:
            outcome: What the gate or the walk reported.
            now_text: The present time as UTC ISO text.

        Returns:
            One entry in the single-site shape.
        """
        settled_at = now_text if outcome.state in PHASE_COMPLETE_STATES else None  # The single-site rule.
        return {
            "name": outcome.name,  # The phase name of the contract.
            "state": outcome.state,  # The verdict of the phase.
            "settled": outcome.settled,  # The count of devices that returned.
            "total": outcome.total,  # The count of devices of the phase.
            "settled_at": settled_at,  # The end time of a complete phase only.
            "note": outcome.note,  # The cause that the gate or the walk named.
            "failures": [{"mac": mac, "reason": reason} for mac, reason in outcome.failures],  # Event failures.
        }

    @staticmethod
    def put(record: MutableMapping[str, Any], entry: Mapping[str, Any]) -> None:
        """Put one phase entry into a record in place.

        Args:
            record: The candidate record of one compare-and-set write.
            entry: The new entry. Its name selects the entry to change.
        """
        name = str(entry.get("name", ""))  # The phase to change.
        record[PHASES_KEY] = [  # Replace the entry of this phase, and keep the fixed order.
            dict(entry) if row["name"] == name else row for row in OrgPhaseEntries.of(record)
        ]

    @staticmethod
    def reset_waiting(record: MutableMapping[str, Any]) -> None:
        """Put each waiting entry of a candidate record back to the pending entry.

        Args:
            record: The candidate record of one compare-and-set write.
        """
        pending = {str(row["name"]): row for row in RunRecordBuilder.initial_phases()}  # The single-site shape.
        waiting = PhaseState.WAITING.value  # The state that a live gate wait writes.
        rows = OrgPhaseEntries.of(record)  # The four entries in the fixed order.
        record[PHASES_KEY] = [  # A waiting entry goes back to pending. Every other entry stays.
            pending[row["name"]] if row.get("state") == waiting else row for row in rows
        ]

    @staticmethod
    def with_exclusions(outcome: PhaseOutcome, excluded: int) -> PhaseOutcome:
        """Return the outcome of a phase that holds devices that the cloud did not accept.

        Why:
            US2 scenario 4. A single-site phase fails when a device does not
            upgrade. The multi-site phase gives the same verdict at once for a
            device whose child job the cloud refused, and it names the count.

        Args:
            outcome: What the gate reported for the accepted devices.
            excluded: The count of devices that the cloud did not accept.

        Returns:
            The same outcome when no device was excluded, or a failed outcome.
        """
        if excluded <= 0:  # Every device of the phase reached the cloud.
            return outcome  # Keep the verdict of the gate.
        note = f"The cloud did not accept the upgrade of {excluded} device(s) of this phase."  # Name the count.
        joined = f"{outcome.note} {note}".strip()  # Keep the note of the gate first.
        return dataclasses.replace(  # The phase fails, and the total counts the excluded devices.
            outcome, state=PhaseState.FAILED.value, total=outcome.total + excluded, note=joined
        )

    @staticmethod
    def first_failure(record: Mapping[str, Any]) -> str | None:
        """Return the reason of the first phase that failed, in the fixed order.

        Why:
            FR-007. The single-site driver keeps the first failure, because it
            is the root cause of each later failure.

        Args:
            record: The durable operation record.

        Returns:
            The reason text, or None when no phase failed.
        """
        failed = [  # The failed entries, in the fixed cascade order.
            row for row in OrgPhaseEntries.of(record) if row.get("state") == PhaseState.FAILED.value
        ]
        if not failed:  # Every phase settled, skipped, or still waits.
            return None  # The watch names no failure.
        row = failed[0]  # The first failure in the fixed order is the root cause.
        if row["name"] == CLIENT_PHASE:  # The client phase fails only when its gate stays shut.
            return CLIENT_GATE_SHUT_REASON  # The single-site driver returns this sentence with no prefix.
        note = str(row.get("note") or "")  # The cause that the gate or the walk named.
        missing = max(int(row.get("total") or 0) - int(row.get("settled") or 0), 0)  # Devices not back.
        detail = note or f"{missing} device(s) did not return before the phase limit."  # The single-site text.
        label = "access point" if row["name"] == AP_PHASE else row["name"]  # The single-site label.
        return f"The {label} phase failed. {detail}"  # The single-site sentence.

    @staticmethod
    def active_label(record: Mapping[str, Any]) -> str | None:
        """Return the label of the phase that the watch follows now (FR-019).

        Args:
            record: The durable operation record.

        Returns:
            The label, or None when no phase waits.
        """
        rows = [  # The waiting entries. The walk keeps one at a time.
            row for row in OrgPhaseEntries.of(record) if row.get("state") == PhaseState.WAITING.value
        ]
        return PHASE_LABELS.get(str(rows[0]["name"])) if rows else None  # One phase waits at a time.


class OrgPhaseStore:
    """Write the phase fields of one operation through the compare-and-set of the store."""

    def __init__(self, store: Any, operation_id: str, now_text: Callable[[], str]) -> None:
        """Keep the store, the operation, and the clock of the watch.

        Args:
            store: The run store with ``read_run`` and ``compare_and_set_run``.
            operation_id: The key of the operation record.
            now_text: The clock that returns the present time as UTC ISO text.
        """
        self._store = store  # The durable store that every route also uses.
        self._operation_id = operation_id  # The key of the record.
        self._now_text = now_text  # One clock for each write.

    def read(self) -> dict[str, Any] | None:
        """Return a detached copy of the current record, or None when it is absent.

        Returns:
            The detached record, or None.
        """
        current = self._store.read_run(self._operation_id)  # The store decides the current version.
        return deepcopy(dict(current)) if isinstance(current, Mapping) else None  # Detach the stored record.

    def update(self, mutate: Callable[[MutableMapping[str, Any]], None]) -> dict[str, Any] | None:
        """Apply one change through a bounded compare-and-set (FR-014).

        Args:
            mutate: The change. It edits the candidate record in place.

        Returns:
            The stored record, or None when the record is absent or every try failed.
        """
        for attempt in range(1, CAS_ATTEMPTS + 1):  # Bound the retries against another writer.
            current = self.read()  # Read the current version before each try.
            expected = current.get("record_version") if current is not None else None  # The version to match.
            if current is None or type(expected) is not int:  # A missing or damaged record cannot take a write.
                logger.error(  # A missing or damaged record cannot take the change.
                    "org cascade: the operation %s holds no writable record", self._operation_id
                )
                return None  # The walk stops its write, and the page keeps the last value.
            candidate = deepcopy(current)  # Keep a failed try detached.
            mutate(candidate)  # Apply the change to the fresh copy only.
            if candidate == current:  # The record already holds the change.
                return current  # Write nothing, so the version and the update time stay.
            if self._write(candidate, expected):  # One atomic write.
                return candidate  # The record now holds the change.
            logger.debug(  # After the conflict. The loop reads the record again.
                "org cascade: write try %d for %s met a conflict", attempt, self._operation_id
            )
        logger.warning("org cascade: every write try for %s met a conflict", self._operation_id)  # FR-014.
        return None  # The next write of the watch tries again.

    def _write(self, candidate: MutableMapping[str, Any], expected: int) -> bool:
        """Write one candidate record, and return True when the store took it."""
        candidate["updated_at"] = self._now_text()  # The progress page shows the age of the last change.
        candidate["record_version"] = expected + 1  # Advance exactly one version.
        return bool(self._store.compare_and_set_run(self._operation_id, expected, dict(candidate)))  # Atomic write.


class OrgPhaseWatch:
    """Build and change the watch fields of one operation."""

    @staticmethod
    def state_of(record: Mapping[str, Any]) -> str:
        """Return the watch state of one record.

        Args:
            record: The durable operation record.

        Returns:
            The stored watch state, or ``not_started`` when the record holds none.
        """
        watch = record.get(WATCH_KEY)  # The watch fields that the submission stored.
        stored = watch.get("state") if isinstance(watch, Mapping) else None  # A damaged field holds no state.
        return str(stored) if stored else WatchState.NOT_STARTED.value  # A missing state reads as not started.

    @staticmethod
    def prepared(record: Mapping[str, Any], anchors: Mapping[str, Any], note: str) -> dict[str, Any]:
        """Return a copy of the record with the anchors, the phases, and the watch state.

        Args:
            record: The durable operation record before the submission.
            anchors: The anchor map, keyed by the normalized device address.
            note: The anchor gap note, or empty text when every read answered.

        Returns:
            A detached replacement record for one compare-and-set write.
        """
        watch = {  # FR-004: the watch starts after the cloud accepts a child job.
            "state": WatchState.NOT_STARTED.value,  # No thread runs yet.
            "note": NOT_STARTED_NOTE,  # The page explains the wait for the cloud answer.
            "reason": None,  # No phase failed yet.
            "anchor_note": note,  # FR-002: every later watch write keeps this gap note.
        }
        return {
            **deepcopy(dict(record)),  # Keep every field of the plan.
            ANCHORS_KEY: dict(anchors),  # FR-001: the anchors before the first write.
            PHASES_KEY: RunRecordBuilder.initial_phases(),  # FR-003: four pending entries.
            WATCH_KEY: watch,  # FR-004: the first watch state.
        }

    @staticmethod
    def set_state(record: MutableMapping[str, Any], state: WatchState, note: str, reason: str | None) -> None:
        """Change the watch state of a candidate record, and keep the anchor gap note.

        Args:
            record: The candidate record of one compare-and-set write.
            state: The new watch state.
            note: The sentence that the page shows for the state.
            reason: The first failure reason, or None.
        """
        current = record.get(WATCH_KEY)  # The watch fields that an earlier write stored.
        kept = current if isinstance(current, Mapping) else {}  # A damaged field keeps nothing.
        record[WATCH_KEY] = {**kept, "state": state.value, "note": note, "reason": reason}  # Keep anchor_note.
