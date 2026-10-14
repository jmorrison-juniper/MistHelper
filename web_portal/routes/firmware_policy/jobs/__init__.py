"""Share one bounded job executor per existing Flask portal application."""

from __future__ import annotations

import threading
from pathlib import Path
from uuid import uuid4

from flask import current_app, session

from src.operations.execution.firmware_policy.sdk import PolicyError

from .manager import JobManager


class PortalJobs:
    """Capture browser ownership and initialize status without app.py changes."""

    lock = threading.RLock()  # Concurrent first requests must create one manager only.

    @staticmethod
    def manager() -> JobManager:
        """Reuse one process-lifetime executor for the long-lived gthread worker."""
        with PortalJobs.lock:
            manager = current_app.extensions.get("firmware_policy_jobs")  # Avoid eager default construction.
            if manager is None:
                manager = JobManager(Path(current_app.config["DATA_DIR"]))  # Recover explicit interrupted outcomes.
                current_app.extensions["firmware_policy_jobs"] = manager  # Requests share the bounded executor.
            return manager  # Worker tasks keep strong references until completion.

    @staticmethod
    def owner() -> str:
        """Use one unpredictable signed-cookie owner for both destructive workflows."""
        owner = session.setdefault("firmware_job_owner", str(uuid4()))  # No private plan enters the cookie.
        if not isinstance(owner, str) or not owner:
            raise PolicyError("The browser session owner is not valid.")
        return owner  # Only a valid random signed-cookie owner can create or confirm work.
