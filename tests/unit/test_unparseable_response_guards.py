"""Tests for HTTP 200 replies that carry an unparseable body."""

from __future__ import annotations  # WHY: keep annotation behavior stable across Python versions.

import logging  # WHY: caplog assertions verify that each guard names the parse failure.
from http import HTTPStatus  # WHY: status constants make the 200 response contract clear.
from unittest.mock import MagicMock, patch  # WHY: tests isolate network and Redis side effects.

import pytest  # WHY: parametrization drives both empty and malformed response bodies.
import requests  # WHY: real Response objects reproduce requests.Response.json behavior.

from src.db import DatabaseConfig  # WHY: build the real Redis writer config object.
from src.device import arp_command_manager as arp_mod  # WHY: patch the product module requests client.
from src.device.arp_command_manager import ARPCommandManager  # WHY: drive the real ARP trigger helper.
from src.network._routing_utils_payload import _RoutingUtilsPayload  # WHY: drive the real routing parser.
from src.utils.address_utils import NominatimValidator  # WHY: drive the real geocode response parser.
from src.websocket.commands import MacTableCommand  # WHY: drive the real WebSocket MAC parser.
from src.websocket.diagnostics import common as diagnostic_common  # WHY: drive the real diagnostic parser.

_BODY_CASES = [b"", b"{bad json"]  # WHY: issue 2967 reports empty and malformed 200 response bodies.
_PARSE_LOG_FRAGMENT = "unparseable body"  # WHY: one shared assertion proves each log names the cause.


def _response(body: bytes, url: str = "https://h/api/v1/test") -> requests.Response:
    """Build a real requests.Response with the supplied raw body."""
    response = requests.Response()  # WHY: real parser raises the production JSONDecodeError subclass.
    response.status_code = HTTPStatus.OK  # WHY: issue 2967 only affects the success-status branch.
    response.url = url  # WHY: logs must name the endpoint that returned an invalid body.
    response._content = body  # WHY: requests stores the raw response bytes in this private slot.
    return response  # WHY: callers drive the real product parse path.


def _messages(caplog: pytest.LogCaptureFixture) -> str:
    """Return the captured log messages as one searchable string."""
    return "\n".join(record.getMessage() for record in caplog.records)  # WHY: substring checks stay compact.


