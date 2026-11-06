"""Prove that requirements exports match uv.lock (issue #3400)."""

import logging  # Keep the export guard observable in CI logs.
import shutil  # Find the required uv executable.
import subprocess  # Run fixed export commands without a shell.
from pathlib import Path  # Build platform-safe paths.

import pytest  # Prove expected failures without creating repository files.

LOGGER = logging.getLogger(__name__)  # Keep guard records on the module logger.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Resolve files from this test, not the current directory.
EXPORTS = (
    ("requirements.txt", ()),  # Export runtime packages from the lock.
    ("requirements-dev.txt", ("--extra", "dev")),  # Export runtime and development packages from the lock.
)


class DependencyExport:
    """Read, generate, and compare the two locked requirements exports."""

    @staticmethod
    def read_export(path: Path) -> str:
        """Read one export and fail when it is missing, unreadable, or empty."""
        if not path.is_file():  # A missing input cannot prove export parity.
            raise AssertionError(f"Requirements export not found: {path.name}")
        LOGGER.info("Reading requirements export %s", path.name)  # Trace before reading the file.
        try:
            content = path.read_text(encoding="utf-8")  # Read the committed or generated export.
        except (OSError, UnicodeError) as error:
            LOGGER.error("Could not read requirements export %s: %s", path.name, error)  # Preserve the read failure.
            raise  # Keep the original file error visible to the guard.
        LOGGER.debug("Read %s characters from %s", len(content), path.name)  # Report the measured file size.
        if not content.strip():  # An empty export hides every declared dependency.
            raise AssertionError(f"Requirements export is empty: {path.name}")  # Fail before an empty export passes.
        return content  # Give the caller the complete export for exact comparison.

    @staticmethod
    def find_uv() -> str:
        """Return the required UV executable or fail with a clear cause."""
        LOGGER.info("Finding the UV executable for export validation.")  # Trace before executable discovery.
        uv_path = shutil.which("uv")  # Resolve the tool required to verify generated exports.
        LOGGER.debug("The UV executable is available: %s", uv_path is not None)  # Report the discovery result.
        if uv_path is None:  # A skipped guard cannot prove export parity.
            LOGGER.error("The UV executable is required for export validation.")  # Preserve the missing tool context.
            raise AssertionError("The UV executable is required for export validation.")
        return uv_path  # Supply the resolved executable to the export command.

    @classmethod
    def render(cls, uv_path: str, output_directory: Path, filename: str, extra: tuple[str, ...]) -> str:
        """Run the locked export command and return stable output for comparison."""
        output_path = output_directory / filename  # Keep generated evidence outside the repository.
        command = [  # Keep each export invocation explicit and shell-free.
            uv_path,  # Use the executable discovered for this validation run.
            "export",  # Generate pip requirements from the lock.
            "--locked",  # Fail if the lock does not match project metadata.
            "--no-hashes",  # Match the checked-in export format.
            "--no-emit-project",  # Exclude MistHelper itself from pip inputs.
            *extra,  # Include the development group only for its export.
            "--output-file",  # Write temporary evidence outside the repository.
            str(output_path),  # Keep each generated file isolated by its name.
        ]  # Use the same lock-only export for every supported host.
        LOGGER.info("Generating locked requirements export %s", filename)  # Trace before the external command.
        try:
            result = subprocess.run(
                command, cwd=REPOSITORY_ROOT, capture_output=True, text=True, check=False, timeout=120
            )  # Keep argument parsing fixed and bound the command time.
        except (OSError, subprocess.SubprocessError) as error:
            LOGGER.error("Could not generate requirements export %s: %s", filename, error)  # Record tool failures.
            raise AssertionError(f"Could not generate requirements export: {filename}") from error  # Preserve cause.
        LOGGER.debug("uv export returned %s for %s", result.returncode, filename)  # Report the command result.
        if result.returncode != 0:
            LOGGER.error("uv export failed for %s with code %s", filename, result.returncode)  # Report failure context.
            raise AssertionError(result.stderr)  # Fail instead of comparing incomplete output.
        content = cls.read_export(output_path)  # Read generated evidence before comparing it.
        return content.replace(str(output_path), filename, 1)  # Normalize the temporary path in the command header.

    @staticmethod
    def count_requirements(exports: list[str]) -> int:
        """Count package lines across the supplied exports."""
        return sum(  # Count package rows across both committed exports.
            1  # Count one non-comment package record.
            for content in exports  # Inspect each checked-in export.
            for line in content.splitlines()  # Inspect each record in that export.
            if line.strip() and not line.lstrip().startswith("#")  # Ignore blanks and UV annotations.
        )  # Count package records, not UV annotations.

    @staticmethod
    def find_defects(actual: dict[str, str], expected: dict[str, str]) -> list[str]:
        """Return the names of exports that differ from their lock output."""
        defects = (  # Select each export whose committed content differs.
            name  # Report the specific stale export.
            for name, content in expected.items()  # Compare every generated export.
            if actual.get(name) != content  # Detect content drift or a missing file.
        )
        return sorted(defects)  # Keep failure ordering stable.


class TestDependencyExport:
    """Prove that the guard checks every export and detects each missing input."""

    def test_requirements_exports_match_the_lock(self, tmp_path: Path) -> None:
        """Fail when either checked-in export differs from the locked UV output."""
        uv_path = DependencyExport.find_uv()  # Require the tool so the guard cannot pass by skipping.
        actual = {  # Read all committed exports before comparison.
            name: DependencyExport.read_export(REPOSITORY_ROOT / name)  # Read one checked-in export.
            for name, _ in EXPORTS  # Include every configured export.
        }
        expected = {  # Generate the same export set from the lock.
            name: DependencyExport.render(uv_path, tmp_path, name, extra)  # Build one lock export.
            for name, extra in EXPORTS  # Include runtime and development variants.
        }
        defects = DependencyExport.find_defects(actual, expected)  # Find stale exports.
        count = DependencyExport.count_requirements(list(actual.values()))  # Measure the package records examined.
        summary = (  # Keep the guard result in one measurable line.
            f"dependency exports: examined {len(actual)} files and "  # Report the number of files.
            f"{count} requirements, {len(defects)} defects"  # Report records and detected drift.
        )
        print(summary)  # Report the guard scope to the test log.
        assert len(actual) == len(EXPORTS), "The guard did not read every configured export"  # Require both files.
        assert defects == [], f"Stale requirements exports: {', '.join(defects)}"  # Reject every stale export.

    def test_missing_export_fails(self, tmp_path: Path) -> None:
        """Prove that the export guard fails when an input file is absent."""
        with pytest.raises(AssertionError, match="Requirements export not found"):  # Require a missing input to fail.
            DependencyExport.read_export(tmp_path / "requirements.txt")  # Exercise the absent export path.

    def test_stale_export_is_detected(self) -> None:
        """Prove that the export guard reports content drift."""
        actual = {"requirements.txt": "requests==2.34.2\n"}  # Model a stale committed export.
        expected = {"requirements.txt": "requests==2.34.3\n"}  # Model the current locked export.
        assert DependencyExport.find_defects(actual, expected) == ["requirements.txt"]  # Require the drifted file name.

    def test_missing_uv_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Prove that the export guard fails when its required tool is absent."""
        monkeypatch.setattr(shutil, "which", lambda _: None)  # Model an environment without the lock tool.
        with pytest.raises(AssertionError, match="UV executable is required"):  # Require a missing tool to fail.
            DependencyExport.find_uv()  # Exercise the tool discovery failure path.
