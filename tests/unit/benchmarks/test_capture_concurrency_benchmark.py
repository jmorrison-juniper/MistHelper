"""Tests for the issue 1988 capture concurrency benchmark."""

from __future__ import annotations  # Keep annotations lazy during test import.

import json  # Parse the JSON Lines artifact that the benchmark writes.
from pathlib import Path  # Build Windows-safe artifact paths.

import pytest  # Restore patched benchmark settings after the test.

from scripts.benchmarks import bench_capture_concurrency as benchmark_module  # Import the measured script as a module.


class TestCaptureConcurrencyBenchmark:
    """Verify the benchmark contract without a live Mist API."""

    def test_benchmark_writes_scrubbed_artifacts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        output_path = Path("data") / "test-artifacts" / "issue1988-benchmark.jsonl"  # Keep test output in data.
        event_path = output_path.with_suffix(".events.jsonl")  # The recorder writes scrubbed spans beside rows.
        output_path.unlink(missing_ok=True)  # Remove a stale artifact before the test starts.
        event_path.unlink(missing_ok=True)  # Remove stale recorder events from an earlier run.
        monkeypatch.setattr(benchmark_module.CaptureConcurrencyBenchmark, "ITERATIONS", 1)  # Keep the unit test fast.
        monkeypatch.setattr(
            benchmark_module.CaptureConcurrencyBenchmark, "CAPTURE_LATENCIES", {"devices": 0.001}
        )  # Use a tiny wave.
        monkeypatch.setattr(
            benchmark_module.CaptureConcurrencyBenchmark, "TIER_THREE_LATENCIES", {"ports": 0.001}
        )  # Use a tiny tier.
        monkeypatch.setattr(
            benchmark_module.CaptureConcurrencyBenchmark, "STORE_LATENCIES", {"arango": 0.001}
        )  # Use a tiny write.
        benchmark = benchmark_module.CaptureConcurrencyBenchmark(output_path)  # Build the benchmark with test paths.
        readings = benchmark.run()  # Execute the synthetic measurement with no cloud service.
        lines = output_path.read_text(encoding="utf-8").splitlines()  # Read the raw artifact for contract checks.
        events = event_path.read_text(encoding="utf-8").splitlines()  # Read the scrubbed recorder artifact.
        assert len(readings) == 3  # One run exists for each compared scenario.
        assert json.loads(lines[0])["summary"]  # The first line holds derived medians.
        assert all("site" not in line.lower() for line in lines)  # The artifact stores no site identifier.
        assert all("token" not in line.lower() for line in events)  # The recorder stores no credential label.
