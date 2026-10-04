"""Tests for WebSockets stream settings."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # caplog checks warning lines.

import pytest  # The settings tests use the caplog fixture type.

from src.mist.realtime.websocket_streams.live.sessions.settings import (
    StreamSettings,
)  # The tests cover environment parsing.


class TestStreamSettings:
    """Verify the environment settings rules."""

    def test_defaults_and_payload(self) -> None:
        """Use safe defaults when the environment is empty."""
        settings = StreamSettings.from_environment({})  # Build settings from an empty source.
        assert settings.max_sessions == 5  # The default live limit is five.
        assert settings.buffer_bytes == 8 * 1024 * 1024  # The MB value becomes bytes.
        assert settings.limits_payload() == {
            "max_sessions": 5,
            "idle_seconds": 120,
            "capture_seconds": 60,
        }  # The public payload is stable.

    def test_flags_accept_enabled_and_disabled_values(self) -> None:
        """Accept each documented flag value."""
        enabled = StreamSettings.from_environment({"PORTAL_WS_ENABLE_CHANGES": "YeS"})  # Case must not matter.
        disabled = StreamSettings.from_environment({"PORTAL_WS_ENABLE_SHELL": "off"})  # Explicit off stays false.
        assert enabled.changes_enabled is True  # The enabled text turns the flag on.
        assert disabled.shell_enabled is False  # The disabled text keeps the flag off.

    def test_bad_values_warn_and_use_defaults(self, caplog: pytest.LogCaptureFixture) -> None:
        """Warn once for each bad value and use defaults."""
        caplog.set_level(logging.WARNING)  # Capture warnings from settings parsing.
        settings = StreamSettings.from_environment(
            {"PORTAL_WS_ENABLE_SHELL": "maybe", "PORTAL_WS_MAX_SESSIONS": "200", "PORTAL_WS_IDLE_SECONDS": "bad"}
        )  # Provide one bad flag, one range error, and one parse error.
        assert settings.shell_enabled is False  # Bad flags never unlock the shell.
        assert settings.max_sessions == 5  # Out-of-range numbers use the default.
        assert settings.idle_seconds == 120  # Non-numbers use the default.
        assert "PORTAL_WS_ENABLE_SHELL" in caplog.text  # The flag warning names the variable.
        assert "PORTAL_WS_MAX_SESSIONS" in caplog.text  # The range warning names the variable.
        assert "PORTAL_WS_IDLE_SECONDS" in caplog.text  # The parse warning names the variable.

    def test_range_edges_are_valid(self) -> None:
        """Accept each numeric range edge."""
        settings = StreamSettings.from_environment(
            {
                "PORTAL_WS_MAX_SESSIONS": "20",
                "PORTAL_WS_IDLE_SECONDS": "30",
                "PORTAL_WS_BUFFER_MESSAGES": "50",
                "PORTAL_WS_BUFFER_MB": "64",
                "PORTAL_WS_MAX_STREAM_MINUTES": "240",
            }
        )  # Provide each documented edge.
        assert settings.max_sessions == 20  # The upper live limit is valid.
        assert settings.idle_seconds == 30  # The lower idle limit is valid.
        assert settings.buffer_messages == 50  # The lower message limit is valid.
        assert settings.buffer_bytes == 64 * 1024 * 1024  # The upper byte limit is valid.
        assert settings.max_stream_seconds == 240 * 60  # The upper minute limit becomes seconds.


class TestTerminalHistorySetting:
    """Verify the terminal history size setting of issue #3671."""

    def test_default_keeps_one_mebibyte(self) -> None:
        """Keep 1,024 KiB of terminal output when the variable is absent."""
        settings = StreamSettings.from_environment({})  # Build settings from an empty source.
        assert settings.terminal_history_bytes == 1024 * 1024  # The default is 1 MiB.

    @pytest.mark.parametrize(
        ("raw", "expected_kib"),
        [
            ("256", 256),  # The lower edge is valid.
            ("8192", 8192),  # The upper edge is valid.
            (" 2048 ", 2048),  # Spaces around the number do not matter.
        ],
    )
    def test_range_values_convert_to_bytes(self, raw: str, expected_kib: int) -> None:
        """Convert each value inside the range from KiB to bytes."""
        settings = StreamSettings.from_environment({"PORTAL_WS_TERMINAL_HISTORY_KB": raw})  # Set one value.
        assert settings.terminal_history_bytes == expected_kib * 1024  # The KiB value becomes bytes.

    @pytest.mark.parametrize("raw", ["255", "8193", "lots", "-1", "1e3"])
    def test_bad_values_warn_and_use_the_default(self, raw: str, caplog: pytest.LogCaptureFixture) -> None:
        """Use the default and name the variable for an out-of-range value or a non-number."""
        caplog.set_level(logging.WARNING)  # Capture warnings from settings parsing.
        settings = StreamSettings.from_environment({"PORTAL_WS_TERMINAL_HISTORY_KB": raw})  # Set one bad value.
        assert settings.terminal_history_bytes == 1024 * 1024  # A bad value cannot change the limit.
        assert "PORTAL_WS_TERMINAL_HISTORY_KB" in caplog.text  # The warning names the variable.

    def test_public_limits_payload_does_not_change(self) -> None:
        """Keep the history size out of the public catalog payload."""
        settings = StreamSettings.from_environment({"PORTAL_WS_TERMINAL_HISTORY_KB": "4096"})  # Set a valid value.
        assert settings.limits_payload() == {
            "max_sessions": 5,
            "idle_seconds": 120,
            "capture_seconds": 60,
        }  # The catalog route sends the same keys as before.
