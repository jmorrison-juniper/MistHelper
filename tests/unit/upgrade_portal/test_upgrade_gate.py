"""Unit tests for the settle gate of the upgrade portal.

Why:
    Two rules of this gate fail quietly when somebody gets them wrong. A gate
    that tests "uptime is near zero" misses a fast reboot and waits for ever,
    because a device already reports a small positive uptime by the time the
    poll reads it. A gate that reads a null uptime as zero sees a decrease
    that never happened and settles a device that never rebooted. Neither
    fault raises an error, so a test is the only guard.

    Every test drives a fake clock forward. No test sleeps, and no test opens
    a socket or names a real credential.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any

import mistapi
import pytest

from src.upgrade_portal.upgrade import gate

# WHY: Obviously fake identifiers. A reader sees at once that no test reaches
#      a real organization, a real site, or a real device.
ORG_ID = "11111111-2222-3333-4444-555555555555"
SITE_ID = "66666666-7777-8888-9999-000000000000"
UPGRADE_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
SWITCH_MAC = "0011220000aa"
ACCESS_POINT_MAC = "0011220000bb"

VERSION_BEFORE = "23.4R2.13"
VERSION_AFTER = "23.4R2-S3.9"

# WHY: A device that ran for 21 days. Every reading below compares against it.
UPTIME_BEFORE = 1832140

# WHY: A small positive uptime, never zero. This is the value that breaks a
#      gate that tests "near zero" instead of "less than the earlier value".
UPTIME_AFTER_FAST_REBOOT = 45

PAGE_LIMIT = 200
HTTP_OK = 200
START_TIME = 1000.0


class FakeClock:
    """A clock that a test drives forward with no real wait.

    Why:
        The gate waits 60 seconds for a switch and 120 seconds for an access
        point. A test that used the real clock would run for two minutes for
        one case. This clock returns whatever the test set, so the same case
        runs in microseconds.
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


def switch_target() -> gate.GateTarget:
    """Build the target record of one switch.

    Returns:
        The state of the switch before the upgrade.
    """
    return gate.GateTarget(
        mac=SWITCH_MAC,
        device_type="switch",
        version_before=VERSION_BEFORE,
        uptime_before=UPTIME_BEFORE,
    )


def access_point_target() -> gate.GateTarget:
    """Build the target record of one access point.

    Returns:
        The state of the access point before the upgrade.
    """
    return gate.GateTarget(
        mac=ACCESS_POINT_MAC,
        device_type="ap",
        version_before=VERSION_BEFORE,
        uptime_before=UPTIME_BEFORE,
    )


def null_uptime_target() -> gate.GateTarget:
    """Build the target record of one switch whose earlier uptime was unread.

    Why:
        The pre-check may read a device whose statistics record carried no
        uptime. That device reaches the gate with a null, never a zero, so
        every test of the version-only rule starts from this record.

    Returns:
        The state of the switch before the upgrade, with no earlier uptime.
    """
    return gate.GateTarget(
        mac=SWITCH_MAC,
        device_type="switch",
        version_before=VERSION_BEFORE,
        uptime_before=None,
    )


def rebooted_reading(mac: str = SWITCH_MAC) -> gate.GateReading:
    """Build a reading that proves a reboot.

    Args:
        mac: The device address of the reading.

    Returns:
        A reading with a lower uptime and a new version.
    """
    return gate.GateReading(mac=mac, version=VERSION_AFTER, uptime=UPTIME_AFTER_FAST_REBOOT)


def fake_response(payload: Any, status: int = HTTP_OK) -> SimpleNamespace:
    """Build one fake cloud answer.

    Args:
        payload: The parsed body of the answer.
        status: The HTTP status of the answer.

    Returns:
        An object with the two attributes that the guard reads.
    """
    return SimpleNamespace(data=payload, status_code=status)


# --- The three settle signals -------------------------------------------


def test_reconnect_alone_does_not_settle() -> None:
    """The reconnect event on its own leaves the device unsettled."""
    progress = gate.advance(switch_target(), gate.GateProgress(), gate.GateSignals(reconnected=True), START_TIME)
    assert progress.reconnected is True
    assert progress.reboot_at is None
    assert gate.is_settled(progress) is False


