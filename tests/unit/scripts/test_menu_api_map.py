"""Tests for the menu API endpoint map tool.

Issue #3411 adds ``scripts/menu_api_map``. The tool walks each menu handler
through the call graph, and it writes the endpoint map pages. Most tests build a
small source tree in ``tmp_path``, so they need no network and no Mist token.

The ``--check`` tests prove that the drift guard fails. The guard fails on a
stale page, on a missing page, and on an orphan page. The SDK index test fails
when the vendored index does not describe the installed mistapi package. A
patch release of mistapi skips the strict row comparison and prints the repair.
"""

from __future__ import annotations  # Postponed annotations keep the type hints light.

import ast  # Builds the handler expression of a synthetic menu option.
import json  # Names the decode error that a damaged data file raises.
import textwrap  # Removes the indent of each fixture source file.
import time  # Supplies the start time that the check command reports.
from pathlib import Path  # Builds the fixture file paths.

import pytest  # Supplies the fixtures and the raises helper.

from scripts.menu_api_map.__main__ import REPO_ROOT, MapBuilder, MenuApiMapCli, PageFiles  # The command.
from scripts.menu_api_map.analysis.reference_data import (  # The data files and their readers.
    SDK_INDEX_PATH,
    CuratedRules,
    SdkEndpoint,
    SdkIndex,
    SdkSourceReader,
)
from scripts.menu_api_map.analysis.resolver import TypeResolver  # Finds the class of a receiver.
from scripts.menu_api_map.analysis.scanner import ScanCache, ScanTools  # Scans each function one time.
from scripts.menu_api_map.analysis.source_index import SourceIndex  # Parses the fixture tree.
from scripts.menu_api_map.analysis.walker import (  # The code under test.
    EndpointUse,
    HelperResult,
    MenuOption,
    MenuRegistryReader,
    MenuResult,
    MenuWalker,
)
from scripts.menu_api_map.render.mermaid import MAX_BREAKDOWN, MermaidDiagram  # The diagram builder.
from scripts.menu_api_map.render.pages import PageInput, PageSet  # The page builder.

SDK_VERSION = "0.0.test"  # The version that the fixture SDK index reports.
SDK_ROWS = [  # A small SDK index: two org and site functions, and two const functions.
    SdkEndpoint("api.v1.orgs.sites.listOrgSites", "GET", "/api/v1/orgs/{org_id}/sites", ""),
    SdkEndpoint("api.v1.sites.devices.listSiteDevices", "GET", "/api/v1/sites/{site_id}/devices", ""),
    SdkEndpoint("api.v1.const.countries.listCountryCodes", "GET", "/api/v1/const/countries", ""),
    SdkEndpoint("api.v1.const.languages.listLanguages", "GET", "/api/v1/const/languages", ""),
]
CURATED = {  # The curated rules of the fixture tree.
    "helper_classes": {"InputUtils": "The helper asks the operator for a value."},
    "generic_names": [],
    "dynamic_calls": [
        {
            "function": "src.handlers.reports:ConstExporter._discover",
            "reason": "The exporter finds each const function at run time.",
            "sdk_prefix": "api.v1.const.",
        }
    ],
    "no_endpoint_reasons": {"0": "Menu 0 closes MistHelper, so it sends no API request."},
}
ENTRY_POINT = '''
    """Fixture entry point with one menu table."""
    from src.handlers.reports import ConstExporter, RawClient, SiteReport
    from src.helpers.input_utils import InputUtils
    from src.utils.operation_registry import OperationRegistry


    class GlobalImportManager:
        """Fixture holder of the menu entry type."""

        class MenuEntry:
            """Fixture menu entry."""

            def __init__(self, **fields):
                self.fields = fields


    menu_actions: dict[str, object] = {
        "1": GlobalImportManager.MenuEntry(menu_id=1, handler=lambda: SiteReport().run(), title="Export  sites"),
        "2": GlobalImportManager.MenuEntry(menu_id=2, handler=lambda: InputUtils.pick_site(), title="Pick a site"),
        "3": GlobalImportManager.MenuEntry(menu_id=3, handler=lambda: RawClient().run(), title="Send a request"),
        "4": GlobalImportManager.MenuEntry(menu_id=4, handler=lambda: ConstExporter().export(), title="Constants"),
        "0": GlobalImportManager.MenuEntry(menu_id=0, handler=lambda: print("bye"), title="Exit"),
        "5": GlobalImportManager.MenuEntry(menu_id=5, handler=lambda: print("new"), title="New option"),
    }
'''
HANDLERS = '''
    """Fixture handlers."""
    import mistapi

    from src.helpers.input_utils import InputUtils


    class SiteReport:
        """Fixture handler that uses a helper and one SDK call."""

        def run(self):
            site_id = InputUtils.pick_site()
            return mistapi.api.v1.sites.devices.listSiteDevices(None, site_id)


    class RawClient:
        """Fixture handler that sends a raw request."""

        def __init__(self):
            self.session = None

        def run(self):
            org_id = "fixture"
            paths = ["/api/v1/orgs/{org_id}/sites"]
            return self.session.mist_get(f"/api/v1/orgs/{org_id}/sites"), paths


    class ConstExporter:
        """Fixture handler with an SDK walk that static analysis cannot follow."""

        def export(self):
            return self._discover()

        def _discover(self):
            return []
'''
HELPER = '''
    """Fixture shared helper."""
    import mistapi


    class InputUtils:
        """Fixture shared helper."""

        @staticmethod
        def pick_site():
            return mistapi.api.v1.orgs.sites.listOrgSites(None, "fixture")
'''
REGISTRY = '''
    """Fixture registry."""


    class OperationRegistry:
        """Fixture registry of the menu categories."""

        _REGISTRY: dict[str, dict[str, str]] = {
            "0": {"category": "interactive"},
            "1": {"category": "safe"},
            "2": {"category": "interactive_safe"},
            "3": {"category": "safe"},
            "4": {"category": "resource_intensive"},
        }
'''
FIXTURE_FILES = {  # Repository path to its source text.
    "MistHelper.py": ENTRY_POINT,
    "src/__init__.py": "",
    "src/handlers/__init__.py": "",
    "src/handlers/reports.py": HANDLERS,
    "src/helpers/__init__.py": "",
    "src/helpers/input_utils.py": HELPER,
    "src/utils/__init__.py": "",
    "src/utils/operation_registry.py": REGISTRY,
}


