"""Contract tests for the Mist SDK WebSocket interfaces."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import inspect  # The contract pins SDK signatures.

from mistapi import APISession  # The tests pin private API session fields used by the own client.
from mistapi.device_utils import ex, mxedge, srx  # The tests inspect SDK utility facades.
from mistapi.device_utils.__tools.__ws_wrapper import UtilResponse  # The tests inspect response behavior.
from mistapi.websockets.__ws_client import _MistWebsocket  # The tests pin the private client seam.


class TestWebSocketSdkContract:
    """Pin the SDK surface that the runners call."""

    def test_mist_websocket_constructor_and_callbacks(self) -> None:
        """Pin the private WebSocket client constructor and callbacks."""
        signature = inspect.signature(_MistWebsocket)  # Read the constructor signature.
        names = tuple(signature.parameters)  # Keep parameter order stable.
        assert names[:2] == ("mist_session", "channels")  # The runner passes these required parameters.
        assert "auto_reconnect" in names  # The runner enables reconnect.
        assert "max_reconnect_attempts" in names  # The runner bounds reconnect attempts.
        assert "ping_interval" in names  # The runner sets the ping interval.
        assert "queue_maxsize" in names  # The runner bounds the SDK queue.
        for callback in ("on_open", "on_message", "on_error", "on_close"):  # The runner registers these callbacks.
            assert hasattr(_MistWebsocket, callback)  # The callback method must exist.

    def test_util_response_contract(self) -> None:
        """Pin the utility response attributes and methods."""
        response = UtilResponse()  # Build the SDK response object.
        assert hasattr(response, "disconnect")  # UtilityRunner.stop calls disconnect.
        assert hasattr(response, "done")  # UtilityRunner monitors done.
        assert hasattr(response, "ws_error")  # UtilityRunner maps WebSocket errors.
        assert hasattr(response, "trigger_api_response")  # UtilityRunner maps trigger status.

    def test_capture_and_shell_signatures(self) -> None:
        """Pin the SDK functions that need custom runner arguments."""
        ex_capture = inspect.signature(ex.remotePcap)  # Read EX capture signature.
        srx_capture = inspect.signature(srx.remotePcap)  # Read SRX capture signature.
        site_mxedge = inspect.signature(mxedge.siteRemotePcap)  # Read site Mist Edge capture signature.
        shell = inspect.signature(ex.createShellSession)  # Read shell factory signature.
        assert "device_interfaces" in ex_capture.parameters  # EX capture needs device_interfaces.
        assert "device_interfaces" in srx_capture.parameters  # SRX capture needs device_interfaces.
        assert "device_interfaces" in site_mxedge.parameters  # Mist Edge capture needs device_interfaces.
        assert tuple(shell.parameters)[:3] == ("apisession", "site_id", "device_id")  # Shell target order is stable.
        assert "rows" in shell.parameters and "cols" in shell.parameters  # The runner sets terminal size.

    def test_api_session_private_transport_attributes(self) -> None:
        """Pin the private API session fields that transport uses."""
        session = APISession()  # Build the SDK session without network authentication.
        assert hasattr(session, "_cloud_uri")  # The endpoint builds the WebSocket host from this field.
        assert hasattr(session, "_apitoken")  # The endpoint builds the token header from this field.
        assert hasattr(session, "_apitoken_index")  # The endpoint reads the active token index from this field.
        assert hasattr(session, "_session")  # The endpoint reads cookies and TLS settings from this field.
        assert session._cloud_uri == ""  # A new offline session starts without a selected cloud.
        assert session._apitoken == []  # A new offline session starts without API tokens.
        assert session._apitoken_index == -1  # A new offline session starts without an active token.
        assert session._session.__class__.__name__ == "Session"  # The SDK keeps a requests Session object.
