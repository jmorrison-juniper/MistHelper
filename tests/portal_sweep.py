"""Run one controlled sweep of portal operations with reviewer evidence."""

from __future__ import annotations

import argparse
import json
import pathlib
import queue
import sys
import threading
import time
import urllib.request
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from portal_harness import ARTIFACT_ROOT, DefectLog, PortalHarness, RunRecord

PORTAL = "http://127.0.0.1:8055"
WORKER_JOIN_TIMEOUT = 7200


def read_categories(base_url: str) -> list[dict[str, Any]]:
    """Return the category list the portal serves."""
    with urllib.request.urlopen(f"{base_url.rstrip('/')}/api/operations/list", timeout=60) as answer:
        return json.load(answer)["categories"]


def parse_csv_filter(value: str) -> set[str]:
    """Return a normalized set from a comma-separated filter."""
    return {item.strip() for item in value.split(",") if item.strip()}


def filter_categories(
    categories: list[dict[str, Any]], menus: set[str], category_filter: set[str]
) -> list[dict[str, Any]]:
    """Apply menu and category filters to the operation list."""
    filtered: list[dict[str, Any]] = []
    category_names = {name.lower() for name in category_filter}
    for category in categories:
        name = str(category.get("name", ""))
        if category_names and name.lower() not in category_names:
            continue
        operations = list(category.get("operations", []))
        if menus:
            operations = [operation for operation in operations if str(operation.get("menu_number")) in menus]
        if operations:
            clone = dict(category)
            clone["operations"] = operations
            filtered.append(clone)
    return filtered


class SweepRunner:
    """Drive portal operations and record what each run produced."""

    def __init__(self, round_number: int, workers: int, base_url: str) -> None:
        """Store sweep settings and build the shared work queue."""
        self.round_number = round_number
        self.workers = workers
        self.base_url = base_url.rstrip("/")
        self.work: queue.Queue = queue.Queue()
        self.lock = threading.Lock()
        self.results: list[RunRecord] = []
        self.started = time.monotonic()

    def load(self, categories: list[dict[str, Any]]) -> int:
        """Put one entry on the queue for each category and return the row count."""
        total = 0
        for category in categories:
            operations = [
                (str(operation["menu_number"]), str(operation.get("description", "")))
                for operation in category["operations"]
            ]
            self.work.put((str(category["name"]), operations))
            total += len(operations)
        return total

    def run(self) -> None:
        """Start the workers and wait for the queue to drain."""
        threads = []
        for index in range(self.workers):
            thread = threading.Thread(target=self._worker, args=(index,), daemon=True)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join(timeout=WORKER_JOIN_TIMEOUT)

    def _worker(self, index: int) -> None:
        """Take one category at a time and run every operation it holds."""
        while True:
            try:
                name, operations = self.work.get_nowait()
            except queue.Empty:
                return
            try:
                self._sweep_category(index, name, operations)
            except Exception as error:
                print(f"[w{index}] {name}: worker error {type(error).__name__}: {error}", flush=True)
            finally:
                self.work.task_done()

    def _sweep_category(self, index: int, name: str, operations: list[tuple[str, str]]) -> None:
        """Run every operation of one category inside a single browser."""
        log = DefectLog(category=name, round_number=self.round_number)
        print(f"[w{index}] {name}: {len(operations)} operations", flush=True)
        with PortalHarness(log, base_url=self.base_url) as harness:
            if not harness.open_category(name):
                print(f"[w{index}] {name}: the category did not open", flush=True)
                return
            for position, (number, description) in enumerate(operations, start=1):
                self._run_one(index, harness, name, number, description, position, len(operations))
        written = log.write()
        print(f"[w{index}] {name}: wrote {written}", flush=True)

    def _run_one(
        self, index: int, harness: PortalHarness, name: str, number: str, description: str, position: int, total: int
    ) -> None:
        """Run one operation and record the outcome."""
        started = time.monotonic()
        try:
            record = harness.run_operation(number, description)
        except Exception as error:
            log = harness.log
            log.add(number, "harness", "high", f"#{number} raised {type(error).__name__}", str(error)[:300], "")
            record = RunRecord(
                name,
                number,
                harness.rendered_label(number),
                f"harness-error:{type(error).__name__}",
                "",
                "",
                round(time.monotonic() - started, 2),
                None,
                None,
                {},
                list(harness.console_errors),
                list(harness.failed_requests),
                [],
                [],
                [],
                browser=harness.browser_label,
            )
            log.record(record)
        with self.lock:
            self.results.append(record)
        elapsed = time.monotonic() - started
        print(
            f"[w{index}] {name} {position}/{total}  menu {number:>4}  {record.verdict:<22} {elapsed:6.1f}s", flush=True
        )

    def report(self) -> tuple[pathlib.Path, pathlib.Path]:
        """Write the whole sweep to JSON and Markdown files."""
        target = ARTIFACT_ROOT / f"round{self.round_number}" / "_sweep-summary.json"
        markdown = ARTIFACT_ROOT / f"round{self.round_number}" / "_sweep-summary.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        duration = time.monotonic() - self.started
        states: dict[str, int] = {}
        for record in self.results:
            states[record.verdict] = states.get(record.verdict, 0) + 1
        ordered = sorted(self.results, key=lambda record: record.total_seconds, reverse=True)
        payload = {
            "round": self.round_number,
            "duration_seconds": round(duration, 1),
            "operations_run": len(self.results),
            "states": states,
            "runs": [record.as_dict() for record in ordered],
        }
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        markdown.write_text(render_markdown_summary(payload), encoding="utf-8")
        print(f"\nsweep finished in {duration / 60:.1f} minutes")
        print(f"operations run: {len(self.results)}")
        for state, count in sorted(states.items(), key=lambda pair: -pair[1]):
            print(f"  {state:<26} {count}")
        print(f"summary: {target}")
        print(f"markdown: {markdown}")
        return target, markdown


