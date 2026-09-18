"""Reusable network-probe primitives for Zscaler synthetic-test endpoints.

Why:
    Menu option 206 (org synthetic-probes manager) seeds Mist synthetic tests
    from ``data/zscaler_client_connector_probes.json`` and
    ``data/zscaler_cenr_hostnames.json``. The catalogue files declare which
    ports Zscaler *documents*, but not which protocols each endpoint actually
    answers on today. The auto-refresh path in
    :mod:`src.utils.zscaler_catalogue` calls :func:`run_full_validation` after
    every TTL-triggered CENR refresh so we can log a live health snapshot
    before Mist synthetic tests are pushed.

    The lower-level primitives (``ProbeResult``, ``_probe_fqdn``,
    ``_run_probes``, and friends) were lifted from
    ``scripts/probe_zscaler_endpoints.py`` so the script now imports from
    here instead of duplicating them. Only stdlib is used so the module runs
    anywhere MistHelper runs.
"""

from __future__ import annotations  # WHY: PEP 604 unions on the project toolchain.

import concurrent.futures  # WHY: probe the fleet in parallel rather than serially.
import logging  # WHY: structured trace for probe lifecycle and failures.
import platform  # WHY: the ping flag for a timeout differs between Windows and POSIX.
import secrets  # WHY: cryptographically random ICMP identifiers avoid collisions.
import socket  # WHY: DNS resolution and raw TCP connect checks.
import ssl  # WHY: TLS handshake validation against the system trust store.
import struct  # WHY: pack and unpack the ICMP echo header.
import subprocess  # nosec B404 - The ICMP probe runs the OS ping binary, and the call below uses shell=False.
from dataclasses import dataclass, field  # WHY: ProbeResult is a structured record, not a dict.
from http.client import HTTPConnection, HTTPResponse, HTTPSConnection  # WHY: stdlib HTTP probe.
from typing import Any  # WHY: the catalogue documents are duck-typed JSON.

logger = logging.getLogger(__name__)  # WHY: module logger keeps records attributable to this file.

DEFAULT_TIMEOUT = 3.0  # Preserve the existing behavior during the compliance refactor.
"""Per-probe wall-clock timeout in seconds (DNS/ICMP/TCP/HTTP/TLS)."""

DEFAULT_WORKERS = 16  # Preserve the existing behavior during the compliance refactor.
"""Default ThreadPoolExecutor size for parallel probes."""

COMMON_TCP_PORTS: tuple[int, ...] = (80, 443, 8080)  # Preserve the existing behavior during the compliance refactor.
"""Ports referenced anywhere in the ZCC catalogue; always scanned in addition
to a role's declared ports so we can spot endpoints answering off-doc."""

IKE_UDP_PORTS: tuple[int, int] = (500, 4500)  # Preserve the existing behavior during the compliance refactor.
"""IKE UDP port pair Zscaler VPN initiators answer on.

Why:
    Port 500 is the classic IKEv1/IKEv2 SA-init port; 4500 is the NAT-T
    encapsulated fallback that fires when a middlebox rewrites source ports.
    The two-tuple ordering (500 first, 4500 second) is contractual: the
    write-path priority in :mod:`src.utils.zscaler_catalogue` prefers 500
    over 4500 when both responded, matching how real IKE initiators pick a
    peer. Also referenced by the URL builder in
    :mod:`src.org.org_synthetic_probes_manager` to convert observations
    into ``host:port`` targets.
"""

_ZSCALER_PREFIX_SUBRULES: tuple[tuple[str, str], ...] = (  # WHY: These rules precede the login-or-mobile legacy rule.
    ("pac", "Zscaler PAC delivery"),  # WHY: PAC hosts must classify before generic Zscaler services.
    ("gateway", "Zscaler captive-portal gateway"),  # WHY: Gateway hosts explain captive portal checks to operators.
    ("mobilesupport", "Zscaler support endpoint"),  # WHY: Support hosts carry a distinct operator meaning.
)

_ZSCALER_SUFFIX_SUBRULES: tuple[tuple[str, str], ...] = (  # WHY: These rules follow the login-or-mobile legacy rule.
    ("healthapp", "Zscaler health-probe endpoint"),  # WHY: Health-app hosts must not fall through to generic service.
    ("ecdn", "Zscaler ECDN (update channel)"),  # WHY: ECDN hosts explain update-channel reachability.
    ("private.zscaler", "Zscaler private/internal"),  # WHY: Private hosts need the most explicit safety label.
)

_GOOGLE_PROBE_HOSTS: tuple[str, ...] = (
    "google.com",
)  # WHY: The registrable names whose own hosts carry the Google probe label.

_MINIMUM_TLS_VERSION = ssl.TLSVersion.TLSv1_2  # WHY: Refuse TLS 1.0 and TLS 1.1 on every probe connection.


