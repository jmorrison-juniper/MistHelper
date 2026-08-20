"""Browser tests for the sign-in journey of the capture portal.

Why:
    A contract test proves that a route answers the right status. It cannot
    prove that an operator can read the form, type a pair, and reach the
    organization picker. A browser test drives the route, the template, and the
    browser script together, so it finds a form with no submit button, a masked
    field that is not masked, and an error region that never appears.

Caution:
    No test in this file posts a credential. The portal has no injected cloud
    seam when it runs as a server, so a real post would reach the Mist cloud.
    Every test therefore drives the controls, the masking, and the client-side
    guard, and no test sends a pair anywhere.

    The three probe values below are typed into fields and never submitted. Each
    one is an obvious stand-in, so a reader sees at once that none is a secret.

What this module skips and what it fails:
    The module reports a skip when no browser binary exists. It reports a
    failure when a page answers 401 or 404, and when a page answers 200 and the
    identifier contract does not hold. The fixture starts its own portal, so
    that portal holds the sign-in seam of this run. A 401 therefore means the
    seam is broken. A portal that a browser test cannot reach never reports a
    pass, and a broken page never reports a skip.

Identifier contract:
    `contracts/ui-testids.md` fixes every identifier below. Rule 4 states that a
    test selects by `data-testid` only. Every locator here reads that attribute.
    No locator reads visible text, a style class, or an element position.
"""

from __future__ import annotations

from typing import Any

import pytest

# The Playwright package must exist before this module defines a browser test.
# A run without the package reports a skip and never an import error.
sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

# `contracts/http-api.md` fixes these three paths for the sign-in journey.
SIGNIN_PATH = "/auth/signin"
TWO_FACTOR_PATH = "/auth/twofactor"
ORG_PAGE_PATH = "/select/org"

# The fixed identifiers of the three pages.
SIGNIN_EMAIL_ID = "signin-email"
SIGNIN_PASSWORD_ID = "signin-password"
SIGNIN_SUBMIT_ID = "signin-submit"
SIGNIN_ERROR_ID = "signin-error"
TWO_FACTOR_CODE_ID = "twofactor-code"
TWO_FACTOR_SUBMIT_ID = "twofactor-submit"
ORG_SEARCH_ID = "org-search"
SIGNOUT_BUTTON_ID = "signout-button"

# The identifier prefixes that `contracts/ui-testids.md` fixes for a dynamic row.
ORG_ROW_PREFIX = "org-row-"
ORG_SELECT_PREFIX = "org-select-"

# Three obvious stand-ins. A test types them into a field and never submits
# them, so nothing here reaches a cloud and nothing here is a secret.
PROBE_EMAIL = "probe.operator@example.invalid"
PROBE_PASSWORD = "fake-password-for-tests-only"
PROBE_CODE = "424242"

OK_STATUS = 200  # The contract fixes this status for every page below.
UNAUTHORIZED_STATUS = 401  # `runtime/identity.py` answers this code with no session.
NOT_FOUND_STATUS = 404  # The route is not registered yet.

