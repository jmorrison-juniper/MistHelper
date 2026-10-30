"""Guard the bounded issue #2753 device ID default repair."""

from __future__ import annotations  # WHY: keep annotations lazy for the test module.

from pathlib import Path  # WHY: build isolated scan paths in temporary directories.

import pytest  # WHY: type capture fixtures and assert explicit failures.

from scripts.scan_2753 import MissingDeviceIdDefaultScanner  # WHY: test the committed scan command.


class TestMissingDeviceIdDefaultScanner:
    """Prove that the bounded scan detects candidates and cannot pass on missing input."""

    def test_detects_a_controlled_empty_id_default(self) -> None:
        """A reintroduced empty ID default must appear in scan results."""
        scanner = MissingDeviceIdDefaultScanner()  # WHY: use the same matcher as the repository guard.
        candidates = scanner.find_empty_defaults('device_id = device.get("id", "")\n')  # WHY: model regression.
        assert candidates == [1]  # WHY: the mutation must create one finding.

    def test_run_fails_with_a_controlled_empty_id_default(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A candidate in a controlled source must fail the full scan command."""
        source_path = tmp_path / "candidate.py"  # WHY: isolate the candidate from repository source.
        source_path.write_text('device_id = device.get("id", "")\n', encoding="utf-8")  # WHY: inject one regression.
        scanner = MissingDeviceIdDefaultScanner(source_path)  # WHY: scan only the controlled source.
        exit_code = scanner.run()  # WHY: exercise the command's nonzero candidate path.
        captured = capsys.readouterr()  # WHY: inspect the measured scan result.
        assert exit_code == 1  # WHY: a detected candidate must fail the guard.
        assert "Scanned 1 source file; found 1 empty device ID defaults." in captured.out  # WHY: verify counts.
        assert "Candidate at line 1." in captured.out  # WHY: report the candidate location.
        assert captured.err == ""  # WHY: a valid scan must not report an input error.

    def test_selected_source_has_no_empty_id_default(self, capsys: pytest.CaptureFixture[str]) -> None:
        """The guard reports one parsed file and requires zero selected candidates."""
        scanner = MissingDeviceIdDefaultScanner()  # WHY: scan the selected production module.
        exit_code = scanner.run()  # WHY: exercise the same command path as local validation.
        output = capsys.readouterr().out  # WHY: verify the guard reports its examined input.
        assert exit_code == 0  # WHY: any remaining candidate must fail the guard.
        assert "Scanned 1 source file; found 0 empty device ID defaults." in output  # WHY: reject silent green.

    def test_missing_source_fails_with_examined_count(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """An absent scan input must not look like a clean source file."""
        scanner = MissingDeviceIdDefaultScanner(tmp_path / "missing.py")  # WHY: model a missing required file.
        exit_code = scanner.run()  # WHY: exercise explicit scan failure handling.
        captured = capsys.readouterr()  # WHY: inspect both status and diagnostic streams.
        assert exit_code == 2  # WHY: unavailable input is not a successful scan.
        assert "Scanned 0 source files; candidate count unavailable." in captured.out  # WHY: report the true count.
        assert "Cannot scan" in captured.err  # WHY: preserve the input failure context.

    def test_invalid_source_fails_with_examined_count(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A syntax error must not look like a clean source file."""
        source_path = tmp_path / "invalid.py"  # WHY: isolate malformed input from repository files.
        source_path.write_text("if :\n", encoding="utf-8")  # WHY: provide invalid Python syntax.
        scanner = MissingDeviceIdDefaultScanner(source_path)  # WHY: scan only the controlled source.
        exit_code = scanner.run()  # WHY: exercise explicit parse failure handling.
        captured = capsys.readouterr()  # WHY: inspect both status and diagnostic streams.
        assert exit_code == 2  # WHY: invalid input is not a successful scan.
        assert "Scanned 0 source files; candidate count unavailable." in captured.out  # WHY: report no parsed files.
        assert "Cannot scan" in captured.err  # WHY: preserve the parser failure context.
