# Quickstart: Implementing Spec 195

## 1) Confirm baseline and scope

- Verify target list from `specs/195-decompose-top5-functions/spec.md`.
- Capture baseline complexity evidence for the five targets before code changes.

## 2) Implement in this order

1. Extract bootstrap dependency check logic into `src/bootstrap/` and keep `_early_dependency_check` facade.
2. Extract org packet capture workflow into `src/capture/org_capture_workflow.py`.
3. Extract loop orchestration into `src/capture/site_capture_loop.py`.
4. Extract 52-week events export into `src/export/device_events_52w_exporter.py`.
5. Extract WAN override analyzer into `src/gateway/gateway_override_analysis.py`.
6. Remove legacy duplicate `with_wan_overrides` heavy body after parity passes.

## 3) Add/adjust tests

- Add unit tests for each extracted module.
- Add integration parity tests for menu/CLI entry compatibility.
- Ensure prompt/order and output schema checks are explicit.

## 4) Run validation gates

### Complexity gates (required)

- `python -m radon cc MistHelper.py -s -a`
- `python -m radon cc src -s -a`
- `python -m radon cc MistHelper.py src -s -a`

### Quality gates (required)

- `python -m py_compile MistHelper.py`
- `python -m ruff check MistHelper.py src`
- `python -m black --check MistHelper.py src`
- `python MistHelper.py --test`
- targeted test files for this feature

## 5) Completion criteria

- Each target entrypoint/responsibility boundary is CC <= 10.
- Menu IDs, labels, and invocation semantics are unchanged.
- Parity/regression tests pass.
- No sensitive data appears in logs from touched paths.

## 6) Final execution sequence (implemented)

1. Implement extracted modules under `src/bootstrap/`, `src/capture/`, `src/export/`, and gateway analyzer alias path.
2. Rewire `MistHelper.py` top-5 target facades to delegate to extracted classes.
3. Run complexity gate:
   - `python scripts/check_top5_complexity.py`
4. Run required quality gates:
   - `python -m py_compile MistHelper.py`
   - `python -m ruff check MistHelper.py src tests scripts/check_top5_complexity.py`
   - `python -m black --check MistHelper.py src tests scripts/check_top5_complexity.py`
5. Run targeted regression/parity suite:
   - `python -m pytest tests/unit/test_dependency_check.py tests/unit/test_gateway_override_analysis.py tests/unit/test_device_events_52w_exporter.py tests/unit/test_top5_risk_controls.py tests/integration/test_packet_capture_org_compatibility.py tests/integration/test_site_capture_loop_compatibility.py tests/integration/test_top5_compatibility_paths.py -q`

Reference outputs:

- `evidence/final_cc_report.md`
- `evidence/quality_gates.md`
- `evidence/test_results.md`
