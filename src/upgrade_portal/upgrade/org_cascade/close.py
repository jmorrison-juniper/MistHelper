"""End the phase watch of one multi-site upgrade, and take the post-check captures first.

Why:
    Issue #3244. The single-site driver takes a post-check capture of its site
    after the last phase, and after a stop. It writes the end of the run only
    after that capture. The multi-site watch follows the same order. The stage
    takes one capture of each site, one site at a time, in the plan order. The
    close then writes the finished state or the stopped state.

    The stage sends no firmware write. It reads each site through the capture
    seam, and it writes the operation record only.
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Mapping, MutableMapping
from typing import Any

from src.upgrade_portal.upgrade.driver import POST_CHECK_MANUAL
from src.upgrade_portal.upgrade.org_cascade.record import (
    FINISHED_NOTE,
    STOPPED_NOTE,
    OrgPhaseEntries,
    OrgPhaseStore,
    OrgPhaseWatch,
    WatchState,
)
from src.upgrade_portal.upgrade.org_postcheck import (
    FAILED_MESSAGE,
    FINAL_ROW_STATES,
    HELD_MESSAGE,
    RUNNING_MESSAGE,
    SKIPPED_MESSAGE,
    STAGE_NOTE,
    OrgPostCheckRows,
    PostCheckResult,
    PostCheckSite,
    PostCheckState,
    PostCheckTaker,
)

logger = logging.getLogger(__name__)  # One logger for the end of the phase watch.


class OrgPostCheckStage:
    """Take the post-check capture of each site of one operation."""

    def __init__(self, taker: PostCheckTaker | None, records: OrgPhaseStore, operation_id: str) -> None:
        """Keep the capture seam, the bounded writer, and the key of one operation.

        Args:
            taker: The capture seam, or None when the walk holds no seam.
            records: The bounded writer of the operation record.
            operation_id: The key of the operation record.
        """
        self._taker = taker  # The seam that reads one site after the upgrade.
        self._records = records  # FR-006: each row reaches the record through the compare-and-set.
        self._operation_id = operation_id  # The key of the record, for the log.

    def run(self) -> None:
        """Visit each site in the plan order, and store one row for each site.

        Why:
            FR-018. The stage ignores a cancel request. A single-site stop
            takes its post-check capture too, and the captures show the state
            of each site after the phases.
        """
        if self._taker is None:  # A caller built the walk with no seam.
            logger.warning(  # The gap, before the walk ends with no capture.
                "org post-check: no post-check seam for %s, so the portal takes no capture", self._operation_id
            )
            return  # The walk ends as it did before issue #3244.
        record = self._records.read() or {}  # One read decides the sites and the stored rows.
        sites = OrgPostCheckRows.sites_of(record)  # FR-005: the plan order.
        if not sites:  # A damaged plan names no site.
            logger.warning("org post-check: the plan of %s names no site", self._operation_id)  # The gap.
            return  # No row and no stage note.
        logger.info("org post-check: visit %d site(s) of %s", len(sites), self._operation_id)  # Before the stage.
        self._records.update(OrgPostCheckStage._open)  # FR-015: the watch stays active during the stage.
        stored = OrgPostCheckRows.of(record)  # FR-008: the rows that an earlier stage wrote.
        for site in sites:  # FR-005: one site at a time.
            self._visit(self._taker, site, stored.get(site.site_id))  # One row for each site.
        logger.debug("org post-check: visited every site of %s", self._operation_id)  # After the stage.

    @staticmethod
    def _open(record: MutableMapping[str, Any]) -> None:
        """Open the stage in a candidate record.

        Why:
            A stop can arrive while a phase waits. No thread waits for that
            phase during the stage, so the entry goes back to pending first.
            The watch keeps the running state, so the page poll continues.
        """
        OrgPhaseEntries.reset_waiting(record)  # The page shows no wait that no thread performs.
        OrgPhaseWatch.set_state(record, WatchState.RUNNING, STAGE_NOTE, None)  # The page names the stage.

    def _visit(self, taker: PostCheckTaker, site: PostCheckSite, stored: Mapping[str, Any] | None) -> None:
        """Store the row of one site, and take its capture when the rules permit it.

        Args:
            taker: The capture seam.
            site: The site to visit.
            stored: The row that an earlier stage stored, or None.
        """
        if stored is not None and stored.get("state") in FINAL_ROW_STATES:  # FR-008: a final row stays.
            logger.info("org post-check: keep the %s row of site %s", stored.get("state"), site.site_id)  # No capture.
            return  # A resumed stage takes no second capture of this site.
        if not site.accepted:  # FR-010: the site received no firmware write.
            self._put(site.row(PostCheckState.SKIPPED, SKIPPED_MESSAGE))  # The row says why.
            return  # No capture of this site.
        if taker.mode == POST_CHECK_MANUAL:  # FR-009: the operator takes the second capture.
            self._put(site.row(PostCheckState.HELD, HELD_MESSAGE))  # The row says why.
            return  # No capture of this site.
        self._put(site.ended_row(self._take(taker, site)))  # FR-011: a failed capture still gets a row.

    def _take(self, taker: PostCheckTaker, site: PostCheckSite) -> PostCheckResult:
        """Take one capture of one site, and turn a fault into a failed result.

        Args:
            taker: The capture seam.
            site: The site to read.

        Returns:
            The end of the capture.
        """
        capture_id = taker.new_capture_id()  # FR-003: a new key with the post-check ordinal.
        self._put(site.row(PostCheckState.RUNNING, RUNNING_MESSAGE, capture_id))  # The page shows the read.
        logger.info("org post-check: take capture %s of site %s", capture_id, site.site_id)  # Before the capture.
        try:  # The capture reads a network, so a fault must stay inside this site.
            result = taker.take(site, capture_id)  # Blocks until the capture ends.
        except Exception as error:  # Keep broad: FR-011 continues with the next site.
            logger.error(  # After the fault. The capture log keeps the details.
                "org post-check: capture %s of site %s stopped with %s", capture_id, site.site_id, type(error).__name__
            )
            return PostCheckResult(capture_id, False, FAILED_MESSAGE)  # The row shows the failure.
        logger.debug(  # After the capture.
            "org post-check: capture %s of site %s verified=%s", capture_id, site.site_id, result.verified
        )
        return result  # The caller stores the final row.

    def _put(self, row: Mapping[str, Any]) -> None:
        """Store one row through the bounded compare-and-set."""
        self._records.update(functools.partial(OrgPostCheckRows.put, row=row))  # One write for each row.


class OrgCascadeClose:
    """End the phase watch of one operation after the post-check stage."""

    def __init__(self, records: OrgPhaseStore, taker: PostCheckTaker | None, operation_id: str) -> None:
        """Keep the bounded writer, the capture seam, and the key of one operation.

        Args:
            records: The bounded writer of the operation record.
            taker: The capture seam, or None when the walk holds no seam.
            operation_id: The key of the operation record.
        """
        self._records = records  # The final state reaches the record through the compare-and-set.
        self._stage = OrgPostCheckStage(taker, records, operation_id)  # The captures come first.
        self._operation_id = operation_id  # The key of the record, for the log.

    def finish(self) -> str:
        """Take the post-check captures, then write the finished state with the first failure.

        Returns:
            The finished watch state.
        """
        self._stage.run()  # FR-001: the captures come before the final state.
        record = self._records.read() or {}  # The phase entries and the post-check rows.
        reason = OrgPhaseEntries.first_failure(record) or OrgPostCheckRows.first_failure(record)  # FR-011.
        note = reason or FINISHED_NOTE  # A failure replaces the note, as the single-site run reason does.
        logger.info("org cascade: finish the watch of %s with reason %s", self._operation_id, reason)  # Before.
        self._records.update(  # The page shows the verdict.
            functools.partial(OrgPhaseWatch.set_state, state=WatchState.FINISHED, note=note, reason=reason)
        )
        logger.debug("org cascade: wrote the finished watch state of %s", self._operation_id)  # After the write.
        return WatchState.FINISHED.value  # The thread ends.

    def stop(self) -> str:
        """Take the post-check captures, then write the stopped state.

        Returns:
            The stopped watch state.
        """
        logger.info("org cascade: stop the watch of %s after a cancellation", self._operation_id)  # Before.
        self._stage.run()  # FR-002: a stop takes the captures too, as a single-site stop does.
        self._records.update(  # The page shows the stopped watch, and no phase waits.
            functools.partial(OrgCascadeClose.end, state=WatchState.STOPPED, note=STOPPED_NOTE)
        )
        logger.debug("org cascade: wrote the stopped watch state of %s", self._operation_id)  # After the write.
        return WatchState.STOPPED.value  # The thread ends.

    @staticmethod
    def end(record: MutableMapping[str, Any], state: WatchState, note: str) -> None:
        """End the watch in a candidate record, and put each waiting phase back to pending.

        Why:
            A single-site phase that a stop interrupts keeps its pending entry.
            The multi-site entry goes back to pending too, so the page does not
            show a wait that no thread performs.

        Args:
            record: The candidate record. The store writes it after this call.
            state: The final watch state.
            note: The sentence that the page shows.
        """
        OrgPhaseEntries.reset_waiting(record)  # No thread waits for a phase after this write.
        OrgPhaseWatch.set_state(record, state, note, None)  # The page shows the end of the watch.
