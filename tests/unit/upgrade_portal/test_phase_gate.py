"""Unit tests for the blocking phase adapter of the upgrade portal.

Why:
    This adapter is the seam between two finished parts that do not meet. The
    driver needs one blocking call for a whole phase, and the settle gate
    offers one pure step for one device. A fault in the loop between them is
    quiet: the run waits instead of failing. These tests therefore measure the
    round count of every case, because the round count is the only visible
    proof that the loop polled, waited, and stopped when it should.

    No test sleeps. The sleep of every test moves a fake clock forward and
    returns at once, and one test measures the real clock to prove it. A phase
    that asks for 30 minutes of waiting finishes here in milliseconds.

    No test opens a socket, names a real organization, or holds a credential.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Collection, Mapping, Sequence
from typing import Any

import pytest

from src.upgrade_portal.runtime.runs import PhaseState
from src.upgrade_portal.upgrade import gate, phase_gate
from src.upgrade_portal.upgrade.driver import PhaseOutcome

# WHY: Obviously fake identifiers. A reader sees at once that no test reaches
#      a real organization, a real site, or a real device.
RUN_ID = "run-0123456789abcdef0123456789abcdef"
SWITCH_MAC = "0011220000aa"
SECOND_SWITCH_MAC = "0011220000cc"
ACCESS_POINT_MAC = "0011220000bb"

VERSION_BEFORE = "23.4R2.13"
VERSION_AFTER = "23.4R2-S3.9"

# WHY: A device that ran for 21 days, and the small positive uptime of a fast
#      reboot. The gate compares the two, so neither value may be zero.
UPTIME_BEFORE = 1832140
UPTIME_AFTER_FAST_REBOOT = 45

START_TIME = 1000.0

# WHY: The expected round count of each settle case. A switch waits 60 seconds
#      and the loop polls every 20, so the round at 60 seconds is the fourth.
#      An access point waits 120 seconds, so its round is the seventh.
SWITCH_SETTLE_ROUNDS = 4
ACCESS_POINT_SETTLE_ROUNDS = 7

# WHY: One failed read costs one round and nothing else.
ROUNDS_AFTER_ONE_FAILED_READ = SWITCH_SETTLE_ROUNDS + 1

# WHY: A whole 30-minute phase must finish well inside one real second.
REAL_TIME_LIMIT_SECONDS = 1.0


class FakeClock:
    """A clock that a test drives forward with no real wait.

    Why:
        The deadline of one phase is 30 minutes. A test that used the real
        clock would run for 30 minutes for one case. This clock returns
        whatever the test set, so the same case runs in milliseconds.
    """

    def __init__(self, start: float = START_TIME) -> None:
        """Build one clock.

        Args:
            start: The first reading in seconds.
        """
        self.value = start

    def __call__(self) -> float:
        """Return the current reading.

        Returns:
            The time in seconds.
        """
        return self.value

    def advance(self, seconds: float) -> None:
        """Move the clock forward.

        Args:
            seconds: The number of seconds to add.
        """
        self.value += seconds


class FakeSleep:
    """A sleep that moves a fake clock forward and waits no real seconds.

    Why:
        The adapter waits 20 seconds between two rounds. A test suite that
        really waited would need 30 minutes for the deadline case alone. This
        callable holds the clock that it moves, so the wait of the loop and the
        time that the gate reads can never disagree.
    """

    def __init__(self, clock: FakeClock | None = None) -> None:
        """Build one fake sleep.

        Args:
            clock: The clock to move. A new clock when the caller passes none.
        """
        self.clock = clock or FakeClock()
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        """Record the wait and move the clock instead of waiting.

        Args:
            seconds: The number of seconds the loop asked to wait.
        """
        self.calls.append(seconds)
        self.clock.advance(seconds)


class FakeReconnectReader:
    """Answer the reconnect poll from a fixed schedule.

    Why:
        A test must choose the round at which each device comes back. The
        schedule holds one answer for each round and repeats its last entry,
        so a long deadline case needs no long schedule.
    """

    def __init__(self, schedule: Sequence[Collection[str]] = (), fail_rounds: Collection[int] = ()) -> None:
        """Build one fake reconnect reader.

        Args:
            schedule: One address set for each round. The last entry repeats.
            fail_rounds: The one-based rounds at which the read raises.
        """
        self._schedule = [frozenset(item) for item in schedule]
        self._fail_rounds = frozenset(fail_rounds)
        self.calls = 0
        self.families: list[str] = []

    def read(self, device_type: str) -> frozenset[str]:
        """Return the addresses that reconnected in this round.

        Args:
            device_type: The family that the adapter asked for.

        Returns:
            The addresses of the round.

        Raises:
            RuntimeError: When the test scheduled a failure for this round.
        """
        self.calls += 1
        self.families.append(device_type)
        if self.calls in self._fail_rounds:
            raise RuntimeError("the cloud refused the event read")
        if not self._schedule:
            return frozenset()
        return self._schedule[min(self.calls - 1, len(self._schedule) - 1)]


class FakeStatisticsReader:
    """Answer the statistics poll with a fixed fleet reading.

    Why:
        The gate ignores a reading that arrives before the reconnect event, so
        one constant answer covers every case. The failure rounds let a test
        prove that a broken read costs one round and never stops the run.
    """

    def __init__(
        self,
        readings: Mapping[str, gate.GateReading] | None = None,
        fail_rounds: Collection[int] = (),
        partial_reasons: Sequence[dict[str, Any]] = (),
    ) -> None:
        """Build one fake statistics reader.

        Args:
            readings: One reading for each device, keyed by the address.
            fail_rounds: The one-based rounds at which the read raises.
            partial_reasons: The reasons that each answer carries.
        """
        self._readings = dict(readings or {})
        self._fail_rounds = frozenset(fail_rounds)
        self._partial_reasons = list(partial_reasons)
        self.calls = 0

    def read(self) -> gate.FleetRead:
        """Return the fleet reading of this round.

        Returns:
            The readings and the reasons of the round.

        Raises:
            RuntimeError: When the test scheduled a failure for this round.
        """
        self.calls += 1
        if self.calls in self._fail_rounds:
            raise RuntimeError("the cloud refused the statistics read")
        return gate.FleetRead(readings=dict(self._readings), partial_reasons=list(self._partial_reasons))


class RecordingReporter:
    """Keep every progress record that the adapter sent."""

    def __init__(self) -> None:
        """Build one recording reporter."""
        self.reports: list[phase_gate.PhaseProgress] = []

    def report(self, progress: phase_gate.PhaseProgress) -> None:
        """Keep one progress record.

        Args:
            progress: The counts after one poll round.
        """
        self.reports.append(progress)


class AlwaysSettledGate:
    """A device gate that settles every device on its first observation.

    Why:
        The real gate waits 60 seconds after the reboot signal, so no phase can
        settle on its first round under the real rules. This stub proves the
        loop on its own: one round, no wait, and a settled outcome. Other tests
        drive the same loop with the real gate and the real waits.
    """

    def __init__(self, clock: FakeClock) -> None:
        """Build one stub gate.

        Args:
            clock: The clock that the loop and the stub share.
        """
        self.clock = clock

    def now(self) -> float:
        """Return the current reading.

        Returns:
            The time in seconds.
        """
        return self.clock()

    def observe(
        self,
        target: gate.GateTarget,
        progress: gate.GateProgress,
        signals: gate.GateSignals,
    ) -> gate.GateProgress:
        """Answer with a settled record whatever the round holds.

        Args:
            target: The device to observe.
            progress: The signals recorded so far.
            signals: The observations of this round.

        Returns:
            A settled progress record.
        """
        moment = self.clock()
        return gate.GateProgress(reconnected=True, reboot_at=moment, settled_at=moment, version_after=VERSION_AFTER)


class Harness:
    """One phase gate with every outside source under the control of a test.

    Why:
        Every test needs the same five parts wired the same way. Building them
        once here keeps each test to the case it proves, and it makes the one
        rule that matters visible in one place: the clock that the gate reads
        is the clock that the sleep moves.
    """

    def __init__(
        self,
        events: FakeReconnectReader,
        statistics: FakeStatisticsReader,
        settle_gate: phase_gate.DeviceGate | None = None,
        deadline_seconds: int = phase_gate.PHASE_DEADLINE_SECONDS,
    ) -> None:
        """Build one harness.

        Args:
            events: The reconnect source.
            statistics: The fleet statistics source.
            settle_gate: The device rules. The real gate when none is passed.
            deadline_seconds: The time limit of the phase.
        """
        self.sleeper = FakeSleep()
        self.reporter = RecordingReporter()
        self.events = events
        self.statistics = statistics
        self.adapter = self._build(settle_gate, deadline_seconds)

    @property
    def clock(self) -> FakeClock:
        """Return the one clock of the harness.

        Returns:
            The clock that the sleep moves and the gate reads.
        """
        return self.sleeper.clock

    def _build(self, settle_gate: phase_gate.DeviceGate | None, deadline_seconds: int) -> phase_gate.PhaseSettleGate:
        """Wire the dependencies into one phase gate.

        Args:
            settle_gate: The device rules. The real gate when none is passed.
            deadline_seconds: The time limit of the phase.

        Returns:
            The phase gate under test.
        """
        deps = phase_gate.PhaseGateDeps(
            event_reader=self.events,
            statistics_reader=self.statistics,
            settle_gate=settle_gate or gate.SettleGate(clock=self.clock),
            progress=self.reporter,
            sleep=self.sleeper,
        )
        return phase_gate.PhaseSettleGate(deps, deadline_seconds)


def target_entry(mac: str, device_type: str = "switch", uptime_before: int | None = UPTIME_BEFORE) -> dict[str, Any]:
    """Build one target entry of the run record.

    Args:
        mac: The device address.
        device_type: The family of the device.
        uptime_before: The uptime before the upgrade. None when it was unread.

    Returns:
        One entry of the ``targets`` list of the run record.
    """
    return {
        "mac": mac,
        "name": f"fake-{mac}",
        "device_type": device_type,
        "version_before": VERSION_BEFORE,
        "version_target": VERSION_AFTER,
        "uptime_before": uptime_before,
    }


def rebooted_readings(*macs: str) -> dict[str, gate.GateReading]:
    """Build a fleet reading that proves a reboot for each named device.

    Args:
        macs: The addresses that rebooted.

    Returns:
        One reading for each address.
    """
    return {mac: gate.GateReading(mac=mac, version=VERSION_AFTER, uptime=UPTIME_AFTER_FAST_REBOOT) for mac in macs}


def switch_harness(**kwargs: Any) -> Harness:
    """Build a harness whose one switch reconnects from the first round.

    Args:
        kwargs: Extra arguments for the harness.

    Returns:
        The harness.
    """
    events = FakeReconnectReader([[SWITCH_MAC]])
    return Harness(events, FakeStatisticsReader(rebooted_readings(SWITCH_MAC)), **kwargs)


# --- The two ends of the wait -------------------------------------------


def test_a_phase_settles_on_the_first_poll() -> None:
    """A phase whose devices are already back returns after one round."""
    sleeper_clock = FakeClock()
    harness = Harness(FakeReconnectReader(), FakeStatisticsReader(), AlwaysSettledGate(sleeper_clock))
    outcome = harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)])
    assert outcome == PhaseOutcome("switches", PhaseState.SETTLED.value, 1, 1)
    assert harness.events.calls == 1
    assert harness.statistics.calls == 1
    assert harness.sleeper.calls == []


def test_a_phase_settles_after_several_polls() -> None:
    """A switch settles on the round that follows its 60-second wait."""
    harness = switch_harness()
    outcome = harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)])
    assert outcome == PhaseOutcome("switches", PhaseState.SETTLED.value, 1, 1)
    assert harness.events.calls == SWITCH_SETTLE_ROUNDS
    assert harness.sleeper.calls == [float(gate.POLL_INTERVAL_SECONDS)] * (SWITCH_SETTLE_ROUNDS - 1)
    assert harness.clock() == START_TIME + float(gate.SETTLE_WAIT_SECONDS)


def test_a_phase_that_hits_the_deadline_reports_the_devices_that_returned() -> None:
    """The limit stops the wait and the counts name who came back."""
    events = FakeReconnectReader([[SWITCH_MAC]])
    harness = Harness(events, FakeStatisticsReader(rebooted_readings(SWITCH_MAC)))
    targets = [target_entry(SWITCH_MAC), target_entry(SECOND_SWITCH_MAC)]
    outcome = harness.adapter.settle(RUN_ID, "switches", targets)
    assert outcome == PhaseOutcome("switches", PhaseState.FAILED.value, 1, 2, (SECOND_SWITCH_MAC,))
    assert harness.events.calls == phase_gate.polls_per_phase()


def test_a_phase_that_hits_the_deadline_names_each_device_that_stayed_out() -> None:
    """FR-047 asks the portal to mark each device that never returned.

    The address reaches the driver in the outcome. A log line alone would leave
    the driver with nothing to mark, so the run record would hold no per-device
    proof that the device stayed out.
    """
    events = FakeReconnectReader([[SWITCH_MAC]])
    harness = Harness(events, FakeStatisticsReader(rebooted_readings(SWITCH_MAC)))
    targets = [target_entry(SWITCH_MAC), target_entry(SECOND_SWITCH_MAC)]
    outcome = harness.adapter.settle(RUN_ID, "switches", targets)
    assert outcome.not_returned == (SECOND_SWITCH_MAC,)
    assert harness.clock() == START_TIME + float(phase_gate.PHASE_DEADLINE_SECONDS)


def test_an_empty_phase_settles_at_once() -> None:
    """A phase with no device target needs no poll and no wait."""
    harness = Harness(FakeReconnectReader(), FakeStatisticsReader())
    outcome = harness.adapter.settle(RUN_ID, "clients", [])
    assert outcome == PhaseOutcome("clients", PhaseState.SETTLED.value, 0, 0)
    assert harness.events.calls == 0
    assert harness.statistics.calls == 0
    assert harness.sleeper.calls == []
    assert harness.reporter.reports == [phase_gate.PhaseProgress(RUN_ID, "clients", 0, 0)]


def test_an_access_point_phase_waits_one_further_minute() -> None:
    """An access point phase takes three more rounds than a switch phase."""
    events = FakeReconnectReader([[ACCESS_POINT_MAC]])
    harness = Harness(events, FakeStatisticsReader(rebooted_readings(ACCESS_POINT_MAC)))
    outcome = harness.adapter.settle(RUN_ID, "aps", [target_entry(ACCESS_POINT_MAC, "ap")])
    assert outcome == PhaseOutcome("aps", PhaseState.SETTLED.value, 1, 1)
    assert harness.events.calls == ACCESS_POINT_SETTLE_ROUNDS
    assert harness.clock() == START_TIME + float(gate.SETTLE_WAIT_SECONDS + gate.ACCESS_POINT_EXTRA_WAIT_SECONDS)


def test_the_access_point_wait_costs_exactly_three_more_rounds() -> None:
    """The extra minute of an access point is 60 seconds and no more."""
    extra_rounds = ACCESS_POINT_SETTLE_ROUNDS - SWITCH_SETTLE_ROUNDS
    assert extra_rounds * gate.POLL_INTERVAL_SECONDS == gate.ACCESS_POINT_EXTRA_WAIT_SECONDS


# --- A failed read --------------------------------------------------------


def test_a_statistics_read_that_raises_costs_one_round() -> None:
    """A broken statistics read loses one round and the phase still settles."""
    events = FakeReconnectReader([[SWITCH_MAC]])
    statistics = FakeStatisticsReader(rebooted_readings(SWITCH_MAC), fail_rounds=[1])
    harness = Harness(events, statistics)
    outcome = harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)])
    assert outcome.state == PhaseState.SETTLED.value
    assert harness.statistics.calls == ROUNDS_AFTER_ONE_FAILED_READ


def test_a_statistics_read_that_always_raises_reaches_the_deadline() -> None:
    """A statistics source that never answers ends at the limit, not in a hang.

    Why:
        The outcome names the source that the portal could not read. An operator
        who sees a failed phase with no cause has no next step.
    """
    events = FakeReconnectReader([[SWITCH_MAC]])
    statistics = FakeStatisticsReader(fail_rounds=range(1, phase_gate.polls_per_phase() + 1))
    harness = Harness(events, statistics)
    outcome = harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)])
    expected = PhaseOutcome(
        "switches", PhaseState.FAILED.value, 0, 1, (SWITCH_MAC,), phase_gate.NOTE_STATISTICS_READ_FAILED
    )
    assert outcome == expected
    assert harness.statistics.calls == phase_gate.polls_per_phase()


def test_an_event_read_that_raises_costs_one_round() -> None:
    """A broken event read loses one round and the phase still settles."""
    events = FakeReconnectReader([[SWITCH_MAC]], fail_rounds=[1])
    harness = Harness(events, FakeStatisticsReader(rebooted_readings(SWITCH_MAC)))
    outcome = harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)])
    assert outcome.state == PhaseState.SETTLED.value
    assert harness.events.calls == ROUNDS_AFTER_ONE_FAILED_READ


def test_an_event_source_that_never_answers_names_the_events() -> None:
    """A phase that lost every event read reports the event source.

    Why:
        The two sources fail apart. The note must name the one that went quiet,
        so the operator looks at the right place.
    """
    events = FakeReconnectReader([], fail_rounds=range(1, phase_gate.polls_per_phase() + 1))
    harness = Harness(events, FakeStatisticsReader(rebooted_readings(SWITCH_MAC)))
    outcome = harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)])
    assert outcome.state == PhaseState.FAILED.value
    assert outcome.note == phase_gate.NOTE_EVENT_READ_FAILED


def test_both_sources_that_fail_name_both_sources() -> None:
    """A round that lost both reads reports both of them.

    Why:
        A cloud that answers nothing at all is a different fault from one
        endpoint that went quiet, and the note must show the difference.
    """
    rounds = range(1, phase_gate.polls_per_phase() + 1)
    harness = Harness(FakeReconnectReader([], fail_rounds=rounds), FakeStatisticsReader(fail_rounds=rounds))
    outcome = harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)])
    assert outcome.note == f"{phase_gate.NOTE_EVENT_READ_FAILED} {phase_gate.NOTE_STATISTICS_READ_FAILED}"


def test_partial_statistics_never_stop_the_run() -> None:
    """A partial read still carries the readings that it holds."""
    reasons = [{"section": gate.SECTION_GATE_STATISTICS, "reason": "page_count_mismatch", "http_status": 200}]
    statistics = FakeStatisticsReader(rebooted_readings(SWITCH_MAC), partial_reasons=reasons)
    harness = Harness(FakeReconnectReader([[SWITCH_MAC]]), statistics)
    outcome = harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)])
    assert outcome.state == PhaseState.SETTLED.value
    assert outcome.note == ""  # A phase that settled needs no cause.


def test_a_phase_that_timed_out_on_partial_reads_says_so() -> None:
    """A read that answered in part reports a part, never a whole fault.

    Why:
        The two words lead to different work. A partial read means some devices
        answered, so the operator looks at the named devices first.
    """
    reasons = [{"section": gate.SECTION_GATE_STATISTICS, "reason": "page_count_mismatch", "http_status": 200}]
    # WHY: The version and the uptime both hold, so the gate proves no reboot and waits to the limit.
    stale = {SWITCH_MAC: gate.GateReading(mac=SWITCH_MAC, version=VERSION_BEFORE, uptime=UPTIME_BEFORE)}
    harness = Harness(FakeReconnectReader([[SWITCH_MAC]]), FakeStatisticsReader(stale, partial_reasons=reasons))
    outcome = harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)])
    assert outcome.state == PhaseState.FAILED.value
    assert outcome.note == phase_gate.NOTE_STATISTICS_PARTIAL


# --- The call budget ------------------------------------------------------


def test_the_round_makes_exactly_two_cloud_calls() -> None:
    """One round reads the events once and the statistics once."""
    harness = switch_harness()
    harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)])
    assert harness.events.calls == harness.statistics.calls
    assert harness.events.calls + harness.statistics.calls == SWITCH_SETTLE_ROUNDS * phase_gate.CALLS_PER_ROUND


def test_the_device_count_never_changes_the_call_count() -> None:
    """A phase of many devices costs the same two calls in each round."""
    events = FakeReconnectReader([[SWITCH_MAC, SECOND_SWITCH_MAC]])
    statistics = FakeStatisticsReader(rebooted_readings(SWITCH_MAC, SECOND_SWITCH_MAC))
    harness = Harness(events, statistics)
    targets = [target_entry(SWITCH_MAC), target_entry(SECOND_SWITCH_MAC)]
    outcome = harness.adapter.settle(RUN_ID, "switches", targets)
    assert outcome == PhaseOutcome("switches", PhaseState.SETTLED.value, 2, 2)
    assert harness.statistics.calls == SWITCH_SETTLE_ROUNDS


def test_a_whole_phase_holds_the_documented_call_budget() -> None:
    """A phase that runs to its limit stays inside the hourly call cap."""
    assert phase_gate.polls_per_phase() == 90
    assert phase_gate.calls_per_phase() == 180
    hourly = phase_gate.calls_per_phase() * gate.SECONDS_PER_HOUR // phase_gate.PHASE_DEADLINE_SECONDS
    assert hourly == gate.MAX_CALLS_PER_HOUR
    assert hourly < gate.HOURLY_CALL_QUOTA * 0.08


def test_the_deadline_is_a_whole_number_of_rounds() -> None:
    """The limit divides by the poll interval, so no round falls outside it."""
    assert phase_gate.PHASE_DEADLINE_SECONDS % gate.POLL_INTERVAL_SECONDS == 0


def test_a_zero_deadline_is_refused() -> None:
    """A phase limit of zero seconds is not a limit."""
    with pytest.raises(ValueError):
        phase_gate.polls_per_phase(0)


# --- The device family of the poll ----------------------------------------


def test_the_event_poll_names_the_family_of_the_phase() -> None:
    """The poll always names the family, because the cloud defaults it to ap."""
    harness = switch_harness()
    harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)])
    assert set(harness.events.families) == {"switch"}


def test_a_gateway_phase_polls_the_gateway_family() -> None:
    """A gateway phase reads gateway events and not access point events."""
    events = FakeReconnectReader([[SWITCH_MAC]])
    harness = Harness(events, FakeStatisticsReader(rebooted_readings(SWITCH_MAC)))
    harness.adapter.settle(RUN_ID, "gateways", [target_entry(SWITCH_MAC, "gateway")])
    assert set(harness.events.families) == {"gateway"}


def test_a_phase_of_two_families_is_refused() -> None:
    """A mixed phase raises before the first poll instead of waiting in silence."""
    harness = switch_harness()
    targets = [target_entry(SWITCH_MAC), target_entry(ACCESS_POINT_MAC, "ap")]
    with pytest.raises(phase_gate.PhaseGateError):
        harness.adapter.settle(RUN_ID, "switches", targets)
    assert harness.events.calls == 0


def test_the_family_of_an_empty_phase_is_empty() -> None:
    """A phase with no target names no family."""
    assert phase_gate.phase_family(()) == ""


# --- The progress report --------------------------------------------------


def test_the_operator_sees_progress_during_the_wait() -> None:
    """A report arrives after every round, not once at the end."""
    events = FakeReconnectReader([[], [SWITCH_MAC], [SWITCH_MAC, SECOND_SWITCH_MAC]])
    statistics = FakeStatisticsReader(rebooted_readings(SWITCH_MAC, SECOND_SWITCH_MAC))
    harness = Harness(events, statistics)
    targets = [target_entry(SWITCH_MAC), target_entry(SECOND_SWITCH_MAC)]
    outcome = harness.adapter.settle(RUN_ID, "switches", targets)
    assert outcome.state == PhaseState.SETTLED.value
    assert [report.settled for report in harness.reporter.reports] == [0, 0, 0, 0, 1, 2]
    assert {report.total for report in harness.reporter.reports} == {2}


def test_every_progress_report_names_the_run_and_the_phase() -> None:
    """The operator sees which run and which phase the counts belong to."""
    harness = switch_harness()
    harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)])
    assert {(report.run_id, report.phase) for report in harness.reporter.reports} == {(RUN_ID, "switches")}


# --- The target builder ---------------------------------------------------


def test_a_target_with_no_address_is_dropped() -> None:
    """An entry with no usable address matches every other malformed entry."""
    built = phase_gate.build_targets([target_entry(SWITCH_MAC), {"device_type": "switch"}])
    assert [target.mac for target in built] == [SWITCH_MAC]


def test_a_target_address_takes_the_shared_form() -> None:
    """The builder uses the one address rule of the capture package."""
    built = phase_gate.build_targets([target_entry("00:11:22:00:00:AA")])
    assert built[0].mac == SWITCH_MAC


def test_a_null_uptime_before_settles_on_the_version_change(caplog: pytest.LogCaptureFixture) -> None:
    """A device with no earlier uptime settles on the version change and says so."""
    caplog.set_level(logging.WARNING)
    events = FakeReconnectReader([[SWITCH_MAC]])
    harness = Harness(events, FakeStatisticsReader(rebooted_readings(SWITCH_MAC)))
    outcome = harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC, uptime_before=None)])
    assert outcome == PhaseOutcome("switches", PhaseState.SETTLED.value, 1, 1)
    assert any(SWITCH_MAC in record.getMessage() for record in caplog.records)


def test_a_null_uptime_before_reaches_the_gate_unchanged() -> None:
    """The gate reads the null itself, so the builder never invents a zero."""
    built = phase_gate.build_targets([target_entry(SWITCH_MAC, uptime_before=None)])
    assert built[0].uptime_before is None


# --- The seam with the driver ---------------------------------------------


def test_the_adapter_answers_with_the_record_the_driver_writes() -> None:
    """The answer is the driver record, so the driver writes it unchanged."""
    harness = switch_harness()
    outcome = harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)])
    assert isinstance(outcome, PhaseOutcome)
    assert (outcome.name, outcome.settled, outcome.total) == ("switches", 1, 1)


def test_the_adapter_fills_the_driver_protocol() -> None:
    """The concrete class meets the shape that the driver calls."""
    harness = switch_harness()
    driver_gate = phase_gate.as_phase_gate(harness.adapter)
    assert driver_gate is harness.adapter
    assert driver_gate.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)]).total == 1


def test_a_settled_device_is_never_observed_again() -> None:
    """The loop skips a device that already returned."""
    events = FakeReconnectReader([[SWITCH_MAC, SECOND_SWITCH_MAC]])
    statistics = FakeStatisticsReader(rebooted_readings(SWITCH_MAC))
    harness = Harness(events, statistics, deadline_seconds=gate.POLL_INTERVAL_SECONDS * 10)
    targets = [target_entry(SWITCH_MAC), target_entry(SECOND_SWITCH_MAC)]
    outcome = harness.adapter.settle(RUN_ID, "switches", targets)
    assert outcome == PhaseOutcome("switches", PhaseState.FAILED.value, 1, 2, (SECOND_SWITCH_MAC,))


# --- The proof that no test waits -----------------------------------------


def test_a_whole_deadline_phase_costs_no_real_time() -> None:
    """A phase that asks for 30 minutes of waiting finishes in milliseconds."""
    harness = Harness(FakeReconnectReader(), FakeStatisticsReader())
    started = time.monotonic()
    outcome = harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)])
    elapsed = time.monotonic() - started
    assert outcome.state == PhaseState.FAILED.value
    assert sum(harness.sleeper.calls) == float(phase_gate.PHASE_DEADLINE_SECONDS)
    assert elapsed < REAL_TIME_LIMIT_SECONDS


def test_the_loop_stops_even_when_the_clock_stands_still() -> None:
    """A clock that never moves still ends the wait at the round ceiling."""
    harness = Harness(FakeReconnectReader(), FakeStatisticsReader())
    harness.sleeper.clock.advance = lambda seconds: None  # type: ignore[method-assign]
    outcome = harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)])
    assert outcome.state == PhaseState.FAILED.value
    assert harness.events.calls == phase_gate.polls_per_phase()
    assert harness.clock() == START_TIME


def test_the_default_sleep_is_the_real_sleep() -> None:
    """The portal waits for real, and only a test passes a fake wait."""
    deps = phase_gate.PhaseGateDeps(FakeReconnectReader(), FakeStatisticsReader())
    assert deps.sleep is time.sleep


def test_the_loop_asks_for_the_documented_poll_interval() -> None:
    """The wait between two rounds is the interval that the gate module holds."""
    harness = switch_harness()
    harness.adapter.settle(RUN_ID, "switches", [target_entry(SWITCH_MAC)])
    assert set(harness.sleeper.calls) == {float(gate.POLL_INTERVAL_SECONDS)}
