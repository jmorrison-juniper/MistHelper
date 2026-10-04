"""Build the terminal runs used by the single-run retry browser tests.

Why:
    The retry tests need a lock on the site of their seeded run. A seeded
    stopping run on the shared first site can refuse that local setup. A
    dedicated site keeps the retry setup independent from other journeys.
"""

from __future__ import annotations

from typing import Any

FAILED_RUN_ID = "e2e-failed-run-0001"
STOPPED_RUN_ID = "e2e-stopped-run-0001"
RETRY_SITE_ID = "77777777-7777-7777-7777-777732923292"


class RetryRunSeeds:
    """Build the failed and stopped runs used by the retry tests."""

    @staticmethod
    def failed_record(org_id: str) -> dict[str, Any]:
        """Build the failed run that shows the retry control."""
        return {
            "run_id": FAILED_RUN_ID,
            "site_id": RETRY_SITE_ID,
            "org_id": org_id,
            "state": "failed",
            "message": "A stand-in failure, so the retry control appears for the browser test.",
            "targets": [],
            "options": {},
        }

    @classmethod
    def stopped_record(cls, org_id: str) -> dict[str, Any]:
        """Build the stopped run that shows the fresh-attempt control."""
        record = cls.failed_record(org_id)
        record["run_id"] = STOPPED_RUN_ID
        record["state"] = "stopped"
        record["message"] = "The stand-in run stopped after an operator cancellation."
        return record
