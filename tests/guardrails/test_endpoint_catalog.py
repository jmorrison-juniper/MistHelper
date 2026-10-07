"""Guardrail: every endpoint family operation owns a description and a safety flag.

Why:
    Menus 259 through 268 offer 284 read operations. Each sub-menu listed the
    raw operationId alone, so an operator read `getOrgWlan` and learned neither
    what the call reads nor whether it changes the Mist cloud.

    `src/operations/exporting/export/endpoint_catalog.py` now holds one description and one safety
    flag for each operation. A later change can add a row to an operation table
    and forget the catalog. The sub-menu would then print a bare name again,
    and the fallback would mark a plain read as interactive.

    These tests read both operation tables and the catalog. They fail when the
    two drift apart, when a safety word leaves the registry vocabulary, or when
    a call that changes the Mist cloud enters a family.
"""

from __future__ import annotations

import ast
import hashlib
import json
import logging
from collections.abc import Iterable, Mapping, Sized
from itertools import chain
from pathlib import Path
from typing import Any, Literal, cast
from unittest.mock import MagicMock, Mock

import pytest

from src.foundation.support.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES
from src.operations.exporting.export.endpoint_catalog import (
    DESTRUCTIVE,
    ENDPOINT_CATALOG,
    INTERACTIVE_SAFE,
    SAFE,
    SAFETY_LABELS,
    VALID_SAFETY,
    EndpointInfo,
    describe,
    menu_text,
)
from src.operations.exporting.export.endpoint_family_exporter import (
    _MSP_DETAIL_OPS,
    _ORG_DETAIL_OPS,
    _OTHER_DETAIL_OPS,
    _SITE_DETAIL_OPS,
    _SITE_MAP_OPS,
    _SITE_SLE_OPS,
    _EndpointFamilyOp,
)
from src.operations.exporting.export.simple_endpoint_exporter import (
    _MSP_OPS,
    _NONE_OPS,
    _ORG_OPS,
    _SITE_OPS,
    _SimpleEndpointOp,
)

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

EXPECTED_OPERATION_COUNT = 284  # Issue #1807 delivered 286 before the two exact retirements.

RegistrationKind = Literal["selectable", "catalog", "pk"]
RegistrationInput = (
    Iterable[_EndpointFamilyOp | _SimpleEndpointOp] | Mapping[str, EndpointInfo | Mapping[str, object]] | None
)
GuardDecision = tuple[bool, int, tuple[str, ...]]
RETIRED_IDENTIFIERS = ("getSiteSleSummary", "getSiteSleClassifierDetails")
DEPRECATED_SCENARIOS = ("live", "injected", "empty", "missing", "shape", "record", "unreadable", "partial")
REGISTRATION_TYPES = {
    "selectable": (_EndpointFamilyOp, _SimpleEndpointOp),
    "catalog": (EndpointInfo,),
    "pk": (Mapping,),
}
PK_FIELDS = (("type", str), ("primary_key", list), ("indexes", list))
MENU_263_TITLE = "Run any site SLE endpoint with scope prompts (15 operations)"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(params=("selectable", "catalog", "pk"))
def deprecated_source(request: pytest.FixtureRequest) -> tuple[RegistrationKind, RegistrationInput]:
    """Read raw registrations separately from isolated negative controls."""
    kind = cast(RegistrationKind, request.param)
    sources: dict[RegistrationKind, RegistrationInput] = {
        "selectable": tuple(row for _menu, table in ALL_TABLES for row in table),
        "catalog": ENDPOINT_CATALOG,
        "pk": ENDPOINT_PRIMARY_KEY_STRATEGIES,
    }
    return kind, sources[kind]


@pytest.fixture
def deprecated_injection(identifier: str) -> dict[RegistrationKind, object]:
    """Construct the original obsolete row and valid matching metadata."""
    classifier = identifier == "getSiteSleClassifierDetails"
    required = ("site_id", "scope", "scope_id", "metric") + (("classifier",) if classifier else ())
    description = "Get site SLE classifier details" if classifier else "Get site SLE summary"
    return {
        "selectable": _EndpointFamilyOp(
            identifier, "mistapi.api.v1.sites.sle", required, (1212 if classifier else 1216,)
        ),
        "catalog": EndpointInfo(description + " (needs scope, scope ID, metric)", INTERACTIVE_SAFE),
        "pk": {
            "type": "auto_increment_with_unique",
            "primary_key": ["misthelper_internal_id"],
            "indexes": list(required),
            "unique_constraints": [],
            "description": "Endpoint family export for " + identifier,
        },
    }


