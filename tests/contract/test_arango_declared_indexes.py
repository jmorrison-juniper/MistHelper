"""Check the real SDK index requests and existing router failure results."""

from collections.abc import Iterator
from copy import deepcopy
from functools import partial
from json import JSONDecodeError, dumps, loads
from typing import Any
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from arango import ArangoClient
from arango.request import Request
from arango.response import Response

from src.foundation.persistence.db import DatabaseConfig, WriteResult
from src.foundation.persistence.db.backends.arango_writer import ArangoDBWriter
from src.foundation.persistence.db.backends.redis_writer import RedisJSONWriter
from src.foundation.persistence.db.coordination.router import DatabaseRouter
from src.foundation.support.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES
from tests.integration.test_arango_declared_indexes_live import IsolatedArangoIndexTarget, IsolatedIndexQueryProof
from tests.unit.arango_indexes.fakes import ArangoIndexWriterHarness


class SDKIndexTransport:
    """Return native SDK responses without opening a socket."""

    def __init__(self) -> None:
        """Keep request evidence separate from the SDK's response formatting."""
        self.requests: list[Request] = []
        self.status = 201

    def respond(self, request: Request) -> Response:
        """Exercise native SDK success and error handlers."""
        self.requests.append(request)
        status = self.status if request.endpoint == "/_api/index" else 201
        response = Response(
            request.method, "http://127.0.0.1:9609" + request.endpoint, {}, status, "Index response", ""
        )
        response.is_success = 200 <= status < 300
        response.body = {"code": status, "error": not response.is_success, **self.body(request)}
        response.error_message = None if response.is_success else "The declared index could not be created."
        return response

    def http_response(self, **arguments: Any) -> Response:
        """Serialize a wire response so the real SDK connection parses the JSON."""
        endpoint = "/_api/" + arguments["url"].rsplit("/_api/", 1)[1]
        request = Request(arguments["method"], endpoint, params=arguments["params"], data=loads(arguments["data"]))
        response = self.respond(request)
        response.raw_body = dumps(response.body)
        return response

    @staticmethod
    def body(request: Request) -> dict[str, Any]:
        """Supply the exact successful response fields that the native SDK reads."""
        if request.endpoint == "/_api/explain":
            return {"plan": {"nodes": [{"type": "IndexNode", "indexes": [{"fields": ["status"]}]}]}}
        if request.endpoint != "/_api/index":
            return {"created": 1, "updated": 0, "errors": 0, "empty": 0}
        return {
            "id": request.params["collection"] + "/7",
            "type": "persistent",
            "fields": request.data["fields"],
            "unique": False,
            "isNewlyCreated": False,
        }


@pytest.fixture
def sdk_writer(request: pytest.FixtureRequest) -> Iterator[tuple[ArangoDBWriter, SDKIndexTransport]]:
    """Run real SDK collection methods inside the real writer."""
    harness = ArangoIndexWriterHarness()
    client = ArangoClient(hosts=harness.config.arango_host)
    api_name = getattr(request, "param", "listOrgMarvisActions")
    collection = client.db(harness.config.arango_database).collection(api_name)
    transport = SDKIndexTransport()
    harness.database.handle.collection.side_effect = None
    harness.database.handle.collection.return_value = collection
    try:
        with patch.object(collection._conn, "send_request", side_effect=transport.respond):
            yield harness.writer(), transport
    finally:
        harness.close()
        client.close()


