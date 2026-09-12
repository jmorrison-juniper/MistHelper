# US1 Packet Capture Parity Evidence

- Delegated `_execute_site_capture_loop` through `SiteCaptureLoopRunner`.
- Delegated `start_org_packet_capture` through `OrgCaptureWorkflow`.
- Added integration tests:
  - `tests/integration/test_packet_capture_org_compatibility.py`
  - `tests/integration/test_site_capture_loop_compatibility.py`
