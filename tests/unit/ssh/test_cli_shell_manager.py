"""Unit tests for ``src.ssh.cli_shell_manager.CLIShellManager``.

Why: Un-omitting this WebSocket CLI shell manager from ``[tool.coverage.run].omit``
requires 100% line + branch coverage across the 10 static methods, the
``_SHELL_KEYMAP`` class attribute, and the module-level ``_has_pyte`` fallback
branch. The manager reaches live-global state (``apisession``, ``mistapi``,
``PromptClientUtils``, ``KeyboardListener``) through lazy
``importlib.import_module("MistHelper")`` reads, so tests inject a fake
``MistHelper`` module via ``sys.modules`` and patch module-scope collaborators
(``websocket``, ``mistapi``, ``pyte``, ``threading``, ``time``,
``shutil.get_terminal_size``) to exercise each branch deterministically.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from src.ssh import cli_shell_manager as csm_module
from src.ssh.cli_shell_manager import CLIShellManager


@pytest.fixture
def fake_mh(monkeypatch):
    """Install a fake MistHelper module for lazy importlib resolution.

    Why: ``launch``, ``_create_session``, and ``_run_interactive`` each call
    ``importlib.import_module("MistHelper")`` and reach ``mh.apisession``,
    ``mh.PromptClientUtils``, ``mh.KeyboardListener``. Injecting a stub lets
    tests control the return values of those live globals without touching
    the real module graph.
    """
    mh = ModuleType("MistHelper")
    mh.apisession = MagicMock(name="apisession")
    mh.PromptClientUtils = MagicMock(name="PromptClientUtils")
    mh.KeyboardListener = MagicMock(name="KeyboardListener")
    monkeypatch.setitem(sys.modules, "MistHelper", mh)
    return mh


class TestModuleLevelPyteImport:
    """Cover the module-level ``try/except ImportError`` around pyte."""

    def test_has_pyte_flag_reflects_import_state(self):
        """The ``_has_pyte`` flag mirrors whether the ``pyte`` import succeeded."""
        # Under the normal test environment pyte is installed and _has_pyte is True.
        assert csm_module._has_pyte is True
        assert csm_module.pyte is not None

    def test_import_falls_back_when_pyte_missing(self, monkeypatch):
        """Load the module into an isolated namespace with ``pyte`` blocked to exercise the ImportError branch."""
        import builtins
        import importlib.util

        real_import = builtins.__import__

        def blocked_import(name, *args, **kwargs):
            if name == "pyte":
                raise ImportError("blocked for test")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", blocked_import)
        monkeypatch.delitem(sys.modules, "pyte", raising=False)

        # Load a fresh copy of the module under a distinct name so csm_module (already
        # imported into other tests' patch bindings) is not disturbed.
        spec = importlib.util.spec_from_file_location("_csm_no_pyte_probe", csm_module.__file__)
        assert spec is not None and spec.loader is not None
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)

        assert probe._has_pyte is False
        assert probe.pyte is None


class TestShellKeymap:
    """Cover ``CLIShellManager._SHELL_KEYMAP`` (class attribute)."""

    def test_keymap_contains_expected_entries(self):
        """The keymap enumerates the eight remapped key names."""
        assert CLIShellManager._SHELL_KEYMAP == {
            "enter": "\n",
            "space": " ",
            "tab": "\t",
            "up": "\x00\x1b[A",
            "down": "\x00\x1b[B",
            "left": "\x00\x1b[D",
            "right": "\x00\x1b[C",
            "backspace": "\x08",
        }


class TestLaunch:
    """Cover ``CLIShellManager.launch``."""

    def test_returns_early_when_site_id_missing(self, fake_mh):
        """Falsy site_id skips shell creation entirely."""
        fake_mh.PromptClientUtils.select_site_and_device_ids.return_value = (None, "d-1")

        with (
            patch.object(CLIShellManager, "_create_session") as m_create,
            patch.object(CLIShellManager, "_run_interactive") as m_run,
        ):
            CLIShellManager.launch()

        m_create.assert_not_called()
        m_run.assert_not_called()

    def test_returns_early_when_device_id_missing(self, fake_mh):
        """Falsy device_id skips shell creation entirely."""
        fake_mh.PromptClientUtils.select_site_and_device_ids.return_value = ("s-1", None)

        with (
            patch.object(CLIShellManager, "_create_session") as m_create,
            patch.object(CLIShellManager, "_run_interactive") as m_run,
        ):
            CLIShellManager.launch()

        m_create.assert_not_called()
        m_run.assert_not_called()

    def test_skips_run_when_url_falsy(self, fake_mh):
        """When _create_session returns None the interactive shell is not entered."""
        fake_mh.PromptClientUtils.select_site_and_device_ids.return_value = ("s-1", "d-1")

        with (
            patch.object(CLIShellManager, "_create_session", return_value=None) as m_create,
            patch.object(CLIShellManager, "_run_interactive") as m_run,
        ):
            CLIShellManager.launch(site_id="s-1", device_id="d-1", debug=True)

        m_create.assert_called_once_with("s-1", "d-1")
        m_run.assert_not_called()

    def test_full_path_invokes_interactive(self, fake_mh):
        """Happy path: valid ids and URL trigger the interactive shell."""
        fake_mh.PromptClientUtils.select_site_and_device_ids.return_value = ("s-1", "d-1")

        with (
            patch.object(CLIShellManager, "_create_session", return_value="wss://x") as m_create,
            patch.object(CLIShellManager, "_run_interactive") as m_run,
        ):
            CLIShellManager.launch(debug=True)

        m_create.assert_called_once_with("s-1", "d-1")
        m_run.assert_called_once_with("wss://x", debug=True)


class TestCreateSession:
    """Cover ``CLIShellManager._create_session``."""

    def test_returns_url_on_success(self, fake_mh):
        """Returns the ``url`` field extracted from the mistapi response."""
        fake_response = MagicMock()
        fake_response.data = {"url": "wss://shell/1"}

        with patch("src.ssh.cli_shell_manager.mistapi") as m_mistapi:
            m_mistapi.api.v1.sites.devices.createSiteDeviceShellSession.return_value = fake_response
            result = CLIShellManager._create_session("s-1", "d-1")

        assert result == "wss://shell/1"
        m_mistapi.api.v1.sites.devices.createSiteDeviceShellSession.assert_called_once_with(
            fake_mh.apisession, "s-1", "d-1"
        )

    def test_returns_none_and_prints_on_exception(self, fake_mh, capsys):
        """Any exception is swallowed, printed, and yields None."""
        with patch("src.ssh.cli_shell_manager.mistapi") as m_mistapi:
            m_mistapi.api.v1.sites.devices.createSiteDeviceShellSession.side_effect = RuntimeError("boom")
            result = CLIShellManager._create_session("s-1", "d-1")

        assert result is None
        captured = capsys.readouterr()
        assert "Failed to create shell session" in captured.out
        assert "boom" in captured.out


class TestShellResizeTerminal:
    """Cover ``CLIShellManager._shell_resize_terminal``."""

    def test_sends_resize_without_debug(self, capsys):
        """Sends a JSON resize control frame; no debug output when debug is off."""
        ws = MagicMock()
        with patch("src.ssh.cli_shell_manager.shutil.get_terminal_size", return_value=(100, 30)):
            CLIShellManager._shell_resize_terminal(ws, debug=False)

        ws.send.assert_called_once_with('{"resize": {"width": 100, "height": 30}}')
        assert capsys.readouterr().out == ""

    def test_sends_resize_with_debug_trace(self, capsys):
        """Debug prints the exact resize payload before sending."""
        ws = MagicMock()
        with patch("src.ssh.cli_shell_manager.shutil.get_terminal_size", return_value=(80, 24)):
            CLIShellManager._shell_resize_terminal(ws, debug=True)

        ws.send.assert_called_once_with('{"resize": {"width": 80, "height": 24}}')
        assert "[DEBUG] Sending resize" in capsys.readouterr().out


class TestShellRenderScreen:
    """Cover ``CLIShellManager._shell_render_screen``."""

    def test_feeds_stream_and_redraws_dirty_rows(self):
        """Dirty rows are moved-to, written, cleared to EOL; the dirty set is cleared."""
        stream = MagicMock()
        screen = MagicMock()
        screen.dirty = {1, 0}
        screen.display = ["row-zero", "row-one", "row-two"]

        with patch("src.ssh.cli_shell_manager.sys.stdout") as m_stdout:
            CLIShellManager._shell_render_screen(stream, screen, "chunk")

        stream.feed.assert_called_once_with("chunk")
        # Rows are sorted -> 0 then 1: two cursor-move writes and two row writes.
        writes = [c.args[0] for c in m_stdout.write.call_args_list]
        assert writes == [
            "\x1b[1;1H",
            "row-zero\x1b[K",
            "\x1b[2;1H",
            "row-one\x1b[K",
        ]
        m_stdout.flush.assert_called_once()
        assert screen.dirty == set()  # cleared after render

    def test_empty_dirty_set_still_flushes(self):
        """Zero dirty rows: no writes but still flush + clear (idempotent path)."""
        stream = MagicMock()
        screen = MagicMock()
        screen.dirty = set()
        screen.display = []

        with patch("src.ssh.cli_shell_manager.sys.stdout") as m_stdout:
            CLIShellManager._shell_render_screen(stream, screen, "")

        stream.feed.assert_called_once_with("")
        m_stdout.write.assert_not_called()
        m_stdout.flush.assert_called_once()


class TestShellDecodeFrame:
    """Cover ``CLIShellManager._shell_decode_frame``."""

    def test_decodes_bytes_frame(self):
        """Bytes input is decoded to UTF-8 text and returned."""
        result = CLIShellManager._shell_decode_frame(b"hello", debug=False)
        assert result == "hello"

    def test_returns_str_frame_unchanged(self):
        """Str input passes through unchanged."""
        result = CLIShellManager._shell_decode_frame("hello", debug=False)
        assert result == "hello"

    def test_returns_none_for_empty_str(self):
        """Empty string frames return None (nothing to render)."""
        assert CLIShellManager._shell_decode_frame("", debug=False) is None

    def test_returns_none_for_non_str_non_bytes(self):
        """Non-str, non-bytes input yields None."""
        assert CLIShellManager._shell_decode_frame(None, debug=False) is None
        assert CLIShellManager._shell_decode_frame(123, debug=False) is None

    def test_debug_prints_raw_payload(self, capsys):
        """Debug mode prints the repr'd payload."""
        CLIShellManager._shell_decode_frame(b"abc", debug=True)
        out = capsys.readouterr().out
        assert "[DEBUG] Raw recv" in out


