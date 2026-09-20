"""Tests for narrowed exception handlers in the JWT session manager."""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.auth import session as auth_session
from src.upgrade_portal.auth.session import JWTSessionManager


def test_validate_token_unexpected_decode_attribute_error_reaches_operator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A broken JWT library surface must not become an invalid token."""
    manager = JWTSessionManager("secret")  # Build the product manager with a test signing key.

    def broken_decode(*args: Any, **kwargs: Any) -> dict[str, Any]:
        """Raise the way a missing library method can fail."""
        raise AttributeError("decode endpoint is absent")  # Model an unexpected library surface defect.

    monkeypatch.setattr(auth_session.jwt, "decode", broken_decode)  # Replace only the JWT decode boundary.

    with pytest.raises(AttributeError, match="decode endpoint is absent"):  # Prove the defect reaches the caller.
        manager.validate_token("token")  # Drive the validation handler that used to hide this class.


def test_refresh_grace_decode_attribute_error_reaches_operator(monkeypatch: pytest.MonkeyPatch) -> None:
    """A broken grace-period decode must not become a token expiry."""
    manager = JWTSessionManager("secret")  # Build the product manager with a test signing key.
    monkeypatch.setattr(  # Force the grace-period branch without building an expired token.
        manager,
        "validate_token",
        lambda token: (False, None, "token_expired"),
    )

    def broken_decode(*args: Any, **kwargs: Any) -> dict[str, Any]:
        """Raise the way a missing library method can fail."""
        raise AttributeError("grace decode endpoint is absent")  # Model an unexpected library surface defect.

    monkeypatch.setattr(auth_session.jwt, "decode", broken_decode)  # Replace only the JWT decode boundary.

    with pytest.raises(AttributeError, match="grace decode endpoint is absent"):  # Prove no broad swallow remains.
        manager.refresh_token("token")  # Drive the refresh handler that used to hide this class.


def test_refresh_create_token_attribute_error_reaches_operator(monkeypatch: pytest.MonkeyPatch) -> None:
    """A broken refresh token creator must not become a refresh error."""
    manager = JWTSessionManager("secret")  # Build the product manager with a test signing key.
    payload = {"user_id": "user-1", "iat": 1, "exp": 2, "issued_at": 1, "expires_at": 2}  # Valid core claims.
    monkeypatch.setattr(manager, "validate_token", lambda token: (True, payload, None))  # Enter create path.

    def broken_create_token(*args: Any, **kwargs: Any) -> str:
        """Raise the way an unexpected creator defect can fail."""
        raise AttributeError("create token dependency is absent")  # Model an unexpected internal defect.

    monkeypatch.setattr(manager, "create_token", broken_create_token)  # Replace only the token creation boundary.

    with pytest.raises(AttributeError, match="create token dependency is absent"):  # Prove no broad swallow remains.
        manager.refresh_token("token")  # Drive the outer refresh handler that used to hide this class.
