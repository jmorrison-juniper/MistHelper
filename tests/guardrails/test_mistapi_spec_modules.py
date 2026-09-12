"""Guard endpoint specification SDK module lines against mistapi drift."""

from __future__ import annotations  # Keep annotation evaluation stable during test collection.

import ast  # Parse SDK source so the guard matches real function definitions.
import logging  # Record each scan step for local diagnosis.
from pathlib import Path  # Resolve repository and package paths on Windows and Linux.

import pytest  # Skip cleanly when the optional SDK package is absent.

mistapi = pytest.importorskip(  # Skip this guard when the local environment has no SDK.
    "mistapi",
    reason="mistapi is not installed, so the SDK module guard cannot run.",
)

_LOGGER = logging.getLogger(__name__)  # Share one logger for this guard module.
_REPO_ROOT = Path(__file__).resolve().parents[2]  # Locate the repository root from tests/guardrails.
_SPECS_ROOT = _REPO_ROOT / "specs"  # Limit the scan to the endpoint specification tree.


class MistapiSpecModuleIndex:
    """Build indexes for endpoint specifications and installed SDK definitions."""

    @staticmethod
    def sdk_definitions() -> dict[str, str]:
        """Return each installed SDK function and the module that defines it."""
        sdk_root = Path(mistapi.__file__).resolve().parent  # Start at the installed mistapi package root.
        definitions: dict[str, str] = {}  # Store one module path for each SDK function name.
        _LOGGER.info("Scanning mistapi SDK source at %s", sdk_root)  # Log the package scan start.
        for python_file in sdk_root.rglob("*.py"):  # Read every SDK source file for real definitions.
            module_path = MistapiSpecModuleIndex._module_path(sdk_root, python_file)  # Get the source module path.
            source_text = python_file.read_text(encoding="utf-8")  # Read the source with a fixed encoding.
            module_ast = ast.parse(source_text, filename=str(python_file))  # Parse the source safely.
            for node in module_ast.body:  # Inspect only top-level definitions from the source file.
                if isinstance(node, ast.FunctionDef):  # Match a real "def" statement, not a substring.
                    definitions[node.name] = module_path  # Remember the exact module that owns the function.
        _LOGGER.debug("Found %s mistapi SDK function definitions", len(definitions))  # Log the scan result size.
        return definitions  # Return the definition map for the assertion phase.

    @staticmethod
    def spec_declarations() -> list[tuple[Path, str, str]]:
        """Return each spec that declares an operation and an SDK module path."""
        declarations: list[tuple[Path, str, str]] = []  # Hold the spec path, operation ID, and declared module.
        _LOGGER.info("Scanning endpoint specifications at %s", _SPECS_ROOT)  # Log the spec scan start.
        for spec_file in sorted(_SPECS_ROOT.rglob("spec.md")):  # Read only endpoint spec files.
            fields = MistapiSpecModuleIndex._source_fields(spec_file)  # Extract source endpoint fields from the spec.
            if fields is not None:  # Keep only specs with both required fields.
                declarations.append((spec_file, fields[0], fields[1]))  # Add one declaration for later validation.
        _LOGGER.debug("Found %s SDK module declarations", len(declarations))  # Log the declaration count.
        return declarations  # Return the complete declaration list for the guard.

    @staticmethod
    def _module_path(sdk_root: Path, python_file: Path) -> str:
        relative_path = python_file.relative_to(sdk_root).with_suffix("")  # Remove the package root and file suffix.
        path_parts = ["mistapi", *relative_path.parts]  # Build the Python module path parts from the file path.
        if path_parts[-1] == "__init__":  # Package initializers expose the package module itself.
            path_parts = path_parts[:-1]  # Drop the initializer file name from the module path.
        return ".".join(path_parts)  # Return the dotted module path used by the specifications.

    @staticmethod
    def _source_fields(spec_file: Path) -> tuple[str, str] | None:
        operation_id = ""  # Use an empty value until the source endpoint line is found.
        sdk_module = ""  # Use an empty value until the SDK module line is found.
        for line in spec_file.read_text(encoding="utf-8").splitlines():  # Read the spec as UTF-8 text.
            if line.startswith("- **operationId**: `"):  # Find the source endpoint operation identifier.
                operation_id = line.split("`", 2)[1]  # Extract the identifier without Markdown markup.
            if line.startswith("- **mistapi SDK module**: `"):  # Find only lines that declare a module path.
                sdk_module = line.split("`", 2)[1]  # Extract the dotted module path without Markdown markup.
        if operation_id and sdk_module:  # A guardable spec must name both the operation and the module.
            return operation_id, sdk_module  # Return the parsed values for validation.
        return None  # Specs without a module path need a separate upstream decision.


class TestMistapiSpecModules:
    """Verify endpoint specs name real mistapi SDK modules."""

    def test_declared_sdk_modules_define_the_declared_operation(self) -> None:
        """Each SDK module line must match the installed source definition."""
        definitions = MistapiSpecModuleIndex.sdk_definitions()  # Build the source-derived SDK function map.
        declarations = MistapiSpecModuleIndex.spec_declarations()  # Build the Markdown declaration list.
        failures = []  # Collect all mismatches so one run reports the full repair set.
        for spec_file, operation_id, sdk_module in declarations:  # Check every declared SDK module path.
            actual_module = definitions.get(operation_id)  # Read the module that actually defines this operation.
            if actual_module != sdk_module:  # A missing function or a wrong module path breaks the specification.
                relative = spec_file.relative_to(_REPO_ROOT)  # Report paths relative to the repository root.
                message = f"{relative}: {operation_id} declares {sdk_module}"  # Start the mismatch report.
                message = f"{message}, found {actual_module}"  # Add the source-derived module path.
                failures.append(message)  # Keep this mismatch for the complete failure report.
        assert not failures, "\n".join(failures)  # Fail once with every bad declaration for a complete report.
