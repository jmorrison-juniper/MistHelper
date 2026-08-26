"""Unit tests for the absolute reboot anchor of the settle gate.

Why:
    The gate decides that a device rebooted when the uptime falls and the
    firmware version changes together. The vendor marks ``uptime`` nullable, so
    a device can return on the new firmware and report no uptime at all. The
    fall test then answers False on every round, the device never settles, and
    the phase waits the full 30 minutes at ``PHASE_DEADLINE_SECONDS``.

    The anchor closes that hole. The cloud raises ``last_seen`` each time the
    device reports, so a moment later than the pre-check moment proves that the
    device returned. Both values are cloud moments for the same device, so the
    test reads no local clock, which FR-045 at ``spec.md:523`` requires.

    The anchor only adds a way to prove a reboot. It never removes the uptime
    path, and it never turns a missing value into proof. The tests below hold
    both halves of that rule, because a gate that settled on an absent value
    would report a device that never rebooted as upgraded.

    Every test drives a fake clock forward. No test sleeps, no test opens a
    socket, and no test names a real credential.
"""

from __future__ import annotations

import logging

import pytest

from src.firmware import upgrade_service
from src.upgrade_portal.upgrade import gate, options, phase_gate

# WHY: Obviously fake identifiers. A reader sees at once that no test reaches a
#      real organization, a real site, or a real device.
SWITCH_MAC = "0011220000aa"
SWITCH_MAC_RAW = "00:11:22:00:00:AA"

VERSION_BEFORE = "23.4R2.13"
VERSION_AFTER = "23.4R2-S3.9"

# WHY: A device that ran for 21 days before the upgrade started.
UPTIME_BEFORE = 1832140

# WHY: A small positive uptime, never zero. A device that reboots quickly
#      already reports a small positive uptime when the poll reads it.
UPTIME_AFTER = 45

# WHY: A larger uptime than the pre-check value. A device that reports this
#      value did not reboot, so it is the guard that the anchor never overrules
#      a real reading.
UPTIME_RISEN = UPTIME_BEFORE + 100

# WHY: Two cloud moments in epoch seconds. The pre-check holds the earlier
#      moment, and the record after the reboot holds the later one.
LAST_SEEN_BEFORE = 1470417522
LAST_SEEN_AFTER = 1470418122

# WHY: The local clock of the test sits nowhere near the cloud moments above. A
#      rule that compared a cloud value against this clock would reach the wrong
#      verdict, so this value is the guard for FR-045.
LOCAL_CLOCK_START = 1000.0

# WHY: The upgrade job values of the status test. The identifier is a fake.
UPGRADE_ID = "0000aaaa-0000-4000-8000-0000000000ff"
START_TIME = 1470417000
HTTP_OK = 200

SWITCH_ROW = {
    "mac": SWITCH_MAC_RAW,
    "name": "fake-switch-1",
    "type": "switch",
    "model": "EX4400-48P",
    "version": VERSION_BEFORE,
    "uptime": UPTIME_BEFORE,
    "last_seen": LAST_SEEN_BEFORE,
}


