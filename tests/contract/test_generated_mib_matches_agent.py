"""Proves that the generated MIB agrees with the running SNMP agent.

Why:
    A MIB that disagrees with the agent is worse than no MIB. A poller that
    reads a name from the MIB then gets `No Such Instance` from the agent, and
    the operator has no way to tell which of the two is wrong. These tests read
    the OID that `OidTree` builds and prove the MIB names the same place.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.metrics_gateway.catalog import ROW_IDENTITY_COLUMN, SUBTREE_BY_SCOPE, MetricCatalog, MetricScope
from src.metrics_gateway.snmp import DEFAULT_BASE_OID

REPO_ROOT = Path(__file__).resolve().parents[2]  # A pytest fixture moves the working folder, so every path is absolute.
MIB_PATH = REPO_ROOT / "documentation" / "mibs" / "MISTHELPER-MIB.mib"  # The file a monitoring system loads.
HAND_PATH = Path(__file__).parent / "fixtures" / "handwritten-MISTHELPER-MIB.mib"  # The pre-generator snapshot.
OBJECT_PATTERN = r"^(mist\w+)\s+OBJECT-TYPE(.*?)::=\s*\{\s*(\w+)\s+(\d+)\s*\}"  # One OBJECT-TYPE block.
ENTRY_NODE = 1  # The entry node of a table, which `OidTree` also uses.
SCALAR_INSTANCE = 0  # The instance part of a scalar, which `OidTree` also uses.
PARENT_SUBTREE = {
    "mistOrg": 1,  # The organization scalars hang below this node.
    "mistSiteEntry": 2,  # The site columns hang below the entry of the site table.
    "mistDeviceEntry": 3,  # The device columns hang below the entry of the device table.
    "mistSleEntry": 4,  # The expectation columns hang below the entry of the expectation table.
}


def _blocks(path: Path) -> dict[str, tuple[str, str, int]]:
    """Return every OBJECT-TYPE of one MIB file.

    Args:
        path: The MIB file to read.

    Returns:
        The body, the parent descriptor, and the number of each object.
    """
    text = path.read_text(encoding="utf-8")  # One read serves every assertion of the module.
    found = re.findall(OBJECT_PATTERN, text, re.S | re.M)
    return {name: (body, parent, int(number)) for name, body, parent, number in found}


@pytest.fixture(scope="module")
def generated() -> dict[str, tuple[str, str, int]]:
    """Return the objects of the generated MIB.

    Returns:
        The objects, keyed by descriptor.
    """
    return _blocks(MIB_PATH)


def test_every_catalog_reading_has_one_object(generated: dict[str, tuple[str, str, int]]) -> None:
    """Prove the MIB names every reading the agent answers."""
    catalog = MetricCatalog()  # The catalog decides what the agent answers, so it decides what the MIB must hold.
    places = {(PARENT_SUBTREE[parent], number) for _, parent, number in generated.values() if parent in PARENT_SUBTREE}
    for scope in MetricScope:  # A missing reading makes the agent answer an OID that no name reaches.
        for definition in catalog.for_scope(scope):
            assert (SUBTREE_BY_SCOPE[scope], definition.column) in places, definition.name


def test_a_table_column_sits_one_level_below_the_entry(generated: dict[str, tuple[str, str, int]]) -> None:
    """Prove no table gained an extra level.

    Why:
        An earlier hand-written MIB nested each table one level too deep, and
        every table object became unreachable by name. The agent answers a cell
        at `<base>.<subtree>.1.<column>.<row>` and nowhere else.
    """
    text = MIB_PATH.read_text(encoding="utf-8")  # The table and the entry assignments both live in this text.
    for word, subtree in (("Site", 2), ("Device", 3), ("Sle", 4)):  # Every table of the module.
        assert re.search(rf"mist{word}Table OBJECT-TYPE.*?::= {{ mistHelperMIB {subtree} }}", text, re.S)
        assert re.search(rf"mist{word}Entry OBJECT-TYPE.*?::= {{ mist{word}Table {ENTRY_NODE} }}", text, re.S)
        columns = [number for _, parent, number in generated.values() if parent == f"mist{word}Entry"]
        assert columns, word  # A table with no column would pass the two searches above and still be useless.


def test_the_identity_column_uses_the_catalog_number(generated: dict[str, tuple[str, str, int]]) -> None:
    """Prove the identity column sits where the agent answers it."""
    for word in ("Site", "Device", "Sle"):  # Every table repeats its row label on the same column.
        _, parent, number = generated[f"mist{word}Identity"]
        assert parent == f"mist{word}Entry"  # The identity is a column of the row, not a node of its own.
        assert number == ROW_IDENTITY_COLUMN  # `ROW_IDENTITY_COLUMN` decides this number for the agent.


def test_only_the_index_column_is_not_accessible(generated: dict[str, tuple[str, str, int]]) -> None:
    """Prove no readable object would answer `No Such Instance`.

    Why:
        Success criterion SC-006 says every readable object must answer. The
        index object is the one object the agent never answers, and SMIv2 marks
        it `not-accessible` for that reason.
    """
    for name, (body, parent, _) in generated.items():  # A readable object must map to a real reading.
        if "not-accessible" in body or parent not in PARENT_SUBTREE:
            continue
        assert "MAX-ACCESS read-only" in body, name
    for word in ("Site", "Device", "Sle"):  # The index of each table stays out of reach on purpose.
        assert "not-accessible" in generated[f"mist{word}Index"][0]


def test_the_module_names_the_base_oid_of_the_agent() -> None:
    """Prove the module root is the root the agent answers at."""
    text = MIB_PATH.read_text(encoding="utf-8")  # The MODULE-IDENTITY holds the two numbers below enterprises.
    parent, child = DEFAULT_BASE_OID.strip(".").split(".")[-2:]
    assert f"::= {{ enterprises {parent} {child} }}" in text


def test_no_hand_written_object_moved(generated: dict[str, tuple[str, str, int]]) -> None:
    """Prove the generator kept the number and the name of all 35 hand-written objects.

    Why:
        A monitoring system stores years of history against an OID. A renumber
        throws that history away without a warning.
    """
    hand = _blocks(HAND_PATH)  # The snapshot of the MIB that a person wrote before the generator existed.
    assert set(hand) <= set(generated)  # The generator must lose no object of the earlier module.
    for name, (_, parent, number) in hand.items():  # A move of either the parent or the number moves the OID.
        assert generated[name][1] == parent, name
        assert generated[name][2] == number, name


def test_a_scalar_answers_below_the_organization_node(generated: dict[str, tuple[str, str, int]]) -> None:
    """Prove the organization readings are scalars and not a table."""
    catalog = MetricCatalog()  # The organization scope holds one reading of each name, so it needs no row.
    columns = {number for _, parent, number in generated.values() if parent == "mistOrg"}
    for definition in catalog.for_scope(MetricScope.ORG):  # Each scalar answers at `<base>.1.<column>.0`.
        assert definition.column in columns, definition.name
    assert SCALAR_INSTANCE == 0  # The MIB states no instance part, because SMIv2 adds the zero itself.
