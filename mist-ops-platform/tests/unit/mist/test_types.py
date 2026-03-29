"""Tests for MistEndpoint dataclass with optional fields and list_method (T004)."""

from src.shared.mist.types import MistEndpoint, MistEntityRegistry


class TestMistEndpointOptionalFields:
    """Verify MistEndpoint supports optional read/write and list_method."""

    def test_all_fields_provided(self) -> None:
        endpoint = MistEndpoint(
            entity_type="device",
            api_module="sites.devices",
            read_method="getSiteDevice",
            write_method="updateSiteDevice",
            id_params=("site_id", "device_id"),
            list_method="listSiteDevices",
        )
        assert endpoint.read_method == "getSiteDevice"
        assert endpoint.write_method == "updateSiteDevice"
        assert endpoint.list_method == "listSiteDevices"

    def test_read_only_endpoint(self) -> None:
        endpoint = MistEndpoint(
            entity_type="device_stats",
            api_module="sites.stats",
            read_method="getSiteDeviceStats",
            write_method=None,
            id_params=("site_id", "device_id"),
        )
        assert endpoint.read_method == "getSiteDeviceStats"
        assert endpoint.write_method is None
        assert endpoint.list_method is None

    def test_write_only_endpoint(self) -> None:
        endpoint = MistEndpoint(
            entity_type="firmware_site",
            api_module="sites.devices",
            read_method=None,
            write_method="upgradeSiteDevices",
            id_params=("site_id",),
        )
        assert endpoint.read_method is None
        assert endpoint.write_method == "upgradeSiteDevices"

    def test_list_only_endpoint(self) -> None:
        endpoint = MistEndpoint(
            entity_type="org_site_list",
            api_module="orgs.sites",
            read_method=None,
            write_method=None,
            id_params=("org_id",),
            list_method="listOrgSites",
        )
        assert endpoint.read_method is None
        assert endpoint.write_method is None
        assert endpoint.list_method == "listOrgSites"

    def test_frozen_immutability(self) -> None:
        endpoint = MistEndpoint(
            entity_type="test",
            api_module="orgs.sites",
            read_method=None,
            write_method=None,
            id_params=("org_id",),
            list_method="listOrgSites",
        )
        try:
            endpoint.entity_type = "changed"  # type: ignore[misc]
            raise AssertionError("Should be frozen")
        except AttributeError:
            pass

    def test_list_method_defaults_none(self) -> None:
        endpoint = MistEndpoint(
            entity_type="device",
            api_module="sites.devices",
            read_method="getSiteDevice",
            write_method="updateSiteDevice",
            id_params=("site_id", "device_id"),
        )
        assert endpoint.list_method is None


class TestMistEntityRegistryLookup:
    """Verify registry lookup works with modified dataclass."""

    def test_get_existing_type(self) -> None:
        endpoint = MistEntityRegistry.get("device")
        assert endpoint.entity_type == "device"
        assert endpoint.api_module == "sites.devices"

    def test_get_unknown_raises(self) -> None:
        try:
            MistEntityRegistry.get("nonexistent_type")
            raise AssertionError("Should raise ValueError")
        except ValueError as exc:
            assert "nonexistent_type" in str(exc)

    def test_has_known_type(self) -> None:
        assert MistEntityRegistry.has("device") is True

    def test_has_unknown_type(self) -> None:
        assert MistEntityRegistry.has("nonexistent") is False
