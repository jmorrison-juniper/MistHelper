"""Run a local pytest shard in bounded chunks on Windows.

Why:
    Issue #2853 showed that two full local pytest commands did not finish in a
    OneDrive worktree on Windows. This runner keeps the same test scope, but it
    splits the scope into small pytest chunks. Each chunk has a per-test timeout
    and a wall-clock timeout, so the command always reaches a final summary.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

EXCLUDED_DIR_NAMES = frozenset({"__pycache__"})  # Ignore cache folders that hold no tests.
UPGRADE_PORTAL_NAME = "upgrade_portal"  # Split this large package one level lower.


@dataclass(frozen=True, slots=True)
class TestChunk:
    """One bounded pytest command."""

    paths: tuple[Path, ...]  # The paths that pytest must run in this chunk.
    ignores: tuple[Path, ...] = ()  # The paths that this chunk must leave for smaller chunks.


@dataclass(frozen=True, slots=True)
class ShardResult:
    """The result of one local shard run."""

    name: str  # The shard name the operator requested.
    chunks: int  # The number of pytest chunks the runner measured.
    seconds: float  # The total wall-clock time of the shard.
    exit_code: int  # Zero means every chunk passed.


class LocalTestShardRunner:
    """Run the requested local shard with bounded pytest chunks."""

    def __init__(self, root: Path, shard: str, chunk_timeout: int, test_timeout: int, durations: int) -> None:
        """Store the runner settings."""
        self.root = root  # Resolve every test path relative to the repository root.
        self.shard = shard  # Select the test scope without duplicating command strings.
        self.chunk_timeout = chunk_timeout  # Stop a hung pytest process before the session stalls.
        self.test_timeout = test_timeout  # Let pytest-timeout name the hung test body.
        self.durations = durations  # Ask pytest to report the slowest tests in each chunk.

    def run(self) -> int:
        """Run every chunk and print one final summary line."""
        import time

        logger.info("Building the local test shard chunks for %s", self.shard)  # Log before path discovery.
        chunks = self._build_chunks()  # Build deterministic chunks from the working tree.
        logger.debug("Built %d local test shard chunk(s)", len(chunks))  # Log the measured chunk count.
        started = time.monotonic()  # Use a monotonic clock for elapsed time.
        for index, chunk in enumerate(chunks, start=1):  # Run chunks in a fixed order for repeatability.
            code = self._run_chunk(index, len(chunks), chunk)  # Execute one bounded pytest command.
            if code != 0:  # Stop at the first failed chunk, so the operator sees the exact fault.
                elapsed = time.monotonic() - started  # Measure the failed shard time.
                result = ShardResult(self.shard, len(chunks), elapsed, code)  # Build the failure summary.
                self._print_summary(result)  # Print the final summary even on failure.
                return code  # Preserve the pytest exit code for automation.
        elapsed = time.monotonic() - started  # Measure the passed shard time.
        result = ShardResult(self.shard, len(chunks), elapsed, 0)  # Build the success summary.
        self._print_summary(result)  # Print the required final summary line.
        return 0  # Report success to PowerShell and CI.

    def _build_chunks(self) -> list[TestChunk]:
        """Return the test paths for the requested shard."""
        if self.shard == "unit":  # The first local shard in issue #2853.
            unit = self.root / "tests" / "unit"  # The same scope as the failing local command.
            portal = unit / UPGRADE_PORTAL_NAME  # The large package that needs smaller chunks.
            return [TestChunk((unit,), (portal,))] + self._children(portal)  # Preserve the root unit shape.
        contract = self.root / "tests" / "contract"  # The first path of the second local shard.
        integration = self.root / "tests" / "integration"  # The third path of the second local shard.
        guardrails = self.root / "tests" / "guardrails"  # The second path of the second local shard.
        contract_portal = contract / UPGRADE_PORTAL_NAME  # Split the large contract portal tree.
        integration_portal = integration / UPGRADE_PORTAL_NAME  # Split the large integration portal tree.
        return (  # The second local shard in issue #2853.
            [TestChunk((contract, guardrails, integration), (contract_portal, integration_portal))]
            + self._children(contract_portal)
            + self._children(integration_portal)
        )

    def _children(self, path: Path) -> list[TestChunk]:
        """Return stable child test paths, splitting large portal folders."""
        logger.info("Reading test paths under %s", path)  # Log before the directory scan.
        children = sorted(path.iterdir(), key=lambda child: child.name)  # Keep the order stable across runs.
        files: list[Path] = []  # Keep sibling files together, because legacy tests share module setup.
        tests: list[TestChunk] = []  # Collect the pytest targets for this path.
        for child in children:  # Read each direct child once.
            if child.name in EXCLUDED_DIR_NAMES:  # Cache folders hold no source test.
                continue  # Skip the cache folder without changing the shard scope.
            if child.is_file() and child.name.startswith("test_") and child.suffix == ".py":  # Direct test file.
                files.append(child)  # Add the file to the sibling file chunk.
            if child.is_dir() and child.name == UPGRADE_PORTAL_NAME:  # Large portal folders need more splits.
                tests.extend(self._children(child))  # Split one level lower for a shorter wall-clock chunk.
            elif child.is_dir():  # Normal package folder.
                tests.append(TestChunk((child,)))  # Run the package as one bounded pytest chunk.
        if files:  # Direct files inside a portal folder still need bounded batches.
            tests[0:0] = self._file_chunks(files)  # Put direct files before package folders.
        logger.debug("Found %d test path(s) under %s", len(tests), path)  # Log the scan result.
        return tests  # The caller runs the stable list.

    def _file_chunks(self, files: list[Path]) -> list[TestChunk]:
        """Split sibling test files into bounded batches."""
        batch_size = 8  # Eight portal files stayed below the Windows wall-clock limit in issue #2853.
        chunks: list[TestChunk] = []  # Collect each file batch as one pytest chunk.
        for offset in range(0, len(files), batch_size):  # Walk the file list without changing the order.
            batch = tuple(files[offset : offset + batch_size])  # Keep neighboring tests in one process.
            chunks.append(TestChunk(batch))  # Add one bounded pytest command.
        return chunks  # The caller inserts the file chunks before subdirectories.

    def _run_chunk(self, index: int, total: int, chunk: TestChunk) -> int:
        """Run one pytest chunk with both timeout layers."""
        relative = tuple(path.relative_to(self.root) for path in chunk.paths)  # Print short paths for each target.
        ignores = tuple(path.relative_to(self.root) for path in chunk.ignores)  # Print short ignored paths.
        label = self._chunk_label(relative, ignores)  # Build one readable chunk label.
        command = self._pytest_command(relative, ignores)  # Build the subprocess argument list without a shell.
        logger.info("Running pytest chunk %d of %d: %s", index, total, label)  # Log before execution.
        print(f"local-shard {self.shard}: chunk {index}/{total} {label}", flush=True)  # Show progress.
        try:  # A chunk timeout must become a clear exit code.
            completed = subprocess.run(  # Run pytest as a child so the wall-clock guard can stop it.
                command,  # Pass a list to avoid shell quoting and command injection.
                cwd=self.root,  # Run from the repository root so imports match normal pytest.
                check=False,  # Read the exit code and still print the final shard summary.
                timeout=self.chunk_timeout,  # Bound the whole chunk, not only one test body.
            )
        except subprocess.TimeoutExpired:  # The wall-clock guard stopped the chunk.
            logging.error("Pytest chunk timed out after %d seconds: %s", self.chunk_timeout, label)
            print(f"local-shard {self.shard}: timed out after {self.chunk_timeout}s at {label}", flush=True)
            return 124  # Use the common timeout exit code.
        logger.debug("Pytest chunk %s exited with code %d", label, completed.returncode)  # Log the result.
        return completed.returncode  # Propagate the pytest result.

    def _pytest_command(self, relative: tuple[Path, ...], ignores: tuple[Path, ...]) -> list[str]:
        """Build one pytest command."""
        command = [  # A list prevents PowerShell quoting faults on paths that contain spaces.
            sys.executable,  # Use the active virtual environment.
            "-m",  # Run pytest as a module, so the interpreter stays explicit.
            "pytest",  # The test runner installed by requirements-dev.txt.
            *(str(path) for path in relative),  # The bounded test paths.
            "-q",  # Keep each chunk readable.
            "--no-cov",  # Local evidence needs pass or fail, not a coverage denominator.
            f"--timeout={self.test_timeout}",  # Let pytest name a hung test before the chunk wall ends.
        ]
        command.extend(f"--ignore={path}" for path in ignores)  # Leave large paths for their smaller chunks.
        if self.durations > 0:  # A measurement run asks pytest for slow-test evidence.
            command.append(f"--durations={self.durations}")  # Print the slowest tests for this chunk.
        return command  # The subprocess runner receives one safe argument list.

    def _chunk_label(self, relative: tuple[Path, ...], ignores: tuple[Path, ...]) -> str:
        """Build one readable label for a chunk."""
        if len(relative) == 1:  # A directory chunk needs no count.
            label = str(relative[0])  # Print the only path.
        else:  # A combined chunk needs a compact label.
            label = f"{relative[0].parent} ({len(relative)} paths)"  # Keep the progress line short.
        if ignores:  # The first shard chunk excludes paths that smaller chunks measure.
            return f"{label} ignoring {len(ignores)} path(s)"  # State that the scope is split.
        return label  # Return the simple label for normal chunks.

    def _print_summary(self, result: ShardResult) -> None:
        """Print one final line that automation can find."""
        status = "passed" if result.exit_code == 0 else "failed"  # Keep the final line easy to scan.
        print(  # Print exactly one final summary line for issue #2853 acceptance.
            f"local-shard {result.name}: {status} {result.chunks} chunks in {result.seconds:.1f}s "
            f"exit_code={result.exit_code}",
            flush=True,
        )


class LocalShardCli:
    """Parse arguments and run the local shard runner."""

    def run(self, argv: list[str] | None = None) -> int:
        """Run the command-line interface."""
        args = self._parser().parse_args(argv)  # Parse once, so validation stays in argparse.
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")  # Show progress in PowerShell.
        root = Path.cwd().resolve()  # The contributor runs this command from the repository root.
        runner = LocalTestShardRunner(root, args.shard, args.chunk_timeout, args.test_timeout, args.durations)
        return runner.run()  # Delegate to the class that owns the shard behavior.

    def _parser(self) -> argparse.ArgumentParser:
        """Build the argument parser."""
        parser = argparse.ArgumentParser(description="Run a bounded local pytest shard.")  # Operator help text.
        parser.add_argument("shard", choices=("unit", "other"), help="The local shard to run.")  # Scope choice.
        parser.add_argument("--chunk-timeout", type=int, default=300, help="Seconds allowed for one chunk.")
        parser.add_argument("--test-timeout", type=int, default=120, help="Seconds allowed for one test.")
        parser.add_argument("--durations", type=int, default=0, help="Slow-test count to print per chunk.")
        return parser  # The caller parses the arguments.


if __name__ == "__main__":  # The script entry point.
    raise SystemExit(LocalShardCli().run())  # Return the runner exit code to the shell.
