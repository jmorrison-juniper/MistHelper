"""Tests for the Marvis alarm join of menu 270 (issue #3339, phase 1).

The index finds the alarm of each action through the alarm ``action_id`` or the
alarm ``id``. The join computes the search window, runs one search, and copies
eight alarm values into each record and each document. A failed search leaves
the columns empty. No test touches the network.
"""

from __future__ import annotations

import logging
import math
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.marvis.actions import alarms as alarms_module
from src.marvis.actions.alarms import (
    ALARM_COLUMNS,
    ALARM_MAX_WINDOW_SECONDS,
    ALARM_WINDOW_MARGIN_SECONDS,
    MarvisAlarmIndex,
    MarvisAlarmJoin,
)
from src.marvis.actions.client import MarvisActionsClient, MarvisListResult
from src.marvis.actions.model import MarvisActionRecord, MarvisActionRecordBuilder, MarvisCatalog
from src.marvis.actions.selection import DISPLAY_LEVEL
from tests.unit.marvis.actions.conftest import make_alarm, make_raw
from web_portal.services.operation import HANDLED_ERROR_MARKERS

EXPORTED_AT = "2026-09-24T00:00:00+00:00"  # The export time of every test record.
NOW = 2_000_000_000  # 2033-05-18T03:33:20+00:00, a fixed time of the run.
DAY = 86_400  # One day in seconds.
EMPTY_COLUMNS = {  # The defaults of the eight alarm columns.
    "alarm_id": "",
    "alarm_type": "",
    "alarm_status": "",
    "alarm_resolved_time_iso": "",
    "alarm_acked": None,
    "alarm_acked_time_iso": "",
    "alarm_ack_admin_name": "",
    "alarm_note": "",
}


def uuid_of(number: int) -> str:
    """Return the uuid of the synthetic action with this number."""
    return str(make_raw(number)["uuid"])


def loaded(*numbers: int) -> tuple[list[MarvisActionRecord], dict[str, dict[str, Any]]]:
    """Return the records and the documents of the synthetic actions, as the operation loads them."""
    builder = MarvisActionRecordBuilder(MarvisCatalog([]), {}, EXPORTED_AT)
    records: list[MarvisActionRecord] = []
    documents: dict[str, dict[str, Any]] = {}
    for number in numbers:
        raw = make_raw(number)
        record = builder.build(raw)
        records.append(record)
        documents[record.uuid] = builder.document(raw, record)
    return records, documents


def fake_client(result: MarvisListResult) -> MagicMock:
    """Return a client whose alarm search returns the result."""
    client = MagicMock(spec=MarvisActionsClient)
    client.search_marvis_alarms.return_value = result
    return client


def alarm_part(row: dict[str, Any]) -> dict[str, Any]:
    """Return the eight alarm columns of one row or document."""
    return {name: row[name] for name in ALARM_COLUMNS}


def other_part(row: dict[str, Any]) -> dict[str, Any]:
    """Return every column of one row that is not an alarm column."""
    return {name: value for name, value in row.items() if name not in ALARM_COLUMNS}


