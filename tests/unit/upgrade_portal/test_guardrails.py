"""Guardrail tests for the rules that bind every task of the upgrade portal.

Why:
    ``specs/1823-upgrade-capture-portal/tasks.md:39-51`` holds the rules that
    bind every task of this feature. Tasks T213 to T218 ask for a guard on the
    registry entry, the two key strategies, the brand theme file, the forbidden
    import, the forbidden call, and the reserved word. No test read these rules
    before this file, so a later contributor breaks one of them by accident.

    Every failure message names the file and the line. A reader opens the
    offending line without a search.

    The reserved word rule needs care. A docstring or a comment that explains
    the ban holds the banned word. A plain text search reports that explanation
    as a violation, and the rule becomes impossible to write. This file solves
    the problem in two steps, and it keeps no allow list.

    1. The Python scan reads the syntax tree. It reads each identifier and each
       string constant that is not a docstring. The tree holds no comment and
       the scan drops each docstring, so an explanation of the ban is exempt by
       construction.
    2. The page scan removes each comment region of an HTML, a JavaScript, or a
       CSS file before it reads the text. The removal writes one line break for
       each line break that it drops, so a reported line number stays correct.

    Each scan reads the syntax tree, never the raw text, for the import rule and
    the call rule. A text search finds a name inside a docstring and reports a
    false failure, and it misses a call that a line break splits.
"""

from __future__ import annotations

import ast
import fnmatch
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from src.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES
from src.upgrade_portal.capture.store import (  # WHY: issue #2061 pins the write name to the read name.
    CAPTURE_COLLECTION,
    CAPTURE_OPERATION,
    RUN_COLLECTION,
    RUN_OPERATION,
)
from src.utils.operation_registry import OperationRegistry

# WHY: This file sits at tests/unit/upgrade_portal, so the root is three levels up.
REPO_ROOT = Path(__file__).resolve().parents[3]

# WHY: Every scan below reads this package and nothing outside it.
PORTAL_ROOT = REPO_ROOT / "src" / "upgrade_portal"

# WHY: The menu classification file that task T004 changed.
REGISTRY_PATH = REPO_ROOT / "src" / "utils" / "operation_registry.py"

# WHY: The key strategy file that tasks T005 and T006 changed.
STRATEGY_PATH = REPO_ROOT / "src" / "refactors" / "endpoint_primary_key_strategies.py"

# WHY: The brand theme from task T018. The brand name stays inside the content.
THEME_PATH = PORTAL_ROOT / "app" / "assets" / "static" / "css" / "themes" / "magenta.css"

# WHY: The container build reads this file, and git never reads it.
DOCKERIGNORE_PATH = REPO_ROOT / ".dockerignore"

# WHY: A theme name that holds a brand token. The control probe proves that the
# ignore check still finds a bad name, so a pass carries meaning.
BRAND_THEME_PROBE = "src/upgrade_portal/app/assets/static/css/themes/tmo.css"

# WHY: tasks.md:48. The module holds four globals and two save-and-restore
# blocks that are not thread safe. The portal uses the seam instead.
FORBIDDEN_MODULE = "firmware_manager"

# WHY: tasks.md:49. The installed SDK builds the cancel path inside that
# function at mistapi/api/v1/orgs/ssr.py:167, so a read cancels the upgrade.
FORBIDDEN_ENDPOINT = "getOrgSsrUpgrade"

# WHY: tasks.md:50. The portal uses threads, so no module imports asyncio.
FORBIDDEN_LIBRARY = "asyncio"

# WHY: tasks.md:51. The cloud upgrade body already uses this field name for a
# Junos file action. The internal term is capture. The search holds no word
# boundary, so a plural form and a longer form also fail.
RESERVED_WORD = re.compile("snapshot", re.IGNORECASE)

# WHY: The portal holds 38 modules today. A floor proves that the scan reads the
# package. A wrong root would pass every ban with an empty file list.
MINIMUM_PORTAL_MODULES = 20

# WHY: The two names that a dynamic import call uses.
DYNAMIC_IMPORT_NAMES = frozenset({"import_module", "__import__"})

