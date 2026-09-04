"""Tests of the rehearsal support modules alone.

Why:
    A broken support module must fail here and not inside a whole run. A
    failure of the clock, of the scripts, or of one stand-in answer is then a
    plain message about that one part.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from src.upgrade_portal.upgrade import events
from tests.support.rehearsal import (
    TYPE_ACCESS_POINT,
    TYPE_GATEWAY,
    TYPE_SWITCH,
    VERSION_AFTER,
    VERSION_BEFORE,
    RehearsalClock,
    RehearsalFirmwareError,
    StandInCloud,
    cascade_fleet,
    stop_fleet,
)
from tests.support.rehearsal.cloud import CATALOGUE_KEYS, FIRMWARE_WRITE_NAMES, STATISTICS_NAME


@pytest.fixture
def clock() -> RehearsalClock:
    """Return one driven clock at its start reading.

    Returns:
        The clock.
    """
    return RehearsalClock()


@pytest.fixture
def cloud(clock: RehearsalClock) -> StandInCloud:
    """Return one stand-in cloud over the cascade fleet.

    Args:
        clock: The one time source of the fleet.

    Returns:
        The stand-in cloud.
    """
    return StandInCloud(cascade_fleet(clock.now()), clock)


def test_the_clock_moves_only_on_a_sleep_or_an_advance(clock: RehearsalClock) -> None:
    """The reading never moves by itself.

    Args:
        clock: The driven clock.
    """
    start = clock.now()  # The reading before any call.
    assert clock.now() == start  # A second read must answer the same value.
    clock.sleep(20.0)  # The wait of one poll round.
    assert clock.now() == start + 20.0  # The sleep moved the reading by its own length.


def test_the_clock_never_moves_backwards(clock: RehearsalClock) -> None:
    """A negative wait leaves the reading where it was.

    Args:
        clock: The driven clock.
    """
    start = clock.now()  # The reading before the call.
    clock.sleep(-5.0)  # A caller that computed a negative wait must not rewind the run.
    assert clock.now() == start  # The reading held its place.


def test_the_clock_records_every_sleep_and_no_advance(clock: RehearsalClock) -> None:
    """Only a sleep joins the wait record.

    Args:
        clock: The driven clock.
    """
    clock.sleep(20.0)  # One poll wait.
    clock.advance(60.0)  # A test step, which is not a wait of the shipped code.
    assert clock.sleeps() == (20.0,)  # The record holds the poll wait alone.


def test_the_clock_answers_a_text_reading(clock: RehearsalClock) -> None:
    """The text reading carries the date and the offset.

    Args:
        clock: The driven clock.
    """
    assert clock.now_text().startswith("2026-01-01T00:00:00")  # The fixed start of every rehearsal.


def test_the_cascade_fleet_holds_six_devices_of_three_families() -> None:
    """The composed run needs two devices of each family."""
    fleet = cascade_fleet(0.0)  # The fleet of user story 1.
    assert len(fleet.scripts) == 6  # Two of each of the three families.
    for family in (TYPE_GATEWAY, TYPE_SWITCH, TYPE_ACCESS_POINT):  # Each family in turn.
        assert len(fleet.scripts_of_type(family)) == 2  # Two devices prove a phase and not one device.


def test_the_stop_fleet_adds_one_session_smart_router() -> None:
    """The stop run needs the organization scope device."""
    fleet = stop_fleet(0.0)  # The fleet of user story 2.
    assert len(fleet.scripts) == 7  # The six cascade devices and the router.
    assert fleet.script_for("dd0000000001") is not None  # The router of the organization scope call.


def test_a_device_reports_the_old_version_before_its_moment() -> None:
    """The version changes at the scripted moment and never before it."""
    script = cascade_fleet(0.0).scripts[0]  # One gateway of the fleet.
    assert script.version_of(0.0) == VERSION_BEFORE  # The start of the run.
    assert script.version_of(script.version_at) == VERSION_AFTER  # The scripted moment itself.


def test_a_device_uptime_falls_at_the_reboot() -> None:
    """The uptime falls, which is the proof that the device rebooted."""
    script = cascade_fleet(0.0).scripts[0]  # One gateway of the fleet.
    before = script.uptime_of(0.0)  # The long uptime of a device that ran for weeks.
    after = script.uptime_of(script.reconnect_at + 10.0)  # The short uptime after the reboot.
    assert after < before  # A fall is the one signal that ``gate.uptime_decreased`` reads.


def test_the_statistics_answer_carries_the_page_fields(cloud: StandInCloud) -> None:
    """The page guard of the shipped reader needs a real page count.

    Args:
        cloud: The stand-in cloud.
    """
    answer = cloud.list_org_devices_stats(None, "org", type="all", site_id=None, fields=None, limit=1000)
    assert set(answer.data) == {"results", "total", "next"}  # The three fields of a Mist page.
    assert answer.data["next"] is None  # One page holds the whole rehearsal fleet.


def test_the_statistics_answer_is_recorded_under_the_shipped_name(cloud: StandInCloud) -> None:
    """The call record names the endpoint that the settle gate reaches.

    Args:
        cloud: The stand-in cloud.
    """
    cloud.list_org_devices_stats(None, "org", type="all", site_id=None, fields=None, limit=1000)
    assert cloud.calls_of(STATISTICS_NAME) == 1  # One read, under the shipped name.


def test_the_event_answer_holds_the_family_that_the_caller_asked_for(
    cloud: StandInCloud, clock: RehearsalClock
) -> None:
    """The stand-in answers the family of the request and no other family.

    Args:
        cloud: The stand-in cloud.
        clock: The one time source of the fleet.
    """
    clock.advance(60.0)  # Past the reconnect moment of every device of the fleet.
    window = events.build_window(clock.now())  # The window that the shipped reader builds.
    answer = cloud.search_org_device_events(
        None,
        "org",
        device_type=TYPE_GATEWAY,
        start=str(window.start),
        end=str(window.end),
        limit=window.limit,
        search_after=None,
    )
    families = {str(row["device_type"]) for row in answer.data["results"]}  # Every family in the answer.
    assert families == {TYPE_GATEWAY}  # The gateway family alone, because the caller named it.


def test_the_catalogue_answer_holds_the_reconnect_keys(cloud: StandInCloud) -> None:
    """The shipped key filter keeps a key that ends in the right suffix.

    Args:
        cloud: The stand-in cloud.
    """
    answer = cloud.list_device_events_definitions(None)  # The one start-up read of the run.
    keys = {str(row["key"]) for row in answer.data}  # Every key of the answer.
    assert keys == set(CATALOGUE_KEYS)  # The four keys that the reconnect filter keeps.


@pytest.mark.parametrize("name", FIRMWARE_WRITE_NAMES)
def test_the_resolver_refuses_every_firmware_write(cloud: StandInCloud, name: str) -> None:
    """No rehearsal may write firmware to any device.

    Args:
        cloud: The stand-in cloud.
        name: The endpoint name of one firmware write.
    """
    with pytest.raises(RehearsalFirmwareError):  # The refusal is the whole point of this seat.
        cloud.resolve_endpoint(name)  # The resolver refuses before any caller can reach the write.


def test_the_pause_hook_runs_once_for_one_poll_round(cloud: StandInCloud) -> None:
    """The pause hook holds a poll round for the run status test.

    Args:
        cloud: The stand-in cloud.
    """
    seen: list[int] = []  # One entry for each paused call.
    cloud.set_pause(lambda: seen.append(1))  # The hook that the run status test installs.
    cloud.list_org_devices_stats(None, "org", type="all", site_id=None, fields=None, limit=1000)
    assert seen == [1]  # The hook ran for the one call.


# ---------------------------------------------------------------------------
# SC-001, the one condition that this suite does not prove
# ---------------------------------------------------------------------------


def test_the_route_level_condition_keeps_its_own_proof() -> None:
    """SC-001 names one condition that another suite proves, so that name must hold.

    Why:
        Condition C1 of scenario C is the refusal to start with no verified
        pre-check. It belongs to the start route, and the rehearsal starts below
        that route on purpose. SC-001 therefore points at a contract test
        instead of claiming the proof here. A rename or a deletion of that test
        would make SC-001 false with no other signal, so this test holds the
        name.
    """
    logging.info("Checking that the contract test named by SC-001 still exists")  # Report before the read.
    path = Path(__file__).resolve().parents[2] / "contract" / "upgrade_portal" / "test_capture_attach.py"
    text = path.read_text(encoding="utf-8")  # The module that owns the route-level proof.
    logging.debug("Read %d characters of the contract module", len(text))  # Record the size after the read.

    assert path.is_file(), "SC-001 names a contract module that must exist"
    assert "def test_a_start_before_the_pre_check_still_refuses(" in text, "SC-001 names this test"
