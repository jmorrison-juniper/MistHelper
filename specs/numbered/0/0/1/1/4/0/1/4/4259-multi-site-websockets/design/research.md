# Research: Multi-site WebSocket operations

**Issue**: #4259

**Date**: 2026-10-16

## Evidence Method

Read the existing specification, constitution, plan template, catalog models, discovery services, route registry, session manager, and UI.
Use local OpenAPI evidence instead of an assumed API maximum.
Use a read-only research agent for the existing transport and runner contracts.
Do not use production credentials or send live Mist requests.
Historical test results remain historical evidence.
This work does not claim a current test pass.

Paths in this document are relative to the repository root.

## 1. Existing Page and Operation Metadata

**Decision**: Extend the existing Flask page with isolated Single Site and Multi Site state.

**Rationale**: The requested page already uses Flask templates and vanilla JavaScript.
Its catalog models define the operation scope and permitted fields.
An independent operation table can drift from the catalog.

**Evidence**:

- `src/mist/realtime/websocket_streams/web/templates/websockets_page.html` contains the current form, session list, and terminal.
- `src/mist/realtime/websocket_streams/web/static/websockets.js` builds fields from catalog metadata and uses current session routes.
- `src/mist/realtime/websocket_streams/catalog/model.py` defines `ChannelDefinition`, `UtilityDefinition`, `FieldSpec`, and `Safety`.
- `ChannelDefinition.repeatable` supports at most 10 path values.
- `UtilityDefinition` supplies device family, target fields, safety, output type, and scope.

**Alternatives considered**:

- A new npm screen. It duplicates the Flask page and increases integration work.
- A fixed list of multi-site operations. It bypasses catalog metadata.
- Replacing the Single Site form. It risks existing terminal and repeatable-selection behavior.

## 2. Complete SDK Discovery

**Decision**: Request the validated runtime page limit, then fetch every page through the SDK.

**Rationale**: The OpenAPI limit schema supplies a default, not a maximum.
The runtime already validates a safe request limit.
One full page does not prove that discovery is complete.

**Evidence**:

- `documentation/mist-api-openapi31json.json` maps `listOrgSites` to `/api/v1/orgs/{org_id}/sites`.
- It maps `listSiteDevices` to `/api/v1/sites/{site_id}/devices`.
- It maps `searchSiteWiredClients` to `/api/v1/sites/{site_id}/wired_clients/search`.
- Its shared `limit` parameter has default 100, minimum 0, and no maximum.
- `.github/copilot-instructions.md` records `DEFAULT_API_PAGE_LIMIT = 1000` and the validated `MIST_PAGE_LIMIT` range.
- `src/mist/realtime/websocket_streams/intake/pickers/devices.py` passes `type="all"` but does not call `get_all`.
- `src/mist/realtime/websocket_streams/intake/pickers/resources.py` uses wired-client `limit=100` and rejects a nonempty `next`.
- The installed Mist SDK is version 0.64.1.
- `mistapi.get_all` follows `response.next`, but it does not surface a failed next-page response as a structured completeness result.
- `mistapi.get_next(mist_session, response)` uses the authenticated SDK session to fetch the next URL.
- `APIResponse` builds `next` from a response `next` URL or pagination headers.
- The wired-client OpenAPI schema defines `next` as the URL for the next results page.

**Required change**: Complete discovery through SDK methods with explicit arguments.
Preserve existing picker route shapes.
Expose complete batch discovery through new routes.
Do not interpret a failure as an empty list.
Use `mistapi.get_next` page by page, and validate each returned status and response shape.
This detects a failed later page before the service returns a complete target snapshot.

**Alternatives considered**:

- Treating 100 as the API maximum. The schema does not support that claim.
- Treating 1000 as a vendor maximum. It is the validated application setting.
- `mistapi.get_all` without per-page validation. It cannot prove that every next-page response succeeded.
- Handwritten REST pagination. It violates the SDK-only boundary.
- Accepting partial discovery. It makes an `all` selection incorrect.

