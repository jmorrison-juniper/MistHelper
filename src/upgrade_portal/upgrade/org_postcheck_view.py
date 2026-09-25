"""The post-check card rows of one multi-site upgrade (issue #3244).

Why:
    The progress page and the status poll show one post-check row for each
    site. A stored row tells the operator what the stage did. A site with no
    stored row needs a sentence too, so the operator never reads an empty row.
    This module builds both kinds of row from the durable record, so the page
    and the poll always agree. It reads no store and no cloud.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final
from urllib.parse import quote, urlencode

from src.upgrade_portal.upgrade.org_cascade.record import SUBMISSION_OPEN_STATES, WATCH_KEY
from src.upgrade_portal.upgrade.org_postcheck import SKIPPED_MESSAGE, OrgPostCheckRows, PostCheckSite, PostCheckState
from src.upgrade_portal.upgrade.org_precheck import OrgPrecheckGate

logger = logging.getLogger(__name__)  # One logger for the post-check card.

# WHY: Two view states have no stored row. The stage writes neither of them.
WAITING_STATE: Final[str] = "waiting"  # The watch can still take the capture.
NOT_TAKEN_STATE: Final[str] = "not_taken"  # The watch ended with no capture of the site.

# WHY: The page shows one short label for each row state.
STATE_LABELS: Final[Mapping[str, str]] = {  # The label of each view state.
    WAITING_STATE: "Waiting",
    PostCheckState.RUNNING.value: "Running",
    PostCheckState.VERIFIED.value: "Verified",
    PostCheckState.FAILED.value: "Failed",
    PostCheckState.HELD.value: "Held",
    PostCheckState.SKIPPED.value: "Skipped",
    NOT_TAKEN_STATE: "Not taken",
}

# WHY: Each row shows one sentence. These sentences belong to the view only.
WAITING_MESSAGE: Final[str] = "The portal takes this capture after the last phase ends."  # Before the stage.
NOT_TAKEN_MESSAGE: Final[str] = "The phase watch ended before the portal took this capture."  # No capture.
LOST_MESSAGE: Final[str] = "The portal did not record the end of this capture."  # A running row with no watch.
VERIFIED_MESSAGE: Final[str] = "The portal read the capture back, and the record matches."  # A row with no text.
NO_PAIR_MESSAGE: Final[str] = (  # A verified row that has no pre-check capture to compare.
    "The portal verified this capture. The operation holds no pre-check capture of this site, "
    "so the page shows no compare link."
)

# WHY: The capture route and the compare route own these two paths.
CAPTURE_PAGE_PREFIX: Final[str] = "/captures/"  # The capture page of one key.
COMPARE_PAGE_PATH: Final[str] = "/compare"  # The compare page of two keys.


@dataclass(frozen=True, slots=True)
class PostCheckFacts:
    """Hold the record facts that every row of one card reads.

    Attributes:
        stored: The stored row of each site, keyed by the site identifier.
        prechecks: The pre-check capture key of each site.
        active: True while the phase watch can still take a capture.
        open_plan: True while the submission can still accept a child job.
    """

    stored: Mapping[str, Mapping[str, Any]]  # The rows that the stage wrote.
    prechecks: Mapping[str, str]  # The first half of each comparison.
    active: bool  # The poll flag of the phase card.
    open_plan: bool  # A site with no write can still receive one.


class OrgPostCheckView:
    """Build the post-check rows of the multi-site page and the status poll."""

    @staticmethod
    def rows(record: Mapping[str, Any], active: bool) -> list[dict[str, Any]]:
        """Return one view row for each site of the plan.

        Args:
            record: The durable operation record.
            active: The ``phase_active`` flag of the phase card.

        Returns:
            The rows in the plan order. A record with no phase watch gets no row (FR-016).
        """
        if not isinstance(record.get(WATCH_KEY), Mapping):  # A record of an earlier release holds no watch.
            logger.debug("org postcheck: the record holds no phase watch, so the page shows no card")  # After.
            return []  # FR-016: no post-check card.
        facts = PostCheckFacts(
            stored=OrgPostCheckRows.of(record),  # The rows that the stage wrote.
            prechecks={str(row["site_id"]): str(row["capture_id"] or "") for row in OrgPrecheckGate.rows_of(record)},
            active=active,  # The same rule as the poll of the phase card.
            open_plan=str(record.get("state", "")) in SUBMISSION_OPEN_STATES,  # The submission still writes.
        )
        return [OrgPostCheckView._row(site, facts) for site in OrgPostCheckRows.sites_of(record)]  # Plan order.

    @staticmethod
    def _row(site: PostCheckSite, facts: PostCheckFacts) -> dict[str, Any]:
        """Return the view row of one site."""
        state, message, capture_id = OrgPostCheckView._shown(site, facts)  # The state that the page shows.
        pre_capture_id = facts.prechecks.get(site.site_id, "")  # The first half of the comparison.
        if state == PostCheckState.VERIFIED and not pre_capture_id:  # FR-013: no pair exists.
            message = NO_PAIR_MESSAGE  # Tell the operator why no compare link shows.
        return {
            "site_id": site.site_id,  # The key of the row on the page.
            "site_name": site.site_name,  # The name that the operator reads.
            "state": state,  # The machine state for the test and the paint.
            "state_label": STATE_LABELS.get(state, state),  # The short label of the page.
            "message": message,  # The sentence of the row.
            "capture_id": capture_id,  # The post-check key, or empty text.
            "capture_href": CAPTURE_PAGE_PREFIX + quote(capture_id, safe="") if capture_id else "",  # One segment.
            "pre_capture_id": pre_capture_id,  # The pre-check key, or empty text.
            "compare_href": OrgPostCheckView._compare_href(state, pre_capture_id, capture_id),  # FR-013.
        }

    @staticmethod
    def _shown(site: PostCheckSite, facts: PostCheckFacts) -> tuple[str, str, str]:
        """Return the state, the sentence, and the capture key that the page shows for one site."""
        stored = facts.stored.get(site.site_id)  # The row that the stage wrote, or None.
        if stored is None:  # The stage did not reach this site.
            state, message = OrgPostCheckView._unstored(site, facts)  # Waiting, skipped, or not taken.
            return state, message, ""  # No capture exists.
        state = str(stored.get("state") or "")  # The stored row state.
        capture_id = str(stored.get("capture_id") or "")  # The key of the capture, or empty text.
        if state == PostCheckState.RUNNING and not facts.active:  # No thread can end this capture now.
            return PostCheckState.FAILED.value, LOST_MESSAGE, capture_id  # Tell the truth about the gap.
        default = VERIFIED_MESSAGE if state == PostCheckState.VERIFIED else ""  # A verified row always has text.
        return state, str(stored.get("message") or default), capture_id  # The stored reading.

    @staticmethod
    def _unstored(site: PostCheckSite, facts: PostCheckFacts) -> tuple[str, str]:
        """Return the state and the sentence of a site with no stored row."""
        if not site.accepted and not facts.open_plan:  # FR-010: the site received no firmware write.
            return PostCheckState.SKIPPED.value, SKIPPED_MESSAGE  # No capture comes for this site.
        if facts.active:  # The watch still runs, so the stage comes later.
            return WAITING_STATE, WAITING_MESSAGE  # User story 2: the row waits.
        return NOT_TAKEN_STATE, NOT_TAKEN_MESSAGE  # The watch ended with no capture.

    @staticmethod
    def _compare_href(state: str, pre_capture_id: str, capture_id: str) -> str:
        """Return the compare link of one row, or empty text when no pair exists."""
        if state != PostCheckState.VERIFIED or not pre_capture_id or not capture_id:  # FR-013: a pair only.
            return ""  # The page then hides the link.
        query = urlencode({"before": pre_capture_id, "after": capture_id})  # Each key stays one quoted value.
        return f"{COMPARE_PAGE_PATH}?{query}"  # The compare page reads both keys.
