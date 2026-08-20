"""Unit tests for the stale statistics rule of the settle gate.

Why:
    FR-046 at ``spec.md:525`` asks the portal to ignore a device statistics
    record that is older than the upgrade. The cloud can serve a copy that it
    cached before the reboot, and that copy holds the old uptime and the old
    version together. Read at the wrong moment it settles a device that never
    rebooted, or it delays a device that did reboot. Neither fault raises an
    error, so a test is the only guard.

    Two traps sit under this rule, and both fail quietly.

    The first trap is the clock. FR-045 at ``spec.md:523`` forbids a
    comparison between a cloud timestamp and the local clock, because the two
    machines keep separate clocks. The tests below prove that the rule reads
    only cloud values, so a fake clock far from the record values changes
    nothing.

    The second trap is the missing value. A record with no ``last_seen`` must
    pass, because an absent value is no evidence. A gate that read a null as
    stale would drop every record of that device and would wait to the phase
    deadline every time.

    Every test drives a fake clock forward. No test sleeps, and no test opens
    a socket or names a real credential.
"""

from __future__ import annotations

import logging

import pytest

from src.upgrade_portal.upgrade import gate

# WHY: Obviously fake identifiers. A reader sees at once that no test reaches
#      a real organization, a real site, or a real device.
SWITCH_MAC = "0011220000aa"
ACCESS_POINT_MAC = "0011220000bb"

VERSION_BEFORE = "23.4R2.13"
VERSION_AFTER = "23.4R2-S3.9"

# WHY: A device that ran for 21 days before the upgrade started.
UPTIME_BEFORE = 1832140

# WHY: A small positive uptime, never zero. A device that reboots quickly
#      already reports a small positive uptime when the poll reads it.
UPTIME_AFTER = 45

# WHY: Two cloud moments in epoch seconds. The cached copy carries the earlier
#      moment, and the fresh record carries the later one. The gap is 10
#      minutes, which is far wider than any poll round.
LAST_SEEN_CACHED = 1470417522
LAST_SEEN_FRESH = 1470418122

# WHY: The local clock of the test sits nowhere near the cloud moments above.
#      A rule that compared a cloud value against this clock would report every
#      record as stale, so this value is the guard for FR-045.
LOCAL_CLOCK_START = 1000.0


class FakeClock:
    """A clock that a test drives forward with no real wait.

    Why:
        The gate waits 60 seconds for a switch and 120 seconds for an access
        point. A test that used the real clock would run for two minutes for
        one case. This clock returns whatever the test set, so the same case
        runs in microseconds.
    """

    def __init__(self, start: float = LOCAL_CLOCK_START) -> None:
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


def _switch_target(uptime_before: int | None = UPTIME_BEFORE) -> gate.GateTarget:
    """Build one switch target for the tests below.

    Why:
        Every test needs the same device state from before the upgrade. One
        builder keeps that state in one place, and the uptime stays a
        parameter because the version-only path needs a null.

    Args:
        uptime_before: The uptime read before the upgrade, or None.

    Returns:
        The target record of one switch.
    """
    return gate.GateTarget(
        mac=SWITCH_MAC,
        device_type="switch",
        version_before=VERSION_BEFORE,
        uptime_before=uptime_before,
    )


def _rebooted_reading(last_seen: int | None) -> gate.GateReading:
    """Build one reading that shows the reboot of the switch.

    Why:
        The reboot rule needs a fallen uptime and a changed version together.
        Every test below varies only the cloud moment, so one builder holds
        the two halves that must stay fixed.

    Args:
        last_seen: The cloud moment of the record, or None.

    Returns:
        The reading of one rebooted switch.
    """
    return gate.GateReading(
        mac=SWITCH_MAC,
        version=VERSION_AFTER,
        uptime=UPTIME_AFTER,
        last_seen=last_seen,
    )


def _opened_progress(last_seen_at: int | None) -> gate.GateProgress:
    """Build the progress of one device that already reconnected.

    Why:
        The gate reads statistics only after the reconnect event, so every
        staleness test must start past that signal. The mark is a parameter,
        because a test either seeds it or leaves it empty.

    Args:
        last_seen_at: The highest cloud moment the gate already read, or None.

    Returns:
        The progress record of one device that waits for its statistics.
    """
    return gate.GateProgress(reconnected=True, last_seen_at=last_seen_at)


