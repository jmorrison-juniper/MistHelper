"""Contract tests for the organization picker, the site list, and the inventory.

Why:
    Stage two of the operator journey answers one question: which site does this
    upgrade run act on? Two documents describe the answer, and they disagree on
    one path. ``contracts/http-api.md`` names ``GET /api/sites`` and holds the
    organization in the session. ``tasks.md`` names
    ``GET /api/orgs/<org_id>/sites`` and holds it in the path. The portal binds
    both rules to one endpoint, so both documents stay true. These tests pin that
    decision, pin the response shape of each route, and pin the endpoint names
    that the page templates render against.

    Every test drives the real routes through the Flask test client. No test
    opens a socket, reads the ``.env`` file, or reaches the Mist cloud. The
    cloud read, the device read, and the site lock read all arrive as injected
    stand-ins through the application configuration.

    Every value below is a literal. A test that imported a constant from the
    module under test would agree with a renamed field and would prove nothing.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.upgrade_portal.runtime import identity

# ---------------------------------------------------------------------------
# The contract values
# ---------------------------------------------------------------------------

# WHY: The paths that `contracts/http-api.md` and `tasks.md` name. A test states
# each path in full, so a renamed constant inside the route module fails here.
ORG_PAGE_PATH = "/select/org"
SITE_PAGE_PATH = "/select/site"
SITES_API_PATH = "/api/sites"
ORG_SITES_API_PATH = "/api/orgs/<org_id>/sites"
INVENTORY_API_PATH = "/api/sites/<site_id>/inventory"

# WHY: The page templates and the browser script build every link from these
# endpoint names. A rename would break the pages with no test failure elsewhere.
ORG_PAGE_ENDPOINT = "select.org_page"
CHOOSE_ORG_ENDPOINT = "select.choose_org"
SITE_PAGE_ENDPOINT = "select.sites_page"
LIST_SITES_ENDPOINT = "select.list_sites"
INVENTORY_ENDPOINT = "select.site_inventory"

# WHY: The five fields that one site row carries. FR-012 asks for the name and
# the search. FR-015 asks for the count. `locked_by` names the operator that
# holds a site. `lock_state` names the state in one word, because a free site
# and a site the portal could not read both carry a null `locked_by`.
# `contracts/site-lock.md:138` asks a read-only page to mark that second case
# unknown, and `contracts/http-api.md:77` lists the first four names only.
SITE_ROW_FIELDS = {"site_id", "name", "device_count", "locked_by", "lock_state"}

# WHY: The three words that `lock_state` may hold. One word for each state keeps
# the page, the JSON answer, and this test file in agreement.
LOCK_STATE_FREE = "free"
LOCK_STATE_LOCKED = "locked"
LOCK_STATE_UNKNOWN = "unknown"

# WHY: FR-013 offers three device type filters, and the page shows the whole
# count above them. The inventory answer therefore carries these four counts.
# `data-model.md` section 3.6 fixes each name, and `select/inventory.html` reads
# the same four names. The cloud names a device type in the singular, so an
# earlier version of this set named the counts `ap`, `gateway`, `switch`, and
# `total`. The page then read four keys that the route never wrote, and every
# count showed the fallback value instead.
INVENTORY_COUNT_FIELDS = {"access_points", "gateways", "switches", "devices_total"}

# WHY: The configuration keys of the three seams. A contract test injects a
# stand-in here, so no test needs the cloud, the device module, or Redis.
MIST_READER_KEY = "MIST_READER"
DEVICE_READER_KEY = "DEVICE_READER"
LOCK_READER_KEY = "SITE_LOCK_READER"

# WHY: The signed session field that carries the chosen organization. The site
# list path without an organization reads the pick from this field.
SELECTED_ORG_SESSION_KEY = "selected_org_id"

# WHY: The error codes that the contract fixes for this stage.
NOT_AUTHENTICATED_CODE = "not_authenticated"
ORG_NOT_CHOSEN_CODE = "org_not_chosen"
ORG_NOT_PERMITTED_CODE = "org_not_permitted"
SITE_NOT_FOUND_CODE = "site_not_found"

# WHY: A reserved domain, so no address here reaches a mail server.
PROBE_EMAIL = "probe.operator@example.invalid"
LOCK_HOLDER_EMAIL = "other.operator@example.invalid"

# WHY: Fixed identifiers keep every canned payload and every path in agreement.
OTHER_ORG_ID = "00000000-0000-0000-0000-0000000000cc"
ABSENT_SITE_ID = "00000000-0000-0000-0000-0000000000dd"

# WHY: The organization-scoped device search is the one call that must never
# carry a device type. That parameter is legal on the site-scoped statistics
# call only, so a device type here would fail against the live cloud.
FORBIDDEN_ORG_DEVICE_READ = "searchOrgDevices"
FORBIDDEN_READ_PARAMETER = "type"


# ---------------------------------------------------------------------------
# Stand-ins for the three seams
# ---------------------------------------------------------------------------


class ScopedCloudSession:
    """Stand-in for a Mist cloud session that states its organization scope.

    Why:
        The portal refuses an organization outside the privilege list of the
        cloud session. A plain object states no scope at all, so a test that
        checks the refusal needs a session that does state one.
    """

    def __init__(self, org_ids: tuple[str, ...]) -> None:
        """Build a cloud session that reaches the named organizations.

        Args:
            org_ids: The organizations the session may act on.
        """
        self.privileges: list[dict[str, Any]] = [{"org_id": found, "name": "Scope"} for found in org_ids]


class RecordingDeviceReader:
    """Stand-in for the device read of one site.

    Why:
        The device read work lives in its own module and arrives after the
        selection routes. This stand-in proves that the inventory route reaches
        that module through the seam, and it records the call parameters so a
        test can prove that no illegal parameter travels with the read.
    """

    def __init__(self, devices: list[dict[str, Any]]) -> None:
        """Build the stand-in with one canned device list.

        Args:
            devices: The device records the reader answers with.
        """
        self.devices = devices  # WHY: The canned answer of every call.
        self.calls: list[dict[str, Any]] = []  # WHY: Records the parameters of each call.

    def __call__(self, **parameters: Any) -> list[dict[str, Any]]:
        """Answer one device read and record the call.

        Args:
            **parameters: The call parameters the route passed.

        Returns:
            A copy of the canned device list.
        """
        self.calls.append(dict(parameters))  # WHY: A copy stops a later edit of the caller dictionary.
        return list(self.devices)


class RecordingLockReader:
    """Stand-in for the site lock read.

    Why:
        ``contracts/site-lock.md`` states that reading data never needs the lock
        and that an unreachable lock store must not stop a read-only page. This
        stand-in gives three answers: a holder index, an empty index, or a
        raised error. A test can therefore check all three lock states.
    """

    def __init__(
        self,
        holders: dict[str, str | None] | None = None,
        fails: bool = False,
        empty_answer: bool = False,
    ) -> None:
        """Build the stand-in with a canned lock index.

        Args:
            holders: The address of the operator that holds each site lock.
            fails: True makes every read raise, which stands for a seam that
                breaks instead of failing open.
            empty_answer: True makes every read answer an empty index. That is
                the exact answer that ``runtime/lock.py`` gives when the lock
                store is out of reach, because a read there fails open.
        """
        self.holders = holders or {}  # WHY: An empty index means no site has a holder.
        self.fails = fails  # WHY: Stands for a seam that raises instead of failing open.
        self.empty_answer = empty_answer  # WHY: Stands for a Redis server that does not answer.
        self.calls: list[tuple[str, list[str]]] = []  # WHY: Records the organization and the sites asked about.

    def __call__(self, org_id: str, site_ids: list[str]) -> dict[str, str | None]:
        """Answer one lock read and record the call.

        Why:
            ``runtime/lock.py`` answers one entry for each site it was asked
            about while the store is reachable, and an empty index while the
            store is out of reach. This stand-in copies that rule exactly. A
            stand-in that answered only the held sites would hide the defect
            that an absent entry now reports.

        Args:
            org_id: The organization that owns the sites.
            site_ids: The sites the route asked about.

        Returns:
            The address of the operator that holds each site lock, or None for a
            free site. The index is empty when the store is out of reach.

        Raises:
            RuntimeError: When the stand-in stands for a broken seam.
        """
        self.calls.append((org_id, list(site_ids)))  # WHY: A copy stops a later edit of the caller list.
        if self.fails:  # WHY: The read-only page must survive this.
            raise RuntimeError("The lock store did not answer.")
        if self.empty_answer:  # WHY: The real reader fails open and answers nothing at all.
            return {}
        return {site_id: self.holders.get(site_id) for site_id in site_ids}  # WHY: One entry for each site asked.


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def device_reader() -> RecordingDeviceReader:
    """Return the stand-in for the device read.

    Returns:
        A fresh recording reader with one access point in its answer.
    """
    return RecordingDeviceReader([{"mac": "5c5b350e0001", "type": "ap", "model": "AP45"}])


@pytest.fixture
def lock_reader() -> RecordingLockReader:
    """Return the stand-in for the site lock read.

    Returns:
        A fresh recording reader that reports no lock at all.
    """
    return RecordingLockReader()


@pytest.fixture
def wired_app(
    portal_app: Flask,
    fake_mist_api: Any,
    device_reader: RecordingDeviceReader,
    lock_reader: RecordingLockReader,
) -> Flask:
    """Return the portal application with all three seams injected.

    Why:
        The selection routes read the cloud, the device module, and the lock
        store. The injection replaces all three, so a contract test runs with no
        network and no dependency on the build order of the other modules.

    Args:
        portal_app: The real application from the shared fixture.
        fake_mist_api: The canned cloud read surface from the shared fixture.
        device_reader: The stand-in for the device read.
        lock_reader: The stand-in for the site lock read.

    Returns:
        The application with the seams in place.
    """
    portal_app.config[MIST_READER_KEY] = fake_mist_api.read  # WHY: One canned answer for each cloud read name.
    portal_app.config[DEVICE_READER_KEY] = device_reader  # WHY: The device module may not be built yet.
    portal_app.config[LOCK_READER_KEY] = lock_reader  # WHY: No Redis server runs in a contract test.
    return portal_app


@pytest.fixture
def select_client(wired_app: Flask) -> Iterator[FlaskClient]:
    """Return a test client for the wired application.

    Args:
        wired_app: The application with the seams injected.

    Yields:
        The Flask test client, with the session held open.
    """
    with wired_app.test_client() as client:  # WHY: The context manager holds the session across requests.
        yield client


@pytest.fixture
def registered_owner() -> Iterator[identity.SessionOwner]:
    """Register one operator whose cloud session states no organization scope.

    Why:
        The guard admits a request only when the signed session and the browser
        cookie both name a registered owner. The registry is a process global,
        so the fixture drops the record again.

    Yields:
        The identity pair of the registered operator.
    """
    yield from register_owner(object())  # WHY: A plain object states no scope, so every organization passes.


@pytest.fixture
def scoped_owner() -> Iterator[identity.SessionOwner]:
    """Register one operator whose cloud session reaches one other organization.

    Why:
        The refusal path needs a session that states a scope and that does not
        hold the organization the request names.

    Yields:
        The identity pair of the registered operator.
    """
    yield from register_owner(ScopedCloudSession((OTHER_ORG_ID,)))


@pytest.fixture
def signed_in_client(
    select_client: FlaskClient,
    registered_owner: identity.SessionOwner,
    fake_org_id: str,
) -> FlaskClient:
    """Return a client that is signed in and that already chose an organization.

    Args:
        select_client: The test client for the wired application.
        registered_owner: The registered operator.
        fake_org_id: The organization every canned payload uses.

    Returns:
        The signed-in client.
    """
    sign_in_client(select_client, registered_owner)
    choose_org(select_client, fake_org_id)
    return select_client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def register_owner(cloud_session: Any) -> Iterator[identity.SessionOwner]:
    """Register one operator, yield the identity pair, then drop the record.

    Why:
        Two fixtures need the same registration and the same cleanup. One helper
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


