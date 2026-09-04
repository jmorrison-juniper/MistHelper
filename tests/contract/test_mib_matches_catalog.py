"""Tests that hold the MIB to the OID layout the agent serves.

Why:
    The agent and the MIB are two files that must agree. The agent decides the
    number of every reading, and the MIB gives that number a name. A change to
    one file without a change to the other breaks every name a monitoring
    system shows, and the break is silent: `snmpwalk` still returns the number,
    and Observium still draws the graph under the wrong label.

    A real defect proved the risk. An earlier MIB placed each table one level
    too deep, so `mistDeviceReceivedBytes` translated to
    `<base>.3.1.1.11` while the agent answered at `<base>.3.1.11.<row>`. Every
    table object was unreachable by name.

    These tests parse the MIB text directly. They need no `snmptranslate`
    binary, so they run on a workstation and in the build.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.metrics_gateway.catalog import (
    ROW_IDENTITY_COLUMN,
    SUBTREE_BY_SCOPE,
    MetricCatalog,
    MetricKind,
    MetricScope,
)
from src.metrics_gateway.snmp import DEFAULT_BASE_OID

MIB_PATH = Path(__file__).resolve().parents[2] / "documentation" / "mibs" / "MISTHELPER-MIB.mib"

# WHY: The agent places a table cell at `<base>.<subtree>.1.<column>.<row>`. In
# MIB terms the table node carries the subtree number, the entry node carries
# the 1, and the column object carries the column number.
TABLE_ROOT_BY_SCOPE = {
    MetricScope.SITE: "mistSiteTable",
    MetricScope.DEVICE: "mistDeviceTable",
    MetricScope.SLE: "mistSleTable",
}
ENTRY_BY_SCOPE = {
    MetricScope.SITE: "mistSiteEntry",
    MetricScope.DEVICE: "mistDeviceEntry",
    MetricScope.SLE: "mistSleEntry",
}

# WHY: An SNMP type must match the metric kind, or a poller stores the wrong
# thing. A byte count needs 64 bits, because a Mist byte count passes the
# 32-bit limit within one day.
SYNTAX_BY_KIND = {
    MetricKind.INFO: "DisplayString",
    MetricKind.GAUGE: "Gauge32",
    MetricKind.COUNTER: "Counter64",
}


@pytest.fixture(scope="module")
def mib_text() -> str:
    """Read the MIB once for every test in this module.

    Returns:
        The whole MIB source text.
    """
    assert MIB_PATH.is_file(), f"The MIB is missing at {MIB_PATH}"
    return MIB_PATH.read_text(encoding="utf-8")


def _assignments(text: str) -> dict[str, tuple[str, int]]:
    """Collect every `name ::= { parent number }` assignment of the MIB.

    Args:
        text: The MIB source text.

    Returns:
        The parent name and the number, keyed by the object name.
    """
    found: dict[str, tuple[str, int]] = {}
    # WHY: an assignment can wrap across lines, so the pattern spans whitespace.
    pattern = re.compile(r"^\s*([a-z][A-Za-z0-9]*)\s+OBJECT", re.MULTILINE)
    for match in pattern.finditer(text):
        name = match.group(1)
        tail = text[match.end() :]
        place = re.search(r"::=\s*\{\s*([A-Za-z0-9]+)\s+(\d+)\s*\}", tail)
        if place:  # An object without an assignment is a syntax fault the parse test catches.
            found[name] = (place.group(1), int(place.group(2)))
    return found


def _numeric_oid(name: str, table: dict[str, tuple[str, int]]) -> tuple[int, ...]:
    """Walk an object name up to the module root and return its numbers.

    Args:
        name: The object name to resolve.
        table: Every assignment of the MIB.

    Returns:
        The sub-identifiers below the module root, outermost first.
    """
    parts: list[int] = []
    current = name
    while current != "mistHelperMIB":  # The module root ends the walk.
        assert current in table, f"The MIB does not define {current}"
        parent, number = table[current]
        parts.append(number)
        current = parent
    return tuple(reversed(parts))


class TestMibRoot:
    """The MIB root and the agent base OID must name the same branch."""

    def test_the_module_root_matches_the_agent_base_oid(self, mib_text: str) -> None:
        """A different root makes every translation wrong."""
        match = re.search(r"::=\s*\{\s*enterprises\s+(\d+)\s+(\d+)\s*\}", mib_text)
        assert match, "The MIB does not assign the module root below `enterprises`"
        root = f".1.3.6.1.4.1.{match.group(1)}.{match.group(2)}"
        assert root == DEFAULT_BASE_OID


class TestScalarColumns:
    """Every organization scalar needs a MIB object at its own column."""

    def test_each_organization_scalar_has_a_matching_object(self, mib_text: str) -> None:
        """A scalar answers at `<base>.1.<column>.0`, so the MIB needs `mistOrg <column>`."""
        table = _assignments(mib_text)
        subtree = SUBTREE_BY_SCOPE[MetricScope.ORG]
        defined = {_numeric_oid(name, table) for name, (parent, _number) in table.items() if parent == "mistOrg"}
        for definition in MetricCatalog().for_scope(MetricScope.ORG):
            expected = (subtree, definition.column)
            assert expected in defined, f"The MIB has no object at {expected} for {definition.name}"


class TestTableColumns:
    """Every table column needs a MIB object at the exact depth the agent uses."""

    @pytest.mark.parametrize("scope", [MetricScope.SITE, MetricScope.DEVICE, MetricScope.SLE])
    def test_the_table_sits_directly_below_the_module_root(self, mib_text: str, scope: MetricScope) -> None:
        """The agent uses `<base>.<subtree>` for the table itself, with no node between."""
        table = _assignments(mib_text)
        assert _numeric_oid(TABLE_ROOT_BY_SCOPE[scope], table) == (SUBTREE_BY_SCOPE[scope],)

    @pytest.mark.parametrize("scope", [MetricScope.SITE, MetricScope.DEVICE, MetricScope.SLE])
    def test_the_entry_sits_directly_below_the_table(self, mib_text: str, scope: MetricScope) -> None:
        """The agent uses `<base>.<subtree>.1` for the row entry."""
        table = _assignments(mib_text)
        assert _numeric_oid(ENTRY_BY_SCOPE[scope], table) == (SUBTREE_BY_SCOPE[scope], 1)

    @pytest.mark.parametrize("scope", [MetricScope.SITE, MetricScope.DEVICE, MetricScope.SLE])
    def test_each_column_has_a_matching_object(self, mib_text: str, scope: MetricScope) -> None:
        """A cell answers at `<base>.<subtree>.1.<column>.<row>`."""
        table = _assignments(mib_text)
        entry = ENTRY_BY_SCOPE[scope]
        defined = {_numeric_oid(name, table) for name, (parent, _number) in table.items() if parent == entry}
        for definition in MetricCatalog().for_scope(scope):
            expected = (SUBTREE_BY_SCOPE[scope], 1, definition.column)
            assert expected in defined, f"The MIB has no object at {expected} for {definition.name}"

    @pytest.mark.parametrize("scope", [MetricScope.SITE, MetricScope.DEVICE, MetricScope.SLE])
    def test_the_row_identity_column_is_defined(self, mib_text: str, scope: MetricScope) -> None:
        """SNMP carries no label, so the identity column tells a poller which row it read."""
        table = _assignments(mib_text)
        entry = ENTRY_BY_SCOPE[scope]
        defined = {_numeric_oid(name, table) for name, (parent, _number) in table.items() if parent == entry}
        expected = (SUBTREE_BY_SCOPE[scope], 1, ROW_IDENTITY_COLUMN)
        assert expected in defined, f"The MIB has no row identity column at {expected}"


class TestSyntax:
    """A byte count needs 64 bits, and a text reading needs a string type."""

    def test_every_counter_uses_a_sixty_four_bit_type(self, mib_text: str) -> None:
        """A 32-bit counter for a Mist byte count wraps within one day."""
        catalog = MetricCatalog()
        counters = [d for scope in MetricScope for d in catalog.for_scope(scope) if d.kind is MetricKind.COUNTER]
        assert counters, "The catalog defines no counter, so this test guards nothing"
        assert mib_text.count("SYNTAX Counter64") >= len(counters)

    def test_the_module_names_every_expected_syntax(self, mib_text: str) -> None:
        """Each metric kind needs its own SNMP type present in the module."""
        for syntax in SYNTAX_BY_KIND.values():
            assert syntax in mib_text, f"The MIB never uses the type {syntax}"