def test_reading_before_the_reconnect_event_is_ignored() -> None:
    """A statistics reading before the reconnect event records no reboot."""
    signals = gate.GateSignals(reconnected=False, reading=rebooted_reading())
    progress = gate.advance(switch_target(), gate.GateProgress(), signals, START_TIME)
    assert progress.reboot_at is None
    assert progress.version_after is None


def test_reconnect_and_reading_alone_do_not_settle() -> None:
    """The first two signals leave the device unsettled until the wait ends."""
    signals = gate.GateSignals(reconnected=True, reading=rebooted_reading())
    progress = gate.advance(switch_target(), gate.GateProgress(), signals, START_TIME)
    assert progress.reboot_at == START_TIME
    assert progress.version_after == VERSION_AFTER
    assert gate.is_settled(progress) is False


def test_all_three_signals_settle_the_device() -> None:
    """The device settles only after the reconnect, the reading, and the wait."""
    target = switch_target()
    signals = gate.GateSignals(reconnected=True, reading=rebooted_reading())
    progress = gate.advance(target, gate.GateProgress(), signals, START_TIME)
    settled = gate.advance(target, progress, gate.GateSignals(), START_TIME + gate.SETTLE_WAIT_SECONDS)
    assert gate.is_settled(settled) is True
    assert settled.settled_at == START_TIME + gate.SETTLE_WAIT_SECONDS


def test_a_settled_device_never_moves_again() -> None:
    """A settled record stays the same after another round."""
    target = switch_target()
    settled = gate.GateProgress(reconnected=True, reboot_at=START_TIME, settled_at=START_TIME + 60.0)
    again = gate.advance(target, settled, gate.GateSignals(reconnected=True, reading=rebooted_reading()), 9999.0)
    assert again == settled


# --- The uptime decrease rule -------------------------------------------


def test_a_small_positive_uptime_still_proves_the_reboot() -> None:
    """A fast reboot reports a small positive uptime and still counts."""
    assert UPTIME_AFTER_FAST_REBOOT > 0
    assert gate.uptime_decreased(UPTIME_BEFORE, UPTIME_AFTER_FAST_REBOOT) is True


def test_an_uptime_that_grew_does_not_prove_the_reboot() -> None:
    """An uptime above the earlier value proves nothing."""
    assert gate.uptime_decreased(UPTIME_BEFORE, UPTIME_BEFORE + 60) is False


def test_an_equal_uptime_does_not_prove_the_reboot() -> None:
    """The test is less than, so an equal reading proves nothing."""
    assert gate.uptime_decreased(UPTIME_BEFORE, UPTIME_BEFORE) is False


def test_an_uptime_that_grew_records_no_reboot() -> None:
    """A reading with a higher uptime leaves the reboot unrecorded."""
    reading = gate.GateReading(mac=SWITCH_MAC, version=VERSION_AFTER, uptime=UPTIME_BEFORE + 60)
    signals = gate.GateSignals(reconnected=True, reading=reading)
    progress = gate.advance(switch_target(), gate.GateProgress(), signals, START_TIME)
    assert progress.reboot_at is None


def test_a_version_that_did_not_change_records_no_reboot() -> None:
    """The uptime and the version must both move in one reading."""
    reading = gate.GateReading(mac=SWITCH_MAC, version=VERSION_BEFORE, uptime=UPTIME_AFTER_FAST_REBOOT)
    signals = gate.GateSignals(reconnected=True, reading=reading)
    progress = gate.advance(switch_target(), gate.GateProgress(), signals, START_TIME)
    assert progress.reboot_at is None


def test_an_empty_version_records_no_reboot() -> None:
    """An empty version is no reading, so it is never a change."""
    reading = gate.GateReading(mac=SWITCH_MAC, version="", uptime=UPTIME_AFTER_FAST_REBOOT)
    signals = gate.GateSignals(reconnected=True, reading=reading)
    progress = gate.advance(switch_target(), gate.GateProgress(), signals, START_TIME)
    assert progress.reboot_at is None


# --- The null uptime rule -----------------------------------------------


def test_a_null_uptime_is_not_zero() -> None:
    """The reader keeps a null uptime apart from zero."""
    assert gate.reading_uptime(None) is None
    assert gate.reading_uptime(0) == 0


