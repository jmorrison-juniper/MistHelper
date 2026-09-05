"""Tests for OrgSecIntelProfileExporter (spec 635, issue #1148).

The suite proves five behaviors that the menu depends on:

1. The list call pages through the shared helper and drops a malformed entry.
2. The numbered prompt returns the chosen profile and refuses a bad answer.
3. The detail call reads ``response.data`` and tolerates a body that is not a
   dict, because the endpoint returns one object and is not paginated.
4. The row builder tags the row with the org and flattens the nested fields.
5. The menu entry point writes through ``write_with_format_selection`` and never
   lets an SDK error escape to the caller.

Every Mist call is mocked, so no test reaches the live cloud.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.export.org_sec_intel_profile_exporter import OrgSecIntelProfileExporter

ORG_ID = "org-1148"
PROFILE_ID = "11111111-2222-3333-4444-555555555555"
MODULE = "src.export.org_sec_intel_profile_exporter"

EXPECTED_TWO = 2


def _profile(name: str = "Baseline", profile_id: str = PROFILE_ID) -> dict[str, Any]:
    """Build one profile row the way the list endpoint returns it."""
    return {"id": profile_id, "name": name, "org_id": ORG_ID}


@pytest.fixture
def mist_helper(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Stand in for the lazily imported MistHelper module.

    The exporter calls ``importlib.import_module("MistHelper")``, which returns
    the entry in ``sys.modules`` when one is present. Replacing that entry keeps
    the stub local to the test. Replacing ``importlib.import_module`` would
    instead mutate the shared importlib module and break ``mock.patch``.
    """
    stub = MagicMock()
    stub.apisession = MagicMock()
    monkeypatch.setitem(sys.modules, "MistHelper", stub)
    return stub


class TestListProfiles:
    """The list call must page every profile and drop a malformed entry."""

    def test_pages_and_keeps_only_dict_rows(self, mist_helper: MagicMock) -> None:
        """A non-dict entry never reaches the caller."""
        rows = [_profile(), "not-a-profile", _profile("Strict", "other-id")]
        with (
            patch(f"{MODULE}.mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles") as listed,
            patch(f"{MODULE}.mistapi.get_all", return_value=rows) as paged,
        ):
            result = OrgSecIntelProfileExporter._list_profiles(ORG_ID)

        listed.assert_called_once_with(mist_helper.apisession, ORG_ID)
        paged.assert_called_once()
        assert len(result) == EXPECTED_TWO
        assert all(isinstance(row, dict) for row in result)

    def test_no_profiles_returns_an_empty_list(self, mist_helper: MagicMock) -> None:
        """A None page result becomes an empty list, not a crash."""
        with (
            patch(f"{MODULE}.mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles"),
            patch(f"{MODULE}.mistapi.get_all", return_value=None),
        ):
            assert OrgSecIntelProfileExporter._list_profiles(ORG_ID) == []


class TestChooseProfile:
    """The prompt must return one profile or refuse the answer."""

    def test_a_valid_number_returns_that_profile(self, mist_helper: MagicMock) -> None:
        """The printed table starts at one, so answer two returns index one."""
        mist_helper.InputUtils.safe_input.return_value = "2"
        profiles = [_profile(), _profile("Strict", "second-id")]

        chosen = OrgSecIntelProfileExporter._choose_profile(profiles)

        assert chosen is not None
        assert chosen["id"] == "second-id"

    @pytest.mark.parametrize("answer", ["", "abc", "0", "3", "-1"])
    def test_a_bad_answer_cancels(self, mist_helper: MagicMock, answer: str) -> None:
        """A non-numeric answer and an out-of-range number both cancel."""
        mist_helper.InputUtils.safe_input.return_value = answer
        profiles = [_profile(), _profile("Strict", "second-id")]

        assert OrgSecIntelProfileExporter._choose_profile(profiles) is None

    def test_an_unnamed_profile_still_prints(self, mist_helper: MagicMock, capsys: Any) -> None:
        """A profile without a name gets a label instead of the word None."""
        mist_helper.InputUtils.safe_input.return_value = "1"
        profiles = [{"id": PROFILE_ID}]

        OrgSecIntelProfileExporter._choose_profile(profiles)

        assert "(unnamed)" in capsys.readouterr().out


