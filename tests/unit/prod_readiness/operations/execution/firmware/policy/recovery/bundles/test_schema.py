"""Prove policy-only restoration, explicit defaults, and unrelated current state preservation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.operations.execution.firmware_policy.recovery.schema import RestoreSchema
from src.operations.execution.firmware_policy.sdk import PolicyError
from tests.unit.prod_readiness.operations.execution.firmware.policy.fakes import ORG_ID


def test_policy_projection_ignores_unknown_readonly_and_null_nonpolicy_values() -> None:
    """Unsupported unrelated settings remain private backup data, not restoration input."""
    settings = {
        "org_id": ORG_ID,
        "unknown": "private-fixture",
        "uwb_config": {"port": None},
        "engagement": {"hours": {"mon": None}},
        "mist_nac": {"idps": [{"id": ORG_ID}]},
        "auto_upgrade": {"enabled": False, "day_of_week": "sun", "time_of_day": "03:00"},
        "ssr": {"conductor_token": "<redacted>", "auto_upgrade": {"enabled": True, "version": "historical"}},
    }
    body, notices = RestoreSchema().project("org", settings)
    assert body == {
        "auto_upgrade": settings["auto_upgrade"],
        "ssr": {"auto_upgrade": {"enabled": True, "version": "historical"}},
    }
    assert notices == ["outside_firmware_policy_scope"]
    assert "private-fixture" not in str(notices)


@pytest.mark.parametrize(
    "policy",
    [
        None,
        [],
        {"unknown": True},
        {"enabled": None},
        {"enabled": "yes"},
        {"custom_versions": {"AP41": "<redacted>"}},
        {"time_of_day": "25:00"},
        {"day_of_week": None},
        {"day_of_week": "Sunday"},
        {"time_of_day": None},
    ],
)
def test_invalid_unknown_and_redacted_policy_fields_fail_before_writes(policy: Any) -> None:
    """A narrow restoration scope still validates every selected policy value."""
    with pytest.raises(PolicyError):
        RestoreSchema().project("site", {"auto_upgrade": policy})


@pytest.mark.parametrize("kind", ["switch", "ssr", "juniper_srx"])
@pytest.mark.parametrize("policy", [{"unknown": True}, {"enabled": "yes"}, {"custom_versions": {"MODEL": "********"}}])
def test_hardware_policy_rejects_unknown_invalid_and_redacted_values(kind: str, policy: Any) -> None:
    """Hardware policies retain strict schema and placeholder checks without a catalog lookup."""
    with pytest.raises(PolicyError):
        RestoreSchema().project("org", {kind: {"auto_upgrade": policy}})


@pytest.mark.parametrize("schedule", [{}, {"day_of_week": "", "time_of_day": ""}])
def test_menu168_ap_defaults_are_reported_without_changing_the_backup(schedule: dict[str, str]) -> None:
    """Missing or empty schedules use the explicitly selected menu 168 defaults."""
    original = {"enabled": False, **schedule}
    body, notices = RestoreSchema().project("org", {"auto_upgrade": original})
    assert body == {"auto_upgrade": {"enabled": False, "day_of_week": "any", "time_of_day": "02:00"}}
    assert notices == [
        "outside_firmware_policy_scope",
        "normalized:auto_upgrade.day_of_week=any",
        "normalized:auto_upgrade.time_of_day=02:00",
    ]
    assert original == {"enabled": False, **schedule}


def test_valid_any_day_and_time_are_preserved_without_default_notices() -> None:
    """Fresh AP schedules retain an explicit any time instead of using the legacy default."""
    policy = {"enabled": True, "day_of_week": "any", "time_of_day": "any"}
    body, notices = RestoreSchema().project("org", {"auto_upgrade": policy})
    assert body == {"auto_upgrade": policy}
    assert notices == ["outside_firmware_policy_scope"]


@pytest.mark.parametrize("saved", [{}, {"ssr": {}}])
@pytest.mark.parametrize("current", [{}, {"ssr": {}}])
def test_absent_and_empty_nested_parents_do_not_create_effective_policy(
    saved: dict[str, Any], current: dict[str, Any]
) -> None:
    """A policy-free parent needs no request and cannot invent a local disabled policy."""
    body, notices = RestoreSchema().body("site", saved, current)
    assert body == {}
    assert notices == ["outside_firmware_policy_scope"]
    RestoreSchema().verify("site", current, body, current)


def test_nested_policy_replacement_preserves_current_not_historical_siblings() -> None:
    """Parent replacement carries current siblings while restoring only the saved policy."""
    schema = RestoreSchema()
    saved = {
        "ssr": {"conductor_token": "historical", "auto_upgrade": {"enabled": False, "version": "historical"}},
        "allow_mist": True,
    }
    current = {
        "ssr": {"conductor_token": "current", "unknown": None, "auto_upgrade": {"enabled": True}},
        "allow_mist": False,
    }
    body, _ = schema.body("org", saved, current)
    assert body == {
        "ssr": {
            "conductor_token": "current",
            "unknown": None,
            "auto_upgrade": {"enabled": False, "version": "historical"},
        }
    }
    assert saved["ssr"]["conductor_token"] == "historical"
    assert current["ssr"]["auto_upgrade"] == {"enabled": True}


def test_absent_site_ap_and_nested_policies_use_proven_deletion_contracts() -> None:
    """AP unset and complete current-parent replacement remove overrides without disabling them."""
    body, _ = RestoreSchema().body(
        "site",
        {"dns_servers": ["old"]},
        {
            "auto_upgrade": {"enabled": True},
            "switch": {"networks": {"current": None}, "auto_upgrade": {"enabled": True}},
            "ssr": {"conductor_token": "current", "auto_upgrade": {"enabled": True}},
            "juniper_srx": {"gateways": [], "auto_upgrade": {"enabled": True}},
        },
    )
    assert body == {
        "-auto_upgrade": "",
        "switch": {"networks": {"current": None}},
        "ssr": {"conductor_token": "current"},
        "juniper_srx": {"gateways": []},
    }


def test_absent_org_ap_policy_has_no_proven_unset_contract() -> None:
    """A missing organization AP policy cannot become an invented disabled policy."""
    with pytest.raises(PolicyError, match="no proven deletion contract"):
        RestoreSchema().body("org", {}, {"auto_upgrade": {"enabled": True}})


def test_readback_preserves_all_current_nonpolicy_fields_except_modified_time() -> None:
    """An unrelated server change fails even when every requested policy persists."""
    schema = RestoreSchema()
    original = {"org_id": ORG_ID, "modified_time": 1, "unknown": None, "allow_mist": False}
    body = {"ssr": {"auto_upgrade": {"enabled": True, "version": "historical"}}}
    saved = {**original, **body, "modified_time": 2}
    schema.verify("org", saved, body, original)
    with pytest.raises(PolicyError, match="verification failed"):
        schema.verify("org", {**saved, "allow_mist": True}, body, original)
    with pytest.raises(PolicyError, match="verification failed"):
        schema.verify("org", {**saved, "new_unrelated_field": None}, body, original)


@pytest.mark.parametrize("content", [b"", b"bad json"])
def test_empty_or_malformed_local_schema_fails_explicitly(monkeypatch: Any, content: bytes) -> None:
    """Missing schema evidence cannot permit an unchecked policy restoration."""
    read_text = Path.read_text
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda path, *args, **kwargs: (
            content.decode() if path.name == "mist-api-openapi31json.json" else read_text(path, *args, **kwargs)
        ),
    )
    with pytest.raises(PolicyError, match="schemas could not be read"):
        RestoreSchema()


def test_policy_projection_needs_only_packaged_authoritative_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    """A candidate image needs no legacy documentation file for scoped policy restoration."""
    reads: list[str] = []
    read_text = Path.read_text

    def authoritative_only(path: Path, *args: Any, **kwargs: Any) -> str:
        """Reject every schema read except the packaged authoritative document."""
        assert path.name == "mist-api-openapi31json.json"
        reads.append(path.name)
        return read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", authoritative_only)
    settings = {"switch": {"auto_upgrade": {"enabled": True, "snapshot": False}}}
    assert RestoreSchema().project("org", settings) == (settings, ["outside_firmware_policy_scope"])
    assert reads == ["mist-api-openapi31json.json"]
