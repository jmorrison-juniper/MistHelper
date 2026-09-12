"""Unit tests for ``private_digest`` in ``src/utils/logger_utils.py`` (issue 1733).

``private_digest`` protects personal data that is not a credential, such as a
street address. These tests prove the token is stable, is not the input, and
cannot be traced back to the input by a reader of the log.
"""

from src.utils.logger_utils import PRIVATE_DIGEST_EMPTY, private_digest  # Helper and its empty-value token.

_STREET = "742 Evergreen Terrace Suite 12"  # A private street used across the tests.


class TestPrivateDigest:
    """The digest hides the value while it stays stable across calls."""

    def test_digest_never_contains_the_input(self) -> None:
        """Prove no part of the street survives inside the token."""
        token = private_digest(_STREET)  # Build the token once.
        assert _STREET not in token  # The whole street must be absent.
        assert "Evergreen" not in token  # The street name must be absent.
        assert "742" not in token  # The house number must be absent.

    def test_digest_is_stable_for_the_same_value(self) -> None:
        """Prove two calls with the same value return the same token."""
        assert private_digest(_STREET) == private_digest(_STREET)  # An operator can follow one address.

    def test_digest_ignores_case_and_spacing(self) -> None:
        """Prove case and spacing changes do not change the token."""
        noisy = "  742   EVERGREEN terrace   Suite 12 "  # The same street with noisy case and spacing.
        assert private_digest(noisy) == private_digest(_STREET)  # Normalization keeps the token stable.

    def test_digest_differs_for_different_values(self) -> None:
        """Prove two different streets return two different tokens."""
        assert private_digest(_STREET) != private_digest("913 Evergreen Terrace")  # Tokens stay distinguishable.

    def test_digest_is_short_and_hexadecimal(self) -> None:
        """Prove the token is a 12-character lowercase hexadecimal string."""
        token = private_digest(_STREET)  # Build the token once.
        assert len(token) == 12  # A short token keeps the log line readable.
        assert all(character in "0123456789abcdef" for character in token)  # Lowercase hexadecimal only.

    def test_empty_value_returns_the_empty_token(self) -> None:
        """Prove an empty or whitespace value returns the constant empty token."""
        assert private_digest("") == PRIVATE_DIGEST_EMPTY  # An empty string has nothing to protect.
        assert private_digest("   ") == PRIVATE_DIGEST_EMPTY  # Whitespace alone has nothing to protect.
        assert private_digest(None) == PRIVATE_DIGEST_EMPTY  # A missing value has nothing to protect.
