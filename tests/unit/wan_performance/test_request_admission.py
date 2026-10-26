"""Check shared transport admission for SDK calls, retries, and concurrent workers."""

import json
from unittest.mock import MagicMock, patch

import pytest
from requests import PreparedRequest, Response

from src.interfaces.wan_performance.collection.request_admission import AdmittedAdapter, RequestLedger


def request():
    """Build an independent test credential that never reaches a network."""
    prepared = PreparedRequest()
    prepared.prepare(method="GET", url="https://api.invalid/api/v1/orgs/org-one/sites")
    prepared.headers["Authorization"] = "Token independent-test-placeholder"
    return prepared


def test_transport_admits_every_send_and_hashes_credential():
    """Count each actual attempt rather than each logical SDK call."""
    redis = MagicMock()
    redis.eval.return_value = 1
    adapter = AdmittedAdapter(RequestLedger(redis), 15)
    with patch("requests.adapters.HTTPAdapter.send", return_value=Response()) as send:
        adapter.send(request())
        adapter.send(request())
    assert redis.eval.call_count == 2
    key = redis.eval.call_args.args[2]
    assert key.startswith("misthelper:api:v1:requests:")
    assert "placeholder" not in key
    assert send.call_args.kwargs["timeout"] == 15
    assert adapter.max_retries.total == 0


def test_shared_quota_or_outage_refuses_network():
    """Stop before the transport when Redis denies or cannot admit a request."""
    redis = MagicMock()
    redis.eval.return_value = 0
    adapter = AdmittedAdapter(RequestLedger(redis), 15)
    with patch("requests.adapters.HTTPAdapter.send") as send:
        with pytest.raises(ConnectionError, match="quota"):
            adapter.send(request())
        redis.eval.side_effect = ConnectionError("store unavailable")
        with pytest.raises(ConnectionError):
            adapter.send(request())
    send.assert_not_called()


def test_http_rate_limit_does_not_start_sdk_retry_wait():
    """Return an explicit failure before the SDK starts Retry-After sleeping."""
    redis = MagicMock()
    redis.eval.return_value = 1
    response = MagicMock(spec=Response)
    response.status_code = 429
    with patch("requests.adapters.HTTPAdapter.send", return_value=response):
        with pytest.raises(ConnectionError, match="429"):
            AdmittedAdapter(RequestLedger(redis), 15).send(request())
    response.close.assert_called_once_with()


def test_missing_authentication_cannot_use_anonymous_quota():
    """Do not make unaccounted data requests from an unconfigured session."""
    prepared = request()
    prepared.headers.clear()
    with pytest.raises(ConnectionError, match="authentication"):
        AdmittedAdapter(RequestLedger(MagicMock()), 15).send(prepared)


def test_existing_cookie_session_uses_the_same_org_ceiling():
    """Account existing authenticated cookie sessions without another login flow."""
    prepared = request()
    prepared.headers.pop("Authorization")
    prepared.headers["Cookie"] = "sessionid=independent-placeholder"
    client = MagicMock()
    client.eval.return_value = 1
    RequestLedger(client).admit(prepared)
    assert client.eval.call_args.args[3] == "misthelper:api:v1:org:org-one"
    assert "placeholder" not in client.eval.call_args.args[2]


def test_common_adapter_factory_uses_shared_ledger_only_when_enabled(monkeypatch):
    """Keep existing timeout behavior unchanged unless admission is explicitly enabled."""
    from src.foundation.support.refactors.initialize_mist_session import MistSessionConfigurator

    monkeypatch.setenv("WAN_SHARED_ADMISSION", "true")
    ledger = RequestLedger(MagicMock())
    with patch.object(RequestLedger, "connect", return_value=ledger):
        adapter = MistSessionConfigurator._build_timeout_adapter(15)
    assert isinstance(adapter, AdmittedAdapter)
    assert adapter.ledger is ledger
    monkeypatch.setenv("WAN_SHARED_ADMISSION", "false")
    original = MistSessionConfigurator._build_timeout_adapter(15)
    assert not isinstance(original, AdmittedAdapter)
    assert original.max_retries.total == 2


def test_parallel_normal_pagination_and_fast_attempts_share_the_same_key():
    """Account every concurrent send through the common session transport."""
    from concurrent.futures import ThreadPoolExecutor

    client = MagicMock()
    client.eval.return_value = 1
    adapters = [AdmittedAdapter(RequestLedger(client), 15) for _ in range(2)]
    with patch("requests.adapters.HTTPAdapter.send", return_value=Response()):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda index: adapters[index % 2].send(request()), range(12)))
    assert len(results) == 12
    assert client.eval.call_count == 12
    assert len({call.args[2] for call in client.eval.call_args_list}) == 1


