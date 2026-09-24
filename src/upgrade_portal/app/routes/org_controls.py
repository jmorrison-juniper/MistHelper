"""The retry, reconciliation, and reschedule routes of one multi-site operation.

Why:
    Issue #3247. The single-site portal can retry the failed devices of a
    finished run, check an uncertain outcome against the running versions, and
    move the start time of a planned run. The multi-site portal could do none
    of the three. These routes add the three controls.

    The retry and the reschedule send nothing to the Mist cloud. The check
    reads the running versions and writes only the durable record. No route
    here sends a firmware request, a stop request, or a cancel request.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each action without a secret.
from collections.abc import Callable, Mapping, MutableMapping  # Accept each stored record without a concrete type.
from typing import Any  # The stored record holds JSON values of mixed types.

from flask import Blueprint, Response, current_app, session  # The routes, the answers, and the signed session.

from ....firmware.aggregate_upgrade_service import ReconcileEvidence, RescheduleRequest  # The service values.
from ...runtime import identity  # The signed operator and the digest of the operator address.
from ...upgrade.options import BadOptionError, build_options  # The start time guard and the reboot rule.
from ...upgrade.org_reconcile import OrgReconcileCheck  # The verdict of each uncertain child job.
from ...upgrade.org_retry import OrgRetryPlan  # The devices of one retry.
from ...upgrade.org_versions import OrgVersionRefresh  # The site read of the progress page.
from ..factory import json_error  # The one error envelope of the portal.
from . import upgrade as upgrade_routes  # The durable store and the typed operator address.
from .org_upgrade import (
    CONFIRM_PAGE_PATH,
    CONFIRMATION_REQUIRED,
    CONFLICT_STATUS,
    DEVICE_VERSION_READER_CONFIG_KEY,
    OPTIONS_INVALID,
    OPTIONS_PAGE_PATH,
    OPTIONS_SESSION_KEY,
    SERVICE_UNAVAILABLE_STATUS,
    SITES_REQUIRED,
    SITES_REQUIRED_MESSAGE,
    STATUS_FAILED,
    WRITE_DISABLED,
    OrgOptionRefusal,
    OrgUpgradeScheduleReader,
    active_context,
    aggregate_service,
    confirmation_value,
    current_cloud_session,
    owned_saved_operation,
    release_operation_locks,
    request_source,
    retry_plan_of,
    selected_rows,
    stored_options,
    writes_enabled,
)
from .select import (
    BAD_REQUEST_STATUS,
    MULTI_SITE_MODE,
    NOT_FOUND_STATUS,
    ORG_UPGRADE_RETRY_KEY,
    clear_org_upgrade_options,
    next_page_answer,
    resolve_org,
    store_chosen_mode,
    store_chosen_sites,
)

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

org_controls_bp = Blueprint("org_controls", __name__)  # The factory finds this name through `{name}_bp`.

RETRY_PATH = "/api/org-upgrades/<upgrade_id>/retry"  # Open a new plan for the devices that need a retry.
RETRY_CLEAR_PATH = "/api/org-upgrades/options/retry/clear"  # End the retry, and plan every device again.
RECONCILE_PATH = "/api/org-upgrades/<upgrade_id>/reconcile"  # Check each uncertain child job.
RESCHEDULE_PATH = "/api/org-upgrades/<upgrade_id>/reschedule"  # Move the start time of one planned operation.
JOB_PAGE_PREFIX = "/upgrade/org/jobs/"  # The progress page of one operation.
RECONCILE_WORD = "RECONCILE"  # The single-site check uses the same typed word.

OPERATION_NOT_FOUND = "org_upgrade_operation_not_found"  # No owned operation holds the identifier.
OPERATION_NOT_FOUND_MESSAGE = "The portal found no operation of this browser session with that identifier."
RETRY_UNAVAILABLE = "org_upgrade_retry_unavailable"  # No device needs a retry now.
RETRY_UNAVAILABLE_MESSAGE = (  # The operator learns both conditions of a retry.
    "No device of this operation needs a retry now. "
    "A retry opens after every child job ends, for each device that did not reach the target version."
)
RECONCILE_UNAVAILABLE = "org_upgrade_reconcile_unavailable"  # No child job holds an uncertain outcome.
RECONCILE_UNAVAILABLE_MESSAGE = "No child job of this operation holds an uncertain outcome, so no check is necessary."
RECONCILE_WORD_MESSAGE = "Type RECONCILE and the operation identifier before you start the check."
RESCHEDULE_REFUSED = "org_upgrade_reschedule_refused"  # The saved plan of the session names another operation.
RESCHEDULE_REFUSED_MESSAGE = (  # The cure is a new save of the options.
    "Only the saved plan of this browser session can move before its confirmation. Save the options again."
)
STORE_FAILED = "org_upgrade_store_failed"  # The durable store did not accept the change.
STORE_FAILED_MESSAGE = "The portal could not store the change. Read the operation again before another action."
WRITE_DISABLED_MESSAGE = "Organization upgrade writes stay disabled until the multi-site safety gates are complete."
CONTEXT_MESSAGE = "The organization upgrade context is incomplete."  # No cloud connection for the check.


def _owned_operation(upgrade_id: str) -> dict[str, Any] | None:
    """Return one operation of the selected organization when the signed operator owns it.

    Args:
        upgrade_id: The identifier of the operation.

    Returns:
        The durable operation record, or None.
    """
    org_id = resolve_org(None)  # The selected organization of the signed session.
    return owned_saved_operation(upgrade_id, org_id) if org_id is not None else None  # The owner check.


def _stored_change(action: Callable[[], object], conflict_code: str) -> tuple[Response, int] | None:
    """Run one durable change, and map a refusal or a store fault to one answer.

    Args:
        action: The service call that makes one compare-and-set write.
        conflict_code: The error code of a refusal.

    Returns:
        A refusal answer, or None when the store accepted the change.
    """
    try:  # The service raises ValueError for a refusal and RuntimeError for a lost write.
        action()  # One compare-and-set write. A refusal writes nothing.
    except ValueError as error:  # The operation left the state that the change needs.
        logger.warning("The aggregate change was refused: %s", error)  # The text holds no secret.
        return json_error(CONFLICT_STATUS, conflict_code, str(error))  # The operator reads the exact reason.
    except Exception as error:  # Keep broad because a store fault must answer with a readable refusal.
        logger.exception("The aggregate change did not store after %s", type(error).__name__)  # Keep the trace.
        return json_error(SERVICE_UNAVAILABLE_STATUS, STORE_FAILED, STORE_FAILED_MESSAGE)  # The outcome is unknown.
    return None  # The store accepted the change.


@org_controls_bp.post(RETRY_PATH)
@identity.require_session
def open_retry(upgrade_id: str) -> Response | tuple[Response, int]:
    """Open a new plan that holds only the devices that need a second attempt.

    Args:
        upgrade_id: The settled operation that the retry repeats.

    Returns:
        The answer that opens the options page, or a refusal.
    """
    logger.info("Open a retry of aggregate upgrade %s", upgrade_id)  # Log before the store read.
    operation = _owned_operation(upgrade_id)  # The operator must own the operation.
    if operation is None:  # No such operation, or another operator owns it.
        return json_error(NOT_FOUND_STATUS, OPERATION_NOT_FOUND, OPERATION_NOT_FOUND_MESSAGE)
    plan = retry_plan_of(operation)  # A child that can still write firmware blocks a retry.
    if plan is None:  # A child job still runs, or every device runs the target version.
        return json_error(CONFLICT_STATUS, RETRY_UNAVAILABLE, RETRY_UNAVAILABLE_MESSAGE)
    if not selected_rows(plan.org_id, list(plan.site_ids)):  # A site left the organization after the plan.
        return json_error(NOT_FOUND_STATUS, SITES_REQUIRED, SITES_REQUIRED_MESSAGE)
    _open_retry_scope(plan)  # Select the sites of the retry, and keep only a reference in the cookie.
    logger.debug("The retry of %s holds %s device(s)", upgrade_id, len(plan.devices))  # Log after the change.
    return next_page_answer(OPTIONS_PAGE_PATH)  # Open the options page with the narrowed device list.


def _open_retry_scope(plan: OrgRetryPlan) -> None:
    """Select the multi-site mode and the retry sites, then store the retry reference.

    Why:
        Each store call below can clear the saved options of an earlier scope,
        and that clear also drops the retry reference. The reference therefore
        goes into the session last.

    Args:
        plan: The retry plan of the settled operation.
    """
    store_chosen_mode(MULTI_SITE_MODE)  # A retry of a multi-site operation stays in the multi-site mode.
    store_chosen_sites(list(plan.site_ids))  # Select only the sites that hold a retry device.
    clear_org_upgrade_options()  # The saved options of the settled operation must not reach the new plan.
    session[ORG_UPGRADE_RETRY_KEY] = plan.to_session()  # The cookie holds the operation identity only.


@org_controls_bp.post(RETRY_CLEAR_PATH)
@identity.require_session
def clear_retry() -> Response | tuple[Response, int]:
    """End the open retry, so the options page plans every device of the selected sites.

    Why:
        The saved options of a retry hold the narrowed device list. The clear
        therefore drops the saved options too. Saved options without a durable
        plan identity must never stay, because the submit then takes the
        earlier access point route.

    Returns:
        The answer that opens the options page.
    """
    logger.info("End the retry of the multi-site options")  # Log before the session change.
    clear_org_upgrade_options()  # Drop the retry reference, the saved options, and the request nonce together.
    logger.debug("The multi-site options now plan every device of the selected sites")  # Log after the change.
    return next_page_answer(OPTIONS_PAGE_PATH)  # Show the full device list again.


@org_controls_bp.post(RECONCILE_PATH)
@identity.require_session
def reconcile_operation(upgrade_id: str) -> Response | tuple[Response, int]:
    """Check each uncertain child job against the running version of its devices.

    Args:
        upgrade_id: The operation that holds an uncertain child job.

    Returns:
        The answer that opens the progress page, or a refusal.
    """
    refusal = _reconcile_guard(upgrade_id)  # The write gate and the typed word come before any read.
    if refusal is not None:  # Stop before any cloud read.
        return refusal  # The operator reads the exact reason.
    operation = _owned_operation(upgrade_id)  # The operator must own the operation.
    if operation is None:  # No such operation, or another operator owns it.
        return json_error(NOT_FOUND_STATUS, OPERATION_NOT_FOUND, OPERATION_NOT_FOUND_MESSAGE)
    cloud_session = current_cloud_session()  # The check reads the running versions with this session.
    if cloud_session is None:  # A signed session normally supplies the cloud connection.
        return json_error(BAD_REQUEST_STATUS, STATUS_FAILED, CONTEXT_MESSAGE)
    check = OrgReconcileCheck(operation)  # The uncertain child jobs of the operation.
    if not check.children():  # No child job needs a check.
        return json_error(CONFLICT_STATUS, RECONCILE_UNAVAILABLE, RECONCILE_UNAVAILABLE_MESSAGE)
    return _store_reconciliation(operation, _reconcile_evidence(cloud_session, check))  # Store each verdict.


def _reconcile_guard(upgrade_id: str) -> tuple[Response, int] | None:
    """Refuse a check when the writes are disabled or the typed word does not match.

    Args:
        upgrade_id: The operation that the typed word must name.

    Returns:
        A refusal answer, or None when the check can continue.
    """
    if not writes_enabled():  # The check changes the durable record of a firmware operation.
        return json_error(SERVICE_UNAVAILABLE_STATUS, WRITE_DISABLED, WRITE_DISABLED_MESSAGE)
    if confirmation_value() != f"{RECONCILE_WORD} {upgrade_id}":  # The exact word names this operation.
        return json_error(BAD_REQUEST_STATUS, CONFIRMATION_REQUIRED, RECONCILE_WORD_MESSAGE)
    return None  # Continue to the ownership check.


def _reconcile_evidence(cloud_session: Any, check: OrgReconcileCheck) -> ReconcileEvidence:
    """Read the running versions of each site of an uncertain child job, and decide each verdict.

    Args:
        cloud_session: The signed cloud session of the operator.
        check: The uncertain child jobs of the operation.

    Returns:
        The verdicts, the readings, and the digest of the operator address.
    """
    reader = current_app.config.get(DEVICE_VERSION_READER_CONFIG_KEY, OrgVersionRefresh.running_versions)
    refresh = OrgVersionRefresh(reader)  # The same site read and the same empty-answer rule as the page.
    site_ids = check.site_ids()  # Each site that holds a device of an uncertain child job.
    logger.info("Read the running versions of %s site(s) for the check", len(site_ids))  # Log before the reads.
    answers = {site_id: refresh.read_site(cloud_session, site_id) for site_id in site_ids}  # None: a failed read.
    readings = check.readings(answers)  # One reading for each device of a site that answered.
    logger.debug("The check read %s device version(s)", len(readings))  # Log the count, never a version.
    actor = identity.email_digest(upgrade_routes.actor_address())  # The digest, never the address.
    return ReconcileEvidence(tuple(check.verdicts(readings)), readings, actor)  # The service stores all three.


def _store_reconciliation(
    operation: MutableMapping[str, Any],
    evidence: ReconcileEvidence,
) -> Response | tuple[Response, int]:
    """Store the verdicts, free the sites of a settled operation, and open the progress page.

    Args:
        operation: The durable operation record. The stored change updates it in place.
        evidence: The verdicts, the readings, and the digest of the operator address.

    Returns:
        The answer that opens the progress page, or a refusal.
    """
    store = upgrade_routes.run_store()  # The durable store of every operation.
    logger.info("Store %s verdict(s) for aggregate upgrade %s", len(evidence.verdicts), operation["operation_id"])
    refusal = _stored_change(lambda: aggregate_service().reconcile(operation, store, evidence), RECONCILE_UNAVAILABLE)
    if refusal is not None:  # A live submission, or a store fault.
        return refusal  # The operator reads the exact reason.
    release_operation_locks(operation)  # A proven child can settle the operation, so its sites go free.
    logger.debug("Aggregate upgrade %s reads %s after the check", operation["operation_id"], operation.get("state"))
    return next_page_answer(f"{JOB_PAGE_PREFIX}{operation['operation_id']}")  # Show the stored verdicts.


@org_controls_bp.post(RESCHEDULE_PATH)
@identity.require_session
def reschedule_operation(upgrade_id: str) -> Response | tuple[Response, int]:
    """Move the start time of one planned operation before its confirmation.

    Args:
        upgrade_id: The planned operation that the confirmation page shows.

    Returns:
        The answer that opens the confirmation page, or a refusal.
    """
    options = stored_options()  # The saved plan of the current browser session.
    operation = _planned_operation(upgrade_id, options)  # Only the plan of the page can move.
    if operation is None:  # The session names another plan, or no plan.
        return json_error(CONFLICT_STATUS, RESCHEDULE_REFUSED, RESCHEDULE_REFUSED_MESSAGE)
    try:  # The window guard refuses a past moment and a moment beyond the site lock window.
        change = _reschedule_request(operation)  # The new start moment and the moved reboot moment.
    except BadOptionError as error:  # The time names no moment, or a moment outside the window.
        return json_error(BAD_REQUEST_STATUS, OPTIONS_INVALID, str(OrgOptionRefusal.translate(error)))
    return _store_reschedule(operation, options, change)  # Move every child job through one write.


def _planned_operation(upgrade_id: str, options: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return the owned plan that the saved options of this session name, or None.

    Args:
        upgrade_id: The operation that the request names.
        options: The saved options of the session.

    Returns:
        The durable operation record, or None.
    """
    if active_context() is None or options.get("operation_id") != upgrade_id:  # The page shows another plan.
        return None  # A reschedule never moves a plan that this session did not save.
    return _owned_operation(upgrade_id)  # The operator must own the plan.


