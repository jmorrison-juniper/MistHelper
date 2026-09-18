"""Guard source packages against imports of the root CLI module."""

from __future__ import annotations  # Keep annotations stable during pytest collection.

import ast  # Parse Python source so comments do not create false failures.
import logging  # Record scan counts for guard proof audits.
from pathlib import Path  # Resolve repository files without hardcoded separators.

logger = logging.getLogger(__name__)  # Share one module logger for guard diagnostics.
_REPO_ROOT = Path(__file__).resolve().parents[2]  # Locate the repository root from this guard file.
_SRC_ROOT = _REPO_ROOT / "src"  # Limit the guard to source packages owned by issue #1703.


class SourceBackReferenceScanner:
    """Find executable source imports that reach back to the root CLI module."""

    @classmethod
    def python_files(cls, root: Path) -> tuple[Path, ...]:
        """Return sorted Python files below the scan root."""
        logger.info("Scanning source files under %s", root)  # Log before reading the filesystem.
        files = tuple(sorted(root.rglob("*.py")))  # Materialize the scan set so zero files cannot pass silently.
        logger.debug("The source back-reference guard found %d file(s)", len(files))  # Record the measured count.
        return files  # Return the exact files used by the guard.

    @classmethod
    def scan_files(cls, files: tuple[Path, ...]) -> tuple[int, tuple[str, ...]]:
        """Return the scanned file count and every executable back-reference."""
        logger.info("Checking %d source file(s) for root imports", len(files))  # Log the proof count.
        failures: list[str] = []  # Collect all failures so one run gives the complete repair list.
        for source_file in files:  # Parse each Python file in the measured set.
            source = source_file.read_text(encoding="utf-8")  # Read source text with the project encoding.
            failures.extend(cls._scan_text(source_file, source))  # Add executable back-reference findings.
        logger.debug("The source back-reference guard found %d issue(s)", len(failures))  # Log the result count.
        return len(files), tuple(failures)  # Return both the proof count and the full finding list.

    @staticmethod
    def _scan_text(source_file: Path, source: str) -> tuple[str, ...]:
        """Return executable back-references from one source string."""
        logger.info("Parsing source file %s for root imports", source_file)  # Log before parsing one file.
        tree = ast.parse(source, filename=str(source_file))  # Parse Python so string mentions do not fail.
        root_names = SourceBackReferenceScanner._root_name_constants(tree)  # Track aliases that hide the root name.
        failures: list[str] = []  # Store every executable import in this file.
        for node in ast.walk(tree):  # Walk all nodes because imports can live inside functions.
            if SourceBackReferenceScanner._imports_root_module(node):  # Detect a direct root import statement.
                failures.append(f"{source_file}:{node.lineno}: import MistHelper")  # Report the exact line.
            if SourceBackReferenceScanner._imports_root_with_importlib(node, root_names):  # Detect a lazy root import.
                failures.append(f"{source_file}:{node.lineno}: importlib root import")  # Report the exact line.
            if SourceBackReferenceScanner._reads_root_from_sys_modules(node, root_names):  # Detect module-table reads.
                failures.append(f"{source_file}:{node.lineno}: sys.modules root lookup")  # Report the exact line.
        logger.debug("Parsed %s and found %d issue(s)", source_file, len(failures))  # Log the per-file result.
        return tuple(failures)  # Return immutable findings for stable assertions.

    @staticmethod
    def _root_name_constants(tree: ast.AST) -> frozenset[str]:
        """Return names that hold the root CLI module string."""
        logger.info("Collecting root-name constants from the source tree")  # Log before scanning assignments.
        names: set[str] = set()  # Store local names that can hide a root import target.
        for node in ast.walk(tree):  # Walk every assignment because constants can live in helper scopes.
            if isinstance(node, ast.Assign) and SourceBackReferenceScanner._is_root_string(node.value):
                names.update(target.id for target in node.targets if isinstance(target, ast.Name))  # Keep name targets.
            if isinstance(node, ast.AnnAssign) and SourceBackReferenceScanner._is_root_string(node.value):
                if isinstance(node.target, ast.Name):  # Annotated assignments have one target only.
                    names.add(node.target.id)  # Keep the annotated name for later call checks.
        logger.debug("Collected %d root-name constant(s)", len(names))  # Log the number of hidden names.
        return frozenset(names)  # Return an immutable set so scan logic cannot mutate it.

    @staticmethod
    def _imports_root_module(node: ast.AST) -> bool:
        """Return true when a node imports the root CLI module."""
        if not isinstance(node, ast.Import):  # Only import statements can match this direct form.
            return False  # Ignore all other nodes.
        return any(alias.name == "MistHelper" for alias in node.names)  # Match executable root imports only.

    @staticmethod
    def _imports_root_with_importlib(node: ast.AST, root_names: frozenset[str]) -> bool:
        """Return true when a node lazily imports the root CLI module."""
        if not isinstance(node, ast.Call):  # Only call expressions can invoke importlib.
            return False  # Ignore non-call nodes.
        if not SourceBackReferenceScanner._calls_import_module(node):  # Require importlib.import_module.
            return False  # Ignore unrelated function calls.
        return bool(node.args and SourceBackReferenceScanner._refers_to_root_name(node.args[0], root_names))

    @staticmethod
    def _calls_import_module(node: ast.Call) -> bool:
        """Return true when the call target is importlib.import_module."""
        function = node.func  # Read the callable expression once for clear branch checks.
        return isinstance(function, ast.Attribute) and function.attr == "import_module"  # Match the API call.

    @staticmethod
    def _reads_root_from_sys_modules(node: ast.AST, root_names: frozenset[str]) -> bool:
        """Return true when code reads the root CLI module from sys.modules."""
        if isinstance(node, ast.Subscript) and SourceBackReferenceScanner._is_sys_modules(node.value):
            return SourceBackReferenceScanner._refers_to_root_name(node.slice, root_names)  # Match sys.modules[name].
        if isinstance(node, ast.Call) and SourceBackReferenceScanner._calls_sys_modules_get(node):
            return bool(node.args and SourceBackReferenceScanner._refers_to_root_name(node.args[0], root_names))
        return False  # Ignore all other nodes.

    @staticmethod
    def _calls_sys_modules_get(node: ast.Call) -> bool:
        """Return true when the call target is sys.modules.get."""
        function = node.func  # Read the callable expression once for clear checks.
        return (
            isinstance(function, ast.Attribute)
            and function.attr == "get"
            and SourceBackReferenceScanner._is_sys_modules(function.value)
        )

    @staticmethod
    def _is_sys_modules(node: ast.AST) -> bool:
        """Return true when the node reads a modules table on a sys alias."""
        return isinstance(node, ast.Attribute) and node.attr == "modules"  # Match sys.modules and local sys aliases.

    @staticmethod
    def _refers_to_root_name(node: ast.AST, root_names: frozenset[str]) -> bool:
        """Return true when an expression points to the root CLI module name."""
        if SourceBackReferenceScanner._is_root_string(node):  # A literal string names the root module directly.
            return True  # Report direct string references.
        return isinstance(node, ast.Name) and node.id in root_names  # Report constant aliases for the same string.

    @staticmethod
    def _is_root_string(node: ast.AST | None) -> bool:
        """Return true when a node is the root CLI module string."""
        return isinstance(node, ast.Constant) and node.value == "MistHelper"  # Match the exact root module name.


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
        source = (  # Build one bad sample with literal, constant, and module-table back-references.
            "import importlib\n"
            "import sys\n"
            "_MIST_MODULE = 'MistHelper'\n"
            "import MistHelper\n"
            "mh = importlib.import_module(_MIST_MODULE)\n"
            "mh2 = sys.modules.get(_MIST_MODULE)\n"
        )
        findings = SourceBackReferenceScanner._scan_text(Path("src") / "bad.py", source)  # Scan without temp files.
        assert len(findings) == 3, f"negative test found {len(findings)} issue(s)"  # Prove all defects fail.

    def test_scanner_reports_zero_scanned_files(self) -> None:
        """The scanner must expose a zero-file scan to the guard assertion."""
        scanned_count, failures = SourceBackReferenceScanner.scan_files(())  # Exercise the zero-input path.
        assert scanned_count == 0, "zero-input proof did not report zero scanned files"  # Prove the count is exact.
        assert not failures, "zero-input proof must not invent failures"  # Keep zero-input behavior deterministic.
