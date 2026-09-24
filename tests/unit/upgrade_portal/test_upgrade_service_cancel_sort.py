"""Unit tests for the shared sort rule of one cancel.

Why:
    Issue #3246. The single-site stop and the access point child job of a
    multi-site operation now use one sort rule. These tests prove that the
    public rule keeps the three single-site outcomes. No test opens a socket.
"""

from __future__ import annotations

from src.firmware.upgrade_service import CancelOutcome, reboot_macs, sort_cancel

FIRST = "00:11:22:33:44:55"  # One device, in the colon spelling of an inventory row.
SECOND = "001122334466"  # A second device, in the bare spelling of the cloud.


def test_a_refused_cancel_keeps_every_device_in_the_writing_list() -> None:
    """A refusal stops no device, so the rule reports no stop."""
    refused = "The cloud refused the cancel with status 404, so every device continues the upgrade."
    assert sort_cancel((FIRST, SECOND), frozenset(), 404) == CancelOutcome((), (FIRST, SECOND), (), refused)


def test_an_unknown_state_keeps_every_device_in_the_writing_list() -> None:
    """An unread device state gives the doubt sentence, not a stop."""
    outcome = sort_cancel((FIRST, SECOND), None, 200)
    assert (outcome.cancelled, outcome.already_writing) == ((), (FIRST, SECOND))
    assert outcome.message.startswith("The cloud accepted the cancel for 2 device(s).")


def test_an_accepted_cancel_splits_the_devices_on_the_reboot_list() -> None:
    """A device on the reboot list can still write firmware, and each other device stopped."""
    outcome = sort_cancel((FIRST, SECOND), frozenset({"001122334455"}), 202)
    split = "The cloud stopped 1 device(s), and 1 device(s) may still finish the write."
    assert outcome == CancelOutcome((SECOND,), (FIRST,), (), split)


def test_the_reboot_reader_reads_the_list_inside_targets() -> None:
    """The cloud can write the reboot list inside the target lists."""
    assert reboot_macs({"targets": {"reboot_in_progress": ["00-11-22-33-44-55"]}}) == frozenset({"001122334455"})


def test_the_reboot_reader_reports_no_answer_for_a_damaged_list() -> None:
    """A text value is not a list, so the reader cannot tell which device writes firmware."""
    assert reboot_macs({"reboot_in_progress": "001122334455"}) is None


def test_an_empty_plan_names_no_device_in_any_list() -> None:
    """A cancel of a plan with no device names no device, and it claims no write."""
    empty = CancelOutcome((), (), (), "The cloud stopped 0 device(s), and no device was writing firmware.")
    assert sort_cancel((), frozenset(), 200) == empty


def test_the_reboot_reader_reads_an_empty_list_as_no_writing_device() -> None:
    """An empty reboot list of a real job means that no device writes firmware."""
    assert reboot_macs({"targets": {"reboot_in_progress": []}}) == frozenset()


def test_the_reboot_reader_reports_no_answer_for_an_empty_payload() -> None:
    """An empty payload is not a job, so the reader cannot tell which device writes firmware."""
    assert reboot_macs({}) is None
