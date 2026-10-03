"""Tests for the guarded Marvis alarm acknowledge step of issue #3357."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.mist.intelligence.marvis.actions.acknowledgement import (
    ACK_OUTCOME_ACKNOWLEDGED,
    ACK_OUTCOME_NOT_SENT,
    MAX_ACKNOWLEDGE_BATCH_SIZE,
    MarvisAlarmAcknowledger,
)
from src.mist.intelligence.marvis.actions.model import RESOLUTION_CODES
from src.mist.intelligence.marvis.actions.selection import MarvisResolveRequest


def acknowledger(client: MagicMock | None = None) -> MarvisAlarmAcknowledger:
    """Return an acknowledger with synthetic resolve values and no live session."""
    request = MarvisResolveRequest(RESOLUTION_CODES[0], "Replaced the cable.", 1_700_000_000_000)
    return MarvisAlarmAcknowledger(client or MagicMock(), request, MagicMock())


class TestMarvisAlarmAcknowledger:
    """The second guard and the documented batch limit protect the write."""

    def test_a_blank_confirmation_sends_no_request(self) -> None:
        """The optional destructive step stays off when the operator does not confirm it."""
        client = MagicMock()
        with patch(
            "src.mist.intelligence.marvis.actions.acknowledgement.MarvisResolvePrompts.ask_acknowledge_confirmation",
            return_value=False,
        ):
            results = acknowledger(client).acknowledge(["alarm-1", "alarm-2"])
        assert client.acknowledge_marvis_alarms.call_count == 0
        assert {result.outcome for result in results.values()} == {ACK_OUTCOME_NOT_SENT}

    def test_each_request_holds_no_more_than_one_thousand_alarm_ids(self) -> None:
        """A list above the API limit becomes multiple explicit batches."""
        client = MagicMock()
        client.acknowledge_marvis_alarms.return_value = (200, "")
        alarm_ids = [f"alarm-{number}" for number in range(MAX_ACKNOWLEDGE_BATCH_SIZE + 1)]
        with patch(
            "src.mist.intelligence.marvis.actions.acknowledgement.MarvisResolvePrompts.ask_acknowledge_confirmation",
            return_value=True,
        ):
            results = acknowledger(client).acknowledge(alarm_ids)
        batches = [call.args[0] for call in client.acknowledge_marvis_alarms.call_args_list]
        print(f"The alarm acknowledge guard checked {len(alarm_ids)} alarms in {len(batches)} batches.")
        assert [len(batch) for batch in batches] == [1000, 1]
        assert len(results) == len(alarm_ids)
        assert {result.outcome for result in results.values()} == {ACK_OUTCOME_ACKNOWLEDGED}

    def test_the_note_holds_the_resolve_code_and_the_comment(self) -> None:
        """Each batch records why the operator resolved the related actions."""
        client = MagicMock()
        client.acknowledge_marvis_alarms.return_value = (200, "")
        with patch(
            "src.mist.intelligence.marvis.actions.acknowledgement.MarvisResolvePrompts.ask_acknowledge_confirmation",
            return_value=True,
        ):
            acknowledger(client).acknowledge(["alarm-1"])
        assert client.acknowledge_marvis_alarms.call_args.args[1] == (
            "MistHelper resolve code: suggested. Comment: Replaced the cable."
        )
