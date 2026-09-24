"""Menu 75 requests each client metric from the path form, and reports each refusal (issue #3297).

The live Mist cloud answers the SDK query form with HTTP 404 and an empty body.
It answers the path form with HTTP 200 and data. The answer double below
replays that behavior for both routes, so each test fails on the old code for
the reason that the issue records.
"""

from __future__ import annotations  # WHY: Keep the annotations cheap to evaluate.

import logging  # WHY: The tests read the operator lines through the log capture.
from collections.abc import Callable  # WHY: Type the answer double.
from types import SimpleNamespace  # WHY: A plain object stands in for the mistapi APIResponse.
from typing import Any  # WHY: The status values of the FR-006 cases have mixed types.
from unittest.mock import MagicMock  # WHY: Stand in for the collaborators that the tests do not read.
from urllib.parse import unquote  # WHY: Read the metric name back from the requested path.

import pytest  # WHY: Parametrize the FR-006 cases and capture the log.

from src.refactors.serial_cc.site_client_insights import SiteClientInsightsService, _ExportContext

SITE_ID = "site-alamo"  # WHY: A fixed site identifier for the path.
SITE_NAME = "AlamoSanAntonio"  # WHY: The site name that tags each record.
CLIENT_MAC = "aa:bb:cc:dd:ee:ff"  # WHY: The colon form that the MAC normalizer returns.
EXPORT_FILE = "SiteClientInsights_AlamoSanAntonio_aabbccddeeff.csv"  # WHY: The file name that menu 75 builds.
PATH_PREFIX = f"/api/v1/sites/{SITE_ID}/insights/client/{CLIENT_MAC}/"  # WHY: The path form without the metric.
RECORDED_METRICS = (  # WHY: The 12 client-scope metrics of the live probe on 2026-09-23.
    "bytes",
    "rx_bytes",
    "tx_bytes",
    "client-rf-metrics",
    "client-auth-latency",
    "client-dhcp-latency",
    "top-app-by-bytes",
    "rssi",
    "network_connection",
    "call-user_qos",
    "call-user_cpu",
    "call-user_feedback",
)
REFUSALS = {  # WHY: Two refusals with a reason, for the refusal tests.
    "rssi": "metric is not supported for this client",
    "call-user_qos": "no call record",
}

Answer = Callable[[str, str], SimpleNamespace]  # WHY: An answer takes the metric and the route name.


def recorded_answer(metric: str, route: str) -> SimpleNamespace:
    """Answer like the live cloud: data for the path form, HTTP 404 with an empty body for the SDK form."""
    if route == "path":  # WHY: The live cloud serves the path form.
        return SimpleNamespace(status_code=200, data={"results": [1, 2], "interval": 3600})  # WHY: Metric data.
    return SimpleNamespace(status_code=404, data={})  # WHY: The live answer to the SDK query form.


def refusing_answer(refused: dict[str, str]) -> Answer:
    """Return an answer that refuses the named metrics on both routes and gives data for the rest."""

    def answer(metric: str, route: str) -> SimpleNamespace:
        """Refuse the named metric with HTTP 400 and a reason, whatever the route."""
        if metric in refused:  # WHY: The API refuses this metric on each route.
            return SimpleNamespace(status_code=400, data={"detail": refused[metric]})  # WHY: A Mist error body.
        return SimpleNamespace(status_code=200, data={"results": [1, 2], "interval": 3600})  # WHY: Metric data.

    return answer  # WHY: The double reads the metric and the route of each request.


def build_deps(answer: Answer = recorded_answer) -> SimpleNamespace:
    """Build the collaborators of menu 75, with both request routes wired to one answer."""
    deps = SimpleNamespace()  # WHY: The service reads its collaborators from one namespace.
    deps.apisession = MagicMock()  # WHY: The session sends the path form request.
    deps.apisession.mist_get.side_effect = lambda uri, *args, **kwargs: answer(
        unquote(uri.removeprefix(PATH_PREFIX)), "path"
    )  # WHY: Read the metric name from the path.
    deps.mistapi = MagicMock()  # WHY: The SDK function sends the query form request.
    sdk_function(deps).side_effect = lambda session, site_id, client_mac, metrics: answer(metrics, "query")
    deps.DataProcessingUtils = MagicMock()  # WHY: Keep the records unchanged before the write.
    deps.DataProcessingUtils.flatten_nested_fields.side_effect = lambda rows: rows  # WHY: No flatten step.
    deps.DataProcessingUtils.escape_multiline.side_effect = lambda rows: rows  # WHY: No escape step.
    deps.DataExporter = MagicMock()  # WHY: Capture the rows and the file name of the write.
    return deps  # WHY: The service reads these collaborators.


