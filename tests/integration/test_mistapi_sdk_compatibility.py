"""Guard MistHelper calls against the installed ``mistapi`` SDK surface."""

from __future__ import annotations  # Keep annotations stable without runtime imports.

import ast  # Read project and SDK files without executing network code.
import importlib.util  # Locate the installed SDK package from this environment.
import logging  # Show the measured guard path when a failure occurs.
from collections.abc import Iterable, Mapping, Sequence  # Type small seams that the guard tests directly.
from dataclasses import dataclass, field  # Store each measured call site in a clear record.
from pathlib import Path  # Keep file handling correct on Windows and Linux.

from pytest import CaptureFixture  # Type captured-output control without importing test internals.

LOGGER = logging.getLogger(__name__)  # Let pytest or callers choose the log level.
REPO_ROOT = Path(__file__).resolve().parents[2]  # Locate the checkout even when pytest changes the working directory.
UNRESOLVED_CALL_SITE_BASELINE = 10  # Fail only when new dynamic SDK paths increase the measured baseline.
UNVERIFIABLE_SIGNATURE_BASELINE = 366  # Fail only when new dynamic SDK argument patterns increase the baseline.
KNOWN_SIGNATURE_FAILURES: frozenset[tuple[str, str, str]] = frozenset()  # Issue #2741 removed the known failures.


@dataclass(frozen=True)
class MistapiCallArguments:
    """Static argument facts from one source call."""

    positional_count: int = 0  # Count positional arguments so required position checks can run.
    keywords: tuple[str, ...] = ()  # Store explicit keywords so parameter renames fail for keyword calls.
    has_starargs: bool = False  # Mark ``*args`` calls because static arity cannot prove them safe.
    has_kwargs: bool = False  # Mark ``**kwargs`` calls because static keywords cannot prove them safe.

    @property
    def has_dynamic_arguments(self) -> bool:
        """Return whether the call uses arguments that static analysis cannot prove."""
        return self.has_starargs or self.has_kwargs  # Treat either dynamic shape as unverifiable.


@dataclass(frozen=True)
class MistapiSdkSignature:
    """One installed SDK function signature in the form this guard needs."""

    positional_parameters: tuple[str, ...]  # Store positional capacity for arity checks.
    required_positional: tuple[str, ...]  # Store required positional-or-keyword names.
    required_keyword_only: tuple[str, ...]  # Store keyword-only names that callers must pass.
    accepted_keywords: frozenset[str]  # Store legal keyword names so removed parameters fail.
    accepts_dynamic: tuple[bool, bool] = (False, False)  # Store ``*args`` and ``**kwargs`` support.

    @property
    def accepts_varargs(self) -> bool:
        """Return whether the SDK function accepts arbitrary positional arguments."""
        return self.accepts_dynamic[0]  # Keep the tuple compact for the five-field rule.

    @property
    def accepts_kwargs(self) -> bool:
        """Return whether the SDK function accepts arbitrary keyword arguments."""
        return self.accepts_dynamic[1]  # Keep the tuple compact for the five-field rule.


@dataclass(frozen=True)
class MistapiCallSite:
    """One source location that tries to call a Mist SDK function."""

    path: Path  # Name the caller file for a direct repair.
    line: int  # Name the caller line for a direct repair.
    function: str  # Store the SDK function path without the ``mistapi`` prefix.
    source: str  # State how the guard found the call site.
    arguments: MistapiCallArguments = field(default_factory=MistapiCallArguments)  # Store static call details.


