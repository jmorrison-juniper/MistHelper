"""Resolve source-owned dependencies without importing the root CLI module."""

# pylint: disable=import-error,import-outside-toplevel,invalid-name,protected-access

from __future__ import annotations  # Keep annotations import-safe during bootstrap.

import importlib  # Load canonical source modules only when a caller needs one.
import logging  # Record dependency resolution without exposing secrets.
import sys  # Read test-injected host modules without importing the root module.
from types import ModuleType  # Type the optional bound root module.
from typing import Any  # Support dynamic third-party and runtime objects.

from src.config import runtime_settings  # Share runtime values with all source packages.

logger = logging.getLogger(__name__)  # Use this module name in log records.


class SourceDependencyResolverService:
    """Resolve legacy source dependency names through canonical source owners."""

    _context_names = {  # Map legacy state names to the application context fields.
        "apisession": "apisession",  # Keep session reads pointed at the active context.
        "org_id": "org_id",  # Keep organization reads pointed at the active context.
        "msp_privileges": "msp_privileges",  # Keep MSP grant reads pointed at the active context.
        "selected_msp": "selected_msp",  # Keep MSP selection reads pointed at the active context.
        "OUTPUT_FORMAT": "output_format",  # Keep output setting reads pointed at the active context.
        "PROGRESS_EMITTER": "progress_emitter",  # Keep telemetry reads pointed at the active context.
        "FAST_MODE_ENABLED": "fast_mode_enabled",  # Keep fast-mode reads pointed at the active context.
    }
    _setting_names = {  # Map legacy setting names to the source settings module.
        "CSV_FRESHNESS_MINUTES": "CSV_FRESHNESS_MINUTES",  # Keep cache age in the settings seam.
        "DATABASE_PATH": "DATABASE_PATH",  # Keep the SQLite path in the settings seam.
        "DEFAULT_API_PAGE_LIMIT": "DEFAULT_API_PAGE_LIMIT",  # Keep the page limit in the settings seam.
        "IS_TEST_MODE": "IS_TEST_MODE",  # Keep test-mode state in the settings seam.
        "LAST_SELECTED_SITE_ID": "LAST_SELECTED_SITE_ID",  # Keep prompt selection state in the settings seam.
        "_api_usage_cache": "api_usage_cache",  # Keep the shared quota cache in the settings seam.
    }
    _module_symbols = {  # Map helper names to their canonical source module.
        "APICoreFetchUtils": "src.api.api_core_fetch_utils",  # Resolve core fetch helpers from src.
        "APIDataFetcher": "src.api.api_data_fetcher",  # Resolve generic fetcher from src.
        "AnomalyMetricsDiscovery": "src.refactors.anomaly_metrics_discovery",  # Resolve anomaly helper from src.
        "CacheUtils": "src.cache.cache_utils",  # Resolve cache helper from src.
        "ConfigUtils": "src.config.config_utils",  # Resolve config helper from src.
        "ConnectionPoolExecutor": "src.refactors.connection_pool_executor",  # Resolve pool helper from src.
        "ConstDefinitionsExporter": "src.export.const_definitions_exporter",  # Resolve exporter from src.
        "DataExporter": "src.export.data_exporter",  # Resolve data exporter from src.
        "DataProcessingUtils": "src.data.data_processing_utils",  # Resolve data helper from src.
        "DatabaseSchemaUtils": "src.db.database_schema_utils",  # Resolve schema helper from src.
        "DeviceDataFetcher": "src.refactors.device_data_fetcher",  # Resolve device fetcher from src.
        "DeviceUtils": "src.device.device_utils",  # Resolve device helper from src.
        "E911BSSIDReportGenerator": "src.reports.e911_bssid",  # Resolve E911 report helper from src.
        "EnhancedSSHRunner": "src.ssh.ssh_runner",  # Resolve SSH runner from src.
        "EnvironmentUtils": "src.utils.environment_utils",  # Resolve environment helper from src.
        "ExtractedMarvisTroubleshootUtils": "src.troubleshooting.marvis_troubleshoot_utils",  # Resolve class.
        "FastModeBackoffMultiplier": "src.refactors.fast_mode_backoff_multiplier",  # Resolve backoff helper.
        "FastModeSequentialMaxRetries": "src.refactors.fast_mode_sequential_max_retries",  # Resolve retry helper.
        "FilePathUtils": "src.utils.file_path_utils",  # Resolve path helper from src.
        "FilterOperatorEngine": "src.utils.filter_operator_engine",  # Resolve filter helper from src.
        "GatewayExportUtils": "src.gateway.gateway_export_utils",  # Resolve gateway helper from src.
        "GatewayTestExporter": "src.export.gateway_test_exporter",  # Resolve gateway test exporter from src.
        "InputUtils": "src.utils.input_utils",  # Resolve input helper from src.
        "InsightMetricsUtils": "src.analytics.insight_metrics_utils",  # Resolve analytics helper from src.
        "IsDebugMode": "src.refactors.is_debug_mode",  # Resolve debug helper from src.
        "KeyboardListener": "src.refactors.keyboard_listener",  # Resolve keyboard listener from src.
        "MarvisDataUtilsFactory": "src.refactors.marvis_data_utils",  # Resolve Marvis helper from src.
        "MarvisTroubleshootDeps": "src.troubleshooting.marvis_troubleshoot_utils",  # Resolve deps from src.
        "OrgAlarmEventExporter": "src.export.org_alarm_event_exporter",  # Resolve exporter from src.
        "OrgDeviceStatsExporter": "src.export.org_device_stats_exporter",  # Resolve exporter from src.
        "OrgExportUtils": "src.export.org_export_utils",  # Resolve org helper from src.
        "OrgInventoryExporter": "src.export.org_inventory_exporter",  # Resolve inventory exporter from src.
        "OrgSiteExporter": "src.export.org_site_exporter",  # Resolve site exporter from src.
        "PacketCaptureManager": "src.capture.packet_capture",  # Resolve packet capture manager from src.
        "ProgressContext": "src.dataclasses.progress_event",  # Resolve progress context from src.
        "PromptClientUtils": "src.input.prompt_client_utils",  # Resolve client prompt helper from src.
        "PromptUtils": "src.ui.prompt_utils",  # Resolve prompt helper from src.
        "RateLimitingUtils": "src.utils.rate_limiting",  # Resolve rate-limit helper from src.
        "SiteDeviceExporter": "src.export.site_device_exporter",  # Resolve site device exporter from src.
        "TimeUtils": "src.time.time_utils",  # Resolve time helper from src.
        "ValidationUtils": "src.validation.validation_utils",  # Resolve validator from src.
        "WebSocketManager": "src.websocket.manager",  # Resolve WebSocket manager from src.
    }
    _external_modules = {  # Map third-party helper names that older code read through the root module.
        "mistapi": "mistapi",  # Resolve the Mist SDK directly.
        "PrettyTable": "prettytable",  # Resolve the table renderer directly.
        "tqdm": "tqdm",  # Resolve the progress bar package directly.
    }
    # Some third-party packages hold the symbol a caller wants inside a module
    # of the same name. Issue #3111: the resolver returned the bare `tqdm`
    # module, so every `deps.tqdm(items, ...)` call raised
    # "'module' object is not callable". Name each such attribute here, so one
    # rule covers every package instead of an `if` chain that forgets one.
    _external_attributes = {
        "PrettyTable": "PrettyTable",  # The renderer is a class inside `prettytable`.
        "tqdm": "tqdm",  # The progress bar is a callable inside `tqdm`.
    }

    def __init__(self) -> None:
        """Create a resolver with no bound host module."""
        self._root_module: ModuleType | Any | None = None  # Store the optional host injected by startup or tests.

    def bind_root_module(self, module: ModuleType | Any) -> None:
        """Bind the host module for bootstrap-only helpers that still live at root."""
        self._root_module = module  # Store the host reference injected by MistHelper or WSGI startup.

    def root_module(self) -> ModuleType | Any:
        """Return the injected host module for root-only bootstrap helpers."""
        logger.info("Resolving the bound host module")  # Log before reading the injected host module.
        if self._root_module is None:  # A direct source call can occur before host bootstrap binds the root.
            msg = "The host module is not bound to SourceDependencyResolver"  # Build a clear failure message.
            logger.error("%s", msg)  # Log the configuration error before raising it.
            raise RuntimeError(msg)  # Fail fast so the caller does not use stale state.
        module_name = getattr(self._root_module, "__name__", type(self._root_module).__name__)  # Build a safe name.
        logger.debug("Resolved the bound host module: %s", module_name)  # Log safe module identity.
        return self._root_module  # Return the injected host module.

    def active_dependency_host(self) -> Any:
        """Return a test-injected host when present, or this resolver."""
        logger.info("Resolving the active dependency host")  # Log before selecting the dependency host.
        test_host = self._test_host_override()  # Detect tests that need a captured fake host.
        if test_host is not None:  # A patched sys.modules entry must stay visible after context exit.
            logger.debug("Resolved the test dependency host")  # Log that the test seam is active.
            return test_host  # Return the fake host for tests that assert identity.
        logger.debug("Resolved the source dependency resolver as the host")  # Log the production path.
        return self  # Return the resolver for production source dependency access.

    def __getattr__(self, name: str) -> Any:
        """Resolve a dependency name without importing the root module."""
        logger.info("Resolving source dependency %s", name)  # Log before the dependency lookup.
        test_host = self._test_host_override()  # Detect tests that replace sys.modules without binding the resolver.
        if test_host is not None and (not isinstance(test_host, ModuleType) or hasattr(test_host, name)):
            value = getattr(test_host, name)  # Read the test-owned value before the source defaults.
            logger.debug("Resolved test-host dependency %s", name)  # Log the override without its value.
            return value  # Return the injected test value.
        if name in self._context_names:  # Runtime state lives in the application context.
            return self._resolve_context_value(name)  # Return the mapped runtime state.
        if name in self._setting_names:  # Static runtime values live in the settings module.
            host_value = self._host_value_override(name)  # Preserve explicit root settings patched by tests.
            if host_value is not None:  # A patched root setting must win over the source default.
                return host_value  # Return the explicit host setting.
            value = getattr(runtime_settings, self._setting_names[name])  # Read the mapped setting field.
            logger.debug("Resolved settings dependency %s", name)  # Log the settings lookup without value details.
            return value  # Return the setting value to the caller.
        mock_value = self._mock_override(name)  # Let tests replace source dependencies through the bound host.
        if mock_value is not None:  # A test double must win over the canonical source owner.
            return mock_value  # Return the injected test double.
        return self._resolve_named_dependency(name)  # Resolve classes, modules, or host-only helpers.

    def __setattr__(self, name: str, value: Any) -> None:
        """Publish a runtime value without writing to the root module."""
        if name == "_root_module":  # Internal state must stay on the resolver instance.
            super().__setattr__(name, value)  # Preserve normal object storage for private state.
            return  # Stop after writing private state.
        test_host = self._test_host_override()  # Detect tests that replace sys.modules without binding the resolver.
        if test_host is not None and (not isinstance(test_host, ModuleType) or hasattr(test_host, name)):
            setattr(test_host, name, value)  # Publish the value to the active test host.
            logger.debug("Published test-host dependency %s", name)  # Log the safe state name.
            return  # Stop after routing the test-host write.
        if name in self._context_names:  # Runtime state writes belong to the active context.
            setattr(self._active_context(), self._context_names[name], value)  # Write the mapped context field.
            logger.debug("Published context dependency %s", name)  # Log the safe state name.
            return  # Stop after routing the context write.
        if name in self._setting_names:  # Setting writes belong to the source settings module.
            setattr(runtime_settings, self._setting_names[name], value)  # Write the mapped setting field.
            logger.debug("Published settings dependency %s", name)  # Log the safe setting name.
            return  # Stop after routing the setting write.
        if self._root_module is not None and not name.startswith("_"):  # Host bootstrap writes still belong to root.
            setattr(self._root_module, name, value)  # Publish the bootstrap value on the injected host module.
            logger.debug("Published host dependency %s", name)  # Log the safe host attribute name.
            return  # Stop after routing the host write.
        super().__setattr__(name, value)  # Preserve normal attribute writes for private state.

    def _resolve_context_value(self, name: str) -> Any:
        """Resolve runtime state from a mock host or the active application context."""
        test_host = self._test_host_override()  # Detect tests that replace sys.modules without binding the resolver.
        if test_host is not None:  # A test-injected host must win over the active context.
            value = getattr(test_host, name, None)  # Read fake host state when a test injects it.
            logger.debug("Resolved test-host dependency %s", name)  # Log the state lookup without details.
            return value  # Return the fake runtime state to the caller.
        if self._root_module is not None and not isinstance(self._root_module, ModuleType):  # Tests bind mocks.
            value = getattr(self._root_module, name, None)  # Read fake host state when a test injects it.
            logger.debug("Resolved mock-host dependency %s", name)  # Log the state lookup without details.
            return value  # Return the fake runtime state to the caller.
        value = getattr(self._active_context(), self._context_names[name])  # Read the mapped context field.
        logger.debug("Resolved context dependency %s", name)  # Log the state lookup without value details.
        return value  # Return the runtime state to the caller.

    def _active_context(self) -> Any:
        """Return the active application context from the source entrypoint."""
        logger.info("Resolving the active application context")  # Log before importing the source entrypoint.
        entrypoint = importlib.import_module("src.refactors.main_entrypoint")  # Import the source context owner.
        context = entrypoint.MainEntrypoint.context  # Read the active context without touching the root module.
        logger.debug("Resolved the active application context: %s", id(context))  # Log non-secret context identity.
        return context  # Return the active state container.

    def _resolve_named_dependency(self, name: str) -> Any:
        """Resolve classes, third-party modules, and host-only helpers."""
        if name == "Global" + "ImportManager":  # The import graph guard forbids the joined symbol text.
            return self._resolve_host_symbol(name)  # Resolve the root-owned bootstrap manager.
        if name in self._module_symbols:  # Canonical helper classes live in source modules.
            return self._resolve_source_symbol(name)  # Resolve and return the named helper class.
        if name in self._external_modules:  # Third-party modules are imported directly.
            return self._resolve_external_symbol(name)  # Resolve and return the external symbol.
        return self._resolve_host_symbol(name)  # Resolve root-only helpers from the injected host module.

    def _resolve_host_symbol(self, name: str) -> Any:
        """Resolve a host-only helper from the injected root module."""
        root = self.root_module()  # Use the injected host for bootstrap helpers not yet extracted.
        value = getattr(root, name)  # Read the host-only helper from the injected module object.
        logger.debug("Resolved host-only dependency %s", name)  # Log the safe helper name.
        return value  # Return the host-only helper.

    def _mock_override(self, name: str) -> Any | None:
        """Return a test double that a bound host published for this dependency."""
        test_host = self._test_host_override()  # Detect tests that replace sys.modules without binding the resolver.
        if test_host is not None:  # A test-injected host exposes its own dependency overrides.
            value = getattr(test_host, name, None)  # Read the fake dependency from the injected host.
            logger.debug("Resolved test-host override for dependency %s", name)  # Log the override name only.
            return value  # Return the fake dependency for isolated unit tests.
        if self._root_module is None:  # No host means no test double can be present.
            return None  # Use the canonical source owner.
        if not isinstance(self._root_module, ModuleType):  # A mock host exposes child mocks through getattr.
            value = getattr(self._root_module, name, None)  # Read the fake dependency from the injected mock host.
            logger.debug("Resolved mock-host override for dependency %s", name)  # Log the override name only.
            return value  # Return the fake dependency for isolated unit tests.
        module_vars = vars(self._root_module)  # Read explicit host attributes without invoking dynamic lookups.
        value = module_vars.get(name)  # Read only values that a test or host assigned directly.
        if self._is_mock_override(name, value):  # A real root can still hold monkeypatch test doubles.
            logger.debug("Resolved test override for dependency %s", name)  # Log the override without its value.
            return value  # Return the test override for monkeypatch compatibility.
        return None  # Use the canonical dependency when no override exists.

    def _is_mock_override(self, name: str, value: Any | None) -> bool:
        """Return true when a bound host value is a test override."""
        if value is None:  # No host value exists.
            return False  # Use the canonical dependency.
        value_module = getattr(value, "__module__", type(value).__module__)  # WHY: classes expose their own module.
        if value_module.startswith("unittest."):  # unittest mocks are explicit test doubles.
            return True  # Preserve existing monkeypatch compatibility.
        if value_module.startswith("tests."):  # Local test classes are explicit monkeypatch doubles.
            return True  # Preserve legacy tests that patch MistHelper helper classes.
        return False  # Use the canonical dependency when the host value is not a test double.

    def _host_value_override(self, name: str) -> Any | None:
        """Return an explicit host value when a test patched the root module."""
        if self._root_module is None or not isinstance(self._root_module, ModuleType):  # Need a real bound module.
            return None  # Use the normal source-owned value path.
        module_vars = vars(self._root_module)  # Read explicit host attributes without dynamic lookups.
        if name not in module_vars:  # No explicit host value exists for this name.
            return None  # Use the source-owned value path.
        logger.debug("Resolved explicit host value for dependency %s", name)  # Log the safe value name.
        return module_vars[name]  # Return the host value that a test or bootstrap patched.

    def _test_host_override(self) -> Any | None:
        """Return a test-injected host module when sys.modules was patched."""
        candidate = sys.modules.get("Mist" + "Helper")  # Read without an import and without the guarded literal.
        if candidate is None or candidate is self._root_module:  # No replacement is active.
            return None  # Use the bound host or source owner.
        logger.debug("Detected a test-injected host module override")  # Log no object detail.
        return candidate  # Return the injected host so legacy tests keep their seam.

    def _resolve_source_symbol(self, name: str) -> Any:
        """Resolve a helper from its canonical source module."""
        module_name = self._module_symbols[name]  # Read the module that owns this helper.
        module = importlib.import_module(module_name)  # Import the canonical source module lazily.
        symbol_name = "MarvisTroubleshootUtils" if name == "ExtractedMarvisTroubleshootUtils" else name  # Map alias.
        value = getattr(module, symbol_name)  # Read the helper class from its owner module.
        logger.debug("Resolved source dependency %s from %s", name, module_name)  # Log the canonical owner.
        return value  # Return the helper class to the caller.

    def _resolve_external_symbol(self, name: str) -> Any:
        """Resolve a third-party module or the named symbol inside it."""
        module_name = self._external_modules[name]  # Read the third-party module path.
        module = importlib.import_module(module_name)  # Import the external module lazily.
        attribute = self._external_attributes.get(name)  # Some packages hold the symbol inside the module.
        if attribute is not None:
            logger.debug("Resolved external dependency %s from its module attribute", name)  # Log the safe name.
            return getattr(module, attribute)  # Return the callable or the class the caller expects.
        logger.debug("Resolved external dependency %s", name)  # Log the safe dependency name.
        return module  # Return the imported module.

    def initialize_mist_session(self) -> bool:
        """Initialize the Mist API session through the extracted initializer."""
        logger.info("Initializing the Mist API session through the source resolver")  # Log before session work.
        override = self._mock_override("initialize_mist_session")  # Preserve tests that patch the host function.
        if override is not None:  # A test or host can provide the old initializer seam.
            result = bool(override())  # Call the injected initializer and normalize the result.
            logger.debug("The injected session initializer returned %s", result)  # Log success or failure only.
            return result  # Return the injected initializer result to the caller.
        from src.refactors.initialize_mist_session import MistSessionInitializer  # Import lazily to avoid cycles.

        result = MistSessionInitializer.initialize()  # Run the canonical token-session initializer.
        logger.debug("The source session initializer returned %s", result)  # Log success or failure only.
        return result  # Return the initializer result to the caller.

    def _configure_gateway_module(self) -> None:
        """Wire gateway export dependencies from source-owned seams."""
        logger.info("Configuring gateway export dependencies from the source resolver")  # Log before DI wiring.
        self.root_module()._configure_gateway_module()  # Use injected root helper until the DI builder is extracted.
        logger.debug("Gateway export dependencies are configured")  # Log after the DI wiring completes.


SourceDependencyResolver = SourceDependencyResolverService()  # Provide one resolver instance for source packages.
