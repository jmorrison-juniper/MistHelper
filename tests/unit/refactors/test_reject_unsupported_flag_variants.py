"""Regression tests for issue #1640: reject `--test-interactive` hyphenated variant.

Verifies that the guard `MistHelper._reject_unsupported_flag_variants` rejects
the natural hyphenated spelling `--test-interactive` (and its `=value` form)
with an actionable error naming the supported spelling `--testinteractive`,
exits with status code 2, and does NOT silently proceed as if the test flag
had been omitted. Also verifies that supported spellings (empty argv, plain
`--testinteractive`, unrelated flags) are passthrough no-ops.

The guard is invoked from `src/refactors/main_entrypoint.py` before
`parser.parse_args()`, so this test also patches the entrypoint pipeline to
prove the guard runs before argparse would otherwise misroute the invocation.
"""

from __future__ import annotations  # WHY: PEP 604 unions in type hints on Python 3.10+.

import argparse  # WHY: MagicMock(spec=argparse.ArgumentParser) contract typing.
import importlib  # WHY: resolve the live MistHelper module for the guard function.
from typing import Any  # WHY: mocks dict holds mixed MagicMock and Namespace objects.
from unittest.mock import MagicMock  # WHY: mock pipeline steps around the guard call.

import pytest  # WHY: monkeypatch + capsys fixtures.

from src.refactors.main_entrypoint import MainEntrypoint  # WHY: exercise full pipeline in one test.


def _guard() -> Any:
    """Return the live `_reject_unsupported_flag_variants` callable from MistHelper.

    Why:
        Resolved lazily so tests fail with a clear ImportError message if the guard
        was accidentally removed or renamed, rather than a stale top-level ImportError
        that would mask the actual regression.

    Returns:
        The bound callable `MistHelper._reject_unsupported_flag_variants`.
    """
    module = importlib.import_module("MistHelper")  # Live import; MistHelper is a top-level script module.
    return module._reject_unsupported_flag_variants  # Access the guard as a module attribute.


class TestRejectUnsupportedFlagVariants:
    """`_reject_unsupported_flag_variants` gates raw argv before argparse."""

    def test_hyphenated_variant_exits_with_actionable_message(self, capsys: pytest.CaptureFixture[str]) -> None:
        """`--test-interactive` triggers SystemExit(2) with both the bad and good spellings in stderr."""
        with pytest.raises(SystemExit) as excinfo:  # WHY: guard MUST terminate the process, not silently return.
            _guard()(["--test-interactive"])  # WHY: bare hyphenated variant is the primary defect case.
        assert excinfo.value.code == 2  # WHY: argparse convention for usage errors is exit-code 2.
        captured = capsys.readouterr()  # WHY: capture the stderr message for content assertions.
        assert "--test-interactive" in captured.err  # WHY: user must see which spelling was rejected.
        assert "--testinteractive" in captured.err  # WHY: user must see the supported spelling suggestion.

    def test_hyphenated_variant_with_equals_value_is_rejected(self, capsys: pytest.CaptureFixture[str]) -> None:
        """`--test-interactive=1` (with an `=value` suffix) is also rejected."""
        with pytest.raises(SystemExit) as excinfo:  # WHY: `--flag=value` form must not slip past by string mismatch.
            _guard()(["--test-interactive=1"])  # WHY: argparse tokenises `=` so guard must split on it too.
        assert excinfo.value.code == 2  # WHY: same exit convention as bare variant.
        assert "--testinteractive" in capsys.readouterr().err  # WHY: suggestion still surfaced.

    def test_supported_spelling_is_passthrough(self) -> None:
        """The supported spelling `--testinteractive` is a no-op that returns None."""
        assert _guard()(["--testinteractive"]) is None  # WHY: correct spelling must not raise.

    def test_empty_argv_is_passthrough(self) -> None:
        """An empty argument list is a no-op."""
        assert _guard()([]) is None  # WHY: guard must not trigger on baseline no-arg invocation.

    def test_unrelated_flags_are_passthrough(self) -> None:
        """Flags that are not in the rejection table are not affected."""
        assert _guard()(["--menu", "1", "--org", "abc"]) is None  # WHY: only the specific bad spelling is gated.

    def test_hyphenated_variant_mixed_with_other_flags_is_rejected(self, capsys: pytest.CaptureFixture[str]) -> None:
        """The guard finds `--test-interactive` even when other flags precede/follow it."""
        with pytest.raises(SystemExit) as excinfo:  # WHY: prove the guard scans all tokens, not just argv[0].
            _guard()(["--debug", "--test-interactive", "--menu", "1"])  # WHY: realistic mixed-flag invocation.
        assert excinfo.value.code == 2  # WHY: same exit convention.
        assert "--testinteractive" in capsys.readouterr().err  # WHY: suggestion still surfaced.