class TestReadingIsStale:
    """The staleness predicate on its own.

    Why:
        The predicate holds the whole rule, so a fault here reaches every
        caller. Testing it apart from the gate names the failure exactly.
    """

    def test_an_older_moment_is_stale(self) -> None:
        """A record that predates the highest moment already read is stale."""
        assert gate.reading_is_stale(LAST_SEEN_FRESH, LAST_SEEN_CACHED) is True

    def test_an_equal_moment_is_stale(self) -> None:
        """A record that repeats the highest moment carries no new evidence.

        Why:
            The cloud serves the same snapshot on two polls. The second copy
            proves nothing that the first did not prove already.
        """
        assert gate.reading_is_stale(LAST_SEEN_FRESH, LAST_SEEN_FRESH) is True

    def test_a_newer_moment_is_fresh(self) -> None:
        """A record with a later moment is the newer snapshot."""
        assert gate.reading_is_stale(LAST_SEEN_CACHED, LAST_SEEN_FRESH) is False

    @pytest.mark.parametrize(
        ("before", "now"),
        [
            (None, LAST_SEEN_CACHED),
            (LAST_SEEN_FRESH, None),
            (None, None),
        ],
    )
    def test_a_missing_moment_is_never_stale(self, before: int | None, now: int | None) -> None:
        """A null on either side answers False, because it proves nothing.

        Why:
            This is the second trap. A gate that read a null as stale would
            drop every record of that device and would wait to the phase
            deadline. The rule follows ``uptime_decreased`` at ``gate.py:281``,
            where a null uptime proves nothing.

        Args:
            before: The mark that the gate holds, or None.
            now: The moment of the current record, or None.
        """
        assert gate.reading_is_stale(before, now) is False


class TestReadingLastSeen:
    """The reader that maps the raw ``last_seen`` value onto a number."""

    def test_it_reads_a_whole_number(self) -> None:
        """The reader returns the moment that the cloud reported."""
        assert gate.reading_last_seen(LAST_SEEN_FRESH) == LAST_SEEN_FRESH

    @pytest.mark.parametrize("value", [None, "", "never", [], {}])
    def test_it_maps_an_unusable_value_onto_none(self, value: object) -> None:
        """A value that holds no number reads as no reading at all.

        Why:
            A reader that turned an unusable value into zero would date the
            record at the start of the epoch. Every later record would then
            look newer, and the staleness rule would never fire.

        Args:
            value: The raw value that the record carried.
        """
        assert gate.reading_last_seen(value) is None

    def test_it_keeps_zero_apart_from_none(self) -> None:
        """A reported zero stays a number, because it is a real reading."""
        assert gate.reading_last_seen(0) == 0


class TestReadingFromRecord:
    """The builder that turns one statistics record into one reading."""

    def test_it_keeps_the_last_seen_value(self) -> None:
        """The builder carries the cloud moment onto the reading."""
        record = {"mac": SWITCH_MAC, "version": VERSION_AFTER, "uptime": UPTIME_AFTER, "last_seen": LAST_SEEN_FRESH}
        reading = gate.reading_from_record(record)
        assert reading is not None
        assert reading.last_seen == LAST_SEEN_FRESH

    def test_a_record_with_no_last_seen_reads_as_none(self) -> None:
        """A record that omits the field builds a reading with no moment.

        Why:
            The field is nullable in the vendor schema, so the builder must
            never invent a value. The gate then treats the record as undated.
        """
        record = {"mac": SWITCH_MAC, "version": VERSION_AFTER, "uptime": UPTIME_AFTER}
        reading = gate.reading_from_record(record)
        assert reading is not None
        assert reading.last_seen is None

    def test_the_statistics_fields_ask_for_last_seen(self) -> None:
        """The poll asks the cloud for the field that dates every record.

        Why:
            The gate cannot apply FR-046 to a record that carries no moment.
            The vendor treats ``fields`` as a list of additional names, so the
            base answer already holds the value, and naming it is the guard
            that keeps the value present.
        """
        assert "last_seen" in gate.STATISTICS_FIELDS.split(",")


