"""The organization AP upgrade options, confirmation, and status routes.

Why:
    The live portal keeps the single-site run routes unchanged. These routes
    add the organization job as a second mode after the organization choice.
    The browser never receives a Mist token or a raw SDK object.
"""

from __future__ import annotations

import logging
import secrets
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from flask import Blueprint, Response, current_app, jsonify, request, session

from ....firmware.org_upgrade_body import OrgUpgradeBody
from ....firmware.org_upgrade_service import OrgUpgradeResult, OrgUpgradeService
from ...runtime import identity
from ..factory import json_error
from .select import (
    BAD_REQUEST_STATUS,
    MULTI_SITE_MODE,
    NOT_FOUND_STATUS,
    OK_STATUS,
    ORG_UPGRADE_OPTIONS_KEY,
    ORG_UPGRADE_OPTIONS_NONCE_KEY,
    ORG_UPGRADE_OPTIONS_ORG_KEY,
    build_site_rows,
    next_page_answer,
    org_display_name,
    render_page,
    resolve_org,
    selected_mode,
    selected_site_ids,
)

logger = logging.getLogger(__name__)

org_upgrade_bp = Blueprint("org_upgrade", __name__)

OPTIONS_PAGE_PATH = "/upgrade/org/options"
OPTIONS_API_PATH = "/api/org-upgrades/options"
CONFIRM_PAGE_PATH = "/upgrade/org/confirm"
SUBMIT_PATH = "/api/org-upgrades"
JOB_PAGE_PATH = "/upgrade/org/jobs/<upgrade_id>"
STATUS_PATH = "/api/org-upgrades/<upgrade_id>"
CANCEL_PATH = "/api/org-upgrades/<upgrade_id>/cancel"

OPTIONS_TEMPLATE = "upgrade/org_options.html"
CONFIRM_TEMPLATE = "upgrade/org_confirm.html"
PROGRESS_TEMPLATE = "upgrade/org_progress.html"

OPTIONS_SESSION_KEY = ORG_UPGRADE_OPTIONS_KEY
OPTIONS_ORG_SESSION_KEY = ORG_UPGRADE_OPTIONS_ORG_KEY
OPTIONS_NONCE_SESSION_KEY = ORG_UPGRADE_OPTIONS_NONCE_KEY
LAST_JOB_SESSION_KEY = "org_upgrade_last_job"
SERVICE_CONFIG_KEY = "ORG_UPGRADE_SERVICE"
WRITES_ENABLED_CONFIG_KEY = "ORG_UPGRADE_WRITES_ENABLED"

MODE_REQUIRED = "multi_site_mode_required"
MODE_REQUIRED_MESSAGE = "Choose the multi-site mode before you configure an organization upgrade."
SITES_REQUIRED = "sites_not_chosen"
SITES_REQUIRED_MESSAGE = "Choose one or more sites before you configure an organization upgrade."
OPTIONS_INVALID = "org_upgrade_options_invalid"
CONFIRMATION_REQUIRED = "confirmation_required"
CONFIRMATION_MESSAGE = "Type CONFIRM before you start the organization upgrade."
SUBMISSION_FAILED = "org_upgrade_submission_failed"
STATUS_FAILED = "org_upgrade_status_failed"
CANCEL_FAILED = "org_upgrade_cancel_failed"
WRITE_DISABLED = "org_upgrade_write_disabled"
ALREADY_SUBMITTED = "org_upgrade_already_submitted"
JOB_NOT_OWNED = "org_upgrade_job_not_owned"
TERMINAL_JOB_STATES = frozenset({"cancelled", "completed", "failed"})

BAD_GATEWAY_STATUS = 502
CONFLICT_STATUS = 409
SERVICE_UNAVAILABLE_STATUS = 503


def upgrade_service() -> Any:
    """Return the injected service or the production service class."""
    return current_app.config.get(SERVICE_CONFIG_KEY, OrgUpgradeService)


def writes_enabled() -> bool:
    """Return true when the deployment enables organization firmware writes."""
    return current_app.config.get(WRITES_ENABLED_CONFIG_KEY) is True


def active_context() -> tuple[str, list[str]] | None:
    """Return the organization and selected sites for the multi-site mode."""
    org_id = resolve_org(None)
    site_ids = selected_site_ids()
    if org_id is None or selected_mode() != MULTI_SITE_MODE or not site_ids:
        return None
    return org_id, site_ids