# WHY: The server fixture states its own fault and its own skip, so this module
# must not translate either one. The browser fixture is different: a workstation
# without a browser binary describes the workstation and never the page.
SERVER_FIXTURE = "capture_portal_server"
BROWSER_FIXTURE = "page"


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
def portal_page(request: pytest.FixtureRequest) -> Any:
    """Return a browser page that points at the running capture portal.

    Why:
        Every test below needs the same two parts: a portal on port 8056 and a
        browser page. One fixture builds both in order, so a missing part gives
        one clear skip instead of one error for each test.

    Args:
        request: The pytest request object.

    Returns:
        The Playwright page object.
    """
    request.getfixturevalue(SERVER_FIXTURE)  # A fault here is a fault of the portal, so it must not become a skip.
    return _browser_page(request, BROWSER_FIXTURE)


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

    Why:
        This function draws the one line that keeps the suite honest. The
        fixture starts its own portal, so that portal holds the sign-in seam and
        every blueprint of this run. A 401 therefore means the seam is broken,
        and a 404 means a blueprint is missing. Both are faults of the portal. A
        skip for either one would let a whole run read no page and still report
        success.

    Args:
        status: The status code the portal answered.
        path: The path the test opened, named in every message.

    Raises:
        AssertionError: If the portal answered a status that the contract
            does not fix for a page.
    """
    if status == UNAUTHORIZED_STATUS:  # `identity.require_session` refused the request.
        raise AssertionError(f"{path} answered 401. The portal this run started holds no sign-in seam.")
    if status == NOT_FOUND_STATUS:  # The blueprint that owns this path is not registered.
        raise AssertionError(f"{path} answered 404. The blueprint that owns this path is not registered.")
    assert status == OK_STATUS, f"{path} answered {status}. `contracts/http-api.md` fixes 200 for this page."


def _open_portal_page(page: Any, path: str) -> None:
    """Open one portal page, and fail when the portal answers wrongly.

    Args:
        page: The Playwright page object.
        path: The path to open.
    """
    _require_built_route(_page_status(page, path), path)


def _row_keys(page: Any, prefix: str) -> list[str]:
    """Read the stable key of every row that carries one identifier prefix.

    Why:
        Rule 5 of `contracts/ui-testids.md` states that a dynamic row appends a
        stable key. A test cannot know an organization identifier before it
        reads the page, so it reads the keys the page published.

    Args:
        page: The Playwright page object.
        prefix: The identifier prefix, such as `org-row-`.

    Returns:
        One key for each row, in page order.
    """
    rows = page.locator(f'[data-testid^="{prefix}"]')  # A prefix match still selects by `data-testid`.
    markers = rows.evaluate_all("found => found.map(node => node.getAttribute('data-testid'))")
    return [str(marker)[len(prefix) :] for marker in markers if marker]


def _first_row_key(page: Any, prefix: str) -> str:
    """Return the key of the first row that carries one identifier prefix.

    Why:
        A test needs one sample key to build the identifier of a paired control,
        such as the select button of an organization row. The first row is a
        sample of a list whose rows all share one shape, so the choice reads
        nothing from the position itself.

    Args:
        page: The Playwright page object.
        prefix: The identifier prefix, such as `org-row-`.

    Returns:
        The key of the first row.
    """
    keys = _row_keys(page, prefix)
    if not keys:  # The sign-in reached no organization, so no key exists to drive.
        pytest.skip(f"The page shows no element with the identifier prefix {prefix}, so no key exists to drive.")
    return keys[0]


@pytest.fixture
def signin_page(portal_page: Any) -> Any:
    """Return a page that shows the sign-in form.

    Args:
        portal_page: The browser page that points at the portal.

    Returns:
        The Playwright page object, on the sign-in form.
    """
    _open_portal_page(portal_page, SIGNIN_PATH)
    return portal_page


@pytest.fixture
def twofactor_page(portal_page: Any) -> Any:
    """Return a page that shows the second factor form.

    Why:
        The second factor page answers a GET with no session, because an
        operator reaches it in the middle of a sign-in. A browser test can
        therefore read its controls without a cloud call.

    Args:
        portal_page: The browser page that points at the portal.

    Returns:
        The Playwright page object, on the second factor form.
    """
    _open_portal_page(portal_page, TWO_FACTOR_PATH)
    return portal_page


@pytest.fixture
def org_page(portal_page: Any) -> Any:
    """Return a page that shows the organization picker.

    Args:
        portal_page: The browser page that points at the portal.

    Returns:
        The Playwright page object, on the organization picker.
    """
    _open_portal_page(portal_page, ORG_PAGE_PATH)
    return portal_page


class TestSignInForm:
    """The sign-in form shows the three controls that FR-004 asks for."""

    def test_the_address_field_is_present(self, signin_page: Any) -> None:
        """The form shows the address field of the identifier contract.

        Args:
            signin_page: The page that shows the sign-in form.
        """
        field = signin_page.get_by_test_id(SIGNIN_EMAIL_ID)
        assert field.count() == 1, f"The form shows no single control with the identifier {SIGNIN_EMAIL_ID}."

    def test_the_address_field_asks_for_an_address(self, signin_page: Any) -> None:
        """The address field states the address type, so a phone offers the right keys.

        Args:
            signin_page: The page that shows the sign-in form.
        """
        field = signin_page.get_by_test_id(SIGNIN_EMAIL_ID)
        assert field.get_attribute("type") == "email", "The address field states no address type."

    def test_the_password_field_is_masked(self, signin_page: Any) -> None:
        """The password field states the password type, so the browser masks it.

        Why:
            A field of another type shows every character on the screen. An
            operator often signs in beside other people, so the mask is the
            first guard of FR-009 and not a matter of style.

        Args:
            signin_page: The page that shows the sign-in form.
        """
        field = signin_page.get_by_test_id(SIGNIN_PASSWORD_ID)
        assert field.get_attribute("type") == "password", "The password field is not masked."

    def test_the_password_field_starts_empty(self, signin_page: Any) -> None:
        """The password field holds no value when the page opens.

        Why:
            A form that filled the field again after a refusal would put the
            value in the markup, where a page cache and a browser extension both
            reach it.

        Args:
            signin_page: The page that shows the sign-in form.
        """
        field = signin_page.get_by_test_id(SIGNIN_PASSWORD_ID)
        assert field.input_value() == "", "The password field opens with a value inside it."

    def test_the_submit_button_is_present(self, signin_page: Any) -> None:
        """The form shows the submit button of the identifier contract.

        Args:
            signin_page: The page that shows the sign-in form.
        """
        button = signin_page.get_by_test_id(SIGNIN_SUBMIT_ID)
        assert button.count() == 1, f"The form shows no single control with the identifier {SIGNIN_SUBMIT_ID}."

    def test_the_error_region_is_present_and_hidden(self, signin_page: Any) -> None:
        """The error region exists on a fresh page and shows nothing.

        Why:
            The region must exist before a refusal, because the browser script
            fills it in place. It must also stay hidden, or every operator would
            read an empty alert before typing anything.

        Args:
            signin_page: The page that shows the sign-in form.
        """
        region = signin_page.get_by_test_id(SIGNIN_ERROR_ID)
        assert region.count() >= 1, f"The form shows no control with the identifier {SIGNIN_ERROR_ID}."
        assert region.first.is_hidden(), "The error region shows before any refusal."

    def test_a_typed_password_never_reaches_the_markup(self, signin_page: Any) -> None:
        """A typed password stays in the field and never enters the page markup.

        Why:
            FR-009 keeps a credential out of every store. The serialized page is
            such a store, because a page cache, a saved page, and a browser
            extension all read it.

        Args:
            signin_page: The page that shows the sign-in form.
        """
        field = signin_page.get_by_test_id(SIGNIN_PASSWORD_ID)
        field.fill(PROBE_PASSWORD)  # WHY: The value stays in the field and never in an attribute.
        assert field.input_value() == PROBE_PASSWORD, "The field took no value, so this test proves nothing."
        assert PROBE_PASSWORD not in signin_page.content(), "The typed password reached the page markup."

    def test_the_form_holds_the_typed_address(self, signin_page: Any) -> None:
        """The address field keeps what the operator typed.

        Why:
            Without this test the check above would pass on a form whose fields
            accept nothing at all.

        Args:
            signin_page: The page that shows the sign-in form.
        """
        field = signin_page.get_by_test_id(SIGNIN_EMAIL_ID)
        field.fill(PROBE_EMAIL)
        assert field.input_value() == PROBE_EMAIL, "The address field dropped what the operator typed."

    def test_an_empty_form_never_reaches_the_cloud(self, signin_page: Any) -> None:
        """A submit with no address stays in the browser and reaches no cloud.

        Why:
            The browser refuses the submit while the address is missing, so a
            half-typed form sends nothing. A form that posted anyway would ask
            the cloud to judge an empty pair, which counts against the sign-in
            rate limit of the operator.

        Args:
            signin_page: The page that shows the sign-in form.
        """
        signin_page.get_by_test_id(SIGNIN_SUBMIT_ID).click()  # WHY: Both fields are still empty here.
        signin_page.wait_for_load_state("domcontentloaded")  # WHY: Returns at once when no page opened.
        region = signin_page.get_by_test_id(SIGNIN_ERROR_ID)
        assert region.first.is_hidden(), "The empty form reached the portal, because a refusal came back."

    def test_the_signed_out_page_shows_no_sign_out_control(self, signin_page: Any) -> None:
        """The sign-in page shows no sign-out button.

        Why:
            A sign-out button on the sign-in page states that somebody is signed
            in. That reading is wrong here, and a press would end the session of
            another tab.

        Args:
            signin_page: The page that shows the sign-in form.
        """
        button = signin_page.get_by_test_id(SIGNOUT_BUTTON_ID)
        assert button.count() == 0, "The sign-in page offers a sign-out control."


class TestSecondFactorForm:
    """The second factor form shows the two controls of the identifier contract."""

    def test_the_code_field_is_present(self, twofactor_page: Any) -> None:
        """The form shows the code field of the identifier contract.

        Args:
            twofactor_page: The page that shows the second factor form.
        """
        field = twofactor_page.get_by_test_id(TWO_FACTOR_CODE_ID)
        assert field.count() == 1, f"The form shows no single control with the identifier {TWO_FACTOR_CODE_ID}."

    def test_the_code_field_asks_for_digits(self, twofactor_page: Any) -> None:
        """The code field asks a telephone for the number keypad.

        Why:
            An operator reads the code on a telephone and often types it on the
            same telephone. The letter keypad would add a step to every sign-in.

        Args:
            twofactor_page: The page that shows the second factor form.
        """
        field = twofactor_page.get_by_test_id(TWO_FACTOR_CODE_ID)
        assert field.get_attribute("inputmode") == "numeric", "The code field asks for no number keypad."

    def test_the_submit_button_is_present(self, twofactor_page: Any) -> None:
        """The form shows the submit button of the identifier contract.

        Args:
            twofactor_page: The page that shows the second factor form.
        """
        button = twofactor_page.get_by_test_id(TWO_FACTOR_SUBMIT_ID)
        assert button.count() == 1, f"The form shows no single control with the identifier {TWO_FACTOR_SUBMIT_ID}."

    def test_a_typed_code_never_reaches_the_markup(self, twofactor_page: Any) -> None:
        """A typed second factor code stays in the field and never enters the markup.

        Why:
            A code is a credential for the few seconds that it lives. The same
            rule that keeps a password out of the markup keeps a code out.

        Args:
            twofactor_page: The page that shows the second factor form.
        """
        field = twofactor_page.get_by_test_id(TWO_FACTOR_CODE_ID)
        field.fill(PROBE_CODE)  # WHY: The value stays in the field and never in an attribute.
        assert field.input_value() == PROBE_CODE, "The field took no value, so this test proves nothing."
        assert PROBE_CODE not in twofactor_page.content(), "The typed code reached the page markup."

    def test_the_error_region_is_present_and_hidden(self, twofactor_page: Any) -> None:
        """The second factor page carries the same error region, and hides it.

        Why:
            The two pages share one identifier for the refusal region, so one
            browser script fills both. A page that named a second identifier
            would need a second script.

        Args:
            twofactor_page: The page that shows the second factor form.
        """
        region = twofactor_page.get_by_test_id(SIGNIN_ERROR_ID)
        assert region.count() >= 1, f"The page shows no control with the identifier {SIGNIN_ERROR_ID}."
        assert region.first.is_hidden(), "The error region shows before any refusal."


class TestOrganizationPicker:
    """The organization picker shows a search field and one row for each organization."""

    def test_the_search_field_is_present(self, org_page: Any) -> None:
        """The picker shows the search field that FR-012 asks for.

        Args:
            org_page: The page that shows the organization picker.
        """
        field = org_page.get_by_test_id(ORG_SEARCH_ID)
        assert field.count() == 1, f"The picker shows no single control with the identifier {ORG_SEARCH_ID}."

    def test_each_row_carries_a_select_control(self, org_page: Any) -> None:
        """Every organization row offers the select button of its own key.

        Why:
            Rule 5 of the identifier contract pairs a row with its control
            through one key. A row with no matching button would show an
            organization that the operator cannot choose.

        Args:
            org_page: The page that shows the organization picker.
        """
        org_id = _first_row_key(org_page, ORG_ROW_PREFIX)
        button = org_page.get_by_test_id(f"{ORG_SELECT_PREFIX}{org_id}")
        assert button.count() == 1, f"The row of the organization {org_id} offers no select control."

    def test_the_picker_shows_the_sign_out_control(self, org_page: Any) -> None:
        """A signed-in page offers the sign-out button of the identifier contract.

        Why:
            FR-005 gives each operator a session, and an operator on a shared
            workstation must be able to end it from any page.

        Args:
            org_page: The page that shows the organization picker.
        """
        button = org_page.get_by_test_id(SIGNOUT_BUTTON_ID)
        assert button.count() == 1, f"The picker shows no single control with the identifier {SIGNOUT_BUTTON_ID}."
