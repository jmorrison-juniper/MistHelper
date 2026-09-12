"""Tests for SelfAccountExporter (spec 907, issue #1415).

The suite proves six behaviors that the menu depends on:

1. The token prompt returns the pasted token and an empty answer cancels.
2. The detail reader reads the 400 body and returns empty for a 200 body.
3. The SDK call passes the token and returns the status code and detail.
4. The audit row holds the org, the status, and a UTC timestamp, and never
   the token.
5. The write reaches the shared selector with the exact operationId.
6. The menu entry point keeps every failure inside the menu and never logs
   the token.

Every Mist call is mocked, so no test reaches the live cloud.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.export.self_account_exporter import SelfAccountExporter

ORG_ID = "org-1415"
TOKEN = "single-use-email-change-token"
MODULE = "src.export.self_account_exporter"


@pytest.fixture
def mist_helper(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Stand in for the lazily imported MistHelper module.

    The exporter calls ``importlib.import_module("MistHelper")``, which returns
    the entry in ``sys.modules`` when one is present. Replacing that entry keeps
    the stub local to the test.
    """
    stub = MagicMock()
    stub.apisession = MagicMock()
    monkeypatch.setitem(sys.modules, "MistHelper", stub)
    return stub


class TestPromptToken:
    """The prompt must return the pasted token and cancel on an empty answer."""

    def test_returns_the_pasted_token(self, mist_helper: MagicMock) -> None:
        """Whitespace around the pasted token is stripped."""
        mist_helper.InputUtils.safe_input.return_value = f"  {TOKEN}  "

        assert SelfAccountExporter._prompt_token() == TOKEN

    def test_an_empty_answer_cancels(self, mist_helper: MagicMock) -> None:
        """An empty answer returns an empty string, so the menu cancels."""
        mist_helper.InputUtils.safe_input.return_value = "   "

        assert SelfAccountExporter._prompt_token() == ""


class TestDetail:
    """The detail reader must read a 400 body and stay empty for a 200 body."""

    def test_reads_the_detail_field(self) -> None:
        """A 400 body carries the reason in the detail field."""
        assert SelfAccountExporter._detail({"detail": "invalid token"}) == "invalid token"

    @pytest.mark.parametrize("body", [None, {}, [], "error", 42])
    def test_a_non_detail_body_is_empty(self, body: Any) -> None:
        """A 200 body is empty, so the reader returns an empty string."""
        assert SelfAccountExporter._detail(body) == ""


class TestVerify:
    """The SDK call must pass the token and return the status and detail."""

    def test_returns_status_and_detail(self, mist_helper: MagicMock) -> None:
        """A 400 body returns its status and its detail message."""
        with patch(
            f"{MODULE}.mistapi.api.v1.self.update.verifySelfEmail",
            return_value=SimpleNamespace(status_code=400, data={"detail": "invalid token"}),
        ) as call:
            status_code, detail = SelfAccountExporter._verify(TOKEN)

        call.assert_called_once_with(mist_helper.apisession, TOKEN)
        assert status_code == 400
        assert detail == "invalid token"

    def test_a_200_body_is_empty(self, mist_helper: MagicMock) -> None:
        """A 200 body is empty, so the detail is an empty string."""
        with patch(
            f"{MODULE}.mistapi.api.v1.self.update.verifySelfEmail",
            return_value=SimpleNamespace(status_code=200, data=None),
        ):
            status_code, detail = SelfAccountExporter._verify(TOKEN)

        assert status_code == 200
        assert detail == ""


class TestBuildRow:
    """The audit row must hold the event and never the token."""

    def test_holds_the_event_fields(self) -> None:
        """The row tags the org, the status, the detail, and a UTC timestamp."""
        row = SelfAccountExporter._build_row(ORG_ID, 400, "invalid token")

        assert row["org_id"] == ORG_ID
        assert row["status_code"] == 400
        assert row["detail"] == "invalid token"
        assert row["verified_at_utc"].endswith("+00:00")

    def test_never_holds_the_token(self) -> None:
        """The token is a credential, so no column may carry it."""
        row = SelfAccountExporter._build_row(ORG_ID, 200, "")

        assert TOKEN not in row.values()


class TestPersist:
    """The write must reach the shared selector with the right operationId."""

    def test_writes_through_the_selector(self, mist_helper: MagicMock) -> None:
        """The operationId decides the primary-key strategy, so it must be exact."""
        SelfAccountExporter._persist({"org_id": ORG_ID}, "verify_self_email.csv")

        mist_helper.DataExporter.write_with_format_selection.assert_called_once()
        kwargs = mist_helper.DataExporter.write_with_format_selection.call_args.kwargs
        assert kwargs["api_function_name"] == "verifySelfEmail"


class TestVerifyEmailMenu:
    """The menu entry point must keep every failure inside the menu."""

    def test_happy_path_writes_one_row(self, mist_helper: MagicMock) -> None:
        """A valid token reaches the writer as one audit row."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        mist_helper.InputUtils.safe_input.return_value = TOKEN
        with patch(
            f"{MODULE}.mistapi.api.v1.self.update.verifySelfEmail",
            return_value=SimpleNamespace(status_code=200, data=None),
        ):
            SelfAccountExporter.verify_email()

        mist_helper.DataExporter.write_with_format_selection.assert_called_once()

    def test_no_org_returns_early(self, mist_helper: MagicMock) -> None:
        """A cancelled org prompt must not call the Mist API."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ""

        with patch(f"{MODULE}.mistapi.api.v1.self.update.verifySelfEmail") as verify:
            SelfAccountExporter.verify_email()

        verify.assert_not_called()

    def test_an_empty_token_cancels(self, mist_helper: MagicMock) -> None:
        """An empty answer must not call the Mist API or write a row."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        mist_helper.InputUtils.safe_input.return_value = ""

        with patch(f"{MODULE}.mistapi.api.v1.self.update.verifySelfEmail") as verify:
            SelfAccountExporter.verify_email()

        verify.assert_not_called()
        mist_helper.DataExporter.write_with_format_selection.assert_not_called()

    def test_a_400_reports_the_detail_and_writes(self, mist_helper: MagicMock) -> None:
        """A 400 body names the reason, and the event still records."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        mist_helper.InputUtils.safe_input.return_value = TOKEN
        with patch(
            f"{MODULE}.mistapi.api.v1.self.update.verifySelfEmail",
            return_value=SimpleNamespace(status_code=400, data={"detail": "invalid token"}),
        ):
            SelfAccountExporter.verify_email()

        mist_helper.DataExporter.write_with_format_selection.assert_called_once()

    def test_an_sdk_error_never_escapes(self, mist_helper: MagicMock) -> None:
        """A network failure must return to the menu, not end the session."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        mist_helper.InputUtils.safe_input.return_value = TOKEN
        with patch(
            f"{MODULE}.mistapi.api.v1.self.update.verifySelfEmail",
            side_effect=RuntimeError("connection reset"),
        ):
            SelfAccountExporter.verify_email()

        mist_helper.DataExporter.write_with_format_selection.assert_not_called()

    def test_the_token_never_reaches_the_log(self, mist_helper: MagicMock, caplog: Any) -> None:
        """The token is a credential, so no log record may carry it."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        mist_helper.InputUtils.safe_input.return_value = TOKEN
        with (
            patch(
                f"{MODULE}.mistapi.api.v1.self.update.verifySelfEmail",
                return_value=SimpleNamespace(status_code=400, data={"detail": "invalid token"}),
            ),
            caplog.at_level("DEBUG"),
        ):
            SelfAccountExporter.verify_email()

        assert TOKEN not in caplog.text
