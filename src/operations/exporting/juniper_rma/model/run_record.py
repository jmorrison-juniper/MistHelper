"""Run record for one menu run: counts, status, and the reason text (data-model.md)."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import uuid  # WHY: a unique run identifier for the run record and the link rows.
from datetime import UTC, datetime  # WHY: UTC timestamps for the run start and end.
from typing import Any  # WHY: the export row is a loosely typed dictionary.


class RunRecord:
    """Counts, status, and reason for one run. A new record starts in the running state."""

    COUNTER_NAMES = {  # WHY: map each outcome status to its counter attribute.
        "matched": "matched_count",
        "unmatched": "unmatched_count",
        "ambiguous": "ambiguous_count",
        "failed": "failed_count",
    }

    def __init__(self, operation: str) -> None:
        """Start the record for one operation with a new run identifier."""
        self.run_id = uuid.uuid4().hex  # WHY: a unique identifier for this run.
        self.operation = operation  # WHY: the menu operation name.
        self.started_at = datetime.now(UTC).isoformat(timespec="seconds")  # WHY: UTC start time.
        self.ended_at = ""  # WHY: set when the run finishes.
        self.status = "running"  # WHY: the run starts in the running state.
        self.problems: list[str] = []  # WHY: short reasons for an incomplete or failed run.
        self.ticket_count = 0  # WHY: Mist tickets read.
        self.matched_count = 0  # WHY: tickets with exactly one matching request.
        self.unmatched_count = 0  # WHY: tickets with no matching request.
        self.ambiguous_count = 0  # WHY: tickets with more than one matching request.
        self.failed_count = 0  # WHY: tickets whose Juniper call failed.
        self.request_count = 0  # WHY: Juniper calls that the run sent.
        self.purged_count = 0  # WHY: export files removed by the retention purge.

    def record_outcome(self, status: str) -> None:
        """Count one ticket outcome. Unknown statuses are ignored."""
        attribute = self.COUNTER_NAMES.get(status)  # WHY: find the counter for this status.
        if attribute is not None:  # WHY: only known statuses change a counter.
            setattr(self, attribute, getattr(self, attribute) + 1)  # WHY: add one to that counter.

    def add_requests(self, count: int = 1) -> None:
        """Count the Juniper calls that the run sent."""
        self.request_count += count  # WHY: keep the total of calls for the summary.

    def note_problem(self, text: str) -> None:
        """Keep a short reason for an incomplete run. Never store a secret or a personal value."""
        self.problems.append(text[:200])  # WHY: short text, bounded in length.

    def finish(self, status: str | None = None) -> None:
        """Set the final status. An explicit status wins. Otherwise any note makes the run incomplete."""
        self.ended_at = datetime.now(UTC).isoformat(timespec="seconds")  # WHY: UTC end time.
        if status is not None:  # WHY: a failed run names its own status.
            self.status = status  # WHY: the caller decides, for example for a failed request list.
        else:  # WHY: the normal path decides from the notes.
            self.status = "incomplete" if self.problems else "complete"  # WHY: notes mean the run was not whole.

    def as_row(self) -> dict[str, Any]:
        """Return one export row for the run record."""
        return {  # WHY: the columns of JuniperRunRecords.csv.
            "runId": self.run_id,  # WHY: run identifier.
            "operation": self.operation,  # WHY: menu operation.
            "startedAt": self.started_at,  # WHY: start time.
            "endedAt": self.ended_at,  # WHY: end time.
            "ticketCount": self.ticket_count,  # WHY: tickets read.
            "matchedCount": self.matched_count,  # WHY: matched tickets.
            "unmatchedCount": self.unmatched_count,  # WHY: unmatched tickets.
            "ambiguousCount": self.ambiguous_count,  # WHY: ambiguous tickets.
            "failedCount": self.failed_count,  # WHY: failed tickets.
            "requestCount": self.request_count,  # WHY: Juniper calls sent.
            "purgedCount": self.purged_count,  # WHY: files removed by the retention purge.
            "status": self.status,  # WHY: final status.
            "reason": "; ".join(self.problems),  # WHY: reasons for an incomplete run.
        }
