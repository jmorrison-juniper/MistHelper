"""SQLite mirror for the Juniper skill factory journal."""

from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from src.juniper_skills.tracking.models import DocumentRecord, StageEvent


class FactoryJournalStore:
    """Persist document journal state before GitHub receives it."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path  # Keep the factory database path explicit for tests and production.
        self.database_path.parent.mkdir(parents=True, exist_ok=True)  # Create the data directory when it is absent.
        self._initialize()  # Ensure the required tables exist before any write.

    def save_document(self, document: DocumentRecord, issue_shape: str) -> None:
        """Upsert one source document record."""
        logging.info("Saving document metadata in the local journal mirror")  # Record the local database action.
        with self._connect() as connection:  # Open a short transaction for this upsert.
            connection.execute(  # Store enough metadata to rebuild the issue title and body.
                """
                INSERT INTO skill_documents
                (document_key, source_path, title, category, page_count, domain, issue_shape)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_key) DO UPDATE SET
                source_path=excluded.source_path, title=excluded.title,
                category=excluded.category, page_count=excluded.page_count,
                domain=excluded.domain, issue_shape=excluded.issue_shape
                """,
                self._document_values(document, issue_shape),
            )
        logging.debug("Saved document metadata for key %s", document.document_key)  # Record the affected key.

    def save_issue_number(self, document_key: str, issue_number: int) -> None:
        """Record the GitHub issue number for a document."""
        logging.info("Saving the GitHub issue number in the local journal mirror")  # Record the local database action.
        with self._connect() as connection:  # Keep the issue update atomic.
            connection.execute(  # Store the GitHub link for idempotent retries.
                "UPDATE skill_documents SET issue_number = ? WHERE document_key = ?",
                (issue_number, document_key),
            )
        logging.debug("Saved issue %d for document key %s", issue_number, document_key)  # Record safe link details.

    def get_issue_number(self, document_key: str) -> int | None:
        """Return the stored GitHub issue number for a document."""
        logging.info("Reading the local GitHub issue number")  # Record the read action.
        with self._connect() as connection:  # Use a short-lived connection for thread safety.
            row = connection.execute(  # Read only the issue number that idempotency needs.
                "SELECT issue_number FROM skill_documents WHERE document_key = ?",
                (document_key,),
            ).fetchone()
        issue_number = None if row is None or row["issue_number"] is None else int(row["issue_number"])  # Normalize.
        logging.debug("Read local issue %s for document key %s", issue_number, document_key)  # Record the result.
        return issue_number

    def enqueue_stage_event(self, event: StageEvent, comment_body: str) -> int:
        """Store a stage event and queue its GitHub comment."""
        logging.info("Saving a stage event in the local journal mirror")  # Record the durable local write.
        with self._connect() as connection:  # Keep the event and queue row in one transaction.
            cursor = connection.execute(  # Store the exact state before any network call.
                """
                INSERT INTO skill_stage_events
                (document_key, stage, next_action, issue_number, created_at, details_json, comment_body, github_synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                """,
                self._event_values(event, comment_body),
            )
            event_id = int(cursor.lastrowid)  # Read the row ID before the connection closes.
        logging.debug("Queued stage event row %d for GitHub sync", event_id)  # Record the queue position.
        return event_id

    def unsynced_stage_events(self, limit: int) -> list[dict[str, Any]]:
        """Return queued stage events that GitHub still needs."""
        logging.info("Reading unsynced stage events from the local mirror")  # Record the queue read.
        with self._connect() as connection:  # Open a read transaction for a bounded batch.
            rows = connection.execute(  # Keep the batch small to respect rate limits.
                """
                SELECT id, issue_number, comment_body FROM skill_stage_events
                WHERE github_synced = 0 AND issue_number IS NOT NULL
                ORDER BY id ASC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        events = [dict(row) for row in rows]  # Convert sqlite rows into test-friendly dictionaries.
        logging.debug("Read %d unsynced stage events", len(events))  # Record the batch size.
        return events

    def mark_stage_event_synced(self, event_id: int) -> None:
        """Mark one queued stage event as sent to GitHub."""
        logging.info("Marking a stage event as synced")  # Record the local update action.
        with self._connect() as connection:  # Keep the update scoped to one row.
            connection.execute(  # Mark the row only after GitHub accepts the comment.
                "UPDATE skill_stage_events SET github_synced = 1 WHERE id = ?",
                (event_id,),
            )
        logging.debug("Marked stage event %d as synced", event_id)  # Record the updated row.

    def local_comment_bodies(self, document_key: str) -> list[str]:
        """Return stored comment bodies for one document."""
        logging.info("Reading local journal comments for crash recovery")  # Record the recovery read action.
        with self._connect() as connection:  # Read local events if GitHub was unavailable.
            rows = connection.execute(  # Order by creation sequence for deterministic recovery.
                "SELECT comment_body FROM skill_stage_events WHERE document_key = ? ORDER BY id ASC",
                (document_key,),
            ).fetchall()
        comments = [str(row["comment_body"]) for row in rows]  # Return only the comment text that the codec parses.
        logging.debug("Read %d local journal comments", len(comments))  # Record the number of local comments.
        return comments

    def _initialize(self) -> None:
        """Create the journal tables if they do not exist."""
        logging.info("Initializing the local journal mirror database")  # Record the schema action.
        with self._connect() as connection:  # Use one transaction for all schema statements.
            connection.execute(self._documents_schema())  # Create the document mirror table.
            connection.execute(self._events_schema())  # Create the durable comment queue table.
        logging.debug("Initialized the local journal mirror at %s", self.database_path)  # Record the database path.

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Open a row-based SQLite connection."""
        connection = sqlite3.connect(self.database_path)  # Open the factory database on demand.
        connection.row_factory = sqlite3.Row  # Make query results clear and name-based.
        try:
            yield connection  # Let the caller run one compact transaction.
            connection.commit()  # Commit successful writes before closing the handle.
        finally:
            connection.close()  # Release the file handle so Windows tests can delete the database.

    def _document_values(self, document: DocumentRecord, issue_shape: str) -> tuple[Any, ...]:
        """Return the document upsert values."""
        return (  # Keep the SQL call compact and repeatable.
            document.document_key,
            str(document.source_path),
            document.title,
            document.category,
            document.page_count,
            document.domain,
            issue_shape,
        )

    def _event_values(self, event: StageEvent, comment_body: str) -> tuple[Any, ...]:
        """Return the stage event insert values."""
        return (  # Keep the SQLite insert small and deterministic.
            event.document_key,
            event.stage.value,
            event.next_action,
            event.issue_number,
            event.created_at,
            json.dumps(event.details, sort_keys=True),
            comment_body,
        )

    def _documents_schema(self) -> str:
        """Return the document table schema."""
        return """
            CREATE TABLE IF NOT EXISTS skill_documents (
                document_key TEXT PRIMARY KEY,
                source_path TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                page_count INTEGER NOT NULL,
                domain TEXT NOT NULL,
                issue_shape TEXT NOT NULL,
                issue_number INTEGER,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """

    def _events_schema(self) -> str:
        """Return the stage event table schema."""
        return """
            CREATE TABLE IF NOT EXISTS skill_stage_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_key TEXT NOT NULL,
                stage TEXT NOT NULL,
                next_action TEXT NOT NULL,
                issue_number INTEGER,
                created_at TEXT NOT NULL,
                details_json TEXT NOT NULL,
                comment_body TEXT NOT NULL,
                github_synced INTEGER NOT NULL DEFAULT 0
            )
        """
