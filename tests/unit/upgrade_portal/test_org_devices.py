"""Unit tests for the device rows and the version reads of a multi-site operation.

Why:
    Issue #3249. The multi-site progress page showed one row for each child
    job, with counts only. These tests prove the rules that build one row for
    each device and the rules that bound the running version reads.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import SimpleNamespace
from typing import Any

import pytest

from src.firmware.running_version import RunningFirmwareVersionResolver
from src.upgrade_portal.upgrade.org_devices import LISTED_FAILURE, OrgChildDevices, OrgDeviceRows
from src.upgrade_portal.upgrade.org_versions import OrgVersionRefresh

SITE_ONE = "11111111-1111-1111-1111-111111111111"
SITE_TWO = "22222222-2222-2222-2222-222222222222"
AP_ONE = "001122334455"
AP_TWO = "001122334466"
SWITCH = "001122334477"
SWITCH_TARGET = "23.4R1.9"
SWITCH_OLD = "23.4R1.8"


def target(mac: str, site_id: str, device_type: str = "ap", version: str = "0.15.1") -> dict[str, str]:
    """Build one stored target record, in the shape that the aggregate service stores."""
    return {
        "mac": mac,
        "name": f"{device_type}-{mac[-2:]}",
        "device_type": device_type,
        "model": "AP45" if device_type == "ap" else "EX4400",
        "version_before": "0.14.1" if device_type == "ap" else SWITCH_OLD,
        "version_target": version,
        "site_id": site_id,
    }


def child(
    child_id: str,
    status: str,
    targets: list[dict[str, str]],
    status_data: Mapping[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Build one aggregate child. An access point child names no site, as the service builds it."""
    family = targets[0]["device_type"] if targets else "ap"
    site_id = None if family == "ap" else targets[0]["site_id"]
    return {
        "child_id": child_id,
        "device_family": family,
        "site_id": site_id,
        "site_name": "One, Two" if site_id is None else "One",
        "status": status,
        "target_ids": [row["mac"] for row in targets],
        "targets": targets,
        "status_data": dict(status_data or {}),
        "error": error,
    }


def switch_child(status: str, listed: str | None = None) -> dict[str, Any]:
    """Build one switch child at site one, with the switch in one cloud list or in no list."""
    status_data = {"targets": {listed: [SWITCH]}} if listed else {}
    return child("child-switch", status, [target(SWITCH, SITE_ONE, "switch", SWITCH_TARGET)], status_data)


class SiteReaderStandIn:
    """Answer each running version read from a fixed map, and record each site."""

    def __init__(self, answers: Mapping[str, Mapping[str, str] | Exception]) -> None:
        """Keep the fixed answer of each site."""
        self.answers = answers
        self.calls: list[str] = []

    def __call__(self, cloud_session: Any, site_id: str) -> Mapping[str, str]:
        """Record the site, then return its answer or raise its fault."""
        del cloud_session  # The stand-in makes no cloud call.
        self.calls.append(site_id)
        answer = self.answers.get(site_id, {})
        if isinstance(answer, Exception):
            raise answer
        return answer


def test_the_failed_list_wins_over_the_upgraded_list() -> None:
    """A device in two cloud lists shows the more serious state."""
    status_data = {"targets": {"upgraded": [AP_ONE], "failed": [AP_ONE]}}
    devices = OrgChildDevices(child("child-ap", "running", [target(AP_ONE, SITE_ONE)], status_data))
    assert devices.state_of(AP_ONE) == "failed"
    assert devices.failure_of(AP_ONE) == LISTED_FAILURE


def test_nested_site_entries_the_root_reboot_list_and_separators() -> None:
    """The state reads every list shape of the cloud answer and every MAC spelling."""
    status_data = {
        "reboot_in_progress": [SWITCH],
        "site_upgrades": [
            {"site_id": SITE_ONE, "upgrade": {"targets": {"upgraded": ["00:11:22:33:44:55"]}}},
            {"site_id": SITE_TWO, "targets": {"downloading": ["00-11-22-33-44-66"]}},
        ],
    }
    targets = [target(AP_ONE, SITE_ONE), target(AP_TWO, SITE_TWO), target(SWITCH, SITE_ONE)]
    devices = OrgChildDevices(child("child-ap", "running", targets, status_data))
    assert [devices.state_of(mac) for mac in (AP_ONE, AP_TWO, SWITCH)] == ["upgraded", "downloading", "rebooting"]


