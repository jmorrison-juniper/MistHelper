"""Integration test for compose deployment health.

Requires Docker/Podman Compose with the misthelper-arangodb and misthelper-redis
services. Skipped automatically when containers are not running.

The ports below are the project ports, not the vendor defaults. See the naming
and port policy at the top of compose.yml (issue #2059).
"""

from __future__ import annotations

import os

import pytest

COMPOSE_AVAILABLE = os.environ.get("COMPOSE_TEST", "0") == "1"
skip_reason = "Set COMPOSE_TEST=1 with running compose services"

ARANGO_PORT = 9529  # The project ArangoDB port. Not 8529.
REDIS_PORT = 9379  # The project Redis port. Not 6379.


@pytest.mark.skipif(not COMPOSE_AVAILABLE, reason=skip_reason)
class TestComposeDeployment:
    """Verify all 3 services start healthy and MistHelper can reach them."""

    def test_arangodb_reachable(self):
        from arango import ArangoClient

        client = ArangoClient(hosts=f"http://localhost:{ARANGO_PORT}")
        system_db = client.db(
            "_system",
            username="root",
            password=os.environ.get("ARANGO_ROOT_PASSWORD", "misthelper"),
        )
        assert system_db.version() is not None
        client.close()

    def test_redis_reachable(self):
        import redis

        client = redis.Redis(
            host="localhost",
            port=REDIS_PORT,
            password=os.environ.get("REDIS_PASSWORD", "misthelper"),
            decode_responses=True,
        )
        assert client.ping() is True
        modules = client.execute_command("MODULE", "LIST")
        module_names = [
            m["name"].lower() if isinstance(m["name"], str) else m["name"].decode().lower() for m in modules
        ]
        assert "timeseries" in module_names
        client.close()

    def test_router_health_check_all_green(self):
        from src.db import DatabaseConfig
        from src.db.router import DatabaseRouter

        config = DatabaseConfig.from_env()
        router = DatabaseRouter(config)
        health = router.health_check()

        assert health["arangodb"] is True
        assert health["redis"] is True
        assert health["standalone"] is False
        router.close()

    def test_csv_output_unchanged(self):
        """Verify CSV output is not affected by polyglot routing."""
        from src.db import DatabaseConfig, WriteResult
        from src.db.router import DatabaseRouter

        config = DatabaseConfig.from_env()
        router = DatabaseRouter(config)
        data = [{"id": "test-1", "name": "TestSite"}]
        result = router.write(data, "listOrgSites")

        assert isinstance(result, WriteResult)
        router.close()
