"""Tests for the container name resolution preflight.

Why:
    The preflight runs one time, inside a container, before any service starts.
    An operator never sees it work, and a fault in it looks like a Mist API
    outage. These tests therefore cover the decision of every branch, and none
    of them touches a real resolver or a real `/etc/resolv.conf`.
"""

from __future__ import annotations

import socket
import struct
from pathlib import Path

import pytest

from src.bootstrap.dns_preflight import (
    DNS_ANSWER_COUNT_OFFSET,
    ContainerDnsRepair,
    DnsRepairReport,
)

PROBE = "api.mist.com"  # The name the preflight asks about.
HOST_RESOLVER = "10.255.255.254"  # The resolver of a Podman machine under WSL.
PODMAN_PROXY = "172.31.240.1"  # The Podman DNS proxy on the bridge gateway.


def _write(path: Path, *addresses: str) -> Path:
    """Write a resolver file that lists the given addresses.

    Args:
        path: The file to write.
        addresses: The nameserver addresses, in order.

    Returns:
        The path that was written.
    """
    lines = ["# a comment line that the reader must skip", "search example.test"]
    lines.extend(f"nameserver {address}" for address in addresses)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _repair(
    tmp_path: Path,
    container: tuple[str, ...],
    host: tuple[str, ...],
    fallback: tuple[str, ...] = (),
) -> ContainerDnsRepair:
    """Build a repair object over two temporary resolver files.

    Args:
        tmp_path: The folder pytest gave the test.
        container: The addresses the container already holds.
        host: The addresses the host lists.
        fallback: The addresses the operator named.

    Returns:
        The repair object.
    """
    return ContainerDnsRepair(
        probe_host=PROBE,
        container_file=_write(tmp_path / "resolv.conf", *container),
        host_file=_write(tmp_path / "resolv.conf.host", *host),
        fallback_servers=fallback,
    )


class TestReadNameservers:
    """The reader must find every address and skip every other line."""

    def test_it_reads_each_address_in_file_order(self, tmp_path: Path) -> None:
        """The host lists its preferred resolver first, so order carries meaning."""
        path = _write(tmp_path / "resolv.conf", "1.1.1.1", "8.8.8.8")
        assert ContainerDnsRepair.read_nameservers(path) == ("1.1.1.1", "8.8.8.8")

    def test_it_skips_a_comment_and_a_search_line(self, tmp_path: Path) -> None:
        """A resolver file holds more than nameserver lines."""
        path = _write(tmp_path / "resolv.conf", "1.1.1.1")
        assert ContainerDnsRepair.read_nameservers(path) == ("1.1.1.1",)

    def test_it_drops_a_repeated_address(self, tmp_path: Path) -> None:
        """A repeated address would make the preflight test the same resolver twice."""
        path = tmp_path / "resolv.conf"
        path.write_text("nameserver 1.1.1.1\nnameserver 1.1.1.1\n", encoding="utf-8")
        assert ContainerDnsRepair.read_nameservers(path) == ("1.1.1.1",)

    def test_a_missing_file_gives_an_empty_result(self, tmp_path: Path) -> None:
        """The operator can skip the bind mount, and the container must still start."""
        assert ContainerDnsRepair.read_nameservers(tmp_path / "absent.conf") == ()

    def test_a_directory_gives_an_empty_result(self, tmp_path: Path) -> None:
        """A compose provider creates a folder when the bind mount source is absent.

        That happens on Windows and on macOS, where the provider resolves the
        source path on the workstation. The reader must treat the folder as no
        file at all, and it must not raise.
        """
        folder = tmp_path / "resolv.conf.host"
        folder.mkdir()
        assert ContainerDnsRepair.read_nameservers(folder) == ()


class TestBuildQuery:
    """The query bytes must form a valid DNS question."""

    def test_it_asks_one_question(self) -> None:
        """A resolver ignores a packet whose question count is wrong."""
        packet = ContainerDnsRepair.build_query(PROBE)
        assert struct.unpack("!H", packet[4:6])[0] == 1

    def test_it_writes_each_label_after_its_length(self) -> None:
        """A DNS name carries no dot. Each label follows a length byte."""
        packet = ContainerDnsRepair.build_query(PROBE)
        assert b"\x03api\x04mist\x03com\x00" in packet

    def test_it_ends_with_the_type_and_the_class(self) -> None:
        """The preflight asks for an address record of the internet class."""
        packet = ContainerDnsRepair.build_query(PROBE)
        assert packet[-4:] == struct.pack("!HH", 1, 1)


