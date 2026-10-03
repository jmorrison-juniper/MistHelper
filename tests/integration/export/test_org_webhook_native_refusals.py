"""Verify webhook refusals through native SDK transport and real CSV output."""

from __future__ import annotations

import csv
import json
import logging
import sys
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from types import FrameType
from typing import Any
from unittest.mock import MagicMock

import mistapi
import pytest
import requests
from mistapi.__api_response import APIResponse
from mistapi.__logger import console as sdk_console
from requests.adapters import BaseAdapter
from requests.exceptions import ConnectionError, Timeout

from src.export.org_webhook_deliveries_exporter import OrgWebhookDeliveriesExporter
from src.refactors.main_entrypoint import AppContext, MainEntrypoint


class NativeWebhookTransport(BaseAdapter):
    """Supply controlled native responses without an external HTTP operation."""

    @dataclass
    class Page:
        """Store one controlled wire response without an I/O operation."""

        status_code: object = 200
        body: bytes = b"[]"
        headers: dict[str, str] = field(default_factory=dict)
        fault: Exception | None = None

    def __init__(self) -> None:
        """Retain only the native sessions and responses that this fixture owns."""
        self.pages: list[NativeWebhookTransport.Page] = []
        self.paths: list[str] = []
        self.responses: list[requests.Response] = []
        self.sessions: list[requests.Session] = []
        self.session_factory = requests.session

    def create_session(self) -> requests.Session:
        """Retain the superclass session that the SDK otherwise replaces."""
        session = self.session_factory()
        session.trust_env = False  # Prevent host proxy settings from reaching the controlled request.
        self.sessions.append(session)
        return session

    def send(self, request: requests.PreparedRequest, *args: object, **kwargs: object) -> requests.Response:
        """Return an actual Requests response for the next expected native call."""
        if not request.url or not request.url.startswith("https://api.mist.com/api/v1/orgs/"):
            raise RuntimeError("The native fixture received an unexpected host or resource.")
        self.paths.append(request.path_url)
        if not self.pages:
            raise RuntimeError("The native fixture has no response for this request.")
        page = self.pages.pop(0)
        if page.fault is not None:
            raise page.fault
        response = requests.Response()
        vars(response)["status_code"] = page.status_code  # Deliberately test values outside the native status type.
        response._content = page.body
        response.raw = BytesIO(page.body)
        response.encoding = "utf-8"
        response.headers.update(page.headers)
        response.url = request.url
        response.request = request
        self.responses.append(response)
        return response

    def close(self) -> None:
        """Close the actual response streams with the SDK session."""
        for response in self.responses:
            response.close()
            response.raw.close()  # The controlled in-memory stream has no urllib3 connection-release method.


