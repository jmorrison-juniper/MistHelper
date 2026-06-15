"""Rate limiting utilities using PID control for Mist API calls.

Extracted from MistHelper.py per issue #217.
"""

import json
import logging
import math
import os
import time
from datetime import UTC, datetime

try:
    import numpy as np

    _has_numpy = True
except ImportError:
    np = None
    _has_numpy = False


def _get_tuning_data_file_path() -> str:
    """Determine the tuning data file path, preferring data/ directory."""
    data_dir = os.path.join(os.getcwd(), "data")
    try:
        os.makedirs(data_dir, exist_ok=True)
    except Exception:
        return os.path.join(os.getcwd(), "tuning_data.json")
    return os.path.join(data_dir, "tuning_data.json")


tuning_data_file = _get_tuning_data_file_path()


class RateLimitingUtils:
    """Centralized rate limiting utilities using PID control.

    Groups all rate limiting, delay calculation, and metrics logging
    functions. All methods are static to avoid unnecessary object
    instantiation.
    """

    @staticmethod
    def _clean_error_values(error_list):
        """Remove non-finite or non-numeric entries from an error list."""
        cleaned = []
        for error_value in error_list:
            if isinstance(error_value, (int, float)) and not (math.isnan(error_value) or math.isinf(error_value)):
                cleaned.append(float(error_value))
        return cleaned

    @staticmethod
    def _load_pid_tuning_data():
        """Load PID tuning data from file with comprehensive logging."""
        logging.debug("ENTRY: RateLimitingUtils._load_pid_tuning_data()")
        defaults = {"k_p": 0.1, "k_i": 0.0005, "error": [], "integral": 0.0}

        if not os.path.exists(tuning_data_file):
            logging.debug("File I/O: %s does not exist, using defaults", tuning_data_file)
            return defaults

        try:
            logging.debug("File I/O: Attempting to read PID tuning data from %s", tuning_data_file)
            with open(tuning_data_file) as file_handle:
                data = json.load(file_handle)
        except (json.JSONDecodeError, OSError, Exception) as load_error:
            logging.error("File I/O: Failed to load %s: %s. Using defaults.", tuning_data_file, load_error)
            return defaults

        if "error" in data and isinstance(data["error"], list):
            data["error"] = RateLimitingUtils._clean_error_values(data["error"])
        else:
            data["error"] = []

        logging.debug("File I/O: Successfully loaded PID tuning data from %s", tuning_data_file)
        return data

    @staticmethod
    def _save_pid_tuning_data(data):
        """Save PID tuning data to file with comprehensive logging."""
        logging.debug(
            "ENTRY: RateLimitingUtils._save_pid_tuning_data(data_keys=%s)",
            list(data.keys()) if data else [],
        )
        try:
            with open(tuning_data_file, "w") as file_handle:
                json.dump(data, file_handle, indent=2)
            logging.debug("File I/O: Successfully wrote PID tuning data to %s", tuning_data_file)
        except (OSError, Exception) as write_error:
            logging.error("File I/O: Error writing to %s: %s", tuning_data_file, write_error)
            raise

    @staticmethod
    def _adjust_gains(data):
        """Adjust PID gains based on the trend of recent errors."""
        recent_errors = data["error"][-10:]
        if not recent_errors:
            return

        error_trend = sum(recent_errors) / len(recent_errors)

        if error_trend > 0:
            data["k_p"] *= 1.05
            data["k_i"] *= 1.05
        elif error_trend < 0:
            data["k_p"] *= 0.95
            data["k_i"] *= 0.95

        data["k_p"] = min(max(data["k_p"], 1e-6), 1.0)
        data["k_i"] = min(max(data["k_i"], 1e-8), 0.01)

    @staticmethod
    def _compute_dynamic_alpha(errors, min_alpha=0.1, max_alpha=0.9):
        """Compute a dynamic smoothing factor alpha based on error standard deviation."""
        if len(errors) < 2:
            return 0.3

        try:
            recent_errors = errors[-10:]
            standard_deviation = RateLimitingUtils._calculate_std_dev(recent_errors)
            normalized = min(standard_deviation / 50, 1.0)
            alpha = min_alpha + (max_alpha - min_alpha) * normalized
            return round(alpha, 3)
        except Exception as alpha_error:
            logging.warning("Failed to compute dynamic alpha: %s. Using fallback.", alpha_error)
            return 0.3

    @staticmethod
    def _calculate_std_dev(values):
        """Calculate standard deviation of a list of numeric values."""
        if _has_numpy and np is not None:
            error_array = np.array(values, dtype=np.float64)
            return float(np.std(error_array))
        mean_val = sum(values) / len(values)
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        return variance**0.5

    @staticmethod
    def _resolve_metrics_filepath(filename):
        """Resolve the metrics log file path into the data/ directory."""
        if filename != "delay_metrics.json":
            return filename
        try:
            data_directory = "data"
            os.makedirs(data_directory, exist_ok=True)
            return os.path.join(data_directory, filename)
        except Exception as directory_error:
            logging.error("File I/O: Failed to ensure data directory: %s", directory_error)
            return filename

    @staticmethod
    def _read_existing_entries(filepath):
        """Read existing JSONL entries from a metrics log file."""
        if not os.path.exists(filepath):
            return []
        try:
            entries = []
            with open(filepath, encoding="utf-8") as file_handle:
                for line in file_handle:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
            logging.debug("File I/O: Loaded %d existing entries from %s", len(entries), filepath)
            return entries
        except (json.JSONDecodeError, OSError) as read_error:
            logging.warning("File I/O: Failed to read %s: %s. Starting fresh.", filepath, read_error)
            return []

    @staticmethod
    def _append_delay_metrics_log(
        delay_metrics, api_cache, tuning_data, filename="delay_metrics.json", max_entries=100
    ):
        """Append delay metrics, API cache, and tuning data to a JSON file.

        Each call writes a new line with a timestamped entry. Maintains
        only the last max_entries (default 100) to prevent unlimited growth.
        """
        filepath = RateLimitingUtils._resolve_metrics_filepath(filename)
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "delay_metrics": delay_metrics,
            "api_cache": api_cache,
            "tuning_data": tuning_data,
        }

        try:
            existing_entries = RateLimitingUtils._read_existing_entries(filepath)
            existing_entries.append(log_entry)
            if len(existing_entries) > max_entries:
                existing_entries = existing_entries[-max_entries:]

            with open(filepath, "w", encoding="utf-8") as file_handle:
                for entry in existing_entries:
                    json.dump(entry, file_handle)
                    file_handle.write("\n")
            logging.debug("File I/O: Successfully updated delay metrics in %s", filepath)
        except (OSError, Exception) as write_error:
            logging.error("File I/O: Failed to write delay metrics to %s: %s", filepath, write_error)

    @staticmethod
    def _refresh_api_usage(apisession, api_usage_cache, current_time):
        """Refresh API usage data from the Mist API."""
        try:
            import mistapi

            usage = mistapi.api.v1.self.usage.getSelfApiUsage(apisession).data
            api_usage_cache["used"] = usage.get("requests", 0)
            api_usage_cache["limit"] = usage.get("request_limit", 5000)
            api_usage_cache["last_updated"] = current_time
            api_usage_cache["perceived_requests"] = 0
            api_usage_cache["initialized"] = True
            logging.debug("API usage refreshed: %d/%d requests", api_usage_cache["used"], api_usage_cache["limit"])
        except Exception as api_error:
            logging.warning("Failed to refresh API usage data: %s. Using cached values.", api_error)

    @staticmethod
    def _estimate_api_usage(api_usage_cache, elapsed, current_time):
        """Estimate API usage growth when a refresh is not needed."""
        estimated_growth = round((api_usage_cache["limit"] / 3600) * elapsed)
        api_usage_cache["used"] += estimated_growth
        api_usage_cache["last_updated"] = current_time
        api_usage_cache["perceived_requests"] += 1
        logging.debug(
            "Using estimated API usage: %d/%d requests",
            api_usage_cache["used"],
            api_usage_cache["limit"],
        )

    @staticmethod
    def _needs_refresh(api_usage_cache, elapsed, now):
        """Determine whether the API usage cache needs a refresh."""
        return (
            not api_usage_cache["initialized"]
            or api_usage_cache["perceived_requests"] >= 100
            or elapsed > 60
            or (now.minute == 0 and now.second < 5)
        )

    @staticmethod
    def _calculate_pid_delay(
        used, limit, seconds_elapsed, delay_integral, k_p, k_i, previous_elapsed
    ):
        """Calculate the PID-controlled delay value.

        Returns a tuple of (sat_delay, error, delay_integral,
        back_calc_gain, seconds_elapsed).
        """
        seconds_remaining = max(3600 - seconds_elapsed, 1)
        ideal_used = (seconds_elapsed / 3600) * limit
        error = used - ideal_used

        if seconds_elapsed < previous_elapsed:
            logging.info(" Hour boundary crossed. Resetting integral.")
            delay_integral *= 0.5

        remaining_requests = max(limit - used, 1)
        base_delay = min(seconds_remaining / remaining_requests, 10)

        unsat_delay = base_delay + k_p * error + k_i * delay_integral
        sat_delay = max(min(unsat_delay, 10), 0.01)

        RateLimitingUtils._log_delay_level(sat_delay, base_delay, error, used, limit)

        back_calc_gain = min(max(abs(sat_delay - unsat_delay) / 10, 0.01), 0.5)
        decay_factor = 0.98
        delay_integral = delay_integral * decay_factor + back_calc_gain * (sat_delay - unsat_delay)
        delay_integral = max(min(delay_integral, 1000), -1000)

        return sat_delay, error, delay_integral, back_calc_gain, seconds_elapsed

    @staticmethod
    def _log_delay_level(sat_delay, base_delay, error, used, limit):
        """Log the calculated delay at the appropriate severity level."""
        if sat_delay > 2.0:
            logging.warning(
                "High delay: %.3fs (base: %.3fs, error: %.1f, used: %d/%d)",
                sat_delay,
                base_delay,
                error,
                used,
                limit,
            )
        elif sat_delay > 1.0:
            logging.info("Moderate delay: %.3fs (used: %d/%d)", sat_delay, used, limit)
        else:
            logging.debug("Normal delay: %.3fs (used: %d/%d)", sat_delay, used, limit)

    @staticmethod
    def _compute_smoothed_delay(sat_delay, error, error_history, smoothed_delay):
        """Compute the final smoothed delay using dynamic alpha.

        Returns a tuple of (smoothed_delay, delay_in_seconds,
        cleaned_error_history).
        """
        if isinstance(error, (int, float)) and not (math.isnan(error) or math.isinf(error)):
            error_history.append(float(error))

        cleaned = RateLimitingUtils._clean_error_values(error_history)
        alpha = RateLimitingUtils._compute_dynamic_alpha(cleaned)

        if not isinstance(alpha, (int, float)) or math.isnan(alpha) or math.isinf(alpha):
            logging.warning("Invalid alpha value: %s. Using fallback 0.3", alpha)
            alpha = 0.3

        if smoothed_delay is None:
            smoothed_delay = sat_delay
        else:
            smoothed_delay = alpha * sat_delay + (1 - alpha) * smoothed_delay

        delay_in_seconds = max(smoothed_delay, 0.01)
        logging.info("Rate limiting: sleeping for %.3f seconds", delay_in_seconds)
        return smoothed_delay, delay_in_seconds, cleaned

    @staticmethod
    def _reset_gains_if_needed(tuning_data):
        """Reset PID gains to defaults if they are out of valid bounds."""
        if (
            tuning_data["k_p"] < 1e-6
            or tuning_data["k_i"] < 1e-8
            or tuning_data["k_p"] > 1.0
            or tuning_data["k_i"] > 0.01
        ):
            logging.warning(
                "PID gains out of bounds, resetting: k_p=%s, k_i=%s",
                tuning_data["k_p"],
                tuning_data["k_i"],
            )
            tuning_data["k_p"] = 0.1
            tuning_data["k_i"] = 0.001

    @staticmethod
    def get_rate_limited_delay(
        smoothed_delay=None, apisession=None, api_usage_cache=None
    ):
        """Calculate an appropriate delay for API rate limiting using PID control.

        Args:
            smoothed_delay: Previous smoothed delay value (or None for first call).
            apisession: The mistapi APISession object for querying API usage.
            api_usage_cache: Mutable dict tracking API usage state between calls.

        Returns:
            Tuple of (smoothed_delay, delay_in_seconds).
        """
        logging.debug("ENTRY: get_rate_limited_delay(smoothed_delay=%s)", smoothed_delay)

        if api_usage_cache is None:
            logging.warning("api_usage_cache not provided, using fallback delay")
            return smoothed_delay, 0.5

        tuning_data = RateLimitingUtils._load_pid_tuning_data()
        RateLimitingUtils._reset_gains_if_needed(tuning_data)

        k_p = float(tuning_data["k_p"])
        k_i = float(tuning_data["k_i"])
        delay_integral = float(tuning_data.get("integral", 0.0))
        error_history = tuning_data.get("error", [])

        try:
            now = datetime.now(UTC)
            current_time = time.time()
            elapsed = current_time - api_usage_cache["last_updated"]
            previous_elapsed = float(api_usage_cache.get("previous_elapsed", elapsed))

            if RateLimitingUtils._needs_refresh(api_usage_cache, elapsed, now):
                RateLimitingUtils._refresh_api_usage(apisession, api_usage_cache, current_time)
            else:
                RateLimitingUtils._estimate_api_usage(api_usage_cache, elapsed, current_time)

            used = min(api_usage_cache["used"], api_usage_cache["limit"])
            limit = api_usage_cache["limit"]
            seconds_elapsed = now.minute * 60 + now.second + now.microsecond / 1_000_000

            sat_delay, error, delay_integral, back_calc_gain, seconds_elapsed = (
                RateLimitingUtils._calculate_pid_delay(
                    used, limit, seconds_elapsed, delay_integral, k_p, k_i, previous_elapsed
                )
            )
            api_usage_cache["previous_elapsed"] = seconds_elapsed

            smoothed_delay, delay_in_seconds, cleaned_history = (
                RateLimitingUtils._compute_smoothed_delay(
                    sat_delay, error, error_history, smoothed_delay
                )
            )

            tuning_data["error"] = cleaned_history[-20:]
            tuning_data["integral"] = delay_integral
            tuning_data["back_calc_gain"] = back_calc_gain
            RateLimitingUtils._adjust_gains(tuning_data)
            RateLimitingUtils._save_pid_tuning_data(tuning_data)

            delay_metrics = {
                "used": used,
                "limit": limit,
                "error": error,
                "base_delay": sat_delay,
                "final_delay": delay_in_seconds,
            }
            RateLimitingUtils._append_delay_metrics_log(delay_metrics, api_usage_cache, tuning_data)

            return smoothed_delay, delay_in_seconds

        except Exception as rate_error:
            logging.error("Failed to calculate dynamic delay: %s. Using 500ms fallback.", rate_error)
            return smoothed_delay, 0.5
