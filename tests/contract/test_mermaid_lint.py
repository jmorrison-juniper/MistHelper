"""Contract tests for the Mermaid syntax gate."""

import subprocess  # Run the parser when local Node dependencies exist.
from pathlib import Path  # Build paths without platform-specific separators.

import pytest  # Skip the runtime check when dependencies are not installed.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Locate the repository from this test file.
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "mermaid" / "lint_mermaid.mjs"  # Identify the parser entry point.
PACKAGE_PATH = REPOSITORY_ROOT / "scripts" / "mermaid" / "package.json"  # Identify the dependency manifest.
LOCK_PATH = REPOSITORY_ROOT / "scripts" / "mermaid" / "package-lock.json"  # Identify the reproducible dependency lock.
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"  # Identify the CI workflow contract.


def test_mermaid_parser_files_exist() -> None:
    """Require the parser and its locked dependencies."""
    assert SCRIPT_PATH.is_file()  # Keep the CI command target available.
    assert PACKAGE_PATH.is_file()  # Keep the dependency manifest available.
    assert LOCK_PATH.is_file()  # Keep npm ci reproducible in CI.


def test_workflow_runs_mermaid_parser() -> None:
    """Require CI to install and run the Mermaid parser."""
    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")  # Read the workflow contract.
    assert "mermaid_lint:" in workflow_text  # Require a dedicated syntax gate.
    assert "scripts/mermaid/package-lock.json" in workflow_text  # Require npm cache coverage.
    assert "run: npm ci" in workflow_text  # Require locked dependency installation.
    assert "node scripts/mermaid/lint_mermaid.mjs" in workflow_text  # Require parser execution.


@pytest.mark.skipif(not (SCRIPT_PATH.parent / "node_modules").is_dir(), reason="Node dependencies are not installed")
def test_current_diagrams_parse() -> None:
    """Require the current documentation tree to pass the parser."""
    completed = subprocess.run(  # Execute the same parser command that CI uses.
        ["node", str(SCRIPT_PATH)],  # Pass the parser entry point to Node.
        cwd=REPOSITORY_ROOT,  # Match the repository root used by CI.
        check=False,  # Capture the result for an assertion with useful test output.
        capture_output=True,  # Preserve parser output when the contract fails.
        text=True,  # Return output as text for readable assertion details.
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr  # Require every current block to parse.


@pytest.mark.skipif(not (SCRIPT_PATH.parent / "node_modules").is_dir(), reason="Node dependencies are not installed")
def test_broken_diagram_fails(tmp_path: Path) -> None:
    """Require a broken Mermaid block to fail with its source path."""
    broken_file = tmp_path / "broken.md"  # Create an isolated invalid diagram input.
    broken_file.write_text("```mermaid\nflowchart TD\n  A -->\n```\n", encoding="utf-8")  # Write a syntax error.
    completed = subprocess.run(  # Execute the parser against the invalid input.
        ["node", str(SCRIPT_PATH), "--docs-dir", str(tmp_path), "--extra-file", str(broken_file)],  # Pass test paths.
        cwd=REPOSITORY_ROOT,  # Match the repository root used by CI.
        check=False,  # Capture the expected failure for assertions.
        capture_output=True,  # Preserve the diagnostic message.
        text=True,  # Return output as text for readable assertions.
    )
    assert completed.returncode == 1  # Require the gate to reject invalid syntax.
    assert "broken.md" in completed.stderr  # Require the diagnostic to name the source file.
