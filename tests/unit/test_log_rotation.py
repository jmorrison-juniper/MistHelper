"""Test bounded rotation for both MistHelper logging setup paths."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from MistHelper import GlobalImportManager, LogRotationSettings, _early_file_handler


class TestLogRotationSettings:
    """Verify safe defaults, overrides, and rollover behavior."""

    def test_defaults_bound_log_size(self, monkeypatch):
        """The default configuration limits size and retains five backups."""
        monkeypatch.delenv("LOGGING_MAX_BYTES", raising=False)
        monkeypatch.delenv("LOGGING_BACKUP_COUNT", raising=False)

        settings = LogRotationSettings.from_environment()

        assert settings.max_bytes == 10 * 1024 * 1024
        assert settings.backup_count == 5

    def test_early_setup_uses_a_rotating_handler(self):
        """The import-time setup path uses a bounded rotating handler."""
        assert isinstance(_early_file_handler, RotatingFileHandler)
        assert _early_file_handler.maxBytes > 0
        assert _early_file_handler.backupCount >= 0

    def test_invalid_values_use_safe_defaults(self, monkeypatch):
        """Malformed or unsafe values cannot disable rotation."""
        monkeypatch.setenv("LOGGING_MAX_BYTES", "not-an-integer")
        monkeypatch.setenv("LOGGING_BACKUP_COUNT", "-1")

        settings = LogRotationSettings.from_environment()

        assert settings.max_bytes == 10 * 1024 * 1024
        assert settings.backup_count == 5

    def test_normal_setup_uses_configured_rotating_handler(self, tmp_path, monkeypatch):
        """The normal setup path applies deployment rotation settings."""
        monkeypatch.setenv("LOGGING_MAX_BYTES", "128")
        monkeypatch.setenv("LOGGING_BACKUP_COUNT", "2")
        manager = GlobalImportManager.__new__(GlobalImportManager)
        monkeypatch.chdir(tmp_path)

        handler = manager._build_file_log_handler(logging.INFO)

        assert isinstance(handler, RotatingFileHandler)
        assert handler.maxBytes == 128
        assert handler.backupCount == 2
        handler.close()

    def test_rotating_handler_preserves_active_log_and_backups(self, tmp_path):
        """The configured handler creates backups and keeps the active log."""
        log_path = tmp_path / "script.log"
        settings = LogRotationSettings(max_bytes=64, backup_count=2)
        handler = settings.build_handler(str(log_path))
        logger = logging.getLogger("test-log-rotation")
        logger.handlers = [handler]
        logger.setLevel(logging.INFO)
        logger.propagate = False

        for index in range(20):
            logger.info("rotation record %s with enough text to cross the limit", index)

        handler.close()
        assert log_path.exists()
        assert (tmp_path / "script.log.1").exists()
        assert (tmp_path / "script.log.2").exists()
