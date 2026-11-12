# Implementation Plan: EX Hardware XML Collection

**Branch**: `feat/4769-ex-hardware-xml` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

**Input**: Managed numeric specification at `specs/numbered/0/0/1/2/3/0/3/4/4769-ex-hardware-xml/spec.md`.

## Summary

Add a dedicated WebSockets preset for currently online EX switches in the configured organization.
The server fixes target scope and separate native XML and JSON commands.
BOTH runs XML, then JSON, with independent captures and format outcomes.
Reuse current shell authentication, bounded capacity, and cancellation.

## Technical Context

**Language/Version**: Python 3.15.2 and the current portal JavaScript.

**Primary Dependencies**: Flask, mistapi 0.64.x, websocket-client, pytest, and the existing browser test tools. Use the Python XML standard library. Add no dependency.

**Storage**: Use the existing private batch artifact tree under `data/`. Store XML and JSON files, the existing target outcome manifest, and the existing ZIP archive.

**Testing**: pytest for unit and mocked integration tests. Use the existing WebSockets page browser test for the end-to-end user journey. Run local tests with this worktree's Python 3.15.2 virtual environment.

**Target Platform**: Windows development and the existing Linux container deployment.

**Project Type**: Authenticated Flask operations portal with browser JavaScript and a Mist shell WebSocket client.

**Performance Goals**: Preserve the existing 1,000-target preview limit, target concurrency limit of five, 30-second shell-command deadline, and shared transport capacity.

**Constraints**: Keep each XML response within the existing 1 MiB record bound and each run within the 63 MiB artifact quota. Count both files against the quota. Keep command output within the configured terminal history bound. A response that exceeds a limit fails without a success file.

**Scale/Scope**: All sites in one configured organization and up to 1,000 unique eligible EX targets. Do not span MSP organizations.

## Constitution Check

**Gate result: PASS with scoped existing process-folder debt.**

- **Structure**: Keep the managed eight-level base-5 feature route. Do not change `.specify/feature.json`; it points to another feature and is shared workflow state. Add no direct child under `specs/`.
- **Process folders**: `specs/` has 795 direct entries, including the managed roots and grandfathered records. `changelog.d/` has 290 direct entries. Both counts exceed five. This feature adds only its required unique release-note fragment. Track legacy process-folder reduction as separate maintenance work and do not reorganize shared records here.
- **Package structure**: Add one source module under the existing `web/services/operations` package. Keep new source modules, top-level names, functions, and classes within the five-item limits. Do not increase unrelated source-package debt.
- **Safety**: Keep the action read-only, server-fixed, organization-scoped, EX-only, bounded, and cancellable. Live acceptance requires explicit authorization and current online status.
- **Transport**: Reuse `ex.createShellSession`, `MistStreamEndpoint`, and SDK running statistics. Add no direct HTTP or new WebSocket transport.
- **Output**: Write private artifacts only beneath the existing `data/` artifact root. Stage each target's selected files before publishing them. Count both output formats against the existing quotas.
- **Tests**: Cover fixed native commands, pagination, current status, framing, independent failures, naming, durable retention, and secret protection.
  Extend the existing WebSockets page test. Do not edit the two protected test files named in the handover.
- **Documentation and commit**: Update the operator guide, add `changelog.d/issue-4769-ex-hardware-xml.md`, and use a Conventional Commit subject with `Closes #4769`. Do not edit `CHANGELOG.md`.

### Complexity Tracking

| Existing condition | Why this feature touches it | Separate remediation |
|---|---|---|
| `changelog.d/` and `specs/` exceed five direct children | Repository workflow requires one unique release fragment and one managed specification | Reduce legacy process-folder excess through a separate migration issue. |
| Existing batch, shell, and artifact modules contain large cohesive classes | The feature must extend their established contracts without replacing existing batch and single-shell behavior | Keep new helpers in the hardware XML module and track broader module decomposition separately. |

## Design Decisions

