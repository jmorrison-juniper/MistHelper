"""Build safe Mist WebSocket connection parameters."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Structured records use repository logging handlers.
import ssl  # TLS settings mirror the Mist SDK behavior.
from dataclasses import dataclass  # The transport profile is immutable.
from urllib.parse import urlparse  # URL parsing prevents unsafe string checks.

import websocket  # Connection failures use websocket-client error types.
from src.websocket_streams.intake.fields.error import StreamRequestError  # Policy refusals use the HTTP contract.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # T072 provides the safe JSON logging boundary.


@dataclass(frozen=True, slots=True)
class TransportProfile:
    """Hold immutable settings for one live WebSocket connection."""

    stream_url: str | None = None  # Tests can replace the Mist cloud address.
    allow_loopback: bool = False  # Fake cloud tests can use loopback WebSockets.
    read_timeout_seconds: float = 20.0  # The reader pings after one quiet interval.
    subscribe_timeout_seconds: float = 10.0  # The cloud must answer each subscription.
    reconnect_delays: tuple[float, ...] = (1.0, 2.0, 4.0)  # Callers use bounded retry delays.


class SessionConnectionValues:
    """Read authentication and TLS values from one Mist API session."""

    def __init__(self, apisession: object) -> None:
        """Store the session and its normalized cloud host."""
        raw_host = getattr(apisession, "_cloud_uri", "")  # Read the SDK-compatible cloud value.
        parsed = urlparse(raw_host if "://" in raw_host else f"https://{raw_host}")  # Accept host-only values.
        self._apisession, self._cloud_host = apisession, parsed.hostname or raw_host  # Store session and host.
        self._log = StructuredTransportLogger(logging.getLogger(__name__))  # Emit bounded JSON records.

    def headers(self) -> list[str]:
        """Return the active token header when token sign-in is configured."""
        self._log.emit(logging.INFO, "transport_auth_build", {"action": "token_headers"})  # Log the safe action.
        tokens, index = (
            getattr(self._apisession, "_apitoken", []),
            getattr(self._apisession, "_apitoken_index", -1),
        )  # Read token state together.
        headers = (
            [f"Authorization: Token {tokens[index]}"]
            if tokens and isinstance(index, int) and 0 <= index < len(tokens)
            else []
        )  # Validate the index before building the header.
        self._log.emit(logging.DEBUG, "transport_auth_ready", {"count": len(headers)})  # Log only the count.
        return headers  # Cookie sign-in uses an empty header list.

    def cookie(self) -> str | None:
        """Return safe cookie pairs for password sign-in."""
        self._log.emit(logging.INFO, "transport_cookie_build", {"action": "cookie_header"})  # Log the safe action.
        cookies = getattr(getattr(self._apisession, "_session", None), "cookies", None)  # Read the cookie jar.
        pairs = [
            f"{cookie.name}={cookie.value or ''}"
            for cookie in cookies or []
            if not any(char in cookie.name or char in (cookie.value or "") for char in "\r\n")
        ]  # Preserve order while excluding header-control characters.
        self._log.emit(logging.DEBUG, "transport_cookie_ready", {"count": len(pairs)})  # Log only the count.
        return "; ".join(pairs) or None  # An empty jar must not create a header.

    def sslopt(self) -> dict[str, object]:
        """Return websocket-client TLS options from the requests session."""
        self._log.emit(logging.INFO, "transport_tls_build", {"action": "tls_options"})  # Log the safe action.
        verify, cert = (
            getattr(getattr(self._apisession, "_session", None), "verify", True),
            getattr(getattr(self._apisession, "_session", None), "cert", None),
        )  # Read both requests-compatible TLS values.
        options = self._tls_options(verify, cert)  # Build the complete websocket-client mapping.
        self._log.emit(logging.DEBUG, "transport_tls_ready", {"count": len(options)})  # Log only the count.
        return options  # The clients pass this mapping without changes.

    def _tls_options(self, verify: object, cert: object) -> dict[str, object]:
        """Build the TLS mapping from requests-compatible values."""
        options: dict[str, object] = {}  # Start with secure websocket-client defaults.
        if verify is False:  # Match an explicit SDK verification disablement.
            options.update({"cert_reqs": ssl.CERT_NONE, "check_hostname": False})  # Disable both checks.
        elif isinstance(verify, str):  # A string names the CA bundle.
            options["ca_certs"] = verify  # Use the websocket-client option name.
        if isinstance(cert, str):  # A string names one certificate file.
            options["certfile"] = cert  # Pass the client certificate.
        elif isinstance(cert, tuple) and cert:  # A tuple can include a private key.
            options.update({"certfile": cert[0], **({"keyfile": cert[1]} if len(cert) > 1 else {})})  # Add files.
        return options  # Return the complete TLS mapping.


class MistStreamEndpoint(SessionConnectionValues):
    """Provide safe connection values for one Mist cloud endpoint."""

    def __init__(self, apisession: object, profile: TransportProfile | None = None) -> None:
        """Build the endpoint from one SDK-compatible API session."""
        super().__init__(apisession)  # Read authentication and cloud values once.
        self._profile = profile or TransportProfile()  # Use the documented defaults when no profile exists.
        self._log.emit(logging.DEBUG, "transport_endpoint_ready", {"action": "endpoint"})  # Report safe readiness.

    @property
    def profile(self) -> TransportProfile:
        """Return the immutable transport profile."""
        return self._profile  # Clients need timeout and reconnect values.

    @property
    def cloud_host(self) -> str:
        """Return the normalized Mist API host."""
        return self._cloud_host  # Address policy uses the same cloud boundary.

    def stream_url(self) -> str:
        """Return the configured or derived stream address."""
        if self._profile.stream_url is not None:  # Offline tests provide an exact loopback address.
            return self._profile.stream_url  # Keep the supplied address byte-for-byte.
        websocket_host = self._cloud_host.replace("api.", "api-ws.", 1)  # Apply the Mist SDK host rule.
        return f"wss://{websocket_host}/api-ws/v1/stream"  # Use the fixed Mist stream path.

    def host_label(self, url: str) -> str:
        """Return only the host part of a WebSocket address."""
        return urlparse(url).hostname or ""  # Exclude the path, query, and credentials.


class ShellAddressPolicy:
    """Validate shell and screen addresses before credentials leave the server."""

    def __init__(self, cloud_host: str, allow_loopback: bool = False) -> None:
        """Build the policy for one Mist cloud domain."""
        self._allow_loopback = allow_loopback  # Offline tests explicitly permit loopback.
        normalized = cloud_host.lower().strip(".")  # Domain checks are case-insensitive.
        self._domain = ".".join(normalized.split(".")[-2:])  # The contract uses the base cloud domain.
        self._log = StructuredTransportLogger(logging.getLogger(__name__))  # Emit bounded JSON records.

    def check(self, url: str) -> str:
        """Return the address when it meets the transport policy."""
        self._log.emit(logging.INFO, "shell_address_check", {"action": "validate"})  # Do not log the address.
        parsed = urlparse(url)  # Parse the address before any credentials are built.
        if self._is_allowed(parsed.scheme, parsed.hostname or "", parsed.port):  # Apply loopback or TLS policy.
            self._log.emit(logging.DEBUG, "shell_address_allowed", {"status": "allowed"})  # Log safe status.
            return url  # Keep the accepted address unchanged.
        self._log.emit(logging.WARNING, "shell_address_refused", {"status": "outside_domain"})  # Log safe reason.
        raise StreamRequestError("bad_request", "The shell address is outside the Mist cloud domain.")  # Refuse it.

    def _is_allowed(self, scheme: str, host: str, port: int | None) -> bool:
        """Return whether the normalized address meets either policy."""
        normalized = host.lower().strip(".")  # Domain checks are case-insensitive.
        loopback = self._allow_loopback and scheme == "ws" and normalized == "127.0.0.1" and port is not None
        mist = scheme == "wss" and (normalized == self._domain or normalized.endswith(f".{self._domain}"))
        return loopback or mist  # Permit explicit tests or secure Mist cloud hosts.


class ConnectFailure:
    """Map WebSocket open failures to safe operator reasons."""

    REFUSED_TEXT = "The Mist cloud refused the WebSocket connection with HTTP status {status}."  # HTTP refusal.
    TIMEOUT_TEXT = "The Mist cloud did not answer the WebSocket connection in time."  # Handshake timeout.
    TLS_TEXT = "The TLS check of the Mist cloud connection failed."  # TLS validation failure.
    ADDRESS_TEXT = "The portal could not find the address of the Mist cloud."  # Name lookup failure.
    NETWORK_TEXT = "The portal could not connect to the Mist cloud."  # TCP or proxy failure.

    @classmethod
    def reason(cls, error: BaseException) -> str | None:
        """Return the safe reason for one recognized connection failure."""
        if isinstance(error, websocket.WebSocketBadStatusException):  # The cloud returned an HTTP status.
            return cls.REFUSED_TEXT.format(status=error.status_code)  # Keep only the numeric status.
        for error_types, text in cls._rules():  # Match specific families before broad operating system errors.
            if isinstance(error, error_types):  # Use the first matching family.
                return text  # Return the stable operator message.
        return None  # Program errors keep their original handling.

    @classmethod
    def _rules(cls) -> tuple[tuple[tuple[type[BaseException], ...], str], ...]:
        """Return connection failure families in match order."""
        return (
            ((TimeoutError, websocket.WebSocketTimeoutException), cls.TIMEOUT_TEXT),  # Timeouts precede OSError.
            ((ssl.SSLError,), cls.TLS_TEXT),  # TLS errors can also inherit from OSError.
            ((websocket.WebSocketAddressException,), cls.ADDRESS_TEXT),  # Name lookup failures are distinct.
            (
                (OSError, websocket.WebSocketProxyException, websocket.WebSocketConnectionClosedException),
                cls.NETWORK_TEXT,
            ),  # Remaining connection failures share one safe reason.
        )
