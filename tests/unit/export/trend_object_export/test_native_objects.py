"""Native documented-object regressions for the real exporter and CSV writer."""

from __future__ import annotations

import csv
import logging
from copy import deepcopy
from pathlib import Path
from unittest.mock import call

import pytest

from src.export.endpoint_family_exporter import EndpointFamilyExporter
from src.export.endpoint_family_response.reader import EndpointFamilyResponseReader
from tests.unit.export.trend_object_export.documents import RICH_DOCUMENTS
from tests.unit.export.trend_object_export.native_transport import (
    NativeBoundaries,
    NativeResponseFactory,
    NativeTrendTransport,
    WireScenario,
)


class TestDocumentedRecords:
    """Prove both literal documents at the persisted record, not a helper result."""

    def test_documented_object_reaches_selected_csv(
        self, native_trend_run: NativeBoundaries, trend_sdk_absence: bool
    ) -> None:
        """Both native operations must write one complete record with the exact routing identifier."""
        document = native_trend_run.document
        EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert [(response.status_code, response.next) for response in native_trend_run.transport.decoded] == [
            (200, None),
            (200, None),
        ]
        assert native_trend_run.transport.decoded[-1].data == document.payload
        assert native_trend_run.writer.call_args_list == [
            call([document.expected], document.target.filename, api_function_name=document.target.operation)
        ], f"Checked 1 native {document.target.operation} object. It must reach exactly 1 output callback."
        path = Path("data") / document.target.filename
        with path.open(encoding="utf-8", newline="") as stream:
            records = list(csv.DictReader(stream))
        assert records == [{key: str(value) for key, value in document.expected.items()}]
        assert path.stat().st_size > 100
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    def test_nonempty_samples_and_nested_classifiers_reach_selected_csv(
        self, native_trend_run: NativeBoundaries, trend_sdk_absence: bool
    ) -> None:
        """Every nonempty sample and nested classifier must survive actual flattening and escaping."""
        document = next(case for case in RICH_DOCUMENTS if case.target == native_trend_run.document.target)
        uri = document.target.uri
        native_trend_run.transport.responses[uri] = NativeResponseFactory.make(uri, WireScenario(200, document.payload))
        EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.writer.call_args_list == [
            call([document.expected], document.target.filename, api_function_name=document.target.operation)
        ]
        with (Path("data") / document.target.filename).open(encoding="utf-8", newline="") as stream:
            assert list(csv.DictReader(stream)) == [{key: str(value) for key, value in document.expected.items()}]
        assert native_trend_run.transport.decoded[-1].data == document.payload
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    @pytest.mark.parametrize("error_value", ("normal measurement", 0, False))
    def test_http_200_error_like_fields_remain_metrics(
        self, native_trend_run: NativeBoundaries, error_value: str | int | bool, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An error field cannot replace the actual successful HTTP status decision."""
        document = native_trend_run.document
        payload, expected = deepcopy(document.payload), {**document.expected, "error": error_value}
        payload["error"] = error_value
        native_trend_run.transport.responses[document.target.uri] = NativeResponseFactory.make(
            document.target.uri, WireScenario(200, payload)
        )
        EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.writer.call_args_list == [
            call([expected], document.target.filename, api_function_name=document.target.operation)
        ]
        assert [
            record.getMessage() for record in caplog.records if record.name.startswith("src.") and record.levelno >= 40
        ] == []
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    def test_oversized_unicode_empty_and_none_metric_values_remain_data(
        self, native_trend_run: NativeBoundaries
    ) -> None:
        """Large and Unicode fields must retain their values without becoming response failures."""
        document = native_trend_run.document
        details = {"unicode": "caf\u00e9", "oversized": "x" * 8192, "empty": "", "none": None}
        payload = {**document.payload, "details": details}
        expected = {**document.expected, **{f"details_{key}": value for key, value in details.items()}}
        native_trend_run.transport.responses[document.target.uri] = NativeResponseFactory.make(
            document.target.uri, WireScenario(200, payload)
        )
        EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.writer.call_args_list == [
            call([expected], document.target.filename, api_function_name=document.target.operation)
        ]
        with (Path("data") / document.target.filename).open(encoding="utf-8", newline="") as stream:
            assert list(csv.DictReader(stream)) == [
                {key: "" if value is None else str(value) for key, value in expected.items()}
            ]
        assert (Path("data") / document.target.filename).stat().st_size > 8192
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)


class TestEmptyAndPageRecords:
    """Preserve genuine empty results and successful native pagination."""

    @pytest.mark.parametrize("empty", ([], {}, {"results": []}, None))
    def test_empty_native_responses_skip_output(self, native_trend_run: NativeBoundaries, empty: object) -> None:
        """Valid empty JSON must retain the existing no-output behavior."""
        document = native_trend_run.document
        native_trend_run.transport.responses[document.target.uri] = NativeResponseFactory.make(
            document.target.uri, WireScenario(200, empty)
        )
        EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert native_trend_run.writer.call_args_list == []
        assert list(Path("data").glob(document.target.filename)) == []
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    @pytest.mark.parametrize("shape", ("list", "results"))
    def test_native_pagination_preserves_records_and_links(
        self, native_trend_run: NativeBoundaries, shape: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Use actual header and results next links without inventing header-total rules."""
        document = native_trend_run.document
        first, second = [{"summary": {"value": 42}, "note": "first\nline"}], [
            {"summary": {"value": 43}, "note": "next\rpage"}
        ]
        next_uri = native_trend_run.transport.paginated(document, shape, first, second)
        with caplog.at_level(logging.DEBUG, logger="src.export.endpoint_family_response.reader"):
            EndpointFamilyExporter.site_sle_endpoints()
        expected = [{"summary_value": 42, "note": "first\\nline"}, {"summary_value": 43, "note": "nextpage"}]
        assert native_trend_run.writer.call_args_list == [
            call(expected, document.target.filename, api_function_name=document.target.operation)
        ]
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document, next_uri)
        assert [response.next for response in native_trend_run.transport.decoded] == [None, next_uri, None]
        assert "Checked 2 responses" in caplog.text
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    @pytest.mark.parametrize(
        "raw,expected",
        ((None, []), ((), []), (({"summary": {"value": 42}},), [{"summary_value": 42}]), (0, [{"value": 0}])),
    )
    def test_tuple_and_scalar_persistence_keep_original_normalization(
        self, native_trend_run: NativeBoundaries, raw: object, expected: list[dict[str, object]]
    ) -> None:
        """The moved normalizer must preserve actual tuple and scalar persistence callers."""
        document = native_trend_run.document
        EndpointFamilyExporter._persist(raw, document.target.filename, document.target.operation)
        expected_calls = (
            [call(expected, document.target.filename, api_function_name=document.target.operation)] if expected else []
        )
        assert native_trend_run.writer.call_args_list == expected_calls
        assert native_trend_run.transport.calls == []
        if expected:
            with (Path("data") / document.target.filename).open(encoding="utf-8", newline="") as stream:
                assert list(csv.DictReader(stream)) == [
                    {key: str(value) for key, value in row.items()} for row in expected
                ]
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    def test_reader_and_normalizer_retain_raw_empty_classifier_array(self, native_trend_run: NativeBoundaries) -> None:
        """The raw document remains exact even when the established flattener omits its empty field."""
        document = native_trend_run.document
        EndpointFamilyExporter.site_sle_endpoints()
        native = native_trend_run.transport.decoded[-1]
        assert EndpointFamilyResponseReader.normalize(native.data) == [document.payload]
        assert native.data == document.payload
        assert native_trend_run.writer.call_args_list == [
            call([document.expected], document.target.filename, api_function_name=document.target.operation)
        ]
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)


