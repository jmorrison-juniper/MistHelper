"""Answers a Net-SNMP `pass_persist` request from the metrics cache.

Why:
    A NOC that runs SNMP keeps its dashboard, its alarm rules, and its on-call
    procedure. Telling that NOC to replace all three is not an upgrade. This
    module keeps the SNMP path, and it drops the four defects that the upstream
    `mist_snmp_gateway` records about its own SNMP agent.

    The upstream binds UDP port 161 itself. Port 161 is privileged, so a Linux
    process must start as root to take it, and MistHelper runs as the non-root
    user `misthelper`. The upstream also holds the community string, and SNMP
    v2c sends that string in clear text. Finally, the upstream MIB claims the
    enterprise OID `.1.3.6.1.4.1.65535`, which is not a registered Private
    Enterprise Number, and its own README warns that the number can collide.

    `pass_persist` removes all four. `snmpd` owns port 161, holds the community
    string or the v3 user, and starts this responder as a child process. The
    operator names the base OID in `snmpd.conf`, so no unregistered number is
    baked into this repository. The protocol is plain text on standard input and
    standard output, so the responder needs no SNMP library at all.

    Configure `snmpd` with one line, choosing a base OID under an enterprise
    number the operator owns:

        pass_persist .1.3.6.1.4.1.8072.9999.9999 /usr/bin/python3 -m MistHelper --metrics-snmp

Warning:
    The responder answers a read only. It replies `not-writable` to every set
    request, because the gateway never changes Mist Cloud.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterator
from typing import IO, TYPE_CHECKING

from src.metrics_gateway.catalog import ROW_IDENTITY_COLUMN, MetricCatalog, MetricKind, MetricScope
from src.metrics_gateway.samples import MetricSample, MetricSnapshot

if TYPE_CHECKING:  # An import for a type only. It must not run, because it would form an import cycle.
    from src.metrics_gateway.cache import MetricsCache

logger = logging.getLogger(__name__)

DEFAULT_BASE_OID = ".1.3.6.1.4.1.8072.9999.9999"  # The Net-SNMP experimental base. No operator has to register it.

PING_REQUEST = "PING"  # `snmpd` sends this to test that the responder is alive.
PING_REPLY = "PONG"  # The only answer that keeps `snmpd` talking to this responder.
GET_REQUEST = "get"  # Read the value at exactly this OID.
GETNEXT_REQUEST = "getnext"  # Read the value at the first OID after this one, which is how a walk moves.
SET_REQUEST = "set"  # Write a value. This responder always refuses.
NO_VALUE_REPLY = "NONE"  # The answer when the OID holds nothing, which ends a walk.
NOT_WRITABLE_REPLY = "not-writable"  # The answer to every set request.

TYPE_STRING = "string"  # Text, used for a name and for a row identity.
TYPE_GAUGE = "gauge"  # An unsigned 32-bit number that rises and falls.
TYPE_COUNTER64 = "counter64"  # An unsigned 64-bit number that only rises. Mist byte counts pass 2^32 in a day.

GAUGE_CEILING = 2**32 - 1  # The largest value an SNMP gauge can carry.
COUNTER64_CEILING = 2**64 - 1  # The largest value an SNMP 64-bit counter can carry.

TABLE_ENTRY_NODE = 1  # Every SNMP table holds its columns under one entry node, by convention numbered 1.
SCALAR_INSTANCE = 0  # Every SNMP scalar answers at instance 0.

OidKey = tuple[int, ...]  # An OID as numbers, so that a sort gives true lexicographic order.


def protect_protocol_streams() -> None:
    """Stop every log record from reaching the two protocol streams.

    Why:
        `snmpd` reads the replies from the pipe it gave this process as standard
        output. It also merges standard error into that same pipe. The net-snmp
        source is explicit about it, in `get_exec_pipes`:

            netsnmp_close_fds(STDOUT_FILENO);
            dup2(STDOUT_FILENO, STDERR_FILENO);

        One log record on either stream therefore lands in the middle of the
        protocol. `snmpd` reads that text where it expected `PONG`, decides the
        helper is broken, closes the pipe, and answers `No Such Instance` for the
        whole subtree. A real `snmpd` reported exactly that:

            open_persist_pipe: Got DEBUG:...Build the metric catalog
            instead of PONG!

        MistHelper configures logging for every mode, so this responder cannot
        assume a quiet stream. It takes the two streams away from logging
        instead. A file handler keeps working, so the audit trail survives.

    Warning:
        Call this before you build the cache and before you build the responder.
        A catalog logs while it builds, so a later call cannot undo a record that
        already reached the pipe.

    Warning:
        This changes the logging configuration of the whole process. It is
        correct here, because a `pass_persist` process exists only to answer
        `snmpd` and owns both streams for its whole life.
    """
    protocol_streams = (sys.stdout, sys.stderr)  # The two channels `snmpd` reads.
    # WHY: this must be a NullHandler and not None. With `lastResort` set to None
    # and no handler found, CPython writes `No handlers could be found for logger`
    # straight to stderr, which corrupts the protocol just as a log record does. A
    # real `snmpd` reported that text in place of `PONG` after the first attempt at
    # this guard used None. A NullHandler discards the record and writes nothing.
    logging.lastResort = logging.NullHandler()
    every_logger: list[logging.Logger] = [logging.getLogger()]  # The root logger holds most handlers.
    for name in list(logging.root.manager.loggerDict):  # A named logger can hold its own handler.
        item = logging.root.manager.loggerDict.get(name)
        if isinstance(item, logging.Logger):  # A placeholder is not a logger and holds no handler.
            every_logger.append(item)
    for owner in every_logger:  # Detach each handler that writes where the protocol lives.
        for handler in list(owner.handlers):
            if isinstance(handler, logging.StreamHandler) and getattr(handler, "stream", None) in protocol_streams:
                owner.removeHandler(handler)


def parse_oid(text: str) -> OidKey:
    """Turn the text of an OID into numbers.

    Why:
        A text sort puts `.10` before `.9`, and a walk built on a text sort
        skips rows. Numbers sort correctly, so the responder holds every OID as
        a tuple of numbers.

    Args:
        text: The OID, with or without a leading dot.

    Returns:
        The sub-identifiers, or an empty tuple when the text is not an OID.
    """
    parts = [part for part in text.strip().split(".") if part]  # A leading dot leaves an empty first part.
    try:  # A malformed request must not stop the responder, because `snmpd` would then lose the whole subtree.
        return tuple(int(part) for part in parts)
    except ValueError:  # A non-numeric sub-identifier cannot name a reading.
        logger.warning("Ignore a request for the malformed OID %s", text)  # Record the bad request.
        return ()


def format_oid(oid: OidKey) -> str:
    """Turn a tuple of numbers back into the text of an OID.

    Args:
        oid: The sub-identifiers.

    Returns:
        The OID text, with the leading dot that `snmpd` expects.
    """
    return "." + ".".join(str(part) for part in oid)


class OidTree:
    """The readings of one snapshot, addressed by OID and held in walk order."""

    def __init__(self, snapshot: MetricSnapshot, base_oid: str = DEFAULT_BASE_OID) -> None:
        """Build the OID tree of one snapshot.

        Args:
            snapshot: The reading to publish.
            base_oid: The base the operator named in `snmpd.conf`.
        """
        self._base = parse_oid(base_oid)  # Every OID in the tree starts with these numbers.
        self._catalog = MetricCatalog()  # The definitions supply the column number and the scale.
        self._values: dict[OidKey, tuple[str, str]] = {}  # The type and the text of each reading, by OID.
        self._build(snapshot)
        self._ordered: list[OidKey] = sorted(self._values)  # A walk reads this list from front to back.
        logger.debug("The OID tree holds %d readings", len(self._ordered))  # Log the size of the tree.

    def _build(self, snapshot: MetricSnapshot) -> None:
        """Fill the tree from every sample of the snapshot.

        Args:
            snapshot: The reading to publish.
        """
        rows_by_scope = {scope: snapshot.row_keys(scope) for scope in MetricScope}  # Fix the row number of each table.
        for sample in snapshot.samples:  # One pass places every reading at its own OID.
            oid = self._oid_for(sample, rows_by_scope[sample.definition.scope])
            if oid:  # A sample whose row left the table between two refreshes has no place in this tree.
                self._values[oid] = self._encode(sample)
        for scope, keys in rows_by_scope.items():  # A table also needs the column that repeats the row identity.
            self._add_identity_column(scope, keys)

    def _add_identity_column(self, scope: MetricScope, keys: tuple[str, ...]) -> None:
        """Publish the row identity of one table as its own column.

        Why:
            SNMP has no label, so a poller that reads row 4 cannot tell which
            site it describes. This column answers that question.

        Args:
            scope: The table to extend.
            keys: The row identities, in row order.
        """
        subtree = self._catalog.subtree(scope)  # The number that follows the base OID for this table.
        for index, key in enumerate(keys, start=1):  # SNMP rows count from 1, not from 0.
            oid = self._base + (subtree, TABLE_ENTRY_NODE, ROW_IDENTITY_COLUMN, index)
            self._values[oid] = (TYPE_STRING, key)

    def _oid_for(self, sample: MetricSample, keys: tuple[str, ...]) -> OidKey | None:
        """Return the OID of one reading.

        Args:
            sample: The reading to place.
            keys: The row identities of the table the reading belongs to.

        Returns:
            The OID, or None when the reading names a row the table does not hold.
        """
        subtree = self._catalog.subtree(sample.definition.scope)  # The number that follows the base OID.
        column = sample.definition.column  # The column number the catalog assigned.
        if not sample.row_key:  # A scalar has no row, so it answers at instance 0 under its column.
            return self._base + (subtree, column, SCALAR_INSTANCE)
        if sample.row_key not in keys:  # The row left the table, so the reading has no address.
            return None
        return self._base + (subtree, TABLE_ENTRY_NODE, column, keys.index(sample.row_key) + 1)

    @staticmethod
    def _encode(sample: MetricSample) -> tuple[str, str]:
        """Turn one reading into an SNMP type and an SNMP value.

        Why:
            SNMP carries whole numbers only, so a fractional reading takes the
            scale factor its catalog entry names. A negative number and a number
            above the type ceiling cannot ride in a gauge, so both become text
            rather than a wrong number.

        Args:
            sample: The reading to encode.

        Returns:
            The SNMP type name and the value as text.
        """
        if sample.text is not None:  # An informational reading carries text, which SNMP sends as a string.
            return (TYPE_STRING, sample.text)
        definition = sample.definition  # The definition names the scale and the metric kind.
        scaled = round(sample.value * definition.snmp_scale)  # SNMP has no fraction, so round after the scale.
        if definition.kind is MetricKind.COUNTER:  # A byte count needs the 64-bit type.
            return (TYPE_COUNTER64, str(min(max(scaled, 0), COUNTER64_CEILING)))
        if 0 <= scaled <= GAUGE_CEILING:  # A gauge is unsigned, so only a value in range may use it.
            return (TYPE_GAUGE, str(scaled))
        return (TYPE_STRING, str(scaled))  # A negative or oversized reading stays true as text.

    def get(self, oid: OidKey) -> tuple[str, str] | None:
        """Return the reading at exactly this OID.

        Args:
            oid: The OID to read.

        Returns:
            The SNMP type and value, or None when the tree holds nothing there.
        """
        return self._values.get(oid)

    def next_oid(self, oid: OidKey) -> OidKey | None:
        """Return the first OID after this one.

        Why:
            `snmpwalk` sends `getnext` again and again until the responder
            answers nothing. The walk therefore depends on this order being
            strict and complete.

        Args:
            oid: The OID the walk has reached.

        Returns:
            The next OID in the tree, or None at the end of the tree.
        """
        for candidate in self._ordered:  # The list is sorted, so the first larger OID is the next one.
            if candidate > oid:
                return candidate
        return None  # The walk has passed the last reading, which ends it.

    def __len__(self) -> int:
        """Return the count of readings the tree holds.

        Returns:
            The number of addressable OIDs.
        """
        return len(self._ordered)


class SnmpPassPersistResponder:
    """Speaks the Net-SNMP `pass_persist` protocol on standard input and output."""

    def __init__(self, cache: MetricsCache, base_oid: str = DEFAULT_BASE_OID) -> None:
        """Store the cache and the base OID.

        Args:
            cache: The source of the reading. It refreshes itself when stale.
            base_oid: The base the operator named in `snmpd.conf`.
        """
        self._cache = cache  # A poll reads memory, so no request reaches Mist Cloud.
        self._base_oid = base_oid  # The operator owns this number, so no unregistered OID is baked in.

    def tree(self) -> OidTree:
        """Build the OID tree of the reading the cache holds now.

        Why:
            One request reads one tree. A walk that spanned two refreshes could
            return a row number that means one device in one step and another
            device in the next.

        Returns:
            The tree for this request.
        """
        return OidTree(self._cache.snapshot(), self._base_oid)

    def handle(self, command: str, argument: str) -> list[str]:
        """Answer one request.

        Args:
            command: The request word, such as `get` or `getnext`.
            argument: The OID the request names, empty for `PING`.

        Returns:
            The reply lines, without their line breaks.
        """
        if command == PING_REQUEST:  # `snmpd` tests the responder before it trusts the subtree.
            return [PING_REPLY]
        if command == SET_REQUEST:  # The gateway is read only, so every write is refused.
            logger.warning("Refuse a set request for %s, because the gateway is read only", argument)
            return [NOT_WRITABLE_REPLY]
        if command == GET_REQUEST:  # Read exactly the named OID.
            return self._reply(parse_oid(argument), exact=True)
        if command == GETNEXT_REQUEST:  # Move the walk one step forward.
            return self._reply(parse_oid(argument), exact=False)
        logger.warning("Ignore the unknown request %s", command)  # A future net-snmp verb must not stop the walk.
        return [NO_VALUE_REPLY]

    def _reply(self, oid: OidKey, exact: bool) -> list[str]:
        """Build the reply to a get request or a getnext request.

        Args:
            oid: The OID the request named.
            exact: True for `get`, and False for `getnext`.

        Returns:
            The three reply lines, or the single line that reports nothing.
        """
        if not oid:  # A malformed OID names no reading, and `NONE` is the honest answer.
            return [NO_VALUE_REPLY]
        tree = self.tree()  # One request reads one snapshot, so a walk cannot mix two refreshes.
        target = oid if exact else tree.next_oid(oid)  # A walk moves forward, and a get stays put.
        found = tree.get(target) if target else None
        if not target or not found:  # The tree holds nothing here, which ends a walk.
            return [NO_VALUE_REPLY]
        snmp_type, value = found  # `snmpd` reads the OID, then the type, then the value.
        return [format_oid(target), snmp_type, value]

    @staticmethod
    def _requests(stream: IO[str]) -> Iterator[tuple[str, str]]:
        """Read one request at a time from the input stream.

        Why:
            `PING` is one line. `get` and `getnext` are two lines, and the OID
            is the second. `set` is three lines. This reader keeps that shape in
            one place, so the handler sees a command and an argument only.

        Warning:
            This loop must call `readline`. A `for line in stream` loop reads
            ahead into an internal buffer, and on a live pipe it blocks until
            that buffer fills. `snmpd` sends one request and then waits for the
            answer, so the read-ahead never fills and neither side moves.
            `snmpd` then treats the helper as dead and stops it, and the whole
            subtree answers `No Such Instance`. A real `snmpd` proved this. No
            test against an in-memory stream can reproduce it, because such a
            stream holds every byte already.

        Args:
            stream: The stream that `snmpd` writes to.

        Yields:
            The command word and its argument.
        """
        while True:  # `snmpd` holds the pipe open, so this loop ends when `snmpd` closes it.
            raw = stream.readline()
            if not raw:  # An empty read means end of file, which is the one clean way out.
                return
            command = raw.strip()
            if not command:  # A blank line carries no request.
                continue
            if command == PING_REQUEST:  # A ping has no argument.
                yield (command, "")
                continue
            argument = (stream.readline() or "").strip()  # Every other request names an OID on the next line.
            if command == SET_REQUEST:  # A set request adds a third line that holds the type and the value.
                stream.readline()
            yield (command, argument)

    def run(self, stdin: IO[str], stdout: IO[str]) -> None:
        """Answer requests until `snmpd` closes the input stream.

        Warning:
            The reply must be flushed after every request. `snmpd` waits for the
            answer before it sends the next request, so a buffered reply stops
            the whole subtree until the buffer fills.

        Args:
            stdin: The stream that `snmpd` writes the requests to.
            stdout: The stream that carries the replies back.
        """
        protect_protocol_streams()  # A backstop. The entry point must already have called this.
        logger.info("Answer Net-SNMP pass_persist requests under the base OID %s", self._base_oid)  # File log only.
        served = 0  # Count the requests, so the log can report the work at the end.
        for command, argument in self._requests(stdin):  # One iteration answers one request.
            for line in self.handle(command, argument):  # A reply is one line or three lines.
                stdout.write(line + "\n")
            stdout.flush()  # `snmpd` blocks until it reads the reply, so the buffer must not hold it.
            served += 1
        logger.info("The pass_persist responder answered %d requests and is stopping", served)  # Log the total.
