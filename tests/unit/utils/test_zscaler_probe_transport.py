"""Tests for the Zscaler probe transport helpers and the parallel probe runner.

Why:
    ``src/utils/zscaler_probe.py`` opens sockets, runs a subprocess, wraps a
    TLS session, and fans probes out across a thread pool. Every one of those
    paths owns a resource that must close on both the success path and the
    failure path. A leak here strands a socket or a worker thread for the whole
    session. This module covers those transport helpers and the runner. Every
    socket, every TLS context, and every subprocess is mocked, so no test
    reaches the network.
"""

from __future__ import annotations

import socket
import ssl
import subprocess
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.utils import zscaler_probe as zp
from src.utils.zscaler_probe import ProbeResult


def _make_result(**overrides: Any) -> ProbeResult:
    """Return a ProbeResult with the required fields filled in.

    Why:
        The dataclass has five required fields. Repeating them in every test
        would hide the one field each test actually cares about.
    """
    # WHY: the defaults describe a plain non-critical host with no declared ports.
    base: dict[str, Any] = {
        "fqdn": "gateway.zscaler.net",
        "role": "zen",
        "role_description": "Zscaler enforcement node",
        "declared_ports": [],
        "critical": False,
    }
    base.update(overrides)  # WHY: let each test override only the field under test.
    return ProbeResult(**base)


class TestResolve:
    """Cover DNS resolution, which must report a failure rather than raise."""

    def test_a_successful_lookup_returns_the_address(self) -> None:
        """A caller needs the address to decide whether any probe can run."""
        with patch.object(socket, "gethostbyname", return_value="10.0.0.1"):
            assert zp._resolve("gateway.zscaler.net") == ("10.0.0.1", None)

    def test_a_failed_lookup_returns_the_reason(self) -> None:
        """The report separates a dead name from a live but unreachable host."""
        # WHY: gaierror is the exact type the resolver raises for an unknown name.
        with patch.object(socket, "gethostbyname", side_effect=socket.gaierror("no such host")):
            ip, error = zp._resolve("nope.invalid")
        assert ip is None  # WHY: no address means no downstream probe can run.
        assert error is not None  # WHY: the reason must survive for the summary.
        assert "gaierror" in error  # WHY: the class name tells the operator it was DNS.

    def test_a_failure_does_not_raise(self) -> None:
        """A raised error inside a worker thread would abort the whole fan-out."""
        with patch.object(socket, "gethostbyname", side_effect=OSError("network down")):
            zp._resolve("gateway.zscaler.net")  # WHY: the call must return, not raise.


