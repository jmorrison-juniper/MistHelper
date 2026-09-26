"""The index of the MistHelper source tree.

The index parses ``MistHelper.py`` and every module below ``src/``. It records
each module, each function, each class, and each module or class constant. It
also records the import map of each module and of each function, because a
local import inside a function is visible only inside that function.
"""

from __future__ import annotations  # Postponed annotations keep the type hints light.

import ast  # Parses each source file.
import logging  # Records each file action for the operator.
from collections import defaultdict  # Groups the keys by their simple name.
from collections.abc import Mapping  # Types the read-only import map of a scope.
from dataclasses import dataclass, field  # Holds the index entries as small values.
from pathlib import Path  # Builds the portable source paths.

LOGGER = logging.getLogger(__name__)  # Keeps the log records tied to this module.

ROUTE_DECORATORS = frozenset({"route", "get", "post", "put", "delete", "patch", "callback"})  # Flask and Dash names.
SCOPE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)  # The nodes that open a new import scope.


class AstNames:
    """Read dotted names and bodies from AST nodes."""

    @staticmethod
    def dotted(node: ast.AST) -> list[str] | None:
        """Return the parts of a dotted name, such as ["self", "cache", "load"], or None."""
        parts: list[str] = []  # Collects the attribute names from right to left.
        while isinstance(node, ast.Attribute):  # Walk down the attribute chain.
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):  # The chain starts at a plain name.
            parts.append(node.id)
            return list(reversed(parts))  # The parts from left to right.
        return None  # The chain starts at a call or another expression.

    @staticmethod
    def loose_parts(node: ast.AST) -> list[str] | None:
        """Return the parts of an attribute chain, with "<expr>" for a head that is not a name."""
        parts: list[str] = []  # Collects the attribute names from right to left.
        while isinstance(node, ast.Attribute):  # Walk down the attribute chain.
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):  # The chain starts at a plain name.
            parts.append(node.id)
        elif not parts:  # The node is not a chain at all.
            return None
        else:  # The chain starts at a call, such as _pc().mistapi.api.
            parts.append("<expr>")
        return list(reversed(parts))  # The parts from left to right.

    @staticmethod
    def body_without_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
        """Return a function body without its docstring, so the docstring text adds no finding."""
        first = body[0] if body else None  # The docstring is always the first statement.
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            return body[1:]  # Skip the docstring.
        return body  # The body has no docstring.


@dataclass
class ModuleInfo:
    """One parsed source module and its top-level import map."""

    name: str  # The dotted module name, such as src.export.site_exporter.
    path: Path  # The absolute file path.
    relative: str  # The repository path with forward slashes, such as src/export/site_exporter.py.
    tree: ast.Module  # The parsed module.
    package: str  # The package that a relative import starts from.
    imports: dict[str, str] = field(default_factory=dict)  # The top-level local name to its dotted target.


@dataclass(frozen=True)
class ScopeView:
    """The names that one scope can see: the module, and the import map of the scope."""

    module: ModuleInfo  # The module that holds the scope.
    imports: Mapping[str, str]  # The module imports plus the local imports of the scope.

    @property
    def name(self) -> str:
        """Return the dotted name of the module."""
        return self.module.name  # The module name is the same for every scope in it.


@dataclass(frozen=True)
class FunctionEntry:
    """One function or method in the index."""

    key: str  # The key, such as src.export.site_exporter:SiteExporter.export.
    module: ModuleInfo  # The module that holds the function.
    node: ast.FunctionDef | ast.AsyncFunctionDef  # The function definition.
    class_key: str | None  # The key of the owner class, or None for a module function.


@dataclass(frozen=True)
class ClassEntry:
    """One class in the index."""

    key: str  # The key, such as src.export.site_exporter:SiteExporter.
    module: ModuleInfo  # The module that holds the class.
    node: ast.ClassDef  # The class definition.


