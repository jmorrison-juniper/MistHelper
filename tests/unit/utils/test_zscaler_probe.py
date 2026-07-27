"""Unit tests for :mod:`src.utils.zscaler_probe`.

Why:
    The probe module is the live-validation half of menu 206's Zscaler
    auto-refresh contract. Regressions in ``_classify``'s rule ordering would
    mislabel endpoints (masking a Zscaler service failure as ``unknown``);
    regressions in ``run_full_validation``'s dedup/merge would either
    double-probe overlapping FQDNs across ZCC/CENR or skip CENR hostnames
    entirely. All real networking is monkey-patched -- no DNS, ICMP, TCP, or
    TLS calls leave the test suite.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.utils import zscaler_probe as zp_mod
from src.utils.zscaler_probe import (
    _CENR_SYNTHETIC_ROLE,
    COMMON_TCP_PORTS,
    DEFAULT_TIMEOUT,
    DEFAULT_WORKERS,
    ProbeResult,
    _classify,
    run_full_validation,
)


class TestProbeResult:
    """Cover :class:`ProbeResult` default-field and custom-field construction."""

    def test_defaults_populate_empty_collections(self) -> None:
        """Default construction should give per-instance mutable collections.

        Why:
            ``tcp``, ``responding_protocols``, and ``notes`` use
            ``field(default_factory=...)``; if a maintainer accidentally
            switched to a shared literal default, two instances would alias
            each other and cross-contaminate.
        """
        a = ProbeResult(
            fqdn="a.example.com",
            role="r",
            role_description="d",
            declared_ports=[80],
            critical=False,
        )
        b = ProbeResult(
            fqdn="b.example.com",
            role="r",
            role_description="d",
            declared_ports=[80],
            critical=False,
        )
        assert a.tcp == {}
        assert a.responding_protocols == []
        assert a.notes == []
        assert a.server_class == "unknown"
        a.tcp[443] = "open"
        a.responding_protocols.append("HTTPS")
        a.notes.append("hello")
        assert b.tcp == {}
        assert b.responding_protocols == []
        assert b.notes == []

    def test_custom_fields_round_trip(self) -> None:
        """Custom-field construction should preserve every attribute verbatim."""
        result = ProbeResult(
            fqdn="pac.zscaler.net",
            role="pac_delivery",
            role_description="PAC file delivery",
            declared_ports=[80, 443],
            critical=True,
            ip="1.2.3.4",
            icmp_ok=True,
            tcp={80: "open", 443: "open"},
            http_status=200,
            https_status=200,
            responding_protocols=["ICMP", "TCP/80", "TCP/443", "HTTPS"],
            server_class="Zscaler PAC delivery",
            notes=["all good"],
        )
        assert result.fqdn == "pac.zscaler.net"
        assert result.role == "pac_delivery"
        assert result.critical is True
        assert result.ip == "1.2.3.4"
        assert result.tcp[80] == "open"
        assert "HTTPS" in result.responding_protocols
        assert result.server_class == "Zscaler PAC delivery"
        assert result.notes == ["all good"]


def _make_result(
    *,
    fqdn: str = "example.com",
    http_server: str | None = None,
    https_server: str | None = None,
    tls_subject: str | None = None,
    tls_issuer: str | None = None,
) -> ProbeResult:
    """Build a bare ProbeResult with only the fields _classify inspects.

    Why:
        ``_classify`` reads ``fqdn``, ``http_server``, ``https_server``,
        ``tls_subject``, and ``tls_issuer`` -- everything else is irrelevant to
        classification, so keep test setup terse.

    Args:
        fqdn: FQDN under test.
        http_server: Value of the plaintext HTTP ``Server`` header.
        https_server: Value of the HTTPS ``Server`` header.
        tls_subject: TLS peer-cert subject CN/O.
        tls_issuer: TLS peer-cert issuer CN/O.

    Returns:
        A minimally populated :class:`ProbeResult`.
    """
    return ProbeResult(
        fqdn=fqdn,
        role="",
        role_description="",
        declared_ports=[],
        critical=False,
        http_server=http_server,
        https_server=https_server,
        tls_subject=tls_subject,
        tls_issuer=tls_issuer,
    )


class TestClassify:
    """Cover every ordered branch of ``_classify``'s rules table."""

    def test_cloudfront_in_fqdn(self) -> None:
        """CloudFront rule should win when the FQDN itself carries the hint."""
        assert _classify(_make_result(fqdn="d123.cloudfront.net")) == ("AWS CloudFront (CDN)")

    def test_cloudfront_in_server_header(self) -> None:
        """CloudFront classification triggers on ``Server: CloudFront``."""
        assert (
            _classify(
                _make_result(fqdn="cdn.example.com", https_server="CloudFront"),
            )
            == "AWS CloudFront (CDN)"
        )

    def test_cloudfront_in_tls_subject(self) -> None:
        """CloudFront classification triggers on a CloudFront-issued cert."""
        assert (
            _classify(
                _make_result(fqdn="cdn.example.com", tls_subject="*.cloudfront.net"),
            )
            == "AWS CloudFront (CDN)"
        )

    def test_sme_zscaler_net_is_zen_proxy(self) -> None:
        """``.sme.zscaler.net`` beats the generic zscaler-issuer branch."""
        assert (
            _classify(
                _make_result(
                    fqdn="zs1.sme.zscaler.net",
                    tls_issuer="Zscaler Root CA",
                ),
            )
            == "Zscaler ZEN proxy node"
        )

    def test_zscaler_pac(self) -> None:
        """``pac`` substring under a zscaler cert routes to PAC delivery."""
        assert (
            _classify(
                _make_result(fqdn="pac.zscaler.net", tls_issuer="Zscaler Inc"),
            )
            == "Zscaler PAC delivery"
        )

    def test_zscaler_gateway(self) -> None:
        """``gateway`` substring routes to the captive-portal branch."""
        assert (
            _classify(
                _make_result(fqdn="gateway.zscaler.net", tls_issuer="Zscaler CA"),
            )
            == "Zscaler captive-portal gateway"
        )

    def test_zscaler_login(self) -> None:
        """``login`` under a zscaler cert routes to enrollment/login."""
        assert (
            _classify(
                _make_result(fqdn="login.zscaler.net", tls_issuer="Zscaler CA"),
            )
            == "Zscaler enrollment/login"
        )

    def test_zscaler_mobile(self) -> None:
        """``mobile`` under a zscaler cert also routes to enrollment/login."""
        assert (
            _classify(
                _make_result(fqdn="mobile.zscaler.net", tls_issuer="Zscaler CA"),
            )
            == "Zscaler enrollment/login"
        )

    def test_zscaler_healthapp(self) -> None:
        """``healthapp`` under a zscaler cert routes to health-probe."""
        assert (
            _classify(
                _make_result(fqdn="healthapp.zscaler.net", tls_issuer="Zscaler CA"),
            )
            == "Zscaler health-probe endpoint"
        )

    def test_zscaler_mobilesupport(self) -> None:
        """``mobilesupport`` routes to the support-endpoint label."""
        assert (
            _classify(
                _make_result(fqdn="mobilesupport.zscaler.net", tls_issuer="Zscaler"),
            )
            == "Zscaler support endpoint"
        )

    def test_zscaler_ecdn(self) -> None:
        """``ecdn`` routes to the update-channel label."""
        assert (
            _classify(
                _make_result(fqdn="ecdn.zscaler.net", tls_issuer="Zscaler"),
            )
            == "Zscaler ECDN (update channel)"
        )

    def test_zscaler_private(self) -> None:
        """``private.zscaler`` routes to the private/internal label."""
        assert (
            _classify(
                _make_result(
                    fqdn="private.zscaler.com",
                    tls_issuer="Zscaler Internal CA",
                ),
            )
            == "Zscaler private/internal"
        )

    def test_zscaler_generic_fallback(self) -> None:
        """Zscaler-cert host with no keyword match returns the generic label."""
        assert (
            _classify(
                _make_result(
                    fqdn="misc.zscaler.example",
                    tls_issuer="Zscaler Root CA",
                ),
            )
            == "Zscaler service"
        )

    def test_digicert_in_fqdn(self) -> None:
        """DigiCert-hostname endpoints classify as OCSP/CRL responders."""
        assert (
            _classify(
                _make_result(fqdn="ocsp.digicert.com"),
            )
            == "DigiCert OCSP/CRL responder"
        )

    def test_digicert_in_server_header(self) -> None:
        """DigiCert classification also triggers on the ``Server`` header."""
        assert (
            _classify(
                _make_result(fqdn="crl.example.com", http_server="digicert"),
            )
            == "DigiCert OCSP/CRL responder"
        )

    def test_google_captive_portal(self) -> None:
        """``*.google.com`` maps to the captive-portal probe target."""
        assert (
            _classify(
                _make_result(fqdn="connectivitycheck.gstatic.google.com"),
            )
            == "Google captive-portal probe target"
        )

    def test_secb2b_samsung(self) -> None:
        """``secb2b`` substring maps to the Samsung ELM activation label."""
        assert (
            _classify(
                _make_result(fqdn="account.secb2b.com"),
            )
            == "Samsung ELM activation (secb2b.com)"
        )

    def test_server_header_fallback(self) -> None:
        """An unrecognized host with a ``Server`` header echoes ``Web server (...)``."""
        assert (
            _classify(
                _make_result(fqdn="unknown.example.com", https_server="nginx"),
            )
            == "Web server (nginx)"
        )

    def test_unknown_when_no_rule_matches(self) -> None:
        """No headers/cert/FQDN hints → ``unknown``."""
        assert _classify(_make_result(fqdn="mystery.example.com")) == "unknown"