def selected_rows(org_id: str, site_ids: list[str]) -> list[dict[str, Any]]:
    """Return the selected site rows and preserve the selection order."""
    index = {str(row.get("site_id", "")): row for row in build_site_rows(org_id)}
    if any(site_id not in index for site_id in site_ids):
        return []
    return [index[site_id] for site_id in site_ids]


def read_options() -> dict[str, Any]:
    """Read and normalize the supported form or JSON option fields."""
    payload: Any = request.get_json(silent=True)
    source: Mapping[str, Any] = payload if isinstance(payload, Mapping) else request.form
    version = str(source.get("version", "")).strip()
    strategy = str(source.get("strategy", "canary")).strip()
    phases_text = str(source.get("canary_phases", "")).strip()
    phases = [int(part.strip()) for part in phases_text.split(",") if part.strip()] if phases_text else []
    failure_text = str(source.get("max_failure_percentage", "5")).strip()
    request_body: dict[str, Any] = {
        "versions": [{"firmware_type": "ap", "version": version}],
        "strategy": strategy,
    }
    if strategy != "big_bang":
        request_body["max_failure_percentage"] = int(failure_text)
    if strategy == "canary":
        request_body["canary_phases"] = phases
    start_text = str(source.get("start_time", "")).strip()
    if start_text:
        start = datetime.fromisoformat(start_text)
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)
        request_body["start_time"] = int(start.timestamp())
    return request_body


def stored_options() -> dict[str, Any]:
    """Return options only when they belong to the selected organization."""
    if session.get(OPTIONS_ORG_SESSION_KEY) != resolve_org(None):
        return {}
    value: Any = session.get(OPTIONS_SESSION_KEY)
    return dict(value) if isinstance(value, dict) else {}


def request_for_service(site_ids: list[str], options: Mapping[str, Any]) -> dict[str, Any]:
    """Build the validated service request from session state."""
    request_body = {**dict(options), "site_ids": list(site_ids)}
    return OrgUpgradeBody.build(request_body)


def options_view(options: Mapping[str, Any]) -> dict[str, Any]:
    """Return form values from the validated service option shape."""
    versions = options.get("versions", [])
    first = versions[0] if isinstance(versions, list) and versions and isinstance(versions[0], Mapping) else {}
    phases = options.get("canary_phases", [])
    start_value = options.get("start_time")
    start_text = ""
    if type(start_value) is int:
        start_text = datetime.fromtimestamp(start_value, UTC).strftime("%Y-%m-%dT%H:%M")
    return {
        "version": first.get("version", ""),
        "strategy": options.get("strategy", "canary"),
        "canary_phases": ",".join(str(value) for value in phases) if isinstance(phases, list) else "",
        "max_failure_percentage": options.get("max_failure_percentage", 5),
        "start_time": start_text,
    }


def current_cloud_session() -> Any:
    """Return the authenticated Mist session of the current operator."""
    record = identity.current_session()
    return None if record is None else record.cloud_session


def result_error(result: OrgUpgradeResult, code: str) -> tuple[Response, int] | None:
    """Return an API error when the cloud outcome is not a valid success."""
    if result.error is None:
        return None
    return json_error(BAD_GATEWAY_STATUS, code, result.error)


def _array_count(value: object) -> int:
    """Return the length of an array or zero."""
    return len(value) if isinstance(value, list) else 0


def _target_counts(targets: Mapping[str, object]) -> tuple[int, int, int]:
    """Return total, upgraded, and failed target counts."""
    raw_total = targets.get("total", 0)
    total = raw_total if type(raw_total) is int else 0
    return total, _array_count(targets.get("upgraded")), _array_count(targets.get("failed"))


def _site_summary(entry: Mapping[str, object]) -> tuple[dict[str, Any], tuple[int, int, int], bool]:
    """Normalize one site entry and its target counts."""
    raw_nested = entry.get("upgrade")
    nested = raw_nested if isinstance(raw_nested, Mapping) else entry
    raw_targets = nested.get("targets")
    targets = raw_targets if isinstance(raw_targets, Mapping) else {}
    counts = _target_counts(targets)
    row = {
        "site_id": entry.get("site_id", nested.get("site_id", "")),
        "id": nested.get("id", entry.get("upgrade_id", "")),
        "status": nested.get("status", "unknown"),
        "total": counts[0],
        "upgraded": counts[1],
        "failed": counts[2],
    }
    return row, counts, bool(targets)


def _site_summaries(entries: object) -> tuple[list[dict[str, Any]], tuple[int, int, int], bool]:
    """Normalize site entries and add their target counts."""
    rows: list[dict[str, Any]] = []
    totals = [0, 0, 0]
    has_targets = False
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, Mapping):
            continue
        row, counts, site_has_targets = _site_summary(entry)
        rows.append(row)
        totals = [current + value for current, value in zip(totals, counts, strict=True)]
        has_targets = has_targets or site_has_targets
    return rows, (totals[0], totals[1], totals[2]), has_targets