def test_a_text_uptime_reads_as_no_reading() -> None:
    """A value that is not a number means no reading, never zero."""
    assert gate.reading_uptime("unknown") is None


def test_a_null_uptime_never_proves_a_decrease() -> None:
    """A null reading answers False rather than looking like zero."""
    assert gate.uptime_decreased(UPTIME_BEFORE, None) is False


def test_a_null_uptime_leaves_the_device_unsettled() -> None:
    """A null reading records no reboot, so the gate retries."""
    reading = gate.GateReading(mac=SWITCH_MAC, version=VERSION_AFTER, uptime=None)
    signals = gate.GateSignals(reconnected=True, reading=reading)
    progress = gate.advance(switch_target(), gate.GateProgress(), signals, START_TIME)
    assert progress.reboot_at is None
    assert progress.version_after is None


def test_a_null_uptime_round_is_followed_by_a_good_round() -> None:
    """The gate retries after a null reading and settles on a real one."""
    target = switch_target()
    null_reading = gate.GateReading(mac=SWITCH_MAC, version=VERSION_AFTER, uptime=None)
    first = gate.advance(target, gate.GateProgress(), gate.GateSignals(True, null_reading), START_TIME)
    second = gate.advance(target, first, gate.GateSignals(reading=rebooted_reading()), START_TIME + 20.0)
    assert second.reboot_at == START_TIME + 20.0


def test_a_missing_reading_leaves_the_device_unsettled() -> None:
    """A poll that returned no record for the device records no reboot."""
    progress = gate.advance(switch_target(), gate.GateProgress(), gate.GateSignals(True, None), START_TIME)
    assert progress.reboot_at is None


def test_a_null_uptime_record_reads_as_no_reading() -> None:
    """A record with a null uptime becomes a reading with a null uptime."""
    reading = gate.reading_from_record({"mac": SWITCH_MAC, "version": VERSION_AFTER, "uptime": None})
    assert reading is not None
    assert reading.uptime is None


def test_a_record_with_no_address_is_dropped() -> None:
    """A record with no usable address matches every other malformed record."""
    assert gate.reading_from_record({"version": VERSION_AFTER, "uptime": 10}) is None


# --- The null earlier uptime rule ---------------------------------------


def test_a_null_earlier_uptime_stays_null() -> None:
    """The target keeps the null, so no reader inside the gate sees a zero."""
    assert null_uptime_target().uptime_before is None


def test_a_null_earlier_uptime_never_proves_a_decrease() -> None:
    """The gate cannot compare a reading against a value it never read."""
    assert gate.uptime_decreased(None, UPTIME_AFTER_FAST_REBOOT) is False
    assert gate.uptime_decreased(None, 0) is False
    assert gate.uptime_decreased(None, None) is False


def test_the_version_change_rule_needs_a_filled_reading() -> None:
    """An empty version is no reading, so it is never a change."""
    assert gate.version_changed(VERSION_BEFORE, VERSION_AFTER) is True
    assert gate.version_changed(VERSION_BEFORE, VERSION_BEFORE) is False
    assert gate.version_changed(VERSION_BEFORE, "") is False


def test_a_null_earlier_uptime_settles_on_the_version_change() -> None:
    """With no earlier uptime the version change alone proves the reboot."""
    target = null_uptime_target()
    signals = gate.GateSignals(reconnected=True, reading=rebooted_reading())
    progress = gate.advance(target, gate.GateProgress(), signals, START_TIME)
    assert progress.reboot_at == START_TIME
    assert progress.version_after == VERSION_AFTER
    settled = gate.advance(target, progress, gate.GateSignals(), START_TIME + gate.SETTLE_WAIT_SECONDS)
    assert gate.is_settled(settled) is True


def test_a_null_earlier_uptime_settles_when_the_reading_uptime_is_null_too() -> None:
    """A device that reports no uptime at all still settles on the version."""
    reading = gate.GateReading(mac=SWITCH_MAC, version=VERSION_AFTER, uptime=None)
    signals = gate.GateSignals(reconnected=True, reading=reading)
    progress = gate.advance(null_uptime_target(), gate.GateProgress(), signals, START_TIME)
    assert progress.reboot_at == START_TIME
    assert progress.version_after == VERSION_AFTER