class TestIcmpPing:
    """Cover the ping subprocess, including the platform flag switch."""

    def test_windows_uses_millisecond_timeout_flags(self) -> None:
        """The Windows ping binary reads the timeout in milliseconds, not seconds."""
        completed = MagicMock(returncode=0)  # WHY: a zero exit means the host answered.
        with (
            patch.object(zp.platform, "system", return_value="Windows"),
            patch.object(subprocess, "run", return_value=completed) as run_spy,
        ):
            assert zp._icmp_ping("10.0.0.1", 3.0) is True
        cmd = run_spy.call_args[0][0]  # WHY: read the argument vector that was built.
        assert cmd[1] == "-n"  # WHY: Windows spells the count flag "-n".
        assert cmd[3] == "-w"  # WHY: Windows spells the timeout flag "-w".
        assert cmd[4] == "3000"  # WHY: three seconds must become three thousand milliseconds.

    def test_posix_uses_second_timeout_flags(self) -> None:
        """The POSIX ping binary reads the timeout in whole seconds."""
        completed = MagicMock(returncode=0)  # WHY: a zero exit means the host answered.
        with (
            patch.object(zp.platform, "system", return_value="Linux"),
            patch.object(subprocess, "run", return_value=completed) as run_spy,
        ):
            zp._icmp_ping("10.0.0.1", 3.0)  # WHY: drive the POSIX branch.
        cmd = run_spy.call_args[0][0]  # WHY: read the argument vector that was built.
        assert cmd[1] == "-c"  # WHY: POSIX spells the count flag "-c".
        assert cmd[3] == "-W"  # WHY: POSIX spells the timeout flag with a capital "W".
        assert cmd[4] == "3"  # WHY: three seconds must stay three, not become three thousand.

    def test_the_shell_is_never_used(self) -> None:
        """A shell would let a hostname from the catalogue start a program."""
        completed = MagicMock(returncode=0)  # WHY: the exit code is not under test here.
        with (
            patch.object(zp.platform, "system", return_value="Linux"),
            patch.object(subprocess, "run", return_value=completed) as run_spy,
        ):
            zp._icmp_ping("10.0.0.1", 3.0)  # WHY: drive the subprocess call.
        _, kwargs = run_spy.call_args  # WHY: read the subprocess keywords.
        # WHY: the absence of shell=True keeps the host as one argv element.
        assert kwargs.get("shell", False) is False

    def test_the_subprocess_timeout_exceeds_the_probe_timeout(self) -> None:
        """A subprocess killed before ping finishes would report a false negative."""
        completed = MagicMock(returncode=0)  # WHY: the exit code is not under test here.
        with (
            patch.object(zp.platform, "system", return_value="Linux"),
            patch.object(subprocess, "run", return_value=completed) as run_spy,
        ):
            zp._icmp_ping("10.0.0.1", 3.0)  # WHY: drive the subprocess call.
        _, kwargs = run_spy.call_args  # WHY: read the subprocess keywords.
        assert kwargs["timeout"] == 5.0  # WHY: the two-second margin lets ping exit on its own.

    def test_a_non_zero_exit_reports_no_answer(self) -> None:
        """A non-zero exit means the host did not answer the echo request."""
        completed = MagicMock(returncode=1)  # WHY: ping exits non-zero on packet loss.
        with (
            patch.object(zp.platform, "system", return_value="Linux"),
            patch.object(subprocess, "run", return_value=completed),
        ):
            assert zp._icmp_ping("10.0.0.1", 3.0) is False

    def test_a_hung_ping_reports_no_answer(self) -> None:
        """A hung subprocess must not propagate out of a probe worker."""
        # WHY: TimeoutExpired is what subprocess raises when it kills the child.
        with (
            patch.object(zp.platform, "system", return_value="Linux"),
            patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired("ping", 5.0)),
        ):
            assert zp._icmp_ping("10.0.0.1", 3.0) is False

    def test_a_missing_ping_binary_reports_no_answer(self) -> None:
        """A container without a ping binary must degrade, not crash the scan."""
        # WHY: a stripped image raises FileNotFoundError, a subclass of OSError.
        with (
            patch.object(zp.platform, "system", return_value="Linux"),
            patch.object(subprocess, "run", side_effect=FileNotFoundError("ping")),
        ):
            assert zp._icmp_ping("10.0.0.1", 3.0) is False


class TestTcpCheck:
    """Cover the TCP handshake, which must always release its socket."""

    def test_a_successful_connect_reports_open(self) -> None:
        """An open port is the signal that a later HTTP probe is worth running."""
        with patch.object(socket, "create_connection", return_value=MagicMock()):
            assert zp._tcp_check("gateway.zscaler.net", 443, 3.0) == "open"

    def test_the_socket_closes_on_the_success_path(self) -> None:
        """A leaked socket would exhaust the file handle budget across a fleet scan."""
        sock = MagicMock()  # WHY: stand in for the connected socket object.
        with patch.object(socket, "create_connection", return_value=sock):
            zp._tcp_check("gateway.zscaler.net", 443, 3.0)  # WHY: drive the context manager.
        # WHY: the with block calls __exit__, which is the close hook on a socket.
        sock.__exit__.assert_called_once()

    def test_a_timeout_reports_closed(self) -> None:
        """A silent drop by a firewall reads as closed, not as an error."""
        with patch.object(socket, "create_connection", side_effect=TimeoutError("timed out")):
            assert zp._tcp_check("gateway.zscaler.net", 443, 3.0) == "closed"

    def test_a_refusal_reports_closed(self) -> None:
        """An explicit refusal also reads as closed, so the report stays simple."""
        with patch.object(socket, "create_connection", side_effect=ConnectionRefusedError()):
            assert zp._tcp_check("gateway.zscaler.net", 443, 3.0) == "closed"

    def test_another_socket_fault_reports_the_class_name(self) -> None:
        """A routing fault differs from a refusal, so the report must say which."""
        # WHY: an unreachable network is a transport fault, not a closed port.
        with patch.object(socket, "create_connection", side_effect=OSError("unreachable")):
            assert zp._tcp_check("gateway.zscaler.net", 443, 3.0) == "error:OSError"

    def test_the_timeout_reaches_the_socket_layer(self) -> None:
        """A connect without a timeout can hang a worker thread forever."""
        with patch.object(socket, "create_connection", return_value=MagicMock()) as connect_spy:
            zp._tcp_check("gateway.zscaler.net", 443, 7.5)  # WHY: drive the connect call.
        _, kwargs = connect_spy.call_args  # WHY: read the connect keywords.
        assert kwargs["timeout"] == 7.5  # WHY: the caller timeout must not be dropped.


