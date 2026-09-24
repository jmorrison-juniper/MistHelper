"""Behavior tests for the refused device insight metrics of menu 76 (issue #3267).

The browser sweep of #3238 ran menu 76 for the gateway ``Branch-SSR``. The run
sent 44 metric requests. Five requests returned HTTP 400, and mistapi 0.64.0
returned each error body as the response data. These tests replay that run
through the real menu 76 code with a stand-in Mist API.
"""

from __future__ import annotations  # WHY: Keep the annotations cheap to evaluate.

import logging  # WHY: Read the operator lines that the operation writes through the logger.
from types import SimpleNamespace  # WHY: Build a response object with a real integer status.
from typing import Any  # WHY: Type the loose rows that the stand-in API returns.
from unittest.mock import MagicMock  # WHY: Stand in for the collaborators that the test does not examine.

import pytest  # WHY: Use the caplog fixture and the parametrize marker.

from src.export.site_insights.device_metric_operation import (  # WHY: Test the real menu 76 operation.
    DeviceMetricOperation,
    DeviceRunContext,
)

RECORDED_METRICS = (  # WHY: The 44 metric names of the recorded run, in the request order.
    "num_clients",
    "rx_bytes",
    "tx_bytes",
    "rx_mcast",
    "rx_bcast",
    "rx_pkts",
    "tx_mcast",
    "tx_bcast",
    "tx_pkts",
    "tx_bps",
    "rx_bps",
    "tx_rx_bps",
    "optic-metrics",
    "bgp-ribs-metrics",
    "port_rx_errors",
    "port_tx_errors",
    "cpu",
    "memory",
    "spu",
    "spu_memory",
    "num_sessions",
    "num_ips",
    "network-table-metrics",
    "port-metrics",
    "power_draw",
    "top-port-by-bytes",
    "top-client",
    "top-ip",
    "top-client_or_ip-by-bytes",
    "top-categories-by-bytes",
    "top-services-by-bytes",
    "uptime-bar",
    "vpn_peer-metrics",
    "worst-vpn_peers",
    "vpn_peer",
    "wan_link_health",
    "wan_policy_hit_count",
    "acl-policy",
    "gateway-metrics",
    "lte_rssi",
    "top-wan-apps",
    "top-wan-policy-by-bytes",
    "top-flow-by-src",
    "top-flow-by-dst",
)
RECORDED_REFUSALS = {  # WHY: The five refusal texts of the recorded run, copied from the export file.
    "bgp-ribs-metrics": "data temporary unavailable",
    "port-metrics": "port_id is required",
    "gateway-metrics": "metric parameter required and must be one of: rx_bytes, tx_bytes, bytes",
    "top-flow-by-src": "top_flows is only supported for switch devices or at site scope",
    "top-flow-by-dst": "top_flows is only supported for switch devices or at site scope",
}
METRIC_BODY = {  # WHY: The shape of a metric body that returned HTTP 200 in the recorded run.
    "start": 1790110800,
    "end": 1790197200,
    "interval": 3600,
    "limit": 168,
    "page": 1,
    "results": [None, 12],
    "rt": ["2026-09-22T21:00:00+00:00", "2026-09-22T22:00:00+00:00"],
}
EXPORT_FILE = "SiteDeviceInsights_AlamoSanAntonio_Branch-SSR.csv"  # WHY: The file name of the recorded run.


def recorded_answer(session: Any, site_id: str, metric: str, device_mac: str) -> SimpleNamespace:
    """Return the answer that the Mist API gave for one metric in the recorded run."""
    if metric in RECORDED_REFUSALS:  # WHY: mistapi returns an HTTP 400 as a response and does not raise.
        return SimpleNamespace(status_code=400, data={"detail": RECORDED_REFUSALS[metric]})  # WHY: Error body.
    return SimpleNamespace(status_code=200, data=dict(METRIC_BODY))  # WHY: A new copy for each metric row.


