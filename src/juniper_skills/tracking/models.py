"""Data shapes for the Juniper skill factory GitHub journal."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class StageName(StrEnum):
    """Known stages that a document moves through."""

    QUEUED = "queued"
    SEGMENTED = "segmented"
    REWRITTEN = "rewritten"
    GUARDED = "guarded"
    BUILT = "built"
    INSTALLED = "installed"
    VERIFIED = "verified"
    FAILED = "failed"


STAGE_ORDER: tuple[StageName, ...] = (  # Keep the resume order stable after a crash.
    StageName.QUEUED,
    StageName.SEGMENTED,
    StageName.REWRITTEN,
    StageName.GUARDED,
    StageName.BUILT,
    StageName.INSTALLED,
    StageName.VERIFIED,
)


@dataclass(frozen=True)
class DocumentRecord:
    """Source document metadata that identifies one factory work item."""

    source_path: Path
    title: str
    category: str
    page_count: int
    domain: str

    @property
    def document_key(self) -> str:
        """Return a stable key that does not expose local path details in logs."""
        normalized_path = self.source_path.as_posix().lower()  # Normalize the path for repeatable keys on Windows.
        safe_chars = [char if char.isalnum() else "-" for char in normalized_path]  # Keep the key URL-safe.
        return "".join(safe_chars).strip("-")[:160]  # Bound the key so SQLite and GitHub titles stay small.


@dataclass(frozen=True)
class StageEvent:
    """One journal event for a document stage."""

    document_key: str
    stage: StageName
    next_action: str
    issue_number: int | None
    created_at: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResumePoint:
    """The exact point where the factory can continue after a crash."""

    document_key: str
    completed_stage: StageName | None
    next_action: str
    issue_number: int | None
    source: str
    failed: bool = False
