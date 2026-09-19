"""Guard the performance hook catalog against source drift.

Why:
    The catalog names files, symbols, and counts that can drift after a rebase.
"""

from __future__ import annotations  # Keep annotations stable during test collection.

import ast  # Parse Python files so the guard checks real syntax.
import csv  # Read the shipped catalog artifacts without extra dependencies.
import json  # Read the shipped summary artifacts without extra dependencies.
import logging  # Record scan steps for local diagnosis.
import subprocess  # Ask Git for the tracked Python files named by the spec.
from dataclasses import dataclass  # Keep scan records explicit and typed.
from pathlib import Path  # Resolve repository paths on Windows and Linux.

from tests.support.git_environment import (
    git_subprocess_environment,  # WHY: issue #3022, repair a partial editor git config set.
)

_LOGGER = logging.getLogger(__name__)  # Share one logger for this guard module.
_REPO_ROOT = Path(__file__).resolve().parents[2]  # Locate the repository root from tests/guardrails.
_ARTIFACT_ROOT = _REPO_ROOT / "specs" / "2448-misthelper-performance-monitoring" / "artifacts"  # Locate artifacts.


@dataclass(frozen=True)
class SymbolRecord:
    """Store one AST symbol from a Python file.

    Why:
        The guard needs exact symbol names and aggregate counts from one scan.
    """

    kind: str  # Keep the AST node type for summary counts.
    name: str  # Keep the local name for catalog rows that name a class.
    qualified_name: str  # Keep the dotted name for catalog rows that name a method.
    nesting_depth: int  # Keep the nesting depth for the nested symbol total.


class CatalogSourceScanner:
    """Scan tracked Python files and build a symbol index.

    Why:
        The specification promises that Git tracked files define the catalog base.
    """

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root  # Store the root so every path stays repository-relative.

    def tracked_python_paths(self) -> list[str]:
        """Return the tracked Python paths from Git.

        Why:
            The catalog uses this command as its source boundary.
        """
        _LOGGER.info("Reading tracked Python files from Git")  # Log the external command before it runs.
        result = subprocess.run(  # Use Git so generated and ignored files stay out of the scan.
            ["git", "ls-files", "*.py"],
            cwd=self.repo_root,
            check=True,
            capture_output=True,
            text=True,
            env=git_subprocess_environment(),  # WHY: issue #3022, a partial editor config set makes git stop.
        )
        paths = [line for line in result.stdout.splitlines() if line]  # Drop the final empty line, if present.
        _LOGGER.debug("Git returned %s tracked Python files", len(paths))  # Log the source set size.
        return sorted(paths)  # Return a stable order for direct artifact comparisons.

    def symbol_index(self, paths: list[str]) -> dict[str, list[SymbolRecord]]:
        """Return the AST symbols for each repository path.

        Why:
            The guard must resolve each catalog row to a real source symbol.
        """
        index: dict[str, list[SymbolRecord]] = {}  # Collect symbols by repository-relative path.
        _LOGGER.info("Parsing %s Python files for the catalog guard", len(paths))  # Log the scan size.
        for path in paths:  # Parse each tracked file that the catalog claims.
            index[path] = self._symbols_for(path)  # Store the exact symbols for this file.
        _LOGGER.debug("Parsed %s Python files for the catalog guard", len(index))  # Log the scan result size.
        return index  # Return the completed index for all assertions.

    def _symbols_for(self, relative_path: str) -> list[SymbolRecord]:
        source_path = self.repo_root / relative_path  # Convert the Git path to a local path.
        source_text = source_path.read_text(encoding="utf-8")  # Read source with the repository encoding.
        module_ast = ast.parse(source_text, filename=relative_path)  # Parse the file instead of matching text.
        visitor = SymbolVisitor()  # Create a visitor with an empty parent stack.
        visitor.visit(module_ast)  # Collect top-level and nested symbols from the parsed tree.
        return visitor.symbols  # Return the exact symbols found in this file.


