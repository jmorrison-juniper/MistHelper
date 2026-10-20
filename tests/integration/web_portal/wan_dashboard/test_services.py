"""Test the WAN dashboard data service without live Mist requests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from threading import Lock
from unittest.mock import MagicMock

import pytest
import redis
import requests

from src.interfaces.portals.wan_dashboard import services
from src.interfaces.portals.wan_dashboard.services import (
    MistSessionRunner,
    RedisDashboardCache,
    WanDashboardService,
    WanDataNormalizer,
)


class FakeResponse:
    """Hold one local SDK response and an optional next-page marker."""

    def __init__(self, status_code: int, data: object, next_page: str | None = None) -> None:
        """Store the response fields used by the service."""
        self.status_code = status_code  # Keep the HTTP result visible to the collector.
        self.data = data  # Supply only synthetic records.
        self.next = next_page  # Name the next page without performing network I/O.


class FakeCache:
    """Store cache entries and record the configured time to live."""

    def __init__(self) -> None:
        """Create an empty in-memory cache for one test."""
        self.values: dict[str, object] = {}  # Keep all state local to this test.
        self.writes: list[tuple[str, object, int]] = []  # Record each write and expiry.

    def get(self, key: str) -> object | None:
        """Return one local cache entry when it exists."""
        return self.values.get(key)  # Model a cache miss without an external service.

    def set(self, key: str, value: object, ttl: int) -> None:
        """Store one local value and its configured expiry."""
        self.values[key] = value  # Make later reads observe this successful value.
        self.writes.append((key, value, ttl))  # Record the bounded lifetime for the assertion.


class FakeMistSession:
    """Expose safe local attributes that the SDK session clone requires."""

    def __init__(self) -> None:
        """Create a cookie-free session with no live token."""
        self._apitoken: list[str] = []  # Keep this fixture free of credentials.
        self._apitoken_index = -1  # No token is active in the local fixture.
        self._session = requests.Session()  # Provide mutable request state without sending traffic.
        self._MAX_429_RETRIES = 3  # Prove that the feature clone sets its own one-pass limit.
        self._token_lock = Lock()  # Match the SDK lock used by its request wrapper.


@pytest.fixture(autouse=True)
def block_live_http(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject network access so every service test stays offline."""

    def refuse_request(*_args: object, **_kwargs: object) -> None:
        """Fail immediately if a test reaches the Requests transport."""
        raise AssertionError("WAN dashboard tests must not send live HTTP requests.")  # Stop a network escape.

    monkeypatch.setattr(requests.sessions.Session, "request", refuse_request)  # Guard SDK transport calls.


@pytest.fixture
def service() -> tuple[WanDashboardService, FakeCache]:
    """Return a service with a fake session and an in-memory cache."""
    cache = FakeCache()  # Keep cache state local to this test.
    dashboard_service = WanDashboardService(FakeMistSession(), "org-local", cache=cache)  # Use only local state.
    return dashboard_service, cache  # Expose cache writes for the TTL checks.


class TestSiteCollection:
    """Prove that site reads preserve complete pages and cache policy."""

    def test_site_pages_are_complete_and_cached_for_five_minutes(
        self, monkeypatch: pytest.MonkeyPatch, service: tuple[WanDashboardService, FakeCache]
    ) -> None:
        """The collector reads every page and caches the complete result."""
        dashboard_service, cache = service  # Read the local service and its cache.
        first_page = FakeResponse(200, [{"id": "site-a"}], "/sites?page=2")  # Model the first result page.
        second_page = FakeResponse(200, [{"id": "site-b"}])  # Model the last result page.
        list_sites = MagicMock(return_value=first_page)  # Record the explicit Mist SDK call.
        monkeypatch.setattr(services.mistapi.api.v1.orgs.sites, "listOrgSites", list_sites)  # Replace Mist.
        monkeypatch.setattr(services.mistapi, "get_next", MagicMock(return_value=second_page))  # Replace paging.

        result = dashboard_service.get_sites()  # Collect all pages through the service boundary.
        cached_result = dashboard_service.get_sites()  # Reuse the successful cached response.

        assert result["status"] == "ok"  # A complete valid result is successful.
        assert result["data"] == [{"id": "site-a"}, {"id": "site-b"}]  # Both pages remain available.
        assert cached_result == result  # The second read uses the successful cache entry.
        list_sites.assert_called_once()  # The SDK request must occur once.
        assert list_sites.call_args.args[1:] == ("org-local",)  # Keep the organization argument explicit.
        assert list_sites.call_args.kwargs == {"limit": 1000}  # Keep pagination bounded.
        assert list_sites.call_args.args[0] is not dashboard_service._session  # The call uses an isolated clone.
        assert cache.writes[0][0].startswith("wan-dashboard:v1:")  # Use the feature cache namespace.
        assert cache.writes[0][2] == 300  # Keep the source five-minute site-list lifetime.

    def test_failed_later_page_does_not_return_partial_success(
        self, monkeypatch: pytest.MonkeyPatch, service: tuple[WanDashboardService, FakeCache]
    ) -> None:
        """A later page failure cannot make the first page look complete."""
        dashboard_service, _cache = service  # Read the local service.
        first_page = FakeResponse(200, [{"id": "site-a"}], "/sites?page=2")  # Model one valid first page.
        failed_page = FakeResponse(503, {"error": "offline"})  # Model the failed second page.
        monkeypatch.setattr(services.mistapi.api.v1.orgs.sites, "listOrgSites", MagicMock(return_value=first_page))
        monkeypatch.setattr(services.mistapi, "get_next", MagicMock(return_value=failed_page))

        result = dashboard_service.get_sites()  # Read both pages through the SDK pagination helper.

        assert result["status"] == "error"  # The service reports the failed page.
        assert result["data"] == []  # The first page is not a success-shaped partial result.
        assert "503" in result["notice"]  # The operator-facing status includes the HTTP result.

    def test_profile_and_template_cache_entries_live_for_ten_minutes(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service: tuple[WanDashboardService, FakeCache],
    ) -> None:
        """Both optional configuration records use the documented ten-minute TTL."""
        dashboard_service, cache = service  # Read the local service and cache.
        profile = FakeResponse(200, {"id": "profile-a"})  # Supply one synthetic device profile.
        template = FakeResponse(200, {"id": "template-a"})  # Supply one synthetic gateway template.
        monkeypatch.setattr(
            services.mistapi.api.v1.orgs.deviceprofiles,
            "getOrgDeviceProfile",
            MagicMock(return_value=profile),
        )  # Replace the profile API.
        monkeypatch.setattr(
            services.mistapi.api.v1.orgs.gatewaytemplates,
            "getOrgGatewayTemplate",
            MagicMock(return_value=template),
        )  # Replace the template API.

        dashboard_service._cached_entity(
            "profiles", "profile-a", services.mistapi.api.v1.orgs.deviceprofiles.getOrgDeviceProfile, "org-local"
        )  # Read the profile through the feature boundary.
        dashboard_service._cached_entity(
            "templates", "template-a", services.mistapi.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate, "org-local"
        )  # Read the template through the feature boundary.

        assert [write[2] for write in cache.writes] == [600, 600]  # Keep the two cache expiries bounded.