class FixtureRepository:
    """Write a small source tree, and build the walker for it."""

    def __init__(self, root: Path) -> None:
        """Store the folder that holds the fixture tree."""
        self.root = root  # The fixture repository root.

    def write(self, files: dict[str, str]) -> FixtureRepository:
        """Write each fixture file, and return this repository for a chained call."""
        for relative, text in files.items():  # One file for each entry.
            path = self.root / relative  # The absolute fixture path.
            path.parent.mkdir(parents=True, exist_ok=True)  # The package folder can be new.
            path.write_text(textwrap.dedent(text), encoding="utf-8")  # Remove the indent of the literal.
        return self

    def walker(self) -> tuple[MenuWalker, MenuRegistryReader]:
        """Index the fixture tree, and return the walker and the menu table reader."""
        index = SourceIndex(self.root).build()  # Parse every fixture file.
        curated = CuratedRules(CURATED)  # The fixture rules.
        sdk = SdkIndex(SDK_ROWS, SDK_VERSION)  # The fixture SDK index.
        tools = ScanTools(index, TypeResolver(index, curated.generic_names), sdk, curated)  # The shared tables.
        return MenuWalker(tools, ScanCache(tools)), MenuRegistryReader(index)

    def page_input(self) -> PageInput:
        """Walk every menu option and every helper, and return the page input."""
        walker, reader = self.walker()  # A fresh walker for each build.
        menus = [walker.walk_menu(option) for option in reader.read()]  # One result for each menu option.
        helpers = walker.walk_helpers()  # The helpers that a walk entered.
        holders = {use.holder for result in [*menus, *helpers] for use in result.endpoints if use.holder}
        return PageInput(menus, helpers, MapBuilder.holder_files(walker, holders), SDK_VERSION)


@pytest.fixture(name="page_input")
def fixture_page_input(tmp_path: Path) -> PageInput:
    """Return the page input of the fixture tree."""
    return FixtureRepository(tmp_path).write(FIXTURE_FILES).page_input()  # One walk for each test.


def menu_of(page_input: PageInput, menu_id: int) -> MenuResult:
    """Return the result of one menu option."""
    return next(result for result in page_input.menus if result.option.menu_id == menu_id)  # The one match.


def sdk_names(endpoints: list[EndpointUse]) -> list[str]:
    """Return the SDK function names of an endpoint list, in list order."""
    return [use.sdk for use in endpoints]  # An empty name marks a raw request.


