"""Guard source packages against imports of the root CLI module."""

from __future__ import annotations  # Keep annotations stable during pytest collection.

import ast  # Parse Python source so comments do not create false failures.
import logging  # Record scan counts for guard proof audits.
from pathlib import Path  # Resolve repository files without hardcoded separators.

_LOGGER = logging.getLogger(__name__)  # Share one logger for guard diagnostics.
_REPO_ROOT = Path(__file__).resolve().parents[2]  # Locate the repository root from this guard file.
_SRC_ROOT = _REPO_ROOT / "src"  # Limit the guard to source packages owned by issue #1703.


class SourceBackReferenceScanner:
    """Find executable source imports that reach back to the root CLI module."""

    @classmethod
    def python_files(cls, root: Path) -> tuple[Path, ...]:
        """Return sorted Python files below the scan root."""
        logging.info("Scanning source files under %s", root)  # Log before reading the filesystem.
        files = tuple(sorted(root.rglob("*.py")))  # Materialize the scan set so zero files cannot pass silently.
        logging.debug("The source back-reference guard found %d file(s)", len(files))  # Record the measured count.
        return files  # Return the exact files used by the guard.

    @classmethod
    def scan_files(cls, files: tuple[Path, ...]) -> tuple[int, tuple[str, ...]]:
        """Return the scanned file count and every executable back-reference."""
        logging.info("Checking %d source file(s) for root imports", len(files))  # Log the proof count.
        failures: list[str] = []  # Collect all failures so one run gives the complete repair list.
        for source_file in files:  # Parse each Python file in the measured set.
            source = source_file.read_text(encoding="utf-8")  # Read source text with the project encoding.
            failures.extend(cls._scan_text(source_file, source))  # Add executable back-reference findings.
        logging.debug("The source back-reference guard found %d issue(s)", len(failures))  # Log the result count.
        return len(files), tuple(failures)  # Return both the proof count and the full finding list.

    @staticmethod
    def _scan_text(source_file: Path, source: str) -> tuple[str, ...]:
        """Return executable back-references from one source string."""
        logging.info("Parsing source file %s for root imports", source_file)  # Log before parsing one file.
        tree = ast.parse(source, filename=str(source_file))  # Parse Python so string mentions do not fail.
        failures: list[str] = []  # Store every executable import in this file.
        for node in ast.walk(tree):  # Walk all nodes because imports can live inside functions.
            if SourceBackReferenceScanner._imports_root_module(node):  # Detect a direct root import statement.
                failures.append(f"{source_file}:{node.lineno}: import MistHelper")  # Report the exact line.
            if SourceBackReferenceScanner._imports_root_with_importlib(node):  # Detect a lazy root import call.
                failures.append(f"{source_file}:{node.lineno}: importlib root import")  # Report the exact line.
        logging.debug("Parsed %s and found %d issue(s)", source_file, len(failures))  # Log the per-file result.
        return tuple(failures)  # Return immutable findings for stable assertions.

    @staticmethod
    def _imports_root_module(node: ast.AST) -> bool:
        """Return true when a node imports the root CLI module."""
        if not isinstance(node, ast.Import):  # Only import statements can match this direct form.
            return False  # Ignore all other nodes.
        return any(alias.name == "MistHelper" for alias in node.names)  # Match executable root imports only.

    @staticmethod
    def _imports_root_with_importlib(node: ast.AST) -> bool:
        """Return true when a node lazily imports the root CLI module."""
        if not isinstance(node, ast.Call):  # Only call expressions can invoke importlib.
            return False  # Ignore non-call nodes.
        if not SourceBackReferenceScanner._calls_import_module(node):  # Require importlib.import_module.
            return False  # Ignore unrelated function calls.
        return bool(node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == "MistHelper")

    @staticmethod
    def _calls_import_module(node: ast.Call) -> bool:
        """Return true when the call target is importlib.import_module."""
        function = node.func  # Read the callable expression once for clear branch checks.
        return isinstance(function, ast.Attribute) and function.attr == "import_module"  # Match the API call.


class TestSourceMistHelperBackReferences:
    """Verify source packages do not import the root CLI module."""

    def test_src_packages_do_not_import_the_root_module(self) -> None:
        """The source tree must contain no executable root-module imports."""
        files = SourceBackReferenceScanner.python_files(_SRC_ROOT)  # Build the measured source file set.
        scanned_count, failures = SourceBackReferenceScanner.scan_files(files)  # Run the executable import scan.
        assert scanned_count > 0, "source back-reference guard scanned 0 files"  # Prove the guard measured input.
        assert not failures, f"scanned {scanned_count} files\n" + "\n".join(failures)  # Report all failures.

    def test_scanner_rejects_a_deliberate_root_import(self) -> None:
        """The scanner must fail a direct import and a lazy import."""
        source = "import importlib\nimport MistHelper\nmh = importlib.import_module('MistHelper')\n"  # Bad sample.
        findings = SourceBackReferenceScanner._scan_text(Path("src") / "bad.py", source)  # Scan without temp files.
        assert len(findings) == 2, f"negative test found {len(findings)} issue(s)"  # Prove both defects fail.

    def test_scanner_reports_zero_scanned_files(self) -> None:
        """The scanner must expose a zero-file scan to the guard assertion."""
        scanned_count, failures = SourceBackReferenceScanner.scan_files(())  # Exercise the zero-input path.
        assert scanned_count == 0, "zero-input proof did not report zero scanned files"  # Prove the count is exact.
        assert not failures, "zero-input proof must not invent failures"  # Keep zero-input behavior deterministic.
