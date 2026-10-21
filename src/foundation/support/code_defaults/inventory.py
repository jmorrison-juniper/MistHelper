"""Discover empty Python defaults in tracked source and preserve stable identities."""

import ast
import logging
import shutil
import subprocess  # nosec B404 -- fixed Git argument vectors avoid shell evaluation.
from dataclasses import dataclass
from pathlib import Path

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Candidate:
    """Describe one empty-default expression without treating it as a defect."""

    identity: str
    path: str
    line: int
    column: int
    symbol: str
    shape: str
    input_key: str
    default_kind: str


@dataclass(frozen=True)
class Inventory:
    """Report tracked-file discovery, parse results, and ordered candidates."""

    revision: str
    discovered_files: int
    parsed_files: int
    parse_failures: tuple[str, ...]
    candidates: tuple[Candidate, ...]
    selected_paths: tuple[str, ...] = ()


class EmptyDefaultVisitor:
    """Visit one syntax tree and record only the five approved empty shapes."""

    def __init__(self, path: str) -> None:
        """Prepare identity state for one source file."""
        self.path = path
        self.scopes: list[str] = []
        self.candidates: list[Candidate] = []
        self.occurrences: dict[tuple[str, str, str], int] = {}

    def visit(self, node: ast.AST) -> None:
        """Visit a node, its empty defaults, and all child expressions."""
        scope_name = node.name if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) else ""
        if scope_name:
            self.scopes.append(scope_name)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            positional_arguments = node.args.posonlyargs + node.args.args
            defaults = list(zip(positional_arguments[-len(node.args.defaults) :], node.args.defaults, strict=False))
            defaults.extend(
                (argument, default)
                for argument, default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=False)
                if default is not None
            )
            for argument, default in defaults:
                self._emit(default, "parameter", argument.arg)
        if isinstance(node, ast.Call):
            self._call_shape(node)
        for child in ast.iter_child_nodes(node):
            self.visit(child)
        if scope_name:
            self.scopes.pop()

    def _call_shape(self, node: ast.Call) -> None:
        """Recognize empty mapping, environment, and attribute defaults."""
        function = ast.unparse(node.func)
        shape = ""
        default_index = 1
        if function in {"os.getenv", "os.environ.get"}:
            shape = "environment"
        elif function == "getattr":
            shape, default_index = "attribute", 2
        elif isinstance(node.func, ast.Attribute) and node.func.attr in {"get", "pop"}:
            shape = f"mapping_{node.func.attr}"
        if shape and len(node.args) > default_index:
            key_index = 1 if shape == "attribute" else 0
            input_key = self._literal_key(node.args[key_index])
            self._emit(node.args[default_index], shape, input_key)

    def _emit(self, default: ast.expr, shape: str, input_key: str) -> None:
        """Add one candidate with an identity that does not use line position."""
        kind = self._empty_kind(default)
        if not kind:
            return
        symbol = ".".join(self.scopes) or "<module>"
        key = (symbol, shape, input_key)
        occurrence = self.occurrences.get(key, 0)
        self.occurrences[key] = occurrence + 1
        identity = f"{self.path}|{symbol}|{shape}|{input_key}|{occurrence}"
        self.candidates.append(
            Candidate(identity, self.path, default.lineno, default.col_offset, symbol, shape, input_key, kind)
        )

    @staticmethod
    def _literal_key(node: ast.AST) -> str:
        """Return a literal input name or a stable marker for a dynamic name."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return "<dynamic>"

    @staticmethod
    def _empty_kind(node: ast.expr) -> str:
        """Return the empty literal type or an empty string for other defaults."""
        if isinstance(node, ast.Constant) and node.value == "":
            return "empty_string"
        if isinstance(node, (ast.List, ast.Tuple)) and not node.elts:
            return f"empty_{type(node).__name__.lower()}"
        if isinstance(node, ast.Dict) and not node.keys:
            return f"empty_{type(node).__name__.lower()}"
        if isinstance(node, ast.Call) and ast.unparse(node.func) == "set" and not node.args:
            return "empty_set"
        return ""


class TrackedSource:
    """Read tracked Python source from a verified Git worktree."""

    def __init__(self, root: Path) -> None:
        """Require an existing worktree root."""
        self.root = root.resolve()
        if not self.root.is_dir():
            raise ValueError(f"root is not a Git worktree: {root}")
        try:
            top_level = self._git("rev-parse", "--show-toplevel")
        except subprocess.CalledProcessError as error:
            raise ValueError(f"root is not a Git worktree: {root}") from error
        if top_level != str(self.root):
            raise ValueError(f"root is not a Git worktree: {root}")

    def paths(self) -> tuple[str, ...]:
        """Return sorted tracked Python files outside test and generated paths."""
        output = self._git("ls-files", "-z", "--", "*.py")
        paths = (path for path in output.split("\0") if path and self._eligible(path))
        return tuple(sorted(paths))

    def revision(self) -> str:
        """Return the current local commit used to identify the scan."""
        return self._git("rev-parse", "HEAD")

    def read(self, relative_path: str) -> str:
        """Read one tracked file as UTF-8 text."""
        return (self.root / relative_path).read_text(encoding="utf-8")

    def _git(self, *arguments: str) -> str:
        """Run Git with an argument list and return its text output."""
        executable = shutil.which("git")
        if executable is None:
            raise ValueError("Git executable is unavailable.")
        command = [executable, "-C", str(self.root), *arguments]
        _LOGGER.info("Running Git %s", arguments[0])
        try:
            result = subprocess.run(  # nosec B603 -- fixed Git argv runs without a shell.
                command,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as error:
            _LOGGER.error("Git %s failed with status %s", arguments[0], error.returncode)
            raise ValueError(f"Git command failed: {arguments[0]}") from error
        _LOGGER.debug("Git %s completed", arguments[0])
        return result.stdout.strip("\n")

    @staticmethod
    def _eligible(path: str) -> bool:
        """Exclude tests, environments, caches, and non-source Python files."""
        parts = Path(path).parts
        excluded = {"tests", "test", ".venv", "venv", "__pycache__", ".tox", ".nox", "build", "dist"}
        name = Path(path).name
        test_path = any(part.startswith("test_") or part.endswith("_tests") for part in parts)
        test_file = name.startswith("test_") or name.endswith("_test.py")
        return Path(path).suffix == ".py" and not excluded.intersection(parts) and not test_path and not test_file


class InventoryScanner:
    """Scan tracked Python source once and return deterministic candidates."""

    def __init__(self, root: Path) -> None:
        """Bind the scanner to one repository worktree."""
        self.source = TrackedSource(root)

    def scan(self, selected_paths: tuple[str, ...] | None = None) -> Inventory:
        """Parse selected tracked files and report missing or invalid inputs."""
        tracked = self.source.paths()
        requested = tracked if selected_paths is None else tuple(sorted(set(selected_paths)))
        failures = [f"missing tracked scope file: {path}" for path in requested if path not in tracked]
        selected = tuple(path for path in requested if path in tracked)
        candidates, parsed, parse_failures = self._parse_files(selected)
        failures.extend(parse_failures)
        return Inventory(
            self.source.revision(),
            len(tracked),
            parsed,
            tuple(sorted(failures)),
            tuple(sorted(candidates, key=lambda candidate: (candidate.path, candidate.identity))),
            selected,
        )

    def _parse_files(self, paths: tuple[str, ...]) -> tuple[list[Candidate], int, list[str]]:
        """Read and parse each selected path once."""
        candidates: list[Candidate] = []
        failures: list[str] = []
        parsed = 0
        for path in paths:
            try:
                tree = ast.parse(self.source.read(path), filename=path)
            except (OSError, UnicodeError, SyntaxError) as error:
                failures.append(f"{path}: {type(error).__name__}: {error}")
                continue
            visitor = EmptyDefaultVisitor(path)
            visitor.visit(tree)
            candidates.extend(visitor.candidates)
            parsed += 1
        return candidates, parsed, failures
