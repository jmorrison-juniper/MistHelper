"""Browser tests for two operators that reach for one site at the same time.

Why:
    The site lock is the one guard that stops two operators from upgrading one
    site together. A unit test of the lock module proves the arithmetic of the
    record. It cannot prove that two real browsers, each with its own cookie
    jar, meet that guard. Only a browser test proves that.

Why the second operator needs a whole browser context:
    The lock identifies a holder by the pair of the work address and the browser
    identifier. Two tabs of one browser share the cookie jar, so they share both
    halves of that pair and read as one operator. A second tab therefore resumes
    the lock and never meets the refusal. `second_operator_page` in
    `conftest.py` builds a separate context for this reason, and one test below
    proves that the two contexts really do carry different cookies.

Why the tests prove that a read is always free:
    A read that waited for the lock would hide the record from the operator who
    watches another upgrade. `contracts/http-api.md:493` states that rule for
    the history, and line 107 states it for the site list. The rule is a product
    decision, so the tests state it. The second operator types no word and holds
    no lock, and every read below still answers.

Why the write refusal uses the run create:
    The contrast makes the read rule meaningful. The run create refuses a second
    operator and reaches no cloud at all, so it is the safest write to drive.

Why the module reaches no cloud:
    The server holds a stand-in cloud session with no request method, so a cloud
    call fails inside the process. No test starts a capture, starts an upgrade,
    or writes a firmware version. Every address below is a reserved `.invalid`
    address that can reach no mail host.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import pytest

# The Playwright package must exist before this module defines a browser test.
# A run without the package reports a skip and never an import error.
sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

# `contracts/http-api.md` fixes these paths.
SITE_PAGE_PATH = "/select/site"
SITE_VIEW_TEMPLATE = "/select/site/{site_id}"
HISTORY_PAGE_PATH = "/history"
SITE_API_PATH = "/api/sites"
LOCK_API_TEMPLATE = "/api/sites/{site_id}/lock"
RUN_CREATE_TEMPLATE = "/api/sites/{site_id}/runs"
HISTORY_API_TEMPLATE = "/api/sites/{site_id}/history"
RUN_HISTORY_API_TEMPLATE = "/api/sites/{site_id}/runs/history"

# `contracts/ui-testids.md` lines 68, 69, and 212 fix these three names.
SITE_ROW_PREFIX = "site-row-"
LOCK_STATE_TEMPLATE = "site-lock-state-{site_id}"
CSRF_META_ID = "csrf-meta"

CSRF_HEADER = "X-CSRFToken"  # `contracts/README.md` fixes this header name for every write.
JSON_TYPE = "application/json"

# `conftest.py` registers both pairs, and the first pair takes the lock.
HOLDER_EMAIL = "e2e.operator@example.invalid"
BROWSER_COOKIE = "browser_id"

# `contracts/README.md:33` fixes the error envelope.
ERROR_FIELD = "error"
CODE_FIELD = "code"
DETAILS_FIELD = "details"
ACTOR_FIELD = "actor_email"
SITE_LOCKED_CODE = "site_locked"

# `contracts/http-api.md:129` fixes the grant body.
TOKEN_FIELD = "lock_token"
STATE_FIELD = "state"
RESUME_STATE = "resume"

OK_STATUS = 200
CREATED_STATUS = 201
BAD_REQUEST_STATUS = 400
UNAUTHORIZED_STATUS = 401
NOT_FOUND_STATUS = 404
CONFLICT_STATUS = 409
STORE_DOWN_STATUS = 503  # `lock_store_unreachable`, which a workstation with no Redis answers.

GATE_TIMEOUT_MS = 5000  # The pages are server rendered, so every control is present at once.

# WHY: The server fixture states its own fault and its own skip, so this module
# must not translate either one. A browser fixture is different: a workstation
# without a browser binary describes the workstation and never the page.
SERVER_FIXTURE = "capture_portal_server"
FIRST_BROWSER_FIXTURE = "page"
SECOND_BROWSER_FIXTURE = "second_operator_page"


def _browser_page(request: pytest.FixtureRequest, name: str) -> Any:
    """Build one browser page, and report a missing browser binary as a skip.

    Why:
        Playwright needs a browser binary that no source tree carries. A plain
        request would report an error, which reads in a report as a broken test.
        A missing binary is the one environment fault this module still hides,
        because it stops every browser test for a reason outside the portal.
        The server fixture states its own fault and its own skip, so this
        function never wraps it.

    Args:
        request: The pytest request object of the calling fixture.
        name: The browser fixture to build.

    Returns:
        The Playwright page object.
    """
    try:  # A missing browser binary describes the workstation, never the page.
        return request.getfixturevalue(name)
    except Exception as failure:  # A skip states the real cause, so nothing hides.
        pytest.skip(f"Playwright could not open a browser, so no browser test can run. Cause: {failure}")


@pytest.fixture
def first_page(request: pytest.FixtureRequest) -> Any:
    """Return the page of the operator who takes the lock.

    Args:
        request: The pytest request object.

    Returns:
        The Playwright page object.
    """
    request.getfixturevalue(SERVER_FIXTURE)  # A fault here is a fault of the portal, so it must not become a skip.
    return _browser_page(request, FIRST_BROWSER_FIXTURE)


@pytest.fixture
def second_page(request: pytest.FixtureRequest) -> Any:
    """Return the page of the operator who meets the refusal.

    Args:
        request: The pytest request object.

    Returns:
        The Playwright page object of the second browser context.
    """
    request.getfixturevalue(SERVER_FIXTURE)  # A fault here is a fault of the portal, so it must not become a skip.
    return _browser_page(request, SECOND_BROWSER_FIXTURE)


def _page_status(page: Any, path: str) -> int:
    """Open one path and return the status code of the answer.

    Args:
        page: The Playwright page object.
        path: The path to open, relative to the portal address.

    Returns:
        The status code that the portal answered.
    """
    answer = page.goto(path, wait_until="domcontentloaded")
    if answer is None:  # A page with no answer gives the test nothing to read.
        pytest.skip(f"The browser returned no response for {path}.")
    status: int = answer.status
    return status


def _require_built_route(status: int, path: str) -> None:
    """Fail when the portal answers a status that the contract does not fix.

    Args:
        status: The status code the portal answered.
        path: The path the test opened, named in every message.

    Raises:
        AssertionError: If the portal answered a status that the contract does
            not fix for a page.
    """
    if status == UNAUTHORIZED_STATUS:  # `identity.require_session` refused the request.
        raise AssertionError(f"{path} answered 401. The portal this run started holds no sign-in seam.")
    if status == NOT_FOUND_STATUS:  # The blueprint that owns this path is not registered.
        raise AssertionError(f"{path} answered 404. The blueprint that owns this path is not registered.")
    assert status == OK_STATUS, f"{path} answered {status}. `contracts/http-api.md` fixes 200 for this page."


def _marker_keys(page: Any, prefix: str) -> list[str]:
    """Return the tail of every identifier on the page that starts with a prefix.

    Args:
        page: The Playwright page object.
        prefix: The identifier prefix, such as `site-row-`.

    Returns:
        The tail of each matching identifier, in page order.
    """
    found = page.locator(f'[data-testid^="{prefix}"]')  # A prefix match still selects by `data-testid`.
    markers = found.evaluate_all("nodes => nodes.map(node => node.getAttribute('data-testid'))")
    return [str(marker)[len(prefix) :] for marker in markers if marker]


def _open_site_picker(page: Any) -> str:
    """Open the site picker on one page and return the first site key.

    Why:
        The lock path names the site, and the picker is the one documented page
        that carries a real site key. The visit also gives the page a token, so
        a write can follow.

    Args:
        page: The Playwright page object.

    Returns:
        The site key of the first row.
    """
    _require_built_route(_page_status(page, SITE_PAGE_PATH), SITE_PAGE_PATH)
    keys = _marker_keys(page, SITE_ROW_PREFIX)
    if not keys:  # The portal reached no site, so no lock path can be built.
        pytest.skip("The site picker shows no site row, so no site key exists to lock.")
    return keys[0]


def _csrf_token(page: Any) -> str:
    """Read the token that the page carries for a write.

    Args:
        page: The Playwright page object, already on a portal page.

    Returns:
        The token text, which is empty when the page carries none.
    """
    return str(page.get_by_test_id(CSRF_META_ID).get_attribute("content") or "")


def _write(page: Any, method: str, path: str, body: dict[str, Any]) -> Any:
    """Send one write to the portal with the token that the page carries.

    Args:
        page: The Playwright page object, already on a portal page.
        method: The word `post` or the word `delete`.
        path: The endpoint path, relative to the portal address.
        body: The request body.

    Returns:
        The Playwright response object.

    Raises:
        AssertionError: If the call never reached the portal. The server fixture
            starts the portal, so a call that cannot complete names a fault of
            that portal and never a gap in the workstation.
    """
    headers = {CSRF_HEADER: _csrf_token(page), "Content-Type": JSON_TYPE}
    try:  # The fixture started this portal, so a call that fails names a fault of it.
        return page.request.fetch(path, method=method, headers=headers, data=json.dumps(body))
    except Exception as failure:  # The portal died, or it never bound the port.
        raise AssertionError(f"The {method} call to {path} did not complete. Cause: {failure}") from failure


def _error_code(answer: Any) -> str:
    """Return the error code of a refusal body.

    Args:
        answer: The Playwright response object of a refused call.

    Returns:
        The code text, which is empty when the body holds no envelope.
    """
    body = json.loads(answer.text())
    return str(body.get(ERROR_FIELD, {}).get(CODE_FIELD, ""))


@pytest.fixture
def held_site(first_page: Any) -> Iterator[str]:
    """Let the first operator take the lock, and release it after the test.

    Why:
        Every test of this module needs a site that one operator already holds.
        A lock left behind would refuse the next test and the next run, so the
        release runs even when the test fails.

    Args:
        first_page: The page of the operator who takes the lock.

    Yields:
        The site key that the first operator now holds.

    Raises:
        AssertionError: If the lock endpoint answers 401 or 404. Both name a
            fault of the portal, so neither may report a skip.
    """
    site = _open_site_picker(first_page)
    path = LOCK_API_TEMPLATE.format(site_id=site)
    answer = _write(first_page, "post", path, {})
    if answer.status in (UNAUTHORIZED_STATUS, NOT_FOUND_STATUS):  # The portal itself is broken.
        raise AssertionError(f"{path} answered {answer.status}, so the portal serves no lock route.")
    if answer.status != OK_STATUS:  # A workstation with no lock store answers 503 here.
        pytest.skip(f"{path} answered {answer.status}, so the first operator holds no lock.")
    token = str(json.loads(answer.text())[TOKEN_FIELD])
    yield site
    _write(first_page, "delete", path, {TOKEN_FIELD: token})  # The next test then finds the site free.


class TestTheSecondOperatorIsRefused:
    """A second operator cannot take a site that another operator holds."""

    def test_the_two_operators_carry_different_browser_cookies(self, first_page: Any, second_page: Any) -> None:
        """The two contexts hold two different browser identifiers.

        Why:
            The lock reads the pair of the address and the browser identifier.
            A second context that shared the cookie would read as the same
            operator, and every refusal test below would then prove nothing.
            This test guards the whole class.

        Args:
            first_page: The page of the first operator.
            second_page: The page of the second operator.
        """
        first = {item["name"]: item["value"] for item in first_page.context.cookies()}
        second = {item["name"]: item["value"] for item in second_page.context.cookies()}
        assert first[BROWSER_COOKIE] != second[BROWSER_COOKIE], "Both contexts carry one browser identifier."

    def test_the_second_operator_reads_the_refusal(self, second_page: Any, held_site: str) -> None:
        """The lock call of the second operator answers `site_locked`.

        Why:
            `contracts/http-api.md:132` fixes this code and this status. Two
            operators that both held one site could write two firmware plans to
            one set of devices.

        Args:
            second_page: The page of the second operator.
            held_site: The site that the first operator holds.
        """
        _open_site_picker(second_page)  # The second page needs its own token before a write.
        answer = _write(second_page, "post", LOCK_API_TEMPLATE.format(site_id=held_site), {})
        assert answer.status == CONFLICT_STATUS, f"The second lock call answered {answer.status}, not 409."
        assert _error_code(answer) == SITE_LOCKED_CODE, "The refusal carries another code."

    def test_the_refusal_names_the_holder(self, second_page: Any, held_site: str) -> None:
        """The refusal tells the second operator who holds the site.

        Why:
            `contracts/http-api.md:143` states that this endpoint is the only
            one that names the holder. An operator who reads no name cannot ask
            the holder to finish, and would only wait.

        Args:
            second_page: The page of the second operator.
            held_site: The site that the first operator holds.
        """
        _open_site_picker(second_page)
        answer = _write(second_page, "post", LOCK_API_TEMPLATE.format(site_id=held_site), {})
        if answer.status in (UNAUTHORIZED_STATUS, NOT_FOUND_STATUS):  # The portal itself is broken.
            raise AssertionError(f"The second lock call answered {answer.status}, so the portal is not serving it.")
        if answer.status != CONFLICT_STATUS:  # The refusal test above states this fault already.
            pytest.skip(f"The second lock call answered {answer.status}, so it carries no refusal body.")
        details = json.loads(answer.text())[ERROR_FIELD].get(DETAILS_FIELD) or {}
        assert details.get(ACTOR_FIELD), "The refusal names no holder."

    def test_the_refusal_carries_no_lock_token(self, second_page: Any, held_site: str) -> None:
        """The refusal hands the second operator no token of the held lock.

        Why:
            A token in a refusal would let the second operator release or extend
            a lock they never took. `contracts/http-api.md:168` keeps the record
            in the signed session of the holder for the same reason.

        Args:
            second_page: The page of the second operator.
            held_site: The site that the first operator holds.
        """
        _open_site_picker(second_page)
        answer = _write(second_page, "post", LOCK_API_TEMPLATE.format(site_id=held_site), {})
        if answer.status in (UNAUTHORIZED_STATUS, NOT_FOUND_STATUS):  # The portal itself is broken.
            raise AssertionError(f"The second lock call answered {answer.status}, so the portal is not serving it.")
        if answer.status != CONFLICT_STATUS:  # The refusal test above states this fault already.
            pytest.skip(f"The second lock call answered {answer.status}, so it carries no refusal body.")
        assert TOKEN_FIELD not in answer.text(), "The refusal body holds a lock token."

    def test_the_site_row_shows_the_lock_to_the_second_operator(self, second_page: Any, held_site: str) -> None:
        """The site picker of the second operator shows the site as locked.

        Why:
            An operator must read the refusal in the page, not in a network log.
            The lock state cell carries the state and the holder, and WCAG 1.4.1
            refuses color as the only signal, so the cell names both in words.

        Args:
            second_page: The page of the second operator.
            held_site: The site that the first operator holds.
        """
        _require_built_route(_page_status(second_page, SITE_PAGE_PATH), SITE_PAGE_PATH)
        cell = second_page.get_by_test_id(LOCK_STATE_TEMPLATE.format(site_id=held_site))
        sync_api.expect(cell).to_be_visible(timeout=GATE_TIMEOUT_MS)
        assert HOLDER_EMAIL in cell.inner_text(), f"The lock cell reads: {cell.inner_text()!r}"

    def test_the_second_operator_cannot_create_a_run(self, second_page: Any, held_site: str) -> None:
        """The second operator cannot start work on the held site.

        Why:
            `contracts/http-api.md:254` refuses this write with the same code.
            The refusal of the lock alone would mean little if the second
            operator could still create a run and upgrade the same devices.

        Args:
            second_page: The page of the second operator.
            held_site: The site that the first operator holds.
        """
        _open_site_picker(second_page)
        answer = _write(second_page, "post", RUN_CREATE_TEMPLATE.format(site_id=held_site), {})
        if answer.status == NOT_FOUND_STATUS:  # The blueprint that owns this path is not registered.
            raise AssertionError("The run create answered 404, so the portal serves no run route.")
        if answer.status in (BAD_REQUEST_STATUS, STORE_DOWN_STATUS):
            pytest.skip(f"The run create answered {answer.status}, which names a cause outside the lock.")
        assert answer.status == CONFLICT_STATUS, f"The run create answered {answer.status}, not 409."
        assert _error_code(answer) == SITE_LOCKED_CODE, "The refusal carries another code."


class TestOneBrowserHoldsOneLock:
    """Two tabs of one browser share the cookie, so they share the lock."""

    def test_a_second_tab_resumes_the_same_lock(self, first_page: Any, held_site: str) -> None:
        """A second tab of the holder reads the lock back, and takes no new one.

        Why:
            `contracts/http-api.md:135` names this state `resume`, and states
            that it means the same operator and the same browser returned to a
            lock they already hold. An operator who opened a second tab and read
            a refusal would think another person had taken their site.

        Args:
            first_page: The page of the operator who holds the lock.
            held_site: The site that this operator holds.
        """
        tab = first_page.context.new_page()  # One context, so one cookie jar and one lock identity.
        try:
            _open_site_picker(tab)
            answer = _write(tab, "post", LOCK_API_TEMPLATE.format(site_id=held_site), {})
            assert answer.status == OK_STATUS, f"The second tab answered {answer.status}, not 200."
            assert json.loads(answer.text())[STATE_FIELD] == RESUME_STATE, "The second tab took a new lock."
        finally:
            tab.close()  # A tab left open would hold a browser target for the whole run.


class TestReadingIsAlwaysFree:
    """A read needs no lock and no typed word, for either operator."""

    @pytest.mark.parametrize("template", (HISTORY_API_TEMPLATE, RUN_HISTORY_API_TEMPLATE))
    def test_the_second_operator_reads_a_history_endpoint(
        self, second_page: Any, held_site: str, template: str
    ) -> None:
        """Both history endpoints answer the operator who holds no lock.

        Why:
            `contracts/http-api.md:493` states that no history route reads the
            lock, because a read that waited for a lock would hide the record
            from the operator who watches another upgrade.

        Args:
            second_page: The page of the second operator.
            held_site: The site that the first operator holds.
            template: The endpoint path template that this run reads.
        """
        path = template.format(site_id=held_site)
        answer = second_page.request.get(path)
        if answer.status == NOT_FOUND_STATUS:  # The route is not registered yet.
            raise AssertionError(f"{path} answered 404. The blueprint that owns this path is not registered.")
        assert answer.status == OK_STATUS, f"{path} answered {answer.status} while another operator held the site."

    def test_the_second_operator_reads_the_site_list(self, second_page: Any, held_site: str) -> None:
        """The site list answers the operator who holds no lock.

        Why:
            `contracts/http-api.md:107` states that reading this endpoint never
            needs the lock. The row that names the holder lives in this answer,
            so a lock on the read would hide the very fact the operator needs.

        Args:
            second_page: The page of the second operator.
            held_site: The site that the first operator holds.
        """
        del held_site  # Requested so the first operator holds the lock during this read.
        answer = second_page.request.get(SITE_API_PATH)
        if answer.status == NOT_FOUND_STATUS:  # The route is not registered yet.
            raise AssertionError(f"{SITE_API_PATH} answered 404. The blueprint that owns this path is not registered.")
        assert answer.status == OK_STATUS, f"{SITE_API_PATH} answered {answer.status} while the site was held."

    @pytest.mark.parametrize("path", (HISTORY_PAGE_PATH, SITE_PAGE_PATH))
    def test_the_second_operator_opens_a_read_page(self, second_page: Any, held_site: str, path: str) -> None:
        """The history page and the site picker open with no lock and no word.

        Why:
            The read rule is a product decision, so a test states it. The second
            operator types nothing, holds nothing, and still reads the state and
            the stored data of a site that another operator holds.

        Args:
            second_page: The page of the second operator.
            held_site: The site that the first operator holds.
            path: The page that this run opens.
        """
        del held_site  # Requested so the first operator holds the lock during this read.
        _require_built_route(_page_status(second_page, path), path)

    def test_the_second_operator_opens_the_site_view(self, second_page: Any, held_site: str) -> None:
        """The inventory page of the held site opens for the second operator.

        Why:
            `select/sites.html` states that a read view needs no lock, so the
            open link works on a locked site too. An operator who must wait for
            a lock to read an inventory cannot plan their own work.

        Args:
            second_page: The page of the second operator.
            held_site: The site that the first operator holds.
        """
        path = SITE_VIEW_TEMPLATE.format(site_id=held_site)
        _require_built_route(_page_status(second_page, path), path)
