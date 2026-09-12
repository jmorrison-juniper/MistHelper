"""Contract test for ``GET /healthz`` of the upgrade capture portal.

Why:
    The container probe calls this endpoint many times each minute. The probe
    kills a worker process that stops answering, so the endpoint must answer
    from the process alone. A health answer that reads ArangoDB or Redis would
    report the portal unhealthy while a backing store hiccups, and the
    orchestrator would then kill a process that still serves every operator.
    This module proves the endpoint is independent of both stores.

    The contract is ``specs/1823-upgrade-capture-portal/contracts/http-api.md``
    section 7 and the shared rules in ``contracts/README.md``. Every assertion
    below comes from those two documents.
"""

from __future__ import annotations

import json
import re
import socket
from collections.abc import Iterator
from importlib.metadata import PackageNotFoundError
from types import ModuleType
from typing import Any

import arango
import arango.client
import pytest
import redis
from flask.testing import FlaskClient

from src.db import router as db_router
from src.upgrade_portal.app import factory
from src.upgrade_portal.capture import store

# WHY: The contract names this exact path. A constant keeps every request on it.
HEALTH_PATH = "/healthz"

# WHY: The contract allows two keys and no more. An extra key would leak a fact
# the probe must not learn, and a missing key would break the probe parser.
EXPECTED_KEYS = {"status", "version"}

# WHY: The contract fixes this word. A test asserts on the word, never on a
# sentence, so a wording change cannot break the probe.
EXPECTED_STATUS = "ok"

# WHY: The word the portal reports when no distribution is installed. The test
# states the literal instead of the constant, because the literal is the value
# on the wire and a constant rename must not change it silently.
UNKNOWN_VERSION_TEXT = "unknown"

# WHY: An obviously invented version. A real version would agree with the
# working copy by accident and would prove nothing.
SAMPLE_VERSION = "9.9.9-contract-sample"

# WHY: The rule at http-api.md line 358 allows a read only. Every other method
# changes state, so the portal must refuse it.
STATE_CHANGING_METHODS = ("POST", "PUT", "DELETE", "PATCH")

# WHY: The two methods the contract allows. HEAD follows GET, because a probe
# often asks for the headers alone.
READ_METHODS = ("GET", "HEAD")

# WHY: http-api.md line 364 forbids a credential and an organization name in
# this answer. The test searches the whole body text for each word.
FORBIDDEN_WORDS = ("token", "password", "secret", "apitoken", "org", "email")

# WHY: The number of repeat calls. A probe calls the endpoint twice each minute,
# so a body that drifts between calls would make the probe flap.
REPEAT_CALLS = 5

# WHY: One sentence proves which seal fired. A test matches on this text, so a
# fault from anywhere else cannot pass as the seal.
STORE_SEAL_MESSAGE = "The health endpoint must reach no store."


class ExplodingStore:
    """A stand-in for a store entry point that refuses every use.

    Why:
        A test that only asserts a status code cannot tell a quiet database
        call from no database call at all. This class turns any use of an
        ArangoDB client, a Redis client, or the portal database opener into an
        immediate fault. The health endpoint then answers 200 only when it
        touches none of them.
    """

    def __init__(self, *arguments: object, **keywords: object) -> None:
        """Refuse the call that built this object.

        Args:
            *arguments: The positional arguments the caller passed.
            **keywords: The keyword arguments the caller passed.

        Raises:
            RuntimeError: Always, because the health endpoint must reach no store.
        """
        raise RuntimeError(STORE_SEAL_MESSAGE)


def refuse_socket(*arguments: object, **keywords: object) -> None:
    """Refuse every outbound socket call.

    Why:
        A store wrapper the portal has not written yet could reach a database
        without the named entry points below. A seal on the socket layer
        catches that path too, so the proof covers a future caller.

    Args:
        *arguments: The positional arguments the caller passed.
        **keywords: The keyword arguments the caller passed.

    Raises:
        RuntimeError: Always, because the health endpoint must reach no store.
    """
    raise RuntimeError(STORE_SEAL_MESSAGE)