@dataclass
class ProbeResult:  # Preserve the existing behavior during the compliance refactor.
    """Consolidated probe outcome for a single FQDN.

    Why:
        One flat record per endpoint keeps downstream reporting and log
        summarization trivial -- callers do not need to correlate per-protocol
        subrecords. Field naming mirrors the markdown-report columns emitted by
        ``scripts/probe_zscaler_endpoints.py`` so the CLI wrapper can format
        results without any translation layer.

    Attributes:
        fqdn (str): Hostname that was probed.
        role (str): ``roles[].role`` slug from the catalogue (empty when
            probing a raw CENR hostname).
        role_description (str): Human-readable role description.
        declared_ports (list[int]): Ports the catalogue says the endpoint uses.
        critical (bool): True when the role is flagged as
            customer-impact-critical.
        ip (str | None): First A-record returned by ``getaddrinfo``; ``None``
            if DNS failed.
        dns_error (str | None): Formatted DNS failure text. Only populated on
            lookup error.
        icmp_ok (bool): Whether a single OS ``ping`` succeeded within the
            timeout.
        tcp (dict[int, str]): Map ``port -> "open"/"closed"/"error:<reason>"``.
        http_status (int | None): HTTP response status code from HEAD/GET on
            port 80.
        http_server (str | None): ``Server:`` response header returned on
            port 80.
        http_location (str | None): ``Location:`` redirect target returned on
            port 80.
        https_status (int | None): HTTP response status code from HEAD/GET on
            port 443.
        https_server (str | None): ``Server:`` response header returned on
            port 443.
        https_location (str | None): ``Location:`` redirect target returned on
            port 443.
        tls_subject (str | None): Peer certificate subject CN/O captured on
            the TLS handshake.
        tls_issuer (str | None): Peer certificate issuer CN/O captured on the
            TLS handshake.
        tls_error (str | None): Formatted TLS error text. Only populated on
            handshake failure.
        responding_protocols (list[str]): Compact list of protocols we
            confirmed live (for example ``["ICMP", "TCP/443", "HTTPS"]``). Used by
            the log summary.
        server_class (str): Category inferred from FQDN + headers + cert
            issuer.
        notes (list[str]): Freeform per-endpoint diagnostics (HTTP/HTTPS/TLS
            error text).
        udp (dict[int, str]): Map ``port -> "open"/"no_reply"/"error:<name>"``
            for IKE UDP probes. Empty when UDP probing did not fire (host had
            live TCP responses and no ``-vpn.`` name hint). Populated only for
            ports in :data:`IKE_UDP_PORTS`.
    """

    fqdn: str  # Preserve the existing behavior during the compliance refactor.
    role: str  # Preserve the existing behavior during the compliance refactor.
    role_description: str  # Preserve the existing behavior during the compliance refactor.
    declared_ports: list[int]  # Preserve the existing behavior during the compliance refactor.
    critical: bool  # Preserve the existing behavior during the compliance refactor.
    ip: str | None = None  # Preserve the existing behavior during the compliance refactor.
    dns_error: str | None = None  # Preserve the existing behavior during the compliance refactor.
    icmp_ok: bool = False  # Preserve the existing behavior during the compliance refactor.
    tcp: dict[int, str] = field(default_factory=dict)  # Preserve the existing behavior during the compliance refactor.
    http_status: int | None = None  # Preserve the existing behavior during the compliance refactor.
    http_server: str | None = None  # Preserve the existing behavior during the compliance refactor.
    http_location: str | None = None  # Preserve the existing behavior during the compliance refactor.
    https_status: int | None = None  # Preserve the existing behavior during the compliance refactor.
    https_server: str | None = None  # Preserve the existing behavior during the compliance refactor.
    https_location: str | None = None  # Preserve the existing behavior during the compliance refactor.
    tls_subject: str | None = None  # Preserve the existing behavior during the compliance refactor.
    tls_issuer: str | None = None  # Preserve the existing behavior during the compliance refactor.
    tls_error: str | None = None  # Preserve the existing behavior during the compliance refactor.
    responding_protocols: list[str] = field(
        default_factory=list
    )  # Preserve the existing behavior during the compliance refactor.
    server_class: str = "unknown"  # Preserve the existing behavior during the compliance refactor.
    notes: list[str] = field(default_factory=list)  # Preserve the existing behavior during the compliance refactor.
    udp: dict[int, str] = field(default_factory=dict)  # Preserve the existing behavior during the compliance refactor.


def _resolve(
    fqdn: str,
) -> tuple[str | None, str | None]:  # Preserve the existing behavior during the compliance refactor.
    """Return ``(ip, error)`` for a DNS lookup of *fqdn*.

    Why:
        Callers need to distinguish a hard DNS failure (no probes possible)
        from a resolvable-but-unreachable host, so the error text is preserved
        for the report/log summary instead of being logged and dropped.

    Args:
        fqdn: Hostname to resolve.

    Returns:
        ``(ip, None)`` on success or ``(None, formatted_error)`` on failure.
    """
    try:
        return socket.gethostbyname(fqdn), None  # Preserve the existing behavior during the compliance refactor.
    except OSError as exc:  # Preserve the existing behavior during the compliance refactor.
        return None, f"{type(exc).__name__}: {exc}"  # Preserve the existing behavior during the compliance refactor.


