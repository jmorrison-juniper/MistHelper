"""Audit log analysis engine.

Groups filtered audit entries by admin and by object, computes
chronological timelines, object changelogs, and rollback diffs
(first-seen vs last-seen state comparison).
"""

import re
from dataclasses import dataclass, field
from typing import Any

OBJECT_NAME_PATTERN = re.compile(r'"([^"]+)"')

MESSAGE_TYPE_MAP = {
    "Update Device": "Device",
    "Update Template": "Template",
    "Update Network": "Network",
    "Update Service": "Service",
    "Update VPN": "VPN",
    "Delete Device": "Device",
    "Delete Template": "Template",
    "Delete Network": "Network",
    "Delete Service": "Service",
    "Create Network": "Network",
    "Create Service": "Service",
    "Create Template": "Template",
    "Update DeviceProfile": "DeviceProfile",
    "Update Org Setting": "OrgSetting",
    "Update Site Setting": "SiteSetting",
}


@dataclass
class AdminTimeline:
    """Chronological record of one admin's actions."""

    admin_name: str
    admin_id: str
    entries: list[dict[str, Any]] = field(default_factory=list)
    first_action: int = 0
    last_action: int = 0
    action_count: int = 0


@dataclass
class ObjectChange:
    """Single change event for a tracked object."""

    timestamp: int
    admin_name: str
    message: str
    before: dict[str, Any] = field(default_factory=dict)
    after: dict[str, Any] = field(default_factory=dict)


@dataclass
class ObjectChangelog:
    """Full modification history for a single config object."""

    object_name: str
    object_type: str
    changes: list[ObjectChange] = field(default_factory=list)


@dataclass
class RollbackDiff:
    """Comparison of first-seen vs last-seen state for an object."""

    object_name: str
    object_type: str
    original_state: dict[str, Any] = field(default_factory=dict)
    final_state: dict[str, Any] = field(default_factory=dict)
    fields_changed: list[str] = field(default_factory=list)
    net_changed: bool = False


@dataclass
class AuditAnalysisResult:
    """Complete analysis output."""

    admin_timelines: list[AdminTimeline] = field(default_factory=list)
    object_changelogs: list[ObjectChangelog] = field(default_factory=list)
    rollback_diffs: list[RollbackDiff] = field(default_factory=list)
    time_range_description: str = ""
    total_entries: int = 0
    filtered_entries: int = 0


class AuditLogAnalyzer:
    """Analyze filtered audit log entries into structured results."""

    def analyze(
        self,
        entries: list[dict[str, Any]],
        time_range_description: str = "",
    ) -> AuditAnalysisResult:
        """Run full analysis on filtered audit entries.

        Args:
            entries: Filtered audit log entries sorted oldest-first.
            time_range_description: Human-readable time range label.

        Returns:
            AuditAnalysisResult with timelines, changelogs, and diffs.
        """
        sorted_entries = sorted(entries, key=lambda e: e.get("timestamp", 0))

        admin_timelines = self._build_admin_timelines(sorted_entries)
        object_changelogs = self._build_object_changelogs(sorted_entries)
        rollback_diffs = self._build_rollback_diffs(object_changelogs)

        return AuditAnalysisResult(
            admin_timelines=admin_timelines,
            object_changelogs=object_changelogs,
            rollback_diffs=rollback_diffs,
            time_range_description=time_range_description,
            total_entries=len(entries),
            filtered_entries=len(sorted_entries),
        )

    def _build_admin_timelines(self, entries: list[dict[str, Any]]) -> list[AdminTimeline]:
        """Group entries by admin into chronological timelines."""
        admin_map: dict[str, AdminTimeline] = {}

        for entry in entries:
            admin_id = entry.get("admin_id", "unknown")
            admin_name = entry.get("admin_name", "Unknown")
            timestamp = entry.get("timestamp", 0)

            if admin_id not in admin_map:
                admin_map[admin_id] = AdminTimeline(
                    admin_name=admin_name,
                    admin_id=admin_id,
                )

            timeline = admin_map[admin_id]
            timeline.entries.append(entry)
            timeline.action_count += 1

            if timeline.first_action == 0 or timestamp < timeline.first_action:
                timeline.first_action = timestamp
            if timestamp > timeline.last_action:
                timeline.last_action = timestamp

        return sorted(
            admin_map.values(),
            key=lambda t: t.first_action,
        )

    def _build_object_changelogs(self, entries: list[dict[str, Any]]) -> list[ObjectChangelog]:
        """Group entries by object into changelogs."""
        object_map: dict[str, ObjectChangelog] = {}

        for entry in entries:
            msg = entry.get("message", "")
            obj_name = self._extract_object_name(msg)
            obj_type = self._extract_object_type(msg)

            if not obj_name:
                continue

            key = f"{obj_type}:{obj_name}"
            if key not in object_map:
                object_map[key] = ObjectChangelog(
                    object_name=obj_name,
                    object_type=obj_type,
                )

            change = ObjectChange(
                timestamp=entry.get("timestamp", 0),
                admin_name=entry.get("admin_name", "Unknown"),
                message=msg,
                before=entry.get("before", {}),
                after=entry.get("after", {}),
            )
            object_map[key].changes.append(change)

        return sorted(
            object_map.values(),
            key=lambda c: c.changes[0].timestamp if c.changes else 0,
        )

    def _build_rollback_diffs(self, changelogs: list[ObjectChangelog]) -> list[RollbackDiff]:
        """Compare first-seen vs last-seen state for each object."""
        diffs = []

        for changelog in changelogs:
            if not changelog.changes:
                continue

            first_change = changelog.changes[0]
            last_change = changelog.changes[-1]

            original = first_change.before
            final = last_change.after

            if not original and not final:
                continue

            fields_changed = self._compute_changed_fields(original, final)
            net_changed = bool(fields_changed)

            diffs.append(
                RollbackDiff(
                    object_name=changelog.object_name,
                    object_type=changelog.object_type,
                    original_state=original,
                    final_state=final,
                    fields_changed=fields_changed,
                    net_changed=net_changed,
                )
            )

        return [d for d in diffs if d.net_changed]

    @staticmethod
    def _extract_object_name(message: str) -> str:
        """Extract quoted object name from audit log message."""
        match = OBJECT_NAME_PATTERN.search(message)
        return match.group(1) if match else ""

    @staticmethod
    def _extract_object_type(message: str) -> str:
        """Determine object type from message prefix."""
        for prefix, obj_type in MESSAGE_TYPE_MAP.items():
            if message.startswith(prefix):
                return obj_type
        return "Unknown"

    @staticmethod
    def _compute_changed_fields(original: dict[str, Any], final: dict[str, Any]) -> list[str]:
        """Compute list of top-level fields that differ."""
        changed = []
        all_keys = set(list(original.keys()) + list(final.keys()))

        for key in sorted(all_keys):
            orig_val = original.get(key)
            final_val = final.get(key)
            if orig_val != final_val:
                changed.append(key)

        return changed