def test_configured_store_enables_common_admission_without_opt_in(monkeypatch):
    """Make every configured integrated session use shared accounting by default."""
    from src.foundation.support.refactors.initialize_mist_session import MistSessionConfigurator

    monkeypatch.delenv("WAN_SHARED_ADMISSION", raising=False)
    with (
        patch("src.foundation.persistence.db.DatabaseConfig.from_env", return_value=MagicMock(standalone_mode=False)),
        patch.object(RequestLedger, "connect", return_value=RequestLedger(MagicMock())),
    ):
        assert isinstance(MistSessionConfigurator._build_timeout_adapter(15), AdmittedAdapter)


def test_different_credentials_share_org_request_accounting():
    """Prevent two authentication values from bypassing one organization budget."""
    client = MagicMock()
    client.eval.return_value = 1
    first, second = request(), request()
    second.headers["Authorization"] = "Token second-independent-placeholder"
    ledger = RequestLedger(client)
    ledger.admit(first)
    ledger.admit(second)
    calls = client.eval.call_args_list
    assert calls[0].args[1] == 2
    assert calls[0].args[3] == calls[1].args[3] == "misthelper:api:v1:org:org-one"
    assert calls[0].args[2] != calls[1].args[2]


def test_configured_redis_outage_cannot_disable_automatic_admission(monkeypatch):
    """Keep outage refusal even when database DNS discovery reports standalone."""
    from src.foundation.support.refactors.initialize_mist_session import MistSessionConfigurator

    monkeypatch.delenv("WAN_SHARED_ADMISSION", raising=False)
    monkeypatch.delenv("MISTHELPER_STANDALONE", raising=False)
    monkeypatch.setenv("REDIS_HOST", "existing.invalid")
    with patch("src.foundation.persistence.db.DatabaseConfig.from_env", return_value=MagicMock(standalone_mode=True)):
        with pytest.raises(ConnectionError, match="configured Redis"):
            MistSessionConfigurator._build_timeout_adapter(15)


def test_hidden_sdk_transport_cannot_bypass_enabled_admission(monkeypatch):
    """Fail explicitly instead of continuing with an unaccounted network transport."""
    from types import SimpleNamespace

    from src.foundation.support.refactors.initialize_mist_session import MistSessionConfigurator

    monkeypatch.setenv("WAN_SHARED_ADMISSION", "true")
    with pytest.raises(ConnectionError, match="transport"):
        MistSessionConfigurator._configure_timeout(SimpleNamespace())


@pytest.mark.parametrize("execution", ["manual", "fetcher"])
def test_actual_sdk_normal_and_paginated_calls_reach_admitted_transport(execution):
    """Exercise the installed SDK and its real pager without any network request."""
    import mistapi
    from mistapi.api.v1.orgs.stats import searchOrgPeerPathStats

    from src.mist.access.api.api_data_fetcher import APIDataFetcher

    with patch.object(mistapi.APISession, "_load_env"):
        session = mistapi.APISession(show_cli_notif=False)
    session._cloud_uri = "api.invalid"
    session._authenticated = True
    session._session.headers["Authorization"] = "Token independent-test-placeholder"
    client = MagicMock()
    client.eval.return_value = 1
    session._session.mount("https://", AdmittedAdapter(RequestLedger(client, "org-one"), 15))
    first, second = Response(), Response()
    first.status_code = second.status_code = 200
    first._content = json.dumps(
        {"results": [{"id": "first"}], "next": "/api/v1/orgs/org-one/stats/peer_paths?page=2"}
    ).encode()
    second._content = json.dumps({"results": [{"id": "second"}]}).encode()
    with patch("requests.adapters.HTTPAdapter.send", side_effect=[first, second]) as send:
        if execution == "manual":
            response = searchOrgPeerPathStats(session, "org-one", duration="1h", limit=1)
            result = mistapi.get_all(session, response)
        else:
            resolver = MagicMock(apisession=session)
            resolver.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-one"
            resolver.RateLimitingUtils.get_rate_limited_delay.return_value = (0, 0)
            fetcher = APIDataFetcher("Independent test", searchOrgPeerPathStats, "unused", duration="1h", limit=1)
            with (
                patch("src.mist.access.api.api_data_fetcher.SourceDependencyResolver", resolver),
                patch.object(fetcher, "_export_and_display_data"),
            ):
                assert fetcher.execute() is True
            result = fetcher.rawdata
    session._session.close()
    assert result == [{"id": "first"}, {"id": "second"}]
    assert send.call_count == client.eval.call_count == 2
    assert {call.args[3] for call in client.eval.call_args_list} == {"misthelper:api:v1:org:org-one"}
