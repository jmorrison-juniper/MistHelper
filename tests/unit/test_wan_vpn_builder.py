"""Unit tests for WanVpnBuilder (Menu 164).

Tests cover all user stories:
- US1: Create a Hub-Spoke VPN from gateway profiles
- US2: Update device profile vpn_paths after VPN creation
- US3: Review existing VPNs before creating

Task coverage: T006, T011, T022, T027, T029
"""

from unittest.mock import MagicMock, patch

import pytest

from src.wan_vpn_builder import WanVpnBuilder

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session():
    """Create a mock mistapi session."""
    return MagicMock()


@pytest.fixture
def sample_profiles():
    """Gateway device profiles with port_config."""
    return [
        {
            "id": "uuid-hub1",
            "name": "VREPOL69",
            "port_config": {
                "HE_WAN1": {"usage": "wan"},
                "HE_WAN2": {"usage": "wan"},
                "HE_5G": {"usage": "wan"},
                "LAN1": {"usage": "lan"},
            },
        },
        {
            "id": "uuid-spoke1",
            "name": "SPOKE01",
            "port_config": {
                "WAN1": {"usage": "wan"},
                "LAN1": {"usage": "lan"},
            },
        },
        {
            "id": "uuid-spoke2",
            "name": "SPOKE02",
            "port_config": {
                "WAN1": {"usage": "wan"},
                "WAN2": {"usage": "wan"},
                "LAN1": {"usage": "lan"},
            },
        },
    ]


@pytest.fixture
def sample_vpns():
    """Existing VPN objects for display tests."""
    return [
        {
            "id": "vpn-existing-1",
            "name": "OrgOverlay",
            "type": "hub_spoke",
            "paths": {"A-WAN1": {"pod": 1}, "A-WAN2": {"pod": 1}},
        },
        {
            "id": "vpn-existing-2",
            "name": "BackupVPN",
            "type": "hub_spoke",
            "paths": {"B-WAN1": {"pod": 2}},
        },
    ]


@pytest.fixture
def hub_spoke_assignments(sample_profiles):
    """Assignments: first profile=hub, second=spoke, third=skip."""
    return [
        {"profile": sample_profiles[0], "role": "hub", "pod": 69},
        {"profile": sample_profiles[1], "role": "spoke", "pod": 1},
        {"profile": sample_profiles[2], "role": "skip", "pod": 0},
    ]


@pytest.fixture
def builder(mock_session):
    """Create a builder instance with a mock safe_input."""
    mock_input = MagicMock(return_value="")
    return WanVpnBuilder(mock_session, "org-1", safe_input_func=mock_input)


# ---------------------------------------------------------------------------
# T006: Tests for _extract_wan_suffix, _classify_interfaces, _suggest_pod
# ---------------------------------------------------------------------------


class TestExtractWanSuffix:
    """Test _extract_wan_suffix static method."""

    def test_standard_prefix(self):
        assert WanVpnBuilder._extract_wan_suffix("HE_WAN1") == "WAN1"

    def test_5g_suffix(self):
        assert WanVpnBuilder._extract_wan_suffix("HE_5G") == "5G"

    def test_no_underscore(self):
        assert WanVpnBuilder._extract_wan_suffix("WAN1") == "WAN1"

    def test_multiple_underscores(self):
        assert WanVpnBuilder._extract_wan_suffix("PREFIX_HE_WAN2") == "WAN2"

    def test_empty_string(self):
        assert WanVpnBuilder._extract_wan_suffix("") == ""


class TestClassifyInterfaces:
    """Test _classify_interfaces static method."""

    def test_mixed_interfaces(self):
        port_config = {
            "HE_WAN1": {"usage": "wan"},
            "HE_WAN2": {"usage": "wan"},
            "LAN1": {"usage": "lan"},
        }
        wan, lan = WanVpnBuilder._classify_interfaces(port_config)
        assert wan == ["HE_WAN1", "HE_WAN2"]
        assert lan == ["LAN1"]

    def test_empty_port_config(self):
        wan, lan = WanVpnBuilder._classify_interfaces({})
        assert wan == []
        assert lan == []

    def test_unknown_usage_ignored(self):
        port_config = {
            "WAN1": {"usage": "wan"},
            "MGMT": {"usage": "management"},
        }
        wan, lan = WanVpnBuilder._classify_interfaces(port_config)
        assert wan == ["WAN1"]
        assert lan == []

    def test_sorted_output(self):
        port_config = {
            "WAN2": {"usage": "wan"},
            "WAN1": {"usage": "wan"},
            "LAN2": {"usage": "lan"},
            "LAN1": {"usage": "lan"},
        }
        wan, lan = WanVpnBuilder._classify_interfaces(port_config)
        assert wan == ["WAN1", "WAN2"]
        assert lan == ["LAN1", "LAN2"]


