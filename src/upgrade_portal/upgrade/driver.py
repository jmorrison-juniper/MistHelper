"""Drive one upgrade run from the submission to the post-check capture.

Why:
    One long-lived thread owns one run. No other thread writes the run
    record. Two threads that wrote the same record under multi-user load
    would leave a record that no operator can explain. The driver reads the
    record back before each write and keeps the `stop_request` field, which
    the route thread owns, so the two threads never fight over one field.

    The cascade order is fixed: gateways, then switches, then access points,
    then wireless clients. Everything sits downstream of the gateways. The
    access points and the wired clients sit downstream of the switches. Only
    the wireless clients sit downstream of the access points. A phase starts
    only after the phase before it reports settled.

    The settle gate, the event reader, and the option builder live in sibling
    modules that other lanes write at the same time. This module names the
    shape it needs as a protocol and takes the object as a dependency, so it
    imports cleanly today and a test injects a double.

    The site lock lives 300 seconds. The browser alone renewed it before this
    module took a heartbeat, so an operator who closed the page during a
    40-minute cascade lost the site after five minutes, and a second operator
    could take a site that was still writing firmware to a switch. The run
    thread now renews the lock as well, at every wait the driver performs and
    at every poll round of the settle gate. The heartbeat starts no thread,
    because a second thread would be a second failure mode.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar, Final, Protocol

from src.upgrade_portal.runtime.lock import (
    HEARTBEAT_SECONDS,
    LockRecord,
    LockStoreUnreachableError,
    ReleaseOutcome,
    SiteLockError,
    build_key,
    refresh_site_lock,
    release_site_lock,
)
from src.upgrade_portal.runtime.runs import PHASE_ORDER, PhaseState, RunState, RunStateMachine, RunTransitionError
from src.upgrade_portal.runtime.signals import RunRecordStore

__all__ = [
    "AP_PHASE",
    "CLIENT_PHASE",
    "DATA_DIRECTORY_NAME",
    "DEFAULT_POST_CHECK_MODE",
    "LOCK_FIELD",
    "LOCK_LOST_REASON",
    "LOCK_RETRY_WINDOW_SECONDS",
    "LOCK_STATE_LOST",
    "LOCK_STORE_QUIET_REASON",
    "POST_CHECK_AUTOMATIC",
    "POST_CHECK_MANUAL",
    "POST_CHECK_ORDINAL",
    "POST_CHECK_ROLE",
    "TARGET_STATE_NOT_RETURNED",
    "TRACKER_FILENAME",
    "CaptureStarter",
    "Clock",
    "LockHeartbeat",
    "LockHeartbeatPlan",
    "LockRefresher",
    "LockReleaser",
    "PhaseGate",
    "PhaseOutcome",
    "ProgressSink",
    "RunDriver",
    "RunDriverDeps",
    "RunDriverError",
    "SystemClock",
    "UpgradeSubmitter",
    "client_gate_open",
    "data_root",
    "lock_heartbeat",
    "mark_not_returned",
    "not_returned_count",
    "phase_partly_settled",
    "phase_targets",
    "post_check_request",
    "settling_state",
    "tracker_path",
    "write_tracker",
]

logger = logging.getLogger(__name__)

# WHY: The pre-check capture takes ordinal 1, so the post-check takes 2. The
# capture module derives the role from the ordinal, and this module writes both
# values, so a reader of the request never has to derive one from the other.
POST_CHECK_ORDINAL: Final[int] = 2
POST_CHECK_ROLE: Final[str] = "post"

# WHY: The customer chose the automatic capture for today and asked for a manual
# switch under the hood. These two names are that switch. The default stays
# automatic, so a portal with no setting behaves as it behaves today. The seam
# adds no run state and no route, so a later change back is one line.
POST_CHECK_AUTOMATIC: Final[str] = "automatic"
POST_CHECK_MANUAL: Final[str] = "manual"
DEFAULT_POST_CHECK_MODE: Final[str] = POST_CHECK_AUTOMATIC

# WHY: The client phase counts wireless clients and holds no device target, so
# the empty-family skip of FR-058 never applies to it.
CLIENT_PHASE: Final[str] = "clients"
AP_PHASE: Final[str] = "aps"

# WHY: src/firmware/firmware_manager.py line 3713 writes this file under the
# bare name, so the file follows the process working directory. A run started
# from one directory then loses the tracker of a run started from another. This
# module resolves every tracker path from the module file instead.
TRACKER_FILENAME: Final[str] = "ActiveUpgrades.json"
DATA_DIRECTORY_NAME: Final[str] = "data"

# WHY: The driver names the step that failed, so the operator reads where the
# run stopped and not only that it stopped.
STAGE_UPGRADE: Final[str] = "upgrade"
STAGE_POST_CAPTURE: Final[str] = "post_capture"

# WHY: The run record reaches ArangoDB, the CSV backup, and the browser. A
# fault of the cloud library, of Redis, or of ArangoDB carries the connection
# string of its own client. The message of such a fault must never reach that
# record. The portal writes the message of every fault it defines itself.
FOREIGN_FAULT_REASON: Final[str] = "The run stopped after the fault {name}."

# WHY: A fault class that this package defines carries a message that the
# portal wrote by hand. No module of this package builds a message from the
# text of a caught fault. A class of the standard library gives no such
# promise, because a foreign library raises the same classes.
PORTAL_PACKAGE: Final[str] = "src.upgrade_portal."

# WHY: A fault of this package names its own step in plain words. The driver
# reads that text to pick the stage, and it reads no other message.
POST_CHECK_MARK: Final[str] = "post-check"

# WHY: A run that counted no wireless client must end failed, because the site
# never reported the clients. The sentence carries no "post-check" text, so
# `_fail` names the upgrade stage. The upgrade lost the access points, and the
# capture itself ran well, so the operator must not chase the capture path.
CLIENT_GATE_SHUT_REASON: Final[str] = "No access point returned, so the portal did not count the wireless clients."

# WHY: A skipped phase counts as complete for the gate that follows it. FR-058
# asks the portal to pass over an empty family and open the next gate.
_PHASE_COMPLETE: Final[frozenset[str]] = frozenset(
    {PhaseState.SETTLED.value, PhaseState.SKIPPED.value},
)

# WHY: A phase that reached its time limit reports this state, at
# src/upgrade_portal/upgrade/phase_gate.py line 748. The driver reads the state
# to tell a wait that ended from a wait that still runs, because a phase that
# still waits also holds a settled count below its total and must never open
# the gate below it.
_PHASE_TIMED_OUT: Final[str] = PhaseState.FAILED.value

# WHY: FR-047 asks the portal to mark a device that passed the time limit. The
# name comes from the target state list of data-model.md section 4.2, which
# already holds a member for a device that did not come back healthy. The
# portal reuses that member and mints no sixth name.
TARGET_STATE_NOT_RETURNED: Final[str] = "failed"

# WHY: The `device_type` value of a target names the family. The client phase
# holds no device, so it takes no entry here.
_PHASE_DEVICE_TYPES: Final[Mapping[str, str]] = {
    "gateways": "gateway",
    "switches": "switch",
    "aps": "ap",
}

# WHY: contracts/site-lock.md line 137 gives a heartbeat 60 seconds to reach a
# lock store that does not answer. The driver retries inside that window and
# gives up after it, so a dead store never holds the run thread for ever.
LOCK_RETRY_WINDOW_SECONDS: Final[int] = 60

# WHY: The run record names the state of the site lock. A reader of the run then
# learns that the site changed hands while the upgrade ran. The run itself
# continues. A takeover never cancels a running upgrade, and firmware already in
# flight cannot be recalled.
LOCK_FIELD: Final[str] = "lock"
LOCK_STATE_LOST: Final[str] = "lost"

# WHY: Two sentences name the two ways a beat fails. Neither sentence holds the
# lock token or a work email address, so both are safe in a log record and in
# the run record that the progress page reads.
#
# Both sentences state twice that the work continues. A lost lock stops the
# portal from writing to the site. It does not stop the upgrade, because the
# cloud already holds the order and firmware already in flight cannot be
# recalled. An operator who reads the loss alone walks away, and the devices
# then reboot hours later with nothing to explain the reboot. The second
# sentence of each pair prevents that outcome.
#
# Neither sentence names a cause. A beat learns that the lock is gone, and it
# cannot tell a takeover from an expiry, so a named cause could be false.
LOCK_LOST_REASON: Final[str] = (
    "This run no longer holds the site lock. The upgrade continues in the cloud, and the devices still reboot."
)
LOCK_STORE_QUIET_REASON: Final[str] = (
    "The portal cannot reach the lock store, so this run no longer holds the site lock. "
    "The upgrade continues in the cloud, and the devices still reboot."
)


class RunDriverError(RuntimeError):
    """Raised when the driver cannot carry one run further.

    Why:
        A run that fails silently leaves the operator with a page that never
        changes. The driver raises with one plain sentence, catches the error
        at the top of the thread, and writes the sentence into the record.
    """


class Clock(Protocol):
    """The one time reading the driver needs.

    Why:
        A test must never sleep. The driver takes the clock as a dependency,
        so a test injects a clock that returns fixed text and the test reads
        the stored times without a wait.
    """

    def now_text(self) -> str:
        """Return the present time as ISO 8601 text in UTC.

        Returns:
            The time stamp the driver writes into the run record.
        """
        ...  # A protocol declares the shape only


class SystemClock:
    """Read the wall clock of this computer.

    Why:
        The production path needs a real clock. This class holds the only
        call to the system time in the module, so a test replaces one object
        and reaches every time stamp.
    """

    def now_text(self) -> str:
        """Return the present time as ISO 8601 text in UTC.

        Returns:
            The present time, always with a time zone.
        """
        return datetime.now(tz=UTC).isoformat()


@dataclass(frozen=True, slots=True)
class PhaseOutcome:
    """What one settle gate reports for one phase of a run.

    Why:
        The settle gate lives in a sibling module that another lane writes at
        the same time. This record fixes the answer shape, so the driver
        depends on the shape and never on the module.

    Attributes:
        name: The phase name. One of the four members of PHASE_ORDER.
        state: The phase state. One of the PhaseState values.
        settled: How many members of the phase returned.
        total: How many members the phase holds.
        not_returned: The address of each member that never came back. Empty
            when the gate reports the counts alone.
        note: One sentence naming what the gate could not read. Empty when
            every read of the last round answered.
    """

    name: str
    state: str = PhaseState.SETTLED.value
    settled: int = 0
    total: int = 0
    not_returned: tuple[str, ...] = ()  # Empty by default, so a gate that reports counts alone still builds one
    note: str = ""  # Empty by default, so a phase that never met a fault names no cause


class PhaseGate(Protocol):
    """The settle gate of one cascade phase.

    Why:
        The gate module and the event module are under work in other lanes.
        The driver calls this shape, so the two lanes proceed at the same
        time and a test injects a double that returns a fixed outcome.
    """

    def settle(self, run_id: str, phase: str, targets: Sequence[Mapping[str, Any]]) -> PhaseOutcome:
        """Wait for one phase to settle and report the result.

        Args:
            run_id: The run key.
            phase: The phase name.
            targets: The target entries of that phase. Empty for clients.

        Returns:
            The outcome of the phase.
        """
        ...  # A protocol declares the shape only


class CaptureStarter(Protocol):
    """The capture path the driver calls for the post-check.

    Why:
        The capture package owns the read of the site. The driver decides
        when the second capture starts and never how it runs.
    """

    def start(self, request: Mapping[str, Any]) -> str | None:
        """Start one capture and return its key.

        Args:
            request: The run key, the ordinal, and the role.

        Returns:
            The capture key, or None when the capture did not start.
        """
        ...  # A protocol declares the shape only


class UpgradeSubmitter(Protocol):
    """The cloud submission the driver calls once for each run.

    Why:
        The submission needs a Mist session and the upgrade plans, which the
        route lane owns. The driver keeps the session out of this module and
        asks only whether the cloud accepted the work.
    """

    def submit(self, record: MutableMapping[str, Any]) -> bool:
        """Send the upgrade to the cloud and record each upgrade identifier.

        Args:
            record: The run record. The method may write the target entries.

        Returns:
            True when the cloud accepted the upgrade.
        """
        ...  # A protocol declares the shape only


class LockRefresher(Protocol):
    """The compare-and-extend call that one heartbeat makes.

    Why:
        `src/upgrade_portal/runtime/lock.py` owns the Redis script. This
        module names the shape it calls, so a test injects a stand-in that
        counts the beats and reaches no store. The shape repeats the real
        signature of `refresh_site_lock`, because a stand-in that is more
        permissive than the real call would hide the very defect the tests
        exist to catch.
    """

    def __call__(self, key: str, record: LockRecord, client: Any = None) -> int:
        """Extend the life of a site lock that the caller still holds.

        Args:
            key: The lock key, from `build_key`.
            record: The lock record the caller holds. Carries the token.
            client: A lock store client. The module opens one by default.

        Returns:
            The seconds the lock now has left.

        Raises:
            SiteLockError: When the lock expired or changed hands.
        """
        ...  # A protocol declares the shape only


class LockReleaser(Protocol):
    """The compare-and-delete call that ends one hold on a site.

    Why:
        `src/upgrade_portal/runtime/lock.py` owns the Redis script. This module
        names the shape it calls, so a test injects a stand-in that records the
        release and reaches no store. The shape repeats the real signature of
        `release_site_lock`, because a stand-in that is more permissive than
        the real call would hide the very defect the tests exist to catch.
    """

    def __call__(self, key: str, record: LockRecord, client: Any = None) -> ReleaseOutcome:
        """Give up a site lock that the caller still holds.

        Args:
            key: The lock key, from `build_key`.
            record: The lock record the caller holds. Carries the token.
            client: A lock store client. The module opens one by default.

        Returns:
            The one outcome that deleted a lock.

        Raises:
            SiteLockError: When the lock expired or changed hands.
        """
        ...  # A protocol declares the shape only


class ProgressSink(Protocol):
    """Anything that takes the counts of one poll round.

    Why:
        `src/upgrade_portal/upgrade/phase_gate.py` calls a progress reporter
        once every poll round, and that module imports this one. This module
        therefore names the shape and imports nothing back, so the two files
        stay free of an import cycle.
    """

    def report(self, progress: Any) -> None:
        """Take the counts of one poll round.

        Args:
            progress: The counts the settle gate reported.
        """
        ...  # A protocol declares the shape only


@dataclass(frozen=True, slots=True)
class LockHeartbeatPlan:
    """Every value one site lock heartbeat needs.

    Why:
        Seven separate parameters would break the parameter limit. This group
        travels as one argument, and every member below the lock record
        carries the default the production path wants, so a caller names the
        key and the record alone.

    Attributes:
        key: The Redis key of the site lock, from `build_key`.
        record: The lock record the portal holds. Carries the token.
        refresh: The compare-and-extend call.
        ticker: Reads a count of seconds that only moves forward.
        interval: The seconds between two beats.
        progress: The reporter that held the seat of the settle gate before
            the heartbeat took it. None when the gate reports nowhere else.
        release: The compare-and-delete call that a final run state makes.
    """

    key: str
    record: LockRecord
    refresh: LockRefresher = refresh_site_lock
    ticker: Callable[[], float] = time.monotonic  # A wall clock that steps back would skip a beat
    interval: int = HEARTBEAT_SECONDS
    progress: ProgressSink | None = None
    release: LockReleaser = release_site_lock


class LockHeartbeat:
    """Renew the site lock of one run for as long as the run is alive.

    Why:
        The site lock lives 300 seconds. Only the browser renewed it before
        this class existed, so an operator who closed the page lost the site
        after five minutes, and a second operator could take a site that was
        still writing firmware to a switch.

        The class holds no thread. Every beat runs on the run thread, at a
        wait the driver already performs and at every poll round of the settle
        gate. A second thread would be a second failure mode.

        Every beat is safe to call at any time. A call inside the interval
        spends no round trip, so a caller adds a beat wherever a wait begins
        and never counts the seconds.

        The application passes this object as the progress reporter of the
        settle gate, so a beat also rides the 20-second poll loop. Without
        that seat the lock still beats at every wait the driver owns, and a
        phase longer than the life of the lock then loses it.
    """

    def __init__(self, plan: LockHeartbeatPlan) -> None:
        """Hold the plan and set the first beat one interval from now.

        Why:
            The lock was fresh when the operator took the site, so the first
            beat waits one whole interval and the run start spends no round
            trip on the lock store.

        Args:
            plan: The key, the lock record, and the calls one beat makes.
        """
        self._plan = plan
        self._due = plan.ticker() + float(plan.interval)  # The first beat waits one whole interval
        self._quiet_since: float | None = None  # Set while the lock store does not answer
        self._stopped = False  # True after a final run state, and after the lock changed hands
        self._sink: Callable[[str], None] | None = None  # The driver writes the loss into the run record

    @property
    def stopped(self) -> bool:
        """Report whether this heartbeat gave up.

        Returns:
            True when the run ended, or when the site lock changed hands.
        """
        return self._stopped

    def watch(self, sink: Callable[[str], None]) -> None:
        """Name the call that records a lost site lock on the run record.

        Why:
            The heartbeat holds no run record and no store. The driver hands
            it one call, so a beat inside a settle gate reaches the record at
            once and the operator does not wait half an hour for the phase to
            end. The driver thread still performs every write.

        Args:
            sink: Takes one plain sentence about the lost lock.
        """
        self._sink = sink

    def stop(self) -> None:
        """Give up every later beat.

        Why:
            A run in a final state needs no lock. A beat after that point
            would hold a site that nobody upgrades, and the next operator
            would wait the full cooldown for nothing.
        """
        self._stopped = True

    def release(self) -> bool:
        """Give the site back at the end of one run.

        Why:
            contracts/site-lock.md line 105 releases the lock when a run reaches
            `complete`, `stopped`, or `failed`. Without the release the next
            operator waits the whole 3600-second life of the lock for a site
            that nobody upgrades. This object holds the key and the token, so
            the release belongs here and the driver never sees the token.

            A run that already ended must not fail because a lock store went
            quiet, so every fault stays inside this method. The log line names
            the class of the fault alone, because the message of a store fault
            can carry a connection string.

        Returns:
            True when the lock store deleted the lock.
        """
        self._stopped = True  # A lock the run gave back must never be renewed
        run_id = self._plan.record.run_id
        try:
            self._plan.release(self._plan.key, self._plan.record)
        except Exception as error:  # noqa: BLE001  # WHY: The run already ended, so no fault may end it again.
            logger.warning("Run %s could not release the site lock (%s)", run_id, type(error).__name__)
            return False
        logger.info("Run %s released the site lock", run_id)
        return True

    def report(self, progress: Any) -> None:
        """Beat for one poll round of the settle gate, then pass the counts on.

        Why:
            The settle gate blocks the run thread for up to half an hour and
            calls this method every 20 seconds. Every third call beats, which
            meets the 60-second interval, so the lock never dies inside one
            phase. The gate holds one reporter seat, so this method passes the
            counts to the reporter that held the seat before.

        Args:
            progress: The counts the settle gate reported.
        """
        self.beat()  # Rate limited, so two rounds of every three spend nothing
        if self._plan.progress is not None:
            self._plan.progress.report(progress)  # The reporter behind this one still gets every round

    def beat(self) -> bool:
        """Renew the site lock when the interval passed.

        Why:
            The caller adds this call at every wait and never counts the
            seconds, so no wait site needs a clock of its own.

        Returns:
            True while the portal still holds the lock. False after the lock
            changed hands, expired, or the run ended.
        """
        if self._stopped:
            return False  # The run ended, or the site already changed hands
        if self._plan.ticker() < self._due:
            return True  # The lock still has life, so this call spends no round trip
        return self._renew()

    def _renew(self) -> bool:
        """Send one compare-and-extend to the lock store.

        Why:
            A beat must never end an upgrade that is writing firmware to a
            switch. Every failure therefore leaves this method as a report and
            never as an exception.

        Returns:
            True while the portal still holds the lock.
        """
        try:
            left = self._plan.refresh(self._plan.key, self._plan.record)
        except LockStoreUnreachableError:
            return self._quiet()  # contracts/site-lock.md line 137 gives the store a retry window
        except SiteLockError:
            return self._lost(LOCK_LOST_REASON)  # A takeover or an expiry moved the lock
        except Exception as error:  # noqa: BLE001  # WHY: A beat must never end a live upgrade.
            return self._lost(f"The portal could not renew the site lock ({type(error).__name__}).")
        return self._held(int(left))

    def _held(self, seconds: int) -> bool:
        """Note one beat that the lock store accepted.

        Why:
            The Redis script behind the refresh call answers 0 when the lock
            changed hands. A count of zero seconds therefore means the same
            thing as the error, and this method reads both as a lost lock.

        Args:
            seconds: The seconds the lock now has left.

        Returns:
            True while the portal still holds the lock.
        """
        if seconds <= 0:
            return self._lost(LOCK_LOST_REASON)  # A store that reports no life left holds no lock
        self._due = self._plan.ticker() + float(self._plan.interval)  # The next beat waits one interval
        self._quiet_since = None  # The store answered, so any earlier outage is over
        logger.info("Run %s renewed the site lock for %s seconds", self._plan.record.run_id, seconds)
        return True

    def _quiet(self) -> bool:
        """Retry a beat that the lock store did not answer.

        Why:
            contracts/site-lock.md line 137 gives the store 60 seconds. The
            next call of the caller is the retry, so the wait costs the run
            thread nothing and needs no sleep.

        Returns:
            True while the retry window is open. False after it closes.
        """
        now = self._plan.ticker()
        if self._quiet_since is None:
            self._quiet_since = now  # The window opens at the first refusal
        self._due = now  # The next call retries at once, inside the window
        if now - self._quiet_since < float(LOCK_RETRY_WINDOW_SECONDS):
            logger.warning("Run %s cannot reach the lock store, so the portal retries", self._plan.record.run_id)
            return True
        return self._lost(LOCK_STORE_QUIET_REASON)

    def _lost(self, reason: str) -> bool:
        """Record that the portal no longer renews this site lock.

        Why:
            A silent loss lets a second operator take a site that is still
            writing firmware, with nothing in the record to explain it. The
            log line and the run record both carry the reason, and neither
            carries the lock token or a work email address.

        Args:
            reason: One plain sentence for the operator.

        Returns:
            Always False, so every path of the caller reads one answer.
        """
        self._stopped = True  # A dead token cannot be renewed, so the portal stops asking
        digest = self._plan.record.owner.email_digest  # The only form of an address a log record may hold
        logger.warning("Run %s lost the site lock of operator %s: %s", self._plan.record.run_id, digest, reason)
        if self._sink is not None:
            self._sink(reason)  # The run record now names the loss, so a reader of the run sees it
        return False


def lock_heartbeat(record: Mapping[str, Any], lock: LockRecord, progress: ProgressSink | None = None) -> LockHeartbeat:
    """Return the site lock heartbeat of one run.

    Why:
        The driver thread holds no request context and cannot read the signed
        session. The run record already carries the organization and the site,
        so the key needs no new channel. The lock record travels as a
        dependency instead, because the run record reaches the store, the
        status body of the progress page, and a log line, and the lock token
        must reach none of the three.

    Args:
        record: The run record.
        lock: The lock record the portal holds for this site.
        progress: The reporter that held the seat of the settle gate before
            the heartbeat took it.

    Returns:
        A heartbeat that renews the site lock of this run.
    """
    key = build_key(str(record.get("org_id", "")), str(record.get("site_id", "")))
    return LockHeartbeat(LockHeartbeatPlan(key=key, record=lock, progress=progress))


@dataclass(frozen=True, slots=True)
class RunDriverDeps:
    """Every collaborator one run driver needs.

    Why:
        Five separate parameters would break the parameter limit and would
        invite a wrong positional order. This group travels as one argument,
        and every member is a protocol, so a test injects a double for each.

    Attributes:
        store: Reads and writes the run record.
        gate: Waits for one cascade phase to settle.
        capture: Starts the post-check capture.
        submit: Sends the upgrade to the cloud. None when the caller already
            sent it.
        clock: Reads the present time.
        heartbeat: Renews the site lock of this run. None when the caller
            holds no lock, and the browser then renews the lock alone.
        post_check_mode: Names who starts the post-check capture. The driver
            starts it under `automatic`, which is the default and the behavior
            of today. An operator starts it under `manual`. Any other text
            counts as automatic.
    """

    store: RunRecordStore
    gate: PhaseGate
    capture: CaptureStarter
    submit: UpgradeSubmitter | None = None
    clock: Clock = field(default_factory=SystemClock)
    heartbeat: LockHeartbeat | None = None  # No member moved, so every existing positional call still builds
    post_check_mode: str = DEFAULT_POST_CHECK_MODE  # Last member, so every existing positional call still builds


def data_root() -> Path:
    """Return the data directory of this repository.

    Why:
        The path comes from the location of this module and never from the
        process working directory. A run started from any directory then
        reaches the same directory.

    Returns:
        The absolute path of the data directory.
    """
    return Path(__file__).resolve().parents[3] / DATA_DIRECTORY_NAME


def tracker_path(filename: str = TRACKER_FILENAME, root: Path | None = None) -> Path:
    """Return the absolute path of one tracker file under the data directory.

    Why:
        A bare file name follows the process working directory, which is the
        defect at src/firmware/firmware_manager.py line 3713. This function
        drops any directory part of the name, so a caller cannot leave the
        data directory.

    Args:
        filename: The tracker file name. Any directory part is dropped.
        root: The data directory. The repository data directory by default.

    Returns:
        The absolute path of the tracker file.
    """
    base = root if root is not None else data_root()
    base.mkdir(parents=True, exist_ok=True)  # The first run of a fresh clone finds no directory
    return base / Path(filename).name  # The name alone, so no caller escapes the data directory


def _read_tracker(path: Path) -> list[dict[str, Any]]:
    """Return the rows the tracker file holds.

    Why:
        A damaged tracker must not stop an upgrade. The reader answers with
        an empty list and writes one warning.

    Args:
        path: The tracker file path.

    Returns:
        Every row of the file. An empty list when the file is absent or bad.
    """
    if not path.exists():
        return []
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.warning("The portal could not read the upgrade tracker at %s", path)
        return []
    return [dict(row) for row in rows if isinstance(row, dict)]


def _tracker_entry(record: Mapping[str, Any], now: str) -> dict[str, Any]:
    """Return the tracker row of one run.

    Args:
        record: The run record.
        now: The present time as ISO 8601 text in UTC.

    Returns:
        The run identifiers and every cloud upgrade identifier of the run.
    """
    targets = record.get("targets", [])
    upgrade_ids = sorted({str(entry.get("upgrade_id")) for entry in targets if entry.get("upgrade_id")})
    return {
        "run_id": str(record.get("run_id", "")),
        "org_id": str(record.get("org_id", "")),
        "site_id": str(record.get("site_id", "")),
        "upgrade_ids": upgrade_ids,
        "updated_at": now,
    }


def write_tracker(record: Mapping[str, Any], now: str, root: Path | None = None) -> Path:
    """Write the active upgrade identifiers of one run under the data directory.

    Why:
        The firmware menu reads this file after a restart to find work that
        is still running. The file must live in one known place, so every
        process finds the same file.

    Args:
        record: The run record.
        now: The present time as ISO 8601 text in UTC.
        root: The data directory. The repository data directory by default.

    Returns:
        The path the driver wrote.
    """
    path = tracker_path(TRACKER_FILENAME, root)
    entry = _tracker_entry(record, now)
    rows = [row for row in _read_tracker(path) if row.get("run_id") != entry["run_id"]]
    rows.append(entry)
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    logger.info("The portal wrote the upgrade tracker for run %s to %s", entry["run_id"], path)
    return path


def settling_state(phase: str) -> RunState:
    """Return the run state that belongs to one cascade phase.

    Args:
        phase: The phase name, one of the members of PHASE_ORDER.

    Returns:
        The settling state of that phase.

    Raises:
        RunDriverError: When the name is not a cascade phase.
    """
    try:
        return RunState(f"settling_{phase}")
    except ValueError as error:
        raise RunDriverError(f"The name {phase} is not a cascade phase.") from error


def phase_targets(record: Mapping[str, Any], phase: str) -> tuple[Mapping[str, Any], ...]:
    """Return every device target of one cascade phase.

    Why:
        FR-058 asks the portal to skip a gate when the site holds no device
        of that family. The driver counts the targets here and skips the
        cloud call, rather than wait for a gate that has nothing to watch.

    Args:
        record: The run record.
        phase: The phase name.

    Returns:
        The matching targets. Always empty for the client phase.
    """
    wanted = _PHASE_DEVICE_TYPES.get(phase)
    if wanted is None:
        return ()
    entries = record.get("targets", [])
    return tuple(entry for entry in entries if str(entry.get("device_type", "")) == wanted)


def _phase_count(entry: Mapping[str, Any], key: str) -> int:
    """Return one count of a phase entry as a whole number.

    Args:
        entry: One phase entry of the run record.
        key: The count to read. Either settled or total.

    Returns:
        The count. Zero when the entry holds no readable number.
    """
    try:
        return int(entry.get(key, 0))  # A stored record may hold text after a repair by hand
    except (TypeError, ValueError):
        return 0  # An unreadable count reads as zero, which keeps every caller safe


def not_returned_count(entry: Mapping[str, Any]) -> int:
    """Return how many devices of one phase never came back.

    Why:
        FR-047 asks the portal to mark a device that passed the time limit as
        not returned. The phase entry already carries the two counts that the
        status contract transports, so this answer needs no new field and the
        phase entry keeps the one shape the page reads.

    Args:
        entry: One phase entry of the run record.

    Returns:
        The count of devices that did not return. Never below zero.
    """
    missing = _phase_count(entry, "total") - _phase_count(entry, "settled")
    return max(missing, 0)  # A settled count above the total would otherwise report a negative


def phase_partly_settled(entry: Mapping[str, Any]) -> bool:
    """Report whether one phase brought some devices back and lost others.

    Why:
        FR-047 splits a wait that ended into three results. Every device came
        back, no device came back, or some came back and some did not. This
        answer names the third result, which must never read like the second:
        one access point of two hundred that stayed out is not an empty site.
        The counts alone cannot say it, because a phase that still waits also
        holds a settled count below its total, so the state must first report
        a wait that ended.

    Args:
        entry: One phase entry of the run record.

    Returns:
        True when the wait ended and the phase holds both a device that
        returned and a device that did not.
    """
    if str(entry.get("state", "")) != _PHASE_TIMED_OUT:
        return False  # A phase that still waits may yet bring every device back
    return 0 < _phase_count(entry, "settled") < _phase_count(entry, "total")


def mark_not_returned(record: MutableMapping[str, Any], addresses: Sequence[str]) -> int:
    """Mark each device that never came back before the time limit.

    Why:
        FR-047 asks the portal to mark the device itself, so the operator reads
        which access point is missing and not only how many. The state name
        comes from data-model.md section 4.2, which the portal never widens.

    Args:
        record: The run record.
        addresses: The address of each device that did not return.

    Returns:
        How many target entries the driver marked.
    """
    wanted = {str(address).strip().lower() for address in addresses}  # The gate and the record may differ in case
    marked = 0  # Counts the entries the driver changed, for the log line below
    for target in record.get("targets", []):
        if str(target.get("mac", "")).strip().lower() in wanted:
            target["state"] = TARGET_STATE_NOT_RETURNED  # FR-047: this device did not come back
            marked += 1  # One more device the operator must chase by hand
    return marked


def client_gate_open(phases: Sequence[Mapping[str, Any]]) -> bool:
    """Report whether the wireless client gate may open.

    Why:
        Only the wireless clients sit downstream of the access points, so an
        access point holds this one gate shut. FR-047 asks the portal to mark
        the device that passed the time limit and to continue with the others,
        and the edge case at spec.md line 275 lets the operator take the second
        capture without the missing device. One access point of two hundred
        must therefore never throw away the post-check of the whole site. The
        gate opens when at least one access point came back, because the
        clients of that access point are present and countable. The gate stays
        shut when none came back, because a client count of zero would then
        report the silence of the access points and not the clients.

    Args:
        phases: The phase entries of the run record.

    Returns:
        True when the access point phase settled, was skipped, or brought some
        access points back.
    """
    for entry in phases:
        if str(entry.get("name", "")) == AP_PHASE:
            return str(entry.get("state", "")) in _PHASE_COMPLETE or phase_partly_settled(entry)
    return False


def post_check_request(run_id: str) -> dict[str, Any]:
    """Return the identity of the post-check capture of one run.

    Why:
        FR-059 to FR-063 ask for a second capture. Under the default mode the
        driver starts it, and no operator starts it by hand. The ordinal is
        always 2 and the role is always post, so the comparison finds the pair
        without a search.

    Args:
        run_id: The run key.

    Returns:
        The run key, the ordinal 2, and the role post.
    """
    return {"run_id": run_id, "ordinal": POST_CHECK_ORDINAL, "role": POST_CHECK_ROLE}


def portal_wrote(error: BaseException) -> bool:
    """Report whether this package defined the class of one fault.

    Why:
        The portal writes the message of every fault class it defines. No
        module builds such a message from the text of a caught fault. The
        class of a foreign fault comes from another package, or it comes from
        the standard library, which a foreign library also raises.

    Args:
        error: The fault to test.

    Returns:
        True when this package defines the class of the fault.
    """
    return type(error).__module__.startswith(PORTAL_PACKAGE)


def operator_reason(error: BaseException) -> str:
    """Return one safe sentence for a fault that stopped a run.

    Why:
        `RunStateMachine.fail` writes this sentence into the run record, and
        that record reaches ArangoDB, the CSV backup, and the browser. The
        driver meets faults from the cloud library, from Redis, and from
        ArangoDB. Such a fault carries the connection string of its own
        client, so its message must never leave this function.

        A fault of this package carries a sentence that the portal wrote for
        the operator, so that text passes through whole.

    Args:
        error: The fault that stopped the run.

    Returns:
        The sentence for the operator, which never holds a credential.
    """
    if portal_wrote(error):
        return str(error) or type(error).__name__
    return FOREIGN_FAULT_REASON.format(name=type(error).__name__)


def failed_stage(error: BaseException) -> str:
    """Name the step where a run stopped.

    Why:
        The operator reads the step to know where to look. A fault of this
        package names its own step in its text, so the driver reads that
        text. A foreign fault carries no such text, and the driver reads no
        foreign message, so a foreign fault reads as the upgrade step.

    Args:
        error: The fault that stopped the run.

    Returns:
        The post-capture step or the upgrade step.
    """
    if portal_wrote(error) and POST_CHECK_MARK in str(error):
        return STAGE_POST_CAPTURE
    return STAGE_UPGRADE


class RunDriver:
    """Carry one upgrade run from the submission to the post-check capture.

    Why:
        One long-lived thread owns one run. The class registry holds the live
        thread of each run, so a second start finds the first thread and
        returns it. Only this thread writes the run record.
    """

    # WHY: One entry for each live run. The guard protects the dictionary,
    # because a route thread may start a run while another run ends.
    _THREADS: ClassVar[dict[str, threading.Thread]] = {}
    _GUARD: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self, deps: RunDriverDeps) -> None:
        """Hold the collaborators of one driver.

        Args:
            deps: Every collaborator the driver calls.
        """
        self._deps = deps
        self._machine = RunStateMachine()

    @classmethod
    def active_thread(cls, run_id: str) -> threading.Thread | None:
        """Return the live driver thread of one run.

        Args:
            run_id: The run key.

        Returns:
            The thread, or None when no thread owns the run.
        """
        with cls._GUARD:
            thread = cls._THREADS.get(run_id)
        return thread if thread is not None and thread.is_alive() else None

    def start(self, record: MutableMapping[str, Any]) -> threading.Thread:
        """Start the one thread that owns this run.

        Why:
            A second thread would write the same record and would corrupt it
            under multi-user load. This method returns the first thread when
            one already owns the run.

        Args:
            record: The run record.

        Returns:
            The thread that owns the run.
        """
        run_id = str(record.get("run_id", ""))
        with RunDriver._GUARD:
            live = RunDriver._THREADS.get(run_id)
            if live is not None and live.is_alive():
                logger.info("Run %s already holds a driver thread", run_id)
                return live
            thread = threading.Thread(target=self.run, args=(record,), name=f"driver-{run_id}", daemon=True)
            RunDriver._THREADS[run_id] = thread
        thread.start()
        return thread

    def run(self, record: MutableMapping[str, Any]) -> dict[str, Any]:
        """Carry one run to its final state.

        Why:
            The thread must never die without a written reason. Every error
            reaches the record, so the run page shows one plain sentence.

        Args:
            record: The run record.

        Returns:
            A copy of the record in its final state.
        """
        run_id = str(record.get("run_id", ""))
        logger.info("Run %s starts the driver thread", run_id)
        self._watch_lock(record)  # The run thread now renews the site lock, so a closed page keeps the site
        try:
            self._submit(record)
            self._cascade(record)
        except Exception as error:  # noqa: BLE001  # WHY: The thread must write the reason, never die silently.
            self._fail(record, error)
        finally:
            self._quiet_lock()  # The run reached a final state, so the heartbeat stops
            self._free_lock(record)  # A final state gives the site back, and no other state does
            RunDriver._release(run_id)
        return dict(record)

    @classmethod
    def _release(cls, run_id: str) -> None:
        """Drop the registry entry of one run.

        Args:
            run_id: The run key.
        """
        with cls._GUARD:
            thread = cls._THREADS.get(run_id)
            if thread is None or thread is threading.current_thread():
                cls._THREADS.pop(run_id, None)

    def _watch_lock(self, record: MutableMapping[str, Any]) -> None:
        """Point the site lock heartbeat at this run record.

        Why:
            A beat that fails inside a settle gate must reach the record at
            once, and the heartbeat holds no store. The driver hands it one
            call and keeps the single-writer rule, because the call runs on
            this thread and no other.

        Args:
            record: The run record.
        """
        beat = self._deps.heartbeat
        if beat is None:
            return  # A caller that passed no heartbeat still runs, and the browser renews the lock alone
        beat.watch(lambda reason: self._note_lock_loss(record, reason))  # The closure holds this one record

    def _note_lock_loss(self, record: MutableMapping[str, Any], reason: str) -> None:
        """Write a lost site lock into the run record.

        Why:
            The operator must read that the site changed hands while the
            upgrade ran. The run continues, because a takeover never cancels a
            running upgrade and firmware already in flight cannot be recalled.

        Args:
            record: The run record.
            reason: One plain sentence for the operator.
        """
        entry = {"state": LOCK_STATE_LOST, "message": reason, "at": self._deps.clock.now_text()}
        record[LOCK_FIELD] = entry  # The field holds no token and no address, so the record stays safe to read
        self._save(record)  # The store must hold the fact at once, and not at the end of the phase

    def _quiet_lock(self) -> None:
        """Stop the site lock heartbeat of this run.

        Why:
            A run in a final state needs no lock. A beat after that point
            would hold a site that nobody upgrades.
        """
        if self._deps.heartbeat is not None:
            self._deps.heartbeat.stop()  # The release below now gives the site back at once

    def _free_lock(self, record: Mapping[str, Any]) -> None:
        """Give the site back when this run reached a final state.

        Why:
            contracts/site-lock.md line 105 releases the lock at `complete`,
            `stopped`, or `failed`. A lock left to expire holds the site for
            the rest of its 3600-second life, and the next operator waits an
            hour for a site that nobody upgrades.

            Every other state keeps the lock. A closed browser leaves the run
            alive, and the contract at line 98 keeps the site held through it.
            This call sits in the `finally` of the run, which only a final
            state reaches, and the guard below proves the state before the
            release runs.

            The heartbeat holds the key and the token, so a run that built no
            heartbeat can release nothing. That run names the held site in the
            log, because no other line reports the wait that follows.

        Args:
            record: The run record.
        """
        if self._final_state(record) is None:
            return  # The run stopped short of a final state, so the site stays held
        beat = self._deps.heartbeat
        if beat is None:
            run_id = record.get("run_id", "")
            logger.warning("Run %s holds no lock token, so the site stays held until the lease ends", run_id)
            return  # A caller that passed no heartbeat holds no key and no token
        beat.release()  # Never raises, so a quiet lock store cannot fail a run that already ended

    @staticmethod
    def _final_state(record: Mapping[str, Any]) -> RunState | None:
        """Return the final state one record holds, or None.

        Why:
            A record that carries an unknown state name must not stop the
            release path with an exception, because the run already ended.

        Args:
            record: The run record.

        Returns:
            The state, when the record holds one of the three final states.
        """
        try:
            state = RunStateMachine.read_state(record)
        except RunTransitionError:
            return None  # An unreadable state names no final state
        return state if state in RunStateMachine.TERMINAL else None

    def _beat(self) -> None:
        """Renew the site lock at one wait of this run.

        Why:
            Every long wait of the driver sits next to one of these calls. The
            heartbeat counts the seconds itself, so a wait site adds this call
            and never a clock.
        """
        if self._deps.heartbeat is not None:
            self._deps.heartbeat.beat()  # Rate limited, so a call inside the interval costs nothing

    def _submit(self, record: MutableMapping[str, Any]) -> None:
        """Send the upgrade to the cloud and write the tracker.

        Args:
            record: The run record.

        Raises:
            RunDriverError: When the cloud refused the upgrade.
        """
        self._advance(record, RunState.UPGRADE_SUBMITTING)
        self._beat()  # The cloud submission takes minutes for a large site, so the lock beats before it
        if self._deps.submit is not None and not self._deps.submit.submit(record):
            raise RunDriverError("The cloud refused the upgrade, so the run stops here.")
        self._beat()  # The submission returned, so the lock beats again before the run moves on
        write_tracker(record, self._deps.clock.now_text())
        self._advance(record, RunState.UPGRADE_RUNNING)

    def _cascade(self, record: MutableMapping[str, Any]) -> None:
        """Run each settle gate in the fixed order and then finish the run.

        Why:
            Everything sits downstream of the gateways. The access points and
            the wired clients sit downstream of the switches. Only the
            wireless clients sit downstream of the access points. A phase
            starts only after the phase before it reports settled.

            The loop always reaches the finish step, even when one phase could
            not run. A phase that left the loop early would take the post-check
            capture away, and that capture is the one record the operator needs
            most when the site came back wrong.

        Args:
            record: The run record.
        """
        reason: str | None = None  # Names why the run must end failed, and stays None while the run is healthy
        for name in PHASE_ORDER:
            self._beat()  # A phase runs up to half an hour, so it never starts on a lock that is nearly dead
            if self._stop_pending(record):
                self._stop(record)
                return
            self._advance(record, settling_state(name))
            lost = self._run_phase(record, name)  # Text when the phase could not run, and None when it ran
            reason = lost or reason  # A later phase that ran well never clears an earlier reason
        self._finish(record, reason)

    def _run_phase(self, record: MutableMapping[str, Any], name: str) -> str | None:
        """Settle one phase and write the result into the record.

        Why:
            A shut client gate must never throw the run away. The gate is right
            to refuse the count, because a client count of zero would report
            the silence of the access points and not the clients. The phase
            therefore reads failed and the cascade continues, so the operator
            still gets the switch versions, the switch state, the access point
            state, and the wired clients of the site.

        Args:
            record: The run record.
            name: The phase name.

        Returns:
            The reason the run must end failed, or None when the phase ran.
        """
        run_id = str(record.get("run_id", ""))  # The log line and the settle call both name the run
        if name == CLIENT_PHASE and not client_gate_open(record.get("phases", ())):
            logger.warning("Run %s counted no wireless client, because no access point returned", run_id)
            shut = PhaseOutcome(name, PhaseState.FAILED.value)  # FR-058 owns skipped, so a lost family reads failed
            self._write_phase(record, shut)  # The record now names the phase that could not run
            return CLIENT_GATE_SHUT_REASON  # The cascade continues and still takes the post-check capture
        targets = phase_targets(record, name)  # Always empty for the client phase, which holds no device
        if name != CLIENT_PHASE and not targets:
            self._write_phase(record, PhaseOutcome(name, PhaseState.SKIPPED.value))  # FR-058: the site holds none
            return None  # An empty family is no failure, so the run may still reach complete
        outcome = self._deps.gate.settle(run_id, name, targets)  # The gate blocks until the phase settles
        self._beat()  # The phase held this thread for up to half an hour, so the lock beats as it ends
        self._write_phase(record, outcome)  # The record now holds the counts the gate reported
        return None  # This phase ran, so it names no reason to fail the run

    def _write_phase(self, record: MutableMapping[str, Any], outcome: PhaseOutcome) -> None:
        """Replace one phase entry of the record and save the record.

        Why:
            The entry carries the note of the gate as well as the counts. A
            phase that waited on a cloud that would not answer shows the
            operator how many devices returned and never why the rest did not,
            so the page would name a failure with no cause.

        Args:
            record: The run record.
            outcome: What the gate reported.
        """
        settled_at = self._deps.clock.now_text() if outcome.state in _PHASE_COMPLETE else None
        entry: dict[str, Any] = {
            "name": outcome.name,
            "state": outcome.state,
            "settled": outcome.settled,
            "total": outcome.total,
            "settled_at": settled_at,
            "note": outcome.note,
        }
        phases = [dict(item) for item in record.get("phases", [])]
        record["phases"] = [entry if str(item.get("name", "")) == outcome.name else item for item in phases]
        self._record_missing(record, outcome)  # FR-047: mark each device before the record reaches the store
        logger.info("Run %s reports phase %s as %s", record.get("run_id", ""), outcome.name, outcome.state)
        self._save(record)

    def _record_missing(self, record: MutableMapping[str, Any], outcome: PhaseOutcome) -> None:
        """Mark the devices of one phase that never came back.

        Why:
            FR-047 asks the portal to mark the device that passed the time
            limit and to continue with the other devices. The log line names
            both counts, so a later reader tells a phase that brought nothing
            back from a phase that lost one device of two hundred.

        Args:
            record: The run record.
            outcome: What the gate reported.
        """
        missing = max(outcome.total - outcome.settled, 0)  # A settled count above the total reports no loss
        if outcome.state != _PHASE_TIMED_OUT or missing == 0:
            return  # The wait still runs, or every device came back, so nothing needs a mark
        marked = mark_not_returned(record, outcome.not_returned)  # FR-047: name the device, not only the count
        detail = f"settled {outcome.settled} of {outcome.total} and marked {marked} as not returned"
        logger.warning("Run %s phase %s %s", record.get("run_id", ""), outcome.name, detail)

    def _finish(self, record: MutableMapping[str, Any], reason: str | None = None) -> None:
        """Start the post-check capture and close the run.

        Why:
            FR-059 to FR-063 ask for a second capture. Under the default mode
            the driver starts it on its own after the client phase settles, so
            the operator presses no button.

            The capture comes before the final state, in the same order that a
            stopped run follows. A run that lost one phase still holds the
            switch versions, the switch state, the access point state, and the
            wired clients, and that record is the evidence of the failure. The
            run then reports failed, so a run with a lost phase never reads
            complete.

        Args:
            record: The run record.
            reason: Why the run must end failed, or None when every phase ran.
        """
        self._advance(record, RunState.POST_CAPTURE_RUNNING)  # The capture starts before any final state
        self._start_post_check(record)  # FR-059: under the default mode the operator presses no button
        self._advance(record, RunState.POST_CAPTURE_DONE)  # The comparison data of the run now exists
        if reason is not None:
            self._fail(record, RunDriverError(reason))  # The model allows post_capture_done to move to failed
            return  # A run that lost one phase must never report complete
        self._advance(record, RunState.COMPLETE)  # Every phase ran, so the run is honestly complete

    def _start_post_check(self, record: MutableMapping[str, Any]) -> None:
        """Ask the capture path for the second capture of the run.

        Why:
            The mode names who starts this capture. The automatic mode is the
            behavior of today, and it stays the default. The manual mode holds
            the capture and marks the record instead, so a later page can offer
            a button.

            Any other text counts as automatic. A typo in a setting must never
            skip the capture that proves the upgrade worked.

        Args:
            record: The run record.

        Raises:
            RunDriverError: When the capture path returned no key.
        """
        run_id = str(record.get("run_id", ""))
        if self._deps.post_check_mode == POST_CHECK_MANUAL:
            self._hold_post_check(record, run_id)
            return  # The operator starts this capture, so the driver starts none
        record["post_capture_pending"] = False  # No reader then finds a stale mark from an earlier run
        request = post_check_request(run_id)
        logger.info("Run %s starts the post-check capture with ordinal %s", run_id, POST_CHECK_ORDINAL)
        self._beat()  # The capture reads the whole site, so the lock beats before the read starts
        capture_id = self._deps.capture.start(request)
        self._beat()  # The capture held this thread for minutes, so the lock beats as it ends
        record["post_capture_id"] = capture_id
        self._save(record)
        if not capture_id:
            raise RunDriverError("The portal could not start the post-check capture.")

    def _hold_post_check(self, record: MutableMapping[str, Any], run_id: str) -> None:
        """Mark the run record for a post-check capture that an operator starts.

        Why:
            The manual mode starts no capture. The mark is the one signal a
            later page needs, so this seam adds no run state and no route. The
            run still reaches its final state, because the mark changes no step
            of the state machine.

        Args:
            record: The run record.
            run_id: The run key.
        """
        record["post_capture_pending"] = True  # The one mark a later page reads
        self._save(record)
        logger.info("Run %s holds the post-check capture, because the mode is %s", run_id, POST_CHECK_MANUAL)

    def _stop_pending(self, record: MutableMapping[str, Any]) -> bool:
        """Report whether an operator asked to stop this run.

        Why:
            The route thread writes the stop request into the record. The
            driver reads the record back to see it, and copies the field into
            its own copy, so the next write keeps the request.

        Args:
            record: The run record.

        Returns:
            True when a stop request is present.
        """
        stored = self._deps.store.read_run(str(record.get("run_id", "")))
        request = stored.get("stop_request") if stored is not None else None
        if request is None:
            return False
        record["stop_request"] = request
        return True

    def _stop(self, record: MutableMapping[str, Any]) -> None:
        """Close a run that an operator stopped.

        Why:
            FR-038g still allows the second capture after a stop, so the
            operator can compare the part of the site that did upgrade.

        Args:
            record: The run record.
        """
        logger.info("Run %s stops at the request of an operator", record.get("run_id", ""))
        self._advance(record, RunState.STOPPING)
        try:
            self._start_post_check(record)
        except RunDriverError:
            logger.warning("Run %s stopped without a post-check capture", record.get("run_id", ""))
        self._advance(record, RunState.STOPPED)

    def _advance(self, record: MutableMapping[str, Any], target: RunState) -> None:
        """Move the run to one state and save it.

        Args:
            record: The run record.
            target: The wanted state.
        """
        if RunStateMachine.read_state(record) is target:
            return  # The caller already moved the record, so the driver adds nothing
        self._machine.advance(record, target)
        self._save(record)

    def _fail(self, record: MutableMapping[str, Any], error: BaseException) -> None:
        """Write the reason one run failed.

        Why:
            `run` catches every fault of the whole journey, so this method
            meets faults from the cloud library, from Redis, and from
            ArangoDB. The helper `operator_reason` drops the text of such a
            fault. It keeps the class name alone, because a reader sees both
            the record and the log line.

        Args:
            record: The run record.
            error: The error the run met.
        """
        message = operator_reason(error)  # Safe by construction, so the log line below may hold it
        run_id = record.get("run_id", "")
        logger.warning("Run %s failed: %s", run_id, message)
        stage = failed_stage(error)
        try:
            self._machine.fail(record, stage, message)
        except RunTransitionError:
            logger.warning("Run %s already holds a final state, so the driver wrote no reason", run_id)
            return
        self._save(record)

    def _save(self, record: MutableMapping[str, Any]) -> None:
        """Write the run record, and keep the field the route thread owns.

        Why:
            The driver owns every field except `stop_request`. The route
            thread writes that one field. A read back before each write keeps
            a stop request that arrived after the driver read the record.

        Args:
            record: The run record.
        """
        stored = self._deps.store.read_run(str(record.get("run_id", "")))
        if stored is not None and stored.get("stop_request") is not None:
            record["stop_request"] = stored["stop_request"]
        record["updated_at"] = self._deps.clock.now_text()
        self._deps.store.write_run(dict(record))
