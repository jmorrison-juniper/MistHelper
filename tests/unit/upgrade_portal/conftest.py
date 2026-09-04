"""Shared fixtures for the unit tests of the upgrade capture portal.

Why:
    A unit test must run offline and must finish fast. These fixtures give a
    fake cloud session, a fake document store, and a fake lock store. No unit
    test opens a socket, an ArangoDB connection, or a Redis connection. An
    autouse fixture turns a hidden network call into a clear error.

    No fixture reads the ``.env`` file. Every credential value below is an
    obviously fake string. No fixture writes a token value into a log record.
"""

from __future__ import annotations

import logging
import socket
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.upgrade_portal.runtime import lock  # WHY: The fixture drops the cached lock store handle.
from tests.support.rehearsal.errors import RehearsalNetworkError  # WHY: The named error of the rehearsal guard.

logger = logging.getLogger(__name__)

# WHY: An obviously fake value. A reader sees at once that this is not a real
# credential. FR-009 forbids a real token value inside the test suite.
FAKE_API_TOKEN = "fake-api-token-for-tests-only"

# WHY: A reserved example host. A request that escapes the network block still
# cannot reach the real cloud.
FAKE_CLOUD_HOST = "api.example.com"


class FakeDocumentStore:
    """In-memory stand-in for the ArangoDB collections of the portal.

    Why:
        The portal writes a capture document and a run document, then reads
        the key back to prove the write. A unit test needs that read-back
        without a database. This class keeps every document in a dictionary
        and records each written key, so a test can check the call order.
    """

    def __init__(self) -> None:
        """Create an empty store."""
        self.documents: dict[str, dict[str, Any]] = {}  # WHY: Holds every written document by key.
        self.written_keys: list[str] = []  # WHY: Records the write order for an assertion.

    def write(self, key: str, document: dict[str, Any]) -> bool:
        """Store one document under the key.

        Args:
            key: The natural primary key of the document.
            document: The document body.

        Returns:
            True, because the fake store always accepts a write.
        """
        self.written_keys.append(key)  # WHY: The test asserts on the order of the writes.
        self.documents[key] = dict(document)  # WHY: A copy stops a later edit of the caller dictionary.
        return True

    def read(self, key: str) -> dict[str, Any] | None:
        """Return the stored document for one key.

        Args:
            key: The natural primary key of the document.

        Returns:
            The stored document, or None when the key is absent.
        """
        return self.documents.get(key)  # WHY: The read-back check needs the stored copy.