def _reschedule_request(operation: Mapping[str, Any]) -> RescheduleRequest:
    """Build the new start moment and the moved reboot moment of one plan.

    Args:
        operation: The durable operation record.

    Returns:
        The change that the service applies to every child job.

    Raises:
        BadOptionError: The start time names no moment, or a moment outside the window.
    """
    body: dict[str, Any] = {}  # The parser adds the start moment when the field holds one.
    OrgUpgradeScheduleReader.add_start_option(body, request_source())  # The same parser as the options save.
    start: int | None = body.get("start_time")  # Epoch seconds, or None to start at once.
    if start is not None:  # An empty field starts the upgrade at once after the confirmation.
        build_options({"start_time": str(start)})  # The single-site window guard refuses a stale moment.
    actor = identity.email_digest(upgrade_routes.actor_address())  # The digest, never the address.
    return RescheduleRequest(start_time=start, reboot_at=_moved_reboot(operation), actor=actor)  # One change.


def _moved_reboot(operation: Mapping[str, Any]) -> int | None:
    """Return the reboot moment of the moved plan, or None when the plan holds no reboot delay.

    Why:
        The save turns the reboot delay into a moment from the clock of the
        save. The reschedule applies the same rule from its own clock, so the
        reboot never falls before the moment of the reschedule.

    Args:
        operation: The durable operation record.

    Returns:
        The new reboot moment in epoch seconds, or None.
    """
    stored = operation.get("plan_options")  # The choices that the save kept beside the plan.
    delay = stored.get("reboot_at") if isinstance(stored, Mapping) else None  # The duration text, such as "1h".
    if not isinstance(delay, str) or not delay.strip():  # The plan holds no reboot delay.
        return None  # The service refuses to move a stored reboot moment without a delay.
    return build_options({"reboot_at": delay}).reboot_at  # The clock of this request plus the delay.


