"""Pytest configuration for MistHelper test suite.

Provides test isolation: temp directories, no network, no .env loading.
Unit tests must run offline with zero API credentials in under 30 seconds.

This file also guards the test environment. A new git worktree holds the tracked
files only, so the worktree has no `.venv` directory. Without the runtime
dependencies, pytest stops with one import error for each test module, and the
reader sees a source defect that does not exist. The guard below replaces those
errors with one message that names the bootstrap command. See issue #1866.
"""

import importlib.util
import logging
import os
import sys
from pathlib import Path

import pytest

# Issue #1991 records the fault this line prevents. A stand-in that answers a
# simpler shape than the real callee agreed with its own reader and disagreed
# with the cloud, and the whole suite stayed green. With this variable set, every
# portal seam compares the injected stand-in against the real callee and raises
# on a difference. A live portal never sets the variable, so a live portal warns
# instead of breaking. See `src/upgrade_portal/app/seam_shapes.py`.
os.environ.setdefault("UPGRADE_PORTAL_SEAM_STRICT", "1")

# Runtime packages that almost every test module imports through `src`. Keep the
# list short, because the guard runs before every test session. `paramiko` sits
# on the import path of `MistHelper.py`, so its absence stops that module part
# way and hides the cause behind a wrong AttributeError. See issue #1923.
_REQUIRED_RUNTIME_PACKAGES: tuple[str, ...] = ("mistapi", "structlog", "dotenv", "paramiko")

# The documented command that creates `.venv` and installs the dependencies.
_BOOTSTRAP_COMMAND = "python scripts/bootstrap_worktree.py"

# The attribute that records why `MistHelper.py` stopped part way through its
# module body. `src/firmware/firmware_manager.py` reads this name and reports the
# recorded cause instead of a wrong "no attribute" message. See issue #1923.
_IMPORT_ERROR_ATTRIBUTE = "__misthelper_import_error__"

# The repository that holds this file. Every `src` import must resolve inside it.
_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

# The command that removes a stale copy of the repository from the environment.
_UNINSTALL_COMMAND = "python -m pip uninstall -y misthelper"


def _shadowing_source_path() -> Path | None:
    """Return the path of a `src` package that sits outside this repository.

    Why:
        Issue #2010 records the fault. `pyproject.toml` sets
        `[tool.hatch.build.targets.wheel] packages = ["."]`, so a `pip install .`
        of this project copies the whole repository root into `site-packages`.
        That copy holds a directory named `src`, and `site-packages` sits on
        `sys.path` ahead of the working directory for a script that runs from
        elsewhere.

        Every import then reads the stale copy. Both copies import cleanly, so no
        gate reports the difference, and a green test run proves nothing about
        the repository.

    Returns:
        The path of the shadowing package, or None when `src` resolves here.
    """
    try:  # A broken or absent entry raises here rather than answering None.
        found = importlib.util.find_spec("src")  # Ask for the location only, so no module body runs.
    except (ImportError, ValueError):  # A broken entry cannot shadow anything.
        return None  # The other guard reports an absent dependency.
    origin = getattr(found, "origin", None) if found is not None else None  # None for a namespace package.
    if origin is None:  # No file means no shadow this guard can name.
        return None  # Leave the session alone.
    resolved = Path(origin).resolve()  # Compare real paths, because a link would defeat a text compare.
    if resolved.is_relative_to(_REPOSITORY_ROOT):  # The normal case, and the quiet one.
        return None  # The tests read the repository.
    return resolved  # The tests would read a copy, so the caller stops the session.


def _shadow_message(found: Path) -> str:
    """Build one actionable message that names the stale copy and the repair step."""
    return (  # One block of text, because pytest prints a UsageError as a single record.
        f"The name 'src' resolves outside this repository, so the tests would read a stale copy. "
        f"Resolved path: {found}. Repository: {_REPOSITORY_ROOT}. "
        f"Warning: a run against the stale copy tests code that nobody ships, and both copies "
        f"import cleanly, so a green result would prove nothing. "
        f"A 'pip install .' of this project puts that copy in site-packages, because the wheel "
        f"packs the repository root. "
        f"To repair the environment, run '{_UNINSTALL_COMMAND}'. Then run the tests again. "
        f"See issue #2010."
    )