class TestOpenProbeConnection:
    """Cover the connection factory, which the 405 retry reuses."""

    def test_a_tls_request_builds_an_https_connection(self) -> None:
        """A plain connection on port 443 would fail the handshake."""
        with (
            patch.object(zp, "HTTPSConnection") as https_cls,
            patch.object(ssl, "create_default_context", return_value=MagicMock()),
        ):
            zp._open_probe_connection("gateway.zscaler.net", 443, 3.0, tls=True)
        https_cls.assert_called_once()  # WHY: TLS must route to the HTTPS class.

    def test_a_tls_request_uses_the_system_trust_store(self) -> None:
        """A permissive context would hide a certificate substitution."""
        context = MagicMock()  # WHY: stand in for the default SSL context.
        with (
            patch.object(zp, "HTTPSConnection") as https_cls,
            patch.object(ssl, "create_default_context", return_value=context),
        ):
            zp._open_probe_connection("gateway.zscaler.net", 443, 3.0, tls=True)
        _, kwargs = https_cls.call_args  # WHY: read the connection keywords.
        assert kwargs["context"] is context  # WHY: the verified context must reach the connection.

    def test_a_plain_request_builds_an_http_connection(self) -> None:
        """Port 80 has no TLS layer, so the plain class is correct."""
        with patch.object(zp, "HTTPConnection") as http_cls:
            zp._open_probe_connection("gateway.zscaler.net", 80, 3.0, tls=False)
        http_cls.assert_called_once_with("gateway.zscaler.net", 80, timeout=3.0)


class TestCloseQuietly:
    """Cover the cleanup helper, which must never mask a probe result."""

    def test_a_healthy_connection_closes(self) -> None:
        """The socket must release as soon as the response headers are read."""
        conn = MagicMock()  # WHY: stand in for the HTTP connection object.
        zp._close_quietly(conn)  # WHY: drive the normal cleanup path.
        conn.close.assert_called_once()  # WHY: a skipped close leaks the socket.

    def test_a_failing_close_is_swallowed(self) -> None:
        """A cleanup error must not replace the probe result the caller earned."""
        conn = MagicMock()  # WHY: stand in for the HTTP connection object.
        conn.close.side_effect = OSError("already closed")  # WHY: reproduce a double close.
        zp._close_quietly(conn)  # WHY: the call must return, not raise.


