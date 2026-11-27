# Feature Specification: Offline Dynamic JVD Labs Preview

**Issue**: #4631, "feat(web-portal): add offline Dynamic JVD Labs preview". State: OPEN. Labels: `feature`, `web-portal`, `needs-human-review`.

**Record path**: `specs/numbered/0/0/1/2/2/0/1/1/4631-offline-jvd-preview/`

**Planned branch**: `feat/4631-offline-jvd-preview`. The branch does not exist yet.

**Created**: 2026-11-26

**Status**: Draft. Implementation waits for the shared-file handover and two human decisions.

**Input**: The issue body and its three comments. The comments are dated 2026-11-07 and 2026-11-17.

## Scope

The Labs preview adds one offline page to the web portal. The page shows capability status and one run-name form. The form uses one server-selected synthetic example. The page shows only logical devices, links, and an intent fingerprint. Provider access, deployment, and execution authority stay disabled.

Registration in the shared portal files waits for the shared-file handover. Public tests use synthetic fixtures and stub planners only.

## Clarifications

### Session 2026-11-26

- Q: Does this change register the Labs page in the portal? A: Not yet. PR 4208 owns `web_portal/app.py` and `web_portal/templates/base.html`. Registration waits for the shared-file handover (D-4). Source: comment 6962287494 and PR 4208.
- Q: Can public code import the private framework? A: No. The framework loads only when a developer installs it. Public tests use stub planners. Decision D-16 needs a human answer. Source: comments 6703043366 and 6962287494.
- Q: Does implementation start from the recovered local branch? A: No. Implementation starts from `main`. GitHub holds none of the recovered commits (R-05, R-06). Source: comment 6961775907.
- Q: Which run names are valid? A: The issue requires one valid run name and defines none. This record uses ASCII names of 1 to 64 characters (D-10). Assumption.
- Q: Does the Cisco config converter program own this issue? A: The issue text names no converter component. This record keeps the Labs scope (F-1).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the offline capability status (Priority: P1)

An operator opens the Labs page. The page states that the preview is offline. The page states that provider access, deployment, and execution authority are disabled.

**Why this priority**: The operator must know that the preview cannot change the network.

**Independent Test**: Request the capability response and the Labs page through the test harness. Both show the disabled values (TR-01, TR-03).

**Acceptance Scenarios**:

1. **Given** the Labs page is registered, **When** the operator opens `/labs/`, **Then** the page shows the capability status and the server example.
2. **Given** the planner package is missing, **When** the operator reads `/labs/capability`, **Then** the response reports `planner` as `absent`.

---

### User Story 2 - Preview one example plan (Priority: P1)

An operator enters one valid run name and submits the form. The page shows the logical devices, the links, and the intent fingerprint of the server example.

**Why this priority**: This is the core value of the preview.

**Independent Test**: Submit a valid run name with a stub planner. The page shows the synthetic devices, links, and fingerprint (TR-07, TU-07).

**Acceptance Scenarios**:

1. **Given** a valid run name and a stub plan, **When** the operator submits, **Then** the page shows the rows and the fingerprint.
2. **Given** the Labs page renders, **When** the form loads, **Then** the form carries the `csrf_token` field.

---

### User Story 3 - Reject invalid or unsafe input (Priority: P1)

The plan route rejects a missing CSRF token, an extra field, a repeated run name, and an invalid run name.

**Why this priority**: The form is the only input that changes page state. Each rejection blocks one known attack path.

**Independent Test**: Post each invalid case to the plan route. Each case returns HTTP 400 and shows no plan rows (TR-05 to TR-10).

**Acceptance Scenarios**:

1. **Given** a request with no CSRF token, **When** the form posts, **Then** the portal returns the shared CSRF answer with HTTP 400.
2. **Given** a request with an extra field, **When** the form posts, **Then** the page returns HTTP 400 and shows no plan rows.
3. **Given** a run name with a space, **When** the form posts, **Then** the page returns HTTP 400 and shows an error panel.