class NativeWebhookProbe:
    """Measure real exporter calls and isolate every external boundary."""

    org_id = "00000000-0000-4000-8000-000000000001"
    webhook_id = "00000000-0000-4000-8000-000000000002"
    module = "src.export.org_webhook_deliveries_exporter"

    class Calls:
        """Observe native call and return events without replacing source results."""

        targets = {
            ("org_webhook_deliveries_exporter.py", "deliveries"): "deliveries",
            ("org_webhook_deliveries_exporter.py", "_select_webhook_id"): "selector",
            ("org_webhook_deliveries_exporter.py", "_persist"): "persist",
            ("webhooks.py", "searchOrgWebhooksDeliveries"): "search",
            ("webhooks.py", "listOrgWebhooks"): "list",
            ("__api_request.py", "mist_get"): "mist_get",
            ("__pagination.py", "get_all"): "get_all",
            ("__pagination.py", "get_next"): "get_next",
            ("data_exporter.py", "write_with_format_selection"): "output",
            ("data_exporter.py", "write_to_csv"): "csv",
            ("data_exporter.py", "_route_to_polyglot"): "polyglot",
            ("data_exporter.py", "_build_polyglot_router"): "router",
            ("data_exporter.py", "_write_sqlite_format"): "sqlite_writer",
            ("data_exporter.py", "_perform_polyglot_write"): "database_write",
        }

        def __init__(self) -> None:
            """Start measured counts without an assumed response or output result."""
            self.counts = dict.fromkeys(self.targets.values(), 0)
            self.results: dict[str, list[Any]] = {}
            self.arguments: dict[str, list[dict[str, Any]]] = {}
            self.native_responses: list[APIResponse] = []
            self.closed_sessions: set[int] = set()
            self.closed_responses: set[int] = set()

        def trace(self, frame: FrameType, event: str, value: Any) -> None:
            """Retain measured native and output boundaries from the actual stack."""
            filename, name = Path(frame.f_code.co_filename).name, frame.f_code.co_name
            key = self.targets.get((filename, name))
            if key and event == "call":
                self.counts[key] += 1
                self.arguments.setdefault(key, []).append(dict(frame.f_locals))
            if key and event == "return":
                self.results.setdefault(key, []).append(value)
            if event == "return" and filename == "__api_response.py" and name == "__init__":
                self.native_responses.append(frame.f_locals["self"])
            if event == "call" and name == "close":
                if filename == "sessions.py":
                    self.closed_sessions.add(id(frame.f_locals["self"]))
                elif filename == "models.py":
                    self.closed_responses.add(id(frame.f_locals["self"]))

        def summary(self, records: list[logging.LogRecord], guards: dict[str, int], paths: list[str]) -> dict[str, Any]:
            """Return source-free counts and native response identity for private evidence."""
            return {
                "calls": self.counts,
                "native_statuses": [response.status_code for response in self.native_responses],
                "native_response_types": [
                    type(response).__module__ + "." + type(response).__qualname__ for response in self.native_responses
                ],
                "persist_rows": [len(arguments["rawdata"]) for arguments in self.arguments.get("persist", [])],
                "output_results": self.results.get("output", []),
                "polyglot_outcomes": [
                    {"written": result.written, "skip_reason": result.skip_reason}
                    for result in self.results.get("polyglot", [])
                ],
                "sessions_closed": len(self.closed_sessions),
                "responses_closed": len(self.closed_responses),
                "live_boundary_attempts": guards,
                "native_paths": paths,
                "exporter_error_records": sum(
                    record.name == NativeWebhookProbe.module and record.levelno >= logging.ERROR for record in records
                ),
                "sdk_error_records": sum(
                    record.name == "mistapi" and record.levelno >= logging.ERROR for record in records
                ),
            }

    def __init__(self, root: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        """Prepare an owned temporary output root and a real SDK session."""
        self.root, self.monkeypatch, self.caplog = root, monkeypatch, caplog
        self.transport, self.calls = NativeWebhookTransport(), self.Calls()
        self.guards: dict[str, MagicMock] = {}
        self.isolate()
        self.session = mistapi.APISession(host="api.mist.com", console_log_level=0, logging_log_level=10)
        self.session._session.mount("https://api.mist.com/", self.transport)
        context = AppContext(apisession=self.session, org_id=self.org_id, output_format="csv")
        monkeypatch.setattr(MainEntrypoint, "context", context)
        caplog.set_level(logging.INFO)
        sys.setprofile(self.calls.trace)

    def isolate(self) -> None:
        """Replace live boundaries, not SDK operations, pagination, or output."""
        self.monkeypatch.chdir(self.root)
        names: tuple[str, ...] = ("MIST_HOST", "MIST_APITOKEN", "MIST_USER", "MIST_PASSWORD")
        names += ("CONSOLE_LOG_LEVEL", "LOGGING_LOG_LEVEL")
        for name in names:
            self.monkeypatch.setenv(name, "")
        self.monkeypatch.setenv("org_id", self.org_id)  # The real pytest resolver uses the controlled operator context.
        self.monkeypatch.setenv("MISTHELPER_STANDALONE", "true")
        self.monkeypatch.setattr(sdk_console, "level", sdk_console.level)
        sdk_logger = logging.getLogger("mistapi")
        self.monkeypatch.setattr(sdk_logger, "level", sdk_logger.level)
        self.monkeypatch.setattr(requests, "session", self.transport.create_session)
        for target in (
            "requests.adapters.HTTPAdapter.send",
            "socket.getaddrinfo",
            "socket.create_connection",
            "socket.socket.connect",
            "sqlite3.connect",
        ):
            guard = MagicMock(side_effect=RuntimeError("The native test attempted a forbidden external boundary."))
            self.monkeypatch.setattr(target, guard)
            self.guards[target] = guard

    def choose_delivery(self) -> None:
        """Supply only the controlled operator selection for delivery-specific tests."""
        choice = MagicMock(return_value=(self.webhook_id, "Probe Hook"))
        self.monkeypatch.setattr(OrgWebhookDeliveriesExporter, "_select_webhook_id", choice)

    def close(self) -> None:
        """Close native resources and require zero external operation attempts."""
        for session in self.transport.sessions:
            session.close()
        sys.setprofile(None)
        assert self.calls.closed_sessions == {id(session) for session in self.transport.sessions}
        assert self.calls.closed_responses == {id(response) for response in self.transport.responses}
        assert all(response.raw.closed for response in self.transport.responses)
        assert {name: guard.call_count for name, guard in self.guards.items()} == dict.fromkeys(self.guards, 0)
        assert self.calls.counts["router"] == 0
        assert self.calls.counts["sqlite_writer"] == 0
        assert self.calls.counts["database_write"] == 0
        guards = {name: guard.call_count for name, guard in self.guards.items()}
        evidence = self.calls.summary(self.caplog.get_records("call"), guards, self.transport.paths)
        print("native_evidence=" + json.dumps(evidence, sort_keys=True))


@pytest.fixture
def native_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> Iterator[NativeWebhookProbe]:
    """Remove each owned temporary directory after closing its native resources."""
    with tempfile.TemporaryDirectory(prefix="issue3745-native-", dir=tmp_path) as directory:
        probe = NativeWebhookProbe(Path(directory), monkeypatch, caplog)
        try:
            yield probe
        finally:
            probe.close()
            monkeypatch.chdir(tmp_path)
    assert not Path(directory).exists()
    print("native_cleanup=temporary_directory_removed")


class TestNativeDeliveryRefusals:
    """Require actual exporter refusals before persistence or partial output."""

    @pytest.mark.parametrize("status_code", [401, 403, 404, 503])
    def test_first_http_refusal(self, native_probe: NativeWebhookProbe, status_code: int) -> None:
        """Reject each native first-page status with an exporter-owned failure signal."""
        native_probe.choose_delivery()
        native_probe.transport.pages.append(
            NativeWebhookTransport.Page(status_code=status_code, body=b'{"detail":"private-response-sentinel"}')
        )
        OrgWebhookDeliveriesExporter.deliveries()
        errors = [record for record in native_probe.caplog.records if record.name == native_probe.module]
        assert any(
            record.levelno == logging.ERROR and f"HTTP {status_code}" in record.getMessage() for record in errors
        )
        assert native_probe.calls.counts["persist"] == 0
        assert native_probe.calls.counts["output"] == 0
        assert native_probe.calls.counts["csv"] == 0
        assert native_probe.calls.counts["polyglot"] == 0
        assert native_probe.calls.counts["search"] == 1
        assert native_probe.calls.counts["mist_get"] == 1
        assert [response.status_code for response in native_probe.calls.native_responses] == [status_code]
        assert all("private-response-sentinel" not in record.getMessage() for record in errors)
        assert "No organization webhook delivery data found" not in native_probe.caplog.text
        assert "records exported" not in native_probe.caplog.text
        assert list(native_probe.root.rglob("*.csv")) == []

    @pytest.mark.parametrize("status_code", [401, 403, 404, 503])
    @pytest.mark.parametrize("shape", ["results", "list"])
    def test_later_http_refusal(self, native_probe: NativeWebhookProbe, status_code: int, shape: str) -> None:
        """Reject a later native refusal without exporting the accepted first-page record."""
        native_probe.choose_delivery()
        path = f"/api/v1/orgs/{native_probe.org_id}/webhooks/{native_probe.webhook_id}/events/search"
        first = [{"id": "delivery-1", "webhook_id": native_probe.webhook_id, "timestamp": 1700000000}]
        body = {"results": first, "next": path + "?search_after=second"} if shape == "results" else first
        headers = {} if shape == "results" else {"X-Page-Total": "2", "X-Page-Limit": "1", "X-Page-Page": "1"}
        native_probe.transport.pages.extend(
            [
                NativeWebhookTransport.Page(body=json.dumps(body).encode(), headers=headers),
                NativeWebhookTransport.Page(status_code=status_code, body=b'{"detail":"private-response-sentinel"}'),
            ]
        )
        OrgWebhookDeliveriesExporter.deliveries()
        expected_next = path + ("?search_after=second" if shape == "results" else "?page=2")
        assert native_probe.transport.paths == [path, expected_next]
        assert native_probe.calls.counts["get_next"] == 1
        assert native_probe.calls.counts["persist"] == 0
        assert native_probe.calls.counts["output"] == 0
        assert list(native_probe.root.rglob("*.csv")) == []
        errors = [record.getMessage() for record in native_probe.caplog.records if record.name == native_probe.module]
        assert any(f"HTTP {status_code}" in message and "page=2" in message for message in errors)
        assert all("private-response-sentinel" not in message for message in errors)
        assert "records exported" not in native_probe.caplog.text

    @pytest.mark.parametrize("body", [b"", b"bad json", b"{", b"null", b"{}", b'{"results":{}}', b'{"results":[null]}'])
    @pytest.mark.parametrize("failure_page", [1, 2])
    def test_unusable_native_body(self, native_probe: NativeWebhookProbe, body: bytes, failure_page: int) -> None:
        """Reject actual empty or malformed native bodies on the first and later pages."""
        native_probe.choose_delivery()
        path = f"/api/v1/orgs/{native_probe.org_id}/webhooks/{native_probe.webhook_id}/events/search"
        if failure_page == 2:
            first = {"results": [{"id": "delivery-1"}], "next": path + "?search_after=second"}
            native_probe.transport.pages.append(NativeWebhookTransport.Page(body=json.dumps(first).encode()))
        native_probe.transport.pages.append(NativeWebhookTransport.Page(body=body))
        OrgWebhookDeliveriesExporter.deliveries()
        errors = [record for record in native_probe.caplog.records if record.name == native_probe.module]
        assert any(
            record.levelno == logging.ERROR and f"page={failure_page}" in record.getMessage() for record in errors
        )
        assert native_probe.calls.counts["mist_get"] == failure_page
        assert native_probe.calls.counts["persist"] == 0
        assert native_probe.calls.counts["output"] == 0
        assert list(native_probe.root.rglob("*.csv")) == []
        assert "No organization webhook delivery data found" not in native_probe.caplog.text

    @pytest.mark.parametrize(
        "fault", [Timeout("private-transport-sentinel"), ConnectionError("private-transport-sentinel")]
    )
    @pytest.mark.parametrize("failure_page", [1, 2])
    def test_native_transport_failure(
        self, native_probe: NativeWebhookProbe, fault: Exception, failure_page: int
    ) -> None:
        """Reject the actual SDK response with unavailable status after a native transport failure."""
        native_probe.choose_delivery()
        path = f"/api/v1/orgs/{native_probe.org_id}/webhooks/{native_probe.webhook_id}/events/search"
        if failure_page == 2:
            body = {"results": [{"id": "delivery-1"}], "next": path + "?search_after=second"}
            native_probe.transport.pages.append(NativeWebhookTransport.Page(body=json.dumps(body).encode()))
        native_probe.transport.pages.append(NativeWebhookTransport.Page(fault=fault))
        OrgWebhookDeliveriesExporter.deliveries()
        assert native_probe.calls.native_responses[-1].status_code is None
        assert native_probe.calls.native_responses[-1].proxy_error is False
        errors = [record for record in native_probe.caplog.records if record.name == native_probe.module]
        assert any(
            record.levelno == logging.ERROR and f"page={failure_page}" in record.getMessage() for record in errors
        )
        assert all("private-transport-sentinel" not in record.getMessage() for record in errors)
        assert native_probe.calls.counts["persist"] == 0
        assert native_probe.calls.counts["output"] == 0
        assert list(native_probe.root.rglob("*.csv")) == []

    @pytest.mark.parametrize("status_code", [None, "200", True, 200.0, 0, 600])
    @pytest.mark.parametrize("failure_page", [1, 2])
    def test_unreliable_native_status(
        self, native_probe: NativeWebhookProbe, status_code: object, failure_page: int
    ) -> None:
        """Reject malformed status values carried by actual native response objects."""
        native_probe.choose_delivery()
        path = f"/api/v1/orgs/{native_probe.org_id}/webhooks/{native_probe.webhook_id}/events/search"
        if failure_page == 2:
            body = {"results": [{"id": "delivery-1"}], "next": path + "?search_after=second"}
            native_probe.transport.pages.append(NativeWebhookTransport.Page(body=json.dumps(body).encode()))
        native_probe.transport.pages.append(
            NativeWebhookTransport.Page(status_code=status_code, body=b'{"results":[{"id":"delivery-2"}]}')
        )
        OrgWebhookDeliveriesExporter.deliveries()
        assert native_probe.calls.native_responses[-1].status_code == status_code
        errors = [record for record in native_probe.caplog.records if record.name == native_probe.module]
        assert any(
            record.levelno == logging.ERROR and f"page={failure_page}" in record.getMessage() for record in errors
        )
        assert native_probe.calls.counts["persist"] == 0
        assert native_probe.calls.counts["output"] == 0
        assert list(native_probe.root.rglob("*.csv")) == []


class TestNativeWebhookSuccessAndDiscovery:
    """Preserve real successful output and verify the separate native selector boundary."""

    class SuccessfulCases:
        """Arrange native page data and inspect actual successful output."""

        @staticmethod
        def delivery_row(probe: NativeWebhookProbe, number: int) -> dict[str, Any]:
            """Keep destination failures and nested values in the successful cloud control."""
            return {
                "id": f"delivery-{number + 1}",
                "webhook_id": probe.webhook_id,
                "timestamp": 1700000000 + number,
                "status_code": 503,
                "status": "failure",
                "details": {"message": "line one\nline two"},
            }

        @classmethod
        def delivery_pages(cls, probe: NativeWebhookProbe, shape: str, count: int) -> list[dict[str, Any]]:
            """Arrange successful SDK pages without a paginator or output replacement."""
            path = f"/api/v1/orgs/{probe.org_id}/webhooks/{probe.webhook_id}/events/search"
            expected: list[dict[str, Any]] = []
            for number in range(max(count, 1)):
                rows = [cls.delivery_row(probe, number)] if count else []
                expected.extend(rows)
                next_link = path + f"?search_after=page-{number + 2}" if number + 1 < count else None
                body = {"results": rows, "next": next_link} if shape == "results" else rows
                headers = (
                    {"X-Page-Total": str(count), "X-Page-Limit": "1", "X-Page-Page": str(number + 1)}
                    if shape == "list"
                    else {}
                )
                probe.transport.pages.append(
                    NativeWebhookTransport.Page(body=json.dumps(body).encode(), headers=headers)
                )
            return expected

        @staticmethod
        def verify_csv(probe: NativeWebhookProbe, count: int) -> None:
            """Inspect exact real output and the truthful standalone database outcome."""
            filename = "OrgWebhookDeliveries_Probe_Hook.csv"
            arguments = probe.calls.arguments["output"][0]
            assert arguments["filename_or_table"] == filename
            assert arguments["api_function_name"] == "searchOrgWebhooksDeliveries"
            assert probe.calls.results["output"] == [True]
            assert probe.calls.counts["csv"] == 1 and probe.calls.counts["polyglot"] == 1
            outcome = probe.calls.results["polyglot"][0]
            assert (outcome.written, outcome.skip_reason) == (False, "standalone_mode")
            with (probe.root / "data" / filename).open(encoding="utf-8", newline="") as stream:
                actual = list(csv.DictReader(stream))
            expected = [
                {
                    "details_message": "line one\\nline two",
                    "id": f"delivery-{number + 1}",
                    "status": "failure",
                    "status_code": "503",
                    "timestamp": str(1700000000 + number),
                    "webhook_id": probe.webhook_id,
                }
                for number in range(count)
            ]
            assert actual == expected
            assert "standalone_mode" in probe.caplog.text and "The database write was dropped" in probe.caplog.text

        @staticmethod
        def discovery_pages(probe: NativeWebhookProbe, count: int, total: int | None = None) -> None:
            """Arrange only real discovery wire pages with native header links."""
            for number in range(max(count, 1)):
                row = {"id": f"00000000-0000-4000-8000-{number + 2:012d}", "name": f"Probe Hook {number + 1}"}
                headers = {
                    "X-Page-Total": str(count if total is None else total),
                    "X-Page-Limit": "1",
                    "X-Page-Page": str(number + 1),
                }
                body = json.dumps([row] if count else []).encode()
                probe.transport.pages.append(NativeWebhookTransport.Page(body=body, headers=headers))

        @staticmethod
        def verify_selected_csv(probe: NativeWebhookProbe, count: int, selected_id: str) -> None:
            """Inspect the output of the actual native discovery and delivery journey."""
            filename = f"OrgWebhookDeliveries_Probe_Hook_{count}.csv"
            assert probe.transport.paths[-1] == f"/api/v1/orgs/{probe.org_id}/webhooks/{selected_id}/events/search"
            with (probe.root / "data" / filename).open(encoding="utf-8", newline="") as stream:
                assert list(csv.DictReader(stream)) == [
                    {"id": "selected-delivery", "timestamp": "1700000000", "webhook_id": selected_id}
                ]

    class TestDeliveryOutput:
        """Verify successful data and statuses that would otherwise permit false output."""

        @pytest.mark.parametrize("shape", ["results", "list"])
        @pytest.mark.parametrize("page_count", [0, 1, 3])
        def test_successful_output(self, native_probe: NativeWebhookProbe, shape: str, page_count: int) -> None:
            """Retain exact row values, native order, output metadata, and valid-empty behavior."""
            native_probe.choose_delivery()
            cases = TestNativeWebhookSuccessAndDiscovery.SuccessfulCases
            expected = cases.delivery_pages(native_probe, shape, page_count)
            OrgWebhookDeliveriesExporter.deliveries()
            assert native_probe.calls.arguments["persist"][0]["rawdata"] == expected
            assert native_probe.calls.counts["mist_get"] == max(page_count, 1)
            assert native_probe.calls.counts["get_next"] == max(page_count - 1, 0)
            if page_count == 0:
                assert native_probe.calls.counts["output"] == 0
                assert list(native_probe.root.rglob("*.csv")) == []
                assert "No organization webhook delivery data found" in native_probe.caplog.text
                return
            cases.verify_csv(native_probe, page_count)

        @pytest.mark.parametrize("status_code", [403, 503])
        @pytest.mark.parametrize("failure_page", [1, 2])
        @pytest.mark.parametrize("shape", ["results", "list"])
        def test_refusal_with_record_arrays(
            self, native_probe: NativeWebhookProbe, status_code: int, failure_page: int, shape: str
        ) -> None:
            """Refuse failed native statuses even when the body could produce normal successful output."""
            native_probe.choose_delivery()
            path = f"/api/v1/orgs/{native_probe.org_id}/webhooks/{native_probe.webhook_id}/events/search"
            if failure_page == 2:
                first = {"results": [{"id": "delivery-1"}], "next": path + "?search_after=second"}
                native_probe.transport.pages.append(NativeWebhookTransport.Page(body=json.dumps(first).encode()))
            rows = [{"id": "refused-record", "webhook_id": native_probe.webhook_id, "timestamp": 1700000000}]
            body = {"results": rows, "next": None} if shape == "results" else rows
            native_probe.transport.pages.append(
                NativeWebhookTransport.Page(status_code=status_code, body=json.dumps(body).encode())
            )
            OrgWebhookDeliveriesExporter.deliveries()
            assert native_probe.calls.counts["persist"] == 0 and native_probe.calls.counts["output"] == 0
            assert native_probe.calls.counts["csv"] == 0 and native_probe.calls.counts["polyglot"] == 0
            assert list(native_probe.root.rglob("*.csv")) == []
            errors = [record for record in native_probe.caplog.records if record.name == native_probe.module]
            assert any(
                record.levelno == logging.ERROR and f"HTTP {status_code}" in record.getMessage() for record in errors
            )
            assert "records exported" not in native_probe.caplog.text

    class TestDiscovery:
        """Verify native selector failures and the complete successful selection journey."""

        @pytest.mark.parametrize("status_code", [401, 403, 404, 503])
        @pytest.mark.parametrize("failure_page", [1, 2])
        def test_native_discovery_refusal(
            self, native_probe: NativeWebhookProbe, status_code: int, failure_page: int
        ) -> None:
            """Refuse actual discovery before a selection prompt or a configured-empty notice."""
            path = f"/api/v1/orgs/{native_probe.org_id}/webhooks"
            prompt = MagicMock(return_value="1")
            native_probe.monkeypatch.setattr("builtins.input", prompt)
            if failure_page == 2:
                TestNativeWebhookSuccessAndDiscovery.SuccessfulCases.discovery_pages(native_probe, 1, total=2)
            native_probe.transport.pages.append(
                NativeWebhookTransport.Page(status_code=status_code, body=b'{"detail":"private-discovery-sentinel"}')
            )
            result = OrgWebhookDeliveriesExporter._select_webhook_id(native_probe.org_id)
            assert result is None and prompt.call_count == 0
            assert native_probe.calls.counts["list"] == 1 and native_probe.calls.counts["mist_get"] == failure_page
            assert native_probe.calls.counts["search"] == 0 and native_probe.calls.counts["persist"] == 0
            assert native_probe.transport.paths == [path] + ([path + "?page=2"] if failure_page == 2 else [])
            errors = [
                record.getMessage() for record in native_probe.caplog.records if record.name == native_probe.module
            ]
            assert any(f"HTTP {status_code}" in message and f"page={failure_page}" in message for message in errors)
            assert all("private-discovery-sentinel" not in message for message in errors)
            assert "No webhooks configured" not in native_probe.caplog.text

        @pytest.mark.parametrize("page_count", [0, 1, 2])
        def test_successful_native_discovery(self, native_probe: NativeWebhookProbe, page_count: int) -> None:
            """Retain discovery order, the operator choice, and actual selected delivery output."""
            cases = TestNativeWebhookSuccessAndDiscovery.SuccessfulCases
            prompt = MagicMock(return_value=str(max(page_count, 1)))
            native_probe.monkeypatch.setattr("builtins.input", prompt)
            cases.discovery_pages(native_probe, page_count)
            selected_id = f"00000000-0000-4000-8000-{page_count + 1:012d}"
            if page_count:
                delivery = {"id": "selected-delivery", "webhook_id": selected_id, "timestamp": 1700000000}
                native_probe.transport.pages.append(
                    NativeWebhookTransport.Page(body=json.dumps({"results": [delivery], "next": None}).encode())
                )
            OrgWebhookDeliveriesExporter.deliveries()
            result = native_probe.calls.results["selector"][0]
            if page_count == 0:
                assert result is None and prompt.call_count == 0
                assert "No webhooks configured" in native_probe.caplog.text
            else:
                assert result == (selected_id, f"Probe Hook {page_count}")
                assert prompt.call_args.args == ("Select webhook number: ",)
                assert native_probe.calls.counts["get_next"] == page_count - 1
                cases.verify_selected_csv(native_probe, page_count, selected_id)
            assert native_probe.calls.counts["list"] == 1
            assert native_probe.calls.counts["search"] == int(page_count > 0)
            assert native_probe.calls.counts["output"] == int(page_count > 0)

        @pytest.mark.parametrize(
            ("status_code", "body"),
            [
                (200, b""),
                (200, b"bad json"),
                (200, b'{"results":[null]}'),
                (200, b'{"results":[],"next":false}'),
                (None, b"[]"),
            ],
        )
        @pytest.mark.parametrize("failure_page", [1, 2])
        def test_discovery_unusable_native_page(
            self, native_probe: NativeWebhookProbe, status_code: object, body: bytes, failure_page: int
        ) -> None:
            """Refuse unreadable discovery pages before a normal empty notice or prompt."""
            prompt = MagicMock(return_value="1")
            native_probe.monkeypatch.setattr("builtins.input", prompt)
            if failure_page == 2:
                TestNativeWebhookSuccessAndDiscovery.SuccessfulCases.discovery_pages(native_probe, 1, total=2)
            native_probe.transport.pages.append(NativeWebhookTransport.Page(status_code=status_code, body=body))
            result = OrgWebhookDeliveriesExporter._select_webhook_id(native_probe.org_id)
            assert result is None and prompt.call_count == 0
            assert native_probe.calls.counts["mist_get"] == failure_page
            assert native_probe.calls.counts["persist"] == 0 and native_probe.calls.counts["output"] == 0
            errors = [record for record in native_probe.caplog.records if record.name == native_probe.module]
            assert any(
                record.levelno == logging.ERROR and f"page={failure_page}" in record.getMessage() for record in errors
            )
            assert "No webhooks configured" not in native_probe.caplog.text