## 3. Verified Target Scope

**Decision**: Freeze natural-key target tuples before confirmation and batch admission.

**Rationale**: Browser selections can change while discovery is pending.
A client MAC alone does not prove device association.
A mutable `all` selector can execute work on targets that the operator did not confirm.

**Evidence**:

- `intake/pickers/service.py` resolves clients through a selected device.
- `intake/pickers/resources.py` requires wired-client site and device association.
- Gateway client association is currently unavailable.
- `web/static/websockets.js` already compares client lookup scopes before applying a response.
- `intake/start_request/validation.py` rejects unknown start keys and uses catalog locks.

These source paths share the prefix `src/mist/realtime/websocket_streams/`.

The batch retains a complete discovery snapshot.
One preview converts all selectors into explicit targets.
A scope change invalidates the preview.
The server never silently adds a newly discovered target after confirmation.
At execution, a denied or removed target receives its own failed outcome.

Organization-only channels execute once.
Unassigned organization Mist Edges retain a null site identity.
Do not fabricate a site to satisfy a display column.

**Alternatives considered**:

- Repeating discovery at every target start. It wastes requests and changes the confirmed set.
- A site-wide client list for a gateway. It lacks verified association.
- A cross-product of sites, devices, and clients. It creates invalid target combinations.

## 4. Existing Transport Exception

**Decision**: Reuse the owned transport for the currently affected flows.
Keep REST utility triggers in `mistapi`.

**Rationale**: The existing exception addresses missing first output and damaged split control sequences.
A batch coordinator does not justify a second transport.

**Evidence**:

- `specs/3671-interactive-terminal/plan.md` names
  `mistapi.device_utils.__tools.__ws_wrapper.WebSocketWrapper.start_with_trigger`.
- That plan records the SDK trigger-before-subscribe defect and the split-screen defect.
- It names `tests/contract/websocket_streams/test_ws_sdk_contract.py`.
- Its proof names are `test_trigger_order_controls_early_command_event_retention`
  and `test_split_screen_sequence_requires_owned_byte_retention`.
- `live/transport/endpoint.py` derives `wss://api-ws.<cloud>/api-ws/v1/stream`.
- It uses `_cloud_uri`, `_apitoken`, `_apitoken_index`, and `_session`.
- `tests/unit/websocket_streams/live/transport/test_ws_endpoint.py` covers cloud hosts and active token selection.
- `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py` covers subscription before trigger and early output retention.
- `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py` covers deferred input, split UTF-8, controls, and terminal outcomes.

The `live/` paths above share the source package prefix.
The private session contract also preserves cookies and TLS settings.
Run the SDK insufficiency proofs before implementation approval.
A missing proof is an ERROR, not a permitted assumption.

**Alternatives considered**:

- Returning immediately to the SDK WebSocket wrapper. It lacks a reviewed output-contract pass.
- Writing a batch-specific socket client. It duplicates transport safety and redaction.
- Direct REST triggers. They violate the SDK-only rule.

## 5. Parent Session and Bounded Work

**Decision**: Admit one public session and schedule private target runners under shared permits.

**Rationale**: One session per target exhausts the session registry and fragments cancellation.
Unbounded child runners can bypass the current session limits.

**Evidence**:

- `live/sessions/manager/operations.py` admits sessions atomically under a lock.
- It exposes list, message polling, stop, delete, and JSONL download.
- `live/sessions/settings.py` defaults to five live sessions and a 30-minute lifetime.
- It bounds idle time, message bytes, message count, and terminal history.
- `live/sessions/manager/lifecycle.py` stops idle and expired sessions.
- It retains at most five ended sessions for at most 600 seconds.
- It applies a 15-second stuck-stop rule and runs cleanup every five seconds.

These paths share the source package prefix.

