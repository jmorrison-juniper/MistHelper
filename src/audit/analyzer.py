"""Audit log analysis engine.

Groups filtered audit entries by admin and by object, computes
chronological timelines, object changelogs, and rollback diffs
(first-seen vs last-seen state comparison).
"""

import re  # regex for extracting quoted object names from audit messages
from dataclasses import dataclass, field  # immutable/mutable result containers
from typing import Any  # audit entry dicts hold heterogeneous values

OBJECT_NAME_PATTERN = re.compile(r'"([^"]+)"')  # first quoted token in audit message

# Table-driven dispatch: message prefix -> object type classification
MESSAGE_TYPE_MAP = {
    "Update Device": "Device",  # AP/switch/gateway modifications
    "Update Template": "Template",  # WLAN or gateway template edits
    "Update Network": "Network",  # network subnet definition edits
    "Update Service": "Service",  # service definition edits
    "Update VPN": "VPN",  # WAN overlay VPN edits
    "Delete Device": "Device",  # device removal audit
    "Delete Template": "Template",  # template removal audit
    "Delete Network": "Network",  # network removal audit
    "Delete Service": "Service",  # service removal audit
    "Create Network": "Network",  # new network creation audit
    "Create Service": "Service",  # new service creation audit
    "Create Template": "Template",  # new template creation audit
    "Update DeviceProfile": "DeviceProfile",  # device profile modifications
    "Update Org Setting": "OrgSetting",  # org-level setting changes
    "Update Site Setting": "SiteSetting",  # site-level setting changes
}


@dataclass
class AdminTimeline:  # per-admin action bucket used for reporter grouping
    """Chronological record of one admin's actions."""

    admin_name: str  # display name for reporting
    admin_id: str  # unique identifier used as map key
    entries: list[dict[str, Any]] = field(default_factory=list)  # raw audit rows
    first_action: int = 0  # earliest timestamp seen (epoch seconds)
    last_action: int = 0  # latest timestamp seen (epoch seconds)
    action_count: int = 0  # cached len for reporting without list traversal


@dataclass
class ObjectChange:  # single mutation event captured from audit stream
    """Single change event for a tracked object."""

    timestamp: int  # epoch seconds when change occurred
    admin_name: str  # who performed the change
    message: str  # raw audit message describing the change
    before: dict[str, Any] = field(default_factory=dict)  # pre-change state snapshot
    after: dict[str, Any] = field(default_factory=dict)  # post-change state snapshot


@dataclass
class ObjectChangelog:  # ordered mutation history for a specific config object
    """Full modification history for a single config object."""

    object_name: str  # quoted name from audit message
    object_type: str  # classified type from MESSAGE_TYPE_MAP
    changes: list[ObjectChange] = field(default_factory=list)  # ordered by timestamp


@dataclass
class RollbackDiff:  # net first-vs-last state comparison for rollback planning
    """Comparison of first-seen vs last-seen state for an object."""

    object_name: str  # object being diffed
    object_type: str  # object type classification
    original_state: dict[str, Any] = field(default_factory=dict)  # first-seen snapshot
    final_state: dict[str, Any] = field(default_factory=dict)  # last-seen snapshot
    fields_changed: list[str] = field(default_factory=list)  # top-level keys that differ
    net_changed: bool = False  # false when object reverted to original state


@dataclass
class AuditAnalysisResult:  # container returned by AuditLogAnalyzer.analyze
    """Complete analysis output."""

    admin_timelines: list[AdminTimeline] = field(default_factory=list)  # per-admin view
    object_changelogs: list[ObjectChangelog] = field(default_factory=list)  # per-object view
    rollback_diffs: list[RollbackDiff] = field(default_factory=list)  # net-changed subset
    time_range_description: str = ""  # human-readable window label
    total_entries: int = 0  # unfiltered input count for context
    filtered_entries: int = 0  # entries actually analyzed


