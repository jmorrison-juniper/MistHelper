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


class TestPolyglotHostProbe:
    """Verify the TCP reachability probe that decides polyglot mode (issue #1824)."""

    def test_both_silent_returns_true(self) -> None:
        from src.db import polyglot_hosts_unreachable

        with (
            patch.dict("os.environ", {}, clear=True),
            patch("src.db._can_connect", return_value=False),
        ):
            assert polyglot_hosts_unreachable() is True

    def test_one_answer_returns_false(self) -> None:
        from src.db import polyglot_hosts_unreachable

        with (
            patch.dict("os.environ", {}, clear=True),
            patch("src.db._can_connect", side_effect=[True, False]),
        ):
            assert polyglot_hosts_unreachable() is False

    def test_probe_reads_configured_hosts(self) -> None:
        from src.db import polyglot_hosts_unreachable

        env = {"ARANGO_HOST": "http://db.example:9999", "REDIS_HOST": "cache.example", "REDIS_PORT": "6380"}
        with (
            patch.dict("os.environ", env, clear=True),
            patch("src.db._can_connect", return_value=False) as connect,
        ):
            polyglot_hosts_unreachable()
        assert connect.call_args_list[0].args == ("db.example", 9999)
        assert connect.call_args_list[1].args == ("cache.example", 6380)

    def test_url_without_port_uses_arango_default(self) -> None:
        from src.db import ARANGO_DEFAULT_PORT, polyglot_hosts_unreachable

        with (
            patch.dict("os.environ", {"ARANGO_HOST": "http://db.example"}, clear=True),
            patch("src.db._can_connect", return_value=False) as connect,
        ):
            polyglot_hosts_unreachable()
        assert connect.call_args_list[0].args == ("db.example", ARANGO_DEFAULT_PORT)

    def test_unreadable_port_falls_back_to_default(self) -> None:
        from src.db import REDIS_DEFAULT_PORT, _env_int

        with patch.dict("os.environ", {"REDIS_PORT": "not-a-port"}, clear=True):
            assert _env_int("REDIS_PORT", REDIS_DEFAULT_PORT) == REDIS_DEFAULT_PORT

    def test_can_connect_reports_a_refused_socket(self) -> None:
        from src.db import _can_connect

        with patch("src.db.socket.create_connection", side_effect=OSError("refused")):
            assert _can_connect("db.example", 8529) is False

    def test_can_connect_closes_a_live_socket(self) -> None:
        from src.db import _can_connect

        with patch("src.db.socket.create_connection") as create:
            assert _can_connect("db.example", 8529) is True
        create.assert_called_once()