class TestShellReceiveLoop:
    """Cover ``CLIShellManager._shell_receive_loop``."""

    def test_renders_text_frames_until_disconnected(self):
        """Reads and renders while connected, then exits when ws.connected flips False."""
        ws = MagicMock()
        # connected: True for the first recv, then False so the while loop ends.
        type(ws).connected = property(lambda self: self._c.pop(0))
        ws._c = [True, False]
        ws.recv.return_value = "payload"

        stream = MagicMock()
        screen = MagicMock()

        with patch.object(CLIShellManager, "_shell_render_screen") as m_render:
            CLIShellManager._shell_receive_loop(ws, stream, screen, debug=False)

        ws.recv.assert_called_once()
        m_render.assert_called_once_with(stream, screen, "payload")

    def test_skips_render_when_decode_returns_none(self):
        """Empty/decoded-to-None frames are not passed to the renderer."""
        ws = MagicMock()
        type(ws).connected = property(lambda self: self._c.pop(0))
        ws._c = [True, False]
        ws.recv.return_value = ""  # empty string -> decode returns None

        with patch.object(CLIShellManager, "_shell_render_screen") as m_render:
            CLIShellManager._shell_receive_loop(ws, MagicMock(), MagicMock(), debug=False)

        m_render.assert_not_called()

    def test_prints_and_returns_on_exception(self, capsys):
        """Exception path prints 'Connection lost' and exits the loop."""
        ws = MagicMock()
        ws.connected = True
        ws.recv.side_effect = OSError("socket dead")

        CLIShellManager._shell_receive_loop(ws, MagicMock(), MagicMock(), debug=False)

        assert "Connection lost" in capsys.readouterr().out