def _store_reschedule(
    operation: MutableMapping[str, Any],
    options: Mapping[str, Any],
    change: RescheduleRequest,
) -> Response | tuple[Response, int]:
    """Move every child job through one write, and keep the saved options in step.

    Args:
        operation: The durable operation record.
        options: The saved options of the session.
        change: The new start moment, the moved reboot moment, and the actor digest.

    Returns:
        The answer that opens the confirmation page, or a refusal.
    """
    store = upgrade_routes.run_store()  # The durable store of every operation.
    logger.info("Move the start time of aggregate upgrade %s", operation["operation_id"])  # Log before the write.
    refusal = _stored_change(lambda: aggregate_service().reschedule(operation, store, change), RESCHEDULE_REFUSED)
    if refusal is not None:  # The plan left the planned state, or the store did not accept the write.
        return refusal  # The operator reads the exact reason.
    updated = {key: value for key, value in options.items() if key != "start_time"}  # A copy without the old start.
    if change.start_time is not None:  # The operator chose a new start moment.
        updated["start_time"] = change.start_time  # The confirmation page names the moved moment.
    session[OPTIONS_SESSION_KEY] = updated  # Reassign the value, so the signed session records the change.
    logger.debug("Aggregate upgrade %s now starts at %s", operation["operation_id"], change.start_time)  # Log after.
    return next_page_answer(CONFIRM_PAGE_PATH)  # Show the moved start time before the typed confirmation.
