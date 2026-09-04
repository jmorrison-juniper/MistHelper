"""Decides the SNMP type of a field and writes the SMIv2 text.

Why:
    The MIB must agree with the running agent. `OidTree._encode` in
    `src/metrics_gateway/snmp.py` decides the type that reaches the wire, and it
    branches on the metric kind of the catalog. This module branches on the same
    value first, so the MIB can never promise a type the agent does not send.

    The output shape follows the agent as well. A scalar sits at
    `<base>.<subtree>.<column>.0`. A table cell sits at
    `<base>.<subtree>.1.<column>.<row>`. The table node carries the subtree
    number and the entry node carries the 1, with no node between them. An
    earlier hand-written MIB added one level there, and every table object was
    unreachable by name.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.metrics_gateway.catalog import (
    RATIO_SNMP_SCALE,
    ROW_IDENTITY_COLUMN,
    SECONDS_SNMP_SCALE,
    SUBTREE_BY_SCOPE,
    MetricDefinition,
    MetricKind,
    MetricScope,
)
from src.metrics_gateway.snmp import DEFAULT_BASE_OID
from src.mib_generator.assignment import LedgerEntry
from src.mib_generator.document import LOG_PREFIX
from src.mib_generator.schema import FieldRecord

logger = logging.getLogger(__name__)


class MibRenderError(Exception):
    """The MIB text contains a syntax error that the SNMP parser cannot fix."""

    pass


MODULE_NAME = "MISTHELPER-MIB"  # The SMIv2 module name that a monitoring system imports.
MODULE_ROOT = "mistHelperMIB"  # The descriptor of the module root.
INDEX_COLUMN = 100  # The index object of a table. The agent never answers it, so it is not accessible.
DISPLAY_STRING = "DisplayString (SIZE (0..255))"  # Observium needs a stated size bound on a text column.
GAUGE32 = "Gauge32"  # An unsigned 32-bit number that rises and falls.
COUNTER64 = "Counter64"  # An unsigned 64-bit number that only rises. A Mist byte count passes 2^32 in one day.
BOOLEAN_SYNTAX = "INTEGER { false(0), true(1) }"  # The SMIv2 spelling of a JSON boolean.
INDEX_SYNTAX = "Integer32 (1..2147483647)"  # A row position, which the agent counts from 1.
RATIO_UNITS = "ten-thousandths"  # The agent sends `round(value * 10000)`, so 0.97 arrives as 9700.
MILLISECOND_UNITS = "milliseconds"  # The agent sends `round(value * 1000)`, so a short duration stays visible.
COMMENT_MARKER = "--"  # Two hyphens open and close an ASN.1 comment, on the same line.
HYPHEN = "-"  # A single hyphen; used to detect rule lines (`--` followed only by hyphens).
SCALE_SENTENCE = {
    RATIO_SNMP_SCALE: "SNMP reports ten-thousandths.",  # A NOC engineer who reads 9700 knows it means 0.97.
    SECONDS_SNMP_SCALE: "SNMP reports milliseconds.",  # A duration below one second stays visible.
}
UNITS_BY_SUFFIX = (
    ("_bytes", "bytes"),  # A memory reading and a byte counter both end this way.
    ("_seconds", "seconds"),  # An uptime and a timestamp both end this way.
    ("_watts", "watts"),  # A power budget ends this way.
    ("_celsius", "degrees Celsius"),  # A temperature ends this way.
)
SCOPE_WORD = {
    MetricScope.ORG: "Org",  # The scalars of the whole organization.
    MetricScope.SITE: "Site",  # The site table.
    MetricScope.DEVICE: "Device",  # The device table, which holds every device type.
    MetricScope.SLE: "Sle",  # The service level expectation table.
}
TABLE_SCOPES = (MetricScope.SITE, MetricScope.DEVICE, MetricScope.SLE)  # Every scope except the organization.


@dataclass(frozen=True, slots=True)
class MibObject:
    """One object of the output MIB.

    Attributes:
        entry: The ledger entry that gives the number and the name.
        scope: The Mist object the reading describes.
        definition: The catalog entry, or None for an obsolete object that the
            catalog no longer names.
        field: The OpenAPI field, or None for a reading that the collector
            derives.
    """

    entry: LedgerEntry
    scope: MetricScope
    definition: MetricDefinition | None = None
    field: FieldRecord | None = None


class SnmpTypeMapper:
    """Decides the SYNTAX and the UNITS of one reading."""

    def syntax_for(self, definition: MetricDefinition, field: FieldRecord | None) -> str:
        """Return the SMIv2 SYNTAX of one reading.

        Why:
            The catalog wins over the OpenAPI file on every conflict, because
            `OidTree._encode` branches on the catalog kind and decides what the
            agent actually puts on the wire.

        Args:
            definition: The catalog entry of the reading.
            field: The OpenAPI field, or None for a derived reading.

        Returns:
            The SYNTAX text.
        """
        if definition.kind is MetricKind.INFO:  # The agent returns text for an informational reading.
            return DISPLAY_STRING
        if definition.kind is MetricKind.COUNTER:  # The agent returns a 64-bit counter for a byte count.
            return COUNTER64
        if definition.snmp_scale != 1:  # A scaled fraction reaches the wire as a whole gauge value.
            return GAUGE32
        if field is not None and field.json_type == "boolean":  # A JSON boolean needs the two named values.
            return BOOLEAN_SYNTAX
        if field is not None and field.json_type == "string":  # A JSON string needs a bounded text type.
            return DISPLAY_STRING
        return GAUGE32  # An integer and a number both reach the wire as a gauge.

    def units_for(self, definition: MetricDefinition) -> str:
        """Return the UNITS text of one reading.

        Args:
            definition: The catalog entry of the reading.

        Returns:
            The UNITS text, or an empty string when the reading has no unit.
        """
        if definition.kind is MetricKind.INFO:  # Text carries no unit.
            return ""
        if definition.snmp_scale == RATIO_SNMP_SCALE:  # The scale is the unit for a ratio.
            return RATIO_UNITS
        if definition.snmp_scale == SECONDS_SNMP_SCALE:  # The scale is the unit for a duration.
            return MILLISECOND_UNITS
        for suffix, units in UNITS_BY_SUFFIX:  # The metric name states the unit of every other reading.
            if definition.name.endswith(suffix):
                return units
        # Extract units from help text for count metrics ("The count of X in ...").
        units_from_help = self._extract_units_from_help(definition.help_text)
        if units_from_help:
            return units_from_help
        return ""

    @staticmethod
    def _extract_units_from_help(help_text: str) -> str:
        """Extract the unit word from help text, if the text describes a count.

        Args:
            help_text: The definition's help text.

        Returns:
            The unit word (e.g., 'sites', 'devices'), or empty string if not found.
        """
        import re

        # Look for "The count of <units> in/the/on" or "The count of <units>."
        match = re.search(r"The count of ([a-z_]+)(?:s)?\b", help_text, re.IGNORECASE)
        if match:
            units = match.group(1)
            # Pluralize if needed for readability in SNMP output
            if not units.endswith("s"):
                units += "s"
            return units
        return ""


class MibWriter:
    """Turns the resolved object set into SMIv2 text."""

    def __init__(self, mapper: SnmpTypeMapper) -> None:
        """Record the type rule that every object block reads.

        Args:
            mapper: The type rule.
        """
        self._mapper = mapper  # Every object block asks this rule for its SYNTAX and its UNITS.

    def render(self, objects: tuple[MibObject, ...], updated: str) -> str:
        """Return the whole SMIv2 module text.

        Args:
            objects: Every object of the MIB, live and obsolete.
            updated: The `LAST-UPDATED` value, in the SMIv2 time form.

        Returns:
            The module text.
        """
        logger.info("%s Rendering %d objects into the MIB text", LOG_PREFIX, len(objects))  # Log before the render.
        by_scope = {scope: [item for item in objects if item.scope is scope] for scope in MetricScope}
        parts = [self._header(updated), self._org_section(by_scope[MetricScope.ORG])]
        parts.extend(self._table_section(scope, by_scope[scope]) for scope in TABLE_SCOPES)
        parts.append(self._conformance(by_scope))
        logger.debug("%s Rendered %d module sections", LOG_PREFIX, len(parts))  # Log the result count.
        text = "\n".join(parts) + "\nEND\n"  # The whole module, before the comment check below.
        self.check_comments(text)  # A broken comment makes every object of the module unreadable.
        return text

    @staticmethod
    def check_comments(text: str) -> None:
        """Stop when a comment line closes itself and leaves live code behind.

        Why:
            ASN.1 opens a comment at two hyphens, and it closes that comment at
            the next two hyphens on the same line. A command line flag such as
            the generate flag therefore ends the comment, and the parser reads
            the rest of the line as code. A real generated module carried the
            flag in its header. Net-SNMP reported `Bad operator (IMPORTS)` 30
            lines later, and every object of the module answered `Unknown
            Object Identifier`.

            The message names the wrong line, so this check exists to name the
            right one. A quoted string carries two hyphens safely, so the cure
            is to move the text into a DESCRIPTION.

        Args:
            text: The whole module text.

        Raises:
            MibRenderError: When a comment line holds text after it closes.
        """
        for number, line in enumerate(text.splitlines(), start=1):  # Report the true line number to the reader.
            body = line.split(COMMENT_MARKER, 1)  # Everything before the first marker is code, which is fine.
            if len(body) < 2:  # The line opens no comment, so no comment can close early.
                continue
            # WHY: a run of hyphens is a rule line. It closes and reopens the
            # comment, it carries no other character, and every parser accepts
            # it. Only a hyphen pair with real text after it is a fault.
            remainder = body[1].replace(HYPHEN, "")  # Drop every hyphen, so a rule line becomes blank.
            if COMMENT_MARKER in body[1] and remainder.strip():
                raise MibRenderError(
                    f"Line {number} closes its comment early, because it holds two hyphens together: {line.strip()!r}. "
                    "ASN.1 reads the rest of that line as code. Move the text into a quoted DESCRIPTION."
                )

    @staticmethod
    def _header(updated: str) -> str:
        """Return the module comment, the imports, and the MODULE-IDENTITY.

        Args:
            updated: The `LAST-UPDATED` value.

        Returns:
            The header text.
        """
        root = DEFAULT_BASE_OID.strip(".").split(".")  # Split the OID into segments.
        # Skip the enterprises prefix (1.3.6.1.4.1) to get the rest of the OID.
        sub_oid_numbers = root[6:]  # enterprises is exactly 6 components.
        sub_oid_str = " ".join(sub_oid_numbers)  # Format as space-separated numbers for ASN.1.
        return _HEADER_TEMPLATE.format(
            module=MODULE_NAME,
            root=MODULE_ROOT,
            updated=updated,
            oid_tail=sub_oid_str,
        )

    def _org_section(self, objects: list[MibObject]) -> str:
        """Return the organization scalars.

        Args:
            objects: The objects of the organization scope.

        Returns:
            The section text.
        """
        subtree = SUBTREE_BY_SCOPE[MetricScope.ORG]  # The scalars answer at `<base>.1.<column>.0`.
        lines = [_SECTION_RULE, _ORG_NODE_TEMPLATE.format(root=MODULE_ROOT, subtree=subtree)]
        lines.extend(self._object_block(item, "mistOrg") for item in _in_column_order(objects))
        return "\n".join(lines)

    def _table_section(self, scope: MetricScope, objects: list[MibObject]) -> str:
        """Return one whole table, from the table node to the index column.

        Args:
            scope: The table to render.
            objects: The objects of that scope.

        Returns:
            The section text.
        """
        word = SCOPE_WORD[scope]  # The word that names every descriptor of this table.
        ordered = _in_column_order(objects)
        rows = [f"{item.entry.descriptor} {self._sequence_type(item)}" for item in ordered]
        rows.append(f"mist{word}Identity DisplayString")  # The identity column repeats the label of the row.
        rows.append(f"mist{word}Index Integer32")  # The index column carries the position of the row.
        header = _TABLE_TEMPLATE.format(word=word, root=MODULE_ROOT, subtree=SUBTREE_BY_SCOPE[scope])
        sequence = _SEQUENCE_TEMPLATE.format(word=word, rows=",\n    ".join(rows))
        blocks = [self._object_block(item, f"mist{word}Entry") for item in ordered]
        return "\n".join([_SECTION_RULE, header, sequence, *blocks, _TAIL_TEMPLATE.format(word=word)])

    def _sequence_type(self, item: MibObject) -> str:
        """Return the bare type name that a SEQUENCE row carries.

        Why:
            SMIv2 forbids a size bound or a range inside a SEQUENCE, so a row
            names the base type only.

        Args:
            item: The object of the row.

        Returns:
            The base type name.
        """
        if item.definition is None:  # An obsolete object keeps a gauge, because it answers nothing.
            return GAUGE32
        syntax = self._mapper.syntax_for(item.definition, item.field)  # The full SYNTAX carries the refinement.
        return syntax.split(" ")[0]  # The first word is the type, and the rest is the bound or the value list.

    def _object_block(self, item: MibObject, parent: str) -> str:
        """Return the OBJECT-TYPE block of one reading.

        Args:
            item: The object to render.
            parent: The descriptor of the node the object hangs below.

        Returns:
            The block text.
        """
        if item.definition is None:  # Mist removed the field, so the number stays reserved under an obsolete name.
            return _OBSOLETE_TEMPLATE.format(name=item.entry.descriptor, parent=parent, number=item.entry.column)
        units = self._mapper.units_for(item.definition)  # An empty unit must emit no UNITS clause at all.
        return _OBJECT_TEMPLATE.format(
            name=item.entry.descriptor,
            syntax=self._mapper.syntax_for(item.definition, item.field),
            units=f'\n    UNITS "{units}"' if units else "",
            description=_describe(item),
            parent=parent,
            number=item.entry.column,
        )

    @staticmethod
    def _conformance(by_scope: dict[MetricScope, list[MibObject]]) -> str:
        """Return the object groups and the compliance statement.

        Args:
            by_scope: The objects of each scope.

        Returns:
            The conformance text.
        """
        groups = []  # One group for each scope, in the subtree order that the agent uses.
        for number, scope in enumerate(sorted(by_scope, key=lambda item: SUBTREE_BY_SCOPE[item]), start=1):
            names = [item.entry.descriptor for item in _in_column_order(by_scope[scope]) if item.definition]
            if scope in TABLE_SCOPES:  # A table also publishes the column that repeats the row identity.
                names.append(f"mist{SCOPE_WORD[scope]}Identity")
            groups.append(_GROUP_TEMPLATE.format(word=SCOPE_WORD[scope], rows=",\n        ".join(names), number=number))
        return "\n".join([_SECTION_RULE, _CONFORMANCE_TEMPLATE.format(root=MODULE_ROOT), *groups, _COMPLIANCE_TEMPLATE])


def _in_column_order(objects: list[MibObject]) -> list[MibObject]:
    """Return the objects of one scope, sorted by column.

    Args:
        objects: The objects of one scope.

    Returns:
        The objects, lowest column first.
    """
    return sorted(objects, key=lambda item: item.entry.column)


def _describe(item: MibObject) -> str:
    """Return the DESCRIPTION text of one reading, wrapped for SMIv2.

    Why:
        The OpenAPI file gives the words of Mist. The catalog gives the words of
        the gateway. The OpenAPI text wins when it exists, because it describes
        the field that Mist actually returns.

    Args:
        item: The object to describe.

    Returns:
        The description text, already indented for the block.
    """
    definition = item.definition  # A caller never renders a description for an obsolete object.
    if definition is None:  # A raise beats an assert here, because Python removes an assert under -O.
        raise ValueError(f"The object {item.entry.descriptor} is obsolete, so it carries no description.")
    source = item.field.description if item.field and item.field.description else definition.help_text
    scale = SCALE_SENTENCE.get(definition.snmp_scale, "")  # A scaled reading must name its scale in plain words.
    sentences = [source.strip(), scale, f"The gateway names this reading {definition.name}."]
    return "\n         ".join(_wrap(" ".join(part for part in sentences if part)))


def _wrap(text: str, width: int = 62) -> list[str]:
    """Break one paragraph into lines that fit inside an SMIv2 block.

    Args:
        text: The paragraph to break.
        width: The largest line length.

    Returns:
        The lines.
    """
    lines: list[str] = [""]  # The first line grows until it reaches the width.
    for word in text.split():  # A word never breaks, because a broken identifier would mislead a reader.
        if lines[-1] and len(lines[-1]) + len(word) + 1 > width:
            lines.append("")
        lines[-1] = f"{lines[-1]} {word}".strip()
    return lines


_SECTION_RULE = "-- ---------------------------------------------------------------------"

_HEADER_TEMPLATE = """{module} DEFINITIONS ::= BEGIN

