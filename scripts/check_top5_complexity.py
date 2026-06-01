"""Check cyclomatic complexity for the five spec-195 target functions."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

TARGETS = {
    "MistHelper.py": [
        "_early_dependency_check",
        "_execute_site_capture_loop",
        "start_org_packet_capture",
        "device_events_52w",
        "with_wan_overrides",
    ],
}


def _run_radon(path: str) -> list[dict[str, object]]:
    """Run radon CC in JSON mode and return function records."""
    command = [sys.executable, "-m", "radon", "cc", path, "-j"]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"radon failed for {path}: {result.stderr.strip()}")
    payload = json.loads(result.stdout or "{}")
    records: list[dict[str, object]] = []
    for file_path, blocks in payload.items():
        for block in blocks:
            record = {
                "file": file_path,
                "name": block.get("name"),
                "complexity": block.get("complexity"),
                "rank": block.get("rank"),
                "line": block.get("lineno"),
            }
            records.append(record)
    return records


def main() -> int:
    """Print target complexity table and fail if any target exceeds CC 10."""
    all_records: list[dict[str, object]] = []
    for path in TARGETS:
        if not Path(path).exists():
            raise FileNotFoundError(f"Missing path: {path}")
        all_records.extend(_run_radon(path))
    target_rows: list[dict[str, object]] = []
    for file_name, target_names in TARGETS.items():
        for target_name in target_names:
            match = next(
                (row for row in all_records if row["file"].endswith(file_name) and row["name"] == target_name),
                None,
            )
            if match is None:
                raise RuntimeError(f"Target function not found in radon output: {target_name}")
            target_rows.append(match)
    print("Target cyclomatic complexity results:")
    for row in target_rows:
        print(f"- {row['name']}: CC={row['complexity']} Rank={row['rank']} " f"({row['file']}:{row['line']})")
    failed = [row for row in target_rows if int(row["complexity"]) > 10]
    if failed:
        print("\nFAIL: One or more target functions exceed CC 10")
        return 1
    print("\nPASS: All target functions are CC <= 10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
