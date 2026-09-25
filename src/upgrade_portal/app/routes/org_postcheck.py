"""The post-check seam of the multi-site phase watch (issue #3244).

Why:
    The phase watch runs in a thread that holds no request. A post-check
    capture needs the cloud session, the operator, the organization name, the
    capture runner, and an application context. This module binds all of them
    inside the request that starts the watch. The watch thread then takes each
    capture through the same path as a capture that the operator starts.

Warning:
    The bridge holds the cloud session, and each capture job holds it too. Do
    not log the bridge, a job, or the owner as a whole. A log of any of them can
    leak the API token of the operator.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from flask import current_app

from ...capture.assembly import standalone_capture_key
from ...runtime import identity
from ...upgrade.driver import POST_CHECK_ORDINAL, POST_CHECK_ROLE
from ...upgrade.org_postcheck import PostCheckResult, PostCheckSite
from ..config import read_post_check_mode
from . import capture as capture_routes
from . import select as select_routes

logger = logging.getLogger(__name__)  # One logger for the post-check seam.


@dataclass(frozen=True, slots=True)
class PostCheckSeams:
    """Hold the three seams that the watch thread cannot read for itself.

    Attributes:
        app_context: The bound method that builds one fresh application context.
        runner: The capture runner that the capture route uses.
        mode: The post-check mode of this portal, ``automatic`` or ``manual``.
    """

    app_context: Callable[[], Any]  # A new context for each capture, so no capture leaks state.
    runner: Callable[[dict[str, Any]], Any]  # The injected runner of a test, or the real collection work.
    mode: str  # The stage holds each site when the mode is manual.


@dataclass(frozen=True, slots=True)
class PostCheckOwner:
    """Hold the job fields that name the organization and the operator.

    Attributes:
        org_id: The organization of the operation.
        org_name: The readable name of the organization.
        actor_email: The address of the operator who started the operation.
        cloud_session: The signed cloud session. The dataclass never prints it.
    """

    org_id: str  # The organization that holds every site.
    org_name: str  # The name that the stored capture shows.
    actor_email: str  # The audit field of the stored capture.
    cloud_session: Any = field(repr=False)  # FR-017: a printed owner never shows the session.


class OrgPostCheckBridge:
    """Take each post-check capture of one operation through the capture route."""

    def __init__(self, seams: PostCheckSeams, owner: PostCheckOwner) -> None:
        """Keep the seams and the owner fields of one operation.

        Args:
            seams: The application context, the runner, and the mode.
            owner: The organization, the operator, and the cloud session.
        """
        self._seams = seams  # Bound inside the request.
        self._owner = owner  # Bound inside the request.

    def __repr__(self) -> str:
        """Return a text that names no secret, so a stray log line leaks nothing."""
        return f"OrgPostCheckBridge(org_id={self._owner.org_id!r}, mode={self._seams.mode!r})"  # FR-017.

    @classmethod
    def bind(cls, operation: Mapping[str, Any], cloud_session: Any) -> OrgPostCheckBridge:
        """Bind every seam inside the request that starts the watch.

        Args:
            operation: The durable operation record.
            cloud_session: The signed cloud session of the operator.

        Returns:
            The bridge that the watch thread calls for each site.
        """
        org_id = str(operation.get("org_id") or "")  # The organization of the operation.
        logger.info("org postcheck: bind the post-check seam of the organization %s", org_id)  # Before the reads.
        seams = PostCheckSeams(current_app.app_context, capture_routes.capture_runner(), read_post_check_mode())
        name = select_routes.org_display_name(org_id)  # The stored session names the organization.
        owner = PostCheckOwner(org_id, name, cls._actor(operation), cloud_session)  # The job fields.
        logger.debug("org postcheck: the seam is bound with the mode %s", seams.mode)  # After the reads.
        return cls(seams, owner)  # The walk keeps this bridge.

    @property
    def mode(self) -> str:
        """Return the post-check mode of this portal."""
        return self._seams.mode  # Read inside the request by ``bind``.

    def new_capture_id(self) -> str:
        """Return the key of one new post-check capture (FR-003)."""
        return standalone_capture_key(POST_CHECK_ORDINAL)  # A fresh nonce with the ordinal 2.

    def take(self, site: PostCheckSite, capture_id: str) -> PostCheckResult:
        """Take one capture of one site, and return its end.

        Args:
            site: The site to read.
            capture_id: The key of the new capture.

        Returns:
            The end of the capture. Only a capture that the portal read back reads as verified.
        """
        logger.info(  # Before the capture. The line names no session and no job.
            "org postcheck: take the capture %s of the site %s at tier %s", capture_id, site.site_id, site.tier
        )
        job = self._job(site, capture_id)  # FR-017: this value holds the cloud session, so no log shows it.
        capture_routes.open_progress(capture_id, capture_routes.opening_record(job))  # The capture page can read it.
        self._run(job, capture_id)  # The whole read of one site runs here.
        result = self._result(capture_id)  # The last progress record decides the verdict.
        logger.debug("org postcheck: the capture %s ended, verified %s", capture_id, result.verified)  # After.
        return result  # The stage stores the row.

    def _job(self, site: PostCheckSite, capture_id: str) -> dict[str, Any]:
        """Return the eleven fields of one capture job, as ``capture.build_job`` builds them."""
        return {  # The runner reads these eleven fields and nothing else.
            "capture_id": capture_id,
            "run_id": "",  # FR-003: a capture with no run, so the store writes no edge.
            "ordinal": POST_CHECK_ORDINAL,
            "role": POST_CHECK_ROLE,
            "org_id": self._owner.org_id,
            "site_id": site.site_id,
            "tier": site.tier,  # FR-004: the tier of the pre-check capture.
            "cloud_session": self._owner.cloud_session,
            "actor_email": self._owner.actor_email,
            "org_name": self._owner.org_name,
            "site_name": site.site_name,
        }

    def _run(self, job: dict[str, Any], capture_id: str) -> None:
        """Run the capture runner inside a fresh application context, and keep each fault inside."""
        try:  # A fault in one capture must not stop the stage.
            capture_routes.worker_body(self._seams.app_context(), self._seams.runner, job)  # The operator path.
        except Exception as error:  # Keep broad: FR-011 says that the stage continues with the next site.
            logger.warning("org postcheck: the capture %s stopped with %s", capture_id, type(error).__name__)
            capture_routes.record_status(  # The capture page shows the short failure text.
                capture_id, state=capture_routes.STATE_FAILED, message=capture_routes.FAILED_MESSAGE
            )

    def _result(self, capture_id: str) -> PostCheckResult:
        """Return the end of one capture from its progress record, or from the store.

        Why:
            A live progress record ends with the state and the read-back flag.
            A stored capture sends the same two words, `verified` or `failed`,
            from the same read-back result (issue #3378). Only the read-back
            flag proves the capture, so the verdict reads that flag first in
            both shapes.
        """
        body = capture_routes.read_progress(capture_id)  # The progress store holds the last state.
        if body is None:  # The progress store dropped the record.
            with self._seams.app_context():  # The stored reader reads the application configuration.
                body = capture_routes.stored_body(capture_id)  # The stored capture holds the state.
        found = body or {}  # No record at all reads as a capture that did not verify.
        state = str(found.get("state") or "")  # The last state of the capture.
        verified = found.get("verified") is True and state != capture_routes.STATE_FAILED  # The read-back proof.
        return PostCheckResult(capture_id, verified, str(found.get("message") or ""))  # The stage stores the row.

    @staticmethod
    def _actor(operation: Mapping[str, Any]) -> str:
        """Return the address of the operator who started the operation."""
        stored = str(operation.get("actor_email") or "")  # Issue #3249 stores the typed address.
        if stored:  # The operation names its operator.
            return stored  # The capture names the same operator.
        owner = identity.current_owner()  # An earlier record holds no address.
        return owner.actor_email if owner is not None else ""  # An empty address is the honest fallback.
