"""Fail CI when retired compatibility symbols are referenced in internal code."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

RETIRED_PATTERNS = {
    "get_csv_file_path_legacy": re.compile(r"\bget_csv_file_path_legacy\b"),
    "export_gateway_templates_to_csv_legacy": re.compile(r"\bexport_gateway_templates_to_csv_legacy\b"),
    "InsightMetricsUtils.export_legacy": re.compile(r"\bInsightMetricsUtils\s*\.\s*export_legacy\b"),
}

SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "specs",
    "abandoned-specs",
    "finished-specs",
    "junk",
    "data",
}

SKIP_PATH_PARTIALS = (
    "check_retired_compat_symbols.py",
    "baseline-internal-references.txt",
)

SCAN_SUFFIXES = {".py"}


def should_skip_file(file_path: Path) -> bool:
    """Return True when file should not be scanned by retired symbol guard."""
    if any(skip_name in file_path.parts for skip_name in SKIP_DIR_NAMES):
        return True
    text_path = file_path.as_posix()
    return any(partial in text_path for partial in SKIP_PATH_PARTIALS)


def collect_python_files() -> list[Path]:
    """Collect repository Python files excluding generated/spec artifacts."""
    collected_files: list[Path] = []
    for candidate in REPO_ROOT.rglob("*"):
        if not candidate.is_file():
            continue
        if candidate.suffix not in SCAN_SUFFIXES:
            continue
        if should_skip_file(candidate):
            continue
        collected_files.append(candidate)
    return collected_files


def find_violations() -> list[str]:
    """Scan Python files for banned retired-symbol references."""
    violations: list[str] = []
    for file_path in collect_python_files():
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        for symbol_name, symbol_pattern in RETIRED_PATTERNS.items():
            for line_number, line_text in enumerate(content.splitlines(), start=1):
                if symbol_pattern.search(line_text):
                    violations.append(
                        f"{file_path.relative_to(REPO_ROOT)}:{line_number}: retired symbol '{symbol_name}' referenced"
                    )
    return violations


def main() -> int:
    """Run retired compatibility symbol guard."""
    violations = find_violations()
    if not violations:
        print("Retired compatibility symbol guard passed.")
        return 0
    print("Retired compatibility symbol guard failed. Remove these references:")
    for violation in violations:
        print(f"  - {violation}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
