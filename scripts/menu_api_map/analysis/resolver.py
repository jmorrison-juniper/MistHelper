"""The type resolver: find the project class of an expression and the target of a call.

The resolver reads the annotations, the constructor calls, the return types, and
the ``self.X = ...`` statements of the source tree. It uses these facts to find
the class of a receiver, and then the method that a call reaches.
"""

from __future__ import annotations  # Postponed annotations keep the type hints light.

import ast  # Reads the expression nodes.
from collections.abc import Callable  # Types the return type callback.
from dataclasses import dataclass, field  # Holds the facts of one scan.

from .source_index import AstNames, ClassEntry, ScopeView, SourceIndex  # The index that the resolver reads.

MAX_BASE_DEPTH = 8  # A deeper base-class chain is a cycle or an error.
RECEIVER_NAMES = ("self", "cls")  # The names of the receiver of a method.
TYPE_WRAPPERS = ("type", "Type", "Optional")  # Subscript heads that wrap one class.


@dataclass
class TypeContext:
    """The facts that one scan knows: the owner class and the class of each local name."""

    class_key: str | None  # The class that owns the scanned method, or None.
    var_types: dict[str, str] = field(default_factory=dict)  # Local name to its class key.


class TypeResolver:
    """Find the project class of an expression and the function that a call reaches."""

    def __init__(self, index: SourceIndex, generic_names: frozenset[str]) -> None:
        """Store the index and the names that the name fallback must skip."""
        self.index = index  # The source index.
        self.generic_names = generic_names  # Method names that match too many classes.
        self.return_types: Callable[[str], set[str]] = lambda key: set()  # The scan cache replaces this.
        self._bases: dict[str, list[str]] = {}  # Class key to its project base classes.
        self._attributes: dict[str, dict[str, str]] = {}  # Class key to its attribute classes.
        self._return_guard: set[str] = set()  # The functions whose return type is in progress.

    # ------------------------------------------------------------------ classes
    def class_bases(self, class_key: str) -> list[str]:
        """Return the project base classes of one class."""
        cached = self._bases.get(class_key)  # The cached answer.
        if cached is not None:
            return cached
        entry = self.index.classes[class_key]  # The class definition.
        view = self.index.module_view(entry.module)  # A base name resolves in the module scope.
        bases = [base for base in (self.base_class(view, node) for node in entry.node.bases) if base]
        self._bases[class_key] = bases  # Keep the answer.
        return bases

    def base_class(self, view: ScopeView, node: ast.expr) -> str | None:
        """Return the class key of one base-class expression, or None."""
        parts = AstNames.dotted(node)  # For example ["BaseExporter"] or ["base", "BaseExporter"].
        if not parts:  # A call or a subscript, such as Generic[T].
            return None
        target = self.index.resolve_symbol(view, parts[0]) if len(parts) == 1 else None  # An imported name.
        if target is None:  # Fall back to a unique class name.
            simple = self.index.class_by_simple.get(parts[-1], [])
            target = simple[0] if len(simple) == 1 else None
        return target if target in self.index.classes else None

    def class_member(self, class_key: str, member: str, depth: int = 0) -> str | None:
        """Return the key of a member of a class or of one of its base classes."""
        if depth > MAX_BASE_DEPTH or class_key not in self.index.classes:  # Stop at a cycle or a foreign class.
            return None
        candidate = f"{class_key}.{member}"  # The member in the class itself.
        if self.index.defines(candidate):
            return candidate
        for base in self.class_bases(class_key):  # Search the base classes in order.
            found = self.class_member(base, member, depth + 1)
            if found:
                return found
        return None

    def class_attr_types(self, class_key: str) -> dict[str, str]:
        """Return the class of each attribute that the class sets, with the base classes last."""
        cached = self._attributes.get(class_key)  # The cached answer.
        if cached is not None:  # An empty dictionary also stops a recursive request.
            return cached
        self._attributes[class_key] = {}  # Stop a recursive request for the same class.
        entry = self.index.classes[class_key]  # The class definition.
        found = self.annotated_attributes(entry)  # The class-level annotations first.
        for node in entry.node.body:  # Each method can set self attributes.
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.method_attributes(entry, node, found)
        for base in self.class_bases(class_key):  # A base class attribute applies too.
            for name, value in self.class_attr_types(base).items():
                found.setdefault(name, value)
        self._attributes[class_key] = found  # Keep the answer.
        return found

    def annotated_attributes(self, entry: ClassEntry) -> dict[str, str]:
        """Return the class of each class-level annotated attribute."""
        view = self.index.module_view(entry.module)  # An annotation resolves in the module scope.
        found: dict[str, str] = {}  # Attribute name to its class key.
        for node in entry.node.body:  # For example: cache: CacheUtils.
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                annotated = self.annotation_class(view, node.annotation)  # The class of the annotation.
                if annotated:
                    found[node.target.id] = annotated
        return found

    def method_attributes(
        self, entry: ClassEntry, method: ast.FunctionDef | ast.AsyncFunctionDef, found: dict[str, str]
    ) -> None:
        """Add the class of each self attribute that one method sets."""
        view = self.index.scope_view(entry.module, method)  # The method sees its local imports.
        arguments = [*method.args.args, *method.args.kwonlyargs]  # The parameters of the method.
        params = {argument.arg: self.annotation_class(view, argument.annotation) for argument in arguments}
        for node in ast.walk(method):  # Every assignment in the method body.
            attribute, value, annotation = self.self_assignment(node)  # The target and the value.
            if attribute is None:  # Not an assignment to a self attribute.
                continue
            assigned = self.annotation_class(view, annotation) if annotation is not None else None
            assigned = assigned or self.value_class(view, value, params, entry.key)  # The class of the value.
            if assigned:
                found.setdefault(attribute, assigned)  # The first assignment wins.

    @staticmethod
    def self_assignment(node: ast.AST) -> tuple[str | None, ast.expr | None, ast.expr | None]:
        """Return the attribute name, the value, and the annotation of a self assignment."""
        if isinstance(node, ast.Assign) and len(node.targets) == 1:  # For example: self.cache = CacheUtils().
            target, value, annotation = node.targets[0], node.value, None
        elif isinstance(node, ast.AnnAssign):  # For example: self.cache: CacheUtils = build().
            target, value, annotation = node.target, node.value, node.annotation
        else:  # Any other node sets no attribute.
            return None, None, None
        if not isinstance(target, ast.Attribute):  # Only an attribute target sets an attribute.
            return None, None, None
        receiver = target.value  # The object that receives the attribute.
        if isinstance(receiver, ast.Name) and receiver.id == "self":  # An assignment to self.X.
            return target.attr, value, annotation
        return None, None, None

    def value_class(
        self, view: ScopeView, value: ast.expr | None, params: dict[str, str | None], class_key: str
    ) -> str | None:
        """Return the class of an assigned value: a parameter, or the result of a call."""
        if isinstance(value, ast.Name):  # For example: self.cache = cache.
            return params.get(value.id)
        if isinstance(value, ast.Call):  # For example: self.cache = CacheUtils().
            return self.call_result_class(view, value, TypeContext(class_key))
        return None

    # ------------------------------------------------------------------ annotations
    def annotation_class(self, view: ScopeView, annotation: ast.expr | None) -> str | None:
        """Return the project class that an annotation names, or None."""
        node = self.parse_string_annotation(annotation)  # A forward reference is a string.
        if node is None:
            return None
        if isinstance(node, ast.BinOp):  # For example: CacheUtils | None.
            return self.annotation_class(view, node.left) or self.annotation_class(view, node.right)
        if isinstance(node, ast.Subscript):  # For example: type[CacheUtils] or Optional[CacheUtils].
            head = AstNames.dotted(node.value)  # The subscript head.
            return self.annotation_class(view, node.slice) if head and head[-1] in TYPE_WRAPPERS else None
        return self.plain_annotation_class(view, node)

    @staticmethod
    def parse_string_annotation(annotation: ast.expr | None) -> ast.expr | None:
        """Return the expression of a string annotation, or the annotation itself."""
        if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):  # A forward reference.
            try:  # A string annotation can hold any text.
                return ast.parse(annotation.value, mode="eval").body
            except SyntaxError:  # The text is not an expression.
                return None
        return annotation  # A plain expression, or None.

    def plain_annotation_class(self, view: ScopeView, node: ast.expr) -> str | None:
        """Return the project class that a plain or dotted annotation names."""
        parts = AstNames.dotted(node)  # For example ["CacheUtils"] or ["cache", "CacheUtils"].
        if not parts:
            return None
        if len(parts) == 1:  # A plain name resolves through the imports.
            target = self.index.resolve_symbol(view, parts[0])
            if target in self.index.classes:
                return target
        simple = self.index.class_by_simple.get(parts[-1], [])  # Fall back to a unique class name.
        return simple[0] if len(simple) == 1 else None

    # ------------------------------------------------------------------ expressions
    def expr_class(self, view: ScopeView, expr: ast.expr, context: TypeContext) -> str | None:
        """Return the project class of an expression, or None."""
        if isinstance(expr, ast.Call):  # For example: CacheUtils() or build_cache().
            return self.call_class(view, expr, context)
        if isinstance(expr, ast.Name):  # For example: cache or self.
            return self.name_class(view, expr, context)
        if isinstance(expr, ast.Attribute):  # For example: self.cache.
            return self.attribute_class(view, expr, context)
        return None

    def call_class(self, view: ScopeView, expr: ast.Call, context: TypeContext) -> str | None:
        """Return the class that a call expression produces."""
        is_own_type = isinstance(expr.func, ast.Name) and expr.func.id in ("type", "cls")  # type(self) or cls().
        if is_own_type and context.class_key:
            return context.class_key
        return self.call_result_class(view, expr, context)

    def name_class(self, view: ScopeView, expr: ast.Name, context: TypeContext) -> str | None:
        """Return the class of a plain name: a local name, the receiver, or an imported class."""
        if expr.id in context.var_types:  # A local name with a known class.
            return context.var_types[expr.id]
        if expr.id in RECEIVER_NAMES and context.class_key:  # The receiver of the method.
            return context.class_key
        target = self.index.resolve_symbol(view, expr.id)  # An imported or module-level class.
        return target if target in self.index.classes else None

    def attribute_class(self, view: ScopeView, expr: ast.Attribute, context: TypeContext) -> str | None:
        """Return the class of an attribute: a nested class, a typed attribute, or a dotted class."""
        owner = self.expr_class(view, expr.value, context)  # The class of the receiver.
        if owner:
            nested = f"{owner}.{expr.attr}"  # A nested class, such as Outer.Inner.
            return nested if nested in self.index.classes else self.class_attr_types(owner).get(expr.attr)
        parts = AstNames.dotted(expr)  # For example ["exporters", "SiteExporter"].
        if not parts:
            return None
        head = self.index.resolve_symbol(view, parts[0])  # The first part can name a project module.
        if head and head.startswith("module:"):  # For example: exporters.SiteExporter.
            key = f"{head.removeprefix('module:')}:{'.'.join(parts[1:])}"
            if key in self.index.classes:
                return key
        simple = self.index.class_by_simple.get(parts[-1], [])  # Fall back to a unique class name.
        return simple[0] if len(simple) == 1 else None

    def call_result_class(self, view: ScopeView, call: ast.Call, context: TypeContext) -> str | None:
        """Return the project class that a call produces, when static analysis can tell."""
        callee = self.resolve_callee(view, call.func, context, strict=True)  # The function or the class.
        if callee is None:
            return None
        if callee in self.index.classes:  # A constructor call.
            return callee
        return self.function_result_class(callee) if callee in self.index.functions else None

    def function_result_class(self, callee: str) -> str | None:
        """Return the class that a function returns: its annotation, or its one returned class."""
        entry = self.index.functions[callee]  # The function definition.
        view = self.index.scope_view(entry.module, entry.node)  # The annotation sees the local imports.
        found = self.annotation_class(view, entry.node.returns)  # The return annotation first.
        if found is not None or callee in self._return_guard:  # A known answer, or a recursive request.
            return found
        self._return_guard.add(callee)  # Stop a recursive request for the same function.
        try:  # Always clear the guard.
            returned = self.return_types(callee)  # The classes of the return statements.
        finally:
            self._return_guard.discard(callee)
        return next(iter(returned)) if len(returned) == 1 else None  # Only one class is a clear answer.

    # ------------------------------------------------------------------ callees
    def resolve_callee(self, view: ScopeView, func: ast.expr, context: TypeContext, strict: bool) -> str | None:
        """Return the function or class key that a callee expression reaches, or None.

        A strict request uses the typed facts only. A loose request also tries a
        unique method name, for a receiver of unknown type or a receiver that
        forwards unknown members with ``__getattr__``.
        """
        if isinstance(func, ast.Name):  # For example: build_cache().
            return self.name_callee(view, func, context)
        if not isinstance(func, ast.Attribute):  # For example: handlers[0]().
            return None
        owner = self.expr_class(view, func.value, context)  # The class of the receiver.
        if owner:  # The receiver has a known class.
            found = self.class_member(owner, func.attr)
            if found or strict or self.class_member(owner, "__getattr__") is None:
                return found  # A member, or no member and no forward.
        found, settled = self.dotted_callee(view, func)  # A module path or a class name in the chain.
        if found or settled or strict:  # A clear answer, or a chain that must not use the name fallback.
            return found
        return self.fallback_callee(func.attr, owner)  # The unique method name.

    def name_callee(self, view: ScopeView, func: ast.Name, context: TypeContext) -> str | None:
        """Return the target of a call through a plain name."""
        if func.id in context.var_types:  # A local object is not a function.
            return None
        if func.id == "cls" and context.class_key:  # cls() builds the owner class.
            return context.class_key
        target = self.index.resolve_symbol(view, func.id)  # An imported or module-level definition.
        return target if target in self.index.functions or target in self.index.classes else None

    def dotted_callee(self, view: ScopeView, func: ast.Attribute) -> tuple[str | None, bool]:
        """Return the target of a dotted call, and a flag that is True when the answer is final.

        The answer is final for a chain into another package and for a chain
        through a project module. The name fallback must not guess in both cases.
        """
        parts = AstNames.dotted(func)  # For example ["exporters", "SiteExporter", "run"].
        if not parts:
            return None, False
        head = self.index.resolve_symbol(view, parts[0])  # The first part of the chain.
        if head and head.startswith("ext:"):  # A chain into another package, such as requests.get.
            return None, True
        if head and head.startswith("module:"):  # A chain through a project module.
            found, settled = self.module_chain(head.removeprefix("module:"), parts)
            if settled:
                return found, True
        return self.class_hint_chain(parts), False  # A class name in the chain.

    def module_chain(self, module_name: str, parts: list[str]) -> tuple[str | None, bool]:
        """Return the target of a call through a project module, and a flag for a final answer."""
        key = f"{module_name}:{'.'.join(parts[1:])}"  # A function or a class in the module.
        if key in self.index.functions or key in self.index.classes:
            return key, True
        class_key = f"{module_name}:{parts[1]}" if len(parts) > 2 else ""  # A class in the module.
        if class_key in self.index.classes:  # The module names the class, so its member is the answer.
            return self.class_member(class_key, parts[2]), True
        return None, False  # The module does not settle the chain.

    def class_hint_chain(self, parts: list[str]) -> str | None:
        """Return the target of a chain that names a class, such as mh.SiteExporter.run."""
        for position in range(len(parts) - 1):  # Each part except the last can name a class.
            candidates = self.class_candidates(parts[position])  # The classes with this name.
            if len(candidates) == 1 and parts[position] not in RECEIVER_NAMES:  # One clear class.
                found = self.class_member(candidates[0], parts[position + 1])
                if found:
                    return found
        return None

    def class_candidates(self, name: str) -> list[str]:
        """Return the classes that a name can refer to: a class name, an alias, or a snake_case name."""
        simple = self.index.class_by_simple.get(name, []) or sorted(self.index.alias_classes.get(name, ()))
        if simple or "_" not in name.strip("_"):  # A direct match, or no snake_case form.
            return simple
        pascal = "".join(word.capitalize() for word in name.strip("_").split("_"))  # site_exporter -> SiteExporter.
        return self.index.class_by_simple.get(pascal, [])

    def fallback_callee(self, name: str, owner: str | None) -> str | None:
        """Return the one project function with this name, and prefer the package of the owner."""
        if name in self.generic_names or name.startswith("__"):  # A common name matches too many functions.
            return None
        candidates = self.index.func_by_simple.get(name, [])  # Every function with this name.
        if owner and len(candidates) > 1:  # Prefer a function in the package of the owner class.
            package = owner.split(":", 1)[0].rsplit(".", 1)[0] + "."  # For example src.ssid_consolidation.
            local = [key for key in candidates if key.split(":", 1)[0].startswith(package)]
            if len(local) == 1:
                return local[0]
        return candidates[0] if len(candidates) == 1 else None