1. Add a dedicated organization-wide preset. Do not expose a generic command field for this action.
2. Resolve organization sites through the existing complete paginated picker, then resolve EX shell targets through the existing family-filtered catalog picker. Deduplicate using the checked organization, site, and device identity.
3. Execute only selected native commands. XML uses `display xml`, and JSON uses `display json`, each with the final `| no-more`.
   BOTH executes XML, then JSON. Wait for a stable CLI prompt before dispatch and completion.
4. Validate the complete UTF-8 XML reply before saving any output. Reject DTD and entity declarations. Preserve the XML document as XML rather than passing it through JSON-line redaction or wrapping it in a JSON envelope.
5. Validate native JSON as a complete object with a nonempty `chassis-inventory` array and chassis content. Preserve its native text.
6. Use safe hostname and device identity stems in one unique run directory. Keep each successful format when another format fails.
7. Keep the existing batch capacity, preview expiry, 30-second command timeout, terminal byte limit, 1 MiB result-record limit, 63 MiB run quota, manifest, and ZIP download. Count every format file against the same run quota.
8. Reject credential fields and values in parsed XML and JSON. Preserve public namespace URLs and slash-separated hardware descriptions. Keep log redaction unchanged.
9. Read current `listSiteDevicesStats` pages at preview and dispatch. Exclude offline and unknown devices, and record later status changes as skipped.
10. Keep hardware files and manifests after session expiry, session deletion, and process restart. Expose the run identifier for filesystem access.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/2/3/0/3/4/4769-ex-hardware-xml/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      ex-hardware-xml.md
    checklists/
      requirements.md
```

### Source Code

```text
src/mist/realtime/websocket_streams/
  intake/start_request/models.py
  live/sessions/manager/factory.py
  live/sessions/record/session.py
  web/services/operations/
    hardware_xml.py
    sessions.py
    artifacts.py
  web/templates/websockets_page.html
  web/static/websockets.js

tests/unit/websocket_streams/web/test_ws_web_services.py
tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py
tests/unit/websocket_streams/live/transport/runtime/test_ws_feature_structure.py
tests/e2e/websockets_tab/test_websockets_page.py
ops-portal/eslint.config.js
ops-portal/.prettierignore
documentation/operator-guide.md
changelog.d/issue-4769-ex-hardware-xml.md
```

`tests/unit/websocket_streams/web` already has five direct entries. Keep the new backend tests inside the existing unowned `test_ws_web_services.py` module rather than adding a sixth entry. Keep the browser journey in the existing unowned page test module because the E2E root already holds its maximum five children.

**Structure Decision**: Extend existing batch, sink, artifact, and session owners.
Keep fixed native commands, XML and JSON validation, safe filenames, and target deduplication in the feature module.
Keep routes and transport endpoints unchanged.

## Mist Cloud Contract Evidence

The existing shell trigger is `mistapi.device_utils.ex.createShellSession`.
The owned shell connection uses `MistStreamEndpoint` and `/api-ws/v1/stream`, with authentication from the SDK session.
The feature adds no transport.
Existing `tests/contract/websocket_streams/test_ws_sdk_contract.py` and `test_ws_utility_trigger_parity.py` protect SDK parity and session fields.
Tests verify the selected native commands, parser safety, per-device failures, and credential handling.

## Validation Gates

- Run the feature's unit and mocked integration tests before implementation changes.
- Run the browser test with a fake WebSocket service. Do not read the main checkout `.env` or use a production credential.
- Run affected Ruff, Black, mypy, Bandit, complexity, pytest, Markdown, citation, and test-quality checks.
- After commit, run the documented test-quality preflight and `test-quality-analyzer --gate --changed-from origin/main`. Do not hide existing baseline findings.
- Do not mark the live-output validation complete. The parent performs it after local deployment and records the XML and JSON evidence.

## Local Environment and Deployment

Create this worktree's environment with Python 3.15.2 and the repository bootstrap script. Do not use the global Python interpreter for tests. The parent owns local container deployment and any later authorized read-only live validation. Do not push or open a pull request in this task.
