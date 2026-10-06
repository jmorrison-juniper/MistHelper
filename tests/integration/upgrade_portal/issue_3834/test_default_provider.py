"""Test the normal-startup request dependency provider."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest
from flask import Flask, jsonify

from src.interfaces.portals.upgrade_portal.runtime import identity


class FakeCollection:
    """Hold the ArangoDB operations used during graph construction."""

    def __init__(self) -> None:
        """Create one empty collection."""
        self.documents: dict[str, dict[str, Any]] = {}
        self.index_definitions: list[dict[str, Any]] = [{"type": "primary", "fields": ["_key"]}]

    def add_index(self, definition: dict[str, Any]) -> dict[str, Any]:
        """Record one idempotent index."""
        if not any(item.get("name") == definition.get("name") for item in self.index_definitions):
            self.index_definitions.append(dict(definition))
        return dict(definition)

    def indexes(self) -> list[dict[str, Any]]:
        """Return detached index definitions."""
        return list(self.index_definitions)

    def get(self, key: str) -> dict[str, Any] | None:
        """Read one stored document."""
        return self.documents.get(key)

    def insert(self, document: dict[str, Any], overwrite: bool = False) -> dict[str, Any]:
        """Store one document."""
        key = str(document.get("_key", ""))
        if key in self.documents and not overwrite:
            raise ValueError("The fake collection rejects a duplicate key.")
        self.documents[key] = dict(document)
        return dict(document)

    def update(self, document: dict[str, Any], merge: bool = True) -> dict[str, Any]:
        """Merge one document update."""
        key = str(document.get("_key", ""))
        current = dict(self.documents.get(key, {})) if merge else {}
        current.update(document)
        self.documents[key] = current
        return dict(current)


class FakeAql:
    """Return no records from an empty test database."""

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None) -> list[Any]:
        """Accept one query without external access."""
        del query, bind_vars
        return []


class FakeDatabase:
    """Hold isolated fake collections for one request."""

    def __init__(self) -> None:
        """Create an empty database."""
        self.collections: dict[str, FakeCollection] = {}
        self.aql = FakeAql()

    def has_collection(self, name: str) -> bool:
        """Report whether one collection exists."""
        return name in self.collections

    def create_collection(self, name: str) -> FakeCollection:
        """Create one collection."""
        collection = FakeCollection()
        self.collections[name] = collection
        return collection

    def collection(self, name: str) -> FakeCollection:
        """Return one existing collection."""
        return self.collections[name]


class FakeArangoClient:
    """Expose one request-owned fake database client."""

    instances: list[FakeArangoClient] = []

    def __init__(self, hosts: str, request_timeout: float) -> None:
        """Record one construction without opening a socket."""
        self.hosts = hosts
        self.request_timeout = request_timeout
        self.database = FakeDatabase()
        self.closed = False
        self.instances.append(self)

    def db(self, name: str, username: str, password: str, verify: bool = False) -> FakeDatabase:
        """Return the isolated database after verification."""
        del name, username, password
        if not verify:
            raise ValueError("The provider must verify the database.")
        return self.database

    def close(self) -> None:
        """Record request cleanup."""
        self.closed = True


class FakeCloudSession:
    """Provide the callable methods required by identity validation."""

    def __init__(self) -> None:
        """Create a session with no cloud behavior."""
        self.get = Mock(name="get")
        self.post = Mock(name="post")


class ProviderHarness:
    """Build a normal application with fake external construction boundaries."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Install the fake ArangoDB client."""
        import arango.client

        FakeArangoClient.instances = []
        monkeypatch.setenv("ARANGO_ROOT_PASSWORD", "fake-password")
        monkeypatch.setattr(arango.client, "ArangoClient", FakeArangoClient)

    @staticmethod
    def application() -> Flask:
        """Build the no-argument application and dependency probe."""
        from src.interfaces.portals.upgrade_portal.app import factory, wiring

        application = factory.create_app()

        def probe() -> Any:
            dependencies = wiring.request_dependencies()
            cached = wiring.request_dependencies()
            return jsonify(
                {
                    "actor": dependencies.operator.owner.actor_email,
                    "capture": type(dependencies.services.capture).__name__,
                    "cached": cached is dependencies,
                }
            )

        application.add_url_rule("/_test/dependencies", view_func=probe)
        return application

    @staticmethod
    def signed_client(application: Flask, email: str) -> tuple[Any, Any, FakeCloudSession]:
        """Create one signed browser and registry-owned cloud session."""
        cloud_session = FakeCloudSession()
        owner = identity.build_owner(email, identity.issue_browser_id())
        identity.SESSION_REGISTRY.register(
            identity.OperatorSession(
                owner=owner,
                cloud_session=cloud_session,
                credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
            )
        )
        client = application.test_client()
        client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
        with client.session_transaction() as browser_session:
            browser_session[identity.SESSION_OWNER_KEY] = owner.key
        return client, owner, cloud_session


def test_default_startup_builds_authenticated_request_graph(monkeypatch: pytest.MonkeyPatch) -> None:
    """Normal startup builds real services only inside a signed request."""
    harness = ProviderHarness(monkeypatch)
    application = harness.application()
    assert FakeArangoClient.instances == []
    client, owner, session = harness.signed_client(application, "operator@example.invalid")
    try:
        response = client.get("/_test/dependencies")
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)
    assert response.status_code == 200
    assert response.get_json() == {
        "actor": owner.actor_email,
        "cached": True,
        "capture": "CaptureService",
    }
    assert len(FakeArangoClient.instances) == 1
    assert FakeArangoClient.instances[0].closed is True
    assert session.get.call_count == 0
    assert session.post.call_count == 0


def test_explicit_service_override_avoids_production_construction(monkeypatch: pytest.MonkeyPatch) -> None:
    """An explicit test service wins without identity or database access."""
    harness = ProviderHarness(monkeypatch)
    application = harness.application()
    stand_in = object()
    application.config["CAPTURE_SERVICE"] = stand_in
    with application.test_request_context("/"):
        from src.interfaces.portals.upgrade_portal.app.wiring import request_service

        assert request_service("CAPTURE_SERVICE", "capture") is stand_in
    assert FakeArangoClient.instances == []
