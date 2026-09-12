"""Unit tests for DeviceConfigTemplateClonerManager (menu 194).

Covers the dependency-injection contract and the CSV-export call signature
that recently regressed in production (TypeError on api_function_name kwarg).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.gateway.device_template_cloner import (
    DEVICE_METADATA_FIELDS_TO_STRIP,
    SECRET_FIELD_NAMES,
    DeviceConfigTemplateClonerManager,
    DeviceTemplateClonerDeps,
)


def _build_deps(**overrides) -> DeviceTemplateClonerDeps:
    """Construct a deps bundle for the cloner; overrides replace individual mocks."""
    fields = {  # Default mock dependency set matching the frozen deps dataclass
        "apisession": MagicMock(name="apisession"),  # Mock mistapi session
        "input_fn": MagicMock(name="input_fn", return_value=""),  # Default prompt returns empty
        "get_csv_path_fn": MagicMock(name="get_csv_path_fn", return_value="data/test.csv"),  # Path stub
        "save_data_fn": MagicMock(name="save_data_fn"),  # Legacy CSV writer stub
        "write_csv_fn": MagicMock(name="write_csv_fn"),  # PK-aware writer stub (the new contract)
    }
    fields.update(overrides)  # Allow individual tests to override specific mocks
    return DeviceTemplateClonerDeps(**fields)  # Build immutable deps bundle


def _build_manager(*, org_id: str = "org-uuid-1", **overrides) -> DeviceConfigTemplateClonerManager:
    """Construct a cloner with mocked dependencies; overrides target the deps fields."""
    return DeviceConfigTemplateClonerManager(org_id=org_id, deps=_build_deps(**overrides))


def test_constructor_accepts_write_csv_fn_dependency() -> None:
    """Cloner constructor must accept write_csv_fn (not check_and_generate_csv_fn)."""
    manager = _build_manager()  # Build cloner with default mocks
    assert callable(manager.write_csv_fn)  # Stored attribute must be the injected callable
    assert manager.org_id == "org-uuid-1"  # Org ID must be stored verbatim


def test_export_result_calls_write_csv_with_correct_signature() -> None:
    """Regression test: _export_result must call write_csv_fn(rows, filename, api_function_name=...).

    Production crashed with `TypeError: got an unexpected keyword argument
    'api_function_name'` because the wrong helper was injected. This test locks
    the correct call signature so the bug cannot regress silently.
    """
    write_csv = MagicMock(name="write_csv_fn")  # Track all calls to the PK-aware writer
    manager = _build_manager(write_csv_fn=write_csv)  # Inject the tracking mock via deps
    gateway = {  # Source device metadata used to populate the export row
        "id": "dev-1",
        "name": "branch-gw-1",
        "model": "SRX340",
        "site_id": "site-1",
    }
    new_template = {  # New template returned by the create API call
        "id": "tmpl-1",
        "name": "branch-gw-1-tmpl",
        "type": "standalone",
    }

    manager._export_result(gateway, new_template)  # Trigger the export step under test

    write_csv.assert_called_once()  # Writer must be invoked exactly once per export
    args, kwargs = write_csv.call_args  # Capture positional and keyword arguments
    assert args[0] == [  # First positional arg must be a list containing a single row dict
        {
            "org_id": "org-uuid-1",
            "template_id": "tmpl-1",
            "template_name": "branch-gw-1-tmpl",
            "template_type": "standalone",
            "source_device_id": "dev-1",
            "source_device_name": "branch-gw-1",
            "source_device_model": "SRX340",
            "source_site_id": "site-1",
        }
    ]
    assert args[1] == "CloneGatewayTemplate.csv"  # Second positional must be the output filename
    assert kwargs == {"api_function_name": "createOrgGatewayTemplate"}  # PK strategy key required


def test_build_template_payload_strips_device_metadata_and_injects_template_fields() -> None:
    """Payload builder removes device-instance metadata and adds template/match fields."""
    manager = _build_manager()  # Build cloner with default mocks
    device_config = {  # Synthetic device config including stripped + preserved fields
        "id": "dev-1",  # Should be stripped (device metadata)
        "mac": "aa:bb:cc:dd:ee:ff",  # Should be stripped (device metadata)
        "site_id": "site-1",  # Should be stripped (device metadata)
        "serial": "ABC123",  # Should be stripped (device metadata)
        "ntp_servers": ["10.0.0.1"],  # Should be preserved (template-relevant config)
    }
    for stripped_field in DEVICE_METADATA_FIELDS_TO_STRIP:  # Sanity-check the constant covers our fixtures
        if stripped_field in device_config:
            assert device_config[stripped_field] is not None  # Fixture values are non-null

    payload = manager._build_template_payload(device_config, "tmpl-X", "standalone", "SRX340")

    reinjected = {"name", "type"}  # These fields are stripped then reinjected with template values
    for stripped_field in DEVICE_METADATA_FIELDS_TO_STRIP - reinjected:  # Pure-strip fields only
        assert stripped_field not in payload, f"{stripped_field} should have been stripped"
    assert payload["name"] == "tmpl-X"  # Template name must be injected verbatim
    assert payload["type"] == "standalone"  # Template type must be injected verbatim
    assert payload["gateway_matching"]["enable"] is True  # Hardware matching block must be enabled
    assert payload["gateway_matching"]["rules"][0]["match_model"] == "SRX340"  # Model targeting wired
    assert payload["ntp_servers"] == ["10.0.0.1"]  # Non-metadata fields must be preserved


def test_redact_secrets_replaces_sensitive_values_with_placeholder() -> None:
    """Secret redactor must walk nested dicts and replace all SECRET_FIELD_NAMES values."""
    manager = _build_manager()  # Build cloner with default mocks
    sample_secret_field = next(iter(SECRET_FIELD_NAMES))  # Pick any secret name from the constant
    payload = {  # Nested structure with a secret at top level and inside a list
        sample_secret_field: "super-secret-value",
        "nested": {sample_secret_field: "another-secret"},
        "list_of_dicts": [{sample_secret_field: "third-secret"}],
        "non_secret": "keep-me",
    }

    redacted = manager._redact_secrets_from_payload(payload)

    assert redacted[sample_secret_field] == "REDACTED"  # Top-level secret must be redacted
    assert redacted["nested"][sample_secret_field] == "REDACTED"  # Nested-dict secret must be redacted
    assert redacted["list_of_dicts"][0][sample_secret_field] == "REDACTED"  # List-of-dicts secret redacted
    assert redacted["non_secret"] == "keep-me"  # Non-secret values must be preserved verbatim
    assert payload[sample_secret_field] == "super-secret-value"  # Original payload must NOT be mutated


def test_confirm_creation_requires_exact_create_keyword() -> None:
    """Confirmation gate must reject anything other than the exact string 'CREATE'."""
    for entered, expected in [("CREATE", True), ("create", False), ("yes", False), ("", False)]:
        input_fn = MagicMock(return_value=entered)  # Mock input returns the test value
        manager = _build_manager(input_fn=input_fn)  # Build cloner with the test input mock
        assert manager._confirm_creation("name", "standalone", "SRX340") is expected


def test_clone_returns_false_when_site_selection_aborted() -> None:
    """Clone workflow must return False (not raise) when site selection returns None."""
    manager = _build_manager()  # Build cloner with default mocks
    with patch.object(manager, "_select_site", return_value=None):  # Force site selection to abort
        assert manager.clone() is False  # Workflow must return False on early abort


def test_clone_returns_false_when_confirmation_declined() -> None:
    """Clone workflow must return False without calling create API if user declines confirmation."""
    manager = _build_manager()  # Build cloner with default mocks
    with patch.multiple(  # Stub every workflow step up to the confirmation gate
        manager,
        _select_site=MagicMock(return_value={"id": "site-1"}),
        _list_gateways=MagicMock(return_value=[{"id": "dev-1", "model": "SRX340"}]),
        _select_gateway=MagicMock(return_value={"id": "dev-1", "model": "SRX340"}),
        _fetch_device_config=MagicMock(return_value={"id": "dev-1"}),
        _fetch_existing_template_names=MagicMock(return_value=set()),
        _prompt_template_meta=MagicMock(return_value=("name", "standalone", "SRX340")),
        _confirm_creation=MagicMock(return_value=False),  # User declines the operation
        _create_template=MagicMock(),  # Must NOT be called when confirmation declined
        _export_result=MagicMock(),  # Must NOT be called when confirmation declined
    ):
        assert manager.clone() is False  # Workflow must return False
        manager._create_template.assert_not_called()  # No API write must occur
        manager._export_result.assert_not_called()  # No CSV export must occur


def test_clone_happy_path_calls_export_with_new_template() -> None:
    """Full happy-path clone workflow must end with _export_result being called once."""
    manager = _build_manager()  # Build cloner with default mocks
    new_template = {"id": "tmpl-1", "name": "name", "type": "standalone"}  # Fake API response
    gateway = {"id": "dev-1", "model": "SRX340"}  # Selected source device
    with patch.multiple(  # Stub the entire workflow chain through successful completion
        manager,
        _select_site=MagicMock(return_value={"id": "site-1"}),
        _list_gateways=MagicMock(return_value=[gateway]),
        _select_gateway=MagicMock(return_value=gateway),
        _fetch_device_config=MagicMock(return_value={"id": "dev-1", "ntp_servers": []}),
        _fetch_existing_template_names=MagicMock(return_value=set()),
        _prompt_template_meta=MagicMock(return_value=("name", "standalone", "SRX340")),
        _confirm_creation=MagicMock(return_value=True),  # User confirms
        _create_template=MagicMock(return_value=new_template),  # API returns new template
        _export_result=MagicMock(),  # Track export invocation
    ):
        assert manager.clone() is True  # Workflow must return True on success
        manager._export_result.assert_called_once_with(gateway, new_template)  # Export wired correctly


@pytest.mark.parametrize(  # Verify every deps dataclass field is required for construction
    "missing_field",
    ["apisession", "input_fn", "get_csv_path_fn", "save_data_fn", "write_csv_fn"],
)
def test_deps_dataclass_requires_all_fields(missing_field: str) -> None:
    """DeviceTemplateClonerDeps must reject construction if any injected field is missing."""
    fields = {  # Complete field set used as the baseline for the deps dataclass
        "apisession": MagicMock(),
        "input_fn": MagicMock(),
        "get_csv_path_fn": MagicMock(),
        "save_data_fn": MagicMock(),
        "write_csv_fn": MagicMock(),
    }
    fields.pop(missing_field)  # Remove one field to verify it is required
    with pytest.raises(TypeError):  # Dataclass must reject incomplete construction
        DeviceTemplateClonerDeps(**fields)


def test_manager_requires_org_id_and_deps() -> None:
    """Manager constructor must require both positional/keyword arguments explicitly."""
    with pytest.raises(TypeError):  # Missing deps must be rejected
        DeviceConfigTemplateClonerManager(org_id="org-1")  # type: ignore[call-arg]
    with pytest.raises(TypeError):  # Missing org_id must be rejected
        DeviceConfigTemplateClonerManager(deps=_build_deps())  # type: ignore[call-arg]
