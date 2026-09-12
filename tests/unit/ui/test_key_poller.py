"""Unit tests for src/ui/input_handlers/key_poller.py."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.ui.input_handlers.key_poller import KeyPoller, _UnixKeyPoller, _WindowsKeyPoller

# --- Windows path --------------------------------------------------------------


def test_windows_poll_returns_none_when_no_input(tui_stub) -> None:
    """Windows poll returns None when msvcrt.kbhit() is False."""
    tui_stub.msvcrt.kbhit.return_value = False  # Nothing buffered
    assert _WindowsKeyPoller(tui_stub).poll() is None  # None -> caller sleeps


def test_windows_poll_returns_printable_key(tui_stub) -> None:
    """Windows path decodes a regular byte to lowercase string."""
    tui_stub.msvcrt.kbhit.return_value = True  # Byte ready
    tui_stub.msvcrt.getch.return_value = b"A"  # Caps A
    assert _WindowsKeyPoller(tui_stub).poll() == "a"  # Lowercased


@pytest.mark.parametrize(
    ("second_byte", "expected"),
    [
        (b"H", "up"),  # Up arrow
        (b"P", "down"),  # Down arrow
        (b"K", "left"),  # Left arrow
        (b"M", "right"),  # Right arrow
        (b"I", "page_up"),  # Page Up
        (b"Q", "page_down"),  # Page Down
        (b"G", "h"),  # Home reuses 'h'
        (b"O", "e"),  # End reuses 'e'
    ],
)
def test_windows_special_key_mapping(tui_stub, second_byte: bytes, expected: str) -> None:
    """Special-key prefix \\xe0 + second byte resolves through dispatch table."""
    tui_stub.msvcrt.kbhit.return_value = True  # First byte ready
    tui_stub.msvcrt.getch.side_effect = [b"\xe0", second_byte]  # Prefix + payload
    assert _WindowsKeyPoller(tui_stub).poll() == expected


def test_windows_unknown_special_key_returns_none(tui_stub) -> None:
    """Unknown special-key second bytes return None."""
    tui_stub.msvcrt.kbhit.return_value = True  # First byte ready
    tui_stub.msvcrt.getch.side_effect = [b"\x00", b"Z"]  # Unknown payload
    assert _WindowsKeyPoller(tui_stub).poll() is None


# --- Unix path -----------------------------------------------------------------


def _wire_unix_select(tui_stub, sequence: list[bool]) -> None:
    """Make select.select return readable on the given truthy schedule."""
    queue = list(sequence)  # Mutable schedule

    def _select(*_a, **_kw):
        ready = queue.pop(0) if queue else False  # Pop next value (default False)
        return ([object()], [], []) if ready else ([], [], [])

    tui_stub.select.select = MagicMock(side_effect=_select)


def _patch_stdin(monkeypatch: pytest.MonkeyPatch, bytes_to_emit: list[str]) -> None:
    """Patch sys.stdin.read(1) so it yields characters one at a time."""
    import sys as _sys

    queue = list(bytes_to_emit)  # Mutable queue

    def _read(_n: int = 1) -> str:
        return queue.pop(0) if queue else ""  # Return next char or EOF

    monkeypatch.setattr(_sys.stdin, "read", _read)  # Patch stdin.read


def test_unix_poll_returns_none_when_no_input(tui_stub) -> None:
    """Unix poll returns None when select reports no readable fds."""
    _wire_unix_select(tui_stub, [False])  # Not readable
    assert _UnixKeyPoller(tui_stub).poll() is None


def test_unix_poll_plain_key(tui_stub, monkeypatch: pytest.MonkeyPatch) -> None:
    """A regular key byte is returned lowercased."""
    _wire_unix_select(tui_stub, [True])  # Readable for first byte
    _patch_stdin(monkeypatch, ["Q"])  # Caps Q -> "q"
    assert _UnixKeyPoller(tui_stub).poll() == "q"


@pytest.mark.parametrize(
    ("csi_bytes", "expected"),
    [
        (["[", "A"], "up"),  # ESC [ A -> up
        (["[", "B"], "down"),  # ESC [ B -> down
        (["[", "C"], "right"),  # ESC [ C -> right
        (["[", "D"], "left"),  # ESC [ D -> left
        (["[", "H"], "h"),  # ESC [ H -> Home alias
        (["[", "F"], "e"),  # ESC [ F -> End alias
    ],
)
def test_unix_csi_letter_dispatch(
    tui_stub,
    monkeypatch: pytest.MonkeyPatch,
    csi_bytes: list[str],
    expected: str,
) -> None:
    """CSI-letter sequences (ESC [ X) are mapped via the dispatch dict."""
    # First select returns ESC, then drain reads the rest of the CSI payload:
    _wire_unix_select(tui_stub, [True] + [True] * len(csi_bytes) + [False])
    _patch_stdin(monkeypatch, ["\x1b", *csi_bytes])  # ESC + payload
    assert _UnixKeyPoller(tui_stub).poll() == expected


def test_unix_csi_page_up_and_down(tui_stub, monkeypatch: pytest.MonkeyPatch) -> None:
    """CSI 5~ / 6~ map to page_up / page_down."""
    _wire_unix_select(tui_stub, [True, True, True, True, False])  # ESC [ 5 ~
    _patch_stdin(monkeypatch, ["\x1b", "[", "5", "~"])  # CSI 5~ -> page_up
    assert _UnixKeyPoller(tui_stub).poll() == "page_up"
    _wire_unix_select(tui_stub, [True, True, True, True, False])
    _patch_stdin(monkeypatch, ["\x1b", "[", "6", "~"])  # CSI 6~ -> page_down
    assert _UnixKeyPoller(tui_stub).poll() == "page_down"


def test_unix_bare_escape_returns_escape(tui_stub, monkeypatch: pytest.MonkeyPatch) -> None:
    """ESC with no follow-up bytes is treated as the 'escape' key."""
    _wire_unix_select(tui_stub, [True, False, False, False, False])  # Only initial ESC
    _patch_stdin(monkeypatch, ["\x1b"])  # Bare ESC
    assert _UnixKeyPoller(tui_stub).poll() == "escape"


def test_unix_non_csi_escape_returns_none(tui_stub, monkeypatch: pytest.MonkeyPatch) -> None:
    """ESC followed by a non-'[' byte returns None (unhandled)."""
    _wire_unix_select(tui_stub, [True, True, False, False])  # ESC then 'X'
    _patch_stdin(monkeypatch, ["\x1b", "X"])  # Not a CSI sequence
    assert _UnixKeyPoller(tui_stub).poll() is None


def test_keypoller_facade_picks_platform(tui_stub) -> None:
    """KeyPoller façade selects Windows vs Unix implementation based on flag."""
    tui_stub.IS_WINDOWS = True  # Windows path selection
    assert isinstance(KeyPoller(tui_stub)._impl, _WindowsKeyPoller)
    tui_stub.IS_WINDOWS = False  # Unix path selection
    assert isinstance(KeyPoller(tui_stub)._impl, _UnixKeyPoller)


def test_keypoller_facade_swallows_implementation_errors(tui_stub) -> None:
    """A raising platform poller is swallowed and returns None."""
    tui_stub.IS_WINDOWS = True  # Pick Windows so we can override its mock
    poller = KeyPoller(tui_stub)  # Build façade
    poller._impl = MagicMock()  # Replace with raising stub
    poller._impl.poll.side_effect = RuntimeError("kaboom")  # Force error
    assert poller.poll() is None  # Swallowed -> None