class SymbolVisitor(ast.NodeVisitor):
    """Collect functions, asynchronous functions, and classes from an AST.

    Why:
        The catalog counts these symbols and names them in hook rows.
    """

    def __init__(self) -> None:
        self.stack: list[str] = []  # Track the current symbol parents.
        self.symbols: list[SymbolRecord] = []  # Store the collected symbols.

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._add(node, "FunctionDef")  # Record the function before its nested symbols.
        self.generic_visit(node)  # Visit nested functions or classes inside this function.
        self.stack.pop()  # Remove this function from the parent stack.

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._add(node, "AsyncFunctionDef")  # Record the asynchronous function before nested symbols.
        self.generic_visit(node)  # Visit nested symbols inside this asynchronous function.
        self.stack.pop()  # Remove this function from the parent stack.

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._add(node, "ClassDef")  # Record the class before its methods or nested classes.
        self.generic_visit(node)  # Visit methods or nested classes inside this class.
        self.stack.pop()  # Remove this class from the parent stack.

    def _add(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef, kind: str) -> None:
        name_parts = [*self.stack, node.name]  # Build a stable qualified name from AST parents.
        qualified_name = ".".join(name_parts)  # Match the dotted form used by the catalog.
        record = SymbolRecord(kind, node.name, qualified_name, len(self.stack))  # Keep all needed fields.
        self.symbols.append(record)  # Add this symbol to the file scan.
        self.stack.append(node.name)  # Make this symbol the parent for nested definitions.


class PerformanceHookCatalog:
    """Read the performance catalog artifacts.

    Why:
        The tests compare the generated files against the current source tree.
    """

    def __init__(self, artifact_root: Path) -> None:
        self.artifact_root = artifact_root  # Store the artifact root for all file reads.

    def inventory_rows(self) -> list[dict[str, str]]:
        return self._csv_rows("python-inventory.csv")  # Read the source inventory rows.

    def hook_rows(self) -> list[dict[str, str]]:
        return self._csv_rows("hook-catalog.csv")  # Read the hook catalog rows.

    def strategy_rows(self) -> list[dict[str, str]]:
        return self._csv_rows("strategy-coverage.csv")  # Read the strategy summary rows.

    def hook_summary(self) -> dict[str, object]:
        return self._json_object("hook-catalog-summary.json")  # Read the hook summary record.

    def scan_summary(self) -> dict[str, object]:
        return self._json_object("scan-summary.json")  # Read the scan summary record.

    def _csv_rows(self, name: str) -> list[dict[str, str]]:
        artifact_path = self.artifact_root / name  # Build the artifact path from a trusted name.
        _LOGGER.info("Reading catalog CSV artifact %s", artifact_path)  # Log the file read before it runs.
        with artifact_path.open(newline="", encoding="utf-8") as artifact_file:  # Open with a fixed encoding.
            rows = list(csv.DictReader(artifact_file))  # Parse the CSV into named columns.
        _LOGGER.debug("Read %s rows from %s", len(rows), name)  # Log the parsed row count.
        return rows  # Return the parsed CSV rows.

    def _json_object(self, name: str) -> dict[str, object]:
        artifact_path = self.artifact_root / name  # Build the artifact path from a trusted name.
        _LOGGER.info("Reading catalog JSON artifact %s", artifact_path)  # Log the file read before it runs.
        data = json.loads(artifact_path.read_text(encoding="utf-8"))  # Parse the JSON artifact.
        _LOGGER.debug("Read JSON keys from %s: %s", name, sorted(data))  # Log the top-level shape.
        return data  # Return the parsed JSON object.