class TestSuggestPod:
    """Test _suggest_pod static method."""

    def test_trailing_digits(self):
        assert WanVpnBuilder._suggest_pod("VREPOL69") == 69

    def test_leading_zero_digits(self):
        assert WanVpnBuilder._suggest_pod("SPOKE01") == 1

    def test_no_digits(self):
        assert WanVpnBuilder._suggest_pod("HUB") == 1

    def test_custom_fallback(self):
        assert WanVpnBuilder._suggest_pod("HUB", fallback=5) == 5

    def test_out_of_range_high(self):
        assert WanVpnBuilder._suggest_pod("SITE999") == 1

    def test_out_of_range_zero(self):
        assert WanVpnBuilder._suggest_pod("DEVICE0") == 1

    def test_max_valid(self):
        assert WanVpnBuilder._suggest_pod("NODE128") == 128


# ---------------------------------------------------------------------------
# T011: Tests for path generation
# ---------------------------------------------------------------------------


class TestCollectWanSuffixes:
    """Test _collect_wan_suffixes static method."""

    def test_global_suffix_set(self, hub_spoke_assignments):
        suffixes = WanVpnBuilder._collect_wan_suffixes(hub_spoke_assignments)
        assert suffixes == {"WAN1", "WAN2", "5G"}

    def test_skip_profiles_excluded(self, sample_profiles):
        all_skip = [
            {"profile": sample_profiles[0], "role": "skip", "pod": 0},
        ]
        suffixes = WanVpnBuilder._collect_wan_suffixes(all_skip)
        assert suffixes == set()

    def test_empty_assignments(self):
        assert WanVpnBuilder._collect_wan_suffixes([]) == set()


class TestGenerateHubPaths:
    """Test _generate_hub_paths static method."""

    def test_hub_wan_direct_and_crossconnect(self):
        paths = WanVpnBuilder._generate_hub_paths("HUB1", ["HE_WAN1"], ["LAN1"], {"WAN1", "WAN2"}, 69)
        assert "HUB1-HE_WAN1" in paths
        assert "HUB1-HE_WAN1-WAN1" in paths
        assert "HUB1-HE_WAN1-WAN2" in paths
        assert "HUB1-LAN1" in paths
        assert all(value["pod"] == 69 for value in paths.values())

    def test_hub_lan_direct_only(self):
        paths = WanVpnBuilder._generate_hub_paths("HUB1", [], ["LAN1", "LAN2"], {"WAN1"}, 10)
        assert "HUB1-LAN1" in paths
        assert "HUB1-LAN2" in paths
        assert len(paths) == 2

    def test_hub_no_interfaces(self):
        paths = WanVpnBuilder._generate_hub_paths("HUB1", [], [], set(), 1)
        assert paths == {}


class TestGenerateSpokePaths:
    """Test _generate_spoke_paths static method."""

    def test_spoke_direct_only(self):
        paths = WanVpnBuilder._generate_spoke_paths("SPOKE01", ["WAN1"], ["LAN1"], 1)
        assert "SPOKE01-WAN1" in paths
        assert "SPOKE01-LAN1" in paths
        assert len(paths) == 2
        assert all(value["pod"] == 1 for value in paths.values())

    def test_spoke_no_crossconnects(self):
        paths = WanVpnBuilder._generate_spoke_paths("SPOKE01", ["WAN1", "WAN2"], [], 5)
        assert len(paths) == 2
        for key in paths:
            assert key.count("-") == 1


class TestBuildVpnBody:
    """Test _build_vpn_body method."""

    def test_full_body_structure(self, builder, hub_spoke_assignments):
        body = builder._build_vpn_body("TestVPN", hub_spoke_assignments)
        assert body["name"] == "TestVPN"
        assert body["type"] == "hub_spoke"
        assert body["path_selection"] == {"strategy": "simple"}
        assert isinstance(body["paths"], dict)
        assert len(body["paths"]) > 0

    def test_hub_has_crossconnects(self, builder, hub_spoke_assignments):
        body = builder._build_vpn_body("TestVPN", hub_spoke_assignments)
        paths = body["paths"]
        hub_cross = [k for k in paths if k.startswith("VREPOL69-") and k.count("-") == 2]
        assert len(hub_cross) > 0

    def test_spoke_no_crossconnects(self, builder, hub_spoke_assignments):
        body = builder._build_vpn_body("TestVPN", hub_spoke_assignments)
        paths = body["paths"]
        spoke_keys = [k for k in paths if k.startswith("SPOKE01-")]
        for key in spoke_keys:
            assert key.count("-") == 1

    def test_skip_profiles_excluded(self, builder, hub_spoke_assignments):
        body = builder._build_vpn_body("TestVPN", hub_spoke_assignments)
        paths = body["paths"]
        spoke2_keys = [k for k in paths if k.startswith("SPOKE02-")]
        assert spoke2_keys == []


