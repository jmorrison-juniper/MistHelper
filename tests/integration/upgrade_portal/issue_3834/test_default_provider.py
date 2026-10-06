"""Exercise default request wiring with the real portal services."""

from __future__ import annotations  # Keep annotations independent from import order.

from typing import Any  # Fake external interfaces receive mixed document values.
from unittest.mock import Mock  # Fake database writers record resource cleanup.

import pytest  # The test runner provides safe monkeypatch restoration.
from flask import Flask, jsonify  # The provider probe runs inside a real Flask request.

from src.interfaces.portals.upgrade_portal.runtime import identity  # Use the real signed-owner registry.


class ProviderDoubles:
    """Provide strict storage and session doubles for the request provider."""

    class Aql:
        """Return no dangling capture edges during the real bootstrap."""

        def execute(self, query: str, bind_vars: dict[str, Any] | None = None) -> list[Any]:
            """Answer one bound query without a database server."""
            del query, bind_vars  # The empty test database has no edges to repair.
            return []  # No live document-store call occurs.

    class Collection:
        """Keep the collection operations used by bootstrap and verification."""

        def __init__(self, name: str, edge: bool = False) -> None:
            """Create one empty fake collection."""
            self.name = name  # The real key is the collection name.
            self.documents: dict[str, dict[str, Any]] = {}  # Store only fake test rows.
            self.index_definitions: list[dict[str, Any]] = [{"type": "edge"}] if edge else []

        def add_index(self, definition: dict[str, Any]) -> dict[str, Any]:
            """Record one idempotent index definition."""
            if not any(entry.get("name") == definition.get("name") for entry in self.index_definitions):
                self.index_definitions.append(dict(definition))  # Keep an isolated copy of the driver input.
            return dict(definition)  # Match the driver result shape.

        def indexes(self) -> list[dict[str, Any]]:
            """Return the index definitions that the bootstrap can verify."""
            return list(self.index_definitions)  # Do not expose the mutable internal list.

        def get(self, key: str) -> dict[str, Any] | None:
            """Read one natural key from the fake collection."""
            return self.documents.get(key)  # An absent key remains absent.

        def insert(self, document: dict[str, Any], overwrite: bool = False) -> dict[str, Any]:
            """Store one test document with the requested overwrite policy."""
            key = str(document.get("_key", ""))  # The driver keys each document by _key.
            if key in self.documents and not overwrite:
                raise ValueError("The fake collection rejects a duplicate key.")
            self.documents[key] = dict(document)  # Read-back uses a detached copy.
            return dict(document)  # Match the driver document result.

        def update(self, document: dict[str, Any], merge: bool = True) -> dict[str, Any]:
            """Apply one verified request update to a stored row."""
            key = str(document.get("_key", ""))  # The request uses the natural run key.
            current = dict(self.documents.get(key, {})) if merge else {}  # Match the driver's merge behavior.
            current.update(document)  # The fake stores the exact fields the request supplied.
            self.documents[key] = current  # The later read-back sees this value.
            return dict(current)  # Match the driver return shape.

    class Database:
        """Own fake collections and an empty query interface."""

        def __init__(self) -> None:
            """Start with an empty isolated database."""
            self.collections: dict[str, ProviderDoubles.Collection] = {}  # A request owns this collection map.
            self.aql = ProviderDoubles.Aql()  # The bootstrap repair finds no edge rows.

        def has_collection(self, name: str) -> bool:
            """Report whether the fake database already holds a collection."""
            return name in self.collections  # The provider creates every missing name.

        def create_collection(self, name: str, edge: bool = False) -> ProviderDoubles.Collection:
            """Create one collection with its correct edge index shape."""
            collection = ProviderDoubles.Collection(name, edge)  # Keep collection type in the fake.
            self.collections[name] = collection  # The next check reads this same object.
            return collection  # Match the driver return shape.

        def collection(self, name: str) -> ProviderDoubles.Collection:
            """Return one existing collection or create a document collection."""
            if name not in self.collections:
                return self.create_collection(name)  # The action store asks for a named collection.
            return self.collections[name]  # Return the request-owned collection.

    class ArangoClient:
        """Hold one fake client whose close call remains observable."""

        def __init__(self, hosts: str, request_timeout: float) -> None:
            """Store the safe constructor arguments."""
            self.hosts = hosts  # The host comes from a fake configuration.
            self.request_timeout = request_timeout  # The request owns the timeout value.
            self.database = ProviderDoubles.Database()  # Each client owns a distinct database.
            self.closed = False  # The teardown must change this field.

        def db(self, name: str, username: str, password: str, verify: bool = False) -> ProviderDoubles.Database:
            """Return the request database after accepting the real call shape."""
            del name, username, password  # Credentials remain inside the fake boundary.
            if not verify:
                raise ValueError("The provider must verify the document handle.")
            return self.database  # The returned handle belongs to this client.

        def close(self) -> None:
            """Record release of the request-owned client."""
            self.closed = True  # The lifecycle test checks one close per request.

    class Writer:
        """Stand in for one configured router backend without opening a socket."""

        instances: list[ProviderDoubles.Writer] = []
        database: ProviderDoubles.Database | None = None

        def __init__(self, config: Any) -> None:
            """Record one router-owned writer."""
            self.config = config  # Preserve the configured connection object.
            self.closed = False  # Teardown must close each request writer.
            self.instances.append(self)  # The test verifies owned-resource cleanup.

        def write(self, data: list[dict[str, Any]], collection_name: str, strategy: dict[str, Any]) -> Any:
            """Return one writer result with the real call signature."""
            from src.foundation.persistence.db.router import WriteResult

            del strategy  # The registered router resolves the same key before this writer call.
            if self.database is None:
                raise RuntimeError("The fake Arango database is unavailable.")
            collection = self.database.collection(collection_name)
            for document in data:
                collection.insert(document, overwrite=True)  # Make audit read-back observable.
            return WriteResult(True, "arangodb", len(data), 0)  # The result names durable fake writes.

        def close(self) -> None:
            """Record release of the request-owned backend."""
            self.closed = True  # The teardown test checks the close count.

    class CloudSession:
        """Hold callable Mist request methods and expose no credential."""

        def __init__(self) -> None:
            """Create a fresh session double."""
            self.get = Mock(name="get")  # No cloud request is made during graph creation.
            self.post = Mock(name="post")  # No cloud mutation is made during graph creation.
            self.closed = False  # The provider must not close this registry-owned object.

    def __init__(self) -> None:
        """Keep the clients and graphs created by one test."""
        self.clients: list[ProviderDoubles.ArangoClient] = []  # The test checks client teardown.
        self.dependencies: list[Any] = []  # The test inspects the graph before and after teardown.
        self.sessions: list[ProviderDoubles.CloudSession] = []  # The registry owns these sessions.
        self.barrier: Any = None  # A concurrency test installs a two-request barrier.
        self.Writer.instances = []  # Keep backend ownership local to this harness.
        self.writer_instances = self.Writer.instances  # Share one test-visible list of fake writers.

    def install(self, monkeypatch: pytest.MonkeyPatch, standalone: bool = False) -> None:
        """Patch only external construction boundaries."""
        from arango import client as arango_client_module  # The provider imports this constructor on request.

        from src.foundation.persistence.db import DatabaseConfig  # The environment reader is an external boundary.
        from src.foundation.persistence.db import router as router_module  # The router class stays real.
        from src.interfaces.portals.upgrade_portal.app import factory  # Factory imports only after traps are set.

        self.settings = factory.load_settings()  # One immutable record supplies matching fake hosts.
        config = DatabaseConfig(  # All values are test strings and no credential comes from the environment.
            arango_host=self.settings.arango.host,
            arango_database=self.settings.arango.database,
            arango_username=self.settings.arango.username,
            arango_password="fake-arango-password",
            redis_host=self.settings.redis.host,
            redis_port=self.settings.redis.port,
            redis_password="fake-redis-password",
            standalone_mode=standalone,
        )
        original_client = self.ArangoClient  # Keep the exact constructor for the observed client list.

        def build_client(hosts: str, request_timeout: float) -> ProviderDoubles.ArangoClient:
            """Build one fake document client with the installed SDK signature."""
            client = original_client(hosts, request_timeout)  # No socket opens in this constructor.
            self.Writer.database = client.database  # The request router writes into its matching fake database.
            self.clients.append(client)  # The teardown check owns this exact object.
            return client  # The provider receives a real-shaped client.

        monkeypatch.setattr(DatabaseConfig, "from_env", classmethod(lambda cls: config))
        monkeypatch.setattr(arango_client_module, "ArangoClient", build_client)
        monkeypatch.setattr(router_module, "ArangoDBWriter", self.Writer)
        monkeypatch.setattr(router_module, "RedisTimeSeriesWriter", self.Writer)
        monkeypatch.setattr(router_module, "RedisJSONWriter", self.Writer)

    def create_app(self) -> Flask:
        """Create the no-argument production application and a test probe."""
        from src.interfaces.portals.upgrade_portal.app import factory, wiring

        application = factory.create_app()  # The default factory stores only provider rules.

        def read_dependencies() -> Any:
            """Resolve the current graph inside this authenticated test request."""
            dependencies = wiring.request_dependencies()  # Exercise the real request provider.
            self.dependencies.append(dependencies)  # Keep the graph for isolation and cleanup assertions.
            if self.barrier is not None:
                self.barrier.wait(timeout=10)  # Hold both operators in the service graph at one time.
            return jsonify({"ready": True})  # The response carries no session or database value.

        def read_csrf_token() -> Any:
            """Issue one real Flask-WTF token for destructive route probes."""
            from flask_wtf.csrf import generate_csrf

            return jsonify({"token": generate_csrf()})  # The token stays in the signed test browser session.

        application.add_url_rule("/_test/request-dependencies", view_func=read_dependencies)
        application.add_url_rule("/_test/csrf-token", view_func=read_csrf_token)
        return application  # The test drives the app through Flask's signed session.

    def signed_client(self, application: Flask, email: str) -> tuple[Any, Any]:
        """Register one real operator record and build its signed browser client."""
        cloud_session = self.CloudSession()  # Each owner receives a separate SDK session.
        owner = identity.build_owner(email, identity.issue_browser_id())  # The owner uses a unique browser key.
        record = identity.OperatorSession(
            owner=owner,
            cloud_session=cloud_session,
            credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
        )
        identity.SESSION_REGISTRY.register(record)  # The real provider reads the registry.
        self.sessions.append(cloud_session)  # The test verifies the provider never closes it.
        client = application.test_client()  # Each operator receives a separate cookie jar.
        client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # The cookie binds this browser.
        with client.session_transaction() as browser_session:  # Flask signs the owner key in the test cookie.
            browser_session[identity.SESSION_OWNER_KEY] = owner.key  # No cloud session enters the cookie.
        return client, owner  # The caller removes the registry entry after its request.