@pytest.fixture
def deprecated_copy(
    deprecated_source: tuple[RegistrationKind, RegistrationInput],
    deprecated_injection: dict[RegistrationKind, object],
    identifier: str,
) -> list[tuple[str, object]]:
    """Inject one original registration into an isolated source copy."""
    kind, source = deprecated_source
    if isinstance(source, Mapping):
        pairs = list(source.items())
    else:
        rows = cast(Iterable[_EndpointFamilyOp | _SimpleEndpointOp], source)
        pairs = [(row.operation, row) for row in rows]
    pairs = [(name, record) for name, record in pairs if name not in RETIRED_IDENTIFIERS]
    return pairs + [(identifier, deprecated_injection[kind])]


@pytest.fixture
def deprecated_registration_case(
    deprecated_source: tuple[RegistrationKind, RegistrationInput],
    deprecated_copy: list[tuple[str, object]],
    identifier: str,
    scenario: str,
) -> tuple[RegistrationInput, GuardDecision]:
    """Keep live inputs intact and prepare measured fail-closed controls."""
    kind, source = deprecated_source
    if scenario == "live":
        return source, (True, len(cast(Sized, source)), ())
    if scenario in ("unreadable", "partial"):
        failure = iter(Mock(side_effect=OSError("registration read failed")), None)
        iterator = chain(deprecated_copy[:1] if scenario == "partial" else (), failure)
        broken = MagicMock(spec=dict if kind != "selectable" else Iterable)
        target = broken.items if kind != "selectable" else broken.__iter__
        target.return_value = iterator if kind != "selectable" else (record for _name, record in iterator)
        return broken, (False, int(scenario == "partial"), ("OSError: registration read failed",))
    records = deprecated_copy if scenario == "injected" else []
    prepared: object = dict(records) if kind != "selectable" else [record for _name, record in records]
    controls = {"missing": None, "shape": 3335, "record": {"invalid": None}}
    if scenario in controls:
        prepared = controls[scenario] if kind != "selectable" or scenario != "record" else [None]
    errors = {"empty": "empty input", "record": "TypeError: invalid registration"}
    findings = (identifier,) if scenario == "injected" else (errors.get(scenario, "TypeError: invalid input shape"),)
    return cast(RegistrationInput, prepared), (False, len(records), findings)


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

    @staticmethod
    def _deprecated_decision(kind: RegistrationKind, source: RegistrationInput) -> GuardDecision:
        """Reject obsolete, malformed, empty, and partially unreadable sources."""
        checked, findings = 0, []
        logging.info("Inspecting %s registrations for retired operations", kind)
        try:
            if not isinstance(source, Iterable) or isinstance(source, Mapping) != (kind != "selectable"):
                raise TypeError("invalid input shape")
            records = source.items() if isinstance(source, Mapping) else enumerate(source)
            for name, record in records:
                name = getattr(record, "operation", None) if kind == "selectable" else name
                if not isinstance(record, REGISTRATION_TYPES[kind]) or not isinstance(name, str) or not name:
                    raise TypeError("invalid registration")
                if isinstance(record, Mapping) and not all(
                    isinstance(record.get(key), value) for key, value in PK_FIELDS
                ):
                    raise TypeError("invalid registration")
                checked += 1
                if name in RETIRED_IDENTIFIERS:
                    findings.append(name)
        except (OSError, TypeError, AttributeError) as error:
            return False, checked, (f"{type(error).__name__}: {error}",)
        finally:
            logging.debug("Inspected %s %s registrations and found %s retired operations", checked, kind, len(findings))
        return checked > 0 and not findings, checked, tuple(findings) if checked else ("empty input",)

    @pytest.mark.parametrize("identifier", RETIRED_IDENTIFIERS)
    @pytest.mark.parametrize("scenario", DEPRECATED_SCENARIOS)
    def test_deprecated_registrations(
        self,
        identifier: str,
        scenario: str,
        deprecated_source: tuple[RegistrationKind, RegistrationInput],
        deprecated_registration_case: tuple[RegistrationInput, GuardDecision],
    ) -> None:
        """Each live absence assertion also owns shaped negative controls."""
        kind, _raw_source = deprecated_source
        source, expected = deprecated_registration_case
        decision = self._deprecated_decision(kind, source)
        message = f"{kind} {scenario} inspected {decision[1]} records: {decision[2]}"
        if scenario == "live":
            assert identifier not in decision[2], f"{kind} contains {identifier}. {message}"
        assert decision == expected, message


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

    @staticmethod
    def _menu_definition(tree: ast.Module, name: str) -> ast.Dict:
        """Read a complete named menu mapping and reject missing metadata."""
        targets: tuple[ast.expr, ...]
        for node in tree.body:
            if isinstance(node, ast.AnnAssign):
                targets = (node.target,)
            elif isinstance(node, ast.Assign):
                targets = tuple(node.targets)
            else:
                continue
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                assert isinstance(node.value, ast.Dict), f"Menu mapping {name} is not a dictionary."
                return node.value
        raise AssertionError(f"Menu mapping {name} is missing.")

    @pytest.mark.parametrize(
        "source,message",
        (
            ("", r"Menu mapping menu_actions is missing\."),
            ("menu_actions = None", r"Menu mapping menu_actions is not a dictionary\."),
            ("menu_actions: dict[str, str] = None", r"Menu mapping menu_actions is not a dictionary\."),
        ),
    )
    def test_menu_definition_rejects_invalid_metadata(self, source: str, message: str) -> None:
        """The metadata guard cannot accept an absent or malformed mapping."""
        tree = ast.parse(source)
        print(f"Checked {len(tree.body)} menu declarations.")
        with pytest.raises(AssertionError, match=message):
            self._menu_definition(tree, "menu_actions")

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

    @pytest.mark.parametrize(
        "path,prefix",
        (
            ("MistHelper.py", 'title="Run any site SLE endpoint'),
            ("web_portal/menu_registry.py", '"263": '),
            ("documentation/menu-highlights.md", "| 263 |"),
        ),
    )
    def test_menu_263_fixed_labels(self, path: str, prefix: str) -> None:
        """Each actual fixed menu row promises exactly the supported count."""
        logging.info("Reading the fixed menu 263 label from %s", path)
        body = (REPOSITORY_ROOT / path).read_text(encoding="utf-8")
        logging.debug("Read %s characters for the label in %s", len(body), path)
        lines = [line.strip() for line in body.splitlines() if line.strip().startswith(prefix)]
        assert len(lines) == 1
        line = lines[0]
        if path == "MistHelper.py":
            label = ast.literal_eval(line.removeprefix("title=").rstrip(","))
        elif path == "web_portal/menu_registry.py":
            label = ast.literal_eval(line.partition(": ")[2].rstrip(","))
        else:
            label = line.split("|")[2].strip()
        assert label == MENU_263_TITLE

    @pytest.mark.parametrize(
        "path,count,expected",
        (
            ("MistHelper.py", 293, "c5b170786bf10934dc4808dd98142ebc91f4c79328cccbe7854d42a4866c959c"),
            ("web_portal/menu_registry.py", 179, "8107cfce5b5c495866486057c28acf24928d1a90530775389dc4b16b82b77430"),
        ),
    )
    def test_menu_263_complete_identity(self, path: str, count: int, expected: str) -> None:
        """The one allowed title edit preserves all other menu metadata."""
        body = (REPOSITORY_ROOT / path).read_text(encoding="utf-8")
        tree = ast.parse(body.replace(MENU_263_TITLE.replace("(15 operations)", "(17 operations)"), MENU_263_TITLE))
        name = "menu_actions" if path == "MistHelper.py" else "MENU_DESCRIPTIONS"
        definition = TestDescriptions._menu_definition(tree, name)
        identifiers = {ast.literal_eval(key) for key in definition.keys if isinstance(key, ast.Constant)}
        assert len(identifiers) == count
        if path == "MistHelper.py":
            values: object = ast.dump(definition, include_attributes=False)
        else:
            values = ast.literal_eval(definition)
        payload = json.dumps(values, sort_keys=True, separators=(",", ":")).encode()
        assert hashlib.sha256(payload).hexdigest() == expected
