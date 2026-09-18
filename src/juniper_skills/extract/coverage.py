"""Coverage manifest analyzer for Juniper source regions."""

from __future__ import annotations  # Keep annotations cheap during factory imports.

import logging  # Record analyzer work for factory operators.
import re  # Find commands, filters, parameters, and checklist terms.

from .extractors import (  # Reuse the structured extractors that find real source facts.
    CommandFactExtractor,
    ConfigurationFactExtractor,
    NumericFactExtractor,
    PlatformReleaseFactExtractor,
    TableRowFactExtractor,
)
from .models import CoverageEntry, CoverageManifest, CoverageVerificationReport, SourceLine  # Share models.
from .parser import SourcePageParser  # Attach page citations before checklist extraction.


class CoverageAnalyzer:
    """Create a checklist of source facts that a writer must cover."""

    def __init__(self) -> None:
        """Create extractor dependencies for manifest analysis."""
        self.parser = SourcePageParser()  # Parse exact page markers before extraction.
        self.command_extractor = CommandFactExtractor()  # Reuse validated command detection.
        self.config_extractor = ConfigurationFactExtractor()  # Reuse validated configuration detection.
        self.numeric_extractor = NumericFactExtractor()  # Reuse anchored numeric detection.
        self.table_extractor = TableRowFactExtractor()  # Reuse table row detection.
        self.qualifier_extractor = PlatformReleaseFactExtractor()  # Reuse scope detection.

    def analyze_text(self, text: str, source_key: str, topic: str | None = None) -> CoverageManifest:
        """Return a deduplicated coverage manifest for one source region."""
        logging.info("Building coverage manifest for %s", source_key)  # Log before analysis.
        lines = self.parser.parse(text)  # Attach citations to all source lines.
        entries = self._entries(lines, source_key)  # Extract all checklist classes.
        useful_entries = tuple(entry for entry in entries if self._useful_entry(entry))  # Drop noise entries.
        kept, merges = self._deduplicate(useful_entries)  # Merge repeated checklist items.
        manifest = CoverageManifest(topic or self._topic(lines), self._region(lines), kept, merges)  # Build report.
        logging.debug("Coverage manifest has %d entries after %d merges", len(kept), merges)  # Log counts.
        return manifest  # Return the checklist for writer and verifier stages.

    def verify(self, manifest: CoverageManifest, topic_text: str) -> CoverageVerificationReport:
        """Return the share of manifest entries covered by a finished topic."""
        logging.info("Verifying topic coverage against a manifest")  # Log before verification.
        covered = tuple(entry for entry in manifest.entries if self._covered(entry, topic_text))  # Find matches.
        missing = tuple(entry for entry in manifest.entries if entry not in covered)  # Keep uncovered facts.
        logging.debug("Coverage verifier found %d of %d entries", len(covered), len(manifest.entries))  # Log result.
        return CoverageVerificationReport(len(manifest.entries), len(covered), missing)  # Return coverage report.

    def _entries(self, lines: tuple[SourceLine, ...], source_key: str) -> tuple[CoverageEntry, ...]:
        """Return all manifest entries before deduplication."""
        entries: list[CoverageEntry] = []  # Collect checklist items by category.
        entries.extend(self._command_entries(lines, source_key))  # Add commands that must stay exact.
        entries.extend(self._pipe_filter_entries(lines, source_key))  # Add pipe filters that often get missed.
        entries.extend(self._fact_entries("configuration statements", self.config_extractor.extract(lines, source_key)))
        entries.extend(self._fact_entries("numeric limits", self.numeric_extractor.extract(lines, source_key)))
        entries.extend(self._fact_entries("table rows", self.table_extractor.extract(lines, source_key)))
        entries.extend(self._caveat_entries(lines, source_key))  # Add restrictions and failure modes.
        entries.extend(self._fact_entries("platform qualifiers", self.qualifier_extractor.extract(lines, source_key)))
        return tuple(entries)  # Return entries in deterministic order.

    def _command_entries(self, lines: tuple[SourceLine, ...], source_key: str) -> list[CoverageEntry]:
        """Return command checklist entries."""
        entries: list[CoverageEntry] = []  # Collect commands in source order.
        for line in lines:  # Scan every cited source line.
            command = self.command_extractor._command(line.text)  # Reuse the strict command parser.
            if command:  # Only real command lines belong in this manifest section.
                entries.append(self._entry("commands found", command, line, source_key))  # Add exact command.
        return entries  # Return command entries.

    def _pipe_filter_entries(self, lines: tuple[SourceLine, ...], source_key: str) -> list[CoverageEntry]:
        """Return pipe filter checklist entries."""
        entries: list[CoverageEntry] = []  # Collect named pipe filters.
        for line in lines:  # Scan every cited source line for filters.
            for filter_name in self._pipe_filters(line.text):  # Extract each filter after a pipe.
                entries.append(self._entry("pipe filters named", filter_name, line, source_key))  # Add filter.
        return entries  # Return filter entries.

    def _pipe_filters(self, text: str) -> tuple[str, ...]:
        """Return pipe filters named in one line."""
        matches = re.findall(r"\|\s*([a-z][a-z0-9-]*(?:\s+\d+)?)", text, re.IGNORECASE)  # Find pipe filters.
        prose = re.findall(r"\b(append|count|display|except|find|hold|last|match|no-more|refresh)\b", text)  # Find.
        return tuple(dict.fromkeys((*matches, *prose)))  # Merge exact filters without duplicates.

    def _fact_entries(self, category: str, facts) -> list[CoverageEntry]:
        """Return manifest entries from structured extractor facts."""
        entries: list[CoverageEntry] = []  # Collect normalized fact values.
        for fact in facts:  # Convert each fact into a checklist item.
            value = self._value_from_fact(category, fact.fact, fact.source_span)  # Prefer exact source structures.
            entries.append(CoverageEntry(category, value, fact.citation_key))  # Keep extractor citation.
        return entries  # Return manifest entries for this category.

    def _value_from_fact(self, category: str, fact_text: str, source_span: str) -> str:
        """Return a compact manifest value from an extractor fact."""
        if category == "table rows":  # Table rows are structured source data.
            return self._table_value(source_span)  # Keep the row anchor instead of only the table title.
        match = re.search(r"`([^`]+)`", fact_text)  # Prefer the first protected verbatim value.
        if match:  # Most structured facts keep their anchor in code spans.
            return match.group(1)  # Return the exact anchor value.
        return self._short_value(source_span)  # Return a safe short value for narrative facts.

    def _table_value(self, source_span: str) -> str:
        """Return a useful table-row checklist value."""
        compact = re.sub(r"\s+", " ", source_span).strip()  # Normalize broken PDF row spacing.
        return compact[:160]  # Keep a bounded row value for readable manifests.

    def _caveat_entries(self, lines: tuple[SourceLine, ...], source_key: str) -> list[CoverageEntry]:
        """Return caveat and ordering checklist entries."""
        entries: list[CoverageEntry] = []  # Collect useful caveat entries.
        for line in lines:  # Scan each cited source line for rule language.
            value = self._caveat_value(line.text)  # Extract the part near the rule signal.
            if value:  # Empty values are headings or weak fragments.
                entries.append(self._entry("caveats", value, line, source_key))  # Add the useful caveat.
        return entries  # Return caveats for the manifest.

    def _caveat_value(self, text: str) -> str:
        """Return a useful caveat value from one source line."""
        if text.strip().startswith("#"):  # Headings are not caveat facts.
            return ""  # Return no caveat for heading text.
        pattern = r"\b(must|cannot|do not|only|requires|required|before|after|fails|failure|Ctrl-C)\b"
        match = re.search(pattern, text, re.IGNORECASE)  # Find strong rule or failure language.
        if not match:  # Lines without a signal are not caveats.
            return ""  # Return no caveat value.
        return self._near_signal(text, match.start())  # Return text around the caveat signal.

    def _near_signal(self, text: str, position: int) -> str:
        """Return a short phrase around a caveat signal."""
        before = text[:position].split()[-2:]  # Keep limited leading context.
        after = text[position:].split()[:5]  # Keep the signal and its immediate effect.
        return self._short_value(" ".join((*before, *after)))  # Keep the manifest phrase copyright safe.

    def _entry(self, category: str, value: str, line: SourceLine, source_key: str) -> CoverageEntry:
        """Return one cited coverage entry."""
        citation = f"[{source_key} p.{line.page}]"  # Build the exact page citation.
        return CoverageEntry(category, value.strip(), citation)  # Return a manifest checklist item.

    def _deduplicate(self, entries: tuple[CoverageEntry, ...]) -> tuple[tuple[CoverageEntry, ...], int]:
        """Return deduplicated manifest entries and the merge count."""
        logging.info("Deduplicating coverage manifest entries")  # Log before manifest merging.
        kept: dict[str, CoverageEntry] = {}  # Store one item for each normalized checklist key.
        for entry in entries:  # Walk each candidate entry once.
            kept.setdefault(self._key(entry), entry)  # Keep the first citation for repeated items.
        logging.debug("Merged %d coverage manifest entries", len(entries) - len(kept))  # Log merge count.
        return tuple(kept.values()), len(entries) - len(kept)  # Return entries and merge count.

    def _key(self, entry: CoverageEntry) -> str:
        """Return a normalized key for one coverage entry."""
        normalized = re.sub(r"\s+", " ", entry.value.lower()).strip()  # Fold whitespace and case.
        return f"{entry.category}:{normalized}"  # Keep categories separate for coverage reports.

    def _useful_entry(self, entry: CoverageEntry) -> bool:
        """Return whether an entry is useful for a NOC engineer."""
        if entry.category in {"pipe filters named", "platform qualifiers"}:  # Single names are valid here.
            return bool(entry.value.strip())  # Keep named filters and qualifiers.
        tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9._/-]*", entry.value)  # Count meaningful tokens.
        return len(tokens) >= 2  # Drop bare fragments and single numbers.

    def _covered(self, entry: CoverageEntry, topic_text: str) -> bool:
        """Return whether the finished topic covers one manifest entry."""
        normalized_topic = topic_text.lower()  # Compare without case noise.
        tokens = [token for token in re.findall(r"[a-z0-9][a-z0-9._/-]*", entry.value.lower()) if len(token) > 2]
        if entry.value.lower() in normalized_topic:  # Exact structured values prove coverage.
            return True  # Accept exact matches first.
        return bool(tokens) and all(token in normalized_topic for token in tokens[:4])  # Accept anchored restatement.

    def _short_value(self, text: str) -> str:
        """Return a short, useful value for prose-derived checklist items."""
        words = re.findall(r"[A-Za-z][A-Za-z0-9._/-]*", text)  # Keep stable technical tokens.
        return " ".join(words[:7])  # Stay below the guard clear band for manifest prose.

    def _topic(self, lines: tuple[SourceLine, ...]) -> str:
        """Return the nearest heading as the manifest topic."""
        for line in lines:  # Search from the beginning for a section title.
            if line.text.strip().startswith("#"):  # A Markdown heading names the source region.
                return line.text.strip("# ").strip()  # Remove Markdown marks from the topic.
        return "Untitled source region"  # Return a safe fallback topic.

    def _region(self, lines: tuple[SourceLine, ...]) -> str:
        """Return the page range covered by the manifest."""
        pages = sorted({line.page for line in lines})  # Collect cited pages in ascending order.
        if not pages:  # Empty input has no cited page range.
            return "p.unknown"  # Return a clear fallback value.
        return f"p.{pages[0]}-{pages[-1]}"  # Return the exact covered page span.
