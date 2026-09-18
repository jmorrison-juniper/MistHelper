"""Property tests for the rogue DHCP merge rule and the record normalizer.

The unit tests pin the behavior for the record shapes Mist documents. These
property tests widen the input space, so a shape the catalog does not show
still holds the two invariants an operator depends on: the merge never invents
a row, and every source produces the same column set.
"""

from __future__ import annotations  # Postponed annotations keep the type hints light.

import pytest  # Skips the module when Hypothesis is not installed.

pytest.importorskip("hypothesis")  # Skip these tests when Hypothesis is absent.

from hypothesis import given, settings  # The decorator that drives the property tests.
from hypothesis import strategies as st  # Builds the input strategies.

from src.security.rogue_dhcp.records import (
    SOURCE_ORG_ALARM,
    SOURCE_ORG_EVENT,
    STATE_ACTIVE,
    STATE_HISTORICAL,
    RogueDhcpFinding,
    RogueDhcpFindingMerger,
    RogueDhcpRecordNormalizer,
)

WINDOW_END = 1_700_000_000.0  # A fixed end time keeps every state decision deterministic.

# Issue #1803: a full-suite run applies memory and CPU pressure that an isolated run
# does not. Hypothesis reports a per-example deadline breach as a failure, so the
# deadline is disabled here. The assertions are unchanged, so a real defect still fails.
_NO_DEADLINE = settings(deadline=None)

_IDENTIFIER = st.from_regex(r"[a-z0-9-]{1,12}", fullmatch=True)  # Site, MAC, and port identifiers.
_TIMESTAMP = st.floats(min_value=WINDOW_END - (30 * 86400), max_value=WINDOW_END, allow_nan=False)


def build_normalizer() -> RogueDhcpRecordNormalizer:
    """Return a normalizer bound to the fixed property window."""
    return RogueDhcpRecordNormalizer("org-1", "2026-09-18T00:00:00+00:00", WINDOW_END)


_ALARM = st.fixed_dictionaries(
    {
        "type": st.just("sw_rogue_dhcp_server_detected"),
        "site_id": _IDENTIFIER,
        "switches": st.lists(_IDENTIFIER, min_size=0, max_size=2),
        "port_id": _IDENTIFIER,
        "timestamp": _TIMESTAMP,
        "count": st.integers(min_value=1, max_value=50),
    }
)

_EVENT = st.fixed_dictionaries(
    {
        "type": st.just("SW_ROGUE_DHCP_SERVER_DETECTED"),
        "site_id": _IDENTIFIER,
        "mac": _IDENTIFIER,
        "port_id": _IDENTIFIER,
        "timestamp": _TIMESTAMP,
        "count": st.integers(min_value=1, max_value=50),
    }
)


@_NO_DEADLINE
@given(alarms=st.lists(_ALARM, min_size=0, max_size=12))
def test_the_merge_never_grows_the_list(alarms: list[dict]) -> None:
    """The merge collapses duplicates, so it can never invent a row."""
    normalizer = build_normalizer()  # One normalizer serves every record in this example.
    findings = [normalizer.from_alarm(record, SOURCE_ORG_ALARM) for record in alarms]
    assert len(RogueDhcpFindingMerger.merge(findings)) <= len(findings)


@_NO_DEADLINE
@given(events=st.lists(_EVENT, min_size=1, max_size=12))
def test_the_merge_keys_stay_unique(events: list[dict]) -> None:
    """No two rows may share a merge key, or a database upsert would lose one."""
    normalizer = build_normalizer()  # One normalizer serves every record in this example.
    findings = [normalizer.from_device_event(record, SOURCE_ORG_EVENT) for record in events]
    merged = RogueDhcpFindingMerger.merge(findings)
    assert len({finding.record_id for finding in merged}) == len(merged)


@_NO_DEADLINE
@given(alarm=_ALARM)
def test_the_alarm_normalizer_returns_the_declared_columns(alarm: dict) -> None:
    """Every alarm must produce the exact declared column set."""
    row = build_normalizer().from_alarm(alarm, SOURCE_ORG_ALARM).as_row()
    assert list(row.keys()) == RogueDhcpFinding.column_names()


@_NO_DEADLINE
@given(event=_EVENT)
def test_the_event_normalizer_returns_the_declared_columns(event: dict) -> None:
    """Every switch event must produce the exact declared column set."""
    row = build_normalizer().from_device_event(event, SOURCE_ORG_EVENT).as_row()
    assert list(row.keys()) == RogueDhcpFinding.column_names()


@_NO_DEADLINE
@given(timestamp=_TIMESTAMP)
def test_the_state_is_always_one_of_two_values(timestamp: float) -> None:
    """An operator filters on this column, so it must never hold a third value."""
    assert build_normalizer().resolve_state(timestamp) in {STATE_ACTIVE, STATE_HISTORICAL}


@_NO_DEADLINE
@given(events=st.lists(_EVENT, min_size=1, max_size=8))
def test_the_merge_preserves_the_total_occurrence_count(events: list[dict]) -> None:
    """A merge must move a count, never drop one."""
    normalizer = build_normalizer()  # One normalizer serves every record in this example.
    findings = [normalizer.from_device_event(record, SOURCE_ORG_EVENT) for record in events]
    merged = RogueDhcpFindingMerger.merge(findings)
    assert sum(row.occurrence_count for row in merged) == sum(row.occurrence_count for row in findings)


@_NO_DEADLINE
@given(event=_EVENT)
def test_the_record_id_is_deterministic(event: dict) -> None:
    """A repeat run must rewrite the same database row, not add a second one."""
    normalizer = build_normalizer()  # One normalizer serves both conversions in this example.
    first = normalizer.from_device_event(event, SOURCE_ORG_EVENT)
    second = normalizer.from_device_event(event, SOURCE_ORG_EVENT)
    assert first.record_id == second.record_id