def build_operation(answer: Any = recorded_answer) -> DeviceMetricOperation:
    """Build the menu 76 operation with a stand-in Mist API and pass-through row helpers."""
    mistapi = MagicMock(name="mistapi")  # WHY: Only the device insight call matters to these tests.
    mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice.side_effect = answer  # WHY: Replay the run.
    processing = MagicMock(name="DataProcessingUtils")  # WHY: Keep the rows unchanged on the way to the writer.
    processing.flatten_nested_fields.side_effect = lambda rows: rows  # WHY: The test reads the raw rows.
    processing.escape_multiline.side_effect = lambda rows: rows  # WHY: The test reads the raw rows.
    metrics = MagicMock(name="InsightMetricsUtils")  # WHY: Serve the metric list of the recorded run.
    metrics.get_by_scope.return_value = list(RECORDED_METRICS)  # WHY: The run asked for these 44 metrics.
    ssh_runner = MagicMock(name="EnhancedSSHRunner")  # WHY: The file name helper must return plain text.
    ssh_runner.sanitize_filename.side_effect = lambda text: text  # WHY: The names of the run hold no space.
    return DeviceMetricOperation(  # WHY: Use the keyword-only constructor of the menu entry.
        apisession=MagicMock(name="apisession"),
        PromptUtils=MagicMock(name="PromptUtils"),
        DataProcessingUtils=processing,
        DataExporter=MagicMock(name="DataExporter"),
        EnhancedSSHRunner=ssh_runner,
        InsightMetricsUtils=metrics,
        PacketCaptureManager=MagicMock(name="PacketCaptureManager"),
        mistapi=mistapi,
    )


def gateway_context() -> DeviceRunContext:
    """Return the run context of the recorded gateway."""
    return DeviceRunContext(  # WHY: The identifiers of the recorded run, with a stand-in site ID.
        site_id="site-alamo",
        site_name="AlamoSanAntonio",
        device_id="device-branch-ssr",
        device_name="Branch-SSR",
        device_mac="90:ec:77:00:00:01",
        device_model="SSR120",
    )


def written_rows(operation: DeviceMetricOperation) -> list[dict[str, Any]]:
    """Return the rows of the one export file that the operation wrote."""
    writer = operation.DataExporter.write_with_format_selection  # WHY: The operation writes one file.
    assert writer.call_count == 1  # WHY: Each run must write exactly one export file.
    return list(writer.call_args.args[0])  # WHY: The first argument holds the rows.


