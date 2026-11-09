"""Verify license request and write outcomes without network or production data."""

from __future__ import annotations

import socket
import sqlite3
from collections.abc import Iterator
from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock

import pytest

from src.operations.exporting.export import org_admin_exporter as module


@pytest.fixture(autouse=True)
def blocked_network(monkeypatch: pytest.MonkeyPatch) -> Iterator[MagicMock]:
    """Reject sockets, DNS, and SQLite and prove that the tests attempt none."""
    blocked = MagicMock(side_effect=AssertionError("Network access is forbidden"))  # Detect any network attempt.
    for name in ("socket", "create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr"):
        monkeypatch.setattr(socket, name, blocked)  # Prevent both address lookup and transport creation.
    monkeypatch.setattr(sqlite3, "connect", blocked)  # Prevent access to a production database.
    yield blocked  # Keep the guard active for the whole test.
    blocked.assert_not_called()  # A caught network error must not hide an attempted request.


@pytest.fixture(params=("direct", "wrapper"))
def license_case(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Provide both endpoint branches with synthetic responses and a writer double."""
    response = SimpleNamespace(status_code=200, data=[{"id": "license-1", "notes": "line\nnext"}])  # No real data.
    resolver = SimpleNamespace(  # Replace all runtime dependencies before the exporter runs.
        apisession=MagicMock(),
        ConfigUtils=MagicMock(),
        DataExporter=MagicMock(),
    )
    resolver.ConfigUtils.get_cached_or_prompted_org_id.return_value = "synthetic-org"  # Avoid operator and env reads.
    resolver.apisession.mist_get.return_value = response  # Keep the direct endpoint offline.
    resolver.DataExporter.write_with_format_selection.return_value = True  # Model a confirmed successful write.
    wrapper = MagicMock(return_value=response)  # Keep the optional SDK endpoint offline.
    sdk = SimpleNamespace(  # Model wrapper presence without changing the installed SDK.
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    licenses=(
                        SimpleNamespace(listOrgLicenses=wrapper) if request.param == "wrapper" else SimpleNamespace()
                    )
                )
            )
        ),
        get_all=MagicMock(side_effect=lambda response, **_options: response.data),
    )
    monkeypatch.setattr(module, "SourceDependencyResolver", resolver)  # Prevent production configuration access.
    monkeypatch.setattr(module, "mistapi", sdk)  # Prevent real API calls and pagination.
    return SimpleNamespace(response=response, resolver=resolver, sdk=sdk, wrapper=wrapper, branch=request.param)


class TestLicenseRequestStatus:
    """Reject failed initial responses before pagination, transformation, or output."""

    @pytest.mark.parametrize("status", (100, 302, 400, 403, 429, 500, 503, 599))
    @pytest.mark.parametrize("body", ({"error": "synthetic failure"}, {}))
    def test_http_failure(
        self, license_case: SimpleNamespace, caplog: pytest.LogCaptureFixture, status: int, body: dict[str, str]
    ) -> None:
        """An error body must never become a license record or an empty export."""
        license_case.response.status_code = status  # Exercise client, server, and other non-success statuses.
        license_case.response.data = body  # Cover both populated and empty error bodies.
        with caplog.at_level("INFO"), pytest.raises(RuntimeError, match=f"HTTP {status}"):
            module.OrgAdminExporter.licenses()  # Drive the public operation through the selected endpoint branch.
        license_case.resolver.DataExporter.write_with_format_selection.assert_not_called()  # No error output.
        license_case.sdk.get_all.assert_not_called()  # Reject the initial response before pagination.
        assert "synthetic-org" in caplog.text  # Identify the target without exposing the response body.
        assert "Exported" not in caplog.text and "writing empty" not in caplog.text  # No false success.

    @pytest.mark.parametrize("status", (None, "200", 200.0, True, False, -1, 0, 600, MagicMock()))
    def test_invalid_status(
        self, license_case: SimpleNamespace, status: object, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An unverified status must fail even when the response contains valid-looking rows."""
        license_case.response.status_code = status  # Numeric strings and Boolean values must not prove success.
        with caplog.at_level("INFO"), pytest.raises(RuntimeError):
            module.OrgAdminExporter.licenses()  # Keep the public error path observable.
        license_case.resolver.DataExporter.write_with_format_selection.assert_not_called()  # Never write bad data.
        license_case.sdk.get_all.assert_not_called()  # No unchecked initial response reaches pagination.
        assert "Failed to export licenses" in caplog.text  # Report a failure instead of silently ignoring it.
        assert "Exported" not in caplog.text  # Do not advertise a file that has no verified source.

    def test_missing_status(self, license_case: SimpleNamespace, caplog: pytest.LogCaptureFixture) -> None:
        """A missing status must not use a success default."""
        del license_case.response.status_code  # Model an incomplete SDK response.
        with caplog.at_level("INFO"), pytest.raises(RuntimeError, match="status"):
            module.OrgAdminExporter.licenses()  # Missing metadata cannot establish successful retrieval.
        license_case.resolver.DataExporter.write_with_format_selection.assert_not_called()  # No recovery write.
        license_case.sdk.get_all.assert_not_called()  # No pagination without initial validation.
        assert "Exported" not in caplog.text  # Preserve truthful operator feedback.

    def test_does_not_read_failed_body(self, license_case: SimpleNamespace) -> None:
        """Status rejection must precede even a direct response body property read."""
        response = MagicMock(status_code=503)  # A body property records consumption independently of output.
        body = PropertyMock(side_effect=AssertionError("Failed body was consumed"))  # Reject premature reads.
        type(response).data = body  # Observe body access in either endpoint branch.
        license_case.resolver.apisession.mist_get.return_value = response  # Supply the direct response.
        license_case.wrapper.return_value = response  # Supply the wrapper response.
        with pytest.raises(RuntimeError, match="HTTP 503"):
            module.OrgAdminExporter.licenses()  # Stop before touching the untrusted payload.
        body.assert_not_called()  # Prove validation order rather than only the eventual writer count.


class TestLicenseWriteStatus:
    """Preserve valid output while reporting empty results and rejected writes correctly."""

    @pytest.mark.parametrize("status", (200, 201, 204, 299))
    def test_success(self, license_case: SimpleNamespace, caplog: pytest.LogCaptureFixture, status: int) -> None:
        """Both endpoints retain real flattening, newline escaping, metadata, and the public return."""
        license_case.response.status_code = status  # Cover both edges of the accepted status range.
        with caplog.at_level("INFO"):
            result = module.OrgAdminExporter.licenses()  # Integrate the real data processing helpers.
        assert result is None  # Preserve the public return contract.
        license_case.resolver.DataExporter.write_with_format_selection.assert_called_once_with(
            [{"id": "license-1", "notes": "line\\nnext"}], "OrgLicenses.csv", api_function_name="listOrgLicenses"
        )  # Keep normalized output and endpoint metadata unchanged.
        assert "Exported 1 license records to OrgLicenses.csv." in caplog.text  # Report confirmed output.
        if license_case.branch == "direct":
            license_case.resolver.apisession.mist_get.assert_called_once_with("/api/v1/orgs/synthetic-org/licenses")
            license_case.sdk.get_all.assert_not_called()  # Preserve direct-path behavior.
        else:
            license_case.wrapper.assert_called_once_with(license_case.resolver.apisession, "synthetic-org", limit=1000)
            license_case.sdk.get_all.assert_called_once_with(
                response=license_case.response, mist_session=license_case.resolver.apisession
            )  # Preserve existing SDK pagination without claiming later-page validation.

    @pytest.mark.parametrize("body", ([], None))
    def test_valid_empty(self, license_case: SimpleNamespace, caplog: pytest.LogCaptureFixture, body: object) -> None:
        """A valid empty response must not claim the shared writer created an empty file."""
        license_case.response.data = body  # Preserve the existing successful null-to-empty normalization.
        license_case.resolver.DataExporter.write_with_format_selection.return_value = False  # Empty input is rejected.
        with caplog.at_level("INFO"):
            result = module.OrgAdminExporter.licenses()  # Treat verified emptiness separately from failure.
        assert result is None  # A valid empty result is not a request error.
        license_case.resolver.DataExporter.write_with_format_selection.assert_not_called()  # No empty file promise.
        assert "No license records" in caplog.text  # Give the operator a truthful empty-result report.
        assert "Exported" not in caplog.text and "writing empty" not in caplog.text  # No false completion.

    def test_writer_false(self, license_case: SimpleNamespace, caplog: pytest.LogCaptureFixture) -> None:
        """An explicit writer rejection must report failure without changing the public return."""
        license_case.resolver.DataExporter.write_with_format_selection.return_value = False  # Model storage rejection.
        with caplog.at_level("INFO"):
            result = module.OrgAdminExporter.licenses()  # Exercise the actual completion message path.
        assert result is None  # Preserve the existing public result.
        assert license_case.resolver.DataExporter.write_with_format_selection.call_count == 1  # No recovery output.
        assert any(record.levelname == "ERROR" and "OrgLicenses.csv" in record.message for record in caplog.records)
        assert "Exported" not in caplog.text  # A rejected writer cannot prove that output exists.

    @pytest.mark.parametrize("stage", ("request", "transform", "writer"))
    def test_exception_propagates(
        self,
        license_case: SimpleNamespace,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        stage: str,
    ) -> None:
        """Exceptions must propagate without a second write or a success message."""
        failure = OSError("synthetic failure")  # Keep external failure content deterministic and non-sensitive.
        targets = {  # Select the action whose existing exception behavior must remain intact.
            "request": (
                license_case.wrapper if license_case.branch == "wrapper" else license_case.resolver.apisession.mist_get
            ),
            "writer": license_case.resolver.DataExporter.write_with_format_selection,
            "transform": MagicMock(side_effect=failure),
        }
        if stage == "transform":
            monkeypatch.setattr(
                module.DataProcessingUtils, "flatten_nested_fields", targets["transform"]
            )  # Inject transform failure.
        targets[stage].side_effect = failure  # Raise the same exception object at the selected action.
        with caplog.at_level("INFO"), pytest.raises(OSError) as caught:
            module.OrgAdminExporter.licenses()  # Verify the public error behavior.
        assert caught.value is failure  # Do not replace the primary failure with a cleanup error.
        assert license_case.resolver.DataExporter.write_with_format_selection.call_count == (
            1 if stage == "writer" else 0
        )
        assert "Failed to export licenses" in caplog.text and "Exported" not in caplog.text  # Report only failure.

    @pytest.mark.parametrize("interruption", (KeyboardInterrupt, EOFError))
    def test_operator_cancellation(self, license_case: SimpleNamespace, interruption: type[BaseException]) -> None:
        """Canceled organization selection must not start any endpoint or write."""
        license_case.resolver.ConfigUtils.get_cached_or_prompted_org_id.side_effect = interruption  # No real prompt.
        with pytest.raises(interruption):
            module.OrgAdminExporter.licenses()  # Preserve the existing operator interruption behavior.
        license_case.resolver.apisession.mist_get.assert_not_called()  # No direct endpoint after cancellation.
        license_case.wrapper.assert_not_called()  # No wrapper endpoint after cancellation.
        license_case.resolver.DataExporter.write_with_format_selection.assert_not_called()  # No canceled output.