@dataclass(frozen=True)
class MistapiGuardReport:
    """The measured result from one SDK compatibility scan."""

    resolved_call_sites: tuple[MistapiCallSite, ...]  # Store checked call sites that have enough static detail.
    unresolved_call_sites: tuple[MistapiCallSite, ...]  # Store call sites that do not name a function statically.
    sdk_signatures: Mapping[str, MistapiSdkSignature]  # Store installed SDK signatures for compatibility checks.

    @property
    def resolved_count(self) -> int:
        """Return the count of call sites that name an SDK function."""
        return len(self.resolved_call_sites)  # Use the tuple length as the proof of measured names.

    @property
    def checked_count(self) -> int:
        """Return the count of call sites that received a static signature check."""
        return len(self.checked_call_sites)  # Count only calls where static arguments are complete.

    @property
    def unresolved_count(self) -> int:
        """Return the count of call sites that do not name a function."""
        return len(self.unresolved_call_sites)  # Use the tuple length so the hidden surface stays visible.

    @property
    def unverifiable_count(self) -> int:
        """Return the count of named calls that cannot receive a signature check."""
        return len(self.unverifiable_call_sites)  # Keep dynamic argument use visible and bounded.

    @property
    def checked_call_sites(self) -> tuple[MistapiCallSite, ...]:
        """Return call sites with a known function and static arguments."""
        return tuple(
            site for site in self.resolved_call_sites if self._can_check_signature(site)
        )  # Filter static calls.

    @property
    def unverifiable_call_sites(self) -> tuple[MistapiCallSite, ...]:
        """Return call sites that are too dynamic for signature proof."""
        return tuple(site for site in self.resolved_call_sites if self._cannot_check_signature(site))  # Filter gaps.

    @property
    def missing_call_sites(self) -> tuple[MistapiCallSite, ...]:
        """Return SDK calls that do not exist in the installed package."""
        return tuple(
            site for site in self.resolved_call_sites if site.function not in self.sdk_signatures
        )  # Flag drift.

    @property
    def signature_messages(self) -> tuple[str, ...]:
        """Return SDK signature failures for statically checked call sites."""
        messages: list[str] = []  # Keep a stable order for tests and pull request evidence.
        for site in self.checked_call_sites:  # Compare each static call against the installed signature.
            comparator = MistapiSignatureComparator(site, self.sdk_signatures[site.function])  # Prepare one check.
            messages.extend(comparator.messages())  # Add all signature issues from this call site.
        return tuple(messages)  # Freeze the result so assertions cannot change it.

    @property
    def failure_messages(self) -> tuple[str, ...]:
        """Return each reason that must make the guard fail."""
        messages = list(self._missing_messages())  # Start with missing SDK functions because they name exact repairs.
        messages.extend(self.unexpected_signature_messages)  # Add new required, removed, and arity failures.
        if self.checked_count == 0:  # A zero count proves that the guard measured no static SDK call.
            messages.append("FAIL checked mistapi call signatures: 0")  # Fail green runs that check no signatures.
        messages.extend(self.failure_messages_for_unresolved_baseline(UNRESOLVED_CALL_SITE_BASELINE))  # Add name gaps.
        messages.extend(
            self.failure_messages_for_unverifiable_baseline(UNVERIFIABLE_SIGNATURE_BASELINE)
        )  # Add arg gaps.
        return tuple(messages)  # Freeze the result so assertions cannot change it.

    def _missing_messages(self) -> Iterable[str]:
        for site in self.missing_call_sites:  # Report each missing SDK function with its caller.
            location = f"{site.path.as_posix()}:{site.line}"  # Build a portable location for Windows and Linux.
            yield f"FAIL {location}: missing mistapi.{site.function}"  # Name the exact broken surface.

    def failure_messages_for_unresolved_baseline(self, baseline: int) -> tuple[str, ...]:
        """Return the failure when dynamic SDK references exceed the baseline."""
        if self.unresolved_count <= baseline:  # Existing dynamic module references stay visible but nonblocking.
            return ()  # Keep the guard useful until each dynamic path receives a direct contract.
        return (
            f"FAIL unresolved mistapi call sites grew to {self.unresolved_count}. Baseline is {baseline}",
        )  # Block new unmeasured SDK paths so the guard coverage cannot shrink silently.

    def failure_messages_for_unverifiable_baseline(self, baseline: int) -> tuple[str, ...]:
        """Return the failure when dynamic SDK argument calls exceed the baseline."""
        if self.unverifiable_count <= baseline:  # Existing dynamic calls stay visible while new gaps fail.
            return ()  # Avoid blocking known safe work because a static check cannot inspect runtime dictionaries.
        return (
            f"FAIL unverifiable mistapi call signatures grew to {self.unverifiable_count}. Baseline is {baseline}",
        )  # Block new unmeasured signature paths so coverage cannot shrink silently.

    def summary(self) -> str:
        """Return a compact measured-work line for pull request evidence."""
        checked = f"Checked mistapi call signatures: {self.checked_count}."  # Keep signature checks visible.
        unresolved = f"Unresolved mistapi call sites: {self.unresolved_count}."  # Keep unnamed paths visible.
        unverifiable = f"Unverifiable mistapi call signatures: {self.unverifiable_count}."  # Keep gaps visible.
        known = (
            f"Known mistapi signature failures: {len(self.known_signature_messages)}."  # Keep filed defects visible.
        )
        resolved = f"Resolved mistapi function names: {self.resolved_count}."  # Keep legacy name coverage visible.
        return " ".join((checked, unresolved, unverifiable, known, resolved))  # Join all measurements for CI logs.

    @property
    def known_signature_messages(self) -> tuple[str, ...]:
        """Return signature failures that this guard documents as separate issues."""
        return tuple(
            message for message in self.signature_messages if self._is_known_signature_failure(message)
        )  # Filter.

    @property
    def unexpected_signature_messages(self) -> tuple[str, ...]:
        """Return signature failures that are not in the recorded baseline."""
        return tuple(
            message for message in self.signature_messages if not self._is_known_signature_failure(message)
        )  # Filter.

    def _is_known_signature_failure(self, message: str) -> bool:
        return any(
            all(part in message for part in parts) for parts in KNOWN_SIGNATURE_FAILURES
        )  # Match exact baselines.

    def _can_check_signature(self, site: MistapiCallSite) -> bool:
        has_signature = site.function in self.sdk_signatures  # Only installed functions can receive signature checks.
        has_static_args = not site.arguments.has_dynamic_arguments  # Dynamic star arguments make a static proof unsafe.
        return has_signature and has_static_args and site.source == "attribute"  # Registry entries are declarations.

    def _cannot_check_signature(self, site: MistapiCallSite) -> bool:
        has_signature = site.function in self.sdk_signatures  # Missing functions fail through the missing path.
        dynamic_args = site.arguments.has_dynamic_arguments  # Dynamic arguments prevent complete static checks.
        return has_signature and (dynamic_args or site.source != "attribute")  # Count each known unverified call shape.