# WHY: The node types that hold a docstring as the first statement of the body.
DOCSTRING_HOLDERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)

# WHY: Each node type and the field that holds an identifier on that node.
IDENTIFIER_FIELDS: dict[type[ast.AST], tuple[str, ...]] = {
    ast.FunctionDef: ("name",),
    ast.AsyncFunctionDef: ("name",),
    ast.ClassDef: ("name",),
    ast.Name: ("id",),
    ast.Attribute: ("attr",),
    ast.arg: ("arg",),
    ast.keyword: ("arg",),
    ast.alias: ("name", "asname"),
    ast.ImportFrom: ("module",),
    ast.ExceptHandler: ("name",),
}

# WHY: Each page file type and the comment regions that the scan removes.
COMMENT_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    ".html": (re.compile(r"<!--.*?-->", re.DOTALL), re.compile(r"\{#.*?#\}", re.DOTALL)),
    ".js": (re.compile(r"/\*.*?\*/", re.DOTALL), re.compile(r"//[^\n]*")),
    ".css": (re.compile(r"/\*.*?\*/", re.DOTALL),),
}


def where(path: Path, line: int) -> str:
    """Return one file position that a reader pastes into an editor.

    Why:
        A bare assertion teaches a reader nothing. Each message below starts
        with this position, so the reader opens the exact line.

    Args:
        path: The path of the file.
        line: The 1-based line number.

    Returns:
        The path relative to the repository root, then a colon and the line.
    """
    return f"{path.relative_to(REPO_ROOT).as_posix()}:{line}"  # WHY: Posix form reads the same on every platform.


def line_of(path: Path, needle: str) -> int:
    """Return the first line that holds one piece of text.

    Why:
        A missing registry entry has no line of its own. The message then names
        the line of the nearest anchor, so the reader sees where to add it.

    Args:
        path: The path of the file to read.
        needle: The text to find.

    Returns:
        The 1-based line number, or 1 when the text is absent.
    """
    lines = path.read_text(encoding="utf-8").splitlines()  # WHY: Reads the file once for one search.
    for index, line in enumerate(lines, start=1):  # WHY: The enumerate start makes the number 1-based.
        if needle in line:  # WHY: A plain match, because the caller passes a literal key.
            return index
    return 1  # WHY: The head of the file is the fallback anchor.


def portal_modules() -> list[Path]:
    """Return every Python module of the portal package.

    Why:
        Five tests read the same file list. One helper keeps the list in one
        place, so a new subpackage joins every scan at once.

    Returns:
        Each module path in a stable order.
    """
    return sorted(PORTAL_ROOT.rglob("*.py"))  # WHY: A stable order keeps a failure list repeatable.


def parse_module(path: Path) -> ast.Module:
    """Return the syntax tree of one module.

    Why:
        A module that does not parse defeats every scan below. The guard fails
        with the offending line instead of a silent skip, because a skip lets a
        broken file hide a banned import.

    Args:
        path: The path of the module.

    Returns:
        The syntax tree of the module.
    """
    text = path.read_text(encoding="utf-8")  # WHY: One read for the parse below.
    try:
        return ast.parse(text)  # WHY: The tree sees a call that a line break splits.
    except SyntaxError as error:  # WHY: A broken file must name its own line.
        pytest.fail(f"{where(path, error.lineno or 1)} does not parse: {error.msg}")


def identifiers(tree: ast.Module) -> list[tuple[str, int]]:
    """Return every identifier of one syntax tree with its line.

    Why:
        The reserved word rule and the forbidden call rule both read names. A
        table of node types keeps the walk to one loop, so the function stays
        inside the Five-Item Rule.

    Args:
        tree: The syntax tree of one module.

    Returns:
        Each identifier with the 1-based line that holds it.
    """
    found: list[tuple[str, int]] = []  # WHY: Collects every name of the module.
    for node in ast.walk(tree):  # WHY: The walk reaches a nested function and a nested class.
        for field in IDENTIFIER_FIELDS.get(type(node), ()):  # WHY: An unlisted node type holds no identifier.
            value = getattr(node, field, None)  # WHY: An absent alias name reads as None.
            if isinstance(value, str):  # WHY: Drops the None of an absent alias name.
                found.append((value, getattr(node, "lineno", 1)))  # WHY: Keeps the line for the message.
    return found


