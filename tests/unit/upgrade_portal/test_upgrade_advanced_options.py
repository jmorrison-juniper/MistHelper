"""Unit tests for the advanced upgrade controls of issue #2156.

Why:
    The portal exposed four upgrade fields and the cloud schema holds eighteen.
    Issue #2156 adds the nine remaining control families. Each one reaches the
    cloud only under its own condition, and a field outside that condition makes
    the cloud refuse the whole call with a message that names no field.

    These tests read
    ``documentation/api/utilities/POST_sites_site_id_devices_upgrade.md`` and
    prove that each field lands in the body that its own schema holds, and lands
    in no other body.

Scope:
    ``build_options`` and ``build_body`` only. Both are pure, so no test here
    reaches the Mist cloud.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import json  # One test replays a record through a JSON store.
from dataclasses import asdict  # The store keeps the option record through this call.
from typing import Any  # A request body is free-form.

import pytest  # The test framework of the project.

from src.firmware.upgrade_service import (
    DeviceTarget,
    GatewayFamily,
    UpgradeOptions,
    build_body,
    plan_upgrade,
)
from src.upgrade_portal.upgrade.options import (
    BadOptionError,
    advanced_option_values,
    build_options,
)

SITE_ID = "11111111-1111-1111-1111-111111111111"
ORG_ID = "22222222-2222-2222-2222-222222222222"

MAC_AP = "5c5b350e0001"
MAC_SECOND_AP = "5c5b350e0002"
MAC_SWITCH = "5c5b350e0003"
MAC_SSR = "5c5b350e0004"

# WHY: A moment two hours ahead sits inside the window that `_guard_start_time`
# accepts. A fixed epoch would fall behind that window as the calendar moves,
# and the whole module would fail one day for no code change at all.
TWO_HOURS_SECONDS = 7200


def moment_soon() -> int:
    """Return a moment that the schedule guard accepts.

    Returns:
        A moment two hours ahead of the stand-in clock.
    """
    return fixed_now() + TWO_HOURS_SECONDS


def fixed_now() -> int:
    """Return the stand-in clock of every test of this module.

    Why:
        The schedule guard compares a chosen moment against now. A fixed clock
        keeps every test of this module independent of the machine that runs it.

    Returns:
        One fixed moment in epoch seconds.
    """
    return 1_800_000_000


def target(mac: str, device_type: str, model: str, version: str) -> DeviceTarget:
    """Return one device target for a body test.

    Args:
        mac: The device address with no separator.
        device_type: The Mist device type word.
        model: The device model text.
        version: The version that the operator picked.

    Returns:
        One device target.
    """
    return DeviceTarget(
        mac=mac,
        name=f"device-{mac[-4:]}",
        device_type=device_type,
        model=model,
        version_before="0.0.1",
        version_target=version,
        site_id=SITE_ID,
    )


def access_points() -> tuple[DeviceTarget, ...]:
    """Return two access points, so no body takes the per-device path.

    Returns:
        Two access point targets of one model and one version.
    """
    return (
        target(MAC_AP, "ap", "AP45", "0.14.29587"),
        target(MAC_SECOND_AP, "ap", "AP45", "0.14.29587"),
    )


def switches() -> tuple[DeviceTarget, ...]:
    """Return two switches, so no body takes the per-device path.

    Returns:
        Two switch targets of one model and one version.
    """
    return (
        target(MAC_SWITCH, "switch", "EX4100-48P", "23.4R2-S3"),
        target(MAC_SECOND_AP, "switch", "EX4100-48P", "23.4R2-S3"),
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
# The staged upgrade
# ---------------------------------------------------------------------------


def test_a_staged_run_carries_the_chosen_phases_instead_of_the_cloud_default() -> None:
    """A chosen phase list reaches the body, and the cloud default does not.

    Why:
        The cloud default of 1, 10, 50, and 100 suits a large site. A site of
        four switches needs its own phases, and a body that carried the default
        would upgrade one device in the first phase whatever the operator asked.
    """
    chosen = options_from({"strategy": "canary", "canary_phases": "25,50,100"})
    body = build_body(switches(), chosen, GatewayFamily.JUNOS)
    assert body["canary_phases"] == [25, 50, 100]  # The chosen list, and never the cloud default.


def test_a_staged_run_with_no_chosen_phases_keeps_the_cloud_default() -> None:
    """An empty phase control keeps the documented cloud default.

    Why:
        The contract asks the portal to keep the current behavior as the safe
        default. A run saved before this feature holds no phase list at all.
    """
    body = build_body(switches(), options_from({"strategy": "canary"}), GatewayFamily.JUNOS)
    assert body["canary_phases"] == [1, 10, 50, 100]  # The schema default at line 42 of the contract.


def test_a_failure_count_reaches_the_body_for_the_staged_strategy() -> None:
    """The per-phase failure count reaches the body beside the phase list."""
    chosen = options_from({"strategy": "canary", "canary_phases": "25,50,100", "max_failures": "1,2,4"})
    body = build_body(switches(), chosen, GatewayFamily.JUNOS)
    assert body["max_failures"] == [1, 2, 4]  # One count for each phase above.


def test_a_failure_count_list_of_the_wrong_length_is_refused() -> None:
    """A failure list that names fewer phases than the plan is refused.

    Why:
        The contract states that the two lists share one length. A shorter list
        would leave a later phase with no limit at all, and the run would
        continue through a failure that the operator meant to stop.
    """
    with pytest.raises(BadOptionError):
        options_from({"strategy": "canary", "canary_phases": "25,50,100", "max_failures": "1,2"})


def test_a_failure_percentage_reaches_every_strategy_above_one_write() -> None:
    """The failure percentage reaches the body of a staged run and a serial run."""
    for word in ("canary", "serial"):
        chosen = options_from({"strategy": word, "max_failure_percentage": "12"})
        body = build_body(switches(), chosen, GatewayFamily.JUNOS)
        assert body["max_failure_percentage"] == 12  # The schema reads the field above `big_bang`.


def test_a_failure_percentage_above_one_hundred_is_refused() -> None:
    """A percentage outside the documented range is refused.

    Why:
        The schema fixes the range 0 to 100 at lines 67 and 68. The cloud
        refusal names no field, so the portal must name it first.
    """
    with pytest.raises(BadOptionError):
        options_from({"strategy": "canary", "max_failure_percentage": "101"})


def test_a_phase_list_outside_the_staged_strategy_is_refused() -> None:
    """A phase list saved with one write of every device is refused.

    Why:
        The cloud reads the list for the staged strategy alone. A body that
        carried it under `big_bang` would drop it without a word, and the
        operator would read a staged plan that the cloud never runs.
    """
    with pytest.raises(BadOptionError):
        options_from({"strategy": "big_bang", "canary_phases": "25,50,100"})


def test_a_failure_percentage_with_one_write_of_every_device_is_refused() -> None:
    """A failure percentage saved with `big_bang` is refused for the same reason."""
    with pytest.raises(BadOptionError):
        options_from({"strategy": "big_bang", "max_failure_percentage": "12"})


# ---------------------------------------------------------------------------
# The access point settings
# ---------------------------------------------------------------------------


def test_the_peer_to_peer_settings_reach_an_access_point_body() -> None:
    """The three peer-to-peer fields reach an access point body together."""
    chosen = options_from({"enable_p2p": "yes", "p2p_cluster_size": "12", "p2p_parallelism": "3"})
    body = build_body(access_points(), chosen, GatewayFamily.JUNOS)
    assert body["enable_p2p"] is True
    assert body["p2p_cluster_size"] == 12
    assert body["p2p_parallelism"] == 3


def test_the_peer_to_peer_settings_reach_no_switch_body() -> None:
    """A switch body carries no peer-to-peer field.

    Why:
        The schema marks every peer-to-peer field "For APs only". A switch body
        that carried one would send a field that its own platform never reads.
    """
    chosen = options_from({"enable_p2p": "yes", "p2p_cluster_size": "12"})
    body = build_body(switches(), chosen, GatewayFamily.JUNOS)
    assert "enable_p2p" not in body
    assert "p2p_cluster_size" not in body


def test_a_cleared_peer_to_peer_control_sends_no_size_field() -> None:
    """A size without the flag reaches no body, because the cloud ignores it."""
    chosen = options_from({"enable_p2p": "no", "p2p_cluster_size": "12"})
    body = build_body(access_points(), chosen, GatewayFamily.JUNOS)
    assert "enable_p2p" not in body  # The default is false, so the field stays away.
    assert "p2p_cluster_size" not in body  # The schema reads it only with the flag.


def test_the_radio_settings_reach_an_access_point_body() -> None:
    """Every radio resource management field reaches an access point body."""
    chosen = options_from(
        {
            "strategy": "rrm",
            "rrm_first_batch_percentage": "2",
            "rrm_max_batch_percentage": "10",
            "rrm_node_order": "center_to_fringe",
            "rrm_mesh_upgrade": "sequential",
            "rrm_slow_ramp": "yes",
        }
    )
    body = build_body(access_points(), chosen, GatewayFamily.JUNOS)
    assert body["strategy"] == "rrm"
    assert body["rrm_first_batch_percentage"] == 2
    assert body["rrm_max_batch_percentage"] == 10
    assert body["rrm_node_order"] == "center_to_fringe"
    assert body["rrm_mesh_upgrade"] == "sequential"
    assert body["rrm_slow_ramp"] is True


def test_the_radio_strategy_reaches_no_switch_body() -> None:
    """A switch body drops the radio strategy word and every radio field.

    Why:
        The schema marks the word and every field "For APs only". The portal
        drops the word instead of a silent change to another strategy, which is
        the same rule that a session smart router already follows.
    """
    chosen = options_from({"strategy": "rrm", "rrm_node_order": "center_to_fringe"})
    body = build_body(switches(), chosen, GatewayFamily.JUNOS)
    assert "strategy" not in body  # A dropped word, and never a word nobody chose.
    assert "rrm_node_order" not in body


def test_a_radio_word_outside_the_documented_list_is_refused() -> None:
    """A radio word that the schema does not name is refused."""
    for field, value in (("rrm_node_order", "sideways"), ("rrm_mesh_upgrade", "at_once")):
        with pytest.raises(BadOptionError):
            options_from({"strategy": "rrm", field: value})


# ---------------------------------------------------------------------------
# The separate reboot window
# ---------------------------------------------------------------------------


def test_a_reboot_window_reaches_a_switch_body_with_the_reboot_on() -> None:
    """A separate reboot moment reaches a switch body that reboots."""
    chosen = options_from({"reboot": "yes", "reboot_at": str(moment_soon())})
    body = build_body(switches(), chosen, GatewayFamily.JUNOS)
    assert body["reboot"] is True
    assert body["reboot_at"] == moment_soon()


def test_a_reboot_window_reaches_no_body_with_the_reboot_held() -> None:
    """A held reboot sends no window, because the cloud reads none.

    Why:
        The schema reads `reboot_at` only when `reboot` is true. A window beside
        a held reboot would tell the operator that a reboot is planned when none
        is planned at all.
    """
    chosen = options_from({"reboot": "no", "reboot_at": str(moment_soon())})
    body = build_body(switches(), chosen, GatewayFamily.JUNOS)
    assert body["reboot"] is False
    assert "reboot_at" not in body


def test_a_reboot_window_already_past_is_refused_under_its_own_name() -> None:
    """A stale reboot moment is refused, and the refusal names the reboot field.

    Why:
        The window guard began as the start time guard. A refusal that named the
        start time for a bad reboot window would send the operator to the wrong
        control.
    """
    with pytest.raises(BadOptionError) as failure:
        options_from({"reboot": "yes", "reboot_at": str(fixed_now() - TWO_HOURS_SECONDS)})
    assert failure.value.field == "reboot_at"  # The refusal names the control that holds the fault.


def test_a_session_smart_router_still_disables_its_reboot_with_the_documented_value() -> None:
    """A held reboot still reaches that family as the documented -1.

    Why:
        That schema holds no reboot flag. Issue #2156 adds an explicit window,
        and the older rule must keep working beside it.
    """
    router = (target(MAC_SSR, "gateway", "SSR120", "6.2.5"),)
    body = build_body(router, options_from({"reboot": "no"}), GatewayFamily.SSR)
    assert body["reboot_at"] == -1  # The one way that schema holds a reboot back.


# ---------------------------------------------------------------------------
# The force flag and the stable build
# ---------------------------------------------------------------------------


def test_the_force_flag_reaches_a_batch_body_and_stays_away_by_default() -> None:
    """The force flag reaches the body only when the operator sets it."""
    assert build_body(switches(), options_from({"force": "yes"}), GatewayFamily.JUNOS)["force"] is True
    assert "force" not in build_body(switches(), options_from({}), GatewayFamily.JUNOS)


def test_the_stable_choice_replaces_every_picked_version() -> None:
    """The stable choice sends the documented word instead of a version."""
    body = build_body(switches(), options_from({"stable_version": "yes"}), GatewayFamily.JUNOS)
    assert body["version"] == "stable"  # The word at line 197 of the contract.


def test_the_plan_warns_that_the_stable_choice_ignores_the_picked_versions() -> None:
    """The plan names the stable choice, because the table still shows versions.

    Why:
        The device table keeps showing the version of each device. An operator
        who reads that table and never reads this sentence believes the cloud
        installs what the page shows.
    """
    plans = plan_upgrade(switches(), options_from({"stable_version": "yes"}), ORG_ID, SITE_ID)
    joined = " ".join(plans[0].warnings)
    assert "stable build" in joined


def test_the_plan_warns_that_the_radio_strategy_misses_the_switches() -> None:
    """The plan names the groups that drop the radio strategy word."""
    mixed = access_points() + switches()
    plans = plan_upgrade(mixed, options_from({"strategy": "rrm"}), ORG_ID, SITE_ID)
    joined = " ".join(plans[0].warnings)
    assert "radio strategy reaches an access point only" in joined


# ---------------------------------------------------------------------------
# The saved run reload
# ---------------------------------------------------------------------------


def test_a_saved_option_record_replays_every_advanced_choice() -> None:
    """A stored record rebuilds the same option record it came from.

    Why:
        The store keeps the record through `asdict`, which nests the three
        advanced groups. The reader must accept that nested shape, or a saved
        run would replay with every advanced choice dropped and the cloud would
        run a plan that nobody picked.
    """
    chosen = options_from(
        {
            "strategy": "canary",
            "canary_phases": "25,50,100",
            "max_failures": "1,2,4",
            "max_failure_percentage": "12",
            "force": "yes",
            "enable_p2p": "yes",
            "p2p_cluster_size": "12",
        }
    )
    stored = asdict(chosen)  # The exact shape that `build_options_record` writes.
    assert build_options(stored, now=None) == chosen  # A replay keeps every choice.


def test_a_record_that_travelled_through_a_json_store_replays_the_same_way() -> None:
    """A record read back from JSON replays the same option record.

    Why:
        ArangoDB and the comma-separated fallback both turn a tuple into a list.
        A reader that accepted a tuple alone would drop every list field of a
        run that survived a portal restart.
    """
    chosen = options_from({"strategy": "canary", "canary_phases": "25,50,100"})
    stored = json.loads(json.dumps(asdict(chosen)))  # A tuple becomes a list here.
    assert build_options(stored, now=None) == chosen


def test_the_options_page_reopens_with_the_text_of_every_advanced_control() -> None:
    """The page reader answers the text of each saved advanced control.

    Why:
        Issue #2156 asks for a saved-run reload. An operator who edits one
        control and loses the other ten sends a plan that nobody reviewed.
    """
    stored = asdict(options_from({"strategy": "rrm", "rrm_slow_ramp": "yes", "p2p_cluster_size": "12"}))
    shown = advanced_option_values(stored)
    assert shown["rrm_slow_ramp"] == "yes"  # A boolean shows as the word the select offers.
    assert shown["p2p_cluster_size"] == "12"  # A number shows as its own text.
    assert shown["canary_phases"] == ""  # An untouched control shows an empty text.


def test_the_options_page_reader_answers_every_control_for_an_older_run() -> None:
    """A run saved before this feature draws every control with no value.

    Why:
        The contract asks a saved run without the new values to keep the current
        behavior. A missing key must read as "keep the cloud default", never as
        a fault page.
    """
    shown = advanced_option_values({"reboot": True, "strategy": "big_bang"})
    assert set(shown.values()) == {""}  # Every control shows the cloud default.
