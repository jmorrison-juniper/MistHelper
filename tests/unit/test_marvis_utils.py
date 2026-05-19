"""Unit tests for MarvisDataUtils (src/marvis/marvis_utils.py).

All tests are pure logic -- no external dependencies, no API calls.
The escape_fn and flatten_fn callables are injected via simple lambdas.

Target audience: Junior NOC engineers verifying that Marvis AI response
formatting produces correct CSV-ready output.
"""

from __future__ import annotations  # Enable PEP 604 union types on Python 3.10+

from typing import Any  # Generic type hint for response data -- used by inject callables

from src.marvis.marvis_utils import MarvisDataUtils  # Module under test

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


def _identity_escape(data: list[dict[str, Any]]) -> list[dict[str, Any]]:  # No-op escape
    """Passthrough escape_fn -- returns the input list unchanged."""
    return data  # Don't modify data so tests can inspect raw output


def _identity_flatten(data: list[Any]) -> list[dict[str, Any]]:  # No-op flatten
    """Passthrough flatten_fn -- casts each item to dict and returns the list."""
    return [item if isinstance(item, dict) else {"value": str(item)} for item in data]  # Minimal conversion


def _make_utils() -> MarvisDataUtils:  # Build MarvisDataUtils with no-op helpers
    """Return a MarvisDataUtils instance with identity-passthrough callables."""
    return MarvisDataUtils(  # Inject no-op callables so tests stay pure-logic
        escape_fn=_identity_escape,  # No escaping needed for unit tests
        flatten_fn=_identity_flatten,  # No flattening needed for unit tests
    )


# ---------------------------------------------------------------------------
# format_for_csv -- edge cases
# ---------------------------------------------------------------------------


class TestFormatForCsvEdgeCases:
    """Tests for format_for_csv -- None/empty inputs and non-list responses."""

    def test_none_response_returns_empty_list(self):  # Guard against None API response
        """Returns [] when api_response_data is None."""
        utils = _make_utils()  # Create instance
        result = utils.format_for_csv(None, "generic")  # Pass None
        assert result == []  # Should return empty list without raising

    def test_empty_list_response_returns_empty_list(self):  # Guard against empty response
        """Returns [] when api_response_data is an empty list."""
        utils = _make_utils()  # Create instance
        result = utils.format_for_csv([], "client")  # Pass empty list
        assert result == []  # Should return empty list without raising

    def test_single_dict_wrapped_in_list(self):  # API sometimes returns a single dict
        """Wraps a single-dict response in a list so it is processed correctly."""
        utils = _make_utils()  # Create instance
        single_item = {"mac": "aa:bb:cc:dd:ee:ff", "status": "connected"}  # Single dict
        result = utils.format_for_csv(single_item, "generic")  # Single dict -- not a list
        assert len(result) == 1  # One item in -- one row out
        assert result[0]["mac"] == "aa:bb:cc:dd:ee:ff"  # MAC preserved in output

    def test_non_dict_item_in_list_is_skipped(self):  # Malformed item in list
        """Skips list items that are not dicts without raising an exception."""
        utils = _make_utils()  # Create instance
        data = ["not-a-dict", {"mac": "aa:bb:cc:dd:ee:ff"}]  # Mixed list
        result = utils.format_for_csv(data, "generic")  # Process mixed list
        assert len(result) == 1  # Non-dict item skipped, only dict processed
        assert result[0]["mac"] == "aa:bb:cc:dd:ee:ff"  # Valid item still present


# ---------------------------------------------------------------------------
# format_for_csv -- analysis_type='sites'
# ---------------------------------------------------------------------------


class TestFormatForCsvSites:
    """Tests for format_for_csv with analysis_type='sites' -- SLE per-site expansion."""

    def test_sites_response_expands_results_list(self):  # Each site becomes its own row
        """Sites analysis type expands the nested 'results' list into one row per site."""
        utils = _make_utils()  # Create instance
        sites_response = [  # Simulated SLE response with two sites
            {
                "org_id": "org-123",  # Top-level org field
                "results": [  # Nested per-site SLE results
                    {"site_id": "site-1", "score": 0.95},  # First site SLE
                    {"site_id": "site-2", "score": 0.88},  # Second site SLE
                ],
            }
        ]
        result = utils.format_for_csv(sites_response, "sites")  # Process sites type
        assert len(result) == 2  # Two sites in results -- should produce two rows
        site_ids = {row.get("site_id") for row in result}  # Extract site IDs
        assert "site-1" in site_ids  # First site should appear
        assert "site-2" in site_ids  # Second site should appear

    def test_sites_single_result_produces_one_row(self):  # Results with one site entry
        """A sites response with one result entry produces exactly one output row."""
        utils = _make_utils()  # Create instance
        sites_response = [  # One org, one site
            {
                "org_id": "org-999",  # org_id on the parent (not necessarily propagated)
                "results": [{"site_id": "site-A", "score": 0.92}],  # One site result
            }
        ]
        result = utils.format_for_csv(sites_response, "sites")  # Process
        assert len(result) == 1  # One site result -- one output row
        assert result[0].get("site_id") == "site-A"  # site_id field preserved in row


