"""Controlled clocks and SDK transports with no Mist network access."""

from __future__ import annotations

import json
import secrets
import threading
from collections.abc import Callable
from copy import deepcopy
from types import SimpleNamespace

from mistapi.__api_request import APIRequest
from mistapi.__api_response import APIResponse
from mistapi.websockets.__ws_client import _MistWebsocket
from requests import Response


class Identities:
    """Keep synthetic identifiers in one fixture namespace."""

    ORG = "11111111-1111-4111-8111-111111111111"
    SITE = "22222222-2222-4222-8222-222222222222"
    DEVICE = "00000000-0000-0000-1000-aabbccddeeff"
    CAPTURE = "33333333-3333-4333-8333-333333333333"
    OTHER = "44444444-4444-4444-8444-444444444444"


class ControlledClock:
    """Advance capture time without changing the process clock."""

    def __init__(self) -> None:
        """Create a clock and a bounded real wait."""
        self.value = 0.0
        self.wakes: set[threading.Event] = set()
        self.waits: list[float] = []
        self.lock = threading.RLock()

    def __call__(self) -> float:
        """Return the controlled monotonic value."""
        with self.lock:
            return self.value

    def advance(self, value: float) -> None:
        """Move to one exact time and wake the capture worker."""
        with self.lock:
            self.value = value
            wakes = tuple(self.wakes)
        for event in wakes:
            event.set()

    def wait(self, event: threading.Event, seconds: float) -> bool:
        """Keep real waits short while the test controls capture time."""
        with self.lock:
            self.wakes.add(event)
            self.waits.append(seconds)
        return event.wait(min(max(seconds, 0.0), 0.01))


class FakeMistSession(APIRequest):
    """Answer the real SDK endpoint functions through a local transport."""

    def __init__(self, family: str = "ap") -> None:
        """Create regional authentication context and scripted responses."""
        super().__init__()
        self._cloud_uri = "api.eu.mist.com"
        self._apitoken = [secrets.token_urlsafe(24)]
        self._apitoken_index = 0
        self.script = SimpleNamespace(
            actions=[],
            scope=SimpleNamespace(org_id=Identities.ORG, site_id=Identities.SITE, family=family, devices=[], edges=[]),
            start=SimpleNamespace(
                status=200,
                data={"id": Identities.CAPTURE, "site_id": Identities.SITE, "org_id": Identities.ORG},
                before_answer=None,
                entered=threading.Event(),
                release=threading.Event(),
            ),
            status=SimpleNamespace(status=200, data={"id": Identities.CAPTURE}),
            stop=SimpleNamespace(status=200, data={}, sockets=[], auto_ack=True),
        )
        self._session.headers["Authorization"] = "Token " + self._apitoken[0]
        self.script.start.release.set()

    def mist_get(self, uri: str, query: object = None) -> APIResponse:
        """Record one SDK read and return its controlled response."""
        self.script.actions.append(("GET", uri, query))
        if uri.endswith("/pcaps/capture"):
            return self.answer(self.script.status.status, self.script.status.data)
        if uri.endswith("/sites"):
            return self.answer(200, [{"id": Identities.SITE, "name": "Local site", "org_id": Identities.ORG}])
        if uri.endswith("/mxedges"):
            return self.answer(
                200, [{"id": Identities.DEVICE, "name": "Local edge", "org_id": self.script.scope.org_id}]
            )
        if "/mxedges/" in uri:
            return self.answer(200, {"id": Identities.DEVICE, "org_id": self.script.scope.org_id})
        if uri.endswith("/devices"):
            family = self.script.scope.family
            kind = "ap" if family == "ap" else "switch" if family == "ex" else "gateway"
            model = "SRX300" if family == "srx" else "SSR120" if family == "ssr" else "EX4100"
            return self.answer(200, [{"id": Identities.DEVICE, "name": "Local device", "type": kind, "model": model}])
        return self.answer(200, {"id": self.script.scope.site_id, "org_id": self.script.scope.org_id})

    def mist_post(self, uri: str, body: object = None) -> APIResponse:
        """Record the actual SDK capture request without sending it."""
        self.script.actions.append(("POST", uri, deepcopy(body)))
        self.script.start.entered.set()
        callback = self.script.start.before_answer
        if callback is not None:
            callback()
        if not self.script.start.release.wait(2.0):
            raise TimeoutError("The local fixture did not release the capture response.")
        return self.answer(self.script.start.status, self.script.start.data)

    def mist_delete(self, uri: str, query: object = None) -> APIResponse:
        """Record one actual SDK cloud stop without a cloud connection."""
        self.script.actions.append(("DELETE", uri, query))
        return self.answer(self.script.stop.status, self.script.stop.data)

    @staticmethod
    def answer(status: int, data: object) -> APIResponse:
        """Build the real SDK response from synthetic JSON."""
        response = Response()
        response.status_code = status
        response._content = json.dumps(data).encode("utf-8")
        response.headers["Content-Type"] = "application/json"
        return APIResponse(response=response, url="https://api.eu.mist.com/local-fixture")


class ControlledSocket(_MistWebsocket):
    """Use real SDK context and callbacks without opening a remote socket."""

    def __init__(
        self,
        mist_session: FakeMistSession,
        channels: list[str] | None = None,
        *,
        site_id: str | None = None,
        **settings,
    ) -> None:
        """Keep SDK URL, authentication, and subscription configuration."""
        selected = channels if channels is not None else [f"/sites/{site_id}/pcaps"]
        super().__init__(mist_session, channels=selected, **settings)
        self.fixture = mist_session.script
        self.disconnect_count = 0
        self.fixture.stop.sockets.append(self)

    def connect(self, run_in_background: bool = True) -> None:
        """Open only the controlled transport and request its subscription."""
        self._finished.clear()
        self._connected.set()
        self.fixture.actions.append(("subscribe", self._channels[0], self._build_ws_url()))
        if self._on_open_cb is not None:
            self._on_open_cb()
        if self.fixture.stop.auto_ack:
            self.emit({"event": "channel_subscribed", "channel": self._channels[0]})

    def emit(self, message: dict[str, object]) -> None:
        """Deliver one fixture event through the registered SDK callback."""
        if not self._connected.is_set():
            return
        if message.get("event") == "channel_subscribed":
            self.fixture.actions.append(("ack", str(message.get("channel")), None))
        if self._on_message_cb is not None:
            self._on_message_cb(message)

    def disconnect(self, wait: bool = False, timeout: float | None = None) -> None:
        """Close the owned controlled transport exactly once."""
        if self._finished.is_set():
            return
        self.disconnect_count += 1
        self._connected.clear()
        self._finished.set()
        if self._on_close_cb is not None:
            self._on_close_cb(1000, None)

    def ready(self) -> bool:
        """Report the controlled connection state."""
        return self._connected.is_set()


class LegacyTimer:
    """Run the installed utility wrapper's timer at a controlled instant."""

    timers: list[LegacyTimer] = []

    def __init__(self, interval: float, function: Callable[[], None]) -> None:
        """Store the real wrapper's duration and disconnect callback."""
        self.interval = interval
        self.function = function
        self.cancelled = False

    def start(self) -> None:
        """Record a timer instead of sleeping for its duration."""
        self.timers.append(self)

    def cancel(self) -> None:
        """Prevent a cancelled timer from firing."""
        self.cancelled = True

    def fire(self) -> None:
        """Invoke the exact wrapper callback when the test reaches its deadline."""
        if not self.cancelled:
            self.function()