class MistapiSignatureComparator:
    """Compare one MistHelper call site against one SDK signature."""

    def __init__(self, site: MistapiCallSite, signature: MistapiSdkSignature) -> None:
        self.site = site  # Store the call site so failure messages name the caller.
        self.signature = signature  # Store the SDK signature that defines allowed arguments.

    def messages(self) -> tuple[str, ...]:
        """Return all compatibility failures for one call site."""
        logging.info("Checking signature for mistapi.%s", self.site.function)  # Log before the comparison.
        messages = [*self._missing_required(), *self._unexpected_keywords()]  # Compare required and named arguments.
        messages.extend(self._too_many_positionals())  # Add positional arity failures after named argument failures.
        logging.debug("Signature check found %d issue(s)", len(messages))  # Log the comparison result.
        return tuple(messages)  # Freeze the result for deterministic assertions.

    def _missing_required(self) -> tuple[str, ...]:
        provided = self._provided_names()  # Convert positional arguments to the parameter names they fill.
        missing = [name for name in self._required_names() if name not in provided]  # Find required gaps.
        return tuple(self._message("omits required parameter", name) for name in missing)  # Report each missing name.

    def _unexpected_keywords(self) -> tuple[str, ...]:
        if self.signature.accepts_kwargs:  # ``**kwargs`` in the SDK signature accepts arbitrary keywords.
            return ()  # Do not reject keywords that the SDK explicitly accepts dynamically.
        extra = [
            name for name in self.site.arguments.keywords if name not in self.signature.accepted_keywords
        ]  # Find drops.
        return tuple(self._message("passes unsupported parameter", name) for name in extra)  # Report each old keyword.

    def _too_many_positionals(self) -> tuple[str, ...]:
        if self.signature.accepts_varargs:  # ``*args`` in the SDK signature accepts arbitrary positional arguments.
            return ()  # Do not reject positional count when the SDK allows it dynamically.
        capacity = len(self.signature.positional_parameters)  # Count declared positional capacity.
        if self.site.arguments.positional_count <= capacity:  # The call fits the installed positional surface.
            return ()  # No arity failure exists.
        detail = f"{self.site.arguments.positional_count} positional arguments but accepts {capacity}"  # Explain arity.
        return (f"FAIL {self._location()}: passes {detail} to mistapi.{self.site.function}",)  # Report arity.

    def _provided_names(self) -> set[str]:
        positional_names = self.signature.positional_parameters[
            : self.site.arguments.positional_count
        ]  # Map positions.
        return {*positional_names, *self.site.arguments.keywords}  # Combine positional and keyword coverage.

    def _required_names(self) -> tuple[str, ...]:
        return (*self.signature.required_positional, *self.signature.required_keyword_only)  # Preserve signature order.

    def _message(self, reason: str, parameter: str) -> str:
        return f"FAIL {self._location()}: {reason} '{parameter}' for mistapi.{self.site.function}"  # Name the fault.

    def _location(self) -> str:
        return f"{self.site.path.as_posix()}:{self.site.line}"  # Build a portable location for Windows and Linux.


