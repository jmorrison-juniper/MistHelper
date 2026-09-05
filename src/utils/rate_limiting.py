"""Rate limiting utilities using PID control for Mist API calls.

Extracted from MistHelper.py per issue #217. Groups PID-based adaptive
rate limiting logic behind a static-method facade so callers avoid
allocating per-request objects.
"""

from __future__ import annotations  # WHY: enable postponed evaluation for the frozen dataclass forward refs.

import json  # WHY: persist PID tuning + metrics as portable JSON records.
import logging  # WHY: centralised structured diagnostics for delay decisions.
import math  # WHY: NaN/Inf detection when sanitising error history samples.
import os  # WHY: cross-platform path composition and dir creation.
import time  # WHY: monotonic-ish wall clock for cache-age accounting.
from dataclasses import dataclass  # WHY: bundle PID inputs into a frozen slot object.
from datetime import UTC, datetime  # WHY: UTC-anchored hour-boundary detection.
from typing import Any  # WHY: typed dict payloads flowing through file I/O helpers.

try:  # WHY: numpy is optional. Fall back to pure-Python stdev when absent.
    import numpy as np  # WHY: vectorised std-dev calculation when available.

    _has_numpy = True  # WHY: gate numpy branches on import success.
except ImportError:  # WHY: environments without numpy remain functional.
    np = None  # type: ignore[assignment]  # WHY: sentinel keeps attribute lookups safe.
    _has_numpy = False  # WHY: mark fallback path required for std-dev math.

_DATA_DIR = "data"  # WHY: canonical relative directory for persisted state artefacts.
_TUNING_FILENAME = "tuning_data.json"  # WHY: on-disk PID tuning payload filename.
_METRICS_FILENAME = "delay_metrics.json"  # WHY: default JSONL-ish metrics log filename.
_DEFAULT_KP = 0.1  # WHY: canonical proportional gain default (see PID tuning notes).
_DEFAULT_KI = 0.0005  # WHY: canonical integral gain default derived empirically.
_RESET_KI = 0.001  # WHY: bounds-reset integral gain differs from cold-start default.
_KP_MIN, _KP_MAX = 1e-6, 1.0  # WHY: safe bounds for proportional gain.
_KI_MIN, _KI_MAX = 1e-8, 0.01  # WHY: safe bounds for integral gain.
_ALPHA_FALLBACK = 0.3  # WHY: smoothing factor used when history is short or numeric.
_ALPHA_MIN = 0.1  # WHY: lower bound of dynamic smoothing factor alpha.
_ALPHA_MAX = 0.9  # WHY: upper bound of dynamic smoothing factor alpha.
_STDDEV_NORMALISER = 50.0  # WHY: divisor mapping std-dev to normalised [0,1] alpha weight.
_DELAY_HARD_MIN = 0.01  # WHY: never-sleep-shorter clamp for rate delay.
_DELAY_HARD_MAX = 10.0  # WHY: never-sleep-longer clamp for rate delay.
_HOUR_SECONDS = 3600  # WHY: request-limit window is one clock hour.
_INTEGRAL_DECAY = 0.98  # WHY: leaky-integrator coefficient for anti-windup.
_INTEGRAL_LIMIT = 1000.0  # WHY: absolute clamp preventing runaway integral term.
_BACKCALC_MIN = 0.01  # WHY: lower bound for back-calculation gain scaling.
_BACKCALC_MAX = 0.5  # WHY: upper bound for back-calculation gain scaling.
_ADJUST_UP = 1.05  # WHY: multiplicative gain nudge when error trend is positive.
_ADJUST_DOWN = 0.95  # WHY: multiplicative gain nudge when error trend is negative.
_ADJUST_WINDOW = 10  # WHY: number of trailing errors used for gain adjustment trend.
_HISTORY_KEEP = 20  # WHY: trailing error samples persisted between calls.
_METRICS_MAX_DEFAULT = 100  # WHY: retention cap on delay metrics log rows.
_REFRESH_THRESHOLD_REQUESTS = 100  # WHY: perceived-request count that forces a live refresh.
_REFRESH_ELAPSED_SECONDS = 60  # WHY: cache-age (in seconds) that forces a live refresh.
_HOUR_ROLLOVER_SECOND_WINDOW = 5  # WHY: initial seconds of each hour where refresh is mandatory.
_ESTIMATE_GROWTH_WINDOW = 3600  # WHY: seconds normaliser for uniform growth estimator.
_FALLBACK_DELAY = 0.5  # WHY: safe delay used when PID pipeline errors out.
_DEFAULT_REQUEST_LIMIT = 5000  # WHY: fallback API request quota per hour if API omits it.
_MODERATE_DELAY = 1.0  # WHY: threshold at which delays become 'info' logged.
_HIGH_DELAY = 2.0  # WHY: threshold at which delays become 'warning' logged.
_HOUR_BOUNDARY_INTEGRAL_SCALE = 0.5  # WHY: soft-reset multiplier applied when hour rolls over.
_MICRO_DIVISOR = 1_000_000  # WHY: microsecond-to-second divisor for subsecond precision.


