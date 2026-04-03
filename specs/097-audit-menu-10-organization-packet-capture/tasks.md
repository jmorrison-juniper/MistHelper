Feature: AUDIT: Menu #10 - Organization Packet Capture (PacketCaptureManager.start_org_packet_capture)
Repository path: C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper
Spec: C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\specs\097-audit-menu-10-organization-packet-capture\spec.md
Plan: C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\specs\097-audit-menu-10-organization-packet-capture\plan.md

PHASE 1 — Setup (project initialization)
- [ ] T001 [P] Create research.md placeholder at C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\specs\097-audit-menu-10-organization-packet-capture\research.md with a short summary of audit findings and links to spec and plan
- [ ] T002 [P] Create data-model.md at C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\specs\097-audit-menu-10-organization-packet-capture\data-model.md listing entities: MxEdge, Interface/Port, Capture Payload, Capture Result
- [ ] T003 [P] Create contracts directory and initial contract file at C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\specs\097-audit-menu-10-organization-packet-capture\contracts\start_org_packet_capture.contract.md that documents the Mist API call and expected payload/result shape
- [ ] T004 [P] Add tests directory and placeholder at C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\test_packet_capture_org.py with module header and imports (pytest, unittest.mock)
- [ ] T005 [P] Add application configuration module at C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\src\config.py with constant DATA_DIR = Path("data").resolve() and configurable POLL_INTERVAL_SEC default

PHASE 2 — Foundational (blocking prerequisites for user stories)
- [ ] T006 Implement normalize_mistapi_response utility in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py to adapt mistapi.get_all results and response objects to a consistent list/dict shape
- [ ] T007 Fix MxEdge listing formatting bug in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (remove stray '}' and ensure f-strings print single-line entries)
- [ ] T008 Unify interactive payload format mapping in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py so options map explicitly to one of: 'pcap', 'stream', 'tzsp' (update prompt text and parsing)
- [ ] T009 Update _execute_org_capture in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py to branch explicitly on capture_format in ('pcap','stream','tzsp') and document behavior in comments
- [ ] T010 Harden polling logic in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (ensure max_polls >= 1, use POLL_INTERVAL_SEC from src\config.py, and make max_wait_time configurable for tests)
- [ ] T011 Replace in-memory pcap download with streaming + retry logic in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py: use requests.get(stream=True) and write to file in chunks, validate Content-Length when present, and implement 3 retries with exponential backoff
- [ ] T012 Add WebSocket message pruning and graceful cancel handling in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\websocket_manager.py to avoid unbounded growth of command_results and support early cancellation

PHASE 3 — User Story Phases (priority order from spec.md)

User Story: US1 — Start org-level packet capture (Priority: P1)
Goal: Allow an operator to interactively start an org-level packet capture and either subscribe to a stream or download a pcap, handling success and failure cases safely.
Independent test criteria:
- Run the interactive menu with a mocked API session returning a single MxEdge and interface stats; after choosing options, assert _execute_org_capture is called with payload containing one mxedge id and a single interface.
- For format=='stream' assert websocket subscribe is called and live counts are displayed; for format=='pcap' assert a file is downloaded to DATA_DIR and its size > 0.

Tasks for US1 (in priority order):
- [ ] T013 [US1] Implement explicit payload construction helper in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py: function build_org_capture_payload(selected_mxedge_id, interface_name, duration, num_packets, max_pkt_len, format, tzsp_host, tzsp_port) that returns the exact dict shape expected by mistapi
- [ ] T014 [US1] Update interactive prompts in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py to use the new build_org_capture_payload helper and validate inputs (indices, duration, num_packets, max_pkt_len, tzsp_port), raising ValueError on invalid input (tests will assert validation)
- [ ] T015 [US1] Implement _execute_org_capture behavior in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py to call mistapi.api.v1.orgs.pcaps.startOrgPacketCapture with the payload, handle non-200 responses, and return the capture result object or raise a controlled exception with user-friendly message
- [ ] T016 [US1] Implement _wait_and_download_pcap_org in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py to poll listOrgPacketCaptures (using normalize_mistapi_response) until pcap_url is present or timeout expires; on pcap_url present, download via streaming to DATA_DIR and validate non-zero size
- [ ] T017 [US1] Implement _subscribe_to_org_capture_stream in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py to subscribe via C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\websocket_manager.py, display live packet counts, and exit cleanly on completion or KeyboardInterrupt
- [ ] T018 [US1] Implement CSV export of capture metadata in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py using the safe field set (capture_id, format, duration, expiry, mxedge_id, interface_name, pcap_path_or_url) and write to C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\data\captures.csv

