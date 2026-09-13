"""Tests for OrgCradlepointConnectionExporter (spec 905, issue #1413).

The suite proves four behaviors that the menu depends on:

1. The status call reads ``response.data`` and tolerates a body that is not a
   dict, because the endpoint returns one object and is not paginated.
2. The row builder tags the row with the org and flattens the fields.
3. The write reaches ``write_with_format_selection`` with the exact
   operationId, and an empty result writes nothing.
4. The menu entry point keeps every failure inside the menu.

Every Mist call is mocked, so no test reaches the live cloud.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.export.org_cradlepoint_connection_exporter import OrgCradlepointConnectionExporter

ORG_ID = "org-1413"
MODULE = "src.export.org_cradlepoint_connection_exporter"


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


class TestFetch:
    """The status call must read the body and tolerate a wrong shape."""

    def test_reads_response_data(self, mist_helper: MagicMock) -> None:
        """A dict body reaches the caller unchanged."""
        body = {"last_status": "active", "error": ""}
        with patch(
            f"{MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection",
            return_value=SimpleNamespace(data=body),
        ) as call:
            assert OrgCradlepointConnectionExporter._fetch(ORG_ID) == body

        call.assert_called_once_with(mist_helper.apisession, ORG_ID)

    @pytest.mark.parametrize("body", [None, [], "error", 42])
    def test_a_non_dict_body_becomes_an_empty_dict(self, mist_helper: MagicMock, body: Any) -> None:
        """Only a dict body can hold the status, so any other shape is empty."""
        with patch(
            f"{MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection",
            return_value=SimpleNamespace(data=body),
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


class TestStatusMenu:
    """The menu entry point must keep every failure inside the menu."""

    def test_happy_path_writes_one_row(self, mist_helper: MagicMock) -> None:
        """A status body reaches the writer as one flattened row."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        with patch(
            f"{MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection",
            return_value=SimpleNamespace(data={"last_status": "active", "error": ""}),
        ):
            OrgCradlepointConnectionExporter.status()

        mist_helper.DataExporter.write_with_format_selection.assert_called_once()

    def test_no_org_returns_early(self, mist_helper: MagicMock) -> None:
        """A cancelled org prompt must not call the Mist API."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ""

        with patch(f"{MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection") as call:
            OrgCradlepointConnectionExporter.status()

        call.assert_not_called()

    def test_an_empty_body_writes_nothing(self, mist_helper: MagicMock) -> None:
        """A body that is not a dict is legitimate, so nothing is written."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        with patch(
            f"{MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection",
            return_value=SimpleNamespace(data=None),
        ):
            OrgCradlepointConnectionExporter.status()

        mist_helper.DataExporter.write_with_format_selection.assert_not_called()

    def test_an_sdk_error_never_escapes(self, mist_helper: MagicMock) -> None:
        """A network failure must return to the menu, not end the session."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        with patch(
            f"{MODULE}.mistapi.api.v1.orgs.setting.testOrgCradlepointConnection",
            side_effect=RuntimeError("connection reset"),
        ):
            OrgCradlepointConnectionExporter.status()

        mist_helper.DataExporter.write_with_format_selection.assert_not_called()