def sdk_function(deps: SimpleNamespace) -> MagicMock:
    """Return the SDK function double that builds the query form."""
    return deps.mistapi.api.v1.sites.insights.getSiteInsightMetricsForClient  # WHY: One name for the SDK route.


def export_context() -> _ExportContext:
    """Build the context of one menu 75 run."""
    return _ExportContext(site_id=SITE_ID, site_name=SITE_NAME, client_mac=CLIENT_MAC, filename=EXPORT_FILE)


def requested_uris(deps: SimpleNamespace) -> list[str]:
    """Return each URI that the session requested, in order."""
    return [call.args[0] for call in deps.apisession.mist_get.call_args_list]  # WHY: The first argument is the URI.


def written_rows(deps: SimpleNamespace) -> list[dict[str, Any]]:
    """Return the rows of the one export write."""
    return list(deps.DataExporter.write_with_format_selection.call_args.args[0])  # WHY: The first argument.


def operator_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Return the log lines that the operator reads, which start with an exclamation mark."""
    return [record.getMessage() for record in caplog.records if record.getMessage().startswith("!")]


def run_export(deps: SimpleNamespace, caplog: pytest.LogCaptureFixture) -> list[str]:
    """Run the collect and export path for the 12 recorded metrics, and return the operator lines."""
    with caplog.at_level(logging.INFO):  # WHY: Capture the summary and the refusal report.
        SiteClientInsightsService._run_collect_and_export(deps, export_context(), list(RECORDED_METRICS))
    return operator_lines(caplog)  # WHY: Only the lines that the operator reads.


def test_the_request_uses_the_path_form() -> None:
    """FR-001: menu 75 requests each metric from the path form that the live cloud serves."""
    deps = build_deps()  # WHY: Replay the live answers.
    SiteClientInsightsService._fetch_single_metric(deps, export_context(), "bytes")  # WHY: Request one metric.
    assert requested_uris(deps) == [PATH_PREFIX + "bytes"]  # WHY: One request on the path form.


def test_the_metric_name_stays_one_path_segment() -> None:
    """FR-001: the path holds the metric name in URL-encoded form."""
    deps = build_deps()  # WHY: Replay the live answers.
    SiteClientInsightsService._fetch_single_metric(deps, export_context(), "top app/bytes")  # WHY: Unsafe name.
    assert requested_uris(deps) == [PATH_PREFIX + "top%20app%2Fbytes"]  # WHY: The name is one encoded segment.


def test_the_sdk_query_form_is_not_requested() -> None:
    """FR-001: menu 75 no longer calls the SDK function, because the live cloud refuses its URL."""
    deps = build_deps()  # WHY: Replay the live answers.
    SiteClientInsightsService._collect_client_metrics(deps, export_context(), list(RECORDED_METRICS))  # WHY: Run.
    assert sdk_function(deps).call_count == 0  # WHY: The SDK query form gets HTTP 404 from the live cloud.


def test_the_probe_replay_exports_every_metric(caplog: pytest.LogCaptureFixture) -> None:
    """SC-001: the replay of the live probe exports 12 records, and the summary states 12."""
    deps = build_deps()  # WHY: Replay the live answers.
    lines = run_export(deps, caplog)  # WHY: Run the collect and export path.
    assert [row["metric_type"] for row in written_rows(deps)] == list(RECORDED_METRICS)  # WHY: One row each.
    assert f"! 12 client insight metrics exported to {EXPORT_FILE}" in lines  # WHY: The count is 12.


def test_a_refused_metric_does_not_become_a_record() -> None:
    """FR-002: an HTTP 400 answer with an error body must not become a record."""
    deps = build_deps(refusing_answer(REFUSALS))  # WHY: The API refuses two metrics.
    assert SiteClientInsightsService._fetch_single_metric(deps, export_context(), "rssi") is None  # WHY: Refused.


def test_the_count_holds_only_the_metrics_with_data() -> None:
    """FR-003: the count holds the 10 metrics with data, not the 2 refusals."""
    deps = build_deps(refusing_answer(REFUSALS))  # WHY: The API refuses two metrics.
    records, retrieved = SiteClientInsightsService._collect_client_metrics(
        deps, export_context(), list(RECORDED_METRICS)
    )  # WHY: Run the collect loop.
    assert retrieved == 10  # WHY: Two of the 12 requests were refused.
    assert sorted(record["metric_type"] for record in records) == sorted(set(RECORDED_METRICS) - set(REFUSALS))


def test_the_operator_reads_each_refused_metric(caplog: pytest.LogCaptureFixture) -> None:
    """FR-004: the operator reads the name, the HTTP status, and the reason of each refused metric."""
    lines = run_export(build_deps(refusing_answer(REFUSALS)), caplog)  # WHY: The API refuses two metrics.
    assert f"! The Mist API refused 2 client insight metrics for {CLIENT_MAC}:" in lines  # WHY: The heading.
    for metric, reason in REFUSALS.items():  # WHY: Each refusal needs its own line.
        assert f"!   {metric}: HTTP 400, {reason}" in lines  # WHY: Name, status, and reason.


def test_a_run_with_only_refusals_reports_them(caplog: pytest.LogCaptureFixture) -> None:
    """SC-002: if the API refuses every metric, the empty summary shows and the refusal report follows."""
    deps = build_deps(lambda metric, route: SimpleNamespace(status_code=404, data={}))  # WHY: Refuse all.
    lines = run_export(deps, caplog)  # WHY: Run the collect and export path.
    assert f"! 0 client insights exported to {EXPORT_FILE} (no data available)" in lines  # WHY: Empty summary.
    assert f"! The Mist API refused 12 client insight metrics for {CLIENT_MAC}:" in lines  # WHY: The report.
    assert "!   bytes: HTTP 404, The error body holds no reason." in lines  # WHY: An empty body names no reason.


def test_a_run_without_refusals_adds_no_refusal_line(caplog: pytest.LogCaptureFixture) -> None:
    """FR-004: a run without a refusal adds no refusal line."""
    lines = run_export(build_deps(), caplog)  # WHY: Replay the live answers, which hold no refusal.
    assert [line for line in lines if "refused" in line] == []  # WHY: No refusal line.


def test_each_context_holds_its_own_refusal_log() -> None:
    """FR-005: each run builds a new context, and each context starts with an empty refusal log."""
    first, second = export_context(), export_context()  # WHY: Two runs build two contexts.
    assert first.refusals is not second.refusals  # WHY: A shared log would carry refusals into the next run.
    assert (first.refusals.refusals, first.refusals.scope_label) == ([], "client insight")  # WHY: Empty start.


@pytest.mark.parametrize("status_code", [MagicMock(name="status"), None, "400"])  # WHY: No integer status.
def test_an_answer_without_an_integer_status_keeps_the_old_path(status_code: Any) -> None:
    """FR-006: an answer without an integer HTTP status keeps its current behavior."""
    deps = build_deps(lambda metric, route: SimpleNamespace(status_code=status_code, data={"detail": "a body"}))
    record = SiteClientInsightsService._fetch_single_metric(deps, export_context(), "bytes")  # WHY: One metric.
    assert isinstance(record, dict)  # WHY: The old path exports every non-empty body as one record.
    assert record["detail"] == "a body"  # WHY: The old path keeps the body unchanged.


def test_the_tags_and_the_file_name_stay_the_same() -> None:
    """FR-007: the MAC form, the file name, and the record tags stay the same."""
    deps = build_deps()  # WHY: Replay the live answers.
    SiteClientInsightsService._run_collect_and_export(deps, export_context(), ["bytes"])  # WHY: One metric.
    (record,) = written_rows(deps)  # WHY: One metric gives one record.
    tags = {key: record[key] for key in ("metric_type", "site_id", "site_name", "client_mac")}  # WHY: Tags.
    assert tags == {"metric_type": "bytes", "site_id": SITE_ID, "site_name": SITE_NAME, "client_mac": CLIENT_MAC}
    assert deps.DataExporter.write_with_format_selection.call_args.args[1] == EXPORT_FILE  # WHY: Same file.