def test_a_null_earlier_uptime_does_not_settle_while_the_version_holds() -> None:
    """An unchanged version leaves the device unsettled however long it waits."""
    target = null_uptime_target()
    reading = gate.GateReading(mac=SWITCH_MAC, version=VERSION_BEFORE, uptime=UPTIME_AFTER_FAST_REBOOT)
    progress = gate.advance(target, gate.GateProgress(), gate.GateSignals(True, reading), START_TIME)
    assert progress.reboot_at is None
    assert progress.version_after is None
    later = gate.advance(target, progress, gate.GateSignals(True, reading), START_TIME + 600.0)
    assert gate.is_settled(later) is False


def test_a_null_earlier_uptime_with_an_empty_version_does_not_settle() -> None:
    """An empty version is no reading, so the weaker rule still refuses it."""
    reading = gate.GateReading(mac=SWITCH_MAC, version="", uptime=None)
    signals = gate.GateSignals(reconnected=True, reading=reading)
    progress = gate.advance(null_uptime_target(), gate.GateProgress(), signals, START_TIME)
    assert progress.reboot_at is None


def test_the_version_only_rule_warns_and_names_the_device(caplog: pytest.LogCaptureFixture) -> None:
    """An operator can see which device settled on the weaker signal."""
    caplog.set_level(logging.WARNING)
    signals = gate.GateSignals(reconnected=True, reading=rebooted_reading())
    gate.advance(null_uptime_target(), gate.GateProgress(), signals, START_TIME)
    warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert any(SWITCH_MAC in record.getMessage() for record in warnings)


def test_an_integer_earlier_uptime_still_needs_both_halves(caplog: pytest.LogCaptureFixture) -> None:
    """A device with a real earlier uptime keeps the two-half proof."""
    caplog.set_level(logging.WARNING)
    reading = gate.GateReading(mac=SWITCH_MAC, version=VERSION_AFTER, uptime=UPTIME_BEFORE + 60)
    signals = gate.GateSignals(reconnected=True, reading=reading)
    progress = gate.advance(switch_target(), gate.GateProgress(), signals, START_TIME)
    assert progress.reboot_at is None
    assert [record for record in caplog.records if record.levelno == logging.WARNING] == []


def test_a_zero_earlier_uptime_is_not_a_null() -> None:
    """A stored zero stays a real value and still needs a fall below it."""
    target = gate.GateTarget(SWITCH_MAC, "switch", VERSION_BEFORE, 0)
    signals = gate.GateSignals(reconnected=True, reading=rebooted_reading())
    assert gate.advance(target, gate.GateProgress(), signals, START_TIME).reboot_at is None


# --- The two extra waits ------------------------------------------------


def test_the_switch_wait_is_sixty_seconds() -> None:
    """A switch waits 60 seconds after the reboot signal."""
    assert gate.settle_wait_seconds("switch") == 60
    assert gate.settle_wait_seconds("gateway") == 60


def test_the_access_point_wait_is_one_hundred_twenty_seconds() -> None:
    """An access point waits a further 60 seconds."""
    assert gate.settle_wait_seconds("ap") == 120
    assert gate.settle_wait_seconds("AP") == 120


def test_a_switch_stays_unsettled_one_second_early() -> None:
    """The switch wait is not finished at 59 seconds."""
    target = switch_target()
    progress = gate.GateProgress(reconnected=True, reboot_at=START_TIME, version_after=VERSION_AFTER)
    later = gate.advance(target, progress, gate.GateSignals(), START_TIME + 59.0)
    assert gate.is_settled(later) is False


def test_an_access_point_stays_unsettled_at_the_switch_wait() -> None:
    """The access point is still unsettled when a switch would be settled."""
    target = access_point_target()
    progress = gate.GateProgress(reconnected=True, reboot_at=START_TIME, version_after=VERSION_AFTER)
    later = gate.advance(target, progress, gate.GateSignals(), START_TIME + 60.0)
    assert gate.is_settled(later) is False
    assert gate.is_settled(gate.advance(target, progress, gate.GateSignals(), START_TIME + 119.0)) is False


