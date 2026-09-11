"""Publish and assemble the isolated upgrade portal E2E support surface."""

from __future__ import annotations  # Keep annotations independent from import order.

import logging  # Record override assembly without record or credential values.
from collections.abc import Mapping  # Accept one named table of E2E stand-in callables.
from functools import partial  # Bind the process-owned lock client to the shipped lock reader.
from typing import Any  # Stand-in callables use different concrete signatures.

from src.upgrade_portal.api.run_controls import (  # Build the explicit factory value groups.
    E2EActionOverrides,
    E2EExternalOverrides,
    E2EFactoryOverrides,
    E2ERecordOverrides,
    E2ESecurityOverrides,
)
from src.upgrade_portal.runtime.lock import read_site_locks  # Parse process-owned locks with shipped rules.

from .environment import build_child_environment as build_child_environment  # Export the credential and path scrub.
from .records import ActionRecordStore, AuditRecordStore, PortalRecordStore, ScriptedCloudStore  # Export stores.
from .resources import E2EResources as E2EResources  # Export the allocated server resource value.
from .resources import allocate_resources as allocate_resources  # Export unique server resource allocation.
from .traps import ArangoConnectorTrap, MistConnectorTrap, PortalFileTrap, RedisConnectorTrap  # Export traps.

logger = logging.getLogger(__name__)  # Keep override assembly records tied to this package.


def _record_values(  # Build the complete run and capture dependency group.
    portal: PortalRecordStore, seams: Mapping[str, Any]
) -> E2ERecordOverrides:
    """Build the process-owned run and capture override group."""
    return E2ERecordOverrides(  # Bind every run and capture route to process-owned records.
        run_store=portal,  # Keep run records inside this E2E process.
        capture_store=portal,  # Keep capture records inside this E2E process.
        capture_runner=seams["capture_runner"],  # Complete captures without a cloud call.
        capture_loader=portal.load_capture,  # Read captures from the owned record graph.
        capture_lister=portal.list_captures,  # List captures from the owned record graph.
        run_lister=portal.list_runs,  # List runs from the owned record graph.
    )


def _action_values(
    actions: ActionRecordStore,
    portal: PortalRecordStore,
    seams: Mapping[str, Any],
) -> E2EActionOverrides:  # Build the complete action dependency group.
    """Build the process-owned action and upgrade override group."""
    return E2EActionOverrides(  # Replace each route action that could reach production.
        action_store=actions,  # Keep action records inside this E2E process.
        run_launcher=seams["run_launcher"],  # Prevent a production firmware launch.
        stop_runner=seams["stop_runner"],  # Prevent a production cloud stop.
        options_builder=seams["options_builder"],  # Build options from stand-in inventory.
        options_view=seams["options_view"],  # Render options from stand-in inventory.
        versions_reader=seams["versions_reader"],  # Return stand-in firmware versions.
        precheck_adopter=portal,  # Link pre-checks inside the owned record graph.
    )


def _security_values(
    portal: PortalRecordStore,
    audits: AuditRecordStore,
    seams: Mapping[str, Any],
) -> E2ESecurityOverrides:  # Build the complete security dependency group.
    """Build the process-owned access and audit override group."""
    return E2ESecurityOverrides(  # Bind access and audit work to process-owned stores.
        access_store=portal,  # Keep access decisions inside this E2E process.
        lock_reader=partial(read_site_locks, client=portal),  # Read the same process-owned locks that routes write.
        lock_client=portal,  # Write locks without a Redis connection.
        authorization_reader=portal.authorization,  # Fail closed from explicit owned decisions.
        audit_store=audits,  # Keep audit rows inside this E2E process.
        audit_reader=audits.list,  # Read audit rows without a record file.
    )


def _external_values(  # Build the complete external dependency group.
    cloud: ScriptedCloudStore, seams: Mapping[str, Any]
) -> E2EExternalOverrides:
    """Build the scripted cloud, connector, and file override group."""
    return E2EExternalOverrides(  # Install every external trap before route registration.
        cloud_evidence=cloud,  # Keep reconciliation evidence inside this E2E process.
        cloud_reader=seams["cloud_reader"],  # Read scripted cloud lists.
        device_reader=seams["device_reader"],  # Read scripted device lists.
        mist_connector=MistConnectorTrap(),  # Fail before Mist connector construction.
        arango_connector=ArangoConnectorTrap(),  # Fail before ArangoDB connector construction.
        redis_connector=RedisConnectorTrap(),  # Fail before Redis connector construction.
        file_opener=PortalFileTrap(),  # Fail before portal record file access.
    )


def build_e2e_overrides(  # Build one complete factory override value.
    test_run_id: str, seams: Mapping[str, Any]
) -> E2EFactoryOverrides:
    """Build the complete process-owned dependency set for one E2E server."""
    logger.info("Build the complete E2E factory override set")  # Record assembly before routes exist.
    portal = PortalRecordStore(test_run_id)  # Own run, capture, lock, and access records.
    actions = ActionRecordStore(test_run_id)  # Own action records.
    audits = AuditRecordStore(test_run_id)  # Own audit records.
    cloud = ScriptedCloudStore(test_run_id)  # Own scripted cloud evidence.
    for capture in seams.get("captures", ()):  # Seed only process-owned capture records.
        portal.write_capture(capture)  # Add the current test owner before storage.
    overrides = E2EFactoryOverrides(  # Join all explicit groups under one validated value.
        test_run_id,
        _record_values(portal, seams),
        _action_values(actions, portal, seams),
        _security_values(portal, audits, seams),
        _external_values(cloud, seams),
    )
    logger.debug("Built the complete E2E factory override set")  # Confirm assembly without record values.
    return overrides  # The factory validates this value before blueprint registration.
