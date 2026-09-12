"""Tests for the MistHelper performance monitoring foundation.

The tests check the event contract, the privacy rules, the bounded sink, and
the recorder gate. They prove that the default state emits no event and that a
sink failure never changes the result of a measured operation.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path

import pytest

from src.utils.performance.clock import Stopwatch
from src.utils.performance.event import (
    MAX_DIMENSIONS,
    MAX_MEASUREMENTS,
    SCHEMA_VERSION,
    EventError,
    EventSource,
    PerformanceEvent,
)
from src.utils.performance.privacy import REDACTED, bucket_size, scrub_value, status_class
from src.utils.performance.recorder import NULL_SPAN, Recorder, RecorderSettings

SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "specs"
    / "2448-misthelper-performance-monitoring"
    / "contracts"
    / "performance-event.schema.json"
)

SOURCE = EventSource(file="src/api/api_data_fetcher.py", symbol="execute", class_name="ApiFetcher")


def _event(**overrides: object) -> PerformanceEvent:
    """Return a valid event, with any field replaced for one test."""
    fields: dict[str, object] = {
        "event_type": "http",
        "monitor_type": "http_transport",
        "source": SOURCE,
        "status": "ok",
        "measurements": {"wall_ns": 1_500_000, "http.requests_total": 3},
        "dimensions": {"endpoint_template": "org_devices", "status_class": "2xx"},
    }
    fields.update(overrides)
    return PerformanceEvent(**fields)  # type: ignore[arg-type]


class TestEventContract:
    """Check the record against the committed JSON Schema."""

    def test_a_valid_event_builds_a_complete_record(self) -> None:
        """A valid event carries the version, the source, and every field."""
        record = _event().to_dict()
        assert record["schema_version"] == SCHEMA_VERSION
        assert record["event_type"] == "http"
        assert record["measurements"]["http.requests_total"] == 3

    def test_the_source_names_the_file_symbol_and_class(self) -> None:
        """The source block gives per-file, per-function, and per-class attribution."""
        source = _event().to_dict()["source"]
        assert source["file"] == "src/api/api_data_fetcher.py"
        assert source["symbol"] == "execute"
        assert source["class"] == "ApiFetcher"

    def test_a_function_outside_a_class_reports_a_null_class(self) -> None:
        """The schema allows a null class for a module level function."""
        plain = EventSource(file="src/utils/console.py", symbol="render")
        assert _event(source=plain).to_dict()["source"]["class"] is None

    def test_the_timestamp_is_utc_and_parses(self) -> None:
        """The builder fills a UTC timestamp that a reader can parse."""
        parsed = datetime.fromisoformat(_event().to_dict()["timestamp_utc"].replace("Z", "+00:00"))
        assert parsed.utcoffset().total_seconds() == 0

    def test_an_empty_source_file_is_refused(self) -> None:
        """An event must name the code location that produced it."""
        with pytest.raises(EventError, match="source file"):
            EventSource(file="", symbol="execute")

    def test_an_empty_source_symbol_is_refused(self) -> None:
        """An event must name the symbol that produced it."""
        with pytest.raises(EventError, match="source symbol"):
            EventSource(file="src/x.py", symbol="")

    @pytest.mark.parametrize("value", ["request", "metric", "", "HTTP"])
    def test_an_unknown_event_type_is_refused(self, value: str) -> None:
        """Only the eight named families may produce an event."""
        with pytest.raises(EventError, match="event_type"):
            _event(event_type=value)

    @pytest.mark.parametrize("value", ["success", "failed", ""])
    def test_an_unknown_status_is_refused(self, value: str) -> None:
        """The status vocabulary stays closed, which bounds the label set."""
        with pytest.raises(EventError, match="status"):
            _event(status=value)

    def test_an_event_without_a_measurement_is_refused(self) -> None:
        """The schema requires at least one measurement."""
        with pytest.raises(EventError, match="at least one measurement"):
            _event(measurements={})

    def test_a_negative_measurement_is_refused(self) -> None:
        """A count or a duration never falls below zero."""
        with pytest.raises(EventError, match="cannot be negative"):
            _event(measurements={"wall_ns": -1})

    def test_a_boolean_measurement_is_refused(self) -> None:
        """A bool is an int in Python, so the contract rejects it explicitly."""
        with pytest.raises(EventError, match="not a number"):
            _event(measurements={"wall_ns": True})

    def test_the_dimension_count_is_bounded(self) -> None:
        """The schema allows sixteen labels, and the seventeenth is refused."""
        too_many = {f"label{index}": "v" for index in range(MAX_DIMENSIONS + 1)}
        with pytest.raises(EventError, match="too many dimensions"):
            _event(dimensions=too_many)

    def test_the_measurement_count_is_bounded(self) -> None:
        """The schema allows thirty-two measurements, and the next one is refused."""
        too_many = {f"count{index}": index for index in range(MAX_MEASUREMENTS + 1)}
        with pytest.raises(EventError, match="too many measurements"):
            _event(measurements=too_many)

    @pytest.mark.parametrize("rate", [0, -0.5, 1.5])
    def test_an_out_of_range_sample_rate_is_refused(self, rate: float) -> None:
        """The schema requires a share above zero and at most one."""
        with pytest.raises(EventError, match="sample_rate"):
            _event(sample_rate=rate)

    @pytest.mark.parametrize("run_id", ["short", "a" * 65, "bad id!"])
    def test_an_invalid_run_id_is_refused(self, run_id: str) -> None:
        """The correlation identifier keeps a fixed bounded shape."""
        with pytest.raises(EventError, match="run_id"):
            _event(run_id=run_id)

    def test_a_valid_run_id_is_accepted(self) -> None:
        """A run identifier correlates the child events of one run."""
        assert _event(run_id="run-01234567").to_dict()["run_id"] == "run-01234567"

    def test_the_record_matches_the_published_schema(self) -> None:
        """Every produced field appears in the committed JSON Schema."""
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        record = _event().to_dict()
        assert set(record).issubset(set(schema["properties"]))
        assert set(schema["required"]).issubset(set(record))
        assert record["event_type"] in schema["properties"]["event_type"]["enum"]
        assert record["status"] in schema["properties"]["status"]["enum"]
        key_pattern = schema["properties"]["measurements"]["propertyNames"]["pattern"]
        for key in record["measurements"]:
            assert re.fullmatch(key_pattern, key)


class TestPrivacy:
    """Check that no private value reaches a metric label."""

    @pytest.mark.parametrize(
        "value",
        [
            "aa:bb:cc:dd:ee:ff",
            "10.20.30.40",
            "/home/someone/report.csv",
            "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
            "SELECT name FROM devices",
            "https://api.mist.com/v1/orgs?token=abc",
            "api_key",
        ],
    )
    def test_a_private_value_never_reaches_a_label(self, value: str) -> None:
        """Every private shape becomes the single redacted placeholder."""
        assert scrub_value(value) == REDACTED

    def test_an_unlisted_label_is_dropped_before_the_sink(self) -> None:
        """A label outside the allowlist never reaches the sink."""
        recorder = Recorder(RecorderSettings(level="base"))
        with recorder.span(SOURCE, family="operation") as span:
            span.label("org_id", "abc123").label("operation", "sync")
        record = json.loads(recorder.sink.drain()[0])
        assert record["dimensions"] == {"operation": "sync"}

    @pytest.mark.parametrize(
        ("count", "expected"),
        [(0, "tiny"), (10, "tiny"), (500, "medium"), (50_000, "huge"), (-1, "invalid")],
    )
    def test_a_count_becomes_a_fixed_bucket(self, count: int, expected: str) -> None:
        """A raw count becomes one of five fixed names."""
        assert bucket_size(count) == expected

    @pytest.mark.parametrize(
        ("code", "expected"), [(200, "2xx"), (429, "4xx"), (503, "5xx"), (99, "invalid")]
    )
    def test_a_status_code_becomes_a_family(self, code: int, expected: str) -> None:
        """An exact status code becomes one of five families."""
        assert status_class(code) == expected


class TestClocks:
    """Check the wall clock and the process CPU clock."""

    def test_a_sleep_adds_wall_time_and_almost_no_cpu_time(self) -> None:
        """The two clocks measure different costs."""
        with Stopwatch() as watch:
            time.sleep(0.05)
        assert watch.elapsed.wall_ns > 20_000_000
        assert watch.elapsed.cpu_ns < watch.elapsed.wall_ns

    def test_the_clock_never_hides_an_exception(self) -> None:
        """The exit path returns False, so the original error propagates."""
        with pytest.raises(RuntimeError, match="boom"), Stopwatch():
            raise RuntimeError("boom")

    def test_the_cpu_clock_can_be_disabled(self) -> None:
        """A disabled CPU clock reports zero rather than a wrong value."""
        with Stopwatch(measure_cpu=False) as watch:
            time.sleep(0.005)
        assert watch.elapsed.cpu_ns == 0
        assert watch.elapsed.wall_ns > 0


class TestRecorderGate:
    """Check the level gate, the sampling rule, and the sink bounds."""

    def test_the_default_recorder_emits_nothing(self) -> None:
        """The feature stays off until an operator selects a level."""
        recorder = Recorder()
        assert recorder.enabled is False
        with recorder.span(SOURCE):
            pass
        assert recorder.sink.drain() == []

    def test_a_forbidden_family_returns_the_shared_null_span(self) -> None:
        """A forbidden family allocates nothing and reads no clock."""
        recorder = Recorder(RecorderSettings(level="base"))
        assert recorder.span(SOURCE, family="diagnostic") is NULL_SPAN

    def test_an_allowed_family_returns_a_measuring_span(self) -> None:
        """The recorder still measures a family the level allows."""
        recorder = Recorder(RecorderSettings(level="base"))
        assert recorder.span(SOURCE, family="http") is not NULL_SPAN

    def test_the_null_span_never_hides_an_exception(self) -> None:
        """A disabled hook must not change the error behavior of the caller."""
        with pytest.raises(ValueError, match="bad"), NULL_SPAN:
            raise ValueError("bad")

    def test_every_event_carries_both_clock_measurements(self) -> None:
        """A hook always reports the wall cost and the process CPU cost."""
        recorder = Recorder(RecorderSettings(level="base"))
        with recorder.span(SOURCE, family="operation"):
            sum(range(1000))
        record = json.loads(recorder.sink.drain()[0])
        assert record["measurements"]["wall_ns"] > 0
        assert record["measurements"]["process_cpu_ns"] >= 0

    def test_an_error_records_the_class_and_not_the_message(self) -> None:
        """The label carries the exception class only."""
        recorder = Recorder(RecorderSettings(level="base"))
        with pytest.raises(ValueError), recorder.span(SOURCE, family="operation"):
            raise ValueError("a secret token appears here")
        record = json.loads(recorder.sink.drain()[0])
        assert record["status"] == "error"
        assert record["dimensions"]["error_class"] == "ValueError"
        assert "secret" not in json.dumps(record)

    def test_sampling_keeps_every_failure(self) -> None:
        """A very low sample rate still records an error."""
        recorder = Recorder(RecorderSettings(level="base", sample_rate=0.000001))
        with pytest.raises(RuntimeError), recorder.span(SOURCE, family="operation"):
            raise RuntimeError("failed")
        assert len(recorder.sink.drain()) == 1

    def test_the_queue_stays_bounded_and_counts_each_drop(self) -> None:
        """A full queue never grows, and it reports the lost events."""
        recorder = Recorder(RecorderSettings(level="base", capacity=2))
        for _ in range(5):
            with recorder.span(SOURCE, family="operation"):
                pass
        assert len(recorder.sink.drain()) == 2
        assert recorder.sink.dropped == 3

    def test_a_flush_writes_json_lines(self, tmp_path: Path) -> None:
        """Each flushed line is one valid JSON object."""
        recorder = Recorder(RecorderSettings(level="base"))
        with recorder.span(SOURCE, family="operation") as span:
            span.count("items_total", 7)
        target = tmp_path / "events" / "perf.jsonl"
        assert recorder.sink.flush_to(target) == 1
        assert json.loads(target.read_text(encoding="utf-8").strip())["event_type"] == "operation"

    def test_a_write_failure_never_raises(self, tmp_path: Path) -> None:
        """A blocked path fails the write and returns zero."""
        recorder = Recorder(RecorderSettings(level="base"))
        with recorder.span(SOURCE, family="operation"):
            pass
        blocked = tmp_path / "blocked"
        blocked.mkdir()
        assert recorder.sink.flush_to(blocked) == 0

    def test_repeated_failures_open_the_circuit(self, tmp_path: Path) -> None:
        """The sink stops writing after the failure limit."""
        recorder = Recorder(RecorderSettings(level="base"))
        blocked = tmp_path / "blocked"
        blocked.mkdir()
        for _ in range(6):
            with recorder.span(SOURCE, family="operation"):
                pass
            recorder.sink.flush_to(blocked)
        assert recorder.sink.circuit_open is True


class TestSettingsFromEnvironment:
    """Check the operator settings reader."""

    def test_an_empty_environment_keeps_the_feature_off(self) -> None:
        """The default state emits no event, so an absent variable means off."""
        assert RecorderSettings.from_env({}).level == "off"

    def test_a_known_level_is_accepted(self) -> None:
        """An operator selects a level by name."""
        settings = RecorderSettings.from_env({"MISTHELPER_PERF_LEVEL": " TARGETED "})
        assert settings.level == "targeted"

    @pytest.mark.parametrize("value", ["on", "1", "", "verbose"])
    def test_an_unknown_level_falls_back_to_off(self, value: str) -> None:
        """A typo must never enable a measurement by accident."""
        assert RecorderSettings.from_env({"MISTHELPER_PERF_LEVEL": value}).level == "off"

    @pytest.mark.parametrize(
        ("value", "expected"), [("0.5", 0.5), ("2.0", 1.0), ("bad", 1.0)]
    )
    def test_the_sample_rate_is_clamped(self, value: str, expected: float) -> None:
        """A bad rate is clamped or replaced, and it never raises at startup."""
        settings = RecorderSettings.from_env({"MISTHELPER_PERF_SAMPLE_RATE": value})
        assert settings.sample_rate == expected

    @pytest.mark.parametrize(("value", "expected"), [("10", 10), ("0", 1), ("999999", 65536)])
    def test_the_capacity_is_clamped(self, value: str, expected: int) -> None:
        """One setting must not exhaust the process memory."""
        assert RecorderSettings.from_env({"MISTHELPER_PERF_CAPACITY": value}).capacity == expected

    def test_the_cpu_clock_can_be_turned_off(self) -> None:
        """The CPU clock is the costly call on some hosts, so it is optional."""
        assert RecorderSettings.from_env({"MISTHELPER_PERF_CPU": "0"}).measure_cpu is False

    def test_an_unknown_level_name_is_refused_by_the_settings(self) -> None:
        """A direct caller receives a clear error for a bad level."""
        with pytest.raises(ValueError, match="unknown observability level"):
            RecorderSettings(level="loud")