class TestNativeFailureControls:
    """Keep native failures in the same source-dependent coverage as positive records."""

    def test_failure_modes_make_no_output(
        self, native_trend_run: NativeBoundaries, native_failure: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Timeout, connection, HTTP, malformed JSON, and empty bodies cannot reach the writer."""
        document = native_trend_run.document
        with caplog.at_level(logging.DEBUG, logger="src.export.endpoint_family_response.reader"):
            EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert native_trend_run.writer.call_args_list == []
        assert list(Path("data").glob(document.target.filename)) == []
        assert document.target.operation in caplog.text
        assert "Error running" in caplog.text
        assert "source-body-marker-3699" not in caplog.text
        assert "credential-marker-3699" not in caplog.text
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    @pytest.mark.parametrize("status", (403, 503))
    def test_http_status_failures_make_no_output(
        self, native_trend_run: NativeBoundaries, status: int, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Exercise concrete client and server statuses in this source-driven test module."""
        document = native_trend_run.document
        native_trend_run.transport.responses[document.target.uri] = NativeResponseFactory.make(
            document.target.uri, WireScenario(status=status, body={"error": "source-body-marker-3699"})
        )
        with caplog.at_level(logging.DEBUG, logger="src.export.endpoint_family_response.reader"):
            EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.transport.decoded[-1].status_code == status
        assert native_trend_run.writer.call_args_list == []
        assert list(Path("data").glob(document.target.filename)) == []
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert f"HTTP {status}" in caplog.text and "source-body-marker-3699" not in caplog.text
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)