class FakeLockStore:
    """In-memory stand-in for the Redis site lock.

    Why:
        The site lock uses one atomic ``SET key value NX EX 300``. A unit test
        must prove that a second operator loses the race. This class repeats
        the ``nx`` behavior of the real client without a Redis server.
    """

    def __init__(self) -> None:
        """Create an empty lock store."""
        self.values: dict[str, str] = {}  # WHY: Holds each lock key and its token.

    def set(self, key: str, value: str, nx: bool = False, ex: int | None = None) -> bool | None:
        """Write one key under the same rules as the real client.

        Args:
            key: The lock key.
            value: The lock token.
            nx: True writes the key only when the key is absent.
            ex: The expiry in seconds. The fake store accepts it and ignores it.

        Returns:
            True after a write, or None when ``nx`` blocked the write.
        """
        if nx and key in self.values:  # WHY: The real client returns None when the key exists.
            return None
        self.values[key] = value
        return True

    def get(self, key: str) -> str | None:
        """Return the token for one lock key.

        Args:
            key: The lock key.

        Returns:
            The stored token, or None when the key is absent.
        """
        return self.values.get(key)

    def delete(self, key: str) -> int:
        """Remove one lock key.

        Args:
            key: The lock key.

        Returns:
            1 after a delete, or 0 when the key was absent.
        """
        return 1 if self.values.pop(key, None) is not None else 0


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Stop every outbound socket call inside this test package.

    Why:
        A unit test must never reach the cloud, ArangoDB, or Redis. A test
        that opens a socket is slow, and it fails on a computer with no
        network. The block turns a hidden network call into a clear error at
        the exact line that made the call.

        The socket block alone does not keep that promise. ``lock`` caches one
        open client in a module global, and a contract test that ran earlier in
        the same process leaves a live Redis connection there. The block stops
        a new socket, so the leftover handle still reaches a real Redis and a
        unit test then writes a real lock that outlives it. The next test reads
        that lock and refuses a free site. This fixture therefore drops the
        cached handle on the way in and on the way out, so each unit test meets
        an unreachable lock store no matter what ran before it.

    Args:
        monkeypatch: The pytest patch helper.

    Yields:
        None. The test body runs with the network blocked.
    """

    def _refuse(*args: Any, **kwargs: Any) -> None:
        """Raise for every socket call.

        Args:
            *args: The arguments the caller passed. The block ignores them.
            **kwargs: The keyword arguments the caller passed.

        Raises:
            RuntimeError: Always, because a unit test must stay offline.
        """
        raise RuntimeError("A unit test must not open a network connection.")

    logger.debug("Block the network for one unit test")  # WHY: ASCII only, %s style, no credential.
    monkeypatch.setattr(socket.socket, "connect", _refuse)  # WHY: Catches a direct socket call.
    monkeypatch.setattr(socket, "create_connection", _refuse)  # WHY: Catches requests and urllib3.
    lock.reset_connection()  # WHY: Drop a live handle that an earlier contract test cached.
    try:  # WHY: The test body runs with no reachable lock store.
        yield
    finally:  # WHY: A handle opened here must not reach the next test either.
        lock.reset_connection()  # WHY: Leave the module as clean as this fixture found it.
        logger.debug("Release the lock store handle after one unit test")  # WHY: Records the cleanup.


class NetworkAttemptCounter:
    """Count every socket call that a rehearsal test tried to make.

    Why:
        SC-004 asks the rehearsal to prove that it reached no network. A block
        that only raises cannot prove the count, because a caller can swallow
        the error. This counter answers the number, so a test can assert zero.
    """

    def __init__(self) -> None:
        """Build one counter at zero."""
        self.attempts: int = 0  # Every refused call adds one, and a test asserts this number.

    def refuse(self, *args: Any, **kwargs: Any) -> None:
        """Count one attempt and refuse it.

        Args:
            *args: The arguments the caller passed. The guard ignores them.
            **kwargs: The keyword arguments the caller passed.

        Raises:
            RehearsalNetworkError: Always, because a rehearsal stays offline.
        """
        self.attempts += 1  # The count comes before the raise, so a swallowed error still shows.
        logger.warning("A rehearsal test tried to open a network connection")  # The refused action.
        raise RehearsalNetworkError("A rehearsal test must not open a network connection.")


@pytest.fixture
def network_guard(monkeypatch: pytest.MonkeyPatch) -> NetworkAttemptCounter:
    """Replace the socket calls with a counting guard for one rehearsal test.

    Why:
        The autouse block above already refuses a socket call, and it raises a
        plain ``RuntimeError``. A rehearsal test needs the count and the named
        error class, so this fixture replaces the block for that one test.

    Args:
        monkeypatch: The pytest patch helper.

    Returns:
        The counter, which answers zero for a healthy rehearsal.
    """
    counter = NetworkAttemptCounter()  # One counter for the life of one test.
    logger.info("Install the counting network guard of one rehearsal test")  # The action.
    monkeypatch.setattr(socket.socket, "connect", counter.refuse)  # A direct socket call.
    monkeypatch.setattr(socket, "create_connection", counter.refuse)  # The path of requests and urllib3.
    logger.debug("The counting network guard holds %s attempts", counter.attempts)  # The result.
    return counter  # The guard test asserts that this count stayed at zero.


@pytest.fixture
def fake_api_token() -> str:
    """Return an obviously fake cloud token.

    Why:
        A test that builds a session needs a token shaped value. The fixture
        never reads the ``.env`` file, so no real credential can enter a test
        run or a log record.

    Returns:
        A fake token string.
    """
    return FAKE_API_TOKEN


@pytest.fixture
def fake_mist_session(fake_api_token: str) -> SimpleNamespace:
    """Return a stand-in for the Mist cloud session.

    Why:
        Every capture reader takes a session and calls a read function on it.
        A unit test needs that shape without a cloud account. The mock members
        record each call, so a test can assert on the parameters.

    Args:
        fake_api_token: The fake token from the sibling fixture.

    Returns:
        A namespace with the members the portal reads.
    """
    return SimpleNamespace(
        apitoken=fake_api_token,  # WHY: Named after the real attribute. The value is fake.
        host=FAKE_CLOUD_HOST,  # WHY: A reserved example host, never the real cloud.
        email="operator@example.com",  # WHY: The identity registry holds the operator email.
        get=MagicMock(name="get"),  # WHY: Records a read call without a request.
        post=MagicMock(name="post"),  # WHY: Records a write call without a request.
    )


@pytest.fixture
def fake_document_store() -> FakeDocumentStore:
    """Return an empty in-memory document store.

    Why:
        The store module writes a document and then reads the key back. This
        fixture gives that behavior with no ArangoDB server.

    Returns:
        A fresh store for one test.
    """
    return FakeDocumentStore()


@pytest.fixture
def fake_lock_store() -> FakeLockStore:
    """Return an empty in-memory lock store.

    Why:
        The site lock module needs a client with the ``nx`` behavior of Redis.
        This fixture gives that behavior with no Redis server.

    Returns:
        A fresh lock store for one test.
    """
    return FakeLockStore()