class TestStaleRecordAtTheGate:
    """The staleness rule inside ``advance``.

    Why:
        The predicate can be right while the wiring is wrong. These tests
        drive the whole gate, so they prove that a stale record reaches no
        rule and that a fresh record still settles the device.
    """

    def test_a_cached_record_never_settles_a_device(self) -> None:
        """A copy cached before the reboot moves no signal of the gate.

        Why:
            This is the fault that FR-046 prevents. The record shows the new
            version and a fallen uptime, so it would satisfy the reboot rule.
            The gate must reject it because the cloud moment did not rise.
        """
        clock = FakeClock()
        settle = gate.SettleGate(clock)
        progress = _opened_progress(LAST_SEEN_FRESH)
        signals = gate.GateSignals(reconnected=True, reading=_rebooted_reading(LAST_SEEN_CACHED))
        result = settle.observe(_switch_target(), progress, signals)
        assert result.reboot_at is None
        assert result.version_after is None

    def test_a_cached_record_never_settles_a_device_with_no_earlier_uptime(self) -> None:
        """The version-only path also rejects a record that repeats a snapshot.

        Why:
            A device with no earlier uptime settles on the version change
            alone at ``gate.py:501``. That path is the weakest one, so a stale
            record with a changed version would settle a device that never
            rebooted. The screen runs before that path.
        """
        clock = FakeClock()
        settle = gate.SettleGate(clock)
        progress = _opened_progress(LAST_SEEN_FRESH)
        signals = gate.GateSignals(reconnected=True, reading=_rebooted_reading(LAST_SEEN_CACHED))
        result = settle.observe(_switch_target(uptime_before=None), progress, signals)
        assert result.reboot_at is None

    def test_a_fresh_record_settles_the_device(self) -> None:
        """A record with a later cloud moment still proves the reboot."""
        clock = FakeClock()
        settle = gate.SettleGate(clock)
        progress = _opened_progress(LAST_SEEN_CACHED)
        signals = gate.GateSignals(reconnected=True, reading=_rebooted_reading(LAST_SEEN_FRESH))
        result = settle.observe(_switch_target(), progress, signals)
        assert result.reboot_at == LOCAL_CLOCK_START
        assert result.version_after == VERSION_AFTER

    def test_a_fresh_record_raises_the_mark(self) -> None:
        """The gate records the moment of every record that it accepts.

        Why:
            The mark is the baseline of the next round. A gate that never
            raised it would compare every later record against the first
            moment and would accept a copy that the cloud cached after it.
        """
        clock = FakeClock()
        settle = gate.SettleGate(clock)
        progress = _opened_progress(LAST_SEEN_CACHED)
        signals = gate.GateSignals(reconnected=True, reading=_rebooted_reading(LAST_SEEN_FRESH))
        result = settle.observe(_switch_target(), progress, signals)
        assert result.last_seen_at == LAST_SEEN_FRESH

    def test_a_stale_record_leaves_the_mark_alone(self) -> None:
        """A rejected record never lowers the highest moment already read."""
        clock = FakeClock()
        settle = gate.SettleGate(clock)
        progress = _opened_progress(LAST_SEEN_FRESH)
        signals = gate.GateSignals(reconnected=True, reading=_rebooted_reading(LAST_SEEN_CACHED))
        result = settle.observe(_switch_target(), progress, signals)
        assert result.last_seen_at == LAST_SEEN_FRESH

    def test_a_record_with_no_moment_still_settles_the_device(self) -> None:
        """An undated record reaches the reboot rule and proves the reboot.

        Why:
            This is the second trap at the gate. A device whose records carry
            no moment must still settle. A gate that dropped those records
            would wait to the phase deadline for that device on every run.
        """
        clock = FakeClock()
        settle = gate.SettleGate(clock)
        progress = _opened_progress(LAST_SEEN_FRESH)
        signals = gate.GateSignals(reconnected=True, reading=_rebooted_reading(None))
        result = settle.observe(_switch_target(), progress, signals)
        assert result.reboot_at == LOCAL_CLOCK_START
        assert result.last_seen_at == LAST_SEEN_FRESH

    def test_the_first_record_of_a_device_is_never_stale(self) -> None:
        """A device with no mark accepts its first record.

        Why:
            The gate holds no baseline before the first record arrives, and an
            absent baseline is no evidence of age.
        """
        clock = FakeClock()
        settle = gate.SettleGate(clock)
        progress = _opened_progress(None)
        signals = gate.GateSignals(reconnected=True, reading=_rebooted_reading(LAST_SEEN_CACHED))
        result = settle.observe(_switch_target(), progress, signals)
        assert result.reboot_at == LOCAL_CLOCK_START
        assert result.last_seen_at == LAST_SEEN_CACHED

    def test_the_rule_reads_no_local_clock(self) -> None:
        """The verdict does not change when the local clock moves far away.

        Why:
            This is the FR-045 guard. The cloud moments sit near 1.47 billion
            seconds and this clock sits near one thousand. A rule that
            compared the two would call every record stale. The gate must
            reach the same verdict whatever the local clock reads.
        """
        readings = [_rebooted_reading(LAST_SEEN_FRESH), _rebooted_reading(LAST_SEEN_CACHED)]
        verdicts = []
        for start in (LOCAL_CLOCK_START, float(LAST_SEEN_FRESH * 2)):
            settle = gate.SettleGate(FakeClock(start))
            signals = gate.GateSignals(reconnected=True, reading=readings[1])
            verdicts.append(settle.observe(_switch_target(), _opened_progress(LAST_SEEN_FRESH), signals).reboot_at)
        assert verdicts == [None, None]

    def test_a_round_with_no_record_leaves_the_mark_alone(self) -> None:
        """A poll that returned nothing for this device changes no mark."""
        clock = FakeClock()
        settle = gate.SettleGate(clock)
        progress = _opened_progress(LAST_SEEN_FRESH)
        result = settle.observe(_switch_target(), progress, gate.GateSignals(reconnected=True, reading=None))
        assert result.last_seen_at == LAST_SEEN_FRESH
        assert result.reboot_at is None

    def test_the_gate_reads_no_statistics_before_the_reconnect(self) -> None:
        """A device that never reconnected keeps its mark empty.

        Why:
            The reconnect event opens the gate, so the screen must not run
            before it. A mark raised early would reject the first record that
            arrives after the event.
        """
        clock = FakeClock()
        settle = gate.SettleGate(clock)
        signals = gate.GateSignals(reconnected=False, reading=_rebooted_reading(LAST_SEEN_FRESH))
        result = settle.observe(_switch_target(), gate.GateProgress(), signals)
        assert result.last_seen_at is None
        assert result.reboot_at is None


