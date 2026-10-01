"""Own bounded HTTP, SDK connections, and correlated packet event delivery."""

from __future__ import annotations

import json
import logging
import socket
import threading
from collections.abc import Callable, Mapping
from copy import copy
from functools import partial
from typing import Any, Protocol, cast

from mistapi.websockets.__ws_client import _MistWebsocket
from requests import PreparedRequest, Response, Session
from requests.adapters import HTTPAdapter
from requests.exceptions import Timeout
from websocket._http import connect as connect_socket
from websocket._http import proxy_info
from websocket._socket import sock_opt

from src.security.credential_redaction import CredentialRedactor
from src.websocket_streams.intake.fields import StreamRequestError
from src.websocket_streams.live.captures.model import CaptureContext
from src.websocket_streams.live.runners.text import PacketSummary
from src.websocket_streams.live.sessions.buffer import MessageBuffer
from src.websocket_streams.live.sessions.record import SessionState
from websocket import WebSocketApp

logger = logging.getLogger(__name__)


class CaptureHttpSession(Session):
    """Preserve request context while bounding SDK HTTP actions and rate waits."""

    class SDKState(Protocol):
        """Type the SDK fields that the private transport owns or updates."""

        _session: Session
        _count: int
        _handle_rate_limit: Callable[[Response, int], None]

    def __init__(self, source: Session, clock: Callable[[], float]) -> None:
        """Copy request settings without sharing connection pools."""
        super().__init__()
        self.clock = clock
        self.deadline = clock() + 30.0
        self.stopping: threading.Event | None = None
        for name in (
            "headers",
            "cookies",
            "proxies",
            "params",
            "hooks",
            "auth",
            "verify",
            "cert",
            "trust_env",
            "max_redirects",
        ):
            setattr(self, name, copy(getattr(source, name)))
        if any(
            type(adapter) is not HTTPAdapter or adapter.max_retries.total not in (0, False)
            for adapter in source.adapters.values()
        ):
            self.close()
            raise StreamRequestError("not_ready", "The Mist HTTP transport cannot run a bounded packet capture.")

    @classmethod
    def for_api(cls, source: object, clock: Callable[[], float]) -> tuple[object, CaptureHttpSession]:
        """Keep the SDK session type, regional host, privileges, and token context."""
        original = getattr(source, "_session", None)
        if not isinstance(original, Session):
            raise StreamRequestError("not_ready", "The Mist session cannot run a bounded packet capture.")
        logger.info("Preparing private packet capture HTTP transport")
        http = cls(original, clock)
        session = cast(CaptureHttpSession.SDKState, copy(source))
        session._session = http
        session._handle_rate_limit = http.wait_rate_limit
        session._count = 0
        logger.debug("Prepared private packet capture HTTP transport")
        return session, http

    def prepare(self, stopping: threading.Event | None) -> None:
        """Give one SDK action a fixed phase budget."""
        self.deadline = self.clock() + 30.0
        self.stopping = stopping

    def send(self, request: PreparedRequest, **kwargs: Any) -> Response:
        """Bound the standard requests keyword boundary without changing its filters."""
        remaining = self.deadline - self.clock()
        if remaining <= 0 or (self.stopping is not None and self.stopping.is_set()):
            raise Timeout("The packet capture HTTP phase ended before transmission.")
        kwargs["timeout"] = (min(5.0, remaining), min(10.0, remaining))
        return super().send(request, **kwargs)

    def wait_rate_limit(self, response: Response, attempt: int) -> None:
        """Respect a rate wait only within the remaining phase budget."""
        raw = response.headers.get("Retry-After", "")
        if raw and (len(raw) > 10 or not raw.isascii() or not raw.isdecimal()):
            raise Timeout("The packet capture rate wait is not bounded.")
        seconds = int(raw) if raw else 5 * 2**attempt
        if seconds >= self.deadline - self.clock():
            raise Timeout("The packet capture rate wait exceeds the HTTP phase.")
        logger.info("Waiting after packet capture rate limit seconds=%s", seconds)
        event = self.stopping if self.stopping is not None else threading.Event()
        if event.wait(seconds):
            raise Timeout("The packet capture stopped during the rate wait.")
        logger.debug("Completed packet capture rate wait")


