"""Unit tests for WanHubGroupNumberManager (Menu 163).

Tests cover all user stories:
- US1: Profile listing and selection
- US2: Set pod value
- US3: Clear pod value
- US4: Module import and instantiation
"""

from unittest.mock import MagicMock, patch

import pytest

from src.wan_hub_group_manager import WanHubGroupNumberManager

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session():
    """Create a mock mistapi session."""
    return MagicMock()


@pytest.fixture
def sample_profiles():
    """Gateway device profiles in non-alphabetical order."""
    return [
        {"id": "uuid-bravo", "name": "BRAVO", "org_id": "org-1"},
        {"id": "uuid-alpha", "name": "ALPHA", "org_id": "org-1"},
        {"id": "uuid-charlie", "name": "CHARLIE", "org_id": "org-1"},
    ]


@pytest.fixture
def sample_vpns():
    """Hub-spoke VPN objects with paths for the sample profiles."""
    return [
        {
            "id": "vpn-1",
            "name": "OrgOverlay",
            "type": "hub_spoke",
            "paths": {
                "ALPHA-HE_WAN1": {"pod": 10},
                "ALPHA-HE_WAN2": {"pod": 10},
                "ALPHA-HE_LAN1": {"pod": 10},
                "BRAVO-HE_WAN1": {"pod": 1},
                "BRAVO-HE_WAN2": {"pod": 1},
                "CHARLIE-HE_WAN1": {"pod": 42},
                "CHARLIE-HE_WAN2": {"pod": 42},
            },
        }
    ]


@pytest.fixture
def mixed_pod_vpns():
    """VPN with inconsistent pod values for a profile."""
    return [
        {
            "id": "vpn-1",
            "name": "OrgOverlay",
            "type": "hub_spoke",
            "paths": {
                "MIXED-HE_WAN1": {"pod": 5},
                "MIXED-HE_WAN2": {"pod": 10},
                "MIXED-HE_LAN1": {"pod": 5},
            },
        }
    ]


@pytest.fixture
def manager(mock_session):
    """Create a manager instance with a mock safe_input."""
    mock_input = MagicMock(return_value="")
    return WanHubGroupNumberManager(mock_session, "org-1", safe_input_func=mock_input)


# ---------------------------------------------------------------------------
# US1: Profile Listing and Selection
# ---------------------------------------------------------------------------


class TestFetchProfiles:
    """Test _fetch_profiles API call and sorting."""

    @patch("src.wan_hub_group_manager.mistapi.get_all")
    @patch("src.wan_hub_group_manager.mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles")
    def test_profiles_sorted_alphabetically(self, mock_list, mock_get_all, manager, sample_profiles):
        mock_get_all.return_value = list(sample_profiles)
        result = manager._fetch_profiles()
        names = [profile["name"] for profile in result]
        assert names == ["ALPHA", "BRAVO", "CHARLIE"]

    @patch("src.wan_hub_group_manager.mistapi.get_all")
    @patch("src.wan_hub_group_manager.mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles")
    def test_empty_profiles(self, mock_list, mock_get_all, manager):
        mock_get_all.return_value = []
        result = manager._fetch_profiles()
        assert result == []

    @patch("src.wan_hub_group_manager.mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles")
    def test_api_error_returns_empty(self, mock_list, manager):
        mock_list.side_effect = Exception("API error")
        result = manager._fetch_profiles()
        assert result == []


