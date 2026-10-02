"""Independent documented inputs and expected records for issue #3699."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TrendTarget:
    """Keep expected SDK routing and console answers independent of the exporter."""

    operation: str
    uri: str
    filename: str
    values: tuple[str, ...]
    answers: tuple[str, ...]


@dataclass(frozen=True)
class TrendDocument:
    """Hold a documented object and its established flattened record."""

    target: TrendTarget
    payload: dict[str, Any]
    expected: dict[str, Any]


CANONICAL_DOCUMENTS = (
    TrendDocument(
        TrendTarget(
            "getSiteSleSummaryTrend",
            "/api/v1/sites/site-3335/sle/site/scope-3335/metric/coverage/summary-trend",
            "getSiteSleSummaryTrend_Local_Site_scope_site_scope_id_scope-3335_metric_coverage.csv",
            ("site-3335", "site", "scope-3335", "coverage"),
            ("4", "0", "site", "scope-3335", "coverage"),
        ),
        {
            "start": 1700000000,
            "end": 1700000600,
            "classifiers": [],
            "sle": {
                "interval": 600,
                "name": "coverage",
                "samples": {"degraded": [1], "total": [10], "value": [90]},
                "x_label": "Time",
                "y_label": "Success",
            },
        },
        {
            "start": 1700000000,
            "end": 1700000600,
            "sle_interval": 600,
            "sle_name": "coverage",
            "sle_samples_degraded": "1",
            "sle_samples_total": "10",
            "sle_samples_value": "90",
            "sle_x_label": "Time",
            "sle_y_label": "Success",
        },
    ),
    TrendDocument(
        TrendTarget(
            "getSiteSleClassifierSummaryTrend",
            "/api/v1/sites/site-3335/sle/site/scope-3335/metric/coverage/classifier/low-rssi/summary-trend",
            "getSiteSleClassifierSummaryTrend_Local_Site_scope_site_scope_id_scope-3335_metric_coverage_classifier_low-rssi.csv",
            ("site-3335", "site", "scope-3335", "coverage", "low-rssi"),
            ("15", "0", "site", "scope-3335", "coverage", "low-rssi"),
        ),
        {
            "start": 1700000000,
            "end": 1700000600,
            "metric": "coverage",
            "classifier": {
                "interval": 600,
                "name": "low-rssi",
                "samples": {"degraded": [1], "duration": [600], "total": [10]},
                "x_label": "Time",
                "y_label": "Impact",
            },
        },
        {
            "start": 1700000000,
            "end": 1700000600,
            "metric": "coverage",
            "classifier_interval": 600,
            "classifier_name": "low-rssi",
            "classifier_samples_degraded": "1",
            "classifier_samples_duration": "600",
            "classifier_samples_total": "10",
            "classifier_x_label": "Time",
            "classifier_y_label": "Impact",
        },
    ),
)

RICH_DOCUMENTS = (
    TrendDocument(
        CANONICAL_DOCUMENTS[0].target,
        {
            "start": 1700000000,
            "end": 1700001800,
            "classifiers": [
                {
                    "interval": 600,
                    "name": "low-rssi",
                    "samples": {"degraded": [1, 0, 2], "duration": [600, 0, 1200], "total": [10, 10, 20]},
                    "x_label": "Time",
                    "y_label": "Impact",
                    "detail": {"reason": "Radio\nsignal", "error": "measurement"},
                },
                {
                    "interval": 600,
                    "name": "client-count",
                    "samples": {"degraded": [0, 1, 3], "duration": [0, 600, 1800], "total": [10, 10, 20]},
                    "x_label": "Time",
                    "y_label": "Impact",
                },
            ],
            "sle": {
                "interval": 600,
                "name": "coverage",
                "samples": {"degraded": [1, 2, 0], "total": [10, 20, 5], "value": [90, 90, 100]},
                "x_label": "Time",
                "y_label": "Success",
            },
            "error": {"classifier": "normal measurement", "samples": {"retry": [0, 1, 2]}},
        },
        {
            "start": 1700000000,
            "end": 1700001800,
            "classifiers_0_interval": 600,
            "classifiers_0_name": "low-rssi",
            "classifiers_0_samples_degraded": "1,0,2",
            "classifiers_0_samples_duration": "600,0,1200",
            "classifiers_0_samples_total": "10,10,20",
            "classifiers_0_x_label": "Time",
            "classifiers_0_y_label": "Impact",
            "classifiers_0_detail_reason": "Radio\\nsignal",
            "classifiers_0_detail_error": "measurement",
            "classifiers_1_interval": 600,
            "classifiers_1_name": "client-count",
            "classifiers_1_samples_degraded": "0,1,3",
            "classifiers_1_samples_duration": "0,600,1800",
            "classifiers_1_samples_total": "10,10,20",
            "classifiers_1_x_label": "Time",
            "classifiers_1_y_label": "Impact",
            "sle_interval": 600,
            "sle_name": "coverage",
            "sle_samples_degraded": "1,2,0",
            "sle_samples_total": "10,20,5",
            "sle_samples_value": "90,90,100",
            "sle_x_label": "Time",
            "sle_y_label": "Success",
            "error_classifier": "normal measurement",
            "error_samples_retry": "0,1,2",
        },
    ),
    TrendDocument(
        CANONICAL_DOCUMENTS[1].target,
        {
            "start": 1700000000,
            "end": 1700001800,
            "metric": "coverage",
            "classifier": {
                "interval": 600,
                "name": "low-rssi",
                "samples": {"degraded": [1, 0, 2], "duration": [600, 0, 1200], "total": [10, 10, 20]},
                "x_label": "Time",
                "y_label": "Impact",
                "detail": {"reason": "Radio\nsignal", "error": "measurement"},
            },
            "error": {"classifier": "normal measurement", "samples": {"retry": [0, 1, 2]}},
        },
        {
            "start": 1700000000,
            "end": 1700001800,
            "metric": "coverage",
            "classifier_interval": 600,
            "classifier_name": "low-rssi",
            "classifier_samples_degraded": "1,0,2",
            "classifier_samples_duration": "600,0,1200",
            "classifier_samples_total": "10,10,20",
            "classifier_x_label": "Time",
            "classifier_y_label": "Impact",
            "classifier_detail_reason": "Radio\\nsignal",
            "classifier_detail_error": "measurement",
            "error_classifier": "normal measurement",
            "error_samples_retry": "0,1,2",
        },
    ),
)
