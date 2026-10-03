"""Verify WiFi exports through native SDK transport and the shipped handler."""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import socket
import sys
from collections import Counter, deque
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from types import FrameType, SimpleNamespace
from typing import Any
from unittest.mock import Mock

import mistapi
import pytest
import requests
from mistapi.__api_response import APIResponse
from mistapi.__logger import console as sdk_console
from mistapi.__logger import logger as sdk_logger
from requests.adapters import BaseAdapter, HTTPAdapter

import MistHelper as entrypoint
from src.export.data_exporter import DataExporter
from src.export.site_client_exporter import SiteClientExporter
from src.export.wifi_clients_exporter import WifiClientsExporter
from src.refactors.main_entrypoint import MainEntrypoint

pytestmark = [pytest.mark.integration, pytest.mark.timeout(30)]


@dataclass
class _Reply:
    """Describe one controlled HTTP response."""

    status_code: object = 200
    body: bytes = b'{"results":[]}'
    headers: dict[str, str] = field(default_factory=dict)
    error: requests.RequestException | None = None


class _ControlledTransport(BaseAdapter):
    """Answer native SDK requests without opening a network connection."""

    def __init__(self) -> None:
        """Start with two valid empty responses."""
        super().__init__()
        self.replies = deque([_Reply(), _Reply()])
        self.urls: list[str] = []
        self.closed = False

    def send(self, request: requests.PreparedRequest, **options: Any) -> requests.Response:
        """Return one controlled response at the actual transport boundary."""
        del options
        if request.method != "GET" or not str(request.url).startswith("https://api.mist.com/api/v1/sites/"):
            raise AssertionError("The native test permits site reads only.")
        self.urls.append(str(request.url))
        if not self.replies:
            raise AssertionError("The native test has no planned response.")
        reply = self.replies.popleft()
        if reply.error is not None:
            raise reply.error
        response = requests.Response()
        response.status_code = reply.status_code
        response.headers.update({"Content-Type": "application/json", **reply.headers})
        response.raw = io.BytesIO(reply.body)
        response.encoding = "utf-8"
        response.url = str(request.url)
        response.request = request
        return response

    def close(self) -> None:
        """Record closure of the owned transport."""
        self.closed = True


class _NativeCallbacks:
    """Build observations without replacing successful output behavior."""

    @classmethod
    def create(cls) -> dict[str, Mock]:
        """Count real writes and stop every unplanned network or SQLite action."""
        return {
            "answer": Mock(return_value="0"),
            "export": Mock(wraps=DataExporter.write_with_format_selection),
            "csv": Mock(wraps=csv.writer),
            "router": Mock(side_effect=cls.router_result),
            "sqlite": Mock(side_effect=AssertionError("A SQLite constructor must not run.")),
            "live_http": Mock(side_effect=AssertionError("A live HTTP request must not run.")),
            "socket": Mock(side_effect=AssertionError("A live socket must not run.")),
        }

    @staticmethod
    def router_result(rows: list[dict[str, Any]], endpoint: str) -> SimpleNamespace:
        """Record a controlled router result without accessing a store."""
        del endpoint
        return SimpleNamespace(success=True, records_written=len(rows), records_failed=0, backend="controlled")

    @staticmethod
    def expected_counts(sdk: int, output: tuple[int, int, int] = (0, 0, 0)) -> dict[str, int]:
        """Describe one actual handler run and its expected output boundaries."""
        export, csv_count, router = output
        return {
            "answer": 1,
            "export": export,
            "csv": csv_count,
            "router": router,
            "sqlite": 0,
            "live_http": 0,
            "socket": 0,
            "handler": 1,
            "exporter": 1,
            "sdk": sdk,
            "transport": sdk,
            "setup_csv": 1,
        }


