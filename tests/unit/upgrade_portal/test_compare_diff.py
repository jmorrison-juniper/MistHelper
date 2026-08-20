"""Unit tests for the device comparison of two upgrade captures.

Why:
    Three faults in this module would each destroy the whole feature, and none
    of them raises an error. A comparison that reads ``uptime`` marks every
    upgraded device changed, because a reboot resets the uptime. A comparison
    that ignores the digests reads the whole document of a quiet site and
    misses the render budget. A comparison that treats an absent digest as a
    match reports a changed site as equal and hides a failed upgrade.

    Every test below feeds plain dictionaries. No test opens a socket, reads
    the ``.env`` file, or names a real credential.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.compare import diff

# WHY: Obviously fake addresses. A reader sees at once that no test reaches a
#      real site.
MASTER_MAC = "0011220000aa"
MEMBER_MAC = "0011220000bb"
NEW_MAC = "0011220000cc"

OLD_VERSION = "21.4R3.15"
NEW_VERSION = "23.4R2.13"

OLD_UPTIME = 900000
NEW_UPTIME = 120

DIGEST_ONE = "b1946ac92492d2347c6235b4d2611184"
DIGEST_TWO = "591785b794601e212b260e25925636fd"

# WHY: The seven fields of data-model.md section 7.2, in report order. A field
#      added here without a decision would change every comparison.
EXPECTED_FIELDS = ("status", "version", "model", "name", "ip", "vc_role", "num_members")


def _device_row(**overrides: Any) -> dict[str, Any]:
    """Return one device index row with the fields a comparison reads.

    Why:
        Each test changes one field of a whole row. Building the row here keeps
        the difference under test on the single line that names it.

    Args:
        **overrides: The fields to replace.

    Returns:
        One device index row.
    """
    row: dict[str, Any] = {
        "name": "switch-01",
        "model": "EX4400-24T",
        "version": OLD_VERSION,
        "status": "connected",
        "ip": "10.10.10.11",
        "uptime": OLD_UPTIME,
        "vc_role": "master",
        "num_members": 2,
    }
    row.update(overrides)
    return row


def _capture(index: dict[str, Any], digests: dict[str, str] | None = None) -> dict[str, Any]:
    """Return one capture document around a device index.

    Why:
        The comparison reads two keys of a large document. A small builder
        keeps every test to the two keys that matter.

    Args:
        index: The device index of the capture.
        digests: The digest map, when the test needs one.

    Returns:
        One capture document.
    """
    capture: dict[str, Any] = {"device_index": index}
    if digests is not None:
        capture["digests"] = digests
    return capture


# ---------------------------------------------------------------------------
# The compared field list
# ---------------------------------------------------------------------------


def test_device_fields_match_the_data_model() -> None:
    """The compared field list holds the seven fields of the data model."""
    assert diff.DEVICE_FIELDS == EXPECTED_FIELDS


def test_uptime_is_not_a_compared_field() -> None:
    """The compared field list never holds ``uptime``."""
    assert diff.FIELD_UPTIME not in diff.DEVICE_FIELDS
    assert diff.FIELD_UPTIME in diff.EXCLUDED_DEVICE_FIELDS


def test_a_new_uptime_alone_leaves_the_device_unchanged() -> None:
    """A reboot changes the uptime, and the device stays ``unchanged``."""
    before = _capture({MASTER_MAC: _device_row(uptime=OLD_UPTIME)})
    after = _capture({MASTER_MAC: _device_row(uptime=NEW_UPTIME)})

    result = diff.compare_devices(before, after)

    assert len(result.deltas) == 1
    assert result.deltas[0].outcome == diff.OUTCOME_UNCHANGED
    assert result.deltas[0].changes == ()


def test_a_new_version_marks_the_device_changed() -> None:
    """A firmware upgrade reports the version before and the version after."""
    before = _capture({MASTER_MAC: _device_row(version=OLD_VERSION)})
    after = _capture({MASTER_MAC: _device_row(version=NEW_VERSION)})

    delta = diff.compare_devices(before, after).deltas[0]

    assert delta.outcome == diff.OUTCOME_CHANGED
    assert delta.changes == (diff.FieldChange(field="version", before=OLD_VERSION, after=NEW_VERSION),)
    assert delta.version_changed is True


def test_a_changed_device_lists_every_differing_field() -> None:
    """A device with two differing fields reports both, in field order."""
    before = _capture({MASTER_MAC: _device_row(status="connected", version=OLD_VERSION)})
    after = _capture({MASTER_MAC: _device_row(status="disconnected", version=NEW_VERSION)})

    delta = diff.compare_devices(before, after).deltas[0]

    assert [change.field for change in delta.changes] == ["status", "version"]


def test_an_uptime_change_never_reaches_the_change_list() -> None:
    """A device that changed its version reports no uptime row."""
    before = _capture({MASTER_MAC: _device_row(version=OLD_VERSION, uptime=OLD_UPTIME)})
    after = _capture({MASTER_MAC: _device_row(version=NEW_VERSION, uptime=NEW_UPTIME)})

    delta = diff.compare_devices(before, after).deltas[0]

    assert [change.field for change in delta.changes] == ["version"]


def test_an_absent_field_matches_an_empty_field() -> None:
    """An absent field and an empty field leave the device ``unchanged``."""
    before_row = _device_row()
    before_row.pop("ip")
    after_row = _device_row(ip=None)

    result = diff.compare_devices(_capture({MASTER_MAC: before_row}), _capture({MASTER_MAC: after_row}))

    assert result.deltas[0].outcome == diff.OUTCOME_UNCHANGED


def test_a_new_field_of_the_capture_never_changes_the_outcome() -> None:
    """A field outside the compared list leaves the device ``unchanged``."""
    before = _capture({MASTER_MAC: _device_row(last_seen=1)})
    after = _capture({MASTER_MAC: _device_row(last_seen=2)})

    assert diff.compare_devices(before, after).deltas[0].outcome == diff.OUTCOME_UNCHANGED


# ---------------------------------------------------------------------------
# The four outcomes
# ---------------------------------------------------------------------------


def test_a_device_of_the_post_check_capture_alone_is_added() -> None:
    """A device that only the post-check capture holds is ``added``."""
    result = diff.compare_devices(_capture({}), _capture({NEW_MAC: _device_row(name="new-switch")}))

    assert result.deltas[0].outcome == diff.OUTCOME_ADDED
    assert result.deltas[0].name == "new-switch"


def test_a_device_of_the_pre_check_capture_alone_is_removed() -> None:
    """A device that only the pre-check capture holds is ``removed``."""
    result = diff.compare_devices(_capture({MASTER_MAC: _device_row()}), _capture({}))

    assert result.deltas[0].outcome == diff.OUTCOME_REMOVED


def test_the_outcome_names_match_the_data_model() -> None:
    """The four device outcomes carry the names of the data model."""
    assert diff.DEVICE_OUTCOMES == ("unchanged", "changed", "added", "removed")


def test_the_comparison_sorts_the_devices_by_address() -> None:
    """The device rows arrive in address order, whichever capture holds them."""
    before = _capture({NEW_MAC: _device_row(), MASTER_MAC: _device_row()})
    after = _capture({MEMBER_MAC: _device_row()})

    result = diff.compare_devices(before, after)

    assert [delta.mac for delta in result.deltas] == [MASTER_MAC, MEMBER_MAC, NEW_MAC]


def test_a_row_of_the_wrong_type_never_stops_the_comparison() -> None:
    """A partial capture with a broken row still reports the good rows."""
    before = _capture({MASTER_MAC: _device_row(), MEMBER_MAC: "not a row"})
    after = _capture({MASTER_MAC: _device_row()})

    result = diff.compare_devices(before, after)

    assert [delta.mac for delta in result.deltas] == [MASTER_MAC]


def test_a_capture_without_a_device_index_reports_no_device() -> None:
    """A capture with no device index reports no device and raises nothing."""
    assert diff.compare_devices({}, {}).deltas == ()


# ---------------------------------------------------------------------------
# The digest short circuit
# ---------------------------------------------------------------------------


def test_a_matching_digest_skips_the_device_section() -> None:
    """Two captures with the same device digest compare no device at all."""
    before = _capture({MASTER_MAC: _device_row(version=OLD_VERSION)}, {"devices": DIGEST_ONE})
    after = _capture({MASTER_MAC: _device_row(version=NEW_VERSION)}, {"devices": DIGEST_ONE})

    result = diff.compare_devices(before, after)

    assert result.deltas == ()
    assert result.skipped_sections == (diff.SECTION_DEVICES,)


def test_a_differing_digest_compares_the_section() -> None:
    """Two captures with different device digests compare every device."""
    before = _capture({MASTER_MAC: _device_row(version=OLD_VERSION)}, {"devices": DIGEST_ONE})
    after = _capture({MASTER_MAC: _device_row(version=NEW_VERSION)}, {"devices": DIGEST_TWO})

    result = diff.compare_devices(before, after)

    assert result.skipped_sections == ()
    assert result.deltas[0].outcome == diff.OUTCOME_CHANGED


def test_an_absent_digest_is_never_a_match() -> None:
    """A capture with no digest map compares the section rather than skipping."""
    before = _capture({MASTER_MAC: _device_row(version=OLD_VERSION)})
    after = _capture({MASTER_MAC: _device_row(version=NEW_VERSION)})

    result = diff.compare_devices(before, after)

    assert result.skipped_sections == ()
    assert result.deltas[0].outcome == diff.OUTCOME_CHANGED


@pytest.mark.parametrize(
    ("before_digests", "after_digests"),
    [
        ({"devices": ""}, {"devices": ""}),
        ({}, {}),
        ({"devices": DIGEST_ONE}, {}),
        ({"devices": None}, {"devices": None}),
    ],
)
def test_an_empty_digest_is_never_a_match(before_digests: Any, after_digests: Any) -> None:
    """An empty, absent, or unreadable digest never counts as a match.

    Args:
        before_digests: The digest map of the pre-check capture.
        after_digests: The digest map of the post-check capture.
    """
    before = _capture({}, before_digests)
    after = _capture({}, after_digests)

    assert diff.digest_matches(before, after, diff.SECTION_DEVICES) is False


def test_the_section_digest_reader_survives_a_broken_digest_map() -> None:
    """A digest map of the wrong type reads as an empty digest."""
    assert diff.section_digest({"digests": "not a map"}, diff.SECTION_DEVICES) == ""


def test_matched_sections_reports_each_matching_section_in_order() -> None:
    """The section reader names every matching section, in the order given."""
    digests = {"devices": DIGEST_ONE, "extras": DIGEST_TWO, "whole": DIGEST_ONE}
    before = _capture({}, digests)
    after = _capture({}, {"devices": DIGEST_ONE, "extras": DIGEST_ONE, "whole": DIGEST_ONE})

    result = diff.matched_sections(before, after, ("devices", "extras", "whole"))

    assert result == ("devices", "whole")


# ---------------------------------------------------------------------------
# The counters and the dictionary form
# ---------------------------------------------------------------------------


def test_the_counters_read_the_outcome_of_each_record() -> None:
    """The counters report one number for each outcome and for the version."""
    deltas = (
        diff.DeviceDelta(mac=MASTER_MAC, outcome=diff.OUTCOME_UNCHANGED),
        diff.DeviceDelta(
            mac=MEMBER_MAC,
            outcome=diff.OUTCOME_CHANGED,
            changes=(diff.FieldChange(field="version", before=OLD_VERSION, after=NEW_VERSION),),
        ),
        diff.DeviceDelta(
            mac=NEW_MAC,
            outcome=diff.OUTCOME_CHANGED,
            changes=(diff.FieldChange(field="ip", before="10.0.0.1", after="10.0.0.2"),),
        ),
    )

    assert diff.count_outcome(deltas, diff.OUTCOME_UNCHANGED) == 1
    assert diff.count_outcome(deltas, diff.OUTCOME_CHANGED) == 2
    assert diff.count_version_changes(deltas) == 1


def test_the_device_result_carries_the_two_contract_keys() -> None:
    """The dictionary form names ``device_deltas`` and ``skipped_sections``."""
    result = diff.DeviceComparison(
        deltas=(diff.DeviceDelta(mac=MASTER_MAC, outcome=diff.OUTCOME_ADDED, name="switch-01"),),
        skipped_sections=(diff.SECTION_EXTRAS,),
    )

    body = result.to_dict()

    assert set(body) == {"device_deltas", "skipped_sections"}
    assert body["skipped_sections"] == ["extras"]
    assert body["device_deltas"][0] == {"mac": MASTER_MAC, "outcome": "added", "name": "switch-01", "changes": []}
