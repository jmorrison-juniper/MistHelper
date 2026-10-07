"""Prove partial insight exports fail honestly for issue #4031."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.foundation.support.utils.menu_entry import MenuEntry
from src.operations.exporting.export.site_insights.device_metric_operation import (
    DeviceMetricOperation,
    DeviceRunContext,
)
from src.operations.exporting.export.site_insights.site_metric_operation import (
    SiteMetricOperation,
    SiteRunContext,
)
from web_portal.services.operation import OperationExecutor


class _EventBus:
    """Collect no events for the portal classifier unit test."""

    def publish(self, *_args: object) -> None:
        """Ignore event publication during the direct classifier test."""


def _response(status_code: int, data: dict) -> SimpleNamespace:
    """Build a response with the status and body returned by mistapi."""
    return SimpleNamespace(status_code=status_code, data=data)


def _site_operation(responses: list[SimpleNamespace]) -> SiteMetricOperation:
    """Build menu 74 with one successful response and one HTTP refusal."""
    session = MagicMock()
    session.mist_get.side_effect = responses
    prompts = MagicMock()
    prompts.select_site.return_value = "site-1"
    metrics = MagicMock()
    metrics.get_by_scope.return_value = ["metric-ok", "metric-failed"]
    processing = MagicMock()
    processing.flatten_nested_fields.side_effect = lambda rows: rows
    processing.escape_multiline.side_effect = lambda rows: rows
    exporter = MagicMock()
    names = MagicMock()
    names.sanitize_filename.return_value = "HQ"
    return SiteMetricOperation(
        apisession=session,
        PromptUtils=prompts,
        DataProcessingUtils=processing,
        DataExporter=exporter,
        EnhancedSSHRunner=names,
        InsightMetricsUtils=metrics,
        mistapi=MagicMock(),
    )


def _device_operation(responses: list[SimpleNamespace]) -> DeviceMetricOperation:
    """Build menu 76 with one successful response and one HTTP refusal."""
    mistapi = MagicMock()
    mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice.side_effect = responses
    metrics = MagicMock()
    metrics.get_by_scope.return_value = ["metric-ok", "metric-failed"]
    processing = MagicMock()
    processing.flatten_nested_fields.side_effect = lambda rows: rows
    processing.escape_multiline.side_effect = lambda rows: rows
    exporter = MagicMock()
    names = MagicMock()
    names.sanitize_filename.return_value = "HQ"
    return DeviceMetricOperation(
        apisession=MagicMock(),
        PromptUtils=MagicMock(),
        DataProcessingUtils=processing,
        DataExporter=exporter,
        EnhancedSSHRunner=names,
        InsightMetricsUtils=metrics,
        PacketCaptureManager=MagicMock(),
        mistapi=mistapi,
    )


@pytest.mark.parametrize("status_code", [400, 500])
def test_site_partial_failure_emits_load_bearing_error(status_code: int, caplog: pytest.LogCaptureFixture) -> None:
    """Menu 74 keeps valid data and emits the portal failure marker for HTTP errors."""
    operation = _site_operation([_response(200, {"results": [1]}), _response(status_code, {"detail": "bad"})])
    with caplog.at_level(logging.INFO):
        rows, retrieved = operation._collect_metrics(SiteRunContext("site-1", "HQ"), ["metric-ok", "metric-failed"])
    assert retrieved == 1
    assert rows == [
        {
            "results": [1],
            "metric_type": "metric-ok",
            "site_id": "site-1",
            "site_name": "HQ",
        }
    ]
    assert operation._refusal_log.refusals[0].status_code == status_code
    assert any(
        record.getMessage() == f"! Error fetching getSiteInsightMetrics: HTTP {status_code} from "
        f"/api/v1/sites/site-1/insights/metric-failed"
        for record in caplog.records
    )


@pytest.mark.parametrize("status_code", [400, 500])
def test_device_partial_failure_emits_load_bearing_error(status_code: int, caplog: pytest.LogCaptureFixture) -> None:
    """Menu 76 keeps valid data and emits the portal failure marker for HTTP errors."""
    operation = _device_operation([_response(200, {"results": [1]}), _response(status_code, {"detail": "bad"})])
    context = DeviceRunContext("site-1", "HQ", "device-1", "Switch", "aa:bb:cc:dd:ee:ff", "EX")
    with caplog.at_level(logging.INFO):
        rows, retrieved = operation._collect_metrics(context, ["metric-ok", "metric-failed"])
    assert retrieved == 1
    assert rows == [
        {
            "results": [1],
            "metric_type": "metric-ok",
            "site_id": "site-1",
            "site_name": "HQ",
            "device_id": "device-1",
            "device_name": "Switch",
            "device_mac": "aa:bb:cc:dd:ee:ff",
        }
    ]
    assert operation._refusal_log.refusals[0].status_code == status_code
    assert any(
        record.getMessage() == f"! Error fetching getSiteInsightMetricsForDevice: HTTP {status_code} from "
        f"/api/v1/sites/site-1/insights/device/aa:bb:cc:dd:ee:ff/metric-failed"
        for record in caplog.records
    )


def test_portal_fails_when_partial_output_has_error_evidence() -> None:
    """The existing portal classifier fails a partial run when the exact marker is present."""
    entry = MenuEntry(
        menu_id="74",
        handler=lambda: None,
        title="Menu 74",
        category="interactive_safe",
        destructive=False,
        supports_fast=False,
    )
    executor = OperationExecutor({"74": entry}, None, None, _EventBus())
    try:
        run = executor._build_run_record("74")
        run["output_files"].append("SiteInsightMetrics_HQ.csv")
        run["log_messages"].append(
            {
                "message": "! Error fetching getSiteInsightMetrics: HTTP 400 from "
                "/api/v1/sites/site-1/insights/metric-failed",
                "level": "info",
            }
        )
        executor._finish_successful_operation(run)
        assert run["status"] == "failed"
        assert "Error fetching getSiteInsightMetrics" in str(run["error_message"])
    finally:
        executor.shutdown(0)
