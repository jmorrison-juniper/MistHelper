"""Encode and decode GitHub issue comments for crash recovery."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from typing import Any

from src.juniper_skills.tracking.models import STAGE_ORDER, ResumePoint, StageEvent, StageName


class StageCommentCodec:
    """Create and parse machine-readable stage comments."""

    block_start = "```json"
    block_end = "```"

    def build_comment(self, event: StageEvent) -> str:
        """Build a comment with STE prose and a JSON state block."""
        logging.info("Building the GitHub journal comment for stage %s", event.stage.value)  # Record the local action.
        payload = self._payload_for_event(event)  # Create the exact state that recovery reads later.
        json_block = json.dumps(payload, indent=2, sort_keys=True)  # Make the state deterministic for tests.
        comment = self._render_comment(event, json_block)  # Add human text before the machine-readable state.
        logging.debug("Built a GitHub journal comment with %d characters", len(comment))  # Record safe output size.
        return comment

    def parse_comments(self, comments: list[str], document_key: str) -> ResumePoint:
        """Read comments and return the most recent valid resume point."""
        logging.info("Parsing %d GitHub journal comments", len(comments))  # Record the recovery action.
        events = [event for body in comments for event in self._events_from_body(body)]  # Read all JSON state blocks.
        matching_events = [event for event in events if event.document_key == document_key]  # Keep this document.
        resume_point = self._resume_from_events(matching_events, document_key)  # Convert events into one resume point.
        logging.debug("Recovered resume action %s", resume_point.next_action)  # Record the recovered next action.
        return resume_point

    def _payload_for_event(self, event: StageEvent) -> dict[str, Any]:
        """Convert a stage event into a stable JSON payload."""
        payload = asdict(event)  # Convert the data class without losing optional fields.
        payload["stage"] = event.stage.value  # Store the public stage value, not the enum object.
        payload["schema"] = "juniper-skill-factory-stage-v1"  # Let future readers identify this block.
        return payload

    def _render_comment(self, event: StageEvent, json_block: str) -> str:
        """Render the human text and the JSON block."""
        metrics = self._metrics_lines(event.details)  # Build measured evidence for the human audit trail.
        human_lines = [  # Keep the prose short so issue comments stay readable.
            "Skill factory journal update.",
            f"Document key: `{event.document_key}`.",
            f"Stage complete: `{event.stage.value}`.",
            f"Next action: {event.next_action}.",
            *metrics,
        ]
        return "\n".join(human_lines + ["", self.block_start, json_block, self.block_end])  # Keep one parseable block.

    def _metrics_lines(self, details: dict[str, Any]) -> list[str]:
        """Return human-readable measured values for one stage."""
        metrics = self._normalized_metrics(details)  # Add defaults so every audit comment has the same fields.
        return [  # Keep each measurement on its own short line for readers.
            f"Topic count: {metrics['topic_count']}.",
            f"Card count: {metrics['card_count']}.",
            f"Retention percentage: {metrics['retention_percentage']}.",
            f"Guard result: {metrics['guard_result']}.",
            f"Longest guard run: {metrics['longest_guard_run']}.",
            f"STE score: {metrics['ste_score']}.",
        ]

    def _normalized_metrics(self, details: dict[str, Any]) -> dict[str, Any]:
        """Return required metrics with safe defaults."""
        return {  # Preserve provided values and make missing measurements explicit.
            "topic_count": details.get("topic_count", "not measured"),
            "card_count": details.get("card_count", "not measured"),
            "retention_percentage": details.get("retention_percentage", "not measured"),
            "guard_result": details.get("guard_result", "not measured"),
            "longest_guard_run": details.get("longest_guard_run", "not measured"),
            "ste_score": details.get("ste_score", "not measured"),
        }

    def _events_from_body(self, body: str) -> list[StageEvent]:
        """Extract all stage events from one issue comment body."""
        logging.info("Reading machine-readable blocks from one issue comment")  # Record each parse operation.
        blocks = self._json_blocks(body)  # Find fenced JSON blocks without reading other prose.
        events = [
            event for block in blocks if (event := self._event_from_json(block)) is not None
        ]  # Keep valid events.
        logging.debug("Read %d stage events from one issue comment", len(events))  # Record the parse result.
        return events

    def _json_blocks(self, body: str) -> list[str]:
        """Return the JSON fence contents from a comment."""
        blocks: list[str] = []  # Collect all machine-readable states in this comment.
        remaining = body  # Walk the string without a regular expression dependency.
        while self.block_start in remaining:  # Support comments that hold more than one state.
            remaining = remaining.split(self.block_start, 1)[1]  # Drop prose before the JSON fence.
            block, _, remaining = remaining.partition(self.block_end)  # Read the fenced JSON content.
            blocks.append(block.strip())  # Store a clean JSON string for decoding.
        return blocks

    def _event_from_json(self, block: str) -> StageEvent | None:
        """Decode one JSON block into a stage event."""
        try:
            payload = json.loads(block)  # Decode the state that GitHub stored.
            if payload.get("schema") != "juniper-skill-factory-stage-v1":  # Ignore unrelated JSON comments.
                return None
            return StageEvent(  # Rebuild the typed event for recovery logic.
                document_key=str(payload["document_key"]),
                stage=StageName(str(payload["stage"])),
                next_action=str(payload["next_action"]),
                issue_number=payload.get("issue_number"),
                created_at=str(payload["created_at"]),
                details=dict(payload.get("details", {})),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            logging.debug("Ignored an invalid journal JSON block: %s", error)  # Tolerate user comments.
            return None

    def _resume_from_events(self, events: list[StageEvent], document_key: str) -> ResumePoint:
        """Create a resume point from stage events."""
        if not events:  # A new document starts at the first pipeline action.
            return ResumePoint(document_key, None, "queue the document", None, "comments")
        latest_event = max(events, key=lambda event: event.created_at)  # Use the newest state as the exact checkpoint.
        if latest_event.stage == StageName.FAILED:  # A failure requires repair before the normal stage order resumes.
            return ResumePoint(
                document_key,
                None,
                latest_event.next_action,
                latest_event.issue_number,
                "comments",
                True,
            )  # Resume at failure repair.
        next_action = self._next_action_after(latest_event.stage)  # Advance from the last completed stage.
        return ResumePoint(document_key, latest_event.stage, next_action, latest_event.issue_number, "comments")

    def _next_action_after(self, stage: StageName) -> str:
        """Return the next pipeline action after a completed stage."""
        if stage in {StageName.VERIFIED, StageName.RELEASED}:  # A terminal document needs no more pipeline work.
            return "no action"
        stage_index = STAGE_ORDER.index(stage)  # Convert the enum into its pipeline position.
        return f"run the {STAGE_ORDER[stage_index + 1].value} stage"  # Name the next stage for recovery.
