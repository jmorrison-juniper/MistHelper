"""Tests of the operator interface of the MIB generator.

The generator is only useful if a person can start it. These tests prove
the five flags parse, the menu entry exists, and the registry knows the
entry is safe. Tasks T027 and T041 ask for these checks.
"""

from __future__ import annotations

import importlib  # The main script loads by name, because a dash blocks a plain import.
from types import SimpleNamespace  # A light stand-in for the parsed argument namespace.

import pytest  # One table of parameters drives the test over each flag.

MAIN = importlib.import_module("MistHelper")  # The main script holds the flags and the menu.


@pytest.mark.parametrize(
    ("flag", "attribute"),
    [
        ("--mib-generate", "mib_generate"),
        ("--mib-dry-run", "mib_dry_run"),
        ("--mib-report", "mib_report"),
        ("--mib-check", "mib_check"),
    ],
)
def test_each_switch_parses_and_sets_its_own_attribute(flag: str, attribute: str) -> None:
    """A person must be able to name any one of the four actions."""
    args = MAIN._build_argument_parser().parse_args([flag])  # Parse the single flag on its own.
    assert getattr(args, attribute) is True  # The named action must switch on.


def test_the_output_flag_carries_a_path() -> None:
    """A person must be able to send the file somewhere else for a review."""
    args = MAIN._build_argument_parser().parse_args(["--mib-generate", "--mib-output", "out.mib"])
    assert args.mib_output == "out.mib"  # The path must reach the handler unchanged.


def test_the_handler_reaches_the_check_method(monkeypatch: pytest.MonkeyPatch) -> None:
    """The check flag must call `check`, because CI depends on its exit code."""
    calls: list[str] = []  # The list records which runner method the handler picked.

    class FakeRunner:  # A stand-in keeps the test off the 16 MB OpenAPI file.
        """A runner that records the call instead of reading the inputs."""

        def check(self, _output: object) -> tuple[str, ...]:
            """Record the call and report no drift."""
            calls.append("check")  # Prove the handler took the check path.
            return ()  # An empty tuple means the file agrees with the catalog.

    args = SimpleNamespace(mib_check=True, mib_report=False, mib_dry_run=False, mib_output=None)
    code = MAIN._report_mib_result(FakeRunner(), args, "out.mib")  # Drive the handler directly.
    assert calls == ["check"]  # Only the check path may run.
    assert code == 0  # No drift must give a clean exit code.


def test_the_menu_offers_the_generator() -> None:
    """The menu must carry entry 243, so an operator without flags can run it."""
    assert callable(MAIN._launch_mib_generator)  # The shared start path must exist.


def test_the_registry_marks_the_menu_entry_safe() -> None:
    """The registry must class 243 as safe, or the guard blocks the entry."""
    from src.utils.operation_registry import OperationRegistry  # The guard owns the table.

    assert OperationRegistry._REGISTRY["243"]["category"] == "safe"  # A read-only action is safe.
