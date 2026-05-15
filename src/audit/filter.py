"""Noise filtering for Mist org audit log entries.

Removes non-actionable entries (logins, packet captures, webshell invocations,
cascade noise from profile pushes) to isolate meaningful configuration changes.
"""

from typing import Any

NOISE_PHRASES = [
    "Accessed Org",
    "Accessed by Mist Support",
    "Packet Capture started",
    "Packet Capture stopped",
    "Invoked Webshell",
    "Clearing sessions",
    "Login ",
    "Logout ",
    "manually restarted",
    "Getting device",
]


class AuditLogFilter:
    """Filter noise from org audit log entries."""

    def __init__(self, noise_phrases: list[str] | None = None):
        """Initialize with optional custom noise phrases.

        Args:
            noise_phrases: List of message substrings to filter.
                Uses defaults if None.
        """
        self.noise_phrases = noise_phrases if noise_phrases is not None else NOISE_PHRASES

    def is_noise(self, entry: dict[str, Any]) -> bool:
        """Determine if an audit log entry is noise.

        Args:
            entry: Single audit log entry dict.

        Returns:
            True if the entry should be filtered out.
        """
        msg = entry.get("message", "")

        for phrase in self.noise_phrases:
            if phrase in msg:
                return True

        if "Update VPN" in msg and "before" not in entry:
            return True

        if "Update Device" in msg:
            before = entry.get("before", {})
            after = entry.get("after", {})
            if before == {"adopted": False} and after == {"adopted": False}:
                return True

        return False

    def filter(self, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter noise entries from a list of audit log entries.

        Args:
            entries: List of audit log entry dicts.

        Returns:
            Filtered list with noise removed, preserving order.
        """
        return [e for e in entries if not self.is_noise(e)]

    def filter_with_stats(self, entries: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
        """Filter entries and return statistics about what was removed.

        Args:
            entries: List of audit log entry dicts.

        Returns:
            Tuple of (filtered_entries, stats_dict).
        """
        kept = []
        removed_count = 0

        for entry in entries:
            if self.is_noise(entry):
                removed_count += 1
            else:
                kept.append(entry)

        stats = {
            "original_count": len(entries),
            "kept_count": len(kept),
            "removed_count": removed_count,
        }
        return kept, stats