class TestRequestHeadOrGet:
    """Cover the HEAD probe and the 405 retry, which needs a second connection."""

    def test_a_normal_response_returns_without_a_retry(self) -> None:
        """A second request would double the load on every healthy endpoint."""
        conn = MagicMock()  # WHY: stand in for the HTTP connection object.
        conn.getresponse.return_value = MagicMock(status=200)  # WHY: a plain success.
        with patch.object(zp, "_open_probe_connection", return_value=conn) as open_spy:
            response = zp._request_head_or_get("gateway.zscaler.net", 443, 3.0, tls=True)
        assert response.status == 200  # WHY: the first response must reach the caller.
        assert open_spy.call_count == 1  # WHY: exactly one connection for a healthy endpoint.

    def test_a_405_response_retries_with_get_on_a_new_connection(self) -> None:
        """The first connection is consumed, so the retry needs a fresh one."""
        first = MagicMock()  # WHY: the connection that answers 405.
        first.getresponse.return_value = MagicMock(status=405)  # WHY: HEAD is refused.
        second = MagicMock()  # WHY: the connection that carries the GET retry.
        second.getresponse.return_value = MagicMock(status=200)  # WHY: GET succeeds.
        with patch.object(zp, "_open_probe_connection", side_effect=[first, second]) as open_spy:
            response = zp._request_head_or_get("pac.zscaler.net", 443, 3.0, tls=True)
        assert response.status == 200  # WHY: the retry result must reach the caller.
        assert open_spy.call_count == 2  # WHY: a reused connection would raise on request.
        assert second.request.call_args[0][0] == "GET"  # WHY: the retry must change the method.

    def test_the_consumed_connection_closes_before_the_retry(self) -> None:
        """Leaving the 405 connection open would leak one socket for every PAC host."""
        first = MagicMock()  # WHY: the connection that answers 405.
        first.getresponse.return_value = MagicMock(status=405)  # WHY: HEAD is refused.
        second = MagicMock()  # WHY: the connection that carries the GET retry.
        second.getresponse.return_value = MagicMock(status=200)  # WHY: GET succeeds.
        with patch.object(zp, "_open_probe_connection", side_effect=[first, second]):
            zp._request_head_or_get("pac.zscaler.net", 443, 3.0, tls=True)
        first.close.assert_called_once()  # WHY: the consumed connection must release.

    def test_the_last_connection_closes_on_the_success_path(self) -> None:
        """The finally block is the only release point for the returned response."""
        conn = MagicMock()  # WHY: stand in for the HTTP connection object.
        conn.getresponse.return_value = MagicMock(status=200)  # WHY: a plain success.
        with patch.object(zp, "_open_probe_connection", return_value=conn):
            zp._request_head_or_get("gateway.zscaler.net", 443, 3.0, tls=True)
        conn.close.assert_called_once()  # WHY: the finally block must run on success too.

    def test_the_connection_closes_when_the_request_fails(self) -> None:
        """A raised error must still release the socket, or the pool leaks.

        Why:
            This is the resource-cleanup case that a success-only test misses.
        """
        conn = MagicMock()  # WHY: stand in for the HTTP connection object.
        conn.request.side_effect = OSError("reset by peer")  # WHY: fail before the response.
        with patch.object(zp, "_open_probe_connection", return_value=conn):
            with pytest.raises(OSError):  # WHY: the caller catches this one level up.
                zp._request_head_or_get("gateway.zscaler.net", 443, 3.0, tls=True)
        conn.close.assert_called_once()  # WHY: the finally block must run on the error path.


class TestDoHttp:
    """Cover the error translation that keeps the probe report readable."""

    def test_a_success_returns_the_response_and_no_error(self) -> None:
        """The caller reads status and headers off the returned response."""
        response = MagicMock(status=200)  # WHY: stand in for the HTTP response object.
        with patch.object(zp, "_request_head_or_get", return_value=response):
            assert zp._do_http("gateway.zscaler.net", 443, 3.0, tls=True) == (response, None)

    def test_a_timeout_is_labeled_as_a_timeout(self) -> None:
        """A stalled edge reads differently from a refused one in the report."""
        with patch.object(zp, "_request_head_or_get", side_effect=TimeoutError("no reply")):
            response, error = zp._do_http("gateway.zscaler.net", 443, 3.0, tls=True)
        assert response is None  # WHY: no response means no status to record.
        assert error is not None and error.startswith("timeout:")  # WHY: the label drives triage.

    def test_a_tls_failure_is_labeled_as_ssl(self) -> None:
        """A certificate rotation must not hide behind a generic transport error."""
        with patch.object(zp, "_request_head_or_get", side_effect=ssl.SSLError("bad cert")):
            _, error = zp._do_http("gateway.zscaler.net", 443, 3.0, tls=True)
        assert error is not None and error.startswith("ssl:")  # WHY: the label names the layer.

    def test_a_transport_failure_reports_the_class_name(self) -> None:
        """The class name tells the operator which layer refused the probe."""
        with patch.object(zp, "_request_head_or_get", side_effect=ConnectionRefusedError("no")):
            _, error = zp._do_http("gateway.zscaler.net", 443, 3.0, tls=True)
        assert error is not None  # WHY: the reason must survive for the summary.
        assert "ConnectionRefusedError" in error  # WHY: the class name is the triage signal.


