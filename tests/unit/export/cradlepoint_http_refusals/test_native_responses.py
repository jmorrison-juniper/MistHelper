"""Prove native HTTP refusal handling without cloud or store access.

These tests use the real mistapi 0.64 response constructor.
The transport mock prohibits every live request.
The Python profiling callback counts real build and persistence calls.
SDK diagnostics remain separate from the captured product diagnostics.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from types import FrameType
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from requests import Response

from src.export.org_cradlepoint_connection_exporter import OrgCradlepointConnectionExporter

if TYPE_CHECKING:
    from mistapi.__api_response import APIResponse

_MODULE = "src.export.org_cradlepoint_connection_exporter"
_ORG_ID = "offline-refusal-org"


class NativeExportRun:
    """Run the real exporter with controlled boundary responses and a recording writer."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        """Install only the organization selector, endpoint, transport, and writer boundaries."""
        self.host = MagicMock()
        self.host.ConfigUtils.get_cached_or_prompted_org_id.return_value = _ORG_ID
        monkeypatch.setitem(sys.modules, "MistHelper", self.host)
        self.endpoint = MagicMock()
        monkeypatch.setattr(f"{_MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection", self.endpoint)
        self.transport = MagicMock(side_effect=AssertionError("A live HTTP request is forbidden."))
        monkeypatch.setattr("requests.sessions.Session.request", self.transport)
        self.caplog = caplog
        self.caplog.set_level(logging.DEBUG)
        self.callback_counts = {"_build_row": 0, "_persist": 0}

    @staticmethod
    def response(status_code: int | None, body: bytes = b"") -> APIResponse:
        """Construct the supported SDK response from controlled requests values."""
        from mistapi.__api_response import APIResponse

        url = f"https://offline.invalid/api/v1/orgs/{_ORG_ID}/setting/cradlepoint/setup"
        if status_code is None:
            return APIResponse(None, url)
        response = Response()
        response.status_code = status_code
        response.url = url
        response.headers["Content-Type"] = "application/json"
        response._content = body  # Supply transport bytes without opening a connection.
        return APIResponse(response, url)

    def record_callback(self, frame: FrameType, event: str, _argument: object) -> None:
        """Count real method entries without replacing production behavior."""
        callback_codes = {
            OrgCradlepointConnectionExporter._build_row.__code__,
            OrgCradlepointConnectionExporter._persist.__code__,
        }
        if event == "call" and frame.f_code in callback_codes:
            self.callback_counts[frame.f_code.co_name] += 1

    @contextmanager
    def capture(self, response: object) -> Iterator[None]:
        """Measure a direct menu call and print its checked-case and callback counts."""
        self.endpoint.return_value = response
        self.caplog.clear()
        previous_profile = sys.getprofile()
        sys.setprofile(self.record_callback)
        try:
            yield
        finally:
            sys.setprofile(previous_profile)  # Do not change the profiler of another test.
            print(
                "Checked 1 response: "
                f"endpoint={self.endpoint.call_count}, "
                f"build={self.callback_counts['_build_row']}, "
                f"persist={self.callback_counts['_persist']}, "
                f"writer={self.host.DataExporter.write_with_format_selection.call_count}, "
                f"live_requests={self.transport.call_count}."
            )

    @property
    def messages(self) -> list[tuple[int, str]]:
        """Read only exporter and existing menu-boundary diagnostics, not SDK diagnostics."""
        return [
            (record.levelno, record.getMessage()) for record in self.caplog.records if record.name in (_MODULE, "root")
        ]


@pytest.fixture
def native_run(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> NativeExportRun:
    """Keep the controlled boundaries and callback counts specific to each test."""
    return NativeExportRun(monkeypatch, caplog)


class TestNativeResponses:
    """Separate refused HTTP requests from valid integration status data."""

    @pytest.mark.parametrize("status_code", [403, 404, 429, 500, 503])
    @pytest.mark.parametrize(
        "body",
        [
            pytest.param(
                b'{"detail":"controlled-private-marker","Authorization":"controlled-private-marker",'
                b'"cookies":"controlled-private-marker","token":"controlled-private-marker",'
                b'"password":"controlled-private-marker"}',
                id="nonempty-dictionary",
            ),
            pytest.param(b"{}", id="empty-dictionary"),
            pytest.param(b'[{"detail":"controlled-private-marker"}]', id="nonempty-list"),
            pytest.param(b"[]", id="empty-list"),
            pytest.param(b"null", id="json-null"),
            pytest.param(b"", id="empty-bytes"),
        ],
    )
    def test_native_http_4xx_5xx_refusals(self, native_run: NativeExportRun, status_code: int, body: bytes) -> None:
        """Every native 4xx or 5xx body must stop before row construction and persistence."""
        response = native_run.response(status_code, body)
        assert response.status_code == status_code
        with native_run.capture(response):
            OrgCradlepointConnectionExporter.status()
        assert native_run.callback_counts == {"_build_row": 0, "_persist": 0}
        native_run.endpoint.assert_called_once_with(native_run.host.apisession, _ORG_ID)
        native_run.host.DataExporter.write_with_format_selection.assert_not_called()
        native_run.transport.assert_not_called()
        failure = f"testOrgCradlepointConnection failed: HTTP {status_code} (checked 1 response)."
        assert (
            logging.ERROR,
            f"Error fetching the Cradlepoint status for org {_ORG_ID}: {failure}",
        ) in native_run.messages
        assert (logging.INFO, f"! Error fetching Cradlepoint connection status: {failure}") in native_run.messages
        assert not any("controlled-private-marker" in message for _, message in native_run.messages)
        assert not any(
            "No Cradlepoint connection status found" in message or "exported to" in message
            for _, message in native_run.messages
        )

    def test_native_none_transport(self, native_run: NativeExportRun) -> None:
        """The native None transport response must not become an ordinary empty success."""
        response = native_run.response(None)
        assert response.status_code is None
        assert response.data == {}
        with native_run.capture(response):
            OrgCradlepointConnectionExporter.status()
        assert native_run.callback_counts == {"_build_row": 0, "_persist": 0}
        native_run.endpoint.assert_called_once_with(native_run.host.apisession, _ORG_ID)
        native_run.host.DataExporter.write_with_format_selection.assert_not_called()
        native_run.transport.assert_not_called()
        failure = "testOrgCradlepointConnection failed: transport status is unavailable (checked 1 response)."
        assert (
            logging.ERROR,
            f"Error fetching the Cradlepoint status for org {_ORG_ID}: {failure}",
        ) in native_run.messages
        assert (logging.INFO, f"! Error fetching Cradlepoint connection status: {failure}") in native_run.messages
        assert not any(
            "No Cradlepoint connection status found" in message or "exported to" in message
            for _, message in native_run.messages
        )

    @pytest.mark.parametrize(
        ("status_code", "expected_status"),
        [
            pytest.param(None, "transport status is unavailable", id="none"),
            pytest.param(0, "transport status is unavailable", id="zero"),
            pytest.param(-1, "transport status is unavailable", id="negative"),
            pytest.param(600, "transport status is unavailable", id="above-http-range"),
            pytest.param("200", "transport status is unavailable", id="string"),
            pytest.param(200.0, "transport status is unavailable", id="float"),
            pytest.param(True, "transport status is unavailable", id="true"),
            pytest.param(False, "transport status is unavailable", id="false"),
            pytest.param({"token": "controlled-private-marker"}, "transport status is unavailable", id="dictionary"),
            pytest.param(object(), "transport status is unavailable", id="opaque-object"),
            pytest.param("absent", "transport status is unavailable", id="absent-attribute"),
            pytest.param(100, "HTTP 100", id="informational"),
            pytest.param(302, "HTTP 302", id="redirect"),
            pytest.param(599, "HTTP 599", id="upper-http-boundary"),
        ],
    )
    def test_transport_status_requires_trustworthy_http_success(
        self, native_run: NativeExportRun, status_code: object, expected_status: str
    ) -> None:
        """An absent or unusable status never establishes success or exposes the status value."""
        response = native_run.response(200, b'{"detail":"controlled-private-marker"}')
        if status_code == "absent":
            delattr(response, "status_code")
        else:
            vars(response)["status_code"] = status_code  # Inject unusable metadata at the response boundary.
        with native_run.capture(response):
            OrgCradlepointConnectionExporter.status()
        assert native_run.callback_counts == {"_build_row": 0, "_persist": 0}
        native_run.endpoint.assert_called_once_with(native_run.host.apisession, _ORG_ID)
        native_run.host.DataExporter.write_with_format_selection.assert_not_called()
        native_run.transport.assert_not_called()
        failure = f"testOrgCradlepointConnection failed: {expected_status} (checked 1 response)."
        assert (
            logging.ERROR,
            f"Error fetching the Cradlepoint status for org {_ORG_ID}: {failure}",
        ) in native_run.messages
        assert (logging.INFO, f"! Error fetching Cradlepoint connection status: {failure}") in native_run.messages
        assert not any(
            "controlled-private-marker" in message
            or "No Cradlepoint connection status found" in message
            or "exported to" in message
            for _, message in native_run.messages
        )

    @pytest.mark.parametrize(
        ("body", "expected_row"),
        [
            pytest.param(
                b'{"last_status":"active","error":""}',
                {"org_id": _ORG_ID, "last_status": "active", "error": ""},
                id="active",
            ),
            pytest.param(
                b'{"last_status":"error","error":"Configuration is invalid\\nCheck the integration."}',
                {
                    "org_id": _ORG_ID,
                    "last_status": "error",
                    "error": "Configuration is invalid\\nCheck the integration.",
                },
                id="integration-error",
            ),
        ],
    )
    def test_native_http_200_preserves_integration_error_and_metadata(
        self, native_run: NativeExportRun, body: bytes, expected_row: dict[str, object]
    ) -> None:
        """A successful response preserves the exact row, escaping, filename, and endpoint metadata."""
        with native_run.capture(native_run.response(200, body)):
            OrgCradlepointConnectionExporter.status()
        assert native_run.callback_counts == {"_build_row": 1, "_persist": 1}
        native_run.endpoint.assert_called_once_with(native_run.host.apisession, _ORG_ID)
        native_run.host.DataExporter.write_with_format_selection.assert_called_once_with(
            [expected_row],
            f"OrgCradlepointConnection_{_ORG_ID}.csv",
            api_function_name="testOrgCradlepointConnection",
        )
        native_run.transport.assert_not_called()
        assert (
            logging.INFO,
            f"! 1 Cradlepoint status record(s) exported to OrgCradlepointConnection_{_ORG_ID}.csv",
        ) in native_run.messages
        assert not any(level == logging.ERROR for level, _ in native_run.messages)

    @pytest.mark.parametrize("status_code", [200, 201, 204, 299])
    @pytest.mark.parametrize("body", [b"{}", b"[]", b"null", b'"error"', b"42", b""])
    def test_native_success_empty_and_non_dict_body(
        self, native_run: NativeExportRun, status_code: int, body: bytes
    ) -> None:
        """Trustworthy success keeps the existing empty and non-dictionary handling."""
        with native_run.capture(native_run.response(status_code, body)):
            OrgCradlepointConnectionExporter.status()
        assert native_run.callback_counts == {"_build_row": 1, "_persist": 1}
        native_run.endpoint.assert_called_once_with(native_run.host.apisession, _ORG_ID)
        native_run.host.DataExporter.write_with_format_selection.assert_not_called()
        native_run.transport.assert_not_called()
        assert (logging.INFO, "! No Cradlepoint connection status found") in native_run.messages
        assert not any(level == logging.ERROR or "exported to" in message for level, message in native_run.messages)
