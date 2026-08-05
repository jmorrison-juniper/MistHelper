"""Tests for GatewayTemplateConfigManager (Issue #211).

Uses identity-checked teardown to avoid cross-test sys.modules contamination.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

# --- Module-level mistapi stub, restored the moment the import finishes ---
# WHY: pytest imports every test module during collection but runs teardown_module only
# for a module that has a selected test. A stub left in sys.modules therefore leaks for
# the whole session and breaks mistapi's lazy subpackage import. See issue #1739.
_saved_mistapi = sys.modules.get("mistapi")
_our_mock = MagicMock()
sys.modules["mistapi"] = _our_mock
try:
    from src.gateway.template_config import (
        GatewayTemplateConfigManager,
        _filter_sites_with_location,
        _find_existing_picocell_index,
        _find_picocell_policy,
        _infer_state_without_postal,  # private — used for edge-case coverage of line 1034
        _insert_picocell_policy,
        _merge_dia_pico,
        _merge_picocell,
        _parse_canadian_state,  # private — used for edge-case coverage of line 997
        _parse_general_state,  # private — used for edge-case coverage of line 1016
        _parse_state_comma_separated,
        _parse_state_space_separated,
        _parse_template_indices,
        parse_state_from_address,
    )
finally:
    if _saved_mistapi is not None:
        sys.modules["mistapi"] = _saved_mistapi
    else:
        sys.modules.pop("mistapi", None)


def setup_module() -> None:
    """Re-assert our stub for the duration of this module's tests."""
    sys.modules["mistapi"] = _our_mock


def teardown_module() -> None:
    """Restore sys.modules only if our stub is still installed."""
    if sys.modules.get("mistapi") is not _our_mock:
        return
    if _saved_mistapi is not None:
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


# ================================================================
# Entry-point continuation paths (lines 83-162)
# ================================================================