def choose_org(client: FlaskClient, org_id: str) -> None:
    """Write the chosen organization straight into the signed session.

    Why:
        The picker posts this value, and a post needs a token. A contract test
        of the read routes checks the read routes only, so it writes the field
        and never drives the token check twice.

    Args:
        client: The test client to change.
        org_id: The organization the operator picked.
    """
    with client.session_transaction() as browser_session:
        browser_session[SELECTED_ORG_SESSION_KEY] = org_id


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


def read_rows(response: TestResponse) -> list[dict[str, Any]]:
    """Return the site rows of a site list answer.

    Args:
        response: The response that holds the rows.

    Returns:
        One record for each site.
    """
    payload: dict[str, Any] = response.get_json()
    rows: list[dict[str, Any]] = payload["sites"]
    return rows


def read_endpoints(app: Flask) -> dict[str, set[str]]:
    """Return the paths that the application binds to each endpoint name.

    Why:
        Two rules bind to one site list endpoint. A path map states that fact
        plainly, so a test reads one dictionary instead of walking the rules.

    Args:
        app: The application to read.

    Returns:
        The set of paths of each endpoint name.
    """
    found: dict[str, set[str]] = {}
    for rule in app.url_map.iter_rules():  # WHY: One pass over every registered rule.
        found.setdefault(rule.endpoint, set()).add(str(rule.rule))
    return found


