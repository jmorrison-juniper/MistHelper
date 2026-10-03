"""Value and error contracts for frame reading."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from dataclasses import dataclass  # FrameRead is a small immutable value.


class ConnectionClosed(Exception):
    """A WebSocket connection ended."""

    def __init__(self, code: int | None = None, dropped: bool = True) -> None:
        """Store the close code and origin."""
        super().__init__("The WebSocket connection closed.")  # Keep the public error message stable.
        self.code = code  # Runners distinguish close status codes.
        self.dropped = dropped  # Local close is not a dropped connection.


@dataclass(frozen=True, slots=True)
class FrameRead:
    """One application data frame."""

    opcode: int  # The WebSocket opcode identifies text or binary data.
    payload: bytes  # The caller owns payload decoding.


class FrameValues:
    """Normalize untrusted websocket-client frame values."""

    @staticmethod
    def payload_bytes(payload: object) -> bytes:
        """Return payload bytes without logging payload content."""
        if isinstance(payload, bytes):  # websocket-client normally returns bytes.
            return payload  # Preserve exact bytes.
        if isinstance(payload, str):  # Some test fakes return text.
            return payload.encode("utf-8")  # Encode text fakes as UTF-8.
        return bytes(payload) if isinstance(payload, bytearray) else b""  # Unknown payloads become empty.

    @staticmethod
    def close_code(payload: bytes) -> int:
        """Return the close code or RFC 6455 code 1005."""
        if len(payload) < 2:  # RFC 6455 defines 1005 when no status code arrived.
            return 1005  # Preserve the prior empty close frame behavior.
        return int.from_bytes(payload[:2], "big")  # Close codes use big-endian bytes.
