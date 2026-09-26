"""Unit tests of the page walk of the reconciliation read (issue #3438).

Why:
    The reconciliation reader passed the first page of the site statistics
    read to ``mistapi.get_all``. That helper adds a later page with no status
    check. A lost later page left a target with no fresh row. The reader then
    showed the stored version of the run record as the running version, and
    the service reported ``cloud_evidence_incomplete``.

    These tests build the real SDK answer objects of
    ``tests/support/sdk_pages.py``. The SDK builds each next link from the page
    headers, as it does for the live cloud. No test reaches the network.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from mistapi.__api_response import APIResponse

from src.upgrade_portal.api.run_controls import routes
from src.upgrade_portal.api.run_controls.routes import SiteStatsFirmwareEvidenceReader
from src.upgrade_portal.api.run_controls.services.reconciliation import StoppingRunReconciler
from src.upgrade_portal.persistence.actions import RUN_COLLECTION, ActionRepository, DurableActorScope
from tests.integration.upgrade_portal.run_controls import FakeDatabase
from tests.support.sdk_pages import HTML_TYPE, JSON_TYPE, PagedSession, build_sdk_answer

ORG_ID = "org-3438"  # The organization of the run.
SITE_ID = "site-3438"  # The site of the run.
RUN_ID = "run-3438"  # The stale stopping run.
OBSERVED_AT = "2026-09-26T07:00:00+00:00"  # The observation time that the caller gives the reader.
CLOCK = datetime(2026, 9, 26, 8, 0, tzinfo=UTC)  # Two days after the last run update, so the run is stale.
TARGET_VERSION = "24.2R2-S3.3"  # The version that each target asked for.
FRESH_MAC = "aabbcc003438"  # The target on page one.
UNREAD_MAC = "aabbcc003439"  # The target on page two.
PAGE_LIMIT = 1  # One row for each page keeps the test small. The SDK reads the page size from the headers.
PAGE_TOTAL = 2  # Two rows, so the cloud sends a second page.
STATS_PATH = f"/api/v1/sites/{SITE_ID}/stats/devices"  # The cloud path of the statistics read.
LINK_TWO = f"{STATS_PATH}?type=all&limit={PAGE_LIMIT}&page=2"  # The link that the SDK builds for page two.


def _url(page: int) -> str:
    """Return the full address of one page of the statistics read.

    Args:
        page: The page number.

    Returns:
        The address that the SDK reads the next link from.
    """
    return f"https://api.mist.com{STATS_PATH}?type=all&limit={PAGE_LIMIT}&page={page}"


def _stats_row(mac: str) -> dict[str, Any]:
    """Return one statistics row that proves a firmware success.

    Args:
        mac: The address of the device, with no separator.

    Returns:
        The row that the cloud sends for the device.
    """
    colon_mac = ":".join(mac[index : index + 2] for index in range(0, len(mac), 2))  # The cloud spells it with colons.
    return {
        "mac": colon_mac,
        "version": TARGET_VERSION,
        "uptime": 120,
        "last_seen": 1790000000,
        "fwupdate": {"status": "success"},
    }


def _page(mac: str, page: int) -> APIResponse:
    """Build one whole page that holds the row of one device.

    Args:
        mac: The address of the device.
        page: The page number.

    Returns:
        The SDK answer for the page.
    """
    headers = {**JSON_TYPE, "X-Page-Total": str(PAGE_TOTAL), "X-Page-Limit": str(PAGE_LIMIT), "X-Page-Page": str(page)}
    return build_sdk_answer(200, json.dumps([_stats_row(mac)]).encode("utf-8"), headers, _url(page))


def _html_error(page: int) -> APIResponse:
    """Build the HTML error page that a gateway sends for a failed call.

    Args:
        page: The page number.

    Returns:
        The SDK answer. The SDK cannot parse the body, so it holds no data.
    """
    return build_sdk_answer(503, b"<html><body>Service Unavailable</body></html>", HTML_TYPE, _url(page))


def _json_error(page: int) -> APIResponse:
    """Build a JSON error page with an error status.

    Args:
        page: The page number.

    Returns:
        The SDK answer with the error body.
    """
    return build_sdk_answer(500, b'{"detail": "internal error"}', JSON_TYPE, _url(page))


def _no_status(page: int) -> APIResponse:
    """Build the answer that the SDK builds when the connection fails.

    Args:
        page: The page number.

    Returns:
        The SDK answer with no status and no data.
    """
    return APIResponse(response=None, url=_url(page))


def _no_list(page: int) -> APIResponse:
    """Build a page with a good status and a body that holds no list.

    Args:
        page: The page number.

    Returns:
        The SDK answer with a body that the reader cannot use.
    """
    return build_sdk_answer(200, b'{"detail": "no rows"}', JSON_TYPE, _url(page))


LOST_PAGES = [  # Each way that the cloud can lose page two.
    pytest.param(_html_error, id="html-error"),
    pytest.param(_json_error, id="json-error"),
    pytest.param(_no_status, id="no-status"),
    pytest.param(_no_list, id="no-list"),
]
FAILED_FIRST_PAGES = [  # Each way that the cloud can fail page one.
    pytest.param(_html_error, id="html-error"),
    pytest.param(_no_status, id="no-status"),
    pytest.param(_no_list, id="no-list"),
]


def _target(mac: str) -> dict[str, Any]:
    """Return one stored target of the stopping run.

    Args:
        mac: The address of the device.

    Returns:
        The target as the run store holds it. The stored version equals the
        target version, so a stored fallback would look like a success.
    """
    return {
        "mac": mac,
        "device_type": "switch",
        "version_target": TARGET_VERSION,
        "version_after": TARGET_VERSION,
        "stop_result": "cancel_accepted",
        "cloud_task_id": f"task-{mac}",
        "driver_state": "stopped",
    }


def _run_record() -> dict[str, Any]:
    """Return the stale stopping run with one target on each page.

    Returns:
        The run as the run store holds it.
    """
    return {
        "_key": RUN_ID,
        "run_id": RUN_ID,
        "site_id": SITE_ID,
        "org_id": ORG_ID,
        "state": "stopping",
        "updated_at": "2026-09-24T07:00:00+00:00",
        "targets": [_target(FRESH_MAC), _target(UNREAD_MAC)],
    }


def _stored_fields(mac: str) -> dict[str, Any]:
    """Return the fields that the stored target gives each evidence row.

    Args:
        mac: The address of the device.

    Returns:
        The stored fallback fields.
    """
    return {
        "target_id": mac,
        "stored_stop_result": "cancel_accepted",
        "task_id": f"task-{mac}",
        "driver_state": "stopped",
        "version_target": TARGET_VERSION,
        "has_conflict": False,
    }


def _fresh_evidence(mac: str) -> dict[str, Any]:
    """Return the evidence row of a target with a fresh statistics row.

    Args:
        mac: The address of the device.

    Returns:
        The evidence row that proves the firmware success.
    """
    return {
        **_stored_fields(mac),
        "running_version": TARGET_VERSION,
        "fwupdate_status": "success",
        "task_state": "final",
        "write_state": "not_writing",
        "sources": ["device"],
        "observed_at": OBSERVED_AT,
        "firmware_success": True,
        "is_complete": True,
    }


def _unread_evidence(mac: str) -> dict[str, Any]:
    """Return the evidence row of a target that the reader did not read.

    Args:
        mac: The address of the device.

    Returns:
        The evidence row of the data model of issue #3438.
    """
    return {
        **_stored_fields(mac),
        "running_version": "",
        "fwupdate_status": "",
        "task_state": "unavailable",
        "write_state": "unavailable",
        "sources": ["stored"],
        "observed_at": None,
        "firmware_success": False,
        "is_complete": False,
    }


class StatisticsCall:
    """Answer the first page of the statistics read and record each call."""

    def __init__(self, first: APIResponse) -> None:
        """Keep the answer of page one.

        Args:
            first: The SDK answer of page one.
        """
        self.first = first  # The answer of each call.
        self.site_ids: list[str] = []  # The site of each call, in call order.

    def __call__(self, session: Any, site_id: str, **parameters: Any) -> APIResponse:
        """Answer page one and record the site.

        Args:
            session: The cloud session. The answer does not depend on it.
            site_id: The site of the read.
            **parameters: The call parameters. The answer does not depend on them.

        Returns:
            The answer of page one.
        """
        del session, parameters  # One fixed answer for each call.
        self.site_ids.append(site_id)  # Record the site of the call.
        return self.first


def _read_evidence(
    monkeypatch: pytest.MonkeyPatch, first: APIResponse, later: list[APIResponse]
) -> tuple[list[dict[str, Any]], PagedSession]:
    """Read the evidence of the stale run through the real reader.

    Args:
        monkeypatch: The pytest patch fixture.
        first: The SDK answer of page one.
        later: The SDK answers of the later pages.

    Returns:
        The evidence rows and the session that answered the later pages.
    """
    session = PagedSession(later)  # The later pages come through the SDK page link.
    call = StatisticsCall(first)  # The first page comes through the SDK call.
    monkeypatch.setattr(routes.mistapi.api.v1.sites.stats, "listSiteDevicesStats", call)  # No network.
    rows = SiteStatsFirmwareEvidenceReader(session).read(_run_record(), OBSERVED_AT)  # The real reader.
    assert call.site_ids == [SITE_ID]  # One call for page one, at the run site.
    return [dict(row) for row in rows], session


@pytest.mark.parametrize("lost_page", LOST_PAGES)
def test_a_lost_page_changes_only_the_evidence_of_the_unread_target(
    monkeypatch: pytest.MonkeyPatch, lost_page: Callable[[int], APIResponse]
) -> None:
    """FR-009 to FR-012, SC-004: compare a whole walk with a walk that lost page two."""
    whole, whole_session = _read_evidence(monkeypatch, _page(FRESH_MAC, 1), [_page(UNREAD_MAC, 2)])  # Both pages.
    lost, lost_session = _read_evidence(monkeypatch, _page(FRESH_MAC, 1), [lost_page(2)])  # Page two is lost.
    assert whole == [_fresh_evidence(FRESH_MAC), _fresh_evidence(UNREAD_MAC)]  # A whole walk reads both pages.
    assert whole_session.links == [LINK_TWO] == lost_session.links  # One call for each page.
    assert lost[0] == whole[0]  # The target of page one keeps its fresh evidence.
    assert lost[1] == _unread_evidence(UNREAD_MAC)  # The target of the lost page holds unavailable evidence.
    assert lost[1]["running_version"] != _target(UNREAD_MAC)["version_after"]  # No stored version shows as running.


@pytest.mark.parametrize("failed_page", FAILED_FIRST_PAGES)
def test_a_failed_first_page_marks_every_target_unavailable(
    monkeypatch: pytest.MonkeyPatch, failed_page: Callable[[int], APIResponse]
) -> None:
    """FR-009, FR-010: a fault of page one marks each target as not read."""
    rows, session = _read_evidence(monkeypatch, failed_page(1), [])  # Page one failed.
    assert rows == [_unread_evidence(FRESH_MAC), _unread_evidence(UNREAD_MAC)]  # No target holds fresh evidence.
    assert session.links == []  # The walk asks for no later page.


def test_the_reader_logs_a_lost_page_once_with_no_device_address(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """FR-003: one warning names the site and the unread count, and it holds no address."""
    caplog.set_level(logging.INFO, logger=routes.logger.name)  # Capture the reader log.
    _read_evidence(monkeypatch, _page(FRESH_MAC, 1), [_html_error(2)])  # Page two is lost.
    warnings = [
        record.getMessage()
        for record in caplog.records
        if record.name == routes.logger.name and record.levelno == logging.WARNING
    ]
    assert len(warnings) == 1  # One warning for one lost read.
    assert SITE_ID in warnings[0]  # The warning names the site.
    assert "1 target(s)" in warnings[0]  # The warning names the unread count.
    assert all(mac not in warnings[0] for mac in (FRESH_MAC, UNREAD_MAC, "aa:bb:cc"))  # No address in the log.


class _OpenGuard:
    """Permit the reconciliation of the test run."""

    def refusal(self, organization_id: str, site_id: str) -> None:
        """Return no refusal for the test organization and site.

        Args:
            organization_id: The organization that the service checks.
            site_id: The site that the service checks.
        """
        assert (organization_id, site_id) == (ORG_ID, SITE_ID)  # The service checks the run scope again.


def _reconcile(monkeypatch: pytest.MonkeyPatch, later: list[APIResponse], request_key: str) -> tuple[str, str]:
    """Reconcile the stale stopping run through the real service and the real reader.

    Args:
        monkeypatch: The pytest patch fixture.
        later: The SDK answers of the later pages.
        request_key: The idempotency key of the request.

    Returns:
        The result reason and the stored run state after the reconciliation.
    """
    database = FakeDatabase()  # One isolated action and run store.
    database.create_collection(RUN_COLLECTION)  # The run collection.
    repository = ActionRepository(database)  # The production repository.
    repository.bootstrap()  # Create the action collection before the reconciliation.
    database.collection(RUN_COLLECTION).insert(_run_record())  # Store the run with a revision.
    call = StatisticsCall(_page(FRESH_MAC, 1))  # Page one holds the first target.
    monkeypatch.setattr(routes.mistapi.api.v1.sites.stats, "listSiteDevicesStats", call)  # No network.
    service = StoppingRunReconciler(
        repository,
        lambda run_id: database.collection(RUN_COLLECTION).get(run_id),
        _OpenGuard(),
        SiteStatsFirmwareEvidenceReader(PagedSession(later)).read,
        lambda: CLOCK,
    )
    action = service.reconcile(
        actor=DurableActorScope.build("email", "operator@example.invalid"),
        idempotency_key=request_key,
        confirmation=f"RECONCILE {RUN_ID}",
        run_id=RUN_ID,
        organization_id=ORG_ID,
        site_id=SITE_ID,
    )
    stored = database.collection(RUN_COLLECTION).get(RUN_ID)  # The run after the reconciliation.
    return action.ledger.items[0].completion.reason, str(stored["state"])


def test_only_a_lost_page_keeps_a_stale_stopping_run_unreconciled(monkeypatch: pytest.MonkeyPatch) -> None:
    """US4 scenarios 3 and 4: a whole walk stops the run, and a lost page reports unavailable evidence."""
    whole = _reconcile(monkeypatch, [_page(UNREAD_MAC, 2)], "issue-3438-reconcile-whole")  # Both pages arrive.
    lost = _reconcile(monkeypatch, [_html_error(2)], "issue-3438-reconcile-lost")  # Page two is lost.
    assert whole == ("stopping_run_reconciled", "stopped")  # A whole walk proves both targets.
    assert lost == ("cloud_evidence_unavailable", "stopping")  # The run keeps its state, and the reason names why.
