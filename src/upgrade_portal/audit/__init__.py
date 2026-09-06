"""Audit logging framework for upgrade portal.

Provides queryable audit trail with automatic secret masking.
Implements FR-019 (log all operations) and SC-010 (zero secrets).
"""

# WHY: re-export public API for convenient imports
from .logger import AuditLogger  # WHY: main audit logging service
from .masker import SecretMasker  # WHY: redaction filter for sensitive data

__all__ = ["AuditLogger", "SecretMasker"]
