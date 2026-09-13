"""Unit tests for src.audit.analyzer module.

Covers AuditLogAnalyzer.analyze, _build_admin_timelines,
_build_object_changelogs, _build_rollback_diffs, _extract_object_name,
_extract_object_type, and _compute_changed_fields.
"""

from src.audit.analyzer import (
    AuditAnalysisResult,
    AuditLogAnalyzer,
    ObjectChange,
    ObjectChangelog,
)


class TestExtractObjectName:
    """Tests for AuditLogAnalyzer._extract_object_name static method."""

    def test_quoted_name_is_extracted(self):
        """A quoted name in the message must be returned without quotes."""
        msg = 'Update Template "CorePolicy"'  # Message with a quoted name
        result = AuditLogAnalyzer._extract_object_name(msg)  # Extract the name
        assert result == "CorePolicy"  # Must match the content between quotes

    def test_no_quotes_returns_empty_string(self):
        """A message without quotes returns an empty string."""
        msg = "Update Template no quotes here"  # No quoted section
        result = AuditLogAnalyzer._extract_object_name(msg)  # Try to extract
        assert result == ""  # No match, must return empty string

    def test_first_quoted_segment_returned(self):
        """When multiple quoted segments exist, the first is returned."""
        msg = 'Update Device "AP-1" on site "Main"'  # Two quoted segments
        result = AuditLogAnalyzer._extract_object_name(msg)  # Extract first name
        assert result == "AP-1"  # First match wins


class TestExtractObjectType:
    """Tests for AuditLogAnalyzer._extract_object_type static method."""

    def test_update_template_prefix_returns_template(self):
        """'Update Template' prefix maps to type 'Template'."""
        msg = 'Update Template "MyPolicy"'  # Template update message
        result = AuditLogAnalyzer._extract_object_type(msg)  # Classify message
        assert result == "Template"  # Correct mapping from MESSAGE_TYPE_MAP

    def test_update_device_prefix_returns_device(self):
        """'Update Device' prefix maps to type 'Device'."""
        msg = 'Update Device "AP-Lab"'  # Device update message
        result = AuditLogAnalyzer._extract_object_type(msg)  # Classify
        assert result == "Device"  # Expected type mapping

    def test_create_network_prefix_returns_network(self):
        """'Create Network' prefix maps to type 'Network'."""
        msg = 'Create Network "VLAN10"'  # Network creation message
        result = AuditLogAnalyzer._extract_object_type(msg)  # Classify
        assert result == "Network"  # Must recognise Create prefix too

    def test_unrecognised_prefix_returns_unknown(self):
        """A message with no recognised prefix returns 'Unknown'."""
        msg = "Something completely unrelated"  # No matching prefix
        result = AuditLogAnalyzer._extract_object_type(msg)  # Default path
        assert result == "Unknown"  # Fallback type

    def test_update_vpn_returns_vpn(self):
        """'Update VPN' prefix maps to 'VPN' type."""
        msg = 'Update VPN "HubSpoke"'  # VPN update message
        result = AuditLogAnalyzer._extract_object_type(msg)  # Classify
        assert result == "VPN"  # VPN type


class TestComputeChangedFields:
    """Tests for AuditLogAnalyzer._compute_changed_fields static method."""

    def test_identical_dicts_returns_empty_list(self):
        """No difference between original and final produces an empty list."""
        orig = {"name": "Test", "enabled": True}  # State before
        final = {"name": "Test", "enabled": True}  # State after (same)
        result = AuditLogAnalyzer._compute_changed_fields(orig, final)  # Compare
        assert result == []  # No fields changed

    def test_changed_value_included_in_result(self):
        """A field with a different value appears in the result list."""
        orig = {"name": "OldName"}  # Before state
        final = {"name": "NewName"}  # After state with changed value
        result = AuditLogAnalyzer._compute_changed_fields(orig, final)  # Compare
        assert "name" in result  # Changed field must be reported

    def test_added_key_reported_as_changed(self):
        """A key that exists in final but not in original is reported."""
        orig = {}  # Empty before state
        final = {"new_key": "value"}  # New key added
        result = AuditLogAnalyzer._compute_changed_fields(orig, final)  # Compare
        assert "new_key" in result  # Addition is treated as a change

    def test_removed_key_reported_as_changed(self):
        """A key that exists in original but not in final is reported."""
        orig = {"removed": "value"}  # Key present before
        final = {}  # Key missing after
        result = AuditLogAnalyzer._compute_changed_fields(orig, final)  # Compare
        assert "removed" in result  # Removal is treated as a change

    def test_multiple_changes_all_reported(self):
        """All changed fields appear in the returned list."""
        orig = {"a": 1, "b": 2, "c": 3}  # Three keys before
        final = {"a": 99, "b": 2, "d": 4}  # a changed, c removed, d added
        result = AuditLogAnalyzer._compute_changed_fields(orig, final)  # Compare
        assert "a" in result  # Changed value
        assert "b" not in result  # Unchanged field must NOT appear
        assert "c" in result  # Removed field
        assert "d" in result  # Added field

    def test_result_is_sorted(self):
        """Changed field names must be returned in sorted order."""
        orig = {"z": 1, "a": 2}  # Two keys
        final = {"z": 9, "a": 9}  # Both changed
        result = AuditLogAnalyzer._compute_changed_fields(orig, final)  # Compare
        assert result == sorted(result)  # Output must be alphabetically sorted


