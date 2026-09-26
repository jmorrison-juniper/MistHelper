"""Expose preview, cancel, result, and reconciliation routes."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any, cast  # Narrow validated request values without runtime changes.

import mistapi
from flask import Blueprint, current_app, jsonify, request, session

from src.firmware.running_version import DEFAULT_STATS_PAGE_LIMIT, RunningFirmwareVersionResolver
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
from src.upgrade_portal.capture.devices import guard_page_count, read_every_page
from src.upgrade_portal.persistence.actions import (
    ActionRequestConflict,
    ActionStateConflict,
    ActionStoreUnavailable,
    DurableActorScope,
    UpgradeRunAction,
    canonical_digest,
)
from src.upgrade_portal.runtime import identity, lock
from src.upgrade_portal.runtime.runs import RunRecordBuilder, RunSpec
from src.upgrade_portal.upgrade import gate

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
STATISTICS_SECTION = "listSiteDevicesStats"  # Issue #3438: the section name that the page walk logs.

BulkActionFields = tuple[str, list[Any], str, str, str]  # Keep the parsed request shape in one local term.


class SiteStatsFirmwareEvidenceReader:
    """Read firmware reconciliation evidence from the site statistics endpoint."""

    def __init__(self, cloud_session: Any) -> None:
        """Store the signed-in Mist session without logging credentials."""
        self._cloud_session = cloud_session  # The identity registry owns the token-bearing object.

    def read(self, record: Mapping[str, Any], observed_at: str) -> list[Mapping[str, Any]]:
        """Return one safe evidence row for each stored target.

        Why:
            Issue #3438. The read walks every page of the site statistics. A
            lost page leaves a target with no fresh row. That target then holds
            unavailable evidence, so its stored version never shows as the
            running version.
        """
        logger.info("Read site statistics for reconciliation evidence")  # Record the read before the cloud call.
        site_id = str(record.get("site_id") or "")  # Limit the approved endpoint to the run site.
        response = self._read_site_statistics(site_id)  # WHY: isolate the SDK call so signature faults stay visible.
        raw_rows, page_lost = self._read_pages(response)  # Issue #3438: walk every page and name a lost page.
        rows = self._project_statistics_rows(raw_rows)  # WHY: keep the approved reconciliation fields only.
        running = RunningFirmwareVersionResolver.index_stats_rows(rows)  # Use the shared running-version rule.
        indexed = self._index_readings(rows, running)  # Preserve firmware status beside the running version.
        targets = self._targets(record)  # The stored targets of the run, in the stored order.
        if page_lost:  # A target with no fresh row must not show its stored version as running.
            self._mark_unread(site_id, targets, indexed)  # One warning names the site and the unread count.
        result = [_target_evidence_row(target, indexed, observed_at) for target in targets]  # One row each.
        logger.debug("Read reconciliation evidence for %s target(s)", len(result))  # Report a safe count.
        return result  # Give the reconciliation service only safe rows.

    def _read_pages(self, response: Any) -> tuple[list[Any], bool]:
        """Walk every page of the statistics read.

        Why:
            Issue #3438. ``mistapi.get_all`` adds a later page with no status
            check, so a lost page looked like a whole read. The shared walk
            stops at the first lost page and names it.

        Args:
            response: The first page, or None when the first call failed.

        Returns:
            The rows of each page that arrived, and true when a page is lost.
        """
        if response is None:  # The first call failed, so no page arrived.
            logger.debug("The statistics read holds no first page")  # The error log above names the status.
            return [], True  # Every target then holds unavailable evidence.
        logger.info("Walk every page of the statistics read")  # Log before the page walk.
        walk = read_every_page(self._cloud_session, STATISTICS_SECTION, response)  # Stop at the first lost page.
        first_page = guard_page_count(STATISTICS_SECTION, len(walk.records), response)  # A fault of page one.
        logger.debug("Read %s raw site statistics row(s)", len(walk.records))  # WHY: measure the cloud result.
        return list(walk.records), bool(first_page or walk.partial_reasons)  # A reason names a lost page.

    @staticmethod
    def _mark_unread(site_id: str, targets: Sequence[Mapping[str, Any]], indexed: dict[str, Mapping[str, Any]]) -> None:
        """Give each target with no fresh row the unavailable evidence.

        Args:
            site_id: The run site, for the one warning.
            targets: The stored targets of the run.
            indexed: The fresh evidence rows by target. This method adds one row for each unread target.
        """
        target_ids = [_target_id(target) for target in targets]  # The identifier of each stored target.
        unread = [target_id for target_id in target_ids if target_id not in indexed]  # No fresh row arrived.
        for target_id in unread:  # Each unread target gets its own row, so no list is shared.
            indexed[target_id] = _unread_evidence()  # Unavailable evidence, never the stored version.
        logger.warning(  # One warning for one lost read. The warning names no device address.
            "The site statistics read at site %s lost a page. %s target(s) hold unavailable evidence.",
            site_id,
            len(unread),
        )

    def _read_site_statistics(self, site_id: str) -> Any:
        """Read device statistics with the installed SDK signature."""
        try:
            logger.info("Call listSiteDevicesStats for reconciliation evidence")  # WHY: audit the cloud read.
            response = mistapi.api.v1.sites.stats.listSiteDevicesStats(  # WHY: mistapi 0.64.0 has no fields kwarg.
                self._cloud_session,
                site_id,
                type="all",
                limit=DEFAULT_STATS_PAGE_LIMIT,
            )
            status_code = getattr(response, "status_code", 200)  # WHY: old tests use response doubles without status.
            if isinstance(status_code, int) and status_code >= 400:  # WHY: failed status makes evidence unusable.
                logger.error(  # WHY: the operator must see the cloud status instead of an empty evidence result.
                    "The cloud returned HTTP %s for reconciliation site statistics at site %s",
                    status_code,
                    site_id,
                )
                return None  # WHY: pagination treats None as no evidence, preserving the failure contract.
            logger.debug("listSiteDevicesStats returned status %s", getattr(response, "status_code", "unknown"))
            return response  # WHY: the pagination helper consumes the response object.
        except TypeError:  # WHY: signature drift is a programming error, not a recoverable cloud result.
            logger.exception(  # WHY: preserve the stack trace for a developer repair.
                "The listSiteDevicesStats call does not match the installed mistapi SDK signature"
            )
            raise  # WHY: keep a malformed SDK call visible to tests and callers.

    @staticmethod
    def _project_statistics_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        """Keep only the reconciliation fields from site statistics rows."""
        field_names = tuple(gate.STATISTICS_FIELDS.split(","))  # WHY: reuse the gate field contract.
        return [  # WHY: avoid storing full cloud rows after the SDK returns them.
            {field_name: row[field_name] for field_name in field_names if field_name in row}
            for row in rows
            if isinstance(row, Mapping)
        ]

    @staticmethod
    def _targets(record: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        """Return the stored target mappings of one run."""
        return [target for target in record.get("targets", ()) if isinstance(target, Mapping)]  # Skip bad rows.

    @staticmethod
    def _index_readings(rows: Sequence[Mapping[str, Any]], running: Mapping[str, str]) -> dict[str, Mapping[str, Any]]:
        """Index safe statistics evidence by target identifier."""
        indexed: dict[str, Mapping[str, Any]] = {}  # Store rows under the identifiers used by run targets.
        for row in rows:  # Convert each current statistics row into a gate reading.
            reading = gate.reading_from_record(row)  # Reuse the firmware-status parser from the settle gate.
            if reading is None:  # A row without a MAC cannot match a target.
                continue
            indexed[reading.mac] = {  # Keep only fields that reconciliation may store.
                "running_version": running.get(reading.mac, reading.version),
                "fwupdate_status": reading.fwupdate_status,
                "task_state": "final",
                "write_state": "not_writing",
                "sources": ["device"],
                "has_conflict": False,
            }
        return indexed  # Return evidence keyed by normalized MAC.

    @staticmethod
    def firmware_success(current: Mapping[str, Any]) -> bool:
        """Report whether one evidence row proves firmware success."""
        status = str(current.get("fwupdate_status") or "").strip().lower()  # Normalize the Mist status token.
        target = str(current.get("version_target") or "")  # Read the requested version from the target row.
        running = str(current.get("running_version") or "")  # Read the running version from site statistics.
        return status == "success" and gate.version_matches(target, running)  # Use the shared comparison rule.


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
    spec = RunSpec(
        org_id=str(source.get("org_id") or source.get("organization_id") or ""),
        org_name=str(source.get("org_name") or source.get("org_id") or ""),
        site_id=str(source.get("site_id") or ""),
        site_name=str(source.get("site_name") or source.get("site_id") or ""),
        actor_email=owner.actor_email,
        browser_id=owner.browser_id,
        tier=_retry_tier(source),
        targets=targets,
        options=options,
    )
    return RunRecordBuilder().build(spec)


def _retry_tier(source: Mapping[str, Any]) -> int:
    """Return one safe retry tier.

    Args:
        source: The stored source run record.

    Returns:
        The integer tier that the run builder accepts.
    """
    tier = source.get("tier", 2)  # Preserve the existing default tier.
    if not isinstance(tier, int) or isinstance(tier, bool):  # Keep bool out of integer-only run tiers.
        tier = 2  # Preserve the prior fallback for unsafe source data.
    return tier  # Give the builder the exact safe tier.


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


def _bulk_action_fields(body: Mapping[str, Any]) -> BulkActionFields | None:
    """Return validated fields from one bulk action request.

    Args:
        body: The decoded JSON object from the request.

    Returns:
        The ordered request fields, or null for an invalid request.
    """
    action = body.get("action")  # Keep the prior request field read order.
    raw_run_ids = body.get("run_ids")  # Keep the prior request field read order.
    confirmation = body.get("confirmation")  # Keep the prior request field read order.
    preview_token = body.get("preview_token")  # Keep the prior request field read order.
    idempotency_key = request.headers.get(IDEMPOTENCY_HEADER, "")  # Preserve the existing header default.
    if not _is_bulk_action_fields_valid(action, raw_run_ids, confirmation, preview_token):  # Keep one refusal point.
        return None  # Tell the caller to return the existing invalid request response.
    return (  # Preserve the tuple value order after the runtime type check.
        cast(str, action),
        cast(list[Any], raw_run_ids),
        cast(str, confirmation),
        cast(str, preview_token),
        idempotency_key,
    )


def _is_bulk_action_fields_valid(
    action: Any,
    raw_run_ids: Any,
    confirmation: Any,
    preview_token: Any,
) -> bool:
    """Report whether one bulk action request has valid field types.

    Args:
        action: The requested action name.
        raw_run_ids: The requested run identifiers.
        confirmation: The typed confirmation text.
        preview_token: The signed preview token.

    Returns:
        True when the request fields can enter preview verification.
    """
    return (  # Keep the prior combined request validation.
        action in {"cancel", "retry"}
        and isinstance(raw_run_ids, list)
        and isinstance(confirmation, str)
        and isinstance(preview_token, str)
    )


def _submit_bulk_result(actor: DurableActorScope, fields: BulkActionFields) -> Any:
    """Run the selected durable bulk action or return a prior refusal.

    Args:
        actor: The current durable actor.
        fields: The validated request fields.

    Returns:
        The durable action response object, or one HTTP refusal response.
    """
    action, raw_run_ids, confirmation, preview_token, idempotency_key = fields  # Keep field order exact.
    preview = _preview_service().verify_action(  # Verify before any mutable state check.
        preview_token,
        actor_scope=actor.actor_scope,
        action=action,
        run_ids=tuple(raw_run_ids),
    )
    organization_id = str(preview["organization_id"])  # Use the signed server-bound organization.
    selected_error = _selected_organization_error(organization_id)  # Preserve the same organization check point.
    if selected_error is not None:  # Keep the prior early response behavior.
        return selected_error  # Return the exact route response before a durable write.
    reader = _run_reader()  # Reuse the configured run reader for site checks and service input.
    service = _bulk_run_action_service(organization_id, raw_run_ids, reader)  # Build the guarded service.
    operation = service.cancel if action == "cancel" else service.retry  # Preserve action dispatch.
    return operation(  # Return the exact durable operation result.
        actor=actor,
        idempotency_key=idempotency_key,
        confirmation=confirmation,
        preview=preview,
    )


def _selected_organization_error(organization_id: str) -> tuple[Any, int] | Any | None:
    """Return the stable response for an organization refusal.

    Args:
        organization_id: The organization from the signed request context.

    Returns:
        The HTTP refusal response, or null when the actor can continue.
    """
    if session.get(SELECTED_ORG_KEY) != organization_id:  # Preserve the selected organization check order.
        return json_error(403, "organization_forbidden", "The selected organization does not match.")  # Same text.
    refusal = identity.org_scope_refusal(organization_id)  # Preserve the organization scope refusal check.
    if refusal is not None:  # Match the prior refusal point.
        return refusal  # Return the exact response object from identity.
    return None  # Let the caller proceed to guarded writes.


def _bulk_run_action_service(
    organization_id: str,
    raw_run_ids: Sequence[Any],
    reader: Any,
) -> BulkRunActionService:
    """Build one bulk action service with current site guards.

    Args:
        organization_id: The organization from the signed preview.
        raw_run_ids: The requested run identifiers.
        reader: The configured run reader.

    Returns:
        The configured bulk run action service.
    """
    site_ids = tuple(  # Preserve the existing site token snapshot source.
        str(record.get("site_id") or "") if (record := reader(run_id)) is not None else "" for run_id in raw_run_ids
    )
    return BulkRunActionService(  # Keep all durable service seams unchanged.
        _action_store(),
        reader,
        _guard(organization_id, site_ids),
        _site_run_reader(),
        _retry_run_builder,
    )


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
    fields = _bulk_action_fields(body)  # Keep request validation before actor lookup.
    if fields is None:
        return json_error(400, "invalid_request", "The run action request is invalid.")
    actor = _actor()
    if actor is None:
        return json_error(401)
    try:
        result = _submit_bulk_result(actor, fields)
    except (
        BulkActionError,
        PreviewError,
        ValueError,
        ActionRequestConflict,
        ActionStateConflict,
        ActionStoreUnavailable,
    ) as error:
        return _action_error(error)
    if not isinstance(result, UpgradeRunAction):  # Preserve organization refusal responses.
        return result
    return jsonify(result.response()), 200


def _evidence_rows(record: Mapping[str, Any], observed_at: str) -> list[Mapping[str, Any]]:
    """Build one current evidence row for every stored target."""
    source = current_app.config.get(CLOUD_EVIDENCE_KEY)
    read = getattr(source, "read", None)
    if not callable(read):  # Production reads the approved site statistics endpoint.
        owner = identity.current_session()  # Read the signed-in session from the identity registry.
        cloud_session = getattr(owner, "cloud_session", None)  # Keep the credential-bearing object out of logs.
        if cloud_session is None:  # A missing session cannot read cloud evidence.
            raise RuntimeError("The cloud evidence reader is unavailable.")
        return SiteStatsFirmwareEvidenceReader(cloud_session).read(record, observed_at)  # Use current cloud proof.
    raw = read("reconciliation", run_id=str(record.get("run_id") or ""))  # Read scripted test evidence.
    indexed = _indexed_evidence(raw)  # Preserve supplied cloud evidence lookup rules.
    return [  # Preserve target order while skipping unsupported target rows.
        _target_evidence_row(target, indexed, observed_at)
        for target in record.get("targets", ())
        if isinstance(target, Mapping)
    ]


def _indexed_evidence(raw: Any) -> dict[str, Mapping[str, Any]]:
    """Return cloud evidence rows indexed by one target identifier.

    Args:
        raw: The raw evidence value from the configured reader.

    Returns:
        The evidence rows keyed by their supported target identifier.
    """
    supplied = raw if isinstance(raw, list) else []  # Preserve the prior list-only evidence rule.
    return {  # Preserve the prior target identifier preference.
        str(row.get("target_id") or row.get("device_id") or row.get("mac") or ""): row
        for row in supplied
        if isinstance(row, Mapping)
    }


def _target_id(target: Mapping[str, Any]) -> str:
    """Return the identifier that keys the evidence of one stored target.

    Args:
        target: The stored target from the run record.

    Returns:
        The device identifier, the address, or the target identifier, in that order.
    """
    return str(target.get("device_id") or target.get("mac") or target.get("id") or "")  # Preserve the priority.


def _unread_evidence() -> dict[str, Any]:
    """Return the evidence of one target that the reader did not read.

    Why:
        Issue #3438. A lost page leaves a target with no fresh row. The stored
        fallbacks of ``_target_evidence_row`` then showed the stored version as
        the running version. These values name the evidence unavailable, so
        the reconciliation service reports ``cloud_evidence_unavailable``.

    Returns:
        A new row. The stored fallbacks add the stored target fields.
    """
    return {
        "running_version": "",  # No fresh row names the running version.
        "fwupdate_status": "",  # No fresh row names the firmware status.
        "task_state": "unavailable",  # The service reads this value as unavailable evidence.
        "write_state": "unavailable",  # The service reads this value as unavailable evidence.
        "sources": ["stored"],  # Only the stored target speaks for this device.
        "observed_at": None,  # No observation took place.
        "firmware_success": False,  # No fresh row proves a success.
        "is_complete": False,  # Unavailable evidence is never complete.
        "has_conflict": False,  # No fresh row disagrees with the stored target.
    }


def _target_evidence_row(
    target: Mapping[str, Any],
    indexed: Mapping[str, Mapping[str, Any]],
    observed_at: str,
) -> Mapping[str, Any]:
    """Return one evidence row with stored target fallbacks.

    Args:
        target: The stored target from the run record.
        indexed: The cloud evidence rows keyed by target.
        observed_at: The observation time for default evidence.

    Returns:
        One evidence row with the same fallback fields as before.
    """
    target_id = _target_id(target)  # Preserve the identifier priority of the stored target.
    current = dict(indexed.get(target_id, {}))  # Copy supplied evidence before defaults are applied.
    current["target_id"] = target_id  # Preserve the stored target identifier in the output.
    current.setdefault("stored_stop_result", str(target.get("stop_result") or "unknown"))  # Keep the stored default.
    current.setdefault("task_id", str(target.get("cloud_task_id") or ""))  # Keep the stored cloud task fallback.
    current.setdefault("driver_state", target.get("driver_state"))  # Keep the stored driver state fallback.
    current.setdefault("version_target", str(target.get("version_target") or target.get("target_version") or ""))
    current.setdefault("running_version", str(target.get("version_after") or ""))
    current.setdefault("fwupdate_status", "")
    current.setdefault("sources", ["stored"])  # Keep the stored-only source fallback.
    current.setdefault("observed_at", observed_at)  # Keep the caller observation time fallback.
    current.setdefault("task_state", "unknown")  # Keep the unknown task fallback.
    current.setdefault("write_state", "unknown")  # Keep the unknown write fallback.
    current.setdefault(
        "firmware_success",
        SiteStatsFirmwareEvidenceReader.firmware_success(current),
    )  # Reuse the gate version comparison.
    current.setdefault("is_complete", bool(current["firmware_success"]))  # Firmware success is complete evidence.
    current.setdefault("has_conflict", False)  # Keep the no-conflict fallback.
    return current  # Return the completed evidence row.


def _reconcile_result(actor: DurableActorScope, run_id: str, confirmation: str) -> Any:
    """Run one reconciliation after request and actor validation.

    Args:
        actor: The current durable actor.
        run_id: The requested run identifier.
        confirmation: The typed confirmation text.

    Returns:
        The durable action response object, or one HTTP refusal response.
    """
    reader = _run_reader()  # Preserve the run lookup before authorization checks.
    record = reader(run_id)  # Read the requested run once for the same decision point.
    if record is None:  # Preserve the existing not-found response before organization checks.
        return json_error(404, "run_not_found", "The portal found no run with this identifier.")
    organization_id = str(record.get("org_id") or record.get("organization_id") or "")  # Preserve source priority.
    site_id = str(record.get("site_id") or "")  # Preserve the stored site identifier rule.
    selected_error = _selected_organization_error(organization_id)  # Preserve selected and scope checks.
    if selected_error is not None:  # Keep the prior early response behavior.
        return selected_error  # Return the exact route response before a durable write.
    service = StoppingRunReconciler(  # Use the same durable reconciliation seams.
        _action_store(),
        reader,
        _guard(organization_id, (site_id,)),
        _evidence_rows,
    )
    return service.reconcile(  # Return the exact durable reconciliation result.
        actor=actor,
        idempotency_key=request.headers.get(IDEMPOTENCY_HEADER, ""),
        confirmation=confirmation,
        run_id=run_id,
        organization_id=organization_id,
        site_id=site_id,
    )


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
        result = _reconcile_result(actor, run_id, confirmation)
    except (ValueError, ActionRequestConflict, ActionStateConflict, ActionStoreUnavailable) as error:
        return _action_error(error)
    if not isinstance(result, UpgradeRunAction):  # Preserve authorization and not-found responses.
        return result
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
