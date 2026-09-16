"""Measure capture portal concurrency candidates for issue 1988."""

from __future__ import annotations  # Keep annotation evaluation cheap during benchmark import.

import argparse  # Parse the output path, so CI and humans can choose an artifact file.
import json  # Write JSON Lines that a later reader can audit without a tool.
import logging  # Record benchmark actions with the project logging system.
import statistics  # Compute medians without an extra dependency.
import sys  # Add the repository root when the script runs by path.
import threading  # Bound synthetic cloud and store contention with semaphores.
import time  # Sleep models remote waits and perf_counter measures total elapsed time.
from collections.abc import Iterable, Mapping  # Type the work-item and JSON payload shapes.
from concurrent.futures import ThreadPoolExecutor  # Model the candidate worker count without production changes.
from dataclasses import asdict, dataclass  # Keep scenario settings immutable and explicit.
from pathlib import Path  # Build paths without hardcoded separators.
from typing import Any, Final  # Type JSON values and constants.

REPO_ROOT = Path(__file__).resolve().parents[2]  # Locate the repository root from scripts\\benchmarks.
sys.path.insert(0, str(REPO_ROOT))  # Make src imports work when the script runs by path.

logging.basicConfig(  # Keep imported performance logs compact.
    level=logging.WARNING, format="%(levelname)s:%(message)s"
)
LOGGER = logging.getLogger(__name__)  # Use one logger for this measurement script.


@dataclass(frozen=True, slots=True)
class Scenario:
    """Hold one benchmark case with no private identifiers."""

    name: str  # Name the case in the artifact.
    capture_workers: int  # Bound concurrent capture call groups.
    store_workers: int  # Bound concurrent store writes.
    cloud_cap: int = 8  # Match FAST_MODE_MAX_CONCURRENT_CONNECTIONS.


@dataclass(frozen=True, slots=True)
class Reading:
    """Hold one timed benchmark reading."""

    scenario: str  # Name the measured case.
    iteration: int  # Name the repeated run number.
    wall_ns: int  # Total elapsed wall time for the run.
    process_cpu_ns: int  # Process CPU cost for the run.
    result_count: int  # Count returned records to prove no data loss.
    error_count: int  # Count failed synthetic operations.


