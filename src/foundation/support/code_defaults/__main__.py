"""Run the local inventory and first-batch regression guard."""

import argparse
import json
import logging
import sys
from pathlib import Path

from src.foundation.support.code_defaults.inventory import Candidate, InventoryScanner
from src.foundation.support.code_defaults.policy import FIRST_BATCH_SCOPE, GuardPolicy, GuardResult

_LOGGER = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    """Build the scan and guard command interface."""
    parser = argparse.ArgumentParser(description="Inventory empty defaults in tracked Python source.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("scan", "guard"):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, default=Path("."))
    commands.choices["guard"].add_argument(
        "--baseline",
        type=Path,
        default=Path(__file__).with_name("baseline.json"),
    )
    return parser


def _load_baseline(path: Path) -> dict[str, object]:
    """Read a JSON baseline and reject malformed or unreadable content."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"baseline is unreadable or invalid: {error}") from error
    if not isinstance(document, dict):
        raise ValueError("baseline must be a JSON object")
    return document


def _candidate_record(candidate: Candidate, policy: GuardPolicy) -> dict[str, object]:
    """Format one candidate with its reviewed status and ownership."""
    classification, evidence = policy.classify(candidate)
    owner = "outside_batch" if classification == "outside_batch" else "issue-2753"
    if classification == "excluded_ownership":
        owner = "issue-2863"
    return {
        "identity": candidate.identity,
        "path": candidate.path,
        "line": candidate.line,
        "column": candidate.column,
        "symbol": candidate.symbol,
        "shape": candidate.shape,
        "input_key": candidate.input_key,
        "default_kind": candidate.default_kind,
        "classification": classification or "unclassified",
        "ownership": owner,
        "evidence": evidence,
    }


def _run_scan(root: Path) -> int:
    """Print a deterministic repository-wide inventory."""
    inventory = InventoryScanner(root).scan()
    policy = GuardPolicy()
    records = [_candidate_record(candidate, policy) for candidate in inventory.candidates]
    counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    for record in records:
        category = str(record["classification"])
        counts[category] = counts.get(category, 0) + 1
        if category == "high":
            severity = "high"
        elif category == "outside_batch":
            severity = "outside_batch"
        elif category == "unclassified":
            severity = "unresolved"
        else:
            severity = "non_high"
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    invalid = bool(inventory.parse_failures) or "unclassified" in counts or not inventory.parsed_files
    document = {
        "revision": inventory.revision,
        "discovered_files": inventory.discovered_files,
        "parsed_files": inventory.parsed_files,
        "parse_failures": list(inventory.parse_failures),
        "candidate_count": len(records),
        "classification_totals": counts,
        "severity_totals": severity_counts,
        "candidates": records,
        "status": "invalid_input" if invalid else "completed",
    }
    print(json.dumps(document, ensure_ascii=True, sort_keys=True, indent=2))
    _LOGGER.info("Scanned %d tracked files and parsed %d files", inventory.discovered_files, inventory.parsed_files)
    return 2 if invalid else 0


def _run_guard(root: Path, baseline_path: Path) -> int:
    """Run the exact-scope guard and report its parsed-file count."""
    inventory = InventoryScanner(root).scan(FIRST_BATCH_SCOPE)
    try:
        baseline = _load_baseline(baseline_path)
        result = GuardPolicy().evaluate(inventory, baseline)
    except ValueError as error:
        result = GuardResult("invalid_input", str(error), inventory.parsed_files, 0)
    document = {
        "status": result.status,
        "message": result.message,
        "parsed_files": result.parsed_files,
        "discovered_files": inventory.discovered_files,
        "candidate_count": len(inventory.candidates),
        "accepted_high_total": result.accepted_total,
        "new_high": list(result.new_high),
        "removed_high": list(result.removed_high),
    }
    print(json.dumps(document, ensure_ascii=True, sort_keys=True, indent=2))
    _LOGGER.info("Guard status %s after parsing %d files", result.status, result.parsed_files)
    return {"passed": 0, "regression": 1, "invalid_input": 2}[result.status]


def main(arguments: list[str] | None = None) -> int:
    """Dispatch the local command and convert invalid inputs to exit status two."""
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(levelname)s %(message)s")
    options = _build_parser().parse_args(arguments)
    try:
        if options.command == "scan":
            return _run_scan(options.root)
        return _run_guard(options.root, options.baseline)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "invalid_input", "message": str(error)}, ensure_ascii=True))
        _LOGGER.error("Command input failed: %s", error)
        return 2


if __name__ == "__main__":
    sys.exit(main())