class MistapiSdkSurfaceCollector:
    """Collect callable signatures that the installed ``mistapi`` package defines."""

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

    def collect(self) -> Mapping[str, MistapiSdkSignature]:
        """Return public callable signatures from the installed SDK."""
        logging.info("Collecting mistapi SDK signatures from %s", self.package_root)  # Log before reading SDK files.
        signatures: dict[str, MistapiSdkSignature] = {}  # Store direct signatures by package-relative name.
        re_exports: list[tuple[str, str]] = []  # Store aliases until all direct signatures exist.
        for path in sorted(self.package_root.rglob("*.py")):  # Walk each installed SDK module once.
            self._add_path_symbols(path, signatures, re_exports)  # Add module definitions and re-export edges.
        self._add_re_export_signatures(signatures, re_exports)  # Copy signatures to aliases such as mistapi.get_all.
        logging.debug("Collected %d mistapi SDK signature(s)", len(signatures))  # Prove the SDK scan read data.
        return signatures  # Return a mapping so callers can read signatures by function path.

    def _add_path_symbols(
        self,
        path: Path,
        signatures: dict[str, MistapiSdkSignature],
        re_exports: list[tuple[str, str]],
    ) -> None:
        relative_module = self._module_name(path)  # Convert the SDK path to a dotted module path.
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))  # Parse the SDK file safely.
        signatures.update(self._top_level_signatures(tree, relative_module))  # Add direct function definitions.
        re_exports.extend(self._re_exported_callables(tree, relative_module))  # Add aliases exposed from package files.

    def _module_name(self, path: Path) -> str:
        parts = (
            path.relative_to(self.package_root).with_suffix("").parts
        )  # Preserve package nesting from the file path.
        clean_parts = parts[:-1] if parts[-1] == "__init__" else parts  # Treat package __init__ as the package itself.
        return ".".join(clean_parts)  # Return a path relative to ``mistapi``.

    def _top_level_signatures(self, tree: ast.Module, module_name: str) -> dict[str, MistapiSdkSignature]:
        signatures: dict[str, MistapiSdkSignature] = {}  # Collect callable signatures defined in this module.
        for node in tree.body:  # Read only module-level definitions because SDK calls target module attributes.
            if isinstance(
                node, ast.FunctionDef | ast.AsyncFunctionDef
            ):  # SDK functions are the call surface to verify.
                name = self._join_name(module_name, node.name)  # Build the callable path without the package prefix.
                signatures[name] = self._signature_from_arguments(node.args)  # Store the installed signature.
            if isinstance(node, ast.ClassDef):  # Constructors are callable but the guard does not inspect class bodies.
                name = self._join_name(module_name, node.name)  # Build the class path without the package prefix.
                signatures[name] = MistapiSdkSignature((), (), (), frozenset(), (True, True))  # Accept constructors.
        return signatures  # Return direct public and private definitions for exact resolution.

    def _signature_from_arguments(self, arguments: ast.arguments) -> MistapiSdkSignature:
        positional_args = (*arguments.posonlyargs, *arguments.args)  # Combine both positional-capable parameter groups.
        positional = tuple(arg.arg for arg in positional_args)  # Store names instead of AST nodes for comparisons.
        defaults_offset = len(positional_args) - len(
            arguments.defaults
        )  # Defaults apply to the right side of positions.
        required_positional = tuple(arg.arg for arg in positional_args[:defaults_offset])  # Keep required positions.
        keyword_only = zip(arguments.kwonlyargs, arguments.kw_defaults, strict=True)  # Pair each keyword-only default.
        required_keyword_only = tuple(
            arg.arg for arg, default in keyword_only if default is None
        )  # Keep required only.
        accepted_keywords = frozenset(
            arg.arg for arg in (*arguments.args, *arguments.kwonlyargs)
        )  # Exclude pos-only names.
        accepts_dynamic = (
            arguments.vararg is not None,
            arguments.kwarg is not None,
        )  # Preserve flexible SDK parameters.
        return MistapiSdkSignature(
            positional, required_positional, required_keyword_only, accepted_keywords, accepts_dynamic
        )

    def _re_exported_callables(self, tree: ast.Module, module_name: str) -> list[tuple[str, str]]:
        names: list[tuple[str, str]] = []  # Collect aliases created by package imports.
        for node in tree.body:  # Read import statements without importing SDK modules.
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("mistapi"):
                names.extend(self._aliases_from_import(node, module_name))  # Add aliases exposed from this package.
        return names  # Return aliases such as ``get_all`` from package ``__init__``.

    def _aliases_from_import(self, node: ast.ImportFrom, module_name: str) -> list[tuple[str, str]]:
        names: list[tuple[str, str]] = []  # Collect re-exported names from one import line.
        for alias in node.names:  # Each alias can expose one callable at the current package level.
            exposed_name = alias.asname or alias.name  # Use the public alias when the import defines one.
            if not exposed_name.startswith("_"):  # Ignore private helper aliases that callers should not use.
                target = self._strip_prefix(f"{node.module}.{alias.name}")  # Store the imported SDK target.
                names.append((self._join_name(module_name, exposed_name), target))  # Add the public alias path.
        return names  # Return aliases from this import statement.

    def _add_re_export_signatures(
        self,
        signatures: dict[str, MistapiSdkSignature],
        re_exports: Sequence[tuple[str, str]],
    ) -> None:
        for exposed, target in re_exports:  # Each edge can copy a direct signature to its public alias.
            if target in signatures and exposed not in signatures:  # Copy only when the target is a known function.
                signatures[exposed] = signatures[target]  # Give callers of the alias the same signature guard.

    def _join_name(self, module_name: str, callable_name: str) -> str:
        return f"{module_name}.{callable_name}" if module_name else callable_name  # Keep root exports short.

    def _strip_prefix(self, value: str) -> str:
        return value.removeprefix("mistapi.")  # Compare names relative to the package root.


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
        self._visit_scoped_body(node)  # Function bodies can add local Mist SDK aliases.

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_scoped_body(node)  # Async function bodies use the same alias scope rule.

    def _visit_scoped_body(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self._aliases.append(dict(self._aliases[-1]))  # Give the function a local copy of known aliases.
        self.generic_visit(node)  # Scan calls and local imports inside the function body.
        self._aliases.pop()  # Restore the outer alias map after the function body.

    def visit_Call(self, node: ast.Call) -> None:
        direct_function = self._call_function(node.func)  # Resolve a normal callable expression when possible.
        if direct_function is not None:  # Direct calls have a function name that the guard can check.
            call_arguments = self._call_arguments(node)  # Store static arguments for signature comparison.
            self.call_sites.append(
                MistapiCallSite(self.path, node.lineno, direct_function, "attribute", call_arguments)
            )  # Save it.
        registry_function = self._registry_call_function(
            node
        )  # Resolve string registry entries such as _SimpleEndpointOp.
        if registry_function is not None:  # Registry entries also name a concrete SDK function.
            self.call_sites.append(MistapiCallSite(self.path, node.lineno, registry_function, "registry"))  # Save it.
        unresolved = self._unresolved_dynamic_import(node)  # Detect an import_module string with no static function.
        if unresolved is not None:  # The guard cannot prove which function the module string calls.
            self.unresolved_call_sites.append(unresolved)  # Make the unmeasured site visible in the report.
        self.generic_visit(node)  # Continue into call arguments for nested SDK calls.

    def _call_arguments(self, node: ast.Call) -> MistapiCallArguments:
        positional_count = sum(1 for arg in node.args if not isinstance(arg, ast.Starred))  # Count static positions.
        keywords = tuple(keyword.arg for keyword in node.keywords if keyword.arg is not None)  # Store named arguments.
        has_starargs = any(isinstance(arg, ast.Starred) for arg in node.args)  # Flag dynamic positional expansion.
        has_kwargs = any(keyword.arg is None for keyword in node.keywords)  # Flag dynamic keyword expansion.
        return MistapiCallArguments(
            positional_count, keywords, has_starargs, has_kwargs
        )  # Return static argument facts.

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
        sdk_signatures = (
            MistapiSdkSurfaceCollector.from_installed_package().collect()
        )  # Read the installed SDK surface.
        sources = self._project_sources()  # Read the project files that can call the SDK.
        report = self.evaluate_sources(sources, sdk_signatures)  # Compare source call sites to SDK definitions.
        logging.debug("%s", report.summary())  # Record the count that proves this guard measured call sites.
        return report  # Return the report so tests can enforce failure rules.

    def evaluate_sources(
        self, sources: Mapping[Path, str], sdk_signatures: Mapping[str, MistapiSdkSignature]
    ) -> MistapiGuardReport:
        """Evaluate supplied project sources against supplied SDK signatures."""
        logging.info("Evaluating %d source file(s) for mistapi call sites", len(sources))  # Log the input size.
        resolved: list[MistapiCallSite] = []  # Collect all statically resolved SDK calls.
        unresolved: list[MistapiCallSite] = []  # Collect all dynamic SDK module references.
        for path, source in sources.items():  # Analyze each source independently for precise file names.
            file_resolved, file_unresolved = MistapiSourceCallCollector(path, source).collect()  # Scan one file.
            resolved.extend(file_resolved)  # Add resolved calls to the report input.
            unresolved.extend(file_unresolved)  # Add unresolved calls so they remain visible.
        logging.debug("Evaluation resolved %d call site(s)", len(resolved))  # Log the measured static coverage.
        return MistapiGuardReport(tuple(resolved), tuple(unresolved), sdk_signatures)  # Build the report.

    def _project_sources(self) -> dict[Path, str]:
        source_paths = [
            self.root / "MistHelper.py",
            *sorted((self.root / "src").rglob("*.py")),
        ]  # Scan app sources only.
        return {path.relative_to(self.root): path.read_text(encoding="utf-8") for path in source_paths}  # Read once.


def test_installed_mistapi_surface_covers_source_calls(capsys: CaptureFixture[str]) -> None:
    guard = MistapiSdkCompatibilityGuard(REPO_ROOT)  # Use the checkout under test as the source of call sites.
    report = guard.evaluate_installed_sdk()  # Compare the source calls to the installed SDK.
    with capsys.disabled():  # Print the measurement even when pytest captures normal output.
        print(report.summary())  # Show the checked call-site count in every local and CI run.
    assert report.checked_count > 0, report.summary()  # Fail if the guard measured no SDK call signature.
    assert not report.failure_messages, "\n".join(report.failure_messages)  # Fail with caller and missing function.


def _sdk_signature(*required_names: str) -> MistapiSdkSignature:
    positional = tuple(required_names)  # Use the fixture names as positional-capable SDK parameters.
    keywords = frozenset(required_names)  # Use the same names as legal keywords for simple fixtures.
    return MistapiSdkSignature(positional, positional, (), keywords)  # Build a compact signature fixture.


def test_guard_fails_for_deliberately_missing_sdk_function() -> None:
    fixture_path = Path("tests/integration/test_mistapi_sdk_compatibility.py")  # Use a real file for citation lint.
    source = (  # Keep the fixture readable while it models two call sites.
        "import mistapi\n"
        "mistapi.api.v1.orgs.fake.missingFunction()\n"
        "mistapi.api.v1.orgs.sites.listOrgSites(apisession)\n"
    )
    sources = {fixture_path: source}  # Provide one broken call and one measured call.
    signatures = {"api.v1.orgs.sites.listOrgSites": _sdk_signature("apisession")}  # Provide one valid SDK function.
    report = MistapiSdkCompatibilityGuard(REPO_ROOT).evaluate_sources(sources, signatures)  # Check it.
    assert report.checked_count == 1  # Prove the test measured one valid call beside the broken call.
    assert report.failure_messages == (
        f"FAIL {fixture_path.as_posix()}:2: missing mistapi.api.v1.orgs.fake.missingFunction",
    )  # Prove failure.


def test_guard_fails_when_required_parameter_is_omitted() -> None:
    fixture_path = Path("tests/integration/test_mistapi_sdk_compatibility.py")  # Use a real file for citation lint.
    source = "import mistapi\nmistapi.device_utils.ex_remote_pcap(apisession, site_id)\n"  # Model the new SDK call.
    signatures = {
        "device_utils.ex_remote_pcap": _sdk_signature("apisession", "site_id", "device_interfaces")
    }  # Require it.
    report = MistapiSdkCompatibilityGuard(REPO_ROOT).evaluate_sources({fixture_path: source}, signatures)  # Check it.
    assert report.checked_count == 1  # Prove the fixture received a signature check.
    expected = (
        "FAIL tests/integration/test_mistapi_sdk_compatibility.py:2: "
        "omits required parameter 'device_interfaces' for mistapi.device_utils.ex_remote_pcap"
    )  # Build the expected message without a long source line.
    assert report.failure_messages == (expected,)  # Prove the required-parameter failure.


def test_guard_fails_when_removed_parameter_is_passed() -> None:
    fixture_path = Path("tests/integration/test_mistapi_sdk_compatibility.py")  # Use a real file for citation lint.
    source = (  # Model old keywords from the pre-0.64.0 remote capture helper.
        "import mistapi\n"
        "mistapi.device_utils.srx_remote_pcap("
        "apisession, site_id, device_id=device_id, port_ids=port_ids)\n"
    )
    signatures = {
        "device_utils.srx_remote_pcap": _sdk_signature("apisession", "site_id", "device_interfaces")
    }  # Drop names.
    report = MistapiSdkCompatibilityGuard(REPO_ROOT).evaluate_sources({fixture_path: source}, signatures)  # Check it.
    assert report.checked_count == 1  # Prove the fixture received a signature check.
    device_id_message = (
        "FAIL tests/integration/test_mistapi_sdk_compatibility.py:2: "
        "passes unsupported parameter 'device_id' for mistapi.device_utils.srx_remote_pcap"
    )  # Build the expected message for the removed device keyword.
    port_ids_message = (
        "FAIL tests/integration/test_mistapi_sdk_compatibility.py:2: "
        "passes unsupported parameter 'port_ids' for mistapi.device_utils.srx_remote_pcap"
    )  # Build the expected message for the removed port keyword.
    assert device_id_message in report.failure_messages  # Prove one removed keyword fails.
    assert port_ids_message in report.failure_messages  # Prove the other removed keyword fails.


def test_guard_fails_when_zero_call_sites_resolve() -> None:
    sources = {Path("src/example.py"): "VALUE = 1\n"}  # This source has no Mist SDK call site.
    signatures = {"api.v1.orgs.sites.listOrgSites": _sdk_signature("apisession")}  # Provide one valid SDK function.
    report = MistapiSdkCompatibilityGuard(REPO_ROOT).evaluate_sources(sources, signatures)  # Check it.
    assert report.checked_count == 0  # Confirm the fixture exercises the zero-measurement path.
    assert report.failure_messages == (
        "FAIL checked mistapi call signatures: 0",
    )  # Prove the guard fails when it measures zero.


def test_guard_reports_unresolved_dynamic_module_imports() -> None:
    sources = {
        Path("src/example.py"): "from importlib import import_module\nmodule = import_module(name)\n"
    }  # Not a Mist path.
    mist_sources = {
        Path("src/mist.py"): "from importlib import import_module\nmodule = import_module('mistapi.api.v1.self.self')\n"
    }  # Mist module only.
    signatures = {"api.v1.self.self.getSelf": _sdk_signature("apisession")}  # Provide a valid SDK function.
    report = MistapiSdkCompatibilityGuard(REPO_ROOT).evaluate_sources(sources | mist_sources, signatures)  # Check it.
    assert report.unresolved_count == 1  # Make the unmeasured dynamic module reference visible.
    assert report.unresolved_call_sites[0].function == "api.v1.self.self"  # Name the module that needs a function.


def test_guard_fails_when_unresolved_call_sites_exceed_baseline() -> None:
    sources = {
        Path("src/mist.py"): "from importlib import import_module\nmodule = import_module('mistapi.api.v1.self.self')\n"
    }  # One dynamic module exceeds the zero baseline used by this test.
    signatures = {"api.v1.self.self.getSelf": _sdk_signature("apisession")}  # Provide a valid SDK function.
    report = MistapiSdkCompatibilityGuard(REPO_ROOT).evaluate_sources(
        sources, signatures
    )  # Evaluate a dynamic module path.
    assert report.unresolved_count == 1  # Confirm the test measures one unresolvable SDK path.
    assert "FAIL unresolved mistapi call sites grew to 1. Baseline is 0" in tuple(
        report.failure_messages_for_unresolved_baseline(0)
    )  # Prove a baseline increase blocks the guard.


def test_guard_fails_when_unverifiable_call_sites_exceed_baseline() -> None:
    source = (  # Model runtime-built arguments that static analysis cannot prove.
        "import mistapi\n"
        "kwargs = {'device_interfaces': []}\n"
        "mistapi.device_utils.ssr_remote_pcap(apisession, site_id, **kwargs)\n"
    )
    signatures = {
        "device_utils.ssr_remote_pcap": _sdk_signature("apisession", "site_id", "device_interfaces")
    }  # Require it.
    report = MistapiSdkCompatibilityGuard(REPO_ROOT).evaluate_sources(
        {Path("src/mist.py"): source}, signatures
    )  # Check it.
    assert report.unverifiable_count == 1  # Confirm the dynamic keyword path is counted.
    assert "FAIL unverifiable mistapi call signatures grew to 1. Baseline is 0" in tuple(
        report.failure_messages_for_unverifiable_baseline(0)
    )  # Prove growth fails.
