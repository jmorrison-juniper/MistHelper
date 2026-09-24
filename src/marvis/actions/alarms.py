"""The Marvis alarm join of menu 270 (issue #3339, phase 1).

Why:
    Mist keeps a Marvis alarm for many Marvis Actions. The alarm holds its own
    status, its resolved time, and its acknowledge values. Before this module,
    a NOC engineer compared the Marvis Actions list and the alarm list by hand.
    This module searches the Marvis alarms one time and copies eight alarm
    values into the export row of each action.

Evidence:
    The live read-only test of 2026-09-24 found 33 Marvis alarms and 112
    actions. The alarm ``id`` equaled the action ``uuid`` for 31 actions. No
    alarm held an ``action_id`` value. The issue names that key, so the index
    reads it first. Research R1 to R5 in ``specs/3339-marvis-alarm-join`` holds
    the counts.

Safety:
    The join reads only. It sends no acknowledge request and no other write
    request to Mist. If the alarm search fails, the export keeps every action
    and leaves the alarm columns empty.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions in the annotations of this module.

import dataclasses  # WHY: copy a frozen record with its alarm columns filled.
import logging  # WHY: log the join step and its two count lines.
import math  # WHY: rank an alarm without a finite last_seen value below every real time.
import time  # WHY: the search window ends at the time of the run.
from collections.abc import Iterable, Mapping, Sequence  # WHY: type the inputs without a concrete class.
from typing import Any  # WHY: a raw alarm row holds values of any JSON type.

from src.marvis.actions.client import MarvisActionsClient  # WHY: the client makes the one alarm search.
from src.marvis.actions.model import MarvisActionRecord, MarvisFieldReader  # WHY: the record and the value readers.
from src.marvis.actions.selection import DISPLAY_LEVEL  # WHY: the count lines must reach the SSH console.

logger = logging.getLogger(__name__)  # WHY: name the logger for this module so a reader filters by source.

ALARM_WINDOW_MARGIN_SECONDS = 86_400  # WHY: the window starts one day before the oldest exported action.
ALARM_MAX_WINDOW_SECONDS = 400 * 86_400  # WHY: the widest window that the live test proved.
ALARM_COLUMNS = (  # WHY: the eight alarm columns, in the order of the record.
    "alarm_id",
    "alarm_type",
    "alarm_status",
    "alarm_resolved_time_iso",
    "alarm_acked",
    "alarm_acked_time_iso",
    "alarm_ack_admin_name",
    "alarm_note",
)


class MarvisAlarmIndex:
    """Find the Marvis alarm of one action through the two alarm keys.

    Why:
        The issue names the alarm ``action_id`` as the join key, and the live
        organization joins through the alarm ``id``. The index reads both keys,
        so a change of the Mist key does not stop the join.
    """

    def __init__(self, alarms: Iterable[Any]) -> None:
        """Map each alarm by its ``action_id`` and by its ``id``.

        Args:
            alarms: The raw Marvis alarm rows. A row that is not an object is skipped.
        """
        self._alarms = [alarm for alarm in alarms if isinstance(alarm, Mapping)]  # WHY: skip a row of another type.
        self._by_action_id: dict[str, Mapping[str, Any]] = {}  # WHY: the key that the issue names.
        self._by_id: dict[str, Mapping[str, Any]] = {}  # WHY: the key that joined the live organization.
        for alarm in self._alarms:  # WHY: one pass fills both maps.
            self._keep(self._by_action_id, MarvisFieldReader.text(alarm.get("action_id")), alarm)  # WHY: key 1.
            self._keep(self._by_id, MarvisFieldReader.text(alarm.get("id")), alarm)  # WHY: key 2.

    def alarm_for(self, action_uuid: str) -> Mapping[str, Any] | None:
        """Return the alarm of one action, or None.

        Args:
            action_uuid: The ``uuid`` of the action.

        Returns:
            The alarm whose ``action_id`` equals the uuid, else the alarm whose ``id`` equals it.
        """
        alarm = self._by_action_id.get(action_uuid)  # WHY: the issue names this key first.
        return alarm if alarm is not None else self._by_id.get(action_uuid)  # WHY: the key of the live test.

    def columns(self, action_uuid: str) -> dict[str, Any]:
        """Return the eight alarm column values of one action.

        Args:
            action_uuid: The ``uuid`` of the action.

        Returns:
            The column values, or an empty map when the action has no alarm.
        """
        alarm = self.alarm_for(action_uuid)  # WHY: find the alarm through the two keys.
        if alarm is None:  # WHY: an action without an alarm keeps the empty defaults.
            return {}  # WHY: nothing to copy.
        return {  # WHY: each reader returns one fixed type, so every store receives the same shape.
            "alarm_id": MarvisFieldReader.text(alarm.get("id")),
            "alarm_type": MarvisFieldReader.text(alarm.get("type")),
            "alarm_status": MarvisFieldReader.text(alarm.get("status")),
            "alarm_resolved_time_iso": MarvisFieldReader.iso_seconds(alarm.get("resolved_time")),
            "alarm_acked": MarvisFieldReader.flag(alarm.get("acked")),
            "alarm_acked_time_iso": MarvisFieldReader.iso_seconds(alarm.get("acked_time")),
            "alarm_ack_admin_name": MarvisFieldReader.text(alarm.get("ack_admin_name")),
            "alarm_note": MarvisFieldReader.text(alarm.get("note")),
        }

    def unmatched_alarm_count(self, action_uuids: Iterable[str]) -> int:
        """Count the alarms that belong to no action of the list.

        Args:
            action_uuids: The ``uuid`` of every action in the list, not only the selected actions.

        Returns:
            The number of distinct alarms whose two keys name no action.
        """
        known = set(action_uuids)  # WHY: a set makes each lookup one step.
        pairs = {  # WHY: a set of key pairs counts an alarm one time, also when two pages repeat it.
            (MarvisFieldReader.text(alarm.get("action_id")), MarvisFieldReader.text(alarm.get("id")))
            for alarm in self._alarms
        }
        unmatched = [pair for pair in pairs if pair[0] not in known and pair[1] not in known]  # WHY: no key matches.
        return len(unmatched)  # WHY: the count line reports this number.

    @classmethod
    def _keep(cls, index: dict[str, Mapping[str, Any]], key: str, alarm: Mapping[str, Any]) -> None:
        """Store one alarm under one key. The alarm with the later ``last_seen`` value wins."""
        if not key:  # WHY: an empty key names no action.
            return  # WHY: skip the key, and keep the other key of the alarm.
        current = index.get(key)  # WHY: an earlier alarm can hold the same key.
        if current is None or cls._seen(alarm) > cls._seen(current):  # WHY: equal values keep the first alarm.
            index[key] = alarm  # WHY: the latest alarm states the current status.

    @staticmethod
    def _seen(alarm: Mapping[str, Any]) -> float:
        """Return the ``last_seen`` value of one alarm, or minus infinity when it holds no finite number."""
        value = alarm.get("last_seen")  # WHY: the alarm search writes epoch seconds.
        if isinstance(value, bool):  # WHY: JSON true and false are not times, although Python treats them as ints.
            return -math.inf  # WHY: a flag ranks below every real time.
        if isinstance(value, int):  # WHY: Python compares a very large int with a float exactly.
            return value  # WHY: keep the exact value.
        if isinstance(value, float) and math.isfinite(value):  # WHY: NaN would break the order of the ranks.
            return value  # WHY: a finite decimal time is a valid rank.
        return -math.inf  # WHY: text, null, NaN, and infinity rank below every real time.


class MarvisAlarmJoin:
    """Search the Marvis alarms one time, and copy the alarm values into each export row.

    Why:
        Modes 1, 2, and 4 write the same rows to the CSV file and to the
        database. The join runs one time before the write, so every store
        receives the same alarm values.
    """

    def __init__(self, client: MarvisActionsClient) -> None:
        """Keep the client of the organization.

        Args:
            client: The API client that makes the alarm search.
        """
        self._client = client  # WHY: the one search of the run uses the session of the list read.

    @staticmethod
    def window(documents: Iterable[Mapping[str, Any]], now: float | None = None) -> tuple[int, int]:
        """Return the search window for the selected actions.

        Args:
            documents: The raw documents of the selected actions.
            now: The time of the run in epoch seconds. None means the current time.

        Returns:
            The start and the end of the window, in epoch seconds.
        """
        end = int(time.time() if now is None else now)  # WHY: the window ends at the time of the run.
        starts = [  # WHY: the start_time of an action is an epoch millisecond value.
            epoch_ms // 1000
            for epoch_ms in (MarvisFieldReader.integer(document.get("start_time")) for document in documents)
            if epoch_ms is not None and epoch_ms > 0
        ]
        oldest = min(starts, default=end - ALARM_MAX_WINDOW_SECONDS)  # WHY: no start time means the widest window.
        start = max(oldest - ALARM_WINDOW_MARGIN_SECONDS, end - ALARM_MAX_WINDOW_SECONDS)  # WHY: cap the width.
        return min(start, end - ALARM_WINDOW_MARGIN_SECONDS), end  # WHY: the window is at least one day wide.

    def apply(
        self, selected: Sequence[MarvisActionRecord], documents: Mapping[str, dict[str, Any]]
    ) -> tuple[list[MarvisActionRecord], list[dict[str, Any]]]:
        """Return the selected records and documents with their alarm columns.

        Args:
            selected: The records that the export writes.
            documents: The raw document of every action in the list, keyed by the action uuid.

        Returns:
            The records and the documents, in the order of ``selected``.
        """
        chosen = [documents[record.uuid] for record in selected]  # WHY: the documents that the export writes.
        result = self._client.search_marvis_alarms(*self.window(chosen))  # WHY: one search for the whole run.
        if result.problem:  # WHY: a failed search must not stop the export.
            logger.warning(  # WHY: the operator learns why the alarm columns are empty.
                "The Marvis alarm search returned no usable result. %s The alarm columns stay empty.",
                result.problem,
            )
            return list(selected), chosen  # WHY: the export writes every action without alarm values.
        logger.info("Joining %d Marvis alarms to %d Marvis Actions", len(result.rows), len(selected))  # WHY: log.
        index = MarvisAlarmIndex(result.rows)  # WHY: map the alarms by their two keys.
        values = [index.columns(record.uuid) for record in selected]  # WHY: the alarm values of each action.
        records = [  # WHY: a frozen record needs a copy with its alarm columns filled.
            dataclasses.replace(record, **cells) for record, cells in zip(selected, values, strict=True)
        ]
        joined = [{**document, **cells} for document, cells in zip(chosen, values, strict=True)]  # WHY: same values.
        self._log_counts(values, index.unmatched_alarm_count(documents.keys()))  # WHY: result summary.
        return records, joined  # WHY: the export writes these rows and documents.

    @staticmethod
    def _log_counts(values: Sequence[Mapping[str, Any]], unmatched: int) -> None:
        """Log the number of joined actions and the number of alarms without an action."""
        joined = sum(1 for cells in values if cells)  # WHY: an empty map means that the action has no alarm.
        logger.log(  # WHY: the operator sees how many rows hold alarm values.
            DISPLAY_LEVEL,
            "Marvis alarm join: %d of %d exported actions have a Marvis alarm. %d have no alarm.",
            joined,
            len(values),
            len(values) - joined,
        )
        logger.log(  # WHY: an alarm without an action can point to a gap in the Marvis Actions list.
            DISPLAY_LEVEL, "Marvis alarms in the search window without an action in the list: %d", unmatched
        )
