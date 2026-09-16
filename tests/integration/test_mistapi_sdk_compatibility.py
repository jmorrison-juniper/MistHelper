"""Guard MistHelper calls against the installed ``mistapi`` SDK surface."""

from __future__ import annotations  # Keep annotations stable without runtime imports.

import ast  # Read project and SDK files without executing network code.
import importlib.util  # Locate the installed SDK package from this environment.
import logging  # Show the measured guard path when a failure occurs.
from collections.abc import Iterable, Mapping, Sequence  # Type small seams that the guard tests directly.
from dataclasses import dataclass  # Store each measured call site in a clear record.
from pathlib import Path  # Keep file handling correct on Windows and Linux.

LOGGER = logging.getLogger(__name__)  # Let pytest or callers choose the log level.
REPO_ROOT = Path(__file__).resolve().parents[2]  # Locate the checkout even when pytest changes the working directory.


@dataclass(frozen=True)
class MistapiCallSite:
    """One source location that tries to call a Mist SDK function."""

    path: Path  # Name the caller file for a direct repair.
    line: int  # Name the caller line for a direct repair.
    function: str  # Store the SDK function path without the ``mistapi`` prefix.
    source: str  # State how the guard found the call site.


@dataclass(frozen=True)
class MistapiGuardReport:
    """The measured result from one SDK compatibility scan."""

    resolved_call_sites: tuple[MistapiCallSite, ...]  # Store checked call sites that have enough static detail.
    unresolved_call_sites: tuple[MistapiCallSite, ...]  # Store call sites that do not name a function statically.
    sdk_functions: frozenset[str]  # Store the installed SDK function names for direct membership checks.

    @property
    def resolved_count(self) -> int:
        """Return the count of call sites that the guard checked."""
        return len(self.resolved_call_sites)  # Use the tuple length as the proof of measured work.

    @property
    def unresolved_count(self) -> int:
        """Return the count of call sites that the guard could not resolve."""
        return len(self.unresolved_call_sites)  # Use the tuple length so the hidden surface stays visible.

    @property
    def missing_call_sites(self) -> tuple[MistapiCallSite, ...]:
        """Return SDK calls that do not exist in the installed package."""
        return tuple(
            site for site in self.resolved_call_sites if site.function not in self.sdk_functions
        )  # Flag drift.

    @property
    def failure_messages(self) -> tuple[str, ...]:
        """Return each reason that must make the guard fail."""
        messages = list(self._missing_messages())  # Start with missing SDK functions because they name exact repairs.
        if self.resolved_count == 0:  # A zero count proves that the guard measured nothing.
            messages.append("FAIL resolved mistapi call sites: 0")  # Fail green runs that check no SDK calls.
        return tuple(messages)  # Freeze the result so assertions cannot change it.

    def _missing_messages(self) -> Iterable[str]:
        for site in self.missing_call_sites:  # Report each missing SDK function with its caller.
            yield f"FAIL {site.path}:{site.line}: missing mistapi.{site.function}"  # Name the exact broken surface.

    def summary(self) -> str:
        """Return a compact measured-work line for pull request evidence."""
        resolved = f"Resolved mistapi call sites: {self.resolved_count}."  # Keep the checked count visible.
        unresolved = f"Unresolved static call sites: {self.unresolved_count}"  # Keep unmeasured paths visible.
        return f"{resolved} {unresolved}"  # Join both counts for one evidence line.