class TestStaleRecordLogging:
    """The log line that a dropped record writes."""

    def test_a_dropped_record_logs_the_address_only(self, caplog: pytest.LogCaptureFixture) -> None:
        """The gate names the device and never writes the whole record.

        Why:
            A statistics record holds many fields, and a log line that carried
            all of them would fill the log of a large phase. The address is
            enough to find the device.

        Args:
            caplog: The log capture fixture of pytest.
        """
        settle = gate.SettleGate(FakeClock())
        signals = gate.GateSignals(reconnected=True, reading=_rebooted_reading(LAST_SEEN_CACHED))
        with caplog.at_level(logging.DEBUG, logger="src.upgrade_portal.upgrade.gate"):
            settle.observe(_switch_target(), _opened_progress(LAST_SEEN_FRESH), signals)
        messages = [record.getMessage() for record in caplog.records]
        assert any(SWITCH_MAC in message and "stale" in message for message in messages)
        assert not any(VERSION_AFTER in message for message in messages)


class TestAccessPointStillWaitsLonger:
    """The settle wait stays untouched by the staleness rule.

    Why:
        The screen sits before the reboot rule, so it must not change the
        waits that follow. This test guards that boundary.
    """

    def test_an_access_point_settles_after_the_longer_wait(self) -> None:
        """The access point still waits 120 seconds after a fresh record."""
        clock = FakeClock()
        settle = gate.SettleGate(clock)
        target = gate.GateTarget(
            mac=ACCESS_POINT_MAC,
            device_type=gate.DEVICE_TYPE_ACCESS_POINT,
            version_before=VERSION_BEFORE,
            uptime_before=UPTIME_BEFORE,
        )
        reading = gate.GateReading(ACCESS_POINT_MAC, VERSION_AFTER, UPTIME_AFTER, LAST_SEEN_FRESH)
        progress = settle.observe(target, _opened_progress(LAST_SEEN_CACHED), gate.GateSignals(True, reading))
        assert progress.reboot_at == LOCAL_CLOCK_START
        clock.advance(gate.SETTLE_WAIT_SECONDS + gate.ACCESS_POINT_EXTRA_WAIT_SECONDS)
        settled = settle.observe(target, progress, gate.GateSignals(reconnected=True))
        assert gate.is_settled(settled) is True
