"""Expose preview, cancel, result, and reconciliation routes."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any

from flask import Blueprint, current_app, jsonify, request, session

from src.upgrade_portal.api.run_controls.models import BulkPreviewRequest
from src.upgrade_portal.api.run_controls.services import (
    BulkActionError,
    BulkActionPreviewService,
    BulkRunActionService,
    PreviewError,
    SiteMutationGuard,
    StoppingRunReconciler,
)
from src.upgrade_portal.app.factory import json_error
from src.upgrade_portal.app.routes.select import SELECTED_ORG_KEY, session_lock_record
from src.upgrade_portal.persistence.actions import (
    ActionRequestConflict,
    ActionStateConflict,
    ActionStoreUnavailable,
    DurableActorScope,
    canonical_digest,
)
from src.upgrade_portal.runtime import identity, lock
from src.upgrade_portal.runtime.runs import RunRecordBuilder, RunSpec

logger = logging.getLogger(__name__)
run_controls_bp = Blueprint("run_controls", __name__)
PREVIEW_PATH = "/api/runs/bulk-actions/preview"
ACTION_PATH = "/api/runs/bulk-actions"
RESULT_PATH = "/api/run-actions/<action_id>"
REQUEST_RESULT_PATH = "/api/run-actions/by-request-key"
RECONCILE_PATH = "/api/runs/<run_id>/reconcile"
PREVIEW_SERVICE_KEY = "RUN_CONTROL_PREVIEW_SERVICE"
ACTION_STORE_KEY = "RUN_ACTION_STORE"
RUN_STORE_KEY = "RUN_STORE"
AUTHORIZATION_READER_KEY = "AUTHORIZATION_READER"
LOCK_CLIENT_KEY = "LOCK_STORE_CLIENT"
CLOUD_EVIDENCE_KEY = "CLOUD_EVIDENCE"
IDEMPOTENCY_HEADER = "Idempotency-Key"


def _visible(record: Mapping[str, Any], organization_id: str, history_scope: str) -> bool:
    """Report whether one record belongs to the requested organization and history scope."""
    if str(record.get("org_id") or record.get("organization_id") or "") != organization_id:
        return False
    if history_scope == "all-sites":
        return True
    if not history_scope.startswith("site:"):
        return False
    return str(record.get("site_id") or "") == history_scope.removeprefix("site:")


def _preview_service() -> BulkActionPreviewService:
    """Return the injected preview service or build one from existing seams."""
    injected = current_app.config.get(PREVIEW_SERVICE_KEY)
    if isinstance(injected, BulkActionPreviewService):
        return injected
    store = current_app.config.get(RUN_STORE_KEY)
    reader = getattr(store, "read_run", None)
    if not callable(reader):
        raise RuntimeError("The run store has no run reader.")
    service = BulkActionPreviewService(
        run_reader=reader,
        visibility_reader=_visible,
        signing_key=str(current_app.config["SECRET_KEY"]),
    )
    current_app.config[PREVIEW_SERVICE_KEY] = service
    return service


def _request_error(code: str) -> tuple[Any, int]:
    """Map one stable preview refusal to its HTTP response."""
    if code == "duplicate_run_id":
        return json_error(400, code, "A run identifier occurs more than once.")
    if code == "batch_size_invalid":
        return json_error(422, code, "Select between 1 and 50 runs.")
    if code == "preview_empty":
        return json_error(422, code, "No selected run is visible in this history scope.")
    return json_error(400, "invalid_request", "The preview request is invalid.")


def _actor() -> DurableActorScope | None:
    """Return the current durable actor scope."""
    owner = identity.current_owner()
    if owner is None:
        return None
    return DurableActorScope.build(owner.identity_kind.value, owner.actor_email)


def _action_store() -> Any:
    """Return the configured durable action repository."""
    store = current_app.config.get(ACTION_STORE_KEY)
    required = ("initialize", "find_request", "read", "claim_item", "write_outcome", "commit_success", "finalize")
    if store is None or any(not callable(getattr(store, name, None)) for name in required):
        raise ActionStoreUnavailable("The ArangoDB action store is unavailable.")
    return store


def _run_reader() -> Any:
    """Return the configured run reader."""
    store = current_app.config.get(RUN_STORE_KEY)
    reader = getattr(store, "read_run", None)
    if not callable(reader):
        raise RuntimeError("The run store has no run reader.")
    return reader


def _site_run_reader() -> Any:
    """Return the configured site run reader."""
    store = current_app.config.get(RUN_STORE_KEY)
    reader = getattr(store, "runs_for_site", None)
    if not callable(reader):
        raise RuntimeError("The run store has no site run reader.")
    return reader


def _retry_run_builder(
    source: Mapping[str, Any],
    targets: list[dict[str, Any]],
    options: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Build one fresh run with current actor ownership and copied safe fields."""
    owner = identity.current_owner()
    if owner is None:
        raise RuntimeError("The retry actor is unavailable.")
    tier = source.get("tier", 2)
    if not isinstance(tier, int) or isinstance(tier, bool):
        tier = 2
    spec = RunSpec(
        org_id=str(source.get("org_id") or source.get("organization_id") or ""),
        org_name=str(source.get("org_name") or source.get("org_id") or ""),
        site_id=str(source.get("site_id") or ""),
        site_name=str(source.get("site_name") or source.get("site_id") or ""),
        actor_email=owner.actor_email,
        browser_id=owner.browser_id,
        tier=tier,
        targets=targets,
        options=options,
    )
    return RunRecordBuilder().build(spec)


