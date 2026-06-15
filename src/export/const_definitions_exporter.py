"""Dynamic exporter for Mist const definitions without compatibility shims."""

from __future__ import annotations

import importlib
import inspect
import logging
import os
import pkgutil
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ConstDefinitionsExporter:
    """Export all Mist const endpoints to CSV with discovery + freshness caching."""

    apisession: Any
    data_exporter: Any
    escape_multiline_strings_for_csv: Any
    cache_max_age_hours: int = 24

    def export_all_const_definitions_to_csv(self) -> None:
        """Discover all const endpoints, fetch stale/missing outputs, and write CSVs."""
        print("Export All Available Const Definitions (Dynamic Discovery):")
        logging.info("Starting comprehensive dynamic export of all const definitions")
        try:
            discovered_endpoints = self._discover_const_endpoints()
            if not discovered_endpoints:
                print("! No const endpoints discovered from mistapi library")
                logging.error("Dynamic discovery found no const endpoints")
                return
            print(f"! Successfully discovered {len(discovered_endpoints)} const endpoints dynamically")
            logging.info("Dynamic discovery completed: %d endpoints found", len(discovered_endpoints))
            counters = {
                "processed": 0,
                "skipped_fresh": 0,
                "updated": 0,
                "failed": 0,
            }
            for endpoint_name, endpoint_config in discovered_endpoints.items():
                self._process_endpoint(endpoint_name, endpoint_config, counters)
            self._print_summary(discovered_endpoints, counters)
        except Exception as exception:
            print(f"! Critical error during dynamic const discovery: {exception}")
            logging.error("Critical error during dynamic const discovery: %s", exception)

    def _discover_const_endpoints(self) -> dict[str, dict[str, Any]]:
        """Build endpoint config map from mistapi const package modules."""
        import mistapi.api.v1.const as const_package

        discovered_endpoints: dict[str, dict[str, Any]] = {}
        print("! Dynamically discovering const endpoints from mistapi library...")
        logging.info("Starting dynamic discovery of const endpoints")
        for _importer, module_name, is_package in pkgutil.iter_modules(
            const_package.__path__,
            const_package.__name__ + ".",
        ):
            if is_package:
                continue
            endpoint_name = module_name.split(".")[-1]
            if endpoint_name.startswith("_"):
                continue
            try:
                endpoint_config = self._discover_single_endpoint(endpoint_name, module_name)
                if endpoint_config is not None:
                    discovered_endpoints[endpoint_name] = endpoint_config
            except Exception as exception:
                print(f"    ! Error inspecting {endpoint_name}: {exception}")
                logging.error("Error inspecting const module %s: %s", endpoint_name, exception)
        return discovered_endpoints

    def _discover_single_endpoint(self, endpoint_name: str, module_name: str) -> dict[str, Any] | None:
        """Inspect one const module and return export config when supported."""
        print(f"  ! Inspecting const module: {endpoint_name}")
        module = importlib.import_module(module_name)
        candidate_functions: list[str] = []
        for function_name, function_object in inspect.getmembers(module):
            if not inspect.isfunction(function_object) or function_name.startswith("_"):
                continue
            signature = inspect.signature(function_object)
            parameter_names = list(signature.parameters.keys())
            if "mist_session" in parameter_names or "apisession" in parameter_names:
                candidate_functions.append(function_name)
                logging.debug("Found potential API function in %s: %s%s", endpoint_name, function_name, signature)
        if not candidate_functions:
            print(f"    ! No API functions found in {endpoint_name}")
            logging.warning("No API functions with mist_session parameter found in %s", endpoint_name)
            return None
        selected_function = self._select_const_function_name(candidate_functions)
        if selected_function is None:
            print(f"    ! No suitable API functions found in {endpoint_name}")
            logging.warning("No suitable API function found in %s", endpoint_name)
            return None
        special_handling = self._classify_special_handling(module, selected_function, endpoint_name)
        if special_handling == "skip":
            return None
        filename = self._endpoint_filename(endpoint_name)
        description = f"{endpoint_name.replace('_', ' ').title()} Definitions"
        print(f"    ! Found API function: {selected_function}() -> {filename}")
        logging.debug("Discovered %s: %s() -> %s", endpoint_name, selected_function, filename)
        return {
            "module": module,
            "function": selected_function,
            "filename": filename,
            "description": description,
            "special_handling": None if special_handling == "none" else special_handling,
        }

    @staticmethod
    def _select_const_function_name(candidate_functions: list[str]) -> str | None:
        """Choose preferred API function: list* then get* then first discovered."""
        for function_name in candidate_functions:
            if function_name.lower().startswith("list"):
                return function_name
        for function_name in candidate_functions:
            if function_name.lower().startswith("get"):
                return function_name
        return candidate_functions[0] if candidate_functions else None

    @staticmethod
    def _endpoint_filename(endpoint_name: str) -> str:
        """Convert endpoint snake_case to expected Const{Name}.csv filename."""
        title_name = "".join(part.capitalize() for part in endpoint_name.split("_"))
        return f"Const{title_name}.csv"

    def _classify_special_handling(self, module: Any, function_name: str, endpoint_name: str) -> str:
        """Return endpoint special handling type or skip marker."""
        signature = inspect.signature(getattr(module, function_name))
        required_params = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.default == inspect.Parameter.empty and parameter.name not in ["mist_session", "apisession"]
        ]
        if not required_params:
            return "none"
        parameter_names = [parameter.name for parameter in required_params]
        if endpoint_name == "default_gateway_config" and "model" in parameter_names:
            print(f"    ! Found special endpoint {function_name}() requiring 'model' parameter")
            print("    ! Will call for all available gateway models")
            return "all_models"
        if endpoint_name == "states" and "country_code" in parameter_names:
            print(f"    ! Found special endpoint {function_name}() requiring 'country_code' parameter")
            print("    ! Will call for all available countries")
            return "all_countries"
        print(f"    ! Skipping {function_name}() - requires additional parameters: {parameter_names}")
        logging.info(
            "Skipping %s.%s() - requires parameters: %s",
            endpoint_name,
            function_name,
            parameter_names,
        )
        return "skip"

    def _process_endpoint(self, endpoint_name: str, endpoint_config: dict[str, Any], counters: dict[str, int]) -> None:
        """Export one endpoint with freshness checks and error accounting."""
        counters["processed"] += 1
        filename = endpoint_config["filename"]
        description = endpoint_config["description"]
        print(f"\n! Processing {description} ({endpoint_name})...")
        is_fresh = self._is_output_fresh(filename, endpoint_name)
        if is_fresh:
            counters["skipped_fresh"] += 1
            return
        try:
            rows = self._fetch_rows_for_endpoint(endpoint_name, endpoint_config)
            processed_rows = self.escape_multiline_strings_for_csv(rows)
            self.data_exporter.save_data_to_output(processed_rows, filename)
            print(f"  ! {len(processed_rows)} {description.lower()} exported to {filename}")
            logging.info(
                "Exported %d fresh %s to %s",
                len(processed_rows),
                description.lower(),
                filename,
            )
            counters["updated"] += 1
        except Exception as exception:
            print(f"  ! Error exporting {description.lower()}: {exception}")
            logging.error("Failed to export %s from %s: %s", description.lower(), endpoint_name, exception)
            self.data_exporter.save_data_to_output([], filename)
            counters["failed"] += 1

    def _is_output_fresh(self, filename: str, endpoint_name: str) -> bool:
        """Check whether output file exists and is newer than freshness threshold."""
        file_path = os.path.join("data", filename)
        if not os.path.exists(file_path):
            print(f"  ! {filename} not found - fetching fresh data from API...")
            logging.info("%s not found, fetching from API", filename)
            return False
        try:
            file_modified_time = os.path.getmtime(file_path)
            file_age_hours = (time.time() - file_modified_time) / 3600
            file_timestamp = datetime.fromtimestamp(file_modified_time).strftime("%Y-%m-%d %H:%M:%S")
            if file_age_hours < self.cache_max_age_hours:
                print(f"  ! Found fresh {filename} (created {file_timestamp}, {file_age_hours:.1f}h old)")
                print(f"  ! Skipping API call - using cached data (cache valid for {self.cache_max_age_hours}h)")
                logging.info("Using cached %s file (age: %.1fh)", endpoint_name, file_age_hours)
                return True
            print(f"  ! Found stale {filename} (created {file_timestamp}, {file_age_hours:.1f}h old)")
            print(f"  ! File is older than {self.cache_max_age_hours}h threshold - fetching fresh data from API...")
            logging.info("Refreshing stale %s file (age: %.1fh)", endpoint_name, file_age_hours)
            return False
        except Exception as exception:
            print(f"  ! Error checking file timestamp: {exception}")
            logging.warning("Could not check %s file timestamp, will fetch fresh data: %s", endpoint_name, exception)
            return False

    def _fetch_rows_for_endpoint(self, endpoint_name: str, endpoint_config: dict[str, Any]) -> list[dict[str, Any]]:
        """Fetch endpoint data and normalize payload into row dictionaries."""
        module = endpoint_config["module"]
        function_name = endpoint_config["function"]
        description = endpoint_config["description"]
        special_handling = endpoint_config.get("special_handling")
        print(f"  ! Requesting fresh {description.lower()} from Mist API using {function_name}()...")
        if special_handling == "all_models":
            payload = self._fetch_default_gateway_config_all_models(module, function_name)
        elif special_handling == "all_countries":
            payload = self._fetch_states_all_countries(module, function_name)
        else:
            api_function = getattr(module, function_name)
            response = api_function(self.apisession)
            payload = getattr(response, "data", response) or {}
        return self._payload_to_rows(endpoint_name, payload)

    def _fetch_default_gateway_config_all_models(self, module: Any, function_name: str) -> list[dict[str, Any]]:
        """Fetch default gateway config for all discovered gateway models."""
        print("  ! Special handling: Calling endpoint for all available gateway models...")
        gateway_models = self._discover_gateway_models()
        api_function = getattr(module, function_name)
        all_rows: list[dict[str, Any]] = []
        successful_models = 0
        failed_models = 0
        for model_name in gateway_models:
            try:
                response = api_function(self.apisession, model=model_name)
                model_payload = getattr(response, "data", response) or {}
                all_rows.extend(self._attach_model_to_payload_rows(model_name, model_payload))
                successful_models += 1
            except Exception as exception:
                logging.warning("Failed to get gateway config for model %s: %s", model_name, exception)
                failed_models += 1
        print(f"    ! Successfully retrieved configs for {successful_models} models, {failed_models} failed")
        return all_rows

    def _fetch_states_all_countries(self, module: Any, function_name: str) -> list[dict[str, Any]]:
        """Fetch states for all discovered countries."""
        print("  ! Special handling: Calling endpoint for all available countries...")
        country_codes = self._discover_country_codes()
        api_function = getattr(module, function_name)
        all_rows: list[dict[str, Any]] = []
        successful_countries = 0
        failed_countries = 0
        for country_code in country_codes:
            try:
                response = api_function(self.apisession, country_code=country_code)
                country_payload = getattr(response, "data", response) or {}
                all_rows.extend(self._attach_country_to_state_rows(country_code, country_payload))
                successful_countries += 1
            except Exception as exception:
                logging.warning("Failed to get states for country %s: %s", country_code, exception)
                failed_countries += 1
        print(
            f"    ! Successfully retrieved states for {successful_countries} countries, {failed_countries} failed"
        )
        return all_rows

    def _discover_gateway_models(self) -> list[str]:
        """Discover gateway models from const.device_models payload, with fallback."""
        fallback_models = ["SRX300", "SRX320", "SRX320-POE", "SRX340", "SRX345", "SRX380"]
        try:
            device_models_module = importlib.import_module("mistapi.api.v1.const.device_models")
            list_models = getattr(device_models_module, "listDeviceModels")
            response = list_models(self.apisession)
            payload = getattr(response, "data", response) or {}
            discovered_models: list[str] = []
            if isinstance(payload, dict):
                for model_name, model_details in payload.items():
                    if isinstance(model_details, dict) and model_details.get("type", "").lower() == "gateway":
                        discovered_models.append(model_name)
            elif isinstance(payload, list):
                for model_item in payload:
                    if isinstance(model_item, dict) and model_item.get("type", "").lower() == "gateway":
                        model_name = model_item.get("model") or model_item.get("name")
                        if model_name:
                            discovered_models.append(str(model_name))
            if discovered_models:
                print(f"    ! Discovered {len(discovered_models)} gateway models from device definitions")
                return discovered_models
        except Exception as exception:
            logging.error("Failed to get gateway models list: %s", exception)
        print(f"    ! Using fallback gateway models: {len(fallback_models)} models")
        return fallback_models

    def _discover_country_codes(self) -> list[str]:
        """Discover country codes from const.countries payload, with fallback."""
        fallback_country_codes = ["US", "CA", "GB", "AU", "DE", "FR", "JP", "CN", "IN", "BR"]
        try:
            countries_module = importlib.import_module("mistapi.api.v1.const.countries")
            list_country_codes = getattr(countries_module, "listCountryCodes")
            response = list_country_codes(self.apisession)
            payload = getattr(response, "data", response) or {}
            country_codes: list[str] = []
            if isinstance(payload, dict):
                country_codes = list(payload.keys())
            elif isinstance(payload, list):
                for item in payload:
                    if not isinstance(item, dict):
                        continue
                    if item.get("code"):
                        country_codes.append(str(item["code"]))
                    elif item.get("alpha2"):
                        country_codes.append(str(item["alpha2"]))
                    elif item.get("name"):
                        country_codes.append(str(item["name"])[:2].upper())
            if country_codes:
                print(f"    ! Discovered {len(country_codes)} country codes from country definitions")
                return country_codes
        except Exception as exception:
            logging.error("Failed to get countries list: %s", exception)
        print(f"    ! Using fallback country codes: {len(fallback_country_codes)} countries")
        return fallback_country_codes

    @staticmethod
    def _attach_model_to_payload_rows(model_name: str, payload: Any) -> list[dict[str, Any]]:
        """Normalize one model payload into rows that include model identifier."""
        rows: list[dict[str, Any]] = []
        if isinstance(payload, dict):
            row = {"model": model_name}
            row.update(payload)
            rows.append(row)
        elif isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    item_copy = dict(item)
                    item_copy["model"] = model_name
                    rows.append(item_copy)
                else:
                    rows.append({"model": model_name, "config": str(item)})
        elif payload:
            rows.append({"model": model_name, "config": str(payload)})
        return rows

    @staticmethod
    def _attach_country_to_state_rows(country_code: str, payload: Any) -> list[dict[str, Any]]:
        """Normalize one country payload into state rows with country context."""
        rows: list[dict[str, Any]] = []
        if isinstance(payload, dict):
            for state_code, state_data in payload.items():
                if isinstance(state_data, dict):
                    row = {"country_code": country_code, "state_code": state_code}
                    row.update(state_data)
                    rows.append(row)
                else:
                    rows.append(
                        {
                            "country_code": country_code,
                            "state_code": state_code,
                            "state_name": str(state_data),
                        }
                    )
        elif isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    item_copy = dict(item)
                    item_copy["country_code"] = country_code
                    rows.append(item_copy)
                else:
                    rows.append({"country_code": country_code, "value": str(item)})
        elif payload:
            rows.append({"country_code": country_code, "value": str(payload)})
        return rows

    def _payload_to_rows(self, endpoint_name: str, payload: Any) -> list[dict[str, Any]]:
        """Convert endpoint payload types (dict/list/scalar) to row list."""
        if not payload:
            return []
        if isinstance(payload, list):
            return [item if isinstance(item, dict) else {"value": str(item)} for item in payload]
        if isinstance(payload, dict):
            if endpoint_name == "insight_metrics":
                return self._flatten_insight_metrics(payload)
            rows: list[dict[str, Any]] = []
            for key, value in payload.items():
                if isinstance(value, dict):
                    row = {"name": key}
                    row.update(value)
                    rows.append(row)
                else:
                    rows.append({"name": key, "value": str(value)})
            return rows
        return [{"value": str(payload)}]

    @staticmethod
    def _flatten_insight_metrics(payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Flatten const insight metrics structure into one row per metric."""
        rows: list[dict[str, Any]] = []
        for metric_name, metric_details in payload.items():
            details = metric_details if isinstance(metric_details, dict) else {}
            row = {
                "metric_name": metric_name,
                "description": details.get("description", ""),
                "type": details.get("type", ""),
                "unit": details.get("unit", ""),
                "scopes": ", ".join(details.get("scopes", [])),
                "report_scopes": ", ".join(details.get("report_scopes", [])),
            }
            row["intervals"] = ConstDefinitionsExporter._format_interval_details(details.get("intervals", {}), True)
            row["report_intervals"] = ConstDefinitionsExporter._format_interval_details(
                details.get("report_intervals", {}),
                False,
            )
            rows.append(row)
        return rows

    @staticmethod
    def _format_interval_details(intervals_payload: Any, include_max_age: bool) -> str:
        """Format interval metadata for CSV readability."""
        if not isinstance(intervals_payload, dict) or not intervals_payload:
            return ""
        formatted_items: list[str] = []
        for interval_name, interval_data in intervals_payload.items():
            if not isinstance(interval_data, dict):
                formatted_items.append(f"{interval_name}({interval_data})")
                continue
            if include_max_age:
                formatted_items.append(
                    f"{interval_name}({interval_data.get('interval', 'N/A')}s, max_age:{interval_data.get('max_age', 'N/A')}s)"
                )
            else:
                formatted_items.append(f"{interval_name}({interval_data.get('interval', 'N/A')}s)")
        return "; ".join(formatted_items)

    @staticmethod
    def _print_summary(discovered_endpoints: dict[str, dict[str, Any]], counters: dict[str, int]) -> None:
        """Print and log final execution summary."""
        print("\n! Dynamic Const Export Summary:")
        print(f"  ! Total endpoints discovered: {len(discovered_endpoints)}")
        print(f"  ! Total endpoints processed: {counters['processed']}")
        print(f"  ! Fresh files skipped: {counters['skipped_fresh']}")
        print(f"  ! Files updated/created: {counters['updated']}")
        print(f"  ! Failed endpoints: {counters['failed']}")
        logging.info(
            "Dynamic const export completed: %d discovered, %d processed, %d skipped (fresh), %d updated, %d failed",
            len(discovered_endpoints),
            counters["processed"],
            counters["skipped_fresh"],
            counters["updated"],
            counters["failed"],
        )
