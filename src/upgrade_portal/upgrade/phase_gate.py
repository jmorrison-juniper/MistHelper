"""The blocking phase adapter between the settle gate and the run driver.

Why:
    ``driver.PhaseGate`` needs one blocking call for a whole phase, and
    ``gate.SettleGate`` offers one pure step for one device. Neither side can
    meet the other on its own, so the cascade cannot run without this module.
    This adapter holds the loop that the two shapes lack. It builds one gate
    target for each device of the phase. It polls the two signal sources every
    20 seconds and feeds each round to the gate. It returns only after the
    phase settles or the deadline passes.

    The adapter owns no settle rule. The gate decides when one device is back.
    This module decides only when to poll and when to stop waiting.

    One round makes exactly two cloud calls, whatever the device count. The
    event poll gives the reconnect signal and the fleet statistics poll gives
    the uptime and the version. One family polls at a time, because the cascade
    runs one phase at a time, so the pair costs 180 plus 180 calls each hour.
    That is the documented budget of ``gate.MAX_CALLS_PER_HOUR``, which is 7.2
    percent of the quota at ``src/utils/rate_limiting.py:56``. The reboot hint
    of ``gate.read_reboot_hint`` is an aid and never a signal, so this loop
    never calls it. A third call in the round would break the budget.

    The deadline for one phase is 30 minutes. FR-047 makes a limit mandatory
    and names no number, so this module chooses one and states the reason here.
    A Junos device writes the image and then reboots, and the vendor publishes
    no settle time for a switch or a gateway
    (``research/settle-gate-apis.md`` section 11), so the value cannot come
    from vendor guidance.

    Thirty minutes covers a slow chassis and still holds the call budget
    exactly. Thirty minutes at 20 seconds is 90 rounds. Each round is one event
    call plus one statistics call, a rate of 360 calls each hour. A run whose
    four phases all reach the limit therefore lasts 2 hours at that same rate.
    A longer limit would leave an operator with no news for too long, and a
    shorter one would call a healthy slow switch a failure.

    Every wait goes through an injected sleep, and every clock reading comes
    from the gate that the caller passed. One clock serves the phase deadline
    and the device waits together, because two clocks would drift and the drift
    would show only under load. A test drives a whole 30-minute phase in
    microseconds and waits no real seconds.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Final, Protocol

from src.upgrade_portal.capture.devices import normalize_device_mac
from src.upgrade_portal.runtime.runs import PhaseState
from src.upgrade_portal.upgrade import events, gate
from src.upgrade_portal.upgrade.driver import PhaseGate, PhaseOutcome

logger = logging.getLogger(__name__)

# WHY: FR-047 makes a time limit mandatory and names no number. The module
# docstring holds the reason for this value. The limit is a whole multiple of
# gate.POLL_INTERVAL_SECONDS, so the round count of a phase that reaches the
# limit holds the pair of poll streams at gate.MAX_CALLS_PER_HOUR exactly.
PHASE_DEADLINE_SECONDS: Final[int] = 1800

# WHY: One event read and one statistics read. A reader who adds a third call
# to the round breaks the budget, and this constant makes a test say so.
CALLS_PER_ROUND: Final[int] = 2

# WHY: A phase that reaches its limit tells the operator how many devices came
# back and never why the wait was blind. These sentences name the source that
# the portal could not read, so the phase entry carries a cause. They avoid the
# word "check", because this feature already uses "pre-check" and "post-check"
# for the two captures.
NOTE_EVENT_READ_FAILED: Final[str] = "The portal could not read the device events."
NOTE_STATISTICS_READ_FAILED: Final[str] = "The portal could not read the device statistics."
NOTE_STATISTICS_PARTIAL: Final[str] = "The portal read part of the device statistics."


class PhaseGateError(RuntimeError):
    """One phase cannot be watched as it stands.

    Why:
        A phase that mixed two device families would poll the first family
        only, because one event call names one family. The devices of the other
        family would then wait to the deadline with no explanation, and the
        cloud reports no error for that case. This error turns the silence into
        a fault at the start of the phase.
    """


@dataclass(frozen=True, slots=True)
class PhaseProgress:
    """How far one phase moved after one poll round.

    Why:
        FR-048 asks the portal to report progress as each device returns. The
        adapter builds this record after every round and hands it to the
        progress seat of `PhaseGateDeps`.

        Caution: in production nothing publishes this record to the operator.
        `app/wiring.py` puts the site lock heartbeat in the progress seat,
        because that seat is the only call inside the 20-second poll loop, and
        `wiring.build_heartbeat` calls `driver.lock_heartbeat` with two
        arguments. The optional `progress` parameter of that function is
        therefore `None`, so the heartbeat renews the lock and forwards this
        record nowhere.

        The run record holds one write site for `phases`, at
        `upgrade/driver.py`, and it runs after `settle()` returns. The count on
        the progress page therefore holds its opening value for the length of a
        phase and then jumps.

        The live channel stays unbuilt on purpose. One store write for each round
        is 30 to 90 extra writes for each phase, and a phase may hold half an
        hour. `audit-2026-08-20.md` section 2.4 declined it, and issue #1995
        records the decision. The page states when the count moves instead, so a
        still count reads as a wait and not as a stall.

    Attributes:
        run_id: The run key.
        phase: The phase name.
        settled: How many devices of the phase returned so far.
        total: How many devices the phase holds.
    """

    run_id: str
    phase: str
    settled: int
    total: int


class ReconnectReader(Protocol):
    """The source of the reconnect signal of one poll round.

    Why:
        The loop must build no cloud session of its own, and a unit test must
        open no socket. This shape lets the application pass the cloud reader
        and lets a test pass a fixed list of answers.
    """

    def read(self, device_type: str) -> frozenset[str]:
        """Return the address of each device of one family that reconnected.

        Args:
            device_type: The family to read.

        Returns:
            The addresses in lower case with no separator.
        """
        ...  # A protocol declares the shape only


class StatisticsReader(Protocol):
    """The source of the uptime and the version of one poll round.

    Why:
        The read covers the whole fleet with one call, so the shape takes no
        device address. A per-device read would multiply the call count by the
        device count and would pass the hourly quota.
    """

    def read(self) -> gate.FleetRead:
        """Read the statistics of the whole fleet with one call.

        Returns:
            The readings and the reasons of one poll.
        """
        ...  # A protocol declares the shape only


class DeviceGate(Protocol):
    """The per-device settle rules and the clock of one run.

    Why:
        ``gate.SettleGate`` fills this shape. Naming the shape here keeps the
        loop separate from the rules, so a test proves the loop with a stub and
        proves the rules with the real gate. It also gives the loop one clock,
        which is the same clock that measures the device waits.
    """

    def now(self) -> float:
        """Return the current clock reading.

        Returns:
            The time in seconds.
        """
        ...  # A protocol declares the shape only

    def observe(
        self,
        target: gate.GateTarget,
        progress: gate.GateProgress,
        signals: gate.GateSignals,
    ) -> gate.GateProgress:
        """Apply one round of observations to one device.

        Args:
            target: The state of the device before the upgrade.
            progress: The signals recorded so far.
            signals: The observations of this round.

        Returns:
            The progress after this round.
        """
        ...  # A protocol declares the shape only


class ProgressReporter(Protocol):
    """The sink that shows the operator how one phase moves."""

    def report(self, progress: PhaseProgress) -> None:
        """Take one progress record of one phase.

        Args:
            progress: The counts after one poll round.
        """
        ...  # A protocol declares the shape only


class LogProgressReporter:
    """Write one progress line after each poll round.

    Why:
        This default keeps the adapter free of the run record store, which one
        thread alone may write. The application passes a reporter that updates
        the run record, and the browser poll then shows the same counts. A
        portal that passed no reporter still leaves a trace in the log.
    """

    def report(self, progress: PhaseProgress) -> None:
        """Write one progress line.

        Args:
            progress: The counts after one poll round.
        """
        logger.info(
            "Run %s phase %s: %s of %s device(s) returned",
            progress.run_id,
            progress.phase,
            progress.settled,
            progress.total,
        )


class CloudReconnectReader:
    """Read the reconnect events of one device family from the cloud.

    Why:
        The event read needs a session, an organization, a time window, and the
        event key catalogue. Holding all four here keeps the poll loop at one
        call and keeps cloud detail out of the loop.

        The catalogue read happens once for the life of the process, because
        ``events.EventCatalogue`` caches it. That is a start-up read and not a
        third poll, so the budget of two calls in each round holds.
    """

    def __init__(
        self,
        session: Any,
        org_id: str,
        catalogue: events.EventCatalogue,
        clock: Callable[[], float],
    ) -> None:
        """Build one cloud reconnect reader.

        Args:
            session: The cloud session. The caller owns it.
            org_id: The organization to read.
            catalogue: The holder of the reconnect event keys.
            clock: The clock that builds the end of the event window.
        """
        self._session = session
        self._org_id = org_id
        self._catalogue = catalogue
        self._clock = clock

    def read(self, device_type: str) -> frozenset[str]:
        """Return the address of each device of one family that reconnected.

        Args:
            device_type: The family to read. The call always sends it, because
                the cloud defaults the value to ``ap``.

        Returns:
            The addresses in lower case with no separator.
        """
        window = events.build_window(self._clock())
        rows = events.drain_device_events(self._session, self._org_id, device_type, window)
        return events.reconnect_macs(rows, self._catalogue.load(self._session))


class CloudStatisticsReader:
    """Read the uptime and the version of the whole fleet from the cloud."""

    def __init__(self, session: Any, org_id: str, site_id: str | None = None) -> None:
        """Build one cloud statistics reader.

        Args:
            session: The cloud session. The caller owns it.
            org_id: The organization that owns the devices.
            site_id: The site to read. None reads every site.
        """
        self._session = session
        self._org_id = org_id
        self._site_id = site_id

    def read(self) -> gate.FleetRead:
        """Read the statistics of the whole fleet with one call.

        Returns:
            The readings and the reasons of one poll.
        """
        return gate.read_fleet_statistics(self._session, self._org_id, self._site_id)


@dataclass(frozen=True, slots=True)
class PhaseGateDeps:
    """Everything the phase gate needs from outside itself.

    Why:
        A constructor that took the session, the organization, the site, the
        clock, the sleep, and the reporter would pass the parameter limit. One
        record holds them together, and a test replaces one member at a time.

    Attributes:
        event_reader: The source of the reconnect signal.
        statistics_reader: The source of the uptime and the version.
        settle_gate: The per-device rules and the one clock of the wait.
        progress: The sink of the progress report.
        sleep: The wait between two poll rounds. A test passes a callable that
            moves a fake clock and waits no real seconds.
    """

    event_reader: ReconnectReader
    statistics_reader: StatisticsReader
    settle_gate: DeviceGate = field(default_factory=gate.SettleGate)
    progress: ProgressReporter = field(default_factory=LogProgressReporter)
    sleep: Callable[[float], None] = time.sleep


@dataclass(frozen=True, slots=True)
class _PhaseWatch:
    """The moving state of one phase wait.

    Why:
        The loop needs the run, the phase, the targets, the limit, and the
        progress of every device together. One record keeps each private method
        at two parameters and keeps the loop free of a long argument list that a
        reader must match by position.

    Attributes:
        run_id: The run key that the progress report names.
        phase: The phase name that the outcome carries.
        targets: One gate target for each device of the phase.
        deadline: The clock reading at which the wait stops.
        progress: The signals of each device so far, keyed by the address.
    """

    run_id: str
    phase: str
    targets: tuple[gate.GateTarget, ...]
    deadline: float
    progress: dict[str, gate.GateProgress]

    @property
    def family(self) -> str:
        """Return the device family that the event poll must ask for.

        Why:
            The family comes from the targets and never from a second phase to
            family map, because the targets already carry it and a second map
            would drift from the first.

        Returns:
            The family in lower case. Empty when the phase holds no target.
        """
        return phase_family(self.targets)

    @property
    def settled(self) -> int:
        """Return how many devices of the phase returned.

        Returns:
            The count of settled devices.
        """
        return sum(1 for record in self.progress.values() if gate.is_settled(record))

    @property
    def is_complete(self) -> bool:
        """Report whether every device of the phase returned.

        Returns:
            True when no device of the phase is still out.
        """
        return self.settled == len(self.targets)

    @property
    def missing(self) -> tuple[str, ...]:
        """Return the address of each device that has not returned.

        Returns:
            The addresses in a stable order, for the operator message.
        """
        return tuple(sorted(mac for mac, item in self.progress.items() if not gate.is_settled(item)))


def polls_per_phase(deadline_seconds: int = PHASE_DEADLINE_SECONDS) -> int:
    """Return how many poll rounds fit inside one phase deadline.

    Why:
        The loop counts its rounds as well as reading the clock. A clock that
        never moves, in a test or after a time step on the host, would otherwise
        hold the run thread for ever. The count comes from the deadline, so the
        two limits can never disagree.

    Args:
        deadline_seconds: The time limit of one phase.

    Returns:
        The largest number of rounds that one phase runs.

    Raises:
        ValueError: When the deadline is zero seconds or less.
    """
    if deadline_seconds <= 0:
        raise ValueError("A phase deadline must be greater than zero seconds.")
    return deadline_seconds // gate.POLL_INTERVAL_SECONDS


def calls_per_phase(deadline_seconds: int = PHASE_DEADLINE_SECONDS) -> int:
    """Return how many cloud calls one phase makes at most.

    Why:
        The budget of this feature must stay checkable rather than stated. A
        test compares this answer against ``gate.MAX_CALLS_PER_HOUR``, so a
        change of the deadline or of the round that breaks the budget fails the
        build instead of failing in production.

    Args:
        deadline_seconds: The time limit of one phase.

    Returns:
        The largest number of cloud calls that one phase makes.

    Raises:
        ValueError: When the deadline is zero seconds or less.
    """
    return polls_per_phase(deadline_seconds) * CALLS_PER_ROUND


def phase_family(targets: Sequence[gate.GateTarget]) -> str:
    """Return the one device family that a phase polls.

    Why:
        One event call names one family, and one cascade phase holds one
        family. A phase that mixed two families would read the events of the
        first family only, and the devices of the second family would never see
        a reconnect. The cloud reports no error for that case, so the mix must
        raise here.

    Args:
        targets: The gate targets of one phase.

    Returns:
        The family in lower case. Empty when the phase holds no target.

    Raises:
        PhaseGateError: When the targets name more than one family.
    """
    families = {target.device_type for target in targets}
    if len(families) > 1:
        raise PhaseGateError(f"One phase polls one device family, and this phase holds {sorted(families)}.")
    return families.pop() if families else ""


def _uptime_before(mac: str, value: Any) -> int | None:
    """Return the uptime that the gate compares each reading against.

    Why:
        ``data-model.md:283`` allows a null ``uptime_before`` and warns that a
        stored zero makes every later reading look larger. The null therefore
        reaches ``gate.GateTarget`` unchanged. The gate then settles that
        device on the firmware version change alone and warns as it does so.
        A zero here would instead hold the device to a fall that no reading
        can show, and it would wait to the phase deadline.

    Args:
        mac: The device address, for the warning.
        value: The raw ``uptime_before`` value of the run record.

    Returns:
        The uptime in seconds, or None when the record holds no reading.
    """
    uptime = gate.reading_uptime(value)  # A null or a text value both mean "not read".
    if uptime is None:  # Name the device now, because the gate will use the weaker rule.
        logger.warning("Upgrade phase gate holds no earlier uptime for device %s", mac)
    return uptime  # The null travels to the gate unchanged.


def _build_target(entry: Mapping[str, Any]) -> gate.GateTarget | None:
    """Build one gate target from one target entry of the run record.

    Why:
        The gate needs both anchors. The uptime can arrive as a null, so the
        entry also carries the cloud moment of the last report before the
        upgrade. A missing anchor stays null and proves nothing.

    Args:
        entry: One entry of the ``targets`` list of the run record.

    Returns:
        The gate target, or None when the entry carries no usable address.
    """
    mac = normalize_device_mac(entry.get("mac"))
    if not mac:
        logger.warning("Upgrade phase gate dropped a target entry that carries no usable address")
        return None
    return gate.GateTarget(
        mac=mac,
        device_type=str(entry.get("device_type", "")).strip().lower(),
        version_before=str(entry.get("version_before", "")),
        uptime_before=_uptime_before(mac, entry.get("uptime_before")),
        last_seen_before=gate.reading_last_seen(entry.get("last_seen_before")),  # The absolute anchor.
    )


def build_targets(targets: Sequence[Mapping[str, Any]]) -> tuple[gate.GateTarget, ...]:
    """Build one gate target for each device entry of one phase.

    Why:
        The driver hands the gate the raw target entries of the run record, and
        the gate needs its own record. The address goes through the shared
        normalizer, because the event poll and the statistics poll both use it.
        An entry with no usable address matches every other malformed entry, so
        this builder drops it.

    Args:
        targets: The target entries of one phase.

    Returns:
        One gate target for each usable entry.
    """
    built = [_build_target(entry) for entry in targets]
    return tuple(target for target in built if target is not None)


class PhaseSettleGate:
    """Wait for one cascade phase to settle and report the result.

    Why:
        ``driver.PhaseGate`` needs one blocking call for a whole phase, and
        ``gate.SettleGate`` offers one pure step for one device. This class is
        the loop between the two. It holds no settle rule of its own.

        The clock comes from the settle gate and never from a second source.
        A phase deadline and a device wait that read two clocks would drift.
    """

    def __init__(self, deps: PhaseGateDeps, deadline_seconds: int = PHASE_DEADLINE_SECONDS) -> None:
        """Build one phase gate.

        Args:
            deps: The readers, the settle gate, the reporter, and the sleep.
            deadline_seconds: The time limit of one phase.

        Raises:
            ValueError: When the deadline is zero seconds or less.
        """
        self._deps = deps
        self._deadline_seconds = deadline_seconds
        self._ceiling = polls_per_phase(deadline_seconds)

    def settle(self, run_id: str, phase: str, targets: Sequence[Mapping[str, Any]]) -> PhaseOutcome:
        """Wait for one phase to settle and report the result.

        Why:
            This is the call that ``driver.PhaseGate`` declares. It blocks the
            run thread until every device of the phase returned or the deadline
            passed. That is what the cascade needs. The next phase must never
            start while the phase above it is still down.

        Args:
            run_id: The run key.
            phase: The phase name.
            targets: The target entries of that phase. Empty for clients.

        Returns:
            The outcome of the phase.

        Raises:
            PhaseGateError: When the targets name more than one device family.
        """
        entries = build_targets(targets)
        if not entries:
            return self._empty_outcome(run_id, phase)
        return self._wait(self._watch(run_id, phase, entries))

    def _empty_outcome(self, run_id: str, phase: str) -> PhaseOutcome:
        """Report a phase that holds no device target.

        Why:
            The client phase carries no device target, because the switch gate
            already released every wired client. FR-058 also skips a family that
            the site does not hold. Both cases settle at once, rather than wait
            for a poll that has nothing to watch.

        Args:
            run_id: The run key.
            phase: The phase name.

        Returns:
            The outcome of the phase.
        """
        logger.info("Run %s phase %s holds no device target, so it settled at once", run_id, phase)
        self._deps.progress.report(PhaseProgress(run_id, phase, 0, 0))
        return PhaseOutcome(phase, PhaseState.SETTLED.value, 0, 0)

    def _watch(self, run_id: str, phase: str, entries: tuple[gate.GateTarget, ...]) -> _PhaseWatch:
        """Build the moving state of one phase wait.

        Args:
            run_id: The run key.
            phase: The phase name.
            entries: The gate targets of the phase.

        Returns:
            The state that the loop moves forward.

        Raises:
            PhaseGateError: When the targets name more than one device family.
        """
        family = phase_family(entries)
        logger.info("Run %s waits for %s %s device(s) of phase %s", run_id, len(entries), family, phase)
        deadline = self._deps.settle_gate.now() + float(self._deadline_seconds)
        return _PhaseWatch(run_id, phase, entries, deadline, {target.mac: gate.GateProgress() for target in entries})

    def _wait(self, watch: _PhaseWatch) -> PhaseOutcome:
        """Poll until the phase settles or the wait reaches its limit.

        Why:
            The deadline test follows the sleep and never precedes the round.
            The loop therefore polls at 0, 20, and every 20 seconds up to one
            interval before the limit, which is the exact round count that
            ``calls_per_phase`` reports. A test that read the clock first would
            add one round and pass the documented call budget.

            The loop keeps the cause of the last round alone. An earlier round
            that failed and a later round that answered describe a cloud that
            recovered, and the page must show the state of the last look.

        Args:
            watch: The moving state of the wait.

        Returns:
            The outcome of the phase.
        """
        note = ""
        for _ in range(self._ceiling):
            note = self._round(watch)
            if watch.is_complete:
                return self._outcome(watch, PhaseState.SETTLED)
            self._deps.sleep(float(gate.POLL_INTERVAL_SECONDS))
            if self._deps.settle_gate.now() >= watch.deadline:
                break
        return self._timeout(watch, note)

    def _round(self, watch: _PhaseWatch) -> str:
        """Run one poll round and report how far the phase moved.

        Why:
            The round makes exactly two cloud calls whatever the device count.
            One event poll gives the reconnect signal, and one fleet statistics
            poll gives the uptime and the version. A third call here would break
            the budget of ``gate.MAX_CALLS_PER_HOUR``.

        Args:
            watch: The moving state of the wait.

        Returns:
            One sentence for each source that this round could not read, joined
            by a space. Empty text after a whole round.
        """
        reconnected, event_note = self._read_reconnects(watch.family)
        readings, statistics_note = self._read_statistics()
        for target in watch.targets:
            self._observe(watch, target, gate.GateSignals(target.mac in reconnected, readings.get(target.mac)))
        self._deps.progress.report(PhaseProgress(watch.run_id, watch.phase, watch.settled, len(watch.targets)))
        return " ".join(note for note in (event_note, statistics_note) if note)

    def _observe(self, watch: _PhaseWatch, target: gate.GateTarget, signals: gate.GateSignals) -> None:
        """Apply one round of observations to one device.

        Why:
            A settled device never moves again, so the loop skips it. The skip
            keeps the log of a large phase readable and keeps the settled count
            of the report stable.

        Args:
            watch: The moving state of the wait.
            target: The device to observe.
            signals: The observations of this round for that device.
        """
        current = watch.progress[target.mac]
        if gate.is_settled(current):
            return
        watch.progress[target.mac] = self._deps.settle_gate.observe(target, current, signals)

    def _read_reconnects(self, family: str) -> tuple[frozenset[str], str]:
        """Read the reconnect signal of one round.

        Why:
            A read that failed must not stop the run. The event window reaches
            300 seconds back and the round repeats after 20 seconds, so the next
            round reads the same event again and the signal is not lost.

            The answer carries the cause as well as the addresses. An empty set
            alone reads exactly like a round in which no device came back, so
            the operator would see a wait with no stated reason.

        Args:
            family: The device family to read.

        Returns:
            The addresses that reconnected, and the cause of a failed read. The
            cause is empty text after a whole read.
        """
        try:
            return self._deps.event_reader.read(family), ""
        except Exception as error:  # A failed read costs one round and never stops the run.
            logger.warning("Upgrade phase gate failed the %s event read: %s", family, type(error).__name__)
            return frozenset(), NOTE_EVENT_READ_FAILED

    def _read_statistics(self) -> tuple[Mapping[str, gate.GateReading], str]:
        """Read the uptime and the version of the whole fleet for one round.

        Why:
            ``gate.read_fleet_statistics`` catches a cloud fault of its own and
            answers with a partial reason. A reader that the application or a
            test passes may still raise, and one failed round must never stop
            the run. The gate keeps the progress it already holds, so a lost
            round costs 20 seconds and nothing else.

            The cause travels back with the readings. The reason entries name a
            machine fault and reach the log alone, so this reader turns them
            into one sentence that an operator can read. An answer that holds no
            reading at all reports a failed read, because a partial read that
            returned nothing helps the operator no more than a fault does.

        Returns:
            One reading for each device, and the cause of a failed or partial
            read. The cause is empty text after a whole read.
        """
        try:
            result = self._deps.statistics_reader.read()
        except Exception as error:  # A failed read costs one round and never stops the run.
            logger.warning("Upgrade phase gate failed the fleet statistics read: %s", type(error).__name__)
            return {}, NOTE_STATISTICS_READ_FAILED
        if not result.partial_reasons:
            return result.readings, ""
        logger.warning("Upgrade phase gate read partial statistics: %s", result.partial_reasons)
        note = NOTE_STATISTICS_PARTIAL if result.readings else NOTE_STATISTICS_READ_FAILED
        return result.readings, note

    def _outcome(
        self,
        watch: _PhaseWatch,
        state: PhaseState,
        not_returned: tuple[str, ...] = (),
        note: str = "",
    ) -> PhaseOutcome:
        """Build the answer that the driver writes into the run record.

        Why:
            FR-047 asks the portal to mark each device that never returned. The
            gate knows those addresses and the driver owns the per-device marks,
            so the addresses travel in the outcome rather than in a log line
            that no later reader can act on.

            The note travels the same way and for the same reason. A phase that
            waited on a cloud that would not answer must say so on the page, and
            the log of the run thread is not a page.

        Args:
            watch: The moving state of the wait.
            state: The phase state to report.
            not_returned: The address of each device that never came back.
            note: One sentence naming what the last round could not read.

        Returns:
            The outcome of the phase.
        """
        return PhaseOutcome(watch.phase, state.value, watch.settled, len(watch.targets), not_returned, note)

    def _timeout(self, watch: _PhaseWatch, note: str = "") -> PhaseOutcome:
        """Report a phase that reached its time limit.

        Why:
            FR-047 asks the portal to mark a device that did not return and to
            continue with the others. The counts of the outcome carry that
            answer: ``settled`` names how many came back and ``total`` names how
            many the phase held. The state is ``failed``, because the phase did
            not settle and the operator must see the difference.

        Args:
            watch: The moving state of the wait.
            note: One sentence naming what the last round could not read.

        Returns:
            The outcome of the phase.
        """
        missing = watch.missing
        logger.warning(
            "Run %s phase %s stopped waiting at its limit with %s device(s) still out: %s",
            watch.run_id,
            watch.phase,
            len(missing),
            ", ".join(missing),
        )
        return self._outcome(watch, PhaseState.FAILED, missing, note)  # FR-047: the driver marks each named device


def as_phase_gate(adapter: PhaseSettleGate) -> PhaseGate:
    """Return one phase gate under the protocol type that the driver needs.

    Why:
        The driver depends on a protocol and never on this module. This function
        is the one place where the concrete class meets that protocol, so the
        type gate proves the match at build time. A drift between the two shapes
        then fails ``mypy`` instead of failing in the middle of an upgrade.

    Args:
        adapter: The phase gate to hand to the driver.

    Returns:
        The same object, typed as the protocol that the driver calls.
    """
    return adapter


__all__ = [
    "CALLS_PER_ROUND",
    "NOTE_EVENT_READ_FAILED",
    "NOTE_STATISTICS_PARTIAL",
    "NOTE_STATISTICS_READ_FAILED",
    "PHASE_DEADLINE_SECONDS",
    "CloudReconnectReader",
    "CloudStatisticsReader",
    "DeviceGate",
    "LogProgressReporter",
    "PhaseGateDeps",
    "PhaseGateError",
    "PhaseProgress",
    "PhaseSettleGate",
    "ProgressReporter",
    "ReconnectReader",
    "StatisticsReader",
    "as_phase_gate",
    "build_targets",
    "calls_per_phase",
    "phase_family",
    "polls_per_phase",
]