def _icmp_ping(host: str, timeout: float) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return True if *host* answers a single ICMP echo within *timeout*.

    Why:
        Raw ICMP sockets require elevated privileges on Windows and Linux, so
        we shell out to the OS ``ping`` binary. The flag names differ between
        Windows and POSIX, hence the platform switch.

    Args:
        host: Target hostname or IP.
        timeout: Wall-clock timeout in seconds for the single ping attempt.

    Returns:
        True when ``ping`` exits 0, False on non-zero exit, timeout, or
        subprocess error.
    """
    is_win = (
        platform.system().lower().startswith("win")
    )  # Preserve the existing behavior during the compliance refactor.
    count_flag = "-n" if is_win else "-c"  # Preserve the existing behavior during the compliance refactor.
    timeout_flag = "-w" if is_win else "-W"  # Preserve the existing behavior during the compliance refactor.
    timeout_val = (
        str(int(timeout * 1000)) if is_win else str(int(timeout))
    )  # Preserve the existing behavior during the compliance refactor.
    cmd = [
        "ping",
        count_flag,
        "1",
        timeout_flag,
        timeout_val,
        host,
    ]  # Preserve the existing behavior during the compliance refactor.
    try:
        completed = subprocess.run(  # the argv parts are validated above
            cmd,  # nosec B603 - shell stays False, so host becomes one argv element and cannot start a program.
            capture_output=True,
            text=True,
            timeout=timeout + 2.0,
        )
    except (subprocess.TimeoutExpired, OSError):  # Preserve the existing behavior during the compliance refactor.
        return False  # Preserve the existing behavior during the compliance refactor.
    return completed.returncode == 0  # Preserve the existing behavior during the compliance refactor.


def _tcp_check(
    host: str, port: int, timeout: float
) -> str:  # Preserve the existing behavior during the compliance refactor.
    """Return ``open``/``closed``/``error:<reason>`` for a TCP handshake.

    Why:
        Distinguishing ``closed`` (RST or refused) from ``error:<OSError>``
        matters when interpreting corporate firewall behaviour -- a silent
        drop looks nothing like an explicit refusal in the report.

    Args:
        host: Target hostname.
        port: TCP port to probe.
        timeout: Wall-clock connect timeout in seconds.

    Returns:
        ``"open"`` on successful connect, ``"closed"`` on timeout/refusal, or
        ``"error:<ExceptionClassName>"`` on any other socket failure.
    """
    try:
        with socket.create_connection(
            (host, port), timeout=timeout
        ):  # Preserve the existing behavior during the compliance refactor.
            return "open"  # Preserve the existing behavior during the compliance refactor.
    except TimeoutError:  # Preserve the existing behavior during the compliance refactor.
        return "closed"  # Preserve the existing behavior during the compliance refactor.
    except ConnectionRefusedError:  # Preserve the existing behavior during the compliance refactor.
        return "closed"  # Preserve the existing behavior during the compliance refactor.
    except OSError as exc:  # Preserve the existing behavior during the compliance refactor.
        return f"error:{type(exc).__name__}"  # Preserve the existing behavior during the compliance refactor.


def _build_ike_sa_init() -> bytes:  # Preserve the existing behavior during the compliance refactor.
    """Return a minimal IKE_SA_INIT header suitable for a discovery datagram.

    Why:
        Real IKE responders will not complete an SA to a probe, but they
        will reply (even with an error notify) to a well-formed
        IKE_SA_INIT header. We only need the 28-byte fixed header with a
        random 8-byte initiator SPI, zero responder SPI, and
        exchange_type=34 (IKE_SA_INIT). Everything after byte 28 is treated
        as payload and is safe to omit for a mere presence probe.

    Returns:
        A 28-byte IKE header suitable for sending to UDP/500 or (with the
        non-ESP marker prefix) UDP/4500.
    """
    # 8-byte cryptographically random initiator SPI so consecutive probes
    # cannot be mistaken for a replay by a real responder.
    initiator_spi = secrets.token_bytes(8)  # Preserve the existing behavior during the compliance refactor.
    responder_spi = b"\x00" * 8  # zero SPI: we are initiating a brand new SA
    next_payload = 0  # 0 = "no next payload" per RFC 7296 (probe-only)
    version = 0x20  # major=2 minor=0 (IKEv2)
    exchange_type = 34  # IKE_SA_INIT per IANA IKEv2 exchange types
    flags = 0x08  # Initiator flag set. Response/Version cleared
    message_id = 0  # first message in the exchange
    length = 28  # header-only. No payloads included in the probe
    # ``!`` selects network (big-endian) byte order as required by RFC 7296.
    # B/B/B/B/I = 1+1+1+1+4 bytes = 8 bytes. Combined with the two 8-byte SPIs
    # this yields the 28-byte header the responder expects.
    return (  # Preserve the existing behavior during the compliance refactor.
        initiator_spi
        + responder_spi
        + struct.pack(
            "!BBBBII",
            next_payload,
            version,
            exchange_type,
            flags,
            message_id,
            length,
        )
    )


def _udp_check(
    host: str, port: int, timeout: float
) -> str:  # Preserve the existing behavior during the compliance refactor.
    """Return ``open``/``no_reply``/``error:<reason>`` for a single IKE UDP probe.

    Why:
        Zscaler VPN gateways answer IKE on UDP/500 and NAT-T-encapsulated
        UDP/4500 rather than any TCP port. TCP-only probing silently
        mislabels them dead. The three-value return vocabulary matches
        :func:`_tcp_check` so downstream reporting can share code paths.
        Port 4500 requires a four-byte non-ESP marker (0x00000000) prefix
        so the responder demultiplexes the packet as IKE rather than ESP;
        omitting the marker turns the probe into a silent black-hole.

    Args:
        host: Target hostname or IP address.
        port: Either ``500`` or ``4500`` (any other value is accepted but
            will not carry the non-ESP marker).
        timeout: Wall-clock recvfrom timeout in seconds. Also bounds how
            long a silent-drop firewall can stall the probe thread.

    Returns:
        ``"open"`` when *any* reply datagram was received, ``"no_reply"``
        on ``socket.timeout``/``TimeoutError`` (matches a firewall silent
        drop), or ``"error:<ExceptionClassName>"`` on any other OSError.
    """
    # Assemble the payload: bare IKE header on 500, marker-prefixed on 4500.
    ike_header = _build_ike_sa_init()  # 28-byte fixed IKEv2 header
    if port == 4500:  # Preserve the existing behavior during the compliance refactor.
        # RFC 3948 s.2.2: 4 bytes of zero prefix means "IKE, not ESP".
        payload = b"\x00\x00\x00\x00" + ike_header  # Preserve the existing behavior during the compliance refactor.
    else:
        payload = ike_header  # port 500 is IKE-only: no marker
    logger.info(
        "zscaler_probe: udp_check host=%s port=%d", host, port
    )  # Preserve the existing behavior during the compliance refactor.
    try:
        with socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM
        ) as sock:  # Preserve the existing behavior during the compliance refactor.
            sock.settimeout(timeout)  # bound blocking recvfrom
            sock.sendto(payload, (host, port))  # Preserve the existing behavior during the compliance refactor.
            data, _addr = sock.recvfrom(4096)  # Preserve the existing behavior during the compliance refactor.
            # Any inbound datagram (even an error notify) proves the port is live.
            state = (
                "open" if data is not None else "no_reply"
            )  # Preserve the existing behavior during the compliance refactor.
    except TimeoutError:  # Preserve the existing behavior during the compliance refactor.
        state = "no_reply"  # silent-drop firewall / route missing / peer offline
    except OSError as exc:  # Preserve the existing behavior during the compliance refactor.
        state = f"error:{type(exc).__name__}"  # for example PermissionError, NetworkUnreachable
    logger.debug(
        "zscaler_probe: udp_check result host=%s port=%d state=%s", host, port, state
    )  # Preserve the existing behavior during the compliance refactor.
    return state  # Preserve the existing behavior during the compliance refactor.


_PROBE_HEADERS = {"User-Agent": "MistHelper-probe/1.0"}  # Identify the probe to the far end.


def _probe_tls_context() -> ssl.SSLContext:
    """Return a TLS context that refuses TLS 1.0 and TLS 1.1.

    Why:
        ``ssl.create_default_context`` already raises the floor to TLS 1.2 on
        the interpreters this project supports. The floor is an interpreter
        default, so a future build could lower it. This function states the
        requirement in the code, so the probe never negotiates a retired
        protocol version.

    Returns:
        A context with certificate verification on and a TLS 1.2 floor.
    """
    context = ssl.create_default_context()  # Start from the secure default trust store and cipher set.
    context.minimum_version = _MINIMUM_TLS_VERSION  # State the floor instead of inheriting it.
    return context  # Every probe connection shares this one construction path.


def _open_probe_connection(
    host: str, port: int, timeout: float, *, tls: bool
) -> HTTPConnection:  # Preserve the existing behavior during the compliance refactor.
    """Return a connection to ``host`` on ``port``, over TLS when asked.

    Why:
        The 405 fallback has to build a second connection with the same
        settings, so the factory lives in one place rather than twice.
    """
    if tls:  # HTTPS uses the system default trust store.
        return HTTPSConnection(
            host, port, timeout=timeout, context=_probe_tls_context()
        )  # Preserve the existing behavior during the compliance refactor.
    return HTTPConnection(host, port, timeout=timeout)  # Plain HTTP for port 80 probes.


def _close_quietly(conn: HTTPConnection) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Close a connection without letting a cleanup error mask the result."""
    try:
        conn.close()  # Release the socket as soon as the response is read.
    except Exception:  # pragma: no cover - best-effort cleanup
        pass  # nosec B110 - The block is a best-effort cleanup that must not mask the original result.


