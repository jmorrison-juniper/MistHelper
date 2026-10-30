# Quickstart: Required Device Identity for Inventory Failure Records

## Prerequisites

- Use the repository Python environment.
- Do not provide Mist credentials. The selected tests use local data.

## Validate the Behavior

```sh
python -m pytest tests/unit/test_csv_comparator.py
```

Expected result: the comparator rejects missing, blank, or non-string device IDs and preserves valid IDs.

## Validate the Candidate Guard

```sh
python scripts/scan_2753.py
python -m pytest tests/guardrails/test_issue_2753_csv_device_id_scan.py
```

Expected result: the scan reports one source file and zero empty-string device ID defaults. The guard detects a controlled reintroduction.
