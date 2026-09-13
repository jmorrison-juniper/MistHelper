"""Unit tests for src.audit.filter module.

Covers AuditLogFilter.__init__, is_noise, filter, and filter_with_stats.
"""

from src.audit.filter import NOISE_PHRASES, AuditLogFilter


class TestAuditLogFilterInit:
    """Tests for AuditLogFilter constructor."""

    def test_default_noise_phrases_used_when_none_given(self):
        """Instantiating without arguments uses the module-level NOISE_PHRASES."""
        flt = AuditLogFilter()  # Use all defaults
        assert flt.noise_phrases is NOISE_PHRASES  # Must reference the module list

    def test_custom_noise_phrases_stored(self):
        """Custom noise phrases replace the defaults entirely."""
        custom = ["CustomNoise"]  # A minimal custom list
        flt = AuditLogFilter(noise_phrases=custom)  # Pass custom phrases
        assert flt.noise_phrases == custom  # Must store provided list


class TestIsNoise:
    """Tests for AuditLogFilter.is_noise method."""

    def setup_method(self):
        """Create a fresh default filter before each test."""
        self.flt = AuditLogFilter()  # Default filter for each test case

    def test_login_message_is_noise(self):
        """An entry containing 'Login ' is classified as noise."""
        entry = {"message": "Login admin@example.com"}  # Matches 'Login ' phrase
        assert self.flt.is_noise(entry) is True  # Login events are noise

    def test_logout_message_is_noise(self):
        """An entry containing 'Logout ' is classified as noise."""
        entry = {"message": "Logout admin@example.com"}  # Matches 'Logout ' phrase
        assert self.flt.is_noise(entry) is True  # Logout events are noise

    def test_packet_capture_is_noise(self):
        """Packet Capture started message is noise."""
        entry = {"message": "Packet Capture started on site AP123"}  # Matches phrase
        assert self.flt.is_noise(entry) is True  # Capture events are noise

    def test_update_vpn_without_before_key_is_noise(self):
        """'Update VPN' with no 'before' key in entry dict is cascade noise."""
        entry = {"message": "Update VPN tunnel config"}  # No 'before' key
        assert self.flt.is_noise(entry) is True  # Missing before = cascade event

    def test_update_vpn_with_before_key_is_not_noise(self):
        """'Update VPN' with a 'before' key present is a real configuration change."""
        entry = {  # 'before' key exists in entry
            "message": "Update VPN tunnel config",
            "before": {"some": "state"},  # Presence of 'before' = real change
        }
        assert self.flt.is_noise(entry) is False  # Has context, keep it

    def test_update_device_adopted_false_is_noise(self):
        """'Update Device' with adopted=False in both before and after is noise."""
        entry = {  # Spurious adoption state event
            "message": "Update Device",
            "before": {"adopted": False},  # Adoption flag unchanged
            "after": {"adopted": False},  # Still unchanged
        }
        assert self.flt.is_noise(entry) is True  # Adoption noise event

    def test_update_device_with_real_change_is_not_noise(self):
        """'Update Device' with meaningful before/after values is kept."""
        entry = {  # Genuine config change
            "message": "Update Device",
            "before": {"name": "OldAP"},  # Real field changed
            "after": {"name": "NewAP"},  # Different value after
        }
        assert self.flt.is_noise(entry) is False  # Real change must be kept

    def test_clean_template_update_is_not_noise(self):
        """A template update message does not match any noise phrase."""
        entry = {"message": 'Update Template "CorePolicy"'}  # Non-noise message
        assert self.flt.is_noise(entry) is False  # Template changes are meaningful

    def test_custom_filter_uses_only_custom_phrases(self):
        """A filter with custom phrases only blocks entries matching those phrases."""
        flt = AuditLogFilter(noise_phrases=["BlockThis"])  # Single custom phrase
        noise_entry = {"message": "BlockThis event"}  # Matches custom phrase
        clean_entry = {"message": "Login admin"}  # Default phrase, not in custom
        assert flt.is_noise(noise_entry) is True  # Custom phrase matched
        assert flt.is_noise(clean_entry) is False  # Default phrase not in custom list