---

### User Story 4 - Show the unavailable state safely (Priority: P2)

The page shows the unavailable state when the planner is absent, when the planner fails, or when a plan result claims authority. The unavailable state shows no device rows and no link rows.

**Why this priority**: The page must fail closed when the framework is missing or returns unsafe data.

**Independent Test**: Use stub planners for each failure. Each case shows the unavailable state with HTTP 200 (TR-11, TU-04, TU-05, TU-09, TU-10).

**Acceptance Scenarios**:

1. **Given** the planner is absent, **When** a valid run name posts, **Then** the page shows `labs-unavailable` and no rows.
2. **Given** a plan result names `execution_authority`, **When** the page renders, **Then** the page shows `labs-unavailable` and logs the reason code.

---

### User Story 5 - Run the browser journey (Priority: P2)

A tester runs the browser journey on a developer machine that has Chromium. The journey covers the page, one valid submission, and the unavailable state. A failed step saves a screenshot.

**Why this priority**: The browser journey checks the stable test identifiers in a real browser. CI does not run it (D-19).

**Independent Test**: Run the browser test module after Chromium installs. The module skips with a stated cause when Chromium is absent (TB-01 to TB-03).

**Acceptance Scenarios**:

1. **Given** Chromium is installed, **When** the journey submits a valid run name, **Then** the fingerprint appears on the page.
2. **Given** Chromium is absent, **When** the browser module runs, **Then** each browser test skips and prints the cause.

---

### Edge Cases

- A run name has 65 characters. The form returns HTTP 400.
- A run name is empty. The form returns HTTP 400.
- A run name contains a non-ASCII letter. The form returns HTTP 400.
- A request repeats the `run_name` field. The form returns HTTP 400.
- A JSON body posts to the plan route. The form finds no `run_name` field and returns HTTP 400.
- The planner returns a value that is not an object. The page shows the unavailable state.
- A link names a device that the plan does not contain. The page shows the unavailable state.
- Two devices share one `id`. The page shows the unavailable state.
- The planner raises an exception. The page shows the unavailable state and logs the error with full context.
- The planner package exists, but one of its dependencies is missing. The gateway reports `absent`. This is a known limit (F-6).
- A device label contains HTML characters. The page shows the characters as text.
- The capability route receives query parameters. The route ignores them.
- Chromium is absent. The browser module skips each test and prints the cause.

## Requirements *(mandatory)*

### Functional Requirements

Routes and page:

- **FR-001**: The portal MUST serve the Labs page at `GET /labs/` after the Labs blueprint registers.
- **FR-002**: The portal MUST serve the capability response at `GET /labs/capability` as JSON.
- **FR-003**: The capability response MUST report provider access, deployment, and execution authority as `disabled`.
- **FR-004**: The Labs page MUST show the capability status from the capability response.
- **FR-005**: The Labs page MUST show one server-selected example and its run name as the default value.
- **FR-006**: The Labs page MUST render the run-name form with the `csrf_token` field.

Run-name form:

- **FR-007**: The plan route MUST reject a missing or invalid CSRF token with the shared CSRF answer.
- **FR-008**: The plan route MUST accept exactly one `run_name` field and the `csrf_token` field.
- **FR-009**: The plan route MUST reject any other field and any repeated `run_name` field with HTTP 400.
- **FR-010**: The plan route MUST reject a run name that fails the ASCII pattern with HTTP 400.

Planner and plan result:

- **FR-011**: The server MUST call the planner with the validated run name and the server example only.
- **FR-012**: The Labs page MUST show only logical devices, links, and the intent fingerprint from a valid plan result.
- **FR-013**: The intent fingerprint MUST equal `sha256:` followed by the SHA-256 of canonical JSON for the sorted devices and links.
- **FR-014**: The Labs page MUST show the unavailable state when the planner is absent or fails.
- **FR-015**: The Labs page MUST show the unavailable state and no rows when a plan result has an unexpected key.
- **FR-016**: The Labs page MUST show the unavailable state when a plan result names an execution authority key.
- **FR-017**: The package MUST NOT import the private framework when the package loads.
- **FR-018**: The public tests MUST use synthetic fixtures and stub planners only.

