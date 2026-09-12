"""Unit tests for the schema version reader and the run history query of the store.

Why:
    US6 of `specs/1823-upgrade-capture-portal/tasks.md` lines 426 to 429 asks
    for two things at once. A capture written by an older schema version still
    opens, and a capture written by a later schema version earns a plain
    sentence that names the true cause. A single mismatch reason cannot say
    both, so the store carries a reason of its own for the later version.

    The run history is the second half. A history page that raises would hide
    the whole run page, so every failure here returns an empty page instead.

    Every test asserts on a ``REASON_`` constant or on a field name, never on
    the message text. A message may change for Simplified Technical English at
    any time, and the reason code stays stable.

    No test opens a socket, a database connection, or a file. The fake handle
    below holds every answer in memory.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

import pytest

from src.upgrade_portal.capture import store
from src.upgrade_portal.runtime.runs import RunRecordBuilder

_KEY = "cap-0001"  # WHY: One capture key serves every load test in this module.
_SITE = "site-0001"  # WHY: One site narrows every history page in this module.
_EMAIL = "operator@example.test"  # WHY: A reserved test domain, so no live address appears.

# WHY: The four names of the task brief that the run writer does not store. The
# guardrail below proves that no row of this store carries one of them. The run
# holds `created_at` and `updated_at` in place of the first two, holds `state`
# in place of the third, and names no device family at all, because a family
# belongs to one entry of `targets` and a run may carry more than one family.
_ABSENT_RUN_FIELDS = ("started_at", "finished_at", "run_state", "device_family")


class _FakeCollection:
    """One collection of a fake document store.

    Why:
        The capture read calls ``collection(name).get(key)``. A test owns that
        one call, so it returns a document or returns nothing. A unit test runs
        with no container and no network.
    """

    def __init__(self, document: dict[str, Any] | None) -> None:
        """Create a collection that holds one document, or holds nothing.

        Args:
            document: The stored document, or None for an empty collection.
        """
        self.document = document  # WHY: The single answer of every read.

    def get(self, key: str) -> dict[str, Any] | None:
        """Return the stored document.

        Args:
            key: The document key. The fake holds one document, so it ignores this value.

        Returns:
            The stored document, or None when the collection is empty.
        """
        return dict(self.document) if self.document is not None else None


class _FakeAql:
    """The query seam of a fake database handle.

    Why:
        A history page runs a count query and then a page query. The fake hands
        back one canned answer for each call in order, and it records every
        query text and every bind value. A test then proves that a narrowing
        value travels as a bind parameter and never as query text.
    """

    def __init__(self) -> None:
        """Create a query seam that answers with nothing."""
        self.calls: list[tuple[str, dict[str, Any]]] = []  # WHY: Records each query and its binds.
        self.answers: list[list[Any]] = []  # WHY: One canned answer for each call, in order.
        self.execute_error: Exception | None = None  # WHY: A test sets this value to fail the query.

    def execute(self, query: str, bind_vars: Mapping[str, Any] | None = None) -> list[Any]:
        """Return the next canned answer.

        Args:
            query: The query text.
            bind_vars: The bind values.

        Returns:
            The next canned answer, or an empty list when none is left.

        Raises:
            Exception: The error that a test placed in ``execute_error``.
        """
        self.calls.append((query, dict(bind_vars or {})))
        if self.execute_error is not None:
            raise self.execute_error
        return self.answers.pop(0) if self.answers else []


class _FakeDatabase:
    """A fake database handle that answers a read and a query.

    Why:
        The store asks the handle for a collection by name and runs a query
        through ``aql``. One fake covers both seams, so a schema test and a
        history test share the same handle.
    """

    def __init__(self, document: dict[str, Any] | None = None) -> None:
        """Create a handle that holds one document.

        Args:
            document: The document that every collection read returns.
        """
        self.fake_collection = _FakeCollection(document)  # WHY: Every name maps to this single store.
        self.aql = _FakeAql()  # WHY: The seam that the history queries run through.

    def collection(self, name: str) -> _FakeCollection:
        """Return the single fake collection.

        Args:
            name: The collection name.

        Returns:
            The fake collection.
        """
        return self.fake_collection


@pytest.fixture(autouse=True)
def _drop_cached_handle() -> Iterator[None]:
    """Clear the cached database handle around every test.

    Why:
        The store caches one shared handle. A leaked handle makes a later test
        read a store that another test built, so each test starts and ends with
        an empty cache.

    Yields:
        None, after the cache is clear.
    """
    store.reset_connection()
    yield
    store.reset_connection()


def _capture(version: Any) -> dict[str, Any]:
    """Return a verified capture that carries one schema version.

    Why:
        The schema gate must run before the state gate, so every capture here
        already holds the verified state. A refusal then comes from the version
        alone and never from the state.

    Args:
        version: The value to place under ``schema_version``.

    Returns:
        A stored capture document.
    """
    state = {store.CAPTURE_STATE_FIELD: store.CaptureState.VERIFIED.value}
    return {"capture_id": _KEY, "schema_version": version, "site_id": _SITE, **state}


# ---------------------------------------------------------------------------
# T207: the schema version reader
# ---------------------------------------------------------------------------


def test_is_readable_schema_version_accepts_this_version_and_every_version_before_it() -> None:
    """A reader understands its own version and every version below it.

    Why:
        A strict equality against ``SCHEMA_VERSION`` refuses an older record as
        well as a later one. US6 asks for the older record to open, so the rule
        is ``stored <= SCHEMA_VERSION``.
    """
    assert store.is_readable_schema_version(store.SCHEMA_VERSION) is True
    assert store.is_readable_schema_version(store.SCHEMA_VERSION - 1) is True
    assert store.is_readable_schema_version(0) is True
    assert store.is_readable_schema_version(store.SCHEMA_VERSION + 1) is False


def test_is_readable_schema_version_refuses_a_value_that_is_no_integer() -> None:
    """A boolean is not a schema version, and neither is a string.

    Why:
        Python makes ``bool`` a subclass of ``int``, so ``isinstance(True, int)``
        is True and a bare integer test would accept ``True`` as the version 1.
        The reader therefore refuses a boolean before it compares the number.
    """
    assert store.is_readable_schema_version(True) is False
    assert store.is_readable_schema_version(False) is False
    assert store.is_readable_schema_version("1") is False
    assert store.is_readable_schema_version(None) is False


def test_schema_version_refusal_opens_an_older_record() -> None:
    """A record written by an older schema version renders."""
    assert store.schema_version_refusal(_capture(store.SCHEMA_VERSION - 1)) == store.REASON_VERIFIED


def test_schema_version_refusal_opens_the_current_record() -> None:
    """A record written by this release renders."""
    assert store.schema_version_refusal(_capture(store.SCHEMA_VERSION)) == store.REASON_VERIFIED


def test_schema_version_refusal_names_a_later_version_with_its_own_reason() -> None:
    """A record written by a later schema version earns a reason of its own.

    Why:
        A shared mismatch reason would send an operator to hunt a corrupt write
        that never happened. The distinct reason lets a route show a plain
        sentence about the version instead.
    """
    refusal = store.schema_version_refusal(_capture(store.SCHEMA_VERSION + 1))
    assert refusal == store.REASON_SCHEMA_TOO_NEW
    assert refusal != store.REASON_SCHEMA
    assert refusal != store.REASON_BAD_SCHEMA


def test_schema_version_refusal_separates_a_bad_value_from_a_later_version() -> None:
    """A value that is no integer is a bad version and never a later version.

    Why:
        A string or a boolean under ``schema_version`` names no release at all.
        A ``too new`` answer for such a value would state a cause that is not
        true.
    """
    assert store.schema_version_refusal(_capture("2")) == store.REASON_BAD_SCHEMA
    assert store.schema_version_refusal(_capture(True)) == store.REASON_BAD_SCHEMA
    assert store.schema_version_refusal({"capture_id": _KEY}) == store.REASON_BAD_SCHEMA


def test_load_capture_opens_a_record_of_an_older_schema_version() -> None:
    """The store hands out a capture that an older release wrote.

    Why:
        The first half of the US6 independent test. No capture disappears with
        age, so an older record still opens and still joins a comparison.
    """
    loaded = store.load_capture(_KEY, _FakeDatabase(_capture(store.SCHEMA_VERSION - 1)))
    assert loaded.capture is not None
    assert loaded.comparable is True
    assert loaded.reason == store.REASON_VERIFIED


def test_load_capture_refuses_a_record_of_a_later_schema_version() -> None:
    """The store refuses a capture that a later release wrote, and says which cause.

    Why:
        The second half of the US6 independent test. The record travels with
        the refusal, so a page can still show the version it found and can name
        the cure.
    """
    loaded = store.load_capture(_KEY, _FakeDatabase(_capture(store.SCHEMA_VERSION + 1)))
    assert loaded.comparable is False
    assert loaded.reason == store.REASON_SCHEMA_TOO_NEW
    assert loaded.capture is not None
    assert loaded.capture["schema_version"] == store.SCHEMA_VERSION + 1


def test_load_capture_for_comparison_withholds_a_record_of_a_later_schema_version() -> None:
    """A capture this release cannot read joins no comparison.

    Why:
        A comparison of a record that the reader does not understand would
        print a difference that is a gap in the reader and not a change at the
        site.
    """
    loaded = store.load_capture_for_comparison(_KEY, _FakeDatabase(_capture(store.SCHEMA_VERSION + 1)))
    assert loaded.capture is None
    assert loaded.comparable is False
    assert loaded.reason == store.REASON_SCHEMA_TOO_NEW


def test_the_later_version_refusal_carries_a_plain_sentence_of_its_own() -> None:
    """The later version reason reads as a sentence and names no backup file.

    Why:
        US6 asks the page to say plainly that the version is too new. The
        record is present, so a sentence about a backup file under ``data/``
        would point the operator at the wrong place.
    """
    sentence = store._MESSAGES[store.REASON_SCHEMA_TOO_NEW]
    assert sentence != store._MESSAGES[store.REASON_SCHEMA]
    assert "data/" not in sentence
    assert sentence.isascii()


# ---------------------------------------------------------------------------
# T205: the run history query
# ---------------------------------------------------------------------------


def test_the_run_row_names_only_fields_that_the_run_writer_stores() -> None:
    """Every field of the run row is a field of the stored run document.

    Why:
        A projection that names a field the writer never stores returns null
        for every row, and the history table then shows an empty column that
        nobody can explain. The required field list of the builder is the
        record of what the writer truly stores.
    """
    stored_fields = set(RunRecordBuilder.REQUIRED_FIELDS)
    assert set(store.RUN_LIST_FIELDS) <= stored_fields
    for name in _ABSENT_RUN_FIELDS:
        assert name not in stored_fields
        assert name not in store.RUN_LIST_FIELDS


def test_the_run_row_carries_the_identifiers_of_the_history_view() -> None:
    """The run row names the run, the site, the times, the state, and both captures.

    Why:
        A history row without the two capture identifiers cannot link to a
        comparison, and the operator would have to search for the pair by hand.
    """
    wanted = ("run_id", "site_id", "site_name", "created_at", "updated_at", "state")
    assert set(wanted) <= set(store.RUN_LIST_FIELDS)
    assert "pre_capture_id" in store.RUN_LIST_FIELDS
    assert "post_capture_id" in store.RUN_LIST_FIELDS


def test_list_runs_returns_the_rows_and_the_total() -> None:
    """A page carries its rows and the total number of runs behind it."""
    database = _FakeDatabase()
    rows = [{"run_id": "run-0001", "state": "complete"}, {"run_id": "run-0002", "state": "failed"}]
    database.aql.answers = [[9], rows]
    page = store.list_runs(store.RunQuery(site_id=_SITE, limit=2), database)
    assert page.total == 9
    assert page.limit == 2
    assert page.database_available is True
    assert [row["run_id"] for row in page.runs] == ["run-0001", "run-0002"]


def test_list_runs_sends_every_narrowing_value_as_a_bind() -> None:
    """A narrowing value travels as a bind parameter and never as query text.

    Why:
        A site identifier and an operator email come from a request. A value
        inside the query text would let that request write the query, so every
        value travels as a bind and every name comes from a fixed tuple.
    """
    database = _FakeDatabase()
    database.aql.answers = [[0], []]
    store.list_runs(store.RunQuery(site_id=_SITE, actor_email=_EMAIL), database)
    count_query, count_binds = database.aql.calls[0]
    page_query, page_binds = database.aql.calls[1]
    assert count_binds == {"site_id": _SITE, "actor_email": _EMAIL}
    assert page_binds == {"site_id": _SITE, "actor_email": _EMAIL, "offset": 0, "limit": 25}
    assert _SITE not in count_query
    assert _EMAIL not in page_query
    assert "FILTER doc.org_id" not in page_query


def test_list_runs_reads_the_run_collection_and_sorts_by_the_indexed_time() -> None:
    """The page reads the run collection and sorts by the field of the site index.

    Why:
        The run history index of `data-model.md` line 396 is ``site_id`` and
        ``created_at``. A sort on any other field would read every run of the
        site and then sort the whole set in memory.
    """
    database = _FakeDatabase()
    database.aql.answers = [[0], []]
    store.list_runs(store.RunQuery(site_id=_SITE), database)
    page_query = database.aql.calls[1][0]
    assert "FOR doc IN " + store.RUN_COLLECTION in page_query
    assert "SORT doc.created_at DESC" in page_query
    assert store.CAPTURE_COLLECTION not in page_query


def test_list_runs_reads_every_site_when_the_caller_narrows_nothing() -> None:
    """A query that names no site reads every run and binds nothing."""
    database = _FakeDatabase()
    database.aql.answers = [[4], []]
    page = store.list_runs(store.RunQuery(), database)
    count_query, count_binds = database.aql.calls[0]
    assert count_binds == {}
    assert "FILTER" not in count_query
    assert page.total == 4
    assert page.limit == store.DEFAULT_LIST_LIMIT


def test_list_runs_reports_the_database_out_of_reach(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty page states that the database never answered.

    Why:
        An empty history that reads as a fact would tell the operator that the
        site holds no run. The flag separates a silent outage from a site that
        never ran an upgrade.
    """
    monkeypatch.setattr(store, "connect_database", lambda: None)
    page = store.list_runs(store.RunQuery(site_id=_SITE))
    assert page.runs == ()
    assert page.total == 0
    assert page.database_available is False


