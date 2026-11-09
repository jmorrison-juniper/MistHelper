"""Check SDK verification URI integration with a protected production handler."""

import logging
from io import StringIO
from unittest.mock import Mock

import mistapi
import pytest

from src.interfaces.portals.upgrade_portal.app import factory


class TestVerificationUrlSdkIntegration:
    """Keep SDK-dependent cases separate from pure filter quality analysis."""

    @pytest.mark.parametrize("value", ["(SDK_SYNTHETIC_VALUE)", "prefix(SDK_SYNTHETIC_VALUE)", "'SDK_SYNTHETIC_VALUE'"])
    def test_sdk_path_punctuation(self, value: str) -> None:
        """Check real SDK URI construction with an in-memory session."""
        session = Mock()
        mistapi.api.v1.self.update.verifySelfEmail(session, value)
        uri = session.mist_get.call_args.kwargs["uri"]
        session.mist_get.assert_called_once_with(uri=f"/api/v1/self/update/verify/{value}", query={})
        record = logging.makeLogRecord({"msg": "SDK request %s", "args": (uri,), "levelno": logging.INFO})
        output = StringIO()
        handler = factory.build_log_handler()
        handler.setStream(output)
        try:
            handler.handle(record)
            rendered = output.getvalue()
            assert "SDK_SYNTHETIC_VALUE" not in rendered
            assert "SDK request /api/v1/self/update/verify/***REDACTED***" in rendered
        finally:
            handler.close()
