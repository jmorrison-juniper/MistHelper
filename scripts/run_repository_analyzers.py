"""Run each repository analyzer with a documented full-scope command."""

from __future__ import annotations  # Keep annotations light for Python 3.13.

import logging  # Log each analyzer command before and after it runs.
from pathlib import Path  # Build paths without hardcoded separators.

from tools.compliance_analyzer.__main__ import ComplianceCLI  # Reuse the package CLI without subprocess.
from tools.refactor_analyzer.__main__ import RefactorCLI  # Reuse the package CLI without subprocess.
from tools.ste_linter.cli import LinterCLI  # Reuse the package CLI without subprocess.
from tools.test_quality_analyzer.__main__ import TestQualityCLI  # Reuse the package CLI without subprocess.

logger = logging.getLogger(__name__)  # Module logger for analyzer orchestration.


class RepositoryAnalyzerRunner:
    """Run every analyzer with the repository scope that issue #1768 defines."""

    def run(self) -> int:
        """Run all repository analyzers and return the highest exit code."""
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")  # Configure logs.
        logger.info("Starting repository analyzer run")  # Log before the first analyzer starts.
        codes = [self._run_compliance(), self._run_refactor(), self._run_ste(), self._run_test_quality()]  # Run all.
        result = max(codes)  # Preserve the most severe analyzer exit code.
        logger.debug("Repository analyzer run completed with exit code %d", result)  # Log the final code.
        return result  # Return a shell-friendly result.

    def _run_compliance(self) -> int:
        """Run the compliance analyzer across repository Python source roots."""
        logger.info("Running compliance analyzer for repository scope")  # Log before analyzer call.
        args = [  # Name every Python source root that the compliance analyzer supports.
            "MistHelper.py",
            "maps_manager.py",
            "wsgi.py",
            "wsgi_capture.py",
            "src",
            "scripts",
            "--recursive",
            "--output",
            str(Path("compliance_report.md")),
        ]
        code = ComplianceCLI().run(args)  # Run in-process so Windows needs no shell quoting.
        logger.debug("Compliance analyzer exited with code %d", code)  # Log after analyzer call.
        return code  # Return the analyzer exit code.

    def _run_refactor(self) -> int:
        """Run the refactor analyzer against the repository entrypoint."""
        logger.info("Running refactor analyzer for repository entrypoint")  # Log before analyzer call.
        args = ["MistHelper.py", "--src-root", "src"]  # Keep analysis scoped to the repository's product source.
        code = RefactorCLI().run(args)  # Run the refactor analyzer in-process.
        logger.debug("Refactor analyzer exited with code %d", code)  # Log after analyzer call.
        return code  # Return the analyzer exit code.

    def _run_ste(self) -> int:
        """Run the STE linter against repository prose contracts."""
        logger.info("Running STE linter for repository prose")  # Log before linter call.
        args = [  # Keep the command bounded to high-value prose and changed specs.
            "README.md",
            "documentation/ASD-STE100_writing-guide.md",
            "specs/1768-analyzer-skips/spec.md",
            "specs/1768-analyzer-skips/plan.md",
            "specs/1768-analyzer-skips/tasks.md",
            "--config",
            ".ste-linter.toml",
            "--min-score",
            "80",
        ]
        code = LinterCLI().run(args)  # Run the linter in-process.
        logger.debug("STE linter exited with code %d", code)  # Log after linter call.
        return code  # Return the analyzer exit code.

    def _run_test_quality(self) -> int:
        """Run the test quality analyzer across every repository test root."""
        logger.info("Running test quality analyzer for repository test roots")  # Log before analyzer call.
        args = ["--baseline", ""]  # Empty baseline keeps this command read-only for first use.
        code = TestQualityCLI().run(args)  # Run with automatic repository test-root discovery.
        logger.debug("Test quality analyzer exited with code %d", code)  # Log after analyzer call.
        return code  # Return the analyzer exit code.


if __name__ == "__main__":  # Run only when the file is used as a script.
    raise SystemExit(RepositoryAnalyzerRunner().run())  # Use the class result as the process exit code.
