"""Serve the protected graphical menu 305 workflow outside generic safe operations."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from flask import Blueprint, Response, current_app, jsonify, make_response, redirect, request, session
from mistapi.api.v1.msps import orgs
from werkzeug.exceptions import HTTPException

from src.operations.execution.firmware_policy import PolicyInventory
from src.operations.execution.firmware_policy.changes import POLICY_TYPES, FirmwarePolicy
from src.operations.execution.firmware_policy.cli import PolicyCatalog
from src.operations.execution.firmware_policy.sdk import PolicyApi, PolicyError, PolicyResponse, SettingsRequestGuard

from .jobs import PortalJobs
from .jobs.state import JobErrors
from .jobs.workflows import JobWorkflows
from .restore import restore_bp

logger = logging.getLogger(__name__)
firmware_policy_bp = Blueprint("firmware_policy", __name__, template_folder="templates")
firmware_policy_bp.register_blueprint(restore_bp)


class PortalPolicyInputs:
    """Validate graphical input and obtain only the existing portal API context."""

    @staticmethod
    def api() -> PolicyApi:
        """Refuse a portal without a valid Mist session before any external read."""
        api_session = current_app.config.get("APISESSION")  # Use the existing authenticated SDK session.
        if api_session is None:
            raise PolicyError("The portal has no Mist API session.")
        return PolicyApi(api_session)  # Do not create or persist another credential.

    @staticmethod
    def organizations(values: Any) -> list[str]:
        """Accept a bounded, explicit set of unique organization identifiers."""
        if not isinstance(values, list) or not values or len(values) > 100:
            raise PolicyError("Select between 1 and 100 organizations.")
        identifiers = [
            PolicyResponse.identifier(value.get("id", "") if isinstance(value, dict) else value) for value in values
        ]  # Validate the identifier and discard any browser-provided organization name.
        if len(set(identifiers)) != len(identifiers):
            raise PolicyError("Select each organization only once.")
        return identifiers  # Resolve every name through the authenticated SDK, never posted names.

    @staticmethod
    def policies(values: Any) -> list[FirmwarePolicy]:
        """Reject unrecognized fields, malformed model maps, and implicit enablement."""
        if not isinstance(values, list) or not values or len(values) > 4:
            raise PolicyError("Select between 1 and 4 supported device policies.")
        result: list[FirmwarePolicy] = []  # Validate every item before using any field.
        for value in values:
            if not isinstance(value, dict) or set(value) - {"kind", "enabled", "models", "day", "time"}:
                raise PolicyError("The policy input contains an unsupported field.")
            if not isinstance(value.get("models"), dict) or len(value["models"]) > 500:
                raise PolicyError("The policy model choices are not valid.")
            enabled = value.get("enabled")
            if not isinstance(enabled, bool):
                raise PolicyError("Select an explicit enabled or disabled state.")
            result.append(
                FirmwarePolicy(
                    value.get("kind", ""),
                    enabled,
                    value["models"],
                    value.get("day", "any"),
                    value.get("time", "any"),
                )
            )
        return result  # Catalog validation follows before any plan is stored.

    @staticmethod
    def workflows() -> JobWorkflows:
        """Capture validated dependencies before the request context ends."""
        api = PortalPolicyInputs.api()  # Reject missing authenticated context before queue admission.
        return JobWorkflows(api.session, Path(current_app.config["DATA_DIR"]))  # No credentials enter status.

    @staticmethod
    def body() -> dict[str, Any]:
        """Refuse unreadable JSON instead of assuming a successful empty input."""
        value = request.get_json(silent=True)  # Malformed input must be reported as a checked error.
        if not isinstance(value, dict):
            raise PolicyError("Send a JSON object for the policy request.")
        return value  # Individual routes validate their required fields.


class FirmwarePolicyRoutes:
    """Present the dynamic policy controls and run only confirmed settings plans."""

    @staticmethod
    def page() -> Response:
        """Select menu 305 in the protected operations workspace."""
        return make_response(redirect("/operations?menu=305"))  # Legacy links retain the integrated menu layout.

    @staticmethod
    def organizations() -> Response:
        """List the current organization or every organization in a selected MSP."""
        api = PortalPolicyInputs.api()  # Use the authenticated session configured for this portal.
        msp_id = request.args.get("msp_id")  # A missing MSP means the existing current org.
        if msp_id:
            msp_id = PolicyResponse.identifier(msp_id)  # The Mist API enforces the account's MSP access.
            with SettingsRequestGuard(api.session):
                rows = PolicyResponse.collect(
                    api.session,
                    lambda: orgs.listMspOrgs(api.session, msp_id),
                    "List MSP organizations",
                    msp_id,
                    api.guard.request,
                )  # The existing SDK diagnostic guard protects failed identity responses.
        else:
            identifier = PolicyResponse.identifier(current_app.config.get("ORG_ID", ""))
            rows = [api.organization(identifier)]  # A failed identity lookup cannot invent a name.
        result = [{"id": PolicyResponse.identifier(row.get("id", "")), "name": row.get("name")} for row in rows]
        if any(not isinstance(row["name"], str) or not row["name"].strip() for row in result):
            raise PolicyError("The organization name is unavailable. Check the account access.")
        return jsonify({"organizations": result, "count": len(result)})  # No settings body reaches the selector.

    @staticmethod
    def catalog() -> Response:
        """Return dynamically available model/version pairs across the selected orgs."""
        body = PortalPolicyInputs.body()  # Catalog requests read only and create no backup.
        identifiers = PortalPolicyInputs.organizations(body.get("organizations"))
        kinds = body.get("kinds")  # Require explicit selected types instead of querying unsupported types.
        if not isinstance(kinds, list) or not kinds or any(kind not in POLICY_TYPES for kind in kinds):
            raise PolicyError("Select supported device types.")
        show_all = body.get("show_all", False)
        if not isinstance(show_all, bool):
            raise PolicyError("The Show all supported models value must be a boolean.")
        api = PortalPolicyInputs.api()  # Reuse authenticated identity and catalog admission.
        organizations = [api.organization(identifier) for identifier in identifiers]  # Ignore posted names.
        supported = PolicyCatalog.common(api, organizations, kinds)
        catalogs = PolicyInventory.display(api, organizations, supported, show_all)
        return jsonify({"catalogs": catalogs})  # Return only non-secret model and version values.

    @staticmethod
    def preview() -> tuple[Response, int]:
        """Validate choices and capture every complete target before browser confirmation."""
        body = PortalPolicyInputs.body()  # Posted policy fields never become a direct SDK body.
        identifiers = PortalPolicyInputs.organizations(body.get("organizations"))
        policies = PortalPolicyInputs.policies(body.get("policies"))
        work = PortalPolicyInputs.workflows().policy(
            identifiers, policies
        )  # Do not read large scopes on a request thread.
        identifier = PortalJobs.manager().start(PortalJobs.owner(), "policy", work)  # Backups finish before ready.
        return jsonify({"job_id": identifier}), 202  # The browser polls owned progress separately.

    @staticmethod
    def apply() -> tuple[Response, int]:
        """Consume an exact confirmed preview and enforce the complete backup gate."""
        body = PortalPolicyInputs.body()  # Do not accept arbitrary organization or site write bodies.
        if body.get("confirmation") != "CONFIGURE":
            raise PolicyError("Type CONFIGURE to confirm this settings change.")
        token = body.get("token")  # The server plan, not posted policy content, defines the change.
        if not isinstance(token, str):
            raise PolicyError("Create a policy preview before confirmation.")
        identifier = PortalJobs.manager().apply(
            PortalJobs.owner(), token, JobWorkflows.apply, "policy"
        )  # Consume before dispatch.
        return jsonify({"job_id": identifier}), 202  # No settings write blocks the request thread.

    @staticmethod
    def job(identifier: str) -> Response | tuple[Response, int]:
        """Return sanitized persistent status only to the owning browser."""
        try:
            result = PortalJobs.manager().status(
                identifier, session.get("firmware_job_owner", "")
            )  # Never create ownership on polling.
        except PolicyError:
            return jsonify({"error": "The job is unavailable for this browser."}), 404  # Hide foreign existence.
        return jsonify(result)  # Private context and owner secrets cannot enter the response.


firmware_policy_bp.add_url_rule("/operations/firmware-policy", view_func=FirmwarePolicyRoutes.page, endpoint="page")
firmware_policy_bp.add_url_rule(
    "/api/firmware-policy/jobs/<identifier>", view_func=FirmwarePolicyRoutes.job, endpoint="job"
)
firmware_policy_bp.add_url_rule(
    "/api/firmware-policy/organizations", view_func=FirmwarePolicyRoutes.organizations, endpoint="organizations"
)
firmware_policy_bp.add_url_rule(
    "/api/firmware-policy/catalog", view_func=FirmwarePolicyRoutes.catalog, endpoint="catalog", methods=["POST"]
)
firmware_policy_bp.add_url_rule(
    "/api/firmware-policy/preview", view_func=FirmwarePolicyRoutes.preview, endpoint="preview", methods=["POST"]
)
firmware_policy_bp.add_url_rule(
    "/api/firmware-policy/apply", view_func=FirmwarePolicyRoutes.apply, endpoint="apply", methods=["POST"]
)


@firmware_policy_bp.errorhandler(PolicyError)
def policy_error(error: PolicyError) -> tuple[Response, int]:
    """Report a checked policy failure without returning full settings or secrets."""
    logger.error(
        "Portal firmware policy request stopped with %s", type(error).__name__
    )  # Do not log private exception content.
    return jsonify({"error": JobErrors.message(error)}), 400  # Preserve safe checked operator diagnostics.


@firmware_policy_bp.errorhandler(Exception)
def unexpected_error(error: Exception) -> tuple[Response, int] | HTTPException:
    """Hide unexpected SDK or storage messages while preserving HTTP access failures."""
    if isinstance(error, HTTPException):
        return error  # Preserve the existing security middleware status code.
    logger.error("Portal firmware request stopped with %s", type(error).__name__)  # Never print exception values.
    return jsonify({"error": "The operation is unavailable. Check the private operator log."}), 500
