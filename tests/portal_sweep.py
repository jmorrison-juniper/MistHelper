"""Run one controlled sweep of every portal operation.

The round two sweep used five agents that coordinated through the portal
run state. They starved each other, and the portal recorded zero runs in
one hour while all five reported themselves busy.

One process removes the coordination problem. This module orders the work
itself, so no participant has to guess whether another one holds a number.

Run it from the repository root with the project interpreter:

    .venv\\Scripts\\python.exe tests/portal_sweep.py --round 2

Add ``--workers 4`` to raise the browser count. Each open page holds one
Gunicorn worker thread, and the portal serves 24, so keep the count well
below that. Issue #3164 recorded the outage that four threads caused.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import queue
import sys
import threading
import time
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from portal_harness import ARTIFACT_ROOT, DefectLog, PortalHarness

PORTAL = "http://127.0.0.1:8055"

# Seconds to wait for the whole sweep before the runner gives up on a worker.
WORKER_JOIN_TIMEOUT = 7200


def read_categories() -> list[dict]:
    """Return the category list the portal serves."""
    with urllib.request.urlopen(f"{PORTAL}/api/operations/list", timeout=60) as answer:
        return json.load(answer)["categories"]


class SweepRunner:
    """Drive every operation once and record what each run produced."""

    def __init__(self, round_number: int, workers: int) -> None:
        """Store the sweep settings and build the shared work queue."""
        self.round_number = round_number  # Names the artifact directory.
        self.workers = workers  # Browser count, kept below the portal thread pool.
        self.work: queue.Queue = queue.Queue()  # Holds one entry for each category.
        self.lock = threading.Lock()  # Guards the shared result lists.
        self.results: list[dict] = []  # One record for each run.
        self.started = time.monotonic()  # Fixes the start, so the report can state the duration.

    def load(self, categories: list[dict]) -> int:
        """Put one entry on the queue for each category and return the row count."""
        total = 0  # Counts every operation the sweep will run.
        for category in categories:
            numbers = [operation["menu_number"] for operation in category["operations"]]
            self.work.put((category["name"], numbers))  # One worker owns a whole category.
            total += len(numbers)
        return total

    def run(self) -> None:
        """Start the workers and wait for the queue to drain."""
        threads = []  # Holds each worker, so the runner can join them.
        for index in range(self.workers):
            thread = threading.Thread(target=self._worker, args=(index,), daemon=True)
            thread.start()  # Start the browser for this worker.
            threads.append(thread)
        for thread in threads:
            thread.join(timeout=WORKER_JOIN_TIMEOUT)  # Never wait forever on a stuck browser.

    def _worker(self, index: int) -> None:
        """Take one category at a time and run every operation it holds."""
        while True:
            try:
                name, numbers = self.work.get_nowait()  # Claim a category, or stop.
            except queue.Empty:
                return
            try:
                self._sweep_category(index, name, numbers)
            except Exception as error:  # One bad category must not end the sweep.
                print(f"[w{index}] {name}: worker error {type(error).__name__}: {error}", flush=True)
            finally:
                self.work.task_done()  # Release the queue entry whatever happened.

    def _sweep_category(self, index: int, name: str, numbers: list[str]) -> None:
        """Run every operation of one category inside a single browser."""
        slug = name.lower().replace(" & ", "-").replace(" ", "-")
        log = DefectLog(category=slug, round_number=self.round_number)
        print(f"[w{index}] {name}: {len(numbers)} operations", flush=True)
        with PortalHarness(log) as harness:
            if not harness.open_category(name):
                print(f"[w{index}] {name}: the category did not open", flush=True)
                return
            for position, number in enumerate(numbers, start=1):
                self._run_one(index, harness, log, name, number, position, len(numbers))
        written = log.write()  # Persist the defects and the timings for this category.
        print(f"[w{index}] {name}: wrote {written}", flush=True)

    def _run_one(self, index, harness, log, name, number, position, total) -> None:
        """Run one operation and record the outcome."""
        label = ""  # Holds the rendered label, so a failure record can name the row.
        started = time.monotonic()
        try:
            label = harness.rendered_label(number)
            state = harness.run_operation(number)
        except Exception as error:  # Record the fault instead of ending the category.
            state = f"harness-error:{type(error).__name__}"
            log.add(number, "harness", "high", f"#{number} raised {type(error).__name__}", str(error)[:300], "")
        elapsed = time.monotonic() - started
        with self.lock:
            self.results.append(
                {
                    "category": name,
                    "menu_number": number,
                    "label": label[:80],
                    "state": state,
                    "seconds": round(elapsed, 2),
                }
            )
        print(f"[w{index}] {name} {position}/{total}  menu {number:>4}  {state:<22} {elapsed:6.1f}s", flush=True)

    def report(self) -> pathlib.Path:
        """Write the whole sweep to one file and print a summary."""
        target = ARTIFACT_ROOT / f"round{self.round_number}" / "_sweep-summary.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        duration = time.monotonic() - self.started
        states: dict[str, int] = {}  # Counts each terminal state, so the summary can rank them.
        for record in self.results:
            states[record["state"]] = states.get(record["state"], 0) + 1
        slow = sorted((r for r in self.results if r["seconds"] > 45.0), key=lambda r: -r["seconds"])
        payload = {
            "round": self.round_number,
            "duration_seconds": round(duration, 1),
            "operations_run": len(self.results),
            "states": states,
            "slow_runs": slow,
            "runs": sorted(self.results, key=lambda r: (r["category"], int(r["menu_number"]))),
        }
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nsweep finished in {duration / 60:.1f} minutes")
        print(f"operations run: {len(self.results)}")
        for state, count in sorted(states.items(), key=lambda pair: -pair[1]):
            print(f"  {state:<26} {count}")
        print(f"over 45 seconds: {len(slow)}")
        print(f"summary: {target}")
        return target


def main() -> int:
    """Parse the arguments, run the sweep, and write the report."""
    parser = argparse.ArgumentParser(description="Run one controlled portal sweep.")
    parser.add_argument("--round", type=int, default=2, help="Artifact round number.")
    parser.add_argument("--workers", type=int, default=3, help="Browser count. Keep it below the portal thread pool.")
    parser.add_argument("--only", default="", help="Run one category by exact name.")
    arguments = parser.parse_args()

    categories = read_categories()
    if arguments.only:
        categories = [category for category in categories if category["name"] == arguments.only]
        if not categories:
            print(f"no category named {arguments.only!r}")
            return 1

    runner = SweepRunner(arguments.round, arguments.workers)
    total = runner.load(categories)
    print(f"{len(categories)} categories, {total} operations, {arguments.workers} browsers\n")
    runner.run()
    runner.report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
