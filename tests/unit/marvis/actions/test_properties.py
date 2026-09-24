"""Property tests for the menu 270 readers, the record builder, and the answer grammar.

The unit tests pin the row shapes that the lab organization returns. These
property tests widen the input space, so a new Mist topic or a changed field
still holds the invariants that an operator depends on: the export never stops
on a strange value, a filter answer never widens past the offered topics, and
only the exact confirmation text starts a resolve.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

pytest.importorskip("hypothesis")

from hypothesis import given, settings
from hypothesis import strategies as st

from src.marvis.actions.model import (
    STATUS_NAMES,
    TOPIC_NAMES,
    MarvisActionRecord,
    MarvisActionRecordBuilder,
    MarvisCatalog,
    MarvisFieldReader,
)
from src.marvis.actions.selection import (
    MODE_EXPORT_ALL,
    MODE_EXPORT_CLOSED,
    MODE_EXPORT_OPEN,
    MarvisResolvePrompts,
    MarvisTopicSelector,
)
from tests.unit.marvis.actions.conftest import make_raw

# Issue #1803: a full-suite run applies memory and CPU pressure that an isolated run
# does not. The deadline is disabled, and the assertions stay unchanged.
_NO_DEADLINE = settings(deadline=None, max_examples=150)
LAST_WINDOWS_EPOCH_MS = 32_503_679_999_000  # 2999-12-31T23:59:59Z. The Windows gmtime stops at the year 3000.

_SCALARS = (
    st.none()
    | st.booleans()
    | st.integers()
    | st.integers(min_value=-(10**400), max_value=10**400)
    | st.floats()
    | st.text(max_size=12)
)
JSON_VALUES = st.recursive(
    _SCALARS,
    lambda children: st.lists(children, max_size=3) | st.dictionaries(st.text(max_size=8), children, max_size=3),
    max_leaves=10,
)
RAW_KEYS = tuple(make_raw())
RAW_OVERRIDES = st.dictionaries(st.sampled_from(RAW_KEYS), JSON_VALUES, max_size=len(RAW_KEYS))
TOPIC_TOKENS = st.sampled_from(sorted({f"{category}/{symptom}" for category, symptom in TOPIC_NAMES}))
ANSWER_TOKENS = st.one_of(
    st.sampled_from(["all", "ALL", " ", "0", "1", "2", "3", "99", "1234567", "switch", "ap", "security"]),
    st.sampled_from(sorted({symptom for _, symptom in TOPIC_NAMES})),
    TOPIC_TOKENS,
    st.text(max_size=10),
)
ANSWERS = st.lists(ANSWER_TOKENS, max_size=4).map(", ".join)
ALL_KNOWN_TOPICS = frozenset(f"{category}/{symptom}" for category, symptom in TOPIC_NAMES)
STATUS_KEYS = st.one_of(st.sampled_from(sorted(STATUS_NAMES)), st.text(max_size=12), st.none())  # Known and new keys.
ACTION_ROWS = st.lists(st.tuples(STATUS_KEYS, st.sampled_from(sorted(TOPIC_NAMES))), min_size=1, max_size=12)


def sample_selector() -> MarvisTopicSelector:
    """Return a selector over five actions in three categories, with two open topics."""
    builder = MarvisActionRecordBuilder(MarvisCatalog([]), {}, "2026-09-23T00:00:00+00:00")
    raws = [
        make_raw(1),
        make_raw(2, status="validated"),
        make_raw(3, category="ap", symptom="ap_disconnect"),
        make_raw(4, category="ap", symptom="non_compliant", status="resolved"),
        make_raw(5, category="gateway", symptom="non_compliant", status="validated"),
    ]
    return MarvisTopicSelector([builder.build(raw) for raw in raws], MarvisCatalog([]), MODE_EXPORT_ALL)


def records_of(rows: list[tuple[Any, tuple[str, str]]]) -> list[MarvisActionRecord]:
    """Return one record for each status key and topic pair."""
    builder = MarvisActionRecordBuilder(MarvisCatalog([]), {}, "2026-09-23T00:00:00+00:00")
    return [
        builder.build(make_raw(number, status=status, category=category, symptom=symptom))
        for number, (status, (category, symptom)) in enumerate(rows, start=1)
    ]


SELECTOR = sample_selector()
SHOWN_TOPICS = frozenset({"switch/sw_offline", "ap/ap_disconnect", "ap/non_compliant", "gateway/non_compliant"})


class TestReaders:
    """Each reader returns its one type for any JSON value."""

    @_NO_DEADLINE
    @given(JSON_VALUES)
    def test_the_readers_never_raise(self, value: Any) -> None:
        """A strange value becomes an empty cell, never a stopped export."""
        assert isinstance(MarvisFieldReader.text(value), str)
        number = MarvisFieldReader.integer(value)
        assert number is None or (isinstance(number, int) and not isinstance(number, bool))
        assert MarvisFieldReader.flag(value) in (True, False, None)
        assert isinstance(MarvisFieldReader.iso(value), str)

    @_NO_DEADLINE
    @given(st.integers(min_value=1, max_value=LAST_WINDOWS_EPOCH_MS))
    def test_a_valid_epoch_time_gives_utc_text(self, epoch_ms: int) -> None:
        """Every time up to the year 3000 reads as UTC text on every platform."""
        assert MarvisFieldReader.iso(epoch_ms).endswith("+00:00")


class TestBuilder:
    """The builder gives one full record for any row shape."""

    @_NO_DEADLINE
    @given(RAW_OVERRIDES)
    def test_the_builder_never_raises_and_fills_every_column(self, overrides: dict[str, Any]) -> None:
        """A new topic or a changed field must not stop the export."""
        raw = {**make_raw(1), **overrides}
        builder = MarvisActionRecordBuilder(MarvisCatalog([]), {}, "2026-09-23T00:00:00+00:00")
        record = builder.build(raw)
        assert list(record.as_row()) == MarvisActionRecord.column_names()
        document = builder.document(raw, record)
        assert document["uuid"] == record.uuid == MarvisActionRecordBuilder.action_key(raw)

    @_NO_DEADLINE
    @given(st.dictionaries(st.text(max_size=6), JSON_VALUES, max_size=4))
    def test_the_action_key_is_stable_for_a_row_without_a_uuid(self, raw: dict[str, Any]) -> None:
        """The same row always gives the same database key, and the key is a UUID."""
        raw.pop("uuid", None)
        key = MarvisActionRecordBuilder.action_key(raw)
        assert key == MarvisActionRecordBuilder.action_key(dict(raw))
        assert str(uuid.UUID(key)) == key


class TestGrammar:
    """A filter answer never widens past the offered topics."""

    @_NO_DEADLINE
    @given(ANSWERS)
    def test_a_category_answer_stays_inside_the_offered_topics(self, answer: str) -> None:
        """A refused answer selects nothing, and an accepted answer selects offered topics only."""
        topics, bad_token = SELECTOR.match_categories(answer)
        assert topics <= SHOWN_TOPICS
        assert not (bad_token and topics)

    @_NO_DEADLINE
    @given(ANSWERS, st.sets(st.sampled_from(sorted(SHOWN_TOPICS))))
    def test_a_subcategory_answer_stays_inside_the_kept_topics(self, answer: str, kept: set[str]) -> None:
        """The second step can only narrow the first step."""
        topics, bad_token = SELECTOR.match_topics(answer, frozenset(kept))
        assert topics <= kept
        assert not (bad_token and topics)


class TestModeSplit:
    """Issue #3342: the open report and the closed report split the full report for any status mix."""

    @_NO_DEADLINE
    @given(ACTION_ROWS)
    def test_modes_2_and_4_split_mode_1_with_no_overlap_and_no_gap(self, rows: list[Any]) -> None:
        """A new status key must land in one report, never in both and never in neither."""
        records = records_of(rows)
        chosen = {
            mode: MarvisTopicSelector(records, MarvisCatalog([]), mode).select(ALL_KNOWN_TOPICS)
            for mode in (MODE_EXPORT_ALL, MODE_EXPORT_OPEN, MODE_EXPORT_CLOSED)
        }
        opened = {record.uuid for record in chosen[MODE_EXPORT_OPEN]}
        closed = {record.uuid for record in chosen[MODE_EXPORT_CLOSED]}
        assert not opened & closed
        assert opened | closed == {record.uuid for record in chosen[MODE_EXPORT_ALL]} == {r.uuid for r in records}
        assert all(record.is_open for record in chosen[MODE_EXPORT_OPEN])
        assert not any(record.is_open for record in chosen[MODE_EXPORT_CLOSED])

    @_NO_DEADLINE
    @given(ACTION_ROWS)
    def test_each_table_row_holds_an_action_of_its_mode(self, rows: list[Any]) -> None:
        """The operator never picks a row that exports nothing in the chosen mode."""
        records = records_of(rows)
        for mode, count_name in ((MODE_EXPORT_OPEN, "open_count"), (MODE_EXPORT_CLOSED, "closed_count")):
            shown = MarvisTopicSelector(records, MarvisCatalog([]), mode)
            for row in [*shown.category_counts(), *shown.topic_counts(ALL_KNOWN_TOPICS)]:
                assert getattr(row, count_name) > 0
                assert row.open_count + row.closed_count == row.total


