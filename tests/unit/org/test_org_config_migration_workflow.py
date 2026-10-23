"""Tests for the org config migration export flow, the operator prompts, and the report.

Why:
    ``src/mist/resources/org/org_config_migration_manager.py`` drives menu 176 and menu 177.
    Menu 177 writes into a live org. Issue #1961 reports that the export flow,
    the file selection prompt, the bundle guard, the confirmation gate, and the
    result summary hold no test. This module covers those blocks. No test
    reaches the Mist API, because a mock replaces every endpoint.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
import requests
from mistapi.__api_response import APIResponse

from src.mist.resources.org import org_config_migration_manager as ocm
from src.mist.resources.org.org_config_migration_manager import OrgConfigMigrationManager

TYPE_KEYS = [str(ct["key"]) for ct in OrgConfigMigrationManager.CONFIG_TYPES]  # WHY: the six keys a bundle must hold.


@pytest.fixture
def manager() -> OrgConfigMigrationManager:
    """Return a manager whose session, org resolver, and input wrapper are mocks.

    Why:
        The constructor stores three collaborators. A mock keeps every test off
        the network and lets a test read back the prompt the code sent.
    """
    # WHY: the org resolver returns a fixed org, so a test never prompts.
    return OrgConfigMigrationManager(MagicMock(), MagicMock(return_value="dest-org"), MagicMock())


def _valid_bundle() -> dict[str, Any]:
    """Return the smallest bundle that passes the structure guard.

    Why:
        The guard needs a metadata section and all six type keys. Several
        tests share this shape, so one builder keeps them consistent.
    """
    bundle: dict[str, Any] = {"metadata": {"source_org_id": "src-org"}}  # WHY: the guard reads this section first.
    for key in TYPE_KEYS:  # WHY: a missing key fails the guard for the wrong reason.
        bundle[key] = []  # WHY: an empty list keeps the fixture free of import work.
    return bundle  # WHY: the caller adds objects to the type it tests.


class TestGetOrgName:
    """Cover the org name lookup that labels every export bundle."""

    @pytest.mark.parametrize("status", [200, 201, 299])
    def test_the_name_is_read_from_the_response(
        self, manager: OrgConfigMigrationManager, caplog: pytest.LogCaptureFixture, status: int
    ) -> None:
        """Accept valid metadata without recording its name in lookup logs."""
        response = requests.Response()  # Exercise the installed SDK response boundary offline.
        response.status_code = status  # Cover both limits of the successful status range.
        response._content = b'{"name": " Acme-Corp "}'  # Preserve the exact source label.
        api_response = APIResponse(response=response, url="https://api.mist.com/api/v1/orgs/dest-org")
        caplog.set_level("DEBUG", logger=ocm.__name__)  # Capture successful diagnostics as well as warnings.
        caplog.clear()  # Limit the assertion to lookup logs, not fixture construction.
        with patch.object(ocm.mistapi.api.v1.orgs.orgs, "getOrg", return_value=api_response) as endpoint:
            assert manager._get_org_name() == " Acme-Corp "
        endpoint.assert_called_once_with(manager.session, manager.org_id)  # Preserve the endpoint arguments.
        assert "Acme-Corp" not in caplog.text  # A valid name must not enter the diagnostic log.
        assert not [record for record in caplog.records if record.levelno >= 30]  # Success must not warn.

    @pytest.mark.parametrize("status", [199, 300, 401, 403, 404, 429, 500, 503])
    def test_a_refused_http_result_returns_unknown(
        self, manager: OrgConfigMigrationManager, caplog: pytest.LogCaptureFixture, status: int
    ) -> None:
        """Reject even plausible names from unsuccessful responses without body logs."""
        response = requests.Response()  # Exercise native HTTP status and payload parsing without a request.
        response.status_code = status  # Include client refusal, server failure, and range boundaries.
        response._content = b'{"name": "sensitive-body-marker", "error": "sensitive-body-marker"}'
        api_response = APIResponse(response=response, url="https://api.mist.com/api/v1/orgs/dest-org")
        manager.org_id = "dest-org"  # Verify that the warning identifies the affected organization.
        caplog.set_level("DEBUG", logger=ocm.__name__)  # Detect leaks at every lookup log level.
        caplog.clear()  # Exclude the SDK fixture construction from lookup diagnostics.
        with (
            patch.object(ocm.mistapi.api.v1.orgs.orgs, "getOrg", return_value=api_response) as endpoint,
            patch.object(APIResponse, "data", new_callable=PropertyMock, create=True) as metadata,
        ):
            metadata.side_effect = AssertionError("Refused metadata must not be read")  # Prove validation order.
            assert manager._get_org_name() == "Unknown"
        metadata.assert_not_called()  # Reject status before inspecting even a plausible name.
        endpoint.assert_called_once_with(manager.session, "dest-org")  # Refusal must not trigger another request.
        assert f"HTTP {status}" in caplog.text  # Report the exact refusal status.
        assert "dest-org" in caplog.text  # Keep enough context to diagnose the failed lookup.
        assert "sensitive-body-marker" not in caplog.text  # Never record the refusal body or supplied name.
        assert any(record.levelno == 30 for record in caplog.records)  # The refusal must be visible.

    @pytest.mark.parametrize(
        "data",
        [
            None,
            [],
            ["sensitive-body-marker"],
            {},
            {"id": "dest-org"},
            {"name": None},
            {"name": 42},
            {"name": ""},
            {"name": "   "},
            {"error": "sensitive-body-marker", "name": "sensitive-body-marker"},
            {"error": "", "name": "sensitive-body-marker"},
        ],
    )
    def test_invalid_metadata_returns_unknown(
        self, manager: OrgConfigMigrationManager, caplog: pytest.LogCaptureFixture, data: object
    ) -> None:
        """Reject malformed metadata and error objects even with HTTP 200."""
        response = SimpleNamespace(status_code=200, data=data)  # Isolate external payload shape validation.
        caplog.set_level("DEBUG", logger=ocm.__name__)  # Include debug records in the privacy assertion.
        with patch.object(ocm.mistapi.api.v1.orgs.orgs, "getOrg", return_value=response):
            assert manager._get_org_name() == "Unknown"
        assert any(record.levelno == 30 for record in caplog.records)  # Invalid metadata must not fail silently.
        assert "sensitive-body-marker" not in caplog.text  # Never log invalid metadata contents.

    @pytest.mark.parametrize("status", [None, "sensitive-status-marker", 200.0, True, False])
    def test_an_invalid_status_is_rejected_before_data(
        self, manager: OrgConfigMigrationManager, caplog: pytest.LogCaptureFixture, status: object
    ) -> None:
        """Do not read metadata until an integer successful status is present."""
        response = MagicMock(spec=["data"])  # An absent status attribute must not imply success.
        if status is not None:  # Also exercise explicit invalid statuses.
            response.status_code = status
        caplog.set_level("DEBUG", logger=ocm.__name__)  # Detect interpolation of invalid external status text.
        with (
            patch.object(ocm.mistapi.api.v1.orgs.orgs, "getOrg", return_value=response),
            patch.object(type(response), "data", new_callable=PropertyMock, create=True) as metadata,
        ):
            metadata.side_effect = AssertionError("Invalid status must not read metadata")  # Prove early exit.
            assert manager._get_org_name() == "Unknown"
        metadata.assert_not_called()  # Attribute access itself must wait for HTTP validation.
        assert "HTTP unavailable" in caplog.text  # Invalid status values need a fixed, safe diagnostic.
        assert any(record.levelno == 30 for record in caplog.records)  # A missing status needs a visible warning.
        assert "sensitive-status-marker" not in caplog.text  # Invalid status objects must not enter logs.

    @pytest.mark.parametrize("error_type", [requests.Timeout, ConnectionError, RuntimeError])
    def test_request_errors_do_not_expose_exception_text(
        self, manager: OrgConfigMigrationManager, caplog: pytest.LogCaptureFixture, error_type: type[Exception]
    ) -> None:
        """Retain the unknown label without exposing exception response text."""
        caplog.set_level("DEBUG", logger=ocm.__name__)  # Exception messages can contain an entire response.
        with patch.object(ocm.mistapi.api.v1.orgs.orgs, "getOrg", side_effect=error_type("sensitive-body-marker")):
            assert manager._get_org_name() == "Unknown"
        assert error_type.__name__ in caplog.text  # Report the failure category without its message.
        assert "sensitive-body-marker" not in caplog.text  # Exception tracebacks can expose sensitive text.
        assert any(record.levelno == 40 for record in caplog.records)  # Request exceptions need an error log.


class TestBuildExportBundle:
    """Cover the metadata wrapper that the import side reads back."""

    def test_the_counts_match_the_fetched_objects(self, manager: OrgConfigMigrationManager) -> None:
        """A wrong count misleads the operator before a destructive import."""
        results = {"networks": [{"name": "A"}, {"name": "B"}], "vpns": []}  # WHY: two objects and one empty type.
        bundle = manager._build_export_bundle(results, "Acme-Corp")  # WHY: drive the wrapper.
        assert bundle["metadata"]["object_counts"] == {"networks": 2, "vpns": 0}

    def test_the_source_org_is_recorded(self, manager: OrgConfigMigrationManager) -> None:
        """The import guard compares this value against the destination org."""
        manager.org_id = "src-org"  # WHY: the export resolves the org before this call.
        bundle = manager._build_export_bundle({}, "Acme-Corp")  # WHY: drive the wrapper.
        assert bundle["metadata"]["source_org_id"] == "src-org"  # WHY: the guard reads this field.
        assert bundle["metadata"]["source_org_name"] == "Acme-Corp"  # WHY: the preview shows this name.

    def test_the_schema_version_is_stamped(self, manager: OrgConfigMigrationManager) -> None:
        """A future format change needs a version to branch on."""
        bundle = manager._build_export_bundle({}, "Acme-Corp")  # WHY: drive the wrapper.
        assert bundle["metadata"]["schema_version"] == "1.0"

    def test_the_fetched_objects_reach_the_bundle(self, manager: OrgConfigMigrationManager) -> None:
        """A bundle without the objects exports nothing the import can use."""
        results = {"networks": [{"name": "Corp-LAN"}]}  # WHY: one object to carry across.
        bundle = manager._build_export_bundle(results, "Acme-Corp")  # WHY: drive the wrapper.
        assert bundle["networks"] == [{"name": "Corp-LAN"}]  # WHY: the payload must survive the wrap.


class TestSaveBundleToFile:
    """Cover the file write, because the filename carries the org and the time."""

    def test_the_bundle_round_trips_through_the_file(
        self, manager: OrgConfigMigrationManager, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """A truncated file makes the later import fail on a parse error."""
        monkeypatch.chdir(tmp_path)  # WHY: the writer joins a relative data directory.
        (tmp_path / "data").mkdir()  # WHY: the writer does not create the directory.
        bundle = {"metadata": {"schema_version": "1.0"}, "networks": [{"name": "Corp-LAN"}]}  # WHY: a small bundle.
        filepath = manager._save_bundle_to_file(bundle, "Acme-Corp")  # WHY: drive the write.
        assert json.loads(Path(filepath).read_text(encoding="utf-8")) == bundle

    def test_an_unsafe_org_name_is_sanitized(
        self, manager: OrgConfigMigrationManager, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """A slash in an org name would send the file outside the data directory."""
        monkeypatch.chdir(tmp_path)  # WHY: the writer joins a relative data directory.
        (tmp_path / "data").mkdir()  # WHY: the writer does not create the directory.
        filepath = manager._save_bundle_to_file({"metadata": {}}, "Acme/Corp Inc.")  # WHY: drive the sanitizer.
        name = Path(filepath).name  # WHY: read only the final path element.
        assert "/" not in name  # WHY: a slash would redirect the write.
        assert "Acme_Corp_Inc_" in name  # WHY: each unsafe character becomes an underscore.

    def test_the_file_lands_in_the_data_directory(
        self, manager: OrgConfigMigrationManager, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Every output of this project belongs under the data directory."""
        monkeypatch.chdir(tmp_path)  # WHY: the writer joins a relative data directory.
        (tmp_path / "data").mkdir()  # WHY: the writer does not create the directory.
        filepath = manager._save_bundle_to_file({"metadata": {}}, "Acme")  # WHY: drive the write.
        assert Path(filepath).parent.name == "data"  # WHY: the runtime enforces this location.