@dataclass(frozen=True)
class ConstantEntry:
    """One module constant or class constant in the index."""

    key: str  # The key, such as src.upgrade_portal.app.routes:bp.
    module: ModuleInfo  # The module that holds the constant.
    value: ast.expr  # The assigned expression.


class SourceIndex:
    """Parse the source tree and index each module, function, class, and constant."""

    def __init__(self, repo_root: Path) -> None:
        """Prepare the empty tables for one repository."""
        self.repo_root = repo_root  # The folder that holds MistHelper.py.
        self.modules: dict[str, ModuleInfo] = {}  # Dotted module name to its module.
        self.functions: dict[str, FunctionEntry] = {}  # Function key to its entry.
        self.classes: dict[str, ClassEntry] = {}  # Class key to its entry.
        self.constants: dict[str, ConstantEntry] = {}  # Constant key to its entry.
        self.route_handlers: dict[str, list[str]] = defaultdict(list)  # Blueprint key to its route functions.
        self.class_by_simple: dict[str, list[str]] = defaultdict(list)  # Class name to its keys.
        self.func_by_simple: dict[str, list[str]] = defaultdict(list)  # Function name to its keys.
        self.alias_classes: dict[str, set[str]] = defaultdict(set)  # Import alias to the classes it names.
        self._local_imports: dict[int, dict[str, str]] = {}  # Scope node id to its local import map.
        self._parents: dict[int, ast.AST | None] = {}  # Scope node id to its enclosing scope node.
        self._views: dict[int, ScopeView] = {}  # Scope node id to its cached view.
        self._module_views: dict[str, ScopeView] = {}  # Module name to its cached module view.

    def build(self) -> SourceIndex:
        """Parse every source file and fill the tables."""
        LOGGER.info("Indexing the source tree below %s", self.repo_root)  # Log before the file walk.
        for path in self.source_files():  # Parse the files in a stable order.
            self.parse_file(path)
        for module in self.modules.values():  # Record the imports of each scope.
            self.walk_scopes(module, module.tree, None)
        for module in self.modules.values():  # Record the definitions of each module.
            self.index_body(module, module.tree.body, "", None)
        self.index_aliases()  # Record the classes that an import alias names.
        LOGGER.debug(
            "Indexed %d modules, %d functions, and %d classes",
            len(self.modules),
            len(self.functions),
            len(self.classes),
        )
        return self  # The caller chains the build call.

    def source_files(self) -> list[Path]:
        """Return MistHelper.py and every module below src/, in a stable order on every platform."""
        files = [path for path in (self.repo_root / "src").rglob("*.py") if "__pycache__" not in path.parts]
        files.sort(key=lambda path: path.relative_to(self.repo_root).as_posix())  # A case-sensitive order.
        return [self.repo_root / "MistHelper.py", *files]  # The entry point first.

    def parse_file(self, path: Path) -> None:
        """Parse one source file and add its module to the table."""
        relative = path.relative_to(self.repo_root).as_posix()  # The repository path with forward slashes.
        parts = relative.removesuffix(".py").split("/")  # The dotted name parts.
        is_package = parts[-1] == "__init__"  # A package file names its folder.
        name = ".".join(parts[:-1] if is_package else parts)  # The dotted module name.
        try:  # A file with a syntax error must not stop the whole map.
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as error:  # Report the file and keep the other modules.
            LOGGER.warning("Skipped %s because it does not parse: %s", relative, error)
            return
        package = name if is_package else name.rpartition(".")[0]  # The start of a relative import.
        self.modules[name] = ModuleInfo(name, path, relative, tree, package)  # Add the module.

    def walk_scopes(self, module: ModuleInfo, node: ast.AST, current: ast.AST | None) -> None:
        """Record the import map of each scope and the parent of each nested scope."""
        for child in ast.iter_child_nodes(node):  # Visit the direct children.
            if isinstance(child, SCOPE_NODES):  # A new function scope starts here.
                self._parents[id(child)] = current  # Remember the enclosing scope.
                self.walk_scopes(module, child, child)  # The child scope holds its own imports.
            elif isinstance(child, (ast.Import, ast.ImportFrom)):  # An import binds names in this scope.
                target = module.imports if current is None else self._local_imports.setdefault(id(current), {})
                self.record_import(target, child, module.package)  # Add the bound names.
            else:  # Any other statement or expression stays in the same scope.
                self.walk_scopes(module, child, current)

    @staticmethod
    def record_import(target: dict[str, str], node: ast.Import | ast.ImportFrom, package: str) -> None:
        """Add the names that one import statement binds to an import map."""
        if isinstance(node, ast.Import):  # For example: import mistapi.api.v1.orgs as orgs_api.
            for alias in node.names:  # Each alias binds one name.
                if alias.asname:  # An alias binds the full dotted target.
                    target[alias.asname] = alias.name
                else:  # A plain import binds the first dotted part only.
                    top = alias.name.split(".")[0]  # For example mistapi for mistapi.api.v1.orgs.
                    target.setdefault(top, top)  # An earlier alias for the same name wins.
            return
        base = node.module or ""  # For example: from .helpers import x.
        if node.level:  # A relative import starts from the package of the module.
            anchor = package.split(".") if package else []  # The package parts.
            anchor = anchor[: len(anchor) - (node.level - 1)] if node.level > 1 else anchor  # Walk up the levels.
            base = ".".join([*anchor, base] if base else anchor)  # The absolute base module.
        for alias in node.names:  # Each alias binds one name.
            target[alias.asname or alias.name] = f"{base}.{alias.name}" if base else alias.name

    def index_body(self, module: ModuleInfo, body: list[ast.stmt], prefix: str, class_key: str | None) -> None:
        """Add the functions, the classes, and the constants of one module body or class body."""
        for node in body:  # Visit each top-level statement.
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):  # A function or a method.
                self.add_function(module, node, prefix, class_key)
            elif isinstance(node, ast.ClassDef):  # A class, which can hold methods and nested classes.
                key = f"{module.name}:{prefix}{node.name}"  # The class key.
                self.classes[key] = ClassEntry(key, module, node)  # Add the class.
                self.class_by_simple[node.name].append(key)  # Index the class by its name.
                self.index_body(module, node.body, f"{prefix}{node.name}.", key)  # Add the members.
            elif isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:  # A constant.
                self.add_constants(module, node, prefix)

    def add_function(
        self, module: ModuleInfo, node: ast.FunctionDef | ast.AsyncFunctionDef, prefix: str, class_key: str | None
    ) -> None:
        """Add one function, and record it as a route handler when a route decorator names it."""
        key = f"{module.name}:{prefix}{node.name}"  # The function key.
        self.functions[key] = FunctionEntry(key, module, node, class_key)  # Add the function.
        self.func_by_simple[node.name].append(key)  # Index the function by its name.
        for decorator in node.decorator_list:  # For example: @bp.route("/runs").
            if not (isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)):
                continue  # A decorator without a call names no route.
            owner = decorator.func.value  # The blueprint or the application.
            if decorator.func.attr in ROUTE_DECORATORS and isinstance(owner, ast.Name):  # A route decorator.
                self.route_handlers[f"{module.name}:{owner.id}"].append(key)  # The constant owns the route.

    def add_constants(self, module: ModuleInfo, node: ast.Assign | ast.AnnAssign, prefix: str) -> None:
        """Add each plain name that one assignment binds."""
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]  # The assigned names.
        for target in targets:  # Each plain name becomes one constant.
            if isinstance(target, ast.Name) and node.value is not None:  # Skip a tuple or an attribute target.
                key = f"{module.name}:{prefix}{target.id}"  # The constant key.
                self.constants[key] = ConstantEntry(key, module, node.value)  # Add the constant.

    def index_aliases(self) -> None:
        """Record each import alias that names a class under another name."""
        import_maps = [module.imports for module in self.modules.values()] + list(self._local_imports.values())
        for import_map in import_maps:  # Every module map and every local map.
            for alias, target in import_map.items():  # Each bound name.
                module_part, _, attribute = target.rpartition(".")  # Split the module and the name.
                key = f"{module_part}:{attribute}"  # The class key when the target is a class.
                if alias != attribute and key in self.classes:  # An alias such as "as Exporter".
                    self.alias_classes[alias].add(key)

    def defines(self, key: str | None) -> bool:
        """Return True when the key names a function, a class, or a constant."""
        return bool(key) and (key in self.functions or key in self.classes or key in self.constants)

    def module_view(self, module: ModuleInfo) -> ScopeView:
        """Return the view of the module scope."""
        view = self._module_views.get(module.name)  # The cached view.
        if view is None:  # The first request for this module.
            view = ScopeView(module, module.imports)  # The module scope sees the module imports only.
            self._module_views[module.name] = view  # Keep it for the next request.
        return view

    def scope_view(self, module: ModuleInfo, scope: ast.AST | None) -> ScopeView:
        """Return the view of one function scope: the module imports plus the local imports."""
        if scope is None:  # The module scope.
            return self.module_view(module)
        view = self._views.get(id(scope))  # The cached view.
        if view is not None:  # The scope was seen before.
            return view
        local = self.local_imports_of(scope)  # The imports of the scope and of each enclosing scope.
        view = ScopeView(module, {**module.imports, **local}) if local else self.module_view(module)
        self._views[id(scope)] = view  # Keep it for the next request.
        return view

    def local_imports_of(self, scope: ast.AST) -> dict[str, str]:
        """Return the local imports that one scope sees, with the inner scope last."""
        chain: list[ast.AST] = []  # The scope and each enclosing scope, from inner to outer.
        current: ast.AST | None = scope  # Start at the scope itself.
        while current is not None:  # Walk out to the module scope.
            chain.append(current)
            current = self._parents.get(id(current))
        local: dict[str, str] = {}  # The merged import map.
        for node in reversed(chain):  # The outer scope first, so an inner import wins.
            local.update(self._local_imports.get(id(node), {}))
        return local

    def resolve_symbol(self, view: ScopeView, name: str) -> str | None:
        """Return the key that a plain name refers to in one scope.

        The result is a function, class, or constant key, or "module:<name>" for
        a project module, or "ext:<target>" for a name from another package.
        """
        local = f"{view.name}:{name}"  # A definition in the same module.
        if self.defines(local):  # The module defines the name.
            return local
        target = view.imports.get(name)  # The import that binds the name.
        return self.resolve_import_target(target) if target else None  # None for an unknown name.

    def resolve_import_target(self, target: str) -> str:
        """Return the key that an import target names."""
        module_part, _, attribute = target.rpartition(".")  # Split the module and the name.
        if module_part in self.modules:  # The target is a name in a project module.
            found = self.module_member(module_part, attribute)  # The definition or the re-export.
            if found:
                return found
        if target in self.modules:  # The target is a project module.
            return f"module:{target}"
        return f"ext:{target}"  # The target is in another package.

    def module_member(self, module_name: str, attribute: str) -> str | None:
        """Return the key of a module member, and follow one re-export through a package."""
        key = f"{module_name}:{attribute}"  # A definition in the module.
        if self.defines(key):
            return key
        reexport = self.modules[module_name].imports.get(attribute)  # A package __init__ re-export.
        if not reexport:  # The module does not bind the name.
            return None
        reexport_module, _, reexport_name = reexport.rpartition(".")  # The real home of the name.
        real = f"{reexport_module}:{reexport_name}"  # The key in the real home.
        return real if real in self.classes or real in self.functions else None
