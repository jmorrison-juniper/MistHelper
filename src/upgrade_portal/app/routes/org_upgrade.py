"""The organization AP upgrade options, confirmation, and status routes.

Why:
    The live portal keeps the single-site run routes unchanged. These routes
    add the organization job as a second mode after the organization choice.
    The browser never receives a Mist token or a raw SDK object.
"""

from __future__ import annotations

import json
import logging
import secrets
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from flask import Blueprint, Response, current_app, jsonify, request, session

from ....firmware.aggregate_upgrade_service import AggregateBuildInput, AggregateUpgradeService
from ....firmware.org_upgrade_body import OrgUpgradeBody
from ....firmware.org_upgrade_service import OrgUpgradeResult, OrgUpgradeService
from ...runtime import identity, lock
from ...upgrade.options import build_options, build_options_record, build_options_view
from ..factory import json_error
from . import select as select_routes
from . import upgrade as upgrade_routes
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
AGGREGATE_SERVICE_CONFIG_KEY = "AGGREGATE_UPGRADE_SERVICE"
OPTIONS_VIEW_CONFIG_KEY = "ORG_UPGRADE_OPTIONS_VIEW"
OPTIONS_BUILDER_CONFIG_KEY = "ORG_UPGRADE_OPTIONS_BUILDER"
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


@dataclass(frozen=True, slots=True)
class SubmissionContext:
    """Hold the validated values for one confirmed submission."""

    cloud_session: Any  # Keep the signed operator session.
    org_id: str  # Keep the selected organization.
    site_ids: list[str]  # Keep the validated site selection.
    options: dict[str, Any]  # Keep the confirmed option record.
    request_nonce: object  # Keep the replay-prevention value.


def upgrade_service() -> Any:
    """Return the injected service or the production service class."""
    return current_app.config.get(SERVICE_CONFIG_KEY, OrgUpgradeService)


def aggregate_service() -> AggregateUpgradeService:
    """Return the injected aggregate service or build the production service."""
    configured = current_app.config.get(AGGREGATE_SERVICE_CONFIG_KEY)  # A test can replace the whole boundary.
    if configured is not None:  # Keep the injected stand-in unchanged.
        return configured
    return AggregateUpgradeService(org_service=upgrade_service())  # Reuse the injected AP service too.


def aggregate_options_view(cloud_session: Any, org_id: str, site_id: str) -> dict[str, Any]:
    """Return the injected multi-site device view or the production view."""
    builder = current_app.config.get(OPTIONS_VIEW_CONFIG_KEY, build_options_view)  # Tests reach no cloud.
    return dict(builder(cloud_session, org_id, site_id))  # Detach the view before template use.