# ---------------------------------------------------------------------------
# T022: Tests for user interaction and workflow
# ---------------------------------------------------------------------------


class TestFetchProfiles:
    """Test _fetch_profiles API call and sorting."""

    @patch("src.wan_vpn_builder.mistapi.get_all")
    @patch("src.wan_vpn_builder.mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles")
    def test_profiles_sorted_alphabetically(self, mock_list, mock_get_all, builder, sample_profiles):
        mock_get_all.return_value = list(sample_profiles)
        result = builder._fetch_profiles()
        names = [profile["name"] for profile in result]
        assert names == ["SPOKE01", "SPOKE02", "VREPOL69"]

    @patch("src.wan_vpn_builder.mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles")
    def test_api_error_returns_empty(self, mock_list, builder):
        mock_list.side_effect = Exception("API error")
        result = builder._fetch_profiles()
        assert result == []


class TestFetchExistingVpns:
    """Test _fetch_existing_vpns API call."""

    @patch("src.wan_vpn_builder.mistapi.get_all")
    @patch("src.wan_vpn_builder.mistapi.api.v1.orgs.vpns.listOrgVpns")
    def test_returns_all_vpns(self, mock_list, mock_get_all, builder, sample_vpns):
        mock_get_all.return_value = list(sample_vpns)
        result = builder._fetch_existing_vpns()
        assert len(result) == 2

    @patch("src.wan_vpn_builder.mistapi.api.v1.orgs.vpns.listOrgVpns")
    def test_api_error_returns_empty(self, mock_list, builder):
        mock_list.side_effect = Exception("API error")
        result = builder._fetch_existing_vpns()
        assert result == []


class TestCreateVpn:
    """Test _create_vpn API call."""

    @patch("src.wan_vpn_builder.mistapi.api.v1.orgs.vpns.createOrgVpn")
    def test_success_returns_dict(self, mock_create, builder):
        mock_response = MagicMock()
        mock_response.data = {"id": "new-vpn-id", "name": "TestVPN"}
        mock_create.return_value = mock_response
        result = builder._create_vpn({"name": "TestVPN"})
        assert result["id"] == "new-vpn-id"

    @patch("src.wan_vpn_builder.mistapi.api.v1.orgs.vpns.createOrgVpn")
    def test_api_error_returns_none(self, mock_create, builder):
        mock_create.side_effect = Exception("API error")
        result = builder._create_vpn({"name": "TestVPN"})
        assert result is None


class TestPromptVpnName:
    """Test _prompt_vpn_name validation."""

    def test_valid_name(self, builder):
        builder._safe_input = MagicMock(return_value="NewVPN")
        result = builder._prompt_vpn_name(["ExistingVPN"])
        assert result == "NewVPN"

    def test_cancel_with_q(self, builder):
        builder._safe_input = MagicMock(return_value="q")
        result = builder._prompt_vpn_name([])
        assert result is None

    def test_duplicate_name_reprompts(self, builder):
        builder._safe_input = MagicMock(side_effect=["ExistingVPN", "NewVPN"])
        result = builder._prompt_vpn_name(["ExistingVPN"])
        assert result == "NewVPN"

    def test_case_insensitive_duplicate(self, builder):
        builder._safe_input = MagicMock(side_effect=["existingvpn", "UniqueName"])
        result = builder._prompt_vpn_name(["ExistingVPN"])
        assert result == "UniqueName"

    def test_empty_name_reprompts(self, builder):
        builder._safe_input = MagicMock(side_effect=["", "  ", "ValidName"])
        result = builder._prompt_vpn_name([])
        assert result == "ValidName"