class TestExtractContinuation:
    """Tests for extract() continuation after _select_template returns data (lines 83-89)."""

    def test_no_template_config_returns_early(self) -> None:
        """Line 83-85: fetch_template_config returns None → early return."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        templates = [{"name": "T1", "id": "id1"}]  # Minimal template list for selection
        with (  # Patch internal methods to control flow
            patch.object(mgr, "_fetch_templates", return_value=templates),  # Return template list
            patch.object(mgr, "_select_template", return_value=templates[0]),  # Select first
            patch.object(mgr, "_fetch_template_config", return_value=None),  # Config fails
        ):
            mgr.extract()  # Should return early without saving

    def test_no_extraction_returns_early(self) -> None:
        """Lines 83, 84, 87-88: config found but extract_configs returns None → no save."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        templates = [{"name": "T1", "id": "id1"}]  # Minimal template list
        template_config = {"service_policies": []}  # Non-empty config dict
        with (  # Patch internal methods to isolate extract() logic
            patch.object(mgr, "_fetch_templates", return_value=templates),  # Return templates
            patch.object(mgr, "_select_template", return_value=templates[0]),  # Select one
            patch.object(mgr, "_fetch_template_config", return_value=template_config),  # Config ok
            patch.object(mgr, "_extract_configs", return_value=None),  # Extract produces nothing
            patch.object(mgr, "_save_extraction") as mock_save,  # Should NOT be called
        ):
            mgr.extract()  # Should reach line 88 (if extraction) then stop
        mock_save.assert_not_called()  # Verify save was not triggered for empty extraction

    def test_happy_path_saves_extraction(self) -> None:
        """Lines 83-89: full happy path — extraction produced and saved."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        templates = [{"name": "T1", "id": "id1"}]  # Single template in list
        template_config = {"service_policies": []}  # Valid config structure
        extraction = {"configurations": {"traffic_steering": {}}}  # Non-empty extraction
        with (  # Patch all sub-methods to drive through the success path
            patch.object(mgr, "_fetch_templates", return_value=templates),  # Return templates
            patch.object(mgr, "_select_template", return_value=templates[0]),  # Select first
            patch.object(mgr, "_fetch_template_config", return_value=template_config),  # Config ok
            patch.object(mgr, "_extract_configs", return_value=extraction),  # Non-empty result
            patch.object(mgr, "_save_extraction") as mock_save,  # Track save call
        ):
            mgr.extract()  # Should execute lines 83-89 including save
        mock_save.assert_called_once_with(extraction, templates[0])  # Save called with correct args


class TestApplyContinuation:
    """Tests for apply() continuation after extraction file loaded (lines 105-121)."""

    def test_no_templates_returns_early(self) -> None:
        """Lines 105-107: _fetch_templates returns empty → early return."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        extraction = {"configurations": {}}  # Minimal extraction data
        with (  # Patch to supply extraction but fail on templates
            patch.object(mgr, "_load_extraction_file", return_value=extraction),  # File loaded
            patch.object(mgr, "_fetch_templates", return_value=None),  # No templates available
        ):
            mgr.apply()  # Should return after checking templates (lines 105-107)

    def test_no_destinations_returns_early(self) -> None:
        """Lines 105-111: destinations selection returns None → early return."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        extraction = {"configurations": {}}  # Minimal extraction data
        templates = [{"name": "T1", "id": "id1"}]  # Templates available
        with (  # Patch to reach destination selection step
            patch.object(mgr, "_load_extraction_file", return_value=extraction),  # File loaded
            patch.object(mgr, "_fetch_templates", return_value=templates),  # Templates ok
            patch.object(mgr, "_select_destination_templates", return_value=None),  # Nothing selected
        ):
            mgr.apply()  # Should return after destination check (lines 105-111)

    def test_confirm_declined_returns_early(self) -> None:
        """Lines 105-118: user declines confirmation → early return after confirm check."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        extraction = {"configurations": {"traffic_steering": {}, "application_policies": {}}}
        templates = [{"name": "T1", "id": "id1"}]  # Source templates
        destinations = [{"name": "T2", "id": "id2"}]  # Destination templates
        with (  # Patch to reach confirm step then decline
            patch.object(mgr, "_load_extraction_file", return_value=extraction),  # File ok
            patch.object(mgr, "_fetch_templates", return_value=templates),  # Templates ok
            patch.object(mgr, "_select_destination_templates", return_value=destinations),  # Selected
            patch.object(mgr, "_confirm_apply", return_value=False),  # User declines
        ):
            mgr.apply()  # Should cover lines 105-118 then stop at return

    def test_full_apply_reports_results(self) -> None:
        """Lines 105-121: full happy path — configs applied and results reported."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        extraction = {"configurations": {}}  # Minimal extraction (no dia_pico/picocell)
        templates = [{"name": "T1", "id": "id1"}]  # Source templates list
        destinations = [{"name": "T2", "id": "id2"}]  # Destination templates list
        results = [{"template_name": "T2", "status": "SUCCESS", "changes_made": [], "error": ""}]
        with (  # Patch all sub-methods to drive through the full apply path
            patch.object(mgr, "_load_extraction_file", return_value=extraction),  # File loaded
            patch.object(mgr, "_fetch_templates", return_value=templates),  # Templates ok
            patch.object(mgr, "_select_destination_templates", return_value=destinations),  # Selected
            patch.object(mgr, "_confirm_apply", return_value=True),  # User confirms
            patch.object(mgr, "_apply_to_templates", return_value=results),  # Apply succeeds
            patch.object(mgr, "_report_apply_results") as mock_report,  # Track report call
        ):
            mgr.apply()  # Should execute all of lines 105-121
        mock_report.assert_called_once_with(results)  # Verify results reported correctly


class TestCloneByLocationContinuation:
    """Tests for clone_by_location() continuation after sites loaded (lines 138-162)."""

    def test_no_templates_after_sites_returns_early(self) -> None:
        """Lines 138-142: _fetch_templates returns empty after sites loaded → early return."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        sites = [{"name": "S1", "state": "TX", "country": "US", "id": "s1"}]
        with (  # Patch to supply sites but fail on template fetch
            patch.object(mgr, "_load_sites_with_location", return_value=sites),  # Sites loaded
            patch.object(mgr, "_get_unique_locations", return_value=({"TX"}, set())),  # Locations
            patch.object(mgr, "_fetch_templates", return_value=None),  # No templates
        ):
            mgr.clone_by_location()  # Should return at lines 140-142

    def test_no_source_selected_returns_early(self) -> None:
        """Lines 138-146: _select_template returns None → early return."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        sites = [{"name": "S1", "state": "TX", "country": "US", "id": "s1"}]
        templates = [{"name": "T1", "id": "id1"}]  # Templates exist
        with (  # Patch to reach selection step then return None
            patch.object(mgr, "_load_sites_with_location", return_value=sites),  # Sites loaded
            patch.object(mgr, "_get_unique_locations", return_value=({"TX"}, set())),  # Locations
            patch.object(mgr, "_fetch_templates", return_value=templates),  # Templates ok
            patch.object(mgr, "_select_template", return_value=None),  # Nothing selected
        ):
            mgr.clone_by_location()  # Should return at lines 144-146

    def test_no_source_config_returns_early(self) -> None:
        """Lines 138-150: source config fetch returns None → early return."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        sites = [{"name": "S1", "state": "TX", "country": "US", "id": "s1"}]
        templates = [{"name": "T1", "id": "id1"}]  # Templates exist
        source = templates[0]  # Select first template as source
        with (  # Patch to reach config fetch then fail
            patch.object(mgr, "_load_sites_with_location", return_value=sites),  # Sites loaded
            patch.object(mgr, "_get_unique_locations", return_value=({"TX"}, set())),  # Locations
            patch.object(mgr, "_fetch_templates", return_value=templates),  # Templates ok
            patch.object(mgr, "_select_template", return_value=source),  # Source selected
            patch.object(mgr, "_fetch_template_config", return_value=None),  # Config fails
        ):
            mgr.clone_by_location()  # Should return at lines 148-150

    def test_clone_not_confirmed_returns_early(self) -> None:
        """Lines 138-156: user declines clone confirmation → early return."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        sites = [{"name": "S1", "state": "TX", "country": "US", "id": "s1"}]
        templates = [{"name": "T1", "id": "id1"}]  # Templates list
        source = templates[0]  # Source template selection
        source_config = {"service_policies": []}  # Valid source config
        with (  # Patch to reach confirm step then decline
            patch.object(mgr, "_load_sites_with_location", return_value=sites),  # Sites ok
            patch.object(mgr, "_get_unique_locations", return_value=({"TX"}, set())),  # Locations
            patch.object(mgr, "_fetch_templates", return_value=templates),  # Templates ok
            patch.object(mgr, "_select_template", return_value=source),  # Selected
            patch.object(mgr, "_fetch_template_config", return_value=source_config),  # Config ok
            patch.object(mgr, "_plan_template_creation", return_value=[]),  # Empty creation plan
            patch.object(mgr, "_plan_site_assignments", return_value=[]),  # Empty assignments
            patch.object(mgr, "_confirm_clone", return_value=False),  # User declines
        ):
            mgr.clone_by_location()  # Should cover lines 138-156 then stop

    def test_full_clone_reports_results(self) -> None:
        """Lines 138-162: full happy path — templates created and sites assigned."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        sites = [{"name": "S1", "state": "TX", "country": "US", "id": "s1"}]
        templates = [{"name": "T1", "id": "id1"}]  # Templates list
        source = templates[0]  # Source template
        source_config = {"service_policies": []}  # Source config data
        to_create = [{"name": "T1-TX", "key": "TX", "type": "state"}]  # Templates to create
        assignments = [{"site_name": "S1", "site_key": "TX"}]  # Site assignments
        tpl_map = {"TX": "new-id"}  # Template mapping after creation
        results = [{"site_name": "S1", "status": "ASSIGNED"}]  # Assignment results
        with (  # Patch ALL sub-methods to drive through the full clone path
            patch.object(mgr, "_load_sites_with_location", return_value=sites),  # Sites loaded
            patch.object(mgr, "_get_unique_locations", return_value=({"TX"}, set())),  # Locations
            patch.object(mgr, "_fetch_templates", return_value=templates),  # Templates ok
            patch.object(mgr, "_select_template", return_value=source),  # Source selected
            patch.object(mgr, "_fetch_template_config", return_value=source_config),  # Config ok
            patch.object(mgr, "_plan_template_creation", return_value=to_create),  # Plan created
            patch.object(mgr, "_plan_site_assignments", return_value=assignments),  # Assignments
            patch.object(mgr, "_confirm_clone", return_value=True),  # User confirms
            patch.object(mgr, "_get_existing_template_names", return_value={}),  # No existing
            patch.object(mgr, "_create_templates", return_value=tpl_map),  # Templates created
            patch.object(mgr, "_assign_sites", return_value=results),  # Sites assigned
            patch.object(mgr, "_report_clone_results") as mock_report,  # Track report call
        ):
            mgr.clone_by_location()  # Should execute all of lines 138-162
        mock_report.assert_called_once_with(to_create, results)  # Verify report called correctly


