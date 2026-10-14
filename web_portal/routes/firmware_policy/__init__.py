"""Serve the protected graphical menu 305 workflow outside generic safe operations."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from flask import Blueprint, Response, current_app, jsonify, render_template, request, session
from mistapi.api.v1.msps import orgs

from src.operations.execution.firmware_policy.changes import POLICY_TYPES, FirmwarePolicy
from src.operations.execution.firmware_policy.cli import POLICY_WARNING, PolicyCatalog
from src.operations.execution.firmware_policy.recovery.backup import PolicyBackup
from src.operations.execution.firmware_policy.sdk import PolicyApi, PolicyError, PolicyResponse
from src.operations.execution.firmware_policy.workflow import OrganizationChange, PolicyWorkflow

from .restore import restore_bp

logger = logging.getLogger(__name__)
firmware_policy_bp = Blueprint("firmware_policy", __name__, template_folder="templates")
firmware_policy_bp.register_blueprint(restore_bp)


@dataclass
class PolicyPreviewStore:
    """Keep bounded, short-lived, session-bound previews out of browser cookies."""

    entries: dict[str, tuple[str, float, list[OrganizationChange]]] = field(default_factory=dict)
    lock: Any = field(default_factory=threading.RLock)

    def create(self, owner: str, plans: list[OrganizationChange]) -> str:
        """Store a complete private plan without returning any sensitive settings."""
        with self.lock:
            now = time.monotonic()  # Use elapsed time rather than the wall clock for expiration.
            self.entries = {key: value for key, value in self.entries.items() if now - value[1] < 600}
            if len(self.entries) >= 50:
                raise PolicyError("The policy preview limit was reached. Wait for an earlier preview to expire.")
            token = str(uuid4())  # Prevent another browser from guessing a preview identifier.
            self.entries[token] = (owner, now, plans)  # Keep full settings on the server only.
            return token  # The browser sees only this opaque reference.

    def consume(self, token: str, owner: str) -> list[OrganizationChange]:
        """Use a confirmed preview once and refuse expiration or a different browser."""
        with self.lock:
            entry = self.entries.get(token)  # Do not remove a preview belonging to another browser.
            if entry is None or entry[0] != owner or time.monotonic() - entry[1] >= 600:
                raise PolicyError("The policy preview expired. Create a new preview.")
            del self.entries[token]  # A duplicate apply cannot submit the same settings plan again.
            return entry[2]  # The workflow verifies current settings before applying it.


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
    def organizations(values: Any) -> list[dict[str, str]]:
        """Accept a bounded, explicit set of unique organization identifiers."""
        if not isinstance(values, list) or not values or len(values) > 100:
            raise PolicyError("Select between 1 and 100 organizations.")
        identifiers = [PolicyResponse.identifier(value) for value in values]  # Validate every posted scope.
        if len(set(identifiers)) != len(identifiers):
            raise PolicyError("Select each organization only once.")
        return [{"id": identifier, "name": identifier} for identifier in identifiers]

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
    def store() -> PolicyPreviewStore:
        """Create one store per Flask app, isolated from other portal instances."""
        with _STORE_LOCK:
            store = current_app.extensions.setdefault("firmware_policy_previews", PolicyPreviewStore())
            if not isinstance(store, PolicyPreviewStore):
                raise PolicyError("The policy preview store is unavailable.")
            return store

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
    def page() -> str:
        """Render the dedicated menu 305 page with existing portal access controls."""
        return render_template("firmware_policy.html", policy_warning=POLICY_WARNING)

    @staticmethod
    def organizations() -> Response:
        """List the current organization or every organization in a selected MSP."""
        api = PortalPolicyInputs.api()  # Use the authenticated session configured for this portal.
        msp_id = request.args.get("msp_id")  # A missing MSP means the existing current org.
        if msp_id:
            msp_id = PolicyResponse.identifier(msp_id)  # The Mist API enforces the account's MSP access.
            rows = PolicyResponse.collect(
                api.session, lambda: orgs.listMspOrgs(api.session, msp_id), "List MSP organizations", msp_id
            )
        else:
            identifier = PolicyResponse.identifier(current_app.config.get("ORG_ID", ""))
            rows = [{"id": identifier, "name": identifier}]  # Do not invent a name when no name was read.
        result = [
            {"id": PolicyResponse.identifier(row.get("id", "")), "name": row.get("name", row.get("id"))} for row in rows
        ]
        return jsonify({"organizations": result, "count": len(result)})  # No settings body reaches the selector.

    @staticmethod
    def catalog() -> Response:
        """Return dynamically available model/version pairs across the selected orgs."""
        body = PortalPolicyInputs.body()  # Catalog requests read only and create no backup.
        organizations = PortalPolicyInputs.organizations(body.get("organizations"))
        kinds = body.get("kinds")  # Require explicit selected types instead of querying unsupported types.
        if not isinstance(kinds, list) or not kinds or any(kind not in POLICY_TYPES for kind in kinds):
            raise PolicyError("Select supported device types.")
        catalogs = PolicyCatalog.common(PortalPolicyInputs.api(), organizations, kinds)
        return jsonify({"catalogs": catalogs})  # Return only non-secret model and version values.

    @staticmethod
    def preview() -> Response:
        """Validate choices and capture every complete target before browser confirmation."""
        body = PortalPolicyInputs.body()  # Posted policy fields never become a direct SDK body.
        organizations = PortalPolicyInputs.organizations(body.get("organizations"))
        policies = PortalPolicyInputs.policies(body.get("policies"))
        api = PortalPolicyInputs.api()  # Reuse the same authenticated SDK session.
        catalogs = PolicyCatalog.common(api, organizations, [policy.kind for policy in policies])
        PolicyCatalog.validate(policies, catalogs)  # Revalidate browser selections against current catalog data.
        workflow = PolicyWorkflow(api, PolicyBackup(Path(current_app.config["DATA_DIR"])))
        plans = [workflow.prepare(org, policies) for org in organizations]  # Read all sites before any mutation.
        token = PortalPolicyInputs.store().create(session.setdefault("policy_owner", str(uuid4())), plans)
        return jsonify(
            {  # The entire preview is sanitized by the shared plan presentation method.
                "token": token,
                "organizations": [plan.preview() for plan in plans],
                "warning": POLICY_WARNING,
                "settings_count": sum(1 + len(plan.sites) for plan in plans),
                "writes": 0,
                "backup": "Required and verified for every scope before the first change.",
            }
        )

    @staticmethod
    def apply() -> Response:
        """Consume an exact confirmed preview and enforce the complete backup gate."""
        body = PortalPolicyInputs.body()  # Do not accept arbitrary organization or site write bodies.
        if body.get("confirmation") != "CONFIGURE":
            raise PolicyError("Type CONFIGURE to confirm this settings change.")
        token = body.get("token")  # The server plan, not posted policy content, defines the change.
        if not isinstance(token, str):
            raise PolicyError("Create a policy preview before confirmation.")
        plans = PortalPolicyInputs.store().consume(token, session.get("policy_owner", ""))
        workflow = PolicyWorkflow(PortalPolicyInputs.api(), PolicyBackup(Path(current_app.config["DATA_DIR"])))
        result = workflow.apply(plans)  # Every full organization and site backup verifies before writes.
        return jsonify(
            {
                "status": "partial" if result.failures else "complete",
                "result": asdict(result),
                "backups_verified": sum(1 + len(plan.sites) for plan in plans),
            }
        )


_STORE_LOCK = threading.RLock()  # Prevent duplicate app-local preview stores during concurrent first requests.
firmware_policy_bp.add_url_rule("/operations/firmware-policy", view_func=FirmwarePolicyRoutes.page, endpoint="page")
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
    logger.error("Portal firmware policy request stopped: %s", error)  # Checked errors contain no response body.
    return jsonify({"error": str(error)}), 400  # Never send a success-shaped response for a failed backup.
