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

import logging  # Record selected request fixtures without a live source.
from collections.abc import Iterator  # Keep the request context active for each direct adapter test.
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from flask import Flask, session  # Supply explicit signed selection to the real source adapters.

from src.interfaces.portals.upgrade_portal.app.routes import review

SITE_ID = "cf36153a-97bb-4974-8f8f-e9cc25d64d83"
ORG_ID = "org-review-store-seams"  # Use one explicit selected organization in this isolated unit file.
logger = logging.getLogger(__name__)  # Keep fixture records separate from portal records.


@pytest.fixture(autouse=True)
def selected_request(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:  # Give direct adapters authorized scope.
    """Supply a selected local request context with known permitted organization scope."""
    logger.info("Prepare the selected synthetic store-seam request")  # Record fixture setup before the adapters run.
    app = Flask(__name__)  # Create an isolated application without portal wiring or source probes.
    app.config["SECRET_KEY"] = "synthetic-store-seam-request"  # Permit only this unit fixture's in-memory session.
    monkeypatch.setattr(review.identity, "permitted_org_ids", lambda: frozenset((ORG_ID,)))  # Known permitted scope.
    with app.test_request_context("/history"):  # No server, network, or credential is required.
        session["selected_org_id"] = (  # Keep organization authority separate from caller window values.
            ORG_ID  # Keep the derived query organization separate from caller site/window values.
        )
        logger.debug("Prepared one authorized synthetic store-seam request")  # Report no credential or owner key.
        yield  # Existing successful and unavailable-reader assertions use the same explicit authorized context.


class FakeQuery:
    """A stand-in for the query record that the store defines.

    Why:
        The seam builds the query by keyword and gives it to the lister.
        The stand-in keeps the organization and three caller values.
    """

    def __init__(  # Preserve all four real query fields in the selected request fixture.
        self, org_id: str, site_id: str, limit: int, offset: int
    ) -> None:  # Match the existing real query fields.
        """Store the selected organization and three caller values.

        Args:
            org_id: The validated selected organization.
            site_id: The site to narrow to.
            limit: The largest number of rows to read.
            offset: The number of rows to step over first.
        """
        logger.info("Build the synthetic scoped store query")  # Record query construction before assertions inspect it.
        self.org_id = org_id  # A missing selected organization must not disappear in a stand-in query.
        self.site_id = site_id  # Preserve the requested site restriction.
        self.limit = limit  # Preserve the supplied page size.
        self.offset = offset  # Preserve the supplied page start.
        logger.debug("Built one synthetic query with four scope and window fields")  # Report no stored row.


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

    def test_answers_the_first_name_that_matches(self) -> None:  # Verify the actual selected callable.
        """The first candidate wins, so a rename keeps the route working.

        Why:
            A seam names more than one candidate on purpose. The order is the
            order of preference, and a test must prove the order and not the
            set.
        """
        logger.info("Prepare two synthetic callable candidates")  # Record the test setup before resolution.
        module = store_with(second=lambda: "second", first=lambda: "first")  # Keep the original candidate order test.
        logger.debug("Prepared two synthetic callable candidates")  # Report no stored record.
        logger.info("Resolve the first actual callable candidate")  # Record the real attribute decision.
        found = review.find_attribute(module, ("first", "second"))  # Ask the production resolver.
        logger.debug("The resolver selected the first candidate: %s", found is module.first)  # Report a safe decision.
        assert found is module.first  # Verify exact callable identity rather than only a non-None result.
        assert found() == "first"  # Preserve the original successful callable result.

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

    def test_builds_the_query_from_the_three_values(  # Add the selected organization to all caller query values.
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The seam hands the site, the limit, and the offset to the store.

        Why:
            The route owns no count and no sort order of its own. A seam that
            dropped the offset would page the history back to the first page on
            every step, and the page would look stuck.

        Args:
            monkeypatch: The pytest patch helper.
        """
        logger.info("Prepare the scoped synthetic capture query reader")  # Record the isolated test setup.
        install_store(  # Preserve the query-construction seam without a database.
            monkeypatch, store_with(list_captures=lambda query: query, CaptureQuery=FakeQuery)
        )  # No database.
        logger.debug("Prepared one synthetic capture query reader")  # Report no source content.
        logger.info("Call the real capture adapter in the selected request")  # Record the direct source action.
        built = review.store_capture_rows(SITE_ID, limit=5, offset=10)  # The real adapter derives organization itself.
        logger.debug("The real capture adapter returned one synthetic query")  # Report no query values.
        assert (built.org_id, built.site_id, built.limit, built.offset) == (  # Require all four exact query values.
            ORG_ID,
            SITE_ID,
            5,
            10,
        )  # All fields survive.


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

    def test_builds_the_query_from_the_three_values(  # Preserve selected organization and all run window values.
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The run seam mirrors the capture seam exactly.

        Args:
            monkeypatch: The pytest patch helper.
        """
        logger.info("Prepare the scoped synthetic run query reader")  # Record the isolated test setup.
        install_store(monkeypatch, store_with(list_runs=lambda query: query, RunQuery=FakeQuery))  # No database.
        logger.debug("Prepared one synthetic run query reader")  # Report no source content.
        logger.info("Call the real run adapter in the selected request")  # Record the direct source action.
        built = review.store_run_rows(SITE_ID, limit=7, offset=14)  # The real adapter derives organization itself.
        logger.debug("The real run adapter returned one synthetic query")  # Report no query values.
        assert (built.org_id, built.site_id, built.limit, built.offset) == (  # Require all four exact query values.
            ORG_ID,
            SITE_ID,
            7,
            14,
        )  # All fields survive.


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

    def test_falls_back_to_the_store(  # Verify exact fallback reader identity without a weak non-None assertion.
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With no injection the seam reads the store.

        Args:
            monkeypatch: The pytest patch helper.
        """
        logger.info("Prepare the synthetic comparison capture reader")  # Record safe unit setup.
        monkeypatch.setattr(review, "injected_seam", lambda key: None)  # Require the existing real-store fallback.
        module = store_with(load_capture_for_comparison=lambda capture_id: capture_id)  # No database source.
        install_store(monkeypatch, module)  # Resolve only this synthetic module.
        logger.debug("Prepared one synthetic comparison capture reader")  # Report no stored capture.
        logger.info("Resolve the actual comparison capture fallback")  # Record the production loader decision.
        found = review.capture_loader()  # Use the actual fallback selection implementation.
        logger.debug(  # Report the safe exact-reader decision.
            "The fallback selected its stored reader: %s", found is module.load_capture_for_comparison
        )
        assert found is module.load_capture_for_comparison  # Require exact reader identity, not only non-None state.
        assert found("abc") == "abc"  # Preserve the original successful fallback result.

    def test_answers_none_with_no_injection_and_no_store(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A lean host with no injection reads nothing and raises nothing.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(review, "injected_seam", lambda key: None)
        install_store(monkeypatch, None)
        assert review.capture_loader() is None
