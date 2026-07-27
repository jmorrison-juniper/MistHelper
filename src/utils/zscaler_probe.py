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

from __future__ import annotations

import concurrent.futures
import logging
import platform
import secrets
import socket
import ssl
import struct
import subprocess
from dataclasses import dataclass, field
from http.client import HTTPConnection, HTTPResponse, HTTPSConnection
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 3.0
"""Per-probe wall-clock timeout in seconds (DNS/ICMP/TCP/HTTP/TLS)."""

DEFAULT_WORKERS = 16
"""Default ThreadPoolExecutor size for parallel probes."""

COMMON_TCP_PORTS: tuple[int, ...] = (80, 443, 8080)
"""Ports referenced anywhere in the ZCC catalogue; always scanned in addition
to a role's declared ports so we can spot endpoints answering off-doc."""

IKE_UDP_PORTS: tuple[int, int] = (500, 4500)
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


@dataclass
class ProbeResult:
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
        dns_error (str | None): Formatted DNS failure text; only populated on
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
        tls_error (str | None): Formatted TLS error text; only populated on
            handshake failure.
        responding_protocols (list[str]): Compact list of protocols we
            confirmed live (for example ``["ICMP", "TCP/443", "HTTPS"]``); used by
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

    fqdn: str
    role: str
    role_description: str
    declared_ports: list[int]
    critical: bool
    ip: str | None = None
    dns_error: str | None = None
    icmp_ok: bool = False
    tcp: dict[int, str] = field(default_factory=dict)
    http_status: int | None = None
    http_server: str | None = None
    http_location: str | None = None
    https_status: int | None = None
    https_server: str | None = None
    https_location: str | None = None
    tls_subject: str | None = None
    tls_issuer: str | None = None
    tls_error: str | None = None
    responding_protocols: list[str] = field(default_factory=list)
    server_class: str = "unknown"
    notes: list[str] = field(default_factory=list)
    udp: dict[int, str] = field(default_factory=dict)


