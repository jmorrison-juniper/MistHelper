"""Tests for the Mist API client exception boundaries."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import Mock

import pytest
from flask import Flask

from src.upgrade_portal.api.mist_client import MistAPIClient
from src.upgrade_portal.app.routes.mist import create_mist_routes


def test_list_sites_missing_sdk_endpoint_reaches_the_route_caller() -> None:
    """A missing SDK method must not become a benign site-read failure."""
    mist_api = Mock()  # Build a Mist stand-in that owns the site endpoint call.
    redis_cache = Mock()  # Build a cache stand-in so the method reaches the SDK path.
    redis_cache.get.return_value = None  # Force a cache miss before the SDK call.
    mist_api.listOrgSites.side_effect = AttributeError("listOrgSites is absent")  # Model a broken SDK surface.
    client = MistAPIClient(mist_api_client=mist_api, redis_cache=redis_cache)  # Build the product client.

    with pytest.raises(AttributeError, match="listOrgSites is absent"):  # Prove the fault is no longer hidden.
        client.list_sites("org-123")  # Drive the route-facing client method.


def test_list_site_devices_missing_sdk_endpoint_reaches_the_route_caller() -> None:
    """A missing SDK method must not become a benign device-read failure."""
    mist_api = Mock()  # Build a Mist stand-in that owns the device endpoint call.
    redis_cache = Mock()  # Build a cache stand-in so the method reaches the SDK path.
    redis_cache.get.return_value = None  # Force a cache miss before the SDK call.
    mist_api.listSiteDevices.side_effect = AttributeError("listSiteDevices is absent")  # Model SDK drift.
    client = MistAPIClient(mist_api_client=mist_api, redis_cache=redis_cache)  # Build the product client.

    with pytest.raises(AttributeError, match="listSiteDevices is absent"):  # Prove the caller sees the fault.
        client.list_site_devices("site-123")  # Drive the route-facing client method.


def test_get_cache_unexpected_runtime_error_reaches_the_route_caller() -> None:
    """An unexpected cache bug must not become a silent cache miss."""
    redis_cache = Mock()  # Build the Redis stand-in that owns the get call.
    redis_cache.get.side_effect = RuntimeError("cache shim bug")  # Model a code defect, not a Redis fault.
    client = MistAPIClient(redis_cache=redis_cache)  # Build the product client with only the cache seam.

    with pytest.raises(RuntimeError, match="cache shim bug"):  # Prove the defect is no longer hidden.
        client._get_cache("sites:org-123")  # Drive the cache parser directly.


def test_set_cache_unexpected_runtime_error_reaches_the_route_caller() -> None:
    """An unexpected cache write bug must not become a false cache failure."""
    redis_cache = Mock()  # Build the Redis stand-in that owns the setex call.
    redis_cache.setex.side_effect = RuntimeError("cache write shim bug")  # Model a code defect.
    client = MistAPIClient(redis_cache=redis_cache)  # Build the product client with only the cache seam.

    with pytest.raises(RuntimeError, match="cache write shim bug"):  # Prove the defect is no longer hidden.
        client._set_cache("sites:org-123", [{"id": "site-1"}], 300)  # Drive the cache writer directly.


def test_empty_cache_body_is_a_cache_miss() -> None:
    """An empty Redis body must not become a false cache row."""
    redis_cache = Mock()  # Build the Redis stand-in that owns the get call.
    redis_cache.get.return_value = b""  # Model an empty response body from the cache.
    client = MistAPIClient(redis_cache=redis_cache)  # Build the product client with only the cache seam.

    assert client._get_cache("sites:org-123") is None  # Prove the empty body becomes a miss.


def test_malformed_cache_json_is_a_cache_miss() -> None:
    """Malformed JSON in Redis must not become a false cache row."""
    redis_cache = Mock()  # Build the Redis stand-in that owns the get call.
    marker = json.JSONDecodeError.__name__  # Name the parser failure class that the cache reader handles.
    redis_cache.get.return_value = f"{{not valid {marker}"  # Model a malformed JSON cache body.
    client = MistAPIClient(redis_cache=redis_cache)  # Build the product client with only the cache seam.

    assert client._get_cache("sites:org-123") is None  # Prove json.JSONDecodeError becomes a cache miss.


def _mist_route_client(mist_client: Mock | None = None) -> Any:
    """Return a Flask test client for the Mist route wrapper."""
    app = Flask(__name__)  # Build the minimal Flask app for this route boundary.
    app.register_blueprint(create_mist_routes(mist_client=mist_client))  # Install the product route wrapper.
    return app.test_client()  # Return the test client that drives HTTP status paths.


def test_missing_org_id_returns_client_error_status() -> None:
    """The route caller maps a missing organization to HTTP 400."""
    mist_client = Mock()  # Build a client stand-in that must not receive a call.
    client = _mist_route_client(mist_client)  # Build the route wrapper around the stand-in.

    response = client.get("/api/sites")  # Omit the required organization query value.

    assert response.status_code == 400  # Prove the client-error status path.
    assert response.get_json()["error"] == "org_id is required"  # Prove the exact refusal text.
    mist_client.list_sites.assert_not_called()  # Prove validation stopped before the Mist client.


def test_missing_mist_client_returns_server_error_status() -> None:
    """The route caller maps a missing Mist client to HTTP 503."""
    client = _mist_route_client(None)  # Build the route wrapper without a Mist client.

    response = client.get("/api/sites", query_string={"org_id": "org-123"})  # Send a syntactically valid request.

    assert response.status_code == 503  # Prove the server-error status path.
    assert response.get_json()["error"] == "Mist API client not available"  # Prove the exact refusal text.
