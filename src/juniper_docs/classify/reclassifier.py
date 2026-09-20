"""Reclassify the early uncategorized corpus documents from the files on disk.

The content classifier gained an absolute strength floor after about 620
documents were already classified. Those early documents carry noisy labels, so
they sit in the wrong folders. This module reads the durable state database,
finds every classified document in the uncategorized bucket, samples each local
PDF again, and scores it with the current rules.

When the new label differs from the stored label, the tool moves the file into
the folder for the new label and updates the stored label, the stored fallback
flag, the stored scores, and the stored local path. The tool reuses the shared
``PdfPathAllocator`` policy, so a move never overwrites a different document.

The dry run mode is the default, so an accidental run cannot damage the corpus.
The tool holds the sampled text in memory only. It never writes the body text
into the database, the manifest, a log line, or any file (FR-024, SC-005).
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import argparse  # Parse the operator command into the reclassifier configuration.
import logging  # Log every action before it runs and its result after it runs.
import re  # Replace each Windows-invalid character in a label folder name.
import shutil  # Move a reclassified file into its new label folder.
import sqlite3  # Read the durable state database and write the updated rows.
from dataclasses import dataclass, field  # Group the run counters into one record.
from datetime import UTC, datetime  # Stamp each updated row with a UTC timestamp.
from pathlib import Path  # Build every corpus path in a portable, Windows-safe way.

from src.juniper_docs.acquire.pdf_paths import PdfPathAllocator  # Shared path policy.
from src.juniper_docs.classify.content_sampler import DEFAULT_SAMPLE_PAGES, ContentSampler
from src.juniper_docs.classify.signal_scorer import CONFIDENCE_THRESHOLD, SignalScorer
from src.juniper_docs.classify.slug_classifier import UNCATEGORIZED  # The content bucket.
from src.juniper_docs.models import ContentAnalysisResult  # The derived label record.

_LOGGER = logging.getLogger(__name__)  # Module logger for the reclassifier.

DEFAULT_OUTPUT_DIR = Path("data/juniper_corpus")  # The corpus root under data/.
_STATE_DB_NAME = "harvest_state.db"  # The durable state database file name.
_CLASSIFIED_STAGE = "classified"  # The stage value of a fully classified document.
_INVALID_NAME = re.compile(r'[<>:"/\\|?*]')  # Characters invalid in a Windows folder name.

# Select every classified document in the uncategorized bucket that has a local
# file. Only the uncategorized bucket uses content analysis, so only this bucket
# needs a fresh label under the current rules.
_CANDIDATE_QUERY = (
    "SELECT root_url, resolved_pdf_url, category, sub_category, is_fallback, local_path "
    "FROM documents WHERE stage = ? AND category = ? AND local_path IS NOT NULL "
    "ORDER BY root_url"
)


@dataclass
class ReclassifyStats:
    """The running counts for one reclassification pass."""

    inspected: int = 0  # The count of documents that the pass read.
    changed: int = 0  # The count of documents whose label changed.
    unchanged: int = 0  # The count of documents whose label stayed the same.
    unreadable: int = 0  # The count of documents whose file yielded no text.
    before_labels: set[str] = field(default_factory=set)  # The distinct stored labels.
    after_labels: set[str] = field(default_factory=set)  # The distinct labels after the pass.

    @property
    def labels_before(self) -> int:
        """Return the count of distinct labels before the pass."""
        return len(self.before_labels)  # The size of the stored-label set.

    @property
    def labels_after(self) -> int:
        """Return the count of distinct labels after the pass."""
        return len(self.after_labels)  # The size of the post-pass label set.


class CorpusReclassifier:
    """Reclassify the early uncategorized documents from the files on disk."""

    def __init__(
        self,
        output_dir: Path,
        sampler: ContentSampler,
        scorer: SignalScorer,
        dry_run: bool = True,
    ) -> None:
        """Store the corpus root, the sampler, the scorer, and the dry run flag.

        Args:
            output_dir: The corpus root that holds the state database and folders.
            sampler: The shared bounded text sampler, reused not duplicated.
            scorer: The shared signal scorer, reused not duplicated.
            dry_run: True reports the changes and writes nothing, the safe default.
        """
        self.output_dir = output_dir  # The corpus root under data/.
        self.db_path = output_dir / _STATE_DB_NAME  # The durable state database path.
        self.sampler = sampler  # Read a bounded, in-memory text sample from one PDF.
        self.scorer = scorer  # Derive the current content sub-category label.
        self.dry_run = dry_run  # Write nothing when true, the safe default.

    def run(self) -> ReclassifyStats:
        """Reclassify every candidate document and return the run counts."""
        _LOGGER.info("Starting a reclassification pass, dry_run=%s", self.dry_run)  # Intent.
        stats = ReclassifyStats()  # Accumulate the counts for the summary.
        connection = self._connect()  # Open the store read-only or read-write.
        try:
            for row in self._candidates(connection):  # Walk every candidate document.
                self._inspect(connection, row, stats)  # Reclassify one document.
            if not self.dry_run:  # A real pass tidies the emptied label folders.
                self._remove_empty_label_dirs()  # Remove each folder left empty by a move.
        finally:
            connection.close()  # Always release the database file.
        self._log_summary(stats)  # Report the counts for the operator.
        return stats  # The caller reads the counts and the label sets.

    def _connect(self) -> sqlite3.Connection:
        """Return a read-only connection for a dry run, else a read-write one."""
        if self.dry_run:  # A dry run must not write, so open the file read-only.
            _LOGGER.info("Opening the state database read-only for a dry run")  # Intent.
            uri = f"{self.db_path.resolve().as_uri()}?mode=ro"  # The read-only file URI.
            connection = sqlite3.connect(uri, uri=True)  # A connection that rejects writes.
        else:  # A real pass writes the updated rows.
            _LOGGER.info("Opening the state database read-write for a real pass")  # Intent.
            connection = sqlite3.connect(str(self.db_path))  # A write-capable connection.
        connection.row_factory = sqlite3.Row  # Read each row by the column name.
        return connection  # The caller owns and closes the connection.

    def _candidates(self, connection: sqlite3.Connection) -> list[sqlite3.Row]:
        """Return every classified uncategorized document that has a local file."""
        _LOGGER.info("Selecting the classified uncategorized documents")  # Intent.
        rows = connection.execute(_CANDIDATE_QUERY, (_CLASSIFIED_STAGE, UNCATEGORIZED)).fetchall()
        _LOGGER.debug("Selected %d candidate documents", len(rows))  # Result count.
        return rows  # The pass reclassifies each of these documents.

    def _inspect(self, connection: sqlite3.Connection, row: sqlite3.Row, stats: ReclassifyStats) -> None:
        """Sample one document, score it, and record the outcome in the counts."""
        stats.inspected += 1  # Count this document as inspected.
        stored_label = str(row["sub_category"])  # The label the harvester stored earlier.
        stats.before_labels.add(stored_label)  # Track the distinct labels before the pass.
        local_path = Path(str(row["local_path"]))  # The file that the harvester saved.
        _LOGGER.info("Reclassifying %s", row["root_url"])  # Name the document under work.
        text = self.sampler.sample(local_path)  # Read a bounded, in-memory text sample.
        if not text.strip():  # A missing or unreadable file yields no text.
            _LOGGER.debug("No readable text for %s", row["root_url"])  # Record the miss.
            stats.unreadable += 1  # Count the unreadable document and leave it alone.
            stats.after_labels.add(stored_label)  # The label does not change for it.
            return  # An unreadable file never moves and never stops the pass.
        result = self.scorer.score(text, local_path.name)  # Derive the current label.
        self._record_outcome(connection, row, result, stats)  # Compare and act.

    def _record_outcome(
        self,
        connection: sqlite3.Connection,
        row: sqlite3.Row,
        result: ContentAnalysisResult,
        stats: ReclassifyStats,
    ) -> None:
        """Count the outcome and apply the change when the label differs."""
        stored_label = str(row["sub_category"])  # The label the harvester stored earlier.
        if result.sub_category == stored_label:  # The current rules keep the same label.
            _LOGGER.debug("Label unchanged for %s", row["root_url"])  # Record the match.
            stats.unchanged += 1  # Count the document as unchanged.
            stats.after_labels.add(stored_label)  # The label set keeps the stored label.
            return  # An unchanged document needs no move and no write.
        _LOGGER.info("Label changed for %s: %s to %s", row["root_url"], stored_label, result.sub_category)
        stats.changed += 1  # Count the document as changed.
        stats.after_labels.add(result.sub_category)  # Track the new label after the pass.
        if not self.dry_run:  # A dry run reports the change and writes nothing.
            self._apply(connection, row, result)  # Move the file and update the row.

    def _apply(self, connection: sqlite3.Connection, row: sqlite3.Row, result: ContentAnalysisResult) -> None:
        """Move the file into the new label folder and update the stored row."""
        source = Path(str(row["local_path"]))  # The file in its current label folder.
        resolved_url = str(row["resolved_pdf_url"])  # The URL that identifies this document.
        final_path = self._place(connection, source, result.sub_category, resolved_url)  # Move it.
        self._update_row(connection, str(row["root_url"]), result, final_path)  # Persist it.

    def _place(self, connection: sqlite3.Connection, source: Path, label: str, resolved_url: str) -> Path:
        """Move one file into its new label folder without destroying a file."""
        final_dir = self.output_dir / UNCATEGORIZED / self._sanitize(label)  # The label folder.
        final_dir.mkdir(parents=True, exist_ok=True)  # Ensure the new label folder exists.
        target = final_dir / source.name  # The preferred final path under the label.
        if source.resolve() == target.resolve():  # The file already sits at the final path.
            return target  # A repeated placement needs no move, so the file stays.
        allocator = PdfPathAllocator(lambda path: self._owner_of(connection, path))  # Shared policy.
        final, move = allocator.plan_file(target, resolved_url, source)  # Resolve a unique path.
        self._relocate(source, final, move)  # Move the file or drop a redundant duplicate.
        return final  # The caller records this real final path in the store.

    def _relocate(self, source: Path, final: Path, move: bool) -> None:
        """Move the file to the final path, or drop it when a copy exists."""
        if move:  # The final path is free, so this is a distinct document.
            _LOGGER.info("Placing %s at %s", source.name, final)  # Log before the move.
            shutil.move(str(source), str(final))  # Move the file into the unique label path.
            _LOGGER.debug("Placed the file at %s", final)  # Report the completed move.
            return  # The distinct document now lives at its own path.
        _LOGGER.info("Dropping the redundant duplicate %s", source.name)  # Log before the delete.
        source.unlink()  # Remove the redundant download, so one stored file remains.
        _LOGGER.debug("Dropped the redundant duplicate of %s", final.name)  # One file remains.

    def _update_row(
        self,
        connection: sqlite3.Connection,
        root_url: str,
        result: ContentAnalysisResult,
        final_path: Path,
    ) -> None:
        """Update the label, the fallback flag, the local path, and the scores."""
        _LOGGER.info("Updating the stored label for %s", root_url)  # Log before the write.
        with connection:  # One atomic transaction commits every write together.
            connection.execute(
                "UPDATE documents SET sub_category = ?, is_fallback = ?, local_path = ?, "
                "updated_at = ? WHERE root_url = ?",
                (result.sub_category, int(result.is_fallback), str(final_path), _now(), root_url),
            )
            connection.execute("DELETE FROM content_scores WHERE root_url = ?", (root_url,))
            connection.executemany(
                "INSERT INTO content_scores (root_url, signal_group, signal_name, score) VALUES (?, ?, ?, ?)",
                self._score_rows(root_url, result),
            )
        _LOGGER.debug("Updated the stored label to %s", result.sub_category)  # Report the result.

    def _remove_empty_label_dirs(self) -> None:
        """Remove each label folder that a move left empty."""
        base = self.output_dir / UNCATEGORIZED  # The parent of every label folder.
        if not base.exists():  # No uncategorized tree means no folder to remove.
            return  # There is nothing to tidy.
        _LOGGER.info("Removing the label folders left empty by the moves")  # Intent.
        for child in sorted(base.iterdir()):  # Walk each label folder in a stable order.
            if child.is_dir() and not any(child.iterdir()):  # An empty label folder remains.
                _LOGGER.debug("Removing the empty label folder %s", child.name)  # Name it.
                child.rmdir()  # Remove the empty folder, which never removes a file.

    def _log_summary(self, stats: ReclassifyStats) -> None:
        """Report the counts and the distinct label counts for the operator."""
        mode = "dry-run" if self.dry_run else "apply"  # Name the mode in the summary.
        _LOGGER.info(
            "Reclassify %s summary: inspected=%d changed=%d unchanged=%d unreadable=%d "
            "labels_before=%d labels_after=%d",
            mode,
            stats.inspected,
            stats.changed,
            stats.unchanged,
            stats.unreadable,
            stats.labels_before,
            stats.labels_after,
        )

    @staticmethod
    def _owner_of(connection: sqlite3.Connection, local_path: str) -> str | None:
        """Return the resolved PDF URL that owns a stored local path, or None."""
        row = connection.execute(
            "SELECT resolved_pdf_url FROM documents WHERE local_path = ? LIMIT 1", (local_path,)
        ).fetchone()  # The single document row that already claims this exact path.
        if row is None or row["resolved_pdf_url"] is None:  # No row, or no resolved URL yet.
            return None  # An unknown path has no recorded owner.
        return str(row["resolved_pdf_url"])  # The resolved URL that produced the stored file.

    @staticmethod
    def _score_rows(root_url: str, result: ContentAnalysisResult) -> list[tuple[str, str, str, float]]:
        """Return the numeric score rows, which hold no body text."""
        rows: list[tuple[str, str, str, float]] = []  # The root, group, name, and score tuples.
        for key, score in result.scores.items():  # Split each group-and-name key in turn.
            group, name = key.split(":", 1)  # The key joins the group and the signal name.
            rows.append((root_url, group, name, score))  # Add one numeric row per signal.
        return rows  # The store records these numeric scores, never any body text.

    @staticmethod
    def _sanitize(name: str) -> str:
        """Return a Windows-safe folder name for one label."""
        cleaned = _INVALID_NAME.sub("-", name)  # Replace each invalid character.
        cleaned = cleaned.strip(" .")  # Trim a trailing dot or space.
        return cleaned or "unnamed"  # Never return an empty folder name.

    @classmethod
    def from_args(cls, argv: list[str] | None = None) -> CorpusReclassifier:
        """Build the reclassifier from the operator command arguments."""
        args = cls._parser().parse_args(argv)  # Parse the arguments with safe defaults.
        sampler = ContentSampler(args.max_sample_pages)  # The shared bounded sampler.
        scorer = SignalScorer(args.confidence_threshold)  # The shared signal scorer.
        return cls(Path(args.output_dir), sampler, scorer, dry_run=not args.apply)  # Configured.

    @staticmethod
    def _parser() -> argparse.ArgumentParser:
        """Return the argument parser for the operator command."""
        parser = argparse.ArgumentParser(description="Reclassify the early uncategorized corpus documents.")
        parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="The corpus root.")
        parser.add_argument("--apply", action="store_true", help="Write the changes; omit for a dry run.")
        parser.add_argument("--max-sample-pages", type=int, default=DEFAULT_SAMPLE_PAGES, help="Sample cap.")
        parser.add_argument("--confidence-threshold", type=float, default=CONFIDENCE_THRESHOLD, help="Floor.")
        return parser  # The caller parses the process arguments.


def _now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(UTC).isoformat()  # A stable, sortable timestamp for updated_at.


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")  # Console log.
    CorpusReclassifier.from_args().run()  # Dry run by default; pass --apply for a real pass.
