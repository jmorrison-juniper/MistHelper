"""Build safe Mist WebSocket connection parameters.

Why:
    Issue #3671 replaces private Mist SDK WebSocket code. These classes keep
    authentication details on the server and validate shell addresses before a
    connection can send credentials.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The transport logs safe connection metadata only.
import ssl  # TLS settings mirror the Mist SDK behavior.
from dataclasses import dataclass  # TransportProfile is immutable configuration.
from http.cookiejar import Cookie  # Cookie iteration uses the standard cookie type.
from urllib.parse import urlparse  # URL parsing avoids unsafe string checks.

from src.websocket_streams.intake.fields import StreamRequestError  # Address refusals use the HTTP contract.

logger = logging.getLogger(__name__)  # Keep transport logs under this module.


@dataclass(frozen=True, slots=True)
class TransportProfile:
    """Configuration for one live WebSocket connection.

    Args:
        stream_url: A test stream address, or None to build the Mist address.
        allow_loopback: Allow loopback shell URLs for offline tests.
        read_timeout_seconds: Quiet time before a ping.
        subscribe_timeout_seconds: Wait for each channel subscription answer.
        reconnect_delays: Retry waits for channel stream callers.
    """

    stream_url: str | None = None  # Tests can replace the Mist cloud address.
    allow_loopback: bool = False  # Fake cloud tests use ws://127.0.0.1 only.
    read_timeout_seconds: float = 20.0  # The client pings after one quiet interval.
    subscribe_timeout_seconds: float = 10.0  # Mist should answer each subscribe quickly.
    reconnect_delays: tuple[float, ...] = (1.0, 2.0, 4.0)  # Runners use the documented retry waits.


class MistStreamEndpoint:
    """Read WebSocket connection values from a Mist API session."""

    def __init__(self, apisession: object, profile: TransportProfile | None = None) -> None:
        """Build the endpoint.

        Args:
            apisession: The Mist API session with the SDK private attributes.
            profile: Optional transport configuration.
        """
        logger.info("Building Mist WebSocket endpoint")  # Log before reading session state.
        self._apisession = apisession  # The endpoint reads private SDK-compatible attributes.
        self._profile = profile or TransportProfile()  # Defaults match the transport contract.
        self._cloud_host = self._read_cloud_host()  # Store the host for repeated safe use.
        logger.debug("Built Mist WebSocket endpoint for host %s", self._cloud_host)  # Log only the host.

    @property
    def profile(self) -> TransportProfile:
        """Return the transport profile.

        Returns:
            The immutable transport profile.
        """
        return self._profile  # Callers need the timeout and retry values.

    @property
    def cloud_host(self) -> str:
        """Return the Mist API host.

        Returns:
            The host name, such as ``api.mist.com``.
        """
        return self._cloud_host  # Shell policy needs the same host.

    def stream_url(self) -> str:
        """Return the Mist stream address.

        Returns:
            The configured test address or the derived Mist stream address.
        """
        if self._profile.stream_url is not None:  # Tests inject a loopback stream address.
            return self._profile.stream_url  # The test address must stay byte-for-byte.
        websocket_host = self._cloud_host.replace("api.", "api-ws.", 1)  # Match the Mist SDK address rule.
        return f"wss://{websocket_host}/api-ws/v1/stream"  # The stream path is fixed by the Mist API.

    def headers(self) -> list[str]:
        """Return the authorization headers for token sign-in.

        Returns:
            A websocket-client header list.
        """
        logger.info("Building Mist WebSocket token headers for host %s", self._cloud_host)  # Log before auth setup.
        tokens = getattr(self._apisession, "_apitoken", [])  # The SDK stores API tokens on this private field.
        index = getattr(self._apisession, "_apitoken_index", -1)  # The SDK stores the active token index here.
        if tokens and isinstance(index, int) and 0 <= index < len(tokens):  # Token sign-in takes precedence.
            logger.debug("Built one Mist WebSocket token header for host %s", self._cloud_host)  # Do not log token.
            return [f"Authorization: Token {tokens[index]}"]  # websocket-client expects header strings.
        logger.debug(
            "Built zero Mist WebSocket token headers for host %s", self._cloud_host
        )  # Cookie sign-in uses none.
        return []  # Password sign-in uses cookies.

    def cookie(self) -> str | None:
        """Return the safe cookie header text for password sign-in.

        Returns:
            The cookie header text, or None when no safe cookie exists.
        """
        logger.info("Building Mist WebSocket cookies for host %s", self._cloud_host)  # Log before cookie processing.
        session = getattr(self._apisession, "_session", None)  # The SDK stores the requests session here.
        cookies = getattr(session, "cookies", None)  # Requests keeps cookies on this jar.
        safe = [self._cookie_pair(cookie) for cookie in cookies or []]  # Skip cookies that could inject headers.
        joined = "; ".join(pair for pair in safe if pair is not None)  # websocket-client wants one cookie string.
        logger.debug("Built %s safe Mist WebSocket cookies for host %s", len([p for p in safe if p]), self._cloud_host)
        return joined or None  # An empty string should not become a header.

    def sslopt(self) -> dict[str, object]:
        """Return websocket-client TLS options.

        Returns:
            TLS options derived from the requests session.
        """
        logger.info("Building Mist WebSocket TLS options for host %s", self._cloud_host)  # Log before TLS setup.
        ssl_options: dict[str, object] = {}  # websocket-client accepts this option dictionary.
        session = getattr(self._apisession, "_session", None)  # The requests session holds verify and cert.
        verify = getattr(session, "verify", True)  # Requests defaults to certificate validation.
        cert = getattr(session, "cert", None)  # Requests allows a client certificate value.
        if verify is False:  # The SDK disables certificate checks for this explicit setting.
            ssl_options["cert_reqs"] = ssl.CERT_NONE  # websocket-client uses ssl constants.
            ssl_options["check_hostname"] = False  # Hostname checks must match the disabled validation.
        elif isinstance(verify, str):  # A path names a CA bundle.
            ssl_options["ca_certs"] = verify  # websocket-client uses ca_certs for the same path.
        self._add_cert_options(ssl_options, cert)  # Client certificate handling matches the SDK.
        logger.debug("Built %s Mist WebSocket TLS options for host %s", len(ssl_options), self._cloud_host)
        return ssl_options  # Callers pass this directly to websocket-client.

    def host_label(self, url: str) -> str:
        """Return only the host label of a URL.

        Args:
            url: A WebSocket URL.

        Returns:
            The URL host, or an empty string when parsing fails.
        """
        parsed = urlparse(url)  # Parsing keeps path and query out of logs.
        return parsed.hostname or ""  # Logs can hold only this label.

    def _read_cloud_host(self) -> str:
        """Read the API cloud host from the SDK-compatible session.

        Returns:
            The normalized host text.
        """
        raw_host = getattr(self._apisession, "_cloud_uri", "")  # The Mist SDK private field holds the cloud host.
        parsed = urlparse(raw_host if "://" in raw_host else f"https://{raw_host}")  # Accept host-only test values.
        return parsed.hostname or raw_host  # Fallback keeps tests explicit.

    def _cookie_pair(self, cookie: Cookie) -> str | None:
        """Return one safe cookie pair.

        Args:
            cookie: One cookie from the requests cookie jar.

        Returns:
            The ``name=value`` text, or None when the cookie is unsafe.
        """
        value = cookie.value or ""  # Empty cookie values are allowed by the SDK behavior.
        if "\r" in cookie.name or "\n" in cookie.name or "\r" in value or "\n" in value:  # CRLF can inject headers.
            logger.warning("Skipping unsafe Mist WebSocket cookie for host %s", self._cloud_host)  # Do not log cookie.
            return None  # Unsafe cookies must not leave the process.
        return f"{cookie.name}={value}"  # websocket-client joins cookie pairs with semicolons.

    def _add_cert_options(self, ssl_options: dict[str, object], cert: object) -> None:
        """Add client certificate options.

        Args:
            ssl_options: The option dictionary to update.
            cert: The requests session certificate value.
        """
        if isinstance(cert, str):  # A single path holds the certificate file.
            ssl_options["certfile"] = cert  # websocket-client uses certfile for this case.
        elif isinstance(cert, tuple) and cert:  # A tuple can hold certificate and key paths.
            ssl_options["certfile"] = cert[0]  # The first item is the certificate.
            if len(cert) > 1:  # The second item is optional.
                ssl_options["keyfile"] = cert[1]  # websocket-client uses keyfile for the private key.


class ShellAddressPolicy:
    """Validate shell and screen WebSocket addresses before credentials are sent."""

    def __init__(self, cloud_host: str, allow_loopback: bool = False) -> None:
        """Build the shell address policy.

        Args:
            cloud_host: The Mist API cloud host.
            allow_loopback: True when offline tests can use loopback WebSocket URLs.
        """
        logger.info("Building shell address policy for host %s", cloud_host)  # Log before deriving the domain.
        self._cloud_host = cloud_host.lower().strip(".")  # Domain comparison is case-insensitive.
        self._allow_loopback = allow_loopback  # Tests need loopback without TLS.
        self._domain = ".".join(self._cloud_host.split(".")[-2:])  # The contract defines the base domain this way.
        logger.debug("Built shell address policy for domain %s", self._domain)  # The domain is safe to log.

    def check(self, url: str) -> str:
        """Return a safe shell address.

        Args:
            url: The address returned by the Mist REST trigger.

        Returns:
            The same URL when it is allowed.

        Raises:
            StreamRequestError: The address is outside the allowed policy.
        """
        logger.info("Checking shell WebSocket address")  # Do not log the URL path.
        parsed = urlparse(url)  # Use structured URL checks.
        host = (parsed.hostname or "").lower().strip(".")  # Normalize host for comparison.
        if self._is_allowed_loopback(parsed.scheme, host, parsed.port):  # Tests can use a local fake cloud.
            logger.debug("Accepted loopback shell WebSocket host %s", host)  # The host is safe to log.
            return url  # The fake cloud URL is allowed only by explicit profile.
        if parsed.scheme == "wss" and self._is_mist_domain(host):  # Production addresses must use TLS in the domain.
            logger.debug("Accepted Mist shell WebSocket host %s", host)  # Do not log path or query.
            return url  # The URL passed the policy.
        logger.warning("Refused shell WebSocket host %s", host)  # The host is safe to log.
        raise StreamRequestError("bad_request", "The shell address is outside the Mist cloud domain.")  # Refuse safely.

    def _is_allowed_loopback(self, scheme: str, host: str, port: int | None) -> bool:
        """Return whether a loopback URL is allowed.

        Args:
            scheme: The parsed URL scheme.
            host: The parsed and normalized host.
            port: The parsed port.

        Returns:
            True when the URL is an allowed loopback URL.
        """
        return self._allow_loopback and scheme == "ws" and host == "127.0.0.1" and port is not None  # Tests only.

    def _is_mist_domain(self, host: str) -> bool:
        """Return whether a host belongs to the Mist domain.

        Args:
            host: The parsed and normalized host.

        Returns:
            True when the host is the base domain or a subdomain.
        """
        return host == self._domain or host.endswith(f".{self._domain}")  # The leading dot blocks look-alike domains.
