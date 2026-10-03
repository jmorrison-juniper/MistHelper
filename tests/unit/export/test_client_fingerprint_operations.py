"""Tests for the raw organization fingerprint operations."""

from types import SimpleNamespace

from src.api.client_fingerprint_operations import (
    countOrgClientFingerprints,
    searchOrgClientFingerprints,
)


def test_count_uses_the_organization_path() -> None:
    """The count operation must not call the invalid site path."""
    calls: list[str] = []
    session = SimpleNamespace(mist_get=lambda path: calls.append(path) or "response")

    assert countOrgClientFingerprints(session, "org-1") == "response"
    assert calls == ["/api/v1/orgs/org-1/insights/fingerprints/count"]


def test_search_uses_the_organization_path() -> None:
    """The search operation must not call the invalid site path."""
    calls: list[str] = []
    session = SimpleNamespace(mist_get=lambda path: calls.append(path) or "response")

    assert searchOrgClientFingerprints(session, "org-1") == "response"
    assert calls == ["/api/v1/orgs/org-1/insights/fingerprints/search"]
