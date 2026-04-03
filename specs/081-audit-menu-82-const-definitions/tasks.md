Tasks for Menu #82 audit

- T82-1: Modify _export_data to use write_with_format_selection and pass api_function_name when config.function_name is known.
- T82-2: Add mapping logic to resolve function_name -> PK strategy key; document heuristics.
- T82-3: Add unit tests tests/unit/test_const_definitions_exporter.py to cover discovery, special handling, and export.
- T82-4: Run validations (py_compile + pytest).