class TestAlarmIndex:
    """The index maps each alarm by its two keys, and the later alarm wins a tie of keys."""

    def test_the_alarm_id_joins_the_action(self) -> None:
        """The live organization joined 31 alarms through the alarm id."""
        index = MarvisAlarmIndex([make_alarm(1), make_alarm(2)])
        assert index.alarm_for(uuid_of(2)) == make_alarm(2)

    def test_the_action_id_joins_before_the_alarm_id(self) -> None:
        """The issue names the action_id key, so that key wins when both keys match."""
        by_action_id = make_alarm(7, action_id=uuid_of(1), type="ap_offline")
        index = MarvisAlarmIndex([make_alarm(1), by_action_id])
        assert index.alarm_for(uuid_of(1)) == by_action_id

    @pytest.mark.parametrize("order", [(10, 20), (20, 10)])
    def test_the_later_last_seen_wins(self, order: tuple[int, int]) -> None:
        """The latest alarm states the current status, whatever the page order."""
        alarms = [make_alarm(1, last_seen=seen, status=f"status-{seen}") for seen in order]
        assert MarvisAlarmIndex(alarms).columns(uuid_of(1))["alarm_status"] == "status-20"

    def test_an_equal_last_seen_keeps_the_first_alarm(self) -> None:
        """A repeated alarm must not change the join result."""
        alarms = [make_alarm(1, last_seen=5, status="first"), make_alarm(1, last_seen=5, status="second")]
        assert MarvisAlarmIndex(alarms).columns(uuid_of(1))["alarm_status"] == "first"

    @pytest.mark.parametrize("seen", [None, "12", True, math.nan, math.inf, [1]])
    def test_an_alarm_without_a_finite_last_seen_ranks_below_a_real_time(self, seen: Any) -> None:
        """A flag, text, NaN, or infinity must not hide an alarm with a real time."""
        alarms = [make_alarm(1, last_seen=seen, status="strange"), make_alarm(1, last_seen=1, status="real")]
        assert MarvisAlarmIndex(alarms).columns(uuid_of(1))["alarm_status"] == "real"

    def test_a_very_large_integer_last_seen_ranks_exactly(self) -> None:
        """Python compares a very large int with a float exactly, so the int wins."""
        alarms = [make_alarm(1, last_seen=1.5e300, status="float"), make_alarm(1, last_seen=10**400, status="int")]
        assert MarvisAlarmIndex(alarms).columns(uuid_of(1))["alarm_status"] == "int"

    def test_the_columns_hold_the_eight_alarm_values(self) -> None:
        """Each reader returns one fixed type, and the keys follow the record order."""
        alarm = make_alarm(
            1, acked=True, acked_time=1_700_001_000, ack_admin_name="Noc Operator", note="  checked the uplink  "
        )
        columns = MarvisAlarmIndex([alarm]).columns(uuid_of(1))
        assert list(columns) == list(ALARM_COLUMNS)
        assert columns == {
            "alarm_id": uuid_of(1),
            "alarm_type": "switch_offline",
            "alarm_status": "resolved",
            "alarm_resolved_time_iso": "2023-11-14T22:29:20+00:00",
            "alarm_acked": True,
            "alarm_acked_time_iso": "2023-11-14T22:30:00+00:00",
            "alarm_ack_admin_name": "Noc Operator",
            "alarm_note": "checked the uplink",
        }

    def test_the_live_alarm_shape_leaves_the_acknowledge_columns_empty(self) -> None:
        """The live alarms held no acked, acked_time, ack_admin_name, or note key."""
        columns = MarvisAlarmIndex([make_alarm(1, resolved_time=None, status="open")]).columns(uuid_of(1))
        assert columns["alarm_status"] == "open"
        assert {name: columns[name] for name in ALARM_COLUMNS[3:]} == {
            name: EMPTY_COLUMNS[name] for name in ALARM_COLUMNS[3:]
        }

    def test_a_text_acked_value_is_not_read_as_a_flag(self) -> None:
        """The reader never guesses a flag from text."""
        assert MarvisAlarmIndex([make_alarm(1, acked="true")]).columns(uuid_of(1))["alarm_acked"] is None

    def test_an_action_without_an_alarm_gets_no_columns(self) -> None:
        """An empty map keeps the empty defaults of the record."""
        index = MarvisAlarmIndex([make_alarm(1)])
        assert (index.alarm_for(uuid_of(2)), index.columns(uuid_of(2))) == (None, {})

    def test_an_empty_key_never_joins(self) -> None:
        """An alarm without keys names no action."""
        index = MarvisAlarmIndex([make_alarm(1, id="", action_id=None)])
        assert (index.alarm_for(""), index.columns(uuid_of(1))) == (None, {})

    def test_a_row_that_is_not_an_object_is_skipped(self) -> None:
        """A malformed row must not stop the export."""
        index = MarvisAlarmIndex(["noise", None, 7, make_alarm(1)])
        assert (index.columns(uuid_of(1))["alarm_id"], index.unmatched_alarm_count([uuid_of(1)])) == (uuid_of(1), 0)

    def test_the_unmatched_count_skips_a_repeated_alarm(self) -> None:
        """Two pages can repeat one alarm, and the count must name it one time."""
        index = MarvisAlarmIndex([make_alarm(1), make_alarm(2), make_alarm(3), make_alarm(2)])
        assert index.unmatched_alarm_count([uuid_of(1)]) == 2

    def test_the_unmatched_count_reads_both_keys(self) -> None:
        """An alarm whose action_id names an action is not unmatched."""
        index = MarvisAlarmIndex([make_alarm(9, action_id=uuid_of(1)), make_alarm(8)])
        assert index.unmatched_alarm_count([uuid_of(1)]) == 1

    def test_an_alarm_without_keys_counts_as_unmatched(self) -> None:
        """An alarm that names no action cannot join a row."""
        assert MarvisAlarmIndex([make_alarm(1, id=None)]).unmatched_alarm_count([uuid_of(1)]) == 1


