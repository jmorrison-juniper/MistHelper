"""Serve protected firmware policy restoration without exposing private backup contents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Blueprint, Response, current_app, jsonify, make_response, redirect, request, session

from src.operations.execution.firmware_policy.recovery.backup import BackupAccess, PolicyBackup
from src.operations.execution.firmware_policy.recovery.bundle import BundleFiles, RestoreSelection
from src.operations.execution.firmware_policy.recovery.workflow import RestoreWorkflow
from src.operations.execution.firmware_policy.sdk import PolicyApi, PolicyError, PolicyResponse

from ..jobs import PortalJobs
from ..jobs.workflows import JobWorkflows
from .inspection import HistoricalInspection

restore_bp = Blueprint("restore", __name__, template_folder="templates")


class RestoreInputs:
    """Obtain existing portal context and reject posted settings or file paths."""

    @staticmethod
    def workflow() -> RestoreWorkflow:
        """Use only the portal's existing authenticated SDK and private data directory."""
        api_session = current_app.config.get("APISESSION")
        if api_session is None:
            raise PolicyError("The portal has no Mist API session.")
        return RestoreWorkflow(PolicyApi(api_session), BundleFiles(PolicyBackup(Path(current_app.config["DATA_DIR"]))))

    @staticmethod
    def body(allowed: set[str]) -> dict[str, Any]:
        """Reject malformed JSON and any settings or path supplied by the browser."""
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or set(body) != allowed:
            raise PolicyError("Send exactly the required restoration request fields.")
        return body

    @staticmethod
    def jobs() -> JobWorkflows:
        """Capture the existing transport before submitting asynchronous recovery."""
        workflow = RestoreInputs.workflow()  # Refuse a missing authenticated API session.
        return JobWorkflows(workflow.api.session, Path(current_app.config["DATA_DIR"]))  # Preserve private root.


class RestoreLabels:
    """Resolve compact backup labels with one complete site listing for each organization."""

    def __init__(self, workflow: RestoreWorkflow) -> None:
        """Share checked identity and membership metadata across every listed backup."""
        self.workflow = workflow  # Reuse the authenticated SDK and private bundle reader.
        self.organizations: dict[str, str] = {}  # Read each organization identity once per request.
        self.sites: dict[str, dict[str, str]] = {}  # Index the existing complete site list by identifier.

    def organization(self, identifier: str) -> str:
        """Resolve checked current names without inventing an identifier-based name."""
        if identifier not in self.organizations:
            self.organizations[identifier] = self.workflow.api.organization(identifier)[
                "name"
            ]  # Failure stops listing.
            listing = self.workflow.api.sites(identifier)  # No individual getSite request is necessary.
            RestoreSelection.membership(
                self.workflow.api, {identifier}, {identifier: listing}
            )  # Check scope ownership.
            self.sites[identifier] = {
                PolicyResponse.identifier(site["id"]): site["name"]
                for site in listing
                if self.safe_name(site.get("name"))
            }  # Missing current labels remain explicitly unavailable.
        return self.organizations[identifier]  # All bundles share one checked identity result.

    @staticmethod
    def safe_name(value: Any) -> bool:
        """Accept only bounded printable labels from current or saved identity metadata."""
        return (
            isinstance(value, str)
            and bool(value.strip())
            and len(value) <= 256
            and all(character.isprintable() for character in value)
        )  # Reject control characters without exposing any unrelated settings.

    def summary(self, token: str) -> dict[str, Any]:
        """Read one verified bundle and retain only named, compact record metadata."""
        bundle = self.workflow.files.read(token)  # Complete private validation precedes metadata use.
        summary = bundle.summary()  # Keep historical settings out of the response.
        for public, saved in zip(summary["records"], bundle.records, strict=True):
            identifier = RestoreSelection.ownership(bundle, saved)  # Legacy ownership must be unambiguous.
            organization = self.organization(identifier)  # One cached getOrg and site list per organization.
            label = organization if saved["scope"] == "org" else self.sites[identifier].get(saved["id"])
            if label is None:
                historical = saved["settings"].get("name")  # A saved label is optional, not an invented name.
                label = historical if self.safe_name(historical) else "Site name unavailable"
            public.update(name=label, organization=organization, organization_id=identifier)
        return summary  # Only source scope, identifier, and checked display labels leave this method.

    def bundles(self) -> list[dict[str, Any]]:
        """Label each root-level bundle without treating private job status as a backup."""
        root = self.workflow.files.backup.root  # This directory already carries private download protection.
        if not root.exists():
            return []  # No private backup exists, so there are no records to label.
        BackupAccess.verify(root, directory=True)  # Reject unsafe storage before enumeration.
        paths = sorted(path for path in root.iterdir() if path.suffix == ".json")  # Ignore the protected job directory.
        return [self.summary(path.stem) for path in paths]  # Every selected file still passes full bundle validation.


