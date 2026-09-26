"""Page builder: turn the walk results into the Markdown pages of the map.

The builder writes two page sets from the same results. The documentation set
lives in ``documentation/menu-api/`` and uses relative links. The wiki set lives
in ``documentation/wiki/`` and uses wiki page names and absolute GitHub links.
"""

from __future__ import annotations  # Postponed annotations keep the type hints light.

from collections import Counter  # Counts the menu options that reach each endpoint.
from dataclasses import dataclass  # Holds the page input as one value.

from ..analysis.walker import MAX_VISITED, ROOT_HOLDER, EndpointUse, HelperResult, MenuResult  # The walk results.
from .markdown import CATEGORY_ORDER, DOCS_STYLE, EVIDENCE_LABELS, WIKI_STYLE, LinkStyle, MarkdownText
from .mermaid import MAX_BREAKDOWN, MermaidDiagram  # The diagram text and its node limit.

DOCS_FOLDER = "documentation/menu-api"  # The folder of the documentation page set.
WIKI_FOLDER = "documentation/wiki"  # The folder of the wiki page set.
TOP_ENDPOINTS = 25  # The number of rows in the table of the most used endpoints.
GENERATED_NOTICE = "<!-- The tool python -m scripts.menu_api_map writes this page. Do not edit it by hand. -->"
CATEGORY_TEXT = {  # One sentence that describes each category.
    "safe": "A menu option in this category reads data and exports it. The --test run executes this category.",
    "interactive_safe": "A menu option in this category asks the operator for input, and it reads data only.",
    "destructive": "A menu option in this category changes the Mist cloud configuration.",
    "interactive": "A menu option in this category needs a live operator session.",
    "websocket": "A menu option in this category opens a WebSocket session to a device or to the Mist cloud.",
    "resource_intensive": "A menu option in this category runs for a long time, or it sends many API calls.",
    "continuous_loop": "A menu option in this category runs until the operator stops it.",
    "unregistered": "A menu option in this category has no entry in OperationRegistry.",
}
DESTRUCTIVE_WARNING = (
    "Warning: a menu option in this category changes the live Mist cloud configuration."
    " Make a change plan before you run one. The change can stop client traffic at a site."
)
OVERVIEW_TEXT = [  # The text that explains the two kinds of diagram on a category page.
    "Each overview diagram links a menu option to the SDK families that it uses.",
    "The section of each menu option has a second diagram.",
    "That diagram links the menu option to the classes that send the requests, and each class to its endpoints.",
]


@dataclass(frozen=True)
class PageInput:
    """The facts that every page reads."""

    menus: list[MenuResult]  # One result for each menu option, sorted by menu number.
    helpers: list[HelperResult]  # One result for each shared helper, sorted by name.
    holder_files: dict[str, str]  # Holder key to its repository file, such as src/export/site_exporter.py.
    sdk_version: str  # The mistapi version of the vendored SDK index.


class EndpointTable:
    """Build the endpoint table of one menu option or one helper."""

    def __init__(self, page_input: PageInput, style: LinkStyle) -> None:
        """Store the page input and the link style."""
        self.page_input = page_input  # The facts of the pages.
        self.style = style  # The link rules.

    def render(self, endpoints: list[EndpointUse]) -> list[str]:
        """Return the table lines of one endpoint list."""
        lines = ["| Method | Path | SDK function | Called from | Found by |", "| - | - | - | - | - |"]  # Header.
        for use in endpoints:  # One row for each endpoint.
            method = "Unknown" if use.method == "?" else use.method  # The code does not state the method.
            cells = [method, MarkdownText.code(use.path), self.sdk_cell(use), self.holder_cell(use.holder)]
            cells.append(EVIDENCE_LABELS.get(use.evidence, use.evidence))  # The evidence label.
            lines.append("| " + " | ".join(cells) + " |")
        return lines

    @staticmethod
    def sdk_cell(use: EndpointUse) -> str:
        """Return the SDK function cell: a document link, a name, or the kind of raw request."""
        if not use.sdk:  # A raw request or a channel has no SDK function.
            return "None (WebSocket channel)" if use.method == "WS" else "None (raw request)"
        name = use.sdk.removeprefix("api.v1.")  # For example orgs.sites.listOrgSites.
        return f"[`{name}`]({use.doc})" if use.doc else MarkdownText.code(name)  # Link to the Juniper document.

    def holder_cell(self, holder: str) -> str:
        """Return the call site cell: the function name and a link to its file."""
        if holder == ROOT_HOLDER:  # The handler expression itself holds the fact.
            return f"[`menu_actions`]({self.style.source('MistHelper.py')})"
        name = holder.split(":", 1)[1]  # For example SiteExporter.export.
        path = self.page_input.holder_files.get(holder, "")  # The repository file of the function.
        return f"[`{name}`]({self.style.source(path)})" if path else MarkdownText.code(name)


