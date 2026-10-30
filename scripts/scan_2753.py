"""Scan the selected inventory comparator for hidden device ID defaults."""

from __future__ import annotations  # WHY: retain consistent annotation behavior across Python versions.

import ast  # WHY: inspect call arguments without matching comments or strings.
import sys  # WHY: report source failures on the error stream.
from pathlib import Path  # WHY: keep the source path portable across operating systems.


class MissingDeviceIdDefaultScanner:
    """Find empty-string device ID defaults and report a bounded scan result."""

    SOURCE_PATH = Path(__file__).resolve().parents[1] / (  # WHY: root the source path at this script's repository.
        "src/mist/resources/inventory/csv_comparator.py"  # WHY: scan only the owned comparator module.
    )

    def __init__(self, source_path: Path = SOURCE_PATH) -> None:
        """Store the source path so tests can model unreadable inputs."""
        self.source_path = source_path  # WHY: tests can supply a controlled path.

    def find_empty_defaults(self, source: str) -> list[int]:
        """Return source lines that default an `id` lookup to an empty string."""
        syntax_tree = ast.parse(source)  # WHY: malformed input must fail instead of passing silently.
        return [
            node.lineno  # WHY: provide an actionable source location.
            for node in ast.walk(syntax_tree)  # WHY: inspect every call in the selected module.
            if isinstance(node, ast.Call)  # WHY: only function calls can carry lookup defaults.
            and isinstance(node.func, ast.Attribute)  # WHY: identify mapping method calls.
            and node.func.attr == "get"  # WHY: the defect uses a mapping get call.
            and len(node.args) == 2  # WHY: require an explicit default argument.
            and isinstance(node.args[0], ast.Constant)  # WHY: read only a literal field name.
            and node.args[0].value == "id"  # WHY: identify the required device ID.
            and isinstance(node.args[1], ast.Constant)  # WHY: require a literal empty default.
            and node.args[1].value == ""  # WHY: identify the missing-input mask.
        ]

    def run(self) -> int:
        """Scan one source file and return a nonzero status for candidates or errors."""
        try:
            source = self.source_path.read_text(encoding="utf-8")  # WHY: parse tracked source as UTF-8.
            candidate_lines = self.find_empty_defaults(source)  # WHY: count only the selected defect.
        except (OSError, SyntaxError) as error:
            print(f"ERROR: Cannot scan {self.source_path}: {error}", file=sys.stderr)  # WHY: expose scan failure.
            print("Scanned 0 source files; candidate count unavailable.")  # WHY: distinguish failure from zero.
            return 2  # WHY: prevent an unreadable source from reporting success.
        print(f"Scanned 1 source file; found {len(candidate_lines)} empty device ID defaults.")  # WHY: report evidence.
        for line_number in candidate_lines:
            print(f"Candidate at line {line_number}.")  # WHY: identify each remaining default.
        return 1 if candidate_lines else 0  # WHY: fail while the selected defect remains.


if __name__ == "__main__":
    raise SystemExit(MissingDeviceIdDefaultScanner().run())  # WHY: preserve the command exit status.
