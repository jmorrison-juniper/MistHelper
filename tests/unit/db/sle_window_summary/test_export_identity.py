"""Verify exact SLE window identities and exporter validation without network access."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.foundation.support.refactors.endpoint_primary_key_strategies import SleWindowIdentity
from src.operations.exporting.export.endpoint_family_exporter import EndpointFamilyExporter

HISTOGRAM_OPERATION = "getSiteSleHistogram"
IMPACT_OPERATION = "getSiteSleImpactSummary"
HISTOGRAM_FIELDS = ("site_id", "scope", "scope_id", "metric", "start", "end")
IMPACT_FIELDS = ("site_id", "scope", "scope_id", "metric", "classifier", "failure", "start", "end")


class TestSleWindowIdentity:
    """Keep summary keys grounded in selected request values and response fields."""

    @pytest.mark.parametrize(
        ("operation", "expected"),
        ((HISTOGRAM_OPERATION, HISTOGRAM_FIELDS), (IMPACT_OPERATION, IMPACT_FIELDS)),
    )
    def test_exact_identity_fields(self, operation: str, expected: tuple[str, ...]) -> None:
        """Declare only source dimensions and actual response-window values."""
        assert SleWindowIdentity.fields(operation) == expected

    @pytest.mark.parametrize(
        ("operation", "row"),
        (
            (
                HISTOGRAM_OPERATION,
                {
                    "site_id": "site-1",
                    "scope": "site",
                    "scope_id": "scope-1",
                    "metric": "coverage",
                    "start": 100,
                    "end": 200,
                },
            ),
            (
                IMPACT_OPERATION,
                {
                    "site_id": "site-1",
                    "scope": "site",
                    "scope_id": "scope-1",
                    "metric": "coverage",
                    "classifier": "low-rssi",
                    "failure": "bad",
                    "start": 100,
                    "end": 200,
                },
            ),
        ),
    )
    def test_every_identity_field_changes_the_key(self, operation: str, row: dict[str, object]) -> None:
        """Keep each source dimension and boundary distinct."""
        fields = SleWindowIdentity.fields(operation)
        original_key = SleWindowIdentity.key(row, list(fields))
        replacements: dict[str, object] = {
            "site_id": "site-2",
            "scope": "ap",
            "scope_id": "scope-2",
            "metric": "capacity",
            "start": 101,
            "end": 201,
            "classifier": "other",
            "failure": "other",
        }
        for field in fields:
            changed_row = {**row, field: replacements[field]}
            assert SleWindowIdentity.key(changed_row, list(fields)) != original_key

    @pytest.mark.parametrize("classifier", ("", "low-rssi"))
    @pytest.mark.parametrize("failure", ("", "bad"))
    def test_empty_impact_strings_remain_valid(self, classifier: str, failure: str) -> None:
        """Accept each documented empty-string combination without coercion."""
        row = {
            "site_id": "site-1",
            "scope": "site",
            "scope_id": "scope-1",
            "metric": "coverage",
            "classifier": classifier,
            "failure": failure,
            "start": 100,
            "end": 200,
        }
        assert SleWindowIdentity.key(row, list(IMPACT_FIELDS))
        assert row["classifier"] == classifier
        assert row["failure"] == failure

    @pytest.mark.parametrize("field", ("classifier", "failure"))
    @pytest.mark.parametrize("invalid", (None, 7, True, [], {}))
    def test_impact_identity_rejects_missing_or_non_string_values(self, field: str, invalid: object) -> None:
        """Reject absent or non-string response identity values before persistence."""
        row: dict[str, object] = {
            "site_id": "site-1",
            "scope": "site",
            "scope_id": "scope-1",
            "metric": "coverage",
            "classifier": "low-rssi",
            "failure": "bad",
            "start": 100,
            "end": 200,
        }
        row[field] = invalid
        with pytest.raises(ValueError, match="SLE"):
            SleWindowIdentity.key(row, list(IMPACT_FIELDS))

    @pytest.mark.parametrize("boundary", (None, True, -1, float("nan"), float("inf"), "", "not-a-number"))
    def test_invalid_boundaries_are_rejected(self, boundary: object) -> None:
        """Reject missing, nonnumeric, nonfinite, and negative response boundaries."""
        row = {
            "site_id": "site-1",
            "scope": "site",
            "scope_id": "scope-1",
            "metric": "coverage",
            "start": boundary,
            "end": 200,
        }
        with pytest.raises(ValueError, match="SLE"):
            SleWindowIdentity.key(row, list(HISTOGRAM_FIELDS))

    def test_reversed_boundaries_are_rejected(self) -> None:
        """Reject a window whose returned end precedes its start."""
        row = {
            "site_id": "site-1",
            "scope": "site",
            "scope_id": "scope-1",
            "metric": "coverage",
            "start": 201,
            "end": 200,
        }
        with pytest.raises(ValueError, match="SLE"):
            SleWindowIdentity.key(row, list(HISTOGRAM_FIELDS))

    def test_equal_numeric_boundaries_share_a_key(self) -> None:
        """Canonicalize equivalent supported numeric values."""
        row = {
            "site_id": "site-1",
            "scope": "site",
            "scope_id": "scope-1",
            "metric": "coverage",
            "start": 100,
            "end": 200,
        }
        key = SleWindowIdentity.key(row, list(HISTOGRAM_FIELDS))
        equivalent = {**row, "start": 100.0, "end": "200.00"}
        assert SleWindowIdentity.key(equivalent, list(HISTOGRAM_FIELDS)) == key

    @pytest.mark.parametrize(
        ("operation", "response"),
        (
            (
                HISTOGRAM_OPERATION,
                {
                    "site_id": "response-site",
                    "scope": "response-scope",
                    "scope_id": "response-id",
                    "metric": "response-metric",
                    "start": 100,
                    "end": 200,
                    "data": [],
                    "x_label": "bucket",
                    "y_label": "count",
                },
            ),
            (
                IMPACT_OPERATION,
                {
                    "site_id": "response-site",
                    "scope": "response-scope",
                    "scope_id": "response-id",
                    "metric": "response-metric",
                    "classifier": "",
                    "failure": "bad",
                    "start": 100,
                    "end": 200,
                    "ap": [],
                    "wlan": [],
                    "device_os": [],
                    "device_type": [],
                    "band": [],
                },
            ),
        ),
    )
    def test_export_uses_selected_path_values_and_response_window(
        self, operation: str, response: dict[str, object]
    ) -> None:
        """Override response source dimensions while retaining its window and content."""
        writer = MagicMock()
        host = SimpleNamespace(DataExporter=SimpleNamespace(write_with_format_selection=writer))
        arguments = {
            "site_id": "selected-site",
            "scope": "site",
            "scope_id": "selected-scope",
            "metric": "coverage",
            "start": "50",
            "end": "250",
            "classifier": "query-classifier",
            "failure": "query-failure",
        }
        with patch.object(EndpointFamilyExporter, "_mist_helper", return_value=host):
            written = EndpointFamilyExporter._persist(response, "summary.csv", operation, arguments)
        assert written == 1
        exported = writer.call_args.args[0][0]
        assert (exported["site_id"], exported["scope"], exported["scope_id"], exported["metric"]) == (
            "selected-site",
            "site",
            "selected-scope",
            "coverage",
        )
        assert (exported["start"], exported["end"]) == (100, 200)
        if operation == IMPACT_OPERATION:
            assert (exported["classifier"], exported["failure"]) == ("", "bad")

    @pytest.mark.parametrize("operation", (HISTOGRAM_OPERATION, IMPACT_OPERATION))
    def test_missing_selected_dimension_rejects_response_fallback(self, operation: str) -> None:
        """Do not accept response dimensions when the selected request omitted them."""
        response = {
            "site_id": "response-site",
            "scope": "site",
            "scope_id": "response-scope",
            "metric": "coverage",
            "start": 100,
            "end": 200,
            "classifier": "",
            "failure": "",
        }
        writer = MagicMock()
        host = SimpleNamespace(DataExporter=SimpleNamespace(write_with_format_selection=writer))
        arguments = {"scope": "site", "scope_id": "selected-scope", "metric": "coverage"}
        with (
            patch.object(EndpointFamilyExporter, "_mist_helper", return_value=host),
            pytest.raises(ValueError, match="site_id"),
        ):
            EndpointFamilyExporter._persist(response, "summary.csv", operation, arguments)
        writer.write_with_format_selection.assert_not_called()

    @pytest.mark.parametrize("operation", (HISTOGRAM_OPERATION, IMPACT_OPERATION))
    def test_invalid_row_prevents_the_entire_export(self, operation: str) -> None:
        """Reject a mixed response batch before the exporter calls either backend."""
        writer = MagicMock()
        host = SimpleNamespace(DataExporter=SimpleNamespace(write_with_format_selection=writer))
        arguments = {
            "site_id": "site-1",
            "scope": "site",
            "scope_id": "scope-1",
            "metric": "coverage",
        }
        valid = {"start": 100, "end": 200}
        invalid = {"start": 100}
        if operation == IMPACT_OPERATION:
            valid.update(classifier="", failure="")
            invalid.update(classifier="", failure="")
        with (
            patch.object(EndpointFamilyExporter, "_mist_helper", return_value=host),
            pytest.raises(ValueError, match="SLE"),
        ):
            EndpointFamilyExporter._persist([valid, invalid], "summary.csv", operation, arguments)
        writer.write_with_format_selection.assert_not_called()

    @pytest.mark.parametrize("operation", (HISTOGRAM_OPERATION, IMPACT_OPERATION))
    def test_empty_response_keeps_no_data_behavior(self, operation: str) -> None:
        """Keep empty endpoint results from creating output records."""
        writer = MagicMock()
        host = SimpleNamespace(DataExporter=SimpleNamespace(write_with_format_selection=writer))
        with patch.object(EndpointFamilyExporter, "_mist_helper", return_value=host):
            written = EndpointFamilyExporter._persist([], "summary.csv", operation, {})
        assert written == 0
        writer.write_with_format_selection.assert_not_called()
