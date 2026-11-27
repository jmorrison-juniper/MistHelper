# Implementation Plan: Mist API Contract Evidence for the Cisco Converter

**Branch**: `feat/4634-mist-api-contract-evidence` | **Date**: 2026-11-26 | **Spec**: `specs\numbered\0\0\1\2\2\0\1\4\4634-mist-api-contract-evidence\spec.md`

**Input**: Numeric specification in `specs/numbered/0/0/1/2/2/0/1/4/`. The route has eight base-5 segments. Issue 4634 equals 122014 in base 5, which pads to 00122014.

## Summary

This change adds offline evidence and tests for the Mist write and read operations named by the Cisco converter parity map. It adds no product code. The evidence comes from the bundled OpenAPI file and the pinned mistapi 0.64.1 source. The tests use bundled schemas and mocked SDK sessions. Every write operation stays disabled.

## Technical Context

**Language/Version**: Python 3.15 or newer (`.specify\memory\constitution.md`, Technology and Compatibility Constraints).

**Primary Dependencies**: mistapi 0.64.1 (`requirements.txt` line 129). jsonschema 4.26.0 (`requirements.txt` line 101 and `pyproject.toml` line 47). pytest. The standard library `unittest.mock` module.

**Storage**: None. The tests write no product output and no database row.

**Testing**: pytest in `tests\contract\web_portal\cisco_config_converter`. Guardrail tests in `tests\guardrails`. Ruff, Black, Bandit, and the STE linter.

**Target Platform**: Windows 11, macOS, and Linux. The tests use `pathlib` paths and run no shell command.

**Project Type**: Test-only addition to the Cisco converter feature, plus a specification record.

**Performance Goals**: Parse the 3.6 MB OpenAPI JSON file once for each test session. Run each test with no network wait.

**Constraints**: No live Mist call. No credential. No production write. No direct HTTP. The five-item rule. The function limits in `AGENTS.md`.

**Scale/Scope**: 22 write operations, 18 read operations, 32 planned test functions, 3 test modules, and 1 conftest module.

## Constitution Check

*GATE: Passed before research. Re-checked after design.*

| Rule | Result | Reason |
| --- | --- | --- |
| I. Five-item rule | Pass | `tests\contract\web_portal` holds one child now. This change adds one child, so it holds two. |
| I. Grandfathered parents | Pass | `tests\contract` (17 children) and `src\mist\resources\gateway\overrides` (six children) receive no change. |
| I. Record folders | Pass | The feature root holds five children. `design` holds five children. `design\contracts` holds four. |
| II. Class-based architecture | Pass | Each test module groups its tests in classes. The change adds no wrapper function. |
| III. Safety first | Pass | The change adds no write, no prompt, and no destructive operation. |
| IV. Full deployment pipeline | Pass | `tasks.md` lists the local gates, the pull request, the remote CI, and the merge. |
| V. Observability and logging | Pass with condition | Each test helper that reads a file logs before and after the read. Log text uses ASCII only. |
| VI. Inline comments | Pass with condition | Each executable line in the new test modules carries an inline comment. |
| VII. Action logging | Pass with condition | The condition of Principle V also applies to each test helper. |
| Mist Cloud: mistapi only | Pass | The change uses no direct HTTP. The tests call mistapi functions through a mocked session. |
| Mist Cloud: owned WebSocket | Pass | The feature owns no WebSocket transport. |
| Python version | Pass | The change uses no syntax older than Python 3.15. |
| Podman | Not applicable | No container starts. The local gates need no container. |
| File paths | Pass | The tests use `pathlib.Path` and no hardcoded separator. |
| Secrets | Pass | The fixtures are synthetic. The tests read no credential variable. |
| Security findings | Pass | The change adds no suppression comment. Bandit scans the test tree (`.github\workflows\ci.yml` line 451). |
| Menu operations | Not applicable | The change adds no menu operation. |
| Spec escalation | Pass | The change touches more than three files, so this record is required. |
| Release note | Pass | The change adds one fragment under `changelog.d`. |

## Architecture

A registry constant in `conftest.py` lists the 22 write operations and the 18 read operations. The contract documents in `design\contracts` mirror that registry. Three test layers read the registry:

1. The OpenAPI layer reads `documentation\mist-api-openapi31json.json`. It checks operation IDs, verbs, paths, request bodies, and declared responses.
2. The SDK layer reads the installed mistapi functions with `inspect`. It calls the write wrappers through a mocked session and checks forwarding, verb, path, and retry behavior.
3. The payload layer validates synthetic request bodies against the bundled schemas and against a local allowlist.

No product module changes. The change creates no runtime state.