class TestTlsPeer:
    """Cover the certificate read, which owns both a socket and a TLS session."""

    @staticmethod
    def _wire_handshake(cert: dict[str, Any]) -> tuple[MagicMock, MagicMock, MagicMock]:
        """Return mocks that emulate a successful handshake returning ``cert``.

        Why:
            Both the raw socket and the wrapped socket are context managers, so
            each test would otherwise repeat six lines of mock plumbing.
        """
        raw = MagicMock()  # WHY: stand in for the plain TCP socket.
        raw.__enter__.return_value = raw  # WHY: the with block binds the same object.
        tls = MagicMock()  # WHY: stand in for the wrapped TLS socket.
        tls.__enter__.return_value = tls  # WHY: the with block binds the same object.
        tls.getpeercert.return_value = cert  # WHY: supply the certificate under test.
        context = MagicMock()  # WHY: stand in for the default SSL context.
        context.wrap_socket.return_value = tls  # WHY: the handshake yields the TLS socket.
        return raw, tls, context

    def test_the_subject_and_the_issuer_are_returned(self) -> None:
        """The issuer common name is the cheapest signal for classifying a host."""
        cert = {
            "subject": ((("commonName", "*.zscaler.net"),),),  # WHY: the served identity.
            "issuer": ((("commonName", "Zscaler Root CA"),),),  # WHY: the signing authority.
        }
        raw, _, context = self._wire_handshake(cert)  # WHY: build the handshake mocks.
        with (
            patch.object(socket, "create_connection", return_value=raw),
            patch.object(ssl, "create_default_context", return_value=context),
        ):
            subject, issuer, error = zp._tls_peer("gateway.zscaler.net", 443, 3.0)
        assert subject == "*.zscaler.net"  # WHY: the subject drives the CloudFront rule.
        assert issuer == "Zscaler Root CA"  # WHY: the issuer drives the Zscaler rule.
        assert error is None  # WHY: a clean handshake reports no error.

    def test_the_hostname_is_sent_as_the_sni_value(self) -> None:
        """Without SNI a shared edge serves the wrong certificate."""
        raw, _, context = self._wire_handshake({})  # WHY: the certificate is not under test.
        with (
            patch.object(socket, "create_connection", return_value=raw),
            patch.object(ssl, "create_default_context", return_value=context),
        ):
            zp._tls_peer("gateway.zscaler.net", 443, 3.0)  # WHY: drive the handshake.
        _, kwargs = context.wrap_socket.call_args  # WHY: read the handshake keywords.
        assert kwargs["server_hostname"] == "gateway.zscaler.net"  # WHY: SNI must match the host.

    def test_both_sockets_close_after_the_handshake(self) -> None:
        """A leaked TLS session holds a socket and a buffer for the whole run."""
        raw, tls, context = self._wire_handshake({})  # WHY: build the handshake mocks.
        with (
            patch.object(socket, "create_connection", return_value=raw),
            patch.object(ssl, "create_default_context", return_value=context),
        ):
            zp._tls_peer("gateway.zscaler.net", 443, 3.0)  # WHY: drive both context managers.
        raw.__exit__.assert_called_once()  # WHY: the plain socket must release.
        tls.__exit__.assert_called_once()  # WHY: the TLS session must release.

    def test_a_missing_certificate_yields_two_none_values(self) -> None:
        """A session without a peer cert must not raise on the dictionary read."""
        raw, tls, context = self._wire_handshake({})  # WHY: build the handshake mocks.
        tls.getpeercert.return_value = None  # WHY: reproduce a session with no peer cert.
        with (
            patch.object(socket, "create_connection", return_value=raw),
            patch.object(ssl, "create_default_context", return_value=context),
        ):
            assert zp._tls_peer("gateway.zscaler.net", 443, 3.0) == (None, None, None)

    def test_a_handshake_timeout_is_labeled(self) -> None:
        """A stalled handshake reads differently from a rejected certificate."""
        with patch.object(socket, "create_connection", side_effect=TimeoutError("slow")):
            _, _, error = zp._tls_peer("gateway.zscaler.net", 443, 3.0)
        assert error is not None and error.startswith("timeout:")  # WHY: the label drives triage.

    def test_a_certificate_rejection_is_labeled_as_ssl(self) -> None:
        """An inspection proxy shows up here as a verification failure."""
        with patch.object(socket, "create_connection", return_value=MagicMock()):
            with patch.object(ssl, "create_default_context", side_effect=ssl.SSLError("bad")):
                _, _, error = zp._tls_peer("gateway.zscaler.net", 443, 3.0)
        assert error is not None and error.startswith("ssl:")  # WHY: the label names the layer.

    def test_a_transport_failure_reports_the_class_name(self) -> None:
        """A refused connection must abort the read, not raise into the worker."""
        with patch.object(socket, "create_connection", side_effect=ConnectionRefusedError("no")):
            _, _, error = zp._tls_peer("gateway.zscaler.net", 443, 3.0)
        assert error is not None  # WHY: the reason must survive for the summary.
        assert "ConnectionRefusedError" in error  # WHY: the class name is the triage signal.


