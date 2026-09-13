"""Define the test-only dependency values for the run control factory.

Why:
    A browser test must provide every external dependency before the factory
    registers a route. These immutable values make that dependency set explicit.
"""

from __future__ import annotations  # Keep each annotation independent from import order.

import logging  # Record validation without exposing a dependency value.
from collections.abc import Callable, Mapping  # Describe seams, records, and ordered identifiers.
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

    def trap_call_counts(self) -> Mapping[str, int]:  # Report all external boundary calls for one response.
        """Return the safe call count for each E2E connector and file trap."""
        return {  # Each value contains a safe count and no connector argument.
            "arango": len(getattr(self.external.arango_connector, "calls", ())),
            "redis": len(getattr(self.external.redis_connector, "calls", ())),
            "mist": len(getattr(self.external.mist_connector, "calls", ())),
            "files": len(getattr(self.external.file_opener, "calls", ())),
        }


@dataclass(frozen=True, slots=True)
class BulkPreviewRequest:  # Hold one validated request for an authoritative preview.
    """Hold the requested action, scope, and ordered run identifiers."""

    action: str  # Accept only the two bulk actions from the HTTP contract.
    organization_id: str  # Bind visibility to the selected organization.
    history_scope: str  # Bind visibility to the active history filter.
    run_ids: tuple[str, ...]  # Preserve the browser order without permitting edits.

    @classmethod
    def from_mapping(cls, body: Mapping[str, Any]) -> BulkPreviewRequest:  # Validate untrusted JSON once.
        """Build one request from a JSON object."""
        logger.info("Validate one bulk preview request")  # Record validation before reading fields.
        action = body.get("action")  # Read the action without coercing an unsupported type.
        organization_id = body.get("organization_id")  # Read the organization scope as supplied.
        history_scope = body.get("history_scope")  # Read the server-defined history scope.
        raw_run_ids = body.get("run_ids")  # Read the ordered candidate list without changing it.
        cls._validate_fields(action, organization_id, history_scope, raw_run_ids)  # Refuse an invalid shape.
        run_ids = tuple(raw_run_ids)  # Freeze the validated list and preserve its order.
        if len(set(run_ids)) != len(run_ids):  # A duplicate can hide an unintended second action.
            raise ValueError("duplicate_run_id")  # Keep the HTTP error mapping stable.
        if not 1 <= len(run_ids) <= 50:  # The contract bounds one request to a safe batch size.
            raise ValueError("batch_size_invalid")  # Keep the HTTP error mapping stable.
        logger.debug("Validated one bulk preview request with %s run(s)", len(run_ids))  # Report a safe count.
        return cls(action, organization_id, history_scope, run_ids)  # Return one immutable request.

    @staticmethod
    def _validate_fields(action: Any, organization_id: Any, history_scope: Any, run_ids: Any) -> None:
        """Reject a request field with an unsupported type or value."""
        if action not in {"cancel", "retry"}:  # No other action can use the bulk preview endpoint.
            raise ValueError("invalid_request")  # Give the route one stable request error.
        if not isinstance(organization_id, str) or not organization_id.strip():  # Require one organization.
            raise ValueError("invalid_request")  # Refuse a missing or non-text scope.
        if not isinstance(history_scope, str) or not history_scope.strip():  # Require one visible history scope.
            raise ValueError("invalid_request")  # Refuse a missing or non-text scope.
        if not isinstance(run_ids, list) or any(not isinstance(value, str) or not value for value in run_ids):
            raise ValueError("invalid_request")  # Refuse a non-list or a blank identifier.


@dataclass(frozen=True, slots=True)
class PreviewScope:  # Bind one preview to its durable actor and visible scope.
    """Hold the actor, organization, history scope, and action."""

    actor_scope: str  # Store only the durable actor digest.
    organization_id: str  # Store the current selected organization.
    history_scope: str  # Store the current server-defined history filter.
    action: str  # Store cancel or retry.


@dataclass(frozen=True, slots=True)
class PreviewSelection:  # Hold the authoritative retained and removed identifiers.
    """Hold the ordered selection and its exact per-site counts."""

    run_ids: tuple[str, ...]  # Keep visible identifiers in the requested order.
    removed_run_ids: tuple[str, ...]  # Name each candidate that the server removed.
    site_counts: Mapping[str, int]  # Give the phrase dialog exact server counts.


@dataclass(frozen=True, slots=True)
class BulkActionPreview:  # Return one signed authoritative preview to the route.
    """Hold one preview identifier, scope, selection, expiry, and signed token."""

    preview_id: str  # Give the action request one opaque preview reference.
    scope: PreviewScope  # Keep actor and visible scope values cohesive.
    selection: PreviewSelection  # Keep retained identifiers and counts cohesive.
    expires_at: str  # State the UTC expiry that the signed token also contains.
    preview_token: str  # Bind every preview field with the application secret.

    def to_mapping(self) -> dict[str, Any]:  # Build the exact public HTTP response.
        """Return the public preview response without the actor scope."""
        run_count = len(self.selection.run_ids)  # Derive the count from the authoritative ordered list.
        return {  # Publish only the fields that the HTTP contract permits.
            "preview_id": self.preview_id,  # Correlate the later action without exposing identity.
            "action": self.scope.action,  # Tell the browser which phrase rule applies.
            "run_ids": list(self.selection.run_ids),  # Replace hidden browser state with this list.
            "removed_run_ids": list(self.selection.removed_run_ids),  # Explain each removed candidate.
            "run_count": run_count,  # Supply the exact phrase count.
            "site_count": len(self.selection.site_counts),  # Supply the exact site count.
            "site_counts": dict(self.selection.site_counts),  # Supply each site count.
            "confirmation": f"{self.scope.action.upper()} {run_count} RUNS",  # Supply the exact phrase.
            "preview_token": self.preview_token,  # Bind the action request to this preview.
            "expires_at": self.expires_at,  # Let the browser state when the preview expires.
        }
