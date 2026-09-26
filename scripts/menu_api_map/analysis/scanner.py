"""The body scanner: find the SDK calls, the request paths, and the call edges of one function.

The scanner visits one function body, or one constant value. It records four
kinds of facts. An SDK fact names a mistapi function. A path fact names a raw
request path. A channel fact names a WebSocket channel. An edge names another
project function that the body can call.
"""

from __future__ import annotations  # Postponed annotations keep the type hints light.

import ast  # Visits the body nodes.
import logging  # Records the scan counts for the operator.
import re  # Matches a WebSocket channel path.
from dataclasses import dataclass, field  # Holds the facts of one scan.

from .reference_data import RAW_CALLS, AstTextReader, CuratedRules, SdkIndex  # The data tables.
from .resolver import TypeContext, TypeResolver  # Finds the class of a receiver.
from .source_index import AstNames, ScopeView, SourceIndex  # The source tree index.

LOGGER = logging.getLogger(__name__)  # Keeps the log records tied to this module.

HTTP_CALLS = {"get": "GET", "post": "POST", "put": "PUT", "delete": "DELETE", "patch": "PATCH"}  # requests style.
DISPATCH_NAMES = frozenset({"call", "invoke", "dispatch", "call_method", "call_parent"})  # Dispatch by name.
WS_CHANNEL = re.compile(r"^/(sites|orgs|msps)/\{[^}]+\}/[a-z_/{}.]+$")  # For example /sites/{site_id}/devices.
MAX_TEXT_LENGTH = 300  # A longer string is a message or a template, not a name.
EVIDENCE_RANK = {"call": 0, "reference": 1, "name": 2, "curated": 3}  # The strongest evidence has rank 0.


@dataclass
class Finding:
    """The facts that one scan finds in one function body or one constant value."""

    sdk: dict[str, str] = field(default_factory=dict)  # SDK dotted name to its strongest evidence.
    raw: set[tuple[str, str]] = field(default_factory=set)  # The method and path of each raw request.
    channels: set[str] = field(default_factory=set)  # The WebSocket channel paths.
    edges: set[str] = field(default_factory=set)  # The project functions and constants that the body reaches.
    returns: set[str] = field(default_factory=set)  # The classes that the return statements produce.

    def add_sdk(self, dotted: str, evidence: str) -> None:
        """Record one SDK function, and keep the strongest evidence for it."""
        current = self.sdk.get(dotted)  # The evidence recorded before, if any.
        if current is None or EVIDENCE_RANK[evidence] < EVIDENCE_RANK[current]:  # New or stronger.
            self.sdk[dotted] = evidence


@dataclass(frozen=True)
class ScanTools:
    """The shared tables that every scan reads."""

    index: SourceIndex  # The source tree index.
    resolver: TypeResolver  # The type resolver.
    sdk: SdkIndex  # The SDK function index.
    curated: CuratedRules  # The hand-written rules.