def _get_tuning_data_file_path() -> str:  # WHY: build absolute tuning-data path with graceful fallback.
    """Determine the tuning data file path, preferring data/ directory."""
    data_dir = os.path.join(os.getcwd(), _DATA_DIR)  # WHY: build absolute data/ path once.
    try:  # WHY: creation may fail on read-only filesystems. Fall back cleanly.
        os.makedirs(data_dir, exist_ok=True)  # WHY: ensure data/ exists idempotently.
    except OSError:  # WHY: narrow to filesystem errors. Other exceptions must bubble.
        return os.path.join(os.getcwd(), _TUNING_FILENAME)  # WHY: cwd fallback keeps writes possible.
    return os.path.join(data_dir, _TUNING_FILENAME)  # WHY: preferred data/ path when writable.


tuning_data_file = _get_tuning_data_file_path()  # WHY: module-level singleton path resolved at import.


@dataclass(frozen=True, slots=True)
class PidInputs:  # WHY: immutable per-call bundle of scalar inputs into the PID controller.
    """Frozen bundle of scalar inputs required for one PID delay evaluation."""

    used: float  # WHY: current API-usage counter for the active hour.
    limit: float  # WHY: hourly API request quota.
    seconds_elapsed: float  # WHY: seconds since the current hour started.
    delay_integral: float  # WHY: running integrator term across calls.
    k_p: float  # WHY: proportional gain from tuning data.
    k_i: float  # WHY: integral gain from tuning data.
    previous_elapsed: float  # WHY: seconds_elapsed from prior call for boundary detection.


@dataclass(frozen=True, slots=True)
class PidUpdate:  # WHY: bundle post-PID outputs the persist step needs, keeping param count low.
    """Frozen bundle of PID-cycle outputs required by the persistence step."""

    cleaned_history: list[float]  # WHY: sanitised trailing error samples ready to trim + persist.
    delay_integral: float  # WHY: updated integrator value to carry forward next call.
    back_calc_gain: float  # WHY: last back-calc gain surfaced for observability + tuning.
    delay_metrics: dict[str, Any]  # WHY: metrics row payload for JSONL log append.


def _defaults() -> dict[str, Any]:  # WHY: single source of truth for cold-start tuning data.
    """Return a fresh PID tuning-data defaults dict."""
    return {"k_p": _DEFAULT_KP, "k_i": _DEFAULT_KI, "error": [], "integral": 0.0}  # WHY: canonical cold-start state.


def _is_finite_number(value: Any) -> bool:  # WHY: shared predicate for input sanitisation across helpers.
    """Return True when value is a finite int/float (bool excluded)."""
    if isinstance(value, bool):  # WHY: bool is int subclass. Excluded to avoid True==1.0 pollution.
        return False  # WHY: reject boolean sentinel as non-numeric.
    if not isinstance(value, (int, float)):  # WHY: only numeric samples participate in PID math.
        return False  # WHY: reject non-numeric input types.
    return not (math.isnan(value) or math.isinf(value))  # WHY: exclude non-finite floats.


