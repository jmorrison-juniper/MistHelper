"""Serve protected complete settings restoration without exposing private backup contents."""

from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from flask import Blueprint, Response, current_app, jsonify, render_template, request, session

from src.operations.execution.firmware_policy.recovery.backup import PolicyBackup
from src.operations.execution.firmware_policy.recovery.bundle import BundleFiles, RestoreSelection
from src.operations.execution.firmware_policy.recovery.workflow import RestorePlan, RestoreWorkflow
from src.operations.execution.firmware_policy.sdk import PolicyApi, PolicyError

restore_bp = Blueprint("restore", __name__, template_folder="templates")


@dataclass
class RestorePreviews:
    """Keep bounded private plans on the server for one authenticated browser."""

    entries: dict[str, tuple[str, float, RestorePlan]] = field(default_factory=dict)
    lock: Any = field(default_factory=threading.RLock)

    def create(self, owner: str, plan: RestorePlan) -> str:
        """Expire old plans and return only a random reference to the new plan."""
        with self.lock:
            now = time.monotonic()
            self.entries = {key: value for key, value in self.entries.items() if now - value[1] < 600}
            if len(self.entries) >= 50:
                raise PolicyError("The restoration preview limit was reached. Wait for a preview to expire.")
            token = str(uuid4())
            self.entries[token] = (owner, now, plan)
            return token

    def consume(self, owner: str, token: Any) -> RestorePlan:
        """Refuse expiration, repetition, malformed tokens, and another browser."""
        with self.lock:
            entry = self.entries.get(token) if isinstance(token, str) else None
            if entry is None or entry[0] != owner or time.monotonic() - entry[1] >= 600:
                raise PolicyError("The restoration preview expired. Create a new preview.")
            del self.entries[token]
            return entry[2]


class RestoreInputs:
    """Obtain existing portal context and reject posted settings or file paths."""

    lock = threading.RLock()

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
    def store() -> RestorePreviews:
        """Initialize one synchronized private store for this Flask application."""
        with RestoreInputs.lock:
            store = current_app.extensions.setdefault("settings_restore_previews", RestorePreviews())
            if not isinstance(store, RestorePreviews):
                raise PolicyError("The restoration preview store is unavailable.")
            return store

    @staticmethod
    def owner() -> str:
        """Bind references to the current browser without storing settings in cookies."""
        return session.setdefault("restore_owner", str(uuid4()))


class RestoreRoutes:
    """Expose sanitized selections and apply only a confirmed server-side plan."""

    @staticmethod
    def page() -> str:
        """Render the dedicated destructive workflow under existing portal protection."""
        return render_template("firmware_restore.html")

    @staticmethod
    def bundles() -> Response:
        """List verified private record identifiers without returning any settings."""
        workflow = RestoreInputs.workflow()
        return jsonify({"cloud": RestoreSelection.cloud(workflow.api), "bundles": workflow.files.list()})

    @staticmethod
    def preview() -> Response:
        """Validate selected scopes and current ownership before storing private snapshots."""
        body = RestoreInputs.body({"bundle", "records", "cloud"})
        workflow = RestoreInputs.workflow()
        plan = workflow.prepare(body["bundle"], body["records"], body["cloud"])
        token = RestoreInputs.store().create(RestoreInputs.owner(), plan)
        return jsonify({"token": token, **plan.preview()})

    @staticmethod
    def apply() -> Response:
        """Consume an exact confirmed preview and execute the shared recovery gates."""
        body = RestoreInputs.body({"token", "confirmation"})
        if body["confirmation"] != "RESTORE":
            raise PolicyError("Type RESTORE exactly to confirm this restoration.")
        plan = RestoreInputs.store().consume(RestoreInputs.owner(), body["token"])
        result = RestoreInputs.workflow().apply(plan, body["confirmation"])
        return jsonify({"status": "partial" if result.failed else "complete", "result": asdict(result)})

    @staticmethod
    def cancel() -> Response:
        """Invalidate the private preview without any cloud mutation."""
        body = RestoreInputs.body({"token"})
        RestoreInputs.store().consume(RestoreInputs.owner(), body["token"])
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