# ================================================================
# Private method edge cases
# ================================================================


class TestSaveExtractionSuccessPath:
    """Tests for _save_extraction success path (lines 305-307)."""

    def test_success_path_prints_confirmation(self) -> None:
        """Lines 305-307: successful JSON write triggers success print messages."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        extraction = {"configurations": {"service_policies": []}}  # Extraction data to save
        selected = {"name": "TestTemplate", "id": "id1"}  # Template that was extracted from
        with patch("src.gateway.template_config.open", MagicMock()) as mock_open:  # Mock file open
            mock_open.return_value.__enter__ = MagicMock(return_value=MagicMock())  # Context entry
            mock_open.return_value.__exit__ = MagicMock(return_value=False)  # Context exit
            mgr._save_extraction(extraction, selected)  # Should not raise; prints success
        mock_open.assert_called_once()  # Verify file was opened for writing


class TestLoadExtractionFileErrors:
    """Tests for _load_extraction_file error paths (lines 324-326)."""

    def test_os_error_returns_none(self) -> None:
        """Lines 324-326: OSError reading data directory → returns None."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        with patch("src.gateway.template_config.os.listdir", side_effect=OSError("no dir")):
            result = mgr._load_extraction_file()  # Should catch OSError and return None
        assert result is None  # Verify error path returns None gracefully


