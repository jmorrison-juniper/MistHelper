# Quickstart: Nested JSON Result Preview

## Prerequisites

- Use the repository's configured Python environment.
- Use temporary local files. Do not use production credentials or live Mist calls.
- Keep the feature selector command-scoped:

```text
SPECIFY_FEATURE_DIRECTORY=specs/numbered/0/0/1/1/2/1/2/1/4036-fix-nested-json-preview
```

## Validate the route behavior

After implementation, run the focused route test:

```text
pytest tests/unit/web_portal/test_preview_row_order.py -q
```

The regression case must create a nested JSON fixture such as `mib_generator/allowlist.json`, request its preview through the Flask test client, and compare the returned data with the fixture. The preview must not return the table-route 404. The corresponding download request must still return the unchanged file.

## Validate compatibility and safety

Run the relevant existing tests after implementation:

```text
pytest tests/unit/web_portal/test_preview_row_order.py tests/unit/test_data_browser_path_guard.py tests/unit/web_portal/test_data_browser_preview_streaming.py -q
```

Confirm these outcomes:

1. A nested JSON file uses its complete relative path and returns its own preview data.
2. A nested SQLite table still returns the existing table response.
3. A missing SQLite table retains its existing missing-table response.
4. A denied path remains denied, including traversal and links outside the data directory.
5. JSON rows, order, pagination, download contents, and output-list membership remain unchanged.
6. No test makes a live Mist call or reads production data.

Use the repository's normal implementation and release gates after the focused tests. The release fragment is part of the implementation, not this planning task.

## References

- [Data model](data-model.md)
- [Research decisions](research.md)
- [Feature requirements](../spec.md)
- [Supplied reproduction evidence](evidence.md)
