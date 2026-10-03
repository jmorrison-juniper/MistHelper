"""Stop only the packet capture that belongs to one utility run."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING

from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)

if TYPE_CHECKING:
    from src.websocket_streams.live.runners.utility.runner.utility_runner import ApiSessionProtocol, RunContext

logger = StructuredTransportLogger(logging.getLogger(__name__))


class CaptureStopper:
    """Stop a packet capture only when its identifier matches."""

    def __init__(self, apisession: ApiSessionProtocol) -> None:
        """Store the checked API session."""
        self._apisession = apisession

    def stop_site(self, site_id: str, capture_id: str) -> bool:
        """Stop a matching site capture."""
        logger.emit(logging.INFO, "site_capture_stop_check")
        response = self._apisession.mist_get(f"/api/v1/sites/{site_id}/pcaps?limit=1")
        self._require_success(response, "lookup")
        if not self._has_capture(response, capture_id):
            return False
        response = self._apisession.mist_delete(f"/api/v1/sites/{site_id}/pcaps")
        self._require_success(response, "stop")
        logger.emit(logging.DEBUG, "site_capture_stopped", {"status": "stopped"})
        return True

    def stop_org(self, org_id: str, capture_id: str) -> bool:
        """Stop a matching organization capture."""
        logger.emit(logging.INFO, "org_capture_stop_check")
        response = self._apisession.mist_get(f"/api/v1/orgs/{org_id}/pcaps?limit=1")
        self._require_success(response, "lookup")
        if not self._has_capture(response, capture_id):
            return False
        response = self._apisession.mist_delete(f"/api/v1/orgs/{org_id}/pcaps")
        self._require_success(response, "stop")
        logger.emit(logging.DEBUG, "org_capture_stopped", {"status": "stopped"})
        return True

    @staticmethod
    def _require_success(response: object, action: str) -> None:
        """Reject failed or unavailable HTTP status before reporting cleanup."""
        logger.emit(logging.INFO, "capture_response_check", {"action": action, "count": 1})
        status = getattr(response, "status_code", None)
        if not isinstance(status, int) or isinstance(status, bool) or status != 200:
            logger.emit(logging.ERROR, "capture_response_failed", {"action": action, "count": 1, "status": "failed"})
            raise RuntimeError(f"The capture {action} failed. The API did not confirm status 200.")
        logger.emit(logging.DEBUG, "capture_response_checked", {"action": action, "count": 1, "status": 200})

    @staticmethod
    def _has_capture(response: object, capture_id: str) -> bool:
        """Return whether one response names the capture."""
        data = getattr(response, "data", None)
        if isinstance(data, list):
            rows = data
        elif isinstance(data, Mapping):
            rows = data.get("results", [])
        else:
            rows = []
        return any(isinstance(row, Mapping) and row.get("id") == capture_id for row in rows)


class CaptureCleanup:
    """Choose capture cleanup from one completed run."""

    def __init__(self, context: RunContext) -> None:
        """Store the run context."""
        self._context = context

    def stop_if_needed(self) -> None:
        """Stop a matching capture after an operator stop."""
        target = self._target()
        if target is None:
            return
        scope, capture_id = target
        actions = {
            "org_pcaps": lambda: CaptureStopper(self._context.apisession).stop_org(
                self._context.request.target("org_id"), capture_id
            ),
            "site_pcaps": lambda: CaptureStopper(self._context.apisession).stop_site(
                self._context.request.target("site_id"), capture_id
            ),
        }
        actions[scope]()

    def _target(self) -> tuple[str, str] | None:
        """Return the stopped capture scope and identifier."""
        trigger = self._context.state.trigger
        if not self._context.state.stopping.is_set() or trigger is None:
            return None
        capture_id = (self._context.state.answer or {}).get("id") if trigger.listen.channel != "cmd" else None
        if not isinstance(capture_id, str):
            return None
        return trigger.listen.channel, capture_id