def test_an_unlisted_device_shows_pending_and_then_the_child_state() -> None:
    """A device in no list waits while its child runs, and then shows the child state."""
    running = OrgChildDevices(child("child-ap", "running", [target(AP_ONE, SITE_ONE)]))
    cancelled = OrgChildDevices(child("child-ap", "cancelled", [target(AP_ONE, SITE_ONE)]))
    assert running.state_of(AP_ONE) == "pending"
    assert cancelled.state_of(AP_ONE) == "cancelled"


def test_the_failure_reason_follows_the_child_error() -> None:
    """A failed device shows the child error, and an upgraded device shows no reason."""
    listed = child(
        "child-switch",
        "failed",
        [target(SWITCH, SITE_ONE, "switch", SWITCH_TARGET)],
        {"targets": {"failed": [SWITCH]}},
        "The switch child failed.",
    )
    refused = child("child-gateway", "rejected", [target(AP_TWO, SITE_ONE, "gateway")], None, "The cloud refused it.")
    upgraded = child("child-ap", "failed", [target(AP_ONE, SITE_ONE)], {"targets": {"upgraded": [AP_ONE]}}, "A fault.")
    assert OrgChildDevices(listed).failure_of(SWITCH) == "The switch child failed."
    assert OrgChildDevices(refused).failure_of(AP_TWO) == "The cloud refused it."
    assert OrgChildDevices(upgraded).failure_of(AP_ONE) == ""


def test_an_unlisted_device_of_a_failed_child_keeps_no_false_list_reason() -> None:
    """The listed-failure words never name a device that the cloud did not list."""
    unlisted = OrgChildDevices(child("child-ap", "failed", [target(AP_ONE, SITE_ONE)]))
    assert unlisted.state_of(AP_ONE) == "failed"
    assert unlisted.failure_of(AP_ONE) == ""


def test_fallback_rows_read_the_version_from_the_stored_body() -> None:
    """A record from an earlier release holds MAC addresses only, and the row still shows them."""
    legacy = child("child-ap", "running", [])
    legacy["target_ids"] = [AP_ONE]
    legacy["body"] = {"versions": [{"firmware_type": "ap", "version": "0.15.1"}]}
    rows = OrgDeviceRows({"children": [legacy]}).rows()
    assert rows == [
        {
            "child_id": "child-ap",
            "site_id": "",
            "site_name": "One, Two",
            "name": "",
            "mac": AP_ONE,
            "device_type": "ap",
            "state": "pending",
            "version_before": "",
            "version_target": "0.15.1",
            "version_after": "",
            "version_outcome": "version_pending",
            "failure_reason": "",
        }
    ]


def test_rows_show_the_stored_reading_and_the_version_check() -> None:
    """Each row compares the stored running version with the requested version."""
    record = {
        "site_names": {SITE_ONE: "One", SITE_TWO: "Two"},
        "device_versions": {
            AP_ONE: {"version": "0.15.1", "read_at": "2026-09-24T01:00:00+00:00", "reads": 1},
            AP_TWO: {"version": "0.14.1", "read_at": "2026-09-24T01:00:00+00:00", "reads": 1},
        },
        "children": [
            child(
                "child-ap",
                "completed",
                [target(AP_ONE, SITE_ONE), target(AP_TWO, SITE_TWO)],
                {"targets": {"upgraded": [AP_ONE, AP_TWO]}},
            ),
            switch_child("running"),
        ],
    }
    rows = {row["mac"]: row for row in OrgDeviceRows(record).rows()}
    assert (rows[AP_ONE]["version_after"], rows[AP_ONE]["version_outcome"]) == ("0.15.1", "version_match")
    assert (rows[AP_TWO]["version_after"], rows[AP_TWO]["version_outcome"]) == ("0.14.1", "version_mismatch")
    assert (rows[SWITCH]["version_after"], rows[SWITCH]["version_outcome"]) == ("", "version_pending")
    assert [rows[mac]["site_name"] for mac in (AP_ONE, AP_TWO, SWITCH)] == ["One", "Two", "One"]


