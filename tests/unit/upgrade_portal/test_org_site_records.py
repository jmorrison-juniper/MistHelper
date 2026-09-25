"""Unit tests for the site records and the site refusal of the multi-site save.

Why:
    Issue #3389. The multi-site save kept the options of the last site only.
    A site with no device answers an empty record, so the choices of the
    operator became the defaults when that site came last. These tests call
    the class directly, so they need no route, no cloud, and no browser.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.upgrade.org_site_records import (
    NAME_LIMIT,
    UNPLANNED_MESSAGE,
    UNREAD_MESSAGE,
    OrgSiteRecords,
    OrgSiteRefusal,
)

FIRST_SITE = "site-one"  # The first selected site of each test.
SECOND_SITE = "site-two"  # The second selected site of each test.
THIRD_SITE = "site-three"  # The third selected site of each test.
CANARY_OPTIONS = {"strategy": "canary", "canary_phases": [1, 10, 50, 100]}  # The choices of the operator.
AP_TARGET = {"mac": "0011223344a1", "version_target": "0.15.1"}  # One planned access point.
SWITCH_TARGET = {"mac": "0011223344b1", "version_target": "23.4R1.9"}  # One planned switch.


def answered(*targets: dict[str, str]) -> dict[str, Any]:
    """Return the record of a site that answered, with the named targets."""
    return {"targets": list(targets), "options": dict(CANARY_OPTIONS), "warnings": []}  # The mapper shape.


def upper_labels(site_ids: list[str]) -> list[str]:
    """Return a label for each site, so a test can tell a label from an identifier."""
    return [site_id.upper() for site_id in site_ids]  # One label for each site, in the same order.


def test_an_empty_last_record_keeps_the_options_of_the_operator() -> None:
    """FR-001: an empty record never replaces the options of a site that answered."""
    records = OrgSiteRecords()  # One save.
    records.add(FIRST_SITE, answered(AP_TARGET))  # The first site answers with the choices of the operator.
    records.add(SECOND_SITE, {})  # The shipped mapper answers an empty record for a site with no device.
    assert records.options == CANARY_OPTIONS  # The old save kept the empty options of the last site.
    assert records.unread_sites == [SECOND_SITE]  # The refusal can name the empty site.


def test_each_target_names_its_site() -> None:
    """Each target carries the site that holds the device."""
    records = OrgSiteRecords()  # One save.
    records.add(FIRST_SITE, answered(AP_TARGET))  # The access point of the first site.
    records.add(SECOND_SITE, answered(SWITCH_TARGET))  # The switch of the second site.
    assert [target["site_id"] for target in records.targets] == [FIRST_SITE, SECOND_SITE]  # The order stays.
    assert records.targets[0]["mac"] == AP_TARGET["mac"]  # Each target keeps the fields of the mapper.


def test_an_empty_record_gives_the_unread_refusal() -> None:
    """FR-002: a site with an empty record stops the save, and the refusal names the site."""
    records = OrgSiteRecords()  # One save.
    records.add(FIRST_SITE, {})  # The first site answers an empty record.
    records.add(SECOND_SITE, answered(AP_TARGET))  # The second site answers.
    refusal = records.refusal(upper_labels)  # Build the refusal with a label for each site.
    assert isinstance(refusal, OrgSiteRefusal)  # The save stops.
    assert str(refusal) == UNREAD_MESSAGE.format(names="SITE-ONE")  # The text names the label, not the identifier.
    assert refusal.labels == ["SITE-ONE"]  # A caller can read the refused sites.


def test_options_that_are_not_a_mapping_count_as_unread() -> None:
    """A record whose options value is not a mapping reads as a site that answered nothing."""
    records = OrgSiteRecords()  # One save.
    records.add(FIRST_SITE, {"targets": [AP_TARGET], "options": ["canary"]})  # A shape that no mapper writes.
    assert records.unread_sites == [FIRST_SITE]  # The refusal can name the site.
    assert records.targets == []  # The targets of a broken record never reach the plan.
    assert records.options is None  # A broken record never gives the options of the plan.


def test_a_site_with_no_target_gives_the_unplanned_refusal() -> None:
    """FR-003: a site with no planned device stops the save when another site holds a device."""
    records = OrgSiteRecords()  # One save.
    records.add(FIRST_SITE, answered(AP_TARGET))  # The first site holds a planned device.
    records.add(SECOND_SITE, answered())  # The second site answers with no planned device.
    refusal = records.refusal(upper_labels)  # Build the refusal with a label for each site.
    assert isinstance(refusal, OrgSiteRefusal)  # The save stops.
    assert str(refusal) == UNPLANNED_MESSAGE.format(names="SITE-TWO")  # The text names the site with no device.


@pytest.mark.parametrize("every_site_planned", [True, False], ids=["plain-save", "retry-save"])
def test_no_target_at_any_site_gives_no_new_refusal(every_site_planned: bool) -> None:
    """FR-004: the old refusal of the route applies when no site holds a target, in a retry too."""
    records = OrgSiteRecords(every_site_planned)  # One save.
    records.add(FIRST_SITE, answered())  # No planned device at the first site.
    records.add(SECOND_SITE, answered())  # No planned device at the second site.
    assert records.refusal(upper_labels) is None  # The route keeps its old refusal.
    assert records.targets == []  # The plan holds no device.
    assert records.options == CANARY_OPTIONS  # The options still come from a site that answered.


def test_the_unread_refusal_comes_before_the_unplanned_refusal() -> None:
    """A site with an empty record gives the first refusal, because a new read can change the plan."""
    records = OrgSiteRecords()  # One save.
    records.add(FIRST_SITE, answered(AP_TARGET))  # The first site holds a planned device.
    records.add(SECOND_SITE, answered())  # The second site holds no planned device.
    records.add(THIRD_SITE, {})  # The third site answers an empty record.
    refusal = records.refusal(upper_labels)  # Build the refusal with a label for each site.
    assert isinstance(refusal, OrgSiteRefusal)  # The save stops.
    assert str(refusal) == UNREAD_MESSAGE.format(names="SITE-THREE")  # The unread site comes first.


def test_every_site_that_answered_gives_no_refusal() -> None:
    """A plan with a device at each selected site gives no refusal."""
    records = OrgSiteRecords()  # One save.
    records.add(FIRST_SITE, answered(AP_TARGET))  # The first site holds a planned device.
    records.add(SECOND_SITE, answered(SWITCH_TARGET))  # The second site holds a planned device.
    assert records.refusal(upper_labels) is None  # The plan covers each selected site.


def test_a_retry_plans_the_other_sites_when_one_site_holds_no_retry_device() -> None:
    """FR-008: a retry of issue #3247 saves the retry devices of the other sites."""
    records = OrgSiteRecords(every_site_planned=False)  # One retry save.
    records.add(FIRST_SITE, answered())  # The operator cleared the device type of the retry device here.
    records.add(SECOND_SITE, answered(AP_TARGET))  # The second site holds a retry device.
    assert records.refusal(upper_labels) is None  # The Sites page would end the retry, so no refusal.
    assert [target["site_id"] for target in records.targets] == [SECOND_SITE]  # Only the retry device.
    assert records.unplanned_sites == [FIRST_SITE]  # The record still knows the site with no device.