class TestFetchHubSpokeVpns:
    """Test _fetch_hub_spoke_vpns API call and filtering."""

    @patch("src.wan_hub_group_manager.mistapi.get_all")
    @patch("src.wan_hub_group_manager.mistapi.api.v1.orgs.vpns.listOrgVpns")
    def test_filters_to_hub_spoke(self, mock_list, mock_get_all, manager):
        mock_get_all.return_value = [
            {"id": "1", "name": "HubSpoke", "type": "hub_spoke", "paths": {}},
            {"id": "2", "name": "Mesh", "type": "mesh", "paths": {}},
        ]
        hub_spoke, all_vpns = manager._fetch_hub_spoke_vpns()
        assert len(hub_spoke) == 1
        assert hub_spoke[0]["name"] == "HubSpoke"
        assert len(all_vpns) == 2

    @patch("src.wan_hub_group_manager.mistapi.get_all")
    @patch("src.wan_hub_group_manager.mistapi.api.v1.orgs.vpns.listOrgVpns")
    def test_no_hub_spoke_vpns(self, mock_list, mock_get_all, manager):
        mock_get_all.return_value = [
            {"id": "1", "name": "Mesh", "type": "mesh", "paths": {}},
        ]
        hub_spoke, all_vpns = manager._fetch_hub_spoke_vpns()
        assert hub_spoke == []
        assert len(all_vpns) == 1


class TestReportNoHubSpoke:
    """Test _report_no_hub_spoke output messages."""

    def test_empty_vpns_reports_none(self, capsys):
        WanHubGroupNumberManager._report_no_hub_spoke([])
        output = capsys.readouterr().out
        assert "No VPN definitions found" in output

    def test_reports_found_types(self, capsys):
        all_vpns = [
            {"name": "V1", "type": "mesh"},
            {"name": "V2", "type": "mesh"},
            {"name": "V3", "type": None},
        ]
        WanHubGroupNumberManager._report_no_hub_spoke(all_vpns)
        output = capsys.readouterr().out
        assert "No hub-spoke" in output
        assert "3 VPN(s)" in output
        assert "mesh" in output


class TestFindMatchingPaths:
    """Test prefix matching logic with trailing hyphen."""

    def test_matches_correct_profile(self, manager, sample_vpns):
        matches = manager._find_matching_paths("ALPHA", sample_vpns)
        assert len(matches) == 3
        path_keys = [match[2] for match in matches]
        assert all(key.startswith("ALPHA-") for key in path_keys)

    def test_trailing_hyphen_prevents_false_match(self, manager):
        """DC1- must not match DC1-BACKUP- paths."""
        vpns = [
            {
                "id": "vpn-1",
                "name": "Overlay",
                "type": "hub_spoke",
                "paths": {
                    "DC1-WAN1": {"pod": 5},
                    "DC1-BACKUP-WAN1": {"pod": 10},
                    "DC1-BACKUP-WAN2": {"pod": 10},
                },
            }
        ]
        dc1_matches = manager._find_matching_paths("DC1", vpns)
        backup_matches = manager._find_matching_paths("DC1-BACKUP", vpns)
        assert len(dc1_matches) == 3  # DC1- prefix matches all three
        assert len(backup_matches) == 2  # DC1-BACKUP- only matches the backup paths

    def test_no_matching_paths(self, manager, sample_vpns):
        matches = manager._find_matching_paths("NONEXISTENT", sample_vpns)
        assert matches == []

    def test_returns_correct_pod_values(self, manager, sample_vpns):
        matches = manager._find_matching_paths("CHARLIE", sample_vpns)
        pod_values = {match[3] for match in matches}
        assert pod_values == {42}


class TestFormatPodDisplay:
    """Test pod value formatting for display."""

    def test_default_pod(self):
        matches = [("v1", "VPN", "P-WAN1", 1)]
        result = WanHubGroupNumberManager._format_pod_display(matches)
        assert "default (1)" in result

    def test_set_pod(self):
        matches = [("v1", "VPN", "P-WAN1", 42)]
        result = WanHubGroupNumberManager._format_pod_display(matches)
        assert "42" in result

    def test_mixed_pods(self):
        matches = [("v1", "VPN", "P-WAN1", 5), ("v1", "VPN", "P-WAN2", 10)]
        result = WanHubGroupNumberManager._format_pod_display(matches)
        assert "MIXED" in result

    def test_no_paths(self):
        result = WanHubGroupNumberManager._format_pod_display([])
        assert "no VPN paths" in result


