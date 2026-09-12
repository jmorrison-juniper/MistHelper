"""Unit tests for the delayed browser opener and its two map-viewer callers.

The tests cover issue #1845 and issue #1854.

Issue #1845 asks for a thread that a caller can stop and join. Issue #1854
records a signature mistake that raised ``TypeError`` inside the viewer thread
on every Dash launch.
"""

from __future__ import annotations

import threading
import webbrowser

import pytest

from src.maps._browser_opener import DelayedBrowserOpener

_NO_DELAY_S = 0.0  # WHY: A zero delay keeps every test fast without a sleep.
_LONG_DELAY_S = 30.0  # WHY: A long delay proves that stop ends the wait early, not that the wait expired.
_JOIN_TIMEOUT_S = 5.0  # WHY: A bounded wait fails the test instead of hanging the suite.


class _ThreadExceptionRecorder:
    """Record every exception that a thread raises, because a thread never reraises into the test."""

    def __init__(self) -> None:
        self.failures: list[BaseException] = []  # WHY: The list holds each captured thread failure.

    def __call__(self, args) -> None:
        """Store the raised exception so a test can assert the thread stayed clean."""
        self.failures.append(args.exc_value)  # WHY: The value carries the type and the message.


@pytest.fixture
def thread_failures(monkeypatch: pytest.MonkeyPatch) -> _ThreadExceptionRecorder:
    """Capture thread exceptions for the duration of one test."""
    recorder = _ThreadExceptionRecorder()  # WHY: One recorder per test keeps the assertions independent.
    monkeypatch.setattr(threading, "excepthook", recorder)  # WHY: The hook is the only route to a thread failure.
    return recorder


