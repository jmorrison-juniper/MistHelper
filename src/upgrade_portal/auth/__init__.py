"""Authentication and session management for upgrade portal.

Provides JWT-based stateless sessions with inactivity timeout
and expiry warnings per SC-009.
"""

# WHY: re-export public API for convenient imports
from .session import JWTSessionManager, require_token  # WHY: session management and decorators

__all__ = ['JWTSessionManager', 'require_token']
