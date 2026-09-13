# Test Results

## Targeted suites executed

- `tests/unit/test_dependency_check.py`
- `tests/unit/test_gateway_override_analysis.py`
- `tests/unit/test_device_events_52w_exporter.py`
- `tests/unit/test_top5_risk_controls.py`
- `tests/integration/test_packet_capture_org_compatibility.py`
- `tests/integration/test_site_capture_loop_compatibility.py`
- `tests/integration/test_top5_compatibility_paths.py`

## Result summary

- Final targeted run: **PASS** (`11 passed`)
- Packet capture parity tests: **PASS**
- Decomposition compatibility matrix test: **PASS**
- Risk control regression tests: **PASS**

## Full-suite execution evidence (`MistHelper.py --test`)

- Command executed: `python MistHelper.py --test`
- Execution date: `2026-06-01`
- Runtime: `491.29 seconds`
- Telemetry file: `data/test_events_20260601_183352.jsonl`

### Systematic test summary (from runner output)

- Successful operations: `63`
- Failed operations: `0`
- Skipped unsafe operations: `131`
- Total coverage: `63/194 (32.5%)`
- Final status: `All tested operations completed successfully`

### Notes

- The support-ticket flow options (`189`, `190`) logged upstream API `400` errors while still reporting success in the script-level summary; no script-level test failure was raised.
