"""Direct fail-capable decisions and metadata contracts for issue #3699."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any
from unittest.mock import call, patch

import pytest
from mistapi import APISession
from mistapi.__api_response import APIResponse
from mistapi.api.v1.sites import sle

from src.export.endpoint_family_exporter import (
    _SITE_SLE_OPS,
    EndpointFamilyExporter,
    _EndpointArgumentSet,
    _EndpointFamilyOp,
)
from src.export.endpoint_family_response.reader import EndpointFamilyResponseReader
from src.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES
from tests.unit.export.test_endpoint_family_exporter import GROUPS
from tests.unit.export.trend_object_export.conftest import (
    local_trend_context as local_trend_context,
)
from tests.unit.export.trend_object_export.conftest import (
    local_trend_environment as local_trend_environment,
)
from tests.unit.export.trend_object_export.conftest import (
    local_trend_session as local_trend_session,
)
from tests.unit.export.trend_object_export.conftest import (
    native_failure as native_failure,
)
from tests.unit.export.trend_object_export.conftest import (
    native_trend_run as native_trend_run,
)
from tests.unit.export.trend_object_export.conftest import (
    trend_document as trend_document,
)
from tests.unit.export.trend_object_export.conftest import (
    trend_sdk_absence as trend_sdk_absence,
)
from tests.unit.export.trend_object_export.conftest import (
    trend_sdk_logging as trend_sdk_logging,
)
from tests.unit.export.trend_object_export.native_transport import (
    NativeBoundaries,
    NativeResponseFactory,
    NativeTrendTransport,
    WireScenario,
)


class ResponseBodyReadGuard:
    """Count public body-field reads on one actual native response."""

    @staticmethod
    def inspect(response: object, name: str) -> Any:
        """Reject body reads on the marked instance without replacing its native fields."""
        fields = object.__getattribute__(response, "__dict__")
        if "checked_body_reads" in fields and name in ("data", "raw_data", "next"):
            fields["checked_body_reads"] += 1
            raise AssertionError("The caller read a refused response body.")
        return object.__getattribute__(response, name)


class TestGuardDecisions:
    """Use actual output decisions to prove both guards can fail."""

    @staticmethod
    def _require_document(boundaries: NativeBoundaries) -> None:
        """Check one native document at the real output callback and persisted row."""
        document = boundaries.document
        count = boundaries.writer.call_count
        message = f"Checked 1 native document: {count} output callbacks."
        print(message)
        assert boundaries.writer.call_args_list == [
            call([document.expected], document.target.filename, api_function_name=document.target.operation)
        ], message
        with (Path("data") / document.target.filename).open(encoding="utf-8", newline="") as stream:
            assert list(csv.DictReader(stream)) == [
                {key: str(value) for key, value in document.expected.items()}
            ], message

    @staticmethod
    def _require_refusal(boundaries: NativeBoundaries) -> None:
        """Check the actual number of unintended output callbacks."""
        count = boundaries.writer.call_count
        message = f"Checked 1 refused response: {count} output callbacks."
        print(message)
        assert boundaries.writer.call_args_list == [], message
        assert list(Path("data").glob(boundaries.document.target.filename)) == [], message

    def test_document_guard_accepts_real_output(self, native_trend_run: NativeBoundaries) -> None:
        """The same guard accepts the unmodified actual exporter journey."""
        EndpointFamilyExporter.site_sle_endpoints()
        self._require_document(native_trend_run)
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(native_trend_run.document)
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    def test_document_guard_fails_when_object_retention_is_removed(
        self, native_trend_run: NativeBoundaries, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Removing the actual object decision must fail the persisted-output guard."""
        monkeypatch.setattr(
            EndpointFamilyResponseReader, "_unpaged_rows", classmethod(lambda _cls, _response, _contract, _page: [])
        )
        EndpointFamilyExporter.site_sle_endpoints()
        with pytest.raises(AssertionError, match="Checked 1 native document: 0 output callbacks"):
            self._require_document(native_trend_run)
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(native_trend_run.document)
        assert native_trend_run.writer.call_args_list == []
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    def test_refusal_guard_fails_when_status_validation_is_bypassed(
        self, native_trend_run: NativeBoundaries, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A bypassed status decision must fail the same real no-output guard."""
        document = native_trend_run.document
        native_trend_run.transport.responses[document.target.uri] = NativeResponseFactory.make(
            document.target.uri, WireScenario(403, {"error": "controlled refusal"})
        )
        monkeypatch.setattr(EndpointFamilyResponseReader, "_validate", staticmethod(lambda _response, _operation: None))
        EndpointFamilyExporter.site_sle_endpoints()
        with pytest.raises(AssertionError, match="Checked 1 refused response: 1 output callbacks"):
            self._require_refusal(native_trend_run)
        assert native_trend_run.writer.call_count == 1
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)


class TestResponseContracts:
    """Retain exact raw data, SDK routing, and key metadata while refusing failures."""

    @pytest.mark.parametrize("status", (403, 500, None))
    def test_status_precedes_all_public_body_fields(
        self, native_trend_run: NativeBoundaries, status: int | None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A refused native response must produce zero body reads and zero writes."""
        document = native_trend_run.document
        response = APIResponse(None, NativeResponseFactory.HOST + document.target.uri)
        response.status_code = status
        response.__dict__["checked_body_reads"] = 0
        native_trend_run.transport.responses[document.target.uri] = response
        monkeypatch.setattr(APIResponse, "__getattribute__", ResponseBodyReadGuard.inspect)
        EndpointFamilyExporter.site_sle_endpoints()
        assert response.__dict__["checked_body_reads"] == 0, "Checked 1 refused response. Its body must have 0 reads."
        assert native_trend_run.writer.call_args_list == []
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)


