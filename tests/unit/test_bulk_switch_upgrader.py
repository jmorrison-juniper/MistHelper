"""Tests for BulkSwitchFirmwareUpgrader extraction.

Validates the extracted module at src/firmware/bulk_switch_upgrader.py
with comprehensive coverage of all upgrade workflow steps.
"""

from __future__ import annotations

import builtins
import os
import sys
import tempfile
import time
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

# ---------------------------------------------------------------------------
# Mock mistapi before importing the module under test
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Stub mistapi for the import, then restore sys.modules at once.
# WHY: pytest imports every test module during collection but runs teardown_module only
# for a module that has a selected test. A stub left in sys.modules therefore leaks for
# the whole session and breaks mistapi's lazy subpackage import. See issue #1739.
# ---------------------------------------------------------------------------
_saved_mistapi = sys.modules.get("mistapi")
_our_mock = MagicMock()
sys.modules["mistapi"] = _our_mock
try:
    from src.firmware.bulk_switch_upgrader import BulkSwitchFirmwareUpgrader
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
        return  # Another module replaced our stub; leave it alone
    if _saved_mistapi is not None:
        sys.modules["mistapi"] = _saved_mistapi
    else:
        sys.modules.pop("mistapi", None)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_apisession() -> MagicMock:
    """Create a mock API session."""
    return MagicMock()


@pytest.fixture()
def mock_safe_input() -> MagicMock:
    """Create a mock safe_input seam that honors builtins.input patches.

    Production routes every prompt through the injected safe_input_fn, so
    interactive-loop tests that drive `@patch("builtins.input", ...)` keep
    working: the seam forwards to that patched callable. When input is left
    unpatched the seam returns the confirm phrase (the prior default) so
    confirmation flows never block on real stdin.
    """

    def _forward(prompt: str = "", *_args: Any, **_kwargs: Any) -> str:
        active = builtins.input  # Current builtin; a test @patch installs a Mock here.
        if isinstance(active, Mock):  # Patched -> drive the loop from the test's sequence/value.
            return str(active(prompt))  # Honor return_value / side_effect provided by the test.
        return "UPGRADE SWITCHES"  # Unpatched -> safe constant default; never touches real stdin.

    return MagicMock(side_effect=_forward)  # Records calls while forwarding input.


@pytest.fixture()
def upgrader(
    mock_apisession: MagicMock,
    mock_safe_input: MagicMock,
) -> BulkSwitchFirmwareUpgrader:
    """Create a BulkSwitchFirmwareUpgrader instance."""
    return BulkSwitchFirmwareUpgrader(
        org_id="test-org-id",
        apisession=mock_apisession,
        safe_input_fn=mock_safe_input,
    )


@pytest.fixture()
def upgrader_with_override(
    mock_apisession: MagicMock,
    mock_safe_input: MagicMock,
) -> BulkSwitchFirmwareUpgrader:
    """Create upgrader with sites override."""
    sites = [
        {"id": "site-1", "name": "Site One"},
        {"id": "site-2", "name": "Site Two"},
    ]
    return BulkSwitchFirmwareUpgrader(
        org_id="test-org-id",
        apisession=mock_apisession,
        safe_input_fn=mock_safe_input,
        sites_override=sites,
    )


# ---------------------------------------------------------------------------
# Initialization Tests
# ---------------------------------------------------------------------------