The design sets default batch concurrency to three.
It also enforces the existing global transport capacity.
These are explicit design decisions, not claims about measured cloud capacity.
The SDK owns bounded rate-limit retries and backoff.
Ambiguous utility and shell execution do not retry automatically.

**Alternatives considered**:

- Public child sessions. They violate the one-session requirement.
- A separate unbounded executor. It can bypass safety limits.
- Stopping the whole batch after one target fails. It loses independent successful results.

## 6. Finite Multi Site Shell

**Decision**: Accept an ordered command list at batch start and close each target shell after collection.

**Rationale**: Interactive broadcast makes confirmation stale and cancellation harder.
Finite per-device work gives each target a clear outcome.

**Evidence**:

- The existing shell transport exposes open, read, send, resize, and close behavior.
- The shell trigger selects one site and device.
- `tests/unit/websocket_streams/live/runners/test_ws_shell_log_completion_3758.py` checks delayed terminal completion.
- The transport research found no existing multi-site finite-command completion protocol.

Use conservative prompt-aware completion and bounded deadlines.
If completion is unproved, stop the device target and mark it failed.
Keep already captured output.
Do not report a device exit code that the transport does not supply.
Keep the Single Site interactive shell unchanged.

**Alternatives considered**:

- Live broadcast input. It changes the confirmed command list.
- A fixed sleep after each command. It can lose slow output.
- Silent success on socket close. A disconnect does not prove command completion.

## 7. Safe Saved Results

**Decision**: Persist redacted result envelopes under a session-owned `data/` subtree.

**Rationale**: The bounded browser buffer cannot serve as the complete batch archive.
Stable IDs prevent labels from becoming unsafe paths.
Session cleanup must remove disk files as well as memory.

**Evidence**:

- The constitution requires product output under `data/`.
- `live/sessions/manager/operations.py` currently exports a bounded message snapshot.
- `live/sessions/manager/lifecycle.py` currently prunes ended session records.
- `web/blueprint/registry.py` exposes session download and lifecycle routes.
- `web/services/operations/artifacts.py` is the existing artifact service location.

These paths share the source package prefix.

Combined and grouped files carry the same record identities.
Use the existing five-session and 600-second ended retention rules.
Use a manifest to describe partial results, files, errors, and truncation.
Reuse output boundary checks and redaction before every saved write.
Treat session evidence separately from general API export backends.

**Alternatives considered**:

- User-supplied paths. They permit traversal and cross-session writes.
- Permanent files without retention. They create unbounded storage.
- Saving only the final browser buffer. It loses evicted records.

## 8. Capacity and Ownership

**Decision**: Create only issue-owned documents now.
Place future code inside existing package children.

**Rationale**: Both `live` directories and both `sessions` directories already have five direct entries.
The requested feature records require the process-record exception.

**Evidence**:

- Source `live`: `__init__.py`, `runners`, `sessions`, `terminal`, and `transport`.
- Test `live`: `__init__.py`, `runners`, `sessions`, `terminal`, and `transport`.
- Source `sessions`: `__init__.py`, `buffer`, `manager`, `record`, and `settings.py`.
- Test `sessions`: `__init__.py` and four existing test modules.
- The existing feature directory contains `spec.md` and `checklists/`.
- The request assigns `.specify/feature.json` to PR #4260.
- The request assigns the existing blueprint route test to PR #4208.

The [plan](../plan.md) records separate capacity remediation actions.
Do not create a new direct child under a saturated source or test parent.
Do not create a new root-level spec directory.

**Alternatives considered**:

- A new `live/batches` directory. It creates a sixth direct entry.
- Moving unrelated modules during planning. It changes scope and ownership.
- Repointing Spec Kit. It changes another PR's file.

## Research Completion

All design questions have explicit decisions.
The shell behavior is an assumption in both the specification and the plan.
The remaining checks are implementation gates, not unresolved design choices.