class TestPickCn:
    """Cover the distinguished-name reader, which tolerates a sparse certificate."""

    def test_a_common_name_is_preferred(self) -> None:
        """The common name is the field the classification rules compare against."""
        rdns = ((("commonName", "*.zscaler.net"),),)  # WHY: a plain single-field name.
        assert zp._pick_cn(rdns) == "*.zscaler.net"

    def test_an_organization_name_is_the_fallback(self) -> None:
        """A handful of Zscaler certificate authorities omit the common name."""
        rdns = ((("organizationName", "Zscaler Inc."),),)  # WHY: reproduce the sparse case.
        assert zp._pick_cn(rdns) == "Zscaler Inc."

    def test_an_unrelated_field_is_skipped(self) -> None:
        """A country field must not be mistaken for an identity."""
        # WHY: the country comes first, so a naive reader would return it.
        rdns = ((("countryName", "US"),), (("commonName", "*.zscaler.net"),))
        assert zp._pick_cn(rdns) == "*.zscaler.net"

    def test_an_empty_sequence_returns_nothing(self) -> None:
        """A certificate with no matching field must not raise on the loop."""
        assert zp._pick_cn(()) is None  # WHY: the caller treats None as unknown.

    def test_a_none_sequence_returns_nothing(self) -> None:
        """A missing key in the certificate dictionary reaches this helper as None."""
        assert zp._pick_cn(None) is None  # WHY: the guard must accept None, not raise.

    def test_the_value_is_coerced_to_a_string(self) -> None:
        """A non-string value would break the later substring comparisons."""
        rdns = ((("commonName", 12345),),)  # WHY: mimic an unusual encoder output.
        assert zp._pick_cn(rdns) == "12345"


class TestProbeHttpStack:
    """Cover the HTTP, HTTPS, and proxy blocks that read from the TCP scan."""

    def test_a_closed_port_80_skips_the_http_probe(self) -> None:
        """Probing a closed port wastes a full timeout on every host."""
        result = _make_result()  # WHY: a fresh result with no ports open.
        result.tcp = {80: "closed", 443: "closed"}  # WHY: nothing is open to probe.
        with patch.object(zp, "_do_http") as http_spy:
            zp._probe_http_stack("gateway.zscaler.net", 3.0, [], result)
        http_spy.assert_not_called()  # WHY: the guard must prevent the request.

    def test_an_http_success_records_the_status_and_the_headers(self) -> None:
        """The server header is a classification input, so it must be captured."""
        result = _make_result()  # WHY: a fresh result to populate.
        result.tcp = {80: "open"}  # WHY: only port 80 is open.
        response = MagicMock(status=302)  # WHY: a redirect is the common ZEN answer.
        # WHY: the helper reads two named headers off the response.
        response.getheader.side_effect = lambda name: {
            "Server": "Zscaler",
            "Location": "https://gateway.zscaler.net/",
        }.get(name)
        with patch.object(zp, "_do_http", return_value=(response, None)):
            zp._probe_http_stack("gateway.zscaler.net", 3.0, [], result)
        assert result.http_status == 302  # WHY: the status drives the report row.
        assert result.http_server == "Zscaler"  # WHY: the server header drives classification.
        assert result.http_location == "https://gateway.zscaler.net/"  # WHY: shows the redirect.
        assert "HTTP" in result.responding_protocols  # WHY: the summary lists live protocols.

    def test_an_http_failure_records_a_note(self) -> None:
        """A silent failure would leave the operator with an unexplained gap."""
        result = _make_result()  # WHY: a fresh result to populate.
        result.tcp = {80: "open"}  # WHY: only port 80 is open.
        with patch.object(zp, "_do_http", return_value=(None, "timeout: no reply")):
            zp._probe_http_stack("gateway.zscaler.net", 3.0, [], result)
        assert result.http_status is None  # WHY: a failure leaves no status to record.
        assert any("HTTP :80 error" in note for note in result.notes)  # WHY: the note explains.

    def test_an_https_success_records_the_certificate_and_the_status(self) -> None:
        """The certificate and the status are read in one pass over port 443."""
        result = _make_result()  # WHY: a fresh result to populate.
        result.tcp = {443: "open"}  # WHY: only port 443 is open.
        response = MagicMock(status=200)  # WHY: a plain success on the TLS port.
        response.getheader.return_value = "Zscaler"  # WHY: both headers read the same value.
        with (
            patch.object(zp, "_tls_peer", return_value=("*.zscaler.net", "Zscaler CA", None)),
            patch.object(zp, "_do_http", return_value=(response, None)),
        ):
            zp._probe_http_stack("gateway.zscaler.net", 3.0, [], result)
        assert result.tls_issuer == "Zscaler CA"  # WHY: the issuer drives the Zscaler rule.
        assert result.https_status == 200  # WHY: the status drives the report row.
        assert "HTTPS" in result.responding_protocols  # WHY: the summary lists live protocols.

    def test_an_https_failure_records_a_note(self) -> None:
        """A TLS port that accepts TCP but refuses HTTP must still be explained."""
        result = _make_result()  # WHY: a fresh result to populate.
        result.tcp = {443: "open"}  # WHY: only port 443 is open.
        with (
            patch.object(zp, "_tls_peer", return_value=(None, None, "ssl:bad cert")),
            patch.object(zp, "_do_http", return_value=(None, "ssl:bad cert")),
        ):
            zp._probe_http_stack("gateway.zscaler.net", 3.0, [], result)
        assert result.tls_error == "ssl:bad cert"  # WHY: the handshake error must survive.
        assert any("HTTPS :443 error" in note for note in result.notes)  # WHY: the note explains.

    def test_an_open_declared_proxy_port_is_recorded(self) -> None:
        """The TCP handshake alone proves a ZEN proxy port is live."""
        result = _make_result(declared_ports=[8080])  # WHY: the role declares the proxy port.
        result.tcp = {8080: "open"}  # WHY: the proxy port answered the handshake.
        zp._probe_http_stack("gateway.zscaler.net", 3.0, [8080], result)  # WHY: drive the branch.
        # WHY: the label distinguishes a proxy port from a plain web port in the report.
        assert "TCP/8080 (proxy)" in result.responding_protocols

    def test_an_undeclared_proxy_port_is_not_recorded(self) -> None:
        """An off-doc open port must not be reported as a working proxy."""
        result = _make_result()  # WHY: the role declares no proxy port.
        result.tcp = {8080: "open"}  # WHY: the port answered, but the role did not declare it.
        zp._probe_http_stack("gateway.zscaler.net", 3.0, [], result)  # WHY: drive the guard.
        assert "TCP/8080 (proxy)" not in result.responding_protocols