def status_summary(result: OrgUpgradeResult) -> dict[str, Any]:
    """Build job totals from the target arrays of each site upgrade."""
    data = dict(result.data)
    entries = data.get("site_upgrades", data.get("upgrades", []))
    sites, counts, has_site_targets = _site_summaries(entries)
    root_targets = data.get("targets")
    if not has_site_targets and isinstance(root_targets, Mapping):
        counts = _target_counts(root_targets)
    return {
        "status": data.get("status", "unknown"),
        "current_phase": data.get("current_phase"),
        "total": counts[0],
        "upgraded_count": counts[1],
        "failed_count": counts[2],
        "site_upgrades": sites,
    }


def remember_job_state(org_id: str, upgrade_id: str, state: object) -> None:
    """Update the owned job marker after a status read."""
    marker = session.get(LAST_JOB_SESSION_KEY)
    if not isinstance(marker, dict):
        return
    if marker.get("org_id") != org_id or marker.get("upgrade_id") != upgrade_id:
        return
    marker["state"] = str(state).lower()
    session[LAST_JOB_SESSION_KEY] = marker


@org_upgrade_bp.get(OPTIONS_PAGE_PATH)
@identity.require_session
def options_page() -> str | tuple[Response, int]:
    """Show the AP-only organization upgrade options."""
    context = active_context()
    if context is None:
        return json_error(BAD_REQUEST_STATUS, MODE_REQUIRED, MODE_REQUIRED_MESSAGE)
    org_id, site_ids = context
    rows = selected_rows(org_id, site_ids)
    if not rows:
        return json_error(NOT_FOUND_STATUS, SITES_REQUIRED, SITES_REQUIRED_MESSAGE)
    return render_page(OPTIONS_TEMPLATE, sites=rows, options=options_view(stored_options()))


@org_upgrade_bp.post(OPTIONS_API_PATH)
@identity.require_session
def save_options() -> Response | tuple[Response, int]:
    """Validate the options and open the familiar confirmation step."""
    context = active_context()
    if context is None:
        return json_error(BAD_REQUEST_STATUS, MODE_REQUIRED, MODE_REQUIRED_MESSAGE)
    org_id, site_ids = context
    try:
        options = read_options()
        request_for_service(site_ids, options)
    except (TypeError, ValueError, OverflowError) as error:
        return json_error(BAD_REQUEST_STATUS, OPTIONS_INVALID, str(error))
    session[OPTIONS_SESSION_KEY] = options
    session[OPTIONS_ORG_SESSION_KEY] = org_id
    session[OPTIONS_NONCE_SESSION_KEY] = secrets.token_urlsafe(24)
    return next_page_answer(CONFIRM_PAGE_PATH)


@org_upgrade_bp.get(CONFIRM_PAGE_PATH)
@identity.require_session
def confirm_page() -> str | tuple[Response, int]:
    """Show the final impact summary and typed confirmation field."""
    context = active_context()
    options = stored_options()
    if context is None or not options:
        return json_error(BAD_REQUEST_STATUS, OPTIONS_INVALID, "Save valid upgrade options before confirmation.")
    org_id, site_ids = context
    rows = selected_rows(org_id, site_ids)
    if not rows:
        return json_error(NOT_FOUND_STATUS, SITES_REQUIRED, SITES_REQUIRED_MESSAGE)
    return render_page(
        CONFIRM_TEMPLATE,
        org_name=org_display_name(org_id),
        site_count=len(rows),
        device_count=sum(int(row.get("device_count", 0)) for row in rows),
        options=options_view(options),
        writes_enabled=writes_enabled(),
    )


def _confirmation_value() -> str:
    """Return the typed confirmation from JSON or form data."""
    payload: Any = request.get_json(silent=True)
    source = payload if isinstance(payload, Mapping) else request.form
    return str(source.get("confirmation", ""))


def _submission_is_repeated(request_nonce: object) -> bool:
    """Return true when the current options cannot start another job."""
    previous = session.get(LAST_JOB_SESSION_KEY)
    if not isinstance(previous, dict):
        return False
    previous_state = str(previous.get("state", ""))
    return (
        previous_state not in TERMINAL_JOB_STATES
        or not isinstance(request_nonce, str)
        or previous.get("request_nonce") == request_nonce
    )