-- =====================================================================
-- This file is generated. Do not edit it by hand.
--
-- The generator is src/mib_generator. Run it again after Mist ships a
-- new OpenAPI file. The MODULE-IDENTITY description below names the
-- exact command.
--
-- Warning: never write two hyphens together inside a comment of this
-- file. ASN.1 opens a comment at two hyphens and it closes the comment
-- at the next two hyphens. A command line flag inside a comment
-- therefore ends the comment, and the parser then reads the rest of the
-- line as code. That defect made a whole generated module unreadable,
-- and every object of it answered "Unknown Object Identifier". A quoted
-- string carries two hyphens safely, so put a flag in a DESCRIPTION.
--
-- The generator reads three inputs:
--   documentation/mist-api-openapi31json.json  the Mist field types.
--   src/metrics_gateway/catalog.py             the readings the agent
--                                              answers.
--   data/mib_generator/oid_assignments.json    the number of each
--                                              field, so no OID moves.
--
-- OID layout
--   A scalar answers at <base>.<subtree>.<column>.0
--   A table cell answers at <base>.<subtree>.1.<column>.<row>
--
--   Subtree 1 holds the organization scalars.
--   Subtree 2 holds the site table.
--   Subtree 3 holds the device table.
--   Subtree 4 holds the service level expectation table.
--
--   Column 99 of each table repeats the row identity, because SNMP
--   carries no label. A poller that reads row 4 uses column 99 to
--   learn which site, device, or expectation row 4 describes.
--
-- Row numbers
--   A row number is a position, not a permanent key. The agent sorts
--   the rows on each read of Mist Cloud. Read column 99 to identify a
--   row. Do not treat a row number as a stable identifier.
--
-- Enterprise number
--   The OID tail {oid_tail} is a high number chosen for this deployment.
--   Caution: this child is not a registered assignment. Request a
--   branch from Hewlett Packard Enterprise before you distribute this
--   module outside your own network.
-- =====================================================================

