"""Read raw terminal output and coordinate terminal outcomes."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Reader actions use structured JSON records.
import threading  # A local stop can interrupt the reader.

from src.websocket_streams.intake.fields.error import (
    StreamRequestError,  # Known open and queued-write failures are plain.
)
from src.websocket_streams.live.runners.shell.lifecycle.contracts import TerminalConfiguration
from src.websocket_streams.live.runners.shell.lifecycle.opening import TerminalOpenError, TerminalOpening
from src.websocket_streams.live.runners.shell.lifecycle.outcomes import TerminalOutcomes
from src.websocket_streams.live.sessions.record.state import SessionSink  # The reader stores exact terminal bytes.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import StructuredTransportLogger
from src.websocket_streams.live.transport.runtime.reader.contracts import ConnectionClosed  # Reads end through this.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply the shared bounded logging boundary.


class TerminalReading:
    """Open one terminal and read until it reaches a final outcome."""

    def __init__(
        self,
        opening: TerminalOpening,
        sink: SessionSink,
        outcomes: TerminalOutcomes,
        configuration: TerminalConfiguration,
        stopping: threading.Event,
    ) -> None:
        """Store terminal reader collaborators."""
        self._opening = opening  # The opening owner supplies the client and trigger action.
        self._sink = sink  # The session keeps exact output bytes and state changes.
        self._outcomes = outcomes  # One mapper owns all final state decisions.
        self._configuration = configuration  # The terminal mode supplies its behavior.
        self._stopping = stopping  # A stop can arrive before or during the open.

    def run(self) -> None:
        """Open, read, map the outcome, and close."""
        try:  # Convert every terminal end into one stable session outcome.
            self._open_and_read()  # Trigger Mist, open the client, and preserve all output.
        except ConnectionClosed as closed:
            status = "output" if self._outcomes.output_seen else "silent"  # Report issue #3710 state safely.
            fields = {"code": closed.code, "dropped": closed.dropped, "status": status}  # Use safe bounded fields.
            logger.emit(logging.INFO, "terminal_connection_closed", fields)  # Log the close before state mapping.
            self._outcomes.finish(closed)  # Publish the correct close outcome.
        except (TerminalOpenError, StreamRequestError) as error:
            reason = str(getattr(error, "message", "") or error)  # Preserve the plain operator-facing reason.
            self._outcomes.fail(reason)  # Publish the known failure.
        except Exception as error:
            logger.emit(logging.ERROR, "terminal_unexpected_failure", {"detail": type(error).__name__})
            self._outcomes.fail("The terminal failed. Read the portal log for the cause.")  # Keep public text plain.
        finally:
            self._opening.close()  # Close the socket on every exit path.

    def _open_and_read(self) -> None:
        """Run the successful open path before the read loop."""
        trigger = self._configuration.trigger()  # Build the mode-specific REST request.
        url = self._opening.trigger.url(trigger)  # Send the REST trigger and read its address.
        self._opening.connector.open(url, self._stopping)  # Apply address safety, connect, and send the size.
        self._opening.mark_live(self._configuration.opened_note)  # Publish the mode-specific open event.
        self._read_loop()  # Read until the client raises the shared close contract.

    def _read_loop(self) -> None:
        """Keep exact output bytes until the connection ends."""
        while True:  # The client raises ConnectionClosed for every terminal end.
            data = self._opening.client.read()  # Read bytes or one quiet interval.
            if data:  # A quiet interval adds no history entry.
                logger.emit(logging.DEBUG, "terminal_output_started", {"byte_count": len(data)})
                self._sink.add_bytes(data)  # Preserve control codes and split UTF-8 bytes.
                logger.emit(logging.DEBUG, "terminal_output_completed", {"byte_count": len(data)})
                self._first_output()  # Release deferred input after the first output.
            self._configuration.behavior.check_limit()  # A screen command can end at its total limit.

    def _first_output(self) -> None:
        """Run the mode first-output action one time."""
        if self._outcomes.output_seen:  # Later output must not release the input queue again.
            return
        self._outcomes.note_output()  # Record the answer before queued writes can fail.
        try:  # A close during deferred writes is reported by the next read.
            self._configuration.behavior.first_output()  # A shell releases queued input here.
        except StreamRequestError:
            logger.emit(logging.DEBUG, "terminal_deferred_input_failed", {"status": "closed"})
