#!/usr/bin/env python3
"""Generate wiki-ready Markdown for the MistHelper GitHub Wiki."""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

# Display names and one-line explanations for each registry category.
_CATEGORY_TITLES = {
    "safe": "Safe org exports",
    "interactive_safe": "Interactive safe",
    "destructive": "Destructive",
    "interactive": "Interactive",
    "websocket": "WebSocket",
    "resource_intensive": "Resource intensive",
    "continuous_loop": "Continuous loop",
}

_CATEGORY_SUMMARIES = {
    "safe": "Read-only org exports. The --test run includes them.",
    "interactive_safe": "Read-only, but they prompt for a site or a device. The --testinteractive run includes them.",
    "destructive": "They change the Mist cloud configuration. Each one needs a typed confirmation.",
    "interactive": "They prompt the operator, so no automated run includes them.",
    "websocket": "They open a WebSocket stream to a device.",
    "resource_intensive": "They run long or fetch a large payload.",
    "continuous_loop": "They loop until the operator stops them.",
}


@dataclass(frozen=True)
class MenuEntry:
    """Single menu action extracted from ``MistHelper.py``."""

    menu_id: int
    description: str
    safety: str
    handler: str


@dataclass(frozen=True)
class CategorySummary:
    """Wiki category row describing a menu range."""

    menu_range: str
    title: str
    summary: str


