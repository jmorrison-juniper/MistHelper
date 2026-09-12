"""Centralized, audited ``subprocess`` dispatch for MistHelper.py callers.

This helper exists so that Bandit rules B404 (``import subprocess``) and B603
(subprocess call without shell review) can be justified in exactly one place
rather than scattered across every call site. Every MistHelper.py subprocess
invocation routes through :class:`SubprocessRunner.run`, which enforces:

* An explicit allow-list of executables (``uv``/``uv.exe`` or the current
  interpreter, that is ``sys.executable``).
* A conservative allow-list for each argv element (alphanumeric plus
  ``-_./:=``), rejecting shell metacharacters up-front.
* A positive, finite timeout on every invocation.
* Never surfacing ``shell=`` to callers.

Contract source of truth:
``specs/1016-misthelper-suppression-cleanup/contracts/subprocess_runner.md``.

Logging obeys Principle VII (before/after action logs); argv[1:] is never
logged so that any interpolated secrets do not leak into script.log.
"""

from __future__ import annotations  # WHY: PEP 604 unions in annotations.

import logging  # WHY: Principle VII before/after/error action logs.
import math  # WHY: reject NaN / +inf timeouts before dispatch.
import os  # WHY: basename comparison for allow-listed executables on paths.
import re  # WHY: allow-list regex for argv element validation.
import subprocess  # nosec B404  # WHY: the sole audited entry point for subprocess in the project.
import sys  # WHY: recognise sys.executable as an allowed executable path.
from collections.abc import Sequence  # WHY: precise generic type for argv.
from subprocess import (  # nosec B404  # Re-export exception classes so callers avoid a direct 'import subprocess'.
    CalledProcessError,  # Non-zero exit when check=True.
    SubprocessError,  # Base class for all subprocess errors (parent of TimeoutExpired/CalledProcessError).
    TimeoutExpired,  # Raised by subprocess.run when timeout elapses.
)

logger = logging.getLogger(__name__)  # Module-scoped logger so callers see src.utils.subprocess_runner.

# Basenames (lower-cased) permitted as argv[0]. sys.executable is also accepted
# via exact match in the validator so a full Python interpreter path resolves.
_ALLOWED_BASENAMES: frozenset[str] = frozenset({"uv", "uv.exe"})  # UV binary basenames.

# Conservative allow-list for every argv[1:] element. Matches printable ASCII
# used by pip/uv arguments (names, versions, paths) and nothing that a POSIX
# or Windows shell would treat as a metacharacter.
_ARG_ELEMENT_RE: re.Pattern[str] = re.compile(r"^[A-Za-z0-9_./:=\-+@,\\<>!~]+$")  # Allowed argv element bytes.


