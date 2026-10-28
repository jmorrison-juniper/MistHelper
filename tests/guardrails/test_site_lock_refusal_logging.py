"""Guard the site lock paths that must record refusals.

Why:
    A response can remain correct while its refusal vanishes from the server
    log. This guard checks the counted exits and proves that a missing log
    causes a failure.
"""

from __future__ import annotations  # Keep annotations stable during test collection.

import ast  # Parse Python structure instead of matching comments or message text.
import logging  # Record measured scope and read failures.
from dataclasses import dataclass  # Hold measured counts in one immutable record.
from pathlib import Path  # Build source paths across supported platforms.

import pytest  # Prove the guard rejects a source function without a log.

logger = logging.getLogger(__name__)  # Keep guard records separate from product records.
_REPO_ROOT = Path(__file__).resolve().parents[2]  # Locate the checkout from this test.
_TARGETS = {
    "src/interfaces/portals/upgrade_portal/app/routes/select.py": {
        "take_site_lock": ("return", 4, None),
        "beat_site_lock": ("return", 3, None),
        "free_site_lock": ("return", 3, None),
        "lock_failure_answer": ("return", 1, None),
        "lock_lost_answer": ("return", 1, None),
    },
    "src/interfaces/portals/upgrade_portal/runtime/lock.py": {
        "_replace_holder": ("raise", 1, None),
        "_grant_to_same_owner": ("raise", 1, None),
        "_grant_to_new_owner": ("raise", 2, None),
        "acquire_site_lock": ("raise", 1, None),
        "refresh_site_lock": ("raise", 1, "LOCK_LOST_MESSAGE"),
    },
}  # Count only the exits that the issue assessment found silent.


@dataclass(frozen=True)
class ScanReport:
    """Hold the scope and refusal exit counts of one guard run."""

    scanned_files: int  # Count inputs so an empty scope cannot pass.
    parsed_files: int  # Count parsed files so unreadable inputs cannot pass.
    checked_functions: int  # Count every named function in the contract.
    checked_exits: int  # Count every targeted return or refusal raise.
    silent_exits: int  # Count targeted exits whose function has no structured log.


