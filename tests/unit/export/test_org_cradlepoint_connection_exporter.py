"""Tests for OrgCradlepointConnectionExporter (spec 905, issue #1413).

The suite proves four behaviors that the menu depends on:

1. The status call reads ``response.data`` and tolerates a body that is not a
   dict, because the endpoint returns one object and is not paginated.
2. The row builder tags the row with the org and flattens the fields.
3. The write reaches ``write_with_format_selection`` with the exact
   operationId, and an empty result writes nothing.
4. The menu entry point keeps every failure inside the menu.
5. The transport status gate of issue #3819 refuses every HTTP result that it
   cannot trust, and it never invents a success value.

Every Mist call is mocked, so no test reaches the live cloud.
"""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.operations.exporting.export.org_cradlepoint_connection_exporter import OrgCradlepointConnectionExporter
from src.operations.exporting.export.org_cradlepoint_connection_exporter import (
    OrgCradlepointConnectionExporter as FailureModeOrgCradlepointConnectionExporter,
)

ORG_ID = "org-1413"
MODULE = "src.operations.exporting.export.org_cradlepoint_connection_exporter"
STATUS_URL = "https://api.mist.com/api/v1/orgs/org-1413/setting/cradlepoint/setup"


@pytest.fixture
def mist_helper(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Stand in for the lazily imported MistHelper module.

    The exporter calls ``SourceDependencyResolver``, which returns
    the entry in ``sys.modules`` when one is present. Replacing that entry keeps
    the stub local to the test.
    """
    stub = MagicMock()
    stub.apisession = MagicMock()
    monkeypatch.setitem(sys.modules, "MistHelper", stub)
    return stub


def sdk_response(status_code: int, payload: dict[str, str]) -> object:
    """Build a real SDK response so HTTP refusal handling matches production."""
    from mistapi.__api_response import APIResponse  # Keep this lazy so analysis includes the full test module.

    response = requests.Response()
    response.status_code = status_code
    response.url = STATUS_URL
    response._content = json.dumps(payload).encode()
    response.headers["Content-Type"] = "application/json"
    return APIResponse(response=response, url=STATUS_URL)


class TestFetch:
    """The status call must read the body and tolerate a wrong shape."""

    def test_reads_response_data(self, mist_helper: MagicMock) -> None:
        """A dict body reaches the caller unchanged."""
        body = {"last_status": "active", "error": ""}
        with patch(
            f"{MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection",
            return_value=SimpleNamespace(status_code=200, data=body),
        ) as call:
            assert OrgCradlepointConnectionExporter._fetch(ORG_ID) == body

        call.assert_called_once_with(mist_helper.apisession, ORG_ID)

    @pytest.mark.parametrize("body", [None, [], "error", 42])
    def test_a_non_dict_body_becomes_an_empty_dict(self, mist_helper: MagicMock, body: Any) -> None:
        """Only a dict body can hold the status, so any other shape is empty."""
        with patch(
            f"{MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection",
            return_value=SimpleNamespace(status_code=200, data=body),
        ):
            assert OrgCradlepointConnectionExporter._fetch(ORG_ID) == {}


class TestBuildRow:
    """The row builder must tag the org and flatten the fields."""

    def test_tags_the_org_and_flattens(self) -> None:
        """The org column joins the status fields and a nested value flattens."""
        payload = {"last_status": "active", "error": "keys are invalid", "extra": {"a": 1}}

        rows = OrgCradlepointConnectionExporter._build_row(ORG_ID, payload)

        assert len(rows) == 1
        assert rows[0]["org_id"] == ORG_ID
        assert rows[0]["last_status"] == "active"
        assert not any(isinstance(value, (dict, list)) for value in rows[0].values())

    def test_an_empty_body_builds_no_row(self) -> None:
        """An absent body has nothing to write."""
        assert OrgCradlepointConnectionExporter._build_row(ORG_ID, {}) == []


class TestPersist:
    """The write must reach the shared selector with the right operationId."""

    def test_writes_through_the_selector(self, mist_helper: MagicMock) -> None:
        """The operationId decides the primary-key strategy, so it must be exact."""
        OrgCradlepointConnectionExporter._persist([{"last_status": "active"}], "OrgCradlepointConnection_x.csv")

        mist_helper.DataExporter.write_with_format_selection.assert_called_once()
        kwargs = mist_helper.DataExporter.write_with_format_selection.call_args.kwargs
        assert kwargs["api_function_name"] == "testOrgCradlepointConnection"

    def test_no_rows_writes_nothing(self, mist_helper: MagicMock) -> None:
        """An empty result reports plainly instead of writing an empty file."""
        OrgCradlepointConnectionExporter._persist([], "OrgCradlepointConnection_x.csv")

        mist_helper.DataExporter.write_with_format_selection.assert_not_called()
        assert not mist_helper.DataExporter.write_with_format_selection.called  # Empty rows must not trigger a write.


class TestStatusMenu:
    """The menu entry point must keep every failure inside the menu."""

    def test_happy_path_writes_one_row(self, mist_helper: MagicMock) -> None:
        """A status body reaches the writer as one flattened row."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        with patch(
            f"{MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection",
            return_value=SimpleNamespace(status_code=200, data={"last_status": "active", "error": ""}),
        ):
            OrgCradlepointConnectionExporter.status()

        mist_helper.DataExporter.write_with_format_selection.assert_called_once()
        assert (
            len(mist_helper.DataExporter.write_with_format_selection.call_args.args[0]) == 1
        )  # The valid response must produce one row.
        assert (
            mist_helper.DataExporter.write_with_format_selection.call_args.args[0][0]["org_id"] == ORG_ID
        )  # The row must identify its organization.
        assert (
            mist_helper.DataExporter.write_with_format_selection.call_args.args[0][0]["last_status"] == "active"
        )  # The row must retain the returned status.

    def test_http_200_configuration_error_is_exported(self, mist_helper: MagicMock) -> None:
        """A valid HTTP 200 status can report its own Cradlepoint configuration error."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        response = sdk_response(200, {"last_status": "inactive", "error": "keys are invalid"})
        with patch(
            f"{MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection",
            return_value=response,
        ):
            FailureModeOrgCradlepointConnectionExporter.status()

        mist_helper.DataExporter.write_with_format_selection.assert_called_once()
        rows = mist_helper.DataExporter.write_with_format_selection.call_args.args[0]
        assert rows[0]["error"] == "keys are invalid"

    def test_no_org_returns_early(self, mist_helper: MagicMock) -> None:
        """A cancelled org prompt must not call the Mist API."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ""

        with patch(f"{MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection") as call:
            OrgCradlepointConnectionExporter.status()

        call.assert_not_called()
        assert call.call_count == 0  # An empty organization must stop before the API call.

    def test_an_empty_body_writes_nothing(self, mist_helper: MagicMock) -> None:
        """A body that is not a dict is legitimate, so nothing is written."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        with patch(
            f"{MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection",
            return_value=SimpleNamespace(status_code=200, data=None),
        ):
            OrgCradlepointConnectionExporter.status()

        mist_helper.DataExporter.write_with_format_selection.assert_not_called()
        assert not mist_helper.DataExporter.write_with_format_selection.called  # Missing data must not trigger a write.

    def test_an_sdk_error_never_escapes(self, mist_helper: MagicMock) -> None:
        """A network failure must return to the menu, not end the session."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        with patch(
            f"{MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection",
            side_effect=RuntimeError("connection reset"),
        ):
            OrgCradlepointConnectionExporter.status()

        mist_helper.DataExporter.write_with_format_selection.assert_not_called()
        assert not mist_helper.DataExporter.write_with_format_selection.called  # Failed requests must not write.

    @pytest.mark.parametrize("status_code", [403, 503])
    def test_http_refusal_response_is_rejected_before_export(
        self,
        mist_helper: MagicMock,
        caplog: pytest.LogCaptureFixture,
        status_code: int,
    ) -> None:
        """A refused SDK response must not become a successful export."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        refused = sdk_response(status_code, {"detail": f"controlled HTTP {status_code} refusal"})
        with patch(
            f"{MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection",
            return_value=refused,
        ):
            with caplog.at_level("ERROR"):
                FailureModeOrgCradlepointConnectionExporter.status()

        assert f"HTTP {status_code}" in caplog.text
        assert "controlled HTTP" not in caplog.text
        mist_helper.DataExporter.write_with_format_selection.assert_not_called()

    @pytest.mark.parametrize("status_code", [404, 503])
    def test_cradlepoint_http_status_sdk_error_is_logged(
        self, mist_helper: MagicMock, caplog: pytest.LogCaptureFixture, status_code: int
    ) -> None:
        """An HTTP 404 or HTTP 503 SDK failure must be logged and contained."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID  # Reach the API call.
        error = RuntimeError(f"HTTP {status_code}")  # Preserve the cloud status in the SDK error.
        with patch(
            f"{MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection",
            side_effect=error,
        ):
            with caplog.at_level("ERROR"):  # Capture the product error signal.
                FailureModeOrgCradlepointConnectionExporter.status()  # Call the real exporter entry point from src.

        assert f"HTTP {status_code}" in caplog.text  # Prove the operator can see the status.
        assert "Error fetching the Cradlepoint status" in caplog.text  # Prove the product logged the failure.
        mist_helper.DataExporter.write_with_format_selection.assert_not_called()  # Failed calls must not write.