## Project Structure

### Documentation (this feature)

```text
specs\numbered\0\0\1\2\2\0\1\4\4634-mist-api-contract-evidence\
  spec.md
  plan.md
  tasks.md
  analysis.md
  design\
    research.md
    data-model.md
    quickstart.md
    contracts\
      mist-write-operations.md
      mist-read-operations.md
      mist-payload-fields.md
      mist-sdk-behavior.md
    checklists\
      requirements.md
      security.md
      contract.md
```

### Source Code (repository root)

```text
tests\contract\web_portal\cisco_config_converter\
  conftest.py
  test_mist_openapi_contract.py
  test_mist_sdk_contract.py
  test_mist_payload_fixtures.py
changelog.d\issue-4634-mist-api-contract-evidence.md
```

**Structure Decision**: The test folder sits under `tests\contract\web_portal`. It does not sit under the converter integration folder. Record 4649 projects that folder at five children (analysis finding A-14). The parent `tests\contract` already holds 17 children, so it receives no child.

## File-by-File Change Map

| Repository path | Action | Purpose |
| --- | --- | --- |
| `specs\numbered\0\0\1\2\2\0\1\4\4634-mist-api-contract-evidence\` (root files) | Add | Record root: `spec.md`, `plan.md`, `tasks.md`, `analysis.md` |
| `specs\numbered\0\0\1\2\2\0\1\4\4634-mist-api-contract-evidence\design\` (files) | Add | `research.md`, `data-model.md`, `quickstart.md` |
| `specs\numbered\0\0\1\2\2\0\1\4\4634-mist-api-contract-evidence\design\contracts\` | Add | Four interface contract files |
| `specs\numbered\0\0\1\2\2\0\1\4\4634-mist-api-contract-evidence\design\checklists\` | Add | Three checklist files |
| `tests\contract\web_portal\cisco_config_converter\conftest.py` | Add | Registry constant, OpenAPI loader, and socket block |
| `tests\contract\web_portal\cisco_config_converter\test_mist_openapi_contract.py` | Add | OpenAPI contract tests |
| `tests\contract\web_portal\cisco_config_converter\test_mist_sdk_contract.py` | Add | SDK signature, forwarding, retry, failure, and guard tests |
| `tests\contract\web_portal\cisco_config_converter\test_mist_payload_fixtures.py` | Add | Synthetic fixture tests |
| `changelog.d\issue-4634-mist-api-contract-evidence.md` | Add | One release note fragment |

Modify: none. Delete: none.

## Dependencies

- mistapi 0.64.1 is the pinned SDK. No change.
- jsonschema 4.26.0 is declared and installed. No change.
- Parent issue 4224 owns the gateway template mapping in `src\interfaces\portals\cisco_config_converter\conversion.py`.
- PR 4596 merged on 2026-11-13. It supplies the parity contract file.
- Records 4636, 4644, and 4645 consume this evidence. Issue 4636 owns the package capacity work (task T004).

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| The SDK repeats HTTP 429 for writes (`__api_request.py` lines 209 to 237). | Count each repeat as one attempt. Classify a final 429 as indeterminate. Pin the count with a test. Keep writes disabled. |
| The SDK logs write request bodies at DEBUG (`__api_request.py` lines 296 and 320). | Keep secret-bearing families disabled. Require redaction evidence before enablement. Record the item in the security checklist. |
| The schema and the service behavior differ. | Keep writes disabled. Owner review under gate G4 remains required. |
| The test folder exceeds five children. | Place the tests under `tests\contract\web_portal`. Record the sibling projection. |
| The issue evidence cites a missing path and an open PR that merged. | Correct the facts in `analysis.md`. The issue owner updates the comments. |
| Pin text in three documents differs from `pyproject.toml`. | Use version 0.64.1. A separate issue corrects the text. |
| A synthetic fixture contains customer data. | Write fixtures from the schema only. Review the fixtures in the security checklist. |

## Rollback Steps

1. If the pull request merged, revert the single squash commit on `main`.
2. If the pull request did not merge, close it, delete the branch, and remove the worktree.

Caution: Reverting removes the evidence and the tests. It changes no Mist object, because this change makes no Mist request.

## Complexity Tracking

No constitution rule needs a justified violation. The change adds no direct child to a noncompliant parent. The existing debt remains recorded. `tests\contract` holds 17 children, and `src\mist\resources\gateway\overrides` holds six children. A separate remediation action owns that debt.

## Git Flow

Before task T-PR, claim issue 4634 with the `in-progress` label. Create a worktree from `main` for the branch named in this record. This follows `AGENTS.md` (Git flow).
