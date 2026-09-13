"""Prove the E2E isolation values, stores, traps, and resources."""

from __future__ import annotations  # Keep annotations independent from import order.

import shutil  # Remove the test-owned artifact root after allocation.
from collections.abc import Callable  # Type one deliberate missing callable value.
from pathlib import Path  # Build an approved repository data path.
from typing import Any, cast  # Type traps and one deliberate invalid runtime value.
from uuid import uuid4  # Keep parallel unit test artifact roots distinct.

import pytest  # Check the fail-closed exceptions.

from src.upgrade_portal.api.run_controls import (  # Import the explicit factory value groups.
    E2EActionOverrides,
    E2EExternalOverrides,
    E2EFactoryOverrides,
    E2ERecordOverrides,
    E2ESecurityOverrides,
)
from tests.support.upgrade_portal_e2e import (  # Import process stores, traps, and resource controls.
    ActionRecordStore,
    ArangoConnectorTrap,
    AuditRecordStore,
    MistConnectorTrap,
    PortalFileTrap,
    PortalRecordStore,
    RedisConnectorTrap,
    ScriptedCloudStore,
    allocate_resources,
    build_child_environment,
)

TRAP_CASES = (  # Pair each trap with the exact isolation contract message.
    (ArangoConnectorTrap, "E2E isolation failed: an ArangoDB connector was called."),
    (RedisConnectorTrap, "E2E isolation failed: a Redis connector was called."),
    (MistConnectorTrap, "E2E isolation failed: a Mist cloud connector was called."),
    (PortalFileTrap, "E2E isolation failed: a portal record file was opened."),
)


def _callable(*_arguments: object, **_options: object) -> object:  # Provide one harmless callable seam.
    """Return one harmless stand-in result."""
    return {}  # The isolation tests inspect construction, not route behavior.


def _overrides(test_run_id: str = "e2e-unit-owner") -> E2EFactoryOverrides:  # Build one complete test value.
    """Build one complete override value for validation tests."""
    portal = PortalRecordStore(test_run_id)  # Own run, capture, lock, and access records.
    actions = ActionRecordStore(test_run_id)  # Own action records.
    audits = AuditRecordStore(test_run_id)  # Own audit records.
    cloud = ScriptedCloudStore(test_run_id)  # Own scripted cloud evidence.
    records = E2ERecordOverrides(  # Bind all run and capture seams.
        portal, portal, _callable, portal.load_capture, portal.list_captures, portal.list_runs
    )
    action_values = E2EActionOverrides(  # Bind all action and upgrade seams.
        actions, _callable, _callable, _callable, _callable, _callable, portal
    )
    security = E2ESecurityOverrides(  # Bind all access and audit seams.
        portal, _callable, portal, portal.authorization, audits, audits.list
    )
    external = E2EExternalOverrides(  # Bind all cloud, connector, and file seams.
        cloud,
        cloud.read,
        _callable,
        MistConnectorTrap(),
        ArangoConnectorTrap(),
        RedisConnectorTrap(),
        PortalFileTrap(),
    )
    return E2EFactoryOverrides(test_run_id, records, action_values, security, external)  # Complete value.


def test_complete_overrides_validate_and_publish_every_seam() -> None:  # Prove complete installation data.
    """A complete override value validates and publishes every boundary."""
    overrides = _overrides()  # Build every required process-owned dependency.
    overrides.validate()  # A complete value must not raise.
    values = overrides.config_values()  # Read the map that wiring installs.
    assert values["RUN_STORE"] is overrides.records.run_store  # Run storage has no fallback.
    assert values["RUN_ACTION_STORE"] is overrides.actions.action_store  # Action storage has no fallback.
    assert values["PORTAL_RECORD_FILE_OPENER"] is overrides.external.file_opener  # File access is trapped.


def test_missing_override_fails_closed() -> None:  # Prove missing dependency validation.
    """A missing connector fails validation before application construction."""
    overrides = _overrides()  # Start from a complete immutable value.
    broken_external = E2EExternalOverrides(  # Replace one required connector with an invalid value.
        overrides.external.cloud_evidence,
        overrides.external.cloud_reader,
        overrides.external.device_reader,
        overrides.external.mist_connector,
        cast(Callable[..., object], None),  # A deliberate invalid value proves runtime validation.
        overrides.external.redis_connector,
        overrides.external.file_opener,
    )
    broken = E2EFactoryOverrides(  # Keep every other required group valid.
        overrides.test_run_id,
        overrides.records,
        overrides.actions,
        overrides.security,
        broken_external,
    )
    with pytest.raises(ValueError, match="external.arango_connector"):  # Name the exact missing seam.
        broken.validate()  # Construction must fail closed.


