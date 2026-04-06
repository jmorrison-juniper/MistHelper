"""Example Hypothesis property-based test for MistHelper.

Demonstrates how Feature Spec Issues define test properties for Hypothesis.
Property-based testing generates random inputs to verify invariants hold
across a wide range of cases, catching edge cases that example-based tests miss.

Usage in Feature Specs:
    When writing a Feature Spec Issue, include a "Test Plan" section that
    defines properties like:
      - "For any valid hostname, validate_hostname returns True"
      - "For any dict, flatten_dict produces only string keys"
      - "For any page_limit > 0, API pagination returns <= page_limit items"

    These property definitions translate directly to @given decorators.
"""

import pytest
try:
    from hypothesis import given, settings
    from hypothesis import strategies as st
except Exception as _hyp_err:
    pytest.skip(f"Skipping Hypothesis tests due to hypothesis import error: {_hyp_err}", allow_module_level=True)


@given(st.dictionaries(st.text(min_size=1), st.integers() | st.text() | st.none()))
@settings(max_examples=50)
def test_flatten_dict_produces_string_keys(input_dict: dict) -> None:
    """Property: flatten_dict always produces string keys regardless of input."""
    result = _simple_flatten(input_dict)
    for key in result:
        assert isinstance(key, str), f"Expected string key, got {type(key)}: {key}"


@given(
    st.text(
        min_size=1,
        max_size=253,
        alphabet=st.characters(
            whitelist_categories=(),
            whitelist_characters="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.",
        ),
    )
)
@settings(max_examples=50)
def test_hostname_chars_are_preserved(hostname: str) -> None:
    """Property: hostname normalization preserves alphanumeric chars and hyphens."""
    normalized = hostname.strip().lower()
    for char in normalized:
        assert char.isalnum() or char in "-.", f"Unexpected char in hostname: {char}"


def _simple_flatten(data: dict, prefix: str = "", separator: str = "_") -> dict:
    """Minimal flatten implementation for testing the property pattern."""
    items: dict = {}
    for key, value in data.items():
        new_key = f"{prefix}{separator}{key}" if prefix else str(key)
        if isinstance(value, dict):
            items.update(_simple_flatten(value, new_key, separator))
        else:
            items[new_key] = value
    return items