class TestRunFullValidation:
    """End-to-end coverage of ``run_full_validation`` with probes stubbed out."""

    def test_probes_all_zcc_and_cenr_hosts(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """ZCC roles enumerate first, then CENR proxy + VPN hostnames get merged.

        Why:
            The dedup contract is that ZCC roles are enumerated first, then
            CENR hostnames are appended under the synthetic role. This test
            asserts the invocation set (roles-first ordering + CENR coverage).
        """
        captured: list[tuple[str, dict[str, Any]]] = []

        def fake_run_probes(
            entries: list[tuple[str, dict[str, Any]]],
            timeout: float,
            workers: int,
        ) -> list[ProbeResult]:
            """Capture entries and synthesize a trivial ProbeResult per FQDN."""
            captured.extend(entries)
            return [
                ProbeResult(
                    fqdn=fqdn,
                    role=str(role.get("role", "")),
                    role_description=str(role.get("description", "")),
                    declared_ports=list(role.get("ports") or []),
                    critical=bool(role.get("critical", False)),
                    responding_protocols=["ICMP"],
                )
                for fqdn, role in entries
            ]

        monkeypatch.setattr(zp_mod, "_run_probes", fake_run_probes)

        probes = {
            "roles": [
                {
                    "role": "pac_delivery",
                    "description": "PAC",
                    "ports": [80, 443],
                    "critical": True,
                    "fqdns": ["pac.zscaler.net", "pac2.zscaler.net"],
                },
                {
                    "role": "gateway",
                    "description": "Gateway",
                    "ports": [443],
                    "critical": False,
                    "fqdns": ["gateway.zscaler.net"],
                },
            ],
        }
        cenr = {
            "proxy_hostnames": ["zen1.zscaler.net", "zen2.zscaler.net"],
            "vpn_hostnames": ["vpn1.zscaler.net"],
        }

        results = run_full_validation(probes, cenr)

        # 3 ZCC + 3 CENR = 6 unique FQDNs, no overlap in this fixture.
        assert len(captured) == 6
        assert len(results) == 6

        # ZCC roles are enumerated first, then CENR proxy_hostnames, then vpn.
        assert [fqdn for fqdn, _ in captured[:3]] == [
            "pac.zscaler.net",
            "pac2.zscaler.net",
            "gateway.zscaler.net",
        ]
        # The remaining three should carry the synthetic CENR role.
        for fqdn, role in captured[3:]:
            assert fqdn in {"zen1.zscaler.net", "zen2.zscaler.net", "vpn1.zscaler.net"}
            assert role is _CENR_SYNTHETIC_ROLE

    def test_dedup_collapses_overlap_between_zcc_and_cenr(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A ZCC FQDN also present in CENR should be probed once, under the ZCC role.

        Why:
            ``run_full_validation`` maintains a single ``seen`` set spanning
            both catalogues; the first insertion wins so ZCC role metadata is
            preserved when CENR happens to list the same host.
        """
        captured: list[tuple[str, dict[str, Any]]] = []

        def fake_run_probes(
            entries: list[tuple[str, dict[str, Any]]],
            timeout: float,
            workers: int,
        ) -> list[ProbeResult]:
            """Record entries; return empty result list (dedup is the assertion)."""
            captured.extend(entries)
            return []

        monkeypatch.setattr(zp_mod, "_run_probes", fake_run_probes)

        probes = {
            "roles": [
                {
                    "role": "pac_delivery",
                    "description": "PAC",
                    "ports": [80, 443],
                    "critical": True,
                    "fqdns": ["shared.zscaler.net"],
                },
            ],
        }
        cenr = {
            "proxy_hostnames": ["shared.zscaler.net", "unique.zscaler.net"],
            "vpn_hostnames": [],
        }

        run_full_validation(probes, cenr)

        fqdns = [fqdn for fqdn, _ in captured]
        assert fqdns.count("shared.zscaler.net") == 1
        assert "unique.zscaler.net" in fqdns  # lgtm[py/incomplete-url-substring-sanitization]
        # The dedup keeps the ZCC role (first insertion) for the shared host.
        shared_role = next(role for fqdn, role in captured if fqdn == "shared.zscaler.net")
        assert shared_role.get("role") == "pac_delivery"

    def test_non_dict_role_is_skipped(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A malformed roles entry (non-dict) is silently dropped.

        Why:
            The catalogue is user-supplied JSON; a hand-edit that swaps a role
            dict for a string should not crash the refresh. The guard makes
            the loader tolerant of that shape drift.
        """
        captured: list[tuple[str, dict[str, Any]]] = []

        def fake_run_probes(
            entries: list[tuple[str, dict[str, Any]]],
            timeout: float,
            workers: int,
        ) -> list[ProbeResult]:
            """Record entries; return empty result list."""
            captured.extend(entries)
            return []

        monkeypatch.setattr(zp_mod, "_run_probes", fake_run_probes)

        probes = {
            "roles": [
                "not a dict",  # skipped
                {
                    "role": "gateway",
                    "description": "Gateway",
                    "ports": [443],
                    "critical": False,
                    "fqdns": ["gateway.zscaler.net"],
                },
                None,  # skipped
            ],
        }
        cenr: dict[str, Any] = {}

        run_full_validation(probes, cenr)

        assert [fqdn for fqdn, _ in captured] == ["gateway.zscaler.net"]

    def test_empty_inputs_return_empty_list(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Empty ZCC + CENR docs should short-circuit to an empty result list."""
        called = {"n": 0}

        def fake_run_probes(
            entries: list[tuple[str, dict[str, Any]]],
            timeout: float,
            workers: int,
        ) -> list[ProbeResult]:
            """Record that _run_probes was called; return empty."""
            called["n"] += 1
            assert entries == []
            return []

        monkeypatch.setattr(zp_mod, "_run_probes", fake_run_probes)

        assert run_full_validation({}, {}) == []
        assert called["n"] == 1

    def test_missing_role_lists_do_not_crash(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Missing ``roles``/``fqdns``/``proxy_hostnames`` keys default to empty."""

        def fake_run_probes(
            entries: list[tuple[str, dict[str, Any]]],
            timeout: float,
            workers: int,
        ) -> list[ProbeResult]:
            """Ignore inputs; return empty."""
            return []

        monkeypatch.setattr(zp_mod, "_run_probes", fake_run_probes)

        # ``roles`` explicitly None + a role missing ``fqdns`` entirely.
        probes: dict[str, Any] = {
            "roles": [
                {"role": "x", "description": "y", "ports": [80], "critical": False},
            ],
        }
        cenr: dict[str, Any] = {"proxy_hostnames": None, "vpn_hostnames": None}
        assert run_full_validation(probes, cenr) == []

    def test_forwards_timeout_and_workers(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Custom ``timeout``/``workers`` kwargs thread through to ``_run_probes``."""
        seen: dict[str, Any] = {}

        def fake_run_probes(
            entries: list[tuple[str, dict[str, Any]]],
            timeout: float,
            workers: int,
        ) -> list[ProbeResult]:
            """Capture the forwarded timeout/workers values."""
            seen["timeout"] = timeout
            seen["workers"] = workers
            return []

        monkeypatch.setattr(zp_mod, "_run_probes", fake_run_probes)

        run_full_validation({}, {}, timeout=7.5, workers=4)
        assert seen == {"timeout": 7.5, "workers": 4}

    def test_defaults_match_module_constants(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Omitted kwargs should adopt ``DEFAULT_TIMEOUT``/``DEFAULT_WORKERS``."""
        seen: dict[str, Any] = {}

        def fake_run_probes(
            entries: list[tuple[str, dict[str, Any]]],
            timeout: float,
            workers: int,
        ) -> list[ProbeResult]:
            """Capture the forwarded timeout/workers values."""
            seen["timeout"] = timeout
            seen["workers"] = workers
            return []

        monkeypatch.setattr(zp_mod, "_run_probes", fake_run_probes)

        run_full_validation({}, {})
        assert seen == {"timeout": DEFAULT_TIMEOUT, "workers": DEFAULT_WORKERS}


class TestModuleConstants:
    """Sanity checks on the module-level constants that other code depends on."""

    def test_common_tcp_ports_include_proxy_ports(self) -> None:
        """80/443/8080 must remain in ``COMMON_TCP_PORTS`` for probe coverage."""
        assert set(COMMON_TCP_PORTS) == {80, 443, 8080}

    def test_cenr_synthetic_role_shape(self) -> None:
        """The synthetic CENR role must expose the fields ``_probe_fqdn`` reads."""
        assert _CENR_SYNTHETIC_ROLE["role"] == "cenr_zen_proxy"
        assert set(_CENR_SYNTHETIC_ROLE["ports"]) == {80, 443, 8080}
        assert _CENR_SYNTHETIC_ROLE["critical"] is False
        assert "description" in _CENR_SYNTHETIC_ROLE


# --------------------------------------------------------------------------- #
# Feature 1023 US2: IKE UDP probe primitive + trigger dispatch                #
# --------------------------------------------------------------------------- #
# Why:
#   Zscaler VPN endpoints (``*-vpn.*`` hostnames) answer IKE on UDP/500 and
#   the NAT-T fallback UDP/4500 rather than any TCP port. Without a
#   UDP probe path Menu 206 schedules TCP-only synthetic tests against
#   these FQDNs and silently labels them dead. US2 adds a stdlib-only
#   IKE_SA_INIT-shaped datagram probe and wires it into ``_probe_fqdn``
#   behind a narrow trigger predicate (vpn hostname OR all TCP dead) so
#   TCP-only endpoints do not regress with pointless UDP overhead.


class _StubDatagramSocket:
    """In-memory ``socket.socket`` double for exercising ``_udp_check`` without touching the network.

    Why:
        The UDP probe must never hit a real name-server or peer during
        pytest; a stub keeps the test suite deterministic and hermetic while
        still asserting the exact datagram bytes we put on the wire (which
        is the load-bearing protocol contract for IKE_SA_INIT + non-ESP
        marker).
    """

    def __init__(
        self,
        *,
        recv_bytes: bytes | None = None,
        recv_exc: Exception | None = None,
        connect_exc: Exception | None = None,
    ) -> None:
        self.sent: list[tuple[bytes, tuple[str, int]]] = []  # captured sendto args
        self.timeout: float | None = None  # captured settimeout arg
        self.closed = False  # so tests can assert cleanup happened
        self._recv_bytes = recv_bytes  # payload returned by recvfrom
        self._recv_exc = recv_exc  # exception raised by recvfrom (e.g. timeout)
        self._connect_exc = connect_exc  # exception raised at socket construction

    def settimeout(self, seconds: float) -> None:
        """Record the timeout the caller set; a real socket would apply it globally."""
        self.timeout = seconds

    def sendto(self, data: bytes, addr: tuple[str, int]) -> int:
        """Capture the outbound datagram bytes and destination for later assertion."""
        self.sent.append((data, addr))
        return len(data)

    def recvfrom(self, _bufsize: int) -> tuple[bytes, tuple[str, int]]:
        """Return the pre-programmed reply or raise the pre-programmed exception."""
        if self._recv_exc is not None:
            raise self._recv_exc
        return (self._recv_bytes or b""), ("0.0.0.0", 0)

    def close(self) -> None:
        """Flip the ``closed`` sentinel so tests can assert the caller cleaned up."""
        self.closed = True

    def __enter__(self) -> _StubDatagramSocket:
        if self._connect_exc is not None:
            raise self._connect_exc
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def _install_udp_stub(monkeypatch: pytest.MonkeyPatch, stub: _StubDatagramSocket) -> list[tuple[int, int, int]]:
    """Patch ``socket.socket`` in ``zscaler_probe`` so ``_udp_check`` uses *stub*.

    Why:
        Consolidates the monkeypatch so each test just declares intent
        (open/timeout/error) without duplicating the boilerplate. Returns the
        capture list of ``(family, type, proto)`` calls so a dedicated test
        can assert that the SOCK_DGRAM path is never accidentally called
        outside the UDP tests.
    """
    calls: list[tuple[int, int, int]] = []  # captured (family, type, proto)

    def _factory(family: int, type_: int, proto: int = 0) -> _StubDatagramSocket:
        calls.append((family, type_, proto))  # record so tests can assert
        return stub

    monkeypatch.setattr(zp_mod.socket, "socket", _factory)
    return calls


def test_udp_check_returns_open_on_datagram(monkeypatch: pytest.MonkeyPatch) -> None:
    """A reply datagram of any length marks the port ``open``.

    Why (FR-002): IKE responders answer with an IKE_SA_INIT-RESP; even a
    stray ICMP-hosted UDP echo is treated as ``open`` because the mere
    presence of any inbound datagram proves the port is not black-holed.
    """
    stub = _StubDatagramSocket(recv_bytes=b"\x00" * 28)  # any non-empty datagram
    _install_udp_stub(monkeypatch, stub)
    assert zp_mod._udp_check("gateway.zscaler.net", 500, timeout=1.0) == "open"


def test_udp_check_returns_no_reply_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """A ``socket.timeout`` on ``recvfrom`` must produce ``no_reply``.

    Why (FR-002): Silent-drop firewalls do not RST UDP; the only signal is
    absence. ``no_reply`` distinguishes "black hole" from a genuine OSError
    so operators can tell "middlebox drop" apart from "route missing".
    """
    stub = _StubDatagramSocket(recv_exc=TimeoutError())  # simulate silent drop
    _install_udp_stub(monkeypatch, stub)
    assert zp_mod._udp_check("gateway.zscaler.net", 4500, timeout=1.0) == "no_reply"


def test_udp_check_returns_error_prefix_on_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    """Any non-timeout ``OSError`` returns ``error:<ExceptionClassName>``.

    Why (FR-002): The exception class name is the operator's fault-domain
    hint (``NetworkUnreachable`` vs ``PermissionError`` vs generic
    ``OSError``). Prefixing with ``error:`` keeps the return type a plain
    string that matches ``_tcp_check``'s vocabulary.
    """
    stub = _StubDatagramSocket(recv_exc=PermissionError())  # simulate raw-socket denial
    _install_udp_stub(monkeypatch, stub)
    result = zp_mod._udp_check("gateway.zscaler.net", 500, timeout=1.0)
    assert result.startswith("error:")
    assert "PermissionError" in result


def test_udp_check_uses_settimeout_and_closes_socket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The caller must apply ``settimeout`` and always release the socket.

    Why (FR-002): Without ``settimeout`` a silent-drop endpoint would block
    the probe thread forever, stalling the whole ThreadPoolExecutor. Leaked
    sockets exhaust the ephemeral-port range on long-running scans.
    """
    stub = _StubDatagramSocket(recv_exc=TimeoutError())  # timeout also triggers close
    _install_udp_stub(monkeypatch, stub)
    zp_mod._udp_check("gateway.zscaler.net", 500, timeout=2.5)
    assert stub.timeout == 2.5  # timeout was applied to the socket
    assert stub.closed is True  # context manager released the socket


def test_udp_check_port_4500_prepends_non_esp_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """On UDP/4500 the payload MUST begin with the four-byte non-ESP marker.

    Why (contract udp_probe_wire_format.md): NAT-T listeners multiplex ESP
    and IKE on 4500 by inspecting the first 4 bytes: 0x00000000 means
    "IKE payload follows"; anything else is treated as ESP and silently
    dropped. Missing this marker turns every UDP/4500 probe into a false
    negative.
    """
    stub = _StubDatagramSocket(recv_bytes=b"\x00" * 28)  # arbitrary reply
    _install_udp_stub(monkeypatch, stub)
    zp_mod._udp_check("vpn.example.zscaler.net", 4500, timeout=1.0)
    assert stub.sent, "sendto was never called"
    payload, addr = stub.sent[0]
    assert addr == ("vpn.example.zscaler.net", 4500)
    assert payload[:4] == b"\x00\x00\x00\x00", "port 4500 requires non-ESP marker"
    # And the IKE header (28 bytes) must actually be present after the marker.
    assert len(payload) >= 4 + 28


def test_udp_check_port_500_omits_non_esp_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """On UDP/500 the payload MUST NOT include the non-ESP marker.

    Why (contract udp_probe_wire_format.md): Port 500 is IKE-only and does
    not multiplex with ESP, so the marker would be interpreted as part of
    the IKE header (leading to a malformed SPI) and the responder would
    drop the datagram.
    """
    stub = _StubDatagramSocket(recv_bytes=b"\x00" * 28)  # arbitrary reply
    _install_udp_stub(monkeypatch, stub)
    zp_mod._udp_check("vpn.example.zscaler.net", 500, timeout=1.0)
    payload, _addr = stub.sent[0]
    # First bytes are the SPI (random), NOT the four-byte zero marker.
    assert payload[:4] != b"\x00\x00\x00\x00", "port 500 must NOT carry marker"


def test_probe_fqdn_triggers_udp_for_vpn_hostname(monkeypatch: pytest.MonkeyPatch) -> None:
    """When the FQDN contains ``-vpn.``, both UDP ports are probed regardless of TCP state.

    Why (FR-002 trigger 1): The catalogue tags VPN hosts by hostname pattern
    since the CENR feed does not distinguish protocol. Firing UDP on the
    pattern match ensures we never miss a VPN endpoint that also happens to
    RST-close port 443.
    """
    # Force all lower-level probes to be no-ops except the UDP path.
    monkeypatch.setattr(zp_mod, "_resolve", lambda _f: ("10.0.0.1", None))
    monkeypatch.setattr(zp_mod, "_icmp_ping", lambda *_a, **_kw: False)
    monkeypatch.setattr(zp_mod, "_tcp_check", lambda *_a, **_kw: "open")  # TCP live
    monkeypatch.setattr(zp_mod, "_do_http", lambda *_a, **_kw: (None, "stub"))
    monkeypatch.setattr(zp_mod, "_tls_peer", lambda *_a, **_kw: (None, None, "stub"))
    seen_udp: list[tuple[str, int]] = []  # captured (host, port) calls

    def _udp_stub(host: str, port: int, _timeout: float) -> str:
        seen_udp.append((host, port))
        return "open"

    monkeypatch.setattr(zp_mod, "_udp_check", _udp_stub)
    result = zp_mod._probe_fqdn("gw-vpn.example.zscaler.net", {"role": "r"}, timeout=1.0)
    assert [p for _h, p in seen_udp] == [500, 4500], "vpn hostname must fire both UDP ports"
    assert result.udp == {500: "open", 4500: "open"}


def test_probe_fqdn_triggers_udp_when_all_tcp_dead(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When every TCP port is dead the fallback UDP probe MUST fire.

    Why (FR-002 trigger 2): A non-``-vpn.`` host with every TCP port
    black-holed is our only signal that we may have misclassified a VPN
    endpoint. Firing UDP in this last-ditch case recovers those endpoints
    without noisily probing every healthy host.
    """
    monkeypatch.setattr(zp_mod, "_resolve", lambda _f: ("10.0.0.1", None))
    monkeypatch.setattr(zp_mod, "_icmp_ping", lambda *_a, **_kw: False)
    # Every TCP probe returns closed -> triggers the "all dead" fallback branch.
    monkeypatch.setattr(zp_mod, "_tcp_check", lambda *_a, **_kw: "closed")
    monkeypatch.setattr(zp_mod, "_do_http", lambda *_a, **_kw: (None, "stub"))
    monkeypatch.setattr(zp_mod, "_tls_peer", lambda *_a, **_kw: (None, None, "stub"))
    seen: list[int] = []

    def _udp_stub(_host: str, port: int, _timeout: float) -> str:
        seen.append(port)
        return "no_reply"

    monkeypatch.setattr(zp_mod, "_udp_check", _udp_stub)
    result = zp_mod._probe_fqdn("mystery.example.net", {"role": "r"}, timeout=1.0)
    assert seen == [500, 4500], "all-TCP-dead must fire both UDP ports"
    assert result.udp == {500: "no_reply", 4500: "no_reply"}


def test_probe_fqdn_skips_udp_when_tcp_live_and_not_vpn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A healthy non-VPN host must not incur any UDP overhead.

    Why (FR-002 negative case): UDP probing on every host would double the
    scan wall-time and generate unwanted IKE traffic to non-VPN
    endpoints. The trigger must be strictly (vpn hostname OR all TCP dead).
    """
    monkeypatch.setattr(zp_mod, "_resolve", lambda _f: ("10.0.0.1", None))
    monkeypatch.setattr(zp_mod, "_icmp_ping", lambda *_a, **_kw: False)
    # At least one TCP port must return "open" to skip the fallback.
    monkeypatch.setattr(zp_mod, "_tcp_check", lambda *_a, **_kw: "open")
    monkeypatch.setattr(zp_mod, "_do_http", lambda *_a, **_kw: (None, "stub"))
    monkeypatch.setattr(zp_mod, "_tls_peer", lambda *_a, **_kw: (None, None, "stub"))
    udp_called = False

    def _udp_stub(*_a: object, **_kw: object) -> str:
        nonlocal udp_called
        udp_called = True  # any invocation is a regression
        return "open"

    monkeypatch.setattr(zp_mod, "_udp_check", _udp_stub)
    result = zp_mod._probe_fqdn("proxy.example.zscaler.net", {"role": "r"}, timeout=1.0)
    assert udp_called is False, "UDP must not fire on healthy non-VPN host"
    assert result.udp == {}, "empty udp dict = no probe attempted"


def test_no_real_sock_dgram_socket_created(monkeypatch: pytest.MonkeyPatch) -> None:
    """Guard-rail: nothing outside ``_udp_check`` may build a SOCK_DGRAM socket.

    Why:
        This test doubles as a canary. If any future refactor accidentally
        creates a raw datagram socket outside the covered ``_udp_check``
        path, this test's assertion trips and forces the author to route
        through the monkey-patch-friendly primitive instead.
    """
    stub = _StubDatagramSocket(recv_bytes=b"\x00" * 28)
    calls = _install_udp_stub(monkeypatch, stub)
    zp_mod._udp_check("host.example", 500, timeout=1.0)
    assert calls, "the socket factory should have been called exactly once"
    for _family, sock_type, _proto in calls:
        # ``socket.SOCK_DGRAM`` is the enum flag for UDP; anything else here
        # means the probe accidentally opened a TCP or raw socket.
        assert sock_type == zp_mod.socket.SOCK_DGRAM
