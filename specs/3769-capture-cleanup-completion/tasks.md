# Tasks: Capture Cleanup Completion

**Input**: `spec.md`, `plan.md`, and `contracts/capture-cleanup.md`.

**Boundary**: The coordinator approved the existing `transport/clients/` directory.
The owned test makes four direct children. Preserve every existing test file.
Keep all publication, Actions, and merge operations held.

## Implementation tasks

- [x] T001 Verify exact accepted base and tree. Read the full issue and all open pull request file lists.
- [x] T002 Claim the issue with actual session identity and exact reservation.
- [x] T003 Prove the original ordering defect once with an event-controlled private DELETE barrier.
- [x] T004 Preserve and seal the original failing test, complete log, and native XML.
- [x] T005 Move terminal notification after both independent cleanup attempts in `execution.py`.
- [x] T006 Preserve runtime stop mapping. Report cleanup failures through `UtilityFinisher.failure`.
- [x] T007 Preserve monitor completion timing in `monitoring.py`.
- [x] T008 Validate GET and DELETE HTTP status in `capture.py`. Preserve paths and capture data selection.
- [x] T009 Add owned tests at `tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py`.
- [x] T010 Prove ordering, site and organization identity, no match, missing ID, HTTP failures, exceptions, and independent close failure.
- [x] T011 Add the issue-owned release note.
- [x] T012 Run targeted source quality gates and owned test coverage. Require at least 80 percent changed-branch coverage.
- [x] T013 Run SpecKit analysis. Resolve material inconsistencies within the reserved boundary.
- [ ] T014 Commit locally only. Include the mandatory Copilot App coauthor trailer.
- [ ] T015 Run the authorized native affected utility scope exactly once on the clean local commit.
- [ ] T016 Run analyzer preflight and required committed-scope check against the accepted base.
- [ ] T017 Compare exact native full analyzer findings, engine, configuration, exclusions, and unchanged baseline.
- [ ] T018 Preserve private evidence, the exact 23-item offline pull request template, receipts, and seals.
- [ ] T019 Report exact commit, tree, parent, file boundary, results, clean state, and all limitations to the coordinator.

## Dependencies

T003 precedes all source changes. T005 through T011 precede T012.
T012 and T013 precede T014. T014 precedes T015 and T016.
T015 through T018 precede T019. No additional implementation agent is authorized.

The post-commit tasks retain their precommit checkbox state in this tracked artifact.
Their private final receipt records completion without changing the verified final commit.
The final native scope contains both `runners/utility/` and the full `transport/clients/` directory.

## Verification commands

Use the owned `.venv/bin/python` and installed development commands.
Run commands separately. Stop on an unrelated failure. Preserve its full log.

```bash
rtk proxy .venv/bin/python -m pytest -q tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py
rtk proxy .venv/bin/python -m py_compile src/websocket_streams/live/runners/utility/runner/execution.py src/websocket_streams/live/runners/utility/runner/capture.py src/websocket_streams/live/runners/utility/runner/monitoring.py
rtk proxy .venv/bin/python -m ruff check src/websocket_streams/live/runners/utility/runner tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py
rtk proxy .venv/bin/python -m black --check src/websocket_streams/live/runners/utility/runner tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py
rtk proxy .venv/bin/python -m mypy src/websocket_streams/live/runners/utility/runner --config-file pyproject.toml
rtk proxy .venv/bin/bandit -c pyproject.toml -r src/websocket_streams/live/runners/utility/runner -q
```

Record complete commands and results privately. Preserve native XML and branch coverage JSON.
The original reproduction has one expected failure. It is not an unrelated new defect or a gate bypass.
Do not infer that passing utility tests qualify #3760, #3761, #3767, or #3575.

## Explicit limitations

No production Mist request, database, container, or shared environment is authorized.
No dependency manifest changes, baseline edits, exclusions, assertion weakening, or timeout increases are authorized.
The standard bootstrap failed with Python 3.9. The owned uv environment uses Python 3.13.
The licensed STE dictionary is unavailable. Do not describe partial language checks as full STE conformance.
The accepted base remains `d4d1110352eeab3d9f9d483242232c12f6de4d2d`.
The externally advanced main branch is not an authorized migration target.

## Analysis decisions

The analysis confirmed the requirement-to-task map. Clarifications resolved its local behavior findings.
Normal completion closes the stream without cloud stop. Cancellation means the existing cooperative operator stop event.
`monitoring.py` appears in the plan and preserves the monitor completion timestamp.
The user holds remote delivery. This local repair makes no release or constitution-compliant deployment claim.

## Precommit measurements

The original private barrier failed once in 0.73 seconds. It observed `STOPPED` during blocked matching DELETE.
The owned tests passed after the repair. All changed-method branch coverage exceeds 80 percent.
Capture methods cover 6 of 6 branches. Execution methods cover 9 of 10. Monitoring methods cover 7 of 8.
The full analyzer retains exactly 725 findings and 48 exclusions. Its configuration, engine, and baseline remain unchanged.
Native collection and final post-commit outcomes belong in the private receipt.
