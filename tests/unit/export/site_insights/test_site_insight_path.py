"""Menu 74 requests each site metric from the path form, and reports each refusal (issue #3266).

The live Mist cloud answers the SDK query form with HTTP 404 and an empty body.
It answers the path form with HTTP 200 and data for 55 of the 64 site-scope
metrics, and with HTTP 400 for the other 9. The answer double below replays
that behavior for both routes, so each test fails on the old code for the
reason that the issue records.
"""

from __future__ import annotations  # WHY: Keep the annotations cheap to evaluate.

import logging  # WHY: The tests read the operator lines through the log capture.
from collections.abc import Callable  # WHY: Type the answer double.
from types import SimpleNamespace  # WHY: A plain object stands in for the mistapi APIResponse.
from typing import Any  # WHY: The status values of the FR-006 cases have mixed types.
from unittest.mock import MagicMock  # WHY: Stand in for the collaborators that the tests do not read.
from urllib.parse import unquote  # WHY: Read the metric name back from the requested path.

import pytest  # WHY: Parametrize the FR-006 cases and capture the log.

from src.export.site_insights.site_metric_operation import SiteMetricOperation, SiteRunContext

SITE_ID = "site-hq"  # WHY: A fixed site identifier for the path.
SITE_NAME = "HQ Site"  # WHY: The site name that tags each record and names the report.
EXPORT_FILE = "SiteInsightMetrics_HQ_Site.csv"  # WHY: The file name that menu 74 builds for this site.
PATH_PREFIX = f"/api/v1/sites/{SITE_ID}/insights/"  # WHY: The path form without the metric.
RECORDED_METRICS = (  # WHY: The 64 site-scope metrics of the live probe on 2026-09-23, in request order.
    "num_clients",
    "bytes",
    "rx_bytes",
    "tx_bytes",
    "bps",
    "tx_bps",
    "rx_bps",
    "tx_retries",
    "rx_retries",
    "num_aps",
    "tx_rates",
    "rx_rates",
    "port_rx_errors",
    "num_ips",
    "client-auth-latency",
    "client-dhcp-latency",
    "dns-latency",
    "top-port-by-bytes",
    "top-wlan-by-bytes",
    "top-wlan-by-num_client",
    "top-ap-by-bytes",
    "top-ap-by-num_client",
    "top-client",
    "top-ip",
    "top-client_or_ip-by-bytes",
    "top-app-by-num_client",
    "top-app-by-bytes",
    "top-categories-by-bytes",
    "top-services-by-bytes",
    "top-client-by-threats",
    "top-client-by-num_ssids",
    "rssi",
    "noise",
    "uptime-bar",
    "time-to-connect",
    "successful-connect",
    "client-roam-band5",
    "client-roam-band24",
    "ap-availability",
    "client-coverage-band5",
    "client-coverage-band24",
    "client-capacity-band5",
    "client-capacity-band24",
    "site-summary",
    "top-switch-by-bytes",
    "top-gateway-by-bytes",
    "activity",
    "ap-count",
    "switch-metrics",
    "gateway-metrics",
    "lte_rssi",
    "call-user_qos",
    "call-user_cpu",
    "call-user_feedback",
    "call-metrics",
    "app-bytes",
    "top-wan-apps",
    "top-wan-policy-by-bytes",
    "minis-app-metrics",
    "minis-probe-stats",
    "minis-top-probes",
    "top-flow-by-src",
    "top-flow-by-dst",
    "top-flow-by-app",
)
UNAVAILABLE = {"detail": "data temporary unavailable"}  # WHY: The reason of six refusals in the probe.
RECORDED_REFUSALS = {  # WHY: The 9 HTTP 400 answers of the live probe, with the error body of each.
    "noise": {"detail": "valid band is required"},
    "time-to-connect": UNAVAILABLE,
    "successful-connect": UNAVAILABLE,
    "client-coverage-band5": UNAVAILABLE,
    "client-coverage-band24": UNAVAILABLE,
    "client-capacity-band5": UNAVAILABLE,
    "client-capacity-band24": UNAVAILABLE,
    "switch-metrics": {"details": "unknown"},
    "gateway-metrics": {"details": "unknown"},
}
DATA_METRICS = [metric for metric in RECORDED_METRICS if metric not in RECORDED_REFUSALS]  # WHY: The 55 with data.

