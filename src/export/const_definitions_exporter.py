"""ConstDefinitionsExporter -- dynamic mistapi const endpoint discovery + CSV export.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 17).
Walks ``mistapi.api.v1.const`` via ``pkgutil.iter_modules``, inspects each
module's public functions, and dispatches API calls per special-handling flag
(``all_models`` / ``all_countries`` / ``all_countries_channels`` / ``None``).
Cached CSVs under 24 hours old are reused. Stale or missing files trigger a
fresh fetch.  Callers continue to reach the class via the
``MistHelper.ConstDefinitionsExporter`` re-export alias.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import importlib  # WHY: lazy MistHelper import to reach DataExporter + DataProcessingUtils without circular load.
import logging  # WHY: structured trace for discovery/fetch/export lifecycle events.
from typing import Any  # WHY: helper return types normalize heterogenous mistapi payloads.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).
from src.dataclasses.endpoint_config import EndpointConfig  # Const endpoint descriptor.


class ConstDefinitionsExporter:  # Const definitions exporter.
    """Exports all available const definitions from the Mist API to individual CSV files.

    Implements fully dynamic discovery and smart caching:
    - Automatically discovers all available const endpoints from mistapi library
    - Dynamically inspects each const module to find correct function names
    - Checks if each Const{EndpointName}.csv exists and is fresh (< 24 hours old)
    - If fresh file exists, skips API call for that endpoint
    - If file is missing or stale, fetches fresh data from API

    Usage:
        exporter = ConstDefinitionsExporter(apisession)
        exporter.export_all()
    """

    CACHE_MAX_AGE_HOURS = 24  # Cache freshness window.
    FALLBACK_GATEWAY_MODELS = ["SRX300", "SRX320", "SRX320-POE", "SRX340", "SRX345", "SRX380"]
    FALLBACK_COUNTRIES = ["US", "CA", "GB", "AU", "DE", "FR", "JP", "CN", "IN", "BR"]  # Fallback country list.
    FALLBACK_CHANNEL_COUNTRIES = ["US", "CA", "GB", "AU", "DE", "FR", "JP"]  # Fallback channel countries.

    def __init__(self, api_session: Any) -> None:  # Capture the session.
        """Initialize exporter with API session and counters."""
        self.api_session = api_session  # Store the session.
        self.discovered_endpoints: dict[str, EndpointConfig] = {}  # Discovered endpoints.
        self.endpoints_processed = 0  # Processed count.
        self.endpoints_skipped_fresh = 0  # Skipped-fresh count.
        self.endpoints_updated = 0  # Updated count.
        self.endpoints_failed = 0  # Failed count.

    def export_all(self) -> None:  # Export every const endpoint.
        """Main entry point: discover and export all const definitions."""
        print("Export All Available Const Definitions (Dynamic Discovery):")  # Header.
        logging.info("Starting comprehensive dynamic export of all const definitions...")  # Log start.

        try:
            self._discover_endpoints()  # Discover endpoints.
            if not self.discovered_endpoints:  # None found.
                print("! No const endpoints discovered from mistapi library")  # Tell the user.
                logging.error("Dynamic discovery found no const endpoints")  # Log the error.
                return  # Abort.

            self._process_all_endpoints()  # Process all endpoints.
            self._print_summary()  # Print the summary.

        except Exception as error:  # Discovery failed.
            print(f"! Critical error during dynamic const discovery: {error}")  # Tell the user.
            logging.error("Critical error during dynamic const discovery: %s", error)  # Log the error.

    def _discover_endpoints(self) -> None:  # Discover const endpoints.
        """Discover all const modules in mistapi.api.v1.const package."""
        import pkgutil  # Import pkgutil.

        import mistapi.api.v1.const as const_package  # Import the const package.

        print("! Dynamically discovering const endpoints from mistapi library...")  # Tell the user.
        logging.info("Starting dynamic discovery of const endpoints")  # Log start.

        # Walk every non-package module under mistapi.api.v1.const for inspection.
        const_prefix = const_package.__name__ + "."
        for modname, ispkg in ((m.name, m.ispkg) for m in pkgutil.iter_modules(const_package.__path__, const_prefix)):
            if ispkg:  # Skip subpackages.
                continue  # Next module.
            self._inspect_module(modname)  # Inspect the module.

        print(f"! Successfully discovered {len(self.discovered_endpoints)} const endpoints dynamically")
        logging.info("Dynamic discovery completed: %s endpoints found", len(self.discovered_endpoints))

    def _inspect_module(self, modname: str) -> None:  # Inspect one const module.
        """Inspect a single const module for API functions."""
        endpoint_name = modname.split(".")[-1]  # Endpoint name from path.
        if endpoint_name.startswith("_"):  # Skip private modules.
            return  # Skip it.

        print(f"  ! Inspecting const module: {endpoint_name}")  # Tell the user.

        try:
            module = importlib.import_module(modname)  # Import the module.
            self._inspect_module_functions(module, endpoint_name, modname)  # Find + register the best API function
        except Exception as error:  # Inspection failed.
            module_display_name = modname.split(".")[-1] if modname else "unknown"  # Module display name.
            print(f"    ! Error inspecting {module_display_name}: {error}")  # Tell the user.
            logging.error("Error inspecting const module %s: %s", module_display_name, error)  # Log the error.

    def _inspect_module_functions(self, module, endpoint_name: str, modname: str) -> None:  # Register best API function
        """Find API functions in a module and register the best one, logging when none qualify."""
        functions = self._find_api_functions(module, endpoint_name)  # Find candidate API functions.
        if not functions:  # None found.
            print(f"    ! No API functions found in {endpoint_name}")  # Tell the user.
            logging.warning("No functions found in %s", endpoint_name)  # Warn none found.
            return  # Skip it.
        api_function = self._select_best_function(functions)  # Pick the best function.
        if not api_function:  # No suitable function (none accept a session param)
            print(f"    ! No suitable API functions found in {endpoint_name}")  # Tell the user none.
            logging.warning("No API functions with mist_session parameter found in %s", endpoint_name)  # Warn
            return  # Nothing to register
        self._register_endpoint(endpoint_name, module, api_function, modname)  # Register the endpoint.

    @staticmethod
    def _is_session_api_function(obj) -> bool:
        """Return True when ``obj`` is a public function whose signature accepts a session arg."""
        import inspect  # Local import to keep top-level imports unchanged

        if not inspect.isfunction(obj):  # Skip classes, builtins, and so on
            return False
        sig = inspect.signature(obj)  # Inspect parameters
        param_names = list(sig.parameters.keys())  # Materialize names for membership test
        if not param_names:  # No params -> cannot be an API call
            return False
        return "mist_session" in param_names or "apisession" in param_names  # Session arg required

    def _find_api_functions(self, module, endpoint_name: str) -> list[str]:  # Find candidate API functions.
        """Find all callable API functions in a module."""
        import inspect  # Used for getmembers + signature trace

        functions = []  # Collect function names
        for name, obj in inspect.getmembers(module):  # Walk module members
            if name.startswith("_"):  # Skip private/dunder
                continue
            if not type(self)._is_session_api_function(obj):  # Combined function/session predicate
                continue
            functions.append(name)  # Keep the function
            logging.debug("Found potential API function in %s: %s%s", endpoint_name, name, inspect.signature(obj))
        return functions  # Return the discovered names

    def _select_best_function(self, functions: list[str]) -> str | None:  # Pick the best function.
        """Select the best API function from a list (prefer list*, then get*, else the first)."""
        return (
            self._first_function_with_prefix(functions, "list")  # Prefer a list* function
            or self._first_function_with_prefix(functions, "get")  # Then a get* function
            or (functions[0] if functions else None)  # Fall back to the first (or None when empty)
        )

    @staticmethod
    def _first_function_with_prefix(functions: list[str], prefix: str) -> str | None:  # First name with a prefix
        """Return the first function name whose lowercase form starts with prefix, or None."""
        for func_name in functions:  # Scan in order
            if func_name.lower().startswith(prefix):  # Case-insensitive prefix match
                return func_name  # Use the first match
        return None  # No function matched this prefix

    def _analyze_api_signature(self, module, api_function: str) -> tuple[list, list[str]]:
        """Inspect the API function's signature and return (required_params, optional_param_names)."""
        import inspect  # Import inspect.

        sig = inspect.signature(getattr(module, api_function))  # Read the signature.
        return self._get_required_params(sig), self._get_optional_params(sig)  # (required, optional).

    def _register_endpoint(self, endpoint_name: str, module, api_function: str, modname: str) -> None:
        """Register an endpoint after analyzing its parameters."""
        filename = self._build_filename(endpoint_name)  # Build the filename.
        description = f"{endpoint_name.replace('_', ' ').title()} Definitions"  # Build the description.
        required_params, optional_params = self._analyze_api_signature(module, api_function)  # Read params.
        special_handling = self._determine_special_handling(  # Decide special handling.
            endpoint_name, api_function, required_params, optional_params, filename
        )
        if special_handling == "skip":  # Endpoint to skip.
            return  # Skip it.
        self.discovered_endpoints[endpoint_name] = EndpointConfig(  # Build + register config.
            endpoint_name=endpoint_name,
            module=module,
            function_name=api_function,
            filename=filename,
            description=description,
            modname=modname,
            special_handling=special_handling,
        )
        print(f"    ! Found API function: {api_function}() -> {filename}")  # Tell the user.
        logging.debug("Discovered %s: %s() -> %s", endpoint_name, api_function, filename)  # Trace the find.

    def _build_filename(self, endpoint_name: str) -> str:  # Build the const filename.
        """Convert endpoint_name to ConstTitleCase.csv filename."""
        parts = endpoint_name.split("_")  # Split on underscores.
        title_name = "".join(word.capitalize() for word in parts)  # Title-case the name.
        return f"Const{title_name}.csv"  # Return the filename.

    def _get_required_params(self, sig) -> list:  # type: ignore[no-untyped-def, type-arg]
        """Extract required parameters from function signature."""
        import inspect  # Import inspect.

        return [  # List required params.
            p
            for p in sig.parameters.values()
            if p.default == inspect.Parameter.empty and p.name not in ["mist_session", "apisession"]
        ]

    def _get_optional_params(self, sig) -> list[str]:  # List optional params.
        """Extract optional parameter names from function signature."""
        import inspect  # Import inspect.

        return [  # List optional params.
            p.name
            for p in sig.parameters.values()
            if p.default != inspect.Parameter.empty and p.name not in ["mist_session", "apisession"]
        ]

    def _classify_required_param(
        self, endpoint_name: str, api_function: str, param_names: list[str], filename: str
    ) -> str:
        """Classify endpoints that need a special required-param fan-out (all_models / all_countries / skip)."""
        if endpoint_name == "default_gateway_config" and "model" in param_names:  # Gateway config special case.
            print(f"    ! Found special endpoint {api_function}() requiring 'model' parameter")  # Tell the user.
            print(f"    ! Will call for all available gateway models -> {filename}")  # Tell the user.
            return "all_models"  # All-models handling.
        if endpoint_name == "states" and "country_code" in param_names:  # States special case.
            print(f"    ! Found special endpoint {api_function}() requiring 'country_code' parameter")  # Tell user.
            print(f"    ! Will call for all available countries -> {filename}")  # Tell the user.
            return "all_countries"  # All-countries handling.
        print(f"    ! Skipping {api_function}() - requires additional parameters: {param_names}")  # Tell user skip.
        logging.info("Skipping %s.%s() - requires parameters: %s", endpoint_name, api_function, param_names)
        return "skip"  # Skip it.

    def _determine_special_handling(
        self,
        endpoint_name: str,
        api_function: str,
        required_params: list,  # type: ignore[type-arg]
        optional_params: list[str],
        filename: str,
    ) -> str | None:
        """Determine special handling type for endpoint."""
        if endpoint_name == "ap_channels" and "country_code" in optional_params:  # AP channels special case.
            print(f"    ! Found special endpoint {api_function}() with optional 'country_code' parameter")
            print(f"    ! Will call for all available countries -> {filename}")  # Tell the user.
            return "all_countries_channels"  # All-countries channels.
        if not required_params:  # No required params.
            return None  # Standard handling.
        param_names = [p.name for p in required_params]  # Required param names.
        return self._classify_required_param(endpoint_name, api_function, param_names, filename)  # Special / skip.

    def _process_all_endpoints(self) -> None:  # Process all endpoints.
        """Process each discovered endpoint."""
        for config in self.discovered_endpoints.values():  # Walk endpoints. Keys are unused here.
            self._process_single_endpoint(config)  # Process each.

    def _process_single_endpoint(self, config: EndpointConfig) -> None:  # Process one endpoint.
        """Process a single endpoint with cache checking and data export."""
        print(f"\n! Processing {config.description} ({config.endpoint_name})...")  # Tell the user.

        try:
            if self._is_file_fresh(config):  # File is fresh.
                self.endpoints_skipped_fresh += 1  # Count skipped-fresh.
                self.endpoints_processed += 1  # Count processed.
                return  # Skip it.

            self._fetch_and_export_endpoint(config)  # Fetch and export.
            self.endpoints_processed += 1  # Count processed.

        except Exception as error:  # Processing failed.
            print(f"! Critical error processing {config.endpoint_name}: {error}")  # Tell the user.
            logging.error("Critical error processing %s: %s", config.endpoint_name, error)  # Log the error.
            self.endpoints_failed += 1  # Count failed.
            self.endpoints_processed += 1  # Count processed.

    def _evaluate_cache_window(self, config: EndpointConfig, file_age_hours: float, file_timestamp: str) -> bool:
        """Decide whether the file is within the cache window. Emit fresh/stale user messages either way."""
        if file_age_hours < self.CACHE_MAX_AGE_HOURS:  # Within the window.
            print(f"  ! Found fresh {config.filename} (created {file_timestamp}, {file_age_hours:.1f}h old)")
            print(f"  ! Skipping API call - using cached data (cache valid for {self.CACHE_MAX_AGE_HOURS}h)")
            logging.info("Using cached %s file (age: %.1fh)", config.endpoint_name, file_age_hours)
            return True  # Fresh.
        print(f"  ! Found stale {config.filename} (created {file_timestamp}, {file_age_hours:.1f}h old)")
        print(f"  ! File is older than {self.CACHE_MAX_AGE_HOURS}h threshold - fetching fresh data from API...")
        logging.info("Refreshing stale %s file (age: %.1fh)", config.endpoint_name, file_age_hours)
        return False  # Stale.

    def _is_file_fresh(self, config: EndpointConfig) -> bool:  # Check cache freshness.
        """Check if cached file exists and is fresh enough to use."""
        import os  # Import os.
        import time  # Import time.
        from datetime import datetime  # Import datetime.

        file_path = os.path.join("data", config.filename)  # Build the file path.
        if not os.path.exists(file_path):  # File missing.
            print(f"  ! {config.filename} not found - fetching fresh data from API...")  # Tell the user.
            logging.info("%s not found, fetching from API", config.filename)  # Log the fetch.
            return False  # Not fresh.
        try:
            file_mtime = os.path.getmtime(file_path)  # Read the mtime.
            file_age_hours = (time.time() - file_mtime) / 3600  # Compute age in hours.
            file_timestamp = datetime.fromtimestamp(file_mtime).strftime("%Y-%m-%d %H:%M:%S")  # Format the timestamp.
            return self._evaluate_cache_window(config, file_age_hours, file_timestamp)  # Compare window + emit message.
        except Exception as error:  # Timestamp check failed.
            print(f"  ! Error checking file timestamp: {error}")  # Tell the user.
            logging.warning("Could not check %s file timestamp, will fetch fresh data: %s", config.endpoint_name, error)
            return False  # Not fresh.

    def _fetch_and_export_endpoint(self, config: EndpointConfig) -> None:  # Fetch and export an endpoint.
        """Fetch data from API and export to file."""
        print(f"  ! Requesting fresh {config.description.lower()} from Mist API using {config.function_name}()...")

        try:
            const_data = self._fetch_endpoint_data(config)  # Fetch the data.
            self._export_data(config, const_data)  # Export the data.
        except Exception as error:  # Export failed.
            print(f"  ! Error exporting {config.description.lower()}: {error}")  # Tell the user.
            logging.error("Failed to export %s from %s: %s", config.description.lower(), config.endpoint_name, error)
            mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter helper.
            mh.DataExporter.write_with_format_selection([], config.filename)  # type: ignore[no-untyped-call]
            self.endpoints_failed += 1  # Count failed.

    def _fetch_endpoint_data(self, config: EndpointConfig):  # Dispatch the fetch type.
        """Fetch data based on special handling type."""
        if config.special_handling == "all_models":  # All-models case.
            return self._fetch_all_gateway_models(config)  # Fetch per model.
        elif config.special_handling == "all_countries":  # All-countries case.
            return self._fetch_all_country_states(config)  # Fetch per country.
        elif config.special_handling == "all_countries_channels":  # All-channels case.
            return self._fetch_all_country_channels(config)  # Fetch per country.
        else:
            return self._fetch_standard_endpoint(config)  # Standard fetch.

    def _fetch_standard_endpoint(self, config: EndpointConfig):  # Fetch a standard endpoint.
        """Fetch data from a standard endpoint with no special parameters."""
        api_function = getattr(config.module, config.function_name)  # Resolve the function.
        response = api_function(self.api_session)  # Call the API.
        return getattr(response, "data", response) or {}  # Unwrap data. Default empty.

    def _fetch_one_gateway_model(self, config: EndpointConfig, model: str) -> list:
        """Call the per-model API and return normalized records (or [] on empty / error)."""
        try:
            api_function = getattr(config.module, config.function_name)  # Resolve the function.
            response = api_function(self.api_session, model=model)  # Call with the model.
            model_data = getattr(response, "data", response) or {}  # Unwrap data. Default empty.
            if model_data:  # Have data.
                return self._normalize_model_data(model, model_data)  # Normalize and return.
            return []  # No data for this model.
        except Exception as error:  # Model fetch failed.
            logging.warning("Failed to get gateway config for model %s: %s", model, error)  # Warn the failure.
            raise  # Re-raise so the caller can tally failure count.

    def _fetch_all_gateway_models(self, config: EndpointConfig) -> list:  # type: ignore[type-arg]
        """Fetch gateway configs for all available models."""
        print(f"  ! Special handling: Calling {config.function_name}() for all available gateway models...")
        gateway_models = self._get_gateway_models_list()  # List gateway models.
        all_configs: list = []  # Accumulate configs.
        successful = 0  # Success count.
        failed = 0  # Failure count.
        for model in gateway_models:  # Fetch each model.
            try:
                records = self._fetch_one_gateway_model(config, model)  # Per-model fetch + normalize.
                if records:  # Got rows.
                    all_configs.extend(records)  # Collect them.
                    successful += 1  # Count success.
            except Exception:  # Per-model fetch threw.
                failed += 1  # Count failure.
        print(f"    ! Successfully retrieved configs for {successful} models, {failed} failed")  # Tell the user.
        return all_configs  # Return all configs.

    def _get_gateway_models_list(self) -> list[str]:  # List gateway models.
        """Get list of gateway models from device_models endpoint."""
        try:
            device_models_module = importlib.import_module("mistapi.api.v1.const.device_models")
            device_models_function = device_models_module.listDeviceModels  # Resolve the function.
            response = device_models_function(self.api_session)  # Call the API.
            device_models_data = getattr(response, "data", response) or {}  # Unwrap data. Default empty.

            gateway_models = self._extract_gateway_models(device_models_data)  # Extract gateway models.

            if gateway_models:  # Have models.
                print(f"    ! Discovered {len(gateway_models)} gateway models from device definitions")
                return gateway_models  # Return them.

        except Exception as error:  # Fetch failed.
            logging.warning("Failed to get gateway models list: %s", error)  # Warn the failure.

        print(f"    ! Using fallback gateway models: {len(self.FALLBACK_GATEWAY_MODELS)} models")
        return self.FALLBACK_GATEWAY_MODELS  # Use the fallback list.

    @staticmethod
    def _filter_gateway_models_from_dict(device_models_data: dict) -> list[str]:
        """Filter gateway models from a dict payload (key=model_name, val=details)."""
        gateway_models = []  # Collect names
        for model_name, model_details in device_models_data.items():  # Walk dict entries
            if not isinstance(model_details, dict):  # Skip non-dict values
                continue
            if model_details.get("type", "").lower() != "gateway":  # Only keep gateways
                continue
            gateway_models.append(model_name)  # Keep this gateway
        return gateway_models  # Filtered result

    @staticmethod
    def _filter_gateway_models_from_list(device_models_data: list) -> list[str]:
        """Filter gateway models from a list payload of model dicts."""
        gateway_models = []  # Collect names
        for model_item in device_models_data:  # Walk list items
            if not isinstance(model_item, dict):  # Skip non-dict items
                continue
            model_name = model_item.get("model", model_item.get("name", ""))  # Read the name
            if not model_name:  # Empty name = unusable
                continue
            if model_item.get("type", "").lower() != "gateway":  # Only keep gateways
                continue
            gateway_models.append(model_name)  # Keep this gateway
        return gateway_models  # Filtered result

    def _extract_gateway_models(self, device_models_data) -> list[str]:  # Filter to gateway models.
        """Extract gateway model names from device models data."""
        if isinstance(device_models_data, dict):  # Dict payload branch
            return self._filter_gateway_models_from_dict(device_models_data)
        if isinstance(device_models_data, list):  # List payload branch
            return self._filter_gateway_models_from_list(device_models_data)
        return []  # Unknown shape — empty result

    def _normalize_model_data(self, model: str, model_data) -> list[dict]:  # type: ignore[no-untyped-def, type-arg]
        """Normalize model data into list of records with model identifier."""
        records = []  # Collect rows.

        if isinstance(model_data, dict):  # Dict payload.
            record = {"model": model}  # Start with the model.
            record.update(model_data)  # Merge the data.
            records.append(record)  # Collect the row.
        elif isinstance(model_data, list):  # List payload.
            for item in model_data:  # Walk items.
                if isinstance(item, dict):  # Dict item.
                    item["model"] = model  # Tag the model.
            records.extend(model_data)  # Collect the items.
        else:
            records.append({"model": model, "config": str(model_data)})  # Wrap scalar payload.

        return records  # Return the rows.

    def _fetch_all_country_states(self, config: EndpointConfig) -> list:  # type: ignore[type-arg]
        """Fetch states for all available countries."""
        print(f"  ! Special handling: Calling {config.function_name}() for all available countries...")

        country_codes = self._get_country_codes_list()  # List country codes.
        all_states: list[Any] = []  # Accumulate states.
        successful = 0  # Success count.
        failed = 0  # Failure count.

        for country_code in country_codes:  # Fetch each country.
            try:
                api_function = getattr(config.module, config.function_name)  # Resolve the function.
                response = api_function(self.api_session, country_code=country_code)  # Call with the country.
                country_data = getattr(response, "data", response) or {}  # Unwrap data. Default empty.

                if country_data:  # Have data.
                    records = self._normalize_states_data(country_code, country_data)  # Normalize state rows.
                    all_states.extend(records)  # Collect them.
                    successful += 1  # Count success.
            except Exception as error:  # Country fetch failed.
                logging.warning("Failed to get states for country %s: %s", country_code, error)  # Warn the failure.
                failed += 1  # Count failure.

        print(f"    ! Successfully retrieved states for {successful} countries, {failed} failed")  # Tell the user.
        return all_states  # Return all states.

    def _call_countries_api(self):
        """Call the Mist country definitions endpoint and return raw countries_data ({} on failure)."""
        try:
            countries_module = importlib.import_module("mistapi.api.v1.const.countries")  # Endpoint module
            countries_function = countries_module.listCountryCodes  # Resolve API entrypoint
            response = countries_function(self.api_session)  # Call the Mist API
            return getattr(response, "data", response) or {}  # Unwrap. Default to empty
        except Exception as error:  # Network/import/auth failure
            logging.warning("Failed to get countries list: %s", error)  # Warn for diagnostics
            return {}  # Empty signals caller to use fallback

    @staticmethod
    def _is_valid_alpha2(code: str) -> bool:
        """Return True only when the code is a 2-letter alphabetic string."""
        if not code:  # Reject empty/None up front
            return False
        if len(code) != 2:  # Must be exactly 2 characters per ISO 3166-1 alpha-2
            return False
        return code.isalpha()  # Final alpha-only guard

    @staticmethod
    def _filter_valid_alpha2_codes(country_codes: list[str]) -> list[str]:
        """Keep only 2-letter alphabetic country codes (logs how many were dropped)."""
        valid = [
            c for c in country_codes if ConstDefinitionsExporter._is_valid_alpha2(c)
        ]  # Delegate predicate to helper
        if len(valid) < len(country_codes):  # Some entries failed validation
            logging.debug("Filtered out %s invalid country codes", len(country_codes) - len(valid))
        return valid

    def _fetch_valid_country_codes_from_api(self) -> list[str]:
        """Call the countries endpoint and return the validated 2-letter alpha codes (empty on failure)."""
        countries_data = self._call_countries_api()  # API call with error guard
        country_codes = self._extract_country_codes(countries_data)  # Extract raw codes
        if not country_codes:  # API returned nothing usable
            return []
        valid = ConstDefinitionsExporter._filter_valid_alpha2_codes(country_codes)  # Drop bad codes
        print(f"    ! Discovered {len(valid)} country codes from country definitions")  # User-facing count
        return valid

    def _get_country_codes_list(self) -> list[str]:  # List country codes.
        """Get list of valid country codes from countries endpoint."""
        country_codes = self._fetch_valid_country_codes_from_api()  # Attempt API fetch + validation
        if country_codes:  # API succeeded
            return country_codes
        print(f"    ! Using fallback country codes: {len(self.FALLBACK_COUNTRIES)} countries")  # User-facing fallback
        return self.FALLBACK_COUNTRIES  # Built-in fallback list

    @staticmethod
    def _resolve_country_code(item: dict) -> str:  # Pull a 2-letter ISO code from a heterogenous country dict
        """Resolve a country code from various dict shapes (code | alpha2 | first 2 letters of name)."""
        if item.get("code"):  # Preferred explicit code
            return item["code"]
        if item.get("alpha2"):  # ISO 3166-1 alpha-2 alternate field
            return item["alpha2"]
        return item.get("name", "")[:2].upper()  # Last resort: derive from name

    @staticmethod
    def _codes_from_list(items: list) -> list[str]:  # type: ignore[type-arg]
        """Resolve country codes from a list of country dicts (skips non-dicts and empty resolutions)."""
        codes = []  # Accumulator for resolved codes
        for item in items:  # Walk each entry
            if not isinstance(item, dict):  # Skip non-dict items
                continue
            code = ConstDefinitionsExporter._resolve_country_code(item)  # Resolve via per-item helper
            if not code:  # Empty resolution — skip
                continue
            codes.append(code)
        return codes

    def _extract_country_codes(self, countries_data) -> list[str]:  # Extract country codes.
        """Extract country codes from countries data."""
        if isinstance(countries_data, dict):  # Dict payload — keys are codes
            return list(countries_data.keys())
        if not isinstance(countries_data, list):  # Unknown shape — return empty
            return []
        return ConstDefinitionsExporter._codes_from_list(countries_data)  # Delegate list walk to helper

    @staticmethod
    def _normalize_states_dict(country_code: str, country_data: dict) -> list[dict]:  # type: ignore[type-arg]
        """Convert a {state_code: state_data} dict into a list of tagged state records."""
        records = []  # Accumulator
        for state_code, state_data in country_data.items():  # Walk each state
            if isinstance(state_data, dict):  # Structured payload
                record = {"country_code": country_code, "state_code": state_code}
                record.update(state_data)  # Inline nested fields
                records.append(record)
            else:  # Scalar fallback -> use as the state name
                records.append({"country_code": country_code, "state_code": state_code, "state_name": str(state_data)})
        return records

    @staticmethod
    def _normalize_states_list(country_code: str, country_data: list) -> list:  # type: ignore[type-arg]
        """Tag each dict in the list with ``country_code`` and return the original list (in-place mutation)."""
        for item in country_data:  # Walk items
            if isinstance(item, dict):  # Only dicts get tagged
                item["country_code"] = country_code
        return country_data

    def _normalize_states_data(self, country_code: str, country_data) -> list[dict]:  # type: ignore[no-untyped-def, type-arg]
        """Normalize states data into list of records with country identifier."""
        if isinstance(country_data, dict):  # {state: data} payload
            return type(self)._normalize_states_dict(country_code, country_data)
        if isinstance(country_data, list):  # Already a list of records
            return type(self)._normalize_states_list(country_code, country_data)
        return []  # Unknown shape -> empty

    def _fetch_all_country_channels(self, config: EndpointConfig) -> list:  # type: ignore[type-arg]
        """Fetch AP channels for all available countries."""
        print(f"  ! Special handling: Calling {config.function_name}() for all available countries...")

        country_codes = self._get_channel_country_codes()  # List channel countries.
        all_channels: list[Any] = []  # Accumulate channels.
        successful = 0  # Success count.
        failed = 0  # Failure count.

        for country_code in country_codes:  # Fetch each country.
            try:
                api_function = getattr(config.module, config.function_name)  # Resolve the function.
                response = api_function(self.api_session, country_code=country_code)  # Call with the country.
                country_data = getattr(response, "data", response) or {}  # Unwrap data. Default empty.

                if country_data:  # Have data.
                    records = self._normalize_channels_data(country_code, country_data)  # Normalize channel rows.
                    all_channels.extend(records)  # Collect them.
                    successful += 1  # Count success.
            except Exception as error:  # Country fetch failed.
                logging.debug("Failed to get AP channels for country %s: %s", country_code, error)  # Trace the failure.
                failed += 1  # Count failure.

        print(f"    ! Successfully retrieved AP channels for {successful} countries, {failed} failed")  # Tell the user.
        return all_channels  # Return all channels.

    @staticmethod
    def _filter_to_iso2_country_codes(country_codes: list[str]) -> list[str]:
        """Keep only 2-letter alphabetic ISO country codes. Log when entries were dropped."""
        original_count = len(country_codes)  # Remember the original count for logging.
        filtered = [c for c in country_codes if ConstDefinitionsExporter._is_valid_alpha2(c)]  # Delegate predicate
        if len(filtered) < original_count:  # Some were filtered.
            logging.debug(  # Trace the filter.
                "Filtered out %s invalid country codes for ap_channels", original_count - len(filtered)
            )
        return filtered  # Return the cleaned list.

    def _get_channel_country_codes(self) -> list[str]:  # List channel countries.
        """Get list of country codes for AP channel lookup."""
        try:
            countries_module = importlib.import_module("mistapi.api.v1.const.countries")  # Import countries.
            countries_function = countries_module.listCountryCodes  # Resolve the function.
            response = countries_function(self.api_session)  # Call the API.
            countries_data = getattr(response, "data", response) or {}  # Unwrap data. Default empty.
            country_codes = self._extract_channel_country_codes(countries_data)  # Extract country codes.
            if country_codes:  # Have codes.
                country_codes = self._filter_to_iso2_country_codes(country_codes)  # ISO-2 filter + logging.
                print(f"    ! Discovered {len(country_codes)} country codes for AP channel lookup")
                return country_codes  # Return them.
        except Exception as error:  # Fetch failed.
            logging.warning("Failed to get countries list for AP channels: %s", error)  # Warn the failure.
        print(f"    ! Using fallback country codes: {len(self.FALLBACK_CHANNEL_COUNTRIES)} countries")
        return self.FALLBACK_CHANNEL_COUNTRIES  # Use the fallback list.

    @staticmethod
    def _extract_country_code_from_item(item) -> str | None:  # type: ignore[no-untyped-def]
        """Return the ``alpha2``/``code`` field from a dict item, or None when item is not a dict or has neither."""
        if not isinstance(item, dict):  # Skip non-dict shapes
            return None
        return item.get("alpha2") or item.get("code") or None  # Prefer alpha2, then code

    @staticmethod
    def _country_codes_from_list(countries_list: list) -> list[str]:  # type: ignore[type-arg]
        """Walk a list-of-dicts payload and collect non-empty country codes."""
        candidates = (
            ConstDefinitionsExporter._extract_country_code_from_item(item) for item in countries_list
        )  # Per-item lookup
        return [code for code in candidates if code]  # Filter blanks/Nones

    def _extract_channel_country_codes(self, countries_data) -> list[str]:  # Extract channel countries.
        """Extract country codes from countries data for channel lookup."""
        if isinstance(countries_data, dict):  # Dict payload -> keys are codes
            return list(countries_data.keys())
        if isinstance(countries_data, list):  # List of dicts -> per-item lookup
            return type(self)._country_codes_from_list(countries_data)
        return []  # Unknown shape -> empty

    def _normalize_channels_data(self, country_code: str, country_data) -> list[dict]:  # type: ignore[no-untyped-def, type-arg]
        """Normalize channels data into list of records with country identifier."""
        records = []  # Collect rows.

        if isinstance(country_data, dict):  # Dict payload.
            record = {"country_code": country_code}  # Start with the country.
            record.update(country_data)  # Merge the data.
            records.append(record)  # Collect the row.
        elif isinstance(country_data, list):  # List payload.
            for item in country_data:  # Walk items.
                if isinstance(item, dict):  # Dict item.
                    item["country_code"] = country_code  # Tag the country.
            records.extend(country_data)  # Collect the items.

        return records  # Return the rows.

    def _export_data(self, config: EndpointConfig, const_data) -> None:  # Export const data to CSV.
        """Convert data to list format and export to file."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter + DataProcessingUtils helpers.
        if not const_data:  # No data.
            print(f"  ! 0 {config.description.lower()} exported to {config.filename} (no data available)")
            logging.warning("No %s data available from %s endpoint", config.description.lower(), config.endpoint_name)
            mh.DataExporter.write_with_format_selection([], config.filename)  # type: ignore[no-untyped-call]
            self.endpoints_updated += 1  # Count updated.
            return  # Abort.

        data_list = self._convert_to_list(config.endpoint_name, const_data)  # Normalize to a list.
        processed = DataProcessingUtils.escape_multiline(data_list)  # type: ignore[no-untyped-call]
        mh.DataExporter.write_with_format_selection(processed, config.filename)  # type: ignore[no-untyped-call]

        print(f"  ! {len(processed)} {config.description.lower()} exported to {config.filename}")  # Tell the user.
        logging.info("Exported %s fresh %s to %s", len(processed), config.description.lower(), config.filename)
        self.endpoints_updated += 1  # Count updated.

    def _convert_to_list(self, endpoint_name: str, const_data) -> list:  # type: ignore[no-untyped-def, type-arg]
        """Convert various data formats to list of records for CSV."""
        if isinstance(const_data, list):  # List payload.
            return const_data  # Return it.

        if not isinstance(const_data, dict):  # Non-dict payload.
            return [const_data] if const_data else []  # Wrap or empty.

        if endpoint_name == "insight_metrics":  # Insight metrics special case.
            return self._convert_insight_metrics(const_data)  # Convert metrics.

        return self._convert_standard_dict(const_data)  # Standard dict conversion.

    def _convert_insight_metrics(self, const_data: dict) -> list[dict]:  # type: ignore[type-arg]
        """Convert insight metrics nested structure to flat list."""
        data_list = []  # Collect rows.

        for metric_name, metric_details in const_data.items():  # Walk metrics.
            metric_row = {  # Build the row.
                "metric_name": metric_name,
                "description": metric_details.get("description", ""),
                "type": metric_details.get("type", ""),
                "unit": metric_details.get("unit", ""),
                "scopes": ", ".join(metric_details.get("scopes", [])),
                "report_scopes": ", ".join(metric_details.get("report_scopes", [])),
                "intervals": self._format_intervals(metric_details.get("intervals", {})),
                "report_intervals": self._format_report_intervals(metric_details.get("report_intervals", {})),
            }
            data_list.append(metric_row)  # Collect the row.

        return data_list  # Return the rows.

    def _format_intervals(self, intervals: dict) -> str:  # type: ignore[type-arg]
        """Format intervals dictionary to string representation."""
        if not intervals:  # No intervals.
            return ""  # Empty string.

        interval_info = []  # Collect interval text.
        for interval_name, interval_data in intervals.items():  # Walk intervals.
            interval_str = f"{interval_name}({interval_data.get('interval', 'N/A')}s, max_age:{interval_data.get('max_age', 'N/A')}s)"  # noqa: E501
            interval_info.append(interval_str)  # Collect the text.

        return "; ".join(interval_info)  # Join with semicolons.

    def _format_report_intervals(self, report_intervals: dict) -> str:  # type: ignore[type-arg]
        """Format report intervals dictionary to string representation."""
        if not report_intervals:  # No intervals.
            return ""  # Empty string.

        report_interval_info = []  # Collect interval text.
        for interval_name, interval_data in report_intervals.items():  # Walk intervals.
            interval_str = f"{interval_name}({interval_data.get('interval', 'N/A')}s)"  # Format the interval.
            report_interval_info.append(interval_str)  # Collect the text.

        return "; ".join(report_interval_info)  # Join with semicolons.

    def _convert_standard_dict(self, const_data: dict) -> list[dict]:  # type: ignore[type-arg]
        """Convert standard dictionary to list of records."""
        data_list = []  # Collect rows.

        for key, value in const_data.items():  # Walk entries.
            if isinstance(value, dict):  # Dict value.
                row = {"name": key}  # Start with the name.
                row.update(value)  # Merge the value.
                data_list.append(row)  # Collect the row.
            else:
                data_list.append({"name": key, "value": str(value)})  # Scalar value row.

        return data_list  # Return the rows.

    def _print_summary(self) -> None:  # Print the export summary.
        """Print export summary statistics."""
        print("\n! Dynamic Const Export Summary:")  # Header.
        print(f"  ! Total endpoints discovered: {len(self.discovered_endpoints)}")  # Discovered count.
        print(f"  ! Total endpoints processed: {self.endpoints_processed}")  # Processed count.
        print(f"  ! Fresh files skipped: {self.endpoints_skipped_fresh}")  # Skipped-fresh count.
        print(f"  ! Files updated/created: {self.endpoints_updated}")  # Updated count.
        print(f"  ! Failed endpoints: {self.endpoints_failed}")  # Failed count.

        logging.info(  # Log the totals.
            "Dynamic const export completed: %s discovered, %s processed, %s skipped (fresh), %s updated, %s failed",
            len(self.discovered_endpoints),
            self.endpoints_processed,
            self.endpoints_skipped_fresh,
            self.endpoints_updated,
            self.endpoints_failed,
        )
