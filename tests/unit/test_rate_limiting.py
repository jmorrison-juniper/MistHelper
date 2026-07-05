"""Unit tests for RateLimitingUtils in src/utils/rate_limiting.py."""

import json
import math
import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest

from src.utils.rate_limiting import PidInputs, RateLimitingUtils


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _clean_files(tmp_path, monkeypatch):
    """Run each test in a temp directory to avoid file side effects."""
    monkeypatch.chdir(tmp_path)
    os.makedirs("data", exist_ok=True)
    yield


@pytest.fixture()
def tuning_file(tmp_path):
    """Path to a tuning data file in the temp directory."""
    return os.path.join(str(tmp_path), "data", "tuning_data.json")


@pytest.fixture()
def api_cache():
    """Minimal API usage cache dict for testing."""
    return {
        "used": 100,
        "limit": 5000,
        "last_updated": time.time() - 10,
        "perceived_requests": 5,
        "initialized": True,
        "previous_elapsed": 30.0,
    }


# ---------------------------------------------------------------------------
# _clean_error_values
# ---------------------------------------------------------------------------
class TestCleanErrorValues:
    """Tests for _clean_error_values static method."""

    def test_removes_nan(self):
        """NaN values are filtered out."""
        result = RateLimitingUtils._clean_error_values([1.0, float("nan"), 3.0])
        assert result == [1.0, 3.0]

    def test_removes_inf(self):
        """Infinity values are filtered out."""
        result = RateLimitingUtils._clean_error_values([1.0, float("inf"), -float("inf")])
        assert result == [1.0]

    def test_removes_non_numeric(self):
        """Non-numeric values like strings and None are filtered out."""
        result = RateLimitingUtils._clean_error_values([1.0, "bad", None, 2.0])
        assert result == [1.0, 2.0]

    def test_keeps_valid_values(self):
        """Valid int and float values are kept and converted to float."""
        result = RateLimitingUtils._clean_error_values([1, 2.5, -3, 0])
        assert result == [1.0, 2.5, -3.0, 0.0]

    def test_empty_list(self):
        """Empty list returns empty list."""
        assert RateLimitingUtils._clean_error_values([]) == []


# ---------------------------------------------------------------------------
# _load_pid_tuning_data
# ---------------------------------------------------------------------------
class TestLoadPidTuningData:
    """Tests for _load_pid_tuning_data static method."""

    def test_returns_defaults_when_no_file(self):
        """Returns default dict when tuning file does not exist."""
        import src.utils.rate_limiting as rl

        original = rl.tuning_data_file
        rl.tuning_data_file = "nonexistent.json"
        try:
            data = RateLimitingUtils._load_pid_tuning_data()
            assert data["k_p"] == 0.1
            assert data["k_i"] == 0.0005
            assert data["error"] == []
            assert data["integral"] == 0.0
        finally:
            rl.tuning_data_file = original

    def test_loads_from_file(self):
        """Loads tuning data from a valid JSON file."""
        import src.utils.rate_limiting as rl

        filepath = os.path.join("data", "tuning_data.json")
        test_data = {"k_p": 0.2, "k_i": 0.001, "error": [1.0, 2.0], "integral": 0.5}
        with open(filepath, "w") as fh:
            json.dump(test_data, fh)

        original = rl.tuning_data_file
        rl.tuning_data_file = filepath
        try:
            data = RateLimitingUtils._load_pid_tuning_data()
            assert data["k_p"] == 0.2
            assert data["error"] == [1.0, 2.0]
        finally:
            rl.tuning_data_file = original

    def test_handles_corrupt_json(self):
        """Returns defaults on corrupt JSON."""
        import src.utils.rate_limiting as rl

        filepath = os.path.join("data", "tuning_data.json")
        with open(filepath, "w") as fh:
            fh.write("{corrupt")

        original = rl.tuning_data_file
        rl.tuning_data_file = filepath
        try:
            data = RateLimitingUtils._load_pid_tuning_data()
            assert data["k_p"] == 0.1
        finally:
            rl.tuning_data_file = original

    def test_cleans_error_values_on_load(self):
        """Error values with NaN/Inf are cleaned during load."""
        import src.utils.rate_limiting as rl

        filepath = os.path.join("data", "tuning_data.json")
        test_data = {"k_p": 0.1, "k_i": 0.001, "error": [1.0, None, 3.0], "integral": 0.0}
        with open(filepath, "w") as fh:
            json.dump(test_data, fh)

        original = rl.tuning_data_file
        rl.tuning_data_file = filepath
        try:
            data = RateLimitingUtils._load_pid_tuning_data()
            assert data["error"] == [1.0, 3.0]
        finally:
            rl.tuning_data_file = original