class TestCacheAndRateLimits:
    """Prove that cache failures and rate limits remain visible."""

    def test_cache_key_uses_the_org_and_record_namespace(self, service: tuple[WanDashboardService, FakeCache]) -> None:
        """Site cache keys include the feature and organization boundaries."""
        dashboard_service, cache = service  # Read the local service and cache.
        cache.values["wan-dashboard:v1:sites:org-local"] = [{"id": "site-a"}]  # Seed a valid cache entry.

        result = dashboard_service.get_sites()  # Read without reaching the SDK.

        assert result["data"] == [{"id": "site-a"}]  # The matching organization uses its own cached rows.
        assert cache.writes == []  # A cache hit does not rewrite the entry.

    @pytest.mark.parametrize(
        "request_error",
        [requests.Timeout("synthetic timeout"), requests.ConnectionError("synthetic connection failure")],
        ids=["timeout", "connection-error"],
    )
    def test_transport_errors_return_explicit_error_instead_of_empty_success(
        self, request_error: requests.RequestException, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A timeout or connection failure is not converted into a valid empty site list."""
        dashboard_service = WanDashboardService(  # Exercise the production request path.
            FakeMistSession(),  # Keep authentication local to the test.
            "org-local",  # Use the synthetic organization.
            cache=FakeCache(),  # Avoid a Redis service dependency.
        )
        list_sites = MagicMock(side_effect=request_error)  # Model an offline Mist call.
        monkeypatch.setattr(
            services.mistapi.api.v1.orgs.sites, "listOrgSites", list_sites
        )  # Replace the cloud call with a local failure.

        result = dashboard_service.get_sites()  # Exercise the collector error boundary.

        assert result["status"] == "error"  # Keep transport errors distinct from success.
        assert result["data"] == []  # The empty list does not imply successful collection.
        assert type(request_error).__name__.lower() in result["notice"].lower()  # Name the transport failure.

    @pytest.mark.parametrize("status_code", [403, 500])
    def test_http_failures_keep_the_status_without_returning_body(
        self,
        status_code: int,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Mist client and server errors stay explicit and do not expose response bodies."""
        dashboard_service = WanDashboardService(  # Exercise the production request path.
            FakeMistSession(),  # Keep authentication local to the test.
            "org-local",  # Use the synthetic organization.
            cache=FakeCache(),  # Avoid a Redis service dependency.
        )
        response = FakeResponse(status_code, {"error": "private Mist response body"})  # Model a failed API call.
        list_sites = MagicMock(return_value=response)  # Keep the SDK call local.
        monkeypatch.setattr(services.mistapi.api.v1.orgs.sites, "listOrgSites", list_sites)

        result = dashboard_service.get_sites()  # Exercise the normal service error boundary.

        assert result["status"] == "error"  # Do not convert a failed request to an empty success.
        assert str(status_code) in result["notice"]  # Keep the HTTP status available to the operator.
        assert "private Mist response body" not in result["notice"]  # Do not disclose source error bodies.

    def test_empty_sdk_body_is_not_reported_as_empty_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An empty SDK body remains malformed, not a valid empty site list."""
        dashboard_service = WanDashboardService(  # Exercise the production request path.
            FakeMistSession(),  # Keep authentication local to the test.
            "org-local",  # Use the synthetic organization.
            cache=FakeCache(),  # Avoid a Redis service dependency.
        )
        response = FakeResponse(200, b"")  # Model an empty successful HTTP response.
        list_sites = MagicMock(return_value=response)  # Keep the SDK call local.
        monkeypatch.setattr(
            services.mistapi.api.v1.orgs.sites, "listOrgSites", list_sites
        )  # Replace the cloud call with an empty response.

        result = dashboard_service.get_sites()  # Validate the empty response body.

        assert result["status"] == "error"  # Reject an empty response body.
        assert result["data"] == []  # Do not present it as a successful empty organization.
        assert "malformed_response" in result["notice"]  # Name the invalid response shape.

    def test_stale_sites_remain_visible_after_a_rate_limit(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service: tuple[WanDashboardService, FakeCache],
    ) -> None:
        """A later 429 keeps the last complete site list with a stale status."""
        dashboard_service, cache = service  # Read the local service and cache.
        list_sites = MagicMock(
            side_effect=[
                FakeResponse(200, [{"id": "site-a", "name": "Site A"}]),
                FakeResponse(429, {"error": "rate limited"}),
            ]
        )  # Model one success followed by a token limit.
        monkeypatch.setattr(services.mistapi.api.v1.orgs.sites, "listOrgSites", list_sites)

        current = dashboard_service.get_sites()  # Save one complete response.
        cache.values.pop("wan-dashboard:v1:sites:org-local")  # Force a new SDK read without clearing stale data.
        stale = dashboard_service.get_sites()  # Read again after the API rate limit.

        assert current["status"] == "ok"  # The initial response is current.
        assert stale["status"] == "stale"  # The later response identifies old data.
        assert stale["data"] == current["data"]  # Retain the last complete rows.
        assert stale["stale"] is True  # Expose stale state to the browser.

    def test_malformed_site_payload_is_not_reported_as_empty(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service: tuple[WanDashboardService, FakeCache],
    ) -> None:
        """A success status with an invalid payload is a data error."""
        dashboard_service, _cache = service  # Read the local service.
        monkeypatch.setattr(
            services.mistapi.api.v1.orgs.sites,
            "listOrgSites",
            MagicMock(return_value=FakeResponse(200, {"results": ["not a row"]})),
        )  # Supply a malformed row without making a live request.

        result = dashboard_service.get_sites()  # Validate the returned page shape.

        assert result["status"] == "error"  # Reject malformed content.
        assert "malformed_response" in result["notice"]  # Name the data failure.


class TestCacheOnlyReads:
    """Prove portal read methods use only complete cached snapshots."""

    def test_cached_overview_filters_without_calling_any_approved_sdk_read(
        self, monkeypatch: pytest.MonkeyPatch, service: tuple[WanDashboardService, FakeCache]
    ) -> None:
        """A dashboard cache read uses no Mist operation and preserves scoped rows."""
        dashboard_service, cache = service  # Read the isolated service and in-memory cache.
        key = "wan-dashboard:v1:overview:org-local:last-success"  # Use the existing complete overview key.
        cache.values[key] = [  # Supply only fictional records from the active organization.
            {"device_id": "gw-a", "site_id": "site-a", "name": "North gateway", "site_name": "North"},
            {"device_id": "gw-b", "site_id": "site-b", "name": "South gateway", "site_name": "South"},
        ]
        sdk_reads = (  # Name the four approved bulk reads that routes must not invoke.
            (services.mistapi.api.v1.orgs.sites, "listOrgSites"),
            (services.mistapi.api.v1.orgs.stats, "listOrgDevicesStats"),
            (services.mistapi.api.v1.orgs.stats, "searchOrgSwOrGwPorts"),
            (services.mistapi.api.v1.orgs.inventory, "getOrgInventory"),
        )
        spies = [MagicMock(side_effect=AssertionError("cache read called Mist")) for _ in sdk_reads]
        for (module, name), spy in zip(sdk_reads, spies, strict=True):
            monkeypatch.setattr(module, name, spy)  # Fail if the cache-only method reaches a Mist SDK read.

        result = dashboard_service.get_cached_overview(site_id="site-a", search="north")

        assert result["status"] == "stale"  # Legacy cache entries have no verified collection timestamp.
        assert result["data"] == [
            {"device_id": "gw-a", "site_id": "site-a", "name": "North gateway", "site_name": "North"}
        ]  # Filters apply to the cached complete organization snapshot.
        assert all(spy.call_count == 0 for spy in spies)  # Prove that the cache read made zero Mist SDK calls.
        assert cache.writes == []  # Read-only routes do not publish or refresh snapshots.

    def test_process_local_snapshot_expires_after_the_stale_ttl(
        self, service: tuple[WanDashboardService, FakeCache]
    ) -> None:
        """A process-local complete value cannot outlive the fixed maximum snapshot age."""
        dashboard_service, _cache = service  # Use a local service without Redis.
        key = "wan-dashboard:v1:overview:org-local"  # Match the organization overview cache key.
        dashboard_service._last_success[key] = [{"device_id": "gw-a"}]  # Seed one complete fictional snapshot.
        dashboard_service._last_success_at[key] = datetime.now(UTC) - timedelta(seconds=86401)

        result = dashboard_service.get_cached_overview()

        assert result["status"] == "unavailable"  # Expired memory data must not appear as stale or current.
        assert result["data"] == []  # Do not return any record after the maximum age.
        assert key not in dashboard_service._last_success  # Remove the expired value from process memory.

    def test_redis_miss_uses_only_a_recent_process_local_snapshot(
        self, service: tuple[WanDashboardService, FakeCache]
    ) -> None:
        """A recent complete process-local snapshot remains visible as stale during Redis loss."""
        dashboard_service, _cache = service  # Use a cache adapter that returns no shared value.
        key = "wan-dashboard:v1:overview:org-local"  # Match the organization overview cache key.
        dashboard_service._last_success[key] = [{"device_id": "gw-a", "site_id": "site-a"}]
        dashboard_service._last_success_at[key] = datetime.now(UTC) - timedelta(seconds=300)

        result = dashboard_service.get_cached_overview()

        assert result["status"] == "stale"  # Redis absence cannot make local data current.
        assert result["data"] == [{"device_id": "gw-a", "site_id": "site-a"}]

    def test_malformed_overview_snapshot_is_unavailable_not_partial(
        self, service: tuple[WanDashboardService, FakeCache]
    ) -> None:
        """One malformed row invalidates the complete cached overview."""
        dashboard_service, cache = service  # Use only the in-memory cache.
        cache.values["wan-dashboard:v1:overview:org-local:last-success"] = [
            {"device_id": "gw-a"},
            "malformed row",
        ]  # Model one invalid record in an otherwise valid snapshot.

        result = dashboard_service.get_cached_overview()

        assert result["status"] == "unavailable"  # Reject the whole cache value rather than return partial data.
        assert result["data"] == []  # Never expose the valid-looking row beside malformed data.


class TestTokenRotation:
    """Prove one-pass token rotation and cooldown behavior."""

    def test_429_rotates_once_and_hashes_the_cooldown_key(self) -> None:
        """A limited first token yields to one remaining token without changing shared state."""
        session = FakeMistSession()  # Keep SDK state local to this test.
        session._apitoken = ["synthetic-token-a", "synthetic-token-b"]  # Use non-production credentials.
        cache = FakeCache()  # Record shared cooldown values without Redis.
        runner = MistSessionRunner(session, "org-local", cache)  # Exercise the production runner.
        function = MagicMock(side_effect=[FakeResponse(429, {}), FakeResponse(200, {"ok": True})])

        response, failure = runner.call(function, session, "org-local")  # Try each available token once.

        assert failure is None  # The second authorized token succeeds.
        assert response.data == {"ok": True}  # Return only the successful SDK response.
        assert function.call_count == 2  # Never retry either token within the request.
        first_session = function.call_args_list[0].args[0]  # Inspect the first isolated SDK session.
        second_session = function.call_args_list[1].args[0]  # Inspect the second isolated SDK session.
        assert first_session._MAX_429_RETRIES == 0  # Disable hidden SDK retries on the clone.
        assert first_session._apitoken == ["synthetic-token-a"]  # Bind the first attempt to one token.
        assert second_session._apitoken == ["synthetic-token-b"]  # Rotate to the next configured token.
        assert "synthetic-token-a" not in cache.writes[0][0]  # Store only a token fingerprint in Redis.
        assert cache.writes[0][1] is True  # Shared storage holds only a cooldown marker.
        assert cache.writes[0][2] == 60  # Enforce the documented sixty-second cooldown.
        assert session._session.headers.get("Authorization") is None  # Keep shared session headers unchanged.
        assert runner._available_tokens() == ["synthetic-token-b"]  # Honor the first token's cooldown.

    def test_all_tokens_enter_cooldown_without_a_followup_attempt(self) -> None:
        """A later request stops when every configured token is cooling down."""
        session = FakeMistSession()  # Keep SDK state local to this test.
        session._apitoken = ["synthetic-token-a", "synthetic-token-b"]  # Use non-production credentials.
        cache = FakeCache()  # Share only hashed cooldown keys within the test.
        runner = MistSessionRunner(session, "org-local", cache)  # Exercise the production runner.
        function = MagicMock(return_value=FakeResponse(429, {}))  # Rate-limit each distinct token.

        response, failure = runner.call(function, session, "org-local")  # Use each token once.
        retry_response, retry_failure = runner.call(function, session, "org-local")  # Check the active cooldown.

        assert response is None  # No 429 response becomes a success payload.
        assert failure == "rate_limited"  # Identify the cause when all tokens are limited.
        assert retry_response is None  # Do not send another request during the cooldown.
        assert retry_failure == "rate_limited"  # Keep the later state explicit.
        assert function.call_count == 2  # The follow-up call sends no request.
        assert len(cache.writes) == 2  # Store one shared cooldown for each token.
        assert all(write[2] == 60 for write in cache.writes)  # Keep every token cooldown at sixty seconds.


class TestDataValidation:
    """Prove malformed identifiers and metric arrays remain safe."""

    def test_foreign_port_is_rejected_before_metric_request(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service: tuple[WanDashboardService, FakeCache],
    ) -> None:
        """An in-scope gateway cannot be used to query an unknown port."""
        dashboard_service, _cache = service  # Read the local service.
        monkeypatch.setattr(
            dashboard_service,
            "get_overview",
            MagicMock(
                return_value={
                    "status": "ok",
                    "data": [
                        {
                            "device_id": "gateway-a",
                            "site_id": "site-a",
                            "ports": [{"port_id": "wan0"}],
                        }
                    ],
                }
            ),
        )  # Avoid Mist calls while checking the organization boundary.

        gateway, error = dashboard_service._resolve_gateway(
            "gateway-a", "wan1", "24h", WanDataNormalizer.TRAFFIC_SECONDS
        )  # Ask to resolve a port absent from the authorized gateway.

        assert gateway == {}  # Do not return gateway data for a rejected port.
        assert error["status"] == "forbidden"  # Do not call the metrics API with a guessed port.

    def test_foreign_gateway_is_rejected_before_device_request(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service: tuple[WanDashboardService, FakeCache],
    ) -> None:
        """A gateway absent from the authorized overview does not reach a site endpoint."""
        dashboard_service, _cache = service  # Read the local service.
        monkeypatch.setattr(
            dashboard_service,
            "get_overview",
            MagicMock(return_value={"status": "ok", "data": []}),
        )  # Model an organization that does not contain the requested gateway.
        get_device = MagicMock(return_value=FakeResponse(200, {"id": "gateway-foreign"}))
        monkeypatch.setattr(services.mistapi.api.v1.sites.devices, "getSiteDevice", get_device)

        result = dashboard_service.get_gateway_ports("gateway-foreign")  # Request a foreign device identifier.

        assert result["status"] == "forbidden"  # Hide foreign gateway existence.
        get_device.assert_not_called()  # Check scope before a site-specific SDK call.

    def test_overview_joins_all_gateway_pages_before_filtering(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service: tuple[WanDashboardService, FakeCache],
    ) -> None:
        """The overview keeps later gateway pages and applies search after pagination."""
        dashboard_service, cache = service  # Read the local service and cache.
        cache.values["wan-dashboard:v1:sites:org-local"] = [
            {"id": "site-a", "name": "Alpha"},
            {"id": "site-b", "name": "Beta"},
        ]  # Seed the authorized site names without a Mist call.
        first_page = FakeResponse(
            200,
            [{"id": "gateway-a", "site_id": "site-a", "mac": "aa:00", "name": "Alpha router"}],
            "/devices?page=2",
        )  # Model the first gateway page.
        second_page = FakeResponse(
            200,
            [{"id": "gateway-b", "site_id": "site-b", "mac": "bb:00", "name": "Beta router"}],
        )  # Model a gateway that appears only on the later page.
        monkeypatch.setattr(
            services.mistapi.api.v1.orgs.stats,
            "listOrgDevicesStats",
            MagicMock(return_value=first_page),
        )  # Replace the gateway statistics request.
        monkeypatch.setattr(
            services.mistapi,
            "get_next",
            MagicMock(return_value=second_page),
        )  # Replace Mist pagination.
        monkeypatch.setattr(
            services.mistapi.api.v1.orgs.stats,
            "searchOrgSwOrGwPorts",
            MagicMock(
                return_value=FakeResponse(
                    200,
                    [
                        {"mac": "aa:00", "port_id": "wan0", "port_usage": "wan"},
                        {"mac": "bb:00", "port_id": "wan1", "port_usage": "wan"},
                    ],
                )
            ),
        )  # Supply one WAN port for each gateway.
        monkeypatch.setattr(
            services.mistapi.api.v1.orgs.inventory,
            "getOrgInventory",
            MagicMock(return_value=FakeResponse(200, [])),
        )  # Supply no optional profile references.

        result = dashboard_service.get_overview(search="beta")

        assert result["status"] == "ok"  # The complete filtered result remains successful.
        assert [row["device_id"] for row in result["data"]] == ["gateway-b"]  # Search sees the second page.
        assert result["data"][0]["wan_port_count"] == 1  # The WAN port total joins by MAC.


class TestRedisDashboardCache:
    """Prove cache behavior remains bounded when Redis is missing or faulty."""

    def test_cache_reads_and_writes_json_with_an_expiry(self) -> None:
        """The shared client receives JSON values and the caller's TTL."""
        client = MagicMock()  # Replace Redis with a local client double.
        client.get.return_value = b'{"ready":true}'  # Supply one encoded cache record.
        cache = RedisDashboardCache(client)  # Use the production cache adapter.

        result = cache.get("wan-dashboard:v1:sites:org-local")  # Decode a shared value.
        cache.set("wan-dashboard:v1:sites:org-local", {"ready": True}, 300)  # Store one expiring value.

        assert result == {"ready": True}  # Return the decoded JSON object.
        client.set.assert_called_once_with(
            "wan-dashboard:v1:sites:org-local", '{"ready":true}', ex=300
        )  # Apply the requested expiry.

    def test_missing_redis_client_and_invalid_json_fail_open(self) -> None:
        """An absent or malformed cache entry falls through to Mist reads."""
        absent_cache = RedisDashboardCache(None)  # Model the shared Redis service as unavailable.
        client = MagicMock()  # Supply a local Redis client double.
        client.get.return_value = b"bad json"  # Model a corrupted optional cache entry.
        invalid_cache = RedisDashboardCache(client)  # Use the production cache adapter.

        assert absent_cache.get("key") is None  # Preserve the no-cache path.
        assert invalid_cache.get("key") is None  # Do not return malformed cache content.

    def test_cache_client_errors_do_not_stop_read_only_service(self) -> None:
        """Redis faults do not hide the dashboard's Mist-backed fallback."""
        client = MagicMock()  # Replace Redis with a local client double.
        client.get.side_effect = redis.RedisError("synthetic failure")  # Model a disconnected cache.
        client.set.side_effect = redis.RedisError("synthetic failure")  # Model a failed cache write.
        cache = RedisDashboardCache(client)  # Use the production cache adapter.

        assert cache.get("key") is None  # Fall through to a direct safe read.
        cache.set("key", {"row": 1}, 30)  # Keep cache write failures non-fatal.
        client.set.assert_called_once()  # Prove that the adapter attempted the write.


class TestWanDataNormalizer:
    """Prove validation and normalization preserve source data safely."""

    def test_identifiers_numeric_values_and_page_envelopes(self) -> None:
        """The normalizer accepts valid source values and rejects malformed values."""
        assert WanDataNormalizer.identifier("gateway-a")  # Accept a safe gateway identifier.
        assert not WanDataNormalizer.identifier("../gateway")  # Reject path traversal.
        assert WanDataNormalizer.identifier("wan/0", port=True)  # Accept an encoded source port name.
        assert WanDataNormalizer.numeric(1.5) == 1.5  # Preserve finite non-negative counters.
        assert WanDataNormalizer.numeric(True) is None  # Do not treat booleans as metric values.
        assert WanDataNormalizer.numeric(float("nan")) is None  # Reject non-finite measurements.
        assert WanDataNormalizer.rows({"results": [{"id": "site-a"}]}) == [{"id": "site-a"}]
        assert WanDataNormalizer.rows({"results": ["invalid"]}) is None  # Reject malformed list members.

    def test_port_and_hourly_rows_keep_missing_values_unavailable(self) -> None:
        """Port and hourly normalization retain valid values and missing fields."""
        ports = WanDataNormalizer.port_rows(
            [
                {
                    "port_id": "wan0",
                    "port_usage": "wan",
                    "speed": 1000,
                    "wan_name": "Broadband",
                    "description": "Primary circuit",
                    "enabled": True,
                    "gateway": "192.0.2.1",
                    "ip": "192.0.2.10",
                    "netmask": 24,
                    "override": "no",
                }
            ],
            {"port_config": {"wan0": {"name": "Primary", "type": "wan", "vlan_id": 42}}},
            {"wan0": {"speed": 0, "rx_bytes": 5}},
        )  # Merge one local configuration and statistics row.
        hourly = WanDataNormalizer.hourly_rows(
            {
                "bandwidth": {"rx_bps": [1], "max_rx_bps": [2]},
                "link_health": {"avg_latency": [3]},
            },
            0,
        )  # Supply incomplete metrics for one UTC hour.

        assert ports[0]["name"] == "Primary"  # Keep the configured port label.
        assert ports[0]["wan_name"] == "Broadband"  # Preserve the source circuit label.
        assert ports[0]["enabled"] is True  # Preserve port administration state.
        assert ports[0]["gateway"] == "192.0.2.1"  # Preserve the peer gateway address.
        assert ports[0]["ip"] == "192.0.2.10"  # Preserve the local WAN address.
        assert ports[0]["netmask"] == 24  # Preserve the configured prefix length.
        assert ports[0]["override"] == "no"  # Preserve the source override state.
        assert ports[0]["vlan_id"] == 42  # Preserve the configured VLAN identifier.
        assert ports[0]["speed"] == 0.0  # Preserve an explicit zero live counter.
        assert ports[0]["tx_bytes"] is None  # Do not invent a missing counter.
        assert hourly[0]["hour_iso"] == "1970-01-01T00:00:00Z"  # Keep UTC export timestamps.
        assert hourly[0]["rx_bps"] == 1.0  # Normalize supplied metric arrays.
        assert hourly[0]["tx_bps"] is None  # Keep missing series unavailable.

    def test_port_enablement_uses_link_state_and_admin_override(self) -> None:
        """The source marks only up and administratively enabled ports as enabled."""
        ports = WanDataNormalizer.port_rows(
            [
                {"port_id": "wan0", "port_usage": "wan", "up": True},
                {"port_id": "wan1", "port_usage": "wan", "up": False},
            ],
            {"port_config": {"wan0": {"disabled": True}, "wan1": {"disabled": False}}},
            {},
        )

        assert ports[0]["enabled"] is False  # An administrative disable overrides a live link.
        assert ports[1]["enabled"] is False  # A down interface remains disabled in the source view.

    def test_malformed_nested_insight_data_produces_safe_unavailable_values(self) -> None:
        """Malformed optional SLE data does not crash insight response shaping."""
        insight = WanDashboardService._application_health(
            {
                "summary": {"sle": {"samples": None}},
                "threshold": None,
                "impacted": "invalid",
            }
        )  # Supply malformed nested values from a synthetic API response.

        assert insight == {
            "summary_pct": None,
            "threshold_pct": None,
            "trend": [],
            "impacted_interfaces": [],
        }  # Keep every unavailable metric explicit.

    def test_application_health_trend_uses_weighted_scores_and_utc_buckets(self) -> None:
        """The source trend reports weighted hourly scores with source timestamps."""
        insight = WanDashboardService._application_health(
            {
                "summary": {
                    "start": 1_700_000_000,
                    "interval": 1800,
                    "sle": {"samples": {"total": [10, 20, 0], "degraded": [1, 4, 0], "value": [90, 80, 50]}},
                },
                "threshold": {"threshold": 95},
                "impacted": [],
            },
            start=1_699_999_000,
        )

        assert insight["summary_pct"] == 83.33  # Weight the summary by source sample counts.
        assert insight["trend"] == [
            {"timestamp": 1_700_000_000, "pct": 90.0},
            {"timestamp": 1_700_001_800, "pct": 80.0},
        ]  # Skip empty buckets and retain the documented interval.


class TestGatewayAndInsightFlows:
    """Prove the detail, traffic, insights, and export service workflows."""

    def test_gateway_details_join_configuration_stats_and_peers(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service: tuple[WanDashboardService, FakeCache],
    ) -> None:
        """An authorized gateway returns its configuration, counters, and peer paths."""
        dashboard_service, _cache = service  # Read the local service.
        gateway = {
            "device_id": "gateway-a",
            "site_id": "site-a",
            "mac": "aa:00",
            "ports": [{"port_id": "wan0", "port_usage": "wan"}],
        }  # Supply a previously authorized gateway.
        monkeypatch.setattr(
            dashboard_service,
            "get_overview",
            MagicMock(return_value={"status": "ok", "data": [gateway]}),
        )  # Keep gateway scope local.
        monkeypatch.setattr(
            dashboard_service,
            "_read_one",
            MagicMock(
                side_effect=[
                    ({"port_config": {"wan0": {"name": "Primary"}}}, None),
                    ({"port_stat": {"wan0": {"rx_bytes": 8}}}, None),
                ]
            ),
        )  # Supply local device configuration and counters.
        monkeypatch.setattr(
            dashboard_service,
            "_read_all",
            MagicMock(return_value=([{"port_id": "wan0", "vpn_name": "Peer A"}], None)),
        )  # Supply one synthetic peer path.

        result = dashboard_service.get_gateway_ports("gateway-a")

        assert result["status"] == "ok"  # The complete detail sources succeed.
        assert result["data"]["ports"][0]["name"] == "Primary"  # Keep the device configuration.
        assert result["data"]["ports"][0]["rx_bytes"] == 8.0  # Keep the live counter.
        assert result["data"]["peers_by_port"]["wan0"][0]["vpn_name"] == "Peer A"

    def test_gateway_detail_failures_return_available_rows_as_partial(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service: tuple[WanDashboardService, FakeCache],
    ) -> None:
        """Failed detail sources do not erase organization-level WAN port rows."""
        dashboard_service, _cache = service  # Read the local service.
        gateway = {
            "device_id": "gateway-a",
            "site_id": "site-a",
            "ports": [{"port_id": "wan0", "port_usage": "wan"}],
        }  # Supply one valid overview record.
        monkeypatch.setattr(
            dashboard_service,
            "get_overview",
            MagicMock(return_value={"status": "ok", "data": [gateway]}),
        )  # Keep gateway scope local.
        monkeypatch.setattr(
            dashboard_service,
            "_read_one",
            MagicMock(side_effect=[(None, "http_500"), (None, "http_503")]),
        )  # Model failed device and statistics reads.
        monkeypatch.setattr(
            dashboard_service,
            "_read_all",
            MagicMock(return_value=([], "http_500")),
        )  # Model an unavailable peer-path page.

        result = dashboard_service.get_gateway_ports("gateway-a")

        assert result["status"] == "partial"  # Expose the unavailable sources.
        assert result["data"]["ports"][0]["port_id"] == "wan0"  # Retain the overview port row.
        assert result["notice"] == "Some gateway details are unavailable."  # Name the unavailable data sources.

    def test_traffic_uses_ten_minute_buckets_and_retains_stale_samples(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service: tuple[WanDashboardService, FakeCache],
    ) -> None:
        """Traffic requests use UTC samples and preserve the last result after a rate limit."""
        dashboard_service, _cache = service  # Read the local service.
        gateway = {"site_id": "site-a", "device_id": "gateway-a"}
        monkeypatch.setattr(
            dashboard_service,
            "_resolve_gateway",
            MagicMock(return_value=(gateway, None)),
        )  # Avoid organization network calls.
        request = MagicMock(
            side_effect=[
                (FakeResponse(200, {"timestamps": [0], "rx_bps": [1], "tx_bps": [2]}), None),
                (None, "rate_limited"),
            ]
        )  # Supply one success and one rate-limit response.
        monkeypatch.setattr(dashboard_service, "_request", request)

        current = dashboard_service.get_traffic("gateway-a", "wan0", "1h")
        stale = dashboard_service.get_traffic("gateway-a", "wan0", "1h")

        assert current["data"][0]["timestamp_utc"] == "1970-01-01T00:00:00+00:00"
        assert stale["status"] == "stale"  # Retain the last successful traffic sample.
        assert stale["data"] == current["data"]  # Keep the sample visible while the API is limited.
        assert request.call_args_list[0].kwargs["interval"] == "10m"  # Preserve the source chart granularity.

    def test_insights_combine_bandwidth_link_health_and_sle(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service: tuple[WanDashboardService, FakeCache],
    ) -> None:
        """The insight view combines source metrics and a valid SLE percentage."""
        dashboard_service, _cache = service  # Read the local service.
        gateway = {"site_id": "site-a", "device_id": "gateway-a"}
        monkeypatch.setattr(
            dashboard_service,
            "_resolve_gateway",
            MagicMock(return_value=(gateway, None)),
        )  # Keep organization scope local.
        monkeypatch.setattr(
            dashboard_service,
            "_gateway_insights",
            MagicMock(
                return_value=(
                    {"rx_bps": [10], "max_rx_bps": [12], "tx_bps": [20], "max_tx_bps": [22]},
                    None,
                )
            ),
        )  # Supply synthetic bandwidth values.
        monkeypatch.setattr(
            dashboard_service,
            "_link_insights",
            MagicMock(return_value=({"avg_jitter": [2], "avg_latency": [5], "avg_loss": [1]}, None)),
        )  # Supply synthetic link-health values.
        monkeypatch.setattr(
            dashboard_service,
            "_sle_insights",
            MagicMock(
                return_value=(
                    {
                        "summary": {"sle": {"samples": {"total": [10], "degraded": [2], "value": [80]}}},
                        "threshold": {"threshold": 90},
                        "impacted": [{"interface": "wan0"}],
                    },
                    None,
                )
            ),
        )  # Supply synthetic Application Health data.

        result = dashboard_service.get_insights("gateway-a", "wan0", "24h")

        assert result["status"] == "ok"  # All insight sources are available.
        assert result["data"]["hourly"][0]["max_rx_bps"] == 12.0  # Preserve bandwidth peaks.
        assert result["data"]["hourly"][0]["avg_latency_ms"] == 5.0  # Preserve link health.
        assert result["data"]["application_health"]["summary_pct"] == 80.0
        assert result["data"]["application_health"]["threshold_pct"] == 90.0

    def test_insight_rate_limit_returns_the_last_complete_view(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service: tuple[WanDashboardService, FakeCache],
    ) -> None:
        """A rate limit after one complete insight response returns stale data."""
        dashboard_service, _cache = service  # Read the local service.
        gateway = {"site_id": "site-a", "device_id": "gateway-a"}
        monkeypatch.setattr(
            dashboard_service,
            "_resolve_gateway",
            MagicMock(return_value=(gateway, None)),
        )  # Keep organization scope local.
        monkeypatch.setattr(
            dashboard_service,
            "_gateway_insights",
            MagicMock(return_value=({"rx_bps": [1]}, None)),
        )  # Supply successful bandwidth data.
        monkeypatch.setattr(
            dashboard_service,
            "_link_insights",
            MagicMock(return_value=({}, None)),
        )  # Supply successful link data.
        monkeypatch.setattr(
            dashboard_service,
            "_sle_insights",
            MagicMock(return_value=({}, None)),
        )  # Supply successful SLE data.
        current = dashboard_service.get_insights("gateway-a", "wan0", "24h")
        monkeypatch.setattr(
            dashboard_service,
            "_gateway_insights",
            MagicMock(return_value=({}, "rate_limited")),
        )  # Model the next request reaching the cooldown.
        monkeypatch.setattr(
            dashboard_service,
            "_link_insights",
            MagicMock(return_value=({}, "rate_limited")),
        )  # Keep every source inside the same cooldown.
        monkeypatch.setattr(
            dashboard_service,
            "_sle_insights",
            MagicMock(return_value=({}, "rate_limited")),
        )  # Keep the final source rate-limited.

        stale = dashboard_service.get_insights("gateway-a", "wan0", "24h")

        assert stale["status"] == "stale"  # Keep the complete earlier view.
        assert stale["data"] == current["data"]  # Do not replace it with empty arrays.

    def test_foreign_gateway_is_rejected_before_device_request(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service: tuple[WanDashboardService, FakeCache],
    ) -> None:
        """A gateway absent from the authorized overview does not reach a site endpoint."""
        dashboard_service, _cache = service  # Read the local service.
        monkeypatch.setattr(
            dashboard_service,
            "get_overview",
            MagicMock(return_value={"status": "ok", "data": []}),
        )  # Model an organization that does not contain the requested gateway.
        get_device = MagicMock(return_value=FakeResponse(200, {"id": "gateway-foreign"}))
        monkeypatch.setattr(services.mistapi.api.v1.sites.devices, "getSiteDevice", get_device)

        result = dashboard_service.get_gateway_ports("gateway-foreign")  # Request a foreign device identifier.

        assert result["status"] == "forbidden"  # Hide foreign gateway existence.
        get_device.assert_not_called()  # Check scope before a site-specific SDK call.

    def test_overview_joins_all_gateway_pages_before_filtering(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service: tuple[WanDashboardService, FakeCache],
    ) -> None:
        """The overview keeps later gateway pages and applies search after pagination."""
        dashboard_service, cache = service  # Read the local service and cache.
        cache.values["wan-dashboard:v1:sites:org-local"] = [
            {"id": "site-a", "name": "Alpha"},
            {"id": "site-b", "name": "Beta"},
        ]  # Seed the authorized site names without a Mist call.
        first_page = FakeResponse(
            200,
            [{"id": "gateway-a", "site_id": "site-a", "mac": "aa:00", "name": "Alpha router"}],
            "/devices?page=2",
        )  # Model the first gateway page.
        second_page = FakeResponse(
            200,
            [{"id": "gateway-b", "site_id": "site-b", "mac": "bb:00", "name": "Beta router"}],
        )  # Model a gateway that appears only on the later page.
        monkeypatch.setattr(
            services.mistapi.api.v1.orgs.stats,
            "listOrgDevicesStats",
            MagicMock(return_value=first_page),
        )  # Replace the gateway statistics request.
        monkeypatch.setattr(
            services.mistapi,
            "get_next",
            MagicMock(return_value=second_page),
        )  # Replace Mist pagination.
        monkeypatch.setattr(
            services.mistapi.api.v1.orgs.stats,
            "searchOrgSwOrGwPorts",
            MagicMock(
                return_value=FakeResponse(
                    200,
                    [
                        {"mac": "aa:00", "port_id": "wan0", "port_usage": "wan"},
                        {"mac": "bb:00", "port_id": "wan1", "port_usage": "wan"},
                    ],
                )
            ),
        )  # Supply one WAN port for each gateway.
        monkeypatch.setattr(
            services.mistapi.api.v1.orgs.inventory,
            "getOrgInventory",
            MagicMock(return_value=FakeResponse(200, [])),
        )  # Supply no optional profile references.

        result = dashboard_service.get_overview(search="beta")

        assert result["status"] == "ok"  # The complete filtered result remains successful.
        assert [row["device_id"] for row in result["data"]] == ["gateway-b"]  # Search sees the second page.
        assert result["data"][0]["wan_port_count"] == 1  # The WAN port total joins by MAC.

    def test_malformed_metric_series_and_epoch_values_are_omitted(self) -> None:
        """A malformed array or timestamp cannot crash traffic normalization."""
        samples = WanDataNormalizer.traffic_samples(
            {"timestamps": [0, 253402300800], "rx_bps": "not-an-array", "tx_bps": [2, 3]},
            0,
            600,
        )  # Mix invalid source shapes with an out-of-range epoch.

        assert samples == [
            {
                "timestamp": 0,
                "timestamp_utc": "1970-01-01T00:00:00+00:00",
                "rx_bps": None,
                "tx_bps": 2.0,
            }
        ]


def test_gateway_and_port_inputs_are_checked_before_sdk_calls(
    monkeypatch: pytest.MonkeyPatch, service: tuple[WanDashboardService, FakeCache]
) -> None:
    """Malformed identifiers stop before the service can call the Mist SDK."""
    dashboard_service, _cache = service  # Read the local service.
    sdk_call = MagicMock(return_value=FakeResponse(200, []))  # Record any accidental external call.
    monkeypatch.setattr(services.mistapi.api.v1.orgs.sites, "listOrgSites", sdk_call)

    result = dashboard_service.get_gateway_ports("bad identifier")  # Supply a value outside the safe allow-list.

    assert result["status"] == "invalid"  # The service rejects malformed input.
    assert result["data"] == []  # Invalid input has no data result.
    sdk_call.assert_not_called()  # Validation happens before any SDK request.