class CaptureRecords:
    """Bound immediate events and deliver only the accepted capture's records."""

    def __init__(self, context: CaptureContext) -> None:
        """Keep the pending buffer separate from the existing card buffer."""
        self.context = context
        self.pending = MessageBuffer(100, 256 * 1024)

    @staticmethod
    def decode(message: Mapping[object, object]) -> dict[str, object]:
        """Decode the nested SDK data without accepting an oversized JSON string."""
        data = message.get("data")
        if isinstance(data, str):
            if len(data) > MessageBuffer.MAX_MESSAGE_BYTES:
                raise StreamRequestError("bad_request", "The packet event exceeds the message limit.")
            try:
                data = json.loads(data)
            except json.JSONDecodeError as error:
                raise StreamRequestError("bad_request", "The packet event has invalid JSON.") from error
        if not isinstance(data, Mapping) or not isinstance(data.get("capture_id"), str) or "pcap_dict" not in data:
            raise StreamRequestError("bad_request", "The packet event has no capture identity or packet record.")
        return {"capture_id": data["capture_id"], "pcap_dict": data["pcap_dict"]}

    def add(self, message: Mapping[object, object]) -> None:
        """Queue early records until the start response establishes identity."""
        record = self.decode(message)
        with self.context.events.lock:
            if self.context.progress.ending:
                return
            if self.context.progress.capture_id is None:
                self.pending.add("", "packet", record, None, None)
            else:
                self._deliver(record)

    def flush(self) -> None:
        """Deliver matching pending records in their original order."""
        for message in self.pending.snapshot():
            self._deliver(json.loads(message.content_json))
        if self.pending.dropped:
            self.context.sink.add_message("event", f"The pending buffer removed {self.pending.dropped} early records.")
        self.pending = MessageBuffer(100, 256 * 1024)

    def _deliver(self, record: Mapping[str, object]) -> None:
        """Keep another capture and raw packet bytes out of the selected card."""
        identifier = record.get("capture_id")
        if not isinstance(identifier, str) or identifier.lower() != self.context.progress.capture_id:
            return
        packet = record.get("pcap_dict")
        progress = self.context.progress
        if packet is None:
            state = SessionState.FINISHED if progress.packets else SessionState.TIMED_OUT
            progress.outcome = progress.outcome or (state, "Mist ended the packet capture.")
            self.context.events.wake.set()
        elif isinstance(packet, dict):
            safe = CredentialRedactor.redact(packet)
            summary = PacketSummary.summarize(safe)[:512]
            self.context.sink.add_message("packet", safe, summary=summary)
            progress.packets += 1
        else:
            raise StreamRequestError("bad_request", "The packet record is not an object.")


class CaptureFeed:
    """Translate SDK callbacks into private capture signals."""

    class SDKMetadata(logging.Filter):
        """Keep owned SDK logs separate from packet, credential, and error content."""

        lock = threading.Lock()

        def filter(self, record: logging.LogRecord) -> bool:
            """Retain SDK action metadata without remote text or traceback values."""
            if isinstance(record.threadName, str) and record.threadName.startswith("ws-pcap-"):
                record.msg = "Packet SDK action=%s level=%s"
                record.args = (record.funcName, record.levelname)
                record.exc_info = None
                record.exc_text = None
            return True

    def __init__(self, context: CaptureContext, records: CaptureRecords) -> None:
        """Share only this capture's state and record buffer."""
        self.context = context
        self.records = records

    def opened(self) -> None:
        """Require a fresh confirmation after every SDK connection."""
        with self.context.events.lock:
            self.context.events.subscribed.clear()
            if self.context.progress.capture_id is not None and not self.context.progress.ending:
                self.context.sink.add_message(
                    "event", "The capture connection reopened. Some packet records can be missing."
                )

    def message(self, message: object) -> None:
        """Accept confirmation and packet events only from the exact owned channel."""
        if not isinstance(message, Mapping) or message.get("channel") != self.context.plan.channel:
            return
        try:
            with self.context.events.lock:
                if self.context.progress.ending:
                    return
                event = message.get("event")
                if event == "channel_subscribed":
                    self.context.events.subscribed.set()
                    self.context.events.wake.set()
                elif event == "subscribe_failed":
                    raise StreamRequestError("not_ready", "Mist refused the packet capture subscription.")
                elif event == "data":
                    self.records.add(message)
        except StreamRequestError as error:
            with self.context.events.lock:
                self.context.progress.outcome = self.context.progress.outcome or (SessionState.FAILED, error.message)
                self.context.events.wake.set()
            logger.error("Packet capture event failed code=%s", error.code)

    def error(self, error: Exception) -> None:
        """Report metadata only and let the SDK perform its bounded reconnect."""
        status = getattr(error, "status_code", None)
        logger.warning(
            "Caution: packet capture connection failed error_type=%s. Packet records can be missing.",
            type(error).__name__,
        )
        if type(status) is int and status in (400, 401, 403, 429):
            with self.context.events.lock:
                reason = f"Mist refused the packet connection with HTTP {status}."
                self.context.progress.outcome = self.context.progress.outcome or (SessionState.FAILED, reason)
                self.context.events.wake.set()

    def closed(self, code: int | None, message: str | None) -> None:
        """Keep an unexpected final disconnect separate from a confirmed cloud stop."""
        with self.context.events.lock:
            self.context.events.closed.set()
            if not self.context.progress.ending:
                outcome = (SessionState.FAILED, "The packet connection closed before the capture ended.")
                self.context.progress.outcome = self.context.progress.outcome or outcome
                self.context.events.wake.set()