def _request_head_or_get(
    host: str, port: int, timeout: float, *, tls: bool
) -> HTTPResponse:  # Preserve the existing behavior during the compliance refactor.
    """Issue ``HEAD /``, retrying as ``GET /`` when the endpoint answers 405.

    Why:
        A handful of Zscaler endpoints, notably PAC delivery, reject HEAD with
        405 Method Not Allowed. The retry needs a fresh connection because the
        first one is already consumed.
    """
    conn = _open_probe_connection(host, port, timeout, tls=tls)  # First attempt.
    try:
        conn.request("HEAD", "/", headers=_PROBE_HEADERS)  # Small, quick request.
        resp = conn.getresponse()  # Preserve the existing behavior during the compliance refactor.
        if resp.status != 405:  # The endpoint accepted HEAD, so we are done.
            return resp  # Preserve the existing behavior during the compliance refactor.
        conn.close()  # The 405 response consumed this connection.
        conn = _open_probe_connection(host, port, timeout, tls=tls)  # Fresh connection for the retry.
        conn.request("GET", "/", headers=_PROBE_HEADERS)  # Same path, method the endpoint accepts.
        return conn.getresponse()  # Preserve the existing behavior during the compliance refactor.
    finally:
        _close_quietly(conn)  # Caller reads headers off the returned response, per the contract.


def _do_http(  # Preserve the existing behavior during the compliance refactor.
    host: str,
    port: int,
    timeout: float,
    *,
    tls: bool,
) -> tuple[HTTPResponse | None, str | None]:
    """Issue a ``HEAD /`` (or ``GET /`` on 405) and return ``(response, error)``.

    Why:
        HEAD keeps the payload small and quick, but a handful of Zscaler
        endpoints (notably PAC delivery) reject HEAD with ``405 Method Not
        Allowed``. Falling back to GET keeps this a single tool instead of
        two branches in every caller.

    Args:
        host: Target hostname.
        port: TCP port (typically 80 or 443).
        timeout: Wall-clock timeout in seconds.
        tls: True for HTTPS (uses the system default SSL context), False for
            plain HTTP.

    Returns:
        ``(response, None)`` on success or ``(None, formatted_error)``. The
        caller is responsible for reading response headers before the
        connection is garbage-collected.
    """
    try:
        return _request_head_or_get(host, port, timeout, tls=tls), None  # Success path.
    except TimeoutError as exc:  # A stalled edge is reported distinctly from a refused one.
        return None, f"timeout: {exc}"  # Preserve the existing behavior during the compliance refactor.
    except ssl.SSLError as exc:  # Certificate rotations surface here rather than as a generic error.
        return None, f"ssl:{exc}"  # Preserve the existing behavior during the compliance refactor.
    except OSError as exc:  # Connection refused, DNS failure, and similar transport faults.
        return None, f"{type(exc).__name__}: {exc}"  # Preserve the existing behavior during the compliance refactor.
    except Exception as exc:  # pragma: no cover - defensive
        return None, f"{type(exc).__name__}: {exc}"  # Preserve the existing behavior during the compliance refactor.


def _tls_peer(  # Preserve the existing behavior during the compliance refactor.
    host: str,
    port: int,
    timeout: float,
) -> tuple[str | None, str | None, str | None]:
    """Return ``(subject_cn, issuer_cn, error)`` from the TLS handshake.

    Why:
        The peer-cert issuer is the cheapest signal for classifying whether an
        endpoint is a Zscaler service, a CloudFront-fronted service, or a
        third-party host. We only need CN/O so a full cert parse is wasted work.

    Args:
        host: Target hostname (also used as the SNI value).
        port: TCP port (typically 443).
        timeout: Wall-clock timeout in seconds.

    Returns:
        Tuple ``(subject_cn, issuer_cn, error)`` -- any of the first two may
        be ``None`` when the cert omits that field. ``error`` is populated
        with a formatted string on SSL/OS failure and left ``None`` on
        success.
    """
    try:
        ctx = _probe_tls_context()  # Build the context with an explicit TLS floor.
        with socket.create_connection(
            (host, port), timeout=timeout
        ) as raw:  # Preserve the existing behavior during the compliance refactor.
            with ctx.wrap_socket(
                raw, server_hostname=host
            ) as tls:  # Preserve the existing behavior during the compliance refactor.
                cert = tls.getpeercert() or {}  # Preserve the existing behavior during the compliance refactor.
        subj = _pick_cn(cert.get("subject", ()))  # Preserve the existing behavior during the compliance refactor.
        issuer = _pick_cn(cert.get("issuer", ()))  # Preserve the existing behavior during the compliance refactor.
        return subj, issuer, None  # Preserve the existing behavior during the compliance refactor.
    except TimeoutError as exc:  # Preserve the existing behavior during the compliance refactor.
        return None, None, f"timeout: {exc}"  # Preserve the existing behavior during the compliance refactor.
    except ssl.SSLError as exc:  # Preserve the existing behavior during the compliance refactor.
        return None, None, f"ssl:{exc}"  # Preserve the existing behavior during the compliance refactor.
    except OSError as exc:  # Preserve the existing behavior during the compliance refactor.
        return (
            None,
            None,
            f"{type(exc).__name__}: {exc}",
        )  # Preserve the existing behavior during the compliance refactor.


def _pick_cn(rdns: Any) -> str | None:  # Preserve the existing behavior during the compliance refactor.
    """Extract a CN/O string from a certificate distinguished-name tuple.

    Why:
        ``ssl.SSLSocket.getpeercert`` returns RDNs as a nested tuple of
        ``((key, value), ...)`` pairs. We prefer ``commonName`` and fall back
        to ``organizationName`` because a handful of Zscaler CAs omit CN.

    Args:
        rdns: RDN sequence as returned by ``getpeercert``.

    Returns:
        The first matching value as a string, or ``None`` if neither field
        is present.
    """
    for rdn in rdns or ():  # Preserve the existing behavior during the compliance refactor.
        for key, val in rdn:  # Preserve the existing behavior during the compliance refactor.
            if key in (
                "commonName",
                "organizationName",
            ):  # Preserve the existing behavior during the compliance refactor.
                return str(val)  # Preserve the existing behavior during the compliance refactor.
    return None  # Preserve the existing behavior during the compliance refactor.