# ---------------------------------------------------------------------------
# format_for_csv -- analysis_type='client'/'device'/'network'/'generic'
# ---------------------------------------------------------------------------


class TestFormatForCsvStandardTypes:
    """Tests for format_for_csv with standard analysis types that use _build_flat_row."""

    def test_client_type_flattens_simple_fields(self):  # Client response without nested dicts
        """Simple scalar fields pass through unchanged for 'client' analysis type."""
        utils = _make_utils()  # Create instance
        data = [{"mac": "aa:bb:cc:dd:ee:ff", "issue": "low RSSI"}]  # Simple client dict
        result = utils.format_for_csv(data, "client")  # Process as client
        assert len(result) == 1  # One item in -- one row out
        assert result[0]["mac"] == "aa:bb:cc:dd:ee:ff"  # MAC preserved
        assert result[0]["issue"] == "low RSSI"  # Issue preserved

    def test_nested_dict_is_flattened_with_underscored_key(self):  # Nested dict expansion
        """Nested dicts are expanded into composite keys like parent_child."""
        utils = _make_utils()  # Create instance
        data = [{"device_info": {"model": "EX2300"}}]  # One level of nesting
        result = utils.format_for_csv(data, "device")  # Process as device
        assert len(result) == 1  # One row produced
        assert result[0].get("device_info_model") == "EX2300"  # Flattened key

    def test_results_array_is_index_expanded(self):  # 'results' key gets indexed expansion
        """The 'results' array is expanded into result_0_key, result_1_key columns."""
        utils = _make_utils()  # Create instance
        data = [  # Marvis client response with results array
            {
                "mac": "aa:bb:cc:dd:ee:ff",  # Top-level field
                "results": [  # Nested array of issue dicts
                    {"category": "WiFi", "reason": "low RSSI"},  # result_0_*
                ],
            }
        ]
        result = utils.format_for_csv(data, "client")  # Process
        assert result[0].get("result_0_category") == "WiFi"  # Index-prefixed key
        assert result[0].get("result_0_reason") == "low RSSI"  # Second field also prefixed

    def test_list_values_converted_to_csv_string(self):  # Lists joined as comma-separated
        """Non-results list values are joined into a comma-separated string."""
        utils = _make_utils()  # Create instance
        data = [{"tags": ["tag1", "tag2", "tag3"]}]  # Field is a list
        result = utils.format_for_csv(data, "generic")  # Process as generic
        assert result[0]["tags"] == "tag1,tag2,tag3"  # Joined as CSV-compatible string

    def test_multiple_items_produce_multiple_rows(self):  # Multiple top-level items
        """Multiple items in the response list each produce their own output row."""
        utils = _make_utils()  # Create instance
        data = [  # Two separate Marvis items
            {"mac": "aa:bb:cc:dd:ee:01", "issue": "A"},
            {"mac": "aa:bb:cc:dd:ee:02", "issue": "B"},
        ]
        result = utils.format_for_csv(data, "network")  # Process as network
        assert len(result) == 2  # Two items in -- two rows out
        macs = {row["mac"] for row in result}  # Collect MACs
        assert "aa:bb:cc:dd:ee:01" in macs  # First MAC present
        assert "aa:bb:cc:dd:ee:02" in macs  # Second MAC present


# ---------------------------------------------------------------------------
# _legacy_fallback (called when format_for_csv raises internally)
# ---------------------------------------------------------------------------


class TestLegacyFallback:
    """Tests for the _legacy_fallback path -- uses injected callables as rescue."""

    def test_fallback_wraps_single_dict_in_list(self):  # Single dict normalised before flatten
        """_legacy_fallback wraps a single dict in a list before calling flatten_fn."""
        calls: list[int] = []  # Track flatten_fn call count

        def counting_flatten(data: list) -> list:  # Custom flatten that records call count
            calls.append(len(data))  # Record the length of the list passed to flatten
            return data  # Pass through unchanged

        utils = MarvisDataUtils(  # Inject custom flatten to observe call
            escape_fn=_identity_escape, flatten_fn=counting_flatten
        )
        single_dict = {"mac": "aa:bb:cc:dd:ee:ff"}  # Single dict -- not a list
        utils._legacy_fallback(single_dict)  # Invoke fallback
        assert calls[0] == 1  # Single dict should have been wrapped in a list of 1

    def test_fallback_returns_flattened_and_escaped_data(self):  # Happy path
        """_legacy_fallback applies flatten then escape and returns the result."""
        utils = _make_utils()  # Create instance with identity callables
        data = [{"mac": "aa:bb:cc:dd:ee:ff"}]  # Minimal valid input
        result = utils._legacy_fallback(data)  # Call fallback directly
        assert result == data  # Identity callables return input unchanged
