"""The menu walker: follow each menu handler through the call graph to its Mist API endpoints.

The walker reads the ``menu_actions`` table of ``MistHelper.py`` and the
category table of ``OperationRegistry``. It scans each handler, then follows
the call edges in breadth-first order. It stops at a shared helper class, so
that one common helper does not add its endpoints to every menu. The shared
helper section of the index page lists the endpoints of each helper one time.
"""

from __future__ import annotations  # Postponed annotations keep the type hints light.

import ast  # Reads the menu table and the category table.
import logging  # Records the walk counts for the operator.
from collections import deque  # Holds the breadth-first queue.
from dataclasses import dataclass, field  # Holds the walk results as small values.

from .reference_data import CuratedRules, SdkIndex  # The data tables.
from .resolver import TypeContext  # The empty context of a menu handler.
from .scanner import EVIDENCE_RANK, BodyScanner, Finding, ScanCache, ScanTools  # The body scanner.
from .source_index import SourceIndex  # The source tree index.

LOGGER = logging.getLogger(__name__)  # Keeps the log records tied to this module.

MAX_VISITED = 4000  # The walk of one menu stops after this many functions.
MENU_MODULE = "MistHelper"  # The module that holds the menu table.
MENU_TABLE = "menu_actions"  # The name of the menu table.
REGISTRY_KEY = "src.utils.operation_registry:OperationRegistry._REGISTRY"  # The category table constant.
ROOT_HOLDER = ""  # The holder key of a fact that the handler expression itself holds.
PATH_RANK = len(EVIDENCE_RANK)  # A raw path or a channel ranks below every SDK evidence kind.


@dataclass(frozen=True)
class MenuOption:
    """One entry of the menu table."""

    menu_id: int  # The menu number, such as 11.
    title: str  # The menu title.
    category: str  # The safety category, such as interactive_safe.
    handler: ast.expr  # The handler expression, often a lambda.
    handler_text: str  # The handler source text.


@dataclass(frozen=True)
class EndpointUse:
    """One Mist API endpoint that a menu or a helper can reach."""

    method: str  # The HTTP method, "WS" for a WebSocket channel, or "?" when the code does not state it.
    path: str  # The request path or the channel path.
    sdk: str  # The dotted mistapi function name, or an empty string for a raw request.
    doc: str  # The Juniper API document link, or an empty string.
    holder: str  # The key of the function that holds the evidence, or ROOT_HOLDER.
    evidence: str  # The evidence kind: call, reference, name, curated, path, or channel.


@dataclass
class WalkResult:
    """The functions that one walk scanned, and the helpers where it stopped."""

    order: list[tuple[str, Finding]] = field(default_factory=list)  # The scanned keys in breadth-first order.
    helpers: set[str] = field(default_factory=set)  # The helper classes where the walk stopped.
    stops: set[str] = field(default_factory=set)  # The helper keys where the walk stopped.
    parents: dict[str, str] = field(default_factory=dict)  # Each queued key to the key that reached it.
    truncated: bool = False  # True when the walk reached MAX_VISITED.


@dataclass
class MenuResult:
    """The endpoints of one menu option."""

    option: MenuOption  # The menu entry.
    endpoints: list[EndpointUse]  # The endpoints, sorted by path and method.
    helpers: list[str]  # The shared helper classes that the menu uses, sorted by name.
    visited: int  # The number of functions that the walk scanned.
    truncated: bool  # True when the walk reached MAX_VISITED.
    reason: str  # The curated reason when the menu reaches no endpoint, or an empty string.


@dataclass
class HelperResult:
    """The endpoints of one shared helper class."""

    name: str  # The helper class name, such as InputUtils.
    purpose: str  # The one-line purpose from the curated rules.
    endpoints: list[EndpointUse]  # The endpoints, sorted by path and method.
    helpers: list[str]  # The other shared helpers that this helper uses, sorted by name.
    truncated: bool  # True when the walk reached MAX_VISITED.