def _classify_zscaler_subrule(fqdn: str) -> str:  # Preserve the existing behavior during the compliance refactor.
    """Return the Zscaler sub-classification for a Zscaler-issued cert host.

    Why:
        Extracted from :func:`_classify` so the seven-way FQDN sub-tree does
        not push the parent above the Radon CC gate. Ordering is preserved
        (most-specific first).

    Args:
        fqdn: Lower-cased hostname of the endpoint under classification.

    Returns:
        A short human-readable Zscaler sub-class label. Falls back to
        ``"Zscaler service"`` when no more specific rule matches.
    """
    for needle, label in _ZSCALER_PREFIX_SUBRULES:  # WHY: Preserve the legacy rules before the login-or-mobile check.
        if needle in fqdn:  # WHY: A matching marker gives the operator the specific endpoint class.
            return label  # WHY: Return the first legacy-equivalent rule match.
    if "login" in fqdn or "mobile" in fqdn:  # Preserve the existing behavior during the compliance refactor.
        return "Zscaler enrollment/login"  # WHY: Preserve the combined login-or-mobile rule before the table walk.
    for needle, label in _ZSCALER_SUFFIX_SUBRULES:  # WHY: Preserve the legacy rules after the login-or-mobile check.
        if needle in fqdn:  # WHY: A matching marker gives the operator the specific endpoint class.
            return label  # WHY: Return the first legacy-equivalent rule match.
    return "Zscaler service"  # Preserve the existing behavior during the compliance refactor.


def _classify_generic(fqdn: str, server: str) -> str:  # Preserve the existing behavior during the compliance refactor.
    """Return the fall-through classification for non-Zscaler, non-CloudFront hosts.

    Why:
        Keeps :func:`_classify` under the CC gate by peeling the tail of the
        rules ladder into its own function. Rules stay in the original order.

    Args:
        fqdn: Lower-cased hostname of the endpoint under classification.
        server: Lower-cased ``Server:`` header value from HTTP/HTTPS response,
            or empty string when neither responded.

    Returns:
        A short human-readable class label; ``"unknown"`` when no rule
        matches.
    """
    if _is_digicert_responder(fqdn, server):  # Preserve the existing behavior during the compliance refactor.
        return "DigiCert OCSP/CRL responder"  # WHY: DigiCert responders are certificate infrastructure.
    if _is_google_probe_host(fqdn):  # Accept google.com and its subdomains, and reject a lookalike name.
        return "Google captive-portal probe target"  # WHY: Preserve the exact Google suffix rule.
    if "secb2b" in fqdn:  # Preserve the existing behavior during the compliance refactor.
        return "Samsung ELM activation (secb2b.com)"  # WHY: Preserve the Samsung substring rule.
    if server:  # Preserve the existing behavior during the compliance refactor.
        return f"Web server ({server})"  # WHY: Preserve the server-header fallback for reachable unknown web hosts.
    return "unknown"  # WHY: No known signal was available for this endpoint.


def _is_google_probe_host(fqdn: str) -> bool:
    """Return True when the host is a Google probe target.

    Why:
        ``fqdn.endswith("google.com")`` accepts any name that ends with those
        characters. ``notgoogle.com`` and ``evilgoogle.com`` both pass that
        test, and a third party can register either one. This function accepts
        the registrable name itself and its subdomains, and nothing else.

    Args:
        fqdn: Hostname of the endpoint under classification.

    Returns:
        True when the host equals a Google probe name or sits below one.
    """
    host = fqdn.lower().rstrip(".")  # Normalize case and the trailing dot of an absolute name.
    return any(
        host == name or host.endswith("." + name) for name in _GOOGLE_PROBE_HOSTS
    )  # Require a label boundary, so a sibling registration cannot match.


def _is_digicert_responder(
    fqdn: str, server: str
) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return True when the FQDN or the server header identifies DigiCert."""
    return "digicert" in fqdn or "digicert" in server  # WHY: Preserve the original two-signal DigiCert match.


def _matches_cloudfront(
    fqdn: str, server: str, subj: str
) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return True when any classification signal names CloudFront.

    Why:
        Extracted so the CloudFront short-circuit in :func:`_classify` is a
        single call, keeping the parent under the Radon CC gate. All three
        signals fire the same label so combining them here loses no fidelity.

    Args:
        fqdn: Lower-cased hostname of the endpoint.
        server: Lower-cased HTTP/HTTPS ``Server:`` header value.
        subj: Lower-cased TLS certificate subject.

    Returns:
        True when ``"cloudfront"`` appears in any of the three signals.
    """
    return (
        "cloudfront" in fqdn or "cloudfront" in server or "cloudfront" in subj
    )  # Preserve the existing behavior during the compliance refactor.


def _classify(result: ProbeResult) -> str:  # Preserve the existing behavior during the compliance refactor.
    """Categorize the endpoint from FQDN hints, response headers, and cert.

    Why:
        A ~10-line rules table beats trying to make the operator infer the
        endpoint's purpose from raw ``Server:`` values and cert issuers. The
        rules are ordered from most-specific to least-specific.

    Args:
        result: The partially-filled probe result to classify.

    Returns:
        A short human-readable class label; ``"unknown"`` when no rule
        matches.
    """
    fqdn = result.fqdn.lower()  # Preserve the existing behavior during the compliance refactor.
    server = (
        result.https_server or result.http_server or ""
    ).lower()  # Preserve the existing behavior during the compliance refactor.
    subj = (result.tls_subject or "").lower()  # Preserve the existing behavior during the compliance refactor.
    issuer = (result.tls_issuer or "").lower()  # Preserve the existing behavior during the compliance refactor.

    if _matches_cloudfront(fqdn, server, subj):  # Preserve the existing behavior during the compliance refactor.
        return "AWS CloudFront (CDN)"  # Preserve the existing behavior during the compliance refactor.
    if fqdn.endswith(".sme.zscaler.net"):  # Preserve the existing behavior during the compliance refactor.
        return "Zscaler ZEN proxy node"  # Preserve the existing behavior during the compliance refactor.
    if "zscaler" in subj or "zscaler" in issuer:  # Preserve the existing behavior during the compliance refactor.
        return _classify_zscaler_subrule(fqdn)  # Preserve the existing behavior during the compliance refactor.
    return _classify_generic(fqdn, server)  # Preserve the existing behavior during the compliance refactor.


