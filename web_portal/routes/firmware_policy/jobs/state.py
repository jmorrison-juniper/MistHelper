"""Keep private execution context separate from the public job record."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from src.operations.execution.firmware_policy.sdk import PolicyError


@dataclass
class JobEntry:
    """Keep one owned operation and its single-use proof in process memory."""

    record: dict[str, Any]
    context: Any = field(default=None, repr=False)
    token: str | None = field(default=None, repr=False)


class JobState:
    """Allow only documented, non-secret progress fields in durable records."""

    @staticmethod
    def owner(value: str) -> str:
        """Avoid saving the browser owner secret in the status file."""
        return hashlib.sha256(value.encode("utf-8")).hexdigest()  # The cookie secret never enters a file.

    @staticmethod
    def progress(event: dict[str, Any]) -> dict[str, Any]:
        """Reject arbitrary callback values rather than persisting private settings."""
        result: dict[str, Any] = {}  # Only the callback contract can cross the privacy boundary.
        for key in ("phase", "scope", "id", "name"):
            if isinstance(event.get(key), str):
                result[key] = event[key][:256]  # Bound external display metadata.
        for key in ("completed", "total", "wait_seconds"):
            value = event.get(key)  # Preserve genuine counts, not estimated totals.
            if isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value < float("inf"):
                result[key] = value  # Ignore invalid and non-finite values.
        return result  # Unknown fields can contain settings and must not escape.

    @staticmethod
    def rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return compact named targets in a stable alphabetical order."""
        fields = ("scope", "id", "name", "organization", "backup", "status")
        public = [{key: row[key] for key in fields if key in row} for row in rows]  # Exclude settings bodies.
        return sorted(public, key=lambda row: (str(row.get("name", "")).casefold(), str(row.get("id", ""))))

    @staticmethod
    def public(entry: JobEntry) -> dict[str, Any]:
        """Hide ownership and expose a confirmation token only after verification."""
        result = {
            key: value for key, value in entry.record.items() if key not in {"owner", "worker"}
        }  # Hide private ownership.
        if result["state"] == "ready" and entry.token:
            result["token"] = entry.token  # Only the owning browser can reach this method.
        return result  # Private plans and proofs have no serialization path.


class JobErrors:
    """Preserve checked operator diagnostics without exposing arbitrary exception text."""

    @staticmethod
    def message(error: Exception) -> str:
        """Accept only bounded ASCII diagnostics from the checked domain boundary."""
        if isinstance(error, PolicyError):
            message = str(error)  # Domain checked errors contain no SDK response body.
            prefixes = (
                "The ",
                "Select ",
                "Type ",
                "Create ",
                "Send ",
                "No ",
                "Wait ",
                "Read ",
                "Write ",
                "List ",
                "Settings ",
                "Organization ",
                "Site ",
                "Saved ",
                "Explicitly ",
                "A ",
                "Windows ",
                "Backup ",
                "Legacy ",
                "Unsupported ",
                "Source ",
                "Restoration ",
                "Complete ",
                "Policy ",
                "Invalid ",
                "Missing ",
                "Recovery ",
                "Firmware ",
                "Model ",
                "Enable ",
                "Prepare ",
            )  # Known domain and route diagnostics start with explicit operator language.
            if (
                len(message) <= 1200
                and message.startswith(prefixes)
                and all(32 <= ord(character) < 127 for character in message)
            ):
                return message  # Preserve confirmation words, identifiers, and checked HTTP status.
        return "The operation stopped. Check the private operator log and prepare again."