class TestBuildAdminTimelines:
    """Tests for AuditLogAnalyzer._build_admin_timelines method."""

    def setup_method(self):
        """Create a fresh analyzer before each test."""
        self.analyzer = AuditLogAnalyzer()  # Fresh instance for isolation

    def test_single_admin_creates_one_timeline(self):
        """Two entries from the same admin produce exactly one AdminTimeline."""
        entries = [  # Two entries for the same admin
            {"admin_id": "u1", "admin_name": "Alice", "timestamp": 1000},
            {"admin_id": "u1", "admin_name": "Alice", "timestamp": 2000},
        ]
        timelines = self.analyzer._build_admin_timelines(entries)  # Build timelines
        assert len(timelines) == 1  # One admin = one timeline
        assert timelines[0].admin_name == "Alice"  # Name preserved
        assert timelines[0].action_count == 2  # Both actions counted

    def test_multiple_admins_create_separate_timelines(self):
        """Entries from different admins produce separate AdminTimeline objects."""
        entries = [  # Two different admins
            {"admin_id": "u1", "admin_name": "Alice", "timestamp": 1000},
            {"admin_id": "u2", "admin_name": "Bob", "timestamp": 2000},
            {"admin_id": "u1", "admin_name": "Alice", "timestamp": 3000},
        ]
        timelines = self.analyzer._build_admin_timelines(entries)  # Build timelines
        assert len(timelines) == 2  # Two admins, two timelines
        names = [t.admin_name for t in timelines]  # Collect timeline names
        assert "Alice" in names  # Alice has a timeline
        assert "Bob" in names  # Bob has a timeline

    def test_first_and_last_action_timestamps(self):
        """first_action and last_action track the earliest and latest timestamps."""
        entries = [  # Three entries with ascending timestamps
            {"admin_id": "u1", "admin_name": "Alice", "timestamp": 1000},
            {"admin_id": "u1", "admin_name": "Alice", "timestamp": 3000},
            {"admin_id": "u1", "admin_name": "Alice", "timestamp": 2000},
        ]
        timelines = self.analyzer._build_admin_timelines(entries)  # Build
        tl = timelines[0]  # Only one admin timeline
        assert tl.first_action == 1000  # Earliest timestamp
        assert tl.last_action == 3000  # Latest timestamp

    def test_empty_entries_returns_empty_list(self):
        """No entries produces an empty list of timelines."""
        timelines = self.analyzer._build_admin_timelines([])  # Empty input
        assert timelines == []  # No timelines to return