def test_default_factory_builds_and_closes_one_authenticated_graph(monkeypatch: pytest.MonkeyPatch) -> None:
    """Normal startup defers resources until an authenticated request."""
    from src.foundation.persistence.db.router import DatabaseRouter
    from src.interfaces.portals.upgrade_portal.audit.logger import AuditLogger

    harness = ProviderDoubles()  # One holder records the request-owned fakes.
    harness.install(monkeypatch)  # No production database, Redis, or Mist boundary is available.
    application = harness.create_app()  # The no-argument factory uses the production provider.
    client, owner = harness.signed_client(application, "operator.one@example.invalid")
    try:  # Always remove the process registry record after the test.
        response = client.get("/_test/request-dependencies")  # The request creates its own complete graph.
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # Do not leak one fake operator into another test.
    dependencies = harness.dependencies[0]  # The route stored only its local dependency graph.
    assert response.status_code == 200  # The authenticated provider built every required dependency.
    assert type(dependencies.services.capture).__name__ == "CaptureService"  # The real capture service is used.
    assert type(dependencies.services.upgrade).__name__ == "UpgradeService"  # The real upgrade service is used.
    assert type(dependencies.services.settle).__name__ == "SettleGateService"  # The real settle service is used.
    assert type(dependencies.services.comparison).__name__ == "ComparisonService"
    assert dependencies.services.comparison.settle_gate_service is dependencies.services.settle  # One shared graph.
    assert isinstance(dependencies.resources.database_router, DatabaseRouter)  # The actual router contract is used.
    assert isinstance(dependencies.resources.audit_logger, AuditLogger)  # Audit uses its actual implementation.
    assert dependencies.resources.database is harness.clients[0].database  # The explicit handle stays separate.
    assert dependencies.services.capture.mist_client is harness.sessions[0]  # The operator session stays request-local.
    assert harness.clients[0].closed is True  # Teardown closes the owned Arango client.
    assert all(writer.closed for writer in harness.writer_instances)  # Teardown closes each router writer.
    assert harness.sessions[0].closed is False  # The registry, not the request, owns the Mist session.