class RateLimitingUtils:  # WHY: static-method facade groups rate-limit helpers without per-call state.
    """Centralized rate limiting utilities using PID control.

    Groups all rate limiting, delay calculation, and metrics logging
    functions. All methods are static to avoid unnecessary object
    instantiation.
    """

    @staticmethod
    def _clean_error_values(error_list: list[Any]) -> list[float]:  # WHY: reused sanitiser across load + smooth paths.
        """Remove non-finite or non-numeric entries from an error list."""
        return [float(value) for value in error_list if _is_finite_number(value)]  # WHY: single-pass sanitiser.

    @staticmethod
    def _read_tuning_file() -> dict[str, Any] | None:  # WHY: split I/O from parsing so caller handles None default.
        """Read raw tuning-data JSON. Return None on any I/O or decode error."""
        if not os.path.exists(tuning_data_file):  # WHY: absence is the common cold-start case.
            logging.debug("File I/O: %s does not exist, using defaults", tuning_data_file)  # WHY: trace missing file.
            return None  # WHY: signal cold-start to caller.
        try:  # WHY: any decode/read failure falls back to defaults.
            logging.debug("File I/O: Attempting to read PID tuning data from %s", tuning_data_file)  # WHY: entry log.
            with open(tuning_data_file, encoding="utf-8") as file_handle:  # WHY: UTF-8 keeps the JSON portable.
                parsed: dict[str, Any] = json.load(file_handle)  # WHY: annotate result for downstream narrowing.
                return parsed  # WHY: surface the decoded tuning-data dict.
        except (json.JSONDecodeError, OSError) as load_error:  # WHY: narrow to expected failure classes.
            logging.error("File I/O: Failed to load %s: %s. Using defaults.", tuning_data_file, load_error)  # WHY: log
            return None  # WHY: signal fallback to defaults on error.

    @staticmethod
    def _load_pid_tuning_data() -> dict[str, Any]:  # WHY: public tuning-data loader with sanitised error history.
        """Load PID tuning data from file with comprehensive logging."""
        logging.debug("ENTRY: RateLimitingUtils._load_pid_tuning_data()")  # WHY: trace entry for diagnostics.
        data = RateLimitingUtils._read_tuning_file()  # WHY: reuse read helper for consistent error handling.
        if data is None:  # WHY: read failed or file missing -> defaults.
            return _defaults()  # WHY: cold-start defaults preserve caller contract.

        raw_errors = data.get("error")  # WHY: normalise to a sanitised list even when key missing/wrong type.
        data["error"] = (
            RateLimitingUtils._clean_error_values(raw_errors) if isinstance(raw_errors, list) else []
        )  # WHY: guard against corrupted 'error' payloads.

        logging.debug("File I/O: Successfully loaded PID tuning data from %s", tuning_data_file)  # WHY: success trace.
        return data  # WHY: surface sanitised tuning-data to caller.

    @staticmethod
    def _save_pid_tuning_data(data: dict[str, Any]) -> None:  # WHY: durable persistence for tuning state.
        """Save PID tuning data to file with comprehensive logging."""
        keys = list(data.keys()) if data else []  # WHY: log summary avoids leaking full payload.
        logging.debug("ENTRY: RateLimitingUtils._save_pid_tuning_data(data_keys=%s)", keys)  # WHY: entry trace.
        try:  # WHY: caller expects OSError on unwritable paths. Keep raise.
            with open(tuning_data_file, "w", encoding="utf-8") as file_handle:  # WHY: overwrite the prior snapshot.
                json.dump(data, file_handle, indent=2)  # WHY: indent keeps file diff-friendly.
            logging.debug("File I/O: Successfully wrote PID tuning data to %s", tuning_data_file)  # WHY: success log.
        except OSError as write_error:  # WHY: narrow catch. Upstream re-raise preserved.
            logging.error("File I/O: Error writing to %s: %s", tuning_data_file, write_error)  # WHY: surface failure.
            raise  # WHY: contract requires caller to see write failures.

    @staticmethod
    def _adjust_gains(data: dict[str, Any]) -> None:  # WHY: gentle nudging of gains toward the current error trend.
        """Adjust PID gains based on the trend of recent errors."""
        recent_errors = data["error"][-_ADJUST_WINDOW:]  # WHY: rolling window drives trend classification.
        if not recent_errors:  # WHY: no samples means no evidence to adjust from.
            return  # WHY: skip nudge when history is empty.

        error_trend = sum(recent_errors) / len(recent_errors)  # WHY: mean captures sign of recent bias.
        scale = _ADJUST_UP if error_trend > 0 else _ADJUST_DOWN if error_trend < 0 else 1.0  # WHY: table-lookup style.
        data["k_p"] = min(max(data["k_p"] * scale, _KP_MIN), _KP_MAX)  # WHY: scaled and clamped in one step.
        data["k_i"] = min(max(data["k_i"] * scale, _KI_MIN), _KI_MAX)  # WHY: parallel clamp for integral gain.

    @staticmethod
    def _compute_dynamic_alpha(
        errors: list[float], min_alpha: float = _ALPHA_MIN, max_alpha: float = _ALPHA_MAX
    ) -> float:  # WHY: adaptive smoothing responds to error dispersion.
        """Compute a dynamic smoothing factor alpha based on error standard deviation."""
        if len(errors) < 2:  # WHY: std-dev undefined for <2 samples. Use safe fallback.
            return _ALPHA_FALLBACK  # WHY: default smoothing when history is insufficient.

        try:  # WHY: numpy path may still raise on exotic inputs. Be defensive.
            standard_deviation = RateLimitingUtils._calculate_std_dev(errors[-_ADJUST_WINDOW:])  # WHY: window std-dev.
            normalized = min(standard_deviation / _STDDEV_NORMALISER, 1.0)  # WHY: cap at 1.0 for bounded interpolation.
            return round(min_alpha + (max_alpha - min_alpha) * normalized, 3)  # WHY: rounded for stable logs.
        except (ValueError, TypeError, ArithmeticError) as alpha_error:  # WHY: narrow expected numeric failures.
            logging.warning("Failed to compute dynamic alpha: %s. Using fallback.", alpha_error)  # WHY: surface issue.
            return _ALPHA_FALLBACK  # WHY: safe fallback on math failures.

    @staticmethod
    def _calculate_std_dev(values: list[float]) -> float:  # WHY: population std-dev, numpy-preferred with fallback.
        """Calculate standard deviation of a list of numeric values."""
        if _has_numpy and np is not None:  # WHY: prefer numpy when it is importable.
            return float(np.std(np.array(values, dtype=np.float64)))  # WHY: population std-dev matches fallback.
        mean_val = sum(values) / len(values)  # WHY: pure-Python fallback preserves behaviour identically.
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)  # WHY: population variance (not sample).
        return float(variance**0.5)  # WHY: sqrt(variance) -> std-dev, cast keeps mypy strict happy.

    @staticmethod
    def _resolve_metrics_filepath(filename: str) -> str:  # WHY: relocate canonical log into data/ dir when possible.
        """Resolve the metrics log file path into the data/ directory."""
        if filename != _METRICS_FILENAME:  # WHY: only the canonical filename is auto-relocated.
            return filename  # WHY: caller-supplied filenames pass through unchanged.
        try:  # WHY: makedirs may fail on read-only FS. Keep original name if so.
            os.makedirs(_DATA_DIR, exist_ok=True)  # WHY: ensure data/ exists idempotently.
            return os.path.join(_DATA_DIR, filename)  # WHY: relocated path prefers data/ dir.
        except OSError as directory_error:  # WHY: narrow catch. Fall back to bare filename.
            logging.error("File I/O: Failed to ensure data directory: %s", directory_error)  # WHY: surface FS issue.
            return filename  # WHY: fallback to bare filename when data/ unwritable.

    @staticmethod
    def _read_existing_entries(filepath: str) -> list[dict[str, Any]]:  # WHY: load existing JSONL history for append.
        """Read existing JSONL entries from a metrics log file."""
        if not os.path.exists(filepath):  # WHY: absence just means empty history.
            return []  # WHY: no prior entries to preserve.
        try:  # WHY: partial corruption should not crash the pipeline. Discard and start fresh.
            entries: list[dict[str, Any]] = []  # WHY: accumulator for decoded rows.
            with open(filepath, encoding="utf-8") as file_handle:  # WHY: explicit utf-8 for portability.
                for line in file_handle:  # WHY: line-oriented so we can skip blanks.
                    stripped = line.strip()  # WHY: tolerate trailing whitespace / blank lines.
                    if stripped:  # WHY: skip empty rows without decoding.
                        entries.append(json.loads(stripped))  # WHY: parse each JSONL row into a dict.
            logging.debug("File I/O: Loaded %d existing entries from %s", len(entries), filepath)  # WHY: trace count.
            return entries  # WHY: surface prior history to caller.
        except (json.JSONDecodeError, OSError) as read_error:  # WHY: narrow to expected classes.
            logging.warning("File I/O: Failed to read %s: %s. Starting fresh.", filepath, read_error)  # WHY: warn.
            return []  # WHY: fresh start on unreadable log file.

    @staticmethod
    def _build_log_entry(
        delay_metrics: dict[str, Any], api_cache: dict[str, Any], tuning_data: dict[str, Any]
    ) -> dict[str, Any]:  # WHY: standardise the JSONL row layout used by downstream consumers.
        """Construct a timestamped metrics log entry."""
        return {  # WHY: single dict layout keeps downstream consumers stable.
            "timestamp": datetime.now(UTC).isoformat(),  # WHY: ISO-8601 UTC anchors row.
            "delay_metrics": delay_metrics,  # WHY: preserve the per-call PID outputs.
            "api_cache": api_cache,  # WHY: capture usage cache snapshot for context.
            "tuning_data": tuning_data,  # WHY: capture tuning gains snapshot for reproducibility.
        }

    @staticmethod
    def _write_entries(filepath: str, entries: list[dict[str, Any]]) -> None:  # WHY: JSONL writer keeps rows atomic.
        """Overwrite the metrics log file with the provided entries."""
        with open(filepath, "w", encoding="utf-8") as file_handle:  # WHY: full rewrite keeps size-cap enforceable.
            for entry in entries:  # WHY: JSONL — one JSON object per line.
                json.dump(entry, file_handle)  # WHY: serialise the row.
                file_handle.write("\n")  # WHY: newline delimiter defines JSONL format.
        logging.debug("File I/O: Successfully updated delay metrics in %s", filepath)  # WHY: success trace.

    @staticmethod
    def _append_delay_metrics_log(
        delay_metrics: dict[str, Any],
        api_cache: dict[str, Any],
        tuning_data: dict[str, Any],
        filename: str = _METRICS_FILENAME,
        max_entries: int = _METRICS_MAX_DEFAULT,
    ) -> None:  # WHY: capped-history JSONL append for delay metrics.
        """Append delay metrics, API cache, and tuning data to a JSON file.

        Each call writes a new line with a timestamped entry. Maintains
        only the last max_entries (default 100) to prevent unlimited growth.
        """
        filepath = RateLimitingUtils._resolve_metrics_filepath(filename)  # WHY: relocate default log to data/.
        log_entry = RateLimitingUtils._build_log_entry(delay_metrics, api_cache, tuning_data)  # WHY: standardised row.
        try:  # WHY: any write failure is logged but must not crash the caller.
            entries = RateLimitingUtils._read_existing_entries(filepath)  # WHY: preserve prior history.
            entries.append(log_entry)  # WHY: new row appended after history.
            RateLimitingUtils._write_entries(filepath, entries[-max_entries:])  # WHY: cap retention in one slice.
        except OSError as write_error:  # WHY: narrow to filesystem errors.
            logging.error("File I/O: Failed to write delay metrics to %s: %s", filepath, write_error)  # WHY: log.

    @staticmethod
    def _refresh_api_usage(
        apisession: Any, api_usage_cache: dict[str, Any], current_time: float
    ) -> None:  # WHY: authoritative refresh from the Mist usage endpoint.
        """Refresh API usage data from the Mist API."""
        try:  # WHY: mistapi may be absent or the call may fail. Swallow gracefully.
            import mistapi  # WHY: lazy import keeps module import cheap and testable.

            usage = mistapi.api.v1.self.usage.getSelfApiUsage(apisession).data  # WHY: canonical usage endpoint.
            api_usage_cache["used"] = usage.get("requests", 0)  # WHY: default 0 when field absent.
            api_usage_cache["limit"] = usage.get("request_limit", _DEFAULT_REQUEST_LIMIT)  # WHY: fall back to default.
            api_usage_cache["last_updated"] = current_time  # WHY: reset cache-age accounting.
            api_usage_cache["perceived_requests"] = 0  # WHY: reset in-flight counter after live refresh.
            api_usage_cache["initialized"] = True  # WHY: mark cache as authoritative.
            logging.debug(
                "API usage refreshed: %d/%d requests", api_usage_cache["used"], api_usage_cache["limit"]
            )  # WHY: trace successful refresh.
        except Exception as api_error:  # WHY: mistapi may raise anything. Log and continue with cached values.
            logging.warning("Failed to refresh API usage data: %s. Using cached values.", api_error)  # WHY: warn.

    @staticmethod
    def _estimate_api_usage(
        api_usage_cache: dict[str, Any], elapsed: float, current_time: float
    ) -> None:  # WHY: local linear extrapolation between live refreshes.
        """Estimate API usage growth when a refresh is not needed."""
        estimated_growth = round((api_usage_cache["limit"] / _ESTIMATE_GROWTH_WINDOW) * elapsed)  # WHY: linear grow.
        api_usage_cache["used"] += estimated_growth  # WHY: increment usage counter locally.
        api_usage_cache["last_updated"] = current_time  # WHY: advance cache clock so next call estimates delta.
        api_usage_cache["perceived_requests"] += 1  # WHY: track in-flight request count for refresh gating.
        logging.debug(
            "Using estimated API usage: %d/%d requests", api_usage_cache["used"], api_usage_cache["limit"]
        )  # WHY: trace estimated-mode update.

    @staticmethod
    def _needs_refresh(
        api_usage_cache: dict[str, Any], elapsed: float, now: datetime
    ) -> bool:  # WHY: refresh decision consolidated for readability.
        """Determine whether the API usage cache needs a refresh."""
        return (
            not api_usage_cache["initialized"]  # WHY: cold-start always refreshes.
            or api_usage_cache["perceived_requests"] >= _REFRESH_THRESHOLD_REQUESTS  # WHY: too many local increments.
            or elapsed > _REFRESH_ELAPSED_SECONDS  # WHY: cache aged past acceptable window.
            or (now.minute == 0 and now.second < _HOUR_ROLLOVER_SECOND_WINDOW)  # WHY: force hour-rollover sync.
        )

    @staticmethod
    def _pid_error_and_base(inputs: PidInputs) -> tuple[float, float]:  # WHY: geometry-only calc split from PID math.
        """Compute the PID error term and unconstrained base delay."""
        ideal_used = (inputs.seconds_elapsed / _HOUR_SECONDS) * inputs.limit  # WHY: expected linear consumption curve.
        error = inputs.used - ideal_used  # WHY: positive means we are ahead of ideal, negative behind.
        seconds_remaining = max(_HOUR_SECONDS - inputs.seconds_elapsed, 1)  # WHY: avoid divide-by-zero at boundary.
        remaining_requests = max(inputs.limit - inputs.used, 1)  # WHY: prevent zero-division on saturation.
        base_delay = min(seconds_remaining / remaining_requests, _DELAY_HARD_MAX)  # WHY: fair-share pace, capped.
        return error, base_delay  # WHY: surface both scalars for downstream PID application.

    @staticmethod
    def _apply_integrator(
        delay_integral: float, unsat_delay: float, sat_delay: float
    ) -> tuple[float, float]:  # WHY: anti-windup update kept in a dedicated helper for clarity.
        """Advance the leaky integrator with anti-windup back-calculation."""
        back_calc_gain = min(
            max(abs(sat_delay - unsat_delay) / _DELAY_HARD_MAX, _BACKCALC_MIN), _BACKCALC_MAX
        )  # WHY: back-calc gain scales with saturation slack.
        updated = delay_integral * _INTEGRAL_DECAY + back_calc_gain * (sat_delay - unsat_delay)  # WHY: leaky term.
        clamped = max(min(updated, _INTEGRAL_LIMIT), -_INTEGRAL_LIMIT)  # WHY: bound integrator to prevent runaway.
        return clamped, back_calc_gain  # WHY: surface updated integrator plus derived gain.

    @staticmethod
    def _calculate_pid_delay(
        inputs: PidInputs,
    ) -> tuple[float, float, float, float, float]:  # WHY: bundle-first signature keeps params under limit.
        """Calculate the PID-controlled delay value.

        Returns a tuple of (sat_delay, error, delay_integral,
        back_calc_gain, seconds_elapsed).
        """
        delay_integral = inputs.delay_integral  # WHY: local mutable copy of integrator.
        if inputs.seconds_elapsed < inputs.previous_elapsed:  # WHY: hour rolled over between calls.
            logging.info(" Hour boundary crossed. Resetting integral.")  # WHY: surface soft reset for observability.
            delay_integral *= _HOUR_BOUNDARY_INTEGRAL_SCALE  # WHY: soft reset preserves partial history.

        error, base_delay = RateLimitingUtils._pid_error_and_base(inputs)  # WHY: geometry-only calc extracted.
        unsat_delay = base_delay + inputs.k_p * error + inputs.k_i * delay_integral  # WHY: canonical PID formula.
        sat_delay = max(min(unsat_delay, _DELAY_HARD_MAX), _DELAY_HARD_MIN)  # WHY: physical bounds on sleep length.

        RateLimitingUtils._log_delay_level(
            sat_delay, base_delay, error, inputs.used, inputs.limit
        )  # WHY: severity-aware delay log.
        delay_integral, back_calc_gain = RateLimitingUtils._apply_integrator(
            delay_integral, unsat_delay, sat_delay
        )  # WHY: anti-windup update in helper.
        return sat_delay, error, delay_integral, back_calc_gain, inputs.seconds_elapsed  # WHY: PID cycle results.

    @staticmethod
    def _log_delay_level(
        sat_delay: float, base_delay: float, error: float, used: float, limit: float
    ) -> None:  # WHY: severity ladder keeps log noise proportionate to backpressure.
        """Log the calculated delay at the appropriate severity level."""
        if sat_delay > _HIGH_DELAY:  # WHY: high-severity branch surfaces backpressure clearly.
            logging.warning(
                "High delay: %.3fs (base: %.3fs, error: %.1f, used: %d/%d)",
                sat_delay,
                base_delay,
                error,
                used,
                limit,
            )  # WHY: warning-level log for high delays.
        elif sat_delay > _MODERATE_DELAY:  # WHY: mid tier logs at info verbosity.
            logging.info(
                "Moderate delay: %.3fs (used: %d/%d)", sat_delay, used, limit
            )  # WHY: info-level log for moderate delays.
        else:  # WHY: normal path stays at debug to avoid log spam.
            logging.debug(
                "Normal delay: %.3fs (used: %d/%d)", sat_delay, used, limit
            )  # WHY: debug-level log for normal delays.

    @staticmethod
    def _resolve_alpha(cleaned: list[float]) -> float:  # WHY: centralise NaN/Inf handling around alpha computation.
        """Compute alpha and normalise to fallback on non-finite results."""
        alpha = RateLimitingUtils._compute_dynamic_alpha(cleaned)  # WHY: dynamic smoothing factor from history.
        if not _is_finite_number(alpha):  # WHY: NaN/Inf must not poison smoothing math.
            logging.warning("Invalid alpha value: %s. Using fallback 0.3", alpha)  # WHY: surface bad alpha value.
            return _ALPHA_FALLBACK  # WHY: safe fallback on non-finite alpha.
        return alpha  # WHY: propagate valid alpha to smoothing step.

    @staticmethod
    def _compute_smoothed_delay(
        sat_delay: float, error: float, error_history: list[float], smoothed_delay: float | None
    ) -> tuple[float, float, list[float]]:  # WHY: EWMA smoothing keeps sleep durations stable across bursts.
        """Compute the final smoothed delay using dynamic alpha.

        Returns a tuple of (smoothed_delay, delay_in_seconds,
        cleaned_error_history).
        """
        if _is_finite_number(error):  # WHY: only well-formed errors extend history.
            error_history.append(float(error))  # WHY: extend rolling error history for adaptive alpha.

        cleaned = RateLimitingUtils._clean_error_values(error_history)  # WHY: purge legacy NaN/Inf.
        alpha = RateLimitingUtils._resolve_alpha(cleaned)  # WHY: helper handles fallback path in one place.
        new_smoothed = (
            sat_delay if smoothed_delay is None else alpha * sat_delay + (1 - alpha) * smoothed_delay
        )  # WHY: first-call bootstrap vs EWMA update.
        delay_in_seconds = max(new_smoothed, _DELAY_HARD_MIN)  # WHY: enforce minimum sleep floor.
        logging.info("Rate limiting: sleeping for %.3f seconds", delay_in_seconds)  # WHY: surface applied delay.
        return new_smoothed, delay_in_seconds, cleaned  # WHY: propagate smoothed state and cleaned history.

    @staticmethod
    def _reset_gains_if_needed(tuning_data: dict[str, Any]) -> None:  # WHY: coerce corrupt tuning gains before math.
        """Reset PID gains to defaults if they are out of valid bounds."""
        out_of_bounds = (  # WHY: composite predicate keeps branch shallow.
            tuning_data["k_p"] < _KP_MIN
            or tuning_data["k_i"] < _KI_MIN
            or tuning_data["k_p"] > _KP_MAX
            or tuning_data["k_i"] > _KI_MAX
        )
        if not out_of_bounds:  # WHY: guard clause avoids nested reset block.
            return  # WHY: skip reset when gains are healthy.
        logging.warning(
            "PID gains out of bounds, resetting: k_p=%s, k_i=%s", tuning_data["k_p"], tuning_data["k_i"]
        )  # WHY: audit trail for gain resets.
        tuning_data["k_p"] = _DEFAULT_KP  # WHY: canonical restart proportional gain.
        tuning_data["k_i"] = _RESET_KI  # WHY: canonical restart integral gain.

    @staticmethod
    def _sync_cache_usage(
        apisession: Any, api_usage_cache: dict[str, Any], elapsed: float, now: datetime, current_time: float
    ) -> None:  # WHY: single dispatch for live-refresh vs local-estimate strategies.
        """Dispatch to live refresh or local estimate based on cache staleness."""
        if RateLimitingUtils._needs_refresh(api_usage_cache, elapsed, now):  # WHY: table-driven refresh choice.
            RateLimitingUtils._refresh_api_usage(apisession, api_usage_cache, current_time)  # WHY: authoritative sync.
        else:
            RateLimitingUtils._estimate_api_usage(
                api_usage_cache, elapsed, current_time
            )  # WHY: cheap local extrapolation.

    @staticmethod
    def _build_pid_inputs(
        api_usage_cache: dict[str, Any], tuning_data: dict[str, Any], now: datetime, previous_elapsed: float
    ) -> PidInputs:  # WHY: assemble immutable PidInputs snapshot per call.
        """Construct the frozen PidInputs bundle from current state."""
        used = min(api_usage_cache["used"], api_usage_cache["limit"])  # WHY: saturate at limit for stable math.
        limit = api_usage_cache["limit"]  # WHY: local alias mirrors PidInputs field.
        seconds_elapsed = now.minute * 60 + now.second + now.microsecond / _MICRO_DIVISOR  # WHY: subsecond precision.
        return PidInputs(  # WHY: immutable snapshot per call.
            used=used,
            limit=limit,
            seconds_elapsed=seconds_elapsed,
            delay_integral=float(tuning_data.get("integral", 0.0)),
            k_p=float(tuning_data["k_p"]),
            k_i=float(tuning_data["k_i"]),
            previous_elapsed=previous_elapsed,
        )

    @staticmethod
    def _build_delay_metrics(
        inputs: PidInputs, error: float, sat_delay: float, delay_in_seconds: float
    ) -> dict[str, Any]:  # WHY: reused metrics-row layout mirrors log consumer expectations.
        """Build the per-call delay metrics dict for logging."""
        return {  # WHY: metrics row layout mirrors log consumers.
            "used": inputs.used,  # WHY: current usage counter.
            "limit": inputs.limit,  # WHY: hourly limit.
            "error": error,  # WHY: PID error term.
            "base_delay": sat_delay,  # WHY: pre-smoothing saturated delay.
            "final_delay": delay_in_seconds,  # WHY: post-smoothing applied delay.
        }

    @staticmethod
    def _persist_state(
        tuning_data: dict[str, Any],
        api_usage_cache: dict[str, Any],
        update: PidUpdate,
    ) -> None:  # WHY: bundle-first signature keeps params under limit.
        """Persist tuning data, adjust gains, and append metrics log row."""
        tuning_data["error"] = update.cleaned_history[-_HISTORY_KEEP:]  # WHY: retain trailing window only.
        tuning_data["integral"] = update.delay_integral  # WHY: carry forward the integrator across calls.
        tuning_data["back_calc_gain"] = update.back_calc_gain  # WHY: expose for observability + tuning.
        RateLimitingUtils._adjust_gains(tuning_data)  # WHY: nudge gains toward trend.
        RateLimitingUtils._save_pid_tuning_data(tuning_data)  # WHY: durable across process restarts.
        RateLimitingUtils._append_delay_metrics_log(update.delay_metrics, api_usage_cache, tuning_data)  # WHY: log row.

    @staticmethod
    def _prepare_pipeline(
        apisession: Any, api_usage_cache: dict[str, Any]
    ) -> tuple[datetime, float]:  # WHY: consolidate clock + cache-sync bookkeeping before PID math.
        """Establish the time anchor and sync the usage cache for one PID cycle."""
        now = datetime.now(UTC)  # WHY: single time anchor for the whole cycle.
        current_time = time.time()  # WHY: wall-clock companion for cache accounting.
        elapsed = current_time - api_usage_cache["last_updated"]  # WHY: cache-age in seconds.
        previous_elapsed = float(api_usage_cache.get("previous_elapsed", elapsed))  # WHY: seed for boundary detect.
        RateLimitingUtils._sync_cache_usage(
            apisession, api_usage_cache, elapsed, now, current_time
        )  # WHY: live or estimated refresh.
        return now, previous_elapsed  # WHY: surface time anchor + prior elapsed to PID stage.

    @staticmethod
    def _evaluate_pid(
        api_usage_cache: dict[str, Any], tuning_data: dict[str, Any], now: datetime, previous_elapsed: float
    ) -> tuple[PidInputs, tuple[float, float, float, float, float]]:  # WHY: pair inputs+outputs for downstream fields.
        """Build the PidInputs bundle and evaluate one PID cycle."""
        inputs = RateLimitingUtils._build_pid_inputs(
            api_usage_cache, tuning_data, now, previous_elapsed
        )  # WHY: immutable snapshot.
        outputs = RateLimitingUtils._calculate_pid_delay(inputs)  # WHY: apply PID controller to snapshot.
        return inputs, outputs  # WHY: pair inputs with PID outputs for downstream helpers.

    @staticmethod
    def _run_pid_pipeline(
        apisession: Any,
        api_usage_cache: dict[str, Any],
        tuning_data: dict[str, Any],
        smoothed_delay: float | None,
    ) -> tuple[float, float]:  # WHY: single-entry orchestrator for one PID evaluation cycle.
        """Execute one PID cycle end-to-end and return (smoothed, delay_in_seconds)."""
        now, previous_elapsed = RateLimitingUtils._prepare_pipeline(apisession, api_usage_cache)  # WHY: time+sync.
        inputs, outputs = RateLimitingUtils._evaluate_pid(
            api_usage_cache, tuning_data, now, previous_elapsed
        )  # WHY: PID math step.
        sat_delay, error, delay_integral, back_calc_gain, seconds_elapsed = outputs  # WHY: unpack tuple locally.
        api_usage_cache["previous_elapsed"] = seconds_elapsed  # WHY: persist for next-call boundary detect.

        new_smoothed, delay_in_seconds, cleaned_history = RateLimitingUtils._compute_smoothed_delay(
            sat_delay, error, tuning_data.get("error", []), smoothed_delay
        )  # WHY: EWMA smoothing + cleaned history.
        update = PidUpdate(
            cleaned_history=cleaned_history,
            delay_integral=delay_integral,
            back_calc_gain=back_calc_gain,
            delay_metrics=RateLimitingUtils._build_delay_metrics(inputs, error, sat_delay, delay_in_seconds),
        )  # WHY: bundle persist inputs to keep _persist_state under param limit.
        RateLimitingUtils._persist_state(tuning_data, api_usage_cache, update)  # WHY: write tuning + metrics.
        return new_smoothed, delay_in_seconds  # WHY: propagate smoothed value + sleep target to caller.

    @staticmethod
    def _try_pipeline_or_fallback(
        apisession: Any,
        api_usage_cache: dict[str, Any],
        tuning_data: dict[str, Any],
        smoothed_delay: float | None,
    ) -> tuple[float | None, float]:  # WHY: wrap pipeline execution with a safety net returning the fallback delay.
        """Run the PID pipeline and fall back to a safe delay on any error."""
        try:  # WHY: any downstream failure must degrade gracefully to fallback.
            return RateLimitingUtils._run_pid_pipeline(
                apisession, api_usage_cache, tuning_data, smoothed_delay
            )  # WHY: happy path.
        except Exception as rate_error:  # WHY: safety net. Log and use fallback delay for any unexpected failure.
            logging.error(
                "Failed to calculate dynamic delay: %s. Using 500ms fallback.", rate_error
            )  # WHY: surface failure.
            return smoothed_delay, _FALLBACK_DELAY  # WHY: caller-safe fallback tuple.

    @staticmethod
    def get_rate_limited_delay(
        smoothed_delay: float | None = None,
        apisession: Any = None,
        api_usage_cache: dict[str, Any] | None = None,
    ) -> tuple[float | None, float]:  # WHY: single public entry point for delay calculation.
        """Calculate an appropriate delay for API rate limiting using PID control.

        Args:
            smoothed_delay: Previous smoothed delay value (or None for first call).
            apisession: The mistapi APISession object for querying API usage.
            api_usage_cache: Mutable dict tracking API usage state between calls.

        Returns:
            Tuple of (smoothed_delay, delay_in_seconds).
        """
        logging.debug("ENTRY: get_rate_limited_delay(smoothed_delay=%s)", smoothed_delay)  # WHY: trace entry.
        if api_usage_cache is None:  # WHY: fail-safe when caller omits the shared cache.
            logging.warning("api_usage_cache not provided, using fallback delay")  # WHY: surface missing cache.
            return smoothed_delay, _FALLBACK_DELAY  # WHY: cannot run PID without cache. Return safe fallback.

        tuning_data = RateLimitingUtils._load_pid_tuning_data()  # WHY: seed tuning state from disk.
        RateLimitingUtils._reset_gains_if_needed(tuning_data)  # WHY: coerce corrupt gains before math.
        return RateLimitingUtils._try_pipeline_or_fallback(
            apisession, api_usage_cache, tuning_data, smoothed_delay
        )  # WHY: safe execution of PID cycle.


