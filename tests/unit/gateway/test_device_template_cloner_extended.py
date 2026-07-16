"""Extended unit tests for DeviceConfigTemplateClonerManager (menu 194).

Focus: internal helpers not covered by the primary test file - site/gateway
selection, device-config fetch, prompt loops, hardware resolver, and the
clone() exception path.
"""

from __future__ import annotations  # PEP 563 postponed evaluation for typing forward refs

from types import SimpleNamespace  # Build fake mistapi response objects with .data attr
from typing import Any  # Untyped kwargs need explicit Any for mypy --strict compatibility
from unittest.mock import MagicMock, patch  # MagicMock for injection, patch for mistapi calls

import pytest  # Parametrize and monkeypatch fixtures

from src.gateway.device_template_cloner import (  # SUT imports for direct manipulation
    COMMON_GATEWAY_MODELS,  # Constant list used to validate hardware picker output
    DeviceConfigTemplateClonerManager,  # Class under test
    DeviceTemplateClonerDeps,  # Frozen deps bundle required by the constructor
)


def _build_deps(**overrides: Any) -> DeviceTemplateClonerDeps:
    """Construct a deps bundle for the cloner with sensible mock defaults."""
    fields: dict[str, Any] = {  # Baseline deps - all replaced by MagicMock so tests never touch real IO
        "apisession": MagicMock(name="apisession"),  # Fake mistapi session object
        "input_fn": MagicMock(name="input_fn", return_value=""),  # Default returns empty string
        "get_csv_path_fn": MagicMock(name="get_csv_path_fn", return_value="data/test.csv"),  # Path stub
        "save_data_fn": MagicMock(name="save_data_fn"),  # Legacy CSV writer stub
        "write_csv_fn": MagicMock(name="write_csv_fn"),  # PK-aware writer stub
    }
    fields.update(overrides)  # Allow individual tests to override specific mocks
    return DeviceTemplateClonerDeps(**fields)  # Build immutable deps bundle


def _build_manager(*, org_id: str = "org-uuid-1", **overrides: Any) -> DeviceConfigTemplateClonerManager:
    """Construct a cloner with mocked dependencies for direct helper testing."""
    return DeviceConfigTemplateClonerManager(org_id=org_id, deps=_build_deps(**overrides))


# ---------------------------------------------------------------------------
# _list_sites and _select_site
# ---------------------------------------------------------------------------


def test_list_sites_extracts_data_from_response() -> None:
    """_list_sites must extract .data from the mistapi response object."""
    manager = _build_manager()  # Build cloner with default mocks
    fake_response = SimpleNamespace(data=[{"id": "site-1", "name": "Site A"}])  # API response stub
    with patch(  # Patch listOrgSites at module import path used by SUT
        "src.gateway.device_template_cloner.mistapi.api.v1.orgs.sites.listOrgSites",
        return_value=fake_response,
    ) as mocked_call:
        sites = manager._list_sites()  # Invoke helper under test
    assert sites == [{"id": "site-1", "name": "Site A"}]  # Must return the .data list verbatim
    mocked_call.assert_called_once_with(manager.apisession, "org-uuid-1")  # Args must match session+org


def test_list_sites_returns_empty_when_response_missing_data_attr() -> None:
    """_list_sites must return [] when the response object lacks a .data attribute."""
    manager = _build_manager()  # Build cloner with default mocks
    fake_response = object()  # Bare object with no .data attribute triggers empty branch
    with patch(  # Patch listOrgSites to return the attr-less response
        "src.gateway.device_template_cloner.mistapi.api.v1.orgs.sites.listOrgSites",
        return_value=fake_response,
    ):
        sites = manager._list_sites()  # Invoke helper under test
    assert sites == []  # Must fall back to empty list when .data missing


def test_select_site_returns_none_when_no_sites(capsys: pytest.CaptureFixture) -> None:
    """_select_site must return None and inform the engineer when no sites exist."""
    manager = _build_manager()  # Build cloner with default mocks
    with patch.object(manager, "_list_sites", return_value=[]):  # Force empty site list
        result = manager._select_site()  # Invoke helper under test
    assert result is None  # Must signal abort with None
    assert "No sites found" in capsys.readouterr().out  # Must inform engineer via stdout


