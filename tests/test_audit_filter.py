"""Tests for src.audit.filter module."""

import pytest

from src.audit.filter import AuditLogFilter


@pytest.fixture
def log_filter():
    return AuditLogFilter()


@pytest.fixture
def noise_entries():
    """Entries that should be filtered out."""
    return [
        {"message": "Accessed Org Settings", "admin_name": "admin@test.com"},
        {"message": "Login via SSO", "admin_name": "admin@test.com"},
        {"message": "Logout ", "admin_name": "admin@test.com"},
        {"message": "Packet Capture started", "admin_name": "admin@test.com"},
        {"message": "Invoked Webshell on device", "admin_name": "admin@test.com"},
        {"message": "Clearing sessions for user", "admin_name": "admin@test.com"},
        {"message": "Device manually restarted", "admin_name": "admin@test.com"},
        {"message": "Getting device config", "admin_name": "admin@test.com"},
    ]


@pytest.fixture
def real_entries():
    """Entries that should be kept."""
    return [
        {
            "message": 'Update Device "switch-lobby"',
            "admin_name": "admin@test.com",
            "before": {"name": "old"},
            "after": {"name": "new"},
        },
        {
            "message": 'Update Template "gateway-prod"',
            "admin_name": "admin@test.com",
            "before": {"networks": []},
            "after": {"networks": ["vlan10"]},
        },
        {
            "message": 'Create Network "VLAN-100"',
            "admin_name": "admin@test.com",
        },
    ]


class TestBasicFiltering:
    """Test noise removal."""

    def test_removes_noise(self, log_filter, noise_entries):
        result = log_filter.filter(noise_entries)
        assert len(result) == 0

    def test_keeps_real(self, log_filter, real_entries):
        result = log_filter.filter(real_entries)
        assert len(result) == 3

    def test_mixed(self, log_filter, noise_entries, real_entries):
        mixed = noise_entries + real_entries
        result = log_filter.filter(mixed)
        assert len(result) == 3


class TestSpecialCases:
    """Test special filtering rules."""

    def test_update_vpn_no_diff_filtered(self, log_filter):
        entries = [{"message": "Update VPN config", "admin_name": "a@b.com"}]
        result = log_filter.filter(entries)
        assert len(result) == 0

    def test_update_vpn_with_diff_kept(self, log_filter):
        entries = [
            {
                "message": "Update VPN config",
                "admin_name": "a@b.com",
                "before": {"key": "old"},
                "after": {"key": "new"},
            }
        ]
        result = log_filter.filter(entries)
        assert len(result) == 1

    def test_update_device_adopted_false_filtered(self, log_filter):
        entries = [
            {
                "message": "Update Device",
                "admin_name": "a@b.com",
                "before": {"adopted": False},
                "after": {"adopted": False},
            }
        ]
        result = log_filter.filter(entries)
        assert len(result) == 0

    def test_update_device_real_change_kept(self, log_filter):
        entries = [
            {
                "message": "Update Device",
                "admin_name": "a@b.com",
                "before": {"name": "old"},
                "after": {"name": "new"},
            }
        ]
        result = log_filter.filter(entries)
        assert len(result) == 1


class TestFilterWithStats:
    """Test filter_with_stats method."""

    def test_returns_stats(self, log_filter, noise_entries, real_entries):
        mixed = noise_entries + real_entries
        filtered, stats = log_filter.filter_with_stats(mixed)
        assert stats["kept_count"] == 3
        assert stats["removed_count"] == len(noise_entries)
        assert stats["original_count"] == len(mixed)
        assert len(filtered) == 3