def _find_missing_packages(names: tuple[str, ...]) -> list[str]:
    """Return each name in `names` that the active interpreter cannot import."""
    missing: list[str] = []  # Collect every absent name, so one message lists all of them.
    for name in names:  # Test each name on its own, because one gap breaks the collection.
        try:  # Guard the lookup, because a broken module entry raises here.
            available = importlib.util.find_spec(name) is not None  # Ask for the location only, so the import is cheap.
        except (ImportError, ValueError):  # A broken or shadowed entry is not usable.
            available = False  # Report the broken entry as an absent package.
        if not available:  # Keep only the names that the interpreter cannot import.
            missing.append(name)  # Add the name to the report list.
    return missing  # Give the caller the full result of one scan.


def _bootstrap_message(missing: list[str]) -> str:
    """Build one actionable message that names the gap and the repair step."""
    names = ", ".join(missing)  # Join the names, so the reader sees every gap on one line.
    return (  # Return one block of text, because pytest prints a UsageError as a single record.
        f"The active Python environment has no MistHelper runtime dependencies. "
        f"Missing packages: {names}. "
        f"Active interpreter: {sys.executable}. "
        f"Caution: 'git worktree add' does not copy the .venv directory, so the tests "
        f"ran against the global interpreter and every test module failed to import. "
        f"To repair the environment, run '{_BOOTSTRAP_COMMAND}' in this worktree. "
        f"Then activate the environment. On Windows, run '.venv\\Scripts\\Activate.ps1'. "
        f"On Linux, run 'source .venv/bin/activate'. Then run the tests again."
    )


def pytest_configure(config: pytest.Config) -> None:
    """Stop the session with one message when the environment cannot serve the tests."""
    logging.info("Checking the test environment for the MistHelper runtime dependencies")
    missing = _find_missing_packages(_REQUIRED_RUNTIME_PACKAGES)  # Scan the short required list once.
    logging.debug("Environment check found %d missing runtime package(s)", len(missing))
    if missing:  # Report the environment gap before pytest collects a single module.
        raise pytest.UsageError(_bootstrap_message(missing))  # Raise one clear error instead of many import errors.
    logging.info("Checking that the name 'src' resolves inside this repository")  # Issue #2010.
    shadow = _shadowing_source_path()  # None in a healthy environment.
    logging.debug("The shadow check found %s", shadow if shadow is not None else "no stale copy")
    if shadow is not None:  # A stale copy would make every result meaningless.
        raise pytest.UsageError(_shadow_message(shadow))  # Name the copy and the removal command.


# Pre-load MistHelper.py (the script) into sys.modules as "MistHelper".
# The project root has an __init__.py which makes the root directory a Python
# package — so `import MistHelper` would normally resolve to __init__.py (empty).
# We force-replace the module in sys.modules with the actual MistHelper.py script.
_mh_path = Path(__file__).parents[1] / "MistHelper.py"
_existing = sys.modules.get("MistHelper")
_is_init = _existing is not None and getattr(_existing, "__file__", "").endswith("__init__.py")
if _mh_path.exists() and (_existing is None or _is_init):
    _spec = importlib.util.spec_from_file_location("MistHelper", _mh_path)
    _mod = importlib.util.module_from_spec(_spec)  # type: ignore[assignment]
    sys.modules["MistHelper"] = _mod
    try:
        _spec.loader.exec_module(_mod)  # type: ignore[union-attr]
    except SystemExit as _exit_signal:
        # MistHelper.py calls sys.exit() during import. The module body stops at
        # that call, so the names below it never bind. Record the cause. #1923.
        setattr(_mod, _IMPORT_ERROR_ATTRIBUTE, _exit_signal)  # Keep the real cause on the half-built module.
    except (ImportError, ModuleNotFoundError) as _import_failure:
        # A dependency is absent, so the module body stops at that import and the
        # names below it never bind. Record the cause, because the half-built
        # module stays in sys.modules and later hides this error. See #1923.
        logging.info("MistHelper.py stopped part way through its import: %s", _import_failure)  # Log the cause.
        setattr(_mod, _IMPORT_ERROR_ATTRIBUTE, _import_failure)  # Keep the real cause on the half-built module.
        logging.debug("Recorded the import failure as %s", _IMPORT_ERROR_ATTRIBUTE)  # Log the result.


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Provide a temporary data directory for test file output."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def tmp_jsonl_file(tmp_data_dir):
    """Provide a temporary JSONL file path for telemetry tests."""
    return str(tmp_data_dir / "test_events.jsonl")


@pytest.fixture(autouse=True)
def isolate_working_directory(tmp_path, monkeypatch):
    """Ensure tests never write to the real data/ directory."""
    monkeypatch.chdir(tmp_path)
