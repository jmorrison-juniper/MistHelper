"""Read the WebSockets tab safety flags and limits.

Why:
    Issue #3551. The portal must bound each live WebSocket session before it
    opens a Mist stream. The defaults are safe, and a bad environment value
    falls back to the default with one warning that names the variable.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The portal uses the standard logger.
import os  # The default settings source is the process environment.
from collections.abc import Mapping  # The tests pass a small fake environment.
from dataclasses import dataclass  # The settings are immutable after build.

logger = logging.getLogger(__name__)  # Keep settings log records under this module.


@dataclass(frozen=True, slots=True)
class StreamSettings:
    """The WebSockets tab flags and resource limits.

    Attributes:
        changes_enabled: True when the change utility flag is on.
        shell_enabled: True when the shell utility flag is on.
        max_sessions: The maximum count of live sessions.
        idle_seconds: The maximum seconds without a page read.
        buffer_messages: The maximum count of buffered messages per session.
        buffer_bytes: The maximum buffered bytes per session.
        max_stream_seconds: The maximum life of a live session.
    """

    changes_enabled: bool = False  # The default keeps state-changing utilities locked.
    shell_enabled: bool = False  # The default keeps remote shells locked.
    max_sessions: int = 5  # The default matches the feature contract.
    idle_seconds: int = 120  # The default stops abandoned browser tabs quickly.
    buffer_messages: int = 500  # The default bounds the message list size.
    buffer_bytes: int = 8 * 1024 * 1024  # The default bounds memory per session.
    max_stream_seconds: int = 1800  # The default bounds channel and shell life.

    @classmethod
    def from_environment(cls, environ: Mapping[str, str] | None = None) -> StreamSettings:
        """Build settings from environment variables.

        Args:
            environ: The environment source, or None to read ``os.environ``.

        Returns:
            The checked settings.
        """
        logger.info("Reading WebSockets tab settings")  # Log before reading process state.
        source = os.environ if environ is None else environ  # Use the real environment only by default.
        settings = cls(
            changes_enabled=cls._read_flag(source, "PORTAL_WS_ENABLE_CHANGES"),
            shell_enabled=cls._read_flag(source, "PORTAL_WS_ENABLE_SHELL"),
            max_sessions=cls._read_number(source, "PORTAL_WS_MAX_SESSIONS", 5, 1, 20),
            idle_seconds=cls._read_number(source, "PORTAL_WS_IDLE_SECONDS", 120, 30, 3600),
            buffer_messages=cls._read_number(source, "PORTAL_WS_BUFFER_MESSAGES", 500, 50, 5000),
            buffer_bytes=cls._read_number(source, "PORTAL_WS_BUFFER_MB", 8, 1, 64) * 1024 * 1024,
            max_stream_seconds=cls._read_number(source, "PORTAL_WS_MAX_STREAM_MINUTES", 30, 1, 240) * 60,
        )  # Convert megabytes and minutes to runtime units.
        logger.debug("Read WebSockets tab settings with max_sessions=%s", settings.max_sessions)  # Log safe data.
        return settings  # Return the immutable settings record.

    def limits_payload(self) -> dict[str, int]:
        """Return the public limit values for the catalog route.

        Returns:
            A JSON-safe dictionary with the public limits.
        """
        logger.info("Building WebSockets tab limits payload")  # Log before building route data.
        payload = {
            "max_sessions": self.max_sessions,
            "idle_seconds": self.idle_seconds,
            "capture_seconds": 60,
        }  # Keep the capture limit fixed.
        logger.debug("Built WebSockets tab limits payload")  # Log after the payload is ready.
        return payload  # The catalog route adds this payload to its answer.

    @staticmethod
    def _read_flag(environ: Mapping[str, str], name: str) -> bool:
        """Return one checked flag value.

        Args:
            environ: The environment source.
            name: The variable name.

        Returns:
            True when the variable holds an enabled value.
        """
        raw = environ.get(name, "")  # A missing flag is off by design.
        value = raw.strip().lower()  # Case must not matter for operators.
        if value in {"1", "true", "yes", "on"}:  # These values enable the flag.
            return True  # The caller can unlock the feature.
        if value in {"", "0", "false", "no", "off"}:  # These values disable the flag.
            return False  # The default is the safe state.
        logger.warning("Ignoring invalid WebSockets flag %s", name)  # Name the bad variable only.
        return False  # A bad flag never unlocks a risky feature.

    @staticmethod
    def _read_number(environ: Mapping[str, str], name: str, default: int, minimum: int, maximum: int) -> int:
        """Return one checked integer value.

        Args:
            environ: The environment source.
            name: The variable name.
            default: The safe value used when the variable is bad.
            minimum: The lowest allowed value.
            maximum: The highest allowed value.

        Returns:
            The checked integer value, or the default.
        """
        raw = environ.get(name, "")  # A missing number uses the documented default.
        if raw == "":  # The operator did not set the variable.
            return default  # The default is inside the safe range.
        try:  # A non-number falls back to the default.
            value = int(raw.strip())  # The environment stores all values as text.
        except ValueError:  # The value is not a whole number.
            logger.warning("Ignoring invalid WebSockets number %s", name)  # Name the bad variable only.
            return default  # A bad number cannot weaken a limit.
        if minimum <= value <= maximum:  # The number is inside the documented range.
            return value  # The operator setting is safe to use.
        logger.warning("Ignoring out of range WebSockets number %s", name)  # Name the bad variable only.
        return default  # An out-of-range number cannot weaken a limit.
