"""The post-check rows of one multi-site upgrade (issue #3244).

Why:
    A single-site run takes a second capture of its site after the last phase.
    The operator then compares the capture before the upgrade with the capture
    after the upgrade. A multi-site operation gets the same proof for each
    site. This module holds the stored row of each site and the rules that read
    and write those rows. It reads no cloud, and it writes no store.
    ``org_cascade/close.py`` takes the captures.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Final, Protocol

from src.upgrade_portal.upgrade.org_cascade.record import OrgPhaseTargets
from src.upgrade_portal.upgrade.org_precheck import DEFAULT_TIER, OrgPrecheckGate

logger = logging.getLogger(__name__)  # One logger for the post-check rows.

# WHY: The operation record keeps the pre-check rows in ``pre_captures``. The
# post-check rows use the matching name, so a reader finds both halves.
POSTCHECK_FIELD: Final[str] = "post_captures"  # The operation field that holds the row of each site.


class PostCheckState(StrEnum):
    """Every state that the post-check row of one site can hold."""

    RUNNING = "running"  # The portal reads the site after the upgrade.
    VERIFIED = "verified"  # The portal read the capture back, and the record matches.
    FAILED = "failed"  # The capture stopped, or the portal could not read it back.
    HELD = "held"  # The post-check mode is manual, so the portal took no capture.
    SKIPPED = "skipped"  # The cloud accepted no firmware write for the site.


# WHY: A resumed stage keeps a row in one of these states. It takes no second
# capture of that site.
FINAL_ROW_STATES: Final[frozenset[str]] = frozenset(  # The states that a later stage never changes.
    {PostCheckState.VERIFIED, PostCheckState.FAILED, PostCheckState.HELD, PostCheckState.SKIPPED}
)

# WHY: The page shows one sentence for each row state. The sentences live here,
# so the stage and the view use the same words.
STAGE_NOTE: Final[str] = "The portal takes the post-check capture of each site."  # The watch note of the stage.
RUNNING_MESSAGE: Final[str] = "The portal reads the site after the upgrade."  # The row text during the read.
HELD_MESSAGE: Final[str] = (  # The row text in the manual mode.
    "The post-check mode is manual, so the portal took no post-check capture of this site."
)
SKIPPED_MESSAGE: Final[str] = (  # The row text of a site with no firmware write.
    "The cloud accepted no firmware write for this site, so the portal took no post-check capture."
)
FAILED_MESSAGE: Final[str] = "The post-check capture did not verify."  # The row text when the capture gave no text.
FAILURE_REASON: Final[str] = "The post-check capture of {site} did not verify."  # The watch reason of a failed row.


@dataclass(frozen=True, slots=True)
class PostCheckResult:
    """Hold the end of one post-check capture.

    Attributes:
        capture_id: The key of the capture.
        verified: True when the portal read the capture back unchanged.
        message: The last progress text of the capture.
    """

    capture_id: str  # The key that the compare link names.
    verified: bool  # Only a verified capture may enter a comparison.
    message: str = ""  # The capture progress text, for the row.


@dataclass(frozen=True, slots=True)
class PostCheckSite:
    """Hold one site that the post-check stage visits.

    Attributes:
        site_id: The site identifier.
        site_name: The name that the page shows.
        tier: The data tier of the pre-check capture. The post-check capture reads the same tier.
        accepted: True when the cloud accepted a firmware write for a device of this site.
    """

    site_id: str  # The key of the row.
    site_name: str  # The name that the page shows.
    tier: int  # The comparison needs two captures of the same tier.
    accepted: bool  # A site with no accepted write needs no proof of an upgrade.

    def row(self, state: PostCheckState, message: str, capture_id: str = "") -> dict[str, Any]:
        """Return the stored row of this site.

        Args:
            state: The state of the row.
            message: The sentence that the page shows.
            capture_id: The key of the capture, or an empty string when the portal took none.

        Returns:
            The row that the operation record stores.
        """
        return {  # One flat row, so the page and the poll read the same fields.
            "site_id": self.site_id,
            "site_name": self.site_name,
            "tier": self.tier,
            "state": state.value,
            "message": message,
            "capture_id": capture_id,
        }

    def ended_row(self, result: PostCheckResult) -> dict[str, Any]:
        """Return the stored row after the capture of this site ended.

        Args:
            result: The end of the capture.

        Returns:
            The verified row or the failed row.
        """
        state = PostCheckState.VERIFIED if result.verified else PostCheckState.FAILED  # The read-back decides.
        default = "" if result.verified else FAILED_MESSAGE  # A failed row always gives a reason.
        return self.row(state, result.message or default, result.capture_id)  # The capture text wins.


class PostCheckTaker(Protocol):
    """Take one post-check capture of one site.

    Why:
        The stage runs in the watch thread, which holds no request. The route
        module binds the cloud session, the operator, and the application
        context inside the request, and it passes this seam to the stage.
    """

    @property
    def mode(self) -> str:
        """Return the post-check mode: ``automatic`` or ``manual``."""

    def new_capture_id(self) -> str:
        """Return the key of one new post-check capture."""

    def take(self, site: PostCheckSite, capture_id: str) -> PostCheckResult:
        """Take one capture of one site, and return its end.

        Args:
            site: The site to read.
            capture_id: The key of the new capture.

        Returns:
            The end of the capture.
        """


class OrgPostCheckRows:
    """Read and write the post-check rows of one operation record."""

    @staticmethod
    def sites_of(record: Mapping[str, Any]) -> list[PostCheckSite]:
        """Return each site of the operation, in the plan order.

        Why:
            The plan stores ``site_ids`` in the order that the operator chose.
            An operation from an earlier release holds only the pre-check rows,
            so the reader then uses their order.

        Args:
            record: The durable operation record.

        Returns:
            One value for each site, with its name, its tier, and its write state.
        """
        prechecks = {str(row["site_id"]): row for row in OrgPrecheckGate.rows_of(record)}  # The first captures.
        names = record.get("site_names") if isinstance(record.get("site_names"), Mapping) else {}  # Page names.
        accepted = OrgPostCheckRows._accepted_sites(record)  # The sites with an accepted firmware write.
        site_ids = OrgPostCheckRows._site_ids(record, list(prechecks))  # The plan order, with no repeat.
        return [OrgPostCheckRows._site(site_id, names, prechecks.get(site_id, {}), accepted) for site_id in site_ids]

    @staticmethod
    def of(record: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
        """Return the stored row of each site, keyed by the site identifier.

        Args:
            record: The durable operation record.

        Returns:
            A detached copy of each stored row.
        """
        return {str(row["site_id"]): dict(row) for row in OrgPostCheckRows.stored(record)}  # One row for each site.

    @staticmethod
    def stored(record: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        """Return the valid stored rows, in the stored order.

        Args:
            record: The durable operation record.

        Returns:
            Each stored row that is a mapping and names a site.
        """
        rows = record.get(POSTCHECK_FIELD)  # The list that the stage writes.
        if not isinstance(rows, list):  # No stage ran yet, or the value is damaged.
            return []  # The page then shows the waiting rows.
        return [row for row in rows if isinstance(row, Mapping) and row.get("site_id")]  # Skip a damaged row.

    @staticmethod
    def put(record: MutableMapping[str, Any], row: Mapping[str, Any]) -> None:
        """Store one row in a candidate record, in place of the old row of its site.

        Args:
            record: The candidate record. The store writes it after this call.
            row: The new row of one site.
        """
        rows = [dict(entry) for entry in OrgPostCheckRows.stored(record)]  # Detached copies of the valid rows.
        sites = [str(entry["site_id"]) for entry in rows]  # The site of each stored row.
        site_id = str(row["site_id"])  # The site of the new row.
        if site_id in sites:  # The site already holds a row.
            rows[sites.index(site_id)] = dict(row)  # Keep the position, so the page order stays.
        else:  # The first row of this site.
            rows.append(dict(row))  # The stage visits the sites in the plan order.
        record[POSTCHECK_FIELD] = rows  # The store writes the whole list in one write.

    @staticmethod
    def first_failure(record: Mapping[str, Any]) -> str | None:
        """Return the reason of the first failed row, or None when no row failed.

        Args:
            record: The durable operation record.

        Returns:
            The sentence that names the first site whose capture failed.
        """
        for row in OrgPostCheckRows.stored(record):  # The stored order is the plan order.
            if row.get("state") == PostCheckState.FAILED:  # The first failure is the root cause.
                return FAILURE_REASON.format(site=row.get("site_name") or row["site_id"])  # Name the site.
        return None  # Every capture verified, or the portal took none.

    @staticmethod
    def _site_ids(record: Mapping[str, Any], fallback: list[str]) -> list[str]:
        """Return the unique site identifiers of the plan, in order."""
        listed = record.get("site_ids")  # The plan order that the operator chose.
        chosen = listed if isinstance(listed, list) else fallback  # An earlier release stored no list.
        return list(dict.fromkeys(str(site) for site in chosen if site))  # Unique, in the first order.

    @staticmethod
    def _site(
        site_id: str, names: Mapping[str, Any], precheck: Mapping[str, Any], accepted: frozenset[str]
    ) -> PostCheckSite:
        """Return the value of one site from the plan fields and its pre-check row."""
        name = str(names.get(site_id) or precheck.get("site_name") or site_id)  # A site with no name shows its key.
        tier = int(precheck.get("tier") or DEFAULT_TIER)  # The pre-check tier, so the comparison can run.
        return PostCheckSite(site_id, name, tier, site_id in accepted)  # One immutable value.

    @staticmethod
    def _accepted_sites(record: Mapping[str, Any]) -> frozenset[str]:
        """Return the sites that hold a device of an accepted child job.

        Why:
            The access point child job has the organization scope. Its own
            site field is empty, so the reader also reads the site of each
            target.
        """
        found: set[str] = set()  # The sites of the accepted child jobs.
        for child in OrgPhaseTargets.children(record):  # The valid child jobs, in the plan order.
            if OrgPhaseTargets.excluded(child):  # The cloud did not accept this child job.
                continue  # Its devices received no firmware write.
            found.add(str(child.get("site_id") or ""))  # A site child job names its site.
            found.update(OrgPostCheckRows._target_sites(child))  # An organization child job names each device site.
        return frozenset(found - {""})  # An empty value names no site.

    @staticmethod
    def _target_sites(child: Mapping[str, Any]) -> set[str]:
        """Return the site of each target of one child job."""
        targets = child.get("targets")  # The devices of the child job.
        if not isinstance(targets, list):  # A damaged child job holds no device list.
            return set()  # The child job adds no site.
        return {str(target.get("site_id") or "") for target in targets if isinstance(target, Mapping)}  # Each site.