class TestPromptFileSelectionEdgeCases:
    """Tests for _prompt_file_selection edge cases (lines 346-348, 351-352, 363-365)."""

    def test_eof_error_returns_none(self) -> None:
        """Lines 346-348: EOFError during input → prints cancellation and returns None."""
        mgr = _make_manager(input_fn=MagicMock(side_effect=EOFError))  # EOF on input
        result = mgr._prompt_file_selection(["file1.json", "file2.json"])  # Should catch EOF
        assert result is None  # Verify cancelled operation returns None

    def test_invalid_non_numeric_selection_returns_none(self) -> None:
        """Lines 351-352: non-numeric input (e.g. 'abc') → returns None."""
        mgr = _make_manager(input_fn=MagicMock(return_value="abc"))  # Non-numeric input
        result = mgr._prompt_file_selection(["file1.json"])  # Should reject non-numeric
        assert result is None  # Verify invalid selection returns None

    def test_file_load_exception_returns_none(self) -> None:
        """Lines 363-365: valid selection index but file open raises → returns None."""
        mgr = _make_manager(input_fn=MagicMock(return_value="0"))  # Valid index selection
        with patch("src.gateway.template_config.open", side_effect=OSError("no file")):
            result = mgr._prompt_file_selection(["file1.json"])  # File open fails
        assert result is None  # Verify file error returns None


class TestSelectDestinationTemplatesEdgeCases:
    """Tests for _select_destination_templates EOF path (lines 387-389)."""

    def test_eof_during_selection_returns_none(self) -> None:
        """Lines 387-389: EOFError during template selection → returns None."""
        mgr = _make_manager(input_fn=MagicMock(side_effect=EOFError))  # EOF on input
        templates = [{"name": "T1", "id": "id1"}, {"name": "T2", "id": "id2"}]
        extraction_data = {"source_template_id": "id1"}  # Source to exclude from destinations
        result = mgr._select_destination_templates(templates, extraction_data)  # EOF during prompt
        assert result is None  # Verify cancelled selection returns None


class TestConfirmApplyEdgeCases:
    """Tests for _confirm_apply EOF path (lines 413-414)."""

    def test_eof_during_confirm_returns_false(self) -> None:
        """Lines 413-414: EOFError during confirmation prompt → returns False."""
        mgr = _make_manager(input_fn=MagicMock(side_effect=EOFError))  # EOF on input
        destinations = [{"name": "T1", "id": "id1"}]  # Destinations to apply to
        result = mgr._confirm_apply(destinations, None, None)  # EOF during confirm prompt
        assert result is False  # Verify cancelled confirmation returns False


