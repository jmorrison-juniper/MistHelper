"""Tests for menu 291 RRM optimize or reset operation."""

from __future__ import annotations  # WHY: keep annotations lightweight during tests.

from typing import Any  # WHY: fakes store dynamic request bodies.

from src.site.rrm_reset.operation import RrmResetDependencies, RrmResetOperation


class FakeClient:
    """Fake RRM client that records operation order."""

    def __init__(self, events: list[str]) -> None:
        """Store the shared event log."""
        self.events = events  # WHY: tests assert before-write ordering.
        self.requests: list[tuple[str, str, dict[str, Any]]] = []  # WHY: tests assert mutation calls.

    def get_current_plan(self, site_id: str) -> list[dict[str, Any]]:
        """Return a different plan for before and after reads."""
        self.events.append(f"read:{site_id}")  # WHY: record read order.
        if self.events.count(f"read:{site_id}") == 1:  # WHY: first read is before capture.
            return [{"site_id": site_id, "ap": "ap-1", "band": "5", "curr_channel": 36, "curr_power": 8}]
        return [{"site_id": site_id, "ap": "ap-1", "band": "5", "curr_channel": 40, "curr_power": 8}]

    def optimize(self, site_id: str, body: dict[str, Any]) -> None:
        """Record an optimize request."""
        self.events.append("optimize")  # WHY: order must follow before write.
        self.requests.append(("optimize", site_id, body))  # WHY: preserve request details.

    def reset(self, site_id: str, body: dict[str, Any]) -> None:
        """Record a reset request."""
        self.events.append("reset")  # WHY: order must follow before write.
        self.requests.append(("reset", site_id, body))  # WHY: preserve request details.


class FakeWriter:
    """Fake writer that records file order."""

    def __init__(self, events: list[str]) -> None:
        """Store the shared event log."""
        self.events = events  # WHY: tests assert before-write order.
        self.diff_rows: list[dict[str, Any]] = []  # WHY: tests assert changed rows.

    def write_before(self, rows: list[dict[str, Any]]) -> bool:
        """Record the before write."""
        self.events.append(f"before:{len(rows)}")  # WHY: before must precede mutation.
        return True  # WHY: allow workflow to continue.

    def write_after(self, rows: list[dict[str, Any]]) -> bool:
        """Record the after write."""
        self.events.append(f"after:{len(rows)}")  # WHY: after must follow mutation.
        return True  # WHY: allow workflow to continue.

    def write_diff(self, rows: list[dict[str, Any]]) -> bool:
        """Record the diff write."""
        self.events.append(f"diff:{len(rows)}")  # WHY: diff is final evidence.
        self.diff_rows = rows  # WHY: preserve diff output for assertions.
        return True  # WHY: writer accepted rows.


class FakePromptUtils:
    """Fake site selector."""

    def select_site(self) -> str:
        """Return one selected site."""
        return "site-1"  # WHY: tests need a valid site id.


class FakeInputUtils:
    """Fake EOF-safe input helper."""

    def __init__(self, answers: list[str]) -> None:
        """Store prompt answers."""
        self.answers = answers  # WHY: tests control action and confirmation.

    def safe_input(self, _prompt: str, context: str = "unknown") -> str:
        """Return the next prompt answer."""
        del context  # WHY: context is not needed by the fake.
        return self.answers.pop(0)  # WHY: prompts consume answers in order.


def _dependencies(events: list[str], answers: list[str]) -> tuple[RrmResetDependencies, FakeClient, FakeWriter]:
    """Create operation dependencies for one test."""
    client = FakeClient(events)  # WHY: record Mist API calls.
    writer = FakeWriter(events)  # WHY: record output writes.
    deps = RrmResetDependencies(client, writer, FakePromptUtils(), FakeInputUtils(answers), lambda _seconds: None)
    return deps, client, writer  # WHY: tests need both dependencies and fakes.


def test_rrm_reset_optimize_writes_before_before_request(monkeypatch: Any) -> None:
    """OPTIMIZE sends no request until after the before write."""
    monkeypatch.setenv("RRM_SETTLE_SECONDS", "0")  # WHY: no wait in the test.
    events: list[str] = []  # WHY: shared event log proves order.
    deps, client, writer = _dependencies(events, ["OPTIMIZE", "OPTIMIZE"])  # WHY: valid action and confirmation.
    RrmResetOperation.run(dry_run=False, dependencies=deps)  # WHY: execute workflow under test.
    assert events[:3] == ["read:site-1", "before:1", "optimize"]  # WHY: before write must precede mutation.
    assert client.requests[0][0] == "optimize"  # WHY: selected action maps to optimize.
    assert writer.diff_rows[0]["before_channel"] == "36"  # WHY: diff includes the before channel.
    assert writer.diff_rows[0]["after_channel"] == "40"  # WHY: diff includes the after channel.


def test_rrm_reset_reset_writes_before_before_request(monkeypatch: Any) -> None:
    """RESET sends no request until after the before write."""
    monkeypatch.setenv("RRM_SETTLE_SECONDS", "0")  # WHY: no wait in the test.
    events: list[str] = []  # WHY: shared event log proves order.
    deps, client, _writer = _dependencies(events, ["RESET", "RESET"])  # WHY: valid reset flow.
    RrmResetOperation.run(dry_run=False, dependencies=deps)  # WHY: execute workflow under test.
    assert events[:3] == ["read:site-1", "before:1", "reset"]  # WHY: before write must precede mutation.
    assert client.requests[0][0] == "reset"  # WHY: selected action maps to reset.


def test_rrm_reset_wrong_confirmation_sends_no_request(monkeypatch: Any) -> None:
    """Wrong confirmation prevents the destructive request."""
    monkeypatch.setenv("RRM_SETTLE_SECONDS", "0")  # WHY: no wait in the test.
    events: list[str] = []  # WHY: shared event log proves no mutation.
    deps, client, _writer = _dependencies(events, ["RESET", "OPTIMIZE"])  # WHY: action and confirmation differ.
    RrmResetOperation.run(dry_run=False, dependencies=deps)  # WHY: execute refusal path.
    assert client.requests == []  # WHY: wrong confirmation must send no request.
    assert events == ["read:site-1", "before:1"]  # WHY: only before evidence is written.


def test_rrm_reset_dry_run_sends_no_request(monkeypatch: Any) -> None:
    """Dry-run writes the before capture and sends no Mist change request."""
    monkeypatch.setenv("RRM_SETTLE_SECONDS", "0")  # WHY: no wait in the test.
    events: list[str] = []  # WHY: shared event log proves no mutation.
    deps, client, _writer = _dependencies(events, ["OPTIMIZE"])  # WHY: dry-run does not ask confirmation.
    RrmResetOperation.run(dry_run=True, dependencies=deps)  # WHY: execute dry-run path.
    assert client.requests == []  # WHY: dry-run must not send a destructive request.
    assert events == ["read:site-1", "before:1"]  # WHY: dry-run writes the before capture only.