class TestShellHandleExitKey:
    """Cover ``CLIShellManager._shell_handle_exit_key``."""

    def test_shuts_down_and_closes_when_sock_present(self, capsys):
        """Present socket: shutdown(2) then close()."""
        ws = MagicMock()
        ws.sock = MagicMock()

        CLIShellManager._shell_handle_exit_key(ws)

        ws.sock.shutdown.assert_called_once_with(2)
        ws.sock.close.assert_called_once()
        assert "Exit from shell" in capsys.readouterr().out

    def test_noop_when_sock_missing(self, capsys):
        """None socket: no shutdown/close; still prints the exit banner."""
        ws = MagicMock()
        ws.sock = None

        CLIShellManager._shell_handle_exit_key(ws)

        assert "Exit from shell" in capsys.readouterr().out


class TestShellSendKey:
    """Cover ``CLIShellManager._shell_send_key``."""

    def test_drops_when_not_connected(self):
        """Not-connected socket: keystroke silently discarded."""
        ws = MagicMock()
        ws.connected = False

        CLIShellManager._shell_send_key(ws, debug=False, key="a")

        ws.send_binary.assert_not_called()

    def test_exit_key_invokes_exit_handler(self):
        """Tilde key delegates to _shell_handle_exit_key and does not send bytes."""
        ws = MagicMock()
        ws.connected = True

        with patch.object(CLIShellManager, "_shell_handle_exit_key") as m_exit:
            CLIShellManager._shell_send_key(ws, debug=False, key="~")

        m_exit.assert_called_once_with(ws)
        ws.send_binary.assert_not_called()

    def test_mapped_key_is_translated(self):
        """Known key names are mapped to their escape sequences."""
        ws = MagicMock()
        ws.connected = True

        CLIShellManager._shell_send_key(ws, debug=False, key="enter")

        expected = bytes(map(ord, "\x00\n"))
        ws.send_binary.assert_called_once_with(expected)

    def test_unmapped_key_passes_through(self, capsys):
        """Unknown key names are sent verbatim (with framing prefix). Debug prints the payload."""
        ws = MagicMock()
        ws.connected = True

        CLIShellManager._shell_send_key(ws, debug=True, key="a")

        expected = bytes(map(ord, "\x00a"))
        ws.send_binary.assert_called_once_with(expected)
        assert "[DEBUG] Sending" in capsys.readouterr().out

    def test_prints_and_returns_when_send_raises(self, capsys):
        """Send-side exception is caught, printed, and does not propagate."""
        ws = MagicMock()
        ws.connected = True
        ws.send_binary.side_effect = OSError("bad pipe")

        CLIShellManager._shell_send_key(ws, debug=False, key="a")

        assert "Send failed" in capsys.readouterr().out


