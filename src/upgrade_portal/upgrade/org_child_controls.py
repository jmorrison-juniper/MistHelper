"""Build the recovery controls and the schedule control of one multi-site operation.

Why:
    Issue #3247. The single-site portal shows a retry control, a
    reconciliation control, and a reschedule control. The multi-site portal
    showed none of the three. This module builds the values that the progress
    page and the confirmation page show. It makes no cloud call and no write.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each view build without a secret.
from collections.abc import Mapping  # Accept each stored record without a concrete type.
from typing import Any  # The stored record holds JSON values of mixed types.

from src.upgrade_portal.upgrade.org_reconcile import OrgReconcileCheck  # The uncertain child jobs.
from src.upgrade_portal.upgrade.org_retry import OrgRetryPlan  # The retry devices.

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

START_NOW_TEXT = "The upgrade starts at once after you confirm."  # The text for a plan with no start time.
PLANNED_STATE = "planned"  # The one state in which no child job reached the cloud.


class OrgScheduleView:
    """Build the start time line and the reschedule control of the confirmation page."""

    @classmethod
    def build(cls, record: Mapping[str, Any] | None, start_value: str) -> dict[str, Any]:
        """Return the schedule values of one planned operation.

        Args:
            record: The durable operation record, or None when the store holds no plan.
            start_value: The start time in the form of the date and time field, or empty text.

        Returns:
            The values that the confirmation page shows.
        """
        operation_id = str(record.get("operation_id") or "") if record is not None else ""  # The plan identity.
        return {  # The page shows the line always, and the form only when the plan can move.
            "available": cls.available(record),
            "operation_id": operation_id,
            "start_value": start_value,
            "start_text": cls.start_text(start_value),
        }

    @staticmethod
    def available(record: Mapping[str, Any] | None) -> bool:
        """Report whether the start time of one operation can move.

        Args:
            record: The durable operation record, or None.

        Returns:
            True when no child job reached the cloud and no submission runs.
        """
        if record is None or record.get("state") != PLANNED_STATE or record.get("submission_claim_id"):
            return False  # A submitted plan keeps its schedule.
        children = record.get("children")  # Every child must still wait for the confirmation.
        rows = children if isinstance(children, list) else []  # A damaged record holds no child.
        return bool(rows) and all(isinstance(row, Mapping) and row.get("status") == PLANNED_STATE for row in rows)

    @staticmethod
    def start_text(start_value: str) -> str:
        """Return the sentence that names the start time of one plan."""
        if not start_value:  # The plan holds no start time.
            return START_NOW_TEXT  # The cloud starts the upgrade when the operator confirms.
        return f"The upgrade starts at {start_value.replace('T', ' ')} UTC."  # The field keeps the UTC value.


class OrgControlsView:
    """Build the recovery controls of the multi-site progress page."""

    @classmethod
    def build(cls, record: Mapping[str, Any], retry_plan: OrgRetryPlan | None) -> dict[str, Any]:
        """Return the retry control, the reconciliation control, and their signature.

        Args:
            record: The durable operation record.
            retry_plan: The retry plan of the operation, or None.

        Returns:
            The values that the progress page and its poll show.
        """
        logger.info("Build the recovery controls of aggregate upgrade %s", record.get("operation_id", ""))
        retry = cls._retry(retry_plan)  # The devices that a retry upgrades again.
        reconcile = cls._reconcile(record)  # The child jobs that a check can settle.
        child_ids = ",".join(str(child["child_id"]) for child in reconcile["children"])  # A stable order.
        signature = f"retry={retry['count']};reconcile={child_ids}"  # The poll reloads the page on a change.
        logger.debug("The recovery controls read %s", signature)  # The signature holds no secret.
        return {"retry": retry, "reconcile": reconcile, "signature": signature}  # The page reads each part.

    @staticmethod
    def _retry(retry_plan: OrgRetryPlan | None) -> dict[str, Any]:
        """Return the retry control values."""
        devices = [dict(device) for device in retry_plan.devices] if retry_plan is not None else []  # Copies.
        return {"available": bool(devices), "count": len(devices), "devices": devices}  # The page lists each one.

    @staticmethod
    def _reconcile(record: Mapping[str, Any]) -> dict[str, Any]:
        """Return the reconciliation control values."""
        children = [child.view() for child in OrgReconcileCheck(record).children()]  # One row for each child.
        claimed = bool(record.get("submission_claim_id"))  # A live submission can still write.
        operation_id = str(record.get("operation_id") or "")  # The typed word names the operation.
        return {  # The page shows the form only when a check can run.
            "available": bool(children) and not claimed,
            "word": f"RECONCILE {operation_id}",
            "children": children,
        }