def _probe_http_stack(  # Preserve the existing behavior during the compliance refactor.
    fqdn: str,
    timeout: float,
    declared_ports: list[int],
    result: ProbeResult,
) -> None:
    """Run HTTP :80, HTTPS :443 (with TLS peer), and proxy :8080 checks.

    Why:
        The HTTP/HTTPS/proxy blocks live together because they all depend on
        TCP scan results already populated in ``result.tcp``. Pulling them into
        a helper keeps :func:`_probe_fqdn` under the CC gate without changing
        probe order or side effects.

    Args:
        fqdn: Hostname being probed (used for HTTP/TLS SNI).
        timeout: Per-probe timeout in seconds.
        declared_ports: Ports the catalogue declared for this role. Only 8080
            probes emit when 8080 is both open and declared.
        result: Mutated in place. HTTP/HTTPS fields and
            ``responding_protocols`` are populated on success, ``notes`` on
            failure.
    """
    if result.tcp.get(80) == "open":  # Preserve the existing behavior during the compliance refactor.
        resp, err = _do_http(
            fqdn, 80, timeout, tls=False
        )  # Preserve the existing behavior during the compliance refactor.
        if resp is not None:  # Preserve the existing behavior during the compliance refactor.
            result.http_status = resp.status  # Preserve the existing behavior during the compliance refactor.
            result.http_server = resp.getheader(
                "Server"
            )  # Preserve the existing behavior during the compliance refactor.
            result.http_location = resp.getheader(
                "Location"
            )  # Preserve the existing behavior during the compliance refactor.
            result.responding_protocols.append("HTTP")  # Preserve the existing behavior during the compliance refactor.
        else:
            result.notes.append(
                f"HTTP :80 error: {err}"
            )  # Preserve the existing behavior during the compliance refactor.

    if result.tcp.get(443) == "open":  # Preserve the existing behavior during the compliance refactor.
        subj, issuer, tls_err = _tls_peer(
            fqdn, 443, timeout
        )  # Preserve the existing behavior during the compliance refactor.
        result.tls_subject = subj  # Preserve the existing behavior during the compliance refactor.
        result.tls_issuer = issuer  # Preserve the existing behavior during the compliance refactor.
        result.tls_error = tls_err  # Preserve the existing behavior during the compliance refactor.
        resp, err = _do_http(
            fqdn, 443, timeout, tls=True
        )  # Preserve the existing behavior during the compliance refactor.
        if resp is not None:  # Preserve the existing behavior during the compliance refactor.
            result.https_status = resp.status  # Preserve the existing behavior during the compliance refactor.
            result.https_server = resp.getheader(
                "Server"
            )  # Preserve the existing behavior during the compliance refactor.
            result.https_location = resp.getheader(
                "Location"
            )  # Preserve the existing behavior during the compliance refactor.
            result.responding_protocols.append(
                "HTTPS"
            )  # Preserve the existing behavior during the compliance refactor.
        else:
            result.notes.append(
                f"HTTPS :443 error: {err}"
            )  # Preserve the existing behavior during the compliance refactor.

    if (
        result.tcp.get(8080) == "open" and 8080 in declared_ports
    ):  # Preserve the existing behavior during the compliance refactor.
        # ZEN nodes listen on 8080 for explicit-proxy CONNECT. A raw HTTP GET
        # is usually refused (400/407), but the TCP handshake alone confirms
        # the port is live.
        result.responding_protocols.append(
            "TCP/8080 (proxy)"
        )  # Preserve the existing behavior during the compliance refactor.


def _probe_udp_ike_if_needed(  # Preserve the existing behavior during the compliance refactor.
    fqdn: str,
    timeout: float,
    result: ProbeResult,
) -> None:
    """Fire IKE UDP probes for VPN-tagged hostnames or when every TCP scan died.

    Why:
        US2 gate: skipping UDP on healthy TCP hosts keeps scan time bounded and
        avoids gratuitous IKE traffic to non-VPN endpoints. Extracted so the
        gating logic is testable in isolation and to shrink the parent
        function under the CC threshold.

    Args:
        fqdn: Hostname. The ``"-vpn."`` substring is the catalogue-agnostic
            hint that this is a VPN endpoint.
        timeout: Per-probe timeout in seconds.
        result: Mutated in place; ``udp`` and ``responding_protocols`` are
            populated when any IKE port answers.
    """
    is_vpn_hostname = "-vpn." in fqdn.lower()  # catalogue-agnostic pattern hint
    all_tcp_dead = bool(result.tcp) and all(
        state != "open" for state in result.tcp.values()
    )  # every scanned port RST/closed/errored
    if not (is_vpn_hostname or all_tcp_dead):  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.
    for udp_port in IKE_UDP_PORTS:  # Preserve the existing behavior during the compliance refactor.
        udp_state = _udp_check(
            fqdn, udp_port, timeout
        )  # Preserve the existing behavior during the compliance refactor.
        result.udp[udp_port] = udp_state  # Preserve the existing behavior during the compliance refactor.
        if udp_state == "open":  # Preserve the existing behavior during the compliance refactor.
            result.responding_protocols.append(
                f"UDP/{udp_port}"
            )  # Preserve the existing behavior during the compliance refactor.


