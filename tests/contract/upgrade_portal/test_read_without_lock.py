"""Contract tests for the read of a run and a capture without the site lock.

Why:
    Issue #2200 records the gap. One operator holds a site at a time, and a
    second operator who wanted to watch a running upgrade had no way to open it.
    A read changes nothing, so the lock must not gate it.

    The write half matters more than the read half. A control that stays live
    for an operator who does not hold the site invites a press, and the operator
    learns of the refusal only after the press. The page therefore renders the
    control shut and names the reason.

    Warning: the count of devices under upgrade must reach the takeover box. A
    takeover moves a live firmware write to the second operator, and that
    operator must read the size of what they take.
"""

from __future__ import annotations

import re

import pytest

from src.upgrade_portal.app.routes import select, upgrade

# One run that writes firmware now, and one that ended. The takeover box names
# the device count of the first and no count for the second.
LIVE_RUN = {"state": "upgrade_running", "targets": [{"mac": "a"}, {"mac": "b"}, {"mac": "c"}]}
FINISHED_RUN = {"state": "complete", "targets": [{"mac": "a"}, {"mac": "b"}]}

# Every state in which the cloud may still write firmware to a device.
LIVE_STATES = sorted(upgrade.LIVE_UPGRADE_STATES)


@pytest.mark.parametrize("state", LIVE_STATES)
def test_a_live_run_names_its_device_count(state: str) -> None:
    """The takeover box needs the size of the write that it moves.

    Args:
        state: The live run state under test.
    """
    assert upgrade.live_upgrade_device_count({"state": state, "targets": [{"mac": "a"}]}) == 1


@pytest.mark.parametrize("state", ["created", "awaiting_confirmation", "complete", "failed", "stopped"])
def test_a_run_that_writes_no_firmware_names_no_count(state: str) -> None:
    """A count from a run that ended would name firmware that never moves.

    Args:
        state: The state of a run that writes to no device.
    """
    assert upgrade.live_upgrade_device_count({"state": state, "targets": [{"mac": "a"}]}) == 0


def test_an_empty_record_names_no_count() -> None:
    """A page with no run names no firmware in flight."""
    assert upgrade.live_upgrade_device_count({}) == 0


def test_the_holder_may_write() -> None:
    """The banner of the holder opens every control that writes to the site."""
    banner = select.build_lock_banner("site-1", select.LOCK_STATE_HELD, "one@example.com", 0, "token")
    assert banner["lock_write_allowed"] is True


def test_a_site_that_another_operator_holds_refuses_the_write() -> None:
    """The one state that shuts a write control is a site that another holds.

    Why:
        The server refuses such a call with 409 site_locked. A control that
        stayed live would answer that refusal only after the press, and the
        operator would learn of the hold by losing time.
    """
    banner = select.build_lock_banner("site-1", select.LOCK_STATE_LOCKED, "one@example.com", 60, "")
    assert banner["lock_write_allowed"] is False


@pytest.mark.parametrize("state", ["free", "unknown", "site_unknown"])
def test_every_other_state_leaves_the_control_live(state: str) -> None:
    """A free site and an unreadable lock store must not stop honest work.

    Why:
        The server is the real guard. A control that shut on a free site would
        refuse work that the server accepts. A control that shut on an
        unreadable store would stop every operator whenever Redis blinked, and
        `contracts/site-lock.md` states that a read never needs that store.

    Args:
        state: The lock state under test.
    """
    assert select.build_lock_banner("site-1", state, "", 0, "")["lock_write_allowed"] is True


def test_the_banner_carries_the_upgrade_device_count() -> None:
    """The takeover box reads this count from the banner context."""
    banner = select.build_lock_banner("site-1", "locked", "one@example.com", 60, "", upgrade_devices=3)
    assert banner["lock_upgrade_devices"] == 3


def test_the_banner_names_no_count_by_default() -> None:
    """A page with no live run hides the count sentence."""
    assert select.build_lock_banner("site-1", "locked", "one@example.com", 60, "")["lock_upgrade_devices"] == 0


def test_the_run_banner_reads_the_live_count() -> None:
    """The run page passes the count of its own record into the banner.

    Why:
        The banner builder reads a site and never a run, so the run page must
        supply the count. Without this the takeover box would name no size.
    """
    record = {"org_id": "", "site_id": "", **LIVE_RUN}  # No site reads as `site_unknown`, which still renders.
    assert upgrade.run_lock_banner(record)["lock_upgrade_devices"] == 3


def test_the_run_banner_names_no_count_for_a_finished_run() -> None:
    """A run that ended moves no firmware, so the takeover box states no size."""
    record = {"org_id": "", "site_id": "", **FINISHED_RUN}
    assert upgrade.run_lock_banner(record)["lock_upgrade_devices"] == 0


def test_no_banner_value_holds_a_lock_token_of_another_operator() -> None:
    """A reader without the lock must reach no token.

    Why:
        The token is the one proof of a hold. A page that leaked the token of
        the holder would let a reader write as that operator.
    """
    banner = select.build_lock_banner("site-1", "locked", "one@example.com", 60, "")
    assert banner["lock_token"] == ""


def test_the_holder_address_reads_as_an_address_and_not_a_token() -> None:
    """The waiting operator learns whom to ask, and learns nothing else."""
    banner = select.build_lock_banner("site-1", "locked", "one@example.com", 60, "")
    assert banner["lock_holder"] == "one@example.com"
    assert not re.search(r"[0-9a-f]{32}", banner["lock_holder"])  # No token shape reaches the page.