def test_an_access_point_settles_at_one_hundred_twenty_seconds() -> None:
    """The access point settles after the second wait ends."""
    target = access_point_target()
    progress = gate.GateProgress(reconnected=True, reboot_at=START_TIME, version_after=VERSION_AFTER)
    later = gate.advance(target, progress, gate.GateSignals(), START_TIME + 120.0)
    assert gate.is_settled(later) is True


# --- The injected clock -------------------------------------------------


def test_the_gate_reads_the_injected_clock() -> None:
    """The gate takes its time from the callable that the caller passed."""
    clock = FakeClock()
    settle_gate = gate.SettleGate(clock=clock)
    assert settle_gate.now() == START_TIME
    clock.advance(30.0)
    assert settle_gate.now() == START_TIME + 30.0


def test_the_injected_clock_drives_both_waits() -> None:
    """A test proves the 120-second wait without any real wait."""
    clock = FakeClock()
    settle_gate = gate.SettleGate(clock=clock)
    target = access_point_target()
    signals = gate.GateSignals(reconnected=True, reading=rebooted_reading(ACCESS_POINT_MAC))
    progress = settle_gate.observe(target, gate.GateProgress(), signals)
    clock.advance(119.0)
    assert gate.is_settled(settle_gate.observe(target, progress, gate.GateSignals())) is False
    clock.advance(1.0)
    assert gate.is_settled(settle_gate.observe(target, progress, gate.GateSignals())) is True


def test_the_default_clock_is_the_wall_clock() -> None:
    """A gate with no clock still answers with a time."""
    assert gate.SettleGate().now() > 0


# --- The statistics poll ------------------------------------------------


def test_the_fleet_poll_sends_the_type_and_the_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """One poll reads every device type and asks for the three gate fields."""
    seen: dict[str, Any] = {}

    def fake_call(session: Any, org_id: str, **kwargs: Any) -> SimpleNamespace:
        seen.update(kwargs)
        seen["org_id"] = org_id
        return fake_response([])

    monkeypatch.setattr(mistapi.api.v1.orgs.stats, "listOrgDevicesStats", fake_call)
    monkeypatch.setattr(mistapi, "get_all", lambda mist_session, response: [])
    gate.read_fleet_statistics(SimpleNamespace(), ORG_ID, SITE_ID, PAGE_LIMIT)
    assert seen["org_id"] == ORG_ID
    assert seen["type"] == "all"
    assert seen["fields"] == gate.STATISTICS_FIELDS
    assert seen["site_id"] == SITE_ID


def test_the_fleet_poll_sends_no_device_address(monkeypatch: pytest.MonkeyPatch) -> None:
    """The poll reads the whole fleet, so it never filters by one device."""
    seen: dict[str, Any] = {}

    def fake_call(session: Any, org_id: str, **kwargs: Any) -> SimpleNamespace:
        seen.update(kwargs)
        return fake_response([])

    monkeypatch.setattr(mistapi.api.v1.orgs.stats, "listOrgDevicesStats", fake_call)
    monkeypatch.setattr(mistapi, "get_all", lambda mist_session, response: [])
    gate.read_fleet_statistics(SimpleNamespace(), ORG_ID, page_limit=PAGE_LIMIT)
    assert "mac" not in seen


def test_the_fleet_poll_keys_the_readings_by_address(monkeypatch: pytest.MonkeyPatch) -> None:
    """The poll returns one reading for each device, keyed by the address."""
    rows = [
        {"mac": "00:11:22:00:00:AA", "version": VERSION_AFTER, "uptime": 45},
        {"mac": ACCESS_POINT_MAC, "version": VERSION_BEFORE, "uptime": None},
    ]
    monkeypatch.setattr(mistapi.api.v1.orgs.stats, "listOrgDevicesStats", lambda *a, **k: fake_response(rows))
    monkeypatch.setattr(mistapi, "get_all", lambda mist_session, response: rows)
    result = gate.read_fleet_statistics(SimpleNamespace(), ORG_ID, page_limit=PAGE_LIMIT)
    assert set(result.readings) == {SWITCH_MAC, ACCESS_POINT_MAC}
    assert result.readings[SWITCH_MAC].uptime == 45
    assert result.readings[ACCESS_POINT_MAC].uptime is None
    assert result.partial_reasons == []


