"""Prove full writable projection, explicit exclusions, and fail-closed deletion."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.operations.execution.firmware_policy.recovery.schema import RestoreSchema
from src.operations.execution.firmware_policy.sdk import PolicyError
from tests.unit.firmware_policy.fakes import ORG_ID


def test_complete_writable_body_excludes_server_managed_fields() -> None:
    """Restore unrelated saved settings while excluding documented response metadata."""
    schema = RestoreSchema()
    body, excluded = schema.body(
        "org", {"org_id": ORG_ID, "modified_time": 1, "allow_mist": True}, {"allow_mist": False}
    )
    assert body == {"allow_mist": True}
    assert excluded == ["modified_time", "org_id"]


@pytest.mark.parametrize(
    "settings",
    [
        {"unknown": "private-fixture"},
        {"allow_mist": "yes"},
        {"ssr": {"conductor_token": "********"}},
        {"auto_upgrade": {"unknown": True}},
        {"auto_upgrade": {"enabled": None}},
        {"ssr": {"conductor_token": "<redacted>"}},
    ],
)
def test_unproven_or_invalid_fields_fail_before_writes(settings: dict[str, Any]) -> None:
    """Do not silently omit unknown fields, invalid values, or secret placeholders."""
    with pytest.raises(PolicyError) as error:
        RestoreSchema().project("org", settings)
    assert "private-fixture" not in str(error.value)


def test_absent_site_policy_uses_proven_inheritance_deletion() -> None:
    """An absent AP policy must restore inheritance rather than disable a local policy."""
    body, _ = RestoreSchema().body("site", {"dns_servers": ["8.8.8.8"]}, {"auto_upgrade": {"enabled": True}})
    assert body == {"dns_servers": ["8.8.8.8"], "-auto_upgrade": ""}


@pytest.mark.parametrize("scope,field,value", [("org", "allow_mist", True), ("site", "dns_servers", ["1.1.1.1"])])
def test_unproven_absent_field_deletion_stops(scope: str, field: str, value: Any) -> None:
    """Missing fields cannot silently survive a claimed complete restoration."""
    with pytest.raises(PolicyError, match="no proven deletion"):
        RestoreSchema().body(scope, {}, {field: value})


def test_readback_compares_complete_writable_state() -> None:
    """A later unexpected writable field or incorrect value must fail verification."""
    schema = RestoreSchema()
    schema.verify("org", {"org_id": ORG_ID, "modified_time": 2, "allow_mist": True}, {"allow_mist": True})
    with pytest.raises(PolicyError, match="verification failed"):
        schema.verify("org", {"allow_mist": True, "disable_pcap": True}, {"allow_mist": True})


@pytest.mark.parametrize("content", [b"", b"bad json"])
def test_empty_or_malformed_local_schema_fails_explicitly(monkeypatch: Any, content: bytes) -> None:
    """Missing readable schema evidence cannot enable an unchecked restoration."""
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