def test_a_retry_still_refuses_a_site_with_an_empty_record() -> None:
    """FR-008: an empty record stops a retry save too, because a new read can change the plan."""
    records = OrgSiteRecords(every_site_planned=False)  # One retry save.
    records.add(FIRST_SITE, {})  # The inventory read of the first site found no device.
    records.add(SECOND_SITE, answered(AP_TARGET))  # The second site holds a retry device.
    refusal = records.refusal(upper_labels)  # Build the refusal with a label for each site.
    assert isinstance(refusal, OrgSiteRefusal)  # The save stops, and no retry device goes missing.
    assert str(refusal) == UNREAD_MESSAGE.format(names="SITE-ONE")  # The text names the unread site.


def test_the_labels_come_only_for_the_refused_sites() -> None:
    """The label reader receives only the sites that the refusal names, in the order of the selection."""
    received: list[list[str]] = []  # Each call of the label reader.

    def spy(site_ids: list[str]) -> list[str]:
        """Record each call, and return the identifiers."""
        received.append(list(site_ids))  # Keep a copy of the call.
        return list(site_ids)  # The identifiers serve as the labels.

    records = OrgSiteRecords()  # One save.
    records.add(THIRD_SITE, {})  # The first unread site of the selection.
    records.add(FIRST_SITE, answered(AP_TARGET))  # A site that answered, which the reader must not receive.
    records.add(SECOND_SITE, {})  # The second unread site of the selection.
    records.refusal(spy)  # Build the refusal.
    assert received == [[THIRD_SITE, SECOND_SITE]]  # One call, with the unread sites in the selection order.


def test_no_refusal_reads_no_label() -> None:
    """A save with no refusal never reads the site names."""
    received: list[list[str]] = []  # Each call of the label reader.

    def spy(site_ids: list[str]) -> list[str]:
        """Record each call, and return the identifiers."""
        received.append(list(site_ids))  # Keep a copy of the call.
        return list(site_ids)  # The identifiers serve as the labels.

    records = OrgSiteRecords()  # One save.
    records.add(FIRST_SITE, answered(AP_TARGET))  # The only site holds a planned device.
    assert records.refusal(spy) is None  # The plan covers each selected site.
    assert received == []  # An accepted save sends no site list read to the cloud.


def test_the_message_shows_ten_names_and_the_count_of_the_rest() -> None:
    """FR-006: a long list shows ten names, and then the count of the other sites."""
    labels = [f"Site {number}" for number in range(1, NAME_LIMIT + 3)]  # Two names more than the limit.
    refusal = OrgSiteRefusal(UNREAD_MESSAGE, labels)  # Build the refusal text.
    shown = ", ".join(labels[:NAME_LIMIT])  # The names that the message shows.
    assert str(refusal) == UNREAD_MESSAGE.format(names=f"{shown}, and 2 more")  # The count of the other sites.
    assert refusal.labels == labels  # The refusal keeps each label for a caller.


def test_the_message_shows_every_name_up_to_the_limit() -> None:
    """FR-006: a list at the limit shows each name and no count."""
    labels = [f"Site {number}" for number in range(1, NAME_LIMIT + 1)]  # Exactly the limit.
    refusal = OrgSiteRefusal(UNPLANNED_MESSAGE, labels)  # Build the refusal text.
    assert str(refusal) == UNPLANNED_MESSAGE.format(names=", ".join(labels))  # Each name shows.
    assert "more" not in str(refusal)  # No count follows a list at the limit.


def test_the_route_catches_the_refusal_as_a_value_error() -> None:
    """The save route answers each `ValueError` with status 400 and the message text."""
    with pytest.raises(ValueError, match=r"these sites: Empty Site\.") as caught:  # The family of the route.
        raise OrgSiteRefusal(UNREAD_MESSAGE, ["Empty Site"])  # The refusal that the route raises.
    assert caught.value.labels == ["Empty Site"]  # The caught error keeps the refused sites.
