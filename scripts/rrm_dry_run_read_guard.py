"""Keep every product RRM_DRY_RUN read inside the adopted policy resolver."""

from __future__ import annotations  # WHY: keep type annotations lightweight.

import ast  # WHY: syntax analysis distinguishes environment reads from documentation text.
import subprocess  # nosec B404  # WHY: git supplies the authoritative tracked file list without a shell.
import sys  # WHY: the guard returns a nonzero process status on a policy violation.
from dataclasses import dataclass  # WHY: one result object carries counts and violations.
from pathlib import Path  # WHY: repository paths must work on each supported platform.

ENVIRONMENT_NAME = "RRM_DRY_RUN"  # WHY: the guard protects this single destructive-safety control.
ALLOWED_PATH = Path("src/mist/resources/site/rrm_reset/dry_run_policy.py")  # WHY: one resolver owns all reads.


@dataclass(frozen=True)
class GuardResult:
    """Hold the scanned file count and each literal environment read site."""

    file_count: int
    read_sites: tuple[tuple[Path, int], ...]

    @property
    def unauthorized_sites(self) -> tuple[tuple[Path, int], ...]:
        """Return read sites that bypass the single policy resolver."""
        return tuple(site for site in self.read_sites if site[0] != ALLOWED_PATH)


class RrmDryRunReadGuard:
    """Find and validate literal RRM_DRY_RUN environment reads."""

    @staticmethod
    def tracked_python_files(root: Path) -> tuple[Path, ...]:
        """Return tracked non-test Python paths from Git."""
        command = ["git", "-C", str(root), "ls-files", "--", "*.py"]  # WHY: Git defines the tracked source set.
        completed = subprocess.run(command, check=True, capture_output=True, text=True)  # nosec B603
        paths = (Path(line) for line in completed.stdout.splitlines() if line)  # WHY: ignore blank output lines.
        return tuple(path for path in paths if not RrmDryRunReadGuard._is_test_path(path))

    @staticmethod
    def _is_test_path(path: Path) -> bool:
        """Return True when a path belongs to test code."""
        lowered_parts = {part.lower() for part in path.parts}  # WHY: Windows paths are case-insensitive.
        return "tests" in lowered_parts or path.name.lower().startswith("test_")

    @staticmethod
    def scan_paths(root: Path, paths: tuple[Path, ...]) -> GuardResult:
        """Parse paths and return each literal environment read."""
        sites: list[tuple[Path, int]] = []  # WHY: the validator reports every bypass location.
        for path in paths:  # WHY: each tracked product module can contain a bypass.
            source = (root / path).read_text(encoding="utf-8")  # WHY: AST needs the exact tracked source text.
            tree = ast.parse(source, filename=str(path))  # WHY: parse failures must fail the guard.
            names = RrmDryRunReadGuard._string_constants(tree)  # WHY: the resolver uses a named literal constant.
            sites.extend((path, line) for line in RrmDryRunReadGuard._read_lines(tree, names))
        return GuardResult(len(paths), tuple(sites))

    @staticmethod
    def _string_constants(tree: ast.AST) -> dict[str, str]:
        """Return module names that bind directly to string literals."""
        constants: dict[str, str] = {}  # WHY: resolve literal names without evaluating code.
        for node in getattr(tree, "body", []):  # WHY: only direct module constants are policy identifiers.
            if (
                isinstance(node, ast.Assign)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                for target in node.targets:  # WHY: one assignment can bind more than one direct name.
                    if isinstance(target, ast.Name):
                        constants[target.id] = node.value.value
        return constants

    @staticmethod
    def _read_lines(tree: ast.AST, names: dict[str, str]) -> tuple[int, ...]:
        """Return lines that read the protected environment value."""
        lines: list[int] = []  # WHY: line numbers make a bypass actionable.
        bindings = RrmDryRunReadGuard._os_bindings(tree)  # WHY: aliases are equivalent environment read paths.
        for node in ast.walk(tree):  # WHY: environment reads can occur in any function or class.
            if isinstance(node, ast.Call) and RrmDryRunReadGuard._is_read_call(node, names, bindings):
                lines.append(node.lineno)
            if isinstance(node, ast.Subscript) and RrmDryRunReadGuard._is_environ(node.value, bindings):
                if RrmDryRunReadGuard._literal_value(node.slice, names) == ENVIRONMENT_NAME:
                    lines.append(node.lineno)
        return tuple(lines)

    @staticmethod
    def _os_bindings(tree: ast.AST) -> tuple[set[str], set[str], set[str]]:
        """Return local names for os modules, environ mappings, and getenv calls."""
        os_names, environ_names, getenv_names = {"os"}, {"environ"}, {"getenv"}
        for node in getattr(tree, "body", []):  # WHY: module imports define the equivalent read spellings.
            if isinstance(node, ast.Import):
                RrmDryRunReadGuard._record_os_import(node, os_names)
            if isinstance(node, ast.ImportFrom) and node.module == "os":
                RrmDryRunReadGuard._record_os_from_import(node, environ_names, getenv_names)
        return os_names, environ_names, getenv_names

    @staticmethod
    def _record_os_import(node: ast.Import, os_names: set[str]) -> None:
        """Record each local name that refers to the os module."""
        for alias in node.names:  # WHY: one import statement can bind several modules.
            if alias.name == "os":
                os_names.add(alias.asname or alias.name)

    @staticmethod
    def _record_os_from_import(
        node: ast.ImportFrom,
        environ_names: set[str],
        getenv_names: set[str],
    ) -> None:
        """Record local names for imported environment readers."""
        for alias in node.names:  # WHY: aliases must not bypass the literal read guard.
            if alias.name == "environ":
                environ_names.add(alias.asname or alias.name)
            if alias.name == "getenv":
                getenv_names.add(alias.asname or alias.name)

    @staticmethod
    def _is_read_call(
        node: ast.Call,
        names: dict[str, str],
        bindings: tuple[set[str], set[str], set[str]],
    ) -> bool:
        """Return True for os.getenv or environment mapping get calls."""
        if not node.args or RrmDryRunReadGuard._literal_value(node.args[0], names) != ENVIRONMENT_NAME:
            return False
        os_names, _environ_names, getenv_names = bindings  # WHY: use the local import names for this module.
        function = node.func  # WHY: the function shape distinguishes environment reads from other calls.
        if isinstance(function, ast.Name):
            return function.id in getenv_names
        if not isinstance(function, ast.Attribute):
            return False
        is_os_getenv = function.attr == "getenv" and isinstance(function.value, ast.Name)
        if is_os_getenv and function.value.id in os_names:
            return True
        return function.attr == "get" and RrmDryRunReadGuard._is_environ(function.value, bindings)

    @staticmethod
    def _is_environ(node: ast.AST, bindings: tuple[set[str], set[str], set[str]]) -> bool:
        """Return True for os.environ or a directly imported environ name."""
        os_names, environ_names, _getenv_names = bindings  # WHY: match each supported import form.
        if isinstance(node, ast.Name):
            return node.id in environ_names
        return (
            isinstance(node, ast.Attribute)
            and node.attr == "environ"
            and isinstance(node.value, ast.Name)
            and node.value.id in os_names
        )

    @staticmethod
    def _literal_value(node: ast.AST, names: dict[str, str]) -> str | None:
        """Return a direct or named string literal without executing the module."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            return names.get(node.id)
        return None

    @staticmethod
    def validate(result: GuardResult) -> tuple[str, ...]:
        """Return each guard failure message."""
        failures: list[str] = []  # WHY: one run must report every policy defect.
        if result.file_count == 0:
            failures.append("No tracked non-test Python files were scanned.")
        if not result.read_sites:
            failures.append("No RRM_DRY_RUN read site was found.")
        for path, line in result.unauthorized_sites:
            failures.append(f"Unauthorized RRM_DRY_RUN read at {path.as_posix()}:{line}.")
        return tuple(failures)


def main() -> int:
    """Scan the repository and return the policy decision as a process status."""
    root = Path(__file__).resolve().parents[1]  # WHY: the script can run from any working directory.
    paths = RrmDryRunReadGuard.tracked_python_files(root)  # WHY: use the authoritative tracked source set.
    result = RrmDryRunReadGuard.scan_paths(root, paths)  # WHY: count and locate each protected read.
    print(
        f"Scanned {result.file_count} tracked non-test Python files. "
        f"Found {len(result.read_sites)} RRM_DRY_RUN read sites."
    )  # WHY: the required stable output reports guard coverage.
    failures = RrmDryRunReadGuard.validate(result)  # WHY: all policy checks use one result.
    for failure in failures:
        print(failure, file=sys.stderr)  # WHY: CI needs the exact bypass cause.
    return 1 if failures else 0  # WHY: any missing coverage or bypass blocks the change.


if __name__ == "__main__":  # WHY: direct execution is the CI and local gate entry point.
    raise SystemExit(main())  # WHY: return the guard decision to the caller.
