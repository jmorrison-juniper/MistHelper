"""
Unit and integration tests for MistHelper CLI and utility functions.

- Tests CLI argument parsing, menu actions, and error handling.
- Tests data flattening, CSV escaping, and utility helpers.
- Requires pytest and MistHelper dependencies.
"""

import sys  # Who: Python standard library; What: System-specific parameters and functions; When: Used for CLI args; Where: Top of file; Why: To simulate CLI input
import pytest  # Who: Pytest authors; What: Testing framework; When: Test run; Where: Top of file; Why: To run and assert tests
import mistapi  # Who: Mist API SDK; What: Mist API interface; When: Used in tests; Where: Top of file; Why: To mock API calls
from MistHelper import MistHelper  # Who: MistHelper author; What: Imports main module; When: Test run; Where: Top of file; Why: To test CLI and functions

# =====================
# CLI/Menu/Integration Tests
# =====================

def test_cli_menu_action_valid(monkeypatch):
    """Test CLI with a valid menu action argument."""
    # Simulate CLI args for a valid menu action (e.g., "11" for export_org_site_list)
    test_args = ["MistHelper.py", "-M", "11"]  # Simulated CLI args
    monkeypatch.setattr(sys, "argv", test_args)  # Patch sys.argv
    # Patch the menu action function to track if it was called
    called = {}
    def fake_export_org_site_list():
        called["ran"] = True
    MistHelper.menu_actions["11"] = (fake_export_org_site_list, "desc")  # Patch menu action
    monkeypatch.setattr(mistapi.cli, "select_org", lambda apisession: ["dummy-org-id"])  # Patch org selection
    # Run main CLI block
    with pytest.raises(SystemExit) as e:
        MistHelper.main()
    assert called.get("ran") is True  # Check if action ran
    assert e.value.code == 0  # Should exit with code 0

