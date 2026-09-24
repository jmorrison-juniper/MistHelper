"""Start one pre-check capture of one site of a multi-site operation.

Why:
    Issue #3243. The multi-site confirm page stays locked until each selected
    site holds a verified pre-check capture. The operator takes each missing
    capture from the same page. This endpoint starts one capture of one site
    with no run, as the capture page does, and answers the shape of the
    capture route. A capture reads the site. It sends no firmware request.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each refusal and each lock step without a secret.

from flask import Blueprint, Response  # The route module and its answer type.

from ...runtime import identity, lock  # The session guard and the site lock rules.
from ..factory import json_error  # The one error envelope of the portal.
from . import (
    capture,  # The capture start, the tier rule, and the capture codes.
    org_upgrade,  # The signed multi-site scope and the saved options.
)
from . import select as select_routes  # The lock store client of the portal or of a test.
from .select import BAD_REQUEST_STATUS, NOT_FOUND_STATUS  # The status values of the refusals.

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

org_precheck_bp = Blueprint("org_precheck", __name__)  # The factory finds the blueprint by this name.

PRECHECK_START_PATH = "/api/org-upgrades/prechecks/<site_id>"  # FR-009: one capture of one site.
PRE_ROLE = "pre"  # The role of a capture before an upgrade.
OPTIONS_MESSAGE = "Save valid upgrade options before you take a pre-check capture."  # The cure of the refusal.


class PrecheckSiteLock:
    """Apply the site lock rules of one pre-check capture of a multi-site operation.

    Why:
        FR-011. The capture page takes the site lock with no run, and so does
        this endpoint. The endpoint keeps no copy of the lock in the browser
        session, because a copy for each site would make the session cookie
        larger than a browser keeps.
    """

    @classmethod
    def claim(cls, org_id: str, site_id: str, operation_id: str) -> tuple[Response, int] | None:
        """Take the site lock with no run, keep a lock of this operator, or refuse.

        Args:
            org_id: The selected organization.
            site_id: The site of the capture.
            operation_id: The operation of the saved options.

        Returns:
            None when the capture can start, or the refusal.
        """
        owner = identity.current_owner()  # The session guard already refused an unsigned request.
        if owner is None:  # No owner can hold a lock.
            logger.warning("org precheck: no signed owner, so site %s starts without a lock", site_id)
            return None  # The capture contract permits a capture without a lock.
        client = select_routes.lock_client()  # The lock store of the portal or of a test.
        held = lock.read_lock(org_id, site_id, client)  # None for a free site, and None when the store is down.
        if held is None:  # No operator holds the site.
            return cls._take(lock.LockRequest(org_id, site_id, owner, ""), client)  # A lock with no run.
        if not held.held_by(owner):  # Another operator or another browser holds the site.
            logger.info("org precheck: another operator holds site %s", site_id)  # Name the refusal.
            return json_error(org_upgrade.CONFLICT_STATUS, capture.SITE_LOCKED_CODE, capture.SITE_LOCKED_MESSAGE)
        if held.run_id in ("", operation_id):  # A lock of a pre-check capture, or of this operation.
            logger.debug("org precheck: site %s keeps the lock of this operator", site_id)  # No renewal.
            return None  # The capture page does not renew a lock with no run.
        logger.info("org precheck: the lock of site %s names another run", site_id)  # Name the refusal.
        return json_error(
            org_upgrade.CONFLICT_STATUS, org_upgrade.SITE_LOCK_WRONG_RUN, org_upgrade.SITE_LOCK_WRONG_RUN_MESSAGE
        )

    @staticmethod
    def _take(request_record: lock.LockRequest, client: object) -> tuple[Response, int] | None:
        """Take the lock of one free site, and start without a lock when the store does not answer."""
        site_id = request_record.site_id  # The site that each record below names.
        logger.info("org precheck: take site %s for a pre-check capture", site_id)  # Before the write.
        try:  # The lock store sits on a network and may not answer.
            lock.acquire_site_lock(request_record, client)  # The atomic take of the capture page.
        except lock.LockStoreUnreachableError:  # The capture contract permits a capture without a lock.
            logger.warning(  # The start of the upgrade takes the lock later.
                "org precheck: the lock store did not answer, so site %s starts without a lock", site_id
            )
            return None  # The capture starts without a lock.
        except lock.SiteLockError as fault:  # Another operator took the site after the read.
            logger.info("org precheck: the lock of site %s reported %s", site_id, fault.code)  # The code only.
            return json_error(org_upgrade.CONFLICT_STATUS, capture.SITE_LOCKED_CODE, capture.SITE_LOCKED_MESSAGE)
        logger.debug("org precheck: this operator holds site %s with no run", site_id)  # After the write.
        return None  # The capture can start.


@org_precheck_bp.post(PRECHECK_START_PATH)
@identity.require_session
def start_org_precheck(site_id: str) -> tuple[Response, int]:
    """Start one pre-check capture of one site of the saved multi-site plan.

    Why:
        FR-010 names the refusal order: the saved options, the site, the tier,
        and the site lock. Each refusal answers before the worker starts.

    Args:
        site_id: The site the path named.

    Returns:
        The capture identifier and its status path, or the refusal envelope.
    """
    scope = org_upgrade.active_context()  # The signed organization and the selected sites.
    options = org_upgrade.stored_options()  # The saved options of the selected organization.
    if scope is None or not options:  # No saved plan names the selection.
        return json_error(BAD_REQUEST_STATUS, org_upgrade.OPTIONS_INVALID, OPTIONS_MESSAGE)
    org_id, site_ids = scope  # The validated scope.
    site = capture.permitted_site(site_id, org_id) if site_id in site_ids else None  # A selected site only.
    if site is None:  # A hand-typed path, or a site of another organization.
        return json_error(NOT_FOUND_STATUS, capture.SITE_NOT_FOUND_CODE, capture.SITE_NOT_FOUND_MESSAGE)
    tier = capture.read_tier(capture.request_body())  # None for a tier other than 2 and 3.
    if tier is None:  # The capture reads tier 2 or tier 3 only.
        return json_error(BAD_REQUEST_STATUS, capture.BAD_TIER_CODE, capture.BAD_TIER_MESSAGE)
    refusal = PrecheckSiteLock.claim(org_id, site_id, str(options.get("operation_id", "")))  # FR-011.
    if refusal is not None:  # Another operator or another run holds the site.
        return refusal  # No capture starts.
    logger.info("org precheck: start a tier %s pre-check capture of site %s", tier, site_id)  # Before the start.
    return capture.launch_capture(site, org_id, tier, {"role": PRE_ROLE})  # 202, and the worker reads the site.