class MenuRegistryReader:
    """Read the menu table and the category table without an import of the project."""

    def __init__(self, index: SourceIndex) -> None:
        """Store the source index that holds both tables."""
        self.index = index  # The source tree index.

    def read(self) -> list[MenuOption]:
        """Return every menu option, sorted by menu number."""
        LOGGER.info("Reading the menu table %s.%s", MENU_MODULE, MENU_TABLE)  # Log before the table read.
        table = self.menu_table()  # The dictionary literal of the menu table.
        categories = self.categories()  # The menu number to its category.
        options = [self.option_of(key, value, categories) for key, value in zip(table.keys, table.values, strict=True)]
        options.sort(key=lambda option: option.menu_id)  # The menu number order.
        LOGGER.debug("Read %d menu options", len(options))  # Log the option count after the read.
        return options

    def menu_table(self) -> ast.Dict:
        """Return the dictionary literal that defines the menu table."""
        tree = self.index.modules[MENU_MODULE].tree  # The parsed entry point.
        for node in tree.body:  # The table is a module-level annotated assignment.
            is_table = isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)  # A named value.
            if is_table and node.target.id == MENU_TABLE and isinstance(node.value, ast.Dict):  # The menu table.
                return node.value
        raise SystemExit(f"{MENU_MODULE}.py holds no {MENU_TABLE} dictionary. Update the menu walker.")

    def categories(self) -> dict[str, str]:
        """Return the category of each menu number from the OperationRegistry table."""
        entry = self.index.constants.get(REGISTRY_KEY)  # The class constant that holds the table.
        if entry is None:  # The registry moved or changed its name.
            raise SystemExit(f"The source tree holds no {REGISTRY_KEY}. Update the menu walker.")
        table = ast.literal_eval(entry.value)  # The table is a plain literal, so no code runs.
        return {str(menu): str(row["category"]) for menu, row in table.items()}  # The menu to its category.

    @staticmethod
    def option_of(key: ast.expr | None, value: ast.expr, categories: dict[str, str]) -> MenuOption:
        """Return the menu option of one table entry."""
        if not (isinstance(key, ast.Constant) and isinstance(value, ast.Call)):  # A malformed entry.
            raise SystemExit(f"The menu table holds an entry that the walker cannot read: {ast.unparse(value)[:80]}")
        fields = {keyword.arg: keyword.value for keyword in value.keywords}  # The named fields of the entry.
        title_node = fields["title"]  # The title expression.
        title = title_node.value if isinstance(title_node, ast.Constant) else ast.unparse(title_node)  # The text.
        handler = fields["handler"]  # The handler expression.
        category = categories.get(str(key.value), "unregistered")  # The registry fails closed.
        return MenuOption(int(key.value), " ".join(str(title).split()), category, handler, ast.unparse(handler))