# WHY: Each pair names a module and the attribute on it that opens a store.
# `arango.client` holds the class and `arango` re-exports it, so both bindings
# need the seal. The capture store binds its own copy of `ArangoClient` with a
# `from ... import` at load time, so a seal on the `arango` package alone would
# leave that copy live and the proof would be false.
SEALED_TARGETS: tuple[tuple[ModuleType, str], ...] = (
    (arango, "ArangoClient"),
    (arango.client, "ArangoClient"),
    (store, "ArangoClient"),
    (store, "connect_database"),
    (db_router, "DatabaseRouter"),
    (redis, "Redis"),
    (redis, "StrictRedis"),
)


@pytest.fixture
def sealed_stores(monkeypatch: pytest.MonkeyPatch) -> tuple[tuple[ModuleType, str], ...]:
    """Seal every ArangoDB entry point, every Redis entry point, and the socket layer.

    Why:
        The fixture runs before the application is built, so the proof covers
        the build as well as the request. A portal that opened a store at build
        time would fail here, and that failure is the point of the fixture.

    Args:
        monkeypatch: The pytest patch helper. It restores every name after the test.

    Returns:
        The sealed targets, so a test can read each one back and prove it raises.
    """
    for owner, name in SEALED_TARGETS:  # One seal for each named store entry point.
        monkeypatch.setattr(owner, name, ExplodingStore)
    monkeypatch.setattr(socket.socket, "connect", refuse_socket)  # Catches a direct socket call.
    monkeypatch.setattr(socket, "create_connection", refuse_socket)  # Catches requests and urllib3.
    return SEALED_TARGETS


@pytest.fixture
def sealed_client(sealed_stores: tuple[tuple[ModuleType, str], ...]) -> Iterator[FlaskClient]:
    """Return a test client for an application built while every store is sealed.

    Why:
        The client is built after the seal, because a fixture runs after the
        fixture it depends on. The order proves that `create_app` needs no
        store either, not only that the view needs none.

    Args:
        sealed_stores: The seal fixture. The client must not exist before it.

    Yields:
        The Flask test client.
    """
    assert sealed_stores  # The seal must hold at least one target, or the proof is empty.
    app = factory.create_app()  # Takes no argument. Every setting comes from the environment.
    app.config.update(TESTING=True)  # Test mode reports the real exception instead of a 500 page.
    with app.test_client() as client:  # No server and no network call.
        yield client


def read_health(client: FlaskClient) -> dict[str, Any]:
    """Call the health endpoint and return the decoded body.

    Args:
        client: The Flask test client.

    Returns:
        The decoded JSON body.
    """
    response = client.get(HEALTH_PATH)
    payload: dict[str, Any] = response.get_json()
    return payload


def test_healthz_answers_with_status_200(portal_client: FlaskClient) -> None:
    """The endpoint answers 200.

    Why:
        http-api.md section 7 documents one answer only. The container probe
        reads the status code and nothing else.

    Args:
        portal_client: The Flask test client from the package conftest.
    """
    response = portal_client.get(HEALTH_PATH)
    assert response.status_code == 200


def test_healthz_answers_with_json_content_type(portal_client: FlaskClient) -> None:
    """The endpoint answers with the JSON content type.

    Why:
        The `Content type` rule of contracts/README.md binds every JSON
        endpoint to `application/json`. A probe that parses JSON needs the
        declared type, because the portal also sends `X-Content-Type-Options`
        with the value `nosniff`.

    Args:
        portal_client: The Flask test client from the package conftest.
    """
    response = portal_client.get(HEALTH_PATH)
    assert response.mimetype == "application/json"  # The bare type, without the charset parameter.


