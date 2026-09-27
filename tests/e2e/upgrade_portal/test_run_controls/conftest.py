"""Shared site lock fixture for the run-control browser tests.

Why:
    A run-control action needs the site lock, so several tests of this package
    take it. The lock lives in the process-owned lock store of the isolated
    server, so it outlives the test that took it.

    A lock left behind refuses the next operator. `test_two_operators.py` then
    reads 400 `confirmation_required` from the lock route, and its fixture
    reports a skip. Pytest reports a skip as a pass, so 18 multi-operator tests
    stopped proving site isolation while the run still reported success.

    Issue #3508. The old teardown logged a warning when a release failed, so
    one test kept its lock and the run still passed. The fixture now gives each
    test a `HeldSiteLocks` record. The teardown fails when a release fails, so
    the report names the test that leaked the lock.
"""

from __future__ import annotations  # Keep annotations independent from import order.

from collections.abc import Iterator  # Type the fixture result.
from typing import Any  # The Playwright page object carries no import-time type here.

import pytest  # Declare the fixture.

from tests.support.upgrade_portal_e2e.lock_holds import HeldSiteLocks  # Issue #3508: the strict lock record.


@pytest.fixture(name="site_lock")
def fixture_site_lock(page: Any) -> Iterator[HeldSiteLocks]:
    """Give a test one record of site locks, and free each lock after the test.

    Why:
        The fixture asks for `page`, so pytest builds it after the page and
        tears it down before the page closes. The release call therefore still
        reaches a live browser session.

        Issue #3508. A failed release fails the teardown. Pytest reports a
        teardown failure as an error of the test, and the result of the test
        body stays in the report.

    Args:
        page: The Playwright page object of the first operator.

    Yields:
        The record. Call `take(site_id)` to lock a site. Call
        `release(site_id)` to free a site before the test ends.
    """
    holds = HeldSiteLocks(page)  # One record for each test, so no test frees the lock of another test.
    yield holds  # The test now takes each lock that it needs.
    holds.release_all()  # Free each lock that remains, and fail when a release fails.
