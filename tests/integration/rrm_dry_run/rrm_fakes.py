"""Shared fake dependencies for the menu 291 RRM dry-run precedence tests."""

from __future__ import annotations  # WHY: keep annotations lightweight in test support code.

from typing import Any  # WHY: fakes store dynamic Mist request bodies.

from src.mist.resources.site.rrm_reset.operation import RrmResetDependencies


class RecordingClient:
    """Record every Mist read and every destructive request."""

    def __init__(self, events: list[str]) -> None:
        """Store the shared event log."""
        self.events = events  # WHY: the event log proves the before-capture order.
        self.requests: list[tuple[str, str, dict[str, Any]]] = []  # WHY: tests assert that no request ran.

    def get_current_plan(self, site_id: str) -> list[dict[str, Any]]:
        """Return one RRM plan row and record the read."""
        self.events.append(f"read:{site_id}")  # WHY: record the read order.
        return [{"site_id": site_id, "ap": "ap-1", "band": "5", "curr_channel": 36, "curr_power": 8}]

    def optimize(self, site_id: str, body: dict[str, Any]) -> None:
        """Record an optimize request."""
        self.events.append("optimize")  # WHY: a live run must appear in the event log.
        self.requests.append(("optimize", site_id, body))  # WHY: preserve the request details.

    def reset(self, site_id: str, body: dict[str, Any]) -> None:
        """Record a reset request."""
        self.events.append("reset")  # WHY: a live run must appear in the event log.
        self.requests.append(("reset", site_id, body))  # WHY: preserve the request details.


class RecordingWriter:
    """Record every durable write."""

    def __init__(self, events: list[str]) -> None:
        """Store the shared event log."""
        self.events = events  # WHY: the before capture must precede any request.

    def write_before(self, rows: list[dict[str, Any]]) -> bool:
        """Record the before write."""
        self.events.append(f"before:{len(rows)}")  # WHY: durable before capture is mandatory.
        return True  # WHY: let the workflow continue.

    def write_after(self, rows: list[dict[str, Any]]) -> bool:
        """Record the after write."""
        self.events.append(f"after:{len(rows)}")  # WHY: the after write follows a live request.
        return True  # WHY: let the workflow continue.

    def write_diff(self, rows: list[dict[str, Any]]) -> bool:
        """Record the diff write."""
        self.events.append(f"diff:{len(rows)}")  # WHY: the diff is the final evidence file.
        return True  # WHY: the writer accepted the rows.


class StaticPromptUtils:
    """Return one fixed site id."""

    def select_site(self) -> str:
        """Return the fixed test site id."""
        return "site-1"  # WHY: every RRM call needs a site id.


class ScriptedInputUtils:
    """Return scripted operator answers."""

    def __init__(self, answers: list[str]) -> None:
        """Store the scripted answers."""
        self.answers = answers  # WHY: tests control the action and the confirmation words.

    def safe_input(self, _prompt: str, context: str = "unknown") -> str:
        """Return the next scripted answer."""
        del context  # WHY: the fake ignores the prompt context.
        return self.answers.pop(0) if self.answers else ""  # WHY: an empty answer aborts rather than raises.


def build_dependencies(events: list[str], answers: list[str]) -> tuple[RrmResetDependencies, RecordingClient]:
    """Build recording dependencies and return them with the client."""
    client = RecordingClient(events)  # WHY: the client proves whether a destructive request ran.
    writer = RecordingWriter(events)  # WHY: the writer proves the durable before capture.
    deps = RrmResetDependencies(client, writer, StaticPromptUtils(), ScriptedInputUtils(answers), lambda _s: None)
    return deps, client  # WHY: tests assert on the client request log.