class TestProbeFqdn:
    """Cover the per-host orchestration, including the DNS short circuit."""

    def test_a_dns_failure_skips_every_later_probe(self) -> None:
        """A name that does not resolve has no address to probe."""
        with (
            patch.object(zp, "_resolve", return_value=(None, "gaierror: unknown")),
            patch.object(zp, "_icmp_ping") as ping_spy,
            patch.object(zp, "_tcp_check") as tcp_spy,
        ):
            result = zp._probe_fqdn("nope.invalid", {"role": "zen"}, 3.0)
        assert result.dns_error is not None  # WHY: the reason reaches the report.
        ping_spy.assert_not_called()  # WHY: an unresolved name wastes a full ping timeout.
        tcp_spy.assert_not_called()  # WHY: an unresolved name wastes three connect timeouts.

    def test_a_successful_ping_is_listed_as_a_protocol(self) -> None:
        """ICMP is the first evidence that a path to the host exists."""
        with (
            patch.object(zp, "_resolve", return_value=("10.0.0.1", None)),
            patch.object(zp, "_icmp_ping", return_value=True),
            patch.object(zp, "_tcp_check", return_value="closed"),
            patch.object(zp, "_probe_http_stack"),
            patch.object(zp, "_probe_udp_ike_if_needed"),
            patch.object(zp, "_classify", return_value="unknown"),
        ):
            result = zp._probe_fqdn("gateway.zscaler.net", {"role": "zen"}, 3.0)
        assert result.icmp_ok is True  # WHY: the flag drives the report column.
        assert "ICMP" in result.responding_protocols  # WHY: the summary lists live protocols.

    def test_the_declared_ports_join_the_common_ports(self) -> None:
        """An off-doc port must be scanned so the report can spot a drift."""
        role = {"role": "zen", "ports": [9443]}  # WHY: a port outside the common tuple.
        with (
            patch.object(zp, "_resolve", return_value=("10.0.0.1", None)),
            patch.object(zp, "_icmp_ping", return_value=False),
            patch.object(zp, "_tcp_check", return_value="closed") as tcp_spy,
            patch.object(zp, "_probe_http_stack"),
            patch.object(zp, "_probe_udp_ike_if_needed"),
            patch.object(zp, "_classify", return_value="unknown"),
        ):
            zp._probe_fqdn("gateway.zscaler.net", role, 3.0)  # WHY: drive the port union.
        scanned = sorted(call[0][1] for call in tcp_spy.call_args_list)  # WHY: read the ports.
        assert scanned == [80, 443, 8080, 9443]  # WHY: the union must be sorted and complete.

    def test_an_open_port_is_listed_as_a_protocol(self) -> None:
        """Each open port earns a line in the responding-protocol summary."""
        with (
            patch.object(zp, "_resolve", return_value=("10.0.0.1", None)),
            patch.object(zp, "_icmp_ping", return_value=False),
            patch.object(zp, "_tcp_check", return_value="open"),
            patch.object(zp, "_probe_http_stack"),
            patch.object(zp, "_probe_udp_ike_if_needed"),
            patch.object(zp, "_classify", return_value="zscaler"),
        ):
            result = zp._probe_fqdn("gateway.zscaler.net", {"role": "zen"}, 3.0)
        assert "TCP/443" in result.responding_protocols  # WHY: the port label must appear.
        assert result.server_class == "zscaler"  # WHY: the classifier result must be stored.


