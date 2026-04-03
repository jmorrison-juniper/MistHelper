Tasks for Menu #68 audit

- T68-1: Add PK strategy for getSiteInsightMetrics.
- T68-2: Replace DataExporter.save_data_to_output with DataExporter.write_with_format_selection(..., api_function_name="getSiteInsightMetrics").
- T68-3: Add tests/unit/test_site_insight_metrics.py to cover normal and empty-data cases.
- T68-4: Run validations (py_compile + pytest).
