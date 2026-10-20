"""Unit tests for WanHubGroupNumberManager (Menu 163).

Tests cover all user stories:
- US1: Profile listing and selection
- US2: Set pod value
- US3: Clear pod value
- US4: Module import and instantiation
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from src.operations.wan.wan_hub_group_manager import WanHubGroupNumberManager

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


@pytest.fixture
def mocked_vpn_update_flow(manager, sample_vpns):
    """Prepare an isolated VPN update flow with mocked SDK calls."""
    with (
        patch("src.operations.wan.wan_hub_group_manager.mistapi.api.v1.orgs.vpns.updateOrgVpn") as mock_update,
        patch("src.operations.wan.wan_hub_group_manager.mistapi.api.v1.orgs.vpns.getOrgVpn") as mock_get,
    ):  # WHY: prevent all Mist network requests during update tests.
        response = MagicMock()  # WHY: provide an SDK-shaped read response.
        response.data = sample_vpns[0]  # WHY: supply current VPN paths for the update flow.
        mock_get.return_value = response  # WHY: isolate the read from Mist.
        yield manager, sample_vpns, mock_update  # WHY: expose the manager and controlled response.


# ---------------------------------------------------------------------------
# US1: Profile Listing and Selection
# ---------------------------------------------------------------------------


class TestFetchProfiles:
    """Test _fetch_profiles API call and sorting."""

    @patch("src.operations.wan.wan_hub_group_manager.mistapi.get_all")
    @patch("src.operations.wan.wan_hub_group_manager.mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles")
    def test_profiles_sorted_alphabetically(self, mock_list, mock_get_all, manager, sample_profiles):
        mock_get_all.return_value = list(sample_profiles)
        result = manager._fetch_profiles()
        names = [profile["name"] for profile in result]
        assert names == ["ALPHA", "BRAVO", "CHARLIE"]

    @patch("src.operations.wan.wan_hub_group_manager.mistapi.get_all")
    @patch("src.operations.wan.wan_hub_group_manager.mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles")
    def test_empty_profiles(self, mock_list, mock_get_all, manager):
        mock_get_all.return_value = []
        result = manager._fetch_profiles()
        assert result == []

    @patch("src.operations.wan.wan_hub_group_manager.mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles")
    def test_api_error_returns_empty(self, mock_list, manager):
        mock_list.side_effect = Exception("API error")
        result = manager._fetch_profiles()
        assert result == []


class TestFetchHubSpokeVpns:
    """Test _fetch_hub_spoke_vpns API call and filtering."""

    @patch("src.operations.wan.wan_hub_group_manager.mistapi.get_all")
    @patch("src.operations.wan.wan_hub_group_manager.mistapi.api.v1.orgs.vpns.listOrgVpns")
    def test_filters_to_hub_spoke(self, mock_list, mock_get_all, manager):
        mock_get_all.return_value = [
            {"id": "1", "name": "HubSpoke", "type": "hub_spoke", "paths": {}},
            {"id": "2", "name": "Mesh", "type": "mesh", "paths": {}},
        ]
        hub_spoke, all_vpns = manager._fetch_hub_spoke_vpns()
        assert len(hub_spoke) == 1
        assert hub_spoke[0]["name"] == "HubSpoke"
        assert len(all_vpns) == 2

    @patch("src.operations.wan.wan_hub_group_manager.mistapi.get_all")
    @patch("src.operations.wan.wan_hub_group_manager.mistapi.api.v1.orgs.vpns.listOrgVpns")
    def test_no_hub_spoke_vpns(self, mock_list, mock_get_all, manager):
        mock_get_all.return_value = [
            {"id": "1", "name": "Mesh", "type": "mesh", "paths": {}},
        ]
        hub_spoke, all_vpns = manager._fetch_hub_spoke_vpns()
        assert hub_spoke == []
        assert len(all_vpns) == 1


class TestReportNoHubSpoke:
    """Test _report_no_hub_spoke output messages."""

    def test_empty_vpns_reports_none(self, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.WARNING)
        WanHubGroupNumberManager._report_no_hub_spoke([])
        assert "No VPN definitions found" in caplog.text

    def test_reports_found_types(self, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.WARNING)
        all_vpns = [
            {"name": "V1", "type": "mesh"},
            {"name": "V2", "type": "mesh"},
            {"name": "V3", "type": None},
        ]
        WanHubGroupNumberManager._report_no_hub_spoke(all_vpns)
        assert "No hub-spoke" in caplog.text
        assert "3 VPN(s)" in caplog.text
        assert "mesh" in caplog.text


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

    @pytest.mark.parametrize("status_code", [200, 204])
    def test_batch_update_all_paths(self, mocked_vpn_update_flow, caplog: pytest.LogCaptureFixture, status_code):
        """Keep successful status results visible as path updates."""
        manager, sample_vpns, mock_update = mocked_vpn_update_flow  # WHY: use isolated SDK calls and sample data.
        mock_update.return_value.status_code = status_code  # WHY: model an accepted SDK update response.
        caplog.set_level(logging.INFO)  # WHY: capture the operator-facing success messages.

        profile = {"id": "uuid-alpha", "name": "ALPHA"}  # WHY: target the matching profile.
        vpn_data = manager._build_vpn_data([profile], sample_vpns)  # WHY: select its VPN paths.
        manager.set_pod(profile, vpn_data, 99)  # WHY: run the public update flow with a mocked response.

        mock_update.assert_called_once()  # WHY: each VPN receives one update request.
        call_args = mock_update.call_args  # WHY: inspect the body sent to the mocked SDK.
        body = (
            call_args.kwargs.get("body") or call_args[1].get("body") or call_args[0][3]
        )  # WHY: accept the body across call forms.
        paths = body.get("paths", {})  # WHY: read the modified VPN paths.
        for key in ["ALPHA-HE_WAN1", "ALPHA-HE_WAN2", "ALPHA-HE_LAN1"]:
            assert paths[key]["pod"] == 99  # WHY: confirm each matching path received the new pod.
        assert "Updated 3 paths in VPN 'OrgOverlay' to pod 99" in caplog.text  # WHY: preserve per-VPN success output.
        assert "Updated 3 paths for 'ALPHA' to pod 99" in caplog.text  # WHY: preserve the final success summary.

    @pytest.mark.parametrize("status_code", [403, 503, None])
    def test_rejected_update_does_not_report_success(
        self, mocked_vpn_update_flow, caplog: pytest.LogCaptureFixture, status_code
    ):
        """Stop update reporting when Mist refuses or does not confirm a write."""
        manager, _, mock_update = mocked_vpn_update_flow  # WHY: use isolated SDK calls.
        mock_update.return_value.status_code = status_code  # WHY: model a refusal or missing status.
        vpn_updates = {  # WHY: verify a refusal stops the remaining VPN updates.
            "vpn-1": {"name": "OrgOverlay", "paths": ["ALPHA-HE_WAN1", "ALPHA-HE_WAN2", "ALPHA-HE_LAN1"]},
            "vpn-2": {"name": "OrgOverlay-2", "paths": ["ALPHA-HE_WAN1"]},
        }

        with caplog.at_level(logging.INFO):  # WHY: capture both error and success-level messages.
            manager._apply_vpn_updates(vpn_updates, "ALPHA", 99)  # WHY: exercise the complete update-reporting flow.

        mock_update.assert_called_once()  # WHY: prove the refusal came from the update response.
        assert "HTTP status" in caplog.text  # WHY: expose the returned status in the failure log.
        assert str(status_code) in caplog.text  # WHY: identify the exact refused or missing status.
        assert "Error updating VPN 'OrgOverlay'" in caplog.text  # WHY: show the operator a failure message.
        assert "Updated 3 paths in VPN" not in caplog.text  # WHY: prevent a false per-VPN success report.
        assert "Updated 3 paths for 'ALPHA'" not in caplog.text  # WHY: prevent a false final success summary.

    def test_update_exception_keeps_existing_failure_handling(
        self, mocked_vpn_update_flow, caplog: pytest.LogCaptureFixture
    ):
        """Keep SDK exceptions on the existing visible failure path."""
        manager, _, mock_update = mocked_vpn_update_flow  # WHY: use isolated SDK calls.
        mock_update.side_effect = RuntimeError("connection failed")  # WHY: preserve exception-path behavior.
        vpn_updates = {  # WHY: select paths so a false success count can be detected.
            "vpn-1": {"name": "OrgOverlay", "paths": ["ALPHA-HE_WAN1", "ALPHA-HE_WAN2", "ALPHA-HE_LAN1"]}
        }

        with caplog.at_level(logging.INFO):  # WHY: capture both error and success-level messages.
            manager._apply_vpn_updates(vpn_updates, "ALPHA", 99)  # WHY: exercise existing exception handling.

        assert "Failed to update VPN 'OrgOverlay'" in caplog.text  # WHY: preserve visible exception reporting.
        assert "connection failed" in caplog.text  # WHY: preserve the exception details for diagnosis.
        assert "Updated 3 paths" not in caplog.text  # WHY: prevent a false success report.

    def test_no_matching_paths(self, manager, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.WARNING)  # WHY: capture the no-op reason for the operator.
        profile = {"id": "uuid-x", "name": "NONEXISTENT"}  # WHY: select a profile without VPN paths.
        vpn_data = {"NONEXISTENT": []}  # WHY: model an empty path match.
        manager.set_pod(profile, vpn_data, 42)  # WHY: exercise the no-match guard.
        assert "No VPN paths found for profile 'NONEXISTENT'" in caplog.text  # WHY: require visible no-op feedback.

    @patch("src.operations.wan.wan_hub_group_manager.mistapi.api.v1.orgs.vpns.updateOrgVpn")
    @patch("src.operations.wan.wan_hub_group_manager.mistapi.api.v1.orgs.vpns.getOrgVpn")
    def test_pod_value_range_validation(self, mock_get, mock_update, manager, sample_vpns):
        """set_pod itself does not validate range (caller does), but verify it sets correctly."""
        mock_response = MagicMock()  # WHY: provide a fake SDK response without a Mist request.
        mock_response.data = sample_vpns[0]  # WHY: supply the VPN data needed for the update.
        mock_get.return_value = mock_response  # WHY: keep the read step isolated from Mist.
        mock_update.return_value.status_code = 200  # WHY: model an accepted SDK update response.

        profile = {"id": "uuid-charlie", "name": "CHARLIE"}  # WHY: target the matching profile.
        vpn_data = manager._build_vpn_data([profile], sample_vpns)  # WHY: select its VPN paths.
        manager.set_pod(profile, vpn_data, 128)  # WHY: verify the existing accepted-update path.

        assert mock_update.call_count == 1  # WHY: require one API update for the selected VPN.
        updated_body = mock_update.call_args.kwargs["body"]  # WHY: inspect the submitted VPN state.
        assert updated_body["paths"]["CHARLIE-HE_WAN1"]["pod"] == 128  # WHY: verify the requested pod value.
        assert updated_body["paths"]["CHARLIE-HE_WAN2"]["pod"] == 128  # WHY: verify every matching path changed.


class TestPromptSetPod:
    """Test pod value input prompt and validation."""

    def test_non_numeric_rejected(self, manager, sample_vpns, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.WARNING)
        profile = {"id": "uuid-alpha", "name": "ALPHA"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager._safe_input = MagicMock(return_value="abc")
        manager._prompt_set_pod(profile, vpn_data)
        assert "must be between" in caplog.text

    def test_zero_rejected(self, manager, sample_vpns, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.WARNING)
        profile = {"id": "uuid-alpha", "name": "ALPHA"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager._safe_input = MagicMock(return_value="0")
        manager._prompt_set_pod(profile, vpn_data)
        assert "must be between" in caplog.text

    def test_over_128_rejected(self, manager, sample_vpns, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.WARNING)
        profile = {"id": "uuid-alpha", "name": "ALPHA"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager._safe_input = MagicMock(return_value="129")
        manager._prompt_set_pod(profile, vpn_data)
        assert "must be between" in caplog.text

    def test_negative_rejected(self, manager, sample_vpns, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.WARNING)
        profile = {"id": "uuid-alpha", "name": "ALPHA"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager._safe_input = MagicMock(return_value="-5")
        manager._prompt_set_pod(profile, vpn_data)
        assert "must be between" in caplog.text


# ---------------------------------------------------------------------------
# US3: Clear Pod Value
# ---------------------------------------------------------------------------


class TestClearPod:
    """Test clear_pod reset logic."""

    def test_already_default_no_action(self, manager, sample_vpns, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.WARNING)
        profile = {"id": "uuid-bravo", "name": "BRAVO"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager.clear_pod(profile, vpn_data)
        assert "already at default" in caplog.text

    @patch.object(WanHubGroupNumberManager, "set_pod")
    def test_delegates_to_set_pod(self, mock_set, manager, sample_vpns):
        profile = {"id": "uuid-charlie", "name": "CHARLIE"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager._safe_input = MagicMock(return_value="y")
        manager.clear_pod(profile, vpn_data)
        mock_set.assert_called_once_with(profile, vpn_data, 1)

    def test_cancelled_by_user(self, manager, sample_vpns):
        profile = {"id": "uuid-charlie", "name": "CHARLIE"}  # WHY: select paths that need a reset.
        vpn_data = manager._build_vpn_data([profile], sample_vpns)  # WHY: prepare the profile path matches.
        manager._safe_input = MagicMock(return_value="n")  # WHY: model an operator cancellation.
        with patch.object(WanHubGroupNumberManager, "set_pod") as mock_set:  # WHY: detect any unintended update.
            manager.clear_pod(profile, vpn_data)  # WHY: exercise the reset confirmation.
            assert mock_set.call_count == 0  # WHY: confirm cancellation sends no update.


# ---------------------------------------------------------------------------
# US4: Module Architecture
# ---------------------------------------------------------------------------


class TestModuleArchitecture:
    """Test clean import and instantiation."""

    def test_module_imports(self):
        assert (
            WanHubGroupNumberManager.__module__ == "src.operations.wan.wan_hub_group_manager"
        )  # WHY: verify the public class resolves from its expected module.

    def test_class_instantiates(self, mock_session):
        manager = WanHubGroupNumberManager(mock_session, "org-1")
        assert manager.apisession is mock_session
        assert manager.org_id == "org-1"

    def test_execute_calls_run(self, mock_session):
        mock_get_org = MagicMock(return_value="org-1")  # WHY: provide an organization without a cloud call.
        mock_input = MagicMock(return_value="q")  # WHY: prevent an interactive prompt.
        with patch.object(WanHubGroupNumberManager, "run") as mock_run:  # WHY: observe the orchestration call.
            WanHubGroupNumberManager.execute(mock_session, mock_get_org, mock_input)  # WHY: run the public entry point.
            assert mock_run.call_count == 1  # WHY: require one workflow start.

    def test_execute_exits_on_no_org(self, mock_session, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.WARNING)
        mock_get_org = MagicMock(return_value=None)
        mock_input = MagicMock()
        WanHubGroupNumberManager.execute(mock_session, mock_get_org, mock_input)
        assert "No organization" in caplog.text


# ---------------------------------------------------------------------------
# Inconsistent Pod Warning
# ---------------------------------------------------------------------------


class TestLogInconsistentPods:
    """Test warning for mixed pod values."""

    def test_warns_on_mixed_pods(self, manager, mixed_pod_vpns, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.WARNING)
        matches = manager._find_matching_paths("MIXED", mixed_pod_vpns)
        manager._log_inconsistent_pods("MIXED", matches)
        assert "mixed pod values" in caplog.text
        assert "5" in caplog.text
        assert "10" in caplog.text

    def test_no_warning_on_consistent_pods(self, manager, sample_vpns, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.WARNING)
        matches = manager._find_matching_paths("ALPHA", sample_vpns)
        manager._log_inconsistent_pods("ALPHA", matches)
        assert "mixed" not in caplog.text.lower()


# ---------------------------------------------------------------------------
# Coverage: run() workflow
# ---------------------------------------------------------------------------


class TestRunWorkflow:
    """Test the main run() orchestration method."""

    @patch.object(WanHubGroupNumberManager, "_fetch_profiles")
    def test_no_profiles_exits(self, mock_fetch, manager, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.WARNING)
        mock_fetch.return_value = []
        manager.run()
        assert "No WAN Hub Profiles" in caplog.text

    @patch.object(WanHubGroupNumberManager, "_prompt_action")
    @patch.object(WanHubGroupNumberManager, "_prompt_profile_selection")
    @patch.object(WanHubGroupNumberManager, "_display_profile_list")
    @patch.object(WanHubGroupNumberManager, "_fetch_hub_spoke_vpns")
    @patch.object(WanHubGroupNumberManager, "_fetch_profiles")
    def test_no_hub_spoke_vpns_exits(
        self,
        mock_profiles,
        mock_vpns,
        mock_display,
        mock_select,
        mock_action,
        manager,
        caplog: pytest.LogCaptureFixture,
    ):
        caplog.set_level(logging.WARNING)  # WHY: capture the empty hub-spoke explanation.
        mock_profiles.return_value = [{"name": "P1"}]  # WHY: continue beyond the profile guard.
        mock_vpns.return_value = ([], [{"type": "mesh"}])  # WHY: model only non-hub-spoke VPN data.
        manager.run()  # WHY: exercise the VPN type filter.
        assert mock_display.call_count == 0  # WHY: prevent selection when no hub-spoke VPN exists.
        assert "No hub-spoke VPN definitions found" in caplog.text  # WHY: require a visible operator reason.

    @patch.object(WanHubGroupNumberManager, "_prompt_action")
    @patch.object(WanHubGroupNumberManager, "_prompt_profile_selection")
    @patch.object(WanHubGroupNumberManager, "_display_profile_list")
    @patch.object(WanHubGroupNumberManager, "_fetch_hub_spoke_vpns")
    @patch.object(WanHubGroupNumberManager, "_fetch_profiles")
    def test_user_cancels_selection(self, mock_profiles, mock_vpns, mock_display, mock_select, mock_action, manager):
        mock_profiles.return_value = [{"name": "P1"}]
        mock_vpns.return_value = ([{"type": "hub_spoke", "paths": {}}], [])
        mock_select.return_value = None
        manager.run()
        assert mock_action.call_count == 0  # A cancelled selection must not reach the action prompt.
        mock_action.assert_not_called()

    @patch.object(WanHubGroupNumberManager, "_prompt_action")
    @patch.object(WanHubGroupNumberManager, "_prompt_profile_selection")
    @patch.object(WanHubGroupNumberManager, "_display_profile_list")
    @patch.object(WanHubGroupNumberManager, "_fetch_hub_spoke_vpns")
    @patch.object(WanHubGroupNumberManager, "_fetch_profiles")
    def test_full_workflow_calls_action(
        self, mock_profiles, mock_vpns, mock_display, mock_select, mock_action, manager
    ):
        profile = {"name": "HUB1"}  # WHY: select the available hub profile.
        mock_profiles.return_value = [profile]  # WHY: provide one profile without a cloud call.
        vpn = {"type": "hub_spoke", "paths": {"HUB1-WAN1": {"pod": 1}}}  # WHY: provide one matching VPN path.
        mock_vpns.return_value = ([vpn], [vpn])  # WHY: satisfy the filtered and total VPN results.
        mock_select.return_value = profile  # WHY: model a valid operator selection.
        manager.run()  # WHY: exercise the complete orchestration path.
        assert mock_action.call_count == 1  # WHY: require one action prompt for the selected profile.


# ---------------------------------------------------------------------------
# Coverage: _fetch_hub_spoke_vpns exception
# ---------------------------------------------------------------------------


class TestFetchHubSpokeVpnsError:
    """Test _fetch_hub_spoke_vpns error handling."""

    @patch("src.operations.wan.wan_hub_group_manager.mistapi.api.v1.orgs.vpns.listOrgVpns")
    def test_api_error_returns_empty(self, mock_list, manager, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.ERROR)
        mock_list.side_effect = Exception("Connection failed")
        hub_spoke, all_vpns = manager._fetch_hub_spoke_vpns()
        assert hub_spoke == []
        assert all_vpns == []
        assert "Error retrieving VPN" in caplog.text


# ---------------------------------------------------------------------------
# Coverage: _display_profile_list
# ---------------------------------------------------------------------------


class TestDisplayProfileList:
    """Test profile list display rendering."""

    def test_renders_profile_names(self, manager, sample_vpns, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.WARNING)
        profiles = [
            {"name": "ALPHA"},
            {"name": "BRAVO"},
        ]
        vpn_data = manager._build_vpn_data(profiles, sample_vpns)
        manager._display_profile_list(profiles, vpn_data)
        assert "1." in caplog.text
        assert "ALPHA" in caplog.text
        assert "2." in caplog.text
        assert "BRAVO" in caplog.text


# ---------------------------------------------------------------------------
# Coverage: _prompt_action
# ---------------------------------------------------------------------------


class TestPromptAction:
    """Test the set/clear/cancel action menu."""

    def test_no_matches_exits(self, manager, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.WARNING)
        profile = {"name": "EMPTY"}
        vpn_data = {"EMPTY": []}
        manager._prompt_action(profile, vpn_data)
        assert "No VPN paths found" in caplog.text

    @patch.object(WanHubGroupNumberManager, "_prompt_set_pod")
    def test_action_1_calls_set_pod(self, mock_set, manager, sample_vpns):
        profile = {"name": "ALPHA"}  # WHY: select a profile with matching VPN paths.
        vpn_data = manager._build_vpn_data([profile], sample_vpns)  # WHY: prepare the action path matches.
        manager._safe_input = MagicMock(return_value="1")  # WHY: select the set action without a prompt.
        manager._prompt_action(profile, vpn_data)  # WHY: dispatch the selected action.
        assert mock_set.call_count == 1  # WHY: require one set operation.

    @patch.object(WanHubGroupNumberManager, "clear_pod")
    def test_action_2_calls_clear(self, mock_clear, manager, sample_vpns):
        profile = {"name": "ALPHA"}  # WHY: select a profile with matching VPN paths.
        vpn_data = manager._build_vpn_data([profile], sample_vpns)  # WHY: prepare the action path matches.
        manager._safe_input = MagicMock(return_value="2")  # WHY: select the clear action without a prompt.
        manager._prompt_action(profile, vpn_data)  # WHY: dispatch the selected action.
        assert mock_clear.call_count == 1  # WHY: require one clear operation.

    def test_action_3_cancels(self, manager, sample_vpns, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.WARNING)
        profile = {"name": "ALPHA"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager._safe_input = MagicMock(return_value="3")
        manager._prompt_action(profile, vpn_data)
        assert "Cancelled" in caplog.text


# ---------------------------------------------------------------------------
# Coverage: _prompt_set_pod happy path + confirmation cancel
# ---------------------------------------------------------------------------


class TestPromptSetPodConfirmation:
    """Test _prompt_set_pod confirmation and cancellation paths."""

    @patch.object(WanHubGroupNumberManager, "set_pod")
    def test_confirmed_calls_set_pod(self, mock_set, manager, sample_vpns):
        profile = {"name": "ALPHA"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager._safe_input = MagicMock(side_effect=["42", "y"])
        manager._prompt_set_pod(profile, vpn_data)
        mock_set.assert_called_once_with(profile, vpn_data, 42)

    def test_declined_cancels(self, manager, sample_vpns, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.WARNING)
        profile = {"name": "ALPHA"}
        vpn_data = manager._build_vpn_data([profile], sample_vpns)
        manager._safe_input = MagicMock(side_effect=["42", "n"])
        manager._prompt_set_pod(profile, vpn_data)
        assert "Cancelled" in caplog.text


# ---------------------------------------------------------------------------
# Coverage: _apply_vpn_updates exception handler
# ---------------------------------------------------------------------------


class TestApplyVpnUpdatesError:
    """Test _apply_vpn_updates error handling."""

    def test_success_summary_uses_info_level(self, manager, caplog: pytest.LogCaptureFixture):
        """Successful pod updates log the summary at INFO, not WARNING."""
        vpn_updates = {"vpn-1": {"name": "OrgOverlay", "paths": ["ALPHA-WAN1"]}}  # WHY: one update is enough.
        manager._apply_one_vpn = MagicMock(return_value=1)  # type: ignore[method-assign] # WHY: avoid API calls.
        with caplog.at_level(logging.INFO):  # WHY: capture the repaired success summary.
            manager._apply_vpn_updates(vpn_updates, "ALPHA", 99)  # WHY: exercise the summary log site.
        summary_records = [
            record for record in caplog.records if "Updated 1 paths for 'ALPHA' to pod 99" in record.getMessage()
        ]  # WHY: isolate the repaired success summary.
        assert [record.levelno for record in summary_records] == [logging.INFO]  # WHY: success is not a warning.

    @patch("src.operations.wan.wan_hub_group_manager.mistapi.api.v1.orgs.vpns.getOrgVpn")
    def test_api_error_prints_message(self, mock_get, manager, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.ERROR)
        mock_get.side_effect = Exception("Network error")
        vpn_updates = {"vpn-1": {"name": "OrgOverlay", "paths": ["ALPHA-WAN1"]}}
        manager._apply_vpn_updates(vpn_updates, "ALPHA", 99)
        assert "Error updating VPN" in caplog.text


# ---------------------------------------------------------------------------
# Coverage: _fallback_input
# ---------------------------------------------------------------------------


class TestFallbackInput:
    """Test the fallback input handler."""

    @patch("builtins.input", return_value="  hello  ")
    def test_strips_whitespace(self, mock_input):
        result = WanHubGroupNumberManager._fallback_input("prompt: ")
        assert result == "hello"

    @patch("builtins.input", side_effect=EOFError)
    def test_eof_returns_empty(self, mock_input):
        result = WanHubGroupNumberManager._fallback_input("prompt: ")
        assert result == ""

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_keyboard_interrupt_returns_empty(self, mock_input):
        result = WanHubGroupNumberManager._fallback_input("prompt: ")
        assert result == ""


def _refused_response():
    """Build a fake mistapi response for an HTTP 403 refusal."""
    response = MagicMock()
    response.status_code = 403
    response.data = {"detail": "You do not have permission to perform this action."}
    response.next = None
    return response


class TestFetchRefusedByApi:
    """HTTP 403 refusals must yield empty results, never error bodies as records."""

    @patch("src.operations.wan.wan_hub_group_manager.mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles")
    def test_profiles_http_403_returns_no_profiles(self, mock_list):
        mock_list.return_value = _refused_response()
        refused_manager = WanHubGroupNumberManager(MagicMock(), "org-1", safe_input_func=MagicMock())
        result = refused_manager._fetch_profiles()
        assert result == []
        assert mock_list.call_count == 1

    @patch("src.operations.wan.wan_hub_group_manager.mistapi.api.v1.orgs.vpns.listOrgVpns")
    def test_vpns_http_403_returns_no_vpns(self, mock_list):
        mock_list.return_value = _refused_response()
        refused_manager = WanHubGroupNumberManager(MagicMock(), "org-1", safe_input_func=MagicMock())
        hub_spoke, all_vpns = refused_manager._fetch_hub_spoke_vpns()
        assert hub_spoke == []
        assert all_vpns == []
        assert mock_list.call_count == 1
