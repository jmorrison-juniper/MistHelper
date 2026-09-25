"""Tests for the Mist API client of menu 270.

The client reads the Marvis Actions list page by page, reads the topic schema
and the site names, and sends one resolve request at a time. It also searches
the Marvis alarms page by page. These tests prove the paging rules, the refusal
of a partial list, and the exact request shapes. No test touches the network.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock, call

import pytest

from src.marvis.actions import client as client_module
from src.marvis.actions.client import (
    ALARM_GROUP,
    ALARM_PAGE_LIMIT,
    ERROR_TEXT_LIMIT,
    LIST_PATH,
    RESOLVE_PATH,
    SCHEMA_PATH,
    SITE_PAGE_LIMIT,
    MarvisActionsClient,
)
from tests.unit.marvis.actions.conftest import (
    ORG_ID,
    SITE_ID,
    SITE_NAME,
    FakeMistSession,
    FakeResponse,
    make_alarm,
    make_alarm_page,
    make_raw,
)


def rows(count: int) -> list[dict[str, Any]]:
    """Return a number of distinct raw rows."""
    return [make_raw(number) for number in range(1, count + 1)]


def client_for(session: Any, page_limit: int = 1000) -> MarvisActionsClient:
    """Return a client for the synthetic organization."""
    return MarvisActionsClient(session, ORG_ID, page_limit)


class TestListRead:
    """The list read follows the paging rules of the Mist UI endpoint."""

    def test_one_page_holds_every_row(self) -> None:
        """A page that reaches the total ends the read."""
        session = FakeMistSession(rows(3))
        result = client_for(session).list_actions()
        assert (len(result.rows), result.complete, result.problem, len(session.list_gets())) == (3, True, "", 1)

    def test_the_request_sends_the_query_of_the_mist_ui(self) -> None:
        """The endpoint returns the action rows only for these values."""
        session = FakeMistSession(rows(1))
        client_for(session, page_limit=250).list_actions()
        assert session.list_gets()[0] == {
            "query": "get_suggestion",
            "resolve_wcid": "true",
            "limit": "250",
            "page": "1",
        }

    def test_the_request_names_the_organization(self) -> None:
        """Every list path names the organization of the run."""
        session = FakeMistSession(rows(1))
        client_for(session).list_actions()
        assert session.gets[0][0] == LIST_PATH.format(org_id=ORG_ID)

    def test_the_read_follows_the_pages_until_the_total(self) -> None:
        """Five rows with a page size of 2 need three pages."""
        session = FakeMistSession(rows(5))
        result = client_for(session, page_limit=2).list_actions()
        pages = [query["page"] for query in session.list_gets()]
        assert (len(result.rows), pages) == (5, ["1", "2", "3"])

    def test_the_total_stops_the_read_on_a_full_page(self) -> None:
        """Four rows with a page size of 2 need two pages, not a third empty page."""
        session = FakeMistSession(rows(4))
        client_for(session, page_limit=2).list_actions()
        assert len(session.list_gets()) == 2

    def test_a_short_page_ends_a_read_without_a_total(self) -> None:
        """Without a total, a page with fewer rows than the limit is the last page."""
        session = FakeMistSession(rows(3))
        session.include_total = False
        result = client_for(session, page_limit=2).list_actions()
        assert (len(result.rows), len(session.list_gets())) == (3, 2)

    def test_an_empty_page_ends_a_read_without_a_total(self) -> None:
        """Without a total, an empty page after a full page ends the read."""
        session = FakeMistSession(rows(4))
        session.include_total = False
        result = client_for(session, page_limit=2).list_actions()
        assert (len(result.rows), len(session.list_gets())) == (4, 3)

    def test_the_stated_limit_of_the_response_decides_a_short_page(self) -> None:
        """If the server caps the page size, a page of that size is not the last page."""
        session = MagicMock()
        session.mist_get.side_effect = [
            FakeResponse(200, {"results": [make_raw(1), make_raw(2)], "limit": 2}),
            FakeResponse(200, {"results": [make_raw(3)], "limit": 2}),
        ]
        result = client_for(session, page_limit=10).list_actions()
        assert (len(result.rows), session.mist_get.call_count) == (3, 2)

    def test_an_item_that_is_not_a_row_is_skipped(self) -> None:
        """A list item that is not an object cannot become a record."""
        session = MagicMock()
        session.mist_get.return_value = FakeResponse(200, {"results": [make_raw(1), "noise", None], "total": 3})
        result = client_for(session).list_actions()
        assert (len(result.rows), session.mist_get.call_count) == (1, 1)

    def test_a_refused_page_discards_every_row(self) -> None:
        """A partial list must never reach a file or a resolve."""
        session = FakeMistSession(rows(4))
        session.list_statuses = [200, 403]
        result = client_for(session, page_limit=2).list_actions()
        assert (result.rows, result.status_code, result.complete) == ([], 403, False)

    def test_a_server_error_page_names_the_status(self) -> None:
        """The operator must learn the HTTP status when the Mist cloud fails."""
        session = FakeMistSession(rows(1))  # One stored row, so only the status can empty the result.
        session.list_statuses = [500]  # The first list page returns a server error.
        result = client_for(session).list_actions()  # Read the list through the product client.
        assert result.status_code == 500  # The result keeps the server error status for the log line.
        assert (result.rows, result.complete, result.problem) == (
            [],
            False,
            "The API returned HTTP 500.",
        )  # A server error gives no rows, an incomplete read, and a named status.

    def test_a_missing_answer_points_to_the_script_log(self) -> None:
        """mistapi returns no status when no HTTP answer arrived."""
        session = MagicMock()
        session.mist_get.return_value = FakeResponse(None, None)
        assert "script.log" in client_for(session).list_actions().problem

    def test_a_changed_response_shape_is_refused(self) -> None:
        """A body without a results list cannot be read safely."""
        session = MagicMock()
        session.mist_get.return_value = FakeResponse(200, {"data": []})
        assert client_for(session).list_actions().problem == "The response holds no results list."

    def test_the_page_guard_keeps_the_rows_and_warns(self, monkeypatch: pytest.MonkeyPatch, caplog: Any) -> None:
        """A server that never ends the list must not hold the run forever."""
        monkeypatch.setattr(client_module, "MAX_LIST_PAGES", 3)
        session = MagicMock()
        session.mist_get.side_effect = lambda uri, query: FakeResponse(
            200, {"results": [make_raw(int(query["page"]))], "limit": 1}
        )
        with caplog.at_level(logging.WARNING):
            result = client_for(session, page_limit=1).list_actions()
        assert (len(result.rows), result.complete, result.problem) == (3, False, "")
        assert "reached the guard of 3 pages" in caplog.text

    def test_a_page_size_below_one_is_raised_to_one(self) -> None:
        """A page size of 0 would never end the read."""
        session = FakeMistSession(rows(1))
        client_for(session, page_limit=0).list_actions()
        assert session.list_gets()[0]["limit"] == "1"


class TestSchemaRead:
    """The schema read is optional, so a failure never stops the export."""

    def test_the_schema_entries_are_returned(self) -> None:
        """The entries sit under the data key."""
        session = FakeMistSession([], schema_rows=[{"category": "switch", "symptom": "sw_offline"}, "noise"])
        assert client_for(session).read_schema() == [{"category": "switch", "symptom": "sw_offline"}]

    def test_the_schema_path_is_the_labs_path(self) -> None:
        """The endpoint report names this path."""
        session = FakeMistSession([])
        client_for(session).read_schema()
        assert session.gets[0][0] == SCHEMA_PATH

    def test_a_failed_schema_read_returns_no_entries(self, caplog: Any) -> None:
        """The built-in catalog still names every known topic."""
        session = FakeMistSession([])
        session.schema_status = 404
        with caplog.at_level(logging.WARNING):
            assert client_for(session).read_schema() == []
        assert "recommended_action column stays empty" in caplog.text

    def test_a_schema_body_of_another_shape_returns_no_entries(self) -> None:
        """A body that is not an object holds no entries."""
        session = MagicMock()
        session.mist_get.return_value = FakeResponse(200, ["unexpected"])
        assert client_for(session).read_schema() == []


class TestSiteRead:
    """The site read adds the site name, and a failure never stops the export."""

    def test_the_site_names_are_mapped_by_identifier(self, site_api: MagicMock) -> None:
        """The builder adds the name to each row."""
        assert client_for(MagicMock()).read_site_names() == {SITE_ID: SITE_NAME}

    def test_the_site_read_asks_for_the_largest_page(self, site_api: MagicMock) -> None:
        """Fewer pages cost fewer API calls."""
        session = MagicMock()
        client_for(session).read_site_names()
        site_api.api.v1.orgs.sites.listOrgSites.assert_called_once_with(session, ORG_ID, limit=SITE_PAGE_LIMIT)

    def test_a_failed_site_read_returns_no_names(self, site_api: MagicMock, caplog: Any) -> None:
        """The rows still carry the site identifier."""
        site_api.api.v1.orgs.sites.listOrgSites.return_value = FakeResponse(403, None)
        with caplog.at_level(logging.WARNING):
            assert client_for(MagicMock()).read_site_names() == {}
        assert "site_name column stays empty" in caplog.text
        site_api.get_all.assert_not_called()

    def test_a_site_item_that_is_not_an_object_is_skipped(self, site_api: MagicMock) -> None:
        """A malformed item must not stop the export."""
        site_api.get_all.return_value = [{"id": SITE_ID, "name": SITE_NAME}, "noise"]
        assert client_for(MagicMock()).read_site_names() == {SITE_ID: SITE_NAME}


def alarm_ids(result: Any) -> list[str]:
    """Return the id of each alarm row of one search result, in order."""
    return [row["id"] for row in result.rows]


class TestAlarmSearch:
    """Issue #3339: the alarm search reads every page of the Marvis group, and a failure returns no rows."""

    def test_the_search_sends_the_group_the_window_and_the_largest_page(self, site_api: MagicMock) -> None:
        """The NOC endpoint report names these query values."""
        session = MagicMock()
        client_for(session).search_marvis_alarms(1_700_000_000, 1_700_086_400)
        site_api.api.v1.orgs.alarms.searchOrgAlarms.assert_called_once_with(
            session, ORG_ID, group=ALARM_GROUP, start="1700000000", end="1700086400", limit=ALARM_PAGE_LIMIT
        )

    def test_the_group_is_marvis_and_the_page_is_the_largest(self) -> None:
        """The other alarm groups hold no action, and a large page saves requests."""
        assert (ALARM_GROUP, ALARM_PAGE_LIMIT) == ("marvis", 1000)

    def test_one_page_without_a_link_holds_every_alarm(self, site_api: MagicMock) -> None:
        """The live organization returned 33 alarms on one page without a next link."""
        site_api.api.v1.orgs.alarms.searchOrgAlarms.return_value = make_alarm_page([make_alarm(1), make_alarm(2)])
        result = client_for(MagicMock()).search_marvis_alarms(1, 2)
        expected = [make_alarm(1)["id"], make_alarm(2)["id"]]
        assert (alarm_ids(result), result.status_code, result.complete, result.problem) == (expected, 200, True, "")
        assert site_api.get_next.call_count == 0

    def test_the_search_follows_each_next_link(self, site_api: MagicMock) -> None:
        """The next link carries the search_after value of the page."""
        first = make_alarm_page([make_alarm(1)], next_link="/api/v1/orgs/org/alarms/search?search_after=a")
        second = make_alarm_page([make_alarm(2)], next_link="/api/v1/orgs/org/alarms/search?search_after=b")
        site_api.api.v1.orgs.alarms.searchOrgAlarms.return_value = first
        site_api.get_next.side_effect = [second, make_alarm_page([make_alarm(3)])]
        session = MagicMock()
        result = client_for(session).search_marvis_alarms(1, 2)
        assert (alarm_ids(result), result.complete) == ([make_alarm(n)["id"] for n in (1, 2, 3)], True)
        site_api.get_next.assert_has_calls([call(session, first), call(session, second)])

    def test_a_refused_page_discards_every_alarm(self, site_api: MagicMock) -> None:
        """A token without the alarm role receives HTTP 403."""
        site_api.api.v1.orgs.alarms.searchOrgAlarms.return_value = FakeResponse(403, {"detail": "forbidden"})
        result = client_for(MagicMock()).search_marvis_alarms(1, 2)
        assert (result.rows, result.status_code, result.complete) == ([], 403, False)
        assert result.problem == "The API returned HTTP 403."

    def test_a_refused_second_page_discards_the_first_page(self, site_api: MagicMock) -> None:
        """A partial alarm list would show an empty alarm cell as a fact."""
        site_api.api.v1.orgs.alarms.searchOrgAlarms.return_value = make_alarm_page([make_alarm(1)], next_link="/next")
        site_api.get_next.return_value = FakeResponse(500, None)
        result = client_for(MagicMock()).search_marvis_alarms(1, 2)
        assert (result.rows, result.status_code, result.problem) == ([], 500, "The API returned HTTP 500.")

    def test_a_missing_next_page_is_a_problem(self, site_api: MagicMock) -> None:
        """The get_next helper returns None when the response holds no next link."""
        site_api.api.v1.orgs.alarms.searchOrgAlarms.return_value = make_alarm_page([make_alarm(1)], next_link="/next")
        site_api.get_next.return_value = None
        result = client_for(MagicMock()).search_marvis_alarms(1, 2)
        assert (result.rows, result.status_code, result.complete) == ([], None, False)
        assert result.problem == "The alarm search returned no next page."

    def test_a_missing_answer_points_to_the_script_log(self, site_api: MagicMock) -> None:
        """The mistapi library returns no status when no HTTP answer arrived."""
        site_api.api.v1.orgs.alarms.searchOrgAlarms.return_value = FakeResponse(None, None)
        result = client_for(MagicMock()).search_marvis_alarms(1, 2)
        assert result.problem == "No HTTP answer arrived. Read the mistapi line in script.log."

    def test_a_changed_response_shape_is_refused(self, site_api: MagicMock) -> None:
        """A body without a results list holds no alarm."""
        site_api.api.v1.orgs.alarms.searchOrgAlarms.return_value = FakeResponse(200, [make_alarm(1)])
        result = client_for(MagicMock()).search_marvis_alarms(1, 2)
        assert (result.rows, result.problem) == ([], "The response holds no results list.")

    def test_a_repeated_link_stops_the_read_and_warns(self, site_api: MagicMock, caplog: Any) -> None:
        """A link that repeats would read the same page again and again."""
        site_api.api.v1.orgs.alarms.searchOrgAlarms.return_value = make_alarm_page([make_alarm(1)], next_link="/same")
        site_api.get_next.side_effect = [make_alarm_page([make_alarm(2)], next_link="/same")]
        with caplog.at_level(logging.WARNING):
            result = client_for(MagicMock()).search_marvis_alarms(1, 2)
        assert (len(result.rows), result.complete, result.problem, site_api.get_next.call_count) == (2, False, "", 1)
        assert "stopped at page 2 before its last page. The join holds the first 2 alarms only." in caplog.text

    def test_the_page_guard_keeps_the_alarms_and_warns(
        self, monkeypatch: pytest.MonkeyPatch, site_api: MagicMock, caplog: Any
    ) -> None:
        """A server that never ends the alarm list must not hold the run forever."""
        monkeypatch.setattr(client_module, "MAX_ALARM_PAGES", 3)
        numbers = iter(range(2, 10))

        def next_page(session: Any, response: Any) -> FakeResponse:
            number = next(numbers)
            return make_alarm_page([make_alarm(number)], next_link=f"/page/{number}")

        site_api.api.v1.orgs.alarms.searchOrgAlarms.return_value = make_alarm_page([make_alarm(1)], next_link="/page/1")
        site_api.get_next.side_effect = next_page
        with caplog.at_level(logging.WARNING):
            result = client_for(MagicMock()).search_marvis_alarms(1, 2)
        assert (len(result.rows), result.complete, result.problem, site_api.get_next.call_count) == (3, False, "", 2)
        assert "stopped at page 3 before its last page. The join holds the first 3 alarms only." in caplog.text

    def test_an_alarm_of_another_group_is_skipped(self, site_api: MagicMock) -> None:
        """The API filters by group, and the client keeps a stray row out of the join."""
        page = [make_alarm(1), make_alarm(2, group="infrastructure"), make_alarm(3, group=None), make_alarm(4)]
        site_api.api.v1.orgs.alarms.searchOrgAlarms.return_value = make_alarm_page(page)
        result = client_for(MagicMock()).search_marvis_alarms(1, 2)
        assert alarm_ids(result) == [make_alarm(1)["id"], make_alarm(4)["id"]]

    def test_an_item_that_is_not_an_object_is_skipped(self, site_api: MagicMock) -> None:
        """A malformed item must not stop the export."""
        site_api.api.v1.orgs.alarms.searchOrgAlarms.return_value = make_alarm_page([make_alarm(1), "noise", None, [1]])
        assert alarm_ids(client_for(MagicMock()).search_marvis_alarms(1, 2)) == [make_alarm(1)["id"]]

    def test_an_empty_page_ends_the_read_even_with_a_link(self, site_api: MagicMock) -> None:
        """An empty page holds no search position, so a next read would find nothing new."""
        site_api.api.v1.orgs.alarms.searchOrgAlarms.return_value = make_alarm_page([], next_link="/more")
        result = client_for(MagicMock()).search_marvis_alarms(1, 2)
        assert (result.rows, result.complete, result.problem, site_api.get_next.call_count) == ([], True, "", 0)

    def test_the_search_logs_each_page_and_the_result(self, site_api: MagicMock, caplog: Any) -> None:
        """The script log shows the window, each page, and the count."""
        site_api.api.v1.orgs.alarms.searchOrgAlarms.return_value = make_alarm_page([make_alarm(1)])
        with caplog.at_level(logging.DEBUG, logger=client_module.__name__):
            client_for(MagicMock()).search_marvis_alarms(10, 20)
        for line in (
            f"Searching the Marvis alarms of org {ORG_ID} from 10 to 20",
            "Reading Marvis alarm page 1",
            "Marvis alarm page 1 returned HTTP 200",
            "Read 1 Marvis alarms on 1 pages",
        ):
            assert line in caplog.text, line