class BodyScanner(ast.NodeVisitor):
    """Visit one body and record its SDK calls, request paths, channels, and call edges."""

    def __init__(self, tools: ScanTools, view: ScopeView, context: TypeContext) -> None:
        """Prepare an empty finding for one scope."""
        self.tools = tools  # The shared tables.
        self.view = view  # The names that the current scope can see.
        self.context = context  # The owner class and the local name classes.
        self.uri_vars: dict[str, str] = {}  # Local name to the request path that it holds.
        self.module_vars: dict[str, str] = {}  # Local name to the mistapi module that importlib loaded.
        self.out = Finding()  # The facts of this scan.
        self.consumed: set[int] = set()  # The node ids that a parent visit already explained.

    # ------------------------------------------------------------------ helpers
    def add_edge(self, key: str | None) -> None:
        """Record an edge to a function or a constant, or to the constructor of a class."""
        index = self.tools.index  # The source tree index.
        if key and (key in index.functions or key in index.constants):  # A direct target.
            self.out.edges.add(key)
            return
        if not key or key not in index.classes:  # No target, or a name outside the project.
            return
        for member in ("__init__", "__call__"):  # A class reference runs its constructor or its call method.
            found = self.tools.resolver.class_member(key, member)
            if found:
                self.out.edges.add(found)

    def uri_of(self, node: ast.AST) -> str | None:
        """Return the request path that a node holds, from the first /api/v1/ part."""
        if isinstance(node, ast.Name) and node.id in self.uri_vars:  # A local name that holds a path.
            return self.uri_vars[node.id]
        text = AstTextReader.fstring_text(node)  # The text of a string or an f-string.
        if text and "/api/v1/" in text:  # Keep the path from the version prefix.
            return "/api/v1/" + text.split("/api/v1/", 1)[1]
        return None

    def sdk_of(self, node: ast.AST) -> str | None:
        """Return the SDK dotted name when an expression names a mistapi function."""
        parts = AstNames.loose_parts(node)  # For example ["mistapi", "api", "v1", "orgs", "sites", "listOrgSites"].
        if not parts:
            return None
        target = self.module_vars.get(parts[0]) or self.view.imports.get(parts[0])  # The import behind the head.
        full = ".".join([target, *parts[1:]]) if target else ".".join(parts)  # The full dotted path.
        position = full.find("api.v1.")  # The SDK path starts at the version prefix.
        if position >= 0 and full[position:] in self.tools.sdk:  # A full SDK path.
            return full[position:]
        return self.tools.sdk.unique_owner(parts[-1])  # A unique SDK function name.

    # ------------------------------------------------------------------ scopes
    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Scan a nested function body with the local imports of that function."""
        saved = self.view  # Restore the outer view after the nested body.
        self.view = self.tools.index.scope_view(saved.module, node)  # The nested scope sees its own imports.
        for statement in node.body:  # The decorators and defaults stay out of the scan.
            self.visit(statement)
        self.view = saved

    visit_AsyncFunctionDef = visit_FunctionDef  # An async function has the same scope rules.

    def visit_Lambda(self, node: ast.Lambda) -> None:
        """Scan a lambda body with the local imports of that lambda."""
        saved = self.view  # Restore the outer view after the lambda body.
        self.view = self.tools.index.scope_view(saved.module, node)  # The lambda scope.
        self.visit(node.body)  # A lambda body is one expression.
        self.view = saved

    # ------------------------------------------------------------------ statements
    def visit_Assign(self, node: ast.Assign) -> None:
        """Record the class, the path, or the mistapi module that an assignment binds."""
        value = node.value  # The assigned expression.
        found = self.tools.resolver.expr_class(self.view, value, self.context) if isinstance(value, ast.Call) else None
        uri = self.uri_of(value) if isinstance(value, (ast.JoinedStr, ast.Constant)) else None  # A path value.
        module = self.imported_module(value)  # A mistapi module that importlib loads.
        for target in node.targets:  # Only a plain name keeps a local fact.
            if isinstance(target, ast.Name):
                self.bind_name(target.id, (found, uri, module))
        if uri:  # The path belongs to the name, so the constant visit must not count it again.
            self.consumed.add(id(value))
        self.generic_visit(node)  # Scan the value for calls.

    def bind_name(self, name: str, facts: tuple[str | None, str | None, str | None]) -> None:
        """Store the class, the path, and the module that one local name holds."""
        found, uri, module = facts  # The three optional facts.
        if found:  # The name holds an object of a known class.
            self.context.var_types[name] = found
        if uri:  # The name holds a request path.
            self.uri_vars[name] = uri
        if module:  # The name holds a mistapi module.
            self.module_vars[name] = module

    @staticmethod
    def imported_module(value: ast.expr) -> str | None:
        """Return the mistapi module that importlib.import_module("mistapi...") loads, or None."""
        if not (isinstance(value, ast.Call) and value.args):  # Not a call with an argument.
            return None
        first = value.args[0]  # The module name argument.
        if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):  # Not a literal module name.
            return None
        parts = AstNames.dotted(value.func)  # For example ["importlib", "import_module"].
        if parts and parts[-1] == "import_module" and first.value.startswith("mistapi."):  # A mistapi module.
            return first.value
        return None

    def visit_Return(self, node: ast.Return) -> None:
        """Record the class that a return statement produces."""
        if node.value is not None:  # A bare return produces no class.
            found = self.tools.resolver.expr_class(self.view, node.value, self.context)
            if found:
                self.out.returns.add(found)
        self.generic_visit(node)  # Scan the value for calls.

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Record the class that an annotated local name holds."""
        if isinstance(node.target, ast.Name):  # Only a plain name keeps a local fact.
            found = self.tools.resolver.annotation_class(self.view, node.annotation)
            if found:
                self.context.var_types[node.target.id] = found
        self.generic_visit(node)  # Scan the value for calls.

    # ------------------------------------------------------------------ calls
    def visit_Call(self, node: ast.Call) -> None:
        """Record an SDK call, a raw request, or an edge to a project function."""
        sdk_name = self.sdk_of(node.func)  # A call to a mistapi function.
        if sdk_name:
            self.out.add_sdk(sdk_name, "call")
            self.consumed.add(id(node.func))  # The callee is explained.
        elif isinstance(node.func, ast.Attribute) and (node.func.attr in RAW_CALLS or node.func.attr in HTTP_CALLS):
            self.record_request(node, node.func.attr)  # A session request or a requests call.
        else:  # A call to a project function, or to an unknown callee.
            self.record_callee(node)
        self.generic_visit(node)  # Scan the arguments for more calls.

    def record_request(self, node: ast.Call, verb: str) -> None:
        """Record the request path of a raw request call."""
        method = RAW_CALLS.get(verb) or HTTP_CALLS[verb]  # The HTTP method of the call.
        candidates = list(node.args[:1]) + [keyword.value for keyword in node.keywords if keyword.arg in ("uri", "url")]
        for candidate in candidates:  # The first argument or the uri and url keywords.
            uri = self.uri_of(candidate)
            if uri:
                self.out.raw.add((method, uri))
                self.consumed.add(id(candidate))  # The path is explained.

    def record_callee(self, node: ast.Call) -> None:
        """Record the edge of a call to a project function, and any dispatch by name."""
        callee = self.tools.resolver.resolve_callee(self.view, node.func, self.context, strict=False)
        self.add_edge(callee)  # The function, or the constructor of the class.
        if callee:
            self.consumed.add(id(node.func))  # The callee is explained.
        self.string_dispatch(node)  # getattr(obj, "name") and self._call("name").

    def string_dispatch(self, node: ast.Call) -> None:
        """Follow getattr(obj, "name") and self._call("name"), which dispatch by method name."""
        name_node = self.dispatch_name_node(node)  # The string that names the method.
        if not (isinstance(name_node, ast.Constant) and isinstance(name_node.value, str)):
            return
        name = name_node.value  # The method name.
        if not name.isidentifier() or name in self.tools.curated.generic_names:  # Not a clear method name.
            return
        chosen = self.dispatch_target(name)  # The one function with this name.
        if chosen:
            self.out.edges.add(chosen)
            self.consumed.add(id(name_node))  # The string is explained.

    @staticmethod
    def dispatch_name_node(node: ast.Call) -> ast.expr | None:
        """Return the argument that names the method in a dispatch call, or None."""
        func = node.func  # The called expression.
        if isinstance(func, ast.Name) and func.id == "getattr" and len(node.args) >= 2:  # getattr(obj, "name").
            return node.args[1]
        if isinstance(func, ast.Attribute) and func.attr.strip("_") in DISPATCH_NAMES and node.args:  # _call("name").
            return node.args[0]
        return None

    def dispatch_target(self, name: str) -> str | None:
        """Return the one function with this name, and prefer a function in the same package."""
        candidates = self.tools.index.func_by_simple.get(name, [])  # Every function with this name.
        package = self.view.name.rsplit(".", 1)[0]  # The package of the current module.
        local = [key for key in candidates if key.split(":", 1)[0].startswith(package)]  # Same package.
        chosen = local if len(local) == 1 else candidates  # A local match wins.
        return chosen[0] if len(chosen) == 1 else None

    # ------------------------------------------------------------------ references
    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Record an SDK reference, or an edge for a function that the code passes as a value."""
        if id(node) in self.consumed:  # The parent call explained the callee.
            self.visit(node.value)  # The receiver can still hold a call.
            return
        sdk_name = self.sdk_of(node)  # An SDK function passed as a value.
        if sdk_name:
            self.out.add_sdk(sdk_name, "reference")
            return
        parts = AstNames.dotted(node)  # For example ["self", "exporter", "run"].
        if parts:
            self.attribute_reference(node, parts)
            return
        self.generic_visit(node)  # A chain that starts at a call.

    def attribute_reference(self, node: ast.Attribute, parts: list[str]) -> None:
        """Record the edge of a dotted reference to a project function or constant."""
        base = self.tools.index.resolve_symbol(self.view, parts[0])  # The head of the chain.
        if base and base.startswith("ext:"):  # A chain into another package holds no project edge.
            return
        callee = self.reference_callee(node, parts)  # The function that the reference names.
        if callee:
            self.add_edge(callee)
            return
        if parts[0] in ("self", "cls") and self.context.class_key and len(parts) == 2:  # A class constant.
            member = self.tools.resolver.class_member(self.context.class_key, parts[1])
            if member and member in self.tools.index.constants:
                self.out.edges.add(member)

    def reference_callee(self, node: ast.Attribute, parts: list[str]) -> str | None:
        """Return the function that a dotted reference names, with the forward rule for self."""
        resolver = self.tools.resolver  # The type resolver.
        callee = resolver.resolve_callee(self.view, node, self.context, strict=True)  # The typed answer.
        if callee is not None or parts[0] not in ("self", "cls") or not self.context.class_key:
            return callee  # A typed answer, or a reference that is not on the receiver.
        if resolver.class_member(self.context.class_key, "__getattr__") is None:  # No forward.
            return None
        return resolver.resolve_callee(self.view, node, self.context, strict=False)  # The forwarded name.

    def visit_Name(self, node: ast.Name) -> None:
        """Record an SDK reference, or an edge for a project name that the code uses as a value."""
        if id(node) in self.consumed:  # The parent call explained the name.
            return
        sdk_name = self.sdk_of(node)  # An SDK function passed as a value.
        if sdk_name:
            self.out.add_sdk(sdk_name, "reference")
            return
        if node.id in self.context.var_types or node.id in self.uri_vars:  # A local value.
            return
        self.add_edge(self.tools.index.resolve_symbol(self.view, node.id))  # A function, a constant, or a class.

    def visit_Dict(self, node: ast.Dict) -> None:
        """Scan the values of a dictionary, and skip the constant keys."""
        for key in node.keys:  # A constant key is a label, not a reference.
            if isinstance(key, ast.Constant):
                self.consumed.add(id(key))
            elif key is not None:  # A computed key can hold a call.
                self.visit(key)
        for value in node.values:  # The values can hold calls and references.
            self.visit(value)

    # ------------------------------------------------------------------ strings
    def visit_Constant(self, node: ast.Constant) -> None:
        """Record an SDK path, an SDK name, a channel, or a request path that a string holds."""
        if id(node) in self.consumed or not isinstance(node.value, str):  # Explained, or not a string.
            return
        text = node.value.strip()  # The string without the outer white space.
        if len(text) <= MAX_TEXT_LENGTH:  # A long string is a message, not a name.
            self.classify_text(text)

    def classify_text(self, text: str) -> None:
        """Record the one fact that a short string holds."""
        sdk = self.tools.sdk  # The SDK function index.
        dotted = text.removeprefix("mistapi.")  # A spec table can name the full import path.
        owner = sdk.unique_owner(text)  # The SDK function when the string is an SDK function name.
        if dotted.startswith("api.v1.") and dotted in sdk:  # A full SDK path.
            self.out.add_sdk(dotted, "reference")
        elif owner:  # An SDK function name, such as "listOrgSites".
            self.out.add_sdk(owner, "name")
        elif WS_CHANNEL.match(text):  # A WebSocket channel.
            self.out.channels.add(text)
        elif text.startswith("/api/v1/") and " " not in text:  # A request path in a table or a message.
            self.out.raw.add(("?", text))

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        """Record a channel or a request path that an f-string builds, and scan its fields."""
        if id(node) in self.consumed:  # The parent assignment explained the path.
            return
        text = AstTextReader.fstring_text(node) or ""  # The text with one placeholder for each field.
        if WS_CHANNEL.match(text):  # A WebSocket channel.
            self.out.channels.add(text)
        elif "/api/v1/" in text and "\n" not in text:  # A request path.
            self.out.raw.add(("?", "/api/v1/" + text.split("/api/v1/", 1)[1]))
        for value in node.values:  # The fields can hold calls.
            if isinstance(value, ast.FormattedValue):
                self.visit(value.value)


class ScanCache:
    """Scan each function and each constant one time, and keep the finding."""

    def __init__(self, tools: ScanTools) -> None:
        """Prepare the empty cache, and give the resolver its return type callback."""
        self.tools = tools  # The shared tables.
        self._results: dict[str, Finding] = {}  # Key to its finding.
        tools.resolver.return_types = self.returns_of  # The resolver reads the returned classes here.

    def returns_of(self, key: str) -> set[str]:
        """Return the classes that the return statements of one function produce."""
        return self.scan(key).returns  # The scan records the returned classes.

    def scan(self, key: str) -> Finding:
        """Return the finding of one function or one constant."""
        cached = self._results.get(key)  # The finding of an earlier request.
        if cached is not None:
            return cached
        is_constant = key in self.tools.index.constants  # A constant holds a value, not a body.
        finding = self.scan_constant(key) if is_constant else self.scan_function(key)
        self.apply_curated(key, finding)  # Add the edges that static analysis cannot find.
        self._results[key] = finding  # Keep the finding for the next request.
        return finding

    def scan_constant(self, key: str) -> Finding:
        """Scan the value of one constant, and add the route handlers of a blueprint."""
        entry = self.tools.index.constants[key]  # The constant definition.
        view = self.tools.index.module_view(entry.module)  # A constant value sees the module scope.
        scanner = BodyScanner(self.tools, view, TypeContext(None))  # A constant has no owner class.
        scanner.visit(entry.value)  # Scan the assigned expression.
        scanner.out.edges.update(self.tools.index.route_handlers.get(key, []))  # A blueprint reaches its routes.
        return scanner.out

    def scan_function(self, key: str) -> Finding:
        """Scan the body of one function with the classes of its annotated parameters."""
        entry = self.tools.index.functions[key]  # The function definition.
        view = self.tools.index.scope_view(entry.module, entry.node)  # The function sees its local imports.
        arguments = [*entry.node.args.args, *entry.node.args.kwonlyargs]  # The parameters.
        params = {
            argument.arg: self.tools.resolver.annotation_class(view, argument.annotation) for argument in arguments
        }
        context = TypeContext(entry.class_key, {name: found for name, found in params.items() if found})
        scanner = BodyScanner(self.tools, view, context)  # One scanner for the body.
        for statement in AstNames.body_without_docstring(entry.node.body):  # The docstring adds no fact.
            scanner.visit(statement)
        return scanner.out

    def apply_curated(self, key: str, finding: Finding) -> None:
        """Add the curated edges and SDK functions of a dynamic call."""
        rule = self.tools.curated.dynamic_calls.get(key)  # The curated rule for this function.
        if rule is None:
            return
        LOGGER.debug("Applying the curated rule for %s", key)  # Log before the rule adds facts.
        if rule.route_handlers_under:  # A registry that imports its route modules by name.
            for blueprint, handlers in self.tools.index.route_handlers.items():
                if blueprint.startswith(rule.route_handlers_under):
                    finding.edges.update(handlers)
        if rule.sdk_prefix:  # A walk of an SDK package that calls each function.
            for dotted in self.tools.sdk.by_dotted:
                if dotted.startswith(rule.sdk_prefix):
                    finding.add_sdk(dotted, "curated")
