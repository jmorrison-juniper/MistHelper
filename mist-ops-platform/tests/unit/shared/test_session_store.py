"""Tests for the session store fallback map and the multi-worker guard.

Why:
    Issue #2051 reports that the in-memory fallback is process-local, so a
    multi-worker deployment loses a session on every request that lands on
    another worker. The fallback map also never expires, so a long-running
    process grows without bound. These tests hold the TTL enforcement and the
    multi-worker guard in place.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from src.shared.services import session_store
from src.shared.services.session_store import (
    _MEMORY_CREATED_AT,
    _MEMORY_RECORDS,
    SESSION_TTL_SECONDS,
    SessionStore,
    build_session_store,
    session_key,
)

TEST_TOKEN = "raw-mist-token-value-for-the-fallback-tests"


@pytest.fixture(autouse=True)
def _clean_fallback_map() -> None:
    """Give every test an empty fallback map, and leave it empty."""
    _MEMORY_RECORDS.clear()
    _MEMORY_CREATED_AT.clear()
    yield
    _MEMORY_RECORDS.clear()
    _MEMORY_CREATED_AT.clear()


def _settings_double(worker_count: int) -> MagicMock:
    """Return a settings double that carries the worker count."""
    settings = MagicMock()  # The guard reads one attribute only.
    settings.worker_count = worker_count
    return settings


class TestFallbackTtl:
    """Cover the TTL enforcement on the process-local map."""

    def test_an_expired_record_resolves_to_none(self) -> None:
        store = SessionStore(redis_client=None)
        session_id = store.create(TEST_TOKEN)
        key = session_key(session_id)
        expired_at = time.time() - SESSION_TTL_SECONDS - 1  # Age the record past the lifetime.
        _MEMORY_CREATED_AT[key] = expired_at
        assert store.resolve(session_id) is None  # An expired record must act as a missing record.
        assert key not in _MEMORY_RECORDS  # The reader must drop the record.

    def test_a_fresh_record_still_resolves(self) -> None:
        store = SessionStore(redis_client=None)
        session_id = store.create(TEST_TOKEN)
        record = store.resolve(session_id)
        assert record is not None  # A record inside the lifetime must resolve.
        assert record.token == TEST_TOKEN

    def test_a_write_sweeps_the_expired_records(self) -> None:
        store = SessionStore(redis_client=None)
        fresh_id = store.create(TEST_TOKEN)
        stale_id = store.create(TEST_TOKEN)
        stale_key = session_key(stale_id)
        expired_at = time.time() - SESSION_TTL_SECONDS - 1  # Age one record past the lifetime.
        _MEMORY_CREATED_AT[stale_key] = expired_at
        store.create(TEST_TOKEN)  # A write must sweep the expired record.
        assert stale_key not in _MEMORY_RECORDS  # The sweep must drop the expired record.
        assert session_key(fresh_id) in _MEMORY_RECORDS  # The sweep must keep the fresh record.

    def test_delete_drops_the_write_time(self) -> None:
        store = SessionStore(redis_client=None)
        session_id = store.create(TEST_TOKEN)
        key = session_key(session_id)
        assert store.delete(session_id) is True  # The first delete must report the record.
        assert key not in _MEMORY_RECORDS  # The payload must leave the map.
        assert key not in _MEMORY_CREATED_AT  # The write time must leave the map.


class TestMultiWorkerGuard:
    """Cover the refusal to fall back when more than one worker runs."""

    def test_a_multi_worker_build_refuses_the_fallback(self) -> None:
        with (
            pytest.raises(RuntimeError, match="Redis is required"),
            patch("src.shared.services.session_store._connect_redis", return_value=None),
            patch(
                "src.shared.services.session_store.get_settings",
                return_value=_settings_double(worker_count=4),
            ),
        ):
            build_session_store()

    def test_a_single_worker_build_allows_the_fallback(self) -> None:
        with (
            patch("src.shared.services.session_store._connect_redis", return_value=None),
            patch(
                "src.shared.services.session_store.get_settings",
                return_value=_settings_double(worker_count=1),
            ),
        ):
            store = build_session_store()
        assert store._redis is None  # A single worker may keep its sessions in the process.

    def test_a_multi_worker_build_uses_redis_when_it_answers(self) -> None:
        client = MagicMock()  # A live client proves Redis answers.
        with (
            patch("src.shared.services.session_store._connect_redis", return_value=client),
            patch(
                "src.shared.services.session_store.get_settings",
                return_value=_settings_double(worker_count=4),
            ),
        ):
            store = build_session_store()
        assert store._redis is client  # The store must use the live client.

    def test_a_worker_count_below_one_is_a_misconfiguration(self) -> None:
        with (
            pytest.raises(RuntimeError, match="at least 1"),
            patch(
                "src.shared.services.session_store.get_settings",
                return_value=_settings_double(worker_count=0),
            ),
        ):
            session_store._read_worker_count()