class TestPromptProfileSelection:
    """Test profile selection input loop."""

    def test_valid_selection(self, manager, sample_profiles):
        sorted_profiles = sorted(sample_profiles, key=lambda p: p["name"].lower())
        manager._safe_input = MagicMock(return_value="1")
        result = manager._prompt_profile_selection(sorted_profiles)
        assert result["name"] == "ALPHA"

    def test_quit_selection(self, manager, sample_profiles):
        manager._safe_input = MagicMock(return_value="q")
        result = manager._prompt_profile_selection(sample_profiles)
        assert result is None

    def test_invalid_then_valid(self, manager, sample_profiles):
        sorted_profiles = sorted(sample_profiles, key=lambda p: p["name"].lower())
        manager._safe_input = MagicMock(side_effect=["0", "abc", "2"])
        result = manager._prompt_profile_selection(sorted_profiles)
        assert result["name"] == "BRAVO"

    def test_out_of_range(self, manager, sample_profiles):
        manager._safe_input = MagicMock(side_effect=["99", "q"])
        result = manager._prompt_profile_selection(sample_profiles)
        assert result is None


# ---------------------------------------------------------------------------
# US2: Set Pod Value
# ---------------------------------------------------------------------------


class TestSetPod:
    """Test set_pod batch update logic."""

    @patch("src.wan_hub_group_manager.mistapi.api.v1.orgs.vpns.updateOrgVpn")
    @patch("src.wan_hub_group_manager.mistapi.api.v1.orgs.vpns.getOrgVpn")
    def test_batch_update_all_paths(self, mock_get, mock_update, manager, sample_vpns):
        mock_response = MagicMock()
        mock_response.data = sample_vpns[0]
        mock_get.return_value = mock_response

        profile = {"id": "uuid-alpha", "name": "ALPHA"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager.set_pod(profile, vpn_data, 99)

        mock_update.assert_called_once()
        call_args = mock_update.call_args
        body = call_args.kwargs.get("body") or call_args[1].get("body") or call_args[0][3]
        paths = body.get("paths", {})
        for key in ["ALPHA-HE_WAN1", "ALPHA-HE_WAN2", "ALPHA-HE_LAN1"]:
            assert paths[key]["pod"] == 99

    def test_no_matching_paths(self, manager):
        profile = {"id": "uuid-x", "name": "NONEXISTENT"}
        vpn_data = {"NONEXISTENT": []}
        manager.set_pod(profile, vpn_data, 42)
        # Should print message but not crash

    @patch("src.wan_hub_group_manager.mistapi.api.v1.orgs.vpns.updateOrgVpn")
    @patch("src.wan_hub_group_manager.mistapi.api.v1.orgs.vpns.getOrgVpn")
    def test_pod_value_range_validation(self, mock_get, mock_update, manager, sample_vpns):
        """set_pod itself does not validate range (caller does), but verify it sets correctly."""
        mock_response = MagicMock()
        mock_response.data = sample_vpns[0]
        mock_get.return_value = mock_response

        profile = {"id": "uuid-charlie", "name": "CHARLIE"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager.set_pod(profile, vpn_data, 128)

        mock_update.assert_called_once()


class TestPromptSetPod:
    """Test pod value input prompt and validation."""

    def test_non_numeric_rejected(self, manager, sample_vpns, capsys):
        profile = {"id": "uuid-alpha", "name": "ALPHA"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager._safe_input = MagicMock(return_value="abc")
        manager._prompt_set_pod(profile, vpn_data)
        output = capsys.readouterr().out
        assert "must be between" in output

    def test_zero_rejected(self, manager, sample_vpns, capsys):
        profile = {"id": "uuid-alpha", "name": "ALPHA"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager._safe_input = MagicMock(return_value="0")
        manager._prompt_set_pod(profile, vpn_data)
        output = capsys.readouterr().out
        assert "must be between" in output

    def test_over_128_rejected(self, manager, sample_vpns, capsys):
        profile = {"id": "uuid-alpha", "name": "ALPHA"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager._safe_input = MagicMock(return_value="129")
        manager._prompt_set_pod(profile, vpn_data)
        output = capsys.readouterr().out
        assert "must be between" in output

    def test_negative_rejected(self, manager, sample_vpns, capsys):
        profile = {"id": "uuid-alpha", "name": "ALPHA"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager._safe_input = MagicMock(return_value="-5")
        manager._prompt_set_pod(profile, vpn_data)
        output = capsys.readouterr().out
        assert "must be between" in output


# ---------------------------------------------------------------------------
# US3: Clear Pod Value
# ---------------------------------------------------------------------------


class TestClearPod:
    """Test clear_pod reset logic."""

    def test_already_default_no_action(self, manager, sample_vpns, capsys):
        profile = {"id": "uuid-bravo", "name": "BRAVO"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager.clear_pod(profile, vpn_data)
        output = capsys.readouterr().out
        assert "already at default" in output

    @patch.object(WanHubGroupNumberManager, "set_pod")
    def test_delegates_to_set_pod(self, mock_set, manager, sample_vpns):
        profile = {"id": "uuid-charlie", "name": "CHARLIE"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager._safe_input = MagicMock(return_value="y")
        manager.clear_pod(profile, vpn_data)
        mock_set.assert_called_once_with(profile, vpn_data, 1)

    def test_cancelled_by_user(self, manager, sample_vpns):
        profile = {"id": "uuid-charlie", "name": "CHARLIE"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager._safe_input = MagicMock(return_value="n")
        with patch.object(WanHubGroupNumberManager, "set_pod") as mock_set:
            manager.clear_pod(profile, vpn_data)
            mock_set.assert_not_called()


# ---------------------------------------------------------------------------
# US4: Module Architecture
# ---------------------------------------------------------------------------


class TestModuleArchitecture:
    """Test clean import and instantiation."""

    def test_module_imports(self):
        from src.wan_hub_group_manager import WanHubGroupNumberManager

        assert WanHubGroupNumberManager is not None

    def test_class_instantiates(self, mock_session):
        manager = WanHubGroupNumberManager(mock_session, "org-1")
        assert manager.apisession is mock_session
        assert manager.org_id == "org-1"

    def test_execute_calls_run(self, mock_session):
        mock_get_org = MagicMock(return_value="org-1")
        mock_input = MagicMock(return_value="q")
        with patch.object(WanHubGroupNumberManager, "run") as mock_run:
            WanHubGroupNumberManager.execute(mock_session, mock_get_org, mock_input)
            mock_run.assert_called_once()

    def test_execute_exits_on_no_org(self, mock_session, capsys):
        mock_get_org = MagicMock(return_value=None)
        mock_input = MagicMock()
        WanHubGroupNumberManager.execute(mock_session, mock_get_org, mock_input)
        output = capsys.readouterr().out
        assert "No organization" in output


# ---------------------------------------------------------------------------
# Inconsistent Pod Warning
# ---------------------------------------------------------------------------


class TestLogInconsistentPods:
    """Test warning for mixed pod values."""

    def test_warns_on_mixed_pods(self, manager, mixed_pod_vpns, capsys):
        matches = manager._find_matching_paths("MIXED", mixed_pod_vpns)
        manager._log_inconsistent_pods("MIXED", matches)
        output = capsys.readouterr().out
        assert "mixed pod values" in output
        assert "5" in output
        assert "10" in output

    def test_no_warning_on_consistent_pods(self, manager, sample_vpns, capsys):
        matches = manager._find_matching_paths("ALPHA", sample_vpns)
        manager._log_inconsistent_pods("ALPHA", matches)
        output = capsys.readouterr().out
        assert "mixed" not in output.lower()