def _store_job_marker(
    org_id: str, site_ids: list[str], request_nonce: object, state: str, upgrade_id: str | None
) -> None:
    """Store one owned organization job marker."""
    session[LAST_JOB_SESSION_KEY] = {
        "upgrade_id": upgrade_id,
        "org_id": org_id,
        "site_count": len(site_ids),
        "state": state,
        "request_nonce": request_nonce,
    }


def _call_submission(
    cloud_session: Any, org_id: str, site_ids: list[str], options: Mapping[str, Any]
) -> OrgUpgradeResult | tuple[Response, int]:
    """Call the service once and map local and unknown failures."""
    try:
        return upgrade_service().submit(cloud_session, org_id, request_for_service(site_ids, options))
    except ValueError as error:
        session.pop(LAST_JOB_SESSION_KEY, None)
        return json_error(BAD_REQUEST_STATUS, OPTIONS_INVALID, str(error))
    except Exception:
        logger.exception("The organization upgrade submission outcome is unknown")
        return json_error(
            SERVICE_UNAVAILABLE_STATUS,
            SUBMISSION_FAILED,
            "The cloud response is unknown. Reconcile job history before another submission.",
        )


def _finish_submission(
    result: OrgUpgradeResult, org_id: str, site_ids: list[str], request_nonce: object
) -> Response | tuple[Response, int]:
    """Validate the accepted result and store its job identifier."""
    refusal = result_error(result, SUBMISSION_FAILED)
    if refusal is not None:
        return refusal
    if result.upgrade_id is None:
        return json_error(
            BAD_GATEWAY_STATUS, SUBMISSION_FAILED, "The cloud returned no organization upgrade identifier."
        )
    _store_job_marker(org_id, site_ids, request_nonce, "submitted", result.upgrade_id)
    session.pop(OPTIONS_SESSION_KEY, None)
    session.pop(OPTIONS_ORG_SESSION_KEY, None)
    session.pop(OPTIONS_NONCE_SESSION_KEY, None)
    return next_page_answer(f"/upgrade/org/jobs/{result.upgrade_id}")


@org_upgrade_bp.post(SUBMIT_PATH)
@identity.require_session
def submit_upgrade() -> Response | tuple[Response, int]:
    """Submit one confirmed organization AP upgrade with no hidden retry."""
    if not writes_enabled():
        return json_error(
            SERVICE_UNAVAILABLE_STATUS,
            WRITE_DISABLED,
            "Organization upgrade writes stay disabled until the multi-site safety gates are complete.",
        )
    request_nonce = session.get(OPTIONS_NONCE_SESSION_KEY)
    if _submission_is_repeated(request_nonce):
        return json_error(
            CONFLICT_STATUS, ALREADY_SUBMITTED, "This confirmed request already started an organization upgrade."
        )
    if _confirmation_value() != "CONFIRM":
        return json_error(BAD_REQUEST_STATUS, CONFIRMATION_REQUIRED, CONFIRMATION_MESSAGE)
    context = active_context()
    options = stored_options()
    cloud_session = current_cloud_session()
    if context is None or not options or cloud_session is None:
        return json_error(BAD_REQUEST_STATUS, OPTIONS_INVALID, "The organization upgrade context is incomplete.")
    org_id, site_ids = context
    _store_job_marker(org_id, site_ids, request_nonce, "submission_unknown", None)
    result = _call_submission(cloud_session, org_id, site_ids, options)
    if not isinstance(result, OrgUpgradeResult):
        return result
    marker = session.get(LAST_JOB_SESSION_KEY)
    if isinstance(marker, dict) and result.upgrade_id is not None:
        marker["upgrade_id"] = result.upgrade_id
        session[LAST_JOB_SESSION_KEY] = marker
    return _finish_submission(result, org_id, site_ids, request_nonce)


@org_upgrade_bp.get(JOB_PAGE_PATH)
@identity.require_session
def job_page(upgrade_id: str) -> str | tuple[Response, int]:
    """Read and show the current organization upgrade state."""
    org_id = resolve_org(None)
    cloud_session = current_cloud_session()
    if org_id is None or cloud_session is None:
        return json_error(BAD_REQUEST_STATUS, STATUS_FAILED, "The organization upgrade context is incomplete.")
    try:
        result = upgrade_service().status(cloud_session, org_id, upgrade_id)
    except (TypeError, ValueError) as error:
        return json_error(BAD_REQUEST_STATUS, STATUS_FAILED, str(error))
    except Exception:
        logger.exception("The organization upgrade status read failed")
        return json_error(SERVICE_UNAVAILABLE_STATUS, STATUS_FAILED, "The cloud status read failed.")
    refusal = result_error(result, STATUS_FAILED)
    if refusal is not None:
        return refusal
    last = session.get(LAST_JOB_SESSION_KEY, {})
    site_count = (
        last.get("site_count", len(selected_site_ids())) if isinstance(last, dict) else len(selected_site_ids())
    )
    summary = status_summary(result)
    remember_job_state(org_id, upgrade_id, summary["status"])
    return render_page(
        PROGRESS_TEMPLATE,
        upgrade_id=upgrade_id,
        site_count=site_count,
        status=summary,
        poll_interval_seconds=current_app.config.get("POLL_INTERVAL_SECONDS", 30),
    )