class _FailurePages:
    """Place a failed native reply at one requested endpoint and page."""

    @staticmethod
    def create(reply: _Reply, endpoint_name: str, later_page: bool) -> deque[_Reply]:
        """Keep earlier pages valid and complete, with a native next-page link."""
        pages = [] if endpoint_name == "clients" else [_Reply(200, b'{"results":[{"mac":"early-client"}]}')]
        if later_page:
            suffix = "" if endpoint_name == "clients" else "/sessions"
            link = f"/api/v1/sites/controlled-site/clients{suffix}/search?cursor=kept&limit=1000"
            body = json.dumps({"results": [{"mac": "early-row", "start_time": 10}], "next": link}).encode()
            pages.append(_Reply(200, body))
        pages.append(reply)
        if endpoint_name == "clients":
            pages.append(_Reply())  # The original companion session control remains valid empty data.
        return deque(pages)


class _MergedCase:
    """Keep independent input and expected records for the complete merge."""

    class Clients:
        """Supply list pages and native pagination headers."""

        FIRST = [
            {
                "mac": "aa",
                "hostname": "Client Caf\u00e9",
                "ssid": "client-ssid",
                "details": {"score": 7},
                "notes": "line1\nline2",
            }
        ]
        LAST = [{"mac": "bb", "hostname": "client-2"}]
        HEADERS = {"X-Page-Total": "2", "X-Page-Limit": "1", "X-Page-Page": "1"}

    class Sessions:
        """Supply search pages with a native cursor link."""

        FIRST = {
            "results": [{"mac": "aa", "start_time": 10, "duration": 3, "ssid": "old"}],
            "next": "/api/v1/sites/controlled-site/clients/sessions/search?cursor=session-page",
        }
        LAST = {
            "results": [
                {"mac": "aa", "start_time": 20, "duration": 9, "ssid": "latest", "extra": {"score": 8}},
                {"mac": "cc", "start_time": 5, "duration": 4, "ssid": "orphan"},
            ]
        }

    EXPECTED = [
        {
            "mac": "aa",
            "hostname": "Client Caf\u00e9",
            "ssid": "client-ssid",
            "details_score": 7,
            "notes": "line1\\nline2",
            "site_id": "controlled-site",
            "site_name": "Lab Site",
            "data_source": "client",
            "session_start_time": 20,
            "session_duration": 9,
            "session_extra_score": 8,
            "session_count": 2,
        },
        {
            "mac": "bb",
            "hostname": "client-2",
            "site_id": "controlled-site",
            "site_name": "Lab Site",
            "data_source": "client",
            "session_count": 0,
        },
        {
            "session_mac": "cc",
            "session_start_time": 5,
            "session_duration": 4,
            "session_ssid": "orphan",
            "site_id": "controlled-site",
            "site_name": "Lab Site",
            "data_source": "session_only",
            "session_count": 1,
        },
    ]
    URLS = [
        "https://api.mist.com/api/v1/sites/controlled-site/clients/search?limit=1000",
        "https://api.mist.com/api/v1/sites/controlled-site/clients/search?limit=1000&page=2",
        "https://api.mist.com/api/v1/sites/controlled-site/clients/sessions/search?limit=1000",
        "https://api.mist.com/api/v1/sites/controlled-site/clients/sessions/search?cursor=session-page",
    ]

    @classmethod
    def replies(cls) -> deque[_Reply]:
        """Build the actual transport bodies without computing expected enrichment."""
        return deque(
            [
                _Reply(200, json.dumps(cls.Clients.FIRST).encode(), cls.Clients.HEADERS),
                _Reply(200, json.dumps(cls.Clients.LAST).encode()),
                _Reply(200, json.dumps(cls.Sessions.FIRST).encode()),
                _Reply(200, json.dumps(cls.Sessions.LAST).encode()),
            ]
        )