class AdaptivePacer:  # WHY: hold the PID state that a sequential write loop must carry between iterations.
    """Pace a sequential write loop with the adaptive PID rate limiter.

    A bulk write loop must wait between requests to stay below the Mist
    per-org quota. A fixed sleep cannot read the real quota. A fixed sleep
    therefore wastes headroom on a small org, and it still permits HTTP 429
    on a large org that shares the quota with another tool. This class
    keeps the smoothed delay between iterations. It then applies the delay
    that RateLimitingUtils.get_rate_limited_delay computes.
    """

    def __init__(
        self,
        apisession: Any = None,
        api_usage_cache: dict[str, Any] | None = None,
        enabled: bool = True,
    ) -> None:  # WHY: one pacer instance owns one loop, so the PID state cannot leak between loops.
        """Store the session, the shared usage cache, and the enable flag."""
        self._apisession = apisession  # WHY: the PID pipeline reads the quota through this session.
        self._api_usage_cache = api_usage_cache  # WHY: shared cache keeps every menu on one quota view.
        self._enabled = enabled  # WHY: a dry run must not spend wall-clock time on a sleep.
        self._smoothed_delay: float | None = None  # WHY: None marks the first call of this loop.
        logging.debug(
            "AdaptivePacer created (enabled=%s, cache_present=%s)", enabled, api_usage_cache is not None
        )  # WHY: record the pacing decision for a later audit of a bulk run.

    @property
    def smoothed_delay(self) -> float | None:  # WHY: expose read-only state so a test can assert the PID carry-over.
        """Return the current smoothed delay in seconds, or None before the first call."""
        return self._smoothed_delay  # WHY: callers must not mutate the PID state directly.

    def next_delay(self) -> float:  # WHY: split the computation from the sleep so a test can run without waiting.
        """Compute the next delay in seconds and keep the smoothed PID state."""
        self._smoothed_delay, delay_in_seconds = RateLimitingUtils.get_rate_limited_delay(
            self._smoothed_delay, self._apisession, self._api_usage_cache
        )  # WHY: the helper returns the new smoothed value and the delay to apply.
        return delay_in_seconds  # WHY: caller decides whether to sleep for this delay.

    def pace(self) -> float:  # WHY: single call site replaces the hard-coded time.sleep in every bulk write loop.
        """Wait for the computed delay and return the number of seconds waited."""
        if not self._enabled:  # WHY: a disabled pacer reports zero wait and performs no sleep.
            return 0.0  # WHY: keep the return type stable for the caller.
        delay_in_seconds = self.next_delay()  # WHY: ask the PID controller for the current quota-aware delay.
        time.sleep(delay_in_seconds)  # WHY: hold the loop for the delay the controller selected.
        return delay_in_seconds  # WHY: report the wait so a caller can log or assert it.