def test_upgrade_submission_uses_supported_sdk_after_verified_intent(monkeypatch: pytest.MonkeyPatch) -> None:
    """The default upgrade service checks versions and stores intent before Mist submission."""
    from types import SimpleNamespace  # Create exact SDK response shapes without network traffic.

    import mistapi.api.v1.orgs.inventory as inventory_api  # The real options reader owns this API call.
    import mistapi.api.v1.sites.devices as devices_api  # The real plan runner owns these API calls.

    from src.interfaces.portals.upgrade_portal.capture import store  # Patch only the durable storage boundary.

    harness = ProviderDoubles()  # Record every request-owned database and session.
    harness.install(monkeypatch)  # The provider uses strict fakes instead of production clients.
    application = harness.create_app()  # The no-argument factory uses request-owned services.
    client, owner = harness.signed_client(application, "operator@corp.local")
    session = harness.sessions[0]  # Every real service call must use this operator session.
    events: list[str] = []  # Verify durable intent precedes firmware submission.
    inventory_answer = SimpleNamespace(
        status_code=200,
        data=[{"mac": "001122334455", "name": "ap-one", "type": "ap", "model": "AP32", "version": "1.0.0"}],
        headers={"X-Page-Total": "1", "X-Page-Limit": "1000"},
        next=None,
    )
    version_answer = SimpleNamespace(
        status_code=200,
        data=[{"model": "AP32", "version": "2.0.0"}],
        headers={"X-Page-Total": "1", "X-Page-Limit": "1000"},
        next=None,
    )
    upgrade_answer = SimpleNamespace(status_code=200, data={"upgrade_id": "upgrade-3834"})
    sessions: list[Any] = []  # The fake endpoint record proves request ownership.

    def inventory_call(mist_session: Any, org_id: str, **kwargs: Any) -> Any:
        """Return one complete logical-device inventory page."""
        sessions.append(mist_session)  # Record the exact borrowed session.
        assert org_id == "00000000-0000-0000-0000-0000000000aa"  # Keep the organization scope exact.
        assert kwargs["site_id"] == "00000000-0000-0000-0000-0000000000bb"  # Keep the site scope exact.
        return inventory_answer  # The production reader validates the page shape.

    def version_call(mist_session: Any, site_id: str, type: str | None = None, model: str | None = None) -> Any:
        """Return the supported firmware version for the model."""
        sessions.append(mist_session)  # Record the exact borrowed session.
        assert type == "ap"  # The SDK call must name the device type.
        assert model == "AP32"  # The SDK call must name the model.
        return version_answer  # The production reader validates the version row.

    def upgrade_call(mist_session: Any, site_id: str, body: dict[str, Any]) -> Any:
        """Accept one site upgrade through the installed SDK endpoint."""
        events.append("cloud")  # This call must follow durable run storage.
        sessions.append(mist_session)  # Record the exact borrowed session.
        assert len(body["device_ids"]) == 1  # The request names only its selected device.
        assert body["device_ids"][0].endswith("001122334455")  # Mist requires the UUID form of its MAC address.
        return upgrade_answer  # The production SDK seam reads the upgrade identifier.

    def write_run(document: dict[str, Any], database: Any = None) -> Any:
        """Verify the initial run through an isolated collection boundary."""
        events.append("store")  # The call order must put this before the cloud mutation.
        database.collection("upgrade_runs").insert(document, overwrite=True)  # Store only the test record.
        return SimpleNamespace(verified=True, backup_written=False, reason="")  # Match StoreResult.

    monkeypatch.setattr(inventory_api, "getOrgInventory", inventory_call)
    monkeypatch.setattr(devices_api, "listSiteAvailableDeviceVersions", version_call)
    monkeypatch.setattr(devices_api, "upgradeSiteDevices", upgrade_call)
    monkeypatch.setattr(store, "write_run", write_run)
    csrf = client.get("/_test/csrf-token").get_json()["token"]  # Preserve the active CSRF guard.
    try:  # Keep the registered operator active through the confirmed mutation request.
        response = client.post(
            "/api/runs/run-3834/upgrade/start",
            json={
                "org_id": "00000000-0000-0000-0000-0000000000aa",
                "site_id": "00000000-0000-0000-0000-0000000000bb",
                "device_ids": ["001122334455"],
                "firmware_version": "2.0.0",
                "strategy": "parallel",
                "rollback_enabled": False,
                "confirm": "CONFIRM",
            },
            headers={"X-CSRFToken": csrf},
        )
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # The registry outlives the test client.
    stored = harness.clients[0].database.collection("upgrade_runs").get("run-3834")
    assert response.status_code == 202  # The supported cloud call accepted the confirmed request.
    assert response.get_json()["status"] == "pending"  # The route keeps its documented response fields.
    assert events.index("store") < events.index("cloud")  # Durable intent precedes each firmware mutation.
    assert sessions and all(call_session is session for call_session in sessions)  # No other session reaches Mist.
    assert stored["upgrades"][0]["upgrade_id"] == "upgrade-3834"  # The accepted cloud ID is durable.
