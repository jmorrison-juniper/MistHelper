"""Build the cancel outcome rows of one multi-site progress page.

Why:
    Issue #3246. The single-site stop page shows three device lists after a
    stop. The lists name the devices that the cloud canceled, the devices that
    can still write firmware, and the devices with no cancel path. The
    multi-site page showed one status word for each child job. This module
    builds the same three lists for each child job from the stored record.

    The portal never guesses a list. If a child job stores no complete set of
    lists, every device of it goes to the writing list. The one exception is
    a record that proves that no cloud job exists for the child job.
"""

from __future__ import annotations  # Keep modern annotations available at runtime.

import logging  # Record each build before and after its action.
from collections.abc import Mapping  # Name the read-only shape of a stored record.
from typing import Any  # Accept the stored record as plain JSON.

logger = logging.getLogger(__name__)  # Use the module logger without secret fields.

NEVER_STARTED_NOTE = (  # The note of a child job that has no cloud job.
    "No upgrade of this child job exists in the cloud, so no device of it writes firmware."
)
UNSORTED_NOTE = (  # The note of a child job whose cancel result holds no complete set of lists.
    "The portal cannot tell which devices of this child job stopped. "
    "Treat each device as a device that can still write firmware."
)


class OrgCancelLists:
    """Apply the three list rules to the cancel result of one child job."""

    KEYS = ("cancelled", "already_writing", "no_cancel_available")  # The three lists of one cancel result.
    REFUSED_STATUSES = range(400, 500)  # A client error proves that the cloud created no job.

    @classmethod
    def lists(cls, child: Mapping[str, Any], claimed: bool) -> tuple[dict[str, list[str]], str]:
        """Return the three lists of one child job, and the note that explains them.

        Args:
            child: The stored child job with a cancel result.
            claimed: True when the operation holds a live submission claim.

        Returns:
            The three lists, and the note, or an empty note for a stored result.
        """
        cancellation = child["cancellation"]  # The stored cancel result.
        if all(isinstance(cancellation.get(key), list) for key in cls.KEYS):  # The result holds every list.
            return {key: [str(mac) for mac in cancellation[key]] for key in cls.KEYS}, ""  # Copy each list.
        empty: dict[str, list[str]] = {key: [] for key in cls.KEYS}  # A partial result is not trusted.
        if cls._never_started(child, claimed):  # The record proves that no cloud job exists.
            return empty, NEVER_STARTED_NOTE  # No device of this child job writes firmware.
        return {**empty, "already_writing": cls._macs(child)}, UNSORTED_NOTE  # Claim no stop for any device.

    @classmethod
    def _never_started(cls, child: Mapping[str, Any], claimed: bool) -> bool:
        """Report whether the record proves that no cloud job exists for one child job.

        Why:
            Issue #3327. A live parent submission can still send a planned
            child job after the cancel. A planned child job proves nothing
            while the parent holds a live submission claim. A server error or
            a damaged success can hide a cloud job, so only a client error
            proves a refusal.
        """
        status = child.get("status")  # The state of the child job.
        if status == "not_submitted":  # The service stopped the plan before this child job.
            return True  # No later request can send it.
        if status == "planned":  # No request sent the child job yet.
            return not claimed  # A live submission can still send it.
        return status == "rejected" and child.get("raw_status") in cls.REFUSED_STATUSES  # The cloud refused it.

    @staticmethod
    def _macs(child: Mapping[str, Any]) -> list[str]:
        """Return the MAC address of each device of one child job, in plan order."""
        rows = [row for row in child.get("targets") or () if isinstance(row, Mapping)]  # Read each target row.
        if rows:  # A record from issue #3249 or later holds one row for each device.
            return [str(row.get("mac") or "") for row in rows]  # Keep the plan order.
        return [str(mac) for mac in child.get("target_ids") or ()]  # An earlier record holds the identifiers.


class OrgCancelOutcomes:
    """Build one cancel outcome row for each child job that holds a cancel result."""

    MULTIPLE_SITES = "Multiple sites"  # The label of a child job with no site name and no site.

    @classmethod
    def rows(cls, record: Any) -> list[dict[str, Any]]:
        """Return one row for each child job with a cancel result, in plan order.

        Args:
            record: The stored operation.

        Returns:
            The rows of the cancel outcome panel, or an empty list.
        """
        children = cls._cancelled_children(record)  # Keep each child job with a cancel result.
        logger.info("Build the cancel outcome rows of %s child job(s)", len(children))  # Log before the build.
        claimed = bool(children) and bool(record.get("submission_claim_id"))  # A live submission can still send.
        rows = [cls._row(child, claimed) for child in children]  # Build one row for each child job.
        logger.debug("Built %s cancel outcome row(s)", len(rows))  # Log after the build.
        return rows  # The page shows the rows in plan order.

    @classmethod
    def signature(cls, record: Any) -> str:
        """Return the cancel status of each child job as one text.

        Why:
            The poll paints text only. When one cancel status changes, the
            page loads again, so a second tab shows the new lists.

        Args:
            record: The stored operation.

        Returns:
            The pairs of child job and cancel status, joined with commas.
        """
        children = cls._cancelled_children(record)  # Keep each child job with a cancel result.
        pairs = [f"{child.get('child_id', '')}:{child['cancellation'].get('status', '')}" for child in children]
        return ",".join(pairs)  # An operation with no cancel result gives an empty text.

    @staticmethod
    def _cancelled_children(record: Any) -> list[Mapping[str, Any]]:
        """Return each child job that holds a cancel result, in plan order."""
        children = record.get("children") if isinstance(record, Mapping) else None  # Read the child jobs.
        if not isinstance(children, list):  # A damaged record holds no child job.
            return []  # The page shows no panel.
        return [  # A damaged child job or a damaged cancel result gives no row.
            child for child in children if isinstance(child, Mapping) and isinstance(child.get("cancellation"), Mapping)
        ]

    @classmethod
    def _row(cls, child: Mapping[str, Any], claimed: bool) -> dict[str, Any]:
        """Build the row of one child job."""
        cancellation = child["cancellation"]  # The stored cancel result.
        lists, note = OrgCancelLists.lists(child, claimed)  # Apply the three list rules.
        return {  # The template reads each key by name.
            "child_id": str(child.get("child_id") or ""),  # The test identifiers of the panel use this value.
            "label": str(child.get("site_name") or child.get("site_id") or cls.MULTIPLE_SITES),  # The site words.
            "device_family": str(child.get("device_family") or ""),  # The family word of the site table.
            "status": str(cancellation.get("status") or ""),  # The status word of the cancel.
            "message": str(cancellation.get("message") or ""),  # The exact sentence of the cancel, or no text.
            "note": note,  # The sentence that explains the lists, or no text.
            **lists,  # The three device lists.
        }