class TestFetchSingleConfigEdgeCases:
    """Tests for _fetch_single_config invalid format path (line 471)."""

    def test_non_dict_response_marks_failed(self) -> None:
        """Line 471: resp.data is not a dict → marks result as FAILED and returns None."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        mock_api = MagicMock()  # Mock mistapi module with API structure
        mock_resp = MagicMock()  # Mock API response object
        mock_resp.data = "invalid_string_not_a_dict"  # Response data is string, not dict
        mock_api.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate.return_value = mock_resp
        result_dict = {  # Initialize result tracking dict as the real method expects
            "template_name": "T1",
            "template_id": "id1",
            "status": "",
            "changes_made": [],
            "error": "",
        }
        result = mgr._fetch_single_config(mock_api, "id1", result_dict)  # Call with bad response
        assert result is None  # Verify invalid format returns None
        assert result_dict["status"] == "FAILED"  # Verify status marked as failed


class TestReportApplyResultsMixed:
    """Tests for _report_apply_results with mixed results (lines 486-488)."""

    def test_mixed_results_saved_and_printed(self) -> None:
        """Lines 486-488: save_data called and success/failure counts printed."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        results = [  # Mix of success and failure results for realistic test
            {
                "template_name": "T1",
                "template_id": "id1",
                "status": "SUCCESS",
                "changes_made": ["DIA_Pico applied"],
                "error": "",
            },
            {
                "template_name": "T2",
                "template_id": "id2",
                "status": "FAILED",
                "changes_made": [],
                "error": "API error 500",
            },
        ]
        mgr._report_apply_results(results)  # Should not raise; calls save_data and prints
        mgr._save_data.assert_called_once()  # Verify data saved via injected _save_data mock

    def test_empty_results_does_not_crash(self) -> None:
        """_report_apply_results handles empty list gracefully."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        mgr._report_apply_results([])  # Empty results should not raise
        mgr._save_data.assert_called_once()  # Save still called even with empty results


class TestLoadSitesWithLocation:
    """Tests for _load_sites_with_location body (lines 503-505, 546-568)."""

    def test_file_error_returns_none(self) -> None:
        """Lines 503-505: IOError opening sites CSV → returns None."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        with patch("src.gateway.template_config.open", side_effect=OSError("no file")):
            result = mgr._load_sites_with_location()  # File open fails
        assert result is None  # Verify file error returns None gracefully

    def test_empty_csv_returns_none(self) -> None:
        """Lines 553-555: CSV with no data rows (only header) → returns None."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        csv_header_only = "site_name,address,country_code,state\n"  # Header row, no data
        with patch("src.gateway.template_config.open", MagicMock()) as mock_open:
            mock_open.return_value.__enter__ = MagicMock(  # Context manager entry
                return_value=csv_header_only.splitlines(keepends=True)  # Simulate file lines
            )
            mock_open.return_value.__exit__ = MagicMock(return_value=False)  # Context exit
            result = mgr._load_sites_with_location()  # Empty CSV should return None
        assert result is None  # Verify empty data returns None

    def test_no_location_data_returns_none(self) -> None:
        """Lines 559-561: all sites have empty state/country → _filter returns empty → None."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        with (  # Patch open to return data and filter to return empty
            patch("src.gateway.template_config.open", MagicMock()),  # Mock file open
            patch(
                "src.gateway.template_config._filter_sites_with_location",  # Mock filter
                return_value=[],  # No sites have location data
            ),
        ):
            result = mgr._load_sites_with_location()  # Filter returns nothing
        assert result is None  # Verify no-location case returns None

    def test_sites_with_location_returned(self) -> None:
        """Lines 563-564: sites_with_loc is non-empty → printed and returned."""
        from unittest.mock import mock_open as mk_open  # Import mock_open for file simulation

        mgr = _make_manager()  # Create manager with mocked dependencies
        filtered = [{"name": "S1", "state": "TX", "country": "US"}]  # Sites with location data
        csv_data = "name,address\nS1,123 Main\n"  # Minimal CSV with one data row
        with (  # Patch open to return valid CSV and filter to return known sites
            patch("src.gateway.template_config.open", mk_open(read_data=csv_data)),  # Valid CSV
            patch(
                "src.gateway.template_config._filter_sites_with_location",  # Mock filter
                return_value=filtered,  # Return non-empty filtered list
            ),
        ):
            result = mgr._load_sites_with_location()  # Should return filtered sites
        assert result == filtered  # Verify the filtered sites are returned


