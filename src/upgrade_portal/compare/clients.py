"""The client comparison between two upgrade captures.

Why:
    The operator asks one question after an upgrade. Did every client
    return? A client that roamed to another access point did return, so the
    comparison reports it as ``moved``. ``moved`` is its own statistic and
    never a loss. A comparison that counted a roam as a loss would raise a
    false alarm on every busy site.

    The match key is the client address alone. A composite registry key joins
    the endpoint, the address, and a timestamp with a colon
    (``src/db/redis_writer.py:627``). A comparison that matched on the whole
    key would see a new key on every capture and would report the whole site
    as new. This module therefore strips the timestamp from the key and keeps
    the address.

    The module reads the three client digests first. A section whose digest
    matched is equal, so the comparison skips it and names it in
    ``skipped_sections``.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from src.upgrade_portal.capture.clients import normalize_mac
from src.upgrade_portal.compare.diff import matched_sections

logger = logging.getLogger(__name__)

# The four client outcomes of data-model.md section 7.3.
OUTCOME_PRESENT = "present"
OUTCOME_MOVED = "moved"
OUTCOME_ADDED = "added"
OUTCOME_MISSING = "missing"

CLIENT_OUTCOMES = (OUTCOME_PRESENT, OUTCOME_MOVED, OUTCOME_ADDED, OUTCOME_MISSING)

# WHY: Only these outcomes mean the client did not return. A roam is not a
# loss, so ``moved`` stays out of this group.
LOSS_OUTCOMES = (OUTCOME_MISSING,)

CLIENTS_KEY = "clients"

KIND_WIRED = "wired"
KIND_WIRELESS = "wireless"
KIND_GUEST = "guest"
CLIENT_KINDS = (KIND_WIRED, KIND_WIRELESS, KIND_GUEST)

SECTION_CLIENTS_WIRED = "clients_wired"
SECTION_CLIENTS_WIRELESS = "clients_wireless"
SECTION_CLIENTS_GUEST = "clients_guest"
CLIENT_SECTIONS = (SECTION_CLIENTS_WIRED, SECTION_CLIENTS_WIRELESS, SECTION_CLIENTS_GUEST)

SECTION_FOR_KIND = {
    KIND_WIRED: SECTION_CLIENTS_WIRED,
    KIND_WIRELESS: SECTION_CLIENTS_WIRELESS,
    KIND_GUEST: SECTION_CLIENTS_GUEST,
}

MAC_KEY = "mac"
HOSTNAME_KEY = "hostname"
DEVICE_MAC_KEY = "device_mac"
DEVICE_NAME_KEY = "device_name"

# WHY: The registry joins the key parts with a colon. The other separators
# appear in hand written keys and in file names, so the reader accepts them
# all rather than trusting one writer.
_KEY_SEPARATORS = re.compile(r"[:|#@/~!,;\s]+")

# WHY: The same separator set that the capture path removes from an address.
_ADDRESS_SEPARATORS = str.maketrans("", "", ":-. \t")

# WHY: An address is 12 hexadecimal characters. The pattern finds one inside a
# key that joins the address to a timestamp with nothing between them.
_EMBEDDED_ADDRESS = re.compile(r"[0-9a-f]{12}")


# ---------------------------------------------------------------------------
# View records
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ClientMove:
    """The device that served one client before and after.

    Why:
        A move is the difference between two serving devices, so both values
        belong in one record. The Five-Item Rule caps a dataclass at 5 fields,
        and this group keeps ``ClientDelta`` inside the cap.

    Attributes:
        before_device: The serving device address in the pre-check capture.
        after_device: The serving device address in the post-check capture.
        before_name: The serving device name in the pre-check capture.
        after_name: The serving device name in the post-check capture.
    """

    before_device: str = ""
    after_device: str = ""
    before_name: str = ""
    after_name: str = ""

    @property
    def moved(self) -> bool:
        """Return whether the serving device changed.

        Why:
            An absent address on either side proves nothing. Calling an absent
            address a move would report a roam that never happened, so the
            test needs both addresses.

        Returns:
            True only when both addresses are known and they differ.
        """
        if not self.before_device or not self.after_device:
            return False
        return self.before_device != self.after_device


@dataclass(frozen=True, slots=True)
class ClientDelta:
    """One client of the union of the two client lists.

    Why:
        The operator reads a client row to find a client that did not return.
        The row therefore carries the name, the kind of client, and the two
        serving devices, so the operator needs no second look at the captures.

    Attributes:
        mac: The client address, in lower case with no separator.
        outcome: One value of ``CLIENT_OUTCOMES``.
        hostname: The client name, from the later capture that holds it.
        kind: ``wired``, ``wireless``, or ``guest``.
        move: The serving device before and after.
    """

    mac: str
    outcome: str
    hostname: str = ""
    kind: str = ""
    move: ClientMove = field(default_factory=ClientMove)

    def to_dict(self) -> dict[str, Any]:
        """Return the client difference as a plain dictionary.

        Why:
            The comparison endpoint returns ``client_deltas`` as JSON, and the
            export writes the same columns. The serving devices are flat here,
            because a table column reads a flat value.

        Returns:
            A dictionary with the address, the outcome, the name, the kind,
            and the two serving devices.
        """
        return {
            "mac": self.mac,
            "outcome": self.outcome,
            "hostname": self.hostname,
            "kind": self.kind,
            "before_device": self.move.before_device,
            "after_device": self.move.after_device,
            "before_device_name": self.move.before_name,
            "after_device_name": self.move.after_name,
        }


@dataclass(frozen=True, slots=True)
class ClientComparison:
    """The client result of one comparison.

    Why:
        The skipped section list travels with the deltas. An empty delta list
        means nothing until the reader knows whether the digests skipped the
        work.

        The proved count travels beside them. A digest match proves every
        client of the section present, so the count states how many clients the
        match covered. A caller that reports a bare zero instead tells the
        operator that the site lost every client, which is a different fact.

    Attributes:
        deltas: One entry for each client, sorted by address.
        skipped_sections: Each client section whose digest matched.
        proved_present: The clients that a matching digest proved present.
            Zero when the comparison read the rows itself.
    """

    deltas: tuple[ClientDelta, ...] = ()
    skipped_sections: tuple[str, ...] = ()
    proved_present: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return the client result as a plain dictionary.

        Why:
            The route lane merges this dictionary into the comparison body,
            so the key names match the contract exactly.

        Returns:
            A dictionary with ``client_deltas`` and ``skipped_sections``.
        """
        return {
            "client_deltas": [delta.to_dict() for delta in self.deltas],
            "skipped_sections": list(self.skipped_sections),
        }


