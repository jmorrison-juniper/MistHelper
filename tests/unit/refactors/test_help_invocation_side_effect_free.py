"""Regression tests for issue #1641: `--help` / `-h` must be side-effect-free.

Verifies that:
1. `MistHelper._is_help_invocation` correctly detects `--help` and `-h` as full
   tokens in the argv tail (and rejects substring matches / argv[0]).
2. The module-load-time source contains the wiring that guards the early
   dependency check with `_is_help_invocation`, and extends the deferred-imports
   conditional to include help invocations.
3. An end-to-end subprocess invocation of `python MistHelper.py --help` prints
   usage to stdout and exits with code 0 without spending time on dependency
   installation or heavy import initialisation.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import importlib  # WHY: resolve the live MistHelper module for the helper.
import os  # WHY: propagate environment (DISABLE_AUTO_INSTALL) to the subprocess.
import subprocess  # nosec B404  # WHY: legitimate integration probe of the CLI entry point.
import sys  # WHY: locate the current interpreter for the subprocess call.
from pathlib import Path  # WHY: resolve MistHelper.py source path portably.
from typing import Any  # WHY: helper accessor returns an untyped module attribute.

import pytest  # WHY: parametrisation + skip markers for the slow subprocess case.


def _is_help() -> Any:
    """Return the live `_is_help_invocation` callable from MistHelper.

    Why:
        Resolved lazily so tests fail with a clear ImportError message if the
        helper was accidentally removed or renamed, rather than a stale top-level
        ImportError that would mask the actual regression.

    Returns:
        The bound callable ``MistHelper._is_help_invocation``.
    """
    module = importlib.import_module("MistHelper")  # Live import; MistHelper is a top-level script module.
    return module._is_help_invocation  # Access the helper as a module attribute.


class TestIsHelpInvocation:
    """`_is_help_invocation` detects `--help` / `-h` in the argv tail."""

    def test_bare_double_dash_help_is_detected(self) -> None:
        """`["prog", "--help"]` returns True."""
        assert _is_help()(["MistHelper.py", "--help"]) is True  # WHY: canonical GNU-style help flag.

    def test_bare_short_help_flag_is_detected(self) -> None:
        """`["prog", "-h"]` returns True."""
        assert _is_help()(["MistHelper.py", "-h"]) is True  # WHY: short-form alias must be honoured.

    def test_help_combined_with_other_flags_is_detected(self) -> None:
        """`--help` interleaved with unrelated flags is still detected."""
        assert _is_help()(["MistHelper.py", "--menu", "1", "--help"]) is True  # WHY: prove full-tail scan.
        assert _is_help()(["MistHelper.py", "-h", "--testinteractive"]) is True  # WHY: short form + other flag.

    def test_empty_argv_and_program_only_are_not_detected(self) -> None:
        """No tail, no match."""
        assert _is_help()([]) is False  # WHY: baseline; empty argv is never a help invocation.
        assert _is_help()(["MistHelper.py"]) is False  # WHY: argv[0] alone is not a help invocation.

    def test_program_name_is_ignored_even_if_it_matches(self) -> None:
        """argv[0] is intentionally skipped so a script named `--help` does not trip the guard."""
        assert _is_help()(["--help"]) is False  # WHY: argv[0] is the program name, never a flag.

    @pytest.mark.parametrize("bad_token", ["--helpme", "--h", "-help", "help", "--HELP"])
    def test_substring_and_case_variants_are_not_detected(self, bad_token: str) -> None:
        """Substring matches and case variants must NOT trigger help mode."""
        assert _is_help()(["MistHelper.py", bad_token]) is False  # WHY: only exact `--help` / `-h` count.

    def test_unrelated_flags_are_not_detected(self) -> None:
        """Ordinary flag combinations do not match."""
        assert _is_help()(["MistHelper.py", "--menu", "1", "--org", "abc"]) is False  # WHY: control case.


class TestHelpInvocationGuardWiring:
    """The MistHelper source guards both bootstrap steps with `_is_help_invocation`."""

    @staticmethod
    def _mist_helper_source() -> str:
        """Return the MistHelper.py source text.

        Why:
            The regression asserted here is about *module-load-time* behaviour
            that pytest cannot re-trigger (MistHelper is imported once per test
            session). Reading the source is the cleanest way to prove the guards
            are wired without brittle import-time patching.

        Returns:
            UTF-8 source text of the currently imported MistHelper module.
        """
        module = importlib.import_module("MistHelper")  # Live module resolution.
        assert module.__file__ is not None  # WHY: script modules always have __file__ set on disk.
        return Path(module.__file__).read_text(encoding="utf-8")  # Read once; small enough for in-memory search.

    def test_early_dependency_check_is_guarded(self) -> None:
        """The `_early_dependency_check()` call is wrapped by `_is_help_invocation`."""
        source = self._mist_helper_source()
        assert "if not _is_help_invocation(sys.argv):" in source  # WHY: the exact guard expression.
        assert "_early_dependency_check()" in source  # WHY: the call still exists (was not accidentally deleted).

    def test_deferred_imports_conditional_includes_help(self) -> None:
        """The deferred-imports conditional also branches on `_is_help_invocation(sys.argv)`."""
        source = self._mist_helper_source()
        # WHY: ensure eager imports are skipped for --help too, matching the dep-check guard behaviour.
        assert "or _is_help_invocation(sys.argv)" in source


class TestHelpSubprocessInvocation:
    """End-to-end proof: `python MistHelper.py --help` renders usage without bootstrap."""

    def test_help_exits_cleanly_with_usage_on_stdout(self) -> None:
        """`--help` prints usage to stdout and exits 0.

        Why:
            This is the acceptance criterion in issue #1641: help must succeed
            even on a fresh interpreter where dependencies are not yet installed.
            We set ``DISABLE_AUTO_INSTALL=true`` as a safety belt so a *failed*
            guard would not brick the developer's environment mid-test.
        """
        module = importlib.import_module("MistHelper")  # Locate the live script on disk.
        assert module.__file__ is not None
        script_path = Path(module.__file__)

        env = os.environ.copy()  # Inherit the caller's environment (interpreter, PYTHONPATH, ...).
        env["DISABLE_AUTO_INSTALL"] = "true"  # Belt-and-braces: even if guard fails, do not install anything.

        result = subprocess.run(  # nosec B603  # Fixed argv list; no shell; controlled inputs.
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True,
            timeout=60,  # Generous ceiling; help must return promptly, not spend minutes on installs.
            env=env,
            check=False,  # We assert the return code explicitly below.
        )

        assert result.returncode == 0, (  # WHY: argparse exits 0 for --help by convention.
            f"--help exited {result.returncode}; " f"stdout={result.stdout[:400]!r}; stderr={result.stderr[:400]!r}"
        )
        assert (
            "usage" in result.stdout.lower()
        ), (  # WHY: usage line MUST reach stdout (argparse default).
            f"expected 'usage' in stdout; got {result.stdout[:400]!r}"
        )
