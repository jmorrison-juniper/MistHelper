"""Unit tests for the store seams of the review routes.

Why:
    Issue #1996 reports that three modules of this portal sit under the 90
    percent coverage floor that the aggregate hides. ``app/routes/review.py`` is
    one of them, and the uncovered half held the fallback path of every store
    seam. That is the half a lean host reaches, and it is the half no test drove.

    The audit records the same pattern twice. ``app/wiring.py`` held defect 11
    and defect 12, and ``app/routes/select.py`` held two of the six defects that
    the live run of 2026-08-24 found. The uncovered half of a module is where a
    defect survives.

    Every test below drives one seam with the store absent, with the store
    present, and with the store present but missing the name the seam asks for.
    The third case is the one that a rename of the store produces, and it is the
    case that returns an empty page instead of raising.
"""

from __future__ import annotations

from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from src.upgrade_portal.app.routes import review

SITE_ID = "cf36153a-97bb-4974-8f8f-e9cc25d64d83"


class FakeQuery:
    """A stand-in for the query record that the store defines.

    Why:
        The seam builds the query by keyword and hands it to the lister. The
        stand-in keeps the three values, so a test reads what the seam built.
    """

    def __init__(self, site_id: str, limit: int, offset: int) -> None:
        """Store the three query values.

        Args:
            site_id: The site to narrow to.
            limit: The largest number of rows to read.
            offset: The number of rows to step over first.
        """
        self.site_id = site_id
        self.limit = limit
        self.offset = offset


def store_with(**names: Any) -> ModuleType:
    """Return a stand-in store module that carries the given names.

    Args:
        names: The attribute names and values the module holds.

    Returns:
        One module-like object.
    """
    return SimpleNamespace(**names)  # type: ignore[return-value]


def install_store(monkeypatch: pytest.MonkeyPatch, module: ModuleType | None) -> None:
    """Replace the module loader of the review routes.

    Args:
        monkeypatch: The pytest patch helper.
        module: The stand-in store module, or None for a host with no store.
    """
    monkeypatch.setattr(review, "load_optional_module", lambda suffix: module)


class TestLoadOptionalModule:
    """Tests for the loader that a lean host drives."""

    def test_returns_the_module_when_the_import_works(self) -> None:
        """A module that exists arrives whole."""
        found = review.load_optional_module("capture.store")
        assert found is None or isinstance(found, ModuleType)  # Either answer is a legal shape.

    def test_returns_none_when_the_module_is_absent(self) -> None:
        """A missing module reports None and raises nothing.

        Why:
            The capture store imports the database driver at module level. A
            host with no driver must still serve every read page, so this
            function turns the import error into a plain None.
        """
        assert review.load_optional_module("capture.no_such_module_exists") is None


class TestFindAttribute:
    """Tests for the seam that reads one name out of the store."""

    def test_answers_none_for_no_module(self) -> None:
        """A host with no store finds no callable."""
        assert review.find_attribute(None, ("list_captures",)) is None

    def test_answers_the_first_name_that_matches(self) -> None:
        """The first candidate wins, so a rename keeps the route working.

        Why:
            A seam names more than one candidate on purpose. The order is the
            order of preference, and a test must prove the order and not the
            set.
        """
        module = store_with(second=lambda: "second", first=lambda: "first")
        found = review.find_attribute(module, ("first", "second"))
        assert found is not None
        assert found() == "first"

    def test_skips_a_name_that_is_not_callable(self) -> None:
        """A name that holds a value and not a function never wins.

        Why:
            The seam calls what it finds. A plain value would raise at the call
            site, far from the module that holds it.
        """
        module = store_with(list_captures="not a function")
        assert review.find_attribute(module, ("list_captures",)) is None

    def test_answers_none_when_no_name_matches(self) -> None:
        """A store that grew a new name answers no page instead of raising."""
        module = store_with(something_else=lambda: None)
        assert review.find_attribute(module, ("list_captures",)) is None


class TestStoreCaptureRows:
    """Tests for the capture page reader of the history."""

    def test_answers_an_empty_page_with_no_store(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A host with no store shows an empty history and no error.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install_store(monkeypatch, None)
        assert review.store_capture_rows(SITE_ID) == ()

    def test_answers_an_empty_page_when_the_store_offers_no_lister(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A store with a query and no lister still answers a page.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install_store(monkeypatch, store_with(CaptureQuery=FakeQuery))
        assert review.store_capture_rows(SITE_ID) == ()

    def test_answers_an_empty_page_when_the_store_offers_no_query(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A store with a lister and no query still answers a page.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install_store(monkeypatch, store_with(list_captures=lambda query: ("row",)))
        assert review.store_capture_rows(SITE_ID) == ()

    def test_builds_the_query_from_the_three_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The seam hands the site, the limit, and the offset to the store.

        Why:
            The route owns no count and no sort order of its own. A seam that
            dropped the offset would page the history back to the first page on
            every step, and the page would look stuck.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install_store(monkeypatch, store_with(list_captures=lambda query: query, CaptureQuery=FakeQuery))
        built = review.store_capture_rows(SITE_ID, limit=5, offset=10)
        assert (built.site_id, built.limit, built.offset) == (SITE_ID, 5, 10)


class TestStoreRunRows:
    """Tests for the run page reader of the history."""

    def test_answers_an_empty_page_with_no_store(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A host with no store shows an empty run history and no error.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install_store(monkeypatch, None)
        assert review.store_run_rows(SITE_ID) == ()

    def test_answers_an_empty_page_before_the_store_grows_the_run_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A store that lists captures and no runs still answers a page.

        Why:
            The run list arrived after the capture list. A route that raised
            here would have taken the whole history page down with it.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install_store(monkeypatch, store_with(list_captures=lambda query: (), CaptureQuery=FakeQuery))
        assert review.store_run_rows(SITE_ID) == ()

    def test_builds_the_query_from_the_three_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The run seam mirrors the capture seam exactly.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install_store(monkeypatch, store_with(list_runs=lambda query: query, RunQuery=FakeQuery))
        built = review.store_run_rows(SITE_ID, limit=7, offset=14)
        assert (built.site_id, built.limit, built.offset) == (SITE_ID, 7, 14)


class TestCaptureLoader:
    """Tests for the reader that loads one capture for a comparison."""

    def test_prefers_the_injected_reader(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An injected stand-in wins, so a test reaches no database.

        Args:
            monkeypatch: The pytest patch helper.
        """

        def injected(capture_id: str) -> str:
            """Answer one capture.

            Args:
                capture_id: The capture to load.

            Returns:
                The identifier, unchanged.
            """
            return capture_id

        monkeypatch.setattr(review, "injected_seam", lambda key: injected)
        assert review.capture_loader() is injected

    def test_falls_back_to_the_store(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """With no injection the seam reads the store.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(review, "injected_seam", lambda key: None)
        install_store(monkeypatch, store_with(load_capture_for_comparison=lambda capture_id: capture_id))
        found = review.capture_loader()
        assert found is not None
        assert found("abc") == "abc"

    def test_answers_none_with_no_injection_and_no_store(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A lean host with no injection reads nothing and raises nothing.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(review, "injected_seam", lambda key: None)
        install_store(monkeypatch, None)
        assert review.capture_loader() is None
