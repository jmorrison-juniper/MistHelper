"""Seed the two stale runs of the bulk tests on a site of their own.

Why:
    The bulk cancel test ends a stale run that never reached the cloud. The
    reconcile test settles a stale run in the state `stopping` from read-only
    evidence. No safe browser journey reaches either state with an old update
    time, so the browser server writes both records at the start.

    Issue #3507. Both runs sat on the first site of the picker. The create
    route refuses a new run on a site that holds a live run, so each create
    call of `test_existing.py` met a seed run in place of its own run. The
    module passed only when `test_bulk.py` ran first and ended both runs. The
    stale site holds these two runs only, and the stand-in cloud does not list
    it, so no create journey meets them.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each seed write without a device address or a secret.
from typing import Any  # The stored records hold JSON values of mixed types.

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

STALE_SITE_ID = "35073507-3507-3507-3507-350735073507"  # Issue #3507: a site that the picker does not list.
STALE_SITE_NAME = "E2E Stale Runs Site"  # The name that the history page shows for the stale site.
STALE_PRE_CLOUD_RUN_ID = "e2e-stale-precloud-0001"  # The run that the bulk cancel test ends.
STALE_STOPPING_RUN_ID = "e2e-stale-stopping-0001"  # The run that the reconcile test settles.
STALE_UPDATE_TIME = "2026-09-01T10:00:00+00:00"  # An old update time, so both runs read as stale.


class StaleRunSeeds:
    """Build and write the two stale runs of the bulk tests."""

    @staticmethod
    def pre_cloud_record(org_id: str) -> dict[str, Any]:
        """Build the stale run that never reached the cloud.

        Args:
            org_id: The organization of the browser server.

        Returns:
            The run record in the state `awaiting_confirmation`.
        """
        return {
            "run_id": STALE_PRE_CLOUD_RUN_ID,  # The key that the bulk cancel test selects.
            "site_id": STALE_SITE_ID,  # Issue #3507: no create journey reads this site.
            "site_name": STALE_SITE_NAME,  # The history page shows a name in place of the identifier.
            "org_id": org_id,  # The lock key needs both halves, so the record carries the organization.
            "state": "awaiting_confirmation",  # A state before the cloud, so a cancel ends the run.
            "updated_at": STALE_UPDATE_TIME,  # The old time makes the run stale.
            "targets": [],  # The cancel reads no target.
            "options": {},  # The cancel reads no option.
        }

    @classmethod
    def stopping_record(cls, org_id: str) -> dict[str, Any]:
        """Build the stale run that waits in the state `stopping`.

        Args:
            org_id: The organization of the browser server.

        Returns:
            The run record in the state `stopping`, with the target of the scripted evidence.
        """
        record = cls.pre_cloud_record(org_id)  # The same site, organization, and update time.
        record["run_id"] = STALE_STOPPING_RUN_ID  # The key that the reconcile test opens.
        record["state"] = "stopping"  # The one state that offers the reconcile control.
        record["targets"] = [{"device_id": "e2e-target-one", "cloud_task_id": "e2e-task-one"}]  # The scripted task.
        return record  # The caller writes the record to the store.

    @classmethod
    def records(cls, org_id: str) -> list[dict[str, Any]]:
        """Build both stale runs, in write order.

        Args:
            org_id: The organization of the browser server.

        Returns:
            The pre-cloud record, then the stopping record.
        """
        return [cls.pre_cloud_record(org_id), cls.stopping_record(org_id)]  # The order of the write.

    @classmethod
    def write(cls, upgrade: Any, org_id: str) -> bool:
        """Write both stale runs through the run store of the browser server.

        Args:
            upgrade: The upgrade route module, which owns `save_run`.
            org_id: The organization of the browser server.

        Returns:
            True when the store accepted both runs.
        """
        logger.info("Seed the two stale runs on the stale site %s", STALE_SITE_ID)  # Log before the writes.
        results = [bool(upgrade.save_run(record)) for record in cls.records(org_id)]  # A refusal stops no write.
        written = all(results)  # A missing seed fails its bulk test, so the caller logs one result.
        logger.debug("The stale run seeds report written=%s", written)  # Log after the writes.
        return written  # The caller logs the result.
