"""Cached similarity guard runner for depth extraction measurements."""

from __future__ import annotations  # Keep annotations cheap during factory imports.

import logging  # Record guard measurement actions for operators.
from pathlib import Path  # Keep generated file identities platform safe.

from src.juniper_skills.rewrite import (  # Reuse the locked copyright guard models.
    SimilarityFileResult,
    SimilarityGuardReport,
    VerbatimSimilarityGuard,
)


class CachedSourceSimilarityGuard:
    """Run the similarity guard when many topic parts share one source."""

    def __init__(self, guard: VerbatimSimilarityGuard | None = None) -> None:
        """Store the guard implementation that defines token rules."""
        self.guard = guard or VerbatimSimilarityGuard()  # Reuse the contract thresholds and token filters.

    def check_texts(self, generated: tuple[tuple[Path, str], ...], source_text: str) -> SimilarityGuardReport:
        """Return guard results for generated texts that share one source."""
        logging.info("Running cached-source similarity guard")  # Log before guard measurement.
        if not generated:  # A guard that measures no topic files must fail.
            return self.guard.check(tuple())  # Reuse the locked zero-file failure report.
        source_words = self.guard.prose_words(source_text)  # Normalize the shared source one time.
        results = tuple(self._check_one(path, text, source_words) for path, text in generated)  # Measure topics.
        report = SimilarityGuardReport(len(results), self.guard.threshold, self.guard.warn_threshold, results, 0.0)
        logging.debug("Cached-source guard checked %d generated texts", len(results))  # Log the measured count.
        return report  # Return the same report model as the base guard.

    def check_files(self, paths: tuple[Path, ...], source_text: str) -> SimilarityGuardReport:
        """Return guard results for generated files that share one source."""
        logging.info("Reading generated files for cached-source guard")  # Log before generated file input.
        generated = tuple((path, path.read_text(encoding="utf-8")) for path in paths)  # Read each topic file once.
        logging.debug("Read %d generated files for cached-source guard", len(generated))  # Log input count.
        return self.check_texts(generated, source_text)  # Measure the generated text values.

    def _check_one(self, path: Path, text: str, source_words: tuple[str, ...]) -> SimilarityFileResult:
        """Return the similarity result for one generated text."""
        generated_words = self.guard.prose_words(text)  # Normalize one generated topic with guard rules.
        longest, phrase = self.guard._longest_common_run(generated_words, source_words)  # Use the exact algorithm.
        status = self.guard._status(longest)  # Classify the run with the locked thresholds.
        passed = status != "failed"  # Only the hard band stops publication.
        return SimilarityFileResult(path, longest, phrase, status, passed)  # Return the shared result model.
