"""Unit tests for the sort of the access points after one organization cancel.

Why:
    Issue #3246. The single-site stop shows which devices stopped, which
    devices can still write firmware, and which devices have no cancel path.
    The access point child job of a multi-site operation stored only the
    status word of its cancel. These tests prove each rule of the new sort. No
    test opens a socket.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.firmware.org_cancel_sort import UNCONFIRMED_TEXT, OrgCancelSort, OrgRebootLists
from src.firmware.org_upgrade_service import OrgUpgradeResult

ORG_ID = "11111111-1111-1111-1111-111111111111"  # The organization of each child job.
SITE_ONE = "22222222-2222-2222-2222-222222222222"  # The first site of the child job.
SITE_TWO = "33333333-3333-3333-3333-333333333333"  # The second site of the child job.
AP_ONE = "001122334455"  # The access point at the first site.
AP_TWO = "001122334466"  # The access point at the second site.
BOTH_SITES = frozenset({SITE_ONE, SITE_TWO})  # The sites of the child job.
ACCEPTED = OrgUpgradeResult(ORG_ID, "ap-job", 200, {}, None)  # The cloud accepted the cancel.


def nested(site_id: str, rebooting: Any) -> dict[str, Any]:
    """Build one site entry in the shape of the real cloud answer."""
    job = {"id": f"job-{site_id[:4]}", "status": "upgrading", "targets": {"reboot_in_progress": rebooting}}
    return {"site_id": site_id, "upgrade": job}  # The cloud nests the site job under "upgrade".


def ap_child(status_data: Any) -> dict[str, Any]:
    """Build the access point child job of both sites with one stored status read."""
    return {
        "child_id": "child-ap",
        "route": "upgradeOrgDevices",
        "targets": [{"mac": AP_ONE, "site_id": SITE_ONE}, {"mac": AP_TWO, "site_id": SITE_TWO}],
        "target_ids": [AP_ONE, AP_TWO],
        "status_data": status_data,
    }


def test_writing_reads_the_nested_list_of_each_site() -> None:
    """The real answer nests each list, and the reader normalizes each MAC spelling."""
    answer = {"upgrades": [nested(SITE_ONE, ["00:11:22:33:44:55"]), nested(SITE_TWO, [])]}
    assert OrgRebootLists.writing(answer, BOTH_SITES) == frozenset({AP_ONE})


def test_writing_reads_the_site_upgrades_field_with_entry_targets() -> None:
    """An earlier answer shape holds the target lists in the site entry itself."""
    answer = {
        "site_upgrades": [
            {"site_id": SITE_ONE, "status": "running", "targets": {"reboot_in_progress": [AP_TWO]}},
            {"site_id": SITE_TWO, "status": "running", "targets": {}},
        ]
    }
    assert OrgRebootLists.writing(answer, BOTH_SITES) == frozenset({AP_TWO})


def test_writing_uses_a_root_list_that_covers_every_site() -> None:
    """A root target list names the devices of every site."""
    answer = {"id": "ap-job", "status": "upgrading", "targets": {"reboot_in_progress": [AP_TWO]}}
    assert OrgRebootLists.writing(answer, BOTH_SITES) == frozenset({AP_TWO})


@pytest.mark.parametrize(
    "answer",
    [
        pytest.param(None, id="no-answer"),
        pytest.param({"id": "ap-job"}, id="no-site-entry"),
        pytest.param({"status": "upgrading"}, id="a-root-word-alone"),
        pytest.param({"upgrades": [nested(SITE_ONE, [])]}, id="one-site-missing"),
        pytest.param(
            {"upgrades": [nested(SITE_ONE, []), {"site_id": SITE_TWO, "upgrade_id": "job-two"}]},
            id="a-reference-entry",
        ),
        pytest.param(
            {"upgrades": [nested(SITE_ONE, []), nested(SITE_TWO, [])], "site_upgrades": [{"site_id": SITE_TWO}]},
            id="one-unread-entry-of-a-read-site",
        ),
        pytest.param({"upgrades": [nested(SITE_ONE, "001122334455"), nested(SITE_TWO, [])]}, id="a-damaged-list"),
        pytest.param({"upgrades": "damaged"}, id="a-damaged-field"),
        pytest.param({"upgrades": [["damaged"], nested(SITE_TWO, [])]}, id="a-damaged-entry"),
        pytest.param({"upgrades": [{"upgrade": {"targets": {}}}]}, id="an-entry-with-no-site"),
        pytest.param({"targets": {"reboot_in_progress": "damaged"}}, id="a-damaged-root-list"),
    ],
)
def test_writing_is_unknown_when_a_site_list_is_missing_or_damaged(answer: Any) -> None:
    """The portal never guesses a list that the answer does not hold."""
    assert OrgRebootLists.writing(answer, BOTH_SITES) is None


def test_an_accepted_cancel_sorts_each_access_point() -> None:
    """One access point reboots, so it can still write firmware, and the other stopped."""
    child = ap_child({"upgrades": [nested(SITE_ONE, []), nested(SITE_TWO, [AP_TWO])]})
    assert OrgCancelSort.result(child, ACCEPTED) == {
        "status": "requested",
        "raw_status": 200,
        "cancelled": [AP_ONE],
        "already_writing": [AP_TWO],
        "no_cancel_available": [],
        "message": "The cloud stopped 1 device(s), and 1 device(s) may still finish the write.",
    }


def test_an_unread_site_lists_every_access_point_as_writing() -> None:
    """The cloud accepted the cancel, but the stored answer names no site list."""
    result = OrgCancelSort.result(ap_child({"id": "ap-job"}), ACCEPTED)
    assert (result["status"], result["cancelled"], result["already_writing"]) == ("requested", [], [AP_ONE, AP_TWO])
    assert result["message"].startswith("The cloud accepted the cancel for 2 device(s).")


def test_a_refused_cancel_lists_every_access_point_as_writing() -> None:
    """A cloud error keeps its text, and the portal claims no stop."""
    refused = OrgUpgradeResult(ORG_ID, "ap-job", 404, {}, "The cloud returned HTTP 404.")
    result = OrgCancelSort.result(ap_child({"upgrades": [nested(SITE_ONE, []), nested(SITE_TWO, [])]}), refused)
    assert (result["status"], result["raw_status"], result["cancelled"]) == ("failed", 404, [])
    assert result["already_writing"] == [AP_ONE, AP_TWO]
    assert result["message"] == f"The cloud returned HTTP 404. {UNCONFIRMED_TEXT}"


def test_an_earlier_record_without_targets_reads_as_unknown() -> None:
    """A record from an earlier release names no site for each access point, so no site list applies."""
    child = ap_child({"upgrades": [nested(SITE_ONE, []), nested(SITE_TWO, [])]})
    del child["targets"]  # The record holds only the target identifiers.
    result = OrgCancelSort.result(child, ACCEPTED)
    assert (result["cancelled"], result["already_writing"]) == ([], [AP_ONE, AP_TWO])