class TestDisplayExportSummary:
    """Cover the summary table the operator reads after an export."""

    def test_every_type_and_the_total_are_shown(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """A missing row hides an empty type that the operator expected to hold data."""
        caplog.set_level(
            "INFO", logger="src.mist.resources.org.org_config_migration_manager"
        )  # WHY: preview now uses INFO.
        counts = {key: 1 for key in TYPE_KEYS}  # WHY: one object of every type.
        bundle = {"metadata": {"object_counts": counts}}  # WHY: the printer reads this section.
        manager._display_export_summary(bundle, "data/OrgConfig_Export_Acme.json")  # WHY: drive the printer.
        for config_type in OrgConfigMigrationManager.CONFIG_TYPES:  # WHY: check all six labels.
            assert str(config_type["display_name"]) in caplog.text
        assert "TOTAL" in caplog.text  # WHY: the operator checks the grand total first.

    def test_an_empty_export_reports_a_zero_total(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """An org with no WAN config must report zero rather than raise."""
        caplog.set_level("INFO")  # WHY: INFO keeps this operator preview visible by default.
        manager._display_export_summary({"metadata": {"object_counts": {}}}, "data/x.json")  # WHY: drive it empty.
        assert "TOTAL" in caplog.text  # WHY: the totals row must still print.


class TestFetchAllTypes:
    """Cover the export fetch loop, which must visit every registered type."""

    def test_every_type_is_fetched_once(self, manager: OrgConfigMigrationManager) -> None:
        """A skipped type silently drops that config from the migration."""
        with patch.object(manager, "_fetch_config_type", return_value=[]) as fetch_spy:
            results = manager._fetch_all_types()  # WHY: drive the loop.
        assert fetch_spy.call_count == len(TYPE_KEYS)  # WHY: one call for each registered type.
        assert sorted(results) == sorted(TYPE_KEYS)  # WHY: the bundle needs all six keys.

    def test_the_results_are_keyed_by_type(self, manager: OrgConfigMigrationManager) -> None:
        """A wrong key would import networks into the services endpoint."""
        with patch.object(manager, "_fetch_config_type", side_effect=lambda ct: [{"key": ct["key"]}]):
            results = manager._fetch_all_types()  # WHY: drive the loop.
        assert results["networks"] == [{"key": "networks"}]  # WHY: each list must sit under its own key.


class TestExportConfig:
    """Cover the menu 176 entry point, which must not write before it fetches."""

    def test_the_flow_reaches_the_file_write(self, manager: OrgConfigMigrationManager) -> None:
        """A broken order would save a bundle before the fetch fills it."""
        with (
            patch.object(manager, "_get_org_name", return_value="Acme"),
            patch.object(manager, "_fetch_all_types", return_value={"networks": []}) as fetch_spy,
            patch.object(manager, "_save_bundle_to_file", return_value="data/x.json") as save_spy,
            patch.object(manager, "_display_export_summary") as summary_spy,
        ):
            manager.export_config()  # WHY: drive the whole menu 176 flow.
        fetch_spy.assert_called_once()  # WHY: the fetch must run before the write.
        save_spy.assert_called_once()  # WHY: exactly one bundle per export.
        summary_spy.assert_called_once_with(save_spy.call_args[0][0], "data/x.json")

    def test_the_org_resolver_sets_the_source_org(self, manager: OrgConfigMigrationManager) -> None:
        """A wrong org would export the config of the wrong customer."""
        with (
            patch.object(manager, "_get_org_name", return_value="Acme"),
            patch.object(manager, "_fetch_all_types", return_value={}),
            patch.object(manager, "_save_bundle_to_file", return_value="data/x.json"),
            patch.object(manager, "_display_export_summary"),
        ):
            manager.export_config()  # WHY: drive the whole menu 176 flow.
        assert manager.org_id == "dest-org"  # WHY: the resolver value must reach the instance.

    @pytest.mark.parametrize("scenario", [(200, "Acme"), (403, "Unknown"), (503, "Unknown")])
    def test_validated_metadata_reaches_the_saved_bundle(
        self,
        manager: OrgConfigMigrationManager,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        scenario: tuple[int, str],
    ) -> None:
        """Integrate lookup validation with the existing export writer without network access."""
        monkeypatch.chdir(tmp_path)  # Keep output separate from production data.
        (tmp_path / "data").mkdir()  # The existing writer expects the product output directory.
        response = requests.Response()  # Use the native SDK response shape for this integrated flow.
        response.status_code = scenario[0]  # Prove that status overrides a plausible body name.
        response._content = b'{"name": "Acme"}'  # The same body must yield different labels after refusal.
        api_response = APIResponse(response=response, url="https://api.mist.com/api/v1/orgs/dest-org")
        with (
            patch.object(ocm.mistapi.api.v1.orgs.orgs, "getOrg", return_value=api_response) as endpoint,
            patch.object(manager, "_fetch_all_types", return_value={key: [] for key in TYPE_KEYS}),
        ):
            manager.export_config()  # Exercise the real lookup, metadata builder, and file writer.
        endpoint.assert_called_once_with(manager.session, "dest-org")  # No extra metadata request is necessary.
        saved_files = list((tmp_path / "data").glob("OrgConfig_Export_*.json"))  # Inspect the private test output.
        assert len(saved_files) == 1  # The flow must persist exactly one export.
        bundle = json.loads(saved_files[0].read_text(encoding="utf-8"))  # Verify the durable metadata result.
        assert bundle["metadata"]["source_org_name"] == scenario[1]  # Preserve success and explicit unknown.
        assert bundle["metadata"]["source_org_id"] == "dest-org"  # The source identifier must remain unchanged.


class TestSelectImportFile:
    """Cover the bundle picker, which is the first gate of menu 177."""

    def test_no_bundle_returns_an_empty_path(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """An import with no bundle must stop, not raise on an empty list."""
        caplog.set_level("WARNING")  # WHY: the guard reports the guidance at WARNING level.
        with patch.object(ocm.glob, "glob", return_value=[]):
            assert manager._select_import_file() == ""
        assert "Menu 176" in caplog.text  # WHY: the message must point at the export step.

    def test_a_single_bundle_is_selected_without_a_prompt(self, manager: OrgConfigMigrationManager) -> None:
        """A prompt with one choice wastes the time of the operator."""
        with (
            patch.object(ocm.glob, "glob", return_value=["data/OrgConfig_Export_A.json"]),
            patch.object(manager, "_prompt_file_selection") as prompt_spy,
        ):
            assert manager._select_import_file() == "data/OrgConfig_Export_A.json"
        prompt_spy.assert_not_called()  # WHY: one file needs no operator choice.

    def test_several_bundles_reach_the_prompt(self, manager: OrgConfigMigrationManager) -> None:
        """The operator must choose when more than one bundle exists."""
        files = ["data/OrgConfig_Export_A.json", "data/OrgConfig_Export_B.json"]  # WHY: two candidates.
        with (
            patch.object(ocm.glob, "glob", return_value=files),
            patch.object(manager, "_prompt_file_selection", return_value=files[0]) as prompt_spy,
        ):
            assert manager._select_import_file() == files[0]
        prompt_spy.assert_called_once()  # WHY: the choice must go to the operator.

    def test_the_newest_bundle_is_listed_first(self, manager: OrgConfigMigrationManager) -> None:
        """The timestamp sorts descending, so the newest export heads the list."""
        files = ["data/OrgConfig_Export_A_20260101.json", "data/OrgConfig_Export_A_20260202.json"]  # WHY: two dates.
        with (
            patch.object(ocm.glob, "glob", return_value=files),
            patch.object(manager, "_prompt_file_selection", side_effect=lambda listed: listed[0]),
        ):
            assert manager._select_import_file() == files[1]  # WHY: the later date must come first.


class TestPromptFileSelection:
    """Cover the numeric prompt that picks one bundle out of many."""

    @staticmethod
    def _files() -> list[str]:
        """Return three candidate bundle paths shared by the tests below."""
        # WHY: three entries let a test prove the middle index resolves.
        return ["data/A.json", "data/B.json", "data/C.json"]

    def test_a_valid_number_selects_that_bundle(self, manager: OrgConfigMigrationManager) -> None:
        """An off-by-one error would import the wrong customer config."""
        manager.safe_input_fn = MagicMock(return_value="2")  # WHY: the operator counts from one.
        assert manager._prompt_file_selection(self._files()) == "data/B.json"

    def test_a_number_above_the_range_is_rejected(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """An out-of-range index would raise or wrap to the wrong bundle."""
        caplog.set_level("WARNING")  # WHY: the guard reports at WARNING level.
        manager.safe_input_fn = MagicMock(return_value="9")  # WHY: only three bundles exist.
        assert manager._prompt_file_selection(self._files()) == ""
        assert "Invalid selection" in caplog.text  # WHY: the operator needs to know why.

    def test_a_zero_is_rejected(self, manager: OrgConfigMigrationManager) -> None:
        """A zero maps to index minus one, which would select the last bundle."""
        manager.safe_input_fn = MagicMock(return_value="0")  # WHY: the boundary below the range.
        assert manager._prompt_file_selection(self._files()) == ""

    def test_text_input_is_rejected(self, manager: OrgConfigMigrationManager) -> None:
        """A typed word must not raise out of the menu."""
        manager.safe_input_fn = MagicMock(return_value="first")  # WHY: reproduce the typing mistake.
        assert manager._prompt_file_selection(self._files()) == ""

    def test_the_prompt_names_the_range(self, manager: OrgConfigMigrationManager) -> None:
        """A prompt without the range leaves the operator guessing."""
        manager.safe_input_fn = MagicMock(return_value="1")  # WHY: any valid answer ends the prompt.
        manager._prompt_file_selection(self._files())  # WHY: drive the prompt.
        assert "[1-3]" in manager.safe_input_fn.call_args[0][0]  # WHY: the range must reach the operator.


class TestLoadAndValidateBundle:
    """Cover the file read guard, which runs before any write to the destination."""

    def test_a_valid_file_is_parsed(self, manager: OrgConfigMigrationManager, tmp_path: Path) -> None:
        """A good bundle must load, or the import never starts."""
        path = tmp_path / "bundle.json"  # WHY: a real file proves the read path works.
        path.write_text(json.dumps(_valid_bundle()), encoding="utf-8")  # WHY: write the valid shape.
        assert manager._load_and_validate_bundle(str(path)) == _valid_bundle()  # WHY: valid JSON must load unchanged.

    def test_corrupt_json_returns_none(self, manager: OrgConfigMigrationManager, tmp_path: Path, caplog: Any) -> None:
        """A truncated export must stop the import instead of raising."""
        caplog.set_level("ERROR")  # WHY: the guard reports at ERROR level.
        path = tmp_path / "bundle.json"  # WHY: a real file proves the read path works.
        path.write_text("{not json", encoding="utf-8")  # WHY: reproduce a truncated write.
        assert manager._load_and_validate_bundle(str(path)) is None
        assert "Error reading bundle" in caplog.text  # WHY: the operator needs the cause.

    def test_a_missing_file_returns_none(self, manager: OrgConfigMigrationManager, tmp_path: Path) -> None:
        """A deleted bundle between the pick and the read must not raise."""
        missing = tmp_path / "gone.json"  # WHY: the path never exists.
        assert manager._load_and_validate_bundle(str(missing)) is None

    def test_a_failed_structure_check_returns_none(self, manager: OrgConfigMigrationManager, tmp_path: Path) -> None:
        """A bundle from another tool must not reach the create loop."""
        path = tmp_path / "bundle.json"  # WHY: a real file proves the read path works.
        path.write_text(json.dumps({"networks": []}), encoding="utf-8")  # WHY: no metadata section.
        assert manager._load_and_validate_bundle(str(path)) is None


class TestValidateBundleStructure:
    """Cover the structure guard, which is the last check before the import runs."""

    def test_a_complete_bundle_passes(self, manager: OrgConfigMigrationManager) -> None:
        """A valid bundle must pass, or menu 177 can never run."""
        assert manager._validate_bundle_structure(_valid_bundle()) is True

    def test_a_missing_metadata_section_fails(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """Without metadata the preview and the source org check cannot run."""
        caplog.set_level("ERROR")  # WHY: the guard reports at ERROR level.
        bundle = {key: [] for key in TYPE_KEYS}  # WHY: every type key but no metadata.
        assert manager._validate_bundle_structure(bundle) is False
        assert "missing 'metadata' section" in caplog.text  # WHY: the message must name the gap.

    def test_a_missing_type_key_fails(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """A partial bundle would import some types and silently drop the rest."""
        caplog.set_level("ERROR")  # WHY: the guard reports at ERROR level.
        bundle = _valid_bundle()  # WHY: start from the valid shape.
        del bundle["vpns"]  # WHY: remove one type to trigger the guard.
        assert manager._validate_bundle_structure(bundle) is False
        assert "vpns" in caplog.text  # WHY: the message must name the missing type.

    def test_a_self_import_warns_the_operator(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """Importing a bundle back into its own org flags every object as a conflict."""
        caplog.set_level("WARNING")  # WHY: the warning is advisory, not blocking.
        manager.org_id = "src-org"  # WHY: the destination matches the source in the bundle.
        assert manager._validate_bundle_structure(_valid_bundle()) is True
        assert "matches destination org" in caplog.text  # WHY: the operator must see the risk.

    def test_a_bundle_without_a_source_org_still_passes(self, manager: OrgConfigMigrationManager) -> None:
        """A hand-built bundle can omit the source org, and the guard must not raise."""
        bundle = _valid_bundle()  # WHY: start from the valid shape.
        bundle["metadata"] = {}  # WHY: remove the source org field.
        assert manager._validate_bundle_structure(bundle) is True


class TestDisplayBundlePreview:
    """Cover the preview the operator reads before the confirmation prompt."""

    def test_the_preview_names_the_source_and_the_total(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """A preview without a count gives the operator nothing to check."""
        caplog.set_level(
            "INFO", logger="src.mist.resources.org.org_config_migration_manager"
        )  # WHY: preview now uses INFO.
        metadata = {
            "source_org_name": "Acme-Corp",  # WHY: the operator recognizes the org by name.
            "export_timestamp": "2026-08-23T00:00:00+00:00",  # WHY: a stale bundle is a common mistake.
            "source_org_id": "src-org-1234",  # WHY: the printer shows the first eight characters.
            "object_counts": {"networks": 2, "vpns": 3},  # WHY: the total must reach five.
        }
        manager._display_bundle_preview({"metadata": metadata})  # WHY: drive the printer.
        assert "Acme-Corp" in caplog.text  # WHY: the source name must reach the operator.
        assert "Total objects: 5" in caplog.text  # WHY: the total must sum every type.

    def test_a_bundle_without_counts_reports_zero(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """A hand-built bundle can omit the counts, and the printer must not raise."""
        caplog.set_level("WARNING")  # WHY: the printer writes at WARNING level.
        manager._display_bundle_preview({"metadata": {"source_org_id": "src-org"}})  # WHY: drive the fallback.
        assert "Total objects: 0" in caplog.text  # WHY: zero is the safe fallback.


class TestPromptDryRun:
    """Cover the safety default, because a dry run makes no change to the cloud."""

    def test_the_default_answer_selects_the_dry_run(self, manager: OrgConfigMigrationManager) -> None:
        """A blank answer must preview, never write."""
        manager.safe_input_fn = MagicMock(return_value="Y")  # WHY: the prompt supplies this default.
        assert manager._prompt_dry_run() is True

    def test_an_uppercase_no_selects_the_live_run(self, manager: OrgConfigMigrationManager) -> None:
        """The operator needs a way to leave the preview and write for real."""
        manager.safe_input_fn = MagicMock(return_value="N")  # WHY: the documented live-run answer.
        assert manager._prompt_dry_run() is False

    def test_a_lowercase_no_selects_the_live_run(self, manager: OrgConfigMigrationManager) -> None:
        """The prompt shows a lowercase option, so it must accept one."""
        manager.safe_input_fn = MagicMock(return_value="n")  # WHY: the prompt reads Y slash n.
        assert manager._prompt_dry_run() is False

    def test_an_unexpected_answer_stays_in_the_dry_run(self, manager: OrgConfigMigrationManager) -> None:
        """A typing mistake must not turn a preview into a live write."""
        manager.safe_input_fn = MagicMock(return_value="maybe")  # WHY: reproduce the typing mistake.
        assert manager._prompt_dry_run() is True

    def test_the_prompt_carries_the_safe_default(self, manager: OrgConfigMigrationManager) -> None:
        """A lost default would let an empty answer fall through to a live write."""
        manager.safe_input_fn = MagicMock(return_value="Y")  # WHY: any answer ends the prompt.
        manager._prompt_dry_run()  # WHY: drive the prompt.
        assert manager.safe_input_fn.call_args.kwargs["default_value"] == "Y"


class TestConfirmImport:
    """Cover the typed confirmation, which is the last gate before a live write."""

    def test_the_exact_word_confirms(self, manager: OrgConfigMigrationManager) -> None:
        """The operator must have a way to proceed after reading the warning."""
        manager.safe_input_fn = MagicMock(return_value="IMPORT")  # WHY: the documented word.
        assert manager._confirm_import() is True

    def test_a_lowercase_word_cancels(self, manager: OrgConfigMigrationManager) -> None:
        """A relaxed compare would let a careless answer write to the cloud."""
        manager.safe_input_fn = MagicMock(return_value="import")  # WHY: the case differs.
        assert manager._confirm_import() is False

    def test_an_empty_answer_cancels(self, manager: OrgConfigMigrationManager) -> None:
        """A bare return key must cancel a destructive operation."""
        manager.safe_input_fn = MagicMock(return_value="")  # WHY: reproduce the bare return key.
        assert manager._confirm_import() is False

    def test_a_padded_word_cancels(self, manager: OrgConfigMigrationManager) -> None:
        """The gate compares the raw answer, so a stray space must cancel."""
        manager.safe_input_fn = MagicMock(return_value=" IMPORT ")  # WHY: reproduce the stray spaces.
        assert manager._confirm_import() is False

    def test_the_warning_names_the_consequence(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """A warning without the consequence does not inform the decision."""
        caplog.set_level("WARNING")  # WHY: the gate writes the warning at WARNING level.
        manager.safe_input_fn = MagicMock(return_value="")  # WHY: any answer ends the prompt.
        manager._confirm_import()  # WHY: drive the warning.
        assert "cannot be automatically undone" in caplog.text  # WHY: the risk must be explicit.


class TestFetchExistingObjects:
    """Cover the conflict cache, because an empty cache lets every duplicate through."""

    def test_every_type_is_cached(self, manager: OrgConfigMigrationManager) -> None:
        """A missing type in the cache disables the conflict guard for that type."""
        with patch.object(manager, "_fetch_config_type", return_value=[{"name": "A"}]):
            manager._fetch_existing_objects()  # WHY: drive the cache fill.
        assert sorted(manager._existing) == sorted(TYPE_KEYS)  # WHY: all six types must be cached.

    def test_an_empty_org_caches_empty_lists(self, manager: OrgConfigMigrationManager) -> None:
        """A brand new destination org holds nothing, and the cache must still exist."""
        with patch.object(manager, "_fetch_config_type", return_value=[]):
            manager._fetch_existing_objects()  # WHY: drive the cache fill.
        assert all(not rows for rows in manager._existing.values())  # WHY: every key maps to a list.


class TestImportConfig:
    """Cover the menu 177 entry point, which must stop at every failed gate."""

    @staticmethod
    def _patched(manager: OrgConfigMigrationManager) -> dict[str, Any]:
        """Return the patch handles that isolate the menu 177 flow from the API."""
        # WHY: one builder keeps the six patches identical across the tests below.
        return {
            "preview": patch.object(manager, "_display_bundle_preview"),  # WHY: silence the printer.
            "fetch": patch.object(manager, "_fetch_existing_objects"),  # WHY: no cache fetch over the network.
            "execute": patch.object(manager, "_execute_import", return_value=[]),  # WHY: no create call.
            "report": patch.object(manager, "_display_import_report"),  # WHY: silence the printer.
        }

    def test_no_bundle_stops_the_flow(self, manager: OrgConfigMigrationManager) -> None:
        """A missing bundle must stop before the destination org is touched."""
        with (
            patch.object(manager, "_select_import_file", return_value=""),
            patch.object(manager, "_load_and_validate_bundle") as load_spy,
        ):
            manager.import_config()  # WHY: drive the menu 177 flow.
        assert load_spy.call_count == 0  # WHY: nothing to load means nothing to read.

    def test_an_invalid_bundle_stops_the_flow(self, manager: OrgConfigMigrationManager) -> None:
        """A bundle that fails the guard must never reach the confirmation prompt."""
        with (
            patch.object(manager, "_select_import_file", return_value="data/x.json"),
            patch.object(manager, "_load_and_validate_bundle", return_value=None),
            patch.object(manager, "_prompt_dry_run") as dry_run_spy,
        ):
            manager.import_config()  # WHY: drive the menu 177 flow.
        assert dry_run_spy.call_count == 0  # WHY: an unusable bundle ends the flow.

    def test_a_cancelled_confirmation_stops_the_flow(self, manager: OrgConfigMigrationManager) -> None:
        """A cancelled confirmation must leave the destination org unchanged."""
        handles = self._patched(manager)  # WHY: isolate the flow from the API.
        with (
            patch.object(manager, "_select_import_file", return_value="data/x.json"),
            patch.object(manager, "_load_and_validate_bundle", return_value=_valid_bundle()),
            patch.object(manager, "_prompt_dry_run", return_value=False),
            patch.object(manager, "_confirm_import", return_value=False),
            handles["preview"],
            handles["fetch"] as fetch_spy,
            handles["execute"] as execute_spy,
        ):
            manager.import_config()  # WHY: drive the menu 177 flow.
        assert fetch_spy.call_count == 0  # WHY: a cancel must stop before any read.
        assert execute_spy.call_count == 0  # WHY: a cancel must stop before any write.

    def test_a_dry_run_skips_the_confirmation(self, manager: OrgConfigMigrationManager) -> None:
        """A preview writes nothing, so a typed word would only slow the operator."""
        handles = self._patched(manager)  # WHY: isolate the flow from the API.
        with (
            patch.object(manager, "_select_import_file", return_value="data/x.json"),
            patch.object(manager, "_load_and_validate_bundle", return_value=_valid_bundle()),
            patch.object(manager, "_prompt_dry_run", return_value=True),
            patch.object(manager, "_confirm_import") as confirm_spy,
            handles["preview"],
            handles["fetch"],
            handles["execute"] as execute_spy,
            handles["report"],
        ):
            manager.import_config()  # WHY: drive the menu 177 flow.
        confirm_spy.assert_not_called()  # WHY: a preview needs no typed word.
        assert execute_spy.call_args[0][1] is True  # WHY: the dry-run flag must reach the driver.

    def test_a_confirmed_live_run_reaches_the_report(self, manager: OrgConfigMigrationManager) -> None:
        """A confirmed import must run the create loop and then show the result."""
        handles = self._patched(manager)  # WHY: isolate the flow from the API.
        with (
            patch.object(manager, "_select_import_file", return_value="data/x.json"),
            patch.object(manager, "_load_and_validate_bundle", return_value=_valid_bundle()),
            patch.object(manager, "_prompt_dry_run", return_value=False),
            patch.object(manager, "_confirm_import", return_value=True),
            handles["preview"],
            handles["fetch"] as fetch_spy,
            handles["execute"] as execute_spy,
            handles["report"] as report_spy,
        ):
            manager.import_config()  # WHY: drive the menu 177 flow.
        fetch_spy.assert_called_once()  # WHY: the conflict cache must load first.
        assert execute_spy.call_args[0][1] is False  # WHY: a live run must clear the dry-run flag.
        report_spy.assert_called_once()  # WHY: the operator always gets a summary.


class TestSubnetOverlapDispatch:
    """Cover the overlap router, which picks the field each type stores an address in."""

    def test_a_network_routes_to_the_subnet_check(self, manager: OrgConfigMigrationManager) -> None:
        """A network stores one CIDR in the subnet field."""
        existing = [{"name": "Corp", "subnet": "10.0.0.0/16"}]  # WHY: one existing network.
        conflict = manager._check_subnet_overlap({"subnet": "10.0.1.0/24"}, existing, "networks")
        assert conflict == {
            "reason": "subnet_overlap",
            "detail": "10.0.1.0/24 overlaps with 'Corp' (10.0.0.0/16)",
        }  # WHY: the networks key must reach the subnet check, which names subnet_overlap.

    def test_a_service_routes_to_the_address_check(self, manager: OrgConfigMigrationManager) -> None:
        """A service stores several addresses in a list."""
        existing = [{"name": "Web", "addresses": ["10.0.0.0/16"]}]  # WHY: one existing service.
        conflict = manager._check_subnet_overlap({"addresses": ["10.0.1.5/32"]}, existing, "services")
        assert conflict == {
            "reason": "address_overlap",
            "detail": "10.0.1.5/32 overlaps with 'Web' (10.0.0.0/16)",
        }  # WHY: the services key must reach the address check, which names address_overlap.

    def test_a_type_without_an_address_field_routes_nowhere(self, manager: OrgConfigMigrationManager) -> None:
        """A VPN holds no address field, so a scan would waste time and could raise."""
        assert manager._check_subnet_overlap({"name": "Hub"}, [{"name": "Spoke"}], "vpns") is None


class TestDisplayImportReport:
    """Cover the result summary, which is the only record the operator reads."""

    @staticmethod
    def _mixed_results() -> list[dict[str, Any]]:
        """Return one result row of each status the report groups on."""
        # WHY: four rows prove every section and every total line renders.
        return [
            {"type": "networks", "name": "Net-A", "status": "imported"},
            {"type": "networks", "name": "Net-B", "status": "skipped", "reason": "duplicate name"},
            {"type": "vpns", "name": "Vpn-C", "status": "failed", "reason": "400 bad body"},
            {"type": "services", "name": "Svc-D", "status": "would_import"},
        ]

    def test_every_section_is_rendered(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """A hidden section would let a failure pass without notice."""
        caplog.set_level("WARNING")  # WHY: the printer writes at WARNING level.
        manager._display_import_report(self._mixed_results())  # WHY: drive the whole report.
        assert "IMPORTED (1)" in caplog.text  # WHY: the success section must render.
        assert "SKIPPED (conflicts) (1)" in caplog.text  # WHY: the conflict section must render.
        assert "FAILED (1)" in caplog.text  # WHY: the failure section must render.
        assert "WOULD IMPORT (dry-run) (1)" in caplog.text  # WHY: the preview section must render.

    def test_the_totals_add_up(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """A wrong total misleads the operator about the size of the change."""
        caplog.set_level("WARNING")  # WHY: the printer writes at WARNING level.
        manager._display_import_report(self._mixed_results())  # WHY: drive the whole report.
        assert "Total: 4 objects processed" in caplog.text  # WHY: the four rows must all count.

    def test_the_reason_reaches_the_row(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """A failure without a reason gives the operator nothing to act on."""
        caplog.set_level("WARNING")  # WHY: the printer writes at WARNING level.
        manager._display_import_report(self._mixed_results())  # WHY: drive the whole report.
        assert "400 bad body" in caplog.text  # WHY: the cause must reach the report.

    def test_an_empty_section_is_suppressed(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """An empty heading pads the report and hides the rows that matter."""
        caplog.set_level("WARNING")  # WHY: the printer writes at WARNING level.
        results = [{"type": "networks", "name": "Net-A", "status": "imported"}]  # WHY: one status only.
        manager._display_import_report(results)  # WHY: drive the whole report.
        assert "FAILED" not in caplog.text  # WHY: no failure row means no failure section.

    def test_an_empty_result_list_still_reports(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """An import over an empty bundle must report zero rather than raise."""
        caplog.set_level("WARNING")  # WHY: the printer writes at WARNING level.
        manager._display_import_report([])  # WHY: drive the empty path.
        assert "Total: 0 objects processed" in caplog.text  # WHY: the totals row must still print.

    def test_a_row_without_a_reason_renders(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """A success carries no reason, and the printer must not raise on the lookup."""
        caplog.set_level("WARNING")  # WHY: the printer writes at WARNING level.
        manager._print_report_section("IMPORTED", [{"type": "networks", "name": "Net-A"}])
        assert "Net-A" in caplog.text  # WHY: the row must render without a reason.
