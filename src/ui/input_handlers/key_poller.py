"""Cross-platform non-blocking keyboard polling for the MistHelper TUI.

Replaces ``MistHelperTUI.check_keyboard_input`` (CC=59) with two focused
platform classes and small dispatch dictionaries — every helper here is CC <= 10.
"""

from __future__ import annotations

import logging
import sys
import time
from typing import Any

# Dispatch table for Windows special-key second bytes (msvcrt: \xe0 / \x00 prefix).
# Each value is the canonical key name returned to the dispatcher.
_WINDOWS_SPECIAL_KEYS: dict[bytes, str] = {
    b"H": "up",  # Up arrow
    b"P": "down",  # Down arrow
    b"K": "left",  # Left arrow
    b"M": "right",  # Right arrow
    b"I": "page_up",  # Page Up (0x49)
    b"Q": "page_down",  # Page Down (0x51)
    b"G": "h",  # Home -> reuse "h" hotkey for jump-to-top
    b"O": "e",  # End  -> reuse "e" hotkey for jump-to-end
}

# Dispatch table for Unix CSI sequences (ESC [ X ...).
# Only the simple single-letter terminators are mapped here. The "5~" / "6~"
# page sequences are handled inline in _parse_unix_csi because they require
# inspecting the third byte.
_UNIX_CSI_LETTERS: dict[str, str] = {
    "A": "up",
    "B": "down",
    "C": "right",
    "D": "left",
    "H": "h",
    "F": "e",
}


class _WindowsKeyPoller:
    """Non-blocking keyboard poller for the Windows platform (msvcrt-backed)."""

    def __init__(self, tui: Any) -> None:
        self._tui = tui  # Back-reference for debug flag access
        self._msvcrt = tui.msvcrt  # Cached msvcrt module reference

    def poll(self) -> str | None:
        """Return the next pressed key as a canonical string, or ``None``."""
        logging.debug("TUI_DEBUG: WindowsKeyPoller.poll() invoked")  # Action log: before poll
        if not self._msvcrt.kbhit():  # Fast path: nothing buffered
            return None  # Caller will sleep and retry
        raw_byte = self._msvcrt.getch()  # Pull first byte from kbhit buffer
        if self._tui.debug_mode:  # Debug-mode trace of raw byte
            logging.debug("TUI_DEBUG: Raw key byte received: %r", raw_byte)
        if raw_byte in (b"\xe0", b"\x00"):  # Special-key escape prefixes
            return self._read_special_key()  # Delegate to second-byte dispatcher
        decoded = raw_byte.decode("utf-8", errors="ignore").lower()  # Normal printable -> lowercase string
        logging.debug("TUI_DEBUG: Decoded key: %r", decoded)  # Action log: after decode
        return str(decoded)  # Coerce to plain str for typing

    def _read_special_key(self) -> str | None:
        """Resolve the second byte of a Windows special-key sequence."""
        second = self._msvcrt.getch()  # Read the follow-up byte
        if self._tui.debug_mode:  # Debug trace of second byte
            logging.debug("TUI_DEBUG: Special key second byte: %r", second)
        mapped = _WINDOWS_SPECIAL_KEYS.get(second)  # Look up canonical name
        if mapped is None and self._tui.debug_mode:  # Unknown sequence -> log only
            logging.debug("TUI_DEBUG: Unhandled special key: %r", second)
        return mapped  # May be None for unknown keys