class AuditLogAnalyzer:  # main entry point orchestrating all three view builders
    """Analyze filtered audit log entries into structured results."""

    def analyze(
        self,
        entries: list[dict[str, Any]],
        time_range_description: str = "",
    ) -> AuditAnalysisResult:  # public API: build all three analysis views
        """Run full analysis on filtered audit entries.

        Args: entries (oldest-first list of dict rows), time_range_description
        (human-readable label). Returns AuditAnalysisResult bundling per-admin
        timelines, per-object changelogs, and net-changed rollback diffs.
        """
        sorted_entries = sorted(entries, key=lambda e: e.get("timestamp", 0))  # defensive re-sort
        admin_timelines = self._build_admin_timelines(sorted_entries)  # per-admin view
        object_changelogs = self._build_object_changelogs(sorted_entries)  # per-object view
        rollback_diffs = self._build_rollback_diffs(object_changelogs)  # net-change subset
        return AuditAnalysisResult(
            admin_timelines=admin_timelines,  # ordered by first_action
            object_changelogs=object_changelogs,  # ordered by earliest change
            rollback_diffs=rollback_diffs,  # net-changed objects only
            time_range_description=time_range_description,  # verbatim report label
            total_entries=len(entries),  # raw input count for context
            filtered_entries=len(sorted_entries),  # count actually analyzed
        )

    def _build_admin_timelines(self, entries: list[dict[str, Any]]) -> list[AdminTimeline]:  # admin view
        """Group entries by admin into chronological timelines."""
        admin_map: dict[str, AdminTimeline] = {}  # admin_id keyed accumulator
        for entry in entries:  # single pass over pre-sorted entries
            self._accumulate_admin_entry(admin_map, entry)  # single-entry merge
        # Sort admins by earliest action so reports display in chronological order
        return sorted(admin_map.values(), key=lambda t: t.first_action)  # chronological order

    @staticmethod
    def _accumulate_admin_entry(  # in-place merge keeps caller loop small
        admin_map: dict[str, AdminTimeline],
        entry: dict[str, Any],
    ) -> None:
        """Merge one entry into the per-admin timeline map (in-place)."""
        admin_id = entry.get("admin_id", "unknown")  # fallback for legacy rows
        timestamp = entry.get("timestamp", 0)  # zero sentinel handled below
        timeline = admin_map.get(admin_id)  # lazy create on first sighting
        if timeline is None:  # first time seeing this admin
            timeline = AdminTimeline(
                admin_name=entry.get("admin_name", "Unknown"),  # display fallback
                admin_id=admin_id,  # map key for stability
            )
            admin_map[admin_id] = timeline  # register newly created timeline
        timeline.entries.append(entry)  # preserve full row for downstream detail views
        timeline.action_count += 1  # cache count to avoid repeated len() calls
        # first_action==0 sentinel handles first-ever assignment
        if timeline.first_action == 0 or timestamp < timeline.first_action:  # update earliest
            timeline.first_action = timestamp  # narrow to smaller epoch
        if timestamp > timeline.last_action:  # update latest
            timeline.last_action = timestamp  # extend to larger epoch

    def _build_object_changelogs(self, entries: list[dict[str, Any]]) -> list[ObjectChangelog]:  # object view
        """Group entries by object into changelogs."""
        object_map: dict[str, ObjectChangelog] = {}  # composite type:name key accumulator
        for entry in entries:  # single pass over sorted entries
            self._accumulate_object_entry(object_map, entry)  # single-entry merge
        # Order changelogs by earliest change so report ordering is stable
        return sorted(
            object_map.values(),  # bucket instances only
            key=lambda c: c.changes[0].timestamp if c.changes else 0,  # earliest ts fallback 0
        )

    def _accumulate_object_entry(  # in-place merge keeps caller loop small
        self,
        object_map: dict[str, ObjectChangelog],
        entry: dict[str, Any],
    ) -> None:
        """Merge one entry into the per-object changelog map (in-place)."""
        msg = entry.get("message", "")  # message drives name/type extraction
        obj_name = self._extract_object_name(msg)  # first quoted token
        if not obj_name:  # unnamed entries carry no object identity so skip them
            return  # nothing to record without an object name
        obj_type = self._extract_object_type(msg)  # classify via prefix table
        key = f"{obj_type}:{obj_name}"  # composite key avoids cross-type name collisions
        changelog = object_map.get(key)  # existing bucket if already sighted
        if changelog is None:  # lazily create on first sighting for this key
            changelog = ObjectChangelog(object_name=obj_name, object_type=obj_type)  # new bucket
            object_map[key] = changelog  # register newly created changelog
        changelog.changes.append(self._make_change(entry, msg))  # append snapshot for diffing

    @staticmethod
    def _make_change(entry: dict[str, Any], msg: str) -> ObjectChange:  # audit->snapshot helper
        """Build ObjectChange snapshot from a raw audit entry."""
        return ObjectChange(
            timestamp=entry.get("timestamp", 0),  # epoch seconds sentinel 0 sorts first
            admin_name=entry.get("admin_name", "Unknown"),  # human display name fallback
            message=msg,  # verbatim message for detail views
            before=entry.get("before", {}),  # missing snapshot treated as empty
            after=entry.get("after", {}),  # missing snapshot treated as empty
        )

    def _build_rollback_diffs(self, changelogs: list[ObjectChangelog]) -> list[RollbackDiff]:  # net view
        """Compare first-seen vs last-seen state for each object."""
        # Only surface objects with net state change to keep report focused
        return [diff for changelog in changelogs if (diff := self._diff_for_changelog(changelog)) is not None]

    def _diff_for_changelog(self, changelog: ObjectChangelog) -> RollbackDiff | None:  # per-object diff
        """Compute rollback diff for one changelog, or None if not net-changed."""
        if not changelog.changes:  # empty history cannot produce a diff
            return None
        original = changelog.changes[0].before  # first-seen pre-state
        final = changelog.changes[-1].after  # last-seen post-state
        if not original and not final:  # both empty means no snapshot data to compare
            return None
        fields_changed = self._compute_changed_fields(original, final)  # top-level diff keys
        if not fields_changed:  # skip reverted objects to avoid report noise
            return None
        return RollbackDiff(
            object_name=changelog.object_name,  # carry-through identity
            object_type=changelog.object_type,  # carry-through classification
            original_state=original,  # baseline for rollback plan
            final_state=final,  # current state for rollback plan
            fields_changed=fields_changed,  # deterministic sorted key list
            net_changed=True,  # true by construction (fields_changed non-empty)
        )

    @staticmethod
    def _extract_object_name(message: str) -> str:
        """Extract quoted object name from audit log message."""
        match = OBJECT_NAME_PATTERN.search(message)  # first quoted token only
        return match.group(1) if match else ""

    @staticmethod
    def _extract_object_type(message: str) -> str:
        """Determine object type from message prefix."""
        # Linear scan is fine: table has ~15 entries and this runs per entry
        for prefix, obj_type in MESSAGE_TYPE_MAP.items():
            if message.startswith(prefix):
                return obj_type
        return "Unknown"  # unclassified prefix falls back to generic bucket

    @staticmethod
    def _compute_changed_fields(original: dict[str, Any], final: dict[str, Any]) -> list[str]:
        """Compute list of top-level fields that differ."""
        # Union of keys catches additions and deletions, not just modifications
        all_keys = set(original.keys()) | set(final.keys())
        # Sorted output makes diffs deterministic for snapshot testing
        return [key for key in sorted(all_keys) if original.get(key) != final.get(key)]