class MistapiSdkSurfaceCollector:
    """Collect callable names that the installed ``mistapi`` package defines."""

    def __init__(self, package_root: Path) -> None:
        self.package_root = package_root  # Keep the root explicit for tests and the installed SDK scan.

    @classmethod
    def from_installed_package(cls) -> MistapiSdkSurfaceCollector:
        """Build a collector for the installed ``mistapi`` package."""
        logging.info("Locating the installed mistapi package")  # Log before environment inspection.
        spec = importlib.util.find_spec("mistapi")  # Ask Python for the package used by this test run.
        if spec is None or spec.origin is None:  # A missing SDK means the guard cannot read its input.
            raise AssertionError("FAIL mistapi package could not be located")  # Fail instead of passing without input.
        package_root = Path(spec.origin).parent  # Convert the package file path to the package directory.
        logging.debug("Located mistapi package at %s", package_root)  # Record the measured SDK root.
        return cls(package_root)  # Return a configured collector for the installed package.

    def collect(self) -> frozenset[str]:
        """Return public callable names from the installed SDK."""
        logging.info("Collecting mistapi SDK functions from %s", self.package_root)  # Log before reading SDK files.
        functions: set[str] = set()  # Use a set so re-exported names do not duplicate the surface.
        for path in sorted(self.package_root.rglob("*.py")):  # Walk each installed SDK module once.
            functions.update(self._functions_from_path(path))  # Add module definitions and supported re-exports.
        logging.debug("Collected %d mistapi SDK function(s)", len(functions))  # Prove the SDK scan read data.
        return frozenset(functions)  # Freeze the set for deterministic guard decisions.

    def _functions_from_path(self, path: Path) -> set[str]:
        relative_module = self._module_name(path)  # Convert the SDK path to a dotted module path.
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))  # Parse the SDK file safely.
        functions = self._top_level_callables(tree, relative_module)  # Add direct functions and classes.
        functions.update(self._re_exported_callables(tree, relative_module))  # Add aliases such as mistapi.get_all.
        return functions  # Return the names from this module.

    def _module_name(self, path: Path) -> str:
        parts = (
            path.relative_to(self.package_root).with_suffix("").parts
        )  # Preserve package nesting from the file path.
        clean_parts = parts[:-1] if parts[-1] == "__init__" else parts  # Treat package __init__ as the package itself.
        return ".".join(clean_parts)  # Return a path relative to ``mistapi``.

    def _top_level_callables(self, tree: ast.Module, module_name: str) -> set[str]:
        names: set[str] = set()  # Collect callable names defined in this module.
        for node in tree.body:  # Read only module-level definitions because SDK calls target module attributes.
            if isinstance(
                node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
            ):  # Classes are callable constructors.
                names.add(self._join_name(module_name, node.name))  # Add the callable path without the package prefix.
        return names  # Return direct public and private definitions for exact resolution.

    def _re_exported_callables(self, tree: ast.Module, module_name: str) -> set[str]:
        names: set[str] = set()  # Collect aliases created by package imports.
        for node in tree.body:  # Read import statements without importing SDK modules.
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("mistapi"):
                names.update(self._aliases_from_import(node, module_name))  # Add aliases exposed from this package.
        return names  # Return aliases such as ``get_all`` from package ``__init__``.

    def _aliases_from_import(self, node: ast.ImportFrom, module_name: str) -> set[str]:
        names: set[str] = set()  # Collect re-exported names from one import line.
        for alias in node.names:  # Each alias can expose one callable at the current package level.
            exposed_name = alias.asname or alias.name  # Use the public alias when the import defines one.
            if not exposed_name.startswith("_"):  # Ignore private helper aliases that callers should not use.
                names.add(self._join_name(module_name, exposed_name))  # Add the public alias path for resolution.
        return names  # Return aliases from this import statement.

    def _join_name(self, module_name: str, callable_name: str) -> str:
        return f"{module_name}.{callable_name}" if module_name else callable_name  # Keep root exports short.