def test_healthz_body_holds_exactly_the_two_contract_keys(portal_client: FlaskClient) -> None:
    """The body holds `status` and `version` and no other key.

    Why:
        An equality check on the key set fails for an extra key and for a
        missing key. A subset check would pass while the portal leaked an
        organization name or a store address into the probe answer.

    Args:
        portal_client: The Flask test client from the package conftest.
    """
    payload = read_health(portal_client)
    assert set(payload) == EXPECTED_KEYS


def test_healthz_reports_the_status_word_ok(portal_client: FlaskClient) -> None:
    """The `status` field holds the word `ok`.

    Args:
        portal_client: The Flask test client from the package conftest.
    """
    payload = read_health(portal_client)
    assert payload["status"] == EXPECTED_STATUS


def test_healthz_version_is_text(portal_client: FlaskClient) -> None:
    """The `version` field holds text.

    Why:
        The contract types the field as a string. A probe writes the value into
        a dashboard label, so a number or a null would break that label.

    Args:
        portal_client: The Flask test client from the package conftest.
    """
    payload = read_health(portal_client)
    assert isinstance(payload["version"], str)
    assert payload["version"] != ""  # An empty label tells an operator nothing.


def test_healthz_reports_a_resolved_version(monkeypatch: pytest.MonkeyPatch, portal_client: FlaskClient) -> None:
    """The endpoint reports the version that the portal resolved.

    Why:
        This is the first of the two version branches. The factory reads the
        version one time at import, so the test replaces the resolved value and
        drives the branch where a distribution is installed.

    Args:
        monkeypatch: The pytest patch helper.
        portal_client: The Flask test client from the package conftest.
    """
    monkeypatch.setattr(factory, "PORTAL_VERSION", SAMPLE_VERSION)  # The view reads this name at call time.
    payload = read_health(portal_client)
    assert payload["version"] == SAMPLE_VERSION
    assert set(payload) == EXPECTED_KEYS  # A resolved version must not add a key.


def test_healthz_reports_unknown_when_no_version_resolves(
    monkeypatch: pytest.MonkeyPatch, portal_client: FlaskClient
) -> None:
    """The endpoint reports the word `unknown` when no version resolves.

    Why:
        This is the second version branch. A developer runs the portal from a
        working copy that holds no installed distribution. The endpoint must
        still answer 200, because a missing version is not a health fault.

    Args:
        monkeypatch: The pytest patch helper.
        portal_client: The Flask test client from the package conftest.
    """
    monkeypatch.setattr(factory, "PORTAL_VERSION", UNKNOWN_VERSION_TEXT)
    response = portal_client.get(HEALTH_PATH)
    payload: dict[str, Any] = response.get_json()
    assert response.status_code == 200  # A missing version never lowers the status.
    assert payload["version"] == UNKNOWN_VERSION_TEXT


def test_read_version_returns_the_installed_version(monkeypatch: pytest.MonkeyPatch) -> None:
    """The resolver returns the version of the portal distribution.

    Why:
        The test records the name the resolver asks for. A resolver that read
        another distribution would report a version the operator cannot match
        against the deployed portal.

    Args:
        monkeypatch: The pytest patch helper.
    """
    asked: list[str] = []  # Records each distribution name the resolver requested.

    def fake_version(name: str) -> str:
        """Answer one metadata read.

        Args:
            name: The distribution name the resolver asked for.

        Returns:
            The sample version.
        """
        asked.append(name)
        return SAMPLE_VERSION

    monkeypatch.setattr(factory, "version", fake_version)
    assert factory.read_version() == SAMPLE_VERSION
    assert asked == [factory.DISTRIBUTION_NAME]  # The resolver names the portal distribution only.


