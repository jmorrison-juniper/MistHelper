"""Unit tests for extracted SiteConfigManager logic."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.site import site_config_manager as module
from src.site.site_config_manager import SiteConfigManager
from src.site.site_config_manager import configure_site_config_manager_dependencies


def _configure_dependencies() -> None:
    """Configure minimal dependency graph for SiteConfigManager unit tests."""
    configure_site_config_manager_dependencies(
        apisession_dependency=object(),
        config_utils=SimpleNamespace(
            get_cached_or_prompted_org_id=MagicMock(return_value="org-1"),
            check_stop_signal=MagicMock(return_value=False),
        ),
        file_path_utils=SimpleNamespace(get_csv_path=MagicMock(return_value="test.csv")),
        input_utils=SimpleNamespace(safe_input=MagicMock(return_value="CREATE")),
        data_exporter=SimpleNamespace(save_data_to_output=MagicMock()),
        mistapi_dependency=SimpleNamespace(),
        default_api_page_limit=1000,
    )


def test_confirm_test_site_creation_requires_exact_keyword() -> None:
    """Menu 171 confirmation accepts only exact CREATE keyword."""
    _configure_dependencies()
    module.InputUtils.safe_input = MagicMock(return_value="create")
    assert SiteConfigManager._confirm_test_site_creation() is False

    module.InputUtils.safe_input = MagicMock(return_value="CREATE")
    assert SiteConfigManager._confirm_test_site_creation() is True


def test_build_site_payload_omits_missing_optional_fields() -> None:
    """Site payload builder keeps required name and excludes empty optional values."""
    _configure_dependencies()

    payload = SiteConfigManager._build_site_payload(
        {
            "name": "Lab Site",
            "address": "",
            "country_code": "US",
            "timezone": "America/New_York",
            "lat": "",
            "lng": "",
        }
    )

    assert payload is not None
    assert payload["name"] == "Lab Site"
    assert payload["country_code"] == "US"
    assert payload["timezone"] == "America/New_York"
    assert "address" not in payload
    assert "latlng" not in payload


def test_confirm_profile_assignment_requires_assign_keyword() -> None:
    """Menu 174 confirmation gate enforces exact ASSIGN keyword."""
    _configure_dependencies()
    module.InputUtils.safe_input = MagicMock(return_value="yes")
    assert SiteConfigManager._confirm_profile_assignment([{"mac": "a"}], []) is False

    module.InputUtils.safe_input = MagicMock(return_value="ASSIGN")
    assert SiteConfigManager._confirm_profile_assignment([{"mac": "a"}], []) is True


def test_analyze_ap_profile_matching_categorizes_records_correctly() -> None:
    """AP profile matcher separates matching, missing-profile, and missing-model records."""
    _configure_dependencies()

    with_profile, without_profile, without_model = SiteConfigManager._analyze_ap_profile_matching(
        all_aps=[
            {"mac": "aa", "name": "ap-a", "model": "AP32"},
            {"mac": "bb", "name": "ap-b", "model": "AP43"},
            {"mac": "cc", "name": "ap-c"},
        ],
        profile_map={"AP-AP32": "prof-1"},
    )

    assert len(with_profile) == 1
    assert with_profile[0]["profile_name"] == "AP-AP32"
    assert len(without_profile) == 1
    assert without_profile[0]["expected_profile"] == "AP-AP43"
    assert len(without_model) == 1
    assert without_model[0]["mac"] == "cc"