def fetch_sites(client: FlaskClient, org_id: str, query: str = "") -> TestResponse:
    """Read the site list through the path that carries the organization.

    Args:
        client: The signed-in test client.
        org_id: The organization to read.
        query: The optional text filter.

    Returns:
        The response the portal built.
    """
    suffix = f"?q={query}" if query else ""  # WHY: An empty filter must send no field at all.
    return client.get(f"/api/orgs/{org_id}/sites{suffix}")


# ---------------------------------------------------------------------------
# The endpoint names and the two paths of one site list
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("endpoint", "path"),
    [
        (ORG_PAGE_ENDPOINT, ORG_PAGE_PATH),
        (CHOOSE_ORG_ENDPOINT, ORG_PAGE_PATH),
        (SITE_PAGE_ENDPOINT, SITE_PAGE_PATH),
        (INVENTORY_ENDPOINT, INVENTORY_API_PATH),
    ],
)
def test_each_selection_endpoint_carries_the_documented_path(portal_app: Flask, endpoint: str, path: str) -> None:
    """Each selection endpoint carries the path that the contract names.

    Why:
        The page templates and the browser script build every link from the
        endpoint name. A rename would break the pages with no other failure.

    Args:
        portal_app: The real application.
        endpoint: The endpoint name under test.
        path: The path the contract binds to that name.
    """
    assert read_endpoints(portal_app).get(endpoint) == {path}