Answer = Callable[[str, str], SimpleNamespace]  # WHY: An answer takes the metric and the route name.


def metric_data() -> dict[str, Any]:
    """Return a new metric body, because the operation adds its tags to the body that it receives."""
    return {"start": 1, "end": 2, "interval": 3600, "results": [1, 2]}  # WHY: The keys of a live answer.


def recorded_answer(metric: str, route: str) -> SimpleNamespace:
    """Answer like the live cloud: the probe result for the path form, HTTP 404 with an empty body for the SDK."""
    if route != "path":  # WHY: The live cloud refuses the SDK query form for every metric.
        return SimpleNamespace(status_code=404, data={})  # WHY: The live answer to the SDK query form.
    if metric in RECORDED_REFUSALS:  # WHY: The live cloud refused 9 metrics on the path form.
        return SimpleNamespace(status_code=400, data=dict(RECORDED_REFUSALS[metric]))  # WHY: The recorded body.
    return SimpleNamespace(status_code=200, data=metric_data())  # WHY: The other 55 metrics hold data.


def same_answer_on_both_routes(refused: dict[str, dict[str, str]]) -> Answer:
    """Return an answer that refuses the named metrics on both routes and gives data for the rest."""

    def answer(metric: str, route: str) -> SimpleNamespace:
        """Refuse the named metric with HTTP 400 and its body, whatever the route."""
        if metric in refused:  # WHY: The API refuses this metric on each route.
            return SimpleNamespace(status_code=400, data=dict(refused[metric]))  # WHY: A Mist error body.
        return SimpleNamespace(status_code=200, data=metric_data())  # WHY: Metric data on each route.

    return answer  # WHY: The double reads the metric and the route of each request.


def refuse_every_metric(metric: str, route: str) -> SimpleNamespace:
    """Refuse each metric on each route with HTTP 404 and an empty body."""
    return SimpleNamespace(status_code=404, data={})  # WHY: The answer names no metric and no route.


def sdk_function(deps: SimpleNamespace) -> MagicMock:
    """Return the SDK function double that builds the query form."""
    return deps.mistapi.api.v1.sites.insights.getSiteInsightMetrics  # WHY: One name for the SDK route.


DEPENDENCY_NAMES = (  # WHY: The keyword names of the SiteMetricOperation constructor.
    "apisession",
    "PromptUtils",
    "DataProcessingUtils",
    "DataExporter",
    "EnhancedSSHRunner",
    "InsightMetricsUtils",
    "mistapi",
)


def build_operation(
    answer: Answer = recorded_answer, metrics: tuple[str, ...] = RECORDED_METRICS
) -> tuple[SiteMetricOperation, SimpleNamespace]:
    """Build menu 74 with both request routes wired to one answer, and return the operation and its doubles."""
    deps = SimpleNamespace(**{name: MagicMock(name=name) for name in DEPENDENCY_NAMES})  # WHY: One double each.
    deps.apisession.mist_get.side_effect = lambda uri, *args, **kwargs: answer(
        unquote(uri.removeprefix(PATH_PREFIX)), "path"
    )  # WHY: Read the metric name from the path.
    sdk_function(deps).side_effect = lambda session, site_id, metrics, *args, **kwargs: answer(metrics, "query")
    deps.PromptUtils.select_site.return_value = SITE_ID  # WHY: The operator selects the site.
    deps.mistapi.api.v1.sites.sites.getSiteInfo.return_value = SimpleNamespace(
        status_code=200, data={"id": SITE_ID, "name": SITE_NAME}
    )  # WHY: The site lookup names the site.
    deps.InsightMetricsUtils.get_by_scope.return_value = list(metrics)  # WHY: The site-scope metric list.
    deps.EnhancedSSHRunner.sanitize_filename.side_effect = lambda name: name.replace(" ", "_")  # WHY: File name.
    deps.DataProcessingUtils.flatten_nested_fields.side_effect = lambda rows: rows  # WHY: No flatten step.
    deps.DataProcessingUtils.escape_multiline.side_effect = lambda rows: rows  # WHY: No escape step.
    return SiteMetricOperation(**vars(deps)), deps  # WHY: The operation reads these collaborators.


def run_context() -> SiteRunContext:
    """Build the context of one menu 74 run."""
    return SiteRunContext(site_id=SITE_ID, site_name=SITE_NAME)  # WHY: The identifiers of the selected site.