def test_cli_menu_action_invalid(monkeypatch, capsys):
    """Test CLI with an invalid menu action argument."""
    # Simulate CLI args for an invalid menu action
    test_args = ["MistHelper.py", "-M", "99"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setattr(mistapi.cli, "select_org", lambda apisession: ["dummy-org-id"])
    with pytest.raises(SystemExit) as e:
        MistHelper.main()
    captured = capsys.readouterr()
    assert "Invalid menu option" in captured.out
    assert e.value.code == 1

def test_cli_site_name_resolution(monkeypatch):
    """Test CLI site name resolution failure (site not found)."""
    # Simulate CLI args with a site name that does not exist
    test_args = ["MistHelper.py", "-M", "11", "-S", "NonexistentSite"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setattr(mistapi.cli, "select_org", lambda apisession: ["dummy-org-id"])
    # Patch MistHelper.mistapi.get_all to return empty list for sites
    monkeypatch.setattr(MistHelper.mistapi, "get_all", lambda *a, **kw: [])
    with pytest.raises(SystemExit) as e:
        MistHelper.main()
    assert e.value.code == 1

def test_interactive_menu(monkeypatch, capsys):
    """Test interactive menu with valid user input."""
    # Simulate no CLI args and user entering a valid menu option
    test_args = ["MistHelper.py"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setattr("builtins.input", lambda _: "11")
    called = {}
    def fake_export_org_site_list():
        called["ran"] = True
    MistHelper.menu_actions["11"] = (fake_export_org_site_list, "desc")
    with pytest.raises(SystemExit):
        MistHelper.main()
    assert called.get("ran") is True

def test_interactive_menu_invalid(monkeypatch, capsys):
    """Test interactive menu with invalid user input."""
    # Simulate no CLI args and user entering an invalid menu option
    test_args = ["MistHelper.py"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setattr("builtins.input", lambda _: "99")
    with pytest.raises(SystemExit):
        MistHelper.main()
    captured = capsys.readouterr()
    assert "Invalid selection" in captured.out

def test_main_exits_properly(monkeypatch):
    """Test main exits properly on valid input."""
    test_args = ["MistHelper.py"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setattr("builtins.input", lambda _: "11")  # or any valid menu option
    # Patch the menu action function to avoid side effects
    called = {}
    def fake_export_org_site_list():
        called["ran"] = True
    MistHelper.menu_actions["11"] = (fake_export_org_site_list, "desc")
    with pytest.raises(SystemExit) as e:
        MistHelper.main()
    assert called.get("ran") is True
    assert e.value.code == 0

def test_cli_with_org_arg(monkeypatch):
    """Test CLI with organization argument."""
    # Simulate CLI args with org argument and valid menu
    test_args = ["MistHelper.py", "-O", "test-org", "-M", "11"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setattr(mistapi.cli, "select_org", lambda apisession: ["test-org"])
    called = {}
    def fake_export_org_site_list():
        called["ran"] = True
    MistHelper.menu_actions["11"] = (fake_export_org_site_list, "desc")
    with pytest.raises(SystemExit) as e:
        MistHelper.main()
    assert called.get("ran") is True
    assert e.value.code == 0

def test_cli_with_invalid_site(monkeypatch, capsys):
    """Test CLI with an invalid site argument."""
    # Simulate CLI args with a site name that does not exist
    test_args = ["MistHelper.py", "-M", "11", "-S", "FakeSite"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setattr(mistapi.cli, "select_org", lambda apisession: ["dummy-org-id"])
    monkeypatch.setattr(mistapi, "get_all", lambda *a, **kw: [{"name": "RealSite", "id": "123"}])
    with pytest.raises(SystemExit) as e:
        MistHelper.main()
    captured = capsys.readouterr()
    assert "not found" in captured.out
    assert e.value.code == 1

def test_cli_with_invalid_device(monkeypatch, capsys):
    """Test CLI with a valid site but invalid device argument."""
    # Simulate CLI args with a valid site but invalid device name
    test_args = ["MistHelper.py", "-M", "11", "-S", "SiteA", "-D", "NoDevice"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setattr(mistapi.cli, "select_org", lambda apisession: ["dummy-org-id"])
    monkeypatch.setattr(
        mistapi, "get_all",
        lambda *a, **kw: [{"name": "SiteA", "id": "site-1"}] if a and "sites" in str(a[0]) else [{"name": "DeviceA", "id": "dev-1"}]
    )
    with pytest.raises(SystemExit) as e:
        MistHelper.main()
    captured = capsys.readouterr()
    assert "not found" in captured.out
    assert e.value.code == 1

def test_cli_with_valid_site_and_device(monkeypatch):
    """Test CLI with valid site and device arguments."""
    import random
    import os
    from dotenv import load_dotenv
    from MistHelper import MistHelper

    MistHelper.org_id = None  # Reset global org_id to force reload from env
    load_dotenv()
    org_id = MistHelper.get_cached_or_prompted_org_id()
    apisession = MistHelper.apisession
    response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
    sites = mistapi.get_all(response=response, mist_session=apisession)
    if not sites:
        pytest.skip("No sites found in org; skipping test.")
    site = random.choice(sites)
    site_name = site["name"]
    site_id = site["id"]
    response = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id)
    devices = mistapi.get_all(response=response, mist_session=apisession)
    if not devices:
        pytest.skip(f"No devices found for site {site_name}; skipping test.")
    device = random.choice(devices)
    device_name = device["name"]
    device_id = device["id"]
    test_args = ["MistHelper.py", "-M", "11", "-O", org_id, "-S", site_name, "-D", device_name]
    monkeypatch.setattr(sys, "argv", test_args)
    called = {}
    def fake_export_org_site_list(**kwargs):
        called["ran"] = True
    MistHelper.menu_actions["11"] = (fake_export_org_site_list, "desc")
    with pytest.raises(SystemExit) as e:
        MistHelper.main()
    assert called.get("ran") is True
    assert e.value.code == 0

def test_interactive_menu_empty_input(monkeypatch, capsys):
    """Test interactive menu with empty user input."""
    # Simulate user pressing enter (empty input) in interactive menu
    test_args = ["MistHelper.py"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setattr("builtins.input", lambda _: "")
    with pytest.raises(SystemExit):
        MistHelper.main()
    captured = capsys.readouterr()
    assert "Invalid selection" in captured.out

def test_interactive_menu_non_numeric_input(monkeypatch, capsys):
    """Test interactive menu with non-numeric user input."""
    # Simulate user entering a non-numeric invalid menu option
    test_args = ["MistHelper.py"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setattr("builtins.input", lambda _: "foobar")
    with pytest.raises(SystemExit):
        MistHelper.main()
    captured = capsys.readouterr()
    assert "Invalid selection" in captured.out

def test_cli_with_port_arg(monkeypatch):
    """Test CLI with port argument (should not affect menu action)."""
    # Simulate CLI args with port argument (should not affect menu action)
    test_args = ["MistHelper.py", "-M", "11", "-P", "eth0"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setattr(mistapi.cli, "select_org", lambda apisession: ["dummy-org-id"])
    called = {}
    def fake_export_org_site_list():
        called["ran"] = True
    MistHelper.menu_actions["11"] = (fake_export_org_site_list, "desc")
    with pytest.raises(SystemExit) as e:
        MistHelper.main()
    assert called.get("ran") is True
    assert e.value.code == 0

# =====================
# flatten_dict_recursively Tests
# =====================

from MistHelper.MistHelper import (  # Who: MistHelper author; What: Imports utility functions; When: Test run; Where: After CLI tests; Why: To test data utilities
    flatten_dict_recursively,
    flatten_nested_fields_in_list,
    escape_multiline_strings_for_csv,
    convert_list_values_to_csv_strings,
    get_all_unique_dict_keys,
)

def test_flatten_nested_dict_simple():
    """Test flattening a simple nested dictionary."""
    d = {"a": 1, "b": {"c": 2, "d": 3}}
    flat = flatten_dict_recursively(d)
    assert flat == {"a": 1, "b_c": 2, "b_d": 3}

def test_flatten_nested_dict_with_list():
    """Test flattening a dictionary with a list value."""
    d = {"a": [1, 2, 3], "b": {"c": [4, 5]}}
    flat = flatten_dict_recursively(d)
    assert flat["a"] == "1,2,3"
    assert flat["b_c"] == "4,5"

def test_flatten_nested_dict_with_list_of_dicts():
    """Test flattening a dictionary with a list of dicts."""
    d = {"a": [{"x": 1}, {"y": 2}], "b": 3}
    flat = flatten_dict_recursively(d)
    assert flat["a_0_x"] == 1
    assert flat["a_1_y"] == 2
    assert flat["b"] == 3

def test_flatten_nested_dict_deeply_nested():
    """Test flattening a deeply nested dictionary."""
    d = {"a": {"b": {"c": {"d": 1}}}}
    flat = flatten_dict_recursively(d)
    assert flat == {"a_b_c_d": 1}

def test_flatten_nested_dict_with_mixed_list_types():
    """Test flattening a dict with a list of mixed types."""
    d = {"a": [1, {"b": 2}, 3]}
    flat = flatten_dict_recursively(d)
    # Should join as string, not flatten dict inside list
    assert flat["a"] == "1,{'b': 2},3" or flat["a"] == "1,{\"b\": 2},3"

def test_flatten_nested_dict_empty():
    """Test flattening an empty dictionary."""
    d = {}
    flat = flatten_dict_recursively(d)
    assert flat == {}

def test_flatten_dict_recursively_with_none_values():
    """Test flatten_dict_recursively with None values in nested dict."""
    d = {"a": None, "b": {"c": None}}
    flat = flatten_dict_recursively(d)
    assert flat["a"] is None
    assert flat["b_c"] is None

# =====================
# flatten_nested_fields_in_list Tests
# =====================

def test_flatten_all_nested_fields():
    """Test flattening all nested fields in a list of dicts."""
    data = [
        {"a": 1, "b": {"c": 2}},
        {"a": 2, "b": {"c": 3, "d": 4}}
    ]
    flat = flatten_nested_fields_in_list(data)
    assert flat[0]["b_c"] == 2
    assert flat[1]["b_d"] == 4

def test_flatten_all_nested_fields_with_stringified_dict():
    """Test flattening a stringified dict field."""
    data = [{"a": "{'x': 1, 'y': 2}"}]
    flat = flatten_nested_fields_in_list(data)
    # Should flatten stringified dict under key 'a'
    assert "a_x" in flat[0]
    assert "a_y" in flat[0]
    assert flat[0]["a_x"] == 1
    assert flat[0]["a_y"] == 2

def test_flatten_all_nested_fields_with_malformed_stringified_dict():
    """Test flattening with a malformed stringified dict."""
    data = [{"a": "{'x': 1, 'y': 2"}]  # missing closing brace
    flat = flatten_nested_fields_in_list(data)
    # Should leave as string if parsing fails
    assert flat[0]["a"] == "{'x': 1, 'y': 2"

def test_flatten_all_nested_fields_empty():
    """Test flattening an empty list."""
    data = []
    flat = flatten_nested_fields_in_list(data)
    assert flat == {}

def test_flatten_nested_fields_in_list_with_bytes():
    """Test flatten_nested_fields_in_list with bytes value."""
    data = [{"a": b"bytes"}]
    flat = flatten_nested_fields_in_list(data)
    assert flat[0]["a"] == b"bytes"

# =====================
# escape_multiline_strings_for_csv Tests
# =====================

def test_escape_multiline_strings():
    """Test escaping multiline strings for CSV output."""
    data = [{"a": "hello\nworld", "b": ["x", "y"]}]
    escaped = escape_multiline_strings_for_csv(data)
    assert escaped[0]["a"] == "hello\\nworld"
    assert escaped[0]["b"] == "x,y"

def test_escape_multiline_strings_with_carriage_return():
    """Test escaping multiline strings with carriage returns."""
    data = [{"a": "line1\r\nline2"}]
    escaped = escape_multiline_strings_for_csv(data)
    assert escaped[0]["a"] == "line1\\nline2"

def test_escape_multiline_strings_with_special_chars():
    """Test escaping multiline strings with special characters."""
    data = [{"a": "hello\nworld\r\n!@#$%^&*()_+"}]
    escaped = escape_multiline_strings_for_csv(data)
    assert "\\n" in escaped[0]["a"]
    assert "\r" not in escaped[0]["a"]

def test_escape_multiline_strings_empty():
    """Test escaping multiline strings in an empty list."""
    data = []
    escaped = escape_multiline_strings_for_csv(data)
    assert escaped == []

def test_escape_multiline_strings_for_csv_with_non_string():
    """Test escape_multiline_strings_for_csv with non-string, non-list value."""
    data = [{"a": 123}]
    escaped = escape_multiline_strings_for_csv(data)
    assert escaped[0]["a"] == 123

# =====================
# convert_list_values_to_csv_strings Tests
# =====================

def test_convert_list_values_to_strings():
    """Test converting list values to CSV strings."""
    data = [{"a": [1, 2, 3], "b": "test"}]
    converted = convert_list_values_to_csv_strings(data)
    assert converted[0]["a"] == "1,2,3"
    assert converted[0]["b"] == "test"

def test_convert_list_values_to_csv_strings_with_nested_lists():
    """Test convert_list_values_to_csv_strings with nested lists."""
    data = [{"a": [[1, 2], [3, 4]], "b": [5, 6]}]
    converted = convert_list_values_to_csv_strings(data)
    assert converted[0]["a"] == "[1, 2],[3, 4]"
    assert converted[0]["b"] == "5,6"

def test_convert_list_values_to_csv_strings_with_non_list():
    """Test convert_list_values_to_csv_strings with non-list values."""
    data = [{"a": "notalist", "b": 123}]
    converted = convert_list_values_to_csv_strings(data)
    assert converted[0]["a"] == "notalist"
    assert converted[0]["b"] == 123

def test_convert_list_values_to_csv_strings_with_set():
    """Test convert_list_values_to_csv_strings with set values."""
    data = [{"a": {1, 2, 3}}]
    converted = convert_list_values_to_csv_strings(data)
    assert "," in converted[0]["a"]

# =====================
# get_all_unique_dict_keys Tests
# =====================

def test_get_all_unique_keys():
    """Test getting all unique keys from a list of dicts."""
    data = [{"a": 1, "b": 2}, {"b": 3, "c": 4}]
    keys = get_all_unique_dict_keys(data)
    assert set(keys) == {"a", "b", "c"}

def test_get_all_unique_dict_keys_with_non_string_keys():
    """Test get_all_unique_dict_keys with non-string keys."""
    data = [{1: "a", "b": 2}, {"c": 3, 2: 4}]
    keys = get_all_unique_dict_keys(data)
    assert set(keys) == {"1", "2", "b", "c"}

def test_get_all_unique_dict_keys_empty_list():
    """Test get_all_unique_dict_keys with empty list."""
    keys = get_all_unique_dict_keys([])
    assert keys == []

# =====================
# MistHelper Utility Function Tests
# =====================

# Additional tests for MistHelper utility functions

def test_write_dict_list_to_csv_permission_error(monkeypatch):
    """Test write_dict_list_to_csv handles PermissionError gracefully."""
    data = [{"a": 1}]
    def fake_open(*a, **kw):
        raise PermissionError("Mocked permission error")
    monkeypatch.setattr("builtins.open", fake_open)
    # Should not raise, just log error
    try:
        write_dict_list_to_csv(data, "should_fail.csv")
    except PermissionError:
        assert False, "PermissionError should be handled internally"

def test_check_and_generate_csv_fresh(monkeypatch, tmp_path):
    """Test check_and_generate_csv uses fresh CSV and does not call generate_function."""
    called = {}
    test_file = tmp_path / "fresh.csv"
    test_file.write_text("header\nrow\n")
    def fake_generate():
        called["ran"] = True
    # Set mtime to now
    os.utime(test_file, None)
    check_and_generate_csv(str(test_file), fake_generate, freshness_minutes=15)
    assert "ran" not in called

def test_check_and_generate_csv_stale(monkeypatch, tmp_path):
    """Test check_and_generate_csv calls generate_function if file is stale."""
    called = {}
    test_file = tmp_path / "stale.csv"
    test_file.write_text("header\nrow\n")
    def fake_generate():
        called["ran"] = True
    # Set mtime to 1 hour ago
    old_time = time.time() - 3600
    os.utime(test_file, (old_time, old_time))
    check_and_generate_csv(str(test_file), fake_generate, freshness_minutes=15)
    assert "ran" in called

def test_get_rate_limited_delay_basic():
    """Test get_rate_limited_delay returns reasonable delay."""
    smoothed, delay = MistHelper.get_rate_limited_delay()
    assert 0.1 < delay < 15

# =====================
# Concurrency and Fast Mode Tests
# =====================

def test_cli_menu_action_with_fast(monkeypatch):
    """Test CLI menu action with --fast argument."""
    test_args = ["MistHelper.py", "-M", "11", "--fast"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setattr(mistapi.cli, "select_org", lambda apisession: ["dummy-org-id"])
    called = {}
    def fake_export_org_site_list(**kwargs):
        called["ran"] = True
        assert kwargs.get("fast") is True
    MistHelper.menu_actions["11"] = (fake_export_org_site_list, "desc")
    with pytest.raises(SystemExit):
        MistHelper.main()
    assert called.get("ran") is True

# =====================
# Error Handling and Edge Case Tests
# =====================

# Add tests for edge cases and error handling

def test_write_dict_list_to_csv_permission_error(monkeypatch):
    """Test write_dict_list_to_csv handles PermissionError gracefully."""
    data = [{"a": 1}]
    def fake_open(*a, **kw):
        raise PermissionError("Mocked permission error")
    monkeypatch.setattr("builtins.open", fake_open)
    # Should not raise, just log error
    try:
        write_dict_list_to_csv(data, "should_fail.csv")
    except PermissionError:
        assert False, "PermissionError should be handled internally"

def test_check_and_generate_csv_fresh(monkeypatch, tmp_path):
    """Test check_and_generate_csv uses fresh CSV and does not call generate_function."""
    called = {}
    test_file = tmp_path / "fresh.csv"
    test_file.write_text("header\nrow\n")
    def fake_generate():
        called["ran"] = True
    # Set mtime to now
    os.utime(test_file, None)
    check_and_generate_csv(str(test_file), fake_generate, freshness_minutes=15)
    assert "ran" not in called

def test_check_and_generate_csv_stale(monkeypatch, tmp_path):
    """Test check_and_generate_csv calls generate_function if file is stale."""
    called = {}
    test_file = tmp_path / "stale.csv"
    test_file.write_text("header\nrow\n")
    def fake_generate():
        called["ran"] = True
    # Set mtime to 1 hour ago
    old_time = time.time() - 3600
    os.utime(test_file, (old_time, old_time))
    check_and_generate_csv(str(test_file), fake_generate, freshness_minutes=15)
    assert "ran" in called

def test_get_rate_limited_delay_basic():
    """Test get_rate_limited_delay returns reasonable delay."""
    smoothed, delay = MistHelper.get_rate_limited_delay()
    assert 0.1 < delay < 15