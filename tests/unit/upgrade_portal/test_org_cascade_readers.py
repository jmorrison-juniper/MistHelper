"""Unit tests for the cloud reads of the multi-site phase watch.

Why:
    Issue #3245. Each phase reads one device family, a read of many pages
    stretches the wait between two rounds, and the anchor read never blocks
    the upgrade. These tests replace the cloud call with a recorder. No test
    opens a socket.
"""

from __future__ import annotations

from typing import Any

import mistapi
import pytest

from src.upgrade_portal.upgrade.org_cascade import readers
from src.upgrade_portal.upgrade.org_cascade.readers import (
    ANCHOR_GAP_NOTE,
    BudgetSleep,
    OrgSettleAnchors,
    OrgStatisticsReader,
)
from tests.support.org_cascade import SITE_IDS, OrgRecordBuilder
from tests.support.rehearsal import ORG_ID, StandInResponse, cascade_fleet

FLEET = cascade_fleet(1.0)  # Two gateways, two switches, and two access points.


class StatisticsRecorder:
    """Answer each statistics read with fixed rows, and record the scope of each read."""

    def __init__(self, rows: list[dict[str, Any]], broken_family: str | None = None) -> None:
        """Keep the rows of each answer and the family whose read must fail."""
        self.rows = rows  # The rows of each answer.
        self.broken_family = broken_family  # The read of this family raises.
        self.scopes: list[tuple[str, Any, Any]] = []  # The family, the site, and the page size of each read.

    def read(self, _session: Any, _org_id: str, **keywords: Any) -> StandInResponse:
        """Record one read, and return the rows of the family that the caller named."""
        family = keywords.get("type")  # The device family that the reader sent.
        self.scopes.append((family, keywords.get("site_id"), keywords.get("limit")))  # Keep the scope.
        if family == self.broken_family:  # The test asks this read to fail.
            raise ConnectionError("the cloud did not answer")  # The broken family proves the gap path.
        rows = [row for row in self.rows if row["type"] == family]  # The cloud answers one family.
        return StandInResponse(
            {"results": rows, "total": len(rows), "next": None}
        )  # The stand-in cloud returns the page.


def attach(monkeypatch: pytest.MonkeyPatch, recorder: StatisticsRecorder, page_limit: int = 1000) -> None:
    """Replace the two cloud calls of one statistics read."""
    monkeypatch.setattr(
        mistapi.api.v1.orgs.stats, "listOrgDevicesStats", recorder.read
    )  # The test replaces the cloud read.
    monkeypatch.setattr(
        mistapi, "get_all", lambda mist_session=None, response=None: list(response.data["results"])
    )  # The test returns the page rows.
    monkeypatch.setattr(readers, "resolve_page_limit", lambda: page_limit)  # The test fixes the page size.


def row(mac: str, family: str, uptime: int | None = 100, last_seen: int = 1_900_000_000) -> dict[str, Any]:
    """Return one statistics row in the shape of the cloud answer."""
    return {
        "mac": mac,
        "type": family,
        "version": "1.0",
        "uptime": uptime,
        "last_seen": last_seen,
    }  # The row matches the cloud page.


def test_a_read_names_one_family_and_one_site(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-015. A phase at one site reads that site, and a phase at two sites reads the organization."""
    recorder = StatisticsRecorder([])  # The recorder stores each read.
    attach(monkeypatch, recorder)  # The test installs the stand-in cloud.
    OrgStatisticsReader(None, ORG_ID, "switch", [SITE_IDS[0]]).read()  # One site must narrow the read.
    OrgStatisticsReader(None, ORG_ID, "ap", list(SITE_IDS)).read()  # Two sites must read the organization.
    assert recorder.scopes == [("switch", SITE_IDS[0], 1000), ("ap", None, 1000)]  # The scopes prove the site rule.


def test_the_page_count_follows_the_last_read(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-016. Five devices in pages of two cost three pages."""
    rows = [row(f"bb00000000{index:02d}", "switch") for index in range(1, 6)]  # Five switch rows create three pages.
    attach(monkeypatch, StatisticsRecorder(rows), page_limit=2)  # The small page size proves many pages.
    reader = OrgStatisticsReader(None, ORG_ID, "switch", list(SITE_IDS))  # The reader watches the switch family.
    assert reader.page_count == 1  # The first round assumes one page.
    assert len(reader.read().readings) == 5  # The read returns every switch row.
    assert reader.page_count == 3  # The next wait sees three pages.


class FixedPages:
    """Report a fixed page count."""

    def __init__(self, pages: int) -> None:
        """Keep the page count."""
        self.page_count = pages  # The count that the budget reads.


@pytest.mark.parametrize(("pages", "expected"), [(1, 20.0), (3, 40.0), (5, 60.0)])
def test_the_budget_sleep_stretches_the_wait_by_the_page_count(pages: int, expected: float) -> None:
    """FR-016. One round costs one event read and one call for each page, and the budget is two calls."""
    waits: list[float] = []  # The list records each wait.
    BudgetSleep(FixedPages(pages), waits.append)(20)  # A fake reader stands in for the statistics reader.
    assert waits == [expected]  # The wait proves the budget rule.


def test_the_anchor_read_stores_the_uptime_and_the_last_report(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-001. The anchors use the single-site field names, and one read serves each family."""
    rows = [
        row(script.mac, script.device_type, uptime=500 + index) for index, script in enumerate(FLEET.scripts)
    ]  # The rows give each device an anchor.
    recorder = StatisticsRecorder(rows)  # The recorder stores the anchor reads.
    attach(monkeypatch, recorder)  # The test installs the anchor stand-in.
    read = OrgSettleAnchors.read(None, OrgRecordBuilder.build(FLEET))  # The read creates the anchor map.
    assert read.note == ""  # A complete read has no gap note.
    assert read.anchors["bb0000000001"] == {
        "uptime_before": 502,
        "last_seen_before": 1_900_000_000.0,
    }  # The switch anchor stores both fields.
    assert sorted(scope[0] for scope in recorder.scopes) == [
        "ap",
        "gateway",
        "switch",
    ]  # The scopes prove each family read.


def test_a_device_with_no_reading_gets_a_null_anchor_and_a_note(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-002. The cloud does not report one switch, so the page names the gap."""
    rows = [
        row(script.mac, script.device_type) for script in FLEET.scripts if script.mac != "bb0000000002"
    ]  # The rows omit one switch reading.
    attach(monkeypatch, StatisticsRecorder(rows))  # The test installs the incomplete page.
    read = OrgSettleAnchors.read(None, OrgRecordBuilder.build(FLEET))  # The read records the missing switch.
    assert read.anchors["bb0000000002"] == {
        "uptime_before": None,
        "last_seen_before": None,
    }  # The missing switch gets a null anchor.
    assert read.note == ANCHOR_GAP_NOTE.format(count=1)  # The note states the gap count.


def test_a_failed_anchor_read_never_blocks_the_upgrade(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-002. The access point read fails, so each access point holds a null anchor, and nothing raises."""
    rows = [row(script.mac, script.device_type) for script in FLEET.scripts]  # The rows cover every device.
    attach(monkeypatch, StatisticsRecorder(rows, broken_family="ap"))  # The stand-in cloud fails one family.
    read = OrgSettleAnchors.read(None, OrgRecordBuilder.build(FLEET))  # The read must not raise.
    assert read.anchors["cc0000000001"]["uptime_before"] is None  # The failed family gets a null anchor.
    assert read.anchors["aa0000000001"]["uptime_before"] == 100  # The good family keeps its anchor.
    assert read.note == ANCHOR_GAP_NOTE.format(count=2)  # The note counts the failed family.
