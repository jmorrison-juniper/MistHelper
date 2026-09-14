"""Guardrail: every endpoint family operation owns a description and a safety flag.

Why:
    Menus 259 through 268 offer 286 read operations. Each sub-menu listed the
    raw operationId alone, so an operator read `getOrgWlan` and learned neither
    what the call reads nor whether it changes the Mist cloud.

    `src/export/endpoint_catalog.py` now holds one description and one safety
    flag for each operation. A later change can add a row to an operation table
    and forget the catalog. The sub-menu would then print a bare name again,
    and the fallback would mark a plain read as interactive.

    These tests read both operation tables and the catalog. They fail when the
    two drift apart, when a safety word leaves the registry vocabulary, or when
    a call that changes the Mist cloud enters a family.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.export.endpoint_catalog import (
    DESTRUCTIVE,
    ENDPOINT_CATALOG,
    INTERACTIVE_SAFE,
    SAFE,
    SAFETY_LABELS,
    VALID_SAFETY,
    describe,
    menu_text,
)
from src.export.endpoint_family_exporter import (
    _MSP_DETAIL_OPS,
    _ORG_DETAIL_OPS,
    _OTHER_DETAIL_OPS,
    _SITE_DETAIL_OPS,
    _SITE_MAP_OPS,
    _SITE_SLE_OPS,
)
from src.export.simple_endpoint_exporter import _MSP_OPS, _NONE_OPS, _ORG_OPS, _SITE_OPS

# The one table that needs no operator identifier. Only these rows may read
# `safe`, because `--test` runs that category without a prompt.
NO_IDENTIFIER_TABLE = _NONE_OPS

# Every table that a family menu offers, with the menu number that reaches it.
ALL_TABLES = (
    ("259", _NONE_OPS),
    ("260", _ORG_OPS),
    ("261", _SITE_OPS),
    ("262", _MSP_OPS),
    ("263", _SITE_SLE_OPS),
    ("264", _SITE_MAP_OPS),
    ("265", _SITE_DETAIL_OPS),
    ("266", _ORG_DETAIL_OPS),
    ("267", _MSP_DETAIL_OPS),
    ("268", _OTHER_DETAIL_OPS),
)

EXPECTED_OPERATION_COUNT = 286  # The count that issue #1807 delivered across ten families.


def table_operations() -> set[str]:
    """Return every operationId that a family menu offers.

    Returns:
        One name for each row of the ten operation tables.
    """
    return {row.operation for _menu, table in ALL_TABLES for row in table}


class TestCatalogCoverage:
    """The catalog and the operation tables name the same operations."""

    def test_every_operation_has_a_catalog_entry(self) -> None:
        """A missing entry makes the sub-menu print a bare operationId again."""
        missing = sorted(table_operations() - set(ENDPOINT_CATALOG))
        assert not missing, f"These operations have no catalog entry: {missing}"

    def test_the_catalog_holds_no_orphan_entry(self) -> None:
        """An entry for no table row records an operation that no menu reaches."""
        orphans = sorted(set(ENDPOINT_CATALOG) - table_operations())
        assert not orphans, f"These catalog entries reach no menu: {orphans}"

    def test_the_catalog_holds_every_family_operation(self) -> None:
        """The count states that no family lost a row in silence."""
        assert len(ENDPOINT_CATALOG) == EXPECTED_OPERATION_COUNT


class TestSafetyWords:
    """Each safety word comes from the registry vocabulary."""

    @pytest.mark.parametrize("menu,table", ALL_TABLES, ids=[menu for menu, _table in ALL_TABLES])
    def test_every_row_uses_a_valid_safety_word(self, menu: str, table: tuple[Any, ...]) -> None:
        """A word outside the vocabulary cannot route `--test` or `--testinteractive`."""
        for row in table:
            safety = ENDPOINT_CATALOG[row.operation].safety
            assert safety in VALID_SAFETY, f"Menu {menu} row {row.operation} uses the safety word {safety!r}"

    def test_no_family_operation_is_destructive(self) -> None:
        """A family menu offers reads only, so a write must never enter one."""
        writes = sorted(name for name, info in ENDPOINT_CATALOG.items() if info.safety == DESTRUCTIVE)
        assert not writes, f"These family operations claim to change the Mist cloud: {writes}"

    def test_only_the_no_identifier_table_is_safe(self) -> None:
        """`--test` runs `safe` without a prompt, so a row that prompts must not claim it."""
        plain = {row.operation for row in NO_IDENTIFIER_TABLE}
        marked = {name for name, info in ENDPOINT_CATALOG.items() if info.safety == SAFE}
        assert marked == plain, f"The safe set does not match menu 259. Difference: {marked ^ plain}"

    def test_every_other_row_is_interactive_safe(self) -> None:
        """A read that needs an identifier belongs to `--testinteractive`."""
        plain = {row.operation for row in NO_IDENTIFIER_TABLE}
        for name in table_operations() - plain:
            assert ENDPOINT_CATALOG[name].safety == INTERACTIVE_SAFE, f"{name} needs an identifier, so it prompts"

    def test_each_safety_word_has_an_operator_label(self) -> None:
        """The menu prints the label, so a missing one would show the code word."""
        for word in VALID_SAFETY:
            assert word in SAFETY_LABELS, f"The safety word {word!r} has no operator label"


class TestDescriptions:
    """Each description states what the endpoint reads."""

    def test_no_description_is_empty(self) -> None:
        """An empty description returns the operator to a bare operationId."""
        empty = sorted(name for name, info in ENDPOINT_CATALOG.items() if not info.description.strip())
        assert not empty, f"These entries hold no description: {empty}"

    def test_no_description_repeats_the_operation_name(self) -> None:
        """A description equal to the name tells the operator nothing new."""
        echoes = sorted(name for name, info in ENDPOINT_CATALOG.items() if info.description.strip() == name)
        assert not echoes, f"These descriptions repeat the operation name: {echoes}"

    def test_every_description_starts_with_a_capital(self) -> None:
        """One shape across the list keeps the sub-menu readable."""
        for name, info in ENDPOINT_CATALOG.items():
            first = info.description[0]
            assert first.isupper(), f"{name} starts its description with {first!r}"


class TestMenuText:
    """The printed line carries the name, the description, and the flag."""

    def test_the_line_holds_all_three_parts(self) -> None:
        """The operator reads the risk and the purpose from this one line."""
        line = menu_text("getSiteWlan")
        assert "getSiteWlan" in line
        assert ENDPOINT_CATALOG["getSiteWlan"].description in line
        assert "[safe interactive]" in line

    def test_a_plain_read_prints_the_safe_label(self) -> None:
        """Menu 259 needs no identifier, so its rows read `safe`."""
        assert menu_text("getSelf").endswith("[safe]")

    def test_an_unknown_operation_never_reads_as_plain_safe(self) -> None:
        """A forgotten row must fail closed, exactly as OperationRegistry does."""
        info = describe("operationThatNoTableHolds")
        assert info.safety == INTERACTIVE_SAFE
        assert info.description == "operationThatNoTableHolds"
