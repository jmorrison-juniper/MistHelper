"""Prove firmware-only field projection, explicit absence, and immutable proposals."""

from copy import deepcopy
from typing import Any

import pytest

from src.operations.execution.firmware_policy.sdk import PolicyError
from web_portal.routes.firmware_policy.restore.policies import PolicyCells, PolicyComparison


def test_saved_raw_defaults_and_proposed_normalization_are_distinct() -> None:
    """Preserve saved schedule absence instead of presenting invented historical values."""
    saved = {"auto_upgrade": {"enabled": False}, "ssr": {"conductor_token": "private-fixture"}}
    proposed = {"auto_upgrade": {"enabled": False, "day_of_week": "any", "time_of_day": "02:00"}}
    original = deepcopy(saved)
    result = PolicyComparison.build("site", {"saved": saved, "current": saved, "proposed": proposed})
    rows = {row["path"]: row for row in result["fields"]}
    assert rows["auto_upgrade.day_of_week"]["cells"]["saved"] == {"present": False}
    assert rows["auto_upgrade.day_of_week"]["proposed_changed"] is True
    assert rows["auto_upgrade.enabled"]["cells"]["saved"]["value"] is False
    assert rows["ssr.auto_upgrade.state"]["cells"]["saved"]["value"] == "Inherited from organization"
    assert "private-fixture" not in str(result)
    assert "conductor_token" not in str(result)
    assert saved == original


@pytest.mark.parametrize(
    ("scope", "policy", "expected"),
    [
        ("org", None, "Missing organization policy"),
        ("site", None, "Inherited from organization"),
        ("site", {}, "Empty policy"),
        ("site", {"enabled": False}, "Disabled"),
        ("site", {"version": "stable"}, "Enablement not specified"),
        ("org", {"enabled": True}, "Enabled"),
    ],
)
def test_presence_state_is_not_a_boolean_default(scope: str, policy: Any, expected: str) -> None:
    """Treat missing, empty, disabled, and unspecified states as different facts."""
    settings = {} if policy is None else {"auto_upgrade": policy}
    result = PolicyCells.project(scope, settings)
    assert result["auto_upgrade.state"] == {"present": True, "value": expected}


@pytest.mark.parametrize("value", [{"unknown_private": "private-fixture"}, {"enabled": "false"}, {"version": "***"}])
def test_unproven_or_masked_policy_values_fail_without_disclosure(value: dict[str, Any]) -> None:
    """Reject unsafe shapes before any comparison can expose their values."""
    with pytest.raises(PolicyError) as failure:
        PolicyCells.project("org", {"auto_upgrade": value})
    assert "private-fixture" not in str(failure.value)


def test_exact_deletion_and_parent_replacement_preserve_source() -> None:
    """Show proposed inheritance without mutating private complete snapshots."""
    saved = {"auto_upgrade": {"enabled": False}, "switch": {"auto_upgrade": {"enabled": False}, "private": 7}}
    original = deepcopy(saved)
    result = PolicyComparison.effect(saved, {"-auto_upgrade": "", "switch": {"private": 7}})
    assert "auto_upgrade" not in result
    assert result["switch"] == {"private": 7}
    assert saved == original