def _resolve(fqdn: str) -> tuple[str | None, str | None]:
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
        return socket.gethostbyname(fqdn), None
    except OSError as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _icmp_ping(host: str, timeout: float) -> bool:
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
    is_win = platform.system().lower().startswith("win")
    count_flag = "-n" if is_win else "-c"
    timeout_flag = "-w" if is_win else "-W"
    timeout_val = str(int(timeout * 1000)) if is_win else str(int(timeout))
    cmd = ["ping", count_flag, "1", timeout_flag, timeout_val, host]
    try:
        completed = subprocess.run(  # noqa: S603 - args are validated above
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 2.0,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return completed.returncode == 0


def _tcp_check(host: str, port: int, timeout: float) -> str:
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
        with socket.create_connection((host, port), timeout=timeout):
            return "open"
    except TimeoutError:
        return "closed"
    except ConnectionRefusedError:
        return "closed"
    except OSError as exc:
        return f"error:{type(exc).__name__}"


def _build_ike_sa_init() -> bytes:
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
    initiator_spi = secrets.token_bytes(8)
    responder_spi = b"\x00" * 8  # zero SPI: we are initiating a brand new SA
    next_payload = 0  # 0 = "no next payload" per RFC 7296 (probe-only)
    version = 0x20  # major=2 minor=0 (IKEv2)
    exchange_type = 34  # IKE_SA_INIT per IANA IKEv2 exchange types
    flags = 0x08  # Initiator flag set; Response/Version cleared
    message_id = 0  # first message in the exchange
    length = 28  # header-only; no payloads included in the probe
    # ``!`` selects network (big-endian) byte order as required by RFC 7296.
    # B/B/B/B/I = 1+1+1+1+4 bytes = 8 bytes; combined with the two 8-byte SPIs
    # this yields the 28-byte header the responder expects.
    return (
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


def _udp_check(host: str, port: int, timeout: float) -> str:
    """Return ``open``/``no_reply``/``error:<reason>`` for a single IKE UDP probe.

    Why:
        Zscaler VPN gateways answer IKE on UDP/500 and NAT-T-encapsulated
        UDP/4500 rather than any TCP port; TCP-only probing silently
        mislabels them dead. The three-value return vocabulary matches
        :func:`_tcp_check` so downstream reporting can share code paths.
        Port 4500 requires a four-byte non-ESP marker (0x00000000) prefix
        so the responder demultiplexes the packet as IKE rather than ESP;
        omitting the marker turns the probe into a silent black-hole.

    Args:
        host: Target hostname or IP address.
        port: Either ``500`` or ``4500`` (any other value is accepted but
            will not carry the non-ESP marker).
        timeout: Wall-clock recvfrom timeout in seconds; also bounds how
            long a silent-drop firewall can stall the probe thread.

    Returns:
        ``"open"`` when *any* reply datagram was received, ``"no_reply"``
        on ``socket.timeout``/``TimeoutError`` (matches a firewall silent
        drop), or ``"error:<ExceptionClassName>"`` on any other OSError.
    """
    # Assemble the payload: bare IKE header on 500, marker-prefixed on 4500.
    ike_header = _build_ike_sa_init()  # 28-byte fixed IKEv2 header
    if port == 4500:
        # RFC 3948 s.2.2: 4 bytes of zero prefix means "IKE, not ESP".
        payload = b"\x00\x00\x00\x00" + ike_header
    else:
        payload = ike_header  # port 500 is IKE-only: no marker
    logger.info("zscaler_probe: udp_check host=%s port=%d", host, port)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)  # bound blocking recvfrom
            sock.sendto(payload, (host, port))
            data, _addr = sock.recvfrom(4096)
            # Any inbound datagram (even an error notify) proves the port is live.
            state = "open" if data is not None else "no_reply"
    except TimeoutError:
        state = "no_reply"  # silent-drop firewall / route missing / peer offline
    except OSError as exc:
        state = f"error:{type(exc).__name__}"  # for example PermissionError, NetworkUnreachable
    logger.debug("zscaler_probe: udp_check result host=%s port=%d state=%s", host, port, state)
    return state


def _do_http(
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
        if tls:
            ctx = ssl.create_default_context()
            conn: HTTPConnection = HTTPSConnection(
                host,
                port,
                timeout=timeout,
                context=ctx,
            )
        else:
            conn = HTTPConnection(host, port, timeout=timeout)
        try:
            conn.request("HEAD", "/", headers={"User-Agent": "MistHelper-probe/1.0"})
            resp = conn.getresponse()
            if resp.status == 405:  # Method Not Allowed -- retry with GET.
                conn.close()
                if tls:
                    conn = HTTPSConnection(
                        host,
                        port,
                        timeout=timeout,
                        context=ssl.create_default_context(),
                    )
                else:
                    conn = HTTPConnection(host, port, timeout=timeout)
                conn.request("GET", "/", headers={"User-Agent": "MistHelper-probe/1.0"})
                resp = conn.getresponse()
            return resp, None
        finally:
            try:
                conn.close()
            except Exception:  # pragma: no cover - best-effort cleanup
                pass
    except TimeoutError as exc:
        return None, f"timeout: {exc}"
    except ssl.SSLError as exc:
        return None, f"ssl:{exc}"
    except OSError as exc:
        return None, f"{type(exc).__name__}: {exc}"
    except Exception as exc:  # pragma: no cover - defensive
        return None, f"{type(exc).__name__}: {exc}"


def _tls_peer(
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
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as raw:
            with ctx.wrap_socket(raw, server_hostname=host) as tls:
                cert = tls.getpeercert() or {}
        subj = _pick_cn(cert.get("subject", ()))
        issuer = _pick_cn(cert.get("issuer", ()))
        return subj, issuer, None
    except TimeoutError as exc:
        return None, None, f"timeout: {exc}"
    except ssl.SSLError as exc:
        return None, None, f"ssl:{exc}"
    except OSError as exc:
        return None, None, f"{type(exc).__name__}: {exc}"


def _pick_cn(rdns: Any) -> str | None:
    """Extract a CN/O string from a certificate distinguished-name tuple.

    Why:
        ``ssl.SSLSocket.getpeercert`` returns RDNs as a nested tuple of
        ``((key, value), ...)`` pairs; we prefer ``commonName`` and fall back
        to ``organizationName`` because a handful of Zscaler CAs omit CN.

    Args:
        rdns: RDN sequence as returned by ``getpeercert``.

    Returns:
        The first matching value as a string, or ``None`` if neither field
        is present.
    """
    for rdn in rdns or ():
        for key, val in rdn:
            if key in ("commonName", "organizationName"):
                return str(val)
    return None


def _classify_zscaler_subrule(fqdn: str) -> str:
    """Return the Zscaler sub-classification for a Zscaler-issued cert host.

    Why:
        Extracted from :func:`_classify` so the seven-way FQDN sub-tree does
        not push the parent above the Radon CC gate. Ordering is preserved
        (most-specific first).

    Args:
        fqdn: Lower-cased hostname of the endpoint under classification.

    Returns:
        A short human-readable Zscaler sub-class label; falls back to
        ``"Zscaler service"`` when no more specific rule matches.
    """
    if "pac" in fqdn:
        return "Zscaler PAC delivery"
    if "gateway" in fqdn:
        return "Zscaler captive-portal gateway"
    if "mobilesupport" in fqdn:
        return "Zscaler support endpoint"
    if "login" in fqdn or "mobile" in fqdn:
        return "Zscaler enrollment/login"
    if "healthapp" in fqdn:
        return "Zscaler health-probe endpoint"
    if "ecdn" in fqdn:
        return "Zscaler ECDN (update channel)"
    if "private.zscaler" in fqdn:
        return "Zscaler private/internal"
    return "Zscaler service"


def _classify_generic(fqdn: str, server: str) -> str:
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
    if "digicert" in fqdn or "digicert" in server:
        return "DigiCert OCSP/CRL responder"
    if fqdn.endswith("google.com"):
        return "Google captive-portal probe target"
    if "secb2b" in fqdn:
        return "Samsung ELM activation (secb2b.com)"
    if server:
        return f"Web server ({server})"
    return "unknown"


def _matches_cloudfront(fqdn: str, server: str, subj: str) -> bool:
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
    return "cloudfront" in fqdn or "cloudfront" in server or "cloudfront" in subj


def _classify(result: ProbeResult) -> str:
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
    fqdn = result.fqdn.lower()
    server = (result.https_server or result.http_server or "").lower()
    subj = (result.tls_subject or "").lower()
    issuer = (result.tls_issuer or "").lower()

    if _matches_cloudfront(fqdn, server, subj):
        return "AWS CloudFront (CDN)"
    if fqdn.endswith(".sme.zscaler.net"):
        return "Zscaler ZEN proxy node"
    if "zscaler" in subj or "zscaler" in issuer:
        return _classify_zscaler_subrule(fqdn)
    return _classify_generic(fqdn, server)


def _probe_http_stack(
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
        result: Mutated in place; HTTP/HTTPS fields and
            ``responding_protocols`` are populated on success, ``notes`` on
            failure.
    """
    if result.tcp.get(80) == "open":
        resp, err = _do_http(fqdn, 80, timeout, tls=False)
        if resp is not None:
            result.http_status = resp.status
            result.http_server = resp.getheader("Server")
            result.http_location = resp.getheader("Location")
            result.responding_protocols.append("HTTP")
        else:
            result.notes.append(f"HTTP :80 error: {err}")

    if result.tcp.get(443) == "open":
        subj, issuer, tls_err = _tls_peer(fqdn, 443, timeout)
        result.tls_subject = subj
        result.tls_issuer = issuer
        result.tls_error = tls_err
        resp, err = _do_http(fqdn, 443, timeout, tls=True)
        if resp is not None:
            result.https_status = resp.status
            result.https_server = resp.getheader("Server")
            result.https_location = resp.getheader("Location")
            result.responding_protocols.append("HTTPS")
        else:
            result.notes.append(f"HTTPS :443 error: {err}")

    if result.tcp.get(8080) == "open" and 8080 in declared_ports:
        # ZEN nodes listen on 8080 for explicit-proxy CONNECT; a raw HTTP GET
        # is usually refused (400/407), but the TCP handshake alone confirms
        # the port is live.
        result.responding_protocols.append("TCP/8080 (proxy)")


def _probe_udp_ike_if_needed(
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
        fqdn: Hostname; the ``"-vpn."`` substring is the catalogue-agnostic
            hint that this is a VPN endpoint.
        timeout: Per-probe timeout in seconds.
        result: Mutated in place; ``udp`` and ``responding_protocols`` are
            populated when any IKE port answers.
    """
    is_vpn_hostname = "-vpn." in fqdn.lower()  # catalogue-agnostic pattern hint
    all_tcp_dead = bool(result.tcp) and all(
        state != "open" for state in result.tcp.values()
    )  # every scanned port RST/closed/errored
    if not (is_vpn_hostname or all_tcp_dead):
        return
    for udp_port in IKE_UDP_PORTS:
        udp_state = _udp_check(fqdn, udp_port, timeout)
        result.udp[udp_port] = udp_state
        if udp_state == "open":
            result.responding_protocols.append(f"UDP/{udp_port}")


def _probe_fqdn(
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
        role: Catalogue role dict; only ``role``, ``description``, ``ports``,
            and ``critical`` are consumed.
        timeout: Per-probe timeout in seconds.

    Returns:
        A fully populated :class:`ProbeResult`. On DNS failure the result is
        returned early with ``ip=None`` and ``dns_error`` set; no downstream
        probes run.
    """
    declared_ports = list(role.get("ports") or [])
    result = ProbeResult(
        fqdn=fqdn,
        role=str(role.get("role", "")),
        role_description=str(role.get("description", "")),
        declared_ports=declared_ports,
        critical=bool(role.get("critical", False)),
    )
    result.ip, result.dns_error = _resolve(fqdn)
    if result.ip is None:
        return result

    result.icmp_ok = _icmp_ping(fqdn, timeout)
    if result.icmp_ok:
        result.responding_protocols.append("ICMP")

    ports_to_scan = sorted(set(list(declared_ports) + list(COMMON_TCP_PORTS)))
    for port in ports_to_scan:
        state = _tcp_check(fqdn, port, timeout)
        result.tcp[port] = state
        if state == "open":
            result.responding_protocols.append(f"TCP/{port}")

    _probe_http_stack(fqdn, timeout, declared_ports, result)
    _probe_udp_ike_if_needed(fqdn, timeout, result)

    result.server_class = _classify(result)
    return result


def _run_probes(
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
    results: list[ProbeResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_probe_fqdn, fqdn, role, timeout): fqdn for fqdn, role in entries}
        for fut in concurrent.futures.as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as exc:  # pragma: no cover - defensive
                fqdn = futures[fut]
                stub = ProbeResult(
                    fqdn=fqdn,
                    role="",
                    role_description="",
                    declared_ports=[],
                    critical=False,
                )
                stub.notes.append(f"probe crashed: {type(exc).__name__}: {exc}")
                results.append(stub)
    results.sort(key=lambda r: (r.role, r.fqdn))
    return results


_CENR_SYNTHETIC_ROLE: dict[str, Any] = {
    "role": "cenr_zen_proxy",
    "description": "Zscaler ZEN cloud-enforcement proxy (from merged CENR feed)",
    "ports": [80, 443, 8080],
    "critical": False,
}
"""Synthetic role dict assigned to every CENR hostname during full-fleet
validation. ZEN proxies do not appear in the ZCC role catalogue, so we mint
a stable role slug (``cenr_zen_proxy``) locally to keep sorting/grouping in
the report and logs consistent."""


def _collect_zcc_probe_entries(
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
        seen: Deduplication set for FQDNs already queued; mutated in place.
        entries: Probe queue tuples ``(fqdn, role)``; mutated in place.
    """
    for role in probes.get("roles", []) or []:
        if not isinstance(role, dict):
            continue
        for entry in role.get("fqdns", []) or []:
            # Unwrap v3 dict entries {"host": ...} while still tolerating
            # legacy flat strings so mid-migration caches keep working.
            fqdn = entry.get("host") if isinstance(entry, dict) else entry
            fqdn_s = str(fqdn) if fqdn is not None else ""  # guard None from broken v3 rows
            if fqdn_s and fqdn_s not in seen:
                seen.add(fqdn_s)
                entries.append((fqdn_s, role))


def _collect_cenr_probe_entries(
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
    for key in ("proxy_hostnames", "vpn_hostnames"):
        for entry in cenr.get(key, []) or []:
            # Same v3-dict unwrap for CENR bags; str() must never see the
            # raw dict or it produces a "{'host': ...}" pseudo-hostname.
            host = entry.get("host") if isinstance(entry, dict) else entry
            host_s = str(host) if host is not None else ""  # guard None from broken v3 rows
            if host_s and host_s not in seen:
                seen.add(host_s)
                entries.append((host_s, _CENR_SYNTHETIC_ROLE))


def _log_probe_failures(results: list[ProbeResult]) -> None:
    """Emit a DEBUG line for every ProbeResult with no responding protocols.

    Why:
        Kept at DEBUG (not INFO) so a batch of transient timeouts during
        an 8-hour refresh window does not spam operator logs; the caller
        still emits one INFO summary. Extracted so the parent's CC drops
        under the gate.

    Args:
        results: The probe result list returned by ``_run_probes``.
    """
    for r in results:
        if not r.responding_protocols:
            logger.debug(
                "zscaler_probe: no response from %s (role=%s ip=%s notes=%s)",
                r.fqdn,
                r.role or "<none>",
                r.ip or "-",
                "; ".join(r.notes) or "-",
            )


def run_full_validation(
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
        transient timeouts does not spam INFO; a single INFO summary line is
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
    entries: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()
    _collect_zcc_probe_entries(probes, seen, entries)
    _collect_cenr_probe_entries(cenr, seen, entries)

    logger.info(
        "zscaler_probe: validating %d endpoints (timeout=%.1fs, workers=%d)",
        len(entries),
        timeout,
        workers,
    )
    results = _run_probes(entries, timeout, workers)

    ok = sum(1 for r in results if r.responding_protocols)
    dns_fail = sum(1 for r in results if r.ip is None)
    tls_fail = sum(1 for r in results if r.tls_error)
    logger.info(
        "zscaler_probe: %d/%d endpoints responded on at least one protocol " "(dns_fail=%d, tls_fail=%d)",
        ok,
        len(results),
        dns_fail,
        tls_fail,
    )
    _log_probe_failures(results)
    return results
