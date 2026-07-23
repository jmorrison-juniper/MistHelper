"""Regression tests for WanClientEventsExporter SDK endpoint resolution.

Why:
    Issue #1639: option 203 raised ``AttributeError`` at runtime because the
    exporter looked up ``mistapi.api.v1.sites.wan_clients.events.search.
    searchSiteWanClientEvents`` — a nested path that does not exist in the
    installed ``mistapi==0.63.3`` SDK. The correct surface is
    ``mistapi.api.v1.sites.wan_clients.searchSiteWanClientEvents``. These
    tests pin the fixed lookup against a namespace stub that mirrors the
    real SDK shape, so a future SDK rename fails loudly instead of silently
    passing under a permissive MagicMock.
"""

from __future__ import annotations  # WHY: PEP 604 unions + forward-ref compatibility on Python 3.13.

from types import SimpleNamespace  # WHY: strict stub whose attribute misses raise AttributeError like the real SDK.
from unittest.mock import MagicMock  # WHY: leaf-callable stubbing for the endpoint + get_all shim.

import pytest  # WHY: standard test runner + fixtures + raises.

from src.export.wan_client_events_exporter import (
    WanClientEventsExporter,  # WHY: subject under test — the exporter dataclass.
    _SiteStamp,  # WHY: reused for stamp-parameter fixtures below.
)


def _build_strict_mistapi(endpoint: MagicMock, get_all: MagicMock) -> SimpleNamespace:
    """Return a stub matching the real mistapi 0.63.3 attribute path.

    Why:
        ``SimpleNamespace`` raises ``AttributeError`` on missing attributes,
        so the exporter's SDK lookup must exactly match the installed
        surface. This catches nested-path regressions that a permissive
        ``MagicMock`` would silently mask.

    Args:
        endpoint: Callable stub returning the first-page response payload.
        get_all: Callable stub returning the paginated result list.

    Returns:
        A namespace with ``api.v1.sites.wan_clients.searchSiteWanClientEvents``
        and a top-level ``get_all`` shim.
    """
    return SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                sites=SimpleNamespace(
                    wan_clients=SimpleNamespace(
                        searchSiteWanClientEvents=endpoint,
                    ),
                ),
            ),
        ),
        get_all=get_all,
    )


def _build_exporter(mistapi_stub: SimpleNamespace) -> WanClientEventsExporter:
    """Construct an exporter with mocked collaborators and the given SDK stub.

    Why:
        Every collaborator except ``mistapi_module`` is irrelevant to the
        endpoint-resolution regression — mocking them keeps the test focused
        on the SDK surface being called.

    Args:
        mistapi_stub: Namespace/mock providing the SDK entry points.

    Returns:
        A fully-wired ``WanClientEventsExporter`` under test.
    """
    return WanClientEventsExporter(
        cache_utils=MagicMock(),
        org_site_exporter=MagicMock(),
        prompt_utils=MagicMock(),
        file_path_utils=MagicMock(),
        data_processing_utils=MagicMock(),
        data_exporter=MagicMock(),
        mistapi_module=mistapi_stub,
        apisession=MagicMock(),
    )


def test_installed_sdk_exposes_search_endpoint_at_expected_path() -> None:
    """The installed mistapi 0.63.3 SDK must expose the endpoint at the fixed path.

    Why:
        Anchors the fix against the real installed SDK — if a future upgrade
        renames the callable again, this test fails at the source of truth
        instead of leaving option 203 broken at runtime for operators.
    """
    import mistapi  # WHY: import locally so unrelated collection failures don't cascade.

    endpoint = mistapi.api.v1.sites.wan_clients.searchSiteWanClientEvents  # WHY: probe the fixed surface directly.
    assert callable(endpoint)  # WHY: guarantee it is a callable, not a stray module.


def test_fetch_events_calls_fixed_sdk_surface() -> None:
    """_fetch_events must resolve the endpoint via the fixed (non-nested) path.

    Why:
        Reproduces the AttributeError from issue #1639 when the exporter walks
        ``.events.search.searchSiteWanClientEvents``: the strict namespace
        stub has no such attribute chain, so any regression to the broken
        nested path raises AttributeError instead of quietly hitting a
        MagicMock leaf.
    """
    endpoint = MagicMock(return_value={"first-page": True})  # WHY: capture args passed to the SDK callable.
    get_all = MagicMock(return_value=[{"event_id": "evt-1"}])  # WHY: bound the paginator to one deterministic row.
    exporter = _build_exporter(_build_strict_mistapi(endpoint, get_all))

    results = exporter._fetch_events("site-abc")  # WHY: direct helper call exercises only the SDK lookup.

    endpoint.assert_called_once_with(exporter.apisession, "site-abc", limit=1000)  # WHY: pin signature + page size.
    get_all.assert_called_once_with(response={"first-page": True}, mist_session=exporter.apisession)
    assert results == [{"event_id": "evt-1"}]  # WHY: pin normalized return value shape.


def test_fetch_events_normalizes_none_to_empty_list() -> None:
    """_fetch_events must return an empty list when the SDK yields None.

    Why:
        The SDK returns ``None`` for empty responses; downstream code assumes
        an iterable. Preserving the normalization contract keeps the fix
        additive with existing behavior.
    """
    endpoint = MagicMock(return_value={})  # WHY: any first-page payload — paginator dictates the branch.
    get_all = MagicMock(return_value=None)  # WHY: force the None-normalization branch.
    exporter = _build_exporter(_build_strict_mistapi(endpoint, get_all))

    results = exporter._fetch_events("site-xyz")

    assert results == []  # WHY: None must degrade to empty list, never propagate to caller.


def test_fetch_events_rejects_legacy_nested_path() -> None:
    """A stub exposing only the legacy nested path must break _fetch_events.

    Why:
        Guardrails against silent regression to
        ``wan_clients.events.search.searchSiteWanClientEvents``. If any future
        refactor reintroduces that lookup, this test fails immediately.
    """
    legacy_only = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                sites=SimpleNamespace(
                    wan_clients=SimpleNamespace(
                        events=SimpleNamespace(
                            search=SimpleNamespace(
                                searchSiteWanClientEvents=MagicMock(),  # WHY: legacy path present, fixed path absent.
                            ),
                        ),
                    ),
                ),
            ),
        ),
        get_all=MagicMock(),
    )
    exporter = _build_exporter(legacy_only)

    with pytest.raises(AttributeError):  # WHY: fixed path must be the ONLY accepted lookup.
        exporter._fetch_events("site-legacy")


def test_site_stamp_is_frozen() -> None:
    """_SiteStamp must remain frozen so downstream stamping cannot mutate ids.

    Why:
        Rows persisted to CSV/SQLite rely on ``site_id``/``site_name`` staying
        stable across the merge/finalize passes. Freezing is an invariant
        depended on by callers.
    """
    stamp = _SiteStamp(site_id="s-1", site_name="Site One")

    with pytest.raises(AttributeError):  # WHY: dataclass(frozen=True) raises on assignment attempts.
        stamp.site_id = "s-2"  # type: ignore[misc]