class FakeClock:
    """A clock that a test drives forward with no real wait.

    Why:
        The gate waits 60 seconds for a switch. A test that used the real clock
        would run for a minute for one case. This clock returns whatever the
        test set, so the same case runs in microseconds.
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


def _target(uptime_before: int | None, last_seen_before: int | None) -> gate.GateTarget:
    """Build one switch target with the two anchors under test.

    Why:
        Every test below varies only the two anchors, so one builder holds the
        address and the firmware version that must stay fixed.

    Args:
        uptime_before: The uptime that the pre-check read, or None.
        last_seen_before: The cloud moment that the pre-check read, or None.

    Returns:
        The target record of one switch.
    """
    return gate.GateTarget(
        mac=SWITCH_MAC,
        device_type="switch",
        version_before=VERSION_BEFORE,
        uptime_before=uptime_before,
        last_seen_before=last_seen_before,
    )


def _reading(uptime: int | None, last_seen: int | None) -> gate.GateReading:
    """Build one reading that reports the new firmware version.

    Why:
        The version half of the reboot rule holds in every test below, because
        each test asks about the second half alone.

    Args:
        uptime: The uptime of the current record, or None.
        last_seen: The cloud moment of the current record, or None.

    Returns:
        The reading of one switch on the new firmware.
    """
    return gate.GateReading(mac=SWITCH_MAC, version=VERSION_AFTER, uptime=uptime, last_seen=last_seen)


def _opened() -> gate.GateProgress:
    """Build the progress of one device that already reconnected.

    Why:
        The gate reads statistics only after the reconnect event, so every test
        below must start past that signal.

    Returns:
        The progress record of one device that waits for its statistics.
    """
    return gate.GateProgress(reconnected=True)


class TestLastSeenAdvanced:
    """The anchor predicate on its own.

    Why:
        The predicate holds the whole anchor rule, so a fault here reaches
        every caller. Testing it apart from the gate names the failure exactly.
    """

    def test_a_later_moment_proves_the_return(self) -> None:
        """The cloud received a report after the pre-check snapshot."""
        assert gate.last_seen_advanced(LAST_SEEN_BEFORE, LAST_SEEN_AFTER) is True

    def test_an_equal_moment_proves_nothing(self) -> None:
        """A repeated moment carries no evidence that the device returned."""
        assert gate.last_seen_advanced(LAST_SEEN_BEFORE, LAST_SEEN_BEFORE) is False

    def test_an_earlier_moment_proves_nothing(self) -> None:
        """A moment before the pre-check snapshot is an older record."""
        assert gate.last_seen_advanced(LAST_SEEN_AFTER, LAST_SEEN_BEFORE) is False

    @pytest.mark.parametrize(
        ("before", "now"),
        [
            (None, LAST_SEEN_AFTER),
            (LAST_SEEN_BEFORE, None),
            (None, None),
        ],
    )
    def test_a_missing_moment_is_never_proof(self, before: int | None, now: int | None) -> None:
        """A null on either side answers False, because it proves nothing.

        Why:
            This is the rule that the anchor must never break. An anchor that
            read a null as proof would settle a device that never rebooted and
            would report a failed upgrade as a success.

        Args:
            before: The moment that the pre-check read, or None.
            now: The moment of the current record, or None.
        """
        assert gate.last_seen_advanced(before, now) is False

    def test_the_rule_reads_no_local_clock(self) -> None:
        """The verdict is the same whatever the local clock reads.

        Why:
            This is the FR-045 guard. The two values are cloud moments for one
            device, so no local reading may reach this rule.
        """
        assert gate.last_seen_advanced(LAST_SEEN_BEFORE, LAST_SEEN_AFTER) is True


class TestANullUptimeSettlesOnTheAnchor:
    """The hole that the anchor closes.

    Why:
        A device that returns on the new firmware and reports no uptime is the
        exact fault of FR-046. Before the anchor that device waited the full
        30 minutes of the phase deadline on every run.
    """

    def test_a_null_uptime_with_a_later_moment_proves_the_reboot(self) -> None:
        """The anchor settles a device that reports no uptime at all."""
        settle = gate.SettleGate(FakeClock())
        signals = gate.GateSignals(reconnected=True, reading=_reading(None, LAST_SEEN_AFTER))
        result = settle.observe(_target(UPTIME_BEFORE, LAST_SEEN_BEFORE), _opened(), signals)
        assert result.reboot_at == LOCAL_CLOCK_START
        assert result.version_after == VERSION_AFTER

    def test_the_device_settles_after_the_wait(self) -> None:
        """The anchor moves the second signal, and the wait still applies.

        Why:
            The anchor proves the reboot. It must not skip the settle wait,
            because the statistics of the device are still arriving.
        """
        clock = FakeClock()
        settle = gate.SettleGate(clock)
        target = _target(UPTIME_BEFORE, LAST_SEEN_BEFORE)
        signals = gate.GateSignals(reconnected=True, reading=_reading(None, LAST_SEEN_AFTER))
        progress = settle.observe(target, _opened(), signals)
        assert gate.is_settled(progress) is False
        clock.advance(gate.SETTLE_WAIT_SECONDS)
        assert gate.is_settled(settle.observe(target, progress, gate.GateSignals(reconnected=True))) is True

    def test_the_anchor_log_names_the_address_only(self, caplog: pytest.LogCaptureFixture) -> None:
        """The gate names the device and never writes the whole record.

        Why:
            A statistics record holds many fields, and a log line that carried
            all of them would fill the log of a large phase.

        Args:
            caplog: The log capture fixture of pytest.
        """
        settle = gate.SettleGate(FakeClock())
        signals = gate.GateSignals(reconnected=True, reading=_reading(None, LAST_SEEN_AFTER))
        with caplog.at_level(logging.DEBUG, logger="src.upgrade_portal.upgrade.gate"):
            settle.observe(_target(UPTIME_BEFORE, LAST_SEEN_BEFORE), _opened(), signals)
        messages = [record.getMessage() for record in caplog.records]
        assert any(SWITCH_MAC in message for message in messages)
        assert not any("{" in message for message in messages)


class TestNoAnchorNeverSettles:
    """The rule that a missing value is never proof.

    Why:
        The anchor adds a path, and it must add nothing else. A device with no
        usable anchor must still wait, because the gate holds no evidence that
        it rebooted.
    """

    @pytest.mark.parametrize(
        ("last_seen_before", "last_seen_now"),
        [
            (None, LAST_SEEN_AFTER),
            (LAST_SEEN_BEFORE, None),
            (None, None),
            (LAST_SEEN_AFTER, LAST_SEEN_BEFORE),
        ],
    )
    def test_a_null_uptime_and_no_anchor_records_no_reboot(
        self,
        last_seen_before: int | None,
        last_seen_now: int | None,
    ) -> None:
        """Neither anchor proves the reboot, so the gate records nothing.

        Args:
            last_seen_before: The moment that the pre-check read, or None.
            last_seen_now: The moment of the current record, or None.
        """
        settle = gate.SettleGate(FakeClock())
        signals = gate.GateSignals(reconnected=True, reading=_reading(None, last_seen_now))
        result = settle.observe(_target(UPTIME_BEFORE, last_seen_before), _opened(), signals)
        assert result.reboot_at is None
        assert result.version_after is None

    def test_the_device_stays_unsettled_over_many_rounds(self) -> None:
        """A device with no anchor never settles, however long the phase runs.

        Why:
            The gate must never invent proof after a number of rounds. That
            device reaches the phase deadline and the run reports it, which is
            the honest outcome.
        """
        clock = FakeClock()
        settle = gate.SettleGate(clock)
        target = _target(UPTIME_BEFORE, None)
        progress = _opened()
        for _round in range(10):
            signals = gate.GateSignals(reconnected=True, reading=_reading(None, LAST_SEEN_AFTER))
            progress = settle.observe(target, progress, signals)
            clock.advance(float(gate.POLL_INTERVAL_SECONDS))
        assert progress.reboot_at is None
        assert gate.is_settled(progress) is False


class TestTheUptimePathKeepsItsVerdict:
    """The anchor never removes or overrules the uptime rule.

    Why:
        A real uptime that rose is evidence against a reboot. An anchor that
        overruled it would settle a device from a record that the cloud built
        before the reboot.
    """

    def test_a_risen_uptime_records_no_reboot(self) -> None:
        """A real uptime that did not fall keeps its verdict."""
        settle = gate.SettleGate(FakeClock())
        signals = gate.GateSignals(reconnected=True, reading=_reading(UPTIME_RISEN, LAST_SEEN_AFTER))
        result = settle.observe(_target(UPTIME_BEFORE, LAST_SEEN_BEFORE), _opened(), signals)
        assert result.reboot_at is None

    def test_a_fallen_uptime_still_proves_the_reboot_with_no_anchor(self) -> None:
        """The uptime path answers alone, exactly as it did before."""
        settle = gate.SettleGate(FakeClock())
        signals = gate.GateSignals(reconnected=True, reading=_reading(UPTIME_AFTER, None))
        result = settle.observe(_target(UPTIME_BEFORE, None), _opened(), signals)
        assert result.reboot_at == LOCAL_CLOCK_START
        assert result.version_after == VERSION_AFTER

    def test_a_device_with_no_earlier_uptime_still_settles_on_the_version(self) -> None:
        """The version-only path answers before the anchor runs.

        Why:
            A device that reached the gate with no earlier uptime settled on
            the firmware version change alone. The anchor must not change that
            device, because no reading can show a fall against an unread value.
        """
        settle = gate.SettleGate(FakeClock())
        signals = gate.GateSignals(reconnected=True, reading=_reading(None, None))
        result = settle.observe(_target(None, None), _opened(), signals)
        assert result.reboot_at == LOCAL_CLOCK_START

    def test_an_unchanged_version_records_no_reboot(self) -> None:
        """The anchor never replaces the firmware version half of the rule.

        Why:
            The cloud raises ``last_seen`` while a device runs, so a rising
            moment alone proves no reboot. The version must change as well.
        """
        settle = gate.SettleGate(FakeClock())
        reading = gate.GateReading(SWITCH_MAC, VERSION_BEFORE, None, LAST_SEEN_AFTER)
        result = settle.observe(_target(UPTIME_BEFORE, LAST_SEEN_BEFORE), _opened(), gate.GateSignals(True, reading))
        assert result.reboot_at is None


class TestTheTargetCarriesTheAnchor:
    """The anchor travels from the pre-check to the gate.

    Why:
        The predicate cannot help a device whose anchor never reaches the gate.
        These tests follow the value along the whole path.
    """

    def test_the_field_carries_a_default(self) -> None:
        """A caller that names no anchor still builds a target.

        Why:
            The application wiring builds gate records, and a required field
            would break every caller that holds no anchor.
        """
        target = gate.GateTarget(
            mac=SWITCH_MAC,
            device_type="switch",
            version_before=VERSION_BEFORE,
            uptime_before=UPTIME_BEFORE,
        )
        assert target.last_seen_before is None

    def test_the_target_entry_records_the_moment(self) -> None:
        """The pre-check writes the cloud moment onto the run record."""
        entry = options.build_target_entry(SWITCH_ROW, VERSION_AFTER)
        assert entry["last_seen_before"] == LAST_SEEN_BEFORE

    def test_a_row_with_no_moment_records_a_null(self) -> None:
        """A device that reports no moment stores a null, and never a zero.

        Why:
            A stored zero sits at the start of the epoch, so every later record
            would look newer and the anchor would prove a reboot that never
            happened.
        """
        row = {key: value for key, value in SWITCH_ROW.items() if key != "last_seen"}
        assert options.build_target_entry(row, VERSION_AFTER)["last_seen_before"] is None

    def test_a_text_moment_records_a_null(self) -> None:
        """A value that holds no number reads as no reading at all."""
        row = dict(SWITCH_ROW, last_seen="never")
        assert options.build_target_entry(row, VERSION_AFTER)["last_seen_before"] is None

    def test_the_phase_gate_reads_the_moment_onto_the_target(self) -> None:
        """The whole path carries the anchor from the row to the gate target."""
        entry = options.build_target_entry(SWITCH_ROW, VERSION_AFTER)
        targets = phase_gate.build_targets([entry])
        assert targets[0].last_seen_before == LAST_SEEN_BEFORE
        assert targets[0].uptime_before == UPTIME_BEFORE

    def test_the_phase_gate_keeps_a_missing_moment_null(self) -> None:
        """An entry with no anchor reaches the gate with a null."""
        entry = options.build_target_entry(SWITCH_ROW, VERSION_AFTER)
        entry["last_seen_before"] = None
        assert phase_gate.build_targets([entry])[0].last_seen_before is None


class TestUpgradeStatusStartTime:
    """The absolute anchor of the upgrade job itself.

    Why:
        The vendor reports the epoch moment when the firmware download started.
        The reader dropped that field, so no caller could date a device reading
        against the run.
    """

    def test_the_status_keeps_the_start_time(self) -> None:
        """The reader carries the moment that the cloud reported."""
        payload = {"status": "upgrading", "current_phase": "reboot", "start_time": START_TIME}
        status = upgrade_service._normalize_status(payload, UPGRADE_ID, HTTP_OK)  # noqa: SLF001  # WHY: the unit here.
        assert status["start_time"] == START_TIME

    def test_a_payload_with_no_start_time_reads_as_none(self) -> None:
        """A missing field stays absent, and the reader invents no moment."""
        status = upgrade_service._normalize_status({}, UPGRADE_ID, HTTP_OK)  # noqa: SLF001  # WHY: the unit here.
        assert status["start_time"] is None

    def test_the_other_status_fields_stay_the_same(self) -> None:
        """The six earlier keys keep their names and their values.

        Why:
            The run driver and the run page read these names. A reader that
            renamed one would report the wrong state on every poll.
        """
        payload = {"status": "upgrading", "current_phase": "reboot", "start_time": START_TIME}
        status = upgrade_service._normalize_status(payload, UPGRADE_ID, HTTP_OK)  # noqa: SLF001  # WHY: the unit.
        assert status["upgrade_id"] == UPGRADE_ID
        assert status["raw_status"] == HTTP_OK
        assert status["status"] == "upgrading"
        assert status["current_phase"] == "reboot"
        assert status["reboot_in_progress"] == ()
        assert status["targets"] == {}
