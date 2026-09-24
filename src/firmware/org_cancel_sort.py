"""Sort the access points of one organization cancel into three lists.

Why:
    Issue #3246. The single-site stop shows which devices stopped, which
    devices can still write firmware, and which devices have no cancel path.
    The access point child job of a multi-site operation kept only the status
    word of its cancel. The operator could not see which access point still
    wrote firmware. This module applies the single-site sort rule to the
    organization answer that the portal read last.

    The organization answer holds one entry for each site. The portal never
    guesses a list that the answer does not hold. If one site has no readable
    list, every access point goes to the list of devices that can still write
    firmware.
"""

from __future__ import annotations  # Keep modern annotations available at runtime.

import logging  # Record each sort before and after its action.
from collections.abc import Mapping, Sequence  # Name the read-only shapes of a stored record.
from typing import Any  # Accept the stored child job as plain JSON.

from src.firmware.org_upgrade_service import OrgUpgradeResult  # The result of one organization cancel.
from src.firmware.upgrade_service import CancelOutcome, reboot_macs, sort_cancel  # The single-site sort rule.

logger = logging.getLogger(__name__)  # Use the module logger without secret fields.

SITE_FIELDS = ("upgrades", "site_upgrades")  # The two answer fields that hold one entry for each site.
UNCONFIRMED_TEXT = (  # The sentence that follows the cloud error of a refused cancel.
    "The portal cannot confirm the cancel. Treat each access point as a device that can still write firmware."
)


class OrgRebootLists:
    """Read the access points that can still write firmware from one organization answer."""

    @classmethod
    def writing(cls, status_data: Any, site_ids: frozenset[str]) -> frozenset[str] | None:
        """Return the access points that can still write firmware.

        Why:
            A root list names the access points of every site. Without a root
            list, each site of the child job needs its own readable list. An
            absent list must never read as an empty list, because the caller
            then reports each access point as stopped.

        Args:
            status_data: The organization answer that the portal read last.
            site_ids: The sites of the access points in the child job.

        Returns:
            The MAC addresses in lower case with no separator, or None when
            the answer does not name a list for every site.
        """
        if not isinstance(status_data, Mapping):  # A child job with no stored answer holds no list.
            return None  # The portal cannot tell which access point writes firmware.
        lists = cls._site_lists(status_data)  # Read the list of each site entry, or None for damage.
        covered = cls._holds_lists(status_data)  # A root list names the access points of every site.
        root = reboot_macs(status_data) if covered else frozenset()  # Read the root list when it exists.
        if lists is None or root is None:  # A damaged list is not a list.
            return None  # Never trust a partial answer.
        known = {site: values for site, values in lists.items() if values is not None}  # Keep each read site.
        if not covered and not site_ids.issubset(known):  # One site of the child job has no list.
            return None  # The portal cannot tell which access point of that site writes firmware.
        return root.union(*known.values())  # Join the root list and each site list.

    @classmethod
    def _site_lists(cls, status_data: Mapping[str, Any]) -> dict[str, frozenset[str] | None] | None:
        """Return the list of each site entry, or None for a damaged answer.

        Why:
            A site entry that names only its job identifier holds no list. The
            site then stays unread, even when a second entry holds a list.
        """
        lists: dict[str, frozenset[str] | None] = {}  # Map each site to its list, or to None when unread.
        for field in SITE_FIELDS:  # The cloud writes the site entries in one of two fields, or in both.
            entries = status_data.get(field) or ()  # An empty or absent field adds no entry.
            if isinstance(entries, str) or not isinstance(entries, Sequence):  # A damaged field is not a list.
                return None  # Never trust a partial answer.
            if not all(cls._add_entry(lists, entry) for entry in entries):  # One damaged entry spoils the answer.
                return None  # Never trust a partial answer.
        return lists  # Give the caller each site list.

    @classmethod
    def _add_entry(cls, lists: dict[str, frozenset[str] | None], entry: Any) -> bool:
        """Add the list of one site entry to the site lists.

        Returns:
            False when the entry is damaged, so the caller trusts no list.
        """
        read = cls._entry_job(entry)  # Split the entry into its site and its job.
        if read is None:  # An entry with no site is damaged.
            return False  # The caller trusts no list.
        site_id, job = read  # Name the two parts of the entry.
        if not cls._holds_lists(job):  # A reference entry names the job, but it holds no list.
            lists[site_id] = None  # The site stays unread, even when another entry reads it.
            return True  # A reference entry is not damaged.
        values = reboot_macs(job)  # Read the reboot list of this site job.
        if values is None:  # A damaged list is not a list.
            return False  # The caller trusts no list.
        known = lists.get(site_id, frozenset())  # The list that the earlier entries of this site gave.
        lists[site_id] = None if known is None else known | values  # An unread site stays unread.
        return True  # The entry added its list.

    @staticmethod
    def _entry_job(entry: Any) -> tuple[str, Mapping[str, Any]] | None:
        """Return the site and the job of one site entry, or None for a damaged entry."""
        site_id = entry.get("site_id") if isinstance(entry, Mapping) else None  # Read the site of the entry.
        if not isinstance(site_id, str) or not site_id:  # An entry with no site cannot cover one.
            return None  # The answer is damaged.
        nested = entry.get("upgrade")  # The real cloud nests the site job under this key.
        job = nested if isinstance(nested, Mapping) else entry  # An earlier shape keeps the lists on the entry.
        return site_id, job  # The caller reads the device lists of this job.

    @staticmethod
    def _holds_lists(job: Mapping[str, Any]) -> bool:
        """Report whether one job holds the target lists of its devices.

        Why:
            A status word alone never holds a list. The reboot reader reads a
            job with a status word and no list as a job with no rebooting
            device. That reading claims a stop that the cloud never confirmed.
        """
        return isinstance(job.get("targets"), Mapping) or "reboot_in_progress" in job  # Look for a list field.