# ---------------------------------------------------------------------------
# The match key
# ---------------------------------------------------------------------------


def _embedded_address(key: str) -> str:
    """Return the first address inside one key that holds no clean separator.

    Why:
        A writer sometimes joins the address and the timestamp with nothing
        between them. A composite key sometimes holds an address that the
        colons already split. Removing every separator and reading the first
        run of 12 hexadecimal characters covers both forms.

    Args:
        key: The raw key text.

    Returns:
        The embedded address, or an empty string when the key holds none.
    """
    flat = key.translate(_ADDRESS_SEPARATORS).lower()
    found = _EMBEDDED_ADDRESS.search(flat)
    return found.group(0) if found else ""


def strip_timestamp_key(key: object) -> str:
    """Return the client address inside one composite registry key.

    Why:
        The registry joins the endpoint, the address, and a timestamp
        (``src/db/redis_writer.py:627``). The timestamp differs in every
        capture, so a comparison that matched on the whole key would report
        every client as new. This reader keeps the address and drops the rest.

    Args:
        key: A plain address, a composite registry key, or any other value.

    Returns:
        The address in lower case with no separator, or an empty string when
        the key holds no address.
    """
    if not isinstance(key, str):
        return ""
    direct = normalize_mac(key)
    if direct:
        return direct
    for part in _KEY_SEPARATORS.split(key):
        address = normalize_mac(part)
        if address:
            return address
    return _embedded_address(key)


