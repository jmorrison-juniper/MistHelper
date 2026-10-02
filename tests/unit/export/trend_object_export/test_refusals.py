"""Native status, wire, transport, and later-page refusal regressions."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from mistapi.__api_response import APIResponse
from requests.exceptions import ConnectionError, Timeout

from src.export.endpoint_family_exporter import EndpointFamilyExporter
from tests.unit.export.trend_object_export.native_transport import (
    NativeBoundaries,
    NativeResponseFactory,
    NativeTrendTransport,
    WireScenario,
)


class TestFirstResponseRefusals:
    """Decide actual HTTP status before an error document can reach output."""

    @pytest.mark.parametrize("status", (403, 404, 429, 500, 503))
    @pytest.mark.parametrize("body_kind", ("json", "html"))
    def test_http_refusals_preserve_previous_output(
        self, native_trend_run: NativeBoundaries, status: int, body_kind: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Neither JSON nor HTML error bodies may replace an existing selected output."""
        document = native_trend_run.document
        path = Path("data") / document.target.filename
        path.write_bytes(b"previous-record\n")
        body = {"error": "source-body-marker-3699", "apitoken": "credential-marker-3699"}
        wire = b"<html>source-body-marker-3699 credential-marker-3699</html>" if body_kind == "html" else None
        native_trend_run.transport.responses[document.target.uri] = NativeResponseFactory.make(
            document.target.uri, WireScenario(status, body, wire=wire)
        )
        with caplog.at_level(logging.DEBUG, logger="src.export.endpoint_family_response.reader"):
            EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert native_trend_run.writer.call_args_list == []
        assert path.read_bytes() == b"previous-record\n"
        assert f"HTTP {status}" in caplog.text
        assert document.target.operation in caplog.text and "Checked 1 response" in caplog.text
        assert "No " + document.target.operation + " data found" not in caplog.text
        assert "source-body-marker-3699" not in caplog.text and "credential-marker-3699" not in caplog.text
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    @pytest.mark.parametrize("status", (None, "200", 200.0, True, "credential-marker-3699"))
    def test_missing_or_unusable_status_refuses_before_output(
        self,
        native_trend_run: NativeBoundaries,
        status: object,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """An unavailable native status cannot become a successful document."""
        document = native_trend_run.document
        native = APIResponse(None, NativeResponseFactory.HOST + document.target.uri)
        monkeypatch.setattr(native, "status_code", status)
        native.data = {"error": "source-body-marker-3699", "apitoken": "credential-marker-3699"}
        native_trend_run.transport.responses[document.target.uri] = native
        with caplog.at_level(logging.DEBUG, logger="src.export.endpoint_family_response.reader"):
            EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert native_trend_run.writer.call_args_list == []
        assert document.target.operation in caplog.text and "no usable HTTP status" in caplog.text
        assert "Checked 1 response" in caplog.text
        assert "source-body-marker-3699" not in caplog.text and "credential-marker-3699" not in caplog.text
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    @pytest.mark.parametrize("wire", (b"", b'{"source-body-marker-3699":"credential-marker-3699",'))
    def test_malformed_json_and_empty_wire_are_failures(
        self, native_trend_run: NativeBoundaries, wire: bytes, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A decoded empty default must not conceal an unreadable HTTP 200 body."""
        document = native_trend_run.document
        native_trend_run.transport.responses[document.target.uri] = NativeResponseFactory.make(
            document.target.uri, WireScenario(200, None, wire=wire)
        )
        with caplog.at_level(logging.DEBUG, logger="src.export.endpoint_family_response.reader"):
            EndpointFamilyExporter.site_sle_endpoints()
        native = native_trend_run.transport.decoded[-1]
        assert (native.status_code, native.raw_data, native.data) == (200, wire.decode("utf-8"), {})
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert native_trend_run.writer.call_args_list == []
        assert document.target.operation in caplog.text and "Error running" in caplog.text
        assert "No " + document.target.operation + " data found" not in caplog.text
        assert "source-body-marker-3699" not in caplog.text and "credential-marker-3699" not in caplog.text
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    @pytest.mark.parametrize("failure_type", (Timeout, ConnectionError))
    def test_actual_transport_exception_identity_and_safe_traceback(
        self, native_trend_run: NativeBoundaries, failure_type: type[Exception], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Contain the actual Requests exception without its private message or chained cause."""
        document = native_trend_run.document
        fault = failure_type("source-body-marker-3699 credential-marker-3699")
        fault.__cause__ = RuntimeError("credential-marker-3699")
        native_trend_run.transport.responses[document.target.uri] = fault
        with caplog.at_level(logging.ERROR):
            EndpointFamilyExporter.site_sle_endpoints()
        errors = [record for record in caplog.records if record.name == "root" and record.exc_info]
        assert len(errors) == 1
        assert errors[0].exc_info is not None and errors[0].exc_info[2] is fault.__traceback__
        assert errors[0].exc_info[1] is not fault
        assert type(fault).__name__ in str(errors[0].exc_info[1])
        assert native_trend_run.transport.responses[document.target.uri] is fault
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert native_trend_run.writer.call_args_list == []
        assert document.target.operation in caplog.text
        assert "source-body-marker-3699" not in caplog.text and "credential-marker-3699" not in caplog.text
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)


class TestPageRefusals:
    """A failed later page must not export prior rows as a complete result."""

    @pytest.mark.parametrize("shape", ("list", "results"))
    @pytest.mark.parametrize(
        "failure", ("403", "503", "malformed_json", "empty_body", "none_status", "missing_response")
    )
    def test_native_later_page_failures_make_no_write(
        self, native_trend_run: NativeBoundaries, shape: str, failure: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Validate every actual get_next response and stop without another page or output."""
        document = native_trend_run.document
        rows = [{"summary": {"value": 42}}]
        next_uri = native_trend_run.transport.paginated(document, shape, rows, [])
        native_trend_run.transport.responses[next_uri] = NativeResponseFactory.failure(next_uri, failure)
        with caplog.at_level(logging.DEBUG, logger="src.export.endpoint_family_response.reader"):
            EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document, next_uri)
        assert native_trend_run.writer.call_args_list == []
        assert list(Path("data").glob(document.target.filename)) == []
        assert document.target.operation in caplog.text and "Error running" in caplog.text
        assert "source-body-marker-3699" not in caplog.text and "credential-marker-3699" not in caplog.text
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    @pytest.mark.parametrize("link_kind", ("body", "headers"))
    def test_object_with_native_next_link_is_not_a_complete_record(
        self, native_trend_run: NativeBoundaries, link_kind: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Reject both native next-link mechanisms before a second request or output."""
        document = native_trend_run.document
        next_uri = document.target.uri + "?page=2"
        payload = {**document.payload, "next": next_uri} if link_kind == "body" else document.payload
        headers = {"X-Page-Total": "2", "X-Page-Limit": "1", "X-Page-Page": "1"} if link_kind == "headers" else {}
        native_trend_run.transport.responses[document.target.uri] = NativeResponseFactory.make(
            document.target.uri, WireScenario(200, payload, headers)
        )
        with caplog.at_level(logging.DEBUG, logger="src.export.endpoint_family_response.reader"):
            EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.transport.decoded[-1].next == next_uri
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert native_trend_run.writer.call_args_list == []
        assert "unsupported page shape" in caplog.text and document.target.operation in caplog.text
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    @pytest.mark.parametrize("shape", ("list", "results"))
    def test_later_page_shape_changes_are_refused(
        self, native_trend_run: NativeBoundaries, shape: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A native page cannot change envelope kind or substitute an unpaged object."""
        document = native_trend_run.document
        next_uri = document.target.uri + "?page=2"
        rows = [{"summary": {"value": 42}}]
        body = rows if shape == "list" else {"results": rows, "next": next_uri}
        headers = {"X-Page-Total": "2", "X-Page-Limit": "1", "X-Page-Page": "1"} if shape == "list" else {}
        native_trend_run.transport.responses[document.target.uri] = NativeResponseFactory.make(
            document.target.uri, WireScenario(200, body, headers)
        )
        native_trend_run.transport.responses[next_uri] = NativeResponseFactory.make(
            next_uri, WireScenario(200, {"results": rows} if shape == "list" else rows)
        )
        with caplog.at_level(logging.DEBUG, logger="src.export.endpoint_family_response.reader"):
            EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document, next_uri)
        assert native_trend_run.writer.call_args_list == []
        assert "changed its page shape" in caplog.text
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    def test_later_results_page_without_results_is_refused(
        self, native_trend_run: NativeBoundaries, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An HTTP 200 object cannot replace the required results envelope on a later page."""
        document = native_trend_run.document
        next_uri = document.target.uri + "?page=2"
        native_trend_run.transport.responses[document.target.uri] = NativeResponseFactory.make(
            document.target.uri, WireScenario(200, {"results": [{"value": 42}], "next": next_uri})
        )
        native_trend_run.transport.responses[next_uri] = NativeResponseFactory.make(
            next_uri, WireScenario(200, document.payload)
        )
        with caplog.at_level(logging.DEBUG, logger="src.export.endpoint_family_response.reader"):
            EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document, next_uri)
        assert native_trend_run.writer.call_args_list == []
        assert "unsupported page shape" in caplog.text
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)


class TestEmptyAndUnreadableShapes:
    """Distinguish successful no-content from unreadable collection shapes."""

    def test_http_204_empty_wire_remains_no_content(self, native_trend_run: NativeBoundaries) -> None:
        """The established successful no-content response creates no output."""
        document = native_trend_run.document
        native_trend_run.transport.responses[document.target.uri] = NativeResponseFactory.make(
            document.target.uri, WireScenario(204, None, wire=b"")
        )
        EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert native_trend_run.writer.call_args_list == []
        assert native_trend_run.transport.decoded[-1].status_code == 204
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    @pytest.mark.parametrize("body", ({"results": None}, {"results": {}}, 42, "plain text"))
    def test_unreadable_results_or_scalar_wire_refuses_output(
        self, native_trend_run: NativeBoundaries, body: object, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A non-list results envelope or scalar wire document is not a readable page."""
        document = native_trend_run.document
        native_trend_run.transport.responses[document.target.uri] = NativeResponseFactory.make(
            document.target.uri, WireScenario(200, body)
        )
        with caplog.at_level(logging.DEBUG, logger="src.export.endpoint_family_response.reader"):
            EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert native_trend_run.writer.call_args_list == []
        assert "readable record list" in caplog.text
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)
