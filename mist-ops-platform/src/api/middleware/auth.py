"""Auth middleware — Bearer token + session cookie with privilege caching (T020).

Validates the ``Authorization: Bearer <token>`` header or a session cookie.
Privilege data is cached in Redis for 5 minutes to avoid repeated lookups.
Scope enforcement: query results are filtered to the user's MSP/org/site
privileges (FR-025).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)
_bearer_scheme = HTTPBearer(auto_error=False)

PRIVILEGE_CACHE_TTL = 300  # 5 minutes


@dataclass(slots=True)
class CurrentUser:
    """Represents the authenticated caller and their privilege scope."""

    token: str
    email: str = ""
    org_ids: list[str] = field(default_factory=list)
    site_ids: list[str] = field(default_factory=list)
    is_msp: bool = False
    privileges: dict = field(default_factory=dict)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser:
    """Extract and validate caller identity from the request."""
    token = _extract_token(request, credentials)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
        )
    from src.shared.services.auth import AuthService

    svc = AuthService(redis=None)
    privs = svc.validate_token(token)
    if not privs.email and not privs.org_ids:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return CurrentUser(
        token=token,
        email=privs.email,
        org_ids=privs.org_ids,
        site_ids=privs.site_ids,
        is_msp=privs.is_msp,
    )


def _extract_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    """Return token from Bearer header or session cookie."""
    if credentials and credentials.credentials:
        return credentials.credentials
    return request.cookies.get("mist_session")


def require_org_access(org_id: str, user: CurrentUser) -> None:
    """Raise 403 if user lacks access to the specified org."""
    if user.is_msp:
        return
    if org_id not in user.org_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges for this organization",
        )