@org_upgrade_bp.get(STATUS_PATH)
@identity.require_session
def upgrade_status(upgrade_id: str) -> tuple[Response, int]:
    """Return the normalized organization job status for browser polling."""
    org_id = resolve_org(None)
    cloud_session = current_cloud_session()
    if org_id is None or cloud_session is None:
        return json_error(BAD_REQUEST_STATUS, STATUS_FAILED, "The organization upgrade context is incomplete.")
    try:
        result = upgrade_service().status(cloud_session, org_id, upgrade_id)
    except (TypeError, ValueError) as error:
        return json_error(BAD_REQUEST_STATUS, STATUS_FAILED, str(error))
    except Exception:
        logger.exception("The organization upgrade status read failed")
        return json_error(SERVICE_UNAVAILABLE_STATUS, STATUS_FAILED, "The cloud status read failed.")
    refusal = result_error(result, STATUS_FAILED)
    if refusal is not None:
        return refusal
    summary = status_summary(result)
    remember_job_state(org_id, upgrade_id, summary["status"])
    return jsonify({"upgrade_id": upgrade_id, **summary}), OK_STATUS


def _cancel_context(upgrade_id: str) -> tuple[str, Any] | tuple[Response, int]:
    """Return the owned organization and session for cancellation."""
    org_id = resolve_org(None)
    cloud_session = current_cloud_session()
    last = session.get(LAST_JOB_SESSION_KEY)
    owns_job = isinstance(last, dict) and last.get("upgrade_id") == upgrade_id and last.get("org_id") == org_id
    if not owns_job:
        return json_error(CONFLICT_STATUS, JOB_NOT_OWNED, "This browser session did not start that organization job.")
    if org_id is None or cloud_session is None:
        return json_error(BAD_REQUEST_STATUS, CANCEL_FAILED, "The organization upgrade context is incomplete.")
    return org_id, cloud_session


def _call_cancellation(cloud_session: Any, org_id: str, upgrade_id: str) -> OrgUpgradeResult | tuple[Response, int]:
    """Call cancellation once and map local and unknown failures."""
    try:
        return upgrade_service().cancel(cloud_session, org_id, upgrade_id)
    except (TypeError, ValueError) as error:
        return json_error(BAD_REQUEST_STATUS, CANCEL_FAILED, str(error))
    except Exception:
        logger.exception("The organization upgrade cancellation outcome is unknown")
        return json_error(
            SERVICE_UNAVAILABLE_STATUS,
            CANCEL_FAILED,
            "The cancellation outcome is unknown. Read the job status before another request.",
        )


@org_upgrade_bp.post(CANCEL_PATH)
@identity.require_session
def cancel_upgrade(upgrade_id: str) -> tuple[Response, int]:
    """Request best-effort cancellation without claiming rollback."""
    if not writes_enabled():
        return json_error(
            SERVICE_UNAVAILABLE_STATUS,
            WRITE_DISABLED,
            "Organization upgrade writes stay disabled until the multi-site safety gates are complete.",
        )
    if _confirmation_value() != "CANCEL":
        return json_error(BAD_REQUEST_STATUS, CONFIRMATION_REQUIRED, "Type CANCEL before you request cancellation.")
    context = _cancel_context(upgrade_id)
    if not isinstance(context[0], str):
        return context
    org_id, cloud_session = context
    result = _call_cancellation(cloud_session, org_id, upgrade_id)
    if not isinstance(result, OrgUpgradeResult):
        return result
    refusal = result_error(result, CANCEL_FAILED)
    if refusal is not None:
        return refusal
    if request.accept_mimetypes.best_match(("application/json", "text/html")) == "text/html":
        return next_page_answer(f"/upgrade/org/jobs/{upgrade_id}")
    return jsonify({"upgrade_id": upgrade_id, "cancel_requested": True}), OK_STATUS
