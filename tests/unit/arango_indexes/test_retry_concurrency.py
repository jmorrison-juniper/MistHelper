"""Prove incomplete checks, retry, and shared process coordination."""

from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from copy import deepcopy
from dataclasses import replace
from functools import partial
from threading import Event
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest
from arango.exceptions import IndexCreateError
from requests.exceptions import ConnectionError as RequestConnectionError
from requests.exceptions import Timeout

from src.db import WriteResult
from src.db.arango_writer import ArangoDBWriter
from src.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES
from tests.unit.arango_indexes.fakes import (
    ArangoIndexCollectionFake,
    ArangoIndexDatabaseFake,
    ArangoIndexWriterHarness,
)


class IndexRequestGate:
    """Hold a real writer's first index request until another write waits."""

    def __init__(self, collection: ArangoIndexCollectionFake) -> None:
        """Keep the request gate separate from fake database state."""
        self.collection = collection
        self.entered = Event()
        self.release = Event()
        collection.handle.add_index.side_effect = self.request

    def request(self, definition: dict[str, Any]) -> dict[str, Any]:
        """Wait under the writer guard before applying the fake server action."""
        self.entered.set()
        if not self.release.wait(timeout=5):
            raise TimeoutError("The test did not release the index request.")
        return self.collection.add_index(definition)

    def create_collection(self, database: ArangoIndexDatabaseFake, name: str, edge: bool = False) -> MagicMock:
        """Attach the gate to a collection created by the actual writer."""
        handle = database.create_collection(name, edge=edge)
        self.collection = database.collections[name]
        handle.add_index.side_effect = self.request
        return handle

    def start(
        self, executor: ThreadPoolExecutor, writer: ArangoDBWriter, strategy: dict[str, Any]
    ) -> Future[WriteResult]:
        """Start the first write and prove that it reaches index creation."""
        future = executor.submit(writer.write, [{"uuid": "action-1"}], "listOrgMarvisActions", strategy)
        if not self.entered.wait(timeout=2):
            self.release.set()
            raise AssertionError("The real writer did not reach the declared index request.")
        return future

    def run_pair(
        self, first_writer: ArangoDBWriter, second_writer: ArangoDBWriter, strategy: dict[str, Any]
    ) -> tuple[Future[WriteResult], Future[WriteResult]]:
        """Prove that the second write cannot pass an incomplete same-scope check."""
        with ThreadPoolExecutor(max_workers=2) as executor:
            first = self.start(executor, first_writer, strategy)
            try:
                second = executor.submit(second_writer.write, [{"uuid": "action-2"}], "listOrgMarvisActions", strategy)
                with pytest.raises(FutureTimeoutError):
                    second.result(timeout=0.05)
                assert second.running() is True
            finally:
                self.release.set()
            return first, second