class SiteLockRefusalLoggingGuard:
    """Measure lock refusal exits and reject functions without structured logs."""

    class StructuredLogPath:
        """Check that each counted exit has a log on its reachable path."""

        @classmethod
        def unlogged_count(
            cls,
            function: ast.FunctionDef | ast.AsyncFunctionDef,
            exits: list[ast.Return | ast.Raise],
        ) -> int:
            """Count target exits without a structured log on their path."""
            parents = {
                child: parent for parent in ast.walk(function) for child in ast.iter_child_nodes(parent)
            }  # Map each node to its direct control-flow parent.
            return sum(
                not cls.exit_has_log(exit_node, function, parents) for exit_node in exits
            )  # Count each unlogged exit separately.

        @classmethod
        def exit_has_log(
            cls,
            exit_node: ast.Return | ast.Raise,
            function: ast.FunctionDef | ast.AsyncFunctionDef,
            parents: dict[ast.AST, ast.AST],
        ) -> bool:
            """Find a log before one exit or a call to a logged refusal helper."""
            if isinstance(exit_node, ast.Return) and isinstance(exit_node.value, ast.Call):
                helper = exit_node.value.func
                if isinstance(helper, ast.Name) and helper.id in {
                    "lock_failure_answer",
                    "lock_lost_answer",
                }:  # These helpers have their own counted exit checks.
                    return True  # The route return delegates its refusal record.
            ancestor = exit_node  # Start at the exact return or raise node.
            while ancestor is not function:  # Walk each containing statement block.
                parent = parents.get(ancestor)  # Read the direct parent.
                if parent is None:  # A detached node cannot prove a log path.
                    return False  # Reject the unparented exit.
                for _, members in ast.iter_fields(parent):  # Find the containing statement list.
                    if isinstance(members, list) and ancestor in members:  # Locate the current statement.
                        prefix = members[: members.index(ancestor)]  # Read statements that ran first.
                        if cls.sequence_always_logs(prefix):  # A prior log covers this reachable path.
                            return True  # The exit has a structured log.
                        ancestor = parent  # Continue through the enclosing branch.
                        break  # Use the matching statement list only.
                else:  # The parent does not contain the current node in a statement list.
                    return False  # Reject an unproven path.
            return False  # No earlier log or logged helper exists.

        @classmethod
        def sequence_always_logs(cls, statements: list[ast.stmt]) -> bool:
            """Return true when prior statements always log before later exits."""
            return any(cls.statement_always_logs(statement) for statement in statements)  # Check each prior statement.

        @classmethod
        def statement_always_logs(cls, statement: ast.stmt) -> bool:
            """Check a logger call or an exhaustive conditional for a log."""
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
                call = statement.value  # Read the candidate logging call.
                target = call.func  # Read its receiver and method name.
                return (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id in {"logger", "_LOGGER"}
                    and target.attr in {"debug", "info", "warning", "error"}
                    and len(call.args) >= 2
                    and isinstance(call.args[0], ast.Constant)
                    and isinstance(call.args[0].value, str)
                )  # Require a safe logger, template, and structured values.
            if isinstance(statement, ast.If):  # Both branches must log before the next statement.
                return cls.sequence_always_logs(statement.body) and cls.sequence_always_logs(
                    statement.orelse
                )  # An absent else branch cannot prove coverage.
            return False  # Other statements do not prove a log on every path.

    @classmethod
    def scan_repository(cls, root: Path) -> ScanReport:
        """Read and measure every lock source file in the guard scope."""
        logger.info("Scanning %d site lock source file(s)", len(_TARGETS))  # Record the input scope.
        parsed_files = 0  # Count files only after a successful parse.
        checked_functions = 0  # Count each required function.
        checked_exits = 0  # Count each target return and refusal raise.
        silent_exits = 0  # Count exits in a function with no structured log.
        for relative, targets in _TARGETS.items():  # Read each source file once.
            path = root / relative  # Build the source path with pathlib.
            try:  # A read failure must fail the guard.
                source = path.read_text(encoding="utf-8")  # Read source as UTF-8.
            except (OSError, UnicodeDecodeError) as read_error:  # Name a missing or invalid input.
                logger.error("Cannot read site lock source %s: %s", path, read_error)  # Report the full input error.
                raise ValueError(f"Cannot read site lock source: {path}") from read_error  # Stop on missing input.
            try:  # A syntax failure must not become a skipped file.
                tree = ast.parse(source, filename=relative)  # Parse the complete source file.
            except SyntaxError as parse_error:  # Name the invalid source.
                logger.error("Cannot parse site lock source %s: %s", path, parse_error)  # Report the full parse error.
                raise ValueError(f"Cannot parse site lock source: {path}") from parse_error  # Stop on invalid syntax.
            parsed_files += 1  # Record the parsed file.
            function_count, exit_count, silent_count = cls.validate_source(tree, targets, relative)  # Check targets.
            checked_functions += function_count  # Accumulate checked functions.
            checked_exits += exit_count  # Accumulate checked exits.
            silent_exits += silent_count  # Accumulate missing log counts.
        cls.ensure_no_silent_exits(silent_exits)  # Reject any unlogged target function.
        report = ScanReport(len(_TARGETS), parsed_files, checked_functions, checked_exits, silent_exits)  # Save counts.
        logger.debug("Checked %d functions and %d refusal exits", checked_functions, checked_exits)  # Report results.
        return report  # Return measured scope to the test.

    @classmethod
    def validate_source(
        cls,
        tree: ast.Module,
        targets: dict[str, tuple[str, int, str | None]],
        relative: str,
    ) -> tuple[int, int, int]:
        """Check function counts, target exits, and structured log calls."""
        functions = [
            node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]  # Find definitions.
        exit_count = 0  # Count target exits in this source.
        silent_exits = 0  # Count exits in functions with no safe log call.
        for name, (kind, expected_count, message_name) in targets.items():  # Check each assessed function.
            matches = [function for function in functions if function.name == name]  # Find the exact function name.
            if len(matches) != 1:  # Missing or duplicate definitions make the scan incomplete.
                raise ValueError(f"{relative}: expected one {name} function, found {len(matches)}")  # Fail closed.
            function = matches[0]  # Read the one matching function.
            target_exits = cls.target_exits(function, kind, message_name)  # Select assessed exits.
            actual_count = len(target_exits)  # Count only the assessed exits.
            if actual_count != expected_count:  # A changed exit count needs a guard review.
                raise ValueError(
                    f"{relative}: {name} has {actual_count} target exits, expected {expected_count}"
                )  # Fail on drift.
            exit_count += actual_count  # Accumulate the measured exits.
            silent_exits += cls.StructuredLogPath.unlogged_count(function, target_exits)  # Check every exit path.
        return len(targets), exit_count, silent_exits  # Return counts for the repository report.

    @staticmethod
    def target_exits(
        function: ast.FunctionDef | ast.AsyncFunctionDef, kind: str, message_name: str | None
    ) -> list[ast.Return | ast.Raise]:
        """Return target exits that match one assessed refusal path."""
        candidates = [
            node for node in ast.walk(function) if isinstance(node, ast.Return if kind == "return" else ast.Raise)
        ]  # Select one exit kind.
        if message_name is None:  # Most target functions count each exit of the selected kind.
            return candidates  # Return the exact measured exits.
        return [
            node
            for node in candidates
            if isinstance(node, ast.Raise)
            and isinstance(node.exc, ast.Call)
            and isinstance(node.exc.func, ast.Name)
            and node.exc.func.id == "LockLostError"
            and node.exc.args
            and isinstance(node.exc.args[0], ast.Name)
            and node.exc.args[0].id == message_name
        ]  # Exclude the already logged life-bound raise.

    @staticmethod
    def ensure_no_silent_exits(silent_exits: int) -> None:
        """Fail when any measured refusal exit belongs to an unlogged function."""
        if silent_exits:  # A positive count means the evidence path is incomplete.
            raise ValueError(f"site lock refusal logging found {silent_exits} silent exit(s)")  # Reject the defect.


