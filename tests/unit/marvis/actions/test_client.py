"""Tests for the Mist API client of menu 270.

The client reads the Marvis Actions list page by page, reads the topic schema
and the site names, and sends one resolve request at a time. These tests prove
the paging rules, the refusal of a partial list, and the exact request shapes.
No test touches the network.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.marvis.actions import client as client_module
from src.marvis.actions.client import (
    ERROR_TEXT_LIMIT,
    LIST_PATH,
    RESOLVE_PATH,
    SCHEMA_PATH,
    SITE_PAGE_LIMIT,
    MarvisActionsClient,
)
from tests.unit.marvis.actions.conftest import ORG_ID, SITE_ID, SITE_NAME, FakeMistSession, FakeResponse, make_raw


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

    def test_a_refused_page_names_the_status(self) -> None:
        """The operator must learn the HTTP status."""
        session = FakeMistSession(rows(1))
        session.list_statuses = [500]
        assert client_for(session).list_actions().problem == "The API returned HTTP 500."

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
