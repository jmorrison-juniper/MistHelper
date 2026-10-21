"""Test local workflows with controlled responses and no cloud access."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolver
from src.foundation.support.utils.address_utils import AddressUtils
from src.mist.resources.device import ap_profile_migration_manager as ap_module
from src.mist.resources.device.ap_profile_migration_manager import APProfileMigrationManager
from src.mist.resources.inventory.csv_comparator import InventoryCSVComparator
from src.mist.resources.org.org_config_migration_manager import OrgConfigMigrationManager


def test_ap_backup_rejects_a_missing_required_plan_before_work(tmp_path: Path) -> None:
    """Reject an absent AP plan before any migration action can use it."""
    backup = tmp_path / "backup.json"
    backup.write_text(
        '{"schema_version":1,"org_id":"org","source_profile_id":"src",'
        '"target_profile_id":"dst","migration_timestamp_utc":"2026-10-20T00:00:00Z"}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="aps_planned"):
        APProfileMigrationManager._load_and_validate_backup(str(backup))


@pytest.mark.parametrize("data", [None, "", "   ", {}, 7, [None]])
def test_ap_profile_fallback_rejects_incomplete_response_data(
    data: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject missing or invalid API data instead of treating it as no profiles."""
    response = SimpleNamespace(data=data, status_code=200)
    monkeypatch.setattr(ap_module._mist_deviceprofiles, "listOrgDeviceProfiles", lambda *_: response)
    monkeypatch.setattr(
        ap_module.mistapi,
        "get_all",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("pagination failed")),
    )

    with pytest.raises(ValueError, match="response.data"):
        APProfileMigrationManager._fetch_and_sort_ap_profiles(object(), "org")


def test_ap_profile_fallback_rejects_a_missing_data_attribute(monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse a pagination fallback when the response has no data field."""
    response = SimpleNamespace(status_code=200)
    monkeypatch.setattr(ap_module._mist_deviceprofiles, "listOrgDeviceProfiles", lambda *_: response)
    monkeypatch.setattr(
        ap_module.mistapi,
        "get_all",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("pagination failed")),
    )

    with pytest.raises(ValueError, match="response.data"):
        APProfileMigrationManager._fetch_and_sort_ap_profiles(object(), "org")


def test_ap_profile_fallback_rejects_a_missing_http_status(monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not treat a response without a status code as a successful empty result."""
    response = SimpleNamespace(data=[])
    monkeypatch.setattr(ap_module._mist_deviceprofiles, "listOrgDeviceProfiles", lambda *_: response)
    monkeypatch.setattr(
        ap_module.mistapi,
        "get_all",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("pagination failed")),
    )

    with pytest.raises(RuntimeError, match="HTTP status None"):
        APProfileMigrationManager._fetch_and_sort_ap_profiles(object(), "org")


def test_ap_profile_fallback_preserves_a_valid_empty_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the existing visible no-profiles result for a valid empty list."""
    response = SimpleNamespace(data=[], status_code=200)
    monkeypatch.setattr(ap_module._mist_deviceprofiles, "listOrgDeviceProfiles", lambda *_: response)
    monkeypatch.setattr(
        ap_module.mistapi,
        "get_all",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("pagination failed")),
    )

    with pytest.raises(RuntimeError, match="No AP device profiles"):
        APProfileMigrationManager._fetch_and_sort_ap_profiles(object(), "org")


def test_site_discovery_rejects_missing_site_data_before_device_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stop AP discovery before listing devices when site data is absent."""
    device_calls: list[str] = []
    response = SimpleNamespace(status_code=200)
    monkeypatch.setattr(ap_module._mist_orgs_sites, "listOrgSites", lambda *_: response)
    monkeypatch.setattr(
        ap_module._mist_site_devices,
        "listSiteDevices",
        lambda *_args, **_kwargs: device_calls.append("called"),
    )
    monkeypatch.setattr(
        ap_module.mistapi,
        "get_all",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("pagination failed")),
    )

    with pytest.raises(ValueError, match="response.data"):
        APProfileMigrationManager._discover_aps_on_source_profile(object(), "org", "profile")

    assert device_calls == []


@pytest.mark.parametrize(
    ("profile_id", "expected"),
    [(None, None), ("", None), ("   ", None), (7, None), ([], None), ("profile-1", "profile-1")],
)
def test_profile_picker_requires_a_valid_id(
    profile_id: object,
    expected: str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject absent and wrong-type profile IDs before migration can begin."""
    monkeypatch.setattr(
        APProfileMigrationManager,
        "_fetch_and_sort_ap_profiles",
        staticmethod(lambda *_args: [{"id": profile_id, "name": "Profile"}]),
    )
    monkeypatch.setattr(SourceDependencyResolver.InputUtils, "safe_input", lambda *_args, **_kwargs: "1")

    if expected is None:
        with pytest.raises(RuntimeError, match="profile id"):
            APProfileMigrationManager._pick_ap_device_profile(object(), "org", "Select profile")
    else:
        result = APProfileMigrationManager._pick_ap_device_profile(object(), "org", "Select profile")
        assert result[0] == expected


def test_org_create_failure_preserves_earlier_result_and_adds_no_mapping() -> None:
    """Keep prior results when a controlled create response has no identity."""
    manager = OrgConfigMigrationManager.__new__(OrgConfigMigrationManager)
    manager._remap_table = {}
    results = [{"type": "networks", "name": "First", "status": "imported"}]
    manager._resolve_api_fn = lambda _name: lambda *_args, **_kwargs: type("Response", (), {"data": {}})()

    manager._create_and_record(
        {"key": "networks", "create_fn": "create"},
        {"name": "Second"},
        "Second",
        "source-second",
        results,
    )

    assert results[0] == {"type": "networks", "name": "First", "status": "imported"}
    assert results[1]["status"] == "failed"
    assert manager._remap_table == {}


def test_missing_address_is_reported_as_a_comparison_conflict() -> None:
    """Carry a missing primary address through comparison into the conflict report."""
    comparator = InventoryCSVComparator.__new__(InventoryCSVComparator)
    comparator._address_utils = AddressUtils
    comparator.address_threshold = 70.0
    comparator.debug = False
    comparator.comparison_address_lookup = {
        "serial-1": {
            "Address": "123 Main St",
            "City": "Springfield",
            "State": "IL",
            "Zip": "62701",
        }
    }
    comparator.counters = SimpleNamespace(mismatches_found=0, perfect_matches=0)
    comparator.all_conflicts = []
    device = {
        "street": "",
        "city": "Springfield",
        "state": "IL",
        "zip_code": "62701",
    }

    comparator._compare_and_record(device, "serial-1", "Switch 1")

    assert comparator.counters.mismatches_found == 1
    assert len(comparator.all_conflicts) == 1
    conflict = comparator.all_conflicts[0]
    assert conflict["mist_address"]["address"] == ""
    assert conflict["comparison_address"]["address"] == "123 Main St"
    assert conflict["comparison_result"]["is_match"] is False
    assert conflict["comparison_result"]["overall_similarity"] == 0.0