def operator_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Return the operator lines, which start with an exclamation mark."""
    return [record.getMessage() for record in caplog.records if record.getMessage().startswith("!")]


def test_the_recorded_metrics_pass_the_gateway_filter() -> None:
    """The replay is valid only if the filter keeps all 44 metrics for a gateway."""
    operation = build_operation()  # WHY: The filter reads the metric list of the stand-in.
    assert operation._filter_metrics("SSR120") == list(RECORDED_METRICS)  # WHY: The run requested all 44.


def test_a_refused_metric_does_not_become_a_row() -> None:
    """FR-001: an HTTP 400 answer must not become an export row."""
    operation = build_operation()  # WHY: Replay the recorded answers.
    assert operation._fetch_one_metric(gateway_context(), "port-metrics") is None  # WHY: The API refused it.


def test_a_metric_with_data_still_becomes_a_row() -> None:
    """An HTTP 200 answer with data must still become an annotated export row."""
    operation = build_operation()  # WHY: Replay the recorded answers.
    row = operation._fetch_one_metric(gateway_context(), "tx_bps")  # WHY: The API answered with data.
    assert isinstance(row, dict)  # WHY: A metric with data must reach the export as one row.
    assert row["metric_type"] == "tx_bps"  # WHY: The row names its metric.
    assert row["results"] == [None, 12]  # WHY: The row keeps the metric data.


def test_the_count_holds_only_the_metrics_with_data() -> None:
    """FR-002: the count must hold the 39 metrics that returned data, not all 44 requests."""
    operation = build_operation()  # WHY: Replay the recorded answers.
    rows, retrieved = operation._collect_metrics(gateway_context(), list(RECORDED_METRICS))  # WHY: Run the loop.
    assert retrieved == 39  # WHY: Five of the 44 requests returned HTTP 400.
    assert len(rows) == 39  # WHY: The row list and the count must agree.
    assert not [row for row in rows if "detail" in row]  # WHY: No error body may reach the rows.


def test_the_export_file_holds_no_error_body(caplog: pytest.LogCaptureFixture) -> None:
    """FR-001 and FR-002: the export file holds 39 metric rows, and the summary states 39."""
    operation = build_operation()  # WHY: Replay the recorded answers.
    with caplog.at_level(logging.INFO):  # WHY: Capture the operator summary line.
        operation._run_export(gateway_context())  # WHY: Run the filter, the loop, and the export.
    rows = written_rows(operation)  # WHY: Read the rows that reached the writer.
    assert sorted(row["metric_type"] for row in rows) == sorted(  # WHY: Only the metrics with data remain.
        metric for metric in RECORDED_METRICS if metric not in RECORDED_REFUSALS
    )
    assert f"! 39 device insight metrics exported to {EXPORT_FILE}" in operator_lines(caplog)  # WHY: Count.


def test_the_operator_reads_each_refused_metric(caplog: pytest.LogCaptureFixture) -> None:
    """FR-003: the operator reads the name, the HTTP status, and the reason of each refused metric."""
    operation = build_operation()  # WHY: Replay the recorded answers.
    with caplog.at_level(logging.INFO):  # WHY: Capture the operator lines.
        operation._run_export(gateway_context())  # WHY: Run the full export path.
    lines = operator_lines(caplog)  # WHY: Read only the lines that the operator sees.
    assert "! The Mist API refused 5 device insight metrics for Branch-SSR:" in lines  # WHY: The heading.
    for metric, reason in RECORDED_REFUSALS.items():  # WHY: Each refusal needs its own line.
        assert f"!   {metric}: HTTP 400, {reason}" in lines  # WHY: Name, status, and reason.


def test_a_run_with_only_refusals_reports_them(caplog: pytest.LogCaptureFixture) -> None:
    """FR-003: the empty export path also reports the refused metrics."""
    operation = build_operation()  # WHY: Replay the recorded answers.
    operation.InsightMetricsUtils.get_by_scope.return_value = ["port-metrics", "gateway-metrics"]  # WHY: Refused.
    with caplog.at_level(logging.INFO):  # WHY: Capture the operator lines.
        operation._run_export(gateway_context())  # WHY: Run the export with no metric data.
    lines = operator_lines(caplog)  # WHY: Read only the lines that the operator sees.
    assert written_rows(operation) == []  # WHY: The empty path still writes one empty file.
    assert f"! 0 device insights exported to {EXPORT_FILE} (no data available)" in lines  # WHY: Empty summary.
    assert "! The Mist API refused 2 device insight metrics for Branch-SSR:" in lines  # WHY: The report follows.


def test_each_run_starts_with_no_refusal(caplog: pytest.LogCaptureFixture) -> None:
    """FR-005: a second run on the same operation must not repeat the refusals of the first run."""
    operation = build_operation()  # WHY: Replay the recorded answers.
    operation._collect_metrics(gateway_context(), ["port-metrics"])  # WHY: The first run holds one refusal.
    operation.InsightMetricsUtils.get_by_scope.return_value = ["tx_bps"]  # WHY: The second run has data only.
    with caplog.at_level(logging.INFO):  # WHY: Capture the operator lines of the second run.
        operation._run_export(gateway_context())  # WHY: Run the second export.
    assert not [line for line in operator_lines(caplog) if "refused" in line]  # WHY: No refusal remains.


@pytest.mark.parametrize("status_code", [MagicMock(name="status"), None, "400"])  # WHY: No integer status.
def test_an_answer_without_an_integer_status_keeps_the_old_path(status_code: Any) -> None:
    """FR-006: an answer without an integer HTTP status keeps its current behavior."""
    answer = SimpleNamespace(status_code=status_code, data={"detail": "a body"})  # WHY: No integer status.
    operation = build_operation(lambda session, site_id, metric, device_mac: answer)  # WHY: One fixed answer.
    row = operation._fetch_one_metric(gateway_context(), "tx_bps")  # WHY: Read the one metric.
    assert isinstance(row, dict)  # WHY: The old path exports every non-empty body as one row.
    assert row["detail"] == "a body"  # WHY: The old path keeps the body unchanged.