def test_one_site_list_endpoint_carries_both_documented_paths(portal_app: Flask) -> None:
    """The site list endpoint carries the contract path and the task path.

    Why:
        ``contracts/http-api.md`` names ``GET /api/sites`` and ``tasks.md`` names
        ``GET /api/orgs/<org_id>/sites``. One endpoint carries both rules, so the
        two documents agree and neither path repeats a line of logic.

    Args:
        portal_app: The real application.
    """
    assert read_endpoints(portal_app).get(LIST_SITES_ENDPOINT) == {SITES_API_PATH, ORG_SITES_API_PATH}


# ---------------------------------------------------------------------------
# The session guard
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/api/sites",
        "/api/orgs/00000000-0000-0000-0000-0000000000aa/sites",
        "/api/sites/00000000-0000-0000-0000-0000000000bb/inventory",
    ],
)
def test_a_request_with_no_session_is_refused(select_client: FlaskClient, path: str) -> None:
    """Every selection read refuses a request that carries no session.

    Args:
        select_client: The test client with no session.
        path: The path under test.
    """
    response = select_client.get(path)
    assert response.status_code == 401
    assert read_error_code(response) == NOT_AUTHENTICATED_CODE


def test_the_refusal_of_a_read_names_no_operator(select_client: FlaskClient) -> None:
    """The refusal envelope of a site list read names no operator address.

    Why:
        An unauthenticated caller must learn nothing about the operators of the
        portal, so no address may reach an error body.

    Args:
        select_client: The test client with no session.
    """
    body = select_client.get(SITES_API_PATH).get_data(as_text=True)
    assert PROBE_EMAIL not in body