@pytest.mark.parametrize("body", _BODY_CASES, ids=["empty-body", "malformed-body"])
def test_arp_trigger_returns_none_for_unparseable_success_body(
    body: bytes,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The ARP trigger honors its None failure contract for invalid JSON."""
    caplog.set_level(logging.ERROR, logger="src.device.arp_command_manager")  # WHY: capture the guard log.
    response = _response(body, "https://h/api/v1/sites/s/devices/d/arp")  # WHY: match the product URL shape.
    with patch.object(arp_mod.requests, "post", return_value=response):  # WHY: isolate the real product function.
        result = ARPCommandManager._trigger_command("h", "t", "s", "d")  # WHY: drive the real call site.
    assert result is None  # WHY: callers already read a falsey session id as the failure contract.
    assert _PARSE_LOG_FRAGMENT in _messages(caplog)  # WHY: issue 1766 forbids a silent failure.


@pytest.mark.parametrize("body", _BODY_CASES, ids=["empty-body", "malformed-body"])
def test_mac_table_extract_disconnects_for_unparseable_success_body(
    body: bytes,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The MAC table parser disconnects and returns None for invalid JSON."""
    caplog.set_level(logging.ERROR, logger="src.websocket.commands")  # WHY: capture the parse guard log.
    websocket_manager = MagicMock()  # WHY: verify that the parse-failure path frees the socket.
    response = _response(body, "https://h/api/v1/sites/s/devices/d/show_mac_table")  # WHY: identify endpoint.
    result = MacTableCommand._extract_session_id(response, websocket_manager)  # WHY: drive the real parser.
    assert result is None  # WHY: caller aborts when no session id exists.
    websocket_manager.disconnect.assert_called_once()  # WHY: issue 2967 warns this path leaked the socket.
    assert _PARSE_LOG_FRAGMENT in _messages(caplog)  # WHY: operators need the parse-failure cause.


@pytest.mark.parametrize("body", _BODY_CASES, ids=["empty-body", "malformed-body"])
def test_routing_payload_returns_error_tuple_for_unparseable_success_body(
    body: bytes,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The routing parser returns its `(None, error)` failure tuple for invalid JSON."""
    caplog.set_level(logging.ERROR, logger="src.network._routing_utils_payload")  # WHY: capture guard log.
    parser = _RoutingUtilsPayload(MagicMock())  # WHY: the parser method does not need parent state.
    response = _response(body, "https://h/api/v1/sites/s/devices/d/cmd")  # WHY: identify the failing endpoint.
    result = parser._parse_command_response(response)  # WHY: drive the real tuple projection helper.
    assert result == (None, "Unparseable response body")  # WHY: match the existing `(None, error)` contract.
    assert _PARSE_LOG_FRAGMENT in _messages(caplog)  # WHY: the log must name what failed.


@pytest.mark.parametrize("body", _BODY_CASES, ids=["empty-body", "malformed-body"])
def test_nominatim_parser_returns_empty_result_for_unparseable_success_body(
    body: bytes,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The geocode parser returns its empty-result failure shape for invalid JSON."""
    caplog.set_level(logging.ERROR, logger="src.utils.address_utils")  # WHY: capture the parse guard log.
    validator = NominatimValidator()  # WHY: drive the real geocode parser with default configuration.
    response = _response(body, "https://nominatim.openstreetmap.org/search")  # WHY: identify service endpoint.
    result = validator._parse_geocode_response(response, ["1 Main St"])  # WHY: drive the real parser.
    assert result["valid"] is False  # WHY: the empty-result contract marks validation failure.
    assert result["error"] == "Unparseable response body"  # WHY: callers receive a clear failure reason.
    assert _PARSE_LOG_FRAGMENT in _messages(caplog)  # WHY: the log must preserve the cause for operators.


@pytest.mark.parametrize("body", _BODY_CASES, ids=["empty-body", "malformed-body"])
def test_diagnostic_common_disconnects_for_unparseable_success_body(
    body: bytes,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The shared diagnostic parser disconnects and returns None for invalid JSON."""
    caplog.set_level(logging.ERROR, logger="src.websocket.diagnostics.common")  # WHY: capture guard log.
    websocket_manager = MagicMock()  # WHY: verify the failure path closes the diagnostic socket.
    response = _response(body, "https://h/api/v1/sites/s/devices/d/arp")  # WHY: identify the endpoint.
    result = diagnostic_common.extract_command_session(response, websocket_manager, "arp")  # WHY: real helper.
    assert result is None  # WHY: callers already abort on a missing session id.
    websocket_manager.disconnect.assert_called_once()  # WHY: match non-200 and missing-session cleanup.
    assert _PARSE_LOG_FRAGMENT in _messages(caplog)  # WHY: operators need the parse-failure cause.


def test_diagnostic_common_reports_404_without_parsing_body(caplog: pytest.LogCaptureFixture) -> None:
    """The shared diagnostic parser reports a 404 and skips success-body parsing."""
    websocket_manager = MagicMock()  # WHY: verify that the non-success path frees the socket.
    response = _response(b'{"session": "ignored"}', "https://h/api/v1/sites/s/devices/d/arp")  # Build response.
    response.status_code = HTTPStatus.NOT_FOUND  # WHY: model a client-side Mist command refusal.
    response.json = MagicMock(side_effect=AssertionError("parsed 404 body"))  # WHY: parsing 4xx would be wrong.
    caplog.set_level(logging.WARNING, logger="src.websocket.diagnostics.common")  # WHY: capture status logs.
    result = diagnostic_common.extract_command_session(response, websocket_manager, "arp")  # WHY: drive parser.
    assert result is None  # WHY: a 404 response must not return a session identifier.
    websocket_manager.disconnect.assert_called_once()  # WHY: no result can arrive, so the socket must close.
    response.json.assert_not_called()  # WHY: non-success status must stop before success-body parsing.
    assert "Failed to issue arp command: 404" in _messages(caplog)  # WHY: the exact status must reach operators.
    assert "command failed; status=404" in _messages(caplog)  # WHY: the audit log must pin the status.


@pytest.mark.parametrize("status_code", [404, 503], ids=["client-error", "server-error"])
def test_diagnostic_common_rejects_http_error_statuses(
    status_code: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The shared diagnostic parser must reject client and server error responses."""
    websocket_manager = MagicMock()  # WHY: prove the failure path releases the WebSocket.
    response = _response(b'{"session": "ignored"}')  # WHY: build a real response object with valid JSON.
    response.status_code = status_code  # WHY: drive the HTTP error branch with a real status field.
    response.json = MagicMock(side_effect=AssertionError("parsed error body"))  # WHY: error bodies must not parse.
    caplog.set_level(logging.WARNING, logger="src.websocket.diagnostics.common")  # WHY: capture the status warning.
    result = diagnostic_common.extract_command_session(response, websocket_manager, "arp")  # WHY: drive parser.
    assert result is None  # WHY: HTTP error responses cannot yield a usable command session.
    websocket_manager.disconnect.assert_called_once()  # WHY: no session can arrive after an HTTP error.
    response.json.assert_not_called()  # WHY: the parser must stop before success-body parsing.
    assert f"command failed; status={status_code}" in _messages(caplog)  # WHY: operators need the exact status.


def test_arp_trigger_timeout_reaches_the_caller() -> None:
    """The ARP trigger must let a transport timeout reach the caller."""
    timeout = requests.exceptions.Timeout("synthetic timeout")  # WHY: use the real Requests timeout type.
    with patch.object(arp_mod.requests, "post", side_effect=timeout) as post:  # WHY: fail the product POST call.
        with pytest.raises(requests.exceptions.Timeout, match="synthetic timeout"):
            ARPCommandManager._trigger_command("h", "t", "s", "d")  # WHY: drive the real product transport seam.
    post.assert_called_once_with(  # WHY: prove the timeout came from the product ARP endpoint call.
        "https://h/api/v1/sites/s/devices/d/arp",
        headers={"Authorization": "Token t"},
        json={},
        timeout=30,
    )


def test_arp_trigger_connection_error_reaches_the_caller() -> None:
    """The ARP trigger must let a transport connection error reach the caller."""
    error = requests.exceptions.ConnectionError("synthetic connection error")  # WHY: use the real Requests type.
    with patch.object(arp_mod.requests, "post", side_effect=error) as post:  # WHY: fail the product POST call.
        with pytest.raises(requests.exceptions.ConnectionError, match="synthetic connection error"):
            ARPCommandManager._trigger_command("h", "t", "s", "d")  # WHY: drive the real product transport seam.
    post.assert_called_once_with(  # WHY: prove the error came from the product ARP endpoint call.
        "https://h/api/v1/sites/s/devices/d/arp",
        headers={"Authorization": "Token t"},
        json={},
        timeout=30,
    )


def test_redis_writer_json_call_is_not_an_http_response_parse() -> None:
    """RedisJSON writer line 597 sends JSON.SET and does not parse an HTTP body."""
    config = DatabaseConfig(redis_host="localhost", redis_port=6379, redis_password="test")  # WHY: real config.
    with patch("src.db.redis_writer.redis.Redis") as redis_class:  # WHY: isolate Redis while driving product code.
        client = MagicMock()  # WHY: product writer receives this fake Redis client.
        redis_class.return_value = client  # WHY: constructor uses the patched Redis class.
        client.module_list.return_value = [{"name": b"ReJSON", "ver": 20600}]  # WHY: pass module guard.
        pipeline = MagicMock()  # WHY: product writer sends JSON.SET commands through a pipeline.
        client.pipeline.return_value = pipeline  # WHY: write() uses this pipeline object.
        pipeline.execute.return_value = [True, True]  # WHY: one JSON.SET and one EXPIRE succeed.
        from src.db.redis_writer import RedisJSONWriter  # WHY: import after patch so no live Redis client is built.

        writer = RedisJSONWriter(config)  # WHY: drive the real writer constructor and module check.
        result = writer.write([{"id": "a"}], "getStats", {"primary_key": ["id"]})  # WHY: drive line 597.
    assert result.success is True  # WHY: successful RedisJSON command preserves the existing contract.
    pipeline.json.return_value.set.assert_called_once()  # WHY: line 597 is a Redis command builder, not a parser.