class RestoreRoutes:
    """Expose sanitized selections and apply only a confirmed server-side plan."""

    @staticmethod
    def page() -> Response:
        """Select menu 306 in the existing protected operations workspace."""
        return make_response(redirect("/operations?menu=306"))  # Legacy links keep the menu list visible.

    @staticmethod
    def bundles() -> Response:
        """List verified private record identifiers without returning any settings."""
        workflow = RestoreInputs.workflow()
        return jsonify(
            {"cloud": RestoreSelection.cloud(workflow.api), "bundles": RestoreLabels(workflow).bundles()}
        )  # Current labels reuse checked identity and complete membership reads.

    @staticmethod
    def preview() -> tuple[Response, int]:
        """Validate selected scopes and current ownership before storing private snapshots."""
        body = RestoreInputs.body({"bundle", "records", "cloud"})
        work = RestoreInputs.jobs().restore(body)  # Domain parsing and complete recovery occur off the request thread.
        identifier = PortalJobs.manager().start(
            PortalJobs.owner(), "restore", work
        )  # Readiness requires verified backups.
        return jsonify({"job_id": identifier}), 202  # Share the same owner-bound status endpoint.

    @staticmethod
    def apply() -> tuple[Response, int]:
        """Consume an exact confirmed preview and execute the shared recovery gates."""
        body = RestoreInputs.body({"token", "confirmation"})
        if body["confirmation"] != "RESTORE":
            raise PolicyError("Type RESTORE exactly to confirm this restoration.")
        if not isinstance(body["token"], str):
            raise PolicyError("Create a restoration preparation before confirmation.")
        identifier = PortalJobs.manager().apply(
            PortalJobs.owner(), body["token"], JobWorkflows.apply, "restore"
        )  # Consume once.
        return jsonify({"job_id": identifier}), 202  # Preserve the preparation identifier during application.

    @staticmethod
    def cancel() -> Response:
        """Invalidate the private preview without any cloud mutation."""
        body = RestoreInputs.body({"token"})
        if not isinstance(body["token"], str):
            raise PolicyError("Select a ready restoration token.")
        PortalJobs.manager().cancel(PortalJobs.owner(), body["token"])  # Invalidate without a settings request.
        return jsonify({"status": "cancelled", "writes": 0})


restore_bp.add_url_rule("/operations/settings-restore", endpoint="page", view_func=RestoreRoutes.page)
restore_bp.add_url_rule("/api/settings-restore/bundles", endpoint="bundles", view_func=RestoreRoutes.bundles)
restore_bp.add_url_rule(
    "/api/settings-restore/preview", endpoint="preview", view_func=RestoreRoutes.preview, methods=["POST"]
)
restore_bp.add_url_rule(
    "/api/settings-restore/apply", endpoint="apply", view_func=RestoreRoutes.apply, methods=["POST"]
)
restore_bp.add_url_rule(
    "/api/settings-restore/cancel", endpoint="cancel", view_func=RestoreRoutes.cancel, methods=["POST"]
)


class InspectionRoutes:
    """Expose protected one-scope inspection without entering preparation or application."""

    @staticmethod
    def historical() -> Response:
        """Require an explicit saved record and optional current comparison."""
        body = RestoreInputs.body({"bundle", "record", "compare"})
        result = HistoricalInspection(RestoreInputs.workflow()).read(body["bundle"], body["record"], body["compare"])
        return jsonify(result)

    @staticmethod
    def prepared(identifier: str) -> Response | tuple[Response, int]:
        """Hide unknown and foreign jobs before resolving private prepared policy values."""
        body = RestoreInputs.body({"scope", "id"})
        if body["scope"] not in ("org", "site"):
            raise PolicyError("Select an organization or site scope.")
        body["id"] = PolicyResponse.identifier(body["id"])
        owner = session.get("firmware_job_owner", "")
        try:
            PortalJobs.manager().status(identifier, owner)
        except PolicyError:
            return jsonify({"error": "The job is unavailable for this browser."}), 404
        return jsonify(PortalJobs.manager().comparison(identifier, owner, body))


restore_bp.add_url_rule(
    "/api/settings-restore/inspect", endpoint="inspect", view_func=InspectionRoutes.historical, methods=["POST"]
)
restore_bp.add_url_rule(
    "/api/firmware-policy/jobs/<identifier>/comparison",
    endpoint="comparison",
    view_func=InspectionRoutes.prepared,
    methods=["POST"],
)