def test_menu_walk_reports_the_sdk_call_and_stops_at_the_helper(page_input: PageInput) -> None:
    """Menu 1 shows its own SDK call, and it names the helper where the walk stopped."""
    result = menu_of(page_input, 1)  # The handler calls a class that calls a helper.
    assert sdk_names(result.endpoints) == ["api.v1.sites.devices.listSiteDevices"]  # The helper call stays out.
    assert result.endpoints[0].holder == "src.handlers.reports:SiteReport.run"  # The method that calls the SDK.
    assert result.endpoints[0].evidence == "call"  # A direct call is the strongest evidence.
    assert result.helpers == ["InputUtils"]  # The walk stopped at the helper.


def test_helper_walk_lists_the_endpoint_behind_the_stop(page_input: PageInput) -> None:
    """The helper section lists the endpoint that the menu walk did not enter."""
    assert [helper.name for helper in page_input.helpers] == ["InputUtils"]  # The one helper that a walk entered.
    helper: HelperResult = page_input.helpers[0]  # The helper result.
    assert sdk_names(helper.endpoints) == ["api.v1.orgs.sites.listOrgSites"]  # The helper call.
    assert helper.truncated is False  # The walk did not reach the limit.


def test_handler_that_calls_only_a_helper_enters_the_helper(page_input: PageInput) -> None:
    """Menu 2 calls the helper and nothing else, so the walk enters the helper."""
    result = menu_of(page_input, 2)  # The handler calls the helper directly.
    assert sdk_names(result.endpoints) == ["api.v1.orgs.sites.listOrgSites"]  # The helper endpoint shows.
    assert result.helpers == []  # The walk did not stop.


def test_raw_request_replaces_the_bare_path_string(page_input: PageInput) -> None:
    """Menu 3 sends one raw request, and the same path in a list adds no second row."""
    endpoints = menu_of(page_input, 3).endpoints  # The raw request and the path string.
    assert len(endpoints) == 1  # One row for one request.
    assert (endpoints[0].method, endpoints[0].path) == ("GET", "/api/v1/orgs/{org_id}/sites")  # The request.
    assert (endpoints[0].sdk, endpoints[0].evidence) == ("", "path")  # No SDK function sends it.


def test_curated_dynamic_call_adds_each_sdk_function_below_the_prefix(page_input: PageInput) -> None:
    """Menu 4 reaches a function that a curated rule expands to every const function."""
    endpoints = menu_of(page_input, 4).endpoints  # The curated functions.
    expected = ["api.v1.const.countries.listCountryCodes", "api.v1.const.languages.listLanguages"]  # Path order.
    assert sdk_names(endpoints) == expected  # Both const functions.
    assert {use.evidence for use in endpoints} == {"curated"}  # The rule is the only evidence.


def test_menu_with_no_endpoint_shows_its_curated_reason(page_input: PageInput) -> None:
    """Menu 0 sends no request, and the curated rules explain why."""
    result = menu_of(page_input, 0)  # The exit option.
    assert result.endpoints == []  # No request.
    assert result.reason == CURATED["no_endpoint_reasons"]["0"]  # The curated reason.


def test_category_comes_from_the_registry_and_fails_closed(page_input: PageInput) -> None:
    """Each category comes from the registry, and a missing entry is unregistered."""
    categories = {result.option.menu_id: result.option.category for result in page_input.menus}  # Menu to category.
    assert categories[1] == "safe"  # A registry entry.
    assert categories[4] == "resource_intensive"  # A second registry entry.
    assert categories[5] == "unregistered"  # Menu 5 has no registry entry.
    assert menu_of(page_input, 1).option.title == "Export sites"  # The reader collapses the spaces.


def test_page_set_writes_both_page_sets_with_menu_links(page_input: PageInput) -> None:
    """The page set holds the documentation pages and the wiki pages, with working menu links."""
    pages = PageSet(page_input).render()  # Every page of both sets.
    assert "documentation/menu-api/README.md" in pages  # The documentation index.
    assert "documentation/wiki/Menu-API-Endpoints-Safe.md" in pages  # A wiki category page.
    assert "[1](safe.md#menu-1)" in pages["documentation/menu-api/README.md"]  # The index links menu 1.
    assert "## Menu 1" in pages["documentation/menu-api/safe.md"]  # The anchor target of the link.
    assert "```mermaid" in pages["documentation/menu-api/safe.md"]  # The page holds the diagrams.