class CaptureConnection:
    """Own one SDK client and its callback and connection cleanup."""

    def __init__(self, apisession: object, context: CaptureContext, feed: CaptureFeed) -> None:
        """Delay SDK connection construction until the worker passes target checks."""
        self.apisession = apisession
        self.context = context
        self.feed = feed
        self.client: _MistWebsocket | None = None
        self.sockets: set[socket.socket] = set()
        with CaptureFeed.SDKMetadata.lock:
            for name in ("mistapi", "websocket"):
                sdk_logger = logging.getLogger(name)
                if not any(isinstance(existing, CaptureFeed.SDKMetadata) for existing in sdk_logger.filters):
                    sdk_logger.addFilter(CaptureFeed.SDKMetadata())

    def open(self) -> None:
        """Install callbacks before the SDK requests the private subscription."""
        logger.info("Opening packet capture connection key=%s", self.context.plan.request.key)
        client = self.context.dependencies.client_type(
            self.apisession,
            channels=[self.context.plan.channel],
            auto_reconnect=True,
            max_reconnect_attempts=3,
            max_reconnect_backoff=5.0,
            ping_interval=30,
            queue_maxsize=64,
            subscription_watchdog_timeout=10.0,
        )
        self.client = client
        client._create_ws_app = partial(self._application, client, client._create_ws_app)
        client.on_open(self.feed.opened)
        client.on_message(self.feed.message)
        client.on_error(self.feed.error)
        client.on_close(self.feed.closed)
        client.connect(run_in_background=True)
        for thread in (client._thread, client._callback_thread):
            if thread is not None:
                thread.name = f"ws-pcap-sdk-{self.context.plan.request.key}"
        logger.debug("Opened packet capture connection key=%s", self.context.plan.request.key)

    def close(self) -> None:
        """Close only the owned SDK connection and bound both thread joins."""
        if self.client is not None:
            logger.info("Closing owned packet capture connection")
            try:
                self.client.disconnect(wait=False)
            finally:
                self._release_sockets()
            threads = (self.client._thread, self.client._callback_thread)
            for thread in threads:
                if thread is not None and thread is not threading.current_thread():
                    thread.join(timeout=5.0)
            if self.client.ready() or any(thread is not None and thread.is_alive() for thread in threads):
                raise StreamRequestError("not_ready", "The packet connection did not close before the time limit.")
            self.context.events.closed.set()
            logger.debug("Closed owned packet capture connection")

    def _release_sockets(self) -> None:
        """Interrupt native reads after the SDK disables reconnect and callbacks."""
        with self.context.events.lock:
            sockets = tuple(self.sockets)
            self.sockets.clear()
        for owned_socket in sockets:
            try:
                owned_socket.shutdown(socket.SHUT_RDWR)
            except OSError as error:
                logger.debug("Owned packet socket shutdown returned error_type=%s", type(error).__name__)
            owned_socket.close()

    def _application(self, client: _MistWebsocket, factory: Callable[[], WebSocketApp]) -> WebSocketApp:
        """Give the SDK an owned socket with bounded connect, TLS, and handshake waits."""
        if self.context.events.stopping.is_set() or self.context.progress.ending:
            raise StreamRequestError("not_open", "The capture stopped before connection.")
        application = factory()
        options = sock_opt(None, client._build_sslopt())
        options.timeout = 5.0
        proxy_factory: Callable[[], proxy_info] = proxy_info
        owned_socket, _address = connect_socket(application.url, options, proxy_factory(), None)
        with self.context.events.lock:
            if self.context.events.stopping.is_set() or self.context.progress.ending:
                owned_socket.close()
                raise StreamRequestError("not_open", "The capture stopped before connection.")
            self.sockets.intersection_update(existing for existing in tuple(self.sockets) if existing.fileno() >= 0)
            self.sockets.add(owned_socket)
        application.prepared_socket = owned_socket
        return application
