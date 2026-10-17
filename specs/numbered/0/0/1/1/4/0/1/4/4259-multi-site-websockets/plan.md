# Implementation Plan: Multi-site WebSocket operations

**Branch**: `jmorrison-juniper-multi-site-websockets`

**Date**: 2026-10-16

**Issue**: #4259

**Spec**: [spec.md](spec.md)

**Input**: `specs/numbered/0/0/1/1/4/0/1/4/4259-multi-site-websockets/spec.md`

## Summary

Add Single Site and Multi Site tabs to the existing Flask WebSockets page.
Keep the Single Site form, repeatable channel selections, terminal, and routes unchanged.
Use catalog metadata to discover eligible organization targets through Mist SDK methods.
Resolve all selections into a fixed target snapshot before confirmation.
Run one public batch session with bounded private target work.
Save redacted results as combined JSONL, grouped JSONL, or both.

This plan defines the design, implementation, validation, and delivery work for issue #4259.
The tasks document assigns the implementation and delivery steps.
It does not change `.specify/feature.json`, which PR #4260 owns.
Do not read or change `tests/unit/websocket_streams/web/test_ws_blueprint_routes.py`, which PR #4208 owns.

### Shell assumption

A Multi Site shell preview accepts a finite operator-supplied command list before review.
It runs that list against each explicitly selected device with bounded concurrency.
It captures the normalized prompt from initial output before sending commands.
It requires that same prompt and two seconds without output after every command.
It preserves partial output and skips later commands if the prompt deadline expires.
It closes each shell after output collection or the deadline.
Confirmation binds to the exact operation, ordered command list, and target set.
The existing Single Site interactive shell remains unchanged.
There is no interactive broadcast input after batch admission.

## Technical Context

| Item | Decision |
| - | - |
| Language/Version | Python 3.13 or newer and vanilla JavaScript |
| Primary Dependencies | Existing Flask 3.x, `mistapi>=0.64.0,<0.65`, and the owned Mist WebSocket transport |
| Storage | Process-local session coordination and session-owned files under `data/` |
| Testing | pytest unit, SDK contract, Flask integration, and existing browser test infrastructure |
| Target Platform | Windows, macOS, and Linux with the current single-worker portal |
| Project Type | Existing Flask operations portal feature |
| Performance Goals | Bounded target concurrency, memory, discovery, and disk writes |
| Constraints | Preserve safety classes, typed confirmations, feature locks, authentication, redaction, and stream limits |
| Scale/Scope | One configured organization and one catalog operation per batch |

No new library, database, server, or root source package is required.
The npm frontend in `ops-portal/` is not this page's implementation surface.

### Resource decisions

These values are proposed design limits, not measured service performance.

| Resource | Design limit |
| - | - |
| Accepted targets | 1 through 1000, after deduplication |
| Channel concurrency | Exactly 1 shared connection for all selected paths |
| Utility and shell concurrency | Default 3, request range 1 through 5 |
| Shared active transport budget | Existing `max_sessions` value, including Single Site work |
| Shell commands | 1 through 20 ordered commands |
| Shell command size | 4096 UTF-8 bytes per command and 16384 bytes per list |
| Target preview | 300 seconds, one use, tied to the authenticated portal scope |
| Discovery retries | Use the Mist SDK's bounded rate-limit retries only |
| Saved batch output | 64 MiB total, including grouped copies and the manifest |

Validate proposed limits before work starts.
Reject an oversized selection instead of silently truncating it.
Expose effective limits through the batch preview response.
Use one shared transport permit pool across batches and Single Site work.
A batch reserves one public session slot, but its children never enter the public session registry.
Do not hold a transport permit while a target waits in the queue.
Reserve available capacity for an admitted Single Site session before dispatching another batch target.

