"""Unit tests for the session smart router upgrade controls of issue #2157.

Why:
    The portal could pick a router version, and it could pick no release train
    and no separate download window. The router schema at
    ``documentation/api/utilities/POST_orgs_org_id_ssr_upgrade.md`` holds six
    fields, and three of them reached no control at all.

    That schema is not the schema of a switch. It holds a channel that no other
    family reads, and it holds no reboot flag. It disables a reboot with a
    ``reboot_at`` of -1 instead. A field that crossed between the two schemas
    would make the cloud refuse the whole call with a message that names no
    field.

    These tests prove that the channel reaches the router body and reaches no
    other body, that the portal refuses every word outside the cloud
    enumeration, and that the plan names the risk of a high-availability pair.

Scope:
    ``build_options``, ``build_body``, and ``plan_upgrade`` only. All three are
    pure, so no test here reaches the Mist cloud.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import json  # One test replays a stored record through a JSON store.
from dataclasses import asdict  # The store keeps the option record through this call.
from typing import Any  # A request body is free-form.

import pytest  # The test framework of the project.

import src.upgrade_portal.upgrade.options as module_options  # Owns the clock seam.
from src.firmware.upgrade_service import (
    ENDPOINT_ORG_SSRS,
    SCOPE_ORG,
    SSR_CHANNEL_CHOICES,
    STRATEGY_SERIAL,
    DeviceTarget,
    GatewayFamily,
    UpgradeOptions,
    build_body,
    plan_upgrade,
)
from src.upgrade_portal.upgrade.options import (
    BadOptionError,
    advanced_option_values,
    build_option_record,
    build_options,
    build_version_options,
    format_duration,
    parse_duration_seconds,
)

SITE_ID = "11111111-1111-1111-1111-111111111111"
ORG_ID = "22222222-2222-2222-2222-222222222222"

MAC_FIRST_ROUTER = "5c5b350e0011"
MAC_SECOND_ROUTER = "5c5b350e0012"
MAC_SWITCH = "5c5b350e0013"

# WHY: The cloud builds a device identifier from the address with this fixed
# prefix. A test that named the finished identifier would repeat a rule that
# `_device_id` already owns, and the two copies would drift apart.
ID_PREFIX = "00000000-0000-0000-1000-"

# WHY: A moment two hours ahead sits inside the window that the schedule guard
# accepts. A fixed epoch would fall behind that window as the calendar moves.
TWO_HOURS_SECONDS = 7200


def fixed_now() -> int:
    """Return the stand-in clock of every test of this module.

    Why:
        The schedule guard compares a chosen moment against now. A fixed clock
        keeps every test of this module independent of the machine that runs it.

    Returns:
        One fixed moment in epoch seconds.
    """
    return 1_800_000_000


def moment_soon() -> int:
    """Return a moment that the schedule guard accepts.

    Returns:
        A moment two hours ahead of the stand-in clock.
    """
    return fixed_now() + TWO_HOURS_SECONDS


def target(mac: str, device_type: str, model: str) -> DeviceTarget:
    """Return one device target for a body test.

    Args:
        mac: The device address with no separator.
        device_type: The Mist device type word.
        model: The device model text.

    Returns:
        One device target.
    """
    return DeviceTarget(
        mac=mac,
        name=f"device-{mac[-4:]}",
        device_type=device_type,
        model=model,
        version_before="5.4.0-100",
        version_target="6.1.2-33",
        site_id=SITE_ID,
    )


def routers() -> tuple[DeviceTarget, ...]:
    """Return two session smart routers of one site.

    Why:
        Two routers of one site often carry the wide area network together, so
        this pair drives the high-availability tests as well as the body tests.

    Returns:
        Two router targets of one model and one version.
    """
    return (
        target(MAC_FIRST_ROUTER, "gateway", "SSR130"),
        target(MAC_SECOND_ROUTER, "gateway", "SSR130"),
    )


def options_from(body: dict[str, Any]) -> UpgradeOptions:
    """Map one browser body onto the option record with the fixed clock.

    Args:
        body: The request body of the options call.

    Returns:
        The finished option record.
    """
    return build_options(body, now=fixed_now)


# ---------------------------------------------------------------------------
# The release train
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("channel", SSR_CHANNEL_CHOICES)
def test_the_router_body_carries_each_channel_that_the_cloud_names(channel: str) -> None:
    """Every word of the cloud enumeration must reach the router body."""
    options = options_from({"channel": channel})
    body = build_body(routers(), options, GatewayFamily.SSR)
    assert body["channel"] == channel


def test_a_channel_reaches_no_switch_body() -> None:
    """The switch schema holds no channel, so the cloud would refuse the call."""
    options = options_from({"channel": "stable"})
    body = build_body((target(MAC_SWITCH, "switch", "EX4100-48P"),), options, GatewayFamily.JUNOS)
    assert "channel" not in body


def test_a_channel_reaches_no_junos_gateway_body() -> None:
    """A Junos gateway follows the switch schema, which holds no channel."""
    options = options_from({"channel": "stable"})
    body = build_body((target(MAC_SWITCH, "gateway", "SRX345"),), options, GatewayFamily.JUNOS)
    assert "channel" not in body


def test_an_operator_who_picks_no_channel_sends_no_channel() -> None:
    """An absent field lets the router keep the train that it follows now."""
    body = build_body(routers(), options_from({}), GatewayFamily.SSR)
    assert "channel" not in body


@pytest.mark.parametrize("word", ["nightly", "release", "prod", "0", "true"])
def test_the_portal_refuses_a_channel_outside_the_cloud_enumeration(word: str) -> None:
    """The cloud answers a bad channel with a 400 that names no field."""
    with pytest.raises(BadOptionError) as caught:
        options_from({"channel": word})
    assert "channel" in str(caught.value)


def test_the_portal_reads_a_channel_whatever_its_letter_case() -> None:
    """An operator who pastes a word in capitals means the same train."""
    assert options_from({"channel": "STABLE"}).ssr.channel == "stable"


# ---------------------------------------------------------------------------
# The download and the reboot schedule
# ---------------------------------------------------------------------------


def test_the_router_body_carries_the_chosen_download_moment() -> None:
    """The router schema reads the download start from this field."""
    options = options_from({"start_time": str(moment_soon())})
    body = build_body(routers(), options, GatewayFamily.SSR)
    assert body["start_time"] == moment_soon()


def test_the_router_body_carries_the_chosen_reboot_moment() -> None:
    """A router can write the firmware in one window and reboot in a later one."""
    options = options_from({"reboot": "yes", "reboot_at": str(moment_soon())})
    body = build_body(routers(), options, GatewayFamily.SSR)
    assert body["reboot_at"] == moment_soon()


def test_a_held_reboot_sends_the_value_that_disables_the_router_reboot() -> None:
    """That schema holds no reboot flag, so -1 is the one way to hold a reboot."""
    body = build_body(routers(), options_from({"reboot": "no"}), GatewayFamily.SSR)
    assert body["reboot_at"] == -1


def test_a_held_reboot_never_sends_the_reboot_flag_of_a_switch() -> None:
    """The router schema holds no reboot field, so the cloud would refuse it."""
    body = build_body(routers(), options_from({"reboot": "no"}), GatewayFamily.SSR)
    assert "reboot" not in body


def test_a_held_reboot_replaces_a_chosen_reboot_moment() -> None:
    """One body cannot name a reboot window and hold the reboot at once."""
    options = options_from({"reboot": "no", "reboot_at": str(moment_soon())})
    body = build_body(routers(), options, GatewayFamily.SSR)
    assert body["reboot_at"] == -1


# ---------------------------------------------------------------------------
# The strategy and the request scope
# ---------------------------------------------------------------------------


def test_the_router_body_carries_the_serial_strategy() -> None:
    """The router schema names big_bang and serial, so serial must reach it."""
    body = build_body(routers(), options_from({"strategy": STRATEGY_SERIAL}), GatewayFamily.SSR)
    assert body["strategy"] == STRATEGY_SERIAL


def test_the_request_names_only_the_selected_routers() -> None:
    """The organization call must never reach a router of another site."""
    plans = plan_upgrade(routers(), options_from({}), ORG_ID, SITE_ID)
    assert plans[0].body["device_ids"] == [
        f"{ID_PREFIX}{MAC_FIRST_ROUTER}",
        f"{ID_PREFIX}{MAC_SECOND_ROUTER}",
    ]


def test_the_router_plan_keeps_the_organization_scope_and_endpoint() -> None:
    """That family owns the one cancel call, and it lives at organization scope."""
    plans = plan_upgrade(routers(), options_from({}), ORG_ID, SITE_ID)
    assert (plans[0].route.scope, plans[0].route.endpoint, plans[0].route.scope_id) == (
        SCOPE_ORG,
        ENDPOINT_ORG_SSRS,
        ORG_ID,
    )


# ---------------------------------------------------------------------------
# The high-availability pair
# ---------------------------------------------------------------------------


def test_a_pair_under_one_wave_reads_the_high_availability_warning() -> None:
    """Two routers of one site may carry the wide area network together."""
    plans = plan_upgrade(routers(), options_from({"strategy": "big_bang"}), ORG_ID, SITE_ID)
    assert any("high-availability pair" in sentence for sentence in plans[0].warnings)


def test_the_high_availability_warning_names_the_count_of_routers() -> None:
    """An operator who reads a count can match it against the device table."""
    plans = plan_upgrade(routers(), options_from({"strategy": "big_bang"}), ORG_ID, SITE_ID)
    assert any("2 session smart routers" in sentence for sentence in plans[0].warnings)


def test_a_serial_pair_reads_no_high_availability_warning() -> None:
    """The serial order already keeps one router of the pair in service."""
    plans = plan_upgrade(routers(), options_from({"strategy": STRATEGY_SERIAL}), ORG_ID, SITE_ID)
    assert not any("high-availability pair" in sentence for sentence in plans[0].warnings)


def test_one_router_reads_no_high_availability_warning() -> None:
    """One router forms no pair, so the sentence would name a risk that is absent."""
    single = (target(MAC_FIRST_ROUTER, "gateway", "SSR130"),)
    plans = plan_upgrade(single, options_from({"strategy": "big_bang"}), ORG_ID, SITE_ID)
    assert not any("high-availability pair" in sentence for sentence in plans[0].warnings)


def test_a_pair_of_switches_reads_no_high_availability_warning() -> None:
    """The sentence names a router risk, so no other family may read it."""
    pair = (target(MAC_SWITCH, "switch", "EX4100-48P"), target(MAC_SECOND_ROUTER, "switch", "EX4100-48P"))
    plans = plan_upgrade(pair, options_from({"strategy": "big_bang"}), ORG_ID, SITE_ID)
    assert not any("high-availability pair" in sentence for sentence in plans[0].warnings)


def test_the_portal_keeps_the_wave_that_the_operator_chose() -> None:
    """A silent change to serial would run an order that nobody reviewed."""
    plans = plan_upgrade(routers(), options_from({"strategy": "big_bang"}), ORG_ID, SITE_ID)
    assert plans[0].body["strategy"] == "big_bang"


# ---------------------------------------------------------------------------
# The saved run
# ---------------------------------------------------------------------------


def test_a_saved_router_choice_returns_through_the_store() -> None:
    """A run that reopens must replay the train that the operator picked."""
    stored = build_option_record({"channel": "beta", "strategy": STRATEGY_SERIAL})
    replayed = build_options(json.loads(json.dumps(stored)), now=None)
    assert (replayed.ssr.channel, replayed.strategy) == ("beta", STRATEGY_SERIAL)


def test_the_stored_record_nests_the_router_settings_under_one_key() -> None:
    """One nested group keeps the record readable and the five-item rule kept."""
    assert build_option_record({"channel": "alpha"})["ssr"] == {"channel": "alpha"}


def test_a_stored_record_survives_the_dataclass_writer() -> None:
    """The driver replays the record through ``asdict``, which keeps the nesting."""
    stored = asdict(options_from({"channel": "beta"}))
    assert build_options(stored, now=None).ssr.channel == "beta"


def test_the_options_page_reopens_with_the_saved_channel() -> None:
    """An operator who edits one control must not lose the others."""
    stored = build_option_record({"channel": "stable"})
    assert advanced_option_values(stored)["channel"] == "stable"


def test_the_options_page_reopens_with_the_saved_download_moment() -> None:
    """The page shows the duration that the operator wrote, not the epoch behind it."""
    stored = build_option_record({"start_time": "8h"})
    assert advanced_option_values(stored)["start_time"] == "8h"


def test_a_run_with_no_router_choice_shows_an_empty_channel_control() -> None:
    """An empty text is the word that every control reads as "no choice"."""
    assert advanced_option_values(build_option_record({}))["channel"] == ""


# ---------------------------------------------------------------------------
# The visibility rule of the page
# ---------------------------------------------------------------------------


def test_a_router_row_names_its_gateway_family_for_the_page() -> None:
    """The page cannot read the model rules, so the row carries the family."""
    device = {"mac": MAC_FIRST_ROUTER, "name": "wan1", "type": "gateway", "model": "SSR130", "version": "5.4.0-100"}
    rows = build_version_options([device], {"SSR130": ("6.1.2-33",)})
    assert rows[0]["gateway_family"] == GatewayFamily.SSR.value


def test_a_switch_row_names_no_gateway_family() -> None:
    """A switch belongs to no gateway family, so the router controls stay hidden."""
    device = {"mac": MAC_SWITCH, "name": "sw1", "type": "switch", "model": "EX4100-48P", "version": "23.4R2-S3"}
    rows = build_version_options([device], {"EX4100-48P": ("23.4R2-S4",)})
    assert rows[0]["gateway_family"] == ""


def test_a_junos_gateway_row_names_the_other_gateway_family() -> None:
    """A Junos gateway reads no channel, so its family must differ from a router."""
    device = {"mac": MAC_SWITCH, "name": "fw1", "type": "gateway", "model": "SRX345", "version": "23.4R2-S3"}
    rows = build_version_options([device], {"SRX345": ("23.4R2-S4",)})
    assert rows[0]["gateway_family"] == GatewayFamily.JUNOS.value


# ---------------------------------------------------------------------------
# Issue #2187: the schedule as a duration
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "seconds"),
    [("200s", 200), ("5m", 300), ("8h", 28800), ("3d", 259200), ("0s", 0), ("5 m", 300)],
)
def test_each_duration_reads_as_its_count_of_seconds(text: str, seconds: int) -> None:
    """The four units cover every window that a maintenance plan uses."""
    assert parse_duration_seconds(text, "start_time") == seconds


@pytest.mark.parametrize("bad", ["300", "5x", "m", "-5m", "5.5m", "400d", "", "s"])
def test_the_portal_refuses_a_duration_that_no_rule_maps(bad: str) -> None:
    """A bare number reads as seconds to one operator and as minutes to another."""
    with pytest.raises(BadOptionError):
        parse_duration_seconds(bad, "start_time")


@pytest.mark.parametrize(("seconds", "text"), [(200, "200s"), (300, "5m"), (28800, "8h"), (259200, "3d"), (90, "90s")])
def test_a_duration_reads_back_in_the_largest_unit_that_fits(seconds: int, text: str) -> None:
    """The page shows the operator a value that they recognise."""
    assert format_duration(seconds) == text


def test_the_duration_reaches_the_body_as_a_moment() -> None:
    """The cloud takes an epoch second, so the portal converts the duration."""
    options = options_from({"start_time": "8h"})
    assert options.start_time == fixed_now() + 28800


def test_the_stored_record_keeps_the_duration_and_not_the_moment() -> None:
    """A saved run must replay against the clock of the start, not of the save."""
    stored = build_option_record({"start_time": "8h", "reboot_at": "3d"})
    assert stored["schedule"] == {"start_time_after": 28800, "reboot_at_after": 259200}


def test_a_saved_duration_resolves_against_a_later_clock() -> None:
    """An operator who reads the plan for ten minutes still gets the window asked for."""
    stored = build_option_record({"start_time": "8h"})
    later = build_options(stored, now=lambda: fixed_now() + 600)
    assert later.start_time == fixed_now() + 600 + 28800


def test_a_run_saved_before_this_change_keeps_its_stored_moment() -> None:
    """A stored epoch second read as a duration would move the run by about 60 years."""
    replayed = build_options({"start_time": fixed_now() + 3600}, now=fixed_now)
    assert (replayed.start_time, replayed.schedule.start_time_after) == (fixed_now() + 3600, None)


def test_an_empty_schedule_holds_no_duration_and_no_moment() -> None:
    """An empty control means the run begins at once."""
    options = options_from({})
    assert (options.start_time, options.schedule.start_time_after) == (None, None)


# ---------------------------------------------------------------------------
# Issue #2196: the schedule must survive the replay of the run driver
# ---------------------------------------------------------------------------


def test_a_stored_duration_reaches_a_moment_with_no_clock() -> None:
    """The run driver replays with no clock, and a duration still needs one.

    Why:
        The driver passes no clock, because an absolute epoch must skip the
        window guard when a run waits past its own start time. A duration counts
        from the start of the job instead, so it must resolve whatever the
        caller passed. Without this rule the moment left the request body, and
        the cloud wrote the firmware at once. Issue #2196 holds that report.
    """
    stored = build_option_record({"start_time": "2h"})
    replayed = build_options(stored, now=None)
    assert replayed.start_time is not None  # The moment must reach the body.


def test_the_replayed_moment_counts_from_the_replay(monkeypatch: pytest.MonkeyPatch) -> None:
    """A duration counts from the start of the job, not from the save."""
    monkeypatch.setattr(module_options, "_now_epoch", lambda: 1_900_000_000)
    stored = build_option_record({"reboot_at": "3h"})
    replayed = build_options(stored, now=None)
    assert replayed.reboot_at == 1_900_000_000 + 10800


def test_the_request_body_carries_the_stored_schedule() -> None:
    """The whole point of the schedule is that the cloud reads it."""
    stored = build_option_record({"start_time": "2h", "reboot_at": "3h", "reboot": "yes"})
    options = build_options(stored, now=None)
    body = build_body(switches_pair(), options, GatewayFamily.JUNOS)
    assert "start_time" in body  # The download window reaches the cloud.
    assert "reboot_at" in body  # The reboot window reaches the cloud.


def test_a_stored_epoch_still_skips_the_window_guard() -> None:
    """A run that waits past its own start time must still upgrade."""
    past = fixed_now() - 999_999  # A moment well outside the window that the guard allows.
    assert build_options({"start_time": past}, now=None).start_time == past


def switches_pair() -> tuple[DeviceTarget, ...]:
    """Return two switches, so no body takes the per-device path.

    Returns:
        Two switch targets of one model and one version.
    """
    return (
        target(MAC_SWITCH, "switch", "EX4100-48P"),
        target(MAC_FIRST_ROUTER, "switch", "EX4100-48P"),
    )