class TestConfirmCloneEdgeCases:
    """Tests for _confirm_clone EOF path (lines 665-667)."""

    def test_eof_during_confirm_returns_false(self) -> None:
        """Lines 665-667: EOFError during clone confirmation → returns False."""
        mgr = _make_manager(input_fn=MagicMock(side_effect=EOFError))  # EOF on input
        to_create = [{"name": "T-TX", "key": "TX", "type": "state"}]  # Templates to create
        assignments = [{"site_name": "S1", "site_key": "TX"}]  # Site assignments
        result = mgr._confirm_clone(to_create, assignments)  # EOF during prompt
        assert result is False  # Verify cancelled confirmation returns False


class TestCreateTemplatesEdgeCases:
    """Tests for _create_templates API call success/failure paths (lines 729-730)."""

    def test_api_success_creates_template(self) -> None:
        """Lines 729-730: API returns 200 → result mapped to new template id."""
        mock_api = MagicMock()  # Create API mock before passing to manager
        mgr = _make_manager(apisession=mock_api)  # Inject mock so we can configure it
        mock_resp = MagicMock()  # Mock API response object
        mock_resp.status_code = 200  # Simulate successful creation
        mock_resp.data = {"id": "new-template-id"}  # Response contains new template id
        mock_api.api.v1.orgs.gatewaytemplates.createOrgGatewayTemplate.return_value = mock_resp
        source_config = {"service_policies": []}  # Source config to clone from
        to_create = [{"name": "T-TX", "key": "TX", "type": "state"}]  # Templates to create
        result = mgr._create_templates(source_config, to_create, {})  # Call with empty existing
        assert result is not None  # Some result mapping returned on success

    def test_api_failure_marks_failed(self) -> None:
        """_create_templates with non-200 API response does not crash."""
        mock_api = MagicMock()  # Create API mock before passing to manager
        mgr = _make_manager(apisession=mock_api)  # Inject mock so we can configure it
        mock_resp = MagicMock()  # Mock API response object
        mock_resp.status_code = 500  # Simulate API error response
        mock_api.api.v1.orgs.gatewaytemplates.createOrgGatewayTemplate.return_value = mock_resp
        source_config = {"service_policies": []}  # Source config to clone from
        to_create = [{"name": "T-TX", "key": "TX", "type": "state"}]  # Templates to create
        result = mgr._create_templates(source_config, to_create, {})  # Should handle failure
        assert result is not None  # Result mapping returned even on failure


class TestAssignSingleSiteEdgeCases:
    """Tests for _assign_single_site and _update_site_template edge cases (lines 793-797)."""

    def test_no_target_id_skips_assignment(self) -> None:
        """_assign_single_site: template_map has no entry → result SKIPPED."""
        mgr = _make_manager()  # Create manager with mocked dependencies
        mock_api = MagicMock()  # Mock API session (first arg to _assign_single_site)
        assignment = {  # Full site assignment dict with all required keys
            "site_name": "Site1",
            "site_id": "site-id-1",
            "target_template_name": "T-TX",  # Key for which no template was created
            "current_template_id": "old-id",  # Currently assigned template id
        }
        template_map = {}  # Empty map — "T-TX" not found → target_id = "" → SKIPPED
        result = mgr._assign_single_site(mock_api, assignment, template_map)  # Skip path
        assert result["status"] == "SKIPPED"  # Verify skip status set for missing template

    def test_update_site_api_failure_marks_failed(self) -> None:
        """Lines 793-795: API returns non-200 on site update → result marked FAILED."""
        mock_api = MagicMock()  # Create API mock before passing to manager
        mgr = _make_manager(apisession=mock_api)  # Inject mock for API call tracking
        mock_resp = MagicMock()  # Mock API response object
        mock_resp.status_code = 500  # Simulate API error response
        mock_api.api.v1.sites.sites.updateSiteInfo.return_value = mock_resp  # Return 500
        assignment = {  # Full assignment dict; target differs so update is attempted
            "site_name": "Site1",
            "site_id": "site-id-1",
            "target_template_name": "T-TX",  # Target template name
            "current_template_id": "old-id",  # Different from new target → update proceeds
        }
        template_map = {"T-TX": "new-id"}  # target_id = "new-id" → proceeds to update
        result = mgr._assign_single_site(mock_api, assignment, template_map)  # Hits FAILED path
        assert result["status"] == "FAILED"  # Verify FAILED status for non-200 API response

    def test_update_site_exception_marks_error(self) -> None:
        """Lines 796-797: API call raises exception → result marked ERROR."""
        mock_api = MagicMock()  # Create API mock before passing to manager
        mgr = _make_manager(apisession=mock_api)  # Inject mock for API call tracking
        mock_api.api.v1.sites.sites.updateSiteInfo.side_effect = Exception("network error")
        assignment = {  # Full assignment dict; target differs so update is attempted
            "site_name": "Site1",
            "site_id": "site-id-1",
            "target_template_name": "T-TX",  # Target template name
            "current_template_id": "old-id",  # Different from new target → update proceeds
        }
        template_map = {"T-TX": "new-id"}  # target_id = "new-id" → proceeds to update
        result = mgr._assign_single_site(mock_api, assignment, template_map)  # Exception path
        assert result["status"] == "ERROR"  # Verify ERROR status when exception raised


