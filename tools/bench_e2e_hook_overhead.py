"""Measure the client comparison hook overhead on a real offline path.

Why:
    Issue 2482 needs an end-to-end measurement, not a span micro-benchmark.
    This harness compares the real `compare_clients` operation with the
    performance level `off` and `base`. It uses generated offline captures and
    never opens a network socket.
"""

from __future__ import annotations  # Keep annotations lazy for Python startup cost.

import argparse  # Parse the budget and repeat controls.
import importlib  # Load project modules after the script adds the repository root.
import logging  # Record each benchmark phase without printing inside the timed path.
import os  # Set the documented environment level for each collection.
import statistics  # Compute medians and interquartile ranges.
import sys  # Insert the repository root into the import path for file execution.
import time  # Read the wall clock for each measured operation.
from dataclasses import dataclass  # Store results in small typed records.
from pathlib import Path  # Locate the repository root on Windows and Linux.
from typing import Any  # Type capture dictionaries from the fixture builder.

REPO_ROOT = Path(__file__).resolve().parents[1]  # Locate the repository root from tools.
sys.path.insert(0, str(REPO_ROOT))  # Make src importable when the script runs by file path.
clients = importlib.import_module("src.upgrade_portal.compare.clients")  # Import the real measured path.
performance = importlib.import_module("src.utils.performance")  # Import the recorder package.
Recorder = performance.Recorder  # Store the recorder class for level changes.

LOGGER = logging.getLogger(__name__)  # Use one logger for benchmark progress.
LEVEL_OFF = "off"  # The default disabled performance level.
LEVEL_BASE = "base"  # The lowest enabled performance level.
CONTROL_LIMIT_PERCENT = 3.0  # A larger control move marks the window as contaminated.
DEFAULT_COLLECTIONS = 3  # The requirement asks for at least three collections.
DEFAULT_REPEATS = 60  # Each collection repeats the operation many times.
DEFAULT_SIZES = (2500, 5000)  # A large site and a larger site.
MAX_ATTEMPTS = 8  # Allow reruns when the control detects contamination.
INNER_LOOPS = 10  # Average each sample over repeated real operations.


@dataclass(frozen=True, slots=True)
class Summary:
    """Hold one timing summary for one level and one workload."""

    median_ns: float  # The middle sample value.
    iqr_ns: float  # The interquartile range of the samples.
    samples: int  # The number of samples behind the summary.


@dataclass(frozen=True, slots=True)
class Row:
    """Hold the output row for one workload size."""

    size: int  # The number of clients in the pre-check capture.
    off: Summary  # The disabled-hook timing summary.
    base: Summary  # The enabled-hook timing summary.
    overhead_percent: float  # The base-vs-off overhead percentage.
    control_percent: float  # The control movement percentage.


def _client_mac(index: int) -> str:
    """Return one synthetic client address."""
    return f"aabbcc{index:06x}"  # Use a fake vendor prefix and a stable ordinal.


def _device_mac(index: int, moved: bool) -> str:
    """Return one synthetic serving device address."""
    offset = index + (10_000 if moved else 0)  # Move some clients after the upgrade.
    return f"001122{offset:06x}"  # Use a fake device address.


def _client_row(index: int, moved: bool) -> dict[str, str]:
    """Return one client row in the capture schema."""
    return {  # Build only the fields that the comparison reads.
        clients.MAC_KEY: _client_mac(index),  # Give the row a stable key.
        clients.DEVICE_MAC_KEY: _device_mac(index, moved),  # Select the serving device.
        clients.DEVICE_NAME_KEY: f"switch-{index % 24}",  # Keep the name cardinality bounded.
        clients.HOSTNAME_KEY: f"client-{index}",  # Give the row a stable name.
    }  # Return one row for the capture fixture.