class CaptureConcurrencyBenchmark:
    """Run a synthetic capture workload through current and candidate limits."""

    CAPTURE_LATENCIES: Final[dict[str, float]] = {
        "devices": 2.00,
        "wired": 1.70,
        "wireless_stats": 1.60,
        "wireless_search": 1.80,
    }  # Four wave-one reads fill the current pool.
    TIER_THREE_LATENCIES: Final[dict[str, float]] = {
        "ports": 1.50,
        "poe": 1.20,
        "radios": 1.30,
        "alarms": 1.10,
    }  # Tier-three fan-out already caps at four.
    STORE_LATENCIES: Final[dict[str, float]] = {
        "arango": 0.70,
        "redis": 0.45,
        "csv": 0.55,
    }  # Store waits model shared write paths.
    ITERATIONS: Final[int] = 3  # Odd count gives one median with enough warm runs.
    ROWS_PER_CALL: Final[int] = 50  # Fixed count proves every scenario kept the same data.

    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path  # The caller chooses the committed artifact path.
        from src.utils.performance import Recorder, RecorderSettings  # Import after sys.path is ready.

        self.recorder = Recorder(RecorderSettings(level="diagnostic", sample_rate=1.0))  # Record every span.
        self.store_lock = threading.Lock()  # Model the shared ArangoDB and Redis write contention.

    def run(self) -> list[Reading]:
        LOGGER.info("Starting capture concurrency benchmark")  # Log before the measurement starts.
        scenarios = [
            Scenario("current_capture_pool_4", 4, 1),
            Scenario("candidate_capture_pool_8", 8, 1),
            Scenario("candidate_parallel_store", 4, 3),
        ]  # Compare one candidate at a time.
        readings = [
            self._measure(scenario, iteration) for scenario in scenarios for iteration in range(self.ITERATIONS)
        ]  # Keep one raw row per run.
        self._write_artifact(readings)  # Persist raw rows and recorder events for audit.
        LOGGER.info("Finished capture concurrency benchmark")  # Log after every artifact write.
        return readings  # Tests read the result without opening the file.

    def _measure(self, scenario: Scenario, iteration: int) -> Reading:
        from src.utils.performance import EventSource, Stopwatch  # Import after sys.path is ready.

        source = EventSource(
            "scripts/benchmarks", "measure", "CaptureConcurrencyBenchmark"
        )  # Avoid raw paths in telemetry.
        with Stopwatch() as watch:  # Use the repository timer for the whole scenario.
            with self.recorder.span(
                source, family="diagnostic", monitor="operation"
            ) as span:  # Use the project recorder.
                results = self._run_capture(scenario)  # Run the synthetic capture and comparison path.
                span.label("operation", "probe")  # Use an allowlisted safe label.
                span.label("workload_size", "small")  # Use a fixed bucket and no site data.
                span.count("result_count", float(len(results)))  # Store the completeness count.
        elapsed = watch.elapsed  # Read the repository timer after the context exits.
        return Reading(
            scenario.name, iteration, elapsed.wall_ns, elapsed.cpu_ns, len(results), 0
        )  # No exception means no synthetic errors.

    def _run_capture(self, scenario: Scenario) -> list[str]:
        cloud_slots = threading.Semaphore(
            scenario.cloud_cap
        )  # Shared cloud cap models FAST_MODE_MAX_CONCURRENT_CONNECTIONS.
        first_wave = self._run_group(
            self.CAPTURE_LATENCIES, scenario.capture_workers, cloud_slots
        )  # Current code runs wave one first.
        second_wave = self._run_group(
            self.TIER_THREE_LATENCIES, min(4, scenario.capture_workers), cloud_slots
        )  # Tier-three fan-out is capped at four.
        stored = self._run_group(
            self.STORE_LATENCIES, scenario.store_workers, cloud_slots, store=True
        )  # Store writes can contend.
        return [*first_wave, *second_wave, *stored, "comparison"]  # Keep one result per completed section.

    def _run_group(
        self, latencies: Mapping[str, float], workers: int, cloud_slots: threading.Semaphore, store: bool = False
    ) -> list[str]:
        with ThreadPoolExecutor(
            max_workers=max(1, workers), thread_name_prefix="issue1988"
        ) as pool:  # Bound each candidate explicitly.
            futures = [
                pool.submit(self._call, name, delay, cloud_slots, store) for name, delay in latencies.items()
            ]  # Start all eligible calls before waiting.
            return [future.result() for future in futures]  # Preserve deterministic result order for comparison.

    def _call(self, name: str, delay: float, cloud_slots: threading.Semaphore, store: bool) -> str:
        lock = self.store_lock if store else cloud_slots  # Store calls serialize on the shared writer lock.
        with lock:  # Hold the modeled scarce resource for the full remote wait.
            time.sleep(delay)  # Sleep to model network or store latency without a live service.
        return f"{name}:{self.ROWS_PER_CALL}"  # Fixed count proves each scenario returned the same data.

    def _write_artifact(self, readings: Iterable[Reading]) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)  # Create the feature artifact directory.
        rows = [asdict(reading) for reading in readings]  # Convert dataclass rows to JSON records.
        summary = self._summarize(rows)  # Add medians so reviewers can check arithmetic in one file.
        with self.output_path.open("w", encoding="utf-8") as handle:  # Replace stale measurement data.
            handle.write(json.dumps({"summary": summary}, sort_keys=True) + "\n")  # First line holds derived values.
            for row in rows:  # Each later line holds one raw run.
                handle.write(json.dumps(row, sort_keys=True) + "\n")  # JSON Lines supports simple review tools.
        self.recorder.sink.flush_to(
            self.output_path.with_suffix(".events.jsonl")
        )  # Store scrubbed recorder events beside raw rows.

    def _summarize(self, rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
        names = sorted({str(row["scenario"]) for row in rows})  # List each scenario once.
        return {
            name: {
                "median_wall_ms": statistics.median(row["wall_ns"] for row in rows if row["scenario"] == name)
                / 1_000_000,
                "median_cpu_ms": statistics.median(row["process_cpu_ns"] for row in rows if row["scenario"] == name)
                / 1_000_000,
                "result_count": float(max(row["result_count"] for row in rows if row["scenario"] == name)),
            }
            for name in names
        }  # Keep only auditable derived values.


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure capture portal concurrency candidates."
    )  # Define the command interface.
    parser.add_argument(
        "--output", type=Path, default=Path("specs") / "1988-capture-concurrency" / "measurements" / "raw-data.jsonl"
    )  # Keep artifacts under the feature spec.
    benchmark = CaptureConcurrencyBenchmark(parser.parse_args().output)  # Bind settings from the command line.
    readings = benchmark.run()  # Execute every scenario before printing a summary.
    groups = {reading.scenario for reading in readings}  # Count scenarios for the operator line.
    print(f"wrote {len(readings)} readings across {len(groups)} scenarios")  # Give CI one concise final line.
    return 0  # A successful write is a successful benchmark.


if __name__ == "__main__":
    raise SystemExit(main())  # Use an explicit exit code for command-line callers.
