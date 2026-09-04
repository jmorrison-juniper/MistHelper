"""Holds the endpoint selection, the descriptor rule, and the OID ledger.

Why:
    A monitoring system stores history against an OID. A renumber destroys that
    history, which is worse than the hand editing this package replaces. This
    module owns the three decisions that could move a number:

    - `AllowList` decides which Mist endpoints reach the MIB.
    - `DescriptorMaker` decides the SMIv2 name of a new field.
    - `OidLedger` decides the number of every field, live or obsolete.

    The ledger key is the scope and the source path, never the descriptor. A
    key on the descriptor would move an OID when a person improves a name.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from src.metrics_gateway.catalog import SUBTREE_BY_SCOPE, MetricCatalog, MetricScope
from src.metrics_gateway.snmp import DEFAULT_BASE_OID
from src.mib_generator.document import LOG_PREFIX, OpenApiDocument

logger = logging.getLogger(__name__)

GET_METHOD = "get"  # Only a GET operation can make a reading. A POST search is out of scope.
DATA_COLUMN_MIN = 1  # The lowest column that `claim` may hand out.
DATA_COLUMN_MAX = 89  # The highest column that `claim` may hand out.
RESERVED_COLUMN_MIN = 90  # The catalog owns the band from here up. `claim` never enters it.
RESERVED_COLUMN_MAX = 98  # The band ends here. Column 99 carries the row identity of a table.
DESCRIPTOR_LIMIT = 64  # SMIv2 refuses a descriptor above this length.
DESCRIPTOR_BASE_LIMIT = 62  # The cut length, so a two-digit collision suffix still fits inside the limit.
COLLISION_LIMIT = 99  # Ninety-nine names that differ by a digit means the naming rule is broken.
LIVE_STATE = "live"  # The field still exists, so the MIB emits it as `STATUS current`.
OBSOLETE_STATE = "obsolete"  # The field is gone, so the MIB emits it as `STATUS obsolete` and keeps the number.
NAME_PREFIX = "mist"  # Every descriptor starts with this word, so it always starts with a lowercase letter.
PATH_SEPARATORS = (".", "_", "[", "]")  # The characters that split a field path into name parts.


class LedgerError(ValueError):
    """The ledger holds a defect that would move or hide a live OID."""


class AllowListError(ValueError):
    """The allow list names an endpoint that the OpenAPI file cannot serve."""


@dataclass(frozen=True, slots=True)
class AllowListEntry:
    """One selected Mist endpoint.

    Attributes:
        operation_id: The `operationId` of a GET operation.
        scope: The scope that the readings of that operation carry.
        notes: The reason the operator selected the endpoint.
    """

    operation_id: str
    scope: MetricScope
    notes: str = ""


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    """The number and the name of one field.

    Attributes:
        key: The stable identity of the field. It is `<scope>/<source path>` for
            a Mist field, and `<scope>/#<metric name>` for a reading that the
            collector derives and no OpenAPI field backs.
        subtree: The subtree number, which comes from `SUBTREE_BY_SCOPE`.
        column: The column number below that subtree.
        descriptor: The SMIv2 name. The ledger stores it, so it never changes.
        state: `live` while the field exists, and `obsolete` after Mist removed
            it. An obsolete entry keeps its number forever.
        notes: Free text for a person.
    """

    key: str
    subtree: int
    column: int
    descriptor: str
    state: str = LIVE_STATE
    notes: str = ""


class AllowList:
    """The checked-in selection of Mist endpoints."""

    def __init__(self, path: Path) -> None:
        """Record the path of the allow list. This call reads nothing.

        Args:
            path: The local path of the allow list JSON file.
        """
        self._path = path  # `load` reads this path, so a caller can build the object and choose later.
        self._entries: tuple[AllowListEntry, ...] = ()  # The selection stays empty until `load` runs.

    def load(self) -> AllowList:
        """Read the allow list file.

        Returns:
            This allow list, so a caller can chain the call.
        """
        logger.info("%s Reading the allow list at %s", LOG_PREFIX, self._path)  # Log before the read.
        raw: dict[str, Any] = json.loads(self._path.read_text(encoding="utf-8"))
        self._entries = tuple(
            AllowListEntry(
                operation_id=str(item["operation_id"]),
                scope=MetricScope(str(item["scope"])),
                notes=str(item.get("notes") or ""),
            )
            for item in raw.get("entries") or []
        )
        logger.info("%s Read %d selected endpoints", LOG_PREFIX, len(self._entries))  # Log the result count.
        return self

    def entries(self) -> tuple[AllowListEntry, ...]:
        """Return every selected endpoint.

        Returns:
            The entries, in file order.
        """
        return self._entries

    def validate(self, document: OpenApiDocument) -> None:
        """Prove that every selected endpoint exists and is a GET.

        Args:
            document: The loaded OpenAPI document.

        Raises:
            AllowListError: If an `operationId` is missing from the document, or
                if the named operation is not a GET.
        """
        available = document.operations()  # One lookup map serves every entry of the allow list.
        for entry in self._entries:  # A single bad entry must stop the run before the writer opens a file.
            if entry.operation_id not in available:  # Mist removed the endpoint, or the operator mistyped it.
                raise AllowListError(f"The OpenAPI file holds no operationId {entry.operation_id!r}.")
            method = available[entry.operation_id][0]
            if method != GET_METHOD:  # Only a GET can make a reading, because a search needs a request body.
                raise AllowListError(
                    f"The operation {entry.operation_id!r} is a {method.upper()}, and a GET is needed."
                )
        logger.debug("%s The allow list names %d valid GET operations", LOG_PREFIX, len(self._entries))


class DescriptorMaker:
    """Turns a scope and a field path into a valid, unique SMIv2 descriptor."""

    def make(self, scope: MetricScope, path: str, taken: frozenset[str]) -> str:
        """Return the descriptor of one new field.

        Why:
            The ledger stores the descriptor of every field it already knows, so
            this call runs for a new field only. A change to the rule below can
            therefore never rename a live object.

        Args:
            scope: The Mist object the field describes.
            path: The dotted path of the field.
            taken: Every descriptor that a live or an obsolete entry already
                holds.

        Returns:
            A name that starts with a lowercase letter, holds letters and digits
            only, and never passes 64 characters.

        Raises:
            LedgerError: If 99 names that differ by a digit are all taken.
        """
        base = self._base_name(scope, path)  # The rule of data-model section 5 gives the candidate name.
        if base not in taken:  # First claim wins, which keeps the common name on the common field.
            return base
        for suffix in range(2, COLLISION_LIMIT + 1):  # A numeric suffix breaks a tie, in a stable order.
            candidate = f"{base}{suffix}"
            if candidate not in taken:
                return candidate
        raise LedgerError(f"The descriptor {base!r} collided {COLLISION_LIMIT} times, so the naming rule is broken.")

    @staticmethod
    def _base_name(scope: MetricScope, path: str) -> str:
        """Build the candidate descriptor of one field.

        Args:
            scope: The Mist object the field describes.
            path: The dotted path of the field.

        Returns:
            The candidate name, cut to 62 characters.
        """
        text = path  # The split below needs one separator, so replace every other separator first.
        for separator in PATH_SEPARATORS:  # A path holds dots, underscores, and array markers.
            text = text.replace(separator, " ")
        parts = [part for part in text.split(" ") if part]  # An empty part comes from two separators in a row.
        joined = NAME_PREFIX + scope.capitalize() + "".join(part[:1].upper() + part[1:] for part in parts)
        cleaned = "".join(character for character in joined if character.isascii() and character.isalnum())
        return (cleaned[:1].lower() + cleaned[1:])[:DESCRIPTOR_BASE_LIMIT]  # Step 6 and step 7 of the rule.


class OidLedger:
    """The number and the name of every field, live or obsolete."""

    def __init__(self, path: Path) -> None:
        """Record the path of the ledger. This call reads nothing.

        Args:
            path: The local path of the ledger JSON file.
        """
        self._path = path  # `load` reads this path, so a caller can build the object and choose later.
        self._base_oid = DEFAULT_BASE_OID  # A file without the field must still fail the comparison honestly.
        self._entries: dict[str, LedgerEntry] = {}  # The entries, keyed by the stable field key.
        self._maker = DescriptorMaker()  # `claim` needs the naming rule for a field the ledger never saw.

    def load(self) -> OidLedger:
        """Read the ledger file, or start an empty ledger when no file exists.

        Returns:
            This ledger, so a caller can chain the call.
        """
        logger.info("%s Reading the OID ledger at %s", LOG_PREFIX, self._path)  # Log before the read.
        raw: dict[str, Any] = json.loads(self._path.read_text(encoding="utf-8")) if self._path.is_file() else {}
        self._base_oid = str(raw.get("base_oid") or DEFAULT_BASE_OID)
        self._entries = {
            str(item["key"]): LedgerEntry(
                key=str(item["key"]),
                subtree=int(item["subtree"]),
                column=int(item["column"]),
                descriptor=str(item["descriptor"]),
                state=str(item.get("state") or LIVE_STATE),
                notes=str(item.get("notes") or ""),
            )
            for item in raw.get("entries") or []
        }
        logger.info("%s Read %d ledger entries", LOG_PREFIX, len(self._entries))  # Log the result count.
        return self

    def entries(self) -> tuple[LedgerEntry, ...]:
        """Return every entry, sorted by subtree and then by column.

        Returns:
            The entries, in the order the file stores them.
        """
        return tuple(sorted(self._entries.values(), key=lambda item: (item.subtree, item.column)))

    def validate(self, catalog: MetricCatalog) -> None:
        """Prove that the ledger can never move or hide a live OID.

        Args:
            catalog: The metric catalog, which owns the reserved column band.

        Raises:
            LedgerError: If the base OID differs from the agent, if two entries
                share a number or a name, or if a column sits outside its band.
        """
        if self._base_oid != DEFAULT_BASE_OID:  # A different root makes every translation of the MIB wrong.
            raise LedgerError(f"The ledger base OID is {self._base_oid}, and the agent answers at {DEFAULT_BASE_OID}.")
        self._check_unique(self.entries())
        self._check_bands(self.entries(), self._reserved_claims(catalog))
        logger.debug("%s The ledger passed every check with %d entries", LOG_PREFIX, len(self._entries))

    @staticmethod
    def _reserved_claims(catalog: MetricCatalog) -> set[tuple[int, int]]:
        """Return the subtree and column of every catalog reading in the reserved band.

        Args:
            catalog: The metric catalog.

        Returns:
            The pairs the catalog claims between column 90 and column 98.
        """
        claims: set[tuple[int, int]] = set()  # The gateway health readings live here, and nothing else may.
        for scope in MetricScope:  # One pass over the whole catalog finds every reserved claim.
            for definition in catalog.for_scope(scope):
                if RESERVED_COLUMN_MIN <= definition.column <= RESERVED_COLUMN_MAX:
                    claims.add((SUBTREE_BY_SCOPE[scope], definition.column))
        return claims

    @staticmethod
    def _check_unique(entries: tuple[LedgerEntry, ...]) -> None:
        """Stop the run when two entries share a number or a name.

        Args:
            entries: Every ledger entry.

        Raises:
            LedgerError: If two entries share a place, or if two share a name.
        """
        places: dict[tuple[int, int], str] = {}  # Two entries at one place make one of them unreachable.
        names: dict[str, str] = {}  # Two entries with one name make the MIB fail to parse.
        for entry in entries:  # One pass finds both kinds of duplicate and it names the offending pair.
            place = (entry.subtree, entry.column)
            if place in places:  # The second claim on a number would silently take the OID of the first.
                raise LedgerError(f"The keys {places[place]!r} and {entry.key!r} both claim column {place}.")
            if entry.descriptor in names:  # SMIv2 refuses a module that defines one descriptor twice.
                raise LedgerError(f"The keys {names[entry.descriptor]!r} and {entry.key!r} share {entry.descriptor!r}.")
            places[place], names[entry.descriptor] = entry.key, entry.key

    @staticmethod
    def _check_bands(entries: tuple[LedgerEntry, ...], claims: set[tuple[int, int]]) -> None:
        """Stop the run when a column sits outside the band its owner may use.

        Args:
            entries: Every ledger entry.
            claims: The reserved pairs that the catalog owns.

        Raises:
            LedgerError: If a subtree is unknown, or if a column is out of band.
        """
        known = set(SUBTREE_BY_SCOPE.values())  # A subtree outside this set names no scope the agent serves.
        for entry in entries:  # One pass proves the place of every entry.
            if entry.subtree not in known:  # The agent answers no request below an unknown subtree.
                raise LedgerError(f"The key {entry.key!r} names the unknown subtree {entry.subtree}.")
            if not DATA_COLUMN_MIN <= entry.column <= RESERVED_COLUMN_MAX:  # Column 99 belongs to the row identity.
                raise LedgerError(f"The key {entry.key!r} names column {entry.column}, which is outside 1 to 98.")
            in_reserved = entry.column >= RESERVED_COLUMN_MIN  # The catalog owns the band from 90 up.
            if in_reserved and (entry.subtree, entry.column) not in claims:
                raise LedgerError(
                    f"The key {entry.key!r} takes reserved column {entry.column} without a catalog claim."
                )

    def claim(self, key: str, scope: MetricScope, path: str, column: int = 0) -> LedgerEntry:
        """Return the entry of one field, and make one when the ledger has none.

        Why:
            The catalog owns the column of every reading it already names, and
            the agent answers at that column today. A caller therefore passes
            that column in, and the ledger only chooses a number for a field
            that no catalog entry names.

        Args:
            key: The stable field key.
            scope: The Mist object the field describes.
            path: The dotted path of the field, used to build a new descriptor.
            column: The column the catalog already owns, or 0 to let the ledger
                choose the lowest free data column.

        Returns:
            The stored entry, or the new entry the ledger just made.

        Raises:
            LedgerError: If a stored entry disagrees with the catalog column, or
                if the subtree holds no free column.
        """
        subtree = SUBTREE_BY_SCOPE[scope]  # A field always takes the subtree of its own scope.
        stored = self._entries.get(key)  # The ledger wins on the name, so a live descriptor can never move.
        if stored and column and stored.column != column:  # A silent move would break every stored history.
            raise LedgerError(f"The key {key!r} sits at column {stored.column}, and the catalog says {column}.")
        if stored:
            return stored
        chosen = column or self._next_column(subtree)  # A field outside the catalog needs a number of its own.
        descriptor = self._maker.make(scope, path, frozenset(item.descriptor for item in self._entries.values()))
        entry = LedgerEntry(key=key, subtree=subtree, column=chosen, descriptor=descriptor)
        self._entries[key] = entry
        logger.info("%s Gave the new field %s the column %d as %s", LOG_PREFIX, key, chosen, descriptor)
        return entry

    def _next_column(self, subtree: int) -> int:
        """Return the lowest free data column of one subtree.

        Args:
            subtree: The subtree the new field belongs to.

        Returns:
            The lowest free column between 1 and 89.

        Raises:
            LedgerError: If every column of the band is taken.
        """
        used = {item.column for item in self._entries.values() if item.subtree == subtree}  # The taken numbers.
        for column in range(DATA_COLUMN_MIN, DATA_COLUMN_MAX + 1):  # The reserved band from 90 up stays untouched.
            if column not in used:
                return column
        raise LedgerError(f"The subtree {subtree} holds no free column below {RESERVED_COLUMN_MIN}.")

    def retire(self, key: str) -> None:
        """Mark one entry obsolete and keep its number reserved forever.

        Args:
            key: The stable field key of the entry to retire.
        """
        entry = self._entries.get(key)  # A key the ledger never held needs no retirement.
        if entry and entry.state != OBSOLETE_STATE:  # A second call must not rewrite the notes of the first.
            self._entries[key] = replace(entry, state=OBSOLETE_STATE)
            logger.info("%s Retired %s and reserved column %d", LOG_PREFIX, key, entry.column)

    def save(self) -> None:
        """Write the ledger back to its file, sorted by subtree and then by column."""
        logger.info("%s Writing %d ledger entries to %s", LOG_PREFIX, len(self._entries), self._path)
        payload = {
            "version": 1,  # A reader needs the format version before it reads the entries.
            "base_oid": self._base_oid,
            "entries": [
                {
                    "key": item.key,
                    "subtree": item.subtree,
                    "column": item.column,
                    "descriptor": item.descriptor,
                    "state": item.state,
                    "notes": item.notes,
                }
                for item in self.entries()
            ],
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)  # A fresh clone holds no data folder yet.
        self._path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        logger.debug("%s Wrote the ledger to %s", LOG_PREFIX, self._path)  # Log the result of the write.
