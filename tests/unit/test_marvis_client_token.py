import pytest
from src.auth.token_cache import TokenCache


def test_token_cache_defaults():
    tc = TokenCache()
    assert tc.get_token() is None
    # No refresh_info provided -> attempt_refresh should be False
    assert tc.attempt_refresh() is False