def test_read_version_returns_unknown_when_the_distribution_is_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """The resolver returns the word `unknown` when the distribution is absent.

    Why:
        A working copy holds no installed distribution. The resolver must
        answer a plain word instead of raising, because a raise inside the
        health path would kill the container at start.

    Args:
        monkeypatch: The pytest patch helper.
    """

    def fake_version(name: str) -> str:
        """Report that the distribution is absent.

        Args:
            name: The distribution name the resolver asked for.

        Returns:
            Nothing. The function always raises.

        Raises:
            PackageNotFoundError: Always, because no distribution is installed.
        """
        raise PackageNotFoundError(name)

    monkeypatch.setattr(factory, "version", fake_version)
    assert factory.read_version() == UNKNOWN_VERSION_TEXT  # The literal, because it travels on the wire.


def test_healthz_answers_while_every_store_is_sealed(sealed_client: FlaskClient) -> None:
    """The endpoint answers 200 while every store entry point raises.

    Why:
        This is the property the endpoint exists for. A health answer that
        reads ArangoDB or Redis would report the portal unhealthy during a
        store hiccup, and the orchestrator would kill a working process. The
        seal covers the ArangoDB client, the Redis client, the portal database
        opener, the database router, and the socket layer.

    Args:
        sealed_client: The client for an application built under the seal.
    """
    response = sealed_client.get(HEALTH_PATH)
    payload: dict[str, Any] = response.get_json()
    assert response.status_code == 200
    assert payload == {"status": EXPECTED_STATUS, "version": factory.PORTAL_VERSION}


def test_the_store_seal_really_raises(sealed_stores: tuple[tuple[ModuleType, str], ...]) -> None:
    """Every sealed entry point raises when a caller uses it.

    Why:
        The test above proves nothing if the seal is empty. A patch on the
        wrong name, a stale import, or a renamed attribute would leave the
        real client in place and the guard would pass for the wrong reason.
        This test reads each sealed name back and calls it.

    Args:
        sealed_stores: The sealed targets from the seal fixture.
    """
    assert len(sealed_stores) == len(SEALED_TARGETS)  # The seal must cover every listed target.
    for owner, name in sealed_stores:  # Read the name back, so a failed patch shows here.
        sealed = getattr(owner, name)
        with pytest.raises(RuntimeError, match=re.escape(STORE_SEAL_MESSAGE)):
            sealed()


def test_the_socket_seal_really_raises(sealed_stores: tuple[tuple[ModuleType, str], ...]) -> None:
    """The socket seal raises for an outbound connection.

    Why:
        The named seals cover the clients the repository imports today. The
        socket seal covers a store wrapper a later task may add, so this test
        proves that second layer is live as well.

    Args:
        sealed_stores: The seal fixture. The socket seal travels with it.
    """
    assert sealed_stores  # The fixture ran, so both seal layers are in place.
    with pytest.raises(RuntimeError, match=re.escape(STORE_SEAL_MESSAGE)):
        socket.create_connection(("127.0.0.1", 1))


@pytest.mark.parametrize("method", READ_METHODS)
def test_healthz_allows_a_read_method(portal_client: FlaskClient, method: str) -> None:
    """The endpoint answers a GET request and a HEAD request.

    Why:
        A probe often sends HEAD, because it needs the status code alone. An
        endpoint that answered GET only would report every HEAD probe as a
        fault.

    Args:
        portal_client: The Flask test client from the package conftest.
        method: The read method under test.
    """
    response = portal_client.open(HEALTH_PATH, method=method)
    assert response.status_code == 200


@pytest.mark.parametrize("method", STATE_CHANGING_METHODS)
def test_healthz_refuses_a_state_changing_method(portal_client: FlaskClient, method: str) -> None:
    """The endpoint answers 405 for every method that changes state.

    Why:
        A health probe reads. A write to this path would mean a caller mistook
        the probe path for an operation path, so the portal must refuse it
        instead of ignoring the body.

    Args:
        portal_client: The Flask test client from the package conftest.
        method: The state-changing method under test.
    """
    response = portal_client.open(HEALTH_PATH, method=method)
    assert response.status_code == 405


