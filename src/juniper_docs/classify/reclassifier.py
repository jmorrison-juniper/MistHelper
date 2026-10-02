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
import sqlite3  # Read the durable state database and write the updated rows.
from dataclasses import dataclass, field  # Group the run counters into one record.
from pathlib import Path  # Build every corpus path in a portable, Windows-safe way.

from src.juniper_docs.acquire.pdf_paths import PdfPathAllocator  # Shared path policy.
from src.juniper_docs.classify.content_sampler import DEFAULT_SAMPLE_PAGES, ContentSampler
from src.juniper_docs.classify.signal_scorer import CONFIDENCE_THRESHOLD, SignalScorer
from src.juniper_docs.classify.slug_classifier import UNCATEGORIZED  # The content bucket.
from src.juniper_docs.harvest.state_store import HarvestStateStore, StateStoreError
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
        self._store: HarvestStateStore | None = None

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
            if self._store is None:
                connection.close()
            else:
                self._store.close()
                self._store = None
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
            self._store = HarvestStateStore(self.db_path)
            connection = self._store._conn
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
        current = connection.execute("SELECT * FROM documents WHERE root_url = ?", (row["root_url"],)).fetchone()
        if current is None or current["local_path"] is None:
            raise StateStoreError("A reclassification source record has no current payload path.")
        local_path = Path(str(current["local_path"]))
        _LOGGER.info("Reclassifying %s", row["root_url"])  # Name the document under work.
        text = self.sampler.sample(local_path)  # Read a bounded, in-memory text sample.
        if not text.strip():  # A missing or unreadable file yields no text.
            _LOGGER.debug("No readable text for %s", row["root_url"])  # Record the miss.
            stats.unreadable += 1  # Count the unreadable document and leave it alone.
            stats.after_labels.add(stored_label)  # The label does not change for it.
            return  # An unreadable file never moves and never stops the pass.
        name = HarvestStateStore._original_name(str(row["resolved_pdf_url"]))
        result = self.scorer.score(text, name)
        self._record_outcome(current, result, stats)

    def _record_outcome(
        self,
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
            self._apply(row, result)

    def _apply(self, row: sqlite3.Row, result: ContentAnalysisResult) -> None:
        """Move the file into the new label folder and update the stored row."""
        if self._store is None:
            raise StateStoreError("A reclassification write requires the durable state store.")
        source = Path(str(row["local_path"]))
        resolved_url = str(row["resolved_pdf_url"])
        final_path = self._place(source, result.sub_category, resolved_url)
        try:
            self._store.reclassify_document(str(row["root_url"]), result, str(source), str(final_path))
        except (StateStoreError, sqlite3.DatabaseError, OSError):
            _LOGGER.exception("Cannot record the corpus reclassification")
            if (
                source != final_path
                and not source.exists()
                and final_path.exists()
                and not self._store.placement_is_recorded(str(final_path))
            ):
                final_path.replace(source)
            raise

    def _place(self, source: Path, label: str, resolved_url: str) -> Path:
        """Move one file into its new label folder without destroying a file."""
        if self._store is None:
            raise StateStoreError("A corpus placement requires the durable state store.")
        if self._store.path_is_shared(str(source)):
            _LOGGER.debug("Retained 1 shared canonical payload during reclassification")
            return source
        final_dir = self.output_dir / UNCATEGORIZED / self._sanitize(label)  # The label folder.
        final_dir.mkdir(parents=True, exist_ok=True)  # Ensure the new label folder exists.
        target = final_dir / source.name  # The preferred final path under the label.
        if source.resolve() == target.resolve():  # The file already sits at the final path.
            return target  # A repeated placement needs no move, so the file stays.
        allocator = PdfPathAllocator(self._store.owner_of_path)
        final, move = allocator.plan_file(target, resolved_url, source)  # Resolve a unique path.
        self._relocate(source, final, move)  # Move the file or drop a redundant duplicate.
        return final  # The caller records this real final path in the store.

    def _relocate(self, source: Path, final: Path, move: bool) -> None:
        """Move one unique payload without deleting an equal historical source."""
        if source.resolve() == final.resolve():
            return
        if move:
            _LOGGER.info("Placing %s at %s", source.name, final)  # Log before the move.
            source.replace(final)
            _LOGGER.debug("Placed the file at %s", final)  # Report the completed move.
        else:
            _LOGGER.debug("Retained an existing equal-content source during reclassification")

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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")  # Console log.
    CorpusReclassifier.from_args().run()  # Dry run by default; pass --apply for a real pass.