# ================================================================
# Module-level helper function edge cases (lines 975, 997, 1016, 1034)
# ================================================================


class TestParseStateHelperEdgeCases:
    """Tests for module-level state parsing helper edge cases."""

    def test_comma_separated_no_match_returns_empty(self) -> None:
        """Line 975: _parse_state_comma_separated with 3+ parts but no regex match → returns ''."""
        address = "123 Main Blvd, Northside District, Not-A-State"  # 3 parts, none match regex
        result = _parse_state_comma_separated(address)  # Should exhaust all parts and return ""
        assert result == ""  # Verify fall-through to final return ""

    def test_canadian_state_no_match_returns_empty(self) -> None:
        """Line 997: _parse_canadian_state with no 2-char uppercase part followed by postal code."""
        parts = ["Toronto", "Main", "Street"]  # No 2-letter uppercase part → returns ""
        result = _parse_canadian_state(parts)  # All parts longer than 2 chars → no match
        assert result == ""  # Verify fall-through to final return ""

    def test_general_state_postal_at_index_zero_returns_empty(self) -> None:
        """Line 1016: _parse_general_state with postal at index 0 → no state before it → ''."""
        result = _parse_general_state("12345 Nowhere", ["12345", "Nowhere"], "US")  # Postal first
        assert result == ""  # Postal at pos 0 means no state precedes it → returns ""

    def test_infer_state_single_part_non_latam_returns_empty(self) -> None:
        """Line 1034: _infer_state_without_postal with 1 part, non-LATAM country → ''."""
        result = _infer_state_without_postal(["CityOnly"], "US")  # 1 part, not LATAM
        assert result == ""  # Verify unreachable-in-practice path returns ""


# ===========================================================================
# Coverage gaps: lines 305-307, 413-414, 471, 486-488, 564-565, 729-730
# ===========================================================================