def test_site_lock_refusal_logging_guard_counts_and_fails_closed() -> None:
    """The guard counts all target exits and rejects a missing structured log."""
    report = SiteLockRefusalLoggingGuard.scan_repository(_REPO_ROOT)  # Scan both tracked lock modules.
    summary = (
        f"site lock refusal logging: checked {report.checked_functions} function(s), "
        f"{report.checked_exits} exit(s), {report.silent_exits} silent"
    )  # Keep the examined counts visible to the guard runner.
    print(summary)  # Report the guard result.

    assert report.scanned_files == 2  # Both lock source files are in scope.
    assert report.parsed_files == 2  # Both source files parsed successfully.
    assert report.checked_functions == 10  # Every function from the issue assessment was checked.
    assert report.checked_exits == 18  # Every assessed silent exit was checked.
    assert report.silent_exits == 0  # No target function remains silent.

    one_silent_branch = ast.parse(
        "def lock_lost_answer(site_id):\n"
        "    if site_id:\n"
        "        logger.warning('refused %s', site_id)\n"
        "        return None\n"
        "    return None\n"
    )  # Build one branch with a log and one branch without it.
    functions, exits, silent = SiteLockRefusalLoggingGuard.validate_source(
        one_silent_branch, {"lock_lost_answer": ("return", 2, None)}, "memory.py"
    )  # Measure the failing input.
    assert functions == 1  # The test input has one target function.
    assert exits == 2  # The test input has two target exits.
    with pytest.raises(ValueError, match="silent exit"):  # A missing log must not report a green scan.
        SiteLockRefusalLoggingGuard.ensure_no_silent_exits(silent)  # Apply the guard decision to the failing input.