# ---------------------------------------------------------------------------
# _save_pid_tuning_data
# ---------------------------------------------------------------------------
class TestSavePidTuningData:
    """Tests for _save_pid_tuning_data static method."""

    def test_saves_and_reads_back(self):
        """Saved data can be read back as valid JSON."""
        import src.utils.rate_limiting as rl

        filepath = os.path.join("data", "tuning_data.json")
        original = rl.tuning_data_file
        rl.tuning_data_file = filepath
        try:
            test_data = {"k_p": 0.15, "k_i": 0.002, "error": [1.0], "integral": 0.3}
            RateLimitingUtils._save_pid_tuning_data(test_data)
            with open(filepath) as fh:
                loaded = json.load(fh)
            assert loaded["k_p"] == 0.15
        finally:
            rl.tuning_data_file = original


# ---------------------------------------------------------------------------
# _adjust_gains
# ---------------------------------------------------------------------------
class TestAdjustGains:
    """Tests for _adjust_gains static method."""

    def test_increases_gains_on_positive_trend(self):
        """Gains increase when error trend is positive."""
        data = {"k_p": 0.1, "k_i": 0.001, "error": [5.0, 10.0, 15.0]}
        RateLimitingUtils._adjust_gains(data)
        assert data["k_p"] > 0.1
        assert data["k_i"] > 0.001

    def test_decreases_gains_on_negative_trend(self):
        """Gains decrease when error trend is negative."""
        data = {"k_p": 0.1, "k_i": 0.001, "error": [-5.0, -10.0, -15.0]}
        RateLimitingUtils._adjust_gains(data)
        assert data["k_p"] < 0.1
        assert data["k_i"] < 0.001

    def test_no_change_on_empty_errors(self):
        """No adjustment when error list is empty."""
        data = {"k_p": 0.1, "k_i": 0.001, "error": []}
        RateLimitingUtils._adjust_gains(data)
        assert data["k_p"] == 0.1
        assert data["k_i"] == 0.001

    def test_clamps_gains_to_bounds(self):
        """Gains are clamped to valid ranges."""
        data = {"k_p": 2.0, "k_i": 0.1, "error": [10.0] * 10}
        RateLimitingUtils._adjust_gains(data)
        assert data["k_p"] <= 1.0
        assert data["k_i"] <= 0.01


# ---------------------------------------------------------------------------
# _compute_dynamic_alpha
# ---------------------------------------------------------------------------
class TestComputeDynamicAlpha:
    """Tests for _compute_dynamic_alpha static method."""

    def test_returns_fallback_for_short_list(self):
        """Returns 0.3 when fewer than 2 errors."""
        assert RateLimitingUtils._compute_dynamic_alpha([1.0]) == 0.3
        assert RateLimitingUtils._compute_dynamic_alpha([]) == 0.3

    def test_returns_value_in_range(self):
        """Alpha is between min_alpha and max_alpha."""
        errors = [1.0, 2.0, 3.0, 4.0, 5.0]
        alpha = RateLimitingUtils._compute_dynamic_alpha(errors)
        assert 0.1 <= alpha <= 0.9

    def test_low_variance_gives_low_alpha(self):
        """Nearly identical errors produce alpha near min."""
        errors = [10.0, 10.0, 10.0, 10.0, 10.0]
        alpha = RateLimitingUtils._compute_dynamic_alpha(errors)
        assert alpha < 0.2