class CategoryPage:
    """Build the page of one menu category."""

    def __init__(self, page_input: PageInput, style: LinkStyle, category: str) -> None:
        """Store the page input, the link style, and the category."""
        self.page_input = page_input  # The facts of the pages.
        self.style = style  # The link rules.
        self.category = category  # The category of this page.
        self.table = EndpointTable(page_input, style)  # Builds each endpoint table.

    def menus(self) -> list[MenuResult]:
        """Return the menu options of this category, sorted by menu number."""
        return [result for result in self.page_input.menus if result.option.category == self.category]

    def render(self) -> str:
        """Return the text of the category page."""
        menus = self.menus()  # The menu options of this page.
        lines = [GENERATED_NOTICE, "", f"# Menu API endpoints: {self.category}", ""]  # The page header.
        lines.extend(self.introduction(len(menus)))  # The purpose of the page.
        lines.extend(["## Overview", "", *OVERVIEW_TEXT, ""])  # The purpose of the two kinds of diagram.
        for block in MermaidDiagram.groups(menus):  # One diagram for each group of menu options.
            lines.extend([block, ""])
        for result in menus:  # One section for each menu option.
            lines.extend(self.menu_section(result))
        return "\n".join(lines).rstrip("\n") + "\n"  # One line end at the end of the file.

    def introduction(self, count: int) -> list[str]:
        """Return the opening paragraphs of the category page."""
        index_link = f"[Menu API endpoint map]({self.style.index_page()})"  # The link to the index page.
        lines = [
            f"This page lists the Mist API endpoints of the {count} menu options in the `{self.category}` category."
        ]
        lines.extend(
            [
                CATEGORY_TEXT.get(self.category, ""),
                "",
                f"The index page explains how to read the map: {index_link}.",
                "",
            ]
        )
        if self.category == "destructive":  # A destructive option needs a warning.
            lines.extend([DESTRUCTIVE_WARNING, ""])
        return lines

    def menu_section(self, result: MenuResult) -> list[str]:
        """Return the section of one menu option."""
        lines = [f"## Menu {result.option.menu_id}", "", f"- Title: {MarkdownText.cell(result.option.title)}"]
        lines.append(f"- Handler: {MarkdownText.code(MarkdownText.handler(result.option.handler_text))}")
        if result.helpers:  # The shared helpers where the walk stopped.
            links = [f"[`{name}`]({self.style.index_page()}#{MarkdownText.anchor(name)})" for name in result.helpers]
            lines.append(f"- Shared helpers: {', '.join(links)}")
        lines.extend([f"- Endpoints: {len(result.endpoints)}", ""])
        if result.truncated:  # The walk stopped at the limit.
            lines.extend(
                [f"The walk stopped at the limit of {MAX_VISITED:,} functions. The list can be incomplete.", ""]
            )
        if not result.endpoints:  # No endpoint to list.
            lines.extend([result.reason or "The map finds no Mist API request for this menu option.", ""])
            return lines
        lines.extend([MermaidDiagram.breakdown(result), ""])  # The callers and their endpoints.
        return [*lines, *self.table.render(result.endpoints), ""]