class TestPromptRoleAssignments:
    """Test _prompt_role_assignments validation."""

    def test_valid_assignments(self, builder, sample_profiles):
        builder._safe_input = MagicMock(side_effect=["h", "s", "k"])
        result = builder._prompt_role_assignments(sample_profiles)
        assert result is not None
        assert result[0]["role"] == "hub"
        assert result[1]["role"] == "spoke"
        assert result[2]["role"] == "skip"

    def test_all_skip_prompts_retry_then_cancel(self, builder, sample_profiles):
        builder._safe_input = MagicMock(side_effect=["k", "k", "k", "n"])
        result = builder._prompt_role_assignments(sample_profiles)
        assert result is None

    def test_invalid_then_valid(self, builder):
        profiles = [{"name": "HUB1", "port_config": {}}]
        builder._safe_input = MagicMock(side_effect=["x", "invalid", "h"])
        result = builder._prompt_role_assignments(profiles)
        assert result is not None
        assert result[0]["role"] == "hub"


class TestDisplayPreview:
    """Test _display_preview confirmation."""

    def test_create_confirmation(self, builder):
        builder._safe_input = MagicMock(return_value="CREATE")
        body = {"type": "hub_spoke", "path_selection": {"strategy": "simple"}, "paths": {"A-WAN1": {"pod": 1}}}
        result = builder._display_preview("TestVPN", body)
        assert result is True

    def test_decline_confirmation(self, builder):
        builder._safe_input = MagicMock(return_value="no")
        body = {"type": "hub_spoke", "path_selection": {"strategy": "simple"}, "paths": {"A-WAN1": {"pod": 1}}}
        result = builder._display_preview("TestVPN", body)
        assert result is False

    def test_empty_input_cancels(self, builder):
        builder._safe_input = MagicMock(return_value="")
        body = {"type": "hub_spoke", "path_selection": {"strategy": "simple"}, "paths": {}}
        result = builder._display_preview("TestVPN", body)
        assert result is False


class TestRunWorkflow:
    """Test run() main workflow orchestration."""

    @patch("src.wan_vpn_builder.mistapi.get_all")
    @patch("src.wan_vpn_builder.mistapi.api.v1.orgs.vpns.createOrgVpn")
    @patch("src.wan_vpn_builder.mistapi.api.v1.orgs.vpns.listOrgVpns")
    @patch("src.wan_vpn_builder.mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles")
    def test_no_profiles_exits(self, mock_list_profiles, mock_list_vpns, mock_create, mock_get_all, builder):
        mock_get_all.return_value = []
        builder.run()
        mock_create.assert_not_called()

    @patch("src.wan_vpn_builder.mistapi.api.v1.orgs.vpns.createOrgVpn")
    def test_api_failure_skips_profile_update(self, mock_create, builder, sample_profiles):
        mock_create.side_effect = Exception("API error")
        builder._fetch_profiles = MagicMock(return_value=sample_profiles)
        builder._fetch_existing_vpns = MagicMock(return_value=[])
        builder._safe_input = MagicMock(side_effect=["TestVPN", "h", "s", "k", "", "", "CREATE"])
        builder.run()
        builder._safe_input.assert_any_call(
            "  Type CREATE to confirm, or anything else to cancel: ",
            context="wan_vpn_create_confirm",
        )
        call_args = [c[0][0] for c in builder._safe_input.call_args_list]
        assert "  Update device profiles with vpn_paths references? (y/N): " not in call_args


class TestExecuteEntryPoint:
    """Test execute() static entry point."""

    def test_no_org_id_exits(self):
        mock_session = MagicMock()
        mock_get_org = MagicMock(return_value=None)
        mock_input = MagicMock()
        WanVpnBuilder.execute(mock_session, mock_get_org, mock_input)
        mock_get_org.assert_called_once()


# ---------------------------------------------------------------------------
# T027: Tests for vpn_paths generation and profile update
# ---------------------------------------------------------------------------


class TestBuildPortVpnPaths:
    """Test _build_port_vpn_paths key format and structure."""

    def test_hub_wan_with_crossconnects(self, builder):
        result = builder._build_port_vpn_paths("VREPOL69", "HE_WAN1", "OrgOverlay", "hub", {"WAN1", "WAN2"})
        assert "VREPOL69-HE_WAN1.OrgOverlay" in result
        assert "VREPOL69-HE_WAN1-WAN1.OrgOverlay" in result
        assert "VREPOL69-HE_WAN1-WAN2.OrgOverlay" in result
        assert result["VREPOL69-HE_WAN1.OrgOverlay"]["role"] == "hub"
        assert result["VREPOL69-HE_WAN1.OrgOverlay"]["key"] == 0

    def test_spoke_direct_only(self, builder):
        result = builder._build_port_vpn_paths("SPOKE01", "WAN1", "OrgOverlay", "spoke", {"WAN1"})
        assert "SPOKE01-WAN1.OrgOverlay" in result
        assert result["SPOKE01-WAN1.OrgOverlay"]["role"] == "spoke"
        cross_keys = [k for k in result if k.count("-") > 1]
        assert cross_keys == []

    def test_key_indexing_sequential(self, builder):
        result = builder._build_port_vpn_paths("HUB1", "HE_WAN1", "VPN1", "hub", {"5G", "WAN1", "WAN2"})
        # Direct key gets key=0, cross-connects get sequential indices
        direct_ref = "HUB1-HE_WAN1.VPN1"
        assert result[direct_ref]["key"] == 0
        cross_entries = {k: v for k, v in result.items() if k != direct_ref}
        keys_used = sorted(v["key"] for v in cross_entries.values())
        assert keys_used == [0, 1, 2]


