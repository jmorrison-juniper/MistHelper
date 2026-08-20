"""Contract test for ``GET /readyz`` of the upgrade capture portal.

Why:
    ``GET /healthz`` reports that the process is alive. ``GET /readyz`` reports
    that the dependencies answer. The two endpoints must stay different, because
    an orchestrator restarts a process that fails the first check and only
    removes a process from the load balancer when it fails the second one.

    The contract is ``specs/1823-upgrade-capture-portal/contracts/http-api.md``
    section 7. That section requires a real write and a real read-back against a
    scratch key, because a check that only opens a connection reports ready
    while every write fails silently. Issue #1824 records that defect.

    No test below needs an ArangoDB server or a Redis server. Each test replaces
    the two connection helpers with a stand-in, so the suite proves the behavior
    of the endpoint and never the behavior of a store.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from types import ModuleType
from typing import Any

import pytest
from flask.testing import FlaskClient

from src.upgrade_portal.app import factory

# WHY: The contract names this exact path. A constant keeps every request on it.
READY_PATH = "/readyz"

# WHY: The contract allows these three keys and no more. An extra key would leak
# a fact the probe must not learn, and a missing key would break a probe parser.
EXPECTED_KEYS = {"status", "database", "redis"}

# WHY: The contract fixes these words. A test asserts on a word, never on a
# sentence, so a wording change cannot break an orchestrator probe.
READY_WORD = "ready"
NOT_READY_WORD = "not_ready"
STORE_OK = "ok"
STORE_DOWN = "unreachable"

# WHY: The two status codes the contract names for this path.
READY_STATUS = 200
NOT_READY_STATUS = 503

# WHY: A readiness body must name the store that failed and nothing else. Each
# string below would name a host, a port, or a credential. The body carries the
# store name only, so an operator reads which store to repair and learns no
# address. `store._safe_host` exists for the same reason.
FORBIDDEN_SUBSTRINGS = ("password", "token", "secret", "://", "@", "8529", "6379", "arangodb", "127.0.0.1")

# WHY: Readiness is a read. Every method below changes state, so the path must
# refuse it with the documented status.
STATE_CHANGING_METHODS = ("POST", "PUT", "DELETE", "PATCH")
METHOD_REFUSED_STATUS = 405

# WHY: An invented fault. A real fault class would agree with a store fault by
# accident and would prove nothing about the guard inside the probe.
SAMPLE_FAULT = RuntimeError("The stand-in store refused the call.")


class FakeArangoCollection:
    """In-memory stand-in for one ArangoDB collection.

    Why:
        The probe writes one document and reads the same key back. A dishonest
        stand-in accepts the write and stores nothing, which is the exact
        failure that issue #1824 describes. One flag switches between the two
        behaviors, so one class covers both cases.
    """

    def __init__(self, *, honest: bool = True) -> None:
        """Create the collection.

        Args:
            honest: True keeps a written document. False drops it silently.
        """
        self.documents: dict[str, dict[str, Any]] = {}  # WHY: Holds each stored document by key.
        self.honest = honest  # WHY: False reproduces a write that reports success and lands nowhere.
        self.writes = 0  # WHY: Counts the writes, so a test can prove the probe wrote at all.
        self.mode: str | None = None  # WHY: Records the write mode the probe chose.

    def insert(self, document: dict[str, Any], overwrite_mode: str | None = None) -> dict[str, Any]:
        """Store one document.

        Args:
            document: The document body, including the `_key` field.
            overwrite_mode: The write mode the probe asked for.

        Returns:
            The small answer that the real driver returns.
        """
        self.writes += 1  # WHY: Counted whether or not the write lands.
        self.mode = overwrite_mode  # WHY: A test reads the mode the probe chose.
        if self.honest:  # WHY: A dishonest collection reports success and stores nothing.
            self.documents[str(document["_key"])] = dict(document)  # WHY: A copy stops a later edit.
        return {"_key": document["_key"]}  # WHY: The real driver answers with the key.

    def get(self, key: str) -> dict[str, Any] | None:
        """Return one stored document.

        Args:
            key: The document key.

        Returns:
            The stored document, or None when the key is absent.
        """
        return self.documents.get(key)  # WHY: The read-back the probe checks.


class FakeArangoDatabase:
    """In-memory stand-in for the open ArangoDB handle.

    Why:
        The probe creates the scratch collection when it is absent, then writes
        and reads. This class gives those three calls with no server.
    """

    def __init__(self, *, honest: bool = True) -> None:
        """Create the database handle.

        Args:
            honest: True keeps a written document. False drops it silently.
        """
        self.collections: dict[str, FakeArangoCollection] = {}  # WHY: Holds each collection by name.
        self.honest = honest  # WHY: Passed to every collection this handle creates.
        self.created: list[str] = []  # WHY: Records each created name for one assertion.

    def has_collection(self, name: str) -> bool:
        """Report whether one collection exists.

        Args:
            name: The collection name.

        Returns:
            True when the collection exists.
        """
        return name in self.collections  # WHY: The probe creates the collection only when absent.

    def create_collection(self, name: str) -> FakeArangoCollection:
        """Create one collection.

        Args:
            name: The collection name.

        Returns:
            The new collection.
        """
        self.created.append(name)  # WHY: A test proves the probe used a scratch name.
        made = FakeArangoCollection(honest=self.honest)  # WHY: The handle sets the behavior of its parts.
        self.collections[name] = made  # WHY: A later read must find the same object.
        return made  # WHY: The real driver answers with the collection.

    def collection(self, name: str) -> FakeArangoCollection:
        """Return one existing collection.

        Args:
            name: The collection name.

        Returns:
            The collection.
        """
        return self.collections[name]  # WHY: The probe creates the collection before it asks for it.


class FakeLockStore:
    """In-memory stand-in for the Redis lock store client.

    Why:
        The probe writes one key with an expiry and reads it back. A dishonest
        stand-in models a read-only replica, which answers a ping and refuses
        every write.
    """

    def __init__(self, *, honest: bool = True) -> None:
        """Create the lock store client.

        Args:
            honest: True keeps a written key. False drops it silently.
        """
        self.values: dict[str, str] = {}  # WHY: Holds each stored value by key.
        self.honest = honest  # WHY: False reproduces a replica that refuses a write.
        self.expiries: list[int | None] = []  # WHY: A test proves the probe set an expiry.

    def set(self, key: str, value: str, ex: int | None = None) -> bool:
        """Store one key with an expiry.

        Args:
            key: The key name.
            value: The value to store.
            ex: The expiry in seconds.

        Returns:
            True, as the real client does.
        """
        self.expiries.append(ex)  # WHY: The scratch key must expire, or the probe leaks a key.
        if self.honest:  # WHY: A dishonest client reports success and stores nothing.
            self.values[key] = value  # WHY: The read-back then finds the value.
        return True  # WHY: The real client answers True after a write.

    def get(self, key: str) -> str | None:
        """Return one stored value.

        Args:
            key: The key name.

        Returns:
            The stored value, or None when the key is absent.
        """
        return self.values.get(key)  # WHY: The client decodes the answer, so this returns text.


@pytest.fixture
def store_module() -> ModuleType:
    """Return the capture store module.

    Why:
        The probe reads `connect_database` from this module at request time, so
        a test replaces the name on this exact object. The guarded import skips
        the test instead of failing collection while the module is being built.

    Returns:
        The imported capture store module.
    """
    return pytest.importorskip(  # WHY: Another lane may be writing this module.
        "src.upgrade_portal.capture.store",
        reason="The capture store module is not built yet.",
    )


@pytest.fixture
def lock_module() -> ModuleType:
    """Return the site lock module.

    Why:
        The probe reads `connect_lock_store` from this module at request time,
        for the same reason as the sibling fixture above.

    Returns:
        The imported site lock module.
    """
    return pytest.importorskip(  # WHY: Another lane may be writing this module.
        "src.upgrade_portal.runtime.lock",
        reason="The site lock module is not built yet.",
    )


def build_connect(answer: Any) -> Callable[[], Any]:
    """Build a stand-in connection helper.

    Why:
        A probe must survive three answers: an open handle, the value None, and
        a fault. One builder covers all three, so no test writes its own stub.

    Args:
        answer: The handle to return, None, or the fault to raise.

    Returns:
        A callable that takes no argument, as both real helpers do.
    """

    def connect() -> Any:
        """Answer as the real connection helper does."""
        if isinstance(answer, Exception):  # WHY: Models a helper that lets a fault escape.
            raise answer  # WHY: The probe must catch this and still answer.
        return answer  # WHY: An open handle, or None for a store that did not open.

    return connect  # WHY: The caller binds this over the real name.


def install_stores(
    monkeypatch: pytest.MonkeyPatch,
    modules: tuple[ModuleType, ModuleType],
    answers: tuple[Any, Any],
) -> None:
    """Replace both connection helpers for one test.

    Args:
        monkeypatch: The pytest patching surface.
        modules: The capture store module and the site lock module.
        answers: The document store answer and the lock store answer.
    """
    monkeypatch.setattr(modules[0], "connect_database", build_connect(answers[0]))  # WHY: The document store.
    monkeypatch.setattr(modules[1], "connect_lock_store", build_connect(answers[1]))  # WHY: The lock store.


def call_readiness(client: FlaskClient) -> tuple[int, dict[str, Any]]:
    """Call the readiness endpoint once and decode the answer.

    Args:
        client: The Flask test client.

    Returns:
        The status code and the decoded body.
    """
    response = client.get(READY_PATH)  # WHY: The contract allows a read on this path.
    return response.status_code, response.get_json()  # WHY: Every assertion below reads these two.


def test_ready_reports_both_stores_ok(
    portal_client: FlaskClient,
    store_module: ModuleType,
    lock_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both stores that accept a write make the portal ready."""
    install_stores(monkeypatch, (store_module, lock_module), (FakeArangoDatabase(), FakeLockStore()))
    status, body = call_readiness(portal_client)  # WHY: One call, then two assertions on it.
    assert status == READY_STATUS, f"A healthy portal must answer {READY_STATUS}, not {status}."
    assert body == {"status": READY_WORD, "database": STORE_OK, "redis": STORE_OK}, f"Wrong body: {body}."