class MenuWalker:
    """Walk each menu handler through the call graph and collect its endpoints."""

    def __init__(self, tools: ScanTools, cache: ScanCache) -> None:
        """Store the shared tables and the scan cache."""
        self.tools = tools  # The shared tables.
        self.cache = cache  # Scans each function one time.
        self.entries: dict[str, set[str]] = {}  # Helper name to the helper keys where a walk stopped.

    @property
    def curated(self) -> CuratedRules:
        """Return the curated rules."""
        return self.tools.curated  # The hand-written rules.

    @property
    def sdk(self) -> SdkIndex:
        """Return the SDK function index."""
        return self.tools.sdk  # The SDK function index.

    def walk_menu(self, option: MenuOption) -> MenuResult:
        """Return the endpoints that one menu option can reach."""
        root, walk = self.start(option)  # Scan the handler and follow its call edges.
        self.record_entries(walk)  # The helper walks start where the menu walks stopped.
        endpoints = self.collect([(ROOT_HOLDER, root), *walk.order])  # Merge the facts.
        reason = "" if endpoints else self.curated.no_endpoint_reasons.get(str(option.menu_id), "")
        return MenuResult(option, endpoints, sorted(walk.helpers), len(walk.order), walk.truncated, reason)

    def record_entries(self, walk: WalkResult) -> set[str]:
        """Add the helper keys where one walk stopped, and return the helpers that gained a key."""
        grown: set[str] = set()  # The helpers with a new entry key.
        for key in walk.stops:  # Each helper key where the walk stopped.
            helper = self.curated.helper_of(key) or ""  # The helper that owns the key.
            known = self.entries.setdefault(helper, set())  # The entry keys of this helper.
            if key not in known:  # A new entry key.
                known.add(key)
                grown.add(helper)
        return grown

    def start(self, option: MenuOption) -> tuple[Finding, WalkResult]:
        """Scan the handler expression of one menu option, and walk the functions that it reaches."""
        view = self.tools.index.module_view(self.tools.index.modules[MENU_MODULE])  # The handler sees the module.
        scanner = BodyScanner(self.tools, view, TypeContext(None))  # A handler has no owner class.
        scanner.visit(option.handler)  # Scan the handler expression.
        roots = sorted(scanner.out.edges)  # A sorted start gives a stable walk.
        return scanner.out, self.breadth_first(roots, self.exempt_helpers(roots))

    def explain(self, option: MenuOption) -> list[str]:
        """Return the call path from the handler to each endpoint of one menu option."""
        root, walk = self.start(option)  # The same walk as the page walk.
        endpoints = self.collect([(ROOT_HOLDER, root), *walk.order])  # Merge the facts.
        lines = [f"Menu {option.menu_id}: {option.title}", f"Scanned {len(walk.order)} functions."]
        lines.append(f"Stopped at the helpers: {', '.join(sorted(walk.helpers)) or 'none'}.")
        for use in endpoints:  # One path for each endpoint.
            chain = [use.holder] if use.holder else []  # Start at the function that holds the fact.
            while chain and chain[-1] in walk.parents:  # Walk back to a root edge.
                chain.append(walk.parents[chain[-1]])
            path = " <- ".join([*(key.split(":", 1)[1] for key in chain), "handler"])  # Inner function first.
            lines.append(f"{use.method} {use.path} [{use.sdk or use.evidence}]: {path}")
        return lines

    def walk_helpers(self) -> list[HelperResult]:
        """Walk each helper that a walk entered, until no helper walk adds a new entry key."""
        results: dict[str, HelperResult] = {}  # Helper name to its latest result.
        pending = sorted(self.entries)  # The helpers that wait for a walk, in name order.
        while pending:  # A helper walk can add entry keys to another helper.
            helper = pending.pop(0)  # The next helper in name order.
            walk = self.breadth_first(sorted(self.entries[helper]), {helper})  # The walk may enter this helper only.
            grown = self.record_entries(walk)  # The helpers that gained an entry key.
            results[helper] = self.helper_result(helper, walk)  # Keep the latest result.
            pending = sorted(set(pending) | grown)  # Walk each grown helper again.
        return [results[name] for name in sorted(results)]  # A stable page order.

    def helper_result(self, helper: str, walk: WalkResult) -> HelperResult:
        """Return the result of one helper walk."""
        endpoints = self.collect(walk.order)  # Merge the facts.
        purpose = self.curated.helper_classes[helper]  # The one-line purpose of the helper.
        others = sorted(walk.helpers - {helper})  # The other helpers where the walk stopped.
        return HelperResult(helper, purpose, endpoints, others, walk.truncated)

    def exempt_helpers(self, roots: list[str]) -> set[str]:
        """Return the helpers that the walk may enter, because the handler calls only helpers."""
        helpers = [self.curated.helper_of(root) for root in roots]  # The helper of each start edge.
        if roots and all(helpers):  # A handler that only calls helpers must still show its endpoints.
            return {helper for helper in helpers if helper}
        return set()  # The walk stops at every helper.

    def breadth_first(self, roots: list[str], exempt: set[str]) -> WalkResult:
        """Scan the functions that the roots reach, in breadth-first order, and stop at the helpers."""
        result = WalkResult()  # The scanned keys and the helpers.
        queue = deque(roots)  # The keys that wait for a scan.
        seen = set(roots)  # The keys that the walk queued.
        while queue and len(seen) < MAX_VISITED:  # The limit keeps one walk small.
            current = queue.popleft()  # The next key in breadth-first order.
            helper = self.curated.helper_of(current)  # The helper that owns the key, if any.
            if helper and helper not in exempt:  # Stop at a shared helper.
                result.helpers.add(helper)
                result.stops.add(current)  # The helper walk starts at this key.
                continue
            finding = self.cache.scan(current)  # The facts of the key.
            result.order.append((current, finding))  # Keep the breadth-first order for the holders.
            fresh = sorted(edge for edge in finding.edges if edge not in seen)  # A sorted order is stable.
            seen.update(fresh)  # Queue each key one time.
            result.parents.update(dict.fromkeys(fresh, current))  # Remember the path for --explain.
            queue.extend(fresh)
        result.truncated = bool(queue)  # Keys that wait at the limit were not scanned.
        return result

    def collect(self, findings: list[tuple[str, Finding]]) -> list[EndpointUse]:
        """Merge the facts of the scanned functions into one sorted endpoint list."""
        best: dict[tuple[str, str], tuple[int, int, EndpointUse]] = {}  # Endpoint key to its best evidence.
        for position, (holder, finding) in enumerate(findings):  # The breadth-first order breaks a tie.
            for use in self.uses_of(holder, finding):  # Each fact of one function.
                rank = EVIDENCE_RANK.get(use.evidence, PATH_RANK)  # A call ranks above a name.
                key = (use.sdk or use.method, use.path)  # One row for each SDK function or raw request.
                if key not in best or (rank, position) < best[key][:2]:  # Stronger evidence, or earlier.
                    best[key] = (rank, position, use)
        uses = [entry[2] for entry in best.values()]  # The chosen row for each endpoint.
        return self.drop_duplicate_paths(uses)  # A raw path that an SDK row covers adds nothing.

    def uses_of(self, holder: str, finding: Finding) -> list[EndpointUse]:
        """Return one endpoint row for each fact of one function."""
        uses: list[EndpointUse] = []  # The rows of this function.
        for dotted, evidence in sorted(finding.sdk.items()):  # Each SDK function.
            row = self.sdk.get(dotted)  # The method, the path, and the document link.
            if row is not None:
                uses.append(EndpointUse(row.method, row.path, dotted, row.doc, holder, evidence))
        uses.extend(EndpointUse(method, path, "", "", holder, "path") for method, path in sorted(finding.raw))
        uses.extend(EndpointUse("WS", channel, "", "", holder, "channel") for channel in sorted(finding.channels))
        return uses

    @staticmethod
    def drop_duplicate_paths(uses: list[EndpointUse]) -> list[EndpointUse]:
        """Drop a raw row that another row already covers, and sort the rows."""
        sdk_requests = {(use.method, use.path) for use in uses if use.sdk}  # The requests that an SDK row names.
        known_paths = {use.path for use in uses if use.sdk or use.method != "?"}  # The paths with a known method.
        kept = [use for use in uses if use.sdk or MenuWalker.raw_row_adds(use, sdk_requests, known_paths)]
        return sorted(kept, key=lambda use: (use.path, use.method, use.sdk))  # A stable page order.

    @staticmethod
    def raw_row_adds(use: EndpointUse, sdk_requests: set[tuple[str, str]], known_paths: set[str]) -> bool:
        """Return True when a raw row names a request that no other row names."""
        if use.method == "?":  # A path string without a method adds only a new path.
            return use.path not in known_paths
        return (use.method, use.path) not in sdk_requests  # A raw request adds a request that no SDK row sends.
