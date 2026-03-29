"""Diagram Reference Validator for MistHelper Mermaid documentation.

Validates that identifiers in Mermaid diagram code blocks correspond to
real Python symbols in the codebase. Runs in CI to prevent stale diagrams.

Exit codes: 0 = all valid, 1 = stale references found, 2 = script error.
"""

import argparse
import ast
import logging
import re
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

BUILT_IN_ALLOWLIST = frozenset([
    "API", "SSH", "CSV", "SQLite", "GHCR", "CI", "CD", "UUID", "PK", "ER",
    "EOF", "MistHelper", "GitHub", "Podman", "Docker", "Flask", "Gunicorn",
    "Mermaid", "Ruff", "Bandit", "CodeQL", "Playwright", "WebSocket",
    "ForceCommand", "NOC", "TCP", "UDP", "VLAN", "BSSID", "MAC", "JSON",
    # Mermaid diagram participant/label terms (not Python symbols)
    "User", "Menu", "Fetch", "Rate", "Process", "Export", "Select",
    "Write", "Upsert", "Accumulate", "GET", "POST", "PUT", "DELETE",
    # Overview-level group labels (plural forms, not class names)
    "InfrastructureCore", "ConfigObjects", "Utilities", "APIFetching",
    "DataProcessing", "OrgExporters", "SiteExporters", "GatewayExporters",
    "WebSocketNet", "Managers", "UITUI", "SystemRegistry", "OrgExporter",
    "SiteExporter", "GatewayExporter", "MigrationManager",
])

CLASS_SUFFIX_PATTERN = re.compile(
    r"[A-Z][a-zA-Z]+(?:Utils|Manager|Exporter|Config|Runner|Writer"
    r"|Fetcher|Processor|Checker|Monitor|Emitter|Registry|TUI)"
)


