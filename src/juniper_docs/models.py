"""Shared dataclasses and enumerations for the harvester.

This module defines the durable stage enum, the document type enum, and the
data-transfer objects that flow between the discovery, acquire, classify, and
harvest layers. The ``ContentAnalysisResult`` holds no body text by design, so
the privacy invariant is structural (FR-024, SC-005).
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

from dataclasses import dataclass, field  # Build small, typed data-transfer objects.
from enum import StrEnum  # Give the stage and the document type a string value set.


class HarvestStage(StrEnum):
    """The stage of one document in the durable store."""

    DISCOVERED = "discovered"  # The document is in the inventory, no PDF resolved yet.
    RESOLVED = "resolved"  # The companion PDF URL is known.
    DOWNLOADED = "downloaded"  # The PDF file is on disk and starts with the marker.
    CLASSIFIED = "classified"  # The document has a category and, when needed, a label.
    FAILED = "failed"  # A per-document error stopped this document, with a reason.
    DROPPED = "dropped"  # A superseded release note, with a recorded reason.
    NO_PDF = "no_pdf"  # The document has no companion PDF, a clean, expected outcome.


class ResolveOutcome(StrEnum):
    """The outcome of one companion PDF resolution."""

    RESOLVED = "resolved"  # A companion PDF URL was chosen.
    NO_PDF = "no_pdf"  # A live page was reached, but it named no PDF.
    FAILED = "failed"  # No live page was reached, a real resolution failure.


class DocumentType(StrEnum):
    """The kind of one inventory document."""

    HTML_ROOT = "html_root"  # An HTML document root that owns one companion PDF.
    DIRECT_PDF = "direct_pdf"  # A sitemap entry that already names a PDF file.


@dataclass(frozen=True, slots=True)
class InventoryRecord:
    """One document in the plan, before any download."""

    source_url: str  # The absolute document root URL, unique in the inventory.
    root_slug: str  # The normalized document root path used for classification.
    doc_type: DocumentType  # Whether the document is an HTML root or a direct PDF.


@dataclass(frozen=True, slots=True)
class PdfCandidate:
    """One PDF reference found during companion resolution."""

    url: str  # The absolute PDF URL of this candidate.
    chosen: bool  # True for the selected companion PDF, false for a rejected one.
    reason: str  # The selection or rejection reason for the audit trail.


@dataclass(frozen=True, slots=True)
class ContentAnalysisResult:
    """The derived metadata for one uncategorized document.

    This record holds no field for the extracted body text. The sampler returns
    the text as a local string, the scorer reads it, and the string then goes
    out of scope (FR-024, SC-005).
    """

    sub_category: str  # The human-readable label or the fixed fallback label.
    detected_signals: tuple[str, ...]  # The signal names that scored above zero.
    scores: dict[str, float]  # A map from signal name to a numeric score.
    is_fallback: bool  # True when no signal reached the threshold or no text read.


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    """The joined view of one document for the manifest render."""

    source_url: str  # The document root URL from the inventory.
    resolved_pdf_url: str | None  # The chosen companion PDF URL, or null.
    category: str  # One of the slug categories or the uncategorized bucket.
    sub_category: str | None  # The content label, present only when uncategorized.
    local_path: str | None  # The saved file path, or null until downloaded.
    file_size: int | None  # The byte count, or null until downloaded.
    status: HarvestStage  # The final stage of the document.
    chosen_pdf: str | None  # The selected companion PDF URL for the audit trail.
    rejected_candidates: list[str] = field(default_factory=list)  # Rejected PDF URLs.
    drop_reason: str | None = None  # The reason a release note was dropped, or null.
    error_reason: str | None = None  # The failure or no-PDF reason, or null.