class TestMainEntrypointGuardIntegration:
    """`MainEntrypoint.run` invokes the guard before `parser.parse_args()`."""

    def test_run_rejects_hyphenated_variant_before_parse(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When `sys.argv` contains `--test-interactive`, `MainEntrypoint.run` exits before dispatch."""
        parser_mock = MagicMock(spec=argparse.ArgumentParser)  # WHY: assert parse_args is NOT reached.
        parser_mock.parse_args.return_value = argparse.Namespace(  # WHY: safety net if guard fails to fire.
            standalone=False, debug=False, login=False, test=False, testinteractive=False
        )
        mocks: dict[str, Any] = {  # WHY: wire only the pre-guard steps the pipeline touches first.
            "_initialize_deferred_imports": MagicMock(),
            "InputUtils": MagicMock(),
            "_build_argument_parser": MagicMock(return_value=parser_mock),
            "_setup_runtime_flags": MagicMock(),
            "_initialize_dependencies": MagicMock(),
            "_establish_mist_session": MagicMock(),
            "_configure_runtime_options": MagicMock(),
            "_dispatch_main_mode": MagicMock(),
        }
        for attr_name, mock_obj in mocks.items():  # WHY: publish each mock as a MistHelper module attribute.
            monkeypatch.setattr(f"MistHelper.{attr_name}", mock_obj, raising=False)
        monkeypatch.setattr("sys.argv", ["MistHelper.py", "--test-interactive"])  # WHY: seed the guard input.

        with pytest.raises(SystemExit) as excinfo:  # WHY: the entrypoint must exit early via the guard.
            MainEntrypoint.run()

        assert excinfo.value.code == 2  # WHY: guard propagates exit code 2.
        captured = capsys.readouterr()  # WHY: verify stderr guidance surfaced through the pipeline.
        assert "--testinteractive" in captured.err  # WHY: supported spelling must be surfaced.
        # Critical: the pipeline must NOT have reached parse_args or any downstream step.
        parser_mock.parse_args.assert_not_called()  # WHY: guard runs BEFORE parse_args.
        mocks["_dispatch_main_mode"].assert_not_called()  # WHY: never silently proceed as if flag was omitted.
        mocks["_setup_runtime_flags"].assert_not_called()  # WHY: no downstream side effects on rejection.

    def test_run_allows_supported_spelling_through_pipeline(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The supported `--testinteractive` spelling still reaches `_dispatch_main_mode`."""
        parser_mock = MagicMock(spec=argparse.ArgumentParser)  # WHY: standard parser mock contract.
        parsed_args = argparse.Namespace(  # WHY: post-parse namespace fed to downstream steps.
            standalone=False, debug=False, login=False, test=False, testinteractive=True
        )
        parser_mock.parse_args.return_value = parsed_args  # WHY: entrypoint reads parse_args() result.
        mocks: dict[str, Any] = {  # WHY: same wiring as reject-test to prove positive path is untouched.
            "_initialize_deferred_imports": MagicMock(),
            "InputUtils": MagicMock(),
            "_build_argument_parser": MagicMock(return_value=parser_mock),
            "_setup_runtime_flags": MagicMock(),
            "_initialize_dependencies": MagicMock(),
            "_establish_mist_session": MagicMock(),
            "_configure_runtime_options": MagicMock(),
            "_dispatch_main_mode": MagicMock(),
        }
        for attr_name, mock_obj in mocks.items():  # WHY: publish each mock as a MistHelper module attribute.
            monkeypatch.setattr(f"MistHelper.{attr_name}", mock_obj, raising=False)
        monkeypatch.setattr("sys.argv", ["MistHelper.py", "--testinteractive"])  # WHY: seed the supported spelling.

        MainEntrypoint.run()  # WHY: must NOT raise; guard is a no-op for supported spellings.

        parser_mock.parse_args.assert_called_once()  # WHY: pipeline proceeded past the guard.
        mocks["_dispatch_main_mode"].assert_called_once_with(parsed_args)  # WHY: dispatch received parsed args.
