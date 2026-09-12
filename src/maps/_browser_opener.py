"""Delayed browser opener for the map viewers.

Both map viewers open the system browser a short time after the local server
starts. The delay lets the server bind its port before the browser sends the
first request.

This module holds that behavior in one class. The class replaces two bare
``time.sleep`` calls that ran on a daemon thread that no caller joined. A
sleeping thread has two costs. The thread pollutes a global ``time.sleep`` spy
in the test suite, and a caller cannot shut the viewer down and know the thread
finished.

:class:`DelayedBrowserOpener` waits on a :class:`threading.Event` instead. A
stop request returns at once, and :meth:`DelayedBrowserOpener.stop` joins the
thread before it returns.
"""

from __future__ import annotations  # WHY: Lets the annotations name the class before Python finishes the class body.

import logging  # WHY: The module reports each lifecycle step, so an operator can trace a browser that never opened.
import threading  # WHY: The wait and the join both need the threading primitives.
import webbrowser  # WHY: The class opens the viewer URL in the default browser of the operator.

logger = logging.getLogger(__name__)  # WHY: A module logger groups these lines and avoids the root logger.

DEFAULT_OPEN_DELAY_S = 1.5  # WHY: The local server needs about this long to bind its port before it answers.
DEFAULT_JOIN_TIMEOUT_S = 5.0  # WHY: A bounded join stops a shutdown from blocking forever on a stuck thread.
_THREAD_NAME = "maps-browser-opener"  # WHY: A named thread makes a leaked thread easy to find in a stack dump.


class DelayedBrowserOpener:
    """Open one URL in the system browser after a delay, on a thread a caller can stop.

    The caller supplies the finished URL. The class never builds an address from
    a port, because a wrong value in an address is hard to see in a log.
    """

    def __init__(self, url: str, delay_s: float = DEFAULT_OPEN_DELAY_S) -> None:
        """Store the target URL and the delay, and prepare the stop control."""
        self._url = url  # WHY: The finished URL removes the chance to bind a wrong value into the address.
        self._delay_s = delay_s  # WHY: The caller can shorten the delay in a test to keep the run fast.
        self._stop_event = threading.Event()  # WHY: An event wait ends at once on a stop, unlike a sleep.
        self._thread: threading.Thread | None = None  # WHY: The handle lets stop join the thread it started.
        self._lock = threading.Lock()  # WHY: The lock keeps a concurrent start and stop from racing on the handle.

    @property
    def url(self) -> str:
        """Return the URL that this opener sends to the browser."""
        return self._url  # WHY: A read-only view lets a caller log the target without reaching into the class.

    def is_running(self) -> bool:
        """Report whether the opener thread is alive."""
        with self._lock:  # WHY: The read must not race with a start that replaces the handle.
            thread = self._thread  # WHY: A local copy keeps the liveness test outside the lock.
        return thread is not None and thread.is_alive()  # WHY: A finished thread counts as not running.

    def start(self) -> None:
        """Start the wait. A second call while the thread runs does nothing."""
        with self._lock:  # WHY: The guard and the assignment must happen as one step.
            if self._thread is not None and self._thread.is_alive():  # WHY: A second thread would open two browsers.
                logger.debug("The browser opener already runs for %s, so this start does nothing", self._url)
                return  # WHY: The guard makes a repeated start safe for the caller.
            self._stop_event.clear()  # WHY: A reused opener must not inherit the stop flag of the previous run.
            self._thread = threading.Thread(  # WHY: The open must not block the caller that starts the server.
                target=self._wait_then_open, name=_THREAD_NAME, daemon=True
            )
            logger.info("The browser opener starts for %s after %.1f seconds", self._url, self._delay_s)
            self._thread.start()  # WHY: The start happens under the lock, so is_running reports the truth at once.

    def stop(self, timeout_s: float = DEFAULT_JOIN_TIMEOUT_S) -> None:
        """Cancel the wait and join the thread. Log a warning if the thread outlives the join."""
        self._stop_event.set()  # WHY: The set ends the wait at once, so the join returns without the full delay.
        with self._lock:  # WHY: The read must not race with a start that replaces the handle.
            thread = self._thread  # WHY: The join must run outside the lock, or a start would block on it.
        if thread is None:  # WHY: A stop before any start is a valid call from a cleanup path.
            logger.debug("The browser opener for %s holds no thread, so this stop does nothing", self._url)
            return  # WHY: Nothing to join.
        logger.info("The browser opener stops for %s", self._url)  # WHY: Records the shutdown request.
        thread.join(timeout_s)  # WHY: The bounded join keeps a stuck thread from blocking the shutdown.
        if thread.is_alive():  # WHY: A live thread after the join means the wait did not end.
            logger.warning("The browser opener thread for %s outlived the %.1f second join", self._url, timeout_s)
            return  # WHY: The handle stays, so a later stop can try the join again.
        self._clear_finished_thread(thread)  # WHY: A cleared handle lets a later start create a fresh thread.

    def _clear_finished_thread(self, thread: threading.Thread) -> None:
        """Drop the stored handle if it still refers to the thread that just finished."""
        with self._lock:  # WHY: The compare and the clear must happen as one step.
            if self._thread is thread:  # WHY: A start between the join and this line owns a newer thread.
                self._thread = None  # WHY: The cleared handle reports the opener as not running.
        logger.debug("The browser opener thread for %s finished", self._url)  # WHY: Confirms the clean exit.

    def _wait_then_open(self) -> None:
        """Wait for the delay, then open the browser. A stop request cancels the open."""
        if self._stop_event.wait(self._delay_s):  # WHY: A true answer means a stop arrived before the delay ended.
            logger.info("A stop request cancelled the browser open for %s", self._url)
            return  # WHY: The caller shut the viewer down, so the browser must not open.
        logger.info("The browser opener opens %s", self._url)  # WHY: Records the attempt before the call.
        if not self._open_url():  # WHY: A failed open must not stop the thread from ending cleanly.
            return  # WHY: The helper already logged the failure.
        logger.debug("The browser opened %s", self._url)  # WHY: Confirms the result after the call.

    def _open_url(self) -> bool:
        """Send the URL to the default browser. Return False if the browser refused the URL."""
        try:
            webbrowser.open(self._url)  # WHY: The default browser is the one the operator expects to see.
        except (webbrowser.Error, OSError) as error:  # WHY: A headless host raises instead of opening a window.
            logger.warning("The browser refused to open %s: %s", self._url, error)
            return False  # WHY: The caller logs nothing more, because this line already named the cause.
        return True  # WHY: A true answer lets the caller log the success.
