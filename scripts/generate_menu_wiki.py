#!/usr/bin/env python3
"""Generate wiki-ready Markdown for the MistHelper GitHub Wiki."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


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
        self.output_path = self.repo_root / "documentation" / "wiki" / "Menu-Reference.md"

    def generate(self) -> None:
        source = self.source_path.read_text(encoding="utf-8")
        entries = self.extract_entries(source)
        categories = self.build_categories()
        markdown = self.render_markdown(entries, categories)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(markdown, encoding="utf-8")
        print(f"WROTE {self.output_path}")

    def extract_entries(self, source: str) -> list[MenuEntry]:
        tree = ast.parse(source, filename=str(self.source_path))
        menu_dict = self.find_menu_actions(tree)
        entries: list[MenuEntry] = []
        for key_node, value_node in zip(menu_dict.keys, menu_dict.values, strict=True):
            menu_id = self.extract_menu_id(key_node)
            handler, description = self.extract_value_pair(value_node)
            entries.append(MenuEntry(menu_id, description, self.classify_safety(description, handler), handler))
        return sorted(entries, key=lambda entry: entry.menu_id)

    def find_menu_actions(self, tree: ast.AST) -> ast.Dict:
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "menu_actions":
                        if isinstance(node.value, ast.Dict):
                            return node.value
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

    def classify_safety(self, description: str, handler: str) -> str:
        haystack = f"{description} {handler}".upper()
        if "DESTRUCTIVE" in haystack:
            return "Destructive"
        if "INTERACTIVE" in haystack or "STREAM" in haystack:
            return "Interactive"
        return "Safe"

    def build_categories(self) -> list[CategorySummary]:
        return [
            CategorySummary("0", "Exit", "Exit and session control"),
            CategorySummary("1-4", "Alarms & Definitions", "Org alarms, device events, audit logs, and gateway management IPs"),
            CategorySummary("5-8", "WebSocket Commands", "MAC table, forwarding table, routing table, and SSR/SRX routing tools"),
            CategorySummary("9-10", "Packet Capture", "Site and org packet capture workflows with WebSocket streaming"),
            CategorySummary("11-15", "Org Inventory Core", "Sites, inventory, device stats, port stats, and VPN peer stats"),
            CategorySummary("16-19", "Gateway Exports", "Synthetic tests, device lists, site settings, and test results"),
            CategorySummary("20-28", "Location & Enrichment", "Sites, gateways, devices, guests, VC stats, combined inventory, and WAN overrides"),
            CategorySummary("29-34", "Site-Scoped", "Per-site ports, clients, devices, stats, VC, and Wi-Fi clients"),
            CategorySummary("35-39", "Template Bundles", "All templates plus network, RF, AP, and switch subsets"),
            CategorySummary("40-44", "Clients & Security", "Wireless and wired clients, security events, rogue clients, and rogue APs"),
            CategorySummary("45-53", "Configuration", "Licenses, PSKs, webhooks, WLANs, beacons, maps, zones, and insights"),
            CategorySummary("54-59", "Admin & Org Mgmt", "API tokens, admins, MSP info, SSO, usage, and MX Edge"),
            CategorySummary("60-62", "Monitoring / Analytics", "Firmware status, inventory comparison, and Marvis troubleshooting"),
            CategorySummary("63-65", "WIP Bulk History", "52-week device events, 52-week audit logs, and gateway configs"),
            CategorySummary("66-69", "Insights API", "Org SLE metrics, site summaries, site insights, and client insights"),
            CategorySummary("70-74", "Interactive Views", "Site selection, inventory browser, device stats, tests, and config views"),
            CategorySummary("75-76", "Continuous Loops", "Continuous collection and refresh loops"),
            CategorySummary("77-78", "Processing & Support", "SFP merge and support package generation"),
            CategorySummary("79-80", "CLI / WebSocket", "Interactive CLI shell and ARP via WebSocket"),
            CategorySummary("81-86", "Advanced Insights", "Device insights and anomaly event exports"),
            CategorySummary("87-89", "WebSocket Device Commands", "Real-time ping, ARP, and service ping streams"),
            CategorySummary("90-100", "Destructive Operations", "Firmware upgrades, reboots, VC operations, SSH runner, and switch/SSR firmware"),
            CategorySummary("101-114", "Advanced Configuration", "TUI, RADIUS timers, WAN2 migration, template config, test-site creation, WAN probe, and maps"),
            CategorySummary("115-121", "Access / MSP / Health", "Interactive login, org firmware, MSP inventory, auto-upgrade, and health analysis"),
            CategorySummary("122-160", "Device Utilities & Reports", "Bulk WLAN config, device commands, clear actions, DHCP, snapshots, offline reports, SSID consolidation, and E911"),
        ]

    def render_markdown(self, entries: list[MenuEntry], categories: list[CategorySummary]) -> str:
        lines: list[str] = []
        lines.extend([
            "# Menu Reference",
            "",
            f"Operation Count: MistHelper currently defines {len(entries)} actionable menu entries (0-160) with some gaps for future expansion.",
            "",
            "Below is the authoritative list derived directly from `menu_actions` in code. WIP = unstable schema, DESTRUCTIVE = requires explicit user confirmation.",
            "",
            "## Important Notes",
            "",
            "- Options 14 and 18 are resource-intensive and may take a long time during large exports.",
            "- Options 63-65 are intentionally marked WIP and may evolve as the bulk-history workflows settle.",
            "- Destructive ranges should never be scripted unattended without explicit human review and confirmation.",
            "",
            "## Operation Categories",
            "",
            "| Range | Category | Summary |",
            "|---|---|---|",
        ])
        for category in categories:
            lines.append(f"| {category.menu_range} | {self.escape(category.title)} | {self.escape(category.summary)} |")
        lines.extend([
            "",
            "## Full Menu Table",
            "",
            "| Menu ID | Short description | Safety | Callable/Handler |",
            "|---:|---|---|---|",
        ])
        for entry in entries:
            lines.append(
                f"| {entry.menu_id} | {self.escape(entry.description)} | {entry.safety} | `{self.escape(entry.handler)}` |"
            )
        lines.extend([
            "",
            "This page should be regenerated whenever `menu_actions` changes so the wiki stays aligned with `MistHelper.py`.",
        ])
        return "\n".join(lines) + "\n"

    def escape(self, text: str) -> str:
        return text.replace("|", "\\|")


if __name__ == "__main__":
    WikiMenuReferenceGenerator().generate()