class TestFetch:
    """The detail call must read the body and tolerate a wrong shape."""

    def test_reads_response_data(self, mist_helper: MagicMock) -> None:
        """A dict body reaches the caller unchanged."""
        body = {"id": PROFILE_ID, "name": "Baseline"}
        with patch(
            f"{MODULE}.mistapi.api.v1.orgs.secintelprofiles.getOrgSecIntelProfile",
            return_value=SimpleNamespace(data=body),
        ) as call:
            assert OrgSecIntelProfileExporter._fetch(ORG_ID, PROFILE_ID) == body

        call.assert_called_once_with(mist_helper.apisession, ORG_ID, PROFILE_ID)

    @pytest.mark.parametrize("body", [None, [], "error", 42])
    def test_a_non_dict_body_becomes_an_empty_dict(self, mist_helper: MagicMock, body: Any) -> None:
        """Only a dict body can describe a profile, so any other shape is empty."""
        with patch(
            f"{MODULE}.mistapi.api.v1.orgs.secintelprofiles.getOrgSecIntelProfile",
            return_value=SimpleNamespace(data=body),
        ):
            assert OrgSecIntelProfileExporter._fetch(ORG_ID, PROFILE_ID) == {}


class TestBuildRow:
    """The row builder must tag the org and flatten the nested fields."""

    def test_tags_the_org_and_flattens(self) -> None:
        """The org column joins the profile fields and a nested list flattens."""
        payload = {"id": PROFILE_ID, "name": "Baseline", "profiles": [{"name": "a"}]}

        rows = OrgSecIntelProfileExporter._build_row(ORG_ID, payload)

        assert len(rows) == 1
        assert rows[0]["org_id"] == ORG_ID
        assert rows[0]["id"] == PROFILE_ID
        assert not any(isinstance(value, (dict, list)) for value in rows[0].values())

    def test_an_empty_body_builds_no_row(self) -> None:
        """An absent body has nothing to write."""
        assert OrgSecIntelProfileExporter._build_row(ORG_ID, {}) == []


class TestPersist:
    """The write must reach the shared selector with the right operationId."""

    def test_writes_through_the_selector(self, mist_helper: MagicMock) -> None:
        """The operationId decides the primary-key strategy, so it must be exact."""
        OrgSecIntelProfileExporter._persist([{"id": PROFILE_ID}], "OrgSecIntelProfile_x.csv")

        mist_helper.DataExporter.write_with_format_selection.assert_called_once()
        kwargs = mist_helper.DataExporter.write_with_format_selection.call_args.kwargs
        assert kwargs["api_function_name"] == "getOrgSecIntelProfile"

    def test_no_rows_writes_nothing(self, mist_helper: MagicMock) -> None:
        """An empty result reports plainly instead of writing an empty file."""
        OrgSecIntelProfileExporter._persist([], "OrgSecIntelProfile_x.csv")

        mist_helper.DataExporter.write_with_format_selection.assert_not_called()


class TestProfileMenu:
    """The menu entry point must keep every failure inside the menu."""

    def test_happy_path_writes_one_row(self, mist_helper: MagicMock) -> None:
        """A chosen profile reaches the writer as one flattened row."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        mist_helper.InputUtils.safe_input.return_value = "1"
        with (
            patch(f"{MODULE}.mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles"),
            patch(f"{MODULE}.mistapi.get_all", return_value=[_profile()]),
            patch(
                f"{MODULE}.mistapi.api.v1.orgs.secintelprofiles.getOrgSecIntelProfile",
                return_value=SimpleNamespace(data={"id": PROFILE_ID, "name": "Baseline"}),
            ),
        ):
            OrgSecIntelProfileExporter.profile()

        mist_helper.DataExporter.write_with_format_selection.assert_called_once()

    def test_no_org_returns_early(self, mist_helper: MagicMock) -> None:
        """A cancelled org prompt must not call the Mist API."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ""

        with patch(f"{MODULE}.mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles") as listed:
            OrgSecIntelProfileExporter.profile()

        listed.assert_not_called()

    def test_an_org_without_a_profile_reports_and_returns(self, mist_helper: MagicMock) -> None:
        """An org that holds no profile is legitimate, so nothing is written."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        with (
            patch(f"{MODULE}.mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles"),
            patch(f"{MODULE}.mistapi.get_all", return_value=[]),
        ):
            OrgSecIntelProfileExporter.profile()

        mist_helper.DataExporter.write_with_format_selection.assert_not_called()

    def test_a_profile_without_an_id_returns(self, mist_helper: MagicMock) -> None:
        """A row that carries no id cannot drive the detail call."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        mist_helper.InputUtils.safe_input.return_value = "1"
        with (
            patch(f"{MODULE}.mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles"),
            patch(f"{MODULE}.mistapi.get_all", return_value=[{"name": "No id"}]),
            patch(f"{MODULE}.mistapi.api.v1.orgs.secintelprofiles.getOrgSecIntelProfile") as detail,
        ):
            OrgSecIntelProfileExporter.profile()

        detail.assert_not_called()

    def test_an_sdk_error_never_escapes(self, mist_helper: MagicMock) -> None:
        """A network failure must return to the menu, not end the session."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
        with patch(
            f"{MODULE}.mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles",
            side_effect=RuntimeError("connection reset"),
        ):
            OrgSecIntelProfileExporter.profile()

        mist_helper.DataExporter.write_with_format_selection.assert_not_called()
