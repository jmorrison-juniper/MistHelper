"""Test that no live seed run of the browser server holds a site of the picker.

Why:
    Issue #3507. The browser server seeded a run in the state
    `awaiting_confirmation` and a run in the state `stopping` on the first site
    of the picker. The create route refuses a new run on a site that holds a
    live run. So each create call of `test_existing.py` drove a seed run in
    place of its own run. The module passed only when `test_bulk.py` ran first,
    because the bulk tests end both seed runs.

    This guard reads each record that the seed writer of the browser server
    saves. It fails when a live record holds a site that the stand-in cloud
    lists, and it names the run, the state, and the site. The decision uses the
    shipped rule `run_is_live`, so the guard and the site scan of the create
    route cannot disagree.

Scope:
    The site scan of the create route reads the field `site_id` only. A
    multi-site operation names its sites in the field `site_ids`, so it blocks
    no create call. The guard reads the field `site_id` only for the same
    reason.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import contextlib  # The stand-in application context enters nothing.
import importlib.util  # A conftest is not importable by name, so this module loads it by path.
import logging  # Record each step of the guard without a secret.
import sys  # The module `dataclasses` reads the loaded conftest back from `sys.modules`.
from collections.abc import Mapping, Sequence  # The scan reads records of any mapping type.
from dataclasses import dataclass  # One value holds the records and the log lines of one write.
from pathlib import Path  # Build the conftest path without a hardcoded separator.
from types import ModuleType  # The loaded conftest is a module value.
from typing import Any  # The records hold JSON values of mixed types.

import pytest  # The fixtures and the parameters of the decision tests.

from src.upgrade_portal.app.routes.upgrade import run_is_live  # The shipped rule of the site scan.
from tests.e2e.upgrade_portal.retry_run_seeds import FAILED_RUN_ID, RETRY_SITE_ID, STOPPED_RUN_ID  # Issue #3292.

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

CONFTEST_PATH = Path(__file__).resolve().parents[3] / "tests" / "e2e" / "upgrade_portal" / "conftest.py"
CONFTEST_MODULE_NAME = "upgrade_portal_e2e_conftest_seed_sites"  # A private name, apart from the pytest load.
REFUSAL_PREFIX = "The browser fixture runs did not write"  # The warning of a writer that stopped early.
REPORT_PREFIX = "Browser fixture run seeds reported"  # The last line of a writer that finished.
LISTED_SITE = "site-listed"  # The one site that the picker lists in the decision tests.


class RecordingUpgrade:
    """Stand in for the upgrade route module, and keep each record that the writer saves."""

    def __init__(self) -> None:
        """Start with no record."""
        self.records: list[dict[str, Any]] = []  # One entry for each save call, in call order.

    def save_run(self, record: Mapping[str, Any]) -> bool:
        """Keep one record, and accept it the way a healthy store does."""
        self.records.append(dict(record))  # A copy, so a later change by the caller does not reach the list.
        return True  # A healthy store accepts each record.


class BuiltApplication:
    """Stand in for the built application, whose context the writer enters."""

    @staticmethod
    def app_context() -> contextlib.AbstractContextManager[None]:
        """Return a context that enters nothing, because the stand-in store needs no application."""
        return contextlib.nullcontext()  # The writer enters and leaves it with no effect.


class LogLines(logging.Handler):
    """Keep the text of each log record that the writer emits."""

    def __init__(self) -> None:
        """Start with no line, and accept each level."""
        super().__init__(logging.DEBUG)  # The final report is an info line, so the handler keeps each level.
        self.lines: list[str] = []  # One entry for each record, in emit order.

    def emit(self, record: logging.LogRecord) -> None:
        """Keep the formatted text of one record."""
        self.lines.append(record.getMessage())  # The text with its arguments, which the tests read.


@dataclass(frozen=True)
class SeedWrite:
    """Hold the records and the log lines of one call of the seed writer."""

    records: tuple[dict[str, Any], ...]  # Each record that the writer saved, in call order.
    lines: tuple[str, ...]  # Each log line of the writer, in emit order.
    listed: frozenset[str]  # Each site that the stand-in cloud lists for the picker.


class SeedSiteScan:
    """Find each live seed run that holds a site of the picker."""

    @staticmethod
    def live_runs_on_listed_sites(records: Sequence[Mapping[str, Any]], listed: frozenset[str]) -> list[str]:
        """Name each live run whose field `site_id` holds a listed site.

        Args:
            records: The run records to scan.
            listed: The site identifiers that the picker lists.

        Returns:
            One line for each live run on a listed site, with its key, its state, and its site.
        """
        found: list[str] = []  # One line for each run that blocks a create call.
        for record in records:  # Each record that the writer saved.
            site_id = str(record.get("site_id") or "")  # A multi-site operation holds no value here.
            if site_id in listed and run_is_live(dict(record)):  # The same rule as the site scan of the route.
                found.append(f"{record.get('run_id')} (state {record.get('state')}, site {site_id})")  # Name it.
        return found  # An empty list means that no seed run blocks a create call.


class SeedWriterRun:
    """Load the browser conftest by path, and run its seed writer one time."""

    @staticmethod
    def load_conftest() -> ModuleType:
        """Load the browser conftest under a private name.

        Returns:
            The loaded conftest module.
        """
        logger.info("Load the browser conftest from %s", CONFTEST_PATH)  # Log before the load.
        spec = importlib.util.spec_from_file_location(CONFTEST_MODULE_NAME, CONFTEST_PATH)  # A load by path.
        assert spec is not None and spec.loader is not None, "the browser conftest must be loadable"  # Fail early.
        module = importlib.util.module_from_spec(spec)  # An empty module that the loader fills.
        sys.modules[CONFTEST_MODULE_NAME] = module  # The module `dataclasses` reads it back while it builds a class.
        try:  # Remove the private entry also when the load fails.
            spec.loader.exec_module(module)  # Run the conftest code one time.
        finally:
            sys.modules.pop(CONFTEST_MODULE_NAME, None)  # No other test finds the private entry.
        logger.debug("Loaded the browser conftest")  # Log after the load.
        return module  # The caller runs the seed writer of this module.

    @staticmethod
    def listed_sites(conftest: ModuleType) -> frozenset[str]:
        """Read the sites that the stand-in cloud lists for the picker of the stand-in organization."""
        logger.info("Read the sites that the stand-in cloud lists")  # Log before the read.
        rows = conftest.stand_in_cloud_read("listOrgSites", org_id=conftest.STAND_IN_ORG_ID)  # The picker read.
        listed = frozenset(str(row["id"]) for row in rows)  # The identifier of each row.
        logger.debug("The stand-in cloud lists %d site(s)", len(listed))  # Log after the read.
        return listed  # The guard compares each seed run with this set.

    @classmethod
    def write(cls, conftest: ModuleType) -> SeedWrite:
        """Run the seed writer with a stand-in store, and keep its records and its log lines."""
        upgrade = RecordingUpgrade()  # The store that keeps each record.
        lines = LogLines()  # The handler that keeps each log line of the writer.
        previous_level = conftest.logger.level  # Restore the level after the write.
        conftest.logger.addHandler(lines)  # Keep the lines of this write only.
        conftest.logger.setLevel(logging.DEBUG)  # The final report is an info line, so each level passes.
        logger.info("Run the seed writer of the browser server with a stand-in store")  # Log before the write.
        try:  # Remove the handler also when the writer raises.
            conftest._write_fixture_runs(BuiltApplication(), upgrade)  # The same writer that the server runs.
        finally:
            conftest.logger.removeHandler(lines)  # No later test reads these lines.
            conftest.logger.setLevel(previous_level)  # Leave the logger as the load left it.
        logger.debug("The seed writer saved %d record(s)", len(upgrade.records))  # Log after the write.
        return SeedWrite(tuple(upgrade.records), tuple(lines.lines), cls.listed_sites(conftest))  # One value.


@pytest.fixture(name="seed_write", scope="module")
def fixture_seed_write() -> SeedWrite:
    """Load the browser conftest and run its seed writer, one time for this module."""
    return SeedWriterRun.write(SeedWriterRun.load_conftest())  # The load takes seconds, so each test shares it.


class TestTheSeedRunSites:
    """No live seed run holds a site of the picker."""

    def test_the_seed_writer_finishes(self, seed_write: SeedWrite) -> None:
        """The writer MUST reach its final report, or the guard reads a partial list."""
        logger.info("Check that the seed writer reached its final report")  # Log the plan.
        refusals = [line for line in seed_write.lines if line.startswith(REFUSAL_PREFIX)]  # A writer that stopped.
        reports = [line for line in seed_write.lines if line.startswith(REPORT_PREFIX)]  # A writer that finished.
        assert refusals == [], f"The seed writer stopped early: {refusals}"  # A stop hides each later seed.
        assert len(reports) == 1, f"The seed writer wrote {len(reports)} final report(s). The test expects 1."
        assert "=False" not in reports[0], f"A seed write reported a refusal: {reports[0]}"  # Each save succeeded.

    def test_no_live_seed_run_holds_a_listed_site(self, seed_write: SeedWrite) -> None:
        """A live seed run on a site of the picker MUST fail the guard, and the message MUST state the count."""
        count = len(seed_write.records)  # The count of runs that the guard reads.
        logger.info("Scan %d seed run(s) against %d listed site(s)", count, len(seed_write.listed))  # Log the plan.
        found = SeedSiteScan.live_runs_on_listed_sites(seed_write.records, seed_write.listed)  # Each blocking run.
        logger.info("The guard read %d seed run(s), and %d of them hold a listed site", count, len(found))  # Result.
        assert count > 0, "The seed writer saved no record, so the guard read nothing."  # Fail on no input.
        assert found == [], (
            f"The guard read {count} seed run(s), and {len(found)} live run(s) hold a site of the picker: "
            f"{'; '.join(found)}. Each create call on that site answers 409 and names the seed run."
        )

    def test_retry_seed_runs_use_their_local_site(self, seed_write: SeedWrite) -> None:
        """The retry seed runs MUST use one site that is not the shared first site."""
        logger.info("Check the site of each retry seed run")  # Log the plan.
        records = {str(record["run_id"]): record for record in seed_write.records}  # Index the saved records.
        retry_records = [records[FAILED_RUN_ID], records[STOPPED_RUN_ID]]  # The two retry records under test.
        assert {str(record["site_id"]) for record in retry_records} == {RETRY_SITE_ID}  # One local site.
        assert RETRY_SITE_ID not in seed_write.listed  # The site does not enter another browser journey.


class TestTheScanDecision:
    """The scan names each live run on a listed site, and no other run."""

    def test_a_live_run_on_a_listed_site_is_named(self) -> None:
        """A live run on a listed site MUST appear with its key, its state, and its site."""
        logger.info("Scan one live run on a listed site")  # Log the plan.
        record = {"run_id": "run-live", "site_id": LISTED_SITE, "state": "awaiting_confirmation"}  # A live run.
        found = SeedSiteScan.live_runs_on_listed_sites([record], frozenset({LISTED_SITE}))  # One scan.
        assert found == [f"run-live (state awaiting_confirmation, site {LISTED_SITE})"]  # One named run.

    @pytest.mark.parametrize(
        "record",
        [
            {"run_id": "run-final", "site_id": LISTED_SITE, "state": "failed"},  # A final run blocks nothing.
            {"run_id": "run-away", "site_id": "site-unlisted", "state": "stopping"},  # The picker omits the site.
            {"run_id": "run-multi", "site_id": None, "site_ids": [LISTED_SITE], "state": "running"},  # Many sites.
            {"run_id": "run-unknown", "site_id": LISTED_SITE, "state": "no-such-state"},  # The rule reads not live.
        ],
        ids=["final-run", "unlisted-site", "multi-site-operation", "unknown-state"],
    )
    def test_a_run_that_blocks_no_create_call_is_not_named(self, record: dict[str, Any]) -> None:
        """A run that the site scan of the create route ignores MUST NOT appear."""
        logger.info("Scan one run that blocks no create call: %s", record["run_id"])  # Log the plan.
        found = SeedSiteScan.live_runs_on_listed_sites([record], frozenset({LISTED_SITE}))  # One scan.
        assert found == []  # The create route accepts a new run on the listed site.
