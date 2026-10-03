"""Verify the WiFi page guard and its complete-read boundary."""

from __future__ import annotations

import logging
from collections import deque
from types import SimpleNamespace
from typing import Any

import pytest

from src.export.wifi_clients_exporter import WifiClientsExporter


class _PageSdk:
    """Record page requests without using the SDK's unchecked aggregate helper."""

    def __init__(self, pages: list[object]) -> None:
        """Keep the exact planned pages and request order."""
        self.pages = deque(pages)
        self.requests: list[tuple[str, Any]] = []

    def first(self, session: object, site_id: str, limit: int) -> object:
        """Answer the first request with its concrete status and body."""
        del session
        self.requests.append(("first", (site_id, limit)))
        return self.pages.popleft()

    def get_next(self, mist_session: object, response: Any) -> object:
        """Keep the current page's next link unchanged."""
        del mist_session
        self.requests.append(("next", response.next))
        return self.pages.popleft()

    def get_all(self, **arguments: Any) -> None:
        """Fail if a caller returns to unchecked aggregate pagination."""
        del arguments
        raise AssertionError("The WiFi boundary must validate each page.")


@pytest.mark.parametrize("status_code", [None, "200", True, False, 0, 199, 201, 204, 302, 403, 503])
def test_page_status_requires_real_http_200(status_code: object, caplog: pytest.LogCaptureFixture) -> None:
    """Reject unavailable, invalid, and refused statuses before accepting empty data."""
    page = SimpleNamespace(status_code=status_code, data={"results": []}, next=None)
    sdk = _PageSdk([page])
    exporter = WifiClientsExporter(None, None, None, None, None, None, sdk, object())
    with caplog.at_level(logging.INFO), pytest.raises(RuntimeError, match="successful HTTP 200"):
        WifiClientsExporter._fetch_paginated(exporter, sdk.first, "controlled-site", "wireless clients")
    assert sdk.requests == [("first", ("controlled-site", 1000))]
    assert "Checking 1 WiFi response page for wireless clients for site controlled-site, page 1" in caplog.text


def test_missing_status_cannot_default_to_success() -> None:
    """Reject a page that supplies records but no status attribute."""
    sdk = _PageSdk([SimpleNamespace(data={"results": [{"mac": "aa"}]}, next=None)])
    exporter = WifiClientsExporter(None, None, None, None, None, None, sdk, object())
    with pytest.raises(RuntimeError, match="page 1, HTTP unavailable"):
        WifiClientsExporter._fetch_paginated(exporter, sdk.first, "controlled-site", "wireless clients")
    assert sdk.requests == [("first", ("controlled-site", 1000))]


@pytest.mark.parametrize(
    "payload",
    [None, {}, {"results": None}, {"results": "invalid"}, {"results": [None]}, [1], "[]", True],
)
def test_successful_status_requires_record_objects(payload: object) -> None:
    """Reject malformed successful shapes without discarding invalid records."""
    sdk = _PageSdk([SimpleNamespace(status_code=200, data=payload, next=None)])
    exporter = WifiClientsExporter(None, None, None, None, None, None, sdk, object())
    with pytest.raises(RuntimeError, match="HTTP 200:.*list of record objects"):
        WifiClientsExporter._fetch_paginated(exporter, sdk.first, "controlled-site", "wireless clients")
    assert len(sdk.requests) == 1
    assert len(sdk.pages) == 0


@pytest.mark.parametrize("raw_body", ["", " \n", '{"results":', "<html>unreadable</html>"])
def test_retained_parse_failure_never_becomes_empty_data(raw_body: str) -> None:
    """Reject the SDK's retained evidence without printing body contents."""
    sdk = _PageSdk([SimpleNamespace(status_code=200, data={}, raw_data=raw_body, next=None)])
    exporter = WifiClientsExporter(None, None, None, None, None, None, sdk, object())
    with pytest.raises(RuntimeError, match="HTTP 200:.*(empty|did not parse)") as caught:
        WifiClientsExporter._fetch_paginated(exporter, sdk.first, "controlled-site", "wireless clients")
    assert "controlled-site, page 1" in str(caught.value)
    if raw_body.strip():
        assert raw_body not in str(caught.value)
    assert len(sdk.requests) == 1


@pytest.mark.parametrize("status_code", [None, 403, 503])
def test_later_page_failure_cannot_return_partial_records(status_code: int | None) -> None:
    """Reject a lost later page after a complete first page."""
    first = SimpleNamespace(status_code=200, data={"results": [{"mac": "aa"}]}, next="/next?cursor=kept")
    later = SimpleNamespace(status_code=status_code, data={"results": []}, next=None)
    sdk = _PageSdk([first, later])
    exporter = WifiClientsExporter(None, None, None, None, None, None, sdk, object())
    with pytest.raises(RuntimeError, match="page 2, HTTP"):
        WifiClientsExporter._fetch_paginated(exporter, sdk.first, "controlled-site", "wireless client sessions")
    assert sdk.requests == [("first", ("controlled-site", 1000)), ("next", "/next?cursor=kept")]
    assert first.data == {"results": [{"mac": "aa"}]}


def test_missing_later_response_cannot_finish_a_partial_read() -> None:
    """Reject a next-page helper that returns no response."""
    first = SimpleNamespace(status_code=200, data=[{"mac": "aa"}], next="/next")
    sdk = _PageSdk([first, None])
    exporter = WifiClientsExporter(None, None, None, None, None, None, sdk, object())
    with pytest.raises(RuntimeError, match="page 2, HTTP unavailable"):
        WifiClientsExporter._fetch_paginated(exporter, sdk.first, "controlled-site", "wireless clients")
    assert sdk.requests == [("first", ("controlled-site", 1000)), ("next", "/next")]


@pytest.mark.parametrize("next_link", [True, 1, [], {}, "/repeated"])
def test_invalid_or_repeated_link_cannot_finish_a_partial_read(next_link: object) -> None:
    """Reject unusable links without exposing their contents."""
    first = SimpleNamespace(status_code=200, data=[], next="/repeated")
    later = SimpleNamespace(status_code=200, data=[], next=next_link)
    sdk = _PageSdk([first, later])
    exporter = WifiClientsExporter(None, None, None, None, None, None, sdk, object())
    with pytest.raises(RuntimeError, match="page 2, HTTP 200:.*invalid or repeated"):
        WifiClientsExporter._fetch_paginated(exporter, sdk.first, "controlled-site", "wireless clients")
    assert sdk.requests == [("first", ("controlled-site", 1000)), ("next", "/repeated")]


@pytest.mark.parametrize("payload", [[], {"results": []}])
def test_valid_empty_page_can_still_have_a_next_page(payload: object, caplog: pytest.LogCaptureFixture) -> None:
    """Preserve list and search shapes without stopping at an empty linked page."""
    first = SimpleNamespace(status_code=200, data=payload, next="/next?cursor=kept")
    later = SimpleNamespace(status_code=200, data=[{"mac": "b"}, {"mac": "a"}], next=None)
    sdk = _PageSdk([first, later])
    exporter = WifiClientsExporter(None, None, None, None, None, None, sdk, object())
    with caplog.at_level(logging.DEBUG):
        rows = WifiClientsExporter._fetch_paginated(exporter, sdk.first, "controlled-site", "wireless clients")
    assert rows == [{"mac": "b"}, {"mac": "a"}]
    assert sdk.requests == [("first", ("controlled-site", 1000)), ("next", "/next?cursor=kept")]
    assert "Fetched 2 wireless clients records from 2 validated pages" in caplog.text
