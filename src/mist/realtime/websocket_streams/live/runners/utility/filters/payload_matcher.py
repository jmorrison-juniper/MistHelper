"""Match utility payloads to one trigger answer."""

from __future__ import annotations

from collections.abc import Mapping

from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError


class UtilityPayloadMatcher:
    """Extract matching command text or packet capture payloads."""

    _CAPTURE_CHANNELS = {"site_pcaps", "org_pcaps"}

    def __init__(self, channel: str) -> None:
        """Store one checked utility channel."""
        if channel not in {"cmd", *self._CAPTURE_CHANNELS}:
            raise StreamRequestError("bad_request", "The utility filter channel is not supported.")
        self._channel = channel

    def answer_value(self, answer: Mapping[str, object]) -> str:
        """Return the required match value from a trigger answer."""
        key = "id" if self._channel in self._CAPTURE_CHANNELS else "session"
        value = answer.get(key)
        if not isinstance(value, str) or value == "":
            raise StreamRequestError("bad_request", "The utility trigger answer has no match value.")
        return value

    def matches(self, payloads: list[object], value: str) -> list[object]:
        """Return matching content in arrival order."""
        matches: list[object] = []
        for payload in payloads:
            content = self.content(payload, value)
            if content is not None:
                matches.append(content)
        return matches

    def content(self, payload: object, value: str) -> object | None:
        """Return visible content when one payload matches."""
        event = self._event_payload(payload)
        if not isinstance(event, Mapping):
            return None
        if self._channel in self._CAPTURE_CHANNELS:
            return dict(event) if event.get("capture_id") == value else None
        raw = event.get("raw") if event.get("session") == value else None
        return raw if isinstance(raw, str) else None

    @staticmethod
    def _event_payload(payload: object) -> object:
        """Return an inner data payload when one exists."""
        if isinstance(payload, Mapping) and payload.get("event") == "data" and "data" in payload:
            return payload["data"]
        return payload