IMPORTS
    MODULE-IDENTITY, OBJECT-TYPE, OBJECT-IDENTITY,
    enterprises, Gauge32, Counter64, Integer32
        FROM SNMPv2-SMI
    MODULE-COMPLIANCE, OBJECT-GROUP
        FROM SNMPv2-CONF
    DisplayString
        FROM SNMPv2-TC;

{root} MODULE-IDENTITY
    LAST-UPDATED "{updated}"
    ORGANIZATION "MistHelper project"
    CONTACT-INFO
        "MistHelper project maintainers
         https://github.com/jmorrison-juniper/MistHelper"
    DESCRIPTION
        "The read-only SNMP view of Mist Cloud health that the
         MistHelper metrics gateway collects from the Mist REST API.
         The gateway reads Mist Cloud on a timer and answers every
         request from memory, so a poll never waits for Mist Cloud."
    REVISION "{updated}"
    DESCRIPTION
        "The generator writes this module. Run it again after Mist ships
         a new OpenAPI file:  python MistHelper.py --mib-generate

         An earlier hand-written module put each table one level too
         deep, so no table object was reachable by name. The generator
         places a table cell at <base>.<subtree>.1.<column>.<row>, which
         is the address the agent answers."
    ::= {{ enterprises {oid_tail} }}