def test_a_site_with_no_stored_name_shows_its_identifier() -> None:
    """The access point child names two sites, so one device must not show that joined name."""
    record = {"children": [child("child-ap", "running", [target(AP_TWO, SITE_TWO)])]}
    assert OrgDeviceRows(record).rows()[0]["site_name"] == SITE_TWO


def test_the_refresh_reads_each_site_once_for_every_child() -> None:
    """Two children at one site cause one read of that site."""
    record = {
        "children": [
            child(
                "child-ap",
                "completed",
                [target(AP_ONE, SITE_ONE), target(AP_TWO, SITE_TWO)],
                {"targets": {"upgraded": [AP_ONE, AP_TWO]}},
            ),
            switch_child("completed", "upgraded"),
        ]
    }
    reader = SiteReaderStandIn({SITE_ONE: {AP_ONE: "0.15.1", SWITCH: SWITCH_TARGET}, SITE_TWO: {AP_TWO: "0.15.1"}})
    result = OrgVersionRefresh(reader).collect(object(), record)
    assert sorted(reader.calls) == sorted([SITE_ONE, SITE_TWO])
    assert result.readings == {AP_ONE: "0.15.1", AP_TWO: "0.15.1", SWITCH: SWITCH_TARGET}
    assert result.final_child_ids == ("child-ap", "child-switch")
    assert result.sites_read == 2


def test_the_refresh_reads_no_site_after_every_child_is_final() -> None:
    """SC-002: a finished operation causes no running version read at all."""
    record = {
        "versions_final": ["child-switch"],
        "device_versions": {SWITCH: {"version": SWITCH_TARGET, "reads": 1}},
        "children": [switch_child("completed", "upgraded")],
    }
    reader = SiteReaderStandIn({SITE_ONE: {SWITCH: SWITCH_TARGET}})
    result = OrgVersionRefresh(reader).collect(object(), record)
    assert reader.calls == []
    assert (result.readings, result.final_child_ids, result.changes) == ({}, (), False)


def test_the_refresh_skips_a_rejected_child_and_an_unlisted_running_device() -> None:
    """A refused child sent no firmware, and an unlisted device has not settled."""
    refused = child("child-gateway", "rejected", [target(AP_TWO, SITE_TWO, "gateway", SWITCH_TARGET)], None, "No.")
    record = {"children": [refused, switch_child("running")]}
    reader = SiteReaderStandIn({})
    result = OrgVersionRefresh(reader).collect(object(), record)
    assert reader.calls == []
    assert result.final_child_ids == ("child-gateway",)


@pytest.mark.parametrize(
    ("entry", "expected_calls"),
    [
        (None, 1),
        ({"version": SWITCH_OLD, "reads": 1}, 1),
        ({"version": SWITCH_OLD, "reads": 2}, 0),
        ({"version": SWITCH_TARGET, "reads": 1}, 0),
    ],
)
def test_the_reads_of_a_running_upgraded_device_are_bounded(
    entry: dict[str, object] | None, expected_calls: int
) -> None:
    """A running child reads an upgraded device until it matches, and at most two times."""
    record: dict[str, Any] = {"children": [switch_child("running", "upgraded")]}
    if entry is not None:
        record["device_versions"] = {SWITCH: entry}
    reader = SiteReaderStandIn({SITE_ONE: {SWITCH: SWITCH_TARGET}})
    OrgVersionRefresh(reader).collect(object(), record)
    assert len(reader.calls) == expected_calls


def test_a_running_failed_device_is_not_read_again() -> None:
    """A failed device keeps its first reading while its child runs."""
    record = {
        "device_versions": {SWITCH: {"version": SWITCH_OLD, "reads": 1}},
        "children": [switch_child("running", "failed")],
    }
    reader = SiteReaderStandIn({SITE_ONE: {SWITCH: SWITCH_OLD}})
    OrgVersionRefresh(reader).collect(object(), record)
    assert reader.calls == []


def test_a_final_child_reads_once_more_and_is_marked_final() -> None:
    """The final read replaces a mismatch that the device reported while it settled."""
    record = {
        "device_versions": {SWITCH: {"version": SWITCH_OLD, "reads": 2}},
        "children": [switch_child("completed", "upgraded")],
    }
    reader = SiteReaderStandIn({SITE_ONE: {SWITCH: SWITCH_TARGET}})
    result = OrgVersionRefresh(reader).collect(object(), record)
    assert reader.calls == [SITE_ONE]
    assert result.readings == {SWITCH: SWITCH_TARGET}
    assert result.final_child_ids == ("child-switch",)