def _permission_reader(organization_id: str, site_id: str) -> bool:
    """Read the current write permission through the configured seam."""
    configured = current_app.config.get(AUTHORIZATION_READER_KEY)
    if callable(configured):
        return bool(configured(f"run-control:write:{organization_id}:{site_id}"))
    return identity.org_scope_refusal(organization_id) is None


def _lock_reader(organization_id: str, site_id: str) -> Any:
    """Read the exact current site lock record."""
    return lock.read_lock(organization_id, site_id, client=current_app.config.get(LOCK_CLIENT_KEY))


def _expected_tokens(organization_id: str, site_ids: Sequence[str]) -> dict[str, str]:
    """Return the signed-session lock token for each requested site."""
    result: dict[str, str] = {}
    for site_id in site_ids:
        if not site_id or site_id in result:
            continue
        held = session_lock_record(site_id)
        token = str(getattr(held, "lock_token", "") or "")
        result[site_id] = token
    return result


def _guard(organization_id: str, site_ids: Sequence[str]) -> SiteMutationGuard:
    """Build one current permission and exact-token guard."""
    return SiteMutationGuard(
        _permission_reader,
        _lock_reader,
        _expected_tokens(organization_id, site_ids),
    )


def _action_error(error: Exception) -> tuple[Any, int]:
    """Map one durable action error to a stable HTTP response."""
    code = str(error)
    if isinstance(error, ActionRequestConflict):
        return json_error(409, "idempotency_key_reused", "The idempotency key already binds another request.")
    if isinstance(error, ActionStoreUnavailable):
        return json_error(503, "action_store_unavailable", "The durable action store is unavailable.")
    if isinstance(error, ActionStateConflict):
        return json_error(409, "run_changed", "The action or run changed before the write.")
    if code == "confirmation_mismatch":
        return json_error(400, code, "The typed confirmation does not match.")
    if code in {"preview_mismatch", "preview_invalid"}:
        return json_error(409, "preview_mismatch", "The action request does not match its preview.")
    if code == "preview_expired":
        return json_error(410, code, "The action preview expired.")
    if code == "duplicate_run_id":
        return json_error(400, code, "A run identifier occurs more than once.")
    if code == "batch_size_invalid":
        return json_error(422, code, "Select between 1 and 50 runs.")
    return json_error(400, "invalid_request", "The run action request is invalid.")