class TestIndexFailureAndRetry:
    """Keep incomplete first checks and incomplete extensions unconfirmed."""

    @pytest.mark.parametrize(
        "error",
        (
            ArangoIndexCollectionFake.index_error(403),
            ArangoIndexCollectionFake.index_error(500),
            ConnectionAbortedError("The database connection stopped."),
            TimeoutError("The index request timed out."),
            RequestConnectionError("The database connection failed."),
            Timeout("The database response timed out."),
        ),
        ids=("http_4xx", "http_5xx", "connection_aborted", "timeout", "connection_error", "request_timeout"),
    )
    def test_failed_first_check_retries_every_unconfirmed_field(
        self, writer_harness: ArangoIndexWriterHarness, error: Exception
    ) -> None:
        """Expose the original failure and retry the complete declaration."""
        api_name = "listOrgMarvisActions"
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]
        writer_harness.database.create_collection(api_name)
        collection = writer_harness.database.collections[api_name]
        collection.state.failures[strategy["indexes"][1]] = error
        writer = writer_harness.writer()
        with pytest.raises(type(error), match="(HTTP|connection|timed out)") as caught:
            writer.write([{"uuid": "action-1"}], api_name, strategy)
        assert caught.value is error
        assert (collection.handle.import_bulk.call_args_list, collection.state.documents) == ([], {})
        result = writer.write([{"uuid": "action-1"}], api_name, strategy)
        expected_fields = strategy["indexes"][:2] + strategy["indexes"]
        assert collection.handle.add_index.call_args_list == [
            call({"type": "persistent", "fields": [name]}) for name in expected_fields
        ]
        assert (result.success, result.records_written, len(collection.state.indexes)) == (True, 1, 5)

    def test_failed_extension_retains_only_earlier_confirmations(
        self, writer_harness: ArangoIndexWriterHarness
    ) -> None:
        """Retry a partial extension without repeating a completed earlier check."""
        api_name = "listOrgMarvisActions"
        strategy = deepcopy(ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name])
        complete_fields = list(strategy["indexes"])
        strategy["indexes"] = complete_fields[:1]
        writer = writer_harness.writer()
        writer.write([{"uuid": "action-1", "status": "old"}], api_name, strategy)
        collection = writer_harness.database.collections[api_name]
        collection.state.failures[complete_fields[2]] = collection.index_error(500)
        strategy["indexes"] = complete_fields
        with pytest.raises(IndexCreateError, match="HTTP 500"):
            writer.write([{"uuid": "action-1", "status": "new"}], api_name, strategy)
        assert collection.state.documents["action-1"]["status"] == "old"
        result = writer_harness.writer().write([{"uuid": "action-1", "status": "new"}], api_name, strategy)
        expected_fields = complete_fields[:1] + complete_fields[1:3] + complete_fields[1:]
        assert collection.handle.add_index.call_args_list == [
            call({"type": "persistent", "fields": [name]}) for name in expected_fields
        ]
        assert (result.success, result.records_written) == (True, 1)
        assert collection.state.documents["action-1"]["status"] == "new"

    def test_index_diagnostics_identify_failure_without_success(self, writer_harness: ArangoIndexWriterHarness) -> None:
        """Log each attempted field and the exact incomplete checked count."""
        api_name = "listOrgMarvisActions"
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]
        writer_harness.database.create_collection(api_name)
        collection = writer_harness.database.collections[api_name]
        collection.state.failures[strategy["indexes"][1]] = collection.index_error(403)
        with patch("src.db.database_schema_utils.index_logger") as log:
            log.bind.return_value = log
            writer = writer_harness.writer()
            with pytest.raises(IndexCreateError, match="HTTP 403"):
                writer.write([{"uuid": "action-1"}], api_name, strategy)
        events = [
            (entry[0], entry.args[0], entry.kwargs["field"]) for entry in log.method_calls if "field" in entry.kwargs
        ]
        assert events == [
            ("info", "arango_index_ensure", "org_id"),
            ("debug", "arango_index_ready", "org_id"),
            ("info", "arango_index_ensure", "site_id"),
            ("exception", "arango_index_failed", "site_id"),
        ]
        log.exception.assert_called_once_with("arango_index_failed", field="site_id", checked_count=2)
        log.bind.assert_any_call(collection=api_name)
        assert [entry.args[0] for entry in log.debug.call_args_list if entry.args[0] == "arango_indexes_ready"] == []


class TestConcurrentIndexChecks:
    """Coordinate first writes and retry without duplicate process-local work."""

    @pytest.mark.parametrize("existing_collection", (False, True))
    def test_concurrent_first_writes_share_one_complete_check(
        self, writer_harness: ArangoIndexWriterHarness, existing_collection: bool
    ) -> None:
        """Hold the first request and prove one ordered check across two writers."""
        api_name = "listOrgMarvisActions"
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]
        gate = IndexRequestGate(ArangoIndexCollectionFake(api_name))
        if existing_collection:
            writer_harness.database.collections[api_name] = gate.collection
        else:
            writer_harness.database.handle.create_collection.side_effect = partial(
                gate.create_collection, writer_harness.database
            )
        first, second = gate.run_pair(writer_harness.writer(), writer_harness.writer(), strategy)
        results = (first.result(timeout=2), second.result(timeout=2))
        assert gate.collection.handle.add_index.call_args_list == [
            call({"type": "persistent", "fields": [name]}) for name in strategy["indexes"]
        ]
        assert [(result.success, result.records_written) for result in results] == [(True, 1), (True, 1)]
        assert tuple(sorted(gate.collection.state.documents)) == ("action-1", "action-2")
        assert writer_harness.database.handle.create_collection.call_args_list == (
            [] if existing_collection else [call(api_name, edge=False)]
        )

    def test_waiting_writer_retries_after_the_first_writer_fails(
        self, writer_harness: ArangoIndexWriterHarness
    ) -> None:
        """Release a failed first check and permit the waiting writer to retry."""
        api_name = "listOrgMarvisActions"
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]
        writer_harness.database.create_collection(api_name)
        collection = writer_harness.database.collections[api_name]
        collection.state.failures["org_id"] = collection.index_error(500)
        gate = IndexRequestGate(collection)
        first, second = gate.run_pair(writer_harness.writer(), writer_harness.writer(), strategy)
        with pytest.raises(IndexCreateError, match="HTTP 500"):
            first.result(timeout=2)
        result = second.result(timeout=2)
        assert collection.handle.add_index.call_args_list == [
            call({"type": "persistent", "fields": [name]}) for name in ["org_id", *strategy["indexes"]]
        ]
        assert (result.success, result.records_written, tuple(collection.state.documents)) == (True, 1, ("action-2",))

    def test_another_database_does_not_wait_for_the_blocked_scope(
        self, writer_harness: ArangoIndexWriterHarness
    ) -> None:
        """Keep independent database guards separate during live writer calls."""
        api_name = "listOrgMarvisActions"
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]
        writer_harness.database.create_collection(api_name)
        gate = IndexRequestGate(writer_harness.database.collections[api_name])
        other = ArangoIndexWriterHarness()
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                first = gate.start(executor, writer_harness.writer(), strategy)
                try:
                    second = executor.submit(other.writer().write, [{"uuid": "action-2"}], api_name, strategy)
                    result = second.result(timeout=2)
                    assert (result.success, result.records_written, gate.release.is_set()) == (True, 1, False)
                finally:
                    gate.release.set()
                assert (first.result(timeout=2).success, len(gate.collection.state.indexes)) == (True, 5)
        finally:
            other.close()


