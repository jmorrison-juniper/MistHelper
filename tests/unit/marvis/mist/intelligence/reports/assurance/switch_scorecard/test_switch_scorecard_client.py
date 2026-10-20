"""Tests for the switch scorecard Mist API client."""

from __future__ import annotations  # WHY: keep annotations consistent with the source package.

from typing import Any  # WHY: fake resolver attributes use dynamic test doubles.

from src.mist.intelligence.reports.switch_scorecard.client import SwitchScorecardClient  # WHY: test the API seam only.


class _Config:
    @staticmethod
    def get_cached_or_prompted_org_id():  # Return the org id without a prompt.
        return "org-1"  # WHY: the client should pass this org id to the fetcher.


class _Resolver:
    ConfigUtils = _Config  # WHY: mimic SourceDependencyResolver for the client.


class _Fetcher:
    instances: list[_Fetcher] = []  # WHY: the test inspects the constructed fetcher.

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs  # WHY: capture fetcher construction parameters.
        self.org_id = ""  # WHY: the client assigns the resolved organization.
        self.rawdata = [{"type": "switch"}, ["bad"], {"type": "switch", "name": "sw"}]
        _Fetcher.instances.append(self)  # WHY: preserve this instance for assertions.

    def _fetch_api_data(self) -> bool:
        return True  # WHY: tests need no network or pagination.


def test_client_uses_shared_fetcher_with_switch_filter():  # Verify T018 and FR-015.
    _Fetcher.instances.clear()  # WHY: isolate this test from prior instances.
    client = SwitchScorecardClient(fetcher_factory=_Fetcher, resolver=_Resolver)

    rows = client.list_switch_stats()  # WHY: exercise the production client flow with fakes.

    assert len(rows) == 2  # WHY: non-dict response entries should not reach the model.
    assert _Fetcher.instances[0].org_id == "org-1"  # WHY: resolved org id must feed the fetcher.
    assert _Fetcher.instances[0].kwargs["type"] == "switch"  # WHY: the brief requires switch-only data.
    assert _Fetcher.instances[0].kwargs["limit"] == 1000  # WHY: match the existing menu 15 page size.
    assert _Fetcher.instances[0].kwargs["duration"] == "7d"  # WHY: uptime tile language uses a seven-day view.


class _FailingFetcher(_Fetcher):
    """Fetcher double whose paginated fetch fails with one HTTP status."""

    status_code = 500  # WHY: subclasses or tests set the HTTP status the failed fetch reports.

    def _fetch_api_data(self) -> bool:
        self.last_status_code = self.status_code  # WHY: mimic a fetcher that kept the last HTTP status.
        return False  # WHY: APIDataFetcher returns False after a failed or refused request.


def test_client_returns_no_rows_and_warns_on_http_403(caplog):  # Verify the HTTP 4xx failure mode.
    _Fetcher.instances.clear()  # WHY: isolate this test from prior instances.
    _FailingFetcher.status_code = 403  # WHY: a token without the org privilege receives 403 Forbidden.
    client = SwitchScorecardClient(fetcher_factory=_FailingFetcher, resolver=_Resolver)

    with caplog.at_level("WARNING"):  # WHY: the operator must see why the report holds zero switches.
        rows = client.list_switch_stats()  # WHY: exercise the refused request path.

    assert rows == []  # WHY: a 403 must not leak the placeholder rawdata rows into the report.
    assert "status=403" in caplog.text  # WHY: the warning names the HTTP status for the operator.
    assert "listOrgDevicesStats" in caplog.text  # WHY: the warning names the endpoint that failed.


def test_client_returns_no_rows_and_warns_on_http_503(caplog):  # Verify the HTTP 5xx failure mode.
    _Fetcher.instances.clear()  # WHY: isolate this test from prior instances.
    _FailingFetcher.status_code = 503  # WHY: a Mist cloud outage answers 503 Service Unavailable.
    client = SwitchScorecardClient(fetcher_factory=_FailingFetcher, resolver=_Resolver)

    with caplog.at_level("WARNING"):  # WHY: the operator must see why the report holds zero switches.
        rows = client.list_switch_stats()  # WHY: exercise the server failure path.

    assert rows == []  # WHY: a 503 must produce an empty result, never a partial or stale one.
    assert "status=503" in caplog.text  # WHY: the warning names the HTTP status for the operator.
