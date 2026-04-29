"""Tests for GatewayTemplateConfigManager (Issue #211).

Uses identity-checked teardown to avoid cross-test sys.modules contamination.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

# --- Module-level mistapi mock (identity-checked teardown) ---
_had_mistapi = "mistapi" in sys.modules
_saved_mistapi = sys.modules.get("mistapi")
_our_mock = MagicMock()
sys.modules["mistapi"] = _our_mock

from src.gateway.template_config import (
    GatewayTemplateConfigManager,
    _filter_sites_with_location,
    _find_existing_picocell_index,
    _find_picocell_policy,
    _insert_picocell_policy,
    _merge_dia_pico,
    _merge_picocell,
    _parse_state_comma_separated,
    _parse_state_space_separated,
    _parse_template_indices,
    parse_state_from_address,
)


def setup_module() -> None:
    """Re-assert our mock in sys.modules before tests run."""
    sys.modules["mistapi"] = _our_mock


def teardown_module() -> None:
    """Restore sys.modules only if our mock is still installed."""
    if sys.modules.get("mistapi") is not _our_mock:
        return
    if _had_mistapi:
        sys.modules["mistapi"] = _saved_mistapi
    else:
        sys.modules.pop("mistapi", None)


# --- Helpers ---


def _make_manager(**overrides: object) -> GatewayTemplateConfigManager:
    """Create a manager with default mocked dependencies."""
    defaults = {
        "org_id": "org-123",
        "apisession": MagicMock(),
        "input_fn": MagicMock(return_value="0"),
        "get_csv_path_fn": MagicMock(return_value="/tmp/test"),
        "save_data_fn": MagicMock(),
        "check_and_generate_csv_fn": MagicMock(),
        "generate_sites_fn": MagicMock(),
        "sanitize_filename_fn": MagicMock(return_value="sanitized"),
    }
    defaults.update(overrides)
    return GatewayTemplateConfigManager(**defaults)  # type: ignore[arg-type]


# ================================================================
# parse_state_from_address tests
# ================================================================


class TestParseStateFromAddress:
    """Tests for the parse_state_from_address function."""

    def test_empty_address_returns_empty(self) -> None:
        assert parse_state_from_address("", "US") == ""

    def test_empty_country_returns_empty(self) -> None:
        assert parse_state_from_address("123 Main St", "") == ""

    def test_small_country_returns_empty(self) -> None:
        assert parse_state_from_address("123 Main St", "BS") == ""
        assert parse_state_from_address("123 Main St", "JM") == ""

    def test_us_comma_format(self) -> None:
        result = parse_state_from_address("123 Main St, Springfield, IL 62701", "US")
        assert result == "IL"

    def test_ca_comma_format(self) -> None:
        result = parse_state_from_address("123 King St, Toronto, ON M5V 1J2", "CA")
        assert result == "ON"

    def test_standalone_state_code(self) -> None:
        result = parse_state_from_address("123 Main St, Springfield, IL", "US")
        assert result == "IL"

    def test_space_separated_with_postal(self) -> None:
        result = parse_state_from_address("Springfield IL 62701", "US")
        assert result == "IL"

    def test_puerto_rico(self) -> None:
        result = parse_state_from_address("San Juan Puerto Rico", "US")
        assert result == "Puerto Rico"

    def test_bay_islands(self) -> None:
        result = parse_state_from_address("Roatan Bay Islands", "HN")
        assert result == "Bay Islands"


class TestParseStateCommaSeparated:
    """Tests for _parse_state_comma_separated helper."""

    def test_fewer_than_3_parts_returns_empty(self) -> None:
        assert _parse_state_comma_separated("Main St, City") == ""

    def test_us_pattern(self) -> None:
        assert _parse_state_comma_separated("123 Main, City, TX 75001") == "TX"

    def test_ca_pattern(self) -> None:
        assert _parse_state_comma_separated("123 King, Toronto, ON M5V") == "ON"


class TestParseStateSpaceSeparated:
    """Tests for _parse_state_space_separated helper."""

    def test_canada_format(self) -> None:
        result = _parse_state_space_separated("Toronto ON M5V", "CA")
        assert result == "ON"

    def test_single_word_returns_empty(self) -> None:
        result = _parse_state_space_separated("City", "US")
        assert result == ""

    def test_two_words_non_latam_returns_empty(self) -> None:
        result = _parse_state_space_separated("City State", "US")
        assert result == ""

    def test_latam_country_returns_last(self) -> None:
        result = _parse_state_space_separated("Ciudad Estado", "MX")
        assert result == "Estado"


# ================================================================
# Module-level helper function tests
# ================================================================


class TestFindPicocellPolicy:
    """Tests for _find_picocell_policy helper."""

    def test_finds_picocell(self) -> None:
        config = {
            "service_policies": [
                {"name": "Other"},
                {"name": "Picocell", "action": "allow"},
            ]
        }
        result = _find_picocell_policy(config, "TestTemplate")
        assert result is not None
        assert result["name"] == "Picocell"

    def test_no_picocell(self) -> None:
        config = {"service_policies": [{"name": "Other"}]}
        result = _find_picocell_policy(config, "TestTemplate")
        assert result is None

    def test_empty_policies(self) -> None:
        config = {"service_policies": []}
        result = _find_picocell_policy(config, "TestTemplate")
        assert result is None

    def test_non_list_policies(self) -> None:
        config = {"service_policies": "invalid"}
        result = _find_picocell_policy(config, "TestTemplate")
        assert result is None


class TestParseTemplateIndices:
    """Tests for _parse_template_indices helper."""

    def test_valid_single(self) -> None:
        available = [{"name": "A"}, {"name": "B"}]
        result = _parse_template_indices("0", available)
        assert result == [{"name": "A"}]

    def test_valid_multiple(self) -> None:
        available = [{"name": "A"}, {"name": "B"}, {"name": "C"}]
        result = _parse_template_indices("0,2", available)
        assert result is not None
        assert len(result) == 2

    def test_invalid_format(self) -> None:
        available = [{"name": "A"}]
        result = _parse_template_indices("abc", available)
        assert result is None

    def test_out_of_range_filtered(self) -> None:
        available = [{"name": "A"}]
        result = _parse_template_indices("0,5", available)
        assert result is not None
        assert len(result) == 1

    def test_all_out_of_range(self) -> None:
        available = [{"name": "A"}]
        result = _parse_template_indices("5", available)
        assert result is None


class TestMergeDiaPico:
    """Tests for _merge_dia_pico helper."""

    def test_adds_dia_pico(self) -> None:
        config: dict[str, object] = {}
        result: dict[str, object] = {"changes_made": []}
        _merge_dia_pico(config, {"strategy": "ordered"}, result)
        assert "path_preferences" in config
        assert "Added/Updated DIA_Pico" in result["changes_made"]

    def test_none_dia_pico_no_change(self) -> None:
        config: dict[str, object] = {}
        result: dict[str, object] = {"changes_made": []}
        _merge_dia_pico(config, None, result)
        assert "path_preferences" not in config


class TestMergePicocell:
    """Tests for _merge_picocell helper."""

    def test_adds_picocell_to_empty(self) -> None:
        config: dict[str, object] = {}
        result: dict[str, object] = {"changes_made": []}
        _merge_picocell(config, {"name": "Picocell"}, result)
        assert len(config["service_policies"]) == 1  # type: ignore[arg-type]

    def test_updates_existing_picocell(self) -> None:
        config: dict[str, object] = {"service_policies": [{"name": "Picocell", "old": True}]}
        result: dict[str, object] = {"changes_made": []}
        _merge_picocell(config, {"name": "Picocell", "new": True}, result)
        assert config["service_policies"][0]["new"] is True  # type: ignore[index]
        assert "Updated existing Picocell" in result["changes_made"]

    def test_none_picocell_no_change(self) -> None:
        config: dict[str, object] = {}
        result: dict[str, object] = {"changes_made": []}
        _merge_picocell(config, None, result)
        assert "service_policies" not in config


class TestInsertPicocellPolicy:
    """Tests for _insert_picocell_policy helper."""

    def test_appends_when_fewer_than_14(self) -> None:
        policies: list[dict[str, object]] = [{"name": "X"}]
        result: dict[str, object] = {"changes_made": []}
        _insert_picocell_policy(policies, {"name": "Picocell"}, result)
        assert len(policies) == 2
        assert "Added Picocell at position 2" in result["changes_made"]

    def test_inserts_at_14_when_14_or_more(self) -> None:
        policies: list[dict[str, object]] = [{"name": f"P{i}"} for i in range(15)]
        result: dict[str, object] = {"changes_made": []}
        _insert_picocell_policy(policies, {"name": "Picocell"}, result)
        assert len(policies) == 16
        assert policies[13]["name"] == "Picocell"
        assert "Inserted Picocell at position 14" in result["changes_made"]


class TestFindExistingPicocellIndex:
    """Tests for _find_existing_picocell_index helper."""

    def test_found(self) -> None:
        policies = [{"name": "X"}, {"name": "Picocell"}]
        assert _find_existing_picocell_index(policies) == 1

    def test_not_found(self) -> None:
        policies = [{"name": "X"}, {"name": "Y"}]
        assert _find_existing_picocell_index(policies) is None

    def test_empty(self) -> None:
        assert _find_existing_picocell_index([]) is None


class TestFilterSitesWithLocation:
    """Tests for _filter_sites_with_location helper."""

    def test_filters_with_country(self) -> None:
        sites = [
            {"address": "", "country_code": "US", "id": "1", "name": "S1", "gatewaytemplate_id": "t1"},
        ]
        result = _filter_sites_with_location(sites)
        assert len(result) == 1
        assert result[0]["country"] == "US"

    def test_filters_without_location(self) -> None:
        sites = [
            {"address": "", "country_code": "", "id": "1", "name": "S1", "gatewaytemplate_id": ""},
        ]
        result = _filter_sites_with_location(sites)
        assert len(result) == 0


# ================================================================
# GatewayTemplateConfigManager class tests
# ================================================================


class TestFetchTemplates:
    """Tests for _fetch_templates method."""

    def test_returns_sorted_templates(self) -> None:
        mgr = _make_manager()
        mock_resp = MagicMock()
        mock_templates = [
            {"name": "Zebra", "id": "z1"},
            {"name": "Alpha", "id": "a1"},
        ]

        with patch("src.gateway.template_config.mistapi") as mock_api:
            mock_api.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates.return_value = mock_resp
            mock_api.get_all.return_value = mock_templates
            result = mgr._fetch_templates()

        assert result is not None
        assert result[0]["name"] == "Alpha"

    def test_returns_none_on_empty(self) -> None:
        mgr = _make_manager()
        mock_resp = MagicMock()

        with patch("src.gateway.template_config.mistapi") as mock_api:
            mock_api.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates.return_value = mock_resp
            mock_api.get_all.return_value = []
            result = mgr._fetch_templates()

        assert result is None

    def test_returns_none_on_exception(self) -> None:
        mgr = _make_manager()

        with patch("src.gateway.template_config.mistapi") as mock_api:
            mock_api.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates.side_effect = RuntimeError("fail")
            result = mgr._fetch_templates()

        assert result is None


class TestSelectTemplate:
    """Tests for _select_template method."""

    def test_valid_selection(self) -> None:
        mgr = _make_manager(input_fn=MagicMock(return_value="0"))
        templates = [{"name": "T1", "type": "standalone", "id": "id1"}]
        result = mgr._select_template(templates, "extract")
        assert result is not None
        assert result["name"] == "T1"

    def test_invalid_non_numeric(self) -> None:
        mgr = _make_manager(input_fn=MagicMock(return_value="abc"))
        templates = [{"name": "T1", "type": "standalone"}]
        result = mgr._select_template(templates, "extract")
        assert result is None

    def test_out_of_range(self) -> None:
        mgr = _make_manager(input_fn=MagicMock(return_value="5"))
        templates = [{"name": "T1", "type": "standalone"}]
        result = mgr._select_template(templates, "extract")
        assert result is None

    def test_eof_returns_none(self) -> None:
        mgr = _make_manager(input_fn=MagicMock(side_effect=EOFError))
        templates = [{"name": "T1", "type": "standalone"}]
        result = mgr._select_template(templates, "extract")
        assert result is None


class TestFetchTemplateConfig:
    """Tests for _fetch_template_config method."""

    def test_returns_config_dict(self) -> None:
        mgr = _make_manager()
        mock_resp = MagicMock()
        mock_resp.data = {"name": "Test", "port_config": {}}

        with patch("src.gateway.template_config.mistapi") as mock_api:
            mock_api.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate.return_value = mock_resp
            result = mgr._fetch_template_config({"id": "t1", "name": "T1"})

        assert result == {"name": "Test", "port_config": {}}

    def test_returns_none_on_non_dict(self) -> None:
        mgr = _make_manager()
        mock_resp = MagicMock()
        mock_resp.data = "invalid"

        with patch("src.gateway.template_config.mistapi") as mock_api:
            mock_api.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate.return_value = mock_resp
            result = mgr._fetch_template_config({"id": "t1", "name": "T1"})

        assert result is None

    def test_returns_none_on_exception(self) -> None:
        mgr = _make_manager()

        with patch("src.gateway.template_config.mistapi") as mock_api:
            mock_api.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate.side_effect = RuntimeError("fail")
            result = mgr._fetch_template_config({"id": "t1", "name": "T1"})

        assert result is None


class TestExtractConfigs:
    """Tests for _extract_configs static method."""

    def test_extracts_both(self) -> None:
        config = {
            "path_preferences": {"DIA_Pico": {"strategy": "ordered"}},
            "service_policies": [{"name": "Picocell", "action": "allow"}],
        }
        result = GatewayTemplateConfigManager._extract_configs(config, {"name": "T1", "id": "id1"})
        assert result is not None
        assert result["configurations"]["traffic_steering"]["DIA_Pico"] is not None
        assert result["configurations"]["application_policies"]["Picocell"] is not None

    def test_extracts_dia_pico_only(self) -> None:
        config = {
            "path_preferences": {"DIA_Pico": {"strategy": "ordered"}},
            "service_policies": [],
        }
        result = GatewayTemplateConfigManager._extract_configs(config, {"name": "T1", "id": "id1"})
        assert result is not None

    def test_returns_none_when_neither_found(self) -> None:
        config = {"path_preferences": {}, "service_policies": []}
        result = GatewayTemplateConfigManager._extract_configs(config, {"name": "T1", "id": "id1"})
        assert result is None


class TestSaveExtraction:
    """Tests for _save_extraction method."""

    def test_saves_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "sanitized_extracted_config.json")
            mgr = _make_manager(
                get_csv_path_fn=MagicMock(return_value=filepath),
                sanitize_filename_fn=MagicMock(return_value="sanitized"),
            )
            extraction = {"source_template_name": "Test", "configurations": {}}
            mgr._save_extraction(extraction, {"name": "Test"})

            assert os.path.exists(filepath)
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
            assert data["source_template_name"] == "Test"


class TestLoadExtractionFile:
    """Tests for _load_extraction_file method."""

    def test_loads_file_successfully(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_extracted_config.json")
            test_data = {"source_template_name": "Test", "configurations": {}}
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(test_data, f)

            mgr = _make_manager(
                get_csv_path_fn=MagicMock(return_value=tmpdir),
                input_fn=MagicMock(return_value="0"),
            )
            result = mgr._load_extraction_file()
            assert result is not None
            assert result["source_template_name"] == "Test"

    def test_no_files_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = _make_manager(get_csv_path_fn=MagicMock(return_value=tmpdir))
            result = mgr._load_extraction_file()
            assert result is None


class TestSelectDestinationTemplates:
    """Tests for _select_destination_templates method."""

    def test_select_all(self) -> None:
        mgr = _make_manager(input_fn=MagicMock(return_value="all"))
        templates = [
            {"name": "T1", "id": "id1"},
            {"name": "T2", "id": "id2"},
        ]
        extraction_data = {"source_template_id": "id1"}
        result = mgr._select_destination_templates(templates, extraction_data)
        assert result is not None
        assert len(result) == 1
        assert result[0]["name"] == "T2"

    def test_select_by_index(self) -> None:
        mgr = _make_manager(input_fn=MagicMock(return_value="0"))
        templates = [
            {"name": "T1", "id": "id1"},
            {"name": "T2", "id": "id2"},
        ]
        extraction_data = {"source_template_id": "id1"}
        result = mgr._select_destination_templates(templates, extraction_data)
        assert result is not None
        assert len(result) == 1

    def test_no_other_templates(self) -> None:
        mgr = _make_manager()
        templates = [{"name": "T1", "id": "id1"}]
        extraction_data = {"source_template_id": "id1"}
        result = mgr._select_destination_templates(templates, extraction_data)
        assert result is None


class TestConfirmApply:
    """Tests for _confirm_apply method."""

    def test_confirmed(self) -> None:
        mgr = _make_manager(input_fn=MagicMock(return_value="APPLY"))
        destinations = [{"name": "T1"}]
        result = mgr._confirm_apply(destinations, {"strategy": "ordered"}, None)
        assert result is True

    def test_cancelled(self) -> None:
        mgr = _make_manager(input_fn=MagicMock(return_value="no"))
        destinations = [{"name": "T1"}]
        result = mgr._confirm_apply(destinations, None, None)
        assert result is False

    def test_eof_cancels(self) -> None:
        mgr = _make_manager(input_fn=MagicMock(side_effect=EOFError))
        destinations = [{"name": "T1"}]
        result = mgr._confirm_apply(destinations, None, None)
        assert result is False


class TestApplyToTemplates:
    """Tests for _apply_to_templates method."""

    def test_successful_apply(self) -> None:
        mgr = _make_manager()

        mock_get_resp = MagicMock()
        mock_get_resp.data = {"name": "T1", "path_preferences": {}}

        mock_update_resp = MagicMock()
        mock_update_resp.status_code = 200

        with patch("src.gateway.template_config.mistapi") as mock_api:
            mock_api.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate.return_value = mock_get_resp
            mock_api.api.v1.orgs.gatewaytemplates.updateOrgGatewayTemplate.return_value = mock_update_resp

            destinations = [{"name": "T1", "id": "id1"}]
            results = mgr._apply_to_templates(destinations, {"strategy": "x"}, None)

        assert len(results) == 1
        assert results[0]["status"] == "SUCCESS"

    def test_failed_apply(self) -> None:
        mgr = _make_manager()

        mock_get_resp = MagicMock()
        mock_get_resp.data = {"name": "T1"}

        mock_update_resp = MagicMock()
        mock_update_resp.status_code = 400

        with patch("src.gateway.template_config.mistapi") as mock_api:
            mock_api.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate.return_value = mock_get_resp
            mock_api.api.v1.orgs.gatewaytemplates.updateOrgGatewayTemplate.return_value = mock_update_resp

            destinations = [{"name": "T1", "id": "id1"}]
            results = mgr._apply_to_templates(destinations, {"strategy": "x"}, None)

        assert results[0]["status"] == "FAILED"


class TestReportApplyResults:
    """Tests for _report_apply_results method."""

    def test_calls_save_data(self) -> None:
        save_mock = MagicMock()
        mgr = _make_manager(save_data_fn=save_mock)
        results = [
            {
                "template_name": "T1",
                "template_id": "id1",
                "status": "SUCCESS",
                "changes_made": ["Added/Updated DIA_Pico"],
                "error": "",
            }
        ]
        mgr._report_apply_results(results)
        save_mock.assert_called_once()


# ================================================================
# Clone-by-location tests
# ================================================================


class TestGetUniqueLocations:
    """Tests for _get_unique_locations static method."""

    def test_separates_states_and_countries(self) -> None:
        sites = [
            {"state": "TX", "country": "US"},
            {"state": "", "country": "MX"},
            {"state": "CA", "country": "US"},
        ]
        states, countries = GatewayTemplateConfigManager._get_unique_locations(sites)
        assert states == {"TX", "CA"}
        assert countries == {"MX"}


class TestPlanTemplateCreation:
    """Tests for _plan_template_creation static method."""

    def test_creates_entries_for_states_and_countries(self) -> None:
        source = {"name": "Base"}
        states = {"TX", "CA"}
        countries = {"MX"}
        result = GatewayTemplateConfigManager._plan_template_creation(source, states, countries)
        names = [r["name"] for r in result]
        assert "Base_TX" in names
        assert "Base_CA" in names
        assert "Base_MX" in names
        assert len(result) == 3


class TestPlanSiteAssignments:
    """Tests for _plan_site_assignments static method."""

    def test_assigns_by_state_then_country(self) -> None:
        sites = [
            {"id": "s1", "name": "Site1", "state": "TX", "country": "US", "current_template_id": ""},
            {"id": "s2", "name": "Site2", "state": "", "country": "MX", "current_template_id": ""},
            {"id": "s3", "name": "Site3", "state": "", "country": "", "current_template_id": ""},
        ]
        source = {"name": "Base"}
        result = GatewayTemplateConfigManager._plan_site_assignments(sites, source)
        assert len(result) == 2
        assert result[0]["target_template_name"] == "Base_TX"
        assert result[1]["target_template_name"] == "Base_MX"


class TestConfirmClone:
    """Tests for _confirm_clone method."""

    def test_confirmed(self) -> None:
        mgr = _make_manager(input_fn=MagicMock(return_value="CLONE"))
        result = mgr._confirm_clone([{"name": "T1"}], [{"site_id": "s1"}])
        assert result is True

    def test_cancelled(self) -> None:
        mgr = _make_manager(input_fn=MagicMock(return_value="no"))
        result = mgr._confirm_clone([{"name": "T1"}], [{"site_id": "s1"}])
        assert result is False


class TestGetExistingTemplateNames:
    """Tests for _get_existing_template_names method."""

    def test_returns_name_to_id_map(self) -> None:
        mgr = _make_manager()
        mock_resp = MagicMock()

        with patch("src.gateway.template_config.mistapi") as mock_api:
            mock_api.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates.return_value = mock_resp
            mock_api.get_all.return_value = [
                {"name": "T1", "id": "id1"},
                {"name": "T2", "id": "id2"},
            ]
            result = mgr._get_existing_template_names()

        assert result == {"T1": "id1", "T2": "id2"}

    def test_returns_empty_on_error(self) -> None:
        mgr = _make_manager()

        with patch("src.gateway.template_config.mistapi") as mock_api:
            mock_api.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates.side_effect = RuntimeError("fail")
            result = mgr._get_existing_template_names()

        assert result == {}


class TestCreateTemplates:
    """Tests for _create_templates method."""

    def test_skips_existing(self) -> None:
        mgr = _make_manager()
        existing = {"Base_TX": "existing-id"}
        to_create = [{"name": "Base_TX"}]

        with patch("src.gateway.template_config.mistapi"):
            result = mgr._create_templates({"name": "Base"}, to_create, existing)

        assert result["Base_TX"] == "existing-id"

    def test_creates_new_template(self) -> None:
        mgr = _make_manager()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.data = {"id": "new-id"}

        to_create = [{"name": "Base_TX"}]

        with patch("src.gateway.template_config.mistapi") as mock_api:
            mock_api.api.v1.orgs.gatewaytemplates.createOrgGatewayTemplate.return_value = mock_resp
            result = mgr._create_templates({"name": "Base", "id": "src-id"}, to_create, {})

        assert result["Base_TX"] == "new-id"


class TestAssignSites:
    """Tests for _assign_sites method."""

    def test_assigns_successfully(self) -> None:
        mgr = _make_manager()
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        assignments = [
            {
                "site_id": "s1",
                "site_name": "Site1",
                "target_template_name": "Base_TX",
                "current_template_id": "old-id",
            }
        ]
        template_map = {"Base_TX": "new-id"}

        with patch("src.gateway.template_config.mistapi") as mock_api:
            mock_api.api.v1.sites.sites.updateSiteInfo.return_value = mock_resp
            results = mgr._assign_sites(assignments, template_map)

        assert results[0]["status"] == "ASSIGNED"

    def test_skips_when_template_not_found(self) -> None:
        mgr = _make_manager()
        assignments = [
            {
                "site_id": "s1",
                "site_name": "Site1",
                "target_template_name": "Base_TX",
                "current_template_id": "",
            }
        ]

        with patch("src.gateway.template_config.mistapi"):
            results = mgr._assign_sites(assignments, {})

        assert results[0]["status"] == "SKIPPED"

    def test_skips_already_assigned(self) -> None:
        mgr = _make_manager()
        assignments = [
            {
                "site_id": "s1",
                "site_name": "Site1",
                "target_template_name": "Base_TX",
                "current_template_id": "same-id",
            }
        ]
        template_map = {"Base_TX": "same-id"}

        with patch("src.gateway.template_config.mistapi"):
            results = mgr._assign_sites(assignments, template_map)

        assert results[0]["status"] == "SKIPPED"


class TestReportCloneResults:
    """Tests for _report_clone_results method."""

    def test_calls_save_data(self) -> None:
        save_mock = MagicMock()
        mgr = _make_manager(save_data_fn=save_mock)
        to_create = [{"name": "T1"}]
        site_results = [{"site_name": "S1", "status": "ASSIGNED", "error": ""}]
        mgr._report_clone_results(to_create, site_results)
        save_mock.assert_called_once()


# ================================================================
# Integration-style entry point tests
# ================================================================


class TestExtractEntryPoint:
    """Tests for the extract() public entry point."""

    def test_extract_no_templates(self) -> None:
        mgr = _make_manager()
        with patch.object(mgr, "_fetch_templates", return_value=None):
            mgr.extract()  # Should not raise

    def test_extract_no_selection(self) -> None:
        mgr = _make_manager()
        templates = [{"name": "T1", "id": "id1"}]
        with (
            patch.object(mgr, "_fetch_templates", return_value=templates),
            patch.object(mgr, "_select_template", return_value=None),
        ):
            mgr.extract()  # Should not raise


class TestApplyEntryPoint:
    """Tests for the apply() public entry point."""

    def test_apply_no_extraction_file(self) -> None:
        mgr = _make_manager()
        with patch.object(mgr, "_load_extraction_file", return_value=None):
            mgr.apply()  # Should not raise


class TestCloneByLocationEntryPoint:
    """Tests for the clone_by_location() public entry point."""

    def test_clone_no_sites(self) -> None:
        mgr = _make_manager()
        with patch.object(mgr, "_load_sites_with_location", return_value=None):
            mgr.clone_by_location()  # Should not raise