class TestBuildObjectChangelogs:
    """Tests for AuditLogAnalyzer._build_object_changelogs method."""

    def setup_method(self):
        """Create a fresh analyzer before each test."""
        self.analyzer = AuditLogAnalyzer()  # Fresh instance

    def test_entries_grouped_by_object_name(self):
        """Multiple changes to the same object create one changelog."""
        entries = [  # Two changes to the same template
            {
                "message": 'Update Template "T1"',
                "admin_name": "Alice",
                "timestamp": 1000,
                "before": {},
                "after": {},
            },
            {
                "message": 'Update Template "T1"',
                "admin_name": "Alice",
                "timestamp": 2000,
                "before": {},
                "after": {},
            },
        ]
        changelogs = self.analyzer._build_object_changelogs(entries)  # Group
        assert len(changelogs) == 1  # Same object = one changelog
        assert changelogs[0].object_name == "T1"  # Name extracted from message
        assert len(changelogs[0].changes) == 2  # Both changes recorded

    def test_entry_without_quoted_name_is_skipped(self):
        """An entry with no quoted object name is excluded from changelogs."""
        entries = [  # Message has no quoted name
            {"message": "Update Template no quotes", "admin_name": "Bob", "timestamp": 1000},
        ]
        changelogs = self.analyzer._build_object_changelogs(entries)  # Build
        assert len(changelogs) == 0  # Entry skipped, no changelogs produced

    def test_different_objects_create_separate_changelogs(self):
        """Changes to different objects create independent changelogs."""
        entries = [  # Two distinct objects
            {"message": 'Update Template "T1"', "admin_name": "Alice", "timestamp": 1000},
            {"message": 'Update Network "VLAN10"', "admin_name": "Bob", "timestamp": 2000},
        ]
        changelogs = self.analyzer._build_object_changelogs(entries)  # Group
        assert len(changelogs) == 2  # Two objects, two changelogs
        names = {c.object_name for c in changelogs}  # Collect object names
        assert "T1" in names  # Template changelog present
        assert "VLAN10" in names  # Network changelog present

    def test_changelogs_sorted_by_first_change_timestamp(self):
        """Changelogs are ordered by the timestamp of their first change."""
        entries = [  # Second object changed before first
            {"message": 'Update Network "VLAN10"', "admin_name": "Bob", "timestamp": 500},
            {"message": 'Update Template "T1"', "admin_name": "Alice", "timestamp": 1000},
        ]
        changelogs = self.analyzer._build_object_changelogs(entries)  # Group
        assert changelogs[0].object_name == "VLAN10"  # Earlier first change comes first
        assert changelogs[1].object_name == "T1"  # Later first change comes second


class TestBuildRollbackDiffs:
    """Tests for AuditLogAnalyzer._build_rollback_diffs method."""

    def setup_method(self):
        """Create a fresh analyzer for each test."""
        self.analyzer = AuditLogAnalyzer()  # Fresh instance

    def _make_changelog(self, name, obj_type, changes_data):
        """Build an ObjectChangelog from (timestamp, before, after) tuples.

        Args:
            name: Object name string.
            obj_type: Object type string.
            changes_data: List of (timestamp, before_dict, after_dict) tuples.

        Returns:
            ObjectChangelog populated with ObjectChange instances.
        """
        changelog = ObjectChangelog(  # Create changelog shell
            object_name=name,
            object_type=obj_type,
        )
        for ts, before, after in changes_data:  # Append each change
            changelog.changes.append(  # Build change record
                ObjectChange(
                    timestamp=ts,
                    admin_name="TestAdmin",  # Placeholder admin
                    message=f'Update {obj_type} "{name}"',  # Realistic message
                    before=before,  # Before state
                    after=after,  # After state
                )
            )
        return changelog  # Return populated changelog

    def test_net_change_produces_rollback_diff(self):
        """A changelog with a genuine net change produces a RollbackDiff."""
        changelog = self._make_changelog(  # One change from Old to New
            "T1",
            "Template",
            [(1000, {"name": "Old"}, {"name": "New"})],
        )
        diffs = self.analyzer._build_rollback_diffs([changelog])  # Compute
        assert len(diffs) == 1  # One diff produced
        assert diffs[0].object_name == "T1"  # Object name preserved
        assert diffs[0].net_changed is True  # Net change confirmed

    def test_empty_before_and_after_skipped(self):
        """A changelog whose first.before and last.after are both empty is skipped."""
        changelog = self._make_changelog(  # Change with empty before/after
            "T2",
            "Template",
            [(1000, {}, {})],  # Both empty
        )
        diffs = self.analyzer._build_rollback_diffs([changelog])  # Compute
        assert len(diffs) == 0  # Skipped because no state data

    def test_reverted_change_has_no_net_change(self):
        """A changelog where original state is restored has net_changed=False."""
        changelog = self._make_changelog(  # Change then revert
            "T3",
            "Template",
            [
                (1000, {"name": "Original"}, {"name": "Changed"}),  # Modified
                (2000, {"name": "Changed"}, {"name": "Original"}),  # Reverted
            ],
        )
        diffs = self.analyzer._build_rollback_diffs([changelog])  # Compute
        assert len(diffs) == 0  # Net change is zero, filtered out

    def test_changelog_with_no_changes_is_skipped(self):
        """An ObjectChangelog with an empty changes list is skipped entirely."""
        changelog = ObjectChangelog(  # No changes appended
            object_name="T4",
            object_type="Template",
        )
        diffs = self.analyzer._build_rollback_diffs([changelog])  # Compute
        assert len(diffs) == 0  # Empty changelog produces nothing

    def test_multiple_changelogs_only_net_changed_returned(self):
        """Only changelogs with a net change appear in the returned diffs."""
        changelog_changed = self._make_changelog(  # Real net change
            "T5",
            "Template",
            [(1000, {"x": 1}, {"x": 2})],  # x changed
        )
        changelog_reverted = self._make_changelog(  # Reverted, no net change
            "T6",
            "Template",
            [
                (1000, {"y": "a"}, {"y": "b"}),  # Changed
                (2000, {"y": "b"}, {"y": "a"}),  # Reverted
            ],
        )
        diffs = self.analyzer._build_rollback_diffs(  # Mix of changed and reverted
            [changelog_changed, changelog_reverted]
        )
        assert len(diffs) == 1  # Only the net-changed one
        assert diffs[0].object_name == "T5"  # The changed one kept