Keep current idle, maximum lifetime, buffer, terminal-history, message-rate, and capture limits.
Use the parent start time for the batch lifetime.
Polling the parent renews its read time, not its lifetime.
Bound the parent message buffer instead of multiplying its allowance by target count.
Write accepted records to disk before buffer eviction.
If storage fails or reaches its limit, stop dispatch, preserve saved results, and report `output_failed`.

## Constitution Check

**Authority**: `.specify/memory/constitution.md`, version 1.9.0.

The pre-design check permits research within the existing transport exception.
The post-design check permits this plan, but does not approve implementation.
No code gate or live validation ran during planning.

| Gate | Pre-design check | Post-design check |
| - | - | - |
| I. Five-Item Rule | Keep existing package roots | No new direct child under either `live` directory or either `sessions` directory |
| II. Class-based behavior | Reuse named catalog and session services | Separate discovery, scheduling, shell collection, and artifact ownership |
| III. Safety | Preserve catalog locks and typed words | Bind confirmation to the operation, parameters, commands, and exact target snapshot |
| IV. Deployment | Reuse the current portal service | Keep the feature within existing package files and deployment settings |
| V. Observability | Reuse structured logging boundary | Log safe counts and states before and after actions |
| VI. Inline comments | No implementation code | Require comments for each future executable line |
| VII. Action logging | No new runtime action | Require before, after, and error records without secrets |
| REST SDK boundary | Use authenticated `mistapi` methods only | Explicit arguments and complete SDK pagination |
| Owned WebSocket exception | Keep the existing affected flows only | Preserve first output, raw split sequences, SDK authentication, and endpoints |
| Output boundary | Product output remains under `data/` | Server-created paths, storage failure reporting, and session cleanup |
| Export backends | No new menu or API data export | JSONL files are session evidence, not a replacement for configured API export backends |
| Ownership | Work only on issue #4259 documents | Preserve PR #4260's pointer and PR #4208's test file |

### Required transport proof

The matching SDK path is
`mistapi.device_utils.__tools.__ws_wrapper.WebSocketWrapper.start_with_trigger`.
It triggers work before subscription and can lose the first output.
The SDK screen path also damages control sequences split across updates.

Existing proof names are:

- `tests/contract/websocket_streams/test_ws_sdk_contract.py::test_trigger_order_controls_early_command_event_retention`
- `tests/contract/websocket_streams/test_ws_sdk_contract.py::test_split_screen_sequence_requires_owned_byte_retention`

The earlier terminal plan records one early event and two split frames in these proofs.
It records SDK retention of zero early events and owned retention of one early event.
These are historical results, not results from this planning run.
Preserve the private-session contracts for `_apitoken`, `_apitoken_index`, `_session`, and `_cloud_uri`.
Preserve token rotation, cookie authentication, TLS validation, and the stream endpoint.
Preserve SDK utility trigger requests for each device.

**Implementation gate**: ERROR if either proof is absent or fails with the supported SDK.
Run the proofs before implementation approval.
Return affected flows to the SDK only after a reviewed release passes both output contracts.

### Setup and hook checks

The Spec Kit setup requires PowerShell, but `pwsh` is unavailable.
Use `.specify/templates/plan-template.md` manually without changing the feature pointer.
Keep `scripts/bootstrap_worktree.py` available for later test setup.
The existing spec directory determines this plan's scope.
Parse hooks with an available YAML parser before and after planning.
Both enabled plan hooks are optional commit hooks.
Do not execute them during artifact generation because this phase does not create a commit.
The mandatory companion hook is disabled.

## Project Structure

### Documentation for this feature

```text
specs/numbered/0/0/1/1/4/0/1/4/4259-multi-site-websockets/
  spec.md
  checklists/requirements.md
  plan.md
  tasks.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      batch-api.md
      discovery.md
      output-and-ui.md
```

The existing `specs/` root remains unchanged.
The feature directory has five direct entries.
The design folder has four direct entries, and its contracts folder has three.
This layout stays within the five-item rule without a feature-folder exception.