def test_healthz_refusal_names_the_two_read_methods(portal_client: FlaskClient) -> None:
    """The 405 answer names GET and HEAD and does not name the refused method.

    Why:
        HTTP requires the `Allow` header on a 405 answer. The header is the
        machine-readable form of the rule that only a read is allowed.

    Args:
        portal_client: The Flask test client from the package conftest.
    """
    response = portal_client.open(HEALTH_PATH, method="POST")
    allowed = {entry.strip() for entry in (response.headers.get("Allow") or "").split(",")}
    assert READ_METHODS[0] in allowed
    assert READ_METHODS[1] in allowed
    assert "POST" not in allowed


@pytest.mark.parametrize("method", STATE_CHANGING_METHODS)
def test_healthz_refusal_carries_the_error_envelope(portal_client: FlaskClient, method: str) -> None:
    """The 405 answer carries the one error envelope the contract allows.

    Why:
        A browser and a probe both parse the portal answers as JSON. An HTML
        page for one status code forces every caller to hold a second parser.

    Args:
        portal_client: The Flask test client from the package conftest.
        method: The state-changing method under test.
    """
    response = portal_client.open(HEALTH_PATH, method=method)
    assert response.mimetype == "application/json"
    payload: dict[str, Any] = response.get_json()
    assert set(payload) == {"error"}  # The envelope holds one key at the top.
    assert set(payload["error"]) >= {"code", "message"}
    code = payload["error"]["code"]
    # WHY: contracts/README.md fixes `code` as a lower-case string and states
    # that a test asserts on `code` and never on `message`. The status table of
    # that document names no code for 405, so the test states the shape rule
    # instead of inventing a word the contract never wrote.
    assert isinstance(code, str)
    assert code == code.lower()
    assert code != ""


def test_healthz_answers_without_a_session(portal_client: FlaskClient) -> None:
    """An unauthenticated caller receives 200.

    Why:
        http-api.md line 364 states that the endpoint requires no session. A
        health check runs before any operator signs in, so a guard on this path
        would keep the container from ever reporting healthy.

    Args:
        portal_client: The Flask test client from the package conftest.
    """
    response = portal_client.get(HEALTH_PATH)  # The client holds no cookie and no session.
    assert response.status_code == 200
    assert response.status_code != 401  # A guarded health path would answer `not_authenticated`.


def test_healthz_sets_no_session_cookie(portal_client: FlaskClient) -> None:
    """The endpoint sets no cookie.

    Why:
        A probe calls this path twice each minute for the life of the
        container. A cookie on each answer would open a session the operator
        never asked for.

    Args:
        portal_client: The Flask test client from the package conftest.
    """
    response = portal_client.get(HEALTH_PATH)
    assert "Set-Cookie" not in response.headers


def test_healthz_reports_no_credential_and_no_organization(portal_client: FlaskClient) -> None:
    """The body names no credential and no organization.

    Why:
        http-api.md line 364 forbids both. The endpoint answers before any
        sign-in, and an unauthenticated caller must learn nothing about the
        cloud account behind the portal.

    Args:
        portal_client: The Flask test client from the package conftest.
    """
    body = portal_client.get(HEALTH_PATH).get_data(as_text=True).lower()
    for word in FORBIDDEN_WORDS:  # One pass over the words the contract forbids.
        assert word not in body


def test_healthz_answers_the_same_body_on_every_call(portal_client: FlaskClient) -> None:
    """Repeat calls return the same body.

    Why:
        A probe compares one answer against the next. A body that drifts
        between two calls would make the probe flap and would restart a healthy
        container.

    Args:
        portal_client: The Flask test client from the package conftest.
    """
    bodies = [json.dumps(read_health(portal_client), sort_keys=True) for _ in range(REPEAT_CALLS)]
    assert len(set(bodies)) == 1  # Every call returned the same canonical text.
    assert json.loads(bodies[0])["status"] == EXPECTED_STATUS
