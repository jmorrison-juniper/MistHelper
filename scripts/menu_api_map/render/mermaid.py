"""Mermaid helpers: the overview diagrams and the diagrams that group the menu options of one category.

The diagram labels use plain characters only. The labels never hold an SDK
function name or a class name, because the ``diagram-refs`` command checks
each name in a diagram that ends in a class suffix, such as ``Config``.
"""

from __future__ import annotations  # Postponed annotations keep the type hints light.

import re  # Cleans the diagram labels.
from collections import Counter  # Counts the endpoints of each SDK family.

from ..analysis.walker import EndpointUse, MenuResult  # The walk results.

MAX_OVERVIEW_FAMILIES = 12  # The largest number of SDK family nodes in the overview diagram of a category.
MAX_BREAKDOWN = 12  # The largest number of endpoint nodes in the diagram of one menu option.
# The smallest number of endpoints that gives a menu option its own diagram. The
# table already shows a smaller menu option. GitHub fails to render the last
# diagrams of a page that holds more than about 60 diagrams.
MIN_BREAKDOWN = 3
MAX_TITLE = 40  # The longest menu title in a diagram label.
# The longest line of a request path in an endpoint node. Mermaid wraps a label
# only at a space, and a path holds no space. A long path therefore made each
# diagram wider than the wiki column, and GitHub then cut off the bottom row.
MAX_PATH_LINE = 20
# The longest line of a menu or caller label. The generator breaks the label at
# its spaces, so that the three columns of a breakdown fit the wiki column.
MAX_LABEL_LINE = 20
LINE_BREAK = "<br/>"  # The line break inside a Mermaid label.
LABEL_UNSAFE = re.compile(r"[^A-Za-z0-9 ,.:/_-]")  # The characters that a label cannot hold.
PATH_UNSAFE = re.compile(r"[^A-Za-z0-9 ,.:/_{}?=&-]")  # The characters that an endpoint label cannot hold.
ROOT_CALLER = "Handler expression in MistHelper.py"  # The caller label when the handler itself sends the request.
LINT_TRIGGERS = re.compile(  # The patterns that the diagram reference lint reads as a class name.
    r"[A-Z][a-zA-Z]+(?:Utils|Manager|Exporter|Config|Runner|Writer|Fetcher|Processor|Checker|Monitor|Emitter"
    r"|Registry|TUI)|class\s+[A-Z]|participant\s+[A-Z]"
)
RAW_FAMILY = "raw requests"  # The family of a request that the code sends without an SDK function.
WS_FAMILY = "websocket channels"  # The family of a WebSocket channel.
FENCE = "```"  # The Markdown code fence.