# ---------------------------------------------------------------------------
# The site list
# ---------------------------------------------------------------------------


def test_the_site_list_answers_the_documented_shape(signed_in_client: FlaskClient, fake_org_id: str) -> None:
    """The site list answers one ``sites`` list of five-field rows.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
    """
    response = fetch_sites(signed_in_client, fake_org_id)
    assert response.status_code == 200
    assert set(response.get_json()) == {"sites"}
    assert [set(row) for row in read_rows(response)] == [SITE_ROW_FIELDS]


def test_the_site_list_carries_the_identifier_and_the_name(
    signed_in_client: FlaskClient,
    fake_org_id: str,
    fake_site_id: str,
) -> None:
    """One site row carries the identifier and the name of the site.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
        fake_site_id: The site every canned payload uses.
    """
    row = read_rows(fetch_sites(signed_in_client, fake_org_id))[0]
    assert row["site_id"] == fake_site_id
    assert row["name"] == "Test Site"


def test_the_short_path_reads_the_organization_from_the_session(
    signed_in_client: FlaskClient,
    fake_org_id: str,
) -> None:
    """The path with no organization answers the same rows as the long path.

    Why:
        One endpoint carries both rules. This test proves that the short path
        reaches the same rows, so the contract document and the task document
        describe one behavior.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
    """
    short = signed_in_client.get(SITES_API_PATH)
    assert short.status_code == 200
    assert read_rows(short) == read_rows(fetch_sites(signed_in_client, fake_org_id))


def test_the_short_path_refuses_a_session_with_no_chosen_organization(
    select_client: FlaskClient,
    registered_owner: identity.SessionOwner,
) -> None:
    """The path with no organization refuses when the session holds no pick.

    Args:
        select_client: The test client for the wired application.
        registered_owner: The registered operator.
    """
    sign_in_client(select_client, registered_owner)
    response = select_client.get(SITES_API_PATH)
    assert response.status_code == 400
    assert read_error_code(response) == ORG_NOT_CHOSEN_CODE


def test_an_organization_outside_the_session_scope_is_refused(
    select_client: FlaskClient,
    scoped_owner: identity.SessionOwner,
    fake_org_id: str,
) -> None:
    """The site list refuses an organization that the cloud session cannot reach.

    Args:
        select_client: The test client for the wired application.
        scoped_owner: An operator whose cloud session reaches one other
            organization.
        fake_org_id: The organization every canned payload uses.
    """
    sign_in_client(select_client, scoped_owner)
    response = fetch_sites(select_client, fake_org_id)
    assert response.status_code == 403
    assert read_error_code(response) == ORG_NOT_PERMITTED_CODE


def test_the_site_list_reads_the_organization_that_the_path_named(
    signed_in_client: FlaskClient,
    fake_org_id: str,
    fake_mist_api: Any,
) -> None:
    """Every cloud read of the site list carries the chosen organization.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
        fake_mist_api: The canned cloud read surface.
    """
    fetch_sites(signed_in_client, fake_org_id)
    assert fake_mist_api.calls  # WHY: A silent route would pass every field check below.
    assert all(parameters.get("org_id") == fake_org_id for _, parameters in fake_mist_api.calls)


# ---------------------------------------------------------------------------
# The device count of one site row
# ---------------------------------------------------------------------------


