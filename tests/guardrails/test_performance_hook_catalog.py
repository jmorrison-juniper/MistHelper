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

import pytest
import yaml

from tests.support.git_environment import (
    git_subprocess_environment,  # WHY: issue #3022, repair a partial editor git config set.
)

_LOGGER = logging.getLogger(__name__)  # Share one logger for this guard module.
_REPO_ROOT = Path(__file__).resolve().parents[2]  # Locate the repository root from tests/guardrails.
_ARTIFACT_ROOT = _REPO_ROOT / "specs" / "2448-misthelper-performance-monitoring" / "artifacts"  # Locate artifacts.
_INVENTORY_SOURCE_REVISION = "7c4e57f3db93afda4c93ef0aec1e73c35fb7774e"  # Pin the historical inventory source.


def missing_catalog_paths(catalog_paths: set[str], source_paths: set[str]) -> list[str]:
    """Return catalog paths that do not exist in the selected source tree."""
    return sorted(catalog_paths - source_paths)  # Keep failure output stable.


def row_resolves(row: dict[str, str], symbol_index: dict[str, list[SymbolRecord]]) -> bool:
    """Return True when one hook row names a live AST symbol.

    Why:
        A moved file keeps its symbols, and a lost symbol must still fail the guard.
    """
    symbols = symbol_index.get(row["file_path"], [])  # Read symbols at the active catalog path.
    names = {symbol.name for symbol in symbols}  # Build a local-name lookup for class rows.
    qualified_names = {symbol.qualified_name for symbol in symbols}  # Build a qualified-name lookup.
    symbol_name = row["symbol_or_class"]  # Read the symbol that the hook row names.
    return symbol_name in names or symbol_name in qualified_names  # Accept exact AST names only.


def unresolved_hook_rows(hook_rows: list[dict[str, str]], symbol_index: dict[str, list[SymbolRecord]]) -> list[str]:
    """Return active hook rows that do not resolve to a current AST symbol."""
    return [
        f"{row['hook_id']} {row['file_path']} {row['symbol_or_class']}"
        for row in hook_rows
        if not row_resolves(row, symbol_index)
    ]  # Report each unresolved row with its evidence.


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

    def tracked_python_paths_at_revision(self, revision: str) -> list[str]:
        """Return tracked Python paths from one historical Git tree."""
        _LOGGER.info("Reading tracked Python files at source revision %s", revision)  # Log the source query.
        result = subprocess.run(  # Read the historical tree without checking out or changing files.
            ["git", "ls-tree", "-r", "--name-only", "-z", revision],
            cwd=self.repo_root,
            check=True,
            capture_output=True,
            text=True,
            env=git_subprocess_environment(),  # WHY: issue #3022, a partial editor git config set makes git stop.
        )
        paths = [path for path in result.stdout.split("\0") if path.endswith(".py")]  # Select Python paths.
        _LOGGER.debug("Git returned %s historical Python paths", len(paths))  # Log the historical set size.
        return sorted(paths)  # Return a stable order for artifact comparisons.

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

    def test_inventory_paths_exist_at_the_recorded_source_revision(self) -> None:
        # WHY: the inventory is historical evidence and must not follow moves after its source revision.
        scanner = CatalogSourceScanner(_REPO_ROOT)  # Create the source scanner for this repository.
        catalog = PerformanceHookCatalog(_ARTIFACT_ROOT)  # Create the artifact reader for this spec.
        inventory_rows = catalog.inventory_rows()  # Read the historical inventory rows.
        inventory_paths = {row["file_path"] for row in inventory_rows}  # Use paths as inventory keys.
        source_paths = set(scanner.tracked_python_paths_at_revision(_INVENTORY_SOURCE_REVISION))
        missing = missing_catalog_paths(inventory_paths, source_paths)  # Find paths absent from that source.
        scan_summary = catalog.scan_summary()  # Read the generated scan summary.
        print(f"Checked {len(inventory_rows)} inventory rows at source revision {_INVENTORY_SOURCE_REVISION}.")
        assert len(inventory_paths) == len(inventory_rows), "Inventory paths must be unique"
        assert scan_summary["eligible_file_count"] == len(inventory_rows), "Inventory row count drifted"
        assert scan_summary["parse_error_count"] == 0, "The recorded scan has parse errors"
        assert not missing, "Missing paths at the recorded source revision:\n" + "\n".join(missing)

    def test_hook_rows_resolve_to_current_ast_symbols(self) -> None:
        scanner = CatalogSourceScanner(_REPO_ROOT)  # Create the source scanner for this repository.
        catalog = PerformanceHookCatalog(_ARTIFACT_ROOT)  # Create the artifact reader for this spec.
        paths = scanner.tracked_python_paths()  # Recreate the documented Git source set.
        symbol_index = scanner.symbol_index(paths)  # Parse source with AST for exact symbol checks.
        hook_rows = catalog.hook_rows()  # Read the active hook rows.
        failures = unresolved_hook_rows(hook_rows, symbol_index)  # Find missing files or symbols.
        print(f"Checked {len(hook_rows)} active hook rows against the current source tree.")
        assert not failures, f"Checked {len(hook_rows)} active hook rows. Unresolved rows:\n" + "\n".join(failures)

    def test_summary_artifacts_match_catalog_tables(self) -> None:
        catalog = PerformanceHookCatalog(_ARTIFACT_ROOT)  # Create the artifact reader for this spec.
        hook_rows = catalog.hook_rows()  # Read hook rows once for all count checks.
        inventory_rows = catalog.inventory_rows()  # Read inventory rows once for all count checks.
        summary = catalog.hook_summary()  # Read the summary that documents hook counts.
        scan_summary = catalog.scan_summary()  # Read the summary that documents inventory counts.
        strategies = catalog.strategy_rows()  # Read the strategy summary table.
        assert summary["inventory_file_rows"] == len(inventory_rows)  # Check the inventory row total.
        assert scan_summary["eligible_file_count"] == len(inventory_rows)  # Check the inventory source count.
        assert summary["hook_count"] == len(hook_rows)  # Check the hook row total.
        assert summary["files_with_hooks"] == len({row["file_path"] for row in hook_rows})  # Check files.
        assert summary["monitor_type_counts"] == self._count_by(hook_rows, "monitor_type")  # Check monitors.
        assert summary["disposition_counts"] == self._count_by(hook_rows, "disposition")  # Check dispositions.
        assert {row["strategy"]: int(row["hook_count"]) for row in strategies} == summary[
            "strategy_hook_counts"
        ]  # Check strategies.
        print(f"Checked {len(hook_rows)} hook rows and {len(inventory_rows)} inventory rows against summaries.")

    @staticmethod
    def _count_by(rows: list[dict[str, str]], column: str) -> dict[str, int]:
        counts: dict[str, int] = {}  # Build a stable count map without an extra dependency.
        for row in rows:  # Count each row by the requested CSV column.
            counts[row[column]] = counts.get(row[column], 0) + 1  # Increment the matching bucket.
        return dict(sorted(counts.items()))  # Return a sorted map for deterministic JSON comparison.