class MistapiSourceCallCollector(ast.NodeVisitor):
    """Collect Mist SDK call sites from one project source file."""

    def __init__(self, path: Path, source: str) -> None:
        self.path = path  # Keep the relative source path for failure output.
        self.call_sites: list[MistapiCallSite] = []  # Store resolved call sites from direct and registry paths.
        self.unresolved_call_sites: list[MistapiCallSite] = []  # Store dynamic paths that the guard cannot prove.
        self._aliases: list[dict[str, str]] = [{"mistapi": "mistapi"}]  # Track imports and lazy import_module aliases.
        self._tree = ast.parse(source, filename=str(path))  # Parse the source once for all collector passes.

    def collect(self) -> tuple[tuple[MistapiCallSite, ...], tuple[MistapiCallSite, ...]]:
        """Return resolved and unresolved Mist SDK call sites from this source."""
        logging.info("Collecting mistapi call sites from %s", self.path)  # Log before source analysis.
        self.visit(self._tree)  # Walk the parsed source and fill both call-site lists.
        logging.debug(
            "Collected %d resolved and %d unresolved call site(s)",
            len(self.call_sites),
            len(self.unresolved_call_sites),
        )  # Report measured paths.
        return tuple(self.call_sites), tuple(self.unresolved_call_sites)  # Return immutable results to the guard.

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:  # Record module aliases such as ``import mistapi as sdk``.
            if alias.name == "mistapi" or alias.name.startswith("mistapi."):
                alias_name = (
                    alias.asname or alias.name.split(".")[0]
                )  # Python binds the root name when no alias exists.
                alias_value = (
                    alias.name if alias.asname else "mistapi"
                )  # Keep ``import mistapi.api`` calls rooted at mistapi.
                self._aliases[-1][alias_name] = alias_value  # Resolve later calls through alias.
        self.generic_visit(node)  # Continue into any child nodes for completeness.

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module and node.module.startswith("mistapi"):
            for alias in node.names:  # Record from-import aliases that call SDK functions directly.
                self._aliases[-1][alias.asname or alias.name] = f"{node.module}.{alias.name}"  # Map alias to SDK path.
        self.generic_visit(node)  # Continue into annotations or other child nodes.

    def visit_Assign(self, node: ast.Assign) -> None:
        target_name = self._single_name_target(node)  # Resolve simple assignments that create aliases.
        alias_value = self._assignment_alias(node.value)  # Read import_module and alias-to-alias assignments.
        if target_name and alias_value:  # Only a simple name can become a later call prefix.
            self._aliases[-1][target_name] = alias_value  # Store the alias in the current scope.
        self.generic_visit(node)  # Continue so calls inside the assignment are still scanned.

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._aliases.append(dict(self._aliases[-1]))  # Give the function a local copy of known aliases.
        self.generic_visit(node)  # Scan calls and local imports inside the function body.
        self._aliases.pop()  # Restore the outer alias map after the function body.

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)  # Async functions use the same alias and call rules.

    def visit_Call(self, node: ast.Call) -> None:
        direct_function = self._call_function(node.func)  # Resolve a normal callable expression when possible.
        if direct_function is not None:  # Direct calls have a function name that the guard can check.
            self.call_sites.append(MistapiCallSite(self.path, node.lineno, direct_function, "attribute"))  # Save it.
        registry_function = self._registry_call_function(
            node
        )  # Resolve string registry entries such as _SimpleEndpointOp.
        if registry_function is not None:  # Registry entries also name a concrete SDK function.
            self.call_sites.append(MistapiCallSite(self.path, node.lineno, registry_function, "registry"))  # Save it.
        unresolved = self._unresolved_dynamic_import(node)  # Detect an import_module string with no static function.
        if unresolved is not None:  # The guard cannot prove which function the module string calls.
            self.unresolved_call_sites.append(unresolved)  # Make the unmeasured site visible in the report.
        self.generic_visit(node)  # Continue into call arguments for nested SDK calls.

    def visit_Tuple(self, node: ast.Tuple) -> None:
        tuple_function = self._tuple_registry_function(node)  # Resolve ("mistapi.module", "function") registries.
        if tuple_function is not None:  # Tuple registries name concrete SDK functions.
            self.call_sites.append(MistapiCallSite(self.path, node.lineno, tuple_function, "registry"))  # Save it.
        self.generic_visit(node)  # Continue so nested values remain visible.

    def _call_function(self, node: ast.AST) -> str | None:
        parts = self._attribute_chain(node)  # Convert an attribute expression to names.
        if not parts:  # Dynamic call expressions cannot resolve statically.
            return None  # Leave them to other checks because no Mist marker exists.
        normalized = self._normalize_parts(parts)  # Convert aliases and deps.mistapi forms to SDK paths.
        return self._strip_prefix(normalized) if normalized else None  # Store names without the package prefix.

    def _registry_call_function(self, node: ast.Call) -> str | None:
        if len(node.args) < 2:  # Registry calls need at least the operation name and module path.
            return None  # This call shape is not a supported SDK registry entry.
        operation = self._constant_string(node.args[0])  # The first argument stores the SDK function name.
        module_path = self._constant_string(node.args[1])  # The second argument stores the SDK module path.
        if operation and module_path and module_path.startswith("mistapi."):
            return self._strip_prefix(f"{module_path}.{operation}")  # Convert the registry entry to a callable path.
        return None  # Other two-string calls are not SDK registries.

    def _tuple_registry_function(self, node: ast.Tuple) -> str | None:
        if len(node.elts) != 2:  # Only two-value tuples can store a module and function pair.
            return None  # Larger tuples do not match the known registry shape.
        first = self._constant_string(node.elts[0])  # Read the first tuple value.
        second = self._constant_string(node.elts[1])  # Read the second tuple value.
        if first and second and first.startswith("mistapi."):
            return self._strip_prefix(f"{first}.{second}")  # Convert the pair to a callable path.
        return None  # Non-Mist tuples are ignored by this guard.

    def _unresolved_dynamic_import(self, node: ast.Call) -> MistapiCallSite | None:
        call_name = ".".join(self._attribute_chain(node.func))  # Name the import helper if it is a plain call.
        module_path = self._constant_string(node.args[0]) if node.args else None  # Read the imported module path.
        if call_name.endswith("import_module") and module_path and module_path.startswith("mistapi."):
            return MistapiCallSite(
                self.path, node.lineno, self._strip_prefix(module_path), "dynamic-module"
            )  # Record it.
        return None  # Other dynamic imports do not affect the Mist SDK guard.

    def _assignment_alias(self, value: ast.AST) -> str | None:
        if isinstance(value, ast.Name):  # An alias can point at a prior Mist SDK alias.
            return self._aliases[-1].get(value.id)  # Return the existing SDK path when one exists.
        if isinstance(value, ast.Call):  # A lazy import_module call can bind a module variable.
            return self._import_module_alias(value)  # Resolve the imported SDK module path.
        return None  # Other assignments do not create a static SDK alias.

    def _import_module_alias(self, value: ast.Call) -> str | None:
        call_name = ".".join(self._attribute_chain(value.func))  # Support import_module and importlib.import_module.
        module_path = self._constant_string(value.args[0]) if value.args else None  # Read the constant module path.
        if call_name.endswith("import_module") and module_path and module_path.startswith("mistapi."):
            return module_path  # Store the full SDK module path for later calls on the variable.
        return None  # Dynamic module names cannot resolve statically.

    def _single_name_target(self, node: ast.Assign) -> str | None:
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):  # Only a single name is safe to alias.
            return node.targets[0].id  # Return the bound name for the alias map.
        return None  # Complex assignment targets do not create stable function aliases.

    def _attribute_chain(self, node: ast.AST) -> list[str]:
        if isinstance(node, ast.Name):  # A bare name is the root of a call or alias.
            return [node.id]  # Return one part so alias resolution can inspect it.
        if isinstance(node, ast.Attribute):  # Attribute calls hold dotted SDK paths.
            parent = self._attribute_chain(node.value)  # Resolve the left side first.
            return [*parent, node.attr] if parent else []  # Add the current attribute when the parent resolved.
        return []  # Subscripts, calls, and lambdas cannot form a static dotted path here.

    def _normalize_parts(self, parts: Sequence[str]) -> str | None:
        first_alias = self._aliases[-1].get(parts[0])  # Resolve imports such as ``sdk.api`` or ``module.getSelf``.
        if first_alias is not None:  # The first name is an SDK alias.
            return ".".join([first_alias, *parts[1:]])  # Build the full SDK path from the alias.
        if "mistapi" in parts:  # Dependency objects can carry ``deps.mistapi``.
            return ".".join(parts[parts.index("mistapi") :])  # Drop the local object prefix.
        return None  # The call does not target the Mist SDK.

    def _strip_prefix(self, value: str) -> str:
        return value.removeprefix("mistapi.")  # Compare names relative to the package root.

    def _constant_string(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):  # Only literal strings are safe to resolve.
            return node.value  # Return the exact registry or module string.
        return None  # Dynamic strings are not statically measured.


