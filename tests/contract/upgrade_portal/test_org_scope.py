"""Contract tests for the organization scope of one signed-in operator.

Why:
    A managed service provider account reaches many organizations, and it must
    not reach every organization. Three rules follow from that, and this file
    pins all three: the picker lists the organizations of the current sign-in,
    the choice reaches the signed session, and an organization outside the scope
    answers ``403 org_not_permitted``.

    ``tests/contract/upgrade_portal/test_select.py`` covers the read routes of
    the same blueprint. It drives no post at all, so the choice and its refusal
    had no contract cover before this file. It also checks the scope through the
    site list path alone, which proves nothing about the picker itself.

    One module holds the scope rule. ``runtime/identity.py`` owns the decision,
    the ``org_not_permitted`` code, the refusal sentence, and the 403 status.
    ``app/routes/select.py`` calls that owner and keeps no copy of any of the
    four. A test below drives the primitive and the route helper together and
    asserts that they answer the same way, so a route that stopped delegating
    would fail here.

    No test opens a socket, reads the ``.env`` file, or reaches the Mist cloud.
    The organization scope arrives on a stand-in cloud session, which is the
    same seam that the real sign-in fills.

    Every value below is a literal. A test that imported a constant from the
    module under test would agree with a renamed field and would prove nothing.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import flask
import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

# WHY: The module, never a constant of it. One test drives the route helper
# beside the identity primitive and proves that the route still delegates.
from src.upgrade_portal.app.routes import select
from src.upgrade_portal.runtime import identity

# ---------------------------------------------------------------------------
# The contract values
# ---------------------------------------------------------------------------

# WHY: `contracts/http-api.md` fixes this path for the picker and for the choice.
ORG_PAGE_PATH = "/select/org"

# WHY: The contract fixes the path that a successful choice names next.
NEXT_AFTER_ORG = "/select/site"

# WHY: The body field and the signed session field that carry the choice.
ORG_FIELD = "org_id"
SELECTED_ORG_SESSION_KEY = "selected_org_id"

# WHY: The header that separates the browser form post from the portal script.
SCRIPT_HEADER = "X-Requested-With"
SCRIPT_HEADER_VALUE = "XMLHttpRequest"
SCRIPT_HEADERS = {SCRIPT_HEADER: SCRIPT_HEADER_VALUE}
BROWSER_HEADERS = {"Accept": "text/html"}
LOCATION_HEADER = "Location"

# WHY: The error codes that the contract fixes for this stage.
NOT_AUTHENTICATED_CODE = "not_authenticated"
ORG_NOT_CHOSEN_CODE = "org_not_chosen"
ORG_NOT_PERMITTED_CODE = "org_not_permitted"

# WHY: The statuses the contract fixes. A browser post earns 303, so the back
# button of the browser never repeats the post.
OK_STATUS = 200
REDIRECT_STATUS = 303
BAD_REQUEST_STATUS = 400
UNAUTHORIZED_STATUS = 401
FORBIDDEN_STATUS = 403

# WHY: A reserved domain, so no address here reaches a mail server.
PROBE_EMAIL = "probe.operator@example.invalid"

# WHY: Fixed identifiers keep the stand-in scope and every path in agreement.
# The second organization sorts after the first by name, so one test can prove
# the picker order without a third record.
SECOND_ORG_ID = "00000000-0000-0000-0000-0000000000ee"
OUTSIDE_ORG_ID = "00000000-0000-0000-0000-0000000000cc"
FIRST_ORG_NAME = "Alpha Networks"
SECOND_ORG_NAME = "Zulu Networks"

# WHY: The identifier prefix that `contracts/ui-testids.md` fixes for one row of
# the picker. The contract test reads the rendered page for this marker, so the
# browser test and this file drive one page through one contract.
ORG_ROW_PREFIX = "org-row-"


# ---------------------------------------------------------------------------
# The stand-in cloud session
# ---------------------------------------------------------------------------


class ScopedCloudSession:
    """Stand-in for a Mist cloud session that states its organization scope.

    Why:
        The portal reads the scope of a sign-in from the privilege list of the
        cloud session. A plain object states no scope at all, so a test of the
        refusal path needs a session that does state one.
    """

    def __init__(self, orgs: tuple[tuple[str, str], ...]) -> None:
        """Build a cloud session that reaches the named organizations.

        Args:
            orgs: One pair of identifier and name for each organization that the
                sign-in may act on.
        """
        self.privileges: list[dict[str, str]] = [{"org_id": key, "name": name} for key, name in orgs]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def register_owner(cloud_session: Any) -> Iterator[identity.SessionOwner]:
    """Register one operator, yield the identity pair, then drop the record.

    Why:
        The registry is a process global that outlives one test. One helper
        keeps the cleanup in one place, so no leaked record signs in a later
        test by accident.

    Args:
        cloud_session: The stand-in for the Mist cloud session.

    Yields:
        The identity pair of the registered operator.
    """
    owner = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())
    record = identity.OperatorSession(
        owner=owner,
        cloud_session=cloud_session,
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
    )
    identity.SESSION_REGISTRY.register(record)
    try:
        yield owner
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # WHY: The registry outlives the test, so clear it here.


def sign_in_client(client: FlaskClient, owner: identity.SessionOwner) -> None:
    """Give one test client the session and the cookie of a registered owner.

    Why:
        The guard checks the signed session against the browser cookie. Both
        halves must agree, so this helper sets both in one place.

    Args:
        client: The test client to sign in.
        owner: The identity pair of the registered operator.
    """
    client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
    with client.session_transaction() as browser_session:
        browser_session[identity.SESSION_OWNER_KEY] = owner.key


def post_org(client: FlaskClient, org_id: str | None) -> TestResponse:
    """Post one organization choice the way the portal script posts it.

    Args:
        client: The test client that carries the session.
        org_id: The organization to choose, or None to post an empty body.

    Returns:
        The response of the portal.
    """
    body = {} if org_id is None else {ORG_FIELD: org_id}  # WHY: An empty body stands for a form with no choice.
    return client.post(ORG_PAGE_PATH, json=body, headers=SCRIPT_HEADERS)


def read_error_code(response: TestResponse) -> str:
    """Return the ``code`` field of an error envelope.

    Why:
        ``contracts/README.md`` states that a test asserts on ``code`` and never
        on ``message``. One reader keeps every test on that rule.

    Args:
        response: The response that holds the envelope.

    Returns:
        The error code.
    """
    payload: dict[str, Any] = response.get_json()
    return str(payload["error"]["code"])


def read_stored_org(client: FlaskClient) -> str | None:
    """Return the organization that the signed browser session holds.

    Args:
        client: The test client that carries the session.

    Returns:
        The stored identifier, or None when the session holds none.
    """
    with client.session_transaction() as browser_session:
        stored = browser_session.get(SELECTED_ORG_SESSION_KEY)
    return None if stored is None else str(stored)


def signed_in_context(app: Flask, owner: identity.SessionOwner) -> Any:
    """Build a request context that carries the session of one owner.

    Why:
        Four tests below call an `identity` function directly instead of driving
        a route. Those functions read the signed session and the browser cookie,
        so they need a request context that holds both halves of the pair.

    Args:
        app: The portal application.
        owner: The identity pair of the registered operator.

    Returns:
        The request context, ready to enter.
    """
    cookie = f"{identity.BROWSER_ID_COOKIE}={owner.browser_id}"  # WHY: The guard reads the cookie half here.
    return app.test_request_context(ORG_PAGE_PATH, headers={"Cookie": cookie})


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def scope_app(portal_app: Flask) -> Flask:
    """Return the portal application with the token check turned off.

    Why:
        `PortalSecurity` arms the token check for every state-changing request,
        and this file drives the choice through a post. The token check has its
        own contract cover in `test_security.py`, so this file turns it off and
        checks the scope rule alone.

    Args:
        portal_app: The real application from the shared fixture.

    Returns:
        The application, ready for a post.
    """
    portal_app.config["WTF_CSRF_ENABLED"] = False  # WHY: `test_security.py` owns the token cover.
    return portal_app


@pytest.fixture
def scope_client(scope_app: Flask) -> Iterator[FlaskClient]:
    """Return a test client for the application.

    Args:
        scope_app: The application with the token check turned off.

    Yields:
        The Flask test client, with the session held open.
    """
    with scope_app.test_client() as client:  # WHY: The context manager holds the session across requests.
        yield client


@pytest.fixture
def scoped_owner(fake_org_id: str) -> Iterator[identity.SessionOwner]:
    """Register one operator that reaches two organizations and no third.

    Args:
        fake_org_id: The organization every canned payload uses.

    Yields:
        The identity pair of the registered operator.
    """
    scope = ((fake_org_id, FIRST_ORG_NAME), (SECOND_ORG_ID, SECOND_ORG_NAME))
    yield from register_owner(ScopedCloudSession(scope))


@pytest.fixture
def unscoped_owner() -> Iterator[identity.SessionOwner]:
    """Register one operator whose cloud session states no scope at all.

    Why:
        An environment token session names no privilege list. The portal must
        treat that state as unknown and not as an empty scope, because a closed
        answer there would refuse every organization.

    Yields:
        The identity pair of the registered operator.
    """
    yield from register_owner(object())  # WHY: A plain object names no privilege list.


@pytest.fixture
def scoped_client(scope_client: FlaskClient, scoped_owner: identity.SessionOwner) -> FlaskClient:
    """Return a client that is signed in as the operator with two organizations.

    Args:
        scope_client: The test client for the application.
        scoped_owner: The registered operator.

    Returns:
        The signed-in client.
    """
    sign_in_client(scope_client, scoped_owner)
    return scope_client


# ---------------------------------------------------------------------------
# The picker
# ---------------------------------------------------------------------------


def test_the_picker_answers_a_page_for_a_signed_in_operator(scoped_client: FlaskClient) -> None:
    """The organization picker answers 200 for a signed-in operator.

    Args:
        scoped_client: The signed-in client.
    """
    answer = scoped_client.get(ORG_PAGE_PATH)
    assert answer.status_code == OK_STATUS, f"{ORG_PAGE_PATH} answered {answer.status_code}."


def test_the_picker_lists_one_row_for_each_permitted_organization(
    scoped_client: FlaskClient,
    fake_org_id: str,
) -> None:
    """The picker shows a row for each organization of the current sign-in.

    Why:
        FR-012 asks for a picker of the organizations that this sign-in may act
        on. A picker built from a wider list would offer a row that the choice
        then refuses, which reads to an operator as a broken portal.

    Args:
        scoped_client: The signed-in client.
        fake_org_id: The first organization of the scope.
    """
    page = scoped_client.get(ORG_PAGE_PATH).get_data(as_text=True)
    assert f"{ORG_ROW_PREFIX}{fake_org_id}" in page, "The picker shows no row for the first organization."
    assert f"{ORG_ROW_PREFIX}{SECOND_ORG_ID}" in page, "The picker shows no row for the second organization."


def test_the_picker_hides_an_organization_outside_the_scope(scoped_client: FlaskClient) -> None:
    """The picker shows no row for an organization outside the scope.

    Why:
        The picker and the refusal must read one scope. A row that the choice
        then refuses would send the operator down a path that always fails.

    Args:
        scoped_client: The signed-in client.
    """
    page = scoped_client.get(ORG_PAGE_PATH).get_data(as_text=True)
    assert OUTSIDE_ORG_ID not in page, "The picker names an organization that this sign-in may not reach."


def test_the_picker_orders_the_rows_by_name(scoped_client: FlaskClient, fake_org_id: str) -> None:
    """The picker lists the organizations by name and not by identifier.

    Why:
        An operator finds an organization by its name. An order by identifier
        would scatter the names, so a long list would need the search field for
        every pick.

    Args:
        scoped_client: The signed-in client.
        fake_org_id: The organization whose name sorts first.
    """
    page = scoped_client.get(ORG_PAGE_PATH).get_data(as_text=True)
    first = page.find(f"{ORG_ROW_PREFIX}{fake_org_id}")
    second = page.find(f"{ORG_ROW_PREFIX}{SECOND_ORG_ID}")
    assert -1 < first < second, f"{FIRST_ORG_NAME} must stand before {SECOND_ORG_NAME} on the picker."


def test_the_picker_refuses_a_request_with_no_session(scope_client: FlaskClient) -> None:
    """The picker refuses a request that carries no session.

    Args:
        scope_client: A client with no session at all.
    """
    answer = scope_client.get(ORG_PAGE_PATH)
    assert answer.status_code == UNAUTHORIZED_STATUS, f"The picker answered {answer.status_code} with no session."
    assert read_error_code(answer) == NOT_AUTHENTICATED_CODE


# ---------------------------------------------------------------------------
# The choice
# ---------------------------------------------------------------------------


def test_a_permitted_organization_answers_the_next_path(scoped_client: FlaskClient, fake_org_id: str) -> None:
    """A choice inside the scope answers 200 and names the next page.

    Args:
        scoped_client: The signed-in client.
        fake_org_id: An organization inside the scope.
    """
    answer = post_org(scoped_client, fake_org_id)
    assert answer.status_code == OK_STATUS, f"The choice answered {answer.status_code}."
    assert answer.get_json() == {"next": NEXT_AFTER_ORG}


def test_a_permitted_organization_reaches_the_signed_session(scoped_client: FlaskClient, fake_org_id: str) -> None:
    """The chosen organization reaches the signed browser session.

    Why:
        `contracts/http-api.md` holds the organization in the session, so the
        site list needs no organization in its path. A choice that answered 200
        and stored nothing would leave the next page with no organization.

    Args:
        scoped_client: The signed-in client.
        fake_org_id: An organization inside the scope.
    """
    post_org(scoped_client, fake_org_id)
    assert read_stored_org(scoped_client) == fake_org_id


def test_a_browser_form_post_answers_a_redirect(scoped_client: FlaskClient, fake_org_id: str) -> None:
    """A plain form post answers 303 and names the next page in the header.

    Why:
        A browser shows a JSON body as raw text. The page must therefore answer
        a redirect, and 303 keeps the back button from repeating the post.

    Args:
        scoped_client: The signed-in client.
        fake_org_id: An organization inside the scope.
    """
    answer = scoped_client.post(ORG_PAGE_PATH, data={ORG_FIELD: fake_org_id}, headers=BROWSER_HEADERS)
    assert answer.status_code == REDIRECT_STATUS, f"The form post answered {answer.status_code}."
    assert answer.headers.get(LOCATION_HEADER) == NEXT_AFTER_ORG


def test_the_script_header_wins_over_the_page_header(scoped_client: FlaskClient, fake_org_id: str) -> None:
    """A script that inherits the page header still reads a JSON body.

    Why:
        A script inside a browser page inherits the `Accept` header of that
        page. Without this rule the portal would answer a redirect to `fetch`,
        and the picker would look frozen to the operator.

    Args:
        scoped_client: The signed-in client.
        fake_org_id: An organization inside the scope.
    """
    headers = {**BROWSER_HEADERS, **SCRIPT_HEADERS}  # WHY: Both headers arrive on one real request.
    answer = scoped_client.post(ORG_PAGE_PATH, json={ORG_FIELD: fake_org_id}, headers=headers)
    assert answer.status_code == OK_STATUS, f"The script post answered {answer.status_code}."
    assert answer.get_json() == {"next": NEXT_AFTER_ORG}


def test_a_second_choice_replaces_the_first(scoped_client: FlaskClient, fake_org_id: str) -> None:
    """A second choice inside the scope replaces the stored organization.

    Args:
        scoped_client: The signed-in client.
        fake_org_id: The organization the operator chooses first.
    """
    post_org(scoped_client, fake_org_id)
    post_org(scoped_client, SECOND_ORG_ID)
    assert read_stored_org(scoped_client) == SECOND_ORG_ID


# ---------------------------------------------------------------------------
# The refusal
# ---------------------------------------------------------------------------


def test_an_organization_outside_the_scope_is_refused(scoped_client: FlaskClient) -> None:
    """A choice outside the scope answers 403 and the documented code.

    Why:
        This is the rule of User Story 5. An account that reaches two
        organizations must not drive an upgrade in a third, whatever the browser
        posts.

    Args:
        scoped_client: The signed-in client.
    """
    answer = post_org(scoped_client, OUTSIDE_ORG_ID)
    assert answer.status_code == FORBIDDEN_STATUS, f"The refused choice answered {answer.status_code}."
    assert read_error_code(answer) == ORG_NOT_PERMITTED_CODE


def test_the_refused_organization_never_reaches_the_session(scoped_client: FlaskClient) -> None:
    """A refused organization never reaches the signed browser session.

    Why:
        A refusal that still stored the pick would let the next page act on the
        organization that this page just refused.

    Args:
        scoped_client: The signed-in client.
    """
    post_org(scoped_client, OUTSIDE_ORG_ID)
    assert read_stored_org(scoped_client) is None


def test_a_refused_choice_never_replaces_a_permitted_choice(scoped_client: FlaskClient, fake_org_id: str) -> None:
    """A refused choice leaves an earlier permitted choice in place.

    Args:
        scoped_client: The signed-in client.
        fake_org_id: The organization the operator chose first.
    """
    post_org(scoped_client, fake_org_id)
    post_org(scoped_client, OUTSIDE_ORG_ID)
    assert read_stored_org(scoped_client) == fake_org_id


def test_a_body_with_no_organization_is_refused(scoped_client: FlaskClient) -> None:
    """A post that names no organization answers 400 and the documented code.

    Args:
        scoped_client: The signed-in client.
    """
    answer = post_org(scoped_client, None)
    assert answer.status_code == BAD_REQUEST_STATUS, f"The empty choice answered {answer.status_code}."
    assert read_error_code(answer) == ORG_NOT_CHOSEN_CODE


def test_the_choice_refuses_a_request_with_no_session(scope_client: FlaskClient, fake_org_id: str) -> None:
    """The choice refuses a request that carries no session.

    Why:
        The refusal of a missing session answers 401 and not 403. The two
        answers name two different faults, and an operator whose session ended
        must reach the sign-in page instead of an access message.

    Args:
        scope_client: A client with no session at all.
        fake_org_id: Any organization identifier.
    """
    answer = post_org(scope_client, fake_org_id)
    assert answer.status_code == UNAUTHORIZED_STATUS, f"The choice answered {answer.status_code} with no session."
    assert read_error_code(answer) == NOT_AUTHENTICATED_CODE


def test_a_session_that_states_no_scope_reaches_every_organization(
    scope_client: FlaskClient,
    unscoped_owner: identity.SessionOwner,
) -> None:
    """A sign-in that lists no privilege passes the scope check.

    Why:
        An environment token session names no privilege list. The portal must
        read that state as unknown and not as an empty scope. A closed answer
        there would refuse every organization and would hide the real refusal.

    Args:
        scope_client: The test client.
        unscoped_owner: The registered operator with no stated scope.
    """
    sign_in_client(scope_client, unscoped_owner)
    answer = post_org(scope_client, OUTSIDE_ORG_ID)
    assert answer.status_code == OK_STATUS, f"An unknown scope answered {answer.status_code} instead of passing."


# ---------------------------------------------------------------------------
# The scope primitive of the identity module
# ---------------------------------------------------------------------------


def test_the_identity_scope_lists_every_permitted_organization(
    scope_app: Flask,
    scoped_owner: identity.SessionOwner,
    fake_org_id: str,
) -> None:
    """The identity module reports both organizations of the sign-in.

    Args:
        scope_app: The portal application.
        scoped_owner: The registered operator with two organizations.
        fake_org_id: The first organization of the scope.
    """
    with signed_in_context(scope_app, scoped_owner):
        flask.session[identity.SESSION_OWNER_KEY] = scoped_owner.key
        assert identity.permitted_org_ids() == frozenset({fake_org_id, SECOND_ORG_ID})


def test_an_unknown_scope_reads_as_none_and_never_as_an_empty_set(
    scope_app: Flask,
    unscoped_owner: identity.SessionOwner,
) -> None:
    """A sign-in that lists no privilege reports an unknown scope.

    Why:
        None and an empty set carry two different meanings here. None means the
        portal does not know the scope, and an empty set means the portal knows
        that the sign-in reaches nothing. A reader that returned an empty set
        for an unknown scope would refuse every request.

    Args:
        scope_app: The portal application.
        unscoped_owner: The registered operator with no stated scope.
    """
    with signed_in_context(scope_app, unscoped_owner):
        flask.session[identity.SESSION_OWNER_KEY] = unscoped_owner.key
        assert identity.permitted_org_ids() is None


def test_a_request_with_no_session_states_an_unknown_scope(scope_app: Flask) -> None:
    """A request with no session reports an unknown scope and raises nothing.

    Why:
        `require_session` owns the refusal of a missing session. The scope
        reader must therefore answer and never raise, because a raise here would
        turn a clean 401 into a fault page.

    Args:
        scope_app: The portal application.
    """
    with scope_app.test_request_context(ORG_PAGE_PATH):
        assert identity.permitted_org_ids() is None


def test_the_route_helper_and_the_identity_module_agree_on_the_scope(
    scope_app: Flask,
    scoped_owner: identity.SessionOwner,
    fake_org_id: str,
) -> None:
    """The route helper answers the same scope that the identity primitive holds.

    Why:
        `runtime/identity.py` owns this rule and `app/routes/select.py` once held
        a copy. A route that kept a copy could admit an organization that the
        primitive refuses. This test drives both, so a route that stops
        delegating fails here.

    Args:
        scope_app: The portal application.
        scoped_owner: The registered operator with two organizations.
        fake_org_id: An organization inside the scope.
    """
    with signed_in_context(scope_app, scoped_owner):
        flask.session[identity.SESSION_OWNER_KEY] = scoped_owner.key
        assert identity.org_is_permitted(fake_org_id) is True
        assert identity.org_is_permitted(OUTSIDE_ORG_ID) is False
        assert select.org_refusal(fake_org_id) is None
        refused = select.org_refusal(OUTSIDE_ORG_ID)
    assert refused is not None, "The route helper admitted an organization outside the scope."
    assert refused[0].get_json()["error"]["code"] == ORG_NOT_PERMITTED_CODE


def test_the_scope_refusal_carries_the_documented_code_and_status(
    scope_app: Flask,
    scoped_owner: identity.SessionOwner,
) -> None:
    """The identity refusal answers 403 and the documented code.

    Args:
        scope_app: The portal application.
        scoped_owner: The registered operator with two organizations.
    """
    with signed_in_context(scope_app, scoped_owner):
        flask.session[identity.SESSION_OWNER_KEY] = scoped_owner.key
        refusal = identity.org_scope_refusal(OUTSIDE_ORG_ID)
    assert refusal is not None, "The identity module admitted an organization outside the scope."
    assert refusal[1] == FORBIDDEN_STATUS
    assert refusal[0].get_json()["error"]["code"] == ORG_NOT_PERMITTED_CODE


def test_the_scope_refusal_admits_an_organization_inside_the_scope(
    scope_app: Flask,
    scoped_owner: identity.SessionOwner,
    fake_org_id: str,
) -> None:
    """The identity refusal answers None for an organization inside the scope.

    Args:
        scope_app: The portal application.
        scoped_owner: The registered operator with two organizations.
        fake_org_id: An organization inside the scope.
    """
    with signed_in_context(scope_app, scoped_owner):
        flask.session[identity.SESSION_OWNER_KEY] = scoped_owner.key
        assert identity.org_scope_refusal(fake_org_id) is None


@identity.require_org_scope
def guarded_view(org_id: str) -> str:
    """Stand for a route whose path names one organization.

    Why:
        The guard reads the path value that Flask passes as a keyword argument.
        A test that registered a real route would need a second application, so
        this function calls the guard the same way that Flask calls it.

    Args:
        org_id: The organization the path named.

    Returns:
        A short marker that proves the route function ran.
    """
    return f"reached {org_id}"


def test_the_scope_guard_refuses_an_organization_named_in_a_path(
    scope_app: Flask,
    scoped_owner: identity.SessionOwner,
) -> None:
    """The guard refuses a path organization outside the scope.

    Args:
        scope_app: The portal application.
        scoped_owner: The registered operator with two organizations.
    """
    with signed_in_context(scope_app, scoped_owner):
        flask.session[identity.SESSION_OWNER_KEY] = scoped_owner.key
        answer = guarded_view(org_id=OUTSIDE_ORG_ID)
    assert isinstance(answer, tuple), "The guard let a refused organization reach the route function."
    assert answer[1] == FORBIDDEN_STATUS


def test_the_scope_guard_admits_an_organization_inside_the_scope(
    scope_app: Flask,
    scoped_owner: identity.SessionOwner,
    fake_org_id: str,
) -> None:
    """The guard calls the route function for an organization inside the scope.

    Args:
        scope_app: The portal application.
        scoped_owner: The registered operator with two organizations.
        fake_org_id: An organization inside the scope.
    """
    with signed_in_context(scope_app, scoped_owner):
        flask.session[identity.SESSION_OWNER_KEY] = scoped_owner.key
        answer = guarded_view(org_id=fake_org_id)
    assert answer == f"reached {fake_org_id}"