class TestFilter:
    """Tests for AuditLogFilter.filter method."""

    def setup_method(self):
        """Create a default filter before each test."""
        self.flt = AuditLogFilter()  # Default filter instance

    def test_empty_input_returns_empty_list(self):
        """Filtering an empty list must return an empty list."""
        result = self.flt.filter([])  # Pass empty input
        assert result == []  # Must return empty list

    def test_all_noise_returns_empty(self):
        """When all entries are noise, the result is empty."""
        entries = [  # All entries match noise phrases
            {"message": "Login admin1"},
            {"message": "Logout admin1"},
        ]
        result = self.flt.filter(entries)  # Filter all-noise list
        assert result == []  # All entries removed

    def test_all_clean_entries_are_preserved(self):
        """Non-noise entries pass through unchanged."""
        entries = [  # No noise phrases in these messages
            {"message": 'Update Network "VLAN10"'},
            {"message": 'Create Template "CoreTemplate"'},
        ]
        result = self.flt.filter(entries)  # Should keep both
        assert len(result) == 2  # Both entries preserved
        assert result[0] is entries[0]  # Same object reference
        assert result[1] is entries[1]  # Order preserved

    def test_mixed_entries_keeps_only_clean(self):
        """A mix of noise and clean entries returns only the clean ones."""
        entries = [  # Mix of noise and non-noise
            {"message": "Login admin"},  # Noise
            {"message": 'Update Network "VLAN10"'},  # Clean
            {"message": "Packet Capture started"},  # Noise
            {"message": 'Update Template "T1"'},  # Clean
        ]
        result = self.flt.filter(entries)  # Filter mixed input
        assert len(result) == 2  # Only the two clean entries remain
        assert result[0]["message"] == 'Update Network "VLAN10"'  # First clean entry
        assert result[1]["message"] == 'Update Template "T1"'  # Second clean entry


class TestFilterWithStats:
    """Tests for AuditLogFilter.filter_with_stats method."""

    def setup_method(self):
        """Create a default filter before each test."""
        self.flt = AuditLogFilter()  # Default filter for each test

    def test_returns_tuple_with_list_and_dict(self):
        """Return value must be a (list, dict) tuple."""
        entries = [{"message": 'Update Template "T1"'}]  # One clean entry
        result = self.flt.filter_with_stats(entries)  # Call the method
        assert isinstance(result, tuple)  # Must be tuple type
        assert len(result) == 2  # Exactly two elements
        assert isinstance(result[0], list)  # First is filtered list
        assert isinstance(result[1], dict)  # Second is stats dict

    def test_stats_counts_are_accurate(self):
        """Stats dict must report original, kept, and removed counts correctly."""
        entries = [  # Mix of noise and clean
            {"message": "Login admin"},  # Noise
            {"message": 'Update Network "VLAN10"'},  # Clean
            {"message": "Logout admin"},  # Noise
        ]
        kept, stats = self.flt.filter_with_stats(entries)  # Unpack results
        assert stats["original_count"] == 3  # Input count
        assert stats["kept_count"] == 1  # One clean entry kept
        assert stats["removed_count"] == 2  # Two noise entries removed

    def test_no_noise_reports_zero_removed(self):
        """When no entries are noise, removed_count must be zero."""
        entries = [{"message": 'Create Network "Net1"'}]  # Clean entry
        kept, stats = self.flt.filter_with_stats(entries)  # Call method
        assert stats["removed_count"] == 0  # Nothing removed
        assert stats["kept_count"] == 1  # Entry was kept
        assert len(kept) == 1  # Kept list contains the entry

    def test_all_noise_reports_all_removed(self):
        """When all entries are noise, kept_count is zero."""
        entries = [  # Only noise entries
            {"message": "Login admin"},
            {"message": "Logout admin"},
        ]
        kept, stats = self.flt.filter_with_stats(entries)  # All removed
        assert stats["kept_count"] == 0  # Nothing kept
        assert stats["removed_count"] == 2  # Both removed
        assert kept == []  # Empty kept list
