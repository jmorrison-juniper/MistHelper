"""Tests that one event stream cannot hold a worker thread forever.

Issue #3164 recorded a portal outage. Gunicorn ran four threads, and the
event stream held one thread for the whole life of a browser tab. Four open
tabs took every thread, and the portal stopped answering every request.

These tests hold two repairs in place. The stream closes itself after a
fixed time, and an unknown run identifier never opens a stream at all.
"""

import re
from pathlib import Path

import pytest

from web_portal.app import WebPortalApp
from web_portal.menu_registry import build_static_menu_actions
from web_portal.routes import operations as operations_routes

# The start script that sizes the Gunicorn thread pool.
START_SCRIPT = Path(__file__).resolve().parents[3] / "container" / "scripts" / "start.sh"

# The thread count that caused the outage. The pool must hold more than this.
OUTAGE_THREAD_COUNT = 4


@pytest.fixture
def portal_client():
    """Return a Flask test client for the real portal application."""
    # build_static_menu_actions avoids a MistHelper import, matching the other portal tests.
    app = WebPortalApp.create_app(apisession=None, menu_actions=build_static_menu_actions(), org_id="test-org-id")
    app.config["TESTING"] = True  # Let the client surface an error instead of an HTML page.
    with app.test_client() as client:
        yield client
    executor = app.config.get("OPERATION_EXECUTOR")  # Read the executor, so teardown can close its pool.
    if executor is not None:
        executor.shutdown()  # Close the pool, so the test leaves no worker thread behind.
    event_bus = app.config.get("EVENT_BUS")  # Read the bus, so teardown can end its heartbeat thread.
    if event_bus is not None:
        event_bus.stop()  # End the heartbeat thread, so the test leaks nothing.


def test_unknown_run_id_never_opens_a_stream(portal_client):
    """An unknown run identifier returns 404 and holds no thread."""
    # A stream for a run that does not exist would heartbeat until the tab closed.
    response = portal_client.get("/api/operations/stream?run_id=no-such-run")
    assert response.status_code == 404  # The route must refuse the request outright.
    assert "Unknown run_id" in response.get_data(as_text=True)  # The body must name the reason.


def test_missing_run_id_never_opens_a_stream(portal_client):
    """A request with no run identifier returns 404 and holds no thread."""
    # A missing identifier reaches the same unknown-run path, so it must be refused too.
    response = portal_client.get("/api/operations/stream")
    assert response.status_code == 404  # The route must refuse the request outright.


def test_stream_cap_defaults_to_a_bounded_value():
    """The shipped stream cap is a positive, finite number of seconds."""
    # An unbounded default would return the portal to the outage state.
    assert operations_routes.DEFAULT_STREAM_MAX_SECONDS > 0  # A cap of zero would close every stream at once.
    assert operations_routes.DEFAULT_STREAM_MAX_SECONDS <= 3600  # An hour-long stream still holds a thread too long.


def test_stream_cap_reads_the_environment(monkeypatch):
    """An operator can shorten or lengthen the cap through the environment."""
    monkeypatch.setenv("PORTAL_STREAM_MAX_SECONDS", "12.5")  # Set a value the default does not use.
    assert operations_routes._stream_max_seconds() == 12.5  # The helper must return the operator value.


@pytest.mark.parametrize("bad_value", ["not-a-number", "0", "-5"])
def test_stream_cap_rejects_an_unusable_value(monkeypatch, bad_value):
    """A bad environment value falls back to the shipped default."""
    # A zero or negative cap would close every stream at once, so the helper must refuse it.
    monkeypatch.setenv("PORTAL_STREAM_MAX_SECONDS", bad_value)  # Supply the value under test.
    assert operations_routes._stream_max_seconds() == operations_routes.DEFAULT_STREAM_MAX_SECONDS


def test_stream_loop_checks_the_deadline():
    """The stream loop compares a deadline before it polls for an event."""
    # The loop must break on time. Without this check the generator never returns.
    source = Path(operations_routes.__file__).read_text(encoding="utf-8")  # Read the shipped route source.
    assert "deadline = time.monotonic()" in source  # The generator must fix a close time.
    assert "time.monotonic() >= deadline" in source  # The loop must test that close time.
    assert "stream_timeout" in source  # The client must learn why the stream closed.


def test_start_script_pool_exceeds_the_outage_count():
    """The Gunicorn thread pool holds more threads than the outage allowed."""
    source = START_SCRIPT.read_text(encoding="utf-8")  # Read the start script that launches Gunicorn.
    match = re.search(r'PORTAL_THREADS="\$\{PORTAL_THREADS:-(\d+)\}"', source)  # Find the default thread count.
    assert match is not None, "start.sh must set a PORTAL_THREADS default"  # A missing default returns the outage.
    threads = int(match.group(1))  # Convert the captured text, so the test can compare numbers.
    assert threads > OUTAGE_THREAD_COUNT  # The pool must exceed the count that caused issue #3164.
    assert "--threads ${PORTAL_THREADS}" in source  # Gunicorn must read the configured value, not a literal.