def requested_uris(deps: SimpleNamespace) -> list[str]:
    """Return each URI that the session requested, in order."""
    return [call.args[0] for call in deps.apisession.mist_get.call_args_list]  # WHY: The first argument is the URI.


def written_rows(deps: SimpleNamespace) -> list[dict[str, Any]]:
    """Return the rows of the one export write."""
    return list(deps.DataExporter.write_with_format_selection.call_args.args[0])  # WHY: The first argument.


def run_menu(operation: SiteMetricOperation, caplog: pytest.LogCaptureFixture) -> list[str]:
    """Run menu 74 from the start, and return the lines that the operator reads."""
    caplog.clear()  # WHY: Read only the lines of this run.
    with caplog.at_level(logging.INFO):  # WHY: Capture the summary and the refusal report.
        operation.execute()  # WHY: Select the site, request each metric, and write the export.
    return [record.getMessage() for record in caplog.records if record.getMessage().startswith("!")]


def test_the_request_uses_the_path_form() -> None:
    """FR-001: menu 74 requests each metric from the path form that the live cloud serves."""
    operation, deps = build_operation()  # WHY: Replay the live answers.
    operation._fetch_one_metric(run_context(), "num_clients")  # WHY: Request one metric.
    assert requested_uris(deps) == [PATH_PREFIX + "num_clients"]  # WHY: One request on the path form.


def test_the_metric_name_stays_one_path_segment() -> None:
    """FR-001: the path holds the metric name in URL-encoded form."""
    operation, deps = build_operation()  # WHY: Replay the live answers.
    operation._fetch_one_metric(run_context(), "top app/bytes")  # WHY: A name with unsafe characters.
    assert requested_uris(deps) == [PATH_PREFIX + "top%20app%2Fbytes"]  # WHY: The name is one encoded segment.


def test_the_sdk_query_form_is_not_requested(caplog: pytest.LogCaptureFixture) -> None:
    """FR-001: menu 74 no longer calls the SDK function, because the live cloud refuses its URL."""
    operation, deps = build_operation()  # WHY: Replay the live answers.
    run_menu(operation, caplog)  # WHY: Run menu 74 for the 64 recorded metrics.
    assert sdk_function(deps).call_count == 0  # WHY: The SDK query form gets HTTP 404 from the live cloud.
    assert len(requested_uris(deps)) == len(RECORDED_METRICS)  # WHY: One path request for each metric.


def test_the_probe_replay_exports_every_metric_with_data(caplog: pytest.LogCaptureFixture) -> None:
    """SC-001: the replay of the live probe exports 55 records, and the summary states 55."""
    operation, deps = build_operation()  # WHY: Replay the live answers.
    lines = run_menu(operation, caplog)  # WHY: Run menu 74 for the 64 recorded metrics.
    assert [row["metric_type"] for row in written_rows(deps)] == DATA_METRICS  # WHY: One row for each.
    assert f"! 55 site insight metrics exported to {EXPORT_FILE}" in lines  # WHY: The count is 55.


def test_the_probe_replay_reports_each_refusal(caplog: pytest.LogCaptureFixture) -> None:
    """SC-002 and FR-008: the operator reads the 9 refusals of the probe, each with its recorded reason."""
    operation, _deps = build_operation()  # WHY: Replay the live answers.
    lines = run_menu(operation, caplog)  # WHY: Run menu 74 for the 64 recorded metrics.
    report = lines[lines.index(f"! The Mist API refused 9 site insight metrics for {SITE_NAME}:") + 1 :]
    assert report == [  # WHY: One line for each refusal, in request order, with the reason of the body.
        "!   noise: HTTP 400, valid band is required",
        "!   time-to-connect: HTTP 400, data temporary unavailable",
        "!   successful-connect: HTTP 400, data temporary unavailable",
        "!   client-coverage-band5: HTTP 400, data temporary unavailable",
        "!   client-coverage-band24: HTTP 400, data temporary unavailable",
        "!   client-capacity-band5: HTTP 400, data temporary unavailable",
        "!   client-capacity-band24: HTTP 400, data temporary unavailable",
        "!   switch-metrics: HTTP 400, unknown",
        "!   gateway-metrics: HTTP 400, unknown",
    ]