def test_list_runs_returns_an_empty_page_when_the_query_fails() -> None:
    """A failed query returns an empty page and raises nothing.

    Why:
        A history page that raises would hide the whole run page. An empty page
        keeps the rest of the view alive.
    """
    database = _FakeDatabase()
    database.aql.execute_error = RuntimeError("The query failed.")
    page = store.list_runs(store.RunQuery(site_id=_SITE), database)
    assert page.runs == ()
    assert page.total == 0
    assert page.database_available is True


def test_list_runs_keeps_the_page_bounds_of_the_request() -> None:
    """The page reports the bounds the caller asked for, so a route can build the next link.

    Why:
        The next page control and the previous page control need the offset
        that produced the rows. A page that reported the clamped value would
        move the operator to the wrong window.
    """
    database = _FakeDatabase()
    database.aql.answers = [[100], []]
    page = store.list_runs(store.RunQuery(site_id=_SITE, limit=10, offset=20), database)
    assert page.limit == 10
    assert page.offset == 20
    assert database.aql.calls[1][1]["offset"] == 20
    assert database.aql.calls[1][1]["limit"] == 10


def test_list_runs_refuses_a_page_of_no_rows_at_all() -> None:
    """A limit below one still asks the database for one row.

    Why:
        A ``LIMIT @offset, 0`` returns nothing for every page, and the operator
        would read an empty history for a site that holds many runs.
    """
    database = _FakeDatabase()
    database.aql.answers = [[3], []]
    store.list_runs(store.RunQuery(site_id=_SITE, limit=0, offset=-5), database)
    page_binds = database.aql.calls[1][1]
    assert page_binds["limit"] == 1
    assert page_binds["offset"] == 0