class TestCandidates:
    """A candidate must be able to repair the fault the container just hit."""

    def test_it_offers_a_host_address_the_container_lacks(self, tmp_path: Path) -> None:
        """This is the case the whole module exists to repair."""
        repair = _repair(tmp_path, (PODMAN_PROXY,), (HOST_RESOLVER,))
        assert repair.candidates() == (HOST_RESOLVER,)

    def test_it_skips_an_address_the_container_already_holds(self, tmp_path: Path) -> None:
        """The container failed with that address, so adding it again repairs nothing."""
        repair = _repair(tmp_path, (PODMAN_PROXY, HOST_RESOLVER), (HOST_RESOLVER,))
        assert repair.candidates() == ()

    def test_it_skips_a_loopback_address(self, tmp_path: Path) -> None:
        """A host that runs systemd-resolved lists 127.0.0.53, which answers nothing here."""
        repair = _repair(tmp_path, (PODMAN_PROXY,), ("127.0.0.53", HOST_RESOLVER))
        assert repair.candidates() == (HOST_RESOLVER,)

    def test_it_keeps_the_host_order(self, tmp_path: Path) -> None:
        """The host lists its preferred resolver first."""
        repair = _repair(tmp_path, (PODMAN_PROXY,), ("9.9.9.9", HOST_RESOLVER))
        assert repair.candidates() == ("9.9.9.9", HOST_RESOLVER)

    def test_the_operator_list_comes_before_the_host_list(self, tmp_path: Path) -> None:
        """An operator who names a resolver knows the network better than the file does."""
        repair = _repair(tmp_path, (PODMAN_PROXY,), (HOST_RESOLVER,), fallback=("9.9.9.9",))
        assert repair.candidates() == ("9.9.9.9", HOST_RESOLVER)

    def test_it_drops_an_address_that_both_lists_name(self, tmp_path: Path) -> None:
        """A repeat costs a probe and repairs nothing."""
        repair = _repair(tmp_path, (PODMAN_PROXY,), (HOST_RESOLVER,), fallback=(HOST_RESOLVER,))
        assert repair.candidates() == (HOST_RESOLVER,)

    def test_the_operator_list_alone_is_enough(self, tmp_path: Path) -> None:
        """macOS and Windows cannot mount the host resolver list, so this is the usual case."""
        repair = ContainerDnsRepair(
            probe_host=PROBE,
            container_file=_write(tmp_path / "resolv.conf", PODMAN_PROXY),
            host_file=tmp_path / "absent.conf",
            fallback_servers=("1.1.1.1", "8.8.8.8"),
        )
        assert repair.candidates() == ("1.1.1.1", "8.8.8.8")