class OrgCancelSort:
    """Build the stored result of one organization cancel of access points."""

    @classmethod
    def result(cls, child: Mapping[str, Any], cancel: OrgUpgradeResult) -> dict[str, Any]:
        """Return the stored cancel result with the three device lists.

        Args:
            child: The access point child job, with its last stored answer.
            cancel: The result of the organization cancel call.

        Returns:
            The status word, the HTTP status, the three lists, and one sentence.
        """
        macs, site_ids = cls._targets(child)  # Name each access point and each site of the child job.
        logger.info("Sort the cancel of %s access point(s) at %s site(s)", len(macs), len(site_ids))  # Log first.
        if cancel.error is not None:  # The cloud refused the cancel, or its answer is damaged.
            outcome = CancelOutcome((), macs, (), f"{cancel.error} {UNCONFIRMED_TEXT}")  # Claim no stop.
        else:  # The cloud accepted the cancel.
            writing = OrgRebootLists.writing(child.get("status_data"), site_ids)  # Read the rebooting devices.
            outcome = sort_cancel(macs, writing, cancel.raw_status)  # Apply the single-site sort rule.
        stopped, writing_count = len(outcome.cancelled), len(outcome.already_writing)  # Count two of the lists.
        logger.debug("The cancel sorted %s stopped and %s writing", stopped, writing_count)  # Log after the sort.
        return {  # Keep the same keys as the result of a site child job.
            "status": "requested" if cancel.error is None else "failed",  # Do not claim a failed request.
            "raw_status": cancel.raw_status,  # Preserve the exact HTTP status.
            "cancelled": list(outcome.cancelled),  # The access points that stopped before the write.
            "already_writing": list(outcome.already_writing),  # The access points that can still write firmware.
            "no_cancel_available": list(outcome.no_cancel_available),  # An organization cancel covers each one.
            "message": outcome.message,  # Keep the exact safe summary.
        }

    @classmethod
    def _targets(cls, child: Mapping[str, Any]) -> tuple[tuple[str, ...], frozenset[str]]:
        """Return the MAC address of each access point, and the site of each one.

        Why:
            A record from before issue #3249 holds no target rows. Its access
            points then get the site "", which no answer can read. Only a root
            list can then sort them.
        """
        rows = cls._rows(child)  # Read each target row that is not damaged.
        if not rows:  # An earlier record holds only the target identifiers.
            return tuple(str(mac) for mac in child.get("target_ids") or ()), frozenset({""})  # No site is known.
        macs = tuple(str(row.get("mac") or "") for row in rows)  # Keep the plan order of the access points.
        return macs, frozenset(str(row.get("site_id") or "") for row in rows)  # A missing site reads as "".

    @staticmethod
    def _rows(child: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        """Return the target rows of one child job, without a damaged row."""
        return [row for row in child.get("targets") or () if isinstance(row, Mapping)]  # Skip a row of another type.