def test_select_site_returns_chosen_site_on_valid_input() -> None:
    """_select_site must return items[choice-1] when the engineer picks a valid number."""
    input_fn = MagicMock(return_value="2")  # Engineer picks second site
    manager = _build_manager(input_fn=input_fn)  # Inject controlled input mock
    sites = [{"id": "site-1", "name": "A"}, {"id": "site-2", "name": "B"}]  # Two-site fixture
    with patch.object(manager, "_list_sites", return_value=sites):  # Force known site list
        result = manager._select_site()  # Invoke helper under test
    assert result == {"id": "site-2", "name": "B"}  # Must return the second site (1-based)


# ---------------------------------------------------------------------------
# _list_gateways and _select_gateway
# ---------------------------------------------------------------------------


def test_list_gateways_filters_only_gateway_type() -> None:
    """_list_gateways must filter the API device list to type==gateway only."""
    manager = _build_manager()  # Build cloner with default mocks
    mixed_devices = [  # API returns mixed device types - only gateway must survive filter
        {"id": "ap-1", "type": "ap"},
        {"id": "gw-1", "type": "gateway", "model": "SRX340"},
        {"id": "sw-1", "type": "switch"},
        {"id": "gw-2", "type": "gateway", "model": "SSR120"},
    ]
    fake_response = SimpleNamespace(data=mixed_devices)  # API response stub
    with patch(  # Patch listSiteDevices at module import path
        "src.gateway.device_template_cloner.mistapi.api.v1.sites.devices.listSiteDevices",
        return_value=fake_response,
    ) as mocked_call:
        gateways = manager._list_gateways("site-1")  # Invoke helper under test
    assert [g["id"] for g in gateways] == ["gw-1", "gw-2"]  # Only gateway-type devices remain
    mocked_call.assert_called_once_with(manager.apisession, "site-1", type="all")  # Must pass type=all


def test_list_gateways_returns_empty_when_response_missing_data_attr() -> None:
    """_list_gateways must return [] when the response object lacks a .data attribute."""
    manager = _build_manager()  # Build cloner with default mocks
    with patch(  # Patch listSiteDevices to return attr-less response
        "src.gateway.device_template_cloner.mistapi.api.v1.sites.devices.listSiteDevices",
        return_value=object(),
    ):
        gateways = manager._list_gateways("site-1")  # Invoke helper under test
    assert gateways == []  # Must fall back to empty list when .data missing


def test_select_gateway_returns_none_when_empty(capsys: pytest.CaptureFixture) -> None:
    """_select_gateway must return None and inform engineer when no gateways found."""
    manager = _build_manager()  # Build cloner with default mocks
    result = manager._select_gateway([])  # Empty gateway list triggers early return
    assert result is None  # Must signal abort with None
    assert "No gateway devices found" in capsys.readouterr().out  # Must inform engineer via stdout


def test_select_gateway_returns_chosen_gateway_on_valid_input() -> None:
    """_select_gateway must return items[choice-1] when the engineer picks a valid number."""
    input_fn = MagicMock(return_value="1")  # Engineer picks first gateway
    manager = _build_manager(input_fn=input_fn)  # Inject controlled input mock
    gateways = [  # Two-gateway fixture with mixed metadata for display path coverage
        {"id": "gw-1", "name": "branch-gw-1", "model": "SRX340"},
        {"id": "gw-2", "mac": "aabbccddeeff", "model": "SSR120"},  # No name - MAC fallback path
    ]
    result = manager._select_gateway(gateways)  # Invoke helper under test
    assert result is not None  # Non-empty gateway list must yield a selection (mypy narrowing)
    assert result["id"] == "gw-1"  # Must return the first gateway (1-based to 0-based conversion)


def test_select_gateway_uses_mac_fallback_when_name_missing(capsys: pytest.CaptureFixture) -> None:
    """_select_gateway must display MAC address as fallback when device has no name."""
    input_fn = MagicMock(return_value="1")  # Any valid input to reach display line
    manager = _build_manager(input_fn=input_fn)  # Inject controlled input mock
    gateways = [{"id": "gw-1", "mac": "aabbccddeeff", "model": "SSR120"}]  # No name field
    manager._select_gateway(gateways)  # Invoke helper - triggers display line
    output = capsys.readouterr().out  # Capture stdout for assertion
    assert "aabbccddeeff" in output  # MAC must appear in display as name fallback