def test_the_site_row_carries_the_reported_device_count(
    signed_in_client: FlaskClient,
    fake_org_id: str,
    fake_site_id: str,
    fake_mist_api: Any,
) -> None:
    """One site row carries the device count that the cloud reported.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
        fake_site_id: The site every canned payload uses.
        fake_mist_api: The canned cloud read surface.
    """
    fake_mist_api.payloads["listOrgSiteStats"] = [{"id": fake_site_id, "num_devices": 7}]
    assert read_rows(fetch_sites(signed_in_client, fake_org_id))[0]["device_count"] == 7


def test_the_device_count_sums_the_parts_when_the_whole_count_is_absent(
    signed_in_client: FlaskClient,
    fake_org_id: str,
    fake_site_id: str,
    fake_mist_api: Any,
) -> None:
    """The device count sums the device types when the cloud reports no whole count.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
        fake_site_id: The site every canned payload uses.
        fake_mist_api: The canned cloud read surface.
    """
    fake_mist_api.payloads["listOrgSiteStats"] = [{"id": fake_site_id, "num_ap": 2, "num_switch": 3, "num_gateway": 1}]
    assert read_rows(fetch_sites(signed_in_client, fake_org_id))[0]["device_count"] == 6


def test_a_site_with_no_statistics_record_reports_no_device(
    signed_in_client: FlaskClient,
    fake_org_id: str,
) -> None:
    """A site with no statistics record reports a device count of zero.

    Why:
        The canned payload holds no statistics record at all, so this test also
        proves that a missing statistics answer never raises.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
    """
    assert read_rows(fetch_sites(signed_in_client, fake_org_id))[0]["device_count"] == 0


# ---------------------------------------------------------------------------
# The site lock state of one site row
# ---------------------------------------------------------------------------


def test_a_free_site_reports_no_lock_holder(signed_in_client: FlaskClient, fake_org_id: str) -> None:
    """A site with no lock reports a null holder and the free state.

    Why:
        The lock store answered about this site and named no holder, so the row
        may state the free state as a fact.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
    """
    row = read_rows(fetch_sites(signed_in_client, fake_org_id))[0]
    assert row["locked_by"] is None
    assert row["lock_state"] == LOCK_STATE_FREE


def test_a_held_site_reports_the_address_of_the_holder(
    signed_in_client: FlaskClient,
    fake_org_id: str,
    fake_site_id: str,
    lock_reader: RecordingLockReader,
) -> None:
    """A site with a lock reports the address of the operator that holds it.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
        fake_site_id: The site every canned payload uses.
        lock_reader: The stand-in for the site lock read.
    """
    lock_reader.holders = {fake_site_id: LOCK_HOLDER_EMAIL}
    row = read_rows(fetch_sites(signed_in_client, fake_org_id))[0]
    assert row["locked_by"] == LOCK_HOLDER_EMAIL
    assert row["lock_state"] == LOCK_STATE_LOCKED


def test_reading_the_site_list_never_takes_the_site_lock(
    signed_in_client: FlaskClient,
    fake_org_id: str,
    fake_site_id: str,
    lock_reader: RecordingLockReader,
) -> None:
    """The site list asks the lock store to read and never asks it to take a lock.

    Why:
        ``contracts/site-lock.md`` states that reading data never needs the lock.
        The route reaches the lock store through a read seam only, and it asks
        that seam about the sites of one organization in one call.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
        fake_site_id: The site every canned payload uses.
        lock_reader: The stand-in for the site lock read.
    """
    fetch_sites(signed_in_client, fake_org_id)
    assert lock_reader.calls == [(fake_org_id, [fake_site_id])]


def test_an_unreachable_lock_store_still_answers_the_site_list(
    signed_in_client: FlaskClient,
    fake_org_id: str,
    lock_reader: RecordingLockReader,
) -> None:
    """The site list answers even when the lock read raises.

    Why:
        ``contracts/site-lock.md:138`` states that an unreachable lock store must
        not stop a read-only page. The page still answers, and every row states
        the unknown state rather than the free state.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
        lock_reader: The stand-in for the site lock read.
    """
    lock_reader.fails = True
    response = fetch_sites(signed_in_client, fake_org_id)
    assert response.status_code == 200
    assert read_rows(response)[0]["lock_state"] == LOCK_STATE_UNKNOWN


