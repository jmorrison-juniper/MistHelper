Plan to remediate menu #82:

1. Enhance ConstDefinitionsExporter._export_data to call DataExporter.write_with_format_selection(..., api_function_name=<detected_api_function_name>) so PK strategies can be applied when available.
2. Create a mapping or a heuristic to translate discovered API function names to ENDPOINT_PRIMARY_KEY_STRATEGIES keys (e.g., listDeviceModels -> listDeviceModels).
3. Add unit tests for dynamic discovery and for _fetch/_export behavior using mocked modules and functions.
4. Ensure caching behavior remains unchanged.