class TestWindow:
    """The window starts one day before the oldest selected action, and it is 1 to 400 days wide."""

    def test_the_window_starts_one_day_before_the_oldest_action(self) -> None:
        """The alarm timestamp equals the action start, so a margin keeps the oldest alarm inside."""
        documents = [{"start_time": (NOW - 5 * DAY) * 1000}, {"start_time": (NOW - 10 * DAY) * 1000}]
        assert MarvisAlarmJoin.window(documents, now=NOW) == (NOW - 11 * DAY, NOW)

    def test_the_margin_is_one_day_and_the_cap_is_400_days(self) -> None:
        """The live test proved a window of 400 days."""
        assert (ALARM_WINDOW_MARGIN_SECONDS, ALARM_MAX_WINDOW_SECONDS) == (DAY, 400 * DAY)

    def test_the_window_is_never_wider_than_400_days(self) -> None:
        """An old action must not widen the search past the proved limit."""
        documents = [{"start_time": (NOW - 500 * DAY) * 1000}]
        assert MarvisAlarmJoin.window(documents, now=NOW) == (NOW - 400 * DAY, NOW)

    def test_the_window_is_at_least_one_day_wide(self) -> None:
        """A start time in the future must not give an empty window."""
        documents = [{"start_time": (NOW + 3_600) * 1000}]
        assert MarvisAlarmJoin.window(documents, now=NOW) == (NOW - DAY, NOW)

    @pytest.mark.parametrize("start_time", [None, 0, -5, "abc", True, 1.5, [1]])
    def test_no_valid_start_time_gives_the_widest_window(self, start_time: Any) -> None:
        """Without a start time, the search covers the last 400 days."""
        assert MarvisAlarmJoin.window([{"start_time": start_time}], now=NOW) == (NOW - 400 * DAY, NOW)

    def test_no_document_gives_the_widest_window(self) -> None:
        """An empty selection still gives a valid window."""
        assert MarvisAlarmJoin.window([], now=NOW) == (NOW - 400 * DAY, NOW)

    def test_a_millisecond_start_is_rounded_down_to_seconds(self) -> None:
        """The alarm search reads whole seconds, so the start must not skip the first second."""
        documents = [{"start_time": NOW * 1000 - 1_500}]
        assert MarvisAlarmJoin.window(documents, now=NOW) == (NOW - 2 - DAY, NOW)

    def test_the_window_ends_at_the_current_time(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The end is a whole second, and it is the time of the run."""
        monkeypatch.setattr(alarms_module.time, "time", lambda: NOW + 0.75)
        assert MarvisAlarmJoin.window([{"start_time": (NOW - DAY) * 1000}]) == (NOW - 2 * DAY, NOW)


class TestJoin:
    """The join searches one time, copies the alarm values, and never stops the export."""

    def test_the_join_copies_the_alarm_values_into_the_record_and_the_document(self) -> None:
        """The CSV file and the database receive the same alarm values."""
        records, documents = loaded(1)
        joined_records, joined_documents = MarvisAlarmJoin(fake_client(MarvisListResult([make_alarm(1)], 200))).apply(
            records, documents
        )
        expected = MarvisAlarmIndex([make_alarm(1)]).columns(uuid_of(1))
        assert alarm_part(joined_records[0].as_row()) == expected
        assert alarm_part(joined_documents[0]) == expected

    def test_the_join_changes_no_column_of_the_action(self) -> None:
        """Only the eight alarm columns change, and the order of the rows stays."""
        records, documents = loaded(1, 2, 3)
        client = fake_client(MarvisListResult([make_alarm(2), make_alarm(3)], 200))
        joined_records, joined_documents = MarvisAlarmJoin(client).apply(records, documents)
        assert [other_part(record.as_row()) for record in joined_records] == [
            other_part(record.as_row()) for record in records
        ]
        assert [other_part(document) for document in joined_documents] == [
            other_part(documents[record.uuid]) for record in records
        ]

    def test_an_action_without_an_alarm_keeps_the_empty_defaults(self) -> None:
        """An old action has no alarm, because Mist keeps an alarm for a shorter time."""
        records, documents = loaded(1, 2)
        joined_records, joined_documents = MarvisAlarmJoin(fake_client(MarvisListResult([make_alarm(1)], 200))).apply(
            records, documents
        )
        assert alarm_part(joined_records[1].as_row()) == EMPTY_COLUMNS
        assert alarm_part(joined_documents[1]) == EMPTY_COLUMNS

    def test_the_search_receives_the_window_of_the_selected_actions(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """One search covers the whole run, and it starts one day before the oldest selected action."""
        monkeypatch.setattr(alarms_module.time, "time", lambda: 1_700_864_000)
        records, documents = loaded(1, 2)
        client = fake_client(MarvisListResult([], 200))
        MarvisAlarmJoin(client).apply(records[1:], documents)
        oldest = int(make_raw(2)["start_time"]) // 1000
        client.search_marvis_alarms.assert_called_once_with(oldest - DAY, 1_700_864_000)

    @pytest.mark.parametrize("status_code", [403, 503])
    def test_a_refused_search_returns_the_records_and_the_documents_unchanged(
        self, status_code: int, caplog: Any
    ) -> None:
        """A client error or a server error keeps every action, and the operator learns why the columns are empty."""
        records, documents = loaded(1)
        problem = f"The API returned HTTP {status_code}."
        client = fake_client(MarvisListResult([], status_code=status_code, complete=False, problem=problem))
        with caplog.at_level(logging.WARNING):
            joined_records, joined_documents = MarvisAlarmJoin(client).apply(records, documents)
        assert (joined_records, joined_documents) == (records, [documents[uuid_of(1)]])
        assert (
            f"The Marvis alarm search returned no usable result. {problem} The alarm columns stay empty." in caplog.text
        )

    def test_the_count_lines_reach_the_display_level(self, caplog: Any) -> None:
        """The SSH operator sees the join count and the count of alarms without an action."""
        records, documents = loaded(1, 2)
        client = fake_client(MarvisListResult([make_alarm(1), make_alarm(9)], 200))
        with caplog.at_level(logging.DEBUG):
            MarvisAlarmJoin(client).apply(records, documents)
        shown = [record.getMessage() for record in caplog.records if record.levelno >= DISPLAY_LEVEL]
        assert shown == [
            "Marvis alarm join: 1 of 2 exported actions have a Marvis alarm. 1 have no alarm.",
            "Marvis alarms in the search window without an action in the list: 1",
        ]

    def test_the_unmatched_count_reads_every_action_of_the_list(self, caplog: Any) -> None:
        """A filter must not count the alarm of an action that the filter left out."""
        records, documents = loaded(1, 2, 3)
        client = fake_client(MarvisListResult([make_alarm(1), make_alarm(2), make_alarm(4)], 200))
        with caplog.at_level(logging.WARNING):
            MarvisAlarmJoin(client).apply(records[:1], documents)
        assert "Marvis alarm join: 1 of 1 exported actions have a Marvis alarm. 0 have no alarm." in caplog.text
        assert "Marvis alarms in the search window without an action in the list: 1" in caplog.text

    def test_the_join_logs_before_and_after(self, caplog: Any) -> None:
        """The script log shows the join step before the count lines."""
        records, documents = loaded(1)
        with caplog.at_level(logging.INFO, logger=alarms_module.__name__):
            MarvisAlarmJoin(fake_client(MarvisListResult([make_alarm(1)], 200))).apply(records, documents)
        messages = [record.getMessage() for record in caplog.records]
        assert messages[0] == "Joining 1 Marvis alarms to 1 Marvis Actions"
        assert messages[1].startswith("Marvis alarm join: 1 of 1")

    @pytest.mark.parametrize(
        ("result", "line_count"),
        [
            (MarvisListResult([make_alarm(1)], 200), 3),
            (MarvisListResult([], status_code=403, complete=False, problem="The API returned HTTP 403."), 1),
            (MarvisListResult([], status_code=503, complete=False, problem="The API returned HTTP 503."), 1),
            (MarvisListResult([], None, False, "No HTTP answer arrived. Read the mistapi line in script.log."), 1),
            (MarvisListResult([], None, False, "The alarm search returned no next page."), 1),
        ],
        ids=["joined", "http-403", "http-503", "no-answer", "no-next-page"],
    )
    def test_no_log_line_holds_a_portal_failure_word(
        self, result: MarvisListResult, line_count: int, caplog: Any
    ) -> None:
        """The portal marks a run as failed when one line holds a failure word, and the join never fails the run."""
        records, documents = loaded(1, 2)
        with caplog.at_level(logging.DEBUG):
            MarvisAlarmJoin(fake_client(result)).apply(records, documents)
        lowered = [record.getMessage().lower() for record in caplog.records]
        assert len(lowered) == line_count
        assert [line for line in lowered if any(marker in line for marker in HANDLED_ERROR_MARKERS)] == []