def test_a_refused_metric_does_not_become_a_record() -> None:
    """FR-002: an HTTP 400 answer with an error body must not become a record."""
    operation, _deps = build_operation(same_answer_on_both_routes(RECORDED_REFUSALS))  # WHY: Refuse 9 metrics.
    assert operation._fetch_one_metric(run_context(), "noise") is None  # WHY: The error body is not data.


def test_the_count_holds_only_the_metrics_with_data() -> None:
    """FR-003: the count holds the 55 metrics with data, not the 9 refusals."""
    operation, _deps = build_operation(same_answer_on_both_routes(RECORDED_REFUSALS))  # WHY: Refuse 9 metrics.
    records, retrieved = operation._collect_metrics(run_context(), list(RECORDED_METRICS))  # WHY: Collect.
    assert retrieved == 55  # WHY: Nine of the 64 requests were refused.
    assert [record["metric_type"] for record in records] == DATA_METRICS  # WHY: No error body is a record.


def test_a_run_with_only_refusals_reports_them(caplog: pytest.LogCaptureFixture) -> None:
    """SC-003: if the API refuses every metric, the empty summary shows and the refusal report follows."""
    operation, _deps = build_operation(refuse_every_metric)  # WHY: The API refuses each of the 64 metrics.
    lines = run_menu(operation, caplog)  # WHY: Run menu 74.
    summary = f"! 0 insight metrics exported to {EXPORT_FILE} (no data available)"  # WHY: The empty summary.
    heading = f"! The Mist API refused 64 site insight metrics for {SITE_NAME}:"  # WHY: The report heading.
    assert lines.index(summary) < lines.index(heading)  # WHY: The report follows the summary.
    assert "!   num_clients: HTTP 404, The error body holds no reason." in lines  # WHY: An empty body.


def test_a_run_without_refusals_adds_no_refusal_line(caplog: pytest.LogCaptureFixture) -> None:
    """FR-004: a run without a refusal adds no refusal line."""
    operation, _deps = build_operation(same_answer_on_both_routes({}))  # WHY: Every metric holds data.
    lines = run_menu(operation, caplog)  # WHY: Run menu 74.
    assert [line for line in lines if "refused" in line] == []  # WHY: No refusal line.


def test_each_run_starts_with_no_refusal(caplog: pytest.LogCaptureFixture) -> None:
    """FR-005: a second run on the same operation reports only its own refusals."""
    operation, _deps = build_operation(same_answer_on_both_routes(RECORDED_REFUSALS))  # WHY: Refuse 9 metrics.
    run_menu(operation, caplog)  # WHY: The first run records 9 refusals.
    lines = run_menu(operation, caplog)  # WHY: The second run must start empty.
    assert f"! The Mist API refused 9 site insight metrics for {SITE_NAME}:" in lines  # WHY: Not 18.


@pytest.mark.parametrize("status_code", [MagicMock(name="status"), None, "400"])  # WHY: No integer status.
def test_an_answer_without_an_integer_status_keeps_the_old_path(status_code: Any) -> None:
    """FR-006: an answer without an integer HTTP status keeps its current behavior."""
    operation, _deps = build_operation(
        lambda metric, route: SimpleNamespace(status_code=status_code, data={"detail": "a body"})
    )  # WHY: The same answer on each route.
    record = operation._fetch_one_metric(run_context(), "num_clients")  # WHY: Request one metric.
    assert isinstance(record, dict)  # WHY: The old path exports every non-empty body as one record.
    assert record["detail"] == "a body"  # WHY: The old path keeps the body unchanged.


def test_the_tags_the_file_name_and_the_endpoint_name_stay_the_same(caplog: pytest.LogCaptureFixture) -> None:
    """FR-007: the record tags, the file name, and the endpoint name of the write stay the same."""
    operation, deps = build_operation(same_answer_on_both_routes({}), ("num_clients",))  # WHY: One metric.
    run_menu(operation, caplog)  # WHY: Run menu 74.
    (record,) = written_rows(deps)  # WHY: One metric gives one record.
    tags = {key: record[key] for key in ("metric_type", "site_id", "site_name")}  # WHY: The three tags.
    assert tags == {"metric_type": "num_clients", "site_id": SITE_ID, "site_name": SITE_NAME}  # WHY: Same tags.
    write = deps.DataExporter.write_with_format_selection.call_args  # WHY: The one export write.
    assert (write.args[1], write.kwargs) == (EXPORT_FILE, {"api_function_name": "getSiteInsightMetrics"})