class IndexPage:
    """Build the index page of the map."""

    def __init__(self, page_input: PageInput, style: LinkStyle) -> None:
        """Store the page input and the link style."""
        self.page_input = page_input  # The facts of the pages.
        self.style = style  # The link rules.
        self.table = EndpointTable(page_input, style)  # Builds each endpoint table.

    def categories(self) -> list[tuple[str, int]]:
        """Return each category that holds a menu option, with its count, in the page order."""
        counts = Counter(result.option.category for result in self.page_input.menus)  # Menus in each category.
        ordered = [name for name in CATEGORY_ORDER if name in counts]  # The known categories first.
        ordered.extend(sorted(name for name in counts if name not in CATEGORY_ORDER))  # Any new category last.
        return [(name, counts[name]) for name in ordered]

    def render(self) -> str:
        """Return the text of the index page."""
        lines = [GENERATED_NOTICE, "", "# Menu API endpoint map", ""]  # The page header.
        for section in (IndexSections.introduction, IndexSections.reading, IndexSections.diagrams):
            lines.extend(section(self))
        for section in (IndexSections.category_table, IndexSections.menu_table, IndexSections.empty_menus):
            lines.extend(section(self))
        for section in (IndexSections.top_endpoints, IndexSections.helper_sections, IndexSections.evidence):
            lines.extend(section(self))
        return "\n".join(lines).rstrip("\n") + "\n"  # One line end at the end of the file.


