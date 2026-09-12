"""Tests for the Prometheus renderer and the metrics cache."""

from __future__ import annotations

from typing import Any

import pytest

from src.metrics_gateway.cache import MINIMUM_REFRESH_SECONDS, MetricsCache
from src.metrics_gateway.catalog import MetricCatalog, MetricKind
from src.metrics_gateway.collector import MistMetricsCollector, MistStatsReader
from src.metrics_gateway.prometheus import NAME_PATTERN, PrometheusRenderer, escape_label_value, format_value
from src.metrics_gateway.samples import MetricSample, MetricSnapshot
from tests.unit.metrics_gateway.conftest import ORG_ID, StubResponse, build_overrides


def _snapshot(overrides: dict[str, Any] | None = None) -> MetricSnapshot:
    """Run one collector pass and return its snapshot.

    Args:
        overrides: The endpoint callables. The shared organization is the default.

    Returns:
        The snapshot of the pass.
    """
    reader = MistStatsReader(session=None, overrides=overrides or build_overrides())
    return MistMetricsCollector(reader, ORG_ID).collect()


class TestValueFormat:
    """The exposition format has its own spelling for the special numbers."""

    def test_a_whole_number_drops_the_decimal_tail(self) -> None:
        """A count reads better as `42` than as `42.0`."""
        assert format_value(42.0) == "42"

    def test_a_fraction_keeps_its_digits(self) -> None:
        """A ratio must not lose precision on the way to the scraper."""
        assert format_value(0.97) == "0.97"

    def test_an_infinity_takes_the_format_spelling(self) -> None:
        """Python writes `inf`, and a scraper rejects it."""
        assert format_value(float("inf")) == "+Inf"
        assert format_value(float("-inf")) == "-Inf"

    def test_a_missing_number_takes_the_format_spelling(self) -> None:
        """Python writes `nan`, and a scraper rejects it."""
        assert format_value(float("nan")) == "NaN"


