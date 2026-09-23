"""Run every operator journey of issue #3200 and build one evidence index.

Why:
    A journey that starts a job takes the site locks inside its portal server.
    A second start journey in the same server then meets those locks and fails
    for a reason that belongs to the test order, not to the product. This
    runner gives each start journey its own server process, runs the other
    journeys together in one process, and joins every journey report into one
    summary file and one HTML index.

Usage:
    python -m tests.e2e.upgrade_portal.journeys.run_journeys [--parallel 3] [--keyword EXPR]
"""

from __future__ import annotations

import argparse  # Read the parallel count and the keyword filter.
import html  # Escape the text of the index page.
import json  # Read each journey report and write the summary.
import logging  # Record each process that the runner starts.
import os  # Pass the start budget to each child.
import subprocess  # Start one pytest process for each group.
import sys  # Reuse the running interpreter for each child.
import time  # Mark the start of the run, so old reports stay out.
from concurrent.futures import ThreadPoolExecutor  # Run the fresh-server journeys side by side.
from pathlib import Path  # Build Windows-compatible paths.
from typing import Any  # The reports are plain JSON values.

from tests.e2e.upgrade_portal.journeys.evidence import ARTIFACT_ROOT, REPO_ROOT  # The evidence folders.

logger = logging.getLogger(__name__)  # Keep the runner records under this module name.

JOURNEY_FOLDER = "tests/e2e/upgrade_portal/journeys"  # Every journey test lives here.
FRESH_MARKER = "fresh_server"  # The marker of a journey that needs its own server.
PYTEST_ARGUMENTS = ("-q", "-p", "no:cacheprovider", "--timeout", "300", "--tb=line", "-rxXf")  # One option set.
SUMMARY_NAME = "summary.json"  # The joined report of one run.
INDEX_NAME = "index.html"  # The page that a person opens first.
SLOW_STEP_COUNT = 15  # The index lists this many of the slowest steps.
READY_BUDGET_VARIABLE = "UPGRADE_PORTAL_E2E_READY_SECONDS"  # The start budget that the server fixture reads.
READY_BUDGET_SECONDS = "120"  # Several portals start at once, so each start may take this long.


def pytest_command(*extra: str) -> list[str]:
    """Return one pytest command line with the shared options.

    Args:
        *extra: The selection arguments of this child.

    Returns:
        The command line.
    """
    return [sys.executable, "-m", "pytest", *PYTEST_ARGUMENTS, *extra]  # The same interpreter as the runner.


def collect_fresh(keyword: str) -> list[str]:
    """Return the node identifiers of the journeys that need their own server.

    Args:
        keyword: The optional pytest keyword filter.

    Returns:
        One node identifier for each fresh-server journey.
    """
    command = pytest_command(JOURNEY_FOLDER, "--collect-only", "-q", "-m", FRESH_MARKER)  # List only.
    command += ["-k", keyword] if keyword else []  # Apply the filter of the caller.
    logger.info("Collect the fresh-server journeys")  # Log before the child starts.
    listing = subprocess.run(command, capture_output=True, text=True, cwd=REPO_ROOT, check=False)  # nosec B603
    nodes = [line.strip() for line in listing.stdout.splitlines() if "::" in line]  # Keep node lines only.
    logger.debug("Collected %s fresh-server journeys", len(nodes))  # Log the count.
    return nodes  # The caller starts one process for each node.


def run_child(arguments: list[str], label: str) -> dict[str, Any]:
    """Run one pytest child and return its result line.

    Args:
        arguments: The selection arguments of the child.
        label: The short label for the summary.

    Returns:
        The label, the exit code, the seconds, and the last output lines.
    """
    logger.info("Start the journey group %s", label)  # Log before the child starts.
    started = time.perf_counter()  # The wall time of the whole child.
    environment = {**os.environ, READY_BUDGET_VARIABLE: READY_BUDGET_SECONDS}  # A loaded host starts slowly.
    finished = subprocess.run(  # nosec B603 - a fixed pytest command with no shell.
        pytest_command(*arguments), capture_output=True, text=True, cwd=REPO_ROOT, env=environment, check=False
    )
    seconds = round(time.perf_counter() - started, 1)  # One decimal is enough for a group.
    tail = finished.stdout.strip().splitlines()[-12:]  # The result lines of pytest.
    logger.debug("The journey group %s ended with %s in %s s", label, finished.returncode, seconds)  # Log after.
    return {"label": label, "exit_code": finished.returncode, "seconds": seconds, "tail": tail}


def read_reports(since: float) -> list[dict[str, Any]]:
    """Read every journey report that this run wrote.

    Args:
        since: The start moment of the run, as epoch seconds.

    Returns:
        One report for each journey folder that this run touched.
    """
    reports = []  # The reports of this run only.
    for path in sorted(ARTIFACT_ROOT.glob("*/journey.json")):  # One report in each journey folder.
        if path.stat().st_mtime >= since:  # An older report belongs to an earlier run.
            reports.append(json.loads(path.read_text(encoding="utf-8")))  # Keep the report.
    return reports  # The caller joins them.


