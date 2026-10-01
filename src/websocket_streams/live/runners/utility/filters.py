"""Filter utility stream messages by trigger answer.

Why:
    Issue #3671 opens the stream before it sends the REST trigger. Early
    messages must wait until the trigger answer supplies the session value or
    capture value.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The filter logs counts only, never device output.
import threading  # The stream reader and trigger thread can share one filter.
from collections.abc import Mapping  # Trigger answers and stream payloads are mappings.

from src.websocket_streams.intake.fields import StreamRequestError  # Bad trigger answers use the contract error.

logger = logging.getLogger(__name__)  # Keep utility filter log records under this module name.


class UtilityMessageFilter:
    """Keep only messages that belong to one utility trigger."""

    _LIMIT = 2000  # Early events are bounded to protect memory.
    _CAPTURE_CHANNELS = {"site_pcaps", "org_pcaps"}  # Capture streams match by capture identifier.

    def __init__(self, channel: str) -> None:
        """Build one filter.

        Args:
            channel: The logical channel from ``UtilityListen``.
        """
        logger.info("Building WebSocket utility message filter for channel %s", channel)  # Log safe metadata only.
        if channel not in {"cmd", "site_pcaps", "org_pcaps"}:  # URL sessions do not use this filter.
            raise StreamRequestError("bad_request", "The utility filter channel is not supported.")  # Refuse bad use.
        self._channel = channel  # Store the channel for match rules.
        self._value: str | None = None  # The trigger answer supplies the match value.
        self._held: list[object] = []  # Early payloads wait here before bind.
        self._dropped = 0  # Count held payloads that overflow the limit.
        self._lock = threading.Lock()  # Protect shared filter state.
        logger.debug("Built WebSocket utility message filter for channel %s", channel)  # Log creation.

    @property
    def dropped_count(self) -> int:
        """Return the count of payloads dropped before bind.

        Returns:
            The dropped payload count.
        """
        with self._lock:  # Read shared state under the lock.
            return self._dropped  # Return the memory protection count.

    def bind(self, answer: Mapping[str, object]) -> list[object]:
        """Bind the filter to a trigger answer.

        Args:
            answer: The REST trigger answer from Mist.

        Returns:
            The held matching payloads in arrival order.

        Raises:
            StreamRequestError: The answer does not hold a match value.
        """
        logger.info("Binding WebSocket utility message filter")  # Log before state change.
        value = self._answer_value(answer)  # Extract the session or capture identifier.
        with self._lock:  # Change shared state and drain held payloads together.
            self._value = value  # Future offers can filter at once.
            held = self._held  # Copy the held list reference before clearing.
            self._held = []  # Release early payload memory.
        matches = self._matches(held)  # Filter outside the lock.
        logger.debug("Bound WebSocket utility message filter with %s held matches", len(matches))  # Log the count.
        return matches  # Preserve arrival order.

    def offer(self, payload: object) -> list[object]:
        """Offer one stream payload to the filter.

        Args:
            payload: The decoded stream payload.

        Returns:
            A one-item list for a matching payload, or an empty list.
        """
        with self._lock:  # Read and update shared filter state.
            if self._value is None:  # The trigger answer has not arrived yet.
                self._hold(payload)  # Store or count the early payload.
                return []  # A caller receives nothing before bind.
            value = self._value  # Copy the match value for use outside the lock.
        result = self._content(payload, value)  # Extract matching content outside the lock.
        return [result] if result is not None else []  # Match the contract list shape.

    def _hold(self, payload: object) -> None:
        """Hold an early payload or count it as dropped.

        Args:
            payload: The early payload.
        """
        if len(self._held) >= self._LIMIT:  # The queue is full.
            self._dropped += 1  # Count the protected drop.
            logger.debug("Dropped early WebSocket utility payload count %s", self._dropped)  # Log no payload content.
            return  # The payload is intentionally discarded.
        self._held.append(payload)  # Keep arrival order for bind.

    def _answer_value(self, answer: Mapping[str, object]) -> str:
        """Return the match value from a trigger answer.

        Args:
            answer: The trigger answer.

        Returns:
            The session or capture identifier.

        Raises:
            StreamRequestError: The match value is absent.
        """
        key = "id" if self._channel in self._CAPTURE_CHANNELS else "session"  # Captures use the capture id.
        value = answer.get(key)  # Read the trigger answer value.
        if not isinstance(value, str) or value == "":  # Empty values cannot filter safely.
            raise StreamRequestError("bad_request", "The utility trigger answer has no match value.")  # Refuse it.
        return value  # The caller stores this value.

    def _matches(self, payloads: list[object]) -> list[object]:
        """Return matching content from held payloads.

        Args:
            payloads: The held payloads.

        Returns:
            Matching content in arrival order.
        """
        value = self._value or ""  # Bind always sets this before calling.
        return [content for payload in payloads if (content := self._content(payload, value)) is not None]  # Filter.

    def _content(self, payload: object, value: str) -> object | None:
        """Return the content for one matching payload.

        Args:
            payload: The decoded stream payload.
            value: The expected session or capture identifier.

        Returns:
            The content to show, or None when the payload does not match.
        """
        event = self._event_payload(payload)  # Accept full stream events and inner payloads.
        if not isinstance(event, Mapping):  # Non-dictionary payloads cannot match.
            return None  # Drop malformed payloads.
        if self._channel in self._CAPTURE_CHANNELS:  # Capture events return the whole payload.
            return dict(event) if event.get("capture_id") == value else None  # Return a copy of the matching payload.
        raw = event.get("raw") if event.get("session") == value else None  # Command events return raw text only.
        return raw if isinstance(raw, str) else None  # Drop missing or non-text raw values.

    @staticmethod
    def _event_payload(payload: object) -> object:
        """Return the inner data payload when present.

        Args:
            payload: A decoded stream event or payload.

        Returns:
            The inner data value, or the original payload.
        """
        if isinstance(payload, Mapping) and payload.get("event") == "data" and "data" in payload:  # Stream event form.
            return payload["data"]  # The filter matches the event payload.
        return payload  # The caller already supplied the payload.
