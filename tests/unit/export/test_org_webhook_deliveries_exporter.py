"""Tests for the organization webhook delivery exporter."""

from __future__ import annotations  # WHY: support the project Python type syntax.

import socket
import sys  # WHY: replace the lazy MistHelper import with a local test double.
from collections.abc import Iterator
from unittest.mock import MagicMock, patch  # WHY: isolate SDK and writer calls.

import pytest  # WHY: provide fixtures and parameterized cases.

from src.operations.exporting.export.org_webhook_deliveries_exporter import OrgWebhookDeliveriesExporter
from src.operations.exporting.export.org_webhook_deliveries_exporter import (
    OrgWebhookDeliveriesExporter as FailureModeOrgWebhookDeliveriesExporter,
)

_MODULE = "src.operations.exporting.export.org_webhook_deliveries_exporter"  # WHY: keep patch targets consistent.
_WEBHOOKS = [{"id": "wh-1", "name": "Alarms"}, {"id": "wh-2", "name": "Audits"}]  # WHY: test two valid choices.


@pytest.fixture(autouse=True)
def block_network(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Reject socket and DNS requests so tests use only synthetic data."""
    blocked = MagicMock(side_effect=AssertionError("Network access is not allowed in webhook export tests"))
    for attribute in ("connect", "connect_ex", "sendto"):
        monkeypatch.setattr(socket.socket, attribute, blocked)
    for attribute in ("create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr"):
        monkeypatch.setattr(socket, attribute, blocked)
    yield
    blocked.assert_not_called()


@pytest.fixture
def mist_helper(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Return a local MistHelper stand-in."""
    stub = MagicMock()  # WHY: expose the session, resolver, and writer used by the exporter.
    stub.apisession = MagicMock()  # WHY: the SDK receives this authenticated session.
    monkeypatch.setitem(sys.modules, "MistHelper", stub)  # WHY: satisfy the lazy module import.
    monkeypatch.setattr(f"{_MODULE}.SourceDependencyResolver", stub)
    return stub  # WHY: let each test configure the shared collaborators.


class TestWebhookSelection:
    """Verify the safe one-based webhook selection."""

    @pytest.mark.parametrize("raw", ["", "x", "0", "3"])  # WHY: cover invalid input boundaries.
    def test_invalid_choices_return_none(self, raw: str) -> None:
        """Reject invalid selections before the API call."""
        assert (
            OrgWebhookDeliveriesExporter._resolve_webhook_choice(raw, _WEBHOOKS) is None
        )  # WHY: no invalid choice may pass.

    def test_valid_choice_returns_id_and_name(self) -> None:
        """Resolve the displayed webhook choice."""
        assert OrgWebhookDeliveriesExporter._resolve_webhook_choice("2", _WEBHOOKS) == (
            "wh-2",
            "Audits",
        )  # WHY: choice two maps to row two.

    def test_missing_name_uses_identifier(self) -> None:
        """Keep a valid webhook selectable when its name is absent."""
        assert OrgWebhookDeliveriesExporter._resolve_webhook_choice("1", [{"id": "wh-3"}]) == (
            "wh-3",
            "wh-3",
        )  # WHY: the identifier remains stable.


class TestWebhookExport:
    """Verify API calls and persistence."""

    def test_selection_lists_webhooks_and_uses_safe_input(self, mist_helper: MagicMock) -> None:
        """List organization webhooks before prompting."""
        with (
            patch(f"{_MODULE}.mistapi.get_all", return_value=_WEBHOOKS),
            patch(f"{_MODULE}.mistapi.api.v1.orgs.webhooks.listOrgWebhooks", return_value=object()) as list_call,
            patch(f"{_MODULE}.InputUtils.safe_input", return_value="1"),
        ):
            result = OrgWebhookDeliveriesExporter._select_webhook_id("org-1")
        assert result == ("wh-1", "Alarms")  # WHY: the first displayed webhook must resolve.
        list_call.assert_called_once_with(mist_helper.apisession, "org-1")  # WHY: list the selected organization.

    def test_persistence_uses_the_operation_id(self, mist_helper: MagicMock) -> None:
        """Pass the exact operationId to the shared writer."""
        with patch(f"{_MODULE}.DataProcessingUtils.flatten_nested_fields", side_effect=lambda rows: rows):
            with patch(f"{_MODULE}.DataProcessingUtils.escape_multiline", side_effect=lambda rows: rows):
                OrgWebhookDeliveriesExporter._persist([{"status": "success"}], "Alarm Hook")
        kwargs = mist_helper.DataExporter.write_with_format_selection.call_args.kwargs  # WHY: inspect writer routing.
        assert (
            kwargs["api_function_name"] == "searchOrgWebhooksDeliveries"
        )  # WHY: the PK strategy depends on this name.

    def test_deliveries_calls_search_once_and_persists_rows(self, mist_helper: MagicMock) -> None:
        """Run the organization delivery search for the selected webhook."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: provide the required scope.
        with (
            patch.object(OrgWebhookDeliveriesExporter, "_select_webhook_id", return_value=("wh-1", "Alarms")),
            patch(
                f"{_MODULE}.mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries", return_value=object()
            ) as search_call,
            patch(f"{_MODULE}.mistapi.get_all", return_value=[{"id": "delivery-1"}]),
            patch.object(OrgWebhookDeliveriesExporter, "_persist") as persist_call,
        ):
            OrgWebhookDeliveriesExporter.deliveries()
        search_call.assert_called_once_with(
            mist_helper.apisession, "org-1", "wh-1"
        )  # WHY: use the selected identifiers.
        persist_call.assert_called_once_with([{"id": "delivery-1"}], "Alarms")  # WHY: pass all returned rows.

    def test_sdk_error_stays_inside_the_menu(self, mist_helper: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Log an SDK failure without raising it to the menu loop."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: reach the API call.
        writer = mist_helper.DataExporter.write_with_format_selection
        with (
            patch.object(OrgWebhookDeliveriesExporter, "_select_webhook_id", return_value=("wh-1", "Alarms")),
            patch(
                f"{_MODULE}.mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries", side_effect=RuntimeError("boom")
            ) as search_call,
            caplog.at_level("ERROR"),
        ):
            OrgWebhookDeliveriesExporter.deliveries()
        search_call.assert_called_once_with(mist_helper.apisession, "org-1", "wh-1")
        assert caplog.record_tuples == [("root", 40, "Error fetching organization webhook deliveries: boom")]
        assert writer.call_args_list == []

    @pytest.mark.parametrize("status_code", [404, 503])
    def test_webhook_http_status_sdk_error_is_logged(
        self, mist_helper: MagicMock, caplog: pytest.LogCaptureFixture, status_code: int
    ) -> None:
        """An HTTP 404 or HTTP 503 SDK failure must be logged and contained."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: reach the API call.
        error = RuntimeError(f"HTTP {status_code}")  # WHY: preserve the cloud status in the SDK error.
        with (
            patch.object(OrgWebhookDeliveriesExporter, "_select_webhook_id", return_value=("wh-1", "Alarms")),
            patch(f"{_MODULE}.mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries", side_effect=error),
            caplog.at_level("ERROR"),
        ):
            FailureModeOrgWebhookDeliveriesExporter.deliveries()  # WHY: call the real exporter entry point from src.
        assert f"HTTP {status_code}" in caplog.text  # WHY: the operator must see the status.
        assert "Error fetching organization webhook deliveries" in caplog.text  # WHY: prove product logging.
        mist_helper.DataExporter.write_with_format_selection.assert_not_called()  # WHY: failed calls write nothing.


class TestWebhookWriteStatus:
    """Verify that completion messages match the storage result."""

    @pytest.mark.parametrize("write_ok", [False, True])
    def test_persist_reports_the_writer_result(
        self, mist_helper: MagicMock, caplog: pytest.LogCaptureFixture, write_ok: bool
    ) -> None:
        """Report failure without a success or persistence message."""
        writer = mist_helper.DataExporter.write_with_format_selection
        writer.return_value = write_ok
        with caplog.at_level("DEBUG", logger=_MODULE):
            result = OrgWebhookDeliveriesExporter._persist([{"id": "delivery-1"}], "Alarm Hook")
        writer.assert_called_once_with(
            [{"id": "delivery-1"}],
            "OrgWebhookDeliveries_Alarm_Hook.csv",
            api_function_name="searchOrgWebhooksDeliveries",
        )
        assert result is None
        completion = "! 1 organization webhook delivery records exported to OrgWebhookDeliveries_Alarm_Hook.csv"
        assert ((_MODULE, 20, completion) in caplog.record_tuples) is write_ok
        assert ("records exported" in caplog.text) is write_ok
        assert ("persisted 1 rows" in caplog.text) is write_ok
        errors = [record.getMessage() for record in caplog.records if record.levelname == "ERROR"]
        expected = (
            []
            if write_ok
            else ["Failed to export 1 organization webhook delivery records to OrgWebhookDeliveries_Alarm_Hook.csv"]
        )
        assert errors == expected

    def test_empty_input_does_not_write(self, mist_helper: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Keep the empty-result behavior without claiming persistence."""
        with caplog.at_level("DEBUG", logger=_MODULE):
            result = OrgWebhookDeliveriesExporter._persist([], "Alarm Hook")
        assert result is None
        mist_helper.DataExporter.write_with_format_selection.assert_not_called()
        assert caplog.record_tuples == [(_MODULE, 20, "! No organization webhook delivery data found")]

    @pytest.mark.parametrize("write_ok", [False, True])
    def test_entrypoint_preserves_the_write_status(
        self, mist_helper: MagicMock, caplog: pytest.LogCaptureFixture, write_ok: bool
    ) -> None:
        """Exercise real persistence after a synthetic delivery search."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
        mist_helper.DataExporter.write_with_format_selection.return_value = write_ok
        with (
            patch.object(OrgWebhookDeliveriesExporter, "_select_webhook_id", return_value=("wh-1", "Alarms")),
            patch(f"{_MODULE}.mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries") as search,
            patch(f"{_MODULE}.mistapi.get_all", return_value=[{"id": "delivery-1"}]),
            caplog.at_level("DEBUG", logger=_MODULE),
        ):
            search.return_value.status_code = 200
            result = OrgWebhookDeliveriesExporter.deliveries()
        assert result is None
        search.assert_called_once_with(mist_helper.apisession, "org-1", "wh-1")
        mist_helper.DataExporter.write_with_format_selection.assert_called_once_with(
            [{"id": "delivery-1"}],
            "OrgWebhookDeliveries_Alarms.csv",
            api_function_name="searchOrgWebhooksDeliveries",
        )
        assert ("records exported" in caplog.text) is write_ok
        assert ("persisted 1 rows" in caplog.text) is write_ok
        assert ("Failed to export" in caplog.text) is not write_ok

    def test_writer_exception_stays_inside_the_entrypoint(
        self, mist_helper: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Keep the existing menu error behavior when storage raises."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
        mist_helper.DataExporter.write_with_format_selection.side_effect = OSError("synthetic write failure")
        with (
            patch.object(OrgWebhookDeliveriesExporter, "_select_webhook_id", return_value=("wh-1", "Alarms")),
            patch(f"{_MODULE}.mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries"),
            patch(f"{_MODULE}.mistapi.get_all", return_value=[{"id": "delivery-1"}]),
            caplog.at_level("DEBUG"),
        ):
            result = OrgWebhookDeliveriesExporter.deliveries()
        assert result is None
        assert (
            "root",
            40,
            "Error fetching organization webhook deliveries: synthetic write failure",
        ) in caplog.record_tuples
        assert "records exported" not in caplog.text
        assert "persisted" not in caplog.text

    @pytest.mark.parametrize("status_code", [403, 500])
    def test_rejected_response_never_reaches_storage(
        self, mist_helper: MagicMock, caplog: pytest.LogCaptureFixture, status_code: int
    ) -> None:
        """Preserve the existing rejected-response boundary."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
        with (
            patch.object(OrgWebhookDeliveriesExporter, "_select_webhook_id", return_value=("wh-1", "Alarms")),
            patch(f"{_MODULE}.mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries") as search,
            patch(f"{_MODULE}.mistapi.get_all") as paginate,
            caplog.at_level("DEBUG", logger=_MODULE),
        ):
            search.return_value.status_code = status_code
            result = OrgWebhookDeliveriesExporter.deliveries()
        assert result is None
        paginate.assert_not_called()
        mist_helper.DataExporter.write_with_format_selection.assert_not_called()
        assert caplog.record_tuples[-1] == (
            _MODULE,
            40,
            f"The cloud returned HTTP {status_code} for organization webhook deliveries at org org-1",
        )
        assert "records exported" not in caplog.text


def test_existing_composite_strategy_matches_delivery_identity() -> None:
    """Keep the existing stable delivery key registration visible to this feature."""
    from src.foundation.support.refactors.endpoint_primary_key_strategies import (
        ENDPOINT_PRIMARY_KEY_STRATEGIES,
    )  # WHY: inspect the central catalog.

    strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES["searchOrgWebhooksDeliveries"]  # WHY: the endpoint must be registered.
    assert strategy["type"] == "composite_pk"  # WHY: delivery rows are time-series records.
    assert strategy["primary_key"] == ["id", "webhook_id", "timestamp"]  # WHY: identify repeated deliveries safely.
