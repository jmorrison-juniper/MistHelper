Plan to remediate menu #85:

1. Add PK strategy entries for listSiteAnomalyEvents and device-filtered anomaly outputs (composite keys including device_id/device_mac).
2. Update device_anomaly_events to use DataExporter.write_with_format_selection with a correct api_function_name.
3. Add unit tests: tests/unit/test_device_anomaly_events.py mocking anomaly discovery and API.
4. Run py_compile and pytest.
