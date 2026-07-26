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
        assert "unique.zscaler.net" in fqdns
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