class _NativeRun:
    """Own native resources and observe real handler and writer boundaries."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Build a credential-free native session and counted output boundaries."""
        self.transport = _ControlledTransport()
        self.session = mistapi.APISession(host="api.mist.com", console_log_level=0, show_cli_notif=False)
        self.session._session.trust_env = False  # Do not read a proxy or a netrc credential.
        self.session._session.mount("https://", self.transport)
        self.calls: Counter[str] = Counter()
        self.responses: list[APIResponse] = []
        self.callbacks = _NativeCallbacks.create()
        self._prepare(monkeypatch)

    def _prepare(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Install observations and create only the separate prompt cache."""
        monkeypatch.setattr(MainEntrypoint.context, "apisession", self.session)
        monkeypatch.setattr(MainEntrypoint.context, "output_format", "csv")
        monkeypatch.setenv("MISTHELPER_STANDALONE", "false")
        monkeypatch.setattr(DataExporter, "_router_initialized", True)
        monkeypatch.setattr(DataExporter, "_router", SimpleNamespace(write=self.callbacks["router"]))
        monkeypatch.setattr("src.export.data_exporter.SQLiteDatabaseWriter", self.callbacks["sqlite"])
        monkeypatch.setattr(HTTPAdapter, "send", self.callbacks["live_http"])
        monkeypatch.setattr(socket.socket, "connect", self.callbacks["socket"])
        monkeypatch.setattr("builtins.input", self.callbacks["answer"])
        monkeypatch.setattr(csv, "writer", self.callbacks["csv"])
        DataExporter.write_to_csv([{"id": "controlled-site", "name": "Lab Site"}], "SiteList.csv")
        self.setup_csv_calls = self.callbacks["csv"].call_count
        self.callbacks["csv"].reset_mock()  # Exclude the prompt-cache write from final output counts.
        monkeypatch.setattr(DataExporter, "write_with_format_selection", self.callbacks["export"])

    @contextmanager
    def observe(self) -> Iterator[None]:
        """Count actual Python boundaries without replacing the source methods."""
        previous = sys.getprofile()
        codes = {
            SiteClientExporter.wifi_clients.__code__: "handler",
            WifiClientsExporter.execute.__code__: "exporter",
        }

        def record(frame: FrameType, event: str, result: Any) -> None:
            del result
            if event == "call" and frame.f_code in codes:
                self.calls[codes[frame.f_code]] += 1
            if event == "return" and frame.f_code is APIResponse.__init__.__code__:
                self.responses.append(frame.f_locals["self"])

        sys.setprofile(record)
        try:
            yield
        finally:
            sys.setprofile(previous)

    def measure(self) -> dict[str, int]:
        """Return actual callback counts and the native request count."""
        counts = {name: callback.call_count for name, callback in self.callbacks.items()}
        return {
            **counts,
            "handler": self.calls["handler"],
            "exporter": self.calls["exporter"],
            "sdk": self.session.get_request_count(),
            "transport": len(self.transport.urls),
            "setup_csv": self.setup_csv_calls,
        }

    def require_failure(self, caplog: pytest.LogCaptureFixture, endpoint_name: str, later_page: bool) -> None:
        """Verify the real failure notice and every final-output boundary."""
        expected_calls = 1 + int(endpoint_name == "sessions") + int(later_page)
        assert self.measure() == _NativeCallbacks.expected_counts(expected_calls)
        assert list(Path("data").glob("SiteWiFiClients*")) == []
        notices = "\n".join(
            record.getMessage() for record in caplog.records if record.name.endswith("wifi_clients_exporter")
        )
        label = "wireless clients" if endpoint_name == "clients" else "wireless client sessions"
        assert f"{label} for site controlled-site, page {1 + int(later_page)}" in notices
        assert "! Failed to fetch WiFi data:" in notices
        assert "No WiFi clients or sessions found at this site." not in notices
        assert "WiFi data exported" not in notices


@pytest.fixture
def native_wifi(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> Iterator[_NativeRun]:
    """Keep the native session credential-free and restore every owned resource."""
    for name in tuple(os.environ):
        if name.startswith("MIST_"):
            monkeypatch.delenv(name)
    console_level, logger_level = sdk_console.level, sdk_logger.level
    run = _NativeRun(monkeypatch)
    assert entrypoint.menu_actions["64"].handler is SiteClientExporter.wifi_clients
    try:
        with run.observe():
            yield run
    finally:
        print(f"Native case checked=1 name={request.node.name} counts={json.dumps(run.measure(), sort_keys=True)}")
        run.session._session.close()
        sdk_console.level = console_level
        sdk_logger.setLevel(logger_level)
        assert run.transport.closed is True


@pytest.fixture(params=["csv", "sqlite"])
def output_backend(native_wifi: _NativeRun, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> str:
    """Choose the real output setting after the native resources are ready."""
    assert native_wifi.setup_csv_calls == 1
    monkeypatch.setattr(MainEntrypoint.context, "output_format", request.param)
    return str(request.param)


def test_native_empty_body_refuses_output(native_wifi: _NativeRun, caplog: pytest.LogCaptureFixture) -> None:
    """Reject HTTP 200 with an empty body instead of writing a placeholder."""
    native_wifi.transport.replies = deque([_Reply(200, b""), _Reply()])
    with caplog.at_level(logging.INFO):
        SiteClientExporter.wifi_clients()
    assert native_wifi.responses[0].data == {}
    assert native_wifi.responses[0].raw_data == ""
    counts = native_wifi.measure()
    assert counts["csv"] == 0, counts
    assert counts["export"] == counts["router"] == counts["sqlite"] == counts["live_http"] == counts["socket"] == 0
    assert "Failed to fetch WiFi data" in caplog.text
    assert "No WiFi clients or sessions found at this site." not in caplog.text


def test_native_malformed_json_refuses_output(native_wifi: _NativeRun, caplog: pytest.LogCaptureFixture) -> None:
    """Reject the parse failure that native APIResponse keeps as empty data."""
    body = b'{"results":'
    with pytest.raises(json.JSONDecodeError):
        json.loads(body)
    native_wifi.transport.replies = deque([_Reply(200, body), _Reply()])
    with caplog.at_level(logging.INFO):
        SiteClientExporter.wifi_clients()
    assert native_wifi.responses[0].data == {}
    assert native_wifi.responses[0].raw_data == body.decode()
    counts = native_wifi.measure()
    assert counts["csv"] == 0, counts
    assert counts["export"] == counts["router"] == counts["sqlite"] == counts["live_http"] == counts["socket"] == 0
    assert "Failed to fetch WiFi data" in caplog.text
    assert "No WiFi clients or sessions found at this site." not in caplog.text


@pytest.mark.parametrize("status_code", [403, 503])
def test_native_http_failure_refuses_output(
    native_wifi: _NativeRun, caplog: pytest.LogCaptureFixture, status_code: int
) -> None:
    """Reject native HTTP 4xx and 5xx responses before any final write."""
    native_wifi.transport.replies = deque([_Reply(status_code, b'{"error":"controlled refusal"}'), _Reply()])
    with caplog.at_level(logging.INFO):
        SiteClientExporter.wifi_clients()
    assert native_wifi.responses[0].status_code == status_code
    assert native_wifi.responses[0].data == {"error": "controlled refusal"}
    counts = native_wifi.measure()
    assert counts["csv"] == 0, counts
    assert counts["export"] == counts["router"] == counts["sqlite"] == counts["live_http"] == counts["socket"] == 0
    assert "Failed to fetch WiFi data" in caplog.text
    assert f"HTTP {status_code}" in caplog.text
    assert "No WiFi clients or sessions found at this site." not in caplog.text


def test_native_valid_empty_keeps_placeholder(native_wifi: _NativeRun) -> None:
    """Preserve the real empty-data CSV for two valid empty search responses."""
    SiteClientExporter.wifi_clients()
    with Path("data", "SiteWiFiClients.CSV").open(encoding="utf-8") as output:
        rows = list(csv.DictReader(output))
    assert rows == [
        {"site_id": "controlled-site", "site_name": "Lab Site", "message": "No WiFi clients or sessions found"}
    ]
    assert native_wifi.measure() == _NativeCallbacks.expected_counts(2, (0, 1, 0))


def test_native_complete_record_keeps_final_writer(native_wifi: _NativeRun) -> None:
    """Preserve complete records through the real final exporter and CSV writer."""
    native_wifi.transport.replies = deque([_Reply(200, b'{"results":[{"mac":"aa","hostname":"client-1"}]}'), _Reply()])
    SiteClientExporter.wifi_clients()
    outputs = list(Path("data").glob("SiteWiFiClients*"))
    assert len(outputs) == 1
    with outputs[0].open(encoding="utf-8") as output:
        rows = list(csv.DictReader(output))
    assert rows == [
        {
            "mac": "aa",
            "hostname": "client-1",
            "site_id": "controlled-site",
            "site_name": "Lab Site",
            "data_source": "client",
            "session_count": "0",
        }
    ]
    assert native_wifi.callbacks["export"].call_args.args[1] == "SiteWiFiClients.CSV"
    assert native_wifi.callbacks["export"].call_args.kwargs == {"api_function_name": "listSiteWirelessClientsStats"}
    assert native_wifi.measure() == _NativeCallbacks.expected_counts(2, (1, 1, 1))
    print(f"Unchanged legacy filename observed={outputs[0].name}")


@pytest.mark.parametrize(("endpoint_name", "later_page"), [("clients", True), ("sessions", False), ("sessions", True)])
@pytest.mark.parametrize("status_code", [403, 503])
@pytest.mark.usefixtures("output_backend")
def test_native_other_http_failures_stop_complete_output(
    native_wifi: _NativeRun, caplog: pytest.LogCaptureFixture, endpoint_name: str, later_page: bool, status_code: int
) -> None:
    """Reject both endpoints' refused pages even when the error body has results."""
    reply = _Reply(status_code, b'{"detail":"controlled refusal","results":[]}')
    native_wifi.transport.replies = _FailurePages.create(reply, endpoint_name, later_page)
    with caplog.at_level(logging.DEBUG):
        SiteClientExporter.wifi_clients()
    native_wifi.require_failure(caplog, endpoint_name, later_page)
    assert native_wifi.responses[-1].status_code == status_code
    assert f"HTTP {status_code}" in caplog.text
    if later_page:
        assert native_wifi.transport.urls[-1].endswith("search?cursor=kept&limit=1000")


@pytest.mark.parametrize(("endpoint_name", "later_page"), [("clients", True), ("sessions", False), ("sessions", True)])
@pytest.mark.parametrize("body", [b"", b'{"results":'])
def test_native_other_parse_failures_stop_complete_output(
    native_wifi: _NativeRun, caplog: pytest.LogCaptureFixture, endpoint_name: str, later_page: bool, body: bytes
) -> None:
    """Reject empty and malformed first or later session and client bodies."""
    native_wifi.transport.replies = _FailurePages.create(_Reply(200, body), endpoint_name, later_page)
    with caplog.at_level(logging.DEBUG):
        SiteClientExporter.wifi_clients()
    native_wifi.require_failure(caplog, endpoint_name, later_page)
    assert native_wifi.responses[-1].status_code == 200
    assert native_wifi.responses[-1].data == {}
    assert "HTTP 200" in caplog.text


@pytest.mark.parametrize("endpoint_name", ["clients", "sessions"])
@pytest.mark.parametrize("later_page", [False, True])
@pytest.mark.parametrize("status_code", [None, "200", True])
def test_native_invalid_status_cannot_default_to_success(
    native_wifi: _NativeRun, caplog: pytest.LogCaptureFixture, endpoint_name: str, later_page: bool, status_code: object
) -> None:
    """Reject actual native responses with unavailable or invalid statuses."""
    native_wifi.transport.replies = _FailurePages.create(_Reply(status_code), endpoint_name, later_page)
    with caplog.at_level(logging.DEBUG):
        SiteClientExporter.wifi_clients()
    native_wifi.require_failure(caplog, endpoint_name, later_page)
    assert native_wifi.responses[-1].status_code == status_code
    assert "HTTP unavailable" in caplog.text


@pytest.mark.parametrize("endpoint_name", ["clients", "sessions"])
@pytest.mark.parametrize("later_page", [False, True])
@pytest.mark.parametrize(
    "body",
    [
        b"{}",
        b'{"results":null}',
        b'{"results":[1]}',
        b'{"results":[{"mac":"valid"},null]}',
        b'{"error":"PRIVATE_BODY_VALUE","results":[]}',
        b"null",
    ],
)
def test_native_malformed_successful_shapes_stop_output(
    native_wifi: _NativeRun, caplog: pytest.LogCaptureFixture, endpoint_name: str, later_page: bool, body: bytes
) -> None:
    """Reject invalid successful shapes without writing a partial record list."""
    native_wifi.transport.replies = _FailurePages.create(_Reply(200, body), endpoint_name, later_page)
    with caplog.at_level(logging.DEBUG):
        SiteClientExporter.wifi_clients()
    native_wifi.require_failure(caplog, endpoint_name, later_page)
    notices = "\n".join(
        record.getMessage() for record in caplog.records if record.name.endswith("wifi_clients_exporter")
    )
    assert "HTTP 200" in notices
    assert "PRIVATE_BODY_VALUE" not in notices


@pytest.mark.parametrize("endpoint_name", ["clients", "sessions"])
@pytest.mark.parametrize("later_page", [False, True])
@pytest.mark.parametrize(
    "fault", [requests.Timeout("controlled timeout"), requests.ConnectionError("controlled connection")]
)
def test_native_transport_failure_cannot_become_empty_data(
    native_wifi: _NativeRun,
    caplog: pytest.LogCaptureFixture,
    endpoint_name: str,
    later_page: bool,
    fault: requests.RequestException,
) -> None:
    """Reject the native no-response object after real controlled transport errors."""
    native_wifi.transport.replies = _FailurePages.create(_Reply(error=fault), endpoint_name, later_page)
    with caplog.at_level(logging.DEBUG):
        SiteClientExporter.wifi_clients()
    native_wifi.require_failure(caplog, endpoint_name, later_page)
    assert native_wifi.responses[-1].status_code is None
    assert native_wifi.responses[-1].data == {}
    assert "HTTP unavailable" in caplog.text


def test_native_list_empty_preserves_the_placeholder(native_wifi: _NativeRun) -> None:
    """Preserve valid empty list bodies as well as valid empty search bodies."""
    native_wifi.transport.replies = deque([_Reply(200, b"[]"), _Reply(200, b"[]")])
    SiteClientExporter.wifi_clients()
    with Path("data", "SiteWiFiClients.CSV").open(encoding="utf-8") as output:
        assert list(csv.DictReader(output)) == [
            {
                "site_id": "controlled-site",
                "site_name": "Lab Site",
                "message": "No WiFi clients or sessions found",
            }
        ]
    counts = native_wifi.measure()
    assert counts["csv"] == 1
    assert counts["sdk"] == counts["transport"] == 2
    assert counts["export"] == counts["router"] == counts["sqlite"] == counts["live_http"] == counts["socket"] == 0


def test_native_empty_linked_page_does_not_end_the_read(native_wifi: _NativeRun) -> None:
    """Follow a native next link even when the current page is empty."""
    link = "/api/v1/sites/controlled-site/clients/search?cursor=kept"
    first = json.dumps({"results": [], "next": link}).encode()
    native_wifi.transport.replies = deque([_Reply(200, first), _Reply(200, b'[{"mac":"later-client"}]'), _Reply()])
    SiteClientExporter.wifi_clients()
    rows = native_wifi.callbacks["export"].call_args.args[0]
    assert rows == [
        {
            "mac": "later-client",
            "site_id": "controlled-site",
            "site_name": "Lab Site",
            "data_source": "client",
            "session_count": 0,
        }
    ]
    assert native_wifi.transport.urls[1] == f"https://api.mist.com{link}"
    counts = native_wifi.measure()
    assert counts["sdk"] == counts["transport"] == 3
    assert counts["export"] == counts["csv"] == counts["router"] == 1
    assert counts["sqlite"] == counts["live_http"] == counts["socket"] == 0


def test_native_full_page_order_and_session_merge(native_wifi: _NativeRun) -> None:
    """Preserve header links, search links, complete fields, and session precedence."""
    native_wifi.transport.replies = _MergedCase.replies()
    SiteClientExporter.wifi_clients()
    records = native_wifi.callbacks["export"].call_args.args[0]
    assert records == _MergedCase.EXPECTED
    assert native_wifi.callbacks["router"].call_args.args == (records, "listSiteWirelessClientsStats")
    assert native_wifi.transport.urls == _MergedCase.URLS
    outputs = list(Path("data").glob("SiteWiFiClients*"))
    assert len(outputs) == 1
    with outputs[0].open(encoding="utf-8") as output:
        csv_records = list(csv.DictReader(output))
    assert csv_records == [{key: str(record.get(key, "")) for key in csv_records[0]} for record in records]
    assert native_wifi.measure() == _NativeCallbacks.expected_counts(4, (1, 1, 1))


@pytest.mark.parametrize("status_code", [403, 503])
@pytest.mark.usefixtures("output_backend")
def test_native_refusal_precedes_a_valid_result_shape(
    native_wifi: _NativeRun, caplog: pytest.LogCaptureFixture, status_code: int
) -> None:
    """Reject a refused first page even when its body contains a valid results list."""
    native_wifi.transport.replies = deque([_Reply(status_code, b'{"results":[]}'), _Reply()])
    with caplog.at_level(logging.DEBUG):
        SiteClientExporter.wifi_clients()
    native_wifi.require_failure(caplog, "clients", False)
    assert native_wifi.responses[0].data == {"results": []}
    assert f"HTTP {status_code}" in caplog.text


def test_native_repeated_next_link_cannot_publish_partial_records(
    native_wifi: _NativeRun, caplog: pytest.LogCaptureFixture
) -> None:
    """Stop a repeated native link without exporting already accepted rows."""
    link = "/api/v1/sites/controlled-site/clients/search?cursor=repeated"
    body = json.dumps({"results": [{"mac": "early-client"}], "next": link}).encode()
    native_wifi.transport.replies = deque([_Reply(200, body), _Reply(200, body), _Reply()])
    with caplog.at_level(logging.DEBUG):
        SiteClientExporter.wifi_clients()
    native_wifi.require_failure(caplog, "clients", True)
    assert native_wifi.transport.urls[-1] == f"https://api.mist.com{link}"
    assert "next-page link is invalid or repeated" in caplog.text


def test_native_large_page_retains_every_record(native_wifi: _NativeRun) -> None:
    """Retain complete records without adding an artificial page-size cutoff."""
    clients = [{"mac": f"client-{index}", "hostname": "Caf\u00e9"} for index in range(1001)]
    native_wifi.transport.replies = deque([_Reply(200, json.dumps({"results": clients}).encode()), _Reply()])
    SiteClientExporter.wifi_clients()
    records = native_wifi.callbacks["export"].call_args.args[0]
    assert len(records) == 1001
    assert [row["mac"] for row in records] == [row["mac"] for row in clients]
    assert all(row["site_id"] == "controlled-site" and row["site_name"] == "Lab Site" for row in records)
    assert all(row["hostname"] == "Caf\u00e9" and row["session_count"] == 0 for row in records)
    counts = native_wifi.measure()
    assert counts["sdk"] == counts["transport"] == 2
    assert counts["export"] == counts["csv"] == counts["router"] == 1
    assert counts["sqlite"] == counts["live_http"] == counts["socket"] == 0