Testing tasks for US1 (unit tests)
- [ ] T019 [US1] Add unit test: test_build_org_capture_payload in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\test_packet_capture_org.py asserting correct mapping for formats ('pcap','stream','tzsp') and shape of returned dict
- [ ] T020 [US1] Add unit test: test_execute_org_capture_success_and_failure in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\test_packet_capture_org.py mocking mistapi to return 200 with result and non-200 to assert error handling
- [ ] T021 [US1] Add unit test: test_wait_and_download_pcap_org_delayed_url in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\test_packet_capture_org.py mocking listOrgPacketCaptures to return no pcap_url then pcap_url and mocking requests to validate streaming write
- [ ] T022 [US1] Add unit test: test_subscribe_to_org_capture_stream_cancel in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\test_packet_capture_org.py mocking websocket_manager to simulate messages and a KeyboardInterrupt to assert graceful exit
- [ ] T023 [US1] Add integration-style test: tests\test_interactive_packet_capture_org.py at C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\test_interactive_packet_capture_org.py that runs the interactive menu with monkeypatched input and mocked mistapi to assert end-to-end flow (stream and pcap branches)

FINAL PHASE — Polish & Cross-Cutting Concerns
- [ ] T024 [P] Update documentation files:
  - Append migration notes to C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\specs\097-audit-menu-10-organization-packet-capture\research.md describing format mapping decision and download strategy
  - Create quickstart at C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\specs\097-audit-menu-10-organization-packet-capture\quickstart.md with steps to run the interactive menu in test mode
- [ ] T025 Update repository-level housekeeping in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\CHANGELOG.md and run linters (local) to ensure no style regressions

Dependencies (story completion order)
- Phase 1 (T001-T005) must be completed before Phase 2 (T006-T012).
- Phase 2 (T006-T012) must be completed before Phase 3 / US1 (T013-T023).
- Final Phase (T024-T025) may run after Phase 3 tasks but docs (T024) can start in parallel with late story tests (T021-T023) [P].

Parallel execution examples
- Setup tasks T001, T002, T003, T004, and T005 are independent and can be executed in parallel by different engineers/agents. (they touch different files)
- Once foundational utilities exist (T006, T009, T010, T011), test-writing tasks T019-T022 can be implemented in parallel (each test file targets different behaviors) while T014-T017 finalize implementation details.
- Documentation (T024) is parallelizable with final polishing (T025) and some test automation.

Implementation strategy
- MVP first: Implement minimal, well-tested path for 'stream' (subscribe) so operators can reliably start and observe org captures. That means prioritize T013, T014, T016, T018, T019, T020.
- Incrementally add pcap download robustness and polling (T015, T011, T021) once the stream path is stable.
- Deliver tests alongside code changes (prefer small PRs where each PR contains code + tests for the changed behavior).

Validation checklist (format compliance)
- All tasks use the checklist format: every line starts with "- [ ]" and includes a sequential TaskID (T001..T025).
- Tasks for the user story include [US1] label; Phase 1 / Foundational / Polish tasks do not include a story label.
- [P] marker is present where tasks are explicitly parallelizable.
- Every task description includes an absolute file path where changes or artifacts should be created.

Summary report
- Path to generated tasks.md: C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\specs\097-audit-menu-10-organization-packet-capture\tasks.md
- Total tasks: 25
- Tasks per user story:
  - US1: 11 tasks (T013-T023)
  - Setup: 5 tasks (T001-T005)
  - Foundational: 7 tasks (T006-T012)
  - Final/Polish: 2 tasks (T024-T025)
- Parallel opportunities identified: Setup tasks T001-T005; documentation T024 and polish T025; tests T019-T023 after foundational tasks
- Independent test criteria (per story): see US1 Independent test criteria section above (explicit assertions for payload, stream subscription, and pcap download)
- Suggested MVP scope: User Story 1 'stream' branch only (implement payload helper, stream subscription, basic success flow and unit tests) — prioritize T013, T014, T016, T018, T019, T020
- Format validation: ALL tasks conform to the required checklist format (checkbox, TaskID, labels when required, absolute file paths included)

If you want, I can now:
- Create initial research.md and data-model.md contents (fill the placeholders),
- Open PR drafts for each grouped phase (if you want me to split into PRs), or
- Generate the unit test skeletons for tests/test_packet_capture_org.py and test_interactive_packet_capture_org.py now.