def docstring_nodes(tree: ast.Module) -> set[int]:
    """Return the identity of every docstring constant of one syntax tree.

    Why:
        A docstring that explains the ban on the reserved word holds that word.
        The reserved word scan drops these nodes, so the explanation stays
        legal and the rule stays enforceable.

    Args:
        tree: The syntax tree of one module.

    Returns:
        The ``id`` of each string constant that serves as a docstring.
    """
    found: set[int] = set()  # WHY: Holds the identity of each docstring constant.
    for node in ast.walk(tree):  # WHY: A docstring sits on a module, a class, or a function.
        body = getattr(node, "body", []) if isinstance(node, DOCSTRING_HOLDERS) else []  # WHY: Other nodes hold none.
        first = body[0] if body else None  # WHY: A docstring is always the first statement.
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):  # WHY: A docstring is a bare string.
            found.add(id(first.value))  # WHY: The tree stays alive, so the identity stays valid.
    return found


def page_strings(tree: ast.Module) -> list[tuple[str, int]]:
    """Return every string constant of one module that is not a docstring.

    Why:
        A page string reaches the operator. The reserved word must not reach the
        operator, and a docstring reaches no operator, so the scan drops each
        docstring first.

    Args:
        tree: The syntax tree of one module.

    Returns:
        Each string value with the 1-based line that holds it.
    """
    skipped = docstring_nodes(tree)  # WHY: The exempt set from the helper above.
    found: list[tuple[str, int]] = []  # WHY: Collects each remaining string.
    for node in ast.walk(tree):  # WHY: A string sits at any depth of the tree.
        # WHY: The identity test drops each docstring, so an explanation of the ban stays legal.
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skipped:
            found.append((node.value, node.lineno))  # WHY: Keeps the line for the message.
    return found


def dynamic_import_targets(node: ast.AST) -> list[tuple[str, int]]:
    """Return the literal module name of one dynamic import call.

    Why:
        A contributor reaches a banned module through ``import_module`` as well
        as through an import statement. The scan reads the literal argument, so
        the check stays precise and no docstring can trip it.

    Args:
        node: One node of the syntax tree.

    Returns:
        The module name with its line, or an empty list.
    """
    if not isinstance(node, ast.Call):  # WHY: Only a call reaches a dynamic import.
        return []
    # WHY: A call reaches the name as import_module(...) or as importlib.import_module(...).
    name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
    first = node.args[0] if node.args else None  # WHY: The module name is the first argument.
    # WHY: A computed name defeats every static scan, so the check reads a literal argument only.
    if name in DYNAMIC_IMPORT_NAMES and isinstance(first, ast.Constant) and isinstance(first.value, str):
        return [(first.value, node.lineno)]  # WHY: The line of the call names the offending position.
    return []


def import_targets(node: ast.AST) -> list[tuple[str, int]]:
    """Return every module name that one import node names.

    Why:
        A ban on a module must catch ``import x``, ``from x import y``, and
        ``import_module("x")``. One helper serves the forbidden import rule and
        the concurrency rule.

    Args:
        node: One node of the syntax tree.

    Returns:
        Each named module with the 1-based line that holds it.
    """
    if isinstance(node, ast.Import):  # WHY: The plain form names each module in an alias.
        return [(alias.name, node.lineno) for alias in node.names]
    if isinstance(node, ast.ImportFrom):  # WHY: The from form names a module and each imported name.
        prefix = node.module or ""  # WHY: A relative import holds no module name.
        members = [(f"{prefix}.{alias.name}", node.lineno) for alias in node.names]  # WHY: Catches a submodule import.
        return [(prefix, node.lineno), *members]
    return dynamic_import_targets(node)  # WHY: The remaining form is a call.