@run_controls_bp.post(PREVIEW_PATH)
@identity.require_session
def preview_bulk_action() -> tuple[Any, int] | Any:
    """Return one signed authoritative preview for the current actor and scope."""
    logger.info("Preview one bulk run action")
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return json_error(400, "invalid_request", "The preview request must be a JSON object.")
    try:
        preview_request = BulkPreviewRequest.from_mapping(body)
    except ValueError as exc:
        return _request_error(str(exc))
    selected_org = session.get(SELECTED_ORG_KEY)
    if selected_org != preview_request.organization_id:
        return json_error(403, "organization_forbidden", "The selected organization does not match.")
    refusal = identity.org_scope_refusal(preview_request.organization_id)
    if refusal is not None:
        return refusal
    actor = _actor()
    if actor is None:
        return json_error(401)
    try:
        preview = _preview_service().preview(preview_request, actor.actor_scope)
    except PreviewError as exc:
        return _request_error(exc.code)
    except RuntimeError:
        logger.exception("The preview service is unavailable")
        return json_error(503, "preview_unavailable", "The preview service is unavailable.")
    return jsonify(preview.to_mapping()), 200


@run_controls_bp.post(ACTION_PATH)
@identity.require_session
def submit_bulk_action() -> tuple[Any, int] | Any:
    """Run one durable bulk cancel from an authoritative preview."""
    logger.info("Submit one bulk run action")
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return json_error(400, "invalid_request", "The run action request must be a JSON object.")
    action = body.get("action")
    raw_run_ids = body.get("run_ids")
    confirmation = body.get("confirmation")
    preview_token = body.get("preview_token")
    idempotency_key = request.headers.get(IDEMPOTENCY_HEADER, "")
    if (
        action not in {"cancel", "retry"}
        or not isinstance(raw_run_ids, list)
        or not isinstance(confirmation, str)
        or not isinstance(preview_token, str)
    ):
        return json_error(400, "invalid_request", "The run action request is invalid.")
    actor = _actor()
    if actor is None:
        return json_error(401)
    try:
        preview = _preview_service().verify_action(
            preview_token,
            actor_scope=actor.actor_scope,
            action=action,
            run_ids=tuple(raw_run_ids),
        )
        organization_id = str(preview["organization_id"])
        if session.get(SELECTED_ORG_KEY) != organization_id:
            return json_error(403, "organization_forbidden", "The selected organization does not match.")
        refusal = identity.org_scope_refusal(organization_id)
        if refusal is not None:
            return refusal
        reader = _run_reader()
        site_ids = tuple(
            str(record.get("site_id") or "") if (record := reader(run_id)) is not None else "" for run_id in raw_run_ids
        )
        service = BulkRunActionService(
            _action_store(),
            reader,
            _guard(organization_id, site_ids),
            _site_run_reader(),
            _retry_run_builder,
        )
        operation = service.cancel if action == "cancel" else service.retry
        result = operation(
            actor=actor,
            idempotency_key=idempotency_key,
            confirmation=confirmation,
            preview=preview,
        )
    except (
        BulkActionError,
        PreviewError,
        ValueError,
        ActionRequestConflict,
        ActionStateConflict,
        ActionStoreUnavailable,
    ) as error:
        return _action_error(error)
    return jsonify(result.response()), 200


