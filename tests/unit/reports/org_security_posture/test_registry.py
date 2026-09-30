"""Tests for the stable check registry."""

import pytest

from src.reports.org_security_posture.checks.registry import OrgSecurityPostureCheckRegistry


def test_registry_has_stable_order_and_minimum_size() -> None:
    checks = OrgSecurityPostureCheckRegistry.checks()  # Load the production registry.
    check_ids = [check.check_id for check in checks]  # Read stable IDs in CSV order.
    assert len(check_ids) >= 12  # The contract requires at least twelve checks.
    assert check_ids[:3] == ["ORGSEC-PASSWORD-001", "ORGSEC-PASSWORD-002", "ORGSEC-PASSWORD-003"]  # Order is stable.


def test_registry_rejects_duplicate_check_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    class DuplicateCheck:
        check_id = "ORGSEC-DUPLICATE-001"  # Duplicate ID used to prove registry validation.

    monkeypatch.setattr(
        OrgSecurityPostureCheckRegistry, "CHECK_CLASSES", (DuplicateCheck, DuplicateCheck)
    )  # Force duplicate.
    with pytest.raises(ValueError):  # Duplicate stable IDs must fail before export.
        OrgSecurityPostureCheckRegistry.checks()
