"""Wave 1 safe-input regression tests for touched production prompt paths."""

from unittest.mock import MagicMock

import MistHelper
from src.refactors.is_debug_mode import IsDebugMode  # WHY: replaces removed MistHelper.is_debug_mode per 1012 SC-002


def test_ssh_runner_confirm_execution_returns_false_on_eof(monkeypatch):
    def raise_eof(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    # Facade wrapper removed; call extracted impl directly with built deps.
    deps = MistHelper.SSHRunnerManager._build_deps()
    assert MistHelper.ExtractedSSHRunnerManager._confirm_execution(deps, 3) is False


def test_wan2_confirm_operation_handles_eof_as_cancel(monkeypatch):
    # Wire canonical WAN2MigrationManager with MistHelper runtime globals (delegator shim removed)
    from src.gateway import wan2_migration_manager as wan2_module  # Import canonical module

    wan2_module.configure_wan2_migration_dependencies(  # Publish MistHelper-owned deps into canonical module
        wan2_module.WAN2MigrationDependencies(  # Frozen bundle mirrors production wiring
            apisession=getattr(MistHelper, "apisession", None),  # Current apisession (may be None in tests)
            config_utils=MistHelper.ConfigUtils,  # Config helper facade
            cache_utils=MistHelper.CacheUtils,  # Cache generation facade
            org_site_exporter=MistHelper.OrgSiteExporter,  # Site exporter facade
            gateway_export_utils=MistHelper.GatewayExportUtils,  # Gateway exporter facade
            file_path_utils=MistHelper.FilePathUtils,  # Path resolver facade
            input_utils=MistHelper.InputUtils,  # Safe input facade
            data_exporter=MistHelper.DataExporter,  # Report writer facade
            mistapi=MistHelper.mistapi,  # mistapi library reference
            site_exclude_prefix=MistHelper.MIST_SITE_EXCLUDE_PREFIX,  # Exclusion prefix
        )
    )
    # Patch org_id lookup before construction so __init__ does not hit the real API
    monkeypatch.setattr(MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org-test")
    manager = wan2_module.WAN2MigrationManager()  # Construct canonical manager directly

    def raise_eof(_prompt):  # Simulate SSH/container EOF on confirmation prompt
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)  # Patch input() after construction
    assert manager._confirm_site_variable_operation(2) is False  # Must cancel cleanly on EOF


def test_troubleshoot_launch_interactive_uses_safe_prompt_and_dispatch(monkeypatch):
    monkeypatch.setattr(MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org-1")
    monkeypatch.setattr(MistHelper.TroubleshootUtils, "client_connectivity", MagicMock())
    monkeypatch.setattr(MistHelper.TroubleshootUtils, "device_performance", MagicMock())
    monkeypatch.setattr(MistHelper.TroubleshootUtils, "network_connectivity", MagicMock())
    monkeypatch.setattr(MistHelper.TroubleshootUtils, "view_insights", MagicMock())

    monkeypatch.setattr(MistHelper.InputUtils, "safe_input", lambda *args, **kwargs: "5")

    MistHelper.TroubleshootUtils.launch_interactive()

    assert MistHelper.TroubleshootUtils.client_connectivity.call_count == 0
    assert MistHelper.TroubleshootUtils.device_performance.call_count == 0
    assert MistHelper.TroubleshootUtils.network_connectivity.call_count == 0
    assert MistHelper.TroubleshootUtils.view_insights.call_count == 0


def test_determine_search_scope_uses_safe_input_for_site_mode(monkeypatch):
    monkeypatch.setattr(MistHelper.InputUtils, "safe_input", lambda *args, **kwargs: "s")
    monkeypatch.setattr(MistHelper.PromptUtils, "select_site", lambda: "site-123")

    result = MistHelper.PromptUtils._determine_search_scope(None)
    assert result == "site-123"


def test_handle_client_selection_returns_none_tuple_on_eof(monkeypatch):
    clients = [{"mac": "aa:bb:cc:dd:ee:ff", "client_type": "wired", "site_id": "site-1"}]
    sites_cache = {"site-1": "Example Site"}

    def raise_eof(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)

    result = MistHelper.PromptUtils._handle_client_selection(clients, sites_cache, "site-1")
    assert result == (None, None, None)


def test_service_ping_parameter_prompts_fall_back_to_defaults_on_eof(monkeypatch):
    # Wire canonical ServicePingManager with MistHelper runtime globals (delegator shim removed)
    from src.websocket.service_ping_manager import (
        ServicePingManager,
        configure_service_ping_manager_dependencies,
    )

    configure_service_ping_manager_dependencies(
        apisession_dependency=getattr(MistHelper, "apisession", None),
        mistapi_dependency=MistHelper.mistapi,
        prompt_utils=MistHelper.PromptUtils,
        input_utils=MistHelper.InputUtils,
        websocket_manager_class=MistHelper.WebSocketManager,
        is_debug_mode=IsDebugMode.check,  # WHY: rewired to IsDebugMode.check per 1012 SC-002 (module-level is_debug_mode() removed)
        api_tenant_fetch_utils=MistHelper.APITenantFetchUtils,
        config_utils=MistHelper.ConfigUtils,
        api_fetch_utils=MistHelper.APIFetchUtils,
    )
    manager = ServicePingManager()

    def raise_eof(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)

    params = manager._prompt_for_ping_parameters()
    assert params["host"] == manager.DEFAULT_HOST
    assert params["count"] == manager.DEFAULT_COUNT
    assert params["size"] == manager.DEFAULT_SIZE
    assert params["node"] is None