class MistapiSdkCompatibilityGuard:
    """Resolve MistHelper SDK calls against the installed package."""

    def __init__(self, root: Path) -> None:
        self.root = root  # Store the checkout root so paths in reports stay relative.

    def evaluate_installed_sdk(self) -> MistapiGuardReport:
        """Return a compatibility report for this checkout and environment."""
        logging.info("Starting mistapi SDK compatibility guard")  # Log the start of the measured guard.
        sdk_functions = MistapiSdkSurfaceCollector.from_installed_package().collect()  # Read the installed SDK surface.
        sources = self._project_sources()  # Read the project files that can call the SDK.
        report = self.evaluate_sources(sources, sdk_functions)  # Compare source call sites to SDK definitions.
        logging.debug("%s", report.summary())  # Record the count that proves this guard measured call sites.
        return report  # Return the report so tests can enforce failure rules.

    def evaluate_sources(self, sources: Mapping[Path, str], sdk_functions: Iterable[str]) -> MistapiGuardReport:
        """Evaluate supplied project sources against supplied SDK functions."""
        logging.info("Evaluating %d source file(s) for mistapi call sites", len(sources))  # Log the input size.
        resolved: list[MistapiCallSite] = []  # Collect all statically resolved SDK calls.
        unresolved: list[MistapiCallSite] = []  # Collect all dynamic SDK module references.
        for path, source in sources.items():  # Analyze each source independently for precise file names.
            file_resolved, file_unresolved = MistapiSourceCallCollector(path, source).collect()  # Scan one file.
            resolved.extend(file_resolved)  # Add resolved calls to the report input.
            unresolved.extend(file_unresolved)  # Add unresolved calls so they remain visible.
        logging.debug("Evaluation resolved %d call site(s)", len(resolved))  # Log the measured static coverage.
        return MistapiGuardReport(tuple(resolved), tuple(unresolved), frozenset(sdk_functions))  # Build the report.

    def _project_sources(self) -> dict[Path, str]:
        source_paths = [
            self.root / "MistHelper.py",
            *sorted((self.root / "src").rglob("*.py")),
        ]  # Scan app sources only.
        return {path.relative_to(self.root): path.read_text(encoding="utf-8") for path in source_paths}  # Read once.