# ---------------------------------------------------------------------------
# _resolve_menu_choice
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(  # Cover every failure path of the shared menu resolver
    "raw_input,items,expected",
    [
        ("abc", [{"a": 1}], None),  # Non-numeric input returns None
        ("0", [{"a": 1}], None),  # Below range (choice < 1) returns None
        ("2", [{"a": 1}], None),  # Above range (choice > len) returns None
        ("", [{"a": 1}], None),  # Empty string is non-numeric - returns None
    ],
)
def test_resolve_menu_choice_returns_none_on_invalid_input(
    raw_input: str, items: list[dict[str, int]], expected: None
) -> None:
    """_resolve_menu_choice must return None on any invalid input variant."""
    manager = _build_manager()  # Build cloner with default mocks
    result = manager._resolve_menu_choice(raw_input, items)  # Invoke resolver under test
    assert result is expected  # Must return None sentinel for every invalid variant


def test_resolve_menu_choice_returns_selected_item_on_valid_input() -> None:
    """_resolve_menu_choice must return items[choice-1] on valid 1-based input."""
    manager = _build_manager()  # Build cloner with default mocks
    items = [{"id": "a"}, {"id": "b"}, {"id": "c"}]  # Three-item list for range check
    assert manager._resolve_menu_choice("3", items) == {"id": "c"}  # Last-item selection


# ---------------------------------------------------------------------------
# _fetch_device_config
# ---------------------------------------------------------------------------


def test_fetch_device_config_returns_dict_on_success() -> None:
    """_fetch_device_config must return the .data dict from getSiteDevice."""
    manager = _build_manager()  # Build cloner with default mocks
    fake_response = SimpleNamespace(data={"id": "dev-1", "name": "gw", "ntp_servers": ["1.1.1.1"]})
    with patch(  # Patch getSiteDevice at module import path
        "src.gateway.device_template_cloner.mistapi.api.v1.sites.devices.getSiteDevice",
        return_value=fake_response,
    ) as mocked_call:
        result = manager._fetch_device_config("site-1", "dev-1")  # Invoke helper under test
    assert result == {"id": "dev-1", "name": "gw", "ntp_servers": ["1.1.1.1"]}  # Full dict returned
    mocked_call.assert_called_once_with(manager.apisession, "site-1", "dev-1")  # Args match


def test_fetch_device_config_returns_none_on_empty_response() -> None:
    """_fetch_device_config must return None when the API response is empty."""
    manager = _build_manager()  # Build cloner with default mocks
    with patch(  # Patch getSiteDevice to return an empty-data response
        "src.gateway.device_template_cloner.mistapi.api.v1.sites.devices.getSiteDevice",
        return_value=SimpleNamespace(data={}),
    ):
        result = manager._fetch_device_config("site-1", "dev-1")  # Invoke helper under test
    assert result is None  # Empty dict must trigger None return for downstream abort


def test_fetch_device_config_returns_none_when_response_missing_data_attr() -> None:
    """_fetch_device_config must return None when response has no .data attribute."""
    manager = _build_manager()  # Build cloner with default mocks
    with patch(  # Patch getSiteDevice to return attr-less response
        "src.gateway.device_template_cloner.mistapi.api.v1.sites.devices.getSiteDevice",
        return_value=object(),
    ):
        result = manager._fetch_device_config("site-1", "dev-1")  # Invoke helper under test
    assert result is None  # Missing .data must trigger None return


# ---------------------------------------------------------------------------
# _fetch_existing_template_names
# ---------------------------------------------------------------------------


def test_fetch_existing_template_names_returns_name_set() -> None:
    """_fetch_existing_template_names must return the set of non-empty template names."""
    manager = _build_manager()  # Build cloner with default mocks
    templates = [  # Fixture includes empty and missing names to exercise filter
        {"id": "t-1", "name": "template-a"},
        {"id": "t-2", "name": ""},  # Empty name must be filtered out
        {"id": "t-3", "name": "template-b"},
        {"id": "t-4"},  # Missing name must be filtered out via .get() default
    ]
    with patch(  # Patch listOrgGatewayTemplates at module import path
        "src.gateway.device_template_cloner.mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates",
        return_value=SimpleNamespace(data=templates),
    ):
        names = manager._fetch_existing_template_names()  # Invoke helper under test
    assert names == {"template-a", "template-b"}  # Empty and missing names filtered out


