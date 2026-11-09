"""Verify portal input privacy through Flask status and terminal replay."""

import builtins
import logging
import re
from dataclasses import replace
from pathlib import Path

import pytest
from flask.testing import FlaskClient

from src.foundation.models.operation_outcome import OperationOutcome
from web_portal.menu_registry import build_static_menu_actions
from web_portal.services.event_bus import PortalEventBus
from web_portal.services.input_hook import InputInterceptor
from web_portal.services.operation import OperationExecutor


def test_flask_status_and_terminal_replay_keep_queued_input_private(
    client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Keep the synthetic answer out of the completed status and replay."""
    answer = "synthetic-person@example.invalid"
    received: list[str] = []
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setattr(builtins, "input", InputInterceptor._patched_input)
    caplog.set_level(logging.DEBUG, logger="web_portal.services.input_hook")

    def handler() -> OperationOutcome:
        """Consume the queued answer without calling an external service."""
        received.append(input("Synthetic prompt: "))
        return OperationOutcome("completed", "Synthetic operation completed.")

    actions = build_static_menu_actions()
    actions["93"] = replace(actions["93"], handler=handler)
    event_bus = PortalEventBus()
    executor = OperationExecutor(actions, None, None, event_bus)
    monkeypatch.setitem(client.application.config, "OPERATION_EXECUTOR", executor)
    monkeypatch.setitem(client.application.config, "EVENT_BUS", event_bus)
    try:
        page = client.get("/operations")
        tokens = re.findall(r'<meta name="csrf-token" content="([^"]+)"', page.get_data(as_text=True))
        assert len(tokens) == 1
        start = client.post(
            "/api/operations/run",
            json={"menu_number": "93", "parameters": {"input_answers": [answer]}},
            headers={"X-CSRFToken": tokens[0]},
        )
        assert start.status_code == 202
        run_id = start.get_json()["run_id"]
        executor._runs[run_id]["_future"].result(timeout=10)
        status = client.get(f"/api/operations/status/{run_id}")
        replay = client.get(f"/api/operations/stream?run_id={run_id}")
        status_body = status.get_data(as_text=True)
        replay_body = replay.get_data(as_text=True)
        assert status.status_code == 200
        assert status.get_json()["status"] == "completed"
        assert replay.status_code == 200
        assert replay.mimetype == "text/event-stream"
        assert "event: complete" in replay_body
        assert received == [answer]
        assert {name: answer in body for name, body in {"status": status_body, "replay": replay_body}.items()} == {
            "status": False,
            "replay": False,
        }
        assert "InputInterceptor: consumed queued answer" in status_body
        assert "InputInterceptor: consumed queued answer" in replay_body
    finally:
        executor.shutdown(10)
        event_bus.stop()