class MermaidDiagram:
    """Build the Mermaid text of the map pages."""

    @staticmethod
    def label(text: str) -> str:
        """Return a label that holds plain characters only."""
        cleaned = LABEL_UNSAFE.sub(" ", text)  # Replace each unsafe character with a space.
        return " ".join(cleaned.split())  # Collapse the spaces.

    @staticmethod
    def menu_label(result: MenuResult) -> str:
        """Return the label of one menu node: the number and a short title."""
        title = MermaidDiagram.label(result.option.title)  # The title with plain characters.
        short = title if len(title) <= MAX_TITLE else title[: MAX_TITLE - 3].rstrip() + "..."  # A short title.
        text = f"Menu {result.option.menu_id}: {short}"  # The number first.
        if LINT_TRIGGERS.search(text):  # Keep the lint clean.
            return f"Menu {result.option.menu_id}"
        return MermaidDiagram.wrap(text)  # Short lines keep the diagram narrow.

    @staticmethod
    def wrap(text: str, width: int = MAX_LABEL_LINE) -> str:
        """Break a label at its spaces into lines of ``width`` characters or fewer.

        A word that is longer than the limit breaks at its underscores.
        """
        lines: list[str] = []
        for word in text.split():  # Add each word to the current line, or start a new line.
            if lines and len(lines[-1]) + 1 + len(word) <= width:
                lines[-1] += " " + word
            elif len(word) > width:  # A long name, such as _fetch_site_name_lookup_from_api.
                lines.extend(MermaidDiagram.split_word(word, width))
            else:
                lines.append(word)
        return LINE_BREAK.join(lines)

    @staticmethod
    def split_word(word: str, width: int) -> list[str]:
        """Break a long name at its underscores and before its capitals.

        The name stays on one line if a break changes the names that the
        diagram reference lint reads, such as a break that makes ExportManager.
        """
        parts = MermaidDiagram.split_parts(word, r"_?[^_A-Z]+|[A-Z][^_A-Z]*|_", width)  # The lines of the name.
        found = [match for line in parts for match in LINT_TRIGGERS.findall(line)]  # The names in the lines.
        return parts if found == LINT_TRIGGERS.findall(word) else [word]

    @staticmethod
    def split_parts(text: str, pattern: str, width: int) -> list[str]:
        """Join the parts of ``text`` that ``pattern`` finds into lines of ``width`` characters or fewer.

        A single part that is longer than the limit stays on one line.
        """
        lines: list[str] = []
        current = ""
        for part in re.findall(pattern, text):
            if current and len(current) + len(part) > width:  # The part does not fit.
                lines.append(current)
                current = part
            else:
                current += part
        if current:
            lines.append(current)
        return lines or [text]

    @staticmethod
    def family(use: EndpointUse) -> str:
        """Return the SDK family of one endpoint, such as orgs/sites."""
        if use.method == "WS":  # A WebSocket channel.
            return WS_FAMILY
        if not use.sdk:  # A raw request.
            return RAW_FAMILY
        module = use.sdk.rsplit(".", 1)[0].removeprefix("api.v1.")  # For example orgs.sites.
        return module.replace(".", "/")  # For example orgs/sites.

    @staticmethod
    def families(result: MenuResult) -> list[str]:
        """Return the SDK families of one menu, with the largest family first."""
        counts = Counter(MermaidDiagram.family(use) for use in result.endpoints)  # Endpoints for each family.
        return [name for name, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]

    @staticmethod
    def node_id(family: str) -> str:
        """Return the node identifier of one family."""
        return "f_" + re.sub(r"[^a-z0-9]+", "_", family.lower()).strip("_")  # For example f_orgs_sites.

    @staticmethod
    def overview(category: str, results: list[MenuResult]) -> str:
        """Return the flowchart that links a category to the SDK families that its menu options use.

        Each family node shows the number of menu options that use the family.
        The diagram is a star with one root, so no two edges cross. An earlier
        form linked each menu option to each of its families, and it grew to
        thousands of pixels of crossing edges that a person could not read.
        """
        usage = Counter(name for result in results for name in MermaidDiagram.families(result))  # Menus per family.
        ranked = sorted(usage.items(), key=lambda item: (-item[1], item[0]))  # The most used family first.
        root = f"{MermaidDiagram.label(category)}: {MermaidDiagram.count_text_plain(len(results), 'menu option')}"
        lines = [
            f"{FENCE}mermaid",
            "flowchart LR",
            f'    root["{MermaidDiagram.wrap(root)}"]',
        ]  # The header and the root.
        for name, count in ranked[:MAX_OVERVIEW_FAMILIES]:  # One node for each of the most used families.
            used_by = MermaidDiagram.count_text_plain(count, "menu option")  # Such as 3 menu options.
            lines.append(f'    root --> {MermaidDiagram.node_id(name)}["{name}{LINE_BREAK}{used_by}"]')
        if len(ranked) > MAX_OVERVIEW_FAMILIES:  # Summarize the other families in one node.
            more = MermaidDiagram.count_text(len(ranked) - MAX_OVERVIEW_FAMILIES, "family", "families")
            lines.append(f'    root --> more["{more}"]')
        lines.append(FENCE)  # Close the fence.
        return "\n".join(lines)

    @staticmethod
    def count_text_plain(count: int, singular: str) -> str:
        """Return a count with its noun, such as 1 menu option or 3 menu options."""
        return f"{count} {singular if count == 1 else singular + 's'}"  # One noun form for each count.

    @staticmethod
    def count_text(count: int, singular: str, plural: str) -> str:
        """Return the text of a summary node, such as 1 more family or 3 more families."""
        return f"{count} more {singular if count == 1 else plural}"  # One noun form for each count.

    @staticmethod
    def caller(use: EndpointUse) -> str:
        """Return the class, the function, or the constant that holds one endpoint."""
        if not use.holder:  # The handler expression itself holds the fact.
            return ROOT_CALLER
        member = use.holder.split(":", 1)[-1]  # For example SiteExporter.export.
        return member.split(".", 1)[0]  # The top-level owner, for example SiteExporter.

    @staticmethod
    def callers(result: MenuResult) -> list[tuple[str, list[EndpointUse]]]:
        """Return each caller of one menu option with its endpoints, with the largest caller first."""
        grouped: dict[str, list[EndpointUse]] = {}  # Caller label to its endpoints, in table order.
        for use in result.endpoints:  # Put each endpoint under the owner that sends it.
            grouped.setdefault(MermaidDiagram.caller(use), []).append(use)
        return sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))  # A stable order.

    @staticmethod
    def endpoint_label(use: EndpointUse) -> str:
        """Return the label of one endpoint node: the HTTP method and the request path."""
        method = "Unknown" if use.method == "?" else use.method  # The code does not state the method.
        cleaned = " ".join(PATH_UNSAFE.sub(" ", use.path).split())  # Keep the path braces, and drop other marks.
        return LINE_BREAK.join([method, *MermaidDiagram.path_lines(cleaned)])  # The method on its own line.

    @staticmethod
    def path_lines(path: str) -> list[str]:
        """Split a request path at its slashes into lines of MAX_PATH_LINE characters or fewer.

        A single segment that is longer than the limit stays on one line.
        """
        return MermaidDiagram.split_parts(path, r"/?[^/]+|/", MAX_PATH_LINE)  # Each segment keeps its slash.

    @staticmethod
    def breakdown(result: MenuResult) -> str:
        """Return the flowchart that links one menu option to its callers, and each caller to its endpoints."""
        lines = [f"{FENCE}mermaid", "flowchart LR", f'    menu["{MermaidDiagram.menu_label(result)}"]']  # The header.
        shown = 0  # The number of endpoint nodes in the diagram.
        for number, (name, uses) in enumerate(MermaidDiagram.callers(result), start=1):  # One node for each caller.
            if shown >= MAX_BREAKDOWN:  # The diagram is full. The table lists the rest.
                break
            lines.append(f'    menu --> c{number}["{MermaidDiagram.wrap(MermaidDiagram.label(name))}"]')
            for use in uses[: MAX_BREAKDOWN - shown]:  # One node for each endpoint of this caller.
                shown += 1
                lines.append(f'    c{number} --> e{shown}["{MermaidDiagram.endpoint_label(use)}"]')
        hidden = len(result.endpoints) - shown  # The endpoints that only the table lists.
        if hidden:  # Summarize the rest in one node.
            lines.append(
                f'    menu --> more["{MermaidDiagram.wrap(MermaidDiagram.count_text(hidden, "endpoint", "endpoints") + " in the table")}"]'
            )
        lines.append(FENCE)  # Close the fence.
        return "\n".join(lines)

    @staticmethod
    def request_path() -> str:
        """Return the flowchart that shows how a menu option reaches the Mist cloud."""
        return "\n".join(
            [
                f"{FENCE}mermaid",
                "flowchart TB",
                '    operator["Operator"] --> menu["Menu option in MistHelper.py"]',
                '    menu --> handler["Handler class below src/"]',
                '    handler --> helpers["Shared helpers: input, cache, and export"]',
                '    handler --> sdk["mistapi SDK function"]',
                "    helpers --> sdk",
                '    sdk --> https["HTTPS request to /api/v1/"]',
                '    handler --> ws["WebSocket channel"]',
                '    https --> cloud["Mist cloud"]',
                "    ws --> cloud",
                '    handler --> output["CSV, SQLite, or ArangoDB and Redis"]',
                FENCE,
            ]
        )

    @staticmethod
    def method() -> str:
        """Return the flowchart that shows how the tool builds the map."""
        return "\n".join(
            [
                f"{FENCE}mermaid",
                "flowchart TB",
                '    table["menu_actions table in MistHelper.py"] --> handler["Handler expression"]',
                '    handler --> walk["Breadth-first walk of the call graph"]',
                '    walk --> stop["Stop at a shared helper"]',
                '    walk --> facts["SDK calls, request paths, and channels"]',
                '    sdk["Vendored SDK index"] --> facts',
                '    curated["Curated rules"] --> walk',
                '    facts --> pages["Map pages and wiki pages"]',
                FENCE,
            ]
        )

    @staticmethod
    def category_pie(counts: list[tuple[str, int]]) -> str:
        """Return the pie chart of the menu options in each category."""
        lines = [f"{FENCE}mermaid", "pie showData", "    title Menu options in each category"]  # The header.
        lines.extend(f'    "{name}" : {count}' for name, count in counts)  # One slice for each category.
        lines.append(FENCE)  # Close the fence.
        return "\n".join(lines)