class TestAnalyze:
    """Integration tests for AuditLogAnalyzer.analyze method."""

    def setup_method(self):
        """Create a fresh analyzer for each test."""
        self.analyzer = AuditLogAnalyzer()  # Fresh instance

    def test_empty_entries_returns_empty_result(self):
        """No entries must produce an AuditAnalysisResult with all zeros."""
        result = self.analyzer.analyze([])  # Analyse empty list
        assert isinstance(result, AuditAnalysisResult)  # Must return correct type
        assert result.total_entries == 0  # No input
        assert result.admin_timelines == []  # No timelines
        assert result.object_changelogs == []  # No changelogs
        assert result.rollback_diffs == []  # No diffs

    def test_time_range_description_preserved(self):
        """The time_range_description argument is stored in the result."""
        result = self.analyzer.analyze(  # Pass a description
            [],
            time_range_description="last 7 days",
        )
        assert result.time_range_description == "last 7 days"  # Stored unchanged

    def test_full_pipeline_produces_structured_result(self):
        """A realistic set of entries generates timelines, changelogs, and diffs."""
        entries = [  # Two admins, two objects
            {
                "admin_id": "u1",
                "admin_name": "Alice",
                "timestamp": 1000,
                "message": 'Update Template "CorePolicy"',
                "before": {"enabled": False},  # Before state
                "after": {"enabled": True},  # After state (changed)
            },
            {
                "admin_id": "u2",
                "admin_name": "Bob",
                "timestamp": 2000,
                "message": 'Update Network "VLAN10"',
                "before": {"vlan_id": 10},  # Before state
                "after": {"vlan_id": 20},  # After state (changed)
            },
        ]
        result = self.analyzer.analyze(  # Run full analysis
            entries,
            time_range_description="last 7 days",
        )
        assert result.total_entries == 2  # Both entries counted
        assert len(result.admin_timelines) == 2  # One per admin
        assert len(result.object_changelogs) == 2  # One per object
        assert len(result.rollback_diffs) == 2  # Both have net changes
        assert result.time_range_description == "last 7 days"  # Description stored

    def test_entries_sorted_by_timestamp_before_analysis(self):
        """Out-of-order entries are sorted before analysis (oldest first)."""
        entries = [  # Deliberately out of order
            {
                "admin_id": "u1",
                "admin_name": "Alice",
                "timestamp": 5000,  # Later entry first
                "message": 'Update Template "T1"',
                "before": {"v": 2},
                "after": {"v": 3},
            },
            {
                "admin_id": "u1",
                "admin_name": "Alice",
                "timestamp": 1000,  # Earlier entry second
                "message": 'Update Template "T1"',
                "before": {"v": 1},
                "after": {"v": 2},
            },
        ]
        result = self.analyzer.analyze(entries)  # Analyse with unsorted input
        tl = result.admin_timelines[0]  # Single admin timeline
        assert tl.first_action == 1000  # Must find minimum timestamp
        assert tl.last_action == 5000  # Must find maximum timestamp
