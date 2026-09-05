"""Secret masking filter for audit logs.

Redacts sensitive data from audit entries to ensure no secrets
are stored in queryable logs (SC-010 compliance).
"""

import re  # WHY: pattern matching for token detection
from typing import Any, Dict  # WHY: type hints for dynamic data structures

import structlog  # WHY: structured logging

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger


class SecretMasker:
    """Redacts sensitive data from audit entries."""

    # WHY: patterns for common secret formats
    PATTERNS = {
        'jwt_token': re.compile(r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.?[A-Za-z0-9_-]*'),  # WHY: JWT format (OIDC/OAuth2)
        'api_key': re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]+)["\']?', re.IGNORECASE),  # WHY: API key declarations
        'password': re.compile(r'(password|pwd)["\']?\s*[:=]\s*["\']?([^"\']*)["\']?', re.IGNORECASE),  # WHY: password field values
        'auth_token': re.compile(r'(auth|bearer|token)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]+)["\']?', re.IGNORECASE),  # WHY: generic auth tokens
        'mist_token': re.compile(r'x-api-token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]+)["\']?', re.IGNORECASE),  # WHY: Mist API token header
    }  # WHY: centralized regex patterns for detection

    def __init__(self, mask_char: str = '*', mask_length: int = 8):
        """Initialize masker with mask character and length.

        Args:
            mask_char: Character to use for masking (default: '*').
            mask_length: Number of mask characters to show (default: 8).

        WHY: configurable masking allows balancing readability with security.
        """
        # WHY: store masking configuration for redaction
        self.mask_char = mask_char  # WHY: character for redaction
        self.mask_length = mask_length  # WHY: number of mask chars to display
        self.mask_placeholder = mask_char * mask_length  # WHY: pre-built mask string for efficiency

    def mask_string(self, value: str) -> str:
        """Mask a sensitive string value.

        Args:
            value: The string to mask.

        Returns:
            Masked string with format: ORIGINAL_FIRST_3_CHARS...LAST_3_CHARS

        WHY: preserve first and last chars for debugging without exposing full secrets.
        """
        # WHY: return placeholder for empty or None values
        if not value or len(value) < 8:  # WHY: too short to mask meaningfully
            return self.mask_placeholder  # WHY: redact entirely for short tokens
        # WHY: show prefix and suffix for context while hiding middle
        prefix = value[:3]  # WHY: first 3 chars for debugging context
        suffix = value[-3:]  # WHY: last 3 chars for debugging context
        return f"{prefix}{self.mask_placeholder}{suffix}"  # WHY: redacted format with context

    def mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively mask sensitive values in a dictionary.

        Args:
            data: Dictionary to mask (can be nested).

        Returns:
            New dictionary with sensitive values redacted.

        WHY: recursive processing handles nested auth objects and complex payloads.
        """
        # WHY: deep copy and recursive masking for nested structures
        if not isinstance(data, dict):  # WHY: type safety
            return data  # WHY: non-dict pass through
        # WHY: iterate and mask all values
        masked = {}  # WHY: new dict for masked output
        for key, value in data.items():  # WHY: process each field
            # WHY: detect and mask sensitive keys
            if self._is_sensitive_key(key):  # WHY: check key name
                masked[key] = self.mask_string(str(value)) if value else None  # WHY: redact sensitive field
            # WHY: recursively process nested dicts
            elif isinstance(value, dict):  # WHY: handle nested objects
                masked[key] = self.mask_dict(value)  # WHY: recursive masking
            # WHY: process list items for nested sensitive data
            elif isinstance(value, list):  # WHY: handle arrays
                masked[key] = [  # WHY: mask items in list
                    self.mask_dict(item) if isinstance(item, dict) else item  # WHY: recursively mask dict items
                    for item in value  # WHY: iterate list
                ]  # WHY: list comprehension for efficiency
            else:
                # WHY: check string values for token patterns
                if isinstance(value, str) and self._contains_secret(value):  # WHY: pattern matching
                    masked[key] = self._mask_matches(value)  # WHY: redact matched patterns
                else:
                    masked[key] = value  # WHY: pass through non-sensitive values
        return masked  # WHY: return masked output

    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key name indicates sensitive data.

        Args:
            key: Key name to check.

        Returns:
            True if key is known to contain sensitive data.

        WHY: key-based detection is first-pass filter before pattern matching.
        """
        # WHY: case-insensitive check against known sensitive key names
        sensitive_keys = {  # WHY: set for O(1) lookup
            'token', 'api_key', 'apikey', 'password', 'pwd', 'secret',  # WHY: common auth keys
            'x-api-token', 'authorization', 'bearer', 'auth',  # WHY: HTTP auth headers
            'mist_token', 'jwt', 'oauth', 'access_token', 'refresh_token',  # WHY: token types
        }  # WHY: whitelist of known sensitive key names
        return key.lower() in sensitive_keys  # WHY: case-insensitive match

    def _contains_secret(self, value: str) -> bool:
        """Check if a string contains a secret pattern.

        Args:
            value: String to check.

        Returns:
            True if value matches a known secret pattern.

        WHY: pattern-based detection catches secrets not caught by key names.
        """
        # WHY: check against all registered patterns
        for pattern in self.PATTERNS.values():  # WHY: iterate patterns
            if pattern.search(value):  # WHY: pattern match
                return True  # WHY: secret detected
        return False  # WHY: no secret found

    def _mask_matches(self, value: str) -> str:
        """Mask all matched secret patterns in a string.

        Args:
            value: String containing secrets.

        Returns:
            String with all matched patterns redacted.

        WHY: handles cases where a single string contains multiple secrets.
        """
        # WHY: replace all pattern matches with masked versions
        result = value  # WHY: start with original
        for pattern in self.PATTERNS.values():  # WHY: iterate patterns
            # WHY: replace each match with mask
            result = pattern.sub(lambda m: self.mask_placeholder, result)  # WHY: regex substitution
        return result  # WHY: return masked string
