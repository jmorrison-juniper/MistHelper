"""Tests for the pagination guards in ``MistEndpointService._paginate``.

Issue #1903. The loop followed the ``next`` cursor with no page limit and no
cycle guard. A repeated cursor made the loop run forever and grow the worker
heap until the operating system stopped the process.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.shared.mist.endpoints import MAX_PAGINATION_PAGES, MistEndpointService
from src.shared.mist.types import MistEndpoint, MistEntityRegistry

_ENDPOINT = MistEndpoint(
    entity_type="org_site_list",
    api_module="orgs.sites",
    read_method=None,
    write_method=None,
    id_params=("org_id",),
    list_method="listOrgSites",
)


def _make_response(data: list, next_url: str | None = None) -> SimpleNamespace:
    """Create a mock SDK response object."""
    return SimpleNamespace(status_code=200, data=data, next=next_url)


def _run(service: MistEndpointService, mock_func: MagicMock):
    """Call list_all_entities with the registry and resolver patched out."""
    with (
        patch.object(service, "_resolve_func", return_value=mock_func),
        patch.object(MistEntityRegistry, "get", return_value=_ENDPOINT),
    ):
        return service.list_all_entities("org_site_list", {"org_id": "test-org"})


EXPECTED_CALLS_ON_REPEAT = 2
EXPECTED_CALLS_ON_ALTERNATING_PAIR = 3
EXPECTED_CALLS_FOR_THREE_PAGES = 3


class TestPaginationCycleGuard:
    """Verify a repeated cursor ends the loop instead of running forever."""

    def test_a_repeated_cursor_stops_the_loop(self) -> None:
        """A server that always returns the same cursor must not hang the worker."""
        service = MistEndpointService(MagicMock())
        # WHY: every page points back at the same cursor, so the old loop never ended.
        mock_func = MagicMock(return_value=_make_response([{"id": "a"}], next_url="/same"))

        result = _run(service, mock_func)

        assert mock_func.call_count == EXPECTED_CALLS_ON_REPEAT
        assert result.data == [{"id": "a"}, {"id": "a"}]

    def test_the_repeat_is_logged_as_an_error(self, caplog) -> None:
        """The operator needs the endpoint name when the loop stops early."""
        service = MistEndpointService(MagicMock())
        mock_func = MagicMock(return_value=_make_response([{"id": "a"}], next_url="/same"))

        with caplog.at_level(logging.ERROR):
            _run(service, mock_func)

        assert "repeated a cursor" in caplog.text

    def test_an_alternating_cursor_pair_stops_the_loop(self) -> None:
        """Two cursors that point at each other must not run forever."""
        service = MistEndpointService(MagicMock())
        pages = [
            _make_response([{"id": "a"}], next_url="/one"),
            _make_response([{"id": "b"}], next_url="/two"),
            _make_response([{"id": "c"}], next_url="/one"),
            _make_response([{"id": "d"}], next_url="/two"),
        ]
        mock_func = MagicMock(side_effect=pages)

        result = _run(service, mock_func)

        # WHY: /one and /two are both seen, so the third repeat ends the loop.
        assert mock_func.call_count == EXPECTED_CALLS_ON_ALTERNATING_PAIR
        assert result.data == [{"id": "a"}, {"id": "b"}, {"id": "c"}]


class TestPaginationPageLimit:
    """Verify the loop stops at the configured page limit."""

    def test_the_loop_stops_at_the_page_limit(self) -> None:
        """A stream of unique cursors must still stop at MAX_PAGINATION_PAGES."""
        service = MistEndpointService(MagicMock())
        counter = {"page": 0}

        def _next_page(*_args, **_kwargs) -> SimpleNamespace:
            counter["page"] += 1
            return _make_response([{"id": counter["page"]}], next_url=f"/page{counter['page']}")

        mock_func = MagicMock(side_effect=_next_page)

        result = _run(service, mock_func)

        assert mock_func.call_count == MAX_PAGINATION_PAGES
        assert len(result.data) == MAX_PAGINATION_PAGES

    def test_the_limit_is_logged_as_a_warning(self, caplog) -> None:
        """An incomplete result must announce itself."""
        service = MistEndpointService(MagicMock())
        counter = {"page": 0}

        def _next_page(*_args, **_kwargs) -> SimpleNamespace:
            counter["page"] += 1
            return _make_response([{"id": counter["page"]}], next_url=f"/page{counter['page']}")

        with caplog.at_level(logging.WARNING):
            _run(service, MagicMock(side_effect=_next_page))

        assert "page limit" in caplog.text


class TestPaginationNormalPathIsUnchanged:
    """Verify the guards do not change a healthy pagination run."""

    def test_a_single_page_still_returns_one_call(self) -> None:
        """A response with no cursor must not trigger a second call."""
        service = MistEndpointService(MagicMock())
        mock_func = MagicMock(return_value=_make_response([{"id": "a"}]))

        result = _run(service, mock_func)

        assert mock_func.call_count == 1
        assert result.data == [{"id": "a"}]

    def test_three_distinct_pages_all_load(self) -> None:
        """Distinct cursors must still walk to the last page."""
        service = MistEndpointService(MagicMock())
        pages = [
            _make_response([{"id": "a"}], next_url="/page2"),
            _make_response([{"id": "b"}], next_url="/page3"),
            _make_response([{"id": "c"}]),
        ]
        mock_func = MagicMock(side_effect=pages)

        result = _run(service, mock_func)

        assert mock_func.call_count == EXPECTED_CALLS_FOR_THREE_PAGES
        assert result.data == [{"id": "a"}, {"id": "b"}, {"id": "c"}]


class TestPaginationEmptyCursor:
    """Verify an empty cursor ends the loop."""

    def test_an_empty_cursor_ends_the_loop(self) -> None:
        """An empty string cursor must end the loop as it did before."""
        service = MistEndpointService(MagicMock())
        mock_func = MagicMock(return_value=_make_response([{"id": "a"}], next_url=""))

        result = _run(service, mock_func)

        assert mock_func.call_count == 1
        assert result.data == [{"id": "a"}]
