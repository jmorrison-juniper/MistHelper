"""Define the test-only dependency values for the run control factory.

Why:
    A browser test must provide every external dependency before the factory
    registers a route. These immutable values make that dependency set explicit.
"""

from __future__ import annotations  # Keep each annotation independent from import order.

import logging  # Record validation without exposing a dependency value.
from collections.abc import Callable, Mapping  # Describe callable seams and the Flask configuration map.
from dataclasses import dataclass, fields  # Build immutable values and inspect required fields.
from typing import Any  # External stand-ins can use different concrete result types.

logger = logging.getLogger(__name__)  # Keep validation records tied to this module.


@dataclass(frozen=True, slots=True)
class E2ERecordOverrides:  # Group every process-owned run and capture seam.
    """Hold the process-owned run and capture record seams."""

    run_store: object  # Keep run records inside the E2E process.
    capture_store: object  # Keep capture records inside the E2E process.
    capture_runner: Callable[..., Any]  # Complete a capture without a cloud call.
    capture_loader: Callable[..., Any]  # Read one process-owned capture.
    capture_lister: Callable[..., Any]  # List process-owned capture rows.
    run_lister: Callable[..., Any]  # List process-owned run rows.

    def config_values(self) -> Mapping[str, object]:  # Map record values to existing route keys.
        """Return the Flask values for run and capture records."""
        return {  # Use existing route keys so process-owned records always win.
            "RUN_STORE": self.run_store,  # Route all run reads and writes to process memory.
            "CAPTURE_STORE": self.capture_store,  # Keep capture writes inside the same process.
            "CAPTURE_RUNNER": self.capture_runner,  # Keep capture work away from the cloud.
            "CAPTURE_LOADER": self.capture_loader,  # Read captures from the owned record graph.
            "CAPTURE_LISTER": self.capture_lister,  # List captures from the owned record graph.
            "RUN_LISTER": self.run_lister,  # List runs from the owned record graph.
        }


@dataclass(frozen=True, slots=True)
class E2EActionOverrides:  # Group every action and upgrade execution seam.
    """Hold action records and each route action that can cause external work."""

    action_store: object  # Keep action records inside the E2E process.
    run_launcher: Callable[..., Any]  # Replace the production firmware launcher.
    stop_runner: Callable[..., Any]  # Replace the production cloud stop worker.
    options_builder: Callable[..., Any]  # Build options from process-owned inventory.
    options_view: Callable[..., Any]  # Read process-owned option choices.
    versions_reader: Callable[..., Any]  # Read process-owned version choices.
    precheck_adopter: object  # Link a process-owned pre-check without storage fallback.

    def config_values(self) -> Mapping[str, object]:  # Map action values to existing route keys.
        """Return the Flask values for action and upgrade work."""
        return {  # Bind every mutation path to an explicit E2E dependency.
            "RUN_ACTION_STORE": self.action_store,  # Keep action records process-owned.
            "RUN_LAUNCHER": self.run_launcher,  # Prevent a production firmware launch.
            "STOP_RUNNER": self.stop_runner,  # Prevent a production cloud stop.
            "UPGRADE_OPTIONS_BUILDER": self.options_builder,  # Build options from stand-in data.
            "UPGRADE_OPTIONS_VIEW": self.options_view,  # Render options from stand-in data.
            "UPGRADE_VERSIONS": self.versions_reader,  # Return stand-in firmware versions.
            "PRECHECK_ADOPTER": self.precheck_adopter,  # Keep pre-check links process-owned.
        }


@dataclass(frozen=True, slots=True)
class E2ESecurityOverrides:  # Group every access, lock, and audit seam.
    """Hold access, lock, authorization, and audit seams."""

    access_store: object  # Keep access decisions inside the E2E process.
    lock_reader: Callable[..., Any]  # Read process-owned site locks.
    lock_client: object  # Write process-owned site locks without Redis.
    authorization_reader: Callable[..., Any]  # Read process-owned authorization decisions.
    audit_store: object  # Keep audit records inside the E2E process.
    audit_reader: Callable[..., Any]  # List process-owned audit records.

    def config_values(self) -> Mapping[str, object]:  # Map security values to existing route keys.
        """Return the Flask values for access, lock, and audit work."""
        return {  # Bind every security record to one process-owned store.
            "E2E_ACCESS_STORE": self.access_store,  # Expose the owned access record store.
            "SITE_LOCK_READER": self.lock_reader,  # Read locks without a Redis connection.
            "LOCK_STORE_CLIENT": self.lock_client,  # Write locks without a Redis connection.
            "AUTHORIZATION_READER": self.authorization_reader,  # Read owned access decisions.
            "E2E_AUDIT_STORE": self.audit_store,  # Expose the owned audit record store.
            "AUDIT_READER": self.audit_reader,  # Read audit rows without a record file.
        }


