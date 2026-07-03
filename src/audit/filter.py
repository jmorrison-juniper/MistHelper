"""Noise filtering for Mist org audit log entries.

Removes non-actionable entries (logins, packet captures, webshell invocations,
cascade noise from profile pushes) to isolate meaningful configuration changes.
"""

from typing import Any  # Any is used for opaque audit-entry values.

NOISE_PHRASES = [  # Default substrings flagged as non-actionable audit noise
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


class AuditLogFilter:  # Encapsulates noise-filtering rules for audit entries
    """Filter noise from org audit log entries."""

    def __init__(self, noise_phrases: list[str] | None = None):  # Allow override for tests
        """Initialize with optional custom noise phrases.

        Args:
            noise_phrases: List of message substrings to filter.
                Uses defaults if None.
        """
        # Fall back to module defaults when caller passes None.
        self.noise_phrases = noise_phrases if noise_phrases is not None else NOISE_PHRASES

    def is_noise(self, entry: dict[str, Any]) -> bool:  # Public predicate used by filter methods
        """Determine if an audit log entry is noise.

        Args:
            entry: Single audit log entry dict.

        Returns:
            True if the entry should be filtered out.
        """
        msg = entry.get("message", "")  # Missing message defaults to empty string
        if self._matches_noise_phrase(msg):  # Phrase-match noise (login/logout, packet capture, etc.)
            return True  # Phrase match short-circuits to noise
        if _is_vpn_cascade(msg, entry):  # VPN update without before/after detail
            return True  # VPN cascade short-circuits to noise
        if _is_adopted_flag_cascade(msg, entry):  # Device update whose only diff is adopted:false
            return True  # Adopted-flag cascade short-circuits to noise
        return False  # Retain the entry

    def _matches_noise_phrase(self, msg: str) -> bool:  # Instance helper: uses configured phrase list
        """Return True when ``msg`` contains any configured noise substring."""
        # WHY: extracted so is_noise drops from CC 8 to <=5.
        return any(phrase in msg for phrase in self.noise_phrases)  # Any-match keeps CC flat

    def filter(self, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:  # Bulk filter
        """Filter noise entries from a list of audit log entries.

        Args:
            entries: List of audit log entry dicts.

        Returns:
            Filtered list with noise removed, preserving order.
        """
        return [e for e in entries if not self.is_noise(e)]  # Preserve original order

    def filter_with_stats(
        self, entries: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], dict[str, int]]:  # Bulk filter + counters
        """Filter entries and return statistics about what was removed.

        Args:
            entries: List of audit log entry dicts.

        Returns:
            Tuple of (filtered_entries, stats_dict).
        """
        kept: list[dict[str, Any]] = []  # Accumulator for retained entries
        removed_count = 0  # Running tally of dropped entries
        for entry in entries:  # Walk every entry once
            if self.is_noise(entry):  # Test each entry against noise rules
                removed_count += 1  # Increment drop counter
            else:
                kept.append(entry)  # Preserve non-noise entries
        stats = {  # Summary dict for the caller
            "original_count": len(entries),  # Total input size
            "kept_count": len(kept),  # Non-noise total
            "removed_count": removed_count,  # Noise total
        }
        return kept, stats  # Return retained entries and stats


def _is_vpn_cascade(msg: str, entry: dict[str, Any]) -> bool:  # Helper: VPN cascade-noise detector
    """Return True for VPN updates that omit a before/after diff."""
    # WHY: extracted so is_noise drops from CC 8 to <=5.
    return "Update VPN" in msg and "before" not in entry  # Missing "before" == cascade-only edit


def _is_adopted_flag_cascade(msg: str, entry: dict[str, Any]) -> bool:  # Helper: adopted:false cascade detector
    """Return True for device updates whose only change is the adopted flag cascade."""
    # WHY: extracted so is_noise drops from CC 8 to <=5.
    if "Update Device" not in msg:  # Guard: only Update Device entries qualify
        return False  # Non-device entries never match this pattern
    before: dict[str, Any] = entry.get("before", {})  # Pre-change device attributes
    after: dict[str, Any] = entry.get("after", {})  # Post-change device attributes
    cascade = {"adopted": False}  # Sentinel diff shape indicating adopted-flag cascade
    return before == cascade and after == cascade  # Both sides carry only the cascade flag