class TestWriterScope:
    """Share only matching configured scopes and invalidate recreated collections."""

    @pytest.mark.parametrize("changed_scope", ("arango_host", "arango_database", "arango_username"))
    def test_independent_database_scopes_each_check_declared_fields(
        self, writer_harness: ArangoIndexWriterHarness, changed_scope: str
    ) -> None:
        """Do not reuse a collection-only confirmation across different scopes."""
        api_name = "listOrgMarvisActions"
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]
        values = {
            "arango_host": "http://127.0.0.1:9610",
            "arango_database": writer_harness.config.arango_database + "-separate",
            "arango_username": "issue3309-separate",
        }
        other = ArangoIndexWriterHarness(replace(writer_harness.config, **{changed_scope: values[changed_scope]}))
        try:
            writer_harness.writer().write([], api_name, strategy)
            other.writer().write([], api_name, strategy)
            expected = [call({"type": "persistent", "fields": [name]}) for name in strategy["indexes"]]
            assert writer_harness.database.collections[api_name].handle.add_index.call_args_list == expected
            assert other.database.collections[api_name].handle.add_index.call_args_list == expected
        finally:
            other.close()

    def test_independent_same_scope_clients_share_confirmation(self, writer_harness: ArangoIndexWriterHarness) -> None:
        """Use each writer's own client without repeating the process check."""
        api_name = "listOrgMarvisActions"
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]
        other = ArangoIndexWriterHarness(writer_harness.config, writer_harness.database)
        try:
            first = writer_harness.writer().write([{"uuid": "action-1"}], api_name, strategy)
            second = other.writer().write([{"uuid": "action-2"}], api_name, strategy)
            collection = writer_harness.database.collections[api_name]
            assert collection.handle.add_index.call_args_list == [
                call({"type": "persistent", "fields": [name]}) for name in strategy["indexes"]
            ]
            assert (first.records_written, second.records_written, len(collection.state.documents)) == (1, 1, 2)
            assert (writer_harness.client.db.call_count, other.client.db.call_count) == (2, 2)
        finally:
            other.close()

    def test_recreated_collection_does_not_reuse_old_confirmation(
        self, writer_harness: ArangoIndexWriterHarness
    ) -> None:
        """Invalidate only the recreated fake collection before its new check."""
        api_name = "listOrgMarvisActions"
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]
        writer = writer_harness.writer()
        writer.write([], api_name, strategy)
        previous = writer_harness.database.collections.pop(api_name)
        writer.write([], api_name, strategy)
        current = writer_harness.database.collections[api_name]
        expected = [call({"type": "persistent", "fields": [name]}) for name in strategy["indexes"]]
        assert (previous.handle.add_index.call_args_list, current.handle.add_index.call_args_list) == (
            expected,
            expected,
        )
        assert current.state.documents == {}
