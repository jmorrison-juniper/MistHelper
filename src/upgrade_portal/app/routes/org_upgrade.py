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
from functools import partial  # Issue #3243: bind the adopter seam to the pre-check reader.
from typing import Any

from flask import Blueprint, Response, current_app, g, jsonify, request, session
from requests.exceptions import RequestException  # Name the transport faults that the Mist SDK can raise.

from ....firmware.aggregate_upgrade_service import (  # Issue #3225: the final states and their cancel refusal.
    FINAL_CANCEL_TEXT,
    FINAL_OPERATION_STATES,
    AggregateBuildInput,
    AggregateUpgradeService,
    FinalOperationError,
)
from ....firmware.org_upgrade_body import OrgUpgradeBody
from ....firmware.org_upgrade_service import OrgUpgradeResult, OrgUpgradeService
from ...api.run_controls.views import RunStalePolicy  # Issue #3249: the age rule of the single-site page.
from ...runtime import identity, lock
from ...upgrade.options import (
    ORG_OPTION_HELP,
    BadOptionError,
    build_options,
    build_options_record,
    build_options_view,
)
from ...upgrade.org_advanced_options import (  # Issue #3383: the advanced controls of the multi-site page.
    OrgAdvancedOptions,
    OrgAdvancedRules,
    OrgAdvancedSummary,
)
from ...upgrade.org_cancel_outcomes import OrgCancelOutcomes  # Issue #3246: the three lists of each cancel.
from ...upgrade.org_cancel_text import OrgCancelText  # Issue #3225: one Cancellation text for the page and the poll.
from ...upgrade.org_cascade.readers import OrgSettleAnchors  # Issue #3245: the anchors before the first write.
from ...upgrade.org_cascade.record import WATCH_KEY, OrgPhaseEntries, OrgPhaseWatch  # Issue #3245: the watch.
from ...upgrade.org_cascade.view import OrgPhaseView  # Issue #3245: the phase card of the page and the poll.
from ...upgrade.org_cascade.walk import OrgCascadeDeps, OrgCascadeRegistry  # Issue #3245: one watch thread.
from ...upgrade.org_child_controls import OrgControlsView, OrgScheduleView  # Issue #3247: the recovery controls.
from ...upgrade.org_devices import OrgDeviceRows  # Issue #3249: one row for each device of the operation.
from ...upgrade.org_postcheck_view import OrgPostCheckView  # Issue #3244: the post-check card of each site.
from ...upgrade.org_precheck import PRECHECK_FIELD, OrgPrecheckGate, OrgPrecheckState  # Issue #3243: the gate.
from ...upgrade.org_retry import OrgRetryPlan, OrgRetrySelection  # Issue #3247: the devices of one retry.
from ...upgrade.org_versions import OrgVersionRefresh  # Issue #3249: the bounded running version reads.
from ..factory import build_error_envelope, json_error  # Issue #3242: a replay refusal can carry details.
from . import select as select_routes
from . import upgrade as upgrade_routes
from .org_postcheck import OrgPostCheckBridge  # Issue #3244: the post-check seam of the watch thread.
from .select import (
    BAD_REQUEST_STATUS,
    MULTI_SITE_MODE,
    NOT_FOUND_STATUS,
    OK_STATUS,
    ORG_UPGRADE_OPTIONS_KEY,
    ORG_UPGRADE_OPTIONS_NONCE_KEY,
    ORG_UPGRADE_OPTIONS_ORG_KEY,
    ORG_UPGRADE_RETRY_KEY,
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
DEVICE_VERSION_READER_CONFIG_KEY = "ORG_DEVICE_VERSION_READER"  # Issue #3249: a test replaces the stats read.
ANCHOR_READER_CONFIG_KEY = "ORG_SETTLE_ANCHOR_READER"  # Issue #3245: a test replaces the anchor read.
CASCADE_STARTER_CONFIG_KEY = "ORG_CASCADE_STARTER"  # Issue #3245: a test replaces the watch thread.
RETRY_CACHE_KEY = "org_retry_plan"  # Issue #3247: one request builds the retry plan one time.
PLAN_OPTION_DROPPED = frozenset({"operation_id", "target_count"})  # Issue #3247: values of the browser session only.

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
NOT_CANCELLABLE = "org_upgrade_not_cancellable"  # Issue #3225: a final operation refuses a cancel.
WRITE_DISABLED = "org_upgrade_write_disabled"
ALREADY_SUBMITTED = "org_upgrade_already_submitted"
LEGACY_REPLAY_MESSAGE = "This confirmed request already started an organization upgrade."  # Issue #3242.
AGGREGATE_REPLAY_MESSAGE = "This confirmed request already started a multi-site upgrade."  # Issue #3242.
UNKNOWN_REPLAY_MESSAGE = (  # Issue #3242: the first cloud answer named no job, so the refusal links nothing.
    "The cloud response to the last organization upgrade request is unknown. "
    "Reconcile the job history before another submission."
)
UNREACHABLE_OPERATOR = "unreachable_operator_address"  # A reserved domain cannot answer for firmware writes.
UNREACHABLE_OPERATOR_MESSAGE = (  # The cure is a reachable address, not a different credential.
    "This operator address uses a reserved domain and cannot answer for a firmware write. "
    "Sign in again with a reachable work address, then start the upgrade."
)
JOB_NOT_OWNED = "org_upgrade_job_not_owned"
SITE_LOCK_WRONG_RUN = "site_lock_wrong_run"  # The operator holds the site for another run.
SITE_LOCK_WRONG_RUN_MESSAGE = "Your existing site lock belongs to another run."  # The cure is the other run.
PRECHECK_MISSING_MESSAGE = (  # Issue #3243: the refusal names the cure and each site with no capture.
    "Save a verified pre-check capture for each selected site before you start the upgrade. "
    "These sites hold no pre-check capture: {names}."
)
PRECHECK_RECORD_MESSAGE = (  # Issue #3243: the plan could not keep the baseline of each site.
    "The portal could not record the pre-check captures. Read the operation before another action."
)
PLANNED_STATE = "planned"  # The one state in which no child job reached the cloud.
SUBMISSION_CLAIMED_STATE = "submission_claimed"  # Issue #3242: a first start holds the claim of the parent.

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


@dataclass(frozen=True, slots=True)
class OperationLockScope:
    """Hold the values that each site lock of one operation shares."""

    org_id: str  # The organization half of each lock key.
    operation_id: str  # The run name that each lock of the operation carries.
    owner: identity.SessionOwner  # The signed operator and browser.
    client: Any  # The lock store client of the production portal or of a test.


class OrgUpgradeScheduleReader:
    """Read organization schedule controls with the single-site schedule rules."""

    @staticmethod
    def add_start_option(body: dict[str, Any], source: Mapping[str, Any]) -> None:
        """Add the optional start time as epoch seconds."""
        start_text = str(source.get("start_time", "")).strip()  # Read the existing local date and time control.
        if not start_text:  # Omit an empty schedule to preserve the current immediate-start behavior.
            return  # Keep an immediate start when the operator leaves the existing control empty.
        logger.info("Read the organization upgrade start time")  # Log before parsing the submitted schedule.
        try:  # A JSON client can send text that names no date and no time.
            start = datetime.fromisoformat(start_text)  # Parse the submitted ISO value from the existing form field.
        except ValueError as error:  # The parser text repeats the typed value, so it never reaches the page.
            logger.warning("The organization upgrade refused a start time that names no date and time")
            raise BadOptionError("start_time", labels=ORG_OPTION_HELP) from error
        start = start.replace(tzinfo=UTC) if start.tzinfo is None else start  # Give a naive value the portal zone.
        body["start_time"] = int(start.timestamp())  # Store the same epoch format as the existing service.
        logger.debug("The organization upgrade start time is present")  # Log after parsing without naming the value.

    @staticmethod
    def add_reboot_option(body: dict[str, Any], source: Mapping[str, Any]) -> None:
        """Add the optional reboot delay by using the single-site duration rules."""
        reboot_text = str(source.get("reboot_at", "")).strip()  # Read the same field name as the single-site form.
        if not reboot_text:  # Omit an empty delay to preserve the current immediate-reboot behavior.
            return  # Keep the existing behavior when the operator leaves the new control empty.
        logger.info("Validate the organization upgrade reboot delay")  # Log before the safety guard runs.
        build_options({"reboot_at": reboot_text})  # Reuse the single-site parser so invalid or past values fail closed.
        body["reboot_at"] = reboot_text  # Store the operator duration for the single-site mapper to convert later.
        logger.debug("The organization upgrade reboot delay passed validation")  # Log after the guard succeeds.

    @staticmethod
    def reboot_text(options: Mapping[str, Any]) -> str:
        """Return the reboot delay text that the options page and confirmation page show."""
        reboot_at = options.get("reboot_at")  # Read the raw duration saved by the organization route.
        return str(reboot_at) if reboot_at is not None else ""  # Preserve the operator text without a unit change.


class OrgOptionRefusal:
    """Name the multi-site control in each option refusal.

    Why:
        Issue #3273 records the cause. The shared option mapper names the
        controls of the single-site page. The multi-site page paints other
        labels, and it holds one target version control for each device type.
        A refusal with a single-site label sent the operator to a control that
        the multi-site page does not hold.

        Issue #3206 also forbids a refusal that names an internal field. The
        parser text of Python names no control and repeats the typed value, so
        this class replaces that text too.
    """

    @staticmethod
    def translate(error: BadOptionError, rows: Sequence[Mapping[str, Any]] = ()) -> BadOptionError:
        """Return the same refusal with the label of the multi-site page.

        Args:
            error: The refusal of the shared option mapper.
            rows: The device rows of the site, which map a model to its device type.

        Returns:
            A refusal with the same model and code, and the multi-site label.
        """
        field = OrgOptionRefusal.page_field(error, rows)  # Find the control that the multi-site page paints.
        logger.debug("The multi-site refusal of %s names the field %s", error.field, field)  # Log the translation.
        return BadOptionError(field, error.model, labels=ORG_OPTION_HELP)  # Keep the model and the error code.

    @staticmethod
    def page_field(error: BadOptionError, rows: Sequence[Mapping[str, Any]]) -> str:
        """Return the field of the multi-site control that matches one refusal.

        Args:
            error: The refusal of the shared option mapper.
            rows: The device rows of the site.

        Returns:
            The family version field for a refused model, or the field of the refusal.
        """
        if error.field != "version_target":  # Every other field keeps its name on both pages.
            return error.field
        families = {str(row.get("device_type", "")) for row in rows if str(row.get("model", "")) == error.model}
        field = f"version_{families.pop()}" if len(families) == 1 else "targets"  # One model has one family.
        return field if field in ORG_OPTION_HELP else "targets"  # An unknown family names the device type legend.

    @staticmethod
    def whole_number(text: str, field: str) -> int:
        """Read one whole number, or refuse it with the multi-site label.

        Args:
            text: The text of one number that the operator typed.
            field: The field that holds the number.

        Returns:
            The number.

        Raises:
            BadOptionError: If the text holds no whole number.
        """
        try:  # The parser text repeats the typed value, so it never reaches the page.
            return int(text)  # Convert the text for the shared mapper, which applies the range rules.
        except ValueError as error:  # A word, a decimal point, or an empty entry holds no whole number.
            logger.warning("The organization upgrade refused the field %s, which holds no whole number", field)
            raise BadOptionError(field, labels=ORG_OPTION_HELP) from error


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
    source = request_source()  # Read one request representation.
    request_body = _base_request_options(source)  # Normalize the shared AP fields.
    OrgUpgradeScheduleReader.add_start_option(request_body, source)  # Add the optional schedule.
    OrgUpgradeScheduleReader.add_reboot_option(request_body, source)  # Add the optional reboot delay.
    selected = _selected_types(source)  # Read all selected device families.
    if selected is not None:  # The legacy AP-only request omits this field.
        _add_device_options(request_body, source, selected)  # Add the multi-device controls.
        request_body.update(OrgAdvancedOptions.read(source))  # Issue #3383: add each advanced control that is set.
    return request_body  # Return one validated input shape.


def request_source() -> Mapping[str, Any]:
    """Return the JSON object or form collection for this request.

    Why:
        Issue #3247. The reschedule route of `org_controls.py` reads the same
        start time field, so the two modules share this one parser.
    """
    payload: Any = request.get_json(silent=True)  # Read JSON without raising for a form request.
    return payload if isinstance(payload, Mapping) else request.form  # Prefer a valid JSON object.


def _base_request_options(source: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize the option fields that both request forms share."""
    version = str(source.get("version", "")).strip()  # Read the legacy AP version.
    strategy = str(source.get("strategy", "canary")).strip()  # Read the rollout strategy.
    body: dict[str, Any] = {"versions": [{"firmware_type": "ap", "version": version}], "strategy": strategy}
    if strategy != "big_bang":  # Big-bang upgrades do not use a failure threshold.
        percentage = str(source.get("max_failure_percentage", "5")).strip()  # Read the failure limit text.
        body["max_failure_percentage"] = OrgOptionRefusal.whole_number(percentage, "max_failure_percentage")
    if strategy == "canary":  # Canary upgrades require phase percentages.
        body["canary_phases"] = _phase_values(source)  # Preserve the submitted phase order.
    return body  # The caller adds optional multi-device fields.


def _phase_values(source: Mapping[str, Any]) -> list[int]:
    """Return the submitted canary phase percentages."""
    text = str(source.get("canary_phases", "")).strip()  # Read the comma-separated field.
    parts = [part.strip() for part in text.split(",") if part.strip()] if text else []  # Drop each empty entry.
    return [OrgOptionRefusal.whole_number(part, "canary_phases") for part in parts]  # Parse each value in order.


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
    return {  # The shared mapper reads the flat field names of the single-site page.
        "targets": targets,  # The explicit devices of this site.
        "selected_types": list(options["selected_types"]),  # The checked device families.
        "strategy": options.get("strategy", "big_bang"),  # The rollout strategy of the whole plan.
        "reboot": options.get("reboot", True),  # The reboot choice of each switch and each gateway.
        "junos_file_action": options.get("junos_file_action", True),  # The Junos file action choice.
        "force": options.get("force", False),  # The forced write choice.
        "start_time": options.get("start_time"),  # The epoch start of the job, or None.
        "reboot_at": options.get("reboot_at"),  # The reboot delay text, or None.
        "canary_phases": ",".join(str(value) for value in options.get("canary_phases", [])),  # The phase text.
        "max_failure_percentage": options.get("max_failure_percentage"),  # The failure limit of the whole run.
        **OrgAdvancedOptions.site_fields(options),  # Issue #3383: each advanced value reaches the mapper.
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
    if not targets or options is None:  # A confirmed request must name a real device at a selected site.
        logger.warning("The organization upgrade options name no device at the selected sites")
        raise BadOptionError("targets", labels=ORG_OPTION_HELP)  # Name the legend that the multi-site page paints.
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
    view = narrowed_view(aggregate_options_view(cloud_session, org_id, site_id))  # Issue #3247: a retry narrows.
    rows = _selected_target_rows(view, options, selected)  # Select explicit targets with a chosen version.
    logger.debug("The site option view selected %s target(s)", len(rows))  # Log after the transformation.
    logger.info("Validate aggregate upgrade options for site %s", site_id)  # Log before validation.
    try:  # The shared mapper names the controls of the single-site page.
        built = aggregate_options_record(cloud_session, org_id, site_id, _site_option_body(options, rows))
    except BadOptionError as error:  # Issue #3273: name the control that the multi-site page paints.
        logger.warning("The option mapper refused the options of site %s", site_id)  # Log the refusal.
        raise OrgOptionRefusal.translate(error, view.get("targets", [])) from error  # The rows map a model to a type.
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


def retry_plan_of(
    record: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]] | None = None,
) -> OrgRetryPlan | None:
    """Return the retry plan of one settled operation, or None.

    Why:
        Issue #3247. A retry while a child job can still write firmware can
        upgrade one device twice at the same time. The retry control therefore
        waits until every child job holds a final state.

    Args:
        record: The durable operation record.
        rows: The device rows, when the caller already built them.

    Returns:
        The retry plan, or None when a child can still write or no device needs a retry.
    """
    if not _operation_is_settled(record):  # A child that can still write firmware blocks a retry.
        return None  # The page shows no retry control yet.
    return OrgRetrySelection.plan(record, rows)  # Select the devices that need a second attempt.


def current_retry_plan() -> OrgRetryPlan | None:
    """Return the retry plan that narrows the current options, or None.

    Why:
        Issue #3247. The signed cookie holds only a reference to the settled
        operation, because the cookie holds 4 KB at most. Each request builds
        the plan again from the durable record, and one request builds it one time.
    """
    if RETRY_CACHE_KEY not in g:  # The first read of this request builds the plan.
        setattr(g, RETRY_CACHE_KEY, _read_retry_plan())  # Keep the plan for the other reads of this request.
    cached: OrgRetryPlan | None = getattr(g, RETRY_CACHE_KEY)  # The plan of this request, or None.
    return cached  # Every site of one save reads the same plan.


def _read_retry_plan() -> OrgRetryPlan | None:
    """Build the retry plan that the signed cookie names, or None."""
    context = active_context()  # A retry needs the multi-site scope.
    org_id = context[0] if context is not None else ""  # No scope means no retry.
    reference = OrgRetryPlan.session_reference(session.get(ORG_UPGRADE_RETRY_KEY), org_id) if org_id else None
    if reference is None:  # The operator opened no retry, or opened it for another organization.
        return None  # The page plans every device.
    logger.info("Read the retry plan of aggregate upgrade %s", reference)  # Log before the store read.
    operation = owned_saved_operation(reference, org_id)  # The operator must own the settled operation.
    plan = retry_plan_of(operation) if operation is not None else None  # Build the devices again.
    logger.debug("The retry plan of %s holds %s device(s)", reference, len(plan.devices) if plan else 0)
    return plan if plan is not None else OrgRetryPlan.empty(reference, org_id)  # Fail closed: plan no device.


def narrowed_view(view: Mapping[str, Any]) -> dict[str, Any]:
    """Return one site view that holds only the retry devices when a retry applies."""
    retry = current_retry_plan()  # The retry that the operator opened, or None.
    return retry.narrow(view) if retry is not None else dict(view)  # A plain plan keeps every device.


def request_for_service(site_ids: list[str], options: Mapping[str, Any]) -> dict[str, Any]:
    """Build the validated service request from session state."""
    supported = {key: value for key, value in options.items() if key in OrgUpgradeBody.FIELDS}
    request_body = {**supported, "site_ids": list(site_ids)}
    return OrgUpgradeBody.build(request_body)


def options_view(options: Mapping[str, Any]) -> dict[str, Any]:
    """Return form values from the validated service option shape."""
    first = _first_version(options.get("versions"))  # Read the legacy AP version record.
    selected_types = list(options.get("selected_types", ["ap", "switch", "gateway"]))  # Restore chosen families.
    return {  # Return the existing template field names.
        "version": options.get("version_ap", first.get("version", "")),  # The legacy AP version field.
        "version_ap": str(options.get("version_ap", first.get("version", ""))),  # Keep the AP target visible.
        "version_switch": str(options.get("version_switch", "")),  # Keep the switch target visible.
        "version_gateway": str(options.get("version_gateway", "")),  # Keep the gateway target visible.
        "selected_types": selected_types,  # Keep the selected family boxes stable after Back.
        "reboot": options.get("reboot", True),  # Keep the reboot radio group stable after Back.
        "junos_file_action": options.get("junos_file_action", True),  # Keep the Junos radio group stable.
        "force": options.get("force", False),  # Keep the force checkbox stable after Back.
        "strategy": options.get("strategy", "canary"),  # Keep the strategy radio group stable after Back.
        "canary_phases": _phase_text(options.get("canary_phases")),  # Show the phases as the operator typed them.
        "max_failure_percentage": options.get("max_failure_percentage", 5),  # The failure limit of the whole run.
        "start_time": _start_text(options.get("start_time")),  # Show the start in the date and time control.
        "reboot_at": OrgUpgradeScheduleReader.reboot_text(options),  # Show the reboot delay text.
        **OrgAdvancedOptions.form_values(options),  # Issue #3383: keep each advanced control stable after Back.
    }


FAMILY_LABELS = (("version_ap", "Access points"), ("version_switch", "Switches"), ("version_gateway", "Gateways"))
STABLE_FAMILY_FIELDS = frozenset({"version_switch", "version_gateway"})  # Issue #3383: these read the stable build.
STABLE_BUILD_TEXT = "the vendor stable build"  # Issue #3383: the cloud picks the build, so no version number shows.


def firmware_summary(view: Mapping[str, Any], families: Sequence[str]) -> str:
    """Return the target version of each selected device family.

    Why:
        An operator must read every target version before the typed
        confirmation. One empty line would hide the exact change. The stable
        build replaces the typed version of each switch and each gateway, so
        the line names the stable build for those two families (issue #3383).
    """
    logger.info("Build the firmware summary for %s device families", len(families))  # Log before the build.
    parts = [  # Name one version for each family that this operation upgrades.
        f"{label} {_summary_version(view, field)}"  # The family and the build that it receives.
        for field, label in FAMILY_LABELS  # Keep the fixed family order of the options page.
        if view.get(field) and (not families or field.removeprefix("version_") in families)  # Selected families.
    ]
    logger.debug("The firmware summary names %s device families", len(parts))  # Log after the build.
    return ", ".join(parts) if parts else str(view.get("version") or "Not selected")  # Keep the AP fallback.


def _summary_version(view: Mapping[str, Any], field: str) -> str:
    """Return the build text of one device family in the firmware summary."""
    if view.get("stable_version") is True and field in STABLE_FAMILY_FIELDS:  # The cloud picks the stable build.
        return STABLE_BUILD_TEXT
    return str(view[field])  # The typed target version.


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
    """Normalize one site entry and its target counts.

    Why:
        Issue #3225. The organization job of an earlier release upgrades
        access points only, so each row names that family from the server.
        The page then needs no guess for a row with no family.
    """
    raw_nested = entry.get("upgrade")  # A cloud answer can nest the site job under one key.
    nested = raw_nested if isinstance(raw_nested, Mapping) else entry  # Read the flat entry otherwise.
    raw_targets = nested.get("targets")  # The device arrays of the site job.
    targets = raw_targets if isinstance(raw_targets, Mapping) else {}  # A damaged value counts as no target.
    counts = _target_counts(targets)  # The total, upgraded, and failed counts.
    row = {  # One public row of the site table.
        "site_id": entry.get("site_id", nested.get("site_id", "")),
        "id": nested.get("id", entry.get("upgrade_id", "")),
        "device_family": "ap",  # The organization job upgrades access points only.
        "status": nested.get("status", "unknown"),
        "total": counts[0],
        "upgraded": counts[1],
        "failed": counts[2],
    }
    return row, counts, bool(targets)  # The caller adds the counts to the job totals.


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
    data = dict(result.data)  # Detach the cloud answer.
    entries = data.get("site_upgrades", data.get("upgrades", []))  # The cloud names the list in two ways.
    sites, counts, has_site_targets = _site_summaries(entries)  # One row for each site job.
    root_targets = data.get("targets")  # A job answer can carry the device arrays at the root.
    if not has_site_targets and isinstance(root_targets, Mapping):  # Use the root arrays only as a fallback.
        counts = _target_counts(root_targets)  # The root arrays count every device of the job.
    root_status = str(data.get("status", "")).lower()  # Prefer the explicit aggregate state.
    status = root_status or _derived_ap_status(sites)  # Derive from all site entries when root is absent.
    return {
        "status": status,
        "current_phase": data.get("current_phase"),
        "total": counts[0],
        "upgraded_count": counts[1],
        "failed_count": counts[2],
        "site_upgrades": sites,
        "cancel_allowed": status not in FINAL_OPERATION_STATES,  # Issue #3225: a final job shows no cancel form.
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
    context = active_context()  # Read the signed organization and site selection.
    if context is None:  # The page belongs to the multi-site mode.
        return json_error(BAD_REQUEST_STATUS, MODE_REQUIRED, MODE_REQUIRED_MESSAGE)
    org_id, site_ids = context  # Use only the validated active context.
    rows = selected_rows(org_id, site_ids)  # Recheck site ownership before display.
    if not rows:  # Show no device of a missing or foreign site.
        return json_error(NOT_FOUND_STATUS, SITES_REQUIRED, SITES_REQUIRED_MESSAGE)
    retry = current_retry_plan()  # Issue #3247: a retry keeps only the devices that need a second attempt.
    prefill = retry.options if retry is not None else {}  # A retry shows the earlier choices first.
    device_views = _option_device_views(org_id, rows)  # One device list for each selected site.
    return render_page(  # Render the options form with one device list for each site.
        OPTIONS_TEMPLATE,
        sites=rows,
        device_views=device_views,
        options=options_view(stored_options() or prefill),
        retry=retry,
        ssr_present=OrgAdvancedRules.holds_router(device_views),  # Issue #3383: the release train control.
    )


def _option_device_views(org_id: str, rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return the device view of each selected site, narrowed to the retry devices when a retry applies."""
    cloud_session = current_cloud_session()  # The options page reads the same inventory as the single-site page.
    if cloud_session is None:  # A signed session normally supplies the cloud connection.
        return []  # Show no device without a cloud connection.
    logger.info("Read the option device views of %s site(s)", len(rows))  # Log before the inventory reads.
    device_views = []  # Keep one visible device list for each selected site.
    for row in rows:  # Each site keeps its identity beside its devices.
        view = narrowed_view(aggregate_options_view(cloud_session, org_id, str(row["site_id"])))  # One site.
        device_views.append({"site": row, **view})  # The template reads the site beside its devices.
    logger.debug("The options page shows %s device view(s)", len(device_views))  # Log after the reads.
    return device_views  # The template paints one table for each site.


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
    except BadOptionError as error:  # Issue #3273: every refusal names a control that this page paints.
        return json_error(BAD_REQUEST_STATUS, OPTIONS_INVALID, str(OrgOptionRefusal.translate(error)))
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
    OrgAdvancedRules.refuse_stable_access_points(choices, aggregate["targets"])  # Issue #3383: no stable AP build.
    OrgAdvancedRules.refuse_large_failure_counts(choices)  # Issue #3383: each count fits the organization body.
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
    _attach_plan_options(operation, options)  # Issue #3247: a later retry reads the choices of this plan.
    _write_operation(operation)  # Persist the complete plan before confirmation.
    options["operation_id"] = operation["operation_id"]  # Keep only the durable identity in the browser.
    options["target_count"] = len(aggregate["targets"])  # Keep a small confirmation value.
    return options, str(operation["request_nonce"])  # Return the durable replay nonce.


def _attach_plan_options(operation: MutableMapping[str, Any], options: Mapping[str, Any]) -> None:
    """Store the choices of the operator and the retry source beside one new plan.

    Why:
        Issue #3247. A retry opens the options form with the earlier choices.
        The browser cookie holds no device list, so the durable record keeps
        the choices, and the new plan names the operation that it repeats.
    """
    choices = {key: value for key, value in options.items() if key not in PLAN_OPTION_DROPPED}  # Durable values.
    operation["plan_options"] = choices  # The retry prefill of a later operation reads these values.
    retry = current_retry_plan()  # The retry that narrowed this plan, or None.
    if retry is not None:  # The new plan repeats an earlier operation.
        operation["retry_of_operation_id"] = retry.operation_id  # The audit link to the earlier operation.
        logger.debug("The new plan repeats aggregate upgrade %s", retry.operation_id)  # Log the link.


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
    operation = _saved_operation(options)  # Read the durable plan one time for every value of the page.
    target_count, families = _confirmation_targets(operation)  # Read only the durable aggregate child summary.
    view = options_view(options)  # Build the display values one time.
    names = {str(row["site_id"]): str(row["name"]) for row in rows}  # The approved name of each site.
    prechecks = precheck_gate().read(site_ids, names)  # Issue #3243: the pre-check capture of each site.
    return render_page(  # Render the existing typed confirmation page.
        CONFIRM_TEMPLATE,  # Keep the existing template.
        org_name=org_display_name(org_id),  # Show the selected organization.
        site_count=len(rows),  # Show the selected site count.
        device_count=target_count or _site_device_count(rows),  # Keep the AP-only count fallback.
        device_families=families,  # Show each planned family.
        options=view,  # Show the confirmed choices.
        firmware_summary=firmware_summary(view, families),  # Name the target version of each family.
        advanced_summary=OrgAdvancedSummary.lines(view, _mapping_children(operation)),  # Each stored child body.
        writes_enabled=writes_enabled(),  # Keep the deployment write gate visible.
        schedule=OrgScheduleView.build(operation, view["start_time"]),  # Issue #3247: the start line and form.
        prechecks=prechecks,  # Issue #3243: the card and the gate of the confirmation field.
    )


def _saved_operation(options: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return the durable plan that the saved options name, or None for an AP-only request."""
    operation_id = str(options.get("operation_id", ""))  # Read only the durable identity from the session.
    return _read_operation(operation_id) if operation_id else None  # Read the confirmed plan from storage.


def precheck_gate() -> OrgPrecheckGate:
    """Return the pre-check gate over the adopter seam of the single-site portal.

    Why:
        Issue #3243. Both modes read the pre-check capture through one seam. A
        site that passes the gate of the single-site run then passes the gate
        of the multi-site operation too.

    Returns:
        The gate. With no adopter seam, the gate stays closed for each site.
    """
    adopter = upgrade_routes.precheck_adopter()  # The same seam as the single-site run create call.
    if adopter is None:  # No wiring, so no site holds a readable capture.
        return OrgPrecheckGate(None)  # The gate fails closed.
    return OrgPrecheckGate(partial(upgrade_routes.read_precheck_pair, adopter))  # One read for each site.


def _submission_prechecks(context: SubmissionContext, operation: Mapping[str, Any] | None) -> OrgPrecheckState:
    """Read the pre-check capture of each site of one confirmed submission.

    Args:
        context: The validated scope of the submission.
        operation: The durable plan, or None for a request for access points only.

    Returns:
        The state of the gate, in the order of the selection.
    """
    stored = operation.get("site_names") if operation is not None else None  # The approved names of the plan.
    names = {str(key): str(value) for key, value in stored.items()} if isinstance(stored, Mapping) else {}
    return precheck_gate().read(context.site_ids, names)  # A site with no name shows its identifier.


def _precheck_refusal(prechecks: OrgPrecheckState) -> tuple[Response, int] | None:
    """Return the refusal of a start with a site that holds no pre-check capture, or None."""
    if prechecks.ready:  # Each selected site holds a verified pre-check capture.
        return None  # The start continues to the site locks.
    names = prechecks.missing_names()  # The sites that close the gate, in the order of the selection.
    logger.warning("The organization upgrade start stops, because %d sites hold no pre-check", len(prechecks.missing))
    message = PRECHECK_MISSING_MESSAGE.format(names=names)  # The cure and each site.
    return json_error(CONFLICT_STATUS, upgrade_routes.PRE_CAPTURE_MISSING_CODE, message)  # The single-site code.


def _confirmation_targets(operation: Mapping[str, Any] | None) -> tuple[int, list[str]]:
    """Return the aggregate target count and device families."""
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


def confirmation_value() -> str:
    """Return the typed confirmation from JSON or form data."""
    payload: Any = request.get_json(silent=True)  # A body that is not JSON reads as None, never a fault.
    source = payload if isinstance(payload, Mapping) else request.form  # Prefer a valid JSON object.
    return str(source.get("confirmation", ""))  # An absent field reads as empty text, which matches no word.


def _submission_is_repeated(request_nonce: object) -> bool:
    """Return true when the current options cannot start another job."""
    previous = session.get(LAST_JOB_SESSION_KEY)  # The signed marker of the last job of this browser.
    if not isinstance(previous, dict):  # No earlier job, so no replay exists.
        return False
    previous_state = str(previous.get("state", ""))  # The last state that a read stored in the marker.
    return (  # Issue #3225: the service owns the one set of final states.
        previous_state not in FINAL_OPERATION_STATES
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
    except Exception as error:  # Keep broad because any failure after the write leaves the outcome unknown.
        logger.exception(
            "The organization upgrade submission outcome is unknown after %s: %s",
            type(error).__name__,
            error,
        )
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
    if candidate != dict(record):  # Issue #3249: only a real change moves the update time.
        candidate["updated_at"] = datetime.now(UTC).isoformat()  # The progress page shows the age of the change.
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
    scope = OperationLockScope(org_id, operation_id, owner, select_routes.lock_client())  # The shared values.
    for site_id in site_ids:  # Acquire each selected site before any cloud write.
        refusal = _operation_site_lock(operation, scope, site_id)  # Take or bind the lock of one site.
        if refusal is not None:  # One site that the operation cannot hold stops every child.
            return refusal  # Preserve the lock code and the lock message.
    return None  # Every selected site lock is durable and bound to this operation.


def _operation_site_lock(
    operation: MutableMapping[str, Any], scope: OperationLockScope, site_id: str
) -> tuple[Response, int] | None:
    """Take or bind the lock of one site, and store the lock in the operation record."""
    held = lock.read_lock(scope.org_id, site_id, scope.client)  # Detect a lock of this operator.
    try:  # Lock writes fail closed and use no memory fallback.
        record = _operation_lock_record(scope, site_id, held)  # The lock that now names the operation.
    except lock.SiteLockError as fault:  # Map the lock error to a safe API response.
        return _lock_fault(fault)  # Preserve the code and the message of the lock module.
    if record is None:  # The operator holds the site for another run.
        return json_error(CONFLICT_STATUS, SITE_LOCK_WRONG_RUN, SITE_LOCK_WRONG_RUN_MESSAGE)  # Refuse unsafe reuse.
    return _store_site_lock(operation, site_id, record)  # Persist this lock before the next site.


def _operation_lock_record(
    scope: OperationLockScope, site_id: str, held: lock.LockRecord | None
) -> lock.LockRecord | None:
    """Return the lock that binds one site to the operation, or None for a lock of another run.

    Why:
        Issue #3243. The pre-check capture of the confirm page takes the site
        with no run, as the capture page does. The start then binds that lock
        to the operation and keeps its token. The start still refuses a lock
        of the same operator that names another run.

    Raises:
        SiteLockError: When the store refuses the lock or does not answer.
    """
    mine = held is not None and held.held_by(scope.owner)  # The same operator and the same browser.
    if held is not None and mine and held.run_id not in ("", scope.operation_id):  # A lock of another run.
        return None  # The caller refuses the start.
    if held is not None and mine and held.run_id == "":  # Issue #3243: a lock of a pre-check capture.
        bound = held.bound_to_run(scope.operation_id)  # The same token, with the name of the operation.
        logger.info("Bind the pre-check lock of site %s to aggregate upgrade %s", site_id, scope.operation_id)
        lock.refresh_site_lock(lock.build_key(scope.org_id, site_id), bound, scope.client)  # Compare the token.
        logger.debug("The lock of site %s now names aggregate upgrade %s", site_id, scope.operation_id)  # After.
        return bound  # The stored copy names the operation.
    request_record = lock.LockRequest(scope.org_id, site_id, scope.owner, scope.operation_id)  # A new lock.
    logger.info("Acquire site %s for aggregate upgrade %s", site_id, scope.operation_id)  # Log before acquisition.
    return lock.acquire_site_lock(request_record, scope.client).record  # Atomically acquire or resume this lock.


def _lock_fault(fault: lock.SiteLockError) -> tuple[Response, int]:
    """Return the answer of one lock error: 503 for an unreachable store, and 409 for the others."""
    unreachable = isinstance(fault, lock.LockStoreUnreachableError)  # The store did not answer.
    status = SERVICE_UNAVAILABLE_STATUS if unreachable else CONFLICT_STATUS  # The contract status.
    logger.warning("The site lock step of an aggregate upgrade reported %s", fault.code)  # Name the safe code only.
    return json_error(status, fault.code, str(fault))  # Preserve the lock module's code and message.


def _store_site_lock(
    operation: MutableMapping[str, Any], site_id: str, record: lock.LockRecord
) -> tuple[Response, int] | None:
    """Store one site lock in the operation record through one compare-and-set write."""
    replacement = dict(operation)  # Build a detached CAS replacement.
    stored_locks = dict(replacement.get("site_locks", {}))  # Preserve locks acquired for earlier sites.
    stored_locks[site_id] = record.to_record()  # Store the JSON-safe lock record.
    replacement["site_locks"] = stored_locks  # Attach the updated lock map.
    if not _cas_operation(operation, replacement):  # Persist this lock before the next acquisition.
        return json_error(SERVICE_UNAVAILABLE_STATUS, SUBMISSION_FAILED, "The portal could not store a site lock.")
    logger.debug("Aggregate upgrade %s stores the lock for site %s", operation.get("operation_id", ""), site_id)
    return None  # The lock is durable in the record.


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
    {"completed", "cancelled", "failed"}
)
# WHY: Issue #3220. `attention_required` once released every site lock, and a
# normal cloud word such as `upgrading` produced that state during the write.
# A lock now stays until each child holds a state in which no firmware write can
# follow. An uncertain child (`submission_unknown`, `read_unknown`) keeps the
# sites, and the lease then expires on its own if no read reconciles it.
FINAL_WRITE_STATES = frozenset(  # Child states in which no firmware write can follow.
    {"completed", "cancelled", "failed", "rejected", "not_submitted"}
)


def release_operation_locks(operation: MutableMapping[str, Any]) -> None:
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
    """Return true when no child of one operation can still write firmware.

    Why:
        A cancel request does not stop a device that already writes firmware,
        and a normal cloud word once read as `attention_required` (issue
        #3220). Only the state of every child proves that the sites are safe
        to release.
    """
    children = [child for child in operation.get("children", ()) if isinstance(child, Mapping)]  # Valid rows.
    if not children:  # A damaged record with no child keeps the conservative state rule.
        return str(operation.get("state", "")) in SETTLED_OPERATION_STATES  # Only a final aggregate state.
    states = [str(child.get("status", "")).strip().lower() for child in children]  # One word for each child.
    return all(state in FINAL_WRITE_STATES for state in states)  # Every child must be past any write.


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
    prechecks: OrgPrecheckState,
) -> Response | tuple[Response, int]:
    """Submit every child through the aggregate boundary."""
    if not _record_operator(operation):  # FR-009: the record names the operator before any lock or cloud write.
        return json_error(
            SERVICE_UNAVAILABLE_STATUS,
            SUBMISSION_FAILED,
            "The portal could not record the operator. Read the operation before another action.",
        )
    if not _record_prechecks(operation, prechecks):  # Issue #3243: the baseline of each site, before any lock.
        return json_error(SERVICE_UNAVAILABLE_STATUS, SUBMISSION_FAILED, PRECHECK_RECORD_MESSAGE)
    site_ids = [str(value) for value in operation.get("site_ids", [])]  # Read the durable lock scope.
    refusal = _acquire_operation_locks(operation, str(operation.get("org_id", "")), site_ids)  # Lock all sites.
    if refusal is not None:  # Stop before the parent or child claim.
        return refusal  # Preserve the existing lock error response.
    _prepare_phase_watch(cloud_session, operation)  # Issue #3245: store the anchors before the first write.
    failure = _send_aggregate(cloud_session, operation)  # Send each planned child at most once.
    if failure is not None:  # A replay, a malformed plan, or an unknown outcome stops the flow here.
        return failure  # Preserve the mapped error response.
    release_operation_locks(operation)  # Free every site when no child can still write firmware.
    _start_phase_watch(cloud_session, operation)  # Issue #3245: follow each phase after the cloud accepts a job.
    session.pop(ORG_UPGRADE_RETRY_KEY, None)  # Issue #3247: the retry ends when its new plan reaches the cloud.
    return next_page_answer(f"/upgrade/org/jobs/{operation['operation_id']}")  # Show one seamless operation.


def _send_aggregate(cloud_session: Any, operation: MutableMapping[str, Any]) -> tuple[Response, int] | None:
    """Send every planned child through the aggregate boundary, and map a fault to a response.

    Args:
        cloud_session: The signed cloud session of the operator.
        operation: The durable operation record. The service updates it in place.

    Returns:
        None after the service stored every child outcome, or the error response.
    """
    logger.info("Send the child jobs of aggregate upgrade %s", operation.get("operation_id", ""))  # Before.
    try:  # The service persists before and after every destructive action.
        aggregate_service().submit(  # Submit through atomic claims and immediate lock refreshes.
            cloud_session,
            operation,
            upgrade_routes.run_store(),
            _refresh_child_locks,
        )
    except ValueError as error:  # A replay or a malformed plan is a conflict.
        operation_id = str(operation.get("operation_id", ""))  # Issue #3242: the store decides the link.
        return OrgReplayRefusal.aggregate(operation_id, error)  # No child job goes to the cloud again.
    except Exception as error:  # Keep broad because aggregate child writes can leave mixed unknown outcomes.
        logger.exception(
            "The aggregate upgrade submission outcome is unknown after %s: %s",
            type(error).__name__,
            error,
        )  # Preserve the aggregate write fault in the log.
        return json_error(  # The operator must read the operation before another action.
            SERVICE_UNAVAILABLE_STATUS,
            SUBMISSION_FAILED,
            "One or more child outcomes are unknown. Read the operation before another action.",
        )
    logger.debug(  # After the submission. The state names the result of the child jobs.
        "Aggregate upgrade %s now has state %s", operation.get("operation_id", ""), operation.get("state")
    )
    return None  # The caller releases the settled sites and starts the phase watch.


def _prepare_phase_watch(cloud_session: Any, operation: MutableMapping[str, Any]) -> None:
    """Store the settle anchors, the four phases, and the first watch state before the first write.

    Why:
        Issue #3245. FR-001 reads the uptime of each device before the cloud
        receives a firmware write. FR-002 says that a failed read never blocks
        the upgrade, so this function logs a fault and returns.

    Args:
        cloud_session: The signed cloud session of the operator.
        operation: The durable operation record. A stored change updates it in place.
    """
    if WATCH_KEY in operation:  # A repeated submission keeps the anchors of the first try.
        return  # Write nothing, and continue.
    reader = current_app.config.get(ANCHOR_READER_CONFIG_KEY, OrgSettleAnchors.read)  # A test reaches no cloud.
    logger.info("Read the settle anchors of aggregate upgrade %s", operation.get("operation_id", ""))  # Before.
    try:  # The read and the write can fail, and neither may stop the upgrade.
        found = reader(cloud_session, operation)  # FR-001: one statistics read for each device family.
        stored = _cas_operation(operation, OrgPhaseWatch.prepared(operation, found.anchors, found.note))  # One write.
    except Exception as error:  # Keep broad: FR-002 says that the anchors never block the upgrade.
        logger.warning("The settle anchor step failed with %s", type(error).__name__)  # Name the type only.
        return  # The submission continues with no phase watch.
    logger.debug("The settle anchor write returned %s", stored)  # A lost race leaves no watch fields.


def _start_phase_watch(cloud_session: Any, operation: Mapping[str, Any]) -> None:
    """Start the phase watch of one operation when no watch thread runs.

    Why:
        Issue #3245. The watch starts after the cloud accepts a child job. The
        page and each status poll call this function too, so a watch starts
        again after a portal restart (FR-012). The registry refuses a second
        thread for the same operation.

    Args:
        cloud_session: The signed cloud session of the operator. The watch reads with it and never writes.
        operation: The durable operation record.
    """
    starter = current_app.config.get(CASCADE_STARTER_CONFIG_KEY, OrgCascadeRegistry.ensure_running)  # A test seam.
    logger.info("Check the phase watch of aggregate upgrade %s", operation.get("operation_id", ""))  # Before.
    post_check = _bind_post_check(operation, cloud_session)  # Issue #3244: None when the seam cannot bind.
    try:  # The page must answer even when the watch cannot start.
        deps = OrgCascadeDeps(
            store=upgrade_routes.run_store(), session=cloud_session, post_check=post_check
        )  # The wall clock, the wait, and the post-check seam.
        started = starter(operation, deps)  # FR-012: at most one thread for each operation.
    except Exception as error:  # Keep broad: a fault in the watch start must not hide the progress page.
        logger.warning("The phase watch start failed with %s", type(error).__name__)  # Name the type only.
        return  # The next poll tries again.
    logger.debug("The phase watch start returned %s", started)  # True only when this call started a thread.


def _bind_post_check(operation: Mapping[str, Any], cloud_session: Any) -> OrgPostCheckBridge | None:
    """Bind the post-check seam of one operation, or return None when it cannot bind.

    Why:
        Issue #3244. The walk takes the post-check capture of each site through
        this seam. A fault in the seam must not stop the phase watch, so the
        walk then ends each phase and takes no post-check capture.

    Args:
        operation: The durable operation record.
        cloud_session: The signed cloud session of the operator.

    Returns:
        The bridge, or None when a seam cannot bind.
    """
    try:  # The phase watch must start even when the seam cannot bind.
        return OrgPostCheckBridge.bind(operation, cloud_session)  # Binds inside this request.
    except Exception as error:  # Keep broad: FR-011 keeps the watch alive after a post-check fault.
        logger.warning("The post-check seam bind failed with %s", type(error).__name__)  # Name the type only.
        return None  # The walk logs that it holds no post-check seam.


def _record_operator(operation: MutableMapping[str, Any]) -> bool:
    """Store the typed operator address and the Mist account before the first cloud write.

    Why:
        Issue #3249. A single-site run records the typed address and the Mist
        account of the operator who started it. FR-009 asks the multi-site
        record for the same two facts, before any child reaches the cloud.

    Args:
        operation: The durable operation record.

    Returns:
        True when the record holds both facts, and False when the write failed.
    """
    if "actor_email" in operation:  # A repeated submission keeps the first operator record.
        return True  # Write nothing, and continue.
    logger.info("Record the operator of aggregate upgrade %s", operation.get("operation_id", ""))  # Before the read.
    replacement = {  # Keep every field of the plan, and add the two audit facts.
        **operation,
        "actor_email": upgrade_routes.actor_address(),  # The typed address of the signed operator.
        "cloud_account": upgrade_routes.read_cloud_account(),  # The Mist account behind the cloud session.
    }
    recorded = _cas_operation(operation, replacement)  # One compare-and-set write, before any site lock.
    logger.debug("The operator record write returned %s", recorded)  # Log the result, not the address.
    return recorded  # A stale record stops the submission before any lock.


def _record_prechecks(operation: MutableMapping[str, Any], prechecks: OrgPrecheckState) -> bool:
    """Store the pre-check capture of each site before the first site lock.

    Why:
        Issue #3243. The comparison after the upgrade needs the baseline of
        each site. The list changes only while the plan waits for its first
        claim, so a repeated start never moves the baseline of a started run.

    Args:
        operation: The durable operation record.
        prechecks: The state of the gate, which is ready.

    Returns:
        True when the record holds the list, and False when the write failed.
    """
    wanted = prechecks.stored()  # One entry for each site, in the order of the selection.
    if operation.get(PRECHECK_FIELD) == wanted:  # A repeated start with the same captures.
        return True  # Write nothing, and continue.
    if operation.get("state") != PLANNED_STATE or operation.get("submission_claim_id"):  # A claimed plan.
        return True  # Keep the list of the first claim. The service then refuses the replay.
    logger.info("Record the pre-check captures of aggregate upgrade %s", operation.get("operation_id", ""))  # Before.
    recorded = _cas_operation(operation, {**operation, PRECHECK_FIELD: wanted})  # One write before any lock.
    logger.debug("The pre-check record write returned %s", recorded)  # Log the result only.
    return recorded  # A stale record stops the submission before any lock.


class OrgReplayRefusal:
    """Build the refusal of a repeated start, and name the job that the first start began.

    Why:
        Issue #3242. A second click or a second tab sent the same confirmed
        plan again. The portal refused the repeated start, but the refusal
        named no job, so the operator could not find the upgrade that ran. The
        refusal now links the job when the durable record or the signed
        session marker proves a start. A refusal that started no job links
        nothing, so the page never sends the operator to an empty job.
    """

    @staticmethod
    def answer(message: str, upgrade_id: str = "") -> tuple[Response, int]:
        """Return the conflict answer, with the job link when the job is known.

        Args:
            message: The plain sentence for the operator.
            upgrade_id: The job that the first start began. An empty value names no job.

        Returns:
            The JSON error answer and the conflict status.
        """
        details = None  # No proven job means no link.
        if upgrade_id:  # The record or the marker names the job of the first start.
            details = {"upgrade_id": upgrade_id, "next": f"/upgrade/org/jobs/{upgrade_id}"}  # The page link.
        return jsonify(build_error_envelope(ALREADY_SUBMITTED, message, details)), CONFLICT_STATUS  # One shape.

    @classmethod
    def legacy(cls) -> tuple[Response, int]:
        """Refuse a repeated access point start, and name its cloud job when the marker holds one.

        Returns:
            The conflict answer of the legacy path.
        """
        marker = session.get(LAST_JOB_SESSION_KEY)  # The signed marker of the last access point start.
        upgrade_id = marker.get("upgrade_id") if isinstance(marker, Mapping) else None  # The cloud job, if known.
        logger.info("Refuse a repeated organization upgrade start on the access point path")  # Before the answer.
        if not isinstance(upgrade_id, str) or not upgrade_id:  # The first cloud answer named no job.
            logger.debug("The repeated start names no job, because the first cloud answer is unknown")  # After.
            return cls.answer(UNKNOWN_REPLAY_MESSAGE)  # The operator reconciles before another start.
        logger.debug("The repeated start names the cloud job %s", upgrade_id)  # Log the decision.
        return cls.answer(LEGACY_REPLAY_MESSAGE, upgrade_id)  # Link the job that the first start began.

    @classmethod
    def aggregate(cls, operation_id: str, error: ValueError) -> tuple[Response, int]:
        """Refuse a repeated multi-site start, and link the operation when its record proves a start.

        Args:
            operation_id: The durable operation of the confirmed plan.
            error: The refusal of the aggregate service.

        Returns:
            The conflict answer of the durable path.
        """
        logger.info("Read aggregate upgrade %s for the refusal of a repeated start", operation_id)  # Before.
        record = _read_operation(operation_id) if operation_id else None  # The store holds the proof.
        if record is None or not cls.started(record):  # No child left the plan, so no link is safe.
            logger.debug("Aggregate upgrade %s shows no start, so the refusal links nothing", operation_id)  # After.
            return cls.answer(str(error))  # Keep the sentence of the service.
        logger.debug("Aggregate upgrade %s shows a start, so the refusal links it", operation_id)  # After.
        return cls.answer(AGGREGATE_REPLAY_MESSAGE, operation_id)  # Link the operation that runs.

    @staticmethod
    def started(record: Mapping[str, Any]) -> bool:
        """Return True when the durable record proves that a start reached the aggregate service.

        Args:
            record: The durable operation record.

        Returns:
            True for a parent claim or for a child that left the plan.
        """
        if record.get("state") == SUBMISSION_CLAIMED_STATE:  # A first request holds the claim now.
            return True  # The first request runs, so its operation page exists.
        children = record.get("children")  # Each child keeps its own status.
        rows = children if isinstance(children, list) else []  # A damaged list proves nothing.
        return any(isinstance(row, Mapping) and row.get("status") != PLANNED_STATE for row in rows)  # A start.


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
    prechecks = _submission_prechecks(loaded, operation)  # Issue #3243: the pre-check capture of each site.
    refusal = _precheck_refusal(prechecks)  # The rule of the single-site start, before any write.
    if refusal is not None:  # One site holds no verified pre-check capture.
        return refusal  # No record change, no site lock, and no child job.
    if operation is not None and _operation_matches_context(operation, loaded):  # Require the exact durable plan.
        return _submit_aggregate(loaded.cloud_session, operation, prechecks)  # Submit each child at most once.
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
        return OrgReplayRefusal.legacy()  # Issue #3242: name the job of the first start when it is known.
    if confirmation_value() != "CONFIRM":  # Require the exact typed confirmation.
        return json_error(BAD_REQUEST_STATUS, CONFIRMATION_REQUIRED, CONFIRMATION_MESSAGE)
    if _operator_cannot_answer():  # A multi-site write reaches many devices, so it needs an accountable name.
        return json_error(BAD_REQUEST_STATUS, UNREACHABLE_OPERATOR, UNREACHABLE_OPERATOR_MESSAGE)  # Names the cure.
    return None  # Continue to the scope and lock checks.


def _operator_cannot_answer() -> bool:
    """Report whether the signed operator address can answer for a firmware write.

    Why:
        Issue #2615. A reserved domain such as `.invalid` reaches no mailbox, so
        no person can answer for the firmware that this route writes. The
        single-site route already refuses such an address. This route writes
        firmware to every selected site, so it needs the same guard.

    Returns:
        True when the portal must refuse the write.
    """
    owner = identity.current_owner()  # The session guard already refused an unsigned request.
    actor = owner.actor_email if owner is not None else ""  # An empty address never reaches a log record.
    logger.info("org upgrade: check that the operator address can answer for a firmware write")  # No address logged.
    if not actor:  # A blank address names nobody, so the write fails closed.
        logger.debug("org upgrade: the operator address is absent, so the write is refused")  # Safe result summary.
        return True  # A session without an address can never answer for production firmware.
    reserved = identity.address_uses_reserved_domain(actor)  # One shared rule serves both upgrade routes.
    logger.debug("org upgrade: the operator address uses a reserved domain: %s", reserved)  # Report no address.
    return reserved  # A reserved domain cannot name an accountable operator.


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
        "current_phase": OrgPhaseEntries.active_label(record),  # Issue #3245: the phase that the watch follows.
        "total": totals[0],
        "upgraded_count": totals[1],
        "failed_count": totals[2],
        "site_upgrades": rows,
        "children": rows,
        "errors": list(record.get("errors", [])),
        "cancellation": record.get("cancellation"),
        "cancel_allowed": record.get("state") not in FINAL_OPERATION_STATES,  # Issue #3225: the form rule.
        **_aggregate_record_view(record),  # Issue #3249: the device rows, the operator, and the age.
    }


def _aggregate_record_view(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return the device rows, the operator, the Mist account, and the age of one operation.

    Why:
        Issue #3249. The single-site page shows each device, the typed operator
        address, the Mist account, and the last update time. The multi-site
        page and its poll now show the same facts from the durable record.

    Args:
        record: The durable operation record.

    Returns:
        The public fields that the page and the poll add to the summary.
    """
    age = RunStalePolicy(datetime.now(tz=UTC)).assess(record)  # The age rule of the single-site page.
    rows = OrgDeviceRows(record).rows()  # One row for each target of each child, built one time.
    phase = OrgPhaseView.build(record)  # Issue #3245: built one time, because the post-check card reads its flag.
    return {
        "devices": rows,  # The device table of the page and the poll.
        "operator_address": str(record.get("actor_email") or ""),  # An earlier record holds no address.
        "cloud_account": str(record.get("cloud_account") or ""),  # An earlier record holds no account.
        "updated_at": age.updated_at,  # The normalized UTC time, or empty text.
        "age_text": age.age_text,  # A short age, or "unknown".
        "controls": OrgControlsView.build(record, retry_plan_of(record, rows)),  # Issue #3247: the recovery.
        "cancel_outcomes": OrgCancelOutcomes.rows(record),  # Issue #3246: the three lists of each cancel.
        "prechecks": OrgPrecheckGate.rows_of(record),  # Issue #3243: the pre-check capture of each site.
        "postchecks": OrgPostCheckView.rows(record, bool(phase["phase_active"])),  # Issue #3244: FR-012 and FR-014.
        **phase,  # Issue #3245: the four phases, the watch line, and the poll rule.
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
        "cloud_status": child.get("cloud_status", ""),  # The exact cloud word behind the state (issue #3220).
        "total": total,
        "upgraded": upgraded,
        "failed": failed,
        "error": child.get("error"),
        "cancellation": child.get("cancellation"),
        "cancellation_text": OrgCancelText.text(child.get("cancellation")),  # Issue #3225: one text for both paints.
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


def owned_saved_operation(operation_id: str, org_id: str) -> dict[str, Any] | None:
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
    operation = owned_saved_operation(upgrade_id, org_id)  # Read only an owned durable operation.
    if operation is not None:  # Aggregate paths keep the existing visible URL.
        _refresh_aggregate(cloud_session, operation)  # Read each child and preserve read failures.
        return _aggregate_job_page(upgrade_id, operation)  # Render all child results together.
    refusal = _unowned_job_refusal(upgrade_id, org_id)  # Issue #3241: no page for a job of another browser.
    if refusal is not None:  # This browser did not start the job.
        return refusal  # Read no cloud job and render no control.
    return _org_job_page(cloud_session, org_id, upgrade_id)  # Keep the AP-only page behavior.


def _unowned_job_refusal(upgrade_id: str, org_id: str) -> tuple[Response, int] | None:
    """Refuse an AP-only job view that this browser session did not start.

    Why:
        Issue #3241. When no owned aggregate operation matched the identifier,
        the page and the status poll read the cloud job of any identifier and
        rendered it with an armed cancel form. The cancel route already refused
        that job through `_owns_org_job`, so the view now follows the same rule.

    Args:
        upgrade_id: The job identifier of the address.
        org_id: The selected organization.

    Returns:
        The refusal envelope, or None when this browser owns the job.
    """
    if _owns_org_job(upgrade_id, org_id):  # The signed marker names this job and this organization.
        return None  # The caller reads and renders the job.
    logger.warning("Refused an organization job view that this browser session did not start")  # No identifier.
    return json_error(CONFLICT_STATUS, JOB_NOT_OWNED, "This browser session did not start that organization job.")


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
    try:  # A failed status read must not hide the last durable state.
        aggregate_service().status(cloud_session, operation, upgrade_routes.run_store())  # Persist each child.
    except Exception as error:  # Keep broad because the status page must show the last durable state.
        logger.exception(
            "The aggregate upgrade status read failed with %s: %s",
            type(error).__name__,
            error,
        )  # Record the unknown read outcome.
    _refresh_device_versions(cloud_session, operation)  # Issue #3249: read the versions that the table needs.
    release_operation_locks(operation)  # Free every site as soon as the operation settles.
    _start_phase_watch(cloud_session, operation)  # Issue #3245: start the watch again after a portal restart.
    logger.debug(  # After the refresh.
        "The aggregate upgrade refresh finished with state %s", operation.get("state", "unknown")
    )


def _refresh_device_versions(cloud_session: Any, operation: MutableMapping[str, Any]) -> None:
    """Read the running versions that the device table needs, and store them.

    Why:
        Issue #3249. FR-005 names the running version as the version after.
        FR-007 bounds the reads, and FR-008 stores them through one write. A
        fault here must not hide the page, so this function logs the fault and
        keeps the last durable readings.

    Args:
        cloud_session: The signed cloud session of the operator.
        operation: The durable operation record. A stored change updates it in place.
    """
    reader = current_app.config.get(DEVICE_VERSION_READER_CONFIG_KEY, OrgVersionRefresh.running_versions)
    try:
        result = OrgVersionRefresh(reader).collect(cloud_session, operation)  # Read only the sites that need it.
        if result.changes:  # A refresh with no news writes nothing, so the update time stays.
            aggregate_service().record_device_versions(  # Store every reading through one write.
                operation,
                upgrade_routes.run_store(),
                result.readings,
                result.final_child_ids,
            )
    except Exception as error:  # Keep broad because the progress page must show the last durable readings.
        logger.exception(
            "The device version refresh failed with %s: %s",
            type(error).__name__,
            error,
        )  # Record the fault, and keep the page readable.


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
    except RequestException as error:
        logger.exception(
            "The organization upgrade status read failed with %s: %s",
            type(error).__name__,
            error,
        )
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
    operation = owned_saved_operation(upgrade_id, org_id)  # Read only an owned durable operation.
    if operation is not None:  # Return every aggregate child in one browser response.
        _refresh_aggregate(cloud_session, operation)  # Read and persist each child.
        return jsonify(aggregate_summary(operation)), OK_STATUS  # Preserve mixed results.
    refusal = _unowned_job_refusal(upgrade_id, org_id)  # Issue #3241: no status for a job of another browser.
    if refusal is not None:  # This browser did not start the job.
        return refusal  # Read no cloud job.
    return _org_status_response(cloud_session, org_id, upgrade_id)  # Keep the AP-only response.


def _org_status_response(cloud_session: Any, org_id: str, upgrade_id: str) -> tuple[Response, int]:
    """Return the existing AP-only polling response."""
    try:  # Map validation and cloud read failures to the existing responses.
        result = upgrade_service().status(cloud_session, org_id, upgrade_id)  # Read the AP job once.
    except (TypeError, ValueError) as error:
        return json_error(BAD_REQUEST_STATUS, STATUS_FAILED, str(error))
    except RequestException as error:
        logger.exception(
            "The organization upgrade status read failed with %s: %s",
            type(error).__name__,
            error,
        )
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
    except Exception as error:  # Keep broad because any failure after the cancel write leaves the outcome unknown.
        logger.exception(
            "The organization upgrade cancellation outcome is unknown after %s: %s",
            type(error).__name__,
            error,
        )
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
    return owned_saved_operation(upgrade_id, org_id)  # Enforce owner and organization matches.


def _cancellation_guard() -> tuple[Response, int] | None:
    """Apply safeguards that precede every cancellation."""
    if not writes_enabled():  # Keep the deployment write gate.
        return json_error(
            SERVICE_UNAVAILABLE_STATUS,
            WRITE_DISABLED,
            "Organization upgrade writes stay disabled until the multi-site safety gates are complete.",
        )
    if confirmation_value() != "CANCEL":  # Require the exact typed confirmation.
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
    except FinalOperationError as error:  # Issue #3225: a final operation sent no cloud request.
        logger.warning("Refused the cancel of final aggregate upgrade %s", upgrade_id)  # No write followed.
        return json_error(CONFLICT_STATUS, NOT_CANCELLABLE, str(error))  # The single-site stop uses 409 too.
    except ValueError as error:  # A replay or malformed state is a conflict.
        return json_error(CONFLICT_STATUS, CANCEL_FAILED, str(error))
    except Exception as error:  # Keep broad because aggregate child cancellations can leave mixed outcomes.
        logger.exception(
            "The aggregate upgrade cancellation outcome is unknown after %s: %s",
            type(error).__name__,
            error,
        )  # Preserve an unknown outcome without a hidden retry.
        return json_error(
            SERVICE_UNAVAILABLE_STATUS,
            CANCEL_FAILED,
            "One or more cancellation outcomes are unknown. Read the operation before another action.",
        )
    logger.debug("The aggregate cancellation %s finished with state %s", upgrade_id, operation.get("state", ""))
    release_operation_locks(operation)  # Free every site after each child holds a cancellation result.
    if _wants_html():  # Keep the browser on one visible operation.
        return next_page_answer(f"/upgrade/org/jobs/{upgrade_id}")  # Return the existing redirect response.
    return jsonify(aggregate_summary(operation)), OK_STATUS  # Show every child cancellation result.


def _cancel_org_job(upgrade_id: str) -> tuple[Response, int]:
    """Cancel the existing AP-only organization job."""
    context = _cancel_context(upgrade_id)  # Enforce browser ownership and organization scope.
    if not isinstance(context[0], str):  # Return the existing ownership or context error.
        return context  # Stop before the cloud call.
    final_refusal = _final_job_refusal()  # Issue #3225: a final job gets no cloud cancel call.
    if final_refusal is not None:  # The last read of this browser stored a final state.
        return final_refusal  # Stop before the cloud call.
    org_id, cloud_session = context  # Use the validated legacy cancel context.
    result = _call_cancellation(cloud_session, org_id, upgrade_id)  # Send the one cloud cancel call.
    if not isinstance(result, OrgUpgradeResult):  # Return a mapped validation or unknown failure.
        return result  # Preserve the existing response.
    refusal = result_error(result, CANCEL_FAILED)  # Reject an invalid cloud response.
    if refusal is not None:  # Preserve the existing gateway response.
        return refusal  # Stop before a false cancellation result.
    if _wants_html():  # Keep the browser on the existing progress page.
        return next_page_answer(f"/upgrade/org/jobs/{upgrade_id}")  # Return the existing redirect response.
    return jsonify({"upgrade_id": upgrade_id, "cancel_requested": True}), OK_STATUS  # Preserve the JSON shape.


def _final_job_refusal() -> tuple[Response, int] | None:
    """Refuse a cancel of an organization job that a read already found final.

    Why:
        Issue #3225. Each page view and each poll store the last state in the
        signed job marker. A job in a final state cannot change, so a cancel
        request only misreports it. The single-site stop answers 409 for a
        final run in the same way.

    Returns:
        The refusal envelope, or None when the job can still change.
    """
    marker = session.get(LAST_JOB_SESSION_KEY)  # The signed marker of the owned job.
    state = str(marker.get("state", "")) if isinstance(marker, dict) else ""  # The last stored state.
    if state not in FINAL_OPERATION_STATES:  # A live or unread job keeps the cancel.
        return None
    logger.warning("Refused the cancel of an organization job in the final state %s", state)  # No identifier.
    return json_error(CONFLICT_STATUS, NOT_CANCELLABLE, FINAL_CANCEL_TEXT.format(state=state))  # No cloud call.


def _wants_html() -> bool:
    """Return true when content negotiation selects HTML."""
    return request.accept_mimetypes.best_match(("application/json", "text/html")) == "text/html"  # Match existing.