class TestShellStartReceiver:
    """Cover ``CLIShellManager._shell_start_receiver``."""

    def test_starts_background_thread(self):
        """A threading.Thread is created with a partial'd receive loop and started."""
        ws = MagicMock()
        stream = MagicMock()
        screen = MagicMock()

        with patch("src.ssh.cli_shell_manager.threading.Thread") as m_thread:
            m_instance = MagicMock()
            m_thread.return_value = m_instance
            CLIShellManager._shell_start_receiver(ws, stream, screen, debug=True)

        m_thread.assert_called_once()
        m_instance.start.assert_called_once()


class TestRunInteractive:
    """Cover ``CLIShellManager._run_interactive``."""

    def test_prints_and_returns_when_pyte_missing(self, fake_mh, monkeypatch, capsys):
        """No pyte -> print install hint and return without opening a WebSocket."""
        monkeypatch.setattr(csm_module, "_has_pyte", False)
        monkeypatch.setattr(csm_module, "pyte", None)

        with patch("src.ssh.cli_shell_manager.websocket") as m_ws:
            CLIShellManager._run_interactive("wss://x", debug=False)

        m_ws.create_connection.assert_not_called()
        assert "requires pyte" in capsys.readouterr().out

    def test_prints_and_returns_when_pyte_module_none(self, fake_mh, monkeypatch, capsys):
        """Even if _has_pyte were True, a None pyte module still triggers the early return."""
        monkeypatch.setattr(csm_module, "_has_pyte", True)
        monkeypatch.setattr(csm_module, "pyte", None)

        with patch("src.ssh.cli_shell_manager.websocket") as m_ws:
            CLIShellManager._run_interactive("wss://x", debug=False)

        m_ws.create_connection.assert_not_called()
        assert "requires pyte" in capsys.readouterr().out

    def test_happy_path_no_debug(self, fake_mh, monkeypatch):
        """Full interactive path: connect, resize, receiver, sleep, wakeup, listen."""
        # Ensure both gates pass.
        monkeypatch.setattr(csm_module, "_has_pyte", True)
        fake_pyte = MagicMock()
        monkeypatch.setattr(csm_module, "pyte", fake_pyte)

        m_ws_conn = MagicMock()
        with (
            patch("src.ssh.cli_shell_manager.websocket") as m_ws_mod,
            patch("src.ssh.cli_shell_manager.time.sleep") as m_sleep,
            patch.object(CLIShellManager, "_shell_resize_terminal") as m_resize,
            patch.object(CLIShellManager, "_shell_start_receiver") as m_start,
        ):
            m_ws_mod.create_connection.return_value = m_ws_conn
            CLIShellManager._run_interactive("wss://x", debug=False)

        m_ws_mod.enableTrace.assert_not_called()
        m_ws_mod.create_connection.assert_called_once_with("wss://x")
        fake_pyte.Screen.assert_called_once_with(80, 40)
        fake_pyte.Stream.assert_called_once()
        m_resize.assert_called_once()
        m_start.assert_called_once()
        m_sleep.assert_called_once_with(1)
        # Wakeup send:
        m_ws_conn.send_binary.assert_called_once_with(bytes(map(ord, "\x00\n\n")))
        # Keyboard listener started:
        fake_mh.KeyboardListener.assert_called_once_with()
        fake_mh.KeyboardListener.return_value.listen.assert_called_once()

    def test_happy_path_with_debug_enables_trace(self, fake_mh, monkeypatch, capsys):
        """Debug mode enables WebSocket tracing and prints the wakeup breadcrumb."""
        monkeypatch.setattr(csm_module, "_has_pyte", True)
        fake_pyte = MagicMock()
        monkeypatch.setattr(csm_module, "pyte", fake_pyte)

        with (
            patch("src.ssh.cli_shell_manager.websocket") as m_ws_mod,
            patch("src.ssh.cli_shell_manager.time.sleep"),
            patch.object(CLIShellManager, "_shell_resize_terminal"),
            patch.object(CLIShellManager, "_shell_start_receiver"),
        ):
            m_ws_mod.create_connection.return_value = MagicMock()
            CLIShellManager._run_interactive("wss://x", debug=True)

        m_ws_mod.enableTrace.assert_called_once_with(True)
        assert "wakeup" in capsys.readouterr().out.lower()
