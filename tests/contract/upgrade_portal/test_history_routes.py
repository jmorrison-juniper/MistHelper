"""Contract tests for the three history routes of the upgrade capture portal.

Why:
    Section 6 of ``contracts/http-api.md`` fixes ``GET
    /api/sites/<site_id>/history`` and ``GET /history``. A lane
    that renames a store field or a body name would otherwise break the
    browser page in silence, so these tests pin the wire names.

    FR-032, FR-081, and FR-082 let any person read the history. Every test
    here therefore drives a client that holds no lock and types no word.

Every value below is a literal. A test that imported a name from the module
under test would agree with a rename and would prove nothing.

The run history and the history view arrive from two other lanes. The tests
that need one of those names guard the import and skip with a plain reason,
so a late arrival never hangs the suite.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.upgrade_portal.runtime import identity

# ---------------------------------------------------------------------------
# The contract values
# ---------------------------------------------------------------------------

SITE_ID = "00000000-0000-0000-0000-0000000000bb"  # Matches the shared site of the other contract tests.

HISTORY_API_PATH = f"/api/sites/{SITE_ID}/history"  # Section 6 of `contracts/http-api.md` names this path.
HISTORY_API_RULE = "/api/sites/<site_id>/history"  # The same path, as the routing table spells it.
RUN_HISTORY_API_PATH = f"/api/sites/{SITE_ID}/runs/history"  # `tasks.md` T205 asks for a run history.
RUN_HISTORY_API_RULE = "/api/sites/<site_id>/runs/history"  # The same path, as the routing table spells it.
HISTORY_PAGE_PATH = "/history"  # Section 6 of `contracts/http-api.md` names this path.

CAPTURES_FIELD = "captures"  # Section 6 of `contracts/http-api.md` names this body field.
RUNS_FIELD = "runs"  # The run history mirrors the capture history.
TOTAL_FIELD = "total"  # Section 6 of `contracts/http-api.md` names this body field.
LIMIT_FIELD = "limit"  # Section 6 of `contracts/http-api.md` names this query value.
OFFSET_FIELD = "offset"  # Section 6 of `contracts/http-api.md` names this query value.
SITE_ID_FIELD = "site_id"  # The history page carries the site as a query value.

DEFAULT_LIMIT = 25  # Section 6 of `contracts/http-api.md` sets this default.
DEFAULT_OFFSET = 0  # Section 6 of `contracts/http-api.md` sets this default.

# The six row fields that section 6 of `contracts/http-api.md` names.
# `stored_size_bytes` is there for FR-032b, which watches the growth of an
# unlimited store.
ROW_FIELDS = frozenset(
    {
        "capture_id",
        "role",
        "started_at",
        "capture_status",
        "actor_email",
        "stored_size_bytes",
    }
)

OK_STATUS = 200
NOT_AUTHENTICATED_STATUS = 401
NOT_AUTHENTICATED_CODE = "not_authenticated"

CAPTURE_LISTER_KEY = "CAPTURE_LISTER"  # The capture list seam of `app/routes/review.py`.
RUN_LISTER_KEY = "RUN_LISTER"  # The run list seam of the same module.

PROBE_EMAIL = "history.operator@example.invalid"  # A reserved domain, so no real address appears.

REVIEW_MODULE = "src.upgrade_portal.app.routes.review"
STORE_MODULE = "src.upgrade_portal.capture.store"
RENDER_MODULE = "src.upgrade_portal.compare.render"

RUN_LIST_NAMES = ("list_runs", "RunQuery", "RunListPage")  # The three names that the run history needs.
HISTORY_VIEW_NAME = "build_history_view"  # The view builder that the history page needs.


# ---------------------------------------------------------------------------
# The canned rows
# ---------------------------------------------------------------------------


def capture_row(ordinal: int) -> dict[str, Any]:
    """Return one whole capture row, as the store lists it.

    Why:
        Each test needs several rows that differ only by their key, so one
        builder keeps the rows in step and keeps every test short.

    Args:
        ordinal: The number of this row inside the history.

    Returns:
        One capture row.
    """
    return {
        "capture_id": f"cap-ab12cd34-{ordinal:02d}",
        "role": "pre" if ordinal % 2 else "post",
        "started_at": f"2026-07-{ordinal:02d}T09:00:00+00:00",
        "capture_status": "complete",
        "actor_email": PROBE_EMAIL,
        "stored_size_bytes": 1024 * ordinal,
        "site_id": SITE_ID,
        "site_name": "Test Site",
    }


def run_row(ordinal: int) -> dict[str, Any]:
    """Return one whole run row, as the store lists it.

    Args:
        ordinal: The number of this row inside the history.

    Returns:
        One run row.
    """
    return {
        "run_id": f"run-ab12cd{ordinal:02d}",
        "site_id": SITE_ID,
        "created_at": f"2026-07-{ordinal:02d}T09:00:00+00:00",
        "state": "complete",
        "actor_email": PROBE_EMAIL,
    }


@dataclass(frozen=True, slots=True)
class FakeCapturePage:
    """The capture list page that the store hands back.

    Why:
        The route reads the rows and the count off the page by name. A small
        stand-in proves that the route reads the same two names as
        ``CaptureListPage`` without a database behind it.

    Attributes:
        captures: The rows of this page.
        total: The count of the whole history.
    """

    captures: tuple[dict[str, Any], ...] = ()
    total: int = 0


@dataclass(frozen=True, slots=True)
class FakeRunPage:
    """The run list page that the store hands back.

    Attributes:
        runs: The rows of this page.
        total: The count of the whole history.
    """

    runs: tuple[dict[str, Any], ...] = ()
    total: int = 0


@dataclass
class RecordingCaptureLister:
    """A capture list seam that records every window it was asked for.

    Why:
        The two page defaults of section 6 of ``contracts/http-api.md`` live
        in the route, so the only honest proof is the window that reaches the
        store. This stand-in declares both window names, exactly as the real
        store fallback does.

    Attributes:
        rows: The whole history, newest first.
        calls: One record for each call, holding the window that arrived.
    """

    rows: list[dict[str, Any]] = field(default_factory=list)
    calls: list[dict[str, Any]] = field(default_factory=list)

    def __call__(self, site_id: str, limit: int = DEFAULT_LIMIT, offset: int = DEFAULT_OFFSET) -> FakeCapturePage:
        """Return one page of the canned history.

        Args:
            site_id: The site that the route asked for.
            limit: The page size that the route asked for.
            offset: The page start that the route asked for.

        Returns:
            The page of rows and the count of the whole history.
        """
        self.calls.append({SITE_ID_FIELD: site_id, LIMIT_FIELD: limit, OFFSET_FIELD: offset})
        return FakeCapturePage(captures=tuple(self.rows[offset : offset + limit]), total=len(self.rows))


@dataclass
class RecordingRunLister:
    """A run list seam that records every window it was asked for.

    Attributes:
        rows: The whole run history, newest first.
        calls: One record for each call, holding the window that arrived.
    """

    rows: list[dict[str, Any]] = field(default_factory=list)
    calls: list[dict[str, Any]] = field(default_factory=list)

    def __call__(self, site_id: str, limit: int = DEFAULT_LIMIT, offset: int = DEFAULT_OFFSET) -> FakeRunPage:
        """Return one page of the canned run history.

        Args:
            site_id: The site that the route asked for.
            limit: The page size that the route asked for.
            offset: The page start that the route asked for.

        Returns:
            The page of rows and the count of the whole history.
        """
        self.calls.append({SITE_ID_FIELD: site_id, LIMIT_FIELD: limit, OFFSET_FIELD: offset})
        return FakeRunPage(runs=tuple(self.rows[offset : offset + limit]), total=len(self.rows))


# ---------------------------------------------------------------------------
# The fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def capture_lister() -> RecordingCaptureLister:
    """Return the capture list seam that every test injects.

    Returns:
        The seam, holding forty canned rows.
    """
    return RecordingCaptureLister(rows=[capture_row(number) for number in range(1, 41)])


@pytest.fixture
def run_lister() -> RecordingRunLister:
    """Return the run list seam that every test injects.

    Returns:
        The seam, holding three canned rows.
    """
    return RecordingRunLister(rows=[run_row(number) for number in range(1, 4)])


@pytest.fixture
def history_app(portal_app: Flask, capture_lister: RecordingCaptureLister, run_lister: RecordingRunLister) -> Flask:
    """Return the portal with both list seams replaced.

    Why:
        The routes fall back to ``capture.store``, and that module imports the
        database driver. Injecting both seams keeps the test free of a
        database and leaves the contract as the only thing under test.

    Args:
        portal_app: The portal application.
        capture_lister: The capture list seam to inject.
        run_lister: The run list seam to inject.

    Returns:
        The wired application.
    """
    portal_app.config[CAPTURE_LISTER_KEY] = capture_lister
    portal_app.config[RUN_LISTER_KEY] = run_lister
    return portal_app


@pytest.fixture
def owner() -> Iterator[identity.SessionOwner]:
    """Register one operator for the length of one test.

    Yields:
        The identity pair of the registered operator.
    """
    owner_record = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())
    record = identity.OperatorSession(
        owner=owner_record,
        cloud_session=object(),  # A plain object states no scope, so every site passes.
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
    )
    identity.SESSION_REGISTRY.register(record)
    try:
        yield owner_record
    finally:
        identity.SESSION_REGISTRY.drop(owner_record.key)  # The registry outlives the test, so clear it here.


@pytest.fixture
def signed_in_client(history_app: Flask, owner: identity.SessionOwner) -> Iterator[FlaskClient]:
    """Return a test client that holds a session and holds no lock.

    Args:
        history_app: The wired application.
        owner: The identity pair of the registered operator.

    Yields:
        The signed-in client.
    """
    with history_app.test_client() as client:  # The context manager holds the session across requests.
        client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
        with client.session_transaction() as browser_session:
            browser_session[identity.SESSION_OWNER_KEY] = owner.key
        yield client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def read_body(response: TestResponse) -> dict[str, Any]:
    """Return the JSON body of one answer.

    Args:
        response: The answer to read.

    Returns:
        The body.
    """
    payload: Any = response.get_json()
    assert isinstance(payload, dict)
    return payload


def read_error_code(response: TestResponse) -> str:
    """Return the ``code`` field of an error envelope.

    Why:
        ``contracts/README.md`` states that a test asserts on ``code`` and
        never on ``message``.

    Args:
        response: The answer to read.

    Returns:
        The error code.
    """
    return str(read_body(response)["error"]["code"])


def read_rows(response: TestResponse, name: str) -> list[dict[str, Any]]:
    """Return the row list of one history answer.

    Args:
        response: The answer to read.
        name: The body field that holds the rows.

    Returns:
        The rows.
    """
    rows: Any = read_body(response)[name]
    assert isinstance(rows, list)
    return [row for row in rows if isinstance(row, dict)]


def bound_rules(application: Flask) -> set[str]:
    """Return every path that the routing table holds.

    Args:
        application: The portal application.

    Returns:
        The set of registered paths.
    """
    return {str(rule.rule) for rule in application.url_map.iter_rules()}


def missing_store_names() -> tuple[str, ...]:
    """Return the run list names that the capture store does not hold yet.

    Why:
        The run list arrives from a different lane. Reporting the absent names
        lets one skip message say exactly what is late.

    Returns:
        The absent names, in the order the run history needs them.
    """
    store = pytest.importorskip(STORE_MODULE, reason="The capture store needs a database driver on this host.")
    return tuple(name for name in RUN_LIST_NAMES if not hasattr(store, name))


# ---------------------------------------------------------------------------
# The capture history endpoint. Section 6 of `contracts/http-api.md`.
# ---------------------------------------------------------------------------


def test_the_history_routes_are_registered(history_app: Flask) -> None:
    """The routing table holds the two paths that the contract names.

    Why:
        A route module that fails to import is skipped with a warning, so a
        typo in a path shows as a 404 rather than as an error. This test turns
        that silence into a plain failure.

    Args:
        history_app: The wired application.
    """
    rules = bound_rules(history_app)
    assert HISTORY_API_RULE in rules, "Section 6 of `contracts/http-api.md` names the capture history endpoint."
    assert HISTORY_PAGE_PATH in rules, "Section 6 of `contracts/http-api.md` names the history page."
    assert RUN_HISTORY_API_RULE in rules, "`tasks.md` T205 asks for the run history endpoint."


def test_the_capture_history_answers_the_two_body_names(signed_in_client: FlaskClient) -> None:
    """`GET /api/sites/<site_id>/history` answers 200 with `captures` and `total`.

    Why:
        Section 6 of `contracts/http-api.md` fixes the two body names, and a browser
        page reads both of them.

    Args:
        signed_in_client: The signed-in client.
    """
    response = signed_in_client.get(HISTORY_API_PATH)

    assert response.status_code == OK_STATUS
    body = read_body(response)
    assert CAPTURES_FIELD in body, "Section 6 of `contracts/http-api.md` names the row list `captures`."
    assert body[TOTAL_FIELD] == 40, "`total` counts the whole history and never one page."


def test_each_history_row_carries_the_six_contract_fields(signed_in_client: FlaskClient) -> None:
    """Every row of the capture history carries the six named fields.

    Why:
        Section 6 of `contracts/http-api.md` names six fields, and
        `stored_size_bytes` answers FR-032b because retention is unlimited.

    Args:
        signed_in_client: The signed-in client.
    """
    rows = read_rows(signed_in_client.get(HISTORY_API_PATH), CAPTURES_FIELD)

    assert rows, "The canned history holds forty rows, so the first page is not empty."
    for row in rows:
        assert ROW_FIELDS <= set(row), f"The row {row.get('capture_id')} drops a field of the contract."


def test_a_partial_row_still_carries_every_contract_field(
    signed_in_client: FlaskClient, capture_lister: RecordingCaptureLister
) -> None:
    """A stored row that drops two fields still answers with all six names.

    Why:
        A partial capture writes fewer fields. A reader that meets a missing
        name reports a fault, so the route fills the gap with a default.

    Args:
        signed_in_client: The signed-in client.
        capture_lister: The injected capture list seam.
    """
    partial = {"capture_id": "cap-ab12cd34-99", "role": "pre", "started_at": "2026-07-01T09:00:00+00:00"}
    capture_lister.rows = [dict(partial)]

    rows = read_rows(signed_in_client.get(HISTORY_API_PATH), CAPTURES_FIELD)

    assert len(rows) == 1
    assert ROW_FIELDS <= set(rows[0]), "The route fills every absent contract name."
    assert rows[0]["stored_size_bytes"] == 0, "An unknown stored size counts as zero, never as absent."
    assert rows[0]["actor_email"] == "", "An unknown actor reads as empty, never as absent."


def test_the_capture_history_reads_the_two_page_defaults(
    signed_in_client: FlaskClient, capture_lister: RecordingCaptureLister
) -> None:
    """A request that names no window asks the store for 25 rows from row zero.

    Why:
        Section 6 of `contracts/http-api.md` sets `limit` to 25 and `offset` to 0. The
        only honest proof is the window that reaches the store.

    Args:
        signed_in_client: The signed-in client.
        capture_lister: The injected capture list seam.
    """
    response = signed_in_client.get(HISTORY_API_PATH)

    assert response.status_code == OK_STATUS
    assert capture_lister.calls == [{SITE_ID_FIELD: SITE_ID, LIMIT_FIELD: DEFAULT_LIMIT, OFFSET_FIELD: DEFAULT_OFFSET}]
    assert len(read_rows(response, CAPTURES_FIELD)) == DEFAULT_LIMIT


def test_the_capture_history_reads_the_window_of_the_query(
    signed_in_client: FlaskClient, capture_lister: RecordingCaptureLister
) -> None:
    """A request that names a window passes that window to the store.

    Args:
        signed_in_client: The signed-in client.
        capture_lister: The injected capture list seam.
    """
    response = signed_in_client.get(HISTORY_API_PATH, query_string={LIMIT_FIELD: "5", OFFSET_FIELD: "10"})

    assert response.status_code == OK_STATUS
    assert capture_lister.calls == [{SITE_ID_FIELD: SITE_ID, LIMIT_FIELD: 5, OFFSET_FIELD: 10}]
    rows = read_rows(response, CAPTURES_FIELD)
    assert len(rows) == 5
    assert rows[0]["capture_id"] == "cap-ab12cd34-11", "The eleventh row starts the page at offset ten."


def test_a_window_value_that_is_not_a_number_falls_back_to_the_default(
    signed_in_client: FlaskClient, capture_lister: RecordingCaptureLister
) -> None:
    """Text in the address bar gives the documented default rather than a fault.

    Why:
        Any person can edit a query value. FR-032 lets that person read the
        history, so a bad value must never answer with a server error.

    Args:
        signed_in_client: The signed-in client.
        capture_lister: The injected capture list seam.
    """
    response = signed_in_client.get(HISTORY_API_PATH, query_string={LIMIT_FIELD: "many", OFFSET_FIELD: "-4"})

    assert response.status_code == OK_STATUS
    assert capture_lister.calls == [{SITE_ID_FIELD: SITE_ID, LIMIT_FIELD: DEFAULT_LIMIT, OFFSET_FIELD: DEFAULT_OFFSET}]


def test_a_very_large_page_size_is_held_inside_a_bound(
    signed_in_client: FlaskClient, capture_lister: RecordingCaptureLister
) -> None:
    """A huge page size answers 200 and reads a bounded page.

    Why:
        FR-032 keeps every capture set for an unlimited period, so one site
        can hold thousands of rows. An unbounded page size would let one
        request read the whole store in one answer.

    Args:
        signed_in_client: The signed-in client.
        capture_lister: The injected capture list seam.
    """
    response = signed_in_client.get(HISTORY_API_PATH, query_string={LIMIT_FIELD: "100000"})

    assert response.status_code == OK_STATUS
    assert capture_lister.calls[0][LIMIT_FIELD] < 100000, "The route holds the page size inside a bound."


def test_the_capture_history_needs_a_session(history_app: Flask) -> None:
    """A client with no session reads 401 `not_authenticated`.

    Why:
        FR-032 removes the lock and the typed word from a read. It does not
        remove the sign-in, because the portal reads the cloud on behalf of
        one named operator.

    Args:
        history_app: The wired application.
    """
    with history_app.test_client() as client:
        response = client.get(HISTORY_API_PATH)

    assert response.status_code == NOT_AUTHENTICATED_STATUS
    assert read_error_code(response) == NOT_AUTHENTICATED_CODE


def test_the_capture_history_asks_for_no_typed_word(signed_in_client: FlaskClient) -> None:
    """A read answers 200 with no `confirm` value and with no lock token.

    Why:
        FR-032, FR-081, and FR-082 state that a person reads the record
        freely. A read that answered 400 `confirmation_required` or 409
        `site_locked` would hide the record from the operator who most needs
        it, which is the operator watching somebody else's upgrade.

    Args:
        signed_in_client: The signed-in client.
    """
    response = signed_in_client.get(HISTORY_API_PATH)

    assert response.status_code == OK_STATUS, "A history read carries no word and no lock token."


# ---------------------------------------------------------------------------
# The run history endpoint. `tasks.md` T205.
# ---------------------------------------------------------------------------


def test_the_run_history_answers_the_rows_and_the_total(
    signed_in_client: FlaskClient, run_lister: RecordingRunLister
) -> None:
    """The run history answers 200 with `runs` and `total`.

    Why:
        The run history mirrors the capture history, so one browser page reads
        both lists the same way.

    Args:
        signed_in_client: The signed-in client.
        run_lister: The injected run list seam.
    """
    response = signed_in_client.get(RUN_HISTORY_API_PATH)

    assert response.status_code == OK_STATUS
    body = read_body(response)
    assert body[TOTAL_FIELD] == 3
    assert [row["run_id"] for row in read_rows(response, RUNS_FIELD)] == [
        "run-ab12cd01",
        "run-ab12cd02",
        "run-ab12cd03",
    ]
    assert run_lister.calls == [{SITE_ID_FIELD: SITE_ID, LIMIT_FIELD: DEFAULT_LIMIT, OFFSET_FIELD: DEFAULT_OFFSET}]


def test_the_run_history_reads_the_window_of_the_query(
    signed_in_client: FlaskClient, run_lister: RecordingRunLister
) -> None:
    """The run history passes the window of the query to the store.

    Args:
        signed_in_client: The signed-in client.
        run_lister: The injected run list seam.
    """
    response = signed_in_client.get(RUN_HISTORY_API_PATH, query_string={LIMIT_FIELD: "2", OFFSET_FIELD: "1"})

    assert response.status_code == OK_STATUS
    assert run_lister.calls == [{SITE_ID_FIELD: SITE_ID, LIMIT_FIELD: 2, OFFSET_FIELD: 1}]


def test_the_run_history_needs_a_session(history_app: Flask) -> None:
    """A client with no session reads 401 `not_authenticated` from the run history.

    Args:
        history_app: The wired application.
    """
    with history_app.test_client() as client:
        response = client.get(RUN_HISTORY_API_PATH)

    assert response.status_code == NOT_AUTHENTICATED_STATUS
    assert read_error_code(response) == NOT_AUTHENTICATED_CODE


def test_the_capture_store_offers_the_three_run_list_names() -> None:
    """The capture store holds `list_runs`, `RunQuery`, and `RunListPage`.

    Why:
        The route falls back to those three names when no seam is injected. A
        running portal has no seam, so an absent name would answer with an
        empty run history and would say nothing about the fault.

        The store lane may land after this lane, so an absent name skips with
        a plain reason rather than failing the suite.
    """
    absent = missing_store_names()
    if absent:  # `pytest.skip` raises `Skipped`, which is not an `Exception`.
        pytest.skip(f"The capture store does not hold {', '.join(absent)} yet, so the store fallback is not wired.")

    store = pytest.importorskip(STORE_MODULE, reason="The capture store needs a database driver on this host.")
    query = store.RunQuery(site_id=SITE_ID, limit=DEFAULT_LIMIT, offset=DEFAULT_OFFSET)
    assert query.site_id == SITE_ID, "`RunQuery` carries the site, as `CaptureQuery` does."
    assert hasattr(store.RunListPage, "__dataclass_fields__"), "`RunListPage` is the page record of the run list."


# ---------------------------------------------------------------------------
# The history page. Section 6 of `contracts/http-api.md`.
# ---------------------------------------------------------------------------


def test_the_history_page_renders_for_one_site(signed_in_client: FlaskClient) -> None:
    """`GET /history` answers 200 for one site.

    Why:
        Section 6 of `contracts/http-api.md` asks for the human view of the same list.
        The site travels as a query value, because one page serves one site
        and the whole organization.

    Args:
        signed_in_client: The signed-in client.
    """
    response = signed_in_client.get(HISTORY_PAGE_PATH, query_string={SITE_ID_FIELD: SITE_ID})

    assert response.status_code == OK_STATUS


def test_the_history_page_reads_the_whole_organization(
    signed_in_client: FlaskClient, capture_lister: RecordingCaptureLister
) -> None:
    """`GET /history` with no site reads every site.

    Why:
        Section 6 of `contracts/http-api.md` states that the page serves one site or
        the organization, so an absent site must not narrow the read.

    Args:
        signed_in_client: The signed-in client.
        capture_lister: The injected capture list seam.
    """
    response = signed_in_client.get(HISTORY_PAGE_PATH)

    assert response.status_code == OK_STATUS
    assert capture_lister.calls[0][SITE_ID_FIELD] == "", "An absent site reads every site."


def test_the_history_page_needs_a_session(history_app: Flask) -> None:
    """A client with no session cannot reach the history page.

    Args:
        history_app: The wired application.
    """
    with history_app.test_client() as client:
        response = client.get(HISTORY_PAGE_PATH)

    assert response.status_code != OK_STATUS, "The page guard runs before the store read."


# ---------------------------------------------------------------------------
# The page window. `tasks.md` T206.
# ---------------------------------------------------------------------------


def review_module() -> Any:
    """Return the review route module.

    Returns:
        The module under test.
    """
    return pytest.importorskip(REVIEW_MODULE, reason="The review routes need Flask on this host.")


def test_the_first_page_offers_a_later_page_and_no_earlier_page() -> None:
    """The first window holds a next address and an empty previous address.

    Why:
        Task T206 asks for the next page and the earlier page. An empty
        address states plainly that the page does not exist, so the template
        hides that control and never offers a dead link.
    """
    review = review_module()

    window = review.build_window(SITE_ID, DEFAULT_LIMIT, DEFAULT_OFFSET, 40)

    assert window.previous_href == "", "No page sits before the first page."
    assert f"{OFFSET_FIELD}=25" in window.next_href, "The next page starts one page later."
    assert f"{SITE_ID_FIELD}={SITE_ID}" in window.next_href, "The next page stays on the same site."


def test_the_last_page_offers_an_earlier_page_and_no_later_page() -> None:
    """The last window holds a previous address and an empty next address."""
    review = review_module()

    window = review.build_window(SITE_ID, DEFAULT_LIMIT, 25, 40)

    assert window.next_href == "", "No page sits after the last page."
    assert f"{OFFSET_FIELD}=0" in window.previous_href, "The earlier page steps back by one page size."


def test_a_history_of_one_page_offers_no_neighbor_at_all() -> None:
    """A history that fits on one page offers neither neighbor."""
    review = review_module()

    window = review.build_window(SITE_ID, DEFAULT_LIMIT, DEFAULT_OFFSET, 3)

    assert window.previous_href == ""
    assert window.next_href == ""
    assert window.total == 3


def test_the_window_of_the_whole_organization_carries_no_site() -> None:
    """A window with no site leaves the site out of both addresses.

    Why:
        The page serves the whole organization as well as one site. An empty
        `site_id` in the address would narrow the next page to no site at all.
    """
    review = review_module()

    window = review.build_window("", DEFAULT_LIMIT, DEFAULT_OFFSET, 40)

    assert SITE_ID_FIELD not in window.next_href, "An organization wide history carries no site."


# ---------------------------------------------------------------------------
# The history view. `tasks.md` T208 and T209.
# ---------------------------------------------------------------------------


def test_the_history_row_reads_the_two_counts_from_the_stored_map(
    signed_in_client: FlaskClient, capture_lister: RecordingCaptureLister
) -> None:
    """A row with a `counts` map answers a real device count and client count.

    Why:
        A history of an upgrade must show how many devices and how many
        clients the site held. The store writes those numbers into the
        `counts` map of the capture, so the row reads them there and costs no
        second read.

    Args:
        signed_in_client: The signed-in client.
        capture_lister: The injected capture list seam.
    """
    row = capture_row(1)
    row["counts"] = {"devices_total": 120, "clients_wired": 40, "clients_wireless": 800, "clients_guest": 12}
    capture_lister.rows = [row]

    rows = read_rows(signed_in_client.get(HISTORY_API_PATH), CAPTURES_FIELD)

    assert rows[0]["device_count"] == 120
    assert rows[0]["client_count"] == 852, "The client count adds the wired group, the wireless group, and the guests."


def test_a_row_with_no_counts_answers_zero_for_both(signed_in_client: FlaskClient) -> None:
    """A row that carries no counts answers zero rather than dropping the name.

    Args:
        signed_in_client: The signed-in client.
    """
    rows = read_rows(signed_in_client.get(HISTORY_API_PATH), CAPTURES_FIELD)

    assert rows[0]["device_count"] == 0
    assert rows[0]["client_count"] == 0


def test_the_capture_store_projects_the_counts_map() -> None:
    """The store history projection reaches the `counts` map.

    Why:
        The page reads the two counts off the row. A projection that dropped
        `counts` would show a zero against every real capture, and the column
        would say the site held no device at all.
    """
    store = pytest.importorskip(STORE_MODULE, reason="The capture store needs a database driver on this host.")

    assert "counts" in store.LIST_FIELDS, "The history projection reaches the stored counts map."


def test_a_capture_of_a_later_release_reads_as_a_conflict() -> None:
    """The refusal table maps `schema_version_too_new` to 409 with its own code.

    Why:
        Section 6 of `contracts/http-api.md` fixes the status and the code. The
        store gate refuses a record that a later release wrote, and that
        refusal is a condition the operator can cure by upgrading the portal.
        An unmapped reason would answer 500 and would read as a server fault.
    """
    review = review_module()
    store = pytest.importorskip(STORE_MODULE, reason="The capture store needs a database driver on this host.")

    refusal = review.refuse(store.REASON_SCHEMA_TOO_NEW, "cap-ab12cd34-01", {"schema_version": 2})

    assert refusal.status == 409, "Section 6 of `contracts/http-api.md` answers 409 for a record of a later release."
    assert refusal.code == "schema_version_too_new", "The bare word `conflict` cannot name this fault."


def test_the_compare_package_offers_the_history_view_builder() -> None:
    """`compare.render` holds `build_history_view`, and the page calls it.

    Why:
        The view builder owns the columns and the stored size of FR-032b. The
        page falls back to the plain rows when the builder is absent, so this
        test is the only thing that reports the absence.

        The view lane may land after this lane, so an absent builder skips
        with a plain reason rather than failing the suite.
    """
    render = pytest.importorskip(RENDER_MODULE, reason="The compare render module is not importable on this host.")
    if not hasattr(render, HISTORY_VIEW_NAME):  # `pytest.skip` raises `Skipped`, which is not an `Exception`.
        pytest.skip(f"`compare.render` does not hold `{HISTORY_VIEW_NAME}` yet, so the page shows the plain rows.")

    rows: Sequence[Mapping[str, Any]] = [capture_row(1)]
    view = getattr(render, HISTORY_VIEW_NAME)(list(rows))

    assert view is not None, "The builder answers a view for one row."
