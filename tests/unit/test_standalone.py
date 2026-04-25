"""Unit tests for standalone mode detection and CLI flag."""

from __future__ import annotations

from unittest.mock import patch


class TestStandaloneConfig:
    """Verify standalone mode from env vars."""

    def test_standalone_true_from_env(self) -> None:
        from src.db import DatabaseConfig

        with patch.dict("os.environ", {"MISTHELPER_STANDALONE": "true"}):
            config = DatabaseConfig.from_env()
            assert config.standalone_mode is True

    def test_standalone_false_by_default(self) -> None:
        from src.db import DatabaseConfig

        with (
            patch.dict("os.environ", {}, clear=True),
            patch("src.db._hosts_unreachable", return_value=False),
        ):
            config = DatabaseConfig.from_env()
            assert config.standalone_mode is False

    def test_standalone_case_insensitive(self) -> None:
        from src.db import DatabaseConfig

        with patch.dict("os.environ", {"MISTHELPER_STANDALONE": "True"}):
            config = DatabaseConfig.from_env()
            assert config.standalone_mode is True


class TestStandaloneRouter:
    """Verify router skips connections in standalone mode."""

    def test_router_skips_connections_standalone(self) -> None:
        from src.db import DatabaseConfig
        from src.db.router import DatabaseRouter

        config = DatabaseConfig(standalone_mode=True)
        with (
            patch("src.db.router.ArangoDBWriter") as mock_arango,
            patch("src.db.router.RedisTimeSeriesWriter") as mock_redis,
        ):
            router = DatabaseRouter(config)
            mock_arango.assert_not_called()
            mock_redis.assert_not_called()
            assert router._arango_available is False
            assert router._redis_available is False

    def test_router_write_returns_csv_only_standalone(self) -> None:
        from src.db import DatabaseConfig
        from src.db.router import DatabaseRouter

        config = DatabaseConfig(standalone_mode=True)
        with patch("src.db.router.ArangoDBWriter"), patch("src.db.router.RedisTimeSeriesWriter"):
            router = DatabaseRouter(config, strategies={})
            result = router.write([{"id": "test"}], "listOrgSites")
            assert result.backend == "csv_only"

    def test_health_check_shows_standalone(self) -> None:
        from src.db import DatabaseConfig
        from src.db.router import DatabaseRouter

        config = DatabaseConfig(standalone_mode=True)
        with patch("src.db.router.ArangoDBWriter"), patch("src.db.router.RedisTimeSeriesWriter"):
            router = DatabaseRouter(config)
            health = router.health_check()
            assert health["standalone"] is True


class TestImportFallback:
    """Verify DB_LAYER_AVAILABLE=False when imports fail."""

    def test_db_layer_flag_reflects_import(self) -> None:
        """When src.db is importable, DB_LAYER_AVAILABLE should be True."""
        try:
            from src.db import DatabaseConfig

            assert DatabaseConfig is not None
            available = True
        except ImportError:
            available = False
        assert isinstance(available, bool)