class TestFromEnvironment:
    """The compose file supplies the settings, so the reader must parse them."""

    def test_it_reads_the_comma_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The compose file writes the addresses as one comma list."""
        monkeypatch.setenv("DNS_FALLBACK_SERVERS", "1.1.1.1, 8.8.8.8")
        monkeypatch.setattr(ContainerDnsRepair, "read_nameservers", staticmethod(lambda _path: ()))
        assert ContainerDnsRepair.from_environment().candidates() == ("1.1.1.1", "8.8.8.8")

    def test_an_empty_value_turns_the_repair_off(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An operator who wants no repair sets the variable to an empty value."""
        monkeypatch.setenv("DNS_FALLBACK_SERVERS", "")
        monkeypatch.setattr(ContainerDnsRepair, "read_nameservers", staticmethod(lambda _path: ()))
        assert ContainerDnsRepair.from_environment().candidates() == ()

    def test_it_drops_a_blank_list_entry(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A trailing comma must not produce an empty address."""
        monkeypatch.setenv("DNS_FALLBACK_SERVERS", "1.1.1.1,,")
        monkeypatch.setattr(ContainerDnsRepair, "read_nameservers", staticmethod(lambda _path: ()))
        assert ContainerDnsRepair.from_environment().candidates() == ("1.1.1.1",)

    def test_it_reads_the_mist_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A Mist cloud outside the global one uses another host name."""
        monkeypatch.setenv("MIST_HOST", "api.eu.mist.com")
        assert ContainerDnsRepair.from_environment().build_query("api.eu.mist.com").endswith(struct.pack("!HH", 1, 1))


class TestAddNameserver:
    """The writer must append and never replace."""

    def test_it_keeps_every_address_the_file_already_held(self, tmp_path: Path) -> None:
        """The Podman proxy answers every container name, so it must survive the repair."""
        repair = _repair(tmp_path, (PODMAN_PROXY,), (HOST_RESOLVER,))
        assert repair.add_nameserver(HOST_RESOLVER) is True
        assert ContainerDnsRepair.read_nameservers(tmp_path / "resolv.conf") == (PODMAN_PROXY, HOST_RESOLVER)

    def test_a_failed_write_reports_false(self, tmp_path: Path) -> None:
        """A read-only mount must warn and never raise."""
        repair = ContainerDnsRepair(
            probe_host=PROBE,
            container_file=tmp_path / "no-such-folder" / "resolv.conf",
            host_file=_write(tmp_path / "resolv.conf.host", HOST_RESOLVER),
        )
        assert repair.add_nameserver(HOST_RESOLVER) is False


class TestRepair:
    """The preflight must repair the fault, and it must change nothing otherwise."""

    def test_a_working_container_is_left_alone(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """The common case. A correct network needs no repair and no log noise."""
        repair = _repair(tmp_path, (PODMAN_PROXY,), (HOST_RESOLVER,))
        monkeypatch.setattr(ContainerDnsRepair, "resolves_now", lambda _self: True)
        report = repair.repair()
        assert report.already_working is True
        assert report.added == ()
        assert ContainerDnsRepair.read_nameservers(tmp_path / "resolv.conf") == (PODMAN_PROXY,)

    def test_it_adds_the_first_resolver_that_answers(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A resolver that answers repairs the container, and the walk stops there."""
        repair = _repair(tmp_path, (PODMAN_PROXY,), ("9.9.9.9", HOST_RESOLVER))
        monkeypatch.setattr(ContainerDnsRepair, "resolves_now", lambda _self: False)
        monkeypatch.setattr(ContainerDnsRepair, "query", lambda _self, server: server == HOST_RESOLVER)
        report = repair.repair()
        assert report.added == (HOST_RESOLVER,)
        assert report.rejected == ("9.9.9.9",)
        assert report.resolved is True

    def test_a_repair_reports_success_although_the_process_still_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """glibc reads /etc/resolv.conf one time for each process and caches it.

        A second lookup inside this process therefore fails after a correct
        repair. A real container appended a working resolver, the second lookup
        still failed, and the report named that success as a failure. The report
        must read the proof from the probe and the write, not from a new lookup.
        """
        repair = _repair(tmp_path, (PODMAN_PROXY,), (HOST_RESOLVER,))
        monkeypatch.setattr(ContainerDnsRepair, "resolves_now", lambda _self: False)  # Always fails, as glibc does.
        monkeypatch.setattr(ContainerDnsRepair, "query", lambda _self, _server: True)
        report = repair.repair()
        assert report.added == (HOST_RESOLVER,)
        assert report.resolved is True
        assert "WARNING" not in report.describe()

    def test_it_reports_every_rejected_address(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """The operator needs the list of addresses the container tried."""
        repair = _repair(tmp_path, (PODMAN_PROXY,), ("9.9.9.9", HOST_RESOLVER))
        monkeypatch.setattr(ContainerDnsRepair, "resolves_now", lambda _self: False)
        monkeypatch.setattr(ContainerDnsRepair, "query", lambda _self, _server: False)
        report = repair.repair()
        assert report.resolved is False
        assert report.rejected == ("9.9.9.9", HOST_RESOLVER)

    def test_no_candidate_still_returns_a_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A missing bind mount must produce a message, never an exception."""
        repair = _repair(tmp_path, (PODMAN_PROXY,), ())
        monkeypatch.setattr(ContainerDnsRepair, "resolves_now", lambda _self: False)
        report = repair.repair()
        assert report.resolved is False
        assert report.added == ()
        assert report.rejected == ()


class TestQuery:
    """The resolver probe must treat every network fault as a plain failure."""

    def test_a_timeout_reports_false(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A container start must never wait on an unreachable resolver."""
        repair = _repair(tmp_path, (PODMAN_PROXY,), (HOST_RESOLVER,))

        class _Silent:
            """A socket that always times out."""

            def __enter__(self) -> _Silent:
                return self

            def __exit__(self, *_args: object) -> None:
                return None

            def settimeout(self, _seconds: float) -> None:
                return None

            def sendto(self, _packet: bytes, _address: tuple[str, int]) -> None:
                return None

            def recvfrom(self, _size: int) -> tuple[bytes, tuple[str, int]]:
                raise TimeoutError("no reply")

        monkeypatch.setattr(socket, "socket", lambda *_a, **_k: _Silent())
        assert repair.query(HOST_RESOLVER) is False

    def test_a_reply_with_no_answer_reports_false(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A resolver that returns zero answers cannot resolve the Mist host."""
        repair = _repair(tmp_path, (PODMAN_PROXY,), (HOST_RESOLVER,))
        empty = bytearray(12)  # A header with an answer count of zero.

        class _Empty:
            """A socket that returns a reply holding no answer record."""

            def __enter__(self) -> _Empty:
                return self

            def __exit__(self, *_args: object) -> None:
                return None

            def settimeout(self, _seconds: float) -> None:
                return None

            def sendto(self, _packet: bytes, _address: tuple[str, int]) -> None:
                return None

            def recvfrom(self, _size: int) -> tuple[bytes, tuple[str, int]]:
                return (bytes(empty), (HOST_RESOLVER, 53))

        monkeypatch.setattr(socket, "socket", lambda *_a, **_k: _Empty())
        assert repair.query(HOST_RESOLVER) is False

    def test_a_reply_with_an_answer_reports_true(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """One answer record proves the resolver can serve the container."""
        repair = _repair(tmp_path, (PODMAN_PROXY,), (HOST_RESOLVER,))
        filled = bytearray(12)
        filled[DNS_ANSWER_COUNT_OFFSET : DNS_ANSWER_COUNT_OFFSET + 2] = struct.pack("!H", 2)

        class _Answering:
            """A socket that returns a reply holding two answer records."""

            def __enter__(self) -> _Answering:
                return self

            def __exit__(self, *_args: object) -> None:
                return None

            def settimeout(self, _seconds: float) -> None:
                return None

            def sendto(self, _packet: bytes, _address: tuple[str, int]) -> None:
                return None

            def recvfrom(self, _size: int) -> tuple[bytes, tuple[str, int]]:
                return (bytes(filled), (HOST_RESOLVER, 53))

        monkeypatch.setattr(socket, "socket", lambda *_a, **_k: _Answering())
        assert repair.query(HOST_RESOLVER) is True


class TestReportText:
    """The container log carries one line, so that line must name the outcome."""

    def test_a_working_container_says_no_repair_is_needed(self) -> None:
        """An operator reading the log must not think a repair ran."""
        report = DnsRepairReport(already_working=True, added=(), rejected=(), resolved=True)
        assert "No repair is needed" in report.describe()

    def test_a_repair_names_the_address_it_added(self) -> None:
        """The operator needs to know which resolver the container now uses."""
        report = DnsRepairReport(already_working=False, added=(HOST_RESOLVER,), rejected=(), resolved=True)
        assert HOST_RESOLVER in report.describe()

    def test_a_repair_after_a_blocked_resolver_reports_the_success(self) -> None:
        """A repair that walks past a blocked resolver fills `added` and `rejected`.

        A message built from `rejected` alone then reports a failure after a
        success. A real container printed "no resolver answered. Tried:
        1.1.1.1" while the repair had already added 8.8.8.8.
        """
        report = DnsRepairReport(
            already_working=False,
            added=("8.8.8.8",),
            rejected=("1.1.1.1",),
            resolved=True,
        )
        text = report.describe()
        assert "Added the resolver 8.8.8.8" in text
        assert "WARNING" not in text
        assert "1.1.1.1" in text  # The blocked address still points at a firewall rule.

    def test_a_failure_warns_and_names_every_attempt(self) -> None:
        """A silent failure would look like a Mist Cloud outage."""
        report = DnsRepairReport(already_working=False, added=(), rejected=("9.9.9.9",), resolved=False)
        text = report.describe()
        assert "WARNING" in text
        assert "9.9.9.9" in text

    def test_a_failure_without_a_candidate_still_warns(self) -> None:
        """A missing bind mount must produce a readable message."""
        report = DnsRepairReport(already_working=False, added=(), rejected=(), resolved=False)
        assert "WARNING" in report.describe()