def test_fetch_existing_template_names_returns_empty_when_response_missing_data_attr() -> None:
    """_fetch_existing_template_names must return empty set when response has no .data."""
    manager = _build_manager()  # Build cloner with default mocks
    with patch(  # Patch listOrgGatewayTemplates to return attr-less response
        "src.gateway.device_template_cloner.mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates",
        return_value=object(),
    ):
        names = manager._fetch_existing_template_names()  # Invoke helper under test
    assert names == set()  # Must fall back to empty set when .data missing


# ---------------------------------------------------------------------------
# _prompt_template_type
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(  # Cover both branches of the type-selection map
    "raw,expected",
    [
        ("2", "spoke"),  # Option 2 explicitly picks spoke
        ("1", "standalone"),  # Option 1 (or anything else) is standalone
        ("", "standalone"),  # Empty defaults to standalone
        ("abc", "standalone"),  # Non-matching returns standalone default
    ],
)
def test_prompt_template_type_maps_input_to_api_string(raw: str, expected: str) -> None:
    """_prompt_template_type must map '2' to spoke and anything else to standalone."""
    input_fn = MagicMock(return_value=raw)  # Return the test raw value
    manager = _build_manager(input_fn=input_fn)  # Inject controlled input mock
    assert manager._prompt_template_type() == expected  # Verify mapping


# ---------------------------------------------------------------------------
# _prompt_template_name
# ---------------------------------------------------------------------------


def test_prompt_template_name_returns_default_when_input_empty() -> None:
    """_prompt_template_name must return default when engineer just presses Enter."""
    input_fn = MagicMock(return_value="")  # Empty response - use default
    manager = _build_manager(input_fn=input_fn)  # Inject controlled input mock
    result = manager._prompt_template_name("suggested-name", set())  # No existing names
    assert result == "suggested-name"  # Must return the default when input empty


def test_prompt_template_name_retries_when_name_already_exists(capsys: pytest.CaptureFixture) -> None:
    """_prompt_template_name must loop when engineer provides a name already in use."""
    input_fn = MagicMock(side_effect=["taken-name", "new-name"])  # First attempt taken, second unique
    manager = _build_manager(input_fn=input_fn)  # Inject controlled input mock
    result = manager._prompt_template_name("default", {"taken-name"})  # Existing set
    assert result == "new-name"  # Must return the second (unique) name
    assert "already exists" in capsys.readouterr().out  # Guidance message must appear


def test_prompt_template_name_retries_when_empty_after_default_empty(
    capsys: pytest.CaptureFixture,
) -> None:
    """_prompt_template_name must loop when both input and default resolve to empty."""
    input_fn = MagicMock(side_effect=["", "final-name"])  # Empty then valid on retry
    manager = _build_manager(input_fn=input_fn)  # Inject controlled input mock
    result = manager._prompt_template_name("", set())  # Empty default - forces retry loop
    assert result == "final-name"  # Second attempt must be accepted
    assert "cannot be empty" in capsys.readouterr().out  # Empty guard message must appear


# ---------------------------------------------------------------------------
# _prompt_hardware_platform and _resolve_hardware_choice
# ---------------------------------------------------------------------------


def test_prompt_hardware_platform_keeps_source_model_on_zero_input() -> None:
    """_prompt_hardware_platform must return source model when engineer types 0."""
    input_fn = MagicMock(return_value="0")  # Explicit keep-source option
    manager = _build_manager(input_fn=input_fn)  # Inject controlled input mock
    assert manager._prompt_hardware_platform("SRX340") == "SRX340"  # Source preserved


def test_prompt_hardware_platform_returns_selected_model_on_valid_index() -> None:
    """_prompt_hardware_platform must return COMMON_GATEWAY_MODELS[choice-1] on valid pick."""
    input_fn = MagicMock(return_value="3")  # Third option in the constant list
    manager = _build_manager(input_fn=input_fn)  # Inject controlled input mock
    assert manager._prompt_hardware_platform("SRX300") == COMMON_GATEWAY_MODELS[2]  # 3->index 2