class TestLabelEscape:
    """A label value must never end its own quotation early."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ('Branch "A"', 'Branch \\"A\\"'),
            ("C:\\sites", "C:\\\\sites"),
            ("line\nbreak", "line\\nbreak"),
            ("plain", "plain"),
        ],
    )
    def test_it_escapes_every_dangerous_character(self, raw: str, expected: str) -> None:
        """One unescaped character corrupts every line that follows it."""
        assert escape_label_value(raw) == expected

    def test_a_backslash_is_escaped_once(self) -> None:
        """The backslash rule must run first, or it would double the other escapes."""
        assert escape_label_value('\\"') == '\\\\\\"'


class TestPrometheusRenderer:
    """The rendered body must be a document a scraper accepts."""

    def test_every_family_carries_a_help_line_and_a_type_line(self) -> None:
        """A scraper prints the help text beside the alarm."""
        body = PrometheusRenderer().render(_snapshot())
        families = {line.split()[2] for line in body.splitlines() if line.startswith("# HELP")}
        types = {line.split()[2] for line in body.splitlines() if line.startswith("# TYPE")}
        assert families == types

    def test_it_never_names_the_info_type(self) -> None:
        """The format defines no `info` type, and a scraper drops a family that names one."""
        body = PrometheusRenderer().render(_snapshot())
        allowed = {"gauge", "counter", "histogram", "summary", "untyped"}
        for line in body.splitlines():
            if line.startswith("# TYPE"):
                assert line.split()[3] in allowed

    def test_a_family_appears_once(self) -> None:
        """A repeated help line makes a scraper drop the whole response."""
        body = PrometheusRenderer().render(_snapshot())
        headers = [line for line in body.splitlines() if line.startswith("# HELP")]
        assert len(headers) == len(set(headers))

    def test_every_reading_of_a_family_follows_its_header(self) -> None:
        """A scraper needs the readings of one family to arrive together."""
        body = PrometheusRenderer().render(_snapshot())
        lines = [line for line in body.splitlines() if not line.startswith("#")]
        names = [line.split("{")[0].split(" ")[0] for line in lines]
        assert names == sorted(names, key=lambda item: names.index(item))

    def test_a_site_name_with_a_quotation_mark_is_escaped(self) -> None:
        """A raw quotation mark would end the label value early."""
        body = PrometheusRenderer().render(_snapshot())
        assert 'site_name="Branch \\"A\\""' in body

    def test_the_body_ends_with_a_line_break(self) -> None:
        """The format needs a line break after the last reading."""
        assert PrometheusRenderer().render(_snapshot()).endswith("\n")

    def test_an_empty_snapshot_renders_an_empty_body(self) -> None:
        """A gateway that has read nothing must still answer a scrape."""
        assert PrometheusRenderer().render(MetricSnapshot()) == "\n"

    def test_every_reading_line_names_a_catalog_metric(self) -> None:
        """A line that names no catalog metric would carry no help text."""
        catalog = MetricCatalog()
        body = PrometheusRenderer().render(_snapshot())
        for line in body.splitlines():
            if line and not line.startswith("#"):
                assert catalog.by_name(line.split("{")[0].split(" ")[0]) is not None

    def test_a_sample_without_a_label_prints_its_name_alone(self) -> None:
        """A gateway health reading carries no label at all."""
        definition = MetricCatalog().by_name("mist_scrape_success")
        assert definition is not None
        sample = MetricSample(definition=definition, labels=(), value=1.0)
        body = PrometheusRenderer().render(MetricSnapshot(samples=(sample,)))
        assert "mist_scrape_success 1" in body

    def test_an_info_family_renders_as_a_gauge(self) -> None:
        """An informational reading is a constant 1, which is a gauge."""
        body = PrometheusRenderer().render(_snapshot())
        assert "# TYPE mist_site_info gauge" in body

    def test_a_counter_keeps_its_type(self) -> None:
        """A byte count only rises, so a scraper must see the counter type."""
        body = PrometheusRenderer().render(_snapshot())
        assert "# TYPE mist_device_received_bytes_total counter" in body

    def test_the_name_grammar_holds_for_a_rendered_line(self) -> None:
        """A name that breaks the grammar makes the scraper drop the response."""
        body = PrometheusRenderer().render(_snapshot())
        for line in body.splitlines():
            if line and not line.startswith("#"):
                assert NAME_PATTERN.match(line.split("{")[0].split(" ")[0])


class FakeClock:
    """A clock a test can move without waiting."""

    def __init__(self) -> None:
        """Start the clock at a round number."""
        self.now = 1_000.0

    def __call__(self) -> float:
        """Return the current time.

        Returns:
            The seconds the test has set.
        """
        return self.now


class CountingCollector(MistMetricsCollector):
    """A collector that records how many passes it ran."""

    def __init__(self, overrides: dict[str, Any]) -> None:
        """Build the collector over the stand-in endpoints.

        Args:
            overrides: The endpoint callables.
        """
        super().__init__(MistStatsReader(session=None, overrides=overrides), ORG_ID)
        self.passes = 0  # The count a test asserts on.

    def collect(self) -> MetricSnapshot:
        """Run one pass and count it.

        Returns:
            The snapshot of the pass.
        """
        self.passes += 1
        return super().collect()


class TestMetricsCache:
    """A poll must read memory, and a failed pass must keep the last good reading."""

    def test_the_first_poll_reads_mist_cloud(self) -> None:
        """The cache starts empty, so the first poll must fill it."""
        collector = CountingCollector(build_overrides())
        cache = MetricsCache(collector, clock=FakeClock())
        assert not cache.snapshot().is_empty()
        assert collector.passes == 1

    def test_a_second_poll_reads_the_cache(self) -> None:
        """A monitoring system polls far faster than the refresh interval."""
        collector = CountingCollector(build_overrides())
        cache = MetricsCache(collector, refresh_seconds=900, clock=FakeClock())
        cache.snapshot()
        cache.snapshot()
        assert collector.passes == 1

    def test_a_stale_reading_triggers_a_new_pass(self) -> None:
        """The cache must read Mist Cloud again once the interval has passed."""
        clock = FakeClock()
        collector = CountingCollector(build_overrides())
        cache = MetricsCache(collector, refresh_seconds=900, clock=clock)
        cache.snapshot()
        clock.now += 901
        cache.snapshot()
        assert collector.passes == 2

    def test_a_short_interval_is_raised_to_the_floor(self) -> None:
        """A shorter interval would spend the Mist rate limit budget on repeat readings."""
        cache = MetricsCache(CountingCollector(build_overrides()), refresh_seconds=1)
        assert cache.refresh_seconds == MINIMUM_REFRESH_SECONDS

    def test_a_failed_pass_keeps_the_last_good_reading(self) -> None:
        """A NOC that suddenly sees no devices cannot tell an outage from a failed refresh."""
        clock = FakeClock()
        overrides = build_overrides()
        collector = CountingCollector(overrides)
        cache = MetricsCache(collector, refresh_seconds=60, clock=clock)
        good = cache.snapshot()
        overrides["getOrgStats"] = _raise_connection_error
        clock.now += 61
        after = cache.snapshot()
        assert len(after.samples) >= len(good.samples) - 3
        assert _reading(after, "mist_org_sites") == 2

    def test_a_failed_pass_reports_the_failure(self) -> None:
        """The success reading is how a monitoring system learns that the cache is stale."""
        overrides = build_overrides()
        overrides["getOrgStats"] = _raise_connection_error
        cache = MetricsCache(CountingCollector(overrides), clock=FakeClock())
        assert _reading(cache.snapshot(), "mist_scrape_success") == 0.0

    def test_a_good_pass_reports_success(self) -> None:
        """A monitoring system must be able to trust a fresh reading."""
        cache = MetricsCache(CountingCollector(build_overrides()), clock=FakeClock())
        assert _reading(cache.snapshot(), "mist_scrape_success") == 1.0

    def test_the_age_grows_with_the_clock(self) -> None:
        """The age is measured at read time, so it cannot live in a frozen snapshot."""
        clock = FakeClock()
        cache = MetricsCache(CountingCollector(build_overrides()), refresh_seconds=900, clock=clock)
        cache.snapshot()
        clock.now += 120
        assert _reading(cache.snapshot(), "mist_scrape_age_seconds") == 120.0

    def test_an_empty_cache_reports_no_age(self) -> None:
        """An infinite age cannot be rendered, and a scraper reads it as a parse fault."""
        overrides = build_overrides()
        overrides["getOrgStats"] = _raise_connection_error
        cache = MetricsCache(CountingCollector(overrides), clock=FakeClock())
        assert _reading(cache.snapshot(), "mist_scrape_age_seconds") is None

    def test_a_forced_refresh_ignores_the_interval(self) -> None:
        """A background thread refreshes on its own schedule."""
        collector = CountingCollector(build_overrides())
        cache = MetricsCache(collector, refresh_seconds=900, clock=FakeClock())
        cache.refresh_now()
        cache.refresh_now()
        assert collector.passes == 2

    def test_the_health_readings_render(self) -> None:
        """A reading the renderer cannot print would break the whole response."""
        cache = MetricsCache(CountingCollector(build_overrides()), clock=FakeClock())
        body = PrometheusRenderer().render(cache.snapshot())
        assert "mist_scrape_success 1" in body

    def test_a_health_reading_is_a_gauge(self) -> None:
        """A gateway health reading rises and falls, so it must not be a counter."""
        definition = MetricCatalog().by_name("mist_scrape_age_seconds")
        assert definition is not None
        assert definition.kind is MetricKind.GAUGE


def _raise_connection_error(_session: Any, _org_id: str) -> StubResponse:
    """Fail the way an unreachable cloud fails.

    Args:
        _session: The unused session.
        _org_id: The unused organization identifier.

    Returns:
        Nothing. The function always raises.

    Raises:
        ConnectionError: Always.
    """
    raise ConnectionError("the cloud is unreachable")


def _reading(snapshot: MetricSnapshot, name: str) -> float | None:
    """Read one value out of a snapshot.

    Args:
        snapshot: The snapshot to search.
        name: The metric name.

    Returns:
        The value, or None when the snapshot holds no such reading.
    """
    for sample in snapshot.samples:
        if sample.definition.name == name:
            return sample.value
    return None