def test_body_holds_the_contract_keys_only(
    portal_client: FlaskClient,
    store_module: ModuleType,
    lock_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The answer carries the three documented keys and no other key."""
    install_stores(monkeypatch, (store_module, lock_module), (FakeArangoDatabase(), FakeLockStore()))
    _, body = call_readiness(portal_client)  # WHY: The status has its own test above.
    assert set(body) == EXPECTED_KEYS, f"The body keys {set(body)} do not match {EXPECTED_KEYS}."


def test_document_store_down_names_the_database(
    portal_client: FlaskClient,
    store_module: ModuleType,
    lock_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A closed document store answers 503 and names the database key."""
    install_stores(monkeypatch, (store_module, lock_module), (None, FakeLockStore()))
    status, body = call_readiness(portal_client)  # WHY: The helper answers None for a closed store.
    assert status == NOT_READY_STATUS, f"A closed document store must answer {NOT_READY_STATUS}, not {status}."
    assert body["database"] == STORE_DOWN, f"The database reading must name the failure, not {body['database']}."
    assert body["redis"] == STORE_OK, f"The lock store answered, so its reading must stay ok, not {body['redis']}."
    assert body["status"] == NOT_READY_WORD, f"The summary word must be {NOT_READY_WORD}, not {body['status']}."


def test_lock_store_down_names_the_redis_key(
    portal_client: FlaskClient,
    store_module: ModuleType,
    lock_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A closed lock store answers 503 and names the redis key."""
    install_stores(monkeypatch, (store_module, lock_module), (FakeArangoDatabase(), None))
    status, body = call_readiness(portal_client)  # WHY: The helper answers None for a closed store.
    assert status == NOT_READY_STATUS, f"A closed lock store must answer {NOT_READY_STATUS}, not {status}."
    assert body["redis"] == STORE_DOWN, f"The redis reading must name the failure, not {body['redis']}."
    assert body["database"] == STORE_OK, "The document store answered, so its reading must stay ok."


def test_both_stores_down_name_both(
    portal_client: FlaskClient,
    store_module: ModuleType,
    lock_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two closed stores answer 503 and name both keys."""
    install_stores(monkeypatch, (store_module, lock_module), (None, None))
    status, body = call_readiness(portal_client)  # WHY: Neither store opened.
    assert status == NOT_READY_STATUS, f"Two closed stores must answer {NOT_READY_STATUS}, not {status}."
    assert body["database"] == STORE_DOWN, f"The database reading must name the failure, not {body['database']}."
    assert body["redis"] == STORE_DOWN, f"The redis reading must name the failure, not {body['redis']}."


def test_document_store_fault_never_raises(
    portal_client: FlaskClient,
    store_module: ModuleType,
    lock_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fault inside the document store helper answers 503, never 500."""
    install_stores(monkeypatch, (store_module, lock_module), (SAMPLE_FAULT, FakeLockStore()))
    status, body = call_readiness(portal_client)  # WHY: A probe that raises turns readiness into a 500.
    assert status == NOT_READY_STATUS, f"A store fault must answer {NOT_READY_STATUS}, not {status}."
    assert body["database"] == STORE_DOWN, f"The database reading must name the failure, not {body['database']}."


def test_lock_store_fault_never_raises(
    portal_client: FlaskClient,
    store_module: ModuleType,
    lock_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fault inside the lock store helper answers 503, never 500."""
    install_stores(monkeypatch, (store_module, lock_module), (FakeArangoDatabase(), SAMPLE_FAULT))
    status, body = call_readiness(portal_client)  # WHY: A probe that raises turns readiness into a 500.
    assert status == NOT_READY_STATUS, f"A store fault must answer {NOT_READY_STATUS}, not {status}."
    assert body["redis"] == STORE_DOWN, f"The redis reading must name the failure, not {body['redis']}."


def test_silent_document_write_reports_unreachable(
    portal_client: FlaskClient,
    store_module: ModuleType,
    lock_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A write that reports success and lands nowhere answers 503."""
    database = FakeArangoDatabase(honest=False)  # WHY: The exact failure that issue #1824 describes.
    install_stores(monkeypatch, (store_module, lock_module), (database, FakeLockStore()))
    status, body = call_readiness(portal_client)  # WHY: Only a read-back can catch this failure.
    assert database.collections[factory.PROBE_COLLECTION].writes == 1, "The probe must attempt one write."
    assert status == NOT_READY_STATUS, f"A silent write must answer {NOT_READY_STATUS}, not {status}."
    assert body["database"] == STORE_DOWN, f"The database reading must name the failure, not {body['database']}."


def test_silent_lock_write_reports_unreachable(
    portal_client: FlaskClient,
    store_module: ModuleType,
    lock_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A lock store that refuses a write answers 503 even though it answers."""
    client = FakeLockStore(honest=False)  # WHY: Models a read-only replica that still answers a ping.
    install_stores(monkeypatch, (store_module, lock_module), (FakeArangoDatabase(), client))
    status, body = call_readiness(portal_client)  # WHY: Only a read-back can catch this failure.
    assert status == NOT_READY_STATUS, f"A refused write must answer {NOT_READY_STATUS}, not {status}."
    assert body["redis"] == STORE_DOWN, f"The redis reading must name the failure, not {body['redis']}."


def test_probe_uses_a_scratch_collection_and_an_expiry(
    portal_client: FlaskClient,
    store_module: ModuleType,
    lock_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The probe writes to a scratch name and gives the lock key an expiry."""
    database = FakeArangoDatabase()  # WHY: The test reads the created names back.
    client = FakeLockStore()  # WHY: The test reads the expiry back.
    install_stores(monkeypatch, (store_module, lock_module), (database, client))
    call_readiness(portal_client)  # WHY: One call arms both records below.
    assert database.created == [factory.PROBE_COLLECTION], f"The probe created {database.created}."
    assert client.expiries == [factory.PROBE_LOCK_TTL_SECONDS], f"The probe set {client.expiries}."


def test_repeat_probes_write_a_fresh_value(
    portal_client: FlaskClient,
    store_module: ModuleType,
    lock_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each probe writes a new value, so a stale document cannot pass."""
    database = FakeArangoDatabase()  # WHY: The test reads the stored document after each call.
    install_stores(monkeypatch, (store_module, lock_module), (database, FakeLockStore()))
    call_readiness(portal_client)  # WHY: The first probe writes the first value.
    first = database.collections[factory.PROBE_COLLECTION].documents[factory.PROBE_KEY][factory.PROBE_FIELD]
    call_readiness(portal_client)  # WHY: The second probe must overwrite that value.
    second = database.collections[factory.PROBE_COLLECTION].documents[factory.PROBE_KEY][factory.PROBE_FIELD]
    assert first != second, f"Two probes wrote the same value {first}, so a stale document would pass."


def test_body_names_no_host_and_no_credential(
    portal_client: FlaskClient,
    store_module: ModuleType,
    lock_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The failing answer names the store and never an address or a secret."""
    install_stores(monkeypatch, (store_module, lock_module), (SAMPLE_FAULT, SAMPLE_FAULT))
    _, body = call_readiness(portal_client)  # WHY: The failing answer is the one that could leak.
    text = json.dumps(body).lower()  # WHY: One search covers every key and every value.
    found = [word for word in FORBIDDEN_SUBSTRINGS if word in text]  # WHY: Names each hit in the message.
    assert not found, f"The readiness body {text} holds the forbidden text {found}."


def test_answer_is_not_the_error_envelope(
    portal_client: FlaskClient,
    store_module: ModuleType,
    lock_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 503 answer stays a flat object and never becomes the error envelope."""
    install_stores(monkeypatch, (store_module, lock_module), (None, None))
    _, body = call_readiness(portal_client)  # WHY: The contract shows a flat object for both codes.
    assert "error" not in body, f"The readiness body must stay flat, not the error envelope: {body}."


@pytest.mark.parametrize("method", STATE_CHANGING_METHODS)
def test_readiness_refuses_a_state_changing_method(portal_client: FlaskClient, method: str) -> None:
    """The readiness path answers a read and refuses every other method.

    Args:
        portal_client: The Flask test client.
        method: The HTTP method under test.
    """
    response = portal_client.open(READY_PATH, method=method)  # WHY: No store stand-in is needed here.
    assert response.status_code == METHOD_REFUSED_STATUS, f"{method} must answer {METHOD_REFUSED_STATUS}."
