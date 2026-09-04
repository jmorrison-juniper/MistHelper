"""Joins the OpenAPI file, the metric catalog, and the OID ledger.

Why:
    Three inputs decide the MIB, and each one answers a different question. The
    OpenAPI file says what type a Mist field carries. The catalog says which
    readings the agent answers. The ledger says which number each reading owns.
    This module holds the join, so no other module needs all three.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.metrics_gateway.catalog import SUBTREE_BY_SCOPE, MetricCatalog, MetricDefinition, MetricScope
from src.mib_generator.assignment import LIVE_STATE, OBSOLETE_STATE, AllowList, OidLedger
from src.mib_generator.document import LOG_PREFIX, OpenApiDocument
from src.mib_generator.mib import MibObject, MibWriter, SnmpTypeMapper
from src.mib_generator.schema import FieldRecord, SchemaFlattener

logger = logging.getLogger(__name__)

DEFAULT_OPENAPI = Path("documentation") / "mist-api-openapi31json.json"  # The Mist file that ships with the repo.
DEFAULT_ALLOWLIST = Path("data") / "mib_generator" / "allowlist.json"  # The checked-in endpoint selection.
DEFAULT_LEDGER = Path("data") / "mib_generator" / "oid_assignments.json"  # The checked-in number of each field.
DEFAULT_OUTPUT = Path("documentation") / "mibs" / "MISTHELPER-MIB.mib"  # The MIB that a monitoring system loads.
DERIVED_MARKER = "#"  # A key of a reading that the collector derives and no Mist field backs.
SLE_PARENT = (MetricScope.ORG, "sle[].")  # The SLE readings arrive inside the `sle` array of the org reading.
REPORT_LIMIT = 40  # The largest candidate list that a person can read in one sitting.
TIME_FORMAT = "%Y%m%d%H%MZ"  # The SMIv2 spelling of a time stamp.


@dataclass(frozen=True, slots=True)
class CandidateReport:
    """One Mist field that the catalog does not yet serve.

    Attributes:
        scope: The Mist object the field describes.
        path: The dotted path of the field.
        json_type: The JSON type of the field.
        description: The words that Mist gives the field.
    """

    scope: MetricScope
    path: str
    json_type: str
    description: str = ""


class MibGeneratorRunner:
    """Runs the generate action, the report action, and the check action."""

    def __init__(
        self, openapi: Path = DEFAULT_OPENAPI, allowlist: Path = DEFAULT_ALLOWLIST, ledger: Path = DEFAULT_LEDGER
    ) -> None:
        """Record the three input paths. This call reads nothing.

        Args:
            openapi: The path of the Mist OpenAPI file.
            allowlist: The path of the endpoint selection.
            ledger: The path of the OID ledger.
        """
        self._document = OpenApiDocument(openapi)  # The reader of the Mist field types.
        self._allowlist = AllowList(allowlist)  # The reader of the endpoint selection.
        self._ledger = OidLedger(ledger)  # The reader and the writer of the numbers.
        self._catalog = MetricCatalog()  # The readings the agent answers. It needs no file.
        self._writer = MibWriter(SnmpTypeMapper())  # The renderer of the SMIv2 text.

    def fields(self) -> dict[MetricScope, dict[str, FieldRecord]]:
        """Return every Mist field of every selected endpoint, keyed by scope and path.

        Returns:
            The fields of each scope.
        """
        logger.info("%s Reading the Mist fields of every selected endpoint", LOG_PREFIX)  # Log before the read.
        self._document.load()
        self._allowlist.load().validate(self._document)
        flattener = SchemaFlattener(self._document)
        found: dict[MetricScope, dict[str, FieldRecord]] = {scope: {} for scope in MetricScope}
        for entry in self._allowlist.entries():  # One pass over the selection fills every scope it names.
            schema = self._document.response_schema(entry.operation_id)
            found[entry.scope] = {item.path: item for item in flattener.flatten(entry.scope, schema)}
        found[MetricScope.SLE] = self._sle_fields(found[SLE_PARENT[0]])
        logger.info("%s Read %d Mist fields in total", LOG_PREFIX, sum(len(item) for item in found.values()))
        return found

    @staticmethod
    def _sle_fields(org_fields: dict[str, FieldRecord]) -> dict[str, FieldRecord]:
        """Return the SLE fields, which sit inside the org reading.

        Why:
            Mist publishes no SLE endpoint of its own. The gateway reads the
            `sle` array of the organization reading, so the SLE paths carry the
            `sle[].` prefix and the catalog paths do not.

        Args:
            org_fields: Every field of the organization scope.

        Returns:
            The SLE fields, with the prefix removed.
        """
        prefix = SLE_PARENT[1]  # The catalog says `user_minutes.total`, and the flattener says `sle[].user_minutes...`.
        return {path[len(prefix) :]: record for path, record in org_fields.items() if path.startswith(prefix)}

    @staticmethod
    def _key(definition: MetricDefinition) -> str:
        """Return the stable ledger key of one reading.

        Why:
            A key on the source path survives a rename of the metric. Four org
            readings and several others carry an empty source, because the
            collector derives them. Those need a key on the metric name, or they
            would all collide on one empty path.

        Args:
            definition: The catalog entry.

        Returns:
            The key.
        """
        tail = definition.source or f"{DERIVED_MARKER}{definition.name}"  # A derived reading has no Mist path.
        return f"{definition.scope}/{tail}"

    def objects(self) -> tuple[MibObject, ...]:
        """Return every object of the MIB, live and obsolete.

        Returns:
            The objects, with a ledger entry on each one.
        """
        logger.info("%s Joining the catalog, the Mist fields, and the ledger", LOG_PREFIX)  # Log before the join.
        found = self.fields()
        self._ledger.load().validate(self._catalog)
        live: dict[str, MibObject] = {}
        for scope in MetricScope:  # One pass over the catalog claims a number for every reading it names.
            for definition in self._catalog.for_scope(scope):
                entry = self._ledger.claim(
                    self._key(definition), scope, definition.source or definition.name, definition.column
                )
                live[entry.key] = MibObject(entry, scope, definition, found[scope].get(definition.source))
        obsolete = self._retired(live)
        logger.info("%s Joined %d live objects and %d obsolete objects", LOG_PREFIX, len(live), len(obsolete))
        return tuple(live.values()) + obsolete

    def _retired(self, live: dict[str, MibObject]) -> tuple[MibObject, ...]:
        """Mark every ledger entry that the catalog no longer names, and return them.

        Args:
            live: The objects the catalog still names, keyed by ledger key.

        Returns:
            The obsolete objects.
        """
        by_subtree = {number: scope for scope, number in SUBTREE_BY_SCOPE.items()}  # A stored entry names no scope.
        gone = tuple(item for item in self._ledger.entries() if item.key not in live)  # Mist or the catalog dropped it.
        for entry in gone:  # A retired number stays reserved, so a later field can never take it.
            self._ledger.retire(entry.key)
        return tuple(MibObject(entry, by_subtree[entry.subtree]) for entry in gone)

    def generate(self, output: Path = DEFAULT_OUTPUT, dry_run: bool = False) -> str:
        """Write the MIB, or return its text without writing when the run is dry.

        Args:
            output: The path of the MIB file.
            dry_run: True to write nothing, which lets a review read the text
                before it reaches the repository.

        Returns:
            The MIB text.
        """
        text = self._writer.render(self.objects(), datetime.now(tz=UTC).strftime(TIME_FORMAT))
        if dry_run:  # A dry run must leave both the MIB and the ledger exactly as it found them.
            logger.info("%s The run is dry, so nothing reached the disk", LOG_PREFIX)
            return text
        logger.info("%s Writing the MIB to %s", LOG_PREFIX, output)  # Log before the write.
        output.parent.mkdir(parents=True, exist_ok=True)  # A fresh clone holds no mibs folder yet.
        output.write_text(text, encoding="utf-8")
        self._ledger.save()  # The ledger holds the number of every new field, so it must reach the disk too.
        logger.info("%s Wrote %d characters to %s", LOG_PREFIX, len(text), output)  # Log the result size.
        return text

    def report(self, limit: int = REPORT_LIMIT) -> tuple[CandidateReport, ...]:
        """Return the Mist fields that the catalog does not yet serve.

        Args:
            limit: The largest number of candidates to return.

        Returns:
            The candidates, in scope order and then in path order.
        """
        logger.info("%s Looking for Mist fields that the catalog does not serve", LOG_PREFIX)  # Log before the scan.
        found = self.fields()
        served = {scope: {item.source for item in self._catalog.for_scope(scope)} for scope in MetricScope}
        rows = [
            CandidateReport(scope, record.path, record.json_type, record.description)
            for scope in MetricScope
            for record in sorted(found[scope].values(), key=lambda item: item.path)
            if record.path not in served[scope]
        ]
        logger.info("%s Found %d candidate fields", LOG_PREFIX, len(rows))  # Log the result count.
        return tuple(rows[:limit])

    def check(self, output: Path = DEFAULT_OUTPUT) -> tuple[str, ...]:
        """Return every disagreement between the inputs and the MIB on the disk.

        Args:
            output: The path of the MIB file to check.

        Returns:
            The problems. An empty result means the MIB agrees with the inputs.
        """
        logger.info("%s Checking the MIB at %s against the three inputs", LOG_PREFIX, output)  # Log before the check.
        problems = [] if output.is_file() else [f"The MIB file {output} does not exist."]
        found = self.fields() if not problems else {}
        problems.extend(self._missing_fields(found))
        problems.extend(self._stale_text(output))
        logger.info("%s The check found %d problems", LOG_PREFIX, len(problems))  # Log the result count.
        return tuple(problems)

    def _missing_fields(self, found: dict[MetricScope, dict[str, FieldRecord]]) -> list[str]:
        """Return one message for each catalog source path that Mist no longer serves.

        Args:
            found: The Mist fields of each scope.

        Returns:
            The messages.
        """
        problems: list[str] = []  # A lost field means the gateway reports a value that Mist stopped sending.
        for scope, records in found.items():  # A derived reading carries no source, so it needs no Mist field.
            for definition in self._catalog.for_scope(scope):
                if definition.source and definition.source not in records:
                    problems.append(f"The Mist file holds no {scope}/{definition.source} for {definition.name}.")
        return problems

    def _stale_text(self, output: Path) -> list[str]:
        """Return one message when the MIB text differs from a fresh render.

        Args:
            output: The path of the MIB file to check.

        Returns:
            The messages.
        """
        if not output.is_file():  # The caller already reported the missing file.
            return []
        current = output.read_text(encoding="utf-8")
        fresh = self._writer.render(self.objects(), "")  # An empty time stamp keeps the comparison stable.
        stamped = _strip_dates(current)  # The stored file carries a real time stamp, and the fresh text does not.
        return [] if stamped == _strip_dates(fresh) else [f"The MIB at {output} is out of date. Generate it again."]

    def ledger_state(self) -> dict[str, str]:
        """Return the state of every ledger key, for a test or a report.

        Returns:
            The state of each key, either `live` or `obsolete`.
        """
        return {item.key: item.state for item in self._ledger.entries()}


def _strip_dates(text: str) -> str:
    """Remove every SMIv2 time stamp from one MIB text.

    Why:
        The generator stamps the render time into the module. A check must
        compare the objects, not the minute the last person ran the generator.

    Args:
        text: The MIB text.

    Returns:
        The text without a time stamp.
    """
    keep = [line for line in text.splitlines() if "LAST-UPDATED" not in line and "REVISION" not in line]
    return "\n".join(keep)


__all__ = ["CandidateReport", "MibGeneratorRunner", "LIVE_STATE", "OBSOLETE_STATE"]
