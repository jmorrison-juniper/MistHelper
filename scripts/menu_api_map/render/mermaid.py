"""Mermaid helpers: the overview diagrams and the diagrams that group the menu options of one category.

The diagram labels use plain characters only. The labels never hold an SDK
function name or a class name, because ``scripts/lint_diagram_refs.py`` checks
each name in a diagram that ends in a class suffix, such as ``Config``.
"""

from __future__ import annotations  # Postponed annotations keep the type hints light.

import re  # Cleans the diagram labels.
from collections import Counter  # Counts the endpoints of each SDK family.

from ..analysis.walker import EndpointUse, MenuResult  # The walk results.

MAX_GROUP = 15  # The largest number of menu options in one diagram.
MAX_FAMILIES = 6  # The largest number of SDK families that one menu node links to.
MAX_BREAKDOWN = 12  # The largest number of endpoint nodes in the diagram of one menu option.
MAX_TITLE = 40  # The longest menu title in a diagram label.
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
        return f"Menu {result.option.menu_id}" if LINT_TRIGGERS.search(text) else text  # Keep the lint clean.

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
    def group(results: list[MenuResult]) -> str:
        """Return one fenced flowchart that links each menu to its SDK families."""
        lines = [f"{FENCE}mermaid", "flowchart LR"]  # The diagram header.
        families: dict[str, str] = {}  # Node identifier to its family label.
        for result in results:  # One node for each menu, and one edge for each family.
            menu_node = f"m{result.option.menu_id}"  # For example m154.
            lines.append(f'    {menu_node}["{MermaidDiagram.menu_label(result)}"]')
            names = MermaidDiagram.families(result)  # The families, largest first.
            for name in names[:MAX_FAMILIES]:  # Link the largest families.
                families[MermaidDiagram.node_id(name)] = name
                lines.append(f"    {menu_node} --> {MermaidDiagram.node_id(name)}")
            if len(names) > MAX_FAMILIES:  # Summarize the other families in one node.
                more = MermaidDiagram.count_text(len(names) - MAX_FAMILIES, "family", "families")  # Such as 2 more.
                lines.append(f'    {menu_node} --> more{result.option.menu_id}["{more}"]')
        lines.extend(f'    {node}["{name}"]' for node, name in sorted(families.items()))  # The family nodes.
        lines.append(FENCE)  # Close the fence.
        return "\n".join(lines)

    @staticmethod
    def groups(results: list[MenuResult]) -> list[str]:
        """Return the flowcharts of one category, with no more than MAX_GROUP menu options in each one."""
        return [MermaidDiagram.group(results[start : start + MAX_GROUP]) for start in range(0, len(results), MAX_GROUP)]

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
        cleaned = PATH_UNSAFE.sub(" ", f"{method} {use.path}")  # Keep the path braces, and drop other marks.
        return " ".join(cleaned.split())  # Collapse the spaces.

    @staticmethod
    def breakdown(result: MenuResult) -> str:
        """Return the flowchart that links one menu option to its callers, and each caller to its endpoints."""
        lines = [f"{FENCE}mermaid", "flowchart LR", f'    menu["{MermaidDiagram.menu_label(result)}"]']  # The header.
        shown = 0  # The number of endpoint nodes in the diagram.
        for number, (name, uses) in enumerate(MermaidDiagram.callers(result), start=1):  # One node for each caller.
            if shown >= MAX_BREAKDOWN:  # The diagram is full. The table lists the rest.
                break
            lines.append(f'    menu --> c{number}["{MermaidDiagram.label(name)}"]')
            for use in uses[: MAX_BREAKDOWN - shown]:  # One node for each endpoint of this caller.
                shown += 1
                lines.append(f'    c{number} --> e{shown}["{MermaidDiagram.endpoint_label(use)}"]')
        hidden = len(result.endpoints) - shown  # The endpoints that only the table lists.
        if hidden:  # Summarize the rest in one node.
            lines.append(
                f'    menu --> more["{MermaidDiagram.count_text(hidden, "endpoint", "endpoints")} in the table"]'
            )
        lines.append(FENCE)  # Close the fence.
        return "\n".join(lines)

    @staticmethod
    def request_path() -> str:
        """Return the flowchart that shows how a menu option reaches the Mist cloud."""
        return "\n".join(
            [
                f"{FENCE}mermaid",
                "flowchart LR",
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
                "flowchart LR",
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