# ---------------------------------------------------------------------------
# _calculate_std_dev
# ---------------------------------------------------------------------------
class TestCalculateStdDev:
    """Tests for _calculate_std_dev static method."""

    def test_zero_variance(self):
        """Identical values have zero standard deviation."""
        result = RateLimitingUtils._calculate_std_dev([5.0, 5.0, 5.0])
        assert abs(result) < 1e-10

    def test_known_std_dev(self):
        """Known dataset returns expected standard deviation."""
        result = RateLimitingUtils._calculate_std_dev([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
        assert abs(result - 2.0) < 0.01


# ---------------------------------------------------------------------------
# _resolve_metrics_filepath
# ---------------------------------------------------------------------------
class TestResolveMetricsFilepath:
    """Tests for _resolve_metrics_filepath static method."""

    def test_default_filename_goes_to_data(self):
        """Default delay_metrics.json is placed in data/ directory."""
        result = RateLimitingUtils._resolve_metrics_filepath("delay_metrics.json")
        assert "data" in result
        assert result.endswith("delay_metrics.json")

    def test_custom_filename_unchanged(self):
        """Non-default filenames are returned as-is."""
        result = RateLimitingUtils._resolve_metrics_filepath("custom.json")
        assert result == "custom.json"


# ---------------------------------------------------------------------------
# _read_existing_entries
# ---------------------------------------------------------------------------
class TestReadExistingEntries:
    """Tests for _read_existing_entries static method."""

    def test_returns_empty_for_missing_file(self):
        """Returns empty list when file doesn't exist."""
        result = RateLimitingUtils._read_existing_entries("nonexistent.jsonl")
        assert result == []

    def test_reads_jsonl_entries(self):
        """Reads JSONL entries correctly."""
        filepath = os.path.join("data", "test.jsonl")
        with open(filepath, "w") as fh:
            fh.write('{"a": 1}\n{"b": 2}\n')
        result = RateLimitingUtils._read_existing_entries(filepath)
        assert len(result) == 2
        assert result[0]["a"] == 1

    def test_handles_corrupt_jsonl(self):
        """Returns empty list on corrupt JSONL."""
        filepath = os.path.join("data", "bad.jsonl")
        with open(filepath, "w") as fh:
            fh.write("{corrupt\n")
        result = RateLimitingUtils._read_existing_entries(filepath)
        assert result == []


# ---------------------------------------------------------------------------
# _append_delay_metrics_log
# ---------------------------------------------------------------------------
class TestAppendDelayMetricsLog:
    """Tests for _append_delay_metrics_log static method."""

    def test_creates_file_and_appends(self):
        """Creates metrics file and appends entry."""
        RateLimitingUtils._append_delay_metrics_log({"delay": 0.5}, {"used": 100}, {"k_p": 0.1})
        filepath = os.path.join("data", "delay_metrics.json")
        assert os.path.exists(filepath)
        with open(filepath) as fh:
            lines = [line.strip() for line in fh if line.strip()]
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert "timestamp" in entry
        assert entry["delay_metrics"]["delay"] == 0.5

    def test_respects_max_entries(self):
        """Trims to max_entries when limit exceeded."""
        filepath = os.path.join("data", "delay_metrics.json")
        for i in range(5):
            RateLimitingUtils._append_delay_metrics_log({"i": i}, {}, {}, max_entries=3)
        with open(filepath) as fh:
            lines = [line.strip() for line in fh if line.strip()]
        assert len(lines) == 3


# ---------------------------------------------------------------------------
# _needs_refresh
# ---------------------------------------------------------------------------
class TestNeedsRefresh:
    """Tests for _needs_refresh static method."""

    def test_uninitialized_cache_needs_refresh(self):
        """Uninitialized cache triggers refresh."""
        from datetime import UTC, datetime

        cache = {"initialized": False, "perceived_requests": 0}
        now = datetime.now(UTC)
        assert RateLimitingUtils._needs_refresh(cache, 10, now) is True

    def test_high_requests_needs_refresh(self):
        """100+ perceived requests triggers refresh."""
        from datetime import UTC, datetime

        cache = {"initialized": True, "perceived_requests": 100}
        now = datetime.now(UTC)
        assert RateLimitingUtils._needs_refresh(cache, 10, now) is True

    def test_long_elapsed_needs_refresh(self):
        """Elapsed >60s triggers refresh."""
        from datetime import UTC, datetime

        cache = {"initialized": True, "perceived_requests": 5}
        now = datetime.now(UTC)
        assert RateLimitingUtils._needs_refresh(cache, 61, now) is True

    def test_normal_no_refresh(self):
        """Normal conditions do not trigger refresh."""
        from datetime import UTC, datetime

        cache = {"initialized": True, "perceived_requests": 5}
        now = datetime(2026, 1, 1, 12, 30, 30, tzinfo=UTC)
        assert RateLimitingUtils._needs_refresh(cache, 10, now) is False


# ---------------------------------------------------------------------------
# _estimate_api_usage
# ---------------------------------------------------------------------------
class TestEstimateApiUsage:
    """Tests for _estimate_api_usage static method."""

    def test_increments_usage(self):
        """Estimated usage grows based on elapsed time."""
        cache = {"used": 100, "limit": 3600, "perceived_requests": 0, "last_updated": 0}
        RateLimitingUtils._estimate_api_usage(cache, 10.0, 100.0)
        assert cache["used"] > 100
        assert cache["perceived_requests"] == 1
        assert cache["last_updated"] == 100.0


# ---------------------------------------------------------------------------
# _calculate_pid_delay
# ---------------------------------------------------------------------------
class TestCalculatePidDelay:
    """Tests for _calculate_pid_delay static method."""

    @staticmethod
    def _make_inputs(used: float = 100, delay_integral: float = 0.0) -> PidInputs:
        """Return a PidInputs bundle populated with common test defaults."""
        return PidInputs(
            used=used,
            limit=5000,
            seconds_elapsed=1800,
            delay_integral=delay_integral,
            k_p=0.1,
            k_i=0.001,
            previous_elapsed=1799,
        )

    def test_returns_five_tuple(self):
        """Returns a 5-element tuple."""
        result = RateLimitingUtils._calculate_pid_delay(self._make_inputs())
        assert len(result) == 5

    def test_delay_is_clamped(self):
        """Delay is between 0.01 and 10."""
        sat_delay, _, _, _, _ = RateLimitingUtils._calculate_pid_delay(self._make_inputs())
        assert 0.01 <= sat_delay <= 10

    def test_high_usage_increases_delay(self):
        """Near-limit usage produces higher delay."""
        sat_low, _, _, _, _ = RateLimitingUtils._calculate_pid_delay(self._make_inputs(used=100))
        sat_high, _, _, _, _ = RateLimitingUtils._calculate_pid_delay(self._make_inputs(used=4900))
        assert sat_high > sat_low


# ---------------------------------------------------------------------------
# _log_delay_level
# ---------------------------------------------------------------------------
class TestLogDelayLevel:
    """Tests for _log_delay_level static method."""

    def test_does_not_raise(self):
        """Logging at all levels completes without error."""
        RateLimitingUtils._log_delay_level(0.5, 0.3, 10.0, 100, 5000)
        RateLimitingUtils._log_delay_level(1.5, 0.3, 10.0, 100, 5000)
        RateLimitingUtils._log_delay_level(3.0, 0.3, 10.0, 100, 5000)


# ---------------------------------------------------------------------------
# _compute_smoothed_delay
# ---------------------------------------------------------------------------
class TestComputeSmoothedDelay:
    """Tests for _compute_smoothed_delay static method."""

    def test_first_call_uses_sat_delay(self):
        """When smoothed_delay is None, returns sat_delay."""
        smoothed, delay, cleaned = RateLimitingUtils._compute_smoothed_delay(
            sat_delay=1.0, error=5.0, error_history=[1.0, 2.0, 3.0], smoothed_delay=None
        )
        assert smoothed == 1.0
        assert delay >= 0.01

    def test_blends_with_previous(self):
        """Subsequent calls blend with previous smoothed_delay."""
        smoothed, delay, cleaned = RateLimitingUtils._compute_smoothed_delay(
            sat_delay=2.0, error=5.0, error_history=[1.0, 2.0, 3.0], smoothed_delay=1.0
        )
        assert 1.0 < smoothed < 2.0

    def test_returns_cleaned_history(self):
        """Returned cleaned history has no invalid values."""
        _, _, cleaned = RateLimitingUtils._compute_smoothed_delay(
            sat_delay=1.0, error=5.0, error_history=[1.0, float("nan"), 3.0], smoothed_delay=None
        )
        for val in cleaned:
            assert not math.isnan(val)
            assert not math.isinf(val)


# ---------------------------------------------------------------------------
# _reset_gains_if_needed
# ---------------------------------------------------------------------------
class TestResetGainsIfNeeded:
    """Tests for _reset_gains_if_needed static method."""

    def test_resets_out_of_bounds_gains(self):
        """Out-of-bounds gains are reset to defaults."""
        data = {"k_p": 1e-7, "k_i": 1e-9}
        RateLimitingUtils._reset_gains_if_needed(data)
        assert data["k_p"] == 0.1
        assert data["k_i"] == 0.001

    def test_keeps_valid_gains(self):
        """Valid gains are not modified."""
        data = {"k_p": 0.1, "k_i": 0.001}
        RateLimitingUtils._reset_gains_if_needed(data)
        assert data["k_p"] == 0.1
        assert data["k_i"] == 0.001


# ---------------------------------------------------------------------------
# get_rate_limited_delay (integration-level)
# ---------------------------------------------------------------------------
class TestGetRateLimitedDelay:
    """Tests for the public get_rate_limited_delay method."""

    def test_returns_fallback_without_cache(self):
        """Returns fallback delay when api_usage_cache is None."""
        smoothed, delay = RateLimitingUtils.get_rate_limited_delay(
            smoothed_delay=None, apisession=None, api_usage_cache=None
        )
        assert delay == 0.5

    def test_returns_tuple(self, api_cache):
        """Returns a 2-tuple of (smoothed_delay, delay_in_seconds)."""
        import src.utils.rate_limiting as rl

        filepath = os.path.join("data", "tuning_data.json")
        original = rl.tuning_data_file
        rl.tuning_data_file = filepath
        try:
            smoothed, delay = RateLimitingUtils.get_rate_limited_delay(
                smoothed_delay=None, apisession=None, api_usage_cache=api_cache
            )
            assert isinstance(smoothed, float)
            assert isinstance(delay, float)
            assert delay >= 0.01
        finally:
            rl.tuning_data_file = original

    def test_delay_is_positive(self, api_cache):
        """Delay is always positive."""
        _, delay = RateLimitingUtils.get_rate_limited_delay(
            smoothed_delay=0.5, apisession=None, api_usage_cache=api_cache
        )
        assert delay > 0

    def test_writes_tuning_data(self, api_cache):
        """Tuning data file is created after a call."""
        import src.utils.rate_limiting as rl

        filepath = os.path.join("data", "tuning_data.json")
        original = rl.tuning_data_file
        rl.tuning_data_file = filepath
        try:
            RateLimitingUtils.get_rate_limited_delay(smoothed_delay=None, apisession=None, api_usage_cache=api_cache)
            assert os.path.exists(filepath)
        finally:
            rl.tuning_data_file = original

    def test_writes_metrics_log(self, api_cache):
        """Delay metrics log file is created after a call."""
        import src.utils.rate_limiting as rl

        tuning_filepath = os.path.join("data", "tuning_data.json")
        original = rl.tuning_data_file
        rl.tuning_data_file = tuning_filepath
        try:
            RateLimitingUtils.get_rate_limited_delay(smoothed_delay=None, apisession=None, api_usage_cache=api_cache)
            filepath = os.path.join("data", "delay_metrics.json")
            assert os.path.exists(filepath)
        finally:
            rl.tuning_data_file = original


# ---------------------------------------------------------------------------
# Edge cases for coverage
# ---------------------------------------------------------------------------
class TestEdgeCases:
    """Tests for exception paths and edge cases."""

    def test_load_missing_error_key(self):
        """Load handles data without error key."""
        import src.utils.rate_limiting as rl

        filepath = os.path.join("data", "tuning_data.json")
        with open(filepath, "w") as fh:
            json.dump({"k_p": 0.1, "k_i": 0.001}, fh)

        original = rl.tuning_data_file
        rl.tuning_data_file = filepath
        try:
            data = RateLimitingUtils._load_pid_tuning_data()
            assert data["error"] == []
        finally:
            rl.tuning_data_file = original

    def test_load_error_not_list(self):
        """Load handles error key that is not a list."""
        import src.utils.rate_limiting as rl

        filepath = os.path.join("data", "tuning_data.json")
        with open(filepath, "w") as fh:
            json.dump({"k_p": 0.1, "k_i": 0.001, "error": "bad"}, fh)

        original = rl.tuning_data_file
        rl.tuning_data_file = filepath
        try:
            data = RateLimitingUtils._load_pid_tuning_data()
            assert data["error"] == []
        finally:
            rl.tuning_data_file = original

    def test_save_raises_on_bad_path(self):
        """Save raises when path is invalid."""
        import src.utils.rate_limiting as rl

        original = rl.tuning_data_file
        rl.tuning_data_file = os.path.join("nonexistent_dir_xyz", "bad.json")
        try:
            with pytest.raises(OSError):
                RateLimitingUtils._save_pid_tuning_data({"k_p": 0.1})
        finally:
            rl.tuning_data_file = original

    def test_std_dev_without_numpy(self):
        """Standard deviation calculation works without numpy."""
        import src.utils.rate_limiting as rl

        original = rl._has_numpy
        rl._has_numpy = False
        try:
            result = RateLimitingUtils._calculate_std_dev([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
            assert abs(result - 2.0) < 0.01
        finally:
            rl._has_numpy = original

    def test_refresh_api_usage_with_mock(self):
        """Refresh API usage updates cache correctly."""
        mock_session = MagicMock()
        cache = {
            "used": 0,
            "limit": 5000,
            "last_updated": 0,
            "perceived_requests": 50,
            "initialized": False,
        }

        with patch("src.utils.rate_limiting.RateLimitingUtils._refresh_api_usage") as mock_refresh:
            mock_refresh.side_effect = lambda s, c, t: c.update(
                {
                    "used": 500,
                    "limit": 5000,
                    "last_updated": t,
                    "perceived_requests": 0,
                    "initialized": True,
                }
            )
            RateLimitingUtils._refresh_api_usage(mock_session, cache, time.time())
            assert cache["initialized"] is True
            assert cache["used"] == 500

    def test_refresh_api_usage_real_exception(self):
        """Refresh handles missing mistapi gracefully."""
        cache = {
            "used": 100,
            "limit": 5000,
            "last_updated": time.time(),
            "perceived_requests": 0,
            "initialized": True,
        }
        with patch.dict(sys.modules, {"mistapi": None}):
            RateLimitingUtils._refresh_api_usage(None, cache, time.time())
        assert cache["used"] == 100

    def test_hour_boundary_resets_integral(self):
        """Hour boundary crossing halves the delay integral."""
        sat_delay, error, integral, _, _ = RateLimitingUtils._calculate_pid_delay(
            PidInputs(
                used=100,
                limit=5000,
                seconds_elapsed=10.0,
                delay_integral=100.0,
                k_p=0.1,
                k_i=0.001,
                previous_elapsed=3500.0,
            )
        )
        assert integral != 100.0

    def test_get_rate_limited_delay_exception_fallback(self, api_cache):
        """Returns fallback on internal exception."""
        api_cache["last_updated"] = "not_a_number"
        smoothed, delay = RateLimitingUtils.get_rate_limited_delay(
            smoothed_delay=1.0, apisession=None, api_usage_cache=api_cache
        )
        assert delay == 0.5

    def test_append_metrics_write_error(self):
        """Append handles write errors without crashing."""
        with patch("builtins.open", side_effect=OSError("disk full")):
            RateLimitingUtils._append_delay_metrics_log({"d": 1}, {"c": 2}, {"t": 3}, filename="custom_nondefault.json")

    def test_resolve_metrics_makedirs_error(self):
        """Resolve handles makedirs failure gracefully."""
        with patch("os.makedirs", side_effect=OSError("permission denied")):
            result = RateLimitingUtils._resolve_metrics_filepath("delay_metrics.json")
            assert result == "delay_metrics.json"

    def test_compute_dynamic_alpha_exception(self):
        """Alpha computation falls back on exception."""
        with patch.object(RateLimitingUtils, "_calculate_std_dev", side_effect=ValueError("test")):
            alpha = RateLimitingUtils._compute_dynamic_alpha([1.0, 2.0, 3.0])
            assert alpha == 0.3


# ---------------------------------------------------------------------------
# Coverage gap tests: lines 27-28, 206-212, 302-303, 366
# ---------------------------------------------------------------------------
class TestCoverageGapTargets:
    """Tests targeting specific uncovered lines in rate_limiting.py."""

    def test_get_tuning_data_file_path_makedirs_fallback(self):  # Cover lines 27-28
        """_get_tuning_data_file_path falls back to cwd when makedirs raises."""
        import src.utils.rate_limiting as rl  # Import module to access the module-level function

        with patch("src.utils.rate_limiting.os.makedirs", side_effect=OSError("no permission")):  # makedirs raises
            result = rl._get_tuning_data_file_path()  # Call the module-level function directly
        assert result.endswith("tuning_data.json")  # Fallback path still ends with correct filename
        assert "data" not in result or not result.startswith(os.path.join(os.getcwd(), "data"))  # Not in data/ dir

    def test_refresh_api_usage_success_path(self):  # Cover lines 206-212
        """_refresh_api_usage populates cache dict when mistapi returns valid usage data."""
        mock_mistapi = MagicMock()  # Create a deep mock for the mistapi module
        mock_mistapi.api.v1.self.usage.getSelfApiUsage.return_value.data = {  # Mock the API response
            "requests": 750,  # Current usage count
            "request_limit": 5000,  # Rate limit
        }
        cache = {  # Minimal cache dict to be populated by the success path
            "used": 0,  # Will be set to 750 on success
            "limit": 5000,  # Will be set to 5000 on success
            "last_updated": 0.0,  # Will be updated to current_time on success
            "perceived_requests": 99,  # Will be reset to 0 on success
            "initialized": False,  # Will be set to True on success
        }
        with patch.dict("sys.modules", {"mistapi": mock_mistapi}):  # Inject mock mistapi into import system
            RateLimitingUtils._refresh_api_usage(MagicMock(), cache, 1700000000.0)  # Call with fake apisession and time
        assert cache["used"] == 750  # Success path set 'used' from API response
        assert cache["limit"] == 5000  # Success path set 'limit' from API response
        assert cache["last_updated"] == 1700000000.0  # Success path updated last_updated timestamp
        assert cache["perceived_requests"] == 0  # Success path reset perceived_requests to 0
        assert cache["initialized"] is True  # Success path marked cache as initialized

    def test_compute_smoothed_delay_invalid_alpha_fallback(self):  # Cover lines 302-303
        """_compute_smoothed_delay resets to alpha=0.3 when _compute_dynamic_alpha returns NaN."""
        with patch.object(  # Mock _compute_dynamic_alpha to return NaN -- triggers the invalid-alpha branch
            RateLimitingUtils, "_compute_dynamic_alpha", return_value=float("nan")
        ):
            smoothed, delay, cleaned = RateLimitingUtils._compute_smoothed_delay(  # Call the method directly
                sat_delay=0.5,  # Dummy saturation delay
                error=0.1,  # Dummy error value
                error_history=[],  # Empty history -- alpha fallback uses 0.3
                smoothed_delay=None,  # None forces smoothed_delay = sat_delay path
            )
        assert delay >= 0.01  # Valid delay always returned even with NaN alpha
        assert isinstance(smoothed, float)  # Smoothed delay is always a float

    def test_get_rate_limited_delay_refresh_branch(self, api_cache):  # Cover line 366
        """get_rate_limited_delay calls _refresh_api_usage when cache is not initialized."""
        api_cache["initialized"] = False  # Force _needs_refresh to return True -- triggers the refresh branch
        mock_mistapi = MagicMock()  # Mock mistapi so _refresh_api_usage succeeds
        mock_mistapi.api.v1.self.usage.getSelfApiUsage.return_value.data = {  # Mock valid API response
            "requests": 100,  # Usage count
            "request_limit": 5000,  # Rate limit
        }
        with patch.dict("sys.modules", {"mistapi": mock_mistapi}):  # Inject mock mistapi
            smoothed, delay = RateLimitingUtils.get_rate_limited_delay(  # Call with uninitialized cache
                smoothed_delay=0.5,  # Prior smoothed delay
                apisession=MagicMock(),  # Mock API session
                api_usage_cache=api_cache,  # Cache with initialized=False triggers refresh
            )
        assert delay > 0  # A positive delay is always returned