### Existing source and test locations

All source paths below start at `src/mist/realtime/websocket_streams/`.

| Location | Planned responsibility |
| - | - |
| `catalog/model.py` | Read `ChannelDefinition`, `UtilityDefinition`, field metadata, family, scope, and safety |
| `intake/pickers/` | Complete SDK discovery and natural-key validation |
| `intake/start_request/` | Separate batch request checks without changing legacy request keys |
| `live/sessions/manager/` | Parent admission, bounded target scheduling, and cancellation |
| `live/sessions/record/` | Target states, result identity, and session-owned artifacts |
| `live/runners/` existing nested packages | SDK triggers and finite shell collection through the current transport |
| `web/blueprint/` existing nested packages | Add batch routes and keep existing route behavior |
| `web/services/` existing nested packages | Resolve previews, confirmations, batches, and downloads |
| `web/templates/websockets_page.html` | Add the two accessible tab panels |
| `web/static/websockets.js` | Add isolated Multi Site state and target controls |

Keep tests under existing `tests/unit/websocket_streams/`,
`tests/contract/websocket_streams/`, and `tests/e2e/websockets_tab/` domains.
Use existing test files when a parent is full.
Place batch route checks in `tests/unit/websocket_streams/web/test_ws_web_services.py`.
Do not use the route test file owned by PR #4208.

**Structure Decision**: Extend existing package children.
Do not create `live/batches`, a new frontend, or a new test root.
Before implementation, count each exact destination with the repository guard.
If a destination has five children, edit an existing child or restructure through an approved ownership change.
Never add a sixth child as a temporary measure.

## Phase 0: Research

Research decisions and evidence are in [research.md](design/research.md).
The research covers catalog scope, pagination, transport proof, session ownership, shell completion, output safety, and directory capacity.
No unresolved clarification marker remains.
Proposed numeric limits are explicit design decisions.
They do not claim undocumented Mist API maxima.

## Phase 1: Design

### Discovery and immutable admission

Derive target fields from catalog metadata instead of fixed UI operation lists.
Use the configured organization, not an organization supplied by a request.
Use the validated runtime page limit, which defaults to 1000 and permits 1 through 1000.
Fetch each later page through `mistapi.get_next` and validate its response before appending records.
Do not use `mistapi.get_all` where it cannot report a failed page.
Pass `type="all"` to `listSiteDevices`.
Keep complete lists for the preview and admitted batch.
Key cached reads by organization, scope, method, filters, and operation.
Discard stale browser responses when the selection revision changes.

Resolve `all` selections to explicit natural-key tuples before confirmation.
Do not invent site membership for organization-only operations or unassigned Mist Edges.
Run an organization channel once rather than once per selected site.
Represent its scope with `site_id: null` and an explicit organization target.
Explain unsupported client association instead of using unverified site-wide clients.
Keep client utility parameters distinct from resource target identifiers.

### Parent session and target work

Reuse the session manager's admission and retention policy.
Use one public session ID for the batch.
Maintain a private target ledger and one outcome for every admitted target.
Dispatch a target only when its batch and shared transport permits are available.
Build catalog paths from checked identifiers only.
Keep the ten-path limit for the existing Single Site request.
Use one owned connection for all validated paths in a Multi Site channel batch.

Cancellation atomically marks queued targets stopped before the next dispatch.
Signal active runners and close sockets through their existing stop contract.
Keep completed output and the first target failure.
A target failure does not stop other valid targets.
Do not retry a utility trigger or shell command automatically after ambiguous execution.
Rely on the Mist SDK's bounded 429 retry and backoff behavior for reads.
Do not add an outer retry loop that multiplies Mist requests.

For a channel batch, build one catalog path for each selected target.
Subscribe to all paths through one owned WebSocket connection.
Map each returned path to its frozen target identity.
Do not apply the Single Site ten-path validation limit to this batch request.
The channel batch uses one transport permit.
Utility and shell batches use bounded private target runners.

