"""Contract tests for polyglot export call sites."""

import ast  # Parse source files without importing the application.
from pathlib import Path  # Resolve the repository source directory.

SOURCE_ROOT = Path(__file__).parents[2] / "src"  # Keep the contract scoped to production source.


def test_source_export_calls_name_the_api_function() -> None:
    """Require every source export call to provide its routing identifier."""
    missing_calls: list[str] = []  # Collect every omission for one useful failure.
    for source_path in SOURCE_ROOT.rglob("*.py"):  # Inspect every production Python module.
        tree = ast.parse(  # Parse the module to inspect call keywords safely.
            source_path.read_text(encoding="utf-8"), filename=str(source_path)
        )
        for node in ast.walk(tree):  # Visit every call expression in the module.
            if not isinstance(node, ast.Call):  # Ignore non-call syntax nodes.
                continue
            if not isinstance(node.func, ast.Attribute):  # Ignore direct function aliases.
                continue
            if node.func.attr != "write_with_format_selection":  # Select only export calls.
                continue
            if not any(keyword.arg == "api_function_name" for keyword in node.keywords):  # Require routing metadata.
                missing_calls.append(f"{source_path}:{node.lineno}")  # Record the exact omission.
    assert not missing_calls, "Missing api_function_name: " + ", ".join(missing_calls)  # Report all omissions.