class TestCallerObjectPolicy:
    """Exercise every real family caller and SDK target with an explicit object contract."""

    @pytest.mark.parametrize(
        "caller,entry",
        [
            (caller, entry)
            for caller, group in (
                ("site_sle_endpoints", "SITE_SLE"),
                ("site_map_endpoints", "SITE_MAP"),
                ("site_detail_endpoints", "SITE_DETAIL"),
                ("org_detail_endpoints", "ORG_DETAIL"),
                ("msp_detail_endpoints", "MSP_DETAIL"),
                ("other_endpoints", "OTHER_DETAIL"),
            )
            for entry in GROUPS[group]
        ],
        ids=lambda value: value.operation if hasattr(value, "operation") else str(value),
    )
    def test_only_two_real_sdk_operations_receive_object_permission(
        self, native_trend_run: NativeBoundaries, local_trend_session: APISession, caller: str, entry: _EndpointFamilyOp
    ) -> None:
        """Execute actual SDK functions and prove every other operation retains zero object writes."""
        document = native_trend_run.document
        native = APIResponse(
            NativeResponseFactory.make("/api/v1/policy", WireScenario(200, document.payload)), "/api/v1/policy"
        )
        values = tuple(f"{name}-value" for name in entry.required)
        position = next(group.index(entry) + 1 for group in GROUPS.values() if entry in group)
        with (
            patch("builtins.input", return_value=str(position)),
            patch.object(
                EndpointFamilyExporter, "_collect_arguments", return_value=_EndpointArgumentSet(values, "policy")
            ),
            patch.object(local_trend_session, "mist_get", return_value=native) as get,
            patch.object(local_trend_session, "mist_post", return_value=native) as post,
        ):
            getattr(EndpointFamilyExporter, caller)()
        permitted = entry.operation in ("getSiteSleSummaryTrend", "getSiteSleClassifierSummaryTrend")
        assert get.call_count + post.call_count == 1
        result_call = call([document.expected], f"{entry.operation}_policy.csv", api_function_name=entry.operation)
        expected = [result_call] if permitted else []
        assert native_trend_run.writer.call_args_list == expected, f"Checked 1 real SDK operation: {entry.operation}."
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    def test_deprecated_sdk_absence_keeps_trend_metadata_exact(
        self, native_trend_run: NativeBoundaries, trend_sdk_absence: bool
    ) -> None:
        """The real retained operation keeps its routing and unchanged strategy."""
        target = native_trend_run.document.target
        entry = next(row for row in _SITE_SLE_OPS if row.operation == target.operation)
        assert EndpointFamilyExporter._resolve(entry) is getattr(sle, target.operation)
        assert not hasattr(EndpointFamilyExporter, "_normalize")
        assert ENDPOINT_PRIMARY_KEY_STRATEGIES[target.operation] == {
            "type": "auto_increment_with_unique",
            "primary_key": ["misthelper_internal_id"],
            "indexes": list(entry.required),
            "unique_constraints": [],
            "description": "Endpoint family export for " + target.operation,
        }
        EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.writer.call_args_list == [
            call([native_trend_run.document.expected], target.filename, api_function_name=target.operation)
        ]
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(native_trend_run.document)
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    def test_failure_modes_preserve_the_no_output_contract(
        self, native_trend_run: NativeBoundaries, native_failure: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Every actual failure must satisfy the same output guard."""
        EndpointFamilyExporter.site_sle_endpoints()
        TestGuardDecisions._require_refusal(native_trend_run)
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(native_trend_run.document)
        assert "Error running" in caplog.text and native_trend_run.document.target.operation in caplog.text
        assert "source-body-marker-3699" not in caplog.text and "credential-marker-3699" not in caplog.text
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)
