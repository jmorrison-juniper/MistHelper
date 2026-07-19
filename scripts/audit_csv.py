"""Audit mist_ideas.csv for data quality issues.

Refs issue #433 phase D (critical CC hotspots). The original ``audit``
function had cyclomatic complexity 30 because it inlined seven emptiness
metrics, a per-row slug-vs-title comparison loop, and a status-sampling
block. This rewrite splits the work across a :class:`CsvAuditor` class so
every method stays under the agents.md 5-block / 5-deep complexity limit
while preserving the same printed output for downstream tooling.
"""

from __future__ import annotations  # PEP 604 unions on Python 3.10+ codebases.

import csv  # Standard library CSV reader for the input file.
import re  # Regex needed to extract the slug fragment from each idea URL.
from collections.abc import Iterable  # Type alias for row iterables passed to helpers.
from typing import Any  # Generic value type for the row-dict payloads.

EXAMPLES_LIMIT = 8  # Maximum number of mismatch examples shown to keep output readable.
EXAMPLE_FIELD_WIDTH = 70  # Truncation width for slug/title preview strings.
STATUS_SAMPLES_LIMIT = 5  # Maximum number of status values printed in the sample section.
STATUS_SAMPLE_WIDTH = 80  # Truncation width for individual status sample strings.


class CsvAuditor:  # Public class exposing the audit workflow.
    """Inspect a single mist_ideas.csv export for completeness and slug drift."""

    def __init__(self, path: str = "data/mist_ideas.csv") -> None:  # Store CSV path for run().
        """Remember which CSV will be audited when :meth:`run` is called."""
        self._path = path  # Path stored on the instance so methods can re-open as needed.

    def run(self) -> None:  # Public entry point that calls each report block.
        """Top-level audit entry point that delegates to focused helpers."""
        rows = self._load_rows()  # Pull all rows up-front to drive every report below.
        total = len(rows)  # Cache for percentage math reused across helpers.
        print(f"Total rows: {total}")  # Match original output exactly.
        self._print_field_emptiness(rows, total)  # Empty-field stats block.
        self._print_slug_mismatch(rows)  # Slug-vs-title comparison block.
        self._print_status_samples(rows)  # Status-value sampling block.

    def _load_rows(self) -> list[dict[str, Any]]:  # Read all rows once from disk.
        """Read the CSV and return all rows as plain dictionaries."""
        with open(self._path, encoding="utf-8-sig") as handle:  # UTF-8 BOM tolerated.
            return list(csv.DictReader(handle))  # Materialize so we can iterate multiple times.

    def _print_field_emptiness(
        self, rows: Iterable[dict[str, Any]], total: int
    ) -> None:  # Print empty-field stats block.
        """Print emptiness percentages for every field we care about."""
        rows = list(rows)  # Local copy lets us iterate seven times without consuming a generator.
        stats = self._compute_field_emptiness(rows)  # Single pass returns dict of counts.
        for label, count in stats.items():  # Iterate once over the pre-computed counts.
            pct = (100 * count / total) if total else 0.0  # Guard against division by zero.
            print(f"{label:<18} {count} ({pct:.1f}%)")  # Aligned column for readability.
        print()  # Trailing blank line matches the original output spacing.

    @staticmethod
    def _compute_field_emptiness(rows: list[dict[str, Any]]) -> dict[str, int]:  # Return per-label empty counts.
        """Return a stable-ordered dict mapping label -> count of "empty" rows."""
        empty = CsvAuditor._count_empty_field  # Short alias keeps the dict literal readable.
        non_zero_count = CsvAuditor._count_non_zero_int_field  # Same idea for the int comparator.
        votes_zero = sum(1 for row in rows if row.get("votes", "0") == "0")  # Pre-compute literal-compare branch.
        return {  # Keys preserved in insertion order to mirror the original printout.
            "Empty title:": empty(rows, "title"),
            "Empty description:": empty(rows, "description_full"),
            "Zero votes:": votes_zero,
            "Has comments:": non_zero_count(rows, "comments_count"),
            "Empty status:": empty(rows, "status"),
            "Empty submitter:": empty(rows, "submitter"),
            "Empty category:": empty(rows, "category"),
        }

    @staticmethod
    def _count_empty_field(rows: list[dict[str, Any]], field: str) -> int:  # Count blank/missing values.
        """Return the number of rows where ``field`` is missing or whitespace."""
        return sum(1 for row in rows if not row.get(field, "").strip())  # Single-branch sum-comprehension.

    @staticmethod
    def _count_non_zero_int_field(rows: list[dict[str, Any]], field: str) -> int:  # Count parses > 0.
        """Return the number of rows where ``field`` parses to a non-zero int."""
        return sum(1 for row in rows if int(row.get(field, "0")) > 0)  # Single-branch sum-comprehension.

    def _print_slug_mismatch(self, rows: Iterable[dict[str, Any]]) -> None:  # Print slug/title compare block.
        """Compare each row's URL-slug first word to its title's first word."""
        matches, mismatches, examples = 0, 0, []  # Counters + bounded examples list.
        for row in rows:  # One pass over the full row set.
            outcome = self._compare_row_slug(row)  # None when not comparable.
            if outcome is None:  # Skip incomparable rows.
                continue  # Skip rows missing url, title, or slug match.
            if outcome["match"]:  # Slug first-word matched title first-word.
                matches += 1  # Slug/title first-word aligned.
            else:  # First words differ.
                mismatches += 1  # Track drift for the summary line.
                if len(examples) < EXAMPLES_LIMIT:  # Cap stored examples for output brevity.
                    examples.append(outcome["example"])  # Pre-built by the comparer.
        self._print_slug_summary(matches, mismatches)  # Header lines + mismatch totals.
        self._print_slug_examples(examples)  # Optional examples block.

    @staticmethod
    def _compare_row_slug(row: dict[str, Any]) -> dict[str, Any] | None:
        """Compare a single row's url-slug first word vs title first word."""
        url = row.get("url", "")  # Missing url -> we cannot extract a slug.
        title = row.get("title", "").lower().strip()  # Lowercased for case-insensitive compare.
        slug = CsvAuditor._extract_slug(url)  # None when URL has no recognizable slug fragment.
        if slug is None or not title:
            return None  # No comparison possible without both pieces.
        slug_first = CsvAuditor._first_word(slug)  # First slug word, "" when empty.
        title_first = CsvAuditor._first_word(title)  # First title word, "" when empty.
        if not slug_first or not title_first:
            return None  # Either side empty -> skip this row entirely.
        is_match = slug_first == title_first  # Cheap exact first-word compare drives the outcome.
        example = {  # Built unconditionally so caller can stash it when needed.
            "idea_id": row.get("idea_id", ""),
            "url_slug": slug[:EXAMPLE_FIELD_WIDTH],
            "title": title[:EXAMPLE_FIELD_WIDTH],
            "desc_len": len(row.get("description_full", "").strip()),
        }
        return {"match": is_match, "example": example}  # Caller picks fields based on match flag.

    @staticmethod
    def _extract_slug(url: str) -> str | None:
        """Extract and normalize the slug fragment from an ideas URL."""
        # WHY: pulling regex + normalization out of _compare_row_slug drops that method's CC from 7 to 5.
        match = re.search(r"/suggestions/\d+-(.+?)$", url)  # Pull the slug fragment from the URL.
        if not match:
            return None  # URL has no recognizable slug.
        return match.group(1).replace("-", " ").lower()  # Normalize slug to space-separated words.

    @staticmethod
    def _first_word(text: str) -> str:
        """Return the first whitespace-split word, or empty string when text is blank."""
        # WHY: extracted so _compare_row_slug doesn't carry two ternary short-circuits.
        words = text.split()  # Whitespace-split preserves the original semantics.
        return words[0] if words else ""  # Guard empty-string case cleanly.

    @staticmethod
    def _print_slug_summary(matches: int, mismatches: int) -> None:
        """Print the slug match/mismatch counts + percentage."""
        print(f"Title matches URL slug: {matches}")  # Match the original output format.
        print(f"Title MISMATCHES slug:  {mismatches}")  # Same casing as the original.
        denom = matches + mismatches  # Cache so the percentage line stays readable.
        rate = (100 * mismatches / denom) if denom else 0.0  # Guard against division by zero.
        print(f"Mismatch rate: {rate:.1f}%")  # Trailing newline matches the original.
        print()

    @staticmethod
    def _print_slug_examples(examples: list[dict[str, Any]]) -> None:
        """Print the per-row mismatch examples when any were collected."""
        if not examples:
            return  # No examples -> nothing to print, matches the original guard.
        print("=== TITLE/SLUG MISMATCH EXAMPLES ===")  # Section header.
        for example in examples:  # One block per example.
            print(f"  idea_id: {example['idea_id']}")  # idea_id helps the user find the row.
            print(f"  slug:    {example['url_slug']}")  # Truncated slug preview.
            print(f"  title:   {example['title']}")  # Truncated title preview.
            print(f"  desc_len: {example['desc_len']}")  # Description length for context.
            print()  # Blank line between examples.

    @staticmethod
    def _print_status_samples(rows: Iterable[dict[str, Any]]) -> None:
        """Print up to a few sample status values when any are populated."""
        non_empty = [row.get("status", "").strip() for row in rows if row.get("status", "").strip()]
        if not non_empty:
            return  # No status values populated -> nothing to print.
        print("=== STATUS VALUES (first 5 non-empty, truncated) ===")  # Section header.
        for status in non_empty[:STATUS_SAMPLES_LIMIT]:  # Iterate the bounded slice.
            print(f"  [{status[:STATUS_SAMPLE_WIDTH]}]")  # Truncated to keep lines short.
        print()  # Trailing newline matches the original output.


def audit() -> None:
    """Module-level entry point preserved for backwards compatibility."""
    CsvAuditor().run()  # Instantiate the auditor with default path and run it.


if __name__ == "__main__":
    audit()  # Allow ``python -m scripts.audit_csv`` to keep working unchanged.