class TestArangoIndexSDKContract:
    """Verify exact native index request shapes through the actual writer."""

    def test_native_sdk_requests_one_persistent_index_per_declared_field(self, sdk_writer) -> None:
        """Keep the SDK method, field order, options, and second-write behavior exact."""
        writer, transport = sdk_writer
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES["listOrgMarvisActions"]
        first = writer.write([{"uuid": "action-1"}], "listOrgMarvisActions", strategy)
        second = writer.write([{"uuid": "action-2"}], "listOrgMarvisActions", strategy)
        requests = [request for request in transport.requests if request.endpoint == "/_api/index"]
        assert [(request.method, request.params, request.data) for request in requests] == [
            ("post", {"collection": "listOrgMarvisActions"}, {"type": "persistent", "fields": [name]})
            for name in strategy["indexes"]
        ]
        assert [request.endpoint for request in transport.requests] == ["/_api/index"] * 5 + ["/_api/import"] * 2
        assert (first.success, first.records_written, second.success, second.records_written) == (True, 1, True, 1)

    @pytest.mark.parametrize("http_status", (403, 500), ids=("http_4xx", "http_5xx"))
    def test_native_sdk_error_remains_an_explicit_router_failure(self, sdk_writer, http_status: int) -> None:
        """Retain the existing failed CSV result instead of claiming index success."""
        writer, transport = sdk_writer
        transport.status = http_status
        router = DatabaseRouter(DatabaseConfig(standalone_mode=True), ENDPOINT_PRIMARY_KEY_STRATEGIES)
        router.config.standalone_mode = False
        router._arango_available = True
        router._arango_writer = writer
        result = router.write([{"uuid": "action-1"}, {"uuid": "action-2"}], "listOrgMarvisActions")
        assert (result.success, result.backend, result.records_written, result.records_failed) == (
            False,
            "csv_only",
            0,
            2,
        )
        assert result.error_message == f"[HTTP {http_status}] The declared index could not be created."
        assert [request.endpoint for request in transport.requests] == ["/_api/index"]
        assert router._arango_available is False

    def test_query_proof_consumes_the_native_sdk_plan_shape(self, sdk_writer) -> None:
        """Prevent a REST response wrapper from replacing the SDK's plan contract."""
        writer, transport = sdk_writer
        client = ArangoClient(hosts="http://127.0.0.1:9609")
        writer._db = client.db("misthelper-tmp-issue3309-query-contract")
        try:
            with patch.object(writer._db._conn, "send_request", side_effect=transport.respond):
                fields = IsolatedIndexQueryProof.query_plan(writer)
            assert fields == [["status"]]
            assert [(request.method, request.endpoint) for request in transport.requests] == [("post", "/_api/explain")]
            assert transport.requests[0].data["options"] == {"allPlans": False}
        finally:
            client.close()

    @pytest.mark.parametrize("sdk_writer", ("searchOrgDeviceEvents",), indirect=True)
    def test_index_failure_keeps_the_independent_dual_write_result(self, sdk_writer) -> None:
        """Keep the Redis result while reporting the failed ArangoDB leg."""
        writer, transport = sdk_writer
        transport.status = 500
        strategy = deepcopy(ENDPOINT_PRIMARY_KEY_STRATEGIES["searchOrgDeviceEvents"])
        router = DatabaseRouter(DatabaseConfig(standalone_mode=True), {"searchOrgDeviceEvents": strategy})
        router.config.standalone_mode = False
        router._arango_available = router._redis_json_available = True
        router._arango_writer = writer
        redis_writer: MagicMock = create_autospec(RedisJSONWriter, instance=True, spec_set=True)
        redis_writer.write.return_value = WriteResult(True, "redis_json", 2, 0)
        router._redis_json_writer = redis_writer
        rows = [{"id": "event-1"}, {"id": "event-2"}]
        result = router.write(rows, "searchOrgDeviceEvents")
        assert (result.success, result.backend, result.records_written, result.records_failed) == (False, "dual", 2, 2)
        assert result.error_message == "arango: [HTTP 500] The declared index could not be created."
        redis_writer.write.assert_called_once_with(rows, "searchOrgDeviceEvents", strategy)
        assert [request.endpoint for request in transport.requests] == ["/_api/index"]

    @pytest.mark.parametrize("raw_body", (b"", b"{"), ids=("empty_body", "malformed_json"))
    def test_malformed_json_or_empty_body_stays_visible_and_retries(self, sdk_writer, raw_body: bytes) -> None:
        """Use the native connection parser and retry without confirming an invalid response."""
        writer, transport = sdk_writer
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES["listOrgMarvisActions"]
        connection = writer._db.collection.return_value._conn
        send_request = partial(type(connection).send_request, connection)
        with pytest.raises(JSONDecodeError):
            loads(raw_body)
        response = Response(
            "post", "http://127.0.0.1:9609/_api/index", {}, 201, "Invalid index response", raw_body.decode()
        )
        with (
            patch.object(connection, "send_request", side_effect=send_request),
            patch.object(connection._http, "send_request", return_value=response) as http,
        ):
            with pytest.raises(AttributeError, match="has no attribute 'pop'"):
                ArangoDBWriter.write(writer, [{"uuid": "action-1"}], "listOrgMarvisActions", strategy)
            assert [entry.kwargs["url"].rsplit("/_api/", 1)[1] for entry in http.call_args_list] == ["index"]
            http.side_effect = transport.http_response
            result = ArangoDBWriter.write(writer, [{"uuid": "action-1"}], "listOrgMarvisActions", strategy)
        fields = [request.data["fields"][0] for request in transport.requests if request.endpoint == "/_api/index"]
        assert fields == strategy["indexes"]
        assert (result.success, result.records_written, result.records_failed, http.call_count) == (True, 1, 0, 7)


class TestIsolatedArangoIndexTarget:
    """Prove that the integration target guard rejects production addresses."""

    @pytest.mark.parametrize(
        "url",
        (
            "http://127.0.0.1:9529",
            "http://127.0.0.1:9379",
            "http://127.0.0.1:9599",
            "http://127.0.0.1:9700",
            "http://localhost:9650",
            "https://127.0.0.1:9650",
            "http://misthelper-arangodb:9650",
            "http://127.0.0.1",
            "http://127.0.0.1:invalid",
            "http://account@127.0.0.1:9650",
            "http://127.0.0.1:9650/_db/misthelper",
            "http://127.0.0.1:9650?database=misthelper",
            "http://127.0.0.1:9650#misthelper",
        ),
    )
    def test_invalid_target_fails_with_one_checked_url(self, url: str) -> None:
        """Fail before a connection and retain an explicit measured count."""
        with patch("tests.integration.test_arango_declared_indexes_live.logger") as log:
            with pytest.raises(ValueError, match="isolated ArangoDB test"):
                IsolatedArangoIndexTarget.configuration(url)
        log.error.assert_called_once_with("arango_index_test_target_invalid", checked_count=1)

    @pytest.mark.parametrize("port", (9600, 9699))
    def test_owned_loopback_range_creates_only_an_issue_prefixed_database(self, port: int) -> None:
        """Accept both range boundaries without reading production configuration."""
        url = f"http://127.0.0.1:{port}"
        config = IsolatedArangoIndexTarget.configuration(url)
        assert (config.arango_host, config.arango_password, config.arango_username) == (url, "", "root")
        assert config.arango_database.startswith("misthelper-tmp-issue3309-")
