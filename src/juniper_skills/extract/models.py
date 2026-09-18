"""Data models for exhaustive Juniper fact extraction."""

from __future__ import annotations  # Keep annotations cheap during factory imports.

from dataclasses import dataclass  # Define small immutable records for extraction.

from src.juniper_skills.rewrite import CardClassMark, KnowledgeCard  # Reuse the locked card contract.


@dataclass(frozen=True)
class SourceLine:
    """One source line with the exact page that produced it."""

    number: int  # Store the physical line number for deterministic sort order.
    page: int  # Store the source page from the nearest page marker.
    text: str  # Store the source line text for extractor scans.


@dataclass(frozen=True)
class ExtractedFact:
    """One candidate fact before cross-extractor deduplication."""

    fact_type: str  # Name the extractor class that produced the fact.
    mark: CardClassMark  # Store the MUST, SHOULD, or INFO card class.
    fact: str  # Store the publishable fact text.
    citation_key: str  # Store the exact source page citation.
    source_span: str  # Store a short internal span for dedup priority.

    def to_card(self) -> KnowledgeCard:
        """Return the existing rewrite card model for this fact."""
        return KnowledgeCard(self.mark, self.fact, self.citation_key)  # Preserve the shared card shape.


@dataclass(frozen=True)
class TopicSplit:
    """One rendered topic file part after size enforcement."""

    name: str  # Store the generated topic part name.
    content: str  # Store the Markdown body for this part.
    size_bytes: int  # Store the encoded size for the hard-limit report.


@dataclass(frozen=True)
class DepthExtractionResult:
    """The full report from one source document extraction."""

    cards: tuple[KnowledgeCard, ...]  # Store the deduplicated cards.
    raw_count: int  # Store the count before deduplication.
    merge_count: int  # Store how many candidate facts merged away.
    pages: tuple[int, ...]  # Store every page that produced at least one line.
    topics: tuple[TopicSplit, ...]  # Store rendered topic parts after size splitting.
    source_prose_chars: int  # Store the measurable source size.
    fact_type_counts: dict[str, int]  # Store deduplicated card counts by extractor fact class.

    @property
    def table_card_count(self) -> int:
        """Return the count of deduplicated table-derived cards."""
        return self.fact_type_counts.get("table-row", 0)  # Report table rows as the table-derived metric.

    @property
    def cards_per_page(self) -> float:
        """Return the average count of cards for each measured page."""
        if not self.pages:  # A damaged source with no pages cannot produce a ratio.
            return 0.0  # Return a safe zero for the report.
        return len(self.cards) / len(self.pages)  # Divide cards by precise page count.

    @property
    def retention_percent(self) -> float:
        """Return generated topic size as a percentage of source prose size."""
        if self.source_prose_chars <= 0:  # Avoid a division error for empty documents.
            return 0.0  # Return a safe zero for the report.
        retained = sum(topic.size_bytes for topic in self.topics)  # Measure generated Markdown bytes.
        return retained * 100.0 / self.source_prose_chars  # Report the retained content percentage.
