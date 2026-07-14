"""Wave 2 P2 coverage for src/output/writer.py (initiative #1018).

Covers the abstract `OutputWriter` NotImplementedError paths and the
concrete `ConsoleOutputWriter` stdout/stderr behaviour under capsys.
No source edits, no monkeypatches of MistHelper, no live I/O.
"""

from __future__ import annotations  # WHY: PEP 604 unions for method signatures under Python 3.10+.

import pytest  # WHY: pytest.raises fixture for NotImplementedError assertions.

from src.output.writer import ConsoleOutputWriter, OutputWriter  # WHY: SUT direct import (no re-export hop).


class TestOutputWriterAbstract:
    """Abstract base OutputWriter surfaces NotImplementedError for every emit method."""

    def test_info_raises_not_implemented(self) -> None:
        """`info` must raise NotImplementedError so concrete subclasses are forced to implement it."""
        writer = OutputWriter()  # WHY: instantiating the abstract class directly is legal for the raise-path check.
        with pytest.raises(NotImplementedError):  # WHY: contract: base class must refuse to emit.
            writer.info("hello")  # WHY: exercise the raising branch of info.

    def test_warn_raises_not_implemented(self) -> None:
        """`warn` must raise NotImplementedError so concrete subclasses are forced to implement it."""
        writer = OutputWriter()  # WHY: same abstract-instantiation pattern for the warn branch.
        with pytest.raises(NotImplementedError):  # WHY: contract: base class must refuse to emit warnings.
            writer.warn("careful")  # WHY: exercise the raising branch of warn.

    def test_error_raises_not_implemented(self) -> None:
        """`error` must raise NotImplementedError so concrete subclasses are forced to implement it."""
        writer = OutputWriter()  # WHY: same abstract-instantiation pattern for the error branch.
        with pytest.raises(NotImplementedError):  # WHY: contract: base class must refuse to emit errors.
            writer.error("boom")  # WHY: exercise the raising branch of error.


class TestConsoleOutputWriter:
    """ConsoleOutputWriter prints prefixed messages to stdout/stderr as declared."""

    def test_info_prints_to_stdout(self, capsys: pytest.CaptureFixture[str]) -> None:
        """`info` writes `[INFO] <msg>` to stdout (not stderr)."""
        ConsoleOutputWriter().info("hello world")  # WHY: exercise info concrete path.
        captured = capsys.readouterr()  # WHY: capture stdout + stderr streams.
        assert captured.out == "[INFO] hello world\n"  # WHY: exact contract on stdout prefix + payload + newline.
        assert captured.err == ""  # WHY: info must never leak to stderr.

    def test_warn_prints_to_stdout(self, capsys: pytest.CaptureFixture[str]) -> None:
        """`warn` writes `[WARN] <msg>` to stdout (not stderr)."""
        ConsoleOutputWriter().warn("watch out")  # WHY: exercise warn concrete path.
        captured = capsys.readouterr()  # WHY: capture stdout + stderr streams.
        assert captured.out == "[WARN] watch out\n"  # WHY: exact contract on stdout prefix + payload + newline.
        assert captured.err == ""  # WHY: warn must land on stdout, not stderr per the docstring.

    def test_error_prints_to_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        """`error` writes `[ERROR] <msg>` to stderr (not stdout)."""
        ConsoleOutputWriter().error("kaboom")  # WHY: exercise error concrete path.
        captured = capsys.readouterr()  # WHY: capture stdout + stderr streams.
        assert captured.err == "[ERROR] kaboom\n"  # WHY: exact contract on stderr prefix + payload + newline.
        assert captured.out == ""  # WHY: error must land on stderr, not stdout per the docstring.

    def test_kwargs_are_accepted_and_ignored(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Extra keyword arguments are accepted for interface uniformity but do not affect output."""
        writer = ConsoleOutputWriter()  # WHY: single instance reused across the three method invocations.
        writer.info("x", extra="ignored")  # WHY: kwargs are permitted by signature but must not appear in output.
        writer.warn("y", severity=1)  # WHY: numeric kwarg exercise; no formatting side-effects expected.
        writer.error("z", details={"k": 1})  # WHY: mapping kwarg exercise; no formatting side-effects expected.
        captured = capsys.readouterr()  # WHY: capture all three method invocations at once.
        assert captured.out == "[INFO] x\n[WARN] y\n"  # WHY: kwargs are dropped; only prefix + msg is printed.
        assert captured.err == "[ERROR] z\n"  # WHY: error still lands on stderr regardless of kwargs.