class IndexSections:
    """Build each section of the index page."""

    @staticmethod
    def introduction(page: IndexPage) -> list[str]:
        """Return the purpose of the map and the command that writes it."""
        count = len(page.page_input.menus)  # The number of menu options.
        return [
            f"This map shows the Mist API endpoints that each of the {count} MistHelper menu options can call.",
            "The count includes menu 0, which closes MistHelper.",
            "The menu reference does not count menu 0 as an actionable entry.",
            "Use the map to find the endpoint that does a task, and to find the code that sends the request.",
            "",
            f"A tool writes each page of the map from the source code and from mistapi {page.page_input.sdk_version}.",
            "Do not edit a page by hand. To write the pages again, run this command from the repository root:",
            "",
            "```powershell",
            "python -m scripts.menu_api_map",
            "```",
            "",
            "The `menu_reference_drift` job runs `python -m scripts.menu_api_map --check` on each pull request.",
            "If a change adds or removes an API call, the job fails until you write the pages again.",
            "",
        ]

    @staticmethod
    def reading(page: IndexPage) -> list[str]:
        """Return the limits of the map."""
        del page  # The limits are the same for each page set.
        return [
            "## How to read the map",
            "",
            "- The map comes from static analysis. The tool does not run MistHelper, and it sends no API request.",
            "- The map shows the endpoints that a menu option can reach. A call can depend on a prompt answer.",
            "- The map can miss a call that the code builds at run time from data.",
            "- The walk stops at a shared helper. The shared helper section lists the endpoints of each helper.",
            "- The HTTP method is Unknown when the code holds the path in a string and does not state the method.",
            f"- The diagram of a menu option shows {MAX_BREAKDOWN} endpoints or fewer. The table lists each endpoint.",
            "",
        ]

    @staticmethod
    def diagrams(page: IndexPage) -> list[str]:
        """Return the overview diagrams."""
        return [
            "## How a menu option reaches the Mist cloud",
            "",
            MermaidDiagram.request_path(),
            "",
            "## How the tool builds the map",
            "",
            MermaidDiagram.method(),
            "",
            "## Menu options in each category",
            "",
            MermaidDiagram.category_pie(page.categories()),
            "",
        ]

    @staticmethod
    def category_table(page: IndexPage) -> list[str]:
        """Return the table of the category pages."""
        lines = ["## Category pages", "", "| Category | Menu options | With an endpoint | Page |", "| - | - | - | - |"]
        for name, count in page.categories():  # One row for each category.
            reached = sum(1 for result in page.page_input.menus if result.option.category == name and result.endpoints)
            link = f"[{name}]({page.style.category_page(name)})"  # The link to the category page.
            lines.append(f"| `{name}` | {count} | {reached} | {link} |")
        return [*lines, ""]

    @staticmethod
    def menu_table(page: IndexPage) -> list[str]:
        """Return the table of every menu option."""
        lines = ["## Find a menu option", "", "| Menu | Title | Category | Endpoints |", "| - | - | - | - |"]
        for result in page.page_input.menus:  # One row for each menu option.
            option = result.option  # The menu entry.
            link = f"[{option.menu_id}]({page.style.category_page(option.category)}#menu-{option.menu_id})"
            lines.append(
                f"| {link} | {MarkdownText.cell(option.title)} | `{option.category}` | {len(result.endpoints)} |"
            )
        return [*lines, ""]

    @staticmethod
    def empty_menus(page: IndexPage) -> list[str]:
        """Return the list of the menu options that reach no endpoint."""
        empty = [result for result in page.page_input.menus if not result.endpoints]  # No endpoint found.
        lines = [
            "## Menu options with no endpoint",
            "",
            f"The map finds no Mist API request for {len(empty)} menu options.",
            "",
        ]
        for result in empty:  # One line for each menu option.
            reason = result.reason or "No curated reason exists yet."  # The curated reason, if any.
            lines.append(f"- Menu {result.option.menu_id}: {reason}")
        return [*lines, ""]

    @staticmethod
    def top_endpoints(page: IndexPage) -> list[str]:
        """Return the table of the endpoints that the most menu options reach."""
        counts: Counter[str] = Counter()  # SDK function to the number of menu options.
        rows: dict[str, EndpointUse] = {}  # SDK function to one row that names it.
        for result in page.page_input.menus:  # Count each SDK function one time for each menu option.
            for use in result.endpoints:
                if use.sdk:
                    counts[use.sdk] += 1
                    rows.setdefault(use.sdk, use)
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:TOP_ENDPOINTS]  # The largest first.
        lines = ["## Most used endpoints", "", "| Menu options | Method | Path | SDK function |", "| - | - | - | - |"]
        for dotted, count in ranked:  # One row for each SDK function.
            use = rows[dotted]  # The row that holds the method and the path.
            lines.append(f"| {count} | {use.method} | {MarkdownText.code(use.path)} | {EndpointTable.sdk_cell(use)} |")
        return [*lines, ""]

    @staticmethod
    def helper_sections(page: IndexPage) -> list[str]:
        """Return one section for each shared helper."""
        lines = ["## Shared helpers", "", "The walk of a menu option stops at these helpers.", ""]
        for helper in page.page_input.helpers:  # One section for each helper.
            lines.extend([f"### {helper.name}", "", helper.purpose, ""])
            if helper.helpers:  # The other helpers that this helper uses.
                lines.extend([f"This helper also uses: {', '.join(f'`{name}`' for name in helper.helpers)}.", ""])
            if helper.truncated:  # The walk stopped at the limit.
                lines.extend(
                    [f"The walk stopped at the limit of {MAX_VISITED:,} functions. The list can be incomplete.", ""]
                )
            if not helper.endpoints:  # No endpoint to list.
                lines.extend(["The map finds no Mist API request for this helper.", ""])
                continue
            lines.extend([*page.table.render(helper.endpoints), ""])
        return lines

    @staticmethod
    def evidence(page: IndexPage) -> list[str]:
        """Return the table that explains each evidence kind."""
        del page  # The evidence kinds are the same for each page set.
        return [
            "## Evidence kinds",
            "",
            "| Found by | Meaning |",
            "| - | - |",
            "| Call | The code calls the SDK function. |",
            "| Reference | The code passes the SDK function as a value, or a string holds its full path. |",
            "| Name | A string holds the SDK function name. The code can call the function by that name. |",
            "| Curated | A curated rule adds the function, because the code finds it at run time. |",
            "| Path | The code holds the request path, and it sends the request without an SDK function. |",
            "| Channel | The code subscribes to this WebSocket channel. |",
            "",
        ]


class PageSet:
    """Build every page of both page sets."""

    def __init__(self, page_input: PageInput) -> None:
        """Store the page input."""
        self.page_input = page_input  # The facts of the pages.

    def render(self) -> dict[str, str]:
        """Return each page, keyed by its repository path with forward slashes."""
        pages: dict[str, str] = {}  # Repository path to its text.
        for style, folder, index_name in (
            (DOCS_STYLE, DOCS_FOLDER, "README.md"),
            (WIKI_STYLE, WIKI_FOLDER, "Menu-API-Endpoints.md"),
        ):
            index = IndexPage(self.page_input, style)  # The index page of this set.
            pages[f"{folder}/{index_name}"] = index.render()
            for category, _ in index.categories():  # One page for each category.
                page = CategoryPage(self.page_input, style, category)
                pages[f"{folder}/{style.category_file(category)}"] = page.render()
        return dict(sorted(pages.items()))  # A sorted order gives a stable write order.