# ---------------------------------------------------------------------------
# The capture readers
# ---------------------------------------------------------------------------


def _row_value(row: Mapping[str, Any], name: str) -> str:
    """Return one text field of one client row.

    Why:
        A capture drops an empty field and the cloud sometimes returns a
        number. One reader gives every caller a string and keeps the type
        tests out of the comparison.

    Args:
        row: One client row.
        name: The field name.

    Returns:
        The field value as text, or an empty string.
    """
    value = row.get(name)
    return value if isinstance(value, str) else ""


def _serving_device(row: Mapping[str, Any]) -> str:
    """Return the address of the device that serves one client.

    Why:
        The move test compares this value between the two captures, so both
        sides need the same address form. A raw cloud value with separators
        would never match a stored value without them.

    Args:
        row: One client row.

    Returns:
        The serving device address, or an empty string.
    """
    return strip_timestamp_key(row.get(DEVICE_MAC_KEY))


def _registry_rows(section: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    """Return the address and the row of each entry of one registry map.

    Why:
        A stored section is sometimes a map keyed by a composite registry key.
        The key holds a timestamp, so the reader takes the address from the
        row first and falls back to the stripped key.

    Args:
        section: One client section as a map.

    Returns:
        One pair for each usable row.
    """
    rows: list[tuple[str, Mapping[str, Any]]] = []
    for key, row in section.items():
        if not isinstance(row, Mapping):
            continue
        address = strip_timestamp_key(row.get(MAC_KEY)) or strip_timestamp_key(key)
        if address:
            rows.append((address, row))
    return rows


def _list_rows(section: Sequence[Any]) -> list[tuple[str, Mapping[str, Any]]]:
    """Return the address and the row of each entry of one client list.

    Why:
        The data model stores each client section as a list of flat records.
        A row without an address cannot match anything, so the reader drops
        it rather than matching every other broken row.

    Args:
        section: One client section as a list.

    Returns:
        One pair for each usable row.
    """
    rows: list[tuple[str, Mapping[str, Any]]] = []
    for row in section:
        if not isinstance(row, Mapping):
            continue
        address = strip_timestamp_key(row.get(MAC_KEY))
        if address:
            rows.append((address, row))
    return rows


def _rows_of_kind(capture: Mapping[str, Any], kind: str) -> list[tuple[str, Mapping[str, Any]]]:
    """Return every client row of one kind of one capture.

    Why:
        A capture that failed part way holds a partial client map. The reader
        returns what the capture does hold and never raises on a missing kind.

    Args:
        capture: One capture document.
        kind: ``wired``, ``wireless``, or ``guest``.

    Returns:
        One pair for each usable row.
    """
    clients = capture.get(CLIENTS_KEY)
    if not isinstance(clients, Mapping):
        return []
    section = clients.get(kind)
    if isinstance(section, Mapping):
        return _registry_rows(section)
    if isinstance(section, Sequence) and not isinstance(section, str):
        return _list_rows(section)
    return []


def _client_map(capture: Mapping[str, Any], kinds: Iterable[str]) -> dict[str, tuple[str, Mapping[str, Any]]]:
    """Return every client of one capture, keyed by address.

    Why:
        The match key is the address alone, so a client that appears in the
        wireless list and in the guest list is one client. The first kind in
        order wins, and the union stays one entry for each address.

    Args:
        capture: One capture document.
        kinds: The kinds to read, in order.

    Returns:
        A map from address to the kind and the row.
    """
    found: dict[str, tuple[str, Mapping[str, Any]]] = {}
    for kind in kinds:
        for address, row in _rows_of_kind(capture, kind):
            found.setdefault(address, (kind, row))
    return found


# ---------------------------------------------------------------------------
# The client comparison
# ---------------------------------------------------------------------------


def _single_delta(mac: str, entry: tuple[str, Mapping[str, Any]], outcome: str) -> ClientDelta:
    """Return the record of a client that one capture holds alone.

    Why:
        An added client has no device before, and a missing client has no
        device after. Filling the correct side keeps the table honest and
        keeps an empty column out of the export.

    Args:
        mac: The client address.
        entry: The kind and the row of the capture that holds the client.
        outcome: ``added`` or ``missing``.

    Returns:
        One client difference record.
    """
    kind, row = entry
    device = _serving_device(row)
    name = _row_value(row, DEVICE_NAME_KEY)
    if outcome == OUTCOME_ADDED:
        move = ClientMove(after_device=device, after_name=name)
    else:
        move = ClientMove(before_device=device, before_name=name)
    return ClientDelta(mac=mac, outcome=outcome, hostname=_row_value(row, HOSTNAME_KEY), kind=kind, move=move)


def _paired_delta(
    mac: str,
    before_entry: tuple[str, Mapping[str, Any]],
    after_entry: tuple[str, Mapping[str, Any]],
) -> ClientDelta:
    """Return the record of a client that both captures hold.

    Why:
        A client on the same device is ``present``. A client on another device
        roamed and is ``moved``. No other field decides the outcome, because a
        new address or a new signal reading is not a move.

    Args:
        mac: The client address.
        before_entry: The kind and the row of the pre-check capture.
        after_entry: The kind and the row of the post-check capture.

    Returns:
        One client difference record.
    """
    before_row = before_entry[1]
    kind, after_row = after_entry
    move = ClientMove(
        before_device=_serving_device(before_row),
        after_device=_serving_device(after_row),
        before_name=_row_value(before_row, DEVICE_NAME_KEY),
        after_name=_row_value(after_row, DEVICE_NAME_KEY),
    )
    outcome = OUTCOME_MOVED if move.moved else OUTCOME_PRESENT
    return ClientDelta(mac=mac, outcome=outcome, hostname=_row_value(after_row, HOSTNAME_KEY), kind=kind, move=move)


def _compare_one_client(
    mac: str,
    before_entry: tuple[str, Mapping[str, Any]] | None,
    after_entry: tuple[str, Mapping[str, Any]] | None,
) -> ClientDelta:
    """Return the difference record of one client.

    Why:
        The four outcomes come from the presence of the two rows and from the
        serving device. Deciding all four in one place keeps the rule out of
        the loop.

    Args:
        mac: The client address.
        before_entry: The pre-check entry, or None.
        after_entry: The post-check entry, or None.

    Returns:
        One client difference record.

    Raises:
        ValueError: When the client holds neither row.
    """
    if before_entry is not None and after_entry is not None:
        return _paired_delta(mac, before_entry, after_entry)
    if after_entry is not None:
        return _single_delta(mac, after_entry, OUTCOME_ADDED)
    if before_entry is None:
        # The caller walks the union of the two maps, so one of the two entries
        # always holds a row. A client with neither row is a programming fault.
        # A made up "missing" record would put a false line in a comparison that
        # an operator attaches to a change record.
        raise ValueError(f"Client {mac} holds no pre-check row and no post-check row.")
    return _single_delta(mac, before_entry, OUTCOME_MISSING)


def _present_section_size(before: Mapping[str, Any], after: Mapping[str, Any], kind: str) -> int:
    """Return how many present clients a matching digest proved for one kind.

    Why:
        A matching digest proves the two client sections equal, so every client
        in the section is present. The comparison reads no row, so the count
        must come from the size of the section instead. A count of zero would
        read as a lost site, which is a different fact.

        The reader takes the larger of the two sizes. The digest proves the two
        sections equal, so the larger size is the true size. A stored document
        that lost a row then never lowers the count.

    Args:
        before: The pre-check capture.
        after: The post-check capture.
        kind: ``wired``, ``wireless``, or ``guest``.

    Returns:
        The present client count of the proved section.
    """
    before_total = len({address for address, _ in _rows_of_kind(before, kind)})  # WHY: One address counts once.
    after_total = len({address for address, _ in _rows_of_kind(after, kind)})  # WHY: The post-check size.
    return max(before_total, after_total)  # WHY: A partial document must never lower a proved count.


def _proved_present_count(before: Mapping[str, Any], after: Mapping[str, Any], skipped: tuple[str, ...]) -> int:
    """Return how many present clients the matching client digests proved.

    Why:
        Each skipped section proves its own clients present, so the count sums
        the three sections. A section the comparison read stays out of the sum,
        because its clients already travel in the delta list. Summing only the
        skipped sections keeps a client out of the count and the delta list at
        once, so no client counts twice.

    Args:
        before: The pre-check capture.
        after: The post-check capture.
        skipped: Each client section whose digest matched.

    Returns:
        The present client count over every skipped client section.
    """
    total = 0  # WHY: The running sum over the skipped sections.
    for kind in CLIENT_KINDS:  # WHY: Walk the three kinds in one fixed order.
        if SECTION_FOR_KIND[kind] in skipped:  # WHY: Only a skipped section proves a count.
            total += _present_section_size(before, after, kind)  # WHY: Add the proved size of this kind.
    return total  # WHY: The whole proved present count of the comparison.


def compare_clients(before: Mapping[str, Any], after: Mapping[str, Any]) -> ClientComparison:
    """Compare the clients of two captures.

    Why:
        This is the client half of the comparison. The digest test runs first
        for each of the three client sections, so a quiet section costs
        nothing. Only a section that really changed reaches the address match.

    Args:
        before: The pre-check capture.
        after: The post-check capture.

    Returns:
        The client differences, each skipped client section, and the count of
        clients that the matching digests proved present.
    """
    skipped = matched_sections(before, after, CLIENT_SECTIONS)
    kinds = tuple(kind for kind in CLIENT_KINDS if SECTION_FOR_KIND[kind] not in skipped)
    before_map = _client_map(before, kinds)
    after_map = _client_map(after, kinds)
    addresses = sorted(set(before_map) | set(after_map))
    deltas = tuple(_compare_one_client(mac, before_map.get(mac), after_map.get(mac)) for mac in addresses)
    proved = _proved_present_count(before, after, skipped)  # WHY: The count replaces the bare zero on the page.
    logger.info("Upgrade portal compared %s clients and skipped %s sections", len(deltas), len(skipped))
    logger.debug("Upgrade portal proved %s clients present over the skipped sections", proved)
    return ClientComparison(deltas=deltas, skipped_sections=skipped, proved_present=proved)


def count_outcome(deltas: Iterable[ClientDelta], outcome: str) -> int:
    """Return how many client records carry one outcome.

    Why:
        The statistics roll-up counts four outcomes the same way. One counter
        keeps the four counts in step.

    Args:
        deltas: The client difference records.
        outcome: One value of ``CLIENT_OUTCOMES``.

    Returns:
        The number of matching records.
    """
    return sum(1 for delta in deltas if delta.outcome == outcome)


__all__ = [
    "CLIENTS_KEY",
    "CLIENT_KINDS",
    "CLIENT_OUTCOMES",
    "CLIENT_SECTIONS",
    "DEVICE_MAC_KEY",
    "DEVICE_NAME_KEY",
    "HOSTNAME_KEY",
    "KIND_GUEST",
    "KIND_WIRED",
    "KIND_WIRELESS",
    "LOSS_OUTCOMES",
    "MAC_KEY",
    "OUTCOME_ADDED",
    "OUTCOME_MISSING",
    "OUTCOME_MOVED",
    "OUTCOME_PRESENT",
    "SECTION_CLIENTS_GUEST",
    "SECTION_CLIENTS_WIRED",
    "SECTION_CLIENTS_WIRELESS",
    "SECTION_FOR_KIND",
    "ClientComparison",
    "ClientDelta",
    "ClientMove",
    "compare_clients",
    "count_outcome",
    "strip_timestamp_key",
]