class TestInit:
    """Test BulkSwitchFirmwareUpgrader initialization."""

    def test_basic_init(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify default initialization values."""
        assert upgrader.org_id == "test-org-id"
        assert upgrader.sites_override is None
        assert upgrader.org_name == ""
        assert upgrader.selected_sites == []
        assert upgrader.switch_models == set()
        assert upgrader.current_firmware_versions == set()
        assert upgrader.available_versions == []
        assert upgrader.compatible_versions == {}
        assert upgrader.target_version == ""
        assert upgrader.upgrade_strategy == ""
        assert upgrader.force_upgrade is False
        assert upgrader.auto_reboot is True
        assert upgrader.take_snapshot is True
        assert upgrader.upgrade_results == {}

    def test_init_with_override(
        self,
        upgrader_with_override: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify initialization with sites override."""
        assert upgrader_with_override.sites_override is not None
        assert len(upgrader_with_override.sites_override) == 2

    def test_cache_constants(self) -> None:
        """Verify cache file path and freshness constants."""
        assert BulkSwitchFirmwareUpgrader.CACHE_FILE == os.path.join("data", "cached_org_devices_versions_switch.csv")
        assert BulkSwitchFirmwareUpgrader.CACHE_FRESHNESS_HOURS == 24


# ---------------------------------------------------------------------------
# Organization Validation Tests
# ---------------------------------------------------------------------------


class TestValidateOrganization:
    """Test organization validation step."""

    def test_successful_validation(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify successful org validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = {"name": "Test Org"}

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.orgs.getOrg.return_value = mock_response

        result = upgrader._validate_organization()

        assert result is True
        assert upgrader.org_name == "Test Org"

    def test_failed_validation_status(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify failed validation with bad status code."""
        mock_response = MagicMock()
        mock_response.status_code = 403

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.orgs.getOrg.return_value = mock_response

        result = upgrader._validate_organization()

        assert result is False

    def test_failed_validation_exception(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify failed validation on exception."""
        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.orgs.getOrg.side_effect = RuntimeError("Connection refused")

        result = upgrader._validate_organization()

        assert result is False

        # Cleanup
        mock_mistapi.api.v1.orgs.orgs.getOrg.side_effect = None


# ---------------------------------------------------------------------------
# Site Selection Tests
# ---------------------------------------------------------------------------


class TestSiteSelection:
    """Test site selection step."""

    def test_override_sites(
        self,
        upgrader_with_override: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify override sites are used directly."""
        result = upgrader_with_override._select_sites()
        assert result is None
        assert len(upgrader_with_override.selected_sites) == 2

    def test_use_override_sites_empty(
        self,
        mock_apisession: MagicMock,
        mock_safe_input: MagicMock,
    ) -> None:
        """Verify empty override list."""
        up = BulkSwitchFirmwareUpgrader(
            org_id="test-org-id",
            apisession=mock_apisession,
            safe_input_fn=mock_safe_input,
            sites_override=[],
        )
        result = up._use_override_sites()
        assert result is None
        assert up.selected_sites == []

    @patch("builtins.input", return_value="A")
    def test_interactive_all_sites(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify selecting all sites interactively."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = [
            {"id": "s1", "name": "Site 1"},
            {"id": "s2", "name": "Site 2"},
        ]

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.sites.listOrgSites.return_value = mock_response

        result = upgrader._interactive_site_selection()
        assert result is None
        assert len(upgrader.selected_sites) == 2

    @patch("builtins.input", return_value="C")
    def test_interactive_cancel(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify cancellation during site selection."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = [{"id": "s1", "name": "Site 1"}]

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.sites.listOrgSites.return_value = mock_response

        result = upgrader._interactive_site_selection()
        assert result is not None
        assert result.get("cancelled") is True

    def test_interactive_api_error(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify error handling on API failure."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.sites.listOrgSites.return_value = mock_response

        result = upgrader._interactive_site_selection()
        assert result is not None
        assert "error" in result

    def test_interactive_exception(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify error handling on exception."""
        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.sites.listOrgSites.side_effect = RuntimeError("Network error")

        result = upgrader._interactive_site_selection()
        assert result is not None
        assert "error" in result

        # Cleanup
        mock_mistapi.api.v1.orgs.sites.listOrgSites.side_effect = None

    def test_display_site_list(self) -> None:
        """Verify site list display does not raise."""
        sites = [
            {"id": "s1", "name": "Site A"},
            {"id": "s2", "name": "Site B"},
        ]
        BulkSwitchFirmwareUpgrader._display_site_list(sites)

    @patch("builtins.input", return_value="1,3")
    def test_parse_specific_sites(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify specific site parsing with indices."""
        all_sites = [
            {"id": "s1", "name": "Site 1"},
            {"id": "s2", "name": "Site 2"},
            {"id": "s3", "name": "Site 3"},
        ]
        result = upgrader._parse_specific_sites(all_sites)
        assert result is None
        assert len(upgrader.selected_sites) == 2

    @patch("builtins.input", return_value="1-3")
    def test_parse_specific_sites_range(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify specific site parsing with range."""
        all_sites = [
            {"id": "s1", "name": "Site 1"},
            {"id": "s2", "name": "Site 2"},
            {"id": "s3", "name": "Site 3"},
        ]
        result = upgrader._parse_specific_sites(all_sites)
        assert result is None
        assert len(upgrader.selected_sites) == 3

    @patch("builtins.input", return_value="abc")
    def test_parse_specific_sites_invalid(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify error on invalid site selection."""
        all_sites = [{"id": "s1", "name": "Site 1"}]
        result = upgrader._parse_specific_sites(all_sites)
        assert result is not None
        assert "error" in result

    @patch("builtins.input", return_value="X")
    def test_prompt_invalid_choice(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify invalid choice handling."""
        all_sites = [{"id": "s1", "name": "Site 1"}]
        result = upgrader._prompt_site_selection(all_sites)
        assert result is not None
        assert "error" in result

    @patch("builtins.input", return_value="99")
    def test_parse_specific_sites_empty_result(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify error when no valid sites selected."""
        all_sites = [{"id": "s1", "name": "Site 1"}]
        result = upgrader._parse_specific_sites(all_sites)
        assert result is not None
        assert "error" in result


# ---------------------------------------------------------------------------
# Upgrade Parameters Tests
# ---------------------------------------------------------------------------


class TestUpgradeParameters:
    """Test upgrade parameter configuration."""

    @patch("builtins.input", side_effect=["1", "2", "1", "1"])
    def test_configure_parameters(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify parameter configuration flow."""
        result = upgrader._configure_upgrade_parameters()
        assert result is True
        assert upgrader.upgrade_strategy == "big_bang"
        assert upgrader.force_upgrade is False
        assert upgrader.auto_reboot is True
        assert upgrader.take_snapshot is True

    @patch("builtins.input", side_effect=["2"])
    def test_select_strategy_serial(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify serial strategy selection."""
        upgrader._select_strategy()
        assert upgrader.upgrade_strategy == "serial"

    @patch("builtins.input", side_effect=["3"])
    def test_select_strategy_canary(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify canary strategy selection."""
        upgrader._select_strategy()
        assert upgrader.upgrade_strategy == "canary"

    @patch("builtins.input", side_effect=["x", "1"])
    def test_select_strategy_invalid_then_valid(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify invalid strategy retries."""
        upgrader._select_strategy()
        assert upgrader.upgrade_strategy == "big_bang"

    @patch("builtins.input", side_effect=["1"])
    def test_select_force_yes(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify force upgrade enabled."""
        upgrader._select_force_option()
        assert upgrader.force_upgrade is True

    @patch("builtins.input", side_effect=["x", "2"])
    def test_select_force_invalid_then_no(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify force option retry on invalid."""
        upgrader._select_force_option()
        assert upgrader.force_upgrade is False

    @patch("builtins.input", side_effect=["2"])
    def test_select_reboot_no(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify reboot disabled shows warning."""
        upgrader._select_reboot_option()
        assert upgrader.auto_reboot is False

    @patch("builtins.input", side_effect=["x", "1"])
    def test_select_reboot_invalid_then_yes(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify reboot option retry."""
        upgrader._select_reboot_option()
        assert upgrader.auto_reboot is True

    @patch("builtins.input", side_effect=["2"])
    def test_select_snapshot_no(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify snapshot disabled."""
        upgrader._select_snapshot_option()
        assert upgrader.take_snapshot is False

    @patch("builtins.input", side_effect=["x", "1"])
    def test_select_snapshot_invalid_then_yes(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify snapshot option retry."""
        upgrader._select_snapshot_option()
        assert upgrader.take_snapshot is True


# ---------------------------------------------------------------------------
# Firmware Discovery Tests
# ---------------------------------------------------------------------------


class TestFirmwareDiscovery:
    """Test firmware discovery and selection."""

    def test_fetch_switch_inventory_success(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify successful switch inventory fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = [
            {"version": "23.4R2.21", "model": "EX4100-48P"},
            {"version": "22.4R3.25", "model": "EX4100-24P"},
            {"version": "23.4R2.21", "model": "EX4100-48P"},
        ]

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.inventory.getOrgInventory.return_value = mock_response

        result = upgrader._fetch_switch_inventory()
        assert result is True
        assert "EX4100-48P" in upgrader.switch_models
        assert "EX4100-24P" in upgrader.switch_models
        assert "23.4R2.21" in upgrader.current_firmware_versions
        assert "22.4R3.25" in upgrader.current_firmware_versions

    def test_fetch_switch_inventory_empty(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify empty inventory handling."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = []

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.inventory.getOrgInventory.return_value = mock_response

        result = upgrader._fetch_switch_inventory()
        assert result is False

    def test_fetch_switch_inventory_error(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify API error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.inventory.getOrgInventory.return_value = mock_response

        result = upgrader._fetch_switch_inventory()
        assert result is False

    def test_fetch_switch_inventory_exception(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify exception handling."""
        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.inventory.getOrgInventory.side_effect = RuntimeError("Timeout")

        result = upgrader._fetch_switch_inventory()
        assert result is False

        # Cleanup
        mock_mistapi.api.v1.orgs.inventory.getOrgInventory.side_effect = None

    def test_fetch_switch_inventory_no_models(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify warning when no models detected."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = [{"version": "23.4R2.21"}]

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.inventory.getOrgInventory.return_value = mock_response

        result = upgrader._fetch_switch_inventory()
        assert result is True
        assert len(upgrader.switch_models) == 0


# ---------------------------------------------------------------------------
# Cache Tests
# ---------------------------------------------------------------------------


class TestCaching:
    """Test firmware data caching."""

    def test_load_from_cache_no_file(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify no-cache-file returns None."""
        with patch("os.path.exists", return_value=False):
            result = upgrader._load_from_cache()
        assert result is None

    def test_load_from_cache_stale(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify stale cache returns None."""
        with (
            patch("os.path.exists", return_value=True),
            patch(
                "os.path.getmtime",
                return_value=time.time() - 100_000,
            ),
        ):
            result = upgrader._load_from_cache()
        assert result is None

    def test_load_from_cache_empty_file(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify empty cache returns None."""
        with (
            patch("os.path.exists", return_value=True),
            patch(
                "os.path.getmtime",
                return_value=time.time(),
            ),
            patch("os.path.getsize", return_value=0),
        ):
            result = upgrader._load_from_cache()
        assert result is None

    def test_load_from_cache_exception(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify cache read error returns None."""
        with (
            patch("os.path.exists", return_value=True),
            patch(
                "os.path.getmtime",
                side_effect=OSError("Permission denied"),
            ),
        ):
            result = upgrader._load_from_cache()
        assert result is None

    def test_save_and_read_cache(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify round-trip cache save and read."""
        firmware_data = [
            {
                "version": "23.4R2.21",
                "model": "EX4100-48P",
                "record_id": 123,
                "record_size": 456,
                "record_md5": "abc123",
                "_short": "23.4R2",
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "test_cache.csv")
            original_cache = upgrader.CACHE_FILE
            upgrader.CACHE_FILE = cache_path

            try:
                upgrader._save_to_cache(firmware_data)
                assert os.path.exists(cache_path)

                loaded = upgrader._read_cache_file()
                assert len(loaded) == 1
                assert loaded[0]["version"] == "23.4R2.21"
                assert loaded[0]["model"] == "EX4100-48P"
                assert loaded[0]["record_id"] == 123
                assert loaded[0]["record_size"] == 456
                assert loaded[0]["record_md5"] == "abc123"
            finally:
                upgrader.CACHE_FILE = original_cache

    def test_save_to_cache_error(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify cache save error handling."""
        original_cache = upgrader.CACHE_FILE
        upgrader.CACHE_FILE = "/nonexistent/path/cache.csv"

        try:
            upgrader._save_to_cache([{"version": "1.0"}])
        finally:
            upgrader.CACHE_FILE = original_cache

    def test_fetch_firmware_from_api_success(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify firmware API fetch success."""
        mock_response = MagicMock()
        mock_response.data = [{"version": "23.4R2.21", "model": "EX4100-48P"}]

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.devices.listOrgAvailableDeviceVersions.return_value = mock_response

        with patch.object(upgrader, "_save_to_cache"):
            result = upgrader._fetch_firmware_from_api()
        assert len(result) == 1

    def test_fetch_firmware_from_api_empty(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify empty API response handling."""
        mock_response = MagicMock()
        mock_response.data = []

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.devices.listOrgAvailableDeviceVersions.return_value = mock_response

        result = upgrader._fetch_firmware_from_api()
        assert result == []

    def test_fetch_firmware_from_api_exception(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify API exception handling."""
        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.devices.listOrgAvailableDeviceVersions.side_effect = RuntimeError("API error")

        result = upgrader._fetch_firmware_from_api()
        assert result == []

        # Cleanup
        mock_mistapi.api.v1.orgs.devices.listOrgAvailableDeviceVersions.side_effect = None


# ---------------------------------------------------------------------------
# Firmware Processing Tests
# ---------------------------------------------------------------------------


class TestFirmwareProcessing:
    """Test firmware data processing and version sorting."""

    def test_process_firmware_data(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify firmware data processing."""
        upgrader.switch_models = {"EX4100-48P", "EX4100-24P"}
        firmware_data = [
            {"version": "23.4R2.21", "model": "EX4100-48P"},
            {"version": "22.4R3.25", "model": "EX4100-24P"},
            {"version": "23.4R2.21", "model": "EX4100-24P"},
            {"version": "21.0R1.1", "model": "SRX-300"},
        ]

        upgrader._process_firmware_data(firmware_data)

        assert len(upgrader.available_versions) == 2
        assert "23.4R2.21" in upgrader.available_versions
        assert "22.4R3.25" in upgrader.available_versions
        assert "EX4100-48P" in upgrader.compatible_versions["23.4R2.21"]
        assert "EX4100-24P" in upgrader.compatible_versions["23.4R2.21"]

    def test_process_firmware_data_empty(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify empty firmware data."""
        upgrader.switch_models = {"EX4100-48P"}
        upgrader._process_firmware_data([])
        assert upgrader.available_versions == []

    def test_process_firmware_data_non_dict(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify non-dict entries are skipped."""
        upgrader.switch_models = {"EX4100-48P"}
        upgrader._process_firmware_data(["not-a-dict", None, 42])  # type: ignore[list-item]
        assert upgrader.available_versions == []

    def test_version_sort_key_standard(self) -> None:
        """Verify standard version sort key."""
        key = BulkSwitchFirmwareUpgrader._version_sort_key("23.4R2.21")
        assert key == [23, 4, 2, 21]

    def test_version_sort_key_with_suffix(self) -> None:
        """Verify version sort key with -S suffix."""
        key = BulkSwitchFirmwareUpgrader._version_sort_key("23.4R2-S1.21")
        assert isinstance(key, list)

    def test_version_sort_key_non_numeric(self) -> None:
        """Verify version sort key with non-numeric parts."""
        key = BulkSwitchFirmwareUpgrader._version_sort_key("beta.1.rc2")
        assert isinstance(key, list)

    def test_version_sort_ordering(self) -> None:
        """Verify versions sort in correct order."""
        versions = [
            "22.4R3.25",
            "23.4R2.21",
            "21.4R3.15",
        ]
        sorted_versions = sorted(
            versions,
            key=BulkSwitchFirmwareUpgrader._version_sort_key,
            reverse=True,
        )
        assert sorted_versions[0] == "23.4R2.21"
        assert sorted_versions[-1] == "21.4R3.15"


# ---------------------------------------------------------------------------
# Version Selection Tests
# ---------------------------------------------------------------------------


class TestVersionSelection:
    """Test firmware version selection."""

    @patch("builtins.input", return_value="1")
    def test_prompt_version_selection(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify version selection by index."""
        upgrader.available_versions = [
            "23.4R2.21",
            "22.4R3.25",
        ]
        upgrader.compatible_versions = {
            "23.4R2.21": {"EX4100-48P"},
            "22.4R3.25": {"EX4100-24P"},
        }

        result = upgrader._prompt_version_selection()
        assert result is None
        assert upgrader.target_version == "23.4R2.21"

    def test_get_version_selection_no_versions(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify handling when no versions available."""
        upgrader.available_versions = []
        upgrader.switch_models = set()

        with patch("builtins.input", return_value="n"):
            result = upgrader._get_version_selection()
        assert result is not None
        assert "error" in result

    @patch("builtins.input", side_effect=["y", "23.4R2.21"])
    def test_handle_no_versions_fallback(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify fallback to manual entry."""
        upgrader.switch_models = {"EX4100-48P"}

        result = upgrader._handle_no_versions()
        assert result is None
        assert upgrader.target_version == "23.4R2.21"

    def test_get_version_notes_installed(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify notes for installed version."""
        upgrader.current_firmware_versions = {"23.4R2.21"}
        notes = upgrader._get_version_notes("23.4R2.21", 2)
        assert "installed" in notes.lower()

    def test_get_version_notes_latest(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify notes for latest version."""
        notes = upgrader._get_version_notes("23.4R2.21", 1)
        assert "recommended" in notes.lower()

    def test_get_version_notes_other(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify empty notes for other versions."""
        notes = upgrader._get_version_notes("22.4R3.25", 3)
        assert notes == ""

    def test_format_compatible_models(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify model formatting."""
        upgrader.compatible_versions = {"23.4R2.21": {"EX4100-48P", "EX4100-24P"}}
        result = upgrader._format_compatible_models("23.4R2.21")
        assert "EX4100" in result

    def test_format_compatible_models_truncated(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify long model string is truncated."""
        upgrader.compatible_versions = {"23.4R2.21": {f"MODEL-{i}" for i in range(20)}}
        result = upgrader._format_compatible_models("23.4R2.21")
        assert len(result) <= 32

    def test_format_compatible_models_unknown(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify unknown models fallback."""
        upgrader.compatible_versions = {}
        result = upgrader._format_compatible_models("23.4R2.21")
        assert result == "Unknown"

    def test_display_version_table(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify version table display does not raise."""
        upgrader.available_versions = ["23.4R2.21"]
        upgrader.compatible_versions = {"23.4R2.21": {"EX4100-48P"}}
        upgrader._display_version_table()


# ---------------------------------------------------------------------------
# Confirmation Tests
# ---------------------------------------------------------------------------


class TestConfirmation:
    """Test upgrade confirmation step."""

    def test_confirm_upgrade_approved(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify successful confirmation."""
        upgrader.org_name = "Test Org"
        upgrader.selected_sites = [{"id": "s1"}]
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"

        result = upgrader._confirm_upgrade()
        assert result is True

    def test_confirm_upgrade_rejected(
        self,
        mock_apisession: MagicMock,
    ) -> None:
        """Verify rejected confirmation."""
        mock_safe = MagicMock(return_value="NO")
        up = BulkSwitchFirmwareUpgrader(
            org_id="test",
            apisession=mock_apisession,
            safe_input_fn=mock_safe,
        )
        up.org_name = "Test Org"
        up.selected_sites = [{"id": "s1"}]
        up.target_version = "23.4R2.21"
        up.upgrade_strategy = "big_bang"

        result = up._confirm_upgrade()
        assert result is False

    def test_confirm_upgrade_none(
        self,
        mock_apisession: MagicMock,
    ) -> None:
        """Verify None confirmation (EOF)."""
        mock_safe = MagicMock(return_value=None)
        up = BulkSwitchFirmwareUpgrader(
            org_id="test",
            apisession=mock_apisession,
            safe_input_fn=mock_safe,
        )
        up.org_name = "Test Org"
        up.selected_sites = [{"id": "s1"}]
        up.target_version = "23.4R2.21"
        up.upgrade_strategy = "big_bang"

        result = up._confirm_upgrade()
        assert result is False


# ---------------------------------------------------------------------------
# Execution Tests
# ---------------------------------------------------------------------------


class TestExecution:
    """Test upgrade execution step."""

    def test_initialize_results(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify results initialization."""
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"

        upgrader._initialize_results()

        assert "operation_id" in upgrader.upgrade_results
        assert upgrader.upgrade_results["target_version"] == "23.4R2.21"
        assert upgrader.upgrade_results["sites_processed"] == 0
        assert upgrader.upgrade_results["sites_successful"] == 0
        assert upgrader.upgrade_results["sites_failed"] == 0

    def test_build_upgrade_request(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify upgrade request payload."""
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "serial"
        upgrader.force_upgrade = True
        upgrader.auto_reboot = True
        upgrader.take_snapshot = False

        request = upgrader._build_upgrade_request(["dev-1", "dev-2"])

        assert request["version"] == "23.4R2.21"
        assert request["strategy"] == "serial"
        assert request["force"] is True
        assert request["reboot"] is True
        assert request["snapshot"] is False
        assert request["device_ids"] == ["dev-1", "dev-2"]

    def test_process_site_no_id(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify site with no ID is skipped."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"
        upgrader.selected_sites = [{"name": "Bad Site"}]

        upgrader._process_site(1, {"name": "Bad Site"})
        assert upgrader.upgrade_results["sites_failed"] == 1

    def test_process_site_no_switches(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify site with no switches is skipped."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"
        upgrader.selected_sites = [{"id": "s1", "name": "Empty Site"}]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = []

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = mock_response

        upgrader._process_site(1, {"id": "s1", "name": "Empty Site"})
        results = upgrader.upgrade_results["site_results"]
        assert len(results) == 1
        assert results[0]["status"] == "skipped"

    def test_process_site_api_error(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify site with API error is recorded."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"
        upgrader.selected_sites = [{"id": "s1", "name": "Error Site"}]

        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = mock_response

        upgrader._process_site(1, {"id": "s1", "name": "Error Site"})
        assert upgrader.upgrade_results["sites_failed"] == 1

    def test_process_site_exception(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify site exception is recorded."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"
        upgrader.selected_sites = [{"id": "s1", "name": "Crash Site"}]

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.sites.devices.listSiteDevices.side_effect = RuntimeError("Crash")

        upgrader._process_site(1, {"id": "s1", "name": "Crash Site"})
        assert upgrader.upgrade_results["sites_failed"] == 1

        # Cleanup
        mock_mistapi.api.v1.sites.devices.listSiteDevices.side_effect = None

    def test_record_upgrade_result_success(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify successful upgrade result recording."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"

        mock_response = MagicMock()
        mock_response.status_code = 200

        switches = [
            {"id": "d1", "type": "switch"},
            {"id": "d2", "type": "switch"},
        ]

        upgrader._record_upgrade_result("s1", "Site 1", switches, mock_response)

        assert upgrader.upgrade_results["sites_successful"] == 1
        result = upgrader.upgrade_results["site_results"][0]
        assert result["status"] == "initiated"
        assert result["switches_count"] == 2

    def test_record_upgrade_result_failure(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify failed upgrade result recording."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.data = {"error": "Bad request"}

        switches = [{"id": "d1", "type": "switch"}]

        upgrader._record_upgrade_result("s1", "Site 1", switches, mock_response)

        assert upgrader.upgrade_results["sites_failed"] == 1

    def test_record_upgrade_result_202(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify 202 accepted response."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"

        mock_response = MagicMock()
        mock_response.status_code = 202

        upgrader._record_upgrade_result("s1", "Site 1", [{"id": "d1"}], mock_response)
        assert upgrader.upgrade_results["sites_successful"] == 1

    def test_record_no_switches(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify no-switches recording."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"

        upgrader._record_no_switches("s1", "Empty Site")

        result = upgrader.upgrade_results["site_results"][0]
        assert result["status"] == "skipped"

    def test_record_site_error(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify site error recording."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"

        upgrader._record_site_error("s1", "Failed Site", "Connection timeout")

        assert upgrader.upgrade_results["sites_failed"] == 1
        result = upgrader.upgrade_results["site_results"][0]
        assert result["error"] == "Connection timeout"

    def test_finalize_results(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify results finalization."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"

        upgrader._finalize_results()

        assert upgrader.upgrade_results["end_time"] is not None

    def test_display_results_summary(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify summary display does not raise."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"
        upgrader._display_results_summary()

    def test_display_failure_details_with_failures(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify failure details display."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"
        upgrader.upgrade_results["sites_failed"] = 2
        upgrader.upgrade_results["site_results"] = [
            {
                "site_name": "Site A",
                "status": "failed",
                "error": "Timeout",
            },
            {
                "site_name": "Site B",
                "status": "error",
                "error": "Connection refused",
            },
        ]

        upgrader._display_failure_details()

    def test_display_failure_details_no_failures(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify no output when no failures."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"
        upgrader._display_failure_details()

    def test_handle_critical_error(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify critical error handling."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"

        result = upgrader._handle_critical_error(RuntimeError("Fatal error"))

        assert "error" in result
        assert result["end_time"] is not None

    def test_display_config_summary(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify config summary display does not raise."""
        upgrader.org_name = "Test Org"
        upgrader.selected_sites = [{"id": "s1"}]
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"
        upgrader._display_config_summary()

    def test_display_warnings(self) -> None:
        """Verify warnings display does not raise."""
        BulkSwitchFirmwareUpgrader._display_warnings()

    def test_execute_site_upgrade_no_device_ids(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify handling when no device IDs found."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"

        switches: list[dict[str, Any]] = [{"name": "switch-no-id"}]
        upgrader._execute_site_upgrade("s1", "Site 1", switches)

        assert upgrader.upgrade_results["sites_failed"] == 1


# ---------------------------------------------------------------------------
# Integration-Level Execute Tests
# ---------------------------------------------------------------------------


class TestExecuteWorkflow:
    """Test the full execute workflow."""

    def test_execute_validation_failure(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify execute returns error on validation failure."""
        mock_response = MagicMock()
        mock_response.status_code = 403

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.orgs.getOrg.return_value = mock_response

        result = upgrader.execute()
        assert "error" in result

    def test_execute_site_selection_cancelled(
        self,
        upgrader_with_override: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify execute with override sites proceeds past site selection."""
        mock_org = MagicMock()
        mock_org.status_code = 200
        mock_org.data = {"name": "Test Org"}

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.orgs.getOrg.return_value = mock_org

        with patch("builtins.input", side_effect=["1", "2", "1", "1"]):
            mock_inv = MagicMock()
            mock_inv.status_code = 200
            mock_inv.data = []
            mock_mistapi.api.v1.orgs.inventory.getOrgInventory.return_value = mock_inv

            result = upgrader_with_override.execute()

        assert "error" in result

    def test_execute_configure_cancelled(
        self,
        upgrader_with_override: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify execute returns cancelled when configure_upgrade_parameters returns False."""
        mock_org = MagicMock()
        mock_org.status_code = 200
        mock_org.data = {"name": "Test Org"}

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.orgs.getOrg.return_value = mock_org

        with patch.object(
            upgrader_with_override,
            "_configure_upgrade_parameters",
            return_value=False,
        ):
            result = upgrader_with_override.execute()

        assert result == {"cancelled": True}

    def test_execute_confirm_cancelled(
        self,
        upgrader_with_override: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify execute returns cancelled when confirm_upgrade returns False."""
        mock_org = MagicMock()
        mock_org.status_code = 200
        mock_org.data = {"name": "Test Org"}

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.orgs.getOrg.return_value = mock_org

        with (
            patch.object(
                upgrader_with_override,
                "_configure_upgrade_parameters",
                return_value=True,
            ),
            patch.object(
                upgrader_with_override,
                "_discover_and_select_firmware",
                return_value=None,
            ),
            patch.object(
                upgrader_with_override,
                "_confirm_upgrade",
                return_value=False,
            ),
        ):
            result = upgrader_with_override.execute()

        assert result == {"cancelled": True}

    def test_execute_full_success(
        self,
        upgrader_with_override: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify execute returns results from _execute_upgrades on success."""
        mock_org = MagicMock()
        mock_org.status_code = 200
        mock_org.data = {"name": "Test Org"}

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.orgs.getOrg.return_value = mock_org

        expected = {"status": "complete", "sites_processed": 1}

        with (
            patch.object(
                upgrader_with_override,
                "_configure_upgrade_parameters",
                return_value=True,
            ),
            patch.object(
                upgrader_with_override,
                "_discover_and_select_firmware",
                return_value=None,
            ),
            patch.object(
                upgrader_with_override,
                "_confirm_upgrade",
                return_value=True,
            ),
            patch.object(
                upgrader_with_override,
                "_execute_upgrades",
                return_value=expected,
            ),
        ):
            result = upgrader_with_override.execute()

        assert result == expected


# ---------------------------------------------------------------------------
# Additional Coverage Tests
# ---------------------------------------------------------------------------


class TestAdditionalCoverage:
    """Cover remaining lines for 90%+ coverage."""

    def test_validate_org_exception(self, upgrader: BulkSwitchFirmwareUpgrader) -> None:
        """Verify org validation handles exceptions."""
        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.orgs.getOrg.side_effect = RuntimeError("Connection refused")

        result = upgrader._validate_organization()
        assert result is False

        mock_mistapi.api.v1.orgs.orgs.getOrg.side_effect = None

    def test_interactive_site_selection_api_error(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify interactive site selection handles API error."""
        mock_mistapi = sys.modules["mistapi"]
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_mistapi.api.v1.orgs.sites.listOrgSites.return_value = mock_response

        result = upgrader._interactive_site_selection()
        assert result is not None
        assert "error" in result

    def test_interactive_site_selection_exception(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify interactive site selection handles exception."""
        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.sites.listOrgSites.side_effect = RuntimeError("Boom")

        result = upgrader._interactive_site_selection()
        assert result is not None
        assert "error" in result

        mock_mistapi.api.v1.orgs.sites.listOrgSites.side_effect = None

    def test_discover_firmware_inventory_failure(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify discover_and_select_firmware returns error when inventory fails."""
        with patch.object(
            upgrader,
            "_fetch_switch_inventory",
            return_value=False,
        ):
            result = upgrader._discover_and_select_firmware()

        assert result is not None
        assert "error" in result

    def test_discover_firmware_no_data(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify discover_and_select_firmware returns error when no firmware data."""
        with (
            patch.object(
                upgrader,
                "_fetch_switch_inventory",
                return_value=True,
            ),
            patch.object(upgrader, "_load_firmware_data", return_value=[]),
        ):
            result = upgrader._discover_and_select_firmware()

        assert result is not None
        assert "error" in result

    def test_cache_stale_returns_none(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
        tmp_path: Any,
    ) -> None:
        """Verify stale cache returns None."""
        cache_file = tmp_path / "stale_cache.csv"
        cache_file.write_text("version,model\n23.4R2.21,EX4100\n")

        original_cache = upgrader.CACHE_FILE
        upgrader.CACHE_FILE = str(cache_file)

        old_time = time.time() - (25 * 3600)
        os.utime(str(cache_file), (old_time, old_time))

        result = upgrader._load_from_cache()
        assert result is None

        upgrader.CACHE_FILE = original_cache

    def test_cache_empty_file_returns_none(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
        tmp_path: Any,
    ) -> None:
        """Verify empty cache file returns None."""
        cache_file = tmp_path / "empty_cache.csv"
        cache_file.write_text("")

        original_cache = upgrader.CACHE_FILE
        upgrader.CACHE_FILE = str(cache_file)

        result = upgrader._load_from_cache()
        assert result is None

        upgrader.CACHE_FILE = original_cache

    def test_process_firmware_data_skips_nondict(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify non-dict entries are skipped."""
        upgrader.switch_models = {"EX4100-48P"}
        data: list[Any] = [
            "not-a-dict",
            {"version": "23.4R2.21", "model": "EX4100-48P"},
        ]
        upgrader._process_firmware_data(data)
        assert len(upgrader.available_versions) == 1

    def test_version_sort_key_exception(self) -> None:
        """Verify sort key handles unparseable versions."""
        result = BulkSwitchFirmwareUpgrader._version_sort_key("")
        assert isinstance(result, list)

    def test_display_version_table(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify version table display runs without error."""
        upgrader.available_versions = ["23.4R2.21", "22.4R3.25"]
        upgrader.compatible_versions = {
            "23.4R2.21": {"EX4100-48P"},
            "22.4R3.25": {"EX4100-48P"},
        }
        upgrader.current_firmware_versions = {"22.4R3.25"}

        upgrader._display_version_table()

    @patch("builtins.input", side_effect=["", "1"])
    def test_prompt_version_selection_empty_then_valid(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify empty input retries, valid input selects."""
        upgrader.available_versions = ["23.4R2.21", "22.4R3.25"]

        result = upgrader._prompt_version_selection()
        assert result is None
        assert upgrader.target_version == "23.4R2.21"

    @patch("builtins.input", side_effect=["99", "1"])
    def test_prompt_version_selection_out_of_range(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify out-of-range retries."""
        upgrader.available_versions = ["23.4R2.21"]

        result = upgrader._prompt_version_selection()
        assert result is None

    @patch("builtins.input", side_effect=["abc", "1"])
    def test_prompt_version_selection_invalid_input(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify non-numeric input retries."""
        upgrader.available_versions = ["23.4R2.21"]

        result = upgrader._prompt_version_selection()
        assert result is None

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_prompt_version_selection_keyboard_interrupt(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify KeyboardInterrupt returns cancelled."""
        upgrader.available_versions = ["23.4R2.21"]

        result = upgrader._prompt_version_selection()
        assert result is not None
        assert "cancelled" in result

    def test_execute_upgrades_success(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify _execute_upgrades processes sites and returns results."""
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"
        upgrader.selected_sites = [{"id": "s1", "name": "Site 1"}]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = [{"id": "d1", "type": "switch"}]

        mock_upgrade_resp = MagicMock()
        mock_upgrade_resp.status_code = 200

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = mock_response
        mock_mistapi.api.v1.sites.devices.upgradeSiteDevices.return_value = mock_upgrade_resp

        result = upgrader._execute_upgrades()
        assert result["sites_processed"] == 1
        assert result["sites_successful"] == 1
        assert result["end_time"] is not None

    def test_execute_upgrades_exception(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify _execute_upgrades handles critical exception."""
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"
        upgrader.selected_sites = [{"id": "s1", "name": "Site 1"}]

        with patch.object(
            upgrader,
            "_process_site",
            side_effect=RuntimeError("Fatal"),
        ):
            result = upgrader._execute_upgrades()

        assert "error" in result

    def test_get_site_switches_error(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify _get_site_switches returns None on API error."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"

        mock_response = MagicMock()
        mock_response.status_code = 403

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.sites.devices.listSiteDevices.return_value = mock_response

        result = upgrader._get_site_switches("s1", "Forbidden Site")
        assert result is None
        assert upgrader.upgrade_results["sites_failed"] == 1

    def test_execute_site_upgrade_success(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify _execute_site_upgrade calls API and records success."""
        upgrader._initialize_results()
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"
        upgrader.force_upgrade = False
        upgrader.auto_reboot = True
        upgrader.take_snapshot = False

        switches = [{"id": "d1", "type": "switch"}]
        mock_upgrade_resp = MagicMock()
        mock_upgrade_resp.status_code = 200

        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.sites.devices.upgradeSiteDevices.return_value = mock_upgrade_resp

        upgrader._execute_site_upgrade("s1", "Site 1", switches)
        assert upgrader.upgrade_results["sites_successful"] == 1

    def test_handle_no_versions_no_models(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify _handle_no_versions with empty switch_models."""
        upgrader.switch_models = set()

        with patch("builtins.input", return_value="n"):
            result = upgrader._handle_no_versions()

        assert result is not None
        assert "error" in result

    @patch("builtins.input", side_effect=["y", "", "23.4R2.21"])
    def test_manual_version_entry_empty_retry(
        self,
        _mock_input: MagicMock,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify empty manual version retries."""
        upgrader.switch_models = {"EX4100-48P"}

        result = upgrader._handle_no_versions()
        assert result is None
        assert upgrader.target_version == "23.4R2.21"

    def test_get_version_selection_with_versions(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify _get_version_selection calls display and prompt."""
        upgrader.available_versions = ["23.4R2.21"]
        upgrader.compatible_versions = {"23.4R2.21": {"EX4100-48P"}}

        with patch("builtins.input", return_value="1"):
            result = upgrader._get_version_selection()

        assert result is None
        assert upgrader.target_version == "23.4R2.21"

    def test_confirm_upgrade_success(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify confirm_upgrade returns True when confirmed."""
        upgrader.org_name = "Test Org"
        upgrader.selected_sites = [{"id": "s1"}]
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"

        upgrader.safe_input_fn = lambda prompt, *args, **kwargs: "UPGRADE SWITCHES"

        result = upgrader._confirm_upgrade()
        assert result is True

    def test_confirm_upgrade_rejected(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify confirm_upgrade returns False when not confirmed."""
        upgrader.org_name = "Test Org"
        upgrader.selected_sites = [{"id": "s1"}]
        upgrader.target_version = "23.4R2.21"
        upgrader.upgrade_strategy = "big_bang"

        upgrader.safe_input_fn = lambda prompt, *args, **kwargs: "NO"

        result = upgrader._confirm_upgrade()
        assert result is False

    def test_fetch_firmware_from_api_empty_response(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify empty API response returns empty list."""
        mock_mistapi = sys.modules["mistapi"]
        mock_response = MagicMock()
        mock_response.data = None
        mock_mistapi.api.v1.orgs.devices.listOrgAvailableDeviceVersions.return_value = mock_response

        result = upgrader._fetch_firmware_from_api()
        assert result == []

    def test_fetch_firmware_from_api_exception(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify API exception returns empty list."""
        mock_mistapi = sys.modules["mistapi"]
        mock_mistapi.api.v1.orgs.devices.listOrgAvailableDeviceVersions.side_effect = RuntimeError("API error")

        result = upgrader._fetch_firmware_from_api()
        assert result == []

        mock_mistapi.api.v1.orgs.devices.listOrgAvailableDeviceVersions.side_effect = None

    def test_save_to_cache_exception(
        self,
        upgrader: BulkSwitchFirmwareUpgrader,
    ) -> None:
        """Verify cache save handles write error gracefully."""
        original = upgrader.CACHE_FILE
        upgrader.CACHE_FILE = "/nonexistent/path/cache.csv"

        upgrader._save_to_cache([{"version": "23.4R2.21", "model": "EX4100"}])

        upgrader.CACHE_FILE = original

    def test_display_site_list(self) -> None:
        """Verify site list display."""
        sites = [
            {"name": "Office A", "id": "s1"},
            {"name": "Office B", "id": "s2"},
        ]
        BulkSwitchFirmwareUpgrader._display_site_list(sites)