@pytest.mark.parametrize("answer", [RuntimeError("The cloud read failed."), {}])
def test_a_failed_or_empty_read_stores_nothing_and_keeps_the_child_open(
    answer: Mapping[str, str] | Exception,
) -> None:
    """A read that proves nothing must not close the child, so a later refresh reads again."""
    reader = SiteReaderStandIn({SITE_ONE: answer})
    result = OrgVersionRefresh(reader).collect(object(), {"children": [switch_child("completed", "upgraded")]})
    assert reader.calls == [SITE_ONE]
    assert (result.readings, result.final_child_ids) == ({}, ())


def test_a_device_that_the_site_does_not_report_gets_an_empty_reading() -> None:
    """A site answer without the device proves that the device reports no version."""
    reader = SiteReaderStandIn({SITE_ONE: {AP_ONE: "0.15.1"}})
    result = OrgVersionRefresh(reader).collect(object(), {"children": [switch_child("completed", "upgraded")]})
    assert result.readings == {SWITCH: ""}
    assert result.final_child_ids == ("child-switch",)


def test_the_reader_keys_are_normalized() -> None:
    """The stats answer can spell a MAC with separators or name a device identifier."""
    answer = {"00:11:22:33:44:77": SWITCH_TARGET, "00000000-0000-0000-1000-001122334477": SWITCH_TARGET}
    reader = SiteReaderStandIn({SITE_ONE: answer})
    result = OrgVersionRefresh(reader).collect(object(), {"children": [switch_child("completed", "upgraded")]})
    assert result.readings == {SWITCH: SWITCH_TARGET}


def test_a_device_without_a_site_is_not_read() -> None:
    """A record from an earlier release names no site for an access point, so no read can find it."""
    legacy = child("child-ap", "completed", [])
    legacy["target_ids"] = [AP_ONE]
    reader = SiteReaderStandIn({})
    result = OrgVersionRefresh(reader).collect(object(), {"children": [legacy]})
    assert reader.calls == []
    assert result.final_child_ids == ("child-ap",)


def test_the_default_reader_uses_the_running_version_resolver(monkeypatch: pytest.MonkeyPatch) -> None:
    """Issue #2006: the version after comes from the running version, never the configured one."""
    seen: list[str] = []

    def fetch(resolver: RunningFirmwareVersionResolver, site_id: str) -> dict[str, str]:
        del resolver  # The stand-in makes no cloud call.
        seen.append(site_id)
        return {SWITCH: SWITCH_TARGET}

    monkeypatch.setattr(RunningFirmwareVersionResolver, "fetch_site_running_versions", fetch)
    assert OrgVersionRefresh.running_versions(object(), SITE_ONE) == {SWITCH: SWITCH_TARGET}
    assert seen == [SITE_ONE]


@pytest.mark.parametrize("status_code", [404, 503])
def test_a_refused_stats_answer_stores_nothing_and_keeps_the_child_open(
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
) -> None:
    """A 4xx or 5xx stats answer proves nothing, so the next refresh reads the site again."""
    import mistapi.api.v1.sites.stats as site_stats  # The endpoint that the production reader calls.

    seen: list[str] = []  # The sites that the production reader read.

    def refused(apisession: object, site_id: str, **parameters: object) -> SimpleNamespace:
        """Refuse the stats read with the status of this case."""
        del apisession, parameters  # The stand-in makes no cloud call.
        seen.append(site_id)  # Count each stats read.
        return SimpleNamespace(status_code=status_code, data={"detail": "The cloud refused the read."})

    monkeypatch.setattr(site_stats, "listSiteDevicesStats", refused)  # Keep the test offline.
    refresh = OrgVersionRefresh(OrgVersionRefresh.running_versions)  # The reader that the routes use.
    result = refresh.collect(object(), {"children": [switch_child("completed", "upgraded")]})  # One final child.
    assert seen == [SITE_ONE]  # The refresh read the one site one time.
    assert (result.readings, result.final_child_ids, result.sites_read) == ({}, (), 1)  # The child stays open.