def _evidence_rows(record: Mapping[str, Any], observed_at: str) -> list[Mapping[str, Any]]:
    """Build one current evidence row for every stored target."""
    source = current_app.config.get(CLOUD_EVIDENCE_KEY)
    read = getattr(source, "read", None)
    if not callable(read):
        raise RuntimeError("The cloud evidence reader is unavailable.")
    raw = read("reconciliation", run_id=str(record.get("run_id") or ""))
    supplied = raw if isinstance(raw, list) else []
    indexed = {
        str(row.get("target_id") or row.get("device_id") or row.get("mac") or ""): row
        for row in supplied
        if isinstance(row, Mapping)
    }
    rows: list[Mapping[str, Any]] = []
    for target in record.get("targets", ()):
        if not isinstance(target, Mapping):
            continue
        target_id = str(target.get("device_id") or target.get("mac") or target.get("id") or "")
        current = dict(indexed.get(target_id, {}))
        current["target_id"] = target_id
        current.setdefault("stored_stop_result", str(target.get("stop_result") or "unknown"))
        current.setdefault("task_id", str(target.get("cloud_task_id") or ""))
        current.setdefault("driver_state", target.get("driver_state"))
        current.setdefault("sources", ["stored"])
        current.setdefault("observed_at", observed_at)
        current.setdefault("task_state", "unknown")
        current.setdefault("write_state", "unknown")
        current.setdefault("is_complete", False)
        current.setdefault("has_conflict", False)
        rows.append(current)
    return rows


@run_controls_bp.post(RECONCILE_PATH)
@identity.require_session
def reconcile_run(run_id: str) -> tuple[Any, int] | Any:
    """Reconcile one stale run from read-only evidence."""
    logger.info("Submit one stale run reconciliation")
    body = request.get_json(silent=True)
    confirmation = body.get("confirmation") if isinstance(body, dict) else None
    if not isinstance(confirmation, str):
        return json_error(400, "invalid_request", "The reconciliation request is invalid.")
    actor = _actor()
    if actor is None:
        return json_error(401)
    try:
        reader = _run_reader()
        record = reader(run_id)
        if record is None:
            return json_error(404, "run_not_found", "The portal found no run with this identifier.")
        organization_id = str(record.get("org_id") or record.get("organization_id") or "")
        site_id = str(record.get("site_id") or "")
        if session.get(SELECTED_ORG_KEY) != organization_id:
            return json_error(403, "organization_forbidden", "The selected organization does not match.")
        refusal = identity.org_scope_refusal(organization_id)
        if refusal is not None:
            return refusal
        service = StoppingRunReconciler(
            _action_store(),
            reader,
            _guard(organization_id, (site_id,)),
            _evidence_rows,
        )
        result = service.reconcile(
            actor=actor,
            idempotency_key=request.headers.get(IDEMPOTENCY_HEADER, ""),
            confirmation=confirmation,
            run_id=run_id,
            organization_id=organization_id,
            site_id=site_id,
        )
    except (ValueError, ActionRequestConflict, ActionStateConflict, ActionStoreUnavailable) as error:
        return _action_error(error)
    return jsonify(result.response()), 200


@run_controls_bp.get(RESULT_PATH)
@identity.require_session
def read_action_result(action_id: str) -> tuple[Any, int] | Any:
    """Return one actor-scoped durable action result."""
    actor = _actor()
    if actor is None:
        return json_error(401)
    try:
        action = _action_store().read(actor.actor_scope, action_id)
    except ActionStoreUnavailable as error:
        return _action_error(error)
    if action is None:
        return json_error(404, "action_not_found", "The portal found no action with this identifier.")
    return jsonify(action.response()), 200


@run_controls_bp.get(REQUEST_RESULT_PATH)
@identity.require_session
def read_action_result_by_request_key() -> tuple[Any, int] | Any:
    """Return one actor-scoped action after a response loss."""
    actor = _actor()
    if actor is None:
        return json_error(401)
    request_key = request.headers.get(IDEMPOTENCY_HEADER, "")
    invalid_character = any(ord(character) < 33 or ord(character) > 126 for character in request_key)
    if not 16 <= len(request_key) <= 128 or invalid_character:
        return json_error(400, "invalid_request", "The idempotency key is invalid.")
    try:
        action = _action_store().find_request(actor.actor_scope, canonical_digest(request_key))
    except ActionStoreUnavailable as error:
        return _action_error(error)
    if action is None:
        return json_error(404, "action_not_found", "The portal found no action for this request key.")
    return jsonify(action.response()), 200
