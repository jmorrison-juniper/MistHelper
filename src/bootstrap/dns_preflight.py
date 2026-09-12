"""Repairs container name resolution before the services start.

Why:
    The container must resolve `api.mist.com`. Under Podman the container
    receives one nameserver, the address of the Podman DNS proxy on the bridge
    gateway. That proxy answers a container name such as `misthelper-app`, and
    it forwards every other name to an upstream resolver. When the network holds
    no upstream resolver, the proxy forwards nothing, and every Mist API call
    fails with `Temporary failure in name resolution`.

    An operator can repair that from the command line:

        podman network update misthelper-network --dns-add <address>

    That command is manual, and `compose down` discards the network, so the
    repair does not survive a restart. This module removes the manual step. The
    container reads the resolver list of the host, tests each address, and adds
    the first address that answers to its own resolver list.

    The compose file names the candidate resolvers in `DNS_FALLBACK_SERVERS`.
    The default holds two public resolvers. An operator whose network blocks a
    public resolver names an internal resolver there instead, and an operator
    who wants no repair at all sets the variable to an empty value.

    On a Linux host the container can also read the host resolver list, when the
    operator mounts it at `/etc/resolv.conf.host`. That mount is optional. It
    does not work on macOS or on Windows, because the compose provider resolves
    the source path on the workstation, where the file does not exist.

Warning:
    This module edits `/etc/resolv.conf` inside the container. It never edits a
    file on the host. It appends a nameserver line and removes none, so the
    Podman proxy stays first and every container name still resolves.

Warning:
    The repair runs only after the container already failed to resolve the name.
    It therefore cannot take a working lookup away from an internal resolver.
"""

from __future__ import annotations

import logging
import os
import socket
import struct
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

CONTAINER_RESOLVER_FILE = Path("/etc/resolv.conf")  # The list the container reads.
HOST_RESOLVER_FILE = Path("/etc/resolv.conf.host")  # The optional host list, on a Linux host only.

FALLBACK_VARIABLE = "DNS_FALLBACK_SERVERS"  # A comma list of resolver addresses.
PROBE_HOST_VARIABLE = "MIST_HOST"  # The Mist Cloud host, which the rest of MistHelper already sets.

DEFAULT_PROBE_HOST = "api.mist.com"  # The name that must resolve for the Mist API to answer.
PROBE_TIMEOUT_SECONDS = 3.0  # A resolver that is slower than this cannot serve an interactive tool.
DNS_PORT = 53  # The port every DNS resolver listens on.
DNS_RESPONSE_HEADER_BYTES = 12  # A DNS reply carries a fixed header of this size.
DNS_ANSWER_COUNT_OFFSET = 6  # The answer count sits at this offset of the header.
DNS_QUERY_IDENTIFIER = 0x4D48  # Any value works. This one spells "MH" for MistHelper.

# WHY: A loopback address inside the container reaches the container itself, not
# the host. A host that runs systemd-resolved lists 127.0.0.53, and that address
# answers nothing here. Skip every address in these two ranges.
UNREACHABLE_PREFIXES = ("127.", "0.")


@dataclass(frozen=True, slots=True)
class DnsRepairReport:
    """The outcome of one preflight.

    Attributes:
        already_working: True when the container resolved the name with the
            resolver list it already had. No repair ran.
        added: The resolver addresses that the preflight added.
        rejected: The candidate addresses that answered nothing.
        resolved: True when the container can resolve the name now.
    """

    already_working: bool
    added: tuple[str, ...]
    rejected: tuple[str, ...]
    resolved: bool

    def describe(self) -> str:
        """Return one line that an operator can read in the container log.

        Warning:
            Test `added` before `rejected`. A repair that walks past two blocked
            resolvers fills both fields, and a message built from `rejected`
            alone then reports a failure after a success. A real container
            printed "no resolver answered. Tried: 1.1.1.1" while the repair had
            already added 8.8.8.8 and name resolution worked.

        Returns:
            The summary line.
        """
        if self.already_working:  # The common case on a correctly configured network.
            return "[DNS] The container resolves external names. No repair is needed."
        if self.added:  # The repair worked, so name the address that fixed it.
            line = f"[DNS] Added the resolver {', '.join(self.added)}. External names resolve now."
            if self.rejected:  # Name the blocked addresses too, because they point at a firewall rule.
                line += f" These answered nothing: {', '.join(self.rejected)}."
            return line
        if self.rejected:  # Every candidate failed, so name them for the operator.
            return f"[DNS] WARNING: no resolver answered. Tried: {', '.join(self.rejected)}."
        return "[DNS] WARNING: the container cannot resolve external names, and it found no candidate resolver."