class DiagramReferenceValidator:
    """Validates Mermaid diagram references against Python codebase symbols."""

    def __init__(self, allowlist: frozenset[str] | None = None):
        self.allowlist = allowlist or BUILT_IN_ALLOWLIST
        self.python_symbols: set[str] = set()
        self.stale_references: list[dict] = []
        self.total_checked = 0
        self.files_scanned = 0

    def extract_mermaid_blocks(self, content: str) -> list[str]:
        """Extract Mermaid code blocks from markdown content."""
        pattern = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
        return pattern.findall(content)

    def extract_identifiers(self, block: str) -> list[str]:
        """Extract class/method identifiers from a Mermaid code block."""
        identifiers: list[str] = []
        identifiers.extend(self._extract_class_diagram_ids(block))
        identifiers.extend(self._extract_sequence_ids(block))
        identifiers.extend(self._extract_suffix_matches(block))
        return list(set(identifiers))

    def _extract_class_diagram_ids(self, block: str) -> list[str]:
        """Extract identifiers from classDiagram syntax."""
        results: list[str] = []
        for match in re.finditer(r"class\s+(\w+)", block):
            name = match.group(1)
            if name[0].isupper():
                results.append(name)
        for match in re.finditer(r"(\w+)\s*:\s*(\w+)\(\)", block):
            results.append(match.group(1))
            results.append(match.group(2))
        for match in re.finditer(
            r"(\w+)\s*<\|--\s*(\w+)", block
        ):
            results.append(match.group(1))
            results.append(match.group(2))
        return results

    def _extract_sequence_ids(self, block: str) -> list[str]:
        """Extract identifiers from sequenceDiagram syntax."""
        results: list[str] = []
        for match in re.finditer(
            r"participant\s+(\w+)(?:\s+as\s+(.+))?", block
        ):
            name = match.group(1)
            if name[0].isupper():
                results.append(name)
        for match in re.finditer(r"(\w+)->>(\w+):\s*(\w+)", block):
            for group_idx in range(1, 4):
                name = match.group(group_idx)
                if name and name[0].isupper():
                    results.append(name)
        return results

    def _extract_suffix_matches(self, block: str) -> list[str]:
        """Extract PascalCase names matching known class suffixes."""
        return CLASS_SUFFIX_PATTERN.findall(block)

    def extract_python_symbols(self, source_path: Path) -> set[str]:
        """Extract class/function names from Python source via AST."""
        try:
            source_text = source_path.read_text(encoding="utf-8")
            tree = ast.parse(source_text, filename=str(source_path))
        except (SyntaxError, OSError) as exc:
            logger.error("Failed to parse %s: %s", source_path, exc)
            return set()

        symbols: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                symbols.add(node.name)
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        symbols.add(item.name)
            elif isinstance(node, ast.FunctionDef):
                symbols.add(node.name)
        return symbols

    def find_closest_match(self, name: str) -> str | None:
        """Find closest Python symbol by edit distance."""
        if not self.python_symbols:
            return None
        best_match = min(
            self.python_symbols,
            key=lambda s: self._edit_distance(name.lower(), s.lower()),
        )
        distance = self._edit_distance(name.lower(), best_match.lower())
        if distance <= len(name) // 2:
            return f"{best_match} (edit distance: {distance})"
        return None

    def _edit_distance(self, first: str, second: str) -> int:
        """Levenshtein edit distance between two strings."""
        if len(first) < len(second):
            return self._edit_distance(second, first)
        if not second:
            return len(first)
        prev_row = list(range(len(second) + 1))
        for i, char_a in enumerate(first):
            curr_row = [i + 1]
            for j, char_b in enumerate(second):
                cost = 0 if char_a == char_b else 1
                curr_row.append(min(
                    curr_row[j] + 1,
                    prev_row[j + 1] + 1,
                    prev_row[j] + cost,
                ))
            prev_row = curr_row
        return prev_row[-1]

    def validate_file(self, filepath: Path, verbose: bool = False) -> int:
        """Validate all Mermaid references in a single markdown file."""
        try:
            content = filepath.read_text(encoding="utf-8")
        except OSError as exc:
            logger.error("Cannot read %s: %s", filepath, exc)
            return 0

        blocks = self.extract_mermaid_blocks(content)
        if not blocks:
            return 0

        self.files_scanned += 1
        lines = content.split("\n")
        file_stale = 0

        for block in blocks:
            identifiers = self.extract_identifiers(block)
            for name in identifiers:
                if name in self.allowlist:
                    continue
                self.total_checked += 1
                if name in self.python_symbols:
                    if verbose:
                        logger.info("  OK: %s:%s", filepath, name)
                    continue
                line_num = self._find_line_number(lines, name)
                closest = self.find_closest_match(name)
                self.stale_references.append({
                    "file": str(filepath),
                    "line": line_num,
                    "name": name,
                    "closest": closest,
                })
                file_stale += 1
        return file_stale

    def _find_line_number(self, lines: list[str], name: str) -> int:
        """Find the 1-based line number where name first appears."""
        for idx, line in enumerate(lines, start=1):
            if name in line:
                return idx
        return 0

    def run(self, config: argparse.Namespace) -> int:
        """Execute full validation pipeline. Returns exit code."""
        for source_path in config.source_files:
            path = Path(source_path)
            if not path.exists():
                logger.error("Source file not found: %s", path)
                return 2
            self.python_symbols.update(
                self.extract_python_symbols(path)
            )

        if not self.python_symbols:
            logger.error("No Python symbols extracted")
            return 2

        markdown_files = self._collect_markdown_files(config)
        if not markdown_files:
            logger.error("No markdown files found")
            return 2

        for md_file in markdown_files:
            self.validate_file(md_file, verbose=config.verbose)

        return self._report_results()

    def _collect_markdown_files(
        self, config: argparse.Namespace
    ) -> list[Path]:
        """Collect all markdown files to scan."""
        files: list[Path] = []
        docs_dir = Path(config.docs_dir)
        if docs_dir.exists():
            files.extend(docs_dir.rglob("*.md"))

        for extra in config.extra_files:
            path = Path(extra)
            if path.exists():
                files.append(path)
        return sorted(set(files))

    def _report_results(self) -> int:
        """Print results and return exit code."""
        if self.stale_references:
            for ref in self.stale_references:
                msg = (
                    f'STALE: {ref["file"]}:{ref["line"]}'
                    f' "{ref["name"]}" not found in codebase'
                )
                logger.warning(msg)
                if ref["closest"]:
                    logger.warning("  Closest match: %s", ref["closest"])
            logger.warning(
                "\nFAILED: %d stale references found across %d diagram files",
                len(self.stale_references),
                self.files_scanned,
            )
            return 1

        logger.info(
            "OK: %d references validated across %d diagram files",
            self.total_checked,
            self.files_scanned,
        )
        return 0


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Validate Mermaid diagram references against codebase"
    )
    parser.add_argument(
        "--docs-dir",
        default="documentation/diagrams/",
        help="Directory containing diagram markdown files",
    )
    parser.add_argument(
        "--extra-files",
        nargs="*",
        default=["README.md"],
        help="Additional markdown files with inline diagrams",
    )
    parser.add_argument(
        "--source-files",
        nargs="*",
        default=["MistHelper.py"],
        help="Python source files to extract symbols from",
    )
    parser.add_argument(
        "--allowlist",
        default=None,
        help="File of identifiers to skip (one per line)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print all checked references",
    )
    return parser


def main() -> int:
    """Entry point for the lint script."""
    parser = build_parser()
    args = parser.parse_args()

    if args.allowlist:
        allowlist_path = Path(args.allowlist)
        if allowlist_path.exists():
            extra = frozenset(
                line.strip()
                for line in allowlist_path.read_text().splitlines()
                if line.strip() and not line.startswith("#")
            )
            validator = DiagramReferenceValidator(
                BUILT_IN_ALLOWLIST | extra
            )
        else:
            logger.error("Allowlist file not found: %s", allowlist_path)
            return 2
    else:
        validator = DiagramReferenceValidator()

    return validator.run(args)


if __name__ == "__main__":
    sys.exit(main())