@pytest.fixture
def opened_urls(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Replace the real browser call so no test opens a window."""
    urls: list[str] = []  # WHY: The list records each URL the code sends to the browser.
    monkeypatch.setattr(webbrowser, "open", urls.append)  # WHY: A recording stub keeps the test headless.
    return urls


def _wait_for(predicate, timeout_s: float = _JOIN_TIMEOUT_S) -> bool:
    """Poll a predicate until it answers True or the timeout expires."""
    deadline = threading.Event()  # WHY: The event supplies a bounded wait without a sleep call.
    for _ in range(int(timeout_s * 100)):  # WHY: A capped loop cannot hang the suite.
        if predicate():  # WHY: The predicate reports the state the test waits for.
            return True  # WHY: The condition arrived inside the timeout.
        deadline.wait(0.01)  # WHY: A short wait yields the processor to the worker thread.
    return False  # WHY: The timeout expired, so the caller fails the test.


def test_start_opens_the_url(opened_urls: list[str], thread_failures: _ThreadExceptionRecorder) -> None:
    """A started opener sends the exact URL to the browser."""
    opener = DelayedBrowserOpener("http://127.0.0.1:8050", delay_s=_NO_DELAY_S)
    opener.start()
    assert _wait_for(lambda: bool(opened_urls))  # WHY: The wait removes the race between the open and the stop.
    opener.stop()

    assert opened_urls == ["http://127.0.0.1:8050"]
    assert thread_failures.failures == []


def test_stop_joins_the_thread_before_it_returns(opened_urls: list[str]) -> None:
    """The thread has finished by the time stop returns. This is the issue #1845 contract."""
    opener = DelayedBrowserOpener("http://127.0.0.1:8050", delay_s=_LONG_DELAY_S)
    opener.start()
    assert opener.is_running()

    opener.stop()

    assert not opener.is_running()
    assert opened_urls == []


def test_stop_cancels_the_pending_open(opened_urls: list[str]) -> None:
    """A stop during the wait cancels the browser open."""
    opener = DelayedBrowserOpener("http://127.0.0.1:8050", delay_s=_LONG_DELAY_S)
    opener.start()
    opener.stop()

    assert opened_urls == []


def test_second_start_does_not_add_a_thread(opened_urls: list[str]) -> None:
    """A second start while the thread runs does nothing, so the browser opens one time."""
    opener = DelayedBrowserOpener("http://127.0.0.1:8050", delay_s=_LONG_DELAY_S)
    opener.start()
    first_thread = opener._thread
    opener.start()

    assert opener._thread is first_thread
    opener.stop()


def test_stop_without_start_does_nothing() -> None:
    """A stop on an unused opener returns without an error."""
    opener = DelayedBrowserOpener("http://127.0.0.1:8050", delay_s=_NO_DELAY_S)
    opener.stop()

    assert not opener.is_running()


def test_stop_warns_when_the_thread_outlives_the_join(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A thread that outlives the join produces a WARNING, and the shutdown still returns."""
    release = threading.Event()  # WHY: The event holds the worker inside the browser call.
    monkeypatch.setattr(webbrowser, "open", lambda _url: release.wait(_JOIN_TIMEOUT_S))
    opener = DelayedBrowserOpener("http://127.0.0.1:8050", delay_s=_NO_DELAY_S)
    opener.start()
    assert _wait_for(opener.is_running)

    with caplog.at_level("WARNING"):
        opener.stop(timeout_s=0.05)

    assert "outlived" in caplog.text
    release.set()  # WHY: The release lets the worker finish, so the suite leaks no thread.
    assert _wait_for(lambda: not opener.is_running())


def test_a_refused_browser_open_logs_a_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, thread_failures: _ThreadExceptionRecorder
) -> None:
    """A headless host raises from the browser call. The thread logs the cause and ends cleanly."""

    def _refuse(_url: str) -> None:
        """Raise the error that a host without a browser raises."""
        raise webbrowser.Error("no browser")

    monkeypatch.setattr(webbrowser, "open", _refuse)
    opener = DelayedBrowserOpener("http://127.0.0.1:8050", delay_s=_NO_DELAY_S)

    with caplog.at_level("WARNING"):
        opener.start()
        assert _wait_for(lambda: "refused to open" in caplog.text)  # WHY: The wait removes the start-stop race.
        opener.stop()

    assert "refused to open" in caplog.text
    assert thread_failures.failures == []


def test_plotly_viewer_schedules_and_stops_the_open(
    monkeypatch: pytest.MonkeyPatch, opened_urls: list[str], thread_failures: _ThreadExceptionRecorder
) -> None:
    """The Dash viewer opens the loopback URL and joins the thread.

    This test is the regression guard for issue #1854. The previous code started
    a bound method whose signature took no argument and passed one argument to
    it. The thread then raised ``TypeError`` and opened no browser.
    """
    from src.maps import _plotly_viewer

    monkeypatch.setattr(_plotly_viewer, "is_running_in_container", lambda: False)
    monkeypatch.setattr(
        _plotly_viewer,
        "DelayedBrowserOpener",
        lambda url, delay_s=_NO_DELAY_S: DelayedBrowserOpener(url, delay_s=_NO_DELAY_S),
    )
    viewer = _plotly_viewer._PlotlyViewer(None)

    viewer._schedule_browser_open(8050)
    assert _wait_for(lambda: bool(opened_urls))  # WHY: The wait removes the race between the open and the stop.
    viewer.stop()

    assert opened_urls == ["http://127.0.0.1:8050"]
    assert thread_failures.failures == []


def test_plotly_viewer_skips_the_open_in_a_container(monkeypatch: pytest.MonkeyPatch, opened_urls: list[str]) -> None:
    """A container run schedules no browser open, because the host owns the browser."""
    from src.maps import _plotly_viewer

    monkeypatch.setattr(_plotly_viewer, "is_running_in_container", lambda: True)
    viewer = _plotly_viewer._PlotlyViewer(None)

    viewer._schedule_browser_open(8050)
    viewer.stop()

    assert viewer._browser_opener is None
    assert opened_urls == []


def test_flask_viewer_returns_a_stoppable_opener(monkeypatch: pytest.MonkeyPatch, opened_urls: list[str]) -> None:
    """The Flask viewer hands the opener back, so the caller can join the thread."""
    pytest.importorskip("mistapi")  # WHY: The Flask viewer imports the Mist SDK at module scope.
    from src.maps import _flask_viewer

    monkeypatch.setattr(_flask_viewer, "is_running_in_container", lambda: False)
    monkeypatch.setattr(_flask_viewer, "_BROWSER_OPEN_DELAY_S", _NO_DELAY_S)

    opener = _flask_viewer._maybe_open_browser(8051)

    assert opener is not None
    assert opener.url == "http://127.0.0.1:8051"
    opener.stop()
    assert not opener.is_running()


def test_flask_viewer_skips_the_open_in_a_container(monkeypatch: pytest.MonkeyPatch) -> None:
    """A container run returns no opener, so the caller has no thread to join."""
    pytest.importorskip("mistapi")  # WHY: The Flask viewer imports the Mist SDK at module scope.
    from src.maps import _flask_viewer

    monkeypatch.setattr(_flask_viewer, "is_running_in_container", lambda: True)

    assert _flask_viewer._maybe_open_browser(8051) is None