def test_walk_and_pages_are_deterministic(tmp_path: Path) -> None:
    """Two builds of the same tree give the same pages, so the drift check is stable."""
    repository = FixtureRepository(tmp_path).write(FIXTURE_FILES)  # One fixture tree.
    first = PageSet(repository.page_input()).render()  # The first build.
    second = PageSet(repository.page_input()).render()  # A second build with a fresh walker.
    assert first == second  # The same text for each page.


def test_reader_fails_when_the_menu_table_is_missing(tmp_path: Path) -> None:
    """A guard that cannot read the menu table must fail, not pass."""
    files = {**FIXTURE_FILES, "MistHelper.py": '"""Entry point with no menu table."""\n'}  # No menu table.
    walker, reader = FixtureRepository(tmp_path).write(files).walker()  # Index the broken tree.
    del walker  # The reader fails before a walk.
    with pytest.raises(SystemExit, match="menu_actions"):  # The message names the missing table.
        reader.read()


def test_build_fails_when_the_menu_table_is_empty(tmp_path: Path) -> None:
    """A guard that reads zero menu options must fail, not report a clean result."""
    entry = '"""Entry point with an empty menu table."""\nmenu_actions: dict[str, object] = {}\n'  # No option.
    FixtureRepository(tmp_path).write({**FIXTURE_FILES, "MistHelper.py": entry})  # Write the empty table.
    with pytest.raises(SystemExit, match="no menu option"):  # The build refuses the empty table.
        MapBuilder(tmp_path).build()