class TestResolveRequest:
    """The resolve request uses the path and the body of the Mist UI."""

    def test_the_request_goes_to_the_labs_suggestions_path(self) -> None:
        """The endpoint report names this path."""
        session = FakeMistSession([make_raw(1)])
        client_for(session).resolve_action({"row_key": "synthetic-row-key-0001", "status": "resolved"})
        assert session.puts[0][0] == RESOLVE_PATH.format(org_id=ORG_ID)

    def test_the_body_reaches_the_api_unchanged(self) -> None:
        """The client must not add or drop a field."""
        session = FakeMistSession([make_raw(1)])
        body = {"row_key": "synthetic-row-key-0001", "status": "resolved", "label": "known", "comment": ""}
        client_for(session).resolve_action(body)
        assert session.puts[0][1] == body

    @pytest.mark.parametrize("status", [200, 201, 204])
    def test_every_success_status_returns_no_error(self, status: int) -> None:
        """Every 2xx status means that Mist accepted the request."""
        session = FakeMistSession([make_raw(1)])
        session.put_statuses = [status]
        assert client_for(session).resolve_action({"row_key": "x"}) == (status, "")

    def test_a_refused_request_returns_the_status_and_the_body(self) -> None:
        """The results file shows why Mist refused the request."""
        session = FakeMistSession([make_raw(1)])
        session.put_statuses = [400]
        status, error = client_for(session).resolve_action({"row_key": "x"})
        assert (status, error) == (400, 'HTTP 400 {"detail": "the request was refused"}')

    def test_a_server_error_returns_the_status_and_the_body(self) -> None:
        """A 5xx answer means that Mist did not resolve the action."""
        session = FakeMistSession([make_raw(1)])  # One stored row, so the request has a real target.
        session.put_statuses = [503]  # The resolve request returns a server error.
        status, error = client_for(session).resolve_action({"row_key": "synthetic-row-key-0001"})  # Send one request.
        assert status == 503  # The caller receives the server error status, not a success.
        assert error == 'HTTP 503 {"detail": "the request was refused"}'  # The results file names the status.
        assert session.rows[0]["status"] == "open"  # The fake session applied no status change.

    def test_a_long_error_body_is_shortened(self) -> None:
        """One results cell stays short enough to read."""
        session = MagicMock()
        session.mist_put.return_value = FakeResponse(500, {"detail": "x" * 2000})
        _, error = client_for(session).resolve_action({"row_key": "x"})
        assert len(error) == ERROR_TEXT_LIMIT

    def test_a_missing_answer_returns_no_status(self) -> None:
        """mistapi returns no status when no HTTP answer arrived."""
        session = MagicMock()
        session.mist_put.return_value = FakeResponse(None, None)
        status, error = client_for(session).resolve_action({"row_key": "x"})
        assert status is None
        assert "script.log" in error

    def test_a_refused_request_without_a_body_names_the_status_only(self) -> None:
        """An empty error body gives a short message."""
        session = MagicMock()
        session.mist_put.return_value = FakeResponse(429, None)
        assert client_for(session).resolve_action({"row_key": "x"}) == (429, "HTTP 429")