def test_a_lock_store_that_answers_nothing_marks_the_state_unknown(
    signed_in_client: FlaskClient,
    fake_org_id: str,
    lock_reader: RecordingLockReader,
) -> None:
    """A lock read that fails open marks every row unknown, never free.

    Why:
        A read in ``runtime/lock.py`` fails open. An unreachable store therefore
        answers an empty index and raises nothing, which is the exact path that
        the live portal takes. The row must not read as free, because an
        operator would then walk into a site that another operator holds.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
        lock_reader: The stand-in for the site lock read.
    """
    lock_reader.empty_answer = True
    row = read_rows(fetch_sites(signed_in_client, fake_org_id))[0]
    assert row["lock_state"] == LOCK_STATE_UNKNOWN
    assert row["locked_by"] is None


def test_the_unknown_lock_state_never_reads_as_the_free_state(
    signed_in_client: FlaskClient,
    fake_org_id: str,
    lock_reader: RecordingLockReader,
) -> None:
    """A dead lock store and a free site answer two different states.

    Why:
        Both cases carry a null ``locked_by``, so ``locked_by`` alone cannot tell
        them apart. This test pins the one field that can.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
        lock_reader: The stand-in for the site lock read.
    """
    free_state = read_rows(fetch_sites(signed_in_client, fake_org_id))[0]["lock_state"]
    lock_reader.empty_answer = True
    unknown_state = read_rows(fetch_sites(signed_in_client, fake_org_id))[0]["lock_state"]
    assert free_state != unknown_state


def test_the_site_page_names_the_unknown_lock_state_in_words(
    signed_in_client: FlaskClient,
    lock_reader: RecordingLockReader,
) -> None:
    """The site page states the unknown lock state in words, not in color alone.

    Why:
        WCAG 1.4.1 forbids color as the only signal. An operator who cannot tell
        the badge colors apart must still learn that the portal could not read
        the lock, so the cell carries the word and a plain sentence.

    Args:
        signed_in_client: The signed-in test client.
        lock_reader: The stand-in for the site lock read.
    """
    lock_reader.empty_answer = True
    body = signed_in_client.get(SITE_PAGE_PATH).get_data(as_text=True)
    assert "Unknown" in body
    assert "The lock store did not answer." in body


# ---------------------------------------------------------------------------
# The text filter of the site list
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("needle", ["Test", "test", "Site", "0000"])
def test_the_text_filter_keeps_a_matching_site(
    signed_in_client: FlaskClient,
    fake_org_id: str,
    needle: str,
) -> None:
    """The text filter keeps a site whose name or identifier holds the text.

    Why:
        FR-012 asks for a searchable list. The filter reads the name and the
        identifier, and it ignores the letter case.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
        needle: The text the operator typed.
    """
    assert len(read_rows(fetch_sites(signed_in_client, fake_org_id, needle))) == 1


def test_the_text_filter_drops_a_site_that_does_not_match(
    signed_in_client: FlaskClient,
    fake_org_id: str,
) -> None:
    """The text filter drops a site that holds the text in neither field.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
    """
    assert read_rows(fetch_sites(signed_in_client, fake_org_id, "no-such-site")) == []


def test_an_empty_text_filter_keeps_every_site(signed_in_client: FlaskClient, fake_org_id: str) -> None:
    """An empty text filter keeps every site.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
    """
    assert len(read_rows(signed_in_client.get(f"/api/orgs/{fake_org_id}/sites?q="))) == 1


# ---------------------------------------------------------------------------
# The site inventory
# ---------------------------------------------------------------------------


def test_the_inventory_answers_the_documented_shape(signed_in_client: FlaskClient, fake_site_id: str) -> None:
    """The inventory answers one device list and one count for each device type.

    Args:
        signed_in_client: The signed-in test client.
        fake_site_id: The site every canned payload uses.
    """
    response = signed_in_client.get(f"/api/sites/{fake_site_id}/inventory")
    assert response.status_code == 200
    payload: dict[str, Any] = response.get_json()
    assert set(payload) == {"devices", "counts"}
    assert set(payload["counts"]) == INVENTORY_COUNT_FIELDS