def render_markdown_summary(payload: dict[str, Any]) -> str:
    """Return a Markdown summary sorted slowest first."""
    lines = ["# Portal sweep summary", ""]
    lines.append(f"Round: {payload['round']}.")
    lines.append(f"Operations run: {payload['operations_run']}.")
    lines.append(f"Duration: {payload['duration_seconds']} seconds.")
    lines.append("")
    lines.append(
        "| Menu | Verdict | Total s | Handler s | Walk s | Console errors | "
        "Failed requests | Log errors | Screenshots |"
    )
    lines.append("| - | - | -: | -: | -: | -: | -: | -: | - |")
    for record in payload["runs"]:
        screenshots = "<br>".join(f"{key}: `{value}`" for key, value in record["screenshots"].items())
        lines.append(
            (
                "| {menu} | {verdict} | {total} | {handler} | {walk} | "
                "{console} | {failed} | {log_errors} | {screenshots} |"
            ).format(
                menu=record["menu_number"],
                verdict=record["verdict"],
                total=record["total_seconds"],
                handler="" if record["handler_seconds"] is None else record["handler_seconds"],
                walk="" if record["walk_seconds"] is None else record["walk_seconds"],
                console=len(record["console_errors"]),
                failed=len(record["failed_requests"]),
                log_errors=len(record["log_errors"]),
                screenshots=screenshots,
            )
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    """Parse the arguments, run the sweep, and write the reports."""
    parser = argparse.ArgumentParser(description="Run one controlled portal sweep.")
    parser.add_argument("--round", type=int, default=2, help="Artifact round number.")
    parser.add_argument(
        "--workers", type=int, default=1, help="Browser count. Default is one for trustworthy evidence."
    )
    parser.add_argument("--menus", default="", help="Comma-separated menu numbers to run.")
    parser.add_argument("--categories", default="", help="Comma-separated category names to run.")
    parser.add_argument("--base-url", default=PORTAL, help="Portal base URL.")
    arguments = parser.parse_args()

    categories = read_categories(arguments.base_url)
    categories = filter_categories(
        categories, parse_csv_filter(arguments.menus), parse_csv_filter(arguments.categories)
    )
    if not categories:
        print("no operations matched the filters")
        return 1

    runner = SweepRunner(arguments.round, arguments.workers, arguments.base_url)
    total = runner.load(categories)
    print(f"{len(categories)} categories, {total} operations, {arguments.workers} browsers\n")
    runner.run()
    runner.report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
