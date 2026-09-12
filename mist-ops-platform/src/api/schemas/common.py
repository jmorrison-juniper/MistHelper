"""Common Pydantic schemas shared across all API routes (T023).

Includes ``ResponseEnvelope``, ``ErrorDetail``, ``PaginationMeta``,
and ``ConfirmBody`` used by destructive operations.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Standard error payload."""

    code: str
    message: str
    detail: str | None = None


class PaginationMeta(BaseModel):
    """Pagination metadata returned in list responses."""

    total: int
    page: int = 1
    page_size: int = 50
    has_next: bool = False


class ResponseEnvelope(BaseModel, Generic[T]):
    """Uniform API response wrapper."""

    data: T
    meta: PaginationMeta | None = None
    errors: list[ErrorDetail] | None = None


class ConfirmBody(BaseModel):
    """Destructive operations require ``confirm: true`` (Principle III)."""

    confirm: bool = Field(
        default=False,
        description="Must be true to execute destructive operations",
    )


class OrgScopeParams(BaseModel):
    """Common org-scoping query parameters."""

    org_id: UUID


class IdResponse(BaseModel):
    """Returned after resource creation."""

    id: UUID


class BulkActionResult(BaseModel):
    """Summary of a bulk operation."""

    total: int
    succeeded: int
    failed: int
    errors: list[dict[str, Any]] = Field(default_factory=list)
