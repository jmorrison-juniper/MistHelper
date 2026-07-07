"""
Unit test scaffolding for DeviceUtilityCommands.readopt_device (Menu #143)

These tests are scaffolds and are marked xfail until the preflight VC-capability checks are implemented.
"""

from unittest.mock import MagicMock

import mistapi
import pytest

from src.device.utility_commands import DeviceUtilityCommands


def make_mock_response(data=None, status_code=200):
    m = MagicMock()
    m.data = data
    m.status_code = status_code
    return m


@pytest.mark.xfail(reason="Preflight VC check not yet implemented in DeviceUtilityCommands.readopt_device")
def test_readopt_calls_api_when_device_is_vc(monkeypatch):
    # Arrange: select a device
    monkeypatch.setattr(
        DeviceUtilityCommands,
        "_select_site_and_device",
        lambda action, *args, **kwargs: ("site-1", "dev-1", "Device1"),
    )

    # Simulate getSiteDeviceVirtualChassis indicating VC membership
    def fake_get_vc(session, site_id, device_id):
        return make_mock_response(data={"is_virtual_chassis": True})

    monkeypatch.setattr(mistapi.api.v1.sites.devices, "getSiteDeviceVirtualChassis", fake_get_vc)

    called = {"readopt": False}

    def fake_readopt(session, site_id, device_id):
        called["readopt"] = True
        return make_mock_response()

    monkeypatch.setattr(mistapi.api.v1.sites.devices, "readoptSiteOctermDevice", fake_readopt)

    # Act
    DeviceUtilityCommands.readopt_device()

    # Assert
    assert called["readopt"] is True


@pytest.mark.xfail(reason="Preflight VC check not yet implemented")
def test_readopt_skips_non_vc_device(monkeypatch):
    monkeypatch.setattr(
        DeviceUtilityCommands,
        "_select_site_and_device",
        lambda action, *args, **kwargs: ("site-1", "dev-1", "Device1"),
    )

    def fake_get_vc(session, site_id, device_id):
        return make_mock_response(data={"is_virtual_chassis": False})

    monkeypatch.setattr(mistapi.api.v1.sites.devices, "getSiteDeviceVirtualChassis", fake_get_vc)

    called = {"readopt": False}

    def fake_readopt(session, site_id, device_id):
        called["readopt"] = True
        return make_mock_response()

    monkeypatch.setattr(mistapi.api.v1.sites.devices, "readoptSiteOctermDevice", fake_readopt)

    DeviceUtilityCommands.readopt_device()

    assert called["readopt"] is False