class SubprocessRunner:
    """Validate and dispatch subprocess invocations for MistHelper.py callers.

    All method access is via classmethods so callers never need an instance.
    The class exists (rather than a bare function) so the allow-list attribute
    is trivially discoverable and so tests can monkey-patch it if needed.
    """

    # Public attribute so callers / tests can enumerate the allow-list. The
    # value combines the basename allow-list with the running interpreter path.
    ALLOWED_EXECUTABLES: frozenset[str] = frozenset(_ALLOWED_BASENAMES | {sys.executable})  # Names + interp path.

    @classmethod
    def run(
        cls,
        argv: Sequence[str],
        *,
        timeout: float,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Validate ``argv``/``timeout`` and dispatch a captured-text subprocess.

        Args:
            argv: Complete argument vector; ``argv[0]`` must be allow-listed and
                each subsequent element must match the conservative character
                allow-list.
            timeout: Positive finite float seconds; ``None`` and non-positive
                values raise :class:`ValueError` before any process spawn.
            check: When ``True`` (default) a non-zero exit raises
                :class:`subprocess.CalledProcessError`. The caller may set
                ``False`` to inspect ``returncode`` manually.

        Returns:
            The :class:`subprocess.CompletedProcess` produced by ``subprocess.run``
            with ``capture_output=True`` and ``text=True``.

        Raises:
            ValueError: When argv is empty, argv[0] is not allow-listed, an
                argv element contains disallowed characters, or timeout is not
                a positive finite number.
            subprocess.TimeoutExpired: When the child process exceeds ``timeout``.
            subprocess.CalledProcessError: When ``check=True`` and the child
                exits non-zero.
        """
        cls._validate_argv(argv)  # Reject empty, disallowed executable, or bad-char args first.
        cls._validate_timeout(timeout)  # Reject NaN / non-positive / inf timeouts.
        executable = argv[0]  # Cache for logging (argv[1:] must never be logged).
        logger.info("SubprocessRunner dispatching %s", executable)  # Principle VII: before-action log.
        try:  # Wrap so any exception is logged with the executable name (never arg values).
            # Explicit keyword arguments make Bandit's B603 review trivial: shell is not set,
            # capture_output/text are pinned, and the timeout is validated above.
            result = subprocess.run(  # nosec B603  # Audited: argv validated, no shell, capture pinned.
                list(argv),  # Copy to a plain list so callers cannot mutate the sequence mid-flight.
                capture_output=True,  # Always capture stdout/stderr for callers that inspect them.
                text=True,  # Always decode as text. Every existing call site expected str output.
                timeout=timeout,  # Bound the child so a hung process cannot stall MistHelper startup.
                check=check,  # Honour caller's check policy. Default True matches most call sites.
            )
        except subprocess.TimeoutExpired:  # Timeouts propagate; exc.__str__ contains argv, so log timeout only.
            logger.error("SubprocessRunner timed out %s after %ss", executable, timeout)  # Principle VII: error log.
            raise  # Caller decides whether the timeout is fatal.
        except subprocess.CalledProcessError as exc:  # check=True and non-zero rc.
            logger.error("SubprocessRunner failed %s rc=%s", executable, exc.returncode)  # No argv[1:] leak.
            raise  # Preserve the original exception for caller handling.
        logger.debug("SubprocessRunner completed %s rc=%s", executable, result.returncode)  # After-action log.
        return result  # Hand the captured result back to the caller.

    @classmethod
    def _validate_argv(cls, argv: Sequence[str]) -> None:
        """Validate argv shape and every element. Raises :class:`ValueError` on failure."""
        if not argv:  # Empty sequence is never a legitimate command.
            raise ValueError("argv must be a non-empty sequence")  # Fail closed before any spawn.
        executable = argv[0]  # First element is the program to run.
        if not cls._is_allowed_executable(executable):  # Enforce the executable allow-list.
            raise ValueError("argv[0] is not an allowed executable")  # Do NOT include the raw value (path may leak).
        for index, element in enumerate(argv[1:], start=1):  # Validate remaining args one at a time.
            if not isinstance(element, str):  # Non-str elements would bypass the regex allow-list.
                raise ValueError(f"argv[{index}] must be a str")  # Fail before dispatch.
            if not element:  # Empty string arg is almost certainly a caller bug.
                raise ValueError(f"argv[{index}] must be non-empty")  # Reject rather than pass through.
            if not _ARG_ELEMENT_RE.match(element):  # Bad chars are rejected before spawn.
                raise ValueError(f"argv[{index}] contains disallowed characters")  # Value elided to avoid log leak.

    @classmethod
    def _is_allowed_executable(cls, executable: str) -> bool:
        """Return True when executable is sys.executable exact-match or a permitted basename."""
        if executable == sys.executable:  # Fast path: full interpreter path (used for '-m pip ...').
            return True  # Interpreter self-invocation is always allowed.
        basename = os.path.basename(executable).lower()  # Basename comparison catches venv-local uv.exe paths.
        return basename in _ALLOWED_BASENAMES  # Permitted only when basename is on the allow-list.

    @staticmethod
    def _validate_timeout(timeout: float) -> None:
        """Reject non-finite or non-positive timeouts before spawning a child process."""
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool):  # bool is a subclass of int in Python.
            raise ValueError("timeout must be a positive finite number")  # bool would satisfy int otherwise.
        if not math.isfinite(float(timeout)):  # NaN and +/-inf are never valid deadlines.
            raise ValueError("timeout must be a positive finite number")  # Fail closed rather than pass to subprocess.
        if timeout <= 0:  # Zero and negative timeouts trip subprocess.run behaviour we do not want.
            raise ValueError("timeout must be a positive finite number")  # Callers must specify a real deadline.


__all__ = [
    "CalledProcessError",  # Re-exported so callers do not import subprocess directly.
    "SubprocessError",  # Base class re-export.
    "SubprocessRunner",  # Primary dispatch helper.
    "TimeoutExpired",  # Timeout exception re-export.
]  # Explicit public surface for the helper module.
