"""Unit tests for the bounded Redis SCAN loop in RetentionManager.

The retention sweep must never run the Redis KEYS command. KEYS blocks the
single Redis thread across the whole keyspace. These tests prove the sweep
uses a cursor-driven SCAN loop and stops at a fixed upper bound.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from src.db import retention
from src.db.retention import RetentionManager


class FakeRedisClient:
    """Record every command and reply with scripted SCAN batches."""

    def __init__(self, replies: list[tuple[int, list[str]]]) -> None:
        """Store the scripted replies and start an empty command log."""
        self.commands: list[tuple[Any, ...]] = []  # WHY: assert on real traffic
        self._replies = list(replies)  # WHY: copy so the test list stays intact

    def execute_command(self, *args: Any) -> tuple[int, list[str]]:
        """Log the command and pop the next scripted reply."""
        self.commands.append(args)  # WHY: the tests assert the command names
        if not self._replies:  # WHY: an unscripted call must end the loop
            return 0, []  # WHY: cursor 0 tells the caller the scan finished
        return self._replies.pop(0)  # WHY: replies run in the scripted order

    @property
    def command_names(self) -> list[str]:
        """Return the first word of each recorded command."""
        return [str(command[0]) for command in self.commands]  # WHY: name only


class EndlessRedisClient:
    """Reply with a full batch forever so the upper bound is the only exit."""

    def __init__(self, batch_size: int) -> None:
        """Store the batch size and start the call counter at zero."""
        self.batch_size = batch_size  # WHY: each reply holds this many keys
        self.calls = 0  # WHY: prove the bound stops the loop after few calls

    def execute_command(self, *args: Any) -> tuple[int, list[str]]:
        """Return a full batch and a non-zero cursor on every call."""
        self.calls += 1  # WHY: count the round trips the sweep costs
        keys = [f"device.{index}.avg_1h" for index in range(self.batch_size)]
        return 1, keys  # WHY: cursor 1 means "more keys remain" to the caller


def _manager(client: Any) -> RetentionManager:
    """Build a RetentionManager whose Redis writer holds the given client."""
    redis_writer = MagicMock()  # WHY: the writer is duck-typed in production
    redis_writer._client = client  # WHY: the manager reads this attribute
    return RetentionManager(  # WHY: ArangoDB is not used by these tests
        arango_writer=MagicMock(),
        redis_writer=redis_writer,
    )


class TestRedisScanReplacesKeys:
    """Verify the sweep issues SCAN and never issues KEYS."""

    def test_scan_is_used_and_keys_is_never_issued(self) -> None:
        """The first command must be SCAN and KEYS must never appear."""
        client = FakeRedisClient([(0, ["a.avg_1h", "b.avg_1h"])])
        result = _manager(client).check_redis_retention()
        assert result == 2  # WHY: the count must match the scripted batch
        assert "KEYS" not in client.command_names  # WHY: KEYS stalls Redis
        assert client.command_names == ["SCAN"]  # WHY: SCAN is the only command

    def test_scan_passes_match_and_a_bounded_count(self) -> None:
        """SCAN must carry MATCH with the pattern and a bounded COUNT."""
        client = FakeRedisClient([(0, [])])
        _manager(client).check_redis_retention()
        command = client.commands[0]  # WHY: only one round trip is scripted
        assert command[1] == 0  # WHY: the SCAN contract starts at cursor 0
        assert "MATCH" in command  # WHY: the filter must stay server-side
        assert retention.REDIS_COMPACTION_PATTERN in command  # WHY: same pattern
        assert "COUNT" in command  # WHY: COUNT bounds the work per batch
        assert command[-1] == retention.REDIS_SCAN_BATCH  # WHY: bounded batch

    def test_scan_follows_the_cursor_until_it_returns_to_zero(self) -> None:
        """The loop must sum every batch across all cursor round trips."""
        client = FakeRedisClient(
            [
                (7, ["a.avg_1h", "b.avg_1h"]),
                (9, ["c.avg_1h"]),
                (0, ["d.avg_1h", "e.avg_1h", "f.avg_1h"]),
            ]
        )
        result = _manager(client).check_redis_retention()
        assert result == 6  # WHY: 2 + 1 + 3 keys across the three batches
        assert client.command_names == ["SCAN", "SCAN", "SCAN"]  # WHY: 3 trips
        assert client.commands[1][1] == 7  # WHY: cursor 7 feeds the next call
        assert client.commands[2][1] == 9  # WHY: cursor 9 feeds the last call

    def test_a_bytes_cursor_still_advances_the_loop(self) -> None:
        """A raw protocol reply returns bytes, and the loop must accept it."""
        client = FakeRedisClient([(b"4", ["a.avg_1h"]), (b"0", ["b.avg_1h"])])  # type: ignore[list-item]
        result = _manager(client).check_redis_retention()
        assert result == 2  # WHY: both batches count toward the total
        assert client.commands[1][1] == 4  # WHY: the bytes cursor became an int


class TestRedisScanUpperBound:
    """Verify the sweep stops after a fixed number of scanned keys."""

    def test_the_bound_stops_the_loop_and_returns_a_partial_count(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An endless keyspace must not produce an endless scan."""
        monkeypatch.setattr(retention, "REDIS_SCAN_BATCH", 10)  # WHY: fast test
        monkeypatch.setattr(retention, "REDIS_SCAN_MAX_KEYS", 30)  # WHY: low cap
        client = EndlessRedisClient(batch_size=10)  # WHY: never returns cursor 0
        result = _manager(client).check_redis_retention()
        assert result == 30  # WHY: the partial count equals the upper bound
        assert client.calls == 3  # WHY: 3 batches of 10 keys reach the bound

    def test_the_default_bound_is_a_positive_integer(self) -> None:
        """A missing or zero bound would let the loop run without a limit."""
        assert isinstance(retention.REDIS_SCAN_MAX_KEYS, int)  # WHY: a real cap
        assert retention.REDIS_SCAN_MAX_KEYS > 0  # WHY: zero disables the cap
        assert isinstance(retention.REDIS_SCAN_BATCH, int)  # WHY: a real batch
        assert retention.REDIS_SCAN_BATCH > 0  # WHY: COUNT must be positive


class TestRedisScanContract:
    """Verify the return contract and the error handling shape do not change."""

    def test_a_missing_client_returns_zero(self) -> None:
        """A writer without a client reports zero checked keys."""
        redis_writer = MagicMock(spec=[])  # WHY: no _client attribute at all
        manager = RetentionManager(
            arango_writer=MagicMock(),
            redis_writer=redis_writer,
        )
        assert manager.check_redis_retention() == 0  # WHY: nothing to validate

    def test_a_redis_error_logs_a_warning_and_returns_zero(self) -> None:
        """An unreachable Redis server must not stop the sweep thread."""
        client = MagicMock()  # WHY: a client that raises on every command
        client.execute_command.side_effect = Exception("connection refused")
        assert _manager(client).check_redis_retention() == 0  # WHY: safe value

    def test_a_malformed_reply_returns_zero(self) -> None:
        """A reply that does not unpack must follow the same error path."""
        client = MagicMock()  # WHY: a client that answers with the wrong shape
        client.execute_command.return_value = []  # WHY: no cursor and no batch
        assert _manager(client).check_redis_retention() == 0  # WHY: safe value

    def test_the_result_is_always_an_int(self) -> None:
        """Callers count keys, so the method must return an int every time."""
        client = FakeRedisClient([(0, ["a.avg_1h"])])
        assert isinstance(_manager(client).check_redis_retention(), int)