def build_capture(size: int, moved: bool = False) -> dict[str, Any]:
    """Build one offline capture with wired, wireless, and guest clients."""
    wired = [_client_row(index, moved and index % 10 == 0) for index in range(size)]  # Main workload.
    wireless = [_client_row(size + index, False) for index in range(size // 5)]  # Add a second section.
    guest = [_client_row(size * 2 + index, False) for index in range(size // 10)]  # Add a third section.
    return {  # Match the real capture shape.
        clients.CLIENTS_KEY: {  # Group rows by client kind.
            clients.KIND_WIRED: wired,  # Store wired clients.
            clients.KIND_WIRELESS: wireless,  # Store wireless clients.
            clients.KIND_GUEST: guest,  # Store guest clients.
        }
    }


def canonical_result(size: int, level: str) -> dict[str, Any]:
    """Return the normalized output of one comparison."""
    _set_level(level)  # Apply the requested performance level outside the timed boundary.
    result = clients.compare_clients(build_capture(size), build_capture(size, moved=True))  # Run the real path.
    return result.to_dict() | {"proved_present": result.proved_present}  # Include every public result value.


def _set_level(level: str) -> None:
    """Apply one documented performance level to the comparison module."""
    logging.info("Setting performance level %s", level)  # Log before the setting change.
    os.environ["MISTHELPER_PERF_LEVEL"] = level  # Use the documented environment variable.
    clients._PERFORMANCE_RECORDER = Recorder(clients._performance_settings())  # Use the production hook settings.
    logging.debug("Set performance level %s", level)  # Log after the setting change.


def _time_call(function: Any, size: int) -> int:
    """Return the elapsed wall time of one function call."""
    total = 0  # Consume each return value so Python cannot skip the work.
    start = time.perf_counter_ns()  # Read the start clock next to the work.
    for _ in range(INNER_LOOPS):  # Batch real calls to reduce scheduler noise.
        total += function(size)  # Run the operation and consume its result.
    elapsed = time.perf_counter_ns() - start  # Read the end clock next to the work.
    if total < 0:  # Keep the accumulator observable without changing normal output.
        raise RuntimeError("The benchmark accumulator went below zero.")  # Fail loudly on impossible data.
    return elapsed // INNER_LOOPS  # Return the average cost of one operation.


def operation(size: int) -> int:
    """Run the real comparison path and return a consumed result count."""
    result = clients.compare_clients(build_capture(size), build_capture(size, moved=True))  # Run the real path.
    return len(result.deltas) + result.proved_present  # Consume the result inside the timed boundary.


def control(size: int) -> int:
    """Run an unhooked control path that should not move with the level."""
    captures = (build_capture(size), build_capture(size, moved=True))  # Build the same two fixtures as the operation.
    addresses: list[str] = []  # Store derived addresses for deterministic sort work.
    for capture in captures:  # Read both sides of the fixture.
        sections = capture[clients.CLIENTS_KEY]  # Read the client section map.
        for kind in clients.CLIENT_KINDS:  # Walk the same section order as the real comparison.
            addresses.extend(row[clients.MAC_KEY].replace(":", "") for row in sections[kind])  # Normalize keys.
    return sum(len(address) for address in sorted(set(addresses)))  # Consume the result without touching the hook.


def _summary(samples: list[int]) -> Summary:
    """Return the median, the interquartile range, and the sample count."""
    ordered = sorted(samples)  # Sort once for the quartile calculation.
    lower = statistics.median(ordered[: len(ordered) // 2])  # Calculate the lower quartile.
    upper = statistics.median(ordered[(len(ordered) + 1) // 2 :])  # Calculate the upper quartile.
    return Summary(statistics.median(ordered), upper - lower, len(ordered))  # Return the timing summary.


def _percent(before: float, after: float) -> float:
    """Return the percentage difference from before to after."""
    return ((after - before) / before) * 100.0 if before else 0.0  # Avoid divide by zero.


def _measure(level: str, size: int, function: Any) -> int:
    """Measure one function after applying one level."""
    _set_level(level)  # Apply the level before the timing loop starts.
    return _time_call(function, size)  # Return one averaged sample.


def _paired_samples(size: int, repeats: int, function: Any) -> tuple[list[int], list[int], list[float]]:
    """Collect paired off and base samples for one function."""
    off_samples: list[int] = []  # Store disabled samples.
    base_samples: list[int] = []  # Store enabled samples.
    percent_samples: list[float] = []  # Store per-pair movement.
    for index in range(repeats):  # Pair samples to control slow host drift.
        if index % 2 == 0:  # Alternate order to reduce second-run bias.
            off = _measure(LEVEL_OFF, size, function)  # Measure the disabled path first.
            base = _measure(LEVEL_BASE, size, function)  # Measure the enabled path second.
        else:
            base = _measure(LEVEL_BASE, size, function)  # Measure the enabled path first.
            off = _measure(LEVEL_OFF, size, function)  # Measure the disabled path second.
        off_samples.append(off)  # Keep the disabled sample.
        base_samples.append(base)  # Keep the enabled sample.
        percent_samples.append(_percent(off, base))  # Keep the paired percentage.
    return off_samples, base_samples, percent_samples  # Return raw and paired results.


def _validate_output(size: int) -> None:
    """Fail loudly when the enabled hook changes the function output."""
    logging.info("Validating output equality for size %s", size)  # Log before the equality check.
    off = canonical_result(size, LEVEL_OFF)  # Build the reference result outside timing.
    base = canonical_result(size, LEVEL_BASE)  # Build the candidate result outside timing.
    if off != base:  # Compare the public output shape.
        raise SystemExit(f"Output changed for size {size}")  # Fail with the affected size.
    logging.debug("Validated output equality for size %s", size)  # Log after the equality check.


def _attempt(size: int, repeats: int) -> Row | None:
    """Run one collection attempt and reject a contaminated window."""
    clients._SAMPLE_COUNTER = 0  # Reset the deterministic sample gate for this collection.
    _off_control_samples, _base_control_samples, control_pairs = _paired_samples(size, repeats, control)  # Control.
    control_percent = statistics.median(control_pairs)  # Calculate the paired control movement.
    if abs(control_percent) > CONTROL_LIMIT_PERCENT:  # Reject a noisy or contaminated window.
        return None  # Let the caller retry this collection.
    off_samples, base_samples, overhead_pairs = _paired_samples(size, repeats, operation)  # Real operation.
    off = _summary(off_samples)  # Summarize the disabled operation.
    base = _summary(base_samples)  # Summarize the enabled operation.
    overhead_percent = statistics.median(overhead_pairs)  # Use paired overhead for the budget decision.
    return Row(size, off, base, overhead_percent, control_percent)  # Return the row.


def collect_rows(sizes: tuple[int, ...], collections: int, repeats: int) -> list[Row]:
    """Collect clean rows for each size."""
    rows: list[Row] = []  # Store one aggregate row for each size.
    for size in sizes:  # Measure each representative input size.
        _validate_output(size)  # Prove the hook preserves output before timing.
        attempts: list[Row] = []  # Store clean collection rows for this size.
        for attempt in range(MAX_ATTEMPTS):  # Retry only when the control detects contamination.
            logging.info("Running collection %s for size %s", attempt + 1, size)  # Log before an attempt.
            row = _attempt(size, repeats)  # Measure one candidate collection.
            if row is not None:  # Accept only clean control windows.
                attempts.append(row)  # Keep the clean attempt.
            logging.debug("Size %s has %s clean collections", size, len(attempts))  # Log the clean count.
            if len(attempts) == collections:  # Stop when the requirement is met.
                break  # Leave the retry loop.
        if len(attempts) < collections:  # Fail when the control stayed contaminated.
            raise SystemExit(f"Control stayed contaminated for size {size}")  # State the blocked size.
        rows.append(_merge_rows(size, attempts))  # Merge collections into one report row.
    return rows  # Return every workload row.


def _merge_rows(size: int, rows: list[Row]) -> Row:
    """Merge clean collection rows into one report row."""
    off = _summary([row.off.median_ns for row in rows])  # Summarize collection medians.
    base = _summary([row.base.median_ns for row in rows])  # Summarize collection medians.
    control = statistics.median(row.control_percent for row in rows)  # Summarize control movement.
    return Row(size, off, base, _percent(off.median_ns, base.median_ns), control)  # Return the merged row.


def _format_ns(value: float) -> str:
    """Return a compact millisecond value."""
    return f"{value / 1_000_000:.3f}"  # Convert nanoseconds to milliseconds for the table.


def print_table(rows: list[Row]) -> None:
    """Print the benchmark table."""
    print(  # Header row.
        "| clients | off median ms | off IQR ms | base median ms | base IQR ms | samples | overhead % | control % |"
    )
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")  # Markdown separator.
    for row in rows:  # Print one row per workload size.
        print(  # Data row.
            f"| {row.size} | {_format_ns(row.off.median_ns)} | {_format_ns(row.off.iqr_ns)} | "
            f"{_format_ns(row.base.median_ns)} | {_format_ns(row.base.iqr_ns)} | {row.off.samples} | "
            f"{row.overhead_percent:.3f} | {row.control_percent:.3f} |"
        )


def parse_args() -> argparse.Namespace:
    """Return parsed benchmark options."""
    parser = argparse.ArgumentParser(description="Measure the MistHelper client comparison hook overhead.")  # Parser.
    parser.add_argument("--budget-percent", type=float, default=1.0)  # Set the overhead budget.
    parser.add_argument("--collections", type=int, default=DEFAULT_COLLECTIONS)  # Set collection count.
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)  # Set repeats per collection.
    parser.add_argument("--sizes", type=int, nargs="+", default=list(DEFAULT_SIZES))  # Set workload sizes.
    return parser.parse_args()  # Return parsed values.


def main() -> int:
    """Run the benchmark and return a process status."""
    logging.basicConfig(level=logging.WARNING)  # Keep timed path logging quiet.
    args = parse_args()  # Read command-line options.
    rows = collect_rows(tuple(args.sizes), args.collections, args.repeats)  # Collect the benchmark rows.
    print_table(rows)  # Print the measured table.
    failed = [row for row in rows if row.overhead_percent > args.budget_percent]  # Find budget failures.
    return 1 if failed else 0  # Return non-zero when any size exceeds the budget.


if __name__ == "__main__":
    raise SystemExit(main())  # Use the function result as the process exit code.
