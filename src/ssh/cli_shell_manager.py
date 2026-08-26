"""CLIShellManager -- interactive WebSocket CLI shell for switches/gateways.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 30).
Provides menu option 140. Direct imports cover stdlib + installed packages
(mistapi, websocket, pyte). Live-global reads (``apisession``,
``PromptClientUtils``, ``KeyboardListener``) are resolved via lazy
``mh = importlib.import_module("MistHelper")`` inside each helper. Callers
continue to reach the class through the ``MistHelper.CLIShellManager``
re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import functools  # WHY: partial() binds shared session state to thread target + keyboard callback.
import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import json  # WHY: encode terminal resize control message for the WebSocket.
import logging  # WHY: #886 print()->logging migration for user-visible banners and debug traces.
import shutil  # WHY: read local terminal size for PTY resize.
import sys  # WHY: direct stdout writes with cursor-move escape sequences.
import threading  # WHY: background WebSocket receive loop runs on its own thread.
import time  # WHY: brief sleep between connect and wakeup so remote prompt is ready.
from typing import Any  # WHY: WebSocket + pyte objects are duck-typed here.

import mistapi  # WHY: createSiteDeviceShellSession call to open a shell.

import websocket  # WHY: create_connection + enableTrace for the interactive shell.

try:  # pyte is optional (terminal emulation for parsing WebSocket output)
    import pyte  # In-memory terminal emulator to render device CLI screens

    _has_pyte = True  # Flag that terminal-emulation features are available
except ImportError:  # pyte not installed
    pyte = None  # type: ignore[assignment]
    _has_pyte = False

_RECEIVER_JOIN_TIMEOUT_SEC = 5.0  # WHY: bound the shutdown wait so a stuck socket cannot hang the menu.


class CLIShellManager:
    """Manage interactive CLI shell sessions for network devices.

    Provides WebSocket-based interactive shell access to switches and gateways
    through the Mist API. Handles session creation, WebSocket communication,
    and terminal emulation.
    """

    _SHELL_KEYMAP = {  # Key-name -> escape-sequence remap table for the interactive shell.
        "enter": "\n",
        "space": " ",
        "tab": "\t",
        "up": "\x00\x1b[A",
        "down": "\x00\x1b[B",
        "left": "\x00\x1b[D",
        "right": "\x00\x1b[C",
        "backspace": "\x08",
    }

    @staticmethod
    def launch(site_id: str | None = None, device_id: str | None = None, debug: bool = False) -> None:
        """Launch an interactive CLI shell session to a device.

        Args:
            site_id: Optional site ID (prompts if not provided)
            device_id: Optional device ID (prompts if not provided)
            debug: Enable debug mode for WebSocket tracing
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of PromptClientUtils facade.
        site_id, device_id = mh.PromptClientUtils.select_site_and_device_ids(site_id, device_id)
        if not site_id or not device_id:  # Need both ids.
            return  # Abort.

        shell_url = CLIShellManager._create_session(site_id, device_id)  # Create the session.
        if shell_url:  # Have a URL.
            CLIShellManager._run_interactive(shell_url, debug=debug)  # Run the shell.

    @staticmethod
    def _create_session(site_id: str, device_id: str) -> str | None:
        """Create a shell session and return the WebSocket URL.

        Args:
            site_id: The site ID containing the device
            device_id: The device ID to connect to

        Returns:
            WebSocket URL for the shell session or None on failure
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession.
        try:
            response = mistapi.api.v1.sites.devices.createSiteDeviceShellSession(mh.apisession, site_id, device_id)
            shell_data = response.data  # Read the URL data.
            return shell_data.get("url")  # type: ignore[no-any-return]
        except Exception as exception:  # Creation failed.
            # WHY: user-visible error banner (was print()).
            logging.warning("! Failed to create shell session: %s", exception)
            return None  # Return None.

    @staticmethod
    def _shell_resize_terminal(ws: Any, debug: bool) -> None:
        """Send the current local terminal dimensions to the remote PTY."""
        cols, rows = shutil.get_terminal_size()  # Read terminal size.
        resize_msg = json.dumps({"resize": {"width": cols, "height": rows}})  # Build the resize msg.
        if debug:  # Verbose troubleshooting output is enabled.
            logging.debug("[DEBUG] Sending resize: %s", resize_msg)  # WHY: trace terminal-resize control (was print()).
        ws.send(resize_msg)  # Tell the remote PTY about the new terminal dimensions.

    @staticmethod
    def _shell_render_screen(stream: Any, screen: Any, data: str) -> None:
        """Feed a text frame into the pyte emulator and redraw only the rows it marks changed."""
        stream.feed(data)  # Feed the bytes into the terminal emulator (pyte).
        for row_index in sorted(screen.dirty):  # Redraw only the rows the emulator marked changed.
            sys.stdout.write(f"\x1b[{row_index + 1};1H")  # Move the cursor to the start of that row.
            sys.stdout.write(screen.display[row_index] + "\x1b[K")  # Write the row text and clear to end of line.
        sys.stdout.flush()  # Flush so the terminal updates immediately.
        screen.dirty.clear()  # Reset the dirty set now that the screen is current.

    @staticmethod
    def _shell_decode_frame(data: Any, debug: bool) -> str | None:
        """Decode one received WebSocket frame to renderable text, or None when it is empty/non-text."""
        if isinstance(data, bytes):  # Binary frames need decoding to text.
            data = data.decode("utf-8", errors="ignore")  # Decode as UTF-8, dropping invalid bytes.
        if debug:  # Verbose troubleshooting output is enabled.
            logging.debug("[DEBUG] Raw recv: %r", data)  # WHY: trace raw received payload (was print()).
        if data and isinstance(data, str):  # We have a non-empty text frame to render.
            # WHY: cast narrows Any->str for mypy strict (no-any-return). Runtime check above ensures str.
            return str(data)  # Renderable text.
        return None  # Nothing to render for this frame.

    @staticmethod
    def _shell_receive_loop(ws: Any, stream: Any, screen: Any, debug: bool) -> None:
        """Read WebSocket frames until the connection drops, rendering each into the terminal emulator."""
        while ws.connected:  # Keep reading while the WebSocket stays open.
            try:  # A read error or close ends the receive loop.
                data = ws.recv()  # Block for the next chunk of terminal output.
                text = CLIShellManager._shell_decode_frame(data, debug)  # Decode to renderable text (or None).
                if text is not None:  # We have a non-empty text frame to render.
                    CLIShellManager._shell_render_screen(stream, screen, text)  # Render it to the screen.
            except Exception as exception:  # The socket closed or a read error occurred.
                # WHY: user-visible disconnect banner (was print()).
                logging.warning("\n## Connection lost: %s ##", exception)
                return  # Exit the receive loop.

    @staticmethod
    def _shell_handle_exit_key(ws: Any) -> None:
        """Handle the '~' exit key by closing the WebSocket socket."""
        logging.warning("\n## Exit from shell ##")  # WHY: user-visible exit banner (was print()).
        if ws.sock is not None:  # Socket present.
            ws.sock.shutdown(2)  # Stop the socket.
            ws.sock.close()  # Close the socket.

    @staticmethod
    def _shell_send_key(ws: Any, debug: bool, key: str) -> None:
        """Map and send one keystroke to the remote PTY; '~' closes the session."""
        if not ws.connected:  # Socket already closed. Nothing to send.
            return  # Drop the keystroke.
        if key == "~":  # Exit key.
            CLIShellManager._shell_handle_exit_key(ws)  # Close the socket (issue #431: no obsolete stop_listening).
            return  # Done after exit.
        mapped_key = CLIShellManager._SHELL_KEYMAP.get(key, key)  # Map the key.
        data = f"\00{mapped_key}"  # Frame the data.
        data_byte = bytes(map(ord, data))  # Immutable bytes: send_binary(payload: bytes) requires bytes.
        if debug:  # Debug mode.
            logging.debug("[DEBUG] Sending: %r", data)  # WHY: trace outgoing keystroke payload (was print()).
        try:  # The socket may drop mid-send.
            ws.send_binary(data_byte)  # Send the bytes.
        except Exception as exception:  # Send failed.
            logging.warning("\n## Send failed: %s ##", exception)  # WHY: user-visible send-error banner (was print()).
            return  # Stop after a failed send.

    @staticmethod
    def _shell_start_receiver(ws: Any, stream: Any, screen: Any, debug: bool) -> threading.Thread:
        """Start the background thread that reads WebSocket output and renders it into the terminal.

        The thread is a daemon thread. A non-daemon thread blocks the interpreter
        exit while it waits inside ``ws.recv()``. MistHelper then hangs after the
        operator leaves the shell. The caller receives the thread so that it can
        join the thread after it closes the socket.
        """
        logging.info("Starting the CLI shell receive thread")  # WHY: audit the thread start.
        receiver = threading.Thread(  # WHY: the receive loop must not block the keyboard listener.
            target=functools.partial(CLIShellManager._shell_receive_loop, ws, stream, screen, debug),
            name="cli-shell-receiver",  # WHY: a named thread makes a stack dump readable.
            daemon=True,  # WHY: a daemon thread never blocks the interpreter exit.
        )
        receiver.start()  # WHY: begin reading frames from the remote PTY.
        logging.debug("CLI shell receive thread started (alive=%s)", receiver.is_alive())  # WHY: result summary.
        return receiver  # WHY: the caller joins this thread during shutdown.

    @staticmethod
    def _shell_shutdown(ws: Any, receiver: threading.Thread) -> None:
        """Close the WebSocket and join the receive thread after the shell session ends.

        Without this cleanup each shell session leaks one open socket and one
        live thread. A long NOC shift opens many sessions and the process then
        reaches the open file limit.
        """
        logging.info("Closing the CLI shell WebSocket")  # WHY: audit before the close.
        try:  # WHY: the socket may already be closed by the exit key handler.
            ws.close()  # WHY: closing wakes the blocked recv() so the receive thread can end.
        except Exception as close_error:  # cleanup must never mask the session outcome.
            logging.debug("CLI shell WebSocket close failed: %s", close_error)  # WHY: trace only.
        receiver.join(timeout=_RECEIVER_JOIN_TIMEOUT_SEC)  # WHY: bound the wait so a stuck socket cannot hang exit.
        logging.debug("CLI shell shutdown done (receiver_alive=%s)", receiver.is_alive())  # WHY: result summary.

    @staticmethod
    def _run_interactive(shell_url: str, debug: bool = False) -> None:
        """Run an interactive WebSocket shell session against shell_url (debug enables WebSocket tracing)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of KeyboardListener facade.
        if not _has_pyte or pyte is None:  # pyte (terminal emulation) is required.
            # WHY: user-visible install hint (was print()).
            logging.warning("! Terminal emulation requires pyte. Install: pip install pyte")
            return  # Abort.
        if debug:  # Debug mode.
            websocket.enableTrace(True)  # Trace the WebSocket.
        logging.warning(" Connecting to WebSocket shell...")  # WHY: user-visible connect banner (was print()).
        ws = websocket.create_connection(shell_url)  # Open the WebSocket.
        logging.warning(" Connected.")  # WHY: user-visible connected banner (was print()).
        screen = pyte.Screen(80, 40)  # Virtual screen.
        stream = pyte.Stream(screen)  # Terminal stream.
        CLIShellManager._shell_resize_terminal(ws, debug)  # Send initial terminal dimensions to the remote PTY.
        receiver = CLIShellManager._shell_start_receiver(ws, stream, screen, debug)  # Start the receive thread.
        try:  # WHY: every exit path must close the socket and join the receive thread.
            time.sleep(1)  # Wait for connect before waking the prompt.
            ws.send_binary(bytes(map(ord, "\00\n\n")))  # Send a wakeup. Bytes (not bytearray) matches send_binary.
            if debug:  # Debug mode.
                logging.debug("[DEBUG] Sent wakeup sequence to Juniper SSRs")  # WHY: trace wakeup handshake.
            mh.KeyboardListener().listen(  # Block on keyboard input, forwarding each key to the PTY.
                on_release=functools.partial(CLIShellManager._shell_send_key, ws, debug),
                delay_second_char=0,
                delay_other_chars=0,
                lower=False,
            )
        finally:  # WHY: a KeyboardInterrupt or a send failure must still release the socket and the thread.
            CLIShellManager._shell_shutdown(ws, receiver)  # WHY: close the socket, then join the receive thread.
