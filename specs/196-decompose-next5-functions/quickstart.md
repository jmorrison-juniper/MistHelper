# Quickstart: Implementing Spec 196

## 1) Confirm baseline scope and evidence

- Confirm the five targets listed in `specs/196-decompose-next5-functions/spec.md`.
- Capture baseline complexity/output behavior before refactor changes.

## 2) Implement in this order

1. Extract multi-AP scan capture logic to `src/capture/multi_ap_scan_workflow.py`.
2. Extract site wait/download logic to `src/capture/site_pcap_wait_download_workflow.py`.
3. Extract org wait/download logic to `src/capture/org_pcap_wait_download_workflow.py`.
4. Extract Wi-Fi client export logic to `src/export/wifi_clients_exporter.py`.
5. Extract interactive test flow to `src/troubleshooting/interactive_test_runner.py`.
6. Keep `MistHelper.py` entrypoints as compatibility facades and reduce each target function to `CC <= 10`.

## 3) Testing and parity validation

- Add unit tests for each extracted workflow/exporter/runner module.
- Add `tests/integration/test_next5_compatibility_paths.py` to verify prompt/output/side-effect parity.
- Validate failure and timeout branches for both PCAP wait/download flows.

## 4) Mandatory validation gates

### Complexity gates

- `python -m radon.complexity MistHelper.py -s -a`
- `python -m radon.complexity src -s -a`
- Baseline snapshots used for this implementation:
  - `git show HEAD:MistHelper.py > specs/196-decompose-next5-functions/evidence/.tmp_misthelper_head_baseline.py`
  - `git archive HEAD src | tar -x -C specs/196-decompose-next5-functions/evidence/.tmp_head_tree`

### Quality gates

- `python -m py_compile MistHelper.py`
- `python -m ruff check MistHelper.py src`
- `python -m black --check MistHelper.py src`
- `python -m pytest tests/unit/capture/test_multi_ap_scan_workflow.py tests/unit/capture/test_site_pcap_wait_download_workflow.py tests/unit/capture/test_org_pcap_wait_download_workflow.py tests/unit/export/test_wifi_clients_exporter.py tests/unit/troubleshooting/test_interactive_test_runner.py tests/integration/test_next5_compatibility_paths.py -q`
- `python -m pytest tests/unit/test_packet_capture.py tests/integration/test_top5_compatibility_paths.py tests/integration/test_runtime_coupling.py -q`

## 5) Evidence artifact locations

- Verification matrix and gate outcomes: `specs/196-decompose-next5-functions/evidence/verification-results.md`
- Function/module/test ownership traceability: `specs/196-decompose-next5-functions/evidence/function-module-test-mapping.md`
- Safety and touched-block compliance index: `specs/196-decompose-next5-functions/evidence/safety-audit-index.md`
- Touched-block checklists: `specs/196-decompose-next5-functions/evidence/checklists/`
- Raw complexity artifacts:
  - `specs/196-decompose-next5-functions/evidence/.tmp_cc_misthelper_baseline.txt`
  - `specs/196-decompose-next5-functions/evidence/.tmp_cc_misthelper_post.txt`
  - `specs/196-decompose-next5-functions/evidence/.tmp_cc_src_baseline.txt`
  - `specs/196-decompose-next5-functions/evidence/.tmp_cc_src_post.txt`

## 6) Implementation constraints checklist (must all be true)

- [ ] All touched executable lines include meaningful same-line inline comments.
- [ ] Every meaningful action in touched blocks has `logging.info` before and `logging.debug` after.
- [ ] Exception paths in touched blocks include contextual `logging.error(..., exc_info=True)`.
- [ ] `safe_input` behavior is preserved for interactive/confirmation flows.
- [ ] Menu IDs and existing invocation patterns remain unchanged.

## 7) Completion evidence bundle

Provide in implementation output/PR:

1. Mapping table from original function to extracted module/class/tests.
2. Baseline vs final complexity table for all five targets.
3. Targeted parity and broader regression results.
4. Inline-comment and action-logging compliance summary for touched blocks.