class ContainerDnsRepair:
    """Tests container name resolution and adds a working resolver when it fails."""

    def __init__(
        self,
        probe_host: str = DEFAULT_PROBE_HOST,
        container_file: Path = CONTAINER_RESOLVER_FILE,
        host_file: Path = HOST_RESOLVER_FILE,
        fallback_servers: tuple[str, ...] = (),
    ) -> None:
        """Store the name to test, the two resolver files, and the fallback list.

        Args:
            probe_host: The name that must resolve.
            container_file: The resolver list the container reads.
            host_file: The optional host resolver list, read only.
            fallback_servers: The addresses the operator named.
        """
        self._probe_host = probe_host  # The one name that decides whether a repair is needed.
        self._container_file = container_file  # The file this class may edit.
        self._host_file = host_file  # The file this class only reads.
        self._fallback_servers = fallback_servers  # The operator preference, tried before the host file.

    @classmethod
    def from_environment(cls) -> ContainerDnsRepair:
        """Build the repair object from the container environment.

        Returns:
            The repair object, with the probe host and the fallback list that
            the compose file supplies.
        """
        probe = (os.environ.get(PROBE_HOST_VARIABLE) or "").strip() or DEFAULT_PROBE_HOST
        raw = os.environ.get(FALLBACK_VARIABLE) or ""  # An unset value and a blank value are the same.
        servers = tuple(part.strip() for part in raw.split(",") if part.strip())  # Drop a blank list entry.
        logger.debug("The fallback list holds %d address(es)", len(servers))  # Log the parsed count.
        return cls(probe_host=probe, fallback_servers=servers)

    @staticmethod
    def read_nameservers(path: Path) -> tuple[str, ...]:
        """Return every nameserver address of a resolver file.

        Args:
            path: The resolver file to read.

        Returns:
            The addresses, in the order the file lists them. A path that is not
            a readable file gives an empty result, because the mount is optional
            and a missing mount must not stop the container.
        """
        if not path.is_file():  # A compose provider creates a folder when the source path is absent.
            logger.debug("No resolver file exists at %s", path)  # Not a fault. The mount is optional.
            return ()
        try:  # A permission fault is possible, and it must warn and never raise.
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as fault:  # An unreadable file must warn and never raise.
            logger.warning("Could not read the resolver file %s: %s", path, fault)
            return ()
        found: list[str] = []  # Collect the addresses in file order, because order is preference.
        for line in text.splitlines():
            parts = line.split()  # A nameserver line holds the keyword and then the address.
            if len(parts) >= 2 and parts[0] == "nameserver" and parts[1] not in found:
                found.append(parts[1])
        return tuple(found)

    @staticmethod
    def build_query(name: str) -> bytes:
        """Build a DNS question that asks one resolver for an address.

        Why:
            The image installs no `dig` and no `nslookup`. The standard library
            has no way to ask one named resolver either, because `getaddrinfo`
            always reads `/etc/resolv.conf`. This method builds the question
            itself, which is 30 lines of bytes and no new dependency.

        Args:
            name: The name to ask about.

        Returns:
            The DNS query packet.
        """
        header = struct.pack(
            "!HHHHHH",
            DNS_QUERY_IDENTIFIER,  # The identifier, which the reply repeats.
            0x0100,  # The flags. This value asks the resolver to do the work.
            1,  # One question follows.
            0,  # No answer travels in a question.
            0,  # No authority record travels in a question.
            0,  # No additional record travels in a question.
        )
        body = b"".join(
            bytes([len(label)]) + label.encode("ascii")  # A DNS name writes each label after its length.
            for label in name.split(".")
            if label
        )
        return header + body + b"\x00" + struct.pack("!HH", 1, 1)  # The root label, then type A and class IN.

    def query(self, server: str) -> bool:
        """Ask one resolver for the probe name and report whether it answered.

        Args:
            server: The resolver address to ask.

        Returns:
            True when the resolver returned at least one answer record.
        """
        logger.info("Test the resolver %s with the name %s", server, self._probe_host)  # Log before the test.
        try:  # A resolver that refuses or times out is a normal outcome here, never a fault.
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
                probe.settimeout(PROBE_TIMEOUT_SECONDS)  # A slow resolver must not hold the container start.
                probe.sendto(self.build_query(self._probe_host), (server, DNS_PORT))
                reply, _address = probe.recvfrom(512)  # A 512-byte buffer holds every reply to an A question.
        except OSError as fault:  # A timeout, a refusal, and an unreachable address all land here.
            logger.debug("The resolver %s did not answer: %s", server, fault)  # Log the failure detail.
            return False
        if len(reply) < DNS_RESPONSE_HEADER_BYTES:  # A short reply carries no answer count.
            return False
        answers = int(struct.unpack("!H", reply[DNS_ANSWER_COUNT_OFFSET : DNS_ANSWER_COUNT_OFFSET + 2])[0])
        logger.debug("The resolver %s returned %d answer records", server, answers)  # Log the result count.
        return answers > 0

    def resolves_now(self) -> bool:
        """Report whether the container resolves the probe name with its current settings.

        Returns:
            True when name resolution already works.
        """
        logger.info("Test whether the container resolves %s", self._probe_host)  # Log before the test.
        try:  # A failure is the case this whole module exists to repair.
            socket.getaddrinfo(self._probe_host, None, family=socket.AF_INET)
        except OSError as fault:  # The name did not resolve, so a repair may be needed.
            logger.debug("The container could not resolve %s: %s", self._probe_host, fault)
            return False
        return True

    def candidates(self) -> tuple[str, ...]:
        """Return the resolver addresses that the container may try.

        Why:
            The operator list comes first, because an operator who names a
            resolver knows the network. The host resolver list comes second, and
            it is present on a Linux host only.

            An address the container already holds cannot repair anything,
            because the container just failed with it. A loopback address
            reaches the container itself, so it cannot reach a host resolver.

        Returns:
            The candidate addresses, in preference order and without a repeat.
        """
        current = set(self.read_nameservers(self._container_file))  # The addresses that already failed.
        usable: list[str] = []  # Collect in preference order, because the first answer wins.
        for address in self._fallback_servers + self.read_nameservers(self._host_file):
            if address in current or address in usable:  # A repeat costs a probe and repairs nothing.
                continue
            if address.startswith(UNREACHABLE_PREFIXES):  # A loopback address reaches the container itself.
                logger.debug("Skip the resolver %s, because a container cannot reach it", address)
                continue
            usable.append(address)
        return tuple(usable)

    def add_nameserver(self, server: str) -> bool:
        """Append one nameserver line to the container resolver list.

        Args:
            server: The resolver address to add.

        Returns:
            True when the write succeeded.
        """
        logger.info("Add the resolver %s to %s", server, self._container_file)  # Log before the write.
        try:  # A read-only mount is possible, so a failed write must warn and never raise.
            with self._container_file.open("a", encoding="utf-8") as target:
                target.write(f"nameserver {server}\n")
        except OSError as fault:  # The container cannot repair itself, and the caller reports that.
            logger.warning("Could not write %s: %s", self._container_file, fault)
            return False
        logger.debug("The resolver %s is now in the container resolver list", server)  # Log the result.
        return True

    def repair(self) -> DnsRepairReport:
        """Test name resolution and repair it when it fails.

        Returns:
            The report of what the preflight found and what it changed.
        """
        if self.resolves_now():  # The network is already correct, which is the common case.
            return DnsRepairReport(already_working=True, added=(), rejected=(), resolved=True)
        logger.warning("The container cannot resolve %s. Look for a working resolver.", self._probe_host)
        rejected: list[str] = []  # Name every failed candidate, so the operator can see the attempt.
        for address in self.candidates():  # Stop at the first address that answers and that writes.
            if not self.query(address):
                rejected.append(address)
                continue
            if not self.add_nameserver(address):  # The address works, but the file refused the write.
                rejected.append(address)
                continue
            return DnsRepairReport(
                already_working=False,
                added=(address,),
                rejected=tuple(rejected),
                # WHY: this reports the proof, not a second lookup. The resolver
                # already answered the probe name in `query` above, and the write
                # above put it in the file, so every process that starts after
                # this one resolves the name. A second `resolves_now` call here
                # returns a false negative, because glibc reads
                # `/etc/resolv.conf` one time for each process and caches the
                # result. A real container proved that: it appended a working
                # resolver, the check still failed, and the report then named a
                # success as a failure.
                resolved=True,
            )
        return DnsRepairReport(already_working=False, added=(), rejected=tuple(rejected), resolved=False)


def main() -> int:
    """Run the preflight and print one line for the container log.

    Why:
        The container start script calls this. It prints a single line, and it
        always reports success, because a container that cannot resolve a name
        must still start. The portal then reports the fault to the operator, and
        that is a clearer message than a container that never starts.

    Returns:
        Always 0, so a failed repair never stops the container.
    """
    logging.basicConfig(level=logging.WARNING, format="%(message)s")  # One line only, because bash prints it.
    report = ContainerDnsRepair.from_environment().repair()  # The class holds every decision.
    print(report.describe())  # The start script sends this line to the container log.
    return 0


if __name__ == "__main__":  # The start script runs this module directly.
    raise SystemExit(main())