@pytest.mark.parametrize(  # Cover every branch of the hardware resolver
    "raw,expected_kind",
    [
        ("0", "source"),  # Explicit keep-source sentinel
        ("", "source"),  # Empty input treated as keep-source
        ("abc", "source"),  # Non-numeric falls back to source model
        ("99", "source"),  # Out-of-range falls back to source model
        ("1", "list"),  # Valid in-range returns COMMON_GATEWAY_MODELS[0]
        ("10", "list"),  # Last valid index returns COMMON_GATEWAY_MODELS[9]
    ],
)
def test_resolve_hardware_choice_all_branches(raw: str, expected_kind: str) -> None:
    """_resolve_hardware_choice must handle every input variant with safe defaults."""
    manager = _build_manager()  # Build cloner with default mocks
    result = manager._resolve_hardware_choice(raw, "SRX-SOURCE")  # Invoke resolver under test
    if expected_kind == "source":  # Verify source model preserved on sentinel/error paths
        assert result == "SRX-SOURCE"
    else:  # Verify concrete model returned on valid picks
        assert result in COMMON_GATEWAY_MODELS


def test_resolve_hardware_choice_prints_message_on_invalid_input(
    capsys: pytest.CaptureFixture,
) -> None:
    """_resolve_hardware_choice must inform engineer when falling back on invalid input."""
    manager = _build_manager()  # Build cloner with default mocks
    manager._resolve_hardware_choice("invalid", "SRX340")  # Non-numeric fallback path
    assert "Invalid selection" in capsys.readouterr().out  # Fallback message must appear


def test_resolve_hardware_choice_prints_message_on_out_of_range(
    capsys: pytest.CaptureFixture,
) -> None:
    """_resolve_hardware_choice must inform engineer when falling back on out-of-range."""
    manager = _build_manager()  # Build cloner with default mocks
    manager._resolve_hardware_choice("999", "SRX340")  # Out-of-range fallback path
    assert "Invalid selection" in capsys.readouterr().out  # Fallback message must appear


# ---------------------------------------------------------------------------
# _create_template
# ---------------------------------------------------------------------------


def test_create_template_returns_new_template_dict() -> None:
    """_create_template must return .data dict from createOrgGatewayTemplate."""
    manager = _build_manager()  # Build cloner with default mocks
    fake_response = SimpleNamespace(data={"id": "tmpl-1", "name": "new-tmpl", "type": "standalone"})
    payload = {"name": "new-tmpl", "type": "standalone", "gateway_matching": {"enable": True}}
    with patch(  # Patch createOrgGatewayTemplate at module import path
        "src.gateway.device_template_cloner.mistapi.api.v1.orgs.gatewaytemplates.createOrgGatewayTemplate",
        return_value=fake_response,
    ) as mocked_call:
        result = manager._create_template(payload)  # Invoke helper under test
    assert result == {"id": "tmpl-1", "name": "new-tmpl", "type": "standalone"}  # Data returned
    mocked_call.assert_called_once_with(manager.apisession, "org-uuid-1", body=payload)  # Args match


def test_create_template_returns_none_on_empty_response() -> None:
    """_create_template must return None when the API response .data is empty."""
    manager = _build_manager()  # Build cloner with default mocks
    with patch(  # Patch createOrgGatewayTemplate to return empty .data
        "src.gateway.device_template_cloner.mistapi.api.v1.orgs.gatewaytemplates.createOrgGatewayTemplate",
        return_value=SimpleNamespace(data={}),
    ):
        result = manager._create_template({"name": "n", "type": "standalone"})  # Invoke helper
    assert result is None  # Empty .data must trigger None return


def test_create_template_returns_none_when_response_missing_data_attr() -> None:
    """_create_template must return None when response object lacks a .data attribute."""
    manager = _build_manager()  # Build cloner with default mocks
    with patch(  # Patch createOrgGatewayTemplate to return attr-less object
        "src.gateway.device_template_cloner.mistapi.api.v1.orgs.gatewaytemplates.createOrgGatewayTemplate",
        return_value=object(),
    ):
        result = manager._create_template({"name": "n"})  # Invoke helper under test
    assert result is None  # Missing .data must trigger None return


# ---------------------------------------------------------------------------
# clone() exception path and abort branches
# ---------------------------------------------------------------------------


