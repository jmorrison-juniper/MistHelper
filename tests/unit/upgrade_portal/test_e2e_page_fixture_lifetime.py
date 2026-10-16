"""Lifetime contract for the session page fixture of the upgrade portal browser tests.

Why:
    Issue #4247 records a teardown that waited in `page.close()` for a page
    target that Chromium never detached. The function-scoped `context` fixture
    of pytest-playwright owns each page. It stops the trace, then disposes the
    browser context, and that path waits for no page detach event. These tests
    use stand-in objects, so they open no browser, bind no port, and make no
    Mist request.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

import pytest

from tests.e2e.upgrade_portal import conftest as portal


class HealthyResponse:
    """Stand in for the `/healthz` answer of the isolated portal."""

    ok = True  # The isolation check reads this flag before the owner check.
    headers: dict[str, str] = {}  # The test replaces the owner check, so no header is necessary.


class StandInPage:
    """Record the calls that the fixture makes on one browser page."""

    def __init__(self) -> None:
        """Start with no visited path and no close request."""
        self.visited: list[str] = []  # Each path that the fixture opens.
        self.close_calls = 0  # A close here would wait for a page detach event without a limit.

    def goto(self, path: str) -> HealthyResponse:
        """Record the path and return a healthy answer."""
        self.visited.append(path)  # Prove the isolation check still runs.
        return HealthyResponse()  # The fixture requires an ok response.

    def screenshot(self, *args: Any, **kwargs: Any) -> bytes:
        """Return empty image bytes, because the retry wrapper needs a method."""
        del args, kwargs  # The lifetime contract takes no screenshot.
        return b""  # A stand-in image keeps the wrapper callable.

    def close(self) -> None:
        """Count a close request that only the context owner may make."""
        self.close_calls += 1  # The contract reads this count after teardown.


class StandInContext:
    """Record the cookies and the page that the fixture builds."""

    def __init__(self) -> None:
        """Hold one page for the fixture to open."""
        self.page = StandInPage()  # The single page that the fixture yields.
        self.cookies: list[dict[str, str]] = []  # The session cookies that the fixture installs.

    def add_cookies(self, cookies: list[dict[str, str]]) -> None:
        """Record the session cookies."""
        self.cookies.extend(cookies)  # Prove the session setup still runs.

    def new_page(self) -> StandInPage:
        """Return the one stand-in page."""
        return self.page  # The fixture opens exactly one page.


class StandInBrowser:
    """Build one stand-in context, as `browser.new_context` does."""

    def __init__(self) -> None:
        """Hold the one context that the fixture opens."""
        self.context = StandInContext()  # The fixture owns and closes this context.
        self.context_close_calls = 0  # The browser-owned fixtures must still close their context.

    def new_context(self, **options: Any) -> StandInContext:
        """Return the one stand-in context and count its close."""
        del options  # The base address does not matter to a stand-in.
        self.context.close = self._count_close  # type: ignore[attr-defined]  # Record the context close.
        return self.context  # The fixture opens exactly one context.

    def _count_close(self) -> None:
        """Count one context close."""
        self.context_close_calls += 1  # The contract reads this count after teardown.


CONTEXT_FIXTURES = (
    "page",
    "controls_operator_page",
    "empty_site_operator_page",
    "short_read_operator_page",
    "lost_page_operator_page",
    "later_check_operator_page",
)  # Each fixture takes the function-scoped `context` of pytest-playwright.
BROWSER_FIXTURES = ("second_operator_page", "signed_out_page")  # Each fixture builds and closes its own context.
COOKIE_HELPERS = (
    "portal_session_cookies",
    "second_operator_cookies",
    "firmware_operator_cookies",
    "controls_operator_cookies",
)  # The fixed-operator helpers that the fixtures read.
ADDRESS = "http://127.0.0.1:9606"  # An ephemeral-range address that no test binds.


def _fixture(name: str) -> Callable[..., Iterator[Any]]:
    """Return the undecorated generator of one fixture of the browser tests."""
    return getattr(portal, name)._get_wrapped_function()  # pytest keeps the generator behind the fixture object.


def _isolate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the session key and the owner check, so no live value enters a test."""
    for helper in COOKIE_HELPERS:  # Each fixture reads one of these helpers.
        monkeypatch.setattr(portal, helper, lambda: [{"name": "session"}])  # No real session key.
    monkeypatch.setattr(portal, "operator_session_cookies", lambda *_args: [{"name": "session"}])  # No real key.
    monkeypatch.setattr(portal.OWNER_CHECK, "require", lambda _headers: None)  # No live portal header.


def _drive(generator: Iterator[Any]) -> Any:
    """Run one fixture generator through setup and teardown, and return the yielded page."""
    yielded = next(generator)  # Setup ends at the yield.
    with pytest.raises(StopIteration):  # Teardown must finish in one step.
        next(generator)
    return yielded


@pytest.mark.parametrize("name", CONTEXT_FIXTURES)
def test_context_fixture_leaves_page_close_to_the_context_owner(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    """Teardown does not close the page itself, so no page detach wait can block it."""
    _isolate(monkeypatch)  # Keep every session value a stand-in.
    context = StandInContext()  # A fresh context for this run.
    yielded = _drive(_fixture(name)(context, ADDRESS))  # Run setup and teardown with no browser.
    assert context.page.close_calls == 0, f"{name} closed the page. The context finalizer owns that close."
    assert yielded is context.page


def test_firmware_fixture_ends_operations_and_leaves_page_close_to_the_context_owner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The firmware fixture still ends each live operation, and it does not close the page."""
    _isolate(monkeypatch)  # Keep every session value a stand-in.
    released: list[Any] = []  # The pages that the release step reads.
    monkeypatch.setattr(portal.OrgOperationRelease, "end_for", lambda page, _ledger: released.append(page))
    context = StandInContext()  # A fresh context for this run.
    _drive(_fixture("firmware_operator_page")(context, ADDRESS, portal.OrgOperationLedger()))
    assert released == [context.page]
    assert context.page.close_calls == 0


@pytest.mark.parametrize("name", BROWSER_FIXTURES)
def test_browser_fixture_closes_its_context_and_not_the_page(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    """A fixture that builds a context closes that context once, and it does not close the page."""
    _isolate(monkeypatch)  # Keep every session value a stand-in.
    browser = StandInBrowser()  # A fresh browser for this run.
    _drive(_fixture(name)(browser, ADDRESS))  # Run setup and teardown with no browser.
    assert browser.context.page.close_calls == 0, f"{name} closed the page before its context."
    assert browser.context_close_calls == 1


def test_page_fixture_keeps_the_session_and_isolation_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    """The repair keeps the cookie setup and the isolation check before the test body."""
    _isolate(monkeypatch)  # Keep every session value a stand-in.
    context = StandInContext()  # A fresh context for this run.
    _drive(_fixture("page")(context, ADDRESS))  # Run setup and teardown with no browser.
    assert context.cookies == [{"name": "session"}]
    assert context.page.visited == ["/healthz"]


def test_page_fixture_rejects_an_unhealthy_portal(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed isolation answer still stops the fixture before the test body."""
    _isolate(monkeypatch)  # Keep every session value a stand-in.
    monkeypatch.setattr(HealthyResponse, "ok", False)  # Simulate a wrong or failed server.
    context = StandInContext()  # A fresh context for this run.
    generator = _fixture("page")(context, ADDRESS)  # Build the fixture with no browser.
    with pytest.raises(AssertionError):  # The isolation assertion must still fail closed.
        next(generator)
    assert context.page.close_calls == 0
