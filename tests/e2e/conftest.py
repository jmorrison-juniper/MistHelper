"""Pytest fixtures for the MistHelper end-to-end tests of the legacy web portal.

The fixtures below build a Flask test client, which needs no browser and no
server process. That client is fast and it runs in continuous integration.

Why this file starts no server:
    A server fixture here once started Gunicorn, and no test ever used it.
    Gunicorn imports `fcntl`, which Windows does not hold, so that fixture could
    not run on a developer workstation at all. The upgrade portal tests start
    their own server in `tests/e2e/upgrade_portal/conftest.py`, which selects
    Waitress on Windows and Gunicorn elsewhere.

Why this file arms a second timer:
    `pytest-timeout` arms one timer for the setup, the call, and the teardown of
    each item. Pytest ends every session fixture inside the teardown phase of
    the last item, so that teardown once shared the 120 second budget of one
    test. A slow teardown then ended the process through `os._exit(1)`, and
    pytest wrote no report. Issue #3517 holds the measured evidence.
"""

import json
import logging
import math
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

logger = logging.getLogger(__name__)  # A module logger keeps the record source readable.

E2E_TIMEOUT_SECONDS = 120  # Bound each E2E test, so one browser wait cannot stop the suite for hours.


class SessionTeardownBudget:
    """Give the session teardown of the last item a budget of its own.

    Why:
        The session fixtures of the E2E suite stop a portal, replay a run
        trail, compare a checkout trail, and close a browser. Those steps cost
        more than one test, and they must not consume the budget of the last
        test. This class replaces the item timer at the start of that teardown.
    """

    DEFAULT_SECONDS = 300.0  # 2.5 times the item budget, which covers a slow browser close.
    ENVIRONMENT_NAME = "MISTHELPER_E2E_TEARDOWN_BUDGET_SECONDS"  # The documented override.

    @classmethod
    def seconds(cls) -> float:
        """Read the teardown budget in seconds.

        Returns:
            The override value when the environment holds one, and the default
            otherwise.

        Raises:
            ValueError: The override is not a positive finite number.
        """
        raw_value = os.environ.get(cls.ENVIRONMENT_NAME, "").strip()  # Read the documented override.
        if not raw_value:  # An absent override keeps the documented default.
            return cls.DEFAULT_SECONDS  # Use the constant that the plan records.
        try:  # A wrong value must report itself instead of falling back in silence.
            value = float(raw_value)  # Parse the override as a number of seconds.
        except ValueError as error:  # Report the exact variable and the exact value.
            raise ValueError(f"{cls.ENVIRONMENT_NAME} must hold a number, not {raw_value!r}.") from error
        if not math.isfinite(value) or value <= 0:  # A budget must be finite and positive.
            raise ValueError(f"{cls.ENVIRONMENT_NAME} must hold a positive finite number, not {raw_value!r}.")
        return value  # Hand back the validated override.

    @classmethod
    def build_settings(cls, item: pytest.Item, seconds: float) -> Any:
        """Build the pytest-timeout settings for the replacement timer.

        Args:
            item: The last item of the session.
            seconds: The teardown budget in seconds.

        Returns:
            A `pytest_timeout.Settings` record that keeps the configured method.
        """
        from pytest_timeout import Settings  # Import here, because the plugin can be absent.

        option_method = item.config.getoption("timeout_method", None)  # Read the command option.
        method = option_method or item.config.getini("timeout_method")  # Keep the method.
        debugger_option = item.config.getoption("timeout_disable_debugger_detection", None)  # Read the option.
        debugger_ini = item.config.getini("timeout_disable_debugger_detection")  # Read the settings file.
        debugger = bool(debugger_option or debugger_ini)  # Keep the configured debugger behavior.
        return Settings(seconds, method or "thread", False, debugger)  # Keep the whole phase.

    @classmethod
    def arm(cls, item: pytest.Item, nextitem: pytest.Item | None) -> float | None:
        """Replace the item timer with the teardown timer for the last item.

        Why:
            `pytest_timeout_set_timer` writes `item.cancel_timeout`, so the
            replacement overwrites that attribute. The cancel call that the
            plugin already makes after its own protocol wrapper then cancels
            this replacement timer, and this repair adds no second cancel path.

        Args:
            item: The item whose teardown phase starts now.
            nextitem: The next item, or `None` for the last item of the session.

        Returns:
            The armed budget in seconds, or `None` when this hook did nothing.
        """
        if nextitem is not None:  # Only the last item tears down the session fixtures.
            return None  # Leave every other teardown on the item budget.
        if not item.config.pluginmanager.hasplugin("timeout"):  # No plugin means no timer to replace.
            return None  # The collection hook already skips the suite in that case.
        if not hasattr(item, "cancel_timeout"):  # The plugin arms no timer when no budget applies.
            return None  # Do not add a bound that the configuration did not ask for.
        seconds = cls.seconds()  # Read and validate the teardown budget.
        logger.info("Arming the E2E session teardown budget of %s seconds", seconds)  # Log before the swap.
        item.config.hook.pytest_timeout_cancel_timer(item=item)  # Cancel the shared item timer.
        settings = cls.build_settings(item, seconds)  # Build the teardown settings record.
        item.config.hook.pytest_timeout_set_timer(item=item, settings=settings)  # Arm the new timer.
        logger.debug("Armed the E2E session teardown budget for %s", item.nodeid)  # Log the armed item.
        return seconds  # Report the armed budget to the caller.