def test_clone_returns_false_on_unexpected_exception(capsys: pytest.CaptureFixture) -> None:
    """clone() must catch unexpected errors, log them, and return False."""
    manager = _build_manager()  # Build cloner with default mocks
    with patch.object(  # Force _gather_source_device to raise unexpected error
        manager, "_gather_source_device", side_effect=RuntimeError("boom")
    ):
        result = manager.clone()  # Invoke workflow under test
    assert result is False  # Must return False on any exception
    assert "Error" in capsys.readouterr().out  # Must print user-friendly error message


def test_clone_returns_false_when_create_template_returns_none(
    capsys: pytest.CaptureFixture,
) -> None:
    """clone() must return False and inform engineer when _create_template returns None."""
    manager = _build_manager()  # Build cloner with default mocks
    gateway = {"id": "gw-1", "model": "SRX340"}  # Selected source gateway
    export_mock = MagicMock()  # Captured out here so mypy sees a MagicMock rather than a bound method
    with patch.multiple(  # Stub every phase up to the create-template call
        manager,
        _select_site=MagicMock(return_value={"id": "site-1"}),
        _list_gateways=MagicMock(return_value=[gateway]),
        _select_gateway=MagicMock(return_value=gateway),
        _fetch_device_config=MagicMock(return_value={"id": "dev-1"}),
        _fetch_existing_template_names=MagicMock(return_value=set()),
        _prompt_template_meta=MagicMock(return_value=("name", "standalone", "SRX340")),
        _confirm_creation=MagicMock(return_value=True),  # User confirms creation
        _create_template=MagicMock(return_value=None),  # API returns empty - triggers failure branch
        _export_result=export_mock,  # Must NOT be called when creation fails
    ):
        result = manager.clone()  # Invoke workflow under test
        assert result is False  # Must return False when template creation fails
        assert "Template creation failed" in capsys.readouterr().out  # Failure message must appear
        export_mock.assert_not_called()  # Export must not fire (assertion inside `with`)


def test_clone_returns_false_when_device_config_missing(capsys: pytest.CaptureFixture) -> None:
    """clone() must return False and inform engineer when device config fetch returns None."""
    manager = _build_manager()  # Build cloner with default mocks
    with patch.multiple(  # Stub phases through device config fetch
        manager,
        _select_site=MagicMock(return_value={"id": "site-1"}),
        _list_gateways=MagicMock(return_value=[{"id": "gw-1", "model": "SRX340"}]),
        _select_gateway=MagicMock(return_value={"id": "gw-1", "model": "SRX340"}),
        _fetch_device_config=MagicMock(return_value=None),  # Config fetch fails
    ):
        result = manager.clone()  # Invoke workflow under test
    assert result is False  # Must return False when config missing
    assert "Failed to fetch device configuration" in capsys.readouterr().out  # Message must appear


def test_clone_returns_false_when_gateway_selection_aborted() -> None:
    """clone() must return False when _select_gateway returns None (abort path)."""
    manager = _build_manager()  # Build cloner with default mocks
    with patch.multiple(  # Stub through gateway selection abort
        manager,
        _select_site=MagicMock(return_value={"id": "site-1"}),
        _list_gateways=MagicMock(return_value=[]),  # Empty list forces None from selector
        _select_gateway=MagicMock(return_value=None),  # Explicit abort return
    ):
        assert manager.clone() is False  # Must return False on gateway abort


# ---------------------------------------------------------------------------
# _prompt_template_meta orchestration
# ---------------------------------------------------------------------------


def test_prompt_template_meta_returns_tuple_of_all_three_values() -> None:
    """_prompt_template_meta must chain the three sub-prompts and return their tuple."""
    manager = _build_manager()  # Build cloner with default mocks
    with patch.multiple(  # Stub each sub-prompt with a known return value
        manager,
        _prompt_template_type=MagicMock(return_value="spoke"),
        _prompt_template_name=MagicMock(return_value="my-name"),
        _prompt_hardware_platform=MagicMock(return_value="SRX345"),
    ):
        name, ttype, model = manager._prompt_template_meta("SRX300", set())  # Invoke orchestrator
    assert (name, ttype, model) == ("my-name", "spoke", "SRX345")  # All three chained correctly