class TestPerformanceHookCatalog:
    """Verify that the shipped catalog matches current source.

    Why:
        Main changes can add, remove, or rename Python files and symbols.
    """

    def test_inventory_names_only_files_that_still_exist(self) -> None:
        # WHY: the catalog is a snapshot, so a new file is normal and must not fail this gate.
        # A REMOVED or RENAMED file is real rot, because a catalog row then names nothing.
        scanner = CatalogSourceScanner(_REPO_ROOT)  # Create the source scanner for this repository.
        catalog = PerformanceHookCatalog(_ARTIFACT_ROOT)  # Create the artifact reader for this spec.
        tracked_paths = set(scanner.tracked_python_paths())  # Recreate the documented Git source set.
        inventory_paths = sorted(row["file_path"] for row in catalog.inventory_rows())  # Read artifact paths.
        stale = [path for path in inventory_paths if path not in tracked_paths]  # Find rows naming no file.
        assert not stale, "The catalog names files that no longer exist:\n" + "\n".join(stale)  # Report each one.

    def test_every_catalogued_file_still_parses(self) -> None:
        # WHY: the summary describes a snapshot the catalog took on one date. An exact symbol
        # count belongs to that snapshot, and live code changes its count for normal reasons.
        # Issue #2547: comparing a recorded count against live source failed the gate on every
        # unrelated change, and it made the summary a shared record that conflicts on each rebase.
        # A file that stops parsing is real rot, so this guard keeps that check.
        # `test_hook_rows_resolve_to_current_ast_symbols` catches symbol rot exactly.
        scanner = CatalogSourceScanner(_REPO_ROOT)  # Create the source scanner for this repository.
        catalog = PerformanceHookCatalog(_ARTIFACT_ROOT)  # Create the artifact reader for this spec.
        paths = sorted(row["file_path"] for row in catalog.inventory_rows())  # Read the snapshot set.
        symbol_index = scanner.symbol_index(paths)  # Parse each recorded file, which raises on bad syntax.
        scan_summary = catalog.scan_summary()  # Read the generated scan summary.
        assert scan_summary["eligible_file_count"] == len(paths)  # The summary must match its own table.
        assert scan_summary["parse_error_count"] == 0  # The snapshot claims every file parsed.
        assert set(symbol_index) == set(paths)  # Every recorded file still parses through AST today.

    def test_hook_rows_resolve_to_current_ast_symbols(self) -> None:
        scanner = CatalogSourceScanner(_REPO_ROOT)  # Create the source scanner for this repository.
        catalog = PerformanceHookCatalog(_ARTIFACT_ROOT)  # Create the artifact reader for this spec.
        paths = scanner.tracked_python_paths()  # Recreate the documented Git source set.
        symbol_index = scanner.symbol_index(paths)  # Parse source with AST for exact symbol checks.
        failures = []  # Collect all stale hook rows for one complete assertion.
        for row in catalog.hook_rows():  # Check each catalog hook row against the source tree.
            if not self._row_resolves(row, symbol_index):  # Detect a missing file or missing symbol.
                failures.append(f"{row['hook_id']} {row['file_path']} {row['symbol_or_class']}")  # Report the row.
        assert not failures, "\n".join(failures)  # Fail once with every stale hook row.

    def test_summary_artifacts_match_catalog_tables(self) -> None:
        catalog = PerformanceHookCatalog(_ARTIFACT_ROOT)  # Create the artifact reader for this spec.
        hook_rows = catalog.hook_rows()  # Read hook rows once for all count checks.
        inventory_rows = catalog.inventory_rows()  # Read inventory rows once for all count checks.
        summary = catalog.hook_summary()  # Read the summary that documents hook counts.
        strategies = catalog.strategy_rows()  # Read the strategy summary table.
        assert summary["inventory_file_rows"] == len(inventory_rows)  # Check the inventory row total.
        assert summary["hook_count"] == len(hook_rows)  # Check the hook row total.
        assert summary["files_with_hooks"] == len({row["file_path"] for row in hook_rows})  # Check files.
        assert summary["monitor_type_counts"] == self._count_by(hook_rows, "monitor_type")  # Check monitors.
        assert summary["disposition_counts"] == self._count_by(hook_rows, "disposition")  # Check dispositions.
        assert {row["strategy"]: int(row["hook_count"]) for row in strategies} == summary[
            "strategy_hook_counts"
        ]  # Check strategies.

    @staticmethod
    def _row_resolves(row: dict[str, str], symbol_index: dict[str, list[SymbolRecord]]) -> bool:
        symbols = symbol_index.get(row["file_path"], [])  # Read symbols for the catalog path, if present.
        names = {symbol.name for symbol in symbols}  # Build a local-name lookup for class rows.
        qualified_names = {symbol.qualified_name for symbol in symbols}  # Build a qualified-name lookup.
        symbol_name = row["symbol_or_class"]  # Read the symbol that the hook row names.
        return symbol_name in names or symbol_name in qualified_names  # Accept exact AST names only.

    @staticmethod
    def _count_by(rows: list[dict[str, str]], column: str) -> dict[str, int]:
        counts: dict[str, int] = {}  # Build a stable count map without an extra dependency.
        for row in rows:  # Count each row by the requested CSV column.
            counts[row[column]] = counts.get(row[column], 0) + 1  # Increment the matching bucket.
        return dict(sorted(counts.items()))  # Return a sorted map for deterministic JSON comparison.