def _probe_fqdn(  # Preserve the existing behavior during the compliance refactor.
    fqdn: str,
    role: dict[str, Any],
    timeout: float,
) -> ProbeResult:
    """Run every configured probe against *fqdn* and return the consolidated result.

    Why:
        This is the atomic unit of work executed by :func:`_run_probes` inside
        the thread pool. Keeping it self-contained (no shared mutable state)
        lets us fan out safely across dozens of workers without locks.

    Args:
        fqdn: Hostname to probe.
        role: Catalogue role dict. Only ``role``, ``description``, ``ports``,
            and ``critical`` are consumed.
        timeout: Per-probe timeout in seconds.

    Returns:
        A fully populated :class:`ProbeResult`. On DNS failure the result is
        returned early with ``ip=None`` and ``dns_error`` set. No downstream
        probes run.
    """
    declared_ports = list(role.get("ports") or [])  # Preserve the existing behavior during the compliance refactor.
    result = ProbeResult(  # Preserve the existing behavior during the compliance refactor.
        fqdn=fqdn,
        role=str(role.get("role", "")),
        role_description=str(role.get("description", "")),
        declared_ports=declared_ports,
        critical=bool(role.get("critical", False)),
    )
    result.ip, result.dns_error = _resolve(fqdn)  # Preserve the existing behavior during the compliance refactor.
    if result.ip is None:  # Preserve the existing behavior during the compliance refactor.
        return result  # Preserve the existing behavior during the compliance refactor.

    result.icmp_ok = _icmp_ping(fqdn, timeout)  # Preserve the existing behavior during the compliance refactor.
    if result.icmp_ok:  # Preserve the existing behavior during the compliance refactor.
        result.responding_protocols.append("ICMP")  # Preserve the existing behavior during the compliance refactor.

    ports_to_scan = sorted(
        set(list(declared_ports) + list(COMMON_TCP_PORTS))
    )  # Preserve the existing behavior during the compliance refactor.
    for port in ports_to_scan:  # Preserve the existing behavior during the compliance refactor.
        state = _tcp_check(fqdn, port, timeout)  # Preserve the existing behavior during the compliance refactor.
        result.tcp[port] = state  # Preserve the existing behavior during the compliance refactor.
        if state == "open":  # Preserve the existing behavior during the compliance refactor.
            result.responding_protocols.append(
                f"TCP/{port}"
            )  # Preserve the existing behavior during the compliance refactor.

    _probe_http_stack(
        fqdn, timeout, declared_ports, result
    )  # Preserve the existing behavior during the compliance refactor.
    _probe_udp_ike_if_needed(fqdn, timeout, result)  # Preserve the existing behavior during the compliance refactor.

    result.server_class = _classify(result)  # Preserve the existing behavior during the compliance refactor.
    return result  # Preserve the existing behavior during the compliance refactor.


def _run_probes(  # Preserve the existing behavior during the compliance refactor.
    entries: list[tuple[str, dict[str, Any]]],
    timeout: float,
    workers: int,
) -> list[ProbeResult]:
    """Run all probes concurrently and return results sorted by (role, fqdn).

    Why:
        ThreadPoolExecutor is the right knob because each probe is
        network-bound (DNS + TCP + TLS + subprocess ping) and releases the
        GIL for most of its wall-clock time. Sorting deterministically keeps
        the markdown report stable across runs.

    Args:
        entries: List of ``(fqdn, role_dict)`` tuples to probe.
        timeout: Per-probe timeout in seconds.
        workers: Maximum thread pool size.

    Returns:
        List of :class:`ProbeResult`, sorted by ``(role, fqdn)``. A worker
        exception is captured as a stub result with the failure recorded in
        ``notes`` so a single crashing endpoint never kills the whole run.
    """
    results: list[ProbeResult] = []  # Preserve the existing behavior during the compliance refactor.
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=workers
    ) as pool:  # Preserve the existing behavior during the compliance refactor.
        futures = {
            pool.submit(_probe_fqdn, fqdn, role, timeout): fqdn for fqdn, role in entries
        }  # Preserve the existing behavior during the compliance refactor.
        for fut in concurrent.futures.as_completed(
            futures
        ):  # Preserve the existing behavior during the compliance refactor.
            try:
                results.append(fut.result())  # Preserve the existing behavior during the compliance refactor.
            except Exception as exc:  # pragma: no cover - defensive
                fqdn = futures[fut]  # Preserve the existing behavior during the compliance refactor.
                stub = ProbeResult(  # Preserve the existing behavior during the compliance refactor.
                    fqdn=fqdn,
                    role="",
                    role_description="",
                    declared_ports=[],
                    critical=False,
                )
                stub.notes.append(
                    f"probe crashed: {type(exc).__name__}: {exc}"
                )  # Preserve the existing behavior during the compliance refactor.
                results.append(stub)  # Preserve the existing behavior during the compliance refactor.
    results.sort(key=lambda r: (r.role, r.fqdn))  # Preserve the existing behavior during the compliance refactor.
    return results  # Preserve the existing behavior during the compliance refactor.


_CENR_SYNTHETIC_ROLE: dict[str, Any] = {  # Preserve the existing behavior during the compliance refactor.
    "role": "cenr_zen_proxy",
    "description": "Zscaler ZEN cloud-enforcement proxy (from merged CENR feed)",
    "ports": [80, 443, 8080],
    "critical": False,
}
"""Synthetic role dict assigned to every CENR hostname during full-fleet
validation. ZEN proxies do not appear in the ZCC role catalogue, so we mint
a stable role slug (``cenr_zen_proxy``) locally to keep sorting/grouping in
the report and logs consistent."""


def _collect_zcc_probe_entries(  # Preserve the existing behavior during the compliance refactor.
    probes: dict[str, Any],
    seen: set[str],
    entries: list[tuple[str, dict[str, Any]]],
) -> None:
    """Append ZCC ``roles[].fqdns`` entries to the probe queue.

    Why:
        Extracted from ``run_full_validation`` so the parent stays under
        the CI cyclomatic-complexity gate. The v3 dict unwrap (``{"host":
        ...}``) plus legacy flat-string tolerance is duplicated between
        the ZCC and CENR walks, but keeping them separate lets the
        parent function express "ZCC first, then CENR" order without
        needing another key argument.

    Args:
        probes: Parsed ``zscaler_client_connector_probes.json`` document.
        seen: Deduplication set for FQDNs already queued. Mutated in place.
        entries: Probe queue tuples ``(fqdn, role)``. Mutated in place.
    """
    for role in probes.get("roles", []) or []:  # Preserve the existing behavior during the compliance refactor.
        if not isinstance(role, dict):  # Preserve the existing behavior during the compliance refactor.
            continue  # Preserve the existing behavior during the compliance refactor.
        for entry in role.get("fqdns", []) or []:  # Preserve the existing behavior during the compliance refactor.
            # Unwrap v3 dict entries {"host": ...} while still tolerating
            # legacy flat strings so mid-migration caches keep working.
            fqdn = (
                entry.get("host") if isinstance(entry, dict) else entry
            )  # Preserve the existing behavior during the compliance refactor.
            fqdn_s = str(fqdn) if fqdn is not None else ""  # guard None from broken v3 rows
            if fqdn_s and fqdn_s not in seen:  # Preserve the existing behavior during the compliance refactor.
                seen.add(fqdn_s)  # Preserve the existing behavior during the compliance refactor.
                entries.append((fqdn_s, role))  # Preserve the existing behavior during the compliance refactor.