class TestConfirmation:
    """Only the exact text starts a resolve."""

    @_NO_DEADLINE
    @given(
        st.integers(min_value=1, max_value=10**6),
        st.text(alphabet=" \t", max_size=3),
        st.text(alphabet=" \t", min_size=1, max_size=3),
        st.text(alphabet=" \t", max_size=3),
    )
    def test_the_exact_text_confirms_with_any_spaces(self, count: int, before: str, between: str, after: str) -> None:
        """Extra spaces around and inside the text are harmless."""
        assert MarvisResolvePrompts.confirmation_matches(f"{before}RESOLVE{between}{count}{after}", count)

    @_NO_DEADLINE
    @given(st.integers(min_value=1, max_value=10**6), st.integers(min_value=0, max_value=10**6))
    def test_a_wrong_count_never_confirms(self, count: int, typed: int) -> None:
        """The count proves that the operator read the preview."""
        if typed != count:
            assert not MarvisResolvePrompts.confirmation_matches(f"RESOLVE {typed}", count)

    @_NO_DEADLINE
    @given(st.text(max_size=20))
    def test_a_random_answer_names_a_known_code_or_none(self, answer: str) -> None:
        """The code prompt can never invent a code."""
        code = MarvisResolvePrompts.parse_code(answer)
        assert code is None or code.key in {"suggested", "nonsuggested", "known", "invalid"}
