"""Guarded Marvis alarm acknowledgement for menu 270.

Why:
    A resolved Marvis Action can have a Marvis alarm. An operator can choose
    to acknowledge only the alarms of actions that this run verified as
    resolved. The choice stays off until the operator types the exact count.

Safety:
    This module never calls ``ackOrgAllAlarms``. It sends only explicit alarm
    identifiers, with no more than 1,000 identifiers in one request.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions in the annotations of this module.

import logging  # WHY: log each guarded step and each batch result.
from collections.abc import Sequence  # WHY: type the alarm identifier list without a concrete class.
from dataclasses import dataclass  # WHY: return one fixed result shape for each alarm.

from src.marvis.actions.client import MarvisActionsClient  # WHY: keep every Mist API call in the client class.
from src.marvis.actions.selection import (  # WHY: reuse the resolve values and the guarded prompt.
    MarvisResolvePrompts,
    MarvisResolveRequest,
)
from src.utils.rate_limiting import AdaptivePacer  # WHY: protect the shared Mist API quota between batches.

logger = logging.getLogger(__name__)  # WHY: name the logger for filtered diagnostics.

MAX_ACKNOWLEDGE_BATCH_SIZE = 1000  # WHY: the bundled Mist API document limits each batch to 1,000 alarm IDs.
ACK_OUTCOME_ACKNOWLEDGED = "acknowledged"  # WHY: Mist accepted the batch that held this alarm.
ACK_OUTCOME_ERROR = "error"  # WHY: Mist refused the batch, or no HTTP answer arrived.
ACK_OUTCOME_NOT_SENT = "not_sent"  # WHY: the operator did not type the exact acknowledge confirmation.


@dataclass(frozen=True, slots=True)
class MarvisAlarmAcknowledgeResult:
    """The acknowledge result of one alarm."""

    alarm_id: str  # WHY: identify the alarm in the mode 3 results file.
    outcome: str  # WHY: state whether Mist accepted the acknowledge request.
    http_status: int | None  # WHY: keep the HTTP status, or no value when no request went out.
    message: str  # WHY: explain the outcome to the operator.


class MarvisAlarmAcknowledger:
    """Acknowledge verified alarms after a second typed confirmation."""

    def __init__(
        self,
        client: MarvisActionsClient,
        request: MarvisResolveRequest,
        pacer: AdaptivePacer,
    ) -> None:
        """Keep the API client, the resolve values, and the quota pacer."""
        self._client = client  # WHY: the client sends only the explicit batch endpoint.
        self._request = request  # WHY: the note records the reason code and the comment.
        self._pacer = pacer  # WHY: wait between two acknowledge batches.

    def acknowledge(self, alarm_ids: Sequence[str]) -> dict[str, MarvisAlarmAcknowledgeResult]:
        """Offer the acknowledge step, then return one result for each unique alarm."""
        unique_ids = list(dict.fromkeys(alarm_id for alarm_id in alarm_ids if alarm_id))  # WHY: send each alarm once.
        if not unique_ids:  # WHY: no verified resolved action has a joined alarm.
            logger.info("No Marvis alarm is eligible for acknowledgement")  # WHY: explain why no prompt appears.
            return {}  # WHY: no alarm result exists.
        if not MarvisResolvePrompts.ask_acknowledge_confirmation(len(unique_ids)):  # WHY: the step is off by default.
            return self._not_sent(unique_ids)  # WHY: record that the second guard stopped every alarm.
        return self._send_batches(unique_ids)  # WHY: the exact confirmation permits only these identifiers.

    def _send_batches(self, alarm_ids: Sequence[str]) -> dict[str, MarvisAlarmAcknowledgeResult]:
        """Send explicit alarm identifiers in batches of no more than 1,000."""
        results: dict[str, MarvisAlarmAcknowledgeResult] = {}  # WHY: one audit result for each alarm.
        batches = list(self._batches(alarm_ids))  # WHY: log the known total before the first request.
        for number, batch in enumerate(batches, start=1):  # WHY: each request has a stable progress number.
            logger.info(  # WHY: action log before the destructive API request.
                "Sending Marvis alarm acknowledge batch %d of %d with %d alarm IDs",
                number,
                len(batches),
                len(batch),
            )
            status, error = self._client.acknowledge_marvis_alarms(  # WHY: call the explicit Marvis list endpoint.
                batch,
                self._note(),
            )
            outcome = ACK_OUTCOME_ERROR if error else ACK_OUTCOME_ACKNOWLEDGED  # WHY: one batch has one answer.
            message = error or "Mist accepted the alarm acknowledge request."  # WHY: keep the batch answer.
            for alarm_id in batch:  # WHY: the results file needs one answer for each alarm.
                results[alarm_id] = MarvisAlarmAcknowledgeResult(alarm_id, outcome, status, message)  # WHY: audit.
            logger.debug(  # WHY: result summary after the API request.
                "Marvis alarm acknowledge batch %d returned HTTP %s for %d alarms",
                number,
                status,
                len(batch),
            )
            if number < len(batches):  # WHY: no wait is needed after the last batch.
                self._pacer.pace()  # WHY: protect the shared quota between requests.
        return results  # WHY: the workflow copies each result into its action row.

    def _note(self) -> str:
        """Return the note that records the resolve reason and comment."""
        comment = self._request.comment or "No comment."  # WHY: the note always states whether a comment existed.
        return f"MistHelper resolve code: {self._request.code.key}. Comment: {comment}"  # WHY: preserve the reason.

    @staticmethod
    def _batches(alarm_ids: Sequence[str]) -> list[list[str]]:
        """Return batches that never exceed the documented API limit."""
        return [  # WHY: a list makes the batch count available before the first request.
            list(alarm_ids[start : start + MAX_ACKNOWLEDGE_BATCH_SIZE])  # WHY: copy one bounded batch.
            for start in range(0, len(alarm_ids), MAX_ACKNOWLEDGE_BATCH_SIZE)  # WHY: visit every alarm once.
        ]

    @staticmethod
    def _not_sent(alarm_ids: Sequence[str]) -> dict[str, MarvisAlarmAcknowledgeResult]:
        """Return the results of a refused or blank acknowledge confirmation."""
        message = "The alarm acknowledge confirmation did not match, so no acknowledge request was sent."  # WHY: audit.
        return {  # WHY: each eligible alarm states that the guard stopped it.
            alarm_id: MarvisAlarmAcknowledgeResult(alarm_id, ACK_OUTCOME_NOT_SENT, None, message)  # WHY: no request.
            for alarm_id in alarm_ids  # WHY: record every eligible alarm.
        }