class _UnixKeyPoller:
    """Non-blocking keyboard poller for Unix/Linux platforms (select-backed)."""

    _MAX_CSI_ATTEMPTS = 4  # Up to 4 inter-byte read attempts
    _WAIT_INCREMENT_S = 0.05  # 50ms wait between attempts (200ms total)

    def __init__(self, tui: Any) -> None:
        self._tui = tui  # Back-reference for debug flag access
        self._select = tui.select  # Cached select module reference

    def poll(self) -> str | None:
        """Return the next pressed key as a canonical string, or ``None``."""
        logging.debug("TUI_DEBUG: UnixKeyPoller.poll() invoked")  # Action log: before poll
        if not self._select.select([sys.stdin], [], [], 0)[0]:  # Non-blocking readability check
            return None  # No data ready
        first_char = sys.stdin.read(1)  # Read the first byte
        if self._tui.debug_mode:  # Debug trace of raw byte
            logging.debug("TUI_DEBUG: Unix raw key: %r", first_char)
        if first_char == "\x1b":  # ESC -> may begin a CSI sequence
            return self._parse_unix_csi()  # Delegate to CSI parser
        return first_char.lower()  # Plain printable key

    def _parse_unix_csi(self) -> str | None:
        """Read remaining bytes of an ESC-prefixed CSI sequence and map it."""
        remaining = self._read_csi_payload()  # Drain the rest of the sequence
        if not remaining:  # Bare ESC -> treat as escape key
            return "escape"
        if not remaining.startswith("["):  # ESC followed by non-bracket -> ignore
            if self._tui.debug_mode:
                logging.debug("TUI_DEBUG: Unix ESC + non-CSI: %r", remaining)
            return None
        arrow_code = remaining[1:2]  # Single-letter CSI terminator
        if arrow_code == "5" and remaining[2:3] == "~":  # CSI 5~  -> Page Up
            return "page_up"
        if arrow_code == "6" and remaining[2:3] == "~":  # CSI 6~  -> Page Down
            return "page_down"
        mapped = _UNIX_CSI_LETTERS.get(arrow_code)  # Map A/B/C/D/H/F via dispatch dict
        if mapped is None and self._tui.debug_mode:  # Unknown CSI letter -> log only
            logging.debug("TUI_DEBUG: Unrecognized CSI: ESC[%s", arrow_code)
        return mapped  # None means unhandled

    def _read_csi_payload(self) -> str:
        """Progressive read of CSI payload to tolerate container TTY latency."""
        buffer = ""  # Accumulator for read bytes
        for attempt in range(self._MAX_CSI_ATTEMPTS):  # Bounded retry loop
            buffer = self._drain_pending(buffer)  # Drain any currently-ready bytes
            if self._is_complete_arrow(buffer):  # Short-circuit on complete A/B/C/D
                return buffer
            if attempt < self._MAX_CSI_ATTEMPTS - 1:  # Not last attempt -> wait then retry
                time.sleep(self._WAIT_INCREMENT_S)
        return buffer  # Return whatever we managed to read

    def _drain_pending(self, buffer: str) -> str:
        """Drain all bytes that are currently readable on stdin into ``buffer``."""
        while self._select.select([sys.stdin], [], [], 0)[0]:  # While bytes remain readable
            buffer += sys.stdin.read(1)  # Append next byte
        return buffer

    @staticmethod
    def _is_complete_arrow(buffer: str) -> bool:
        """Return True when ``buffer`` is a complete CSI arrow (ESC [ A/B/C/D)."""
        return len(buffer) >= 2 and buffer[0] == "[" and buffer[1] in "ABCD"


class KeyPoller:
    """Public façade exposed to MistHelperTUI — picks the right platform poller."""

    def __init__(self, tui: Any) -> None:
        """Pick the platform-specific key poller implementation once at construction."""
        self._tui = tui  # Back-reference for shared state
        if tui.IS_WINDOWS:  # Platform selection happens once
            self._impl: Any = _WindowsKeyPoller(tui)  # Windows uses msvcrt path
        else:
            self._impl = _UnixKeyPoller(tui)  # Unix uses select+CSI path

    def poll(self) -> str | None:
        """Return the next pressed key, or ``None`` if no input is ready."""
        try:
            result: str | None = self._impl.poll()  # Delegate to platform implementation
            return result
        except Exception as error:  # Preserve original error-tolerant shape
            logging.debug("TUI_MODE: Keyboard input error - %s", error)
            return None