"""

_ORG_NODE_TEMPLATE = """-- Subtree {subtree}: the organization scalars.
-- Each object answers at <base>.{subtree}.<column>.0
{{root_rule}}

mistOrg OBJECT-IDENTITY
    STATUS current
    DESCRIPTION
        "The scalars that describe the whole Mist organization."
    ::= {{ {root} {subtree} }}
""".replace("{{root_rule}}", _SECTION_RULE)

_TABLE_TEMPLATE = """-- Subtree {subtree}: the {word} table.
-- Each cell answers at <base>.{subtree}.1.<column>.<row>
{{rule}}

mist{word}Table OBJECT-TYPE
    SYNTAX SEQUENCE OF Mist{word}Entry
    MAX-ACCESS not-accessible
    STATUS current
    DESCRIPTION
        "One row for each {word} record that the gateway reads."
    ::= {{ {root} {subtree} }}

mist{word}Entry OBJECT-TYPE
    SYNTAX Mist{word}Entry
    MAX-ACCESS not-accessible
    STATUS current
    DESCRIPTION
        "The readings of one row. Read mist{word}Identity to learn
         which record the row describes."
    INDEX {{ mist{word}Index }}
    ::= {{ mist{word}Table 1 }}
""".replace("{{rule}}", _SECTION_RULE)

_SEQUENCE_TEMPLATE = """
Mist{word}Entry ::= SEQUENCE {{
    {rows}
}}
"""

_OBJECT_TEMPLATE = """
{name} OBJECT-TYPE
    SYNTAX {syntax}{units}
    MAX-ACCESS read-only
    STATUS current
    DESCRIPTION
        "{description}"
    ::= {{ {parent} {number} }}