def test_the_inventory_counts_the_devices_of_each_type(signed_in_client: FlaskClient, fake_site_id: str) -> None:
    """The inventory counts one access point and no other device type.

    Args:
        signed_in_client: The signed-in test client.
        fake_site_id: The site every canned payload uses.
    """
    payload: dict[str, Any] = signed_in_client.get(f"/api/sites/{fake_site_id}/inventory").get_json()
    assert payload["counts"] == {"access_points": 1, "gateways": 0, "switches": 0, "devices_total": 1}
    assert len(payload["devices"]) == 1


def test_the_inventory_reads_the_site_through_the_device_seam(
    signed_in_client: FlaskClient,
    fake_org_id: str,
    fake_site_id: str,
    device_reader: RecordingDeviceReader,
) -> None:
    """The inventory asks the device module for the chosen organization and site.

    Why:
        The device read work lives in its own module. This test proves that the
        route reaches that module through the seam and passes both identifiers.

    Args:
        signed_in_client: The signed-in test client.
        fake_org_id: The organization every canned payload uses.
        fake_site_id: The site every canned payload uses.
        device_reader: The stand-in for the device read.
    """
    signed_in_client.get(f"/api/sites/{fake_site_id}/inventory")
    assert device_reader.calls == [{"org_id": fake_org_id, "site_id": fake_site_id}]


def test_the_inventory_never_sends_a_device_type_to_a_cloud_read(
    signed_in_client: FlaskClient,
    fake_site_id: str,
    fake_mist_api: Any,
) -> None:
    """No cloud read of the inventory route carries a device type parameter.

    Why:
        A device type is legal on the site-scoped device statistics call and is
        not legal on the organization-scoped device search. This route runs no
        device search at all, so no read of it may carry that parameter.

    Args:
        signed_in_client: The signed-in test client.
        fake_site_id: The site every canned payload uses.
        fake_mist_api: The canned cloud read surface.
    """
    signed_in_client.get(f"/api/sites/{fake_site_id}/inventory")
    names = [name for name, _ in fake_mist_api.calls]
    assert FORBIDDEN_ORG_DEVICE_READ not in names
    assert all(FORBIDDEN_READ_PARAMETER not in parameters for _, parameters in fake_mist_api.calls)


def test_an_unknown_site_answers_site_not_found(signed_in_client: FlaskClient) -> None:
    """The inventory refuses a site that the chosen organization does not hold.

    Args:
        signed_in_client: The signed-in test client.
    """
    response = signed_in_client.get(f"/api/sites/{ABSENT_SITE_ID}/inventory")
    assert response.status_code == 404
    assert read_error_code(response) == SITE_NOT_FOUND_CODE


def test_an_unknown_site_never_reaches_the_device_read(
    signed_in_client: FlaskClient,
    device_reader: RecordingDeviceReader,
) -> None:
    """The inventory checks the site before it reads any device.

    Why:
        A stale link and a hand-typed path both reach this route. The check runs
        first, so a site of another organization returns no device record.

    Args:
        signed_in_client: The signed-in test client.
        device_reader: The stand-in for the device read.
    """
    signed_in_client.get(f"/api/sites/{ABSENT_SITE_ID}/inventory")
    assert device_reader.calls == []


def test_the_inventory_refuses_a_session_with_no_chosen_organization(
    select_client: FlaskClient,
    registered_owner: identity.SessionOwner,
    fake_site_id: str,
) -> None:
    """The inventory refuses when the session holds no chosen organization.

    Why:
        The inventory path carries no organization, so the session must supply
        one. Without a pick the portal cannot place the site.

    Args:
        select_client: The test client for the wired application.
        registered_owner: The registered operator.
        fake_site_id: The site every canned payload uses.
    """
    sign_in_client(select_client, registered_owner)
    response = select_client.get(f"/api/sites/{fake_site_id}/inventory")
    assert response.status_code == 404
    assert read_error_code(response) == SITE_NOT_FOUND_CODE