class TestCatalogContractFailures:
    """Prove that both catalog contracts reject stale evidence."""

    def test_inventory_path_absent_from_source_revision_is_reported(self) -> None:
        missing = missing_catalog_paths({"src/removed.py"}, {"src/current.py"})
        print("Checked 1 synthetic inventory path against 1 source path.")
        assert missing == ["src/removed.py"]

    def test_hook_path_or_symbol_absent_from_current_tree_is_reported(self) -> None:
        hook_rows = [
            {
                "hook_id": "hook-test",
                "file_path": "src/removed.py",
                "symbol_or_class": "RemovedSymbol",
            }
        ]
        failures = unresolved_hook_rows(hook_rows, {})
        print("Checked 1 synthetic active hook row against 0 indexed symbols.")
        assert failures == ["hook-test src/removed.py RemovedSymbol"]

    def test_inventory_source_revision_is_documented(self) -> None:
        quickstart_path = _REPO_ROOT / "specs" / "2448-misthelper-performance-monitoring" / "quickstart.md"
        quickstart = quickstart_path.read_text(encoding="utf-8")
        assert f"`{_INVENTORY_SOURCE_REVISION}`" in quickstart

    def test_spec_inventory_counts_match_scan_summary(self) -> None:
        catalog = PerformanceHookCatalog(_ARTIFACT_ROOT)
        summary = catalog.scan_summary()
        specification = (_REPO_ROOT / "specs" / "2448-misthelper-performance-monitoring" / "spec.md").read_text(
            encoding="utf-8"
        )
        expected_counts = (
            f"The final inventory contains {int(summary['eligible_file_count']):,} Python files and "
            f"{int(summary['symbol_count']):,} symbols.",
            f"The symbols include {int(summary['function_count']):,} functions, "
            f"{int(summary['async_function_count']):,} asynchronous functions, and "
            f"{int(summary['class_count']):,} classes.",
            f"The inventory identifies {int(summary['nested_symbol_count']):,} nested symbols and no parse errors.",
        )
        print(f"Checked {len(expected_counts)} specification counts against the scan summary.")
        for expected_count in expected_counts:
            assert expected_count in specification


class TestCatalogWorkflowRevision:
    """Require CI to fetch the historical tree before the catalog guard runs."""

    @staticmethod
    def _revision_fetch_is_valid(steps: list[dict[str, object]]) -> bool:
        """Check the exact revision, shard scope, and execution order."""
        fetch_command = f"git fetch --no-tags --depth=1 origin {_INVENTORY_SOURCE_REVISION}"
        test_index = next(index for index, step in enumerate(steps) if step.get("name") == "Run tests with coverage")
        return any(
            step.get("run") == fetch_command and step.get("if") == "${{ matrix.shard == 'root-and-contracts' }}"
            for step in steps[:test_index]
        )

    def test_coverage_shard_fetches_the_recorded_revision(self) -> None:
        """Protect the pinned Git tree in a clean shallow CI checkout."""
        workflow = yaml.safe_load((_REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
        steps = workflow["jobs"]["pytest_coverage_shards"]["steps"]
        print(f"Checked {len(steps)} coverage workflow steps for the inventory revision fetch.")
        assert self._revision_fetch_is_valid(steps), "Fetch the exact inventory revision before the coverage tests"

    @pytest.mark.parametrize("defect", ["missing", "wrong-revision", "wrong-shard", "late-fetch"])
    def test_revision_fetch_guard_rejects_invalid_workflow_steps(self, defect: str) -> None:
        """Prove that missing, incorrect, or late fetches fail the workflow contract."""
        fetch_step = {
            "run": f"git fetch --no-tags --depth=1 origin {_INVENTORY_SOURCE_REVISION}",
            "if": "${{ matrix.shard == 'root-and-contracts' }}",
        }
        steps = [fetch_step, {"name": "Run tests with coverage"}]
        if defect == "missing":
            steps.pop(0)
        elif defect == "wrong-revision":
            fetch_step["run"] = "git fetch --no-tags --depth=1 origin HEAD"
        elif defect == "wrong-shard":
            fetch_step["if"] = "${{ matrix.shard == 'root-units' }}"
        else:
            steps.reverse()
        print(f"Checked {len(steps)} synthetic workflow steps with defect {defect}.")
        assert not self._revision_fetch_is_valid(steps)
