"""Prove firmware policy shape, inheritance removal, and unrelated-setting preservation."""

from __future__ import annotations

from copy import deepcopy

import pytest

from src.operations.execution.firmware_policy.changes import FirmwarePolicy, PolicyChanges
from src.operations.execution.firmware_policy.sdk import PolicyError


@pytest.mark.parametrize("kind", ["ap", "switch", "ssr", "juniper_srx"])
def test_organization_preserves_siblings_and_replaces_versions(kind: str) -> None:
    """Replace selected model values without deleting unrelated parent members."""
    settings = {kind: {"proxy": {"url": "private"}, "auto_upgrade": {"version": "old", "snapshot": True}}}
    before = deepcopy(settings)
    policy = FirmwarePolicy(kind, False, {"MODEL": "new"})
    body = PolicyChanges.organization(settings, [policy])
    saved_policy = body["auto_upgrade"] if kind == "ap" else body[kind]["auto_upgrade"]
    assert saved_policy["enabled"] is False
    assert saved_policy["custom_versions"] == {"MODEL": "new"}
    if kind != "ap":
        assert body[kind]["proxy"] == {"url": "private"}
        assert "version" not in saved_policy
    else:
        assert saved_policy["version"] == "custom"
        assert saved_policy["time_of_day"] == "any"
    assert settings == before


@pytest.mark.parametrize("time", ["24:00", "12:60", "9:05", "never", "12:34:00"])
def test_invalid_ap_time_fails(time: str) -> None:
    """Reject times outside the schema format."""
    with pytest.raises(PolicyError, match="HH:MM"):
        FirmwarePolicy("ap", True, {"AP41": "v1"}, time=time)


@pytest.mark.parametrize(
    "values",
    [
        {"kind": "unknown", "enabled": False, "models": {"AP41": "v1"}},
        {"kind": "ap", "enabled": "yes", "models": {"AP41": "v1"}},
        {"kind": "ap", "enabled": True, "models": {}},
        {"kind": "ap", "enabled": True, "models": {"AP41": ""}},
        {"kind": "switch", "enabled": True, "models": {"EX": "v1"}, "day": "mon"},
        {"kind": "ap", "enabled": True, "models": {"AP41": "v1"}, "day": "monday"},
    ],
)
def test_invalid_policy_fails(values: dict) -> None:
    """Reject unsupported or incomplete operator choices."""
    with pytest.raises(PolicyError):
        FirmwarePolicy(**values)


def test_site_removal_preserves_all_nested_siblings() -> None:
    """Use the AP unset marker and replace complete nested containers."""
    original = {
        "auto_upgrade": {"enabled": False},
        "timezone": "America/New_York",
        "switch": {"auto_upgrade": {"custom_versions": {"EX": "old"}}, "networks": {"a": {"vlan_id": 5}}},
        "ssr": {"auto_upgrade": {"enabled": True}, "conductor_token": "private-value"},
        "juniper_srx": {"auto_upgrade": {"enabled": True}, "gateways": {"one": "two"}},
    }
    before = deepcopy(original)
    body = PolicyChanges.site(original)
    assert body["-auto_upgrade"] == ""
    assert body["switch"] == {"networks": {"a": {"vlan_id": 5}}}
    assert body["ssr"] == {"conductor_token": "private-value"}
    assert body["juniper_srx"] == {"gateways": {"one": "two"}}
    assert "timezone" not in body
    assert original == before
    saved = {key: value for key, value in original.items() if key != "auto_upgrade"}
    saved.update({key: value for key, value in body.items() if key != "-auto_upgrade"})
    PolicyChanges.verify_site(saved, original)


@pytest.mark.parametrize("settings", [{"switch": None}, {"ssr": []}, {"juniper_srx": "bad"}])
def test_malformed_parent_fails(settings: dict) -> None:
    """Refuse unsafe replacement when a parent object is unreadable."""
    with pytest.raises(PolicyError, match="not an object"):
        PolicyChanges.site(settings)


def test_readback_rejects_remaining_override_and_changed_siblings() -> None:
    """A successful HTTP write alone is not proof of inheritance."""
    with pytest.raises(PolicyError, match="override remains"):
        PolicyChanges.verify_site({"auto_upgrade": {}}, {})
    with pytest.raises(PolicyError, match="timezone"):
        PolicyChanges.verify_site({"timezone": "UTC"}, {"timezone": "Europe/London"})
    with pytest.raises(PolicyError, match="Organization verification"):
        PolicyChanges.verify_org({"auto_upgrade": {"enabled": False}}, {"auto_upgrade": {"enabled": True}})


def test_inherited_site_needs_no_write() -> None:
    """A site with no local policy remains unchanged."""
    assert PolicyChanges.site({"timezone": "UTC", "ssr": {"disable_stats": True}}) == {}


def test_site_readback_allows_server_timestamp_and_omitted_empty_container() -> None:
    """Server-managed modification time and empty-object normalization do not alter settings."""
    original = {"modified_time": 1, "ssr": {"auto_upgrade": {"enabled": False}}, "timezone": "UTC"}
    saved = {"modified_time": 2, "timezone": "UTC"}
    PolicyChanges.verify_site(saved, original)
    assert PolicyChanges.site(saved) == {}