def aggregate_options_record(
    cloud_session: Any,
    org_id: str,
    site_id: str,
    body: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the injected multi-site option record or the production record."""
    builder = current_app.config.get(OPTIONS_BUILDER_CONFIG_KEY, build_options_record)  # Tests reach no cloud.
    return dict(builder(cloud_session, org_id, site_id, body))  # Detach the stored values.


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
    source = _request_source()  # Read one request representation.
    request_body = _base_request_options(source)  # Normalize the shared AP fields.
    _add_start_option(request_body, source)  # Add the optional schedule.
    selected = _selected_types(source)  # Read all selected device families.
    if selected is not None:  # The legacy AP-only request omits this field.
        _add_device_options(request_body, source, selected)  # Add the multi-device controls.
    return request_body  # Return one validated input shape.


def _request_source() -> Mapping[str, Any]:
    """Return the JSON object or form collection for this request."""
    payload: Any = request.get_json(silent=True)  # Read JSON without raising for a form request.
    return payload if isinstance(payload, Mapping) else request.form  # Prefer a valid JSON object.


def _base_request_options(source: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize the option fields that both request forms share."""
    version = str(source.get("version", "")).strip()  # Read the legacy AP version.
    strategy = str(source.get("strategy", "canary")).strip()  # Read the rollout strategy.
    body: dict[str, Any] = {"versions": [{"firmware_type": "ap", "version": version}], "strategy": strategy}
    if strategy != "big_bang":  # Big-bang upgrades do not use a failure threshold.
        body["max_failure_percentage"] = int(str(source.get("max_failure_percentage", "5")).strip())
    if strategy == "canary":  # Canary upgrades require phase percentages.
        body["canary_phases"] = _phase_values(source)  # Preserve the submitted phase order.
    return body  # The caller adds optional multi-device fields.


def _phase_values(source: Mapping[str, Any]) -> list[int]:
    """Return the submitted canary phase percentages."""
    text = str(source.get("canary_phases", "")).strip()  # Read the comma-separated field.
    return [int(part.strip()) for part in text.split(",") if part.strip()] if text else []  # Parse each value.


def _add_start_option(body: dict[str, Any], source: Mapping[str, Any]) -> None:
    """Add the optional start time as epoch seconds."""
    start_text = str(source.get("start_time", "")).strip()  # Read the local date and time.
    if not start_text:  # Omit an empty schedule.
        return  # Keep an immediate start.
    start = datetime.fromisoformat(start_text)  # Parse the submitted ISO value.
    start = start.replace(tzinfo=UTC) if start.tzinfo is None else start  # Give a naive value the portal zone.
    body["start_time"] = int(start.timestamp())  # Store the same epoch format as the service.


def _selected_types(source: Mapping[str, Any]) -> list[str] | None:
    """Return selected device families or None for a legacy request."""
    selected = source.get("selected_types")  # JSON sends a list.
    if not isinstance(selected, list) and hasattr(source, "getlist"):  # A form sends repeated fields.
        selected = source.getlist("selected_types")  # Read every checked value.
    if not isinstance(selected, list):  # The legacy AP-only request omits the field.
        return None  # Keep the legacy request path.
    return [str(value) for value in selected]  # Normalize each family name.


def _add_device_options(body: dict[str, Any], source: Mapping[str, Any], selected: list[str]) -> None:
    """Add fields that the multi-device workflow supports."""
    legacy_version = str(body["versions"][0]["version"])  # Preserve the AP fallback for old forms.
    body["selected_types"] = selected  # Keep every checked device family.
    body["version_ap"] = str(source.get("version_ap", legacy_version)).strip()  # Read the AP target.
    body["version_switch"] = str(source.get("version_switch", "")).strip()  # Read the switch target.
    body["version_gateway"] = str(source.get("version_gateway", "")).strip()  # Read the gateway target.
    body["reboot"] = _yes_value(source.get("reboot", "yes"))  # Preserve the reboot choice.
    body["junos_file_action"] = _yes_value(source.get("junos_file_action", "yes"))  # Preserve the Junos action.
    body["force"] = str(source.get("force", "")).lower() in ("1", "true", "yes", "on")  # Preserve force.


def _yes_value(value: object) -> bool:
    """Return true only for the form yes value."""
    return str(value).lower() == "yes"  # Match the existing checkbox semantics.


def _site_option_body(options: Mapping[str, Any], targets: list[dict[str, str]]) -> dict[str, Any]:
    """Build the single-site option body that the proven mapper validates."""
    return {
        "targets": targets,
        "selected_types": list(options["selected_types"]),
        "strategy": options.get("strategy", "big_bang"),
        "reboot": options.get("reboot", True),
        "junos_file_action": options.get("junos_file_action", True),
        "force": options.get("force", False),
        "start_time": options.get("start_time"),
        "canary_phases": ",".join(str(value) for value in options.get("canary_phases", [])),
        "max_failure_percentage": options.get("max_failure_percentage"),
    }


def _aggregate_option_record(org_id: str, site_ids: list[str], options: Mapping[str, Any]) -> dict[str, Any]:
    """Build every explicit target through the existing site option mapper."""
    cloud_session = current_cloud_session()  # The inventory and version reads use the signed operator session.
    if cloud_session is None:  # No cloud scope can validate a target.
        raise ValueError("The organization upgrade context is incomplete.")
    selected = _selected_families(options)  # Keep the checked family order.
    all_targets: list[dict[str, Any]] = []  # The operation stores every selected device explicitly.
    common_options: dict[str, Any] | None = None  # Every site uses the same visible controls.
    for site_id in site_ids:  # Reuse the single-site inventory and compatibility rules for each site.
        built = _site_option_record(cloud_session, org_id, site_id, options, selected)  # Validate one site.
        all_targets.extend({**dict(target), "site_id": site_id} for target in built.get("targets", []))
        common_options = dict(built.get("options", {}))
    return _complete_aggregate_options(all_targets, common_options, selected)  # Validate the combined record.


def _selected_families(options: Mapping[str, Any]) -> tuple[str, ...]:
    """Return the selected device families in their submitted order."""
    return tuple(str(value) for value in options.get("selected_types", ()))  # Normalize each family name.


def _complete_aggregate_options(
    targets: list[dict[str, Any]],
    options: dict[str, Any] | None,
    selected: tuple[str, ...],
) -> dict[str, Any]:
    """Validate and return the combined site option record."""
    if not targets:  # A confirmed request must name a real device.
        raise ValueError("Choose a target version for at least one supported device type.")
    if options is None:  # Every selected site must produce the common option record.
        raise ValueError("Choose a target version for at least one supported device type.")
    return {"targets": targets, "options": options, "selected_types": list(selected)}  # Return detached values.


def _site_option_record(
    cloud_session: Any,
    org_id: str,
    site_id: str,
    options: Mapping[str, Any],
    selected: tuple[str, ...],
) -> dict[str, Any]:
    """Build one site's options through the existing option mapper."""
    logger.info("Read aggregate upgrade options for site %s", site_id)  # Log before the inventory read.
    view = aggregate_options_view(cloud_session, org_id, site_id)  # Read the approved site inventory.
    rows = _selected_target_rows(view, options, selected)  # Select explicit targets with a chosen version.
    logger.debug("The site option view selected %s target(s)", len(rows))  # Log after the transformation.
    logger.info("Validate aggregate upgrade options for site %s", site_id)  # Log before validation.
    built = aggregate_options_record(cloud_session, org_id, site_id, _site_option_body(options, rows))
    logger.debug("The site option record holds %s target(s)", len(built.get("targets", [])))  # Log after validation.
    return built  # The caller combines the detached site records.


def _selected_target_rows(
    view: Mapping[str, Any],
    options: Mapping[str, Any],
    selected: tuple[str, ...],
) -> list[dict[str, str]]:
    """Return explicit targets for selected families that have a version."""
    return [  # Keep the inventory order from the existing option view.
        {"mac": str(row["mac"]), "version_target": str(options.get(f"version_{row['device_type']}", ""))}
        for row in view.get("targets", [])  # Inspect each device in the selected site.
        if str(row.get("device_type", "")) in selected  # Keep only checked families.
        and options.get(f"version_{row['device_type']}")  # Require a target version for the family.
    ]


def stored_options() -> dict[str, Any]:
    """Return options only when they belong to the selected organization."""
    if session.get(OPTIONS_ORG_SESSION_KEY) != resolve_org(None):
        return {}
    value: Any = session.get(OPTIONS_SESSION_KEY)
    return dict(value) if isinstance(value, dict) else {}


def request_for_service(site_ids: list[str], options: Mapping[str, Any]) -> dict[str, Any]:
    """Build the validated service request from session state."""
    supported = {key: value for key, value in options.items() if key in OrgUpgradeBody.FIELDS}
    request_body = {**supported, "site_ids": list(site_ids)}
    return OrgUpgradeBody.build(request_body)


def options_view(options: Mapping[str, Any]) -> dict[str, Any]:
    """Return form values from the validated service option shape."""
    first = _first_version(options.get("versions"))  # Read the legacy AP version record.
    return {  # Return the existing template field names.
        "version": options.get("version_ap", first.get("version", "")),
        "strategy": options.get("strategy", "canary"),
        "canary_phases": _phase_text(options.get("canary_phases")),
        "max_failure_percentage": options.get("max_failure_percentage", 5),
        "start_time": _start_text(options.get("start_time")),
    }


def _first_version(value: object) -> Mapping[str, Any]:
    """Return the first valid version record."""
    if not isinstance(value, list) or not value:  # Reject a missing or empty version list.
        return {}  # Keep the existing empty fallback.
    return value[0] if isinstance(value[0], Mapping) else {}  # Return only an object record.


def _phase_text(value: object) -> str:
    """Return the comma-separated canary phases."""
    if not isinstance(value, list):  # Reject a malformed stored phase value.
        return ""  # Keep the existing empty fallback.
    return ",".join(str(item) for item in value)  # Preserve the stored phase order.


def _start_text(value: object) -> str:
    """Return the local form value for an epoch start time."""
    if type(value) is not int:  # Reject bool and non-integer stored values.
        return ""  # Keep the existing empty fallback.
    return datetime.fromtimestamp(value, UTC).strftime("%Y-%m-%dT%H:%M")  # Preserve the existing UTC display.


def _device_targets(entries: Sequence[Mapping[str, Any]]) -> tuple[Any, ...]:
    """Build the immutable target records with their original site identities."""
    from ....firmware.upgrade_service import DeviceTarget  # Keep the route import list below the project limit.

    return tuple(
        DeviceTarget(
            mac=str(entry["mac"]),
            name=str(entry.get("name", "")),
            device_type=str(entry["device_type"]),
            model=str(entry.get("model", "")),
            version_before=str(entry.get("version_before", "")),
            version_target=str(entry["version_target"]),
            site_id=str(entry["site_id"]),
        )
        for entry in entries
    )


def _owner_key() -> str:
    """Return the signed owner key of the current operator."""
    record = identity.current_session()  # The server-side session owns the browser identity.
    return "" if record is None else record.owner.key  # An empty key cannot own a persisted operation.


def _write_operation(record: MutableMapping[str, Any]) -> None:
    """Write one aggregate record or raise a visible persistence failure."""
    logger.info("Write aggregate upgrade %s", record.get("operation_id", ""))  # Log before the action.
    if not upgrade_routes.run_store().write_run(dict(record)):  # The durable store must accept every state.
        raise RuntimeError("The portal could not persist the aggregate upgrade.")
    logger.debug("The aggregate upgrade %s is durable", record.get("operation_id", ""))  # Log after the action.


def _read_operation(operation_id: str) -> dict[str, Any] | None:
    """Read one durable aggregate operation."""
    record = upgrade_routes.run_store().read_run(operation_id)  # The store, not the browser, owns the operation.
    return dict(record) if isinstance(record, Mapping) and record.get("operation_id") == operation_id else None


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
    for entry in _mapping_entries(entries):  # Ignore malformed site rows.
        row, counts, site_has_targets = _site_summary(entry)
        rows.append(row)
        totals = [current + value for current, value in zip(totals, counts, strict=True)]
        has_targets = has_targets or site_has_targets
    return rows, (totals[0], totals[1], totals[2]), has_targets


def _mapping_entries(entries: object) -> tuple[Mapping[str, object], ...]:
    """Return only mapping entries from a possible site list."""
    if not isinstance(entries, list):  # Reject a malformed site collection.
        return ()  # Give the summary loop a stable empty input.
    return tuple(entry for entry in entries if isinstance(entry, Mapping))  # Keep valid rows in order.


def status_summary(result: OrgUpgradeResult) -> dict[str, Any]:
    """Build job totals from the target arrays of each site upgrade."""
    data = dict(result.data)
    entries = data.get("site_upgrades", data.get("upgrades", []))
    sites, counts, has_site_targets = _site_summaries(entries)
    root_targets = data.get("targets")
    if not has_site_targets and isinstance(root_targets, Mapping):
        counts = _target_counts(root_targets)
    root_status = str(data.get("status", "")).lower()  # Prefer the explicit aggregate state.
    return {
        "status": root_status or _derived_ap_status(sites),  # Derive from all site entries when root is absent.
        "current_phase": data.get("current_phase"),
        "total": counts[0],
        "upgraded_count": counts[1],
        "failed_count": counts[2],
        "site_upgrades": sites,
    }


def _derived_ap_status(sites: Sequence[Mapping[str, Any]]) -> str:
    """Derive one AP display state from all normalized site entries."""
    states = [str(site.get("status", "unknown")).lower() for site in sites]  # Preserve every cloud state.
    return AggregateUpgradeService._combined_site_status(states)  # Apply the aggregate mixed-state rules.


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
    """Show the multi-device organization upgrade options."""
    context = active_context()
    if context is None:
        return json_error(BAD_REQUEST_STATUS, MODE_REQUIRED, MODE_REQUIRED_MESSAGE)
    org_id, site_ids = context
    rows = selected_rows(org_id, site_ids)
    if not rows:
        return json_error(NOT_FOUND_STATUS, SITES_REQUIRED, SITES_REQUIRED_MESSAGE)
    cloud_session = current_cloud_session()  # The options page reads the same inventory as the single-site page.
    device_views = []  # Keep one visible device list for each selected site.
    if cloud_session is not None:  # A signed session normally supplies the cloud connection.
        for row in rows:  # Each site keeps its identity beside its devices.
            view = aggregate_options_view(cloud_session, org_id, str(row["site_id"]))
            device_views.append({"site": row, **view})
    return render_page(
        OPTIONS_TEMPLATE,
        sites=rows,
        device_views=device_views,
        options=options_view(stored_options()),
    )


@org_upgrade_bp.post(OPTIONS_API_PATH)
@identity.require_session
def save_options() -> Response | tuple[Response, int]:
    """Validate the options and open the familiar confirmation step."""
    context = active_context()  # Read the signed organization and site selection.
    if context is None:  # Reject a request outside the multi-site workflow.
        return json_error(BAD_REQUEST_STATUS, MODE_REQUIRED, MODE_REQUIRED_MESSAGE)
    org_id, site_ids = context  # Use only the validated active context.
    try:  # Map option and storage failures to the existing response.
        options, nonce = _validated_saved_options(org_id, site_ids)  # Build the legacy or aggregate record.
    except (TypeError, ValueError, OverflowError, RuntimeError) as error:
        return json_error(BAD_REQUEST_STATUS, OPTIONS_INVALID, str(error))
    session[OPTIONS_SESSION_KEY] = options  # Keep the validated display options in the signed session.
    session[OPTIONS_ORG_SESSION_KEY] = org_id  # Bind the options to the selected organization.
    session[OPTIONS_NONCE_SESSION_KEY] = nonce  # Bind submission to this confirmation.
    return next_page_answer(CONFIRM_PAGE_PATH)  # Open the typed confirmation step.


def _validated_saved_options(org_id: str, site_ids: list[str]) -> tuple[dict[str, Any], str]:
    """Build validated options and the nonce that protects submission."""
    options = read_options()  # Normalize the submitted request fields.
    if "selected_types" not in options:  # Keep an older AP-only client compatible.
        request_for_service(site_ids, options)  # Validate the narrow organization body.
        return options, secrets.token_urlsafe(24)  # Give the legacy request its replay nonce.
    return _aggregate_saved_options(org_id, site_ids, options)  # Build the durable multi-device plan.


def _aggregate_saved_options(
    org_id: str,
    site_ids: list[str],
    options: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    """Build and persist one confirmed aggregate operation."""
    aggregate = _aggregate_option_record(org_id, site_ids, options)  # Validate each explicit target.
    rows = selected_rows(org_id, site_ids)  # Preserve approved site names with the operation.
    choices = build_options(aggregate["options"], now=None)  # Reuse the proven option mapping.
    request_data = AggregateBuildInput(  # Group the confirmed build values below the parameter limit.
        owner=_owner_key(),  # Bind the operation to the signed operator.
        org_id=org_id,  # Bind every child to the selected organization.
        sites=rows,  # Keep only approved sites.
        targets=_device_targets(aggregate["targets"]),  # Keep every selected device explicit.
        options=choices,  # Keep the validated service options.
        request_nonce=secrets.token_urlsafe(24),  # Prevent a repeated submission.
    )
    logger.info("Build the durable aggregate upgrade plan for organization %s", org_id)  # Log before the build.
    operation = aggregate_service().build(request_data)  # Build every child without a cloud write.
    logger.debug("The aggregate plan holds %s child job(s)", len(operation["children"]))  # Log after the build.
    _write_operation(operation)  # Persist the complete plan before confirmation.
    options["operation_id"] = operation["operation_id"]  # Keep only the durable identity in the browser.
    options["target_count"] = len(aggregate["targets"])  # Keep a small confirmation value.
    return options, str(operation["request_nonce"])  # Return the durable replay nonce.


@org_upgrade_bp.get(CONFIRM_PAGE_PATH)
@identity.require_session
def confirm_page() -> str | tuple[Response, int]:
    """Show the final impact summary and typed confirmation field."""
    context = active_context()  # Read the signed organization and site selection.
    options = stored_options()  # Read options only for the selected organization.
    if context is None or not options:  # Require a complete confirmed context.
        return json_error(BAD_REQUEST_STATUS, OPTIONS_INVALID, "Save valid upgrade options before confirmation.")
    org_id, site_ids = context  # Use only the validated active context.
    rows = selected_rows(org_id, site_ids)  # Recheck site ownership before display.
    if not rows:  # Do not show an operation for missing or foreign sites.
        return json_error(NOT_FOUND_STATUS, SITES_REQUIRED, SITES_REQUIRED_MESSAGE)
    target_count, families = _confirmation_targets(options)  # Read only the durable aggregate child summary.
    return render_page(  # Render the existing typed confirmation page.
        CONFIRM_TEMPLATE,  # Keep the existing template.
        org_name=org_display_name(org_id),  # Show the selected organization.
        site_count=len(rows),  # Show the selected site count.
        device_count=target_count or _site_device_count(rows),  # Keep the AP-only count fallback.
        device_families=families,  # Show each planned family.
        options=options_view(options),  # Show the confirmed choices.
        writes_enabled=writes_enabled(),  # Keep the deployment write gate visible.
    )


def _confirmation_targets(options: Mapping[str, Any]) -> tuple[int, list[str]]:
    """Return the aggregate target count and device families."""
    operation_id = str(options.get("operation_id", ""))  # Read only the durable identity from the session.
    operation = _read_operation(operation_id) if operation_id else None  # Read the confirmed plan from storage.
    children = _mapping_children(operation)  # Ignore malformed child rows.
    return _aggregate_target_count(children), _aggregate_families(children)  # Build the display values.


def _mapping_children(record: Mapping[str, Any] | None) -> tuple[Mapping[str, Any], ...]:
    """Return valid child records from one aggregate operation."""
    entries = record.get("children", []) if record is not None else []  # Read no child from browser state.
    return tuple(child for child in entries if isinstance(child, Mapping))  # Ignore malformed rows.


def _aggregate_target_count(children: Sequence[Mapping[str, Any]]) -> int:
    """Return the number of explicit aggregate targets."""
    return sum(len(child.get("target_ids", [])) for child in children)  # Count each durable target once.


def _aggregate_families(children: Sequence[Mapping[str, Any]]) -> list[str]:
    """Return the sorted device families of aggregate children."""
    return sorted({str(child.get("device_family", "")) for child in children})  # Keep stable display order.


def _site_device_count(rows: Sequence[Mapping[str, Any]]) -> int:
    """Return the device count from the selected site rows."""
    return sum(int(row.get("device_count", 0)) for row in rows)  # Preserve the existing site total.


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


def _owned_operation(options: Mapping[str, Any], org_id: str) -> dict[str, Any] | None:
    """Return the durable operation only when this operator owns its scope."""
    operation_id = str(options.get("operation_id", ""))  # The saved options carry the durable identity.
    operation = _read_operation(operation_id) if operation_id else None  # Read no child from the browser session.
    if operation is None or operation.get("owner") != _owner_key() or operation.get("org_id") != org_id:
        return None  # Ownership and organization mismatches reveal no operation.
    return operation  # The caller can now read or change this operation.


def _operation_matches_context(operation: Mapping[str, Any], context: SubmissionContext) -> bool:
    """Return true when the durable plan matches the complete active context."""
    operation_id = str(context.options.get("operation_id", ""))  # Read the browser's durable plan identity.
    return (  # Require exact identity, organization, ordered sites, and nonce.
        operation.get("operation_id") == operation_id  # Match the durable operation identity.
        and operation.get("org_id") == context.org_id  # Match the selected organization.
        and list(operation.get("site_ids", [])) == context.site_ids  # Match the exact selected site order.
        and operation.get("request_nonce") == context.request_nonce  # Match the confirmation nonce.
    )


def _cas_operation(record: MutableMapping[str, Any], replacement: Mapping[str, Any]) -> bool:
    """Replace one aggregate record through the actual run-store seam."""
    expected = record.get("record_version")  # Read the version of the current durable snapshot.
    if type(expected) is not int:  # A malformed version cannot coordinate a destructive action.
        return False  # Fail closed before any cloud write.
    candidate = dict(replacement)  # Detach the replacement from the caller.
    candidate["record_version"] = expected + 1  # Advance exactly one application version.
    store = upgrade_routes.run_store()  # Use the same durable seam as all run routes.
    changed = store.compare_and_set_run(str(record["run_id"]), expected, candidate)  # Apply one atomic CAS.
    if changed:  # Keep the caller synchronized only after the durable replacement succeeds.
        record.clear()  # Remove the stale snapshot.
        record.update(candidate)  # Continue with the accepted durable version.
    return changed  # Report the exact compare-and-set result.


def _acquire_operation_locks(
    operation: MutableMapping[str, Any],
    org_id: str,
    site_ids: Sequence[str],
) -> tuple[Response, int] | None:
    """Acquire and store every site lock for one aggregate operation."""
    owner = identity.current_owner()  # Bind locks to the authenticated operator and browser.
    if owner is None:  # A missing owner cannot hold a production lock.
        return json_error(CONFLICT_STATUS, JOB_NOT_OWNED, "The signed operator identity is unavailable.")
    operation_id = str(operation.get("operation_id", ""))  # Bind every lock to one aggregate identity.
    client = select_routes.lock_client()  # Use the configured production or test lock client.
    for site_id in site_ids:  # Acquire each selected site before any cloud write.
        held = lock.read_lock(org_id, site_id, client)  # Detect a same-owner lock bound to another run.
        if held is not None and held.held_by(owner) and held.run_id != operation_id:  # Refuse unsafe reuse.
            return json_error(CONFLICT_STATUS, "site_lock_wrong_run", "Your existing site lock belongs to another run.")
        request_record = lock.LockRequest(org_id, site_id, owner, operation_id)  # Build the existing lock request.
        logger.info("Acquire site %s for aggregate upgrade %s", site_id, operation_id)  # Log before acquisition.
        try:  # Lock writes fail closed and use no memory fallback.
            grant = lock.acquire_site_lock(request_record, client)  # Atomically acquire or resume this run lock.
        except lock.SiteLockError as fault:  # Map the existing lock error to a safe API response.
            status = (
                SERVICE_UNAVAILABLE_STATUS if isinstance(fault, lock.LockStoreUnreachableError) else CONFLICT_STATUS
            )
            return json_error(status, fault.code, str(fault))  # Preserve the lock module's code and message.
        replacement = dict(operation)  # Build a detached CAS replacement.
        stored_locks = dict(replacement.get("site_locks", {}))  # Preserve locks acquired for earlier sites.
        stored_locks[site_id] = grant.record.to_record()  # Store the JSON-safe lock record.
        replacement["site_locks"] = stored_locks  # Attach the updated lock map.
        if not _cas_operation(operation, replacement):  # Persist this lock before the next acquisition.
            return json_error(SERVICE_UNAVAILABLE_STATUS, SUBMISSION_FAILED, "The portal could not store a site lock.")
        logger.debug("Aggregate upgrade %s stores the lock for site %s", operation_id, site_id)  # Log after CAS.
    return None  # Every selected site lock is durable and bound to this operation.


def _refresh_child_locks(operation: Mapping[str, Any], child: Mapping[str, Any]) -> None:
    """Refresh every site lock that one child requires."""
    owner = identity.current_owner()  # Revalidate against the current authenticated owner.
    if owner is None:  # A missing identity cannot continue a destructive action.
        raise lock.LockLostError("The signed operator identity is unavailable.")  # Fail closed.
    operation_id = str(operation.get("operation_id", ""))  # Read the required run binding.
    stored = operation.get("site_locks")  # Read the durable lock map.
    if not isinstance(stored, Mapping):  # A missing map cannot prove ownership.
        raise lock.LockLostError("The aggregate operation has no stored site locks.")  # Fail closed.
    for site_id in _child_site_ids(child):  # Refresh each site immediately before this child claim.
        value = stored.get(site_id)  # Read the JSON-safe stored lock record.
        saved = lock.LockRecord.from_json(json.dumps(value)) if isinstance(value, Mapping) else None  # Rebuild it.
        if saved is None or not saved.held_by(owner) or saved.run_id != operation_id:  # Validate identity and run.
            raise lock.LockLostError("The stored site lock does not match this aggregate operation.")  # Stop.
        key = lock.build_key(str(operation.get("org_id", "")), site_id)  # Build the existing Redis key.
        logger.info("Refresh site %s for aggregate child %s", site_id, child.get("child_id", ""))  # Log before.
        lock.refresh_site_lock(key, saved, select_routes.lock_client())  # Use the existing atomic refresh API.
        logger.debug("The aggregate child %s still holds site %s", child.get("child_id", ""), site_id)  # Log after.


def _child_site_ids(child: Mapping[str, Any]) -> tuple[str, ...]:
    """Return every site lock that one child requires."""
    body = child.get("body")  # The organization AP child stores its selected sites in the body.
    if child.get("route") == "upgradeOrgDevices" and isinstance(body, Mapping):  # Read AP site scope.
        values = body.get("site_ids", [])  # Preserve the confirmed site order.
        return tuple(str(value) for value in values) if isinstance(values, list) else ()  # Normalize valid sites.
    site_id = str(child.get("site_id", ""))  # Site and SSR children hold one site identity.
    return (site_id,) if site_id else ()  # A missing site causes no false lock validation.


SETTLED_OPERATION_STATES = frozenset(  # States that end every destructive child action of one operation.
    {"completed", "cancelled", "failed", "attention_required"}
)


def _release_operation_locks(operation: MutableMapping[str, Any]) -> None:
    """Release every stored site lock after one operation settles.

    Why:
        `contracts/site-lock.md` releases a site when its run ends. An
        operation that keeps its locks would block every later capture and
        every later upgrade at the same site.
    """
    stored = operation.get("site_locks")  # Read the durable lock map of this operation.
    if not isinstance(stored, Mapping) or not stored:  # An empty map needs no release.
        return  # The operation holds no site.
    if not _operation_is_settled(operation):  # Keep the locks while a child can still write firmware.
        return  # Another request releases the locks after the work ends.
    org_id = str(operation.get("org_id", ""))  # Build each key inside the approved organization.
    for site_id, value in list(stored.items()):  # Release every site that this operation holds.
        _release_one_lock(org_id, str(site_id), value)  # Preserve the other releases after one failure.
    replacement = dict(operation)  # Build a detached compare-and-set replacement.
    replacement["site_locks"] = {}  # The settled operation holds no site.
    _cas_operation(operation, replacement)  # Persist the released state without hiding a lost race.


def _operation_is_settled(operation: Mapping[str, Any]) -> bool:
    """Return true when the portal sends no further write for one operation."""
    if str(operation.get("state", "")) in SETTLED_OPERATION_STATES:  # A final state ends every child action.
        return True  # The operation needs no site.
    cancellation = operation.get("cancellation")  # Read the durable cancellation marker.
    return isinstance(cancellation, Mapping) and cancellation.get("requested") is True  # A stop ends the work.


def _release_one_lock(org_id: str, site_id: str, value: object) -> None:
    """Release one stored site lock and keep a failure visible."""
    saved = lock.LockRecord.from_json(json.dumps(value)) if isinstance(value, Mapping) else None  # Rebuild it.
    if saved is None:  # A damaged record names no token, so no safe release exists.
        logger.warning("The aggregate operation holds no readable lock for site %s", site_id)  # Name the gap.
        return  # The lease then expires on its own.
    logger.info("Release site %s after the aggregate operation settled", site_id)  # Log before the release.
    try:  # The compare and the delete run as one step, so no release frees another operator.
        lock.release_site_lock(lock.build_key(org_id, site_id), saved, select_routes.lock_client())
    except lock.SiteLockError as fault:  # A takeover or an unreachable store must not stop the other releases.
        logger.warning("The release of site %s reported %s", site_id, fault.code)  # Name the safe code only.
        return  # The remaining sites still receive a release.
    logger.debug("The aggregate operation released site %s", site_id)  # Log after the release.


def _submit_aggregate(
    cloud_session: Any,
    operation: MutableMapping[str, Any],
) -> Response | tuple[Response, int]:
    """Submit every child through the aggregate boundary."""
    site_ids = [str(value) for value in operation.get("site_ids", [])]  # Read the durable lock scope.
    refusal = _acquire_operation_locks(operation, str(operation.get("org_id", "")), site_ids)  # Lock all sites.
    if refusal is not None:  # Stop before the parent or child claim.
        return refusal  # Preserve the existing lock error response.
    try:  # The service persists before and after every destructive action.
        aggregate_service().submit(  # Submit through atomic claims and immediate lock refreshes.
            cloud_session,
            operation,
            upgrade_routes.run_store(),
            _refresh_child_locks,
        )
    except ValueError as error:  # A replay or a malformed plan is a conflict.
        return json_error(CONFLICT_STATUS, ALREADY_SUBMITTED, str(error))
    except Exception:
        logger.exception("The aggregate upgrade submission outcome is unknown")
        return json_error(
            SERVICE_UNAVAILABLE_STATUS,
            SUBMISSION_FAILED,
            "One or more child outcomes are unknown. Read the operation before another action.",
        )
    _release_operation_locks(operation)  # Free every site when no child can still write firmware.
    return next_page_answer(f"/upgrade/org/jobs/{operation['operation_id']}")  # Show one seamless operation.


@org_upgrade_bp.post(SUBMIT_PATH)
@identity.require_session
def submit_upgrade() -> Response | tuple[Response, int]:
    """Submit one confirmed organization AP upgrade with no hidden retry."""
    request_nonce = session.get(OPTIONS_NONCE_SESSION_KEY)  # Read the confirmation replay value.
    refusal = _submission_guard(request_nonce)  # Apply write, replay, and typed confirmation gates.
    if refusal is not None:  # Stop before any cloud or storage action.
        return refusal  # Preserve the existing error response.
    loaded = _load_submission_context(request_nonce)  # Validate organization, sites, session, and locks.
    if not isinstance(loaded, SubmissionContext):  # A failed safeguard returns its existing response.
        return loaded  # Stop before any destructive action.
    operation = _owned_operation(loaded.options, loaded.org_id)  # Read an owned durable plan only.
    if operation is not None and _operation_matches_context(operation, loaded):  # Require the exact durable plan.
        return _submit_aggregate(loaded.cloud_session, operation)  # Submit each child at most once.
    if loaded.options.get("operation_id"):  # Never fall back to a legacy write when a durable plan mismatches.
        return json_error(CONFLICT_STATUS, ALREADY_SUBMITTED, "The confirmed aggregate plan no longer matches.")
    return _submit_org_job(loaded)  # Keep the existing AP-only route unchanged.


def _submission_guard(request_nonce: object) -> tuple[Response, int] | None:
    """Apply safeguards that do not need the active cloud context."""
    if not writes_enabled():  # Keep the deployment write gate.
        return json_error(
            SERVICE_UNAVAILABLE_STATUS,
            WRITE_DISABLED,
            "Organization upgrade writes stay disabled until the multi-site safety gates are complete.",
        )
    if not stored_options().get("operation_id") and _submission_is_repeated(request_nonce):  # Guard legacy only.
        return json_error(
            CONFLICT_STATUS, ALREADY_SUBMITTED, "This confirmed request already started an organization upgrade."
        )
    if _confirmation_value() != "CONFIRM":  # Require the exact typed confirmation.
        return json_error(BAD_REQUEST_STATUS, CONFIRMATION_REQUIRED, CONFIRMATION_MESSAGE)
    return None  # Continue to the scope and lock checks.


def _load_submission_context(request_nonce: object) -> SubmissionContext | tuple[Response, int]:
    """Validate the active scope, cloud session, and site locks."""
    context = active_context()  # Read the signed organization and selected sites.
    options = stored_options()  # Read options only for that organization.
    cloud_session = current_cloud_session()  # Read the signed operator cloud session.
    if context is None:  # Require the multi-site mode and at least one site.
        return json_error(BAD_REQUEST_STATUS, OPTIONS_INVALID, "The organization upgrade context is incomplete.")
    if not options or cloud_session is None:  # Require confirmed options and an authenticated cloud session.
        return json_error(BAD_REQUEST_STATUS, OPTIONS_INVALID, "The organization upgrade context is incomplete.")
    org_id, site_ids = context  # Use only the validated active scope.
    refusal = _site_lock_refusal(org_id, site_ids)  # Keep every existing site lock.
    if refusal is not None:  # One blocked site stops every destructive child.
        return refusal  # Preserve the existing lock response.
    return SubmissionContext(cloud_session, org_id, site_ids, options, request_nonce)  # Return the safe context.


def _site_lock_refusal(org_id: str, site_ids: Sequence[str]) -> tuple[Response, int] | None:
    """Return the first existing site lock refusal."""
    for site_id in site_ids:  # Check every selected site before any child write.
        refusal = upgrade_routes.lock_refusal(org_id, site_id)  # Reuse the existing lock boundary.
        if refusal is not None:  # Stop at the first blocked site.
            return refusal  # Return the existing conflict response.
    return None  # Every selected site permits the operation.


def _submit_org_job(context: SubmissionContext) -> Response | tuple[Response, int]:
    """Submit the existing AP-only organization request."""
    _store_job_marker(context.org_id, context.site_ids, context.request_nonce, "submission_unknown", None)
    result = _call_submission(context.cloud_session, context.org_id, context.site_ids, context.options)  # Send once.
    if not isinstance(result, OrgUpgradeResult):  # Return a mapped local or unknown failure.
        return result  # Preserve the existing response.
    _remember_submitted_identifier(result)  # Keep the cloud identifier in the browser marker.
    return _finish_submission(result, context.org_id, context.site_ids, context.request_nonce)  # Finish the flow.


def _remember_submitted_identifier(result: OrgUpgradeResult) -> None:
    """Add a known cloud identifier to the legacy browser marker."""
    marker = session.get(LAST_JOB_SESSION_KEY)  # Read the marker that blocks a replay.
    if not isinstance(marker, dict) or result.upgrade_id is None:  # Keep an unknown outcome unchanged.
        return  # Store no false cloud identity.
    marker["upgrade_id"] = result.upgrade_id  # Preserve the accepted cloud identity.
    session[LAST_JOB_SESSION_KEY] = marker  # Save the changed signed marker.


def aggregate_summary(record: Mapping[str, Any]) -> dict[str, Any]:
    """Build the public status without hiding a child result."""
    rows: list[dict[str, Any]] = []  # The progress table shows every backend child transparently.
    totals = [0, 0, 0]  # Store target, upgraded, and failed totals.
    for child in record.get("children", []):  # Preserve one row for each child route.
        if not isinstance(child, Mapping):  # A damaged child cannot erase the valid rows.
            continue
        row, counts = _aggregate_child_summary(child)  # Normalize one independent child result.
        rows.append(row)  # Keep the child visible even when another child failed.
        totals = [current + value for current, value in zip(totals, counts, strict=True)]  # Add known counts.
    return {  # Return one public operation with every child row.
        "upgrade_id": record.get("operation_id", ""),
        "status": record.get("state", "unknown"),
        "current_phase": None,
        "total": totals[0],
        "upgraded_count": totals[1],
        "failed_count": totals[2],
        "site_upgrades": rows,
        "children": rows,
        "errors": list(record.get("errors", [])),
        "cancellation": record.get("cancellation"),
    }


def _aggregate_child_summary(child: Mapping[str, Any]) -> tuple[dict[str, Any], tuple[int, int, int]]:
    """Normalize one aggregate child and its target counts."""
    total, upgraded, failed = _aggregate_child_counts(child)  # Read the root or nested target arrays.
    row = {  # Preserve the exact route, state, error, and cancellation result.
        "child_id": child.get("child_id", ""),
        "site_id": child.get("site_id") or "Multiple sites",
        "site_name": child.get("site_name", ""),
        "device_family": child.get("device_family", ""),
        "route": child.get("route", ""),
        "id": child.get("upgrade_id", ""),
        "status": child.get("status", "unknown"),
        "total": total,
        "upgraded": upgraded,
        "failed": failed,
        "error": child.get("error"),
        "cancellation": child.get("cancellation"),
    }
    return row, (total, upgraded, failed)  # Let the caller add aggregate totals.


def _aggregate_child_counts(child: Mapping[str, Any]) -> tuple[int, int, int]:
    """Return explicit, upgraded, and failed counts for one child."""
    data = child.get("status_data") if isinstance(child.get("status_data"), Mapping) else {}  # Read status.
    targets = data.get("targets") if isinstance(data.get("targets"), Mapping) else {}  # Read root targets.
    counts = (
        len(child.get("target_ids", [])),
        _array_count(targets.get("upgraded")),
        _array_count(targets.get("failed")),
    )
    entries = data.get("site_upgrades", data.get("upgrades", []))  # Read organization site results.
    _, nested_counts, has_nested_targets = _site_summaries(entries)  # Count nested AP target arrays.
    return (counts[0], nested_counts[1], nested_counts[2]) if has_nested_targets else counts  # Prefer nested counts.


def _owned_saved_operation(operation_id: str, org_id: str) -> dict[str, Any] | None:
    """Return one operation when the signed operator owns it."""
    operation = _read_operation(operation_id)  # Read from the durable store.
    if operation is None or operation.get("owner") != _owner_key() or operation.get("org_id") != org_id:
        return None  # Keep ownership and organization boundaries intact.
    return operation  # The caller can now poll or cancel it.


@org_upgrade_bp.get(JOB_PAGE_PATH)
@identity.require_session
def job_page(upgrade_id: str) -> str | tuple[Response, int]:
    """Read and show the current organization upgrade state."""
    context = _status_context()  # Require the selected organization and signed cloud session.
    if not isinstance(context[0], str):  # Return the existing incomplete-context response.
        return context  # Stop before a storage or cloud read.
    org_id, cloud_session = context  # Use the validated status context.
    operation = _owned_saved_operation(upgrade_id, org_id)  # Read only an owned durable operation.
    if operation is not None:  # Aggregate paths keep the existing visible URL.
        _refresh_aggregate(cloud_session, operation)  # Read each child and preserve read failures.
        return _aggregate_job_page(upgrade_id, operation)  # Render all child results together.
    return _org_job_page(cloud_session, org_id, upgrade_id)  # Keep the AP-only page behavior.


def _status_context() -> tuple[str, Any] | tuple[Response, int]:
    """Return the organization and cloud session for a status read."""
    org_id = resolve_org(None)  # Read the selected organization.
    cloud_session = current_cloud_session()  # Read the signed operator cloud session.
    if org_id is None or cloud_session is None:  # Require both scope and authentication.
        return json_error(BAD_REQUEST_STATUS, STATUS_FAILED, "The organization upgrade context is incomplete.")
    return org_id, cloud_session  # Return the validated read context.


def _refresh_aggregate(cloud_session: Any, operation: MutableMapping[str, Any]) -> None:
    """Refresh one aggregate operation and preserve its durable fallback."""
    logger.info("Refresh aggregate upgrade %s", operation.get("operation_id", ""))  # Log before child reads.
    try:
        aggregate_service().status(cloud_session, operation, upgrade_routes.run_store())  # Persist each child.
    except Exception:  # The last durable state remains safe to show.
        logger.exception("The aggregate upgrade status read failed")  # Record the unknown read outcome.
    _release_operation_locks(operation)  # Free every site as soon as the operation settles.
    logger.debug("The aggregate upgrade refresh finished with state %s", operation.get("state", "unknown"))


def _aggregate_job_page(upgrade_id: str, operation: Mapping[str, Any]) -> str:
    """Render the progress page for one aggregate operation."""
    summary = aggregate_summary(operation)  # Build one public view from every durable child.
    return render_page(  # Keep the existing progress template and poll interval.
        PROGRESS_TEMPLATE,
        upgrade_id=upgrade_id,
        site_count=len(operation.get("site_ids", [])),
        status=summary,
        poll_interval_seconds=current_app.config.get("POLL_INTERVAL_SECONDS", 30),
    )


def _org_job_page(cloud_session: Any, org_id: str, upgrade_id: str) -> str | tuple[Response, int]:
    """Read and render the existing AP-only organization job."""
    try:  # Map validation and cloud read failures to the existing responses.
        result = upgrade_service().status(cloud_session, org_id, upgrade_id)  # Read the AP job once.
    except (TypeError, ValueError) as error:
        return json_error(BAD_REQUEST_STATUS, STATUS_FAILED, str(error))
    except Exception:
        logger.exception("The organization upgrade status read failed")
        return json_error(SERVICE_UNAVAILABLE_STATUS, STATUS_FAILED, "The cloud status read failed.")
    refusal = result_error(result, STATUS_FAILED)  # Reject an invalid cloud response.
    if refusal is not None:  # Preserve the existing gateway response.
        return refusal  # Stop before a false status page.
    summary = status_summary(result)  # Normalize the AP job response.
    remember_job_state(org_id, upgrade_id, summary["status"])  # Update legacy replay state.
    return _org_progress_page(upgrade_id, summary)  # Render the existing progress page.


def _org_progress_page(upgrade_id: str, summary: Mapping[str, Any]) -> str:
    """Render the existing AP-only progress page."""
    last = session.get(LAST_JOB_SESSION_KEY, {})  # Read the browser-owned site count.
    fallback = len(selected_site_ids())  # Keep the current selection as a fallback.
    site_count = last.get("site_count", fallback) if isinstance(last, dict) else fallback  # Preserve behavior.
    return render_page(  # Keep the existing template and poll interval.
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
    context = _status_context()  # Require the selected organization and signed cloud session.
    if not isinstance(context[0], str):  # Return the existing incomplete-context response.
        return context  # Stop before a storage or cloud read.
    org_id, cloud_session = context  # Use the validated status context.
    operation = _owned_saved_operation(upgrade_id, org_id)  # Read only an owned durable operation.
    if operation is not None:  # Return every aggregate child in one browser response.
        _refresh_aggregate(cloud_session, operation)  # Read and persist each child.
        return jsonify(aggregate_summary(operation)), OK_STATUS  # Preserve mixed results.
    return _org_status_response(cloud_session, org_id, upgrade_id)  # Keep the AP-only response.


def _org_status_response(cloud_session: Any, org_id: str, upgrade_id: str) -> tuple[Response, int]:
    """Return the existing AP-only polling response."""
    try:  # Map validation and cloud read failures to the existing responses.
        result = upgrade_service().status(cloud_session, org_id, upgrade_id)  # Read the AP job once.
    except (TypeError, ValueError) as error:
        return json_error(BAD_REQUEST_STATUS, STATUS_FAILED, str(error))
    except Exception:
        logger.exception("The organization upgrade status read failed")
        return json_error(SERVICE_UNAVAILABLE_STATUS, STATUS_FAILED, "The cloud status read failed.")
    refusal = result_error(result, STATUS_FAILED)  # Reject an invalid cloud response.
    if refusal is not None:  # Preserve the existing gateway response.
        return refusal  # Stop before a false success response.
    summary = status_summary(result)  # Normalize the AP job response.
    remember_job_state(org_id, upgrade_id, summary["status"])  # Update the legacy replay state.
    return jsonify({"upgrade_id": upgrade_id, **summary}), OK_STATUS  # Return the existing public shape.


def _cancel_context(upgrade_id: str) -> tuple[str, Any] | tuple[Response, int]:
    """Return the owned organization and session for cancellation."""
    org_id = resolve_org(None)  # Read the selected organization.
    cloud_session = current_cloud_session()  # Read the signed operator cloud session.
    if not _owns_org_job(upgrade_id, org_id):  # Require this browser to own the AP job.
        return json_error(CONFLICT_STATUS, JOB_NOT_OWNED, "This browser session did not start that organization job.")
    if org_id is None or cloud_session is None:  # Require both scope and authentication.
        return json_error(BAD_REQUEST_STATUS, CANCEL_FAILED, "The organization upgrade context is incomplete.")
    return org_id, cloud_session  # Return the validated cancel context.


def _owns_org_job(upgrade_id: str, org_id: str | None) -> bool:
    """Return true when this browser owns the AP organization job."""
    last = session.get(LAST_JOB_SESSION_KEY)  # Read the signed browser marker.
    if not isinstance(last, dict):  # A missing marker owns no legacy job.
        return False  # Reject the cancellation.
    return last.get("upgrade_id") == upgrade_id and last.get("org_id") == org_id  # Match job and organization.


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
    refusal = _cancellation_guard()  # Apply the write gate and typed confirmation.
    if refusal is not None:  # Stop before a destructive action.
        return refusal  # Preserve the existing error response.
    org_id = resolve_org(None)  # The selected organization guards the durable operation.
    cloud_session = current_cloud_session()  # The cancel calls use the signed operator session.
    operation = _cancel_operation(upgrade_id, org_id)  # Enforce ownership and organization scope.
    if operation is not None and cloud_session is not None:  # Use the aggregate child cancellation flow.
        return _cancel_aggregate(cloud_session, operation, upgrade_id)  # Cancel each eligible child once.
    return _cancel_org_job(upgrade_id)  # Keep the existing AP-only cancellation behavior.


def _cancel_operation(upgrade_id: str, org_id: str | None) -> dict[str, Any] | None:
    """Return an owned aggregate operation for cancellation."""
    if org_id is None:  # An operation cannot cross an absent organization scope.
        return None  # Continue to the existing context error.
    return _owned_saved_operation(upgrade_id, org_id)  # Enforce owner and organization matches.


def _cancellation_guard() -> tuple[Response, int] | None:
    """Apply safeguards that precede every cancellation."""
    if not writes_enabled():  # Keep the deployment write gate.
        return json_error(
            SERVICE_UNAVAILABLE_STATUS,
            WRITE_DISABLED,
            "Organization upgrade writes stay disabled until the multi-site safety gates are complete.",
        )
    if _confirmation_value() != "CANCEL":  # Require the exact typed confirmation.
        return json_error(BAD_REQUEST_STATUS, CONFIRMATION_REQUIRED, "Type CANCEL before you request cancellation.")
    return None  # Continue to ownership and scope checks.


def _cancel_aggregate(
    cloud_session: Any,
    operation: MutableMapping[str, Any],
    upgrade_id: str,
) -> tuple[Response, int]:
    """Cancel every eligible aggregate child one time."""
    logger.info("Cancel durable aggregate upgrade %s", upgrade_id)  # Log before child cancellation.
    try:  # The service persists before and after every destructive action.
        aggregate_service().cancel(cloud_session, operation, upgrade_routes.run_store())
    except ValueError as error:  # A replay or malformed state is a conflict.
        return json_error(CONFLICT_STATUS, CANCEL_FAILED, str(error))
    except Exception:  # Preserve an unknown outcome without a hidden retry.
        logger.exception("The aggregate upgrade cancellation outcome is unknown")
        return json_error(
            SERVICE_UNAVAILABLE_STATUS,
            CANCEL_FAILED,
            "One or more cancellation outcomes are unknown. Read the operation before another action.",
        )
    logger.debug("The aggregate cancellation %s finished with state %s", upgrade_id, operation.get("state", ""))
    _release_operation_locks(operation)  # Free every site after each child holds a cancellation result.
    if _wants_html():  # Keep the browser on one visible operation.
        return next_page_answer(f"/upgrade/org/jobs/{upgrade_id}")  # Return the existing redirect response.
    return jsonify(aggregate_summary(operation)), OK_STATUS  # Show every child cancellation result.


def _cancel_org_job(upgrade_id: str) -> tuple[Response, int]:
    """Cancel the existing AP-only organization job."""
    context = _cancel_context(upgrade_id)  # Enforce browser ownership and organization scope.
    if not isinstance(context[0], str):  # Return the existing ownership or context error.
        return context  # Stop before the cloud call.
    org_id, cloud_session = context  # Use the validated legacy cancel context.
    result = _call_cancellation(cloud_session, org_id, upgrade_id)
    if not isinstance(result, OrgUpgradeResult):  # Return a mapped validation or unknown failure.
        return result  # Preserve the existing response.
    refusal = result_error(result, CANCEL_FAILED)  # Reject an invalid cloud response.
    if refusal is not None:  # Preserve the existing gateway response.
        return refusal  # Stop before a false cancellation result.
    if _wants_html():  # Keep the browser on the existing progress page.
        return next_page_answer(f"/upgrade/org/jobs/{upgrade_id}")  # Return the existing redirect response.
    return jsonify({"upgrade_id": upgrade_id, "cancel_requested": True}), OK_STATUS  # Preserve the JSON shape.


def _wants_html() -> bool:
    """Return true when content negotiation selects HTML."""
    return request.accept_mimetypes.best_match(("application/json", "text/html")) == "text/html"  # Match existing.
