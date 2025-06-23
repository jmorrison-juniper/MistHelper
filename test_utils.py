import sys
import pytest
import mistapi  # <-- Add this import
from MistHelper import MistHelper

def test_cli_menu_action_valid(monkeypatch):
    # Simulate CLI args for a valid menu action (e.g., "11" for export_org_site_list)
    test_args = ["MistHelper.py", "-M", "11"]
    monkeypatch.setattr(sys, "argv", test_args)
    # Patch the menu action function to track if it was called
    called = {}
    def fake_export_org_site_list():
        called["ran"] = True
    MistHelper.menu_actions["11"] = (fake_export_org_site_list, "desc")
    monkeypatch.setattr(mistapi.cli, "select_org", lambda apisession: ["dummy-org-id"])  # <-- Patch here
    # Run main CLI block
    with pytest.raises(SystemExit) as e:
        MistHelper.main()
    assert called.get("ran") is True
    assert e.value.code == 0

def test_cli_menu_action_invalid(monkeypatch, capsys):
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
    # Simulate no CLI args and user entering an invalid menu option
    test_args = ["MistHelper.py"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setattr("builtins.input", lambda _: "99")
    with pytest.raises(SystemExit):
        MistHelper.main()
    captured = capsys.readouterr()
    assert "Invalid selection" in captured.out

from MistHelper.MistHelper import (
    flatten_dict_recursively,
    flatten_nested_fields_in_list,
    escape_multiline_strings_for_csv,
    convert_list_values_to_csv_strings,
    get_all_unique_dict_keys,
)

def test_flatten_nested_dict_simple():
    d = {"a": 1, "b": {"c": 2, "d": 3}}
    flat = flatten_dict_recursively(d)
    assert flat == {"a": 1, "b_c": 2, "b_d": 3}

def test_flatten_nested_dict_with_list():
    d = {"a": [1, 2, 3], "b": {"c": [4, 5]}}
    flat = flatten_dict_recursively(d)
    assert flat["a"] == "1,2,3"
    assert flat["b_c"] == "4,5"

def test_flatten_nested_dict_with_list_of_dicts():
    d = {"a": [{"x": 1}, {"y": 2}], "b": 3}
    flat = flatten_dict_recursively(d)
    assert flat["a_0_x"] == 1
    assert flat["a_1_y"] == 2
    assert flat["b"] == 3

def test_flatten_all_nested_fields():
    data = [
        {"a": 1, "b": {"c": 2}},
        {"a": 2, "b": {"c": 3, "d": 4}}
    ]
    flat = flatten_nested_fields_in_list(data)
    assert flat[0]["b_c"] == 2
    assert flat[1]["b_d"] == 4

def test_flatten_all_nested_fields_with_stringified_dict():
    data = [{"a": "{'x': 1, 'y': 2}"}]
    flat = flatten_nested_fields_in_list(data)
    # Should flatten stringified dict under key 'a'
    assert "a_x" in flat[0]
    assert "a_y" in flat[0]
    assert flat[0]["a_x"] == 1
    assert flat[0]["a_y"] == 2

def test_escape_multiline_strings():
    data = [{"a": "hello\nworld", "b": ["x", "y"]}]
    escaped = escape_multiline_strings_for_csv(data)
    assert escaped[0]["a"] == "hello\\nworld"
    assert escaped[0]["b"] == "x,y"

def test_escape_multiline_strings_with_carriage_return():
    data = [{"a": "line1\r\nline2"}]
    escaped = escape_multiline_strings_for_csv(data)
    assert escaped[0]["a"] == "line1\\nline2"

def test_convert_list_values_to_strings():
    data = [{"a": [1, 2, 3], "b": "test"}]
    converted = convert_list_values_to_csv_strings(data)
    assert converted[0]["a"] == "1,2,3"
    assert converted[0]["b"] == "test"

def test_get_all_unique_keys():
    data = [{"a": 1, "b": 2}, {"b": 3, "c": 4}]
    keys = get_all_unique_dict_keys(data)
    assert set(keys) == {"a", "b", "c"}

def test_flatten_nested_dict_empty():
    d = {}
    flat = flatten_dict_recursively(d)
    assert flat == {}

def test_flatten_all_nested_fields_empty():
    data = []
    flat = flatten_nested_fields_in_list(data)
    assert flat == []

def test_escape_multiline_strings_empty():
    data = []
    escaped = escape_multiline_strings_for_csv(data)
    assert escaped == []

def test_main_exits_properly(monkeypatch):
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
    # Simulate user pressing enter (empty input) in interactive menu
    test_args = ["MistHelper.py"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setattr("builtins.input", lambda _: "")
    with pytest.raises(SystemExit):
        MistHelper.main()
    captured = capsys.readouterr()
    assert "Invalid selection" in captured.out

def test_interactive_menu_non_numeric_input(monkeypatch, capsys):
    # Simulate user entering a non-numeric invalid menu option
    test_args = ["MistHelper.py"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setattr("builtins.input", lambda _: "foobar")
    with pytest.raises(SystemExit):
        MistHelper.main()
    captured = capsys.readouterr()
    assert "Invalid selection" in captured.out

def test_cli_with_port_arg(monkeypatch):
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

def test_flatten_all_nested_fields_with_malformed_stringified_dict():
    """Test flattening with a malformed stringified dict (should not raise)."""
    data = [{"a": "{'x': 1, 'y': 2"}]  # missing closing brace
    flat = flatten_nested_fields_in_list(data)
    # Should leave as string if parsing fails
    assert flat[0]["a"] == "{'x': 1, 'y': 2"

def test_escape_multiline_strings_with_special_chars():
    """Test escaping multiline strings with special characters."""
    data = [{"a": "hello\nworld\r\n!@#$%^&*()_+"}]
    escaped = escape_multiline_strings_for_csv(data)
    assert "\\n" in escaped[0]["a"]
    assert "\r" not in escaped[0]["a"]

def test_get_all_unique_dict_keys_with_non_string_keys():
    """Test get_all_unique_dict_keys with non-string keys (should handle gracefully)."""
    data = [{1: "a", "b": 2}, {"c": 3, 2: 4}]
    keys = get_all_unique_dict_keys(data)
    assert set(keys) == {"1", "2", "b", "c"}

def test_convert_list_values_to_csv_strings_with_nested_lists():
    """Test convert_list_values_to_csv_strings with nested lists (should join only top-level)."""
    data = [{"a": [[1, 2], [3, 4]], "b": [5, 6]}]
    converted = convert_list_values_to_csv_strings(data)
    assert converted[0]["a"] == "[1, 2],[3, 4]"
    assert converted[0]["b"] == "5,6"

def test_convert_list_values_to_csv_strings_with_non_list():
    """Test convert_list_values_to_csv_strings with non-list values (should not change)."""
    data = [{"a": "notalist", "b": 123}]
    converted = convert_list_values_to_csv_strings(data)
    assert converted[0]["a"] == "notalist"
    assert converted[0]["b"] == 123