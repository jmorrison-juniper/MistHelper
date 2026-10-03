"""Verify status, body, pagination, and menu refusal decisions in the real exporter."""

from __future__ import annotations

import json
import logging
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock, call, patch

import pytest
from hypothesis import given, strategies

from src.export.org_webhook_deliveries_exporter import OrgWebhookDeliveriesExporter, OrgWebhookResponseRefusal


@pytest.fixture
def unit_host(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Supply only the operator context and the SDK session boundary for unit cases."""
    host = MagicMock()
    host.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    monkeypatch.setitem(sys.modules, "MistHelper", host)
    persistence = MagicMock(wraps=OrgWebhookDeliveriesExporter._persist)
    monkeypatch.setattr(OrgWebhookDeliveriesExporter, "_persist", persistence)
    host.persistence = persistence
    return host


class TestResponseStatus:
    """Require a reliable successful response before any body access."""

    @pytest.mark.parametrize("status_code", [401, 403, 404, 503])
    def test_http_refusal_precedes_body(self, status_code: int, caplog: pytest.LogCaptureFixture) -> None:
        """Do not read body properties after the actual status guard refuses a response."""
        response = MagicMock(status_code=status_code)
        body = PropertyMock(side_effect=RuntimeError("private-body-sentinel"))
        type(response).raw_data = body
        result = OrgWebhookDeliveriesExporter.ResponsePages.read(
            response, ("searchOrgWebhooksDeliveries", "org-1", "wh-1")
        )
        assert result is None
        assert body.call_count == 0
        assert f"HTTP {status_code}" in caplog.text
        assert "checked_pages=1" in caplog.text
        assert "private-body-sentinel" not in caplog.text

    @pytest.mark.parametrize("status_code", [None, "200", True, False, 200.0, 0, 99, 600, [], {}])
    def test_unavailable_or_malformed_status(self, status_code: object, caplog: pytest.LogCaptureFixture) -> None:
        """Do not convert a missing or malformed status into success."""
        response = SimpleNamespace(status_code=status_code, raw_data="[]", data=[], next=None)
        result = OrgWebhookDeliveriesExporter.ResponsePages.read(
            response, ("searchOrgWebhooksDeliveries", "org-1", "wh-1")
        )
        assert result is None
        assert "HTTP unavailable" in caplog.text
        assert "The HTTP status is unavailable or invalid." in caplog.text
        assert "checked_pages=1" in caplog.text

    def test_unreadable_status_is_visible(self, caplog: pytest.LogCaptureFixture) -> None:
        """Contain an unreadable status property without disclosing its exception text."""
        response = MagicMock()
        status = PropertyMock(side_effect=RuntimeError("private-status-sentinel"))
        type(response).status_code = status
        result = OrgWebhookDeliveriesExporter.ResponsePages.read(
            response, ("searchOrgWebhooksDeliveries", "org-1", "wh-1")
        )
        assert result is None
        assert status.call_count == 1
        assert "reason=RuntimeError" in caplog.text
        assert "HTTP unavailable" in caplog.text
        assert "private-status-sentinel" not in caplog.text

    @given(status_code=strategies.integers(min_value=-100000, max_value=100000))
    def test_actual_status_guard_matches_success_range(self, status_code: int) -> None:
        """Exercise the actual imported guard across successful and failed integer ranges."""
        if 200 <= status_code < 300:
            assert OrgWebhookDeliveriesExporter.ResponsePages._status(status_code) == status_code
        else:
            with pytest.raises(OrgWebhookResponseRefusal, match="HTTP"):
                OrgWebhookDeliveriesExporter.ResponsePages._status(status_code)


class TestResponseBody:
    """Refuse unreadable or unsupported bodies without changing valid record values."""

    @pytest.mark.parametrize("field", ["raw_data", "data", "next"])
    def test_unreadable_response_field(self, field: str, caplog: pytest.LogCaptureFixture) -> None:
        """Report an unreadable body or pagination property through the actual reader."""
        response = MagicMock(status_code=200, raw_data="[]", data=[], next=None)
        unreadable = PropertyMock(side_effect=ValueError("private-field-sentinel"))
        setattr(type(response), field, unreadable)
        result = OrgWebhookDeliveriesExporter.ResponsePages.read(
            response, ("searchOrgWebhooksDeliveries", "org-1", "wh-1")
        )
        assert result is None
        assert unreadable.call_count >= 1
        assert "HTTP 200" in caplog.text
        assert "reason=ValueError" in caplog.text
        assert "private-field-sentinel" not in caplog.text

    @pytest.mark.parametrize("body", ["", " \r\n\t", "bad json", "{"])
    def test_empty_or_malformed_wire(self, body: str, caplog: pytest.LogCaptureFixture) -> None:
        """Check the actual retained-body signal instead of treating a parse failure as emptiness."""
        response = SimpleNamespace(status_code=200, raw_data=body, data={}, next=None)
        result = OrgWebhookDeliveriesExporter.ResponsePages.read(
            response, ("searchOrgWebhooksDeliveries", "org-1", "wh-1")
        )
        assert result is None
        assert "HTTP 200" in caplog.text
        assert any(record.levelno == logging.ERROR for record in caplog.records)
        assert "empty or unavailable" in caplog.text or "did not parse as JSON" in caplog.text

    @pytest.mark.parametrize(
        "data", [None, {}, {"results": None}, {"results": {}}, {"results": "text"}, [None], ["text"]]
    )
    def test_unsupported_record_shape(self, data: object, caplog: pytest.LogCaptureFixture) -> None:
        """Reject unsupported actual reader inputs before the flattener can silently discard them."""
        response = SimpleNamespace(status_code=200, raw_data=json.dumps(data), data=data, next=None)
        result = OrgWebhookDeliveriesExporter.ResponsePages.read(
            response, ("searchOrgWebhooksDeliveries", "org-1", "wh-1")
        )
        assert result is None
        assert "HTTP 200" in caplog.text
        assert "record array" in caplog.text or "non-object record" in caplog.text

    def test_success_status_with_error_envelope(self, caplog: pytest.LogCaptureFixture) -> None:
        """Refuse a native-style API error envelope even when it includes an empty results array."""
        data = {"error": "private-error-sentinel", "results": []}
        response = SimpleNamespace(status_code=200, raw_data=json.dumps(data), data=data, next=None)
        result = OrgWebhookDeliveriesExporter.ResponsePages.read(
            response, ("searchOrgWebhooksDeliveries", "org-1", "wh-1")
        )
        assert result is None
        assert "response body reports an API error" in caplog.text
        assert "private-error-sentinel" not in caplog.text
        assert "HTTP 200" in caplog.text

    @pytest.mark.parametrize("shape", ["list", "results"])
    @pytest.mark.parametrize(
        "rows", [[], [{"id": "delivery-1", "status_code": 503, "nested": {"name": "Hook \u00e9"}}]]
    )
    def test_successful_shape_preserves_values(self, shape: str, rows: list[dict[str, object]]) -> None:
        """Retain successful empty and nonempty arrays without confusing a destination status with the cloud status."""
        data = rows if shape == "list" else {"results": rows}
        response = SimpleNamespace(status_code=200, raw_data=json.dumps(data), data=data, next=None)
        result = OrgWebhookDeliveriesExporter.ResponsePages.read(
            response, ("searchOrgWebhooksDeliveries", "org-1", "wh-1")
        )
        assert result == rows


class TestResponsePagination:
    """Use real SDK pagination while refusing incomplete collections."""

    @pytest.mark.parametrize("shape", ["list", "results"])
    def test_native_next_link_and_order(self, unit_host: MagicMock, shape: str) -> None:
        """Pass the original SDK link and preserve accepted row order across shape variants."""
        first = [{"id": "delivery-1"}]
        second = [{"id": "delivery-2"}]
        first_data = first if shape == "list" else {"results": first}
        second_data = second if shape == "list" else {"results": second}
        link = "/api/v1/orgs/org-1/webhooks/wh-1/events/search?search_after=opaque%2Bcursor"
        response = SimpleNamespace(status_code=200, raw_data=json.dumps(first_data), data=first_data, next=link)
        unit_host.apisession.mist_get.return_value = SimpleNamespace(
            status_code=200, raw_data=json.dumps(second_data), data=second_data, next=None
        )
        result = OrgWebhookDeliveriesExporter.ResponsePages.read(
            response, ("searchOrgWebhooksDeliveries", "org-1", "wh-1")
        )
        assert result == first + second
        assert unit_host.apisession.mist_get.call_args_list == [call(link)]

    @pytest.mark.parametrize("next_link", [False, True, 1, [], {}])
    def test_malformed_next_link(
        self, unit_host: MagicMock, next_link: object, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Do not ask the SDK to fetch a malformed link."""
        response = SimpleNamespace(status_code=200, raw_data="[]", data=[], next=next_link)
        result = OrgWebhookDeliveriesExporter.ResponsePages.read(
            response, ("searchOrgWebhooksDeliveries", "org-1", "wh-1")
        )
        assert result is None
        assert unit_host.apisession.mist_get.call_count == 0
        assert "next-page link is invalid" in caplog.text
        assert "checked_pages=1" in caplog.text

    def test_repeated_next_link_is_bounded(self, unit_host: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Stop a repeated native link without persisting a duplicate or incomplete collection."""
        link = "/api/v1/orgs/org-1/webhooks/wh-1/events/search?search_after=repeat"
        response = SimpleNamespace(
            status_code=200, raw_data='[{"id":"delivery-1"}]', data=[{"id": "delivery-1"}], next=link
        )
        unit_host.apisession.mist_get.return_value = response
        result = OrgWebhookDeliveriesExporter.ResponsePages.read(
            response, ("searchOrgWebhooksDeliveries", "org-1", "wh-1")
        )
        assert result is None
        assert unit_host.apisession.mist_get.call_args_list == [call(link)]
        assert "next-page link repeats" in caplog.text
        assert "page=2 checked_pages=2" in caplog.text

    def test_missing_next_response_is_refused(self, unit_host: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Do not accept prior rows when the real pagination helper receives no next response."""
        response = SimpleNamespace(status_code=200, raw_data="[]", data=[], next="/api/v1/orgs/org-1/webhooks?page=2")
        unit_host.apisession.mist_get.return_value = None
        result = OrgWebhookDeliveriesExporter.ResponsePages.read(response, ("listOrgWebhooks", "org-1", "selection"))
        assert result is None
        assert unit_host.apisession.mist_get.call_count == 1
        assert "HTTP unavailable" in caplog.text
        assert "page=2 checked_pages=2" in caplog.text

    def test_pagination_exception_keeps_identity_and_private_text(
        self, unit_host: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Preserve the SDK exception object without exposing its private text in exporter records."""
        response = SimpleNamespace(status_code=200, raw_data="[]", data=[], next="/api/v1/orgs/org-1/webhooks?page=2")
        fault = RuntimeError("private-pagination-sentinel")
        unit_host.apisession.mist_get.side_effect = fault
        result = OrgWebhookDeliveriesExporter.ResponsePages.read(response, ("listOrgWebhooks", "org-1", "selection"))
        assert result is None
        assert unit_host.apisession.mist_get.side_effect is fault
        assert "page=2 checked_pages=1" in caplog.text
        assert "reason=RuntimeError" in caplog.text
        assert "private-pagination-sentinel" not in caplog.text


class TestMenuRefusalBoundaries:
    """Apply actual response refusals before selection, search, or persistence."""

    @pytest.mark.parametrize("status_code", [401, 403, 404, 503])
    def test_discovery_refusal_stops_menu(
        self, unit_host: MagicMock, status_code: int, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Do not prompt or search deliveries after the actual discovery response fails."""
        unit_host.apisession.mist_get.return_value = SimpleNamespace(
            status_code=status_code, raw_data='{"detail":"Forbidden"}', data={"detail": "Forbidden"}, next=None
        )
        prompt = MagicMock(return_value="1")
        monkeypatch.setattr("builtins.input", prompt)
        OrgWebhookDeliveriesExporter.deliveries()
        assert prompt.call_count == 0
        assert unit_host.apisession.mist_get.call_count == 1
        assert unit_host.persistence.call_count == 0
        assert unit_host.DataExporter.write_with_format_selection.call_count == 0

    @pytest.mark.parametrize("status_code", [401, 403, 404, 503])
    def test_delivery_refusal_stops_persistence(
        self, unit_host: MagicMock, status_code: int, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Read a real successful discovery result before refusing the failed delivery response."""
        webhooks = [{"id": "wh-1", "name": "Alarm Hook"}]
        unit_host.apisession.mist_get.side_effect = [
            SimpleNamespace(status_code=200, raw_data=json.dumps(webhooks), data=webhooks, next=None),
            SimpleNamespace(
                status_code=status_code, raw_data='{"detail":"Forbidden"}', data={"detail": "Forbidden"}, next=None
            ),
        ]
        monkeypatch.setattr("builtins.input", MagicMock(return_value="1"))
        OrgWebhookDeliveriesExporter.deliveries()
        assert unit_host.apisession.mist_get.call_count == 2
        assert unit_host.persistence.call_count == 0
        assert unit_host.DataExporter.write_with_format_selection.call_count == 0

    def test_no_organization_stops_before_discovery(self, unit_host: MagicMock) -> None:
        """Keep the original no-selection behavior without any SDK operation."""
        unit_host.ConfigUtils.get_cached_or_prompted_org_id.return_value = None
        OrgWebhookDeliveriesExporter.deliveries()
        assert unit_host.apisession.mist_get.call_count == 0
        assert unit_host.persistence.call_count == 0

    def test_discovery_sdk_exception_is_contained(self, unit_host: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Contain a directly coupled SDK exception without exposing its private details."""
        fault = RuntimeError("private-discovery-sentinel")
        unit_host.apisession.mist_get.side_effect = fault
        result = OrgWebhookDeliveriesExporter._select_webhook_id("org-1")
        assert result is None
        assert unit_host.apisession.mist_get.side_effect is fault
        assert "checked_pages=0" in caplog.text
        assert "reason=RuntimeError" in caplog.text
        assert "private-discovery-sentinel" not in caplog.text

    @pytest.mark.parametrize("message", ["HTTP 403", "HTTP 503", "HTTP 403 private", "private-runtime-sentinel"])
    def test_delivery_sdk_exception_uses_safe_context(
        self, unit_host: MagicMock, message: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Retain explicit HTTP failure text only when the complete message contains a safe status."""
        unit_host.apisession.mist_get.side_effect = RuntimeError(message)
        with patch.object(OrgWebhookDeliveriesExporter, "_select_webhook_id", return_value=("wh-1", "Alarm Hook")):
            OrgWebhookDeliveriesExporter.deliveries()
        assert unit_host.persistence.call_count == 0
        assert "Error fetching organization webhook deliveries" in caplog.text
        assert ("reason=" + message in caplog.text) is (message in {"HTTP 403", "HTTP 503"})
        assert "private" not in caplog.text
