"""Tests for the Redis socket timeout values that every client must carry.

Why:
    Issue #1918 reports that the token cache, the session store, and the rate
    limiter built a Redis client with no socket timeout. A host that drops
    packets stays silent instead of refusing the connection, so the caller waits
    without a limit and the worker never returns. These tests hold the limits in
    place at every call site.
"""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.shared.redis_timeouts import REDIS_SOCKET_TIMEOUT_SECONDS, redis_timeout_kwargs

# WHY: the two keyword arguments that redis-py reads for the socket limits.
REQUIRED_KEYS = ("socket_timeout", "socket_connect_timeout")

# WHY: every module that builds a Redis client. A new client must join this list.
CLIENT_MODULES = (
    "src/shared/mist/session.py",
    "src/shared/services/session_store.py",
    "src/api/middleware/rate_limit.py",
    "src/api/routes/health.py",
)


def _settings_double(read: float = 7.5, connect: float = 2.5) -> MagicMock:
    """Return a settings double that carries both timeout fields."""
    settings = MagicMock()  # WHY: the helper reads two attributes only.
    settings.redis_socket_timeout_seconds = read
    settings.redis_connect_timeout_seconds = connect
    return settings


class TestRedisTimeoutKwargs:
    """Cover the helper that every call site reads."""

    def test_both_keys_are_present(self) -> None:
        """The helper must return both socket limits."""
        with patch("src.shared.config.settings.get_settings", return_value=_settings_double()):
            kwargs = redis_timeout_kwargs()
        # WHY: a missing key restores the unlimited wait that issue #1918 reports.
        assert set(kwargs) == set(REQUIRED_KEYS)

    def test_the_settings_values_reach_the_client(self) -> None:
        """The helper must pass the configured values, not the module default."""
        with patch(
            "src.shared.config.settings.get_settings",
            return_value=_settings_double(read=7.5, connect=2.5),
        ):
            kwargs = redis_timeout_kwargs()
        # WHY: a hard-coded value would ignore the operator's configuration.
        assert kwargs["socket_timeout"] == pytest.approx(7.5)
        assert kwargs["socket_connect_timeout"] == pytest.approx(2.5)

    def test_every_value_is_a_number(self) -> None:
        """A string from the environment must reach redis-py as a number."""
        with patch(
            "src.shared.config.settings.get_settings",
            return_value=_settings_double(read="3", connect="4"),
        ):
            kwargs = redis_timeout_kwargs()
        # WHY: redis-py compares the limit against a clock, so a string would raise.
        assert all(isinstance(value, float) for value in kwargs.values())

    def test_no_limit_is_zero_or_negative(self) -> None:
        """A limit of zero or less would restore the unlimited wait."""
        with patch("src.shared.config.settings.get_settings", return_value=_settings_double()):
            kwargs = redis_timeout_kwargs()
        # WHY: redis-py reads 0 and None as "wait without a limit".
        assert all(value > 0 for value in kwargs.values())

    def test_the_shared_default_is_positive(self) -> None:
        """The module default must be a usable limit."""
        # WHY: the default applies when the operator sets no environment variable.
        assert REDIS_SOCKET_TIMEOUT_SECONDS > 0


class TestEveryCallSitePassesTheLimits:
    """Prove that no from_url call can omit the socket limits."""

    @pytest.mark.parametrize("module_path", CLIENT_MODULES)
    def test_from_url_receives_the_timeout_kwargs(self, module_path: str) -> None:
        """Every from_url call must spread redis_timeout_kwargs into its arguments."""
        # WHY: a unit test can reach one call site at a time. A source scan reaches
        # every call site at once, so a new client cannot skip the limits unseen.
        source = Path(__file__).resolve().parents[3] / module_path
        tree = ast.parse(source.read_text(encoding="utf-8"))
        # WHY: a module can call redis_lib.Redis.from_url or a bare from_url that it
        # imported by name. Both forms build a client, so both forms need the limits.
        calls = [
            node for node in ast.walk(tree) if isinstance(node, ast.Call) and self._callee_name(node) == "from_url"
        ]
        assert calls, f"{module_path} builds no Redis client, so this list is stale"
        for call in calls:
            spread = [kw for kw in call.keywords if kw.arg is None]
            assert spread, (
                f"{module_path} line {call.lineno}: from_url carries no **kwargs spread, "
                "so the Redis client waits without a socket limit"
            )
            names = {
                node.func.id
                for kw in spread
                for node in ast.walk(kw.value)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            }
            assert "redis_timeout_kwargs" in names, (
                f"{module_path} line {call.lineno}: from_url spreads a value that is not " "redis_timeout_kwargs()"
            )

    @staticmethod
    def _callee_name(node: ast.Call) -> str | None:
        """Return the final name of the callee, for a bare call or an attribute call."""
        if isinstance(node.func, ast.Attribute):
            return node.func.attr  # WHY: matches redis_lib.Redis.from_url(...).
        if isinstance(node.func, ast.Name):
            return node.func.id  # WHY: matches a from_url that the module imported.
        return None