def summarize(reports: list[dict[str, Any]], groups: list[dict[str, Any]]) -> dict[str, Any]:
    """Join the journey reports and the group results into one summary.

    Args:
        reports: The journey reports of this run.
        groups: The pytest group results.

    Returns:
        The summary record.
    """
    outcomes: dict[str, int] = {}  # The count of each outcome word.
    for report in reports:  # Count each journey once.
        outcomes[report["outcome"]] = outcomes.get(report["outcome"], 0) + 1  # One more of this word.
    steps = [dict(step, journey=report["journey"]) for report in reports for step in report["steps"]]  # Flat.
    slowest = sorted(steps, key=lambda step: step["seconds"], reverse=True)[:SLOW_STEP_COUNT]  # The slow steps.
    return {"journeys": len(reports), "outcomes": outcomes, "groups": groups, "slowest_steps": slowest}


def screenshot_link(screenshot: str) -> str:
    """Return the link of one screenshot, relative to the index page.

    Args:
        screenshot: The absolute path that the recorder stored.

    Returns:
        The folder name and the file name, joined with a slash.
    """
    path = Path(screenshot)  # The recorder stores an absolute path.
    return f"{path.parent.name}/{path.name}"  # The index sits in the parent of every journey folder.


def write_index(summary: dict[str, Any], reports: list[dict[str, Any]]) -> Path:
    """Write the HTML index of the run.

    Args:
        summary: The joined summary.
        reports: The journey reports of this run.

    Returns:
        The path of the index page.
    """
    rows = []  # One table row for each journey.
    for report in sorted(reports, key=lambda item: item["journey"]):  # A stable order for the reader.
        events = report["events"]  # The browser events of the journey.
        shots = " ".join(  # One link for each step screenshot, relative to the index page.
            f'<a href="{html.escape(screenshot_link(step["screenshot"]))}">{step["number"]}</a>'
            for step in report["steps"]
        )
        problems = len(events["console_errors"]) + len(events["page_errors"]) + len(events["error_responses"])
        rows.append(
            f"<tr><td>{html.escape(report['journey'])}</td><td>{html.escape(report['outcome'])}</td>"
            f"<td>{len(report['steps'])}</td><td>{problems}</td><td>{shots}</td></tr>"
        )
    body = (  # One plain page, so it opens with no server.
        "<html><head><meta charset='utf-8'><title>Upgrade portal journeys</title></head><body>"
        f"<h1>Upgrade portal journeys</h1><pre>{html.escape(json.dumps(summary['outcomes'], indent=2))}</pre>"
        "<table border='1' cellpadding='4'><tr><th>Journey</th><th>Outcome</th><th>Steps</th>"
        f"<th>Browser problems</th><th>Screenshots</th></tr>{''.join(rows)}</table></body></html>"
    )
    path = ARTIFACT_ROOT / INDEX_NAME  # One index at the root of the evidence folder.
    path.write_text(body, encoding="utf-8")  # Replace the index of an earlier run.
    return path  # The caller prints the path.


def main() -> int:
    """Run every journey group and write the summary and the index.

    Returns:
        Zero when every group passed, else one.
    """
    parser = argparse.ArgumentParser(description=__doc__)  # The usage text is the module text.
    parser.add_argument("--parallel", type=int, default=3, help="Fresh-server journeys that run at one time.")
    parser.add_argument("--keyword", default="", help="An optional pytest -k expression.")
    options = parser.parse_args()  # Read the command line.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")  # One log format.
    since = time.time()  # Reports older than this moment stay out of the summary.
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)  # The first run creates the folder.
    shared = [JOURNEY_FOLDER, "-m", f"not {FRESH_MARKER}"] + (["-k", options.keyword] if options.keyword else [])
    fresh = collect_fresh(options.keyword)  # One server for each of these journeys.
    with ThreadPoolExecutor(max_workers=max(1, options.parallel)) as pool:  # Bound the browser count.
        futures = [pool.submit(run_child, shared, "shared-server journeys")]  # The shared group.
        futures += [pool.submit(run_child, [node], node) for node in fresh]  # One child for each start journey.
        groups = [future.result() for future in futures]  # Wait for every child.
    reports = read_reports(since)  # The journeys that this run wrote.
    summary = summarize(reports, groups)  # Join the results.
    (ARTIFACT_ROOT / SUMMARY_NAME).write_text(json.dumps(summary, indent=2), encoding="utf-8")  # The summary.
    index = write_index(summary, reports)  # The page that a person opens first.
    print(json.dumps({"index": str(index), "outcomes": summary["outcomes"]}, indent=2))  # One result line set.
    return 0 if all(group["exit_code"] == 0 for group in groups) else 1  # Fail when one group failed.


if __name__ == "__main__":
    raise SystemExit(main())