For a change or shell batch, derive a typed phrase such as `RUN 4 TARGETS`.
Bind the phrase to the exact operation, parameters, ordered commands, and target fingerprint.
Keep the existing Single Site device-name confirmation unchanged.

### Finite shell collection

Require explicit device selection and the existing shell feature lock.
Resolve an `all` device choice into an explicit list before operator review.
Open one shell per running device.
Capture and normalize the initial prompt before sending the first command.
Send commands in order and collect output under the device identity.
Use an output-aware prompt boundary and a bounded quiet interval between commands.
Never use a fixed sleep alone as proof of command completion.

Use a 30-second initial-output deadline and a 30-second per-command deadline within the parent lifetime.
Require the same normalized prompt and two seconds without output before the next command.
If the initial or returned prompt is not recognized, stop that target with `completion_unproven`.
Preserve partial output and do not send later commands to an unknown shell state.
Reject continuous, interactive, or paged commands when finite completion cannot be proved.
Test command echo, split prompts, delayed chunks, and unsolicited output.
Close the shell after the last confirmed command output or a deadline.
A clean socket close alone does not prove command success.
Report collection completion separately from a device command's unavailable exit status.

### Artifacts and interface contracts

See [data-model.md](design/data-model.md) for identities and state transitions.
See [batch-api.md](design/contracts/batch-api.md) for additive portal routes.
See [discovery.md](design/contracts/discovery.md) for SDK calls and error rules.
See [output-and-ui.md](design/contracts/output-and-ui.md) for files, cleanup, and browser behavior.
See [quickstart.md](design/quickstart.md) for validation commands and expected results.

## Verification and Delivery Order

1. Add failing contract tests for pagination, immutable confirmation, resource limits, and output containment.
2. Extend discovery and intake through existing package children.
3. Add private target scheduling and result persistence under one public session.
4. Add finite shell collection without changing Single Site terminal behavior.
5. Add Multi Site controls and run unit, contract, integration, and browser checks.

Before implementation approval, run the transport proofs and all changed-file gates.
Include positive tests and negative tests for every safety guard.
Count examined fixtures and targets in test evidence.
Keep mock evidence under temporary paths or ignored `test-artifacts/`.
Run no live shell during this planning work.

Later delivery requires the complete repository pipeline and a separate approved implementation change.
Use a Conventional Commit subject such as `feat(web-portal): add multi-site websocket batches`.
Update user documentation and the issue-owned release note only during authorized implementation.

## Complexity Tracking

| Existing condition | Constraint for #4259 | Separate remediation action |
| - | - | - |
| Both `live` directories have five direct entries | Add no direct child | Capacity action CAP-4259-1: inventory nested owners and approve a later package split |
| Both `live/sessions` directories have five direct entries | Edit existing children only | CAP-4259-1 also reserves capacity through a content-preserving move and import tests |
| Existing catalog, intake, web, and browser folders have structural debt | Do not increase their direct child counts | CAP-4259-2: measure those parents and migrate one owned group in a separate change |
| Spec Kit requires several supporting documents | Keep supporting documents under `design/` | CAP-4259-3: update Spec Kit tooling to preserve this bounded nested layout |
| Owned WebSocket exception uses private SDK fields | Keep existing proof and scope | Reevaluate after a reviewed supported SDK release |

CAP-4259 actions are planning records, not newly filed GitHub issues.
Do not mix their package moves into this document-only change.
The implementation owner must resolve destination capacity before adding a new module.
No new product-code structure exception is approved.

## Post-design Review

The design preserves existing Single Site requests, paths, and the interactive shell.
It uses SDK-only discovery and the current owned transport exception.
It defines target outcomes, cancellation, finite shells, saved output, and retention.
Implementation remains gated on executable transport proof, capacity checks, safety tests, and normal quality gates.
The absent planning setup tools do not block manual artifact creation.