Scope limits, security, and process:

- **FR-019**: The feature MUST add only the three routes named in this record.
- **FR-020**: The feature MUST make no Mist API call, provider call, or device action.
- **FR-021**: Each new interactive element MUST carry a stable `data-testid` attribute.
- **FR-022**: Log output MUST use ASCII only and MUST NOT record raw form values.
- **FR-023**: Registration in `web_portal/app.py` and navigation in `web_portal/templates/base.html` MUST wait for the shared-file handover.
- **FR-024**: The change MUST add one changelog fragment. The operator guide MUST gain one Labs row after registration.
- **FR-025**: Each new directory MUST hold five children or fewer.
- **FR-026**: The page copy MUST use plain words for a junior network operations engineer.

### Mist Cloud Transport Requirements

Not applicable. The feature sends no request to a Mist REST endpoint. The feature owns no WebSocket transport. The Mist coverage files list no Labs endpoint (R-78, R-79).

### Key Entities

- **Logical device**: One planned device. Its `id` is the natural key inside one plan.
- **Link**: One planned connection between two logical devices. It holds `a_end` and `z_end`.
- **Plan result**: The validated output of one planner call. It holds the devices, the links, and the fingerprint.
- **Planner outcome**: The state of one planner call. The state is `available`, `absent`, or `failed`.
- **Run name**: One ASCII value from the form. The server does not store it.

See `design/data-model.md` for the fields and the state transitions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 12 route tests pass or skip with a stated cause.
- **SC-002**: Zero device or link rows appear for any plan result with an unexpected key or an authority key.
- **SC-003**: The package imports with the private framework absent. Test TU-12 passes.
- **SC-004**: Line coverage for `src/interfaces/labs` is 80 percent or above in the coverage gate.
- **SC-005**: Zero new direct children appear in `src/interfaces/portals`, `tests/e2e`, `tests/unit`, or `web_portal`.
- **SC-006**: The remote check count is 82 in `STATUS.json`, in `design/research.md`, and in the summary.
- **SC-007**: Test TU-13 finds zero Mist, provider, or device imports in the package.

## Assumptions

- The shared-file handover (gate G3 in record 4648) arrives before registration starts.
- PR 4208 remains a draft or closes before the handover. The owner decides this.
- A present planner exposes the module name `vmm_topology`, as issue #4504 names it (U-1).
- Flask 3.1.3 and Flask-WTF 1.3.0 stay pinned in `requirements.txt`.
- The owner keeps the recovered local copies until issue #4822 finishes preservation.
- Developers run the browser journey on a machine that has Chromium.

## Out of Scope

- Live provider access, deployment, plan execution, and plan storage.
- Importing or publishing the private framework, its fixtures, or its archives.
- Publishing, rebasing, or cherry-picking the recovered local branch or its tags.
- The VMM editor export contract. Issue #4822 preserves it as a separate document.
- New menu operations, `OperationRegistry` entries, or README menu counts.
- Mist API calls and new dependencies.
- Edits to `web_portal/app.py` and `web_portal/templates/base.html` before the shared-file handover.
- Cisco config converter routes, state, or registration.
- Five-item debt repair in `src/interfaces/portals`, `tests/e2e`, `tests/unit`, and `web_portal` (RA-1 to RA-3).

## Dependencies

- Shared-file handover (gate G3 in record 4648). It blocks T013 and T014.
- PR 4208, open draft. It owns `web_portal/app.py` and `web_portal/templates/base.html`.
- Issue #4822, open. It preserves the recovered local copies before cleanup.
- Human decisions D-16 and D-17. Each needs an owner answer.

Caution: Without the shared-file handover, the Labs page stays unreachable from the portal.

Warning: Removing the recovered local copies before issue #4822 verifies them cannot be undone.