class PhaseTrailWriter:
    """Append one JSON line for each pytest phase report.

    Why:
        A fired budget still ends the process through `os._exit(1)`, so a bound
        alone does not save the evidence. One append and one close for each
        phase puts the bytes in the operating system before the next phase
        starts, and `os._exit` does not lose them.
    """

    ENVIRONMENT_NAME = "MISTHELPER_E2E_PHASE_TRAIL"  # The documented override of the trail path.
    DEFAULT_PATH = Path(__file__).resolve().parents[2] / "test-artifacts" / "e2e-phase-trail.jsonl"

    @classmethod
    def path(cls) -> Path:
        """Return the trail path.

        Returns:
            The override path when the environment holds one, and the default
            path under `test-artifacts/` otherwise.
        """
        raw_value = os.environ.get(cls.ENVIRONMENT_NAME, "").strip()  # Read the documented override.
        if not raw_value:  # An absent override keeps the repository artifact path.
            return cls.DEFAULT_PATH  # Use the path that the plan records.
        return Path(raw_value).expanduser().resolve()  # Build the override path for this platform.

    @classmethod
    def record(cls, report: pytest.TestReport) -> dict[str, object]:
        """Build the record of one phase report.

        Args:
            report: The phase report that pytest produced.

        Returns:
            A dictionary with the node identifier, the phase, the outcome, the
            duration in seconds, and a UTC ISO 8601 timestamp. It holds no
            other field, so it carries no credential and no payload.
        """
        return {  # Keep the field set small, because this file leaves the machine as evidence.
            "node_id": report.nodeid,  # Name the test that the record describes.
            "phase": report.when,  # Name the setup, the call, or the teardown phase.
            "outcome": report.outcome,  # Record the passed, failed, or skipped result.
            "duration_seconds": round(float(report.duration), 6),  # Record the measured cost.
            "timestamp_utc": datetime.now(UTC).isoformat(),  # Record the UTC ISO 8601 time.
        }

    @classmethod
    def write(cls, report: pytest.TestReport) -> None:
        """Append one record to the trail file.

        Args:
            report: The phase report that pytest produced.

        Raises:
            RuntimeError: The trail directory or the trail file rejected the write.
        """
        target = cls.path()  # Resolve the trail path for this run.
        line = json.dumps(cls.record(report), sort_keys=True)  # Build one ASCII JSON line.
        logger.info("Writing an E2E phase record for %s", report.nodeid)  # Log before the file write.
        try:  # A file error must name the path, because the trail is the evidence of a stopped run.
            target.parent.mkdir(parents=True, exist_ok=True)  # Create the artifact directory one time.
            with target.open("a", encoding="ascii") as handle:  # Append, then close, so the bytes leave Python.
                handle.write(line + "\n")  # Write exactly one record on one line.
        except OSError as error:  # Report the path and the cause instead of losing the evidence in silence.
            logger.error("Cannot write the E2E phase trail to %s: %s", target, error)  # Log the full context.
            raise RuntimeError(f"Cannot write the E2E phase trail to {target}: {error}") from error
        logger.debug("Wrote an E2E phase record for %s in phase %s", report.nodeid, report.when)  # Log the result.


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Add a per-test timeout to every E2E item.

    Why:
        Browser tests can wait on a page, a browser, or a server. A missing
        boundary can then block a full suite for hours. This hook applies only
        inside the ``tests/e2e`` tree, so unit and contract tests keep their
        existing timing.

    Args:
        config: The active pytest configuration.
        items: The E2E test items that pytest collected under this directory.
    """
    logger.info("Checking the E2E timeout guard")  # Log before the plugin check.
    timeout_is_ready = config.pluginmanager.hasplugin("timeout")  # Confirm that pytest-timeout loaded.
    logger.debug("E2E timeout plugin loaded: %s", timeout_is_ready)  # Log the plugin state.
    if not timeout_is_ready:  # A missing guard must not let browser tests hang.
        logger.info("Adding E2E skip marks because pytest-timeout is missing")  # Log before the skip marks.
        skip_mark = pytest.mark.skip(  # Build one skip mark with the exact missing guard.
            reason="pytest-timeout is not installed, so the E2E timeout guard cannot run."
        )
        for item in items:  # Apply the skip to every collected E2E item.
            item.add_marker(skip_mark)  # Skip unsafe E2E tests instead of letting them run unbounded.
        logger.debug("Added E2E skip marks to %d items", len(items))  # Log the number of skipped items.
        return  # Stop before the timeout mark, because the plugin is not present.
    logger.info("Adding per-test timeout marks to E2E tests")  # Log before the timeout marks.
    timeout_mark = pytest.mark.timeout(E2E_TIMEOUT_SECONDS)  # Use the declared pytest-timeout plugin.
    marked_count = 0  # Count items that this hook protects.
    for item in items:  # Visit each collected E2E item once.
        if any(mark.name == "timeout" for mark in item.iter_markers()):  # Keep a narrower explicit timeout.
            continue  # Preserve an item-specific timeout from a test module.
        item.add_marker(timeout_mark)  # Bound this E2E test with the default guard.
        marked_count += 1  # Count the guard that this hook added.
    logger.debug("Added E2E timeout marks to %d items", marked_count)  # Log the number of protected items.


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_teardown(item: pytest.Item, nextitem: pytest.Item | None) -> None:
    """Give the teardown of the last item its own budget.

    Why:
        Pytest ends every session fixture inside the teardown phase of the last
        item. Without this hook that teardown shares the 120 second budget of
        one test, and a slow teardown ends the process before the report.
        Issue #3517 holds the measured evidence.

    Args:
        item: The item whose teardown phase starts now.
        nextitem: The next item, or `None` for the last item of the session.
    """
    SessionTeardownBudget.arm(item, nextitem)  # Swap the timer only for the last item of the session.


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Record one durable line for each pytest phase report.

    Why:
        A fired budget ends the process through `os._exit(1)`, so pytest writes
        no report. This trail keeps the name and the outcome of each phase that
        finished before the stop.

    Args:
        report: The phase report that pytest produced.
    """
    PhaseTrailWriter.write(report)  # Append the record before the next phase can start.


@pytest.fixture(scope="session")
def flask_app():
    """Create a Flask app instance for testing without API authentication.

    Uses the static menu registry (no MistHelper import needed).
    Returns the Flask app with test config applied.
    """
    os.environ.setdefault("PORTAL_TITLE", "MistHelper Test")
    os.environ.setdefault("PORTAL_THEME", "dark")

    from web_portal.app import WebPortalApp
    from web_portal.menu_registry import build_static_menu_actions

    menu_actions = build_static_menu_actions()
    app = WebPortalApp.create_app(
        apisession=None,
        menu_actions=menu_actions,
        org_id="test-org-id",
    )
    app.config["TESTING"] = True
    yield app  # Hand the app to every test in the session.
    # Stop the heartbeat thread and drain the pool now, while streams are still open.
    # Without this, the atexit hook still runs, but only after pytest closes its
    # own capture streams, so its shutdown log lines fail with a closed-file error.
    WebPortalApp.shutdown_app(app)


@pytest.fixture(scope="session")
def client(flask_app):
    """Flask test client for fast E2E-style tests without a browser."""
    return flask_app.test_client()