class TestCheckGuard:
    """Prove that the --check guard fails on each kind of drift, and passes on clean pages."""

    PAGES = {  # Two expected pages, one in each page set.
        "documentation/menu-api/README.md": "index\n",
        "documentation/wiki/Menu-API-Endpoints.md": "wiki index\n",
    }

    @staticmethod
    def write(root: Path, pages: dict[str, str]) -> None:
        """Write the named pages below the root folder."""
        for relative, text in pages.items():  # One file for each page.
            path = root / relative  # The absolute page path.
            path.parent.mkdir(parents=True, exist_ok=True)  # The page folder can be new.
            path.write_text(text, encoding="utf-8")  # The page text.

    def test_check_passes_when_every_page_matches(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Clean pages give exit code 0 and a count of the checked pages."""
        self.write(tmp_path, self.PAGES)  # The pages match.
        code = MenuApiMapCli.check(PageFiles(tmp_path, self.PAGES), 6, time.perf_counter())  # Run the guard.
        assert code == 0  # The guard passes.
        assert "OK: 2 map pages match the source for 6 menu options" in capsys.readouterr().out  # The counts.

    def test_check_fails_on_a_stale_page(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """A page with old text gives exit code 1, and the report names the page and the fix."""
        self.write(tmp_path, {**self.PAGES, "documentation/menu-api/README.md": "old index\n"})  # One stale page.
        code = MenuApiMapCli.check(PageFiles(tmp_path, self.PAGES), 6, time.perf_counter())  # Run the guard.
        output = capsys.readouterr().out  # The report.
        assert code == 1  # The guard fails.
        assert "stale: documentation/menu-api/README.md" in output  # The report names the page.
        assert "python -m scripts.menu_api_map" in output  # The report names the fix command.

    def test_check_fails_on_a_missing_page(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """A page that does not exist gives exit code 1."""
        self.write(tmp_path, {"documentation/menu-api/README.md": "index\n"})  # The wiki page is missing.
        code = MenuApiMapCli.check(PageFiles(tmp_path, self.PAGES), 6, time.perf_counter())  # Run the guard.
        assert code == 1  # The guard fails.
        assert "stale: documentation/wiki/Menu-API-Endpoints.md" in capsys.readouterr().out  # The missing page.

    def test_check_fails_on_an_orphan_page(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """A map page that the source no longer makes gives exit code 1, and other wiki pages stay out."""
        orphans = {"documentation/menu-api/old.md": "old\n", "documentation/wiki/Menu-API-Endpoints-Old.md": "old\n"}
        self.write(tmp_path, {**self.PAGES, **orphans, "documentation/wiki/Home.md": "home\n"})  # Extra pages.
        code = MenuApiMapCli.check(PageFiles(tmp_path, self.PAGES), 6, time.perf_counter())  # Run the guard.
        output = capsys.readouterr().out  # The report.
        assert code == 1  # The guard fails.
        assert all(f"orphan: {relative}" in output for relative in orphans)  # Each orphan appears.
        assert "Home.md" not in output  # A wiki page outside the map is not an orphan.

    def test_write_repairs_the_drift_with_unix_line_ends(self, tmp_path: Path) -> None:
        """The write action fixes each stale page and each orphan page, and the check then passes."""
        self.write(tmp_path, {"documentation/menu-api/README.md": "old\n", "documentation/menu-api/old.md": "x\n"})
        files = PageFiles(tmp_path, self.PAGES)  # The expected pages.
        assert MenuApiMapCli.write(files, 6, time.perf_counter()) == 0  # The write succeeds.
        assert files.stale() == [] and files.orphans() == []  # No drift remains.
        assert b"\r\n" not in (tmp_path / "documentation/menu-api/README.md").read_bytes()  # Unix line ends.


def synthetic_menu(title: str, endpoint_count: int) -> MenuResult:
    """Return a menu result with the given title and the given number of endpoints."""
    option = MenuOption(7, title, "safe", ast.Constant(None), "None")  # A synthetic menu option.
    uses = [  # One GET row for each endpoint, all from one class.
        EndpointUse("GET", f"/api/v1/sites/{{site_id}}/item{number:02d}", "", "", "src.a:Reader.run", "path")
        for number in range(endpoint_count)
    ]
    return MenuResult(option, uses, [], 1, False, "")


def test_breakdown_caps_the_endpoint_nodes_and_counts_the_rest() -> None:
    """A large menu shows MAX_BREAKDOWN endpoint nodes, and one node counts the rest."""
    diagram = MermaidDiagram.breakdown(synthetic_menu("Read items", MAX_BREAKDOWN + 2))  # Two endpoints too many.
    assert diagram.count("--> e") == MAX_BREAKDOWN  # The endpoint node limit.
    assert '"2 more endpoints in the table"' in diagram  # The summary node.
    assert 'c1["Reader"]' in diagram  # The caller node names the class.


def test_breakdown_uses_the_singular_for_one_hidden_endpoint() -> None:
    """One hidden endpoint gives a singular noun in the summary node."""
    diagram = MermaidDiagram.breakdown(synthetic_menu("Read items", MAX_BREAKDOWN + 1))  # One endpoint too many.
    assert '"1 more endpoint in the table"' in diagram  # The singular form.


def test_endpoint_label_keeps_the_path_braces() -> None:
    """An endpoint label keeps the path parameters, so a reader can match the path to the table."""
    use = EndpointUse("?", "/api/v1/orgs/{org_id}/sites", "", "", "src.a:Reader.run", "path")  # No method.
    assert MermaidDiagram.endpoint_label(use) == "Unknown /api/v1/orgs/{org_id}/sites"  # The label text.


def test_menu_label_hides_a_title_that_the_reference_lint_reads_as_a_class() -> None:
    """A title with a class-like word becomes Menu N, so the diagram reference lint stays clean."""
    assert MermaidDiagram.menu_label(synthetic_menu("Open the SSHRunner console", 0)) == "Menu 7"  # Hidden title.
    assert MermaidDiagram.menu_label(synthetic_menu("Read items", 0)) == "Menu 7: Read items"  # A plain title.


def test_curated_rules_match_the_source_tree() -> None:
    """Each curated rule must name code that exists, or a rename disables the rule without a failure."""
    index = SourceIndex(REPO_ROOT).build()  # The real source tree.
    curated = CuratedRules.load()  # The real curated rules.
    class_names = {key.split(":", 1)[1] for key in index.classes}  # Every class name.
    constant_names = {key.split(":", 1)[1] for key in index.constants}  # Every constant name.
    missing = [name for name in curated.helper_classes if name not in class_names | constant_names]
    assert missing == [], f"curated.json names helper classes that do not exist: {missing}"  # Helpers exist.
    functions = [rule.function for rule in curated.dynamic_calls.values()]  # The dynamic call keys.
    absent = [key for key in functions if key not in index.functions]  # A renamed function.
    assert absent == [], f"curated.json names dynamic calls that do not exist: {absent}"  # Functions exist.
    menu_ids = {str(option.menu_id) for option in MenuRegistryReader(index).read()}  # The real menu numbers.
    assert set(curated.no_endpoint_reasons) <= menu_ids  # Each reason names a real menu option.


def test_sdk_index_load_stops_on_malformed_json(tmp_path: Path) -> None:
    """A damaged SDK index stops the command with the file name and the repair."""
    path = tmp_path / "sdk_index.json"  # A damaged index file.
    path.write_text('{"format": 1, "functions": [', encoding="utf-8")  # The JSON text ends too early.
    with pytest.raises(SystemExit, match="does not hold valid JSON") as error:  # The command stops.
        SdkIndex.load(path)
    assert isinstance(error.value.__cause__, json.JSONDecodeError)  # The decode error is the cause.
    assert "--refresh-sdk-index" in str(error.value)  # The message names the repair.


def test_curated_rules_load_stops_on_an_empty_file(tmp_path: Path) -> None:
    """An empty curated file stops the command, and it does not give a map with no rules."""
    path = tmp_path / "curated.json"  # An empty rules file.
    path.write_bytes(b"")  # The file holds no bytes.
    with pytest.raises(SystemExit, match="is empty"):  # The command stops.
        CuratedRules.load(path)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("[1, 2]", "does not hold a JSON object"),  # A list, not an object.
        ("   \n", "is empty"),  # White space only.
    ],
)
def test_data_file_rejects_a_file_that_holds_no_object(tmp_path: Path, text: str, expected: str) -> None:
    """A data file must hold one JSON object, because the loaders read named fields."""
    path = tmp_path / "data.json"  # The data file.
    path.write_text(text, encoding="utf-8")  # The text under test.
    with pytest.raises(SystemExit, match=expected):  # The reason appears in the message.
        CuratedRules.load(path)


def test_data_file_stops_when_the_file_does_not_exist(tmp_path: Path) -> None:
    """A missing data file stops the command with the file name."""
    with pytest.raises(SystemExit, match="does not exist"):  # The command stops.
        SdkIndex.load(tmp_path / "missing.json")


class SdkReleaseCheck:
    """Decide how the SDK index test compares the vendored index with the installed mistapi."""

    SAME = "same"  # The index describes the installed release, so every row must match.
    PATCH = "patch"  # Only the patch number differs, so the strict row comparison skips.
    LINE = "line"  # The major or the minor number differs, so the test fails.

    @staticmethod
    def decide(installed: str, vendored: str) -> str:
        """Return SAME, PATCH, or LINE for the installed and the vendored mistapi versions.

        The requirement range permits each patch release of one release line. An
        upstream patch release must not stop every unrelated pull request. A new
        release line comes only from a change to the requirement range, and that
        change must refresh the index.
        """
        if installed == vendored:  # The index describes this exact release.
            return SdkReleaseCheck.SAME
        if installed.split(".")[:2] == vendored.split(".")[:2]:  # The same major and minor numbers.
            return SdkReleaseCheck.PATCH
        return SdkReleaseCheck.LINE  # A new release line.


@pytest.mark.parametrize(
    ("installed", "expected"),
    [
        ("0.64.0", SdkReleaseCheck.SAME),  # The exact release of the index.
        ("0.64.3", SdkReleaseCheck.PATCH),  # A patch release that the range permits.
        ("0.65.0", SdkReleaseCheck.LINE),  # A new minor release line.
        ("1.64.0", SdkReleaseCheck.LINE),  # A new major release line.
    ],
)
def test_sdk_release_check_fails_only_on_a_new_release_line(installed: str, expected: str) -> None:
    """The decision needs no network and no installed package, so it proves each branch of the guard."""
    assert SdkReleaseCheck.decide(installed, "0.64.0") == expected  # The decision for each release.


def test_vendored_sdk_index_matches_the_installed_mistapi() -> None:
    """The vendored SDK index must describe the installed mistapi, or the map shows old endpoints."""
    vendored = SdkIndex.load()  # The index that the map reads.
    installed = SdkSourceReader.installed_version()  # The mistapi release in this environment.
    fix = "Run python -m scripts.menu_api_map --refresh-sdk-index, then python -m scripts.menu_api_map."  # The fix.
    decision = SdkReleaseCheck.decide(installed, vendored.version)  # Compare the two releases.
    found = f"The vendored SDK index describes mistapi {vendored.version}, and mistapi {installed} is installed."
    assert decision != SdkReleaseCheck.LINE, f"{found} {fix}"  # A new release line must refresh the index.
    if decision == SdkReleaseCheck.PATCH:  # A patch release must not stop an unrelated pull request.
        pytest.skip(f"{found} The strict row comparison needs the same release. {fix}")
    rows = SdkSourceReader(SdkSourceReader.installed_dir()).read()  # Read the installed SDK source.
    expected = SdkIndex(rows, installed).render()  # The index text it produces.
    assert SDK_INDEX_PATH.read_text(encoding="utf-8") == expected, f"The vendored SDK index is stale. {fix}"
