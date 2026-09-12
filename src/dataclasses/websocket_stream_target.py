"""Frozen dataclass that groups the WebSocket stream connection-target fields.

``ARPCommandManager._listen_for_output`` in ``MistHelper.py`` took 8 parameters,
which exceeded the 5-Item Rule's max-5 limit. The five connection-identity
values (host, API token, site, device, session) that locate the device stream
are grouped here so the method's option parameters (timeout, idle_timeout,
debug) stay as direct arguments and the signature drops to 4 parameters.

Issue: https://github.com/jmorrison-juniper/MistHelper/issues/470
"""

from __future__ import annotations  # Enable PEP 604 union syntax on older runtimes.

from dataclasses import dataclass  # The standard library dataclass decorator.


@dataclass(frozen=True, slots=True)
class WebSocketStreamTarget:
    """Connection identity that locates one device's WebSocket command stream."""

    mist_host: str  # Mist API-WS host the stream connects to (for example api-ws.mist.com).
    mist_apitoken: str  # API token used in the WebSocket Authorization header.
    site_id: str  # Site UUID the target device belongs to.
    device_id: str  # Device UUID whose command output is being streamed.
    session_id: str  # Command session id used to match inbound stream messages.
