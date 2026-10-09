"""Read-only boundary checks for the Juniper integration (FR-006, FR-007, SC-005)."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

import re  # WHY: find each import of the HTTP library.
from pathlib import Path  # WHY: read the source files.

from src.foundation.support.refactors.endpoint_primary_key_strategies import (
    ENDPOINT_PRIMARY_KEY_STRATEGIES,  # WHY: the strategy table.
)
from src.foundation.support.utils.operation_registry import OperationRegistry  # WHY: the registry table.

REPO_ROOT = Path(__file__).resolve().parents[4]  # WHY: tests/unit/juniper_rma/workflows -> repository root.
PACKAGE = REPO_ROOT / "src" / "operations" / "exporting" / "juniper_rma"  # WHY: the code under test.
WRITE_OPERATION_NAMES = (  # WHY: Case and Asset operations that change a customer's data or issue an upload credential.
    "createsr",
    "updatesr",
    "escalatesr",
    "closesr",
    "attachfile",
    "getfileuploadtoken",
)
NEW_STRATEGY_NAMES = (  # WHY: the strategy names that the exports use.
    "juniperQuerySrList",
    "juniperQuerySrDetails",
    "juniperQuerySrDetailRecords",
    "juniperQueryRmaHeaders",
    "juniperQueryRmaDetails",
    "juniperQuerySrNoteDetails",
    "juniperGetLov",
    "juniperGetSoftwareEosLov",
    "juniperQueryAssetsBulkData",
    "juniperQueryAssetsBulkNoData",
    "juniperQueryAssetsDetails",
    "juniperQueryAssetCoverage",
    "juniperCorrelationLinks",
    "juniperRunRecords",
)


def _package_sources() -> list[Path]:
    """Return every Python file in the package, in a stable order."""
    return sorted(PACKAGE.rglob("*.py"))  # WHY: a stable order keeps the failure messages readable.


def test_no_write_operation_name_appears_in_the_package() -> None:
    """No source file names a Juniper operation that changes data or leaves the approved hosts."""
    for path in _package_sources():  # WHY: check every file.
        text = path.read_text(encoding="utf-8").lower()  # WHY: names are compared without case.
        for name in WRITE_OPERATION_NAMES:  # WHY: check each forbidden name.
            assert name not in text, f"{path.name} names the out-of-scope operation {name}"  # WHY: fail with the file.


def test_only_the_gateway_and_the_settings_import_the_http_library() -> None:
    """The gateway is the one network path. The settings module imports the library for typing only."""
    importers = sorted(  # WHY: list every file that imports the HTTP library.
        path.name
        for path in _package_sources()
        if re.search(r"^\s*(import requests|from requests)", path.read_text(encoding="utf-8"), re.MULTILINE)
    )
    assert importers == ["gateway.py", "settings.py"]  # WHY: no other module may open a connection.


def test_juniper_menus_are_registered_as_interactive_safe() -> None:
    """Each Juniper menu is registered in the interactive-safe category and never in the safe category."""
    for option in ("294", "295", "296", "297", "298", "299", "300", "301", "302", "303", "304"):  # WHY: all.
        assert OperationRegistry.skip_category(option) == "interactive_safe"  # WHY: never automatic under --test.


def test_every_juniper_export_has_a_key_strategy() -> None:
    """Each API name that an export uses has a primary key strategy (constitution database rule)."""
    for name in NEW_STRATEGY_NAMES:  # WHY: every export name.
        assert name in ENDPOINT_PRIMARY_KEY_STRATEGIES, f"{name} has no key strategy"  # WHY: fail with the name.
