"""Find each run that one browser module of the upgrade portal left live.

Why:
    Issue #3511. The walk of `test_capture.py` built a run on the first site of
    the picker, and no teardown ended it. The portal refuses a create call at a
    site that holds a live run, so each later create call at that site answered
    409. Two tests then used the leftover run in place of their own run, and
    each test passed. No check saw the leftover run.

    `LiveRun` applies the live rule of the create refusal to one history row.
    `SiteRunReader` reads the run history of each site through the portal.
    `LiveRunCheck` compares the live runs before and after one module, and it
    fails the module that left a new live run. Each class holds one decision,
    so a direct test proves each decision with no browser and no portal.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import logging  # Record each step of the scan without a cookie value.
import time  # The default clock of the scan.
import urllib.request  # Read the history route with the standard library, so the check needs no browser page.
from collections.abc import Callable, Iterable  # The types of the opener, the clock, and the site list.
from dataclasses import asdict, dataclass  # Describe each run, each scan, and each check.
from typing import Any, ClassVar  # A history row holds values of mixed types.
from urllib.error import HTTPError  # A refused read carries a status and a body.
from urllib.parse import urlencode  # Build the page query of each read.

from tests.support.upgrade_portal_e2e.site_lock import AnswerBody  # Read each body as a JSON object.

logger = logging.getLogger(__name__)  # Keep each record of the live-run check tied to this module.


@dataclass(frozen=True, order=True)
class LiveRun:  # One run that can still block a create call at its site.
    """Name one run that can still block a create call at its site.

    Why:
        The portal refuses a create call at a site that holds a live run. The
        check uses the same live rule, so it cannot miss a leak that blocks a
        create call, and it cannot report a final run as a leak.
    """

    site_id: str  # The site that holds the run. It comes first, so a sort groups the runs of each site.
    run_id: str  # The key of the run.
    state: str  # The state of the run, which each message names.

    @classmethod
    def from_row(cls, site_id: str, row: dict[str, Any]) -> LiveRun | None:
        """Return the live run of one history row, or None when no stop can change the run.

        Args:
            site_id: The site whose history holds the row.
            row: One row of the run history.

        Returns:
            The live run, or None for a final run and for a state outside the run model.
        """
        from src.upgrade_portal.app.routes.upgrade import run_is_live  # Late, so a collection loads no portal.

        if not run_is_live(row):  # The create refusal skips a final run and a state outside the model.
            return None  # The run blocks no create call.
        return cls(site_id, str(row.get("run_id", "")), str(row.get("state", "")))  # The three names of a leak.


@dataclass(frozen=True)
class SiteRunScan:  # The live runs, the size, and the time of one scan of the picker sites.
    """Hold the result of one scan of the run history of each site.

    Why:
        The record of each module holds the size and the time of its scan. A
        reader can then see that the check read each site, and how long the
        read took.
    """

    runs: frozenset[LiveRun]  # Each live run that the scan found.
    rows: int  # The count of history rows that the scan read. A damaged row counts too.
    sites: int  # The count of sites that the scan read.
    elapsed_ms: float  # The time of the scan in milliseconds.


class SiteRunReader:  # Read the run history of each site through the portal.
    """Read the run history of each site of the picker through the portal.

    Why:
        The history route reads the same run records as the create refusal. A
        read with the session cookies of the browser needs no browser page, so
        the check can run after each module, even after a module that closed
        its page.
    """

    PATH: ClassVar[str] = "/api/sites/{site_id}/runs/history"  # The run history route of one site.
    RUNS_FIELD: ClassVar[str] = "runs"  # The field of the body that holds the rows of the page.
    PAGE_SIZE: ClassVar[int] = 200  # `LARGEST_HISTORY_LIMIT` of the route, so each read asks for the largest page.
    PAGE_BOUND: ClassVar[int] = 50  # The most pages of one site. A longer history means a fault of the route.
    TIMEOUT_S: ClassVar[float] = 30.0  # The bound of one read, so a stopped portal cannot stop the run.

    def __init__(
        self,
        base_url: str,
        cookie_header: str,
        opener: Callable[..., Any] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        """Keep the address of the portal, the session cookies, the opener, and the clock.

        Args:
            base_url: The address of the portal.
            cookie_header: The Cookie header of one signed-in operator.
            opener: The call that opens one request. The default opener sends no read through a proxy.
            clock: The clock that times the scan. The default clock is `time.perf_counter`.
        """
        self._base_url = base_url.rstrip("/")  # Each path starts with a slash.
        self._cookie_header = cookie_header  # The history route needs a signed-in session.
        direct = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # A loopback read skips each proxy.
        self._open = opener or direct.open  # A direct test gives a scripted opener.
        self._clock = clock or time.perf_counter  # A monotonic clock times the scan.

    def scan(self, site_ids: Iterable[str]) -> SiteRunScan:
        """Read the history of each site, and return each live run that the reads found.

        Args:
            site_ids: The sites to read, in the order of the reads.

        Returns:
            The live runs, the row count, the site count, and the time of the scan.

        Raises:
            AssertionError: One read failed, or one history did not end within the page bound.
        """
        sites = list(site_ids)  # Read the sites one time, in the order given.
        logger.info("Scan the run history of %s site(s) for a live run", len(sites))  # Log before the scan.
        start = self._clock()  # The first of the two clock reads.
        runs: set[LiveRun] = set()  # A set holds each live run one time.
        rows = 0  # No history row read yet.
        for site_id in sites:  # Read each site in the order given.
            site_rows = self._site_rows(site_id)  # Each row of the whole history of the site.
            rows += len(site_rows)  # A damaged row counts as read, so the count matches the route.
            found = (LiveRun.from_row(site_id, row) for row in site_rows if isinstance(row, dict))  # Object rows.
            runs.update(run for run in found if run is not None)  # A final run gives None.
        elapsed_ms = round((self._clock() - start) * 1000, 1)  # The second clock read.
        logger.debug("The scan read %s row(s) and found %s live run(s)", rows, len(runs))  # Log after the scan.
        return SiteRunScan(frozenset(runs), rows, len(sites), elapsed_ms)  # The result of the scan.

    def _site_rows(self, site_id: str) -> list[Any]:
        """Read each page of the history of one site, up to the page bound.

        Args:
            site_id: The site to read.

        Returns:
            Each row of each page, in the order of the pages.

        Raises:
            AssertionError: One read failed, or the history did not end within the page bound.
        """
        rows: list[Any] = []  # No row of this site read yet.
        for _ in range(self.PAGE_BOUND):  # A history that does not end must not start an endless read.
            page = self._read_page(site_id, len(rows))  # The next page starts after each row so far.
            rows.extend(page)  # Keep each row. A damaged row counts too.
            if len(page) < self.PAGE_SIZE:  # A short page is the last page.
                return rows  # The whole history of the site.
        raise AssertionError(  # The route answered only full pages, so the check cannot see the whole history.
            f"The run history of site {site_id} did not end within {self.PAGE_BOUND} pages of "
            f"{self.PAGE_SIZE} rows. The live-run check of issue #3511 cannot read the whole history."
        )

    def _read_page(self, site_id: str, offset: int) -> list[Any]:
        """Read one page of the history of one site, and return its rows.

        Args:
            site_id: The site to read.
            offset: The count of rows to step over first.

        Returns:
            The rows of the page.

        Raises:
            AssertionError: The read failed, or the body holds no run list.
        """
        path = self.PATH.format(site_id=site_id)  # The history route of the site.
        query = urlencode({"limit": self.PAGE_SIZE, "offset": offset})  # The largest page from the offset.
        call = f"GET {path}?{query}"  # Each message names this call. It holds no cookie value.
        logger.info("Read one page of the run history: %s", call)  # Log before the read.
        status, text = self._answer(call, f"{self._base_url}{path}?{query}")  # One signed read.
        rows = AnswerBody.read(call, status, text).get(self.RUNS_FIELD)  # The body must be a JSON object.
        if not isinstance(rows, list):  # A body with no run list would hide a leak as "no live run".
            raise AssertionError(f"{call} answered {status} with no run list. The body reads: {text!r}")
        logger.debug("The page answered %s with %s row(s)", status, len(rows))  # Log after the read.
        return rows  # The rows of the page.

    def _answer(self, call: str, url: str) -> tuple[int, str]:
        """Send one read with the session cookies, and return the status and the body text.

        Args:
            call: The method and the path of the read, which each message names.
            url: The whole address of the read.

        Returns:
            The status and the body text of the answer.

        Raises:
            AssertionError: The portal refused the read, or the read got no answer.
        """
        headers = {"Cookie": self._cookie_header, "Accept": "application/json"}  # A signed read of JSON.
        request = urllib.request.Request(url, headers=headers)  # A request with no body is a GET.
        try:  # The opener raises for a refusal and for a read that got no answer.
            with self._open(request, timeout=self.TIMEOUT_S) as answer:  # The read cannot wait for ever.
                return int(answer.status), answer.read().decode("utf-8")  # The portal answers UTF-8 text.
        except HTTPError as refusal:  # The portal answered a status of 400 or more.
            body = refusal.fp.read().decode("utf-8", "replace") if refusal.fp is not None else ""  # The code.
            raise AssertionError(  # A refused read would hide a leak as "no live run".
                f"{call} answered {refusal.code}, so the live-run check of issue #3511 cannot read "
                f"the history. The body reads: {body!r}"
            ) from refusal
        except OSError as failure:  # A refused connection or a timeout, so the portal gave no answer.
            raise AssertionError(  # A read with no answer would hide a leak as "no live run".
                f"{call} did not answer, so the live-run check of issue #3511 cannot read the history: {failure}"
            ) from failure


@dataclass(frozen=True)
class LiveRunCheck:  # Decide whether one module left a new live run.
    """Compare the live runs before and after one browser module.

    Why:
        A run that was live before the module belongs to an earlier module, so
        the check blames only a new run. The first module compares against an
        empty set, because each browser run starts the portal with a new store.
    """

    module: str  # The node id of the module.
    before: frozenset[LiveRun]  # The live runs after the previous module.
    after: SiteRunScan  # The scan after this module.

    @property
    def leaks(self) -> tuple[LiveRun, ...]:
        """Return each new live run, in the order of the site and the key."""
        known = {run.run_id for run in self.before}  # A key that was live before the module, in any state.
        return tuple(sorted(run for run in self.after.runs if run.run_id not in known))  # New runs only.

    def record(self) -> dict[str, Any]:
        """Return the fields of one line of the record of the check."""
        return {  # One JSON line for each module.
            "module": self.module,  # The module that the scan followed.
            "before": len(self.before),  # The count of live runs before the module.
            "after": len(self.after.runs),  # The count of live runs after the module.
            "leaks": [asdict(run) for run in self.leaks],  # Each new live run, with its site and its state.
            "rows": self.after.rows,  # The size of the scan.
            "sites": self.after.sites,  # The count of sites that the scan read.
            "elapsed_ms": self.after.elapsed_ms,  # The time of the scan.
        }

    def require_no_leak(self) -> None:
        """Fail the module that left a new live run.

        Raises:
            AssertionError: The module left one or more new live runs.
        """
        logger.info("Decide whether the module left a new live run")  # Log before the decision.
        leaks = self.leaks  # Find the new live runs one time.
        logger.debug("The module left %s new live run(s)", len(leaks))  # Log after the decision.
        if not leaks:  # Each run of the module ended, or the module built no run.
            return  # The module passes.
        lines = [f"- Run {run.run_id} in state {run.state} at site {run.site_id}." for run in leaks]  # One each.
        raise AssertionError(  # Pytest reports a teardown error for the last test of the module.
            "\n".join(
                [
                    f"The module {self.module} left {len(leaks)} live run(s):",  # The count and the module.
                    *lines,  # Each run, with its state and its site.
                    "A test or a seed of the module left each run live. The live-run check of issue #3511 "
                    "fails the module, because a live run blocks each later create call at its site.",
                ]
            )
        )

    @staticmethod
    def summary(checks: list[LiveRunCheck]) -> str:
        """Return the one line of the terminal summary, or an empty text when no module ran the check."""
        if not checks:  # No portal started, so no module ran the check.
            return ""  # The hook prints no line.
        sites = max(check.after.sites for check in checks)  # Each scan reads the same picker sites.
        rows = sum(check.after.rows for check in checks)  # The total size of the scans.
        leaks = sum(len(check.leaks) for check in checks)  # The total count of leaks.
        elapsed_ms = round(sum(check.after.elapsed_ms for check in checks), 1)  # The total time of the scans.
        return (  # One line, so the terminal summary stays short.
            f"The live-run check of issue #3511 scanned {sites} site(s) after each of {len(checks)} module(s). "
            f"It read {rows} history row(s), found {leaks} leaked live run(s), and took {elapsed_ms} ms."
        )
