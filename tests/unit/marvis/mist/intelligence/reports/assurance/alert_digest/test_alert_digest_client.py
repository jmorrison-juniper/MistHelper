"""Tests for the alert digest Mist API client."""

from __future__ import annotations  # Enable modern annotations without runtime imports.

from typing import Any  # Type fake SDK helper inputs.
from unittest.mock import MagicMock, call, patch  # Replace mistapi without network calls.

from src.mist.intelligence.reports.alert_digest.client import (
    ALARM_PAGE_LIMIT,
    AlertDigestClient,
)  # Test the client wrapper.

from .conftest import ORG_ID, FakeResponse, alarm, alarm_page, definition  # Reuse fake response factories.


def client(session: Any | None = None) -> AlertDigestClient:
    """Return a client that uses a fake session."""
    return AlertDigestClient(session or MagicMock(), ORG_ID)  # Build the client under test.


def test_list_alarm_definitions_uses_sdk_method() -> None:
    """The client wraps listAlarmDefinitions."""
    with patch("src.mist.intelligence.reports.alert_digest.client.mistapi") as mistapi_module:  # Replace SDK calls.
        mistapi_module.api.v1.const.alarm_defs.listAlarmDefinitions.return_value = FakeResponse(200, [definition()])
        assert client().list_alarm_definitions()[0]["key"] == "device_down"  # Confirm returned row.
        mistapi_module.api.v1.const.alarm_defs.listAlarmDefinitions.assert_called_once()  # Confirm SDK wrapper.


def test_search_alarms_uses_duration_and_limit() -> None:
    """The alarm search uses the shared lookback window."""
    session = MagicMock()  # Fake session object.
    with patch("src.mist.intelligence.reports.alert_digest.client.mistapi") as mistapi_module:  # Replace SDK calls.
        mistapi_module.api.v1.orgs.alarms.searchOrgAlarms.return_value = alarm_page([alarm(1)])
        result = client(session).search_alarms(24)  # Run one-page search.
        assert [row["id"] for row in result.rows] == ["alarm-1"]  # Confirm rows returned.
        mistapi_module.api.v1.orgs.alarms.searchOrgAlarms.assert_called_once_with(
            session, ORG_ID, duration="24h", limit=ALARM_PAGE_LIMIT
        )


def test_search_alarms_follows_next_links() -> None:
    """The client follows paged alarm search results."""
    session = MagicMock()  # Fake session object.
    first = alarm_page([alarm(1)], next_link="/next")  # First page has a next link.
    second = alarm_page([alarm(2)])  # Second page ends the read.
    with patch("src.mist.intelligence.reports.alert_digest.client.mistapi") as mistapi_module:  # Replace SDK calls.
        mistapi_module.api.v1.orgs.alarms.searchOrgAlarms.return_value = first
        mistapi_module.get_next.return_value = second
        result = client(session).search_alarms(8)  # Run paged search.
        assert [row["id"] for row in result.rows] == ["alarm-1", "alarm-2"]  # Confirm both pages.
        mistapi_module.get_next.assert_has_calls([call(session, first)])  # Confirm SDK paging helper.


def test_search_alarms_reports_failed_page() -> None:
    """A failed page returns no rows and names the problem."""
    with patch("src.mist.intelligence.reports.alert_digest.client.mistapi") as mistapi_module:  # Replace SDK calls.
        mistapi_module.api.v1.orgs.alarms.searchOrgAlarms.return_value = FakeResponse(403, {"detail": "forbidden"})
        result = client().search_alarms(24)  # Run failed search.
        assert result.rows == []  # Confirm no partial rows.
        assert result.problem == "The alarm search returned HTTP 403."  # Confirm clear error text.


def test_list_alarm_definitions_reports_server_failure() -> None:
    """A 5xx definition read returns an empty definition list."""
    with patch("src.mist.intelligence.reports.alert_digest.client.mistapi") as mistapi_module:  # Replace SDK calls.
        mistapi_module.api.v1.const.alarm_defs.listAlarmDefinitions.return_value = FakeResponse(500, {})
        assert client().list_alarm_definitions() == []  # Confirm failed constants read becomes unknown mapping.


def test_acknowledge_and_unacknowledge_use_bulk_sdk_methods() -> None:
    """The client wraps both bulk alarm state change methods."""
    session = MagicMock()  # Fake session object.
    with patch("src.mist.intelligence.reports.alert_digest.client.mistapi") as mistapi_module:  # Replace SDK calls.
        mistapi_module.api.v1.orgs.alarms.ackOrgMultipleAlarms.return_value = FakeResponse(200, {})
        mistapi_module.api.v1.orgs.alarms.unackOrgMultipleAlarms.return_value = FakeResponse(200, {})
        assert client(session).acknowledge_alarms(["alarm-1"]) == (200, "")  # Confirm acknowledgement success.
        assert client(session).unacknowledge_alarms(["alarm-1"]) == (200, "")  # Confirm unacknowledgement success.
        mistapi_module.api.v1.orgs.alarms.ackOrgMultipleAlarms.assert_called_once()  # Confirm ack wrapper.
        mistapi_module.api.v1.orgs.alarms.unackOrgMultipleAlarms.assert_called_once()  # Confirm unack wrapper.


def test_acknowledge_reports_client_failure() -> None:
    """A 4xx acknowledgement response returns the HTTP problem."""
    with patch("src.mist.intelligence.reports.alert_digest.client.mistapi") as mistapi_module:  # Replace SDK calls.
        mistapi_module.api.v1.orgs.alarms.ackOrgMultipleAlarms.return_value = FakeResponse(400, {"detail": "bad"})
        status, problem = client().acknowledge_alarms(["alarm-1"])  # Run failed acknowledgement.
        assert status == 400  # Confirm the HTTP status is preserved.
        assert "HTTP 400" in problem  # Confirm the problem is operator-readable.


def test_unacknowledge_reports_server_failure() -> None:
    """A 5xx unacknowledgement response returns the HTTP problem."""
    with patch("src.mist.intelligence.reports.alert_digest.client.mistapi") as mistapi_module:  # Replace SDK calls.
        mistapi_module.api.v1.orgs.alarms.unackOrgMultipleAlarms.return_value = FakeResponse(503, {"detail": "busy"})
        status, problem = client().unacknowledge_alarms(["alarm-1"])  # Run failed unacknowledgement.
        assert status == 503  # Confirm the HTTP status is preserved.
        assert "HTTP 503" in problem  # Confirm the problem is operator-readable.