class WikiMenuReferenceGenerator:
    """Build the wiki menu reference directly from the canonical source file."""

    def __init__(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.source_path = self.repo_root / "MistHelper.py"
        # Both files hold the same content, so the wiki and the repository copy cannot diverge.
        self.output_paths = (
            self.repo_root / "documentation" / "wiki" / "Menu-Reference.md",
            self.repo_root / "documentation" / "menu_reference.md",
        )

    def generate(self) -> None:
        source = self.source_path.read_text(encoding="utf-8")
        entries = self.extract_entries(source)
        categories = self.build_categories()
        markdown = self.render_markdown(entries, categories)
        for output_path in self.output_paths:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")
            print(f"WROTE {output_path}")

    def extract_entries(self, source: str) -> list[MenuEntry]:
        tree = ast.parse(source, filename=str(self.source_path))
        menu_dict = self.find_menu_actions(tree)
        registry = self.load_registry()
        entries: list[MenuEntry] = []
        for key_node, value_node in zip(menu_dict.keys, menu_dict.values, strict=True):
            menu_id = self.extract_menu_id(key_node)
            handler, description = self.extract_value_pair(value_node)
            category = registry.get(menu_id, "unregistered")
            entries.append(MenuEntry(menu_id, description, _CATEGORY_TITLES.get(category, category), handler))
        return sorted(entries, key=lambda entry: entry.menu_id)

    def find_menu_actions(self, tree: ast.AST) -> ast.Dict:
        for node in ast.walk(tree):
            # `menu_actions` carries a type annotation, so the node is AnnAssign, not Assign.
            targets: list[ast.expr] = []
            value: ast.expr | None = None
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
                value = node.value
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
                value = node.value
            else:
                continue
            for target in targets:
                if isinstance(target, ast.Name) and target.id == "menu_actions":
                    if isinstance(value, ast.Dict):
                        return value
        raise SystemExit("menu_actions not found")

    def extract_menu_id(self, key_node: ast.expr | None) -> int:
        if key_node is None:
            raise SystemExit("Unexpected empty menu_actions key")
        if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
            return int(key_node.value)
        raise SystemExit("Unexpected menu_actions key format")

    def extract_value_pair(self, value_node: ast.AST) -> tuple[str, str]:
        if not isinstance(value_node, ast.Tuple) or len(value_node.elts) < 2:
            raise SystemExit("Unexpected menu_actions value format")
        handler_node = value_node.elts[0]
        description_node = value_node.elts[1]
        handler = ast.unparse(handler_node).strip()
        description = self.extract_string(description_node)
        return handler, description

    def extract_string(self, node: ast.AST) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return " ".join(node.value.split())
        raise SystemExit("Unexpected description format")

    def load_registry(self) -> dict[int, str]:
        """Return the menu number to category map from the single source of truth."""
        sys.path.insert(0, str(self.repo_root))
        from src.utils.operation_registry import OperationRegistry

        return {
            int(option): OperationRegistry.skip_category(option)
            for option in OperationRegistry.registered_options()
            if option.isdigit()
        }

    def build_categories(self) -> list[CategorySummary]:
        """Build one summary row per registry category, with the spans computed from the data."""
        buckets: dict[str, list[int]] = defaultdict(list)
        for menu_id, category in self.load_registry().items():
            buckets[category].append(menu_id)
        rows: list[CategorySummary] = []
        for category in sorted(buckets, key=lambda name: -len(buckets[name])):
            numbers = sorted(buckets[category])
            rows.append(
                CategorySummary(
                    menu_range=self.compact_spans(numbers),
                    title=_CATEGORY_TITLES.get(category, category),
                    summary=f"{len(numbers)} operations. {_CATEGORY_SUMMARIES.get(category, '')}".strip(),
                )
            )
        return rows

    def compact_spans(self, numbers: list[int]) -> str:
        """Collapse a sorted number list into compact range notation such as ``1-13, 15-17``."""
        spans: list[str] = []
        start = previous = numbers[0]
        for number in numbers[1:]:
            if number == previous + 1:
                previous = number
                continue
            spans.append(f"{start}-{previous}" if start != previous else f"{start}")
            start = previous = number
        spans.append(f"{start}-{previous}" if start != previous else f"{start}")
        return ", ".join(spans)

    def render_markdown(self, entries: list[MenuEntry], categories: list[CategorySummary]) -> str:
        registry = self.load_registry()
        numbers = sorted(entry.menu_id for entry in entries)
        actionable = [n for n in numbers if n != 0]
        gaps = [n for n in range(numbers[0], numbers[-1] + 1) if n not in set(numbers)]
        heavy = self.compact_spans(sorted(n for n, c in registry.items() if c == "resource_intensive"))
        destructive = self.compact_spans(sorted(n for n, c in registry.items() if c == "destructive"))
        lines: list[str] = []
        lines.extend(
            [
                "# Menu Reference",
                "",
                "This page is generated. Run `python scripts/generate_menu_wiki.py` after any",
                "change to `menu_actions` in `MistHelper.py` or to `src/utils/operation_registry.py`.",
                "",
                f"MistHelper defines **{len(actionable)} actionable menu entries**, numbered",
                f"{actionable[0]} to {actionable[-1]}"
                + (f" with gaps at {self.compact_spans(gaps)}." if gaps else " with no gaps."),
                f"Menu 0 is Exit, so the registry holds {len(numbers)} entries in total.",
                "",
                "The Safety column reads from `src/utils/operation_registry.py`, which is the",
                "single source of truth. The classifier fails closed, so an unregistered option",
                "never runs in an automated test pass.",
                "",
                "## Important Notes",
                "",
                f"- Options {heavy} are resource intensive. They can run for a long time on a large org.",
                f"- Options {destructive} are destructive. They change the Mist cloud configuration.",
                "- Warning: Do not script a destructive option unattended. Each one needs a typed",
                "  confirmation from a human operator.",
                "",
                "## Operation Categories",
                "",
                "| Menu numbers | Category | Summary |",
                "|---|---|---|",
            ]
        )
        for category in categories:
            lines.append(f"| {category.menu_range} | {self.escape(category.title)} | {self.escape(category.summary)} |")
        lines.extend(
            [
                "",
                "## Full Menu Table",
                "",
                "| Menu ID | Short description | Safety | Callable/Handler |",
                "|---:|---|---|---|",
            ]
        )
        for entry in entries:
            description = self.escape(entry.description)
            handler = self.escape(entry.handler)
            lines.append(f"| {entry.menu_id} | {description} | {entry.safety} | `{handler}` |")
        lines.extend(
            [
                "",
                "This page should be regenerated whenever `menu_actions` or the operation registry",
                "changes, so the wiki stays aligned with the code.",
            ]
        )
        return "\n".join(lines) + "\n"

    def escape(self, text: str) -> str:
        return text.replace("|", "\\|")


if __name__ == "__main__":
    WikiMenuReferenceGenerator().generate()
