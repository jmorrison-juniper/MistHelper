"""Tests for src.audit.analyzer module."""

import pytest

from src.audit.analyzer import AuditLogAnalyzer


@pytest.fixture
def analyzer():
    return AuditLogAnalyzer()


@pytest.fixture
def sample_entries():
    """Realistic filtered audit log entries."""
    return [
        {
            "timestamp": 1700000000,
            "admin_name": "alice@corp.com",
            "admin_id": "uid-alice",
            "message": 'Update Device "switch-lobby"',
            "before": {"port_config": {"ge-0/0/1": {"vlan": 10}}},
            "after": {"port_config": {"ge-0/0/1": {"vlan": 20}}},
        },
        {
            "timestamp": 1700000100,
            "admin_name": "bob@corp.com",
            "admin_id": "uid-bob",
            "message": 'Update Template "gw-template-east"',
            "before": {"dns": ["8.8.8.8"]},
            "after": {"dns": ["1.1.1.1"]},
        },
        {
            "timestamp": 1700000200,
            "admin_name": "alice@corp.com",
            "admin_id": "uid-alice",
            "message": 'Update Device "switch-lobby"',
            "before": {"port_config": {"ge-0/0/1": {"vlan": 20}}},
            "after": {"port_config": {"ge-0/0/1": {"vlan": 30}}},
        },
    ]


class TestAdminTimelines:
    """Test admin timeline grouping."""

    def test_groups_by_admin(self, analyzer, sample_entries):
        result = analyzer.analyze(sample_entries)
        assert len(result.admin_timelines) == 2

    def test_timeline_action_count(self, analyzer, sample_entries):
        result = analyzer.analyze(sample_entries)
        alice = next(t for t in result.admin_timelines if t.admin_name == "alice@corp.com")
        assert alice.action_count == 2

    def test_timeline_timestamps(self, analyzer, sample_entries):
        result = analyzer.analyze(sample_entries)
        alice = next(t for t in result.admin_timelines if t.admin_name == "alice@corp.com")
        assert alice.first_action == 1700000000
        assert alice.last_action == 1700000200

    def test_sorted_by_first_action(self, analyzer, sample_entries):
        result = analyzer.analyze(sample_entries)
        assert result.admin_timelines[0].first_action <= result.admin_timelines[1].first_action


class TestObjectChangelogs:
    """Test object changelog grouping."""

    def test_groups_by_object(self, analyzer, sample_entries):
        result = analyzer.analyze(sample_entries)
        assert len(result.object_changelogs) == 2  # switch-lobby and gw-template-east

    def test_multiple_changes_same_object(self, analyzer, sample_entries):
        result = analyzer.analyze(sample_entries)
        lobby = next(c for c in result.object_changelogs if c.object_name == "switch-lobby")
        assert len(lobby.changes) == 2

    def test_object_type_detection(self, analyzer, sample_entries):
        result = analyzer.analyze(sample_entries)
        lobby = next(c for c in result.object_changelogs if c.object_name == "switch-lobby")
        assert lobby.object_type == "Device"
        template = next(c for c in result.object_changelogs if c.object_name == "gw-template-east")
        assert template.object_type == "Template"


class TestRollbackDiffs:
    """Test rollback diff computation."""

    def test_detects_net_change(self, analyzer, sample_entries):
        result = analyzer.analyze(sample_entries)
        # switch-lobby: vlan 10 -> 20 -> 30 (net change: 10 vs 30)
        assert len(result.rollback_diffs) >= 1
        lobby_diff = next(
            (d for d in result.rollback_diffs if d.object_name == "switch-lobby"),
            None,
        )
        assert lobby_diff is not None
        assert lobby_diff.net_changed is True

    def test_no_diff_when_reverted(self, analyzer):
        """If object returns to original state, no rollback needed."""
        entries = [
            {
                "timestamp": 1700000000,
                "admin_name": "alice@corp.com",
                "admin_id": "uid-alice",
                "message": 'Update Device "switch-x"',
                "before": {"vlan": 10},
                "after": {"vlan": 20},
            },
            {
                "timestamp": 1700000100,
                "admin_name": "alice@corp.com",
                "admin_id": "uid-alice",
                "message": 'Update Device "switch-x"',
                "before": {"vlan": 20},
                "after": {"vlan": 10},
            },
        ]
        result = analyzer.analyze(entries)
        switch_diff = next(
            (d for d in result.rollback_diffs if d.object_name == "switch-x"),
            None,
        )
        # No net change since final == original
        assert switch_diff is None


class TestAnalysisMetadata:
    """Test analysis result metadata."""

    def test_total_entries(self, analyzer, sample_entries):
        result = analyzer.analyze(sample_entries, time_range_description="Last 3 days")
        assert result.total_entries == 3
        assert result.filtered_entries == 3
        assert result.time_range_description == "Last 3 days"

    def test_empty_input(self, analyzer):
        result = analyzer.analyze([])
        assert result.total_entries == 0
        assert len(result.admin_timelines) == 0
        assert len(result.object_changelogs) == 0
        assert len(result.rollback_diffs) == 0