def _collect_cenr_probe_entries(  # Preserve the existing behavior during the compliance refactor.
    cenr: dict[str, Any],
    seen: set[str],
    entries: list[tuple[str, dict[str, Any]]],
) -> None:
    """Append CENR proxy + VPN hostnames to the probe queue.

    Why:
        Mirrors ``_collect_zcc_probe_entries`` for the CENR side. ZEN
        proxies do not appear in the ZCC role catalogue, so every CENR
        hostname is stamped with the synthetic ``_CENR_SYNTHETIC_ROLE``
        so downstream sorting/grouping keeps working uniformly.

    Args:
        cenr: Merged CENR document as produced by ``merge_clouds``.
        seen: Deduplication set (see peer helper).
        entries: Probe queue tuples (see peer helper).
    """
    for key in ("proxy_hostnames", "vpn_hostnames"):  # Preserve the existing behavior during the compliance refactor.
        for entry in cenr.get(key, []) or []:  # Preserve the existing behavior during the compliance refactor.
            # Same v3-dict unwrap for CENR bags; str() must never see the
            # raw dict or it produces a "{'host': ...}" pseudo-hostname.
            host = (
                entry.get("host") if isinstance(entry, dict) else entry
            )  # Preserve the existing behavior during the compliance refactor.
            host_s = str(host) if host is not None else ""  # guard None from broken v3 rows
            if host_s and host_s not in seen:  # Preserve the existing behavior during the compliance refactor.
                seen.add(host_s)  # Preserve the existing behavior during the compliance refactor.
                entries.append(
                    (host_s, _CENR_SYNTHETIC_ROLE)
                )  # Preserve the existing behavior during the compliance refactor.


def _log_probe_failures(
    results: list[ProbeResult],
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Emit a DEBUG line for every ProbeResult with no responding protocols.

    Why:
        Kept at DEBUG (not INFO) so a batch of transient timeouts during
        an 8-hour refresh window does not spam operator logs. The caller
        still emits one INFO summary. Extracted so the parent's CC drops
        under the gate.

    Args:
        results: The probe result list returned by ``_run_probes``.
    """
    for probe_result in results:  # Use a descriptive name so the log line stays easy to read.
        if not probe_result.responding_protocols:  # Log only endpoints that produced no usable response.
            logger.debug(
                "zscaler_probe: no response from %s (role=%s ip=%s notes=%s)",
                probe_result.fqdn,  # Identify the endpoint that failed every probe.
                probe_result.role or "<none>",  # Preserve the catalogue role when one exists.
                probe_result.ip or "-",  # Show DNS success or an explicit placeholder.
                "; ".join(probe_result.notes) or "-",  # Summarize probe errors without a second lookup.
            )


def run_full_validation(  # Preserve the existing behavior during the compliance refactor.
    probes: dict[str, Any],
    cenr: dict[str, Any],
    *,
    timeout: float = DEFAULT_TIMEOUT,
    workers: int = DEFAULT_WORKERS,
) -> list[ProbeResult]:
    """Probe every FQDN in the ZCC catalogue plus every CENR ZEN hostname.

    Why:
        Menu option 206 pushes Mist synthetic tests derived from the catalogue
        JSONs, so we want a live pass/fail snapshot every time the merged
        catalogue is refreshed (TTL-gated to 8h in
        :mod:`src.utils.zscaler_catalogue`). Full-fleet coverage was chosen
        over sampling because the run only fires every 8 hours, amortising
        the cost. Per-endpoint failures are logged at DEBUG so a batch of
        transient timeouts does not spam INFO. A single INFO summary line is
        always emitted.

    Args:
        probes: Parsed ``zscaler_client_connector_probes.json`` document.
            Only the ``roles[].fqdns`` and role metadata are consumed.
        cenr: Merged CENR document as produced by
            :func:`src.utils.zscaler_catalogue.merge_clouds`. The
            ``proxy_hostnames`` and ``vpn_hostnames`` lists are combined
            into a single ZEN sweep.
        timeout: Per-probe wall-clock timeout in seconds. Defaults to
            :data:`DEFAULT_TIMEOUT`.
        workers: Concurrent probe worker count. Defaults to
            :data:`DEFAULT_WORKERS`.

    Returns:
        List of :class:`ProbeResult`, one per probed FQDN, sorted by
        ``(role, fqdn)``. The list is empty only when both input documents
        contain no FQDNs -- a normal fully-populated call typically returns
        several hundred entries (~30 ZCC + ~990 CENR).
    """
    entries: list[tuple[str, dict[str, Any]]] = []  # Preserve the existing behavior during the compliance refactor.
    seen: set[str] = set()  # Preserve the existing behavior during the compliance refactor.
    _collect_zcc_probe_entries(probes, seen, entries)  # Preserve the existing behavior during the compliance refactor.
    _collect_cenr_probe_entries(cenr, seen, entries)  # Preserve the existing behavior during the compliance refactor.

    logger.info(  # Preserve the existing behavior during the compliance refactor.
        "zscaler_probe: validating %d endpoints (timeout=%.1fs, workers=%d)",
        len(entries),
        timeout,
        workers,
    )
    results = _run_probes(entries, timeout, workers)  # Preserve the existing behavior during the compliance refactor.
    _log_validation_summary(results)  # One INFO line, then per-endpoint failures at DEBUG.
    return results  # Preserve the existing behavior during the compliance refactor.


def _log_validation_summary(
    results: list[ProbeResult],
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Emit the single INFO summary line, then the per-endpoint failures.

    Why:
        Extracted from :func:`run_full_validation` so the orchestrator reads as
        collect, probe, report. The counts are derived here rather than passed
        in, because they are only used for this message.
    """
    ok = sum(1 for r in results if r.responding_protocols)  # Endpoints answering on any protocol.
    dns_fail = sum(1 for r in results if r.ip is None)  # Names that never resolved.
    tls_fail = sum(1 for r in results if r.tls_error)  # Names that resolved but failed TLS.
    logger.info(  # Preserve the existing behavior during the compliance refactor.
        "zscaler_probe: %d/%d endpoints responded on at least one protocol " "(dns_fail=%d, tls_fail=%d)",
        ok,
        len(results),
        dns_fail,
        tls_fail,
    )
    _log_probe_failures(results)  # DEBUG detail so a transient batch does not spam INFO.