@dataclass(frozen=True, slots=True)
class E2EExternalOverrides:  # Group every cloud, connector, and file boundary.
    """Hold cloud, connector, and portal record file seams."""

    cloud_evidence: object  # Keep reconciliation evidence inside the E2E process.
    cloud_reader: Callable[..., Any]  # Read scripted cloud rows without Mist.
    device_reader: Callable[..., Any]  # Read scripted devices without Mist.
    mist_connector: Callable[..., Any]  # Fail if code constructs a Mist connector.
    arango_connector: Callable[..., Any]  # Fail if code constructs an ArangoDB connector.
    redis_connector: Callable[..., Any]  # Fail if code constructs a Redis connector.
    file_opener: Callable[..., Any]  # Fail if code opens a portal record file.

    def config_values(self) -> Mapping[str, object]:  # Map external values to existing route keys.
        """Return the Flask values for cloud, connector, and file boundaries."""
        return {  # Bind every external boundary before a blueprint registers.
            "CLOUD_EVIDENCE": self.cloud_evidence,  # Read scripted reconciliation evidence.
            "MIST_READER": self.cloud_reader,  # Read scripted cloud lists.
            "DEVICE_READER": self.device_reader,  # Read scripted device lists.
            "MIST_CONNECTOR": self.mist_connector,  # Trap unexpected Mist construction.
            "ARANGO_CONNECTOR": self.arango_connector,  # Trap unexpected ArangoDB construction.
            "REDIS_CONNECTOR": self.redis_connector,  # Trap unexpected Redis construction.
            "PORTAL_RECORD_FILE_OPENER": self.file_opener,  # Trap portal record file access.
        }


@dataclass(frozen=True, slots=True)
class E2EFactoryOverrides:  # Hold one complete fail-closed E2E dependency value.
    """Hold every dependency that an isolated E2E application requires."""

    test_run_id: str  # Identify one isolated server in each response.
    records: E2ERecordOverrides  # Supply all run and capture record seams.
    actions: E2EActionOverrides  # Supply all mutation and action record seams.
    security: E2ESecurityOverrides  # Supply all access and audit seams.
    external: E2EExternalOverrides  # Supply all cloud, connector, and file seams.

    def validate(self) -> None:  # Verify every required nested value before route registration.
        """Reject an incomplete E2E dependency set before route registration."""
        logging.info("Validate the E2E factory override set")  # Start the fail-closed validation.
        missing = self._missing_values()  # Find every absent nested value before installation.
        if missing:  # An incomplete test application could reach a production fallback.
            joined = ", ".join(missing)  # Give the test a stable list of missing field paths.
            raise ValueError(f"E2E factory overrides are incomplete: {joined}.")  # Stop construction before routes.
        logging.debug("The E2E factory override set contains every required seam")  # Confirm safe construction.

    def _missing_values(self) -> tuple[str, ...]:  # Collect each blank required dependency path.
        """Return each blank required value as a stable dotted field path."""
        missing: list[str] = []  # Preserve field order for a stable failure message.
        for group_field in fields(self):  # Inspect the five explicit top-level values.
            group_value = getattr(self, group_field.name)  # Read one immutable group value.
            missing.extend(self._missing_group(group_field.name, group_value))  # Add each unsafe nested path.
        return tuple(missing)  # An immutable answer stops a caller edit.

    @staticmethod
    def _missing_group(group_name: str, group_value: object) -> tuple[str, ...]:  # Inspect one dependency group.
        """Return the missing paths for one top-level override group."""
        if group_value is None or group_value == "":  # A blank top-level value is never safe.
            return (group_name,)  # Name the exact missing top-level value.
        if not hasattr(group_value, "__dataclass_fields__"):  # The run identifier is plain text.
            return ()  # Only nested override groups need field inspection.
        return E2EFactoryOverrides._missing_fields(group_name, group_value)  # Inspect the nested seam values.

    @staticmethod
    def _missing_fields(group_name: str, group_value: object) -> tuple[str, ...]:  # Inspect nested fields.
        """Return each missing value in one validated dataclass group."""
        return tuple(  # Keep field order so the construction error stays stable.
            f"{group_name}.{value_field.name}"  # Name the exact unsafe nested seam.
            for value_field in fields(group_value)  # Inspect each required seam in the group.
            if getattr(group_value, value_field.name) is None  # None would select a production fallback.
        )

    def config_values(self) -> Mapping[str, object]:  # Build one complete Flask configuration map.
        """Return the Flask configuration values for every required E2E seam."""
        logging.info("Build the E2E seam configuration")  # Start one visible installation action.
        values: dict[str, object] = {}  # Merge four explicit groups into one installation map.
        for group in (self.records, self.actions, self.security, self.external):  # Preserve group order.
            values.update(group.config_values())  # Add one complete dependency group.
        values["E2E_OVERRIDES_ACTIVE"] = True  # Mark this application as isolated.
        values["E2E_TEST_RUN_ID"] = self.test_run_id  # Bind responses to this test process.
        logging.debug("Built %s E2E seam configuration values", len(values))  # Report a safe count only.
        return values  # The wiring installs this complete map before blueprints.
