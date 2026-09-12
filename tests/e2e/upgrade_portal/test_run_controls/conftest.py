"""Shared site lock fixture for the run-control browser tests.

Why:
    A run-control action needs the site lock, so several tests of this package
    take it. The lock lives in the process-owned lock store of the isolated
    server, so it outlives the test that took it.

    A lock left behind refuses the next operator. `test_two_operators.py` then
    reads 400 `confirmation_required` from the lock route, and its fixture
    reports a skip. Pytest reports a skip as a pass, so 18 multi-operator tests
    stopped proving site isolation while the run still reported success.

    This fixture releases every lock it took, so no test leaks the site.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import json  # Read the lock token out of the answer body.
import logging  # Record each lock action of this fixture.
from collections.abc import Callable, Iterator  # Type the helper and the fixture result.
from typing import Any  # The Playwright page object carries no import-time type here.

import pytest  # Declare the fixture.

logger = logging.getLogger(__name__)  # Keep every lock record tied to this module.

LOCK_PATH_TEMPLATE = "/api/sites/{site_id}/lock"  # `contracts/site-lock.md` fixes this path.
TOKEN_FIELD = "lock_token"  # The field that the release call must send back.
CSRF_SELECTOR = 'meta[name="csrf-token"]'  # `layout.html` publishes the token in the page head.

# WHY: One script serves the take and the release, because both calls need the
# browser session cookie and the cross-site request token of the same page.
LOCK_SCRIPT = """async ({path, token, method, body}) => {
    const response = await fetch(path, {
        method: method,
        credentials: "same-origin",
        headers: {"X-CSRFToken": token, "Content-Type": "application/json"},
        body: body
    });
    return {ok: response.ok, status: response.status, text: await response.text()};
}"""


def _csrf_token(page: Any) -> str:
    """Return the cross-site request token of one page.

    Args:
        page: The Playwright page object, on any portal page.

    Returns:
        The token text, which is empty when the page published none.
    """
    return str(page.locator(CSRF_SELECTOR).get_attribute("content") or "")  # An empty value still refuses the write.


def _call_lock(page: Any, site_id: str, method: str, body: str) -> dict[str, Any]:
    """Send one lock call from the browser session of one page.

    Args:
        page: The Playwright page object that holds the operator session.
        site_id: The site the call names.
        method: The HTTP method, `POST` to take and `DELETE` to release.
        body: The request body text.

    Returns:
        The answer state, the status, and the body text.
    """
    path = LOCK_PATH_TEMPLATE.format(site_id=site_id)  # Build the one path the contract fixes.
    logger.info("Send a %s lock call for one site", method)  # Record the call before it starts.
    answer = page.evaluate(  # The browser sends the call, so the session cookie travels with it.
        LOCK_SCRIPT,
        {"path": path, "token": _csrf_token(page), "method": method, "body": body},
    )
    logger.debug("The %s lock call answered status %s", method, answer.get("status"))  # Report no token value.
    return dict(answer)  # The caller reads the state and the body text.


def _release(page: Any, site_id: str, token: str) -> None:
    """Release one site lock, and report a refusal instead of raising.

    Why:
        A teardown must never replace the result of the test that just ran. A
        failed release is still worth a warning, because it names the cause of
        a later skip.

    Args:
        page: The Playwright page object that took the lock.
        site_id: The site the lock covers.
        token: The token that the take call returned.
    """
    try:  # A closed page and a changed session both raise here.
        answer = _call_lock(page, site_id, "DELETE", json.dumps({TOKEN_FIELD: token}))
    except Exception as failure:  # A raise here would hide the result of the test.
        logger.warning("The site lock release did not run. Cause: %s", failure)  # Name the cause for the reader.
        return  # Leave the lock, because no other action is available now.
    if not answer.get("ok"):  # The portal refused the release, so the next test can still meet the lock.
        logger.warning("The site lock release answered status %s", answer.get("status"))  # Name the status.


@pytest.fixture(name="site_lock")
def fixture_site_lock(page: Any) -> Iterator[Callable[..., None]]:
    """Give a test one site lock, and release every lock after the test.

    Why:
        The fixture asks for `page`, so pytest builds it after the page and
        tears it down before the page closes. The release call therefore still
        reaches a live browser session.

    Args:
        page: The Playwright page object of the first operator.

    Yields:
        A function that takes the lock of one site for one page.
    """
    held: list[tuple[Any, str, str]] = []  # Hold one record for each lock this test took.

    def take(site_id: str, lock_page: Any = page) -> None:
        """Take the lock of one site and remember its token.

        Args:
            site_id: The site to lock.
            lock_page: The page that holds the operator session. The first
                operator page is the default.

        Raises:
            AssertionError: If the portal refused the lock, because every
                caller of this helper needs the site.
        """
        answer = _call_lock(lock_page, site_id, "POST", "{}")  # The store decides the race, never this test.
        assert answer["ok"], answer["text"]  # A refusal is a real fault, so it must stop the test.
        token = str(json.loads(answer["text"])[TOKEN_FIELD])  # The release call must send this value back.
        held.append((lock_page, site_id, token))  # Record the lock, so the teardown can release it.

    yield take  # The test now takes every lock it needs.
    for lock_page, site_id, token in reversed(held):  # Release in the reverse order of the take.
        _release(lock_page, site_id, token)  # The next test then finds the site free.