def imports_of(path: Path, tree: ast.Module, banned: str) -> list[str]:
    """Return one message for each import of a banned module.

    Why:
        The forbidden import rule and the concurrency rule read the same shape.
        One helper keeps the two tests short.

    Args:
        path: The path of the module under test.
        tree: The syntax tree of the module.
        banned: The module name that no portal module may import.

    Returns:
        One message for each offending import.
    """
    offenders: list[str] = []  # WHY: Collects each violation of one module.
    for node in ast.walk(tree):  # WHY: An import inside a function also counts.
        for name, line in import_targets(node):  # WHY: One import node can name several modules.
            if banned in name.split("."):  # WHY: A segment match keeps a similar name, such as asyncio_tools, legal.
                offenders.append(f"{where(path, line)} imports {name}")  # WHY: The message names file and line.
    return offenders


def run_git(*arguments: str) -> subprocess.CompletedProcess[str]:
    """Run one git command at the repository root.

    Why:
        Git is the only authority on a tracked file and on a ``.gitignore``
        rule. A hand-written matcher for ``.gitignore`` would drift from git.

    Args:
        *arguments: The git arguments after the executable.

    Returns:
        The finished process with its output.
    """
    executable = shutil.which("git")  # WHY: The absolute path avoids a shell lookup.
    if executable is None:  # WHY: A computer without git cannot answer the question.
        pytest.skip("git is absent, so the test cannot read the index")
    return subprocess.run([executable, *arguments], cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def active_ignore_patterns(path: Path) -> list[tuple[str, int]]:
    """Return every active pattern of one ignore file.

    Why:
        The container build reads ``.dockerignore``, and git never reads it. No
        tool reports a match, so the test matches the patterns itself.

    Args:
        path: The path of the ignore file.

    Returns:
        Each pattern with the 1-based line that holds it.
    """
    entries: list[tuple[str, int]] = []  # WHY: Collects each pattern that the build applies.
    for index, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()  # WHY: A trailing space would break the match.
        if line and not line.startswith(("#", "!")):  # WHY: A comment and an exception apply no exclusion.
            entries.append((line.rstrip("/"), index))  # WHY: A directory pattern matches the bare name.
    return entries


def matching_ignore_patterns(relative: str, entries: list[tuple[str, int]]) -> list[str]:
    """Return one message for each ignore pattern that matches one path.

    Why:
        The build drops a file when a pattern matches the whole path or one
        directory of the path. The check reads both forms.

    Args:
        relative: The path relative to the repository root, in posix form.
        entries: Each pattern with its line number.

    Returns:
        One message for each matching pattern.
    """
    parts = relative.split("/")  # WHY: A pattern can match one directory of the path.
    matches: list[str] = []  # WHY: Collects each rule that would drop the file.
    for pattern, line in entries:  # WHY: The build applies every pattern of the file.
        whole = fnmatch.fnmatchcase(relative, pattern)  # WHY: Case matters, because the brand rules repeat the case.
        segment = any(fnmatch.fnmatchcase(part, pattern) for part in parts)  # WHY: Catches a directory rule.
        if whole or segment:  # WHY: Either form drops the file from the image.
            matches.append(f"{where(DOCKERIGNORE_PATH, line)} pattern {pattern} drops the file")
    return matches


def reserved_word_offenders(path: Path, tree: ast.Module) -> list[str]:
    """Return one message for each reserved word in the code of one module.

    Why:
        The scan reads an identifier and a page string. It reads no docstring
        and no comment, so an explanation of the ban stays legal.

    Args:
        path: The path of the module under test.
        tree: The syntax tree of the module.

    Returns:
        One message for each offending identifier and each offending string.
    """
    names = [(f"identifier {name}", line) for name, line in identifiers(tree) if RESERVED_WORD.search(name)]
    texts = [(f"string {text.strip()[:40]}", line) for text, line in page_strings(tree) if RESERVED_WORD.search(text)]
    return [f"{where(path, line)} holds the reserved word in the {detail}" for detail, line in names + texts]


def page_files() -> list[Path]:
    """Return every page file of the portal that the team owns.

    Why:
        The vendored Bootstrap files are third-party. The team never edits them,
        so the reserved word rule does not apply to them.

    Returns:
        Each template, script, and stylesheet path in a stable order.
    """
    root = PORTAL_ROOT / "app" / "assets"  # WHY: Every page file sits under the asset directory.
    found = (item for item in root.rglob("*") if item.suffix in COMMENT_PATTERNS)  # WHY: Skips a binary asset.
    return sorted(item for item in found if "vendor" not in item.parts)  # WHY: Drops the third-party subtree.


def strip_comments(text: str, suffix: str) -> str:
    """Return the text of one page file without its comment regions.

    Why:
        A comment that explains the ban on the reserved word holds that word.
        The replacement writes one line break for each dropped line break, so a
        reported line number stays correct.

    Args:
        text: The content of the page file.
        suffix: The file suffix, which selects the comment syntax.

    Returns:
        The text with each comment region replaced by its line breaks.
    """
    for pattern in COMMENT_PATTERNS.get(suffix, ()):  # WHY: Each file type uses its own comment syntax.
        text = pattern.sub(lambda match: "\n" * match.group(0).count("\n"), text)  # WHY: Keeps the line count.
    return text


class TestRepositoryGuardrails:
    """Tests for the repository entries that the portal needs (T213 to T215)."""

    def test_menu_238_carries_the_destructive_registry_entry(self) -> None:
        """Menu 239 holds a registry row, and the row names the destructive category.

        Why:
            ``OperationRegistry.get`` fails closed. An absent option returns the
            ``unregistered`` category and the build breaks. Menu 239 starts a
            web server and drives a firmware upgrade, so it writes device state.
        """
        anchor = where(REGISTRY_PATH, line_of(REGISTRY_PATH, '"239":'))  # WHY: Names the row or the head of the file.
        entry = OperationRegistry.get("239")  # WHY: The public reader, never the private table.
        category = entry.get("category", "")  # WHY: An absent key reads as an empty string.
        assert category != "unregistered", f"{anchor} holds no row for menu 239"
        assert category == "destructive", f"{anchor} sets the category {category}, and the row needs destructive"
        assert entry.get("skip_reason", "") != "", f"{anchor} holds no skip reason for menu 239"

    @pytest.mark.parametrize(
        ("endpoint", "key_field"),
        [(CAPTURE_COLLECTION, "capture_id"), (RUN_COLLECTION, "run_id")],
    )
    def test_the_portal_write_endpoint_uses_natural_pk(self, endpoint: str, key_field: str) -> None:
        """Each portal write endpoint uses the natural primary key strategy.

        Why:
            ``src/db/redis_writer.py:598`` puts a 7-day time to live on every
            ``composite_pk`` document. The portal keeps a capture and a run
            forever, so a change to the strategy would delete the history.

        Args:
            endpoint: The endpoint name in the strategy table.
            key_field: The single field that forms the key.
        """
        anchor = where(STRATEGY_PATH, line_of(STRATEGY_PATH, f'"{endpoint}"'))  # WHY: Names the entry.
        entry = ENDPOINT_PRIMARY_KEY_STRATEGIES.get(endpoint)  # WHY: An absent entry reads as None.
        assert entry is not None, f"{anchor} holds no {endpoint} entry"
        strategy = entry.get("type", "")  # WHY: The message repeats the wrong value.
        assert strategy == "natural_pk", f"{anchor} sets the strategy {strategy} for {endpoint}"
        assert entry.get("primary_key") == [key_field], f"{anchor} names another key field for {endpoint}"

    @pytest.mark.parametrize(
        ("operation", "collection"),
        [(CAPTURE_OPERATION, CAPTURE_COLLECTION), (RUN_OPERATION, RUN_COLLECTION)],
    )
    def test_the_write_name_equals_the_read_name(self, operation: str, collection: str) -> None:
        """The name the portal writes equals the name the portal reads.

        Why:
            Issue #2061. ``DataExporter.write_with_format_selection`` hands the
            operation name to ``DatabaseRouter.write``, which hands it to
            ``ArangoWriter.write`` as the collection name.
            ``ArangoWriter._ensure_collection`` then creates whatever it is
            handed. Nothing translates the name on the way.

            The two constants used to differ. Every capture wrote into a
            collection named ``upgradeCaptureWrite`` while the read-back looked
            in ``upgrade_captures``, found nothing, and reported
            ``document_absent``. Every capture failed while the write succeeded,
            and the storage bootstrap still reported all three collections
            ready, so no readiness signal caught it.

        Args:
            operation: The name the portal writes through.
            collection: The name the portal reads back.
        """
        assert operation == collection, (
            f"The portal writes {operation!r} and reads {collection!r}. "
            "The router creates the collection it is handed, so a capture would "
            "land in the write name and the verify would fail with document_absent."
        )

    @pytest.mark.parametrize("stale", ["upgradeCaptureWrite", "upgradeRunWrite"])
    def test_no_stale_write_endpoint_name_returns(self, stale: str) -> None:
        """Neither retired endpoint name comes back into the strategy table.

        Why:
            Issue #2061. Each of these names created a collection of its own and
            broke every capture. An entry under one of them would mean the write
            name and the read name had parted again.

        Args:
            stale: The retired endpoint name.
        """
        assert (
            stale not in ENDPOINT_PRIMARY_KEY_STRATEGIES
        ), f"{stale} returned to the strategy table. It names a collection that the portal never reads."

    def test_the_brand_theme_stays_tracked_by_git(self) -> None:
        """Git tracks the brand theme, and no ``.gitignore`` rule drops it.

        Why:
            ``.gitignore:31-35`` drops any path that holds a brand token. The
            theme keeps the brand name inside its content only. A rename to a
            brand name would drop the file from the repository in silence.
        """
        relative = THEME_PATH.relative_to(REPO_ROOT).as_posix()  # WHY: Git reads a posix path on every platform.
        tracked = run_git("ls-files", "--error-unmatch", relative)  # WHY: A tracked path returns 0.
        assert tracked.returncode == 0, f"{relative}:1 is not tracked by git"
        ignored = run_git("check-ignore", "--no-index", "-q", relative)  # WHY: The flag reads the rules, not the index.
        assert ignored.returncode != 0, f"{relative}:1 matches a .gitignore rule"
        probe = run_git("check-ignore", "--no-index", "-q", BRAND_THEME_PROBE)  # WHY: Proves the check still works.
        assert probe.returncode == 0, f"{BRAND_THEME_PROBE}:1 escapes the brand rules, so the check is empty"

    def test_the_brand_theme_matches_no_dockerignore_pattern(self) -> None:
        """No ``.dockerignore`` pattern drops the brand theme from the image.

        Why:
            ``.dockerignore:93-96`` drops any path that holds a brand token.
            Git never reads that file, so no git command answers this question.
            A dropped theme leaves the portal without its brand colors.
        """
        entries = active_ignore_patterns(DOCKERIGNORE_PATH)  # WHY: Each pattern that the build applies.
        relative = THEME_PATH.relative_to(REPO_ROOT).as_posix()  # WHY: The build reads a posix path.
        offenders = matching_ignore_patterns(relative, entries)  # WHY: Each rule that would drop the theme.
        assert offenders == [], "\n".join([f"{relative} is dropped from the image:", *offenders])
        probe = matching_ignore_patterns(BRAND_THEME_PROBE, entries)  # WHY: Proves the matcher still finds a bad name.
        assert probe != [], f"{BRAND_THEME_PROBE} escapes the brand rules, so the check is empty"


class TestPortalCodeGuardrails:
    """Tests for the rules that bind every module of the portal (T216 to T218)."""

    def test_the_scan_reads_every_portal_module(self) -> None:
        """The scan finds the portal package and its modules.

        Why:
            A wrong root gives an empty file list, and every ban below then
            passes without a read. This test fails first when the package moves.
        """
        modules = portal_modules()  # WHY: The same list that every ban below reads.
        assert PORTAL_ROOT.is_dir(), f"{PORTAL_ROOT.as_posix()}:1 is not a directory"
        assert len(modules) >= MINIMUM_PORTAL_MODULES, f"The scan found {len(modules)} modules under {PORTAL_ROOT.name}"

    def test_the_portal_imports_no_firmware_manager_name(self) -> None:
        """No portal module imports a name from ``src/firmware/firmware_manager.py``.

        Why:
            tasks.md:48 bans the module. It holds four globals at ``:34-37``,
            and the save-and-restore blocks at ``:1736`` and ``:1797`` are not
            thread safe. The portal uses the seam ``src/firmware/upgrade_service.py``.
        """
        offenders: list[str] = []  # WHY: Collects each import across the package.
        for path in portal_modules():  # WHY: Every module of the package needs the check.
            offenders.extend(imports_of(path, parse_module(path), FORBIDDEN_MODULE))  # WHY: One parse for one scan.
        assert offenders == [], "\n".join(["The portal must use the upgrade seam:", *offenders])

    def test_the_portal_names_no_broken_ssr_endpoint(self) -> None:
        """No portal module names ``getOrgSsrUpgrade``.

        Why:
            tasks.md:49 bans the call. The installed SDK builds the cancel path
            inside that function at ``mistapi/api/v1/orgs/ssr.py:167``. A status
            read would therefore cancel the upgrade of the operator.
        """
        offenders: list[str] = []  # WHY: Collects each mention across the package.
        for path in portal_modules():  # WHY: Every module of the package needs the check.
            tree = parse_module(path)  # WHY: The tree sees a call that a line break splits.
            offenders.extend(  # WHY: Adds each mention of the endpoint in this module.
                f"{where(path, line)} names {name}" for name, line in identifiers(tree) if name == FORBIDDEN_ENDPOINT
            )
        assert offenders == [], "\n".join(["The SDK function cancels instead of reads:", *offenders])

    def test_the_portal_imports_no_asyncio(self) -> None:
        """No portal module imports ``asyncio``.

        Why:
            tasks.md:50 asks for threads. The portal shares a connection pool
            executor with the rest of the repository, and that pool uses
            threads. An async module would need a second runtime.
        """
        offenders: list[str] = []  # WHY: Collects each import across the package.
        for path in portal_modules():  # WHY: Every module of the package needs the check.
            offenders.extend(imports_of(path, parse_module(path), FORBIDDEN_LIBRARY))  # WHY: One parse for one scan.
        assert offenders == [], "\n".join(["The portal uses threads, never asyncio:", *offenders])

    def test_the_portal_code_holds_no_reserved_word(self) -> None:
        """No identifier and no string of the portal holds the word ``snapshot``.

        Why:
            tasks.md:51 reserves the word. The cloud upgrade body already uses
            that field name for a Junos file action, and Junos also uses the
            word for its recovery snapshot. The internal term is ``capture``.
            The scan reads no docstring and no comment, so an explanation of
            the ban stays legal. The module docstring above holds the reasons.
        """
        offenders: list[str] = []  # WHY: Collects each identifier and each string.
        for path in portal_modules():  # WHY: Every module of the package needs the check.
            offenders.extend(reserved_word_offenders(path, parse_module(path)))  # WHY: Reads names and strings.
            if RESERVED_WORD.search(path.stem):  # WHY: A file name is an identifier for the import system.
                offenders.append(f"{where(path, 1)} holds the reserved word in the file name")
        assert offenders == [], "\n".join(["The internal term is capture:", *offenders])

    def test_the_portal_pages_hold_no_reserved_word(self) -> None:
        """No template, script, or stylesheet of the portal holds the word ``snapshot``.

        Why:
            A page string reaches the operator, and the operator must read one
            term for one concept. The scan removes each comment region first, so
            a comment that explains the ban stays legal.
        """
        offenders: list[str] = []  # WHY: Collects each page line that breaks the rule.
        for path in page_files():  # WHY: The vendored third-party files stay outside the scan.
            text = strip_comments(path.read_text(encoding="utf-8"), path.suffix)  # WHY: Keeps the line count.
            offenders.extend(  # WHY: Adds each page line that holds the word.
                f"{where(path, number)} holds the reserved word"
                for number, line in enumerate(text.splitlines(), start=1)  # WHY: The start makes the number 1-based.
                if RESERVED_WORD.search(line)  # WHY: The comment regions already left the text.
            )
        assert offenders == [], "\n".join(["The internal term is capture:", *offenders])