def test_a_failed_poll_becomes_a_partial_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    """A cloud fault marks the round partial and never stops the run."""

    def fake_call(*args: Any, **kwargs: Any) -> SimpleNamespace:
        raise RuntimeError("the cloud refused the read")

    monkeypatch.setattr(mistapi.api.v1.orgs.stats, "listOrgDevicesStats", fake_call)
    result = gate.read_fleet_statistics(SimpleNamespace(), ORG_ID, page_limit=PAGE_LIMIT)
    assert result.readings == {}
    assert result.partial_reasons[0]["section"] == gate.SECTION_GATE_STATISTICS
    assert result.partial_reasons[0]["reason"] == "read_failed"


def test_a_short_poll_becomes_a_partial_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    """A page count below the reported total marks the round partial."""
    body = {"results": [{"mac": SWITCH_MAC}], "total": 4}
    monkeypatch.setattr(mistapi.api.v1.orgs.stats, "listOrgDevicesStats", lambda *a, **k: fake_response(body))
    monkeypatch.setattr(mistapi, "get_all", lambda mist_session, response: [{"mac": SWITCH_MAC}])
    result = gate.read_fleet_statistics(SimpleNamespace(), ORG_ID, page_limit=PAGE_LIMIT)
    assert result.partial_reasons[0]["reason"] == "page_count_mismatch"


def test_an_unknown_answer_shape_becomes_a_partial_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    """The page helper answers with an empty list for a shape it cannot read."""
    monkeypatch.setattr(mistapi.api.v1.orgs.stats, "listOrgDevicesStats", lambda *a, **k: fake_response({"x": 1}))
    monkeypatch.setattr(mistapi, "get_all", lambda mist_session, response: [])
    result = gate.read_fleet_statistics(SimpleNamespace(), ORG_ID, page_limit=PAGE_LIMIT)
    assert result.partial_reasons[0]["reason"] == "unexpected_response_shape"


# --- The reboot hint ----------------------------------------------------


def test_the_reboot_hint_reads_the_normalized_field() -> None:
    """The hint reads the field that the upgrade seam already normalized."""
    status = {"reboot_in_progress": (SWITCH_MAC, ACCESS_POINT_MAC)}
    assert gate.reboot_hint(status) == frozenset({SWITCH_MAC, ACCESS_POINT_MAC})


def test_the_reboot_hint_reads_the_nested_targets_field() -> None:
    """The hint falls back to ``targets.reboot_in_progress``."""
    status = {"targets": {"reboot_in_progress": ["00:11:22:00:00:AA"]}}
    assert gate.reboot_hint(status) == frozenset({SWITCH_MAC})


def test_the_reboot_hint_is_empty_when_the_job_reports_none() -> None:
    """A job with no reboot list gives an empty hint."""
    assert gate.reboot_hint({"targets": {}}) == frozenset()
    assert gate.reboot_hint({}) == frozenset()


def test_the_reboot_hint_ignores_the_status_field() -> None:
    """The gate builds nothing on the statistics ``status`` field."""
    status = {"status": "rebooting", "targets": {}}
    assert gate.reboot_hint(status) == frozenset()


def test_the_reboot_hint_reader_makes_one_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """One call to the upgrade job tells the gate which devices reboot."""
    calls: list[tuple[Any, ...]] = []

    def fake_read(*args: Any) -> dict[str, Any]:
        calls.append(args)
        return {"reboot_in_progress": (SWITCH_MAC,)}

    monkeypatch.setattr(gate, "read_upgrade_status", fake_read)
    hint = gate.read_reboot_hint(SimpleNamespace(), "site", SITE_ID, UPGRADE_ID)
    assert hint == frozenset({SWITCH_MAC})
    assert len(calls) == 1


# --- The call budget ----------------------------------------------------


def test_the_poll_budget_stays_under_the_quota() -> None:
    """The two poll streams stay far below the hourly call quota."""
    stream = gate.polls_per_hour(gate.POLL_INTERVAL_SECONDS)
    assert stream == 180
    assert stream * 2 == gate.MAX_CALLS_PER_HOUR
    assert gate.MAX_CALLS_PER_HOUR < gate.HOURLY_CALL_QUOTA * 0.08


def test_a_zero_interval_is_refused() -> None:
    """A poll interval of zero seconds is not a rate."""
    with pytest.raises(ValueError):
        gate.polls_per_hour(0)