class TestRunProbes:
    """Cover the thread pool, which must join every worker and sort the output."""

    def test_every_entry_produces_a_result(self) -> None:
        """A dropped result would silently shrink the report."""
        # WHY: three entries prove the fan-out collects more than one future.
        entries = [
            ("a.zscaler.net", {"role": "zen"}),
            ("b.zscaler.net", {"role": "zen"}),
            ("c.zscaler.net", {"role": "zen"}),
        ]
        with patch.object(zp, "_probe_fqdn", side_effect=lambda f, r, t: _make_result(fqdn=f)):
            results = zp._run_probes(entries, 3.0, workers=2)
        assert len(results) == 3  # WHY: one result for each submitted entry.

    def test_the_output_is_sorted_by_role_and_then_by_name(self) -> None:
        """An unsorted report changes order between runs and hides a real diff."""
        entries = [
            ("z.zscaler.net", {"role": "zen"}),  # WHY: last by both keys.
            ("a.zscaler.net", {"role": "pac"}),  # WHY: first by role.
            ("b.zscaler.net", {"role": "zen"}),  # WHY: same role as the first entry.
        ]

        def _fake(fqdn: str, role: dict[str, Any], _timeout: float) -> ProbeResult:
            """Return a result carrying the role, so the sort key is real."""
            # WHY: the sort reads role first and fqdn second, so both must be set.
            return _make_result(fqdn=fqdn, role=str(role["role"]))

        with patch.object(zp, "_probe_fqdn", side_effect=_fake):
            results = zp._run_probes(entries, 3.0, workers=3)
        # WHY: pac ranks before zen, then the two zen rows sort by name.
        assert [r.fqdn for r in results] == ["a.zscaler.net", "b.zscaler.net", "z.zscaler.net"]

    def test_the_worker_count_reaches_the_pool(self) -> None:
        """An unbounded pool would open one socket for every catalogue host."""
        entries = [("a.zscaler.net", {"role": "zen"})]  # WHY: one entry is enough.
        with (
            patch.object(zp, "_probe_fqdn", return_value=_make_result()),
            patch.object(zp.concurrent.futures, "ThreadPoolExecutor") as pool_cls,
        ):
            # WHY: an empty iterator keeps the loop body out of this assertion.
            pool_cls.return_value.__enter__.return_value.submit.return_value = MagicMock()
            with patch.object(zp.concurrent.futures, "as_completed", return_value=[]):
                zp._run_probes(entries, 3.0, workers=7)
        _, kwargs = pool_cls.call_args  # WHY: read the pool keywords.
        assert kwargs["max_workers"] == 7  # WHY: the caller bound must not be dropped.

    def test_an_empty_entry_list_returns_no_results(self) -> None:
        """An empty catalogue must return cleanly, not hang on the pool."""
        assert zp._run_probes([], 3.0, workers=4) == []  # WHY: the pool must still close.