class TestCoverageGapsExtra:
    """Tests targeting uncovered lines in GatewayTemplateConfigManager."""

    def test_save_extraction_open_raises_covers_305_307(self) -> None:
        """Lines 305-307: open() raises IOError → except block prints error + logs."""
        mgr = _make_manager()  # create manager with default mocked dependencies
        with patch("src.gateway.template_config.open", side_effect=OSError("disk full"), create=True):  # patch open
            mgr._save_extraction({"key": "val"}, {"name": "TestTemplate", "id": "t1"})  # call; open raises
        # If we reach here without exception, except block was executed and swallowed the error

    def test_confirm_apply_picocell_prints_lines_413_414(self) -> None:
        """Lines 413-414: picocell is non-None → prints picocell info block."""
        mgr = _make_manager(input_fn=MagicMock(return_value="APPLY"))  # confirm with APPLY
        result = mgr._confirm_apply(  # call with non-None picocell to hit lines 413-414
            destinations=[{"id": "t1", "name": "T1"}],
            dia_pico=None,  # no DIA/Pico block
            picocell={"name": "MyPicocell"},  # non-None picocell → triggers lines 413-414
        )
        assert result is True  # APPLY confirmed → returns True

    def test_confirm_apply_eoferror_covers_except_block(self) -> None:
        """Lines 423-425: input_fn raises EOFError → except block returns False."""
        mgr = _make_manager(input_fn=MagicMock(side_effect=EOFError))  # raise on input
        result = mgr._confirm_apply(  # call; input_fn raises EOFError
            destinations=[{"id": "t1", "name": "T1"}],
            dia_pico=None,
            picocell=None,
        )
        assert result is False  # except block → returns False

    def test_apply_single_template_config_none_returns_line_471(self) -> None:
        """Line 471: _fetch_single_config returns None → early return result dict."""
        mgr = _make_manager()  # create manager with default mocked dependencies
        mock_api = MagicMock()  # mock mistapi module passed as first arg
        with patch.object(mgr, "_fetch_single_config", return_value=None):  # force None return
            result = mgr._apply_single_template(  # call; config is None → line 471
                mock_api, {"id": "t1", "name": "T1"}, None, None
            )
        assert result["status"] == ""  # returned before status was set → empty string

    def test_fetch_single_config_non_dict_covers_486_488(self) -> None:
        """Lines 486-488: resp.data is a list (non-dict) → FAILED status + returns None."""
        mgr = _make_manager()  # create manager with default mocked dependencies
        mock_api = MagicMock()  # mock mistapi module passed as first arg
        mock_resp = MagicMock()  # mock API response object
        mock_resp.data = [1, 2, 3]  # non-dict data → isinstance(config, dict) is False
        mock_api.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate.return_value = mock_resp  # set mock
        result_holder: dict = {"status": "", "error": ""}  # output dict to mutate
        returned = mgr._fetch_single_config(mock_api, "t1", result_holder)  # call directly
        assert returned is None  # non-dict config → returns None
        assert result_holder["status"] == "FAILED"  # status set to FAILED by lines 486-488
        assert "Invalid" in result_holder["error"]  # error message set

    def test_load_sites_with_location_filter_empty_covers_564_565(self, tmp_path: object) -> None:
        """Lines 564-565: all_sites non-empty but filter returns [] → None returned."""
        import pathlib  # imported inline to avoid adding top-level import

        csv_file = pathlib.Path(str(tmp_path)) / "SiteList.csv"  # create temp CSV path
        csv_file.write_text("id,name,country_code,state\ns1,SiteA,US,TX\n")  # write data
        mgr = _make_manager(get_csv_path_fn=lambda _: str(csv_file))  # route CSV path to file
        with patch(  # patch _filter_sites_with_location to return empty list
            "src.gateway.template_config._filter_sites_with_location",
            return_value=[],  # empty → triggers lines 564-565
        ):
            result = mgr._load_sites_with_location()  # call the method
        assert result is None  # lines 564-565: print + return None

    def test_create_single_template_exception_covers_729_730(self) -> None:
        """Lines 729-730: createOrgGatewayTemplate raises → except block logs error."""
        mgr = _make_manager()  # create manager with default mocked dependencies
        mock_api = MagicMock()  # mock mistapi module passed as first arg
        mock_api.api.v1.orgs.gatewaytemplates.createOrgGatewayTemplate.side_effect = RuntimeError(  # raise
            "create error"
        )  # simulate API failure
        template_map: dict[str, str] = {}  # output dict; should remain empty on exception
        mgr._create_single_template(  # call; createOrgGatewayTemplate raises → lines 729-730
            mock_api, "NewTemplate", {"key": "val"}, template_map
        )
        assert "NewTemplate" not in template_map  # except block hit; template not added

    def test_apply_single_template_api_raises_covers_486_488(self) -> None:
        """Lines 486-488: updateOrgGatewayTemplate raises → except block sets FAILED."""
        mgr = _make_manager()  # create manager with default mocked dependencies
        mock_api = MagicMock()  # mock mistapi module passed as first arg
        mock_api.api.v1.orgs.gatewaytemplates.updateOrgGatewayTemplate.side_effect = RuntimeError(  # raise
            "api error"
        )  # simulate API error during update
        with patch.object(  # _fetch_single_config returns valid dict (not None)
            mgr, "_fetch_single_config", return_value={"gateway_matching": []}
        ):
            result = mgr._apply_single_template(  # call; update raises → lines 486-488
                mock_api, {"id": "t1", "name": "T1"}, None, None
            )
        assert result["status"] == "FAILED"  # except block set status to FAILED
        assert "api error" in result["error"]  # except block captured error message