def test_installed_mistapi_surface_covers_source_calls() -> None:
    guard = MistapiSdkCompatibilityGuard(REPO_ROOT)  # Use the checkout under test as the source of call sites.
    report = guard.evaluate_installed_sdk()  # Compare the source calls to the installed SDK.
    assert report.resolved_count > 0, report.summary()  # Fail if the guard measured no SDK call site.
    assert not report.missing_call_sites, "\n".join(report.failure_messages)  # Fail with caller and missing function.


def test_guard_fails_for_deliberately_missing_sdk_function() -> None:
    sources = {Path("src/example.py"): "import mistapi\nmistapi.api.v1.orgs.fake.missingFunction()\n"}  # Broken call.
    report = MistapiSdkCompatibilityGuard(REPO_ROOT).evaluate_sources(
        sources, {"api.v1.orgs.sites.listOrgSites"}
    )  # Check it.
    assert report.resolved_count == 1  # Prove the test measured the deliberate broken call site.
    assert report.failure_messages == (
        "FAIL src\\example.py:2: missing mistapi.api.v1.orgs.fake.missingFunction",
    )  # Prove failure.


def test_guard_fails_when_zero_call_sites_resolve() -> None:
    sources = {Path("src/example.py"): "VALUE = 1\n"}  # This source has no Mist SDK call site.
    report = MistapiSdkCompatibilityGuard(REPO_ROOT).evaluate_sources(
        sources, {"api.v1.orgs.sites.listOrgSites"}
    )  # Check it.
    assert report.resolved_count == 0  # Confirm the fixture exercises the zero-measurement path.
    assert report.failure_messages == (
        "FAIL resolved mistapi call sites: 0",
    )  # Prove the guard fails when it measures zero.


def test_guard_reports_unresolved_dynamic_module_imports() -> None:
    sources = {
        Path("src/example.py"): "from importlib import import_module\nmodule = import_module(name)\n"
    }  # Not a Mist path.
    mist_sources = {
        Path("src/mist.py"): "from importlib import import_module\nmodule = import_module('mistapi.api.v1.self.self')\n"
    }  # Mist module only.
    report = MistapiSdkCompatibilityGuard(REPO_ROOT).evaluate_sources(
        sources | mist_sources, {"api.v1.self.self.getSelf"}
    )  # Check it.
    assert report.unresolved_count == 1  # Make the unmeasured dynamic module reference visible.
    assert report.unresolved_call_sites[0].function == "api.v1.self.self"  # Name the module that needs a function.