@pytest.mark.parametrize(("trap_type", "message"), TRAP_CASES)
def test_each_trap_records_and_fails_with_the_contract_message(  # Prove one trap contract.
    trap_type: type[object], message: str
) -> None:
    """Each isolation trap records the call and raises the exact contract text."""
    trap: Any = trap_type()  # Build one empty trap with the shared call-record shape.
    with pytest.raises(AssertionError, match=f"^{message.replace('.', '[.]')}$"):  # Match the full contract text.
        trap()  # Any call must fail before an external operation.
    assert trap.calls == ["open" if trap_type is PortalFileTrap else "connect"]  # Record one safe name.


def test_child_environment_scrubs_credentials_paths_and_uses_sentinels() -> None:  # Prove child isolation.
    """The child environment contains no parent credential or persistent output path."""
    parent = {  # Use unique values so a copied production value is visible.
        "ARANGO_DATABASE": "production-database",
        "ARANGO_USERNAME": "production-user",
        "ARANGO_ROOT_PASSWORD": "production-password",
        "REDIS_PASSWORD": "production-redis-password",
        "MIST_APITOKEN": "production-mist-token",
        "MIST_API_TOKEN": "production-mist-token-two",
        "OUTPUT_FORMAT": "sqlite",
        "DATABASE_PATH": "production.db",
        "PORTAL_BACKUP_PATH": "production-backup",
        "PORTAL_EXPORT_PATH": "production-export",
        "PATH": "test-path",
    }
    child = build_child_environment(parent)  # Scrub before a child process starts.
    assert child["ARANGO_HOST"] == "http://127.0.0.1:1"  # Use the required document store sentinel.
    assert child["REDIS_HOST"] == "127.0.0.1"  # Use the required lock store host sentinel.
    assert child["REDIS_PORT"] == "1"  # Use the required lock store port sentinel.
    assert child["PATH"] == "test-path"  # Preserve noncredential process settings.
    assert not any(value.startswith("production") for value in child.values())  # Leak no production value.


def test_resource_allocation_uses_unique_ports_paths_and_identifiers() -> None:  # Prove unique resources.
    """Two allocations share no server resource."""
    root = Path.cwd() / "data" / "test-artifacts" / f"unit-{uuid4().hex}"  # Use approved repository output.
    first = allocate_resources(root)  # Allocate the first isolated server resources.
    second = allocate_resources(root)  # Allocate the second isolated server resources.
    try:  # Release both reservations and remove only this test-owned root.
        assert first.test_run_id != second.test_run_id  # Give each record graph a different owner.
        assert first.port != second.port  # Give each child a different loopback port.
        assert first.artifact_directory != second.artifact_directory  # Separate every server artifact.
        assert first.log_path != second.log_path  # Separate every server log.
        assert first.process_owner_path != second.process_owner_path  # Separate every process owner file.
    finally:  # A failed assertion must not leave a reserved socket or an artifact directory.
        first.release_port()  # Release the first loopback reservation.
        second.release_port()  # Release the second loopback reservation.
        shutil.rmtree(root, ignore_errors=True)  # Remove only the unique unit test artifact root.


def test_each_record_store_rejects_a_different_owner() -> None:  # Prove record ownership enforcement.
    """Every process-owned store rejects a record from another E2E run."""
    portal = PortalRecordStore("owner-a")  # Own portal records for one E2E run.
    actions = ActionRecordStore("owner-a")  # Own action records for the same E2E run.
    audits = AuditRecordStore("owner-a")  # Own audit records for the same E2E run.
    cloud = ScriptedCloudStore("owner-a")  # Own cloud scripts for the same E2E run.
    with pytest.raises(ValueError, match="different E2E test run"):  # Reject a foreign run record.
        portal.write_run({"run_id": "run-a", "test_run_id": "owner-b"})  # Supply the wrong owner.
    with pytest.raises(ValueError, match="different E2E test run"):  # Reject a foreign action record.
        actions.write({"action_id": "action-a", "test_run_id": "owner-b"})  # Supply the wrong owner.
    with pytest.raises(ValueError, match="different E2E test run"):  # Reject a foreign audit record.
        audits.append({"event": "read", "test_run_id": "owner-b"})  # Supply the wrong owner.
    with pytest.raises(ValueError, match="different E2E test run"):  # Reject a foreign cloud script.
        cloud.write("evidence", {"value": [], "test_run_id": "owner-b"})  # Supply the wrong owner.