class TestTransportStatusGate:
    """Issue #3819: an untrustworthy HTTP transport status must never write a row.

    Before the repair the exporter changed an absent ``status_code`` to ``200``
    and accepted ``None``, a string, a float, ``True``, ``False``, ``1xx``, and
    ``3xx``. A payload of ``last_status: active`` then reached CSV and SQLite
    although the HTTP result was unknown. Each test here proves that the
    exporter now binds the condition, names it in the log, and writes nothing.
    """

    ACTIVE_BODY = {"last_status": "active", "error": ""}  # The payload that must never escape a blind gate.

    @staticmethod
    def _run_status(mist_helper: MagicMock, response: object) -> None:
        """Drive the menu entry point against one controlled SDK response double.

        Args:
            mist_helper: The MistHelper stub that owns the org prompt and the writer.
            response: The SDK response double that carries the transport status under test.
        """
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID  # Reach the API call.
        with patch(  # Replace the SDK call so no test reaches the live cloud.
            f"{MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection",
            return_value=response,
        ):
            FailureModeOrgCradlepointConnectionExporter.status()  # Call the real exporter entry point from src.

    def _writer_of(self, mist_helper: MagicMock) -> MagicMock:
        """Return the export writer so each test can prove that no row escaped.

        Args:
            mist_helper: The MistHelper stub whose writer must stay untouched.

        Returns:
            The writer mock, so each caller can add its own explicit assertions.
        """
        return mist_helper.DataExporter.write_with_format_selection  # Bind the writer for the caller checks.

    def test_an_absent_transport_status_is_refused(
        self, mist_helper: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A response with no ``status_code`` must not be read as HTTP 200."""
        response = SimpleNamespace(data=dict(self.ACTIVE_BODY))  # No status_code attribute at all.
        with caplog.at_level("ERROR"):  # Capture the product refusal signal.
            self._run_status(mist_helper, response)
        assert "outcome=absent" in caplog.text  # The refusal must carry an explicit, named outcome.
        assert "no HTTP transport status" in caplog.text  # The log must state the condition in plain words.
        assert not self._writer_of(mist_helper).called  # An untrustworthy status must never reach persistence.
        assert "active" not in str(self._writer_of(mist_helper).call_args_list)  # No false active row was written.

    @pytest.mark.parametrize("status_code", [None, "200", "", 200.0, [200]])
    def test_a_malformed_transport_status_is_refused(
        self, mist_helper: MagicMock, caplog: pytest.LogCaptureFixture, status_code: Any
    ) -> None:
        """A ``None`` or non-integer ``status_code`` carries no usable HTTP result."""
        response = SimpleNamespace(status_code=status_code, data=dict(self.ACTIVE_BODY))  # Malformed transport value.
        with caplog.at_level("ERROR"):  # Capture the product refusal signal.
            self._run_status(mist_helper, response)
        assert "outcome=malformed" in caplog.text  # The refusal must carry an explicit, named outcome.
        assert type(status_code).__name__ in caplog.text  # The log must name the type it refused.
        assert not self._writer_of(mist_helper).called  # An untrustworthy status must never reach persistence.
        assert "active" not in str(self._writer_of(mist_helper).call_args_list)  # No false active row was written.

    @pytest.mark.parametrize("status_code", [True, False])
    def test_a_boolean_transport_status_is_refused(
        self, mist_helper: MagicMock, caplog: pytest.LogCaptureFixture, status_code: bool
    ) -> None:
        """``bool`` is an ``int`` subclass, so a plain integer test accepts it by accident."""
        response = SimpleNamespace(status_code=status_code, data=dict(self.ACTIVE_BODY))  # Boolean transport value.
        with caplog.at_level("ERROR"):  # Capture the product refusal signal.
            self._run_status(mist_helper, response)
        assert "outcome=malformed" in caplog.text  # A boolean is not an HTTP status.
        assert "of type bool" in caplog.text  # The log must name bool, not treat it as an integer status.
        assert not self._writer_of(mist_helper).called  # An untrustworthy status must never reach persistence.
        assert "active" not in str(self._writer_of(mist_helper).call_args_list)  # No false active row was written.

    @pytest.mark.parametrize("status_code", [100, 199, 300, 302, 399])
    def test_a_non_success_transport_status_is_refused(
        self, mist_helper: MagicMock, caplog: pytest.LogCaptureFixture, status_code: int
    ) -> None:
        """A 1xx or 3xx result is not a completed success, so no row may be written."""
        response = SimpleNamespace(status_code=status_code, data=dict(self.ACTIVE_BODY))  # Non-success transport value.
        with caplog.at_level("ERROR"):  # Capture the product refusal signal.
            self._run_status(mist_helper, response)
        assert "outcome=out-of-range" in caplog.text  # The refusal must carry an explicit, named outcome.
        assert f"HTTP {status_code}" in caplog.text  # The operator must read the exact status.
        assert not self._writer_of(mist_helper).called  # An untrustworthy status must never reach persistence.
        assert "active" not in str(self._writer_of(mist_helper).call_args_list)  # No false active row was written.

    @pytest.mark.parametrize("status_code", [200, 204, 299])
    def test_a_success_transport_status_reaches_the_writer(self, mist_helper: MagicMock, status_code: int) -> None:
        """A trustworthy 2xx result keeps the existing export behavior unchanged."""
        response = SimpleNamespace(status_code=status_code, data=dict(self.ACTIVE_BODY))  # Trustworthy transport value.
        self._run_status(mist_helper, response)
        writer = mist_helper.DataExporter.write_with_format_selection  # Bind the writer for the two checks below.
        writer.assert_called_once()  # A valid 2xx status must still export exactly one row.
        assert writer.call_args.args[0][0]["last_status"] == "active"  # The payload must pass through unchanged.

    def test_a_refusal_never_logs_the_response_body(
        self, mist_helper: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A refusal reports the condition only, so a controlled body never reaches the log."""
        secret_body = {"last_status": "active", "error": "controlled-body-marker"}  # A marker that must not be logged.
        response = SimpleNamespace(status_code="unusable-status-marker", data=secret_body)  # Malformed value and body.
        with caplog.at_level("DEBUG"):  # Capture every record, so a leak at any level fails this test.
            self._run_status(mist_helper, response)
        assert "controlled-body-marker" not in caplog.text  # The response body must never reach the log.
        assert "unusable-status-marker" not in caplog.text  # The unusable value itself must never reach the log.
        assert "outcome=malformed" in caplog.text  # The refusal must still name its outcome.
