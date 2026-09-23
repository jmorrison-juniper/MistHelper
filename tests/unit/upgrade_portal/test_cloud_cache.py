"""Unit tests of the short reuse of organization list reads (issue #3210)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from src.upgrade_portal.app.routes import select
from src.upgrade_portal.runtime.cloud_cache import CloudReadCache

SITES = [{"id": "site-1", "name": "One"}, {"id": "site-2", "name": "Two"}]  # One cloud answer.
KEY = ("owner-a", "listOrgSites", "org-1", 1)  # One operator, one read, one organization, one session.


class Clock:
    """A clock that a test moves by hand."""

    def __init__(self) -> None:
        """Start at zero seconds."""
        self.now = 0.0  # The present reading.

    def __call__(self) -> float:
        """Return the present reading."""
        return self.now  # The cache reads the time through this call.


def test_a_fresh_answer_returns_a_copy() -> None:
    """A kept answer returns equal records that the caller cannot change inside the cache."""
    cache = CloudReadCache(60, 8, Clock())  # One cache with a still clock.
    cache.put(KEY, SITES)  # Keep one answer.
    first = cache.get(KEY) or []  # Read it back. An empty list fails the next line.
    assert first == SITES  # The same records.
    first[0]["name"] = "Changed"  # A caller edits its copy.
    assert cache.get(KEY) == SITES  # The kept records stay whole.


def test_an_old_answer_is_dropped() -> None:
    """An answer older than the period reads as absent."""
    clock = Clock()  # A clock that the test moves.
    cache = CloudReadCache(60, 8, clock)  # One cache with a 60-second period.
    cache.put(KEY, SITES)  # Keep one answer at second 0.
    clock.now = 60.0  # Exactly at the end of the period.
    assert cache.get(KEY) == SITES  # The answer is still valid.
    clock.now = 60.5  # Past the end of the period.
    assert cache.get(KEY) is None  # The next view reads the cloud again.


def test_an_empty_answer_is_never_kept() -> None:
    """A read that answered nothing must not hide the sites for the whole period."""
    cache = CloudReadCache(60, 8, Clock())  # One cache.
    cache.put(KEY, [])  # A failed read answers an empty list.
    assert cache.get(KEY) is None  # The next view reads the cloud again.


def test_the_oldest_entry_leaves_a_full_cache_first() -> None:
    """A full cache drops its oldest entry."""
    cache = CloudReadCache(60, 2, Clock())  # Room for two answers.
    keys = [("owner-a", "listOrgSites", f"org-{index}", 1) for index in range(3)]  # Three organizations.
    for key in keys:  # Keep three answers in order.
        cache.put(key, SITES)  # One answer for each organization.
    assert cache.get(keys[0]) is None  # The oldest answer left.
    assert cache.get(keys[1]) == SITES  # The two newest answers stay.
    assert cache.get(keys[2]) == SITES


class CloudStandIn:
    """Count each cloud read that `default_cloud_read` makes."""

    def __init__(self, answer: list[dict[str, Any]]) -> None:
        """Keep one fixed answer."""
        self.answer = answer  # The records of every read.
        self.reads = 0  # The count of cloud reads.

    def listOrgSites(self, cloud_session: Any, org_id: str, limit: int) -> SimpleNamespace:
        """Answer one first page, as the software development kit does."""
        del cloud_session, org_id, limit  # One fixed answer for every call.
        self.reads += 1  # Count the read.
        return SimpleNamespace(data=list(self.answer))  # The shape that `collect_pages` reads.


@pytest.fixture
def cloud(monkeypatch: pytest.MonkeyPatch) -> CloudStandIn:
    """Route `default_cloud_read` to a counting stand-in with a fresh cache."""
    stand_in = CloudStandIn(SITES)  # The cloud answers two sites.
    monkeypatch.setattr(select, "CLOUD_READ_CACHE", CloudReadCache(60, 8, Clock()))  # No state from another test.
    monkeypatch.setattr(select, "import_module", lambda name: stand_in)  # The call resolves to the stand-in.
    monkeypatch.setattr(select, "collect_pages", lambda session, page, name: list(page.data))  # One page only.
    operator = SimpleNamespace(owner=SimpleNamespace(key="owner-a"), cloud_session=object())  # One operator.
    monkeypatch.setattr(select.identity, "current_session", lambda: operator)  # The signed-in record.
    return stand_in


def test_a_repeated_view_reads_the_cloud_once(cloud: CloudStandIn) -> None:
    """Issue #3210: the second view of the same list inside one minute makes no cloud read."""
    first = select.default_cloud_read("listOrgSites", org_id="org-1")  # The first view reads the cloud.
    second = select.default_cloud_read("listOrgSites", org_id="org-1")  # The second view reuses the answer.
    assert first == second == SITES  # Both views show the same sites.
    assert cloud.reads == 1  # Only the first view reached the cloud.


def test_another_organization_reads_the_cloud_again(cloud: CloudStandIn) -> None:
    """A different organization never reuses the list of another organization."""
    select.default_cloud_read("listOrgSites", org_id="org-1")  # The first organization.
    select.default_cloud_read("listOrgSites", org_id="org-2")  # The second organization.
    assert cloud.reads == 2  # Each organization reached the cloud once.


def test_another_operator_reads_the_cloud_again(cloud: CloudStandIn, monkeypatch: pytest.MonkeyPatch) -> None:
    """A second operator never reuses the list that another credential fetched."""
    select.default_cloud_read("listOrgSites", org_id="org-1")  # The first operator.
    other = SimpleNamespace(owner=SimpleNamespace(key="owner-b"), cloud_session=object())  # A second operator.
    monkeypatch.setattr(select.identity, "current_session", lambda: other)  # The second signed-in record.
    select.default_cloud_read("listOrgSites", org_id="org-1")  # The same organization, another credential.
    assert cloud.reads == 2  # Each operator reached the cloud once.


def test_an_empty_answer_reads_the_cloud_on_the_next_view(cloud: CloudStandIn) -> None:
    """An empty answer is not kept, so a failed read cannot hide the sites."""
    cloud.answer = []  # The cloud answers no site.
    select.default_cloud_read("listOrgSites", org_id="org-1")  # The first view.
    select.default_cloud_read("listOrgSites", org_id="org-1")  # The second view.
    assert cloud.reads == 2  # Both views reached the cloud.
