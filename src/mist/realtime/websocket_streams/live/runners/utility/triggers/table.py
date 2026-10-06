"""Build utility REST triggers from checked requests."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError
from src.mist.realtime.websocket_streams.intake.start_request.models import StartRequest
from src.mist.realtime.websocket_streams.live.runners.utility.triggers.body_builder import (
    CaptureBodyBuilder,
    CommandBodyBuilder,
)
from src.mist.realtime.websocket_streams.live.runners.utility.triggers.definitions import UtilityTriggerDefinitions
from src.mist.realtime.websocket_streams.live.runners.utility.triggers.models import (
    UtilityListen,
    UtilityRequest,
    UtilityTiming,
)
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)

logger = StructuredTransportLogger(logging.getLogger(__name__))


@dataclass(slots=True)
class UtilityRequestBuilder:
    """Build one complete utility request from one trigger row."""

    definitions: UtilityTriggerDefinitions
    commands: CommandBodyBuilder = field(default_factory=CommandBodyBuilder)
    captures: CaptureBodyBuilder = field(default_factory=CaptureBodyBuilder)

    def build(self, request: StartRequest, row: tuple[str, str, str, str, float]) -> UtilityRequest:
        """Return one complete utility request."""
        scope, suffix, body_kind, channel, quiet = row
        path = self._path(scope, suffix, request)
        body = self._body(body_kind, request)
        listen = self._listen(channel, quiet, request, body)
        return UtilityRequest(request.key, "POST", path, body, listen)

    @staticmethod
    def _path(scope: str, suffix: str, request: StartRequest) -> str:
        """Return the REST path for one trigger scope."""
        if scope == "org_pcap":
            return f"/api/v1/orgs/{request.target('org_id')}{suffix}"
        if scope == "site_pcap":
            return f"/api/v1/sites/{request.target('site_id')}{suffix}"
        site_id = request.target("site_id")
        device_id = request.target("device_id")
        return f"/api/v1/sites/{site_id}/devices/{device_id}{suffix}"

    def _body(self, kind: str, request: StartRequest) -> dict[str, object] | None:
        """Return the SDK-parity body."""
        if kind.endswith("_pcap"):
            return self.captures.build(kind, request)
        return self.commands.build(kind, request.parameters)

    def _listen(
        self, channel: str, quiet: float, request: StartRequest, body: dict[str, object] | None
    ) -> UtilityListen:
        """Return stream metadata for one trigger."""
        timing = self._timing(channel, quiet, body)
        values = {name: request.target(name) for name in ("site_id", "device_id", "org_id")}
        path = self.definitions.channel_path(channel).format_map(values)
        return UtilityListen(channel, path, timing)

    def _timing(self, channel: str, quiet: float, body: dict[str, object] | None) -> UtilityTiming:
        """Return time limits for one command or capture."""
        total = self.definitions.DEFAULT_TOTAL_SECONDS
        if channel in {"site_pcaps", "org_pcaps"} and body is not None:
            duration = body.get("duration")
            total = float(duration) + 10.0 if isinstance(duration, int) else total
        return UtilityTiming(self.definitions.FIRST_OUTPUT_SECONDS, max(5.0, quiet), total)


class UtilityTriggerTable:
    """Provide SDK-parity utility and shell trigger requests."""

    def __init__(self) -> None:
        """Build immutable definitions and the request builder."""
        self._definitions = UtilityTriggerDefinitions()
        self._builder = UtilityRequestBuilder(self._definitions)

    def keys(self) -> tuple[str, ...]:
        """Return supported utility keys."""
        keys = self._definitions.keys()
        logger.emit(logging.DEBUG, "utility_trigger_keys", {"count": len(keys)})
        return keys

    def request_for(self, request: StartRequest) -> UtilityRequest:
        """Return the trigger for one checked utility request."""
        logger.emit(logging.INFO, "utility_trigger_build", {"action": request.key})
        row = self._row(request.key)
        trigger = self._builder.build(request, row)
        logger.emit(logging.DEBUG, "utility_trigger_built", {"action": request.key})
        return trigger

    def shell_request(self, site_id: str, device_id: str, node: str | None = None) -> UtilityRequest:
        """Return the shell REST trigger."""
        logger.emit(logging.INFO, "utility_shell_trigger_build")
        path = f"/api/v1/sites/{site_id}/devices/{device_id}/shell"
        listen = UtilityListen("url", "", self._definitions.shell_timing())
        body: dict[str, object] = {"node": node} if node else {}
        logger.emit(logging.DEBUG, "utility_shell_trigger_built")
        return UtilityRequest("shell", "POST", path, body, listen)

    def _row(self, key: str) -> tuple[str, str, str, str, float]:
        """Return one supported trigger row."""
        row = self._definitions.row(key)
        if row is None:
            raise StreamRequestError("bad_request", "The utility trigger key is not supported.")
        return row