class TestUpdateSingleProfile:
    """Test _update_single_profile API interaction."""

    @patch("src.wan_vpn_builder.mistapi.api.v1.orgs.deviceprofiles.updateOrgDeviceProfile")
    @patch("src.wan_vpn_builder.mistapi.api.v1.orgs.deviceprofiles.getOrgDeviceProfile")
    def test_success(self, mock_get, mock_update, builder):
        mock_response = MagicMock()
        mock_response.data = {
            "id": "uuid-1",
            "name": "VREPOL69",
            "port_config": {
                "HE_WAN1": {"usage": "wan", "vpn_paths": {}},
                "LAN1": {"usage": "lan", "vpn_paths": {}},
            },
        }
        mock_get.return_value = mock_response
        assignment = {"role": "hub", "pod": 69}
        result = builder._update_single_profile("uuid-1", "VREPOL69", "OrgOverlay", assignment, {"WAN1"})
        assert result is True
        mock_update.assert_called_once()

    @patch("src.wan_vpn_builder.mistapi.api.v1.orgs.deviceprofiles.getOrgDeviceProfile")
    def test_api_failure(self, mock_get, builder):
        mock_get.side_effect = Exception("API error")
        assignment = {"role": "hub", "pod": 69}
        result = builder._update_single_profile("uuid-1", "HUB1", "VPN1", assignment, {"WAN1"})
        assert result is False


class TestPromptProfileUpdates:
    """Test _prompt_profile_updates flow."""

    def test_decline_skips_updates(self, builder, hub_spoke_assignments):
        builder._safe_input = MagicMock(return_value="n")
        builder._update_single_profile = MagicMock()
        builder._prompt_profile_updates("vpn-id", "TestVPN", hub_spoke_assignments)
        builder._update_single_profile.assert_not_called()

    def test_accept_calls_update(self, builder, hub_spoke_assignments):
        builder._safe_input = MagicMock(return_value="y")
        builder._update_single_profile = MagicMock(return_value=True)
        builder._prompt_profile_updates("vpn-id", "TestVPN", hub_spoke_assignments)
        assert builder._update_single_profile.call_count == 2

    def test_partial_failure_continues(self, builder, hub_spoke_assignments):
        builder._safe_input = MagicMock(return_value="y")
        builder._update_single_profile = MagicMock(side_effect=[False, True])
        builder._prompt_profile_updates("vpn-id", "TestVPN", hub_spoke_assignments)
        assert builder._update_single_profile.call_count == 2


# ---------------------------------------------------------------------------
# T029: Tests for enhanced VPN display
# ---------------------------------------------------------------------------


class TestDisplayExistingVpns:
    """Test _display_existing_vpns output."""

    def test_with_vpns(self, builder, sample_vpns, capsys):
        builder._display_existing_vpns(sample_vpns)
        output = capsys.readouterr().out
        assert "OrgOverlay" in output
        assert "BackupVPN" in output
        assert "hub_spoke" in output

    def test_no_vpns(self, builder, capsys):
        builder._display_existing_vpns([])
        output = capsys.readouterr().out
        assert "No existing VPN definitions" in output

    def test_shows_path_count(self, builder, sample_vpns, capsys):
        builder._display_existing_vpns(sample_vpns)
        output = capsys.readouterr().out
        assert "2" in output
        assert "1" in output


class TestDisplayProfileList:
    """Test _display_profile_list output."""

    def test_shows_wan_lan_counts(self, builder, sample_profiles, capsys):
        builder._display_profile_list(sample_profiles)
        output = capsys.readouterr().out
        assert "VREPOL69" in output
        assert "SPOKE01" in output

    def test_warns_no_wan(self, builder, capsys):
        profiles = [{"name": "LAN_ONLY", "port_config": {"LAN1": {"usage": "lan"}}}]
        builder._display_profile_list(profiles)
        output = capsys.readouterr().out
        assert "No WAN interfaces" in output