"""

_OBSOLETE_TEMPLATE = """
{name} OBJECT-TYPE
    SYNTAX Gauge32
    MAX-ACCESS read-only
    STATUS obsolete
    DESCRIPTION
        "Mist removed the field that this object reported. The number
         stays reserved, and the gateway answers nothing here."
    ::= {{ {parent} {number} }}
"""

_TAIL_TEMPLATE = f"""
mist{{word}}Identity OBJECT-TYPE
    SYNTAX {DISPLAY_STRING}
    MAX-ACCESS read-only
    STATUS current
    DESCRIPTION
        "The identity of the record in this row. SNMP carries no label,
         so read this object to learn which record the row number
         describes."
    ::= {{{{ mist{{word}}Entry {ROW_IDENTITY_COLUMN} }}}}

mist{{word}}Index OBJECT-TYPE
    SYNTAX {INDEX_SYNTAX}
    MAX-ACCESS not-accessible
    STATUS current
    DESCRIPTION
        "The position of the row. The agent counts from 1. The agent
         does not answer a request for this object, because the row
         number is already the last part of every cell OID."
    ::= {{{{ mist{{word}}Entry {INDEX_COLUMN} }}}}
"""

_CONFORMANCE_TEMPLATE = """-- Conformance
{{rule}}

mistHelperConformance OBJECT-IDENTITY
    STATUS current
    DESCRIPTION
        "The groups and the compliance statement of this module."
    ::= {{ {root} 100 }}

mistHelperGroups OBJECT-IDENTITY
    STATUS current
    DESCRIPTION "The object groups of this module."
    ::= {{ mistHelperConformance 1 }}

mistHelperCompliances OBJECT-IDENTITY
    STATUS current
    DESCRIPTION "The compliance statements of this module."
    ::= {{ mistHelperConformance 2 }}
""".replace("{{rule}}", _SECTION_RULE)

_GROUP_TEMPLATE = """
mist{word}Group OBJECT-GROUP
    OBJECTS {{
        {rows}
    }}
    STATUS current
    DESCRIPTION "The objects of the {word} scope."
    ::= {{ mistHelperGroups {number} }}
"""

_COMPLIANCE_TEMPLATE = """
mistHelperCompliance MODULE-COMPLIANCE
    STATUS current
    DESCRIPTION
        "The gateway serves every object of this module as read-only.
         The gateway refuses every write request, because it never
         changes Mist Cloud."
    MODULE
        MANDATORY-GROUPS {
            mistOrgGroup,
            mistSiteGroup,
            mistDeviceGroup,
            mistSleGroup
        }
    ::= { mistHelperCompliances 1 }
"""
